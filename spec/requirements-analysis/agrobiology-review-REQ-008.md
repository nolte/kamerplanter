# Agrarbiologisches Anforderungsreview: REQ-008 Post-Harvest

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Indoor-Anbau, Hydroponik, geschuetzter Anbau, Zimmerpflanzen (soweit anwendbar)
**Analysierte Dokumente:**
- `spec/req/REQ-008_Post-Harvest.md` (Hauptdokument, Version 2.0)
- `spec/req/REQ-007_Erntemanagement.md` (Upstream-Abhaengigkeit)
- `spec/req/REQ-003_Phasensteuerung.md` (Phasen-State-Machine)
- `spec/req/REQ-010_IPM-System.md` (Pflanzenschutz, Karenzzeiten)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 3/5 | Grundwerte bei Cannabis und Allium brauchbar, aber mehrere biologische Fehler und Ungenauigkeiten (Pilze, Fermentation, Haltbarkeit) |
| Indoor-Vollstaendigkeit | 3/5 | Cannabis-Curing sehr detailliert, andere Indoor-Kulturen (Kraeuter, Microgreens, Chili) stark unterrepraesentiert |
| Hydroponik-Tiefe | 1/5 | Keine Differenzierung der Post-Harvest-Anforderungen nach Anbausystem (Hydro vs. Soil vs. Substrat) |
| Messbarkeit der Parameter | 4/5 | RH%, Temperatur und Gewicht gut quantifiziert; fehlend: Wasseraktivitaet (aw), Restfeuchte-Messung |
| Praktische Umsetzbarkeit | 3/5 | Cannabis-Curing und Schimmel-Praevention gut umsetzbar; Haltbarkeitsprognose stark vereinfacht; Mold-Identifikation per Keyword zu fehleranfaellig |
| Abdeckung Anbaukontexte | 2/5 | Stark Cannabis-zentriert, Gemuese/Kraeuter nur oberflaechlich, Pilze fehlerhaft |

REQ-008 ist ein solide strukturiertes Dokument mit starkem Fokus auf Cannabis-Post-Harvest-Prozesse (Trocknung, Jar-Curing, Burping). Die ArangoDB-Modellierung und die Python-Logik sind durchdacht und weitgehend praxisnah. Allerdings weist das Dokument mehrere biologische Ungenauigkeiten auf (insbesondere bei Pilzen und Fermentation), ignoriert den zentralen Parameter Wasseraktivitaet (aw) als primaeren Indikator fuer mikrobiologische Sicherheit, und differenziert nicht zwischen Post-Harvest-Anforderungen verschiedener Anbausysteme. Die Haltbarkeitsprognose ueber hardcodierte Tages-Literale ist biologisch zu simplifiziert und praktisch irrefuehrend.

---

## Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: Pilz-Trocknung -- Wirkstoffverlust-Schwelle bei Agaricus bisporus falsch kontextualisiert

**Anforderung:** "Pilze: Dehydrator: 35-40 Grad C bis cracker-dry. Kritisch: Ueber 40 Grad C = Wirkstoffverlust" (`REQ-008_Post-Harvest.md`, Zeile 35-36)
**Problem:** *Agaricus bisporus* (Champignon) ist ein Speisepilz ohne pharmakologisch relevante "Wirkstoffe" im engeren Sinne. Die 40-Grad-C-Grenze ist spezifisch fuer *Psilocybe*-Arten relevant (Psilocybin-Degradation beginnt ab ca. 50-60 Grad C, nicht 40 Grad C -- die Literatur zeigt signifikante Verluste erst ab 60 Grad C). Fuer Speisepilze (Shiitake, Champignon) sind 50-60 Grad C gaengig und unproblematisch. Die Zuordnung von *Agaricus bisporus* als Referenzart im `DRYING_SPECS`-Dict (Zeile 704) mit der "Wirkstoffverlust"-Warnung ist taxonomisch und biochemisch falsch.
**Korrekte Formulierung:** Speisepilze (*Agaricus bisporus*, *Lentinula edodes*) separat von Funktionspilzen fuehren. Trocknungstemperatur speziesspezifisch: Champignon 50-60 Grad C, Shiitake 40-50 Grad C (Lentinan-Erhalt), *Psilocybe* spp. max. 40 Grad C (Alkaloid-Erhalt, wobei auch hier neuere Studien hoehere Toleranz zeigen). "Wirkstoffverlust" nur bei Arten mit definierten Wirkstoffen verwenden.
**Gilt fuer Anbaukontext:** Indoor (Pilzzucht), Gewaeechshaus

### F-002: Fermentation Sauerkraut/Kimchi -- Temperaturbereich und Prozess falsch beschrieben

