# Legacy implementation workspace. Spec anchors: deployment/DEPLOYMENT.md,
# roadmap/BUILD_ORDER.md. Run `make install` once, then `make test`.

.PHONY: install install-api install-web dev-api dev-web test test-api test-web build up down smoke

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
