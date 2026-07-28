"""
RAG Orchestrator – Central coordination layer for the customer support agent.

Combines Memory Service, Retrieval Service, and LLM Provider into a
single production-ready orchestration pipeline.  This is the ONLY public
entry point for chat interactions.

Design principles:
  - Single Responsibility: orchestrates services, does NOT implement them.
  - Dependency Injection: all collaborators are injected, never constructed.
  - Open/Closed: new pipelines can be added without modifying existing code.
  - No FastAPI routes, no UI, no vector search, no embedding generation.

Usage:
    from app.services.rag_orchestrator import RAGOrchestrator
    orchestrator = RAGOrchestrator(
        retrieval_service=retrieval,
        memory_service=memory,
        llm_provider=llm,
    )
    response = orchestrator.chat(session_id="abc-123", query="How do I reset?")
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import (
    LLMException,
    MemoryException,
    RAGException,
    RetrievalException,
    ValidationException,
)
from app.core.logger import get_logger
from app.llm.base import LLMProvider
from app.models.chat import ChatResponse, SourceDocument
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService

logger = get_logger(__name__)

# ── System Instructions ───────────────────────────
_SYSTEM_INSTRUCTIONS = (
    "You are a helpful customer support assistant. "
    "Answer the user's question based on the provided knowledge base. "
    "If the knowledge base does not contain relevant information, "
    "say so clearly and offer to help in another way. "
    "Be concise, professional, and friendly."
)


class RAGOrchestrator:
    """Central coordinator for the RAG-based customer support chat pipeline.

    Orchestrates three injected services:
      - ``RetrievalService`` – vector search and context formatting.
      - ``MemoryService`` – conversation history management.
      - ``LLMProvider`` – language model generation.

    The orchestrator never duplicates retrieval, memory, or embedding logic.
    It delegates entirely to the injected services and only handles
    prompt construction, pipeline sequencing, and response assembly.

    Args:
        retrieval_service: Injected retrieval service for context gathering.
        memory_service:    Injected memory service for conversation history.
        llm_provider:      Injected LLM provider for text generation.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        memory_service: MemoryService,
        llm_provider: LLMProvider,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._memory_service = memory_service
        self._llm_provider = llm_provider
        logger.info(
            "RAGOrchestrator initialised",
            extra={"llm_model": llm_provider.model_name},
        )

    # ── Public API ─────────────────────────────────

    def chat(self, session_id: str, query: str) -> ChatResponse:
        """Process a user chat message through the full RAG pipeline.

        Pipeline steps:
          1. Validate inputs (reject empty query, invalid session).
          2. Ensure session exists (auto-create if missing).
          3. Store user message in memory.
          4. Retrieve relevant context via RetrievalService.
          5. Read conversation history via MemoryService.
          6. Build a single prompt combining instructions, history, context, and query.
          7. Call the LLM exactly once.
          8. Store the assistant response in memory.
          9. Return a ChatResponse.

        Args:
            session_id: UUID of the conversation session.  May be empty
                        for a new conversation (a session will be created).
            query:      The user's message text.

        Returns:
            A ``ChatResponse`` with the assistant's answer, sources, and metadata.

        Raises:
            ValidationException:  If query is empty/whitespace or session_id
                                  is invalid.
            MemoryException:      Propagated from memory operations.
            RetrievalException:   Propagated from retrieval operations.
            LLMException:         Propagated from LLM generation.
            RAGException:         Wraps any unexpected failure.
        """
        pipeline_start = time.perf_counter()

        try:
            # ── 1. Validate ────────────────────────
            logger.info(
                "RAG pipeline started",
                extra={"query_length": len(query)},
            )
            validated_session_id, validated_query = self._validate(
                session_id, query
            )

            # ── 2. Ensure session exists ───────────
            effective_session_id = self._ensure_session(validated_session_id)

            # ── 3. Store user message ──────────────
            self._store_user_message(effective_session_id, validated_query)

            # ── 4. Retrieve context ────────────────
            retrieved_context = self._retrieve_context(validated_query)

            # ── 5. Read conversation history ───────
            conversation_history = self._read_history(effective_session_id)

            # ── 6. Build prompt ────────────────────
            prompt = self._build_prompt(
                conversation_history=conversation_history,
                retrieved_context=retrieved_context.context,
                query=validated_query,
            )

            # ── 7. Call LLM ───────────────────────
            llm_response = self._generate_response(prompt)

            # ── 8. Store assistant response ────────
            source_dicts = [
                {"id": doc.id, "content": doc.content, "score": doc.score}
                for doc in retrieved_context.documents
            ]
            self._store_assistant_message(
                effective_session_id, llm_response, source_dicts
            )

            # ── 9. Build response ──────────────────
            elapsed_ms = round((time.perf_counter() - pipeline_start) * 1000, 2)

            sources = [
                SourceDocument(
                    id=doc.id,
                    content=doc.content,
                    score=doc.score,
                    metadata=doc.metadata,
                )
                for doc in retrieved_context.documents
            ]

            response = ChatResponse(
                session_id=effective_session_id,
                answer=llm_response,
                sources=sources,
                model=self._llm_provider.model_name,
                latency_ms=int(elapsed_ms),
                timestamp=datetime.now(timezone.utc),
            )

            logger.info(
                "RAG pipeline completed",
                extra={
                    "session_id": effective_session_id,
                    "query_length": len(validated_query),
                    "document_count": len(sources),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return response

        except (ValidationException, MemoryException, RetrievalException, LLMException):
            raise
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - pipeline_start) * 1000, 2)
            logger.error(
                "RAG pipeline failed",
                extra={"error": str(exc), "elapsed_ms": elapsed_ms},
                exc_info=True,
            )
            raise RAGException(
                message="An unexpected error occurred in the RAG pipeline.",
                details={"error": str(exc), "query_length": len(query)},
            ) from exc

    # ── Private Helpers ────────────────────────────

    def _validate(self, session_id: str, query: str) -> tuple[str, str]:
        """Validate and sanitise the incoming request parameters.

        Args:
            session_id: The session UUID from the request.
            query:      The user's message text.

        Returns:
            A tuple of (validated_session_id, validated_query).

        Raises:
            ValidationException: If query is empty/whitespace or session_id
                                 is invalid.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValidationException(
                message="Query must not be empty or whitespace-only.",
                details={"field": "query", "value": repr(query)},
            )

        validated_query = query.strip()

        if session_id is not None and (
            not isinstance(session_id, str) or not session_id.strip()
        ):
            raise ValidationException(
                message="Session ID must be a non-empty string when provided.",
                details={"field": "session_id", "value": repr(session_id)},
            )

        validated_session_id = session_id.strip() if session_id else ""

        logger.info(
            "Validation completed",
            extra={
                "session_id": validated_session_id or "new",
                "query_length": len(validated_query),
            },
        )

        return validated_session_id, validated_query

    def _ensure_session(self, session_id: str) -> str:
        """Ensure a conversation session exists, creating one if needed.

        Args:
            session_id: The session UUID.  May be empty for new conversations.

        Returns:
            The effective session UUID (existing or newly created).

        Raises:
            MemoryException: If session creation fails unexpectedly.
        """
        if session_id and self._memory_service.session_exists(session_id):
            logger.info(
                "Existing session found",
                extra={"session_id": session_id},
            )
            return session_id

        new_session_id = self._memory_service.create_session()
        logger.info(
            "New session created",
            extra={
                "original_session_id": session_id or "none",
                "new_session_id": new_session_id,
            },
        )
        return new_session_id

    def _store_user_message(self, session_id: str, query: str) -> None:
        """Append the user's message to conversation memory.

        Args:
            session_id: The session UUID.
            query:      The user's message text.

        Raises:
            MemoryException: If the message cannot be stored.
        """
        try:
            self._memory_service.add_message(
                session_id=session_id,
                role="user",
                content=query,
            )
            logger.info(
                "User message stored",
                extra={"session_id": session_id, "query_length": len(query)},
            )
        except (ValidationException, MemoryException):
            raise
        except Exception as exc:
            raise MemoryException(
                message="Failed to store user message.",
                details={"session_id": session_id, "error": str(exc)},
            ) from exc

    def _retrieve_context(self, query: str) -> "RetrievedContext":
        """Retrieve relevant context from the knowledge base.

        Delegates entirely to ``RetrievalService.retrieve()``.  Does NOT
        perform vector search or embedding generation directly.

        Args:
            query: The user's search query.

        Returns:
            A ``RetrievedContext`` with documents and formatted context.

        Raises:
            RetrievalException: If retrieval fails.
        """
        try:
            logger.info("Retrieval started", extra={"query_length": len(query)})
            context = self._retrieval_service.retrieve(query=query)
            logger.info(
                "Retrieval completed",
                extra={
                    "document_count": context.document_count,
                    "elapsed_ms": context.elapsed_ms,
                },
            )
            return context
        except RetrievalException:
            raise
        except Exception as exc:
            raise RetrievalException(
                message="Context retrieval failed in RAG pipeline.",
                details={"error": str(exc), "query_length": len(query)},
            ) from exc

    def _read_history(self, session_id: str) -> str:
        """Read formatted conversation history from memory.

        Delegates entirely to ``MemoryService.get_formatted_history()``.

        Args:
            session_id: The session UUID.

        Returns:
            Formatted conversation history string.

        Raises:
            MemoryException: If history retrieval fails.
        """
        try:
            history = self._memory_service.get_formatted_history(session_id)
            logger.info(
                "Conversation history read",
                extra={
                    "session_id": session_id,
                    "history_length": len(history),
                },
            )
            return history
        except MemoryException:
            raise
        except Exception as exc:
            raise MemoryException(
                message="Failed to read conversation history.",
                details={"session_id": session_id, "error": str(exc)},
            ) from exc

    def _build_prompt(
        self,
        conversation_history: str,
        retrieved_context: str,
        query: str,
    ) -> str:
        """Construct the full prompt for the LLM.

        Combines system instructions, conversation history, retrieved
        knowledge, and the current user question into a single prompt
        string.  This is the only place where prompt construction occurs.

        Layout:
            System Instructions
            Conversation History: ...
            Retrieved Knowledge: ...
            User Question: ...
            Answer:

        Args:
            conversation_history: Formatted conversation history.
            retrieved_context:    Formatted retrieved context from knowledge base.
            query:                The current user question.

        Returns:
            The fully constructed prompt string.
        """
        parts: list[str] = [_SYSTEM_INSTRUCTIONS]

        if conversation_history:
            parts.append(f"\nConversation History:\n{conversation_history}")

        if retrieved_context:
            parts.append(f"\nRetrieved Knowledge:\n{retrieved_context}")

        parts.append(f"\nUser Question:\n{query}")
        parts.append("\nAnswer:")

        prompt = "\n".join(parts)

        logger.info(
            "Prompt built",
            extra={"prompt_length": len(prompt)},
        )

        return prompt

    def _generate_response(self, prompt: str) -> str:
        """Call the LLM to generate a response.

        Delegates entirely to ``LLMProvider.generate()``.  Does NOT
        instantiate the Gemini SDK directly.

        Args:
            prompt: The fully constructed prompt string.

        Returns:
            The LLM's generated text response.

        Raises:
            LLMException: If the LLM call fails.
        """
        try:
            logger.info(
                "LLM request started",
                extra={
                    "model": self._llm_provider.model_name,
                    "prompt_length": len(prompt),
                },
            )
            response = self._llm_provider.generate(prompt)
            logger.info(
                "LLM request completed",
                extra={
                    "model": self._llm_provider.model_name,
                    "response_length": len(response),
                },
            )
            return response
        except LLMException:
            raise
        except Exception as exc:
            raise LLMException(
                message="LLM generation failed in RAG pipeline.",
                details={"model": self._llm_provider.model_name, "error": str(exc)},
            ) from exc

    def _store_assistant_message(
        self,
        session_id: str,
        content: str,
        sources: list[dict],
    ) -> None:
        """Save the assistant's response to conversation memory.

        Args:
            session_id: The session UUID.
            content:    The assistant's response text.
            sources:    List of source document metadata dicts.

        Raises:
            MemoryException: If the message cannot be stored.
        """
        try:
            self._memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=content,
                sources=sources,
            )
            logger.info(
                "Assistant message stored",
                extra={
                    "session_id": session_id,
                    "response_length": len(content),
                    "source_count": len(sources),
                },
            )
        except (ValidationException, MemoryException):
            raise
        except Exception as exc:
            raise MemoryException(
                message="Failed to store assistant response.",
                details={"session_id": session_id, "error": str(exc)},
            ) from exc