**Anforderung:** "Fermentation: 3-6 Wochen bei 18-22 Grad C. Taeglich Gasen ablassen." (`REQ-008_Post-Harvest.md`, Zeile 52-53)
**Problem:** Milchsaeurefermentation (Sauerkraut) laeuft optimal bei 18-20 Grad C in den ersten 3 Tagen und sollte dann bei 15-18 Grad C fortgefuehrt werden. Die Aussage "3-6 Wochen" bei konstantem Temperaturbereich ist ungenuegend differenziert. Wichtiger: "Taeglich Gasen ablassen" ist fachlich missverstaendlich -- bei klassischer Gaertopf-Fermentation mit Wasserrinne entweicht CO2 selbsttaetig. Bei Schraubglaesern muss das Gas zwar abgelassen werden, aber die Formulierung suggeriert, dass dies eine inhaerent notwendige Pflegemassnahme ist, anstatt ein Artefakt des Behaeltertyps. Kimchi hat zudem voellig andere Temperaturprofile (initial bei Raumtemperatur 1-3 Tage, dann Kuehlschrank 4 Grad C fuer Wochen bis Monate).
**Korrekte Formulierung:** Sauerkraut: Phase 1 (heterofermentativ, Tag 1-3): 18-20 Grad C; Phase 2 (homofermentativ, Tag 4-28): 15-18 Grad C. Gasmanagement behaelterabhaengig (Gaertopf: automatisch; Schraubglas: taeglich entlueften). Kimchi: Separat fuehren mit eigenem Temperaturprofil. pH-Monitoring als Fermentationskontrolle ergaenzen (Ziel: pH < 4,6 fuer Lebensmittelsicherheit).
**Gilt fuer Anbaukontext:** Indoor (Verarbeitung), alle Kontexte

### F-003: Tabak-Fermentation -- Temperaturgrenze und Prozess stark vereinfacht

**Anforderung:** "Tabak: Fermentation in Ballen: 6-12 Monate. Temperatur-kontrolliert: Nicht ueber 55 Grad C" (`REQ-008_Post-Harvest.md`, Zeile 57-58)
**Problem:** Tabakfermentation ist ein hochkomplexer Prozess mit mindestens drei unterschiedlichen Methoden (Air-Curing, Flue-Curing, Fire-Curing, Sun-Curing), die jeweils voellig andere Parameter haben. "Fermentation in Ballen" beschreibt nur die Bulk-Curing-Phase, die nach dem initialen Trocknen/Curing stattfindet. Die 55-Grad-C-Grenze bezieht sich auf Flue-Curing und ist kein allgemeines Maximum. Fuer ein System das primaer auf Indoor-Anbau und Hobbygaertner zielt, ist die Einbindung von Tabak-Fermentation fraglich, da der Anbau in Deutschland genehmigungspflichtig ist (TabStG) und die Fermentation professionelles Equipment erfordert.
**Korrekte Formulierung:** Entweder Tabak aus dem Scope entfernen oder deutlich differenzierter beschreiben mit Curing-Typ-Unterscheidung. Mindestens einen Rechtshinweis zum Tabaksteuergesetz ergaenzen.
**Gilt fuer Anbaukontext:** Outdoor (Tabakanbau ist primaer Freiland)

### F-004: Cannabis Slow-Dry Gewichtsverlust-Zielwert fehlerhaft

**Anforderung:** "Ziel: 60-65% Gewichtsverlust (von Nass zu Trocken)" (`REQ-008_Post-Harvest.md`, Zeile 25)
**Problem:** Der Gewichtsverlust bei der Trocknung von Cannabis betraegt typischerweise 75-80%, nicht 60-65%. Frisches Cannabis hat einen Wassergehalt von ca. 75-80%. Das Ziel-Trockengewicht liegt bei 10-12% Restfeuchte, was einem Gewichtsverlust von ca. 75-80% entspricht. Die 60-65% wuerden eine Restfeuchte von 20-25% bedeuten -- das ist deutlich zu feucht und ein Schimmelrisiko. Widerspruch: Im Python-Code (`calculate_dryness_progress`, Zeile 572-573) wird korrekt von "75-80% Gewichtsverlust fuer ~10% Restfeuchte" gesprochen, und im Testszenario 1 wird bei 450g -> 112g Zielgewicht (75% Verlust) gerechnet. Die Business-Case-Beschreibung widerspricht also dem eigenen Code.
**Korrekte Formulierung:** "Ziel: 75-80% Gewichtsverlust (von Nassgewicht zu Trockengewicht), entsprechend 10-12% Restfeuchte. Bei 450g Nassgewicht ergibt sich ein Ziel-Trockengewicht von 90-112g."
**Gilt fuer Anbaukontext:** Indoor (Growbox, Growzelt)

### F-005: BurpingEvent-Validator -- RH nach Burping KANN hoeher sein

