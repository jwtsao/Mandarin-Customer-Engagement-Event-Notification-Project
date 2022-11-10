import logging

logging.basicConfig(level=logging.DEBUG)


def event_handler(event, context):
    logging.info("Received request")
    return {"message": "Hello World"}
