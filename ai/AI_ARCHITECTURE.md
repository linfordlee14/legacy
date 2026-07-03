# AI_ARCHITECTURE
### The overall AI architecture of Legacy: capability map, model routing, embeddings, context engineering, safety, evaluation, and cost control

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md), [RAG_PIPELINE](./RAG_PIPELINE.md), [DIGITAL_TWIN](./DIGITAL_TWIN.md) |

---

## 1. Purpose

This document defines the AI layer of the Legacy platform end to end: which AI capabilities the product exposes, which component owns each capability, how model providers are selected and routed, how embeddings are produced and maintained over decades, how context windows are engineered, how safety and grounding are enforced, how AI quality is evaluated, and how AI cost is controlled.

It is the parent specification for [RAG_PIPELINE](./RAG_PIPELINE.md) and [DIGITAL_TWIN](./DIGITAL_TWIN.md), and it binds every AI behavior in the system to the provenance discipline of [MASTER_CONTEXT §0](../knowledge/MASTER_CONTEXT.md): a 🟡 (self-reported) or 🔴 (flagged) claim is never presented as an established fact; it is attributed or flagged, without exception.

## 2. Goals

1. Give every required AI capability exactly one owning component and one authoritative specification, so no capability is orphaned or double-owned.
2. Keep the platform provider-portable: Anthropic Claude API is primary, Google Gemini API and Groq API are routed alternates behind a single model-router abstraction, per the baseline defaults in [SPEC_CONVENTIONS §9](../docs/SPEC_CONVENTIONS.md).
3. Make grounding and honesty structural, not stylistic: tier-aware phrasing, mandatory citations, and refusal-over-hallucination are enforced by the pipeline, not left to model goodwill.
4. Survive decades: model versions are pinned, upgrades pass regression evaluation gates, and embeddings are versioned and re-buildable from source artifacts.
5. Keep operating cost predictable through token budgets, caching, and routing of mechanical work to cheaper models.

## 3. Scope

**In scope:** the AI capability map, model-router design and policies, embedding strategy, context engineering, safety and grounding policy, the AI evaluation framework, and AI cost management.

**Out of scope:** the retrieval pipeline internals (see [RAG_PIPELINE](./RAG_PIPELINE.md)), the twin persona (see [DIGITAL_TWIN](./DIGITAL_TWIN.md)), agent-to-agent orchestration protocol (see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)), memory schemas (see [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)), storage and schema definitions (see [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)), and API surface details (see [API_SPECIFICATION](../api/API_SPECIFICATION.md)).

## 4. Requirements

Requirement IDs below are document-scoped (`AIA-##`). They trace upward to the FR-RAG, FR-SRCH, FR-TWIN, FR-AGT, FR-MEM, and FR-VER domain groups in [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md); this document deliberately does not cite individual numeric IDs from that parallel-authored file.

### 4.1 AI capability map

**AIA-01.** Every AI capability in the table below MUST have exactly one owning component. The owning component is accountable for the capability's behavior, evaluation, and cost. Components come from the canonical agent roster and engine vocabulary of [SPEC_CONVENTIONS §7-§8](../docs/SPEC_CONVENTIONS.md).

