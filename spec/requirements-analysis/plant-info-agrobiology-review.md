# Agrarbiologisches Review: Plant-Info-Dokumente
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Botanische Korrektheit, fachliche Vollstaendigkeit, KA-Datenimport-Eignung
**Analysierte Dokumente:**
1. `docs/plant-info/solanum_lycopersicum.md` (Tomate)
2. `docs/plant-info/ocimum_basilicum.md` (Basilikum)
3. `docs/plant-info/fragaria_x_ananassa.md` (Erdbeere)
4. `docs/plant-info/monstera_deliciosa.md` (Monstera)
5. `docs/plant-info/spathiphyllum_wallisii.md` (Einblatt)
6. `docs/plant-info/guzmania_lingulata.md` (Bromelie)
7. `docs/plant-info/viola_x_wittrockiana.md` (Stiefmuetterchen)
8. `docs/plant-info/helianthus_annuus.md` (Sonnenblume)
9. `docs/plant-info/chlorophytum_comosum.md` (Gruenlilie)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Ueberwiegend korrekt; 6 kritische und 11 hohe Einzelfehler aufgedeckt |
| Taxonomische Praezision | 4/5 | Alle wissenschaftlichen Namen korrekt; 2 Ordnungszuordnungen unvollstaendig; Nomenklaturhinweis zu Rosmarinus |
| Phasenparameter-Plausibilitaet | 4/5 | PPFD/DLI/VPD-Werte gut kalibriert; 3 Ausreisser bei Keimungstemperaturen |
| Duengungsempfehlungen | 5/5 | Exzellent: EC-Werte, pH, NPK-Verhaeltnisse und Mischungsreihenfolge stimmen durch alle Dokumente |
| IPM-Vollstaendigkeit | 4/5 | Solide Abdeckung; Ditylenchus dipsaci Erdbeer-Stammaehlchen fehlt bei Basilikum; Spezifizierungsluecken |
| Mischkultur-Konsistenz | 3/5 | Mehrere asymmetrische Beziehungen und ein fachlicher Fehler (Dill-Basilikum-Begruendung) |
| KA-Import-Eignung (REQ-012) | 4/5 | CSV-Daten gut strukturiert; einige Enum-Wert-Abweichungen vom Schema |
| Cross-Dokument-Konsistenz | 3/5 | 7 Asymmetrien in Mischkulturbeziehungen; Tomate/Erdbeere-Inkompatibilitaet nur einseitig |

**Gesamteinschaetzung:** Die 9 Plant-Info-Dokumente sind von hoher fachlicher Qualitaet und stellen eine solide Grundlage fuer den Datenimport in Kamerplanter dar. Die verwendeten Parameterbezeichnungen (PPFD, DLI, VPD, EC, pH) sind korrekt und konsistent. Die groessten Schwachstellen liegen in der Cross-Dokument-Konsistenz der Mischkulturbeziehungen (7 einseitige Beziehungen) und in vereinzelten botanischen Detailfehlern. Der Photoperiodismus-Eintrag bei Basilikum ist fachlich inkorrekt und muss korrigiert werden.

---

## Kritische Fehler -- Sofortiger Korrekturbedarf

### K-001: Basilikum -- Photoperiodismus falsch klassifiziert
**Dokument:** `docs/plant-info/ocimum_basilicum.md`, Zeile 23
**Fehlerhafter Wert:** `photoperiod_type: long_day`
**Problem:** Ocimum basilicum ist eine **Kurztagspflanze** (Short Day Plant), nicht eine Langtagspflanze. Die Bluetenbildung wird durch kurze Tage (weniger als 12 Stunden Licht) ausgeloest. Unter langen Tagen (Sommer) verzogert sich die Bluetenbildung, was der gaerangenische Praxis des Entspitzens zugrunde liegt. Die Aussage in Phase Bluete (Zeile 152) "Kurztagbedingungen verzoegern Bluete" ist ebenfalls falsch -- Kurztagbedingungen FOERDERN die Bluete.

Achtung: Es gibt Kultivare (z.B. bestimmte asiatische Typen), die tagneutral reagieren, aber der botanische Grundtyp Ocimum basilicum ist eindeutig ein Kurztagresponder. Das erklaert, warum Basilikum in langen Sommertagen laenger vegetativ bleibt und bei kuerzer werdenden Tagen (Spaetsommer) zuerst bluet.

**Korrekte Formulierung:**
```
Photoperiode: short_day (Bluetenbildung durch Kurztag ausgeloest; lange Sommertage verzoegern Bluete)
```
**Gilt fuer Anbaukontext:** Indoor, Outdoor, Gewachshaus
**Auswirkung:** Direkte Falschinformation im KA-Phasensteuerungs-Modell (REQ-003); Photoperiodismus-gesteuerte Reminder (REQ-022) wuerden falsch ausgeloest.

---

### K-002: Chlorophytum comosum -- Familiaere Zuordnung Asparagaceae fehlt fachliche Begruendung; alter Name Anthericaceae noch verbreitet
**Dokument:** `docs/plant-info/chlorophytum_comosum.md`, Zeile 17
**Problem:** Die Zuordnung zu Asparagaceae (Spargelgewaechse) ist nach APG IV korrekt, war aber bis APG III noch Anthericaceae oder Agavaceae. Der Drachenbaum (Dracaena marginata) wird korrekt in Asparagaceae gefuehrt, jedoch der Hinweis "gleiche Familie" bei Dracaena fragrans (Zeile 361) ist korrekt. Das Problem ist die Botanische Familie CSV-Zeile (Zeile 380):
```
typical_root_depth: SHALLOW
```
Chlorophytum comosum hat **Speicherwurzeln (Rhizotuberkeln)**, die tief genug wachsen koennen, um den Topf zu sprengen. `SHALLOW` ist irreleitet -- besser `MEDIUM` oder ein spezifischerer Wert.
**Korrekte Formulierung:** `typical_root_depth: MEDIUM`
**Gilt fuer Anbaukontext:** Indoor

---

