"""
Pydantic Settings – Typed environment configuration.

Loads variables from .env and validates at boot time (fail-fast).
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application-wide configuration parsed from environment variables."""

    # ── Application ───────────────────────────────
    APP_ENV: str = Field(default="development", description="Runtime environment")
    APP_DEBUG: bool = Field(default=False, description="Enable debug mode")
    APP_HOST: str = Field(default="0.0.0.0", description="Server bind host")
    APP_PORT: int = Field(default=8000, description="Server bind port")

    # ── Google Gemini (used in future tickets) ────
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")

    # ── ChromaDB (used in future tickets) ─────────
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma", description="ChromaDB persistence path"
    )

    # ── Embedding Model (used in future tickets) ──
    EMBEDDING_MODEL_NAME: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformer model name"
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


# Singleton instance – imported across the application
settings = Settings()
