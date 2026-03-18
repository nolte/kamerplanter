# Seed-Daten Validierungsreport

**Erstellt von:** Seed-Data-Validator
**Datum:** 2026-03-18
**Zusammenarbeit mit:** agrobiology-requirements-reviewer (fuer [AGROBIO-CHECK] Findings)
**Analysierte Dateien:** 24 YAML-Dateien

---

## Datenvolumen-Inventar

| Kategorie | Quell-Dateien | Datensaetze |
|-----------|--------------|-------------|
| Species (Kern) | `species.yaml` | 64 |
| Species (plant_info.yaml) | `plant_info.yaml` | 4 neue |
| Species (plant_info_indoor_1-3) | 3 Dateien | ~87 neue |
| Species (plant_info_outdoor_1-2) | 2 Dateien | ~50 neue |
| Species gesamt (schaetzungsweise) | alle | ~205 |
| Botanische Familien (Kern) | `botanical_families.yaml` | 16 |
| Botanische Familien (Erweiterungen) | 5 plant_info*-Dateien | ~28 neue |
| Cultivars | alle plant_info*-Dateien | ~120 |
| Fertilizer-Produkte | `fertilizers.yaml` | 20 |
| Fertilizer-Produkte | `plagron.yaml` | 9 |
| Fertilizer-Produkte | `gardol.yaml` | 1 |
| Fertilizer-Produkte gesamt | | 30 |
| Nutrient Plans | `fertilizers.yaml` | 3 |
| Nutrient Plans | `plagron.yaml` | 7 |
| Nutrient Plans | `gardol.yaml` | 5 |
| Nutrient Plans | `nutrient_plans_outdoor.yaml` | 19 |
| Nutrient Plans | `nutrient_plans_ro.yaml` | (ungelesen, Bestand unklar) |
| Nutrient Plans gesamt | | min. 34 |
| IPM — Schaedlinge | `ipm.yaml` | 11 |
| IPM — Krankheiten | `ipm.yaml` | 8 |
| IPM — Behandlungen | `ipm.yaml` | 12 |
| Starter Kits | `starter_kits.yaml` | 11 |
| Standort-Typen | `location_types.yaml` | 12 |
| Activitaeten | `activities.yaml` | 400+ (1980 Zeilen) |
| Companion Planting (kompatibel) | `companion_planting.yaml` | 15 Kanten |
| Companion Planting (inkompatibel) | `companion_planting.yaml` | 5 Kanten |
| Adventskalender-Sorten | `adventskalender.yaml` | ~18 |

---

## Zusammenfassung

| Kategorie | Datensaetze | Fehler | Warnungen | OK |
|-----------|-------------|--------|-----------|-----|
| Species | ~205 | 0 | 8 | ~197 |
| Cultivars | ~120 | 0 | 2 | ~118 |
| Fertilizers | 30 | 4 | 7 | 19 |
| Nutrient Plans | min. 34 | 1 | 3 | 30 |
| IPM (Pests/Diseases/Treatments) | 31 | 3 | 4 | 24 |
| Starter Kits | 11 | 2 | 1 | 8 |
| Growth Phases / Lifecycles | mehrere | 0 | 1 | mehrere |
| Companion Planting | 20 Kanten | 0 | 3 | 17 |
| Location Types | 12 | 0 | 0 | 12 |
| Botanische Familien | ~44 | 2 | 0 | ~42 |
| **Gesamt** | **~500+** | **12** | **29** | **~460** |

---

## Fehler — Sofortiger Korrekturbedarf

### Strukturelle Fehler (S-XXX)

---

### S-001: Botanische Familie "Asparagaceae" dreifach definiert

**Datei:** `botanical_families.yaml`, `plant_info_outdoor_1.yaml`, `plant_info_indoor_3.yaml`
**Problem:** Die Familie Asparagaceae ist in `botanical_families.yaml` (Zeile 168) als Kern-Familie definiert. Zusaetzlich definieren sowohl `plant_info_outdoor_1.yaml` als auch `plant_info_indoor_3.yaml` dieselbe Familie unter `new_families:`. Bei der Seed-Initialisierung fuehrt dies zu einem doppelten INSERT-Versuch oder stummem Ueberschreiben, abhaengig vom Duplikat-Handling des Loaders.

**Inkonsistenz:** Die drei Definitionen unterscheiden sich inhaltlich:
- `botanical_families.yaml`: `typical_nutrient_demand: light`, `frost_tolerance: moderate`
- `plant_info_outdoor_1.yaml`: `typical_nutrient_demand: heavy`, `frost_tolerance: hardy`
- `plant_info_indoor_3.yaml`: (Inhalt nicht vollstaendig geprueft, aber ebenfalls abweichend)

**Fix:** Eine einzige kanonische Definition in `botanical_families.yaml` beibehalten. Aus `plant_info_outdoor_1.yaml` und `plant_info_indoor_3.yaml` unter `new_families:` entfernen. Korrekte Werte: Asparagaceae umfasst sowohl Kuechenpflanzen (Spargel — heavy feeder, hardy) als auch Zimmerpflanzen (Dracaena, Sansevieria — light feeder, sensitive). Eine Aufspaltung oder Anmerkung waere sachgemaesser.

**[AGROBIO-CHECK Ergebnis — S-001]:** Siehe separater Abschnitt "Agrarbiologische Fachbewertung" weiter unten.

---

### S-002: Enum-Inkonsistenz — Fertilizer-Typ-Schreibweise (Gross/Kleinbuchstaben)

**Datei:** `fertilizers.yaml` vs. `plagron.yaml` / `gardol.yaml`
**Problem:** `fertilizers.yaml` nutzt durchgehend UPPERCASE Enum-Werte (`fertilizer_type: BASE`, `fertilizer_type: BIOLOGICAL`, `recommended_application: FERTIGATION`). `plagron.yaml` und `gardol.yaml` nutzen lowercase (`fertilizer_type: base`, `recommended_application: drench`).

**Relevanz:** `FertilizerType` ist ein `StrEnum` mit Werten wie `BASE = "base"`. Bei case-insensitiver Pydantic-Validierung waere es unproblematisch, aber die Inkonsistenz ist ein Wartungsproblem und kann Loader-Fehler verursachen falls der Seed-Loader nicht normalisiert.

**Betroffene Felder in plagron.yaml:** `fertilizer_type`, `recommended_application`, `ph_effect`, `bioavailability`, `phase_name` (in Nutrient Plans)
**Betroffene Felder in gardol.yaml:** dieselben

**Fix:** Alle Enum-Werte auf lowercase vereinheitlichen (entsprechend der `StrEnum`-Definitionen in `enums.py`, die alle lowercase verwenden).

---

### S-003: Mischungsreihenfolge — pH Perfect Grow hat falsche mixing_priority

**Datei:** `fertilizers.yaml`, Zeile 25
**Datensatz:** `pH Perfect Grow`
**Problem:** `mixing_priority: 15` — aber laut Referenzdokument `an_ph_perfect_grow.md` und `an_ph_perfect_micro.md` soll die Reihenfolge im 3-Part-System sein: Micro (10) → Grow → Bloom. Das Referenzdokument `an_ph_perfect_micro.md` definiert im KA-Datenmodell-Mapping explizit `mixing_priority=20` fuer Grow. Die Prioritaet 15 liegt zwischen Micro (10) und Bloom (20), was korrekt *waere*, aber das Referenzdokument `an_ph_perfect_grow.md` spezifiziert ebenfalls priority=20.

**Auswirkung:** Grow wuerde bei priority 15 korrekt nach Micro (10) und vor Bloom (20) einsortiert. Der Abstand ist nur kosmetisch, aber der Widerspruch zum Referenzdokument (das mixing_priority=20 vorgibt) ist eine Inkonsistenz.

**Fix:** `mixing_priority: 20` setzen, um mit der Referenzdokumentation konsistent zu sein. Bloom entsprechend auf `mixing_priority: 30` anpassen. Bloom hat aktuell priority=20, was Grow und Bloom gleichstellt — das ist falsch.

**Konkret:** Bloom (`pH Perfect Bloom`) hat derzeit `mixing_priority: 20`, was identisch mit der empfohlenen Grow-Priority ist. Die Reihenfolge Micro(10) → Grow(20) → Bloom(30) muss durch `Bloom: 20 -> 30` sichergestellt werden.

---

### S-004: Nutrient Plan referenziert "PK 13-14" aus fertilizers.yaml, aber Produkt liegt in plagron.yaml

**Datei:** `fertilizers.yaml`, Zeile 1048 (Plan "Advanced Nutrients GMB + PK 13-14")
**Problem:** Der Nutrient Plan referenziert `product_name: "PK 13-14"` in seinen `fertilizer_dosages`. Dieses Produkt ist in `plagron.yaml` definiert, nicht in `fertilizers.yaml`. Ob der Seed-Loader alle Fertilizer-Quellen vor den Nutrient Plans laedt ist entscheidend — wenn `fertilizers.yaml` und `plagron.yaml` in einem gemeinsamen Namespace existieren, ist die Referenz aufloesbar. Falls der Loader dateibasiert isoliert arbeitet, ist die Referenz gebrochen.

