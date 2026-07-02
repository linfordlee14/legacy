# SECURITY
### Overall security specification for the Legacy platform: objectives, threat model, and control catalog

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [PRIVACY](./PRIVACY.md), [AUTHENTICATION](./AUTHENTICATION.md), [AUTHORIZATION](./AUTHORIZATION.md) |

---

## 1. Purpose

This document is the top-level security specification for Legacy, a single-owner, lifelong digital legacy platform. Legacy holds the most sensitive data a person can produce: journals, prayer reflections, private conversations, project history, and a digital twin that speaks in the owner's voice. A breach is not an inconvenience here, it is a violation of a life record and of the owner's public reputation.

This specification defines the security objectives, the crown-jewel asset inventory, the threat model, and the control catalog that every other specification in this repository must satisfy. Detailed identity mechanics live in [AUTHENTICATION](./AUTHENTICATION.md), access decisions in [AUTHORIZATION](./AUTHORIZATION.md), and data governance in [PRIVACY](./PRIVACY.md).

## 2. Goals

1. Protect the confidentiality of P2 (Private) and P3 (Sealed) content against every actor except the Owner, for the Owner's entire lifetime and beyond.
2. Preserve the integrity of the corpus and of the digital twin's persona: no unauthorized party can alter memories, claims, or the twin's voice.
3. Keep the platform available to the Owner while accepting that, as a single-owner system, availability ranks below confidentiality and integrity when they conflict.
4. Contain LLM-specific risks (prompt injection, data leakage through model context, tool misuse by agents) with controls designed for agentic systems, not just web applications.
5. Meet the security safeguard duties of POPIA (Protection of Personal Information Act 4 of 2013, South Africa) as the anchor regulation, with GDPR concepts used as supplementary guidance.
6. Make security auditable: every security-relevant event produces an `AuditLogEntry`, and controls are testable in CI (see [CI_CD](../deployment/CI_CD.md)).

## 3. Scope

**In scope**

- Security objectives and asset classification for the whole platform.
- Threat model covering human, machine, and AI-specific adversaries.
- Control catalog: encryption, key management, secrets, supply chain, secure SDLC gates, LLM-specific controls, vulnerability management, incident response, security testing.
- Security requirements that downstream specs (API, database, agents, deployment) must implement.

**Out of scope**

- Authentication mechanics (see [AUTHENTICATION](./AUTHENTICATION.md)).
- Authorization model and enforcement points (see [AUTHORIZATION](./AUTHORIZATION.md)).
- Privacy tier semantics, data subject rights, and regulatory workflows (see [PRIVACY](./PRIVACY.md)).
- Backup schedules and disaster recovery procedures (see [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)); this document only sets the security requirements backups must meet.
- Physical security of third-party data centers (inherited from Supabase and hosting providers; see the shared responsibility note in section 4.3.11).

## 4. Requirements

