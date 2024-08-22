from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools import Tracer

from base64 import b64decode, b64encode
import json
import os
import requests
import boto3

formatter = LambdaPowertoolsFormatter(utc=False, log_record_order=["message"])
logger = Logger(logger_formatter=formatter, utc=False)
tracer = Tracer()

ssm = parameters.SSMProvider()
bucket = ssm.get(os.environ["s3_bucket_parameter"], 300)
s3 = boto3.client('s3')

credentials = json.loads(
        ssm.get(os.environ['PARAMETER_NAME'], 300, decrypt=True))
        
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('izum-attachments')

def get_headers(authorization, api_key):
    return {
        "accept": "application/json",
        "Authorization": authorization,
        "x-api-key": api_key,
    }

def get_authorization(credentials):
    auth_url = credentials["auth_url"] 
    client_id = credentials["client_id"] 
    client_secret = credentials["client_secret"] 
    username = credentials["username"] 
    password = credentials["password"] 
    
    response = requests.post(auth_url, {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'password',
        'username': username,
        'password': password
    },)

    return {
        'data': response.json() if response.json() else 'No response data',
        'status': response.status_code
    }

def get_base64_blob_string(response):
    blob = b''
    for chunk in response.iter_content(chunk_size=128):
        blob += chunk

    return b64encode(blob).decode('ascii')

def lambda_handler(event, context):
    # TODO implement
    logger.info(event)
    csvFile = event['Items']

    if not credentials:
        result = {
            'message': 'Credentials parameter is empty'
        }
        print(F'result: {json.dumps(result)}')
        raise result
    
    auth_response = get_authorization(credentials)
    response_status = auth_response['status']
    
    if response_status > 199 and response_status < 300:
        print(auth_response)
        token_type = auth_response["data"]["token_type"]
        access_token = auth_response["data"]["access_token"]
        instance_url = auth_response["data"]["instance_url"]
        issued_at = auth_response["data"]["issued_at"]
        
        result = {
            'authorization': F'{token_type} {access_token}',
            'api_url': instance_url,
            'issued_at': int(issued_at[:-3])
        }
    
        print(F'auth response status: {response_status}')
    
        print(result)
    else:
        result = {
            'message': 'Error during authentication request to Salesforce',
            'response': auth_response
        }
    
        print(F'result: {json.dumps(result)}')
    
        print(result)
    
    authorization = result['authorization']
    api_key = ''
    
    headers = get_headers(authorization, api_key)
    
    for value in csvFile:
        partition = value['ParentId']
        name = value['Name'] 
        logger.info(name)
        response = requests.get(value['URL'], headers=headers, stream=True)
        if response.ok:
            encoded_response = get_base64_blob_string(response)
        else:
            logger.info(response)
            logger.info(response.text)
            return response.text
        
        base_bytes = b64decode(encoded_response, validate=True)
        key = f'attachments-migration/{partition}/{name}'
        file = s3.put_object(Body=base_bytes, Bucket=bucket, Key=key)
        s3_location = f's3://{bucket}/{key}'
        value['S3Location'] = s3_location
        if file["ResponseMetadata"]["HTTPStatusCode"] == 200:
            migrated_file = table.put_item(Item=value)
            logger.info(migrated_file)
            continue
        else:
            raise f'Error on {partition} parentid and file {name}'
            
        
        