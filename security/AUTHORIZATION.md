# AUTHORIZATION
### Roles, privacy-tier ceilings, grants, and policy enforcement for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [AUTHENTICATION](AUTHENTICATION.md), [PRIVACY](PRIVACY.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) |

---

## 1. Purpose

This document specifies what authenticated principals may do in Legacy. Authorization combines two orthogonal systems: role-based access control (what actions a role can perform) and per-item privacy tiers (what content a principal can see). Effective access is always the intersection: a role's ceiling meets an item's tier, and the more restrictive wins. The posture everywhere is deny by default.

## 2. Goals

- Make the four privacy tiers (P0 Public, P1 Trusted, P2 Private, P3 Sealed) enforceable at every layer, not just the UI.
- Keep the role catalog small and auditable for a single-owner platform.
- Give agents exactly the access their invoking principal has, never more.
- Make every authorization decision explainable and logged.

## 3. Scope

**In scope:** role catalog, permission matrix, tier ceilings, the Grant model, policy enforcement points, agent authorization, succession-mode changes, and authorization auditing.

**Out of scope:** identity proofing and sessions (see [AUTHENTICATION](AUTHENTICATION.md)); tier semantics and governance policy (see [PRIVACY](PRIVACY.md)).

## 4. Requirements

### 4.1 Role catalog and ceilings

| Role | Description | Content ceiling | Notes |
|------|-------------|-----------------|-------|
| Owner | Linford; ultimate authority | P3 (with unseal actions) | Only role that changes tiers, grants, and seals |
| Steward | Estate steward | P1 pre-activation; up to P3 post-activation per release conditions | Elevation only via the succession protocol |
| Trusted Collaborator | P1-granted human | P1, scoped by Grant | No administrative permissions |
| Public Visitor | Unauthenticated or basic account | P0 | Portfolio and public twin only |
| Machine Consumer | PAT-holding integration | Per PAT scope, max P2 | Never P3 |
| Agent Service (x12) | Internal workload identities | Invoking principal's ceiling | Plus per-agent tool allowlists |

### 4.2 Permission matrix (summary)

Actions beyond reading are role-gated regardless of tier:

| Action | Owner | Steward (post-activation) | Trusted | Public | Machine |
|--------|-------|---------------------------|---------|--------|---------|
| Read content at or below ceiling | Yes | Yes | Yes (per grant) | Yes (P0) | Per scope |
| Create and edit content | Yes | Limited (curation, annotation) | No | No | Per `write:content` scope |
| Change privacy tier | Yes | No (proposals only) | No | No | No |
| Seal and unseal (P3) | Yes | Release-condition execution only | No | No | No |
| Manage grants | Yes | Yes (revoke only) | No | No | No |
| Approve agent actions (A2) | Yes | Yes | No | No | No |
| Publish and unpublish (P0) | Yes | Unpublish only | No | No | No |
| Vault export | Yes | Yes | No | No | No |
| Redaction and permanent erasure | Yes | Per documented owner wishes only | No | No | No |
| View audit log | Yes | Yes | Own events only | No | Own events only |

The full matrix (per endpoint group) lives with the contract tests defined in [TESTING](../testing/TESTING.md).

### 4.3 The Grant model

P1 sharing is never role-wide; it is granted:

- A `Grant` binds a principal to a scope (collections, tags, projects, or explicit item lists), a ceiling (at most P1), and an expiry (default 12 months, maximum 24, renewable).
- Grants are created and modified by the owner only, with step-up authentication, and take effect immediately.
- Revocation is immediate: active sessions lose access on next request (revocation check at the policy decision point, not at token issuance).
- Every grant creation, use pattern summary, and revocation is auditable; a quarterly access review lists all active grants for owner confirmation.

### 4.4 Policy enforcement points

Authorization is evaluated at four mandatory points; failing any one denies:

