# CONTRIBUTING
### How humans and AI sessions contribute to the Legacy specification repository

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](docs/SPEC_CONVENTIONS.md), [LEGACY_PRINCIPLES](docs/LEGACY_PRINCIPLES.md) |

---

## 1. Purpose

This document defines how anyone (Linford, a trusted human collaborator, or a future AI session) makes changes to this repository. The repository contains only Markdown specifications; contributing means authoring or revising specs, never writing application code. The rules here exist so that documents written months or years apart, by different minds, read as one coherent system and never corrupt the factual record about Linford.

## 2. Goals

- Make every contribution session start from the same context and land in the same conventions.
- Protect the two things this repository cannot recover from losing: factual integrity (confidence tiers) and identifier stability.
- Give reviewers a mechanical checklist so quality does not depend on reviewer memory.
- Keep the change history (branches, commits, changelog, ADRs) useful to a reader ten years from now.

## 3. Scope

**In scope:** contribution workflow, mandatory reading, authoring rules, review checklist, branch and commit conventions, ADR change proposals, changelog maintenance.

**Out of scope:** the authoring conventions themselves (defined normatively in [SPEC_CONVENTIONS](docs/SPEC_CONVENTIONS.md); this document applies them, it does not redefine them), repository hosting and access control (an operational matter for the owner), and any application-code workflow (no application code exists here).

## 4. Requirements

### 4.1 Before your first change (mandatory reading order)

1. [knowledge/MASTER_CONTEXT.md](knowledge/MASTER_CONTEXT.md): the immutable single source of truth about Linford, including the confidence tier system in its §0. Read it in full. Never edit it (updates to it are an owner-run consolidation process, not a normal contribution).
2. [docs/SPEC_CONVENTIONS.md](docs/SPEC_CONVENTIONS.md): the normative template, ID schemes, canonical vocabulary, privacy tiers, and baseline architecture decisions.
3. [docs/VISION.md](docs/VISION.md), [docs/MISSION.md](docs/MISSION.md), [docs/LEGACY_PRINCIPLES.md](docs/LEGACY_PRINCIPLES.md): the product intent your change must serve.
4. The specific spec you are changing, plus every document it lists under Depends on.

### 4.2 Authoring rules (summary of the normative set)

- **Structure.** Every spec uses the title block and the 12 mandatory sections in order (Purpose, Goals, Scope, Requirements, Acceptance Criteria, Dependencies, Risks, Future Enhancements, Examples, Open Questions, References, Related Specifications). `README.md`, `CHANGELOG.md`, and `knowledge/MASTER_CONTEXT.md` are exempt.
- **No application code.** No SQL, Python, React, YAML pipelines, or executable API definitions anywhere. Tables, ASCII diagrams, JSON data examples, and natural-language walkthroughs are the permitted illustration tools.
- **Style.** No em dashes anywhere; use commas, colons, or parentheses. American English. Sentence-case headings after the title block. Production-grade prose, no filler.
- **Cross-references.** Relative Markdown links between specs. When citing requirements defined in a document you are not currently editing, cite the domain group or the document (for example "the FR-RAG group in specs/FUNCTIONAL_REQUIREMENTS.md") rather than a specific numeric ID you have not confirmed exists in that document's current text.

### 4.3 Identifier stability

- IDs (`PR-###`, `FR-<DOM>-###`, `ADR-##`, and the rest of the SPEC_CONVENTIONS §4 schemes) are permanent. **Never renumber. Never reuse.**
- New items take the next free number in their scheme, even if earlier numbers were deprecated.
- Retiring an item means marking it `Deprecated` in place with a one-line reason and, where applicable, a pointer to its replacement. Deleting an ID from a document is a defect.
- Renaming a document that defines IDs requires a redirect note at the old path reference points; the IDs themselves do not change.

### 4.4 Confidence-tier discipline

