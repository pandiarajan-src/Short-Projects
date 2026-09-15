"""

"""

import json
from building_with_claude_api.utils.llm_messages import add_user_message, add_assistant_message, chat, text_from_message
from building_with_claude_api.utils.tool_datetime import get_current_datetime_schema, get_current_datetime
from anthropic import Anthropic

def run_tool(tool_name, tool_input):
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_input)


def run_tools(message):
    tool_requests = [block for block in message.content if block.type == "tool_use"]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks


def run_conversation(messages):
    while True:
        response = chat(messages, tools=[get_current_datetime_schema])

        add_assistant_message(messages, response)
        print(text_from_message(response))

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

    return messages

if __name__ == "__main__":
    messages = []
    add_user_message(
        messages,
        "What is the current time in HH:MM format? Also, what is the current time in SS format?",
    )
    run_conversation(messages)