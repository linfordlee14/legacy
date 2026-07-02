# KNOWLEDGE_GRAPH
### The Legacy knowledge graph: node and edge taxonomies, provenance, temporal model, construction pipeline, storage, and query patterns

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](MASTER_CONTEXT.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) |

---

## 1. Purpose

The knowledge graph is the connective tissue of Legacy. Documents, embeddings, and memories answer "what did Linford write or say"; the graph answers "how does everything relate": which person collaborated on which project, which talk presented which project at which event, which claim is supported by which source. This specification defines the graph model (typed nodes, typed directed temporal edges), the complete node and edge taxonomies, provenance and confidence-tier propagation, the construction pipeline operated by the Graph Agent, the storage mapping onto PostgreSQL, and the query patterns the rest of the system depends on.

This document is the authoritative definition of relationship semantics for the repository, as designated in [SPEC_CONVENTIONS §6](../docs/SPEC_CONVENTIONS.md). Attribute-level entity definitions live in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md).

## 2. Goals

1. Represent every knowledge domain of a whole professional and personal life (biography through future plans, see §4.2) as typed nodes with zero loss into free text.
2. Make every node and every edge carry provenance: at least one `Claim` or `Source` link and a confidence tier that is never silently upgraded.
3. Model time as a first-class dimension so the Timeline Agent and timeline engine can be driven directly from the graph.
4. Keep the v1 graph inside PostgreSQL (node and edge tables per the baseline architecture) while defining an explicit decision gate for a dedicated graph database.
5. Support the query patterns needed by the Retrieval Agent, Twin Agent, and Mentor Agent: neighborhood expansion, typed traversals, path finding, and temporal filtering.
6. Keep the graph auditable: every mutation is attributable to an agent run or a human action and is reversible.

## 3. Scope

### In scope

- Graph data model: node types, the `Edge` entity, attributes required on both.
- Node taxonomy with full knowledge-domain coverage and mapping to canonical entities.
- Edge type taxonomy with domain, range, and semantics for each type.
- Provenance, confidence tiers, and privacy tiers on graph elements.
- Temporal modeling (validity intervals, point events, durations).
- Graph construction pipeline: extraction, entity resolution, deduplication, human confirmation.
- Storage mapping to PostgreSQL and the graph-database decision gate.
- Query patterns, quality metrics, versioning, and audit.

### Out of scope

- Physical schema (column types, indexes): [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md).
- Embedding and chunking of node content: [RAG_PIPELINE](../ai/RAG_PIPELINE.md).
- Agent tooling and orchestration details: [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md).
- Timeline rendering and chronology heuristics: the timeline engine specification (TL domain).
- Visualization UI: [UI_UX](../ui/UI_UX.md).

## 4. Requirements

Requirement IDs below (`KG-##`) are local to this document. Product-level traceability to these requirements lives in the FR-KG group of [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md).

### 4.1 Graph model

- **KG-01** The graph consists of nodes, which are instances of the canonical knowledge entities in [SPEC_CONVENTIONS §6](../docs/SPEC_CONVENTIONS.md), and edges, which are instances of the canonical `Edge` entity.
- **KG-02** Every edge is typed (one type from §4.3), directed (a `from` node and a `to` node), and temporal (carries the validity attributes of §4.4). Symmetric relationships (for example `collaborated_with`) are stored once with a documented canonical ordering rule and treated as bidirectional at query time.
- **KG-03** Edges MAY carry a small attribute map (for example `role: "CTO"` on a `works_at` edge) but MUST NOT smuggle in entity-grade data; anything with independent identity becomes a node.
- **KG-04** Every node and every edge carries: a stable identifier, a privacy tier (P0 to P3, default P2), a confidence tier (`verified`, `self_reported`, `flagged`), provenance links (§4.4), and audit fields (created/updated by which `AgentRun` or user, when).
- **KG-05** Multiple edges of the same type between the same pair of nodes are permitted only when their validity intervals differ (for example two separate periods of `works_at`).

### 4.2 Node taxonomy and knowledge-domain coverage

The graph MUST cover every knowledge domain below. Domains do not introduce new entity types; they map onto the canonical entities, often distinguished by a `kind` attribute defined in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md).

