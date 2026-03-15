# Agrarbiologisches Review: Pflanzen-Informationsdokumente Batch 1
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-05
**Fokus:** Verifizierung der Korrekturen K-001 bis K-003, M-001 bis M-009 sowie Neufehler-Screening
**Analysierte Dokumente:**
1. `spec/ref/plant-info/dahlia_hapet_daydream.md`
2. `spec/ref/plant-info/dahlia_pinnata_great_silence.md`
3. `spec/ref/plant-info/dahlia_x_hybrida_lavender_perfection.md`
4. `spec/ref/plant-info/dahlia_x_hybrida_armateras.md`
5. `spec/ref/plant-info/dahlia_embassy.md`
6. `spec/ref/plant-info/tigridia_pavonia.md`
7. `spec/ref/plant-info/petunia_x_hybrida.md`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Kernfehler behoben; 3 neue Fehler identifiziert |
| Dahlia-Konsistenz | 3/5 | Great Silence hat Inkonsistenz im Fruchtfolge-Abschnitt (medium_feeder vs. heavy_feeder) |
| Tigridia-Korrektheit | 5/5 | K-003 korrekt umgesetzt; biologisch akkurat |
| Petunia-Vollstaendigkeit | 4/5 | M-008/M-009 korrekt; leichte VPD-Abweichung in Bluetephase |
| CSV-Import-Eignung | 4/5 | Embassy-CSV hat fehlende Pflichtfelder; Great Silence CSV hat Randbereich-Problem |
| Dokumenten-Konsistenz | 3/5 | Great Silence: Widerspruch Stammdaten (heavy_feeder) vs. Fruchtfolge (medium_feeder) |

Die Korrekturen K-001, K-003, M-002, M-004 (teilweise), M-006, M-008 und M-009 wurden korrekt umgesetzt. Zwei verbleibende Probleme erfordern Nachkorrektur: der Widerspruch im Great Silence Fruchtfolge-Abschnitt (M-004 nur halb geloest) und ein neuer Fehler im Embassy-Dokument bezueglich des CSV-Formats. Ausserdem wird eine biologisch begruendete Praezisierung des VPD-Bereichs in der Petunia-Bluetephase empfohlen. Tigridia und Petunia sind in sehr gutem Zustand.

---

## Abschnitt 1: Verifizierung der beauftragten Korrekturen

### K-001: Dahlia pinnata als scientific_name (alle Dahlien)

**Status: KORREKT UMGESETZT**

Alle fuenf Dahlia-Dokumente verwenden konsistent `Dahlia pinnata` als wissenschaftlichen Artnamen sowohl im Textteil (Tabelle 1.1) als auch in den CSV-Zeilen (Section 8.1).

| Dokument | Textteil | CSV Section 8.1 | Ergebnis |
|----------|----------|-----------------|---------|
| dahlia_hapet_daydream.md | `Dahlia pinnata Cav.` | `Dahlia pinnata` | Korrekt |
| dahlia_pinnata_great_silence.md | `Dahlia pinnata Cav.` | `Dahlia pinnata` | Korrekt |
| dahlia_x_hybrida_lavender_perfection.md | `Dahlia pinnata Cav.` | `Dahlia pinnata` | Korrekt |
| dahlia_x_hybrida_armateras.md | `Dahlia pinnata` | `Dahlia pinnata` | Korrekt |
| dahlia_embassy.md | `Dahlia pinnata Cav.` | `Dahlia pinnata` | Korrekt |

Zusaetzlich korrekt: Armateras behaelt einen erklaerenden Hinweis auf das Synonym `Dahlia x hybrida` und `Dahlia variabilis` als historische Handelsnamen.

---

### K-002: Photoperiodismus als "fakultativ" mit 12h Nacht-Schwellenwert

**Status: KORREKT UMGESETZT**