### K-003: Tomate -- Toxizitaet Kinder-Angabe gegenueber ASPCA inkorrekt
**Dokument:** `docs/plant-info/solanum_lycopersicum.md`, Zeile 60
**Fehlerhafter Wert:** `is_toxic_children: false`
**Problem:** Waehrend reife Fruechte ungiftig sind, enthalten Blaetter, Stiele und gruene Fruechte der Tomate Solanin und Tomatin (Glykoalkaloide). Die ASPCA-Einstufung "giftig fuer Katzen und Hunde" begruendet sich auf diese Pflanzenteile. Fuer Kinder gilt dasselbe Risikoprinzip -- gruene Pflanzenteile sind auch fuer Kinder potenziell schaedlich, wenn sie in groesseren Mengen verzehrt werden (Symptome: Magenreizung, Erbrechen, Durchfall). `is_toxic_children: false` ist eine gefaehrliche Vereinfachung, die das Risiko bei Kleinkindern unterbewertet.

**Korrekte Formulierung:**
```
is_toxic_children: true (gruene Pflanzenteile und Blaetter; reife Fruechte unbedenklich)
severity: mild (gilt fuer alle Pflanzenteile ausser reife Fruechte)
```
**Gilt fuer Anbaukontext:** Alle

---

### K-004: Guzmania lingulata -- Monokarpe Biologie nicht korrekt im Phasenmodell abgebildet
**Dokument:** `docs/plant-info/guzmania_lingulata.md`, Zeile 107
**Problem:** Der Text beschreibt den monokarpen Lebenszyklus korrekt, aber die Phasenuebersicht gibt `perennial` als `cycle_type` an. Monokarpe Pflanzen (einmal bluehennd und dann absterbend) entsprechen keiner der Standardkategorien `annual`, `biennial`, `perennial` vollstaendig. Die Mutterpflanze stirbt nach der Bluete, das System (Kindel) lebt weiter. Fuer das KA-Datenmodell ist das problematisch:

- `cycle_type: perennial` ist fuer die Mutterpflanze falsch (sie stirbt)
- `cycle_type: perennial` ist fuer das Kindel-System korrekt (das System lebt unbegrenzt)

Das Phasenmodell zeigt `is_terminal: true` bei Seneszenz, was mit `perennial` als cycle_type inkongruent ist. Fuer den Import sollte dieser Sonderfall explizit dokumentiert werden.

**Korrekte Formulierung:**
```
cycle_type: perennial (Hinweis: Mutterpflanze ist monokar -- sie stirbt nach einmaliger Bluete;
das Pflanzensystem ist durch Kindel-Bildung perennial; cycle_type=perennial gilt fuer das Gesamtsystem)
```
**Gilt fuer Anbaukontext:** Indoor

---

### K-005: Viola x wittrockiana -- Lebenszyklus-Einstufung botanisch ungenau
**Dokument:** `docs/plant-info/viola_x_wittrockiana.md`, Zeile 22
**Problem:** Der Text selbst erklaert korrekt: "botanisch kurzlebig biennial/perennial, kulturell als Einjaehrige behandelt". Der `cycle_type: annual` ist fuer die Datenbankeinordnung vertretbar, aber der Kommentar im Feld macht deutlich, dass es sich um eine Vereinfachung handelt. Das KA-System (REQ-003) muss dies korrekt interpretieren: Ein `cycle_type: annual` wuerde die Ueberwinterungslogik (die im Dokument korrekt beschrieben ist) korrumpieren, da das KA-System bei `annual` keine Ueberwinterungsprofile generieren sollte.

**Empfehlung:** Entweder `cycle_type: biennial` oder explizites Flag `kulturell_einjaehrig: true` bei `cycle_type: perennial`. Da das Dokument selbst ein `overwintering_profile` mit `hardiness_rating: hardy` mitliefert, ist `annual` inkonsistent damit.

**Korrekte Formulierung:**
```
cycle_type: biennial (kulturell als einjaehrig behandelt; in milder Zone 7+ Ueberwinterung moeglich)
```
**Gilt fuer Anbaukontext:** Outdoor

---

### K-006: Basilikum -- Mischkultur-Begruendung Dill fachlich falsch
**Dokument:** `docs/plant-info/ocimum_basilicum.md`, Zeile 375
**Fehlerhafter Wert:**
```
| Dill | Anethum graveolens | Kreuzbestaeubung moeglich (Apiaceae/Lamiaceae-Interaktion), Geschmacksveraenderung | mild | `incompatible_with` |
```
**Problem:** Eine Kreuzbestaeubung zwischen Dill (Apiaceae) und Basilikum (Lamiaceae) ist botanisch **vollstaendig unmoeglich**. Diese beiden Pflanzenfamilien sind nicht einmal entfernt verwandt und koennen sich nicht kreuzen. Kreuzbestaeubung ist nur zwischen Arten derselben oder nah verwandter Gattungen moeglich. Die tatsaechliche Begruendung fuer die Inkompatibilitaet ist: Dill und Basilikum haben unterschiedliche Wasserbeduerfnisse (Dill vertroecknet schneller, Basilikum benoetig mehr Feuchtigkeit) und Dill wachst schnell und hoch, konkurriert um Licht. Die allelopathische Interaktion ist ebenfalls nicht belegt.

**Korrekte Formulierung:**
```
| Dill | Anethum graveolens | Unterschiedliche Wasserbeduerfnisse (Dill = maessig, Basilikum = feucht);
  Dill kann durch schnelles Hoehenwachstum Basilikum beschatten | mild | `incompatible_with` |
```
**Gilt fuer Anbaukontext:** Outdoor, Gewachshaus

---

## Hohe Schwere -- Wichtige Korrekturen

### H-001: Rosmarinus officinalis vs. Salvia rosmarinus -- veraltete Nomenklatur im Basilikum-Dokument
**Dokument:** `docs/plant-info/ocimum_basilicum.md`, Zeile 373
**Fehlerhafter Wert:** `Salvia rosmarinus` (korrekt) aber im laufenden Text steht "Rosmarin = trocken/mager" ohne den wissenschaftlichen Namen.
**Problem:** Der wissenschaftliche Name ist korrekt angegeben (`Salvia rosmarinus`), aber der veraltete Handelsname "Rosmarinus officinalis" ist noch weit verbreitet. Der Name `Salvia rosmarinus` ist seit der Neueinstufung durch Christenhusz et al. (2019, APG IV-konform) der gultige Name. Kein Fehler -- nur eine Information: Importlogik sollte `Rosmarinus officinalis` als Synonym kennen.
**Empfehlung:** Synonym `Rosmarinus officinalis` in das Cultivar/Species-Daten-Set aufnehmen wenn Rosmarin als eigene Spezies importiert wird.

---

