"""Knowledge base indexing pipeline into persistent ChromaDB storage."""

from pathlib import Path
from typing import Any
import chromadb
from chromadb.api.models.Collection import Collection

from src.config import settings
from src.rag.chunker import DocumentChunk, MarkdownChunker
from src.rag.embeddings import Embedder, SentenceTransformerEmbedder


def get_chroma_client(persist_dir: str | Path | None = None) -> chromadb.PersistentClient:
    """Initialize or connect to a local persistent ChromaDB client."""
    path = str(persist_dir or settings.CHROMA_PERSIST_DIR)
    return chromadb.PersistentClient(path=path)


def get_or_create_collection(
    persist_dir: str | Path | None = None,
    collection_name: str | None = None,
) -> Collection:
    """Retrieve or create a persistent ChromaDB collection."""
    client = get_chroma_client(persist_dir)
    name = collection_name or settings.CHROMA_COLLECTION_NAME
    # Use cosine distance for normalized sentence transformer vectors
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def index_knowledge_base(
    kb_dir: str | Path = "data/knowledge_base",
    persist_dir: str | Path | None = None,
    collection_name: str | None = None,
    embedder: Embedder | None = None,
    chunker: MarkdownChunker | None = None,
) -> dict[str, Any]:
    """Process, chunk, embed, and upsert knowledge base documents into ChromaDB.

    Idempotent: Re-indexing existing files updates records under stable IDs
    without duplicating chunks.
    """
    kb_path = Path(kb_dir)
    if not kb_path.is_dir():
        raise FileNotFoundError(f"Knowledge base directory does not exist: {kb_path}")

    md_files = sorted(list(kb_path.glob("*.md")))
    if not md_files:
        raise ValueError(f"No Markdown (.md) documents found in: {kb_path}")

    if chunker is None:
        chunker = MarkdownChunker()

    if embedder is None:
        embedder = SentenceTransformerEmbedder(settings.RAG_EMBEDDING_MODEL)

    collection = get_or_create_collection(persist_dir, collection_name)

    # Prune existing chunks for these documents to remove stale chunks from previous revisions
    for file_path in md_files:
        try:
            collection.delete(where={"document_name": file_path.name})
        except Exception:
            pass

    all_chunks: list[DocumentChunk] = []
    for file_path in md_files:
        chunks = chunker.chunk_document(file_path)
        all_chunks.extend(chunks)

    if not all_chunks:
        return {
            "document_count": len(md_files),
            "chunk_count": 0,
            "collection_name": collection.name,
            "persist_dir": str(persist_dir or settings.CHROMA_PERSIST_DIR),
            "total_collection_count": collection.count(),
        }

    ids = [chunk.id for chunk in all_chunks]
    documents = [chunk.content for chunk in all_chunks]
    metadatas = [chunk.metadata for chunk in all_chunks]

    # Generate embeddings
    embeddings = embedder.encode(documents)

    # Upsert chunks into ChromaDB (idempotent: updates existing, adds new)
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return {
        "document_count": len(md_files),
        "chunk_count": len(all_chunks),
        "collection_name": collection.name,
        "persist_dir": str(persist_dir or settings.CHROMA_PERSIST_DIR),
        "total_collection_count": collection.count(),
    }

