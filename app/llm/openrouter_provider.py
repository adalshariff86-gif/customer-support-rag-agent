"""
OpenRouter LLM Provider – OpenRouter integration via OpenAI-compatible HTTP API.

Wraps OpenRouter's chat completions endpoint behind the ``LLMProvider`` ABC
so the rest of the application never imports the HTTP client directly.

Responsibilities:
  - Send prompts to OpenRouter's OpenAI-compatible API.
  - Handle HTTP errors, timeouts, and empty responses.
  - Translate failures into ``LLMException``.

Usage:
    from app.llm.openrouter_provider import OpenRouterProvider
    provider = OpenRouterProvider(api_key="...", model="openrouter/free")
    answer = provider.generate("What is your return policy?")
"""

from __future__ import annotations

import re
import time

import httpx

from app.core.config import settings
from app.core.exceptions import LLMException
from app.core.logger import get_logger
from app.llm.base import LLMProvider

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────
_DEFAULT_MODEL = settings.OPENROUTER_MODEL
_DEFAULT_BASE_URL = settings.OPENROUTER_BASE_URL
_DEFAULT_TIMEOUT = 60
_MAX_RETRIES = 2
# Patterns that indicate the model returned a safety classification
# instead of a real answer.
_SAFETY_PATTERNS = re.compile(
    r"^\s*(user\s+safety|safety\s*:\s*safe|content\s*flagged|"
    r"this\s+(query|request|message)\s+(has\s+been|is)\s+(flagged|blocked))\s*$",
    re.IGNORECASE,
)