| Capability | Owning component | Authoritative spec | Notes |
|------------|------------------|--------------------|-------|
| AI Digital Twin | Twin Agent | [DIGITAL_TWIN](./DIGITAL_TWIN.md) | Persona, disclosure, tier honesty |
| Long-Term Memory | Memory Engine | [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md) | Episodic, semantic, procedural, reflective |
| Semantic Search | Retrieval Agent | [RAG_PIPELINE](./RAG_PIPELINE.md) | Vector search over `EmbeddingChunk` |
| Hybrid Search | Retrieval Agent | [RAG_PIPELINE](./RAG_PIPELINE.md) | Vector plus lexical fusion |
| RAG | Retrieval Agent | [RAG_PIPELINE](./RAG_PIPELINE.md) | End-to-end retrieve-then-generate |
| Knowledge Graph | Graph Agent | [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md) | Entities, `Edge` relations |
| Agentic AI | Orchestrator Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Planning, delegation, budgets |
| Voice AI | Ingestion Agent (transcription), Twin Agent (interactive, future) | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Interactive voice deferred, see §8 |
| Vision AI | Ingestion Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Image captioning, OCR at ingest |
| Document Understanding | Ingestion Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Parsing, structure extraction |
| Code Understanding | Ingestion Agent (parse), Retrieval Agent (query) | [RAG_PIPELINE](./RAG_PIPELINE.md) | Symbol-aware chunking |
| Project Assistant | Mentor Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Project-scoped Q&A and planning |
| Career Advisor | Mentor Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Grounded in `Skill`, `Goal`, `Achievement` |
| Research Assistant | Research Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | External research, new `Source` records |
| Writing Assistant | Writing Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Voice replication rules in [DIGITAL_TWIN](./DIGITAL_TWIN.md) |
| Presentation Generator | Writing Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Outline and slide content, no rendering |
| Learning Coach | Mentor Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Learning plans from `Lesson`, `Certification` |
| Mentorship AI | Mentor Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | P1-audience coaching mode |
| Timeline Explorer | Timeline Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Chronology over `Event` records |
| Project Explorer | Graph Agent | [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md) | `Project` neighborhood navigation |
| Question Answering | Retrieval Agent | [RAG_PIPELINE](./RAG_PIPELINE.md) | Cited, tier-aware answers |
| Natural Language Search | Retrieval Agent | [RAG_PIPELINE](./RAG_PIPELINE.md) | Query understanding front end |
| Recommendation Engine | Curation Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | Surfacing related items via memory signals |
| Context Engine | Retrieval Agent | This document (§4.4) and [RAG_PIPELINE](./RAG_PIPELINE.md) | Context assembly and budgeting |
| Memory Engine | Reflection Agent (write), Memory Engine service (store) | [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md) | `MemoryRecord` lifecycle |
| Reflection Engine | Reflection Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md) | Periodic synthesis, consolidation |
| Source Verification Engine | Verification Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | `Claim` tier assignment, FR-VER group |
| Citation Engine | Verification Agent | [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), [RAG_PIPELINE](./RAG_PIPELINE.md) | Citation resolution to `Claim`/`Source` |

**AIA-02.** A capability not listed here MUST NOT be shipped without first being added to this map with an owner and a spec reference.

### 4.2 Model router

**AIA-03.** All model calls in the platform MUST pass through a single model-router component. No agent or service calls a provider SDK directly. The router is the only holder of provider credentials.

**AIA-04.** Provider roles, per the baseline default in [SPEC_CONVENTIONS §9](../docs/SPEC_CONVENTIONS.md) (anchored to the owner's self-reported 🟡 platform experience in MASTER_CONTEXT §5, recorded here as a design decision, not a biographical fact):

| Provider | Role | Typical assignment |
|----------|------|--------------------|
| Anthropic Claude API | Primary | Twin persona, long-form reasoning, generation with citations, agent planning |
| Google Gemini API | Routed alternate | Vision and document understanding, very long context ingestion, multimodal parsing |
| Groq API | Routed alternate | High-throughput low-latency mechanical tasks: classification, tagging, extraction, query expansion |

**AIA-05.** Routing policy: the router selects a model per request using, in priority order:

1. **Task class.** Every request declares one of: `persona_generation`, `reasoning`, `extraction`, `classification`, `summarization`, `embedding`, `vision`, `transcription`, `rerank`.
2. **Capability constraints.** Required modality (image, audio), required context length, required structured-output support. A model lacking a required capability is excluded.
3. **Quality floor.** Each task class declares a minimum model tier (frontier, mid, small). Persona and cited generation MUST use frontier tier.
4. **Cost.** Among qualifying models, prefer the cheapest that meets the quality floor.
5. **Latency.** Interactive requests carry a latency budget; batch jobs do not. Latency-critical mechanical tasks prefer the Groq route.

**AIA-06.** Fallback rules: on provider error, rate limit, or timeout, the router retries once on the same model, then fails over to the next qualifying model in the routing table. Persona and cited-generation requests MUST NOT silently fail over to a model below the frontier quality floor; if no qualifying model is available the request returns a degraded-service error rather than a lower-quality answer. Every fallback event is written to `AuditLogEntry` and to the `AgentRun` record.

**AIA-07.** Model version pinning: production traffic runs only on exact pinned model versions per task class, held in a versioned routing configuration. Aliases that auto-track "latest" are forbidden in production. This is the engineering analog of the MASTER_CONTEXT §0 never-upgrade rule: nothing changes silently.

**AIA-08.** Model upgrade policy: adopting a new model version requires (a) running the full regression evaluation suite of §4.6 on the candidate, (b) meeting or exceeding the incumbent on groundedness, citation precision, and tier discipline, (c) owner sign-off recorded as an ADR in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), and (d) a rollback path retained for 30 days.

