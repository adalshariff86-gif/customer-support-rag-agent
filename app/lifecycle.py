"""
Application Lifecycle – Startup / Shutdown orchestration.

Responsibilities:
  - Validate configuration before boot.
  - Create and verify all singleton dependencies via the DI container.
  - Ensure required directories exist.
  - Verify connectivity to external providers (embedding, LLM, vector store).
  - Gracefully release resources on shutdown.
  - Provide a deep health check payload for the /health endpoint.

Design principles:
  - No business logic – this module only orchestrates infrastructure.
  - All singletons are obtained from ``app.core.dependencies``; never
    constructed manually here.
  - Every step is logged; failures are wrapped in ``StartupException``.
  - Thread-safe: ``ApplicationLifecycle`` is instantiated once per process.

Usage:
    from app.lifecycle import ApplicationLifecycle

    lifecycle = ApplicationLifecycle()
    await lifecycle.startup()
    # ... application runs ...
    await lifecycle.shutdown()
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.exceptions import (
    StartupException,
    ValidationException,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class ApplicationLifecycle:
    """Manages the full startup and shutdown lifecycle of the application.

    Attributes:
        _started_at:   UTC timestamp when ``startup()`` completed.
        _startup_ok:   ``True`` if ``startup()`` finished without error.
        _shutdown_ok:  ``True`` if ``shutdown()`` finished without error.
        _lock:         asyncio lock for concurrency-safe startup/shutdown.
    """

    def __init__(self) -> None:
        self._started_at: datetime | None = None
        self._startup_ok: bool = False
        self._shutdown_ok: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()

    # ── Startup ─────────────────────────────────────

    async def startup(self) -> None:
        """Execute the full startup sequence.

        Steps:
          1. Log application version and environment.
          2. Validate configuration (fail-fast on bad config).
          3. Ensure required directories exist.
          4. Initialise and verify every singleton dependency.
          5. Record startup completion timestamp.

        This method is idempotent – calling it multiple times is safe.
        The first call performs startup; subsequent calls return immediately.

        Raises:
            StartupException: If any step fails unexpectedly.
        """
        async with self._lock:
            if self._startup_ok:
                logger.info("Startup already completed — skipping (idempotent)")
                return

            start = time.perf_counter()

            try:
                logger.info("=== Application startup initiated ===")
                logger.info(
                    "Startup configuration",
                    extra={
                        "version": settings.APP_VERSION,
                        "environment": settings.APP_ENV,
                        "debug": settings.APP_DEBUG,
                        "host": settings.APP_HOST,
                        "port": settings.APP_PORT,
                    },
                )

                # ── 1. Validate configuration ──────────
                self._validate_configuration()

                # ── 2. Ensure directories ───────────────
                self._ensure_directories()

                # ── 3. Verify dependencies ──────────────
                self._verify_dependencies()

                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                self._started_at = datetime.now(UTC)
                self._startup_ok = True

                logger.info(
                    "=== Application startup completed ===",
                    extra={
                        "elapsed_ms": elapsed_ms,
                        "environment": settings.APP_ENV,
                        "version": settings.APP_VERSION,
                    },
                )

            except StartupException:
                raise
            except ValidationException:
                raise
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.error(
                    "Startup failed with unexpected error",
                    extra={"error": str(exc), "elapsed_ms": elapsed_ms},
                    exc_info=True,
                )
                raise StartupException(
                    message=f"Application startup failed: {exc}",
                    details={"error": str(exc), "elapsed_ms": elapsed_ms},
                ) from exc

    # ── Shutdown ────────────────────────────────────

    async def shutdown(self) -> None:
        """Execute the graceful shutdown sequence.

        Steps:
          1. Release vector store resources (reset collections + client ref).
          2. Reset singleton caches in the DI container.
          3. Clear lifecycle state.
          4. Log shutdown completion.

        This method is idempotent – calling it multiple times is safe.
        """
        async with self._lock:
            if self._shutdown_ok:
                logger.info("Shutdown already completed — skipping (idempotent)")
                return

            start = time.perf_counter()

            try:
                logger.info("=== Application shutdown initiated ===")

                self._release_vector_store()
                self._reset_singletons()
                self._clear_lifecycle_state()

                self._shutdown_ok = True

                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.info(
                    "=== Application shutdown completed ===",
                    extra={"elapsed_ms": elapsed_ms},
                )

            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.error(
                    "Shutdown error (non-fatal)",
                    extra={"error": str(exc), "elapsed_ms": elapsed_ms},
                    exc_info=True,
                )

    # ── Health Check ────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Build a deep health check payload.

        Verifies:
          - Application has completed startup.
          - Vector store is reachable.
          - Embedding provider is initialised.
          - LLM provider is configured.

        Returns:
            A dict conforming to ``HealthCheckResponse`` schema.

        Note:
            Never exposes API keys or secrets in the response.
        """
        overall_status = "healthy"
        dependencies: list[dict[str, Any]] = []

        # ── Vector Store ───────────────────────────
        vs_health = self._check_vector_store_health()
        dependencies.append(vs_health)
        if vs_health["status"] != "healthy":
            overall_status = "degraded"

        # ── Embedding Provider ─────────────────────
        emb_health = self._check_embedding_health()
        dependencies.append(emb_health)
        if emb_health["status"] != "healthy":
            overall_status = "degraded"

        # ── LLM Provider ───────────────────────────
        llm_health = self._check_llm_health()
        dependencies.append(llm_health)
        if llm_health["status"] != "healthy":
            overall_status = "degraded"

        # ── Overall ────────────────────────────────
        if not self._startup_ok:
            overall_status = "unhealthy"

        uptime_seconds: float | None = None
        if self._started_at:
            uptime_seconds = round(
                (datetime.now(UTC) - self._started_at).total_seconds(), 2
            )

        return {
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": settings.APP_ENV,
            "version": settings.APP_VERSION,
            "uptime_seconds": uptime_seconds,
            "dependencies": dependencies,
        }

    # ── Private: Configuration ─────────────────────

    def _validate_configuration(self) -> None:
        """Validate all configuration settings.

        Raises:
            ValidationException: If any setting is invalid.
        """
        logger.info("Validating configuration")
        try:
            settings.validate_runtime()
            logger.info("Configuration validation passed")
        except ValidationException:
            raise
        except Exception as exc:
            raise ValidationException(
                message=f"Configuration validation failed: {exc}",
                details={"error": str(exc)},
            ) from exc

    # ── Private: Directories ───────────────────────

    def _ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        import os
        from pathlib import Path

        directories = [
            Path(settings.CHROMA_PERSIST_DIRECTORY),
            Path(settings.CHROMA_PERSIST_DIRECTORY).parent,
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(
                    "Directory ensured",
                    extra={"path": str(directory)},
                )
            except OSError as exc:
                raise StartupException(
                    message=f"Failed to create directory '{directory}'.",
                    details={"path": str(directory), "error": str(exc)},
                ) from exc

    # ── Private: Dependency Verification ───────────

    def _verify_dependencies(self) -> None:
        """Verify every singleton can be created.

        Uses the existing DI providers from ``app.core.dependencies``.
        No manual construction – only calls the provider functions.

        Raises:
            StartupException: If any dependency fails to initialise.
        """
        logger.info("Verifying dependencies")

        dependency_checks = [
            ("vector_store", self._verify_vector_store),
            ("embedding_provider", self._verify_embedding_provider),
            ("llm_provider", self._verify_llm_provider),
            ("retrieval_service", self._verify_retrieval_service),
            ("memory_service", self._verify_memory_service),
            ("rag_orchestrator", self._verify_rag_orchestrator),
            ("chat_service", self._verify_chat_service),
        ]

        for name, check_fn in dependency_checks:
            try:
                check_fn()
                logger.info(
                    "Dependency verified",
                    extra={"dependency": name},
                )
            except StartupException:
                raise
            except Exception as exc:
                raise StartupException(
                    message=f"Failed to verify dependency '{name}'.",
                    details={"dependency": name, "error": str(exc)},
                ) from exc

        logger.info("All dependencies verified")

    def _verify_vector_store(self) -> None:
        """Verify the ChromaDB vector store singleton can be created."""
        from app.core.dependencies import get_vector_store

        store = get_vector_store()
        # Force client initialisation to verify connectivity
        store._get_client()

    def _verify_embedding_provider(self) -> None:
        """Verify the embedding provider singleton can be created."""
        from app.core.dependencies import get_embedding_provider

        provider = get_embedding_provider()
        # Ensure the provider is usable (model loads lazily)
        _ = provider.model_name

    def _verify_llm_provider(self) -> None:
        """Verify the LLM provider singleton can be created."""
        from app.core.dependencies import get_llm_service

        provider = get_llm_service()
        _ = provider.model_name

    def _verify_retrieval_service(self) -> None:
        """Verify the retrieval service singleton can be created."""
        from app.core.dependencies import get_retrieval_service

        _ = get_retrieval_service()

    def _verify_memory_service(self) -> None:
        """Verify the memory service singleton can be created."""
        from app.core.dependencies import get_memory_service

        _ = get_memory_service()

    def _verify_rag_orchestrator(self) -> None:
        """Verify the RAG orchestrator singleton can be created."""
        from app.core.dependencies import get_rag_orchestrator

        _ = get_rag_orchestrator()

    def _verify_chat_service(self) -> None:
        """Verify the chat service singleton can be created."""
        from app.core.dependencies import get_chat_service

        _ = get_chat_service()

    # ── Private: Health Checks ─────────────────────

    def _check_vector_store_health(self) -> dict[str, Any]:
        """Check vector store connectivity.

        Returns:
            A ``DependencyHealth``-compatible dict.
        """
        try:
            from app.core.dependencies import get_vector_store

            store = get_vector_store()
            start = time.perf_counter()
            client = store._get_client()
            # Simple round-trip: list collections
            client.list_collections()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            return {
                "name": "chromadb",
                "status": "healthy",
                "latency_ms": latency_ms,
                "details": {"persist_directory": settings.CHROMA_PERSIST_DIRECTORY},
                "checked_at": datetime.now(UTC).isoformat(),
            }
        except Exception as exc:
            return {
                "name": "chromadb",
                "status": "unhealthy",
                "details": {"error": str(exc)},
                "checked_at": datetime.now(UTC).isoformat(),
            }

    def _check_embedding_health(self) -> dict[str, Any]:
        """Check embedding provider status.

        Returns:
            A ``DependencyHealth``-compatible dict.
        """
        try:
            from app.core.dependencies import get_embedding_provider

            provider = get_embedding_provider()
            return {
                "name": "embedding_provider",
                "status": "healthy",
                "details": {
                    "model_name": settings.EMBEDDING_MODEL_NAME,
                    "device": settings.EMBEDDING_DEVICE,
                },
                "checked_at": datetime.now(UTC).isoformat(),
            }
        except Exception as exc:
            return {
                "name": "embedding_provider",
                "status": "unhealthy",
                "details": {"error": str(exc)},
                "checked_at": datetime.now(UTC).isoformat(),
            }

    def _check_llm_health(self) -> dict[str, Any]:
        """Check LLM provider status.

        Returns:
            A ``DependencyHealth``-compatible dict.
        """
        try:
            from app.core.dependencies import get_llm_service

            provider = get_llm_service()
            has_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
            return {
                "name": "llm_provider",
                "status": "healthy" if has_key else "degraded",
                "details": {
                    "model_name": provider.model_name,
                    "api_key_configured": has_key,
                },
                "checked_at": datetime.now(UTC).isoformat(),
            }
        except Exception as exc:
            return {
                "name": "llm_provider",
                "status": "unhealthy",
                "details": {"error": str(exc)},
                "checked_at": datetime.now(UTC).isoformat(),
            }

    # ── Private: Shutdown Helpers ──────────────────

    def _release_vector_store(self) -> None:
        """Release ChromaDB client reference without deleting data.

        ChromaDB's ``PersistentClient`` flushes data to disk automatically
        on close.  We do NOT call ``reset()`` here because that would
        destroy all persisted collections on every shutdown/restart.
        """
        try:
            from app.vectorstore.chroma_store import ChromaVectorStore

            ChromaVectorStore._client = None
            logger.info("Vector store client reference released")
        except Exception as exc:
            logger.warning(
                "Failed to release vector store resources",
                extra={"error": str(exc)},
            )

    def _reset_singletons(self) -> None:
        """Reset all singleton caches in the DI container.

        Delegates to ``app.core.dependencies.reset_singletons()`` which
        is the single source of truth for clearing the DI container.
        """
        from app.core.dependencies import reset_singletons

        reset_singletons()

    def _clear_lifecycle_state(self) -> None:
        """Clear lifecycle-internal state after shutdown."""
        self._started_at = None
        self._startup_ok = False
        logger.info("Lifecycle state cleared")
