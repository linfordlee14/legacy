# AUTHENTICATION
### Identity and authentication for every principal in the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SECURITY](SECURITY.md), [AUTHORIZATION](AUTHORIZATION.md), [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) |

---

## 1. Purpose

This document specifies how every principal proves identity to Legacy: the owner, trusted users, the estate steward, machine consumers, and the platform's own agent services. Because Legacy guards a lifetime of deeply personal content, authentication must be strong enough to protect P2 and P3 content for decades, yet recoverable enough that the owner is never permanently locked out of his own legacy, and transferable enough that succession can genuinely happen.

## 2. Goals

- Strong, phishing-resistant authentication for high-privilege principals.
- A recovery design that never becomes the weakest link.
- A succession activation path that is deliberate, verifiable, delayed, and cancellable.
- Least-privilege machine and service identities with full auditability.

## 3. Scope

**In scope:** identity model, login flows, MFA policy, session management, personal access tokens, service identities, account recovery, and succession activation authentication.

**Out of scope:** what authenticated principals may do (see [AUTHORIZATION](AUTHORIZATION.md)); transport and storage encryption (see [SECURITY](SECURITY.md)).

## 4. Requirements

### 4.1 Identity model

| Principal | Description | Credential class |
|-----------|-------------|------------------|
| Owner | Linford Musiyambodza; the only P3-capable human principal | OIDC login plus mandatory MFA |
| Trusted User | Collaborator, mentee, or family member holding P1 grants | OIDC login plus MFA strongly encouraged, required for grant ceilings above P0 content download |
| Steward | Estate steward or executor; elevated only after succession activation | OIDC login plus mandatory MFA, registered in advance |
| Machine Consumer | External integration or future AI session using the API | Scoped personal access token (PAT) |
| Agent Service | Internal workload identity per canonical agent | Platform-issued workload credentials, short-lived |

Identity provider: managed OIDC, with Supabase Auth as the default decision consistent with the baseline stack in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §9 (a design decision anchored to a 🟡 stack claim; alternatives remain open). Social login providers may be attached for convenience but never reduce MFA requirements.

### 4.2 Authentication strength

- MFA is mandatory for Owner and Steward (NFR-028): WebAuthn/passkeys preferred, TOTP as fallback. SMS is not an accepted factor.
- Password policy (where passwords exist at all): length-first, breach-list screening, no forced periodic rotation.
- New-device sign-in requires step-up verification and generates an owner notification.
- Brute force and credential stuffing controls: progressive delays, IP and identity rate limits, breached-credential rejection, and alerting per [OBSERVABILITY](../deployment/OBSERVABILITY.md).

### 4.3 Sessions and tokens

- Access tokens are short-lived (target 15 minutes); refresh tokens rotate on every use and are revocable individually and globally ("sign out everywhere").
- Sensitive actions (tier changes, grant changes, unsealing, vault export, succession controls) require recent re-authentication (step-up within 10 minutes).
- PATs are scoped (see the scope list in [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.5), expiring (max 12 months), individually revocable, shown once at creation, and logged on every use.
- Agent service credentials are short-lived workload identities bound to a single agent and its tool allowlist; they cannot authenticate interactively.

### 4.4 Account recovery

Recovery must not become a cheaper attack path than login:

- Owner recovery: pre-generated one-time recovery codes (stored offline by the owner) plus a documented cold-start procedure using backup credentials held per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) key escrow.
- Recovery attempts trigger notification on all registered channels and a 24-hour delay before high-privilege recovery completes, cancellable from any authenticated session.
- Trusted-user recovery: standard provider flow; their grants are re-confirmable by the owner afterwards.

> TODO(decision): whether to add a trusted-contact (social) recovery path for the owner. It improves lockout resilience but widens the attack surface; decide before Phase 1 exit with the risk register entry in [RISKS](../roadmap/RISKS.md) in view.

### 4.5 Succession activation

Succession is an authentication event before it is anything else. Design (legal mechanics pending professional review):

