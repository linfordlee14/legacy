"""Owner document batch import (MVP-014): local files through the pipeline.

A thin walker over the existing ingestion pipeline (MVP-010): originals are
stored content-addressed BEFORE any parsing, extraction failures become
owner-visible review flags (never silent), duplicates dedup by checksum,
and every created row carries ingestion provenance and the P2 default tier.

Idempotent and re-runnable: re-importing the same files creates no second
Artifact row (checksum dedup); every run is still recorded as its own
IngestionJob plus an audit entry, so the import history is inspectable.
The batch runs as the system principal, like the MVP-013 claim seed; the
storage directory must be the one the API service uses, so refs resolve.

Exit status: 0 when every item stored or deduped; 1 when items need review
(the per-item detail is in the printed summary and the job record); 2 on
configuration errors.
"""

import argparse
import asyncio
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from legacy_api.audit import SYSTEM_USER_ID, write_audit_event
from legacy_api.ingestion import process_job, validate_tier
from legacy_api.routes.ingestion import MAX_FILE_BYTES
from legacy_api.storage import LocalObjectStorage, ObjectStorage

# VCS internals and build output are never owner documents.
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    ".next", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}


def _excluded(relative: Path) -> bool:
    return any(part in SKIP_DIRS or part.startswith(".") for part in relative.parts)


def collect_files(
    paths: list[Path], extensions: set[str] | None
) -> tuple[list[tuple[Path, str]], list[dict[str, str]], int]:
    """Walk the given files and directories.

    Returns (files as (path, display name), skipped entries, excluded count).
    Empty and over-ceiling files are reported as skipped, never dropped
    silently; hidden files, VCS and build directories, and extension-filter
    misses are excluded with only a count (they are not owner content).
    """
    candidates: list[tuple[Path, str]] = []
    excluded = 0
    for path in paths:
        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if path.is_file():
            candidates.append((path, path.name))
            continue
        for child in sorted(path.rglob("*")):
            if not child.is_file():
                continue
            relative = child.relative_to(path)
            if _excluded(relative):
                excluded += 1
                continue
            candidates.append((child, str(Path(path.name) / relative)))

    files: list[tuple[Path, str]] = []
    skipped: list[dict[str, str]] = []
    for path, name in candidates:
        if extensions is not None and path.suffix.lower() not in extensions:
            excluded += 1
            continue
        size = path.stat().st_size
        if size == 0:
            skipped.append({"name": name, "reason": "empty"})
        elif size > MAX_FILE_BYTES:
            skipped.append({"name": name, "reason": "exceeds_size_ceiling"})
        else:
            files.append((path, name))
    files.sort(key=lambda entry: entry[1])
    return files, skipped, excluded


async def import_documents(
    pool: AsyncConnectionPool,
    storage: ObjectStorage,
    paths: list[Path],
    *,
    tier: str | None = None,
    extensions: set[str] | None = None,
) -> dict[str, Any]:
    """Run one batch through the ingestion pipeline; returns the run summary."""
    tier_value = validate_tier(tier)
    files, skipped, excluded = collect_files(paths, extensions)
    if not files:
        raise ValueError("no importable files found under the given paths")

    items: list[dict[str, Any]] = []
    for path, name in files:
        data = path.read_bytes()
        key = storage.put(data)  # preserve the original before anything else
        items.append(
            {
                "index": len(items),
                "type": "file",
                "name": name,
                "mime": mimetypes.guess_type(name)[0] or "application/octet-stream",
                "storage_ref": key,
                "privacy_tier": tier_value,
                "status": "pending",
            }
        )

    descriptor = {
        "kind": "owner_document_batch",
        "roots": [str(path) for path in paths],
        "items": items,
        "skipped": skipped,
    }
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO ingestion_job
                    (job_type, source_descriptor, status, progress_percent,
                     created_by, origin_type)
                VALUES ('bulk_import', %s, 'queued', 0, %s, 'system')
                RETURNING id
                """,
                (Jsonb(descriptor), SYSTEM_USER_ID),
            )
            row = await cur.fetchone()
            assert row is not None
            job_id = str(row["id"])
        await write_audit_event(
            conn,
            actor_type="system",
            actor_id=None,
            action="seed_import",
            subject_type="IngestionJob",
            subject_id=job_id,
            payload={
                "seed": "owner_document_batch",
                "item_count": len(items),
                "skipped_count": len(skipped),
                "excluded_count": excluded,
            },
        )

    # The existing pipeline: extraction, checksum dedup, review flags,
    # per-item statuses, completion audit (MVP-010).
    await process_job(pool, storage, job_id)

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT status, source_descriptor FROM ingestion_job WHERE id = %s",
                (job_id,),
            )
            final = await cur.fetchone()
            assert final is not None

    final_items: list[dict[str, Any]] = final["source_descriptor"].get("items", [])
    by_status: dict[str, int] = {}
    for item in final_items:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
    return {
        "job_id": job_id,
        "status": final["status"],
        "item_count": len(final_items),
        "by_status": by_status,
        "needs_review": [
            item["name"] for item in final_items if item["status"] in ("review", "failed")
        ],
        "skipped": skipped,
        "excluded_count": excluded,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m legacy_api.seed.documents",
        description="Batch-import owner documents through the ingestion pipeline (MVP-014).",
    )
    parser.add_argument("paths", nargs="+", help="files or directories to import")
    parser.add_argument(
        "--tier", default=None, help="privacy tier for every item (P0-P3; default P2)"
    )
    parser.add_argument(
        "--ext",
        action="append",
        default=None,
        metavar="EXTS",
        help="only import these extensions (comma-separated, e.g. .md,.txt,.pdf)",
    )
    return parser


def _parse_extensions(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    extensions = set()
    for value in values:
        for raw in value.split(","):
            ext = raw.strip().lower()
            if not ext:
                continue
            extensions.add(ext if ext.startswith(".") else f".{ext}")
    return extensions or None


async def _amain(argv: list[str] | None = None) -> int:
    from legacy_api.config import get_settings
    from legacy_api.db import create_pool

    args = build_parser().parse_args(argv)
    settings = get_settings()
    if not settings.database_url:
        print("LEGACY_DATABASE_URL is required (DEP-18)", file=sys.stderr)
        return 2

    pool = create_pool(settings.database_url)
    await pool.open()
    storage = LocalObjectStorage(Path(settings.storage_dir))
    try:
        summary = await import_documents(
            pool,
            storage,
            # Resolved so display names carry the real directory name even
            # when the batch is invoked with relative paths like "." or "..".
            [Path(raw).resolve() for raw in args.paths],
            tier=args.tier,
            extensions=_parse_extensions(args.ext),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        await pool.close()
    print(json.dumps(summary, indent=2))
    # Review items are loud: nonzero exit until the owner has looked.
    return 1 if summary["needs_review"] else 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()
