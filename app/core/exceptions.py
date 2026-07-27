"""
Domain Exception Hierarchy – Maps application failures to HTTP status codes.

Design principles:
  - Every exception carries a ``status_code``, ``error_code``, ``message``,
    and optional ``details`` for RFC 7807 Problem Details responses.
  - FastAPI exception handlers in ``main.py`` catch ``AppException`` and
    serialize it to a standardized JSON error body.
  - Subclasses represent specific failure domains (LLM, VectorDB, etc.)
    so the API layer can return the correct HTTP code without inspecting
    exception internals.

Usage:
    from app.core.exceptions import LLMException
    raise LLMException(
        message="Gemini API timed out",
        details={"timeout_seconds": 30},
    )
"""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for all application-level errors.

    Attributes:
        status_code: HTTP status code to return (default 500).
        error_code:  Machine-readable error identifier (e.g. ``INTERNAL_ERROR``).
        message:     Human-readable error description.
        details:     Optional dict with additional context for debugging.
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        details: Optional[dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to RFC 7807 Problem Details JSON structure."""
        return {
            "type": f"errors/{self.error_code.lower()}",
            "title": self.error_code.replace("_", " ").title(),
            "status": self.status_code,
            "detail": self.message,
            "errors": self.details if self.details else None,
        }


# ── Validation ────────────────────────────────────
class ValidationException(AppException):
    """Raised when request data fails business validation rules.

    Maps to HTTP 422 Unprocessable Entity.
    """

    status_code: int = 422
    error_code: str = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str = "Validation failed.",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Configuration ─────────────────────────────────
class ConfigurationException(AppException):
    """Raised when required configuration is missing or invalid.

    Maps to HTTP 500 (should halt application at startup).
    """

    status_code: int = 500
    error_code: str = "CONFIGURATION_ERROR"

    def __init__(
        self,
        message: str = "Application configuration error.",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── LLM / Gemini ──────────────────────────────────
class LLMException(AppException):
    """Raised when the upstream LLM provider (Gemini) fails.

    Maps to HTTP 502 Bad Gateway (upstream failure)
    or HTTP 504 Gateway Timeout.
    """

    status_code: int = 502
    error_code: str = "LLM_ERROR"

    def __init__(
        self,
        message: str = "Language model service failed.",
        details: Optional[dict[str, Any]] = None,
        status_code: int = 502,
    ) -> None:
        super().__init__(message=message, details=details, status_code=status_code)


# ── Vector Store / ChromaDB ───────────────────────
class VectorStoreException(AppException):
    """Raised when vector database operations fail.

    Maps to HTTP 500 Internal Server Error.
    """

    status_code: int = 500
    error_code: str = "VECTOR_STORE_ERROR"

    def __init__(
        self,
        message: str = "Vector store operation failed.",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Memory ────────────────────────────────────────
class MemoryException(AppException):
    """Raised when conversation memory operations fail.

    Maps to HTTP 500 Internal Server Error
    or HTTP 404 if session not found.
    """

    status_code: int = 500
    error_code: str = "MEMORY_ERROR"

    def __init__(
        self,
        message: str = "Memory service error.",
        details: Optional[dict[str, Any]] = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, details=details, status_code=status_code)


# ── Document Ingestion ────────────────────────────
class DocumentException(AppException):
    """Raised when document loading, parsing, or chunking fails.

    Maps to HTTP 500 Internal Server Error.
    """

    status_code: int = 500
    error_code: str = "DOCUMENT_ERROR"

    def __init__(
        self,
        message: str = "Document processing failed.",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)
