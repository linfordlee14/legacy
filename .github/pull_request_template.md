<!--
Legacy is specification-driven. A PR that cites no spec sections will be asked to.
Read roadmap/BUILD_ORDER.md section 4.1 (session protocol) before opening your first PR.
Never include P2/P3 content, secrets, or real personal data in diffs, fixtures, or screenshots.
-->

## Summary

<!-- One to three sentences: what this PR does and why now. -->

## Task and milestone

- Task: <!-- MVP-### or TASK-### -->
- Closes: <!-- #issue -->
- Milestone: <!-- M1 to M9 per roadmap/GITHUB_MILESTONES.md -->
- Build-order step: <!-- per roadmap/BUILD_ORDER.md section 4.2, if applicable -->

## Specification sections implemented

<!-- The sections that define this change. This list is mandatory (spec-first rule,
     testing/QUALITY_ASSURANCE.md). If implementation deviated from a spec, the spec
     update must be in this PR or already merged, with a CHANGELOG entry. -->

-

## Verification

- [ ] Acceptance criteria of the task pass in CI
- [ ] New or changed behavior is covered by tests (unit, contract, or e2e as the task defines)
- [ ] Privacy-tier enforcement tested where touched: no above-ceiling read, list, count, or export (NFR-035); `not_found` shape preserved
- [ ] Provenance preserved where touched: no tier upgraded, citations and provenance blocks present (NFR-037, NFR-038)
- [ ] Audit entries written for new mutations and denials (NFR-030)
- [ ] Logs remain content-free: entity IDs only, redaction test green (NFR-033)
- [ ] Accessibility gate green; new UI keyboard-complete with text-labeled badges (NFR-041 to NFR-043)
- [ ] No em dashes in UI strings or repository documents (owner style rule)
- [ ] Spec changes (if any) updated the document first and include a CHANGELOG entry
- [ ] No P2/P3 content, secrets, or real personal data anywhere in this PR

## Deviations and notes

<!-- "None" or: what differed from the plan, decisions escalated to the owner,
     any TODO(verify) items created, and anything for the Gate evidence log. -->
