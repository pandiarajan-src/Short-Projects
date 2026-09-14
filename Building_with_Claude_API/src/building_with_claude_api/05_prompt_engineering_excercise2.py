"""

"""

from building_with_claude_api.utils.prompt_evaluator import PromptEvaluator
from building_with_claude_api.utils.llm_messages import add_user_message, add_assistant_message, chat


# Define and run the prompt you want to evaluate, returning the raw model output
# This function is executed once for each test case
def run_prompt(prompt_inputs):
    prompt = f"""
        Extract key topics mentioned from a passage of text from scholarly journal into a JSON array of strings. 
        
        <text>
        {prompt_inputs["content"]}
        </text>

        Follow these stpes:
        1. Closely examine the provided text
        2. Idenfity each topics mentioned in the text
        3. Add each topic to a JSON array of strings, ensuring that each topic is unique and relevant to the content of the text
        4. Respond with the JSON array of strings only, without any additional commentary or explanation.

    """

    messages = []
    add_user_message(messages, prompt)
    return chat(messages)

if __name__ == "__main__":
    # Create an instance of PromptEvaluator
    # Increase 'max_concurrentt_tasks' for greater concurrency, but beware of rate limit errors!
    evaluator = PromptEvaluator(max_concurrent_tasks=1)

    # Generate Dataset of unique test case ideas
    dataset = evaluator.generate_dataset(
        # Describe the purpose or goal of the prompt you are trying to test
        task_description="Extract topics out of a passage of text from scholarly journal into a JSON array of strings",
        #Describe the different inputs that your prompt requires
        prompt_inputs_spec={
            "content": "One paragraph of text from a scholarly journal article written in English."
        },
        # where to write the generated dataset
        output_file="dataset.json",
        #Number of test cases to generate (recommend keeping this low if you are getting rate limit errors)
        num_cases=3,
    )
    
    results = evaluator.run_evaluation(
        run_prompt_function=run_prompt,
        dataset_file="dataset.json",
        extra_criteria="""
        - Contains JSON array of strings, containing each topic mentioned in the article
        - The strings should contain only the topic, without any additional commentary or explanation
        - Response should contain the JSON array strings only, nothin else.
        """,
    )