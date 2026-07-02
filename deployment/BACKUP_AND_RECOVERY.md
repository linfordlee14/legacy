# BACKUP_AND_RECOVERY
### Backup strategy, the Legacy Vault, and recovery procedures for a platform that must outlive its infrastructure

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [DEPLOYMENT](DEPLOYMENT.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md) |

---

## 1. Purpose

Legacy exists to preserve a lifetime of knowledge for future generations. Every other quality of the platform is negotiable in an emergency; durability is not. This document specifies how the corpus is backed up, how the human-readable Legacy Vault export works, how recovery happens at every scale (one item, one table, the whole platform), and how all of it remains executable by a steward who did not build the system.

## 2. Goals

- Zero permanent loss of committed knowledge (NFR-020), demonstrated by drills, not assumed.
- Independence from any single vendor, medium, region, or decade (NFR-025).
- A vault format readable with standard tools and no Legacy software (NFR-019, NFR-021).
- Recovery procedures a competent outsider can execute from documentation alone (NFR-053).

## 3. Scope

**In scope:** backup coverage, schedules, retention, encryption and key escrow, the Legacy Vault format and cadence, restore procedures, drill regimen, and succession handoff of backup access.

**Out of scope:** high-availability replication within the live platform (see [DEPLOYMENT](DEPLOYMENT.md)); who may trigger exports (see [AUTHORIZATION](../security/AUTHORIZATION.md)).

## 4. Requirements

### 4.1 Strategy: 3-2-1-1-0

| Element | Requirement |
|---------|-------------|
| 3 copies | Live data plus at least two independent backups |
| 2 media | At least two distinct storage classes or providers |
| 1 offsite | At least one copy in a different region and provider than production |
| 1 offline or immutable | At least one copy offline or object-locked (immutable), beyond reach of compromised credentials |
| 0 errors | Every backup verified by checksum and by scheduled restore tests |

### 4.2 Coverage

| Asset | Backed up | Notes |
|-------|-----------|-------|
| PostgreSQL database (all entities, graph, claims, audit log) | Yes: daily full plus point-in-time WAL-class continuous backup | The canonical record |
| Object storage (original media and artifacts) | Yes: daily incremental | Originals are never modified post-ingestion |
| Embeddings and indexes | Yes, low priority | Re-derivable (NFR-024); backed up to shorten RTO, not for durability |
| Configuration and infrastructure definitions | Yes: versioned in git plus included in backup sets | |
| This specification repository | Yes: git remotes plus inclusion in the vault | The platform's blueprint must survive with its data |
| Encryption keys | Escrowed, never in the same backup set as data | See §4.4 |
| Telemetry | No (retention per [OBSERVABILITY](OBSERVABILITY.md)) | Not corpus data |

### 4.3 Schedule and retention ladder

| Cadence | Content | Retention |
|---------|---------|-----------|
| Continuous | Database point-in-time stream | 7 days |
| Daily | Full database snapshot, storage incrementals | 30 days |
| Weekly | Consolidated full set | 6 months |
| Monthly | Full set to offsite immutable storage | 5 years |
| Quarterly | Legacy Vault export (see §4.5) | Latest 8 vaults, then yearly forever |
| Yearly | Archival full set plus vault, checksummed | Indefinite; media refresh per §4.8 |

### 4.4 Encryption and key escrow

- All backups are encrypted with owner-controlled keys; P3 content is additionally wrapped under the separate P3 key hierarchy per [SECURITY](../security/SECURITY.md).
- Keys are escrowed offline in at least two geographically separate locations, sealed, with tamper-evident packaging, and inventoried annually.
- The escrow package includes the recovery runbook (§4.6), not just key material: keys without instructions fail NFR-053.
- Key rotation re-wraps backup keys without re-encrypting historical archives (envelope encryption).

> TODO(verify): the legal instrument giving the steward access to one escrow location upon succession (safe deposit arrangement, attorney custody, or equivalent under South African practice) requires professional advice; record the chosen mechanism here once decided.

### 4.5 The Legacy Vault

The vault is the platform's answer to "what if everything else disappears": a complete, human-readable, open-format export.

| Property | Specification |
|----------|---------------|
| Formats | Markdown for all textual content; JSON for structured data (entities, edges, claims, sources, tiers); original standard formats for media; no proprietary formats (NFR-021) |
| Structure | Folder tree mirroring the knowledge domains; an index document; per-item provenance blocks preserving confidence tiers |
| Integrity | A manifest with per-file checksums and a signed top-level digest |
| Privacy | Tier labels travel with every item; P3 content included only as encrypted bundles with their release conditions attached in plaintext metadata |
| Readability | A person with a file browser and text editor can navigate the corpus; verified by drill (§4.7) |
| Consistency | Exports run against a consistent snapshot, never a live-mutating view |
| Cadence | Quarterly automatic plus on-demand via `POST /v1/vault/exports` |
| Destination | Owner-controlled storage independent of the production provider |