**Anforderung:** "RH nach Burping sollte nicht hoeher sein als vorher" -- `field_validator` in `BurpingEvent` (`REQ-008_Post-Harvest.md`, Zeile 1230-1237)
**Problem:** Diese Validierungsregel ist biologisch falsch. Wenn die Umgebungsluft eine hoehere Luftfeuchtigkeit hat als das Jar-Innere (z.B. im Sommer oder in feuchten Raeumen), KANN die RH im Jar nach dem Burping steigen. Das Burping tauscht Luft aus -- die Richtung des Feuchtigkeitsausgleichs haengt vom VPD-Gradienten zwischen Jar und Umgebung ab. Diese Validierungsregel wuerde korrekte Messwerte ablehnen.
**Korrekte Formulierung:** Validator entfernen oder in eine Warnung umwandeln: "WARNUNG: RH nach Burping hoeher als vorher -- Umgebungsluft pruefen. Burping ist nur sinnvoll wenn Umgebungs-RH < Jar-RH."
**Gilt fuer Anbaukontext:** Indoor

### F-006: Ethylen-Management bei Tomaten -- vereinfachte Darstellung

**Anforderung:** "Ethylen-Management: Mit reifen Aepfeln lagern" (`REQ-008_Post-Harvest.md`, Zeile 66)
**Problem:** Die Empfehlung "mit reifen Aepfeln lagern" ist eine starke Vereinfachung. Ethylen-empfindliche Produkte (z.B. Salat, Gurken, Brokkoli) duerfen NICHT zusammen mit Ethylen-produzierenden Fruechten gelagert werden. Das System muss Ethylen-Kompatibilitaetsgruppen fuehren, nicht nur eine pauschale Empfehlung. Zudem: Exogenes Ethylen (Ethrel/Ethephon) ist die professionelle Methode, nicht Aepfel-Beilagerung. Fuer Indoor-Nachreife ist kontrollierte Ethylen-Exposition (0,1-1 ppm) bei 18-21 Grad C der Fachstandard.
**Korrekte Formulierung:** Ethylen-Kompatibilitaetsgruppen als Datenmodell ergaenzen. Nachreife-Protokoll: "Klimakterische Fruechte (Tomate, Banane, Avocado): 18-21 Grad C, 85-90% rH, Ethylen 0,1-1 ppm oder Beilagerung mit klimakterischen Fruechten. NICHT zusammen mit ethylenempfindlichen Produkten lagern."
**Gilt fuer Anbaukontext:** Indoor, Gewaeechshaus, Outdoor

---

## Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: Wasseraktivitaet (aw) als primaerer Sicherheitsparameter fehlt

**Anbaukontext:** Indoor, Gewaeechshaus, alle Kontexte
**Fehlende Parameter:** Wasseraktivitaet (aw) als messbare Groesse in `StorageCondition`, `DryingProgress` und `StorageObservation`
**Begruendung:** Die Wasseraktivitaet (aw) ist DER zentrale Parameter fuer mikrobiologische Sicherheit in der Post-Harvest-Phase. Sie beschreibt das verfuegbare Wasser fuer Mikroorganismen und ist aussagekraeftiger als die relative Luftfeuchtigkeit der Umgebung. Schimmelpilze wachsen ab aw > 0,65, Hefen ab aw > 0,88, Bakterien ab aw > 0,91. Getrocknete Kraeuterprodukte muessen aw < 0,60 erreichen fuer Langzeitlagerung. Das Dokument verwendet ausschliesslich RH% als Proxy, was bei heterogenem Trocknungsgut (z.B. dichte Cannabis-Blueten mit Feuchtnestern) versagen kann.
**Formulierungsvorschlag:**
```
StorageCondition ergaenzen:
- aw_target: Optional[float]  # Wasseraktivitaet Zielwert (0.0-1.0)
- aw_critical_max: float = 0.65  # Schimmelgrenze

StorageObservation ergaenzen:
- water_activity: Optional[float]  # aw-Messung (Handgeraete ab ca. 200 EUR verfuegbar)

DryingProgress ergaenzen:
- water_activity: Optional[float]  # aw als primaerer Endpunkt-Indikator

Spezies-spezifische aw-Zielwerte:
- Cannabis/Kraeutertrocknung: aw < 0.55 (Langzeitlagerung) bis 0.60 (Kurzzeit)
- Getrocknete Chili: aw < 0.60
- Pilze getrocknet: aw < 0.50
```

### U-002: Differenzierung nach Anbausystem (Hydro vs. Soil vs. Organisch) fehlt

**Anbaukontext:** Hydroponik, Indoor
**Fehlende Parameter:** Post-Harvest-Qualitaetsunterschiede nach Anbausystem
**Begruendung:** Das Anbausystem beeinflusst die Post-Harvest-Qualitaet signifikant:
- **Hydro-Cannabis:** Typischerweise niedrigerer Terpen-Gehalt, schnellere Trocknung (weniger Pflanzenstruktur), Curing-Dauer kann kuerzer ausfallen
- **Living-Soil-Cannabis:** Hoeherer Terpen-Gehalt, langsamere Trocknung empfohlen, laengeres Curing lohnt sich mehr
- **Hydro-Gemuese:** Hoeherer Wassergehalt (z.B. Tomaten), schlechtere Lagerfaehigkeit als Freilandprodukte, Brix-Werte oft niedriger
- **Freiland-Gemuese:** Dickere Schalen (UV-Exposition), bessere natuerliche Lagerfaehigkeit
Das Dokument behandelt alle Produkte gleich unabhaengig vom Anbausystem.
**Formulierungsvorschlag:** `StorageProtocol` um `growing_system_modifier: Optional[dict]` ergaenzen mit angepassten Trocknungszeiten und Curing-Empfehlungen pro Anbausystem.

