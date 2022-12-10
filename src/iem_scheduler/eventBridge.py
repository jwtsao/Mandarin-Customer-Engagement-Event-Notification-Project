import json
import boto3


class eventBridge:
    def __init__(self):
        pass

    def eventscheduler(name, scheduleExpression, eventdetails):
        client = boto3.client("scheduler")
        response = client.create_schedule(
            FlexibleTimeWindow={"Mode": "OFF"},
            Name=name,
            ScheduleExpression=scheduleExpression,
            Target={
                "Arn": "arn:aws:lambda:us-east-1:413409169525:function:IemNotification",
                "RoleArn": "arn:aws:iam::413409169525:role/eventbridge-scheduler-role",
                "Input": eventdetails,
            },
        )

    def timeExpressionEditor(time):
        # format is 12/08/2022 08:00 AM
        # we want at(2022-08-12T08:00:00)"

        time_list = time.split(" ")
        date_list = time_list[0].split("/")
        hour = time_list[1].split(":")[0]
        minutes = time_list[1].split(":")[1]
        if time_list[2] == "PM":
            hour = int(hour) + 12
            hour = str(hour)

        time_formatted = (
            "at("
            + date_list[2]
            + "-"
            + date_list[1]
            + "-"
            + date_list[0]
            + "T"
            + hour
            + ":"
            + minutes
            + ":00)"
        )
        return time_formatted
