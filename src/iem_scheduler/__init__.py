import logging
import sys

from .dynamodbWriting import DynamodbIEM
from .eventBridge import EventBridge
from .sim_reader import IemTicket

# import your python files below


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def event_handler(event, context):
    logging.debug("Received request")

    # Get ticket data from SIM
    ticket = IemTicket(event)
    ticket_id = ticket.ticket_id

    if ticket.is_action_needed:
        engineers = ticket.assign_engineers
        if ticket.is_create:
            db = DynamodbIEM()
            for entry in engineers:
                db.write(
                    ticket_id,
                    entry["login"],
                    entry["start time"],
                    entry["end time"],
                    entry["profile"],
                )
                event_details = db.read(ticket_id, entry["login"])
                new_event = EventBridge()
                event_name = entry["login"] + "_" + ticket_id
                event_time = new_event.timeExpressionEditor(entry["start time"])
                new_event.eventScheduler(event_name, event_time, event_details)
        else:
            # ticket editing
            pass  # TODO

    print(ticket.assigned_engineers)
    print(ticket.event_date_from)
    print(ticket.event_date_to)
    print(ticket.is_action_needed)
    print(ticket.ticket_id)
    print("is_support_respurces_changed: {}".format(ticket.is_support_respurces_changed))
    print("is_event_date_from_changed: {}".format(ticket.is_event_date_from_changed))
    print("is_event_date_to_changed: {}".format(ticket.is_event_date_to_changed))

    return {"status": 200}