### U-003: Keine Verknuepfung zwischen IPM-Karenzzeiten (REQ-010) und Post-Harvest-Sicherheit

**Anbaukontext:** Indoor, Gewaeechshaus
**Fehlende Parameter:** Karenzzeit-Status als Eingangsbedingung fuer Post-Harvest-Prozesse
**Begruendung:** REQ-010 definiert `safety_interval_days` fuer Pflanzenschutzbehandlungen und eine Karenzzeit-Pruefung vor Ernte (`requires_harvest_delay`-Edge). REQ-008 referenziert REQ-010 nicht in den Abhaengigkeiten. Kritisch: Wenn ein Batch nach Ernte in den Post-Harvest-Prozess geht, muss sichergestellt sein, dass alle Karenzzeiten eingehalten wurden. Besonders bei Cannabis ist PSM-Rueckstandsfreiheit ein Qualitaetskriterium. Zudem koennen bestimmte Trocknungs-/Fermentierungsprozesse Rueckstaende konzentrieren (durch Wasserverlust steigt die Konzentration pro Trockenmasse).
**Formulierungsvorschlag:**
```
Abhaengigkeiten ergaenzen:
- REQ-010 (IPM): Karenzzeit-Validierung als Gate-Condition vor Batch-Erstellung

StorageObservation ergaenzen:
- pesticide_residue_status: Literal['not_tested', 'passed', 'failed', 'pending']

Geschaeftslogik: Batch darf Post-Harvest nur starten wenn:
1. Alle aktiven Karenzzeiten aus REQ-010 abgelaufen sind
2. ODER expliziter Override mit Dokumentation
```

### U-004: Schimmelidentifikation -- Aspergillus-Mykotoxin-Warnung fehlt

**Anbaukontext:** Indoor, alle Kontexte
**Fehlende Parameter:** Mykotoxin-Risikobewertung, insbesondere Aflatoxine (Aspergillus flavus/parasiticus) und Ochratoxin A (Aspergillus ochraceus)
**Begruendung:** Die `identify_mold_type`-Methode identifiziert Aspergillus nur als "Schwarzschimmel", was zu kurz greift. *Aspergillus niger* (schwarz) ist vergleichsweise harmlos, waehrend *Aspergillus flavus* (gruen-gelb) Aflatoxine produziert -- eines der staerksten natuerlichen Karzinogene. Die Farbzuordnung "schwarz/dunkelgruen = Aspergillus" ist taxonomisch ungenau und fuehrt zu falschen Risikoeinschaetzungen. Bei Cannabis ist Aspergillus-Kontamination ein ernstes Gesundheitsrisiko, insbesondere fuer Immunsupprimierte.
**Formulierungsvorschlag:** Aspergillus in Untergruppen differenzieren (*A. niger*, *A. flavus*, *A. fumigatus*). Generelle Empfehlung bei jedem Schimmelfund auf Cannabis: "Kontaminiertes Material NICHT konsumieren. Bei Verdacht auf Aspergillus: Laboranalyse empfohlen."

### U-005: Fehlende CO2-Ueberwachung im Trocknungsraum

**Anbaukontext:** Indoor
**Fehlende Parameter:** CO2-Konzentration in `StorageCondition` und `StorageObservation`
**Begruendung:** Im Business Case wird CO2-Akkumulation korrekt als Risiko bei zu wenig Luftaustausch genannt (Zeile 95-96), aber weder im Datenmodell noch in der Monitoring-Logik wird CO2 erfasst. In geschlossenen Trocknungsraeumen mit grosser Pflanzenmasse kann die CO2-Konzentration auf 2000-5000 ppm steigen (Zellatmung waehrend Trocknung), was die Trocknungskinetik beeinflusst und auf unzureichende Belueftung hinweist.
**Formulierungsvorschlag:**
```
StorageCondition ergaenzen:
- co2_max_ppm: Optional[int] = 1500  # Grenzwert fuer Belueftungsalarm

StorageObservation ergaenzen:
- co2_ppm: Optional[int]  # Gemessene CO2-Konzentration
```

### U-006: Fehlende Verknuepfung zu REQ-003 Phasen-State-Machine

