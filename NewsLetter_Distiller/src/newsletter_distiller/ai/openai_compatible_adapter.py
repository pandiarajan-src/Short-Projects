"""Generic OpenAI-compatible chat-completions adapter.

Covers any provider exposing an OpenAI-style `/chat/completions`
endpoint (Ollama, DeepSeek, Kimi/Moonshot, etc.) via a configurable
base URL, without a dedicated adapter per vendor. Implemented as a raw
HTTP call rather than the `openai` SDK, since several compatible
servers deviate slightly from the SDK's strict client-side validation
(design.md: "Provider adapters").
"""

from __future__ import annotations

import base64

import requests

from newsletter_distiller.ai.base import build_user_text
from newsletter_distiller.ai.request import DistillationRequest
from newsletter_distiller.errors import AIRequestError

DEFAULT_TIMEOUT_SECONDS = 120.0

_MEDIA_TYPE_BY_EXTENSION = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class OpenAICompatibleAdapter:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def distill(self, request: DistillationRequest) -> str:
        user_content: list[dict] = [{"type": "text", "text": build_user_text(request)}]

        for image in request.images:
            if image.content is None:
                continue
            media_type = _MEDIA_TYPE_BY_EXTENSION.get(image.extension, "image/png")
            data_url = (
                f"data:{media_type};base64,"
                f"{base64.b64encode(image.content).decode('ascii')}"
            )
            user_content.append(
                {"type": "image_url", "image_url": {"url": data_url}}
            )

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

        try:
            response = requests.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
        except requests.Timeout as exc:
            raise AIRequestError(f"request to '{self._base_url}' timed out: {exc}") from exc
        except requests.RequestException as exc:
            raise AIRequestError(f"request to '{self._base_url}' failed: {exc}") from exc

        if response.status_code == 401:
            raise AIRequestError(f"authentication failed against '{self._base_url}'")
        if response.status_code == 429:
            raise AIRequestError(f"rate limit exceeded against '{self._base_url}'")
        if not response.ok:
            raise AIRequestError(
                f"'{self._base_url}' returned HTTP {response.status_code}: {response.text[:500]}"
            )

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            raise AIRequestError(
                f"unexpected response shape from '{self._base_url}': {exc}"
            ) from exc
