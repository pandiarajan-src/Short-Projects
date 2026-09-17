"""

"""

from building_with_claude_api.utils.llm_messages import add_user_message, chat
from building_with_claude_api.utils.tool_inbuilt_schemas import web_search_schema

if __name__ == "__main__":
    messages = []
    add_user_message(
        messages,
        "What's the best exercise for gaining leg muscle?"
    )
    response = chat(messages, tools=[web_search_schema])
    print(response)

