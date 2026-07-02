# QUALITY_ASSURANCE
### QA process governing spec-driven implementation of the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [TESTING](./TESTING.md), [CI_CD](../deployment/CI_CD.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) |

---

## 1. Purpose

This document defines the quality assurance process that wraps the test strategy in [TESTING](./TESTING.md). Where TESTING defines what is verified and how, this document defines when work is allowed to start, when it counts as done, how deviations from specification are handled, how defects are managed, and what must be true before a release ships.

Legacy is built spec-first by design (the owner practices Specification-Driven Development, MASTER_CONTEXT §2, 🟡). This process makes that discipline enforceable: the specifications in this repository are the contract, implementation follows them, and any divergence flows back into the specs before it flows into code.

## 2. Goals

1. No implementation work begins on an underspecified feature, and no feature is called done without passing its specified acceptance criteria and tests.
2. The specs stay truthful to the shipped system: spec drift is detected and corrected, never accumulated.
3. Defects are triaged predictably, and escaped defects teach the process something (escape analysis).
4. Quality is measurable: a small set of metrics shows whether the process is working.
5. The process fits a solo founder without collapsing into "I checked it myself": structured self-review, AI-assisted review, and periodic external review compensate for the missing second pair of eyes.

## 3. Scope

### 3.1 In scope

- Definition of ready and definition of done for spec-driven work.
- Spec review gates on implementation PRs and the spec-first deviation rule.
- Traceability audits across the PR to FR/NFR to FS to TASK chain.
- Release criteria checklist, defect management, quality metrics, solo-founder adaptations, and documentation quality (stale-spec detection).

### 3.2 Out of scope

- Test categories, coverage targets, and gate contents: [TESTING](./TESTING.md).
- Pipeline implementation of the gates: [CI_CD](../deployment/CI_CD.md).
- Repository authoring conventions themselves: [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md).
- Security incident response: the SECURITY specification.

## 4. Requirements

