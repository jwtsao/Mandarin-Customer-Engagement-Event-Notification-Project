import json

import boto3
import urllib3
from botocore.exceptions import ClientError


class Notification:
    def __init__(self):
        self.new_assignee_webhook_url = self.get_secret("new_assignee_workflow_url")
        self.remove_assignee_webhook_url = self.get_secret("remove_assignee_workflow_url")
        self.update_records_webhook_url = self.get_secret("update_records_webhook_url")
        self.schedule_notification_webhook_url = self.get_secret(
            "schedule_notification_webhook_url"
        )
        self.reminder_url = self.get_secret("reminder_webhook_url")

    def get_secret(self, key):
        secret_name = "countdown_notification_slack_webhook_url"
        region_name = "us-east-1"

        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            raise e

        secret = get_secret_value_response["SecretString"]

        secret_dict = json.loads(secret)
        webhook_url = secret_dict[key]

        return webhook_url

    def send_notification(self, entry, webhook_url):
        login = entry["login@startDate"][:-14]
        email = login + "@amazon.com"
        ticketid = entry["ticketId"]
        service = entry["service"]
        eventdatefrom = entry["eventDateFrom"]
        starttime = entry["startTime"]
        eventdateto = entry["eventDateTo"]
        endtime = entry["endTime"]
        ticketlink = "https://sim.amazon.com/issues/" + ticketid
        customer = entry["customer"]

        data = {
            "user": email,
            "ticketID": ticketid,
            "service": service,
            "eventDateFrom": eventdatefrom,
            "start_time": starttime,
            "eventDateTo": eventdateto,
            "end_time": endtime,
            "link": ticketlink,
            "customer": customer,
        }

        http = urllib3.PoolManager()
        http.request(
            "POST",
            webhook_url,
            body=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        return {"statusCode": 200, "body": json.dumps("Send to Slack succeed!")}
