# Agrarbiologische Prüfung der Schoss-Regeln mit Quellen (#3152)

| Feld | Wert |
|------|------|
| Datum | 2026-11-27 |
| Bezug | GitHub #3152; REQ-003 E1, E2, E5, E6 (`spec/req/REQ-003_Phasensteuerung.md:1824-1845`, `:1883-1886`, `:1910-1911`, `:1920-1929`); F-19 (#3151, Vorschlag der Ursache `bolting` im Ausfall-Dialog); REQ-053 E-10 |
| Gegenstand | Welche Arten des Seed-Bestands sollen eine Übergangsregel `→ bolting` mit `is_premature: true` tragen, mit welchem Auslöser und welchen Parametern |
| Methode | E-10: je Aussage und je Zahlenwert drei voneinander unabhängige Quellen, sonst bleibt der Wert `null`. Regeln wie in `spec/analysis/agrobiology-soil-hazards-research-2888.md` §0 und `agrobiology-soil-water-balance-review-3002.md` §0 |
| Status | Recherche, keine Entscheidung — Vorschläge für den Betreiber. Kein Code, kein Steckbrief, keine Seed-Datei und keine REQ wurde geändert. |

## 0. Lesehinweise zur Methode

- **Regeln.** Mehrere Seiten oder Dokumente derselben Institution zählen als **eine** Quelle. Eine Quelle, die erkennbar eine andere wiedergibt, zählt mit ihr zusammen als eine. „verifiziert“ heißt: Text der Quelle für dieses Dokument abgerufen und selbst gelesen (HTML oder per `pdftotext` aus dem PDF). „Suchauszug“ heißt: Aussage nur aus dem Treffertext einer Suche; Suchauszüge zählen nicht zum Belegstatus.
- **Belegklassen.** **3/3** = drei unabhängige, verifizierte Quellen. **3/3 (Spanne)** = der vorgeschlagene Wert liegt in den Angaben dreier unabhängiger Quellen (Betreiberentscheid vom 2026-11-22: Spannen zählen). **2/3**, **1/3**, **widersprüchlich**, **nicht gefunden** wie dort. Ein Wert unter 3/3 bleibt `null`. Die qualitative Aussage „Art X schosst vorzeitig unter Faktor Y“ gilt erst mit 3/3 als bestätigt.
- **Zusammengehörige Quellen in dieser Recherche.**
  - **Linie W (Wiebe/Krug).** Die Tabelle der Michigan State University [Q1] nennt als Quelle 1 fast jeder Zeile „Wiebe, H.J. 1990. Vernalization of vegetable crops – a review“. Die Hortipendium-Tabelle „Schossverhalten wichtiger Gemüsearten“ [Q2] führt Wiebe und Krug als Autoren und Krug 1991 („Gemüseproduktion“) als Quelle; ihre Zahlen stimmen mit [Q1] bis auf die Umrechnung von °F in °C überein. Die Hortipendium-Kulturseiten [Q3] stammen aus demselben Haus (DLR Rheinpfalz). Die Anbauempfehlungen der MSU zu Zwiebel und Sellerie [Q4] sind dieselbe Institution wie [Q1]. **Q1 bis Q4 zählen in diesem Dokument zusammen als eine Quelle.**
  - Die beiden Wageninger Arbeiten zu Spinat [Q13] und die Arbeit zu Endivie [Q30] erschienen in derselben Zeitschrift, zwei davon aus demselben Labor; sie zählen als eine Quelle.
  - RHS „Bolting in vegetables“ und RHS „Florence fennel“ [Q6] sind eine Quelle. Die drei Blätter der Bayerischen Gartenakademie [Q8] sind eine Quelle. Die Seiten der Utah State University [Q14, Q19, Q23, Q25] sind eine Quelle, ebenso die der University of Wisconsin [Q18, Q20].
  - Die Kolumne der WSU-Master-Gardener [Q32] nennt Oregon State, Arizona und MSU als ihre Quellen und stellt nur eine Liste zusammen. Sie zählt nicht zum Belegstatus.
- **Was sich öffnen ließ.** MSU „Bolting in spring vegetables“ (nur über das Internet Archive; die Originalseite wies den Abruf ab), Hortipendium (Übersichtstabelle und 14 Kulturseiten), University of Delaware, RHS (zwei Seiten), FiBL-Merkblatt 1212, drei Blätter der Bayerischen Gartenakademie, Purdue, UC IPM, zwei Übersichts-/Originalarbeiten zu Salat, drei Wageninger Arbeiten (Spinat, Endivie), JARQ-Übersicht zu Rettich, Oregon State, Wisconsin, Utah State, Illinois, Arizona, Missouri, NC State, UMass (über das Internet Archive), der dänische Versuchsbericht zu Dill, die Zusammenfassung der Rucola-Arbeit in „Eco-Engineering“.
- **Was sich nicht öffnen ließ** (steht im Text als „nicht geprüft“): Wiebe 1990 und Krug 1991 im Original; die beiden HortScience-Arbeiten zur kritischen Tageslänge von Spinat (35(4):624 und 51(5):481, Zugriff abgewiesen); „Photoperiodic Responses of Dill, a Very Sensitive Long Day Plant“ (University of Chicago Press, HTTP 403); University of Minnesota „Non-pest issues in cool-season crops“ (HTTP 403, auch im Archiv nicht); OMAFRA „Florence Fennel“ (HTTP 502); UF/IFAS zu Koriander (Seitentext nicht extrahierbar); University of Hawaii zu Zwiebel (HTTP 404); Sächsische Gartenakademie zu Chinakohl (HTTP 404); Springer-Artikel zur Spinatzüchtung (nur Umleitung). LfL Bayern, die Landwirtschaftskammern und Agroscope lieferten zu den Fragen keine geöffnete Fundstelle.
- **Abrufdatum.** Alle Quellen wurden am 2026-11-27 abgerufen.
- **Einheiten.** °F in °C umgerechnet: 40 °F = 4,4 °C; 50 °F = 10 °C; 55 °F = 12,8 °C; 68 °F = 20 °C.

---

## 1. Was die Regel heute bewirkt — und was nicht

### 1.1 Der Weg vom Seed zum Vorschlag

| Schritt | Fundstelle | Befund |
|---|---|---|
| Regel im Seed | `src/backend/app/migrations/seed_data/lifecycles_outdoor.yaml:1720-1737` | Spinat trägt die Phase `bolting` (Reihenfolge 6, außerhalb des linearen Pfads) und eine Regel `vegetative → bolting`, `trigger_type: photoperiod_based`, `is_premature: true`. Es ist die einzige Regel dieser Art im Seed-Verzeichnis. |
| Schema | `schemas/lifecycles.schema.yaml:58-90`; `schemas/_defs.schema.yaml:228-231` | `transition_rules` gibt es nur im Schema von `lifecycles_outdoor.yaml`. Zulässige `trigger_type`: `time_based`, `manual`, `event_based`, `conditional`, `gdd_based`, `photoperiod_based`, `vernalization_based`. |
| Lader | `seed_lifecycles_outdoor.py:67-115` | Nur dieser Lader legt Übergangsregeln an. Die Lader für `plant_info*.yaml`, `adventskalender.yaml` und `species.yaml` kennen keine Regeln. |
| Kennzeichnung | `phase_transition_engine.py:115-123`, `:236` | `_is_premature` liest die Regeln der **aktuellen** Phase und prüft, ob eine davon zur Zielphase führt und `is_premature` trägt. Der Trigger-Typ spielt dabei keine Rolle. |
| Vorschlag | `failure_cause_engine.py:122-128` | `bolting` wird vorgeschlagen, wenn die offene Phase `bolting` heißt und mit `is_premature` betreten wurde. |

### 1.2 Welche Trigger-Typen automatisch ausgewertet werden

| `trigger_type` | Auswertung | Voraussetzung | Stand |
|---|---|---|---|
| `time_based` | `tasks/phase_transitions.py:250-255` | `auto_transition_after_days` an der Regel | ausgewertet |
| `photoperiod_based` | `:256-263`, `transition_trigger_evaluator.py:29-46` | `photoperiod_type` = `long_day` oder `short_day` **und** `critical_day_length_hours` am Lebenszyklus; Tageslänge aus dem Lichtplan des Standorts oder aus GPS und Datum. Langtag: feuert, sobald Tageslänge > Schwelle. | ausgewertet |
| `vernalization_based` | `:264-271`, `transition_trigger_evaluator.py:48-58` | `vernalization_min_days` am Lebenszyklus gegen `chill_days_accumulated` der Pflanze | ausgewertet, aber der Zähler steht still (siehe unten) |
| `gdd_based` | `transition_trigger_evaluator.py:60-65` | — | Funktion vorhanden, im Scan nicht aufgerufen |
| `manual`, `event_based`, `conditional` | — | — | nie automatisch |

Einen Trigger für **Hitze**, **Trockenheit** oder allgemein **Stress** gibt es nicht. Einen Trigger für den **Kältereiz der Jungpflanze** gibt es ebenfalls nicht: `vernalization_based` zählt Kältetage über die ganze Standzeit, unabhängig vom Entwicklungsstadium, mit einer festen Schwelle von 5 °C Tagesmittel (`vernalization_tracker.py:24`).

### 1.3 Drei Befunde, die über die Trigger-Frage hinausgehen

