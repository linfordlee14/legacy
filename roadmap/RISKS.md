# RISKS
### The risk register for the Legacy platform and its specification-driven delivery

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [ROADMAP](ROADMAP.md), [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md), [SECURITY](../security/SECURITY.md) |

---

## 1. Purpose

This register names the ways Legacy can fail, honestly and specifically, so mitigations are designed rather than improvised. Legacy's failure modes are unusual: beyond ordinary software risk, it can fail by outliving its maintainer badly, by misrepresenting a real person, or by leaking a life's most private thoughts. Those deserve first-class treatment.

## 2. Goals

- Track every material risk with likelihood, impact, mitigation, and early warning signals.
- Bind mitigations to concrete specs and tasks, not intentions.
- Review the register at every phase gate (per [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)) and after any incident.

## 3. Scope

**In scope:** product, technical, security, privacy, delivery, and longevity risks for the platform and this repository. **Out of scope:** the owner's general business or personal risks unrelated to the platform.

Ratings: likelihood and impact on Low / Medium / High. Risk owner is the Owner (Linford) for all entries at this stage.

> TODO(verify): several mitigations would benefit from a second responsible person (steward, collaborator). Assign named delegates when those relationships are formalized (candidates in MASTER_CONTEXT §10 are 🟡).

## 4. Requirements

### 4.1 The register

