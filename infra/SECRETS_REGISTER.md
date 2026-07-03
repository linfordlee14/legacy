# Secrets register

Implements DEP-19 to DEP-21 of [`deployment/DEPLOYMENT.md`](../deployment/DEPLOYMENT.md)
and is referenced from [`security/SECURITY.md`](../security/SECURITY.md).
Names and metadata only: secret values NEVER appear in this repository, in
logs, or in any environment file. Values live only in each environment's
platform secret manager and are never shared across environments.

Owner of every secret: Linford Musiyambodza. Rotation cadence: at most
12 months, immediate on suspected exposure (DEP-20).

## Active secrets

| Name | Purpose | Environments | Stored in | Last rotated |
|------|---------|--------------|-----------|--------------|
| LEGACY_DATABASE_URL | Postgres connection for migrations and (later) the API | staging, production | Platform secret manager per environment; local uses the non-secret docker-compose convention value | pending provisioning |

Rotation procedure for LEGACY_DATABASE_URL: rotate the database password in
Supabase, update the secret manager value, redeploy; the old credential is
invalid immediately.

## Known upcoming secrets (created when their step lands)

| Name | Purpose | First needed at |
|------|---------|-----------------|
| Supabase storage and service-role credentials | Object storage access | Step 10 (MVP-010) |
| OIDC provider credentials | Authentication | Step 4 (MVP-004) |
| Anthropic API key | Model router, stretch scope | Step S1 (MVP-024) |
| Backup encryption keys | Owner-held; escrowed OUTSIDE platform secret managers per DEP-22 and BACKUP_AND_RECOVERY §4.4 | Step 8 (MVP-009) |

Rotation procedures are documented per secret when the secret is created;
an entry without a documented rotation procedure fails review (DEP-20).
