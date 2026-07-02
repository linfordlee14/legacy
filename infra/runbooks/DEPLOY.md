# Deploy and rollback runbook

Implements DEP-23 to DEP-27 of [`deployment/DEPLOYMENT.md`](../../deployment/DEPLOYMENT.md).
Every production deployment follows the same five steps; no ad hoc production
changes, ever.

> TODO(verify): the staging and production commands below bind to the managed
> platforms once the vendor ADR (DEPLOYMENT §4.2) is recorded and accounts are
> provisioned. The procedure itself is final; only the platform CLI bindings
> are pending. Local commands are fully operational now.

## The five steps (DEP-23)

### 1. Build

- Backend: build the immutable container image (DEP-24), tagged with the git
  commit: `docker build -t legacy-api:<git-sha> services/api`. Record the image
  digest; the digest, not the tag, is what gets promoted.
- Frontend: `npm run build` in `apps/web` (on the managed host, triggered by
  the platform's git integration once provisioned).

### 2. Verify

- Run the test suites: `make test`.
- Staging receives the artifacts; automated checks run against staging.
  (The AI evaluation gate joins this step when the ask path ships.)

### 3. Deploy

- Local: `docker compose up --build -d` (uses `infra/environments/local.env`).
- Staging/production: promote the verified image BY DIGEST on the container
  platform; frontend build promoted on the managed host. Owner approval
  required for production (DEP-23 step 3).

### 4. Smoke test

- Run `scripts/smoke_test.sh <base-url> <expected-environment>` within
  15 minutes of deploy. It exercises the health endpoints and asserts the
  environment identity (DEP-06). The smoke script grows with the platform
  (login, search, cited answer) as those capabilities ship (DEPLOYMENT §4.6).

### 5. Rollback (DEP-25)

- If any smoke check fails or an alert fires in the first hour: roll back
  first, investigate second.
- Local: `docker compose down && git checkout <previous-sha> && docker compose up --build -d`.
- Staging/production: platform-native re-deploy of the previous image digest
  (backend) and previous build (frontend). Target: under 10 minutes from the
  decision.
- Schema migrations are expand-and-contract (DEP-26), so rollback never
  requires a schema downgrade.

## Deployment record (DEP-27)

Until the audit trail ships (MVP-008), append a record per deployment to
`infra/runbooks/DEPLOY_LOG.md`: date, deployer, git sha, image digest,
migrations applied, smoke result. Move to the audit trail when it exists.

## Maintenance windows (DEP-29)

Non-zero-downtime maintenance requires a declared window, 48 hours notice,
scheduling outside usual working hours, and a tested rollback plan.