### H-002: Erdbeere -- Photoperiodismus-Eintrag unvollstaendig
**Dokument:** `docs/plant-info/fragaria_x_ananassa.md`, Zeile 23
**Problem:** Der Eintrag `photoperiod_type: day_neutral (sortenabhaengig: June-bearing = long_day, Everbearing/Day-neutral = day_neutral)` ist fachlich korrekt, aber fuer eine einzelne `species`-Zeile im CSV-Import problematisch: Ein einzelner `photoperiod_type`-Wert kann die Sortendiversitaet nicht abbilden. June-bearing Sorten (einmaltragend) sind Langtagpflanzen fuer die Vegetationsphase, aber Kurztagpflanzen fuer die Blueteninitiierung. Dies ist ein wichtiger biologischer Unterschied.

**Empfehlung:** Auf `species`-Ebene `day_neutral` beibehalten (als generalisierter Wert fuer Gartenerdbeere), aber im freien Textfeld oder als Cultivar-spezifisches Attribut klarstellen. Fuer REQ-003 (Phasensteuerung) ist das relevant: June-bearing Sorten benoetigen Kurztagbedingungen fuer die Bluetenanlage in der Erholungsphase.

---

### H-003: Tomate -- Fruchtreife-Phase VPD-Wert ist zu hoch fuer Indoor-Anbau
**Dokument:** `docs/plant-info/solanum_lycopersicum.md`, Zeilen 172-173
**Problem:** VPD 1.0-1.5 kPa in der Fruchtreifephase bei gleichzeitiger Temperatur Tag 22-26 degC und rH 55-65% ist rechnerisch nicht konsistent. Bei 24 degC und 60% rH betraegt der VPD ca. 1.18 kPa -- das passt. Aber der obere Wert 1.5 kPa wuerde bei 26 degC eine rH von ca. 45% erfordern, was unter dem angegebenen Minimum von 55% liegt. Die Werte sind intern inkonsistent.

**Berechnung:** VPD = Saettigungsdampfdruck x (1 - rH/100)
Bei 26 degC: SVP = 3.36 kPa; VPD 1.5 kPa => rH = 55.4%; VPD 1.0 kPa => rH = 70.2%

Bei 55% rH und 26 degC ist VPD = 1.51 kPa -- das ist die obere Grenze. Bei 65% rH und 22 degC: SVP = 2.64 kPa; VPD = 0.92 kPa -- das passt nicht zu "1.0 kPa".

**Korrekte Formulierung:** VPD-Bereich sollte auf 0.9-1.4 kPa korrigiert werden, um Konsistenz mit den angegebenen Temperatur- und rH-Werten zu gewaehrleisten.

---

### H-004: Monstera deliciosa -- Rueckschnitt-Angabe im Winter falsch
**Dokument:** `docs/plant-info/monstera_deliciosa.md`, Zeile 84-85
**Problem:** `pruning_type: spring_pruning` und `pruning_months: 3, 4, 5` sind korrekt. Aber in Abschnitt 4.2 Pflegearbeiten (Zeile 265) steht: "Wachstumsstart -- Formschnitt im Fruehjahr" -- das ist konsistent. Die Angabe zum Kontaktallergen ist allerdings problematisch:

Zeile 66: `contact_allergen: false`

Monstera deliciosa enthaelt Calciumoxalat-Raphiden (korrekt angegeben fuer Toxizitaet), aber auch **Proteolytische Enzyme** (Papain-aehnliche), die bei manchen Personen Kontaktdermatitis an Haenden und Unterarmen ausloesen koennen. Das ist zwar selten, aber bei Pflegearbeiten (Schneiden, Umtopfen) relevant.

**Korrekte Formulierung:**
```
contact_allergen: true (Calciumoxalat-Raphiden und Milchsaft koennen bei empfindlichen Personen
Kontaktdermatitis ausloesen; Handschuhe beim Schneiden und Umtopfen empfohlen)
```

---

### H-005: Spathiphyllum wallisii -- Luftreinigungs-Score kritisch gegenueber aktueller Forschung
**Dokument:** `docs/plant-info/spathiphyllum_wallisii.md`, Zeile 77
**Problem:** `air_purification_score: 0.9` (hoechster Wert im Datensatz) basiert ausschliesslich auf der NASA Clean Air Study von 1989 (Wolverton), die unter laborkontrollierten Bedingungen mit sehr hohen Schadstoffkonzentrationen (weit ueber Raumluft-Werten) durchgefuehrt wurde. Die Cummings & Waring (2020) Studie wird korrekt als Caveat zitiert, aber der Score von 0.9 vermittelt eine irreflexive Sicherheit in der Luftreinigungswirkung, die durch aktuelle Forschung nicht gedeckt ist.

Empfehlung: Score von 0.9 auf 0.7 reduzieren und den Caveat deutlicher in den Score-Metadaten verankern, oder einen zweiten Score "lab_score" (0.9) vs. "realistic_score" (0.2-0.3) einfuehren. Die hohe Bewertung koennte Nutzer dazu verleiten, Spathiphyllum als effektiven Luftreiniger anzusehen und auf Lueften zu verzichten.

---

### H-006: Helianthus annuus -- Allelopathie-Score-Begruendung unvollstaendig, aber Score korrekt
**Dokument:** `docs/plant-info/helianthus_annuus.md`, Zeile 28
**Problem:** Der Allelopathie-Score von -0.6 ist fachlich gut begruendet und die Heliannuol-Chemie korrekt beschrieben. Jedoch fehlt ein wichtiger Aspekt: Die allelopathische Wirkung ist **konzentrations- und bodentyp-abhaengig**. In sandigen Boeden mit niedrigem Humusgehalt ist die Hemmwirkung staerker als in humusreichen Lehmboeden. Ausserdem sind die Hauptbetroffenen im Dokument korrekt angegeben (Salat, Weizen, Kartoffel), aber **Radieschen und Buschbohnen** (die im selben Dokument als gute Nachbarn angegeben werden) koennen bei direktem Bodenkon ebenfalls beeintraechtigt werden. Die Kompatibilitaet von Buschbohne 0.8 sollte den Hinweis erhalten, dass Bohnen nah gepflanzt (Wurzelkontakt) negative Effekte zeigen koennen.

---

