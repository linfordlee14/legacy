# FEATURE_SPECIFICATIONS
### Detailed specifications for the sixteen core features of the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md), [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md), [USER_PERSONAS](USER_PERSONAS.md), [USE_CASES](USE_CASES.md) |

---

## 1. Purpose

This document specifies each of the sixteen canonical features (F1 through F16) as an implementable unit: FS-001 through FS-016, one per feature. Each feature specification describes behavior, key scenarios, edge cases, data touched, agents involved, privacy-tier behavior, and success metrics, at the level of detail an implementation session needs to build the feature without redesigning it.

## 2. Goals

- Give every feature a stable identity (FS ID) that tasks in [TASKS](../roadmap/TASKS.md) and phases in [ROADMAP](../roadmap/ROADMAP.md) can reference.
- Bind each feature to its functional requirement groups (by domain code), its personas, and its data entities.
- Make edge cases and privacy behavior explicit, because that is where a legacy platform earns or loses trust.

## 3. Scope

**In scope:** the sixteen features F1 through F16 as defined in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) usage across this repository.

**Out of scope:** post-v1 candidates (see [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)), UI layout detail (see [UI_UX](../ui/UI_UX.md)), and API shapes (see [API_SPECIFICATION](../api/API_SPECIFICATION.md)).

## 4. Requirements

### FS-001 · F1 Capture and Ingestion

- **Overview.** Every knowledge domain listed in MASTER_CONTEXT enters Legacy through one pipeline: documents, photos, videos, presentations, code repositories, AI conversations, notes, and voice memos.
- **Behavior.** Uploads and connected sources create an `IngestionJob`. The Ingestion Agent parses format-appropriately (text extraction, OCR for images, transcription for audio and video, repository crawling for GitHub projects), normalizes to canonical entities plus `Artifact` records, chunks content for embedding, and hands off to the Curation Agent for tagging and deduplication. Every ingested item receives a privacy tier (default P2), provenance metadata, and a link to its original file, which is preserved unmodified.
- **Key scenarios.** Batch document upload; connect the `linfordlee14` GitHub account and ingest repositories; paste an AI conversation transcript; record a voice note that becomes a transcribed `Note`.
- **Edge cases.** Duplicate uploads (deduplicate by content hash, keep both references); unparseable files (job completes with a review flag, original preserved); mixed-language content; oversized media (size ceiling with clear error); partially failed batches (per-item status, resumable).
- **Data.** `IngestionJob`, `Artifact`, `Note`, `Conversation`, `EmbeddingChunk`, `Source`.
- **Agents.** Ingestion Agent, Curation Agent.
- **Privacy.** Everything lands at P2 unless the owner sets otherwise at capture time. Nothing auto-publishes.
- **Requirements group.** FR-ING, FR-DATA. **Metrics.** Time-to-searchable (NFR-005), ingestion success rate, review-flag rate.

### FS-002 · F2 Knowledge Graph and Entity Linking

- **Overview.** A typed, directed, temporal graph connects every entity in the corpus, per [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md).
- **Behavior.** The Graph Agent extracts entities and relationships from ingested content, resolves them against existing nodes (with confidence thresholds), and proposes low-confidence merges to the owner instead of applying them. Every node and edge carries provenance (Claim and Source links plus confidence tier).
- **Key scenarios.** Ingesting a talk description links `Talk` → presented_at → `Event` (GDG Cape Town) → part_of → `Organization`; browsing a project shows its people, artifacts, events, and lessons.
- **Edge cases.** Ambiguous person names (never auto-merge across the attribution rules in MASTER_CONTEXT §1); conflicting relationship claims (both stored, flagged to verification); entity deletion with dependent edges (soft delete plus orphan review).
- **Data.** All knowledge entities, `Edge`, `Claim`, `Source`.
- **Agents.** Graph Agent, Verification Agent, Curation Agent.
- **Privacy.** Edges inherit the more restrictive tier of their endpoints. Graph queries filter by caller ceiling before traversal results return.
- **Requirements group.** FR-KG, FR-VER. **Metrics.** Entity resolution precision, orphan rate, proposal acceptance rate.

