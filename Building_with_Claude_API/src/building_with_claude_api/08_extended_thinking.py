"""
"""

from building_with_claude_api.utils.llm_messages import (
    add_user_message,
    text_from_message,
    thinking_chat,
)

# Magic string to trigger redacted thinking
thinking_test_str = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"


if __name__ == "__main__":
    user_query = input("Enter your user query: =>")
    messages = []
    add_user_message(messages, user_query)
    # Normal thinking chat
    response = thinking_chat(messages)
    print(response)

    # Redated use the special string and it 
    add_user_message(messages, thinking_test_str)
    # Normal thinking chat
    response = thinking_chat(messages)
    print(response)    
