# RAG_PIPELINE
### The retrieval-augmented generation pipeline: from ingested artifact to cited, tier-aware answer

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [AI_ARCHITECTURE](./AI_ARCHITECTURE.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [API_SPECIFICATION](../api/API_SPECIFICATION.md) |

---

## 1. Purpose

This document specifies the retrieval-augmented generation (RAG) pipeline of Legacy end to end: how ingested content becomes chunks, how chunks become searchable (vector plus lexical), how queries are understood and answered, how privacy tiers are enforced before any model sees content, how every answer is grounded in `Claim` and `Source` records with citations, and how the pipeline stays healthy over decades of corpus growth and model change.

The pipeline is the mechanism behind the Semantic Search, Hybrid Search, RAG, Question Answering, and Natural Language Search capabilities assigned to the Retrieval Agent in the capability map of [AI_ARCHITECTURE](./AI_ARCHITECTURE.md).

## 2. Goals

1. Answers are grounded: every factual statement in a generated answer traces to retrieved corpus content, with citations rendered per the API contract.
2. Honesty over fluency: when the corpus does not contain an answer, the pipeline says so instead of hallucinating, and tier-aware phrasing is applied to every biographical claim.
3. Privacy is structural: tier filtering happens in the retrieval store, before context assembly, so no model ever receives content above the caller's tier ceiling.
4. Retrieval quality is measurable and regression-guarded across content types, model upgrades, and decades of drift.
5. The index is a rebuildable cache: source artifacts are durable, embeddings and indexes can always be regenerated.

## 3. Scope

**In scope:** the handoff from ingestion, chunking strategy per content type, embedding and indexing, the query pipeline, context assembly, generation rules, the citation rendering contract, failure modes, quality metrics and evaluation datasets, and re-indexing and drift management.

**Out of scope:** capture and parsing of raw sources (Ingestion Agent, see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)), model routing internals ([AI_ARCHITECTURE](./AI_ARCHITECTURE.md) §4.2), memory record lifecycle ([MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)), physical schema ([DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)), and endpoint definitions ([API_SPECIFICATION](../api/API_SPECIFICATION.md)).

## 4. Requirements

Requirement IDs are document-scoped (`RAG-##`). They trace to the FR-RAG and FR-SRCH domain groups in [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md).

### 4.1 Pipeline overview

```
INGESTION SIDE (write path)
  Ingestion Agent output (IngestionJob)
        |  normalized artifact + metadata (tier, source, timestamps)
        v
  [1] Chunking (per content type)
        v
  [2] Enrichment (titles, entity links, injection flags via Curation Agent)
        v
  [3] Embedding (versioned model)  ---->  [4] Indexing
                                           - pgvector index (semantic)
                                           - lexical index (keyword)
                                           - metadata columns (tier, type, time)

QUERY SIDE (read path)
  User / Agent query (with caller identity and tier ceiling)
        v
  [5] Query understanding -> [6] Query expansion
        v
  [7] Hybrid retrieval (vector + lexical, TIER FILTER APPLIED IN STORE)
        v
  [8] Reranking -> [9] Context assembly (budget, dedup, diversity,
                        recency and importance weighting via memory system)
        v
  [10] Generation (tier-aware, citation-mandatory)
        v
  [11] Citation resolution to Claim/Source -> API response
```

### 4.2 Ingestion handoff

**RAG-01.** The pipeline consumes only the normalized output of the Ingestion Agent, recorded as an `IngestionJob` result. Each handed-off artifact MUST carry: a stable artifact identifier, content type, privacy tier (default P2 per [SPEC_CONVENTIONS §5](../docs/SPEC_CONVENTIONS.md)), source reference (`Source` record), creation and ingestion timestamps, language, and a content hash.

**RAG-02.** Artifacts missing a privacy tier or source reference are rejected back to the ingestion queue; the pipeline never guesses provenance.

**RAG-03.** Idempotency: re-ingesting an artifact with an unchanged content hash is a no-op; a changed hash triggers re-chunk and re-embed of that artifact only, with old chunks tombstoned, not deleted, until index consistency is confirmed.

### 4.3 Chunking strategy per content type

**RAG-04.** Chunking is structure-aware per content type. Sizes are in tokens and are tunable configuration, not code constants:

