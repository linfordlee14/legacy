# FUNCTIONAL_REQUIREMENTS
### Testable functional requirements for the Legacy platform, grouped by domain

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md), [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md) |

## 1. Purpose

This document defines the behavior of Legacy as testable functional requirements using the `FR-<DOM>-###` scheme and the fifteen domain codes of [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4: ING, KG, MEM, RAG, SRCH, TWIN, AGT, TL, VER, API, UI, SEC, PRIV, OPS, DATA. Every requirement traces to at least one product requirement in [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md) and is implemented by feature specifications in [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md).

## 2. Goals

- Turn each product requirement into behavior specific enough to write acceptance tests against.
- Encode the confidence-tier and privacy-tier disciplines as enforced behavior in every domain, not as policy text.
- Make the manual verification queue of [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §12 a concrete product workflow (see FR-VER-003).
- Keep the requirement set implementable by a solo founder: Musts define v1 behavior, Shoulds sequence after.

## 3. Scope

**In scope**

- Functional behavior across all fifteen domains, covering features F1 to F16.
- Workflow-level behavior: verification queue, publish approvals, succession activation, redaction propagation.

**Out of scope**

- Quality targets (latency, availability, compliance): [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md).
- Screen-level design: [../ui/UI_UX.md](../ui/UI_UX.md) and [../ui/DESIGN_SYSTEM.md](../ui/DESIGN_SYSTEM.md).
- Attribute-level data definitions: [../database/DATABASE_SCHEMA.md](../database/DATABASE_SCHEMA.md).
- Endpoint-by-endpoint API detail: [../api/API_SPECIFICATION.md](../api/API_SPECIFICATION.md).

## 4. Requirements

Each table row: stable ID, MoSCoW priority, testable requirement, one-line rationale with product requirement trace in parentheses. "System" means Legacy; "owner" means the authenticated owner role; "surface" means portfolio, workspace, API, or vault.

### 4.1 ING: ingestion and capture (F1)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-ING-001 | Must | The system accepts documents (PDF, office formats, Markdown, plain text), images, audio, video, presentations, code repositories, AI conversation exports, and freeform notes via upload, URL, and connected-source jobs. | Full format coverage of the knowledge domains (PR-001). |
| FR-ING-002 | Must | Scanned documents and images are processed with OCR and vision-model description through the Model Router; extracted text is stored as a derived artifact linked to the original. | Photos and scans are unsearchable without extraction (PR-001, SYS-008). |
| FR-ING-003 | Must | Audio and voice recordings are transcribed with timestamps and, where determinable, speaker labels; transcripts are derived artifacts linked to the original media. | Voice capture is a first-class input (PR-001). |
| FR-ING-004 | Must | Videos are processed into an audio transcript plus scene or keyframe descriptions, both linked to the original. | Talks and demos are otherwise opaque blobs (PR-001). |
| FR-ING-005 | Must | GitHub repository ingestion snapshots code, README, language statistics, and commit metadata as Artifacts, and generates a code-understanding summary per repository. | GitHub `linfordlee14` is the verified core of the project record (PR-001, SYS-029). |
| FR-ING-006 | Must | AI conversation imports are parsed into Conversation entities preserving turns, timestamps, participants, and the model used. | AI conversations are a named knowledge domain (PR-001). |
| FR-ING-007 | Must | Every ingestion runs as an IngestionJob with states queued, processing, failed, complete; failures retry with backoff and land in an owner-visible dead-letter view. | Silent ingestion loss is corpus corruption (SYS-004). |
| FR-ING-008 | Must | Every ingested and derived item records provenance: source, capture method, transformation chain, timestamp, and initial tier P2 unless the owner sets otherwise at capture. | Provenance at write time only (PR-002, PR-044, PR-046). |
| FR-ING-009 | Should | Near-duplicate detection flags matches above a similarity threshold at ingestion and asks the owner to keep, merge, or discard. | Decades of capture demand deduplication (PR-004). |
| FR-ING-010 | Should | Quick capture (note, photo, or link with optional tags) completes in at most three interactions from the workspace entry screen. | Capture friction kills lifelong archives (PR-003). |

### 4.2 KG: knowledge graph (F2)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-KG-001 | Must | Ingested content is analyzed for candidate entities of the canonical types (SPEC_CONVENTIONS §6) with type and extraction confidence recorded. | Structure begins with extraction (PR-005). |
| FR-KG-002 | Must | Candidate entities are resolved against the existing graph before node creation; ambiguous matches queue for owner review instead of auto-merging. | Wrong merges are worse than duplicates (PR-006). |
| FR-KG-003 | Must | Relationships are stored as typed Edges carrying provenance: the artifact or claim that produced them and the extraction method. | An edge without provenance cannot be trusted or fixed (PR-044). |
| FR-KG-004 | Must | The owner can merge, split, edit, and deprecate entities and can declare alias mappings; the "Linford Lee" alias (🟡, MASTER_CONTEXT §1) remains unmerged until its verification queue item resolves. | Owner curation is the graph's error correction (PR-006, FR-VER-003). |
| FR-KG-005 | Must | Biographical claims are stored as Claim nodes linked to their subject entities and Source records; graph views can display per-claim tiers. | The Claim model is the provenance backbone (PR-024). |
| FR-KG-006 | Should | The API exposes graph traversal: neighbors, typed-edge filters, and bounded-depth subgraphs per entity. | Powers the explorer and associative browsing (PR-007, PR-035). |
| FR-KG-007 | Should | Scheduled consistency reports list orphan entities, dangling edges, and unsourced claims for owner review. | Graph rot is inevitable without inspection (PR-006). |
| FR-KG-008 | Must | Graph responses expose only entities, edges, and claims the requesting principal's tier permissions allow. | The graph must not become a tier bypass (PR-046). |

### 4.3 MEM: memory system (F7)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-MEM-001 | Must | Each session assembles working memory from the current interaction plus retrieved long-term MemoryRecords relevant to the task. | Canonical memory vocabulary in action (PR-018). |
| FR-MEM-002 | Must | Long-term memories persist as MemoryRecords typed episodic, semantic, procedural, or reflective, with embeddings for retrieval. | Types per [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md) (PR-018). |
| FR-MEM-003 | Must | Every MemoryRecord carries provenance (originating conversation or agent run) and inherits the most restrictive tier of its source content. | Memory must not launder tiers (PR-046, PR-044). |
| FR-MEM-004 | Must | No MemoryRecord is created from sealed P3 content, and memory retrieval filters by the requesting surface's permitted tiers. | Sealing includes memory (PR-033). |
| FR-MEM-005 | Must | The owner can browse, search, correct, and permanently delete memories; deletion cascades to embeddings and caches within the redaction window of FR-PRIV-004. | Owner governance of memory (PR-019). |
| FR-MEM-006 | Should | The Reflection Agent runs scheduled consolidation, producing reflective summaries linked to their source memories without deleting originals. | Compression with an audit trail (PR-020). |
| FR-MEM-007 | Should | Stale episodic memories are downweighted in retrieval by age and disuse, never silently deleted. | Relevance decay without data loss (PR-020, SYS-022). |
| FR-MEM-008 | Could | Contradictions between memories are detected and flagged to the owner with both records shown. | Memory hygiene, valuable but not v1-critical (PR-019). |

### 4.4 RAG: retrieval and question answering (F5)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-RAG-001 | Must | Question answering runs a staged pipeline: query understanding, hybrid retrieval, reranking, tier-filtered context assembly, generation, citation check. | Defined stages make failures diagnosable (PR-012, SYS-005). |
| FR-RAG-002 | Must | Every factual statement in an answer cites at least one Claim, Source, or Artifact; answers failing the citation check are blocked or visibly flagged before display. | Mandatory citations (PR-012). |
| FR-RAG-003 | Must | Statements grounded in self_reported or flagged claims use attribution or uncertainty language ("Linford reports that...", "unverified") and are never rendered as established fact. | Tier-aware grounding, the MASTER_CONTEXT §0 rule as behavior (PR-013). |
| FR-RAG-004 | Must | When retrieval yields insufficient evidence, the answer states that the corpus does not support a response and, on owner surfaces, offers to open a verification queue item. | Honest refusal over extrapolation (PR-014, FR-VER-003). |
| FR-RAG-005 | Must | Context assembly includes only content permitted for the requesting principal and surface; P0 surfaces assemble from P0 content only. | Tier enforcement inside the pipeline (PR-046). |
| FR-RAG-006 | Must | Answers stream token-by-token, with all citations resolvable when the answer completes. | Responsiveness without losing grounding (SYS-002). |
| FR-RAG-007 | Should | Each answer carries a confidence badge computed from the tier mix of its citations (all verified, mixed, self-reported only). | Explainability at a glance (PR-013). |
| FR-RAG-008 | Should | Ranking favors curated Claims over raw chunks and applies recency weighting for time-sensitive questions. | Curation should outrank noise (PR-024). |
| FR-RAG-009 | Should | Users can mark an answer or citation incorrect; the report routes to the verification queue with the answer context attached. | Feedback loops feed verification (PR-025). |

### 4.5 SRCH: search (F4)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-SRCH-001 | Must | A single query input accepts both natural-language and keyword queries. | One retrieval front door (PR-010). |
| FR-SRCH-002 | Must | Retrieval combines lexical and vector search with configurable fusion into one ranked list. | Hybrid beats either alone (PR-011, SYS-005). |
| FR-SRCH-003 | Must | Results filter by content type, entity, time range, privacy tier, and confidence tier, combinable. | Filters make a lifelong corpus navigable (PR-011). |
| FR-SRCH-004 | Must | Each result shows a snippet, source artifact, privacy tier badge, and confidence tier where the result is claim-backed. | Search results teach provenance (PR-044, PR-045). |
| FR-SRCH-005 | Must | Tier filtering executes in the query layer; content above the caller's permission never reaches the client, including in counts and aggregations. | Post-filtering in the client is a leak (PR-046). |
| FR-SRCH-006 | Must | Newly ingested content becomes searchable within the freshness window defined in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md). | Capture-to-findable latency is a user promise (PR-010). |
| FR-SRCH-007 | Should | Users can save searches and build Collections directly from result sets. | Curation from retrieval (PR-030). |
| FR-SRCH-008 | Could | Query suggestions draw on graph entities (people, projects, events) as typed. | Discoverability, not launch-critical (PR-007). |

### 4.6 TWIN: digital twin (F6)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-TWIN-001 | Must | The twin grounds every biographical statement in corpus Claims, Artifacts, or MemoryRecords; model prior knowledge about the owner is never presented as fact. | The twin speaks from the record only (PR-015). |
| FR-TWIN-002 | Must | The twin discloses that it is an AI representation at the start of every session and maintains a persistent visual indicator throughout. | Non-negotiable disclosure (PR-016). |
| FR-TWIN-003 | Must | Twin knowledge is surface-scoped: on public surfaces it grounds only in P0 content and verified claims; on the workspace it grounds in the owner's permitted tiers. | Two twins in effect, one identity (PR-027, PR-046). |
| FR-TWIN-004 | Must | The twin applies FR-RAG-003 attribution rules to self_reported and flagged claims in first person ("I have said that...", never asserting unverified claims as fact). | Tier discipline survives persona voice (PR-013). |
| FR-TWIN-005 | Must | When asked for views or facts absent from the corpus, the twin says the owner has not recorded a position; any extrapolation is explicitly labeled as extrapolation. | Fabricated opinions are the worst failure mode (PR-014). |
| FR-TWIN-006 | Should | Twin voice and style are calibrated from owner writing samples against the self-reported style guide (🟡, MASTER_CONTEXT §2); calibration choices are recorded as design decisions in [../ai/DIGITAL_TWIN.md](../ai/DIGITAL_TWIN.md). | Fidelity without upgrading 🟡 style facts (PR-017). |
| FR-TWIN-007 | Should | The owner can review twin conversation transcripts; corrections create verification queue items and memory updates. | The owner trains the twin by correction (PR-025, PR-019). |
| FR-TWIN-008 | Should | Under an activated succession plan, the twin states the owner's status, shifts to legacy phrasing, and applies the succession plan's content release rules. | The twin outlives the owner honestly (PR-042). |

### 4.7 AGT: agents and orchestration (F8)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-AGT-001 | Must | All AI tasks enter through the Orchestrator Agent, which produces a visible plan naming the roster agents it will delegate to. | One entry point, inspectable plans (PR-021). |
| FR-AGT-002 | Must | The agent roster is exactly the twelve agents of SPEC_CONVENTIONS §7; adding or renaming agents requires a specification change first. | Governance against agent sprawl (PR-021). |
| FR-AGT-003 | Must | Consequential actions (publish to P0, delete or redact content, change a tier, external writes, spend above a configured threshold) block on explicit owner approval with a diff-style preview. | Human-in-the-loop as enforced behavior (PR-022, PR-028). |
| FR-AGT-004 | Must | Every agent execution writes an AgentRun record: inputs, plan, tool calls, model calls with providers, token counts, cost, outputs, and outcome. | Auditability builds trust (PR-023, SYS-010). |
| FR-AGT-005 | Must | Budgets are enforced per run and per period; a run that would exceed budget pauses and notifies the owner rather than failing silently or overspending. | Cost control is a safety property here (SYS-019, SYS-026). |
| FR-AGT-006 | Must | Each agent's tool access is an explicit MCP allowlist (for example Tavily MCP for the Research Agent); calls outside the allowlist are refused and logged. | Bounded reach per agent (SYS-028). |
| FR-AGT-007 | Should | Agent failures retry within policy, then escalate to the owner with the failure context and the partial AgentRun attached. | Solo operators need failures to self-report (PR-023). |
| FR-AGT-008 | Should | Multi-agent work for one user request shares a correlation identifier so the full delegation chain reconstructs from logs. | End-to-end traceability across handoffs (PR-023). |

### 4.8 TL: timeline engine (F3)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-TL-001 | Must | Temporal extraction produces Event records from ingested content with a date precision level: exact, month, year, approximate, or unknown. | Uncertainty modeled, not faked (PR-008, PR-009). |
| FR-TL-002 | Must | Events normalize into a single chronology with consistent time zone handling; displayed precision never exceeds stored precision. | False precision is misinformation (PR-009). |
| FR-TL-003 | Must | When sources disagree about an event's date or occurrence, the conflict is recorded and a verification queue item is created. | Timeline conflicts are verification work (PR-025). |
| FR-TL-004 | Must | The owner can pin, correct, annotate, and hide events; curation overlays extraction and never destroys the extracted record. | Curated narrative atop honest data (PR-008). |
| FR-TL-005 | Must | Timeline rendering is tier-filtered; the public timeline renders P0 events only. | The timeline is a surface like any other (PR-046, PR-027). |
| FR-TL-006 | Should | The owner can define chapters (for example education, ALX era, Linfy Tech era) as named overlays grouping events. | Narrative structure for decades of events (PR-008). |
| FR-TL-007 | Should | Per-entity timelines render the chronology of a single Project, Organization, or Person. | Localized chronology for the explorer (PR-035). |

### 4.9 VER: verification, provenance, citations (F9)

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-VER-001 | Must | Claims carry exactly one tier: verified, self_reported, or flagged, mapping one-to-one to ✅, 🟡, 🔴 of MASTER_CONTEXT §0. | The tier system is the product's spine (PR-024). |
| FR-VER-002 | Must | Every Claim links to at least one Source, or is explicitly marked unsourced, in which case its tier is flagged. | No free-floating facts (PR-024). |
| FR-VER-003 | Must | A verification queue manages items with states open, evidence-attached, resolved, rejected; the initial queue is seeded from MASTER_CONTEXT §12 (source URL attachment, IUS Africa role, SpazaLink placement, HBS Foundry, ADEL and ICMM statuses, WorldQuant enrollment, Pie & AI listing, social presence gaps, live repo confirmation, alias mapping). | The §12 queue becomes a workflow (PR-025). |
| FR-VER-004 | Must | Tier transitions require attached evidence and explicit owner confirmation, and write an AuditLogEntry; the system never auto-upgrades a tier. | "Never upgrade without new evidence" enforced (PR-026). |
| FR-VER-005 | Must | A tier change propagates to all dependent surfaces (portfolio text, twin grounding, RAG behavior, badges) within a defined propagation window. | Stale tiers on live surfaces are silent lies (PR-026). |
| FR-VER-006 | Must | Citations render in a standard format resolving to the Source record with its retrieval date and, where applicable, URL. | Citations must be checkable, not decorative (PR-012). |
| FR-VER-007 | Should | Source URLs are re-checked on a schedule; unreachable sources flag their dependent Claims for review. | Link rot erodes verification over decades (PR-049). |
| FR-VER-008 | Should | Contradiction detection flags Claims that conflict with each other or with new evidence, creating queue items. | The corpus should argue with itself productively (PR-025). |
| FR-VER-009 | Should | The Research Agent proposes candidate evidence for open queue items but can never resolve an item itself. | Machines gather, the owner decides (PR-022, PR-026). |

### 4.10 API: public and internal APIs

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-API-001 | Must | The `/v1` REST API exposes resources for canonical entities, search, question answering, agent runs, ingestion jobs, verification queue, vault, and administration. | API-first per SYS-002 (PR-050). |
| FR-API-002 | Must | Authentication uses OAuth 2.0 / OIDC and personal access tokens; anonymous requests reach only P0 read endpoints. | AuthN boundary matches the tier boundary (PR-046). |
| FR-API-003 | Must | Generation endpoints stream via Server-Sent Events, including partial-answer and citation events. | Streaming contract for FR-RAG-006 (SYS-002). |
| FR-API-004 | Must | All list endpoints support pagination, filtering, and stable sort. | A million-item corpus needs disciplined listing (SYS-018). |
| FR-API-005 | Must | Errors follow a uniform machine-readable model (code, message, correlation ID) and never expose internals. | Debuggable for the owner, opaque to attackers (PR-023). |
| FR-API-006 | Must | Rate limits apply per principal, and all authenticated API access is audited. | Abuse control and forensics (SYS-010). |
| FR-API-007 | Should | API versioning follows a published deprecation policy with at least 12 months of notice for breaking changes. | Longevity applies to interfaces too (PR-049). |

### 4.11 UI: user interface

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-UI-001 | Must | The workspace provides capture, search, ask (RAG and twin), review queues, timeline, explorer, and settings as its primary navigation. | The owner's daily surface (PR-030). |
| FR-UI-002 | Must | The portfolio renders P0 content as a public site: projects, articles, talks, achievements, certifications, public timeline. | The public face (PR-027, PR-029). |
| FR-UI-003 | Must | Every content view displays its privacy tier badge and offers a provenance affordance showing source and transformation chain. | Tier and provenance always visible (PR-044, PR-046). |
| FR-UI-004 | Must | Claims render with confidence badges wherever they appear (search results, answers, portfolio, explorer), visually distinguishing verified, self-reported, and flagged. | Explainability in the visual language (PR-013, PR-024). |
| FR-UI-005 | Must | Citations are interactive: expanding a citation shows the Source detail without leaving the answer context. | Checking a citation must be one gesture (PR-012). |
| FR-UI-006 | Must | Review queue interfaces exist for the verification queue, publish approvals, ingestion dead letters, and entity-resolution reviews. | The human-in-the-loop needs a desk (PR-022, PR-025). |
| FR-UI-007 | Must | AI-generated or AI-transformed content is visually labeled as such on every surface. | Human versus machine authorship stays legible (PR-045). |
| FR-UI-008 | Should | Timeline and graph visual explorers support zoom, filtering, and navigation into underlying artifacts. | Exploration is the payoff of structure (PR-007, PR-008). |

### 4.12 SEC: security

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-SEC-001 | Must | Owner and trusted users authenticate via OIDC with multi-factor authentication; personal access tokens are scoped and expiring. | The corpus is a life; protect it accordingly (PR-046). |
| FR-SEC-002 | Must | Authorization is RBAC with roles owner, trusted, successor, and public; effective permission is the intersection of role capabilities and item tier. | Role times tier is the whole access model (PR-046, PR-047). |
| FR-SEC-003 | Must | Sessions are individually revocable and the owner can list active sessions and tokens. | Compromise response for a solo operator (SYS-031). |
| FR-SEC-004 | Must | All data is encrypted in transit (TLS) and at rest, including backups and vault archives at rest. | Baseline confidentiality (SYS-016). |
| FR-SEC-005 | Must | Security-relevant events (logins, permission changes, tier changes, exports, succession actions) write to the append-only audit log. | Forensics and deterrence (SYS-010). |
| FR-SEC-006 | Must | Successor access is escrowed: credentials or recovery paths activate only under the succession plan's verified conditions, with the mechanism specified in [../security/AUTHENTICATION.md](../security/AUTHENTICATION.md). | Succession without a standing backdoor (PR-042). |
| FR-SEC-007 | Should | Anomalous access patterns (mass export, unusual read volume, new geography) alert the owner in near real time. | Early warning fits a single-victim threat model (SYS-031). |
| FR-SEC-008 | Should | Dependencies are scanned and patched on a defined cadence with critical vulnerabilities addressed within a defined SLA. | Decades of operation means decades of CVEs (PR-049). |

### 4.13 PRIV: privacy and data governance

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-PRIV-001 | Must | Every item carries exactly one tier P0 to P3, assigned at creation, defaulting to P2. | The invariant of SPEC_CONVENTIONS §5 (PR-046). |
| FR-PRIV-002 | Must | Tier relaxation (toward P0) requires an explicit owner action with confirmation and writes an audit entry; tier restriction may be immediate. | Asymmetric friction protects by default (PR-047). |
| FR-PRIV-003 | Must | P3 sealing supports unlock conditions (date-based or succession-based); sealed content is excluded from search indexes, RAG and twin grounding, memory creation, external model calls, and default exports until unlocked. | A seal with no side channels (PR-032, PR-033, SYS-032). |
| FR-PRIV-004 | Must | Redaction or deletion propagates to derived chunks, embeddings, memories, caches, and search indexes within a defined propagation window, with completion reported to the owner. | Deletion that does not cascade is not deletion (PR-019). |
| FR-PRIV-005 | Must | Person entities other than the owner are tracked in a third-party register; exposing them on P0 requires owner review, and removal or minimization requests are honored per POPIA obligations. | Other people's data lives in this graph (PR-048). |
| FR-PRIV-006 | Must | The owner can export all personal data in machine-readable form; third parties can request a copy of data about themselves. | Data subject rights as features (PR-050, PR-048). |
| FR-PRIV-007 | Should | P1 grants are scoped to named Collections and tiers, expire by default, and are revocable immediately. | Trusted does not mean unlimited (PR-031). |
| FR-PRIV-008 | Should | New features touching tiers or third-party data pass a privacy review checklist before release, recorded in the repository. | Process guard for a one-person team (PR-048). |

### 4.14 OPS: deployment, observability, backup

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-OPS-001 | Must | Deployments are automated with one-step rollback to the previous version. | Solo operations cannot afford ceremony (SYS-013). |
| FR-OPS-002 | Must | The system emits structured logs, metrics, and traces, including per-agent and per-provider token and cost metrics. | Observability includes AI spend (SYS-010, SYS-026). |
| FR-OPS-003 | Must | Backups run on schedule and restore tests execute periodically with results recorded; targets live in [../deployment/BACKUP_AND_RECOVERY.md](../deployment/BACKUP_AND_RECOVERY.md). | Untested backups are hopes (PR-049). |
| FR-OPS-004 | Must | Background jobs (ingestion, consolidation, vault, verification re-checks) are monitored; stuck or dead-lettered jobs surface in the owner's review queues. | Async systems fail quietly unless watched (FR-ING-007). |
| FR-OPS-005 | Must | Monthly cost reports and threshold alerts cover infrastructure and model spend against the ceilings in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md). | Cost overrun is an existential risk here (SYS-019). |
| FR-OPS-006 | Should | Uptime checks on portfolio and API alert the owner through a channel independent of the platform itself. | The system cannot be its own only alarm (SYS-013). |
| FR-OPS-007 | Should | Operational runbooks are maintained as Markdown in the repository so any competent successor can operate the system. | Longevity includes operability by others (PR-042). |

