"""URL scheme validation (content-extraction: URL scheme validation)."""

from __future__ import annotations

from urllib.parse import urlparse

from newsletter_distiller.errors import ValidationError

ALLOWED_SCHEMES = ("http", "https")


def validate_url_scheme(url: str) -> None:
    """Raise ValidationError unless the URL uses http(s), before any fetch."""
    scheme = urlparse(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise ValidationError(
            f"unsupported URL scheme '{scheme or '(none)'}' in '{url}' "
            f"— only {', '.join(ALLOWED_SCHEMES)} are allowed"
        )