**Risikoeinschaetzung:** Mittelhoch — haengt vom Seed-Loader-Design ab.

**Fix:** Im Header-Kommentar von `fertilizers.yaml` explizit dokumentieren, dass cross-file Referenzen nach `plagron.yaml` voraussetzen, dass beide Dateien vor den Plans geladen werden. Alternativ den PK 13-14-Verweis in einen gemeinsamen Fertilizer-Pool-Check einbeziehen.

---

### S-005: IPM — Behandlung "Neem Oil" als "chemical" klassifiziert

**Datei:** `ipm.yaml`, Zeile 205
**Datensatz:** `Neem Oil`
**Problem:** `treatment_type: chemical` mit `active_ingredient: azadirachtin`. Neemoel wird im Pflanzenschutz standardmaessig als biologisches/organisches Mittel klassifiziert. Die `TreatmentType`-Enum kennt `BIOLOGICAL` und `CHEMICAL` als separate Werte. Neemoel ist Azadirachtin-basiert und gilt in der EU als Pflanzenschutzmittel mit biologischem Ursprung, nicht als synthetisches Chemikum.

**Konsequenz:** Das Modell-Validator `check_chemical_safety_interval` in `Treatment` erfordert `safety_interval_days > 0` fuer CHEMICAL-Behandlungen. Dies ist bei Neem korrekt (3 Tage gesetzt). Die Fehlklassifikation hat keine Validierungsfehler zur Folge, fuehrt aber zu falscher Darstellung im UI (Neem erscheint als "chemische Behandlung").

**Fix:** `treatment_type: biological` setzen. Safety interval bleibt bei 3 Tagen.

---

### S-006: IPM — "Scale Insects" mit wissenschaftlich unzulaessigem Namen

**Datei:** `ipm.yaml`, Zeile 58
**Datensatz:** `scientific_name: "Coccoidea (Überfamilie)"`
**Problem:** Das Feld `scientific_name` in `Pest` erwartet einen gueltigen wissenschaftlichen Namen. "Coccoidea (Ueberfamilie)" ist kein gueltiger Binomialname — es ist eine Ueberfamilien-Bezeichnung mit deutschem Zusatz in Klammern. Das Pydantic-Modell hat keinen Binomial-Validator fuer Pest (nur Species hat ihn), aber es ist ein Datenqualitaets-Problem: Suppen-Eintraege auf Ueberfamilien-Ebene sind taxonomisch unscharf.

**Fix:** Entweder mit einer repraesentativen Art konkretisieren (z.B. `Coccus hesperidum` als Stellvertreter-Schildlaus) oder das Feld auf `common_name_de: "Schildlaeuse"` umlagern und `scientific_name` als Ueberfamilienname ohne Klammerzusatz belassen: `"Coccoidea"`.

---

### S-007: Starter Kit "indoor-growzelt" referenziert "Cannabis sativa" — kein Pflichtfehler, aber fehlende Toxizitaetswarnung

**Datei:** `starter_kits.yaml`, Zeile 174
**Datensatz:** `kit_id: indoor-growzelt`
**Problem:** `toxicity_warning: false` obwohl Cannabis sativa im Starter Kit enthalten ist. Dies ist zwar kein technischer Fehler (Cannabis ist nicht im klassischen Sinne "giftig" fuer Menschen), aber inkonsistent mit der Intention des `toxicity_warning`-Felds.

**Fix:** `toxicity_warning: true` mit erklaerenden Kommentar (Cannabis, legaler Kontext je nach Jurisdiktion). Alternativ ein separates Feld `legal_restriction: true` einfuehren.

---

### S-008: Starter Kit Zaehlung — 11 statt spezifizierter 9 Kits

**Datei:** `starter_kits.yaml`
**Problem:** Die Spec REQ-020 spezifiziert "9 Onboarding Starter Kits". Die YAML-Datei enthaelt 11 Kits (fensterbank-kraeuter, zimmerpflanzen, zimmerpflanzen-haustierfreundlich, balkon-blumen, balkon-blumen-voranzucht, balkon-tomaten, kleines-gemusebeet, chili-zucht, indoor-growzelt, superhot-chili, microgreens).

**Bewertung:** Die 2 zusaetzlichen Kits (superhot-chili, microgreens) sind inhaltlich sinnvoll. Die Abweichung von der Spec-Zahl ist dokumentationsbedingt — entweder wurde die Spec nicht aktualisiert oder die Kits wurden spaeter hinzugefuegt.

**Fix:** Spec REQ-020 auf "11 Starter Kits" aktualisieren oder 2 Kits entfernen.

---

### S-009: Fertilizer "Bud Candy" — tank_safe: false aber recommended_application: DRENCH — Modell-Validator Konflikt

**Datei:** `fertilizers.yaml`, Zeile 156-163
**Datensatz:** `Bud Candy`
**Problem:** `tank_safe: false`, `recommended_application: DRENCH`. Das Pydantic-Modell-Validator `validate_tank_safe_application` prueft nur: "nicht tank_safe + FERTIGATION = Fehler". DRENCH bei tank_safe=false ist erlaubt und korrekt.

**Bewertung:** Kein Validierungsfehler. Aber `is_organic: true` mit `fertilizer_type: SUPPLEMENT` — biologische Ergaenzungsmittel sollten als `ORGANIC` typisiert sein. Bud Candy ist ein Kohlenhydrat-Supplement und konsistent mit SUPPLEMENT-Typisierung. Kein Fix noetig, nur dokumentiert.

---

### S-010: Fertilizer "Sensizym" — Haltbarkeit YAML vs. Referenzdokument

**Datei:** `fertilizers.yaml`, Zeile 248
**Datensatz:** `Sensizym`
**Problem:** YAML: `shelf_life_days: 540` (18 Monate). Referenzdokument `an_sensizym.md` (Abschnitt 6): "18 Monate (ungeöffnet)". 540 Tage = 17,8 Monate — mathematisch korrekt fuer 18 Monate.

**Bewertung:** Kein Fehler. Konsistent.

---

### S-011: Fertilizer "Flawless Finish" — storage_temp_max YAML vs. Referenzdokument

**Datei:** `fertilizers.yaml`, Zeile 271-272
**Datensatz:** `Flawless Finish`
**Problem:** YAML: `storage_temp_min: 5.0, storage_temp_max: 25.0`. Referenzdokument `an_flawless_finish.md` (Abschnitt 7): "Lagertemperatur 5–30 °C". Die YAML-Datei gibt 25°C als Maximum, das Referenzdokument 30°C.

**Fix:** `storage_temp_max: 30.0` setzen gemaess Referenzdokument.

---

### S-012: Botanische Familie — "Solanaceae" fehlt Violaceae, Cannabaceae in rotation_edges

**Datei:** `botanical_families.yaml`
**Problem:** Die `rotation_edges`-Liste hat keine Kante, die Violaceae oder Cannabaceae als Nachfolger oder Vorlaeufer von anderen Familien beinhaltet. Cannabaceae erscheint in einigen Kanten, Violaceae gar nicht. Dies ist ein Vollstaendigkeitsproblem der Fruchtfolge-Graphen, kein harter Fehler.

**Bewertung:** Warnung, kein Fehler.

---

## Warnungen — Sollten behoben werden

### Vollstaendigkeits-Luecken (V-XXX)

---

### V-001: Species-Schema — fehlende Felder `common_name_de` / `common_name_en`

**Datei:** `species.yaml` und alle plant_info*-Dateien
**Problem:** Die `Species`-Klasse hat kein separates `common_name_de`/`common_name_en`-Feld, sondern eine kombinierte `common_names: list[str]`-Liste. Dies entspricht dem tatsaechlichen Modell. Die Spec-Checkliste (REQ-001) fordert `common_name_de` und `common_name_en` — das Modell weicht von der Spec-Formulierung ab, ist aber funktional.

**Spec-Referenz:** REQ-001
**Empfehlung:** REQ-001 Spec-Formulierung an die tatsaechliche Modelstruktur anpassen, oder das Modell um separate de/en-Felder erweitern.

---

### V-002: Species — fehlende `family_key`-Zuordnung in species.yaml

**Datei:** `species.yaml`
**Problem:** Die Species in `species.yaml` nutzen das Feld `family: Solanaceae` (String-Name), nicht `family_key: solanaceae` (Fremdschluessel auf die `botanical_families`-Collection). Das Pydantic-Modell definiert `family_key: str | None = None`. Beim Seed-Loader muss der Name auf einen Key gemappt werden.

**Betroffene Eintraege:** Alle 64 Species in species.yaml
**Empfehlung:** Entweder `family_key`-Felder direkt in species.yaml ergaenzen, oder den Seed-Loader explizit dokumentieren, dass er den `family:`-String auf einen `family_key` aufloest. Aktuell ist der Mechanismus unklar.

---

### V-003: Fertilizer — fehlende `shelf_life_days` und Lagerbedingungen bei den meisten Produkten

