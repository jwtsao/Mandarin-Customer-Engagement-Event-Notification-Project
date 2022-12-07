import logging

from .notif_parser import SimParser
from .sim_reader import IemTicket

# import your python files below

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.debug("Received request")

    # Parsing event data from SIM --> SNS
    event = SimParser(event)
    print(event.sim_ticket_id)
    print(event.edit_id)
    print(event.updated_fields)
    print(event.sim_action)

    # Get ticket data or updated fields from SIM
    ticket = IemTicket(event.sim_ticket_id)

    return {"status": 200}
