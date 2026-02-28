# Agrarbiologisches Anforderungsreview: REQ-026 Aquaponik-Management

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Aquaponik, Fisch-Pflanzen-Kreislaufsysteme, Wasserchemie
**Analysiertes Dokument:** `spec/req/REQ-026_Aquaponik-Management.md` (Version 1.0)
**Status:** Alle Findings eingearbeitet (2026-02-27)

**Zusammenfassung der eingearbeiteten Korrekturen:**
- **F-001:** Zurückgezogen (Formel korrekt)
- **F-002 bis F-004:** [BEHOBEN] Testvektoren korrigiert (Emerson-Formel konsistent)
- **F-005:** [BEHOBEN] Karpfen/Koi Taxonomie-Hinweis präzisiert (C. rubrofuscus)
- **F-006:** [BEHOBEN] Forelle lethal_low_c auf -0.5 geändert + Hinweis
- **F-007:** [BEHOBEN] Silurus glanis → temperate (20-26°C)
- **F-008:** [BEHOBEN] TAN-Formel: Futter × Protein% × 0.092 + DEFAULT_PROTEIN_BY_FEED_TYPE
- **F-009:** [BEHOBEN] Chlor/Chloramin differenziert + REQ-014 Querverw.
- **F-010:** [BEHOBEN] Goldfisch 10 kg/1000L + Hinweis bis 15 kg
- **F-011:** [BEHOBEN] Goldfisch FCR → null (Zierfisch)
- **U-001:** [BEHOBEN] Zn in Tabelle + ZnSO4 als SupplementType
- **U-002:** [BEHOBEN] Cu in Nährstoffdefizit-Tabelle
- **U-003:** [BEHOBEN] Bor in Tabelle mit Toxizitätswarnung
- **U-004:** [BEHOBEN] GH in evaluate_water_quality (<4°dH, >20°dH)
- **U-005:** [BEHOBEN] DO-Sättigung + calculate_do_saturation Methode
- **U-006:** [BEHOBEN] Phosphat-Akkumulationswarnung >80 ppm
- **U-007:** [BEHOBEN] Temperatur-Schwellenstufen (critical/warning/info)
- **U-008:** [BEHOBEN] Nitrifikation <5°C = 0 in BiofilterManager
- **U-009:** [BEHOBEN] FishHealthMonitor Engine + API-Endpunkte + Celery-Task
- **U-010:** [BEHOBEN] REQ-007 Verweis + EU-VO 37/2010 + geplante v2.0-Erweiterung
- **U-011:** [BEHOBEN] Vermicompost-Parameter in Szenario 3
- **U-012:** [BEHOBEN] Photoperiode/Schosser in Saisonaltabelle
- **P-001:** [BEHOBEN] pH-Kompromisszone erklärt + systemtyp-abhängige Defaults
- **P-002:** [BEHOBEN] Cycling ≥80% Zielfutter + >15°C
- **P-003:** [BEHOBEN] max_stocking_density_professional_kg_per_1000l Feld ergänzt
- **P-004:** [BEHOBEN] DEFAULT_PROTEIN_BY_FEED_TYPE Map
- **P-005:** [BEHOBEN] Asymmetrische Temperaturkorrektur (Q10 + Hitzestress + Stopp)
- **P-006:** [BEHOBEN] Ramp-up temperaturabhängig + Wasserqualitäts-Gate
- **H-001:** [BEHOBEN] Säure-Nuance für Experten (H3PO4, HNO3)
- **H-002:** [BEHOBEN] EU-VO auf Gattung Clarias erweitert
- **H-003:** [BEHOBEN] Seed-Edge-Generierungsalgorithmus dokumentiert
- **H-004:** [BEHOBEN] Cycling-Erinnerung → täglich (statt 2 Tage)
- **H-005:** [BEHOBEN] WaterTest vs TankState Beziehung geklärt
- **H-006:** [BEHOBEN] Garnelen/Shrimp als v2.0-Erweiterung dokumentiert
- **H-007:** [BEHOBEN] Clarias batrachus → gesamte Gattung Clarias

---

## Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: Emerson-Formel -- pKa-Gleichung ist falsch

**Anforderung:** `pKa = 0.09018 + 2729.92 / T_kelvin` (Zeile 47)
**Problem:** Die zitierte Emerson-Formel verwendet die falsche pKa-Gleichung. Die korrekte Gleichung nach Emerson et al. (1975) lautet:

```
pKa = 0.09018 + 2729.92 / T_kelvin
```

Rechenkontrolle des Testvektors: pH 7.0, 25 Grad C (298.15 K):
- pKa = 0.09018 + 2729.92 / 298.15 = 0.09018 + 9.1566 = **9.2468**
- fraction_NH3 = 1 / (10^(9.2468 - 7.0) + 1) = 1 / (10^2.2468 + 1) = 1 / (176.6 + 1) = **0.00563**
- Bei TAN 1.0 mg/L: NH3 = 0.00563 mg/L

Das Dokument gibt pKa = 9.245 und fraction = 0.0057 an. Das ist numerisch hinreichend konsistent (Abweichung <2%). **Die Formel selbst ist korrekt**, aber der angegebene Testvektor-Ergebniswert 0.0057 weicht geringfuegig vom exakten Wert 0.00563 ab. Das liegt im akzeptablen Rundungsbereich. **Kein Korrekturbedarf bei der Formel.**

**KORREKTUR:** Die pKa-Formel ist nach erneuter Pruefung korrekt. Dieser Befund wird zurueckgezogen.

---

### F-002: Szenario 5 Ammoniak-Berechnung -- Testvektor inkonsistent

