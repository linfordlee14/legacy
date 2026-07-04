# Performance baseline (MVP-019)

Measured results only; nothing here is estimated. Re-measure on provisioned
infrastructure at Gate G1/G2 and update this file alongside
[VERIFICATION_LOG](VERIFICATION_LOG.md).

## Run record

| Field | Value |
|-------|-------|
| Date | 2026-07-04 |
| Harness | `scripts/perf/measure_baseline.py` (`make perf-baseline`) |
| Environment | Sandbox Linux container; PostgreSQL 16.13 + pgvector 0.6.0 over a local socket; Python 3.11; uvicorn, single worker; real HTTP |
| Corpus | 72 seeded Claims (MVP-013), 15 reference specification documents (knowledge, ai, api, database, security, deployment), 100 synthetic mixed documents (60 md, 30 txt, 10 pdf), freshness probes |
| Embeddings | Deterministic in-process stand-in at the pinned 1536 dimension: full store, fusion, and HTTP path; NO real provider round-trips (`LEGACY_GEMINI_API_KEY` not provisioned) |
| Hardware profile | Not the production reference profile (undefined until provisioning); NFR acceptance requires re-measuring there |

## NFR verdicts

| NFR | Budget | Measured | Verdict |
|-----|--------|----------|---------|
| NFR-001 lexical search p95 (Should) | 300 ms | 103.1 ms (p50 87.8, n=60, golden queries) | Green in this environment |
| NFR-002 hybrid search p95 (Must) | 1.5 s | 107.2 ms store path (p50 91.7, n=60) | Green on the store path; with-provider run outstanding (see below) |
| NFR-005 capture to searchable (Must) | 2 min | 0.63 s upload to lexical-searchable, full pipeline with in-process embedder | Green on the store path; with-provider run outstanding. With no embedding provider, chunks queue for `make reindex` by design (RAG-08) and the deferred counter exposes the gap |
| NFR-006 100-doc batch (Should) | 8 h | 1.01 s ingest plus index, 100 of 100 stored | Green on the store path |
| NFR-003, NFR-004 (ask streaming/completion) | 3 s / 30 s | Not measured | Not applicable: `/v1/ask` is not built (stretch MVP-025) |
| NFR-007, NFR-008 (graph/timeline) | 500 / 800 ms | Not measured | Not applicable: Phase 2 features |
| NFR-009, NFR-010 (page interactivity) | 3 s / 2 s | Not measured | Outstanding: needs a deployed environment and the defined hardware/network profile |
| NFR-051/NFR-052 (RPO/RTO) | 24 h / 72 h | Restore drill PASS in 3.5 s wall on the reference corpus (35 tables verified, schema 0004, 436 KB encrypted backup); cadence enforced by the per-push and monthly CI drills | Green at this corpus size; re-measure at production scale |
| NFR-053 steward drill | Documentation-only restore | Not run | Outstanding: requires a human steward |

## Supporting measurements

| Measure | Result |
|---------|--------|
| `GET /healthz` | p50 2.0 ms, p95 2.3 ms (n=50) |
| `GET /v1/claims` (owner) | p50 4.4 ms, p95 5.4 ms (n=30) |
| `GET /v1/notes` (owner) | p50 3.1 ms, p95 3.4 ms (n=30) |
| Semantic search (store path) | p50 7.9 ms, p95 8.4 ms (n=60) |
| Seed claims import (72 claims) | 0.06 s |
| Reference corpus ingest plus index (15 docs) | 1.04 s |
| Alert pipeline (`make test-alert`) | Delivered: SEV-2 emission reached the owner notification channel |
| `/metrics` exposure | Request counters and the embedding-deferred (searchable-lag) counter present |

## Outstanding measurements (never silently closed)

Tracked in [VERIFICATION_LOG](VERIFICATION_LOG.md): with-provider NFR-002
and NFR-005 (needs `LEGACY_GEMINI_API_KEY`, then `make reindex` and
`make perf-baseline` against real embeddings), NFR-009/NFR-010 page
audits on a deployed environment, the NFR-053 steward drill, the
production-hardware re-run of every number above, and the TST-40/TST-41
nightly trending environment.
