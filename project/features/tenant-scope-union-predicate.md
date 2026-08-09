---
id: F-4
title: Geteiltes Mandanten-Union-Leseprädikat (Extraktion)
status: ready
roadmap_item: R-14
sprint: 2
created: 2026-08-09
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-08-09
  agent_version: feature-consistency-reviewer@27055772e
  findings:
    - kind: prior-art
      target: src/backend/app/data_access/arango/fertilizer_repository.py:42
      resolution: proceed
      evidence: "Three verbatim 3-arm copies confirmed real: fertilizer_repository.py:42, nutrient_plan_repository.py:46, task_repository.py:61 — `(doc.tenant_key == @tenant_key OR doc.tenant_key == \"\" OR doc.tenant_key == null)`. No shared helper exists (grep: zero hits). Extraction target is real."
    - kind: prior-art
      target: src/backend/app/data_access/arango/task_repository.py:832
      resolution: proceed
      evidence: "task_repository holds a SECOND copy of the predicate at line 832 (list_for_run, with a SORT tie-break) beyond the line-61 copy. acceptance-2 must catch both, and the line-832 SORT tie-break must be preserved."
    - kind: drift
      target: src/backend/app/data_access/arango/ai_repository.py:37
      resolution: revisit-after "operator reconciles acceptance-2/acceptance-3 with the 2-arm ai variant — resolved here as: helper parameterises the empty-string arm; ai keeps 2-arm semantics"
      evidence: "The ai_repository variant is 2-arm only: `FILTER doc.tenant_key == @tenant_key OR doc.tenant_key == null` — NO `== \"\"` arm. Folding it into the 3-arm helper ADDS that arm = a behaviour change, contradicting acceptance-3. Resolution: the helper takes an `include_empty_string` parameter (default true, 3-arm); ai calls it with false to keep its 2-arm read scope unchanged."
    - kind: prior-art
      target: src/backend/app/data_access/arango/botanical_family_repository.py:14
      resolution: proceed
      evidence: "botanical_family_repository quotes the 3-arm union as its documented target rule but applies NO predicate today (species has no tenant_key). A future (5th) consumer once F-3 lands, not a current copy to extract."
---

## Description

Das Mandanten-Union-Prädikat, das globale und eigen-Tenant-Zeilen zusammen
sichtbar hält (`tenant_key == @tenant OR tenant_key == "" OR tenant_key ==
null`), ist heute mehrfach wortgleich als Inline-AQL dupliziert. Dieses Feature
extrahiert es in **einen geteilten Helfer**, sodass alle Konsumenten dieselbe
Regel verwenden und F-5 (tenant-bewusstes Species-Lesen) ihn als fünften
Konsumenten nutzen kann, statt eine weitere Kopie anzulegen. Für bestehende
Konsumenten ändert sich das Verhalten nicht: der `ai_repository`-Konsument nutzt
heute bewusst nur zwei Arme (ohne den `== ""`-Arm), weshalb der Helfer den
Leerstring-Arm parametrisierbar macht und `ai_repository` ihn ausgeschaltet
aufruft.

## Acceptance criteria

- [ ] **acceptance-1** Ein einziger geteilter Helfer erzeugt das Union-Prädikat; der `== ""`-Arm ist über einen Parameter (Default: an/3-armig) schaltbar.
- [ ] **acceptance-2** `fertilizer_repository.py`, `nutrient_plan_repository.py`, `task_repository.py` (BEIDE Kopien: Z.61 und Z.832) und `ai_repository.py` rufen den Helfer auf; keine wortgleiche Inline-Kopie des Prädikats verbleibt. Der SORT-Tie-Break in `task_repository.py:832` bleibt erhalten.
- [ ] **acceptance-3** Kein Verhaltenswechsel für bestehende Konsumenten: die 3-armigen Konsumenten bleiben 3-armig, `ai_repository` bleibt 2-armig (Helfer mit ausgeschaltetem Leerstring-Arm); die bestehenden Tenant-Filter-Tests dieser Repos bleiben unverändert grün.

## Test hooks

- **acceptance-1** — Unit-Test des Helfers (3-armig default; 2-armig bei ausgeschaltetem Parameter) — pending
- **acceptance-2** — Grep-/Struktur-Test: keine Inline-Kopie mehr; alle fünf Aufrufstellen nutzen den Helfer; task:832-SORT erhalten — pending
- **acceptance-3** — bestehende Tenant-Filter-Tests von fertilizer/nutrient_plan/task/ai bleiben grün (Regressionslauf) — pending

## Consistency notes

- **prior-art (drei 3-armige Kopien):** fertilizer:42, nutrient_plan:46, task:61
  sind wortgleich; kein geteilter Helfer existiert. Extraktionsziel real.
  Resolution: `proceed`.
- **prior-art (task-Doppelkopie):** `task_repository` hält eine ZWEITE Kopie bei
  Z.832 (`list_for_run`, mit SORT-Tie-Break). acceptance-2 muss beide erfassen und
  den Tie-Break bewahren. Resolution: `proceed`.
- **drift (ai 2-armig vs 3-armig) — schärfstes Konsistenzrisiko der Charge:**
  `ai_repository:37` ist nur 2-armig (`tenant_key == @tenant OR tenant_key ==
  null`, ohne `== ""`). Ein Einfalten in den 3-armigen Helfer würde den
  `== ""`-Arm hinzufügen = Verhaltenswechsel, im Widerspruch zu acceptance-3.
  **Resolution (revisit-after, hier entschieden):** der Helfer bekommt einen
  `include_empty_string`-Parameter (Default `true`, 3-armig); `ai_repository` ruft
  ihn mit `false` auf und behält damit exakt seine 2-armige Lesesemantik. So
  bleibt acceptance-3 wörtlich wahr. Falls die Implementierung stattdessen ai
  bewusst auf 3-armig migrieren will, ist acceptance-3 vorher umzuformulieren und
  ein Verhaltens-Test zu ergänzen.
- **prior-art (botanical_family):** zitiert die 3-armige Union als dokumentierte
  Zielregel, wendet aber heute kein Prädikat an — ein künftiger (fünfter)
  Konsument, sobald F-3 landet, keine aktuelle Kopie. Resolution: `proceed`.

## Risks

- Wird der `ai_repository`-Aufruf ohne den ausgeschalteten Leerstring-Arm
  umgestellt, ändert sich still die Lese-Scope von `ai_provider_configs` — die
  „behauptet mehr als sie leistet"-Fehlerklasse unter einem „kein
  Verhaltenswechsel"-Banner. Der Parameter-Default und der ai-Aufruf mit `false`
  verhindern das; acceptance-3 pinnt es.
- Die zweite task-Kopie (Z.832) ist leicht zu übersehen; acceptance-2 nennt sie
  explizit.

## Open questions

- Bestätigung, dass die Parameter-Lösung (ai bleibt 2-armig) gegenüber einer
  bewussten 3-armig-Migration von `ai_repository` bevorzugt wird. Vorgeschlagene
  und hier eingetragene Default-Antwort: Parameter-Lösung (verhaltenserhaltend).