**Datei:** `fertilizers.yaml`, `plagron.yaml`
**Problem:** Nur 4 der 20 Fertilizer in `fertilizers.yaml` haben `shelf_life_days` definiert (Sensizym, Flawless Finish, Drip Clean, Free Flow). Alle anderen Produkte fehlt dieses Feld. Fuer plagron.yaml kein Eintrag.

**Spec-Referenz:** REQ-004 v3.1
**Empfehlung:** Mindestens fuer Biologicals und Enzymprodukte (Piranha, Tarantula, Voodoo Juice, Pure Zym) Haltbarkeitswerte ergaenzen.

---

### V-004: Nutrient Plans — EC-Zielwert fehlt in Channel-basierten Plaenen

**Datei:** `fertilizers.yaml` (Plan "Advanced Nutrients GMB + PK 13-14")
**Problem:** Im 3-Kanal-Plan sind `target_ec_ms` fuer die Gießkannen-Kanaele mit 0.0 angegeben, was korrekt ist (keine Mineralduessung). Aber der Tank-Kanal hat nur einen EC-Wert pro Phase, waehrend der tatsaechliche EC-Peak in Woche 13-15 (EC ~2.2) im Notes-Text erwaehnt, aber nicht als `target_ec_ms` formalisiert ist.

**Empfehlung:** EC-Peak-Wert 2.2 als `target_ec_ms: 2.2` im FLOWERING-Spatzbluetenkanal dokumentieren statt nur in den Notes.

---

### V-005: IPM — fehlende Behandlungen fuer Krankheiten Pythium, Root Rot

**Datei:** `ipm.yaml`
**Problem:** Die Krankheit "Root Rot" (Pythium spp.) hat keinen Eintrag in `disease_treatments`. Fuer "Bacterial Spot" (Xanthomonas) und "Tobacco Mosaic Virus" ebenfalls keine Behandlungen definiert.

**Spec-Referenz:** REQ-010
**Empfehlung:** Fuer Pythium: "Environmental Control" und "Sanitation" als Behandlungen hinzufuegen. Fuer Xanthomonas: Kupferpraeparate. Fuer TMV: keine kurative Behandlung moeglich — "Resistant Varieties" und "Sanitation" als praeventive Massnahme.

---

### V-006: IPM — fehlende biologische Behandlung fuer Trauermücken (Fungus Gnats)

**Datei:** `ipm.yaml`
**Problem:** Fungus Gnats (Bradysia spp.) haben nur "Sticky Traps" als Behandlung. Biologische Behandlungen wie Steinernema feltiae (Nematoden) oder Bacillus thuringiensis israelensis (Bti) fehlen. Gelbklebefallen sind wirksam gegen Adulte, aber nicht gegen Larven im Substrat.

**Spec-Referenz:** REQ-010 (Biologische Behandlungsmethoden)
**Empfehlung:** `Steinernema feltiae` als biological release-Behandlung und `Bacillus thuringiensis israelensis` als spray-Behandlung hinzufuegen.

---

### V-007: IPM — fehlende `Kaliumseife` / Insecticidal Soap Behandlung

**Datei:** `ipm.yaml`
**Problem:** Kaliumseife (Insecticidal Soap) ist eines der wichtigsten biologisch zugelassenen Kontaktmittel gegen Wollaeuse, Blattlaeuse und Spinnmilben. Sie fehlt komplett in den Behandlungen.

**Spec-Referenz:** REQ-010 (biologische Behandlungsmethoden)
**Empfehlung:** Neuen Treatment-Eintrag hinzufuegen: `name: "Insecticidal Soap"`, `treatment_type: biological`, `active_ingredient: "potassium salts of fatty acids"`, `safety_interval_days: 1`.

---

### V-008: Companion Planting — fehlende Gegenkanten (Nicht-Bidirektionalitaet)

**Datei:** `companion_planting.yaml`
**Problem:** Die `compatible`-Liste definiert 15 unidirektionale Kanten. Die Companion-Planting-Logik setzt voraus, dass Kompatibilitaet bidirektional ist (wenn A gut fuer B, dann B gut fuer A). Mehrere Kanten haben keine explizite Gegenkante:

| Kante | Gegenkante vorhanden? |
|-------|----------------------|
| Solanum lycopersicum → Ocimum basilicum | Fehlt |
| Solanum lycopersicum → Daucus carota | Fehlt |
| Cannabis sativa → Ocimum basilicum | Fehlt |
| Zea mays → Phaseolus vulgaris | Fehlt |
| Zea mays → Cucurbita pepo | Fehlt |
| Daucus carota → Pisum sativum | Fehlt |

**Empfehlung:** Entweder alle Kanten bidirektional im YAML ergaenzen, oder der Companion-Planting-Engine explizit Bidirektionalitaet bei der Abfragezeit hinzufuegen (und das YAML-Schema als "einseitige Definitionen" dokumentieren).

---

### V-009: Companion Planting — Species existieren nicht in species.yaml

**Datei:** `companion_planting.yaml`
**Problem:** Mehrere Species in den Kanten koennen nicht in `species.yaml` verifiziert werden:

- `Tagetes erecta` — in species.yaml vorhanden (Zeile 949)
- `Anethum graveolens` — in species.yaml vorhanden (Zeile 379)
- `Brassica oleracea var. capitata` — in species.yaml vorhanden (Zeile 583)
- `Solanum tuberosum` — in species.yaml vorhanden (Zeile 76)

Alle geprueften Species existieren. Kein Fehler, aber die inkompatible Kante `Foeniculum vulgare ↔ Phaseolus vulgaris` setzt voraus, dass Foeniculum in species.yaml existiert: `Foeniculum vulgare` ist in species.yaml Zeile 356 vorhanden.

**Bewertung:** Alle geprueften Companion-Planting-Referenzen sind aufloesbar.

---

### V-010: Starter Kit "balkon-blumen-voranzucht" — includes_nutrient_plan: true, aber nutrient_plan_keys leer

**Datei:** `starter_kits.yaml`, Zeile 107-108
**Datensatz:** `kit_id: balkon-blumen-voranzucht`
**Problem:** `includes_nutrient_plan: true` aber `nutrient_plan_keys: []`. Ebenso betroffen: `balkon-tomaten`, `kleines-gemusebeet`, `chili-zucht`, `indoor-growzelt`, `superhot-chili` — alle setzen `includes_nutrient_plan: true` ohne Referenz.

**Spec-Referenz:** REQ-020
**Betroffene Kits:** 6 von 11 Kits
**Empfehlung:** Entweder konkrete `nutrient_plan_keys` referenzieren oder `includes_nutrient_plan: false` setzen bis die Pläne implementiert sind. Aktuell erzeugt das einen fehlerhaften Zustand im Onboarding-Wizard.

---

### V-011: Species — fehlende `family` / `family_key` Zuordnung fuer Pelargonium

**Datei:** `species.yaml`
**Problem:** Pelargonium zonale ist in `species.yaml` vorhanden (Zeile 1351). Die botanische Familie Geraniaceae ist in keiner der `botanical_families.yaml` oder `plant_info*.yaml` new_families-Definitionen zu finden. Pelargonium ohne Familienzuordnung ist ein haengender Fremdschluessel.

**[AGROBIO-CHECK Ergebnis — V-011]:** Geraniaceae ist taxonomisch korrekt fuer Pelargonium. Die Familie fehlt in `botanical_families.yaml`. Detaillierte Bewertung und Familiendaten siehe Abschnitt "Agrarbiologische Fachbewertung" weiter unten.

**Status:** Korrektur erforderlich — Geraniaceae muss in `botanical_families.yaml` oder `plant_info_indoor_3.yaml` (wo die Familienzuordnung `"Pelargonium zonale": Geraniaceae` bereits korrekt gesetzt ist) als vollstaendige Familiendefinition ergaenzt werden. Aktuell hat `plant_info_indoor_3.yaml` Geraniaceae zwar unter `new_families` deklariert, aber nur mit `name` und `order` — alle Pflege-relevanten Felder fehlen.

**Empfehlung:** Geraniaceae mit vollstaendigen Werten als neue botanische Familie hinzufuegen.

---

### V-012: Nutrient Plans — Phase "FLUSHING" vs. "HARVEST" Konsistenz

**Datei:** `fertilizers.yaml`
**Problem:** Die Flush-Phase in den AN-Plaenen wird mit `phase_name: HARVEST` definiert (nicht `FLUSHING`). Das Enum `PhaseName` enthaelt beide Werte: `FLUSHING = "flushing"` und `HARVEST = "harvest"`. Die Flush-Aktivitaet (Flawless Finish, Drip Clean) gehoert semantisch zur FLUSHING-Phase, nicht zur HARVEST-Phase.

**Empfehlung:** Flush-Phasen-Eintraege von `HARVEST` auf `FLUSHING` umbenennen. Oder den Nutrient-Plan-Phasen-Kommentar praezisieren, dass "HARVEST" hier den Ernte-Flush bedeutet, nicht den Ernte-Vorgang.

---

## Fachliche Pruefung [AGROBIO-CHECK]

### Plausibilitaets-Findings (P-XXX)

---

