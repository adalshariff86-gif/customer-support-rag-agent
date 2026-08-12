"""
Chat Request/Response Models – Pydantic schemas for the chat endpoint.

Defines the contract between the API layer and the ChatService.
All fields include validation constraints and OpenAPI examples.
"""

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints


class ChatRequest(BaseModel):
    """Request payload for a single chat interaction.

    Attributes:
        session_id: UUID of the conversation session (created on first message).
        message: User's input text (1-4000 characters).
        context_override: Optional flag to bypass RAG retrieval for testing.
    """

    session_id: (
        Annotated[
            str,
            StringConstraints(
                pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
            ),
        ]
        | None
    ) = Field(
        default=None,
        description="Existing session UUID. Omit to create a new session.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    message: Annotated[str, StringConstraints(min_length=1, max_length=4000)] = Field(
        ...,
        description="User message text.",
        examples=["How do I reset my password?"],
    )
    context_override: bool = Field(
        default=False,
        description="If true, skip RAG retrieval and use only LLM knowledge.",
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "message": "How do I reset my password?",
                    "context_override": False,
                },
                {
                    "message": "What are your business hours?",
                    "context_override": True,
                },
            ]
        }
    }


class SourceDocument(BaseModel):
    """A single retrieved document used as context for the answer.

    Attributes:
        id: Unique document identifier.
        content: Relevant text excerpt (truncated for response size).
        score: Similarity score from vector search (0.0-1.0).
        metadata: Original document metadata (source, page, etc.).
    """

    id: str = Field(..., description="Document UUID.", examples=["doc_abc123"])
    content: str = Field(
        ...,
        description="Retrieved text snippet.",
        examples=["To reset your password, visit..."],
    )
    score: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Vector similarity score.", examples=[0.87]
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value pairs from the source document.",
        examples=[{"source": "faq.md", "section": "account"}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "doc_abc123",
                    "content": "To reset your password, visit the account settings page and click 'Forgot Password'.",
                    "score": 0.87,
                    "metadata": {"source": "faq.md", "section": "account"},
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Response payload for a chat interaction.

    Attributes:
        session_id: UUID of the conversation session.
        answer: Generated assistant response.
        sources: List of retrieved documents used as context (empty if context_override).
        model: LLM model identifier used for generation.
        latency_ms: Total request processing time in milliseconds.
        timestamp: UTC timestamp of response generation.
    """

    session_id: str = Field(
        ...,
        description="Conversation session UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    answer: str = Field(
        ...,
        description="Assistant's generated response.",
        examples=["To reset your password..."],
    )
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="Retrieved context documents. Empty when context_override=true.",
    )
    model: str = Field(
        ..., description="LLM model identifier.", examples=["gemini-1.5-flash"]
    )
    latency_ms: Annotated[int, Field(ge=0)] = Field(
        ..., description="End-to-end latency in milliseconds.", examples=[245]
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of response generation.",
        examples=["2024-01-15T10:30:45.123Z"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "answer": "To reset your password, visit the account settings page and click 'Forgot Password'. You'll receive an email with a reset link.",
                    "sources": [
                        {
                            "id": "doc_abc123",
                            "content": "To reset your password, visit the account settings page and click 'Forgot Password'.",
                            "score": 0.87,
                            "metadata": {"source": "faq.md", "section": "account"},
                        }
                    ],
                    "model": "gemini-1.5-flash",
                    "latency_ms": 245,
                    "timestamp": "2024-01-15T10:30:45.123Z",
                }
            ]
        }
    }


class ChatFeedback(BaseModel):
    """User feedback on a chat response.

    Attributes:
        session_id: Session UUID the feedback applies to.
        message_id: Unique identifier for the specific message (future use).
        rating: Binary helpfulness rating (thumbs up/down).
        comment: Optional free-text feedback.
    """

    session_id: Annotated[
        str,
        StringConstraints(
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        ),
    ] = Field(
        ...,
        description="Conversation session UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    message_id: str = Field(
        ..., description="Message UUID (future use).", examples=["msg_xyz789"]
    )
    rating: Literal["helpful", "not_helpful"] = Field(
        ..., description="Binary helpfulness rating.", examples=["helpful"]
    )
    comment: Annotated[str, StringConstraints(max_length=1000)] | None = Field(
        default=None,
        description="Optional free-text feedback.",
        examples=["Answer was accurate but could be more concise."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "message_id": "msg_xyz789",
                    "rating": "helpful",
                    "comment": "Answer was accurate but could be more concise.",
                }
            ]
        }
    }
