# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB resource and table
dynamodb = boto3.resource('dynamodb')
tbl_name = os.environ['TABLE_NAME']
table = dynamodb.Table(tbl_name)

def query_table(guid):
    """Get results from DynamoDB table for one specific GUID.

    Args:
        guid (str): A string containing the unique ID.

    Returns:
        result_map (dict): A dictionary with the content from the table.

    Examples:

        >>> data = query_table(guid='f39caef7-94a7-4ca4-8b59-6811055672f0')

    """
    result_map = dict()
    try:
        result_map = table.query(
            KeyConditionExpression=Key('guid').eq(guid)
        )["Items"][0]
    except:
        print("Not data found!")
    return result_map
