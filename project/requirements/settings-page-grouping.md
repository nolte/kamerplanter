# Requirements — Settings page grouping (#2935)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Interview conducted 2026-11-17 with the operator (German); artifact in English.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Regroup the settings page (`src/frontend/src/pages/auth/AccountSettingsPage.tsx`, 12–14 tabs in one scrollable bar) into a small number of grouped sections; every existing setting stays reachable; the page is split so each group owns its state.
- **For whom:** every signed-in user in light and full mode; operators (`canManageInstanceSettings`) and platform admins with their additional entries.
- **Out of scope:** new settings; changes to gate or permission logic; reworking the content of the individual forms; the weather fetch interval of #2934 (it moves into the new structure afterwards); redirects for old tab keys (dropped, Q5).
- _source_: Q1 "passt".

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8` (6 used)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (final teach-back Q6 confirmed, no positive-EVPI question left)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.9 | specification (resolved) | Q2 nav pattern, Q4 group table, Q6 teach-back |
| `non_functional` | yes | 0.8 | specification | mobile-first + no horizontal scroll from issue AC; Q6 teach-back |
| `constraints` | yes | 0.9 | specification (resolved) | Q3 operator placement, gates unchanged (Q1, Q6) |
| `domain_objects` | yes | 0.9 | interpretation | Q4 tab→group mapping confirmed |
| `actors` | yes | 0.9 | interpretation | Q1 bounded context, Q4 visibility column |
| `acceptance_criteria` | yes | 0.85 | specification | issue AC minus redirect AC (Q5); Q6 teach-back |
| `edge_cases` | yes | 0.8 | specification | Q5 unknown/forbidden key fallback, empty-group hiding (Q6) |
| `scope_boundaries` | yes | 0.9 | specification (resolved) | Q1, Q5 "no special cases for old links" |

Self-consistency (k=2) was applied on the navigation pattern (sidebar vs. top tabs diverged → Q2) and on the operator group placement (settings page vs. `/admin` diverged → Q3); both were resolved by decision questions.

## Requirements

- **R1** — WHEN the settings page is rendered on desktop, the frontend SHALL show the groups in a vertical side navigation (expandable to their sections) with the content on the right, all entries visible without horizontal scrolling.
  - _dimension_: `functional`, `non_functional` · _status_: `confirmed` · _source_: Q2 "passt" (option B), Q6 "ja"
- **R2** — WHEN the settings page is rendered on a mobile viewport, the frontend SHALL show a list of groups, and a tap on a group SHALL open that group as a detail view with a back arrow.
  - _dimension_: `functional`, `non_functional` · _status_: `confirmed` · _source_: Q2, Q6
- **R3** — The settings page SHALL group today's tabs as follows: Profile & account (`profile`, `account`); Display & behaviour (`experience`, `kiosk`, `modules`, `dashboard`); Notifications (`notifications`, standalone group); Security & access (`security`, `sessions`, `apikeys`, `connect`); Integrations (`ha`, `ha-publish`); Installation (`storage`, `weather-providers`).
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: Q4 "ja passt"
- **R4** — WHILE the user has `canManageInstanceSettings`, the side navigation SHALL show the Installation group visually separated (divider + heading) from the personal groups; otherwise it SHALL not be shown.
  - _dimension_: `constraints`, `actors` · _status_: `confirmed` · _source_: Q3 "C", Q4, Q6
- **R5** — The `platform` settings SHALL move from the settings page to a new hub page `/admin/platform`, reachable from a side-navigation entry visible only to platform admins and gated as today; the admin pages' back links and breadcrumbs SHALL point to it, and the platform-admin-only `PestContributionsAdminCard` SHALL move there as well.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Q3 "C"; revisit 2026-11-17 decisions 4+5 "ok passt"
- **R6** — Within a group, the former tabs SHALL be rendered as sections (cards) one below the other; the content of the individual forms SHALL stay unchanged.
  - _dimension_: `functional`, `scope_boundaries` · _status_: `confirmed` · _source_: Q2 option B, Q1, Q6
- **R7** — The settings page SHALL be addressable as `/settings/<group>` and `/settings/<group>#<section>`; on mobile a section link SHALL open the group detail view scrolled to the section.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q5 "passt"
- **R8** — WHEN the URL path names an unknown group, the frontend SHALL show the 404 page (UI-NFR-005 R-018). WHEN it names a known group that is not visible to the user in the current mode or role, the frontend SHALL show the first visible group. WHEN the `#<section>` fragment is unknown, the frontend SHALL show the top of the group. No mapping or redirect for the old tab keys SHALL be built; the R-004 (301) exception for these hash fragments SHALL be recorded in UI-NFR-005.
  - _dimension_: `edge_cases`, `scope_boundaries` · _status_: `confirmed` · _source_: Q5 "du brauchst aber keine sonderlocken für alte links einbauen", Q6; revisit 2026-11-17 decisions 1+2 "ok passt"
- **R9** — The existing visibility gates (light vs. full mode, `isSmartHomeEnabled`, `canManageInstanceSettings`, platform admin) SHALL apply unchanged per section; a group with no visible section SHALL be hidden.
  - _dimension_: `constraints`, `edge_cases` · _status_: `confirmed` · _source_: Q1, Q6
- **R10** — Every existing setting SHALL remain reachable exactly once; none is removed or duplicated.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: issue AC, Q6
- **R11** — `AccountSettingsPage.tsx` SHALL be split so that each group is its own component owning its state and handlers.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: issue AC, Q6
- **R12** — The change SHALL ship with i18n (DE + EN), new test ids `settings-group-<group>` and `settings-section-<section>` (E2E tests migrated; old `settings-tab-<key>` ids not kept as aliases) and updated user documentation.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Q5, Q6
- **R13** — #2934 (weather fetch interval) SHALL build on this structure and place its setting in the Installation group.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q6
- **R14** — The dashboard section SHALL be shown in light and full mode (fixes the full-mode dead link `DashboardPage.tsx:258,344` → `/settings#dashboard`; REQ-045 has no mode restriction).
  - _dimension_: `functional`, `edge_cases` · _status_: `confirmed` · _source_: revisit 2026-11-17 decision 3 "ok passt"
- **R15** — The instance-wide cards of today's `ha` tab (HA connection, Pl@ntNet, plant/pest recognition; gated `canManageInstanceSettings`) SHALL be placed in the Installation group; the Integrations group keeps the per-user/per-tenant parts.
  - _dimension_: `domain_objects`, `constraints` · _status_: `confirmed` · _source_: revisit 2026-11-17 decision 4 "ok passt"
- **R16** — The platform move (R5) SHALL be delivered before the grouping (R1–R4), so the grouping is built without the `platform` tab.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: revisit 2026-11-17 decision 6 "ok passt"

## Surviving assumptions / open risks

- **Dropped issue AC:** "Existing tab URLs keep working (redirect to the new location)" is removed by operator decision (Q5); old bookmarks land on the first visible group (R8). The issue must be updated accordingly.
- **Internal links:** in-app links and notification deep links that use today's `#<key>` hash keys (`useTabUrl.ts:22`) must be migrated to the new scheme in the same change — otherwise they silently fall back (R8). Not a redirect, a call-site update. `assumed`.
- **Revisit 2026-11-17:** the consistency check of F-11/F-12 found UI-NFR-005 R-018/R-004 conflicts, the full-mode dashboard defect, the instance-wide `ha` cards and the missing admin navigation; the operator accepted all six recommendations (R5, R8 revised; R14–R16 added).
- **Desktop/mobile breakpoint** follows the existing MUI breakpoint used for the app's drawer. `assumed`.