**Anforderung:** "pH 7.2, Temp 26 Grad C [...] free NH3 = 3.5 x 0.0089 = 0.031 mg/L" (Zeile 240-241)
**Problem:** Nachrechnung mit der angegebenen Emerson-Formel:
- T_kelvin = 26 + 273.15 = 299.15
- pKa = 0.09018 + 2729.92 / 299.15 = 0.09018 + 9.1262 = **9.2164**
- fraction_NH3 = 1 / (10^(9.2164 - 7.2) + 1) = 1 / (10^2.0164 + 1) = 1 / (103.85 + 1) = **0.00954**
- free_NH3 = 3.5 x 0.00954 = **0.0334 mg/L**

Das Dokument verwendet den Faktor 0.0089, der eine fraction von 0.89% ergibt. Der korrekte Wert ist 0.954%, was zu NH3 = 0.0334 mg/L fuehrt. Die Abweichung ist ~12%, was fuer einen Testvektor zu hoch ist.

**Korrekte Formulierung:** "free NH3 = 3.5 x 0.00954 = 0.0334 mg/L"

---

### F-003: Szenario 2 Response-Berechnung -- Testvektor ebenfalls inkonsistent

**Anforderung:** "free_ammonia berechnet: 3.0 x (1/(10^(9.11-7.5)+1)) = 0.073 mg/L" (Zeile 1516)
**Problem:** Nachrechnung:
- T_kelvin = 28 + 273.15 = 301.15
- pKa = 0.09018 + 2729.92 / 301.15 = 0.09018 + 9.0654 = **9.1556**
- fraction_NH3 = 1 / (10^(9.1556 - 7.5) + 1) = 1 / (10^1.6556 + 1) = 1 / (45.26 + 1) = **0.02161**
- free_NH3 = 3.0 x 0.02161 = **0.0648 mg/L**

Das Dokument verwendet pKa = 9.11, was nicht der Emerson-Formel entspricht (korrekt: 9.1556). Der berechnete Wert 0.073 mg/L weicht um ~13% vom korrekten Wert 0.0648 mg/L ab.

**Korrekte Formulierung:** "free_ammonia berechnet: 3.0 x (1/(10^(9.156-7.5)+1)) = 0.0648 mg/L"

---

### F-004: API-Response Testvektor free_ammonia_mgl ebenfalls falsch

**Anforderung:** Response-Beispiel zeigt `"free_ammonia_mgl": 0.0154` bei pH 7.2, 26 Grad C, TAN 1.5 (Zeile 1348)
**Problem:** Nachrechnung:
- pKa = 9.2164 (wie F-002)
- fraction = 0.00954
- free_NH3 = 1.5 x 0.00954 = **0.01431**

Der angegebene Wert 0.0154 weicht um ~8% ab. Nicht dramatisch, aber fuer ein API-Response-Beispiel, das als Referenz fuer die Implementierung dient, sollte der Wert exakt berechnet sein.

**Korrekte Formulierung:** `"free_ammonia_mgl": 0.0143`

---

### F-005: Karpfen/Koi -- taxonomische Ungenauigkeit

**Anforderung:** `"scientific_name": "Cyprinus carpio"` mit Hinweis `"Koi = Cyprinus rubrofuscus"` (Zeile 609, 625)
**Problem:** Die taxonomische Zuordnung von Koi ist korrekt angesprochen, aber inkonsequent umgesetzt. Aktuelle Taxonomie (Kottelat 2008, akzeptiert durch FishBase):
- Gemeiner Karpfen: *Cyprinus carpio* Linnaeus, 1758
- Koi (Nishikigoi): *Cyprinus rubrofuscus* Lacepede, 1803 (frueher als Unterart *C. carpio haematopterus*)

Die Seed-Daten fuehren beide unter einem einzigen Eintrag `"Cyprinus carpio"`. Wenn Koi explizit erwaehnt werden, sollten sie entweder als separater Seed-Eintrag (`koi_carp` mit `"Cyprinus rubrofuscus"`) oder der Hinweis sollte in den `notes_de` als klarstellender Taxonomie-Hinweis formuliert werden, ohne den falschen Eindruck zu erwecken, sie seien konspezifisch.

**Empfehlung:** Entweder (a) separaten Seed-Eintrag fuer Koi erstellen, oder (b) `common_name_de` aendern zu "Karpfen" und Koi-Hinweis in Notes belassen, oder (c) die notes_de praezisieren: "Koi gehoeren taxonomisch zu *Cyprinus rubrofuscus* (Lacepede 1803), nicht zu *C. carpio*. Beide Arten haben identische Haltungsparameter."

---

### F-006: Regenbogenforelle -- Lethaltemperatur 0 Grad C ist falsch

**Anforderung:** `"temperature_lethal_low_c": 0` fuer Regenbogenforelle (Zeile 592)
**Problem:** Regenbogenforellen (*Oncorhynchus mykiss*) ueberleben problemlos in Gewaessern nahe dem Gefrierpunkt, sofern das Wasser nicht zufriert. In der Aquakultur-Literatur wird die untere Lethaltemperatur (LT50) fuer *O. mykiss* typisch bei **-0.5 bis 0 Grad C** angegeben, was jedoch nur relevant ist, wenn Eis-Kristallbildung eintritt. In einem Aquaponik-System mit Umwaelzung und Heizung friert das Wasser nicht ein. Der Wert 0 Grad C ist als konservative Untergrenze vertretbar, aber biologisch ist die Art kalt-eurytherm und uebersteht auch knapp unter 0 Grad C in fluessigem Wasser.

**Empfehlung:** Wert auf -0.5 aendern oder bei 0 belassen mit Hinweis in `notes_de`, dass die Art bei fluessigem Wasser auch unter 0 Grad C ueberlebt.