Formal cross-repository requirement IDs (the FR-SEC group) are maintained in [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md). The identifiers below (SEC-##) are local anchors for this document.

### 4.1 Security objectives and crown-jewel inventory

Legacy classifies assets by damage potential. The crown jewels are the assets whose compromise is unacceptable at any cost tradeoff.

| # | Asset | Description | Privacy tier | Compromise impact |
|---|-------|-------------|--------------|-------------------|
| A1 | Personal corpus (P2/P3) | Journals, prayer reflections, private notes, AI conversations, `MemoryRecord` rows | P2, P3 | Catastrophic: lifelong private record exposed; prayer reflections are religious content and special personal information under POPIA |
| A2 | Sealed content keys | Key hierarchy that encrypts P3 content | N/A (system) | Catastrophic: defeats sealing and succession gating |
| A3 | Credentials and secrets | Owner and Steward credentials, personal access tokens, LLM provider API keys, database credentials | N/A (system) | Critical: enables every other attack |
| A4 | Twin persona integrity | Twin Agent persona definition, voice profile, guardrails, `Claim` confidence tiers | P2 | Critical: reputation attack, false statements in the owner's voice |
| A5 | Knowledge graph and third-party data | `Person` records for collaborators and mentors | P1/P2 | High: harms other data subjects, POPIA exposure |
| A6 | Backups and Legacy Vault exports | Full-corpus snapshots, offline vault archives | Mirrors source tiers | Critical: a stolen backup equals a full breach |
| A7 | Audit log | `AuditLogEntry` stream | N/A (system) | High: loss of integrity hides every other compromise |
| A8 | Succession configuration | Steward designation, activation conditions, sealed-release rules | P2 | High: attacker could trigger or block succession |

- **SEC-01.** Every asset in the inventory MUST have an identified owner control (encryption, access policy, audit) traceable in this document or a linked spec.
- **SEC-02.** Confidentiality of A1 and A2 takes precedence over availability in any design tradeoff. A failure mode that denies the Owner access is preferred over one that exposes P2/P3 content.

### 4.2 Threat model

Likelihood and impact use Low / Medium / High / Critical. Mitigations reference the control catalog (section 4.3).

| # | Threat | Actor | Vector | Impact | Likelihood | Key mitigations |
|---|--------|-------|--------|--------|------------|-----------------|
| T1 | Account takeover of Owner or Steward | External attacker | Phishing, credential stuffing, password reuse | Critical | Medium | Mandatory MFA with passkeys, breached-password screening, login anomaly alerts (4.3.7; [AUTHENTICATION](./AUTHENTICATION.md)) |
| T2 | Session hijacking | External attacker | Stolen tokens, XSS, token replay | High | Medium | Short-lived access tokens, refresh rotation with reuse detection, strict cookie flags, CSP (4.3.1, [AUTHENTICATION](./AUTHENTICATION.md)) |
| T3 | Data exfiltration via API or export | Any authenticated actor or attacker with a token | Bulk API reads, export endpoint abuse, scraping | Critical | Medium | Tier enforcement at retrieval and export layers, rate limits, export watermarking and audit, anomaly detection on volume (4.3.6; [AUTHORIZATION](./AUTHORIZATION.md)) |
| T4 | Prompt injection via ingested content | External attacker (indirect) | Malicious instructions embedded in web pages, documents, or emails that the Ingestion Agent captures and the Retrieval Agent later feeds to other agents | High | High | Instruction/data separation, content sandboxing at ingestion, output filtering, per-agent tool allowlists, no privileged tool calls from retrieved-content context (4.3.6) |
| T5 | Twin impersonation and reputation attack | External attacker, malicious insider | Compromised twin config, poisoned memory, spoofed public twin endpoint | Critical | Medium | Persona config under Owner-only write control, `Claim` tier enforcement in twin answers, provenance citations, signed public artifacts, memory write auditing (4.3.6; [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md)) |
| T6 | Malicious or careless trusted user (P1 overreach) | Trusted Collaborator | Screenshotting, re-sharing, probing beyond granted scope | High | Medium | Time-boxed scoped Grants, per-item tier ceilings, watermarked views for shared content, access review cadence, full read auditing ([AUTHORIZATION](./AUTHORIZATION.md)) |
| T7 | Supply chain compromise | External attacker | Malicious dependency, typosquatting, compromised build pipeline | Critical | Medium | Dependency pinning, lockfile integrity, vulnerability scanning, SBOM, CI provenance checks (4.3.4, 4.3.5) |
| T8 | LLM provider data exposure | Provider breach or provider-side retention misuse | P1/P2 content sent as model context to Anthropic, Google, or Groq | High | Low-Medium | Data minimization in context assembly, provider DPA review, zero-retention configuration where offered, hard rule that P3 never leaves the system boundary (4.3.6; [PRIVACY](./PRIVACY.md)) |
| T9 | Backup theft | External attacker, cloud provider insider | Stolen snapshot, misconfigured storage bucket, intercepted vault export | Critical | Medium | Client-side encryption of backups before storage, separate backup keys, no public buckets, restore-test auditing (4.3.2; [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)) |
| T10 | Physical device loss | Opportunistic thief | Lost or stolen laptop or phone with active session or local vault copy | High | Medium | Full-disk encryption expectation on owner devices, remote session revocation, encrypted Legacy Vault archives, short session lifetimes (4.3.1; [AUTHENTICATION](./AUTHENTICATION.md)) |
| T11 | Audit log tampering | Attacker post-compromise | Deleting or editing `AuditLogEntry` rows to hide activity | High | Low | Append-only audit design, integrity chaining or external log shipping, restricted delete permissions (4.3.8) |
| T12 | Succession abuse | Malicious steward, impersonator | Fraudulent activation of succession to unlock P3 | Critical | Low | Multi-condition activation (legal trigger, verification, time delay), owner veto window, full auditing ([AUTHENTICATION](./AUTHENTICATION.md), [PRIVACY](./PRIVACY.md)) |

> TODO(verify): revisit likelihood ratings once the platform has real deployment telemetry; current ratings are design-time estimates without operational data.

### 4.3 Control catalog

#### 4.3.1 Encryption in transit

- **SEC-03.** All network paths MUST use TLS 1.3 (TLS 1.2 permitted only where a managed dependency cannot yet negotiate 1.3, recorded as an exception). This covers browser to frontend, frontend to API, API to Supabase, API to LLM providers, and webhook traffic.
- **SEC-04.** HSTS MUST be enabled on all public hostnames. Plain HTTP MUST NOT be served.
- **SEC-05.** Internal service-to-service calls MUST authenticate both ends (workload identity plus TLS), not rely on network position alone.

#### 4.3.2 Encryption at rest and key management

- **SEC-06.** All datastores (Postgres, Supabase Storage, backup targets) MUST use provider-level encryption at rest as a baseline.
- **SEC-07.** P3 (Sealed) content MUST additionally use application-level envelope encryption with a key hierarchy separate from the general data keys, so that database-level access alone cannot read sealed plaintext.

```
                 +---------------------------+
                 |  Root key (KMS, HSM-backed)|
                 +------------+--------------+
                              |
            +-----------------+------------------+
            |                                    |
   +--------v---------+                +---------v---------+
   | General KEK       |                | Sealed KEK (P3)   |
   | (P0-P2 services)  |                | separate hierarchy|
   +--------+---------+                +---------+---------+
            |                                    |
   +--------v---------+                +---------v---------+
   | Data keys (DEKs)  |                | Per-item P3 DEKs  |
   | per table/bucket  |                | envelope-encrypted|
   +------------------+                +-------------------+
```

- **SEC-08.** Keys MUST be held in a managed KMS. Root keys never leave the KMS; data encryption keys (DEKs) are envelope-encrypted by key encryption keys (KEKs).
- **SEC-09.** KEKs MUST rotate at least annually and immediately after any suspected compromise. DEK re-encryption follows lazily on next write, with a completion deadline of 90 days.
- **SEC-10.** Access to the Sealed KEK MUST require the succession-activation state or the Owner's authenticated session; no standing service credential may decrypt P3 content.
> TODO(verify): select the concrete KMS (options: Supabase Vault, cloud provider KMS, self-managed with HSM). Decision belongs in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) as an ADR.

