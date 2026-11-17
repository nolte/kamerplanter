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

## Risks

- The speicherstand (store level) depends on F-29; before F-29 lands the widget shows the single-day balance.

## References

- Issue #3002, roadmap item R-27, REQ-037 §4
- `project/requirements/measured-rain-soil-water-balance.md` (R5, R8)