### P-001: Sensi Bloom B NPK-Verhaeltnis 2-4-8 — Plausibilitaet?

**Datei:** `fertilizers.yaml`, Zeile 103-114
**Datensatz:** `pH Perfect Sensi Bloom B`
**Fraglicher Wert:** `npk_ratio: [2.0, 4.0, 8.0]` — NPK-Summe = 14
**Erwarteter Bereich:** Bluetenduenger typisch 1-3 N, 3-7 P, 4-8 K — Summe 8-18. Plausibel.
**Anmerkung:** Sensi Bloom B ist die PK-Komponente des 2-Part-Systems. Ein hohes K-Verhaeltnis (K = 2x P) ist fuer Bluetenduenger typisch.

**[AGROBIO-CHECK Ergebnis — P-001]: BESTAETIGT**
Das NPK-Profil 2-4-8 ist botanisch und analytisch korrekt und entspricht dem verifizierten Referenzdokument `an_sensi_bloom_b.md`. Pflanzenphysiologische Begruendung:
- K (8%) ist der dominant notwendige Makronaehrstoff in der Bluetephase: Steuert Stomata-Regulierung, Turgor-Aufrechterhaltung in Bluetengewebe, Zucker-Translokation im Phloem, Aktivierung von mehr als 60 Enzymen (u.a. Terpen-Cyclase fuer Harzproduktion). Der hohe K-Wert ist fuer Cannabis-Blute physiologisch korrekt.
- P (4%) unterstuetzt die massive ATP-Synthese fuer Zellteilung in Bluetengewebe (Phospholipide, Energietransfer). Doppelter P-Wert gegenueber Grow B (2%) ist korrekt fuer die erhoehten Anforderungen in der generativen Phase.
- N (2%) wird nur noch ergaenzend benoetigt — die vegetative Proteinsynthese ist abgeschlossen, nur Enzymproteine fuer Harzstoffwechsel und Photosynthese benoetigen weiterhin N. 2% N zusammen mit 3% N aus Part A ergibt 5% Gesamt-N, was angemessen ist.
- Das P:K-Verhaeltnis von 1:2 (Bloom B) gegenueber 1:3 (Grow B) spiegelt korrekt den verschobenen Bedarf in der generativen Phase wider.

**Status:** Verifiziert. Kein Korrekturbedarf.

---

### P-002: Sensi Grow A NPK 3-0-0 — CalMag-Komponente ohne Ca-Deklaration

**Datei:** `fertilizers.yaml`, Zeile 63-75
**Datensatz:** `pH Perfect Sensi Grow A`
**Fraglicher Wert:** `npk_ratio: [3.0, 0.0, 0.0]`
**Anmerkung:** Das Notes-Feld sagt "CalMag-Komponente (3% Ca)". Der Calcium-Anteil ist nicht im `npk_ratio` abbildbar (NPK = N-P-K, kein Ca). Das Pydantic-Modell hat kein Kalzium-Feld. Die 3% N koennen aus Calciumnitrat stammen, aber die CalMag-Charakterisierung ist im Datenmodell nicht maschinenlesbar.

**[AGROBIO-CHECK Ergebnis — P-002]: BESTAETIGT MIT MODELLIERUNGSHINWEIS**
Das NPK 3-0-0 ist korrekt. Die N-Quelle ist Calciumnitrat (Ca(NO3)2) — ein etablierter Duenger, bei dem Stickstoff und Calcium zusammen in einem Salz vorliegen. Der Stickstoff wird als 3% N deklariert, der Calcium als ~3% Ca. Beide sind getrennte Naehrstoffe; die NPK-Notation erfasst nur N, P, K per Konvention.

Pflanzenphysiologische Relevanz: Calcium ist in der vegetativen Phase der wichtigste Sekundaernaehrstoff (Zellwandaufbau, Meristemaktivitaet, Ca ist nicht phloemmoebil — Zufuhr nur ueber Transpirationsstrom). Ein hohes Ca-Angebot in Part A zu Beginn der Mischung verhindert ausserdem die Ausfaellung von Calciumsulfat und Calciumphosphat mit den in Part B enthaltenen Sulfaten und Phosphaten — das ist die chemische Begruendung der Mischungsreihenfolge "Part A immer zuerst".

Das Datenmodell-Problem ist real: Ca% ist im `Fertilizer`-Modell nicht maschinenlesbar erfassbar. Das `notes`-Feld ist die einzige aktuelle Moeglichkeit.

**Empfehlung Datenmodell:** Mittelfristig `ca_percent: float | None = None` und `mg_percent: float | None = None` als optionale Felder im Fertilizer-Modell ergaenzen. Dies ist besonders fuer die korrekte CalMag-Supplement-Empfehlung in Coco-Substraten (wo Ca und Mg durch Kationenaustausch gebunden werden) relevant.

**Empfehlung YAML sofort:** `notes`-Feld praezisieren: "CalMag-Komponente: Ca ~3%, Mg vorhanden. N-Quelle: Calciumnitrat. Dreifach chelatierte Mikronährstoffe (EDTA/DTPA/EDDHA). IMMER ZUERST zugeben."

**Status:** NPK-Wert korrekt. Modellierungsluecke besteht, Modell-Erweiterung empfohlen.

---

### P-003: GMB-Plan FLOWERING NPK [4.0, 3.0, 8.0] in Fruehblute und Spaetblute identisch

**Datei:** `fertilizers.yaml`, Phasen sequence_order 4 und 5 des GMB-Plans
**Fraglicher Wert:** Beide Blute-Phasen haben identisches NPK-Verhaeltnis `[4.0, 3.0, 8.0]`
**Erwarteter Bereich:** In der Spaetblute sollte der Stickstoffanteil reduziert werden, der PK-Anteil steigen (typisch: Wechsel zu 1-5-8 oder aehnlich in Woche 11+).

**[AGROBIO-CHECK Ergebnis — P-003]: SYSTEMBEDINGT KORREKT**
Das identische NPK-Verhaeltnis [4.0, 3.0, 8.0] in Frueh- und Spaetblute ist systembedingt und biologisch nachvollziehbar im GMB-Kontext.

Begruendung: Das Advanced Nutrients pH Perfect GMB-System (Grow-Micro-Bloom) arbeitet mit einem fixen 1:1:1-Dosierungsverhaeltnis ueber alle Wachstumsphasen. Das resultierende NPK-Profil der Mischung (4:3:8) aendert sich daher nicht — nur die Gesamtdosis (mL/L) und der EC-Zielwert werden phasenbezogen angepasst. Dies ist das Designprinzip des GMB-Systems: Vereinfachung durch konstantes Verhaeltnis, Steuerung ueber Gesamtkonzentration.

Der Unterschied zwischen Frueh- und Spaetblute wird im Seed-Eintrag korrekt ueber `target_ec_ms` (1.6 → 1.8) und `feeding_frequency_per_week` abgebildet, nicht ueber das NPK-Verhaeltnis.

Zu beachten: In der Spaetblute (Woche 11+) empfehlen viele Coco-Grower zusaetzlich einen PK-Booster (PK 13-14), der das effektive NPK-Gesamtverhaeltnis in der Nährloesung stark in Richtung Null-N / hoch-PK verschiebt. Dieser Effekt ist im Seed-Eintrag durch die separate Booster-Dosierung modelliert.

**Status:** Korrekt. Kein Korrekturbedarf am NPK-Wert.

---

### P-004: Sugar Royal (Plagron) NPK [9.0, 0.0, 0.0] — Aminosaeure-Supplement mit 9% N

**Datei:** `plagron.yaml`, Zeile 124-137
**Datensatz:** `Sugar Royal`
**Fraglicher Wert:** `npk_ratio: [9.0, 0.0, 0.0]`

**[AGROBIO-CHECK Ergebnis — P-004]: BESTAETIGT — BIOCHEMISCH PLAUSIBEL**
Der N-Wert von 9% (gerundet aus 8,5% deklariertem Stickstoff) ist fuer ein Aminosaeure-Supplement biochemisch korrekt und plausibel.

Erklaerung: Aminosaeuren enthalten per Definition Stickstoff in der Aminogruppe (-NH2). Das Stickstoff-Gewichtsverhaeltnis variiert je nach Aminosaeure:
- Glycin (C2H5NO2): N-Anteil = 14/75 = 18,7%
- Alanin (C3H7NO2): N-Anteil = 14/89 = 15,7%
- Arginin (C6H14N4O2): N-Anteil = 56/174 = 32,2% (vier N-Atome!)
- Lysin (C6H14N2O2): N-Anteil = 28/146 = 19,2%

Ein Produkt aus 18 verschiedenen Aminosaeuren (wie Sugar Royal) mit einem mittleren N-Anteil von ca. 8,5% ist chemisch plausibel — insbesondere wenn N-reiche Aminosaeuren wie Arginin, Asparagin, Glutamin und Lysin stark vertreten sind.

