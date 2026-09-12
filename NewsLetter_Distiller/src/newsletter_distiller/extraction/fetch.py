"""Fetch newsletter HTML over HTTP(S) with an explicit timeout."""

from __future__ import annotations

import requests

from newsletter_distiller.errors import FetchError

DEFAULT_TIMEOUT_SECONDS = 30.0
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 newsletter-distiller"
)


def fetch_html(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    """Fetch the page at `url` and return its HTML text.

    Raises FetchError on connection failure, timeout, or a non-success
    HTTP status — never returns partial/garbage content silently.
    """
    try:
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=timeout
        )
    except requests.Timeout as exc:
        raise FetchError(f"request to '{url}' timed out after {timeout}s") from exc
    except requests.RequestException as exc:
        raise FetchError(f"failed to fetch '{url}': {exc}") from exc

    if not response.ok:
        raise FetchError(
            f"'{url}' returned HTTP {response.status_code}"
        )

    return response.text
