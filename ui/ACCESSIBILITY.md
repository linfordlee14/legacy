# ACCESSIBILITY
### Accessibility requirements and conformance program for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [UI_UX](UI_UX.md), [DESIGN_SYSTEM](DESIGN_SYSTEM.md), [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) |

---

## 1. Purpose

Legacy is built to be read for decades by people whose abilities, tools, and contexts cannot be predicted today: family members, collaborators, future researchers, and the owner himself across a lifetime. This document specifies the platform's accessibility requirements, the per-surface obligations, and the testing program that keeps conformance real rather than claimed. The platform principle "Accessible" in [LEGACY_PRINCIPLES](../docs/LEGACY_PRINCIPLES.md) is implemented here.

## 2. Goals

- WCAG 2.2 Level AA conformance across both surfaces (NFR-041), as a floor, not a ceiling.
- Full keyboard operability for every workflow (NFR-042).
- Provenance and privacy semantics perceivable by everyone: never color, emoji, or position alone (NFR-043).
- Media accessibility for a corpus full of talks, photos, and videos.

## 3. Scope

**In scope:** conformance target, per-surface and per-component requirements, keyboard support, screen reader behavior, media accessibility, cognitive accessibility, testing regimen, and the public accessibility statement.

**Out of scope:** visual design token values (see [DESIGN_SYSTEM](DESIGN_SYSTEM.md)); non-UI accessibility of exported vault files (covered by the open-format rules in [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)).

## 4. Requirements

### 4.1 Conformance target

WCAG 2.2 Level AA for the Private Workspace and the Public Portfolio. Where the platform's mission raises the bar (provenance clarity, long-form reading), requirements below exceed AA deliberately.

### 4.2 Perceivable

- Text alternatives: every image ingested requires alt text at capture time (an FR-ING behavior); decorative UI images are marked decorative; entity photos carry human-written descriptions.
- Media: talks and videos require captions; transcripts are produced by the ingestion transcription pipeline and attached to the artifact; audio-only content gets transcripts. Auto-generated transcripts are labeled as such until human-reviewed.
- Contrast: text at 4.5:1 minimum (3:1 for large text); interactive and state indicators at 3:1 against adjacent colors; provenance and tier colors meet the same floors in both themes and always pair with text labels.
- Reflow: all content usable at 320 px width and 400 percent zoom; wide content (tables, timeline, graph) scrolls within its own region, never the page.

### 4.3 Operable

- Keyboard: every workflow completable by keyboard alone, including capture, tier changes, sealing, approvals, verification resolution, and chat. No keyboard traps; a visible skip-to-content link; focus order follows reading order.
- Focus visibility: a high-visibility focus indicator meeting WCAG 2.2 focus-appearance guidance on every interactive element.
- Shortcuts: single-key shortcuts (`c` capture, `/` search) are remappable and disableable; they never fire while typing in inputs.
- Target size: minimum 24 by 24 CSS pixels for all targets (44 for primary mobile-web actions).
- Timing: no time limits on content interactions; approval expirations are measured in days and warned well in advance.
- Motion: all animation respects `prefers-reduced-motion` with functional no-motion equivalents; nothing flashes above threshold.

### 4.4 Understandable and robust

- Language attributes set at page and, where content differs, element level; multilingual content marked up correctly.
- Plain-language summaries accompany dense surfaces (verification queue explains what a tier decision means; succession settings explain consequences in plain terms).
- Consistent navigation and component behavior across surfaces; identical components behave identically.
- Errors identify the field, the problem, and the fix in text; destructive confirmations are described, not just styled.
- Semantic HTML first; ARIA only where semantics fall short; all components in [DESIGN_SYSTEM](DESIGN_SYSTEM.md) §4.2 ship with their accessibility contracts verified.

### 4.5 Signature component behavior

| Component | Requirement |
|-----------|-------------|
| ConfidenceBadge | Announced as "confidence: verified / self-reported / flagged"; the MASTER_CONTEXT emoji tiers (✅🟡🔴) never appear without their text labels |
| CitationChip | In tab order; expands via disclosure pattern; expanded content is a described region linking source and tier |
| StreamingAnswerPanel | Progressive text lands in a polite live region in sentence-sized chunks (never token-by-token announcements); completion and error announced assertively; stop control always focusable |
| Timeline Explorer | The canvas visualization is enhancement only; a keyboard-navigable, screen-reader-complete list view is the primary equivalent with identical data |
| Graph Explorer | Same rule: the list/table neighborhood view is primary; canvas is enhancement; every relationship readable as text |
| SealedContentPlaceholder | Announces sealed status and release summary without leaking content hints |
| TierSelector | Audience consequences read out in the confirmation dialog before commit |
| Twin chat disclosure | The AI-representation disclosure is a landmark read before first message on every visit, not a one-time toast |