#### 4.3.3 Secrets management

- **SEC-11.** Application secrets (LLM provider keys, database credentials, signing keys) MUST live in a secrets manager, never in the repository, environment files committed to git, or client-side code.
- **SEC-12.** Secrets MUST be scoped per environment (dev, staging, production) with no cross-environment reuse.
- **SEC-13.** Secret rotation MUST be possible without downtime; provider API keys rotate at least quarterly.
- **SEC-14.** CI MUST run secret scanning on every push; a detected secret blocks merge and triggers rotation of the exposed value.

#### 4.3.4 Dependency and supply chain policy

- **SEC-15.** All dependencies MUST be version-pinned via lockfiles committed to the repository.
- **SEC-16.** Automated dependency vulnerability scanning MUST run in CI on every pull request and on a daily schedule; Critical findings block deploys.
- **SEC-17.** Each release MUST produce a software bill of materials (SBOM) covering frontend, backend, and agent runtime dependencies.
- **SEC-18.** New dependencies require a lightweight review: maintenance health, install-script behavior, and typosquatting check before adoption.
- **SEC-19.** Build artifacts MUST be produced only by the CI pipeline described in [CI_CD](../deployment/CI_CD.md); no manually built artifact may reach production.

#### 4.3.5 Secure SDLC gates

