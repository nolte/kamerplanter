# Agrarbiologisches Anforderungsreview: REQ-005 Hybrid-Sensorik
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Indoor-Anbau, Hydroponik, Zimmerpflanzen, Gewaechshaus, Outdoor (ergaenzend)
**Analysierte Dokumente:**
- `spec/req/REQ-005_Hybrid-Sensorik.md` (v2.0) -- Hauptdokument
- `spec/req/REQ-003_Phasensteuerung.md` (v2.1) -- Querverweise Soll-Ist-Vergleich
- `spec/req/REQ-004_Duenge-Logik.md` (v2.0) -- EC/pH-Sensorik
- `spec/req/REQ-014_Tankmanagement.md` (v1.0) -- Tank-Sensoren
- `spec/req/REQ-018_Umgebungssteuerung.md` (v1.1) -- Sensor-Aktor-Regelkreis
- `spec/req/REQ-019_Substratverwaltung.md` (v4.1) -- Substrat-Monitoring
- `spec/req/REQ-010_IPM-System.md` (v1.0) -- Klimadaten fuer Schaedlingsrisiko
- `spec/req/REQ-002_Standortverwaltung.md` (v4.0) -- Standort-Zuordnung

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Solide Grundlagen; VPD-Berechnung, PPFD/DLI korrekt differenziert. Einzelne biologische Ungenauigkeiten bei Validierungsbereichen und Blatttemperatur-Annahmen |
| Indoor-Vollstaendigkeit | 3/5 | Klimaparameter gut abgedeckt; Lichtspektrum-Monitoring oberflaeglich, Substratfeuchte-Differenzierung fehlt |
| Zimmerpflanzen-Abdeckung | 2/5 | Kein Anbaukontext -- System ist auf Nutzpflanzen-Indoor/Hydro ausgerichtet (Projekt-Scope), Zimmerpflanzen daher nicht im Fokus |
| Hydroponik-Tiefe | 4/5 | DO, EC, pH, Wassertemperatur vorhanden; ORP fehlt als Sensorparameter (nur in REQ-014 TankState), Chiller-Steuerung nicht als Sensoranforderung definiert |
| Messbarkeit der Parameter | 4/5 | Gute Validierungsbereiche mit Quality-Scoring; einige physikalisch fragwuerdige Grenzen |
| Praktische Umsetzbarkeit | 4/5 | Hybrid-Ansatz (Auto/Semi/Manual) hervorragend durchdacht; Interpolation, Fallback, Health-Monitoring praxisnah |

**Gesamteinschaetzung:**
REQ-005 ist eine der staerksten Spezifikationen im Projekt. Der Hybrid-Ansatz mit drei Betriebsmodi (vollautomatisch, semi-automatisch, manuell) und der hierarchischen Fallback-Kette ist fachlich exzellent konzipiert und adressiert ein reales Problem: Die meisten Hobby-Grower haben keine lueckenlose Sensorik. Die Datenqualitaetsbewertung ueber Quality-Scores, die statistische Anomalieerkennung und die automatische Task-Generierung bei Sensorausfall sind praxisnah und biologisch sinnvoll.

Verbesserungspotenzial besteht bei der biologischen Praezision einzelner Validierungsbereiche, der fehlenden Beruecksichtigung der Sensorplatzierung als Datenqualitaetsfaktor und der unvollstaendigen Integration von Substrat- und Wasserqualitaetsparametern, die in REQ-014 und REQ-019 definiert, aber nicht sauber als Sensorparameter in REQ-005 gespiegelt werden.

---

## Rot: Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: EC-Validierungsbereich zu eng -- verhindert valide Hydroponik-Messungen [BEHOBEN]
**Anforderung:** `VALID_RANGES = { ... 'ec': (0, 5) ... }` (`REQ-005_Hybrid-Sensorik.md`, ~Zeile 460)
**Problem:** Der obere Validierungsbereich von 5 mS/cm ist fuer die Plausibilitaetspruefung zu niedrig. Im Drain-to-Waste-Hydroponik-Betrieb und bei Runoff-Messungen sind EC-Werte bis 8-10 mS/cm keine Seltenheit -- insbesondere bei:
- Runoff-Messungen nach Trockenphasen (Salzakkumulation im Substrat)
- Rezirkulationssystemen mit Konzentrationsanstieg durch Verdunstung
- Steinwolle-Slabs im Spaetsommer (Substrat-EC kann 6-8 mS/cm erreichen)
- Kokossubstrat bei unzureichender Vorspuelung (natuerlicher Kationen-Austausch)

Ein Wert von 6.5 mS/cm in der Naehloesung ist zwar problematisch und sollte einen Alert ausloesen, ist aber physikalisch und in der Praxis absolut moeglich und darf nicht als "ausserhalb des physikalisch moeglichen Bereichs" abgelehnt werden.

**Korrekte Formulierung:** `'ec': (0, 15)` -- physikalischer Plausibilitaetsbereich. Der agronomisch sinnvolle Bereich (0.5-3.5 mS/cm je nach Kultur und Phase) wird ueber die Alert-Schwellwerte (`alert_threshold_min`/`alert_threshold_max`) abgebildet, nicht ueber die Plausibilitaetspruefung.
**Gilt fuer Anbaukontext:** Indoor, Hydroponik/Soilless, Gewaechshaus