**Anbaukontext:** alle Kontexte
**Fehlende Parameter:** Post-Harvest als explizite Phase in der State-Machine
**Begruendung:** REQ-003 definiert die Phasen-Sequenz als "Keimung -> Saemling -> Vegetativ -> Bluete -> Fruchtreife -> Seneszenz". Post-Harvest-Prozesse sind hier nicht abgebildet. Die Schnittstelle zwischen REQ-003 (Phase `is_terminal: true`) und REQ-008 (Post-Harvest-Start) ist nicht formal definiert. Wann genau endet die REQ-003-Zustaendigkeit und wann beginnt REQ-008? Die `batches`-Collection in REQ-007 stellt die Bruecke dar, aber der Uebergang ist nicht als State-Transition modelliert.
**Formulierungsvorschlag:** Eine explizite `post_harvest`-Phase in REQ-003 ergaenzen oder alternativ einen formalen State-Uebergang "Phase terminal -> Batch erstellt -> Post-Harvest-Protokoll gestartet" definieren. Das wuerde auch die Abfolge Flushing (REQ-007) -> Ernte (REQ-007) -> Trocknung (REQ-008) -> Curing (REQ-008) -> Storage (REQ-008) als zusammenhaengende Pipeline sichtbar machen.

### U-007: Trim/Manikuere-Prozess fehlt vollstaendig

**Anbaukontext:** Indoor (Cannabis)
**Fehlende Parameter:** Trim-Phase zwischen Ernte und Trocknung/Curing
**Begruendung:** Fuer Cannabis fehlt der Trim-Prozess (Wet-Trim vs. Dry-Trim), der qualitaets- und workflow-relevant ist:
- **Wet-Trim:** Sofort nach Ernte, einfacher, schnellere Trocknung, geringerer Platz
- **Dry-Trim:** Nach Trocknung, langsamere Trocknung (besser fuer Terpen-Erhalt), hoehere Arbeitsintensitaet
- **Trim-Waste:** REQ-007 erfasst `trim_waste_percent` in `yield_metrics`, aber REQ-008 nutzt diese Daten nicht
- **Sugar-Leaves vs. Fan-Leaves:** Unterschiedliche Verwertung (Hash/Extrakt vs. Kompost)
**Formulierungsvorschlag:** `TrimProtocol`-Node ergaenzen mit: `trim_type: Literal['wet', 'dry', 'mixed']`, `trim_quality: Literal['machine', 'hand', 'combination']`, `trim_weight_g: float`, `usable_trim_g: float`. Als Phase zwischen Ernte und Trocknung/Curing einordnen.

### U-008: Fehlende Beruecksichtigung von Licht als Degradationsfaktor

**Anbaukontext:** Indoor, alle Kontexte
**Fehlende Parameter:** UV-Exposition und Licht-Degradation im Monitoring
**Begruendung:** Das `StorageCondition`-Modell hat `light_exposure` als Literal ('none', 'minimal', 'indirect', 'direct'), aber es fehlt:
- Quantifizierung der Lichtexposition (Lux oder besser: UV-Dosis in mJ/cm2)
- UV-spezifische Degradation: THC -> CBN-Konversion unter UV-Licht, Carotinoid-Abbau in Gemuese, Chlorophyll-Bleaching
- Verpackungsempfehlung: Dunkle Glaeser, lichtdichte Beutel, opake Behaelter
- Fuer Cannabis: UV-Licht ist der Hauptfaktor fuer THC-Degradation bei Langzeitlagerung, noch vor Temperatur und Sauerstoff
**Formulierungsvorschlag:** `StorageCondition` um `max_uv_exposure_mj_cm2: Optional[float]` ergaenzen. Lagerempfehlung fuer lichtempfindliche Produkte explizit machen.

---

## Zu Ungenau -- Praezisierung noetig

### P-001: Haltbarkeitsprognose mit hardcodierten Artenliteralen

**Vage Anforderung:** `shelf_life_days = (species.scientific_name == 'Cannabis sativa' ? 365 : ...)` (`REQ-008_Post-Harvest.md`, AQL-Abschnitt, Zeile 488-493)
**Problem:** Die Haltbarkeit wird als statische Zuordnung zum wissenschaftlichen Namen modelliert. Das ist aus mehreren Gruenden ungenau:
1. Die Haltbarkeit haengt massgeblich von den *tatsaechlichen* Lagerbedingungen ab, nicht nur von der Art
2. Cannabis bei optimaler Lagerung (dunkel, 15-18 Grad C, 58-62% RH, Stickstofffuellung) haelt 1-2 Jahre; bei suboptimaler Lagerung (Licht, Waerme) nur 3-6 Monate
3. Kartoffeln bei 7-10 Grad C und 85-90% RH halten 9 Monate; bei Raumtemperatur nur 2-4 Wochen
4. Der Default von 90 Tagen ist fuer getrocknete Kraeuterprodukte zu kurz (12+ Monate moeglich) und fuer frisches Blattgemuese viel zu lang
**Messbare Alternative:** Haltbarkeit als Funktion modellieren: `estimated_shelf_life = base_shelf_life * condition_factor(actual_temp, actual_rh, light_exposure)`. Alternativ: Haltbarkeit ueber aw-Wert + Temperatur dynamisch berechnen (Arrhenius-Kinetik fuer Qualitaetsverlust).

### P-002: Snap-Test als binaerer Readiness-Indikator unzureichend

