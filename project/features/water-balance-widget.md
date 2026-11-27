---
id: F-31
title: Wasserbilanz-Widget mit gemessenem Regen
status: draft
roadmap_item: R-27
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/backend/app/tasks/irrigation_tasks.py:156
      resolution: revisit-after Edit acceptance-2 (an F-29 binden)
      evidence: "Nur demand_date=today wird geschrieben; 'die nächsten Tage je Tag' und 'Speicherstand' gibt es erst, wenn F-29 Vorausrechnung, Speicherstand und Herkunft je Tag liefert (IrrigationDemand hat heute keines der Felder, irrigation_demand.py:26-49)."
    - kind: drift
      target: src/backend/app/common/enums.py:482
      resolution: revisit-after Edit acceptance-2
      evidence: "Bedarf entsteht auch für BALCONY; 'nur Outdoor und Gewächshaus' weicht vom Code ab (REQ-037 §4 :401 nennt ebenfalls nur outdoor/greenhouse)."
    - kind: prior-art
      target: src/backend/app/api/v1/tenant_scoped/weather/tenant_router.py:160
      resolution: proceed
      evidence: "GET /sites/{site_key}/weather-forecast liefert je Tag precipitation_mm, source, data_kind für jedes Mitglied, 404 für fremde Standorte (verify_site_owned :178) - Vorlage für acceptance-1 und Quelle für den Vergleich in acceptance-4."
    - kind: prior-art
      target: src/frontend/src/routes/AppRoutes.tsx:59
      resolution: proceed
      evidence: "SiteDetailPage ist lazy; die Seite besteht aus statisch importierten Sektionen (SiteDetailPage.tsx:41-44, :493-500), keine Tabs. Das Widget landet im Seiten-Chunk, nicht im Initial-Bundle."
    - kind: prior-art
      target: src/frontend/bundle-budget.json:4
      resolution: proceed
      evidence: "initialJsGzipKb 360, 'never raise it'; Seitentexte gehören in pages.json (lazy, i18n.ts:18-23), nicht in den Kern."
    - kind: prior-art
      target: src/frontend/src/components/dashboard/widgetRegistry.ts:42
      resolution: proceed
      evidence: "Die REQ-045-Registry kennt weather_forecast, aber F-31 liegt laut REQ-037 §4 auf der Standort-Detailseite und erweitert die Registry nicht; REQ-045 enthält keinen Wasser- oder Standort-Bezug (Grep ohne Treffer)."
---

## Description

REQ-037 sieht auf der Standort-Detailseite ein Widget „Wasserbilanz“ vor, das
es nicht gibt; auch einen Endpunkt zum Lesen des Gießbedarfs gibt es nicht.
Nutzer sehen deshalb nicht, warum Kamerplanter zum Gießen rät oder nicht.

Nach dieser Änderung zeigt das Widget für Outdoor- und Gewächshaus-Standorte
die nächsten Tage mit ET₀, ETc, Niederschlag, Speicherstand und Netto-Bedarf
(mm und Liter), die verwendete Methode und je Tag, ob der Niederschlag gemessen
oder vorhergesagt ist. Weichen Messung und Prognose stark voneinander ab, weist
es darauf hin, ohne einen Wert zu ändern.

## Acceptance criteria

- [ ] **acceptance-1** Ein mandantengebundener Lese-Endpunkt liefert den Gießbedarf eines Standorts je Run und Tag; Mitglieder des Mandanten dürfen lesen, Fremde erhalten 404.
- [ ] **acceptance-2** Das Widget auf der Standort-Detailseite (nur Outdoor und Gewächshaus) zeigt je Tag ET₀, ETc, Niederschlag, Speicherstand, Netto-Bedarf in mm und Litern sowie Methode und Qualität.
- [ ] **acceptance-3** Je Tag ist erkennbar, ob der Niederschlag gemessen oder vorhergesagt ist (gleiche Kennzeichnung wie `WeatherProvenanceBadge`).
- [ ] **acceptance-4** Bei starker Abweichung (z. B. 0 mm gemessen gegen 20 mm vorhergesagt) zeigt das Widget einen Hinweis; keiner der Werte wird automatisch korrigiert.
- [ ] **acceptance-5** Leer-, Lade- und Fehlerzustand sind gestaltet; das Widget ist mobil ohne horizontales Scrollen lesbar; Beschriftungen DE + EN.

