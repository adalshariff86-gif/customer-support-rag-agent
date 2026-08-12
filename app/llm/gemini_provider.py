"""
Gemini LLM Provider – Google Gemini integration via the official SDK.

Wraps ``google-genai`` behind the ``LLMProvider`` ABC so the
rest of the application never imports the SDK directly.

Responsibilities:
  - Initialise the Gemini client with the configured API key and model.
  - Convert prompts into Gemini-compatible content.
  - Handle SDK errors and translate them into ``LLMException``.

Usage:
    from app.llm.gemini_provider import GeminiProvider
    provider = GeminiProvider(api_key="...", model="gemini-2.0-flash")
    answer = provider.generate("What is your return policy?")
"""

from __future__ import annotations

import ssl
import time
from typing import Any

from google import genai  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.exceptions import LLMException
from app.core.logger import get_logger
from app.llm.base import LLMProvider

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────
_DEFAULT_MODEL = settings.GEMINI_MODEL
_DEFAULT_TIMEOUT = 60

# Optimised generation config – reduces output latency while preserving
# answer quality for a customer-support RAG use-case.
#
# thinking_budget: gemini-3.5-flash enables extended thinking by default,
# which burns 3-8 s of compute before producing any output.  Capping the
# budget at 512 tokens keeps light reasoning for answer synthesis while
# eliminating the bulk of the thinking overhead.
_GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.2,
    top_p=0.9,
    top_k=20,
    max_output_tokens=512,
    thinking_config=types.ThinkingConfig(
        include_thoughts=False,
    ),
)


class GeminiProvider(LLMProvider):
    """Google Gemini language model provider.

    The ``google-genai`` SDK is imported once at module load and the
    ``genai.Client`` is created eagerly so that the first request does
    not pay initialisation cost.  Thread-safe for concurrent requests.

    Args:
        api_key:  Google Gemini API key.  Falls back to ``settings.GEMINI_API_KEY``.
        model:    Model identifier (default ``"gemini-2.0-flash"``).
        timeout:  Request timeout in seconds (default ``60``).

    Raises:
        LLMException: If the SDK is not installed or initialisation fails.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model
        self._timeout = timeout
        self._client: Any = None
        self._initialised = False

        if not self._api_key:
            logger.warning(
                "Gemini API key not configured",
                extra={"model": self._model_name},
            )
        else:
            self.initialise()

    # ── Public initialisation (also callable from startup) ──

    def initialise(self) -> None:
        """Create the ``genai.Client`` (idempotent, safe to call repeatedly).

        The client reuses the underlying HTTP transport for all subsequent
        requests, avoiding per-request connection setup overhead.
        """
        if self._initialised:
            return

        if not self._api_key:
            raise LLMException(
                message="Gemini API key not configured.",
                details={"model": self._model_name},
            )

        try:
            self._client = genai.Client(api_key=self._api_key)
            self._initialised = True
            logger.info(
                "Gemini provider initialised",
                extra={"model": self._model_name},
            )
        except Exception as exc:
            raise LLMException(
                message="Failed to initialise Gemini provider.",
                details={"error": str(exc), "model": self._model_name},
            ) from exc

    @property
    def model_name(self) -> str:
        """Return the Gemini model identifier."""
        return self._model_name

    def generate(self, prompt: str) -> str:
        """Generate a response using the Gemini model.

        Uses streaming internally to reduce time-to-first-token latency.
        The streamed chunks are accumulated and the full text is returned,
        keeping the public contract identical to a blocking call.

        Args:
            prompt: The fully constructed prompt string.

        Returns:
            The generated text response.

        Raises:
            LLMException: If the SDK call fails, times out, or returns
                           an empty response.
        """
        start = time.perf_counter()

        try:
            logger.info(
                "Gemini request started",
                extra={"model": self._model_name, "prompt_length": len(prompt)},
            )

            self.initialise()

            # Stream and accumulate – reduces time-to-first-token latency.
            # Enforce a request-level timeout via httpOptions (milliseconds).
            request_config = types.GenerateContentConfig(
                temperature=_GENERATION_CONFIG.temperature,
                top_p=_GENERATION_CONFIG.top_p,
                top_k=_GENERATION_CONFIG.top_k,
                max_output_tokens=_GENERATION_CONFIG.max_output_tokens,
                thinking_config=_GENERATION_CONFIG.thinking_config,
                http_options=types.HttpOptions(
                    timeout=self._timeout * 1000,
                ),
            )
            stream = self._client.models.generate_content_stream(
                model=self._model_name,
                contents=prompt,
                config=request_config,
            )
            text_parts: list[str] = []
            for chunk in stream:
                if chunk.text:
                    text_parts.append(chunk.text)
            response_text = "".join(text_parts)

            if not response_text:
                raise LLMException(
                    message="Gemini returned an empty response.",
                    details={"model": self._model_name},
                )

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Gemini request completed",
                extra={
                    "model": self._model_name,
                    "response_length": len(response_text),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return response_text

        except LLMException:
            raise
        except ssl.SSLError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Gemini SSL error",
                extra={
                    "model": self._model_name,
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
            )
            raise LLMException(
                message=f"Gemini SSL/TLS error: {exc}",
                details={"model": self._model_name, "error": str(exc)},
            ) from exc
        except TimeoutError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Gemini request timed out",
                extra={
                    "model": self._model_name,
                    "timeout_seconds": self._timeout,
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
            )
            raise LLMException(
                message=f"Gemini request timed out after {self._timeout}s.",
                details={"model": self._model_name, "timeout_seconds": self._timeout},
                status_code=504,
            ) from exc
        except ConnectionError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Gemini connection error",
                extra={
                    "model": self._model_name,
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
            )
            raise LLMException(
                message=f"Gemini connection failed: {exc}",
                details={"model": self._model_name, "error": str(exc)},
            ) from exc
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            error_type = type(exc).__name__
            error_msg = str(exc).lower()
            if any(kw in error_msg for kw in ("deadline", "timeout", "timed out")):
                logger.error(
                    "Gemini request timed out",
                    extra={
                        "model": self._model_name,
                        "timeout_seconds": self._timeout,
                        "error": str(exc),
                        "elapsed_ms": elapsed_ms,
                    },
                )
                raise LLMException(
                    message=f"Gemini request timed out after {self._timeout}s.",
                    details={
                        "model": self._model_name,
                        "timeout_seconds": self._timeout,
                    },
                    status_code=504,
                ) from exc
            logger.error(
                "Gemini request failed",
                extra={
                    "model": self._model_name,
                    "error_type": error_type,
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
            )
            raise LLMException(
                message=f"Gemini model call failed: {exc}",
                details={"model": self._model_name, "error": str(exc)},
            ) from exc
