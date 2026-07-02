# SYSTEM_REQUIREMENTS
### System composition, environments, capacity, and integration requirements for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) |

## 1. Purpose

This document defines the system-level requirements (`SYS-###`) for Legacy: what subsystems compose the platform, what environments it runs in, what capacity a single-owner system growing over decades must plan for, which external services it integrates with, and what the offline Legacy Vault must satisfy. It sits between the product requirements in [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md) and the architecture in [../architecture/MASTER_ARCHITECTURE.md](../architecture/MASTER_ARCHITECTURE.md); architecture decides how, this document constrains what the system must consist of and tolerate.

## 2. Goals

- Fix the canonical subsystem decomposition so every other specification names the same eight subsystems.
- Constrain external dependencies (model providers, MCP tools, GitHub) so that no single vendor becomes a survival risk.
- State capacity and growth assumptions honestly for one owner over decades, with TODO(verify) markers where real volumes are unknown.
- Make offline capability (the Legacy Vault) a system requirement, not an afterthought.

## 3. Scope

**In scope**

- System composition: web client, API backend, agent runtime, ingestion pipeline, retrieval services, graph and memory services, model router, storage.
- Environment requirements (development, staging, production) and hosting constraints.
- Capacity assumptions and data volume growth for a single-owner corpus.
- External integrations: Anthropic Claude API (primary), Google Gemini API, Groq API via the model router; MCP integrations (Supabase MCP, Tavily MCP); GitHub for repository ingestion.
- Offline Legacy Vault system requirements.

**Out of scope**

- Behavior-level requirements per subsystem: [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md).
- Quality targets (latency numbers, availability, RPO/RTO): [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md).
- Concrete infrastructure choices and topology: [../deployment/DEPLOYMENT.md](../deployment/DEPLOYMENT.md).

## 4. Requirements

### 4.1 System composition

Legacy is composed of exactly eight logical subsystems. The names below are canonical across all specifications.

```
                      +----------------------+
  Public visitors --> |  Web Client          | <-- Owner / trusted users
  (P0 portfolio)      |  (portfolio + wksp)  |
                      +----------+-----------+
                                 |  REST /v1 + SSE
                      +----------v-----------+
                      |  API Backend         |----> AuditLog (all subsystems)
                      +---+------+------+----+
                          |      |      |
             +------------+      |      +-------------+
             v                   v                    v
  +-------------------+  +---------------+  +-------------------+
  | Ingestion         |  | Agent Runtime |  | Retrieval         |
  | Pipeline          |  | (12 agents)   |  | Services          |
  +---------+---------+  +-------+-------+  +---------+---------+
            |                    |                    |
            |            +-------v-------+            |
            |            | Model Router  |--> Claude (primary)
            |            | (+ MCP tools) |--> Gemini, Groq
            |            +---------------+
            v                                         v
  +-------------------------------------------------------------+
  |  Graph & Memory Services (knowledge graph, memory engine)   |
  +-------------------------------+-----------------------------+
                                  v
  +-------------------------------------------------------------+
  |  Storage (PostgreSQL/Supabase + pgvector, object storage)   |
  +-------------------------------------------------------------+
```

