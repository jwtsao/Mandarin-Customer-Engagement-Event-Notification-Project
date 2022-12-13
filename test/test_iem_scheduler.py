import json

from bender.sim import SIMIssue

from iem_scheduler.constants import IemTicketFields
from iem_scheduler.sim_reader import IemTicket


class MockIemTicket(IemTicket):
    def __init__(self):
        pass


class TestSimReader:
    f = open("test/test_data/ticket_data.json")
    TESTING_TICKET_JSON = json.load(f)
    sim_testing_data = SIMIssue(TESTING_TICKET_JSON)

    reader = MockIemTicket()
    reader._ticket = sim_testing_data

    def test_get_mand_iem_alias_id_by_simissue(self):
        expected_alias = "MAND-IEM-546"
        alias = self.reader._get_mand_iem_alias_id_by_simissue(self.reader._ticket)

        assert alias == expected_alias

    def test_parse_nominated_support_resources(self):
        custom_fields = self.reader._ticket.custom_fields[
            IemTicketFields.NOMINATED_SUPPORT_RESOURCES.split("/")[-1]
        ]

        expected_support_resources = [
            {
                "login": "liyent",
                "start time": "12/08/2022 08:00 AM",
                "end time": "12/08/2022 12:00 AM",
                "profile": "SCD",
            },
            {
                "login": "werfserf",
                "start time": "12/08/2022 08:00 AM",
                "end time": "12/08/2022 12:00 AM",
                "profile": "Networking",
            },
            {
                "login": "werfrf",
                "start time": "12/08/2022 08:00 AM",
                "end time": "12/08/2022 12:00 AM",
                "profile": "Networking",
            },
        ]
        support_resources = self.reader._parse_nominated_support_resources(custom_fields)

        assert support_resources == expected_support_resources
