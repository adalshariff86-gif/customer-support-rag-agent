"""
FastAPI Application Factory – Entry point for the Customer Support RAG Agent.

Configures:
  - CORS middleware
  - Global exception handlers (AppException → RFC 7807 JSON)
  - Request ID middleware for traceability
  - Startup / Shutdown lifecycle events
  - Root and Health endpoints
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat_router, documents_router
from app.core.auth import APIKeyAuthMiddleware
from app.core.config import settings
from app.core.dependencies import get_request_id
from app.core.exceptions import AppException, StartupException
from app.core.logger import get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.lifecycle import ApplicationLifecycle

logger = get_logger(__name__)

# ── Module-level lifecycle instance (one per process) ──
_lifecycle = ApplicationLifecycle()


# ── Lifespan (Startup / Shutdown) ─────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:  Initialise dependencies, validate config, verify providers.
    Shutdown: Release resources gracefully.
    """
    # ── Startup ───────────────────────────────────
    try:
        await _lifecycle.startup()
    except StartupException as exc:
        logger.critical(
            "Startup failed: %s",
            exc.message,
            extra={"details": exc.details},
        )
        raise
    except Exception as exc:
        logger.critical(
            "Startup failed with unexpected error: %s",
            str(exc),
            exc_info=True,
        )
        raise StartupException(
            message=f"Startup failed: {exc}",
            details={"error": str(exc)},
        ) from exc

    yield  # Application runs between startup and shutdown

    # ── Shutdown ──────────────────────────────────
    await _lifecycle.shutdown()


# ── Application Instance ──────────────────────────
app = FastAPI(
    title="Customer Support RAG Agent",
    description="AI customer support assistant powered by RAG with Google Gemini.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────
_cors_origins = [
    o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APIKeyAuthMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── API Routers ──────────────────────────────────
app.include_router(chat_router)
app.include_router(documents_router)


# ── Request ID Middleware ─────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a unique request ID to every incoming HTTP request."""
    rid = await get_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# ── Global Exception Handlers ────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Catch all domain exceptions and return RFC 7807 Problem Details JSON."""
    logger.error(
        "AppException: %s (code=%s, status=%d)",
        exc.message,
        exc.error_code,
        exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions. Returns generic 500."""
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "type": "errors/internal_error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected internal error occurred.",
        },
    )


# ── Root Endpoint ─────────────────────────────────
@app.get("/", tags=["General"])
async def root():
    """Root welcome endpoint."""
    return {
        "service": "customer-support-rag",
        "version": settings.APP_VERSION,
        "status": "online",
    }


# ── Health Check Endpoint ─────────────────────────
@app.get("/health", tags=["General"])
async def health_check():
    """
    Deep health check.

    Verifies:
      - Application startup status
      - Vector database connectivity
      - Embedding provider status
      - LLM provider configuration
      - Uptime and timestamp

    Never exposes API keys or secrets.
    """
    logger.info("Health check requested")
    return _lifecycle.health_check()
