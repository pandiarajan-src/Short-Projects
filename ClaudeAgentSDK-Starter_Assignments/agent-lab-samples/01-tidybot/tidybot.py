#!/usr/bin/env python3
"""TidyBot - a Claude Agent SDK agent that tidies a messy Downloads folder.

The agent can only touch the folder through four custom tools:
  list_folder  - see what is there (name, size, detected type)
  peek_file    - look at the first bytes of a file (catches PDFs with no extension)
  move_file    - move a file into a category subfolder, never overwriting
  skip_file    - leave a file alone and say why (system files, lock files ...)

Usage:
  python tidybot.py sample-downloads.zip            # unzip a fresh copy into ./work and tidy it
  python tidybot.py ./work/sample-downloads --dry-run
"""

import argparse
import asyncio
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

CATEGORIES = [
    "Documents",     # pdf, docx, resumes, invoices
    "Images",        # jpg, png, webp
    "Audio",         # mp3, wav, m4a
    "Video",         # mp4, mkv
    "Archives",      # zip, 7z, tar.gz
    "Installers",    # deb, rpm, pkg, AppImage, dmg
    "Spreadsheets",  # csv, tsv, xlsx
    "Notes",         # txt, md, plain-text notes
    "Code",          # json, yaml, scripts, config
    "Other",
]

DOUBLE_EXTENSIONS = (".tar.gz", ".tar.bz2", ".tar.xz")

# (magic bytes, offset, label)
SIGNATURES = [
    (b"%PDF", 0, "PDF document"),
    (b"\x89PNG", 0, "PNG image"),
    (b"\xff\xd8\xff", 0, "JPEG image"),
    (b"RIFF", 0, "RIFF container (WAV audio or WEBP image)"),
    (b"ID3", 0, "MP3 audio"),
    (b"ftyp", 4, "MP4/M4A media"),
    (b"PK\x03\x04", 0, "ZIP archive (or docx/xlsx)"),
    (b"\x1f\x8b", 0, "GZIP archive"),
    (b"7z\xbc\xaf\x27\x1c", 0, "7-Zip archive"),
    (b"!<arch>", 0, "Debian package"),
    (b"\xed\xab\xee\xdb", 0, "RPM package"),
    (b"xar!", 0, "macOS installer package"),
    (b"\x7fELF", 0, "Linux executable (ELF)"),
]


def detect_type(path: Path) -> str:
    head = path.read_bytes()[:64]
    for magic, offset, label in SIGNATURES:
        if head[offset:offset + len(magic)] == magic:
            return label
    try:
        head.decode("utf-8")
        return "plain text" if head else "empty file"
    except UnicodeDecodeError:
        return "unknown binary"


def split_name(name: str) -> tuple[str, str]:
    """'archive.tar.gz' -> ('archive', '.tar.gz'); 'report.pdf' -> ('report', '.pdf')."""
    lower = name.lower()
    for ext in DOUBLE_EXTENSIONS:
        if lower.endswith(ext) and len(name) > len(ext):
            return name[: -len(ext)], name[-len(ext):]
    p = Path(name)
    return (p.stem, p.suffix) if p.suffix else (name, "")


def text(msg: str, error: bool = False) -> dict:
    result = {"content": [{"type": "text", "text": msg}]}
    if error:
        result["is_error"] = True
    return result


