"""
RAG Orchestrator – Central coordination layer for the customer support agent.

Combines Memory Service, Retrieval Service, and LLM Provider into a
single orchestration pipeline.

The orchestrator is responsible only for:
- validating chat input
- managing session lifecycle
- coordinating memory
- coordinating retrieval
- constructing the LLM prompt
- calling the LLM
- assembling the final response
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

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


_SYSTEM_INSTRUCTIONS = (
    "You are a helpful customer support assistant for TechStore. "
    "You MUST answer using only the information contained in the provided "
    "Retrieved Knowledge and conversation history.\n\n"

    "GROUNDING RULES:\n"
    "1. Retrieved Knowledge is the authoritative source for factual answers "
    "about TechStore.\n"

    "2. Never invent, assume, or guess facts that are not supported by the "
    "Retrieved Knowledge.\n"

    "3. If the user's question contains a claim or assumption that conflicts "
    "with the Retrieved Knowledge, ignore the user's claim and answer using "
    "the Retrieved Knowledge.\n"

    "4. If the Retrieved Knowledge says a policy is 7 days and the user asks "
    "about 30 days, do NOT repeat or accept 30 days as the policy. State the "
    "actual 7-day policy clearly.\n"

    "5. If the answer cannot be found in the Retrieved Knowledge, explicitly "
    "say that the information is not available in the knowledge base.\n"

    "6. Do not use outside knowledge for TechStore-specific questions.\n"

    "7. Keep answers concise, professional, friendly, and directly relevant "
    "to the user's question."
)


class RAGOrchestrator:
    """
    Central coordinator for the RAG-based customer support chat pipeline.

    Coordinates:
        - RetrievalService
        - MemoryService
        - LLMProvider

    The orchestrator does not implement vector search, embeddings,
    memory storage, or LLM SDK logic directly.
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_session(self) -> str:
        """Create a new conversation session."""

        try:
            session_id = self._memory_service.create_session()

            logger.info(
                "Session created via orchestrator",
                extra={"session_id": session_id},
            )

            return session_id

        except MemoryException:
            raise

        except Exception as exc:
            raise MemoryException(
                message="Failed to create session via orchestrator.",
                details={"error": str(exc)},
            ) from exc

    def chat(self, session_id: str | None, query: str) -> ChatResponse:
        """
        Process a user message through the complete RAG pipeline.

        Session behaviour:
            - No session ID -> create a new session.
            - Existing session ID -> continue that session.
            - Invalid/non-existent session ID -> raise MemoryException.

        This prevents accidental creation of a new conversation when
        the client supplies an old or invalid session ID.
        """

        pipeline_start = time.perf_counter()

        try:
            # ----------------------------------------------------------
            # 1. Validate
            # ----------------------------------------------------------

            validated_session_id, validated_query = self._validate(
                session_id,
                query,
            )

            logger.info(
                "RAG pipeline started",
                extra={
                    "session_id": validated_session_id or "new",
                    "query_length": len(validated_query),
                },
            )

            # ----------------------------------------------------------
            # 2. Ensure session
            # ----------------------------------------------------------

            effective_session_id = self._ensure_session(
                validated_session_id
            )

            # ----------------------------------------------------------
            # 3. Store user message
            # ----------------------------------------------------------

            self._store_user_message(
                effective_session_id,
                validated_query,
            )

            # ----------------------------------------------------------
            # 4. Retrieve knowledge
            # ----------------------------------------------------------

            retrieved_context = self._retrieve_context(
                validated_query
            )

            # ----------------------------------------------------------
            # 5. Read conversation history
            # ----------------------------------------------------------

            conversation_history = self._read_history(
                effective_session_id
            )

            # ----------------------------------------------------------
            # 6. Build prompt
            # ----------------------------------------------------------

            messages = self._build_messages(
                conversation_history=conversation_history,
                retrieved_context=retrieved_context.context,
                query=validated_query,
            )

            # ----------------------------------------------------------
            # 7. Generate LLM response
            # ----------------------------------------------------------

            llm_response = self._generate_response(messages)

            # ----------------------------------------------------------
            # 8. Store assistant response
            # ----------------------------------------------------------

            source_dicts = [
                {
                    "id": doc.id,
                    "content": doc.content,
                    "score": doc.score,
                }
                for doc in retrieved_context.documents
            ]

            self._store_assistant_message(
                session_id=effective_session_id,
                content=llm_response,
                sources=source_dicts,
            )

            # ----------------------------------------------------------
            # 9. Build response
            # ----------------------------------------------------------

            elapsed_ms = round(
                (time.perf_counter() - pipeline_start) * 1000,
                2,
            )

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
                timestamp=datetime.now(UTC),
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

        except (
            ValidationException,
            MemoryException,
            RetrievalException,
            LLMException,
        ):
            raise

        except Exception as exc:
            elapsed_ms = round(
                (time.perf_counter() - pipeline_start) * 1000,
                2,
            )

            logger.error(
                "RAG pipeline failed",
                extra={
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
                exc_info=True,
            )

            raise RAGException(
                message="An unexpected error occurred in the RAG pipeline.",
                details={
                    "error": str(exc),
                    "query_length": (
                        len(query)
                        if isinstance(query, str)
                        else 0
                    ),
                },
            ) from exc

    # ------------------------------------------------------------------
    # Session handling
    # ------------------------------------------------------------------

    def _ensure_session(self, session_id: str) -> str:
        """
        Resolve the session.

        IMPORTANT:
        We only auto-create a session when no session ID was supplied.

        If the caller explicitly supplies a session ID that does not exist,
        we raise an error instead of silently creating a different session.
        """

        # No session supplied -> create one.
        if not session_id:
            new_session_id = self._memory_service.create_session()

            logger.info(
                "New session created",
                extra={"new_session_id": new_session_id},
            )

            return new_session_id

        # Existing session -> continue conversation.
        if self._memory_service.session_exists(session_id):
            logger.info(
                "Existing session found",
                extra={"session_id": session_id},
            )

            return session_id

        # Supplied session does not exist.
        logger.warning(
            "Requested session does not exist",
            extra={"session_id": session_id},
        )

        raise MemoryException(
            message=f"Session not found: {session_id}",
            details={"session_id": session_id},
        )

    def get_session_messages(
        self, session_id: str
    ) -> list:
        """Retrieve all messages for a given session.

        Args:
            session_id: The session UUID.

        Returns:
            List of MemoryMessage instances.

        Raises:
            ValidationException: If session_id is invalid.
            MemoryException:     If the session does not exist.
        """
        try:
            return self._memory_service.get_messages(session_id)

        except (ValidationException, MemoryException):
            raise

        except Exception as exc:
            raise MemoryException(
                message="Failed to retrieve session messages.",
                details={
                    "session_id": session_id,
                    "error": str(exc),
                },
            ) from exc

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(
        self,
        session_id: str | None,
        query: str,
    ) -> tuple[str, str]:
        """Validate and sanitise incoming parameters."""

        if not isinstance(query, str) or not query.strip():
            raise ValidationException(
                message="Query must not be empty or whitespace-only.",
                details={
                    "field": "query",
                    "value": repr(query),
                },
            )

        validated_query = query.strip()

        if session_id is not None and not isinstance(session_id, str):
            raise ValidationException(
                message="Session ID must be a string when provided.",
                details={
                    "field": "session_id",
                    "value": repr(session_id),
                },
            )

        validated_session_id = (
            session_id.strip()
            if session_id
            else ""
        )

        return validated_session_id, validated_query

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def _store_user_message(
        self,
        session_id: str,
        query: str,
    ) -> None:
        """Store the user's message."""

        try:
            self._memory_service.add_message(
                session_id=session_id,
                role="user",
                content=query,
            )

        except (ValidationException, MemoryException):
            raise

        except Exception as exc:
            raise MemoryException(
                message="Failed to store user message.",
                details={
                    "session_id": session_id,
                    "error": str(exc),
                },
            ) from exc

    def _read_history(self, session_id: str) -> str:
        """Read formatted conversation history."""

        try:
            return self._memory_service.get_formatted_history(
                session_id
            )

        except MemoryException:
            raise

        except Exception as exc:
            raise MemoryException(
                message="Failed to read conversation history.",
                details={
                    "session_id": session_id,
                    "error": str(exc),
                },
            ) from exc

    def _store_assistant_message(
        self,
        session_id: str,
        content: str,
        sources: list[dict],
    ) -> None:
        """Store the assistant response."""

        try:
            self._memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=content,
                sources=sources,
            )

        except (ValidationException, MemoryException):
            raise

        except Exception as exc:
            raise MemoryException(
                message="Failed to store assistant response.",
                details={
                    "session_id": session_id,
                    "error": str(exc),
                },
            ) from exc

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def _retrieve_context(self, query: str):
        """Retrieve relevant knowledge."""

        try:
            return self._retrieval_service.retrieve(
                query=query
            )

        except RetrievalException:
            raise

        except Exception as exc:
            raise RetrievalException(
                message="Context retrieval failed in RAG pipeline.",
                details={
                    "error": str(exc),
                    "query_length": len(query),
                },
            ) from exc

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        conversation_history: str,
        retrieved_context: str,
        query: str,
    ) -> str:
        """Build the complete LLM prompt as a single string.

        This method is retained for backward compatibility with providers
        that only support a single-prompt interface.  The orchestrator
        uses ``_build_messages()`` when calling ``generate_messages()``.
        """

        parts: list[str] = [
            _SYSTEM_INSTRUCTIONS
        ]

        if conversation_history:
            parts.append(
                f"\nConversation History:\n"
                f"{conversation_history}"
            )

        if retrieved_context:
            parts.append(
                f"\nRetrieved Knowledge:\n"
                f"{retrieved_context}"
            )

        parts.append(
            f"\nUser Question:\n{query}"
        )

        parts.append("\nAnswer:")

        return "\n".join(parts)

    def _build_messages(
        self,
        conversation_history: str,
        retrieved_context: str,
        query: str,
    ) -> list[dict]:
        """Build structured chat messages for the LLM.

        Returns a list of message dicts with ``role`` and ``content`` keys.
        Uses ``system`` role for grounding rules and context, and ``user``
        role for conversation history and the current question.  This format
        produces much better results with free OpenRouter models.
        """

        system_parts: list[str] = [
            _SYSTEM_INSTRUCTIONS,
        ]

        if conversation_history:
            system_parts.append(
                f"Conversation History:\n{conversation_history}"
            )

        if retrieved_context:
            system_parts.append(
                f"Retrieved Knowledge:\n{retrieved_context}"
            )

        messages: list[dict] = [
            {
                "role": "system",
                "content": "\n\n".join(system_parts),
            },
            {
                "role": "user",
                "content": query,
            },
        ]

        return messages

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    def _generate_response(self, messages: list[dict]) -> str:
        """Generate the response through the injected LLM provider.

        Uses ``generate_messages()`` when available for structured chat
        formatting (system + user roles).  Falls back to ``generate()``
        with a concatenated prompt for providers that don't support it.
        """

        try:
            if hasattr(self._llm_provider, "generate_messages"):
                response = self._llm_provider.generate_messages(messages)
            else:
                # Fallback: concatenate all messages into a single prompt
                prompt = "\n\n".join(
                    f"[{m['role'].upper()}]\n{m['content']}"
                    for m in messages
                )
                response = self._llm_provider.generate(prompt)

            if not isinstance(response, str) or not response.strip():
                raise LLMException(
                    message="LLM returned an empty response."
                )

            return response.strip()

        except LLMException:
            raise

        except Exception as exc:
            raise LLMException(
                message="LLM generation failed in RAG pipeline.",
                details={
                    "model": self._llm_provider.model_name,
                    "error": str(exc),
                },
            ) from exc