## Test hooks

- **acceptance-1** — API tests: member read, foreign tenant 404 — pending
- **acceptance-2** — vitest on the widget with a multi-day payload; hidden for indoor sites — pending
- **acceptance-3** — vitest: observed vs. forecast badge per day — pending
- **acceptance-4** — vitest with diverging measured/forecast series — pending
- **acceptance-5** — vitest empty/loading/error + mobile breakpoint; i18n completeness check — pending

## Consistency notes

**Missing widget and endpoint (proceed, D4).** Established: REQ-037 §4 (`:400`)
specifies the widget, `src/frontend/src` has none, and REQ-037:462 notes the
missing read endpoint. Split out of F-30 so the deferral feature stays focused;
ordered before F-30 because F-30's annotation refers to the visible balance.

**Overlap with F-24 (proceed).** F-24 works on the care dashboard; F-31 on the
site detail page. They share only the provenance badge.

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`; same run, triggers and caveats as recorded in `site-rain-sensor.md` (no test run; resolutions are proposals). The frontmatter holds the six findings of this run; the four findings of 2026-11-17 (`feature-consistency-reviewer@5d01b6c4`) are listed with their fate. The report's verdict: **promotable after the edits below**; no operator decision blocks.

**Findings of 2026-11-17 — fate.**

1. `REQ-037:400` (drift, proceed) — moved to `:401`. Still true: grep for waterBalance / Wasserbilanz / irrigation_demand in `src/frontend/src` has no hit.
2. `REQ-037:462` (drift, proceed) — moved to `:463`. Still true (no endpoint; the only readers are `watering_service` and `irrigation_zone_repository.bed_demands`).
3. `WeatherProvenanceBadge.tsx:15` (prior-art, proceed) — still true.
4. Overlap F-24 (proceed) — still true (F-24 `draft`, different surface).

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@5d01b6c4
  findings:
    - kind: drift
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:400
      resolution: proceed
      evidence: "REQ-037 §4 specifies a 'Wasserbilanz' widget on the site detail page, but src/frontend/src has no hit for waterBalance/Wasserbilanz/irrigation demand — split out of F-30 by operator decision D4."
    - kind: drift
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:462
      resolution: proceed
      evidence: "REQ-037 states irrigation_demands has no endpoint — acceptance-1 adds the tenant-scoped read endpoint."
    - kind: prior-art
      target: src/frontend/src/components/weather/WeatherProvenanceBadge.tsx:15
      resolution: proceed
      evidence: "The badge already separates observed vs. forecast via data_kind/is_current_conditions (REQ-046 §4.2 :406) — acceptance-3 reuses it."
    - kind: overlap
      target: F-24
      resolution: proceed
      evidence: "F-24 extends the care dashboard; F-31 lives on the site detail page (REQ-037 §4) — different surface, shared provenance badge."
```

**New findings.**