Alle fuenf Dahlia-Dokumente enthalten im Feld `Photoperiode` die korrekte Formulierung: `short_day (fakultativ; Blueteninitiierung bei Nachtlaenge > 12 h gefaerdert, Dahlien bluehen jedoch auch unter Langtagbedingungen; Tuberisierung eindeutig kurztaggesteuert bei Nacht > 12 h)`.

Biologisch korrekt und praezise: Die Unterscheidung zwischen fakultativer Blueteninitiierung (kann auch bei Langtag bluehen) und eindeutiger Tuberisierung (Knollenbildung) unter Kurztagbedingungen ist akkurat. Literaturbeleg: Dahlia Doctor (dahliadoctor.com) bestaetigt den 12h-Schwellenwert.

---

### K-003: Tigridia root_type = corm (nicht bulbous)

**Status: KORREKT UMGESETZT**

Dokument `tigridia_pavonia.md`, Zeile 21:
```
| Wurzeltyp | corm (Korm -- solides Speicherorgan ohne Schalen; bildet jaehrlich Tochterkormen an der Basis; keine echte Zwiebel) |
```

CSV Section 8.1, Zeile 500: `root_type` = `corm`

Ausserdem enthaelt der erklaerende Text einen biologisch korrekten Zusatz, der den Unterschied zur Zwiebel erlaeutert ("kein echte Zwiebel"). Der CSV-Wert `corm` ist konsistent mit dem Textteil. Die Beschreibung "solides Speicherorgan ohne Schalen" ist botanisch praezise (im Gegensatz zur Zwiebel/Bulb mit Schuppenblaetern).

---

### M-002: Great Silence seed_type = clone

**Status: KORREKT UMGESETZT**

Dokument `dahlia_pinnata_great_silence.md`, Section 8.2, Zeile 502:
```csv
Great Silence,Dahlia pinnata,Peter Komen,2018,"informal_decorative;dark_blend;coral_pink;golden_center;long_stems;bee_friendly;cut_flower",90,,clone,
```

`seed_type: clone` ist korrekt fuer eine vegetativ (Knollenteilung/Stecklinge) vermehrte Sorte. Keine Sortenechtheit durch Samen moeglich.

---

### M-004: Armateras + Great Silence = heavy_feeder

**Status: TEILS UMGESETZT - KRITISCHER WIDERSPRUCH IN GREAT SILENCE**

#### Armateras: korrekt
Dokument `dahlia_x_hybrida_armateras.md`, Zeile 46:
```
| Naehrstoffbedarf-Stufe | `heavy_feeder` (Starkzehrer)
```
CSV: `heavy_feeder` - korrekt.

#### Great Silence: WIDERSPRUCH (neuer Fehler nach Korrektur)

Im Stammdaten-Abschnitt (Zeile 31) steht korrekt:
```
| Nährstoffbedarf-Stufe | heavy_feeder (Starkzehrer)
```

Im Fruchtfolge-Abschnitt (Zeile 436) steht jedoch noch der alte, falsche Wert:
```
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
```

Diese Inkonsistenz innerhalb desselben Dokuments ist ein CSV-Import-Risiko: Wenn ein Importer beide Felder liest, entstehen widersprueche. Ausserdem ist `medium_feeder` fuer Dahlia pinnata biologisch falsch - Dahlien sind nachgewiesene Starkzehrer (American Dahlia Society, Greenhouse Grower Dahlia Fertilizer).

**Erforderliche Aktion:** Zeile 436 in `dahlia_pinnata_great_silence.md` korrigieren:
```
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
```

---

### M-006: Dormanz-Luftfeuchte einheitlich 60-75%

**Status: KORREKT UMGESETZT (mit einer Randabweichung)**

| Dokument | Dormanz-Luftfeuchte | Konsistent? |
|----------|---------------------|-------------|
| dahlia_hapet_daydream.md | 65-75% (Tag + Nacht) | Innerhalb des Rahmens |
| dahlia_pinnata_great_silence.md | 60-75% | Korrekt |
| dahlia_x_hybrida_lavender_perfection.md | 60-75% (Tag + Nacht) | Korrekt |
| dahlia_x_hybrida_armateras.md | Keine dedizierte Dormanz-Phase in den Phasenprofilen | Nicht anwendbar |
| dahlia_embassy.md | 60-75% | Korrekt |

