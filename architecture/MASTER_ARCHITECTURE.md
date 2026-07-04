# MASTER_ARCHITECTURE
### System architecture, container model, data flows, and architecture decision records for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) |

---

## 1. Purpose

This document is the authoritative system architecture for Legacy, a single-owner, lifelong AI Digital Legacy platform. It defines the system context, the container-level architecture, component responsibilities and interfaces, the key end-to-end data flows, the cross-cutting concerns that every component must honor, and the full set of Architecture Decision Records (ADR-01 upward). Every other technical specification in this repository refines a part of this document; none may contradict it without a superseding ADR.

## 2. Goals

1. Give implementers a complete, unambiguous structural picture: what the containers are, what each one owns, and how they talk to each other.
2. Record every significant architectural decision as an ADR with context, decision, consequences, and status, so future sessions (human or AI) can trace why the system is shaped this way.
3. Encode the platform's non-negotiable qualities structurally: provenance integrity, privacy-tier enforcement at every layer, auditability, cost control, and decades-scale longevity.
4. Anchor all stack choices to [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §5 as design decisions with confidence-tier honesty, never as invented facts.
5. Keep the architecture small enough for a single owner to operate and cheap enough to run for decades.

## 3. Scope

**In scope:** architectural overview and quality attributes; system context (actors and external systems); container-level architecture in C4 style; component responsibilities and interfaces; the five key data flows (ingestion, RAG query, twin conversation, agent task, export); cross-cutting concerns; ADR-01 through ADR-15.

**Out of scope:** attribute-level data modeling (see [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)); endpoint-level API contracts (see [API_SPECIFICATION](../api/API_SPECIFICATION.md)); agent prompt and orchestration internals (see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)); RAG pipeline internals (see [RAG_PIPELINE](../ai/RAG_PIPELINE.md)); deployment topology and environments (see [DEPLOYMENT](../deployment/DEPLOYMENT.md)); UI structure (see [UI_UX](../ui/UI_UX.md)).

## 4. Requirements

Detailed numbered functional and non-functional requirements live in the `specs/` documents (the FR-API, FR-DATA, FR-RAG, FR-AGT, FR-VER, and FR-PRIV groups in particular). The subsections below are the normative structural requirements of the architecture itself.

### 4.1 Architectural overview and quality attributes

Legacy is a single-tenant, API-first system: one Postgres-centered knowledge core, one FastAPI backend exposing REST `/v1` with SSE streaming, one Next.js web application, and an agent runtime that performs all AI work through a model-routing abstraction. All AI output is grounded in the Claim and Source provenance model and filtered by privacy tier before it leaves any layer.

| Quality attribute | Architectural meaning | Primary mechanism |
|-------------------|----------------------|-------------------|
| Longevity | The system must remain readable and operable for decades | Open formats (Markdown, JSON), Legacy Vault export, boring-technology bias (ADR-03, ADR-12, ADR-13) |
| Provenance integrity | No stated fact without a traceable Claim and tier | Claim/Source as first-class schema (ADR-10), citation-mandatory AI responses |
| Privacy | P0-P3 tiers enforced at every layer, default P2 | RBAC plus per-item tiers (ADR-09), tier filter pushdown in retrieval |
| Auditability | Every read of sensitive data and every mutation is reconstructable | Event-sourced audit log (ADR-11) |
| Cost control | Bounded spend for a self-funded owner | Model router with budgets (ADR-06), per-run token budgets, caching |
| Evolvability | Components replaceable without rewrites | API-first boundaries (ADR-14), decision gates (ADR-05) |
| Portability | Owner can leave any vendor with data intact | Vault export (ADR-12), standard Postgres, standard object storage |

### 4.2 System context

**Actors (human and machine principals):**

