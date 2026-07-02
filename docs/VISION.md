# VISION
### Product vision for Legacy, a lifelong AI digital legacy platform for Linford Musiyambodza

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md), [MISSION](./MISSION.md), [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md) |

---

## 1. Purpose

This document states what Legacy is, what it must grow into, and how far into the future it must remain useful. Every other specification in this repository elaborates some part of this vision; when a design question has no obvious answer, contributors resolve it against this document, [MISSION](./MISSION.md), and [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md), in that order of abstraction.

**Legacy is a living AI operating system for one person's life work. It is not a biography.** A biography is a finished artifact written once, from the outside, about a closed period. Legacy is the opposite on every axis: it is continuously written from the inside, it operates on live work rather than summarizing finished work, and it is an active system (it retrieves, reasons, drafts, mentors, and answers) rather than a passive record. The person is Linford Musiyambodza: founder of Linfy Tech Solutions, CTO of NeuroGrowth Labs, and a faith-driven African software builder based in Strand, Cape Town (all ✅ per [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §1 and §4). Legacy exists so that his projects, research, code, writing, values, relationships, and lessons compound over a lifetime instead of dissipating across scattered platforms, and so that they remain intelligible and useful after him.

The single-owner focus is a deliberate design decision, not a limitation to be apologized for. Building for exactly one deeply understood owner allows a depth of personalization (provenance discipline, voice replication, privacy semantics, succession rules) that generic tools cannot reach.

## 2. Goals

These are the north-star outcomes. They are stated as observable end states; the requirement documents in `specs/` decompose them into testable requirements.

1. **Nothing important is lost.** Any project, idea, note, conversation, artifact, or event that Linford considers worth keeping is captured once and preserved durably, with media, context, and dates intact.
2. **Everything is findable in seconds.** Any preserved item is reachable through natural-language search, semantic search, graph traversal, or timeline navigation, without the owner remembering where it was stored.
3. **Every answer is traceable.** Anything the system asserts about Linford's life or work cites its sources and carries the confidence tier of the underlying `Claim` (✅ Verified, 🟡 Self-reported, 🔴 Flagged), productizing MASTER_CONTEXT §0.
4. **The twin is honest.** The AI Digital Twin answers in Linford's voice and from his knowledge, and it refuses to overstate: it attributes self-reported claims, surfaces flagged claims as unverified, and says "not in my knowledge" rather than inventing.
5. **The system outlives its tools.** Legacy survives model deprecations, vendor changes, and format churn through exportable open formats, versioned specifications, and a vendor-neutral core (the Future Proof and Offline Capable principles).
6. **The system outlives its owner.** Privacy tiers P0 through P3, succession rules, and the sealed tier (P3) let Legacy continue serving family, mentees, and the public on terms Linford defined while alive.
7. **It serves others on Linford's terms.** The public sees a portfolio (P0), trusted people see what they were granted (P1), and everything else stays private (P2) or sealed (P3) by default.
8. **It gives time back.** Legacy reduces the cost of remembering, retrieving, summarizing, and drafting, so the owner spends his hours building, not archiving.

## 3. Scope

### 3.1 In scope for this vision

- The sixteen identities Legacy grows into (§4) and their mapping to repository specifications.
- The time horizon the platform is designed for.
- North-star outcomes and explicit non-goals.

### 3.2 Time horizon: lifetime plus generations

Legacy is designed for a service life measured in decades, with a preservation life measured in generations. This is a design decision with concrete consequences recorded across the architecture and security specs.

| Horizon | Period | What Legacy must be |
|---------|--------|---------------------|
| H1: Foundation | 2026 to roughly 2028 | A working system of record: ingestion, storage, search, graph, timeline, first agents, public portfolio |
| H2: Working decades | Linford's active career | A daily instrument: second brain, twin, mentor, company knowledge base, research engine, writing partner |
| H3: Generations | Beyond the owner's lifetime | A stewarded estate: succession-governed access, sealed-tier releases, durable exports, an honest record for family and successors |