Hapet Daydream verwendet 65-75% statt 60-75%. Dies ist biologisch akzeptabel (65% liegt innerhalb des 60-75%-Rahmens), aber leicht inkonsistent gegenueber den anderen Dokumenten. Da 65% innerhalb des definierten Zielbereichs liegt, ist dies kein kritischer Fehler, aber eine Vereinheitlichung auf 60-75% waere empfehlenswert.

Biologische Begruendung des 60-75%-Bereichs: Unter 60% trocknen Knollen aus (Zellschaden, reduzierte Keimrate). Ueber 80% besteht Botrytis-Faulnisgefahr. Der Bereich 60-75% ist wissenschaftlich begruendet und konsistent mit American Dahlia Society-Empfehlungen.

---

### M-008: Petunia Allelopathie = 0.0

**Status: KORREKT UMGESETZT**

Dokument `petunia_x_hybrida.md`, Zeile 28:
```
| Allelopathie-Score | 0.0 (neutral — keine belegte allelopathische Wirkung) |
```

CSV Section 8.1: `allelopathy_score` = `0.0` - korrekt.

---

### M-009: Petunia-Tomate Kompatibilitaets-Score = 0.5

**Status: KORREKT UMGESETZT**

Dokument `petunia_x_hybrida.md`, Section 6.2, Zeile 443:
```
| Tomate (im Gemüsebeet) | Solanum lycopersicum | 0.5 | Bestäubungsförderung durch Petunia-Blüten (nachgewiesen); ABER: geteilte Solanaceae-Schädlinge...
```

Score 0.5 ist fachlich gut begruendet: Die Petunia-Tomate-Kombination hat nachgewiesene Vorteile (Bestaeubungsfoerderung durch gemeinsame Solanaceae-Physiologie), aber auch klare Risiken (geteilte Schiadlinge, TSWV-Uebertragungsrisiko). Ein neutraler bis schwach positiver Score von 0.5 ist korrekt.

---

## Abschnitt 2: Neue Fehler und Praezisierungsbedarfe

### F-001: Petunia VPD Bluetephase zu hoch
**Schwere: Gelb (Praezisierungsbedarf)**
**Dokument:** `spec/ref/plant-info/petunia_x_hybrida.md`, Phase Bluete, Zeile 201

**Aktueller Wert:**
```
| VPD-Ziel (kPa) | 1.0–1.8 |
```

**Problem:** Der obere Grenzwert von 1.8 kPa ist fuer eine einjahrige krautige Pflanze (annuelle Petunie) in der Bluetephase zu hoch. Bei VPD > 1.6 kPa reagieren die meisten Balkonpflanzen mit Trockenstress, Blattrandnekrosen und reduzierter Bluetenqualitaet. Petunien sind zwar waerme- und sonnenliebend, aber kein Xerophyt.

Zum Vergleich: Cannabis in der Blutephase wird auf 0.8-1.2 kPa gehalten; Tomatenpflanzen tolerieren bis ca. 1.5 kPa. Petunien als krutige Annuelle liegen physiologisch naher bei Tomaten als bei Kakteen.

Ausserdem ist 1.8 kPa bei typischen Sommertemperaturen (28°C) und der angegebenen Luftfeuchte von 40-65% rechnerisch kaum erreichbar (bei 28°C und 40% rH ergibt sich VPD = 2.33 kPa - das wuerde weit ueber 1.8 liegen).

**Korrekte Formulierung:** `0.9–1.5 kPa` mit Hinweis: "Bei VPD > 1.5 kPa und Temperaturen > 30°C Bewaesserungsintervall auf taeglich verkuerzen."

---

