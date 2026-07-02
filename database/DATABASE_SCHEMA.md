# DATABASE_SCHEMA
### Logical database schema for all Legacy entities, provenance, indexing, and data lifecycle (no SQL)

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) |

---

## 1. Purpose

This document is the authoritative attribute-level definition of every canonical entity in Legacy, per [SPEC_CONVENTIONS §6](../docs/SPEC_CONVENTIONS.md). It describes the logical schema for Supabase Postgres with pgvector (ADR-03, ADR-04 in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md)) entirely in prose and tables: no SQL DDL appears here. It also defines the provenance sub-model, the Edge relationship table, the indexing strategy, and the data lifecycle rules (soft delete, redaction, retention, migration, decades-scale longevity).

## 2. Goals

1. Define every knowledge and system entity with columns, logical types, requiredness, keys, and relationships, so implementation requires no schema invention.
2. Productize the MASTER_CONTEXT §0 confidence tiers as the Claim/Source sub-model with the never-auto-upgrade rule stated as a data integrity constraint.
3. Guarantee that privacy tier, provenance, and audit hooks exist on every row that carries content.
4. Specify indexing conceptually (vector, lexical, timeline, graph) so query patterns in the FR-SRCH, FR-RAG, FR-KG, and FR-TL groups are served.
5. Make the schema survivable for decades: open formats, additive migration policy, explicit versioning.

## 3. Scope

**In scope:** logical schema for all 22 knowledge entities and 8 system entities; common base fields; provenance sub-model; Edge table; embedding storage; indexing strategy in words; lifecycle policies.

**Out of scope:** physical tuning (fill factors, partitioning specifics), SQL of any kind, Supabase row-level security policy text (mechanics in [AUTHORIZATION](../security/AUTHORIZATION.md)), edge-type taxonomy semantics (owned by [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md)), memory consolidation algorithms (owned by [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)).

## 4. Requirements

### 4.1 Modeling conventions and logical types

- Table names are the singular PascalCase entity names from SPEC_CONVENTIONS §6; the physical naming convention (snake case) is an implementation detail.
- Logical types used below: `identifier` (time-ordered unique id, UUID v7 style), `short text`, `long text` (Markdown per ADR-13), `timestamp` (with time zone, UTC stored), `date`, `partial date` (date plus a precision qualifier: exact, month, year, approximate), `enum` (closed value list given in words), `boolean`, `integer`, `decimal`, `JSON document`, `vector` (fixed-dimension embedding, dimension bound to the embedding model version), `reference (Entity)` (foreign key described in words), `entity reference` (polymorphic pair of entity type plus identifier).
- Every reference is enforced as a foreign key except polymorphic entity references, which are enforced by service-layer validation plus a periodic integrity job (described in [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)).
- All identifiers are stable forever: never reused, never renumbered (machine-consumer guarantee in [API_SPECIFICATION](../api/API_SPECIFICATION.md)).

### 4.2 Common base fields

Every entity table includes these columns unless its subsection states an exception. They are not repeated in the per-entity tables.

| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| id | identifier | yes | Primary key, time-ordered, globally unique across the system |
| created_at | timestamp | yes | Set once at insert |
| updated_at | timestamp | yes | Maintained on every update |
| deleted_at | timestamp | no | Soft-delete marker; non-null rows are excluded from all default reads (§4.8) |
| privacy_tier | enum (P0 public, P1 trusted, P2 private, P3 sealed) | yes | Defaults to P2; JournalEntry defaults to P3; relaxation requires explicit owner action |
| created_by | reference (User) | yes | The principal that created the row (owner, grantee, or service principal acting for an agent) |
| origin_type | enum (manual, ingestion, agent, system) | yes | How the row came to exist |
| origin_ref | entity reference | no | The IngestionJob or AgentRun that produced the row, when origin_type is ingestion or agent |
| row_version | integer | yes | Optimistic concurrency counter, incremented on update |

Exceptions: `AuditLogEntry` is append-only and omits updated_at, deleted_at, and row_version; `EmbeddingChunk` derives privacy_tier from its parent (denormalized copy, §4.6); `User`, `Role`, and `Grant` carry no privacy_tier (they are access-control rows, visible only to owner and steward surfaces).