| # | Knowledge domain | Canonical entity | Notes |
|---|------------------|------------------|-------|
| 1 | Biography | `Person` plus `Claim` | Biographical facts are Claims attached to the Person node, each with a tier per [MASTER_CONTEXT §0](MASTER_CONTEXT.md) |
| 2 | Timeline | `Event` | Point or duration events, ordered via `precedes` and timestamps |
| 3 | Projects | `Project` | For example CyberBuddy, WildGuard AI (✅ per MASTER_CONTEXT §6) |
| 4 | GitHub repositories | `Artifact` (kind: code_snapshot) | Linked to its `Project` via `part_of`; repo URL is a `Source` |
| 5 | Articles | `Article` | For example DEV.to writing (✅) |
| 6 | Talks | `Talk` | Linked to `Event` via `presented_at` |
| 7 | Research | `Artifact` (kind: research_note) or `Note` | Research outputs; external references become `Source` nodes |
| 8 | Hackathons | `Event` (kind: hackathon) | Participation via `participated_in` |
| 9 | Certifications | `Certification` | Attests skills via `attests` |
| 10 | Skills | `Skill` | Includes technologies; demonstrated vs claimed is expressed by edge tier |
| 11 | Companies | `Organization` (kind: company) | For example Linfy Tech Solutions (✅) |
| 12 | Leadership roles | `Edge` (`works_at` with role attributes) plus `Claim` | Roles are relationships, not entities; tier per MASTER_CONTEXT §4 |
| 13 | Ideas | `Idea` | Origination captured with `derived_from` and `inspired_by` |
| 14 | Design decisions | `Note` (kind: decision) | Links to affected `Project` or `Artifact` via `documents` |
| 15 | AI conversations | `Conversation` | High-volume source of `mentions` and `derived_from` edges |
| 16 | Source documents | `Source` and `Artifact` (kind: document) | `Source` is the provenance anchor; the file itself is an `Artifact` |
| 17 | Photos | `Artifact` (kind: photo) | Media stored per DATABASE_SCHEMA storage rules |
| 18 | Videos | `Artifact` (kind: video) | Same |
| 19 | Presentations | `Artifact` (kind: presentation) | Usually `part_of` a `Talk` |
| 20 | Architecture documents | `Artifact` (kind: architecture_doc) | `documents` a `Project` |
| 21 | Specifications | `Artifact` (kind: specification) | SDD artifacts (mission, roadmap, techstack files) |
| 22 | Personal notes | `Note` | Default P2 |
| 23 | Journal entries | `JournalEntry` | Default P2, elevatable to P3 |
| 24 | Prayer reflections | `JournalEntry` (kind: prayer_reflection) | P3 by default, sealed per [PRIVACY](../security/PRIVACY.md) |
| 25 | Goals | `Goal` | Pursued via `pursues`, aimed via `targets` |
| 26 | Roadmaps | `Collection` (kind: roadmap) of `Goal` and `Project` | Ordered membership via `part_of` |
| 27 | Lessons learned | `Lesson` | Often produced by the Reflection Agent |
| 28 | Books | `Book` | Reading history via `learned_from` |
| 29 | Learning history | `Certification`, `Event` (kind: course), `learned_from` edges | Courses and programs, for example ALX Africa (✅) |
| 30 | Networking | `Person` plus `knows` edges | Named collaborators in MASTER_CONTEXT §10 are 🟡 |
| 31 | Mentors | `Person` plus `mentored_by` edges | Direction: mentee to mentor |
| 32 | Collaborators | `Person` plus `collaborated_with` edges | Symmetric, stored once |
| 33 | Achievements | `Achievement` | Tier discipline is critical here (MASTER_CONTEXT §7 has 🔴 items) |
| 34 | Failures | `Lesson` (kind: failure) linked to the `Event` or `Project` | Failures are first-class learning inputs, never hidden |
| 35 | Future plans | `Goal` (horizon attribute) | Long-term vision items from MASTER_CONTEXT §11 |

- **KG-06** Every ingested item MUST resolve to at least one node in this taxonomy; items that cannot be classified are parked in a triage `Collection` and surfaced to the owner, never dropped.