The CI/CD pipeline (see [CI_CD](../deployment/CI_CD.md)) enforces, at minimum, these security gates in order: secret scan, SAST, dependency audit, license check, SBOM generation, and (for releases) a manual owner approval for changes touching security-critical paths (auth, tier enforcement, key handling, export).

- **SEC-20.** A change to any policy enforcement point (see [AUTHORIZATION](./AUTHORIZATION.md)) MUST NOT ship without a passing authorization test suite run.
- **SEC-21.** Privacy-impacting changes follow the privacy by design checkpoints in [PRIVACY](./PRIVACY.md).

#### 4.3.6 LLM and agent-specific security

Legacy is an agentic system; the OWASP Top 10 for LLM Applications is the reference taxonomy here.

- **SEC-22 (instruction/data separation).** Retrieved content, ingested documents, and third-party text MUST always enter model context as clearly delimited data, never concatenated into the system or instruction channel. Agent prompts treat all corpus content as untrusted data.
- **SEC-23 (content sandboxing at ingestion).** The Ingestion Agent MUST strip or neutralize active content (scripts, embedded instructions, hidden text, tracking pixels) and record the raw original separately from the sanitized working copy.
- **SEC-24 (per-agent tool allowlists).** Each of the twelve canonical agents (see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)) has an explicit tool allowlist. Example: the Retrieval Agent has no write tools; the Research Agent has web access but no corpus write; only the Ingestion and Curation Agents may write content records. Deny by default.
- **SEC-25 (no privileged actions from retrieved context).** A tool call with side effects (write, export, share, external send) MUST NOT be triggerable solely by content found in retrieved documents; it requires an instruction originating from an authenticated principal's request.
- **SEC-26 (output filtering).** Agent outputs destined for the public tier (P0) or for external channels MUST pass an output filter that checks for P1+ content leakage, secrets patterns, and third-party personal data before release.
- **SEC-27 (context tier ceiling).** The Retrieval Agent MUST filter candidate chunks by the invoking principal's effective tier ceiling BEFORE context assembly (see [AUTHORIZATION](./AUTHORIZATION.md) and [RAG_PIPELINE](../ai/RAG_PIPELINE.md)). P3 content is excluded from all model context unconditionally (see [PRIVACY](./PRIVACY.md)).
- **SEC-28 (twin integrity).** The Twin Agent MUST attach provenance to factual statements, respect `Claim` confidence tiers (never asserting a `flagged` claim as fact, per MASTER_CONTEXT section 0), and refuse persona-override instructions from any channel other than Owner configuration.
- **SEC-29 (model router egress control).** The model router is the single egress point to Anthropic, Google, and Groq. It MUST log every outbound context (metadata, not full content), enforce the P3 exclusion rule, and apply provider-specific data minimization.

#### 4.3.7 Brute force, abuse, and edge protections

- **SEC-30.** Public endpoints MUST have rate limiting (per IP and per principal), request size limits, and standard web protections (CSP, X-Content-Type-Options, frame denial).
- Authentication-specific protections (lockout, credential stuffing defense) are specified in [AUTHENTICATION](./AUTHENTICATION.md).

#### 4.3.8 Audit integrity

- **SEC-31.** `AuditLogEntry` storage MUST be append-only from the application's perspective; no API path deletes or mutates audit rows.
- **SEC-32.** Audit events MUST be shipped to a second location (log sink or object storage with retention lock) so a database compromise does not erase history. See [OBSERVABILITY](../deployment/OBSERVABILITY.md).

#### 4.3.9 Vulnerability management and disclosure

- **SEC-33.** Vulnerability intake sources: CI scanning, provider advisories, and external reports. Each finding gets severity (CVSS-informed), an owner, and a deadline: Critical 48 hours, High 7 days, Medium 30 days, Low 90 days.
- **SEC-34.** A public `security.txt` and a disclosure policy MUST exist for the public site, inviting responsible disclosure to a monitored address.
> TODO(verify): confirm the disclosure contact address and whether a small bounty or acknowledgment page is offered; owner decision pending.

#### 4.3.10 Incident response runbook (outline)