Provenance linkage rule: knowledge entities do not embed claim columns; Claims reference entities through a subject entity reference (§4.4), and Edges carry a claim reference (§4.5). This keeps facts atomic and separately tiered.

### 4.3 Knowledge entities

Only entity-specific columns are listed; base fields from §4.2 apply to all. "Keys" describes uniqueness beyond the primary key, in words.

#### Person
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| full_name | short text | yes | Display name |
| aliases | JSON document | no | Known alternate names and handles, as a list |
| relationship_to_owner | short text | no | For example collaborator, mentor, family; edge types carry the structured form |
| bio | long text | no | Free-form Markdown biography |
| links | JSON document | no | Public profile URLs, each with a label |

Keys: no natural uniqueness (names collide); duplicates are merged by the Curation Agent. Relationships: connected to Organization, Project, Event via Edges (for example collaborated_on, member_of). The owner is represented by a Person row referenced from system configuration, kept in sync with MASTER_CONTEXT through Claims only.

#### Organization
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | short text | yes | Organization name |
| org_type | enum (company, community, school, program, nonprofit, other) | yes | Classification |
| description | long text | no | Markdown description |
| links | JSON document | no | Website and profile URLs |

Keys: name unique case-insensitively among non-deleted rows. Relationships: roles held by Person rows are Edges with temporal validity (for example founder_of, member_of).

#### Project
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | short text | yes | Project name |
| slug | short text | yes | URL-safe stable handle for portfolio routes |
| status | enum (concept, active, paused, shipped, archived) | yes | Lifecycle state |
| summary | short text | no | One-paragraph pitch |
| description | long text | no | Full Markdown write-up |
| started_on | partial date | no | Start, possibly approximate |
| ended_on | partial date | no | End, when applicable |
| links | JSON document | no | Repo, demo, press URLs |
| featured | boolean | yes | Portfolio prominence flag, defaults false |

Keys: slug unique among non-deleted rows. Relationships: Edges to Person (collaborators), Organization, Skill (demonstrates), Artifact (has_artifact), Event (originated_at, for example a hackathon), Achievement.

#### Artifact
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Human-readable name |
| artifact_type | enum (document, photo, video, presentation, code_snapshot, audio, dataset, other) | yes | Media class |
| storage_ref | short text | yes | Object Storage key, content-addressed |
| mime_type | short text | yes | Original MIME type |
| byte_size | integer | yes | Size of original |
| checksum | short text | yes | Cryptographic hash of the original bytes |
| captured_at | timestamp | no | When the underlying content was created, if known |
| canonical_markdown | long text | no | Normalized text rendition when extractable (ADR-13) |
| extraction_status | enum (pending, extracted, partial, not_applicable, failed) | yes | Text extraction state |

Keys: checksum unique among non-deleted rows (dedupe guard). Relationships: attached to any knowledge entity via Edges (has_artifact); referenced by Source when an artifact is evidence.

#### Event
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Event name |
| event_type | enum (milestone, talk_event, hackathon, launch, education, personal, community, other) | yes | Timeline classification |
| starts_at | timestamp | yes | Start instant (midnight when only a date is known) |
| ends_at | timestamp | no | End instant for ranges |
| date_precision | enum (exact, day, month, year, approximate) | yes | Honesty qualifier for timeline rendering |
| location | short text | no | Free-form place name |
| description | long text | no | Markdown detail |

Keys: none natural. Relationships: the backbone of the Timeline Engine (FR-TL group); Edges connect Events to Projects, People, Organizations, Talks, Achievements.

#### Idea
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Idea name |
| body | long text | no | Markdown exploration |
| status | enum (spark, exploring, parked, promoted, discarded) | yes | Idea lifecycle |
| promoted_project_id | reference (Project) | no | Set when an idea graduates into a Project |

Keys: none. Relationships: Edge inspired_by to any entity; promotion recorded both as the reference above and an Edge for graph traversal.

#### Note
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | no | Optional heading |
| body | long text | yes | Markdown content |
| note_context | short text | no | Free-form capture context (meeting, reading, field note) |

Keys: none. Relationships: Edges about (Note to any entity); Notes are the most common chunking source for EmbeddingChunk.

#### JournalEntry
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| entry_date | date | yes | The day the entry belongs to |
| title | short text | no | Optional heading |
| body | long text | yes | Markdown content |
| entry_kind | enum (daily, reflection, prayer, gratitude, freeform) | yes | Owner-defined classification, defaults freeform |

