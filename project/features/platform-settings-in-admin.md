---
id: F-12
title: Plattform-Einstellungen im Admin-Bereich
status: done
roadmap_item: R-17
sprint: 3
created: 2026-11-17
ended: 2026-11-23
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@03ccf46ca
  findings:
    - kind: overlap
      target: F-11
      resolution: proceed
      evidence: "Both change AccountSettingsPage.tsx:253/:1726 (platform tab) and the /settings#platform back links (AdminEditTenantPage.tsx:258,348; AdminEditUserPage.tsx:229,309; AdminOidcProvidersPage.tsx:216; AdminPlansPage.tsx:179; AdminTenantImportsPage.tsx:365,637)."
    - kind: drift
      target: src/frontend/src/layouts/Sidebar.tsx
      resolution: proceed
      evidence: "No admin entry in Sidebar.tsx; AppRoutes.tsx:331-386 has five leaf routes without an /admin index; the platform tab itself is the only hub (AccountSettingsPage.tsx:1850,1872,1895,1958,2042)."
    - kind: drift
      target: src/frontend/src/pages/auth/AccountSettingsPage.tsx:1726
      resolution: proceed
      evidence: "The platform tab holds mode cards (:1729-1812), statistics, tenant/user tables and launchers (:1815+); no admin write call in the page code — 'same save behaviour' was not testable."
    - kind: drift
      target: src/frontend/src/pages/auth/AccountSettingsPage.tsx:1721
      resolution: proceed
      evidence: "PestContributionsAdminCard is platform-admin-only but lives in the ha tab, not the platform tab."
    - kind: prior-art
      target: src/frontend/src/routes/roleGuardedRoutes.ts:318
      resolution: proceed
      evidence: "PLATFORM_ADMIN_ROUTES + platformAdminRouteGuards.test.tsx:61,70 enforce registration of every RequirePlatformAdmin route; doc paragraph :273-287 describes the platform tab as page-gated; AccountSettingsPlatformTabGating.test.tsx:51-53 counts admin reads."
    - kind: prior-art
      target: docs/de/user-guide/admin.md:10
      resolution: proceed
      evidence: "admin.md:10 already names /admin/platform (no such route exists); admin.md:55 points to 'Einstellungen > Plattform-Modus'."
---

## Description

Plattform-Administratoren finden die Plattform-Verwaltung heute als Tab
„Plattform“ auf der persönlichen Einstellungsseite, zwischen Profil und
API-Keys. Dieser Tab ist zugleich der einzige Einstieg zu den Admin-Seiten
(Mandanten, Nutzer, OIDC-Provider, Pläne, Mandanten-Importe).

Nach dieser Änderung hat die Plattform-Verwaltung eine eigene Seite
`/admin/platform`, die Plattform-Admins über einen eigenen Eintrag in der
Seitennavigation erreichen. Sie zeigt dieselben Inhalte wie der bisherige Tab
(Betriebsmodus, Statistik, Mandanten- und Nutzertabellen, Einstiege zu den
Admin-Seiten) plus die bisher im HA-Tab versteckte Karte für
Schädlings-Beiträge. Alle Admin-Seiten führen per Zurück-Link und Breadcrumb
auf diese Seite zurück; die Einstellungsseite enthält keine
Plattform-Inhalte mehr.

## Acceptance criteria

- [x] **acceptance-1** Ein Plattform-Admin erreicht die Plattform-Verwaltung über einen Seitennavigations-Eintrag unter `/admin/platform`; Zurück-Links und Breadcrumbs aller Admin-Seiten führen dorthin.
- [x] **acceptance-2** Wer kein Plattform-Admin ist, sieht weder den Navigationseintrag noch erreicht er `/admin/platform` (gleiches Gate wie heute).
- [x] **acceptance-3** Die Einstellungsseite zeigt weder den Plattform-Tab noch die Schädlings-Beitrags-Karte; beide liegen auf `/admin/platform`.
- [x] **acceptance-4** `/admin/platform` zeigt dieselben Inhalte und lädt dieselben Daten wie der bisherige Tab; für Nicht-Admins werden keine Admin-Daten abgefragt.
- [x] **acceptance-5** Beschriftungen (DE + EN) und die Nutzerdoku (`admin.md` DE + EN) beschreiben den neuen Ort.

## Test hooks

