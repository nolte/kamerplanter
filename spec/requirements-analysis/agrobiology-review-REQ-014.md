# Agrarbiologisches Anforderungsreview: REQ-014 Tankmanagement

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Tankmanagement, Naehrstoffloesungen, pH/EC-Management, Bewasserungsstrategien
**Analysierte Dokumente:**
- `spec/req/REQ-014_Tankmanagement.md` (v1.0, Hauptdokument)
- `spec/req/REQ-004_Duenge-Logik.md` (v2.0, Querverweise)
- `spec/req/REQ-019_Substratverwaltung.md` (v4.1, Querverweise)
- `spec/req/REQ-002_Standortverwaltung.md` (v4.0, Querverweise)
- `spec/req/REQ-005_Hybrid-Sensorik.md` (v2.1, Querverweise)
- `spec/req/REQ-003_Phasensteuerung.md` (v2.1, Querverweise)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Solide Grundlagen, wenige aber korrekturbeduerftige Fehler bei DO-Saettigung und Organik-Erkennung |
| Hydroponik-Tiefe | 5/5 | Hervorragend differenzierte Tank-Typen, Rezirkulation, DO, ORP |
| pH/EC-Management | 4/5 | Gute Differenzierung nach Tank-Typ, fehlende Aspekte bei Rezirkulations-EC-Dynamik |
| Wartungs-Vollstaendigkeit | 4/5 | Gute Standardintervalle, fehlende Anpassung an Jahreszeit/Umgebung |
| Messbarkeit der Parameter | 5/5 | Durchgehend quantifiziert, gute Schwellenwerte |
| Praktische Umsetzbarkeit | 4/5 | Hoch, aber einige Heuristiken sind zu vereinfacht |
| Konsistenz mit REQ-004/019 | 5/5 | Hervorragende Querverweise, konsistente Modelle |

REQ-014 ist ein fachlich sehr ausgereiftes Dokument, das die Tankinfrastruktur mit bemerkenswert hoher Detailtiefe spezifiziert. Die Differenzierung nach Tank-Typen (nutrient, irrigation, reservoir, recirculation) mit jeweils angepassten Schwellenwerten ist fachlich korrekt und praxisrelevant. Die Integration von WateringEvents fuer ergaenzende Handduengung neben automatischer Fertigation zeigt ein fortgeschrittenes Verstaendnis realer Anbauszenarien. Es gibt einige korrekturbeduerftige Punkte bei der DO-Saettigungsphysik, der Organik-Erkennung und dem Loesungsalter-Modell, die im Folgenden detailliert werden.

---

## ROT -- Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: DO-Saettigungswerte in TankStateRecord-Beschreibung sind ungenau [BEHOBEN]

**Anforderung:** "optimal >6 mg/L, kritisch <4 mg/L. Sinkt mit steigender Temperatur (20 Grad C: max ~9.1; 30 Grad C: max ~7.5)." (`REQ-014_Tankmanagement.md`, ~Zeile 477)

**Problem:** Die Saettigungswerte sind fuer reine Wasser-Luft-Gleichgewichte angegeben. Eine Naehrstoffloesung hat durch geloeste Salze (EC 1.5-3.0 mS/cm) eine um 5-10% reduzierte Sauerstoff-Loeslichkeit (Salting-Out-Effekt). Bei EC 2.5 und 25 Grad C liegt die tatsaechliche DO-Saettigung nicht bei ~8.2 mg/L (Reinwasser) sondern bei ~7.5-7.8 mg/L. Das bedeutet, dass die Warnschwelle von 6 mg/L in warmer, konzentrierter Naehrstoffloesung enger an der physikalischen Saettigung liegt als suggeriert.

**Korrekte Formulierung:** Die Beschreibung sollte den Salting-Out-Effekt erwaehnen:
```
"Gelöstsauerstoff in mg/L. Kritisch für Hydroponik: optimal >6 mg/L (>75% Sättigung),
kritisch <4 mg/L (anaerobe Bedingungen). Sättigung sinkt mit steigender Temperatur
UND steigendem EC (Salting-Out-Effekt): Reinwasser 20°C: ~9.1 mg/L;
Nährlösung EC 2.0 bei 25°C: ~7.2-7.5 mg/L."
```

**Gilt fuer Anbaukontext:** Hydroponik/Soilless, Indoor


### F-002: Organik-Erkennung ueber fehlenden product_key ist ein Fehlschluss [BEHOBEN]

**Anforderung:** Loesungsalter-Check im `check_alerts`: `has_organics = any(not f.get('product_key') for f in ...)` (`REQ-014_Tankmanagement.md`, ~Zeile 906-908)

