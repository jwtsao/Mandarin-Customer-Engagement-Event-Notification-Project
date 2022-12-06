import json
from pprint import pprint

from .constants import IemTicketFields, SimActions


class SimParser:
    def __init__(self, event: dict):
        self.sns_event_message_attr = event["Records"][0]["SNS"]["MessageAttributes"]
        self.sns_event_message = json.loads(event["Records"][0]["SNS"]["Message"])

        self.sim_ticket_id = self.sns_event_message["documentId"]["id"]
        self.edit_id = None
        self.sim_action = None
        self.updated_fields = list()

        # Default bool attributes
        self.is_action_needed = True

        if (
            "editId" in self.sns_event_message
            and self.sns_event_message["Actions"] == SimActions.MODIFY
        ):
            self.edit_id = self.sns_event_message["editId"]
            self.sim_action = SimActions.MODIFY
            all_updated_fields = set(
                json.loads(self.sns_event_message_attr["updated_fields"]["Value"])
            )

            # Get the intersection of the two "set", fields updated in TT and fields actually required monitoring by us
            updated_fields_set: set = IemTicketFields.all_related_fields().intersection(
                all_updated_fields
            )
            self.updated_fields += list(updated_fields_set)

        elif self.sns_event_message["Actions"] == SimActions.CREATE:
            self.sim_action = SimActions.CREATE
        else:
            self.is_action_needed = False