### F-002: Great Silence Dormanz-Phasenprofil unvollstaendig
**Schwere: Gelb (Unvollstaendigkeit)**
**Dokument:** `spec/ref/plant-info/dahlia_pinnata_great_silence.md`, Phase Seneszenz und Dormanz, Zeilen 206-218

**Problem:** Die Phasen Seneszenz und Dormanz sind in diesem Dokument signifikant weniger detailliert als in den anderen vier Dahlia-Dokumenten. Phase Seneszenz enthaelt nur drei Parameter (Licht mit Platzhalter `<!-- DATEN FEHLEN -->`, Giessen, Temperatur) anstatt der vollen 11 Parameter. Phase Dormanz enthaelt keine Tag/Nacht-Trennung und keinen VPD-Wert.

Konkret: Zeile 207 enthaelt einen sichtbaren HTML-Kommentar als Platzhalter:
```
| Licht PPFD (µmol/m²/s) | <!-- DATEN FEHLEN --> (Freiland, kein Management) |
```

Dieser Platzhalter-Kommentar ist nicht CSV-importierbar und wuerde beim Import zu einem Parse-Fehler fuehren.

**Erforderliche Aktion:** Phase Seneszenz mit denselben Werten wie in dahlia_hapet_daydream.md ausfullen (PPFD 200-600, DLI 8-15, Temp 8-16/2-10, rH 50-70/60-80, VPD 0.3-0.8). HTML-Kommentar entfernen.

---

### F-003: Embassy CSV Cultivar-Zeile fehlt photoperiod_type Wert
**Schwere: Gelb (CSV-Import-Eignung)**
**Dokument:** `spec/ref/plant-info/dahlia_embassy.md`, Section 8.2, Zeile 529

**Aktueller CSV-Inhalt:**
```csv
name,parent_species,breeder,breeding_year,traits,seed_type,photoperiod_type
Embassy,Dahlia pinnata,,,,"ornamental;bee_friendly;cut_flower",clone,
```

**Problem 1:** Der `photoperiod_type`-Wert ist leer (letztes Komma ohne Wert). Wenn das Datenbankschema `NOT NULL` fuer dieses Feld erwartet, wuerde der Import fehlschlagen.

**Problem 2:** `breeder` und `breeding_year` sind leer - fuer Embassy ist der Zuechter und das Jahr tatsaechlich nicht dokumentiert, aber es waere praeferabel, `unknown` oder `--` statt leere Felder zu verwenden, um Import-Parser-Ausnahmen zu vermeiden.

**Problem 3:** Gegenueber anderen Cultivar-CSVs fehlt das Feld `days_to_maturity` und `disease_resistances`. Das Embassy-CSV hat eine andere Spaltenstruktur als die anderen Dahlia-Cultivar-CSVs:

Andere Dahlien verwenden: `name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type`
Embassy verwendet: `name,parent_species,breeder,breeding_year,traits,seed_type,photoperiod_type`

Diese Inkonsistenz der Spaltenreihenfolge und -auswahl wuerde beim Batch-Import zu Mapping-Fehlern fuehren.

**Korrekte CSV-Zeile:**
```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Embassy,Dahlia pinnata,unknown,unknown,"ornamental;bee_friendly;cut_flower",90,,clone
```

---

### F-004: Hapet Daydream Dormanz-Luftfeuchte leicht abweichend
**Schwere: Gruen (Konsistenzhinweis, kein Fehler)**
**Dokument:** `spec/ref/plant-info/dahlia_hapet_daydream.md`, Dormanz-Phase, Zeilen 245-246

**Aktueller Wert:** `65-75%` (Tag und Nacht)
**Zielvorgabe laut M-006:** `60-75%`

Biologisch liegt 65-75% innerhalb des Zielbereichs, aber es ist die einzige der fuenf Dahlia-Dokumentationen, die den unteren Grenzwert bei 65% statt 60% ansetzt. Fuer die Konsistenz im CSV-Batch-Import und fuer einheitliche Pflegeerinnerungen waere eine Anpassung auf 60-75% empfehlenswert.

