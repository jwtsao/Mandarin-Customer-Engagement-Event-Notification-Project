import os

from aws4auth_handler import AWS4AuthHandler
from bender.sim import SIM

from .notif_parser import SimPaser

API_ENDPOINT = "https://issues-ext.amazon.com"
SIM_REGION = "us-east-1"
FOLDER_ID = "e0794c41-09db-48dd-af10-d2fd97c40e95"


class CountdownTicket:
    def __init__(self, event: dict):
        self.sim = self.create_sim_client()
        self.sns_message = event

    def create_sim_client(self) -> SIM:
        sim = SIM(
            auth=AWS4AuthHandler(
                access_key=os.environ["AWS_ACCESS_KEY_ID"],
                secret_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                service_name="sim",
                region_name=SIM_REGION,
                security_token=os.environ["AWS_SESSION_TOKEN"],
            ),
            api_endpoint=API_ENDPOINT,
            region=SIM_REGION,
        )
        return sim

    def read_nominated_support_resource(self):
        support_resource = ""
        parser = SimPaser(self.sns_message)

        if parser.ticketID is None:
            print("Info: No valid ticketID found. Message action might be 'Resolved'. Ignoring...")
            return None

        try:
            issue = self.sim.get_issue(parser.ticketID)
            full_text = issue.data["customFields"]["full_text"]
        except KeyError:
            print("Warning: 'full_text' key not found in customFields. Exiting function.")
            return None

        for entry in full_text:
            if entry.get("id") == "nominated_support_resources":
                support_resource = entry.get("value")

        return support_resource

    def read_nominated_support_resource2(self):
        support_resource = ""
        parser = SimPaser(self.sns_message)

        if parser.ticketID is None:
            print("Info: No valid ticketID found. Message action might be 'Resolved'. Ignoring...")
            return None

        try:
            issue = self.sim.get_issue(parser.ticketID)
            full_text = issue.data["customFields"]["full_text"]
        except KeyError:
            print("Warning: 'full_text' key not found in customFields. Exiting function.")
            return None

        for entry in full_text:
            if entry.get("id") == "nominated_support_resources_2":
                support_resource = entry.get("value")

        return support_resource

    def read_post_event_data(self, ticketid):
        issue = self.sim.get_issue(ticketid)

        post_event_data = ""
        full_text = issue.data["customFields"]["full_text"]
        for entry in full_text:
            if entry.get("id") == "post_event_data_collection":
                post_event_data = entry.get("value")

        return post_event_data

    def parse_post_event_content(self, content):
        entries = content.split("\n")
        parsed_entries = []

        for entry in entries:
            parts = entry.split(": ")
            # Captured content parsing
            if len(parts) >= 2:
                parts = entry.split(": ")
                site, profile, service, login = parts[0].split(", ")
                site = site.split("- ")[1]
                hour, survey = parts[1].split(", ")

                parsed_entries.append(
                    {
                        "service": service,
                        "site": site,
                        "profile": profile,
                        "login": login,
                        "hour": hour,
                        "survey": survey,
                    }
                )

        return parsed_entries

    # Here three function could only used by function whose message is from SNS
    def issueid(self):
        issue = self.sim.get_issue(SimPaser(self.sns_message).ticketID)
        return issue.main_id

    def issuetitle(self):
        issue = self.sim.get_issue(SimPaser(self.sns_message).ticketID)
        return issue.title

    def get_customer_name(self):
        issue = self.sim.get_issue(SimPaser(self.sns_message).ticketID)

        customer_name = ""
        custom_field = issue.data["customFields"]

        string_entries = custom_field.get("string", [])
        for item in string_entries:
            if item.get("id") == "customer_name":
                customer_name = item.get("value")

        return customer_name
