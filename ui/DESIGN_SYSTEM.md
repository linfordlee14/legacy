# DESIGN_SYSTEM
### Design tokens, components, and visual language foundations for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [UI_UX](UI_UX.md), [ACCESSIBILITY](ACCESSIBILITY.md) |

---

## 1. Purpose

This document specifies the design system underlying every Legacy surface: token architecture, the component inventory, behavior rules, and the visual language principles. It defines structure and semantics now, and leaves brand aesthetics (palette, typefaces, iconography) as owner decisions recorded here when made. The system's signature obligation is making provenance and privacy visible everywhere, beautifully and quietly.

## 2. Goals

- One component library serving both surfaces (workspace and portfolio) with strict surface separation at build time.
- Provenance and privacy indicators as first-class, unskippable components.
- Light and dark themes from a single token architecture.
- Accessibility built into component contracts, not retrofitted.

## 3. Scope

**In scope:** token architecture, typography and spacing scales, color roles, component inventory with states and accessibility notes, motion principles, and UI voice rules.

**Out of scope:** page layouts and flows (see [UI_UX](UI_UX.md)); WCAG conformance program (see [ACCESSIBILITY](ACCESSIBILITY.md)).

## 4. Requirements

### 4.1 Token architecture

Three layers: primitive tokens (raw values) → semantic tokens (roles) → component tokens (per-component bindings). Only semantic and component tokens appear in component specifications; primitives change without touching components.

**Color roles (semantic layer):**

| Role | Use |
|------|-----|
| background, surface, surface-raised | Page and card layering |
| text-primary, text-secondary, text-muted | Content hierarchy |
| accent | Interactive emphasis, links, focus companions |
| success, warning, danger, info | System feedback |
| provenance-verified | The Verified tier |
| provenance-selfreported | The Self-reported tier |
| provenance-flagged | The Flagged tier |
| tier-public, tier-trusted, tier-private, tier-sealed | Privacy tier indication |

All role pairs meet the contrast floors in [ACCESSIBILITY](ACCESSIBILITY.md); provenance and tier colors are never the sole signal (each pairs with a text label and an icon slot).

> TODO(verify): no brand palette, logo, or typeface exists in MASTER_CONTEXT. The owner defines primitive color values and brand assets; until then, implementation uses a neutral placeholder palette validated for contrast, and this document records the final values when chosen.

**Typography:** a role-based scale (display, title, heading, body, body-small, caption, mono) with relative sizing (rem-based), generous line heights for long-form reading (journals, articles), and a system font stack as the default decision pending a brand typeface (TODO above). Unicode bold serif headers are a documented LinkedIn styling habit of the owner (🟡, MASTER_CONTEXT §2); they are a social-content convention and are NOT carried into product typography.

**Spacing and layout:** an 8-point spacing scale with 4-point half-steps; a 12-column fluid grid for the workspace; a narrower reading-measure layout (65 to 75 characters) for long-form content; container queries preferred over viewport-only breakpoints.

### 4.2 Component inventory

| Component | Purpose | States | Accessibility notes |
|-----------|---------|--------|---------------------|
| ConfidenceBadge | Displays a claim's tier as label plus color plus icon slot: "Verified", "Self-reported", "Flagged" | default, compact, expanded | Text always present; announced as "confidence: {tier}"; never emoji-only (the ✅🟡🔴 of MASTER_CONTEXT map to these labels) |
| CitationChip | Inline citation marker expanding to source detail | collapsed, expanded, unresolvable | Keyboard reachable; expansion is a disclosure, not hover-only |
| PrivacyTierIndicator | Shows an item's tier (P0 to P3) | read-only, interactive | Text label always; tooltip explains audience |
| TierSelector | Changes an item's tier with audience preview | default, confirming, disabled | Confirmation dialog described by screen readers; danger styling on loosening |
| SealedContentPlaceholder | Stands in for P3 content | locked, releasable | Announces sealed status and release summary; never leaks content length or preview |
| CaptureQuickAdd | Global capture modal | text, file, voice, link modes | Focus-trapped modal; voice mode fully keyboard-operable |
| StreamingAnswerPanel | Renders progressive AI answers with citations | idle, streaming, complete, stopped, error | Live region announcements per [ACCESSIBILITY](ACCESSIBILITY.md); visible stop control |
| DisclosureBanner | Permanent "AI representation" notice on twin surfaces | default | Role note landmark; not dismissible on public surface |
| AgentApprovalCard | Presents a proposed agent effect as a diff with approve and reject | pending, approved, rejected, expired | Effect summary readable as text; buttons clearly labeled with consequences |
| TimelineEntry | An event on the timeline with date, tier, provenance | default, focused, undated | Date semantics in machine-readable form; undated announced explicitly |
| GraphNodeCard | Entity summary in explorers and search | default, focused, merge-proposal | Relationship counts as text; card fully keyboard-navigable |
| VerificationQueueItem | A claim awaiting verification with evidence state | open, in-research, proposal-ready, resolved | Status conveyed in text; actions reachable in order |
| SearchResult | Unified result row with type, tier, provenance, snippet | default, focused | Snippet highlights marked up semantically, not color-only |
| RevisionHistory | Item revision list with restore | default, comparing | Diff view offers a textual change summary |
| EmptyState | Teaching empty state with one primary action | default | Heading plus action; no decorative-only content |
| Toast and InlineAlert | Feedback per the semantic roles | info, success, warning, danger | Announced politely; danger interrupts |

