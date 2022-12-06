import json
import logging
import os
import textwrap
import traceback
from time import sleep
from typing import TypeVar

from bender.sim import SIM, SIMEdit, SIMIssue

API_ENDPOINT = "https://maxis-service-prod-iad.amazon.com"
SIM_REGION = "us-east-1 "
FOLDER_ID = "e0794c41-09db-48dd-af10-d2fd97c40e95"

# Execution role ≠credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

IemTicket = TypeVar("IemTicket", bound="IemTicket")


class IemTicket:
    """This class represents an IEM Ticket object."""

    def __init__(self, ticket_id: str, edit_id: str = None):
        self.is_edit = False
        self.is_create = self._invert(self.is_edit)
        self.original_support_respurces = None
        self.updated_support_resources = None
        self.original_event_date_from = None
        self.updated_event_date_from = None
        self.original_event_date_to = None
        self.updated_event_date_to = None

        if edit_id:
            self._get_sim_edit_info(edit_id)
            self.is_edit = True
            self.is_create = self._invert(self.is_edit)
        else:
            self.ticket = self._get_sim_tt(ticket_id)

    def _create_sim_client(self) -> SIM:
        return SIM(
            access_key=AWS_ACCESS_KEY_ID,
            secret_key=AWS_SECRET_ACCESS_KEY,
            security_token=AWS_SESSION_TOKEN,
            api_endpoint=API_ENDPOINT,
            region=SIM_REGION,
        )

    def _get_sim_tt(self, ticket_id: str) -> SIMIssue:

        # https://tiny.amazon.com/1byhoxhxa/BenderLibSIM/mainline/mainline#L485
        ticket = self._create_sim_client().get_issue(ticket_id)
        return ticket

    def _get_sim_edit_info(self, edit_id: str) -> SIMEdit:

        # https://tiny.amazon.com/s97zunky/BenderLibSIM/mainline/mainline#L1581
        edit = self._create_sim_client().get_edit_by_id(edit_id).path_edits
        logging.info(traceback.print_exc())
        logging.info(edit)

        return edit

    @staticmethod
    def _invert(arg: bool):
        return not arg

    def get_assigned_engineers(self):
        # TODO
        pass

    def get_iem_time(self):
        # TODO
        pass

    def is_assigned_engineer_login_changed(self):
        # TODO
        pass

    def get_assigned_engineer_login_change(self):
        # TODO
        pass

    def is_iem_time_changed(self):
        # TODO
        pass

    def get_iem_time_chang(self):
        # TODO
        pass
