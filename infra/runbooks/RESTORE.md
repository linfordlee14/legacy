# Restore runbooks 1 and 2

Implements the first two restore procedures of
[`deployment/BACKUP_AND_RECOVERY.md`](../../deployment/BACKUP_AND_RECOVERY.md)
§4.6 and the drill automation of §4.7 (MVP-009). Runbooks 3 to 5 (full
disaster restore, vault-only access, post-restore verification at platform
scale) arrive with the vault work (TASK-504, TASK-508).

**Never restore into production with these tools.** Restores target scratch
or freshly created databases; promoting a verified restore is a deliberate,
separate action.

## Tooling

| Script | Purpose |
|--------|---------|
| `scripts/backup/backup.sh` | Encrypted full backup with manifest (checksums, per-table row counts, schema version) |
| `scripts/backup/restore.sh` | Decrypt, verify checksum, restore into a target database |
| `scripts/backup/restore_drill.sh` | Runbook 2 automation: backup, restore to scratch, verify counts and schema |

Key model (§4.4, DEP-22): backups are hybrid-encrypted. The RSA public key
lives in the backup environment; the private key is owner-held with escrow
copies, never in platform secret managers. Losing the private key makes
backups unreadable: escrow discipline is existential (RISK-18).

Credentials (MVP-009 acceptance): backups run as a dedicated read-only
database role (`legacy_backup`), never the application credential; drill
restores use scratch-side credentials. Create the role once per environment:
a login role with SELECT on all tables in schema public and default
privileges for future tables.

## Runbook 1: item-level restore

Recover a soft-deleted-then-purged or corrupted item.

1. First choice is the application path: soft-deleted rows within the 90-day
   undo window are restorable in place (clear `deleted_at`); edited content
   has revision history.
2. Otherwise, pick the newest backup that predates the loss:
   `ls backups/` (timestamps are UTC).
3. Restore it to a scratch database:
   `LEGACY_BACKUP_PRIVATE_KEY_FILE=... scripts/backup/restore.sh backups/<stamp> <scratch_url>`
4. Extract the item and its dependents (Claims, ClaimSources, Edges,
   EmbeddingChunks referencing it) with `psql \copy` from scratch, and
   re-insert into production via `psql` in one transaction. Preserve the
   original `id` values (identifiers are stable forever, DATABASE_SCHEMA 4.1).
5. Write an AuditLogEntry describing the restore (action `create`, payload
   noting the source backup stamp), and drop the scratch database.

Target: minutes to a single restored item (§4.6).

## Runbook 2: point-in-time restore

1. **Managed production (Supabase):** use the provider's PITR to the target
   timestamp, restoring into a NEW project or branch database, never in
   place. Verify with step 3 before any promotion decision. Enabling PITR on
   the project is a provisioning-time owner action (see manual configuration
   in the step 8 report and DEPLOYMENT §4.2).
2. **Any environment (logical fallback):** restore the newest backup at or
   before the target time with `restore.sh` into a scratch database. The
   granularity of the fallback is the backup cadence; the RPO target of 24
   hours (NFR-051) is met by the daily schedule, and provider PITR tightens
   it further in production.
3. **Verify before trusting:** `restore_drill.sh` encapsulates the checks
   (decrypt, plaintext checksum, schema version, per-table row counts). For
   a manual restore, run its verification block against the restored
   database, then sample-read a handful of known items.

Target: under 4 hours (§4.6).

## Drill automation (§4.7)

- The `backup-drill` job in `.github/workflows/ci.yml` runs the full drill
  against disposable databases on every push and on the monthly schedule
  (cron, third day of the month). A red drill blocks merges like any gate;
  two consecutive failures are release-blocking per QUALITY_ASSURANCE.
- Real-environment drills: `make restore-drill` with the environment's
  source URL, a scratch URL, and the escrowed key pair. Record outcomes in
  the operations log; a failed real drill is SEV-1 (OBSERVABILITY 4.5).
