import json
import os
import boto3
from boto3.dynamodb.conditions import Attr, And
import logging
from botocore.exceptions import ClientError
import io
from boto3.dynamodb.conditions import Attr
from PIL import Image
from urllib.parse import urlparse


# Declaring and initializing variables
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# ENV VARIABLES
allow_formats = os.environ["ALLOW_FORMATS"].split(",") # Convert allow formats to list
minimum_quality = int(os.environ["MINIMUM_QUALITY"])
output_format = os.environ["OUTPUT_FORMAT"]
quality = int(os.environ["QUALITY"])
target_size = int(os.environ["TARGET_SIZE"])
origin_bucket = os.environ["ORIGIN_BUCKET"] 
destiny_bucket = os.environ["DESTINY_BUCKET"] 
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)

def update_table(key, attribute_updates):
    try:
        # Update the item
        response = table.update_item(
            Key=key,
            AttributeUpdates=attribute_updates,
            ReturnValues='UPDATED_NEW' 
        )

        return response
    except Exception as e:
        raise e

def scan_table(filter_expression, projection_expression):
    try:
        # Perform the initial scan
        response = table.scan(FilterExpression=filter_expression, ProjectionExpression=projection_expression)
        data = response['Items']

        # Perform paginator to scan all items
        while 'LastEvaluatedKey' in response:
            response = table.scan(FilterExpression=filter_expression, ProjectionExpression=projection_expression, ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        
        logger.info(len(data))
        return data

    except Exception as e:
        raise e


def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def compress_img(image_name, new_size_ratio=0.9, quality=90, width=None, height=None, output_format="WebP"):
    # Load the image to memory
    img = Image.open(image_name)
    logger.info(f"[*] Image shape: {img.size}")

    # get the original image size in bytes
    image_size = os.path.getsize(image_name)

    logger.info(f"[*] Size before compression: {get_size_format(image_size)}")

    if new_size_ratio < 1.0:
        # if resizing ratio is below 1.0, then multiply width & height with this ratio to reduce image size
        img = img.resize((int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)), Image.Resampling.LANCZOS)
        logger.info(f"[+] New Image shape: {img.size}")
    elif width and height:
        # if width and height are set, resize with them instead
        img = img.resize((width, height), Image.ANTIALIAS)
        logger.info(f"[+] New Image shape: {img.size}")

    # split the filename and extension
    filename, ext = os.path.splitext(image_name)
    new_filename = f"{filename}_compressed.{output_format.lower()}"
    try:
        # save the image with the corresponding quality and optimize set to True
        img.save(new_filename, quality=quality, optimize=True, format=output_format)
    except OSError:
        # convert the image to RGB mode first
        img = img.convert("RGB")
        # save the image with the corresponding quality and optimize set to True
        img.save(new_filename, quality=quality, optimize=True, format=output_format)
    logger.info(f"[+] New file saved: {new_filename}")

    # get the new image size in bytes
    new_image_size = os.path.getsize(new_filename)
    logger.info(f"[+] Size after compression: {get_size_format(new_image_size)}")

    # calculate the saving bytes
    saving_diff = new_image_size - image_size
    logger.info(f"[+] Image size change: {saving_diff/image_size*100:.2f}% of the original image size.")
    return new_filename

def lambda_handler(event, context):
    s3_dict = event["Records"][0]["s3"]
    key_name = s3_dict["object"]["key"]
    logger.info(f"Event Notification: {event}")
    # base_s3_location = f"s3://{origin_bucket}/{key_name}"

    # PARAMS for Compress a lot of images (Migration stage)
    # images_filter_expression_total = Attr('ContentType').contains('image/') 
    # images_filter_expression_not_equal_true = And(Attr('ContentType').contains('image/'), Attr('IsCompressed').ne(True)) 
    # images_filter_expression_true = And(Attr('ContentType').contains('image/'), Attr('IsCompressed').eq(True))
    # images_projection_expression = "Id, S3Location"
    
    # images_data = scan_table(images_filter_expression_not_equal_true, images_projection_expression)
    # logger.info(f"Total de registros: {len(scan_table(images_filter_expression_total, images_projection_expression))}")
    # logger.info(f"Total de comprimidas: {len(scan_table(images_filter_expression_true, images_projection_expression))}")


    # for value in images_data:
        # key = {'Id': value["Id"]}
        # attribute_updates = {
        #     'IsCompressed': {
        #         'Value': False,
        #         'Action': 'PUT'
        #     }
        # }
        # update_table(key, attribute_updates)
        # new_s3_location = value["S3Location"].replace(origin_bucket, destiny_bucket)
        # new_s3_location = base_s3_location.replace(origin_bucket, destiny_bucket)

        # Extract the bucket name and key
        # key_name = new_s3_location.replace(f"s3://{destiny_bucket}/", "")
                
    local_path = f'/tmp/{key_name}'
    logger.info(f"Imágen descargada en {local_path}")
    local_dir = os.path.dirname(local_path)

    # Create local directories if they do not exist
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    try:
        file_name, ext = os.path.splitext(key_name)
        logger.info(origin_bucket)
        s3.download_file(origin_bucket, key_name.replace('+', ' '), local_path)
        file_path = compress_img(image_name=local_path)
        s3.upload_file(file_path, destiny_bucket, f'{file_name.replace('+', ' ')}.{output_format.lower()}')

    except Exception as e:
        logger.error(f"Error {e}")
        raise e
        
    return {
        'statusCode': 200,
        'body': json.dumps('Compressed and uploaded image successful!!')
    }