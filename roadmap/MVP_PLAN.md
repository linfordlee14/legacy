# MVP_PLAN
### The smallest production-ready Legacy MVP, derived from the completed specification repository

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [ROADMAP](ROADMAP.md), [TASKS](TASKS.md), [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) |

---

## 1. Purpose (MVP Vision)

The MVP is the smallest slice of Legacy that a single builder can ship to production in roughly four working weeks and that the owner will genuinely use every day afterward:

> **A trustworthy private system of record: sign in securely, capture documents and notes in under a minute, lose nothing ever, find anything fast, and see the truth status of every claim about your life in one queue.**

This is [ROADMAP](ROADMAP.md) Phase 1 in full, plus two independently buildable milestones cherry-picked from Phase 2 (M7 Search and M8 Verification Queue, which the roadmap dependency diagram shows need only M2 and M3), plus an optional owner-only preview of cited question answering. It designs nothing new: every scope line below is an existing specification section, and every task maps to an existing TASK ID.

## 2. Goals (MVP Goals)

1. Ship the daily-use core (capture, storage, search) so the platform starts earning its place immediately (mitigates RISK-15, abandonment).
2. Establish the non-negotiable invariants from day one: privacy tiers with deny-by-default, provenance with confidence tiers, audit logging, and verified backups (RISK-02, RISK-04).
3. Seed the corpus with MASTER_CONTEXT as tiered `Claim` records so provenance is real data, not a promise (FS-009 seed, TASK-111).
4. Produce the usage evidence Gate G1 needs (stack confirmation) without letting gate ceremony block delivery.
5. Leave the codebase spec-aligned so every later feature is an addition, not a rework (NFR-044, RISK-17).

## 3. Scope (Features Included and Deferred)

### 3.1 Features included

| Feature | MVP slice | Spec anchor |
|---------|-----------|-------------|
| F1 Capture and Ingestion | Documents and notes only: upload, quick add, `IngestionJob` lifecycle, dedup by content hash, original preservation. No OCR, no transcription, no connectors | FS-001, FR-ING group |
| F11 Private Workspace | Shell only: navigation, minimal dashboard, capture inbox, item list and detail, settings. Owner account only | FS-011, [UI_UX](../ui/UI_UX.md) §4.1 Phase 1 areas |
| F4 Search | Lexical, semantic, and hybrid over pgvector plus lexical index, with tier filtering at the retrieval layer and provenance badges in results | FS-004, [RAG_PIPELINE](../ai/RAG_PIPELINE.md) indexing sections |
| F9 Verification and Citation Engine | Queue MVP: `Claim`/`Source` model live, queue seeded with the six MASTER_CONTEXT §12 items, owner resolves claims end to end with audit trail. No Research Agent automation | FS-009, TASK-206 |
| F5 RAG Question Answering | STRETCH, owner-only feature flag: `/v1/ask` with mandatory citations and explicit refusal behavior, Claude only behind the router abstraction | FS-005, TASK-301/302 subsets |
| Platform invariants | AuthN with MFA, authz core (Owner role, tiers, deny-by-default), audit log, structured observability with log redaction, 3-2-1 backup baseline with restore drills, CI with quality gates | [AUTHENTICATION](../security/AUTHENTICATION.md), [AUTHORIZATION](../security/AUTHORIZATION.md), [OBSERVABILITY](../deployment/OBSERVABILITY.md), [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md), [CI_CD](../deployment/CI_CD.md) |

MVP subsets are scope reductions inside the specs, never deviations from them: the full logical schema from [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) is migrated up front (cheap now, expensive later), but only the entities above are populated by MVP features.

### 3.2 Features deferred (with their roadmap home)

| Deferred | Home |
|----------|------|
| F2 Knowledge graph extraction, F3 Timeline | Phase 2 remainder (TASK-203 to TASK-205, TASK-208) |
| F7 Memory, F13 Explorer, full model router with Gemini/Groq, multimedia ingestion (OCR, transcription), GitHub connector | Phase 3 (TASK-301 completion, TASK-305 to TASK-307, TASK-207) |
| F6 Twin, F8 Agent runtime, F14 Mentor, F15 Writing | Phase 4 (TASK-401 to TASK-409) |
| F10 Public portfolio, F12 Journal sealing (P3 mechanics), F16 Vault and succession | Phase 5 (TASK-501 to TASK-508) |
| Trusted users, Grants UI, Steward pre-registration | Post-MVP; schema and policy service support them, no UI ships |
| Everything in [FUTURE_FEATURES](FUTURE_FEATURES.md) | Not committed |

Note: journals as plain P2 notes work in the MVP (a `JournalEntry` is capturable); only P3 sealing mechanics are deferred. There is deliberately no public surface of any kind in the MVP.

## 4. Requirements (Development Order and Stages)

