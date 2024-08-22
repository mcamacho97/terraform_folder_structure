from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools import Tracer

import awswrangler as wr
import os
import pandas as pd
import boto3
import numpy as np
import json
formatter = LambdaPowertoolsFormatter(utc=False, log_record_order=["message"])
logger = Logger(logger_formatter=formatter, utc=False)
tracer = Tracer()

ssm = parameters.SSMProvider()
bucket = ssm.get(os.environ["s3_bucket_parameter"], 300)
key = "attachments_files/final_attachments.csv"
s3 = boto3.client("s3")


# dynamodb = boto3.resource("dynamodb")
# table = dynamodb.Table("izum-attachments")

dynamodb = boto3.client('dynamodb')

def convert_to_string_dynamo_values(x):
    # x = json.loads(x)
    
    if not isinstance(x, dict):
        return x
    if x.get("S"):
        pass
    else:
        return ""
    return x["S"]

def lambda_handler(event, context):
    scan_params = {
        "TableName": "izum-attachments"
    }

    all_items = []

    # Perform the initial scan
    response = dynamodb.scan(**scan_params)

    # Collect the first page of items
    all_items.extend(response["Items"])

    # Check if there are more pages
    while "LastEvaluatedKey" in response:
        # Update the scan parameters with the last evaluated key
        scan_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]

        # Perform the next scan
        response = dynamodb.scan(**scan_params)

        # Collect the next page of items
        all_items.extend(response["Items"])

    # attachments = table.scan()
    # attachments_df = pd.DataFrame(attachments["Items"])
    attachments_df = pd.DataFrame(all_items)
    # print(attachments_df)
    # attachments_df.fillna({"S":""})
    print(attachments_df.dtypes)
    for column in attachments_df:
        
        attachments_df[column] = attachments_df[column].apply(convert_to_string_dynamo_values)
    
    dynamo_items = wr.s3.to_csv(
        df=attachments_df,
        path=f"s3://{bucket}/attachments_files/dynamo_attachments.csv",
        index=False,
    )
    df = wr.s3.read_csv(
            path=f"s3://{bucket}/attachments_files/attachments.csv", index_col=False, encoding='utf8'
        )
    if len(attachments_df) > 0:

        
        merged_df = df.merge(attachments_df, how="left", on="Id")

        # print(len(df))
        # print(len(merged_df))
        merged_df["URL_y"] = merged_df["URL_y"].replace(np.nan, "0")

        # print(merged_df.columns)

        merged_df_new = merged_df.loc[merged_df["URL_y"] == "0"]

        for value in merged_df_new.columns:
            if "_y" in value:
                merged_df_new = merged_df_new.drop(columns=[value])
            if "_x" in value:
                merged_df_new = merged_df_new.rename(
                    columns={value: value.replace("_x", "")}
                )

        # print(len(merged_df_new))
        # print(merged_df_new.columns)
        # merged_df_new = merged_df_new.drop(1, axis=0)
        new_csv = wr.s3.to_csv(
            df=merged_df_new,
            path=f"s3://{bucket}/{key}",
            index=False,
        )
        return {
            "base_csv_count": len(df),
            "dynamo_attachments_count": len(attachments_df),
            "new_csv_count": len(merged_df_new),
            "key": key
        }
    else:
        new_csv = wr.s3.to_csv(
            df=df,
            path=f"s3://{bucket}/{key}",
            index=False,
        )
        
        return {
            "base_csv_count": len(df),
            "dynamo_attachments_count": len(attachments_df),
            "new_csv_count": len(df),
            "key": key
        }
