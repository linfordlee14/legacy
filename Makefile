# Legacy implementation workspace. Spec anchors: deployment/DEPLOYMENT.md,
# roadmap/BUILD_ORDER.md. Run `make install` once, then `make test`.

.PHONY: install install-api install-web dev-api dev-web test test-api test-web build up down smoke spec-check lint audit ci seed seed-docs reindex perf-baseline full-restore-drill security-retest

install: install-api install-web

install-api:
	cd services/api && uv venv --allow-existing && uv pip install -e ".[dev]"

install-web:
	cd apps/web && npm install

dev-api:
	cd services/api && LEGACY_ENV=local .venv/bin/uvicorn legacy_api.main:app --reload --port 8000

dev-web:
	cd apps/web && NEXT_PUBLIC_LEGACY_ENV=local NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev

test: test-api test-web

test-api:
	cd services/api && LEGACY_ENV=local .venv/bin/python -m pytest

test-web:
	cd apps/web && npm test && npm run typecheck

build:
	docker build -t legacy-api:dev services/api
	cd apps/web && npm run build

up:
	docker compose up --build -d

down:
	docker compose down

smoke:
	./scripts/smoke_test.sh http://localhost:8000 local

db-up:
	docker compose up -d db

migrate:
	cd services/api && LEGACY_DATABASE_URL=$${LEGACY_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} .venv/bin/alembic upgrade head

migrate-down:
	cd services/api && LEGACY_DATABASE_URL=$${LEGACY_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} .venv/bin/alembic downgrade -1

# Rebuild the chunk store from source rows (MVP-016; NFR-024 drill path).
# Requires LEGACY_GEMINI_API_KEY (ADR-16). Safe to re-run: unchanged
# entities are no-ops (RAG-03).
reindex:
	cd services/api && LEGACY_ENV=$${LEGACY_ENV:-local} LEGACY_DATABASE_URL=$${LEGACY_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} .venv/bin/python -m legacy_api.rag.reindex

# Seed MASTER_CONTEXT.md as tiered Claims (BUILD_ORDER step 13; MVP-013).
# Idempotent: re-running creates no duplicate claims, sources, or links.
seed:
	cd services/api && LEGACY_ENV=$${LEGACY_ENV:-local} LEGACY_DATABASE_URL=$${LEGACY_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} .venv/bin/python -m legacy_api.seed

# Batch-import owner documents through the ingestion pipeline (step 14; MVP-014).
# Usage: make seed-docs DOCS="path/to/folder" [TIER=P2] [EXT=".md,.txt,.pdf"]
# Idempotent: re-running dedups by checksum; originals preserved unmodified.
# DOCS paths are relative to the repository root; the storage directory must
# be the one the API service uses (dev-api runs with services/api/storage).
seed-docs:
	@test -n "$(DOCS)" || { echo "DOCS is required: make seed-docs DOCS=path/to/folder"; exit 2; }
	LEGACY_ENV=$${LEGACY_ENV:-local} LEGACY_DATABASE_URL=$${LEGACY_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} LEGACY_STORAGE_DIR=$${LEGACY_STORAGE_DIR:-services/api/storage} services/api/.venv/bin/python -m legacy_api.seed.documents $(DOCS) $(if $(TIER),--tier $(TIER)) $(if $(EXT),--ext $(EXT))

# Proves the alert pipeline end to end (OBSERVABILITY 4.5; step 7 acceptance).
test-alert:
	cd services/api && LEGACY_ENV=local .venv/bin/python -m legacy_api.obs.alerts

# Encrypted backup of the local database (BACKUP_AND_RECOVERY 4.2 to 4.4).
backup:
	LEGACY_BACKUP_DATABASE_URL=$${LEGACY_BACKUP_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} ./scripts/backup/backup.sh

# Runbook 2 drill: backup, restore to scratch, verify (BACKUP_AND_RECOVERY 4.7).
restore-drill:
	./scripts/backup/restore_drill.sh

# Runbook 3 drill: full platform restore onto fresh scratch infrastructure,
# database plus object storage, with runbook 5 verification (MVP-021).
full-restore-drill:
	./scripts/backup/full_restore_drill.sh

# Security re-test of the auth and tier paths (MVP-021; SEC-37): the
# authorization regression suites, leak suites included, in one gate.
security-retest:
	cd services/api && LEGACY_ENV=local .venv/bin/python -m pytest -q \
		tests/test_auth.py tests/test_auth_unit.py tests/test_authorization.py \
		tests/test_policy_unit.py tests/test_pats.py tests/test_content.py \
		tests/test_content_edit.py tests/test_search_api.py tests/test_verification.py

# Record the MVP-019 performance baseline (NFR 4.1) against a DISPOSABLE
# database; results belong in infra/PERFORMANCE_BASELINE.md.
perf-baseline:
	LEGACY_ENV=$${LEGACY_ENV:-local} LEGACY_PERF_DATABASE_URL=$${LEGACY_PERF_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_perf} services/api/.venv/bin/python scripts/perf/measure_baseline.py

spec-check:
	python3 scripts/check_specs.py

lint:
	cd services/api && .venv/bin/ruff check . && .venv/bin/mypy
	cd apps/web && npm run lint && npm run typecheck

audit:
	cd services/api && .venv/bin/bandit -r src --severity-level high -q && .venv/bin/pip-audit --skip-editable
	cd apps/web && npm audit --audit-level=high

# The full local equivalent of the CI gates (deployment/CI_CD.md 4.2 and 4.3).
ci: spec-check lint test audit
	cd apps/web && NEXT_PUBLIC_LEGACY_ENV=local npm run build