| Phase | Actions |
|-------|---------|
| Detect | Alert sources: auth anomaly alerts, audit analysis, provider notifications, rate-limit trips. Triage severity within 4 hours of detection. |
| Contain | Revoke affected sessions and tokens, rotate implicated secrets, disable implicated agents or endpoints, snapshot evidence before changes. |
| Eradicate | Identify root cause, patch, remove attacker artifacts, verify no persistence (webhooks, tokens, altered agent configs, poisoned memory records). |
| Recover | Restore from verified backups if integrity is in doubt, re-enable services progressively, heighten monitoring for 30 days. |
| Notify | POPIA section 22 duty: where personal information has been accessed or acquired by an unauthorized person, notify the Information Regulator (South Africa) and affected data subjects as soon as reasonably possible. Third-party data subjects in the graph (collaborators, mentors) are included. Internal target: notification decision within 72 hours (GDPR-informed discipline applied voluntarily). |
| Learn | Post-incident review within 14 days; findings become requirements or risk register entries in [RISKS](../roadmap/RISKS.md). |

> TODO(verify): no legal counsel is currently engaged for breach-notification review; the POPIA section 22 workflow needs validation by a South African privacy attorney before production launch.

#### 4.3.11 Shared responsibility

Supabase, the hosting platform, and LLM providers own physical security, hypervisor security, and their own service hardening. Legacy owns everything above: configuration, keys it controls, application logic, agent behavior, and data governance. Provider assurances (SOC 2, ISO 27001) are inputs to vendor review.
> TODO(verify): collect and review current compliance attestations for Supabase, the chosen host, Anthropic, Google, and Groq.

### 4.4 Security testing expectations

- **SEC-35.** SAST on every pull request (backend and frontend).
- **SEC-36.** Dependency audit on every pull request and daily.
- **SEC-37.** An authorization regression suite (tier ceilings, deny-by-default, export gating) runs on every change; see [TESTING](../testing/TESTING.md).
- **SEC-38.** LLM red-team test set (prompt injection corpus, exfiltration attempts through the twin, tool-abuse cases) runs before any agent behavior release.
- **SEC-39.** Periodic penetration test of the public surface and API.
> TODO(verify): pentest cadence and provider are undecided; owner budget decision. Proposed default: annual, plus after major architecture changes.

## 5. Acceptance Criteria

1. Every threat T1 through T12 maps to at least one implemented, testable control, and the mapping is maintained in this document.
2. TLS 1.3 is verified on all public endpoints by an automated external check.
3. P3 content is unreadable with database-level access alone: demonstrated by a test that reads raw storage and confirms ciphertext.
4. No standing credential can decrypt P3 content; attempting it produces a denied, audited event.
5. Secret scanning, SAST, and dependency audit gates block merges in CI, verified by intentionally failing fixtures.
6. An SBOM exists for the latest release artifact.
7. The prompt injection test corpus passes: no test case causes a privileged tool call or P1+ leakage into P0 output.
8. Audit log rows cannot be deleted through any API path; the second log sink receives all security events.
9. A tabletop incident response exercise has been run against the section 4.3.10 runbook at least once before production launch, including a mock POPIA notification decision.
10. Every `> TODO(verify)` in this document appears in section 10 and has an owner or trigger condition.

## 6. Dependencies

- [AUTHENTICATION](./AUTHENTICATION.md): identity, MFA, sessions, succession activation.
- [AUTHORIZATION](./AUTHORIZATION.md): enforcement points that implement tier ceilings.
- [PRIVACY](./PRIVACY.md): tier semantics, POPIA alignment, LLM provider data flows.
- [CI_CD](../deployment/CI_CD.md): pipeline gates that operationalize sections 4.3.4 and 4.3.5.
- [OBSERVABILITY](../deployment/OBSERVABILITY.md): alerting and log shipping for detection and audit integrity.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): encrypted backups, restore verification.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) and [RAG_PIPELINE](../ai/RAG_PIPELINE.md): agent tool allowlists and retrieval-time filtering.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): storage of tiers, grants, audit entries, encrypted fields.

## 7. Risks