### 4.3 Edge type taxonomy

- **KG-07** Edge types are a closed, versioned vocabulary. Adding a type requires a change to this specification. The v1 vocabulary is:

| Edge type | Domain (from) | Range (to) | Semantics | Temporality |
|-----------|---------------|------------|-----------|-------------|
| `founded` | Person | Organization | Subject founded the organization | Point (valid_from) |
| `works_at` | Person | Organization | Employment or formal role; role name and title in attributes | Duration |
| `member_of` | Person | Organization, Collection | Community, program, or group membership | Duration |
| `worked_on` | Person | Project | Sustained, substantive contribution | Duration |
| `contributed_to` | Person | Project, Artifact, Organization | Discrete, bounded contribution | Point or duration |
| `authored` | Person | Article, Book, Note, Talk, Artifact, Idea | Authorship or origination | Point |
| `presented_at` | Talk, Project | Event | Delivered or showcased at an event | Point |
| `participated_in` | Person | Event | Attendance, competition, or program participation | Point or duration |
| `organized` | Person | Event | Organizer or host role | Point or duration |
| `mentored_by` | Person | Person | Mentee to mentor relationship | Duration |
| `collaborated_with` | Person | Person | Peer collaboration; symmetric, stored once | Duration |
| `knows` | Person | Person | Networking connection weaker than collaboration | Duration |
| `derived_from` | Idea, Note, Artifact, Lesson, Article, MemoryRecord subject | Any node | Content produced directly from another item | Point |
| `inspired_by` | Project, Idea, Artifact | Any node | Creative influence, weaker than `derived_from` | Point |
| `cites` | Article, Artifact, Note, Claim | Source, Artifact | Explicit citation | Atemporal |
| `supports` | Source, Claim | Claim | Evidence in favor of a claim | Atemporal |
| `contradicts` | Source, Claim | Claim | Evidence against a claim; feeds the verification queue | Atemporal |
| `verified_by` | Claim | Source | The verification link that justifies a `verified` tier | Point (verified_at) |
| `tagged_with` | Any node | Tag | Classification and faceting | Atemporal |
| `part_of` | Any node | Collection, Project, Organization, Event | Composition and hierarchy | Duration |
| `precedes` | Event | Event | Chronological ordering for the timeline engine | Atemporal (derived) |
| `located_in` | Person, Organization, Event | Tag (kind: place) | Physical or host location; see Open Questions on a Place entity | Duration |
| `learned_from` | Person, Lesson, Skill | Book, Person, Event, Conversation, Project | Learning provenance | Point |
| `achieved` | Person | Achievement | Attainment of a recognition | Point |
| `achieved_at` | Achievement | Event, Organization | Context where the achievement occurred | Point |
| `holds` | Person | Certification | Certification attainment; expiry in valid_to | Duration |
| `attests` | Certification | Skill | Certification evidences a skill | Atemporal |
| `demonstrates` | Project, Artifact, Talk | Skill | Work product evidences a skill | Atemporal |
| `has_skill` | Person | Skill | Competency; tier distinguishes demonstrated (✅) from claimed (🟡) | Duration |
| `uses` | Project, Artifact | Skill, Artifact | Technology or component usage | Duration |
| `documents` | Artifact, Note | Project, Event, Idea, Organization | Documentation relationship | Atemporal |
| `mentions` | Conversation, Note, JournalEntry, Article, Artifact | Any node | Weak extracted reference; high volume, low weight | Point |
| `reflects_on` | JournalEntry, Lesson, Conversation | Event, Project, Goal | Reflective content about a subject | Point |
| `pursues` | Person | Goal | Active pursuit of a goal | Duration |
| `targets` | Goal | Project, Skill, Achievement, Organization | What the goal aims at | Duration |
| `supersedes` | Artifact, Goal, Idea | Same entity type | Versioning lineage between revisions | Point |

- **KG-08** Domain and range are validated at write time. An edge whose endpoints violate the table is rejected and returned to the proposing agent with a machine-readable reason.
- **KG-09** `mentions` edges are quarantined at a lower query weight than curated edges and are eligible for archival if never promoted (see quality metrics, §4.9).

