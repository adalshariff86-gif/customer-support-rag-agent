"""
Chat Service – Business layer for the customer support RAG agent.

Coordinates client requests and delegates all AI work to the
RAGOrchestrator.  Contains NO retrieval logic, NO memory logic,
NO embedding logic, NO vector search, and NO prompt engineering.

Design principles:
  - Single Responsibility: validates requests, invokes orchestrator, returns responses.
  - Dependency Injection: receives only RAGOrchestrator; never instantiates services.
  - Open/Closed: new business rules added without modifying existing code.
  - Clean Architecture: business layer depends only on the orchestrator interface.

Usage:
    from app.services.chat_service import ChatService
    service = ChatService(orchestrator=orchestrator)
    response = service.chat(request=ChatRequest(message="Hello"))
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import (
    ChatException,
    LLMException,
    MemoryException,
    RAGException,
    RetrievalException,
    ValidationException,
)
from app.core.logger import get_logger
from app.models.chat import ChatRequest, ChatResponse
from app.services.rag_orchestrator import RAGOrchestrator

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────
_SERVICE_VERSION: str = "1.0.0"


class ChatService:
    """Business layer for the customer support RAG chat pipeline.

    Validates incoming requests, delegates all AI and retrieval work to the
    injected ``RAGOrchestrator``, and returns structured responses.  This
    service contains zero retrieval, memory, embedding, or prompt logic.

    Args:
        orchestrator: Injected RAG orchestrator for all AI pipeline operations.

    Thread Safety:
        This class holds no mutable state.  Thread safety is guaranteed by
        the singleton pattern enforced via Dependency Injection and the
        immutability of instance attributes.
    """

    def __init__(self, orchestrator: RAGOrchestrator) -> None:
        self._orchestrator = orchestrator
        logger.info("ChatService initialised")

    # ── Public API ─────────────────────────────────

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request through the RAG pipeline.

        Validates the request, delegates to the orchestrator, and returns
        the assembled response.  No retrieval, memory, or LLM logic is
        executed directly.

        Args:
            request: Validated chat request payload.

        Returns:
            A ``ChatResponse`` with the assistant's answer, sources, and metadata.

        Raises:
            ValidationException: If the request fails business validation.
            MemoryException:     Propagated from memory operations.
            RetrievalException:  Propagated from retrieval operations.
            LLMException:        Propagated from LLM generation.
            RAGException:        Propagated from orchestrator pipeline errors.
            ChatException:       Wraps any unexpected failure.
        """
        start_time = time.perf_counter()

        try:
            logger.info(
                "Chat request started",
                extra={"query_length": len(request.message)},
            )

            self._validate_request(request)

            response = self._execute_chat(request)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Chat request completed",
                extra={
                    "session_id": response.session_id,
                    "query_length": len(request.message),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return response

        except (ValidationException, MemoryException, RetrievalException, LLMException, RAGException):
            raise
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "Chat request failed",
                extra={
                    "query_length": len(request.message),
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise ChatException(
                message="An unexpected error occurred in the chat service.",
                details={"error": str(exc), "query_length": len(request.message)},
            ) from exc

    def new_chat(self) -> str:
        """Create a new conversation session.

        Delegates session creation to the orchestrator, which in turn
        uses the injected MemoryService.  No custom IDs are generated
        manually.

        Returns:
            A new session UUID string.

        Raises:
            MemoryException: Propagated from session creation failures.
            ChatException:   Wraps any unexpected failure.
        """
        start_time = time.perf_counter()

        try:
            logger.info("New chat session requested")

            session_id = self._orchestrator.create_session()

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "New chat session created",
                extra={
                    "session_id": session_id,
                    "elapsed_ms": elapsed_ms,
                },
            )

            return session_id

        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "New chat session creation failed",
                extra={
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise ChatException(
                message="Failed to create a new chat session.",
                details={"error": str(exc)},
            ) from exc

    def health_check(self) -> dict[str, Any]:
        """Return service health status without external calls.

        Provides a lightweight health check that confirms the service
        is running.  Performs no database writes or external API calls.

        Returns:
            A dict with status, service name, UTC timestamp, and version.
        """
        return self._build_health_response()

    # ── Private Helpers ────────────────────────────

    def _validate_request(self, request: ChatRequest) -> None:
        """Validate the incoming chat request.

        Rejects empty queries and whitespace-only queries.  Pydantic
        handles structural validation; this method enforces business rules.

        Args:
            request: The chat request to validate.

        Raises:
            ValidationException: If the query is empty or whitespace-only.
        """
        query = request.message

        if not query or not query.strip():
            raise ValidationException(
                message="Query must not be empty or whitespace-only.",
                details={"field": "message", "value": repr(query)},
            )

        logger.info(
            "Request validation passed",
            extra={"query_length": len(query)},
        )

    def _execute_chat(self, request: ChatRequest) -> ChatResponse:
        """Delegate chat execution to the RAG orchestrator.

        Converts the ``ChatRequest`` into the orchestrator's expected
        parameters and returns the orchestrator's response directly.

        Args:
            request: The validated chat request.

        Returns:
            The ``ChatResponse`` from the orchestrator.

        Raises:
            MemoryException:     Propagated from memory operations.
            RetrievalException:  Propagated from retrieval operations.
            LLMException:        Propagated from LLM generation.
            RAGException:        Propagated from orchestrator errors.
        """
        logger.info("Delegating to RAG orchestrator")

        response = self._orchestrator.chat(
            session_id=request.session_id or "",
            query=request.message,
        )

        return response

    def _build_health_response(self) -> dict[str, Any]:
        """Build the service health check response.

        Returns:
            A dict containing status, service name, timestamp, and version.
        """
        return {
            "status": "healthy",
            "service": "chat",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": _SERVICE_VERSION,
        }