| ID | Priority | Requirement | Rationale |
|----|----------|-------------|-----------|
| SYS-001 | Must | The system MUST include a Web Client serving two surfaces: the public portfolio (P0, unauthenticated) and the private workspace (authenticated), per the baseline Next.js decision in SPEC_CONVENTIONS §9. | Two audiences, one client codebase, hard tier boundary between surfaces (PR-027, PR-030). |
| SYS-002 | Must | The system MUST include an API Backend exposing all functionality as a versioned REST JSON API under `/v1` with Server-Sent Events for AI streaming; the Web Client MUST NOT bypass it. | API-first (SPEC_CONVENTIONS §9) keeps enforcement of tiers and audit in one place. |
| SYS-003 | Must | The system MUST include an Agent Runtime hosting the twelve canonical agents of SPEC_CONVENTIONS §7, with per-run budget, tool allowlists, and run logging. | PR-021 to PR-023 require governed orchestration, not free-floating scripts. |
| SYS-004 | Must | The system MUST include an Ingestion Pipeline processing IngestionJob records asynchronously: fetch, parse, OCR or transcribe, chunk, embed, link, index. | Ingestion of video, audio, and repositories cannot run synchronously in a request cycle. |
| SYS-005 | Must | The system MUST include Retrieval Services providing lexical search, vector search, and hybrid ranking over EmbeddingChunk and entity data, consumed by search (F4), RAG (F5), the twin (F6), and memory recall (F7). | One retrieval layer prevents four divergent implementations of tier filtering. |
| SYS-006 | Must | The system MUST include a Graph Service maintaining canonical entities and typed Edges, modeled in PostgreSQL node and edge tables for v1 per SPEC_CONVENTIONS §9. | PR-005; a dedicated graph database is a deferred decision gate, not a v1 dependency. |
| SYS-007 | Must | The system MUST include a Memory Service persisting MemoryRecord rows (episodic, semantic, procedural, reflective) with vector embeddings and owner-governed deletion. | PR-018 and PR-019 require memory as a first-class subsystem. |
| SYS-008 | Must | The system MUST include a Model Router through which all LLM, embedding, transcription, and vision model calls pass; no subsystem calls a provider API directly. | Vendor independence (PR-049 to PR-051) is only enforceable at a single choke point. |
| SYS-009 | Must | The system MUST include a Storage layer: PostgreSQL (Supabase) with pgvector for structured data and embeddings, and object storage for media originals, per SPEC_CONVENTIONS §9 (🟡 stack alignment, recorded as a design decision). | One primary datastore keeps a solo-founder system operable. |
| SYS-010 | Must | Every subsystem MUST emit AuditLogEntry records for security-relevant and content-mutating operations to a shared, append-only audit log. | Cross-cutting auditability underpins PR-023, PR-026, PR-047. |

### 4.2 Environment requirements

| ID | Priority | Requirement | Rationale |
|----|----------|-------------|-----------|
| SYS-011 | Must | The system MUST support three environments: local development, staging, and a single production tenant; production holds the only real corpus. | Real legacy data must never be scattered across test environments. |
| SYS-012 | Must | Non-production environments MUST use synthetic or explicitly copied-and-scrubbed data; P3 content MUST never leave production. | PR-033; sealed content in a dev database is a breach. |
| SYS-013 | Must | Production MUST run on managed cloud services requiring no always-on manual administration by the owner. | The operator is one person with a company to run. |
| SYS-014 | Should | Hosting SHOULD prefer regions and providers compatible with POPIA cross-border transfer conditions for personal information. | The owner is in South Africa; see [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md) privacy group. |
| SYS-015 | Must | The Web Client MUST function on current evergreen desktop and mobile browsers; no native mobile app is required for v1. | Scoping decision per SPEC_CONVENTIONS §9. |
| SYS-016 | Must | All secrets (provider keys, tokens, MCP credentials) MUST live in a managed secret store, never in configuration files or the repository. | A specification repository plus a leaked key is a public corpus. |

### 4.3 Capacity assumptions (single owner, decades)

Legacy serves exactly one owner, a small circle of trusted users, and anonymous portfolio visitors. Capacity planning is about corpus growth over decades, not user concurrency.