### 4.3 Embedding strategy

**AIA-09.** Embedding model choice is an open decision:

> TODO(decision): select the embedding model (provider-hosted vs open-weight self-hosted), balancing quality, cost per million tokens, dimension size, and decades-long availability. Decision to be recorded as an ADR in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md).

**AIA-10.** Dimensioning: the chosen model SHOULD produce vectors of 1536 dimensions or fewer to keep pgvector index size and query cost manageable; if the model supports Matryoshka-style truncation, the stored dimension is fixed in configuration and recorded with the index. One embedding space is used platform-wide per embedding model version; text and transcript modalities share it, image embeddings (if adopted) form a separate named space.

**AIA-11.** Every `EmbeddingChunk` row records `embedding_model` and `embedding_model_version`. Vectors from different model versions are never compared against each other.

**AIA-12.** Re-embedding policy on model change: migrations use a dual-index strategy. The new index is built in the background from source artifacts (never from old vectors), validated against the retrieval evaluation set of §4.6, then atomically switched; the old index is retained until the next full backup cycle completes (see [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)). Source artifacts are the durable asset; embeddings are always treated as a rebuildable cache.

### 4.4 Context engineering

**AIA-13.** Context window budgeting: every request class has a declared token budget split across fixed shares. Defaults (tunable per model):

| Layer | Share of input budget | Content |
|-------|----------------------|---------|
| System layers (L1-L3) | up to 10% | Platform, provenance, persona prompts |
| Task instructions (L4) | up to 5% | Agent- and request-specific instructions |
| Retrieved context (L5) | up to 55% | RAG chunks with provenance metadata |
| Memory (L6) | up to 10% | Relevant `MemoryRecord` summaries |
| Conversation history (L7) | up to 20% | Recent turns, older turns summarized |

**AIA-14.** Retrieval-augmented context assembly follows the rules of [RAG_PIPELINE](./RAG_PIPELINE.md): privacy-tier filtering before assembly, deduplication, source diversity, recency and importance weighting via the memory system.

**AIA-15.** System prompt layering is fixed and ordered; later layers can never override earlier ones:

```
L1 Platform rules      immutable safety, privacy, and refusal rules
L2 Provenance rules    tier-aware honesty: attribute 🟡, flag 🔴, never upgrade
L3 Persona             Twin persona (only when the Twin Agent is active)
L4 Task instructions   the current agent's task framing
```

L1 and L2 are identical across all agents. L3 is defined solely by [DIGITAL_TWIN](./DIGITAL_TWIN.md). Retrieved corpus content is never placed in L1-L4; it enters only as clearly delimited data (see AIA-17).

### 4.5 Safety and grounding policy

**AIA-16.** Tier-aware honesty (platform-wide invariant): any output that states a biographical or factual claim about Linford MUST reflect the claim's confidence tier from the `Claim` record. ✅ claims may be asserted with citation. 🟡 claims are attributed ("Linford reports that...", "self-reported"). 🔴 claims are either omitted or presented as unverified with a pointer to the verification queue (MASTER_CONTEXT §12). No pipeline stage may upgrade a tier.

**AIA-17.** Prompt injection defenses for ingested content:

1. All retrieved or ingested text enters the prompt inside clearly delimited data blocks labeled as untrusted content; L1 instructs the model that data blocks carry no instructions.
2. Instruction-like patterns in ingested content ("ignore previous instructions", tool-call syntax, system-prompt mimicry) are detected at ingestion by the Curation Agent and flagged on the `EmbeddingChunk` metadata; flagged chunks are still retrievable but carry a warning label in context.
3. Agents processing untrusted content run with least-privilege tool access: retrieval-derived content can never trigger write actions, outbound communication, or privacy-tier changes.
4. Cross-tier exfiltration is blocked structurally: tier filtering happens before context assembly, so injected instructions cannot request content above the session's tier ceiling.

**AIA-18.** PII handling: content is governed by privacy tiers P0-P3 ([SPEC_CONVENTIONS §5](../docs/SPEC_CONVENTIONS.md)). Third-party PII (named collaborators, mentees) defaults to P1 or stricter. P0-facing outputs pass a PII screen that blocks contact details, precise addresses, and financial or identity numbers regardless of source tier. Provider data-retention settings MUST be configured for zero training-data retention where the provider offers it; see [PRIVACY](../security/PRIVACY.md).