Identifiers below (QA-##) are local to this document.

### 4.1 Definition of ready (DoR)

**QA-01.** A work item is ready for implementation only when all of the following hold:

1. It maps to a `TASK` in `roadmap/TASKS.md`, which traces to at least one feature specification (`FS`) in `specs/FEATURE_SPECIFICATIONS.md`.
2. The FS cites the functional requirements it implements (by FR group and ID within that document) and has non-empty acceptance criteria.
3. Privacy impact is stated: which privacy tiers (P0 to P3) the feature touches, and whether it can move content between tiers.
4. AI impact is stated: whether the feature touches retrieval, twin behavior, or confidence-tier presentation; if yes, the relevant eval sets in [TESTING](./TESTING.md) §4.2 are identified.
5. Open questions blocking the design are resolved or explicitly deferred with a TODO in the owning spec.

**QA-02.** Work items failing DoR are returned to specification, not started "provisionally."

### 4.2 Definition of done (DoD)

**QA-03.** A feature is done when:

1. It satisfies every acceptance criterion of its FS, demonstrated by mapped tests or a recorded manual verification.
2. It passes all tests mapped to its FR group, plus the blocking CI gates in [TESTING](./TESTING.md) §4.9.
3. If it touches AI behavior: the relevant golden sets, tier-discipline checks, and disclosure tests pass; if it changes the twin's prompt or model, a persona fidelity review has been completed.
4. If it touches privacy tiers: the enforcement suites (retrieval leakage, redaction, tombstone, agent ceilings) pass, and the authorization matrix is regenerated if roles or resources changed.
5. Traceability is updated: the PR records its FS and FR group references, the TASK is closed with links, and any spec text made inaccurate by the change was updated in a merged spec PR first.
6. User-facing surfaces meet [ACCESSIBILITY](../ui/ACCESSIBILITY.md) requirements for the changed screens, and UI copy follows the voice rules in [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) (including the no em dashes rule).
7. `CHANGELOG.md` is updated when behavior visible to any surface changes.

### 4.3 Spec review gates (spec-first rule)

**QA-10.** Every implementation PR description cites the specification sections it implements: at minimum the FS ID and the FR group, plus any ADRs relied on. PRs without citations fail review.

**QA-11.** The spec-first rule: if implementation reveals that a spec is wrong, ambiguous, or must change, the spec is updated in its own PR and merged before (or together with, in one reviewable unit ordered spec-then-code) the implementation change. Code never silently diverges from spec. "Temporary" divergence is not a category this process recognizes.

**QA-12.** Spec PRs themselves are reviewed against [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): section structure, title block, identifier discipline, tier discipline for biographical facts, no em dashes, TODO convention. A conventions checklist runs as an automated lint where feasible (structure, forbidden characters, broken relative links) and as review checklist otherwise.

**QA-13.** Changes touching [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) are out of bounds for implementation work entirely: it is immutable input. New facts route to its verification queue process, not to spec edits.

### 4.4 Traceability audits

**QA-20.** The traceability chain is `PR` to `FR`/`NFR` to `FS` to `TASK` (with `US`/`UC` linking personas to FRs), per [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4. Quarterly, a sampled audit takes at least 10 percent of the quarter's merged implementation PRs and walks the chain in both directions:

1. Forward: does each sampled requirement have implementing FS, TASK, shipped code, and passing tests?
2. Backward: does each sampled PR cite real spec sections, and does the shipped behavior match them?

**QA-21.** Audit findings are classified as: broken link (metadata fixable), spec drift (behavior diverged, triggers QA-11 correction), or orphan behavior (shipped behavior with no owning spec, the most serious class; it must gain a spec or be removed).

**QA-22.** Audit results (sample size, findings by class, corrections) are recorded in a short dated note under `roadmap/` and feed the spec-coverage metric (§4.7).

### 4.5 Release criteria checklist

**QA-30.** A release ships only when every item below is green. The checklist is completed per release and archived.

| # | Criterion | Source |
|---|-----------|--------|
| 1 | All blocking CI gates green on the release candidate | [TESTING](./TESTING.md) §4.9 |
| 2 | Full AI eval suite passed: golden sets, groundedness, citation accuracy, tier discipline, twin disclosure, injection set | [TESTING](./TESTING.md) §4.2 |
| 3 | Privacy enforcement suites passed, authorization matrix current | [TESTING](./TESTING.md) §4.3, §4.4 |
| 4 | Accessibility checks passed: automated suite green, manual pass done for changed screens | [ACCESSIBILITY](../ui/ACCESSIBILITY.md) |
| 5 | Security scans passed (dependencies, secrets, static analysis), no unresolved high findings | [SECURITY](../security/SECURITY.md) |
| 6 | Performance suite within NFR budgets, or waiver recorded | [TESTING](./TESTING.md) §4.5 |
| 7 | Most recent restore drill passed within its scheduled window | [TESTING](./TESTING.md) §4.7 |
| 8 | No open S1 or S2 defects against the release scope | §4.6 |
| 9 | CHANGELOG updated; release notes list spec sections newly implemented | Repository meta |
| 10 | Spec drift check: no known unresolved QA-11 divergences | §4.3 |

**QA-31.** Waivers (allowed only for criteria 6 and non-blocking findings elsewhere) are written, dated, owner-signed, and expire: each waiver names the release by which it must be resolved.

### 4.6 Defect management

**QA-40. Severity ladder.**

| Severity | Definition | Examples | Response |
|----------|-----------|----------|----------|
| S1 | Data loss, privacy-tier leak, security breach, tier discipline broken in production | P2 content visible at P0; twin asserts a 🔴 claim as fact in production | Stop-the-line: fix before any other work; incident note required |
| S2 | Core journey broken, no workaround | Capture fails; twin chat down; export corrupt | Fix before next release; triage within one day |
| S3 | Degraded behavior with workaround | Slow search within a journey; layout defect obscuring content | Scheduled into the next one or two iterations |
| S4 | Cosmetic, minor copy, polish | Misaligned badge, non-blocking copy issue | Backlog, batched |

**QA-41. Triage cadence.** New defects are triaged at least weekly (S1 immediately on discovery). Triage assigns severity, maps the defect to the spec section whose behavior it violates (or flags orphan behavior per QA-21), and links the test that should have caught it.

**QA-42. Escape analysis.** Every S1 and S2 that reaches production gets a short written escape analysis: which gate should have caught it, why it did not, and the specific test, eval case, or checklist item added so the same class cannot escape again. Injection-class escapes additionally extend the injection set per [TESTING](./TESTING.md).

### 4.7 Quality metrics

**QA-50.** Tracked per release and trended:

| Metric | Definition | Direction |
|--------|-----------|-----------|
| Defect escape rate | S1+S2 found in production divided by total S1+S2 found in the period | Down |
| Eval regression rate | Share of releases where any AI eval gate required a fix or waiver before shipping | Down |
| Spec coverage of shipped behavior | Share of sampled shipped behaviors with an owning spec section (from QA-20 audits) | Up toward 100 percent |
| Gate integrity | Count of waivers active at release time | Down |
| Flake rate | From [TESTING](./TESTING.md) §4.10 | Under budget |
| Stale-spec count | Specs past their review interval (§4.9) | Down |

**QA-51.** Metrics exist to steer, not to grade: a worsening trend triggers a process retrospective, not metric gaming. Targets are set after two releases of baseline data. `> TODO(verify): owner to set initial numeric targets after baseline.`

### 4.8 Solo-founder adaptations

**QA-60.** Legacy is built by one person; classic peer review is unavailable by default. Compensating controls:

1. **Structured self-review.** Every PR gets a self-review pass against a written checklist (spec citations present, DoD items, privacy and AI impact statements, conventions lint) performed after a deliberate break from writing the code, and recorded in the PR.
2. **AI-assisted review.** An AI reviewer pass over every implementation PR, prompted with the cited spec sections, checking spec conformance, tier discipline, privacy handling, and test adequacy. AI review is an aid, never the approval of record; the owner remains accountable.
3. **Two-session rule for dangerous changes.** Changes touching privacy enforcement, succession, sealing (P3), redaction, or tier presentation are written in one session and approved in a separate later session, so no such change is conceived and approved in a single sitting.
4. **Periodic external review.** `> TODO(verify): owner to arrange an external reviewer (trusted peer from the GDG Cape Town network or a paid security reviewer) at least annually for the security and privacy surfaces; record the arrangement here when made.`

### 4.9 Documentation quality: stale-spec detection

**QA-70.** Every spec carries its `Last updated` date in the title block. A spec is stale when its domain has shipped behavior changes since that date, or when it has not been reviewed within 12 months (6 months for security, privacy, and AI behavior specs).

**QA-71.** A stale-spec report (automatable from git history against spec references in PRs) runs quarterly alongside the traceability audit. Stale specs are either re-verified (date bumped after review) or corrected via QA-11.

**QA-72.** Specs remain honest about confidence: biographical statements keep their MASTER_CONTEXT tiers forever; a quarterly pass confirms no spec has silently upgraded a 🟡 or 🔴 claim.

## 5. Acceptance Criteria

1. DoR and DoD are written into the contribution workflow (`CONTRIBUTING.md` references this document) and every closed TASK links evidence for the DoD items.
2. Every merged implementation PR in a sampled audit cites at least one FS and FR group; PRs lacking citations are rejected at review, demonstrably.
3. At least one spec-first correction (QA-11) can be traced end to end once implementation begins: divergence found, spec PR merged, code aligned.
4. Quarterly traceability audit notes exist for every completed quarter after implementation start.
5. A completed release checklist is archived for every production release, including any waivers with expiry.
6. Escape analyses exist for 100 percent of production S1 and S2 defects.
7. The quality metrics table is populated and trended by the second release.
8. The stale-spec report runs quarterly and its findings are actioned or waived.

## 6. Dependencies

- [TESTING](./TESTING.md): all gate contents, suites, and budgets this process invokes.
- [CI_CD](../deployment/CI_CD.md): mechanical enforcement of blocking gates and checklist automation.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): identifier schemes and the traceability chain audited here.
- `specs/FEATURE_SPECIFICATIONS.md`, `specs/FUNCTIONAL_REQUIREMENTS.md`, `roadmap/TASKS.md`: the artifacts DoR and DoD bind together.
- [SECURITY](../security/SECURITY.md) and [PRIVACY](../security/PRIVACY.md): scan requirements and privacy impact definitions.
- `CHANGELOG.md` and `CONTRIBUTING.md`: repository meta updated by this process.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Process weight overwhelms a solo founder | Checklists skipped under pressure, quality theater | Keep blocking items few and automated; QA-30 is ten lines, not fifty; automate lints |
| Self-review blind spots | Defects the author cannot see | AI-assisted review, two-session rule, external review TODO (QA-60) |
| Spec-first rule bypassed "just once" | Spec drift compounds until specs are fiction | Orphan-behavior class in audits treated as most serious (QA-21); gate integrity metric |
| Escape analyses become blame rituals or get skipped | Same defect classes recur | Keep them short, factual, and template-driven; required only for S1/S2 |
| Metrics gamed (severity downgrading, waiver overuse) | Dashboard green, product decaying | Waivers expire and are counted; severity definitions are behavioral, not negotiable |
| External review never materializes | Security and privacy surfaces reviewed by author only | Standing TODO surfaced in every release checklist until resolved |

## 8. Future Enhancements

- Automated DoD bot: a CI check that parses PR descriptions for FS and FR citations and blocks merge when absent.
- Traceability graph tooling: generate the PR to FR to FS to TASK graph from repository metadata instead of manual sampling.
- Defect prediction from escape-analysis tags once enough history exists.
- Formal periodic third-party security audit when budget allows, upgrading the QA-60 external review from TODO to contract.
- Multi-contributor review rules (true peer review, CODEOWNERS-style spec ownership) if the project gains contributors.

## 9. Examples

**PR description skeleton (illustrative):**

```
Implements: FS-0xx (capture quick add), FR-ING group
Spec sections: specs/FEATURE_SPECIFICATIONS.md FS-0xx; ui/UI_UX.md capture pattern
Privacy impact: creates P2 content only; no tier movement
AI impact: none (no retrieval or twin changes)
DoD evidence: acceptance criteria mapped to tests <links>; CHANGELOG updated
Self-review: checklist completed <link>; AI review pass attached
```

**Spec-first correction:** implementation of timeline zoom reveals the FS assumed events always carry exact dates, but ingestion produces fuzzy dates ("mid 2025"). The developer stops, opens a spec PR updating the FS and the timeline domain requirements to define fuzzy-date rendering, merges it, then implements against the corrected spec. The PR cites both.

**Escape analysis (S2, condensed):** "Citation chip showed a Source the viewer's tier could not access. Escaped because the citation accuracy suite checked existence and support but not viewer-tier visibility on the chip render path. Added: UI-level tier visibility case to the citation suite and an authorization matrix row for citation rendering. Gate: nightly eval. Spec updated: none needed, behavior was specified correctly."

## 10. Open Questions

- Numeric targets for §4.7 metrics: deferred until two releases of baseline data. `> TODO(verify): set after baseline.`
- External reviewer arrangement for QA-60 item 4. `> TODO(verify): owner to secure and record.`
- Should the quarterly audit sample rate rise above 10 percent while the codebase is small (when full audit is cheap)? Proposed: audit 100 percent until PR volume makes sampling necessary.
- Tooling choice for the defect tracker and checklist automation. `> TODO(verify): decide with the CI_CD toolchain.`

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier rules this process must keep intact), §2 (SDD as the owner's discipline, 🟡).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §2 (non-negotiable rules), §4 (traceability chain).

## 12. Related Specifications

- [TESTING](./TESTING.md): the strategy this process wraps.
- [CI_CD](../deployment/CI_CD.md), [OBSERVABILITY](../deployment/OBSERVABILITY.md).
- `specs/FEATURE_SPECIFICATIONS.md`, `specs/FUNCTIONAL_REQUIREMENTS.md`, `specs/NON_FUNCTIONAL_REQUIREMENTS.md`, `roadmap/TASKS.md`, `roadmap/RISKS.md`.
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md).
- [UI_UX](../ui/UI_UX.md), [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md), [ACCESSIBILITY](../ui/ACCESSIBILITY.md).