Component contracts (props, events, keyboard maps) are specified at implementation time but every component above must ship with all listed states and its accessibility notes satisfied before use.

### 4.3 Motion

Subtle and purposeful: state transitions under 200 ms, streaming text without bounce or shimmer, no parallax, no autoplaying motion. All motion respects the reduced-motion preference with a no-motion equivalent (see [ACCESSIBILITY](ACCESSIBILITY.md)).

### 4.4 Voice in UI copy

Direct, warm, unhurried, consistent with the owner's documented builder-narrative tone (🟡, MASTER_CONTEXT §2). No em dashes in any UI string (the owner's documented style rule applies to product copy). Sentence case throughout. System messages state facts and next steps, never blame. Faith-related content (prayer reflection labels) is worded respectfully and neutrally; the El Roi signature is owner content, never system chrome (per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) policy).

### 4.5 Theming

Light and dark themes ship at v1 from the same semantic tokens; theme choice persists per user. The portfolio defaults to the visitor's system preference. A future white-label variant for Linfy Tech Solutions reuse is a noted possibility (🟡 company context), designed for only insofar as the token architecture already permits it.

## 5. Acceptance Criteria

- Token architecture implemented in three layers; a theme switch touches only primitive bindings (verified by changing themes with zero component edits).
- Every component in §4.2 ships with all listed states, keyboard support, and its accessibility notes verified in component tests.
- ConfidenceBadge and PrivacyTierIndicator appear in every context where claims or tiered content render, verified by the NFR-039 audit.
- Contrast checks pass for all role pairs in both themes (automated in CI per [CI_CD](../deployment/CI_CD.md)).
- No UI string in the string catalog contains an em dash (automated lint rule).

## 6. Dependencies

- [ACCESSIBILITY](ACCESSIBILITY.md): contrast floors, live-region patterns, keyboard contracts.
- [UI_UX](UI_UX.md): the screens and patterns these components compose into.
- Owner brand decisions (palette, typeface, logo): the TODO in §4.1.

## 7. Risks

- Placeholder aesthetics hardening into de facto brand; mitigated by the explicit TODO and a Phase 2 brand decision checkpoint in [ROADMAP](../roadmap/ROADMAP.md).
- Provenance badge fatigue; mitigated by compact-by-default styling and expansion on demand rather than visual shouting.
- Component drift between surfaces; mitigated by a single library with surface-scoped composition and visual regression tests.

## 8. Future Enhancements

- White-label theming for Linfy Tech reuse (noted above, not committed).
- High-contrast theme beyond AA as a user option.
- Print stylesheets for journals and vault-adjacent reading.

## 9. Examples

A search result for "RhinoGuardians" renders: type icon (Project), title, snippet, a "Self-reported" ConfidenceBadge, and a "Private P2" PrivacyTierIndicator. The same entity in the public portfolio simply does not exist. In dark mode, both badges pass contrast automatically because only primitives changed. A screen reader announces the row as: "Project, RhinoGuardians, confidence: self-reported, privacy: private."

## 10. Open Questions

- Brand palette, typeface, logo, and iconography set (§4.1 TODO): owner decisions pending.
- Should the portfolio get a distinct typographic personality from the workspace, or stay unified? Prototype during Phase 5.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §2 (style identifiers, 🟡; the no-em-dash rule; tone).
- WCAG 2.2 contrast requirements; design token community group format (W3C draft) as a structural reference.

## 12. Related Specifications

- [UI_UX](UI_UX.md), [ACCESSIBILITY](ACCESSIBILITY.md)
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) (disclosure and signature policy), [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md)
- [CI_CD](../deployment/CI_CD.md) (automated checks), [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) (NFR-039, NFR-043)
