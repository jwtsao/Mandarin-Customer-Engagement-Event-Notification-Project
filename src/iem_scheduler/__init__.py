import logging

from .notif_parser import SimParser
from .sim_reader import IemTicket

# import your python files below

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.info("Received request")

    # Parsing event data from SIM --> SNS
    event = SimParser(event)
    logging.info(event.sim_ticket_id)
    logging.info(event.edit_id)
    logging.info(event.updated_fields)
    logging.info(event.sim_action)

    # Get ticket data or updated fields from SIM
    ticket = IemTicket(event.sim_ticket_id)

    return {"status": 200}