---

## Abschnitt 3: Cross-Dokument-Konsistenzpruefung

### 3.1 Dahlia pinnata - Konsistenz der Kernparameter

| Parameter | Hapet Daydream | Great Silence | Lav. Perfection | Armateras | Embassy | Konsistent? |
|-----------|---------------|---------------|-----------------|-----------|---------|-------------|
| scientific_name | Dahlia pinnata Cav. | Dahlia pinnata Cav. | Dahlia pinnata Cav. | Dahlia pinnata | Dahlia pinnata Cav. | Ja (K-001) |
| photoperiod_type | short_day (fakultativ) | short_day (fakultativ) | short_day (fakultativ) | short_day (fakultativ) | short_day (fakultativ) | Ja (K-002) |
| root_type | tuberous | tuberous | tuberous | tuberous | tuberous | Ja |
| cycle_type | perennial | perennial | perennial | perennial | perennial | Ja |
| frost_sensitivity | tender | tender | tender | tender | tender | Ja |
| nutrient_demand_level | heavy_feeder | heavy_feeder (aber Fruchtfolge: medium_feeder!) | heavy_feeder | heavy_feeder | heavy_feeder | NEIN - Great Silence Widerspruch |
| Dormanz-Luftfeuchte | 65-75% | 60-75% | 60-75% | nicht separat | 60-75% | Leicht abweichend |
| seed_type (Cultivar) | clone | clone | clone | clone | clone | Ja |
| allelopathy_score | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Ja |

### 3.2 Tigridia pavonia - Isolierte Pruefung

Tigridia hat keinen Batch-Gegenpeer; Cross-Konsistenz-Pruefung entfaellt. Interne Konsistenz ist gegeben: `corm` im Text und im CSV identisch, `light_feeder` konsistent, VPD-Werte plausibel, Dormanz-Parameter (10-13 degC, 50-65% rH) korrekt und von Dahlien-Werten korrekt abgegrenzt.

Wichtig: Der Hinweis in Section 4.3, dass Tigridia-Kormen NICHT bei 4-8 degC mit Dahlien-Knollen gelagert werden sollen (Tigridia benoetigt 10-13 degC), ist biologisch korrekt und fuer das Kamerplanter-System wichtig, da Nutzer moeglicherweise beide Arten gleichzeitig kultivieren.

### 3.3 Petunia x hybrida - Isolierte Pruefung

Petunia hat keine Batch-Peers. Interne Konsistenz ist gut. Der `allelopathy_score: 0.0` (M-008) und der Tomate-Score `0.5` (M-009) sind korrekt umgesetzt. Der Solanaceae-Familienhinweis (geteilte Schiadlinge mit Kartoffel, Tomate) ist konsistent mit dem Mischkultur-Abschnitt.

---

## Abschnitt 4: Weitere fachliche Pruefpunkte

### 4.1 Biologische Korrektheit - Ergebnis OK

**Tuberisierung vs. Blueteninitiierung bei Dahlien (K-002):**
Die in allen Dahlia-Dokumenten verwendete Formulierung ist biologisch korrekt. Die Tuberisierung (Knollenbildung) bei Dahlien ist staerker kurztagsabhaengig als die Blueteninitiierung. Studien (Warrington & Norton 1991, American Dahlia Society) bestaetigen den 12h-Nacht-Schwellenwert fuer die Tuberisierung. Dahlien sind praktisch tagneutral zur Bluete und werden bei Langtagbedingungen durch andere Signale (Temperatur, Pflanzenalter) zur Blute angeregt.

**Tigridia pavonia Corm vs. Bulb (K-003):**
Korrekt. Tigridia bildet einen echten Korm (Corm): ein solides, modifiziertes Speicherorgan aus Stengelgewebe, ohne die charakteristischen Schuppenblaetter einer Zwiebel (Bulb). Die Mutterknolle wird vollstaendig verbraucht und durch neue Tochterkormen ersetzt - auch dies korrekt beschrieben.

