"""
Health Models – Pydantic schemas for health check responses.

Defines structured health check responses for monitoring and orchestration.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DependencyStatus(str, Enum):
    """Health status of an external dependency."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    NOT_INITIALIZED = "not_initialized"
    UNKNOWN = "unknown"


class DependencyHealth(BaseModel):
    """Health status of a single external dependency.

    Attributes:
        name: Dependency identifier (e.g., "chromadb", "gemini_api").
        status: Current health state.
        latency_ms: Optional round-trip latency in milliseconds.
        details: Optional additional context (version, error message, etc.).
        checked_at: UTC timestamp of the health check.
    """

    name: str = Field(..., description="Dependency identifier.", examples=["chromadb", "gemini_api"])
    status: DependencyStatus = Field(..., description="Current health state.", examples=["healthy"])
    latency_ms: Optional[float] = Field(
        default=None, description="Round-trip latency in milliseconds.", examples=[12.5]
    )
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Additional context (version, error, etc.).", examples=[{"version": "0.4.22"}]
    )
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the check.",
        examples=["2024-01-15T10:30:45.123Z"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "chromadb", "status": "healthy", "latency_ms": 12.5, "details": {"version": "0.4.22"}},
                {"name": "gemini_api", "status": "degraded", "latency_ms": 1250.0, "details": {"error": "high_latency"}},
                {"name": "embedding_model", "status": "not_initialized", "details": {"reason": "not_loaded"}},
            ]
        }
    }


class HealthCheckResponse(BaseModel):
    """Full health check response for deep monitoring.

    Attributes:
        status: Overall application health (healthy if all deps healthy).
        timestamp: UTC timestamp of the check.
        environment: Deployment environment.
        version: Application version.
        dependencies: Per-dependency health details.
    """

    status: DependencyStatus = Field(..., description="Overall health status.", examples=["healthy"])
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the check.",
        examples=["2024-01-15T10:30:45.123Z"],
    )
    environment: str = Field(..., description="Deployment environment.", examples=["development", "production"])
    version: str = Field(..., description="Application version.", examples=["1.0.0"])
    dependencies: list[DependencyHealth] = Field(
        default_factory=list, description="Per-dependency health details."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2024-01-15T10:30:45.123Z",
                    "environment": "development",
                    "version": "1.0.0",
                    "dependencies": [
                        {"name": "chromadb", "status": "healthy", "latency_ms": 12.5, "details": {"version": "0.4.22"}},
                        {"name": "gemini_api", "status": "healthy", "latency_ms": 45.2, "details": {"model": "gemini-1.5-flash"}},
                    ],
                },
                {
                    "status": "degraded",
                    "timestamp": "2024-01-15T10:30:45.123Z",
                    "environment": "production",
                    "version": "1.0.0",
                    "dependencies": [
                        {"name": "chromadb", "status": "healthy", "latency_ms": 8.1},
                        {"name": "gemini_api", "status": "degraded", "latency_ms": 2100.0, "details": {"error": "high_latency"}},
                    ],
                },
            ]
        }
    }


class LivenessResponse(BaseModel):
    """Kubernetes liveness probe response.

    Lightweight endpoint that only confirms the process is running.
    Does NOT check external dependencies.

    Attributes:
        status: Always "alive" if the process responds.
        timestamp: UTC timestamp.
    """

    status: str = Field(default="alive", description="Liveness status.", examples=["alive"])
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp.",
        examples=["2024-01-15T10:30:45.123Z"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": "alive", "timestamp": "2024-01-15T10:30:45.123Z"}]
        }
    }


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe response.

    Checks if the application can serve traffic (dependencies healthy).

    Attributes:
        status: "ready" if all critical dependencies are healthy.
        timestamp: UTC timestamp.
        checks: Optional list of critical dependency checks.
    """

    status: DependencyStatus = Field(..., description="Readiness status.", examples=["ready"])
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp.",
        examples=["2024-01-15T10:30:45.123Z"],
    )
    checks: Optional[list[DependencyHealth]] = Field(
        default=None, description="Critical dependency checks.", examples=[[]]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "ready", "timestamp": "2024-01-15T10:30:45.123Z", "checks": []},
                {
                    "status": "not_ready",
                    "timestamp": "2024-01-15T10:30:45.123Z",
                    "checks": [
                        {"name": "chromadb", "status": "unhealthy", "details": {"error": "connection_refused"}}
                    ],
                },
            ]
        }
    }