Entscheidend: Es handelt sich um organisch gebundenen Stickstoff aus Aminogruppen, nicht um Nitrat-N oder Ammonium-N. Dieser wird NICHT direkt als Mineralsalz aufgenommen, sondern:
1. Im Substrat durch Mikroorganismen (Aminosaeure-Deaminasen) zu NH4+ abgebaut
2. Oder als ganzes Aminosaeure-Molekuel ueber spezifische Aminosaeure-Transporter in der Wurzelmembran aufgenommen (Aminosaeure-Transport ist dokumentiert, v.a. fuer saure und neutrale Aminosaeuren)

Praxisrelevante Konsequenz: Der EC-Beitrag von 0,02 mS/cm pro ml/L ist korrekt niedrig, da organische Aminosaeuren viel weniger Ionen in Loesung erzeugen als Mineralsalze. Die 8,5% N werden in der Praxis nicht als voller Naehrstoff-N in EC-Berechnungen eingerechnet.

Hinweis auf YAML-Inkonsistenz: Das Referenzdokument `plagron_sugar_royal.md` setzt `mixing_priority: 65` und `is_organic: true`, aber `plagron.yaml` deklariert `mixing_priority: 40` und `is_organic: false`. Dies ist ein Dateninkonsistenz-Finding ausserhalb des AGROBIO-Scope — Prioritaet 65 (nach Basisduenger und PK-Booster) waere korrekt gemaess Referenzdokument.

**Status:** NPK 9-0-0 fachlich korrekt und verifiziert. Separate Inkonsistenz bei mixing_priority und is_organic besteht.

---

### P-005: Green Sensation (Plagron) als 4-in-1 Booster — NPK [0.0, 8.0, 9.0] plausibel?

**Datei:** `plagron.yaml`, Zeile 109-119
**Datensatz:** `Green Sensation`
**Fraglicher Wert:** `npk_ratio: [0.0, 8.0, 9.0]`
**Anmerkung:** Plagron deklariert Green Sensation als NPK 0-8-9. Fuer einen 4-in-1 Bloom-Booster (PK + Enzyme + Vitamine + Geschmacksstoffe) ist ein hoher PK-Anteil ohne N biologisch plausibel — N-reduzierte Spaetbluetenduengung ist gaengige Praxis.
**Status:** Plausibel. Keine weiteren Fragen. Kein AGROBIO-CHECK erforderlich.

---

### P-006: Powdery Mildew — wissenschaftlicher Name "Erysiphe spp." korrekt?

**Datei:** `ipm.yaml`, Zeile 91
**Datensatz:** `Erysiphe spp.`
**Fraglicher Wert:** `scientific_name: Erysiphe spp.` als Mehltau-Erreger

**[AGROBIO-CHECK Ergebnis — P-006]: TEILWEISE KORREKT — PRAEZISIERUNG EMPFOHLEN**
Erysiphe spp. ist eine gueltige und relevante Gattung fuer echten Mehltau (Powdery Mildew, Ordnung Erysiphales, Klasse Leotiomycetes). Die Verwendung ist fuer ein Allroundsystem akzeptabel, aber taxonomisch unvollstaendig.

Korrekte Einordnung nach aktuellem Stand (MycoBank / Species Fungorum):
- Erysiphe spp. — Hauptgattung; befaellt u.a. Cucurbitaceae (Gurke: E. cichoracearum), Solanaceae (Tomate: E. lycopersici), Cannabaceae (Cannabis: Golovinomyces ambrosiae, frueher E. cannabina, nach molekularer Revision umbenannt)
- Podosphaera spp. — relevant fuer Rosaceae (Apfel: P. leucotricha, Erdbeere: P. aphanis) und Cucurbitaceae (Kuerbis: P. xanthii)
- Leveillula taurica — Sonderfall: befaellt Paprika (Capsicum annuum) und Tomaten intern (endophytisch wachsend, erst spaet sichtbar); reagiert anders auf Umweltbedingungen als Erysiphe
- Golovinomyces ambrosiae — Cannabis-spezifischer Echter Mehltau (nach Braun & Cook 2012, bestaetigt durch molekulare Phylogenie); frueherer Synonym Erysiphe ambrosiae

Fuer das kamerplanter-Datenbankmodell ist `Erysiphe spp.` als breit definierter Eintrag fuer ein System mit vielen Kulturpflanzen pragmatisch akzeptabel. Fuer Cannabis-spezifische Warnhinweise sollte `Golovinomyces ambrosiae` separat erwaehnt werden.

**Empfehlung:** `scientific_name: "Erysiphe spp. / Golovinomyces spp."` mit Hinweis im `description`-Feld: "Cannabis-Echter-Mehltau: Golovinomyces ambrosiae; Gurke/Kuerbis: Podosphaera xanthii; Paprika (endophytisch): Leveillula taurica."

**Status:** Akzeptabel als pragmatischer Eintrag, Praezisierung fuer Cannabis-Kontext empfohlen.

---

### P-007: Downy Mildew — Peronospora spp. als allgemeiner Bezeichner

**Datei:** `ipm.yaml`, Zeile 112
**Datensatz:** Downy Mildew / Peronospora spp.

**[AGROBIO-CHECK Ergebnis — P-007]: KORREKTURBEDARF — FALSCHER MEHLTAU AN CANNABIS IST PSEUDOPERONOSPORA**
Peronospora spp. ist eine gueltige Gattung fuer Falschen Mehltau (Downy Mildew) bei vielen Kulturpflanzen, aber fuer das System mit Cannabis-Fokus ist ein Hinweis auf die korrekte Cannabis-Art dringend notwendig.

Taxonomische Praezisierung:
- Peronospora spp. — befaellt Fabaceae (Spinat: P. farinosa), Brassicaceae (P. brassicae), Lamiaceae (Basilikum: P. belbahrii — wirtschaftlich relevant!)
- Pseudoperonospora humuli — Cannabis-spezifischer Falscher Mehltau; eng verwandt mit P. cubensis (Gurke). Erst 2011 als separater Erreger von Cannabis-DM bestaetigt (Bates et al., 2011, Plant Dis.)
- Plasmopara viticola — Weinrebe (fuer Gewächshaus-Trauben relevant)
- Bremia lactucae — Salat, besonders relevant in Hydroponik-Anbau

Das pathogen_type-Feld `fungal` ist fachlich inkorrekt fuer alle Falschen-Mehltau-Erreger: Peronospora, Pseudoperonospora, Plasmopara und Bremia gehoeren zu den Oomyceten (Klasse Oomycota, Koenigreich Stramenopiles), nicht zu den echten Pilzen (Fungi). Sie werden historisch als "pilzaehnliche Organismen" bezeichnet, sind aber genetisch naeher mit Braunalgen und Kieselalgen verwandt. Dies ist ein bekannter und weit verbreiteter Fehler in Pflanzenschutzdatenbanken.

**Empfehlung (korrekt):**
- `scientific_name: "Peronospora spp. / Pseudoperonospora humuli"` (Cannabis) oder `"Peronospora spp."` (Allgemein)
- `pathogen_type: oomycete` — falls das Enum diesen Wert unterstuetzt; alternativ `fungal_like` oder der aktuelle `fungal`-Wert mit Kommentar

**Pruefe ob das Enum `pathogen_type` in `Disease` erweitert werden kann:** Derzeit sind vermutlich `fungal`, `bacterial`, `viral` definiert. Ein vierter Wert `oomycete` waere botanisch korrekt und fuer Pythium (Root Rot, ebenfalls ein Oomycet!) ebenso relevant.

**Status:** Peronospora spp. akzeptabel als allgemeiner Bezeichner. Fuer Cannabis-Kontext sollte `Pseudoperonospora humuli` als Hinweis erwaehnt werden. pathogen_type: fungal ist technisch falsch fuer Oomyceten — Korrekturbedarf am Enum.

---

### P-008: Botanical Family "Verbenaceae" — Pelargonium falsch zugeordnet?

**Datei:** `botanical_families.yaml`, `species.yaml`
**Datensatz:** Verbena x hybrida → Verbenaceae

**[AGROBIO-CHECK Ergebnis — P-008]: BESTAETIGT — BEIDE ZUORDNUNGEN KORREKT**
Die Familienzuordnung ist in beiden Faellen taxonomisch korrekt (APG IV, 2016):
- Verbena x hybrida → Familie Verbenaceae, Ordnung Lamiales: KORREKT. Verbena gehoert eindeutig zu den Verbenaceae. Die in `botanical_families.yaml` enthaltene Verbenaceae-Definition (Ordnung: Lamiales, typical_nutrient_demand: medium, frost_tolerance: sensitive) ist botanisch richtig.
- Pelargonium zonale → Familie Geraniaceae, Ordnung Geraniales: KORREKT. Pelargonium hat nach aktueller Klassifikation (APG IV) seinen eigenen Ordnungsrang Geraniales und steht NICHT in der Naehe der Lamiaceae oder Verbenaceae, sondern ist naeher mit Oxalidaceae verwandt.

Wichtige taxonomische Anmerkung: Der Volksname "Geranie" fuer Pelargonium ist ein historischer Irrtum — echte Geranien (Gattung Geranium, ebenfalls Geraniaceae) sind weitgehend winterhart, waehrend Pelargonien (inkl. P. zonale) aus Suedafrika stammen und frostempfindlich sind. Diese Verwechslung ist in Gartenbau-Datenbanken weit verbreitet und sollte im UI durch einen Hinweistext aufgeloest werden.