- **Store level and following days depend on F-29 (drift, `irrigation_tasks.py:156`).** Only `demand_date=today` is written; "the next days, per day" and "store level" exist only once F-29 delivers look-ahead, store level and provenance per day (`IrrigationDemand` has none of the fields today, `irrigation_demand.py:26-49`). acceptance-2 should be bound to F-29; the dependency is now recorded under References.
- **Site types (drift, `enums.py:482`).** Demand also arises for BALCONY; "only outdoor and greenhouse" deviates from the code (REQ-037 §4 `:401` also names only outdoor/greenhouse).
- **Template for the read endpoint (prior-art, proceed, `weather/tenant_router.py:160`).** `GET /sites/{site_key}/weather-forecast` returns `precipitation_mm`, `source`, `data_kind` per day for every member and 404 for foreign sites (`verify_site_owned` `:178`) — the template for acceptance-1 and the source of the comparison in acceptance-4.
- **Bundle (prior-art, proceed, `AppRoutes.tsx:59`, `bundle-budget.json:4`).** `SiteDetailPage` is lazy; the page consists of statically imported sections (`SiteDetailPage.tsx:41-44`, `:493-500`), no tabs. The widget lands in the page chunk, not in the initial bundle (`initialJsGzipKb` 360, "never raise it"); page texts belong in `pages.json` (lazy, `i18n.ts:18-23`), not in the core.
- **Not a dashboard widget (prior-art, proceed, `widgetRegistry.ts:42`).** The REQ-045 registry knows `weather_forecast`, but F-31 lives on the site detail page per REQ-037 §4 and does not extend the registry; REQ-045 has no water or site reference. If it were to become a dashboard widget later it would meet F-22/F-23/F-24 (all `draft`). Recommendation: write the non-goal into the file.

**Further discussion.**

- **Mobile.** The bottom navigation (#3149, `MobileBottomNav.tsx`, `bottomNavOffset.ts`) concerns only fixed elements; a card in the page flow is untouched.
- **acceptance-4.** "Strong deviation" has no threshold (parameter 15 of the F-29 review). After F-28 the weather endpoint returns two rows for today; the comparison can be built from them.
- **acceptance-1** can be built independently of F-28/F-29 and serves F-30 as a test access.

**Already implemented:** nothing of the widget or the endpoint; only the badge, the weather endpoint as a pattern and the collection.

**Cross-feature.** F-31 depends on F-29 (store level, following days). It is no technical precondition for F-30; the roadmap order F-28, F-29, F-31, F-30 (D4) stays defensible because the read endpoint makes the chain visible. The common gaps (among them balcony in the site-type set) and the comparison with issue #3002 are in `site-rain-sensor.md`; the issue does not mention a widget — F-31 comes from the requirements interview and REQ-037 §4.

**Edits required before `ready`** (the report's verdict for F-31, translated):

1. Bind acceptance-2 to F-29 (store level, following days), or state the stand before F-29 explicitly as today's single-day balance.
2. Align the site types with the code.
3. Name the threshold for acceptance-4.
4. Add the non-goal "no dashboard widget".

acceptance-1 (the read endpoint) can be built at once.

## Risks

- The speicherstand (store level) depends on F-29; before F-29 lands the widget shows the single-day balance.

## References

- Issue #3002, roadmap item R-27, REQ-037 §4
- `project/requirements/measured-rain-soil-water-balance.md` (R5, R8)
- Depends on F-29 (store level, following days) — recorded by the consistency re-run 2026-11-27

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

Keine Entscheidung blockiert F-31. Festzuhalten sind:

- **Nicht-Ziel: kein Dashboard-Widget.** F-31 liegt auf der Standort-Detailseite (REQ-037 §4) und erweitert die Widget-Registry des Dashboards nicht (`src/frontend/src/components/dashboard/widgetRegistry.ts:42`). Ein Dashboard-Widget träfe F-22, F-23 und F-24 (alle `draft`).
- **Schwelle für acceptance-4 („starke Abweichung“ zwischen Messung und Prognose).** Heute gibt es keine Schwelle; sie ist Parameter 15 des agrarbiologischen Reviews von F-29 und wird dort mit bestätigt.
  - **Schwelle aus dem Review übernehmen:** acceptance-4 wird erst mit dem bestätigten Wert prüfbar.
  - **Ohne Schwelle:** Das Kriterium bleibt nicht testbar.
- **Stand vor F-29 (acceptance-2).** Heute schreibt der Task nur den Bedarf von heute (`irrigation_tasks.py:156`); Speicherstand und Folgetage gibt es erst mit F-29.
  - **An F-29 binden:** Das Widget zeigt Speicherstand und die nächsten Tage, kommt aber erst nach F-29.
  - **Tagesbilanz von heute festschreiben:** Das Widget ist vor F-29 lieferbar und zeigt nur den heutigen Tag.
