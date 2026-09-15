"""
LLM Messages Utility Functions
In this module, we provide utility functions to facilitate the creation and management of messages for interacting with the Anthropic API. The functions allow you to add user and assistant messages to a conversation and send chat requests to the API with specified parameters.
Functions:
- add_user_message(messages, content): Adds a user message to the messages list.
- add_assistant_message(messages, content): Adds an assistant message to the messages list.
- chat(messages, model=default_model, system=None, stop_sequences=[]): Sends a chat request to the Anthropic API with the provided messages and parameters.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import Message

# Load environment variables from .env file
load_dotenv()
default_model = os.getenv("ANTHROPIC_DEFAULT_MODEL_TO_USE", "claude-haiku-4-5-20251001")

def add_user_message(messages, message):
    '''
    Function to add a user message to the messages list.
    '''
    user_message = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)    

def add_assistant_message(messages, message):
    '''
    Function to add an assistant message to the messages list.
    '''
    assistant_message = {
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(assistant_message)

def chat_return_text(messages, model=default_model, system=None, stop_sequences=[], tools=None):
    response = chat(messages=messages, model=model, system=system, stop_sequences=stop_sequences, tools=tools)
    return response.content[0].text

def chat_return_response(messages, model=default_model, system=None, stop_sequences=[], tools=None):
    response = chat(messages=messages, model=model, system=system, stop_sequences=stop_sequences, tools=tools)
    return response

def chat(messages, model=default_model, system=None, stop_sequences=[], tools=None):
    '''
    Function to send a chat request to the Anthropic API with the provided messages and parameters.
    '''
    client = Anthropic()
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "stop_sequences": stop_sequences,
    }

    if system:
        params["system"] = system

    if tools:
        params["tools"] = tools

    message = client.messages.create(**params)
    return message

def text_from_message(message):
    return "\n".join([block.text for block in message.content if block.type == "text"])
