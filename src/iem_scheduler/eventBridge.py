import json
from datetime import datetime, timedelta

import boto3


class EventBridge:
    def __init__(self):
        pass

    def transform_datetime(self, date_str, time_str):
        time_str = time_str.replace("a.m.", "AM").replace("p.m.", "PM")
        combined_str = f"{date_str} {time_str}"

        datetime_obj = datetime.strptime(combined_str, "%Y-%m-%d %I:%M %p")

        # 12 hrs before the assigned start time
        datetime_obj_12hr_before = datetime_obj - timedelta(hours=12)

        formatted_str = f"at({datetime_obj_12hr_before.strftime('%Y-%m-%dT%H:%M:%S')})"

        return formatted_str

    def post_event_datetime_transform(self, date_str, time_str, day):
        time_str = time_str.replace("a.m.", "AM").replace("p.m.", "PM")
        combined_str = f"{date_str} {time_str}"

        datetime_obj = datetime.strptime(combined_str, "%Y-%m-%d %I:%M %p")

        datetime_obj_one_day_after = datetime_obj + timedelta(days=int(day))

        formatted_str = f"at({datetime_obj_one_day_after.strftime('%Y-%m-%dT%H:%M:%S')})"

        return formatted_str

    def create_schedule(self, name, schedule_expression, eventdetails):
        client = boto3.client("scheduler", region_name="us-east-1")
        response = client.create_schedule(
            # ActionAfterCompletion='DELETE',
            FlexibleTimeWindow={"Mode": "OFF"},
            Name=name,
            ScheduleExpression=schedule_expression,
            ScheduleExpressionTimezone="Asia/Taipei",
            Target={
                "Arn": "arn:aws:lambda:us-east-1:413409169525:function:IemScheduler",
                "RoleArn": "arn:aws:iam::413409169525:role/SchedulerExecutionRole",
                "Input": json.dumps(eventdetails),
            },
        )

        return response

    def delete_schedule(self, name):
        client = boto3.client("scheduler", region_name="us-east-1")
        response = client.delete_schedule(
            Name=name,
        )

        return response

    def get_schedule(self, name):
        client = boto3.client("scheduler", region_name="us-east-1")
        response = client.get_schedule(
            Name=name,
        )

        return response
