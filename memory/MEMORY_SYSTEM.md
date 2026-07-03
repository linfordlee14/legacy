# MEMORY_SYSTEM
### The Legacy long-term memory system: taxonomy, MemoryRecord lifecycle, consolidation, retrieval integration, privacy, and decades-scale durability

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) |

---

## 1. Purpose

Legacy must remember, not merely store. Documents and the knowledge graph hold structured knowledge; the memory system holds the living residue of interaction and reflection: what happened in conversations, what patterns emerged, how the owner works, and what he learned. This specification is the authoritative definition of the canonical memory vocabulary named in [SPEC_CONVENTIONS §8](../docs/SPEC_CONVENTIONS.md). It defines the memory taxonomy, the `MemoryRecord` lifecycle from creation through consolidation to archival, importance scoring and decay, integration with the retrieval pipeline, provenance and privacy behavior inside memory, the reflection engine, conflict handling, metrics, and durability across decades.

## 2. Goals

1. Give every AI surface in Legacy (Twin, Mentor, chat, agents) a persistent, queryable memory that improves with use.
2. Preserve honesty: memories inherit and display confidence tiers, and a memory derived from self-reported content never masquerades as verified fact.
3. Never lose anything silently: memory is consolidated and archived, not deleted, with the sole exception of an explicit owner-driven redaction workflow that leaves a tombstone.
4. Keep sealed (P3) material absolutely out of reach of retrieval until its release conditions are met.
5. Turn raw experience into durable knowledge on a schedule: episodic detail is summarized and promoted into semantic and reflective memory by the Reflection Agent.
6. Remain useful in 2046: embeddings, formats, and models will change many times; memory content must survive all of them.

## 3. Scope

### In scope

- Memory taxonomy: working memory plus the four long-term types (episodic, semantic, procedural, reflective).
- `MemoryRecord` structure at the behavioral level and its full lifecycle.
- Consolidation, importance scoring, decay, and archival policy.
- Memory as a retrieval source inside the RAG pipeline, and its scoring.
- Provenance, confidence tiers, privacy tiers, sealing, and redaction inside memory.
- The reflection engine: scheduled synthesis jobs.
- Conflict handling between contradictory memories.
- Metrics and decades-scale migration duties.

### Out of scope

- Physical storage of `MemoryRecord` and embeddings: [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md).
- The retrieval pipeline's own ranking and context assembly: [RAG_PIPELINE](../ai/RAG_PIPELINE.md).
- Twin persona behavior that consumes memory: [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md).
- Agent scheduling mechanics: [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md).
- Legal and succession rules for sealed content: [PRIVACY](../security/PRIVACY.md) and the security domain.

## 4. Requirements

Requirement IDs (`MEM-##`) are local to this document; product-level traceability lives in the FR-MEM group of [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md).

### 4.1 Memory taxonomy

- **MEM-01** The system implements exactly the canonical vocabulary of [SPEC_CONVENTIONS §8](../docs/SPEC_CONVENTIONS.md): `working memory`, and long-term types `episodic`, `semantic`, `procedural`, `reflective`.

| Type | Scope | Definition | Legacy example |
|------|-------|------------|----------------|
| Working | Session | Transient context for the current conversation or agent run: recent turns, active task state, scratch conclusions. Not persisted beyond the session except through explicit promotion. | The current chat's discussion of a CyberBuddy feature before anything is saved |
| Episodic | Long-term | Time-stamped records of specific happenings: a conversation, an ingestion, an event, a decision made on a date. | "On 2026-06-30 Linford presented CyberBuddy at GDG Cape Town Pet Projects 2026 (✅)" |
| Semantic | Long-term | Stable facts and generalizations distilled from episodes, usually mirrored by Claims and graph elements. | "Linford's public tagline is: Building in public. Building for Africa. (✅)" |
| Procedural | Long-term | How the owner does things: workflows, preferences, methods, style rules. | "Starts builds with mission.md, roadmap.md, techstack.md per his SDD practice (🟡)"; "never use em dashes in written content (🟡, self-reported style guide)" |
| Reflective | Long-term | Synthesized insight about patterns, lessons, and trajectories, produced mainly by the Reflection Agent. | "Hackathons have been the primary launchpad for conservation projects, a pattern across WildGuard AI and related work" |