**Vage Anforderung:** "snap_test_ready = progress >= 70" (`REQ-008_Post-Harvest.md`, Python-Code, Zeile 577)
**Problem:** Der Snap-Test wird hier am Gewichtsverlust-Fortschritt festgemacht, nicht am tatsaechlichen Test-Ergebnis. 70% Fortschritt korreliert nicht zuverlaessig mit der physikalischen Eigenschaft "Zweig bricht sauber". Die Trocknungsgeschwindigkeit variiert stark mit:
- Dichte der Blueten (kompakte Indicas trocknen langsamer als lockere Sativas)
- Stammdicke (dicke Staemme halten laenger Feuchtigkeit)
- Umgebungsbedingungen (niedrigere RH = schnellere Trocknung)
- Ausgangswassergehalt (vorgetrocknete vs. frisch geerntete Pflanzen)
**Messbare Alternative:** Snap-Test als unabhaengigen booleschen Input modellieren, NICHT aus dem Gewichtsverlust ableiten. Die `perform_snap_test()`-Methode existiert bereits korrekt -- sie sollte der primaere Trigger sein, nicht `progress >= 70`.

### P-003: Schimmelrisiko-Score-Berechnung zu vereinfacht

**Vage Anforderung:** MoldPreventionMonitor.assess_mold_risk mit linearem Scoring (Zeile 906-1015)
**Problem:** Das Schimmelrisiko wird als additive Summe von Risikofaktoren modelliert. Biologisch ist das nicht korrekt:
1. **Taupunkt fehlt:** Kondenswasserbildung ist der kritischste Faktor, nicht die durchschnittliche RH. Wenn die Oberflaechentemperatur des Trocknungsguts unter den Taupunkt der Raumluft faellt, kondensiert Wasser -- selbst bei 55% RH im Raum.
2. **Expositionsdauer nicht-linear:** Schimmelwachstum folgt einer Lag-Phase (12-48h bei optimalen Bedingungen), dann exponentielles Wachstum. Ein 6h-Fenster bei 66% RH ist signifikant weniger gefaehrlich als 24h bei 63% RH.
3. **Temperatur-RH-Interaktion:** Die Kombinations-Tabelle (HIGH_RISK_COMBOS) ist zu grob. VPD waere der korrektere zusammengesetzte Parameter.
**Messbare Alternative:** VPD-basierte Risikobewertung statt isolierter Temp/RH-Schwellen. Taupunktberechnung (`dew_point = temp - ((100 - rh) / 5)` als Naeherung) als zusaetzlichen Risikofaktor. Expositionsdauer gewichtet (quadratisch statt linear).

### P-004: Zwiebel/Knoblauch-Lagerung -- UV-Exposition als Empfehlung problematisch

**Vage Anforderung:** "UV-Exposition: Foerdert Schalenhaeertung" (`REQ-008_Post-Harvest.md`, Zeile 39)
**Problem:** UV-Licht foerdert zwar die Schalenhaeertung bei Zwiebeln waehrend der Feldtrocknung (Curing), aber bei Langzeitlagerung ist Dunkelheit essentiell. Kartoffeln bilden unter Licht Solanin (korrekt erwaehnt bei Lagerhinweisen, Zeile 1172), aber auch bei Zwiebeln foerdert Licht Austrieb und Qualitaetsverlust. Die Formulierung unterscheidet nicht klar zwischen der kurzen Haertungsphase (2-3 Wochen mit Licht) und der anschliessenden Lagerung (dunkel).
**Messbare Alternative:** Phasen trennen: "Schalenhaeertung (Phase 1): 2-3 Wochen, 25-30 Grad C, niedrige RH, indirekte Sonneneinstrahlung tolerabel. Langzeitlagerung (Phase 2): dunkel, 10-15 Grad C, 60-70% RH."

### P-005: Kartoffel-Haltbarkeit ohne Keimhemmung unrealistisch

**Vage Anforderung:** `'Solanum tuberosum' ? 270` (270 Tage Haltbarkeit) (`REQ-008_Post-Harvest.md`, Zeile 491)
**Problem:** 270 Tage (9 Monate) Haltbarkeit fuer Kartoffeln ist nur mit professioneller Kuehlung (2-4 Grad C) und/oder Keimhemmungsmitteln (CIPC, Ethylen, UV-C) erreichbar. Fuer den Hobbygaertner mit Kellerlagerung (8-12 Grad C) sind 3-5 Monate realistisch, abhaengig von der Sorte (fruehe Sorten: 2-3 Monate, spaete Sorten: 5-6 Monate). Zudem ist die Temperaturangabe im Speicher-Abschnitt (10-15 Grad C fuer Kartoffeln) zu hoch -- professionelle Kartoffellagerung erfolgt bei 4-8 Grad C, Hobby-Kellerlagerung bei 6-10 Grad C.
**Messbare Alternative:** Haltbarkeit sortenabhaengig und temperaturabhaengig angeben. Mindestens zwischen Fruehkartoffeln (max. 2 Monate), mittelfruh (3-4 Monate) und spaete Lagersorten (5-8 Monate bei 4-8 Grad C) differenzieren.

