"""Ingestion pipeline for documents and notes (MVP-010; FS-001 slice;
FR-ING-001, FR-ING-007, FR-ING-008).

Originals are stored unmodified and content-addressed before any parsing;
extraction failures become owner-visible review flags, never data loss.
Every created row carries ingestion provenance (origin_type, origin_ref)
and the P2 default tier unless set at capture time.
"""

import hashlib
import json
import logging
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from legacy_api.audit import write_audit_event
from legacy_api.obs.tracing import span
from legacy_api.storage import ObjectStorage

logger = logging.getLogger("legacy_api.ingestion")

TIERS = {"P0", "P1", "P2", "P3"}

TEXT_EXTENSIONS = {".txt", ".text", ".log"}
MARKDOWN_EXTENSIONS = {".md", ".markdown"}


def extract_text(name: str, mime: str, data: bytes) -> tuple[str | None, str]:
    """Return (canonical_markdown, extraction_status) for a document.

    Formats beyond the MVP slice (images, audio, video: FR-ING-002 to
    FR-ING-004) are stored with status not_applicable until their pipelines
    ship; broken inputs return failed and become review flags.
    """
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    try:
        if suffix in MARKDOWN_EXTENSIONS or mime == "text/markdown":
            return data.decode("utf-8"), "extracted"
        if suffix in TEXT_EXTENSIONS or mime.startswith("text/"):
            return data.decode("utf-8"), "extracted"
        if suffix == ".pdf" or mime == "application/pdf":
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if not text:
                return None, "partial"
            return text, "extracted"
        return None, "not_applicable"
    except Exception:
        return None, "failed"


def checksum_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def process_job(
    pool: AsyncConnectionPool,
    storage: ObjectStorage,
    job_id: str,
    router: Any = None,
    metrics: Any = None,
) -> None:
    """Run one processing pass over a job's pending items (also the retry
    pass: review and failed items are reprocessed, FR-ING-007). With a
    Model Router present, stored rows are chunk-indexed on the same pass
    (RAG-01 handoff; RAG-08 freshness); without one they stay queued for
    `make reindex`, and the gap is logged, never silent."""
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT id, source_descriptor, created_by FROM ingestion_job "
                "WHERE id = %s AND deleted_at IS NULL",
                (job_id,),
            )
            job = await cur.fetchone()
        if job is None:
            logger.warning("ingestion job missing", extra={"job_id": job_id})
            return

        descriptor = job["source_descriptor"]
        items: list[dict[str, Any]] = descriptor.get("items", [])
        creator = str(job["created_by"])
        created = {"Artifact": 0, "Note": 0, "duplicates": 0}
        review = 0

        with span("ingestion.process", item_count=len(items)):
            for item in items:
                if item.get("status") in ("stored", "duplicate"):
                    continue
                try:
                    if item["type"] == "note":
                        await _process_note(conn, item, creator, job_id)
                        created["Note"] += 1
                    else:
                        outcome = await _process_file(conn, storage, item, creator, job_id)
                        if outcome == "duplicate":
                            created["duplicates"] += 1
                        elif outcome == "review":
                            review += 1
                        else:
                            created["Artifact"] += 1
                except Exception:
                    logger.exception("ingestion item failed", extra={"job_id": job_id})
                    item["status"] = "failed"
                    item["reason"] = "unexpected_error"
                    review += 1

        status = "review" if review else "complete"
        await conn.execute(
            """
            UPDATE ingestion_job
            SET status = %s, progress_percent = 100,
                items_created = %s, source_descriptor = %s,
                error_detail = %s
            WHERE id = %s
            """,
            (
                status,
                Jsonb(created),
                Jsonb(descriptor),
                Jsonb({"review_items": review}) if review else None,
                job_id,
            ),
        )
        await write_audit_event(
            conn,
            actor_type="system",
            actor_id=creator,
            action="update",
            subject_type="IngestionJob",
            subject_id=job_id,
            payload={"status": status, "review_count": review},
        )

        # RAG write path: chunk-index what this pass stored (MVP-016).
        from legacy_api.rag.indexer import index_entity_or_queue

        stored = [
            ("Note", item["note_id"]) if item["type"] == "note"
            else ("Artifact", item["artifact_id"])
            for item in items
            if item.get("status") == "stored"
            and (item.get("note_id") or item.get("artifact_id"))
        ]
        if router is None:
            if stored:
                logger.info(
                    "chunk indexing deferred to reindex (no model router)",
                    extra={"job_id": job_id, "entity_count": len(stored)},
                )
                if metrics is not None:
                    metrics.record_embedding_deferred()
        else:
            with span("rag.index", entity_count=len(stored)):
                for entity_type, entity_id in stored:
                    await index_entity_or_queue(
                        conn, router, entity_type, str(entity_id), metrics=metrics
                    )


