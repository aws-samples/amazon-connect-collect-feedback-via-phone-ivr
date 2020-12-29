# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

import json

from add_comprehend_results import add_comprehend_results
from query_table import table, query_table
from read_transcripts import read_transcripts

def lambda_handler(event, context):
    """General Lambda entry point to run the Lambda function.

    Args:
        event (dict): A dictionary with the event tags coming from Amazon Connect.
        context (dict): A dictionary with context tags.

    Returns:
        output (dict): A dictionary with the status and results body.

    """
    # Log event in CloudWatch
    print(event)
    # Get UID from the JSON file and the src S3 bucket
    guid = event["Records"][0]["s3"]["object"]["key"].split(".")[0]
    src_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    # Read transcript from S3
    spoken_text = read_transcripts(src_bucket=src_bucket, guid=guid)
    # Query DynamoDB
    guid = guid.split("-call-recording")[0]
    result_map = query_table(guid=guid)
    try:
        output = {
            'statusCode': 200,
            'body': json.dumps("No records available!")
        }
        if len(result_map) > 0:
            # Add results from comprehend
            result_map = add_comprehend_results(
                result_map=result_map,
                spoken_text=spoken_text
            )
            # Write to DynamoDB
            response = table.put_item(Item=result_map)
            output['body'] = json.dumps(result_map)
    except AssertionError as error:
        print(error)
        output = {
            'statusCode': 500,
            'body': json.dumps("Internal Error!")
        }
    # Log output in CloudWatch
    print(output)
    return output
