# Legacy
### Your Life. Your Knowledge. Your Impact. Preserved Forever.

**Legacy** is a lifelong, AI-powered knowledge platform that preserves, organizes, understands, and extends the work, ideas, projects, research, code, values, and impact of **Linford Musiyambodza**. It is not a biography. It is a living AI operating system, designed to grow throughout his lifetime and remain valuable for future generations.

This repository is the **Specification-Driven Development (SDD) foundation** of the platform. It contains no application code. Every document here is a production-grade specification, written so that future engineering sessions (human or AI) can implement the complete platform feature by feature without redesigning the architecture.

---

## Canonical source of truth

All facts about Linford Musiyambodza come from one file:

> **[`knowledge/MASTER_CONTEXT.md`](knowledge/MASTER_CONTEXT.md)**, immutable.

It carries a confidence tier on every claim (✅ Verified, 🟡 Self-reported, 🔴 Flagged). No specification, feature, or AI behavior may upgrade a 🟡 or 🔴 claim to established fact. This provenance discipline is productized throughout the platform (see the Claim and Source entities, the Verification Engine, and the Citation Engine).

## How to read this repository

Read in this order:

1. **Foundation:** [`docs/VISION.md`](docs/VISION.md) · [`docs/MISSION.md`](docs/MISSION.md) · [`docs/LEGACY_PRINCIPLES.md`](docs/LEGACY_PRINCIPLES.md)
2. **Conventions (normative for all authors):** [`docs/SPEC_CONVENTIONS.md`](docs/SPEC_CONVENTIONS.md)
3. **Requirements:** [`specs/PRODUCT_REQUIREMENTS.md`](specs/PRODUCT_REQUIREMENTS.md) · [`specs/SYSTEM_REQUIREMENTS.md`](specs/SYSTEM_REQUIREMENTS.md) · [`specs/FUNCTIONAL_REQUIREMENTS.md`](specs/FUNCTIONAL_REQUIREMENTS.md) · [`specs/NON_FUNCTIONAL_REQUIREMENTS.md`](specs/NON_FUNCTIONAL_REQUIREMENTS.md)
4. **Users and features:** [`specs/USER_PERSONAS.md`](specs/USER_PERSONAS.md) · [`specs/USER_STORIES.md`](specs/USER_STORIES.md) · [`specs/USE_CASES.md`](specs/USE_CASES.md) · [`specs/FEATURE_SPECIFICATIONS.md`](specs/FEATURE_SPECIFICATIONS.md)
5. **Architecture:** [`architecture/MASTER_ARCHITECTURE.md`](architecture/MASTER_ARCHITECTURE.md) · [`database/DATABASE_SCHEMA.md`](database/DATABASE_SCHEMA.md) · [`api/API_SPECIFICATION.md`](api/API_SPECIFICATION.md)
6. **AI systems:** [`ai/AI_ARCHITECTURE.md`](ai/AI_ARCHITECTURE.md) · [`ai/RAG_PIPELINE.md`](ai/RAG_PIPELINE.md) · [`ai/DIGITAL_TWIN.md`](ai/DIGITAL_TWIN.md) · [`agents/MULTI_AGENT_ARCHITECTURE.md`](agents/MULTI_AGENT_ARCHITECTURE.md) · [`knowledge/KNOWLEDGE_GRAPH.md`](knowledge/KNOWLEDGE_GRAPH.md) · [`memory/MEMORY_SYSTEM.md`](memory/MEMORY_SYSTEM.md)
7. **Security and privacy:** [`security/SECURITY.md`](security/SECURITY.md) · [`security/PRIVACY.md`](security/PRIVACY.md) · [`security/AUTHENTICATION.md`](security/AUTHENTICATION.md) · [`security/AUTHORIZATION.md`](security/AUTHORIZATION.md)
8. **Operations:** [`deployment/DEPLOYMENT.md`](deployment/DEPLOYMENT.md) · [`deployment/CI_CD.md`](deployment/CI_CD.md) · [`deployment/OBSERVABILITY.md`](deployment/OBSERVABILITY.md) · [`deployment/BACKUP_AND_RECOVERY.md`](deployment/BACKUP_AND_RECOVERY.md)
9. **Quality and experience:** [`testing/TESTING.md`](testing/TESTING.md) · [`testing/QUALITY_ASSURANCE.md`](testing/QUALITY_ASSURANCE.md) · [`ui/UI_UX.md`](ui/UI_UX.md) · [`ui/DESIGN_SYSTEM.md`](ui/DESIGN_SYSTEM.md) · [`ui/ACCESSIBILITY.md`](ui/ACCESSIBILITY.md)
10. **Delivery:** [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md) · [`roadmap/TASKS.md`](roadmap/TASKS.md) · [`roadmap/RISKS.md`](roadmap/RISKS.md) · [`roadmap/FUTURE_FEATURES.md`](roadmap/FUTURE_FEATURES.md)

Repository meta: [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`CHANGELOG.md`](CHANGELOG.md)

## What Legacy becomes

Personal Knowledge System · Digital Memory · AI Second Brain · AI Digital Twin · Project Archive · Research Repository · Company Knowledge Base · AI Mentor · Timeline Engine · Search Engine · Knowledge Graph · Legacy Preservation Platform · Public Portfolio · Private Workspace · Multi-Agent AI System · Long-Term Memory System

## Core design commitments

- **Specification driven.** Implementation follows these documents; deviations update the spec first.
- **Provenance first.** Every fact carries a confidence tier and citations, end to end, from database row to UI badge.
- **Privacy first.** Four privacy tiers (P0 Public, P1 Trusted, P2 Private, P3 Sealed), enforced at every layer, deny by default.
- **Built to outlive vendors.** Open formats, versioned exports (the Legacy Vault), documented succession, decades-scale durability.
- **AI native, human governed.** A twelve-agent AI system does the work; irreversible and outward-facing actions require human approval.

## Baseline stack (proposed defaults)

Next.js web client · FastAPI backend · Supabase PostgreSQL with pgvector · Anthropic Claude API primary with Gemini and Groq behind a model router · MCP tool integrations · REST `/v1` with SSE streaming. Recorded as ADRs in [`architecture/MASTER_ARCHITECTURE.md`](architecture/MASTER_ARCHITECTURE.md); each anchored to the owner's demonstrated stack in MASTER_CONTEXT §5.

## Status

Specification phase (Phase 0). See [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md) for the implementation plan and [`CHANGELOG.md`](CHANGELOG.md) for repository history.

---

*El Roi.*
