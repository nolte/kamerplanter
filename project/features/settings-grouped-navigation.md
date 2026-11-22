---
id: F-11
title: Gruppierte Einstellungsnavigation
status: ready
roadmap_item: R-17
sprint: 3
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@03ccf46ca
  findings:
    - kind: drift
      target: spec/ui-nfr/UI-NFR-005_Navigation.md:55
      resolution: proceed
      evidence: "R-004 (MUSS) demands 301 redirects on URL changes; old tab keys are hash fragments (useTabUrl.ts:23) — a server 301 is impossible; the operator dropped client-side mapping (Q5)."
    - kind: drift
      target: spec/ui-nfr/UI-NFR-005_Navigation.md:108
      resolution: proceed
      evidence: "R-018 (MUSS) demands a 404 page for invalid URLs; resolved by operator decision 2026-11-17: unknown group path -> 404, invisible known group -> first visible group, unknown #section -> top of group."
    - kind: drift
      target: src/frontend/src/pages/auth/AccountSettingsPage.tsx:237
      resolution: proceed
      evidence: "Full-mode tab set (:237-255) lacks 'dashboard' while DashboardPage.tsx:258,344 links /settings#dashboard in both modes and REQ-045:407 has no mode restriction; operator decision: show the section in both modes."
    - kind: drift
      target: src/frontend/src/pages/auth/AccountSettingsPage.tsx:1414
      resolution: proceed
      evidence: "The ha tab holds instance-wide cards (HA connection :1417, Pl@ntNet :1532, recognition/pest :1715-1716, canManageInstanceSettings); operator decision: they move to the Installation group."
    - kind: drift
      target: spec/req/REQ-045_Individualisierbares-Dashboard.md:407
      resolution: proceed
      evidence: "REQ-045:407/424/545/652 fix the deep link /settings#dashboard; REQ-042:274/294 'Tab Module & Funktionen'; REQ-023:1639 '/settings/account' — specs updated in the same change."
    - kind: overlap
      target: F-12
      resolution: proceed
      evidence: "Both touch AccountSettingsPage.tsx (platform tab :253/:1726) and the /settings#platform admin back links; F-12 goes first and owns them."
    - kind: prior-art
      target: src/frontend/src/hooks/useTabUrl.ts:22
      resolution: proceed
      evidence: "Deep links use the hash (#key); an unknown hash already falls back to index 0 (:24-26) — reusable for the section fallback."
    - kind: prior-art
      target: src/frontend/src/components/common/ModuleGuard.tsx:55
      resolution: proceed
      evidence: "In-app link inventory: ModuleGuard.tsx:55,62; ModulesSettingsTab.tsx:314; DashboardPage.tsx:258,344; Sidebar.tsx:594-595; breadcrumbs.ts:84; MainLayout.tsx:90,194; no backend/notification links to settings tabs."
    - kind: prior-art
      target: tests/e2e/pages/account_settings_page.py:21
      resolution: proceed
      evidence: "E2E selects tabs via '.MuiTab-root' + label (:21, :63-92), hash paths in notification_settings_page.py:43, connect_device_dialog_page.py:79, expertise_level_page.py:82; click_tab/open(tab=) 9x in test_req023_account_settings.py."
    - kind: prior-art
      target: docs/de/user-guide/account.md:130
      resolution: proceed
      evidence: "account.md describes the tabs; further settings references in dashboard.md, dashboard-personalization.md, notifications.md, module-visibility.md, kiosk-mode.md, weather-services.md, guides/home-assistant-integration.md, guides/browser-push-setup.md (DE+EN)."
---

## Description

Die Einstellungsseite besteht heute aus einer horizontal scrollenden Leiste mit
bis zu 14 Tabs. Die meisten Einträge sind nur durch Scrollen auffindbar, und
persönliche Einstellungen stehen gleichrangig neben Einstellungen, die die
ganze Installation betreffen.