- **MEM-02** Every long-term memory is persisted as a `MemoryRecord` row (system entity per SPEC_CONVENTIONS §6) with a vector embedding as an `EmbeddingChunk`, plus type, tiers, provenance, importance, and lifecycle state.
- **MEM-03** Working memory is session-scoped by definition. Promotion from working memory into a `MemoryRecord` happens only through the defined creation paths of §4.2, never as an invisible side effect.

### 4.2 MemoryRecord creation

- **MEM-04** Memories are created from three sources only, each stamped on the record:
  1. **Conversations**: salient moments extracted from AI conversations (`Conversation` entities) at session end or at explicit "remember this" moments.
  2. **Ingestion**: the Ingestion and Curation Agents emit episodic memories for notable ingested items ("first artifact for project X", "new person encountered").
  3. **Agent runs**: agents record episodic memories of significant outcomes (task completed, contradiction found), always linked to the `AgentRun`.
- **MEM-05** A new record enters state `candidate`. Candidates become `active` after passing quality checks (non-duplicate, provenance complete, tier assigned). Failed candidates are archived with a reason, not deleted.
- **MEM-06** Every record links to its origin (Conversation, IngestionJob, or AgentRun), to any graph nodes it concerns, and to at least one `Claim` when it asserts a fact. A memory asserting a biographical fact without a Claim link fails the quality check.

### 4.3 Lifecycle states

```
create -> [candidate] -> quality check -> [active]
                                             |
                     consolidation (Reflection Agent)
                                             |
              +---------------+--------------+-------------+
              v               v                            v
        [consolidated]   promoted content              [archived]
        (source records   becomes new                  (out of default
        point to their    semantic/reflective          retrieval scope,
        summary record)   records                      never deleted)

        [redacted] : tombstone state, reachable only from active/archived
                     via the owner redaction workflow (MEM-19)
```

- **MEM-07** State transitions are audited (`AuditLogEntry`) and reversible except `redacted`, which is intentionally one-way and leaves a tombstone.
- **MEM-08** Nothing is silently deleted. The only removal path is the redaction workflow of §4.7, which requires explicit owner action and preserves a tombstone recording that something was removed, when, and under whose authority, without preserving the content.

### 4.4 Importance scoring, decay, and archival

- **MEM-09** Every record carries an importance score in [0, 1], recomputed on consolidation runs from weighted factors:

| Factor | Signal |
|--------|--------|
| Source weight | Owner-explicit "remember this" ranks highest; agent-inferred lowest |
| Entity centrality | Memories touching well-connected graph nodes (core projects, key people) rank higher |
| Recurrence | Repeated appearance of the same fact or pattern across independent episodes |
| Emotional or milestone markers | First launches, achievements, failures, decisions |
| Usage | Retrieval hits that led to accepted answers raise importance |
| Tier | `verified` content weighs above `self_reported`; `flagged` is capped low |

- **MEM-10** Decay: importance decays with age for episodic records that are neither retrieved nor referenced, on a slow half-life measured in months. Semantic, procedural, and reflective records do not decay by age alone; they lose importance only when superseded or contradicted.
- **MEM-11** Archival: records whose importance falls below the archival floor move to `archived`. Archived records remain fully stored, embedded, and searchable in explicit deep-search mode ("search everything, including archive"), but are excluded from default retrieval. Archival is reversible.

### 4.5 Consolidation by the Reflection Agent

- **MEM-12** The Reflection Agent (roster per [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)) owns consolidation with three operations:
  1. **Summarization**: clusters of related episodic records are summarized into a single consolidated record; the sources transition to `consolidated` and link to their summary. Source records remain retrievable through the summary.
  2. **Deduplication**: near-duplicate memories (embedding similarity above a configured threshold plus matching entities) are merged, provenance union preserved. Low-confidence merges go to the human confirmation queue, mirroring the graph merge policy in [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md).
  3. **Promotion**: recurring episodic evidence is promoted to semantic memory ("this keeps being true"), and cross-cutting patterns to reflective memory. Promotion never raises the confidence tier: five 🟡 episodes promote to a 🟡 semantic memory (MEM-16).
- **MEM-13** Consolidation is conservative: when the agent is uncertain whether two memories describe the same thing, it keeps both and links them with a "possibly same" marker for the queue.

### 4.6 Retrieval integration