| Actor | Description | Typical access |
|-------|-------------|----------------|
| Owner | Linford Musiyambodza, the single tenant; full control | All tiers P0-P3, all admin surfaces |
| Trusted user | Explicitly granted collaborator, mentee, or family member | P0-P1, scoped by Grant |
| Public visitor | Anonymous reader of the published portfolio and public twin | P0 only |
| Estate steward | Successor principal activated under succession conditions | Conditional, defined by Grants with succession triggers (see [SECURITY](../security/SECURITY.md)) |
| External AI consumer | Future AI agent or service reading Legacy through the API with a token | Tier-scoped by its token, machine-readable guidance in [API_SPECIFICATION](../api/API_SPECIFICATION.md) |

**External systems:**

| External system | Role | Boundary |
|-----------------|------|----------|
| LLM providers (Anthropic Claude API primary; Google Gemini API, Groq API secondary) | Text generation, embeddings, tool-use reasoning | Reached only through the Model Router; no other container calls a provider directly |
| GitHub | Source of repository snapshots, activity, and public code artifacts | Read via the Ingestion Pipeline connectors |
| MCP tool servers (Supabase MCP, Tavily MCP, others over time) | Tool capabilities for agents (data operations, web research) | Reached only through the Agent Runtime's MCP client |

The provider list mirrors MASTER_CONTEXT §5, which carries a 🟡 tier for AI platform APIs and data infrastructure.

> TODO(verify): Confirm active Anthropic, Google, and Groq API accounts and the Supabase project that will host production, per MASTER_CONTEXT §5 (🟡).

### 4.3 Container-level architecture

C4 container view, described in prose below the diagram. Every synchronous arrow is HTTPS; internal service calls share the API Backend's process boundary in v1 (modular monolith, see ADR-14 consequences).

```
  Owner | Trusted User | Public Visitor | Estate Steward        External AI Consumer
     |         |              |               |                          |
     +---------+------+-------+---------------+                          |
                      | HTTPS (browser)                                  |
        +-------------v--------------+                                   |
        |     Web App (Next.js)      |                                   |
        | owner console, portfolio,  |                                   |
        | twin chat, admin surfaces  |                                   |
        +-------------+--------------+                                   |
                      | REST /v1 + SSE                                   |
                      +--------------------+-----------------------------+
                                           |
        +----------------------------------v-----------------------------------+
        |                        API Backend (FastAPI)                         |
        |  authn/authz, privacy-tier filter, idempotency, rate limits, audit   |
        +---+--------+---------+---------+---------+-------------+---------+---+
            |        |         |         |         |             |         |
   +--------v--+ +---v-----+ +-v-------+ +v-------+ +-----------v--+ +----v------+
   | Ingestion | |Retrieval| | Graph   | | Memory | |    Agent     | |  Vault    |
   | Pipeline  | | Service | | Service | | Service| |   Runtime    | | Exporter  |
   +-----+-----+ +----+----+ +----+----+ +---+----+ +--+--------+--+ +-----+-----+
         |            |           |          |         |        |          |
         |            |           |          |         |   MCP client --> MCP tool
         |            |           |          |         |                  servers
         |       +----v-----------v----------v---------v---+              |
         |       |               Model Router              +--> LLM providers
         |       |  provider selection, budgets, fallback  |   (Claude, Gemini, Groq)
         |       +----+------------------------------------+              |
         |            |                                                   |
   +-----v------------v---------------------------------------------------v-----+
   |        Supabase Postgres + pgvector          |         Object Storage      |
   |  entities, graph, claims, memory, audit      |  media, uploads, exports    |
   +----------------------------------------------------------------------------+
         ^
         +--- GitHub (repo capture via Ingestion Pipeline connectors)
```

### 4.4 Component responsibilities and interfaces