### FS-003 · F3 Timeline Engine

- **Overview.** A chronological spine of the owner's life and work: events, durations, and milestones, browsable and queryable.
- **Behavior.** The Timeline Agent extracts dated events from ingested content, normalizes partial dates (year-only, month-only), links events to graph entities, and maintains ordering. The timeline explorer renders eras, filters by domain (projects, talks, education), and answers range queries.
- **Key scenarios.** "Show 2026" returns the GDG Cape Town Pet Projects talk (30 June 2026, ✅) alongside other dated items with their tiers; zooming from decade to day.
- **Edge cases.** Unknown dates (undated shelf, never fabricated); conflicting dates for one event (both recorded, verification flag); retroactive corrections (audit-logged revisions).
- **Data.** `Event`, `Edge`, `Claim`.
- **Agents.** Timeline Agent, Verification Agent.
- **Privacy.** Timeline views assemble only items at or below the caller's ceiling; the public timeline shows P0 highlights only.
- **Requirements group.** FR-TL. **Metrics.** Dated-item coverage, date accuracy on sampled audit.

### FS-004 · F4 Search

- **Overview.** Lexical, semantic, and hybrid search plus natural-language querying over the entire accessible corpus.
- **Behavior.** Queries run against the lexical index and pgvector embeddings; hybrid ranking merges results. Natural-language queries are interpreted by the Retrieval Agent into structured search (entities, date ranges, types) with the interpretation shown to the user. Results always display provenance tier and privacy tier.
- **Key scenarios.** "hackathon projects using YOLOv5" (hybrid); "what did I present at GDG?" (natural language resolving to Talk entities); filter-by-entity from a graph node.
- **Edge cases.** Zero results (suggest broader scopes, never fabricate); query terms matching sealed content (P3 items are invisible, not teased, to callers without access); very long queries (truncation with notice).
- **Data.** `EmbeddingChunk`, all knowledge entities.
- **Agents.** Retrieval Agent.
- **Privacy.** Tier filtering happens in the retrieval layer before ranking, per the FR-PRIV group.
- **Requirements group.** FR-SRCH, FR-RAG. **Metrics.** NFR-001/NFR-002 latency, recall on the golden query set.

### FS-005 · F5 RAG Question Answering

- **Overview.** Grounded question answering over the corpus with mandatory citations, per [RAG_PIPELINE](../ai/RAG_PIPELINE.md).
- **Behavior.** Retrieval assembles tier-filtered context; generation must cite `Source` records for every factual statement and phrase 🟡/🔴 claims with attribution. When the corpus lacks an answer, the system says so explicitly instead of guessing.
- **Key scenarios.** "Which projects used FastAPI?" answered with citations; "Did I get into HBS Foundry?" answered with the flagged status per MASTER_CONTEXT §7.
- **Edge cases.** Contradictory sources (present both with tiers); questions about people other than the owner (minimal-exposure rules per [PRIVACY](../security/PRIVACY.md)); prompt injection embedded in retrieved content (instruction/data separation per FR-SEC).
- **Data.** `EmbeddingChunk`, `Claim`, `Source`, `Conversation`.
- **Agents.** Retrieval Agent, Verification Agent (citation checking).
- **Privacy.** Context assembly is capped at the caller's ceiling; P3 never enters model context (NFR-032).
- **Requirements group.** FR-RAG, FR-VER. **Metrics.** Citation coverage (NFR-037), groundedness score, tier-discipline pass rate (NFR-038).

### FS-006 · F6 AI Digital Twin

