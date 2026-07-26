# TC-ID-Drift-Inventar — klassische E2E-Suite (`tests/e2e/test_req*.py`)

**Issue:** nolte/kamerplanter#775 — "chore(e2e): quantify and resolve the spec-to-test TC-ID drift in the classic suite"  
**Lane:** L6, Schritt 1 (nur Messung, keine Reparatur)  
**Datum:** 2026-07-26  
**Scope:** rein lesend gegen `tests/e2e/`, `spec/e2e-testcases/`, `scripts/check_bdd_traceability.py`. Keine Testdatei, keine Page-Object, kein Skript wurde verändert.

---

## Kopfzahlen (headline numbers)

Diese Auswertung misst **zwei verschiedene Kanäle**, weil sich während der Analyse herausstellte, dass es davon tatsächlich zwei im Quellcode gibt (siehe Befund 0 unten) — und die beiden ein grundlegend anderes Bild liefern:

- **naiv** — nur der von `tests/e2e/conftest.py::_tc_id_from_docstring` tatsächlich gelesene Kanal: die erste Zeile des Test-Docstrings, gescannt mit `conftest.py::_TC_ID_SCAN` und gegen `spec/e2e-testcases/`-Überschriften aufgelöst (`scripts/check_bdd_traceability.py::collect_spec_cases`, für beide legalen Schreibweisen `TC-NNN-NNN`/`TC-REQ-NNN-NNN`).
- **autoritativ** — zusätzlich ausgewertet: eine zweite, in ca. 86 % der Testfunktionen vorhandene, aber von **keinem** Werkzeug gelesene Zeile der Form `Spec: TC-NNN-NNN -- <Titel>` im Docstring-Fließtext (nicht die erste Zeile). Diese Zeile ist die vom jeweiligen Testautor tatsächlich verifizierte Spec-Referenz — und weicht in der überwältigenden Mehrheit der Fälle von der ID ab, die in der ersten Docstring-Zeile steht und die der Runtime-Kanal tatsächlich liest.

| # | Frage | naiv (Docstring-1.-Zeile) | autoritativ (`Spec:`-Zeile wo vorhanden, sonst Docstring-Fallback) |
|---|---|---:|---:|
| 1 | Claims, die auf eine Spec-Überschrift auflösen | 647 Claims → 634 verschiedene Spec-IDs | 670 Claims → 386 verschiedene Spec-IDs |
| 2 | Claims, die **nicht** auflösen (Waisen) | 67 | 16 |
| 3 | Spec-IDs, die von >1 Test beansprucht werden | 13 | 115 |
| 4 | Spec-IDs ganz ohne Test | 1539 von 2173 (kein Defekt) | 1787 von 2173 (kein Defekt) |
| 5 | Testfunktionen ganz ohne TC-ID im Docstring | 8 | 8 (identisch — kanalunabhängig) |
| 6 | Anzahl unterschiedlicher ID-Shapes | 5 (siehe unten) | — |

Grundgesamtheit: **722 Testfunktionen** in **76 klassischen Dateien** (`tests/e2e/test_req*.py`, ohne die eine `*_bdd.py`-Datei — siehe Befund 3). **2173 Spec-Testfälle** über **39 Dokumente** unter `spec/e2e-testcases/`.

**Warum die beiden Spalten so weit auseinanderliegen, ist selbst der wichtigste Befund dieser Analyse** (Befund 1 unten): Zeile 1 des Docstrings ist überwiegend eine rein test-lokale, pro Datei fortlaufende Zählung, die rein zufällig oft eine Zahl trifft, die *irgendein* Spec-Testfall der gleichen REQ auch trägt — ohne dass damit der *richtige* Testfall gemeint ist. Von 620 Testfunktionen, die eine `Spec:`-Zeile UND eine Docstring-Erst-Zeilen-ID tragen, stimmen die beiden nur in **4 Fällen** überein; in **616 Fällen widersprechen sie sich**.

---

## Befund 0 — die Spec selbst benutzt zwei Überschriften-Shapes

`scripts/check_bdd_traceability.py::collect_spec_cases` indiziert `spec/e2e-testcases/*.md` rein über die `## TC-<id>: <Titel>`-Überschrift, unabhängig von der konkreten Schreibweise. Dabei zeigt sich: **28 der 39 Spec-Dokumente** deklarieren ihre Testfälle als `## TC-NNN-NNN` (z. B. `TC-REQ-001.md` → `## TC-001-001`), aber **5 Dokumente deklarieren sie nativ als `## TC-REQ-NNN-NNN`** (mit REQ-Infix in der Überschrift selbst, nicht nur im Dateinamen):

- `spec/e2e-testcases/TC-REQ-005.md` (z. B. `### TC-REQ-005-001: …`)
- `spec/e2e-testcases/TC-REQ-008.md`
- `spec/e2e-testcases/TC-REQ-030.md`
- `spec/e2e-testcases/TC-REQ-034.md`
- `spec/e2e-testcases/TC-REQ-039.md`

Das bedeutet: Ein Test-Docstring mit `TC-REQ-005-001` ist für REQ-005 **korrekt buchstabiert**, obwohl er exakt dieselbe Form trägt wie die „test-lokalen" `TC-REQ-NNN-NNN`-IDs anderswo, die (siehe Befund 1) fast nie mit ihrer eigenen `Spec:`-Zeile übereinstimmen. Jede Reparatur (Lane 2) muss dies pro Dokument respektieren, sonst werden fünf Dokumente kaputtnormalisiert. `check_bdd_traceability.py::suggest_alternative` behandelt beide Schreibweisen bereits als gleichberechtigt für den Gherkin-Kanal; diese Analyse hat dieselbe Zwei-Schreibweisen-Logik für den docstring-Kanal reproduziert (`resolves()`).

---

## Befund 1 — die Docstring-Erst-Zeilen-ID ist überwiegend eine test-lokale Zählung, keine Spec-Referenz

Der entscheidende, vom Issue nicht antizipierte Befund: **826 Zeilen** in **60 der 76 Dateien** enthalten eine zweite, nicht-maschinenlesbare Annotation der Form

```
Spec: TC-001-006 -- Neue Botanische Familie erfolgreich erstellen (Dialog-Oeffnung).
```