### F-002: Blatttemperatur-Differenz als feste Konstante ist biologisch ungenau [BEHOBEN]
**Anforderung:** `LET leaf_temp = temp - 2.0` (REQ-003, Zeile ~189, referenziert durch REQ-005 VPD-Berechnung)
**Problem:** Die Annahme "Blatttemperatur = Lufttemperatur - 2 Grad C" ist eine haeufig verwendete, aber fachlich problematische Vereinfachung. Die tatsaechliche Blatttemperatur-Differenz (Delta-T_leaf) haengt ab von:
- **Transpirationsrate** (hoch bei niedrigem VPD, niedrig bei Trockenstress): Unter gut transpirierenden Bedingungen kann Delta-T_leaf -3 bis -5 Grad C betragen
- **Lichtintensitaet/PPFD:** Unter Hochdruckentladungslampen (HPS) mit hohem Infrarotanteil kann die Blatttemperatur ueber der Lufttemperatur liegen (+1 bis +3 Grad C)
- **LED-Beleuchtung:** Weniger IR-Strahlung, daher typischerweise Blatt kuehler als Luft (-1 bis -3 Grad C)
- **Luftbewegung:** Starke Ventilation reduziert die Grenzschicht und naehert Blatt- an Lufttemperatur an

REQ-005 definiert die Blatttemperatur-Differenz als Sensorparameter (Zeile 28: "Blatttemperatur-Differenz"), bietet aber keine Moeglichkeit, diese als konfigurierbaren Wert (statt hart kodierte -2 Grad C) oder als gemessenen Wert (IR-Thermometer) in die VPD-Berechnung einzuspeisen.

**Korrekte Formulierung:** Die VPD-Berechnung sollte drei Modi unterstuetzen:
1. **Gemessen:** Blatttemperatursensor (IR-Thermometer, z.B. Apogee SI-131) als eigener Sensorparameter `leaf_temp`
2. **Konfigurierbar:** `leaf_temperature_offset_c: float` pro Location/Lichttyp (Default: -2.0 fuer LED, +1.0 fuer HPS)
3. **Berechnet:** Modellbasiert aus PPFD, Lufttemperatur, rH und Luftbewegung (fortgeschritten)
**Gilt fuer Anbaukontext:** Indoor, Gewaechshaus

### F-003: CO2-Validierungsbereich-Untergrenze physikalisch falsch [BEHOBEN]
**Anforderung:** `VALID_RANGES = { ... 'co2': (200, 5000) ... }` (`REQ-005_Hybrid-Sensorik.md`, ~Zeile 460)
**Problem:** Die Untergrenze von 200 ppm ist physikalisch unrealistisch fuer erdnahe Messungen. Der atmosphaerische CO2-Gehalt liegt aktuell bei ca. 420 ppm (2026, Mauna Loa). Werte unter 300 ppm treten nur unter extremen Umstaenden auf (z.B. stark photosynthetisch aktiver, geschlossener Gewaechshausraum ohne Belueftung am Ende der Lichtperiode -- selbst dann selten unter 250 ppm). Ein Messwert von 220 ppm bei einem Indoor-Grow deutet fast sicher auf einen defekten Sensor hin.

Gleichzeitig sollte die Obergrenze hoeher sein: CO2-Dosierungsanlagen koennen bei Fehlfunktion Werte ueber 5000 ppm erzeugen. Der MAK-Wert (Maximale Arbeitsplatzkonzentration) fuer CO2 liegt bei 5000 ppm -- Werte darueber sind gesundheitsgefaehrdend und muessen als Sicherheitsalarm erfasst werden koennen.

**Korrekte Formulierung:**
- Physikalischer Plausibilitaetsbereich: `'co2': (150, 10000)` -- erlaubt Erfassung von Extremwerten bei Fehlfunktion
- Agronomisch sinnvoller Bereich (Warning-Zone): 350-1500 ppm
- Sicherheits-Alert ab 5000 ppm (Gesundheitsschutz, wird in REQ-018 als Notabschaltung referenziert)
**Gilt fuer Anbaukontext:** Indoor, Gewaechshaus

---

## Orange: Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: Fehlender Sensorparameter "Blatttemperatur" (leaf_temp) [BEHOBEN]
**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** `leaf_temp` als eigenstaendiger `ParameterType` in der Sensor-Enum
**Begruendung:** REQ-005 erwaehnt in Zeile 28 ausdruecklich "Blatttemperatur-Differenz" als ueberwachten Klimaparameter. Jedoch fehlt `leaf_temp` in der `ParameterType`-Enum (Zeile 1143): `Literal['temp', 'humidity', 'ec', 'ph', 'ppfd', 'co2', 'soil_moisture', 'water_level', 'vpd']`. Ohne diesen Parameter kann kein dedizierter Blatttemperatur-Sensor (z.B. Apogee SI-131, Melexis MLX90614) korrekt erfasst werden.

Die Blatttemperatur ist der biologisch relevantere Wert fuer die VPD-Berechnung (Leaf-VPD vs. Air-VPD). Leaf-VPD beschreibt den tatsaechlichen Transpirationsdruck an der Blattoberflaeche und korreliert besser mit der Pflanzenphysiologie als Air-VPD.

**Formulierungsvorschlag:**
```python
ParameterType = Literal[
    'temp', 'leaf_temp', 'humidity', 'ec', 'ph', 'ppfd',
    'co2', 'soil_moisture', 'water_level', 'vpd',
    'do', 'orp', 'water_temp', 'flow_rate', 'air_velocity',
    'substrate_temp', 'dli', 'par_spectrum'
]
```