| Container | Responsibilities | Provided interface | Consumed interfaces |
|-----------|------------------|--------------------|---------------------|
| Web App (Next.js) | Owner console, public portfolio site, twin chat UI, verification queue UI, admin surfaces; renders only what the API returns (no direct database access) | Browser UI | REST `/v1` plus SSE |
| API Backend (FastAPI) | Single entry point: authentication, authorization, privacy-tier filtering on every response, request validation, idempotency, rate limiting, audit event emission, routing to internal services | REST `/v1` JSON plus SSE streams | All internal services, Postgres |
| Ingestion Pipeline | Connector execution (uploads, GitHub sync, URL capture, conversation import), parsing, normalization to Markdown, chunking, embedding requests, IngestionJob state machine | Internal job API, invoked via `/v1` ingestion endpoints | Model Router (embeddings), Object Storage, Postgres, GitHub |
| Retrieval Service | Lexical, semantic, and hybrid search; RAG context assembly with tier pre-filtering; reranking; citation candidate selection | Internal search and context API | pgvector, Postgres full-text, Model Router (embeddings, reranking) |
| Graph Service | Entity and Edge persistence, traversal and neighborhood queries, temporal validity handling, graph integrity rules | Internal graph API | Postgres (node and edge tables) |
| Memory Service | MemoryRecord lifecycle: write, decay scoring, consolidation, redaction; serves working-memory assembly for agents and twin | Internal memory API | Postgres, pgvector, Model Router (consolidation summaries) |
| Agent Runtime | Executes the 12-agent roster from [SPEC_CONVENTIONS §7](../docs/SPEC_CONVENTIONS.md); planning, delegation, approval gates, AgentRun records, MCP tool calls | Internal task API, invoked via `/v1` agent endpoints | Model Router, MCP tool servers, all internal services through the same interfaces the API uses |
| Model Router | Single choke point for every LLM and embedding call: provider selection by task class, fallback, retry, token accounting, budget enforcement, response caching | Internal completion and embedding API | Anthropic, Google, Groq APIs |
| Supabase Postgres + pgvector | System of record: all entities, graph, claims, memory, embeddings, audit log | SQL over the platform's client (internal only) | None |
| Object Storage (Supabase Storage) | Original media, upload staging, vault export bundles; content-addressed keys | Signed URL issuance via API Backend | None |
| Vault Exporter | Builds versioned Legacy Vault bundles (Markdown, JSON, media manifest), verifies checksums, records export manifests | Internal export API, invoked via `/v1` vault endpoints | Postgres, Object Storage |

Interface rules: the Web App and all external consumers use only `/v1`; internal services expose interfaces only to the API Backend and Agent Runtime; only the Model Router holds provider credentials; only the API Backend holds session authority.

### 4.5 Key data flows

**Flow A: ingestion.**
1. Owner submits content (file upload, GitHub sync request, URL, or conversation export) via the Web App; the API Backend creates an IngestionJob (status queued) and returns its id.
2. Ingestion Pipeline picks up the job, stores the original bytes in Object Storage under a content-addressed key, and records an Artifact.
3. Parser normalizes content to canonical Markdown; the Curation Agent deduplicates and tags.
4. Chunker produces EmbeddingChunk rows inheriting the item's privacy tier; the Model Router returns embeddings, stored in pgvector with model version.
5. Graph Agent extracts candidate entities and Edges; each extracted factual statement is written as a Claim at tier `self_reported` (or `flagged` when extraction confidence is low) linked to a Source record for the ingested item.
6. Items needing human review enter the verification queue; the job closes with counts, and an AuditLogEntry records the whole job.

**Flow B: RAG query.**
1. A caller sends a question to the ask endpoint; the API Backend resolves the caller's maximum privacy tier.
2. Retrieval Service runs hybrid retrieval (lexical plus vector) with the tier filter applied inside the query, never after it.
3. Candidates are reranked; the context bundle is assembled with each passage's Claim ids and tiers attached.
4. Model Router sends the grounded prompt to the selected provider; the response streams back over SSE.
5. The API Backend validates that every factual assertion in the answer maps to a citation; uncited assertions are stripped or the response is marked degraded.
6. Response, citations, token usage, and tier context are audited.

**Flow C: twin conversation.**
1. A caller opens a twin conversation; the API Backend stamps the session with the caller's tier and the twin disclosure metadata (AI-generated, persona version, model id).
2. Memory Service assembles working memory: relevant episodic, semantic, procedural, and reflective MemoryRecords within tier.
3. Retrieval Service adds grounded context as in Flow B; the Twin Agent's persona instructions are applied.
4. Model Router streams the reply over SSE; every biographical statement carries its Claim tier, and 🟡 or 🔴 backed statements are voiced attributively ("Linford has described..."), honoring MASTER_CONTEXT §0.
5. The conversation is persisted as a Conversation entity (default P2); memory writes are queued for the Reflection Agent.