**Dahlia pinnata als korrekter wissenschaftlicher Name (K-001):**
Korrekt. `Dahlia pinnata` Cav. ist der akzeptierte Name nach Plants of the World Online (POWO, powo.science.kew.org). `Dahlia variabilis` Willd. und `Dahlia x hybrida` sind Synonyme bzw. Handelsnamen ohne taxonomischen Status. Die APG IV-Klassifikation hat keinen Einfluss auf diese Nomenklatur (Asteraceae-Rang unveraendert).

### 4.2 Pruefung: IPM-Daten fachlich korrekt?

**Dahlien:** Die angegebenen Schiadlinge (Myzus persicae, Aphis gossypii, Forficula auricularia, Tetranychus urticae, Frankliniella occidentalis) sind korrekt und vollstaendig fuer mitteleuropaeische Freilandkultur. Hinweis auf Ohrwurm (Forficula auricularia) als Nützling bei Blattlaeussen ist biologisch korrekt und im Kontext ambivalent bewertet - das ist fachlich akkurat.

**Tigridia:** Wuehlmaus (Arvicola terrestris) als Schaedling auf Knolle/Corm ist korrekt und ein praktisch relevasntes, oft unterbewertetes Risiko. Der Hinweis auf physischen Schutz durch Drahtgeflecht-Pflanzkorb ist die einzige wirksame Praeventionsmassnahme und korrekt dokumentiert.

**Petunia:** Die vollstaendige Erwaehnung der Weissen Fliege (Trialeurodes vaporariorum) ist korrekt und fuer Petunia als Solanaceae relevant. Encarsia formosa als biologisches Gegenmassel ist korrekt angegeben.

### 4.3 Pruefung: Toxizitaetsdaten vollstaendig?

| Art | Katzen | Hunde | Kinder | Pferde | Bewertung |
|-----|--------|-------|--------|--------|-----------|
| Dahlia pinnata | Ja (ASPCA) | Ja (ASPCA) | Nein (korrekt) | Nicht erwaehnt | Pferde fehlen in allen Dahlia-Docs - Hinweis fuer zukuenftige Revision |
| Tigridia pavonia | Nein | Nein | Nein | Nicht erwaehnt | Korrekt; keine ASPCA-Listung als giftig |
| Petunia x hybrida | Nein | Nein | Nein | Nicht erwaehnt | Korrekt (ASPCA: nicht giftig) |

Dahlien: ASPCA listet `Dahlia spp.` als giftig fuer Hunde, Katzen UND Pferde. In keinem der fuenf Dahlia-Dokumente wird die Toxizitaet fuer Pferde erwaehnt. Fuer eine App mit Fokus auf Hobby-Gaertner ist dies relevant (Gaerten in Pferdenaehe). Empfehlung: `is_toxic_horses: true` ergaenzen.

### 4.4 Pruefung: Pollenallergen-Eintraege konsistent?

| Art | Pollenallergen | Begruendung | Korrekt? |
|-----|---------------|-------------|----------|
| Dahlia pinnata | true (alle 5 Docs) | Asteraceae-Pollen; entomophil, aber Kreuzreaktion mit Korbblutlern | Korrekt |
| Tigridia pavonia | false | Insektenbestaeubung, nicht aerogen | Korrekt |
| Petunia x hybrida | false | Insektenbestaeubung, Solanaceae | Korrekt |

Hinweis: Bei Hapet Daydream und Great Silence ist `pollenallergen: true` mit dem Hinweis auf Kreuzreaktionen mit Chrysantheme und Kamille erwaehnt. Dies ist klinisch relevant (Asteraceae-Kreuzallergie). Korrekt dokumentiert.

---

## Abschnitt 5: CSV-Import-Gesamtbewertung

