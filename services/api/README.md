# legacy-api

The Legacy platform API service (FastAPI). Governing specifications:
`architecture/MASTER_ARCHITECTURE.md`, `api/API_SPECIFICATION.md`,
`deployment/DEPLOYMENT.md`.

Current scope (BUILD_ORDER step 1): service skeleton with configuration and
health endpoints. The `/v1` API surface arrives at step 6 (MVP-007).

## Run locally

```
cd services/api
uv venv && uv pip install -e ".[dev]"
LEGACY_ENV=local .venv/bin/uvicorn legacy_api.main:app --reload
```

## Test

```
.venv/bin/pytest
```
