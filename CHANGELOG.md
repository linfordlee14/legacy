# CHANGELOG
### Version history of the Legacy specification repository

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-04 |

All notable changes to this specification repository are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and versioning follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) as applied to specifications: major for restructuring that breaks references or ID meaning, minor for new documents or requirements, patch for corrections that change no requirement's meaning. See [CONTRIBUTING](CONTRIBUTING.md) for how entries are added.

This file is exempt from the 12-section specification structure per [SPEC_CONVENTIONS](docs/SPEC_CONVENTIONS.md).

## [Unreleased]

Nothing yet.

## [0.4.0] - 2026-07-04

Implementation-phase specification synchronization (MVP-023), cut at the
v0.2.0-alpha implementation milestone (BUILD_ORDER steps 1 to 21 complete;
release notes in `infra/releases/v0.2.0-alpha.md`). Every entry below was
disclosed at the step that discovered it; the implementation carries zero
undocumented deviations.

### Added

- `api/API_SPECIFICATION.md` §4.4: `POST /v1/verification/claims/{id}/evidence` (owner attaches an evidence Source, supports or contradicts, audit-logged), and the resolve row now states its step-up requirement. Defect: FS-009, the UI_UX queue screen ("attach evidence"), and MVP-020 make owner evidence attachment normative, but the contract offered only the agent-scoped proposals surface (agent automation is explicitly out of MVP-020 scope).
- `database/DATABASE_SCHEMA.md` §4.6 `Revision`: documented the snapshot shape for Claim tier resolutions (tier fields plus privacy_tier). Clarification supporting MVP-020's reuse of revision history; the shape was defined only for the PATCH-editable content collections.

- `architecture/MASTER_ARCHITECTURE.md` ADR-17: hybrid retrieval fuses by reciprocal rank fusion (k = 60 default, k and pool sizes configuration-defined; lexical and semantic retrieval stay independent before fusion). Resolves the fusion `TODO(decision)` in `ai/RAG_PIPELINE.md` §10; weighted score fusion is re-evaluated at a gate review if the retrieval label set grows enough to calibrate score normalization.
- `architecture/MASTER_ARCHITECTURE.md` ADR-16: the platform embedding model is pinned to exactly `gemini-embedding-001` at `output_dimensionality` 1536 (version string `gemini-embedding-001:1536`, L2-normalized vectors, cosine distance), verified against the official Gemini API documentation on 2026-07-04. Resolves the AIA-09 `TODO(decision)` in `ai/AI_ARCHITECTURE.md` (now pointing at the ADR), narrows ADR-06's `TODO(verify)` to provider accounts, updates the RAG-06 parenthetical, and closes the matching open question. Model changes henceforth follow AIA-08/AIA-12 and require a new ADR.
- `database/DATABASE_SCHEMA.md` §4.6 `EmbeddingChunk`: `heading_path`, `language`, and `injection_flag` columns. Defect: RAG-05 makes the chunk provenance packet normative (heading or symbol path, language, injection-flag status travel with every chunk) and RAG-24 requires heading-path citation locators, but the entity defined no columns to hold them.

- `database/DATABASE_SCHEMA.md` §4.6: `Revision` system entity (SPEC_CONVENTIONS §6 entity list updated), and the §4.8 redaction rule now strikes Revision snapshots in the same transaction. Defect: API_SPECIFICATION §4.4 (`GET /v1/{collection}/{id}/revisions`), UI_UX (autosave revision history; soft delete with undo), and FEATURE_SPECIFICATIONS F11 (last-write-wins with revision history) all made revision history normative, but no storage entity existed; DATABASE_SCHEMA §5 requires a spec change before any new table.
- `api/API_SPECIFICATION.md` §4.4: `POST /v1/{collection}/{id}/restore` (undo a soft delete while the row is retained per DATABASE_SCHEMA §4.8). Defect: soft delete with undo was normative (UI_UX destructive-action rules; NFR-022; MVP-015 acceptance) but the contract offered no undo surface.

- `database/DATABASE_SCHEMA.md` §4.6: `PersonalAccessToken` system entity (and the §4.2 exception list plus the SPEC_CONVENTIONS §6 entity list updated). Defect: AUTHENTICATION §4.3 and API_SPECIFICATION §4.5 mandate scoped, expiring, revocable, audited PATs, but no entity existed to store them; DATABASE_SCHEMA §5 requires a spec change before any new table.
- `api/API_SPECIFICATION.md` §4.4: personal access token lifecycle endpoints (create with step-up returning the secret once, metadata listing, immediate revocation). Defect: PATs were normative in §4.1 and §4.5 with no owner-operable lifecycle surface.

