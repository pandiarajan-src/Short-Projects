"""Native Anthropic Messages API adapter."""

from __future__ import annotations

import base64

import anthropic

from newsletter_distiller.ai.base import build_user_text
from newsletter_distiller.ai.request import DistillationRequest
from newsletter_distiller.errors import AIRequestError

DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_MAX_TOKENS = 8192

_MEDIA_TYPE_BY_EXTENSION = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class AnthropicAdapter:
    def __init__(self, api_key: str, model: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self._model = model

    def distill(self, request: DistillationRequest) -> str:
        content: list[dict] = [{"type": "text", "text": build_user_text(request)}]

        for image in request.images:
            if image.content is None:
                continue
            media_type = _MEDIA_TYPE_BY_EXTENSION.get(image.extension, "image/png")
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.b64encode(image.content).decode("ascii"),
                    },
                }
            )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=DEFAULT_MAX_TOKENS,
                system=request.system_prompt,
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.AuthenticationError as exc:
            raise AIRequestError(f"Anthropic authentication failed: {exc}") from exc
        except anthropic.RateLimitError as exc:
            raise AIRequestError(f"Anthropic rate limit exceeded: {exc}") from exc
        except anthropic.APITimeoutError as exc:
            raise AIRequestError(f"Anthropic request timed out: {exc}") from exc
        except anthropic.APIError as exc:
            raise AIRequestError(f"Anthropic API error: {exc}") from exc

        return "".join(
            block.text for block in response.content if block.type == "text"
        )