1. **Pre-registration.** The owner registers the steward identity in advance, with MFA enrolled and verified at registration time. The steward holds no elevated access while the owner is active.
2. **Trigger.** The steward initiates activation via `POST /v1/succession/activation`, supplying the agreed legal evidence reference.
3. **Verification conditions.** All must hold: steward MFA authentication; the legal evidence reference recorded; a waiting period (default 30 days) during which every owner channel is notified repeatedly.
4. **Cancellation.** Any successful owner authentication during the waiting period cancels activation and locks it for a cooling-off period.
5. **Completion.** After the delay, steward elevation applies per [AUTHORIZATION](AUTHORIZATION.md) succession mode, P3 release conditions referencing succession begin evaluating, and every step is written to the audit log.

> TODO(verify): the legal trigger (death certificate handling, executor authority under South African law) requires professional legal review before implementation. The waiting-period length and evidence requirements are design proposals.

### 4.6 Authentication event auditing

All authentication events (success, failure, MFA challenges, recovery attempts, PAT creation and use, succession steps) are recorded as `AuditLogEntry` rows: append-only, tamper-evident (NFR-030), and queryable via `GET /v1/audit`.

## 5. Acceptance Criteria

- AuthN test matrix per [TESTING](../testing/TESTING.md) covers every principal class: MFA enforcement, session expiry and rotation, revocation propagation within 60 seconds, step-up on sensitive actions.
- Recovery drill: the owner completes documented recovery from total credential loss using offline materials only; the 24-hour delay and notifications fire.
- Succession dry run: a test steward completes pre-registration through simulated activation; owner cancellation works at every stage of the waiting period.
- No authentication path exists that bypasses MFA for Owner or Steward, verified by review and tests.

## 6. Dependencies

- Managed OIDC provider (default decision: Supabase Auth) and WebAuthn support in target browsers.
- [AUTHORIZATION](AUTHORIZATION.md): role elevation semantics that authentication events unlock.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): key escrow used by cold-start recovery and succession.
- [OBSERVABILITY](../deployment/OBSERVABILITY.md): audit sink and alerting.

## 7. Risks

- Owner lockout is the mirror risk of attacker lockout; the recovery design balances both, and the TODO(decision) in §4.4 is the open trade-off.
- Succession activation fraud (forged evidence, coerced steward); mitigated by the waiting period, multi-channel notification, and cancellation lock.
- Provider dependency: an OIDC provider outage blocks login; mitigated by session longevity choices and the vendor exit path (NFR-025).
- Decades-scale credential drift (dead phone numbers, expired passkeys); mitigated by an annual credential health review on the operations calendar.

## 8. Future Enhancements

- Hardware security key enrollment for the owner as primary factor.
- Anomaly-based sign-in risk scoring.
- Delegated, time-boxed "guest researcher" identities if the public researcher API ships (see [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)).

## 9. Examples

The owner signs in on a new laptop with a passkey; a step-up challenge and a notification to existing sessions follow. Later he creates a PAT scoped `read:private` for a personal script; the token shows once, its every use appears in the audit log, and it expires in 90 days. Years later, the steward initiates activation with the agreed evidence reference; the owner, alive and traveling, receives notifications, signs in, cancels, and the attempt is locked and logged.

## 10. Open Questions

- Trusted-contact recovery (§4.4 TODO): include or not?
- Succession legal mechanics (§4.5 TODO): pending legal review.
- Should trusted users with P1 grants above a sensitivity threshold require mandatory MFA rather than encouraged? Current answer: yes for content download ceilings; revisit with real grant usage data.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §1 (owner identity), §10 (the people who might become trusted users or stewards, all 🟡).
- NIST SP 800-63B (digital identity guidelines), WebAuthn (W3C), OAuth 2.0 / OIDC specifications.

## 12. Related Specifications

- [AUTHORIZATION](AUTHORIZATION.md), [SECURITY](SECURITY.md), [PRIVACY](PRIVACY.md)
- [API_SPECIFICATION](../api/API_SPECIFICATION.md), [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)
- [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (FR-SEC group), [USE_CASES](../specs/USE_CASES.md)