---

### F-007: Silurus glanis als "Warmwasser" klassifiziert -- fraglich

**Anforderung:** `"temperature_zone": "warmwater"` fuer *Silurus glanis* (Zeile 632)
**Problem:** Der Europaeische Wels (*Silurus glanis*) wird im Dokument als "warmwater" (24-30 Grad C) klassifiziert, hat aber einen Optimalbereich von 22-28 Grad C und kann bis 4 Grad C Lethaltemperatur ueberleben. In der Aquakultur-Literatur wird *S. glanis* ueblicherweise als **eurytherme Art** betrachtet, die sowohl im temperierten als auch im warmen Bereich gut waechst. Die Klassifikation als reiner "warmwater"-Fisch ist in der Praxis irrelevant fuer die meisten DACH-Aquaponiker, da die Art im Sommer outdoor bei 22-28 Grad C optimal waechst, im Winter aber inaktiv wird.

Die Zonierung hat aber Konsequenzen fuer den Kompatibilitaets-Algorithmus: Bei `warmwater`-Klassifikation wuerde der Wels als inkompatibel mit Salat (besser bei 18-22 Grad C) bewertet, obwohl er im temperierten Bereich (18-24 Grad C) ebenfalls gut waechst.

**Empfehlung:** `temperature_zone` auf `"temperate"` aendern. Der Optimalbereich 22-28 Grad C ueberlappt sowohl mit temperate (18-24) als auch warmwater (24-30). Fuer die Praxis im DACH-Raum ist "temperate" treffender, da der Wels hier ueblicherweise nicht bei 28+ Grad C gehalten wird.

---

### F-008: TAN-Produktionsregel "3% des Futtergewichts" ist zu vereinfacht

**Anforderung:** "Faustregel: ~3% des Futtergewichts = TAN" (Zeile 163, 524, 1003-1005)
**Problem:** Die 3%-Faustregel ist eine haeufig zitierte Vereinfachung, die den Proteingehalt des Futters ignoriert. Die korrekte Berechnung lautet:

```
TAN_g = Futter_g x Proteingehalt_Anteil x 0.16 (N-Anteil im Protein) x 0.80 (Assimilationsrate) x (17/14) (NH3/N Molmassen-Verhaeltnis)
```

Vereinfacht: TAN = Futter x Protein% x 0.092

Beispiele:
- Tilapia-Futter (32% Protein): TAN = 100g x 0.32 x 0.092 = **2.94g** (nahe an 3%)
- Forellenfutter (45% Protein): TAN = 100g x 0.45 x 0.092 = **4.14g** (38% mehr als 3%!)
- Goldfischfutter (28% Protein): TAN = 100g x 0.28 x 0.092 = **2.58g** (14% weniger als 3%)

Fuer Karnivore wie Forelle und Zander mit 40-48% Proteinfutter unterschaetzt die 3%-Regel die TAN-Produktion erheblich, was zu einer Unterdimensionierung des Biofilters fuehren kann.

**Korrekte Formulierung:** Die `calculate_tan_production`-Methode sollte den optionalen `protein_percent`-Parameter aus `FishFeedingEvent` einbeziehen:
```
TAN = daily_feed_g x (protein_percent/100) x 0.092
Fallback (ohne Proteingehalt): TAN = daily_feed_g x 0.03
```

---

### F-009: Chlor-Grenzwert "<0.01 ppm" fuer Fische ist zu konservativ in der Formulierung

**Anforderung:** ">0.01 ppm Chlor ist toedlich fuer Fische" (Zeile 1050-1051)
**Problem:** Der in der Aquakultur-Literatur akzeptierte Grenzwert fuer freies Chlor liegt bei **<0.003 mg/L** (3 ug/L) fuer empfindliche Arten (Salmoniden) und **<0.01 mg/L** fuer robuste Arten (Tilapia, Karpfen). Die Formulierung "toedlich" ist fuer den Wert 0.01 ppm bei robusten Arten uebertrieben -- korrekt waere "schaedigend" oder "stressausloesend". Bei 0.01 ppm sterben Forellen nicht sofort, aber die Kiemenepithelien werden geschaedigt.

Wichtiger: Das Dokument unterscheidet nicht zwischen **freiem Chlor** und **Chloramin**. Chloramin (NH2Cl), das viele kommunale Wasserversorger in DACH verwenden, laesst sich im Gegensatz zu freiem Chlor **nicht durch Abstehen/Belueftung** entfernen und ist bei gleicher Konzentration fuer Fische ebenso toxisch. REQ-014 erwaehnt diese Unterscheidung bereits korrekt (Zeile 93).

**Korrekte Formulierung:** "Freies Chlor und Chloramin >0.003 mg/L schaedigen Kiemen und Biofilter-Bakterien. Grenzwert: <0.003 mg/L fuer Salmoniden, <0.01 mg/L fuer Cypriniden/Cichliden. Leitungswasser MUSS entchlort werden (Aktivkohle oder Natriumthiosulfat). Abstehen reicht nur bei freiem Chlor, nicht bei Chloramin."

---

### F-010: Goldfisch max_stocking_density 5 kg/1000L ist untypisch niedrig

**Anforderung:** `"max_stocking_density_kg_per_1000l": 5` fuer Goldfisch (Zeile 685)
**Problem:** 5 kg/1000L fuer Goldfische ist extrem konservativ. In der Aquaponik-Literatur (Somerville et al. 2014, FAO Technical Paper 589) werden fuer Zierfische in Aquaponik-Systemen 10-15 kg/1000L als Hobby-Maximum angegeben. Der niedrige Wert von 5 kg fuehrt dazu, dass ein 300L-Tank nur 1.5 kg Goldfische halten kann, was bei einem Durchschnittsgewicht von 50-100g nur 15-30 Fische waere -- das passt zum Szenario 3, ist aber als absolutes Maximum fuer ein Aquaponik-System unterdimensioniert. Goldfische sind extrem robuste Fische mit niedrigem DO-Bedarf.