def build_tools(root: Path, dry_run: bool, log: list):
    planned: set[Path] = set()  # destinations already used in this run (matters for --dry-run)
    handled: set[str] = set()

    def resolve(name: str) -> Path | None:
        p = (root / name).resolve()
        if p.parent != root.resolve() or not p.is_file():
            return None
        return p

    def free_destination(folder: Path, filename: str) -> Path:
        stem, ext = split_name(filename)
        dest, n = folder / filename, 1
        while dest.exists() or dest in planned:
            dest = folder / f"{stem} ({n}){ext}"
            n += 1
        return dest

    @tool("list_folder", "List the loose files at the top of the folder, with size and detected type. "
          "Also lists the existing subfolders and what they contain.", {})
    async def list_folder(args):
        lines = ["FILES:"]
        for p in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if p.is_file() and p.name not in handled:
                lines.append(f"- {p.name!r}  size={p.stat().st_size}B  detected={detect_type(p)}")
        lines.append("EXISTING SUBFOLDERS:")
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            lines.append(f"- {d.name}/: {', '.join(sorted(c.name for c in d.iterdir())) or '(empty)'}")
        return text("\n".join(lines))

    @tool("peek_file", "Show the first bytes of a file as text so you can tell what it really is.",
          {"name": str})
    async def peek_file(args):
        p = resolve(args["name"])
        if not p:
            return text(f"No such file at top level: {args['name']!r}", error=True)
        raw = p.read_bytes()[:300]
        preview = raw.decode("utf-8", errors="replace")
        return text(f"detected={detect_type(p)}\nfirst {len(raw)} bytes:\n{preview}")

    @tool("move_file",
          "Move one top-level file into a category subfolder. Never overwrites: if the name is taken a "
          "numeric suffix like ' (1)' is added. Use new_name only to add a missing extension "
          "(e.g. 'download (1)' -> 'download (1).pdf').",
          {
              "type": "object",
              "properties": {
                  "name": {"type": "string"},
                  "category": {"type": "string", "enum": CATEGORIES},
                  "reason": {"type": "string"},
                  "new_name": {"type": "string"},
              },
              "required": ["name", "category", "reason"],
          })
    async def move_file(args):
        p = resolve(args["name"])
        if not p:
            return text(f"No such file at top level: {args['name']!r}", error=True)
        if args["name"] in handled:
            return text(f"{args['name']!r} was already handled.", error=True)
        target_name = args.get("new_name") or p.name
        if "/" in target_name or "\\" in target_name or not target_name.startswith(p.name):
            return text("new_name may only append an extension to the original name.", error=True)

        dest = free_destination(root / args["category"], target_name)
        planned.add(dest)
        handled.add(p.name)
        if not dry_run:
            dest.parent.mkdir(exist_ok=True)
            shutil.move(str(p), str(dest))
        rel = dest.relative_to(root)
        log.append(("MOVE", p.name, str(rel), args["reason"]))
        note = " (renamed to avoid overwriting an existing file)" if dest.name != target_name else ""
        return text(f"{'Would move' if dry_run else 'Moved'} {p.name!r} -> {rel}{note}")

    @tool("skip_file", "Leave a file where it is and record why.", {"name": str, "reason": str})
    async def skip_file(args):
        if not resolve(args["name"]):
            return text(f"No such file at top level: {args['name']!r}", error=True)
        handled.add(args["name"])
        log.append(("SKIP", args["name"], "-", args["reason"]))
        return text(f"Leaving {args['name']!r} alone.")

    return [list_folder, peek_file, move_file, skip_file]


SYSTEM_PROMPT = f"""You are TidyBot, a careful assistant that organises a Downloads folder.

Rules:
- Start with list_folder. Handle EVERY loose file exactly once, with move_file or skip_file.
- Decide by the real content, not just the name. If a file has no extension, an odd extension, or
  the detected type disagrees with the extension, call peek_file first. If a file with no extension
  is clearly e.g. a PDF, move it and add the right extension with new_name.
- Extensions are case-insensitive (.PDF == .pdf). 'archive.tar.gz' is one archive.
- Leave operating-system files alone (desktop.ini, Thumbs.db, .DS_Store) and Office lock files
  whose names start with '~$' - use skip_file.
- Categories: {", ".join(CATEGORIES)}. Use existing subfolders when they match.
- Never delete anything. Never invent files. Moves never overwrite; the tool handles name clashes.
- Finish with a short plain-text summary: how many files moved per category, what you skipped and
  anything surprising (e.g. a file that was not what its name said).
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
    ap = argparse.ArgumentParser(description="TidyBot - tidy a Downloads folder with Claude.")
    ap.add_argument("folder", type=Path, help="folder to tidy, or a .zip to unzip into ./work first")
    ap.add_argument("--dry-run", action="store_true", help="plan the moves without touching files")
    ap.add_argument("--model", default=None, help="Claude model to use (default: SDK default)")
    args = ap.parse_args()

    root = prepare_folder(args.folder).resolve()
    if not root.is_dir():
        sys.exit(f"Not a folder: {root}")

    log: list[tuple[str, str, str, str]] = []
    server = create_sdk_mcp_server("tidy", tools=build_tools(root, args.dry_run, log))
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"tidy": server},
        tools=[],  # no built-in tools: the agent can only use our four
        allowed_tools=[f"mcp__tidy__{n}" for n in ("list_folder", "peek_file", "move_file", "skip_file")],
        permission_mode="dontAsk",
        max_turns=60,
        model=args.model,
    )

    mode = "DRY RUN - nothing will be moved" if args.dry_run else "LIVE - files will be moved"
    print(f"TidyBot on {root}  [{mode}]\n")
    prompt = "Please tidy this Downloads folder."
    if args.dry_run:
        prompt += " This is a dry run: moves are only planned, so word your summary as a plan."
    exit_code = 1
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"  -> {block.name.split('__')[-1]} {block.input}")
        elif isinstance(msg, ResultMessage):
            print("\n=== Actions ===")
            for action, name, dest, reason in log:
                print(f"{action:4}  {name!r:36} -> {dest:36} {reason}")
            print(f"\nTurns: {msg.num_turns}  Cost: ${msg.total_cost_usd or 0:.4f}")
            exit_code = 1 if msg.is_error else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