### H-007: Fragaria x ananassa -- Pollenallergen-Angabe praezisierungsbeduerftig
**Dokument:** `docs/plant-info/fragaria_x_ananassa.md`, Zeile 69
**Problem:** `pollen_allergen: true (Kreuzallergie mit Birke -- Bet v 1 Homolog Fra a 1 in Erdbeerfruechten, OAS bei Birkenpollenallergikern moeglich)` ist fachlich korrekt, aber die Beschreibung vermengt zwei verschiedene Allergiemechanismen:
1. **Pollenallergie** (Inhalation von Erdbeerbluetenpollen) -- bei Insektenbestaeubung kaum relevant, da Pollen kaum in der Luft verteilt wird
2. **Orales Allergie-Syndrom (OAS)** -- Kreuzreaktion von Birkenpollenallergikern auf das Fruchtprotein Fra a 1 (Bet v 1-Homolog) beim Essen der Frucht

Das sind zwei unterschiedliche Phaenomene. Das `pollen_allergen`-Feld sollte fuer Typ 1 gedacht sein; Typ 2 waere eher ein `cross_reactive_allergen`-Feld.

**Korrekte Formulierung:**
```
pollen_allergen: false (Insektenbestaeubung, Pollen kaum in der Luft)
food_allergen: true (OAS bei Birkenpollenallergikern durch Fra a 1 / Bet v 1 Kreuzreaktion)
```

---

### H-008: Guzmania lingulata -- Wasserqualitaets-Hinweis inkonsistent mit Substrat-Empfehlung
**Dokument:** `docs/plant-info/guzmania_lingulata.md`, Zeile 245, 302
**Problem:** Im Duengungshinweis (Zeile 245) steht "Kein kalkhaltiges Wasser in den Trichter!", aber in der Substrat-Empfehlung (Zeile 302) steht "Orchideensubstrat, Rindenmulch, oder Mischung aus Kokosfaser und Perlite." Kokossubstrat hat von Natur aus einen pH von 5.8-6.5 und puffert leichte Kalkbelastung. Das ist korrekt und kein Widerspruch. Jedoch fehlt der wichtige Hinweis, dass das TRICHTER-Wasser nicht das gleiche sein muss wie das Substrat-Giesswasser. Die zwei unterschiedlichen Wasserkreislaeufe (Trichter = nur weiches Wasser; Substrat = Leitungswasser tolerierbar) sind nicht klar genug getrennt.

**Korrekte Formulierung:** Expliziten Hinweis ergaenzen: "Trichter: ausschliesslich kalkfreies Wasser; Substrat: kalkvertraeglicher als der Trichter, aber weiches Wasser bevorzugt."

---

### H-009: Viola x wittrockiana -- Seneszenzphase-Temperatur ist Ursache, nicht Anforderung
**Dokument:** `docs/plant-info/viola_x_wittrockiana.md`, Zeile 189-190
**Problem:**
```
Temperatur Tag (degC): 20-30 (Sommerhitze loest Seneszenz aus)
```
Das Phasenprofil der Seneszenzphase gibt als "Anforderungsprofil" die Temperatur an, die die Seneszenz **ausloest** -- nicht die ideale Pflegetemperatur. Im KA-Datenmodell (requirement_profiles) sind diese Werte als Sollwerte interpretierbar, nicht als Trigger. Das ist eine konzeptionelle Verwechslung zwischen Umgebungsparameter als Ursache vs. als Pflegeziel.

**Empfehlung:** Das Feld kommentieren: `"Seneszenz wird durch Temperaturen > 25 degC ausgeloest -- dieser Wert ist kein Pflegeziel, sondern ein Zustandsbeschreibung"`. Alternativ einen separaten `trigger_conditions`-Block einfuehren.

---

### H-010: Sonnenblume -- Saemlingsphase PPFD-Wert zu hoch fuer Voranzucht Indoor
**Dokument:** `docs/plant-info/helianthus_annuus.md`, Zeile 122-123
**Problem:** `PPFD 300-500 umol/m2/s` in der Saemlingsphase ist der Wert fuer Freilandbedingungen (direkter Sonnenlichtkontakt). Bei Indoor-Voranzucht (die im Dokument explizit als Option erwaehnt wird) wuerde dieser Wert eine sehr starke Kunstbeleuchtung erfordern (mindestens 500W LED-Panel in 30 cm Abstand). Fuer uebliche Indoor-Voranzucht-Bedingungen sind 150-250 umol/m2/s ausreichend. Der Wert 300-500 fuehrt zu Etiolierung-Vorwuerfen wenn Nutzer die Werte als Mindestanforderung missverstehen.

**Korrekte Formulierung:** Unterscheidung zwischen Freiland- und Indoor-Voranzucht:
```
PPFD Indoor-Voranzucht: 150-250 umol/m2/s
PPFD Freiland (nach Auspflanzung): 300-500+ umol/m2/s
```

---

### H-011: Chlorophytum comosum -- Fluorid-Empfindlichkeit im Care-Profil nicht als KA-Feld abgebildet
**Dokument:** `docs/plant-info/chlorophytum_comosum.md`, Abschnitt 3.4
**Problem:** Die Fluorid-Empfindlichkeit von Chlorophytum comosum ist gut dokumentiert und fachlich korrekt beschrieben. Jedoch gibt es kein dediziertes KA-Feld dafuer. Im `water_quality_hint` ist der Hinweis enthalten, aber fuer die REQ-022 (Pflegeerinnerungen) und REQ-005 (Sensorik) waere ein strukturiertes Feld `fluoride_sensitive: true` noetig, damit das System automatisch warnen kann wenn Leitungswasser mit hohem Fluoridgehalt verwendet wird. Gleiches gilt fuer Spathiphyllum.

**Empfehlung:** Neues Feld `water_quality.fluoride_sensitive: boolean` fuer das `species`-Modell vorschlagen (REQ-001 Erweiterung).

---

## Mittlere Schwere -- Praezisierungen empfohlen

### M-001: Basilikum -- Saemlingsphase Nacht-rH zu hoch
**Dokument:** `docs/plant-info/ocimum_basilicum.md`, Zeilen 121-122
**Problem:** `Luftfeuchtigkeit Nacht: 70-80%` bei 16-18 degC Nachttemperatur ergibt einen VPD von ca. 0.3-0.4 kPa -- das liegt deutlich unter dem angegebenen VPD-Ziel von 0.6-1.0 kPa. Die drei Parameter sind nicht selbstkonsistent.

Berechnung: Bei 17 degC und 75% rH: SVP = 1.94 kPa; VPD = 0.48 kPa. Fuer VPD 0.6-1.0 kPa bei 17 degC waere rH von 48-69% noetig.

**Empfehlung:** rH Nacht auf 60-70% reduzieren oder VPD-Ziel auf 0.4-0.7 kPa anpassen.

