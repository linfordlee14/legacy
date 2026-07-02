# USER_PERSONAS
### Canonical personas (PERS-01 to PERS-07) for the Legacy digital legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) |

---

## 1. Purpose

This document defines the canonical set of personas served by Legacy. Every user story ([USER_STORIES](./USER_STORIES.md)), use case ([USE_CASES](./USE_CASES.md)), and feature specification ([FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md)) traces to at least one persona defined here. Personas are the bridge between the facts in [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) and testable product behavior, and they carry the same confidence-tier discipline: attributes of PERS-01 are grounded in MASTER_CONTEXT with tiers (✅ verified, 🟡 self-reported, 🔴 flagged); all other personas are archetypal roles, not real named individuals.

## 2. Goals

- Give every downstream spec a stable persona vocabulary (`PERS-##`) that is never renumbered.
- Map each persona to the privacy tiers (P0-P3) it may touch, so authorization specs have a human-level anchor.
- Capture goals, frustrations, key journeys, and success criteria per persona so acceptance testing has behavioral targets.
- Encode the provenance rules of MASTER_CONTEXT §0 into persona expectations (for example, PERS-04 must see verification markers; PERS-06 must receive machine-readable tiers).
- Keep future-generation and collaborator personas archetypal so the repository never invents facts about real people.

## 3. Scope

**In scope:** persona definitions PERS-01 through PERS-07; their context, goals, frustrations, access tier mapping, key journeys (cross-referenced to UC and US IDs), and success criteria; persona-to-feature affinity.

**Out of scope:** requirement statements (see the requirements documents in `specs/`), authorization mechanics (see [AUTHORIZATION](../security/AUTHORIZATION.md)), UI treatments (see [UI_UX](../ui/UI_UX.md)), and the agent roster (see [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)). No new biographical facts are introduced here.

## 4. Requirements

