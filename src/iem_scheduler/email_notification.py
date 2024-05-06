import hashlib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3


class EmailNotification:
    def __init__(self):
        pass

    def generate_uid(self, event):
        deterministic_data = f"{event['ticketId']}-{event['login']}"
        uid_hash = hashlib.sha256(deterministic_data.encode()).hexdigest()
        return f"Schedule-{uid_hash}"

    def format_datetime(self, date, time):
        time = time.replace("a.m.", "AM").replace("p.m.", "PM")
        datetime_str = f"{date} {time}"
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
        dt_earlier = dt - timedelta(hours=8)

        dt_trans = dt_earlier.strftime("%Y%m%dT%H%M%SZ")

        return dt_trans

    def send_calendar_invitation(self, event, option, sequence):
        login = event["login"]
        ticketid = event["ticketId"]
        start_time = self.format_datetime(event["eventDateFrom"], event["startTime"])
        end_time = self.format_datetime(event["eventDateFrom"], event["endTime"])
        date_till = self.format_datetime(event["eventDateTo"], event["endTime"])

        # Here we use eventDateFrom to send Email for the first day schedule to ensure the calendar invitation correct.
        ticketlink = "https://sim.amazon.com/issues/" + ticketid

        sender = "MCE-notification@jwtsao.people.aws.dev"
        recipient = login + "@amazon.com"
        subject = f"""Reminder: MCE Event {ticketid} Notification"""

        unique_id = self.generate_uid(event)

        description = "Thank you for contributing to the MCE event and our customer."

        html_content_invitation = (
            f"<html>"
            f"<head></head>"
            f"<body>"
            f"<b>This Email is only for Notification purposes. If you can't participate in this MCE event, please discuss your schedule with your manager.</b>"
            f"<br>"
            f"<p>Hi {login}, </p>"
            f"<p>you have been assigned to MCE event: <strong>{ticketid}</strong>.</p>"
            f"<p>Please visit: {ticketlink} and check the nominated support resource on the SIM issue page -> Information Tab. Look at the custom field below to check your assigned information.</p>"
            f"<br><br>"
            f"<p>For additional information, including a user guide, please visit <a href='{'https://w.amazon.com/bin/view/AWSSupportMandarin/OperationalExcellence/CustomerEngagementProcess/Mandarin_Engagement_Event_Dashboard/'}'>Mandarin_Engagement_Event_Dashboard</a> Wiki.</p>"
            f"<br>"
            f"</body>"
            f"</html>"
        )

        html_content_modification = (
            f"<html>"
            f"<head></head>"
            f"<body>"
            f"<b>This Email is only for Notification purposes. If you can't participate in this MCE event, please discuss your schedule with your manager.</b>"
            f"<br>"
            f"<p>Hi {login}, </p>"
            f"<p>the MCE event you have been assigned to: <strong>{ticketid}</strong> have change the schedule.</p>"
            f"<p>Please visit: {ticketlink} and check the nominated support resource on the SIM issue page -> Information Tab. Look at the custom field below to check your assigned information.</p>"
            f"<br><br>"
            f"<p>For additional information, including a user guide, please visit <a href='{'https://w.amazon.com/bin/view/AWSSupportMandarin/OperationalExcellence/CustomerEngagementProcess/Mandarin_Engagement_Event_Dashboard/'}'>Mandarin_Engagement_Event_Dashboard</a> Wiki.</p>"
            f"<br>"
            f"</body>"
            f"</html>"
        )
        html_list = []
        html_list.append(html_content_invitation)
        html_list.append(html_content_modification)

        # Create the calendar event
        calendar_content_type = []
        calendar_content_occurence = f"""
BEGIN:VCALENDAR\r
PRODID:-//TPE11//Countdown//EN\r
VERSION:2.0\r
CALSCALE:GREGORIAN\r
METHOD:REQUEST\r
BEGIN:VEVENT\r
UID:{unique_id}\r
DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\r
DTSTART:{start_time}\r
DTEND:{end_time}\r
SUMMARY:Countdown Notification\r
STATUS:CONFIRMED\r
LOCATION:Virtual\r
DESCRIPTION:{description}\r
ORGANIZER;CN="MCE Notification":mailto:{sender}\r
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=FALSE;CN="{login}":mailto:{recipient}\r
BEGIN:VALARM\r
DESCRIPTION:REMINDER\r
TRIGGER;RELATED=START:-PT15M\r
ACTION:DISPLAY\r
END:VALARM\r
END:VEVENT\r
END:VCALENDAR
"""

        calendar_content_series = f"""
BEGIN:VCALENDAR\r
PRODID:-//TPE11//Countdown//EN\r
VERSION:2.0\r
CALSCALE:GREGORIAN\r
METHOD:REQUEST\r
BEGIN:VEVENT\r
RRULE:FREQ=DAILY;UNTIL={date_till};INTERVAL=1\r
UID:{unique_id}\r
DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\r
DTSTART:{start_time}\r
DTEND:{end_time}\r
SUMMARY:Countdown Notification\r
STATUS:CONFIRMED\r
LOCATION:Virtual\r
DESCRIPTION:{description}\r
ORGANIZER;CN="MCE Notification":mailto:{sender}\r
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=FALSE;CN="{login}":mailto:{recipient}\r
BEGIN:VALARM\r
DESCRIPTION:REMINDER\r
TRIGGER;RELATED=START:-PT15M\r
ACTION:DISPLAY\r
END:VALARM\r
END:VEVENT\r
END:VCALENDAR
"""
        calendar_content_type.append(calendar_content_occurence)
        calendar_content_type.append(calendar_content_series)

        # MIME message
        msg = MIMEMultipart("mixed")
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject

        mime_html = MIMEText(
            html_list[option], "html", "utf-8"
        )  # option decided the email content is assign or update, 0 for assign and 1 for update
        msg.attach(mime_html)

        mime_text = MIMEText(
            calendar_content_type[sequence], "calendar; method=REQUEST", "utf-8"
        )  # sequence decide whether the schedule is occurrence or series, 0 for occurence and 1 for series
        msg.attach(mime_text)
        raw_message = msg.as_string()

        ses = boto3.client("ses", region_name="us-east-1")
        response = ses.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={"Data": raw_message},
        )

        return {"statusCode": 200, "body": response}

    def send_calendar_cancellation(self, event, sequence):
        login = event["login"]
        ticketid = event["ticketId"]
        start_time = self.format_datetime(event["eventDateFrom"], event["startTime"])
        end_time = self.format_datetime(event["eventDateFrom"], event["endTime"])
        date_till = self.format_datetime(event["eventDateTo"], event["endTime"])

        ticketlink = "https://sim.amazon.com/issues/" + ticketid

        sender = "MCE-notification@jwtsao.people.aws.dev"
        recipient = login + "@amazon.com"
        subject = f"Canceled: MCE Event {ticketid} Notification"

        unique_id = self.generate_uid(event)

        description = "Thank you for contributing to the MCE event and our customer."

        html_content = (
            f"<html>"
            f"<head></head>"
            f"<body>"
            f"<p>Hi {login},</p>"
            f"<p>Your nominated support resource of MCE event: <strong>{ticketid}</strong> has been cancelled.</p>"
            f"<p>For more information, please visit: {ticketlink}</p>"
            f"<p>There is no further action required."
            f"<br><br>"
            f"<p>For additional information, including a user guide, please visit <a href='{'https://w.amazon.com/bin/view/AWSSupportMandarin/OperationalExcellence/CustomerEngagementProcess/Mandarin_Engagement_Event_Dashboard/'}'>Mandarin_Engagement_Event_Dashboard</a> Wiki.</p>"
            f"<br>"
            f"</body>"
            f"</html>"
        )

        # Create the cancellation for the calendar event
        calendar_content_list = []
        calendar_content_occurrence = f"""
BEGIN:VCALENDAR\r
METHOD:CANCEL\r
PRODID:-//TPE11//Countdown//EN\r
VERSION:2.0\r
CALSCALE:GREGORIAN\r
BEGIN:VEVENT\r
UID:{unique_id}\r
SUMMARY;LANGUAGE=en-US:Canceled: MCE Event {ticketid} Notification\r
DTSTART:{start_time}\r
DTEND:{end_time}\r
DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\r
LOCATION:Virtual\r
STATUS:CANCELLED\r
DESCRIPTION:{description}\r
ORGANIZER;CN="MCE Notification":mailto:{sender}\r
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=FALSE;CN="{login}":mailto:{recipient}\r
END:VEVENT\r
END:VCALENDAR
"""
        calendar_content_series = f"""
BEGIN:VCALENDAR\r
METHOD:CANCEL\r
PRODID:-//TPE11//Countdown//EN\r
VERSION:2.0\r
CALSCALE:GREGORIAN\r
BEGIN:VEVENT\r
RRULE:FREQ=DAILY;UNTIL={date_till};INTERVAL=1\r
UID:{unique_id}\r
SUMMARY;LANGUAGE=en-US:Canceled: MCE Event {ticketid} Notification\r
DTSTART:{start_time}\r
DTEND:{end_time}\r
DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\r
LOCATION:Virtual\r
STATUS:CANCELLED\r
DESCRIPTION:{description}\r
ORGANIZER;CN="MCE Notification":mailto:{sender}\r
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=FALSE;CN="{login}":mailto:{recipient}\r
END:VEVENT\r
END:VCALENDAR
"""
        calendar_content_list.append(calendar_content_occurrence)
        calendar_content_list.append(calendar_content_series)

        # MIME message for cancellation
        msg = MIMEMultipart("mixed")
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject

        mime_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(mime_html)

        mime_text = MIMEText(calendar_content_list[sequence], "calendar; method=CANCEL", "utf-8")
        msg.attach(mime_text)
        raw_message = msg.as_string()

        ses = boto3.client("ses", region_name="us-east-1")
        response = ses.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={"Data": raw_message},
        )

        return {"statusCode": 200, "body": response}

    def find_schedule_change(self, old_record, new_record):
        old_record_dict = {item["login"]: item for item in old_record}
        time_change_list = []

        for new_item in new_record:
            login = new_item["login"]
            if login in old_record_dict:
                old_item = old_record_dict[login]
                if (
                    new_item["eventDateFrom"] != old_item["eventDateFrom"]
                    or new_item["startTime"] != old_item["startTime"]
                    or new_item["eventDateTo"] != old_item["eventDateTo"]
                    or new_item["endTime"] != old_item["endTime"]
                ):
                    time_change_list.append(new_item)

        return time_change_list
