import re
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.exceptions import DocumentException


class DocumentMetadata(BaseModel):
    """Metadata for a loaded document."""

    source_filename: str = Field(description="Original filename")
    file_extension: str = Field(description="File extension")
    character_count: int = Field(description="Number of characters in content")
    load_timestamp: datetime = Field(description="When document was loaded")
    file_size_bytes: int = Field(description="File size in bytes")


class Document(BaseModel):
    """Structured document representation."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique document ID"
    )
    filename: str = Field(description="Document filename")
    file_type: str = Field(description="File type/extension")
    content: str = Field(description="Cleaned document content")
    metadata: DocumentMetadata = Field(description="Document metadata")


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""

    source_file: str = Field(description="Source filename")
    chunk_number: int = Field(description="Chunk index (0-based)")
    character_count: int = Field(description="Number of characters in chunk")
    start_char_index: int = Field(description="Character index in original document")
    end_char_index: int = Field(description="End character index in original document")


class Chunk(BaseModel):
    """Text chunk representation."""

    chunk_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique chunk ID"
    )
    document_id: str = Field(description="Source document ID")
    text: str = Field(description="Chunk text content")
    chunk_index: int = Field(description="Chunk index (0-based)")
    metadata: ChunkMetadata = Field(description="Chunk metadata")


class DocumentLoader:
    """Production-ready document loader for PDF, TXT, and MD files."""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

    def __init__(self) -> None:
        """Initialize document loader."""

    def supported_extensions(self) -> set[str]:
        """Get set of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def _detect_file_type(self, file_path: Path) -> str:
        """Detect file type from extension."""
        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise DocumentException(
                message=f"Unsupported file type: {ext}",
                details={
                    "supported_extensions": list(self.SUPPORTED_EXTENSIONS),
                    "provided_extension": ext,
                    "file_path": str(file_path),
                },
            )
        return ext

    def _load_pdf(self, file_path: Path) -> str:
        """Load PDF file content."""
        try:
            import PyPDF2

            text_parts = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted)
            return "\n".join(text_parts)
        except Exception as e:
            import PyPDF2

            if isinstance(e, PyPDF2.errors.PdfReadError) or "EOF marker" in str(e):
                raise DocumentException(
                    message="Corrupted PDF file",
                    details={"file_path": str(file_path), "error": str(e)},
                )
            if isinstance(e, DocumentException):
                raise
            raise DocumentException(
                message=f"Failed to load PDF file: {e!s}",
                details={"file_path": str(file_path)},
            )

    def _load_text_file(self, file_path: Path, encoding: str = "utf-8") -> str:
        """Load text file content with specified encoding."""
        encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise DocumentException(
            message="Failed to decode file with any supported encoding",
            details={"file_path": str(file_path), "attempted_encodings": encodings},
        )

    def clean_text(self, text: str) -> str:
        """Clean extracted text.

        Removes:
        - Repeated whitespace
        Preserves paragraphs
        """
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split into lines
        lines = text.split("\n")

        # Clean each line
        cleaned_lines = []
        for line in lines:
            # Remove extra whitespace within the line, preserve empty lines
            line = re.sub(r"[ \t]+", " ", line).strip()
            cleaned_lines.append(line)

        # Join lines with single newline
        cleaned_text = "\n".join(cleaned_lines)

        # Consecutive blank lines become exactly two newlines (paragraph boundary)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text.strip()

    def load_document(self, file_path: str | Path) -> Document:
        """Load a single document from file path."""
        try:
            path = Path(file_path)

            if not path.exists():
                raise DocumentException(
                    message="File does not exist", details={"file_path": str(path)}
                )

            if not path.is_file():
                raise DocumentException(
                    message="Path is not a file", details={"file_path": str(path)}
                )

            file_type = self._detect_file_type(path)
            file_size = path.stat().st_size

            # Load content based on file type
            if file_type == ".pdf":
                content = self._load_pdf(path)
            else:  # .txt or .md
                content = self._load_text_file(path)

            # Clean the content
            cleaned_content = self.clean_text(content)

            # Create metadata
            metadata = DocumentMetadata(
                source_filename=path.name,
                file_extension=file_type,
                character_count=len(cleaned_content),
                load_timestamp=datetime.now(),
                file_size_bytes=file_size,
            )

            return Document(
                filename=path.name,
                file_type=file_type,
                content=cleaned_content,
                metadata=metadata,
            )

        except DocumentException:
            raise
        except Exception as e:
            raise DocumentException(
                message=f"Failed to load document: {e!s}",
                details={"file_path": str(file_path)},
            )

    def load_directory(self, directory_path: str | Path) -> list[Document]:
        """Load all supported documents from a directory."""
        try:
            path = Path(directory_path)

            if not path.exists():
                raise DocumentException(
                    message="Directory does not exist",
                    details={"directory_path": str(path)},
                )

            if not path.is_dir():
                raise DocumentException(
                    message="Path is not a directory",
                    details={"directory_path": str(path)},
                )

            documents = []
            for file_path in path.iterdir():
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
                ):
                    try:
                        document = self.load_document(file_path)
                        documents.append(document)
                    except DocumentException:
                        # Skip files that fail to load but continue with others
                        continue

            return documents

        except DocumentException:
            raise
        except Exception as e:
            raise DocumentException(
                message=f"Failed to load directory: {e!s}",
                details={"directory_path": str(directory_path)},
            )
