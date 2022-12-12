import json

import boto3

from .sim_reader import IemTicket


class DynamodbIEM:
    def __init__(self):
        pass

    def write(
        self, ticket_id, login, start_time, end_time, profile, event_date_from, event_date_to
    ):
        client = boto3.client("dynamodb")

        response = client.put_item(
            TableName="Iem-Scheduler",
            Item={
                "ticketId": {"S": ticket_id},
                "login": {"S": login},
                "eventDateFrom": {"S": event_date_from},
                "eventDateTo": {"S": event_date_to},
                "startTime": {"S": start_time},
                "endTime": {"S": end_time},
                "profile": {"S": profile},
            },
        )

    def read(self, ticket_id, login):
        client = boto3.client("dynamodb")

        response = client.get_item(
            TableName="Iem-Scheduler", Key={"ticketId": {"S": ticket_id}, "login": {"S": login}}
        )
        return response
