"""Provenance block serialization (API_SPECIFICATION 4.3, ADR-10).

Every factual response carries provenance inline: per-claim confidence tier
and resolvable source references. Clients never fetch provenance separately
to render a tier badge (NFR-037 to NFR-039).
"""

from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel


class SourceRef(BaseModel):
    source_id: str
    label: str
    url: str | None


class ClaimProvenance(BaseModel):
    claim_id: str
    tier: str  # verified | self_reported | flagged
    predicate: str
    sources: list[SourceRef]


class ProvenanceBlock(BaseModel):
    claims: list[ClaimProvenance]


async def provenance_for_claims(
    conn: AsyncConnection[Any], claim_ids: list[str]
) -> dict[str, ClaimProvenance]:
    """Build provenance entries for the given claims, sources included."""
    if not claim_ids:
        return {}
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT c.id AS claim_id, c.confidence_tier, c.predicate,
                   s.id AS source_id, s.title AS source_title, s.url AS source_url
            FROM claim c
            LEFT JOIN claim_source cs
                   ON cs.claim_id = c.id AND cs.deleted_at IS NULL
            LEFT JOIN source s
                   ON s.id = cs.source_id AND s.deleted_at IS NULL
            WHERE c.id = ANY(%s) AND c.deleted_at IS NULL
            ORDER BY c.id, s.id
            """,
            (claim_ids,),
        )
        rows = await cur.fetchall()

    out: dict[str, ClaimProvenance] = {}
    for row in rows:
        claim_id = str(row["claim_id"])
        entry = out.get(claim_id)
        if entry is None:
            entry = ClaimProvenance(
                claim_id=claim_id,
                tier=row["confidence_tier"],
                predicate=row["predicate"],
                sources=[],
            )
            out[claim_id] = entry
        if row["source_id"] is not None:
            entry.sources.append(
                SourceRef(
                    source_id=str(row["source_id"]),
                    label=row["source_title"],
                    url=row["source_url"],
                )
            )
    return out


async def provenance_for_entity(
    conn: AsyncConnection[Any], entity_type: str, entity_id: str, allowed_tiers: list[str]
) -> ProvenanceBlock:
    """The provenance block for an entity: all claims about it within the
    caller's ceiling (claims are tiered rows themselves)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id FROM claim
            WHERE subject_type = %s AND subject_id = %s AND deleted_at IS NULL
              AND privacy_tier = ANY(%s)
            ORDER BY id
            """,
            (entity_type, entity_id, allowed_tiers),
        )
        ids = [str(row["id"]) for row in await cur.fetchall()]
    by_id = await provenance_for_claims(conn, ids)
    return ProvenanceBlock(claims=[by_id[i] for i in ids if i in by_id])
