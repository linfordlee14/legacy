# OBSERVABILITY
### Logging, metrics, tracing, auditing, alerting, and SLOs for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [DEPLOYMENT](./DEPLOYMENT.md), [PRIVACY](../security/PRIVACY.md), [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) |

---

## 1. Purpose

This specification defines how Legacy is observed in operation: what is logged, measured, traced, audited, and alerted on, and which service level objectives the platform holds itself to. Legacy has one user who is also the operator, so observability must detect issues before the owner notices them, explain AI behavior after the fact, and keep model spend under control, all without ever leaking private content into telemetry.

## 2. Goals

1. Detect degradation and failure before the owner encounters it in normal use.
2. Make every AI answer explainable in retrospect: which context was retrieved, which model ran, which citations were produced, at what cost.
3. Keep telemetry privacy-clean: P2 and P3 content never appears in logs, metrics, or traces.
4. Control cost with per-day, per-model spend visibility and alerts.
5. Provide an immutable audit trail for security-relevant and succession-relevant events.
6. Define SLOs that are honest for a single-owner platform and use their error budgets to pace risk-taking.

## 3. Scope

### In scope
- Structured logging policy, levels, redaction.
- Metrics: system, product, and AI-specific.
- Distributed tracing including AgentRun traces.
- Audit log requirements (referencing the AuditLogEntry entity).
- Alerting: severities, channels, quiet hours, digest.
- Dashboards.
- Telemetry retention.
- SLO definitions and error budgets (design proposals).

### Out of scope
- The deployment of the telemetry stack itself (see [DEPLOYMENT](./DEPLOYMENT.md); tool selection is an ADR).
- Backup verification metrics beyond alert hooks (see [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md)).
- The attribute-level schema of AuditLogEntry (see [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)).
- Security incident response process (see [SECURITY](../security/SECURITY.md)).

## 4. Requirements

