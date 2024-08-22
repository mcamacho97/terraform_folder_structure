from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities import parameters
import json
import boto3
import os
import logging
from botocore.exceptions import ClientError
from botocore.client import Config

logger = Logger()
s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))
ssm = parameters.SSMProvider()
bucket_value = ssm.get(os.environ["s3_bucket_parameter"], 300)
clientMethods = {'GET': 'get_object', 'PUT': 'put_object'}
response = {
    'headers': {
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Origin': os.environ['ALLOWED_ORIGIN'],
        'Access-Control-Allow-Methods': 'GET,PUT'
    },
}

# Validating the parameters passed in the query string.


def validateParameters(queryParams):
    if 'key' in queryParams and queryParams['key']:
        key = queryParams['key']
    else:
        response['body'] += '"key" query parameter is required'
        return

    bucket = queryParams['bucket'] if 'bucket' in queryParams and queryParams['bucket'] else bucket_value

    time = int(
        queryParams['time']) if 'time' in queryParams and queryParams['time'] and queryParams['time'].isnumeric() else 900

    return [{'Bucket': bucket, 'Key': key}, time]


# This function is generating a presigned URL for the S3 object.
def generatePresignURL(method, params, time):
    if clientMethods.get(method):
        try:
            logger.info(clientMethods[method])
            presignedURL = s3_client.generate_presigned_url(
                clientMethods[method], params, time)
        except ClientError as error:
            logger.error(error)
            response['body'] = str(error)
            return
        return presignedURL
    else:
        response['body'] += 'Method No Supported'
        return



@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    
    response['statusCode'] = 400
    response['body'] = 'Invalid Request: '

    logger.info(F"event: {json.dumps(event)}")

    method = event['httpMethod']
    queryParams = event['queryStringParameters']

    validationResult = validateParameters(queryParams)

    logger.info(F"validationResult: {json.dumps(validationResult)}")

    if not validationResult:
        logger.info(F"response: {json.dumps(response)}")
        return response

    [params, time] = validationResult

    generatorResult = generatePresignURL(method, params, time)

    logger.info(F"generatorResult: {json.dumps(generatorResult)}")

    if not generatorResult:
        logger.info(F"response: {json.dumps(response)}")
        return response

    response['statusCode'] = 200
    response['body'] = generatorResult
    logger.info(F"response: {json.dumps(response)}")
    return response