### U-002: Fehlende Sensorparameter fuer Hydroponik-Wasserqualitaet [BEHOBEN]
**Anbaukontext:** Hydroponik/Soilless
**Fehlende Parameter:**
- `do` (Dissolved Oxygen / Geloester Sauerstoff, mg/L) -- erwaehnt in Business Case Zeile 52 ("Geloester Sauerstoff"), aber nicht in `ParameterType` oder `VALID_RANGES`
- `orp` (Oxidation-Reduction Potential, mV) -- erwaehnt in REQ-014 TankState, fehlt komplett in REQ-005
- `water_temp` (Wassertemperatur Naehloesung, Grad C) -- erwaehnt in Business Case Zeile 49, fehlt in `ParameterType`
- `flow_rate` (Durchflussrate, L/h) -- erwaehnt in Business Case Zeile 50, fehlt in `ParameterType`

**Begruendung:** Diese Parameter sind in der Business-Case-Beschreibung (Abschnitt "Hydro-Systeme", Zeilen 47-52) explizit aufgefuehrt, fehlen aber in den technischen Modellen. Insbesondere ist DO (geloester Sauerstoff) ein ueberlebenswichtiger Parameter fuer DWC-Systeme (Deep Water Culture): Unter 4 mg/L O2 entstehen anaerobe Bedingungen, die innerhalb von 24-48 Stunden zu irreversibler Wurzelfaeule (Pythium, Fusarium) fuehren. REQ-014 definiert DO in TankState (Zeile 115), aber REQ-005 kann diesen Wert weder erfassen noch validieren.

**Formulierungsvorschlag:** Ergaenzung von `VALID_RANGES`:
```python
VALID_RANGES = {
    # ... bestehende ...
    'do': (0, 20),           # mg/L; optimal >6, kritisch <4
    'orp': (-500, 1000),     # mV; >700 steril, <250 Pathogen-Risiko
    'water_temp': (0, 45),   # Grad C; optimal 18-22, >25 Algen/Pythium
    'flow_rate': (0, 5000),  # L/h
    'substrate_temp': (0, 50), # Grad C; <12 Wurzelstress, >28 Pythium
}
```

### U-003: Fehlende Sensorplatzierung als Qualitaetsfaktor [BEHOBEN]
**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Sensorposition relativ zur Pflanzenzone (Canopy-Level, Substrat-Level, Raumdecke)
**Begruendung:** Die Messposition hat enormen Einfluss auf die agronomische Relevanz der Daten. Ein Temperatursensor an der Zeltwand misst systematisch andere Werte als einer auf Canopy-Hoehe (Pflanzenspitzen-Niveau). Relevante Probleme:

- **Temperatur:** Vertikaler Gradient von 2-5 Grad C zwischen Boden und Decke in Growzelten. Ein Sensor an der Decke misst bis zu 5 Grad C hoeher als Canopy-Level.
- **Luftfeuchtigkeit:** Am Substrat oft 10-20% rH hoeher als auf Canopy-Hoehe.
- **PPFD:** Variiert um 30-50% zwischen Zentrumsmessung und Randbereich unter einer Lampe (Inverse-Square-Law / Kosinus-Korrektur).
- **CO2:** Schichtet sich in geschlossenen Raeumen (schwerer als Luft) -- Messung auf Canopy-Hoehe kritisch.

Das `Sensor`-Modell hat `location_type: Literal['air', 'substrate', 'water', 'light']`, aber keine Information ueber die vertikale Position oder den Abstand zum Pflanzenbestand.

**Formulierungsvorschlag:** Erweiterung des Sensor-Modells:
```python
# In Sensor-Node
mounting_height_cm: Optional[int]  # Hoehe ueber Boden
mounting_position: Optional[Literal[
    'canopy_level', 'substrate_level', 'intake',
    'exhaust', 'ambient', 'center', 'edge'
]]
representative_area_m2: Optional[float]  # Repraesentative Flaeche
```

### U-004: Fehlende Rate-of-Change-Validierung fuer PPFD und Substratfeuchte [BEHOBEN]
**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** `max_rate_of_change` fuer `ppfd` und `soil_moisture` (Zeile 554-562)
**Begruendung:** Die `SensorReadingValidator.validate_reading_sequence()` definiert `max_rate_of_change`-Defaults nur fuer `temp`, `humidity`, `ec`, `ph` und `co2`. PPFD und Bodenfeuchte fehlen:

- **PPFD:** Im Gewaechshaus aendert sich PPFD bei Wolkendurchzug sprunghaft (0 -> 800 umol/m2/s in Sekunden). Indoor bleibt PPFD bei konstantem Dimmer stabil -- Spruenge deuten auf Lampenfehler. Sinnvoller Default: 500 umol/m2/s/min (erlaubt Wolkendurchzug) bzw. 100 fuer Indoor-only.
- **Bodenfeuchte:** Aendert sich sprunghaft beim Giessen (z.B. 25% -> 70% in 1 Minute), aber langsam durch Verdunstung. Hier ist die Rate asymmetrisch: schneller Anstieg (Giessen) = normal, schneller Abfall = Sensorfehler oder Topf umgekippt. Sinnvoller Default: 30%/min (Anstieg) bzw. 5%/min (Abfall).

**Formulierungsvorschlag:**
```python
max_rate_of_change = {
    # ... bestehende ...
    'ppfd': 800.0,           # umol/m2/s pro Minute (Wolkendurchzug)
    'soil_moisture': 30.0,   # %/min (Giess-Spruenge erlaubt)
    'water_level': 10.0,     # %/min (schnelle Tankentleerung = Leck-Alarm)
    'water_temp': 0.3,       # Grad C/min (Chiller-Einfluss)
}
```