### 5.1 Importierbarkeit der Species CSV-Zeilen

| Dokument | Spalten vollstaendig | Werte plausibel | Sonderzeichen OK | Import-Status |
|----------|---------------------|-----------------|------------------|---------------|
| dahlia_hapet_daydream.md | Ja | Ja | Ja | OK |
| dahlia_pinnata_great_silence.md | Ja | Ja | Ja | OK |
| dahlia_x_hybrida_lavender_perfection.md | Ja | Ja | Ja | OK |
| dahlia_x_hybrida_armateras.md | Ja | Ja | Ja | OK |
| dahlia_embassy.md | Ja | Ja | Ja | OK |
| tigridia_pavonia.md | Ja | Ja | Ja | OK |
| petunia_x_hybrida.md | Ja | Ja | Teilweise (Wertebereiche mit Bindestrich in numerischen Feldern) | Pruefbedarf |

Hinweis Petunia CSV: Felder wie `mature_height_cm` enthalten Werte wie `"20–40"` (Bereich als String) statt einem einzelnen numerischen Wert. Dies ist in anderen Dokumenten konsistent gehandhabt (Hapet Daydream: `120`), aber bei Petunia ist ein Wert-Bereich angegeben. Wenn das Schema numerische Einzelwerte erwartet, wuerde dies einen Importfehler ausloesen.

### 5.2 Importierbarkeit der Cultivar CSV-Zeilen

| Dokument | Spaltenstruktur | Fehlende Werte | Import-Status |
|----------|-----------------|----------------|---------------|
| dahlia_hapet_daydream.md | Standardstruktur | Keine | OK |
| dahlia_pinnata_great_silence.md | Erweitert (+photoperiod_type, leer) | photoperiod_type leer | Warnung |
| dahlia_x_hybrida_lavender_perfection.md | Standardstruktur | Keine | OK |
| dahlia_x_hybrida_armateras.md | Standardstruktur | disease_resistances leer | OK (nullable) |
| dahlia_embassy.md | ABWEICHENDE Struktur | breeding_year, breeder leer | FEHLER (F-003) |

---

## Abschnitt 6: Priorisierte Massnahmenliste

### Kritisch (vor CSV-Import zu beheben)

| ID | Dokument | Problem | Massnahme |
|----|----------|---------|-----------|
| A-001 | dahlia_pinnata_great_silence.md | Fruchtfolge-Abschnitt Zeile 436: `medium_feeder` statt `heavy_feeder` (Inkonsistenz zu Stammdaten) | Ersetzen durch `Starkzehrer (heavy_feeder)` |
| A-002 | dahlia_pinnata_great_silence.md | Seneszenz-Phase Zeile 207: HTML-Kommentar `<!-- DATEN FEHLEN -->` nicht CSV-importierbar | Durch korrekten PPFD-Wert ersetzen (z.B. `0–400 (Freiland, keine Steuerung)`) |
| A-003 | dahlia_embassy.md | Cultivar CSV Section 8.2: Abweichende Spaltenstruktur, fehlende `days_to_maturity` und `disease_resistances` Spalten | CSV-Zeile auf Standardformat anpassen |

### Empfohlen (fachliche Verbesserung)

| ID | Dokument | Problem | Massnahme |
|----|----------|---------|-----------|
| B-001 | petunia_x_hybrida.md | VPD Bluetephase 1.0-1.8 kPa; oberer Wert physiologisch kritisch | Anpassen auf 0.9-1.5 kPa |
| B-002 | dahlia_hapet_daydream.md | Dormanz-Luftfeuchte 65-75% statt 60-75% (Konsistenz) | Anpassen auf 60-75% |
| B-003 | Alle 5 Dahlia-Docs | Pferde-Toxizitaet fehlt (ASPCA: giftig fuer Pferde) | `is_toxic_horses: true` ergaenzen |

### Optional (zukuenftige Revision)