### 4.15 DATA: database and storage

| ID | Priority | Requirement | Rationale (trace) |
|----|----------|-------------|-------------------|
| FR-DATA-001 | Must | Storage implements the canonical entities of SPEC_CONVENTIONS §6 exactly as defined in [../database/DATABASE_SCHEMA.md](../database/DATABASE_SCHEMA.md). | One vocabulary from spec to storage (PR-005). |
| FR-DATA-002 | Must | EmbeddingChunks record their source artifact, offsets, and the embedding model and version, enabling selective re-embedding during migrations. | Migration-ready from day one (PR-051, SYS-020). |
| FR-DATA-003 | Must | Media originals are immutable and stored with checksums; derived renditions are regenerable and marked as such. | Originals are irreplaceable (SYS-024, SYS-035). |
| FR-DATA-004 | Must | Referential integrity holds across Claims, Sources, entities, and Artifacts; unsourced Claims are impossible except in the explicit flagged state of FR-VER-002. | The provenance chain must not dangle (PR-024). |
| FR-DATA-005 | Must | Content mutations use soft delete with audit history; hard deletion happens only through the redaction workflow of FR-PRIV-004. | History-preserving by default, erasable by intent (PR-047). |
| FR-DATA-006 | Must | Schema migrations are versioned, tested against a staging copy, and reversible where feasible. | Decades of migrations demand discipline (SYS-011). |
| FR-DATA-007 | Should | Every stored content type has a documented open-format vault representation, kept in sync with [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md) §4.6. | Exportability is a schema property (PR-049, PR-041). |