| Content type | Strategy | Target size | Overlap | Notes |
|--------------|----------|-------------|---------|-------|
| Documents (articles, specs, PDFs) | Heading- and paragraph-aware splitting; never split mid-sentence | 400-800 | 10-15% | Preserve heading path in metadata for citation display |
| Code (repos, snippets) | Symbol-aware: function, class, or module units; file summary chunk per file | 200-600 | 0% (structural) | Language, path, and symbol name in metadata |
| Conversations (AI chats, message logs) | Turn-grouped windows keeping question-answer pairs intact | 300-600 | 1 turn | Speaker labels preserved |
| Journal entries | Entry-level; split only entries above the max size, on section breaks | up to 800 | 10% | Journals are frequently P2/P3; tier enforcement critical |
| Media transcripts (talks, voice notes, video) | Time-coded segments aligned to pauses or topic shifts | 60-120 seconds of speech (roughly 150-400) | 1 segment | Start/end timestamps in metadata for deep-linking |

**RAG-05.** Every chunk stores, alongside its text: artifact id, chunk ordinal, heading or symbol path, privacy tier (inherited from artifact), content type, source reference, timestamps, language, content hash, injection-flag status, and embedding model version. This metadata IS the provenance packet and travels with the chunk through retrieval into context assembly.

### 4.4 Embedding and indexing

**RAG-06.** Embeddings are produced by the platform embedding model chosen under the AI architecture's embedding strategy (decided: MASTER_ARCHITECTURE ADR-16, `gemini-embedding-001` at 1536 dimensions); vectors are stored in PostgreSQL with pgvector per the baseline default in [SPEC_CONVENTIONS §9](../docs/SPEC_CONVENTIONS.md).

**RAG-07.** Two indexes are maintained over the same chunk store: (a) an approximate nearest neighbor vector index (HNSW-class) for semantic retrieval, and (b) a lexical full-text index with stemming and exact-phrase support for keyword retrieval. Hybrid search requires both to be healthy; index health is monitored per [OBSERVABILITY](../deployment/OBSERVABILITY.md).

**RAG-08.** Embedding writes are asynchronous with a freshness target: newly ingested content becomes searchable within minutes, and the searchable-lag metric is exported. Interim lexical-only availability is acceptable; vector-only gaps are not silently ignored.

### 4.5 Query pipeline

**RAG-09.** Query understanding: each query is classified (factual lookup, exploratory, chronological, comparative, generation request), key entities are linked to knowledge graph nodes where possible ([KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md)), and time expressions are resolved ("during the RhinoGuardians hackathon period" resolves to a date range). This step runs on a small-tier routed model per the cost rules in [AI_ARCHITECTURE](./AI_ARCHITECTURE.md).

**RAG-10.** Query expansion: bounded generation of reformulations and synonyms (including project alias handling, for example a query about "the anti-poaching project" expanding toward RhinoGuardians and WildGuard AI as candidate entities). Expansion never adds terms that presuppose unverified facts.

**RAG-11.** Hybrid retrieval: vector top-k and lexical top-k are retrieved in parallel and fused (reciprocal rank fusion or equivalent, configuration-defined). Both retrievals execute WITH the caller's privacy-tier predicate applied in the datastore query itself.

**RAG-12.** Privacy-tier filtering BEFORE model context assembly is a hard invariant: the tier predicate (caller ceiling: P0 for public, P1 for trusted grantees per `Grant`, P2 for owner, P3 only when release conditions are met, see [DIGITAL_TWIN](./DIGITAL_TWIN.md) and [AUTHORIZATION](../security/AUTHORIZATION.md)) is applied inside retrieval queries, enforced by row-level policy in the database as defense in depth. Post-retrieval filtering alone is forbidden. No chunk above the ceiling may ever appear in any prompt layer, log excerpt, or error message.

**RAG-13.** Reranking: fused candidates (typically 30-50) are reranked to the final candidate set (typically 8-15) by a cross-encoder or LLM reranker on a cheap routed model, scoring semantic relevance to the resolved query intent.

**RAG-14.** Provenance is carried with every chunk end to end: the assembly step receives (chunk text, provenance packet per RAG-05) pairs, and the generation step receives chunks wrapped in delimited untrusted-data blocks labeled with a citable chunk reference.

### 4.6 Context assembly rules