- **Overview.** A corpus-grounded conversational representation of the owner, per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md).
- **Behavior.** The Twin Agent answers in the owner's documented voice profile, always discloses that it is an AI, respects tier-aware honesty, and refuses to fabricate opinions absent from the corpus. Public twin mode uses P0 content only; owner mode reaches P2.
- **Key scenarios.** A recruiter asks the public twin about verified projects; the owner rehearses an interview answer against his own history.
- **Edge cases.** Requests to impersonate (refused); questions touching sealed content (unanswerable until release conditions); emotional or spiritual questions (respectful, bounded responses; the El Roi signature is reserved for owner-authored content).
- **Data.** All knowledge entities via retrieval, `Conversation`, `MemoryRecord`.
- **Agents.** Twin Agent, Retrieval Agent, Verification Agent.
- **Privacy.** Mode-scoped ceilings (P0 public, P2 owner); disclosure metadata on every response.
- **Requirements group.** FR-TWIN. **Metrics.** Persona fidelity review score, disclosure compliance (100 percent), tier-discipline pass rate.

### FS-007 · F7 Long-Term Memory Engine

- **Overview.** Durable memory over interactions and content, per [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): working, episodic, semantic, procedural, reflective.
- **Behavior.** Conversations and agent runs produce `MemoryRecord`s; the Reflection Agent consolidates episodic records into semantic summaries on a schedule, scores importance, and archives (never silently deletes). Memories join retrieval with recency and importance weighting.
- **Key scenarios.** The twin remembers a preference stated last month; a weekly rollup summarizes progress on goals.
- **Edge cases.** Contradictory memories (flag, do not merge); redaction requests (tombstone plus re-embedding); memory derived from 🟡 content stays 🟡.
- **Data.** `MemoryRecord`, `EmbeddingChunk`, `Conversation`.
- **Agents.** Reflection Agent, Retrieval Agent.
- **Privacy.** Memories default P2; sealed memories excluded from all retrieval until released.
- **Requirements group.** FR-MEM. **Metrics.** Consolidation compression ratio, memory retrieval hit quality.

### FS-008 · F8 Multi-Agent Orchestration

- **Overview.** The twelve-agent system that does Legacy's work, per [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md).
- **Behavior.** The Orchestrator Agent decomposes tasks, delegates to specialists, tracks budgets, and enforces approval gates for irreversible or outward-facing actions. Every run is an auditable `AgentRun` trace.
- **Key scenarios.** "Research current anti-poaching AI approaches and file a report" fans out Research Agent work, with the Writing Agent drafting and the owner approving before anything is stored as reviewed content.
- **Edge cases.** Budget exhaustion mid-task (partial results plus resumable state); tool failure (retry ladder, dead-letter queue); attempted tier upgrade by an agent (hard-blocked; only the Verification Agent proposes, only the owner approves).
- **Data.** `AgentRun`, `MemoryRecord`, task-dependent entities.
- **Agents.** All twelve.
- **Privacy.** Agents inherit the invoking principal's ceiling; per-agent tool allowlists.
- **Requirements group.** FR-AGT. **Metrics.** Task success rate, approval queue latency, cost per run.

### FS-009 · F9 Verification and Citation Engine

- **Overview.** The productization of MASTER_CONTEXT §0: claims, sources, confidence tiers, and a working verification queue seeded from MASTER_CONTEXT §12.
- **Behavior.** Every factual statement extracted from content becomes a `Claim` linked to `Source`s with a tier. The verification queue lists 🔴 and stale 🟡 claims; the Verification Agent gathers evidence (via Research Agent tools) and proposes tier changes; only the owner applies them. Citations render everywhere claims surface.
- **Key scenarios.** Working the seeded queue (IUS Africa role, SpazaLink placement, HBS Foundry, WorldQuant enrollment per §12); attaching source URLs from `Research/15 Sources.md` to ✅ claims.
- **Edge cases.** Evidence contradicting a ✅ claim (downgrade proposal with audit trail); sources that disappear (link-rot detection, archived snapshots); circular citations (detected and flagged).
- **Data.** `Claim`, `Source`, `AuditLogEntry`.
- **Agents.** Verification Agent, Research Agent.
- **Privacy.** Verification evidence for private claims stays at the claim's tier.
- **Requirements group.** FR-VER. **Metrics.** Queue burn-down, citation resolvability rate, unauthorized-upgrade count (must be zero).