## 5. Acceptance criteria

1. Traceability: every FR above cites at least one PR or SYS requirement, and every Must-priority PR in [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md) is cited by at least one FR.
2. Ingestion matrix: one sample of each FR-ING-001 format ingests to complete status with provenance (FR-ING-008) and becomes searchable within the FR-SRCH-006 window.
3. Tier wall: a scripted suite exercising search, RAG, twin, graph, timeline, API, and vault as an anonymous user returns zero non-P0 items across all channels including counts (FR-SRCH-005, FR-RAG-005, FR-TWIN-003, FR-KG-008, FR-TL-005).
4. Citation gate: 20 sampled answers show 100 percent citation coverage of factual statements, and every answer touching a 🟡 or 🔴 claim uses attribution language (FR-RAG-002, FR-RAG-003).
5. Verification queue: the MASTER_CONTEXT §12 seed items exist as open queue items; resolving one with evidence updates the claim tier, writes an audit entry, and propagates to a portfolio page within the FR-VER-005 window.
6. Approval gate: an agent attempting to publish, delete, or change a tier without owner approval is blocked and the attempt is logged (FR-AGT-003).
7. Sealing: a P3 journal entry is absent from search, answers, twin responses, memory, and a default vault; it appears only after its unlock condition is met (FR-PRIV-003).
8. Redaction: deleting a test artifact removes its chunks, embeddings, memories, and index entries within the propagation window, verified by direct store inspection (FR-PRIV-004).
9. Succession drill: activating a test succession plan grants the successor role exactly the planned content, switches the twin to succession mode, and audits every step (FR-SEC-006, FR-TWIN-008).