Horizon 3 is why the repository insists on open export formats, the "Legacy Vault" export defined as a baseline decision in [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md) §9, provenance that does not decay, and specifications (this repository) that a future maintainer or AI can implement from scratch if every current dependency has disappeared.

### 3.3 Non-goals

Legacy is **not**:

- **A biography or memoir generator.** It can draft narrative outputs, but its essence is an operating system over living knowledge, not a book.
- **A general-purpose product for the public.** It is single-owner by design; multi-tenant productization is at most a future enhancement (§8).
- **A social network.** There are no feeds, followers, or engagement mechanics. The public surface is a portfolio, not a channel.
- **An autonomous actor.** Agents draft, retrieve, and propose; they do not publish, message, spend, or commit on Linford's behalf without explicit owner action (see the AGT and SEC requirement groups in `specs/FUNCTIONAL_REQUIREMENTS.md`).
- **A simulation of the person.** The Digital Twin is a representation of Linford's documented knowledge, voice, and values. It is never presented as being Linford, and after his lifetime it is governed by the succession rules, not by a claim of continuity. This boundary is part of the Faith-Respectful Stewardship principle in [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md).
- **A source of new facts about Linford.** [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) plus verified `Source` records are the only fact base; the system never upgrades confidence tiers on its own.

## 4. Requirements

At vision level, the requirement is that Legacy grow into sixteen distinct identities on one shared substrate (one datastore, one graph, one memory system, one agent runtime), rather than sixteen disconnected tools. Each identity below names what Legacy must become and anchors it to the specifications that define it. Detailed, numbered requirements live in `specs/PRODUCT_REQUIREMENTS.md` and `specs/FUNCTIONAL_REQUIREMENTS.md`.

| # | Identity | What Legacy must become | Anchor specifications |
|---|----------|------------------------|-----------------------|
| 1 | Personal Knowledge System | The single structured home for notes, ideas, documents, and references, replacing scattered platforms | FR-ING and FR-SRCH groups in `specs/FUNCTIONAL_REQUIREMENTS.md`; `database/DATABASE_SCHEMA.md` |
| 2 | Digital Memory | A durable, dated, media-inclusive record of what happened, immune to platform shutdowns | `memory/MEMORY_SYSTEM.md`; `deployment/BACKUP_AND_RECOVERY.md` |
| 3 | AI Second Brain | An always-available thinking partner that retrieves, connects, and summarizes the owner's own knowledge | `ai/AI_ARCHITECTURE.md`; `ai/RAG_PIPELINE.md` |
| 4 | AI Digital Twin | A persona that answers in Linford's voice, from his knowledge, with his documented values, honestly tiered | `ai/DIGITAL_TWIN.md`; FR-TWIN group |
| 5 | Project Archive | The authoritative registry of every project (WildGuard AI, CyberBuddy, PhishGuard, and all others per MASTER_CONTEXT §6) with status, stack, artifacts, and provenance | `Project` entity in `knowledge/KNOWLEDGE_GRAPH.md`; FR-ING group |
| 6 | Research Repository | A citable store of sources, claims, and findings with confidence tiers on every claim | `Claim` and `Source` entities; FR-VER group; `ai/RAG_PIPELINE.md` |
| 7 | Company Knowledge Base | The institutional memory of Linfy Tech Solutions and related ventures, partitioned by privacy tier | `Organization` entity; `security/PRIVACY.md` |
| 8 | AI Mentor | A coach that uses Linford's own trajectory, lessons, and goals to advise him and, at P1, his mentees | Mentor Agent in `agents/MULTI_AGENT_ARCHITECTURE.md` |
| 9 | Timeline Engine | A navigable chronology of life and work events at every zoom level from day to decade | FR-TL group; Timeline Agent |
| 10 | Search Engine | Sub-second semantic, hybrid, and natural-language search over everything the querying identity is allowed to see | FR-SRCH group; `api/API_SPECIFICATION.md` |
| 11 | Knowledge Graph | A typed graph of people, organizations, projects, events, ideas, and artifacts and the edges between them | `knowledge/KNOWLEDGE_GRAPH.md`; FR-KG group |
| 12 | Legacy Preservation Platform | The mechanisms of permanence: exports, backups, sealed tier, succession, format migration | `security/` specs; `deployment/BACKUP_AND_RECOVERY.md` |
| 13 | Public Portfolio | The P0 surface: projects, writing, talks, and achievements presented to the world with verified-only claims by default | `ui/UI_UX.md`; P0 tier in `security/PRIVACY.md` |
| 14 | Private Workspace | The P2 default surface where drafts, journals, and unfinished thinking live unobserved | `security/AUTHENTICATION.md`; `security/AUTHORIZATION.md` |
| 15 | Multi-Agent AI System | The twelve-agent roster of [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md) §7 operating under an orchestrator with budgets and audit | `agents/MULTI_AGENT_ARCHITECTURE.md` |
| 16 | Long-Term Memory System | Episodic, semantic, procedural, and reflective memory that consolidates over time instead of merely accumulating | `memory/MEMORY_SYSTEM.md` |