1. **Der Scan läuft nicht.** `check_auto_transitions` ist weder geplant noch wird er angestoßen; der Guard führt ihn als bewusste Ausnahme: „until then phase transitions are manual, as they have been in production all along“ (`tests/unit/guards/test_every_task_is_scheduled_or_dispatched.py:46-51`). Dasselbe gilt für `update_vernalization_progress` (`:58-62`, `tasks/vernalization_updates.py:13-17`), der als einziger den Kältetage-Zähler erhöht. **Folge:** Kein Trigger-Typ löst heute etwas aus, auch `photoperiod_based` beim Spinat nicht. Die Regel wirkt ausschließlich als **Markierung**: Setzt der Nutzer die Pflanze von Hand in die Phase `bolting`, trägt der Phasenverlauf `is_premature`, und der Ausfall-Dialog schlägt `bolting` vor.
2. **Die Spinat-Regel hängt nur an `vegetative`.** Die Ernte liegt beim Spinat in der Phase `ripening` („Ernte“, `allows_harvest: true`, `lifecycles_outdoor.yaml:1706-1712`). Schosst der Spinat während der Ernte, gibt es von `ripening` keine Regel nach `bolting`; der Wechsel ist erlaubt, aber nicht als vorzeitig markiert, und der Vorschlag bleibt aus.
3. **Würde der Scan eingeplant, feuerte die Spinat-Regel falsch.** Die Bedingung ist allein „Tageslänge > 13 h“. Nach der astronomischen Tageslänge (eigene Rechnung, Sonnenaufgang bei −0,833°) gilt das auf 50° N vom 04.04. bis 07.09., auf 54° N vom 02.04. bis 09.09. Jede Spinatpflanze, die in diesem Zeitraum die Phase `vegetative` erreicht, würde beim ersten Lauf nach `bolting` gesetzt — ohne Mindestalter, ohne Dauer. Die Quellen beschreiben die Langtagreaktion von Spinat als quantitativ und sortenabhängig (§3.1), nicht als Schalter.

**Folgerung für diese Prüfung.** Die Frage „welcher Trigger-Typ“ entscheidet heute nichts. Ehrlich ist `trigger_type: manual`: Die Regel ist eine Markierung für den Handwechsel. Ein automatischer Typ ist nur vertretbar, wenn seine Parameter 3/3 belegt sind **und** die Bedingung das vorzeitige Schossen von der normalen Entwicklung trennt. Das trifft nach §3 auf keine Art zu.

---

## 2. Bestand

### 2.1 Woher Lebenszyklen im Seed kommen

Gemessen per Skript über `src/backend/app/migrations/seed_data/` (Zählung der Einträge, Stand dieses Branches):

| Datei | Abschnitt | Einträge | Übergangsregeln möglich |
|---|---|---|---|
| `lifecycles_outdoor.yaml` | `lifecycles` | 53 | ja |
| `plant_info*.yaml` (9 Dateien) | `lifecycle_configs` / `growth_phases` | zusammen 114 / 107 Arten | nein |
| `adventskalender.yaml` | `lifecycle_configs` / `growth_phases` | 18 / 18 | nein |
| `species.yaml` | `species` ohne eigenen Lebenszyklus-Eintrag | Standardphasen `seedling`, `vegetative`, `flowering`, `flushing`, `ripening`; `photoperiod_type = unspecified` (`seed_data.py:766-781`) | nein |

Eine Datei `lifecycles_indoor.yaml` gibt es nicht. Insgesamt führen die Seed-Dateien 207 Arten und 180 verschiedene Lebenszyklus-Einträge (eine Art kann in zwei Dateien stehen; je Name einmal gezählt).

### 2.2 Arten, die vor der Blüte geerntet werden

Ausgewählt nach `harvested_part` (`leaf`, `root`, `bulb`, `stem`) und `plant_category` (`herb`). Arten, deren Erntegut Frucht, Samen oder Blüte ist, scheiden aus: Dort ist die Blüte kein Ausfall. Mehrjährige Kräuter und Stauden (Minze, Melisse, Oregano, Liebstöckel, Salbei, Thymian, Rosmarin, Schnittlauch, Estragon, Rhabarber, Spargel, Knoblauch) blühen planmäßig jedes Jahr und stehen nicht in der Tabelle.

| Art | Lebenszyklus aus | `cycle_type` | `photoperiod_type` | `vernalization_required` | krit. Tageslänge / Vern.-Tage im Seed | Phasen im Seed |
|---|---|---|---|---|---|---|
| *Spinacia oleracea* (Spinat) | `lifecycles_outdoor.yaml` | annual | long_day | false | 13 / — | germination, seedling, vegetative, ripening, senescence, **bolting** |
| *Lactuca sativa* (Salat) | `adventskalender.yaml` | annual | long_day | false | 14,0 / — | germination, seedling, vegetative, ripening |
| *Raphanus sativus* (Radieschen) | `adventskalender.yaml` | annual | day_neutral | false | — / — | germination, seedling, tuber_formation, ripening |
| *Coriandrum sativum* (Koriander) | `plant_info_outdoor_1.yaml` | annual | long_day | false | 12 / — | keine eigenen (nur `lifecycle_configs`) |
| *Eruca vesicaria* (Rucola) | kein Eintrag | (Standard) | unspecified | — | — / — | Standardphasen |
| *Foeniculum vulgare* (Knollenfenchel) | `plant_info_outdoor_1.yaml` | annual | long_day | true | — / 5 | keine eigenen |
| *Beta vulgaris* subsp. *vulgaris* (Rote Bete) | `adventskalender.yaml` | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, ripening |
| *Apium graveolens* (Sellerie) | `adventskalender.yaml` | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, tuber_formation, ripening |
| *Apium graveolens* var. *rapaceum* (Knollensellerie) | `plant_info.yaml` | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, tuber_formation, ripening |
| *Allium cepa* (Zwiebel) | `lifecycles_outdoor.yaml` | biennial | long_day | true | 13,75 / 90 | germination, seedling, vegetative, dormancy, flowering, ripening |
| *Allium porrum* (Lauch) | `adventskalender.yaml` | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, shaft_growth, ripening |
| *Daucus carota* (Möhre) | `adventskalender.yaml` (zusätzlich `plant_info_outdoor_1.yaml`) | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, ripening |
| *Brassica oleracea* var. *gongylodes* (Kohlrabi) | kein Eintrag | (Standard; Anbau biennial) | unspecified | — | — / — | Standardphasen |
| *Brassica oleracea* var. *capitata* (Kopfkohl) | kein Eintrag | (Standard; Anbau biennial) | unspecified | — | — / — | Standardphasen |
| *Brassica oleracea* var. *sabellica* (Grünkohl) | `plant_info_outdoor_1.yaml` | biennial | day_neutral | true | — / — | keine eigenen |
| *Brassica oleracea* var. *gemmifera* (Rosenkohl) | `adventskalender.yaml` | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, sprout_formation, ripening |
| *Anethum graveolens* (Dill) | `adventskalender.yaml` | annual | long_day | false | 14,0 / — | germination, seedling, vegetative, flowering, senescence |
| *Petroselinum crispum* (Petersilie) | `adventskalender.yaml` | biennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, dormancy, flowering |
| *Ocimum basilicum* (Basilikum) | `adventskalender.yaml` | perennial (Anbau annual) | day_neutral | false | — / — | germination, seedling, vegetative, flowering, senescence |
| *Cichorium intybus* (Chicorée, Radicchio) | `adventskalender.yaml` (zusätzlich `plant_info_outdoor_1.yaml`) | perennial | long_day | true | 14,0 / 42 | germination, seedling, vegetative, flowering, dormancy |
| *Pastinaca sativa* (Pastinake) | `lifecycles_outdoor.yaml` | biennial | day_neutral | true | — / 30 | germination, seedling, vegetative, dormancy, flowering, ripening |
| *Satureja hortensis* (Bohnenkraut) | `lifecycles_outdoor.yaml` | annual | day_neutral | false | — / — | germination, seedling, vegetative, ripening, senescence |

Beobachtungen am Bestand:

- Die Phase `bolting` trägt nur Spinat. Kein zweijähriger Lebenszyklus im Seed bildet das **planmäßige** Schossen als Phase `bolting` ab; Zwiebel, Pastinake und Petersilie gehen von `dormancy` direkt nach `flowering`. Eine vorzeitige Regel aus einer Phase **vor** `dormancy` ist damit eindeutig vom planmäßigen Verlauf getrennt.
- Sieben Einträge in `adventskalender.yaml` tragen dieselbe Kombination `long_day` / 14,0 h / 42 Tage (Lauch, Rote Bete, Rosenkohl, Möhre, Petersilie, Sellerie, Chicorée; dazu Schnittlauch). Der Wert ist nicht artspezifisch.
- Von den Kandidaten liegt nur Spinat (und für die Zweijährigen Zwiebel und Pastinake) in `lifecycles_outdoor.yaml`. Alle übrigen können heute **keine Regel tragen**, weil ihre Seed-Datei keine Übergangsregeln kennt (§1.1).

### 2.3 Arten der Aufgabenliste, die im Seed fehlen

| Gesucht | Stand im Seed |
|---|---|
| Pak Choi, Chinakohl, Mairübe (*Brassica rapa*) | nicht vorhanden |
| Wilde Rauke (*Diplotaxis tenuifolia*) | nicht vorhanden |
| Feldsalat (*Valerianella locusta*) | nicht vorhanden |
| Endivie (*Cichorium endivia*) | nicht vorhanden (nur *C. intybus*) |
| Mangold | kein eigener Eintrag; „*Beta vulgaris* subsp. *vulgaris*“ ist nach dem Steckbrief die Rote Bete |
| Rettich | kein eigener Eintrag; „*Raphanus sativus*“ ist nach dem Steckbrief (`raphanus_sativus_var_sativus.md`) das Radieschen |

Zu diesen Arten liegen verifizierte Fundstellen vor (§3.4); sie sind für spätere Seed-Einträge festgehalten und gehen nicht in die Aufnahme-Tabelle ein.

### 2.4 Steckbrief gegen Seed

Der Steckbrief ist die Quelle der Wahrheit. Für die Kandidaten weichen Steckbrief und Seed in den Feldern ab, an denen eine automatische Regel hinge:

