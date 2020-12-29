# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""
import json
import boto3

# Get S3 client
s3 = boto3.client("s3")

def read_transcripts(src_bucket, guid):
    """Get the transcripts JSON file from the S3 bucket.

    Args:
        src_bucket (str): A string containing the S3 source bucket.
        guid (str): A string containing the unique ID.

    Returns:
        spoken_text (str): A string with the text the customer spoke to Connect

    Examples:

        >>> data = query_table(guid='f39caef7-94a7-4ca4-8b59-6811055672f0')

    """
    try:
        spoken_text = json.loads(
            s3.get_object(
                Bucket=src_bucket,
                Key=guid+".json"
            )["Body"].read()
        )
        spoken_text = spoken_text["results"]["transcripts"][0]["transcript"]
    except:
        spoken_text = ""
    return spoken_text
