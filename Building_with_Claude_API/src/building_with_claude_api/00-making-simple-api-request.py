"""
This script demonstrates how to make a simple API request to the Anthropic API using the Claude model.
It uses the `anthropic` Python package to send a prompt and receive a response.
Make sure to set your API key in the .env file before running this script.
Usage: python 00-making-simple-api-request.py
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
    messages.append({
        "role": "user",
        "content": content
    })

def add_assistant_message(messages, content):
    '''
    Function to add an assistant message to the messages list.
    '''
    messages.append({
        "role": "assistant",
        "content": content
    })

def chat(messages, prompt, system_prompt=None, max_tokens=1000, model=default_model):
    '''
    Function to send a chat request to the Anthropic API with the provided messages and prompt.
    '''
    client = Anthropic()
    add_user_message(messages, prompt)
    parameters = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system_prompt:
        parameters["system"] = system_prompt
    response = client.messages.create(**parameters)
    print(f"\033[90m{response}\033[0m")
    return response.content[0].text


if __name__ == "__main__":
    # Initialize the messages list and system prompt
    messages = []
    system_prompt = "You are a helpful assistant, who can answer questions in simple layman's terms. Use examples and analogies to explain complex concepts. Be concise and clear in your responses."

    while True:
        prompt = input("Enter your prompt: ")
        if prompt.strip() == "":
            print("Prompt cannot be empty. Please enter a valid prompt.")
        elif prompt.strip().lower() == "exit" or prompt.strip().lower() == "quit":
            print("Exiting the program.")
            break
        else:
            response = chat(messages, prompt, system_prompt=system_prompt)
            print(f"Answer: {response}")
            add_assistant_message(messages, response)