- **MEM-14** Memory is a first-class retrieval source in the RAG pipeline, alongside document chunks and graph context, per [RAG_PIPELINE](../ai/RAG_PIPELINE.md). The memory retriever returns `MemoryRecord` candidates scored by a blend of:
  - **Relevance**: embedding similarity plus lexical match against the query.
  - **Recency**: freshness of the underlying episode, with type-aware weighting (recency matters most for episodic, least for semantic).
  - **Importance**: the MEM-09 score.
  The blend weights are configuration owned by the RAG pipeline spec; this spec requires only that all three signals are available per record.
- **MEM-15** Every memory delivered into a prompt context carries its type, tier, and timestamp so downstream generation can attribute correctly ("Linford has said..." for 🟡) per the rule in [MASTER_CONTEXT §0](../knowledge/MASTER_CONTEXT.md). Working memory of the current session is always available to the active session without retrieval scoring.

### 4.7 Provenance, tiers, privacy, and redaction

- **MEM-16** Tier inheritance: a memory's confidence tier is the minimum tier across its source material, and consolidation output takes the minimum tier of its inputs. Memories derived from 🟡 content stay 🟡 forever unless the underlying Claim is upgraded through the Verification Agent plus owner approval; the memory then updates by reference, never by local edit.
- **MEM-17** Privacy default is P2 (owner only). Memories derived from P1 content stay at most P1-visible under the granting rules of [AUTHORIZATION](../security/AUTHORIZATION.md); a memory mixing tiers takes the most restrictive tier of its sources.
- **MEM-18** Sealed memory: P3 records (for example anything derived from prayer reflections or sealed journal entries) are excluded from all retrieval, all consolidation summaries visible below P3, all metrics samples, and all agent contexts until their release condition (time lock or succession event, per [PRIVACY](../security/PRIVACY.md)) is met. Sealing is enforced at the datastore query boundary, not by prompt instructions.
- **MEM-19** Redaction workflow: the owner can order content removed. Steps: (1) owner selects records or a content pattern, (2) system shows every derived record, summary, and embedding affected, (3) on confirmation, content is erased, a tombstone `MemoryRecord` (state `redacted`) is written per erased record, (4) all consolidated summaries that included the content are regenerated without it, (5) all affected embeddings are recomputed so no vector residue of the redacted content remains, (6) the audit log records the action without recording the removed content.

### 4.8 Reflection engine schedules

- **MEM-20** Scheduled synthesis jobs, run by the Reflection Agent under Orchestrator budgets:

| Job | Cadence | Output |
|-----|---------|--------|
| Weekly rollup | Weekly | Reflective record summarizing the week's episodes: work, events, conversations, notable decisions |
| Lessons-learned extraction | Monthly and after any Event with kind hackathon or launch | `Lesson` graph nodes plus reflective memories, linked via `reflects_on` |
| Goal progress tracking | Monthly | Per active `Goal`: evidence of progress or stall from episodic memory, surfaced to the owner |
| Consolidation sweep | Monthly | Summarization, dedup, promotion per §4.5 |
| Tier and conflict audit | Quarterly | Contradiction report feeding the verification queue (§4.9) |
| Annual retrospective | Yearly | Long-form reflective synthesis, a candidate input for Writing Agent year-in-review drafts |

- **MEM-21** Every job emits an `AgentRun` trace and its outputs enter the normal candidate lifecycle; scheduled jobs get no shortcut past quality checks.

### 4.9 Conflict handling

- **MEM-22** When a new or consolidated memory contradicts an existing memory or Claim (detected via entity overlap plus stance comparison), the system MUST NOT silently merge, average, or pick a winner. Both records are kept `active`, linked with a `contradicts` edge at the graph layer, and a verification task is enqueued to the human verification queue (the productization of [MASTER_CONTEXT §12](../knowledge/MASTER_CONTEXT.md)).
- **MEM-23** Until resolved, retrieval that would surface either memory surfaces the conflict marker too, so generated answers can hedge honestly. Resolution (owner decision or Verification Agent evidence) downgrades or archives the losing record with an audit trail.

### 4.10 Metrics

- **MEM-24** Emitted to [OBSERVABILITY](../deployment/OBSERVABILITY.md):