Each persona below is a normative definition. "Access tier mapping" states the maximum tier reachable and under what condition; defaults follow [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §5 (new content defaults to P2, nothing becomes less restrictive without explicit owner action).

### PERS-01: Linford, the Owner

**One line:** The living subject, sole owner, and primary operator of Legacy.

**Context.** Linford Musiyambodza is a faith-driven African software builder and AI engineer based in Strand, Cape Town, South Africa (✅). He is the founder and CEO of Linfy Tech Solutions (✅) and CTO of NeuroGrowth Labs (✅). He builds in public under the tagline "Building in public. Building for Africa." (✅) and signs work "El Roi" (✅). His primary code presence is GitHub `linfordlee14` (✅) with hackathon handle `hacker1401` (✅). He practices Specification-Driven Development, starting builds with mission, roadmap, and tech stack documents (🟡, self-reported methodology). His documented style guide includes no em dashes and a direct, warm builder-narrative tone (🟡, self-reported style preferences). He is an active GDG Cape Town community member who presented CyberBuddy at Pet Projects: The 2026 Edition (✅).

**Goals.**
- Capture everything that matters (code, writing, talks, projects, journals, prayer reflections) with near-zero friction, so the corpus is complete while he is alive to verify it.
- Maintain a provably honest record: verified claims separated from self-reported and flagged ones, per MASTER_CONTEXT §0.
- Operate a public portfolio that advances Linfy Tech Solutions and his build-in-public practice without ever leaking private material.
- Leave a Digital Twin and an offline vault that can speak for him faithfully to future generations.
- Delegate research, curation, and writing to agents while retaining human approval over anything public or destructive.

**Frustrations.**
- Context scattered across GitHub, DEV.to, LinkedIn, hackathon platforms, and local files; re-explaining himself to every new AI session.
- AI tools that overstate facts: he needs a system that refuses to upgrade 🟡/🔴 claims (MASTER_CONTEXT §0 rule).
- Manual verification backlog (MASTER_CONTEXT §12 lists a concrete queue) with no tooling to work it down.
- Fear of platform lock-in and data loss over a multi-decade horizon.

**Access tier mapping.**

| Tier | Access |
|------|--------|
| P0-P2 | Full read/write |
| P3 | Full write; read subject to any self-imposed time locks he configures (see Open Questions) |

**Key journeys.** UC-001 (ingest documents), UC-002 (ingest a repository), UC-006 (publish to portfolio), UC-008 (sealed journal entry), UC-009 (verification queue), UC-010 (generate presentation), UC-011 (agent research task), UC-014 (vault export). Stories US-001 through US-035.

**Success criteria.**
- Anything captured is findable and citable within minutes, not days.
- No public surface ever asserts a 🔴 claim as fact; a zero-incident record on privacy leaks.
- Weekly time spent on manual curation trends down as agents take over routine work with approval gates.
- He would trust the twin to represent him to a recruiter, a mentee, or a grandchild.

### PERS-02: Future Family Member / Descendant

**One line:** An archetypal member of a future generation who inherits access to the legacy.

> TODO(verify): MASTER_CONTEXT records no verified family members. This persona is deliberately archetypal (no names, no invented relationships) until the owner adds verified family context to MASTER_CONTEXT.

**Context.** A descendant or family member, possibly decades in the future, who may never have met Linford. Technical skill ranges from casual phone user to none. They arrive through succession (see PERS-05) or through content released to them under P3 rules. Their interest is personal: who was he, what did he believe, what did he build, what would he say to me.

**Goals.**
- Understand Linford's life story, values, and faith in his own words and voice.
- Ask conversational questions and receive honest, tier-aware answers rather than a hagiography.
- Read journal entries and prayer reflections released to them by time lock or succession rules.
- Access the legacy even if the hosted platform no longer exists (offline vault).

**Frustrations.**
- Dead links, defunct platforms, unreadable proprietary formats.
- Not knowing what is fact versus family legend; they need provenance surfaced gently.
- Overwhelming raw archives with no narrative entry point (timeline, twin, curated collections).

**Access tier mapping.**

| Tier | Access |
|------|--------|
| P0 | Always readable |
| P1 | If granted (by owner in life, or by succession plan) |
| P2 | No access unless the succession plan explicitly converts specific items |
| P3 | Read only items whose release conditions (time lock, succession event) have been met |

**Key journeys.** UC-003 (ask the twin a biographical question), UC-004 (explore the timeline), UC-014/UC-015 (open the vault, post-succession access). Stories US-036 to US-039.

**Success criteria.**
- Can answer "what was he like" after one session with the twin and timeline.
- Sealed content appears exactly when its release conditions say it should, never earlier.
- The vault opens and reads on commodity software with no live platform dependency.

### PERS-03: Trusted Collaborator or Mentee

**One line:** A person the owner explicitly trusts with a scoped slice of the private corpus.

**Context.** MASTER_CONTEXT §10 records a pattern of named collaborators (hackathon teammates, community organizers, a prayer partner, mentees); all of those individual identifications are 🟡 self-reported. This persona models the pattern, not any named individual: a co-builder on a project such as a hackathon submission, or a township youth mentee in a mentorship program the owner has described building (🟡). They receive a P1 `Grant` scoped to specific projects or collections.

**Goals.**
- See exactly the shared material (project docs, research notes, drafts) and nothing else.
- Ask questions of the corpus and get answers restricted to their grant scope.
- For mentees: receive curated learning material and mentorship guidance derived from the owner's real experience.
- Contribute artifacts back (notes, drafts) that enter the owner's review pipeline rather than publishing directly.

**Frustrations.**
- Ambiguity about what they can and cannot see or repeat publicly.
- Access that silently breaks mid-project, or lingers after the collaboration ends.
- Answers that leak context from outside their scope (a trust violation in both directions).

**Access tier mapping.**

| Tier | Access |
|------|--------|
| P0 | Always readable |
| P1 | Read (optionally comment/contribute) within explicit `Grant` scope, time-boxed by default |
| P2, P3 | Never |

**Key journeys.** UC-007 (receive a P1 grant), UC-003 variant (scoped question answering). Stories US-040 to US-042.

**Success criteria.**
- Zero access beyond grant scope in audit review; grants expire or are revoked cleanly.
- Collaborators report the shared workspace is clearer than ad-hoc file sharing.

### PERS-04: Public Visitor

**One line:** Anyone on the open web: recruiter, potential partner, community member, journalist, curious stranger.

**Context.** Arrives at the public portfolio (F10) via search, LinkedIn, GitHub, DEV.to, or a conference talk. A recruiter is assessing credibility and skill evidence; a partner or funder is doing due diligence; a GDG community member is following the build-in-public narrative. They have no account and no trust relationship.

**Goals.**
- Quickly assess who Linford is, what he has shipped, and whether claims are substantiated.
- Follow projects, talks, and writing; find a legitimate contact pathway.
- For due-diligence visitors: distinguish verified achievements from self-reported ones (the portfolio surfaces tier markers rather than flattening everything to fact).

**Frustrations.**
- Portfolios that are all claims and no evidence.
- Broken or stale content; no way to tell what is current.
- Dark patterns: they should never be prompted for data to see public content.

**Access tier mapping.**

| Tier | Access |
|------|--------|
| P0 | Read only |
| P1-P3 | No access, no existence disclosure (private items must not be enumerable or inferable) |

**Key journeys.** Browse portfolio, project pages, timeline (public slice), public search. Stories US-043 to US-046.

**Success criteria.**
- A recruiter can trace any public achievement claim to a citation or an explicit "self-reported" marker.
- No P1+ artifact, title, or metadata ever appears in public pages, sitemaps, feeds, or search indexes.

### PERS-05: Estate Steward / Executor

**One line:** The person or institution legally and technically responsible for executing succession.

**Context.** Appointed by the owner in the succession plan (F16). May be a family member, a professional executor, or a trusted peer; technically capable of following a documented runbook but not necessarily a developer. Acts rarely and under high stakes: incapacity, death, or a planned handover.

> TODO(verify): no steward has been named in MASTER_CONTEXT; the role is defined structurally and assigned later by the owner.

**Goals.**
- Activate succession through a verifiable, multi-step process that resists both fraud and accident.
- Execute the owner's release schedule for P3 content exactly as written, without needing to read the content itself.
- Hand over access to designated heirs (PERS-02) and wind down or transfer infrastructure.
- Leave a complete audit trail of every action taken.

**Frustrations.**
- Ambiguous instructions at the worst possible time.
- Systems that require the deceased owner's live credentials.
- Legal exposure from over- or under-releasing content.

**Access tier mapping.**

| Tier | Access |
|------|--------|
| P0 | Read |
| P1 | Administrative visibility of grants (who has access), not necessarily content |
| P2 | No content access by default; administrative actions only (export, transfer) unless the plan grants more |
| P3 | Execute release operations without content read access, unless the succession plan explicitly grants read |

**Key journeys.** UC-015 (activate succession), UC-014 (final vault export), release-schedule execution. Stories US-047 to US-050.

**Success criteria.**
- Succession completes end-to-end from the runbook alone, with every step logged as `AuditLogEntry` records.
- No P3 item is released outside its defined conditions; false-activation attempts are detected and blocked.

### PERS-06: Machine Consumer

**One line:** A future AI agent, model session, or automated integration reading the corpus through the API.

**Context.** MASTER_CONTEXT is explicitly written so that "any future AI reading this file" can understand Linford without re-research. Legacy generalizes that intent: a machine consumer may be the owner's own agent stack, a family-operated assistant decades later, or an integration (for example a site generator). It authenticates with a scoped token and consumes structured data: entities, `Claim` records with confidence tiers, `Source` links, embeddings, and change feeds.

**Goals.**
- Deterministic, documented, versioned API access ([API_SPECIFICATION](../api/API_SPECIFICATION.md)).
- Machine-readable provenance: every factual payload carries its tier (`verified`, `self_reported`, `flagged`) and source references so downstream generation can obey the never-upgrade rule.
- Stable IDs, pagination, and incremental sync so long-running consumers stay consistent.

**Frustrations.**
- Prose-only knowledge with no structured claims; silent schema changes; tier information stripped in transit.
- Rate limits or auth models that assume an interactive human.

**Access tier mapping.**

| Tier | Access |
|------|--------|
| P0 | Default token scope |
| P1-P3 | Only when the token is explicitly scoped by the owner (or by succession rules); every request tier-checked and audited |

**Key journeys.** UC-016 (read the corpus via API). Stories US-051 to US-053.

**Success criteria.**
- A cold-start agent can reconstruct an accurate, tier-faithful biography from the API alone.
- Zero tier-violation responses under authorization test suites ([TESTING](../testing/TESTING.md)).

### PERS-07: Linfy Tech Team Member (optional persona)

**One line:** A member of the owner's company working inside a company-scoped slice of the workspace.

**Context.** Linfy Tech Solutions is the owner's verified company (✅); the internal team composition and the Hermes agent ecosystem are self-reported (🟡) and are not part of Legacy's design (see the roster note in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §7). This persona covers a team member granted P1 access to company-related collections: project documentation, brand voice material, published content pipelines.

**Goals.**
- Reuse the owner's project history and brand voice assets to produce consistent company content.
- Keep company work separated from personal journals, family material, and sealed content.

**Frustrations.**
- Blurred personal/company boundaries; accidentally drafting from private personal context.

**Access tier mapping.** P0 read; P1 read/contribute within company-scoped `Collection` grants; P2/P3 never.

**Key journeys.** UC-007 (grant pattern), UC-010 (presentation generation from shared projects). Stories US-054 to US-055.

**Success criteria.** Company content is produced from granted scope only, with attribution rules honored; offboarding revokes access in one action.

### Persona-to-feature affinity matrix

| Persona | Primary features | Secondary features |
|---------|-----------------|--------------------|
| PERS-01 Owner | F1-F16 (all) | : |
| PERS-02 Descendant | F6, F3, F16, F12 (released items) | F4, F5, F10 |
| PERS-03 Collaborator/Mentee | F11 (granted slice), F5, F14 | F4, F13 |
| PERS-04 Public Visitor | F10 | F4 (public scope), F3 (public slice), F9 (markers) |
| PERS-05 Estate Steward | F16 | F12 (release execution), audit surfaces |
| PERS-06 Machine Consumer | API over F2, F5, F9 | F4, F7 |
| PERS-07 Linfy Tech Team Member | F11 (company scope), F15 | F13, F10 pipeline |

## 5. Acceptance Criteria

- AC-1: Every persona has context, goals, frustrations, an explicit P0-P3 access mapping, key journeys, and success criteria. Verified by review against this document's structure.
- AC-2: Every attribute of PERS-01 is traceable to MASTER_CONTEXT with its confidence tier preserved; no attribute exists here that is absent there.
- AC-3: PERS-02 contains no invented names, relationships, or biographical details; the TODO(verify) marker remains until MASTER_CONTEXT is updated.
- AC-4: PERS-03 references the collaborator pattern of MASTER_CONTEXT §10 without asserting any named individual as a verified user of the system.
- AC-5: Every user story in [USER_STORIES](./USER_STORIES.md) names exactly one primary persona from this document; every use case in [USE_CASES](./USE_CASES.md) casts its actors from this roster.
- AC-6: The access tier mappings here are consistent with [AUTHORIZATION](../security/AUTHORIZATION.md) and [PRIVACY](../security/PRIVACY.md) once those documents are finalized; discrepancies are resolved in favor of the security specs and back-ported here.

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): sole source of PERS-01 facts and of the confidence-tier rules all personas inherit.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): privacy tier definitions (§5), canonical entities (§6), ID scheme (§4).
- [AUTHORIZATION](../security/AUTHORIZATION.md) and [PRIVACY](../security/PRIVACY.md): enforcement of the access mappings stated here.
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md): PERS-01 voice fidelity and PERS-02 conversational experience.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): PERS-06 contract.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Persona drift: specs quietly serve an idealized owner rather than the documented one | Features misaligned with real workflows | AC-2 review on every revision; MASTER_CONTEXT remains immutable input |
| Archetypal personas get "filled in" with invented details over time | Fabricated facts contaminate the corpus | TODO(verify) markers; review rule that PERS-02/PERS-05 stay nameless until verified |
| Access mappings here diverge from security specs | Contradictory implementations | AC-6 reconciliation rule, security specs win |
| PERS-06 designed only for today's AI interfaces | Corpus unreadable to future consumers | Vault format (F16) and versioned API as dual channels; plain-data fallbacks |
| Steward persona untested until a real crisis | Succession failure at the worst time | Succession rehearsal drills required in [TESTING](../testing/TESTING.md) and F16 spec |