Keys: none (multiple entries per day allowed). Privacy: defaults to P3 (sealed), per the tier examples in SPEC_CONVENTIONS §5; unsealing conditions live in [PRIVACY](../security/PRIVACY.md). Relationships: Reflection Agent reads JournalEntry rows (within tier rules) to produce MemoryRecords and Lessons.

#### Conversation
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | no | Display title, may be AI-generated |
| channel | enum (twin, ask, agent, imported) | yes | Where the conversation happened |
| participant_user_id | reference (User) | no | The human party, when known |
| started_at | timestamp | yes | First message time |
| transcript | JSON document | yes | Ordered messages with role, content, timestamps, disclosure metadata |
| summary | long text | no | AI summary, provenance-marked as generated |
| token_count | integer | no | Total tokens across the exchange |

Keys: none. Relationships: source material for MemoryRecords; a Conversation that produced content links to it via Edges (produced).

#### Skill
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | short text | yes | Skill name |
| category | enum (language, framework, platform, domain, practice, leadership, other) | yes | Grouping for display |
| evidence_level | enum (demonstrated, claimed) | yes | Demonstrated requires at least one supporting Edge to a shipped Project or Artifact; mirrors the MASTER_CONTEXT §5 guidance |
| description | long text | no | Markdown notes |

Keys: name unique case-insensitively. Relationships: Edges demonstrates (Project to Skill), certifies (Certification to Skill). Integrity rule in words: evidence_level may be demonstrated only while at least one non-deleted supporting Edge exists; the Curation Agent downgrades orphaned skills to claimed.

#### Certification
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | short text | yes | Credential name |
| issuer_org_id | reference (Organization) | no | Issuing body |
| issued_on | partial date | no | Award date |
| expires_on | date | no | Expiry when applicable |
| credential_url | short text | no | Public verification URL |
| status | enum (active, expired, in_progress, claimed) | yes | Lifecycle; claimed marks self-reported credentials awaiting a Source |

Keys: none. Relationships: certifies Edges to Skill; every Certification should be backed by a Claim whose tier reflects MASTER_CONTEXT evidence (for example ALX Africa ✅ verified, USAII CAIE 🟡 self_reported).

#### Achievement
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | What was achieved |
| achieved_on | partial date | no | When |
| description | long text | no | Markdown detail |
| awarding_org_id | reference (Organization) | no | Awarding body, when any |

Keys: none. Relationships: Edges to Project and Event; display logic must render the strongest linked Claim tier next to every Achievement (FR-VER group), because several known achievements are 🔴 flagged in MASTER_CONTEXT §7.

#### Goal
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Goal statement |
| description | long text | no | Markdown detail |
| horizon | enum (quarter, year, decade, lifetime) | yes | Planning horizon |
| status | enum (active, achieved, revised, dropped) | yes | Lifecycle |
| target_date | date | no | Optional deadline |

Keys: none. Relationships: Edges pursues (Goal to Project), reflects_value; the Mentor Agent reads Goals within tier.

#### Lesson
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | The lesson in one line |
| body | long text | yes | Markdown narrative |
| learned_on | partial date | no | When it crystallized |

Keys: none. Relationships: Edges learned_from (Lesson to Project, Event, or JournalEntry); primary output of the Reflection Agent.

#### Book
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Book title |
| authors | JSON document | yes | List of author names |
| isbn | short text | no | ISBN when known |
| reading_status | enum (to_read, reading, finished, abandoned) | yes | Owner's status |
| finished_on | partial date | no | Completion date |
| takeaways | long text | no | Markdown notes |

Keys: isbn unique when present. Relationships: Edges influenced (Book to Idea, Goal, Lesson).

#### Talk
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Talk title |
| delivered_on | partial date | no | Delivery date |
| venue | short text | no | Venue or community, for example GDG Cape Town |
| event_id | reference (Event) | no | The Event it occurred at |
| slides_artifact_id | reference (Artifact) | no | Slides |
| recording_url | short text | no | Public recording |

Keys: none. Relationships: presents Edges to Project (for example the CyberBuddy talk, MASTER_CONTEXT §9 ✅).

