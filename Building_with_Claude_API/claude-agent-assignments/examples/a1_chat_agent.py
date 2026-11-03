"""
Assignment 1 - Reference example: a small chat agent with the Claude API.

What this shows:
  * Creating an Anthropic client (reads ANTHROPIC_API_KEY from .env)
  * A system prompt that gives the agent a persona
  * Conversation memory: the API is stateless, so WE keep the message history
  * Streaming the answer token-by-token
  * Reading token usage from the final message
  * Simple slash commands (/reset, /usage, /quit)

Run:
  uv run python examples/a1_chat_agent.py
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

SYSTEM_PROMPT = """You are "Study Buddy", a friendly tutor for college students.
- Explain concepts simply, using a short example or analogy.
- Keep answers under 150 words unless the student asks for more detail.
- If you are not sure about something, say so instead of guessing."""


class ChatAgent:
    """Keeps the conversation history and talks to Claude."""

    def __init__(self, client: anthropic.Anthropic, model: str, system: str):
        self.client = client
        self.model = model
        self.system = system
        self.messages: list[dict] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def reset(self) -> None:
        self.messages = []

    def send(self, user_text: str) -> str:
        """Send one user turn, stream the reply to the terminal, and remember it."""
        self.messages.append({"role": "user", "content": user_text})

        with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=self.system,
            messages=self.messages,
            # Chat is a light task, so low effort keeps it fast and cheap.
            output_config={"effort": "low"},
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            print()
            final = stream.get_final_message()

        # Store the whole content list (not just the text) so nothing is lost.
        self.messages.append({"role": "assistant", "content": final.content})

        self.total_input_tokens += final.usage.input_tokens
        self.total_output_tokens += final.usage.output_tokens

        if final.stop_reason == "max_tokens":
            print("\033[33m[warning] reply was cut off - raise max_tokens]\033[0m")

        return "".join(b.text for b in final.content if b.type == "text")


def main() -> None:
    agent = ChatAgent(anthropic.Anthropic(), MODEL, SYSTEM_PROMPT)
    print(f"Study Buddy ({MODEL}). Commands: /reset  /usage  /quit\n")

    while True:
        try:
            user_text = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_text:
            continue
        if user_text in ("/quit", "/exit"):
            break
        if user_text == "/reset":
            agent.reset()
            print("(conversation cleared)\n")
            continue
        if user_text == "/usage":
            print(
                f"turns={len(agent.messages) // 2}  "
                f"input_tokens={agent.total_input_tokens}  "
                f"output_tokens={agent.total_output_tokens}\n"
            )
            continue

        print("buddy > ", end="")
        try:
            agent.send(user_text)
        except anthropic.AuthenticationError:
            print("\nInvalid API key - check ANTHROPIC_API_KEY in your .env file.")
            break
        except anthropic.RateLimitError:
            print("\nRate limited - wait a few seconds and try again.")
            agent.messages.pop()  # drop the unanswered user turn
        except anthropic.APIConnectionError:
            print("\nNetwork error - check your internet connection.")
            agent.messages.pop()
        print()


if __name__ == "__main__":
    main()
