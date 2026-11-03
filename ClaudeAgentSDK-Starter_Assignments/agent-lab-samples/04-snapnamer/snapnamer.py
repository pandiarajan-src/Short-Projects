#!/usr/bin/env python3
"""SnapNamer - a Claude Agent SDK agent that looks at images and gives them descriptive file names.

Custom tools:
  list_files    - every file in the folder, marked image / not-image (by content, not just extension)
  view_image    - returns the actual image so Claude can see it
  rename_image  - rename to a kebab-case description; keeps the original extension exactly
                  (IMG_3001.PNG stays .PNG), refuses non-images and refuses name clashes

Usage:
  python snapnamer.py sample-images.zip            # unzip a fresh copy into ./work and rename
  python snapnamer.py ./work/sample-images --dry-run
"""

import argparse
import asyncio
import base64
import re
import shutil
import sys
import zipfile
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

IMAGE_SIGNATURES = [
    (b"\x89PNG", 0, "image/png"),
    (b"\xff\xd8\xff", 0, "image/jpeg"),
    (b"GIF8", 0, "image/gif"),
    (b"WEBP", 8, "image/webp"),
]
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){1,7}$")


def image_type(path: Path) -> str | None:
    head = path.read_bytes()[:16]
    for magic, offset, mime in IMAGE_SIGNATURES:
        if head[offset:offset + len(magic)] == magic:
            return mime
    return None


def text(msg: str, error: bool = False) -> dict:
    result = {"content": [{"type": "text", "text": msg}]}
    if error:
        result["is_error"] = True
    return result


def build_tools(root: Path, dry_run: bool, log: list):
    taken: set[str] = {p.name.lower() for p in root.iterdir()}
    renamed: set[str] = set()

    def find(name: str) -> Path | None:
        p = (root / name).resolve()
        return p if p.parent == root and p.is_file() else None

    @tool("list_files", "List every file in the folder and whether it is really an image.", {})
    async def list_files(args):
        lines = []
        for p in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if p.is_file():
                kind = image_type(p) or "NOT AN IMAGE - skip"
                lines.append(f"- {p.name!r}  {kind}  {p.stat().st_size}B")
        return text("\n".join(lines))

    @tool("view_image", "Look at one image.", {"name": str})
    async def view_image(args):
        p = find(args["name"])
        if not p:
            return text(f"No such file: {args['name']!r}", error=True)
        mime = image_type(p)
        if not mime:
            return text(f"{p.name!r} is not an image.", error=True)
        data = base64.b64encode(p.read_bytes()).decode()
        return {"content": [{"type": "image", "data": data, "mimeType": mime},
                            {"type": "text", "text": f"This is {p.name!r}."}]}

    @tool("rename_image",
          "Rename one image. new_base is the name WITHOUT extension: lowercase words joined by "
          "hyphens, 2-8 words, e.g. 'pie-chart-october-expenses'. The original extension is kept.",
          {"name": str, "new_base": str})
    async def rename_image(args):
        p = find(args["name"])
        if not p:
            return text(f"No such file: {args['name']!r}", error=True)
        if not image_type(p):
            return text(f"{p.name!r} is not an image; leave it alone.", error=True)
        if p.name in renamed:
            return text(f"{p.name!r} was already renamed.", error=True)
        base = args["new_base"].strip()
        if not SLUG.match(base):
            return text(f"{base!r} is not 2-8 lowercase words joined by hyphens.", error=True)
        new_name = base + p.suffix  # suffix kept exactly, including upper case
        if new_name.lower() in taken:
            return text(f"{new_name!r} is already used. Pick a name that says how this image differs.",
                        error=True)
        taken.add(new_name.lower())
        renamed.add(p.name)
        if not dry_run:
            p.rename(root / new_name)
        log.append((p.name, new_name))
        return text(f"{'Would rename' if dry_run else 'Renamed'} {p.name!r} -> {new_name!r}")

    return [list_files, view_image, rename_image]


SYSTEM_PROMPT = """You are SnapNamer. You give image files short, descriptive, searchable names.

Steps: list_files, then view_image on each real image one at a time, then rename_image it.
Rules:
- Skip anything marked NOT AN IMAGE (notes, desktop.ini, Thumbs.db, readme ...). Never rename those.
- Describe what is actually visible: subject first, then a distinguishing detail
  ('red-bicycle-against-brick-wall', 'bar-chart-quarterly-sales').
- If text in the image tells you something specific (a month, a title, an app name), use it - this
  is how you keep near-identical images (e.g. two charts for different months) distinct.
- If an image is blurry, abstract or unclear, say so modestly ('blurry-abstract-colours').
  Never invent a subject you cannot see.
- Do not include words like 'image', 'photo-of' or 'screenshot' unless it really is a screenshot.
Finish with a short table: old name -> new name, plus the files you skipped and why.
"""


def prepare_folder(path: Path) -> Path:
    """If given a .zip, unzip a fresh copy into ./work next to this script and return the folder."""
    if path.suffix.lower() != ".zip":
        return path
    work = Path(__file__).parent / "work"
    target = work / path.stem
    if target.exists():
        shutil.rmtree(target)
    with zipfile.ZipFile(path) as zf:
        zf.extractall(work)
    print(f"Unzipped a fresh copy to {target}")
    return target


async def main() -> int:
    ap = argparse.ArgumentParser(description="SnapNamer - give images descriptive names with Claude.")
    ap.add_argument("folder", type=Path, help="folder of images, or a .zip to unzip into ./work first")
    ap.add_argument("--dry-run", action="store_true", help="suggest names without renaming")
    ap.add_argument("--model", default=None, help="Claude model to use (default: SDK default)")
    args = ap.parse_args()

    root = prepare_folder(args.folder).resolve()
    if not root.is_dir():
        sys.exit(f"Not a folder: {root}")

    log: list[tuple[str, str]] = []
    server = create_sdk_mcp_server("snap", tools=build_tools(root, args.dry_run, log))
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"snap": server},
        tools=[],
        allowed_tools=[f"mcp__snap__{n}" for n in ("list_files", "view_image", "rename_image")],
        permission_mode="dontAsk",
        max_turns=50,
        model=args.model,
    )

    prompt = "Please give the images in this folder descriptive names."
    if args.dry_run:
        prompt += (" This is a dry run: still call rename_image for every image - the tool only "
                   "records the plan and does not touch the files.")
    print(f"SnapNamer on {root}  [{'DRY RUN' if args.dry_run else 'LIVE'}]\n")
    exit_code = 1
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"  -> {block.name.split('__')[-1]} {block.input}")
        elif isinstance(msg, ResultMessage):
            print("\n=== Renames ===")
            for old, new in log:
                print(f"{old!r:45} -> {new!r}")
            print(f"\nTurns: {msg.num_turns}  Cost: ${msg.total_cost_usd or 0:.4f}")
            exit_code = 1 if msg.is_error else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