| ID | Dokument | Problem | Massnahme |
|----|----------|---------|-----------|
| C-001 | petunia_x_hybrida.md | `mature_height_cm` und `mature_width_cm` als Wertebereiche in CSV (kein einzelner Zahlenwert) | Entscheidung ob Schema Bereiche als String akzeptiert oder Maximalwert angegeben werden soll |
| C-002 | dahlia_pinnata_great_silence.md | Cultivar CSV hat zusaetzliche Spalte `photoperiod_type` ohne Wert | Leere Spalte entfernen |

---

## Abschnitt 7: Biologische Qualitaets-Highlights

Folgende Aspekte der Dokumente verdienen besondere Erwaehnung als fachlich besonders gut ausgefuehrt:

**Tigridia pavonia - Lagertemperatur-Differenzierung:**
Der explizite Hinweis, dass Tigridia-Kormen bei 10-13 degC gelagert werden muessen (und NICHT bei den fuer Dahlien ueblichen 4-8 degC), ist biologisch korrekt und praktisch wichtig. Tigridia stammt aus mexikanischen Hochlagen (2000-3000 m) mit milderen Wintertemperaturen als die mitteleuropaeischen Klimazonen. Dieser Unterschied wird in Gartenliteratur oft vernachlaessigt.

**Dahlia - Tuberisierung vs. Blueteninitiierung:**
Die Unterscheidung zwischen fakultativer Blueteninitiierung (short_day, aber auch unter Langtag moeglich) und eindeutiger Kurztagabhaengigkeit der Tuberisierung ist wissenschaftlich korrekt und in Gaertner-Praxisliteratur selten so praezise formuliert.

**Petunia - Eisenbedarf:**
Der Hinweis auf den hohen Eisenbedarf von Petunia x hybrida und die pH-abhaengige Eisenverfuegbarkeit (Eisenchelat-Empfehlung ab pH > 6.2) ist ein klinisch relevanter und oft missverstandener Aspekt der Petunien-Pflege. Gut dokumentiert.

**Dahlia - Ohrwurm-Ambivalenz:**
Der Ohrwurm (Forficula auricularia) ist in allen fuenf Dahlia-Dokumenten korrekt als ambivalent eingestuft: Frasskaden an Bluetenblaettern, aber auch Blattlaus-Fraesser. Der Hinweis "Bekaempfung abwaegen" ist agrarbiologisch korrekt im Sinne des integrierten Pflanzenschutzes (IPM).

---

## Glossar

- **PPFD** (Photosynthetic Photon Flux Density): Photosynthetisch nutzbare Lichtmenge in umol/m2/s
- **DLI** (Daily Light Integral): Tageslicht-Gesamtmenge in mol/m2/d
- **VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa - beschreibt den "Durst" der Luft
- **Corm (Korm)**: Modifiziertes, solides Speicherorgan aus Stengelgewebe (Tigridia, Gladiole, Krokus) - keine Zwiebel
- **Bulb (Zwiebel)**: Speicherorgan aus modifizierten Schuppenblaetern (Tulpe, Narzisse, Zwiebel)
- **Tuberous Root (Knollenwurzel)**: Verdickte, naehrstoffspeichernde Wurzel (Dahlie) - kein Stengel-Organ
- **Tuberisierung**: Bildung von Speicherknollen bei Dahlien - kurztagsabhaengig (Nacht > 12h)
- **Fakultativer Kurztagspflanze**: Pflanze, bei der Blute durch Kurztag gefaerdert wird, aber auch unter Langtag erfolgen kann
- **heavy_feeder / Starkzehrer**: Pflanzen mit hohem Naehrstoffbedarf, die regelmassige intensive Duengung benoetigen
- **Clone (seed_type)**: Vegetativ vermehrte Sorte - keine generative Vermehrung durch Samen moeglich ohne Sortenechts-Verlust
- **IPM** (Integrated Pest Management): Integrierter Pflanzenschutz - biologische, physikalische und chemische Massnahmen kombiniert