**Empfehlung:** `max_stocking_density_kg_per_1000l` auf 10 erhoehen (Hobby-Aquaponik), mit Hinweis in `notes_de`: "Besatzdichte kann in gut beluefteten Systemen bis 15 kg/1000L betragen, fuer Einsteiger sind 5-10 kg/1000L empfohlen."

---

### F-011: Goldfisch FCR 2.5 (Hobby) und 2.0 (Professional) sind zu hoch

**Anforderung:** `"fcr_hobby": 2.5, "fcr_professional": 2.0` fuer Goldfisch (Zeile 683)
**Problem:** FCR (Feed Conversion Ratio) misst die Effizienz der Futterverwertung (kg Futter pro kg Gewichtszunahme). Ein FCR von 2.5 bedeutet, dass 2.5 kg Futter fuer 1 kg Wachstum benoetigt werden. Fuer Goldfische ist FCR als Kennzahl **nicht sinnvoll**, da sie nicht als Speisefische gehalten werden und in Aquaponik-Systemen typischerweise nicht auf Gewichtszunahme optimiert werden. Die angegebenen Werte sind plausible Schaetzwerte, aber die Kennzahl selbst ist fuer Zierfische irrelevant.

**Empfehlung:** `fcr_hobby` und `fcr_professional` auf `null` setzen und in `notes_de` ergaenzen: "FCR nicht anwendbar (Zierfisch, kein Wachstumsziel). Futtermenge orientiert sich an Wasserqualitaet und Pflanzenbedarf, nicht an Gewichtszunahme."

---

## Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: Fehlender Zink-Eintrag in der Naehrstoffdefizit-Tabelle

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** Zink (Zn)
**Begruendung:** Zink ist nach Eisen das zweithaeufigste Mikronaeher-Defizit in Aquaponik-Systemen, besonders bei pH >7.0. Zinkmangel aeussert sich in verkuerzten Internodien (Rosettenbildung), chlorotischen jungen Blaettern und reduzierter Blattgroesse. In der FAO-Publikation zu Aquaponik (Somerville et al. 2014) wird Zn explizit als defizitaerer Mikronaeher aufgefuehrt.

**Formulierungsvorschlag:**
Zeile in der Naehrstoffdefizit-Tabelle ergaenzen:
```
| Zink (Zn) | Haeufig bei pH >7.0 | Verkuerzte Internodien, kleine Blaetter, Chlorose junger Blaetter | ZnSO4 -- nur bei Mangelsymptomen, enger Toxizitaetsbereich | 0.05-0.3 ppm |
```

Ausserdem `ZnSO4` als neuen `SupplementType`-Enum-Wert ergaenzen:
```python
ZNSO4 = "znso4"  # Zinksulfat (nur bei Mangel, eng dosieren!)
```

---

### U-002: Fehlende Kupfer (Cu)-Erwaehnung als natuerliches Spurenelement

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** Kupfer (Cu) als essentielles Mikronaeher
**Begruendung:** Kupfer ist fuer Pflanzen essentiell (Photosynthese, Lignin-Biosynthese), aber in Aquaponik ein Balanceakt: Kupfer-PSM sind fischgiftig (korrekt im Dokument erwaehnt), aber Kupfer-Spurenelemente im Fischfutter reichen oft nicht aus. Der Zielwert in Aquaponik liegt bei 0.02-0.06 ppm -- deutlich unter dem fischgiftigen Bereich (>0.1 ppm). Das Defizit tritt selten auf, aber die Naehrstoff-Tabelle sollte es erwaehnen.

**Formulierungsvorschlag:**
```
| Kupfer (Cu) | Selten | Welke junger Triebe, chlorotische Blaetter | Monitoring -- Ergaenzung nur unter Aufsicht, Fischgift >0.1 ppm! | 0.02-0.06 ppm |
```

---

### U-003: Fehlende Bor (B)-Zielwerte in der Naehrstofftabelle

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** Bor (B) -- obwohl `H3BO3` als SupplementType existiert (Zeile 816), fehlt Bor in der Naehrstoffdefizit-Tabelle
**Begruendung:** Borsaeure (H3BO3) ist als Supplement-Typ aufgefuehrt, aber der zugehoerige Tabelleneintrag mit Defizit-Symptomen, Zielwert und Sicherheitshinweisen fehlt. Bor hat einen **extrem engen Toxizitaetsbereich** (Optimum 0.3-0.5 ppm, toxisch ab 1.0 ppm fuer viele Pflanzen, fischgiftig ab 1.0 ppm), was einen expliziten Tabelleneintrag zwingend erforderlich macht.

**Formulierungsvorschlag:**
```
| Bor (B) | Selten | Hohle Staengel (Brokkoli), rissige Fruechte (Tomate), kurze Wurzeln | H3BO3 (Borsaeure) -- ENGER TOXIZITAETSBEREICH! Max. 0.5 ppm. Fischgiftig ab 1.0 ppm | 0.3-0.5 ppm |
```

---