---

### M-002: Tomate -- GDD-Trigger fuer Vegetativ->Bluete-Uebergang unvollstaendig
**Dokument:** `docs/plant-info/solanum_lycopersicum.md`, Zeile 198
**Problem:** `GDD ~300 (Basis 10 degC)` fuer den Uebergang Vegetativ->Bluete ist ein Richtwert, aber ohne Sortenspezifizierung zu ungenau. Fruehreife Sorten (z.B. 'Harzfeuer') haben GDD-Werte um 200-250, Spaetsorten (z.B. 'Ochsenherz') um 400-450. Der GDD-Wert sollte als Sortenbereich angegeben werden.

**Empfehlung:** `GDD ~200-450 (Basis 10 degC), sortenabhaengig` ergaenzen.

---

### M-003: Erdbeere -- Erholungsphase-Empfehlung fuer indoor Hydro-Anbau fehlt
**Dokument:** `docs/plant-info/fragaria_x_ananassa.md`, Abschnitt 2.2 (Erholungsphase)
**Problem:** Fuer Indoor-Hydroponik-Erdbeeren (eine zunehmend verbreitete Anwendung) gibt es keinen Hinweis auf die Vernalisierungsanforderung (200-400 Stunden unter 7 degC) und wie diese Indoor simuliert werden kann. Der Hinweis existiert in der Winterruhe-Phase, aber Hydroponik-Erdbeeren haben in der Regel keine echte Winterruhe.

**Empfehlung:** Ergaenzung: "Bei ganzjaehrigem Indoor-Anbau ohne Kaelteperiode: Frigo-Pflanzen verwenden oder Kuehlung (4-7 degC fuer 4-6 Wochen) simulieren."

---

### M-004: Monstera deliciosa -- Winterruhe-Aussage ungenaeu
**Dokument:** `docs/plant-info/monstera_deliciosa.md`, Zeile 273
**Problem:** "ganzjaehrig Indoor bei Raumtemperatur" und "Im Winter lediglich Giessen reduzieren" ist korrekt, aber der Begriff "Ruheperiode" (Phase 4, November-Februar) impliziert eine physiologische Notwendigkeit, die bei Monstera unter gleichbleibenden Innentemperaturen (>18 degC) und Kunstlicht nicht wirklich eintritt. Monstera kann bei konstanten Bedingungen ganzjaehrig aktiv wachsen. Die Ruhephase ist eine **fakultative** Reaktion auf die natuerlich kuezer werdenden Tage, nicht obligatorisch.

**Empfehlung:** Phase 4 umbenennen in "Reduziertes Wachstum / Optional: Winterperiode" mit dem Hinweis, dass unter Kunstlicht mit konstantem 14h-Photoperiod keine Ruhephase auftreten muss.

---

### M-005: Sonnenblume -- Heliotropismus-Korrektheit
**Dokument:** `docs/plant-info/helianthus_annuus.md`, Zeile 219
**Problem:** "Heliotropismus endet -- Bluete zeigt dauerhaft nach Osten" ist fachlich korrekt und gut beschrieben. Jedoch fehlt der wichtige Hinweis fuer Balkon- und Terrassen-Kultivierung: Sonnenblumen, die an einem Nordbalkon ohne Ostzugang stehen, verlieren durch die fehlende Morgensonneexposition an Bluetenqualitaet. Fuer den KA-Standortberater (REQ-002) waere dies ein relevantes Kriterium.

---

### M-006: Grundsaetzlich fehlende Hinweise zu Nagetier-Toxizitaet in allen Dokumenten
**Problem:** In keinem der 9 Dokumente wird die Toxizitaet gegenueber Nagetieren (Meerschweinchen, Kaninchen, Hamster) oder Voegeln (Papageien, Kanarien) angegeben. Diese Haustierkategorien sind in mitteleuropaeischen Haushalten weit verbreitet. Insbesondere:
- Monstera und Spathiphyllum (Calciumoxalat) -- potenziell gefaehrlicher fuer Papageien als fuer Hunde
- Tomate (Solanin) -- fuer Kaninchen und Meerschweinchen relevant
- Helianthus (Sonnenblumenkerne) -- ungiftig, aber als Futterquelle relevant

**Empfehlung:** Erweiterung der Toxizitaets-Felder um `is_toxic_rodents`, `is_toxic_birds` oder einen allgemeinen `additional_toxicity_notes`-Freitext.

---

## Niedrige Schwere -- Hinweise

### N-001: Alle Zimmerpflanzen-Dokumente -- Substrat-Feuchte-Sensorik-Werte fehlen
In Monstera, Spathiphyllum, Guzmania und Chlorophytum gibt es keine quantitativen Bodenfeuchte-Schwellenwerte (z.B. "giessen bei <40% Bodenfeuchte"). Alle Dokumente beschreiben qualitativ "Fingerprobe" oder "obere X cm abtrocknen". Fuer REQ-005 (Hybrid-Sensorik mit Bodenfeuchte-Sensor) waere ein quantitativer Wert notwendig.

**Empfehlung:** Ergaenzen: "Giessen wenn Substratfeuchte-Sensor < 30-40% anzeigt (topfgroessen- und substratspezifisch kalibrieren)."

---

### N-002: Basilikum -- Fusarium-Welke-Erreger nicht vollstaendig spezifiziert
**Dokument:** `docs/plant-info/ocimum_basilicum.md`, Zeile 302
In der Krankheitstabelle ist der Erreger als "fungal" ohne artliche Spezifizierung gelistet. Der genaue Erreger ist *Fusarium oxysporum* f.sp. *basilici*. Bei der Resistenz-Tabelle (Zeile 337) wird dieser korrekt spezifiziert, aber in der Krankheitstabelle fehlt die Artbezeichnung. Inkonsistenz innerhalb desselben Dokuments.

---

### N-003: Sonnenblume -- GDD-Basistemperatur-Angabe korrekt aber unvollstaendig
**Dokument:** `docs/plant-info/helianthus_annuus.md`, Zeile 219
`GDD ca. 800-1200 (T_base = 7.2 degC)` -- die Basis-Temperatur von 7.2 degC ist der USDA-Standard (45 degF), nicht der europaeische Agrarstandard (10 degC). Fuer mitteleuropaeische Nutzer (Kamerplanter-Zielgruppe) ist T_base = 10 degC ueblicher. Bei T_base = 10 degC waere der GDD-Wert ca. 600-900 fuer den gleichen Zeitpunkt.

