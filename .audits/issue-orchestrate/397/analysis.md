---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "397"
classification: "feature-request"
secondary-classes: []
route: "direct"
status: approved
created: "2026-07-09"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #397 — Species list: add origin provenance filter (UI-NFR-018 R-016/017)
- **URL**: https://github.com/nolte/kamerplanter/issues/397
- **Labels**: enhancement
- **Linked items**: split out of #367; no PR resolves it (only unrelated deps PR #135 references the number)
- **Prior art checked**: `SpeciesListPage.tsx` already renders the origin column via `OriginChip` + `resolveOrigin`, and has a mature filter system (`ToggleFilter` set, `growthHabitFilter`, `familyFilter`, `filteredItems`) — but **no** origin filter. No `project/features/` entry, no `project/roadmap.md` item, no open PR addresses it. Requirement artefact authored this run: `project/requirements/species-origin-filter.md` (`U_gate = 0.85`).

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: none
- **Rationale**: Adds a new user-facing UI capability (origin filter) to an existing list; no defect, spec change, or security surface.

## Scope

- **In scope**: A multi-select origin chip filter on the species list (`SpeciesListPage.tsx`), OR-combined within origin and AND-composed with existing filters, URL-persistent, reusing `OriginChip` labels/colours and existing `common.origin.*` i18n keys. Per UI-NFR-018 R-016/017/018 + UI-NFR-010 R-010/R-016/R-017/R-031.
- **Out of scope**: Backend/API changes (origin already on the read model); any other list (cultivars, diseases, treatments, nutrient plans, workflow templates); new i18n keys; `OriginChip` rendering changes. No conditional-hide of the filter.

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome, a single PR strand, frontend-only, no new or retargeted roadmap item → direct implementation (operator-confirmed).
- **Pipeline hand-off**: n/a

## Work packages

### P1 — Species-list origin provenance filter

- **Problem statement**: The species list shows each row's origin but cannot be filtered by it. Add a multi-select chip filter for the four origins (system / enrichment / import / tenant), wired into the existing list filtering.
- **Acceptance criteria**:
  - A "Herkunft" filter control offers all four origins with the existing `common.origin.*` labels and `OriginChip` colours (R1, R5).
  - Selecting one or more origins narrows the list to rows whose resolved origin is one of the selected (OR within origin); no selection = all rows (R2, R3).
  - The origin filter is AND-composed with family, growth-habit, and toggle filters (R4).
  - The filter state is reflected in the URL query params and restored on load (R6).
  - The origin filter counts toward the active-filter badge, is cleared by "Alle Filter zurücksetzen", and a zero-row result shows the specific empty-filter hint (R7).
  - `tenant` ("Eigene"/"Custom") is selectable even though `OriginChip` renders nothing for tenant rows (R8).
  - Vitest coverage for the new filtering logic (OR-within / AND-across, empty-result, URL round-trip); `tsc` + ESLint clean.
- **Touched files / artifacts**: `src/frontend/src/pages/stammdaten/SpeciesListPage.tsx` (filter state, `filteredItems`, `filterChips`/panel, URL sync); reference `src/frontend/src/components/common/OriginChip.tsx` and `src/hooks/useOriginProtection` (`resolveOrigin`); species list test under `src/frontend/src/pages/stammdaten/__tests__/` (or existing test file); `common.origin.*` i18n already present (add only an "all"/reset affordance if missing).
- **Specialist**: `fullstack-developer`
- **Depends on**: none

## Dependency ordering

P1 (single package, no dependencies).

## Risks

- **Custom-hook stability**: any object/array returned by a new hook or memo must be `useMemo`-stabilised (project convention) — mitigate by extending the existing `filteredItems` useMemo rather than adding a new unstabilised hook.
- **URL param naming collision**: pick an `origin` query key that does not clash with the existing `family` param; keep the family filter's `searchParams` pattern.
- **tenant option vs OriginChip null-render**: the filter must label `tenant` ("Eigene"/"Custom") even though the chip hides it — verified in R8; ensure the filter option list is built independently of the chip's render guard.
- Security: none — no security-sensitive path touched; `code-security-reviewer` / `security-review` not required for this diff.

## Open questions

None — select semantics resolved (multi-select OR, operator-confirmed); all other dimensions authoritatively fixed by UI-NFR-018/UI-NFR-010 and the existing frontend infrastructure.

## Dispatch log

2026-07-09 P1 dispatched to `fullstack-developer` — implemented origin filter in `SpeciesListPage.tsx` + 8 vitest cases; vitest 23 passed, tsc clean, eslint clean. No backend/i18n changes needed.
2026-07-09 P1 UI-review dispatched to `frontend-usability-optimizer` — mandatory post-frontend-change review (project convention).