### U-004: Fehlende Wasserhaerte-Parameter (GH) in der Grenzwertbewertung

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** GH (Gesamthaerte) als bewerteter Parameter in `evaluate_water_quality`
**Begruendung:** GH wird im WaterTest-Modell korrekt als `gh_dh: Optional[float]` erfasst (Zeile 350), aber in der `evaluate_water_quality`-Methode (Zeile 876) nicht als Pruefparameter aufgefuehrt. GH ist relevant, weil:
- Zu niedrige GH (<4 Grad dH) bei Verwendung von Osmose-/Regenwasser fuehrt zu Calcium- und Magnesiummangel
- Zu hohe GH (>20 Grad dH) kann bei empfindlichen Fischarten Stress verursachen
- GH sollte mindestens als Warning-Parameter (nicht Critical) bewertet werden

**Formulierungsvorschlag:** In der `evaluate_water_quality`-Dokumentation ergaenzen: "Prueft: TAN/free NH3, NO2, NO3, pH, DO, Temperatur, KH, **GH**."

---

### U-005: Fehlende DO-Temperaturkorrelation

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** DO-Saettigungsgrenze als Funktion der Temperatur
**Begruendung:** Geloester Sauerstoff (DO) ist **temperaturabhaengig** -- waermeres Wasser kann weniger O2 halten. Bei 25 Grad C liegt die DO-Saettigung bei ~8.3 mg/L, bei 30 Grad C nur noch bei ~7.6 mg/L. Das bedeutet:
- Warmwasser-Systeme (Tilapia bei 28 Grad C) haben physikalisch weniger DO verfuegbar
- Ein DO-Minimum von 5.0 mg/L fuer Tilapia bei 28 Grad C laesst nur 2.6 mg/L Puffer
- Die Sommer-Saison-Warnung "DO-Achtung!" (Zeile 127) sollte mit konkreten Werten unterfuettert werden

**Formulierungsvorschlag:** Im `NitrogenCycleEngine` eine Methode `calculate_do_saturation(temp_c: float) -> float` ergaenzen:
```
DO_saturation = 14.6 - 0.3943*T + 0.007714*T^2 - 0.0000646*T^3  (Benson & Krause 1984)
```
Und in `evaluate_water_quality`: Warnung wenn DO < 70% der Saettigung.

---

### U-006: Fehlende Phosphat-Akkumulationswarnung

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** Phosphat-Obergrenze
**Begruendung:** Die Naehrstofftabelle gibt einen Zielwert von 10-60 ppm PO4 an und erwaehnt, dass Phosphat "selten defizitaer" ist (Zeile 101). Das stimmt -- aber die Kehrseite fehlt: Phosphat akkumuliert in reifen Systemen haeufig **ueber** 60 ppm und kann bei >100 ppm die Eisenverfuegbarkeit reduzieren (Fe-P-Praezipitation) und Algenbluten foerdern. Eine Warnung bei Phosphat >80 ppm waere fachlich sinnvoll.

**Formulierungsvorschlag:** In der Naehrstofftabelle ergaenzen: "Hinweis: Phosphat akkumuliert in reifen Systemen. Bei >80 ppm: Teilwasserwechsel oder Pflanzen mit hohem P-Bedarf (Tomaten, Paprika) einsetzen."

---

### U-007: Fehlende Wassertemperatur-Grenzwertpruefung im WaterTest

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** Artspezifische Temperaturwarnung in `evaluate_water_quality`
**Begruendung:** Die `FishSpecies`-Seeds enthalten detaillierte Temperaturwerte (min, max, optimal_min, optimal_max, lethal_low, lethal_high), aber die `evaluate_water_quality`-Methode prueft nur "TAN/free NH3, NO2, NO3, pH, DO, Temperatur, KH" ohne die gestuften Schwellen zu spezifizieren:
- `temperature_c < lethal_low` oder `> lethal_high`: **critical** (unmittelbare Lebensgefahr)
- `temperature_c < temperature_min` oder `> temperature_max`: **warning** (Stressbereich)
- `temperature_c` ausserhalb `optimal_min`/`optimal_max`: **info** (suboptimal)

Dies ist implizit gemeint, sollte aber explizit dokumentiert werden.

---

### U-008: Fehlende Nitrifikations-Temperaturuntergrenze

**Anbaukontext:** Aquaponik
**Fehlender Parameter:** Nitrifikations-Stopp unter 5 Grad C
**Begruendung:** Die Nitrifikation (Ammoniak -> Nitrit -> Nitrat) kommt unter ~4-5 Grad C praktisch zum Erliegen. Das ist im Dormanz-Konzept implizit abgedeckt (cycling_status: dormant bei <10 Grad C), aber die `BiofilterManager`-Logik sollte explizit eine **untere Grenze der Nitrifikationsrate** einbeziehen. Die Q10-basierte Temperaturkorrektur (Zeile 1124: "halbiert sich pro 10 Grad C unter 25 Grad C") wuerde bei 5 Grad C eine Kapazitaet von 25% berechnen -- tatsaechlich ist sie nahe Null.

**Formulierungsvorschlag:** In `estimate_required_surface_area`: "Temperatur-Faktor: Q10-Regel, aber Nitrifikation <5 Grad C = 0 (praktischer Stopp). Zwischen 5-10 Grad C: <10% der Nominalkapazitaet."

---

### U-009: Fehlende Fisch-Mortalitaetsrate und Gesundheitsmonitoring

**Anbaukontext:** Aquaponik
**Fehlende Funktionalitaet:** Mortalitaets-Tracking ist als API-Endpunkt vorhanden (Zeile 1283), aber es fehlen:
1. **Mortalitaetsrate-Berechnung** (% Verlust pro Woche/Monat)
2. **Alarm bei ueberdurchschnittlicher Mortalitaet** (>2% pro Woche als Warnschwelle)
3. **Fischverhalten als Fruehwarnung** -- `fish_response: refused` in FeedingEvent sollte nach 2 aufeinanderfolgenden "refused"-Events einen Gesundheitsalarm ausloesen

