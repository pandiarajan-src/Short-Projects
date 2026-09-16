"""

"""

from building_with_claude_api.utils.llm_messages import add_user_message
from building_with_claude_api.utils.tools_execution import run_conversation

def test_one_tool_2_get_date_time():
    messages = []
    add_user_message(
        messages,
        "What is the current date and time in HH:MM:SS format?",
    )
    return messages

def test_two_tool_2_run_couple_tools():
    messages = []
    add_user_message(
        messages,
        "Set a reminder for my doctors appointment. Its 177 days after Jan 1st, 2050.",
    )
    return messages


if __name__ == "__main__":
    messages = test_two_tool_2_run_couple_tools()
    run_conversation(messages)