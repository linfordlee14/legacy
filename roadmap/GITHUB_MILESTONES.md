# GITHUB_MILESTONES
### GitHub milestone strategy for the Legacy repository, from MVP to Version 1.0

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [ROADMAP](ROADMAP.md), [MVP_PLAN](MVP_PLAN.md), [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md), [BUILD_ORDER](BUILD_ORDER.md), [TASKS](TASKS.md) |

---

## 1. Purpose

This document defines the GitHub milestone strategy for delivering Legacy: nine milestones from MVP Foundation to Version 1.0, each mapped to existing MVP-### and TASK-### IDs, roadmap phases, and decision gates. It also specifies the label taxonomy, project board, and issue and PR templates shipped under `.github/`. Nothing here redesigns anything: milestones are a GitHub projection of [ROADMAP](ROADMAP.md) and [BUILD_ORDER](BUILD_ORDER.md), and where a suggested milestone name could be misread against the specs, the reconciliation is stated explicitly.

## 2. Goals

- Give every issue and pull request a home: one milestone, canonical task IDs, consistent labels.
- Preserve roadmap fidelity: phase ordering stays normative, decision gates (G1 to G5) close milestones, and no calendar due dates are set (per the roadmap's no-date rule; GitHub milestones are created without due dates).
- Make progress legible to outsiders: an enterprise-quality public face for a build-in-public project.

## 3. Scope

**In scope:** the nine milestones, label taxonomy, project board definition, template inventory, and setup commands. **Out of scope:** task content (canonical in [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md) and [TASKS](TASKS.md)) and any scope or ordering change to the roadmap.

**Naming reconciliations (read before using the milestones):**

1. **Milestone 2 "Knowledge Vault"** means the trusted, indexed, provenance-tracked corpus (Claims, Sources, verification queue, index pipeline). It is NOT the F16 "Legacy Vault" export feature, which lives in Milestone 7.
2. **Milestone 4 "Timeline & Portfolio"** delivers the PRIVATE portfolio: the knowledge graph, timeline, and the project and research explorer (F13). The PUBLIC portfolio (F10) deliberately waits for Milestone 8, because the roadmap ships honesty infrastructure before anything public (ROADMAP §7).
3. **Milestone 5 "Digital Twin"** includes the Phase 3 intelligence layer (full RAG, memory, model router) plus the orchestrator runtime core, because the twin is specified as an agent on that runtime and Gate G3 forbids twin work before RAG quality is measured.

## 4. Requirements

### 4.1 Milestone 1: MVP Foundation

- **Title:** `M1 – MVP Foundation`
- **Description (GitHub field):** Secure system of record: sign in with MFA, capture documents and notes in under a minute, full schema with privacy tiers, audit logging, verified backups. BUILD_ORDER steps 1 to 15.
- **Objective:** Complete MVP Stages 1 and 2 (Bedrock, Capture) so the owner can capture daily with nothing silently lost.
- **Included tasks:** MVP-001, MVP-002, MVP-003, MVP-004, MVP-005, MVP-006, MVP-007, MVP-008, MVP-009, MVP-010, MVP-011, MVP-012, MVP-013, MVP-014, MVP-015 (parents: TASK-101 to TASK-111 partially discharged).
- **Completion criteria:** Roadmap Phase 1 exit criteria 1, 2, 4, 5 pass ([ROADMAP](ROADMAP.md) §4.5); point-in-time restore drill passed (criterion 3 baseline); capture under one minute measured; MASTER_CONTEXT seeded as tiered Claims; accessibility CI gate green.
- **Dependencies:** External accounts and owner inputs ([MVP_PLAN](MVP_PLAN.md) §6). Nothing upstream.
- **Labels:** `priority: P0`, `type: infra`, `type: security`, `domain: ingestion`, `domain: ui`, `domain: data`, `domain: api`.
- **Priority:** P0 (highest; everything depends on it).

### 4.2 Milestone 2: Knowledge Vault

- **Title:** `M2 – Knowledge Vault`
- **Description:** The corpus becomes trusted knowledge: chunking and embedding pipeline, Claim and Source provenance live, verification queue seeded with the MASTER_CONTEXT §12 items and worked for the first time.
- **Objective:** Provenance as working data, not decoration: every claim tiered, the queue operational, the index rebuildable from source.
- **Included tasks:** MVP-016, MVP-020 (parents TASK-201 partial, TASK-206); maintenance TASK-001, TASK-002, TASK-003.
- **Completion criteria:** All content chunked and embedded with tier and provenance metadata; rebuild-from-source drill passes (NFR-024); all six §12 items listed in the queue; at least one 🔴 claim resolved end to end with audit trail (roadmap Phase 2 exit criterion 4); source URLs attached to ✅ claims per TASK-001.
- **Dependencies:** Milestone 1 (schema, ingestion, seeds, workspace shell).
- **Labels:** `priority: P0`, `domain: verification`, `domain: rag`, `invariant: provenance`, `type: feature`.
- **Priority:** P0.

### 4.3 Milestone 3: AI Search

- **Title:** `M3 – AI Search`
- **Description:** Find anything fast: lexical, semantic, and hybrid search with airtight privacy-tier filtering, search UI with provenance badges, production hardening, and the MVP acceptance run. Closing this milestone ships the MVP.
- **Objective:** Complete and ship the MVP defined in [MVP_PLAN](MVP_PLAN.md); open the Gate G1 evidence log.
- **Included tasks:** MVP-017, MVP-018, MVP-019, MVP-021, MVP-022, MVP-023 (parents TASK-202, plus TASK-109 drill completion); stretch (optional, may roll to Milestone 5): MVP-024, MVP-025, MVP-026 (parents TASK-301 to TASK-303 subsets).
- **Completion criteria:** MVP_PLAN §5 criteria 1 through 6 pass in production (criterion 7 only if stretch shipped); tier-leak suite green (NFR-035); NFR-001/002 latency met; full restore drill passed; CHANGELOG updated with zero undocumented deviations; G1 evidence log opened.
- **Dependencies:** Milestones 1 and 2.
- **Labels:** `priority: P0`, `domain: search`, `invariant: privacy-tiers`, `type: feature`, `type: drill`.
- **Priority:** P0 (MVP ship gate).

### 4.4 Milestone 4: Timeline & Portfolio

- **Title:** `M4 – Timeline & Portfolio`
- **Description:** The private portfolio: knowledge graph extraction with owner-approved merges, timeline explorer, GitHub repository ingestion, and the project and research explorer. Closes roadmap Phase 2 and Gate G2.
- **Objective:** Turn the stored corpus into structured, navigable knowledge (roadmap Phase 2 objective) plus the F13 explorer.
- **Included tasks:** TASK-203, TASK-204, TASK-205, TASK-207, TASK-208 (Gate G2 review), TASK-306.
- **Completion criteria:** Roadmap Phase 2 exit criteria 1, 2, 3, 5 pass (criterion 4 already met in Milestone 2); Gate G2 decision recorded as an ADR update (graph database re-evaluation, embedding model locked); explorer browses projects with graph, timeline, and search integration; list-first accessibility rule verified on both explorers.
- **Dependencies:** Milestone 3 (search live, Gate G1 evidence accumulating; the formal G1 review completes before heavy Phase 2 investment per [ROADMAP](ROADMAP.md) §4.5).
- **Labels:** `priority: P1`, `domain: graph`, `domain: timeline`, `type: feature`, `gate`.
- **Priority:** P1.

### 4.5 Milestone 5: Digital Twin

- **Title:** `M5 – Digital Twin`
- **Description:** The intelligence layer and the twin: full model router (Claude primary, Gemini and Groq alternates), production RAG with citations, long-term memory, multimedia ingestion, the orchestrator runtime core, and the tier-honest Digital Twin in owner mode. Closes roadmap Phase 3, Gate G3, and the twin portion of Phase 4.
- **Objective:** The corpus answers questions honestly, remembers across sessions, and speaks in a disclosed, tier-disciplined twin voice for the owner only.
- **Included tasks:** TASK-301, TASK-302, TASK-303, TASK-304, TASK-305, TASK-307 (Phase 3); TASK-401 (runtime core, pulled forward as the twin's substrate); TASK-403 (twin). If Milestone 3 stretch shipped, TASK-302 to TASK-304 harden it; if not, they build it.
- **Completion criteria:** Roadmap Phase 3 exit criteria 1 through 6 pass; Gate G3 recorded (citation coverage, refusal accuracy, cost per answer measured and accepted); twin passes the honesty red-team suite (Phase 4 exit criterion 1); disclosure compliance 100 percent; twin remains owner-only pending Gate G4.
- **Dependencies:** Milestone 4 (Gate G2 recorded; graph and explorer feed RAG context and twin grounding).
- **Labels:** `priority: P1`, `domain: rag`, `domain: memory`, `domain: twin`, `invariant: provenance`, `type: eval`, `gate`.
- **Priority:** P1 (highest reputational risk concentration, RISK-03; the eval gates are non-negotiable).

### 4.6 Milestone 6: Multi-Agent System

- **Title:** `M6 – Multi-Agent System`
- **Description:** The full twelve-agent roster on the audited runtime: ingestion, curation, graph, timeline, research, verification, mentor, writing, and reflection agents, with approval gates, budgets, prompt-injection defenses, and the A2A adoption decision. Closes roadmap Phase 4 and Gate G4.
- **Objective:** Legacy operates itself under human government: agents do the routine work, every irreversible action waits for owner approval, every run is traceable.
- **Included tasks:** TASK-402, TASK-404, TASK-405, TASK-406, TASK-407, TASK-408 (A2A decision ADR), TASK-409.
- **Completion criteria:** Roadmap Phase 4 exit criteria 2 through 6 pass; Gate G4 passed (honesty suite at threshold for two consecutive review points, prerequisite for anything public); prompt-injection suite green; autonomy boundary tests prove no unapproved outward action.
- **Dependencies:** Milestone 5 (runtime core, twin, evals).
- **Labels:** `priority: P1`, `domain: agents`, `type: security`, `type: eval`, `gate`.
- **Priority:** P1.

### 4.7 Milestone 7: Legacy Vault

- **Title:** `M7 – Legacy Vault`
- **Description:** The platform outlives its infrastructure: P3 journal sealing with release conditions, the open-format Legacy Vault export with integrity manifest, the succession protocol, steward documentation and drills, and the first full disaster restore drill. This is the F16 feature (distinct from Milestone 2's corpus work).
- **Objective:** Durability and succession proven by drills: a steward who did not build the system can read the corpus and operate the essentials.
- **Included tasks:** TASK-501, TASK-504, TASK-505, TASK-506, TASK-508; prerequisite owner action TASK-006 (legal review of succession mechanics).
- **Completion criteria:** Roadmap Phase 5 exit criteria 2, 3, 4 pass (sealing with no read path before release conditions; vault produced, restored on a clean machine, read offline; steward simulation completed); NFR-032 egress test green; RPO/RTO targets met in the disaster drill (NFR-051/052).
- **Dependencies:** Milestone 5 (memory and tier plumbing for sealing); TASK-006 legal input. Independent of Milestone 6 agent work except shared release cadence.
- **Labels:** `priority: P0`, `domain: privacy`, `domain: ops`, `type: drill`, `type: security`, `needs: legal-review`.
- **Priority:** P0 (existential purpose of the platform; priority reflects importance, not sequence).

### 4.8 Milestone 8: Public Beta

- **Title:** `M8 – Public Beta`
- **Description:** Legacy opens outward: the public portfolio serving only P0 content through the publication gate, the public twin with permanent disclosure, the accessibility statement and pre-launch audit, and the POPIA review with a reachable third-party complaint process. Invited audience first, then open beta.
- **Objective:** A public face that never overstates: 🔴 claims blocked from publication, 🟡 claims rendered with attribution, twin honesty already gate-proven.
- **Included tasks:** TASK-502, TASK-503, TASK-507; POPIA review completion and complaint process publication (roadmap Phase 5 exit criterion 5); TASK-005 closure (brand palette applied or placeholder consciously kept for beta).
- **Completion criteria:** Roadmap Phase 5 exit criteria 1 and 5 pass; Gate G4 precondition confirmed still green; publication gate demonstrably blocks a seeded 🔴-dependent page; public twin ceiling tests pass (P0 only); accessibility statement live; NFR-010 portfolio performance met; beta feedback channel open.
- **Dependencies:** Milestones 5 and 6 (Gate G4), Milestone 7 recommended first (breach stakes rise with public exposure, RISK-02).
- **Labels:** `priority: P1`, `domain: ui`, `domain: twin`, `invariant: privacy-tiers`, `invariant: provenance`, `type: feature`.
- **Priority:** P1.

### 4.9 Milestone 9: Version 1.0

- **Title:** `M9 – Version 1.0`
- **Description:** Declaration and consolidation: Gate G5 go/no-go on full public launch, every phase exit criterion re-verified, verification queue healthy, risk register reviewed, v1.0 tagged, and remaining ambitions triaged to FUTURE_FEATURES.
- **Objective:** Declare v1 honestly: everything the specs promised for v1 is verified in production, and everything else is explicitly not promised.
- **Included tasks:** Gate G5 review (recorded as ADR update); full acceptance sweep of roadmap Phase 1 to 5 exit criteria; [RISKS](RISKS.md) phase-gate review; [FUTURE_FEATURES](FUTURE_FEATURES.md) trigger triage; TASK-004 (CHANGELOG and status currency) closure for the release; release notes and v1.0 tag.
- **Completion criteria:** Gate G5 passed and recorded; no untriaged 🔴 claim older than the staleness threshold; all Must-priority NFRs green in the latest verification cycle; CHANGELOG 1.0.0 entry; v1.0 tag on the default branch; risk register review dated within the release window.
- **Dependencies:** Milestones 1 through 8 all closed.
- **Labels:** `priority: P0`, `type: docs`, `gate`, `type: drill`.
- **Priority:** P0 (release integrity).

### 4.10 Label taxonomy

Machine-readable definitions live in [`.github/labels.yml`](../.github/labels.yml) (apply with `github-label-sync` or the commands in §4.13). Groups:

| Group | Labels | Use |
|-------|--------|-----|
| Type | `type: feature`, `type: bug`, `type: spec`, `type: docs`, `type: infra`, `type: security`, `type: drill`, `type: eval` | Exactly one per issue; drills and evals are first-class work in this project |
| Priority | `priority: P0`, `priority: P1`, `priority: P2` | Mirrors the MoSCoW-derived scheme in [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md) |
| Domain | `domain: ingestion`, `domain: graph`, `domain: timeline`, `domain: search`, `domain: rag`, `domain: memory`, `domain: twin`, `domain: agents`, `domain: verification`, `domain: api`, `domain: ui`, `domain: data`, `domain: privacy`, `domain: security`, `domain: ops` | Mirrors the FR domain codes in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4 |
| Invariant | `invariant: privacy-tiers`, `invariant: provenance` | Anything touching the two platform invariants; these issues get extra review |
| Workflow | `status: blocked`, `needs: owner-decision`, `needs: legal-review`, `gate`, `descope-ladder`, `good first issue`, `help wanted` | Process signals; `gate` marks decision-gate reviews (G1 to G5) |

### 4.11 Project board (GitHub Projects)

One project: **Legacy Delivery** (GitHub Projects cannot be defined by repository files; create per §4.13).

- **Custom fields:** `Step` (number, from BUILD_ORDER), `Effort (days)`, `Priority` (P0/P1/P2), `Domain`, `Spec sections` (text), `Milestone` (built-in).
- **Views:**
  1. **Build Order** (table): all items sorted by `Step`; the canonical "what next" view mirroring [BUILD_ORDER](BUILD_ORDER.md) §4.2.
  2. **Board** (kanban): `Backlog / Ready / In progress / In review / Blocked / Done`; one item per session in progress, per the BUILD_ORDER session protocol.
  3. **Milestones** (table grouped by Milestone): the roadmap projection for outside readers.
  4. **Invariants watch** (filtered): open items labeled `invariant: privacy-tiers` or `invariant: provenance`.
- **Automation:** issue closed → `Done`; PR merged linked to issue → `In review` cleared; `status: blocked` label → `Blocked` column.

### 4.12 Repository templates

Shipped under `.github/` alongside this strategy:

| File | Purpose |
|------|---------|
| `ISSUE_TEMPLATE/1-implementation-task.yml` | Spec-anchored engineering task (the default work item; requires task ID and spec sections) |
| `ISSUE_TEMPLATE/2-bug-report.yml` | Bug report with severity, spec-expected behavior, and a mandatory privacy notice (never paste P2/P3 content) |
| `ISSUE_TEMPLATE/3-feature-request.yml` | Feature request routed through the spec-first rule and FUTURE_FEATURES trigger discipline |
| `ISSUE_TEMPLATE/4-documentation.yml` | Specification or documentation change (spec-first changes start here) |
| `ISSUE_TEMPLATE/config.yml` | Disables blank issues; links CONTRIBUTING and SPEC_CONVENTIONS |
| `pull_request_template.md` | PR checklist enforcing spec citations, invariant tests, CHANGELOG discipline, and style rules |

### 4.13 Setup commands (run once by the owner)

Milestones (no due dates, per the roadmap's no-date rule):

```text
gh api repos/{owner}/legacy/milestones -f title="M1 – MVP Foundation" -f description="Secure system of record: auth, schema, capture, backups. BUILD_ORDER steps 1-15." -f state="open"
# repeat for M2 through M9 with the Title and Description fields from sections 4.1 to 4.9
```

Labels: `npx github-label-sync --access-token <token> --labels .github/labels.yml {owner}/legacy` (or `gh label create` per entry). Project: create "Legacy Delivery" in the GitHub UI or via `gh project create`, then add the §4.11 fields and views.

## 5. Acceptance Criteria

- All nine milestones exist on GitHub with the §4 titles and descriptions, no due dates, and every open implementation issue assigned to exactly one milestone.
- Every MVP-### and post-MVP TASK-### referenced in [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md) and [TASKS](TASKS.md) §4.2 to §4.6 appears in exactly one milestone above (verified by the coverage table check: M1 covers MVP-001..015; M2 covers MVP-016, MVP-020, TASK-001..003; M3 covers MVP-017..019, MVP-021..026; M4 covers TASK-203..208, TASK-306; M5 covers TASK-301..305, TASK-307, TASK-401, TASK-403; M6 covers TASK-402, TASK-404..409; M7 covers TASK-501, TASK-504..506, TASK-508, TASK-006; M8 covers TASK-502, TASK-503, TASK-507, TASK-005; M9 covers gate and release work plus TASK-004).
- Labels match `.github/labels.yml` exactly; templates render correctly on GitHub's new-issue page.
- No milestone completion criterion contradicts a roadmap exit criterion or gate.

## 6. Dependencies

- [ROADMAP](ROADMAP.md) phases and gates (the ordering authority), [BUILD_ORDER](BUILD_ORDER.md) (step sequence inside M1 to M3), [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md) and [TASKS](TASKS.md) (task content).
- GitHub features: milestones, labels, issue forms, Projects.
- Owner action for §4.13 setup (requires repository admin).

## 7. Risks

- Milestone names could drift from spec vocabulary; the §3 reconciliations are normative and repeated in milestone descriptions where confusion is likeliest.
- GitHub milestones tempt due dates; the roadmap forbids them, and §4.13 deliberately omits `due_on`.
- Cross-milestone dependency violations (for example starting TASK-403 before Gate G3 is recorded); the `gate` label plus the Build Order view are the controls.
- TASK-501 note: it appears in Milestone 7 with its TASK dependency on memory (TASK-305, Milestone 5) intact; do not pull it earlier.

## 8. Future Enhancements

- Release automation (tagged releases per milestone close) once implementation CI exists.
- A public roadmap page rendered from milestone state.
- Issue-to-spec link checking in CI (fail a PR whose issue cites no spec section).

## 9. Examples

A contributor opens the repository during Milestone 3: the Build Order view shows step 17 (search API) as `Ready` with priority P0 and spec sections listed; they file nothing new, take the linked `1-implementation-task` issue, read the cited sections per the session protocol, and open a PR whose template forces spec citations and the tier-leak checklist. The PR closes the issue, automation moves it to Done, and the milestone progress bar ticks toward the MVP ship.

## 10. Open Questions

- Should Milestone 7 (Legacy Vault) run before Milestone 6 (agents) for a solo builder, since it depends only on Milestone 5? The roadmap keeps Phase 4 before Phase 5; revisit at the Gate G3 review with capacity evidence.
- Public beta audience for Milestone 8 (invited list versus open): owner decision at Gate G4.

## 11. References

- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) §4 (domain codes mirrored by labels).
- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §12 (the claims worked in Milestone 2).
- GitHub documentation: milestones, issue forms, Projects (linked from the GitHub docs site).

## 12. Related Specifications

- [ROADMAP](ROADMAP.md), [MVP_PLAN](MVP_PLAN.md), [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md), [BUILD_ORDER](BUILD_ORDER.md), [TASKS](TASKS.md), [RISKS](RISKS.md)
- [CONTRIBUTING](../CONTRIBUTING.md) (the workflow these templates enforce), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) (the spec-first rule in the PR template)