class OpenRouterProvider(LLMProvider):
    """OpenRouter language model provider.

    Uses OpenRouter's OpenAI-compatible chat completions endpoint via
    ``httpx``.  The client is created lazily on first use.

    Args:
        api_key:   OpenRouter API key.  Falls back to ``settings.OPENROUTER_API_KEY``.
        model:     Model identifier (default from settings).
        base_url:  API base URL (default from settings).
        timeout:   Request timeout in seconds (default ``60``).

    Raises:
        LLMException: If initialisation fails.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or settings.OPENROUTER_API_KEY
        self._model_name = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.Client | None = None
        self._initialised = False

        if not self._api_key:
            logger.warning(
                "OpenRouter API key not configured",
                extra={"model": self._model_name},
            )
        else:
            self.initialise()

    def initialise(self) -> None:
        """Create the ``httpx.Client`` (idempotent, safe to call repeatedly)."""
        if self._initialised:
            return

        if not self._api_key:
            raise LLMException(
                message="OpenRouter API key not configured.",
                details={"model": self._model_name},
            )

        try:
            self._client = httpx.Client(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://customer-support-rag.local",
                    "X-Title": "Customer Support RAG",
                },
                timeout=httpx.Timeout(self._timeout),
            )
            self._initialised = True
            logger.info(
                "OpenRouter provider initialised",
                extra={"model": self._model_name},
            )
        except Exception as exc:
            raise LLMException(
                message="Failed to initialise OpenRouter provider.",
                details={"error": str(exc), "model": self._model_name},
            ) from exc

    @property
    def model_name(self) -> str:
        """Return the OpenRouter model identifier."""
        return self._model_name

    def generate(self, prompt: str) -> str:
        """Generate a response using the OpenRouter model.

        Sends the prompt as a user message via the chat completions endpoint.

        Args:
            prompt: The fully constructed prompt string.

        Returns:
            The generated text response.

        Raises:
            LLMException: If the API call fails, times out, or returns
                           an empty response.
        """
        messages = [{"role": "user", "content": prompt}]
        return self._chat_completion(messages)

    def generate_messages(self, messages: list[dict]) -> str:
        """Generate a response using structured chat messages.

        Sends properly formatted system/user messages via the chat completions
        endpoint.  This produces much better results with free OpenRouter
        models that may misinterpret long single-user-message prompts.

        Args:
            messages: List of message dicts with ``role`` and ``content`` keys.

        Returns:
            The generated text response.

        Raises:
            LLMException: If the API call fails, times out, or returns
                           an empty response.
        """
        return self._chat_completion(messages)

    def _chat_completion(self, messages: list[dict]) -> str:
        """Shared chat completion implementation.

        Includes retry logic for safety-classification responses that some
        free OpenRouter models incorrectly return.

        Args:
            messages: List of message dicts with ``role`` and ``content`` keys.

        Returns:
            The generated text response.

        Raises:
            LLMException: If the API call fails, times out, or returns
                           an empty response.
        """
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            start = time.perf_counter()

            try:
                logger.info(
                    "OpenRouter request started",
                    extra={
                        "model": self._model_name,
                        "message_count": len(messages),
                        "attempt": attempt + 1,
                    },
                )

                self.initialise()
                assert self._client is not None

                response = self._client.post(
                    "/chat/completions",
                    json={
                        "model": self._model_name,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 512,
                    },
                )

                response.raise_for_status()
                data = response.json()

                choices = data.get("choices", [])
                if not choices:
                    raise LLMException(
                        message="OpenRouter returned no choices.",
                        details={"model": self._model_name},
                    )

                response_text = choices[0].get("message", {}).get("content", "")
                if not response_text:
                    raise LLMException(
                        message="OpenRouter returned an empty response.",
                        details={"model": self._model_name},
                    )

                # Validate: detect safety-classification responses
                if _SAFETY_PATTERNS.match(response_text):
                    logger.warning(
                        "OpenRouter returned safety-classification response, retrying",
                        extra={
                            "model": self._model_name,
                            "attempt": attempt + 1,
                            "response_preview": response_text[:100],
                        },
                    )
                    if attempt < _MAX_RETRIES:
                        continue
                    # Final attempt: return the response as-is rather than raising,
                    # since the caller may want to handle it gracefully.
                    logger.error(
                        "OpenRouter safety-classification response persists after retries",
                        extra={"model": self._model_name},
                    )

                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.info(
                    "OpenRouter request completed",
                    extra={
                        "model": self._model_name,
                        "response_length": len(response_text),
                        "elapsed_ms": elapsed_ms,
                    },
                )

                return response_text

            except LLMException:
                raise
            except httpx.TimeoutException as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.error(
                    "OpenRouter request timed out",
                    extra={
                        "model": self._model_name,
                        "timeout_seconds": self._timeout,
                        "error": str(exc),
                        "elapsed_ms": elapsed_ms,
                        "attempt": attempt + 1,
                    },
                )
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    continue
                raise LLMException(
                    message=f"OpenRouter request timed out after {self._timeout}s.",
                    details={"model": self._model_name, "timeout_seconds": self._timeout},
                    status_code=504,
                ) from exc
            except httpx.HTTPStatusError as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                status_code = exc.response.status_code
                logger.error(
                    "OpenRouter HTTP error",
                    extra={
                        "model": self._model_name,
                        "status_code": status_code,
                        "error": str(exc),
                        "elapsed_ms": elapsed_ms,
                        "attempt": attempt + 1,
                    },
                )
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    continue
                raise LLMException(
                    message=f"OpenRouter returned HTTP {status_code}.",
                    details={"model": self._model_name, "status_code": status_code},
                    status_code=502,
                ) from exc
            except httpx.RequestError as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.error(
                    "OpenRouter request failed",
                    extra={
                        "model": self._model_name,
                        "error": str(exc),
                        "elapsed_ms": elapsed_ms,
                        "attempt": attempt + 1,
                    },
                )
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    continue
                raise LLMException(
                    message=f"OpenRouter request failed: {exc}",
                    details={"model": self._model_name, "error": str(exc)},
                ) from exc
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                error_type = type(exc).__name__
                logger.error(
                    "OpenRouter request failed",
                    extra={
                        "model": self._model_name,
                        "error_type": error_type,
                        "error": str(exc),
                        "elapsed_ms": elapsed_ms,
                        "attempt": attempt + 1,
                    },
                )
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    continue
                raise LLMException(
                    message=f"OpenRouter model call failed: {exc}",
                    details={"model": self._model_name, "error": str(exc)},
                ) from exc

        # Should not be reached, but just in case
        raise LLMException(
            message="OpenRouter request failed after all retries.",
            details={"model": self._model_name},
        )
