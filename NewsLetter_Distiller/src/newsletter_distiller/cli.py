"""newsletter-distiller CLI entry point.

Wires content extraction -> AI distillation -> output assembly together
in the order the specs require: ordered fail-fast validation first, then
fetch/extract, then the output-location guard (before the AI call), then
the AI request, then placeholder resolution and final write.
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from newsletter_distiller.ai.provider import SUPPORTED_PROVIDERS, build_adapter
from newsletter_distiller.ai.request import build_request
from newsletter_distiller.ai.vision import is_vision_capable
from newsletter_distiller.config import load_config
from newsletter_distiller.errors import DistillerError
from newsletter_distiller.extraction.fetch import fetch_html
from newsletter_distiller.extraction.images import download_images
from newsletter_distiller.extraction.parse import extract_content
from newsletter_distiller.output.assembler import check_output_ready, slugify, write_output
from newsletter_distiller.output.placeholders import resolve_placeholders
from newsletter_distiller.validation import validate_startup


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="newsletter-distiller",
        description=(
            "Fetch a newsletter URL and produce a clean Markdown digest with "
            "the substantive text and genuine concept/chart images, using "
            "whichever LLM backend you configure."
        ),
    )
    parser.add_argument("url", help="Newsletter URL to fetch and distill")
    parser.add_argument(
        "--provider",
        choices=list(SUPPORTED_PROVIDERS),
        default=None,
        help=(
            "AI provider to use (default: $NEWSLETTER_DISTILLER_PROVIDER; "
            "no provider is silently assumed)"
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name for the selected provider (default: $NEWSLETTER_DISTILLER_MODEL)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Base URL for the openai-compatible provider "
            "(default: $NEWSLETTER_DISTILLER_BASE_URL)"
        ),
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Path to the system prompt file (default: prompts/system_prompt.txt)",
    )
    parser.add_argument(
        "--user-prompt",
        default=None,
        help="Path to the user prompt file (default: prompts/user_prompt.txt)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory under which the per-newsletter output folder is created (default: output)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow reusing an existing output folder for this newsletter",
    )
    vision_group = parser.add_mutually_exclusive_group()
    vision_group.add_argument(
        "--vision",
        dest="vision",
        action="store_const",
        const=True,
        default=None,
        help="Force-treat the configured model as vision-capable",
    )
    vision_group.add_argument(
        "--no-vision",
        dest="vision",
        action="store_const",
        const=False,
        help="Force-treat the configured model as text-only",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_arg_parser().parse_args(argv)

    try:
        config = load_config(args)
        system_prompt, user_prompt = validate_startup(config)

        html = fetch_html(config.url, timeout=config.fetch_timeout)
        extracted = extract_content(html, config.url)

        slug = slugify(extracted.title, config.url)
        target = check_output_ready(config.output_dir, slug, config.overwrite)

        downloaded_images = download_images(
            extracted.candidate_images, timeout=config.image_timeout
        )

        vision_capable = is_vision_capable(config.model, override=config.vision_override)
        request = build_request(
            system_prompt, user_prompt, extracted, downloaded_images, vision_capable
        )

        adapter = build_adapter(
            config.provider, config.model, config.base_url, timeout=config.ai_timeout
        )
        ai_markdown = adapter.distill(request)

        resolved_markdown = resolve_placeholders(ai_markdown, downloaded_images)
        md_path = write_output(target, slug, resolved_markdown, downloaded_images)
    except DistillerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(md_path)
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