**Problem:** Die Annahme "kein Produkt-Key = wahrscheinlich organisch" ist biologisch und logisch falsch. Ein fehlender `product_key` bedeutet lediglich, dass der Duenger nicht in der Datenbank hinterlegt ist -- das kann auch ein mineralischer Duenger sein, der manuell eingegeben wurde. Umgekehrt koennen organische Produkte sehr wohl einen `product_key` haben (z.B. "Komposttee" oder "Fischemulsion" aus dem REQ-004-Datenbestand). In REQ-004 existiert bereits das Feld `is_organic: bool` auf dem Fertilizer-Modell, das genau diese Unterscheidung korrekt trifft.

**Korrekte Formulierung:** Die Organik-Erkennung sollte auf dem `is_organic`-Flag des Duenger-Snapshots basieren. Der FertilizerSnapshot muss um ein `is_organic: bool`-Feld erweitert werden:
```python
class FertilizerSnapshot(BaseModel):
    product_key: Optional[str] = None
    product_name: str
    ml_per_liter: float = Field(gt=0, le=50.0)
    is_organic: bool = Field(default=False)  # NEU

# Im Loesungsalter-Check:
has_organics = any(
    f.get('is_organic', False)
    for f in (last_fill_event.get('fertilizers_used') or [])
)
```

**Gilt fuer Anbaukontext:** Alle Kontexte mit Tank-Nutzung


### F-003: Chloramin wird nicht ausreichend von Chlor unterschieden [BEHOBEN]

**Anforderung:** "Chlor/Chloramin im Ausgangswasser (ppm). >0.5 ppm toetet Mykorrhiza und Nuetzlinge ab." (`REQ-014_Tankmanagement.md`, ~Zeile 530-536)

**Problem:** Chlor (freies Cl2/HOCl) und Chloramin (NH2Cl) werden zwar im Feldnamen `chlorine_ppm` zusammengefasst, haben aber fundamental unterschiedliche Eigenschaften:
- **Freies Chlor** verfluechtigt sich durch 24h Abstehen oder Belueftung (Entgasung).
- **Chloramin** ist stabil, verfluechtigt sich NICHT durch Stehen und erfordert chemische Behandlung (Ascorbinsaeure, Kaliummetabisulfit oder Aktivkohlefilter).

Die Empfehlung "24h Abstehen lassen" (Zeile 983) ist fuer Chloramin falsch und wuerde die biologischen Additive trotzdem schaedigen. Viele kommunale Wasserversorger in den USA und zunehmend auch in Europa verwenden Chloramin statt Chlor.

**Korrekte Formulierung:** Entweder zwei separate Felder oder ein kombiniertes Feld mit Typ-Angabe:
```python
chlorine_ppm: Optional[float] = None         # Freies Chlor
chloramine_ppm: Optional[float] = None       # Gebundenes Chlor (Chloramin)
# ODER:
chlorine_type: Optional[Literal['free_chlorine', 'chloramine', 'unknown']] = None
```
Die Warnung muss differenzierte Entchlorungsempfehlungen geben:
- Freies Chlor: "24h Abstehen lassen ODER Ascorbinsaeure (1g pro 400L bei 1 ppm Cl)"
- Chloramin: "Ascorbinsaeure zwingend (1g pro 400L bei 1 ppm) ODER Aktivkohle-Filter. Abstehen ist NICHT ausreichend."

**Gilt fuer Anbaukontext:** Alle Kontexte mit biologischen Additiven


---

## ORANGE -- Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: Rezirkulierende Systeme -- EC-Drift-Richtung als diagnostisches Signal fehlt [BEHOBEN]

**Anbaukontext:** Hydroponik/Soilless (Rezirkulation)

**Fehlende Parameter:** EC-Drift-Richtung (steigend vs. fallend) mit diagnostischer Interpretation

**Begruendung:** Bei rezirkulierenden Systemen ist die *Richtung* der EC-Aenderung ein entscheidendes diagnostisches Signal:
- **EC steigt:** Pflanzen nehmen mehr Wasser als Naehrstoffe auf (haeufig bei Hitze, hoher Transpiration, oder zu hoher EC). Handlung: Mit Reinstwasser auffuellen, NICHT mit Naehrstoffloesung.
- **EC sinkt:** Pflanzen nehmen mehr Naehrstoffe als Wasser auf (haeufig bei niedrigem EC, Starkzehrerphase). Handlung: Konzentrierte Stammloesung nachdosieren.
- **EC stabil, pH sinkt:** Hohe Nitrat-Aufnahme (Pflanzen geben H+-Ionen ab). Kation/Anion-Balance pruefen.
- **EC stabil, pH steigt:** Hohe Ammonium-Aufnahme. Nitrat:Ammonium-Verhaeltnis korrigieren.

Das aktuelle Alert-System erkennt nur absolute EC-Abweichung vom Zielwert, nicht die *Verlaufsrichtung*, die fuer die korrekte Korrekturmassnahme entscheidend ist.

