"""Executable script to index the security knowledge base into persistent ChromaDB."""

import sys
from pathlib import Path

# Add project root to path if running directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings
from src.rag.chunker import MarkdownChunker
from src.rag.embeddings import SentenceTransformerEmbedder
from src.rag.indexer import index_knowledge_base


def run_indexing() -> bool:
    kb_dir = PROJECT_ROOT / "data/knowledge_base"
    persist_dir = PROJECT_ROOT / settings.CHROMA_PERSIST_DIR

    print("=== Knowledge Base Indexing Pipeline ===")
    print(f"Source Directory: {kb_dir}")
    print(f"Persistence Directory: {persist_dir}")
    print(f"Collection Name: {settings.CHROMA_COLLECTION_NAME}")
    print(f"Embedding Model: {settings.RAG_EMBEDDING_MODEL}")

    if not kb_dir.is_dir():
        print(f"ERROR: Knowledge base directory not found at: {kb_dir}")
        return False

    required_files = [
        "phishing_indicators.md",
        "attack_patterns.md",
        "security_policies.md",
        "incident_response.md",
    ]
    for rf in required_files:
        if not (kb_dir / rf).is_file():
            print(f"ERROR: Missing required document: {rf}")
            return False

    try:
        print("\n[1/3] Loading embedding model...")
        embedder = SentenceTransformerEmbedder(settings.RAG_EMBEDDING_MODEL)
        print(f"  -> Model initialized. Embedding dimension: {embedder.dimension}, Max sequence length: {embedder.max_seq_length}")

        print("\n[2/3] Chunking documents and generating vector embeddings...")
        chunker = MarkdownChunker()
        stats = index_knowledge_base(
            kb_dir=kb_dir,
            persist_dir=persist_dir,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedder=embedder,
            chunker=chunker,
        )

        print("\n[3/3] Indexing completed successfully!")
        print(f"  -> Processed Documents: {stats['document_count']}")
        print(f"  -> Generated Chunks: {stats['chunk_count']}")
        print(f"  -> Collection Total Records: {stats['total_collection_count']}")
        print(f"  -> Collection: {stats['collection_name']}")
        print(f"  -> Storage: {stats['persist_dir']}")
        return True

    except Exception as exc:
        print(f"ERROR: Indexing failed: {type(exc).__name__}: {exc}")
        return False


if __name__ == "__main__":
    success = run_indexing()
    sys.exit(0 if success else 1)