### 4.4 Provenance and confidence

- **KG-10** Every node and edge MUST link to at least one `Claim`, and every `Claim` to at least one `Source`, per the provenance model in [SPEC_CONVENTIONS §6](../docs/SPEC_CONVENTIONS.md). Graph elements created by inference (for example a derived `precedes` edge) link to a synthetic `Source` describing the inference and the `AgentRun` that produced it.
- **KG-11** Confidence tiers on graph elements mirror [MASTER_CONTEXT §0](MASTER_CONTEXT.md): `verified` (✅), `self_reported` (🟡), `flagged` (🔴). A derived element's tier is the minimum tier of its inputs.
- **KG-12** No agent may upgrade a tier. Only the Verification Agent may propose an upgrade, with new `Source` evidence, and the owner must approve it (see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), safety rails). Downgrades on new contradicting evidence are proposed the same way but flagged as urgent.
- **KG-13** Elements referencing the named collaborators of MASTER_CONTEXT §10 carry `self_reported` until independent sources are attached; this includes all example content in Legacy itself.

### 4.5 Temporal modeling

- **KG-14** Edges carry `valid_from` and `valid_to` (nullable ISO 8601 timestamps): both set means a duration, only `valid_from` means ongoing or a point (disambiguated by an `is_instant` flag), both null means atemporal per the taxonomy table.
- **KG-15** `Event` nodes carry `starts_at` and `ends_at`; a point event sets `ends_at` equal to `starts_at`. Partial dates (year only, month only) are stored with an explicit precision attribute rather than fabricated day-level precision.
- **KG-16** All graph elements additionally carry `recorded_at` (when Legacy learned it), which is distinct from validity. Queries default to "currently valid" semantics; historical "as of" queries are supported by filtering on both axes.
- **KG-17** The Timeline Agent derives `precedes` edges from timestamps; hand-asserted `precedes` edges (for undated events) take precedence and are marked as asserted.

### 4.6 Construction pipeline

The Graph Agent (see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)) owns graph construction. Pipeline stages:

```
Ingested content (chunks, per RAG_PIPELINE)
      |
      v
[1] Candidate extraction      -> candidate nodes + candidate edges + spans
      |
      v
[2] Entity resolution         -> match candidates against existing nodes
      |                          (blocking by type, then similarity scoring)
      +--> score >= 0.92: auto-merge, logged, reversible
      +--> 0.75 <= score < 0.92: human confirmation queue
      +--> score < 0.75: create new node
      |
      v
[3] Edge validation           -> domain/range check (KG-08), tier assignment (KG-11)
      |
      v
[4] Provenance binding        -> Claim + Source links (KG-10)
      |
      v
[5] Commit + audit            -> AuditLogEntry per mutation, AgentRun trace
```

- **KG-18** Entity resolution scores combine normalized name similarity, type compatibility, attribute overlap, and shared-neighborhood evidence. Thresholds above are v1 defaults and are tunable configuration, recorded per decision in the audit log.
- **KG-19** Auto-merges below the human-confirmation threshold are forbidden. The confirmation queue presents both candidates, their provenance, and the score breakdown; the owner (or a P1 delegate with an explicit `Grant`) approves, rejects, or edits.
- **KG-20** Every merge records a reversible mapping (losing node id, surviving node id, edge rewires) so an incorrect merge can be split without data loss.
- **KG-21** Alias discipline follows MASTER_CONTEXT §1: handles `linfordlee14` and `hacker1401` resolve to the owner Person node (✅); the "Linford Lee" alias remains a 🟡 alias attribute and MUST NOT cause automatic attribution of look-alike content.

### 4.7 Storage mapping

- **KG-22** v1 stores the graph natively in PostgreSQL per [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): one table per canonical entity for nodes, and a single `Edge` table holding type, endpoints (polymorphic id plus entity type), attributes, temporal fields, tier, and provenance references.
- **KG-23** Traversal is served through recursive queries and materialized adjacency views for hot patterns (owner-centric neighborhoods, event chronology). The specific mechanisms are defined in DATABASE_SCHEMA; this spec constrains only observable behavior (§4.8, §5).
- **KG-24** Decision gate for a dedicated graph database (Neo4j-class or similar). Re-evaluate when any of the following holds for 30 consecutive days: edge count above 5 million, p95 latency above 500 ms for depth-3 traversals, or a product need for graph algorithms (community detection, centrality) beyond SQL practicality. The evaluation is recorded as an ADR in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md). Until then, portability is preserved by keeping all graph semantics in this spec, not in database features.

