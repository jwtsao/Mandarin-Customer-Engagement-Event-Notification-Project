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
    """This class represents an IEM Ticket object."""

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

        self._parse_event(event)

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