## 8. Future Enhancements

- Add verified family personas if and when MASTER_CONTEXT gains verified family context.
- Split PERS-03 into distinct Collaborator and Mentee personas if their journeys diverge materially (mentorship program maturity would trigger this).
- Add an Institutional Researcher / Historian persona (archives, universities) for the multi-decade horizon.
- Add a Legal/Compliance Reviewer persona if POPIA or estate-law workflows require a distinct actor.
- Persona analytics: instrument surfaces to validate assumed journeys against real usage.

## 9. Examples

**Example 1, tier-faithful twin answer for PERS-02.** A descendant asks the twin: "Did he win at SA Startup Week?" The twin responds in first person with attribution: "I reported that SpazaLink placed 3rd at SA Startup Week 2026, but that placement is still flagged for verification in my records, so treat it as my account rather than an established fact." (Grounded in MASTER_CONTEXT §7, 🔴 item.)

**Example 2, PERS-04 recruiter flow.** A recruiter opens the public portfolio, sees the CyberBuddy project page marked with a verified badge citing the GDG Cape Town Pet Projects 2026 presentation (✅), and sees the "39+ hackathons" figure explicitly labeled self-reported (🟡). They export a citation list for their notes.

**Example 3, PERS-05 scoped power.** The steward executes "release tranche 1 of sealed journals to designated family" from the succession runbook. The system releases exactly the `JournalEntry` items whose conditions match, logs each release, and never displays the entry contents to the steward.

