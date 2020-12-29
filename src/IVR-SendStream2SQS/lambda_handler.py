# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

import os
import json
import boto3

# Get SQS client and queue url
queue_url = os.environ['QUEUE_URL']
client = boto3.client('sqs')

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
        # Using the input event you need to extract the StreamARN, ContactId,
        # StartFragmentNumber and Address and then input these into the
        # corresponding message attributes. Note that the queue url is stored in
        # a environmental variable.
        response = client.send_message(
            MessageBody = json.dumps(event, separators=(',', ':')),
            DelaySeconds = 45,
            MessageAttributes = {
                'StreamARN': {
                    'StringValue': event["Details"]["ContactData"]["MediaStreams"]["Customer"]["Audio"]["StreamARN"],
                    'DataType': 'String'
                },
                'ContactId': {
                    'StringValue': event["Details"]["ContactData"]["ContactId"],
                    'DataType': 'String'
                },
                'StartFragmentNumber': {
                    'StringValue': event["Details"]["ContactData"]["MediaStreams"]["Customer"]["Audio"]["StartFragmentNumber"],
                    'DataType': 'String'
                },
                'CustomerEndpointAddress': {
                    'StringValue': event["Details"]["ContactData"]["CustomerEndpoint"]["Address"],
                    'DataType': 'String'
                },
                'SystemEndpointAddress': {
                    'StringValue': event["Details"]["ContactData"]["SystemEndpoint"]["Address"],
                    'DataType': 'String'
                }
            },
            QueueUrl = queue_url
        )
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
