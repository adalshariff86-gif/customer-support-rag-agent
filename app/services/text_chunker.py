import re
from dataclasses import dataclass

from app.services.document_loader import Chunk, ChunkMetadata


@dataclass
class ChunkerConfig:
    """Configuration for text chunking."""

    chunk_size: int = 1000
    chunk_overlap: int = 100
    minimum_chunk_size: int = 50

    def validate(self) -> None:
        """Validate chunker configuration."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if self.minimum_chunk_size <= 0:
            raise ValueError("minimum_chunk_size must be positive")
        if self.minimum_chunk_size > self.chunk_size:
            raise ValueError("minimum_chunk_size cannot exceed chunk_size")


class TextChunker:
    """Production-quality text chunker with recursive splitting."""

    # Splitting separators in order of preference
    SPLIT_SEPARATORS = [
        ("\n\n", "paragraph"),  # Paragraph break
        ("\n", "newline"),  # Line break
        (r"(?<=[.!?])\s+", "sentence"),  # Sentence boundary
        (" ", "space"),  # Word boundary
    ]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        minimum_chunk_size: int = 50,
    ) -> None:
        """Initialize text chunker.

        Args:
            chunk_size: Target size for chunks (in characters)
            chunk_overlap: Overlap between consecutive chunks (in characters)
            minimum_chunk_size: Minimum acceptable chunk size
        """
        self.config = ChunkerConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            minimum_chunk_size=minimum_chunk_size,
        )
        self.config.validate()

    def _split_by_separator(
        self, text: str, start_offset: int, separator_pattern: str
    ) -> list[tuple[str, int]]:
        """Split text by a separator pattern, tracking offsets."""
        parts = []
        if separator_pattern == r"(?<=[.!?])\s+":
            start = 0
            for match in re.finditer(separator_pattern, text):
                parts.append((text[start : match.start()], start_offset + start))
                start = match.end()
            parts.append((text[start:], start_offset + start))
        else:
            start = 0
            for part in text.split(separator_pattern):
                parts.append((part, start_offset + start))
                start += len(part) + len(separator_pattern)

        return [(p, offset) for p, offset in parts if p.strip()]

    def _recursive_split(
        self, text: str, start_offset: int = 0, separator_index: int = 0
    ) -> list[tuple[str, int]]:
        """Recursively split text using separators in order of preference."""
        if len(text) <= self.config.chunk_size:
            return [(text, start_offset)] if text.strip() else []

        # Try current separator
        separator_pattern, separator_type = self.SPLIT_SEPARATORS[separator_index]

        # Split the text
        parts = self._split_by_separator(text, start_offset, separator_pattern)

        # If splitting didn't work or created too small parts, try next separator
        if len(parts) <= 1 and separator_index < len(self.SPLIT_SEPARATORS) - 1:
            return self._recursive_split(text, start_offset, separator_index + 1)

        result = []
        last_separator = separator_index >= len(self.SPLIT_SEPARATORS) - 1

        for part_text, part_offset in parts:
            if len(part_text) > self.config.chunk_size:
                if last_separator:
                    result.extend(self._character_split(part_text, part_offset))
                else:
                    result.extend(
                        self._recursive_split(
                            part_text, part_offset, separator_index + 1
                        )
                    )
            else:
                result.append((part_text, part_offset))

        return result

    def _character_split(
        self, text: str, start_offset: int = 0
    ) -> list[tuple[str, int]]:
        """Fallback: split text by character count, tracking offsets."""
        chunks = []
        start = 0

        while start < len(text):
            # Calculate end position
            end = start + self.config.chunk_size

            # Try to find a good break point near the end
            if end < len(text):
                # Look for sentence endings near the boundary
                sentence_end = text.rfind(
                    ".", start + self.config.minimum_chunk_size, end
                )
                if (
                    sentence_end != -1
                    and sentence_end > start + self.config.minimum_chunk_size
                ):
                    end = sentence_end + 1
                else:
                    # Look for paragraph breaks
                    paragraph_end = text.rfind(
                        "\n\n", start + self.config.minimum_chunk_size, end
                    )
                    if (
                        paragraph_end != -1
                        and paragraph_end > start + self.config.minimum_chunk_size
                    ):
                        end = paragraph_end + 2
                    else:
                        # Look for line breaks
                        line_end = text.rfind(
                            "\n", start + self.config.minimum_chunk_size, end
                        )
                        if (
                            line_end != -1
                            and line_end > start + self.config.minimum_chunk_size
                        ):
                            end = line_end + 1
                        else:
                            # Look for word boundaries
                            word_end = text.rfind(
                                " ", start + self.config.minimum_chunk_size, end
                            )
                            if (
                                word_end != -1
                                and word_end > start + self.config.minimum_chunk_size
                            ):
                                end = word_end + 1

            chunk = text[start:end]
            if chunk.strip() and len(chunk.strip()) >= self.config.minimum_chunk_size:
                chunks.append((chunk, start_offset + start))

            # Move start position with overlap
            start = end - self.config.chunk_overlap

        return chunks

    def chunk_document(
        self, document_id: str, content: str, source_file: str
    ) -> list[Chunk]:
        """Split document content into chunks with metadata.

        Args:
            document_id: Unique ID of the source document
            content: Cleaned document text content
            source_file: Source filename

        Returns:
            List of Chunk objects
        """
        if not content or not content.strip():
            return []

        # Recursively split the content
        text_chunks = self._recursive_split(content, 0)

        # Create chunk objects
        chunks = []

        for idx, (chunk_text, start_pos) in enumerate(text_chunks):
            # Calculate strip offset adjustment
            lstrip_len = len(chunk_text) - len(chunk_text.lstrip())
            actual_start = start_pos + lstrip_len
            stripped_text = chunk_text.strip()

            if not stripped_text:
                continue

            end_pos = actual_start + len(stripped_text)

            # Create metadata
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_number=idx,
                character_count=len(stripped_text),
                start_char_index=actual_start,
                end_char_index=end_pos,
            )

            chunk = Chunk(
                document_id=document_id,
                text=stripped_text,
                chunk_index=idx,
                metadata=metadata,
            )

            chunks.append(chunk)

        return chunks

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks (simplified interface).

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        return [chunk[0].strip() for chunk in self._recursive_split(text, 0)]
