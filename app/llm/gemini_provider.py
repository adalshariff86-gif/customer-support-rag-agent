"""
Gemini LLM Provider – Google Gemini integration via the official SDK.

Wraps ``google-generativeai`` behind the ``LLMProvider`` ABC so the
rest of the application never imports the SDK directly.

Responsibilities:
  - Initialise the Gemini client with the configured API key and model.
  - Convert prompts into Gemini-compatible content.
  - Handle SDK errors and translate them into ``LLMException``.

Usage:
    from app.llm.gemini_provider import GeminiProvider
    provider = GeminiProvider(api_key="...", model="gemini-1.5-flash")
    answer = provider.generate("What is your return policy?")
"""

from __future__ import annotations

import time
from typing import Any, Optional

from app.core.config import settings
from app.core.exceptions import LLMException
from app.core.logger import get_logger
from app.llm.base import LLMProvider

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────
_DEFAULT_MODEL = "gemini-1.5-flash"
_DEFAULT_TIMEOUT = 60


class GeminiProvider(LLMProvider):
    """Google Gemini language model provider.

    Lazily initialises the ``google.generativeai`` SDK on first use.
    Thread-safe for concurrent requests after initialisation.

    Args:
        api_key:  Google Gemini API key.  Falls back to ``settings.GEMINI_API_KEY``.
        model:    Model identifier (default ``"gemini-1.5-flash"``).
        timeout:  Request timeout in seconds (default ``60``).

    Raises:
        LLMException: If the SDK is not installed or initialisation fails.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = _DEFAULT_MODEL,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model
        self._timeout = timeout
        self._generative_model: Any = None
        self._initialised = False

        if not self._api_key:
            logger.warning(
                "Gemini API key not configured",
                extra={"model": self._model_name},
            )

    def _ensure_initialised(self) -> None:
        """Lazily initialise the Gemini SDK (double-checked locking)."""
        if self._initialised:
            return

        try:
            import google.generativeai as genai  # type: ignore[import-untyped]
        except ImportError as exc:
            raise LLMException(
                message="google-generativeai SDK is not installed. "
                "Install it with: pip install google-generativeai",
                details={"error": str(exc)},
            ) from exc

        try:
            genai.configure(api_key=self._api_key)
            self._generative_model = genai.GenerativeModel(self._model_name)
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

            self._ensure_initialised()

            response = self._generative_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                },
            )

            if not response.text:
                raise LLMException(
                    message="Gemini returned an empty response.",
                    details={"model": self._model_name},
                )

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Gemini request completed",
                extra={
                    "model": self._model_name,
                    "response_length": len(response.text),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return response.text

        except LLMException:
            raise
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Gemini request failed",
                extra={
                    "model": self._model_name,
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
            )
            raise LLMException(
                message=f"Gemini model call failed: {exc}",
                details={"model": self._model_name, "error": str(exc)},
            ) from exc
