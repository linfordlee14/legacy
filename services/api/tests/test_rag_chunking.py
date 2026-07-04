"""Chunking unit tests (MVP-016; RAG-04, RAG-05, RAG-24).

Pure functions, no database: heading-aware packing, sentence-boundary
splitting, overlap, tunable configuration, and deterministic hashing.
"""

from legacy_api.rag.chunking import Chunk, ChunkingConfig, chunk_document

DOC = """# Projects

## WildGuard AI

WildGuard AI is a multi-agent wildlife conservation system. It watches
camera feeds. It raises alerts for rangers.

## CyberBuddy

CyberBuddy coaches cybersecurity habits. It gamifies daily practice.

### Stack

Kotlin and Jetpack Compose on Android. Gemini for coaching content.
"""


def test_heading_paths_are_preserved() -> None:
    # Small targets force one chunk per section so each carries its path.
    chunks = chunk_document(DOC, ChunkingConfig(target_tokens=25, max_tokens=60))
    assert len(chunks) > 1, "sections must land in separate chunks at this size"
    paths = {chunk.heading_path for chunk in chunks}
    assert any(path and "WildGuard AI" in path for path in paths)
    # Heading path is the full stack, joined for citation locators (RAG-24).
    assert "Projects > CyberBuddy > Stack" in chunks_by_text(chunks, "Kotlin")


def chunks_by_text(chunks: list[Chunk], needle: str) -> list[str | None]:
    return [chunk.heading_path for chunk in chunks if needle in chunk.text]


def test_chunks_respect_max_size_and_sentence_boundaries() -> None:
    config = ChunkingConfig(target_tokens=40, max_tokens=60, overlap_ratio=0.1)
    one_paragraph = " ".join(
        f"Sentence number {i} carries a modest amount of text." for i in range(40)
    )
    chunks = chunk_document(one_paragraph, config)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.token_count <= config.max_tokens
        # Never split mid-sentence: every piece of a split paragraph ends
        # at a sentence boundary.
        assert chunk.text.rstrip().endswith(".")


def test_consecutive_chunks_overlap() -> None:
    config = ChunkingConfig(target_tokens=50, max_tokens=80, overlap_ratio=0.15)
    text = "\n\n".join(
        f"Paragraph {i} says something distinct and specific. It has two sentences."
        for i in range(12)
    )
    chunks = chunk_document(text, config)
    assert len(chunks) > 1
    overlaps = 0
    for previous, current in zip(chunks, chunks[1:], strict=False):
        last_sentence = previous.text.rstrip().rsplit(". ", 1)[-1]
        if last_sentence and last_sentence in current.text:
            overlaps += 1
    assert overlaps > 0  # 10-15% trailing overlap (RAG-04)


def test_configuration_is_tunable_not_constant() -> None:
    text = "\n\n".join(f"Paragraph {i} with a sentence of reasonable size." for i in range(30))
    small = chunk_document(text, ChunkingConfig(target_tokens=30, max_tokens=50))
    large = chunk_document(text, ChunkingConfig(target_tokens=600, max_tokens=800))
    assert len(small) > len(large)


def test_chunking_is_deterministic() -> None:
    first = chunk_document(DOC)
    second = chunk_document(DOC)
    assert [c.content_hash for c in first] == [c.content_hash for c in second]
    assert [c.index for c in first] == list(range(len(first)))


def test_code_fences_stay_intact() -> None:
    text = "Intro paragraph.\n\n```python\n\ndef f():\n    return 1\n\n```\n\nOutro."
    chunks = chunk_document(text)
    fenced = [c for c in chunks if "def f()" in c.text]
    assert fenced and "```python" in fenced[0].text
