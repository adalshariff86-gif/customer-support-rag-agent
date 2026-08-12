"""
API Key Authentication Middleware.

Validates the ``X-API-Key`` header on protected routes.
Health and root endpoints are exempt.

Design:
  - If ``settings.API_KEY`` is empty, auth is disabled (dev mode).
  - Never logs the API key value.
  - Constant-time comparison to prevent timing attacks.
"""

import hmac

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

# Paths that are always public (no auth required).
_PUBLIC_PATHS: frozenset[str] = frozenset({"/", "/health", "/chat/health"})


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that checks ``X-API-Key`` on protected paths."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Auth disabled when no key is configured.
        if not settings.API_KEY:
            return await call_next(request)

        # Exempt public paths and OpenAPI docs.
        path = request.url.path
        if path in _PUBLIC_PATHS or path.startswith(("/docs", "/openapi")):
            return await call_next(request)

        provided = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(provided, settings.API_KEY):
            return JSONResponse(
                status_code=401,
                content={
                    "type": "errors/UNAUTHORIZED",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Missing or invalid API key. Provide a valid X-API-Key header.",
                },
            )

        return await call_next(request)
