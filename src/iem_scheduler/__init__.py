import logging
import json 


from .sim_reader import IemTicket

# import your python files below

from .dynamodbWriting import dynamodbIEM
from .eventBridge import eventBridge

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.debug("Received request")

    # Get ticket data from SIM
    ticket = IemTicket(event)
    ticket_id = ticket.ticket_id
    
    if ticket.is_action_needed:
        engineers = ticket.assign_engineers
        if ticket.is_create:
            db = dynamodbIEM()
            for entry in engineers:
                db.write(ticket_id, entry["login"], entry["start time"], entry["end time"], entry["profile"])
                event_details = db.read(ticket_id, entry["login"])
                newEvent = eventBridge()
                eventName = entry["login"] + "_" + ticket_id
                eventTime = newEvent.timeExpressionEditor(entry["start time"])
                newEvent.eventScheduler(eventName, eventTime, event_details)
        else:
            #ticket editing 

    


    print(ticket.assigned_engineers)
    print(ticket.event_date_from)
    print(ticket.event_date_to)
    print(ticket.is_action_needed)
    print(ticket.ticket_id)
    print("is_support_respurces_changed: {}".format(ticket.is_support_respurces_changed))
    print("is_event_date_from_changed: {}".format(ticket.is_event_date_from_changed))
    print("is_event_date_to_changed: {}".format(ticket.is_event_date_to_changed))

    return {"status": 200}
