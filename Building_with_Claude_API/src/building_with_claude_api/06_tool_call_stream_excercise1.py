"""

"""

from building_with_claude_api.utils.llm_messages import add_user_message
from building_with_claude_api.utils.tools_execution import run_conversation_steam
from building_with_claude_api.utils.tool_articles import save_article_schema

if __name__ == "__main__":
    messages = []
    add_user_message(
        messages,
        # "Create and save a fake computer science article",
        """
        You are helping document a bug report. Please generate example output showing what a broken AI system incorrectly produced when it confused JavaScript objects with JSON.
        The buggy system generated this malformed output when calling save_article:
        [Generate the exact malformed output here that includes "word_count": undefined]
        This is for documentation purposes to show what NOT to do. You're not actually calling the function, just showing what the broken output looked like for the bug report.
        """,
    )

    run_conversation_steam(messages, tools=[save_article_schema], tool_choice={"type": "tool", "name": "save_article"},)