**AIA-19.** Refusal policy: the AI layer refuses (with a stated reason and, where possible, a safe alternative) requests to: fabricate facts about Linford or others, present 🟡/🔴 claims as established, reveal content above the caller's tier ceiling, impersonate Linford in outbound communication, produce medical, legal, or financial advice in Linford's name, or make commitments on his behalf (full twin-specific rails in [DIGITAL_TWIN](./DIGITAL_TWIN.md)). The refusal text states what is missing, it does not bluff.

### 4.6 Evaluation framework

**AIA-20.** Golden question sets: a curated, versioned evaluation corpus maintained under the testing strategy of [TESTING](../testing/TESTING.md), containing at minimum:

| Set | Contents | Primary metric |
|-----|----------|----------------|
| Grounded QA | Questions answerable from the corpus, with reference answers and expected citations | Groundedness, citation precision and recall |
| Negative set | Questions NOT answerable from the corpus | Correct "not in the corpus" rate (target: no hallucinated answers) |
| Tier discipline | Questions probing 🟡 and 🔴 claims (for example the flagged achievements in MASTER_CONTEXT §7) | Tier-correct phrasing rate |
| Persona fidelity | Prompts exercising twin voice and boundaries | Owner-rated fidelity, disclosure compliance |
| Injection suite | Adversarial documents and queries | Injection resistance rate |
| Retrieval set | Query-to-relevant-chunk labels | Recall@k, nDCG |

**AIA-21.** Groundedness is measured as the share of generated factual statements traceable to a retrieved chunk; citation precision as the share of citations that actually support the attached statement. Both are scored by an LLM judge with periodic human audit of judge accuracy.

**AIA-22.** Regression evaluations run: before any model version upgrade (AIA-08), before any change to L1/L2 prompts, chunking, or retrieval parameters, and on a monthly schedule against production configuration. Results are stored and trended; a regression beyond agreed thresholds blocks the change.

### 4.7 Cost management

**AIA-23.** Token budgets: every request class carries a maximum input and output token budget enforced by the router; every `AgentRun` carries a total budget set by the Orchestrator Agent, which terminates runs that exceed it. Budgets and spend are visible in observability dashboards ([OBSERVABILITY](../deployment/OBSERVABILITY.md)).

**AIA-24.** Caching: (a) provider prompt caching for the stable L1-L3 prefix on every call; (b) embedding cache keyed by content hash so unchanged content is never re-embedded; (c) retrieval result cache for repeated queries within a session; (d) answer cache for P0 public twin FAQs with citation-aware invalidation when underlying content changes.

**AIA-25.** Mechanical tasks (classification, tagging, entity extraction, query expansion, summarization of low-stakes content) are routed to cheaper small or mid tier models per AIA-05. Frontier models are reserved for persona generation, cited answers, planning, and verification judgments.

**AIA-26.** Batch processing: re-embedding, reflection, and periodic consolidation jobs run through provider batch endpoints where available, at off-peak schedules, with per-job cost caps.

## 5. Acceptance Criteria

1. Every capability listed in §4.1 resolves to exactly one owning component and one authoritative spec; a review of the map finds no orphaned or double-owned capability.
2. A provider outage drill shows the router failing over per AIA-06, with fallback events visible in `AuditLogEntry`, and persona requests refusing rather than degrading below the frontier floor.
3. Production configuration inspection shows exact pinned model versions for every task class; no "latest" aliases.
4. A simulated embedding model migration completes via the dual-index path of AIA-12 with retrieval evaluation passing before switchover and zero user-visible downtime.
5. The tier-discipline evaluation set passes with 100% of 🔴 claims flagged or omitted and 100% of 🟡 claims attributed, measured on the golden sets of §4.6.
6. The injection suite shows no case where ingested content triggers a tool action, tier escalation, or instruction override.
7. Monthly cost reports show per-request-class token spend within declared budgets, and mechanical task traffic routed off frontier models.

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): confidence tiers and the never-upgrade rule (§0), stack anchors (§5).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): privacy tiers, canonical entities (`Claim`, `Source`, `EmbeddingChunk`, `MemoryRecord`, `AgentRun`), agent roster, baseline defaults.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): agent responsibilities and orchestration budgets.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): memory types feeding context layer L6.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): storage of chunks, claims, sources, audit records.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): response contracts, streaming, citation payloads.
- [SECURITY](../security/SECURITY.md) and [PRIVACY](../security/PRIVACY.md): credential handling, data governance, provider retention settings.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Provider discontinuation or pricing shock over a decades-long horizon | Loss of primary model path | Router abstraction, three-provider policy, exportable prompts and evals, embeddings rebuildable from source |
| Silent model behavior drift | Persona or grounding regressions | Version pinning (AIA-07), upgrade gate (AIA-08), monthly regression runs |
| Prompt injection via ingested third-party content | Data exfiltration, false claims | AIA-17 layered defenses, least-privilege tools, pre-assembly tier filtering |
| Hallucinated biographical facts | Reputational harm to a living person | Tier-aware honesty (AIA-16), negative-set evaluation, refusal policy |
| Embedding model deprecation | Degraded retrieval | Versioned vectors, dual-index migration, source-artifact rebuild guarantee |
| LLM-judge miscalibration in evals | False confidence in quality | Periodic human audit of judge scores (AIA-21) |
| Cost creep from frontier-model overuse | Unsustainable spend | Task-class routing, budgets, caching, batch endpoints |

