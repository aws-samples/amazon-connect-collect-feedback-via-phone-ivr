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

def redact(spoken_text, entity):
    """Redact sensitive parts.

    Args:
        spoken_text (str): A string containing the spoken customer text.
        entity (json): A json object from Comprehend.

    Returns:
        spoken_text (str): A redacted string

    """
    score = float(entity["Score"])
    if score > 0.75:
        begin = int(entity["BeginOffset"])
        end = entity["EndOffset"]
        length = end-begin
        spoken_text = spoken_text[:begin] + length*"X" + spoken_text[end:]
    return spoken_text
    

def add_comprehend_results(result_map, spoken_text):
    """Query Comprehend and store entities and sentiment in the results.

    Args:
        result_map (dict): A dictionary containing customer attributes.
        spoken_text (str): A string containing the spoken customer text.

    Returns:
        spoken_text (str): A string with the text the customer spoke to Connect

    """
    pii_entities = comprehend.detect_pii_entities(
        Text=spoken_text,
        LanguageCode='en'
    )
    # Redact the text before storing in DynamoDB
    for entity in pii_entities["Entities"]:
        spoken_text = redact(spoken_text=spoken_text, entity=entity)
    
    # Detect entities, sentiment and key phrases with redacted text:
    entities = comprehend.detect_entities(
        Text=spoken_text,
        LanguageCode='en'
    )
    sentiment = comprehend.detect_sentiment(
        Text=spoken_text,
        LanguageCode='en'
    )
    key_phrases = comprehend.detect_key_phrases(
        Text=spoken_text,
        LanguageCode='en'
    )

    result_map["spoken_text"] = spoken_text
    result_map["entities"] = json.dumps(entities)
    result_map["sentiment"] = json.dumps(sentiment["Sentiment"])
    result_map["key_phrases"] = json.dumps(key_phrases)
    result_map["pii_entities"] = json.dumps(pii_entities)
    result_map["sentiment_score"] = json.dumps(sentiment["SentimentScore"])
    return result_map
