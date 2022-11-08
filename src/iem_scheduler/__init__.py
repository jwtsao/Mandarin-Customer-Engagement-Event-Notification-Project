from aws_lambda_powertools import Logger

logger = Logger(service="iem_scheduler")


def hello_world(event, context):
    logger.info("Received request")
    return {"message": "Hello World"}