### U-005: Fehlende Verknuepfung Sensorwert -> Wachstumsphase fuer dynamische Alerting [BEHOBEN]
**Anbaukontext:** Indoor, Hydroponik
**Fehlende Logik:** Phasenabhaengige Alert-Schwellwerte
**Begruendung:** Die Alert-Schwellwerte (`alert_threshold_min`, `alert_threshold_max`) im Sensor-Modell sind statische Werte. In der Realitaet aendern sich optimale Bereiche mit der Wachstumsphase erheblich:

| Parameter | Keimung | Saemling | Vegetativ | Bluete | Reife |
|-----------|---------|----------|-----------|--------|-------|
| VPD (kPa) | 0.4-0.8 | 0.5-0.8 | 0.8-1.2 | 1.0-1.5 | 1.2-1.6 |
| rH (%) | 70-80 | 65-75 | 55-70 | 40-60 | 40-50 |
| EC (mS/cm) | 0.5-0.8 | 0.8-1.2 | 1.2-2.0 | 1.8-2.8 | Flush |
| PPFD (umol) | 50-150 | 150-300 | 400-600 | 600-900 | 400-600 |

REQ-003 definiert `requirement_profiles` mit Soll-Werten pro Phase, und die Edge `validates` (REQ-005, Zeile 168: `observations -> requirement_profiles`) deutet diese Verknuepfung an. Allerdings fehlt die technische Spezifikation, wie:
1. Der aktuelle Soll-Bereich dynamisch aus der Phase geladen wird
2. Alerts phasenabhaengig ausgeloest werden
3. Bei Phasenuebergang die Schwellwerte automatisch angepasst werden

REQ-018 loest dies teilweise fuer Aktoren (PhaseControlProfile), aber REQ-005 hat kein Aequivalent fuer Sensor-Alerting.

**Formulierungsvorschlag:** Ergaenzung eines `PhaseAlertProfile`-Konzepts:
```
phase_alert_profile: growth_phases -> alert_profiles  // Phase bestimmt Alerting-Schwellwerte
```
Oder alternativ: Alert-Schwellwerte direkt aus `requirement_profiles` ableiten, mit konfigurierbarer Toleranz (z.B. Alert bei >15% Abweichung vom Soll-VPD).

### U-006: Fehlender Parameter Lichtspektrum (PAR-Spektralverhaeltnis) [BEHOBEN]
**Anbaukontext:** Indoor
**Fehlende Parameter:** `par_spectrum` -- Rot/Blau/Fernrot-Verhaeltnis
**Begruendung:** REQ-005 erwaehnt in Zeile 44 ausdruecklich "Spektrum-Analyse - Rot/Blau/Far-Red-Verhaeltnis" als ueberwachten Lichtparameter. REQ-003 definiert in `requirement_profiles` ein `light_spectrum`-Dict mit Blau/Gruen/Rot/Far-Red-Anteilen. Jedoch fehlt jegliche technische Modellierung in REQ-005:
- Kein Sensorparameter `par_spectrum` in `ParameterType`
- Keine Validierungsbereiche fuer Spektralverhaeltnisse
- Keine Sensor-Empfehlung (z.B. Apogee SQ-610 Spektral-PAR-Sensor)

Das Rot/Fernrot-Verhaeltnis (R:FR) ist pflanzenphysiologisch hochrelevant: Es steuert ueber das Phytochromsystem das Streckungswachstum und die Bluehinduktion. Bei Indoor-Anbau mit mehrkanaligen LED-Leuchten (die per `spectrum_control`-Capability in REQ-018 steuerbar sind) muss das tatsaechliche Spektrum auch gemessen werden koennen, um den Regelkreis zu schliessen.

**Formulierungsvorschlag:** Mindestens R:FR-Verhaeltnis als skalaren Sensorwert modellieren:
```python
'r_fr_ratio': (0.1, 20.0),  # Rot:Fernrot -- Sonnenlicht ~1.2, LED veg ~5-10, LED bloom ~2-3
'blue_fraction': (0.0, 1.0), # Blauanteil 400-500nm (%)
```

### U-007: TimescaleDB-Downsampling-Strategie nicht spezifiziert [BEHOBEN]
**Anbaukontext:** Alle
**Fehlende Logik:** Aggregationsintervalle und Retention-Policy fuer Zeitreihendaten
**Begruendung:** REQ-005 erwaehnt TimescaleDB als empfohlene Technologie (Zeile 8, 1249) und definiert `AggregatedMetric` mit Typen `hourly`, `daily`, `weekly` (Zeile 131). Was fehlt:

1. **Retention-Policy:** Wie lange werden Rohdaten (sekundengenau) vs. aggregierte Daten gespeichert? Empfehlung:
   - Rohdaten: 30 Tage (hohe Granularitaet fuer Debugging/Anomalieerkennung)
   - Stuendliche Aggregate: 1 Jahr (Saison-Vergleich)
   - Taegliche Aggregate: 5 Jahre (Langzeit-Trends)
2. **Continuous Aggregates:** TimescaleDB unterstuetzt materialized continuous aggregates -- diese muessen pro Sensortyp definiert werden
3. **DLI-Akkumulation:** DLI (Daily Light Integral) ist kein einzelner Sensorwert, sondern die Integral-Summe von PPFD ueber den Tag: `DLI = Summe(PPFD_i * delta_t_i) / 1.000.000`. Dies muss als TimescaleDB-Aggregate definiert werden, nicht als einzelner Sensor.

