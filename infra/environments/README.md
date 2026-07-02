# Environment configuration register

This register implements DEP-05, DEP-14, and DEP-18 of
[`deployment/DEPLOYMENT.md`](../../deployment/DEPLOYMENT.md): every environment
is fully described by versioned configuration, regions are recorded in one
place, and only non-secret values live in these files. Secrets live exclusively
in each environment's platform secret manager and are inventoried (names only)
in [`infra/SECRETS_REGISTER.md`](../SECRETS_REGISTER.md).

## Environments (DEP-01)

| Environment | Config file | Status |
|-------------|------------|--------|
| local | `local.env` | Active: containers or native processes on the developer machine |
| staging | `staging.env` | Defined; awaiting owner provisioning (see below) |
| production | `production.env` | Defined; awaiting owner provisioning (see below) |

## Region register (DEP-13, DEP-14)

| Concern | Region | Status |
|---------|--------|--------|
| Compute (container platform) | closest available to Cape Town | TODO(verify): vendor ADR pending (DEPLOYMENT §4.2) |
| Frontend host | edge/CDN default | TODO(verify): vendor ADR pending |
| Supabase project | closest available to Cape Town | TODO(verify): owner provisioning plus POPIA residency review (DEPLOYMENT §4.3) |

## Provisioning state

Staging and production require, in order (owner actions):

1. Vendor selection ADR for the Next.js host and container platform
   (DEPLOYMENT §4.2 TODO; record in `architecture/MASTER_ARCHITECTURE.md`).
2. Accounts created; regions chosen per DEP-13 and recorded above.
3. Secret managers seeded per the secrets register.
4. `staging.env` and `production.env` URL values filled in and committed.

Recreating any environment must require no steps beyond this register and the
runbooks in [`infra/runbooks/`](../runbooks/) (DEP-05).
