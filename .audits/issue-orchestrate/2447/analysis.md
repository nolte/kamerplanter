# Pre-analysis: #2447 garden-plan documentation (transient, removed before merge)

Class: docs. Source: issue #2447 (REQ-053 WP 6.3, "Depends on: waves 1-5 merged" — met; waves 6-7 are also merged). Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: the issue (What / Acceptance) is the decision record.

## Scope (issue text)
MkDocs DE/EN per spec/style-guides/DOCS.md (DE canonical, informal "du", REQ-ID visibility rule, admonitions `!!! warning "Noch nicht implementiert"`, end-user vs technical audience separation, generated fact tables):
1. User guide "Gartenplan": drawing, gestures, field mode, site conditions, plant-state legend, export/import (and what waves 6-7 added: zones/watering round, templates, underlay, layers, snapshots, partial export, new season if merged — measure what is actually merged).
2. Technical page: geometry model and batch contract.
3. REQ-032 section 2.5 reference.
4. Release-notes section.
5. Check what earlier waves already added under `docs/` (user-guide/locations-substrates.md, reference/api-reference.md, changelog/unreleased.md, ...) and CONSOLIDATE instead of duplicating; mkdocs.yml nav.

## Acceptance
`mkdocs build --strict` green (with the generated catalog: `task docs:build` regenerates it; in a worktree the git-revision-date plugin warns on generated catalog pages — those are not caused by the change), Vale clean (Vale cannot run locally: vocabulary not synced; follow shipped-vocabulary wording rules in spec/style-guides/DOCS.md and say so), `docs-freshness-checker` without critical finding (DE/EN parity, dead links, stale references).

## Rules for the specialist
- Every statement of behaviour, endpoint, limit or role must be MEASURED against the code or spec (routes via the router files, limits via constants, roles via require_* decorators, UI via the components and i18n texts); do not copy from the plan. Where a feature is specified but not implemented (check each against develop), use the `!!! warning "Noch nicht implementiert"` admonition, never describe it as working.
- No REQ-IDs in end-user text beyond what DOCS.md allows (hidden HTML comment form).
- Do not raise budgets, no prod deploy talk (E-07): prod release P-4 stays with the operator.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | inventory of existing docs + user guide page DE/EN (consolidate) | mkdocs-documentation |
| P2 | technical page (geometry model, batch contract, import/export contract) DE/EN + REQ-032 2.5 reference | mkdocs-documentation |
| P3 | release-notes section, nav, links, strict build, freshness check | mkdocs-documentation |
Review after: docs-freshness-checker (read-only) and a fact-check pass by a code-reading reviewer.