**Flow D: agent task.**
1. Owner (or a scheduled trigger) creates an AgentRun with a task, budget, and approval policy.
2. Orchestrator Agent produces a plan (steps, delegated agents, tool needs, cost estimate) and persists it on the AgentRun.
3. Steps marked consequential (external calls, publishing, deletions, tier changes) pause the run at `awaiting_approval`; the owner approves or rejects via the API.
4. Approved steps execute; every MCP tool call and model call is metered against the run budget by the Model Router and logged.
5. The run completes with a result summary; all artifacts it created carry provenance pointing at the run.

**Flow E: export.**
1. Owner requests a vault export with a tier ceiling (for example P0-P2, or full including P3).
2. Vault Exporter snapshots entities to Markdown files with JSON frontmatter, graph and claims to JSON, and builds a media manifest with checksums referencing Object Storage originals.
3. The bundle is versioned, checksummed end to end, written to Object Storage, and a signed download link is issued.
4. The export manifest (contents, tier ceiling, checksums, format versions) is stored and audited; the bundle is readable offline with no Legacy software.

### 4.6 Cross-cutting concerns

**Provenance propagation.** Claim and Source identifiers travel with content through every hop: ingestion writes them, chunks carry them, retrieval returns them, prompts embed them, responses cite them, and exports serialize them. No layer may strip provenance; a component that cannot preserve it must reject the operation.

**Privacy-tier enforcement at every layer.** The tier check is not a gateway feature; it is repeated defense: the API Backend filters responses, the Retrieval Service pushes tier predicates into vector and lexical queries, the Memory Service scopes working memory, the Agent Runtime caps agent context at the run initiator's tier, the Twin Agent applies disclosure rules, and the Vault Exporter enforces the export ceiling. Default tier for new content is P2; tier relaxation requires explicit owner action (see [PRIVACY](../security/PRIVACY.md)).

**Auditability.** Every mutation, every AI generation, every P1-P3 read, every grant change, and every export produces an immutable AuditLogEntry (ADR-11). Audit is a write path, never a best-effort side effect: if the audit write fails, the operation fails.

**Cost control.** The Model Router is the single metering point: per-task-class provider selection (fast cheap models for classification and tagging, the primary model for generation and twin voice), per-AgentRun token budgets, monthly spend ceilings, and cache-first embedding reuse (content hash keyed). Budget exhaustion degrades gracefully to queued work, never to silent overspend.

### 4.7 Architecture decision records

ADR statuses: Proposed, Accepted, Superseded. All ADRs below are Accepted as v1 baseline decisions unless noted. The `ADR-##` range is owned by this document.

#### ADR-01: Single-tenant, single-owner design
**Context.** Legacy exists to preserve one person's knowledge and voice across decades. Multi-tenancy adds isolation machinery, noisy-neighbor concerns, and compliance surface that serve no user here.
**Decision.** The system is single-tenant with exactly one Owner principal; other humans and machines are grantees, never tenants.
**Consequences.** Simpler authorization (one tier lattice, one grant table), simpler backups, cheaper operations. Reuse as a product for others would require deliberate re-architecture; that is acceptable and out of scope.

#### ADR-02: Specification-driven development
**Context.** MASTER_CONTEXT §2 records SDD as the owner's self-reported working discipline (🟡). The repository predates any code by design.
**Decision.** Every component is specified in this repository before implementation; code changes that contradict a spec require a spec change first.
**Consequences.** Higher upfront writing cost, drastically lower drift across AI-assisted implementation sessions; the repo itself becomes an ingestible artifact of the legacy.
> TODO(verify): Confirm the owner's preferred SDD file conventions (mission, roadmap, techstack naming) for the implementation repos, per MASTER_CONTEXT §2 (🟡).