- **acceptance-1** — `src/frontend/src/test/` route test for `/admin/platform` + sidebar entry; E2E `tests/e2e/` admin navigation — passing — `AdminPlatformPage.test.tsx`, `layouts/Sidebar.test.tsx` (sidebar entry), `routes/breadcrumbs.test.ts`, `AdminBackLinksToHub.test.tsx`; E2E `test_req024_platform_admin_hub.py` — e2e-nightly run 45173235993 (profile=all, develop e074bde9a): green in tablet, mobile, full-tablet, light, full-mobile, full for this feature's tests (#3102)
- **acceptance-2** — `platformAdminRouteGuards.test.tsx` (route registered in `PLATFORM_ADMIN_ROUTES`) — passing — `platformAdminRouteGuards.test.tsx` (`registers the platform admin hub /admin/platform behind the guard`) + `AdminPlatformPageGating.test.tsx` (`refuses a non-admin at the route guard and reads nothing`) (#3102)
- **acceptance-3** — vitest on the settings page: no platform section / pest-contribution card rendered — passing — `AdminPlatformPageGating.test.tsx` (`shows a platform admin no pest-contribution card in the installation group`, no admin probe from the settings page) + `AdminPlatformPage.test.tsx` (pest card now on the hub) (#3102, #3107)
- **acceptance-4** — `AccountSettingsPlatformTabGating.test.tsx` migrated to the hub page (admin request count for non-admins = 0) — passing — `AdminPlatformPageGating.test.tsx` (`loads the three admin reads once for a platform admin`, `reads no admin endpoint for a member who is not a platform admin`) — the former `AccountSettingsPlatformTabGating.test.tsx` migrated there (#3102)
- **acceptance-5** — i18n completeness check + `mkdocs build --strict` — passing — `i18n/adminPlatform.test.ts` (DE/EN parity, removed tab label dropped); `admin.md` DE+EN updated in #3102; `mkdocs build --strict` on develop e074bde9a (2026-11-23): no link or nav warning — its only 45 warnings are the git-revision-date plugin on the locally generated, git-ignored catalog pages (docs/*/skills, agents, tags)

## Consistency notes

**Overlap with F-11 (proceed).** Established: both features touch
`AccountSettingsPage.tsx:253/:1726` and the `/settings#platform` back links in
the five admin pages (`AdminEditTenantPage.tsx:258,348`,
`AdminEditUserPage.tsx:229,309`, `AdminOidcProvidersPage.tsx:216`,
`AdminPlansPage.tsx:179`, `AdminTenantImportsPage.tsx:365,637`). Rationale for
`proceed` instead of `merge-into F-11`: F-12 has its own gate, route registry
and documentation scope, and F-11 already carries seven criteria. Operator
decision 2026-11-17: **F-12 is delivered first** and owns the hub page, the
admin back links and the breadcrumb parents (`breadcrumbs.ts:90-94`); F-11
then builds the groups without the platform tab.

**Missing admin navigation (drift, proceed).** Established: `Sidebar.tsx` has
no admin entry and `AppRoutes.tsx:331-386` has no `/admin` index. Operator
decision 2026-11-17: F-12 builds the hub `/admin/platform` and a
platform-admin-only sidebar entry; the path makes `docs/de/user-guide/admin.md:10`
true.

**No save behaviour on the platform tab (drift, proceed).** Established: the
tab (`AccountSettingsPage.tsx:1726-2042`) only reads and links. Criterion 4 was
rephrased to same content, same loads, no admin reads for non-admins.

**PestContributionsAdminCard (drift, proceed).** Established: the card sits in
the ha tab (`AccountSettingsPage.tsx:1721`) but is platform-admin-only.
Operator decision 2026-11-17: it moves to `/admin/platform` (criterion 3).

**Gate prior art (proceed).** Established: `PLATFORM_ADMIN_ROUTES`
(`roleGuardedRoutes.ts:318`) with `platformAdminRouteGuards.test.tsx:61,70`
enforces registration; the doc paragraph `roleGuardedRoutes.ts:273-287` and the
request-count test `AccountSettingsPlatformTabGating.test.tsx:51-53` move with
the page.

**Docs prior art (proceed).** Established: `admin.md:10` already names
`/admin/platform`; `admin.md:55` points to the old settings location and is
updated (criterion 5).

## Risks

- Platform admins with bookmarks on `/settings#platform` land on the first settings group (no redirect, operator decision Q5).
- The step-up re-auth return compares only the pathname (`useStepUpReauth.ts:80`); unestablished whether it works for `/admin/platform` — verify in the implementation.

## References

- Issue #2935, roadmap item R-17
- `project/requirements/settings-page-grouping.md` (R5, R16)
