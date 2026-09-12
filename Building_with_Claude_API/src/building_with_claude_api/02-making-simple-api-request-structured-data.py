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

def chat(messages, prompt, system_prompt=None, max_tokens=1000, model=default_model, start_sequences=None, stop_sequences=None):
    '''
    Function to send a chat request to the Anthropic API with the provided messages and prompt.
    '''
    client = Anthropic()
    add_user_message(messages, prompt)
    if start_sequences is not None:
        add_assistant_message(messages, start_sequences)

    parameters = {}
    if stop_sequences is not None:
        parameters = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "stop_sequences": [stop_sequences]
        }
    else:
        parameters = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
    if system_prompt:
        parameters["system"] = system_prompt
    final_message = None
    with client.messages.stream(**parameters) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print("\n\033[90mResponse completed.\033[0m")
        final_message = stream.get_final_message()
    return final_message


if __name__ == "__main__":
    # Initialize the messages list and system prompt
    messages = []
    system_prompt = "You are a helpful assistant, who can answer questions in simple layman's terms. Use examples and analogies to explain complex concepts. Be concise and clear in your responses."

    while True:
        prompt = input("Enter your prompt: ")
        if prompt.strip() == "":
            print("Prompt cannot be empty. Please enter a valid prompt.")
        elif prompt.strip().lower() == "exit" or prompt.strip().lower() == "quit" or prompt.strip().lower() == "bye":
            print("Exiting the program.")
            break
        else:
            # use this examples to see the difference between structured data and unstructured data
            # "what is the uv command to init, sycn and run python file without any comments just the command alone in respective format"
            response = chat(messages, prompt, system_prompt=system_prompt, start_sequences=None, stop_sequences=None)
            response = chat(messages, prompt, system_prompt=system_prompt, start_sequences="```json", stop_sequences="```")
            response = chat(messages, prompt, system_prompt=system_prompt, start_sequences="```bash", stop_sequences="```")