## 10. Open Questions

- Should PERS-01 be able to hard-seal P3 items against his own casual reading (a true time capsule), or is owner access always absolute? > TODO(verify): owner decision needed; affects F12 and F16 designs.
- Does PERS-05 require split control (two stewards confirming activation) by default? Recommended, pending owner decision.
- Do mentee journeys (PERS-03) need a child-safety review if Linfy Academy serves minors (🟡 project description)? > TODO(verify): program details and applicable policy.
- Should PERS-07 exist at v1, or is company access deferred until Linfy Tech workflows are concrete? Marked optional pending roadmap decision.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tiers), §1 (identity), §2 (values), §4 (roles), §6 (projects), §10 (network), §12 (verification queue).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4 (IDs), §5 (privacy tiers), §6 (entities), §7 (agent roster).

## 12. Related Specifications

- [USER_STORIES](./USER_STORIES.md): stories grouped by these personas.
- [USE_CASES](./USE_CASES.md): flows casting these personas as actors.
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md): feature behavior per persona and tier.
- [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md) and [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md): requirement statements these personas motivate.
- [AUTHORIZATION](../security/AUTHORIZATION.md), [PRIVACY](../security/PRIVACY.md): enforcement of tier mappings.
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), [API_SPECIFICATION](../api/API_SPECIFICATION.md): PERS-02 and PERS-06 primary surfaces.