## 6. Dependencies

- [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md) and [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md): upstream requirements traced throughout.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 and §12: tier semantics and the verification queue seed.
- [../database/DATABASE_SCHEMA.md](../database/DATABASE_SCHEMA.md), [../knowledge/KNOWLEDGE_GRAPH.md](../knowledge/KNOWLEDGE_GRAPH.md), [../memory/MEMORY_SYSTEM.md](../memory/MEMORY_SYSTEM.md): authoritative definitions of entities, edges, and memory types.
- [../ai/RAG_PIPELINE.md](../ai/RAG_PIPELINE.md), [../ai/DIGITAL_TWIN.md](../ai/DIGITAL_TWIN.md), [../agents/MULTI_AGENT_ARCHITECTURE.md](../agents/MULTI_AGENT_ARCHITECTURE.md): pipeline and agent design realizing RAG, TWIN, AGT domains.
- [../security/AUTHENTICATION.md](../security/AUTHENTICATION.md), [../security/AUTHORIZATION.md](../security/AUTHORIZATION.md), [../security/PRIVACY.md](../security/PRIVACY.md): SEC and PRIV realization.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Citation checking is hard; over-strict gates make answers unusable, lax gates leak fabrication | Trust failure either way | FR-RAG-002 allows block or visible flag; tune via FR-RAG-009 feedback |
| Tier filtering implemented in multiple places drifts apart | Silent leaks | Single retrieval layer (SYS-005), acceptance criterion 3 as regression suite |
| Entity extraction floods the owner with review work | Curation abandoned, graph rots | Confidence thresholds in FR-KG-002, batch review UIs in FR-UI-006 |
| Redaction propagation misses a derived store added later | Deletion promise broken | FR-PRIV-004 completion reporting plus store inventory in [../database/DATABASE_SCHEMA.md](../database/DATABASE_SCHEMA.md) |
| Approval fatigue: too many FR-AGT-003 gates train reflexive approval | Safety gate becomes theater | Threshold tuning, batched approvals, clear diff previews |
| Succession mechanics never tested until needed | Failure at the worst moment | Acceptance criterion 9 succession drill, repeated annually |