### FS-010 · F10 Public Portfolio

- **Overview.** The P0 surface: profile, projects, talks, articles, and timeline highlights for recruiters, partners, and community, honoring the "building in public" identity (✅ MASTER_CONTEXT §1).
- **Behavior.** Publishing is an explicit owner action through a review gate showing exactly what becomes public. Portfolio pages render only ✅ content as unqualified statements; 🟡 content, if published, carries visible attribution phrasing. The public twin chat runs here with a disclosure banner.
- **Key scenarios.** Publishing the CyberBuddy project page with its GDG Cape Town talk (✅); a visitor asks the public twin about Linfy Tech Solutions.
- **Edge cases.** Unpublishing (immediate removal plus cache purge); attempted publication of a 🔴-claim-dependent page (blocked pending verification); third-party names in public content (consent posture per [PRIVACY](../security/PRIVACY.md)).
- **Data.** P0-tier entities, `Claim`, `Source`.
- **Agents.** Twin Agent (public mode), Writing Agent (drafts).
- **Privacy.** P0 only, enforced at the API and rendering layers; publishing events audit-logged.
- **Requirements group.** FR-UI, FR-PRIV, FR-VER. **Metrics.** NFR-010 performance, zero tier-leak incidents.

### FS-011 · F11 Private Workspace

- **Overview.** The owner's daily operating surface: dashboard, capture inbox, explorers, search, twin chat, journals, verification queue, agent monitor, and settings, per [UI_UX](../ui/UI_UX.md).
- **Behavior.** Everything the platform can do is reachable here, scoped to the owner's P2 ceiling (P3 requires unseal actions). Capture-first design: adding knowledge is never more than one action away.
- **Key scenarios.** Morning review of overnight ingestion and agent runs; quick-capturing an idea; approving a pending agent action.
- **Edge cases.** Concurrent edits from two owner sessions (last-write-wins with revision history); offline access (read-only vault mode per NFR-018/019).
- **Data.** All entities.
- **Agents.** All, surfaced through the agent activity monitor.
- **Privacy.** P2 ceiling by default; trusted users see a P1-scoped variant per their grants.
- **Requirements group.** FR-UI. **Metrics.** NFR-009 performance, daily-use retention by the owner (the platform must earn its place).

### FS-012 · F12 Journals and Reflections

- **Overview.** Personal notes, journal entries, and prayer reflections: the most sensitive content in Legacy, faith-respectful by design.
- **Behavior.** Journal entries default to P2 and can be sealed to P3 with release conditions (a date, a succession event, or never). Sealed entries vanish from all retrieval, search, twin context, and non-vault export until conditions are met. Prayer reflections are a first-class journal type honoring the owner's faith-led identity (✅ §2), never surfaced in any AI output without explicit unsealing.
- **Key scenarios.** Writing a sealed reflection releasable to family after succession; the Reflection Agent summarizing unsealed journal themes for the owner only.
- **Edge cases.** Editing release conditions (owner only, audit-logged); attempting to cite a sealed entry (citation blocked, no existence leak); unsealing at scale (staged confirmation).
- **Data.** `JournalEntry`, `Note`, `Claim`.
- **Agents.** Reflection Agent (unsealed content only).
- **Privacy.** The strictest surface: P3 mechanics per the FR-PRIV group and NFR-032.
- **Requirements group.** FR-PRIV, FR-ING. **Metrics.** Zero sealed-content egress incidents.

### FS-013 · F13 Project and Research Explorer

