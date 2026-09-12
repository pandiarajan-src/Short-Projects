import re
from pathlib import Path

import pytest
import responses

from newsletter_distiller import cli
from newsletter_distiller.ai.provider import ANTHROPIC_API_KEY_ENV, OPENAI_COMPATIBLE_API_KEY_ENV

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "sample_newsletter.html").read_text()
FIXTURE_URL = "https://info.deeplearning.ai/driving-the-build-is-now-an-essential-ai-engineering-skill"


def _write_prompts(tmp_path):
    system_path = tmp_path / "system.txt"
    user_path = tmp_path / "user.txt"
    system_path.write_text("Be concise.")
    user_path.write_text("Summarize this newsletter.")
    return system_path, user_path


# --- 6.1 entry point / --help --------------------------------------------

def test_help_documents_every_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.build_arg_parser().parse_args(["--help"])
    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    for flag in [
        "--provider", "--model", "--base-url", "--system-prompt",
        "--user-prompt", "--output-dir", "--overwrite", "--vision", "--no-vision",
    ]:
        assert flag in output


# --- 6.2 ordered validation runs before any network call -------------------

def test_validation_failure_prevents_network_calls(monkeypatch, tmp_path):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("fetch_html should not be called when startup validation fails")

    monkeypatch.setattr(cli, "fetch_html", _fail_if_called)

    missing_prompt = tmp_path / "missing.txt"
    exit_code = cli.run(
        [
            FIXTURE_URL,
            "--provider", "anthropic",
            "--model", "claude-sonnet-5",
            "--system-prompt", str(missing_prompt),
            "--user-prompt", str(missing_prompt),
        ]
    )
    assert exit_code == 1


# --- 6.3 end-to-end with mocked AI provider --------------------------------

@responses.activate
def test_end_to_end_produces_markdown_with_resolved_images(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(OPENAI_COMPATIBLE_API_KEY_ENV, "ollama")
    system_path, user_path = _write_prompts(tmp_path)
    output_dir = tmp_path / "output"

    responses.add(responses.GET, FIXTURE_URL, body=FIXTURE_HTML, status=200)
    responses.add(
        responses.GET,
        re.compile(r"https://info\.deeplearning\.ai/hs-fs/hubfs/.*"),
        body=b"FAKEIMAGEBYTES",
        content_type="image/png",
    )
    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        json={
            "choices": [
                {
                    "message": {
                        "content": (
                            "# The Batch Digest\n\n"
                            "Intro text.\n\n"
                            "![Skills map](IMAGE_2)\n\n"
                            "More text.\n\n"
                            "![Astra chart](IMAGE_4)\n"
                        )
                    }
                }
            ]
        },
        status=200,
    )

    exit_code = cli.run(
        [
            FIXTURE_URL,
            "--provider", "openai-compatible",
            "--model", "llava-13b",
            "--base-url", "http://localhost:11434/v1",
            "--system-prompt", str(system_path),
            "--user-prompt", str(user_path),
            "--output-dir", str(output_dir),
        ]
    )

    assert exit_code == 0
    printed_path = Path(capsys.readouterr().out.strip())
    assert printed_path.exists()

    markdown = printed_path.read_text()
    assert "assets/IMAGE_2.png" in markdown
    assert "assets/IMAGE_4.png" in markdown
    assert "IMAGE_2)" not in markdown.replace("IMAGE_2.png)", "")
    assert (printed_path.parent / "assets" / "IMAGE_2.png").read_bytes() == b"FAKEIMAGEBYTES"


# --- 6.4 distinct, stage-attributed error messages -------------------------

def test_bad_url_scheme_reports_validation_stage(capsys):
    exit_code = cli.run(["ftp://example.com/x", "--provider", "anthropic", "--model", "m"])
    assert exit_code == 1
    assert "[validation]" in capsys.readouterr().err


@responses.activate
def test_fetch_failure_reports_fetch_stage(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "sk-test")
    system_path, user_path = _write_prompts(tmp_path)
    responses.add(responses.GET, FIXTURE_URL, status=500)

    exit_code = cli.run(
        [
            FIXTURE_URL,
            "--provider", "anthropic",
            "--model", "claude-sonnet-5",
            "--system-prompt", str(system_path),
            "--user-prompt", str(user_path),
            "--output-dir", str(tmp_path / "output"),
        ]
    )
    assert exit_code == 1
    assert "[fetch]" in capsys.readouterr().err


@responses.activate
def test_empty_extraction_reports_extraction_stage(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "sk-test")
    system_path, user_path = _write_prompts(tmp_path)
    thin_url = "https://example.com/thin"
    responses.add(responses.GET, thin_url, body="<html><title>t</title><body><p>hi</p></body></html>")

    exit_code = cli.run(
        [
            thin_url,
            "--provider", "anthropic",
            "--model", "claude-sonnet-5",
            "--system-prompt", str(system_path),
            "--user-prompt", str(user_path),
            "--output-dir", str(tmp_path / "output"),
        ]
    )
    assert exit_code == 1
    assert "[extraction]" in capsys.readouterr().err


@responses.activate
def test_ai_failure_reports_ai_stage_and_writes_no_file(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(OPENAI_COMPATIBLE_API_KEY_ENV, "ollama")
    system_path, user_path = _write_prompts(tmp_path)
    output_dir = tmp_path / "output"

    responses.add(responses.GET, FIXTURE_URL, body=FIXTURE_HTML, status=200)
    responses.add(
        responses.GET,
        re.compile(r"https://info\.deeplearning\.ai/hs-fs/hubfs/.*"),
        body=b"FAKEIMAGEBYTES",
        content_type="image/png",
    )
    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        status=401,
    )

    exit_code = cli.run(
        [
            FIXTURE_URL,
            "--provider", "openai-compatible",
            "--model", "llava-13b",
            "--base-url", "http://localhost:11434/v1",
            "--system-prompt", str(system_path),
            "--user-prompt", str(user_path),
            "--output-dir", str(output_dir),
        ]
    )
    assert exit_code == 1
    assert "[ai]" in capsys.readouterr().err
    assert not output_dir.exists() or not any(output_dir.rglob("*.md"))
