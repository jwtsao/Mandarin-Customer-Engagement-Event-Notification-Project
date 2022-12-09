import logging
import sys

from .sim_reader import IemTicket

# import your python files below

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def event_handler(event, context):
    logging.debug("Received request")

    # Get ticket data from SIM
    ticket = IemTicket(event)
    print(ticket.assigned_engineers)
    print(ticket.event_date_from)
    print(ticket.event_date_to)
    print(ticket.is_action_needed)
    print(ticket.ticket_id)
    print("is_support_respurces_changed: {}".format(ticket.is_support_respurces_changed))
    print("is_event_date_from_changed: {}".format(ticket.is_event_date_from_changed))
    print("is_event_date_to_changed: {}".format(ticket.is_event_date_to_changed))

    return {"status": 200}
