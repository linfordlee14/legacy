# API_SPECIFICATION
### The REST API contract for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [AUTHENTICATION](../security/AUTHENTICATION.md), [AUTHORIZATION](../security/AUTHORIZATION.md) |

---

## 1. Purpose

This document defines the API contract for Legacy: conventions, resource groups, endpoint behavior, and response guarantees. Legacy is API-first: every capability of the platform, including everything the UI does, is reachable through this API, and the API is the durable interface for machine consumers (the PERS-06 persona in [USER_PERSONAS](../specs/USER_PERSONAS.md)), including future AI sessions.

This is a specification, not an executable definition. No OpenAPI document is generated here; one will be derived from this contract during implementation and kept in sync with it.

## 2. Goals

- Define a stable, versioned contract that outlives implementations.
- Guarantee provenance and privacy invariants at the contract level: every claim-bearing response carries tiers and citations; every response is filtered by the caller's access ceiling.
- Serve human clients (web UI) and machine consumers with the same endpoints.
- Keep the surface small and orthogonal: resources plus a small set of action endpoints.

## 3. Scope

**In scope:** the `/v1` REST surface: conventions, all resource groups, streaming behavior, error model, and deprecation policy.

**Out of scope:** transport security and token issuance (see [AUTHENTICATION](../security/AUTHENTICATION.md)), permission semantics (see [AUTHORIZATION](../security/AUTHORIZATION.md)), and internal service-to-service interfaces (see [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md)).

## 4. Requirements

### 4.1 Conventions

| Concern | Rule |
|---------|------|
| Base path | `/v1`; breaking changes require `/v2` plus a deprecation window |
| Format | JSON request and response bodies, UTF-8; media via signed URLs |
| Authentication | OAuth 2.0 / OIDC bearer tokens for interactive principals; scoped personal access tokens (PATs) for machine consumers |
| Authorization | Every request evaluated against role ceiling and item privacy tier before any data access; deny by default |
| IDs | Opaque, stable, never reused; identical to the entity IDs in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) |
| Pagination | Cursor-based: `cursor` and `limit` (default 25, max 100); responses include `next_cursor` or null |
| Filtering | Query parameters per resource (type, tier, tag, date range); documented per endpoint |
| Sorting | `sort` parameter with allowlisted fields; default is resource-appropriate (usually recency) |
| Idempotency | All mutating requests accept an `Idempotency-Key` header; retries with the same key return the original result |
| Rate limiting | Per-principal budgets; `429` with `Retry-After`; machine consumers get documented quotas |
| Timestamps | RFC 3339 UTC everywhere |
| Streaming | Server-Sent Events for AI endpoints; event types `token`, `citation`, `status`, `done`, `error` |
| Audit | Every mutation and every authorization denial writes an `AuditLogEntry` |

### 4.2 Response envelope and errors

Successful list responses: `{ "data": [...], "next_cursor": "..." }`. Single resources return the object directly. Errors use one envelope everywhere:

```json
{
  "error": {
    "code": "tier_forbidden",
    "message": "This item is above your access ceiling.",
    "request_id": "req_9f3a1c",
    "details": { "required_tier": "P1", "your_ceiling": "P0" }
  }
}
```

Canonical error codes: `unauthenticated`, `forbidden`, `tier_forbidden`, `not_found`, `validation_failed`, `conflict`, `rate_limited`, `idempotency_replay`, `provider_unavailable`, `internal`. `not_found` is returned for items that exist above the caller's ceiling: existence itself is not leaked (see the FR-PRIV group).

### 4.3 Provenance guarantee

Every response object that contains factual content includes a `provenance` block: confidence tier (`verified`, `self_reported`, `flagged`), claim IDs, and resolvable source references. This is a contract-level invariant (NFR-037 through NFR-039 in [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md)); clients never need to fetch provenance separately to render a tier badge.

### 4.4 Resource groups

#### Content entities