async def _process_note(
    conn: Any, item: dict[str, Any], creator: str, job_id: str
) -> None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO note (title, body, note_context, privacy_tier,
                              created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, %s, %s, %s, %s, 'ingestion', 'IngestionJob', %s)
            RETURNING id
            """,
            (
                item.get("title"),
                item["body"],
                item.get("note_context"),
                item.get("privacy_tier", "P2"),
                creator,
                job_id,
            ),
        )
        row = await cur.fetchone()
    item["status"] = "stored"
    item["note_id"] = str(row["id"])
    # The body has landed as content; the lingering job row keeps IDs only.
    item.pop("body", None)
    item.pop("title", None)


async def _process_file(
    conn: Any, storage: ObjectStorage, item: dict[str, Any], creator: str, job_id: str
) -> str:
    data = storage.get(item["storage_ref"])
    checksum = checksum_of(data)

    if item.get("artifact_id"):
        # Retry pass: the artifact exists; re-extract into it (FR-ING-007).
        text, extraction_status = extract_text(item["name"], item.get("mime", ""), data)
        await conn.execute(
            "UPDATE artifact SET canonical_markdown = %s, extraction_status = %s "
            "WHERE id = %s",
            (text, extraction_status, item["artifact_id"]),
        )
        if extraction_status == "failed":
            item["status"] = "review"
            item["reason"] = "extraction_failed"
            return "review"
        item["status"] = "stored"
        return "stored"

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id FROM artifact WHERE checksum = %s AND deleted_at IS NULL",
            (checksum,),
        )
        existing = await cur.fetchone()
    if existing:
        # Dedup by content hash: keep the reference, create no second row.
        item["status"] = "duplicate"
        item["duplicate_of"] = str(existing["id"])
        return "duplicate"

    text, extraction_status = extract_text(item["name"], item.get("mime", ""), data)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO artifact
                (title, artifact_type, storage_ref, mime_type, byte_size, checksum,
                 canonical_markdown, extraction_status, privacy_tier,
                 created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, 'document', %s, %s, %s, %s, %s, %s, %s,
                    %s, 'ingestion', 'IngestionJob', %s)
            RETURNING id
            """,
            (
                item["name"],
                item["storage_ref"],
                item.get("mime", "application/octet-stream"),
                len(data),
                checksum,
                text,
                extraction_status,
                item.get("privacy_tier", "P2"),
                creator,
                job_id,
            ),
        )
        row = await cur.fetchone()
    item["artifact_id"] = str(row["id"])
    if extraction_status == "failed":
        # Review flag: the original is preserved; a human decides next steps.
        item["status"] = "review"
        item["reason"] = "extraction_failed"
        return "review"
    item["status"] = "stored"
    return "stored"


def serialize_job(row: dict[str, Any]) -> dict[str, Any]:
    descriptor = row.get("source_descriptor") or {}
    items = [
        {k: v for k, v in item.items() if k not in ("body", "title")}
        for item in descriptor.get("items", [])
    ]
    return {
        "id": str(row["id"]),
        "job_type": row["job_type"],
        "status": row["status"],
        "progress_percent": row["progress_percent"],
        "items": items,
        "items_created": row["items_created"],
        "error_detail": row["error_detail"],
        "created_at": row["created_at"].isoformat(),
    }


def validate_tier(tier: Any) -> str:
    if tier is None:
        return "P2"
    if not isinstance(tier, str) or tier not in TIERS:
        raise ValueError(f"invalid privacy tier: {tier!r}")
    return tier


def job_fingerprint(payload: dict[str, Any], file_hashes: list[str]) -> bytes:
    return json.dumps(
        {"payload": payload, "files": file_hashes}, sort_keys=True
    ).encode()
