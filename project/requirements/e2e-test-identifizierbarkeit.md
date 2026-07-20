# Requirements — E2E-Testfälle maschinell identifizierbar machen + Kernfunktions-Abdeckung prüfen

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

## Bounded context

- **Was:** Zwei zusammenhängende Ergebnisse. (1) **Identifizierbarkeit** — die bestehende
  E2E-Suite (`tests/e2e/`, Selenium/pytest, Page-Object-Pattern) so markieren, dass nach einer
  Code-/Feature-Änderung **gezielt und maschinell selektierbar** die betroffenen Testfälle laufen.
  Heute nur grob per Dateipfad oder über 2 fachliche Pauschal-Marker (`smoke`, `core_crud`).
  (2) **Abdeckungs-Check** der fünf Kernfunktionen (Pflanzenerfassung, Gießen/Bewässerung,
  Düngen/Dünger, Ernte, Aussaat-/Kalenderansicht) — echte Lücken benennen.
- **Für wen:** Der Entwickler/Operator, der die Suite lokal manuell über `task test:e2e`
  bzw. `scripts/run-e2e.sh` fährt. **Kein CI-Konsument** — E2E hat bewusst kein CI-Gate
  (GH-Runner zu schwach; dokumentierte Entscheidung, nicht als Lücke zu melden).
- **Explizit außerhalb (operator-geklärt 2026-07-14):**
  - **Kein** E2E-CI-Gate erzwingen.
  - **Keine** Change→Test-Mapping-Datei (Ansatz D) in dieser Iteration; die Marker-Struktur
    bleibt aber kompatibel zu `nolte-engineering:release-regression-scope`.
  - **Keine** neuen Tests zum Schließen der Kernfunktions-Lücken — Lücken werden nur **benannt**;
    Implementierung ist separate Iteration/Issues.
  - TC-ID wird **nicht** zum Selektions-Marker (keine `-m TC-…`-Achse) — nur ins Protokoll gehoben.
  - 702 Testfunktionen werden **nicht** per Hand markiert, wo Auto-Ableitung reicht.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `4`
  (3 Design-Fragen-Turns + 1 Teach-back-Turn; spec-Defaults sonst unverändert)
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (alle erforderlichen Dimensionen ≥ τ_high nach Teach-back;
  keine Frage mit positivem Netto-EVPI verblieb — die 6 im Plan vorregistrierten offenen
  Fragen sind alle operator-beantwortet)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | specification | Operator-Antworten Selektions-Achse (A+B) + strict-markers + record_property (2026-07-14), Teach-back bestätigt |
| `non_functional` | yes | 0.85 | interpretation | Plan-Invarianten NFR-003 (Tests Englisch), NFR-008a (Page-Object/Protokoll), `--strict-markers` als Robustheits-Anforderung; Teach-back |
| `constraints` | yes | 0.95 | specification | Authoritative operator answers (kein CI-Gate, minimal-invasiv, Ansatz D ausgeschlossen) + CLAUDE.md/Plan §Invarianten |
| `domain_objects` | yes | 0.85 | interpretation | Plan Ist-Zustand: 75 Dateien/702 Fkt., 65 Page-Objects, conftest-Marker, `spec/e2e-testcases/` TCs |
| `actors` | yes | 0.85 | specification | Operator: lokaler Entwickler/Operator, kein CI-Konsument (args + Teach-back) |
| `acceptance_criteria` | yes | 0.85 | specification | Operator-Scope „Mechanik + Lücken dokumentieren" + demonstrierte Selektion; Teach-back bestätigt „Fertig"-Definition |
| `edge_cases` | yes | 0.80 | interpretation | Plan: Feature streut über REQs (Dünger), Kern-Journeys mehr-REQ, Marker-Drift via strict, Dublette |
| `scope_boundaries` | yes | 0.95 | specification | Authoritative operator answers (alle 6 Plan-Fragen + Teach-back, 2026-07-14) |

## Requirements

- **R1** — WHEN eine E2E-Testdatei dem Muster `test_req<NNN>_*.py` folgt, the conftest-Collection-Hook
  (`pytest_collection_modifyitems`) SHALL jedem enthaltenen Test **automatisch** einen REQ-Marker
  (`req<NNN>`) zuweisen, ohne dass die Testfunktion von Hand markiert werden muss.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "REQ + Feature-Achse (A+B) … Auto: filename test_req004_* -> @req004" (Operator 2026-07-14)
- **R2** — WHEN eine E2E-Testdatei eine Datei-Level-Feature-Konstante deklariert
  (Feature ∈ {`plant`, `watering`, `nutrient`, `harvest`, `calendar`, …}), the conftest-Hook SHALL
  jedem Test dieser Datei den entsprechenden **Feature-Marker** zuweisen, sodass feature-quere
  Selektion quer zu REQ-IDs möglich ist (z. B. Dünger über mehrere REQ-004-Dateien, Kern-Journeys
  über mehrere REQs).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "semantische Feature-Marker … quer zu REQs … Feature: 1 Datei-Level-Konstante" (Operator 2026-07-14)
