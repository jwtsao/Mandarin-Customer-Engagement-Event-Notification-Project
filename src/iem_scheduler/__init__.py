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
        engineers = ticket.assigned_engineers
        # comment out the below if statement for testing
        # if ticket.is_create:
        db = DynamodbIEM()
        for entry in engineers:
            db.write(
                ticket_id,
                entry["login"],
                entry["start time"],
                entry["end time"],
                entry["profile"],
                ticket.event_date_from,
                ticket.event_date_to,
            )
            event_details = db.read(ticket_id, entry["login"])
            new_event = EventBridge()
            event_name = entry["login"] + "_" + ticket_id
            event_time = new_event.time_expression_editor(entry["start time"])
            new_event.event_scheduler(event_name, event_time, event_details)
    #     else:
    #         # ticket editing
    #         pass  # TODO

    return {"status": 200}
