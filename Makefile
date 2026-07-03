# Legacy implementation workspace. Spec anchors: deployment/DEPLOYMENT.md,
# roadmap/BUILD_ORDER.md. Run `make install` once, then `make test`.

.PHONY: install install-api install-web dev-api dev-web test test-api test-web build up down smoke spec-check lint audit ci

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

# Proves the alert pipeline end to end (OBSERVABILITY 4.5; step 7 acceptance).
test-alert:
	cd services/api && LEGACY_ENV=local .venv/bin/python -m legacy_api.obs.alerts

# Encrypted backup of the local database (BACKUP_AND_RECOVERY 4.2 to 4.4).
backup:
	LEGACY_BACKUP_DATABASE_URL=$${LEGACY_BACKUP_DATABASE_URL:-postgresql://legacy:legacy@localhost:5432/legacy_local} ./scripts/backup/backup.sh

# Runbook 2 drill: backup, restore to scratch, verify (BACKUP_AND_RECOVERY 4.7).
restore-drill:
	./scripts/backup/restore_drill.sh

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