im Docstring-Fließtext (nach der ersten Zeile — und damit unsichtbar für `conftest.py::_tc_id_from_docstring`, das laut eigenem Docstring nur „the first line" liest). Beispiel `tests/e2e/test_req001_botanical_family_create.py:36`:

```python
def test_open_create_dialog(...):
    """TC-REQ-001-013: Open the create dialog and verify form fields.

    Spec: TC-001-006 -- Neue Botanische Familie erfolgreich erstellen (Dialog-Oeffnung).
    """
```

Die Erst-Zeile trägt `TC-REQ-001-013` (normalisiert `TC-001-013` — existiert zufällig als Spec-Überschrift, "resolved" also naiv), der Autor selbst dokumentiert aber explizit, dass der **eigentlich gemeinte** Testfall `TC-001-006` ist. Das ist kein Einzelfall: von 620 Testfunktionen mit beiden Anmerkungen stimmen nur 4 überein, 616 widersprechen sich — d. h. die naive Auflösungsquote von 647 Claims ist zu >90 % eine **Zahlenkoinzidenz**, keine echte Traceability. Die Docstring-Erst-Zeile ist erkennbar eine reine fortlaufende Zählung pro Testdatei (`-013, -014, -015, -016, …`), die historisch parallel zur, aber unabhängig von der Spec-Nummerierung gewachsen ist; die `Spec:`-Zeile ist die tatsächlich vom Autor verifizierte Kreuzreferenz.

**Konsequenz für Lane 2 (Reparatur):** Diese `Spec:`-Zeilen sind bereits eine von Menschen erarbeitete Umsetzungstabelle für einen Großteil der Reconciliation-Arbeit — sie müssen nur an die Position gehoben werden, die die Werkzeuge lesen (oder ein neuer Docstring-/Marker-Kanal muss sie lesen), statt aus 0 rekonstruiert zu werden. Das senkt die Kosten von Option (a) unten erheblich.

**Einschränkung:** 65 Testfunktionen (in mehreren Dateien, u. a. `test_req002_standorte.py`, alle 16 in `test_req004_watering_log.py`, die acht "route reachable or skipped"-Stubs) tragen **keine** `Spec:`-Zeile — für diese existiert keine zweite, überprüfbare Quelle; die Docstring-Erst-Zeile ist hier die einzige Aufzeichnung, ob korrekt oder nicht.

Weiter zeigt sich eine **dritte Spur**: In 5 Dateien (`test_req005_hybrid_sensor.py`, `test_req025_privacy_settings.py`, `test_req027_light_mode.py`, `test_req028_mischkultur.py`, `test_req032_print.py`) referenziert die `Spec:`-Zeile nicht `spec/e2e-testcases/`, sondern direkt einen **Abschnitt des funktionalen Requirements** (`spec/req/REQ-XXX_*.md`), z. B.:

```
Spec: REQ-028 §7.1 -- Mischkultur-Partner-Panel ist Einstieg in die …
```

Diese Tests waren nie als `spec/e2e-testcases/`-Traceability gedacht — ihre naive „Auflösung" gegen eine `TC-REQ-005-001`-Überschrift ist ebenfalls reiner Zufall (siehe Befund 0: `TC-REQ-005.md` deklariert zufällig dieselbe Nummer). Das ist **kein Defekt**, sondern ein dritter, legitimer Traceability-Kanal außerhalb des Scopes von `spec/e2e-testcases/` — wird hier aber explizit gemeldet, weil er die naive Zählung in diesen 5 Dateien komplett verfälscht (37 Testfunktionen insgesamt tragen eine `Spec:`-Zeile ohne auswertbare TC-ID: 34 REQ-Abschnittsreferenzen + 2 explizite "(no direct spec TC)" + der Rest dokument-weite Verweise wie "TC-001" ohne Fallnummer in `test_req001_plant_instance.py`, ebenfalls ein ehrlicher Selbstbefund des Autors "kein präziser Spec-Fall").

---

## Befund 2 — `_tc_id_from_docstring` liest tatsächlich nur Zeile 1 (bestätigt, kein zusätzlicher Datenverlust)

Separat von Befund 1 geprüft: Enthält irgendeine Testfunktion eine TC-ID, die **weiter unten** im Docstring steht, aber **nicht** auf der ersten Zeile (die also für den Runtime-Kanal unsichtbar wäre, obwohl sie im weitesten Scan-Muster `_TC_ID_SCAN` läge)? **Ergebnis: 0.** Jede Testfunktion, die überhaupt eine `TC-…`-ID trägt, trägt sie auch auf Zeile 1. Der einzige tatsächlich „unsichtbare" Kanal ist die separat benannte `Spec:`-Zeile aus Befund 1 (die aber ohnehin kein `TC-…`-Shape auf Zeile 1 dupliziert, sondern eine andere ID nennt).

---

## Befund 3 — die eine `*_bdd.py`-Datei ist strukturell kein Docstring-Kanal-Kandidat

`tests/e2e/test_req004_watering_cross_view_consistency_bdd.py` matcht das Datei-Glob `test_req*.py`, ist aber die pytest-bdd-Step-Bindung des BDD-Proof-of-Concept (ADR-010). Ihre einzige `@scenario`-dekorierte Funktion (`test_watering_is_consistent_across_views`, Zeile 110) trägt zur Compile-Zeit einen literalen Docstring mit `TC-004-092`, der aber laut `tests/e2e/README.md` zur Laufzeit von `pytest_bdd.scenario` bedingungslos mit "<feature>: <scenario>" überschrieben wird — der Docstring-Kanal ist für diese Funktion strukturell tot; die TC-ID kommt zur Laufzeit stattdessen über den `@TC-004-092`-Marker (`conftest.py::_tc_id_from_markers`). Diese Datei ist daher **aus der 76er-Grundgesamtheit ausgeschlossen** — sie gehört zum Gherkin-Kanal, den `scripts/check_bdd_traceability.py` bereits abdeckt, nicht zum hier untersuchten Docstring-Kanal.

---

## Shape-Aufschlüsselung (die entscheidende Eingabe für die Schema-Entscheidung)

Gemessen an der Docstring-Erst-Zeile (der Shape, den `_TC_ID_SCAN` extrahiert), über alle 722 Testfunktionen:

| Shape | Anzahl | Beispiele (Datei:Zeile ID) |
|---|---:|---|
| `TC-REQ-NNN-NNN` (passt das *strikte* `TC_ID_PATTERN`, mit REQ-Infix) | 667 | `test_req001_botanical_family_create.py:36 TC-REQ-001-013`, `test_req001_botanical_family_create.py:52 TC-REQ-001-014` |
| `TC-REQ-NNN-Wxxx[Buchstabe]` (Buchstabe+Ziffern-Suffix, z. B. `-W001`, `-J079`) | 29 | `test_req001_core_lifecycle_journey.py:70 TC-REQ-001-J079`, `test_req004_watering_log.py:59 TC-REQ-004-W001` |
| `TC-REQ-NNN-XX-nnn[Buchstabe]` (Buchstaben-Gruppen-Suffix, z. B. `-PI-001`) | 16 | `test_req001_plant_instance.py:58 TC-REQ-001-PI-001`, `test_req001_plant_instance.py:81 TC-REQ-001-PI-002` |
| `TC-NNN-NNN` (spec-natives Kürzel ohne REQ-Infix, passt ebenfalls das strikte Pattern) | 1 | `test_req004_watering_cross_view_consistency.py:92 TC-004-092` (der klassische Zwilling des BDD-PoC) |
| `TC-REQ-NNN-NNNletter` (Fallnummer + einzelner Anhängebuchstabe, kein Infix) | 1 | `test_req024_invitation.py:157 TC-REQ-024-032b` |

Von den 667 „strikt geformten" IDs lösen 21 selbst naiv (also rein über Ziffernübereinstimmung) **nicht** auf:

- **14 in `test_req001_*.py`** (`TC-REQ-001-082` … `-095`, z. B. `test_req001_cross_entity.py:58,173,200,228`, `test_req001_datatable.py:114,136,155`, `test_req001_i18n.py:57,109,147`, `test_req001_seed_data.py:55,79,114,161`) liegen **oberhalb der höchsten in `spec/e2e-testcases/TC-REQ-001.md` deklarierten Fallnummer** (`TC-001-081`, Zeile 2239). Die Tests wurden offenbar nach dem letzten Spec-Update hinzugefügt, ohne dass die Spec-Datei um die entsprechenden Fälle ergänzt wurde — Test ist der Spec hier voraus, nicht umgekehrt.
- **7 in `test_req015_*.py`** (`TC-REQ-015-008` und `-009` in `test_req015_calendar.py:246,266`; `-015`..`-017` in `test_req015_calendar.py:424,448,479`; `-064`/`-065` in `test_req015_season_overview.py:151,187`) fallen in **Nummerierungslücken innerhalb der Spec-eigenen Abschnittsblöcke** (die Spec nummeriert bewusst in Zehnerblöcken: `001–007`, `010–014`, `020–024`, `030–036`, …, mit Reserve-Lücken für künftige Fälle). Die Testautoren haben hier offenbar eine durchgehende statt einer blockweisen Nummerierung angenommen.

Die 29 `W`/`J`-Suffix- und 16 `PI`-Gruppen-Suffix-IDs sind durchgängig test-lokale Erfindungen ohne Entsprechung im strikten Shape — das ist exakt die im Issue benannte Drift-Klasse.

---

## Duplikat-Claims

**Naiv:** 13 Spec-IDs werden von je 2 Tests beansprucht — überwiegend Zufallstreffer zweier unabhängiger test-lokaler Zählungen auf dieselbe Zahl (z. B. `TC-004-043`, beansprucht von `test_req004_feeding_events.py:108` UND `test_req004_nutrient_plan.py:221`, obwohl inhaltlich beide Tests nichts miteinander zu tun haben).

**Autoritativ** (`Spec:`-Zeile als Wahrheit, 115 Spec-IDs von >1 Test beansprucht) zeigt ein anderes, **erwartbares** Muster: Viele Spec-Testfälle sind grobkörnige User-Journey-Szenarien, die die klassische Suite in mehrere feinkörnige UI-Einzelassertionen zerlegt. Beispiel `TC-001-030` ("Companion Planting") wird von 10 Tests in `test_req001_companion_planting.py`, `test_req001_cross_entity.py`, `test_req001_navigation.py` und `test_req001_species.py` beansprucht — jeder prüft einen anderen Teilaspekt (Auswahl, Hinzufügen, Leerzustand, Navigation, Dropdown-Filter …) desselben Spec-Szenarios. Das ist nach der Logik, die `check_bdd_traceability.py` für die Gherkin-Seite bereits anwendet (die Rückrichtung "Fall ohne Szenario" ist kein Defekt), ebenfalls **kein Defekt**, sondern ein Granularitäts-Unterschied Spec-vs-Test, der bei einer Reconciliation **bewusst zugelassen** werden muss — eine 1:1-Kardinalitätsregel (wie sie `check_bdd_traceability.py` für Gherkin-Szenarien in die andere Richtung nicht erzwingt) würde hier 115 falsche Alarme auslösen.

Vollständige Liste (115 Einträge, `Spec:`-Zeile als Quelle wo vorhanden, sonst Docstring-Fallback):

| Spec-TC-ID | Anzahl Claims | Test-Fundstellen (Datei:Zeile) |
|---|---:|---|
| TC-001-001 | 6 | `test_req001_botanical_family_list.py:34`; `test_req001_botanical_family_list.py:172`; `test_req001_datatable.py:92`; `test_req001_datatable.py:114`; `test_req001_datatable.py:136`; `test_req001_navigation.py:38` |
| TC-001-003 | 3 | `test_req001_botanical_family_list.py:62`; `test_req001_botanical_family_list.py:83`; `test_req001_botanical_family_list.py:122` |
| TC-001-005 | 4 | `test_req001_botanical_family_detail.py:49`; `test_req001_botanical_family_list.py:150`; `test_req001_datatable.py:66`; `test_req001_datatable.py:155` |
| TC-001-006 | 4 | `test_req001_botanical_family_create.py:36`; `test_req001_botanical_family_create.py:52`; `test_req001_botanical_family_create.py:127`; `test_req001_cross_entity.py:58` |
| TC-001-012 | 2 | `test_req001_botanical_family_create.py:151`; `test_req001_botanical_family_detail.py:95` |
| TC-001-019 | 2 | `test_req001_navigation.py:58`; `test_req001_species.py:43` |
| TC-001-025 | 5 | `test_req001_cross_entity.py:58`; `test_req001_cross_entity.py:173`; `test_req001_species.py:85`; `test_req001_species.py:101`; `test_req001_species.py:138` |
| TC-001-030 | 10 | `test_req001_companion_planting.py:32`; `test_req001_companion_planting.py:63`; `test_req001_companion_planting.py:95`; `test_req001_companion_planting.py:125`; `test_req001_companion_planting.py:159`; `test_req001_companion_planting.py:181`; `test_req001_cross_entity.py:200`; `test_req001_navigation.py:78`; `test_req001_species.py:61`; `test_req001_species.py:161` |
| TC-001-037 | 2 | `test_req001_cross_entity.py:58`; `test_req001_cultivar.py:97` |
| TC-001-047 | 5 | `test_req001_cross_entity.py:58`; `test_req001_lifecycle.py:61`; `test_req001_lifecycle.py:79`; `test_req001_lifecycle.py:108`; `test_req001_lifecycle.py:313` |
| TC-001-048 | 5 | `test_req001_cross_entity.py:58`; `test_req001_lifecycle.py:137`; `test_req001_lifecycle.py:158`; `test_req001_lifecycle.py:198`; `test_req001_lifecycle.py:233` |
| TC-001-050 | 7 | `test_req001_crop_rotation.py:31`; `test_req001_crop_rotation.py:56`; `test_req001_crop_rotation.py:94`; `test_req001_crop_rotation.py:122`; `test_req001_crop_rotation.py:148`; `test_req001_cross_entity.py:228`; `test_req001_navigation.py:98` |
| TC-001-053 | 3 | `test_req001_i18n.py:57`; `test_req001_i18n.py:109`; `test_req001_i18n.py:147` |
| TC-001-054 | 3 | `test_req001_seed_data.py:55`; `test_req001_seed_data.py:79`; `test_req001_seed_data.py:114` |
| TC-001-068 | 3 | `test_req001_botanical_family_detail.py:170`; `test_req001_error_handling.py:85`; `test_req001_navigation.py:118` |
| TC-002-004 | 2 | `test_req002_standorte.py:194`; `test_req002_standorte.py:340` |
| TC-002-010 | 3 | `test_req002_standorte.py:315`; `test_req002_standorte.py:395`; `test_req002_standorte.py:468` |
| TC-002-012 | 2 | `test_req002_standorte.py:364`; `test_req002_standorte.py:548` |
| TC-002-021 | 2 | `test_req002_standorte.py:525`; `test_req002_standorte.py:605` |
| TC-002-022 | 2 | `test_req002_standorte.py:633`; `test_req002_standorte.py:675` |
| TC-003-010 | 2 | `test_req003_phasensteuerung.py:433`; `test_req003_phasensteuerung.py:855` |
| TC-003-019 | 11 | `test_req003_phasensteuerung.py:267`; `test_req003_phasensteuerung.py:389`; `test_req003_phasensteuerung.py:411`; `test_req003_phasensteuerung.py:506`; `test_req003_phasensteuerung.py:540`; `test_req003_phasensteuerung.py:571`; `test_req003_phasensteuerung.py:602`; `test_req003_phasensteuerung.py:664`; `test_req003_phasensteuerung.py:696`; `test_req003_phasensteuerung.py:730`; `test_req003_phasensteuerung.py:936` |
| TC-003-021 | 2 | `test_req003_phasensteuerung.py:775`; `test_req003_phasensteuerung.py:816` |
| TC-003-023 | 2 | `test_req003_phasensteuerung.py:478`; `test_req003_phasensteuerung.py:890` |
| TC-003-024 | 3 | `test_req003_phasensteuerung.py:322`; `test_req003_phasensteuerung.py:347`; `test_req003_phasensteuerung.py:368` |
| TC-003-032 | 5 | `test_req003_phasensteuerung.py:109`; `test_req003_phasensteuerung.py:126`; `test_req003_phasensteuerung.py:150`; `test_req003_phasensteuerung.py:197`; `test_req003_phasensteuerung.py:290` |
| TC-004-001 | 5 | `test_req004_fertilizer.py:68`; `test_req004_fertilizer.py:85`; `test_req004_fertilizer.py:108`; `test_req004_fertilizer.py:177`; `test_req004_fertilizer.py:218` |
| TC-004-002 | 2 | `test_req004_fertilizer.py:125`; `test_req004_fertilizer.py:149` |
| TC-004-006 | 6 | `test_req004_fertilizer.py:273`; `test_req004_fertilizer.py:294`; `test_req004_fertilizer.py:325`; `test_req004_fertilizer.py:396`; `test_req004_fertilizer.py:434`; `test_req004_fertilizer.py:452` |
| TC-004-008 | 7 | `test_req004_fertilizer.py:240`; `test_req004_fertilizer.py:500`; `test_req004_fertilizer.py:525`; `test_req004_fertilizer.py:550`; `test_req004_fertilizer.py:602`; `test_req004_fertilizer.py:631`; `test_req004_fertilizer.py:662` |
| TC-004-012 | 10 | `test_req004_nutrient_plan.py:66`; `test_req004_nutrient_plan.py:83`; `test_req004_nutrient_plan.py:145`; `test_req004_nutrient_plan.py:171`; `test_req004_nutrient_plan.py:188`; `test_req004_nutrient_plan.py:424`; `test_req004_nutrient_plan.py:448`; `test_req004_nutrient_plan.py:531`; `test_req004_nutrient_plan.py:558`; `test_req004_nutrient_plan.py:588` |
| TC-004-013 | 2 | `test_req004_nutrient_plan.py:100`; `test_req004_nutrient_plan.py:125` |
| TC-004-015 | 5 | `test_req004_nutrient_plan.py:221`; `test_req004_nutrient_plan.py:242`; `test_req004_nutrient_plan.py:273`; `test_req004_nutrient_plan.py:329`; `test_req004_nutrient_plan.py:361` |
| TC-004-028 | 13 | `test_req004_nutrient_calculations.py:112`; `test_req004_nutrient_calculations.py:129`; `test_req004_nutrient_calculations.py:146`; `test_req004_nutrient_calculations.py:163`; `test_req004_nutrient_calculations.py:317`; `test_req004_nutrient_calculations.py:341`; `test_req004_nutrient_calculations.py:366`; `test_req004_nutrient_calculations.py:388`; `test_req004_nutrient_calculations.py:416`; `test_req004_nutrient_calculations.py:447`; `test_req004_nutrient_calculations.py:479`; `test_req004_nutrient_calculations.py:507`; `test_req004_nutrient_calculations.py:533` |
| TC-004-031 | 3 | `test_req004_nutrient_calculations.py:194`; `test_req004_nutrient_calculations.py:226`; `test_req004_nutrient_calculations.py:283` |
| TC-004-032 | 4 | `test_req004_nutrient_calculations.py:572`; `test_req004_nutrient_calculations.py:601`; `test_req004_nutrient_calculations.py:626`; `test_req004_nutrient_calculations.py:645` |
| TC-006-001 | 3 | `test_req006_navigation.py:191`; `test_req006_task_queue.py:86`; `test_req006_task_queue.py:106` |
| TC-006-005 | 3 | `test_req006_task_queue.py:159`; `test_req006_task_queue.py:184`; `test_req006_task_queue.py:212` |
| TC-006-006 | 3 | `test_req006_task_detail.py:190`; `test_req006_task_detail.py:247`; `test_req006_task_queue.py:261` |
| TC-006-008 | 2 | `test_req006_task_detail.py:278`; `test_req006_task_queue.py:319` |
| TC-006-009 | 2 | `test_req006_task_queue.py:355`; `test_req006_task_queue.py:389` |
| TC-006-019 | 4 | `test_req006_navigation.py:59`; `test_req006_task_detail.py:56`; `test_req006_task_detail.py:110`; `test_req006_task_detail.py:316` |
| TC-006-020 | 3 | `test_req006_navigation.py:106`; `test_req006_task_detail.py:84`; `test_req006_task_detail.py:156` |
| TC-006-034 | 6 | `test_req006_navigation.py:217`; `test_req006_workflow.py:50`; `test_req006_workflow.py:72`; `test_req006_workflow.py:95`; `test_req006_workflow.py:116`; `test_req006_workflow.py:138` |
| TC-006-039 | 5 | `test_req006_navigation.py:150`; `test_req006_workflow.py:213`; `test_req006_workflow.py:245`; `test_req006_workflow.py:282`; `test_req006_workflow.py:323` |
| TC-007-001 | 4 | `test_req007_harvest_list.py:51`; `test_req007_harvest_list.py:72`; `test_req007_harvest_list.py:94`; `test_req007_harvest_list.py:119` |
| TC-007-007 | 2 | `test_req007_harvest_list.py:281`; `test_req007_harvest_list.py:387` |
| TC-007-014 | 2 | `test_req007_harvest_detail.py:72`; `test_req007_harvest_detail.py:100` |
| TC-007-017 | 2 | `test_req007_harvest_detail.py:175`; `test_req007_harvest_detail.py:225` |
| TC-007-022 | 2 | `test_req007_harvest_detail.py:304`; `test_req007_harvest_detail.py:371` |
| TC-007-028 | 2 | `test_req007_harvest_detail.py:456`; `test_req007_harvest_detail.py:484` |
| TC-009-001 | 4 | `test_req009_dashboard.py:30`; `test_req009_dashboard.py:46`; `test_req009_dashboard.py:62`; `test_req009_dashboard.py:78` |
| TC-010-001 | 4 | `test_req010_pest_list.py:47`; `test_req010_pest_list.py:70`; `test_req010_pest_list.py:91`; `test_req010_pest_list.py:217` |
| TC-010-003 | 3 | `test_req010_pest_list.py:108`; `test_req010_pest_list.py:160`; `test_req010_pest_list.py:188` |
| TC-010-013 | 7 | `test_req010_disease_list.py:44`; `test_req010_disease_list.py:67`; `test_req010_disease_list.py:88`; `test_req010_disease_list.py:105`; `test_req010_disease_list.py:134`; `test_req010_disease_list.py:154`; `test_req010_disease_list.py:182` |
| TC-010-016 | 2 | `test_req010_disease_list.py:210`; `test_req010_disease_list.py:315` |
| TC-010-019 | 7 | `test_req010_treatment_list.py:45`; `test_req010_treatment_list.py:68`; `test_req010_treatment_list.py:86`; `test_req010_treatment_list.py:103`; `test_req010_treatment_list.py:132`; `test_req010_treatment_list.py:152`; `test_req010_treatment_list.py:180` |
| TC-010-023 | 2 | `test_req010_treatment_list.py:208`; `test_req010_treatment_list.py:322` |
| TC-010-047 | 3 | `test_req010_ipm_navigation.py:49`; `test_req010_ipm_navigation.py:115`; `test_req010_ipm_navigation.py:148` |
| TC-010-048 | 2 | `test_req010_ipm_navigation.py:71`; `test_req010_ipm_navigation.py:93` |
| TC-012-004 | 2 | `test_req012_import.py:131`; `test_req012_import.py:568` |
| TC-012-005 | 2 | `test_req012_import.py:150`; `test_req012_import.py:594` |
| TC-013-001 | 4 | `test_req013_planting_run.py:62`; `test_req013_planting_run.py:81`; `test_req013_planting_run.py:101`; `test_req013_planting_run.py:226` |
| TC-013-003 | 3 | `test_req013_planting_run.py:143`; `test_req013_planting_run.py:173`; `test_req013_planting_run.py:202` |
| TC-013-005 | 3 | `test_req013_planting_run.py:253`; `test_req013_planting_run.py:273`; `test_req013_planting_run.py:354` |
| TC-013-020 | 2 | `test_req013_planting_run.py:404`; `test_req013_planting_run.py:495` |
| TC-013-026 | 2 | `test_req013_planting_run.py:523`; `test_req013_planting_run.py:557` |
| TC-013-037 | 2 | `test_req013_planting_run.py:602`; `test_req013_planting_run.py:634` |
| TC-013-050 | 2 | `test_req013_planting_run.py:429`; `test_req013_planting_run.py:454` |
| TC-014-001 | 4 | `test_req014_tank.py:69`; `test_req014_tank.py:88`; `test_req014_tank.py:108`; `test_req014_tank.py:233` |
| TC-014-003 | 3 | `test_req014_tank.py:150`; `test_req014_tank.py:180`; `test_req014_tank.py:209` |
| TC-014-006 | 3 | `test_req014_tank.py:334`; `test_req014_tank.py:373`; `test_req014_tank.py:406` |
| TC-014-010 | 3 | `test_req014_tank.py:442`; `test_req014_tank.py:467`; `test_req014_tank.py:492` |
| TC-014-011 | 2 | `test_req014_tank.py:521`; `test_req014_tank.py:552` |
| TC-014-019 | 3 | `test_req014_tank.py:591`; `test_req014_tank.py:621`; `test_req014_tank.py:663` |
| TC-014-024 | 3 | `test_req014_tank.py:708`; `test_req014_tank.py:738`; `test_req014_tank.py:780` |
| TC-014-037 | 2 | `test_req014_tank.py:858`; `test_req014_tank.py:890` |
| TC-015-002 | 2 | `test_req015_calendar.py:100`; `test_req015_calendar.py:156` |
| TC-015-004 | 2 | `test_req015_calendar.py:185`; `test_req015_calendar.py:266` |
| TC-015-010 | 2 | `test_req015_calendar.py:297`; `test_req015_calendar.py:315` |
| TC-015-030 | 2 | `test_req015_calendar.py:398`; `test_req015_calendar.py:448` |
| TC-015-040 | 3 | `test_req015_sowing_calendar.py:55`; `test_req015_sowing_calendar.py:96`; `test_req015_sowing_calendar.py:246` |
| TC-015-046 | 4 | `test_req015_sowing_calendar.py:148`; `test_req015_sowing_calendar.py:165`; `test_req015_sowing_calendar.py:192`; `test_req015_sowing_calendar.py:211` |
| TC-015-060 | 4 | `test_req015_season_overview.py:53`; `test_req015_season_overview.py:81`; `test_req015_season_overview.py:105`; `test_req015_season_overview.py:151` |
| TC-019-001 | 4 | `test_req019_substrate.py:60`; `test_req019_substrate.py:79`; `test_req019_substrate.py:103`; `test_req019_substrate.py:220` |
| TC-019-003 | 2 | `test_req019_substrate.py:145`; `test_req019_substrate.py:196` |
| TC-019-007 | 3 | `test_req019_substrate.py:248`; `test_req019_substrate.py:318`; `test_req019_substrate.py:353` |
| TC-019-015 | 2 | `test_req019_substrate.py:390`; `test_req019_substrate.py:423` |
| TC-019-018 | 2 | `test_req019_substrate.py:496`; `test_req019_substrate.py:564` |
| TC-020-001 | 2 | `test_req020_onboarding_wizard.py:103`; `test_req020_onboarding_wizard.py:915` |
| TC-022-001 | 4 | `test_req022_pflege_dashboard.py:81`; `test_req022_pflege_dashboard.py:101`; `test_req022_pflege_dashboard.py:157`; `test_req022_pflege_dashboard.py:330` |
| TC-022-009 | 5 | `test_req022_pflege_dashboard.py:193`; `test_req022_pflege_dashboard.py:218`; `test_req022_pflege_dashboard.py:246`; `test_req022_pflege_dashboard.py:274`; `test_req022_pflege_dashboard.py:302` |
| TC-022-012 | 6 | `test_req022_pflege_dashboard.py:355`; `test_req022_pflege_dashboard.py:455`; `test_req022_pflege_dashboard.py:484`; `test_req022_pflege_dashboard.py:511`; `test_req022_pflege_dashboard.py:538`; `test_req022_pflege_dashboard.py:575` |
| TC-022-016 | 3 | `test_req022_pflege_dashboard.py:382`; `test_req022_pflege_dashboard.py:619`; `test_req022_pflege_dashboard.py:649` |
| TC-022-018 | 7 | `test_req022_care_profile.py:100`; `test_req022_care_profile.py:129`; `test_req022_care_profile.py:153`; `test_req022_care_profile.py:447`; `test_req022_care_profile.py:511`; `test_req022_care_profile.py:541`; `test_req022_pflege_dashboard.py:409` |
| TC-022-019 | 2 | `test_req022_care_profile.py:190`; `test_req022_care_profile.py:479` |
| TC-022-021 | 2 | `test_req022_care_profile.py:214`; `test_req022_care_profile.py:238` |
| TC-023-001 | 2 | `test_req023_register.py:52`; `test_req023_register.py:78` |
| TC-023-006 | 2 | `test_req023_login.py:356`; `test_req023_register.py:232` |
| TC-023-007 | 2 | `test_req023_email_verification.py:45`; `test_req023_email_verification.py:169` |
| TC-023-008 | 3 | `test_req023_email_verification.py:75`; `test_req023_email_verification.py:107`; `test_req023_email_verification.py:142` |
| TC-023-009 | 2 | `test_req023_login.py:59`; `test_req023_login.py:88` |
| TC-023-013 | 2 | `test_req023_login.py:193`; `test_req023_login.py:234` |
| TC-023-020 | 2 | `test_req023_password_reset.py:58`; `test_req023_password_reset.py:87` |
| TC-023-026 | 2 | `test_req023_account_settings.py:61`; `test_req023_account_settings.py:254` |
| TC-023-029 | 2 | `test_req023_account_settings.py:147`; `test_req023_account_settings.py:170` |
| TC-024-003 | 6 | `test_req024_navigation.py:110`; `test_req024_navigation.py:134`; `test_req024_tenant_create.py:69`; `test_req024_tenant_create.py:93`; `test_req024_tenant_create.py:143`; `test_req024_tenant_create.py:249` |
| TC-024-005 | 2 | `test_req024_tenant_create.py:199`; `test_req024_tenant_create.py:224` |
| TC-024-008 | 6 | `test_req024_tenant_switcher.py:63`; `test_req024_tenant_switcher.py:86`; `test_req024_tenant_switcher.py:114`; `test_req024_tenant_switcher.py:141`; `test_req024_tenant_switcher.py:165`; `test_req024_tenant_switcher.py:184` |
| TC-024-012 | 5 | `test_req024_navigation.py:86`; `test_req024_navigation.py:134`; `test_req024_tenant_settings.py:67`; `test_req024_tenant_settings.py:91`; `test_req024_tenant_settings.py:114` |
| TC-024-015 | 3 | `test_req024_tenant_settings.py:145`; `test_req024_tenant_settings.py:170`; `test_req024_tenant_settings.py:199` |
| TC-024-022 | 3 | `test_req024_tenant_settings.py:227`; `test_req024_tenant_settings.py:251`; `test_req024_tenant_settings.py:301` |
| TC-024-023 | 2 | `test_req024_tenant_settings.py:275`; `test_req024_tenant_settings.py:334` |
| TC-024-025 | 2 | `test_req024_invitation.py:60`; `test_req024_invitation.py:196` |
| TC-024-026 | 7 | `test_req024_invitation.py:84`; `test_req024_invitation.py:119`; `test_req024_invitation.py:157`; `test_req024_navigation.py:174`; `test_req024_navigation.py:198`; `test_req024_navigation.py:227`; `test_req024_navigation.py:256` |

---

## Verwaiste Claims — autoritative Sicht (16, alle in einer Datei)

Nach Anwendung der `Spec:`-Zeile als Wahrheit bleiben nur **16 nicht auflösende Claims übrig, ausnahmslos in `tests/e2e/test_req004_watering_log.py`** — die komplette `W`-Suffix-Testfamilie dieser einen Datei trägt weder eine gültige, auf eine Spec-Überschrift auflösende ID noch eine `Spec:`-Kreuzreferenz. Für diese 16 Fälle existiert **keinerlei** Aufzeichnung (weder maschinenlesbar noch im Fließtext), welchem Spec-Testfall sie tatsächlich entsprechen — das ist der einzige Fund dieser Analyse, der eine echte, nicht durch eine zweite Quelle auflösbare Traceability-Lücke ist:

```
('tests/e2e/test_req004_watering_log.py', 59, 'test_list_page_renders_with_correct_testid', 'TC-REQ-004-W001', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 80, 'test_create_button_is_visible', 'TC-REQ-004-W002', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 101, 'test_list_displays_data_table_or_empty_state', 'TC-REQ-004-W001b', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 125, 'test_showing_count_when_rows_exist', 'TC-REQ-004-W001c', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 156, 'test_create_dialog_opens_on_button_click', 'TC-REQ-004-W003', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 189, 'test_create_watering_log_happy_path', 'TC-REQ-004-W004', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 246, 'test_create_dialog_validation_volume_required', 'TC-REQ-004-W005', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 284, 'test_create_dialog_cancel_closes_without_saving', 'TC-REQ-004-W006', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 319, 'test_create_dialog_add_fertilizer_button', 'TC-REQ-004-W004b', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 356, 'test_search_filters_table_rows', 'TC-REQ-004-W007', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 398, 'test_click_row_navigates_to_detail', 'TC-REQ-004-W008', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 431, 'test_detail_page_has_two_tabs', 'TC-REQ-004-W009', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 460, 'test_detail_page_shows_measurement_cards', 'TC-REQ-004-W009b', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 489, 'test_detail_page_has_analyze_runoff_button', 'TC-REQ-004-W009c', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 517, 'test_detail_page_delete_dialog_opens', 'TC-REQ-004-W009d', 'docstring-only')
('tests/e2e/test_req004_watering_log.py', 550, 'test_detail_page_edit_tab_shows_form', 'TC-REQ-004-W009e', 'docstring-only')
```

---

## Per-Datei-Tabelle

Vollständige Aufschlüsselung über alle 76 klassischen Dateien (`*_bdd.py` ausgeschlossen, siehe Befund 3):

| Datei | Testfunktionen | naiv aufgelöst | naiv verwaist | ohne TC-ID | autoritativ aufgelöst (Claims) | autoritativ verwaist |
|---|---:|---:|---:|---:|---:|---:|
| `test_req001_botanical_family_create.py` | 9 | 9 | 0 | 0 | 9 | 0 |
| `test_req001_botanical_family_detail.py` | 5 | 5 | 0 | 0 | 5 | 0 |
| `test_req001_botanical_family_list.py` | 7 | 7 | 0 | 0 | 7 | 0 |
| `test_req001_companion_planting.py` | 6 | 6 | 0 | 0 | 6 | 0 |
| `test_req001_core_lifecycle_journey.py` | 3 | 0 | 3 | 0 | 3 | 0 |
| `test_req001_crop_rotation.py` | 5 | 5 | 0 | 0 | 5 | 0 |
| `test_req001_cross_entity.py` | 4 | 0 | 4 | 0 | 8 | 0 |
| `test_req001_cultivar.py` | 5 | 5 | 0 | 0 | 5 | 0 |
| `test_req001_datatable.py` | 6 | 3 | 3 | 0 | 6 | 0 |
| `test_req001_error_handling.py` | 3 | 3 | 0 | 0 | 1 | 0 |
| `test_req001_i18n.py` | 3 | 0 | 3 | 0 | 3 | 0 |
| `test_req001_lifecycle.py` | 8 | 8 | 0 | 0 | 8 | 0 |
| `test_req001_navigation.py` | 5 | 5 | 0 | 0 | 6 | 0 |
| `test_req001_plant_instance.py` | 16 | 0 | 16 | 0 | 0 | 0 |
| `test_req001_seed_data.py` | 4 | 0 | 4 | 0 | 4 | 0 |
| `test_req001_species.py` | 9 | 9 | 0 | 0 | 9 | 0 |
| `test_req002_standorte.py` | 35 | 35 | 0 | 0 | 35 | 0 |
| `test_req003_phasensteuerung.py` | 33 | 30 | 3 | 0 | 33 | 0 |
| `test_req004_core_lifecycle_journey.py` | 3 | 0 | 3 | 0 | 3 | 0 |
| `test_req004_feeding_events.py` | 14 | 14 | 0 | 0 | 14 | 0 |
| `test_req004_fertilizer.py` | 23 | 23 | 0 | 0 | 23 | 0 |
| `test_req004_nutrient_calculations.py` | 21 | 21 | 0 | 0 | 21 | 0 |
| `test_req004_nutrient_plan.py` | 21 | 21 | 0 | 0 | 21 | 0 |
| `test_req004_watering_cross_view_consistency.py` | 1 | 1 | 0 | 0 | 1 | 0 |
| `test_req004_watering_log.py` | 16 | 0 | 16 | 0 | 0 | 16 |
| `test_req005_hybrid_sensor.py` | 3 | 3 | 0 | 0 | 0 | 0 |
| `test_req006_core_lifecycle_journey.py` | 2 | 0 | 2 | 0 | 2 | 0 |
| `test_req006_navigation.py` | 5 | 5 | 0 | 0 | 5 | 0 |
| `test_req006_task_detail.py` | 9 | 9 | 0 | 0 | 9 | 0 |
| `test_req006_task_queue.py` | 18 | 18 | 0 | 0 | 18 | 0 |
| `test_req006_workflow.py` | 10 | 10 | 0 | 0 | 10 | 0 |
| `test_req007_harvest_detail.py` | 15 | 15 | 0 | 0 | 16 | 0 |
| `test_req007_harvest_list.py` | 14 | 14 | 0 | 0 | 14 | 0 |
| `test_req007_harvest_readiness.py` | 3 | 3 | 0 | 0 | 3 | 0 |
| `test_req008_post_harvest.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req009_dashboard.py` | 4 | 4 | 0 | 0 | 4 | 0 |
| `test_req010_disease_list.py` | 10 | 10 | 0 | 0 | 10 | 0 |
| `test_req010_ipm_navigation.py` | 5 | 5 | 0 | 0 | 5 | 0 |
| `test_req010_pest_list.py` | 13 | 13 | 0 | 0 | 13 | 0 |
| `test_req010_treatment_list.py` | 11 | 11 | 0 | 0 | 11 | 0 |
| `test_req012_import.py` | 17 | 17 | 0 | 0 | 17 | 0 |
| `test_req013_planting_run.py` | 23 | 23 | 0 | 0 | 23 | 0 |
| `test_req014_tank.py` | 30 | 30 | 0 | 0 | 30 | 0 |
| `test_req015_calendar.py` | 17 | 12 | 5 | 0 | 17 | 0 |
| `test_req015_season_overview.py` | 6 | 4 | 2 | 0 | 6 | 0 |
| `test_req015_sowing_calendar.py` | 9 | 9 | 0 | 0 | 9 | 0 |
| `test_req017_propagation.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req018_actuators.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req019_substrate.py` | 20 | 20 | 0 | 0 | 19 | 0 |
| `test_req020_onboarding_steps.py` | 6 | 6 | 0 | 0 | 6 | 0 |
| `test_req020_onboarding_wizard.py` | 27 | 27 | 0 | 0 | 27 | 0 |
| `test_req021_experience_level.py` | 20 | 20 | 0 | 0 | 21 | 0 |
| `test_req022_care_profile.py` | 17 | 17 | 0 | 0 | 18 | 0 |
| `test_req022_core_lifecycle_journey.py` | 2 | 0 | 2 | 0 | 2 | 0 |
| `test_req022_pflege_dashboard.py` | 21 | 21 | 0 | 0 | 21 | 0 |
| `test_req023_account_settings.py` | 7 | 7 | 0 | 0 | 7 | 0 |
| `test_req023_email_verification.py` | 5 | 5 | 0 | 0 | 5 | 0 |
| `test_req023_login.py` | 10 | 10 | 0 | 0 | 10 | 0 |
| `test_req023_password_reset.py` | 7 | 7 | 0 | 0 | 7 | 0 |
| `test_req023_register.py` | 6 | 6 | 0 | 0 | 6 | 0 |
| `test_req024_invitation.py` | 5 | 4 | 1 | 0 | 5 | 0 |
| `test_req024_navigation.py` | 7 | 7 | 0 | 0 | 8 | 0 |
| `test_req024_tenant_create.py` | 7 | 7 | 0 | 0 | 7 | 0 |
| `test_req024_tenant_settings.py` | 11 | 11 | 0 | 0 | 11 | 0 |
| `test_req024_tenant_switcher.py` | 8 | 8 | 0 | 0 | 8 | 0 |
| `test_req025_privacy_settings.py` | 2 | 2 | 0 | 0 | 0 | 0 |
| `test_req026_aquaponik.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req027_light_mode.py` | 3 | 3 | 0 | 0 | 0 | 0 |
| `test_req028_mischkultur.py` | 6 | 6 | 0 | 0 | 0 | 0 |
| `test_req029_recognition.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req030_notifications.py` | 14 | 14 | 0 | 0 | 14 | 0 |
| `test_req031_ki_assistent.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req032_print.py` | 4 | 4 | 0 | 0 | 0 | 0 |
| `test_req034_plant_gallery.py` | 10 | 10 | 0 | 0 | 10 | 0 |
| `test_req035_glossar.py` | 1 | 0 | 0 | 1 | 0 | 0 |
| `test_req036_diagnose.py` | 1 | 0 | 0 | 1 | 0 | 0 |

---

## Empfehlung

**Empfehlung: Option (a) — Test-lokale IDs auf das Spec-Schema `TC-NNN-NNN` (bzw. `TC-REQ-NNN-NNN` für die 5 nativ so schreibenden Dokumente, Befund 0) rekonziliieren — nicht Option (b).**

Begründung, an den gemessenen Zahlen aufgehängt:

1. **Die Rekonziliationsarbeit ist bereits zu 86 % vorgeleistet.** 620 von 722 Testfunktionen tragen bereits eine von Menschenhand verifizierte `Spec: TC-NNN-NNN`-Kreuzreferenz (Befund 1) — Lane 2 muss diese überwiegend nur an die Stelle heben, die die Tooling-Kette liest (Docstring-Erstzeile oder ein neuer Marker-Kanal analog zum BDD-Vorbild `_tc_id_from_markers`), statt sie von Grund auf zu recherchieren. Nur für 65 Testfunktionen (dominant `test_req002_standorte.py` und `test_req004_watering_log.py`) fehlt diese Quelle komplett und erfordert echte manuelle Zuordnung.

2. **Ein zweites Schema (Option b) würde die falsche Sache legitimieren.** Der dominante Drift ist nicht "die Test-Suite hat ein zweites, gleichwertiges ID-Schema erfunden" — er ist "die Erstzeilen-ID ist eine test-lokale Zählung, die in 616 von 620 überprüfbaren Fällen NICHT das meint, was der Test tatsächlich testet." Das als zweites legitimes Schema zu erklären hieße, eine Zahlenkoinzidenz zur Spezifikation zu erheben.

3. **Kosten Option (a):** ~620 Docstrings (in ca. 60 Dateien) brauchen eine mechanische Erstzeilen-Korrektur (die `Spec:`-Zeile ihres eigenen Docstrings nach oben ziehen — pro Fall bereits bekannt, kein Recherche-Aufwand) + ~65 Testfunktionen ohne jede Referenz brauchen manuelle Spec-Zuordnung (überschaubar, konzentriert in wenigen Dateien) + `scripts/check_bdd_traceability.py` (oder ein neues Schwester-Skript) muss um den Docstring-Kanal erweitert werden, inklusive einer bewussten Kardinalitätsregel "ein Spec-Fall darf von >1 Test beansprucht werden" (Duplikat-Befund oben), sonst schlagen 115 legitime Viele-zu-eins-Zuordnungen sofort als Defekt auf. Die 21 naiv-verwaisten `test_req001`/`test_req015`-Fälle brauchen zusätzlich eine Entscheidung: neue Spec-Fälle ergänzen (14, Suite ist der Spec voraus) bzw. auf die korrekten Blocknummern zurückführen (7, Nummerierungslücken-Missverständnis).

4. **Kosten Option (b) (zweites Schema legitimieren):** scheinbar günstiger (0 Docstring-Änderungen), aber trügerisch — es müsste dennoch für jede der 616 widersprüchlichen Erstzeilen-IDs entschieden werden, ob sie als "Schema B, Fall X" oder als echter Fehler zu werten ist, weil Schema B (test-lokale Zählung) nirgendwo eine stabile, von der Spec unabhängige Bedeutung hat, die man einfach kanonisieren könnte — man würde also dieselbe Fallunterscheidungsarbeit leisten wie bei (a), nur ohne am Ende eine Spec-Traceability zu gewinnen. Es bliebe zusätzlich der oben belegte Bruch: 5 Spec-Dokumente (Befund 0) und 5 weitere Testdateien (Befund 1, REQ-Abschnittsreferenzen) benutzen `TC-REQ-NNN-NNN` bereits mit unterschiedlicher, jeweils korrekter Bedeutung — ein zweites, kanonisiertes Test-lokales Schema würde diese Mehrdeutigkeit zementieren statt auflösen.

**Kurz:** Option (a) kostet konzentrierte, aber größtenteils mechanische Arbeit an ~620+65 Stellen mit bereits vorhandener Quelle; Option (b) kostet dieselbe Fallentscheidung ohne den Traceability-Gewinn und vertieft die bestehende Mehrdeutigkeit zwischen Spec-Dokumenten. Lane 2 sollte auf (a) aufsetzen.

---

## Methodik (Transparenz für Nachvollziehbarkeit)

- **Strikte ID-Form:** geladen aus `tests/e2e/protocol_plugin.py::TC_ID_PATTERN` über denselben `_load_module_by_path`-Mechanismus, den `scripts/check_bdd_traceability.py` selbst für sein SSOT-Laden verwendet (Standardbibliothek, keine Selenium-Abhängigkeit).
- **Weite Scan-Form für den Docstring-Kanal:** `tests/e2e/conftest.py::_TC_ID_SCAN` (`\bTC-(?:REQ-)?\d{3}-[A-Za-z0-9-]*\d[a-z]?\b`) konnte nicht per `_load_module_by_path` geladen werden — `conftest.py` importiert relativ (`from ._gherkin import …`), was ohne echten Paket-Kontext einen `ImportError` wirft. Das Pattern wurde daher **wörtlich aus der Quelldatei transkribiert** und die Übereinstimmung mit der lebenden Quelle bei jedem Lauf per Assertion gegen den frisch aus `conftest.py` extrahierten String geprüft (kein manuelles Abtippen ohne Gegenprobe).
- **Spec-Index:** `scripts/check_bdd_traceability.py::collect_spec_cases` unverändert wiederverwendet (liefert auch die Duplikat-Erkennung auf Spec-Seite: 0 doppelte Überschriften-IDs gefunden).
- **`Spec:`-Zeile:** eigens für diese Analyse erkannt (`Spec:\s*([^\n]+)`, dann `TC-(?:REQ-)?\d{3}-\d+`-Token darin gesucht) — dieser Kanal existiert in keinem der wiederverwendeten Module, weil ihn keines der beiden bisherigen Werkzeuge kennt; genau das ist Befund 1.
- **Skript:** Ad-hoc-Analyseskript (Python, ast-basiert), außerhalb des Arbeitsbaums unter `/tmp/.../scratchpad/` erstellt und nach Fertigstellung dieses Berichts **gelöscht** (kein Wiederverwendungswert über diese eine Messung hinaus — kein Testcode wurde ausgeführt oder verändert).

---

## Entscheidung (Operator, 2026-07-26)

**Option (a) ist beschlossen:** Die test-lokalen IDs werden auf das Spec-Schema
rekonziliiert. Ein zweites legitimiertes ID-Schema wird **nicht** eingeführt.

Damit ist Akzeptanzkriterium 2 von Issue #775 („A decision is recorded on the
target ID scheme, with reasoning") erfüllt; die Begründung ist der
Empfehlungsabschnitt oben, getragen von den gemessenen Zahlen — insbesondere
davon, dass 620 der 722 Testfunktionen die korrekte Spec-Referenz bereits im
Docstring tragen und die Erstzeile in 608–616 überprüfbaren Fällen etwas
anderes behauptet als der Test tatsächlich prüft.

### Verbindliche Vorgaben für die Umsetzung (Lane L10)

1. **Zielschema** ist die Überschriften-ID des jeweiligen Spec-Dokuments —
   `TC-NNN-NNN` für die 28 Dokumente, die so schreiben, und `TC-REQ-NNN-NNN`
   für die 5, die es nativ tun (`TC-REQ-005/008/030/034/039.md`). Kein drittes
   Schema, keine neue Regex: `tests/e2e/protocol_plugin.py::TC_ID_PATTERN`
   bleibt die einzige Quelle der ID-Form (#770/#771).
2. **Kardinalitätsregel bewusst setzen:** ein Spec-Fall darf von mehr als einem
   Test beansprucht werden. Ohne diese Regel schlagen die 115 legitimen
   1:n-Zuordnungen beim Scharfschalten sofort als Defekt auf und der Check wird
   binnen einer Woche abgeschaltet — genau das Ergebnis, das #775 vermeiden will.
3. **REQ-Abschnittsreferenzen** (`Spec: REQ-028 §7.1 …`, 5 Dateien) sind eine
   dritte, legitime Kategorie und **kein** Defekt. Sie brauchen entweder eine
   eigene, ausdrücklich erlaubte Form oder eine dokumentierte Ausnahme.
4. **Reihenfolge:** Der Check wird erst erweitert, **nachdem** die
   Rekonziliation grün ist. Ein rot scharfgeschalteter Check verletzt das
   Akzeptanzkriterium „stays green from the moment it is extended".
5. **Die 21 naiv-verwaisten Fälle** brauchen eine gesonderte Teilentscheidung:
   14 (Suite ist der Spec voraus) → Spec-Fälle ergänzen; 7 → auf die korrekten
   Blocknummern zurückführen.

### Warum die Umsetzung hier noch nicht passiert

Die Rekonziliation ändert Docstrings in ~60 Dateien unter `tests/e2e/` — dem
Territorium des offenen Draft-PR #759 (90 der 221 geänderten Dateien liegen
dort). Sie ist bis zu dessen Merge blockiert und läuft danach als Lane L10,
zeitlich **nach** L7 (#785), weil beide dieselben Testmodule anfassen.
Akzeptanzkriterien 3 und 4 von #775 bleiben bis dahin offen.