- **R3** — WHEN pytest die E2E-Suite sammelt, the Konfiguration SHALL `--strict-markers` erzwingen
  und alle REQ- und Feature-Marker zentral registrieren (`pyproject.toml`/conftest), sodass ein
  unbekannter/vertippter Marker als harter Fehler auffällt.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: "Ja, strict + zentrale Registrierung" (Operator 2026-07-14)
- **R4** — WHEN ein E2E-Test eine TC-ID im Header/Docstring trägt (`TC-REQ-<NNN>-<lfd>`),
  the Test SHALL diese TC-ID via `record_property('tc_id', …)` maschinenlesbar ins generierte
  Protokoll heben, **ohne** die TC-ID zu einem Selektions-Marker zu machen.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "record_property + Dublette bereinigen … TC-ID … maschinenlesbar, ohne TC-ID zum Selektions-Marker zu machen" (Operator 2026-07-14)
- **R5** — WHEN der Abdeckungs-Detail-Check der fünf Kernfunktionen gegen `spec/e2e-testcases/TC-REQ-*.md`
  durchgeführt ist, the Ergebnis SHALL ein Report (unter `.audits/`) sein, der echte Lücken
  (fehlende/veraltete TCs) **benennt**; neue Tests zum Schließen der Lücken SHALL NICHT in dieser
  Iteration entstehen, sondern separaten Issues/Iterationen vorbehalten bleiben.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: "Mechanik + Lücken dokumentieren … Luecken NUR benannt … Separate Issues" (Operator 2026-07-14)
- **R6** — WHEN die Dublette `spec/test-cases/TC-REQ-001.md` (parallel zu `spec/e2e-testcases/TC-REQ-001.md`)
  angetroffen wird, the Iteration SHALL sie klären (entfernen oder mergen), sodass es eine
  eindeutige TC-Quelle gibt.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: "spec/test-cases/TC-REQ-001.md (Dublette) -> entfernen/mergen" (Operator 2026-07-14)
- **R7** — WHEN die Marker-Mechanik steht, the Iteration SHALL die Selektion demonstrieren
  (`pytest -m req004`, `-m watering`, `-m 'nutrient and smoke'`) und mindestens die betroffene
  Teilmenge lokal via `task test:e2e`/`run-e2e.sh` grün belegen; ein CI-Gate SHALL NICHT
  eingeführt werden.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: "Selektion demonstriert (-m watering …)" + Plan §Invarianten (kein E2E-CI-Gate) (Operator 2026-07-14)
- **R8** — WHILE die Suite erweitert wird, the Testcode/Marker-Mechanik SHALL NFR-003
  (Quellcode/Tests Englisch) und NFR-008a (Page-Object-Pattern, Screenshot-Checkpoints,
  Protokoll-Generierung) einhalten und den Selektions-Workflow in der Test-Doku beschreiben.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Plan §Invarianten + Teach-back (2026-07-14)

## Surviving assumptions / open risks

- **A1 (assumed)** — Die exakte Feature-Marker-Liste (`plant`, `watering`, `nutrient`, `harvest`,
  `calendar`) ist der Startsatz für die 5 Kernfunktionen; weitere Feature-Marker können beim
  Detail-Check ergänzt werden. Nicht per Teach-back einzeln bestätigt → beim Umsetzen verifizieren.
- **A2 (assumed)** — Die Marker-Struktur bleibt so gehalten, dass
  `nolte-engineering:release-regression-scope` sie später als Change→Test-Treiber nutzen könnte;
  diese Kopplung wird jetzt **nicht** gebaut.
- **R-Risk-1** — `--strict-markers` (R3) kann Alt-Marker/Alt-Tests brechen, falls irgendwo ein
  unregistrierter Marker existiert; Registrierung muss vollständig sein (inkl. der 4 Bestandsmarker
  `smoke`, `core_crud`, `requires_auth`, `requires_desktop`).
- **R-Risk-2 (edge_cases, c_d = 0.80)** — Datei-Level-Feature-Konstante (R2) setzt eine Konvention
  voraus, die in 75 Dateien konsistent gepflegt werden muss; ein fehlender/falscher Wert führt zu
  stiller Fehl-Selektion. Mitigation: Feature-Konstante optional + Detail-Check verifiziert Abdeckung.
- **R-Risk-3** — Der Abdeckungs-Report (R5) benennt Lücken, schließt sie nicht; Kernfunktionen
  bleiben ggf. unvollständig getestet, bis Folge-Issues abgearbeitet sind (bewusst akzeptiert).