#### ADR-03: Supabase Postgres as the primary datastore
**Context.** The owner's demonstrated and self-reported stack includes Supabase with pgvector (MASTER_CONTEXT §5, 🟡). The system needs relational integrity, full-text search, vectors, row-level security, and managed operations on a solo-founder budget.
**Decision.** One PostgreSQL instance managed by Supabase is the system of record for all structured data; Supabase Storage serves as Object Storage.
**Consequences.** One backup story, one query surface, transactional writes across entities, graph, and audit. Vendor exposure is mitigated because everything is standard Postgres plus open formats, restorable anywhere (supports ADR-12).
> TODO(verify): Confirm the production Supabase project, region, and plan limits (🟡 stack claim).

#### ADR-04: pgvector for embeddings
**Context.** Embedding search must live next to relational filters (privacy tier, entity type, time) without cross-store joins. Corpus scale is one person's lifetime of content, not web scale.
**Decision.** Embeddings are stored in pgvector columns with approximate-nearest-neighbor indexing; no external vector database in v1.
**Consequences.** Tier filtering happens inside the same query as similarity search (essential for §4.6); one fewer system to run. If corpus growth or latency ever exceeds pgvector's comfort, the Retrieval Service interface localizes the swap. Reassess at the scale gate defined in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md).

#### ADR-05: Postgres-native knowledge graph for v1, decision gate for a graph database
**Context.** The knowledge graph (typed Edges between canonical entities) needs traversal to a few hops, temporal validity, and provenance per edge. Dedicated graph databases add operational weight and split the transactional boundary.
**Decision.** Model the graph natively in Postgres as node tables plus one Edge table; recursive traversal to bounded depth is served by the Graph Service. A decision gate is set: if median 3-hop neighborhood queries exceed interactive latency targets in the NFR document, or edge count grows beyond low millions, evaluate a dedicated graph store.
**Consequences.** Graph writes share transactions with entities, claims, and audit. Deep analytics (community detection, centrality) are deferred to batch jobs or the future gate. The Edge taxonomy lives in [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md).

#### ADR-06: Model-router abstraction over Claude, Gemini, and Groq
**Context.** MASTER_CONTEXT §5 records Anthropic Claude, Google Gemini, and Groq APIs in the owner's stack (🟡). Providers change pricing, models, and availability on timescales far shorter than this system's lifetime.
**Decision.** All LLM and embedding calls pass through a Model Router: Claude is the primary provider for generation and twin voice; Gemini and Groq serve fallback and cost-optimized task classes. Routing policy is configuration, not code scattered across services.
**Consequences.** Provider swap is a config change; budgets and token accounting are centralized; prompt portability constraints (provider-neutral prompt formats) must be honored by all agents.
> TODO(verify): Confirm current provider accounts and model availability at implementation time (🟡). The embedding model choice is resolved: see ADR-16.

#### ADR-07: MCP for tool integrations
**Context.** Agents need tools (database operations, web research, future integrations). The owner's stack references Supabase MCP and Tavily MCP (MASTER_CONTEXT §5, 🟡). MCP is an open protocol with growing ecosystem support.
**Decision.** Agent tool access is exclusively via MCP servers registered with the Agent Runtime; no bespoke per-tool SDK wiring inside agents.
**Consequences.** Uniform tool auditing and budgeting; new capabilities arrive by registering a server. MCP protocol evolution is a tracked dependency; each registered server carries an allowlist of tools and a tier ceiling.
> TODO(verify): Confirm the initial MCP server set and their authentication methods (🟡).

#### ADR-08: REST plus SSE over GraphQL and WebSockets
**Context.** Consumers are the Web App, future AI agents, and scripts across decades. Longevity favors the most boring, cacheable, debuggable contract. Streaming is needed only server-to-client (tokens, progress).
**Decision.** The API is resource-oriented REST JSON under `/v1`; streaming uses Server-Sent Events. No GraphQL, no WebSockets in v1.
**Consequences.** Simple caching, curl-ability, trivial client generation; some over-fetching accepted. Bidirectional realtime features, if ever needed, get their own ADR.

