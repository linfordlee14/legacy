"""Structure-aware chunking (RAG-04): heading- and paragraph-aware for
documents, never splitting mid-sentence, preserving the heading path for
citation locators (RAG-24). Sizes are tunable configuration, not code
constants.

Token counts are a documented estimate (roughly four characters per
token): the exact tokenizer belongs to the embedding provider, and the
targets in RAG-04 are ranges, not contracts.
"""

import hashlib
import re
from dataclasses import dataclass

from legacy_api.ai.router import estimate_tokens

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# Sentence boundary: terminal punctuation followed by whitespace. Naive but
# only used to split paragraphs that alone exceed the maximum size.
SENTENCES = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ChunkingConfig:
    """Documents row of the RAG-04 table: 400-800 tokens, 10-15% overlap."""

    target_tokens: int = 600
    max_tokens: int = 800
    overlap_ratio: float = 0.12


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    token_count: int
    heading_path: str | None

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()


def _sentences(paragraph: str) -> list[str]:
    return [part for part in SENTENCES.split(paragraph) if part.strip()]


def _units(text: str) -> list[tuple[str | None, str]]:
    """(heading_path, unit) pairs: paragraphs annotated with the heading
    stack above them. Fenced code blocks stay intact as single units."""
    units: list[tuple[str | None, str]] = []
    stack: list[tuple[int, str]] = []
    paragraph: list[str] = []
    in_fence = False

    def flush() -> None:
        if paragraph:
            path = " > ".join(title for _, title in stack) or None
            units.append((path, "\n".join(paragraph).strip()))
            paragraph.clear()

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            paragraph.append(line)
            continue
        if in_fence:
            paragraph.append(line)
            continue
        match = HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, match.group(2).strip()))
            continue
        if not line.strip():
            flush()
            continue
        paragraph.append(line)
    flush()
    return units


def chunk_document(text: str, config: ChunkingConfig | None = None) -> list[Chunk]:
    """Heading- and paragraph-aware packing. Paragraphs are the atomic
    unit; a paragraph larger than the maximum is split on sentence
    boundaries only (never mid-sentence, RAG-04). Consecutive chunks
    overlap by trailing sentences up to the configured ratio."""
    config = config or ChunkingConfig()
    pieces: list[tuple[str | None, str]] = []
    for path, unit in _units(text):
        if estimate_tokens(unit) <= config.max_tokens:
            pieces.append((path, unit))
            continue
        sentences = _sentences(unit) or [unit]
        current: list[str] = []
        for sentence in sentences:
            candidate = " ".join([*current, sentence])
            if current and estimate_tokens(candidate) > config.max_tokens:
                pieces.append((path, " ".join(current)))
                current = [sentence]
            else:
                current.append(sentence)
        if current:
            pieces.append((path, " ".join(current)))

    chunks: list[Chunk] = []
    current_pieces: list[tuple[str | None, str]] = []

    def emit() -> None:
        if not current_pieces:
            return
        body = "\n\n".join(piece for _, piece in current_pieces)
        path = current_pieces[0][0]
        chunks.append(
            Chunk(
                index=len(chunks),
                text=body,
                token_count=estimate_tokens(body),
                heading_path=path,
            )
        )

    overlap_budget = int(config.target_tokens * config.overlap_ratio)
    for path, piece in pieces:
        current_size = sum(estimate_tokens(p) for _, p in current_pieces)
        if current_pieces and current_size + estimate_tokens(piece) > config.target_tokens:
            emit()
            # Overlap: carry the trailing sentences of the previous chunk
            # forward, within the overlap budget.
            tail = _sentences(current_pieces[-1][1])
            carried: list[str] = []
            for sentence in reversed(tail):
                candidate = " ".join([sentence, *carried])
                if estimate_tokens(candidate) > overlap_budget:
                    break
                carried.insert(0, sentence)
            current_pieces = (
                [(current_pieces[-1][0], " ".join(carried))] if carried else []
            )
        current_pieces.append((path, piece))
    emit()
    return chunks
