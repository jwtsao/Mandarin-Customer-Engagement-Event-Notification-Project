import logging

from .notif_parser import SimParser
from .sim_reader import IemTicket

# import your python files below

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.debug("Received request")

    # Parsing event data from SIM --> SNS
    event = SimParser(event)
    logging.debug(event.sim_ticket_id)
    logging.debug(event.edit_id)
    logging.debug(event.updated_fields)
    logging.debug(event.sim_action)

    # Get ticket data or updated fields from SIM
    ticket = IemTicket(event.sim_ticket_id)

    return {"status": 200}