**Formulierungsvorschlag:** Neue Engine-Methode:
```python
def evaluate_fish_health(
    self,
    fish_stock: FishStock,
    recent_feedings: list[FishFeedingEvent],
    recent_water_tests: list[WaterTest],
) -> list[HealthAlert]:
    """
    Prueft: Mortalitaetsrate >2%/Woche,
    2+ refused feedings, DO < stress threshold,
    TAN > species max.
    """
```

---

### U-010: Fehlende Integration mit REQ-007 (Erntemanagement) fuer Fisch-Ernte

**Anbaukontext:** Aquaponik
**Fehlende Funktionalitaet:** Das Dokument behandelt Fisch-Ernte nur implizit ueber "FishStock loeschen" (HTTP 409 wenn >0 Fische). Es fehlt:
1. **Fisch-Ernte-Workflow** analog zu REQ-007 (HarvestBatch fuer Fische)
2. **Schlachtgewicht-Tracking** (market_weight_g ist als Seed-Datum vorhanden, aber kein Ernte-Event)
3. **Karenz-Konzept fuer Fische** -- Medikamente (z.B. Formalin gegen Ichthyophthirius) haben Wartezeiten vor der Schlachtung (EU-VO 37/2010)

**Formulierungsvorschlag:** Mindestens einen Hinweis ergaenzen: "Fisch-Ernte-Workflow wird in einer zukuenftigen Erweiterung ueber REQ-007 abgebildet. Tierarzneimittel-Rueckstandsverordnung (EU-VO 37/2010) definiert Wartezeiten fuer Speisefische."

---

### U-011: Fehlende Vermicompost-Parameter

**Anbaukontext:** Aquaponik (Media-Bed)
**Fehlende Parameter:** Wurmkompost (Vermicompost) ist als Boolean-Flag `has_vermicompost` modelliert (Zeile 331), aber ohne jegliche Fachlogik:
1. Eisenia fetida (Kompostwurm) -- korrekt erwaehnt (Zeile 198) -- hat einen Temperaturoptimalbereich von 15-25 Grad C und stirbt ab >35 Grad C
2. Vermicompost verbessert die Mineralisierung und Fe/K-Verfuegbarkeit signifikant -- dieser Effekt sollte in der Naehrstoffdefizit-Analyse beruecksichtigt werden (geringere Supplementierungshaeufigkeit)

**Formulierungsvorschlag:** Mindestens in Notes oder als Logik-Hinweis: "Systeme mit Vermicompost: Eisen- und Kalium-Defizite treten seltener auf. Wurmkompost-Temperatur-Limit beachten (Eisenia fetida: max 30 Grad C, optimal 15-25 Grad C, keine Warmwasser-Media-Bed-Systeme ueber 30 Grad C)."

---

### U-012: Fehlende Saison-bezogene Photoperioden-Interaktion

**Anbaukontext:** Outdoor-Aquaponik
**Fehlender Parameter:** Photoperiode und Kurztagspflanzen-Risiko
**Begruendung:** Outdoor-Aquaponik-Pflanzen sind den natuerlichen Tageslaengen ausgesetzt. Salat als Langtagspflanze schosst bei >14h Licht im Hochsommer. Das ist ein bekanntes Problem in Sommer-Aquaponik-Systemen im DACH-Raum (>16h Tageslicht im Juni/Juli). Die Saisonalitaetstabelle (Zeile 124-129) erwaehnt "Blattsalate" im Fruehling und "Fruchtgemuese" im Sommer, aber nicht den Schosser-Effekt bei Salat im Hochsommer.

**Formulierungsvorschlag:** In der Saisonalitaetstabelle ergaenzen:
```
| Sommer | Maximum | >25 Grad C (DO-Achtung!) | Fruchtgemuese, Tomaten. **Salat schosst** bei >25 Grad C und >14h -- hitzetolerante Sorten waehlen oder verschatten | Volle Kapazitaet |
```

---

## Zu Ungenau -- Praezisierung noetig

### P-001: pH-Zielbereich 6.8-7.2 ohne Begruendung der Kompromisszone

**Vage Anforderung:** `ph_target_min: float` (Default: 6.8) / `ph_target_max: float` (Default: 7.2) (Zeile 336-337)
**Problem:** Der Default-Bereich 6.8-7.2 ist der klassische Aquaponik-Kompromiss, wird aber nicht erklaert. Fuer die Implementierung und Nutzer-Dokumentation fehlt der Kontext:
- Fische bevorzugen pH 7.0-8.0
- Pflanzen-Naehrstoffverfuegbarkeit ist optimal bei pH 5.5-6.5
- Nitrifikationsbakterien arbeiten optimal bei pH 7.0-8.0
- Der Bereich 6.8-7.2 ist ein Kompromiss, der keine der drei Gruppen optimal bedient

**Messbare Alternative:** Den Default-Bereich in den Notes/Dokumentation erklaeren und ggf. systemtyp-abhaengig machen:
- Media-Bed (bessere Pufferung): 6.4-7.0
- DWC/NFT (geringere Pufferung): 6.8-7.2
- Kalkstein-Media-Bed: 7.0-7.5 (natuerliche pH-Anhebung)

---

### P-002: Cycling-Schwellenwerte ohne pH/Temperatur-Kontext

