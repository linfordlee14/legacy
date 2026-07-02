# NON_FUNCTIONAL_REQUIREMENTS
### Quality attributes, constraints, and service targets for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md), [SYSTEM_REQUIREMENTS](SYSTEM_REQUIREMENTS.md), [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) |

---

## 1. Purpose

This document defines the non-functional requirements (NFRs) for Legacy: the measurable quality attributes the platform must exhibit regardless of which features are being exercised. Functional behavior is specified in [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md); this document specifies how well that behavior must perform, how safely, how durably, and at what cost.

Legacy is a single-owner platform intended to operate for decades and to remain restorable by non-experts after the owner can no longer maintain it. Longevity, provenance integrity, and privacy therefore rank above raw performance in every trade-off.

## 2. Goals

- Make every quality attribute measurable and testable, with explicit verification methods.
- Encode the platform's defining constraints (decades-scale durability, tier-aware honesty, P3 isolation) as hard requirements, not aspirations.
- Give a solo founder realistic targets: strict where harm is irreversible (data loss, privacy), pragmatic where it is not (availability of a personal workspace).
- Provide the quality gates referenced by [CI_CD](../deployment/CI_CD.md) and [TESTING](../testing/TESTING.md).

## 3. Scope

**In scope:** performance, capacity, availability, durability and longevity, security, privacy and compliance, accessibility, explainability, maintainability, portability, cost, observability, and disaster recovery requirements for all Legacy components described in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md).

**Out of scope:** functional behavior (see [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md)), implementation technique, and organizational policy not expressible as a system property.

All numeric targets in this document are design proposals for v1. They may be revised through the change process in [CONTRIBUTING](../CONTRIBUTING.md), never silently.

## 4. Requirements

Priorities use MoSCoW. Every requirement lists its verification method (how [TESTING](../testing/TESTING.md) or operations will prove it).

### 4.1 Performance

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-001 | Lexical search returns first results within 300 ms at p95 over the reference corpus | Should | Performance test |
| NFR-002 | Hybrid (semantic plus lexical) search returns ranked results within 1.5 s at p95 | Must | Performance test |
| NFR-003 | RAG question answering streams its first token within 3 s at p95 | Must | Performance test |
| NFR-004 | A complete cited RAG answer finishes within 30 s at p95 | Should | Performance test |
| NFR-005 | A single ingested text document becomes searchable within 2 minutes of upload | Must | Integration test |
| NFR-006 | A batch of 100 mixed documents completes ingestion within 8 hours (overnight window) | Should | Load test |
| NFR-007 | Knowledge graph neighborhood queries (2 hops) return within 500 ms at p95 | Should | Performance test |
| NFR-008 | Timeline range queries return within 800 ms at p95 | Should | Performance test |
| NFR-009 | Private Workspace initial page becomes interactive within 3 s on mid-range hardware and a 10 Mbps connection | Should | Lighthouse-style audit |
| NFR-010 | Public Portfolio pages become interactive within 2 s under the same conditions | Should | Lighthouse-style audit |

### 4.2 Capacity and scalability

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-011 | The design supports a corpus of at least 100,000 knowledge items and 10 million embedding chunks without architectural change | Must | Design review, load test |
| NFR-012 | The design supports at least 40 years of continuous accumulation at the assumed growth rate | Must | Capacity model review |
| NFR-013 | The Private Workspace supports the owner plus at least 10 concurrent trusted users | Must | Load test |
| NFR-014 | The Public Portfolio tolerates bursts of at least 500 concurrent visitors without affecting workspace operation | Should | Load test |

> TODO(verify): actual corpus size and growth rate are unknown. Seed the capacity model with real numbers after the first ingestion phase (see the FR-ING group).

### 4.3 Availability

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-015 | Private Workspace availability of 99.5 percent measured monthly | Should | Uptime monitoring |
| NFR-016 | Public Portfolio availability of 99.9 percent measured monthly | Should | Uptime monitoring |
| NFR-017 | Loss of any external LLM provider degrades AI features gracefully (fallback routing or clear unavailability notice); browsing, search, and capture continue | Must | Chaos test |
| NFR-018 | A read-only mode exists that serves the corpus even when write paths or AI services are down | Should | Chaos test |
| NFR-019 | The exported Legacy Vault is readable with zero platform infrastructure (standard file tools only) | Must | Vault verification drill |