#### Article
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| title | short text | yes | Article title |
| platform | enum (devto, linkedin, personal_site, other) | yes | Publication venue |
| canonical_url | short text | no | Public URL when published |
| published_on | partial date | no | Publication date |
| body_markdown | long text | no | Canonical Markdown body (ADR-13) |
| publication_status | enum (draft, published, retired) | yes | Lifecycle |

Keys: canonical_url unique when present. Relationships: authored_by is implicit (single owner); Edges about to any entity; the Writing Agent drafts Articles as origin_type agent.

#### Tag
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | short text | yes | Tag label |
| description | short text | no | Meaning note |

Keys: name unique case-insensitively. Relationships: tagging is an Edge of type tagged_with from any entity to Tag; Tags carry privacy_tier so that private taxonomies never leak into P0 responses.

#### Collection
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | short text | yes | Collection name |
| description | long text | no | Markdown purpose statement |
| collection_type | enum (manual, smart) | yes | Manual membership or rule-based |
| smart_rule | JSON document | no | Declarative filter for smart collections (entity types, tags, tiers, date ranges) |

Keys: name unique among non-deleted rows. Relationships: membership is an Edge of type member_of from the item to the Collection; smart collections materialize membership lazily at query time and never persist member Edges.

Source, Claim (§4.4) and Edge (§4.5) complete the knowledge entity set.

### 4.4 Provenance sub-model: Source, Claim, ClaimSource

This sub-model is the direct productization of MASTER_CONTEXT §0 and ADR-10. It is the only place confidence tiers are stored; every other surface derives tier display from here.

#### Source
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| source_type | enum (url, document, artifact, testimony, system_record, external_api) | yes | What kind of evidence this is |
| title | short text | yes | Human-readable label |
| url | short text | no | Public URL when the source is online |
| publisher | short text | no | Platform or issuer, for example GitHub, DEV.to, GDG Cape Town |
| accessed_at | timestamp | no | When the evidence was captured |
| archived_artifact_id | reference (Artifact) | no | Snapshot of the evidence, guarding against link rot |
| reliability_note | short text | no | Free-form caveat, for example single-source |

Keys: none natural; near-duplicate URLs are merged by the Verification Agent. Rule in words: a Source of type url should gain an archived_artifact_id within one ingestion cycle; unarchived URL sources are surfaced in the verification queue.

#### Claim
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| subject_type | short text | yes | Entity type name of the subject (from the canonical list) |
| subject_id | identifier | yes | The subject row |
| predicate | short text | yes | Machine-friendly relation name, for example presented_at, placed_third_at |
| statement | long text | yes | The atomic factual statement in plain language |
| confidence_tier | enum (verified, self_reported, flagged) | yes | Mirrors ✅, 🟡, 🔴 from MASTER_CONTEXT §0 |
| tier_rationale | short text | no | Why the tier is what it is |
| verified_at | timestamp | no | Set only when tier is verified |
| verified_by | reference (User) | no | The principal who performed verification (never a service principal, see rule below) |
| review_due_at | date | no | Optional re-verification reminder for perishable facts |

Keys: uniqueness in words: at most one non-deleted Claim per (subject_type, subject_id, predicate, statement) combination; duplicates are merged, never forked. Relationships: many-to-many with Source via ClaimSource; Edges reference a Claim for their provenance (§4.5).

#### ClaimSource (association)
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| claim_id | reference (Claim) | yes | The claim |
| source_id | reference (Source) | yes | The evidence |
| support_type | enum (supports, contradicts, mentions) | yes | How the source bears on the claim |
| note | short text | no | Reviewer annotation |

Keys: unique per (claim_id, source_id) pair. ClaimSource carries base fields except privacy_tier (it inherits the stricter of its claim's and source's tiers at read time, described in words, evaluated by the service layer).

**Never-auto-upgrade rule (data integrity constraint, stated in words).** The confidence_tier of a Claim may transition to `verified` only when all of the following hold: the acting principal is the owner or an owner-approved human verifier (never an agent or service principal), at least one ClaimSource row with support_type `supports` references a Source that is independent of the owner's own accounts, and the transition is recorded as an AuditLogEntry naming actor, prior tier, and evidence. Automated processes (ingestion, agents) may create Claims at `self_reported` or `flagged` and may downgrade any Claim to `flagged` (for example when a source disappears), but no automated path may raise a tier. Implementations must enforce this both in the service layer and as a database-level guard that rejects forbidden transitions; the guard's mechanics are an implementation detail, its behavior is normative here. Downstream display rule: any surface rendering a Claim below `verified` must use attributive voice, per MASTER_CONTEXT §0.

