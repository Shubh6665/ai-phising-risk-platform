"""Markdown document chunker preserving structural hierarchy and metadata."""

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Default sizing parameters calibrated for all-MiniLM-L6-v2 (256-token maximum context window).
# English text averages ~4 characters per token. 750 characters is ~180 tokens.
DEFAULT_CHUNK_SIZE_CHARS = 750
DEFAULT_CHUNK_OVERLAP_CHARS = 120


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a discrete semantic chunk of a knowledge base document."""

    id: str
    content: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarkdownChunker:
    """Splits Markdown documents by section headings and paragraphs with sliding overlap."""

    def __init__(
        self,
        max_chunk_chars: int = DEFAULT_CHUNK_SIZE_CHARS,
        chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
    ):
        if max_chunk_chars <= chunk_overlap_chars:
            raise ValueError("max_chunk_chars must be strictly greater than chunk_overlap_chars")
        if chunk_overlap_chars < 0:
            raise ValueError("chunk_overlap_chars cannot be negative")

        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def chunk_document(self, file_path: str | Path, content: str | None = None) -> list[DocumentChunk]:
        """Split a Markdown document into structured, attributed chunks."""
        path = Path(file_path)
        if content is None:
            content = path.read_text(encoding="utf-8")

        if not content.strip():
            return []

        doc_name = path.name
        doc_metadata = self._extract_document_metadata(path, content)

        # Split document into heading-delimited sections
        sections = self._parse_sections(content)
        chunks: list[DocumentChunk] = []
        global_chunk_idx = 0

        for section in sections:
            section_heading = section["heading"]
            section_content = section["text"].strip()
            if not section_content:
                continue

            # If section content fits within the chunk budget, keep it whole
            if len(section_content) <= self.max_chunk_chars:
                chunk_id = self._compute_chunk_id(doc_name, global_chunk_idx, section_content)
                meta = {
                    **doc_metadata,
                    "heading": section_heading,
                    "chunk_index": global_chunk_idx,
                }
                chunks.append(DocumentChunk(id=chunk_id, content=section_content, metadata=meta))
                global_chunk_idx += 1
            else:
                # Split large section by paragraphs or sentences with overlap
                sub_chunks = self._split_text_with_overlap(section_content)
                for sub_text in sub_chunks:
                    sub_text = sub_text.strip()
                    if not sub_text:
                        continue
                    chunk_id = self._compute_chunk_id(doc_name, global_chunk_idx, sub_text)
                    meta = {
                        **doc_metadata,
                        "heading": section_heading,
                        "chunk_index": global_chunk_idx,
                    }
                    chunks.append(DocumentChunk(id=chunk_id, content=sub_text, metadata=meta))
                    global_chunk_idx += 1

        return chunks

    def _parse_sections(self, content: str) -> list[dict[str, str]]:
        """Split markdown text into sections based on H1/H2/H3 headings."""
        lines = content.splitlines()
        sections: list[dict[str, str]] = []
        current_heading = "Preamble"
        current_lines: list[str] = []

        for line in lines:
            if re.match(r"^#{1,3}\s+", line):
                if current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.append({"heading": current_heading, "text": text})
                    current_lines = []
                current_heading = line.lstrip("#").strip()
            current_lines.append(line)

        if current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                sections.append({"heading": current_heading, "text": text})

        return sections

    def _split_text_with_overlap(self, text: str) -> list[str]:
        """Split text larger than max_chunk_chars using paragraphs and overlap."""
        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds the limit
            if len(current_chunk) + len(para) + 2 > self.max_chunk_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Form overlap from end of current chunk
                    overlap = current_chunk[-self.chunk_overlap_chars :] if self.chunk_overlap_chars > 0 else ""
                    current_chunk = overlap + "\n\n" + para if overlap else para
                else:
                    # Paragraph itself is longer than max_chunk_chars, hard-split it
                    sub_splits = self._hard_split_string(para)
                    for split in sub_splits[:-1]:
                        chunks.append(split.strip())
                    current_chunk = sub_splits[-1]
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _hard_split_string(self, text: str) -> list[str]:
        """Sliding window character split for oversized continuous blocks."""
        splits: list[str] = []
        start = 0
        text_len = len(text)
        step = self.max_chunk_chars - self.chunk_overlap_chars

        while start < text_len:
            end = min(start + self.max_chunk_chars, text_len)
            splits.append(text[start:end])
            if end >= text_len:
                break
            start += step

        return splits

    def _extract_document_metadata(self, path: Path, content: str) -> dict[str, Any]:
        """Derive standard metadata attributes from document path and header comments."""
        doc_name = path.name

        # Detect genuinely mock material from explicit header declaration or mock filename
        has_mock_header = bool(
            re.search(r">\s*(?:\*{2})?Document Type(?:\*{2})?:\s*Mock", content, re.IGNORECASE)
            or re.search(
                r">\s*(?:\[!(?:IMPORTANT|WARNING|NOTE)\])?\s*\n?>\s*(?:\*{2})?MOCK\s+(?:DOCUMENT|POLICY|PLAYBOOK|INCIDENT|GUIDANCE)",
                content,
                re.IGNORECASE,
            )
        )
        has_mock_filename = doc_name.lower().startswith("mock_") or "_mock." in doc_name.lower()
        is_mock = has_mock_header or has_mock_filename

        # Extract title from first H1
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else doc_name

        # Extract source attribution if present
        source_match = re.search(r">\s*\*\*Sources?\*\*:\s*(.+)$", content, re.MULTILINE)
        if source_match:
            source_attribution = source_match.group(1).strip()
        elif is_mock:
            source_attribution = "Fictional Project Policy / Internal Standard"
        else:
            source_attribution = "Authoritative Security Standard"

        document_type = "mock" if is_mock else "authoritative"

        return {
            "source_path": str(path),
            "document_name": doc_name,
            "document_title": title,
            "document_type": document_type,
            "is_mock": is_mock,
            "source_attribution": source_attribution,
        }

    def _compute_chunk_id(self, doc_name: str, index: int, content: str) -> str:
        """Create a stable, deterministic chunk identifier."""
        content_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:12]
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", doc_name.replace(".md", ""))
        return f"{clean_name}_{index:03d}_{content_hash}"

