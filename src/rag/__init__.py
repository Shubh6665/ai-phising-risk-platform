"""Retrieval-Augmented Generation (RAG) package."""

from src.rag.chunker import DocumentChunk, MarkdownChunker
from src.rag.embeddings import DummyEmbedder, Embedder, SentenceTransformerEmbedder
from src.rag.indexer import get_or_create_collection, index_knowledge_base
from src.rag.retriever import search_knowledge_base

__all__ = [
    "DocumentChunk",
    "MarkdownChunker",
    "Embedder",
    "SentenceTransformerEmbedder",
    "DummyEmbedder",
    "get_or_create_collection",
    "index_knowledge_base",
    "search_knowledge_base",
]

