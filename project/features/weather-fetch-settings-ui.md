---
id: F-14
title: Wetterabruf-Einstellungen in der Installations-Gruppe
status: draft
roadmap_item: R-18
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@6b9b769c6
  findings:
    - kind: overlap
      target: F-11
      resolution: proceed
      evidence: "F-11 moves WeatherProvidersSettingsTab (AccountSettingsPage.tsx:209-211,1380) into the Installation group and edits weather-services.md; F-14 edits the same card and doc — ordered after F-11."
    - kind: drift
      target: docs/de/user-guide/notifications.md:189
      resolution: proceed
      evidence: "notifications.md:189 (DE+EN) says frost is checked 'einmal täglich'; added to acceptance-6."
    - kind: prior-art
      target: src/frontend/src/pages/auth/AccountSettingsPage.tsx:196
      resolution: proceed
      evidence: "canManageInstanceSettings = isLightMode || isPlatformAdminUser (:196) matches the light-mode-aware require_platform_admin (weather_providers/router.py:16-19) — acceptance-5 reuses the gate."
    - kind: prior-art
      target: src/frontend/src/i18n/locales/de/pages.json:4860
      resolution: proceed
      evidence: "fetchTimeout/fetchTimeoutHelper (de :4860-4861, en :4859-4860) and fetchDesc (de :4859, en :4858) are the keys to reword; weather-services.md:69 already says 'pro Wetterabfrage'."
---

## Description

In der Karte „Abruf-Einstellungen“ der Wetterquellen gibt es heute nur das
Zeitlimit pro Anfrage und die Standardquelle. Das Zeitlimit (bis 120 s) wird
leicht als Abrufhäufigkeit missverstanden, und es ist nicht zu sehen, wann
zuletzt Wetterdaten geholt wurden.

Nach dieser Änderung stellt der Plattform-Admin in derselben Karte, die mit
F-11 in die Gruppe „Installation“ zieht, das Abrufintervall in Stunden ein,
startet mit „Jetzt abrufen“ einen Abruf und verfolgt dessen Fortschritt und
Ergebnis. Die Karte zeigt, wann der letzte erfolgreiche Abruf war und wann der
nächste geplant ist; das Zeitlimit-Feld ist eindeutig als Grenze pro Anfrage
beschriftet.

## Acceptance criteria

- [ ] **acceptance-1** In der Karte „Abruf-Einstellungen“ der Gruppe „Installation“ gibt es ein Feld für das Abrufintervall in Stunden (mindestens 6), das wie die übrigen Felder gespeichert wird.
- [ ] **acceptance-2** „Jetzt abrufen“ zeigt Fortschritt und anschließend das Ergebnis; ein abgelehnter Abruf zeigt, ab wann ein neuer Abruf möglich ist.
- [ ] **acceptance-3** Die Karte zeigt den letzten erfolgreichen und den nächsten geplanten Abruf.
- [ ] **acceptance-4** Beschriftung und Hilfetext des Zeitlimit-Felds machen in DE und EN klar, dass es sich um ein Zeitlimit pro Anfrage und nicht um die Abrufhäufigkeit handelt.
- [ ] **acceptance-5** Nur wer Instanzeinstellungen verwalten darf (Plattform-Admin bzw. light-Modus), sieht diese Bedienelemente.
- [ ] **acceptance-6** Die Nutzerdoku (`weather-services.md` und `notifications.md`, DE + EN) beschreibt Intervall, manuellen Abruf und die Frostprüfung nach jedem Abruf.

## Test hooks

- **acceptance-1** — vitest on `WeatherProvidersSettingsTab` (field, min 6, saved payload) — pending
- **acceptance-2** — vitest with mocked 202 / status polling / 409 / 429 + `Retry-After` — pending
- **acceptance-3** — vitest rendering the status (last/next fetch) — pending
- **acceptance-4** — i18n completeness check + review of the DE/EN strings — pending
- **acceptance-5** — vitest gate test (non-admin in full mode sees no controls) — pending
- **acceptance-6** — `mkdocs build --strict` — pending

## Consistency notes

**Overlap with F-11 (proceed).** Established: F-11 moves
`WeatherProvidersSettingsTab` (`AccountSettingsPage.tsx:209-211,1380`) into the
Installation group and rewrites `weather-services.md:13`; F-14 edits the same
card and doc file. Not merged: F-14 depends on its own backend contracts
(F-13) and has its own criteria. The order F-11 → F-14 (requirement R11)
resolves the overlap; F-14 starts only after F-11 is merged.

**Frost wording in the docs (drift, proceed).** Established:
`notifications.md:189` (DE + EN) says frost is checked "einmal täglich", which
becomes wrong with F-13; included in acceptance-6.

**Gate prior art (proceed).** Established: `canManageInstanceSettings`
(`AccountSettingsPage.tsx:196`) equals the light-mode-aware
`require_platform_admin` of the weather admin router
(`weather_providers/router.py:16-19`); acceptance-5 reuses it.

**i18n prior art (proceed).** Established: the keys to reword are
`fetchTimeout`/`fetchTimeoutHelper` (de `pages.json:4860-4861`, en
`:4859-4860`) and `fetchDesc` (de `:4859`, en `:4858`).

## Risks

- Depends on F-11 (card location) and F-13 (backend contracts); starting earlier causes merge conflicts in the settings page.

## References

- Issue #2934, roadmap item R-18
- `project/requirements/weather-fetch-interval.md`