### 4.4 Durability and longevity

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-020 | No committed knowledge item is ever lost: durability backed by the 3-2-1-1-0 backup strategy in [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) | Must | Restore drills |
| NFR-021 | All canonical content is stored or exportable in open, non-proprietary formats (Markdown, JSON, standard media formats) | Must | Vault format audit |
| NFR-022 | Deletion is soft by default; permanent erasure happens only through the explicit redaction workflow with tombstones | Must | Data layer test |
| NFR-023 | A format longevity review runs at least every 5 years, with documented migration decisions | Must | Process audit |
| NFR-024 | Embeddings are re-derivable from source content; loss of a vector index never causes knowledge loss | Must | Rebuild drill |
| NFR-025 | The platform survives the disappearance of any single vendor: each managed service has a documented, tested exit path | Must | Annual exit-path review |

### 4.5 Security

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-026 | All network transport uses TLS 1.3 or later | Must | Configuration scan |
| NFR-027 | All data at rest is encrypted with industry-standard algorithms; P3 Sealed content uses a separate key hierarchy per [SECURITY](../security/SECURITY.md) | Must | Configuration audit |
| NFR-028 | MFA is enforced for Owner and Steward accounts | Must | AuthN test matrix |
| NFR-029 | Critical dependency vulnerabilities are patched within 72 hours of advisory publication; high within 14 days | Must | Vulnerability management audit |
| NFR-030 | The audit log is append-only and tamper-evident | Must | Audit log test |
| NFR-031 | Agents operate under per-agent tool allowlists and can never exceed the invoking principal's access ceiling | Must | Authorization test matrix |

### 4.6 Privacy and compliance

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-032 | P3 Sealed content never leaves the system boundary: it is excluded from external model calls, telemetry, and non-vault exports | Must | Egress test, code review gate |
| NFR-033 | Logs and telemetry never contain P2 or P3 content; content is referenced by ID only | Must | Log audit, redaction test |
| NFR-034 | The platform aligns with POPIA; data subject requests (access, correction, erasure, portability) complete within 30 days | Must | DSR workflow test |
| NFR-035 | Privacy-tier filtering executes before retrieval results reach any model context or API response | Must | Retrieval layer test |
| NFR-036 | Every processing of third-party personal data (collaborators, mentors) follows the consent posture in [PRIVACY](../security/PRIVACY.md) | Must | Privacy review |

### 4.7 Explainability and provenance

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-037 | 100 percent of RAG and twin answers carry citations resolvable to Source records | Must | Citation coverage eval |
| NFR-038 | No AI output presents a 🟡 self-reported or 🔴 flagged claim as established fact; attribution phrasing is mandatory | Must | Tier-discipline eval suite |
| NFR-039 | Confidence tiers are visible wherever claim-derived content is displayed (UI badges per [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md)) | Must | UI test |
| NFR-040 | Every agent run is fully traceable: steps, tools, model calls, tokens, and costs are inspectable | Must | AgentRun trace test |

### 4.8 Accessibility

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-041 | All surfaces conform to WCAG 2.2 level AA per [ACCESSIBILITY](../ui/ACCESSIBILITY.md) | Must | Automated plus manual audit |
| NFR-042 | Every workflow is completable with keyboard alone | Must | Keyboard audit |
| NFR-043 | Confidence and privacy indicators convey meaning through text, never color or emoji alone | Must | Component review |

### 4.9 Maintainability and operability

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-044 | Implementation follows the spec-first rule: shipped behavior traces to a specification section, and deviations update the spec first | Must | Traceability audit per [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) |
| NFR-045 | Routine operations (deploys, backups, monitoring review) require no more than 4 hours per month of owner time | Should | Ops time tracking |
| NFR-046 | A competent engineer unfamiliar with the codebase can stand up a working development environment within one day using repository documentation alone | Should | Onboarding drill |
| NFR-047 | Model or prompt changes pass the AI evaluation gate before production | Must | CI gate |