| ID | Risk | Category | Likelihood | Impact | Mitigation | Early warning signals |
|----|------|----------|-----------|--------|------------|----------------------|
| RISK-01 | Solo-maintainer bus factor: only one person can operate or evolve the system | Longevity | Medium | High | This spec repository as the durable blueprint; steward drills (NFR-053); vault exports; TASK-506 | Drills skipped; docs drifting from reality |
| RISK-02 | Privacy breach of P2/P3 content: personal and reputational harm to the owner and third parties | Privacy | Low | High | Tier enforcement at four points ([AUTHORIZATION](../security/AUTHORIZATION.md) §4.4); P3 isolation (NFR-032); egress tests; encryption and key separation | Authorization denial anomalies; failed egress tests; audit gaps |
| RISK-03 | Twin misrepresentation: AI states 🟡/🔴 claims as fact, or invents opinions, damaging a real person's reputation | AI integrity | Medium | High | The never-upgrade rule as schema constraint and eval gate (NFR-038, TASK-303); disclosure requirements; corpus-grounded refusals per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) | Eval regression; owner spotting wrong claims in answers |
| RISK-04 | Data loss: the corpus, or part of it, is permanently destroyed | Durability | Low | High | 3-2-1-1-0 strategy and drill regimen in [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md); NFR-020 | Failed restore drills; checksum errors; backup job silence |
| RISK-05 | LLM API cost escalation beyond a solo founder's means | Cost | Medium | Medium | Model routing to cheaper tiers, caching, hard caps and alerts (NFR-048/049); local-model future option | Monthly spend trend; cap alerts firing |
| RISK-06 | Vendor lock-in or vendor death across decades (Supabase, Anthropic, hosting) | Longevity | Medium | High | Open formats (NFR-021); documented exit paths reviewed annually (NFR-025); the vault as ultimate fallback | Vendor pricing/policy shifts; deprecation notices |
| RISK-07 | Format rot: today's formats or embeddings unreadable decades on | Longevity | Medium | Medium | Open-format canon; 5-year format reviews (NFR-023); re-derivable embeddings (NFR-024); vault version readers | Format review overdue; niche formats entering the corpus |
| RISK-08 | Verification debt: 🔴 claims accumulate unresolved and eventually leak into public content as fact | Provenance | Medium | High | The verification queue as a product feature (FS-009) seeded from MASTER_CONTEXT §12; publish gates blocking 🔴-dependent pages (FS-010); TASK-002 | Queue growth without burn-down; stale 🟡 claims aging |
| RISK-09 | Prompt injection via ingested or researched content hijacks agents | Security | Medium | High | Instruction/data separation, tool allowlists, outward-action A2 gates ([MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) §4.4); TASK-409 test suite | Injection test failures; unexplained agent behavior in traces |
| RISK-10 | Scope creep across sixteen features stalls delivery permanently | Delivery | High | Medium | Phase gating with exit criteria ([ROADMAP](ROADMAP.md)); FUTURE_FEATURES as the pressure valve; MoSCoW discipline in requirements | Phases without exits; work outside the current phase |
| RISK-11 | POPIA non-compliance in handling third-party personal data | Compliance | Low | Medium | Consent posture and DSR workflows in [PRIVACY](../security/PRIVACY.md); NFR-034/036; legal review TODOs tracked in TASK-006 | Removal requests; unclear lawful basis on new data classes |
| RISK-12 | Third-party complaints: named collaborators or mentors object to their data in the graph | Privacy | Medium | Medium | Minimal public exposure defaults; removal-on-request workflow; 🟡 labeling of §10 relationships | Any inbound complaint; publish previews touching third parties |
| RISK-13 | Model behavior drift after provider upgrades silently degrades grounding or persona | AI integrity | Medium | Medium | Version pinning and regression evals on every model change ([AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md); NFR-047) | Eval score drops; owner-perceived voice drift |
| RISK-14 | Succession failure: the steward cannot activate, operate, or even read the system when it matters | Longevity | Medium | High | The multi-condition activation protocol; steward drills; escrowed runbooks with keys; TASK-505/506; legal review TASK-006 | Steward unregistered; drills failing or skipped; escrow inventory stale |
| RISK-15 | Abandonment: the platform is not valuable early enough and the owner stops using it, leaving a dead archive | Product | Medium | High | Phase 1 delivers daily-use value (capture plus search first); the "first 90 days" narrative in [ROADMAP](ROADMAP.md); dashboard usage honesty | Capture frequency dropping; dashboards unvisited |
| RISK-16 | Trusted-user overreach: a P1 grantee exfiltrates or misuses shared content | Security | Low | Medium | Scoped, expiring grants; audit of use; quarterly access reviews ([AUTHORIZATION](../security/AUTHORIZATION.md) §4.3) | Unusual access patterns in grant usage summaries |
| RISK-17 | Spec drift: implementation quietly diverges from these documents, destroying the repo's authority | Delivery | Medium | High | The spec-first rule and traceability audits in [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md); NFR-044 | PRs without spec citations; stale Status fields |
| RISK-18 | Key loss: encryption keys lost, rendering backups and P3 content unrecoverable | Durability | Low | High | Dual-location escrow with runbooks, annual inventory ([BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.4) | Escrow inventory overdue; single-location drift |

### 4.2 Register operations

- Review cadence: every phase gate, after every incident, and yearly at minimum; each review re-scores likelihood and impact and prunes or adds entries (new entries take new IDs).
- Every High-impact risk must have at least one mitigation that is a testable spec requirement or a tracked task, not a stated intention.
- Accepted risks (no further mitigation planned) are marked as such with rationale, never silently ignored.

## 5. Acceptance Criteria

- Every register entry cites at least one concrete mitigation anchor (spec section, NFR, FS, or TASK).
- Phase gate reviews are recorded (date, changes) in this document's history.
- No High/High risk exists without a mitigation task scheduled in the current or next phase.
- The TODO on delegated risk ownership is resolved or explicitly renewed at each yearly review.

## 6. Dependencies

- [ROADMAP](ROADMAP.md) phase gates as the review trigger.
- Mitigation anchors across the security, deployment, testing, and AI specifications.
- Owner decisions and legal review (TASK-005, TASK-006) for RISK-11 and RISK-14.

## 7. Risks

The register's own meta-risks: staleness (mitigated by gate-bound reviews) and false comfort (a written mitigation is not an implemented one: acceptance criteria demand anchors to testable requirements).

## 8. Future Enhancements

- Quantified risk scoring if the register grows beyond comfortable qualitative review.
- Automated early-warning wiring: dashboards in [OBSERVABILITY](../deployment/OBSERVABILITY.md) surfacing the signal columns directly.

## 9. Examples

At the Phase 2 gate, review finds RISK-08's early warning firing: the verification queue grew from six seeded items to nineteen with no burn-down. The response is concrete: TASK-002 is promoted into the phase plan, and the publish gate check (FS-010) is verified as actually blocking 🔴-dependent pages in staging. The register entry records the review and the re-scored likelihood.

## 10. Open Questions

- Which risks warrant delegated owners once trusted relationships formalize (§3 TODO)?
- Should RISK-15 (abandonment) gain a formal usage SLO the dashboard tracks? Leaning yes at Phase 1 exit.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §10 (potential delegates, 🟡), §12 (verification queue feeding RISK-08).
- ISO 31000 vocabulary as loose guidance for register structure.

## 12. Related Specifications

- [ROADMAP](ROADMAP.md), [TASKS](TASKS.md), [FUTURE_FEATURES](FUTURE_FEATURES.md)
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md), [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)
