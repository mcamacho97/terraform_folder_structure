import json
import boto3
import os
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer

formatter = LambdaPowertoolsFormatter(utc=False, log_record_order=["message"])
logger = Logger(logger_formatter=formatter, utc=False)
step_functions = boto3.client("stepfunctions")
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    event = json.loads(event["body"])
    data = event["data"] if event.get("data") else {}
    step_arn = os.environ["WORKFLOW"].format(
        context.invoked_function_arn.split(":")[3],
        context.invoked_function_arn.split(":")[4],
    )

    step_functions.start_execution(
        stateMachineArn=step_arn, input=json.dumps(data)
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "SUCCESS"})
    }
