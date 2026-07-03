# SPEC_CONVENTIONS.md
### Authoring Conventions for the Legacy Specification Repository

> **Status:** Normative. Every specification in this repository MUST follow this document.
> **Audience:** Human contributors and AI sessions authoring or revising specifications.
> **Canonical context:** [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) is the single source of truth about Linford Musiyambodza. It is immutable. Specifications never restate personal facts without preserving its confidence tiers.

---

## 1. Purpose

This document defines the shared template, identifier schemes, canonical vocabulary, and baseline architecture decisions used across every specification in this repository. It exists so that forty-plus documents written by different sessions read as one coherent system and can be implemented without redesign.

## 2. Non-negotiable rules

1. **MASTER_CONTEXT.md is the only source of truth for facts about Linford.** Do not invent facts. Do not upgrade 🟡 (self-reported) or 🔴 (flagged) claims to established facts. When a fact is needed but missing, write a TODO instead.
2. **Specification only.** This repository contains no application code: no React, no Python, no SQL, no executable API definitions. Illustrative data examples (JSON payloads, table-shaped schema descriptions, natural-language queries) are permitted; implementation code is not.
3. **Confidence tiers are first-class.** The tier system (✅ Verified, 🟡 Self-reported, 🔴 Flagged) from MASTER_CONTEXT §0 carries into the product itself (see the `Claim` entity, §6 below) and into any spec text that references biographical facts.
4. **TODO convention.** Unknowns are recorded as a blockquote in place. Two marker forms exist and no others: `> TODO(verify): <missing fact and where it would come from>` for facts awaiting evidence, and `> TODO(decision): <decision to make and its decision point>` for pending design decisions. Every spec also collects its unknowns in its Open Questions section.
5. **Style.** Clear, direct, production-grade technical prose. No em dashes anywhere in repository content (this mirrors the owner's documented style guide); use commas, colons, or parentheses instead. American English. Sentence-case headings after the title block.

## 3. Mandatory section structure

Every specification document MUST contain these sections, in this order. A section that is genuinely empty states why in one line rather than being omitted.

1. **Purpose**
2. **Goals**
3. **Scope** (in scope and out of scope)
4. **Requirements**
5. **Acceptance Criteria**
6. **Dependencies**
7. **Risks**
8. **Future Enhancements**
9. **Examples**
10. **Open Questions**
11. **References**
12. **Related Specifications**

Documents that are indexes, meta-documents, or narrative anchors (`README.md`, `CHANGELOG.md`, `knowledge/MASTER_CONTEXT.md`, and this conventions document) are exempt. `VISION.md`, `MISSION.md`, and `LEGACY_PRINCIPLES.md` follow the structure with sections interpreted at product level.

Each document begins with a title block:

```markdown
# <FILE_NAME without extension>
### <one-line description>

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | <linked specs> |
```

## 4. Identifier schemes

All requirements, stories, and use cases carry stable IDs. IDs are never renumbered; retired items are marked Deprecated, not deleted.

| Prefix | Meaning | Defined in |
|--------|---------|------------|
| `PR-###` | Product requirement | `specs/PRODUCT_REQUIREMENTS.md` |
| `SYS-###` | System requirement | `specs/SYSTEM_REQUIREMENTS.md` |
| `FR-<DOM>-###` | Functional requirement, grouped by domain code | `specs/FUNCTIONAL_REQUIREMENTS.md` |
| `NFR-###` | Non-functional requirement | `specs/NON_FUNCTIONAL_REQUIREMENTS.md` |
| `PERS-##` | Persona | `specs/USER_PERSONAS.md` |
| `US-###` | User story | `specs/USER_STORIES.md` |
| `UC-###` | Use case | `specs/USE_CASES.md` |
| `FS-###` | Feature specification | `specs/FEATURE_SPECIFICATIONS.md` |
| `ADR-##` | Architecture decision record | `architecture/MASTER_ARCHITECTURE.md` |
| `RISK-##` | Risk register entry | `roadmap/RISKS.md` |
| `TASK-###` | Implementation task | `roadmap/TASKS.md` |

**Domain codes** for `FR-<DOM>-###` and general grouping:

| Code | Domain |
|------|--------|
| ING | Ingestion and capture |
| KG | Knowledge graph |
| MEM | Memory system |
| RAG | Retrieval and RAG pipeline |
| SRCH | Search (semantic, hybrid, natural language) |
| TWIN | Digital twin |
| AGT | Agents and orchestration |
| TL | Timeline engine |
| VER | Verification, provenance, citations |
| API | Public and internal APIs |
| UI | User interface |
| SEC | Security |
| PRIV | Privacy and data governance |
| OPS | Deployment, observability, backup |
| DATA | Database and storage |

Traceability chain: `PR` → `FR`/`NFR` → `FS` → `TASK`, with `US`/`UC` linking personas to `FR`. Every `FS` cites the `FR`s it implements.

## 5. Canonical privacy tiers

Every piece of content in Legacy carries exactly one privacy tier. These names are canonical across all specs.

| Tier | Name | Meaning |
|------|------|---------|
| P0 | Public | Portfolio-grade content, published to the public site |
| P1 | Trusted | Shared with explicitly granted collaborators, mentees, family |
| P2 | Private | Owner only |
| P3 | Sealed | Time-locked or succession-gated (for example journals and prayer reflections released only under defined conditions) |

Default for new content is P2. Nothing moves to a less restrictive tier without an explicit owner action.

## 6. Canonical domain entities

Specs use these entity names exactly (singular, PascalCase). The authoritative attribute-level definition lives in `database/DATABASE_SCHEMA.md`; the relationship semantics live in `knowledge/KNOWLEDGE_GRAPH.md`.

**Knowledge entities:** `Person`, `Organization`, `Project`, `Artifact` (document, photo, video, presentation, code snapshot), `Event`, `Idea`, `Note`, `JournalEntry`, `Conversation` (AI conversation), `Skill`, `Certification`, `Achievement`, `Goal`, `Lesson`, `Book`, `Talk`, `Article`, `Source`, `Claim`, `Tag`, `Collection`, `Edge` (typed relationship between entities).

**System entities:** `User`, `Role`, `Grant`, `PersonalAccessToken`, `MemoryRecord`, `EmbeddingChunk`, `AuditLogEntry`, `IngestionJob`, `AgentRun`.

**Provenance model:** a `Claim` is an atomic factual statement with a confidence tier (`verified`, `self_reported`, `flagged`), linked to one or more `Source` records. The Verification Engine and Citation Engine operate on Claims and Sources. This is the direct productization of MASTER_CONTEXT §0.

## 7. Canonical agent roster

The multi-agent system uses plain functional names (no invented brand lore). Authoritative definitions live in `agents/MULTI_AGENT_ARCHITECTURE.md`.

| Agent | Responsibility |
|-------|----------------|
| Orchestrator Agent | Intent routing, planning, delegation, budget control |
| Ingestion Agent | Capture, parsing, chunking, media handling |
| Curation Agent | Deduplication, tagging, quality scoring |
| Graph Agent | Entity and relationship extraction, graph maintenance |
| Timeline Agent | Event extraction and chronology |
| Retrieval Agent | Semantic and hybrid search, RAG context assembly |
| Twin Agent | Digital twin persona and voice |
| Mentor Agent | Career, learning, and mentorship coaching |
| Research Agent | External research and source gathering |
| Writing Agent | Articles, presentations, summaries |
| Verification Agent | Source verification, confidence tiers, citations |
| Reflection Agent | Periodic synthesis, lessons learned, memory consolidation |

> Note: the Hermes nine-agent ecosystem described in MASTER_CONTEXT §6 is a separate, self-reported Linfy Tech design. Legacy's roster is its own design and must not be presented as Hermes.

## 8. Canonical memory vocabulary

Defined authoritatively in `memory/MEMORY_SYSTEM.md`: `working memory` (session-scoped context), and four long-term memory types: `episodic`, `semantic`, `procedural`, `reflective`. Long-term memory is persisted as `MemoryRecord` rows with vector embeddings.

## 9. Baseline architecture decisions (proposed defaults)

These defaults align with the owner's demonstrated and self-reported stack (MASTER_CONTEXT §5). They are recorded as ADRs in `architecture/MASTER_ARCHITECTURE.md`. They are design decisions, not facts about Linford, and each carries a confirmation TODO where relevant.

| Area | Default | Rationale anchor |
|------|---------|------------------|
| Web frontend | Next.js with React and TypeScript | ✅ §5 languages and frameworks |
| Backend API | FastAPI (Python) | ✅ §5 backend |
| Primary datastore | PostgreSQL via Supabase, with pgvector for embeddings, Supabase Storage for media | 🟡 §5 data and infra |
| Knowledge graph | Modeled natively in PostgreSQL (node and edge tables) for v1; dedicated graph database is a deferred decision gate | Design decision |
| LLM providers | Anthropic Claude API primary; Google Gemini API and Groq API behind a model-routing abstraction | 🟡 §5 AI platform |
| Tool integrations | MCP-based integrations (Supabase MCP, Tavily MCP) | 🟡 §5 |
| API style | REST JSON under `/v1`, Server-Sent Events for AI streaming, API-first | Design decision |
| AuthN/AuthZ | OAuth 2.0 / OIDC plus personal access tokens; RBAC with per-item privacy tiers | Design decision |
| Offline capability | Versioned "Legacy Vault" export (Markdown, JSON, media manifest) enabling local read-only access | Design decision, honors the Offline Capable principle |
| Mobile | Out of scope for v1; Android (Kotlin, Jetpack Compose) is a future enhancement | ✅ §5 skill exists; scoping decision |

## 10. Repository map

| Path | Content |
|------|---------|
| `README.md` | Repository index and reading order |
| `docs/` | VISION, MISSION, LEGACY_PRINCIPLES, SPEC_CONVENTIONS |
| `specs/` | Product, system, functional, non-functional requirements; personas, stories, use cases, feature specs |
| `architecture/` | MASTER_ARCHITECTURE (system architecture and ADRs) |
| `database/` | DATABASE_SCHEMA (logical schema, no SQL) |
| `api/` | API_SPECIFICATION (resource model, no executable definitions) |
| `ai/` | AI_ARCHITECTURE, RAG_PIPELINE, DIGITAL_TWIN |
| `agents/` | MULTI_AGENT_ARCHITECTURE |
| `knowledge/` | MASTER_CONTEXT (immutable), KNOWLEDGE_GRAPH |
| `memory/` | MEMORY_SYSTEM |
| `security/` | SECURITY, PRIVACY, AUTHENTICATION, AUTHORIZATION |
| `deployment/` | DEPLOYMENT, CI_CD, OBSERVABILITY, BACKUP_AND_RECOVERY |
| `testing/` | TESTING, QUALITY_ASSURANCE |
| `ui/` | UI_UX, DESIGN_SYSTEM, ACCESSIBILITY |
| `roadmap/` | ROADMAP, TASKS, RISKS, FUTURE_FEATURES |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Repository meta |

Cross-references between specs use relative links, for example `[MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)`.

## 11. Open Questions

- Should ADRs eventually split into one file per decision under `architecture/decisions/`? Deferred until the ADR count exceeds roughly fifteen.

## 12. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md), the canonical personal context, especially §0 (confidence tiers), §5 (technical expertise), §12 (verification queue).

## 13. Related Specifications

- All documents in this repository. Start with [`README.md`](../README.md) and [`architecture/MASTER_ARCHITECTURE.md`](../architecture/MASTER_ARCHITECTURE.md).