The MVP runs in four stages. Assumption: one experienced builder working full time, pairing with AI coding sessions; estimates are focused engineering days including tests. Total P0 effort is roughly 27 to 29 days, which lands the MVP at the four-week end of the 2-to-4-week window; the descope ladder in §7 defines how to hit three weeks if needed. Stage names deliberately avoid "Phase" to prevent collision with roadmap Phases 0 to 5.

### Stage 1: Bedrock (target week 1)

Project setup, environments and IaC, CI pipeline with quality gates, full schema migration, authentication (OIDC, MFA, sessions, PATs), authorization core (policy service, Owner ceiling, deny-by-default, uniform not_found), API skeleton (error envelope, pagination, idempotency), observability baseline, backup baseline.

- **Complexity:** High (security-critical, everything depends on it).
- **Time:** 6 to 7 days.
- **Files affected (implementation surfaces):** infrastructure definitions; database migrations; backend auth, policy, and API-core modules; CI configuration; logging middleware.
- **Specifications referenced:** [DEPLOYMENT](../deployment/DEPLOYMENT.md) §4.1 to §4.6, [CI_CD](../deployment/CI_CD.md) §4.1 to §4.3, [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) all of §4, [AUTHENTICATION](../security/AUTHENTICATION.md) §4.1 to §4.4 and §4.6, [AUTHORIZATION](../security/AUTHORIZATION.md) §4.1 to §4.5 and §4.7, [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.1 to §4.3, [OBSERVABILITY](../deployment/OBSERVABILITY.md) logging and audit sections, [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.1 to §4.3.

### Stage 2: Capture (target week 2)

Ingestion pipeline for documents and notes with `IngestionJob` lifecycle; workspace shell (navigation, dashboard v0, capture inbox, item list and detail with revision history and soft delete); seed imports (MASTER_CONTEXT claims with tiers, owner's existing document batch); accessibility gate live in CI.

- **Complexity:** Medium.
- **Time:** 6 to 7 days.
- **Files affected:** backend ingestion module and job queue; content entity endpoints; web app shell, capture components, list and detail views; seed import scripts.
- **Specifications referenced:** FS-001 and FS-011 in [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), FR-ING and FR-UI groups in [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md), [UI_UX](../ui/UI_UX.md) §4.1 to §4.5, [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) §4.2 (CaptureQuickAdd, PrivacyTierIndicator, ConfidenceBadge, EmptyState), [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.2 to §4.4 and §4.7, [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.3 and §4.4 and §4.6.

### Stage 3: Findability (target week 3)

Chunking, embedding, and lexical indexing; search API (lexical, semantic, hybrid modes) with tier filtering before ranking; search UI with tier and provenance badges; rebuild-from-source drill; performance verification against NFR targets.

- **Complexity:** Medium-High (the tier-filtering invariant must be airtight).
- **Time:** 5 to 6 days.
- **Files affected:** embedding pipeline and index management; search service; search endpoints; search UI components.
- **Specifications referenced:** FS-004, FR-SRCH group, [RAG_PIPELINE](../ai/RAG_PIPELINE.md) chunking and indexing and query pipeline sections, [API_SPECIFICATION](../api/API_SPECIFICATION.md) search endpoints, [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) NFR-001, NFR-002, NFR-005, NFR-024, NFR-035.

### Stage 4: Truth and hardening (target week 4)

Verification queue MVP seeded with the MASTER_CONTEXT §12 items; production hardening (full restore drill, go-live checklist, security review of the auth and tier paths); MVP acceptance run; spec sync (CHANGELOG, deviations, Gate G1 evidence log). Stretch, only if the week has room: model router skeleton (Claude only) and the owner-only cited `/v1/ask` preview with its tier-discipline mini-eval.

- **Complexity:** Medium (stretch items Medium-High).
- **Time:** 5 to 6 days P0, plus 4 days stretch.
- **Files affected:** verification queue endpoints and UI; drill runbooks and results log; go-live checklist; stretch: router abstraction, ask endpoint, eval harness seed.
- **Specifications referenced:** FS-009, FR-VER group, TASK-206 definition of done, [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.6 and §4.7, [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) release criteria; stretch: FS-005, [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md) router and safety sections, [RAG_PIPELINE](../ai/RAG_PIPELINE.md) generation rules, NFR-037, NFR-038.

## 5. Acceptance Criteria (Success Criteria)

The MVP ships when all of the following pass, in production:

1. **Roadmap Phase 1 exit criteria 1 through 5** ([ROADMAP](ROADMAP.md) §4.5) all pass: OIDC plus PAT sign-in with audit entries; document and note stored as P2 `Artifact` and `Note` with `IngestionJob`; scheduled backups plus one passed restore drill; CI blocking on the test baseline; seed corpus imported and listed.
2. **Search works and leaks nothing:** hybrid search over the real corpus meets NFR-001/NFR-002 latency at the reference corpus size, and the tier-filtering test suite proves no result, snippet, or count reveals content above the caller's ceiling (NFR-035).
3. **Provenance is live data:** every MASTER_CONTEXT claim exists as a `Claim` row with correct tier; the verification queue lists all six §12 items; the owner has resolved or documented at least one 🔴 item end to end with an audit trail (Phase 2 exit criterion 4, pulled forward).
4. **Capture is habit-fast:** capturing a note or document takes under one minute end to end, measured, per the 90-day narrative friction target in [ROADMAP](ROADMAP.md) §9.1.
5. **Nothing silently fails:** logs contain no P2 content (redaction test), every mutation and denial writes an `AuditLogEntry`, and alerts reach the owner.
6. **Spec alignment is auditable:** every merged change cites the spec sections it implements ([QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) spec-first rule); deviations, if any, updated the spec first and appear in [CHANGELOG](../CHANGELOG.md).
7. **Stretch (only if built):** every `/v1/ask` answer carries citations (NFR-037 at 100 percent on the golden mini-set), refuses rather than invents, and passes the tier-discipline mini-eval (NFR-038); the flag stays owner-only.

## 6. Dependencies

- **Accounts and access:** hosting, Supabase project, Anthropic API key (stretch), DNS, secrets manager seeded ([DEPLOYMENT](../deployment/DEPLOYMENT.md) entry criteria).
- **Owner inputs, needed by Stage 1:** monthly cost ceiling (NFR-048 TODO), MFA enrollment, seed document batch selected, choice of production region ([DEPLOYMENT](../deployment/DEPLOYMENT.md) §4.3 TODO).
- **Specs:** the repository is complete; no spec work blocks the MVP. TASK-005 (brand palette) is NOT a blocker: the MVP ships on the neutral placeholder palette per [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) §4.1.
- **Sequencing:** Stage 2 needs Stage 1 (auth, schema, API core); Stage 3 needs Stage 2 (content to index); Stage 4 queue needs Stage 1 schema (`Claim`/`Source`) and benefits from Stage 3 search; stretch ask needs Stage 3.

## 7. Risks

| Risk | Register entry | MVP handling |
|------|----------------|--------------|
| Four weeks is tight for a P0 set of ~27-29 days | RISK-10 | The descope ladder, in order: drop stretch ask first; then defer PATs (MVP-005) and revision history (MVP-015); then defer the verification queue UI to week 5 while keeping seeded `Claim` data. Never descope: auth, tiers, backups, audit, capture, search tier filtering |
| Security shortcuts under time pressure | RISK-02 | Stage 1 is deliberately the longest stage; the go-live checklist re-tests auth and tier paths; deny-by-default is scaffolded before any feature endpoint exists |
| Search quality disappoints on a small corpus | RISK-20 | Golden query set built from the seed corpus in Stage 3; lexical search is the guaranteed floor |
| Owner capacity assumption wrong (part-time reality) | RISK-15, roadmap §1 TODO | Stages are strictly ordered and independently shippable; a part-time builder ships Stage 1+2 as a still-valuable capture vault and continues |
| Stretch ask ships half-hardened | RISK-03 | The flag is owner-only, and criterion 7 gates it; if the mini-eval is not green, the flag stays off at ship time |

## 8. Future Enhancements

Everything after the MVP follows [TASKS](TASKS.md) in roadmap order: Phase 2 remainder (graph, timeline, gate G2), then Phase 3 onward. The MVP adds no new future work; see [BUILD_ORDER](BUILD_ORDER.md) §After-the-MVP.

## 9. Examples

A day-one-after-ship morning: the owner signs in with a passkey, drags in three hackathon PDFs (each searchable within two minutes, NFR-005), quick-adds a note about a mentorship conversation, and searches "YOLOv5 accuracy" to pull the RhinoGuardians claim, which renders with a Self-reported badge. The dashboard shows the verification queue at five open items because he resolved the WorldQuant claim yesterday: evidence attached, tier updated, audit trail written. Nightly backups ran; the monthly restore drill is on the calendar.

## 10. Open Questions

- Which six-to-ten questions form the golden mini-set for the stretch ask eval? Draft from the seed corpus during Stage 3.
- Does the owner want journals (plain P2 notes) surfaced as a distinct workspace area in the MVP shell, or under notes until Phase 5? Default: under notes; one-line decision at Stage 2 start.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §12 (verification queue seed data), §0 (tier vocabulary shipped in the MVP).
- [ROADMAP](ROADMAP.md) §4.3 dependency diagram (the M-numbers cited here), §4.5 and §4.6 (exit criteria pulled into §5).

## 12. Related Specifications

- [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md): the task-level breakdown of this plan.
- [BUILD_ORDER](BUILD_ORDER.md): the strict build sequence for implementation sessions.
- [TASKS](TASKS.md): the canonical backlog these MVP tasks subset.
- [ROADMAP](ROADMAP.md), [RISKS](RISKS.md), [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md).
