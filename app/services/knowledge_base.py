import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.core.exceptions import DocumentException
from app.services.document_loader import DocumentLoader, Document, Chunk
from app.services.text_chunker import TextChunker


@dataclass
class KnowledgeBaseStatistics:
    """Statistics for knowledge base operations."""
    
    documents_loaded: int = 0
    chunks_created: int = 0
    average_chunk_size: float = 0.0
    last_update_timestamp: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "documents_loaded": self.documents_loaded,
            "chunks_created": self.chunks_created,
            "average_chunk_size": round(self.average_chunk_size, 2),
            "last_update_timestamp": self.last_update_timestamp.isoformat() 
                if self.last_update_timestamp else None
        }


class KnowledgeBaseService:
    """Knowledge base service for document ingestion and chunking."""
    
    def __init__(
        self,
        document_loader: Optional[DocumentLoader] = None,
        text_chunker: Optional[TextChunker] = None,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize knowledge base service.
        
        Args:
            document_loader: DocumentLoader instance (injected)
            text_chunker: TextChunker instance (injected)
            logger: Logger instance (injected)
        """
        self.document_loader = document_loader or DocumentLoader()
        self.text_chunker = text_chunker or TextChunker()
        self.logger = logger or logging.getLogger(__name__)
        
        self._documents: List[Document] = []
        self._chunks: List[Chunk] = []
        self._statistics = KnowledgeBaseStatistics()
    
    def load_knowledge_base(self, directory_path: str | Path) -> List[Chunk]:
        """Load documents from directory and split into chunks.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of processed chunks
            
        Raises:
            DocumentException: If loading fails
        """
        try:
            # Load documents
            documents = self.document_loader.load_directory(directory_path)
            
            # Clear previous state
            self._documents = documents
            self._chunks = []
            
            # Process each document
            all_chunks = []
            for document in documents:
                chunks = self.text_chunker.chunk_document(
                    document_id=document.id,
                    content=document.content,
                    source_file=document.filename
                )
                all_chunks.extend(chunks)
            
            # Update statistics
            self._chunks = all_chunks
            self._update_statistics()
            
            self.logger.info(
                f"Loaded {len(documents)} documents, created {len(all_chunks)} chunks"
            )
            
            return all_chunks
            
        except Exception as e:
            self.logger.error(f"Failed to load knowledge base: {str(e)}")
            if isinstance(e, DocumentException):
                raise
            raise DocumentException(
                message=f"Failed to load knowledge base: {str(e)}",
                details={"directory_path": str(directory_path)}
            )
    
    def reload(self, directory_path: str | Path) -> List[Chunk]:
        """Reload knowledge base from directory.
        
        Equivalent to clear() followed by load_knowledge_base().
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of processed chunks
        """
        self.clear()
        return self.load_knowledge_base(directory_path)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all loaded documents with metadata.
        
        Returns:
            List of document summaries
        """
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "character_count": doc.metadata.character_count,
                "file_size_bytes": doc.metadata.file_size_bytes,
                "load_timestamp": doc.metadata.load_timestamp.isoformat()
            }
            for doc in self._documents
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics.
        
        Returns:
            Statistics dictionary
        """
        return self._statistics.to_dict()
    
    def clear(self) -> None:
        """Clear all loaded documents and chunks."""
        self._documents = []
        self._chunks = []
        self._statistics = KnowledgeBaseStatistics()
        self.logger.info("Knowledge base cleared")
    
    def _update_statistics(self) -> None:
        """Update statistics based on current state."""
        total_chars = sum(len(chunk.text) for chunk in self._chunks)
        
        self._statistics.documents_loaded = len(self._documents)
        self._statistics.chunks_created = len(self._chunks)
        self._statistics.average_chunk_size = (
            total_chars / len(self._chunks) if self._chunks else 0.0
        )
        self._statistics.last_update_timestamp = datetime.now()
    
    @property
    def documents(self) -> List[Document]:
        """Get loaded documents."""
        return self._documents.copy()
    
    @property
    def chunks(self) -> List[Chunk]:
        """Get processed chunks."""
        return self._chunks.copy()