| Art | Steckbrief (`spec/knowledge/plants/`) | Seed | Abweichung |
|---|---|---|---|
| Salat | `long_day`; kritische Tageslänge „~12“, sortenabhängig (`lactuca_sativa.md:23`, `:29`) | 14,0 h | ja |
| Radieschen | `long_day`, 14 h; „Vernalisation/Kältereiz löst das unerwünschte Schossen aus“, dennoch `false` (`raphanus_sativus_var_sativus.md:23`, `:29`, `:31`) | `day_neutral`, kein Wert | ja |
| Koriander | `long_day`, 12 h, „fakultativer Langtag“ (`coriandrum_sativum.md:23`, `:30`) | `long_day`, 12 | nein |
| Rucola | `long_day`; kritische Tageslänge leer, „Schossungstrigger ~12–13 h; siehe Freitext“ (`eruca_vesicaria.md:23`, `:29`) | kein Lebenszyklus-Eintrag | Eintrag fehlt |
| Knollenfenchel | `long_day`; Vernalisation `true`, 5 Tage unter ~7 °C; kritische Tageslänge „DATEN FEHLEN“ (`foeniculum_vulgare.md:25`, `:30-32`) | `long_day`, 5 Tage | nein; der Wert 5 Tage ist in dieser Recherche nicht belegt (§3.2) |
| Spinat | `long_day`, 13–14 h (`spinacia_oleracea.md:23`, `:27`) | 13 | Spanne auf einen Wert gekürzt |
| Rote Bete | Vernalisation 84 Tage; 14 h gilt „im 2. Jahr nach Vernalisation; KEIN Blühtrigger für das Erntegut im 1. Jahr“ (`beta_vulgaris_subsp_vulgaris.md:40-41`) | 42 Tage, 14,0 h | ja |
| Sellerie / Knollensellerie | Vernalisation 10 Tage; kritische Tageslänge „DATEN FEHLEN“ (`apium_graveolens.md:31-32`; `apium_graveolens_var_rapaceum.md:33-34`) | 42 Tage, 14,0 h | ja |
| Zwiebel | 13,75–14 h ist der „Langtag-Trigger der Zwiebelbildung“ (`allium_cepa.md:38`) | 13,75 h | Wert stimmt, meint aber die Zwiebelbildung, nicht das Schossen |
| Lauch | `day_neutral`; 21–28 Tage; keine kritische Tageslänge (`allium_porrum.md:23`, `:37-38`) | `long_day`, 14,0 h, 42 Tage | ja |
| Möhre | `day_neutral`; 42 Tage; keine kritische Tageslänge (`daucus_carota.md:26`, `:33-34`) | `long_day`, 14,0 h, 42 Tage | ja |
| Kohlrabi | `long_day`; Vernalisation `true`, 42–70 Tage, „Kältereiz < 11 °C“ (`brassica_oleracea_var_gongylodes.md:26`, `:31-33`) | kein Lebenszyklus-Eintrag | Eintrag fehlt |
| Dill | `long_day`; kritische Tageslänge „DATEN FEHLEN“ (`anethum_graveolens.md:27`, `:33`) | 14,0 h | ja |

Diese Abweichungen sind Befund, nicht Teil des Auftrags; sie gehören in den Steckbrief-Seed-Abgleich (§8, Schritt 1).

---

## 3. Auslöser je Art

Schreibweise: [W] steht für die Linie Wiebe/Krug (Q1–Q4, eine Quelle).

### 3.1 Einjährige Blatt- und Krautkulturen

#### Spinat (*Spinacia oleracea*) — Abgleich des Bestands

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | weitere | Belegklasse |
|---|---|---|---|---|---|
| Schosst unter Langtag | Delaware: „Bolting in spinach, lettuce, and some radishes (oriental types) will occur naturally as days get longer (daylength effect).“ [Q5] | RHS: „Annual crops sensitive to photoperiod … include lettuce, some radish cultivars and spinach. They are long-day plants“ [Q6] | Verkerk und Volosky Yadlin: „For the bolting in spinach the long day is of primary importance.“ [Q13] | [W]: „Die Blütenbildung wird durch den Langtag im Sommer induziert.“ [Q3]; UC IPM: „Bolting is caused by long daylight periods from late spring to early fall.“ [Q10]; Utah State [Q14]; Arizona [Q15]; Purdue [Q9] | **3/3** |
| Wärme beschleunigt das Schossen | Delaware: „High temperatures will accelerate bolting in spinach and lettuce.“ [Q5] | Utah State: „Spinach will flower (bolts) during long days and warm temperatures in summer.“ [Q14] | Arizona: „As days grow hotter and longer, spinach tends to flower and go to seed“ [Q15] | Purdue [Q9] | **3/3** |
| Kälte in Keimung und Jungpflanze verfrüht die Blüte | Parlevliet 1968: „Low temperatures during germination and in the young seedling stage induce an earlier flowering in spinach“ [Q13] | [W]: Tabelle, Kältebedürfnis fakultativ, „receptive from seed“, 1–3 Wochen [Q1, Q2] | — | Verkerk: „Vernalization has a weak effect on the bolting in spinach“ [Q13, zählt mit Quelle 1] | **2/3** |
| Trockenheit fördert das Schossen | RHS: „Dry soil can also encourage bolting, particularly with cauliflower, rocket and spinach.“ [Q6] | — | — | — | **1/3** |
| Kritische Tageslänge in Stunden | — | — | — | Nur Suchauszug: HortScience 35(4):624 nennt „longer than 13 h and shorter than 15 h“ für Jungpflanzen einer Sorte (nicht geöffnet). [Q32] setzt für alle Langtagpflanzen pauschal „> 12 hrs“ (zählt nicht). | **nicht gefunden** (0 verifizierte Quellen) |

**Befund.** Die Regel für Spinat ist berechtigt; Langtag als Auslöser ist bestätigt. Der Seed-Wert 13 h ist nach E-10 nicht belegt und bleibt `null`. Mit `null` feuert `photoperiod_based` nie (`transition_trigger_evaluator.py:40-41`); die Regel ist dann eine reine Markierung, was sie nach §1.3 heute ohnehin ist.

#### Kopf- und Schnittsalat (*Lactuca sativa*)

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | weitere | Belegklasse |
|---|---|---|---|---|---|
| Schosst unter Langtag | Delaware [Q5] (Wortlaut oben) | RHS [Q6] (Wortlaut oben) | Han u. a. 2021: „lettuce is also a facultative long-day plant“; Sorten reichen von wenig empfindlich bis „highly sensitive“ [Q11] | Purdue: „lettuce and spinach will bolt as days grow longer in summer“ [Q9]; [W]: Photoperiode „LT“, fakultativ [Q2] | **3/3** |
| Hitze löst das Schossen aus oder beschleunigt es | Delaware: „Lettuce may also be induced to bol[t] just by high temperature stress.“ [Q5] | Han u. a. 2021: „Heat-accelerated bolting and flowering is a common phenomenon“ [Q11] | UC IPM: „Flower stalk initiation may be stimulated by high temperatures.“ [Q10] | Han u. a. 2016: „Bolting in lettuce is promoted by high temperature“ [Q12]; Purdue [Q9] | **3/3** |
| Kälte ab Keimung fördert die Blüte | [W]: „receptive from seed“, 2–3 Wochen, fakultativ [Q1, Q2] | — | — | Die Gartenakademie zieht den ersten Salatsatz bei 8–12 °C an und zählt Salat **nicht** zu den schossgefährdeten Arten [Q8]; FiBL führt Salat als „temperaturindifferent“ [Q7] | **1/3**, mit zwei Gegenstimmen aus der Praxis |
| Kritische Tageslänge in Stunden | — | — | — | Fakultative Langtagpflanze: Es gibt keinen Schwellenwert, unter dem die Blüte ausbleibt [Q11] | **nicht gefunden**; ein Wert ist der Sache nach nicht zu erwarten |

**Befund.** Aufnehmen. Auslöser Langtag und Hitze, beide 3/3. Der Seed-Wert 14,0 h und der Steckbrief-Wert „~12“ sind beide unbelegt.

#### Koriander (*Coriandrum sativum*)

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Wärme löst das Schossen aus oder beschleunigt es | Oregon State: „In warm weather, cilantro completes its life cycle faster. In mid-summer, it typically bolts … within four to six weeks.“ [Q17] | Wisconsin: „tends to bolt (go to seed) in hot weather“ [Q18] | Utah State: gegen das Schossen „Plant early when it is cool … Mulch the soil to keep it cool“ [Q19] | **3/3** |
| Schosst unter Langtag | Oregon State: „Both temperature and day length influence flowering and seed set“ [Q17] | Wisconsin: keine Sorte hält „under high temperatures and long days“ [Q18] | — ([W]: nur „relativ baldige Blütenbildung“, ohne Ursache [Q3]) | **2/3** |
| Kritische Tageslänge in Stunden | — | — | — | **nicht gefunden** |