Document-local requirement IDs (OBS-##) are used below. They roll up to the FR-OPS group in the `specs/` documents.

### 4.1 Logging

| ID | Requirement |
|----|-------------|
| OBS-01 | All services emit structured logs (JSON lines) with at minimum: timestamp, level, service, environment, request or job identifier, trace identifier, event name, and typed fields. Free-text messages carry no interpolated content values. |
| OBS-02 | Levels are `debug`, `info`, `warn`, `error`. Production runs at `info`; `debug` may be enabled per component for a bounded time window and auto-reverts. |
| OBS-03 | Privacy rule, absolute: P2 and P3 content never appears in logs. Content is referenced by entity ID and privacy tier only (for example `artifact_id`, `chunk_id`, `journal_entry_id`). This includes query text, prompt text, retrieved chunk text, model output text, and file names that may embed personal content. |
| OBS-04 | P0 and P1 content is also excluded from logs by default; the ID-only rule is uniform so that a tier change never retroactively makes old logs non-compliant. |
| OBS-05 | A redaction middleware sits in the logging path of every service: it enforces field allowlists, strips known content-bearing fields, and pattern-scrubs residual values (emails, tokens, long free text). Redaction failures fail closed: the event is dropped and a `warn` about the drop is emitted. |
| OBS-06 | Log emission is asynchronous and non-blocking; telemetry outages degrade to local buffering, never to request failures. |

### 4.2 Metrics

System metrics (per service, per environment):

| Metric | Notes |
|--------|-------|
| Request latency (p50, p95, p99) | Per route group of the `/v1` API |
| Error rate | 5xx and 4xx-excluding-auth-noise, per route group |
| Saturation | CPU, memory, queue depth, DB connections, storage growth |
| Availability probe | External synthetic check of health and one read path |

Product metrics:

| Metric | Notes |
|--------|-------|
| Ingestion throughput | Items and bytes per hour; IngestionJob success and retry rates |
| Ingestion backlog age | Oldest unprocessed item, drives worker scaling |
| Search latency | End-to-end semantic and hybrid search, p95 |
| RAG answer latency | Request to final token; first-token latency tracked separately |
| Export outcomes | Legacy Vault export success, duration, size, manifest verification result |

AI-specific metrics:

| Metric | Notes |
|--------|-------|
| Token spend per model per day | Input and output tokens, priced; the primary cost control signal |
| Model router decisions | Count per provider and model, with routing reason code |
| Cache hit rate | Prompt and retrieval cache layers |
| Groundedness sampling score | Scheduled sampling of production answers re-scored by the eval suite |
| Citation coverage | Share of factual answer sentences carrying at least one citation |
| Agent run success rate | AgentRun terminal states per agent type; budget-exceeded terminations counted separately |
| Human-approval queue depth | Pending approvals awaiting the owner, with oldest-item age |
| Claim tier fidelity incidents | Any detected assertion of a 🟡 or 🔴 claim as fact, target zero |

| ID | Requirement |
|----|-------------|
| OBS-07 | All metrics above exist with per-environment labels; cardinality is bounded (no per-entity labels). |
| OBS-08 | Token spend per model per day feeds the cost ceiling alerts defined with the cost posture in [DEPLOYMENT](./DEPLOYMENT.md). |
| OBS-09 | Groundedness sampling and citation coverage run on a schedule against sampled production traffic, using the same scoring definitions as the CI evaluation gate in [CI_CD](./CI_CD.md), so pre-release and in-production quality are comparable. Samples are scored in place; sampled content is not copied into telemetry storage. |

### 4.3 Tracing

| ID | Requirement |
|----|-------------|
| OBS-10 | Every API request and every background job carries a trace: API handling, retrieval steps (query embedding, vector search, rerank), model calls (provider, model, token counts, latency, cost), and post-processing appear as spans. |
| OBS-11 | AgentRun traces are first-class: an AgentRun (see [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)) maps to a root span with child spans per agent step, tool call, and model call, linked by the AgentRun ID so the UI can show "what did this agent do and why". |
| OBS-12 | Span attributes obey the same redaction rules as logs (OBS-03 to OBS-05): IDs, counts, durations, model names, reason codes; never content. |
| OBS-13 | Trace context propagates across the queue: a background job spawned by a request links to the originating trace. |
| OBS-14 | Sampling: 100 percent of traces are retained at single-owner traffic volumes; if volume ever forces sampling, errors, agent runs, and slow requests are always retained. |

```
Trace: POST /v1/ask  (trace_id: tr_91f2)
 |- span: api.request                       42 ms
 |- span: retrieval.embed_query             35 ms
 |- span: retrieval.vector_search           58 ms   chunks=12
 |- span: retrieval.rerank                  61 ms   kept=6
 |- span: model.call  provider=claude      2100 ms  in_tok=3800 out_tok=420
 |- span: verify.citations                  38 ms   coverage=1.0
 '- span: api.stream_response              2900 ms  first_token=680 ms
```

### 4.4 Audit log

| ID | Requirement |
|----|-------------|
| OBS-15 | Security-relevant and legacy-relevant events are written as AuditLogEntry records per [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): authentication events (success and failure), authorization denials, privacy tier changes, Grant issuance and revocation, exports (vault and ad hoc), key operations, succession-related events, and administrative configuration changes. |
| OBS-16 | The audit log is append-only and immutable: no update or delete path exists in the application; retention is indefinite; integrity is protected (hash chaining or equivalent tamper evidence, mechanism decided in [SECURITY](../security/SECURITY.md)). |
| OBS-17 | Audit entries record actor, action, target entity ID, environment, timestamp, and outcome; they follow the ID-only content rule. |
| OBS-18 | The audit log is included in backups and in succession documentation: a future steward must be able to reconstruct who accessed and exported what. |

### 4.5 Alerting

Severity ladder:

| Severity | Meaning | Notification | Examples |
|----------|---------|--------------|----------|
| SEV-1 | Platform down or data at risk | Page immediately, ignore quiet hours | Availability probe failing, backup or vault export failed, suspected tamper of audit log |
| SEV-2 | Degraded but usable, or budget threat | Notify immediately during waking hours, else first morning slot | Error rate breach, ingestion backlog stalling, 80 percent cost ceiling, groundedness sample below threshold |
| SEV-3 | Needs attention this week | Daily summary | Retry rates elevated, cache hit rate drop, approval queue aging |
| SEV-4 | Informational | Weekly digest only | Deploys, cost trend, storage growth |

| ID | Requirement |
|----|-------------|
| OBS-19 | Owner notification channels are, in order: push notification, then email, with SEV-1 additionally using a phone-level channel. Exact channel bindings are configuration, not spec. |
| OBS-20 | Quiet hours are owner-configured; SEV-1 overrides them, SEV-2 and below queue until quiet hours end. |
| OBS-21 | A weekly digest summarizes: SLO and error budget status, cost versus ceiling, AI quality samples, backup and vault outcomes, audit log highlights, and open SEV-3 items. |
| OBS-22 | Every alert links to a runbook entry; an alert without a documented response action is a defect. |
| OBS-23 | Alert fatigue control: any alert that fires more than three times in a week without action is reviewed and either fixed, re-thresholded, or downgraded. |

### 4.6 Dashboards

| Dashboard | Content |
|-----------|---------|
| Operations | Availability probe, latency and error rates per route group, saturation, queue depth, ingestion backlog, deploy markers |
| AI quality | Groundedness samples, citation coverage, tier fidelity incidents, agent run success, router decisions, approval queue |
| Cost | Token spend per model per day, infrastructure spend per service, spend versus ceiling, cache hit rate as a savings lever |

| ID | Requirement |
|----|-------------|
| OBS-24 | The three dashboards above exist for production; staging has the operations dashboard at minimum. Deploy events are annotated on all of them. |

### 4.7 Telemetry retention

| Data | Retention | Rationale |
|------|-----------|-----------|
| Logs (info and above) | 90 days hot, 12 months archived | Debugging and incident review; aligned with [PRIVACY](../security/PRIVACY.md) since logs carry IDs only |
| Debug logs | 7 days | Bounded troubleshooting windows |
| Metrics | 13 months full resolution or downsampled after 90 days | Year-over-year cost and capacity trends |
| Traces | 30 days | Behavior explanation window |
| AgentRun records | Indefinite (application data, not telemetry) | Part of the corpus's provenance story |
| Audit log | Indefinite, immutable | OBS-16 |

| ID | Requirement |
|----|-------------|
| OBS-25 | Telemetry stores enforce these retention limits automatically; retention changes are reviewed against [PRIVACY](../security/PRIVACY.md) before adoption. |

### 4.8 SLOs and error budgets (design proposals)

These are proposals for a single-owner platform, to be confirmed after one quarter of baseline data.

| SLO | Target | Window | Error budget |
|-----|--------|--------|--------------|
| Availability (API read path probe) | 99.5 percent | 30 days | ~3.6 hours per month |
| Search latency | p95 under 1.5 s | 30 days | 5 percent of requests may exceed |
| RAG streaming first token | p95 under 3 s | 30 days | 5 percent of requests may exceed |
| Vault export success | Every scheduled export succeeds or is retried to success within 24 h | Per schedule | Zero missed generations |

| ID | Requirement |
|----|-------------|
| OBS-26 | Error budget policy: when a 30-day budget is exhausted, feature deploys pause in favor of reliability work until the budget recovers; SEV-4 notes track budget burn weekly. |
| OBS-27 | SLO targets are revisited after the first quarter of production data and whenever topology changes materially. |

## 5. Acceptance Criteria

1. A seeded log event containing P2 content markers is stripped or dropped by the redaction middleware, and the drop is itself observable.
2. Grepping a week of production logs for known corpus phrases returns zero hits (verified during a drill with owner-selected phrases).
3. Every metric in section 4.2 is queryable with environment labels, and the three dashboards render them.
4. An AgentRun in the UI links to a complete trace: steps, tool calls, model calls, token counts, and cost, with no content in span attributes.
5. Authentication failure, an authorization denial, a tier change, and a vault export each produce an AuditLogEntry; attempts to update or delete an entry fail. |
6. A simulated availability failure pages within 5 minutes; a simulated vault export failure raises SEV-1; the 80 percent cost threshold raises SEV-2.
7. Quiet hours suppress a SEV-3 alert and do not suppress a SEV-1 alert in a scheduled test.
8. The weekly digest is delivered and contains all sections listed in OBS-21.
9. Telemetry stores demonstrate automatic expiry consistent with the retention table.

## 6. Dependencies

- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): AuditLogEntry, AgentRun, IngestionJob definitions.
- [PRIVACY](../security/PRIVACY.md): tier definitions and telemetry retention constraints.
- [SECURITY](../security/SECURITY.md): audit integrity mechanism, incident response the alerts feed into.
- [DEPLOYMENT](./DEPLOYMENT.md): environments, cost ceiling, smoke tests that emit deploy markers.
- [CI_CD](./CI_CD.md): shared scoring definitions between the eval gate and production sampling.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): agent step semantics traced in OBS-11.
- External: telemetry stack selection (an ADR) and notification channel providers.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Content leaks into telemetry despite policy | Privacy breach of P2/P3 material | Allowlist-based redaction failing closed (OBS-05), uniform ID-only rule (OBS-04), grep drills (Acceptance 2) |
| Owner-as-operator misses alerts | Prolonged degradation | Severity ladder with paging (OBS-19), weekly digest as backstop, alert fatigue control (OBS-23) |
| Telemetry cost grows to rival product cost | Budget pressure | Bounded cardinality (OBS-07), retention limits, single-owner sampling posture |
| Groundedness sampling drifts from the CI gate definition | Two incompatible quality numbers | Shared suite and definitions (OBS-09) |
| Audit log grows unbounded | Storage cost on an indefinite store | ID-only compact entries, archival tiering, but never deletion |
| Telemetry stack outage blinds operations | Silent failures | External availability probe independent of the stack, non-blocking emission (OBS-06) |

