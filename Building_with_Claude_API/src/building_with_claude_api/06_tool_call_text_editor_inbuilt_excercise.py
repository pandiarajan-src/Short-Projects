"""

"""

from building_with_claude_api.utils.llm_messages import add_user_message
from building_with_claude_api.utils.tools_execution import run_conversation
from building_with_claude_api.utils.tool_text_editor import get_text_edit_schema

if __name__ == "__main__":
    # msgs = [
    #     "Create a file called hello.py that prints 'Hello, World! in current directory, if file already exists delete it first and then create the file",
    #     "Show me the contents of hello.py",
    #     "In hello.py (in current directory), change 'Hello, World!' to 'Hello, Claude!' and show me the content of hello.py",
    #     "Add a comment at the top of hello.py (in current directory) explaining what the script does and show me the content of hello.py",
    #     "Undo your last change to hello.py (in current directory) and show me the content of hello.py"
    # ]
    msgs = [
        "Create a Python script called calculator.py with add and subtract functions, then add a multiply function to it, then show me the final file.",
        "Create a file notes.txt with three lines of placeholder text, replace the second line, and then view the file to confirm.",
        "List the files in the current directory, then create a README.md summarizing what's here."
    ]

    for msg in msgs:
        messages = []
        print("="*25)
        print(f"user input: {msg}")
        print("="*25)
        add_user_message(
            messages,
            msg
        )
        run_conversation(messages)
        print("="*25)