- **Overview.** Deep, structured views of projects and research: purpose, stack, artifacts, events, collaborators, lessons, and status, spanning the verified portfolio (WildGuard AI, CyberBuddy, NecroNet, PhishGuard, RhinoShield, ✅ §6) and self-reported work (🟡, labeled).
- **Behavior.** Project pages assemble graph neighborhoods: repos, talks, hackathons, teammates, design decisions, failures, and lessons learned. Research views collect sources, notes, and claims per topic. Tier labeling follows MASTER_CONTEXT §6 guidance: non-verified projects render as "a project Linford has described building."
- **Key scenarios.** Reviewing everything about CyberBuddy before a talk; tracing which lessons came from which hackathon.
- **Edge cases.** Projects with no artifacts yet (spec-stage flag per §12 item 5); merged or renamed projects (aliases with history).
- **Data.** `Project`, `Artifact`, `Event`, `Lesson`, `Idea`, `Edge`.
- **Agents.** Graph Agent, Retrieval Agent.
- **Privacy.** Project pages respect item tiers; public project pages show the P0 subset.
- **Requirements group.** FR-KG, FR-UI. **Metrics.** Explorer usage, completeness of project linkage.

### FS-014 · F14 Mentor and Career Advisor

- **Overview.** AI coaching grounded in the owner's actual history: skills evidence, learning history, goals, and trajectory.
- **Behavior.** The Mentor Agent answers career questions with corpus evidence (demonstrated skills per §5 rank above claimed breadth), tracks goals, suggests learning paths, and prepares application or interview material from verified history. It advises; it never acts externally.
- **Key scenarios.** "What evidence do I have for cybersecurity depth?" answered from shipped security projects (✅) with the depth caveat (🟡) intact; goal progress reviews.
- **Edge cases.** Advice requests beyond the corpus (general guidance clearly labeled as not personalized evidence); sensitive career decisions (frames options, never decides).
- **Data.** `Skill`, `Certification`, `Goal`, `Lesson`, `Achievement`, `MemoryRecord`.
- **Agents.** Mentor Agent, Retrieval Agent.
- **Privacy.** Owner-mode only in v1 (P2 ceiling).
- **Requirements group.** FR-TWIN, FR-MEM. **Metrics.** Owner-rated usefulness, evidence-grounding rate.

### FS-015 · F15 Writing and Presentation Assistant

- **Overview.** Drafting articles, talks, posts, and presentations from corpus material in the owner's documented voice.
- **Behavior.** The Writing Agent drafts from cited corpus content, applies the voice profile (🟡 §2: direct warm builder-narrative tone, no em dashes, structural conventions), and always routes output through owner review before anything is published or stored as authored content. Presentation generation produces structured outlines and speaker notes from project history.
- **Key scenarios.** Drafting a DEV.to article about a project; generating a talk deck outline from the CyberBuddy graph neighborhood.
- **Edge cases.** Draft touching 🔴 claims (blocked or attribution-phrased, flagged in review); voice drift (periodic fidelity review); plagiarism of external sources (citation required, similarity check).
- **Data.** `Article`, `Talk`, `Artifact`, `Claim`, `Source`.
- **Agents.** Writing Agent, Retrieval Agent, Verification Agent.
- **Privacy.** Drafts are P2 until the owner publishes through the F10 gate.
- **Requirements group.** FR-TWIN, FR-VER. **Metrics.** Owner edit distance on drafts, citation coverage in drafts.

### FS-016 · F16 Legacy Vault Export and Succession