**Befund.** Aufnehmen, Auslöser Wärme (3/3). Der Seed-Wert 12 h ist unbelegt. Vorbehalt Doppelnutzung: Koriander wird auch für die Samen gebaut; dort ist die Blüte das Ziel (Oregon State: „You may lose the leaves, but you'll gain coriander seeds.“ [Q17]). Die Regel ist nur für die Blattnutzung richtig (Frage 2 in §6).

#### Rucola (*Eruca vesicaria*)

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | weitere | Belegklasse |
|---|---|---|---|---|---|
| Schosst unter Langtag | [W]: „Rucola ist eine Langtagpflanze. … bei zunehmendem Langtag mit der Blütenbildung beginnt.“ [Q3] | Wisconsin: „under the appropriate conditions (long days, high temperatures, and/or dry soil) quickly produce a … flower stem“ [Q20] | Illinois: „Summer heat and long days trigger the plant to flower, known as bolting.“ [Q21] | Koike 2008: Blütenknospen nur „Under photoperiods at and above 13-hrs“ [Q22] | **3/3** |
| Hitze | Wisconsin [Q20] | Illinois [Q21] | — | — | **2/3** |
| Trockenheit | Wisconsin [Q20] | RHS [Q6] (Wortlaut bei Spinat) | — | [W]: „verstärkt durch Stressbedingungen“ [Q3] nennt die Trockenheit nicht | **2/3** |
| Kein Kältereiz | [W]: Die „bei den verwandten Kreuzblütler Arten, aktuelle Schosserbildung im Frühjahr ist bei Rucola nicht aktuell“ [Q3] | — | — | — | **1/3** |
| Kritische Tageslänge 13 h | Koike 2008 [Q22] (nur Zusammenfassung gelesen) | — | — | — | **1/3** → `null` |

**Befund.** Aufnehmen, Auslöser Langtag (3/3). Vorher braucht die Art überhaupt einen Lebenszyklus-Eintrag (§2.2).

#### Dill (*Anethum graveolens*)

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Schosst unter Langtag | Boelt 1990: „Dill is a long day plant“; „Decreasing daylength results in a delayed formation of reproductive organs“ [Q24] | [W]: „Im Langtag (Juni bis September) gehen die Pflanzen in Blüte.“ [Q3] | — (der Titel „Photoperiodic Responses of Dill, a Very Sensitive Long Day Plant“ ließ sich nicht öffnen) | **2/3** |
| Hitze fördert das Schossen | Utah State: „Temperature stress (high heat) and overcrowding promote bolting“ [Q25] | UC Master Gardeners Sonoma: „Expect heat-sensitive dill to bolt when summer temperatures soar“ [Q26] | Boelt 1990: „increasing daylength and higher temperature promote umbel appearance“ [Q24] | **3/3** |

**Befund.** Offen. Hitze ist 3/3, aber die Blüte ist beim Dill ein reguläres Erntegut (Dolden zum Einlegen, Samen); im Seed trägt die Phase `flowering` `allows_harvest: true`. Ob die Blüte hier ein Ausfall ist, hängt von der Nutzung ab (Frage 2).

### 3.2 Knollenfenchel (*Foeniculum vulgare*)

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Trockenheit und Stress lösen das Schossen aus | [W]: „Schosser werden durch Langtag ausgelöst und durch Stress (Trockenheit) stark forciert.“ [Q3] | Utah State: „susceptible to bolting if growth is stressed by lack of water or damage occurs to plants or roots“ [Q23] | RHS: „It tends to bolt (flower) in dry conditions, which ruins the harvest.“ [Q6] | **3/3** |
| Schosst unter Langtag | [W]: „beginnen mit der Blütenbildung beim Langtag, bes. im Monat Juli und August“ [Q3] | Utah State: „Hot summer temperatures and long days accelerate bolting“ [Q23] | — | **2/3** |
| Hitze | [W]: „Im Sommeranbau steigt das Schossrisiko enorm“ [Q3] | Utah State [Q23] | — | **2/3** |
| Kälte in der Jugend löst das Schossen aus | FiBL: Mindest-Anzuchttemperatur „> 16 °C Sellerie, Knollenfenchel“ für frühe Sätze schossgefährdeter Arten [Q7] | RHS: „Early sowings are very liable to bolt“ [Q6] (nennt die Kälte nicht ausdrücklich) | **dagegen** [W]: „Es besteht kein Schosserrisiko durch niedrige Temperaturen.“ [Q3] | **widersprüchlich** |
| 5 Tage unter 7 °C (Steckbrief und Seed) | — | — | — | **nicht gefunden** |

**Befund.** Aufnehmen, Auslöser Trockenstress (3/3). `vernalization_required: true` mit 5 Tagen ist in den geöffneten Quellen nicht belegt und für die Kälte widersprüchlich; das ist ein Punkt für den Steckbrief, nicht für die Regel.

### 3.3 Zweijährige: Schossen im ersten Jahr ist vorzeitig, im zweiten planmäßig

Allen gemeinsam: Die Blüte folgt planmäßig im zweiten Jahr auf den Winter. Vorzeitig ist sie, wenn ein Kältereiz die Jungpflanze im ersten Frühjahr trifft. RHS: Zweijährige „such as onions, leeks, carrot and beetroot can initiate flowers in the first year. This … usually occurs after a prolonged cold spell, often during the propagation phase.“ [Q6]

| Art | Kältereiz der Jungpflanze löst vorzeitiges Schossen aus | Belegklasse | Zahlenwerte |
|---|---|---|---|
| **Rote Bete** (*Beta vulgaris*) | [W]: empfänglich ab Samen, „temperatures between 41 and 48 F for one to five weeks“; „Schon während der Keimung lösen zu niedrige Keimtemperaturen einen Schosser Impuls aus.“ [Q1, Q3] · RHS [Q6] · Delaware: „beets, carrots, and onions also can be induced to bolt but only once plants have reached a certain size“ [Q5] · Gartenakademie (Mangold, dieselbe Art): „Zu frühe Aussaat und damit zu tiefe Temperaturen führen zu Schossern.“ [Q8] | **3/3** | wirksame Temperatur und Dauer nur aus [W] (0–18 °C, 3–5 Wochen): **1/3** → `null`. Delaware und [W] widersprechen sich zum Beginn der Empfänglichkeit (ab bestimmter Größe gegen ab Samen). |
| **Sellerie, Knollensellerie** (*Apium graveolens*) | [W]: „Temperaturen unter 15 °C sind riskant …, besonders kritisch sind Werte von 5-8 °C. Der Schossreiz kann ab dem Zweiblattstadium erfolgen und muss 2-5 Wochen einwirken.“ [Q3]; „exposed to temperatures below 55° F for 7 days or longer“ [Q4] · FiBL: „Mindestens 16, besser 18 °C einhalten, um Schossen zu verhindern.“ [Q7] · Gartenakademie: Sellerie nie „unter 14 bis 16 °C“ anziehen, „sonst besteht die Gefahr des frühzeitigen Schossens“ [Q8] · UMass: „bolting … will occur if temperatures below 40°F persist over a period of 10 to 14 days. … Keep greenhouse temperatures above 55°F to prevent bolting“ [Q27] | **3/3** | **Temperatur:** Unter 13 °C gilt in vier unabhängigen Quellen als riskant (12,8 °C [W, Q27]; 14–16 °C [Q8]; 16 °C [Q7]) → **3/3 (Spanne)** für „unter 13 °C“. **Dauer:** 7 Tage [Q4], 10–14 Tage bei unter 4,4 °C [Q27], 2–5 Wochen [Q3] → **widersprüchlich**, `null`. |
| **Zwiebel** (*Allium cepa*) | [W]: „if they are subjected to cool temperatures after reaching the five-leaf stage. Temperatures must be below 50 degrees F for several days“ [Q4] · Missouri: „temperatures below 50°F for 3-4 weeks“ [Q28] · RHS [Q6] · Delaware [Q5] · NC State: Schossen bei „prolonged or extreme cold conditions“ [Q29] | **3/3** | „unter 10 °C“: [W] und Missouri → **2/3**, `null`. Dauer „mehrere Tage“ gegen „3–4 Wochen“ → **widersprüchlich**. |
| **Möhre** (*Daucus carota*) | [W]: nach der Jugendphase (über 8 Blätter), 5–12 Wochen [Q1, Q2] · RHS [Q6] · Delaware [Q5] · Purdue: „Most biennial vegetables, including onions, carrots, heading cabbage, have to reach a certain stage of growth“ [Q9] | **3/3** | nur [W] → **1/3**, `null`. [W] nennt Möhre als wenig gefährdet: lange Jugendphase, lange Einwirkzeit [Q1]. |
| **Kohlrabi** (*B. oleracea* var. *gongylodes*) | [W]: „ab den 5-Blattstadium der Jungpflanzen Temperaturen unter 14°C ein zu frühes Schossen und auch die unerwünschte ‚Flaschenbildung‘“ [Q3] · Gartenakademie: nie unter 14 bis 16 °C [Q8] · FiBL: „> 14 °C Kopf- und Rosenkohl, Kohlrabi, Petersilie“ [Q7] | **3/3** | „unter 14 °C“ steht in allen drei → **3/3 (Spanne)**. Dauer (4–8 Wochen) nur [W] → `null`. |
| **Kopfkohl** (*B. oleracea* var. *capitata*) | [W]: 4–15 Blätter, 4–20 Wochen [Q1, Q2] · Delaware: „cabbage planted very early in cold springs may bolt“ [Q5] · Gartenakademie: Frühkohl nie unter 14–16 °C [Q8] · FiBL: über 14 °C [Q7] · UC IPM: Kohlarten, „prolonged cold temperatures below 50°F“ [Q10] · Purdue [Q9] | **3/3** | „unter 10 °C“ liegt unter allen genannten Grenzen ([W] wirksam bis 12 °C; [Q8] 14–16 °C; [Q7] 14 °C; [Q10] 10 °C) → **3/3 (Spanne)**. Dauer nur [W] → `null`. |
| **Lauch** (*Allium porrum*) | [W]: „Zu einer Schosserbildung kann es bei Temperaturen von bis zu 18°C kommen. 5-8°C sind besonders risikoreich. … Die Kälteempfindlichkeit beginnt erst ab dem 3-Blattstadium.“ [Q3] · RHS [Q6] | **2/3** | nur [W] → `null` |
| **Petersilie** (*Petroselinum crispum*) | [W]: über 5 Blätter, 5–8 Wochen [Q1, Q2] · FiBL: über 14 °C [Q7] | **2/3** | nur [W] → `null` |
| **Rosenkohl, Grünkohl** | Rosenkohl: [W] [Q1, Q2] · FiBL [Q7]. Grünkohl: [W] · Delaware („kale, and collards also … when planted too early“) [Q5] | je **2/3** | — |
| **Chicorée, Radicchio** (*Cichorium intybus*) | [W]: empfänglich ab Samen, 4–8 Wochen [Q1, Q2] · FiBL: „> 22 °C Radicchio/Cicorino“ [Q7] | **2/3** | — |
| **Pastinake** (*Pastinaca sativa*) | [W]: überwinterte Pastinaken „will readily bolt in the next spring“ — das ist der planmäßige Verlauf [Q1] | **1/3**; vorzeitiges Schossen im ersten Jahr nicht belegt | — |

**Zwiebel und Tageslänge.** Missouri: „Bolting in onions is not induced by photoperiod, as is sometimes believed. However, bulb formation of onions requires long days (short nights) of 12-16 hours depending on cultivars and types.“ [Q28] NC State: „Long-day onions bulb at 14–16 hours of daylength.“ [Q29] Der Seed-Wert 13,75 h beschreibt die Zwiebelbildung. Eine `photoperiod_based`-Schossregel an der Zwiebel wäre sachlich falsch: Sie setzte jede Zwiebel im Juni zur Zeit der Zwiebelbildung auf `bolting`.

**Rote Bete und Tageslänge.** [W]: „Following vernalization, beets still require long-days for flowering to progress“ [Q1]. Der Langtag wirkt erst **nach** dem Kältereiz; allein löst er nichts aus. Das deckt sich mit dem Steckbrief (`:41`).

### 3.4 Radieschen und Arten außerhalb des Seeds

#### Radieschen (*Raphanus sativus*)

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | weitere | Belegklasse |
|---|---|---|---|---|---|
| Kälte ab der Keimung löst das Schossen aus | [W]: „receptive from germination“, 1–3 Wochen; Rettich: „Temperaturen von 5-11°C sind besonders kritisch und können schon ab der Keimung einen Schossreiz hervorrufen.“ [Q1, Q3] | Delaware: „turnips, Chinese cabbage, and salad radishes require a greater amount of cold to initiate the bolting response“ [Q5] | Nishijima 2003: „precocious bolting and flowering by low temperature and subsequent long daylength“ [Q16] | — | **3/3** |
| Langtag (sortenabhängig) | RHS: „some radish cultivars“ [Q6] | Delaware: „some radishes (oriental types)“ [Q5] | Nishijima 2003 [Q16] | [W]: „Once vernalized, long days going into mid- to late June can cause them to bolt.“ [Q1] | **3/3** |
| Temperatur und Dauer | [W] | — | — | — | **1/3** → `null` |

**Befund.** Aufnehmen. Der Seed führt Radieschen als `day_neutral`, der Steckbrief als `long_day`; die Quellen nennen beide Auslöser, den Langtag nur für einen Teil der Sorten.

#### Nicht im Seed (festgehalten für spätere Einträge)

| Art | Fundstellen | Belegklasse |
|---|---|---|
| Chinakohl | [W]: „Temperaturen unter 20°C erhöhen das Schosserrisiko. Kritisch sind insbesondere Werte von 5-8° C … Der Schossreiz kann ab der Keimung stattfinden. Die Mindesteinwirkungszeit beträgt 1-4 Wochen.“ [Q3] · FiBL: über 20 °C; trockene Anzucht erhöht das Risiko [Q7] · Delaware [Q5] | Kälte **3/3**; „unter 20 °C riskant“ [W] und FiBL → 2/3 |
| Pak Choi | Gartenakademie: „kühle Temperaturen (unter 10 °C) und lange Tage (über 12 Stunden Tageslänge) führen zur Blüte“ [Q8] · [W]: „There is little data on mizuna and bok choi“ [Q1] | **1/3** mit Zahl; [W] ohne eigene Daten |
| Endivie | [W]: „Temperaturen unter 17°C fördern die Schosserbildung. … Gefördert … zusätzlich noch durch den Langtag.“ [Q3] · FiBL: über 18 °C [Q7] · Harrington u. a. 1959: „Vernalization of the germinating seed or of young plants hastened floral initiation“; „Long photoperiods hasten bolting“ [Q30] | Kälte **3/3**; Langtag 2/3 |
| Wilde Rauke (*Diplotaxis tenuifolia*) | Taylor u. a.: „rocket is a facultative long day plant“; Kälte von zwei bis acht Wochen ohne Wirkung auf die Schosszeit [Q31] | **1/3** |
| Feldsalat | [W]: „Temperaturen unter 10°C leiten die Blütenbildung ein.“ [Q3] | **1/3** |

### 3.5 Nicht geprüft

Basilikum (*Ocimum basilicum*), Bohnenkraut (*Satureja hortensis*), Grünkohl über die Tabelle hinaus, Blumenkohl und Brokkoli. Bei Blumenkohl und Brokkoli ist das Erntegut die Blütenanlage; das vorzeitige Auslösen heißt dort „buttoning“ ([Q1]) und ist ein anderes Ausfallbild als das Schossen einer Blattkultur. Für Basilikum führt der Steckbrief `day_neutral` und nennt Alter und Temperatur als Auslöser (`ocimum_basilicum.md:30`); eine Websuche dazu fand nicht statt.

---

## 4. Ergebnis: Aufnahme-Tabelle

„Markierung“ heißt: `trigger_type: manual`. Die Regel löst nichts aus; sie kennzeichnet den Handwechsel nach `bolting` als vorzeitig, sodass der Ausfall-Dialog `bolting` vorschlägt.

| Art | Aufnehmen | Auslöser (bestätigt) | Vorgeschlagener `trigger_type` | Belegte Parameter | Evidenz Auslöser | Abgrenzung planmäßig / vorzeitig |
|---|---|---|---|---|---|---|
| Spinat | **ja** (Bestand) | Langtag; Wärme beschleunigt | `manual` (heute `photoperiod_based`) | kritische Tageslänge `null` (Seed: 13) | 3/3 | einjährig; jede Blüte vor Ernteende ist vorzeitig |
| Salat | **ja** | Langtag; Hitze | `manual` | kritische Tageslänge `null` (Seed: 14,0) | 3/3 | einjährig; wie Spinat |
| Radieschen | **ja** | Kälte ab Keimung; Langtag (sortenabhängig) | `manual` | Temperatur, Dauer `null` | 3/3 | einjährig; wie Spinat |
| Koriander | **ja**, nur Blattnutzung | Wärme | `manual` | kritische Tageslänge `null` (Seed: 12) | 3/3 (Langtag 2/3) | Samenbau: Blüte ist das Ziel |
| Rucola | **ja** | Langtag | `manual` | kritische Tageslänge `null` (1/3: 13 h) | 3/3 | einjährig; wie Spinat |
| Knollenfenchel | **ja** | Trockenstress | `manual` | — | 3/3 (Langtag 2/3; Kälte widersprüchlich) | im Anbau einjährig; Blüte vor der Knollenernte ist vorzeitig |
| Rote Bete | **ja** | Kältereiz in Keimung und Jugend | `manual` | Temperatur, Dauer `null` | 3/3 | Regel nur aus Phasen des ersten Jahres |
| Sellerie | **ja** | Kältereiz der Jungpflanze | `manual` | Temperatur „unter 13 °C“ 3/3 (Spanne); Dauer `null` | 3/3 | wie Rote Bete |
| Knollensellerie | **ja** | Kältereiz der Jungpflanze | `manual` | wie Sellerie | 3/3 | wie Rote Bete |
| Zwiebel | **ja** | Kältereiz nach der Jugendphase | `manual` — **nicht** `photoperiod_based` | Temperatur `null` (2/3: unter 10 °C); Dauer `null` | 3/3 | Regel aus `vegetative`, nicht aus `dormancy`; planmäßig bleibt `dormancy → flowering` |
| Möhre | **ja** | Kältereiz nach der Jugendphase | `manual` | `null` | 3/3 | wie Rote Bete |
| Kohlrabi | **ja** | Kältereiz der Jungpflanze | `manual` | Temperatur „unter 14 °C“ 3/3 (Spanne); Dauer `null` | 3/3 | wie Rote Bete |
| Kopfkohl | **ja** | Kältereiz der Jungpflanze | `manual` | Temperatur „unter 10 °C“ 3/3 (Spanne); Dauer `null` | 3/3 | wie Rote Bete |
| Dill | **offen** | Hitze | — | — | 3/3 (Langtag 2/3) | Blüte ist reguläres Erntegut |
| Lauch | **offen** | Kältereiz ab 3-Blatt-Stadium | — | `null` | 2/3 | wie Rote Bete |
| Petersilie | **offen** | Kältereiz der Jungpflanze | — | `null` | 2/3 | Regel dürfte nur vor `dormancy` ansetzen |
| Rosenkohl, Grünkohl | **offen** | Kältereiz der Jungpflanze | — | `null` | 2/3 | — |
| Chicorée, Radicchio | **offen** | Kältereiz ab Keimung | — | `null` | 2/3 | im Seed mehrjährig geführt |
| Pastinake | **nein** | — | — | — | 1/3 | Schossen im zweiten Jahr ist planmäßig; vorzeitiges nicht belegt |
| Basilikum, Bohnenkraut | **nein** (nicht geprüft) | — | — | — | — | — |
| Blumenkohl, Brokkoli | **nein** | — | — | — | — | Erntegut ist die Blütenanlage |
| Knoblauch, Schnittlauch, mehrjährige Kräuter, Rhabarber, Spargel | **nein** | — | — | — | — | planmäßige jährliche Blüte |

Ergebnis in Zahlen: 13 Einträge „ja“ (Spinat und zwölf neue), 5 Zeilen „offen“ mit 6 Arten, der Rest „nein“.

---

## 5. Was die Engine nicht abbilden kann

| Auslöser | Arten | Vorhandener Trigger | Was fehlt | Folge für die Regel |
|---|---|---|---|---|
| Langtag | Spinat, Salat, Rucola (Radieschen, Koriander, Dill, Fenchel teilweise) | `photoperiod_based` | Ein 3/3 belegter Schwellenwert. Für Salat ist keiner zu erwarten (fakultativ). Außerdem trennt „Tageslänge > x“ das vorzeitige Schossen nicht vom normalen Sommer: Auf 50° N liegt die Tageslänge vom 20.04. bis 22.08. über 14 h. | Mit `null` feuert der Trigger nie. Mit einem unbelegten Wert feuerte er — sobald der Scan läuft — für fast jede Frühjahrs- und Sommerkultur. **Inert oder falsch.** |
| Kältereiz der Jungpflanze | Rote Bete, Sellerie, Zwiebel, Möhre, Kohlrabi, Kopfkohl, Radieschen (Lauch, Petersilie) | `vernalization_based` | (1) Der Zähler `chill_days_accumulated` wird nicht fortgeschrieben; der Task ist nicht geplant und bräuchte eine Temperatur je Standort. (2) Die Kälteschwelle ist fest 5 °C Tagesmittel; die Quellen nennen wirksame Temperaturen bis 12–18 °C. (3) Kein Bezug zum Entwicklungsstadium (Jugendphase, Blattzahl). (4) `vernalization_min_days` dient bereits dem **planmäßigen** Schossen im zweiten Jahr; dieselbe Zahl kann nicht zugleich die Schwelle des vorzeitigen sein. (5) Keine Devernalisation. (6) Die Anzucht findet oft außerhalb der Software statt (zugekaufte Jungpflanzen). | **Inert.** Eine Regel mit `vernalization_based` löste nie aus und läse, wenn der Zähler liefe, den falschen Parameter. |
| Hitze | Salat, Koriander, Dill (Spinat, Fenchel beschleunigend) | keiner | Temperatur-Trigger | **Nicht abbildbar.** |
| Trockenstress | Knollenfenchel (Rucola, Spinat 1–2/3) | keiner | Stress-Trigger; die Bodenwasser-Bilanz (F-29) ist nicht mit Phasenübergängen verbunden | **Nicht abbildbar.** |
| Alle | alle | — | `check_auto_transitions` ist nicht geplant | **Jeder** Trigger ist heute inert, auch der bestehende beim Spinat. |

Je Art ehrlich benannt:

- **Spinat:** `photoperiod_based` ist heute inert (Scan läuft nicht) und wäre mit dem unbelegten Wert 13 h bei laufendem Scan falsch (§1.3 Nr. 3).
- **Salat, Rucola:** `photoperiod_based` wäre inert (kein belegter Wert) oder falsch.
- **Radieschen, Rote Bete, Sellerie, Knollensellerie, Zwiebel, Möhre, Kohlrabi, Kopfkohl:** `vernalization_based` wäre inert.
- **Koriander, Knollenfenchel:** kein passender Trigger-Typ.

Die Markierung (`manual`) ist für alle dreizehn Arten wirksam, weil sie am Handwechsel hängt und nicht am Scan.

---

## 6. Entscheidungsvorlage für den Betreiber

Jede Frage ist einzeln beantwortbar. Der Vorschlag steht zuerst.

**Frage 1 — Liste der Arten.** Vorschlag: Die dreizehn Einträge „ja“ aus §4 tragen eine Schoss-Regel: Spinat, Salat, Radieschen, Koriander, Rucola, Knollenfenchel, Rote Bete, Sellerie, Knollensellerie, Zwiebel, Möhre, Kohlrabi, Kopfkohl.
- Alternative A: nur die sechs im Issue genannten Arten, soweit im Seed vorhanden (Salat, Radieschen, Koriander, Rucola, Fenchel; Pak Choi fehlt im Seed) — Folge: Zweijährige mit Kältereiz bleiben ohne Vorschlag, obwohl sie 3/3 belegt sind.
- Alternative B: zusätzlich die „offen“-Arten mit 2/3 (Lauch, Petersilie, Rosenkohl, Grünkohl, Chicorée) — Folge: verstößt gegen E-10; der Betreiber trüge die Aufnahme als eigene Festlegung.

**Frage 2 — Kräuter mit Doppelnutzung.** Vorschlag: Koriander aufnehmen, Dill nicht. Beim Dill ist die Blüte reguläres Erntegut (Phase `flowering` mit Ernte); die Regel markierte eine gewollte Blüte als Ausfall.
- Alternative: beide aufnehmen — Folge: Der Nutzer, der Dolden oder Koriandersamen ernten will, bekommt beim Entfernen `bolting` vorgeschlagen und muss es abwählen. Die Regel greift nur, wenn er die Pflanze von Hand nach `bolting` setzt; wer Samen will, setzt sie nach `flowering`.

**Frage 3 — Trigger-Typ der neuen Regeln.** Vorschlag: `trigger_type: manual` für alle neuen Regeln. Die Regel ist eine Markierung.
- Alternative: `photoperiod_based` bei den Langtag-Arten, `vernalization_based` bei den Kälte-Arten, wie REQ-003 E6 es nahelegt — Folge: Heute kein Unterschied (Scan läuft nicht). Sobald der Scan eingeplant wird, feuern die Langtag-Regeln mit jedem gesetzten Schwellenwert zu früh und die Kälte-Regeln nie (§5).

**Frage 4 — Bestehende Spinat-Regel.** Vorschlag: auf `manual` umstellen und eine zweite Regel `ripening → bolting` ergänzen, weil die Ernte in `ripening` liegt (§1.3 Nr. 2).
- Alternative: `photoperiod_based` belassen — Folge: bleibt als Fußangel für den Tag, an dem der Scan eingeplant wird.

**Frage 5 — Kritische Tageslänge von Spinat (13 h).** Stand: keine verifizierte Quelle mit Zahl; ein Suchauszug nennt „über 13 und unter 15 h“ für Jungpflanzen einer Sorte. Vorschlag: `critical_day_length_hours` bleibt im Lebenszyklus stehen (das Feld dient auch anderen Lesern, etwa dem Zelt-Hinweis), wird aber nicht als Schoss-Schwelle verwendet.
- Alternative: Wert auf `null` setzen, bis die HortScience-Arbeit gelesen ist — Folge: sauber nach E-10; zu prüfen wäre, welche anderen Leser den Wert brauchen (`tent_rules_engine.py:110-117` nimmt sonst 12 h an).

**Frage 6 — Schwellenwerte „3/3 (Spanne)“.** Drei Temperaturwerte liegen in den Angaben dreier unabhängiger Quellen: Sellerie „unter 13 °C“, Kohlrabi „unter 14 °C“, Kopfkohl „unter 10 °C“. Sie haben heute kein Feld (die Kälteschwelle ist fest 5 °C). Vorschlag: im Steckbrief als Freitext mit Quelle festhalten, nicht ins Datenmodell.
- Alternative: Feld für eine artspezifische Kälteschwelle der Jungpflanze anlegen — Folge: REQ-003-Änderung; ohne laufende Temperaturzählung je Standort bleibt das Feld ungelesen.

**Frage 7 — Werte mit 2/3 oder weniger.** Sie bleiben nach E-10 `null`: Zwiebel „unter 10 °C“ (2/3), Rucola „13 h“ (1/3), Pak Choi „unter 10 °C und über 12 h“ (1/3), alle Einwirkdauern. Vorschlag: bestätigen.

**Frage 8 — Nicht abbildbare Auslöser (Hitze, Trockenheit, Kältereiz der Jungpflanze).** Vorschlag: nicht nachbauen. Der Nutzer sieht das Schossen am Beet früher und sicherer, als ein Modell es schätzt; die Markierung genügt für F-19.
- Alternative: Folge-Issue für einen Hinweis „Schossgefahr“ aus Standortwetter (Tageslänge, Nachttemperaturen in der Jugendphase, Trockenheit aus F-29) — Folge: ein Hinweis an den Nutzer, kein automatischer Phasenwechsel; setzt Wetter je Standort voraus (derselbe Engpass wie bei `check_dormancy_triggers`).

**Frage 9 — Arten, die im Seed fehlen.** Pak Choi, Chinakohl, Endivie, Feldsalat, wilde Rauke, Mangold und Rettich als eigene Einträge. Vorschlag: nicht Teil von #3152; als Steckbrief-Aufträge erfassen, wenn die Arten gewünscht sind. Für Chinakohl und Endivie ist der Kältereiz bereits 3/3 belegt (§3.4).

**Frage 10 — Wortlaut von REQ-003 E6.** E6 nennt „`conditional`/`photoperiod_based`“ und als Ursache „Hitze-/Langtag-Stress“; die Zweijährigen mit Kältereiz und die Markierung über `manual` fehlen. Vorschlag: E6 um den Kältereiz der Jungpflanze und um `manual` als zulässigen Typ ergänzen, vor dem Seed (Spec vor Code).

---

## 7. Was diese Prüfung nicht leistet

- **Keine Sortenebene.** Schossfestigkeit ist ein Sortenmerkmal; mehrere Quellen nennen sie als wichtigste Gegenmaßnahme ([Q3], [Q5], [Q6], [Q8]). Die Regel hängt an der Art. Eine schossfeste Sorte bekommt denselben Vorschlag.
- **Keine Primärliteratur zu den Vernalisationszahlen.** Wiebe 1990 und Krug 1991 wurden nur über [Q1] und [Q2] gelesen. Die Arbeiten, auf die [Q1] je Kultur verweist (Elers und Wiebe 1984, Wiebe u. a. 1992, Wiebe 1994, Atherton u. a., Streck 2003), wurden nicht geöffnet. Mit ihnen könnten einzelne Zahlen 3/3 erreichen; ob sie unabhängig von der Linie W sind, wäre je Arbeit zu prüfen (drei davon stammen von Wiebe selbst).
- **Keine eigene Datenauswertung.** Die Aussagen zum Verhalten bei eingeplantem Scan (§1.3 Nr. 3) folgen aus dem gelesenen Code und einer Tageslängenrechnung, nicht aus einem Lauf.
- **Kein Klimabezug.** Die Quellen stammen aus Mitteleuropa, Großbritannien, den USA und Japan. Ob ein Kältereiz in einer bestimmten Lage tatsächlich eintritt, sagt die Liste nicht.
- **Keine Prüfung der Lebenszyklus-Felder außerhalb des Schossens.** Die Abweichungen in §2.4 sind gemessen, aber nicht bewertet; welcher Wert richtig ist, wäre je Feld eine eigene E-10-Prüfung. Insbesondere ist nicht geprüft, welcher Lader gewinnt, wenn eine Art in zwei Seed-Dateien einen Lebenszyklus trägt (Möhre, Chicorée).
- **Nicht geprüfte Arten.** Basilikum, Bohnenkraut, Blumenkohl, Brokkoli (§3.5).
- **Keine Aussage zur Oberfläche.** Ob der Nutzer die Phase `bolting` im Phasenwechsel-Dialog findet und versteht, ist nicht untersucht. Ohne diesen Handwechsel bleibt jede Regel wirkungslos.

---

## 8. Folgeschritte für die Umsetzung

1. **Steckbriefe zuerst.** Je aufgenommener Art im Steckbrief einen Abschnitt „Vorzeitiges Schossen“ ergänzen: Auslöser, Belegklasse, Quellen aus §9; Zahlen nur, wo 3/3. Dabei die Abweichungen aus §2.4 an den Feldern `photoperiod_type`, `critical_day_length_hours`, `vernalization_min_days` klären oder als offen kennzeichnen (Agenten `growing-phase-auditor`, danach `plant-info-to-seed-yaml`).
2. **REQ-003 E6 nachziehen** (Frage 10), vor dem Seed.
3. **Ort der Regeln festlegen.** Übergangsregeln kennt nur `lifecycles_outdoor.yaml`. Zwei Wege:
   - **a)** Die zwölf neuen Arten nach `lifecycles_outdoor.yaml` umziehen, wie für die mehrjährigen Arten geschehen (Hinweis in `plant_info_outdoor_1.yaml:1980-1987`: kein Lebenszyklus doppelt). Aufwand: Phasen, Profile und Zuordnungen mitnehmen; `adventskalender.yaml` und `plant_info*.yaml` verlieren die Einträge.
   - **b)** `transition_rules` in die Schemas und Lader von `plant_info*.yaml` und `adventskalender.yaml` aufnehmen. Aufwand: drei Lader, zwei Schemas; die Regel-Logik aus `seed_lifecycles_outdoor.py:67-115` wiederverwenden statt kopieren.
   Für Rucola, Kohlrabi und Kopfkohl muss zuerst ein Lebenszyklus-Eintrag entstehen.