**Formulierungsvorschlag:** Ergaenzung eines Abschnitts "Daten-Retention und Aggregation":
```
| Datentyp | Granularitaet | Retention | Storage-Engine |
|----------|---------------|-----------|----------------|
| Rohdaten | Messintervall (10s-60min) | 30 Tage | TimescaleDB hypertable |
| Stuendlich | 1h | 1 Jahr | TimescaleDB continuous aggregate |
| Taeglich | 1d | 5 Jahre | TimescaleDB continuous aggregate |
| DLI | 1d (berechnet) | 5 Jahre | TimescaleDB continuous aggregate |
| Woechentlich | 1w | Unbegrenzt | ArangoDB AggregatedMetric |
```

### U-008: Fehlende Substratfeuchte-Differenzierung nach Messprinzip [BEHOBEN]
**Anbaukontext:** Indoor, Hydroponik
**Fehlende Information:** Substratfeuchte-Sensortypen messen grundverschiedene physikalische Groessen
**Begruendung:** REQ-005 definiert `soil_moisture` als Prozent (0-100%) (Zeile 459). In der Praxis gibt es drei fundamental verschiedene Messprinzipien, die nicht direkt vergleichbar sind:

1. **Kapazitive Sensoren** (z.B. Xiaomi Plant Sensor, ECOWITT WH51): Messen die Dielektrizitaetskonstante. Ausgabe in "%" ist herstellerspezifisch skaliert und substratabhaengig -- 50% in Kokos bedeutet etwas voellig anderes als 50% in Blumenerde.
2. **Tensiometer** (z.B. Irrometer): Messen die Saugspannung (Matrixpotential) in kPa oder cbar. Pflanzenphysiologisch der relevanteste Wert, da er beschreibt, wie fest das Wasser im Substrat gebunden ist. Optimal: -10 bis -30 kPa fuer die meisten Kulturen.
3. **TDR/FDR** (Time/Frequency Domain Reflectometry, z.B. Teros 10): Messen volumetrischen Wassergehalt (VWC) in %. Wissenschaftlich am genauesten, aber teuer.

Ohne Kenntnis des Sensortyps ist der Wert "50% Bodenfeuchte" nicht interpretierbar. Ein kapazitiver Sensor bei 50% kann je nach Substrat "zu trocken" oder "zu nass" bedeuten.

**Formulierungsvorschlag:** Erweiterung des `soil_moisture`-Parameters:
```python
# Im Sensor-Modell
soil_moisture_method: Optional[Literal[
    'capacitive', 'tensiometer', 'tdr', 'fdr', 'gravimetric'
]]
soil_moisture_unit: Optional[Literal['percent_vwc', 'kpa', 'cbar', 'raw_adc']]
substrate_type_key: Optional[str]  # Verweis auf REQ-019 Substrat -- fuer korrekte Kalibrierung
```

---

## Gelb: Zu Ungenau -- Praezisierung noetig

### P-001: PPFD-Validierungsbereich zu eng fuer Gewaechshaeuser [BEHOBEN]
**Vage Anforderung:** `'ppfd': (0, 2000)` (~Zeile 460)
**Problem:** 2000 umol/m2/s ist als Obergrenze physikalisch korrekt fuer Kunstlicht, aber im Gewaechshaus bei direkter Sonneneinstrahlung werden 2200+ umol/m2/s gemessen (Sommer, Suedeuropa). Zudem koennen Vollsonnewerte im Hochsommer durch Reflexion/Diffusion sogar kurzfristig 2500 umol/m2/s erreichen.
**Messbare Alternative:** `'ppfd': (0, 2500)` -- erlaubt Gewaechshaus-Szenarien. Alert-Schwellwert kulturspezifisch (z.B. Salat: Warnung ab 500, Cannabis: Warnung ab 1500 bei normalem CO2).

### P-002: Interpolations-Schwellwert von 2h zu pauschal [BEHOBEN]
**Vage Anforderung:** "Interpolation bei kurzen Ausfaellen (<2h)" (~Zeile 63)
**Problem:** Ob 2 Stunden "kurz" sind, haengt vom Parameter und Kontext ab:
- **Temperatur, Luftfeuchtigkeit, VPD:** 2h Interpolation ist bei stabilen Indoor-Bedingungen vertretbar.
- **EC in Rezirkulation:** EC kann sich bei Verdunstung oder pH-Drift innerhalb von 1-2h um 0.5+ mS/cm aendern -- 2h Interpolation waere hier riskant.
- **Substratfeuchte:** Abhaengig vom Substrat (Steinwolle trocknet in 2h merklich, Erde kaum).
- **CO2:** Bei aktiver Dosierung aendert sich CO2 in Minuten um Hunderte ppm.
**Messbare Alternative:** Parameter-spezifische Interpolationsgrenzen:
```python
MAX_INTERPOLATION_HOURS = {
    'temp': 3.0,
    'humidity': 3.0,
    'vpd': 2.0,
    'ec': 1.0,        # Schnelle Aenderungen in Hydro
    'ph': 1.0,
    'co2': 0.5,       # Sehr dynamisch bei Dosierung
    'ppfd': 0.5,       # Licht aendert sich sprunghaft
    'soil_moisture': 4.0,  # Aendert sich langsam (ausser beim Giessen)
    'water_temp': 3.0,
    'do': 1.0,         # Kritisch fuer Hydroponik
}
```