#### ADR-09: RBAC plus per-item privacy tiers
**Context.** Role-based access alone cannot express "this journal is sealed, this project is public"; per-item ACLs alone are unmanageable over decades.
**Decision.** Authorization combines coarse roles (owner, steward, trusted, public, service) with the P0-P3 tier on every item; effective access is the intersection of the caller's grant ceiling and the item's tier. Nothing auto-relaxes.
**Consequences.** One mental model everywhere (API, retrieval, memory, export); grants stay few and auditable. Tier must exist on every row that carries content, which DATABASE_SCHEMA enforces as a base field.

#### ADR-10: Claim and Source provenance model as first-class schema
**Context.** MASTER_CONTEXT §0 defines confidence tiers and the rule that unverified claims are never upgraded silently. A legacy system that hallucinates its owner's biography is worse than none.
**Decision.** Claim (with tier enum `verified`, `self_reported`, `flagged`) and Source are first-class entities. AI responses about the owner must cite Claims; the never-auto-upgrade rule is a data integrity constraint (described in DATABASE_SCHEMA) and a Verification Agent responsibility.
**Consequences.** Every pipeline writes claims, which costs storage and effort; in exchange the product's core promise (truthful legacy) is structurally enforced rather than prompt-enforced.

#### ADR-11: Event-sourced audit log
**Context.** Trust over decades, succession scenarios, and AI actors demand reconstructable history: who saw what, what changed, which agent did it, at what cost.
**Decision.** An append-only AuditLogEntry stream records every mutation, AI generation, sensitive read, grant change, and export, with actor, subject, and payload summary. Mutations fail if the audit write fails. The log is never updated or deleted, only appended (redaction tombstones reference but do not erase entries).
**Consequences.** Storage grows monotonically (acceptable at single-owner scale, with archival policy in DATABASE_SCHEMA); investigations and steward handover become queries, not forensics.

#### ADR-12: Legacy Vault open-format export
**Context.** The platform must outlive every vendor and possibly its own runtime. The Offline Capable principle (see [LEGACY_PRINCIPLES](../docs/LEGACY_PRINCIPLES.md)) requires readable data with no running system.
**Decision.** The Vault Exporter produces versioned bundles: Markdown with JSON frontmatter for entities, JSON for graph, claims, and memory, a checksum-verified media manifest, and a plain-text reading guide. Export is a first-class scheduled feature, not a one-off script.
**Consequences.** Schema changes must ship with export format updates in the same release; the vault format becomes a compatibility contract tested in CI (see [TESTING](../testing/TESTING.md)).

#### ADR-13: Markdown as the canonical document format
**Context.** The owner's working practice is Markdown-first (this repository included); Markdown is the most durable widely-readable rich-text format available.
**Decision.** All authored and ingested textual content is normalized to CommonMark-compatible Markdown as its canonical stored form; originals are retained as Artifacts in Object Storage.
**Consequences.** One parsing target for chunking, rendering, and export; lossy conversions (complex office documents) keep the original artifact linked for fidelity.

#### ADR-14: API-first boundaries
**Context.** The Web App is one consumer among several (agents, scripts, external AI); privileging it with private backdoors would fork behavior and break auditability.
**Decision.** Every capability is exposed through `/v1` before or at the same time as any UI; the Web App uses the public API. Internally, v1 ships as a modular monolith (one FastAPI deployment hosting the internal services of §4.4) with interfaces clean enough to extract later.
**Consequences.** The API contract is the product's real surface; UI can be rebuilt in any era. Monolith-first keeps solo operations tractable while preserving extraction seams.

#### ADR-15: Deferred mobile client
**Context.** The owner has verified Android skills (Kotlin, Jetpack Compose, MASTER_CONTEXT §5 ✅), but a mobile client multiplies surface area without advancing the core promise (capture, preserve, retrieve, represent).
**Decision.** No mobile client in v1. Mobile capture needs are met by the responsive Web App and by ingestion connectors. A native Android app is a named future enhancement.
**Consequences.** Some capture friction on mobile accepted for now; the API-first rule (ADR-14) guarantees a future app needs no backend rework.