### 4.5 Edge

The single relationship table for the Postgres-native knowledge graph (ADR-05). Edge-type semantics, direction conventions, and the full taxonomy are owned by [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md); this document owns the storage shape.

| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| from_type | short text | yes | Entity type name of the origin |
| from_id | identifier | yes | Origin row |
| to_type | short text | yes | Entity type name of the target |
| to_id | identifier | yes | Target row |
| edge_type | short text | yes | Taxonomy value from KNOWLEDGE_GRAPH (for example collaborated_on, member_of, demonstrates, learned_from, tagged_with) |
| valid_from | partial date | no | When the relationship began, for temporal queries |
| valid_to | partial date | no | When it ended; null means ongoing |
| weight | decimal | no | Optional strength score used by retrieval ranking |
| claim_id | reference (Claim) | no | Provenance: the Claim asserting this relationship; required for owner-biographical edges, optional for structural edges like tagged_with |
| attributes | JSON document | no | Edge-type-specific qualifiers (for example role name on member_of) |

Keys: unique per (from_type, from_id, to_type, to_id, edge_type, valid_from) among non-deleted rows, so a relationship can recur across time without duplicating an open interval. Tier rule in words: an Edge is readable only when the caller clears the tier of the Edge row itself and of both endpoint rows; the Graph Service applies all three predicates inside traversal queries.

### 4.6 System entities

#### User
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| email | short text | yes | Login and contact address |
| display_name | short text | yes | Shown in UI and audit trails |
| auth_subject | short text | no | OIDC subject identifier once linked |
| user_kind | enum (human, service) | yes | Service rows represent agent and machine principals |
| account_status | enum (active, suspended, revoked) | yes | Lifecycle |
| is_owner | boolean | yes | Exactly one non-deleted row is true, stated as a uniqueness rule in words |
| last_login_at | timestamp | no | Observability |

Keys: email unique case-insensitively; auth_subject unique when present. No privacy_tier (see §4.2 exceptions).

#### Role
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| name | enum (owner, steward, trusted, public, service) | yes | Canonical roles per ADR-09 |
| description | short text | yes | Human meaning |
| max_privacy_tier | enum (P0, P1, P2, P3) | yes | The ceiling this role can ever reach; Grants may narrow, never widen |

Keys: name unique. Roles are a small, fixed reference table; new roles require a spec change.

#### Grant
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| user_id | reference (User) | yes | The grantee |
| role_id | reference (Role) | yes | The role granted |
| scope_type | enum (global, collection, entity) | yes | Breadth of the grant |
| scope_ref | entity reference | no | The Collection or entity when scope is narrowed |
| granted_by | reference (User) | yes | Almost always the owner |
| expires_at | timestamp | no | Time-bound access |
| activation_condition | JSON document | no | Declarative succession or time-lock condition (used for the estate steward and P3 unsealing; semantics in [SECURITY](../security/SECURITY.md)) |

Keys: unique per (user_id, role_id, scope_type, scope_ref) among non-deleted rows. Every Grant creation, change, and revocation is audited.

#### MemoryRecord
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| memory_type | enum (episodic, semantic, procedural, reflective) | yes | Canonical vocabulary from SPEC_CONVENTIONS §8 |
| content | long text | yes | The memory statement in Markdown |
| salience | decimal | yes | Retention score maintained by the Reflection Agent |
| source_refs | JSON document | no | Entity references this memory derives from (Conversations, JournalEntries, Events) |
| embedding | vector | yes | Semantic embedding of content; dimension bound to embedding_model_version |
| embedding_model_version | short text | yes | Model and version that produced the vector |
| last_accessed_at | timestamp | no | For decay scoring |
| access_count | integer | yes | For decay scoring, defaults zero |
| consolidated_from | JSON document | no | Ids of MemoryRecords merged into this one; merged rows are soft-deleted, never destroyed |
| expires_at | timestamp | no | Optional decay horizon for low-salience working residue |

Keys: none natural. Consolidation lineage rule in words: a consolidated record must reference all of its parents, and redacting any parent forces re-review of the child (FR-MEM group; algorithms in [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)).