| Risk | Notes | Mitigation direction |
|------|-------|----------------------|
| Single-owner key loss | Envelope encryption makes P3 unrecoverable if the key hierarchy is lost | Recovery codes, KMS durability, documented recovery drill; tension with SEC-10 is acknowledged and resolved in favor of confidentiality |
| Security controls outpace a solo operator | One person operates this platform; heavy processes may be skipped under time pressure | Automate gates in CI so security does not depend on discipline alone |
| LLM controls are a moving target | Prompt injection defenses are not provably complete | Defense in depth (SEC-22 through SEC-29), red-team suite updated quarterly |
| Provider posture changes | An LLM provider changes retention or training policies | Model router abstraction allows provider exit; DPA review cadence in [PRIVACY](./PRIVACY.md) |
| Audit volume cost | Full auditing has storage and cost weight | Tiered retention: security events long-lived, routine reads summarized |

## 8. Future Enhancements

- Client-side (end-to-end) encryption option for journals, where even the server cannot read P2 content; deferred because it conflicts with server-side embedding and retrieval.
- Hardware security key enforcement (FIDO2 only, no TOTP fallback) once owner device inventory supports it.
- Anomaly detection on retrieval patterns (ML-based exfiltration detection).
- Confidential computing or self-hosted inference for P2 content to remove T8 entirely.
- Formal SOC 2-style self-assessment once the platform serves external trusted users at scale.

## 9. Examples

Audit entry for a blocked prompt injection attempt (illustrative shape, authoritative schema in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)):

```json
{
  "audit_id": "aud_01J9X4T8",
  "timestamp": "2026-07-02T14:22:05Z",
  "category": "llm_security",
  "event": "tool_call_blocked",
  "principal": "agent:retrieval",
  "invoking_user": "usr_owner",
  "detail": {
    "agent_run": "run_88f2",
    "attempted_tool": "export.create",
    "reason": "side_effect_tool_from_retrieved_context",
    "source_chunk": "chunk_4471",
    "source_artifact": "art_web_20260630_113"
  },
  "policy_version": "authz-2026.07",
  "outcome": "denied"
}
```

Incident severity classification (used in the runbook, section 4.3.10):

| Severity | Definition | Example |
|----------|------------|---------|
| SEV-1 | Confirmed exposure of P2/P3 content or key material | Backup bucket found public |
| SEV-2 | Compromise of a credential or agent without confirmed data exposure | Leaked PAT rotated before use |
| SEV-3 | Contained attempt, controls held | Prompt injection blocked by SEC-25 |
| SEV-4 | Hygiene finding | Dependency CVE with no exposed path |

## 10. Open Questions

1. Which KMS backs the key hierarchy (Supabase Vault, cloud KMS, HSM-backed)? (section 4.3.2)
2. Disclosure contact and whether to offer acknowledgment or bounty. (section 4.3.9)
3. Pentest cadence and provider budget. (section 4.4)
4. Legal review of the POPIA section 22 notification workflow: no counsel engaged yet. (section 4.3.10)
5. Provider compliance attestations to collect and review. (section 4.3.11)
6. Threat likelihoods need recalibration after first production telemetry. (section 4.2)

## 11. References

- POPIA: Protection of Personal Information Act 4 of 2013 (South Africa), especially sections 19 to 22 (security safeguards and notification).
- OWASP Top 10 for Large Language Model Applications.
- OWASP Application Security Verification Standard (ASVS) as a control checklist source.
- NIST SP 800-61 (incident handling) as the runbook pattern source.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) section 0 (confidence tiers) and section 5 (owner's security background).

## 12. Related Specifications

- [PRIVACY](./PRIVACY.md), [AUTHENTICATION](./AUTHENTICATION.md), [AUTHORIZATION](./AUTHORIZATION.md)
- [CI_CD](../deployment/CI_CD.md), [OBSERVABILITY](../deployment/OBSERVABILITY.md), [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md), [DEPLOYMENT](../deployment/DEPLOYMENT.md)
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md)
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [API_SPECIFICATION](../api/API_SPECIFICATION.md)
- [TESTING](../testing/TESTING.md), [RISKS](../roadmap/RISKS.md)
