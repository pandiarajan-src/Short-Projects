"""
This script demonstrates how to run evaluations on the generated prompt dataset.
The evaluation is both model and code based, and does not include human evaluation. 
The script will run the prompts in the dataset, grade the results, and save the evaluation results to a JSON file.
"""

import os
import json
import re
from statistics import mean
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

def run_prompts(test_case):
    """
    Merge the prompt and test case input, then return the results
    """
    prompt = f"""
        Please solve the following task and provide the expected output in {test_case['format'].lower()} format.
        {test_case["task"]},
    """
    messages = []
    add_user_message(messages, prompt)
    output = chat(messages)
    return output

def grade_by_model(test_case, output):
    """
    Grade the output by comparing it to the expected output in the test case with the help of Model.
    """
    # Create a prompt to ask the model to grade the output
    grading_prompt = f"""
        You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

        Original Task:
        <task>
        {test_case["task"]}
        </task>

        Solution to Evaluate:
        <solution>
        {output}
        </solution>

        Solutioin Criteria to Evaluate Against:
        <criteria>
        {test_case["solution_criteria"]}
        </criteria>

        Output Format
        Provide your evaluation as a structured JSON object with the following fields, in this specific order:
        - "strengths": An array of 1-3 key strengths
        - "weaknesses": An array of 1-3 key areas for improvement
        - "reasoning": A concise explanation of your overall assessment
        - "score": A number between 1-10

        Respond with JSON. Keep your response concise and direct.
        Example response shape:
        {{
            "strengths": string[],
            "weaknesses": string[],
            "reasoning": string,
            "score": number
        }}
    """
    messages = []
    add_user_message(messages, grading_prompt)
    add_assistant_message(messages, "```json")

    evaluation_output = chat(messages, stop_sequences=["```"])
    return parse_model_json(evaluation_output)


def parse_model_json(text):
    """
    Parse JSON returned by the model, repairing invalid backslash escapes
    (e.g. from embedded code containing regex or file paths like "\\d" or
    "C:\\path") that are common in model output but not valid JSON escapes.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
        return json.loads(repaired)


def run_test_cases(test_case):
    """
    Call run_prompt(), then grade the results
    """
    output = run_prompts(test_case)

    # Grade the results
    model_grade = grade_by_model(test_case, output)
    score = model_grade.get("score", 0)  # Default to 0 if score is not present
    reasoning = model_grade.get("reasoning", "")

    return{
        "output": output,
        "reasoning": reasoning,
        "score": score,
        "test_case": test_case
    }

def run_evaluations(dataset):
    """
    Load the datasets and calls the run_test_case() funciton for each test case, then return the results
    """
    results = []

    for test_case in dataset:
        result = run_test_cases(test_case)
        results.append(result)

    average_score = mean([result["score"] for result in results])
    print(f"=======Average Score across all test cases: {average_score:.2f}=======")

    return results

if __name__ == "__main__":
    # Load the dataset from a JSON file
    with open("prompt_eval_dataset.json", "r") as f:
        dataset = json.load(f)

    # Run evaluations on the dataset
    evaluation_results = run_evaluations(dataset)
    print("=== Evaluation results ===")
    print(json.dumps(evaluation_results, indent=4))

    # Save the evaluation results to a JSON file
    with open("evaluation_results.json", "w") as f:
        json.dump(evaluation_results, f, indent=4)