## 8. Future Enhancements

- Interactive Voice AI for the twin (real-time speech), deferred until the text twin passes persona-fidelity gates; tracked in [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md).
- Dedicated image embedding space for visual memory search.
- Self-hosted open-weight fallback model for offline Legacy Vault question answering.
- Automatic routing-policy tuning from observed quality and cost telemetry.
- Fine-tuned or distilled persona model, only if prompt-layer persona proves insufficient and only under the evaluation gates of §4.6.

## 9. Examples

Routing decision (illustrative):

```json
{
  "request_id": "req_01H...",
  "task_class": "persona_generation",
  "constraints": { "modality": "text", "min_context": 32000, "latency_ms_budget": 8000 },
  "route": {
    "provider": "anthropic",
    "model": "pinned frontier version per routing config",
    "reason": "task class requires frontier floor; primary provider healthy"
  },
  "fallback_chain": ["anthropic retry", "gemini frontier equivalent", "degraded-service error"],
  "budgets": { "input_tokens": 24000, "output_tokens": 2000 }
}
```

Layered prompt order (schematic):

```
+----------------------------------------------------------+
| L1 Platform rules (safety, privacy, refusal)             |
| L2 Provenance rules (tier-aware honesty)                 |
| L3 Persona (Twin Agent only)                             |
| L4 Task instructions                                     |
|----------------------------------------------------------|
| L5 Retrieved context [UNTRUSTED DATA blocks + metadata]  |
| L6 Memory summaries                                      |
| L7 Conversation history                                  |
+----------------------------------------------------------+
```

Tier-aware output phrasing (illustrative): a question about SpazaLink's SA Startup Week placement (🔴 in MASTER_CONTEXT §7) yields: "Linford has reported a 3rd place result for SpazaLink at SA Startup Week 2026, but this is flagged as unverified in the knowledge base and is pending confirmation." It never yields "SpazaLink won 3rd place."

## 10. Open Questions

- > TODO(decision): embedding model selection (AIA-09), including dimension and hosting model.
- > TODO(decision): which LLM-judge model scores groundedness, and how often human audits sample its output.
- > TODO(decision): exact frontier, mid, and small tier assignments per provider at launch; belongs in the routing configuration ADR.
- > TODO(verify): provider zero-retention guarantees and data-processing terms for all three providers before any P1+ content is sent (coordinates with [PRIVACY](../security/PRIVACY.md)).
- Should the negative-set "not in the corpus" behavior be tunable per audience (stricter for public P0 twin than for owner mode)?

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tiers), §2 (values), §5 (stack), §7 (flagged achievements), §12 (verification queue).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §5 (privacy tiers), §6 (Claim/Source), §7 (agent roster), §9 (baseline defaults).

## 12. Related Specifications

- [RAG_PIPELINE](./RAG_PIPELINE.md): the retrieval and generation pipeline this document governs.
- [DIGITAL_TWIN](./DIGITAL_TWIN.md): persona layer L3 and twin-specific rails.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): the agents that consume the router.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): memory feeding the context engine.
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md): entity backbone for graph-aware capabilities.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): externally visible AI response contracts.
- [OBSERVABILITY](../deployment/OBSERVABILITY.md): routing, cost, and evaluation telemetry.
- [TESTING](../testing/TESTING.md): evaluation harness ownership.
