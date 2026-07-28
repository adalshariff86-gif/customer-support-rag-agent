"""
Memory Service – In-process conversation history manager.

Stores, retrieves, and manages conversation messages per session.
Thread-safe, configurable history length, no external dependencies.

Responsibilities:
  - Store conversation messages in memory
  - Retrieve full or partial history
  - Enforce configurable message limits
  - Format history for LLM consumption
  - Session lifecycle (create, clear, delete, list)

Do NOT use for: AI responses, RAG, vector search, embedding generation.
"""

import time
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.exceptions import MemoryException, ValidationException
from app.core.logger import get_logger

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────
_VALID_ROLES: frozenset[str] = frozenset({"user", "assistant", "system"})


# ── Internal Data Models ───────────────────────────
@dataclass
class MemoryMessage:
    """Single message in conversation history.

    Attributes:
        role:     Message author – one of "user", "assistant", "system".
        content:  Message text content.
        timestamp: UTC timestamp of when the message was created.
        sources:  Source documents used for assistant messages (empty list for others).
    """

    role: str
    content: str
    timestamp: datetime
    sources: list[dict] = field(default_factory=list)


@dataclass
class Conversation:
    """A conversation session containing ordered messages.

    Attributes:
        session_id:  Unique identifier for this session.
        messages:    Ordered list of messages (oldest first).
        created_at:  UTC timestamp of session creation.
        updated_at:  UTC timestamp of last activity.
    """

    session_id: str
    messages: list[MemoryMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Memory Service ─────────────────────────────────
class MemoryService:
    """In-process conversation memory manager.

    Thread-safe storage and retrieval of conversation histories.
    Enforces configurable message limits per session.

    Example:
        >>> memory = MemoryService()
        >>> session_id = memory.create_session()
        >>> memory.add_message(session_id, "user", "Hello!")
        >>> print(memory.get_formatted_history(session_id))
        User: Hello!
    """

    def __init__(self, max_messages: Optional[int] = None) -> None:
        """Initialise the memory service.

        Args:
            max_messages: Maximum messages per session.  Defaults to
                ``settings.MAX_HISTORY_TURNS``.
        """
        self._max_messages: int = max_messages or settings.MAX_HISTORY_TURNS
        self._sessions: dict[str, Conversation] = {}
        self._lock: threading.RLock = threading.RLock()
        logger.info(
            "MemoryService initialised",
            extra={"max_messages": self._max_messages},
        )

    # ── Public API ──────────────────────────────────

    def create_session(self) -> str:
        """Create a new empty conversation session.

        Returns:
            The generated session UUID.

        Raises:
            MemoryException: If session creation fails unexpectedly.
        """
        start = time.monotonic()
        try:
            with self._lock:
                session_id = str(uuid.uuid4())
                self._sessions[session_id] = Conversation(session_id=session_id)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Session created",
                    extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                )
                return session_id
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Session creation failed",
                extra={"elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to create session.") from exc

    def session_exists(self, session_id: str) -> bool:
        """Check whether a session exists.

        Args:
            session_id: The session UUID to look up.

        Returns:
            ``True`` if the session exists, ``False`` otherwise.
        """
        self._validate_session_id(session_id)
        with self._lock:
            return session_id in self._sessions

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[list[dict]] = None,
    ) -> None:
        """Append a message to a session's conversation history.

        Automatically enforces the configured message limit by discarding
        the oldest messages when exceeded.

        Args:
            session_id: The session UUID.
            role:        Message role – "user", "assistant", or "system".
            content:     Message text content.
            sources:     Optional list of source document dicts (for assistant messages).

        Raises:
            ValidationException: If session_id, role, or content is invalid.
            MemoryException:     If the session does not exist or an error occurs.
        """
        start = time.monotonic()
        self._validate_session_id(session_id)
        self._validate_role(role)
        self._validate_content(content)
        try:
            with self._lock:
                conversation = self._get_conversation_or_raise(session_id)
                message = MemoryMessage(
                    role=role,
                    content=content,
                    timestamp=datetime.now(timezone.utc),
                    sources=sources or [],
                )
                conversation.messages.append(message)
                conversation.updated_at = message.timestamp
                self._enforce_limit(conversation)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Message added",
                    extra={
                        "session_id": session_id,
                        "role": role,
                        "message_count": len(conversation.messages),
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
        except ValidationException:
            raise
        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to add message",
                extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to add message.") from exc

    def get_messages(self, session_id: str) -> list[MemoryMessage]:
        """Retrieve all messages in a session's history.

        Args:
            session_id: The session UUID.

        Returns:
            Ordered list of ``MemoryMessage`` instances (oldest first).

        Raises:
            ValidationException: If session_id is invalid.
            MemoryException:     If the session does not exist.
        """
        start = time.monotonic()
        self._validate_session_id(session_id)
        try:
            with self._lock:
                conversation = self._get_conversation_or_raise(session_id)
                messages = list(conversation.messages)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Messages retrieved",
                    extra={
                        "session_id": session_id,
                        "message_count": len(messages),
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
                return messages
        except ValidationException:
            raise
        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to retrieve messages",
                extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to retrieve messages.") from exc

    def get_recent_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> list[MemoryMessage]:
        """Retrieve the most recent messages from a session.

        Args:
            session_id: The session UUID.
            limit:      Maximum number of messages to return.
                        Defaults to ``self._max_messages``.

        Returns:
            Ordered list of ``MemoryMessage`` instances (oldest first within the limit).

        Raises:
            ValidationException: If session_id is invalid or limit is negative.
            MemoryException:     If the session does not exist.
        """
        start = time.monotonic()
        self._validate_session_id(session_id)
        if limit is not None and limit < 0:
            raise ValidationException(
                message="Limit must be a non-negative integer.",
                details={"limit": limit},
            )
        try:
            with self._lock:
                conversation = self._get_conversation_or_raise(session_id)
                effective_limit = limit if limit is not None else self._max_messages
                messages = list(conversation.messages[-effective_limit:])
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Recent messages retrieved",
                    extra={
                        "session_id": session_id,
                        "limit": effective_limit,
                        "returned": len(messages),
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
                return messages
        except ValidationException:
            raise
        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to retrieve recent messages",
                extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to retrieve recent messages.") from exc

    def get_formatted_history(self, session_id: str) -> str:
        """Return the conversation history as a plain-text string.

        Format::

            User: How do refunds work?
            Assistant: Refunds are available for 30 days.
            User: Thank you.

        Args:
            session_id: The session UUID.

        Returns:
            Formatted conversation string, or empty string for new sessions.

        Raises:
            ValidationException: If session_id is invalid.
            MemoryException:     If the session does not exist.
        """
        start = time.monotonic()
        self._validate_session_id(session_id)
        try:
            with self._lock:
                conversation = self._get_conversation_or_raise(session_id)
                lines: list[str] = []
                for msg in conversation.messages:
                    prefix = msg.role.capitalize()
                    lines.append(f"{prefix}: {msg.content}")
                formatted = "\n".join(lines)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "History formatted",
                    extra={
                        "session_id": session_id,
                        "line_count": len(lines),
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
                return formatted
        except ValidationException:
            raise
        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to format history",
                extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to format history.") from exc

    def clear_session(self, session_id: str) -> None:
        """Remove all messages from a session while keeping it alive.

        Args:
            session_id: The session UUID.

        Raises:
            ValidationException: If session_id is invalid.
            MemoryException:     If the session does not exist.
        """
        start = time.monotonic()
        self._validate_session_id(session_id)
        try:
            with self._lock:
                conversation = self._get_conversation_or_raise(session_id)
                conversation.messages.clear()
                conversation.updated_at = datetime.now(timezone.utc)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Session cleared",
                    extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                )
        except ValidationException:
            raise
        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to clear session",
                extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to clear session.") from exc

    def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages.

        Args:
            session_id: The session UUID.

        Raises:
            ValidationException: If session_id is invalid.
            MemoryException:     If the session does not exist.
        """
        start = time.monotonic()
        self._validate_session_id(session_id)
        try:
            with self._lock:
                if session_id not in self._sessions:
                    raise MemoryException(
                        message=f"Session not found: {session_id}",
                        details={"session_id": session_id},
                    )
                del self._sessions[session_id]
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Session deleted",
                    extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                )
        except ValidationException:
            raise
        except MemoryException:
            raise
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to delete session",
                extra={"session_id": session_id, "elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to delete session.") from exc

    def list_sessions(self) -> list[str]:
        """Return a list of all active session IDs.

        Returns:
            List of session UUID strings.
        """
        start = time.monotonic()
        try:
            with self._lock:
                sessions = list(self._sessions.keys())
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "Sessions listed",
                    extra={"count": len(sessions), "elapsed_ms": round(elapsed_ms, 2)},
                )
                return sessions
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Failed to list sessions",
                extra={"elapsed_ms": round(elapsed_ms, 2)},
                exc_info=True,
            )
            raise MemoryException(message="Failed to list sessions.") from exc

    def session_count(self) -> int:
        """Return the number of active sessions.

        Returns:
            Count of sessions in memory.
        """
        try:
            with self._lock:
                count = len(self._sessions)
                logger.debug("Session count", extra={"count": count})
                return count
        except Exception as exc:
            logger.error(
                "Failed to get session count",
                exc_info=True,
            )
            raise MemoryException(message="Failed to get session count.") from exc

    # ── Private Helpers ─────────────────────────────

    def _get_conversation_or_raise(self, session_id: str) -> Conversation:
        """Retrieve a conversation or raise MemoryException if missing.

        Args:
            session_id: The session UUID.

        Returns:
            The ``Conversation`` instance.

        Raises:
            MemoryException: If the session does not exist.
        """
        conversation = self._sessions.get(session_id)
        if conversation is None:
            raise MemoryException(
                message=f"Session not found: {session_id}",
                details={"session_id": session_id},
            )
        return conversation

    def _enforce_limit(self, conversation: Conversation) -> None:
        """Trim oldest messages when the history exceeds the configured limit.

        Args:
            conversation: The conversation to trim.
        """
        excess = len(conversation.messages) - self._max_messages
        if excess > 0:
            conversation.messages = conversation.messages[excess:]
            logger.info(
                "History truncated",
                extra={
                    "session_id": conversation.session_id,
                    "removed": excess,
                    "remaining": len(conversation.messages),
                },
            )

    @staticmethod
    def _validate_session_id(session_id: str) -> None:
        """Validate the session ID parameter.

        Args:
            session_id: The session UUID string.

        Raises:
            ValidationException: If session_id is empty or blank.
        """
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValidationException(
                message="Session ID must be a non-empty, non-blank string.",
                details={"session_id": session_id},
            )

    @staticmethod
    def _validate_role(role: str) -> None:
        """Validate the message role.

        Args:
            role: The role string.

        Raises:
            ValidationException: If role is not one of the allowed values.
        """
        if role not in _VALID_ROLES:
            raise ValidationException(
                message=f"Invalid role: '{role}'. Must be one of: {', '.join(sorted(_VALID_ROLES))}.",
                details={"role": role, "valid_roles": sorted(_VALID_ROLES)},
            )

    @staticmethod
    def _validate_content(content: str) -> None:
        """Validate the message content.

        Args:
            content: The message content string.

        Raises:
            ValidationException: If content is empty or blank.
        """
        if not isinstance(content, str) or not content.strip():
            raise ValidationException(
                message="Message content must be a non-empty, non-blank string.",
                details={"content": content},
            )