Nach dieser Änderung gliedert eine Seitennavigation (Desktop) bzw. eine
Gruppenliste mit Detailansicht und Zurück-Pfeil (mobil) die Einstellungen in
Gruppen: Profil & Konto, Anzeige & Verhalten, Benachrichtigungen, Sicherheit &
Zugang, Integrationen und — mit Trennlinie abgesetzt und nur für Betreiber —
Installation (Speicher, Wetterquellen und die installationsweiten Karten wie
HA-Verbindung, Pl@ntNet und Erkennung). Innerhalb einer Gruppe stehen die
bisherigen Tabs als Abschnitte untereinander; die Formulare selbst bleiben
unverändert. Die Dashboard-Einstellungen erscheinen jetzt in beiden
Betriebsmodi.

Jede Gruppe ist unter `/settings/<gruppe>` und jeder Abschnitt unter
`/settings/<gruppe>#<abschnitt>` direkt verlinkbar. Alte Tab-Links werden nicht
umgeleitet; sie landen auf der ersten sichtbaren Gruppe.

## Acceptance criteria

- [ ] **acceptance-1** Auf dem Desktop sind alle Gruppen ohne horizontales Scrollen in einer Seitennavigation sichtbar; mobil öffnet ein Tipp auf eine Gruppe deren Detailansicht mit Zurück-Pfeil.
- [ ] **acceptance-2** Jede bisherige Einstellung ist genau einmal in ihrer zugeordneten Gruppe erreichbar; die Dashboard-Einstellungen sind in light- und full-Modus erreichbar.
- [ ] **acceptance-3** Die Sichtbarkeits-Gates (light/full, Smart-Home aktiv, Instanzverwaltung) gelten unverändert pro Abschnitt; die Gruppe „Installation“ ist sichtbar abgesetzt und nur für Betreiber sichtbar; Gruppen ohne sichtbaren Abschnitt werden ausgeblendet.
- [ ] **acceptance-4** `/settings/<gruppe>#<abschnitt>` öffnet Gruppe und Abschnitt; eine unbekannte Gruppe zeigt die 404-Seite, eine nicht sichtbare Gruppe die erste sichtbare Gruppe, ein unbekannter Abschnitt den Anfang der Gruppe.
- [ ] **acceptance-5** Jeder Link innerhalb der App, der auf eine Einstellung zeigt, führt an deren neuen Ort.
- [ ] **acceptance-6** Jede Gruppe ist eine eigene Komponente mit eigenem Zustand; keine einzelne Seitenkomponente hält den Zustand aller Gruppen.
- [ ] **acceptance-7** Beschriftungen (DE + EN) und die Nutzerdoku beschreiben die neue Struktur.

## Test hooks

- **acceptance-1** — vitest on the settings layout at desktop/mobile breakpoints + E2E `tests/e2e/pages/account_settings_page.py` (migrated to `settings-group-*`) — pending
- **acceptance-2** — vitest inventory test: every former tab's section rendered exactly once per mode — pending
- **acceptance-3** — vitest gate matrix (light/full × smart-home × canManageInstanceSettings) — pending
- **acceptance-4** — vitest routing tests for `/settings/<group>#<section>`, unknown group (404), invisible group, unknown section — pending
- **acceptance-5** — vitest/grep guard: no `/settings#<old-key>` link left in `src/frontend/src` — pending
- **acceptance-6** — code review of the split (`AccountSettingsPage.tsx` no longer holds per-group state) — pending
- **acceptance-7** — i18n completeness check + `mkdocs build --strict` — pending

## Consistency notes

**UI-NFR-005 R-004 (drift, proceed).** Established:
`spec/ui-nfr/UI-NFR-005_Navigation.md:55` requires 301 redirects when the URL
structure changes; the old tab keys are hash fragments (`useTabUrl.ts:23`), for
which a server-side 301 is technically impossible, and the operator rejected a
client-side mapping (Q5). The exception is recorded in UI-NFR-005 within the
implementing change.

