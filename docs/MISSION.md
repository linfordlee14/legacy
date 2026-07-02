# MISSION
### Mission of the Legacy platform, derived from Linford Musiyambodza's canonical personal mission

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md), [VISION](./VISION.md) |

---

## 1. Purpose

This document records two missions and the relationship between them: the owner's personal mission, quoted from its canonical source, and the platform mission of Legacy, which is derived from it. It also fixes the guiding commitments every specification must honor, the measures by which mission success is judged, and the stakeholders the mission serves. Where [VISION](./VISION.md) describes what Legacy becomes, this document describes why it exists at all.

### 1.1 The owner's canonical mission statement

Quoted character for character from [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §3:

> To build practical, AI-powered software that serves African communities — protecting wildlife, digitizing the informal economy, improving community safety, and empowering township youth — as an act of faith-driven service.

Two provenance notes, both required by MASTER_CONTEXT itself:

1. **This wording is an editorial synthesis, not a verbatim quote from Linford.** MASTER_CONTEXT §3 states that the statement was "synthesized from consistent public tagline + project portfolio," rated ✅ for the pattern it expresses and editorial for its exact wording. Specifications may rely on the pattern; they must not present the sentence as words Linford spoke or wrote.
2. **Punctuation caveat.** The quotation above preserves the source's original punctuation, including its em dashes, exactly because it is a quotation. Repository prose never uses em dashes (SPEC_CONVENTIONS §2.5); when other documents restate the mission in their own words, they follow repository style.

### 1.2 The platform mission

The platform mission is a design decision derived from the personal mission and from MASTER_CONTEXT §11 (long-term vision):

**Legacy exists to preserve, organize, understand, and extend Linford Musiyambodza's work, ideas, projects, research, code, values, and impact, across his lifetime and beyond it, with verifiable provenance and owner-controlled privacy.**

The derivation is direct. A mission of practical, faith-driven building for African communities generates a large and growing body of work (MASTER_CONTEXT §6 lists five ✅ public projects and a longer self-reported portfolio). That body of work is the evidence of the mission, the raw material for future work, and the inheritance Linford leaves. Legacy is the system that keeps that body of work alive, truthful, and usable.

## 2. Goals

The platform mission decomposes into four verbs. Each verb is a goal with a distinct failure mode that Legacy must prevent.

| Verb | Goal | Failure prevented | Primary mechanisms |
|------|------|-------------------|--------------------|
| Preserve | Capture and durably store work, ideas, projects, research, code snapshots, artifacts, and reflections | Loss: platform shutdowns, dead links, forgotten drafts | FR-ING group in `specs/FUNCTIONAL_REQUIREMENTS.md`; `deployment/BACKUP_AND_RECOVERY.md`; Legacy Vault export |
| Organize | Give everything structure: entities, typed relationships, chronology, tags, tiers | Chaos: an archive nobody can navigate | `knowledge/KNOWLEDGE_GRAPH.md`; FR-KG and FR-TL groups; Curation Agent |
| Understand | Make the corpus answerable: search, retrieval, synthesis, reflection, verification | Opacity: data that exists but yields no insight | `ai/RAG_PIPELINE.md`; FR-SRCH and FR-VER groups; Reflection Agent |
| Extend | Put the corpus to work: the twin, the mentor, the portfolio, new writing, mentees served | Inertness: a museum instead of an instrument | `ai/DIGITAL_TWIN.md`; Mentor and Writing Agents; P0 portfolio surface |

A secondary goal follows from the faith dimension of the personal mission: Legacy must handle the owner's faith identity (the "El Roi" signature is ✅ per MASTER_CONTEXT §1; faith-led mission framing is ✅ per §2) with the care defined by the Faith-Respectful Stewardship principle in [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md).

## 3. Scope

### 3.1 In scope

- The mission of the Legacy platform and its derivation from the owner's mission.
- Guiding commitments binding on all specifications (§4).
- Measures of mission success (§5) and the stakeholder map (§3.3).

### 3.2 Out of scope

- The owner's personal mission itself: it is owned by Linford and recorded canonically in MASTER_CONTEXT §3. This document quotes it; it never edits it.
- Product mechanics, requirements, and architecture: these live in `specs/` and `architecture/`.
- Any claim that Legacy advances African communities directly. Legacy serves the person who does that work; the communities are served through him. Overclaiming here would violate the honesty norms of this repository.

### 3.3 Stakeholders

Personas are specified in `specs/USER_PERSONAS.md`; this table fixes the mission-level view.

| Stakeholder | Relationship to the mission | Default tier exposure |
|-------------|-----------------------------|-----------------------|
| Linford Musiyambodza | Owner; sole authority; primary daily user | P0 to P3 (all) |
| Trusted collaborators and mentees | Named individuals granted specific access (for example collaborators listed in MASTER_CONTEXT §10, all 🟡) | P0 plus granted P1 |
| Family and successors | Inheritors of the record under succession rules | P0 plus granted P1; P3 on unlock conditions |
| Public audience | Readers of the portfolio: peers, employers, partners, community | P0 only |
| Future AI sessions and agents | Maintainers and operators of the system; consumers of this repository | Tier-scoped per task; bound by [CONTRIBUTING](../CONTRIBUTING.md) |

## 4. Requirements

At mission level, requirements take the form of guiding commitments. Every specification, feature, and agent behavior must be compatible with all seven. Numbered, testable requirements derived from these live in `specs/PRODUCT_REQUIREMENTS.md`.

1. **Truthfulness.** The system never asserts more than its evidence supports. Confidence tiers travel with every claim from ingestion to display (Provenance First principle).
2. **Stewardship, not exploitation.** The corpus is held in trust for the owner and his successors. No monetization of personal data, no training external models on private tiers, no dark patterns.
3. **Service orientation.** Features are judged by whether they help the owner build, learn, mentor, and ship, in line with his documented "practical impact over theory" value (✅ per MASTER_CONTEXT §2).
4. **Privacy sovereignty.** The owner alone moves content toward broader audiences; the system defaults everything to P2 and never widens exposure automatically.
5. **Durability.** Every mission-critical capability has an answer to the question "what happens in thirty years?": open formats, exports, documented rebuild paths.
6. **Faith respect.** Faith-related content is first-class and protected: prayer reflections default to P2 and are P3-capable, and the twin does not perform faith beyond what the record supports (Faith-Respectful Stewardship principle).
7. **Honest representation of Africa-focused work.** Project impact claims (users served, accuracy figures, placements) carry tiers like all other claims; the portfolio presents 🟡 and 🔴 items as reported, not achieved.

## 5. Acceptance Criteria

Mission success is measured on the four verbs plus the commitments. Exact thresholds are owned by `specs/NON_FUNCTIONAL_REQUIREMENTS.md`; these criteria define what is measured.

- **Preserve:** coverage of the known corpus (every ✅ project and artifact class in MASTER_CONTEXT §6 and §9 represented in the system); zero unrecoverable losses; Vault export freshness within its defined window.
- **Organize:** proportion of stored items connected to at least one entity and one timeline event; duplicate rate trending down under the Curation Agent.
- **Understand:** owner-judged answer quality on a recurring evaluation set; citation presence on all biographical answers; retrieval latency within NFR bounds.
- **Extend:** cadence of outputs actually shipped from the system (portfolio updates, articles, talk materials); mentee sessions served at P1; twin honesty review passed (no tier upgrades, correct refusals).
- **Commitments:** zero incidents of automatic exposure widening; zero unattributed 🟡/🔴 claims on public surfaces; audit log completeness for all agent actions.

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §2, §3, §11: the values, mission, and long-term vision this document derives from.
- [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md): tier names, entity names, and style rules used here.
- [VISION](./VISION.md): the sixteen identities that operationalize this mission.
- `specs/USER_PERSONAS.md`: detailed stakeholder personas.

## 7. Risks

| Risk | Mission impact | Mitigation |
|------|----------------|------------|
| Mission drift toward a generic notes product | The four verbs blur; Extend and faith respect get dropped as "nice to have" | This document is normative; review checklist in [CONTRIBUTING](../CONTRIBUTING.md) checks mission compatibility |
| Overclaiming impact | Public portfolio inflates 🟡/🔴 achievements, damaging the credibility the mission depends on | Commitment 7; FR-VER group; portfolio defaults to ✅-only fact presentation |
| Owner mission evolution | Linford's personal mission may be restated over time | MASTER_CONTEXT is the single place it changes; this document quotes rather than copies semantics into many files |
| Stakeholder conflict | Family, mentees, and public audiences want different things from the record | Tier system plus succession rules; owner authority is final while living |
| Sensitive faith content exposure | Prayer reflections or faith journaling leak beyond intent | P2 default, P3 capability, Faith-Respectful Stewardship principle |

## 8. Future Enhancements

- A periodic (for example annual) mission review ritual, supported by the Reflection Agent, producing a signed owner statement of any mission evolution for MASTER_CONTEXT's maintainers.
- Impact evidence pipeline: attaching verifiable artifacts (deployment records, testimonials, event listings) to project impact claims so 🔴 items can graduate to ✅.
- Mentee-facing mission mode: a P1 view where the Mentor Agent explains the owner's trajectory to township youth audiences, consistent with the Linfy Academy concept (🟡 per MASTER_CONTEXT §6).

## 9. Examples

**Mission applied to a feature decision.** A proposal suggests auto-publishing weekly activity summaries to the public portfolio. Commitment 4 (privacy sovereignty) rejects auto-publishing; commitment 3 reshapes it: the Writing Agent drafts the summary to a P2 queue, and the owner promotes to P0 explicitly.

**Mission applied to twin behavior.** Asked "did Linford win SA Startup Week?", the twin consults the `Claim` record, finds a 🔴 tier (MASTER_CONTEXT §7), and answers: "Linford reports a 3rd place for SpazaLink at SA Startup Week 2026; this has not been independently verified." Truthfulness beats impressiveness.

**Mission applied to preservation.** The RhinoGuardians prototype (🟡, with a reported ~95% accuracy figure per MASTER_CONTEXT §6) is ingested with its code snapshot, hackathon context, and the accuracy claim stored as a self-reported `Claim`, so the number can never silently become a verified fact in a future retelling.

## 10. Open Questions

- Should the platform mission statement itself ever be shown on the public portfolio, and if so, how is it distinguished from the owner's personal mission? Owner decision pending.
- `> TODO(verify): exact wording Linford would personally sign for his mission, to replace or ratify the editorial synthesis in MASTER_CONTEXT §3.`
- How often should mission-level acceptance criteria (§5) be formally reviewed: annually, or per roadmap phase? To be settled in `roadmap/ROADMAP.md`.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §2 (values and philosophy), §3 (canonical mission), §11 (long-term vision).
- [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md) §2 (non-negotiable rules), §5 (privacy tiers).

## 12. Related Specifications

- [VISION](./VISION.md): what Legacy becomes in service of this mission.
- [LEGACY_PRINCIPLES](./LEGACY_PRINCIPLES.md): the design principles enforcing the commitments above.
- `specs/PRODUCT_REQUIREMENTS.md`: requirement-level decomposition.
- `security/PRIVACY.md`: enforcement of privacy sovereignty.
- `ai/DIGITAL_TWIN.md`: enforcement of truthful representation.