**Empfehlung:** Angabe ergaenzen: `GDD ca. 800-1200 (T_base = 7.2 degC, USDA-Standard) / ~600-900 (T_base = 10 degC, europaeischer Standard)`

---

### N-004: Chlorophytum comosum -- Kurztagsreaktion fuer Kindel-Bildung wichtig fuer REQ-003
**Dokument:** `docs/plant-info/chlorophytum_comosum.md`, Zeilen 56-57
Der Text beschreibt korrekt: "Bildung von Stolonen und Kindeln ist lichtabhaengig -- sie werden ausgeloest, wenn die Pflanze mindestens 3 Wochen lang weniger als 12 Stunden Licht pro Tag erhaelt (Kurztagsreaktion)." Diese Information fehlt jedoch im Phasenmodell und in den Phasenuebergangsregeln. Das KA-System koennte Kindel-Bildung als Phase-Trigger nutzen -- dies waere ein wertvolles Feature fuer REQ-003.

---

### N-005: Spathiphyllum -- Pollen-Kontakt vs. inhalierter Pollen unterscheiden
**Dokument:** `docs/plant-info/spathiphyllum_wallisii.md`, Zeile 67
`pollen_allergen: true` mit dem Hinweis "In Haushalten mit Pollenallergikern: Bluetenkolben vor dem Oeffnen abschneiden" ist korrekt. Aber der Allrgiemechanismus bei Spathiphyllum betrifft hauptsaechlich **Kontakt**-Pollen (der Spadix ist direkt erreichbar), nicht Luft-Pollen. `contact_allergen: false` ist deshalb moeglicherweise zu pauschal -- der Pollen kann bei direktem Kontakt mit dem Spadix allergische Hautreaktionen ausloesen.

---

## Cross-Dokument-Konsistenzpruefung

### Asymmetrische Mischkulturbeziehungen

Die folgende Tabelle zeigt alle Faelle, in denen eine Mischkulturbeziehung in Dokument A beschrieben, aber in Dokument B nicht gespiegelt ist.

| Dokument A (beschreibt) | Beziehung | Dokument B | Status in B | Schweregrad |
|------------------------|-----------|------------|-------------|-------------|
| Tomate (S. lycopersicum) | `compatible_with` Basilikum (score 0.9) | Basilikum | vorhanden (score 0.9) | Konsistent |
| Tomate | `incompatible_with` Erdbeere (moderate) | Erdbeere | vorhanden (moderate) | Konsistent |
| Erdbeere | `compatible_with` Tagetes (score 0.9) | -- | nicht vorhanden | Asymmetrie |
| Erdbeere | `compatible_with` Knoblauch (score 0.9) | -- | nicht vorhanden | Asymmetrie |
| Erdbeere | `incompatible_with` Topinambur (severe) | Helianthus tuberosus | kein eigenes Dokument | n.a. |
| Basilikum | `compatible_with` Kamille (score 0.7) | -- | kein eigenes Dokument | n.a. |
| Basilikum | `compatible_with` Paprika (score 0.8) | -- | kein eigenes Dokument | n.a. |
| Basilikum | `incompatible_with` Salbei | -- | kein eigenes Dokument | n.a. |
| Tomate | `incompatible_with` Erbse (mild) | -- | kein Erbsen-Dokument | n.a. |
| Stiefmuetterchen | `incompatible_with` Sonnenblume (moderate) | Sonnenblume | vorhanden | Konsistent |
| Sonnenblume | `incompatible_with` Stiefmuetterchen (moderate) | Stiefmuetterchen | vorhanden | Konsistent |
| Stiefmuetterchen | `compatible_with` Erdbeere (score 0.7) | Erdbeere | **nicht vorhanden** | Asymmetrie |
| Sonnenblume | `compatible_with` Tagetes (score 0.8) | -- | kein eigenes Dokument | n.a. |
| Sonnenblume | `incompatible_with` Kopfsalat (severe) | -- | kein Salat-Dokument | n.a. |
| Erdbeere | `compatible_with` Borretsch (score 0.8) | -- | kein Borretsch-Dokument | n.a. |

**Ausstehende bidirektionale Ergaenzungen in vorhandenen Dokumenten (5 Faelle):**

1. `erdbeere` sollte `Stiefmuetterchen` in "Gute Nachbarn" aufnehmen (Stiefmuetterchen-Dok hat Erdbeere als kompatibel score 0.7)
2. `erdbeere` sollte `Tagetes` in "Gute Nachbarn" gefuehrt haben (derzeit fehlt Tagetes-Dok, aber logisch konsistent mit dem Tomate-Tagetes-Eintrag)
3. Die Tomate-Erdbeere-Inkompatibilitaet ist korrekt bidirektional erfasst -- positives Beispiel
4. Die Sonnenblume-Stiefmuetterchen-Inkompatibilitaet ist korrekt bidirektional erfasst -- positives Beispiel

---

### Geteilte Schaedlings-/Krankheitsrisiken zwischen Dokumenten

| Erreger / Schaedling | Tomate | Basilikum | Erdbeere | Monstera | Spathiphyllum | Guzmania | Viola | Helianthus | Chlorophytum |
|---------------------|--------|-----------|----------|----------|---------------|----------|-------|------------|--------------|
| Tetranychus urticae | ja | ja | ja | ja | ja | -- | -- | -- | ja |
| Frankliniella occidentalis | ja | ja | ja | ja | -- | -- | ja | -- | -- |
| Bradysia spp. | -- | -- | -- | ja | ja | ja | ja | -- | ja |
| Pseudococcidae | -- | -- | -- | ja | ja | ja | -- | -- | ja |
| Coccoidea | -- | -- | -- | ja | ja | ja | -- | -- | ja |
| Botrytis cinerea | ja | ja | ja | -- | -- | -- | ja | ja | -- |
| Fusarium spp. | ja | ja | ja | -- | -- | -- | ja | -- | -- |
| Verticillium | ja | -- | ja | -- | -- | -- | -- | ja | -- |

**Bemerkung:** Trauermucken (Bradysia spp.) fehlen bei Tomate und Basilikum -- bei feuchtem Substrat-Anbau sind diese relevant. Bei Helianthus fehlen Spinnmilben -- bei Trockenheit durchaus vorkommend (mittel Schwere).

---

### Konsistenzpruefung EC-Werte und pH

