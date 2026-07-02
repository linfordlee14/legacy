# UI_UX
### User interface and experience specification for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [DESIGN_SYSTEM](DESIGN_SYSTEM.md), [ACCESSIBILITY](ACCESSIBILITY.md) |

---

## 1. Purpose

This document specifies the user experience of Legacy across its two surfaces: the Private Workspace (the owner's daily operating environment) and the Public Portfolio (the world's window into the work). The experience must make three things effortless and constant: capturing knowledge, trusting what the system says (provenance always visible), and knowing who can see what (privacy state always visible).

## 2. Goals

- Capture-first: adding knowledge is never more than one action away, anywhere in the workspace.
- Provenance-first: every claim-derived element shows its confidence tier without extra clicks.
- Privacy-legible: the current tier of any content, and the audience of any surface, is always on screen.
- Calm and archival in tone: this is a place for a life's work, not a growth-hacked feed.

## 3. Scope

**In scope:** experience principles, information architecture, navigation, key screen specifications with wireframes, interaction patterns, and system states for both surfaces.

**Out of scope:** visual tokens and component internals (see [DESIGN_SYSTEM](DESIGN_SYSTEM.md)); accessibility conformance detail (see [ACCESSIBILITY](ACCESSIBILITY.md)); API mechanics (see [API_SPECIFICATION](../api/API_SPECIFICATION.md)).

## 4. Requirements

### 4.1 Information architecture

**Private Workspace** (authenticated; owner sees P2 ceiling, trusted users a grant-scoped subset):

| Area | Content | Feature |
|------|---------|---------|
| Dashboard | Today's captures, agent activity, approvals due, verification queue count, goal snapshots | FS-011 |
| Capture Inbox | Quick add (text, file, voice, link), ingestion job statuses, review flags | FS-001 |
| Timeline Explorer | Chronological navigation, era zoom, domain filters | FS-003 |
| Graph Explorer | Entity neighborhoods, merge proposals, edge browsing | FS-002 |
| Projects and Research | Project pages, research collections, lessons | FS-013 |
| Search | Unified lexical, semantic, hybrid, natural-language search | FS-004 |
| Ask and Twin Chat | Cited Q&A and twin conversations | FS-005, FS-006 |
| Journals | Entries, prayer reflections, sealing controls | FS-012 |
| Verification Queue | 🔴 and stale 🟡 claims, evidence packets, tier decisions | FS-009 |
| Agent Monitor | Runs, traces, budgets, approvals | FS-008 |
| Mentor | Goals, evidence-based coaching | FS-014 |
| Studio | Writing and presentation drafts under review | FS-015 |
| Vault and Succession | Exports, drills, steward settings | FS-016 |
| Settings | Account, grants, tokens, appearance | All |

**Public Portfolio** (P0 only): profile, projects, talks, articles, timeline highlights, public twin chat with a permanent disclosure banner, accessibility statement, contact.

### 4.2 Navigation model

Persistent left navigation (workspace) with the capture button fixed and globally available (keyboard: `c`). Global search from any screen (keyboard: `/`). Breadcrumbs on entity pages reflecting graph position. The portfolio uses a simple top navigation; no workspace chrome leaks into it.

### 4.3 Key screens

**Dashboard**

```
+----------------------------------------------------------------------+
| LEGACY  [Search /]                                   [+ Capture] [LM] |
+------------+---------------------------------------------------------+
| Dashboard  | Good morning. 3 approvals waiting - 2 flags to review    |
| Capture    | +---------------------+  +-----------------------------+ |
| Timeline   | | Agent activity      |  | Verification queue (4)      | |
| Graph      | | night ingest: 42 ok |  | [FLAGGED] SpazaLink placing | |
| Projects   | | reflection: done    |  | [FLAGGED] HBS Foundry       | |
| Search     | +---------------------+  +-----------------------------+ |
| Ask        | | Recent captures     |  | Goals                        | |
| Journals   | | idea: kasi commerce |  | cybersecurity depth [====  ] | |
| ...        | +---------------------+  +-----------------------------+ |
+------------+---------------------------------------------------------+
```

**Twin Chat** (workspace mode shown; public mode identical plus disclosure banner and P0 scope):

```
+----------------------------------------------------------------------+
| Twin Chat                                   Scope: Private (P2) [i]   |
+----------------------------------------------------------------------+
| You: Did SpazaLink place at SA Startup Week?                          |
| Twin (AI representation): Linford reports a 3rd place finish for      |
| SpazaLink at SA Startup Week 2026, but this claim is currently        |
| unverified. [Claim: FLAGGED] [source: master context - achievements]  |
|                                                                       |
|                 [citation chips: hover or Enter to expand source]     |
+----------------------------------------------------------------------+
| [message input.....................................] [send]           |
+----------------------------------------------------------------------+
```

**Verification Queue**

```
+----------------------------------------------------------------------+
| Verification Queue (4 open)             [sort: oldest] [filter: all]  |
+----------------------------------------------------------------------+
| [FLAGGED] "SpazaLink: 3rd place, SA Startup Week 2026"                |
|   evidence: 0 attached - proposal: none yet                           |
|   [request research] [attach evidence] [resolve...]                   |
| [FLAGGED] "IUS Africa: Assistant Cluster Leader"                      |
|   evidence: 1 packet from Verification Agent - proposal: keep flagged |
|   [review packet] [resolve...]                                        |
+----------------------------------------------------------------------+
```

