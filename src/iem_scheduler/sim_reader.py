import json
import logging
import os
import re
import textwrap
import traceback
from time import sleep
from typing import List, TypeVar

from aws4auth_handler import AWS4AuthHandler
from bender.sim import SIM, SIMEdit, SIMEdits, SIMIssue, SIMPathEdit

from .constants import IemTicketFields, Profiles, SimActions
from .notif_parser import SimParser

API_ENDPOINT = "https://issues-ext.amazon.com"
SIM_REGION = "us-east-1 "
FOLDER_ID = "e0794c41-09db-48dd-af10-d2fd97c40e95"


IemTicket = TypeVar("IemTicket", bound="IemTicket")


class IemTicket:
    """This class represents an IEM Ticket object.
    
    Pass the whole SNS event sent from SIM ti this class while constructing this class.
    It will identify the event is a SIM ticket "Modify" event or a "Create" event, and parse the data in ticket.

    Attributes:
        event: A dictionary representing the event structure sent from an SNS message.
        
        is_action_needed: A boolean variable identifying whether it is needed to modify/create message-sending schedules.
        assigned_engineers: A list of engineers currently assigned to the IEM event. For example:
            [
                {"login": "liyent", "start time": "12/08/2022 08:00 AM", "end time": "12/08/2022 12:00 AM", "profile": "SCD"},
                {"login": "tonychwu", "start time": "12/08/2022 08:00 AM", "end time": "12/08/2022 12:00 AM", "profile": "Networking"},
                ...
            ]
        event_date_from: A datetime string which is the start date of the IEM. Though the value contains both "date" and "time", please ignore the "time" part of the string since the web form on SIM only allows us to select a "date".
            For example: "2022-09-14T16:00:00.000Z"
        event_date_to: A datetime string which is the end date of the IEM. The format is the same as event_date_from.
        ticket_id: A string represending IEM ticket ID. Example: "MAND-IEM-542"
        is_support_respurces_changed: A boolean veriable showing if there's any changes to the assigned engineer list.
        is_event_date_from_changed: A boolean veriable showing if event_date_from was modified.
        is_event_date_to_changed: A boolean veriable showing if event_date_to was modified.

        Typical usage example:

        >>> ticket = IemTicket(event)
        >>> ticket_id = ticket.ticket_id
        >>> if ticket.is_action_needed:
        >>>     engineers = ticket.assigned_engineers
        >>>     if ticket.is_edit:
        >>>         # query database to obtain the original scheduled messages for all engineers related to this IEM ticket
        >>>         if ticket.is_support_respurces_changed:
        >>>             # compare the differences (e.g. is there any engineer been removed/replaced or added)
        >>>             # write/delete entries in the database
        >>>     elif ticket.is_create:
        >>>         # write entries in the database based on the value of ticket.assigned_engineers
    """

    def __init__(self, event: dict):
        self._event = SimParser(event)
        self._ticket_id: str = None
        self._is_edit: bool = False
        self._is_create: bool = False
        self._updated_support_resources: list = None
        self._updated_event_date_from: str = None
        self._updated_event_date_to: str = None

        self._is_support_respurces_changed = False
        self._is_event_date_from_changed = False
        self._is_event_date_to_changed = False

        self._ticket: SIMIssue = None
        self._edit: SIMEdit = None

        if self._event.is_action_needed:
            if self._event.sim_action == SimActions.MODIFY:
                self._get_sim_edits(self._event.edit_id)
                self._is_edit = True
            elif self._event.sim_action == SimActions.CREATE:
                self._get_sim_tt(event.sim_ticket_id)
                self._is_create = True
        else:
            pass  # do nothing

    @staticmethod
    def _create_sim_client() -> SIM:
        return SIM(
            auth=AWS4AuthHandler(
                os.environ["AWS_ACCESS_KEY_ID"],
                os.environ["AWS_SECRET_ACCESS_KEY"],
                "sim",
                "us-east-1",
                os.environ["AWS_SESSION_TOKEN"],
            ),
            api_endpoint=API_ENDPOINT,
            region=SIM_REGION,
        )

    def _get_sim_tt(self, ticket_id: str) -> SIMIssue:

        # https://tiny.amazon.com/1byhoxhxa/BenderLibSIM/mainline/mainline#L485
        self._ticket = self._create_sim_client().get_issue(ticket_id)
        custom_fields: dict = self._ticket.custom_fields
        self._updated_support_resources = self._parse_nominated_support_resources(
            custom_fields["full_text"][0]["value"]
        )
        for date in custom_fields["date"]:
            if date["id"] == IemTicketFields.EVENT_DATE_FROM.split("/")[-1]:
                self._updated_event_date_from = date["value"]
            elif date["id"] == IemTicketFields.EVENT_DATE_TO.split("/")[-1]:
                self._updated_event_date_to = date["value"]

    def _get_sim_edits(self, edit_id: str):
        self._ticket = self._get_sim_tt(edit_id.split(":")[0])
        self._ticket_id = self._get_mand_iem_alias_id_by_simissue(self._ticket)
        # https://tiny.amazon.com/s97zunky/BenderLibSIM/mainline/mainline#L1581
        self._edit = self._create_sim_client().get_edit_by_id(edit_id)
        sim_path_edits: List[SIMPathEdit] = self._edit.path_edits
        for path_edit in sim_path_edits:
            if path_edit.path in self._event.updated_fields:
                if path_edit.path == IemTicketFields.NOMINATED_SUPPORT_RESOURCES:
                    self._is_support_respurces_changed = True
                    self._updated_support_resources = self._parse_nominated_support_resources(
                        path_edit.edit_data["value"]
                    )
                if path_edit.path == IemTicketFields.EVENT_DATE_FROM:
                    self._is_event_date_from_changed = True
                    self._updated_event_date_from = path_edit.edit_data["value"]
                if path_edit.path == IemTicketFields.EVENT_DATE_TO:
                    self._is_event_date_to_changed = True
                    self._updated_event_date_to = path_edit.edit_data["value"]

    def _parse_nominated_support_resources(self, value: str) -> list:
        """
        [{"login": engineer_login, "start time": start_time, "end time": end_time, "profile": profile}]
        """
        anchor_categories = ["ps team", "tam", "field team"]
        support_resources = list()
        value = value.replace("-", "")
        content = re.sub(r"<.*?>", "", value).strip().split("\n")
        current_section = ""
        for line in content:
            if line.lower() in anchor_categories:
                current_section = line.strip()
            elif current_section.lower() == "ps team":
                current_profile = line.split(":")[0]
                if current_profile in Profiles.all_profiles():
                    engineer = {
                        "login": line.split(",")[1].strip(),
                        "start time": line.split(",")[2],
                        "end time": line.split(",")[3],
                        "profile": current_profile,
                    }
                    support_resources.append(engineer)
        return support_resources

    @staticmethod
    def _get_mand_iem_alias_id_by_simissue(sim_issue: SIMIssue) -> str:
        return [(aliase.id) for aliase in sim_issue.aliases if re.match(r"MAND-IEM-.*", aliase.id)][
            0
        ]

    @property
    def assigned_engineers(self):
        return self._updated_support_resources

    @property
    def event_date_from(self):
        return self._updated_event_date_from

    @property
    def event_date_to(self):
        return self._updated_event_date_to

    @property
    def is_action_needed(self) -> bool:
        return self._event.is_action_needed

    @property
    def ticket_id(self) -> str:
        return self._ticket_id

    @property
    def is_support_respurces_changed(self):
        return self._is_support_respurces_changed

    @property
    def is_event_date_from_changed(self):
        return self._is_event_date_from_changed

    @property
    def is_event_date_to_changed(self):
        return self._is_event_date_to_changed