### 4.8 Query patterns

- **KG-25** The graph MUST answer at least these pattern families, exposed to agents via the internal API (API domain) and to users via natural-language search (SRCH domain):

| Pattern | Description | Example (natural language) |
|---------|-------------|----------------------------|
| Neighborhood | All edges of a node, filtered by type, tier, tier floor, time | "Everything connected to CyberBuddy" |
| Typed traversal | Fixed-shape multi-hop walk | "All projects presented at GDG Cape Town events" |
| Path finding | Shortest or all simple paths between two nodes, bounded depth | "How is a given mentor connected to RhinoShield?" |
| Temporal slice | Graph as of a date, or activity within a range | "What was Linford working on in June 2026?" |
| Provenance walk | From any element down to its Claims and Sources | "Why does Legacy believe Linford is CTO of NeuroGrowth Labs?" |
| Aggregation | Counts and rollups over typed edges | "Talks per year", "skills demonstrated by more than two projects" |

- **KG-26** Every query result carries, per element, its confidence tier and privacy tier; the API layer filters by the caller's `Grant` before results leave the datastore boundary.
- **KG-27** Traversal depth is capped (default 6) and every query is budgeted, so a malformed agent query cannot exhaust the datastore.

### 4.9 Quality metrics

- **KG-28** The following metrics are computed on a schedule and exposed via [OBSERVABILITY](../deployment/OBSERVABILITY.md):

| Metric | Definition | v1 target |
|--------|------------|-----------|
| Orphan rate | Nodes with zero curated edges (excluding `mentions` and `tagged_with`) / total nodes | Below 5 percent |
| Resolution precision | Sampled auto-merges judged correct on human review | Above 98 percent |
| Resolution recall | Sampled known duplicates actually merged or queued | Above 90 percent |
| Provenance coverage | Elements with at least one Claim-Source chain / total | 100 percent (hard invariant) |
| Dangling edge count | Edges whose endpoint was archived without rewire | 0 (hard invariant) |
| Tier distribution drift | Week-over-week change in ✅/🟡/🔴 proportions | Monitored, alert on anomaly |
| Confirmation queue age | Oldest unresolved merge candidate | Below 14 days |

### 4.10 Versioning and audit

- **KG-29** Graph mutations (create, update, merge, split, archive) are append-only events in `AuditLogEntry`, each linked to the responsible `AgentRun` or user action. Nothing is hard-deleted; archival removes elements from default query scope while preserving history, consistent with [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md) archival policy.
- **KG-30** Node and edge records are versioned: an update writes a new version and links it via `supersedes` semantics at the storage layer. "As recorded on date X" reconstruction MUST be possible for any element.
- **KG-31** The edge-type vocabulary itself is versioned in this document's changelog; migrations that retype existing edges are executed as auditable batch jobs with dry-run reports.

## 5. Acceptance Criteria

1. Given the ✅ facts of MASTER_CONTEXT §1 to §9, the construction pipeline produces a graph containing at least the subgraph of Example 9.1 with matching types, edges, and tiers.
2. Creating an edge with endpoints violating the §4.3 domain/range table is rejected with a machine-readable error.
3. No write path exists that raises a confidence tier without a Verification Agent proposal plus owner approval; attempting it via any agent tool fails and is audited.
4. An entity-resolution candidate scoring 0.85 appears in the human confirmation queue and is not merged automatically.
5. A merge approved in the queue is reversible: splitting restores both original nodes and rewires edges, verified by an audit-log replay test.
6. The query "all projects presented at GDG Cape Town events" (Example 9.2) returns CyberBuddy with its ✅ tier and the supporting provenance chain.
7. A P3-tier node (for example a prayer reflection) never appears in any query result for callers without the sealing release condition satisfied, including agent-issued queries.
8. Provenance coverage measures 100 percent on a full scan; any element failing the invariant blocks the pipeline run that produced it.
9. Temporal queries distinguish "currently valid" from "as of 2026-06-30" and return different results when history differs.
10. All quality metrics of §4.9 are emitted to the observability stack with the defined definitions.

