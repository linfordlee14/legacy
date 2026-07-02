# MULTI_AGENT_ARCHITECTURE
### The twelve-agent AI system that operates the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md), [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [AUTHORIZATION](../security/AUTHORIZATION.md) |

---

## 1. Purpose

This document specifies Legacy's multi-agent system: the twelve specialized agents, how the Orchestrator coordinates them, how they communicate, what they may and may not do, and how every action they take remains auditable and human-governed. The agents are the platform's workforce; the owner is its government.

> Relationship to Hermes: MASTER_CONTEXT §6 describes a nine-agent "Hermes" ecosystem (Hermes orchestrator; Maverick, Oracle, Scribe specialists) as a self-reported (🟡) Linfy Tech Solutions design. Legacy's agent roster is an independent design with plain functional names. The two must never be conflated in documentation or product copy.

## 2. Goals

- Define each agent's mission, inputs, outputs, tools, and autonomy level precisely enough to implement.
- Guarantee that no agent can violate the platform's two prime invariants: privacy ceilings and confidence-tier discipline.
- Keep humans in the loop exactly where it matters (irreversible or outward-facing actions) and out of the loop where it does not (routine internal processing).
- Make every agent action traceable, budgeted, and interruptible.

## 3. Scope

**In scope:** agent roster, orchestration model, communication schema, autonomy and approval policy, safety rails, budgets, failure handling, and evaluation.

**Out of scope:** model selection and routing (see [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md)), retrieval mechanics (see [RAG_PIPELINE](../ai/RAG_PIPELINE.md)), twin persona rules (see [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md)).

## 4. Requirements

### 4.1 Agent roster

Autonomy levels: **A0** fully automatic (internal, reversible); **A1** automatic with owner-visible reporting; **A2** proposes, owner approves before effect.

| Agent | Mission | Key inputs | Key outputs | Tools | Autonomy |
|-------|---------|-----------|-------------|-------|----------|
| Orchestrator | Decompose tasks, delegate, track budgets, enforce gates | Owner tasks, schedules | AgentRun plans, delegations | Task queue, all agent interfaces | A1 |
| Ingestion | Parse, normalize, chunk all incoming content | IngestionJobs, uploads, connectors | Artifacts, entities, chunks | Parsers, OCR, transcription, GitHub connector, storage | A1 |
| Curation | Deduplicate, tag, quality-score content | New entities and chunks | Tags, dedup links, quality flags | Search, similarity, taxonomy | A0 for tags, A2 for merges |
| Graph | Extract entities and relationships, maintain the graph | Curated content | Nodes, edges, merge proposals | Entity extraction, graph store | A1 for high-confidence, A2 for merges |
| Timeline | Extract and order dated events | Curated content | Events, chronology links | Date parsing, graph store | A1 |
| Retrieval | Serve search and assemble RAG context | Queries | Ranked, tier-filtered context | Vector and lexical indexes | A0 |
| Twin | Converse as the owner's AI representation | Conversations, retrieval context | Disclosed twin responses | Retrieval, memory | A1 (talk), A2 (anything outward) |
| Mentor | Career and learning coaching from corpus evidence | Owner questions, goals | Advice with evidence, goal tracking | Retrieval, memory | A1 |
| Research | Gather external evidence and material | Research tasks | Source records, findings | Web research via MCP (Tavily MCP per convention defaults), fetch | A1, external calls logged |
| Writing | Draft articles, talks, presentations in the owner's voice | Corpus material, briefs | Drafts with citations | Retrieval, templates | A2 (all output owner-reviewed) |
| Verification | Verify claims, manage tiers, maintain citations | Verification queue, new claims | Evidence packets, tier-change proposals | Research results, source archive | A2 (tier changes owner-applied) |
| Reflection | Consolidate memory, synthesize lessons, run rollups | Memory records, journals (unsealed) | Semantic memories, rollups | Memory store, retrieval | A1 |

### 4.2 Orchestration model

1. A task enters via `POST /v1/agents/tasks` (owner action or approved schedule).
2. The Orchestrator produces a plan: steps, assigned agents, sequencing (sequential where outputs chain, parallel where independent), a token and cost budget, and the list of steps requiring approval (every A2 effect).
3. Steps execute; each records inputs, outputs, tool calls, model calls, tokens, and cost into the `AgentRun` trace.
4. A2 steps pause the run and surface an approval request (workspace notification and approval queue). Approval or rejection resumes or prunes the plan.
5. Completion produces a result summary plus the full trace, both retained per the audit policy.

Scheduled work (nightly ingestion sweeps, weekly reflection rollups, verification queue refresh) follows the same path with pre-approved plans whose scope is fixed; any step outside the pre-approved scope escalates to A2.

### 4.3 Communication schema

Agents exchange task messages through the Orchestrator (hub and spoke; no hidden peer channels). Illustrative message:

```json
{
  "run_id": "run_0142",
  "step_id": "step_03",
  "from": "orchestrator",
  "to": "verification",
  "intent": "verify_claim",
  "payload": { "claim_id": "clm_204", "evidence_refs": ["src_88", "src_91"] },
  "constraints": { "max_tokens": 20000, "deadline_s": 600, "ceiling": "P2" },
  "provenance_rules": "attribute_self_reported; never_upgrade"
}
```