| ID | Priority | Requirement | Rationale |
|----|----------|-------------|-----------|
| SYS-017 | Must | The system MUST be sized for one owner, up to 25 concurrent trusted (P1) users, and portfolio bursts of at least 1,000 unique visitors per day (design assumption, for example after a talk or launch). | Single-owner reality with public-moment spikes. |
| SYS-018 | Must | The system MUST tolerate a corpus of at least 1 million EmbeddingChunk records and 100,000 Artifacts without redesign. | Two to three decades of steady capture lands in this order of magnitude (design assumption). |
| SYS-019 | Must | Idle cost MUST scale toward the storage floor: compute for ingestion and agents MUST NOT run when there is no work. | Solo-founder economics; see cost ceilings in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md). |
| SYS-020 | Should | The system SHOULD support full corpus re-processing (re-chunking, re-embedding, re-linking) as a batch operation completable within 30 days at assumed maximum corpus size. | Model and format migrations (PR-051) require re-processing everything, eventually more than once. |
| SYS-021 | Should | Retrieval quality and latency targets SHOULD be validated at 10x current corpus size at least annually. | Growth is slow enough to plan for and fast enough to break assumptions silently. |

### 4.4 Data volume growth assumptions

The table below records planning assumptions. None of these are measured facts about the owner's existing archives.

| Content class | Assumed steady-state growth | Assumed year-one import |
|---------------|-----------------------------|-------------------------|
| Notes, journals, reflections | 500 to 2,000 items per year | backlog unknown |
| Documents, specs, presentations | 200 to 500 files per year | backlog unknown |
| Photos | 1,000 to 5,000 per year | backlog unknown |
| Video and audio | 10 to 100 hours per year | backlog unknown |
| Code repositories | 10 to 40 active repos snapshotted | ~dozens (GitHub `linfordlee14`, ✅) |
| AI conversations | 1,000 to 10,000 per year | backlog unknown |

> TODO(verify): Actual volumes of the owner's existing archives (drives, phone media, note apps, AI conversation exports, repository count and sizes) are unknown. An inventory pass must replace every "backlog unknown" above before capacity numbers in SYS-018 are finalized.

| ID | Priority | Requirement | Rationale |
|----|----------|-------------|-----------|
| SYS-022 | Must | Nothing in the corpus is ever deleted by capacity policy; growth is met with storage, tiering, and archival, never expiry. | A legacy system that expires memories has failed its one job (PR-049). |
| SYS-023 | Must | Storage MUST maintain at least 12 months of projected growth headroom, reviewed quarterly. | Prevents emergency migrations under pressure. |
| SYS-024 | Should | Media originals SHOULD be stored once at full fidelity with derived renditions (thumbnails, transcodes, transcripts) regenerable rather than precious. | Originals are irreplaceable; derivations are cattle. |

### 4.5 External integrations

| ID | Priority | Requirement | Rationale |
|----|----------|-------------|-----------|
| SYS-025 | Must | The Model Router MUST support Anthropic Claude API as the primary LLM provider, with Google Gemini API and Groq API as configured alternates (🟡 stack alignment per MASTER_CONTEXT §5, adopted here as a design decision). | Primary-plus-alternates is the minimum for PR-049 vendor independence. |
| SYS-026 | Must | Router policy MUST select providers per task class (reasoning, drafting, embedding, transcription, vision) under per-feature cost budgets and provider health checks. | Different work has different quality and cost profiles; budgets enforce SYS-019. |
| SYS-027 | Must | Loss of any single model provider MUST NOT make stored content unreadable or block read paths (search over existing indexes, portfolio, vault); only generation-dependent features may degrade. | The corpus must outlive any AI vendor. |
| SYS-028 | Must | External tool access from the Agent Runtime MUST go through MCP integrations on an explicit allowlist, initially Supabase MCP and Tavily MCP (🟡 stack alignment, design decision). | Bounded tool surface is a security requirement, not a convenience (PR-022). |
| SYS-029 | Must | The system MUST integrate with GitHub to ingest the owner's repositories (account `linfordlee14`, ✅) including code snapshots, READMEs, and repository metadata as Artifacts. | GitHub is the owner's verified primary code presence and a core knowledge domain. |
| SYS-030 | Should | The Research Agent SHOULD use Tavily MCP (or an equivalent allowlisted search tool) to gather candidate Sources for the verification queue. | PR-025 needs an evidence supply chain, not manual browsing alone. |
| SYS-031 | Must | All integration credentials MUST be scoped to least privilege, individually revocable, and rotated on a defined schedule. | A decades-long system will survive multiple credential leaks; blast radius must be small. |
| SYS-032 | Should | Provider-facing data flows SHOULD send the minimum content necessary per call, and MUST never send P3 content to any external model provider while sealed. | PR-033; sealing includes third-party model providers. |

