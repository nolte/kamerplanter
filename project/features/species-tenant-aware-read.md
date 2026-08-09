---
id: F-5
title: Tenant-bewusstes Species-Lesen auf der globalen Route
status: ready
roadmap_item: R-14
sprint: 2
created: 2026-08-09
ended: null
verifies_sprint_value: acceptance-2
consistency_check:
  performed_at: 2026-08-09
  agent_version: feature-consistency-reviewer@27055772e
  findings:
    - kind: prior-art
      target: src/backend/tests/unit/data_access/arango/test_botanical_family_repository.py:131
      resolution: proceed
      evidence: "TestSpeciesScopeConsistency (#816) ALREADY exists and is explicitly written to keep holding when the REQ-001 v4.0 tenant scope lands. acceptance-4's anchor is real; F-5 fills in the predicate the test already guards, it does not create the test."
    - kind: prior-art
      target: src/backend/app/domain/services/species_service.py:70
      resolution: proceed
      evidence: "list_species is `return self._repo.get_all(offset, limit)` — fully UNFILTERED; the route is /api/v1/species (global, not /t/{slug}/). Plus botanical_family_repository.get_species_by_family/_count apply no predicate. F-5 must scope BOTH surfaces or TestSpeciesScopeConsistency breaks."
    - kind: prior-art
      target: src/backend/app/common/auth.py:61
      resolution: revisit-after "F-3 lands tenant_key on Species"
      evidence: "get_current_tenant is structurally bound to the tenant_slug Path param, so /species has no tenant context today (acceptance-3 mechanism genuinely unimplemented; grep: no existing global-tenant-resolution helper). The read predicate is also inert until F-3 adds tenant_key — F-5 depends on both F-3 and F-4."
---

## Description

Die globale Species-Route gibt heute jede Art an jeden authentifizierten
Aufrufer zurück. Mit diesem Feature liefert sie künftig nur noch **globale und
eigen-Tenant-Arten**; privat angelegte Arten fremder Mandanten bleiben verborgen
— genau das Sprint-Versprechen. Dazu entsteht der bislang fehlende
**Tenant-Auflösungs-Mechanismus für globale-aber-tenant-bewusste Routen** (heute
ist `get_current_tenant` strukturell an den `/t/{slug}/`-Path-Parameter gebunden;
die konkrete Form sitzt auf der #780/REQ-049-Achse und wird im Zuge dieses
Features entworfen und dokumentiert). Auf beide Species-Lesesurfaces — die
Species-Liste und die Species-Reads des Botanical-Family-Repositories — wird das
in F-4 extrahierte geteilte Union-Prädikat angewandt, damit Count und Listing
nicht divergieren. Das Feature ist inert, bis F-3 den `tenant_key` liefert, und
nutzt den F-4-Helfer; Reihenfolge im Sprint daher F-3 → F-4 → F-5.

## Acceptance criteria

- [ ] **acceptance-1** Die Species-Liste liefert globale (`tenant_key == ""`) UND eigen-Tenant-Arten des Aufrufers (die #324-Sichtbarkeit — globaler Seed-Katalog bleibt für alle sichtbar).
- [ ] **acceptance-2** Eine Art eines fremden Mandanten erscheint NICHT in der Species-Liste eines anderen Mandanten.
- [ ] **acceptance-3** Ein Tenant-Auflösungs-Mechanismus für globale-aber-tenant-bewusste Routen ist implementiert, und sein Entwurf ist dokumentiert.
- [ ] **acceptance-4** Species-Count und -Listing schränken die Collection identisch ein (beide Lesesurfaces gescoped); `TestSpeciesScopeConsistency` (#816) bleibt grün.

## Test hooks

- **acceptance-1** — API/Repo-Test: Liste enthält globale + eigen-Tenant-Arten — pending
- **acceptance-2** — beidseitiger Isolationstest (fremd-Tenant-Art fehlt in fremder Liste) — pending
- **acceptance-3** — Test des Tenant-Auflösungs-Mechanismus auf der globalen Route + ADR/Doku-Verweis — pending
- **acceptance-4** — `TestSpeciesScopeConsistency` (#816) grün; Count==Listing-Scope über beide Surfaces — pending

## Consistency notes

- **prior-art (#816-Test existiert):** `TestSpeciesScopeConsistency`
  (`test_botanical_family_repository.py:131`) ist bereits vorhanden und dafür
  geschrieben, beim Landen des REQ-001-v4.0-Scopes weiter zu halten. acceptance-4
  ist auf einen realen, aktuell grünen Test verankert; F-5 füllt das Prädikat, das
  der Test bereits bewacht. Resolution: `proceed`.
- **prior-art (unfiltered read, zwei Surfaces):** `species_service.list_species`
  ist ungefiltert (`get_all`), und die Species-Reads des
  Botanical-Family-Repos wenden kein Prädikat an. F-5 muss BEIDE Surfaces
  scopen, sonst bricht #816 (Count/Listing-Divergenz). Resolution: `proceed`.
- **prior-art / dependency (kein Tenant-Kontext auf globaler Route):**
  `get_current_tenant` (`auth.py:61`) ist an den Path-Parameter gebunden; für
  `/species` gibt es heute keinen Tenant-Kontext, und das Leseprädikat ist inert,
  bis F-3 `tenant_key` hinzufügt. Ordnungs-Constraint: **F-3 → F-4 → F-5**.
  Resolution: `revisit-after F-3`.

## Risks

- Wird nur die Species-Liste, aber nicht der Botanical-Family-Species-Read
  gescoped (oder umgekehrt), divergieren Count und Listing und `#816` bricht —
  genau die Asymmetrie, die acceptance-4 verhindert.
- Der Tenant-Auflösungs-Mechanismus (acceptance-3) ist eine echte
  Architektur-Entscheidung (Form offen, A1 im Requirement); sie muss dokumentiert
  werden, damit spätere tenant-bewusste globale Routen demselben Muster folgen.

## References

- Requirement: `project/requirements/species-tenant-ownership.md` (R3, R5, R7, R8; A1)
- Abhängig von F-3 (`tenant_key`) und F-4 (geteilter Helfer)