> TODO(decision): MASTER_CONTEXT §8 records DeepLearning.AI coursework on the A2A protocol (🟡). Evaluate A2A as the wire format for these messages before Phase 4 implementation; adopt only if it simplifies interoperability without weakening the hub-and-spoke audit point.

### 4.4 Safety rails

- **Ceiling inheritance.** Every run carries the invoking principal's privacy ceiling; no agent, tool call, or sub-delegation may exceed it (NFR-031). P3 content is invisible to all agents except the vault path, which never sends it to models (NFR-032).
- **Tool allowlists.** Each agent has a fixed tool set (table above). Tool calls outside the allowlist fail closed and alert.
- **Tier discipline.** No agent may change a confidence tier. The Verification Agent proposes; only the owner applies (FS-009 in [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md)).
- **Instruction and data separation.** Content retrieved from the corpus or the web is data, never instructions. Agent prompts wrap external content in clearly delimited, non-executable context, and injection-resistance tests are part of the eval suite (see [TESTING](../testing/TESTING.md)).
- **Outward-action gate.** Publishing, outbound communication of any kind, deletions, tier changes, and grant changes are always A2, regardless of which agent proposes them.
- **Budget caps.** Per-run and per-day token and cost caps; exceeding a cap pauses the run in a resumable state (never silent truncation of results).

### 4.5 Auditability and failure handling

- Every run is an `AgentRun` with a complete step trace, inspectable via `GET /v1/agents/runs/{id}` and retained per [OBSERVABILITY](../deployment/OBSERVABILITY.md).
- Failures retry with backoff (3 attempts for transient tool errors); persistent failures move the step to a dead-letter state with owner notification; completed sibling steps are preserved (partial results are results).
- A kill switch halts all agent execution platform-wide; scheduled work resumes only on explicit re-enable.

## 5. Acceptance Criteria

- Each of the twelve agents has an implementable definition (mission, I/O, tools, autonomy) and at least one scenario in [USE_CASES](../specs/USE_CASES.md) or [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md) exercising it.
- Authorization tests prove ceiling inheritance and tool allowlists (attempted violations fail closed and are logged).
- The tier-discipline invariant has an automated eval: agents attempting tier changes are blocked in 100 percent of test scenarios.
- Approval-gate tests prove every A2 action pauses for owner decision and that rejection prunes cleanly.
- A full `AgentRun` trace reconstructs any run's decisions, costs, and outputs without gaps.

## 6. Dependencies

- [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md): model routing, context engineering, and safety policy the agents run on.
- [AUTHORIZATION](../security/AUTHORIZATION.md): ceilings, roles, and the agent service identities.
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): the Reflection Agent's store and everyone's working memory.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): task, run, and approval endpoints.
- MCP tool servers (Supabase MCP, Tavily MCP per convention defaults, 🟡 anchored): the Research and Ingestion Agents' external tools.

## 7. Risks

- Prompt injection through ingested or researched content is the highest-likelihood attack path; mitigated by instruction/data separation, allowlists, and the outward-action gate.
- Approval fatigue could push the owner to over-approve; mitigated by batching approvals, clear diffs of proposed effects, and keeping A2 scope tight.
- Agent cost runaway; mitigated by hard caps and the budget alerts in the FR-OPS group.
- Orchestrator becomes a single point of failure; mitigated by resumable run state and the kill switch's independent path.
- Conflating Legacy's agents with Hermes in public materials would misstate a 🟡 claim; mitigated by the naming rule in §1.

## 8. Future Enhancements

- Adoption of A2A or a successor protocol for inter-agent messages (pending the §4.3 decision).
- Learned routing: using AgentRun outcomes to improve plan quality.
- Trusted-user-facing agents (mentee coaching) after the P1 surface matures.
- Local-model execution for A0 agents to cut cost and improve privacy (pairs with the on-device enhancement in [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)).

## 9. Examples

The owner files: "Prepare a talk outline about lessons from my conservation projects." The Orchestrator plans: Retrieval assembles the conservation neighborhood (WildGuard AI, RhinoShield ✅; RhinoGuardians 🟡 labeled as self-reported); Reflection surfaces related lessons; Writing drafts an outline with citations, phrasing the 🟡 project as "a project Linford has described building"; the draft lands as an A2 approval. The owner edits one section, approves, and the outline is stored as a P2 draft. Total cost, every model call, and both agent handoffs are visible in the run trace.

## 10. Open Questions

- A2A adoption decision (§4.3 TODO) before Phase 4.
- Should scheduled reflection rollups be A0 instead of A1 once trust is established? Revisit after three months of production use.
- Does the Mentor Agent need a distinct voice from the Twin Agent? Currently yes (advisor voice, not persona voice); validate with the owner.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §5 (agentic AI and A2A exposure, 🟡), §6 (Hermes, 🟡), §8 (coursework, 🟡).
- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) §7 (canonical roster).

## 12. Related Specifications

- [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md), [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md)
- [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md), [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md)
- [AUTHORIZATION](../security/AUTHORIZATION.md), [SECURITY](../security/SECURITY.md), [OBSERVABILITY](../deployment/OBSERVABILITY.md)
- [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (FR-AGT group), [TESTING](../testing/TESTING.md)
