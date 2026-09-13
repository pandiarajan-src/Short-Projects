"""
This script demonstrates how to build a prompt evaluation framework using the Anthropic API and the Claude model.
It uses the `anthropic` Python package to send prompts and receive responses, allowing you to evaluate the quality of prompts and their corresponding responses.
Make sure to set your API key in the .env file before running this script.
Usage: python 03_prompt_evals.py
"""

from http import client
import os
import json
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

def chat(messages, model=default_model, system=None, temperature=1.0, stop_sequences=[]):
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

def generate_dataset():
    prompt = """
        Generate a evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
        that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects,
        each representing task that requires Python, JSON, or a Regex to complete.

        Example output:
        ```json
        [
            {
                "task": "Description of task",
                "format": "python/json/regex",
                "solution_criteria": "Description of what the solution should achieve"
            },
            ...additional
        ]
        ```

        * Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
        * Focus on tasks that do not require writing much code

        Please generate 3 objects.
    """
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")
    response_text = chat(messages, stop_sequences=["```"])

    # Parse the JSON response
    dataset = json.loads(response_text)
    return dataset

if __name__ == "__main__":
    # Generate the dataset
    dataset = generate_dataset()
    print("Generated Dataset:")
    print(json.dumps(dataset, indent=4))

    # Write the dataset to a JSON file, deleting any existing file with the same name
    if os.path.exists("prompt_eval_dataset.json"):
        os.remove("prompt_eval_dataset.json")
    with open("prompt_eval_dataset.json", "w") as f:
        json.dump(dataset, f, indent=4)
