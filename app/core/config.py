"""
Pydantic Settings – Typed environment configuration.

Loads variables from .env and validates at boot time (fail-fast).
"""

import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from app.core.exceptions import ValidationException


class Settings(BaseSettings):
    """Application-wide configuration parsed from environment variables."""

    # ── Application ───────────────────────────────
    APP_ENV: str = Field(default="development", description="Runtime environment")
    APP_DEBUG: bool = Field(default=False, description="Enable debug mode")
    APP_HOST: str = Field(default="0.0.0.0", description="Server bind host")
    APP_PORT: int = Field(default=8000, description="Server bind port")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")

    # ── Google Gemini (used in future tickets) ────
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")

    # ── ChromaDB (used in future tickets) ─────────
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma", description="ChromaDB persistence path"
    )

    # ── Embedding Model (Ticket 5) ─────────────────
    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence Transformer model name",
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=32, description="Batch size for embedding generation"
    )
    EMBEDDING_DEVICE: str = Field(
        default="cpu", description="Device for embedding model (cpu/cuda)"
    )

    # ── Memory ────────────────────────────────────
    MAX_HISTORY_TURNS: int = Field(
        default=5, description="Maximum conversation turns to retain per session"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    # ── Validators ─────────────────────────────────

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Ensure APP_ENV is one of the recognised values."""
        allowed = {"development", "staging", "production", "testing"}
        if v not in allowed:
            raise ValueError(
                f"APP_ENV must be one of {sorted(allowed)}, got '{v}'."
            )
        return v

    @field_validator("APP_PORT")
    @classmethod
    def validate_app_port(cls, v: int) -> int:
        """Ensure APP_PORT is within the valid TCP range."""
        if not (1 <= v <= 65535):
            raise ValueError(
                f"APP_PORT must be between 1 and 65535, got {v}."
            )
        return v

    @field_validator("EMBEDDING_BATCH_SIZE")
    @classmethod
    def validate_embedding_batch_size(cls, v: int) -> int:
        """Ensure EMBEDDING_BATCH_SIZE is positive."""
        if v <= 0:
            raise ValueError(
                f"EMBEDDING_BATCH_SIZE must be positive, got {v}."
            )
        return v

    @field_validator("MAX_HISTORY_TURNS")
    @classmethod
    def validate_max_history_turns(cls, v: int) -> int:
        """Ensure MAX_HISTORY_TURNS is positive."""
        if v <= 0:
            raise ValueError(
                f"MAX_HISTORY_TURNS must be positive, got {v}."
            )
        return v

    @field_validator("EMBEDDING_DEVICE")
    @classmethod
    def validate_embedding_device(cls, v: str) -> str:
        """Ensure EMBEDDING_DEVICE is a recognised compute device."""
        allowed = {"cpu", "cuda", "mps"}
        if v not in allowed:
            raise ValueError(
                f"EMBEDDING_DEVICE must be one of {sorted(allowed)}, got '{v}'."
            )
        return v

    # ── Custom validation (post-init) ──────────────

    def validate_runtime(self) -> list[str]:
        """Run deep configuration validation at startup.

        Checks:
          - GEMINI_API_KEY is not empty.
          - CHROMA_PERSIST_DIRECTORY parent is writable.
          - EMBEDDING_MODEL_NAME is not empty.

        Returns:
            A list of validation error messages (empty if all valid).

        Raises:
            ValidationException: If any critical configuration is invalid.
        """
        errors: list[str] = []

        if not self.GEMINI_API_KEY or not self.GEMINI_API_KEY.strip():
            errors.append(
                "GEMINI_API_KEY is required but not set. "
                "Set it in your .env file or environment."
            )

        if not self.EMBEDDING_MODEL_NAME or not self.EMBEDDING_MODEL_NAME.strip():
            errors.append("EMBEDDING_MODEL_NAME must not be empty.")

        persist_path = Path(self.CHROMA_PERSIST_DIRECTORY)
        try:
            parent = persist_path.parent
            if not parent.exists():
                os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            errors.append(
                f"CHROMA_PERSIST_DIRECTORY parent is not writable: {exc}"
            )

        if errors:
            raise ValidationException(
                message="Configuration validation failed.",
                details={"validation_errors": errors},
            )

        return errors


# Singleton instance – imported across the application
settings = Settings()