**UI-NFR-005 R-018 (drift, proceed).** Established:
`UI-NFR-005_Navigation.md:108` requires a 404 page for invalid URLs. Operator
decision 2026-11-17: an unknown group path shows the 404 page; a known but
invisible group shows the first visible group; an unknown `#section` shows the
top of the group (criterion 4). This keeps R-018 for paths and the silent
fallback for fragments.

**Dashboard in full mode (drift, proceed).** Established: the full-mode tab
set (`AccountSettingsPage.tsx:237-255`) has no `dashboard` entry while
`DashboardPage.tsx:258,344` links `/settings#dashboard` in both modes and
`REQ-045:407` sets no mode restriction. Operator decision 2026-11-17: the
section is shown in both modes (criterion 2) — a pre-existing defect fixed
inline.

**Instance-wide ha cards (drift, proceed).** Established: the ha tab holds the
HA connection (`AccountSettingsPage.tsx:1417`), Pl@ntNet (`:1532`) and
recognition/pest cards (`:1715-1716`), all gated `canManageInstanceSettings`;
`roleGuardedRoutes.ts:273-276` calls them "the instance-wide half of the ha
tab". Operator decision 2026-11-17: they move to the Installation group; the
platform-admin-only pest-contribution card moves with F-12.

**Spec deep links (drift, proceed).** Established: `REQ-045:407/424/545/652`
fix `/settings#dashboard`, `REQ-042:274/294` name the tab "Module & Funktionen",
`REQ-023:1639` names `/settings/account`. These specs are updated in the same
change.

**Overlap with F-12 (proceed).** Established: both touch the platform tab
(`AccountSettingsPage.tsx:253/:1726`) and the `/settings#platform` admin back
links. Operator decision 2026-11-17: F-12 is delivered first and owns the hub,
the admin back links and the breadcrumb parents; F-11 builds the groups
without the platform tab. Not merged because F-12 has its own gate, registry
and documentation scope.

**Deep-link prior art (proceed).** Established: `useTabUrl.ts:22-26` drives the
tabs via the hash and already falls back to index 0 on an unknown key —
reusable for the section fallback.

**In-app link inventory (proceed).** Established: links to settings tabs sit
in `ModuleGuard.tsx:55,62`, `ModulesSettingsTab.tsx:314`,
`DashboardPage.tsx:258,344`, `Sidebar.tsx:594-595` (exact `pathname ===
'/settings'` comparison), `breadcrumbs.ts:84`, `MainLayout.tsx:90,194`; no
backend or notification payload links to a settings tab. This is the scope of
criterion 5.

**E2E prior art (proceed).** Established: the page objects select tabs by
`.MuiTab-root` + label (`account_settings_page.py:21,63-92`) and by hash path
(`notification_settings_page.py:43`, `connect_device_dialog_page.py:79`,
`expertise_level_page.py:82`); `click_tab`/`open(tab=)` occurs 9× in
`test_req023_account_settings.py`. All migrate to `settings-group-*` /
`settings-section-*`.

**Docs prior art (proceed).** Established by grep: `account.md` describes the
tabs; further settings references in `dashboard.md`,
`dashboard-personalization.md`, `notifications.md`, `module-visibility.md`,
`kiosk-mode.md`, `weather-services.md`, `guides/home-assistant-integration.md`,
`guides/browser-push-setup.md` (DE + EN). Unestablished: whether every hit is
a settings-tab reference; checked per file during implementation.

## Risks

- Bookmarks on old tab URLs land on the first visible group (operator decision Q5, no redirect).
- `AccountSettingsPage.tsx` is 2,233 lines; the split touches many handlers at once — the inventory test (acceptance-2) is the guard against a lost setting.
- Step-up re-auth return compares only the pathname (`useStepUpReauth.ts:80`); unestablished for group paths — `StepUpCallbackPage.test.tsx:52` already uses `/settings/account#account`.

## References

- Issue #2935, roadmap item R-17, depends on F-12
- `project/requirements/settings-page-grouping.md`
- #2934 places the weather fetch interval in the Installation group