- Facts about Linford come only from [MASTER_CONTEXT](knowledge/MASTER_CONTEXT.md) and retain their tier markers (✅ Verified, 🟡 Self-reported, 🔴 Flagged) wherever restated.
- Never upgrade a 🟡 or 🔴 claim to plain fact. Attribute instead: "Linford reports that..." for 🟡, and explicit unverified framing for 🔴.
- Design decisions are always allowed but must be labeled as decisions (as SPEC_CONVENTIONS §9 does), never phrased as facts about Linford or his stack.
- If your spec needs a fact that MASTER_CONTEXT does not contain, do not research it into existence and do not guess. Record the gap (§4.5) and move on.

### 4.5 The TODO(verify) convention

Unknowns are recorded exactly as:

`> TODO(verify): <what is missing, and where the answer would come from>`

placed inline where the gap matters, and echoed in that spec's Open Questions section. TODO(verify) items are contributions, not embarrassments: they are how the verification queue in MASTER_CONTEXT §12 grows and shrinks honestly. Resolving one requires evidence, and the resolving change must cite it.

### 4.6 Branch and commit conventions

- **Never commit directly to the default branch.** All changes flow through feature branches.
- Branch names: `spec/<area>-<topic>` for spec content (for example `spec/memory-consolidation-rules`), `docs/<topic>` for meta documents, `fix/<topic>` for corrections. Lowercase, hyphen-separated.
- Commits are small and descriptive: an imperative subject line under 72 characters naming the document and the change (for example `Add sealed-tier unlock conditions to security privacy spec`), plus a body stating what changed and why, referencing affected IDs where relevant.
- One logical change per branch. A branch that touches requirement IDs, an ADR, and the changelog for one coherent reason is fine; a grab bag is not.
- AI sessions state in the commit body that the change was AI-authored and against which instructions or task it was produced.

### 4.7 Proposing ADR changes

Architecture decision records live in `architecture/MASTER_ARCHITECTURE.md` under the `ADR-##` scheme.

1. **Never rewrite an accepted ADR's decision.** ADRs are historical records.
2. To change a decision, author a new ADR with the next free number, containing: context (what changed since the original), the new decision, consequences, and a `Supersedes` line naming the old ADR.
3. Mark the old ADR `Superseded by ADR-<new>` without altering its original text.
4. Open the proposal as a feature branch touching the ADR, any specs the new decision invalidates (update them in the same branch or list them as follow-up TODOs), and a changelog entry.
5. The owner accepts or rejects ADRs; until accepted, a proposed ADR carries status `Proposed`.

### 4.8 CHANGELOG maintenance

