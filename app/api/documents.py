"""
Documents API Router – HTTP layer for document ingestion management.

Endpoints:
  POST /documents/ingest  – Trigger document ingestion into the knowledge base.
  GET  /documents/status   – Return ingestion collection status.

Design principles:
  - Thin API layer: validates HTTP requests, calls IngestionService, returns responses.
  - No business logic, no chunking, no embeddings.
  - All domain exceptions are mapped to HTTP responses by the global handler in main.py.
"""

import asyncio
import time

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_ingestion_service
from app.core.logger import get_logger
from app.services.ingestion_service import IngestionService

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# -- Response Models --
class IngestionResponse(BaseModel):
    """Response payload for document ingestion trigger.

    Attributes:
        documents_loaded: Number of documents loaded from disk.
        chunks_created:   Number of text chunks created.
        vectors_stored:   Number of vectors written to the store.
        collection_name:  Target collection name.
        elapsed_ms:       Wall-clock time for the pipeline (ms).
        already_indexed:  True when ingestion was skipped.
        message:          Human-readable summary.
    """

    documents_loaded: int = Field(
        default=0,
        description="Number of documents loaded from disk.",
        examples=[10],
    )
    chunks_created: int = Field(
        default=0,
        description="Number of text chunks created.",
        examples=[47],
    )
    vectors_stored: int = Field(
        default=0,
        description="Number of vectors written to the store.",
        examples=[47],
    )
    collection_name: str = Field(
        default="documents",
        description="Target collection name.",
        examples=["documents"],
    )
    elapsed_ms: float = Field(
        default=0.0,
        description="Wall-clock time for the pipeline in milliseconds.",
        examples=[3421.5],
    )
    already_indexed: bool = Field(
        default=False,
        description="True when ingestion was skipped because collection is populated.",
        examples=[False],
    )
    message: str = Field(
        default="",
        description="Human-readable summary of the ingestion run.",
        examples=["Ingestion complete | documents=10 chunks=47 vectors=47"],
    )


class IngestionStatusResponse(BaseModel):
    """Response payload for ingestion status query.

    Attributes:
        collection_name:   Target collection name.
        collection_exists: Whether the collection exists in the vector store.
        document_count:    Number of documents currently stored.
    """

    collection_name: str = Field(
        default="documents",
        description="Target collection name.",
        examples=["documents"],
    )
    collection_exists: bool = Field(
        default=False,
        description="Whether the collection exists.",
        examples=[True],
    )
    document_count: int = Field(
        default=0,
        description="Number of documents currently in the collection.",
        examples=[47],
    )


# -- POST /documents/ingest --
@router.post(
    "/ingest",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger document ingestion",
    description=(
        "Run the document ingestion pipeline: load files from the data "
        "directory, chunk them, generate embeddings, and store in ChromaDB. "
        "Idempotent: if the collection is already populated, ingestion is "
        "skipped unless ``force=true``."
    ),
    responses={
        200: {
            "description": "Ingestion completed or collection already populated.",
        },
        500: {"description": "Internal server error."},
    },
)
async def ingest_documents(
    force: bool = Query(
        default=False,
        description="Force re-ingestion even if collection is populated.",
    ),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> IngestionResponse:
    """Trigger the document ingestion pipeline.

    Runs the CPU-heavy ingestion in a thread executor to avoid blocking
    the async event loop.
    """
    start_time = time.perf_counter()

    logger.info(
        "Ingestion requested | force=%s",
        force,
    )

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: ingestion_service.ingest(force=force),
    )

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "Ingestion endpoint completed | status=200 elapsed_ms=%.1f",
        elapsed_ms,
    )

    return IngestionResponse(
        documents_loaded=result.documents_loaded,
        chunks_created=result.chunks_created,
        vectors_stored=result.vectors_stored,
        collection_name=result.collection_name,
        elapsed_ms=result.elapsed_ms,
        already_indexed=result.already_indexed,
        message=result.message,
    )


# -- GET /documents/status --
@router.get(
    "/status",
    response_model=IngestionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ingestion status",
    description=(
        "Return the current status of the document ingestion collection: "
        "whether it exists and how many documents it contains."
    ),
    responses={
        200: {
            "description": "Current ingestion status.",
        },
        500: {"description": "Internal server error."},
    },
)
async def get_ingestion_status(
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> IngestionStatusResponse:
    """Return the current ingestion collection status."""
    start_time = time.perf_counter()

    loop = asyncio.get_running_loop()
    status_data = await loop.run_in_executor(
        None,
        ingestion_service.get_status,
    )

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "Status endpoint completed | status=200 elapsed_ms=%.1f",
        elapsed_ms,
    )

    return IngestionStatusResponse(
        collection_name=status_data["collection_name"],
        collection_exists=status_data["collection_exists"],
        document_count=status_data["document_count"],
    )