| Method and path | Purpose | Minimum role |
|-----------------|---------|--------------|
| `GET /v1/{collection}` | List projects, artifacts, notes, journals, events, ideas, talks, articles, skills, goals, lessons, books, people, organizations (one collection per canonical entity) | Per item tier |
| `POST /v1/{collection}` | Create an item (defaults to P2) | Owner |
| `GET /v1/{collection}/{id}` | Fetch one item with provenance | Per item tier |
| `PATCH /v1/{collection}/{id}` | Update; tier changes require the explicit `tier_change` sub-action with confirmation semantics | Owner |
| `DELETE /v1/{collection}/{id}` | Soft delete; permanent erasure only via the redaction workflow | Owner |
| `POST /v1/{collection}/{id}/restore` | Undo a soft delete while the row is retained (90-day window per [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.8) | Owner |
| `GET /v1/{collection}/{id}/revisions` | Revision history | Owner |

#### Ingestion

| Method and path | Purpose | Minimum role |
|-----------------|---------|--------------|
| `POST /v1/ingestion/jobs` | Create a job (upload references, connector source, or pasted content) | Owner |
| `GET /v1/ingestion/jobs` and `/{id}` | List and inspect jobs, per-item status | Owner |
| `POST /v1/ingestion/jobs/{id}/retry` | Retry failed items | Owner |

#### Search and answers

| Method and path | Purpose | Minimum role |
|-----------------|---------|--------------|
| `GET /v1/search` | Lexical, semantic, or hybrid search (`mode` parameter); results carry tiers | Any (ceiling-filtered) |
| `POST /v1/ask` | RAG question answering; SSE stream with inline `citation` events | Any (ceiling-filtered) |
| `POST /v1/twin/conversations` and `POST .../{id}/messages` | Twin chat; SSE; every response carries `disclosure` metadata identifying the AI | Any (mode-scoped) |

Example `/v1/ask` final payload (after streaming):

```json
{
  "answer": "CyberBuddy was presented at GDG Cape Town's Pet Projects 2026 on 30 June 2026.",
  "citations": [
    {
      "claim_id": "clm_18",
      "tier": "verified",
      "sources": [ { "source_id": "src_07", "label": "GDG Cape Town event page", "url": null } ]
    }
  ],
  "coverage": "full",
  "conversation_id": "cnv_3021"
}
```

> Note: `url` is null until source URLs are attached per MASTER_CONTEXT §12 item 1; the contract requires the field, not the value.

#### Knowledge graph and timeline

| Method and path | Purpose | Minimum role |
|-----------------|---------|--------------|
| `GET /v1/graph/nodes/{id}` | Node with provenance | Per tier |
| `GET /v1/graph/nodes/{id}/neighborhood` | Typed traversal, `depth` up to 3, tier-filtered before return | Per tier |
| `GET /v1/graph/edges` | Query edges by type, endpoint, validity window | Per tier |
| `POST /v1/graph/proposals/{id}/resolve` | Accept or reject an entity-merge or edge proposal | Owner |
| `GET /v1/timeline` | Range query with domain filters; undated items excluded, listed via `include=undated` | Per tier |

#### Memory, agents, verification

| Method and path | Purpose | Minimum role |
|-----------------|---------|--------------|
| `GET /v1/memory/records` | List memory records by type, importance, recency | Owner |
| `POST /v1/memory/records/{id}/redact` | Redaction workflow: tombstone plus re-embedding | Owner |
| `POST /v1/agents/tasks` | Create an orchestrated task | Owner |
| `GET /v1/agents/runs` and `/{id}` | Inspect runs: steps, tools, tokens, costs | Owner |
| `POST /v1/agents/runs/{id}/approvals/{step}` | Approve or reject a gated step | Owner |
| `GET /v1/verification/queue` | Open 🔴 and stale 🟡 claims | Owner |
| `POST /v1/verification/claims/{id}/evidence` | Owner attaches an evidence Source to a claim (supports or contradicts); audit-logged | Owner |
| `POST /v1/verification/claims/{id}/proposals` | Verification Agent files evidence and a tier-change proposal | Agent (Verification) |
| `POST /v1/verification/claims/{id}/resolve` | Owner applies or rejects a tier change; step-up required; audit-logged | Owner |

#### Publishing, vault, admin

| Method and path | Purpose | Minimum role |
|-----------------|---------|--------------|
| `POST /v1/portfolio/publications` | Publish an item to P0 through the review gate | Owner |
| `DELETE /v1/portfolio/publications/{id}` | Unpublish with cache purge | Owner |
| `POST /v1/vault/exports` | Trigger a Legacy Vault export; returns manifest reference | Owner, Steward (post-activation) |
| `GET /v1/vault/exports/{id}` | Export status and integrity manifest | Owner, Steward |
| `GET /v1/audit` | Query the audit log | Owner, Steward |
| `POST /v1/succession/activation` | Begin the multi-condition succession protocol (see [AUTHENTICATION](../security/AUTHENTICATION.md)); time-delayed, cancellable by the owner | Steward |
| `GET /v1/grants`, `POST /v1/grants`, `DELETE /v1/grants/{id}` | Manage P1 access grants (scoped, time-boxed) | Owner |
| `POST /v1/auth/tokens` | Create a personal access token; the secret is returned exactly once | Owner, step-up |
| `GET /v1/auth/tokens` | List token metadata (label, scopes, expiry, last use; never secrets) | Owner |
| `DELETE /v1/auth/tokens/{id}` | Revoke a token, effective immediately | Owner |

### 4.5 Machine consumer guarantees

For PERS-06 consumers (future AI sessions, integrations): IDs are permanent; fields are additive within `/v1`; removed or renamed fields require `/v2`; `provenance` blocks are always present on factual content; documented PAT scopes follow least privilege (`read:public`, `read:trusted`, `read:private`, `write:content`, `admin`); the deprecation window for any endpoint is at least 12 months with `Sunset` headers.

## 5. Acceptance Criteria

- Contract tests exist for every endpoint group, including tier-filtering tests proving `not_found` behavior for above-ceiling items and provenance-block presence on all factual responses.
- SSE endpoints stream first tokens within the NFR-003 target and always terminate with `done` or `error`.
- Idempotency replay, pagination, and rate-limit behavior verified by automated tests per [TESTING](../testing/TESTING.md).
- The derived OpenAPI document (implementation phase) is generated from or validated against this contract in CI.

## 6. Dependencies

- [AUTHENTICATION](../security/AUTHENTICATION.md) and [AUTHORIZATION](../security/AUTHORIZATION.md): token semantics, roles, ceilings, grants.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): entity shapes serialized by these endpoints.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md) and [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md): behavior behind `/v1/ask` and `/v1/twin`.
- [OBSERVABILITY](../deployment/OBSERVABILITY.md): request tracing and audit sink.