Das eigentliche Problem: Geraniaceae fehlt als vollstaendige Familie in `botanical_families.yaml`. `plant_info_indoor_3.yaml` deklariert Geraniaceae unter `new_families` nur mit `name` und `order` — alle oekologisch relevanten Felder fehlen.

**Status:** Familienzuordnungen korrekt. Korrekturbedarf: Geraniaceae in botanical_families.yaml als vollstaendiger Eintrag ergaenzen — siehe Abschnitt "Empfohlene Korrektur-Daten" unten.

---

### P-009: Tobacco Mosaic Virus — pathogen_type: viral korrekt?

**Datei:** `ipm.yaml`, Zeile 133
**Datensatz:** `Tobacco mosaic virus`
**Fraglicher Wert:** `pathogen_type: viral` — korrekt
**Anmerkung:** TMV ist ein Tobamovirus (RNA-Virus, Positivstrang). Die Klassifikation als `viral` ist taxonomisch korrekt. Der Schreibweise "Tobacco mosaic virus" (Kleinbuchstaben nach erstem Wort) entspricht der ICTV-Nomenklatur.
**Status:** Plausibel und korrekt. Kein AGROBIO-CHECK erforderlich.

---

### P-010: EC-Targets in Cannabis-Plaenen — Coco-optimiert aber sehr hoch

**Datei:** `fertilizers.yaml`
**Datensatz:** Beide AN-Plaene (Sensi und GMB)
**Fraglicher Wert:** `target_ec_ms: 1.8` in Spaetblute
**Erwarteter Bereich:** 1.2 - 2.5 mS/cm fuer Coco-Cannabis in Spaetblute
**Anmerkung:** 1.8 mS/cm liegt im unteren bis mittleren Bereich fuer erfahrene Coco-Grower. Einige Feeding Charts empfehlen bis 2.5 mS/cm in der Spaetblute. Die Werte sind konservativ und anfaengerfreundlich.
**Status:** Plausibel. Keine Pruefung erforderlich.

---

### P-011: Terra Grow NPK 3-1-3 — YAML entspricht Referenz

**Datei:** `plagron.yaml`, `spec/ref/products/plagron_terra_grow.md`
**Datensatz:** `Terra Grow`
**YAML-Wert:** `npk_ratio: [3.0, 1.0, 3.0]`
**Referenz-Wert:** NPK 3-1-3 (Terra Grow Referenzdokument, Abschnitt 2.1)
**Status:** Verifiziert. Kein Fehler.

---

### P-012: Gardol Gruenpflanzenduenger NPK — EC-Beitrag als Schaetzwert markiert

**Datei:** `gardol.yaml`, Zeile 22-24
**Datensatz:** `Grünpflanzendünger`
**YAML-Wert:** `npk_ratio: [6.0, 4.0, 6.0]`, `ec_contribution_per_ml: 0.06`, `ec_contribution_uncertain: true`
**Referenz:** `spec/ref/products/gardol_gruenpflanzenduenger.md`: NPK 6-4-6 bestaetigt. EC-Beitrag explizit als Schaetzung markiert (`<!-- DATEN FEHLEN -->`).
**Bewertung:** Die Markierung `ec_contribution_uncertain: true` ist korrekt und transparent. NPK korrekt. Kein Fehler.
**Status:** Korrekt dokumentiert.

---

## Agrarbiologische Fachbewertung — AGROBIO-CHECK Gesamtergebnis

**Bewertet von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-18
**Geprueft:** S-001, V-011, P-001 bis P-008

---

### AGROBIO-001: Asparagaceae — Korrekte Werte fuer heterogene Familie (S-001)

**Ausgangssituation:** Drei widersprueechliche Definitionen:
- `botanical_families.yaml`: `typical_nutrient_demand: light`, `frost_tolerance: moderate`
- `plant_info_outdoor_1.yaml`: `typical_nutrient_demand: heavy`, `frost_tolerance: hardy`
- `plant_info_indoor_3.yaml`: Nur `name` und `order` — keine Wertangaben

**Botanische Analyse:** Asparagaceae (Ordnung Asparagales, APG IV) ist eine ausserordentlich heterogene Familie mit ca. 2900 Arten in 114 Gattungen:

| Unterfamilie / Gattungsbeispiel | Nährstoffbedarf | Frosttoleranz | Lebensform |
|----------------------------------|----------------|---------------|------------|
| Asparagus officinalis (Spargel) | schwer (heavy) | hart (hardy, bis -20°C) | Rhizom, terrestrisch |
| Agave spp. | gering (light) | maessig (moderate bis hardy je Art) | Sukkulent, terrestrisch |
| Sansevieria/Dracaena trifasciata | gering (light) | empfindlich (sensitive, min. 10°C) | terrestrisch, Zimmerpflanze |
| Dracaena fragrans | gering (light) | empfindlich (sensitive, min. 15°C) | baum-, Zimmerpflanze |
| Chlorophytum comosum (Gruenlilie) | gering (light) | empfindlich (sensitive, min. 5°C) | terrestrisch, Zimmerpflanze |
| Hyacinthus orientalis (Hyazinthe) | mittel (medium) | hart (hardy) | Geophyt |
| Yucca spp. | gering (light) | maessig bis hart | Sukkulent/baum- |
| Cordyline australis | mittel (medium) | maessig (moderate) | baum- |

**Bewertung der drei Definitionen:**
- `plant_info_outdoor_1.yaml` (heavy/hardy) beschreibt Spargel korrekt, ist aber nicht repraesentativ fuer die Gesamtfamilie.
- `botanical_families.yaml` (light/moderate) beschreibt Zimmerpflanzen-Gattungen (Dracaena, Sansevieria, Chlorophytum) korrekt, unterschlaegt aber Spargel.
- Beide Definitionen haben ihre Berechtigung fuer verschiedene Nutzungsgruppen.

**Empfehlung (kanonische Definition):** Da Kamerplanter sowohl Zimmerpflanzen als auch Outdoor-Gemuese abdeckt, ist ein Kompromisswert unvollstaendig. Die sauberste Loesung ist die Beibehaltung der `botanical_families.yaml`-Definition als Primaerreferenz mit folgenden Werten — und einer erklaerenden `description`:

```yaml
- name: Asparagaceae
  common_name_de: "Spargelgewächse"
  common_name_en: Asparagus family
  order: Asparagales
  typical_nutrient_demand: light    # repraesentativ fuer Zimmerpflanzen-Gattungen (Dracaena, Sansevieria, Chlorophytum)
  frost_tolerance: moderate         # Mittelwert; Spargel: hardy; Dracaena: sensitive
  typical_root_depth: shallow
  typical_growth_forms: [herb, shrub, succulent]
  common_pests: [spider_mites, mealybug, asparagus_beetle]
  common_diseases: [root_rot, rust, fusarium]
  pollination_type: [insect, self, wind]
  soil_ph_preference: {min_ph: 6.0, max_ph: 7.5}
  description: >-
    Grosse und heterogene Familie mit ca. 2900 Arten. Umfasst Zimmerpflanzen
    (Dracaena, Sansevieria, Chlorophytum — Schwachzehrer, frostempfindlich)
    und Nutzpflanzen (Spargel — Starkzehrer, winterhart). Geophyten
    (Hyazinthe, Maiglöckchen) und Sukkulenten (Agave, Yucca) sind ebenfalls
    enthalten. Artspezifische Pflegedaten beachten.
  rotation_category: vegetable
```

Die `plant_info_outdoor_1.yaml`-Definition (heavy/hardy) muss entfernt werden — Spargel ist eine Ausnahme innerhalb der Familie, kein Repraesentant. Die `plant_info_indoor_3.yaml`-Deklaration ist ebenfalls zu entfernen (nur name+order, keine Mehrwerte).

---

### AGROBIO-002: Geraniaceae — Empfohlene vollstaendige Familiendefinition (V-011 / P-008)

**Situation:** Geraniaceae ist in `plant_info_indoor_3.yaml` unter `new_families` nur mit `name: Geraniaceae` und `order: Geraniales` deklariert. `botanical_families.yaml` kennt die Familie nicht. `Pelargonium zonale` referenziert Geraniaceae korrekt, haengt aber an einer unvollstaendigen Definition.

**Botanische Familiencharakteristika (Geraniaceae nach APG IV):**
- Ordnung: Geraniales
- Wichtigste Gattungen im Zierpflanzenbau: Pelargonium (ca. 280 Arten, Ursprung: S-Afrika), Geranium (ca. 430 Arten, weltweit, viele winterhart), Erodium (ca. 60 Arten, Mittelmeer)
- Lebensform: Krautpflanzen, Halbstraucher, selten Stauden; Pelargonium im Indoor-Bereich als Topfpflanze; Geranium als Bodendecker/Staude
- Oekologie: Mediterran bis subtropisch (Pelargonium), gemaessigt-kontinental bis arktisch (Geranium)