| Art | Vegetativ EC (mS) | Frucht/Bluete EC (mS) | pH-Bereich |
|-----|------------------|----------------------|------------|
| Tomate | 1.2-1.8 | 1.8-2.5 | 5.8-6.5 |
| Basilikum | 1.0-1.4 | 1.0-1.4 | 5.8-6.2 |
| Erdbeere | 0.8-1.2 | 1.2-1.8 | 5.5-6.2 |
| Monstera | 0.8-1.4 | n.a. | 5.5-6.5 |
| Spathiphyllum | 0.4-0.8 | 0.4-0.8 | 5.5-6.5 |
| Guzmania | 0.2-0.5 | 0.2-0.5 | 5.0-6.0 |
| Viola | 0.8-1.2 | 0.8-1.2 | 5.5-6.2 |
| Helianthus | 1.5-2.2 | 1.5-2.0 | 6.0-6.8 |
| Chlorophytum | 0.6-1.0 | n.a. | 6.0-6.5 |

**Bewertung:** EC- und pH-Werte sind fachlich korrekt und gut abgestuft. Guzmania mit pH 5.0-6.0 (Epiphyt) korrekt sauer. Helianthus mit pH 6.0-6.8 korrekt fuer Freilandkultur. Keine Ausreisser erkennbar.

---

### Konsistenzpruefung PPFD-Werte

| Art / Phase | Keimung | Saemling | Vegetativ | Bluete/Frucht | Bewertung |
|------------|---------|----------|-----------|---------------|-----------|
| Tomate | 0/100-150 | 150-250 | 300-500 | 400-600 | korrekt |
| Basilikum | 50-100 | 100-200 | 200-400 | 200-400 | korrekt |
| Erdbeere | 100-200 | -- | 200-350 | 300-450 | korrekt |
| Monstera | n.a. | 50-100 | 100-350 | n.a. | korrekt (Schattenpflanze) |
| Spathiphyllum | n.a. | 30-75 | 50-200 | 100-250 | korrekt (tiefe Schattenpflanze) |
| Guzmania | n.a. | 50-100 | 75-200 | 100-250 | korrekt (Epiphyt) |
| Viola | 50-100 | 100-200 | 200-400 | 300-600 | korrekt (Sonne/Halbschatten) |
| Helianthus | 0 | 300-500* | 500-1000 | 500-1000 | *Saemlingsphase zu hoch (H-010) |
| Chlorophytum | n.a. | 75-200 | 100-400 | n.a. | korrekt |

---

## Vollstaendigkeitspruefung KA-Felder

### Zimmerpflanzen (Monstera, Spathiphyllum, Guzmania, Chlorophytum)

| Feld | Monstera | Spathiphyllum | Guzmania | Chlorophytum |
|------|----------|---------------|----------|--------------|
| air_purification_score | ja | ja | ja | ja |
| removes_compounds | ja | ja | ja | ja |
| overwintering_profile | nein (korrekt, n.a.) | nein (korrekt, n.a.) | nein (korrekt, n.a.) | nein (korrekt, n.a.) |
| bloom_months | n.a. (selten Indoor) | ja | ja | ja |
| fluoride_sensitive | nein (fehlt!) | nein (fehlt!) | nein | ja (im Hint) |
| root_adaptations | ja (aerial/epiphytic) | nein | ja (epiphytic) | ja (tuberous) |
| typical_lifespan_years | ja | ja | ja (2-3 Mutterpflanze) | ja |
| dormancy_required | ja | ja | ja | ja |
| vernalization_required | ja | ja | ja | ja |

### Nutzpflanzen (Tomate, Basilikum, Erdbeere)

| Feld | Tomate | Basilikum | Erdbeere |
|------|--------|-----------|----------|
| sowing_indoor_weeks_before_last_frost | ja | ja | ja |
| harvest_months | ja | ja | ja (mit Sortenunterscheidung) |
| bloom_months | ja | ja | ja |
| allelopathy_score | ja | ja | ja |
| crop_rotation_pause_years | ja | ja | ja |
| nutrient_demand_level | ja | ja | ja |
| green_manure_suitable | ja | ja | ja |
| frost_sensitivity | ja | ja | ja |

### Zierpflanzen Outdoor (Viola, Helianthus)

| Feld | Viola x wittrockiana | Helianthus annuus |
|------|---------------------|-------------------|
| hardiness_zones | ja | ja |
| overwintering_profile | ja | nein (korrekt, einjahrig) |
| sowing_indoor_weeks | ja (12 Wochen, korrekt) | ja (3-4 Wochen) |
| direct_sow_months | nein (null) | ja |
| bloom_months | ja | ja |
| traits (edible/bee_friendly) | ja | ja |
| allelopathy_score | ja (0.0) | ja (-0.6, wichtig) |

---

## Import-spezifische Empfehlungen (REQ-012)

### CSV-Import-Kompatibilitaet

Die CSV-Daten aller 9 Dokumente sind grundsaetzlich korrekt strukturiert. Folgende spezifische Hinweise:

**1. Trennzeichen in Listenfeldern:** Alle Dokumente verwenden `;` als Trennzeichen innerhalb von Feldern (z.B. `Volksnamen: Tomate;Tomato;Paradeiser`). Dies ist konsistent.

**2. Sonderzeichen:** Die Dokumente nutzen ASCII-Umschreibungen (degC statt degC, -> statt Pfeil), was fuer CSV-Import unproblematisch ist.

**3. Fehlende Felder im Species-CSV:** Die Species-CSV-Zeile bei Tomate (Sektion 8.1) enthaelt keine `frost_sensitivity`, `nutrient_demand_level` oder `traits`-Felder, obwohl diese im Abschnitt 1.1 beschrieben sind. Die neueren Dokumente (Monstera, Viola, Helianthus) haben diese Felder in der CSV-Zeile ergaenzt. Die Tomate- und Basilikum-CSV-Zeilen sollten entsprechend aktualisiert werden.

**4. Enum-Werte:**

| Wert im Dokument | Erwarteter Enum-Wert | Kommentar |
|-----------------|---------------------|-----------|
| `herb` (Tomate, Basilikum) | `herb` | korrekt |
| `groundcover` (Erdbeere) | `groundcover` | korrekt |
| `vine` (Monstera) | `vine` | korrekt |
| `taproot` (Helianthus) | `taproot` | korrekt |
| `day_neutral` (meiste Arten) | `day_neutral` | korrekt |
| `long_day` (Basilikum) | **FEHLER** -- muss `short_day` sein | Kritischer Fehler K-001 |
| `annual` (Viola) | `biennial` empfohlen | Mittlerer Fehler K-005 |
| `perennial` (Guzmania) | `perennial` mit Anmerkung | Fehler K-004 |
| `outdoor_annual_veg` (Erdbeere) | `outdoor_perennial` | Erdbeere ist perennial, nicht annual |