- **Overview.** The feature that makes Legacy outlive its infrastructure: open-format export and a governed handover path, per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) and the succession design in [AUTHENTICATION](../security/AUTHENTICATION.md) and [AUTHORIZATION](../security/AUTHORIZATION.md).
- **Behavior.** Scheduled vault exports produce Markdown, JSON, and standard media formats with an integrity manifest, readable without Legacy software (NFR-019). Succession activation follows the multi-condition protocol (legal trigger, steward verification, time delay) and shifts the platform into steward-governed mode, releasing P3 content whose conditions specify it.
- **Key scenarios.** Quarterly vault export verified by checksum; a steward drill; actual succession activation decades from now.
- **Edge cases.** Vault export requested during active ingestion (consistent snapshot); steward loses credentials (recovery per AUTHENTICATION with delays); contested activation (cancellation window, owner override while alive).
- **Data.** Everything; `AuditLogEntry` for all succession events.
- **Agents.** None autonomous: succession is deliberately human-governed.
- **Privacy.** The vault contains tiered content with P3 material encrypted under the escrow key hierarchy; release conditions travel with the data.
- **Requirements group.** FR-OPS, FR-PRIV, FR-SEC. **Metrics.** Vault verification pass rate, steward drill success, RPO/RTO compliance (NFR-051/052).

> TODO(verify): succession legal mechanics (will, executor instructions, jurisdiction specifics for South Africa) require professional legal review before F16 implementation completes.

## 5. Acceptance Criteria

- Each FS section above is implementable without consulting sources outside this repository, and each cites the FR domain groups it realizes.
- Every FS has at least one use case in [USE_CASES](USE_CASES.md) and stories in [USER_STORIES](USER_STORIES.md) exercising it.
- The tier-discipline behaviors written into FS-005, FS-006, FS-009, FS-010, and FS-015 have corresponding automated evals per [TESTING](../testing/TESTING.md).
- Phase mapping in [ROADMAP](../roadmap/ROADMAP.md) covers all sixteen features with no orphans.

## 6. Dependencies

- [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md): the FR groups each feature realizes.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): entities named in each Data line.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): agent capabilities assumed here.
- [PRIVACY](../security/PRIVACY.md) and [AUTHORIZATION](../security/AUTHORIZATION.md): tier and ceiling semantics used throughout.

## 7. Risks

- Sixteen features is a large surface for a solo founder; the phase gating in [ROADMAP](../roadmap/ROADMAP.md) and the scope-creep entry in [RISKS](../roadmap/RISKS.md) are the controls.
- Features FS-005/006 (RAG, twin) concentrate reputational risk; their tier-discipline requirements are Must-level and eval-gated.
- FS-016 depends on legal facts not yet gathered (see TODO above); building it on assumptions would create false security.

## 8. Future Enhancements

See [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md). Notable adjacencies: Android companion capture app (extends FS-001), family multi-user (extends FS-011), voice conversations (extends FS-006).

## 9. Examples

A single day through the features: the owner voice-captures an idea on the go (FS-001), overnight agents link it to two related projects (FS-002) and place it on the timeline (FS-003). Next morning he searches "ideas about township commerce" (FS-004), asks for a summary with citations (FS-005), drafts a post about it (FS-015), and publishes a cut-down version publicly (FS-010). The reflection rollup that weekend notes the new thread of thinking (FS-007, FS-012), and the verification queue reminds him the related achievement claim is still 🔴 (FS-009).

## 10. Open Questions

- Should FS-014 (Mentor) open to trusted mentees (P1) in v1, or stay owner-only? Current answer: owner-only; revisit at Phase 4 exit.
- Does FS-010 need a lightweight CMS-style preview environment, or is the review gate sufficient? Deferred to UI design.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §1, §2, §5, §6, §7, §12 (all feature content anchors).
- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) §5 through §9 (tiers, entities, agents, defaults).

## 12. Related Specifications

- [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md), [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md), [NON_FUNCTIONAL_REQUIREMENTS](NON_FUNCTIONAL_REQUIREMENTS.md)
- [USER_PERSONAS](USER_PERSONAS.md), [USER_STORIES](USER_STORIES.md), [USE_CASES](USE_CASES.md)
- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [ROADMAP](../roadmap/ROADMAP.md), [TASKS](../roadmap/TASKS.md)