**RAG-15.** Budget: assembled retrieval context fits the L5 share of the request's token budget defined in [AI_ARCHITECTURE](./AI_ARCHITECTURE.md) §4.4. Chunks are admitted in ranked order until the budget is filled; a chunk is never truncated mid-sentence, it is dropped instead.

**RAG-16.** Deduplication: near-duplicate chunks (same content hash, or similarity above a configured threshold) are collapsed to the single best-ranked instance, keeping the union of their provenance references.

**RAG-17.** Source diversity: assembly guarantees a configurable minimum spread across distinct artifacts and source types when available, so one long document cannot monopolize context for broad questions.

**RAG-18.** Recency and importance weighting: final ordering blends rerank score with signals from the memory system ([MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)): recency decay for time-sensitive intents, `MemoryRecord` importance scores, and reflective-memory pointers ("lessons learned" records boost their cited sources). Chronological intents override recency decay with timeline ordering.

### 4.7 Generation rules

**RAG-19.** Mandatory citations: every factual statement in the answer MUST carry at least one citation resolving to a `Claim` and its `Source` records, or to a specific chunk reference when no curated Claim exists yet. Uncited factual sentences are a generation defect measured in evaluation.

**RAG-20.** Tier-aware phrasing (inherits the platform invariant in [AI_ARCHITECTURE](./AI_ARCHITECTURE.md) and MASTER_CONTEXT §0): verified claims may be asserted with citation; self-reported claims are attributed ("Linford reports..."); flagged claims are omitted or explicitly marked unverified, never asserted. The generation prompt (layer L2) contains these rules verbatim; the Verification Agent's tier data arrives with each chunk's provenance packet.

**RAG-21.** Not-in-corpus behavior: when retrieval confidence is below threshold or the reranked set is empty or off-topic, the answer states plainly that the information is not in the corpus (for example: "I do not have that in Linford's records"), optionally suggesting related material that IS present. Guessing is a defect. The negative evaluation set (§4.10) enforces this.

**RAG-22.** Answers never reveal the existence or subject matter of content above the caller's tier ceiling ("there is a private journal about this" is itself a leak).

### 4.8 Citation rendering contract

**RAG-23.** The API returns citations as structured data, not prose, per [API_SPECIFICATION](../api/API_SPECIFICATION.md). Contract shape (illustrative, field names authoritative in the API spec):

```json
{
  "answer": "text with inline citation markers like [1] and [2]",
  "citations": [
    {
      "marker": "[1]",
      "claim_id": "clm_...",
      "confidence_tier": "verified",
      "sources": [
        { "source_id": "src_...", "title": "GDG Cape Town, Pet Projects 2026",
          "artifact_id": "art_...", "chunk_ref": "art_...#c14",
          "locator": { "type": "heading_path", "value": "Talks > 2026" } }
      ]
    },
    {
      "marker": "[2]",
      "claim_id": "clm_...",
      "confidence_tier": "self_reported",
      "attribution_phrase": "Linford reports",
      "sources": [ { "source_id": "src_...", "artifact_id": "art_...",
                     "chunk_ref": "art_...#c03",
                     "locator": { "type": "timestamp", "value": "00:12:40-00:14:05" } } ]
    }
  ],
  "retrieval": { "chunks_considered": 42, "chunks_used": 9, "tier_ceiling": "P1" },
  "not_in_corpus": false
}
```

**RAG-24.** Locators are content-type appropriate: heading path for documents, symbol path for code, turn index for conversations, timestamp range for transcripts. Clients can deep-link every citation.

### 4.9 Failure modes and fallbacks

| Failure | Detection | Fallback behavior |
|---------|-----------|-------------------|
| Vector index unavailable | Health check, query error | Lexical-only retrieval, response flagged `degraded: true` |
| Lexical index unavailable | Health check | Vector-only retrieval, degraded flag |
| Embedding service down | Write-path queue growth | Ingestion continues, chunks queue for embedding; searchable-lag alert fires |
| Reranker failure | Timeout or error | Skip rerank, use fusion order, degraded flag |
| Generation model unavailable | Router error after fallback chain | Return retrieved passages with citations and no synthesized answer ("sources-only mode") |
| Low retrieval confidence | Score threshold | Not-in-corpus response per RAG-21 |
| Tier predicate cannot be evaluated | Authorization error | Fail closed: refuse the query, never default to a wider ceiling |
| Citation resolution failure | Missing Claim/Source link | Withhold the affected sentence, log a verification task |