**Vage Anforderung:** "`cycling -> cycled`: TAN <0.25 mg/L UND NO2 <0.1 mg/L fuer >=7 aufeinanderfolgende Tage bei voller Futtermenge" (Zeile 77)
**Problem:** Die Schwellenwerte sind fuer einen standardmaessig gefuetterten System bei 20-25 Grad C sinnvoll. Aber:
1. "Bei voller Futtermenge" -- was ist "voll"? Sollte `daily_feed_target_g` auf dem System sein
2. Bei niedrigen Temperaturen (15 Grad C) ist TAN <0.25 auch erreichbar, weil weniger gefuettert wird -- der Biofilter waere trotzdem nicht fuer volle Last eingefahren
3. Die 7-Tage-Regel sollte "7 Tage bei >=80% der Ziel-Futtermenge" lauten

**Messbare Alternative:** "`cycling -> cycled`: TAN <0.25 mg/L UND NO2 <0.1 mg/L fuer >=7 aufeinanderfolgende Tage bei >=80% der daily_feed_target_g UND Wassertemperatur >15 Grad C"

---

### P-003: "Besatzdichte-Maximum" ohne Klarstellung ob Hobby oder Profi

**Vage Anforderung:** `max_stocking_density_kg_per_1000l` -- im Modell als einzelner Wert (Zeile 283)
**Problem:** Die FishSpecies hat ein einzelnes Feld `max_stocking_density_kg_per_1000l`, das laut Kommentar das "Hobby-Maximum" ist (Zeile 283). In der professionellen RAS-Aquakultur liegen die Besatzdichten fuer Tilapia bei 80-100 kg/1000L (vs. 25 kg/1000L im Hobby). Es fehlt ein `max_stocking_density_professional` analog zu den FCR-Feldern (die Hobby/Professional unterscheiden).

**Messbare Alternative:** Entweder zweites Feld `max_stocking_density_professional_kg_per_1000l` ergaenzen, oder das bestehende Feld explizit als "konservatives Hobby-Maximum" dokumentieren und fuer professionelle Anwendung auf Fachliteratur verweisen.

---

### P-004: feed_type auf FishSpecies (carnivore/omnivore/herbivore) ohne Auswirkung auf Logik

**Vage Anforderung:** `feed_type: Literal['carnivore', 'omnivore', 'herbivore']` auf FishSpecies (Zeile 282)
**Problem:** Der `feed_type` ist als Stammdatum vorhanden, wird aber in keiner Engine-Logik verwendet. Er sollte mindestens folgende Auswirkungen haben:
1. **TAN-Berechnung:** Karnivore haben proteinreicheres Futter (40-48%) -> hoehere TAN-Produktion (vgl. F-008)
2. **Naehrstoffprofil:** Karnivore produzieren mehr Phosphat (proteinreiches Futter = mehr P-Ausscheidung)
3. **Futterwahl-Empfehlung:** Karnivore benoetigen Fischmehl-basiertes Futter (Nachhaltigkeitshinweis)

**Messbare Alternative:** `feed_type` in `FeedingRateCalculator.calculate_tan_production()` einbeziehen:
```python
DEFAULT_PROTEIN_BY_FEED_TYPE = {
    'carnivore': 0.45,  # 45% Protein
    'omnivore': 0.32,   # 32% Protein
    'herbivore': 0.28,  # 28% Protein
}
```

---

### P-005: Q10-Temperaturkorrektur fuer Fuetterung ohne Referenztemperatur-Klarstellung

**Vage Anforderung:** "Q10-Regel: Futtermenge halbiert sich pro 10 Grad C unter Optimaltemperatur" (Zeile 994)
**Problem:** Die Q10-Regel wird hier vereinfacht dargestellt. Fragen:
1. Welche Referenztemperatur? `temperature_optimal_min_c` oder `temperature_optimal_max_c`?
2. Was passiert ueber Optimaltemperatur? Fuetterung steigt nicht weiter -- sie sollte sogar **sinken** bei Hitzestress (>temperature_max_c)
3. Q10 = 2 ist ein Standardwert fuer biochemische Reaktionen, aber Fisch-Appetit folgt eher einer Glocken-/Asymmetrie-Kurve, nicht einer linearen Q10-Reduktion

**Messbare Alternative:** Die Formel explizit machen:
```
temp_factor = 2^((water_temp - optimal_min) / 10)  wenn water_temp < optimal_min
temp_factor = 1.0  wenn optimal_min <= water_temp <= optimal_max
temp_factor = max(0, 1 - (water_temp - optimal_max) / (max_temp - optimal_max))  wenn water_temp > optimal_max
temp_factor = 0  wenn water_temp >= max_temp (Fuetterung stoppen!)
```

---

### P-006: Saison-Ramp-up ist pauschal 4x2 Wochen ohne Temperaturabhaengigkeit

**Vage Anforderung:** "Woche 1-2: 25%, Woche 3-4: 50%, Woche 5-6: 75%, ab Woche 7: 100%" (Zeile 132-135, 1014)
**Problem:** Der Ramp-up-Plan ist temperaturunabhaengig. Bei 15 Grad C Wassertemperatur im Maerz dauert die Biofilter-Reaktivierung laenger als bei 20 Grad C im April. Ein fester 7-Wochen-Plan ist bei niedrigen Temperaturen zu aggressiv.

**Messbare Alternative:** Ramp-up-Geschwindigkeit mit Temperaturfaktor versehen:
```
ramp_duration_weeks = 7 / temp_factor  (mit temp_factor basierend auf Q10)
```
Oder pragmatischer: "Ramp-up nur weiter steigern, wenn TAN <0.5 mg/L UND NO2 <0.5 mg/L. Bei Spikes: aktuelle Stufe beibehalten bis Werte stabil."

---

## Hinweise und Best Practices

### H-001: Saeureausschluss in Aquaponik -- Regel ist zu absolut