#### ADR-16: Pinned embedding model, gemini-embedding-001 at 1536 dimensions
**Context.** [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md) AIA-09 left the embedding model an open decision balancing quality, cost per million tokens, dimension size, and decades-long availability, with AIA-10 requiring 1536 dimensions or fewer. ADR-06 already fixes the provider set (Anthropic, Google, Groq) behind the Model Router, and MVP-016 cannot ship chunk indexing without the choice. Verified against the official Gemini API documentation on 2026-07-04: `gemini-embedding-001` is Google's designated stable text embedding model (3072 dimensions by default, Matryoshka truncation with documented recommended sizes 768/1536/3072, 2048-token input limit per text, embeddings at non-default dimensions require client-side normalization); a newer multimodal `gemini-embedding-2` reached general availability but is the newest release, not the designated stable text model.
**Decision.** The platform embedding model is pinned to exactly `gemini-embedding-001` with `output_dimensionality` 1536, vectors L2-normalized at write and query time, cosine distance, recorded on every chunk as embedding model version `gemini-embedding-001:1536`. Selection rationale: it stays inside the ADR-06 provider set (no vendor expansion); it is the stable designated model rather than the newest release, per the AIA-07 nothing-changes-silently rule; 1536 dimensions satisfies AIA-10 and halves pgvector index cost against the default; the corpus is text-only in this phase, so multimodal capability buys nothing yet. Per AIA-07 the identifier is pinned and immutable in a versioned routing configuration; no auto-tracking alias is ever used.
**Consequences.** Embedding calls route exclusively through the Model Router's Gemini adapter with a `LEGACY_GEMINI_API_KEY` secret arriving via the environment (DEP-18). Chunk rows carry the version string, ANN indexes are scoped to it, and vectors from different versions are never compared (AIA-11). Migrating (including to `gemini-embedding-2`, the natural successor candidate) is a Gate G2 or later decision following AIA-12/RAG-28: dual index rebuilt from source artifacts, evaluation against the retrieval set, atomic switch, old index retained one backup cycle, recorded as a new ADR. Embeddings remain a rebuildable cache; source artifacts are the durable asset.

## 5. Acceptance Criteria

1. Every container named in §4.3 has exactly one owning specification document listed in §12, and no capability exists outside a container.
2. Every stack choice in this document traces to an ADR, and every ADR resting on a 🟡 or 🔴 claim carries a confirmation TODO.
3. The five data flows in §4.5 are implementable without introducing a component or interface not defined in §4.4.
4. A reviewer can answer "where is privacy tier enforced" with at least one mechanism per container on the read path.
5. No AI-generated response path exists that can emit an uncited factual assertion about the owner (Flow B step 5, Flow C step 4).
6. The document contains no SQL, no executable code, and no em dashes, per [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md).

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): confidence tiers and the §5 stack evidence anchoring ADR-03, ADR-04, ADR-06, ADR-07.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): entity names, privacy tiers, agent roster, baseline defaults this document formalizes.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) and [API_SPECIFICATION](../api/API_SPECIFICATION.md): the attribute-level and contract-level refinements of this architecture.
- The requirements documents in `specs/` (FR groups ING, KG, MEM, RAG, SRCH, TWIN, AGT, TL, VER, API, SEC, PRIV, OPS, DATA) constrain component behavior.
- External: Anthropic, Google, and Groq API availability; Supabase platform; MCP protocol stability; GitHub API.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Supabase platform discontinuity or pricing shift | Loss of managed operations | Standard Postgres and open formats (ADR-03, ADR-12); documented restore-anywhere runbook in [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) |
| pgvector performance ceiling as corpus grows | Slow retrieval, degraded RAG | ADR-04 swap seam behind Retrieval Service; scale gate metrics |
| Graph-in-Postgres traversal limits | Slow neighborhood queries | ADR-05 decision gate with explicit thresholds |
| LLM provider churn (models, prices, deprecations) | Broken flows, cost spikes | ADR-06 router; provider-neutral prompts; budget ceilings |
| Modular monolith erodes into tangled monolith | Extraction becomes rewrite | Interface rules in §4.4 enforced in review; ADR-14 |
| Audit log growth over decades | Storage cost, slow queries | Append-only with archival tiering policy in DATABASE_SCHEMA |
| Solo-operator bus factor | System stalls without the owner | Vault export, steward grants, this specification repository itself |
| 🟡 stack claims prove wrong at implementation | Rework of ADR-03/04/06/07 | Confirmation TODOs resolved before build tasks start (roadmap gate) |

