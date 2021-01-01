# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from create_result_map import create_result_map

# DynamoDB resource and table
dynamodb = boto3.resource('dynamodb')
tbl_name = os.environ['TABLE_NAME']
table = dynamodb.Table(tbl_name)

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
        result_map = create_result_map(event=event)
        response = table.put_item(Item=result_map)
        output = {
            'statusCode': 200,
            'body': json.dumps(result_map)
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