## 7. Risks

- Contract drift between this document and implementation; mitigated by the CI validation requirement above and the spec-first rule.
- Existence leaks through timing or error-shape differences for above-ceiling items; mitigated by uniform `not_found` responses and tests.
- SSE compatibility issues with some proxies; mitigated by a long-poll fallback documented at implementation time.
- Overly generous PAT scopes eroding least privilege; mitigated by scope review in the quarterly access review ([AUTHORIZATION](../security/AUTHORIZATION.md)).

## 8. Future Enhancements

- Webhook subscriptions for ingestion and verification events.
- A read-only public API subset for researchers (see [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)).
- Batch mutation endpoints if ingestion-scale editing emerges as a need.
- GraphQL read layer, only if client query diversity demonstrably outgrows REST (decision gate, not a plan).

## 9. Examples

A trusted collaborator (P1 grant, PAT scope `read:trusted`) calls `GET /v1/projects?tag=conservation`. The response contains the ✅ verified conservation projects plus 🟡 items each carrying `provenance.tier: "self_reported"`; a P2 draft project is absent entirely. The collaborator then calls `POST /v1/ask` with "What is RhinoShield's architecture?" and receives a streamed answer noting the architecture is still to be confirmed, citing the claim's source records, because the corpus marks that detail as unconfirmed (MASTER_CONTEXT §6).

## 10. Open Questions

- Should `/v1/ask` support multi-turn context natively, or always via `conversation_id`? Current design: always via conversation resources, for auditability.
- Do vault exports need resumable downloads at expected sizes? Resolve with real corpus size data (see the capacity TODO in [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md)).

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §0 (tier vocabulary serialized in `provenance`), §12 (source URL attachment queue).
- RFC 3339 (timestamps), RFC 9457 (error shape inspiration), Server-Sent Events (WHATWG HTML standard).

## 12. Related Specifications

- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)
- [AUTHENTICATION](../security/AUTHENTICATION.md), [AUTHORIZATION](../security/AUTHORIZATION.md), [PRIVACY](../security/PRIVACY.md)
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)
- [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (FR-API group), [TESTING](../testing/TESTING.md)
