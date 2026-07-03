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

### Added

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
