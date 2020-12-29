# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

import json
import boto3

# Get comprehend client
comprehend = boto3.client("comprehend")

def add_comprehend_results(result_map, spoken_text):
    """Query Comprehend and store entities and sentiment in the results.

    Args:
        result_map (dict): A dictionary containing customer attributes.
        spoken_text (str): A string containing the spoken customer text.

    Returns:
        spoken_text (str): A string with the text the customer spoke to Connect

    """
    entities = comprehend.detect_entities(
        Text=spoken_text,
        LanguageCode='en'
    )
    sentiment = comprehend.detect_sentiment(
        Text=spoken_text,
        LanguageCode='en'
    )
    result_map["spoken_text"] = spoken_text
    result_map["entities"] = json.dumps(entities["Entities"])
    result_map["sentiment"] = json.dumps(sentiment["Sentiment"])
    result_map["sentiment_score"] = json.dumps(sentiment["SentimentScore"])
    return result_map