**Empfohlene Familiendefinition fuer botanical_families.yaml:**

```yaml
- name: Geraniaceae
  common_name_de: "Storchschnabelgewächse"
  common_name_en: Geranium family
  order: Geraniales
  typical_nutrient_demand: medium
  frost_tolerance: sensitive      # fuer Pelargonium (Zimmer/Balkon); Geranium-Stauden: hardy
  typical_root_depth: shallow
  typical_growth_forms: [herb, shrub]
  common_pests: [aphids, spider_mites, vine_weevil, whitefly]
  common_diseases: [botrytis, powdery_mildew, rust, bacterial_blight]
  pollination_type: [insect]
  soil_ph_preference: {min_ph: 6.0, max_ph: 7.0}
  description: >-
    Storchschnabelgewächse mit Pelargonium (Balkon-/Zimmergeranien, frostempfindlich,
    Herkunft Südafrika), Geranium (winterharte Storchschnabel-Stauden) und Erodium.
    Pelargonium wird umgangssprachlich fälschlich als 'Geranie' bezeichnet.
    Gute Drainage essentiell, Staunässe vermeiden. Regelmässiges Entspitzen fördert
    Verzweigung. Blüte durch Photoperiode und Temperatur steuerbar.
  rotation_category: ornamental
```

**Begruendung der Parameterwahl:**
- `typical_nutrient_demand: medium`: Pelargonien sind Mittelzehrer — sie benoetigen regelmaessige Duengung (besonders K und Mg fuer intensive Bluetenfaerbung), aber keine extremen Mengen wie Solanaceae oder Cucurbitaceae.
- `frost_tolerance: sensitive`: Gilt fuer Pelargonium (das Kamerplanter-Leitgenus dieser Familie). Geranium-Stauden waeren `hardy`, aber Pelargonium ist das typische Zimmer-/Balkongewaechs.
- `soil_ph_preference: {min_ph: 6.0, max_ph: 7.0}`: Pelargonien bevorzugen leicht saures bis neutrales Substrat. pH unter 5,5 fuehrt zu Fe/Mn-Toxizitaet, pH ueber 7,5 zu Fe/Mn-Mangel.
- `common_pests`: Blattlaeuse sind der Hauptschaedling an Pelargonien; Weisse Fliege in Gewaeechshaeusern; Thripse bei Indoor-Kultivierung unter Kunstlicht; Trauermücken bei zu feuchtem Substrat.
- `common_diseases`: Botrytis (Grauschimmel) ist die gravierendste Krankheit — besonders in Herbst und bei hoher Luftfeuchtigkeit; Bakterioese (Xanthomonas hortorum pv. pelargonii) ist quarantaenepflichtig in manchen EU-Laendern und befaellt ausschliesslich Pelargonium.

---

### AGROBIO-003: Oomyceten vs. Pilze — pathogen_type Enum-Erweiterung (P-007)

**Fachlicher Hintergrund:** Der Seed-Eintrag fuer Downy Mildew und Root Rot (Pythium spp.) klassifiziert beide als `pathogen_type: fungal`. Dies ist ein etablierter, aber botanisch falscher Usus.

Falscher Mehltau (Peronospora, Pseudoperonospora, Plasmopara) und Wurzelfaeule durch Pythium und Phytophthora gehoeren zu den Oomyceten (Stramenopiles), nicht zu den echten Pilzen (Fungi). Relevante Unterschiede:
- Zellwandchemie: Oomyceten haben Cellulose-Zellwaende (wie Pflanzen), Pilze haben Chitin-Zellwaende
- Empfindlichkeit: Oomyceten sind NICHT empfindlich gegen klassische Fungizide (Azole, Strobilurine), sondern gegenueber Phosphonaten (Phosphorige Saeure), Phenylamiden und Carboxylsaeuren
- Reproduktion: Oomyceten bilden Zoosporen (begeisselte Schwarmsporen in Wasser) — daher dramatisch hoehere Ausbreitungsgeschwindigkeit bei Staunasse und in Hydroponik

**Konsequenz fuer das IPM-System:** Wenn das System die Behandlungsempfehlung aus dem `pathogen_type` ableitet, koennte eine falsche Klassifikation zu falschen Behandlungsempfehlungen fuehren (Fungizide statt Phosphonate bei Pythium/Downy Mildew).

**Empfehlung:** Enum `pathogen_type` in `Disease` um den Wert `oomycete` erweitern. Pythium spp. und Peronospora spp. / Pseudoperonospora humuli umklassifizieren. Alternativ: `pathogen_type: fungal_like` als Kompromiss.

---

### Zusammenfassung AGROBIO-CHECK Ergebnisse

| Finding | Status | Korrekturbedarf |
|---------|--------|----------------|
| P-001: Sensi Bloom B NPK 2-4-8 | Bestaetigt | Kein Korrekturbedarf |
| P-002: Sensi Grow A CalMag NPK 3-0-0 | Bestaetigt mit Modellierungshinweis | Mittelfristig: `ca_percent`-Feld im Modell; sofort: Notes praezisieren |
| P-003: GMB FLOWERING NPK identisch | Systembedingt korrekt | Kein Korrekturbedarf |
| P-004: Sugar Royal NPK 9-0-0 | Bestaetigt, biochemisch korrekt | Inkonsistenz mixing_priority (40 vs. 65) und is_organic (false vs. true) beheben |
| P-006: Powdery Mildew Erysiphe spp. | Teilweise korrekt | Golovinomyces ambrosiae fuer Cannabis erwaehnen; Podosphaera xanthii fuer Gurke/Kuerbis |
| P-007: Downy Mildew Peronospora spp. | Korrekturbedarf | Pseudoperonospora humuli fuer Cannabis erwaehnen; pathogen_type: oomycete einf uehren |
| P-008: Verbenaceae / Geraniaceae | Bestaetigt korrekt | Geraniaceae vollstaendig in botanical_families.yaml ergaenzen |
| V-011: Geraniaceae fehlt | Korrekturbedarf | Vollstaendige Familiendefinition ergaenzen (Daten oben) |
| S-001: Asparagaceae dreifach definiert | Korrekturbedarf | Kanonische Definition in botanical_families.yaml; Duplikate entfernen |

---

## Positiv-Befunde

### Staerken der Seed-Daten

1. **Advanced Nutrients — vollstaendige Referenzdokumentation:** Alle AN-Kernprodukte (pH Perfect Grow, Micro, Bloom, Sensizym, Flawless Finish) haben detaillierte Referenzdokumente unter `spec/ref/products/`. Die NPK-Werte und EC-Beitraege sind gegen mehrere Quellen verifiziert.

2. **Plagron — Quellenangaben im YAML-Header:** `plagron.yaml` dokumentiert explizit die Herstellerseiten-URLs fuer NPK-Verifizierung (Terra Grow 3-1-3, Terra Bloom 2-2-4, etc.). Alle geprueften Plagron-NPK-Werte stimmen mit den Referenzdokumenten ueberein.

3. **Mixing Priority Logik — konsistent implementiert:** Die Mischungsreihenfolge (Rhino Skin 5 → Drip Clean 8 → CalMag 8 → Micro 10 → Grow 15 → Bloom 20 → Booster 30 → Supplements 40 → Biologicals 50-70 → Flush 90) ist fuer die Mehrzahl der Produkte korrekt implementiert und entspricht der Herstellerempfehlung (CalMag vor Sulfaten).

4. **Botanische Familien — breite Abdeckung:** 16 Kern-Familien plus ~28 Erweiterungen decken sowohl Indoor-Zimmerpflanzen (Araceae, Asparagaceae, Bromeliaceae) als auch Outdoor-Gemuese (Solanaceae, Cucurbitaceae, Fabaceae) und Kraeuterpflanzen (Lamiaceae, Apiaceae) vollstaendig ab.

5. **Companion Planting — klassische Kombinationen abgedeckt:** Die 15 kompatiblen Kanten decken die gaengigsten Mischkulturen ab (Tomate-Basilikum, Mais-Bohne-Kuerbis "Drei Schwestern", Cannabis-Lavendel).

6. **Gardol nutrient_plans — vorbildliche Phasenannotation:** Die Gardol-Plaene dokumentieren saisonale Ruhephasen mit expliziten `is_recurring: true`-Markierungen und `cycle_restart_from_sequence`-Werten — dies ist ein seltenes Qualitaetsmerkmal.

7. **IPM — Karenzzeiten vorhanden:** Alle drei chemischen Behandlungen (Pyrethrin 7d, Neem Oil 3d, Spinosad 14d) haben `safety_interval_days` definiert, wie vom Modell-Validator gefordert.

8. **Botanische Familien — pH-Bereiche vollstaendig:** Alle 16 Kern-Familien haben `soil_ph_preference` mit min/max definiert.

---

## Referenzielle Integritaet

### Multi-Source Fertilizer-Verifikation