### P-003: Quality-Score fuer manuelle Eingaben pauschal zu niedrig [BEHOBEN]
**Vage Anforderung:** `'manual': 0.85` (Zeile 508)
**Problem:** Ein manueller Messwert von einem kalibrierten Apera pH20 (Genauigkeit +/-0.01 pH) ist qualitativ hoeher als ein Auto-Wert von einem unkalibriertem kapazitiven China-Sensor. Der Quality-Score basiert ausschliesslich auf der Datenquelle (Auto vs. Manual), nicht auf der Messgeraete-Qualitaet oder dem Kalibrierungsstatus des Sensors.
**Messbare Alternative:** Quality-Score-Berechnung erweitern:
```python
# Faktor 1: Source (wie bisher)
# Faktor 2: Kalibrierungsstatus des Sensors
calibration_penalty = 1.0
if days_since_calibration > 90:
    calibration_penalty = 0.7
elif days_since_calibration > 30:
    calibration_penalty = 0.9

# Faktor 3: Messgeraetegenauigkeit (wenn angegeben)
accuracy_factor = 1.0 - (sensor.accuracy_percent / 200) if sensor.accuracy_percent else 0.9

# Faktor 4: Manuelle Eingabe mit professionellem Geraet
if source == 'manual' and measurement_tool_accuracy < 2.0:
    manual_quality = 0.95  # statt pauschal 0.85
```

### P-004: Anomalieerkennung -- Z-Score >2 als Ausreisser-Schwelle zu sensitiv [BEHOBEN]
**Vage Anforderung:** `FILTER z_score > 2.0` und Observation als Ausreisser markieren (Zeile 372)
**Problem:** Bei einer Normalverteilung liegen 4.6% aller Werte ausserhalb von +/-2 Standardabweichungen. Bei einem Sensor mit 60 Messwerten pro Stunde (1/min) wuerden rein statistisch fast 3 "Ausreisser" pro Stunde gemeldet -- das erzeugt Alert-Fatigue. Zudem sind viele Umweltparameter nicht normalverteilt:
- CO2 hat bei aktiver Dosierung eine bimodale Verteilung (Licht an/aus)
- PPFD im Gewaechshaus hat eine stark rechtschiefe Verteilung (meist bewoelkt, selten Vollsonne)
- VPD aendert sich systematisch mit der Tageszeit (kein Rauschen, sondern Trend)
**Messbare Alternative:**
- Z-Score > 3.0 fuer `warning` (0.3% Fehlalarmrate)
- Z-Score > 4.0 fuer `critical`
- Verwendung eines gleitenden Fensters (z.B. letzte 4h statt 7 Tage) fuer Paramater mit Tagesgang (CO2, VPD, PPFD)
- Alternativ: Modified Z-Score basierend auf Median/MAD (robuster gegen Ausreisser)

### P-005: Sensor-Ausfall-Erkennung -- 6h Warning-Schwelle zu pauschal [BEHOBEN]
**Vage Anforderung:** `MAX_AGE_WARNING_HOURS = 6` (Zeile 819)
**Problem:** 6 Stunden ohne Sensorupdate sind fuer verschiedene Parameter unterschiedlich kritisch:
- **EC/pH in Hydroponik:** 6h ohne Messung bei Rezirkulation kann bedeuten, dass EC um 1+ mS/cm gedriftet ist -- eine "Warning" ist hier zu spaet, das sollte bereits nach 2h "Critical" sein
- **Temperatur Indoor:** Bei Klimaanlage/Heizung relativ stabil -- 6h Warning ist angemessen
- **Substratfeuchte:** In Erde kaum kritisch (aendert sich langsam), in Steinwolle/Kokos bei hohem VPD kann die Pflanze in 6h sichtbar welken
**Messbare Alternative:** Parameterspezifische Warning-Schwellen definieren, analog zu P-002.

### P-006: Entity-ID-Inferenz basierend auf Naming ist fragil [BEHOBEN]
**Vage Anforderung:** `_infer_parameter_from_entity()` Methode (Zeile 763-797)
**Problem:** Die Methode inferiert den Parametertyp aus dem Entity-ID-Namen und der Unit. Diese Heuristik hat biologisch relevante Schwaechen:
- `'hum' in entity_lower or unit_lower == '%'` -- Substratfeuchte hat auch die Unit "%" und koennte "moisture" im Namen haben. Verwechslungsgefahr zwischen Luftfeuchtigkeit und Substratfeuchte.
- `'ec' in entity_lower` -- wuerde auch `sensor.electric_consumption` matchen
- Die Methode kann nicht zwischen `water_temp` (Naehloesung) und `temp` (Luft) unterscheiden, obwohl beide in Grad C gemessen werden und "temp" im Namen haben koennen

**Messbare Alternative:** Die Zuordnung Entity-ID -> Parameter sollte nicht inferiert, sondern explizit beim Sensor-Setup konfiguriert werden. Die Inferenz-Methode kann als Vorschlag dienen, aber der Nutzer muss bestaetigen.

---

## Gruen: Hinweise & Best Practices

### H-001: VPD-Berechnung -- Tetens-Formel vs. Buck-Equation
Die VPD-Berechnung in REQ-003 (Zeile 190) verwendet die August-Roche-Magnus-Approximation:
`SVP = 610.7 * 10^(7.5 * T / (237.3 + T))`
Dies ist eine gaengige und ausreichend genaue Naeherung fuer den Temperaturbereich 0-50 Grad C (Fehler <0.5%). Alternativ bietet die Buck-Gleichung (1981) eine leicht hoehere Genauigkeit:
`SVP = 611.21 * exp((18.678 - T/234.5) * (T / (257.14 + T)))`
Fuer die Praxis im Indoor-Anbau ist der Unterschied vernachlaessigbar. Die gewahlte Formel ist korrekt.