---

## Hinweise & Best Practices

### H-001: Sauerstoff-Ausschluss als Lagerungsparameter

Fuer die Langzeitlagerung von Cannabis und getrockneten Kraeutern ist der Sauerstoffgehalt ein wichtiger Degradationsfaktor. Professionelle Lagerung nutzt:
- Stickstofffuellung (N2-Flush) in luftdichten Behaeltern
- Vakuum-Verschweissung
- Sauerstoffabsorber (wie bei Lebensmittel-Langzeitlagerung)

Dies fehlt im Datenmodell vollstaendig. Empfehlung: `StorageCondition` um `atmosphere_type: Literal['ambient', 'nitrogen', 'vacuum', 'modified']` ergaenzen.

### H-002: Temperatur-Logging in der Trocknungs-Kurve

Die Trocknungskurve (Gewicht ueber Zeit) ist ohne korreliertes Temperatur-Logging schwer interpretierbar. Empfehlung: In der AQL-Query fuer Trocknungs-Fortschritt (Zeile 378-449) die Temperatur- und RH-Werte als Kontext mitspeichern, um Anomalien (z.B. ploetzlicher Gewichtsverlust durch Temperaturanstieg) korrekt zu interpretieren.

### H-003: Burping-Automatisierung -- Boveda-Alternative

Das Dokument empfiehlt Boveda-Packs (62% RH) ab Woche 2 des Curings. Dies ist eine gute Praxisempfehlung, aber das System sollte auch dokumentieren:
- Boveda-Packs haben eine begrenzte Lebensdauer (2-4 Monate)
- Boveda kontrolliert RH bidirektional (absorbiert UND gibt ab)
- Alternative: Integra Boost (55%/62% Optionen)
- Keine Boveda bei frisch getrockneten Buds die noch zu feucht sind (>65% RH) -- Boveda kann dann nicht genuegend Feuchtigkeit absorbieren

### H-004: Qualitaetskontrolle -- Laboranalytik als optionale Integration

Fuer Cannabis-Post-Harvest waere eine optionale Integration mit Laboranalytik-Ergebnissen sinnvoll:
- Cannabinoid-Profil (THC, CBD, CBN, CBG)
- Terpen-Analyse (GC-MS)
- Mykotoxin-Screening
- Schwermetall-Analyse
- PSM-Rueckstandsanalytik

Dies koennte als `LabResult`-Node mit `tested_by`-Edge zu `batches` modelliert werden.

### H-005: Multi-Species-Storage-Optimizer erkennt Inkompatibilitaeten nicht zuverlaessig

Die `get_ideal_conditions`-Methode (Zeile 1124-1162) berechnet die Ueberschneidung von Temperatur- und RH-Bereichen, erkennt aber nicht korrekt, wenn es KEINE Ueberschneidung gibt. Im Testszenario 6 wird korrekt gezeigt, dass Kartoffeln (85-90% RH) und Zwiebeln (60-70% RH) einen RH-Konflikt haben. Aber der Code wuerde `optimal_rh = (85, 70)` zurueckgeben, was ein umgekehrtes Intervall ist (min > max). Dies muss als Fehler/Inkompatibilitaet erkannt und gemeldet werden.

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|--------------------|-----------|
| Temperatur (Grad C) | Ja | art- und phasenspezifisch | Hoch |
| Relative Luftfeuchte (RH%) | Ja | 45-62% (Trocknung/Curing) | Hoch |
| Gewicht (g) | Ja | Tracking ueber Zeit | Hoch |
| Wasseraktivitaet (aw) | NEIN | < 0.60 fuer Langzeitlagerung | Hoch |
| CO2-Konzentration (ppm) | NEIN | < 1500 ppm im Trocknungsraum | Mittel |
| VPD (kPa) | NEIN | nicht direkt fuer Post-Harvest, aber fuer Schimmelrisiko relevant | Mittel |
| Taupunkt (Grad C) | NEIN | Oberflaechentemp muss > Taupunkt sein | Mittel |
| Sauerstoffgehalt (%) | NEIN | < 5% fuer Langzeitlagerung (N2-Flush) | Niedrig |
| UV-Exposition | Teilweise | light_exposure als Enum, nicht quantifiziert | Niedrig |
| Ethylen (ppm) | NEIN | 0,1-1 ppm fuer Nachreife klimakterischer Fruechte | Niedrig |
| pH-Wert (Fermentation) | NEIN | < 4,6 fuer Lebensmittelsicherheit (Sauerkraut) | Mittel |
| Leitfaehigkeit Salzlake | NEIN | 2-3% NaCl = ca. 35-50 mS/cm | Niedrig |

---

## Schnittstellenanalyse mit anderen REQs

### REQ-007 (Erntemanagement) -> REQ-008 (Post-Harvest)

**Gut geloest:**
- `batches`-Collection als gemeinsame Entitaet
- `stored_in`-Edge als Uebergabe von Batch an StorageLocation
- `actual_dry_weight_g` in batches wird von REQ-008 beschrieben
- QR-Code-System durchgaengig