## 8. Future Enhancements

1. Native Android client (reverses ADR-15 via a new ADR when capture friction justifies it).
2. Dedicated graph database behind the Graph Service if the ADR-05 gate trips.
3. Read replica or edge cache for the public portfolio if traffic warrants.
4. Additional MCP servers (calendar, email ingestion, research tools) under ADR-07.
5. Voice interface for the twin (streaming audio over the existing SSE seam or a successor ADR).
6. Multi-region disaster recovery beyond scheduled vault exports.

## 9. Examples

**Example: tracing one fact through the architecture.** The verified fact "CyberBuddy was presented at GDG Cape Town Pet Projects 2026" (MASTER_CONTEXT §7 ✅) enters via Flow A as a Talk entity plus a Claim at tier `verified` linked to a Source for the event page. Its chunks carry tier P0 (owner published it). A public visitor asks the twin about speaking experience: Flow C retrieves the chunk (tier filter passes at P0), the answer cites the Claim id with tier `verified`, the citation appears in the SSE stream, and the read is audited with actor type `public`.

**Example: a flagged fact stays honest.** The claim "SpazaLink placed 3rd at SA Startup Week 2026" is 🔴 in MASTER_CONTEXT §7. It exists as a Claim at tier `flagged`. The twin, asked about awards, either omits it or voices it as "Linford has reported a placement that is not yet independently verified", because Flow C step 4 requires attributive voice below `verified`. No pipeline may auto-upgrade it (ADR-10); only a Verification Agent action with new Source evidence, approved by the owner, moves it.

## 10. Open Questions

- Should the ADR set split into `architecture/decisions/` one-file-per-ADR once it exceeds roughly fifteen entries (mirrors the SPEC_CONVENTIONS open question)?
- Where exactly does the Agent Runtime execute in v1 deployment terms (same process as FastAPI, worker pool, or scheduled jobs)? Owned by [DEPLOYMENT](../deployment/DEPLOYMENT.md); this document only fixes its interfaces.
- ~~Which embedding model and dimension ship first?~~ Resolved: ADR-16 pins `gemini-embedding-001` at 1536 dimensions.
- Does the estate steward's activation mechanism require an offline legal artifact in addition to Grants with succession conditions? Owned by [SECURITY](../security/SECURITY.md).
> TODO(verify): Resolve the 🟡 stack confirmations named in ADR-02, ADR-03, ADR-06, ADR-07 before roadmap build tasks begin.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (confidence tiers), §5 (technical expertise), §12 (verification queue).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §5 (privacy tiers), §6 (canonical entities), §7 (agent roster), §9 (baseline decisions).
- C4 model conventions for context and container views (used descriptively; no tooling dependency).

## 12. Related Specifications

- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): attribute-level schema for every entity named here.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): the `/v1` contract for every flow in §4.5.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): the Agent Runtime's roster and orchestration.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md): Flows B and C internals.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): Edge taxonomy behind the Graph Service.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): MemoryRecord semantics behind the Memory Service.
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md), [AUTHENTICATION](../security/AUTHENTICATION.md), [AUTHORIZATION](../security/AUTHORIZATION.md): the enforcement details of ADR-09.
- [DEPLOYMENT](../deployment/DEPLOYMENT.md), [OBSERVABILITY](../deployment/OBSERVABILITY.md), [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): operating this architecture.