**Formulierungsvorschlag:** Erweiterung des `check_alerts` um Trendanalyse ueber die letzten 3-5 TankState-Records:
```python
# EC-Trend bei Rezirkulation (letzten 3+ Messungen)
if tank_type == 'recirculation' and len(recent_states) >= 3:
    ec_values = [s['ec_ms'] for s in recent_states if s.get('ec_ms')]
    if len(ec_values) >= 3:
        ec_trend = ec_values[-1] - ec_values[0]
        if ec_trend > 0.3:
            alerts.append({
                'type': 'ec_trend_rising',
                'severity': 'medium',
                'message': "EC steigt — Pflanzen nehmen mehr Wasser als Nährstoffe. "
                           "Mit Reinstwasser auffüllen, NICHT mit Nährlösung.",
            })
        elif ec_trend < -0.3:
            alerts.append({
                'type': 'ec_trend_falling',
                'severity': 'medium',
                'message': "EC sinkt — Pflanzen nehmen mehr Nährstoffe als Wasser. "
                           "Konzentrierte Stammlösung nachdosieren.",
            })
```


### U-002: Wassertemperatur-Korrektur -- Zusammenhang mit DO fehlt im Alert-System [BEHOBEN]

**Anbaukontext:** Hydroponik/Soilless

**Fehlende Parameter:** Kreuz-Validierung Temperatur x DO