- [CHANGELOG.md](CHANGELOG.md) follows Keep a Changelog 1.1.0 with semantic versioning applied to the specification set.
- Every substantive branch adds a line under the `Unreleased` heading in the appropriate category (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`). Editorial typo fixes may skip the changelog.
- Version semantics for a spec repository (a design decision): **major** for restructuring that breaks existing references or removes IDs' meaning, **minor** for new documents or new requirements, **patch** for corrections and clarifications that change no requirement's meaning.
- Releases (moving `Unreleased` into a dated version) are cut by the owner.

## 5. Acceptance Criteria

A contribution is accepted when it passes this review checklist. Reviewers (the owner, or an AI session acting as reviewer) apply it mechanically:

1. Title block present and correct (Status, Owner, Last updated refreshed to the change date, Depends on accurate).
2. All 12 sections present, in order, non-empty or with a one-line reason (exempt files excepted).
3. No em dashes anywhere in the changed content; no application code of any kind.
4. Every biographical statement carries or inherits its tier; no 🟡/🔴 upgrades; attributions phrased correctly.
5. All `> TODO(verify): ...` items are well-formed and echoed in Open Questions.
6. No ID renumbered, reused, or deleted; new IDs take the next free number; traceability links (PR to FR to FS to TASK) intact where touched.
7. All relative links resolve to files that exist in the branch, or are clearly marked as forward references to planned documents.
8. Canonical vocabulary used exactly: entity names, agent names, tier names, memory types per SPEC_CONVENTIONS §5 to §8.
9. The change is compatible with every principle in [LEGACY_PRINCIPLES](docs/LEGACY_PRINCIPLES.md), or carries a proposed ADR for the exception.
10. Changelog entry added under `Unreleased` (unless purely editorial), and commit messages meet §4.6.

## 6. Dependencies

- [SPEC_CONVENTIONS](docs/SPEC_CONVENTIONS.md): all normative authoring rules this document operationalizes.
- [MASTER_CONTEXT](knowledge/MASTER_CONTEXT.md): the fact base and tier system that §4.4 protects.
- [LEGACY_PRINCIPLES](docs/LEGACY_PRINCIPLES.md): checklist item 9.
- Git hosting with branch protection on the default branch (operational prerequisite).

## 7. Risks

| Risk | Effect | Mitigation |
|------|--------|------------|
| AI session skips mandatory reading | Conventions drift, facts get invented | §4.1 ordering is stated in README and here; review checklist catches violations |
| Parallel authorship collisions | Two branches define the same next ID or contradict each other | Small branches, owner-serialized merges, ID allocation checked at review |
| Tier erosion through paraphrase | Repeated restatement drops "reports that" and hardens 🟡 into fact | Checklist item 4; Provenance First principle; periodic repository lint (future) |
| Checklist fatigue | Reviews degrade into rubber stamps | Checklist is short, mechanical, and ordered by severity; automation candidates listed in §8 |
| Changelog rot | Unreleased section stops reflecting reality | Checklist item 10 makes it part of acceptance, not an afterthought |

## 8. Future Enhancements

- Automated lint pass (a future tool, specified before built): em dash detection, link resolution, title block validation, ID uniqueness, and tier-attribution heuristics on changed files.
- A `docs/GLOSSARY.md` consolidating canonical vocabulary for quicker cold starts.
- Reviewer rotation notes for multi-collaborator phases: what P1 collaborators may review versus what stays owner-only.
- Session log convention for AI contributors: a standard commit-body block recording model, date, and task framing.

## 9. Examples

**A well-formed TODO.**
`> TODO(verify): official IUS Africa listing for the Assistant Cluster Leader role (flagged 🔴 in MASTER_CONTEXT §4); confirmation would come from an IUS Africa public page or letter.`

**A well-formed commit.**
Subject: `Add reflective memory consolidation rules to memory spec`
Body: explains that consolidation cadence and provenance-preserving summarization rules were added to the Requirements of `memory/MEMORY_SYSTEM.md`, why weekly cadence was chosen (decision, not fact), notes the new changelog line, and states AI authorship with the task reference.

**A well-formed changelog line under Unreleased/Added.**
`- memory/MEMORY_SYSTEM.md: consolidation cadence and provenance rules for reflective memory.`

**An ADR supersession.** A future decision to adopt a dedicated graph database would arrive as a new ADR marked `Supersedes` the ADR that chose PostgreSQL-native graph modeling, with `knowledge/KNOWLEDGE_GRAPH.md` and `database/DATABASE_SCHEMA.md` updated or TODO-flagged in the same branch.

## 10. Open Questions

- Should ADRs split into one file per decision under `architecture/decisions/` once the count grows? Tracked in SPEC_CONVENTIONS §11; revisit past roughly fifteen ADRs.
- Do P1 human collaborators ever get merge rights, or does the owner remain the only merger for the repository's lifetime? Owner decision pending.
- `> TODO(verify): whether the owner wants signed commits or another authenticity mechanism for long-horizon attribution of changes.`

## 11. References

- [MASTER_CONTEXT](knowledge/MASTER_CONTEXT.md) §0 (tiers) and §12 (verification queue).
- [SPEC_CONVENTIONS](docs/SPEC_CONVENTIONS.md) §2 to §10 (all normative rules summarized here).
- Keep a Changelog 1.1.0 and Semantic Versioning 2.0.0 (external conventions adopted by [CHANGELOG](CHANGELOG.md)).

## 12. Related Specifications

- [CHANGELOG](CHANGELOG.md): where accepted changes are recorded.
- [docs/LEGACY_PRINCIPLES.md](docs/LEGACY_PRINCIPLES.md): principle compatibility required by the checklist.
- `architecture/MASTER_ARCHITECTURE.md`: home of the ADRs governed by §4.7.
- `README.md`: repository index and reading order for newcomers.