1. **API layer.** Role and scope checks on every request; uniform `not_found` for above-ceiling items (no existence leaks, per [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.2).
2. **Retrieval layer.** Tier filtering applies before ranking and before any content enters model context (NFR-035). This is the invariant that keeps private content out of AI answers.
3. **Export layer.** Vault and any download path re-evaluate tiers at export time; P3 content exports only encrypted under the escrow hierarchy.
4. **UI layer.** Rendering respects tiers for defense in depth; the UI is never the only control.

Policy decisions are centralized (one decision service or library, versioned policies) so the four points cannot drift apart. Every decision carries the policy version that produced it.

### 4.5 Agent authorization

- Agents run under workload identities but always on behalf of an invoking principal; the run inherits that principal's ceiling and cannot raise it (NFR-031).
- Per-agent tool allowlists (defined in [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) §4.1) are enforced by the same policy service; out-of-list tool calls fail closed and alert.
- No agent has permission to change tiers, grants, or seals; those permissions simply do not exist for agent identities, independent of any prompt-level rule.

### 4.6 Succession mode

Succession activation (per [AUTHENTICATION](AUTHENTICATION.md) §4.5) switches the policy set:

- Steward gains the post-activation column in §4.2; owner credentials are suspended (not deleted) pending the documented estate process.
- P3 items whose release conditions reference succession begin releasing on their own schedules; nothing releases in bulk by default.
- A memorial policy variant restricts the public twin per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) post-mortem mode.
- All succession-mode decisions log with the succession policy version for later review.

### 4.7 Auditing

Every authorization denial and every sensitive allow (tier change, grant change, unseal, export, succession action) writes an `AuditLogEntry` with principal, action, item, decision, policy version, and request ID (NFR-030). Denial spikes alert per [OBSERVABILITY](../deployment/OBSERVABILITY.md).

## 5. Acceptance Criteria

- The authorization test matrix exercises every role against every action class and every tier, including agent inheritance and allowlist enforcement; attempted violations fail closed and log.
- Existence-leak tests confirm identical responses (shape and timing tolerance) for "does not exist" and "above ceiling."
- Grant lifecycle tests: creation, scope enforcement, expiry, immediate revocation.
- Succession-mode policy switch is tested end to end in a staging drill, including P3 release-condition evaluation.
- A quarterly access review report is producible from live data with one action.

## 6. Dependencies

- [AUTHENTICATION](AUTHENTICATION.md): principal identity, step-up, and succession triggers.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): `Role`, `Grant`, `AuditLogEntry`, and per-item `privacy_tier`.
- [PRIVACY](PRIVACY.md): tier semantics, release conditions, and governance rules this document enforces.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): agent roster and tool allowlists.

## 7. Risks

- Policy drift between enforcement points; mitigated by the single decision service and contract tests.
- Grant sprawl over years; mitigated by default expiry and the quarterly review.
- Succession-mode bugs are catastrophic and rarely exercised; mitigated by the mandatory staging drill and policy versioning.
- Over-broad PAT scopes; mitigated by least-privilege scope design and audit visibility.

## 8. Future Enhancements

- Attribute-based conditions on grants (for example, watermarked read-only exports for P1 users).
- Purpose-bound access requests ("request access to X for reason Y") with owner one-click decisions.
- Fine-grained sub-tiers within P1 if trusted-user diversity grows (family versus professional collaborators).

## 9. Examples

A mentee holds a grant scoped to the tag `mentorship` at ceiling P1, expiring in 6 months. She searches "leadership lessons": results include P0 and P1 items tagged `mentorship`; an untagged P1 project and all P2 journals are absent, and requesting a known P2 item's URL returns `not_found`. When she asks the twin a question, the Retrieval Agent assembles context under her ceiling: the answer cites only what she could read herself. The owner's quarterly review later shows her grant, its usage summary, and one click renews or revokes it.

## 10. Open Questions

- Should the Steward's pre-activation ceiling be P0 instead of P1? Current design says P1 so the steward can rehearse duties; revisit with the owner.
- Watermarking exports for P1 users: worth the complexity in v1? Deferred to Future Enhancements.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §10 (candidate trusted users, 🟡), §12 (verification queue whose workflow permissions this document gates).
- NIST RBAC model (INCITS 359), OWASP Authorization Cheat Sheet.

## 12. Related Specifications

- [AUTHENTICATION](AUTHENTICATION.md), [PRIVACY](PRIVACY.md), [SECURITY](SECURITY.md)
- [API_SPECIFICATION](../api/API_SPECIFICATION.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (FR-SEC and FR-PRIV groups), [TESTING](../testing/TESTING.md)
