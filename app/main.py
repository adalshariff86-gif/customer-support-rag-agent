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
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logger import get_logger, request_id_ctx
from app.core.dependencies import get_request_id

logger = get_logger(__name__)


# ── Lifespan (Startup / Shutdown) ─────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:  Initialize connections and services.
    Shutdown: Release resources gracefully.
    """
    # ── Startup ───────────────────────────────────
    logger.info("Starting Customer Support RAG Agent...")
    logger.info("Environment: %s", settings.APP_ENV)
    logger.info("Debug mode:  %s", settings.APP_DEBUG)
    # Future tickets will initialize ChromaDB, EmbeddingService, etc. here.

    yield  # Application runs between startup and shutdown

    # ── Shutdown ──────────────────────────────────
    logger.info("Shutting down Customer Support RAG Agent...")
    # Future tickets will close DB connections, flush logs, etc. here.


# ── Application Instance ──────────────────────────
app = FastAPI(
    title="Customer Support RAG Agent",
    description="AI customer support assistant powered by RAG with Google Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "version": "1.0.0",
        "status": "online",
    }


# ── Health Check Endpoint ─────────────────────────
@app.get("/health", tags=["General"])
async def health_check():
    """
    Deep health check.
    Future tickets will ping ChromaDB and Gemini connectivity here.
    """
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.APP_ENV,
        "dependencies": {
            "chromadb": "not_initialized",
            "gemini_api": "not_initialized",
        },
    }
