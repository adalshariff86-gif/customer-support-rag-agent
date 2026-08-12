"""
Error Response Models – Pydantic schemas for standardized error payloads.

All error responses follow RFC 7807 Problem Details format.
Used by global exception handlers in main.py.
"""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """RFC 7807 Problem Details error response.

    Attributes:
        type: URI-reference identifying the problem type.
        title: Short, human-readable summary of the problem type.
        status: HTTP status code.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI-reference identifying the specific occurrence (request path).
        errors: Optional structured validation errors or additional context.
    """

    type: str = Field(
        ..., description="Problem type URI.", examples=["errors/validation_error"]
    )
    title: str = Field(
        ..., description="Short problem summary.", examples=["Validation Error"]
    )
    status: int = Field(
        ..., ge=100, le=599, description="HTTP status code.", examples=[422]
    )
    detail: str = Field(
        ...,
        description="Human-readable error detail.",
        examples=["Request validation failed."],
    )
    instance: str | None = Field(
        default=None,
        description="Request path where error occurred.",
        examples=["/api/v1/chat"],
    )
    errors: dict[str, list[str]] | None = Field(
        default=None,
        description="Structured validation errors or additional context.",
        examples=[
            {"field_errors": ["message: ensure this value has at least 1 characters"]}
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "errors/validation_error",
                    "title": "Validation Error",
                    "status": 422,
                    "detail": "Request validation failed.",
                    "instance": "/api/v1/chat",
                    "errors": {
                        "field_errors": [
                            "message: ensure this value has at least 1 characters"
                        ]
                    },
                },
                {
                    "type": "errors/llm_error",
                    "title": "Llm Error",
                    "status": 502,
                    "detail": "Language model service failed.",
                    "instance": "/api/v1/chat",
                    "errors": {"upstream": ["Gemini API timeout after 30s"]},
                },
                {
                    "type": "errors/internal_error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "An unexpected internal error occurred.",
                    "instance": "/api/v1/chat",
                    "errors": None,
                },
            ]
        }
    }


class ValidationErrorDetail(BaseModel):
    """Structured validation error for a single field."""

    field: str = Field(
        ..., description="Field name that failed validation.", examples=["message"]
    )
    message: str = Field(
        ...,
        description="Validation error message.",
        examples=["ensure this value has at least 1 characters"],
    )
    value: str | None = Field(
        default=None, description="Invalid value that was provided.", examples=[""]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "field": "message",
                    "message": "ensure this value has at least 1 characters",
                    "value": "",
                },
                {
                    "field": "session_id",
                    "message": "invalid UUID format",
                    "value": "not-a-uuid",
                },
            ]
        }
    }


class ValidationErrorResponse(ErrorResponse):
    """Extended error response for validation failures (HTTP 422).

    Includes structured field-level errors for client-side display.
    """

    errors: dict[str, list[ValidationErrorDetail]] = Field(
        ...,
        description="Field-level validation errors.",
        examples=[
            {
                "field_errors": [
                    {
                        "field": "message",
                        "message": "ensure this value has at least 1 characters",
                        "value": "",
                    }
                ]
            }
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "errors/validation_error",
                    "title": "Validation Error",
                    "status": 422,
                    "detail": "Request validation failed.",
                    "instance": "/api/v1/chat",
                    "errors": {
                        "field_errors": [
                            {
                                "field": "message",
                                "message": "ensure this value has at least 1 characters",
                                "value": "",
                            },
                            {
                                "field": "session_id",
                                "message": "invalid UUID format",
                                "value": "not-a-uuid",
                            },
                        ]
                    },
                }
            ]
        }
    }
