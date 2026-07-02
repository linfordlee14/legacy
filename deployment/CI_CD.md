# CI_CD
### Continuous integration and delivery for the Legacy specification repository and the future implementation

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [DEPLOYMENT](./DEPLOYMENT.md), [TESTING](../testing/TESTING.md) |

---

## 1. Purpose

This specification defines how changes reach production safely: branch strategy, pipeline stages for the current specification-only repository, pipeline stages for the future implementation, release and versioning discipline, rollback, environment promotion, secrets in CI, review policy adapted to a solo founder, and artifact retention. All pipelines are described in prose and tables; no pipeline definitions are implemented in this repository.

## 2. Goals

1. Treat specification changes with the same rigor as code changes: reviewed, checked, versioned.
2. Make the future implementation pipeline strict enough that a solo founder can trust an all-green run as permission to deploy.
3. Gate production behind an AI evaluation gate so that regressions in groundedness or privacy tier discipline cannot ship silently.
4. Keep every release identifiable, reproducible, and reversible.
5. Keep CI credentials short-lived and least-privilege so the pipeline is not the weakest security link.

## 3. Scope

### In scope
- Branch strategy and protection rules.
- Specification repository checks (current phase).
- Implementation pipeline stages (future phase), including the AI evaluation gate.
- Release and versioning policy, CHANGELOG discipline, tagged releases.
- Rollback procedure at pipeline level.
- Environment promotion rules.
- Secrets handling within CI.
- Required status checks and review policy.
- Artifact retention.

### Out of scope
- Hosting topology and deployment mechanics (see [DEPLOYMENT](./DEPLOYMENT.md)).
- Test case content and coverage targets (see [TESTING](../testing/TESTING.md) and [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)).
- Evaluation dataset design for AI quality (see [RAG_PIPELINE](../ai/RAG_PIPELINE.md) and [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md)).
- Executable pipeline definitions of any kind.

## 4. Requirements