#### EmbeddingChunk
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| entity_type | short text | yes | Type of the source entity |
| entity_id | identifier | yes | The source row |
| chunk_index | integer | yes | Position within the source's chunk sequence |
| chunk_text | long text | yes | The exact text embedded, retained for citation display and re-embedding |
| token_count | integer | yes | Size accounting |
| content_hash | short text | yes | Hash of chunk_text for cache-first re-embedding (cost control) |
| embedding | vector | yes | The embedding; conceptually a fixed-dimension array whose dimension is a property of the model version, never mixed within one index |
| embedding_model_version | short text | yes | Exact model and version |
| privacy_tier | enum (P0-P3) | yes | Denormalized copy of the parent entity's tier so tier predicates push into vector queries; recomputed synchronously whenever the parent tier changes |
| superseded_by | reference (EmbeddingChunk) | no | Set when re-chunking or re-embedding replaces this row |

Keys: unique per (entity_type, entity_id, chunk_index, embedding_model_version) among non-superseded rows. Rules in words: chunks are immutable (a text change creates successors and supersedes predecessors); when a parent row is redacted or hard-deleted, its chunks are hard-deleted in the same transaction, because embeddings can leak content.

#### AuditLogEntry
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| sequence_number | integer | yes | Monotonic, gap-tolerant ordering across the whole system |
| occurred_at | timestamp | yes | Event time |
| actor_type | enum (user, agent, system) | yes | Who acted |
| actor_id | identifier | yes | User id or AgentRun id |
| action | short text | yes | Verb from the audit taxonomy (create, update, soft_delete, redact, read_sensitive, generate, export, grant_change, tier_change, verify_claim, and so on; full taxonomy in [OBSERVABILITY](../deployment/OBSERVABILITY.md)) |
| subject_type | short text | no | Entity type acted on |
| subject_id | identifier | no | Entity row acted on |
| payload_summary | JSON document | no | Before/after digests, token counts, citation ids; never full P3 content |
| request_id | short text | no | Correlates to the API request |
| token_ref | short text | no | Hashed identifier of the PAT or session that authorized the action |

Keys: sequence_number unique. Append-only per ADR-11: no updates, no deletes, exceptions to base fields per §4.2. Tier note in words: audit entries about P3 subjects are themselves readable only by the owner (and steward after activation).

#### IngestionJob
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| job_type | enum (upload, github_sync, url_capture, conversation_import, bulk_import) | yes | Connector class |
| source_descriptor | JSON document | yes | Connector input (file manifest, repo name, URL) with secrets excluded |
| status | enum (queued, parsing, chunking, embedding, graph_extraction, review, complete, failed, cancelled) | yes | State machine; legal transitions are forward-only plus failed/cancelled from any active state |
| progress_percent | integer | no | Coarse progress for UI |
| error_detail | JSON document | no | Structured failure info on failed |
| items_created | JSON document | no | Counts by entity type on completion |

Keys: none. Relationships: rows created by the job carry origin_ref pointing back to it (§4.2), giving capture provenance for every ingested row.

#### AgentRun
| Column | Logical type | Required | Description |
|--------|--------------|----------|-------------|
| agent_name | enum (the 12 roster names from SPEC_CONVENTIONS §7) | yes | Which agent leads the run |
| task | long text | yes | The instruction given |
| status | enum (planned, awaiting_approval, running, paused, completed, failed, cancelled) | yes | Run state machine |
| plan | JSON document | no | Ordered steps with tool needs and cost estimates |
| current_step | integer | no | Progress pointer |
| budget_tokens | integer | yes | Hard token ceiling enforced by the Model Router |
| tokens_used | integer | yes | Metered actuals, defaults zero |
| cost_estimate | decimal | no | Currency estimate maintained by the Model Router |
| parent_run_id | reference (AgentRun) | no | Delegation chain for orchestrated sub-runs |
| result_summary | long text | no | Outcome in Markdown |

Keys: none. Relationships: every entity an agent creates carries origin_ref to the run; approvals and step transitions are AuditLogEntries, not separate tables, keeping one history.

### 4.7 Indexing strategy (conceptual, no SQL)