## 8. Future enhancements

- Streaming ingestion connectors (note apps, phone camera roll sync) beyond upload and URL capture.
- Cross-language search and answering when non-English sources enter the corpus.
- Fine-grained P1 collaboration: comments and contributed memories from trusted users, with their own provenance.
- Semi-automated tier suggestions (never auto-applied) based on content classification.
- Voice interface for capture and twin conversation, building on FR-ING-003.

## 9. Examples

**Example 1: tier-aware answer flow (FR-RAG-002 to FR-RAG-004).** Workspace question: "What certifications do I hold?" The answer cites the ALX Africa alumnus claim as fact (✅), attributes the USAII CAIE certification as self-reported (🟡), and notes that WorldQuant University enrollment is flagged and pending verification (🔴), linking its open queue item.

**Example 2: verification queue item (FR-VER-003, illustrative JSON).**

```json
{
  "queue_item": "seeded-from MASTER_CONTEXT §12 item 2",
  "claim_summary": "SpazaLink placed 3rd at SA Startup Week 2026",
  "current_tier": "flagged",
  "status": "open",
  "candidate_evidence": ["awaiting Research Agent proposals (FR-VER-009)"],
  "resolution_rule": "owner confirmation with evidence required (FR-VER-004)"
}
```

**Example 3: approval gate (FR-AGT-003).** The Writing Agent finishes a portfolio draft about CyberBuddy and requests publish-to-P0. The owner sees a preview with tier badges, one 🟡 attribution, and citations; approval publishes and audits, rejection returns the draft with comments. No path publishes without this step.