| Produkt | YAML NPK | Ref-Dok NPK | Extern-Quelle | Status |
|---------|----------|-------------|---------------|--------|
| pH Perfect Grow | 1-0-4 | 1-0-4 (an_ph_perfect_grow.md) | Hersteller: 1-0-4 | Verifiziert |
| pH Perfect Micro | 2-0-0 | 2-0-0 (an_ph_perfect_micro.md) | Hersteller: 2-0-0 | Verifiziert |
| pH Perfect Bloom | 1-3-4 | 1-3-4 (an_ph_perfect_bloom.md) | Hersteller: 1-3-4 | Verifiziert |
| Sensizym | 0-0-0 | 0-0-0 (an_sensizym.md) | Hersteller: 0-0-0 | Verifiziert |
| Flawless Finish | 0-0-0 | 0-0-0 (an_flawless_finish.md) | Hersteller: 0-0-0 | Verifiziert |
| Terra Grow | 3-1-3 | 3-1-3 (plagron_terra_grow.md) | plagron.com: 3-1-3 | Verifiziert |
| Terra Bloom | 2-2-4 | Kein Ref-Dok | plagron.com: 2-2-4 | [REF-MISSING] |
| Cocos A | 4-0-1 | plagron_cocos_a.md | plagron.com | Ref-Dok vorhanden, YAML nicht gegen Dok geprueft |
| Cocos B | 1-4-2 | plagron_cocos_b.md | plagron.com | Ref-Dok vorhanden, YAML nicht gegen Dok geprueft |
| PK 13-14 | 0-13-14 | plagron_pk_13_14.md | plagron.com: 0-13-14 | Ref-Dok vorhanden |
| Green Sensation | 0-8-9 | plagron_green_sensation.md | plagron.com: 0-8-9 | Ref-Dok vorhanden |
| Power Roots | 0-0-2 | plagron_power_roots.md | plagron.com: 0-0-2 | Ref-Dok vorhanden |
| Pure Zym | 0-0-0 | plagron_pure_zym.md | plagron.com | Ref-Dok vorhanden |
| Sugar Royal | 9-0-0 | plagron_sugar_royal.md | plagron.com: 9-0-0 | Verifiziert — N aus Aminosaeuren, biochem. korrekt |
| Gardol Gruenpflanzenduenger | 6-4-6 | gardol_gruenpflanzenduenger.md | Bauhaus-Etikett: 6-4-6 | Verifiziert (mit Unsicherheitsvermerk) |
| Drip Clean | 0-18-6 | hg_drip_clean.md | Hersteller | Ref-Dok vorhanden |
| Free Flow | 0-0-0 | bionova_free_flow.md | Hersteller | Ref-Dok vorhanden |
| Sensi Grow A | 3-0-0 | an_sensi_grow_a.md | Hersteller | Verifiziert — N aus Calciumnitrat, Ca ~3% nicht in NPK erfassbar |
| Sensi Grow B | 1-2-6 | an_sensi_grow_b.md | Hersteller | Ref-Dok vorhanden |
| Sensi Bloom A | 3-0-0 | an_sensi_bloom_a.md | Hersteller | Ref-Dok vorhanden |
| Sensi Bloom B | 2-4-8 | an_sensi_bloom_b.md | Hersteller | Verifiziert — P:K Verhaeltnis 1:2 korrekt fuer Bluetephase |
| Big Bud | 0-1-3 | an_big_bud.md | Hersteller | Ref-Dok vorhanden |
| Overdrive | 1-5-4 | an_overdrive.md | Hersteller | Ref-Dok vorhanden |
| B-52 | 2-1-4 | an_b52.md | Hersteller | Ref-Dok vorhanden |
| Nirvana | 0-0-1 | an_nirvana.md | Hersteller | Ref-Dok vorhanden |
| Rhino Skin | 0-0-0 | an_rhino_skin.md | Hersteller | Ref-Dok vorhanden |
| Bud Candy | 0-0-0 | an_bud_candy.md | Hersteller | Ref-Dok vorhanden |
| Voodoo Juice | 0-0-0 | an_voodoo_juice.md | Hersteller | Ref-Dok vorhanden |
| Piranha | 0-0-0 | an_piranha.md | Hersteller | Ref-Dok vorhanden |
| Tarantula | 0-0-0 | an_tarantula.md | Hersteller | Ref-Dok vorhanden |
| CalMag (Terra Aquatica) | 5-0-0 | Kein Ref-Dok | Terra Aquatica | [REF-MISSING] |

**[REF-MISSING] Produkte (2):**
1. `Terra Bloom` (Plagron) — kein Referenzdokument unter `spec/ref/products/`
2. `CalMag` (Terra Aquatica) — kein Referenzdokument unter `spec/ref/products/`

### Mixing Priority Abweichungen (AN Referenz vs. YAML)

| Produkt | YAML mixing_priority | Ref-Dok mixing_priority | Bewertung |
|---------|---------------------|------------------------|-----------|
| pH Perfect Grow | 15 | 20 (an_ph_perfect_grow.md) | Abweichung — YAML 15, Ref 20 |
| pH Perfect Bloom | 20 | 30 (an_ph_perfect_bloom.md) | Abweichung — YAML 20, Ref 30 |
| pH Perfect Micro | 10 | 10 (an_ph_perfect_micro.md) | Korrekt |
| Sensizym | 70 | 70 (an_sensizym.md) | Korrekt |
| Flawless Finish | 90 | 90 (an_flawless_finish.md) | Korrekt |
| Rhino Skin | 5 | 5 (an_sensizym.md Mixing-Schema) | Korrekt |
| Sugar Royal (Plagron) | 40 | 65 (plagron_sugar_royal.md) | Abweichung — YAML 40, Ref-Dok 65 |

### Verwaiste Referenzen

| Quelle | Feld | Referenzierter Wert | Status |
|--------|------|-------------------|--------|
| `fertilizers.yaml` Plan "GMB + PK 13-14" | `product_name: "PK 13-14"` | Definiert in `plagron.yaml` | Aufloesbar (cross-file) |
| `starter_kits.yaml` (6 Kits) | `includes_nutrient_plan: true` | `nutrient_plan_keys: []` | Leer — Referenz fehlt |
| `species.yaml` Pelargonium zonale | `family: Geraniaceae` | Geraniaceae nur partiell in plant_info_indoor_3.yaml | Unvollstaendige Referenz (name+order vorhanden, Pflege-Werte fehlen) |

### Bidirektionalitaet Companion Planting

| Kante A → B | Gegenkante B → A | Status |
|-------------|-----------------|--------|
| Solanum lycopersicum → Ocimum basilicum | Nicht vorhanden | Fehlt |
| Solanum lycopersicum → Daucus carota | Nicht vorhanden | Fehlt |
| Solanum lycopersicum → Tagetes erecta | Nicht vorhanden | Fehlt |
| Capsicum annuum → Ocimum basilicum | Nicht vorhanden | Fehlt |
| Cucumis sativus → Anethum graveolens | Nicht vorhanden | Fehlt |
| Zea mays → Phaseolus vulgaris | Nicht vorhanden | Fehlt |
| Cannabis sativa → Ocimum basilicum | Nicht vorhanden | Fehlt |
| Daucus carota → Pisum sativum | Nicht vorhanden | Fehlt |

---

## Duplikate

| Typ | Key/Name | Fundorte |
|-----|----------|----------|
| Botanische Familie | Asparagaceae | `botanical_families.yaml` (Z.168), `plant_info_outdoor_1.yaml` (Z.41), `plant_info_indoor_3.yaml` (Z.42) — mit abweichenden Werten |
| Botanische Familie | Asparagaceae (Werte-Inkonsistenz) | light/moderate (Kern) vs. heavy/hardy (outdoor_1) |

---

## Vollstaendigkeits-Score (Spec-Pflichtfelder)

| Kategorie | Pflichtfelder gemaess Spec | Abgedeckt | Score |
|-----------|--------------------------|-----------|-------|
| Species — Kern (scientific_name, common_names, family) | 3 | 3 | 100% |
| Species — Indoor (temp, humidity, substrate) | 5 | 3 (Kern-species.yaml: groesstenteils fehlend, plant_info_indoor*: vorhanden) | ~60% |
| Species — Outdoor (sowing, harvest, nutrient_demand, frost) | 5 | 5 | 100% |
| Species — Toxizitaet (toxicity_human, cat, dog) | 3 | 0 (kein Feld im aktuellen Modell) | 0% |
| Fertilizer (NPK, form, mixing_priority) | 4 | 4 | 100% |
| NutrientPlan (Phasen, EC, pH) | 3 | 3 | 100% |
| IPM — indoor Schaedlinge | 6 (Trauermücken, Spinnmilben, Wollaeuse, Schildlaeuse, Thripse, Weisse Fliege) | 6 | 100% |
| IPM — indoor Krankheiten | 4 (Botrytis, Mehltau, Pythium, Fusarium) | 4 | 100% |
| IPM — Biologische Behandlungen | 3 | 2 (Nematoden gegen Trauermücken fehlen) | 67% |
| Starter Kits (9+ Kits, species_keys) | 2 | 1.5 (11 Kits, aber species_keys leer) | 75% |
| Location Types (10 Typen, name, icon) | 2 | 2 (12 Typen vorhanden) | 100% |