| Metric | Definition | Intent |
|--------|------------|--------|
| Retrieval hit quality | Share of retrieved memories judged useful (owner feedback plus LLM-judge sampling) | Is memory helping answers |
| Consolidation compression ratio | Source records consolidated / summary records produced | Is consolidation earning its cost |
| Promotion rate | Episodic records promoted to semantic or reflective per sweep | Is experience becoming knowledge |
| Archive rate and recall-from-archive | Records archived per month; archived records later restored | Is decay tuned correctly |
| Conflict backlog | Open contradiction tasks and their age | Honesty debt |
| Tier composition | ✅/🟡/🔴 share of active memory | Drift watch |
| Sealed leakage tests | Scheduled negative tests proving P3 exclusion | Hard invariant, must be zero leaks |

### 4.11 Decades-scale durability

- **MEM-25** Embedding independence: memory content is canonical as text plus structured fields; embeddings are derived data. Every `EmbeddingChunk` records its model and version. When the embedding model changes, a re-embedding migration regenerates vectors from canonical content in the background, with dual-index querying during cutover. Losing every vector must lose zero memories.
- **MEM-26** Format migration: `MemoryRecord` schema changes ship with forward migrations and an export path. Memory participates in the versioned Legacy Vault export (Markdown plus JSON per [SPEC_CONVENTIONS §9](../docs/SPEC_CONVENTIONS.md)) so the corpus outlives any datastore.
- **MEM-27** Model-neutral phrasing: consolidated summaries are written as plain declarative text with explicit dates, names, and tiers, not model-specific prompt artifacts, so future models can consume them unchanged.

## 5. Acceptance Criteria

1. Creating memories through each of the three creation paths yields records with correct origin links, and any record missing provenance fails the candidate quality check.
2. A consolidation run over a cluster of related episodic records produces one summary record, transitions sources to `consolidated`, and the sources remain reachable from the summary.
3. Promotion of five self-reported episodes produces a semantic memory carrying `self_reported`, and no code path can mark it `verified` without a Verification Agent proposal plus owner approval.
4. No delete operation exists on active or archived memory outside the redaction workflow; attempting one is rejected and audited.
5. Redacting a record erases its content, writes a tombstone, regenerates affected summaries, and re-embeds affected chunks; a subsequent semantic search for the redacted content over all indexes returns nothing derived from it.
6. P3-derived memories never appear in retrieval results, consolidation outputs below P3, or agent contexts; the scheduled leakage test suite passes with zero leaks.
7. Two contradictory memories are both retained, linked as contradictory, and a verification queue task exists; retrieval surfacing either includes the conflict marker.
8. The weekly rollup, monthly consolidation, and goal progress jobs each produce auditable `AgentRun` traces and lifecycle-compliant outputs.
9. After a simulated embedding-model change, re-embedding completes from canonical text alone and retrieval quality metrics return to baseline.
10. An archived record is excluded from default retrieval, findable in deep-search mode, and restorable to `active`.

## 6. Dependencies

- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): `MemoryRecord`, `EmbeddingChunk`, `AuditLogEntry` definitions and pgvector storage.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md): retrieval scoring, context assembly, deep-search mode.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): Reflection Agent, Verification Agent, Orchestrator scheduling and budgets.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): graph nodes referenced by memories, `contradicts` and `reflects_on` semantics, merge-queue pattern.
- [PRIVACY](../security/PRIVACY.md) and [AUTHORIZATION](../security/AUTHORIZATION.md): P3 sealing conditions, Grants, redaction authority.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): tier system and the verification queue this system productizes.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Consolidation hallucination (summary asserts what sources do not) | Corrupted long-term knowledge | Summaries cite source records; sampled LLM-judge and owner review; conservative MEM-13 policy |
| Tier laundering through summarization | 🟡 presented as fact | Minimum-tier inheritance (MEM-16), tier displayed at retrieval (MEM-15) |
| Sealed content leaking via derived artifacts | Deep personal harm, broken trust | Boundary enforcement, no prompt-level trust, scheduled leakage tests (MEM-18, metrics) |
| Vector residue after redaction | Redaction promise broken | Mandatory re-embedding step in the workflow (MEM-19) |
| Memory bloat from low-value episodes | Cost, retrieval noise | Importance scoring, decay, archival (MEM-09 to MEM-11) |
| Over-aggressive decay hiding rare but precious memories | Lost history | Archive is searchable and reversible; recall-from-archive metric watched |
| Embedding model deprecation | Silent retrieval degradation | Versioned embeddings, canonical-text regeneration (MEM-25) |
| Conflict backlog growing unbounded | Honesty debt normalizes | Backlog metric with alert threshold, quarterly audit job |

