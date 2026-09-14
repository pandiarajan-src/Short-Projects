"""

"""

from building_with_claude_api.utils.prompt_evaluator import PromptEvaluator
from building_with_claude_api.utils.llm_messages import add_user_message, add_assistant_message, chat


# Define and run the prompt you want to evaluate, returning the raw model output
# This function is executed once for each test case
def run_prompt(prompt_inputs):
    prompt = f"""
    Generate a one-day meal plan for an athlete that meets their dietary restrictions.

    <athlete_information> 
    - Height: {prompt_inputs["height"]} 
    - Weight: {prompt_inputs["weight"]} 
    - Goal: {prompt_inputs["goal"]} 
    - Dietary restrictions: {prompt_inputs["restrictions"]} 
    </athlete_information>

    Guidelines:
    1. Include accurate daily calorie amount
    2. Show protein, fat, and carb amounts
    3. Specify when to eat each meal
    4. Use only foods that fit restrictions
    5. List all portion sizes in grams
    6. Keep budget-friendly if mentioned

    Here is an example with a sample input and an ideal output:
    <sample_input>
    height: 170
    weight: 70
    goal: Maintain fitness and improve cholesterol levels
    restrictions: High cholesterol
    </sample_input>
    <ideal_output>
    Here is a one-day meal plan for an athlete aiming to maintain fitness and improve cholesterol levels:

    *   **Calorie Target:** Approximately 2500 calories
    *   **Macronutrient Breakdown:** Protein (140g), Fat (70g), Carbs (340g)

    **Meal Plan:**

    *   **Breakfast (7:00 AM):** Oatmeal (80g dry weight) with berries (100g) and walnuts (15g). Skim milk (240g).
        *   Protein: 15g, Fat: 15g, Carbs: 60g
    *   **Mid-Morning Snack (10:00 AM):** Apple (150g) with almond butter (30g).
        *   Protein: 7g, Fat: 18g, Carbs: 25g
    *   **Lunch (1:00 PM):** Grilled chicken breast (120g) salad with mixed greens (150g), cucumber (50g), tomato (50g), and a light vinaigrette dressing (30g). Whole wheat bread (60g).
        *   Protein: 40g, Fat: 15g, Carbs: 70g
    *   **Afternoon Snack (4:00 PM):** Greek yogurt (170g, non-fat) with a banana (120g).
        *   Protein: 20g, Fat: 0g, Carbs: 40g
    *   **Dinner (7:00 PM):** Baked salmon (140g) with steamed broccoli (200g) and quinoa (75g dry weight).
        *   Protein: 40g, Fat: 20g, Carbs: 80g
    *   **Evening Snack (9:00 PM):** Small handful of almonds (20g).
        *   Protein: 8g, Fat: 12g, Carbs: 15g

    This meal plan prioritizes lean protein sources, whole grains, fruits, and vegetables, while limiting saturated and trans fats to support healthy cholesterol levels.
    </ideal_output>
    This example meal plan is well-structured, provides detailed information on food choices and quantities, and aligns with the athlete's goals and restrictions.
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
        task_description="Write a compact, concise 1 day meal plan for a single athlete",
        #Describe the different inputs that your prompt requires
        prompt_inputs_spec={
            "height": "Height of the athlete in cm",
            "weight": "Weight of the athlete in kg",
            "goal": "Goal of the athlete (e.g., weight loss, muscle gain, endurance training)",
            "restrictions": "dietary restrictions or preferences (e.g., vegetarian, vegan, gluten-free)",
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
        The output should include:
        - Daily caloric total
        - Macronutrient breakdown
        - Meals with exact foods, portions, and timing
        """,
    )