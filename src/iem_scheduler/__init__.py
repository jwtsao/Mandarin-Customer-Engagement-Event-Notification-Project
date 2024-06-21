import json

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from .dynamodbWriting import DynamoDBCountdown
from .email_notification import EmailNotification
from .eventBridge import EventBridge
from .sim_reader import CountdownTicket
from .slack_notification import Notification

logger = Logger(service="iem_scheduler_dev")


def lambda_handler(event, context):
    logger.info("Received request")

    if "Records" in event and "Sns" in event["Records"][0]:
        print("SNS event received")
        ticket = CountdownTicket(event)
        nominated_support_resource = ticket.read_nominated_support_resource()
        nominated_support_resource2 = ticket.read_nominated_support_resource2()

        if nominated_support_resource is None:
            logger.info("No nominated support resource found, exiting.")
            return {"statusCode": 400, "body": json.dumps("No nominated support resource found.")}

        ticket_id = ticket.issueid()
        print("Ticket ID: ", ticket_id)
        customer_name = ticket.get_customer_name()

        db = DynamoDBCountdown()

        # parsed_entries should be list of dictionary with multiple entries(if the custom field content contains several assignments)
        parsed_entries1 = db.parse_captured_content(nominated_support_resource)
        parsed_entries2 = db.parse_captured_content2(nominated_support_resource2)
        parsed_entries = parsed_entries1 + parsed_entries2

        dbquery = db.query(ticket_id)

        records_to_delete, records_to_insert = db.records_comparision(
            ticket_id, dbquery, parsed_entries
        )

        # Write records_to_delete and records_to_insert to DynamoDB
        for entry in records_to_delete:
            db.delete(entry["ticketId"], entry)

        for entry in records_to_insert:
            db.write(ticket_id, entry)

        # Create EventBridge Schedules
        eb = EventBridge()

        for entry in records_to_delete:
            # first try to get the exist event schedule, if there is no schedule then skip delete
            day = ["1", "3", "5"]
            schedule_name = entry["ticketId"] + "_" + entry["login@startDate"].replace("@", "-")
            try:
                eb.delete_schedule(schedule_name)
            except ClientError as error:
                if error.response["Error"]["Code"] == "ResourceNotFoundException":
                    print(f"Schedule {schedule_name} does not exist, skipping...")
            for d in day:
                schedule_name_post = schedule_name + "_post_" + d
                try:
                    eb.delete_schedule(schedule_name_post)
                except ClientError as error:
                    if error.response["Error"]["Code"] == "ResourceNotFoundException":
                        print(f"Schedule {schedule_name_post} does not exist, skipping...")

        for entry in records_to_insert:
            print("Creating EventBridge Schedule: ", entry["login@startDate"], " ...")
            payload = entry
            payload["customer"] = customer_name
            schedule_time = eb.transform_datetime(entry["eventDateFrom"], entry["startTime"])
            schedule_name = entry["ticketId"] + "_" + entry["login@startDate"].replace("@", "-")
            try:
                eb.create_schedule(schedule_name, schedule_time, payload)
                print("Successfully create EventBridge Schedule: ", schedule_name)
            except ClientError as error:
                if error.response["Error"]["Code"] == "ConflictException":
                    print(f"Schedule {schedule_name} already exists. Deleting existing schedule.")
                    eb.delete_schedule(schedule_name)
                    print("Re-creating the schedule.")
                    eb.create_schedule(schedule_name, schedule_time, payload)

        en = EmailNotification()

        # Send notification to slack webhook by storing webhook URL to secret manager
        sn = Notification()
        new_assignee = sn.new_assignee_webhook_url
        remove_assignee = sn.remove_assignee_webhook_url

        print("records to delete: ", records_to_delete)
        print("records to insert: ", records_to_insert)

        # Send notification to Microsoft Outlook to enable calendar reminder
        for entry in records_to_delete:
            records_d = entry
            records_d["customer"] = customer_name
            sn.send_notification(records_d, remove_assignee)
            if records_d["eventDateFrom"] == records_d["eventDateTo"]:
                en.send_calendar_cancellation(records_d, 0)
            else:
                en.send_calendar_cancellation(records_d, 1)

        for entry in records_to_insert:
            records_i = entry
            records_i["customer"] = customer_name
            sn.send_notification(records_i, new_assignee)
            if records_i["eventDateFrom"] == records_i["eventDateTo"]:
                en.send_calendar_invitation(records_i, 0, 0)
            else:
                en.send_calendar_invitation(records_i, 0, 1)

    if "ticketId" in event:
        if "post_event" in event:
            # This is a post notification
            print("Post event received")
            print("Ticket ID: ", event["ticketId"])

            ticket = CountdownTicket(event)
            eb = EventBridge()
            sn = Notification()
            post_event_data = ticket.read_post_event_data(event["ticketId"])
            post_parsed_entries = ticket.parse_post_event_content(post_event_data)
            post_login_list = []
            for entry in post_parsed_entries:
                post_login_list.append(entry["login"])  # Try to drop duplicate login here

            login = event["login@startDate"][:-11]

            if login not in post_login_list:  # The Engineer not yet fill the form
                reminder = sn.reminder_url
                sn.send_notification(event, reminder)
                schedule_name = (
                    event["ticketId"]
                    + "_"
                    + event["login@startDate"].replace("@", "-")
                    + "_post_"
                    + str(event["post_event"])
                )
                try:
                    eb.delete_schedule(schedule_name)
                except ClientError as error:
                    if error.response["Error"]["Code"] == "ResourceNotFoundException":
                        print(f"Schedule {schedule_name} does not exist, skipping...")
            else:  # The Engineer have already filled out the form
                day = ["1", "3", "5"]
                for d in day:
                    schedule_name = (
                        event["ticketId"]
                        + "_"
                        + event["login@startDate"].replace("@", "-")
                        + "_post_"
                        + d
                    )
                    try:
                        eb.delete_schedule(schedule_name)
                    except ClientError as error:
                        if error.response["Error"]["Code"] == "ResourceNotFoundException":
                            print(f"Schedule {schedule_name} does not exist, skipping...")

            return {"status": 200}

        if "post_event" not in event:
            print("EventBridge event received")
            print("Ticket ID: ", event["ticketId"])

            sn = Notification()
            schedule_notification = sn.schedule_notification_webhook_url

            sn.send_notification(event, schedule_notification)

            eb = EventBridge()
            schedule_name = event["ticketId"] + "_" + event["login@startDate"].replace("@", "-")
            try:
                eb.delete_schedule(schedule_name)
            except ClientError as error:
                if error.response["Error"]["Code"] == "ResourceNotFoundException":
                    print(f"Schedule {schedule_name} does not exist, skipping...")

            # Below logic write the post event schedule of 1, 3, and 5 day using for loop
            day = ["1", "3", "5"]

            for d in day:
                day_after_notif_time = eb.post_event_datetime_transform(
                    event["eventDateTo"], event["endTime"], d
                )
                day_after_schedule_name = (
                    event["ticketId"]
                    + "_"
                    + event["login@startDate"].replace("@", "-")
                    + "_post_"
                    + d
                )
                payload = event
                payload["post_event"] = d
                try:
                    eb.create_schedule(day_after_schedule_name, day_after_notif_time, payload)
                except ClientError as error:
                    if error.response["Error"]["Code"] == "ConflictException":
                        print(
                            f"Schedule {day_after_schedule_name} already exists. Deleting existing schedule."
                        )
                        eb.delete_schedule(day_after_schedule_name)
                        print("Re-creating the schedule.")
                        eb.create_schedule(day_after_schedule_name, day_after_notif_time, payload)

    return {"status": 200}