## 6. Dependencies

- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): physical node and edge tables, attribute definitions, storage of media and sources.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): Graph Agent, Verification Agent, Timeline Agent responsibilities and safety rails.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md): chunked content that feeds candidate extraction; graph context injected into retrieval.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): memories reference graph nodes; consolidation may propose new edges.
- [PRIVACY](../security/PRIVACY.md) and [AUTHORIZATION](../security/AUTHORIZATION.md): privacy tiers and Grant-based filtering.
- [MASTER_CONTEXT](MASTER_CONTEXT.md): seed facts and the tier system the graph productizes.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-merging distinct people or projects | Corrupted biography, wrong attributions | Conservative thresholds, human queue, reversible merges (KG-19, KG-20) |
| Under-merging creates duplicate hubs | Fragmented answers, poor retrieval | Recall metric, periodic dedup sweeps by the Curation Agent |
| Tier erosion (🟡 treated as fact downstream) | Legacy asserts unverified claims | Tier carried on every element and every query result (KG-26), twin-layer attribution rules |
| `mentions` edge explosion from conversations | Noise drowns curated structure | Weighting and archival policy (KG-09) |
| Postgres traversal performance ceiling | Slow multi-hop queries | Materialized views, depth caps, decision gate (KG-24) |
| Look-alike handle content wrongly attributed | False biography | Alias discipline (KG-21), attribution rules from MASTER_CONTEXT §1 |
| Temporal fabrication (fake day precision) | Wrong timeline | Precision attribute (KG-15) |

## 8. Future Enhancements

1. Dedicated graph database migration if the KG-24 gate triggers, with a dual-write validation period.
2. Graph algorithms layer: centrality to surface under-documented but highly connected entities, community detection for era or theme clustering.
3. First-class `Place` entity replacing place-kind Tags (see Open Questions).
4. Confidence-weighted path ranking (paths through ✅ edges rank above 🟡 paths).
5. Public subgraph export: a P0-only, provenance-preserving graph view for the public portfolio site.
6. Contradiction surfacing dashboards built on `contradicts` edges and the verification queue.
7. Graph-native embeddings (node2vec-class) as an additional retrieval signal, gated by measured retrieval lift.

## 9. Examples

### 9.1 Illustrative subgraph (✅ facts only, from MASTER_CONTEXT)

Nodes:

| Node id (illustrative) | Entity | Label | Tier |
|------------------------|--------|-------|------|
| person_linford | Person | Linford Musiyambodza | ✅ |
| org_linfytech | Organization (company) | Linfy Tech Solutions | ✅ |
| org_neurogrowth | Organization (company) | NeuroGrowth Labs | ✅ |
| org_gdgct | Organization (community) | GDG Cape Town | ✅ |
| proj_cyberbuddy | Project | CyberBuddy | ✅ |
| proj_wildguard | Project | WildGuard AI | ✅ |
| event_petprojects2026 | Event (meetup) | Pet Projects: The 2026 Edition (2026-06-30) | ✅ |
| talk_cyberbuddy | Talk | CyberBuddy presentation | ✅ |
| skill_python | Skill | Python | ✅ |
| org_alx | Organization (education) | ALX Africa | ✅ |

Edges:

| From | Type | To | Tier | Temporal notes |
|------|------|----|------|----------------|
| person_linford | founded | org_linfytech | ✅ | valid_from unknown, precision: unknown, TODO(verify): founding date |
| person_linford | works_at (role: CTO) | org_neurogrowth | ✅ | ongoing per research pass |
| person_linford | member_of | org_gdgct | ✅ | ongoing |
| person_linford | worked_on | proj_cyberbuddy | ✅ | ongoing |
| person_linford | worked_on | proj_wildguard | ✅ | ongoing |
| talk_cyberbuddy | presented_at | event_petprojects2026 | ✅ | point, 2026-06-30 |
| talk_cyberbuddy | documents | proj_cyberbuddy | ✅ | atemporal |
| person_linford | authored | talk_cyberbuddy | ✅ | point |
| person_linford | has_skill | skill_python | ✅ | demonstrated via public repos |
| person_linford | learned_from | org_alx | ✅ | Data Science and Cybersecurity tracks |