### H-002: DLI-Berechnung -- Formel korrekt referenziert
REQ-003 (Zeile 55) und REQ-018 (Zeile 75) verwenden korrekt:
`DLI = PPFD * h * 3600 / 1.000.000` (Ergebnis in mol/m2/Tag)
Vereinfacht: `DLI = PPFD * h * 0.0036`
Die Formel ist korrekt. Die angegebenen DLI-Bereiche (Salat 12-17, Kraeuter 15-20, Tomaten 20-30, Cannabis 35-45) entsprechen der Fachliteratur.

### H-003: Empfehlung -- Sensorredundanz fuer kritische Parameter
Die Multi-Sensor-Aggregation (Zeile 296ff) ist exzellent konzipiert. Empfehlung fuer die Implementierung:
- **Pflicht-Redundanz** (mindestens 2 Sensoren): EC, pH (beide driften und erfordern Kalibrierung)
- **Empfohlen** (2 Sensoren): Temperatur, Luftfeuchtigkeit (fuer VPD-Berechnung -- Fehler propagieren)
- **Optional** (1 Sensor reicht): CO2, PPFD, Substratfeuchte

### H-004: Empfehlung -- Sensor-Kalibrierungsintervalle biologie-basiert definieren
Die Kalibrierungs-Erinnerung bei >90 Tagen (Zeile 1284) ist ein sinnvoller Default. Fachlich empfohlene Intervalle:
- **pH-Sonde:** Alle 14-30 Tage (Glasmembran degradiert, besonders in naehrstoffreicher Loesung)
- **EC-Sonde:** Alle 30-60 Tage (stabiler als pH)
- **PPFD-Sensor (Quantensensor):** Jaehrlich (sehr stabil)
- **Temperatur/Feuchte (DHT22, SHT31):** Werkskalibriert, Austausch nach 2-3 Jahren
- **DO-Sonde:** Alle 14-30 Tage (Membran-Elektrolyt degradiert)

### H-005: Korrekte Unterscheidung PPFD vs. Lux -- Positiv
REQ-005 verwendet durchgehend PPFD (umol/m2/s) als Licht-Messgroesse und nicht Lux. Dies ist fachlich korrekt: PPFD misst die photosynthetisch aktive Strahlung (PAR, 400-700nm), waehrend Lux auf die menschliche Sehempfindlichkeit normiert ist und den pflanzenphysiologisch relevanten Rot- und Blauanteil unterbewertet. Die Spezifikation erwaehnt Lux an keiner Stelle -- dies ist konsistent und korrekt.

### H-006: Empfehlung -- Sensorik fuer IPM-Risikomodelle (REQ-010)
REQ-010 (IPM) definiert `environmental_triggers` fuer Krankheiten (Zeile 36). Die Verknuepfung mit REQ-005 Sensordaten ist in den Abhaengigkeiten genannt (Zeile 1259), aber die konkreten Kopplungen fehlen. Beispiele:
- **Botrytis-Risiko:** rH > 85% + Temperatur 18-25 Grad C + schlechte Luftzirkulation (air_velocity < 0.3 m/s) => hohes Risiko
- **Spinnmilben-Risiko:** rH < 40% + Temperatur > 26 Grad C => hohes Risiko
- **Pythium-Risiko:** Wassertemperatur > 25 Grad C + DO < 5 mg/L => kritisch
- **Echter Mehltau:** rH 40-70% + grosse Tag/Nacht-Temperaturschwankungen > 10 Grad C => hohes Risiko

Diese Risikomodelle koennten als `calculated`-Sensoren (virtuelle Sensoren) in REQ-005 modelliert werden.

### H-007: Empfehlung -- Photoperioden-Ueberwachung als Sicherheitsfunktion
REQ-005 erwaehnt "Fotoperiode - Tatsaechliche Beleuchtungsdauer" (Zeile 45), definiert aber keinen Sensorparameter oder Alerting dafuer. Bei Kurztagspflanzen (Cannabis, Weihnachtskaktus) ist eine Licht-Leckage waehrend der Dunkelphase kritisch: Bereits 5-10 Minuten Streulicht koennen die Blueteinduktion stoeren oder Herkomphorhermaphroditismus ausloesen. Ein `photoperiod_violation`-Alert (virtueller Sensor: PPFD > 1 umol/m2/s waehrend Dunkelphase laut Zeitplan aus REQ-018) waere eine wertvolle Sicherheitsfunktion.

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | In Business Case erwaehnt? | In ParameterType-Enum? | In VALID_RANGES? | Empfohlener Bereich | Prioritaet |
|-----------|---------------------------|----------------------|-----------------|--------------------|-----------|
| PPFD (umol/m2/s) | Ja | Ja | Ja (0-2000) | 0-2500 korrigieren | Hoch |
| DLI (mol/m2/d) | Ja | Nein | Nein | 0-65 (berechnet) | Hoch |
| VPD (kPa) | Ja | Ja | Nein | 0.0-3.5 | Hoch |
| Blatttemperatur (Grad C) | Ja ("Blatttemp-Differenz") | Nein | Nein | 10-45 | Hoch |
| Substrattemperatur (Grad C) | Nein (in REQ-019) | Nein | Nein | 5-40 | Mittel |
| Geloester Sauerstoff DO (mg/L) | Ja | Nein | Nein | 0-20 | Hoch (Hydro) |
| ORP (mV) | Nein (nur REQ-014) | Nein | Nein | -500 bis 1000 | Mittel (Rezirk.) |
| Wassertemperatur (Grad C) | Ja | Nein | Nein | 0-45 | Hoch (Hydro) |
| Durchflussrate (L/h) | Ja | Nein | Nein | 0-5000 | Niedrig |
| TDS (ppm) | Ja | Nein | Nein | 0-5000 | Niedrig (EC reicht) |
| Luftbewegung (m/s) | Ja | Nein | Nein | 0-10 | Mittel |
| Lichtspektrum R:FR | Ja ("Rot/Blau/Far-Red") | Nein | Nein | 0.1-20 | Mittel |
| EC (mS/cm) | Ja | Ja | Ja (0-5) | 0-15 korrigieren | Hoch |
| CO2 (ppm) | Ja | Ja | Ja (200-5000) | 150-10000 korrigieren | Hoch |
| rH (%) | Ja | Ja | Ja (0-100) | OK | -- |
| pH | Ja | Ja | Ja (0-14) | OK | -- |
| Bodenfeuchte (%) | Ja | Ja | Ja (0-100) | OK (Einheit unklar) | Mittel |

