---
id: F-27
title: Verlauf-Tab an der Pflanze
status: draft
roadmap_item: R-23
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@4a3321288
  findings:
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:1507
      resolution: proceed
      evidence: "PS-UX-001: tabs Profil/Verlauf belong to the core module plants and are always visible; social only gates the Mastodon part (§25.2:1500, Anhang K no. 18) — acceptance-4 follows."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:1472
      resolution: proceed
      evidence: "§25.1: visible DE label 'Verlauf', 'Timeline' forbidden in visible texts; i18n pages.plantTimeline.*, enums.plantEventType.*, enums.eventOrigin.* (PS-UX-013:1542); testids timeline-item-{key}, timeline-filter-{type} (PS-UX-012) — acceptance-5."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:1539
      resolution: proceed
      evidence: "PS-UX-010 / TC-055-006 (TC-REQ-055.md:268-271): relative date with absolute tooltip, who-sees-it icon, status 'nicht gezeigt' per row — added to acceptance-1."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:388
      resolution: proceed
      evidence: "PS-EVT-005 per-event visibility change vs. PS-EVT-003 'only write action'; operator decision: visibility change moves to R-24 (no effect without a profile)."
    - kind: prior-art
      target: src/backend/app/core/permissions.py:32
      resolution: proceed
      evidence: "No ResourceType.SOCIAL / PLANT_EVENT; §21:1124 roles viewer+ read, grower+ backfill; operator decision: timeline routes use ResourceType.PLANT, SOCIAL with wave 2."
    - kind: prior-art
      target: src/frontend/src/pages/pflanzen/PlantInstanceDetailPage.tsx:180
      resolution: proceed
      evidence: "Tabs are index-based via useTabUrl([...,'photos','diary']); inserting earlier repoints setTab(8) — append the new tab at the end; phase and diary tabs stay (§25.2:1500)."
---

## Description

Wer wissen will, was mit einer Pflanze in den letzten Wochen passiert ist,
muss heute Tagebuch, Phasen und Fotos einzeln durchsehen.

Nach dieser Änderung hat jede Pflanze einen Tab „Verlauf“. Er zeigt alles,
was passiert ist, das Neueste zuerst: was es war, wann (relativ, mit genauem
Zeitpunkt beim Überfahren), woher es kommt (du selbst, Kamerplanter, ein
Sensor, ein Import …), wer es sehen kann und dass es nirgends gezeigt wird.
Ein Link führt zur Quelle, etwa zum Tagebucheintrag. Mehrere gleichartige
Ereignisse eines Tages erscheinen auf einer Karte. Filter grenzen nach Art,
Herkunft und Zeitraum ein. Der Verlauf selbst ist nur lesend — mit einer
Ausnahme: „Meilenstein festhalten“ legt einen Tagebucheintrag an, aus dem das
Ereignis entsteht. Der Tab ist für jede Pflanze da, auch im einfachen Modus.

## Acceptance criteria

- [ ] **acceptance-1** Der Tab „Verlauf“ zeigt die Ereignisse einer Pflanze, das Neueste zuerst, je Zeile mit Symbol, Kurztext, relativem Datum (genauer Zeitpunkt als Tooltip), Herkunftskennzeichen, Sichtbarkeitssymbol, Status „nicht gezeigt“ und Link zur Quelle; die Liste lädt seitenweise nach und lässt sich nach Art, Herkunft und Zeitraum filtern.
- [ ] **acceptance-2** „Meilenstein festhalten“ ist die einzige schreibende Aktion und legt einen Tagebucheintrag vom Typ Meilenstein an; einen zweiten Erfassungsweg gibt es nicht.
- [ ] **acceptance-3** Ereignisse derselben Art innerhalb von 24 Stunden erscheinen auf einer gemeinsamen Karte; die Einzelereignisse bleiben erhalten.
- [ ] **acceptance-4** Der Tab ist für jede Pflanze immer sichtbar — im einfachen und im vollen Modus, ohne Identität und ohne Verbindung zu einem Dienst — und hängt nicht am Modul für Veröffentlichungen; alle Mitglieder lesen, Nachtragen (F-26) ist ab Gärtner möglich.
- [ ] **acceptance-5** Sichtbare Texte verwenden die Begriffsliste (DE „Verlauf“, nie „Timeline“) in DE und EN, und die Nutzerdoku beschreibt den Verlauf.

## Test hooks

- **acceptance-1** — vitest on the timeline tab (row fields, pagination, filters) + E2E TC-055-006 — pending
- **acceptance-2** — vitest: action creates a milestone diary entry; backend has no event write endpoint — pending
- **acceptance-3** — vitest grouping within 24 h — pending
- **acceptance-4** — vitest in light mode without identity; router tests (viewer 200, viewer backfill 403) on `ResourceType.PLANT` — pending
- **acceptance-5** — i18n completeness + vocabulary check (no visible "Timeline"); `mkdocs build --strict` — pending

## Consistency notes

**Module gating (drift, proceed).** Established: PS-UX-001 (`REQ-055:1507`),
§25.2 (`:1500`) and Anhang K no. 18 put the tab in the core module `plants`,
always visible; `social` only gates the Mastodon part. Acceptance-4 follows
the spec.

**Vocabulary and keys (drift, proceed).** Established: §25.1 (`:1472`)
requires the visible label "Verlauf" and forbids "Timeline"; PS-UX-013
(`:1542`) fixes the i18n namespaces, PS-UX-012 the test ids
`timeline-item-{key}`, `timeline-filter-{type}` (acceptance-5).

**Row content (drift, proceed).** Established: PS-UX-010 (`:1539`) and
TC-055-006 (`TC-REQ-055.md:268-271`) require relative date with tooltip, a
who-sees-it icon and the status "nicht gezeigt"; added to acceptance-1.
Further publishing statuses follow with wave 3.

**Visibility change moved (decision).** Established: PS-EVT-005 (`:388`)
allows changing an event's visibility while PS-EVT-003 calls the milestone
the only write action. Operator decision 2026-11-17: the visibility change
moves to R-24, where a profile makes it effective; acceptance-2 holds as
written.

**Permissions (prior-art, proceed).** Established: there is no
`ResourceType.SOCIAL`/`PLANT_EVENT` (`permissions.py:32-61`); §21 (`:1124`)
lets every member read and growers backfill. Operator decision 2026-11-17: the
timeline routes use `ResourceType.PLANT`; `SOCIAL` arrives with wave 2.

**Tab index trap (prior-art, proceed).** Established: the plant detail tabs
are index-based (`PlantInstanceDetailPage.tsx:180-183`); inserting a tab
earlier silently repoints `setTab(8)` calls. The new tab is appended at the
end; the phase and diary tabs stay (§25.2).

## Risks

- TC-055-006 assumes a time-based phase change, but `check_auto_transitions` is intentionally not scheduled; the E2E seed has to create the case.

## References

- REQ-055 v1.5 §10, §25; roadmap item R-23; after F-25 (parallel to F-26)
- Requirement gate: operator override 2026-11-17 (REQ-055 v1.5 as basis)

## Betreiberentscheidungen 2026-11-27

- Der Verlauf zeigt die Herkunftsklasse eines Ereignisses und „du" für eigene Ereignisse. Den Namen einer anderen Person zeigt er nur, wenn die Sichtbarkeitsmatrix es erlaubt (`spec/privacy/05-access-and-visibility.md`). acceptance-4 („alle Mitglieder lesen") gilt für die Ereignisse, nicht für die Namen.