- `.github/workflows/ci.yml` and `scripts/check_specs.py`: the seven specification checks of `deployment/CI_CD.md` §4.2 are now automated (stages 1 to 6 by script; stage 7 remains reviewer judgment via the PR checklist), together with the applicable §4.3 implementation gates (lint, type check, unit tests, SAST, dependency audit, secret scan, build artifacts) and the CI-04 MASTER_CONTEXT immutability guard. CI-06's manual pre-merge checklist era ends; the checks are required status checks once branch protection is enabled.

- `docs/SPEC_CONVENTIONS.md` §2 rule 4: documented the `> TODO(decision):` marker form for pending design decisions. Defect: the corpus used three marker spellings (decision, and the undocumented decide and design variants) while the convention documented only `TODO(verify)`.

### Fixed

- Normalized all decision-marker spellings to the canonical `TODO(decision)` form in `ai/AI_ARCHITECTURE.md`, `ai/RAG_PIPELINE.md`, `ai/DIGITAL_TWIN.md`, `knowledge/KNOWLEDGE_GRAPH.md`, and `memory/MEMORY_SYSTEM.md` (marker form only, no content changes).

## [0.3.0] - 2026-07-02

GitHub delivery infrastructure.

### Added

- `roadmap/GITHUB_MILESTONES.md`: nine-milestone GitHub strategy (M1 MVP Foundation through M9 Version 1.0) mapped to MVP-### and TASK-### IDs, roadmap phases, and decision gates, with label taxonomy, project board definition, and setup commands.
- `.github/labels.yml`: machine-readable label definitions (type, priority, domain, invariant, workflow groups) mirroring the SPEC_CONVENTIONS domain codes.
- `.github/ISSUE_TEMPLATE/`: issue forms for implementation tasks, bug reports (with privacy notice and invariant checks), feature requests (spec-first routed), and specification changes, plus `config.yml` disabling blank issues.
- `.github/pull_request_template.md`: PR checklist enforcing spec citations, invariant tests, audit and redaction checks, accessibility gates, and CHANGELOG discipline.

## [0.2.0] - 2026-07-02

MVP implementation planning.

### Added

- `roadmap/MVP_PLAN.md`: the smallest production-ready MVP (roadmap Phase 1 plus the M7 search and M8 verification queue milestones), with staged development order, success criteria, and a descope ladder.
- `roadmap/IMPLEMENTATION_TASKS.md`: MVP-001 through MVP-026 engineering tasks with acceptance criteria, dependencies, effort, and priority, each mapped to its parent canonical TASK ID.
- `roadmap/BUILD_ORDER.md`: the strict build sequence (steps 1 to 22 plus stretch S1 to S3), a session protocol for implementation sessions, and the post-MVP continuation order.
- `roadmap/RISKS.md`: RISK-19 (graph extraction quality) and RISK-20 (retrieval quality) added to the register.

### Fixed

- `roadmap/ROADMAP.md`: risk ID cross-references aligned to the canonical numbering in `roadmap/RISKS.md` (the two documents were authored in parallel with divergent numbering); maintenance task range corrected to TASK-001 through TASK-006.

## [0.1.0] - 2026-07-02

Initial specification repository.

### Added

- `docs/`: VISION, MISSION, LEGACY_PRINCIPLES, and the normative SPEC_CONVENTIONS authoring standard.
- `specs/`: product, system, functional, and non-functional requirements; user personas, user stories, use cases, and feature specifications.
- `architecture/`: MASTER_ARCHITECTURE with the system architecture and architecture decision records.
- `database/`: DATABASE_SCHEMA, the logical data model (no SQL).
- `api/`: API_SPECIFICATION, the resource model and endpoint semantics (no executable definitions).
- `ai/`: AI_ARCHITECTURE, RAG_PIPELINE, and DIGITAL_TWIN specifications.
- `agents/`: MULTI_AGENT_ARCHITECTURE defining the canonical twelve-agent roster.
- `knowledge/`: MASTER_CONTEXT (immutable canonical context for Linford Musiyambodza) and KNOWLEDGE_GRAPH.
- `memory/`: MEMORY_SYSTEM covering working memory and the four long-term memory types.
- `security/`: SECURITY, PRIVACY, AUTHENTICATION, and AUTHORIZATION, including the P0 to P3 privacy tier model.
- `deployment/`: DEPLOYMENT, CI_CD, OBSERVABILITY, and BACKUP_AND_RECOVERY.
- `testing/`: TESTING and QUALITY_ASSURANCE.
- `ui/`: UI_UX, DESIGN_SYSTEM, and ACCESSIBILITY.
- `roadmap/`: ROADMAP, TASKS, RISKS, and FUTURE_FEATURES.
- Repository meta: README index, CONTRIBUTING workflow, and this CHANGELOG.
