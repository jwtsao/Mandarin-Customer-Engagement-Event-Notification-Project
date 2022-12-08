import logging

from .sim_reader import IemTicket

# import your python files below

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.debug("Received request")

    # Get ticket data from SIM
    ticket = IemTicket(event)

    return {"status": 200}