### 4.6 Restore procedures

Runbooks (maintained alongside this spec, tested by drills):

1. **Item-level restore.** Recover a deleted or corrupted item from snapshots or revision history; target minutes.
2. **Point-in-time restore.** Roll the database to a timestamp within the continuous window; target under 4 hours.
3. **Full platform restore.** From offsite backups onto fresh infrastructure per [DEPLOYMENT](DEPLOYMENT.md): database, storage, configuration, then re-derive indexes; targets RTO 72 hours, RPO 24 hours (NFR-051, NFR-052).
4. **Read-only corpus access.** From the latest vault alone, without platform infrastructure: target 8 hours; this is the steward's minimum-viable outcome.
5. **Post-restore verification.** Checksums, row counts against manifests, sampled content reads, and an audit-log continuity check before declaring recovery complete.

### 4.7 Drill regimen

| Drill | Cadence | Pass condition |
|-------|---------|----------------|
| Automated restore test (random snapshot to scratch environment) | Monthly | Checksums and sampled queries pass |
| Point-in-time restore drill | Quarterly | Within targets, documented |
| Vault verification (open latest vault with standard tools, read sampled items, verify manifest) | Quarterly | A human confirms readability |
| Full disaster restore drill | Yearly | RTO/RPO met on clean infrastructure |
| Steward drill (an outsider executes runbook 4, then runbook 3 with support) | Yearly | NFR-053 demonstrated |

Drill results are recorded; two consecutive failures of any drill are a release-blocking incident per [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md).

### 4.8 Longevity operations

- Media and provider refresh review every 5 years: migrate archives forward before formats or vendors decay (NFR-023).
- Checksum re-verification of archival sets yearly; any corruption triggers re-copy from a healthy sibling.
- The vault format itself is versioned; readers for every historical version are documented in the vault index.

## 5. Acceptance Criteria

- All five drill types have run at least once before Phase 5 exit, with documented results meeting their pass conditions.
- An egress-style audit confirms backup sets and vaults respect tier rules (P3 encrypted, nothing above the export's authorization).
- Escrow inventory exists, is dated within 12 months, and includes runbooks with the keys.
- RPO and RTO measurements from the latest yearly drill meet NFR-051 and NFR-052.

## 6. Dependencies

- [DEPLOYMENT](DEPLOYMENT.md): infrastructure definitions used by full restore.
- [SECURITY](../security/SECURITY.md): key hierarchies and escrow security.
- [AUTHORIZATION](../security/AUTHORIZATION.md): who may export, restore, and access escrow.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): entity and manifest structures the vault serializes.
- Provider capabilities: point-in-time recovery, object lock or equivalent immutability.

## 7. Risks

- Backups that silently rot are the classic failure; the 0-errors element and drill regimen exist precisely for this.
- Key escrow is a physical-world dependency (loss, theft, estate disputes); mitigated by dual locations, tamper evidence, and the legal TODO in §4.4.
- Ransomware or credential compromise reaching backups; mitigated by the offline/immutable copy and separate credentials for backup infrastructure.
- Solo-founder drill fatigue; mitigated by automating the monthly drill entirely and calendar-forcing the rest.

## 8. Future Enhancements

- Cross-continent archival copy if family geography warrants it.
- Public-portion vault published as a static archive (pairs with the static portfolio question in [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) §10).
- Automated vault-readability checking (parse and render every file headlessly each quarter).

## 9. Examples

A quarterly vault lands in owner-controlled storage: `timeline/2026/06/talk-gdg-pet-projects.md` contains the CyberBuddy talk entry with its provenance block (`tier: verified`), and `claims/claims.json` carries the flagged achievement claims with their 🔴 status intact, so even a reader decades from now inherits the honesty discipline. During the yearly steward drill, a volunteer engineer receives the runbook and escrow package, mounts the latest vault, and reads that same talk entry within the 8-hour target, never touching Legacy code.

## 10. Open Questions

- Escrow legal mechanism (§4.4 TODO): pending professional advice.
- Should embeddings be dropped from backups entirely once rebuild time is measured? Decide after the first full restore drill produces real numbers.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) preamble (purpose: future AI and generations must be able to reconstruct context), §0 (tiers preserved in the vault).
- 3-2-1 backup rule and object-lock immutability practices (industry standard guidance).

## 12. Related Specifications

- [DEPLOYMENT](DEPLOYMENT.md), [OBSERVABILITY](OBSERVABILITY.md), [CI_CD](CI_CD.md)
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md), [AUTHENTICATION](../security/AUTHENTICATION.md), [AUTHORIZATION](../security/AUTHORIZATION.md)
- [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md), [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md) (FS-016), [RISKS](../roadmap/RISKS.md)
