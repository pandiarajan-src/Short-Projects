# Build Systems using ChatGPT API

Worked through the [deeplearning.ai](https://www.deeplearning.ai) short course ["Building Systems with the ChatGPT API"](https://www.deeplearning.ai/short-courses/building-systems-with-chatgpt/). One notebook per lesson, learning how to build multi-step LLM systems with OpenAI APIs.

## Lessons

- `L1_basics_chatgpt_api.ipynb` — API basics
- `L2_evaluate_inputs_classification.ipynb` — classifying inputs
- `L3_evaluate_inputs_moderation.ipynb` — moderating inputs
- `L4_process_inputs_Chain_of_thought_reasoning.ipynb` — chain-of-thought reasoning
- `L5_process_inputs_Chaining_Prompts.ipynb` — chaining prompts
- `L6_check_outputs.ipynb` — checking model outputs
- `L7_end_to_end_example.ipynb` — end-to-end example (customer service)
- `L8_evaluate1_model.ipynb` — evaluating the model
- `L9_evaluate2_ruberic_expert.ipynb` — evaluating with a rubric / expert

Supporting files: `products.json` (sample product catalog) and `utils.py` (shared helpers).

## Setup

```bash
pip install -r requirements.txt  # or the course's install instructions
```

Set your OpenAI API key, then open the notebooks (L1 first, L9 last).

## Credits

Taught by [Andrew Ng](https://www.andrewng.org) and [Isha Fulford](https://www.coursera.org/instructor/~137229549), who collaborated with [deeplearning.ai](https://www.deeplearning.ai) to create the course. All credit goes to them.