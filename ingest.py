from app.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider
from app.services.document_loader import DocumentLoader
from app.services.ingestion_service import IngestionService
from app.services.text_chunker import TextChunker
from app.vectorstore.chroma_store import ChromaVectorStore


def main():
    service = IngestionService(
        document_loader=DocumentLoader(),
        text_chunker=TextChunker(),
        embedding_provider=SentenceTransformerEmbeddingProvider(),
        vector_store=ChromaVectorStore(),
    )
    result = service.ingest()
    print(result.message)


if __name__ == "__main__":
    main()