### 4.1 How the identities layer

The sixteen identities are four layers of one system, not sixteen products:

```
+--------------------------------------------------------------+
| EXPRESSION      Public Portfolio | Digital Twin | AI Mentor   |
|                 (what the world and the owner interact with)  |
+--------------------------------------------------------------+
| INTELLIGENCE    Second Brain | Search | Multi-Agent System    |
|                 (reasoning, retrieval, orchestration)         |
+--------------------------------------------------------------+
| STRUCTURE       Knowledge Graph | Timeline | Research Repo |  |
|                 Project Archive | Company KB                  |
|                 (organization and meaning)                    |
+--------------------------------------------------------------+
| SUBSTRATE       Personal Knowledge System | Digital Memory |  |
|                 Long-Term Memory | Private Workspace |        |
|                 Preservation Platform                         |
|                 (capture, storage, privacy, permanence)       |
+--------------------------------------------------------------+
```

### 4.2 Vision invariants

These hold across all horizons and all identities:

- Exactly one owner; all authority derives from Linford or from succession rules he defined.
- Every stored item carries exactly one privacy tier (P0 to P3); default is P2.
- Every biographical assertion is a `Claim` with a confidence tier and linked `Source` records.
- The specification repository remains implementation-free and is itself part of the legacy.

## 5. Acceptance Criteria

The vision is being realized when the following hold, verified per horizon. Numeric thresholds are owned by `specs/NON_FUNCTIONAL_REQUIREMENTS.md`; the criteria here are directional.

**Horizon 1 (foundation) is met when:**
- Every ✅ project in MASTER_CONTEXT §6 exists as a `Project` entity with artifacts, dates, and sources attached.
- A natural-language question about Linford's own work returns a cited, tier-labeled answer.
- The public portfolio renders exclusively P0 content and displays only ✅ claims as fact.
- A complete Legacy Vault export can be produced and read offline.

**Horizon 2 (working decades) is met when:**
- Legacy is the first place the owner looks for his own past work, and the lookup succeeds without leaving the system.
- The Digital Twin passes an owner-run honesty review: no invented facts, correct attribution of 🟡 and 🔴 claims, correct refusals.
- The Reflection Agent produces periodic syntheses the owner actually uses (lessons, goal progress, memory consolidation).
- The 🔴 verification queue from MASTER_CONTEXT §12 trends downward because the Verification Agent resolves items with new evidence.

**Horizon 3 (generations) is met when:**
- A designated successor can gain the access Linford defined, and only that access, without any current vendor's cooperation being essential.
- Sealed (P3) content releases exactly under its defined conditions.
- A future maintainer can rebuild a functioning system from this repository plus a Vault export.

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): the immutable fact base this vision serves.
- [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md): canonical tiers, entities, agent roster, and baseline architecture defaults assumed throughout this document.
- [MISSION](./MISSION.md) and [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md): the normative companions of this vision.
- `specs/PRODUCT_REQUIREMENTS.md` and its downstream chain, which decompose these goals into stable, numbered requirements.

## 7. Risks

