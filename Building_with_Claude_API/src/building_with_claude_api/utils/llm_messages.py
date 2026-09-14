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

# Load environment variables from .env file
load_dotenv()
default_model = os.getenv("ANTHROPIC_DEFAULT_MODEL_TO_USE", "claude-haiku-4-5-20251001")

def add_user_message(messages, content):
    '''
    Function to add a user message to the messages list.
    '''
    messages.append({"role": "user", "content": content })

def add_assistant_message(messages, content):
    '''
    Function to add an assistant message to the messages list.
    '''
    messages.append({"role": "assistant", "content": content })

def chat(messages, model=default_model, system=None, stop_sequences=[]):
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

    message = client.messages.create(**params)
    return message.content[0].text
