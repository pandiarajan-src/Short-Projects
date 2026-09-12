from pathlib import Path

import pytest
import responses

from newsletter_distiller.errors import EmptyContentError, FetchError, ValidationError
from newsletter_distiller.extraction.fetch import fetch_html
from newsletter_distiller.extraction.images import download_images
from newsletter_distiller.extraction.parse import CandidateImage, extract_content
from newsletter_distiller.extraction.url import validate_url_scheme

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "sample_newsletter.html").read_text()
FIXTURE_URL = "https://info.deeplearning.ai/driving-the-build-is-now-an-essential-ai-engineering-skill"


# --- 3.1 URL scheme validation -----------------------------------------

def test_validate_url_scheme_accepts_https():
    validate_url_scheme("https://example.com/newsletter")  # should not raise


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/x", "javascript:alert(1)"])
def test_validate_url_scheme_rejects_non_http(url):
    with pytest.raises(ValidationError):
        validate_url_scheme(url)


# --- 3.2 HTTP fetch with timeout ----------------------------------------

@responses.activate
def test_fetch_html_success():
    responses.add(responses.GET, "https://example.com/ok", body="<html>hi</html>", status=200)
    assert fetch_html("https://example.com/ok") == "<html>hi</html>"


@responses.activate
def test_fetch_html_non_success_status():
    responses.add(responses.GET, "https://example.com/missing", status=404)
    with pytest.raises(FetchError):
        fetch_html("https://example.com/missing")


@responses.activate
def test_fetch_html_timeout():
    import requests

    responses.add(
        responses.GET,
        "https://example.com/slow",
        body=requests.exceptions.Timeout("timed out"),
    )
    with pytest.raises(FetchError):
        fetch_html("https://example.com/slow", timeout=1.0)


# --- 3.3 / 3.4 / 3.5 / 3.6 boilerplate stripping + text/image extraction ---

def test_extract_content_strips_footer_and_preheader():
    extracted = extract_content(FIXTURE_HTML, FIXTURE_URL)
    assert "unsubscribe" not in extracted.text.lower()
    assert "manage preferences" not in extracted.text.lower()
    assert "view in browser" not in extracted.text.lower()


def test_extract_content_preserves_reading_order():
    extracted = extract_content(FIXTURE_HTML, FIXTURE_URL)
    idx_news_heading = extracted.text.find("# News")
    idx_astra_heading = extracted.text.find("GPT-6 Astra Is a")
    assert idx_news_heading != -1
    assert idx_astra_heading != -1
    assert idx_news_heading < idx_astra_heading


def test_extract_content_raises_on_empty_extraction():
    thin_html = "<html><title>t</title><body><footer>unsubscribe here</footer></body></html>"
    with pytest.raises(EmptyContentError):
        extract_content(thin_html, "https://example.com/thin")


def test_extract_content_collects_candidate_images_with_metadata():
    extracted = extract_content(FIXTURE_HTML, FIXTURE_URL)
    assert len(extracted.candidate_images) == 8
    astra_image = next(
        img for img in extracted.candidate_images if "GPT-6 Astra" in img.alt
    )
    assert astra_image.alt.startswith("A graph shows GPT-6 Astra")
    assert astra_image.src.startswith("https://info.deeplearning.ai/")


def test_extract_content_flags_tracking_pixel_as_removed():
    html = (
        "<html><title>Pixel test</title><body>"
        "<p>" + ("substantive article content " * 10) + "</p>"
        '<img src="https://example.com/pixel.gif" width="1" height="1" alt="tracker">'
        "</body></html>"
    )
    extracted = extract_content(html, "https://example.com/pixel-test")
    assert extracted.candidate_images == []


# --- 3.7 image download + stable IDs -------------------------------------

@responses.activate
def test_download_images_assigns_sequential_ids():
    responses.add(
        responses.GET, "https://example.com/a.png", body=b"AAA",
        content_type="image/png",
    )
    responses.add(
        responses.GET, "https://example.com/b.png", body=b"BBB",
        content_type="image/png",
    )
    candidates = [
        CandidateImage(position=0, src="https://example.com/a.png", alt="a", surrounding_text=""),
        CandidateImage(position=1, src="https://example.com/b.png", alt="b", surrounding_text=""),
    ]
    downloaded = download_images(candidates)
    assert [img.id for img in downloaded] == ["IMAGE_1", "IMAGE_2"]
    assert downloaded[0].content == b"AAA"
    assert downloaded[0].extension == "png"


@responses.activate
def test_download_images_skips_broken_link_and_continues():
    responses.add(responses.GET, "https://example.com/broken.png", status=404)
    responses.add(
        responses.GET, "https://example.com/ok.png", body=b"OK",
        content_type="image/png",
    )
    candidates = [
        CandidateImage(position=0, src="https://example.com/broken.png", alt="broken", surrounding_text=""),
        CandidateImage(position=1, src="https://example.com/ok.png", alt="ok", surrounding_text=""),
    ]
    downloaded = download_images(candidates)
    assert len(downloaded) == 1
    assert downloaded[0].id == "IMAGE_1"
    assert downloaded[0].src == "https://example.com/ok.png"
