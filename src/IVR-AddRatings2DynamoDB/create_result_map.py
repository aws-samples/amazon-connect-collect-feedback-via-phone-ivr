# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

from datetime import datetime

def create_result_map(event):
    """Extract the Attributes and Contact ID from the customer call to be
    stored in DynamoDB.

    Args:
        event (dict): A dictionary with the events sent from Amazon Connect.

    Returns:
        result_map (dict): A dictionary with the attributes, contact id and dttm

    """
    result_map = event["Details"]["ContactData"]["Attributes"]
    result_map["guid"] = event["Details"]["ContactData"]["ContactId"]
    result_map["dttm"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result_map