## 8. Future Enhancements

1. Owner-authored memory annotations: inline corrections that generate high-importance procedural or semantic records.
2. Cross-session working-memory handoff for explicitly continued tasks, without weakening MEM-03.
3. Affect and significance tagging of episodes to improve milestone detection in importance scoring.
4. Family and mentee memory views: P1-scoped reflective digests, gated by the security domain.
5. Time-capsule memories: owner-authored records with P3 time locks addressed to future readers.
6. Selective memory replay: periodic resurfacing of high-importance old memories to the owner ("on this day"), feeding usage signals back into importance.
7. Compression research: measured tradeoffs between summary depth and retrieval fidelity once real usage data exists.

## 9. Examples

### 9.1 Episodic MemoryRecord (illustrative JSON, from a ✅ fact)

```json
{
  "id": "mem_01J...",
  "memory_type": "episodic",
  "state": "active",
  "content": "On 2026-06-30 Linford presented CyberBuddy at GDG Cape Town, Pet Projects: The 2026 Edition.",
  "occurred_at": "2026-06-30",
  "confidence_tier": "verified",
  "privacy_tier": "P0",
  "importance": 0.86,
  "origin": { "kind": "ingestion", "ingestion_job": "job_01J..." },
  "graph_refs": ["person_linford", "proj_cyberbuddy", "org_gdgct", "event_petprojects2026"],
  "claims": ["claim_gdg_petprojects_talk"],
  "embedding": { "chunk_id": "emb_01J...", "model": "embed-model-a", "model_version": "2026-05" }
}
```

### 9.2 Promotion with tier preservation

Inputs: four episodic memories, each recording Linford describing his SDD practice (starting builds with mission.md, roadmap.md, techstack.md), all 🟡 because the practice is self-reported per [MASTER_CONTEXT §2](../knowledge/MASTER_CONTEXT.md).
Consolidation output: one procedural memory, "Linford's stated build methodology begins with mission.md, roadmap.md, and techstack.md," `confidence_tier: self_reported`, linked to the four sources (now `consolidated`) and to the underlying Claim. The Twin Agent consuming this memory says "Linford describes his practice as..." rather than asserting it, honoring MEM-15.

### 9.3 Conflict example

An episodic memory from a conversation states a project deadline of "end of August 2026"; a later ingested note states "mid-September 2026." Both stay active, a `contradicts` link is written, a verification task appears in the queue, and until the owner resolves it, any retrieval containing either memory carries the marker "conflicting information on this deadline exists."

### 9.4 Sealed memory behavior

A journal entry with kind prayer_reflection is ingested at P3. Its derived memory is stored, embedded, and invisible: it appears in no retrieval, no weekly rollup below P3, and no agent context. When its release condition triggers decades later, it enters retrieval with its original tier and timestamps intact.

## 10. Open Questions

- > TODO(decision): Final numeric weights for relevance, recency, and importance in the retrieval blend; owned by RAG_PIPELINE, needs joint calibration once a corpus exists.
- > TODO(decision): Archival floor value and episodic decay half-life; initial proposal is conservative (long half-life) pending real usage data.
- > TODO(decision): Whether owner feedback ("that answer used a bad memory") should down-rank a memory automatically or only queue it for review.
- > TODO(verify): Release-condition taxonomy for P3 (time lock durations, succession triggers) is owned by the security domain and must be finalized before sealed memory ships.
- > TODO(decision): Exact near-duplicate similarity threshold for memory dedup, and whether it shares configuration with the graph entity-resolution thresholds.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): §0 tier system and downstream-AI rule, §2 style and SDD practice (🟡), §12 verification queue.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): §5 privacy tiers, §6 system entities, §8 canonical memory vocabulary, §9 baseline stack.
- Cognitive-architecture background: the episodic/semantic/procedural distinction follows long-standing memory-systems literature; reflective memory is a Legacy-specific addition for synthesized insight. No external standard is normative.

## 12. Related Specifications

- [RAG_PIPELINE](../ai/RAG_PIPELINE.md)
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md)
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md)
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)
- [PRIVACY](../security/PRIVACY.md), [AUTHORIZATION](../security/AUTHORIZATION.md)
- [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (the FR-MEM group)
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)