| Risk | Nature | Vision-level mitigation |
|------|--------|------------------------|
| Scope sprawl | Sixteen identities invite building sixteen shallow tools | One substrate, layered identities (§4.1); roadmap sequencing in `roadmap/ROADMAP.md` |
| Verification debt | 🟡 and 🔴 claims harden into "facts" through repetition | Provenance First principle; Verification Agent; tier discipline enforced at review (see [CONTRIBUTING](../CONTRIBUTING.md)) |
| Single-owner bus factor | Only Linford understands or can operate the system | Succession rules, Vault exports, and this specification repository as executable-by-humans documentation |
| Vendor and model churn | LLM providers, Supabase, or formats change or disappear | Model-routing abstraction and open-format exports per SPEC_CONVENTIONS §9; Future Proof principle |
| Privacy failure | A P2 or P3 item leaks to a broader audience | Privacy First and Secure by Default principles; deny-by-default authorization in the `security/` specs |
| Twin misrepresentation | The twin asserts unverified claims or is mistaken for the person | Honesty goals (§2, goal 4); non-goal boundary (§3.3); FR-TWIN and FR-VER requirement groups |
| Motivation decay | Capture stops, the record goes stale | Low-friction ingestion (FR-ING group); Reflection Agent prompts; value must exceed maintenance cost (§2, goal 8) |

## 8. Future Enhancements

Beyond the sixteen identities, plausible extensions the vision permits but does not require:

- Family multi-user mode: distinct accounts for family members with their own P1 spaces.
- Mobile capture client (Android, Kotlin, Jetpack Compose), consistent with the owner's ✅ Android skills; deferred per SPEC_CONVENTIONS §9.
- Voice interface for the twin and mentor identities.
- Physical-artifact digitization pipeline (paper notes, certificates, memorabilia).
- Generalization into a template others could self-host for their own legacies, without ever pooling data.

## 9. Examples

**H1, 2026: capture and retrieval.** Linford finishes a GDG Cape Town talk (his CyberBuddy presentation at Pet Projects 2026 is ✅ per MASTER_CONTEXT §7). He drops the slide deck, notes, and event link into Legacy. The Ingestion Agent files an `Artifact` and an `Event`, the Graph Agent links them to the `Project` CyberBuddy and the `Organization` GDG Cape Town, and the Timeline Agent places the talk on 30 June 2026. Months later, the query "what did I say about gamified security coaching?" returns the deck, the notes, and a cited summary in seconds.

**H2, 2031: honest twin.** A journalist emails a question about an award. The twin drafts a reply from P0 and P1 knowledge and inserts: "Linford reports a 3rd place at SA Startup Week 2026 for SpazaLink; this placement is flagged as unverified in his records." The 🔴 tier from MASTER_CONTEXT §7 survived five years of system evolution, exactly as Provenance First demands.

**H3, decades on: succession.** A successor presents the credentials defined in the succession rules. Sealed journals whose release condition is met move from P3 to the audience Linford specified; everything else stays sealed. The successor reads a life's work with every claim still labeled ✅, 🟡, or 🔴.

## 10. Open Questions

- Succession governance: who are the successors, what unlock conditions apply, and what legal instrument (will, trust) backs the technical mechanism? `> TODO(verify): requires owner decision; capture in security/ succession material.`
- Post-lifetime twin policy: does the twin keep answering after the owner's death, in what voice, and labeled how? Owner decision pending.
- Data residency for generational storage (South Africa, Zimbabwe, offshore replicas) and POPIA implications. Owner and legal decision pending.
- Which 🔴 items in MASTER_CONTEXT §12 get verified first, and by whom? `> TODO(verify): verification queue priorities from the owner.`

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tiers), §1 (identity), §2 (values), §6 (projects), §11 (long-term vision), §12 (verification queue).
- [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md) §5 (privacy tiers), §6 (entities), §7 (agent roster), §9 (baseline architecture decisions).

## 12. Related Specifications

- [MISSION](./MISSION.md): why the platform exists.
- [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md): the binding design principles.
- `specs/PRODUCT_REQUIREMENTS.md`: the requirement-level decomposition of this vision.
- `architecture/MASTER_ARCHITECTURE.md`: how the layered identities become a system.
- `roadmap/ROADMAP.md`: the sequencing of the horizons.