Document-local requirement IDs (CI-##) are used below. They roll up to the FR-OPS group in the `specs/` documents.

### 4.1 Branch strategy

| ID | Requirement |
|----|-------------|
| CI-01 | The default branch is protected: no direct pushes, no force pushes, no deletion. All changes arrive by pull request. |
| CI-02 | Work happens on short-lived feature branches named `<type>/<short-topic>` where type is one of `spec`, `feat`, `fix`, `chore`, `docs`. |
| CI-03 | Specification changes are reviewed like code: a pull request with a diff, required checks, and an explicit approval before merge. |
| CI-04 | `knowledge/MASTER_CONTEXT.md` is immutable per [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md); any pull request touching it fails a dedicated check unless the change is an approved consolidation pass explicitly labeled as such by the owner. |
| CI-05 | Merges to the default branch use squash or fast-forward with a conventional, imperative commit message referencing the affected documents. |

### 4.2 Pipeline for the current specification-only repository

These are described checks, to be implemented when the repository gains automation; until then they run as a manual pre-merge checklist.

| Stage | Check | Failure condition |
|-------|-------|-------------------|
| 1. Markdown lint | Well-formed Markdown, consistent heading levels, no broken tables | Any lint error |
| 2. Relative link check | Every intra-repo link resolves to an existing file and anchor | Any dead link |
| 3. Conventions: sections | Every spec contains the 12 mandatory sections in order | Missing or misordered section |
| 4. Conventions: title block | Title block present with Status, Owner, Last updated, Depends on | Missing or malformed block |
| 5. Conventions: style | No em dash characters anywhere in repository content | Any em dash found |
| 6. Conventions: TODO format | Unknowns use the `> TODO(verify): ...` blockquote form | Malformed TODO markers |
| 7. Tier discipline | Biographical claims cite tiers consistent with MASTER_CONTEXT; no 🟡 or 🔴 claim stated as fact | Reviewer judgment plus keyword heuristics |

| ID | Requirement |
|----|-------------|
| CI-06 | All seven specification checks are required status checks on the default branch once automated; until automation exists, the pull request template embeds them as a checklist that the author completes. |
| CI-07 | The link checker treats links into not-yet-authored planned documents (paths listed in the SPEC_CONVENTIONS repository map) as warnings during the authoring phase and as failures after the repository is declared complete. |

### 4.3 Pipeline for the future implementation

When application code exists (in one or more implementation repositories), every pull request runs stages 1 to 7 and every merge to the default branch runs stages 1 to 10; production deploy (stage 11) is manual-approval only.

| Stage | Content | Gate |
|-------|---------|------|
| 1. Lint | Code style for TypeScript and Python | Blocking |
| 2. Type check | TypeScript strict mode; Python type checking | Blocking |
| 3. Unit tests | Fast, isolated tests | Blocking |
| 4. Integration tests | API against ephemeral Postgres with pgvector; queue round-trips | Blocking |
| 5. Security: SAST | Static analysis on both languages | Blocking on high severity |
| 6. Security: dependency audit | Known-vulnerability scan of lockfiles; license check | Blocking on high severity |
| 7. Secret scan | No credentials in diff or history | Blocking |
| 8. Build artifacts | Frontend build; backend OCI image tagged by commit and digest | Blocking |
| 9. Staging deploy | Automatic deploy of the built artifacts to staging | Blocking on deploy failure |
| 10. AI evaluation gate | Groundedness and tier-discipline evals against staging | Blocking, see CI-10 |
| 11. Production deploy | Promotion of the identical artifacts, owner approval required | Manual approval |

| ID | Requirement |
|----|-------------|
| CI-08 | The artifact built at stage 8 is the artifact deployed at stages 9 and 11; no rebuilds between environments (matches the promotion rule in [DEPLOYMENT](./DEPLOYMENT.md)). |
| CI-09 | Integration tests run against disposable infrastructure created for the run and destroyed after it; they never touch staging or production data. |
| CI-10 | The AI evaluation gate runs a fixed, versioned evaluation suite against staging: (a) RAG groundedness, every sampled answer supported by retrieved sources with citations; (b) tier discipline, no P2 or P3 content surfaced to a caller lacking the tier, and no 🟡 or 🔴 claim asserted as verified fact. The gate fails closed: eval infrastructure errors block promotion just as failing scores do. Thresholds are defined with the suite in the AI specs and versioned alongside it. |
| CI-11 | A failed production deploy or a failed post-deploy smoke test triggers the rollback procedure in section 4.5 automatically where the platform supports it, and pages the owner either way. |

### 4.4 Release and versioning

| ID | Requirement |
|----|-------------|
| CI-12 | Releases use semantic versioning: MAJOR for breaking API or schema changes, MINOR for features, PATCH for fixes. The specification repository versions the spec set the same way. |
| CI-13 | `CHANGELOG.md` is updated in the same pull request as the change it describes: human-readable entries grouped under Unreleased until tagged. |
| CI-14 | Every production deploy corresponds to an annotated git tag `vMAJOR.MINOR.PATCH`; the tag, the CHANGELOG entry, and the artifact digests are recorded together in the deployment record. |
| CI-15 | Hotfixes branch from the latest production tag, receive a PATCH version, and merge back to the default branch. |

### 4.5 Rollback procedure

| ID | Requirement |
|----|-------------|
| CI-16 | Rollback means redeploying the previous known-good artifacts (frontend build and backend image digest recorded in the last successful deployment record), not reverting commits under time pressure. |
| CI-17 | Rollback completes within 10 minutes of the decision, per the target in [DEPLOYMENT](./DEPLOYMENT.md). |
| CI-18 | Because migrations are expand-and-contract, rollback never runs a schema downgrade; if a migration itself is faulty, recovery follows [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md) point-in-time procedures instead. |
| CI-19 | After any rollback, the default branch is treated as broken: a fix or revert pull request is the next merge, and the failed tag is marked yanked in the CHANGELOG. |

### 4.6 Environment promotion rules

| ID | Requirement |
|----|-------------|
| CI-20 | Promotion order is fixed: local, then staging, then production. No artifact reaches production without passing staging and the AI evaluation gate. |
| CI-21 | Staging auto-deploys on merge to the default branch; production deploys only on manual approval of a specific staged artifact. |
| CI-22 | Configuration changes promote through the same order as code; a production-only configuration change is an incident-class exception requiring a follow-up reconciliation (mirrors the infrastructure rule in [DEPLOYMENT](./DEPLOYMENT.md)). |
| CI-23 | An artifact older than 14 days in staging must re-run the full pipeline before production promotion (dependencies and evals may have moved). |

### 4.7 Secrets in CI

| ID | Requirement |
|----|-------------|
| CI-24 | CI jobs authenticate to cloud platforms with short-lived, per-run credentials (workload identity or OIDC-federated tokens where the platform supports it); no long-lived cloud keys stored in CI. |
| CI-25 | Where a static secret is unavoidable, it is scoped least-privilege (deploy-only, environment-specific), stored in the CI provider's secret store, and rotated at least every 6 months. |
| CI-26 | Pull requests from forks (should the repository ever accept them) never receive secrets; secret-consuming stages run only on trusted branches. |
| CI-27 | Model API keys used by the AI evaluation gate are staging-scoped, budget-capped keys, distinct from production keys. |
| CI-28 | CI logs are treated as untrusted output: masking is enabled, and the secret scan stage also runs over generated logs of the pipeline itself. |

### 4.8 Required status checks and review policy

Solo-founder adaptation: there is one human. The policy compensates with structured self-review plus AI review rather than pretending a second human exists.

| ID | Requirement |
|----|-------------|
| CI-29 | All blocking stages for the phase (spec checks now, stages 1 to 10 later) are required status checks; administrators are not exempt from them. |
| CI-30 | Every pull request completes a self-review checklist (conventions compliance, tier discipline, security impact, cost impact, rollback story) recorded in the pull request body. |
| CI-31 | Every pull request receives an AI review pass (an LLM reviewer prompted with SPEC_CONVENTIONS and the security and privacy specs) whose findings are addressed or explicitly dismissed with a reason before merge. |
| CI-32 | Changes touching authentication, authorization, privacy tiers, backup, or succession logic require a cooling-off period: authored one day, merged no earlier than the next, to force a second look with fresh eyes. |

> TODO(verify): whether a second human reviewer (a trusted collaborator such as those named in MASTER_CONTEXT section 10, all 🟡) will be granted review access for security-critical changes, or whether the AI-plus-cooling-off policy stands alone. Owner decision, revisit before implementation phase.

### 4.9 Artifact retention

| ID | Requirement |
|----|-------------|
| CI-33 | Production-deployed artifacts (frontend builds, backend images) are retained for at least 12 months or the last 20 releases, whichever is longer, so any recent version remains rollback-eligible. |
| CI-34 | CI working artifacts (test reports, eval reports, logs) are retained 90 days; AI evaluation gate reports for production releases are retained permanently as part of the release record. |
| CI-35 | Retention of anything containing telemetry follows [OBSERVABILITY](./OBSERVABILITY.md); CI artifacts must not contain corpus content at all (eval fixtures are synthetic or P0). |

## 5. Acceptance Criteria

1. The default branch rejects direct pushes and merges lacking required checks, verified by attempting both.
2. A pull request introducing an em dash, a missing section, or a dead relative link fails the specification checks (or the manual checklist catches it, in the pre-automation phase).
3. A pull request touching MASTER_CONTEXT without the owner's consolidation label cannot merge.
4. In the implementation phase, an artifact that fails any of stages 1 to 10 cannot be promoted to production by any path.
5. A seeded groundedness regression (an answer without supporting sources) fails the AI evaluation gate and blocks promotion; the same holds for a seeded tier leak.
6. Every production release has a tag, a CHANGELOG entry, and retained artifacts with matching digests.
7. A rollback drill using only the deployment record (no rebuild) completes within 10 minutes.
8. CI runs show no long-lived cloud credentials; secret scanning passes over pipeline logs.

## 6. Dependencies

- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): the rules the spec checks enforce.
- [DEPLOYMENT](./DEPLOYMENT.md): promotion targets, deployment records, rollback mechanics.
- [TESTING](../testing/TESTING.md) and [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md): test suites executed by stages 3 and 4.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md) and [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md): definition and thresholds of the evaluation suite behind the AI gate.
- [SECURITY](../security/SECURITY.md): SAST severity policy, secret management standards.
- External: CI provider capabilities (required checks, OIDC federation, secret masking).

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Solo review misses a defect an outside reviewer would catch | Defect ships | AI review (CI-31), cooling-off for critical paths (CI-32), strict gates |
| AI evaluation gate goes stale as the corpus evolves | Gate passes while quality degrades | Versioned eval suite reviewed quarterly, production groundedness sampling in [OBSERVABILITY](./OBSERVABILITY.md) as backstop |
| Checks not yet automated in spec phase are skipped | Convention drift across documents | Pull request template checklist (CI-06), periodic full-repo audit |
| Eval gate flakiness trains the owner to override it | Gate loses authority | Fail-closed design (CI-10), flake budget tracked, overrides logged in the release record |
| CI provider compromise | Credential and supply chain exposure | Short-lived credentials (CI-24), least privilege, artifact digest verification at deploy |
| Emergency change bypasses the pipeline | Untested production state | Only rollback is allowed outside the pipeline; everything else, including hotfixes, flows through it (CI-15) |