### 4.6 Offline Legacy Vault

| ID | Priority | Requirement | Rationale |
|----|----------|-------------|-----------|
| SYS-033 | Must | The system MUST include a Vault Generator producing a versioned export: Markdown for textual content, JSON for structured entities and claims, original media files, and a machine-readable manifest. | PR-041; formats per SPEC_CONVENTIONS §9 offline capability decision. |
| SYS-034 | Must | A vault MUST be readable offline using only ubiquitous software (file browser, text editor, web browser opening local files); a static HTML index MUST be included. | The vault's threat model is "the platform no longer exists." |
| SYS-035 | Must | Every vault MUST include per-file checksums and a signed manifest so successors can detect tampering or corruption. | Integrity is meaningless if unverifiable decades later. |
| SYS-036 | Must | Vault content selection MUST respect privacy tiers: default vaults exclude sealed P3 content; succession vaults apply the release rules of the succession plan (PR-042). | The vault must not become the P3 side channel prohibited by PR-033. |
| SYS-037 | Should | Vault generation SHOULD run on a schedule (proposed: monthly incremental, annual full) with completion and integrity results reported to the owner. | PR-043; an unmonitored export rots silently. |
| SYS-038 | Should | The vault format itself SHOULD be versioned with a documented changelog so a successor can interpret any vault generation ever produced. | Format drift across decades is certain; undocumented drift is fatal. |

## 5. Acceptance criteria

1. An architecture review maps every component in [../architecture/MASTER_ARCHITECTURE.md](../architecture/MASTER_ARCHITECTURE.md) to exactly one of the eight subsystems of SYS-001 to SYS-009, with no orphan components.
2. Static inspection confirms no subsystem holds provider API credentials except the Model Router (SYS-008) and no secret exists outside the secret store (SYS-016).
3. A staged provider outage (Claude API unreachable) leaves portfolio, search over existing indexes, and vault reads functioning (SYS-027).
4. A synthetic corpus at SYS-018 scale (1 million chunks) passes the retrieval latency targets of [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md).
5. A full re-embedding of the synthetic corpus completes within the SYS-020 window with measured cost recorded.
6. A generated vault passes checksum verification and is navigated successfully on an offline machine by a person with no prior exposure to the system (SYS-034, SYS-035).
7. Audit inspection shows AuditLogEntry records from all eight subsystems for a scripted day of representative operations (SYS-010).
8. A staging environment scan finds zero P3-tier records (SYS-012).

## 6. Dependencies

- [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md): every SYS requirement serves at least one PR.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §9 baseline architecture defaults, adopted here as design decisions.
- [../architecture/MASTER_ARCHITECTURE.md](../architecture/MASTER_ARCHITECTURE.md) for the decision records realizing this composition.
- [../deployment/DEPLOYMENT.md](../deployment/DEPLOYMENT.md), [../deployment/BACKUP_AND_RECOVERY.md](../deployment/BACKUP_AND_RECOVERY.md) for environment and recovery realization.
- External services: Anthropic Claude API, Google Gemini API, Groq API, Supabase, GitHub, Tavily (via MCP).

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Supabase as primary datastore concentrates vendor risk | Migration under duress | SYS-009 uses standard PostgreSQL and pgvector; portability requirements in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md) |
| Model provider pricing or API changes over decades | Features become unaffordable or break | SYS-008 router choke point, SYS-025 to SYS-027 alternates and degradation |
| Growth assumptions in §4.4 are wrong in either direction | Over-spend or capacity crisis | TODO(verify) inventory pass; SYS-021 annual 10x validation |
| MCP tool compromise gives agents unintended reach | Data exfiltration or destructive writes | SYS-028 allowlist, SYS-031 least privilege, PR-022 human approval gates |
| Vault format understood by no one in 2046 | Succession fails at the last mile | SYS-034 ubiquitous-software rule, SYS-038 versioned format documentation |