**Begruendung:** Temperatur und DO sind physikalisch gekoppelt (Henry'sches Gesetz): Steigende Wassertemperatur senkt die DO-Saettigung. Das aktuelle Alert-System generiert separate Warnungen fuer beide Parameter, gibt aber keinen Hinweis auf den kausalen Zusammenhang. Ein Alert "DO niedrig" bei gleichzeitig hoher Temperatur sollte priorisiert auf Temperaturreduktion hinweisen (Ursache beheben), nicht nur auf "Belueftung erhoehen" (Symptom bekaempfen).

**Formulierungsvorschlag:**
```python
# Kreuz-Alert: Hohe Temperatur + niedriger DO
if (current_state.get('water_temp_celsius', 0) > 22
    and current_state.get('dissolved_oxygen_mgl', 99) < 6
    and tank_type in ('nutrient', 'recirculation')):
    alerts.append({
        'type': 'temp_do_compound',
        'severity': 'critical',
        'message': "Hohe Temperatur UND niedriger DO — Wassertemperatur senken "
                   "ist effektiver als Belüftung erhöhen. Ursache (Temperatur) "
                   "statt Symptom (DO) beheben. Optionen: Wasserkühler, "
                   "Eisflaschen, Nacht-Wasserwechsel.",
    })
```


### U-003: Biofilm-Risiko bei Rezirkulationssystemen nicht als eigenstaendiger Alert [BEHOBEN]

**Anbaukontext:** Hydroponik/Soilless (Rezirkulation)

**Fehlende Parameter:** Biofilm-Risikobewertung

**Begruendung:** Biofilm (bakterielle/pilzliche Belaege in Leitungen, Pumpen und Tanks) ist eines der groessten Probleme in rezirkulierenden Hydroponik-Systemen. Biofilm bietet *Pythium*, *Fusarium* und anderen Wurzelpathogenen einen geschuetzten Lebensraum und macht UV-Sterilisation und H2O2-Behandlung weniger wirksam. Das Biofilm-Risiko korreliert mit:
- Loesung mit organischen Bestandteilen (Huminsaeure, Fulvinsaeure, Komposttee)
- Hohe Wassertemperatur (>22 Grad C)
- Fehlende UV-Sterilisation oder Ozon
- Langer Loesungswechsel-Intervall

Das aktuelle System warnt nur bei "nicht-tanksicheren" Duengern beim Einfuellen (Zeile 1003), aber nicht bei der *Kombination* mehrerer Risikofaktoren, die Biofilm foerdern.

**Formulierungsvorschlag:** Neuer Alert-Typ `biofilm_risk`:
```python
if tank_type == 'recirculation':
    risk_score = 0
    if current_state.get('water_temp_celsius', 0) > 22:
        risk_score += 1
    if not tank.get('has_uv_sterilizer') and not tank.get('has_ozone_generator'):
        risk_score += 1
    if has_organics:
        risk_score += 2  # Organische Additive erhoehen Biofilm-Risiko stark
    if age_hours > 120:
        risk_score += 1
    if risk_score >= 3:
        alerts.append({
            'type': 'biofilm_risk',
            'severity': 'high',
            'message': "Erhöhtes Biofilm-Risiko in Rezirkulationssystem. "
                       "Kombination aus [Faktoren]. Enzymatischen Reiniger einsetzen "
                       "oder Wasserwechsel-Intervall verkürzen.",
        })
```


### U-004: Fehlende Unterstuetzung fuer Stammloesung-Tanks (Concentrated Stock Solutions) [BEHOBEN]

**Anbaukontext:** Hydroponik/Soilless, Indoor

**Fehlende Parameter:** Tank-Typ fuer konzentrierte Stammloesungen (A/B-Tanks)

**Begruendung:** In professionelleren Indoor-Setups und insbesondere bei automatisierter Duengung (REQ-018) werden konzentrierte Stammloesungen (100x-200x) in separaten kleinen Tanks vorgehalten, die dann ueber Dosierpumpen in den Mischtank dosiert werden. Diese Stammloesung-Tanks haben voellig andere Anforderungen:
- EC-Werte von 50-200 mS/cm (weit ueber dem aktuellen Limit von 10 mS/cm!)
- pH kann extrem sein (A-Tank oft pH 2-3, B-Tank oft pH 4-5)
- Volumen typisch 5-25L (klein)
- Mischung von A+B im Konzentrat ist VERBOTEN (Ausfaellung!)
- Fuellstand-Tracking ist kritisch fuer Nachbestellungs-Planung

Das aktuelle TankType-Enum (nutrient, irrigation, reservoir, recirculation) deckt diesen Anwendungsfall nicht ab.

**Formulierungsvorschlag:** Neuer Tank-Typ `stock_solution` mit angepassten Grenzwerten:
```python
class TankType(str, Enum):
    NUTRIENT = "nutrient"
    IRRIGATION = "irrigation"
    RESERVOIR = "reservoir"
    RECIRCULATION = "recirculation"
    STOCK_SOLUTION = "stock_solution"  # NEU: Konzentrierte Stammlösung (A/B)
```
Mit angepassten Validierungsgrenzen (EC bis 250 mS/cm, pH 1.0-14.0) und einem Alert, wenn ein stock_solution-Tank direkt einer Location zugeordnet wird (muss immer ueber feeds_from-Kaskade laufen).

**Hinweis:** Dies kann auch als zukuenftiges Feature behandelt werden, sollte aber im Datenmodell bereits vorgesehen sein (erweiterbare TankType-Enum). Falls nicht im aktuellen Scope: Mindestens einen Hinweis im Dokument, dass konzentrierte Stammloesungen ausser Scope sind.


### U-005: WateringEvent fehlt Substrattyp-Kontext fuer sinnvolle Drain-Bewertung [BEHOBEN]

**Anbaukontext:** Indoor, Hydroponik/Soilless

**Fehlende Parameter:** Substrattyp oder Drain-to-Waste-Prozentsatz im WateringEvent oder als Referenz

**Begruendung:** Die `runoff_ec_ms` und `runoff_ph` Felder im WateringEvent (Zeile 602-603) sind nur sinnvoll interpretierbar, wenn der Substrattyp bekannt ist:
- **Coco (Drain-to-Waste):** 10-30% Drain ist normal und gewuenscht. Runoff-EC sollte idealerweise nicht mehr als 0.3-0.5 mS/cm ueber Input-EC liegen.
- **Steinwolle:** Drain-EC kann im Tagesverlauf stark schwanken (morgens hoher, abends niedriger).
- **Erde:** Kaum messbarer Drain, Runoff-EC ist stark gepuffert durch CEC.
- **Hydroponik (NFT/DWC):** Kein Drain, Runoff-Konzept nicht anwendbar.

Die Methode `validate_volume_per_slot` (Zeile 1075) referenziert bereits `slot_substrate_volume_liters`, aber das WateringEvent selbst hat keine Information ueber den Substrattyp, um Runoff-Werte sinnvoll zu interpretieren.

**Formulierungsvorschlag:** Entweder:
1. Den Substrattyp ueber die Slot -> SubstrateBatch -> Substrate-Kette im Service aufloesen (empfohlen, keine Modell-Aenderung noetig), ODER
2. Ein optionales `substrate_type`-Feld im WateringEvent fuer Denormalisierung (schnellere Auswertung)

Zusaetzlich: Runoff-Interpretation als Teil des Alert-Systems:
```python
# Runoff-EC-Analyse (substrat-abhaengig)
if runoff_ec > input_ec + 0.5 and substrate_type in ('coco', 'rockwool_slab'):
    warnings.append("Runoff-EC deutlich über Input — Salzakkumulation im Substrat. "
                     "Flush-Event oder erhöhtes Drain-Volumen empfohlen.")
```


### U-006: Fehlende Beruecksichtigung der Wassertemperatur bei Top-Up [BEHOBEN]

**Anbaukontext:** Hydroponik/Soilless

**Fehlende Parameter:** Wassertemperatur des Nachfuellwassers

**Begruendung:** Beim Auffuellen eines warmen Tanks mit kaltem Osmosewasser (oder umgekehrt) kann ein Temperaturschock der Wurzeln resultieren. Wenn z.B. ein 50L-Tank mit 22 Grad C Loesungstemperatur mit 15L kaltem Osmosewasser (8 Grad C) aufgefuellt wird, sinkt die Temperatur auf ~18.6 Grad C -- das ist noch akzeptabel. Aber bei groesseren Nachfuellmengen oder extremeren Temperaturdifferenzen kann die resultierende Mischtemperatur problematisch werden.

**Formulierungsvorschlag:** Optionales Feld `water_temperature_celsius` im TankFillEvent und Plausibilitaets-Check:
```python
# Im record_fill_event:
if (fill_event.water_temperature_celsius is not None
    and current_state.get('water_temp_celsius') is not None):
    temp_diff = abs(fill_event.water_temperature_celsius - current_state['water_temp_celsius'])
    if temp_diff > 5:
        warnings.append(
            f"Temperaturdifferenz {temp_diff:.1f}°C zwischen Nachfüllwasser "
            f"({fill_event.water_temperature_celsius}°C) und Tanklösung "
            f"({current_state['water_temp_celsius']}°C). Wurzelschock möglich."
        )
```


---

## GELB -- Zu Ungenau -- Praezisierung noetig

### P-001: Loesungsalter-Schwellenwerte zu vereinfacht [BEHOBEN]

**Vage Anforderung:** "Automatische Warnung nach 5 Tagen (mit Organik) / 10 Tagen (mineralisch) -- Chelat-Degradation" (`REQ-014_Tankmanagement.md`, ~Zeile 81)

**Problem:** Die pauschalen Loesungsalter-Grenzen ignorieren wesentliche Einflussfaktoren:
- **Temperatur:** Chelat-Degradation (besonders Fe-DTPA und Fe-EDTA) beschleunigt sich exponentiell mit Temperatur. Bei 30 Grad C ist Fe-DTPA nach 3-4 Tagen signifikant degradiert, bei 18 Grad C haelt es 10-14 Tage.
- **pH:** Bei pH >6.5 degradieren Eisenchelate deutlich schneller.
- **Licht:** UV-Licht (auch indirektes) beschleunigt den Chelat-Zerfall -- ein Tank ohne Deckel bei Lichtexposition hat kuerzere Haltbarkeit.
- **Chelattyp:** Fe-DTPA (stabil bis pH 7.0) vs. Fe-EDDHA (stabil bis pH 9.0) haben voellig unterschiedliche Haltbarkeiten.

**Messbare Alternative:** Temperatur-abhaengiges Loesungsalter:
```python
# Temperatur-korrigiertes Loesungsalter (Q10-Regel: 2x Degradation pro 10°C)
avg_temp = average_tank_temp_over_period  # aus TankState-Historie
temp_factor = 2 ** ((avg_temp - 20) / 10)  # Normalisiert auf 20°C Referenz
effective_age_hours = actual_age_hours * temp_factor

base_warning_hours = 120 if has_organics else 240  # 5 bzw. 10 Tage bei 20°C
if effective_age_hours > base_warning_hours:
    # Warnung mit temperaturbereinigtem Alter
```


### P-002: pH-Bereich fuer Irrigation-Tank zu weit gefasst [BEHOBEN]

**Vage Anforderung:** `'irrigation': (5.8, 6.8)` als pH-Bereich fuer Giesswasser-Tanks (`REQ-014_Tankmanagement.md`, ~Zeile 684)

**Problem:** Der pH-Bereich 5.8-6.8 ist fuer die meisten Substrate korrekt, aber fuer bestimmte Anwendungen zu ungenau:
- Erde mit hoher Pufferkapazitaet: pH 6.0-6.8 im Giesswasser ergibt Substrat-pH 6.2-7.0 (akzeptabel)
- Coco ohne Pufferung: pH 5.8-6.2 im Giesswasser ist optimal; pH 6.8 kann bereits zu Fe/Mn-Lockout fuehren
- Living Soil: pH 6.2-6.8 im Giesswasser; zu sauer (5.8) kann das Mikrobiom schaedigen

**Messbare Alternative:** Der pH-Bereich des Irrigation-Tanks sollte optional an den Substrattyp der versorgten Location gekoppelt werden koennen:
```python
PH_RANGES_BY_SUBSTRATE = {
    'irrigation_coco':    (5.8, 6.2),
    'irrigation_soil':    (6.0, 6.8),
    'irrigation_living_soil': (6.2, 6.8),
    'irrigation_default': (5.8, 6.8),
}
```


### P-003: Kalibrierungsintervall "alle 2-4 Wochen" zu pauschal [BEHOBEN]

**Vage Anforderung:** "Kalibrierung (calibration): EC-/pH-Sonden im Tank kalibrieren -- alle 2-4 Wochen" (`REQ-014_Tankmanagement.md`, ~Zeile 42)

**Problem:** Die notwendige Kalibrierungsfrequenz haengt stark von der Beanspruchung ab:
- Dauerhaft in Loesung getauchte Sonden: Alle 7-14 Tage (Membran-Verschmutzung, Referenzelektrolyt-Verduennung)
- Punktuelle Messung (Hand-pH-Meter): Alle 4-8 Wochen
- In organischer Loesung (Komposttee, organische Duenger): Alle 7 Tage (Proteine/Fette lagern sich auf Glasmembran ab)
- In Rezirkulationssystemen: Alle 7-14 Tage wegen hoeherem Verschmutzungsgrad

**Messbare Alternative:** Die Default-Wartungsintervalle fuer Kalibrierung sollten Tank-Typ-abhaengig sein (was teilweise bereits geschieht -- nutrient 14d, recirculation 14d). Zusaetzlich sollte die Sondenplatzierung (dauerhaft vs. punktuell) als Faktor beruecksichtigt werden.


### P-004: Algen-Risikowarnung nur bei Temperatur+Deckel, ignoriert Naehrstoffe und Licht [BEHOBEN]

**Vage Anforderung:** Algenwarnug bei "Tank ohne Deckel >22 Grad C" (`REQ-014_Tankmanagement.md`, ~Zeile 886-893)

**Problem:** Algenwachstum wird durch drei Faktoren getrieben, nicht nur durch zwei:
1. **Licht** (primaerer Treiber) -- ohne Licht keine Photosynthese, keine Algen
2. **Naehrstoffe** (besonders Nitrat und Phosphat) -- immer vorhanden in Naehrstofftanks
3. **Temperatur** (sekundaer, beschleunigt Wachstum)

Ein Tank MIT Deckel aber mit transparentem/transluzenten Material (z.B. weisses Plastik, das Licht durchlaesst) hat ebenfalls ein erhebliches Algenrisiko. Umgekehrt hat ein offener Tank in einem voellig dunklen Raum kein Algenrisiko.

**Messbare Alternative:** Algenrisiko-Score statt binaerer Warnung:
```python
algae_risk = 0
if not tank.get('has_lid'):
    algae_risk += 2
elif tank.get('material') in ('glass', 'plastic'):
    algae_risk += 1  # Transparentes Material laesst Licht durch
if water_temp > 22:
    algae_risk += 1
if water_temp > 28:
    algae_risk += 1
if tank_type in ('nutrient', 'recirculation'):
    algae_risk += 1  # Naehrstoffe immer vorhanden
# Warnung ab Risiko-Score >= 3
```

Zusaetzliche Empfehlung: Im Tank-Modell ein optionales Feld `is_light_proof: bool` (lichtdicht) ergaenzen, das praeziser als `has_lid` ist.


### P-005: Seed-Daten -- Top-Up ohne CalMag bei Osmosewasser in Coco ist ein Praxisfehler [BEHOBEN]

**Vage Anforderung:** Seed-Daten `fill_zelt1_002` zeigt Top-Up mit Flora Micro + Flora Bloom, aber ohne CalMag (`REQ-014_Tankmanagement.md`, ~Zeile 1342)

**Problem:** Bei Coco-Substrat und Osmosewasser als Basis ist CalMag bei *jedem* Nachfuellen essentiell, nicht nur beim Vollwechsel. Coco hat eine hohe Kationenaustauschkapazitaet (CEC 40-100 meq/100g) und bindet selektiv Kalzium und Magnesium, waehrend es Natrium und Kalium freisetzt. Ohne CalMag bei jedem Top-Up entsteht ein zunehmender Ca/Mg-Mangel im Wurzelraum.

Die Seed-Daten suggerieren fuer Anfaenger, dass CalMag nur beim Vollwechsel noetig ist. Das ist ein haeufiger Praxisfehler mit dem Resultat: Braune Blattspitzen (Ca-Mangel) und Intervenalchlorose (Mg-Mangel) ab Woche 3-4.

**Messbare Alternative:** Korrektur der Seed-Daten:
```json
{
  "_key": "fill_zelt1_002",
  "fertilizers_used": [
    {"product_name": "CalMag", "ml_per_liter": 0.5, "product_key": "fert_calmag"},
    {"product_name": "Flora Micro", "ml_per_liter": 1.5, "product_key": "fert_micro"},
    {"product_name": "Flora Bloom", "ml_per_liter": 2.0, "product_key": "fert_bloom"}
  ]
}
```
Reduktion der CalMag-Dosis auf 0.5 ml/L beim Top-Up (vs. 1.0 ml/L beim Vollwechsel) ist fachlich korrekt, da die bestehende Loesung bereits CalMag enthaelt.


---

## GRUEN -- Hinweise und Best Practices

### H-001: Hervorragende Differenzierung der Tanktypen

Die Aufteilung in nutrient, irrigation, reservoir und recirculation mit jeweils angepassten Schwellenwerten fuer pH, EC, Temperatur und DO ist fachlich exzellent. Besonders positiv:
- Engerer pH-Bereich fuer Rezirkulation (5.5-6.3 statt 5.5-6.5) -- korrekt wegen schnellerer pH-Drift
- Strenger Temperatur-Grenzwert fuer Rezirkulation (25 Grad C statt 26 Grad C) -- korrekt wegen systemweitem Infektionsrisiko
- ORP-Ueberwachung fuer Rezirkulation -- professionelles Feature, das oft fehlt


### H-002: Tank-Safety-Konzept fuer organische Duenger ist praxisnah

Die Trennung zwischen tank-sicherer Fertigation und manueller Ergaenzungsduengung per Giesskanne (WateringEvent mit `is_supplemental=true`) bildet ein reales Praxisbeduerfnis ab. Viele Gaertner kombinieren mineralische Basis-Ernaehrung ueber Tropfer mit gelegentlicher organischer Ergaenzung per Hand. Die Warnung bei `tank_safe=false` und der Vorschlag einer alternativen Applikationsmethode ist ein sehr gutes UX-Pattern.


### H-003: Chlor-Warnung bei biologischen Additiven

Die Erkennung von Chlor >0.5 ppm in Kombination mit Mykorrhiza/Trichoderma/Bacillus und die Empfehlung zur Entchlorung ist ein wichtiges Feature, das in den meisten vergleichbaren Systemen fehlt. Die String-basierte Erkennung (`'myko' in name.lower()`) ist pragmatisch, sollte aber langfristig durch das `type: 'biological'`-Feld aus REQ-004 ergaenzt werden fuer zuverlaessigere Erkennung.


### H-004: Befuellungshistorie mit unveraenderlichem Duenger-Snapshot

Das Konzept, Duenger-Dosierungen als FertilizerSnapshot unabhaengig vom Quell-Dokument zu speichern, ist architektonisch korrekt. Wenn ein Duenger-Produkt spaeter aktualisiert wird (z.B. neue NPK-Werte), bleiben historische Records konsistent. Dies ist fuer Rueckverfolgbarkeit und Problemdiagnose ("Was habe ich damals wirklich verwendet?") essentiell.


### H-005: Empfehlung fuer zukuenftige Erweiterungen

1. **Nutrient Ratio Tracking in Rezirkulation:** In geschlossenen Systemen veraendert sich das Naehrstoff-Verhaeltnis ueber die Zeit ungleichmaessig (Pflanzen nehmen z.B. mehr N als P auf). Eine Erweiterung um ionenspezifische Sensorik (NO3, NH4, K, Ca) wuerde gezielte Nachdosierung einzelner Elemente ermoeglichen.

2. **Automatische Wasserwechsel-Empfehlung basierend auf EC-Drift-Rate:** Statt fixer 7-Tage-Intervalle koennte das System den optimalen Wechselzeitpunkt aus der EC-Drift-Rate berechnen (langsamer Drift = laengeres Intervall moeglich).

3. **Integration mit REQ-018 Aktorik:** Automatische pH-Korrektur ueber Dosierpumpen und automatisches Top-Up basierend auf Fuellstandssensoren -- die Tank-Datenstruktur ist dafuer bereits gut vorbereitet.


---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|---------------------|-----------|
| pH (nach Tank-Typ) | JA | nutrient 5.5-6.5, recirc 5.5-6.3, irrig 5.8-6.8 | Hoch |
| EC (mS/cm) | JA | Relativ zu Ziel-EC, abs. Fallback 3.5 mS | Hoch |
| Wassertemperatur (Grad C) | JA | 18-22 Grad C optimal (nutrient/recirc) | Hoch |
| DO (mg/L) | JA | >6 mg/L optimal, <4 mg/L kritisch | Hoch |
| ORP (mV) | JA | >700 mV steril, <250 mV pathogen | Mittel |
| Fuellstand (%) | JA | Warnung <20% | Hoch |
| Chlor/Chloramin (ppm) | TEILWEISE | <0.5 ppm bei Biologicals -- Typ-Unterscheidung fehlt | Mittel |
| Alkalitaet (ppm CaCO3) | JA | Fuer pH-Drift-Vorhersage | Niedrig |
| EC-Drift-Richtung | NEIN | Steigend/Fallend als diagnostisches Signal | Hoch |
| Loesungstemperatur Nachfuellwasser | NEIN | Delta <5 Grad C zum Tankinhalt | Mittel |
| Biofilm-Risiko-Score | NEIN | Multifaktoriell (Temp, Organik, UV, Alter) | Mittel |
| Substrattyp-Kontext fuer Runoff | NEIN | Ueber Slot-Relation aufloesbar | Mittel |
| Lichtdichtheit des Tanks | NEIN | Relevant fuer Algenrisiko | Niedrig |

---

## Konsistenz mit referenzierten Anforderungen

### Konsistenz mit REQ-004 (Duenge-Logik) -- GUT

- `ApplicationMethod`-Enum ist identisch (fertigation, drench, foliar, top_dress)
- `FertilizerSnapshot` konsistent mit Fertilizer-Modell
- `tank_safe`-Flag wird korrekt referenziert
- `mixing_result_key` und `nutrient_plan_key` als optionale Referenzen sind konsistent
- `base_water_ec_ms` und `base_water_alkalinity_ppm` konsistent mit NutrientSolutionCalculator
- `is_supplemental`-Flag konsistent in WateringEvent und FeedingEvent

**Einzige Inkonsistenz:** FertilizerSnapshot in REQ-014 hat `ml_per_liter` als einzige Dosierungsangabe. Fuer `top_dress`-Applikationen (Feststoffe) waere `g_per_liter` oder `g_per_plant` angemessener. REQ-004 hat dieses Problem ebenfalls -- es sollte in beiden Specs konsistent geloest werden.

### Konsistenz mit REQ-019 (Substratverwaltung) -- GUT

- REQ-019 verweist korrekt auf REQ-014 fuer substratlose Systeme (`none` -> Tank mit Typ `nutrient`)
- Kein `hydro_solution`-Substrattyp mehr -- klare Abgrenzung
- `irrigation_strategy`-Mapping in REQ-019 ist komplementaer zum Tank-Konzept
- `cec_meq_per_100g` in REQ-019 ist relevant fuer Spaelberechnung, wird aber in REQ-014 nicht referenziert (akzeptabel, da REQ-004 diese Bruecke schlaegt)

### Konsistenz mit REQ-002 (Standortverwaltung) -- GUT

- `irrigation_system`-Literal (`manual`, `drip`, `hydro`, `mist`) wird korrekt fuer Pflichtvalidierung verwendet
- Korrekte Anmerkung in REQ-002 (Zeile 58), dass ergaenzendes manuelles Giessen immer moeglich ist
- `has_tank`-Edge konsistent mit Location-Modell

### Konsistenz mit REQ-005 (Sensorik) -- GUT

- `source`-Literal (`manual`, `sensor`, `home_assistant`) in TankState ist identisch mit REQ-005 Hybrid-Modell
- Hydro-Parameter (Fuellstand, Wassertemperatur, DO, TDS) sind in REQ-005 bereits als Sensor-Typen definiert

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| DO-Saettigung nach Temperatur/Salinitat | USGS Water Resources | water.usgs.gov |
| Eisenchelat-Stabilitaet | Lindsay (1979), Lindsay & Schwab | -- |
| Pythium-Management Hydroponik | Sutton et al., Plant Disease | -- |
| ORP-Werte fuer Wasserdesinfektion | WHO Guidelines for Drinking-water Quality | who.int |
| Chlor/Chloramin-Entfernung | AWWA (American Water Works Association) | awwa.org |
| Rezirkulations-Naehrstoffdynamik | Savvas et al. (2009), Scientia Horticulturae | -- |
| CEC und Substrat-Naehrstoffbindung | Abad et al. (2001), Acta Horticulturae | -- |

---

## Glossar (REQ-014-spezifisch)

- **DO (Dissolved Oxygen):** Geloester Sauerstoff in mg/L -- entscheidend fuer aerobe Wurzelatmung in Hydroponik. Sinkt mit steigender Temperatur und steigendem Salzgehalt (Salting-Out-Effekt).
- **ORP (Oxidation-Reduction Potential):** Redoxpotenzial in mV -- Indikator fuer Sterilisationseffektivitaet in Rezirkulationssystemen. >700 mV = effektive Desinfektion.
- **Chelat-Degradation:** Zerfall von Metallkomplexen (z.B. Fe-DTPA, Fe-EDTA) in Naehrstoffloesung -- fuehrt zu Eisenmangel trotz ausreichender Gesamtkonzentration. Beschleunigt durch Waerme, Licht und hohen pH.
- **Biofilm:** Bakterielle/pilzliche Belaege auf Oberflaechen in Kontakt mit Naehrstoffloesung -- bietet Pathogenen geschuetzten Lebensraum und reduziert Wirksamkeit von UV/Ozon.
- **Salting-Out-Effekt:** Reduktion der Gasloeslichkeit (hier: O2) durch geloeste Salze in der Naehrstoffloesung.
- **EC-Drift:** Zeitliche Veraenderung der elektrischen Leitfaehigkeit in einer Naehrstoffloesung durch Pflanzenaufnahme, Verdunstung oder chemische Reaktionen.
- **CalMag-Pufferung:** Vorbehandlung von Coco-Substrat mit Kalzium/Magnesium-Loesung, um die CEC-Bindungsplaetze zu saettigen und Naehrstoff-Lockout zu verhindern.
- **Drain-to-Waste:** Offenes Bewaesserungssystem, bei dem ueberschuessige Naehrstoffloesung abfliesst und nicht rezirkuliert wird. Typisch 10-30% des Giessvolumens.