### 4.6 Cognitive accessibility

Calm defaults (no autoplaying anything, no unexpected context changes), one primary action per screen region, progressive disclosure for advanced controls, consistent iconography with labels, and readable typography defaults for long-form content (line length, spacing per [DESIGN_SYSTEM](DESIGN_SYSTEM.md)).

### 4.7 Testing regimen

| Check | Cadence | Gate |
|-------|---------|------|
| Automated checks (axe-class) on all screens and states | Every CI run | Blocking per [CI_CD](../deployment/CI_CD.md) |
| Keyboard-only walkthrough of core journeys | Every release | Blocking |
| Screen reader passes (at least one desktop reader plus one mobile) | Quarterly and before major releases | Blocking on signature components |
| Contrast audit across both themes | On token changes | Blocking |
| Manual WCAG 2.2 AA audit | Yearly, plus before the portfolio's public launch | Findings triaged to the defect ladder in [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) |
| Assistive tech matrix review (browsers, readers, magnifiers) | Yearly | Documented |

### 4.8 Accessibility statement

The Public Portfolio publishes an accessibility statement: conformance status, known gaps with remediation intent, contact for issues, and the date of the last audit. Known gaps live in a tracked list; each carries an owner decision (fix, mitigate, or accept with rationale), reviewed quarterly.

## 5. Acceptance Criteria

- Automated accessibility checks run in CI and block merges on new violations (zero-regression policy).
- Every core journey in [USE_CASES](../specs/USE_CASES.md) passes a keyboard-only walkthrough.
- Signature component behaviors in §4.5 verified with at least two screen readers before Phase 5 exit.
- The yearly manual audit exists, is dated, and its findings are triaged.
- The portfolio ships with its accessibility statement from day one of public availability.

## 6. Dependencies

- [DESIGN_SYSTEM](DESIGN_SYSTEM.md): component contracts that carry these requirements.
- [UI_UX](UI_UX.md): screens and journeys under test.
- Ingestion pipeline (FR-ING group): alt text capture and transcription that media accessibility depends on.
- [CI_CD](../deployment/CI_CD.md) and [TESTING](../testing/TESTING.md): where the gates run.

## 7. Risks

- Canvas-heavy explorers (timeline, graph) drifting into inaccessible primaries; the list-first rule in §4.5 is the control, enforced by review.
- Auto-generated transcripts shipping unlabeled or unreviewed; mitigated by the labeling requirement and review queue.
- Solo-founder audits slipping; mitigated by CI automation carrying the routine load and calendar-forced yearly audits.
- AI streaming interfaces are a young accessibility area; mitigated by conservative live-region patterns and quarterly reader testing.

## 8. Future Enhancements

- AAA targets for long-form reading surfaces (journals, articles).
- User-adjustable reading preferences (spacing, width, font) beyond themes.
- Voice-driven operation pairing with the future voice interface (see [FUTURE_FEATURES](../roadmap/FUTURE_FEATURES.md)).

## 9. Examples

A screen-reader user asks the public twin about verified projects. The disclosure landmark reads first: "You are chatting with an AI representation of Linford Musiyambodza." The answer streams into a polite live region sentence by sentence; each citation announces as "citation: GDG Cape Town event page, confidence: verified." Tabbing moves through citation chips in order; expanding one reads the source details. Switching to the timeline, the user lands in the list view: "June 2026: presented CyberBuddy at GDG Cape Town Pet Projects, confidence: verified, privacy: public."

## 10. Open Questions

- Which exact screen reader and browser combinations form the support matrix? Propose at Phase 1 exit based on real usage context.
- Should transcript human-review be blocking before a talk publishes to P0, or label-and-improve? Current answer: blocking for P0, label-and-improve for private content; confirm with the owner.

## 11. References

- WCAG 2.2 (W3C Recommendation), WAI-ARIA Authoring Practices Guide.
- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §0 (the tier vocabulary these announcements carry).

## 12. Related Specifications

- [UI_UX](UI_UX.md), [DESIGN_SYSTEM](DESIGN_SYSTEM.md)
- [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) (NFR-041 through NFR-043), [TESTING](../testing/TESTING.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)
- [CI_CD](../deployment/CI_CD.md), [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) (FR-UI and FR-ING groups)