Every row above traces to a `Claim` with `verified` tier and a `Source` naming the platform found in the research pass (GitHub, GDG Cape Town event page, DEV.to), per MASTER_CONTEXT §13. Named collaborators (MASTER_CONTEXT §10) are deliberately absent from this example because they are 🟡; if added, their nodes and edges carry `self_reported`.

### 9.2 Worked query examples

**Query A: "All projects presented at GDG Cape Town events."**
Traversal: start at `org_gdgct`, follow incoming `part_of` from Event nodes (events hosted by the community), then incoming `presented_at` from Talk or Project nodes, then for Talks follow `documents` to Project. Filter: none on tier, but each result row carries its tier. Result against 9.1: CyberBuddy (✅), via event_petprojects2026 and talk_cyberbuddy, with the full provenance chain attached.

**Query B: "Path between a mentor and a project."**
Traversal: bounded shortest path (depth cap 6) between a Person node reached via `mentored_by` and the target Project node, restricted to curated edge types (excluding `mentions`). The response lists each hop with edge type and tier so the reader can judge the strength of the connection. Note: no mentor relationship is ✅ in MASTER_CONTEXT today, so any live answer would surface 🟡 edges and say so.

**Query C: "What was Linford working on in June 2026?"**
Traversal: from person_linford, `worked_on` and `contributed_to` edges where the validity interval overlaps 2026-06-01 to 2026-06-30, plus Events in that window via `participated_in`. Against 9.1 this returns CyberBuddy, WildGuard AI, and the Pet Projects event.

### 9.3 Edge record example (illustrative JSON)

```json
{
  "id": "edge_01J...",
  "type": "presented_at",
  "from": { "entity": "Talk", "id": "talk_cyberbuddy" },
  "to": { "entity": "Event", "id": "event_petprojects2026" },
  "attributes": { "format": "community talk" },
  "valid_from": "2026-06-30",
  "valid_to": "2026-06-30",
  "is_instant": true,
  "confidence_tier": "verified",
  "privacy_tier": "P0",
  "claims": ["claim_gdg_petprojects_talk"],
  "recorded_at": "2026-07-01T09:12:00Z",
  "created_by": { "agent_run": "run_graph_01J..." }
}
```

## 10. Open Questions

- > TODO(verify): Should `Place` become a first-class canonical entity instead of place-kind Tags? Needs a decision in DATABASE_SCHEMA and SPEC_CONVENTIONS §6 before promotion.
- > TODO(verify): Exact founding date of Linfy Tech Solutions for the `founded` edge validity; source expected from the owner's records or a registry listing.
- > TODO(design): Whether inverse edge names (for example `mentors` as the inverse of `mentored_by`) are materialized or purely computed at query time.
- > TODO(design): Final entity-resolution similarity feature set and whether embedding similarity of node descriptions joins the v1 scorer.
- > TODO(design): Whether `mentions` edges should expire to archive automatically after a fixed period without promotion, and the period.
- > TODO(verify): Which of the 🟡 portfolio projects in MASTER_CONTEXT §6 get graph nodes at seed time versus only after a repo or demo URL is attached (MASTER_CONTEXT §12 item 5).

## 11. References

- [MASTER_CONTEXT](MASTER_CONTEXT.md): §0 tiers, §1 identity and aliases, §6 projects, §10 people, §12 verification queue, §13 source preservation.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): §5 privacy tiers, §6 canonical entities and provenance model, §9 baseline architecture defaults.
- General background: property-graph modeling and temporal graph literature informed the validity-interval design; no external standard is normative here.

## 12. Related Specifications

- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md)
- [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md)
- [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (the FR-KG group)
- [PRIVACY](../security/PRIVACY.md), [AUTHORIZATION](../security/AUTHORIZATION.md)
- [OBSERVABILITY](../deployment/OBSERVABILITY.md)