**Journal Editor**: full-width writing surface; tier control always visible in the header (`Private P2 ▾` with P3 sealing and release-condition dialog); prayer reflection type selectable; autosave with revision history.

**Timeline Explorer**: horizontal era band (decade → year → month zoom), vertical event list for the selected range, undated shelf toggle, every entry carrying tier and provenance badges.

**Graph Explorer**: focus-node canvas plus an always-present list/table equivalent (the accessible primary per [ACCESSIBILITY](ACCESSIBILITY.md)); merge proposals appear as a review tray, never auto-applied.

### 4.4 Interaction patterns

| Pattern | Rule |
|---------|------|
| Quick capture | Global button and shortcut; capture completes in one modal; refinement can happen later in the inbox |
| Citation chips | Inline after any claim-derived sentence; hover or keyboard-expand reveals source, tier, and a link to the claim |
| Confidence badges | Rendered as text-bearing badges (Verified, Self-reported, Flagged) per [DESIGN_SYSTEM](DESIGN_SYSTEM.md); emoji tiers from MASTER_CONTEXT map to these labels; never color or emoji alone |
| Tier changes | Always a confirmation dialog stating exactly who gains or loses visibility; publishing to P0 shows a full preview of what becomes public |
| Agent approvals | Actionable cards showing the proposed effect as a diff (what will be created, changed, published, or deleted); approve and reject with one action each |
| Sealed content | Rendered as a labeled placeholder with release conditions summary; contents never previewed |
| Streaming answers | Progressive rendering with a visible "answering" state; citations attach as they arrive; a stop control is always present |
| Destructive actions | Two-step with typed confirmation for permanent erasure; soft delete everywhere else with undo |

### 4.5 System states

Every screen defines empty, loading, streaming (where applicable), error, and offline states. Empty states teach (what this area is for, one primary action). Errors are honest and specific, echoing the API error model. Offline mode presents the read-only vault view with a persistent banner (NFR-018). The public portfolio degrades gracefully to fully static content if AI services are down.

### 4.6 Content tone

UI copy is direct and warm, in the builder-narrative spirit documented as the owner's style (🟡, MASTER_CONTEXT §2). No em dashes in UI strings (the owner's documented preference extends to product copy). No dark patterns of any kind; the platform never nags, never guilt-trips, never auto-shares.

## 5. Acceptance Criteria

- Every FS feature in [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md) is reachable through the IA above, verified by a navigation audit.
- Capture is reachable in one action from every workspace screen (automated UI test).
- 100 percent of claim-derived UI elements render tier badges and expandable citations (component audit plus the NFR-039 test).
- Tier-change and publish flows show accurate audience previews in usability review with the owner.
- All key screens implement all defined states; the offline vault mode renders the corpus read-only.

## 6. Dependencies

- [DESIGN_SYSTEM](DESIGN_SYSTEM.md): components and tokens these screens compose.
- [ACCESSIBILITY](ACCESSIBILITY.md): conformance requirements that shape navigation and component choices.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): the data and streaming contracts behind every screen.
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md): disclosure and mode rules the chat surfaces implement.

## 7. Risks

- Provenance UI could overwhelm reading flow if badges are heavy-handed; mitigated by quiet-by-default badge styling with full detail on demand.
- Graph canvas interactions are notoriously inaccessible; mitigated by making the list/table equivalent primary, not secondary.
- Approval cards that hide effects breed rubber-stamping; the diff-style effect preview is mandatory, not cosmetic.
- Two surfaces sharing components risks P2 chrome leaking into P0 pages; mitigated by build-level surface separation and tests.

## 8. Future Enhancements

- Mobile capture app pairing (see [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)).
- Command palette for power navigation.
- Reading-mode themes for long-form journal review.
- Family-facing memorial layout refinements for post-succession mode.

## 9. Examples

The owner lands on the dashboard, sees two verification flags, opens the queue, requests research on the SpazaLink claim, and captures a passing idea with `c` without losing his place. That afternoon, publishing a project page shows him precisely the P0 preview a recruiter will see: the CyberBuddy entry renders "Verified" badges on the GDG talk, while a self-reported metric renders as "Linford reports" phrasing with a "Self-reported" badge. Nothing about the sealed journal from that morning exists anywhere in the preview.

## 10. Open Questions

- Should trusted users get a reduced dashboard or land directly in scoped search? Usability-test with a real P1 user during Phase 2.
- Is the undated shelf better as a timeline toggle or a separate view? Prototype both.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §1 (public persona the portfolio serves), §2 (tone and style identifiers, 🟡), §7 (flagged claims used in screen examples).
- Nielsen heuristics and calm-technology principles as general guidance.

## 12. Related Specifications

- [DESIGN_SYSTEM](DESIGN_SYSTEM.md), [ACCESSIBILITY](ACCESSIBILITY.md)
- [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [USER_PERSONAS](../specs/USER_PERSONAS.md), [USE_CASES](../specs/USE_CASES.md)
- [API_SPECIFICATION](../api/API_SPECIFICATION.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (FR-UI group)