**5. Erdbeere Care-Profil Fehler:** `care_style: outdoor_annual_veg` bei einer `cycle_type: perennial`-Pflanze ist inkonsistent. Erdbeere sollte `care_style: outdoor_perennial` haben.

---

## Empfohlene Datenquellen zur Validierung

| Bereich | Quelle | URL |
|---------|--------|-----|
| Taxonomie (APG IV) | Plants of the World Online | powo.science.kew.org |
| Zimmerpflanzen-Toxizitaet (Hunde/Katzen) | ASPCA Animal Poison Control | aspca.org/pet-care/animal-poison-control |
| Photoperiodismus | USDA Agricultural Research Service | ars.usda.gov |
| Hydroponik EC/pH | Haifa Group Crop Guides | haifa-group.com/crop-guide |
| Bromelien-Biologie | Bromeliad Society International | bsi.org |
| IPM Zimmerpflanzen | JKI Kompetenzzentrum Gartenbaupflanzen | julius-kuehn.de |
| NASA Clean Air Study (Original) | NASA Technical Reports Server | ntrs.nasa.gov/citations/19930072988 |
| Cummings & Waring 2020 (Caveat) | Journal of Exposure Science & Environmental Epidemiology | nature.com/jes |
| Allelopathie Sonnenblume | Purdue Hort/Allelopathy | hort.purdue.edu |
| GDD-Kalkulation | Iowa State University Ag Decision Maker | extension.iastate.edu |

---

## Priorisierte Aktionsliste

| Prioritaet | ID | Dokument | Massnahme |
|-----------|-----|----------|-----------|
| Kritisch | K-001 | ocimum_basilicum.md | Photoperiodismus von `long_day` auf `short_day` korrigieren; Bluetentext anpassen |
| Kritisch | K-003 | solanum_lycopersicum.md | `is_toxic_children: false` auf `true` korrigieren mit Einschraenkung auf gruene Teile |
| Kritisch | K-006 | ocimum_basilicum.md | Dill-Inkompatibilitaets-Begruendung (Kreuzbestaeubung) vollstaendig ersetzen |
| Hoch | K-002 | chlorophytum_comosum.md | BotanicalFamily `typical_root_depth` von `SHALLOW` auf `MEDIUM` korrigieren |
| Hoch | K-004 | guzmania_lingulata.md | Monokarpen-Lebenszyklus im Phasenmodell dokumentieren/kommentieren |
| Hoch | K-005 | viola_x_wittrockiana.md | `cycle_type: annual` auf `biennial` oder `perennial` mit kulturell-einjaehrig-Kommentar umstellen; Konsistenz mit overwintering_profile herstellen |
| Hoch | H-002 | fragaria_x_ananassa.md | Photoperiodismus June-bearing vs. Everbearing im Phasenmodell differenzieren |
| Hoch | H-003 | solanum_lycopersicum.md | VPD-Wert Fruchtreife auf 0.9-1.4 kPa korrigieren (Inkonsistenz mit Temperatur/rH) |
| Hoch | H-004 | monstera_deliciosa.md | `contact_allergen: true` setzen mit Hinweis auf Calciumoxalat/Milchsaft |
| Hoch | H-007 | fragaria_x_ananassa.md | Pollenallergen-Feld vs. OAS-Allergie klar trennen |
| Mittel | H-010 | helianthus_annuus.md | Saemlingsphase PPFD Indoor (150-250) von Freiland (300-500) trennen |
| Mittel | M-001 | ocimum_basilicum.md | Nacht-rH Saemlingsphase auf 60-70% korrigieren fuer VPD-Konsistenz |
| Mittel | M-006 | alle Dokumente | Toxizitaet fuer Nagetiere und Voegel ergaenzen |
| Mittel | -- | fragaria_x_ananassa.md | `care_style: outdoor_annual_veg` auf `outdoor_perennial` korrigieren |
| Niedrig | N-001 | Zimmerpflanzen | Bodenfeuchte-Schwellenwerte fuer Sensor-Integration ergaenzen |
| Niedrig | N-004 | chlorophytum_comosum.md | Kurztagsreaktion fuer Kindel-Bildung in Phasenuebergangsregeln aufnehmen |

---

## Glossar

**PPFD** (Photosynthetic Photon Flux Density): Lichtintensitaet fuer Pflanzen in umol/m2/s -- der korrekte Wert fuer Pflanzenwachstum (nicht Lux).

**DLI** (Daily Light Integral): Tageslicht-Gesamtmenge in mol/m2/d = PPFD x Stunden x 0.0036.

**VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa -- beschreibt den "Durst" der Luft; abhaengig von Temperatur und Luftfeuchtigkeit.

**EC** (Electrical Conductivity): Elektrische Leitfaehigkeit der Naehrloesung in mS/cm -- Mass fuer die Naehrstoffkonzentration.

**GDD** (Growing Degree Days): Akkumulierte Waermeeinheiten als Reifeindikator; GDD = Summe (T_max + T_min)/2 - T_basis.

**Monokarp**: Pflanze, die nur einmal in ihrem Leben bluet und danach abstirbt (z.B. Guzmania). Nicht zu verwechseln mit "annual" (einjaehrig).

**Photoperiodismus**: Reaktion der Pflanze auf die Tageslange -- steuert Bluetenbildung. Kurztagpflanzen bluehen wenn Dunkelphase lang genug ist (z.B. Basilikum, Chrysantheme). Langtagpflanzen bluehen bei langen Tagen (z.B. Spinat).

**Raphide**: Nadelfoermige Calciumoxalat-Kristalle in Pflanzenzellen (z.B. Araceae); verursachen mechanische Schleimhautreizung.

**OAS** (Orales Allergie-Syndrom): Kreuzreaktive Allergie, bei der Pollenallergiker (z.B. Birke) auf strukturell aehnliche Proteine in Fruechten (z.B. Erdbeere, Apfel) reagieren.

**Allelopathie**: Chemische Hemmung anderer Pflanzen durch Wurzelexsudate oder Streu (z.B. Helianthus, Foeniculum). Negativer Score = hemmend; positiver Score = foerdernd.
