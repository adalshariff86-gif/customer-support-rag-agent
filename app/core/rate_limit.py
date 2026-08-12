"""
Simple in-memory sliding-window rate limiter middleware.

Tracks requests per client IP with a configurable window and limit.
Only applies to resource-consuming paths (chat, documents).

Design:
  - No external dependencies (Redis, etc.).
  - Thread-safe via threading.Lock.
  - Automatically evicts expired entries to prevent memory growth.
  - Never logs the client IP.
"""

import threading
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

# Paths subject to rate limiting.
_LIMITED_PATHS: frozenset[str] = frozenset({"/chat", "/chat/new", "/documents/ingest"})

# Defaults (can be overridden via Settings later).
_DEFAULT_WINDOW_SECONDS = 60
_DEFAULT_MAX_REQUESTS = 30


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter per client IP."""

    def __init__(
        self,
        app,
        window_seconds: int = _DEFAULT_WINDOW_SECONDS,
        max_requests: int = _DEFAULT_MAX_REQUESTS,
    ):
        super().__init__(app)
        self._window = window_seconds
        self._max = max_requests
        # {ip: [timestamp, ...]}
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            hits = self._hits[ip]
            # Prune expired entries.
            self._hits[ip] = [t for t in hits if t > cutoff]
            if len(self._hits[ip]) >= self._max:
                return True
            self._hits[ip].append(now)
            return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        # Only rate-limit expensive endpoints.
        if not any(path == p or path.startswith(p + "/") for p in _LIMITED_PATHS):
            return await call_next(request)

        # Skip rate limiting when auth is disabled (dev mode).
        if not settings.API_KEY:
            return await call_next(request)

        ip = self._client_ip(request)
        if self._is_rate_limited(ip):
            return JSONResponse(
                status_code=429,
                content={
                    "type": "errors/RATE_LIMITED",
                    "title": "Too Many Requests",
                    "status": 429,
                    "detail": f"Rate limit exceeded. Max {_DEFAULT_MAX_REQUESTS} requests per {_DEFAULT_WINDOW_SECONDS}s.",
                },
                headers={"Retry-After": str(_DEFAULT_WINDOW_SECONDS)},
            )

        return await call_next(request)
