# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

import json
import time
import boto3
import os

# Get Transcribe client and target S3 bucket
s3 = boto3.client("s3")
transcribe = boto3.client("transcribe")
target_bucket = os.environ["TARGET"]

def lambda_handler(event, context):
    """General Lambda entry point to run the Lambda function.

    Args:
        event (dict): A dictionary with the event tags coming from Connect.
        context (dict): A dictionary with context tags.

    Returns:
        output (dict): A dictionary with the status and results body.

    """
    # Log event in CloudWatch
    print(event)
    try:
        # Extract general information from the event that was triggered
        # by a put event in the corresponding S3 bucket.
        region = event["Records"][0]["awsRegion"]
        src_bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"].split(".")[0]
        media_url = 'https://s3-{}.amazonaws.com/{}/{}.wav'.format(
            region,
            src_bucket,
            key
        )
        # Run Transcribe with the corresponding setting against the key file
        # form the S3 bucket
        response = transcribe.start_transcription_job(
            TranscriptionJobName = key,
            LanguageCode = 'en-US',
            MediaFormat = 'wav',
            Media = {
                'MediaFileUri': media_url
            },
            OutputBucketName = target_bucket
        )
        # Set the output
        output = {
            'statusCode': 200,
            'body': json.dumps("Success!")
        }
    except AssertionError as error:
        print(error)
        output = {
            'statusCode': 500,
            'body': json.dumps("Internal Error!")
        }
    # Log output in CloudWatch
    print(output)
    return output
