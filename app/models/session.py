"""
Session Models – Pydantic schemas for session lifecycle management.

Defines request/response contracts for session creation, retrieval, and history.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated


class SessionCreateRequest(BaseModel):
    """Request to create a new chat session.

    Attributes:
        initial_message: Optional first message to start the conversation.
        context_override: If true, skip RAG retrieval for the first message.
    """

    initial_message: Optional[Annotated[str, StringConstraints(min_length=1, max_length=4000)]] = Field(
        default=None, description="Optional initial user message.", examples=["Hello, I need help with my account."]
    )
    context_override: bool = Field(
        default=False,
        description="If true, skip RAG retrieval for the initial message.",
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"initial_message": "Hello, I need help with my account.", "context_override": False},
                {"context_override": True},
            ]
        }
    }


class SessionCreateResponse(BaseModel):
    """Response after creating a new session.

    Attributes:
        session_id: Newly created session UUID.
        created_at: UTC timestamp of session creation.
    """

    session_id: Annotated[
        str, StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    ] = Field(..., description="New session UUID.", examples=["550e8400-e29b-41d4-a716-446655440000"])
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of session creation.",
        examples=["2024-01-15T10:30:45.123Z"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"session_id": "550e8400-e29b-41d4-a716-446655440000", "created_at": "2024-01-15T10:30:45.123Z"}
            ]
        }
    }


class SessionHistoryItem(BaseModel):
    """Single message in a session's conversation history.

    Attributes:
        role: "user" or "assistant".
        content: Message text.
        timestamp: UTC timestamp of the message.
        sources: Sources used for assistant messages (empty for user messages).
    """

    role: str = Field(..., pattern=r"^(user|assistant)$", description="Message role.", examples=["user"])
    content: str = Field(..., description="Message text.", examples=["How do I reset my password?"])
    timestamp: datetime = Field(
        ..., description="UTC timestamp of the message.", examples=["2024-01-15T10:30:45.123Z"]
    )
    sources: list[dict] = Field(
        default_factory=list,
        description="Source documents for assistant messages (empty for user messages).",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "How do I reset my password?",
                    "timestamp": "2024-01-15T10:30:45.123Z",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "To reset your password, visit the account settings page...",
                    "timestamp": "2024-01-15T10:30:47.456Z",
                    "sources": [
                        {
                            "id": "doc_abc123",
                            "content": "To reset your password, visit...",
                            "score": 0.87,
                            "metadata": {"source": "faq.md", "section": "account"},
                        }
                    ],
                },
            ]
        }
    }


class SessionHistoryResponse(BaseModel):
    """Full conversation history for a session.

    Attributes:
        session_id: Session UUID.
        created_at: Session creation timestamp.
        updated_at: Last activity timestamp.
        message_count: Total messages in history.
        history: Ordered list of messages (oldest first).
    """

    session_id: Annotated[
        str, StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    ] = Field(..., description="Session UUID.", examples=["550e8400-e29b-41d4-a716-446655440000"])
    created_at: datetime = Field(..., description="Session creation timestamp.", examples=["2024-01-15T10:30:45.123Z"])
    updated_at: datetime = Field(..., description="Last activity timestamp.", examples=["2024-01-15T10:35:12.789Z"])
    message_count: int = Field(..., ge=0, description="Total messages in history.", examples=[4])
    history: list[SessionHistoryItem] = Field(..., description="Ordered conversation history.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "created_at": "2024-01-15T10:30:45.123Z",
                    "updated_at": "2024-01-15T10:35:12.789Z",
                    "message_count": 4,
                    "history": [
                        {
                            "role": "user",
                            "content": "How do I reset my password?",
                            "timestamp": "2024-01-15T10:30:45.123Z",
                            "sources": [],
                        },
                        {
                            "role": "assistant",
                            "content": "To reset your password, visit the account settings page...",
                            "timestamp": "2024-01-15T10:30:47.456Z",
                            "sources": [
                                {
                                    "id": "doc_abc123",
                                    "content": "To reset your password, visit...",
                                    "score": 0.87,
                                    "metadata": {"source": "faq.md", "section": "account"},
                                }
                            ],
                        },
                        {
                            "role": "user",
                            "content": "Thanks!",
                            "timestamp": "2024-01-15T10:35:10.000Z",
                            "sources": [],
                        },
                        {
                            "role": "assistant",
                            "content": "You're welcome! Let me know if you need anything else.",
                            "timestamp": "2024-01-15T10:35:12.789Z",
                            "sources": [],
                        },
                    ],
                }
            ]
        }
    }


class SessionDeleteResponse(BaseModel):
    """Response after deleting a session.

    Attributes:
        session_id: Deleted session UUID.
        deleted_at: UTC timestamp of deletion.
        message: Confirmation message.
    """

    session_id: Annotated[
        str, StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    ] = Field(..., description="Deleted session UUID.", examples=["550e8400-e29b-41d4-a716-446655440000"])
    deleted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of deletion.",
        examples=["2024-01-15T10:40:00.000Z"],
    )
    message: str = Field(..., description="Confirmation message.", examples=["Session deleted successfully."])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "deleted_at": "2024-01-15T10:40:00.000Z",
                    "message": "Session deleted successfully.",
                }
            ]
        }
    }