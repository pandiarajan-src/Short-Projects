"""
LLM Messages Utility Functions
In this module, we provide utility functions to facilitate the creation and management of messages for interacting with the Anthropic API. The functions allow you to add user and assistant messages to a conversation and send chat requests to the API with specified parameters.
Functions:
- add_user_message(messages, content): Adds a user message to the messages list.
- add_assistant_message(messages, content): Adds an assistant message to the messages list.
- chat(messages, model=default_model, system=None, stop_sequences=[]): Sends a chat request to the Anthropic API with the provided messages and parameters.
"""

import base64
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import Message

# Load environment variables from .env file
load_dotenv()
default_model = os.getenv("ANTHROPIC_DEFAULT_MODEL_TO_USE", "claude-haiku-4-5-20251001")

def get_default_model():
    return default_model

def add_image_to_user_message(messages, image_path, text=None):
    if not os.path.exists(image_path):
        return "FAIL: Image file doesn't exist"
    with open(image_path, "rb") as f:
        image_bytes = base64.standard_b64encode(f.read()).decode("utf-8")
        # Build Image block
        image_block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_bytes,
            }
        }
        content = [image_block]
        if text:
            content.append({"type": "text", "text": text})
        user_message = {
            "role": "user",
            "content": content,
        }
        messages.append(user_message)
    return "SUCCESS: added the image block to message"


def add_user_message(messages, message):
    '''
    Function to add a user message to the messages list.
    Add a user turn. Accepts a Message object, a list of content blocks, or a plain string.
    Always stores content as a list of blocks.
    '''
    if isinstance(message, Message):
        content = message.content
    elif isinstance(message, list):
        content = message
    else:
        content = [{"type": "text", "text": message}]

    messages.append({"role": "user", "content": content})

def add_assistant_message(messages, message):
    '''
    Function to add an assistant message to the messages list.
    '''
    assistant_message = {
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(assistant_message)


def add_assistant_message(messages, message):
    '''
    Function to add an assistant message to the messages list.
    '''
    if isinstance(message, list):
        assistant_message = {
            "role": "assistant",
            "content": message,
        }
    elif hasattr(message, "content"):
        content_list = []
        for block in message.content:
            if block.type == "text":
                content_list.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_list.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
        assistant_message = {
            "role": "assistant",
            "content": content_list,
        }
    else:
        # String messages need to be wrapped in a list with text block
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": message}],
        }
    messages.append(assistant_message)    


def chat(messages, model=default_model, system=None, stop_sequences=[], tools=None):
    '''
    Function to send a chat request to the Anthropic API with the provided messages and parameters.
    '''
    response = chat_internal(messages=messages, model=model, system=system, stop_sequences=stop_sequences, tools=tools)
    return response.content[0].text


def chat_internal(messages, model=default_model, system=None, stop_sequences=[], tools=None, thinking=False, thinking_budget=1024):
    '''
    Function to send a chat request to the Anthropic API with the provided messages and parameters.
    '''
    client = Anthropic()
    max_tokens = thinking_budget + 1024 if thinking else 1024
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "stop_sequences": stop_sequences,
    }

    if thinking:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

    if system:
        params["system"] = system

    if tools:
        params["tools"] = tools

    message = client.messages.create(**params)
    return message

def chat_stream(messages, model=default_model, system=None, stop_sequence=[], tools=None, tool_choice=None, betas=[]):
    '''
    Function to send a chat request to Anthropic API and stream the return data
    '''
    client = Anthropic()
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "stop_sequences": stop_sequence,
    }

    if tool_choice:
        params["tool_choice"] = tool_choice

    if tools:
        params["tools"] = tools

    if system:
        params["system"] = system

    if betas:
        params["betas"] = betas

    return client.beta.messages.stream(**params)


def thinking_chat(
    messages,
    model=default_model,
    system=None,
    stop_sequences=[],
    tools=None,
    thinking=True,
    thinking_budget=1024,
):
    """
    Function to send a chat request to the Anthropic API with thinking feature and provided messages and parameters.
    """
    return chat_internal(messages=messages, model=model, system=system,
                         stop_sequences=stop_sequences, tools=tools, 
                         thinking=thinking, thinking_budget=thinking_budget)


def text_from_message(message):
    return "\n".join([block.text for block in message.content if block.type == "text"])
