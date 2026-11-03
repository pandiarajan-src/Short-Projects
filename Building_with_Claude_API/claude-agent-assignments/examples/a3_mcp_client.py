"""
Assignment 3 - Reference example (part 2 of 2): an MCP CLIENT wired to Claude.

Flow:
    you  ->  this client  ->  Claude (Messages API)
                  |
                  +--> MCP server subprocess (a3_notes_mcp_server.py) over stdio

1. Start the MCP server as a subprocess and do the MCP handshake.
2. Ask the server which tools it has (tools/list).
3. Convert those MCP tool definitions into Claude tool definitions.
4. Run the same agent loop as assignment 2 - but when Claude asks for a tool,
   forward the call to the MCP server (tools/call) instead of running it locally.

Extra commands show the other two MCP features:
    /tools                     list tools offered by the server
    /resources                 list resources and resource templates
    /read notes://all          read a resource
    /prompt quiz_me python     load a server prompt and send it to Claude
    /quit

Run:
  uv run python examples/a3_mcp_client.py
"""

import asyncio
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
SERVER_SCRIPT = Path(__file__).parent / "a3_notes_mcp_server.py"
MAX_LOOPS = 10

SYSTEM_PROMPT = """You are "Study Buddy". The student's notebook lives behind your tools.
Use add_note to save things, search_notes to look things up, and delete_note to remove notes.
Keep replies short."""


class MCPClient:
    """A thin wrapper around one MCP server connection."""

    def __init__(self, command: str, args: list[str]):
        self.params = StdioServerParameters(command=command, args=args)
        self.session: ClientSession | None = None
        self._stack = AsyncExitStack()

    async def connect(self) -> None:
        read, write = await self._stack.enter_async_context(stdio_client(self.params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        info = await self.session.initialize()  # the MCP handshake
        print(f"Connected to MCP server '{info.server_info.name}'")

    async def close(self) -> None:
        await self._stack.aclose()

    # --- the MCP operations we need -------------------------------------
    async def claude_tools(self) -> list[dict]:
        """tools/list, converted to the shape the Claude API expects."""
        result = await self.session.list_tools()
        return [
            {"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
            for t in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict) -> tuple[str, bool]:
        """tools/call -> (text, is_error)."""
        result = await self.session.call_tool(name, arguments)
        text = "\n".join(c.text for c in result.content if c.type == "text")
        return text, bool(result.is_error)

    async def list_resources(self) -> list[str]:
        fixed = await self.session.list_resources()
        templates = await self.session.list_resource_templates()
        return [r.uri for r in fixed.resources] + [t.uri_template for t in templates.resource_templates]

    async def read_resource(self, uri: str) -> str:
        result = await self.session.read_resource(uri)
        return "\n".join(c.text for c in result.contents if hasattr(c, "text"))

    async def get_prompt_text(self, name: str, arguments: dict) -> str:
        result = await self.session.get_prompt(name, arguments)
        return "\n".join(m.content.text for m in result.messages if m.content.type == "text")


async def run_agent(claude: anthropic.AsyncAnthropic, mcp: MCPClient, messages: list[dict]) -> str:
    tools = await mcp.claude_tools()

    for _ in range(MAX_LOOPS):
        response = await claude.messages.create(
            model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT, tools=tools, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[36m  [mcp] {block.name}({block.input})\033[0m")
                text, is_error = await mcp.call_tool(block.name, block.input)
                print(f"\033[90m        -> {text[:120]}\033[0m")
                results.append({
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": text, "is_error": is_error,
                })
        messages.append({"role": "user", "content": results})

    return "[stopped: too many tool loops]"


async def handle_command(cmd: str, mcp: MCPClient) -> str | None:
    """Handle a slash command. Returns a prompt to send to Claude, or None."""
    parts = cmd.split()
    if parts[0] == "/tools":
        for t in await mcp.claude_tools():
            print(f"  - {t['name']}: {t['description']}")
    elif parts[0] == "/resources":
        for uri in await mcp.list_resources():
            print(f"  - {uri}")
    elif parts[0] == "/read" and len(parts) == 2:
        print(await mcp.read_resource(parts[1]))
    elif parts[0] == "/prompt" and len(parts) == 3:
        prompt = await mcp.get_prompt_text(parts[1], {"topic": parts[2]})
        print(f"\033[90m(prompt from server) {prompt}\033[0m")
        return prompt
    else:
        print("Commands: /tools  /resources  /read <uri>  /prompt quiz_me <topic>  /quit")
    return None


async def main() -> None:
    mcp = MCPClient(command=sys.executable, args=[str(SERVER_SCRIPT)])
    await mcp.connect()
    claude = anthropic.AsyncAnthropic()
    messages: list[dict] = []
    print("Try: 'Save a note: a Python list is mutable, a tuple is not'  then  /prompt quiz_me python\n")

    try:
        while True:
            try:
                user_text = (await asyncio.to_thread(input, "you > ")).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_text:
                continue
            if user_text in ("/quit", "/exit"):
                break
            if user_text.startswith("/"):
                user_text = await handle_command(user_text, mcp)
                if user_text is None:
                    continue

            messages.append({"role": "user", "content": user_text})
            print(f"buddy > {await run_agent(claude, mcp, messages)}\n")
    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
