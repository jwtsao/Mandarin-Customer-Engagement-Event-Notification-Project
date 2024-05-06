import json


class SimPaser:
    def __init__(self, event: dict):
        self.sns_event_message = json.loads(event["Records"][0]["Sns"]["Message"])
        self.ticketID = None

        if self.sns_event_message["action"] == "Modify":
            self.ticketID = self.sns_event_message["documentId"]["id"]