**RAG-25.** All degraded responses carry an explicit machine-readable degradation flag; silent quality loss is not permitted.

### 4.10 Quality metrics and evaluation datasets

**RAG-26.** Metrics, computed on the golden sets defined in [AI_ARCHITECTURE](./AI_ARCHITECTURE.md) §4.6 and trended per [OBSERVABILITY](../deployment/OBSERVABILITY.md):

| Metric | Definition | Gate |
|--------|------------|------|
| Retrieval recall@k | Share of labeled relevant chunks present in top k | Regression-blocked |
| Groundedness | Share of answer statements supported by retrieved chunks | Regression-blocked |
| Citation accuracy | Precision and recall of citations against reference labels | Regression-blocked |
| Tier discipline | Correct attribution/flagging of 🟡 and 🔴 claims | Hard gate, target 100% |
| Not-in-corpus correctness | Correct refusals on the negative set | Hard gate |
| Answer latency | p50 and p95 end-to-end, per request class | Budget in [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) |

**RAG-27.** Evaluation datasets: the retrieval label set, grounded QA set, negative set, and tier-discipline set are versioned artifacts owned under [TESTING](../testing/TESTING.md); they grow with the corpus (new labeled samples per content type per quarter) so evaluation tracks real corpus composition.

### 4.11 Re-indexing and drift management over decades

**RAG-28.** Embedding model migrations follow the dual-index policy in [AI_ARCHITECTURE](./AI_ARCHITECTURE.md) §4.3: rebuild from source artifacts, validate against the retrieval set, atomic switch, retain the old index through one backup cycle.

**RAG-29.** Scheduled index maintenance: periodic vacuum and index rebuild windows, orphan-chunk sweeps (chunks whose artifact was deleted or re-tiered), and tombstone cleanup, run as background jobs with cost caps.

**RAG-30.** Semantic drift: as vocabulary, project names, and roles change over years, the Curation Agent maintains alias maps (fed by the knowledge graph) used in query expansion, and quarterly drift reviews sample queries whose retrieval quality decayed against historical baselines.

**RAG-31.** Re-chunk policy: changes to chunking configuration apply prospectively by default; a full retrospective re-chunk is an explicit, ADR-recorded operation with the same validation gate as a model migration.

**RAG-32.** Tier changes propagate synchronously: when the owner re-tiers an artifact, all its chunks' tier metadata updates in the same transaction, and answer caches touching those chunks are invalidated before the operation reports success.

## 5. Acceptance Criteria

1. An artifact of each content type in §4.3, ingested end to end, becomes searchable within the freshness target, with chunk metadata complete per RAG-05.
2. A penetration-style test issuing P0-ceiling queries against a corpus containing P1-P3 content shows zero above-ceiling chunks in retrieval results, prompts, logs, or answers, including existence leaks (RAG-22).
3. Every answer in the grounded QA evaluation carries resolvable citations; citation accuracy and groundedness meet the gates of RAG-26 on the current golden sets.
4. The negative set produces not-in-corpus responses with zero hallucinated answers; the tier-discipline set passes at 100%.
5. Disabling the vector index, the lexical index, and the reranker (one at a time) in a drill produces the documented fallback with `degraded: true`, never an error-free silent degradation.
6. A rehearsed embedding migration on a corpus snapshot completes with retrieval recall within tolerance of the pre-migration baseline before switchover.
7. Re-tiering an artifact makes its content immediately unavailable to callers below the new tier, verified by cache-invalidation test.

## 6. Dependencies

- [AI_ARCHITECTURE](./AI_ARCHITECTURE.md): model routing, context budgets, embedding strategy, evaluation framework.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): Ingestion Agent (handoff), Curation Agent (enrichment, aliases), Retrieval Agent (owner of this pipeline), Verification Agent (Claims, citations).
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): importance and recency signals for assembly (RAG-18).
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): `EmbeddingChunk`, `IngestionJob`, `Claim`, `Source` definitions; row-level tier policies.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): entity linking in query understanding.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): authoritative citation payload and streaming contract.
- [AUTHORIZATION](../security/AUTHORIZATION.md): caller tier-ceiling resolution and `Grant` semantics.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tier filter bypass through a secondary path (cache, logs, error text) | Privacy breach of P2/P3 content | Filtering in-store plus row-level policy, leak tests in CI, cache keys include tier ceiling |
| Chunking that splits meaning (verse, code symbol, journal thought) | Wrong or misleading answers | Structure-aware strategies (RAG-04), per-type evaluation samples |
| Citation theater (citations attached but not supporting the claim) | False confidence | Citation precision metric with LLM-judge plus human audit |
| Corpus growth degrading latency over decades | Slow answers | ANN indexing, partitioning strategy in DATABASE_SCHEMA, latency budgets and alerts |
| Alias and vocabulary drift | Silent recall decay | RAG-30 drift reviews, graph-fed alias maps |
| Injection payloads inside retrieved chunks | Instruction hijack | Untrusted-data delimiting and flags inherited from [AI_ARCHITECTURE](./AI_ARCHITECTURE.md) §4.5 |
| Over-reliance on one long document | One-sided answers | Source diversity rule (RAG-17) |