## 8. Future Enhancements

- Automate the seven specification checks as pre-merge status checks.
- Nightly scheduled run of the full AI evaluation suite against staging, independent of merges.
- Canary deploys with automatic rollback on smoke metric regression.
- Reproducible (hermetic) builds with provenance attestation for the container image.
- A release dashboard summarizing version, eval scores, and cost delta per release.

## 9. Examples

Pull request self-review checklist (embedded in the PR template):

```
[ ] 12 sections present and ordered; title block correct
[ ] No em dashes; TODO(verify) format used for unknowns
[ ] Relative links resolve (or are flagged as planned paths)
[ ] Tier discipline: no self-reported or flagged claim stated as fact
[ ] Security, privacy, cost, rollback impact considered and noted
[ ] CHANGELOG updated
```

AI evaluation gate report (illustrative JSON, retained with the release):

```json
{
  "release": "v1.4.0",
  "environment": "staging",
  "suite_version": "evals@2026-07-01",
  "results": {
    "rag_groundedness": {"score": 0.97, "threshold": 0.95, "status": "pass"},
    "citation_coverage": {"score": 0.99, "threshold": 0.98, "status": "pass"},
    "tier_discipline": {"leaks_found": 0, "threshold": 0, "status": "pass"},
    "claim_tier_fidelity": {"violations": 0, "threshold": 0, "status": "pass"}
  },
  "verdict": "promote_allowed",
  "approver": "linford",
  "timestamp": "2026-07-02T16:40:00Z"
}
```

## 10. Open Questions

1. > TODO(verify): second-human review for security-critical changes (see CI-32 note): who, with what access, and for which paths.
2. > TODO(verify): CI provider choice and whether it supports OIDC federation to the selected hosting platforms (interacts with the vendor decisions in DEPLOYMENT).
3. Should the spec repository and the future implementation live in one repository or several? Promotion rules here assume separate artifacts either way.
4. Exact numeric thresholds for the AI evaluation gate: owned by the AI specs, referenced here; initial values above are illustrative.

## 11. References

- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): mandatory structure and style rules the pipeline enforces.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), section 0: the tier system behind the tier-discipline checks.
- Semantic Versioning 2.0.0 and Keep a Changelog conventions (public specifications) as the versioning and CHANGELOG models.

## 12. Related Specifications

- [DEPLOYMENT](./DEPLOYMENT.md)
- [OBSERVABILITY](./OBSERVABILITY.md)
- [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md)
- [TESTING](../testing/TESTING.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md)
- [SECURITY](../security/SECURITY.md)