Die Aussage "In Aquaponik-Systemen duerfen **keine Saeuren** als pH-Down verwendet werden" (Zeile 103) ist eine Vereinfachung. In der Praxis verwenden einige fortgeschrittene Aquaponiker:
- **Phosphorsaeure (H3PO4)** in minimalen Dosen zur pH-Korrektur, wenn die Nitrifikation den pH nicht ausreichend senkt (z.B. bei kalkreichem Leitungswasser mit sehr hoher KH)
- **Salpetersaeure (HNO3)** -- fuegt gleichzeitig Nitrat hinzu

Der absolute Ausschluss ist fuer Einsteiger korrekt und sicher, aber fuer fortgeschrittene Nutzer (REQ-021 Erfahrungsstufen) koennte eine abgestufte Empfehlung sinnvoll sein:
- Beginner: "Keine Saeuren verwenden" (Hard-Block)
- Expert: "Phosphorsaeure in Kleinstmengen moeglich (max 0.5 mL/100L, pH nie unter 6.5 senken)" (Warning)

### H-002: EU-VO 1143/2014 -- Clarias gariepinus Status pruefen

Die Angabe, dass *Clarias gariepinus* (Afrikanischer Raubwels) als invasive Art nach EU-VO 1143/2014 gelistet ist (Zeile 145), sollte geprueft werden. *Clarias gariepinus* steht auf der **Unionsliste invasiver gebietsfremder Arten** (Durchfuehrungsverordnung (EU) 2016/1141, aktualisiert). Der Status ist korrekt. Allerdings gibt es in einigen EU-Mitgliedstaaten Ausnahmeregelungen fuer geschlossene Kreislaufanlagen (RAS). Fuer die DACH-Region:
- **DE:** Haltung in geschlossenen RAS unter Auflagen moeglich (TierSchG + FischSeuchV)
- **AT:** Generell verboten (Oesterreichisches Artenschutzgesetz)
- **CH:** Nicht EU-Mitglied, eigene Regelung (Freisetzungsverordnung)

Die `regulatory_notes` auf dem Silurus-glanis-Eintrag (Zeile 645-646) erwaehnen den Verbotsgrund korrekt.

### H-003: Fehlende Datenquelle fuer Fisch-Pflanzen-Kompatibilitaet

Die `compatible_fish_plant`- und `incompatible_fish_plant`-Edges benoetigen initialen Seed-Daten-Bestand. Es fehlt:
1. Eine Liste der konkreten Seed-Edges (welche Fischarten mit welchen Pflanzenarten kompatibel sind)
2. Eine Referenz auf die Datenquelle fuer diese Zuordnung
3. Ein Algorithmus oder Heuristik zur automatischen Generierung basierend auf Temperaturzonen

**Empfehlung:** Seed-Edges basierend auf der Temperaturzonen-Tabelle (Zeile 112-116) automatisch generieren:
```
FUER JEDE FishSpecies f:
  FUER JEDE Species p (mit Wurzelzonen-Temperatur-Anforderung):
    temperature_overlap = overlap(f.optimal_range, p.root_zone_range)
    WENN temperature_overlap > 0: compatible_fish_plant (temperature_match = overlap_score)
    SONST: incompatible_fish_plant (reason = "Temperaturzone inkompatibel")
```

### H-004: Fehlende Celery-Task-Frequenz fuer Cycling-Systeme

Die `generate_water_test_reminders`-Task (Zeile 1454) unterscheidet zwischen Cycling (>2 Tage) und Cycled (>7 Tage). Fuer Cycling-Systeme sollte die Erinnerungsfrequenz **taeglich** sein (nicht alle 2 Tage), da Ammonia- und Nitrit-Spikes innerhalb von 24h letale Werte erreichen koennen. Die 2-Tage-Schwelle ist fuer Hobby-Systeme mit manuellen Tests akzeptabel, aber die Empfehlung in der Cycling-Phase sollte "taeglich" lauten.

### H-005: Redundanz zwischen WaterTest und TankState

REQ-014 definiert TankState mit pH, EC, Temperatur, DO. REQ-026 definiert WaterTest mit pH, TAN, NO2, NO3, Temperatur, DO, KH, GH, Fe, K, Ca, Mg, PO4. Die Erweiterung von TankState um `ammonia_tan_mgl`, `nitrite_mgl`, `nitrate_mgl`, `kh_dh`, `gh_dh` (Zeile 405-410) fuehrt zu einer Datenredundanz: Ein Wassertest im Aquaponik-System erzeugt sowohl einen WaterTest-Record als auch einen TankState-Record mit teilweise identischen Daten. Die Beziehung sollte geklaert werden -- vermutlich ist WaterTest das primaere Event und TankState wird daraus abgeleitet.

### H-006: Fehlende Beruecksichtigung von Garnelen/Shrimp

Fuer den DACH-Markt zunehmend relevant sind Suesswassergarnelen (*Macrobrachium rosenbergii*, Riesensuesswassergarnele) und *Neocaridina davidi* (Zwerggarnele) in Aquaponik-Systemen. Garnelen haben deutlich andere Wasserparameter (niedrigere TAN-Toleranz, hoehere Ca-Anforderung fuer Haeutung, Cu-Empfindlichkeit). Dies waere eine Erweiterung fuer v2.0.

### H-007: Clarias batrachus vs. Clarias gariepinus

Im Dokument wird nur *Clarias gariepinus* als invasive Art erwaehnt (Zeile 145). Auch *Clarias batrachus* (Walking Catfish) ist in der EU als invasiv gelistet. Die regulatory_notes sollten allgemein auf "Gattung *Clarias*" verweisen, nicht nur auf eine Art.