## 8. Future Enhancements

- Graph-augmented retrieval: expanding candidate sets through knowledge graph neighborhoods before reranking.
- Multimodal retrieval over image embeddings (pending the separate image space decision in AI_ARCHITECTURE).
- Personal relevance feedback: owner thumbs-up/down on citations feeding rerank training data.
- Offline retrieval subset inside the Legacy Vault export (lexical-only, P0/P1 content).
- Per-collection retrieval scopes ("search only my journals from 2026").

## 9. Examples

Query walk-through (owner mode, P2 ceiling): the owner asks "What accuracy did the anti-poaching prototype reach, and where did it start?" Query understanding links "anti-poaching prototype" toward RhinoGuardians (🟡 project per MASTER_CONTEXT §6); hybrid retrieval returns journal and project-note chunks; generation answers: "Linford reports that the RhinoGuardians prototype reached approximately 95% detection accuracy [1], and that the project originated at the AI Genesis Hackathon in November 2025 [2]." Both markers resolve to self_reported Claims. The reported HBS Foundry acceptance, being 🔴, is either omitted or explicitly stated as unverified and pending confirmation.

Public mode contrast (P0 ceiling): the same question from an anonymous visitor retrieves only P0 chunks. If no P0 artifact covers the accuracy figure, the answer is: "I do not have that detail in the public records. Public sources do cover the WildGuard AI conservation project [1]." No mention is made of private notes existing.

Ingestion-to-index trace (illustrative):

```json
{
  "ingestion_job": "job_...",
  "artifact_id": "art_talk_gdg_2026",
  "content_type": "media_transcript",
  "privacy_tier": "P0",
  "chunks": [
    { "chunk_ref": "art_talk_gdg_2026#c01", "ordinal": 1,
      "locator": { "type": "timestamp", "value": "00:00:00-00:01:45" },
      "embedding_model_version": "emb-v1", "injection_flag": false }
  ],
  "indexed": { "vector": true, "lexical": true, "searchable_lag_seconds": 84 }
}
```

## 10. Open Questions

- > TODO(decision): fusion algorithm and weights for hybrid retrieval (reciprocal rank fusion vs weighted score fusion); tune on the retrieval label set.
- > TODO(decision): retrieval confidence threshold that triggers not-in-corpus behavior, possibly stricter for the public twin than owner mode (shared question with AI_ARCHITECTURE).
- > TODO(decision): whether reranking uses a hosted reranker model or an LLM-judge pattern at launch.
- > TODO(verify): pgvector index parameters (HNSW build settings) appropriate for the projected corpus size; coordinate with DATABASE_SCHEMA capacity planning.
- Should conversations with the AI itself (Conversation entities) be retrievable by default, or opt-in, to avoid feedback loops of the system citing its own prior outputs as evidence?

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier rules), §6 (project examples used in this spec), §7 (flagged achievements).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §5 (privacy tiers), §6 (Claim/Source provenance model), §9 (pgvector baseline).

## 12. Related Specifications

- [AI_ARCHITECTURE](./AI_ARCHITECTURE.md): parent AI architecture, routing, budgets, evaluation.
- [DIGITAL_TWIN](./DIGITAL_TWIN.md): the primary consumer of this pipeline's tier-aware answers.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): weighting signals and memory retrieval interplay.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): entity linking and alias maps.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): chunk and index storage.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): citation payload contract.
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md), [AUTHORIZATION](../security/AUTHORIZATION.md): tier enforcement foundations.
- [TESTING](../testing/TESTING.md): evaluation dataset ownership.
