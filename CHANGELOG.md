# CHANGELOG
### Version history of the Legacy specification repository

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |

All notable changes to this specification repository are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and versioning follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) as applied to specifications: major for restructuring that breaks references or ID meaning, minor for new documents or requirements, patch for corrections that change no requirement's meaning. See [CONTRIBUTING](CONTRIBUTING.md) for how entries are added.

This file is exempt from the 12-section specification structure per [SPEC_CONVENTIONS](docs/SPEC_CONVENTIONS.md).

## [Unreleased]

- Nothing yet.

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