## 8. Future enhancements

- Local or self-hosted model support behind the Model Router for cost control and additional privacy (particularly for P2 content processing).
- Dedicated graph database behind the Graph Service interface when the deferred decision gate in SPEC_CONVENTIONS §9 is triggered.
- Additional MCP integrations (calendar, email ingestion) after the allowlist governance of SYS-028 matures.
- Cold-storage archival tier for media originals with restore-on-demand.

## 9. Examples

**Example 1: model routing decision (illustrative JSON).**

```json
{
  "task_class": "rag_answer",
  "surface": "private_workspace",
  "provider_order": ["anthropic_claude", "google_gemini", "groq"],
  "budget_usd_per_call": 0.05,
  "p3_content_permitted": false
}
```

**Example 2: vault manifest excerpt (illustrative JSON).**

```json
{
  "vault_version": "2026.07",
  "generated_at": "2026-07-02T06:00:00Z",
  "tier_policy": "P0-P2, P3 excluded (no succession trigger)",
  "files": [
    {"path": "entities/projects/cyberbuddy.json", "sha256": "..."},
    {"path": "articles/2026/building-cyberbuddy.md", "sha256": "..."}
  ]
}
```

**Example 3: degradation matrix for a Claude API outage (SYS-027).**

| Capability | During outage |
|------------|---------------|
| Portfolio browsing | Unaffected |
| Search over existing indexes | Unaffected |
| RAG answers, twin, agents | Degraded to alternate provider or paused with clear notice |
| Ingestion | Queued; OCR and transcription retried when a provider is available |
| Vault read | Unaffected by design |

## 10. Open questions

> TODO(verify): Actual data volumes of existing owner archives (see §4.4); blocks final sizing of SYS-018 and SYS-023.

> TODO(verify): Confirm Supabase hosting region options against POPIA cross-border transfer requirements for SYS-014; legal review input needed.

> TODO(verify): The owner's actual current provider accounts and plan tiers (Anthropic, Google, Groq, Supabase, Tavily) are 🟡 self-reported stack items; confirm which accounts exist before integration build-out.

> TODO(verify): Signing mechanism and key custody for the SYS-035 vault manifest (who holds keys across succession) needs a decision in [../security/SECURITY.md](../security/SECURITY.md).

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §5 (technical stack, tiered), §6 (GitHub presence).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §6 (system entities), §7 (agent roster), §9 (baseline architecture decisions).
- [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md) cross-cutting groups (provenance, privacy, longevity).

## 12. Related specifications

- [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md): behavior of each subsystem defined here.
- [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md): quality targets these subsystems must meet.
- [../architecture/MASTER_ARCHITECTURE.md](../architecture/MASTER_ARCHITECTURE.md), [../database/DATABASE_SCHEMA.md](../database/DATABASE_SCHEMA.md), [../api/API_SPECIFICATION.md](../api/API_SPECIFICATION.md).
- [../agents/MULTI_AGENT_ARCHITECTURE.md](../agents/MULTI_AGENT_ARCHITECTURE.md), [../ai/AI_ARCHITECTURE.md](../ai/AI_ARCHITECTURE.md), [../memory/MEMORY_SYSTEM.md](../memory/MEMORY_SYSTEM.md).
- [../deployment/DEPLOYMENT.md](../deployment/DEPLOYMENT.md), [../deployment/OBSERVABILITY.md](../deployment/OBSERVABILITY.md), [../deployment/BACKUP_AND_RECOVERY.md](../deployment/BACKUP_AND_RECOVERY.md).