### 4.10 Cost

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-048 | Monthly operating cost stays within the owner-defined ceiling | Must | Cost dashboard |
| NFR-049 | Token spend alerts fire at 80 percent of the monthly AI budget; hard caps prevent runaway agent loops | Must | Budget test |
| NFR-050 | Median cost per cited RAG answer stays under a defined target through routing and caching | Should | Cost sampling |

> TODO(verify): the owner's actual monthly budget ceiling and per-answer cost target are not on record. Set both before Phase 3 (see [ROADMAP](../roadmap/ROADMAP.md)).

### 4.11 Disaster recovery

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| NFR-051 | Recovery Point Objective: 24 hours or better for all corpus data | Must | Restore drill |
| NFR-052 | Recovery Time Objective: 72 hours for full platform restore; 8 hours for read-only corpus access | Must | Restore drill |
| NFR-053 | Restore procedures are executable by a technically competent steward who did not build the system, using documentation alone | Must | Steward drill |

## 5. Acceptance Criteria

- Every NFR above has at least one automated or scheduled manual verification wired into [CI_CD](../deployment/CI_CD.md), [TESTING](../testing/TESTING.md), or the operations calendar in [OBSERVABILITY](../deployment/OBSERVABILITY.md).
- Performance NFRs are measured against a documented reference corpus and reference hardware profile, recorded in the test plan.
- The two TODO(verify) items in this document are resolved (real capacity numbers, real budget ceiling) before Phase 3 entry.
- No release ships while a Must-priority NFR is failing its verification.

## 6. Dependencies

- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md): component boundaries that these attributes constrain.
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md): control catalogs that implement NFR-026 through NFR-036.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): implements NFR-020 and NFR-051 through NFR-053.
- [TESTING](../testing/TESTING.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md): verification machinery.
- External providers (LLM APIs, managed hosting): their published SLAs bound NFR-015 through NFR-017.

## 7. Risks

- Targets set without production data may be unrealistically strict or loose; mitigated by the Phase 3 review checkpoint.
- Solo-founder operations make scheduled drills (restore, steward, onboarding) easy to skip; mitigated by calendar automation and the risk register (see RISK entries in [RISKS](../roadmap/RISKS.md)).
- External provider SLA changes can silently invalidate availability targets; mitigated by the annual exit-path review (NFR-025).
- Over-investment in performance tuning for a single-user system could starve durability work; the priority ordering in §1 governs.

## 8. Future Enhancements

- Percentile-based SLO dashboards with error budgets once telemetry matures.
- Automated capacity forecasting from observed growth.
- Formal availability tiering if family multi-user expansion ships (see [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)).

## 9. Examples

- **NFR-038 in practice.** Asked "Did SpazaLink win 3rd place at SA Startup Week 2026?", the twin must answer in the pattern: "Linford reports a 3rd place finish for SpazaLink at SA Startup Week 2026, but this is flagged as unverified in the canonical context." A response asserting the placement as fact fails the tier-discipline eval and blocks release.
- **NFR-032 in practice.** A sealed journal entry (P3) exists in the corpus. An egress test issues every retrieval and export path and asserts the entry's content never appears in any external model request payload, log line, or non-vault export.
- **NFR-053 in practice.** A steward drill hands the restore runbook and backup credentials to a volunteer engineer with no prior exposure; success means read-only corpus access within 8 hours.

## 10. Open Questions

- What are the real corpus growth numbers? (Blocks final capacity model; NFR-011, NFR-012.)
- What is the owner's monthly cost ceiling? (Blocks NFR-048 through NFR-050 calibration.)
- Should Public Portfolio availability be raised by serving it as a static export? Decision deferred to Phase 5 planning.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §0 (confidence tiers, the never-upgrade rule), §7 (flagged achievement claims used in examples).
- WCAG 2.2 (W3C Recommendation), POPIA (Protection of Personal Information Act, South Africa).
- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) for ID scheme and tier vocabulary.

## 12. Related Specifications

- [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md), [SYSTEM_REQUIREMENTS](SYSTEM_REQUIREMENTS.md), [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md)
- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md)
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md), [OBSERVABILITY](../deployment/OBSERVABILITY.md)
- [TESTING](../testing/TESTING.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md), [ACCESSIBILITY](../ui/ACCESSIBILITY.md)