## 8. Future Enhancements

- Anomaly detection on spend and ingestion patterns rather than static thresholds.
- Owner-facing "explain this answer" view assembled directly from the trace and citation data.
- Synthetic AI-quality probes: scheduled canned questions with known-good grounded answers.
- Budget-aware model router feedback loop using router decision metrics.
- Steward-facing read-only status page for succession scenarios.

## 9. Examples

Structured log line (illustrative, note the absence of content):

```json
{
  "ts": "2026-07-02T14:12:09.331Z",
  "level": "info",
  "service": "api",
  "env": "production",
  "event": "rag.answer.completed",
  "trace_id": "tr_91f2",
  "request_id": "req_5c77",
  "entity_refs": {"conversation_id": "conv_8812", "chunk_ids_count": 6},
  "model": {"provider": "claude", "name": "primary-router-choice"},
  "tokens": {"input": 3800, "output": 420},
  "latency_ms": 3234,
  "citation_coverage": 1.0,
  "privacy_tier_max": "P2"
}
```

Alert payload (illustrative):

```json
{
  "severity": "SEV-1",
  "alert": "vault_export_failed",
  "environment": "production",
  "detail": "Scheduled Legacy Vault export did not complete; manifest not written",
  "runbook": "deployment/BACKUP_AND_RECOVERY.md#restore-and-export-runbooks",
  "fired_at": "2026-07-02T02:15:00Z",
  "quiet_hours_override": true
}
```

## 10. Open Questions

1. > TODO(verify): telemetry stack selection (managed observability vendor versus platform-native tooling), to be recorded as an ADR with an exit note per DEPLOYMENT's vendor rules.
2. > TODO(verify): owner's notification channels and quiet hours preferences (configuration values, needed before production).
3. Should groundedness sampling scores be shown to the owner in-product per answer, or only aggregated? Interacts with trust framing in the UI specs.
4. Is 99.5 percent availability the right target for a single-owner platform, or is it stricter than needed at this budget? Revisit with OBS-27.

## 11. References

- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): privacy tiers P0 to P3 and canonical entities used throughout.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), section 0: the confidence tier system behind tier fidelity metrics.
- Google SRE workbook concepts (SLOs, error budgets) as the general model adapted here to a single-owner platform.

## 12. Related Specifications

- [DEPLOYMENT](./DEPLOYMENT.md)
- [CI_CD](./CI_CD.md)
- [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md)
- [PRIVACY](../security/PRIVACY.md), [SECURITY](../security/SECURITY.md)
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md)
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md)