**Luecken:**
- Kein definierter Status-Uebergang (Batch-Status: harvested -> drying -> curing -> stored)
- `trim_waste_percent` aus REQ-007 yield_metrics wird in REQ-008 nicht weiterverwendet
- Pre-Harvest-Protokolle (Flushing, Dark Period) aus REQ-007 beeinflussen Trocknungsparameter (z.B. geflusht = weniger Chlorophyll = kuerzeres Curing), aber diese Korrelation wird nicht modelliert
- Dry-Weight-Factor aus REQ-007 (Cannabis 0.25, Tomate 0.06) muesste den `target_weight_g` in REQ-008 `DryingProgress` initialisieren -- diese Verknuepfung fehlt

### REQ-003 (Phasensteuerung) -> REQ-008 (Post-Harvest)

**Luecken:**
- Post-Harvest-Phasen (Trocknung, Curing, Lagerung) sind nicht als Phasen in REQ-003 modelliert
- Stress-Phasen in REQ-003 (z.B. "Drought-Stress fuer Terpen-Induktion") haben direkten Einfluss auf Post-Harvest-Qualitaet, aber diese Korrelation fehlt
- Saison-Vergleich (REQ-003 `seasonal_cycles`) koennte Post-Harvest-Qualitaet ueber Jahre vergleichen

### REQ-010 (IPM) -> REQ-008 (Post-Harvest)

**Kritische Luecke:**
- REQ-010 fehlt in der Abhaengigkeitsliste von REQ-008
- Karenzzeit-Validierung (`requires_harvest_delay`-Edge) muss als Gate vor Post-Harvest-Start integriert werden
- IPM-Inspektionen waehrend der Trocknungs-/Lagerphase fehlen (Lagerschaedlinge: Tabakkafer *Lasioderma serricorne*, Doerrfruchtmotte *Plodia interpunctella*, Brotkaefer *Stegobium paniceum*)
- Mold-Monitoring in REQ-008 und Krankheitsmonitoring in REQ-010 sind nicht verknuepft -- Botrytis und Aspergillus tauchen in beiden REQs auf, aber ohne gegenseitige Referenz

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL/Referenz |
|---------|--------|-----|
| Wasseraktivitaet | METER Group (ehem. Decagon) | metergroup.com |
| Cannabis Post-Harvest | University of Guelph, Dept. of Plant Agriculture | uoguelph.ca |
| Mykotoxine | BfR (Bundesinstitut fuer Risikobewertung) | bfr.bund.de |
| Lagerschaedlinge | JKI (Julius Kuehn-Institut) | julius-kuehn.de |
| Fermentation | Sandor Katz, "The Art of Fermentation" | ISBN 978-1603582865 |
| Cannabis Trocknung/Curing | Ed Rosenthal, "Marijuana Harvest" | ISBN 978-1936807253 |
| Lagerung pflanzlicher Produkte | KTBL (Kuratorium fuer Technik und Bauwesen in der Landwirtschaft) | ktbl.de |
| Ethylen-Management | UC Davis Postharvest Technology Center | postharvest.ucdavis.edu |
| Schimmelpilz-Taxonomie | MycoBank | mycobank.org |

---

## Glossar

- **aw (Wasseraktivitaet):** Mass fuer das verfuegbare ("freie") Wasser in einem Produkt, Skala 0.0-1.0. Entscheidend fuer mikrobiologische Sicherheit -- Schimmelpilze benoetigen aw > 0.65.
- **Burping:** Kontrolliertes Lueften von verschlossenen Glasbehaeltern waehrend des Cannabis-Curings, um ueberschuessige Feuchtigkeit und Gase abzufuehren.
- **Curing:** Veredelungsprozess nach der Trocknung, bei dem kontrollierte Bedingungen den Abbau von Chlorophyll und die Entwicklung von Terpenen foerdern.
- **Klimakterisch:** Fruchttyp, der nach der Ernte weiterreift (Tomate, Banane, Apfel) -- im Gegensatz zu nicht-klimakterischen Fruechten (Erdbeere, Gurke, Zitrus).
- **Mykotoxin:** Giftige Stoffwechselprodukte von Schimmelpilzen (z.B. Aflatoxine von *Aspergillus flavus*), die auch nach Abtoeeten des Pilzes im Produkt verbleiben.
- **Snap-Test:** Haptischer Trocknungstest fuer Cannabis -- ein Zweig wird gebogen. "Bricht sauber" = optimal trocken, "biegt sich" = zu feucht, "splittert" = zu trocken.
- **Taupunkt:** Temperatur, bei der die Luft ihre maximale Saettigung erreicht und Wasserdampf kondensiert. Kritisch fuer Kondenswasserbildung auf Trocknungsgut.
- **VPD (Vapor Pressure Deficit):** Dampfdruckdefizit in kPa -- beschreibt die "Verdunstungskraft" der Luft. Abhaengig von Temperatur und Luftfeuchtigkeit.