**Example 4: sealed reflection (FR-PRIV-003).** The owner writes a prayer reflection sealed P3 until succession. It is stored encrypted, absent from every index and answer, and appears in a succession vault only if the succession plan releases P3 content.

## 10. Open questions

> TODO(verify): Which AI conversation export formats the owner actually has (platform-specific exports vary) before fixing FR-ING-006 parser scope.

> TODO(verify): Whether transcription and OCR quality for the owner's accent and document types meets acceptance thresholds; needs a pilot with real samples (FR-ING-002, FR-ING-003).

> TODO(verify): The concrete propagation windows for FR-VER-005 and FR-PRIV-004 are proposed in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md) but need owner sign-off as product promises.

> TODO(verify): Whether the public portfolio should expose a public twin at launch (FR-TWIN-003 supports it; the decision is a product choice not yet made).

> TODO(verify): Legal review of FR-PRIV-005 third-party mechanics against POPIA sections applicable to a personal-but-published archive.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier rules), §1 (alias), §12 (verification queue seed).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4 (domain codes), §5 (privacy tiers), §6 (entities), §7 (agent roster), §8 (memory vocabulary).
- [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md), [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md): all trace targets.

## 12. Related specifications

- [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md): quality targets referenced by FR-SRCH-006, FR-OPS-005, and others.
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md), [USER_STORIES](./USER_STORIES.md), [USE_CASES](./USE_CASES.md): downstream elaboration and persona linkage.
- [../api/API_SPECIFICATION.md](../api/API_SPECIFICATION.md), [../ui/UI_UX.md](../ui/UI_UX.md), [../ui/ACCESSIBILITY.md](../ui/ACCESSIBILITY.md).
- [../testing/TESTING.md](../testing/TESTING.md), [../testing/QUALITY_ASSURANCE.md](../testing/QUALITY_ASSURANCE.md): where the acceptance criteria above become test plans.
