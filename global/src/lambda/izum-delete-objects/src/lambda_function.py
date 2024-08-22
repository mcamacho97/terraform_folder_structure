from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities import parameters
import json
import boto3
import os
import logging
from botocore.exceptions import ClientError
from botocore.client import Config
from datetime import datetime, timedelta
logger = Logger()
s3 = boto3.client("s3")

# Bucket name
ssm = parameters.SSMProvider()
bucket_name = ssm.get(os.environ["s3_bucket_parameter"], 300)

clientMethods = {'GET': 'get_object', 'PUT': 'put_object'}
response = {
    'headers': {
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Origin': os.environ['ALLOWED_ORIGIN'],
        'Access-Control-Allow-Methods': 'GET,PUT'
    },
}

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

    response = {}
    query_string_parameters = event['queryStringParameters']
    response['statusCode'] = 400
    
    
    if query_string_parameters != None and query_string_parameters.get('key'):
        # Optional parameters
        prefix = query_string_parameters['key']  # Filter objects by prefix
        method = event['httpMethod']
        # delimiter = '/'  # Delimiter to use for grouping objects
        
        # List objects in the bucket
        delete_object = s3.delete_object(
            Bucket=f'{bucket_name}',
            Key=f'{prefix}'
        )
        # Print the list of objects
    
        response['statusCode'] = 200
        response['body'] = json.dumps({'prefix': prefix, 'message': f'Deleted {prefix} object successfully!'})
        return response
    else:
        response['body'] = json.dumps({'message': 'Error: You must specify the key parameter'})
        return response