- **Primary access:** all tables are keyed on id; time-ordered ids keep inserts append-friendly.
- **Vector search:** approximate-nearest-neighbor indexes (HNSW-style as supported by pgvector) on EmbeddingChunk.embedding and MemoryRecord.embedding, one index per active embedding_model_version; queries always combine the ANN scan with predicates on privacy_tier (denormalized for this purpose), entity_type, and superseded_by being empty.
- **Lexical search:** full-text search indexes over title and body-bearing columns (Note.body, Article.body_markdown, Project.description, JournalEntry.body, Claim.statement, and peers), plus trigram-style fuzzy indexes on name columns (Person.full_name, Organization.name, Tag.name) for typo-tolerant lookup.
- **Timeline queries:** composite index over Event on (starts_at, event_type) and on date_precision for honest rendering; partial-date columns store a normalized sortable form alongside precision.
- **Graph traversal:** two composite indexes on Edge, (from_type, from_id, edge_type) and (to_type, to_id, edge_type), each including validity columns, so bounded-depth traversals and neighborhood queries resolve by index; the ADR-05 decision gate is measured against these.
- **Provenance joins:** Claim indexed on (subject_type, subject_id) and on confidence_tier; ClaimSource on both foreign keys.
- **Audit scale:** AuditLogEntry indexed on sequence_number and occurred_at with a block-range style index suited to append-only growth; actor and subject composites for investigations.
- **Uniqueness guards:** the case-insensitive and partial uniqueness rules stated per entity in §4.3-§4.6 are implemented as unique indexes filtered to non-deleted rows, described here in words only.

### 4.8 Data lifecycle

- **Soft delete.** Setting deleted_at hides a row from every default read path (API, retrieval, graph, export). Soft-deleted rows are retained for a 90-day undo window, then eligible for purge by a scheduled job, except entities referenced by Claims or audit entries, which are retained until redacted. Embeddings of soft-deleted parents are excluded from search immediately.
- **Redaction.** Redaction is the irreversible removal of content while preserving structure: content columns are replaced with a fixed tombstone marker, associated EmbeddingChunks are hard-deleted in the same transaction, Object Storage originals are deleted, and an AuditLogEntry records the redaction with a reason but never the removed content. The row id and its Edges survive as tombstones so history stays navigable. Redaction of a MemoryRecord parent triggers child re-review (§4.6).
- **Retention.** AuditLogEntry rows are retained indefinitely (ADR-11) with cold archival to Object Storage in vault-compatible form after a configurable horizon. Conversations default to indefinite retention at P2; the owner may set per-channel retention rules. IngestionJob and AgentRun operational rows are retained at least as long as any row whose origin_ref points to them.
- **Schema migration and versioning.** The schema carries an explicit schema_version recorded in a small metadata table (described, not defined). Migrations follow expand and contract: additive first (new columns nullable or defaulted), dual-read window, contraction only after the Vault export format and API have caught up. Enum expansion is additive; enum value removal requires a deprecation cycle mirroring the API policy. Every migration ships in the same release as its Vault format update (ADR-12 consequence) and a CHANGELOG entry.
- **Decades-scale format longevity.** Column types are restricted to widely portable forms (text, integers, decimals, timestamps, JSON, vectors); no proprietary extensions beyond pgvector, which is isolated behind the Retrieval Service seam (ADR-04). Canonical content is Markdown (ADR-13). An annual longevity drill restores the latest backup and opens the latest Vault bundle on a clean machine; failures are treated as release blockers (see [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)).

## 5. Acceptance Criteria

1. Every canonical entity in SPEC_CONVENTIONS §6 has a subsection here with columns, types, requiredness, keys in words, and relationship notes; no extra entities exist without a spec change.
2. Every content-bearing table carries the §4.2 base fields or a stated exception.
3. The never-auto-upgrade rule in §4.4 is stated as a constraint with actor, evidence, and audit conditions, and no other document contradicts it.
4. EmbeddingChunk supports tier-filtered vector search without joining to the parent at query time, and parent tier changes propagate synchronously.
5. Edge queries for neighborhood and bounded-depth traversal are index-served per §4.7.
6. Redaction, soft delete, and retention behaviors are defined such that no redacted content can survive in chunks, memory children, exports, or audit payloads.
7. The document contains no SQL and no em dashes.

## 6. Dependencies

- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md): ADR-03, ADR-04, ADR-05, ADR-10, ADR-11, ADR-12, ADR-13 shape this schema.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): edge-type taxonomy consumed by §4.5.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): consolidation and decay semantics behind MemoryRecord.
- [AUTHORIZATION](../security/AUTHORIZATION.md) and [PRIVACY](../security/PRIVACY.md): enforcement mechanics for tiers, Grants, and P3 unsealing.
- The FR-DATA group in `specs/` for behavioral requirements this schema serves.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Polymorphic entity references weaken referential integrity | Orphaned Claims or Edges | Service-layer validation plus periodic integrity job (§4.1); tombstone rules keep ids resolvable |
| Denormalized tier on EmbeddingChunk drifts from parent | Privacy leak in vector search | Synchronous recompute on tier change stated as normative; drift detector in QA suite |
| Embedding model migration invalidates vectors | Retrieval outage or double storage | Version-scoped indexes and superseded_by lineage allow side-by-side re-embedding |
| JSON document columns become schema hiding places | Unqueryable, unmigratable data | Each JSON column's shape is documented in its owning feature spec; new JSON columns require spec review |
| Audit volume from read_sensitive events | Cost and noise | Sensitive-read auditing scoped to P1-P3 reads; archival tiering (§4.8) |
| Enum churn across decades | Migration fatigue | Additive-first enum policy with deprecation cycle (§4.8) |

## 8. Future Enhancements

1. Dedicated graph store projection if the ADR-05 gate trips (Edge table becomes the source of a synchronized projection).
2. Partitioning of AuditLogEntry and EmbeddingChunk by time or model version when row counts warrant.
3. Field-level encryption for P3 content at rest beyond platform encryption (paired with [SECURITY](../security/SECURITY.md)).
4. Claim confidence sub-scores (source count, independence rating) beyond the three canonical tiers, without ever weakening the tier rules.
5. Content-defined chunking upgrades with full re-embedding lineage via superseded_by.

## 9. Examples

**Example: one verified fact at rest.** The Talk row "CyberBuddy at GDG Cape Town Pet Projects 2026" (P0) links via Edge presents to the Project row CyberBuddy, with claim_id pointing at a Claim: subject the Talk, predicate presented_at, statement "Linford presented CyberBuddy at GDG Cape Town Pet Projects on 30 June 2026", confidence_tier verified, one ClaimSource supporting row referencing a Source (source_type url, publisher GDG Cape Town, archived_artifact_id set). MASTER_CONTEXT §7 carries this as ✅.

**Example: a flagged achievement.** The Achievement row "SpazaLink 3rd place, SA Startup Week 2026" exists at P1 with a Claim at confidence_tier flagged (MASTER_CONTEXT §7 🔴) and tier_rationale "no independent source located". The API renders it only with attributive framing; the Verification Agent may attach a new Source and mark the ClaimSource supports, but only the owner's explicit verification action can raise the tier, which writes verified_at, verified_by, and an AuditLogEntry.

**Example: redaction cascade.** The owner redacts a JournalEntry (P3). In one transaction: body becomes the tombstone marker, its EmbeddingChunks are hard-deleted, a reflective MemoryRecord consolidated from it is queued for re-review, and an AuditLogEntry (action redact) records the event without content. A later Vault export contains the tombstone, not the text.

## 10. Open Questions

- Should smart Collection rules (§4.3) be restricted to a closed filter grammar in v1 to keep exports interpretable offline?
- Do we store a normalized sortable form for every partial date column, or compute it at query time? Leaning stored, pending FR-TL group performance targets.
- Is a 90-day soft-delete undo window right for a single-owner system, or should JournalEntry get a longer window?
> TODO(verify): Confirm pgvector index type availability (HNSW support) on the chosen Supabase plan, per the 🟡 stack claim in MASTER_CONTEXT §5.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier definitions and the downstream-AI rule this schema enforces), §5, §7.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §5 (privacy tiers), §6 (canonical entities), §8 (memory vocabulary).
- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) §4.7 (ADRs cited throughout).

## 12. Related Specifications

- [API_SPECIFICATION](../api/API_SPECIFICATION.md): the contract through which every table here is read and written.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): Edge semantics.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): MemoryRecord behavior.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md): EmbeddingChunk production and consumption.
- [PRIVACY](../security/PRIVACY.md), [AUTHORIZATION](../security/AUTHORIZATION.md): tier and grant enforcement.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): lifecycle drills in §4.8.
