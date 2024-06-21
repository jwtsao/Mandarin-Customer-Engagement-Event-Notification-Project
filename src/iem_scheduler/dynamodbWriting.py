import datetime

import boto3
import pandas as pd


class DynamoDBCountdown:
    def __init__(self):
        pass

    def parse_captured_content(self, content):
        entries = content.split("\n")
        parsed_entries = []

        for entry in entries:
            parts = entry.split(", ")
            # Captured content parsing
            if len(parts) >= 3:
                site, profile, service = parts[0].split("- ")[1], parts[1].strip(), parts[2].strip()
                login = parts[3].split(": ")[0]
                event_date_from = parts[3].split(": ")[1]
                start_time = parts[4].split(" - ")[0]
                event_date_to = parts[4].split(" - ")[1]
                end_time = parts[5].replace("", "").strip()

                time_str = start_time.replace(".", "")
                time_obj = datetime.datetime.strptime(time_str, "%I:%M %p")
                time_24hr = time_obj.strftime("%H:%M")

                parsed_entries.append(
                    {
                        "service": service,
                        "site": site,
                        "profile": profile,
                        "login@startDate": login + "@" + event_date_from + "_" + time_24hr[:2],
                        "eventDateFrom": event_date_from,
                        "startTime": start_time,
                        "eventDateTo": event_date_to,
                        "endTime": end_time,
                    }
                )

        return parsed_entries

    def write(
        self, ticket_id, entry
    ):  # Here entry stands for one single record, should for loop this entry to write the whole content to DynamoDB
        client = boto3.client("dynamodb")

        response = client.put_item(
            TableName="MCE_Notification",
            Item={
                "ticketId": {"S": ticket_id},
                "site": {"S": entry["site"]},
                "service": {"S": entry["service"]},
                "profile": {"S": entry["profile"]},
                "login@startDate": {"S": entry["login@startDate"]},
                "eventDateFrom": {"S": entry["eventDateFrom"]},
                "startTime": {"S": entry["startTime"]},
                "eventDateTo": {"S": entry["eventDateTo"]},
                "endTime": {"S": entry["endTime"]},
            },
        )
        return response

    def read(self, ticket_id, login):
        client = boto3.client("dynamodb")

        response = client.get_item(
            TableName="Countdown_Notification",
            Key={"ticketId": {"S": ticket_id}, "login": {"S": login}},
        )
        return response

    def query(self, ticket_id):
        client = boto3.client("dynamodb")

        partition_key_value = ticket_id

        response = client.query(
            TableName="MCE_Notification",
            KeyConditionExpression="ticketId = :value",
            ExpressionAttributeValues={":value": {"S": partition_key_value}},
        )

        items = response["Items"]

        return items

    def delete(self, ticketid, entry):
        client = boto3.client("dynamodb")

        response = client.delete_item(
            TableName="MCE_Notification",
            Key={
                "ticketId": {"S": ticketid},
                "login@startDate": {"S": entry["login@startDate"]},
            },
        )

        return response

    def records_comparision(self, ticketid, dbquery, ticketcontent):
        transformed_result = []
        for item in dbquery:
            transformed_item = {k: v["S"] for k, v in item.items()}
            transformed_result.append(transformed_item)

        # Check if transformed_result is empty
        if transformed_result:
            df_old = pd.DataFrame(transformed_result)
        else:
            # Initialize an empty DataFrame with the necessary columns if dbquery is empty
            df_old = pd.DataFrame(
                columns=[
                    "ticketId",
                    "site",
                    "login@startDate",
                    "profile",
                    "service",
                    "eventDateFrom",
                    "startTime",
                    "eventDateTo",
                    "endTime",
                ]
            )

        # Assign ticketId to df_new and check if ticketcontent is empty
        if ticketcontent:
            df_new = pd.DataFrame(ticketcontent)
            df_new["ticketId"] = ticketid
        else:
            df_new = pd.DataFrame(
                columns=[
                    "ticketId",
                    "site",
                    "login@startDate",
                    "profile",
                    "service",
                    "eventDateFrom",
                    "startTime",
                    "eventDateTo",
                    "endTime",
                ]
            )
            df_new["ticketId"] = ticketid  # Ensure the ticketId column is present even if empty

        # Ensure both DataFrames have consistent column order
        df_old = df_old[
            [
                "ticketId",
                "site",
                "login@startDate",
                "profile",
                "service",
                "eventDateFrom",
                "startTime",
                "eventDateTo",
                "endTime",
            ]
        ]
        df_new = df_new[
            [
                "ticketId",
                "site",
                "login@startDate",
                "profile",
                "service",
                "eventDateFrom",
                "startTime",
                "eventDateTo",
                "endTime",
            ]
        ]

        # Concatenate 2 dataframe without duplicate records
        df_concat = pd.concat([df_old, df_new]).drop_duplicates().reset_index(drop=True)

        # Find to_delete and to_insert records that we need to do action to DynamoDB
        df_to_delete = pd.merge(df_concat, df_new, how="outer", indicator=True)
        records_to_delete = df_to_delete.loc[df_to_delete["_merge"] == "left_only"].drop(
            "_merge", axis=1
        )

        df_to_insert = pd.merge(df_concat, df_old, how="outer", indicator=True)
        records_to_insert = df_to_insert.loc[df_to_insert["_merge"] == "left_only"].drop(
            "_merge", axis=1
        )

        # Write the dataframe back to list of dictionary to allow action on DynamoDB
        to_delete_dict_list = records_to_delete.to_dict("records")
        to_insert_dict_list = records_to_insert.to_dict("records")

        return to_delete_dict_list, to_insert_dict_list