4. **Je Art:** Phase `bolting` außerhalb des linearen Pfads (wie beim Spinat: höchste `sequence_order`, `is_terminal: true`, `allows_harvest: false`) und je eine Regel aus **jeder** Phase, in der die Kultur steht, wenn sie schosst: bei Blattkulturen `vegetative` und die Erntephase, bei Zweijährigen die Phasen des ersten Jahres, nie `dormancy`.
5. **Migration.** Bestehende Installationen bekommen Phase und Regeln nur über eine Migration; die Regel-Anlage in `_seed_transition_rules` ist idempotent (`:102`), die Phase muss es ebenfalls sein. Ein geänderter `trigger_type` an der bestehenden Spinat-Regel wird von der Idempotenzprüfung nicht überschrieben — das braucht einen eigenen Schritt.
6. **Test, der die Liste festnagelt.** Ein Unit-Test über alle Seed-Dateien, der die Menge der Arten mit einer `is_premature`-Regel nach `bolting` gegen eine ausgeschriebene Liste vergleicht (Gleichheit, nicht Teilmenge), und je Art prüft: Die Zielphase heißt `bolting` (`BOLTING_PHASE_NAME`); keine Regel geht von `dormancy` aus; kein zweijähriger Lebenszyklus erreicht `bolting` ohne `is_premature`-Regel; jede Phase mit `allows_harvest: true` einer aufgenommenen Blattkultur hat eine Regel nach `bolting`. Die Gegenprobe gehört dazu: eine Art aus der Liste streichen und sehen, dass der Test rot wird.
7. **Test am Verhalten.** Für eine neue Art (etwa Salat) und für eine Zweijährige (etwa Zwiebel): Handwechsel in `bolting` aus der Erntephase → `termination-options` liefert `suggested_cause = bolting`; Handwechsel `dormancy → flowering` bei der Zwiebel → kein Vorschlag (Akzeptanzkriterium 2 von #3152).
8. **Guard gegen die Fußangel.** Solange Schoss-Regeln einen automatischen Typ tragen dürften: ein Test, der für jede `is_premature`-Regel `trigger_type == manual` verlangt, bis eine Betreiberentscheidung (Frage 3) etwas anderes festlegt.

---

## 9. Quellen

Prüftiefe „verifiziert“: für dieses Dokument am 2026-11-27 abgerufen und im Volltext gelesen. „o. J.“, wo die Seite kein Datum trägt. Die Spalte „Entnommene Aussage“ nennt, wofür die Quelle hier steht; die Wortlaute stehen in §3.

| Nr. | Titel, Herausgeber, Jahr | URL | Entnommene Aussage | Prüftiefe |
|---|---|---|---|---|
| Q1 | Phillips, Goldy, Brainard: „Bolting in spring vegetables“, Michigan State University Extension, 20.05.2020. Gelesen über das Internet Archive; die Originalseite wies den Abruf ab. Tabelle 1 nach Wiebe 1990 | <https://www.canr.msu.edu/news/bolting-in-spring-vegetables> (Archiv: <https://web.archive.org/web/2024/https://www.canr.msu.edu/news/bolting-in-spring-vegetables>) | Vernalisationsbereiche, Jugendphasen, Einwirkdauer und Devernalisation für 25 Kulturen; Rote Bete braucht nach der Kälte den Langtag; wenig Daten zu Pak Choi | verifiziert |
| Q2 | Schlaghecken (Artikelautor; Mitwirkende Krug, Wiebe, Ziegler): „Schossverhalten wichtiger Gemüsearten“, Hortipendium, DLR Rheinpfalz (o. J.); Quelle: Krug 1991, „Gemüseproduktion“. Zählt mit Q1 | <https://www.hortipendium.de/Schossverhalten_wichtiger_Gemüsearten> | Tabelle der Vernalisationsdaten; Kälte ohne Jugendphase bei Chinakohl und Rettich; Langtag beschleunigt nach der Vernalisation | verifiziert |
| Q3 | Hortipendium, DLR Rheinpfalz — Kulturseiten Erwerbsanbau (o. J.): Spinat, Chinakohl, Knollenfenchel, Porree, Kohlrabi, Knollensellerie und Bundsellerie, Speise Bete, Endivien, Rucola, Dill, Petersilie, Feldsalat, Rettich, Koriander. Zählt mit Q1 und Q2 | <https://www.hortipendium.de/Spinat_Erwerbsanbau>, <https://www.hortipendium.de/Chinakohl>, <https://www.hortipendium.de/Knollenfenchel>, <https://www.hortipendium.de/Porree>, <https://www.hortipendium.de/Kohlrabi_Erwerbsanbau>, <https://www.hortipendium.de/Knollensellerie_und_Bundsellerie_Erwerbsanbau>, <https://www.hortipendium.de/Speise_Bete_Erwerbsanbau>, <https://www.hortipendium.de/Endivien_Erwerbsanbau>, <https://www.hortipendium.de/Rucola_Erwerbsanbau>, <https://www.hortipendium.de/Dill_Erwerbsanbau>, <https://www.hortipendium.de/Petersilie_Erwerbsanbau>, <https://www.hortipendium.de/Feldsalat_Erwerbsanbau>, <https://www.hortipendium.de/Rettich_Erwerbsanbau>, <https://www.hortipendium.de/Koriander> | Langtag bei Spinat, Rucola, Dill, Fenchel; Trockenstress bei Fenchel; kein Kälterisiko bei Fenchel und Rucola; Kälteschwellen bei Sellerie, Kohlrabi, Lauch, Chinakohl, Endivie, Rettich, Speise Bete | verifiziert |
| Q4 | Zandstra u. a.: „Commercial Vegetable Recommendations: Onions“, MSU Extension Bulletin E1307, 1996 (Archivkopie); „Celery“, Bulletin E1308 (über das Internet Archive). Zählt mit Q1 | <https://archive.lib.msu.edu/DMC/extension_publications/e1307/E1307-1996.PDF>, <https://www.canr.msu.edu/resources/celery_commercial_vegetable_recommendations_e1308> | Zwiebel: Schossen nach dem Fünfblattstadium bei unter 50 °F über mehrere Tage; Sellerie: unter 55 °F über 7 Tage oder länger | verifiziert |
| Q5 | Johnson: „Bolting in Spring Planted Vegetables“, University of Delaware Cooperative Extension, Weekly Crop Update, 19.05.2023 | <https://sites.udel.edu/weeklycropupdate/?p=22287> | Langtag bei Spinat, Salat, Rettich; Hitze bei Spinat und Salat; Kälte bei Kreuzblütlern, Kohl, Rote Bete, Möhre, Zwiebel | verifiziert |
| Q6 | Royal Horticultural Society: „Bolting in vegetables“ (o. J.); „Florence fennel – grow your own“ (o. J.) | <https://www.rhs.org.uk/advice/profile?pid=262>, <https://www.rhs.org.uk/vegetables/florence-fennel/grow-your-own> | Einjährige Langtagpflanzen (Salat, Radieschen, Spinat); Zweijährige nach Kälteperiode (Zwiebel, Lauch, Möhre, Rote Bete); trockener Boden bei Blumenkohl, Rucola, Spinat; Fenchel schosst bei Trockenheit und früher Saat | verifiziert |
| Q7 | Lichtenhahn u. a.: „Biogemüsebau: Anzucht und Einsatz von Jungpflanzen“, FiBL-Merkblatt 1212, 2. Auflage 2001 | <https://www.fibl.org/fileadmin/documents/shop/1212-gemuesejungpflanzen.pdf> | Mindest-Anzuchttemperaturen schossgefährdeter Arten: über 22 °C Radicchio, 20 °C Chinakohl, 18 °C Endivie, 16 °C Sellerie und Knollenfenchel, 14 °C Kopf- und Rosenkohl, Kohlrabi, Petersilie; Salat temperaturindifferent | verifiziert |
| Q8 | LWG Bayern, Bayerische Gartenakademie: Merkblatt 2110 „Jungpflanzen – selbst anziehen oder kaufen?“ (2020); Merkblatt 2156 „Pak Choi“ (o. J.); Merkblatt 2155 „Mangold – ein uraltes Gemüse“ (2016) | <https://www.lwg.bayern.de/mam/cms06/gartenakademie/dateien/2110-2020.pdf>, <https://www.lwg.bayern.de/mam/cms06/gartenakademie/dateien/2156_pak_choi.pdf>, <https://www.lwg.bayern.de/mam/cms06/gartenakademie/dateien/2155-2016.pdf> | Kohlrabi, Frühkohl, Blumenkohl, Sellerie nie unter 14–16 °C anziehen; Pak Choi: unter 10 °C und über 12 h; Mangold: zu frühe Aussaat führt zu Schossern | verifiziert |
| Q9 | Lerner: „Lettuce Bolting“, Purdue University, Plant and Pest Diagnostic Laboratory, Picture of the Week, 2021 | <https://ag.purdue.edu/department/btny/ppdl/potw-dept-folder/2021/lettuce-bolting.html> | Salat und Spinat schossen mit längeren Tagen; Hitze und trockener Boden beschleunigen; Zweijährige nach Kälte erst ab einem Entwicklungsstadium | verifiziert |
| Q10 | University of California, Statewide IPM Program: „Bolting“ (o. J.) | <https://ipm.ucanr.edu/home-and-landscape/bolting/> | Salat: hohe Temperaturen; Spinat: lange Tage; Kohlarten: anhaltende Kälte unter 50 °F | verifiziert |
| Q11 | Han, Truco, Lavelle, Michelmore: „A Composite Analysis of Flowering Time Regulation in Lettuce“, Frontiers in Plant Science 12:632708, 2021 | <https://pmc.ncbi.nlm.nih.gov/articles/PMC7982828> | Salat ist fakultative Langtagpflanze mit starker Sortenstreuung; hitzebeschleunigtes Schossen ist verbreitet | verifiziert |
| Q12 | Han, Chen, Lv u. a.: „MADS-Box Genes and Gibberellins Regulate Bolting in Lettuce (Lactuca sativa L.)“, Frontiers in Plant Science 7:1889, 2016 | <https://www.frontiersin.org/articles/10.3389/fpls.2016.01889/full> | Hohe Temperatur fördert das Schossen von Salat | verifiziert |
| Q13 | Verkerk, Volosky Yadlin: „The effect of daylength, gibberellin, seedvernalization and their interaction on spinach“, Netherlands Journal of Agricultural Science, 1959; Parlevliet: „The influence of sowing date and germination temperature on yield of spinach and chervil“, Neth. J. Agric. Sci. 16:53–57, 1968 | <https://library.wur.nl/ojs/index.php/njas/article/download/17674/17088/18795>, <https://library.wur.nl/ojs/index.php/njas/article/download/17426/16840> | Langtag ist für das Schossen von Spinat der Hauptfaktor, Vernalisation wirkt schwach; Kälte in Keimung und Jungpflanze verfrüht die Blüte | verifiziert |
| Q14 | Utah State University Extension: „How to Grow Spinach in Your Garden“ (o. J.) | <https://extension.usu.edu/yardandgarden/research/spinach-in-the-garden> | Spinat schosst bei langen Tagen und Wärme | verifiziert |
| Q15 | University of Arizona Cooperative Extension: „Growing Spinach“, Backyard Gardener Nr. 173 (o. J.) | <https://extension.arizona.edu/sites/default/files/attachment/Spinach.pdf> | Spinat schosst mit heißeren und längeren Tagen | verifiziert |
| Q16 | Nishijima: „Effect of Gibberellin Biosynthesis Inhibitor on Prevention of Precocious Bolting and Flowering in Japanese Radish“, JARQ 37(3):175–181, 2003 | <https://www.jircas.go.jp/sites/default/files/publication/jarq/37-03-05_0.pdf> | Vorzeitiges Schossen von Rettich durch Kälte und anschließenden Langtag | verifiziert |
| Q17 | Oregon State University Extension: „How to grow cilantro for leaves — or coriander seeds“ (o. J.) | <https://extension.oregonstate.edu/news/how-grow-cilantro-leaves-or-coriander-seeds> | Temperatur und Tageslänge steuern die Blüte von Koriander; im Hochsommer Blüte in vier bis sechs Wochen | verifiziert |
| Q18 | University of Wisconsin–Madison Extension, Wisconsin Horticulture: „Cilantro / Coriander, Coriandrum sativum“ (o. J.) | <https://hort.extension.wisc.edu/articles/cilantro-coriander-coriandrum-sativum/> | Koriander schosst bei Hitze; keine Sorte hält bei Hitze und langen Tagen | verifiziert |
| Q19 | Utah State University Extension: „Cilantro/Coriander in the Garden“ (o. J.). Zählt mit Q14 | <https://extension.usu.edu/yardandgarden/research/cilantro-coriander-in-the-garden> | Gegen das Schossen: früh und kühl pflanzen, Boden kühl halten | verifiziert |
| Q20 | University of Wisconsin–Madison Extension, Wisconsin Horticulture: „Arugula, Eruca sativa“ (o. J.). Zählt mit Q18 | <https://hort.extension.wisc.edu/articles/arugula> | Rucola schosst bei langen Tagen, Hitze oder trockenem Boden | verifiziert |
| Q21 | University of Illinois Extension, Good Growing: „Arugula: A New Trendy Green from the Old World“, 07.11.2018 | <https://extension.illinois.edu/blogs/good-growing/2018-11-07-arugula-new-trendy-green-old-world> | Sommerhitze und lange Tage lösen die Blüte von Rucola aus | verifiziert |
| Q22 | Koike: „Effect of Photoperiod on Flowering of Eruca sativa Mill.“, Eco-Engineering 20(2):85–87, 2008 | <https://www.jstage.jst.go.jp/article/seitaikogaku/20/2/20_2_85/_article/-char/en> | Blütenknospen ab 13 h Photoperiode | verifiziert (nur Zusammenfassung) |
| Q23 | Utah State University Extension: „How to Grow Fennel in Your Garden“ (o. J.). Zählt mit Q14 | <https://extension.usu.edu/yardandgarden/research/fennel-in-the-garden.php> | Fenchel schosst bei Wassermangel und Wurzelschäden; Hitze und lange Tage beschleunigen | verifiziert |
| Q24 | Boelt: „Seed rate, sowing time and harvest time in dill (Anethum graveolens L.) for freeze drying“, Tidsskrift for Planteavl 94:497–502, 1990, Statens Planteavlsforsøg, Beretning 2103 | <https://dcapub.au.dk/pub/planteavl_94_497.pdf> | Dill ist Langtagpflanze; zunehmende Tageslänge und höhere Temperatur fördern das Erscheinen der Dolden | verifiziert |
| Q25 | Utah State University Extension: „How to Grow Dill in Your Garden“ (o. J.). Zählt mit Q14 | <https://extension.usu.edu/yardandgarden/research/dill-in-the-garden> | Hitze und Dichtstand fördern das Schossen von Dill | verifiziert |
| Q26 | UC Master Gardeners of Sonoma County: „Dill“ (o. J.) | <https://ucanr.edu/site/mg-sonoma/dill> | Dill schosst bei hohen Sommertemperaturen | verifiziert |
| Q27 | UMass Extension Vegetable Program: „Celery“ (Fact Sheet, o. J.). Gelesen über das Internet Archive; die Originalseite antwortete mit HTTP 403 | <https://www.umass.edu/agriculture-food-environment/vegetable/fact-sheets/celery> | Sellerie schosst nach 10 bis 14 Tagen unter 40 °F; Gewächshaus über 55 °F halten | verifiziert |
| Q28 | University of Missouri, Integrated Pest Management: „Why Onions Bolt, Failing to Bulb?“, Missouri Produce Growers Bulletin, 01.11.2010 | <https://ipm.missouri.edu/mpg/2010/11/Why-Onions-Bolt-Failing-to-Bulb> | Zwiebel: unter 50 °F über 3 bis 4 Wochen; Schossen nicht durch die Photoperiode ausgelöst; Zwiebelbildung braucht 12 bis 16 h | verifiziert |
| Q29 | NC State Extension: „Bulb Onions“ (o. J.) | <https://content.ces.ncsu.edu/publication/bulb-onions> | Zwiebel schosst bei anhaltender oder extremer Kälte; Langtagzwiebeln bilden bei 14 bis 16 h | verifiziert |
| Q30 | Harrington, Verkerk, Doorenbos: „Interaction of vernalization, photoperiod and light intensity in floral initiation of endive“, Netherlands Journal of Agricultural Science, 1959. Zählt mit Q13 | <https://library.wur.nl/ojs/index.php/njas/article/download/17695/17109/18816> | Endivie: Vernalisation von Keimling oder Jungpflanze verfrüht die Blüte; Langtag beschleunigt | verifiziert |
| Q31 | Taylor, Massiah, Kennedy, Hong, Jackson: „FLC expression is down-regulated by cold treatment in Diplotaxis tenuifolia (wild rocket), but flowering time is unaffected“, Journal of Plant Physiology, 2017 | <https://pmc.ncbi.nlm.nih.gov/articles/PMC5477103> | Wilde Rauke ist fakultative Langtagpflanze ohne Vernalisationsbedarf | verifiziert |
| Q32 | Wolfe: „Day Length and Your Vegetable Garden“, WSU Extension, Skagit County Master Gardeners, 27.04.2012. Sammelliste nach Oregon State, Arizona und MSU; zählt nicht | <https://wpcdn.web.wsu.edu/extension/uploads/sites/57/2020/04/04-27-12_Day-Length-Vegetable-Gardens.pdf> | Pauschale Einteilung „Long Day Plants (Day Length > 12 hrs)“ | verifiziert, nicht eigenständig |

Nicht geöffnet und daher ohne Belegwert: Wiebe 1990 (Acta Horticulturae 267:323–328); Krug 1991 („Gemüseproduktion“, Parey); HortScience 35(4):624–626 und 51(5):481; „Photoperiodic Responses of Dill, a Very Sensitive Long Day Plant“ (Botanical Gazette); University of Minnesota Extension „Non-pest issues in cool-season crops“; OMAFRA „Florence Fennel“; UF/IFAS „Cilantro – Great for Cool Season Gardening“; University of Hawaii „Onion“ (HI-HV99); Sächsische Gartenakademie „Chinakohl“; Springer, Euphytica BF00035662.
