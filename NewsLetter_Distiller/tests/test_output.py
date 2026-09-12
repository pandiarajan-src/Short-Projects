import pytest

from newsletter_distiller.errors import OutputError, UnknownImagePlaceholderError
from newsletter_distiller.extraction.images import DownloadedImage
from newsletter_distiller.output.assembler import check_output_ready, slugify, write_output
from newsletter_distiller.output.placeholders import resolve_placeholders


def _image(image_id: str = "IMAGE_1") -> DownloadedImage:
    return DownloadedImage(
        id=image_id, src="https://example.com/x.png", alt="alt",
        surrounding_text="ctx", position=0, content=b"BYTES", extension="png",
    )


# --- 5.1 placeholder resolution ---------------------------------------------

def test_resolve_placeholders_multiple_images():
    images = [_image("IMAGE_1"), _image("IMAGE_2")]
    markdown = "Intro\n\n![a](IMAGE_1)\n\nMore text\n\n![b](IMAGE_2)\n"
    resolved = resolve_placeholders(markdown, images)
    assert "assets/IMAGE_1.png" in resolved
    assert "assets/IMAGE_2.png" in resolved
    assert "IMAGE_1)" not in resolved.replace("assets/IMAGE_1.png)", "")


# --- 5.2 unknown placeholder validation --------------------------------------

def test_resolve_placeholders_unknown_id_raises():
    images = [_image("IMAGE_1")]
    markdown = "![a](IMAGE_1)\n![ghost](IMAGE_99)"
    with pytest.raises(UnknownImagePlaceholderError):
        resolve_placeholders(markdown, images)


# --- 5.3 slug derivation + output folder writing -----------------------------

def test_slugify_from_title():
    slug = slugify(
        "Driving the Build Is Now An Essential AI Engineering Skill!",
        "https://info.deeplearning.ai/some-path",
    )
    assert slug == "driving-the-build-is-now-an-essential-ai-engineering-skill"


def test_slugify_falls_back_to_url_when_title_missing():
    slug = slugify("", "https://example.com/some-newsletter-issue")
    assert slug == "some-newsletter-issue"


def test_write_output_creates_expected_layout(tmp_path):
    output_dir = tmp_path / "output"
    slug = "my-newsletter"
    target = check_output_ready(output_dir, slug, overwrite=False)
    md_path = write_output(target, slug, "# Digest\n\n![a](assets/IMAGE_1.png)", [_image()])

    assert md_path == output_dir / slug / f"{slug}.md"
    assert md_path.exists()
    assert (output_dir / slug / "assets" / "IMAGE_1.png").read_bytes() == b"BYTES"


# --- 5.4 output-directory writable + overwrite guard -------------------------

def test_check_output_ready_rejects_existing_without_overwrite(tmp_path):
    output_dir = tmp_path / "output"
    slug = "dup"
    check_output_ready(output_dir, slug, overwrite=False)
    with pytest.raises(OutputError):
        check_output_ready(output_dir, slug, overwrite=False)


def test_check_output_ready_allows_existing_with_overwrite(tmp_path):
    output_dir = tmp_path / "output"
    slug = "dup"
    check_output_ready(output_dir, slug, overwrite=False)
    target = check_output_ready(output_dir, slug, overwrite=True)
    assert target == output_dir / slug


def test_check_output_ready_rejects_unwritable_location(tmp_path):
    output_dir = tmp_path / "readonly"
    output_dir.mkdir()
    output_dir.chmod(0o400)
    try:
        with pytest.raises(OutputError):
            check_output_ready(output_dir, "slug", overwrite=False)
    finally:
        output_dir.chmod(0o700)
