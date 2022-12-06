import logging

from .notif_parser import parser
from .sim_reader import IemTicket

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.info("Received request")
    logging.info(event)
    parser(event)
    return {"status": 200}
