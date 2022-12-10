import json
import boto3

from .sim_reader import IemTicket


class dynamodbIEM:
    def __init(self):
        pass

    def write(ticketID, login, startTime, endTime, profile):
        client = boto3.client("dynamodb")

        response = client.put_item(
            TableName="Iem-Scheduler",
            Item={
                "ticketId": {"S": ticketID},
                "login": {"S": login},
                "eventDateFrom": {"S": eventDateFrom},
                "eventDateTo": {"S": eventDateTo},
                "startTime": {"S": startTime},
                "endTime": {"S": endTime},
                "profile": {"S": profile},
            },
        )

    def read(ticketId, login):
        client = boto3.client("dynamodb")

        response = client.get_item(
            TableName="Iem-Scheduler", Key={"ticketId": {"S": ticketId}, "login": {"S": login}}
        )
        return response