---

## Querverweise-Konsistenz

| REQ-005 Parameter | Korrespondenz in REQ-014 TankState | Korrespondenz in REQ-003 RequirementProfile | Korrespondenz in REQ-018 ControlRule | Status |
|-------------------|-----------------------------------|-------------------------------------------|-------------------------------------|--------|
| EC (mS/cm) | `ec_ms` | `target_ec_ms` | `sensor_parameter: "ec"` | Konsistent |
| pH | `ph` | `target_ph` | `sensor_parameter: "ph"` | Konsistent |
| Wassertemperatur | `water_temp_celsius` | -- | -- | Nur REQ-014, fehlt in REQ-005 Enum |
| DO (mg/L) | `dissolved_oxygen_mgl` | -- | -- | Nur REQ-014, fehlt in REQ-005 Enum |
| ORP (mV) | `orp_mv` | -- | -- | Nur REQ-014, fehlt in REQ-005 Enum |
| VPD (kPa) | -- | `vpd_target_kpa` | `sensor_parameter: "vpd"` | Konsistent, aber VPD fehlt in VALID_RANGES |
| PPFD | -- | `light_ppfd_target` | -- (DLI-basiert in REQ-018) | Konsistent |
| DLI | -- | `dli_target_mol` | DLI-basierte Lichtsteuerung | DLI als berechneter Wert, kein eigener Sensor |
| Substratfeuchte | -- | -- | `sensor_parameter: "soil_moisture"` | Kein Soll-Wert in REQ-003 |
| Luftbewegung | -- | -- | -- | In keinem REQ als Zielwert |

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| VPD-Berechnung | Monteith & Unsworth (2013) | Principles of Environmental Physics |
| PPFD-Referenzwerte | Apogee Instruments | apogeeinstruments.com |
| Sensorempfehlungen | Meter Group (TEROS) | metergroup.com |
| DLI-Empfehlungen | Faust & Logan (2018) | HortTechnology 28(4) |
| Hydroponik-EC/pH | Resh, Howard M. (2022) | Hydroponic Food Production, 8th Ed. |
| DO-Management | Graves, Chris (1983) | ISOSC Proceedings |
| Blatttemperatur-Modelle | Gates, David M. (1980) | Biophysical Ecology |
| Pflanzensensorik allgemein | Kacira, Murat et al. (2023) | Sensors in Agriculture |

---

## Glossar

- **PPFD** (Photosynthetic Photon Flux Density): Mass fuer die photosynthetisch nutzbare Lichtmenge in umol/m2/s -- der korrekte Wert fuer Pflanzenwachstum (nicht Lux!)
- **DLI** (Daily Light Integral): Tageslicht-Gesamtmenge in mol/m2/d -- PPFD * Stunden * 0.0036
- **VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa -- beschreibt den "Durst" der Luft, abhaengig von Temperatur und Luftfeuchtigkeit. Steuert die Transpiration und damit Naehrstofftransport.
- **EC** (Electrical Conductivity): Elektrische Leitfaehigkeit der Naehrloesung in mS/cm -- Mass fuer die Naehrstoffkonzentration
- **DO** (Dissolved Oxygen): Geloester Sauerstoff in der Naehrloesung in mg/L -- kritisch fuer Wurzelgesundheit in Hydroponik
- **ORP** (Oxidation-Reduction Potential): Redoxpotential in mV -- Indikator fuer Sterilisationseffektivitaet in Rezirkulationssystemen
- **DIF**: Differenz zwischen Tag- und Nachttemperatur -- steuert Streckungswachstum ueber Gibberellin-Synthese
- **R:FR** (Red:Far-Red Ratio): Verhaeltnis von Rotlicht (660nm) zu Fernrotlicht (730nm) -- steuert Phytochrom-Gleichgewicht und damit Streckungswachstum/Bluehinduktion
- **TDR** (Time Domain Reflectometry): Messprinzip fuer volumetrischen Wassergehalt im Substrat
- **MAD** (Median Absolute Deviation): Robustes Streumass, weniger ausreisserempfindlich als Standardabweichung
- **Leaf-VPD vs. Air-VPD**: Leaf-VPD berechnet den Dampfdruck an der Blattoberflaeche (biologisch relevanter), Air-VPD nur aus Lufttemperatur/Feuchte (einfacher zu messen)
