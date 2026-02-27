# Agrarbiologisches Anforderungsreview -- REQ-017 Vermehrungsmanagement

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Indoor-Anbau, Hydroponik, geschuetzter Anbau, Vermehrungsmanagement
**Analysierte Dokumente:**
- `spec/req/REQ-017_Vermehrungsmanagement.md` (Hauptdokument)
- `spec/req/REQ-001_Stammdatenverwaltung.md` (Taxonomie, Veredelungs-Referenz)
- `spec/req/REQ-003_Phasensteuerung.md` (Phasen-Integration)
- `spec/req/REQ-013_Pflanzdurchlauf.md` (Batch-Integration)
- `spec/req/REQ-004_Duenge-Logik.md` (Naehrstoff-Kontext)
- `spec/req/REQ-010_IPM-System.md` (Pflanzenschutz-Kontext)
- `spec/req/REQ-019_Substratverwaltung.md` (Substrat-Kontext)
- `spec/req/REQ-002_Standortverwaltung.md` (Standort-Kontext)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Grundlagenwissen solide; einige biologisch ungenaue/fehlende Details |
| Indoor-Vollstaendigkeit | 4/5 | Gute Abdeckung Indoor-Vermehrung; Umgebungsparameter koennten tiefer gehen |
| Zimmerpflanzen-Abdeckung | 2/5 | Stark auf Nutzpflanzen (Cannabis, Tomate, Basilikum) fokussiert; Zimmerpflanzen-Vermehrung fehlt fast vollstaendig |
| Hydroponik-Tiefe | 3/5 | Aeroponik-Kloner erwaehnt; DWC-Kloner und NFT-Propagation fehlen; EC/pH der Naehrloesungen nicht betrachtet |
| Messbarkeit der Parameter | 4/5 | PPFD, Temperatur, Luftfeuchtigkeit in Protokollen vorhanden; VPD fehlt |
| Praktische Umsetzbarkeit | 4/5 | Technisch gut strukturiert; einige biologische Vereinfachungen bei genetischer Drift und Veredelungs-Kompatibilitaet |

**Gesamteinschaetzung:**
REQ-017 ist ein fachlich fundiertes und technisch gut durchdachtes Dokument fuer die Vermehrung von Nutzpflanzen im Indoor-Bereich. Die Modellierung der Abstammungslinie ueber ArangoDB-Graphen, die Mutterpflanzen-Ueberwachung und das Bewurzelungsprotokoll-System sind praxisnah und bilden reale Workflows korrekt ab. Biologisch relevante Schwaechen liegen in der uebermaessigen Vereinfachung des Konzepts "genetische Drift" bei klonaler Vermehrung (korrekt waere "somatische Mutation" und "epigenetische Drift"), dem Fehlen von VPD als zentralem Bewurzelungsparameter, und einer zu vereinfachten Veredelungs-Kompatibilitaetspruefung. Der Zimmerpflanzen-Anbaukontext (Orchideen-Vermehrung, Sukkulenten-Blattstecklinge, Rhizomteilung tropischer Pflanzen) ist trotz des "Fokus: Beides" im Header nahezu nicht vertreten.

---

## Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: "Genetische Drift" bei klonaler Vermehrung ist ein terminologischer Fehler

**Anforderung:** "Generationszaehler: Wie viele Generationen von Klonen bereits existieren (genetische Drift-Warnung ab Generation 10+)" (`REQ-017`, ~Zeile 32)
**Problem:** Genetische Drift (genetic drift) ist ein populationsgenetisches Phaenomen -- die zufaellige Verschiebung von Allelfrequenzen in kleinen Populationen ueber sexuelle Generationen hinweg. Bei klonaler (vegetativer) Vermehrung gibt es definitionsgemaess keine Rekombination und damit keine genetische Drift im populationsgenetischen Sinne.

Was bei Klonlinien tatsaechlich auftritt, sind:
1. **Somatische Mutationen** -- Punktmutationen in mitotisch sich teilenden Zellen, die sich bei vegetativer Vermehrung akkumulieren koennen. Die Frequenz liegt bei etwa 10^-7 bis 10^-6 pro Basenpaar pro Zellteilung. Ueber viele Klon-Generationen koennen sich diese akkumulieren (bekannt bei Weinreben, Obstbaeumen, Kartoffeln).
2. **Epigenetische Drift** -- Veraenderungen im DNA-Methylierungsmuster ohne Sequenzaenderung, die den Phaenotyp beeinflussen (z.B. veraenderte Blattform, reduzierte Vitalitaet).
3. **Virus-Akkumulation** -- Schleichende Virustiter-Erhoehung ueber Klon-Generationen (insbesondere Viroide bei Kartoffel, Tomato Mosaic Virus), die zu Leistungsabfall fuehrt und oft faelschlich als "Alterserscheinung" der Klonlinie interpretiert wird.

Die Warnschwelle "Generation 10+" ist zudem willkuerlich und nicht durch Literatur belegt. Cannabis-Klonlinien werden in der kommerziellen Produktion routinemaessig ueber 50+ Generationen gefuehrt, ebenso Kartoffelsorten (hunderte Klon-Generationen). Probleme entstehen typischerweise durch mangelnde Hygiene (Virusinfektionen) oder ungenuegend kontrollierte Vermehrungsbedingungen, nicht durch eine inherente Generationsgrenze.

**Korrekte Formulierung:**
```
- Generationszaehler: Tracking der Klon-Generation (0 = Saemling/Ur-Mutter)
- Warnung bei somatischer Mutationslast:
  - Ab Generation 5: Hinweis "Phaenotyp-Monitoring empfohlen -- somatische Mutationen moeglich"
  - Ab Generation 15: Warnung "Meristem-Reinigung oder Neustart aus Samen empfohlen"
  - Schwellenwerte muessen als konfigurierbare Spezies-Parameter gespeichert werden,
    da die Mutationsrate spezies-abhaengig ist
- Virus-Screening-Empfehlung: Unabhaengig von Generation, periodisch (konfigurierbar)
```
**Gilt fuer Anbaukontext:** Indoor, Gewaechshaus, alle Vermehrungskontexte

---

### F-002: Veredelungs-Kompatibilitaet "gleiche Familie = moeglicherweise kompatibel" ist zu vereinfacht

**Anforderung:** "Innerhalb derselben Familie: moeglicherweise kompatibel (z.B. Tomate auf Kartoffel-Unterlage)" (`REQ-017`, ~Zeile 68)
**Problem:** Die Kompatibilitaet innerhalb einer Pflanzenfamilie variiert drastisch und ist auf taxonomischer Ebene nicht zuverlaessig vorhersagbar. Beispiele:

- **Solanaceae:** *Solanum lycopersicum* auf *S. melongena* (Aubergine) funktioniert (gleiche Gattung), aber *Capsicum annuum* (Paprika) auf *Solanum* funktioniert in der Praxis schlecht trotz gleicher Familie.
- **Rosaceae:** *Malus* (Apfel) auf *Pyrus* (Birne) funktioniert trotz verschiedener Gattungen (Unterfamilie Maloideae).
- **Cucurbitaceae:** *Cucumis sativus* (Gurke) auf *Cucurbita* (Kuerbis) ist Standard-Praxis in der kommerziellen Produktion trotz verschiedener Gattungen.
- **Fabaceae:** Veredelung ist hier kaum moeglich trotz riesiger Familie.

Die binaere Logik (same_genus = compatible, same_family = possibly_compatible, else = incompatible) bildet die Realitaet unzureichend ab.

**Korrekte Formulierung:**
```
Veredelungs-Kompatibilitaet sollte als Graph-Edge modelliert werden:
- Neue Edge-Collection: `graft_compatible_with: Species -> Species`
  - Properties: {compatibility_level: 'proven' | 'experimental' | 'incompatible',
                 success_rate_literature: Optional[float],
                 notes: str,
                 source: str}
- Fallback-Heuristik wenn kein expliziter Edge existiert:
  1. Gleiche Gattung: "wahrscheinlich kompatibel" (nicht garantiert!)
  2. Gleiche Unterfamilie (subfamily): "moeglicherweise kompatibel"
  3. Gleiche Familie: "experimentell, Literatur pruefen"
  4. Verschiedene Familien: "inkompatibel"
- Seed-Daten fuer bekannteste Veredelungskombinationen:
  - Tomate (S. lycopersicum) auf Tomaten-Unterlage (S. lycopersicum): proven
  - Tomate auf Aubergine (S. melongena): proven
  - Gurke (Cucumis sativus) auf Kuerbis (Cucurbita maxima x moschata): proven
  - Melone (Cucumis melo) auf Kuerbis: proven
  - Paprika (Capsicum) auf Capsicum-Unterlage: proven
```
**Gilt fuer Anbaukontext:** Gewaechshaus, Indoor, Outdoor

---

### F-003: Basilikum (*Ocimum basilicum*) ist keine Kurztagspflanze

**Anforderung:** "GIVEN: Basilikum (Ocimum basilicum) als einjaehrige Kurztagspflanze" (`REQ-001`, Testszenario 1, referenziert in REQ-017 Kontext)
**Problem:** *Ocimum basilicum* ist fakultativ tagneutral (quantitative long-day plant in manchen Quellen). Die Bluete wird nicht primaer durch Taglaenge gesteuert, sondern durch Temperatur und Alter. Unter Indoor-Bedingungen blueht Basilikum bei jeder Photoperiode, wenn die Pflanze genuegend entwickelt ist. Die Einstufung als "Kurztagspflanze" ist botanisch falsch.

**Korrekte Formulierung:**
```
Basilikum (Ocimum basilicum): tagneutral (day_neutral)
Bluetenbildung primaer abhaengig von:
- Pflanzenalter (Wochen nach Keimung, spezies-/sortenabhaengig)
- Temperatursumme (GDD-basiert)
- Nicht primaer photoperiodisch gesteuert
```
**Gilt fuer Anbaukontext:** Indoor, Gewaechshaus, Outdoor

---

### F-004: Generationsberechnung bei Aussaat (seed_sowing) ist konzeptionell inkorrekt

**Anforderung:** `calculate_generation()` gibt fuer `seed_sowing` denselben Wert wie fuer `cutting` zurueck: `mother_generation + 1` (`REQ-017`, ~Zeile 797-799)
**Problem:** Die Generationszaehlung bei sexueller vs. vegetativer Vermehrung folgt unterschiedlichen Konventionen:

- **Vegetativ (Klon):** Selbe Genotyp-Generation. Klon-Generation !=  genetische Generation. Ein Klon ist genetisch identisch mit der Mutter (minus somatische Mutationen). Die Zaehlung "+1" ist eine reine Tracking-Konvention.
- **Sexuell (Samen/Kreuzung):** Echte genetische Generation. F1, F2, F3 etc. Jede Generation hat neuen Genotyp durch Rekombination. P (Eltern) -> F1 -> F2 ist die korrekte Zaehlung.

Die Funktion behandelt beides gleich, was biologisch falsch und fuer Zuechtungs-Tracking unbrauchbar ist.

**Korrekte Formulierung:**
```python
def calculate_generation(
    self,
    parents: list[dict],  # [{generation: int, relationship: str}, ...]
    method: str,
) -> tuple[int, str]:
    """
    Berechnet Generation und Generations-Typ.
    Returns: (generation_number, generation_type)
    """
    if method in ('cutting', 'division', 'layering', 'tissue_culture'):
        # Klonale Generation: Tracking-Zaehler, keine genetische Bedeutung
        mother = next(p for p in parents if p['relationship'] != 'rootstock')
        return mother['generation'] + 1, 'clonal'

    elif method == 'seed_sowing':
        # Sexuelle Generation: F1, F2 etc.
        # Wenn beide Eltern P (Generation 0): Nachkommen = F1 (Generation 1)
        # Wenn beide Eltern F1: Nachkommen = F2 (Generation 2)
        # Wenn Eltern verschiedene Generationen: hoechste + 1
        max_gen = max(p['generation'] for p in parents
                      if p['relationship'] in ('seed_mother', 'seed_father'))
        return max_gen + 1, 'filial'

    elif method == 'grafting':
        # Edelreis behaelt seine Generation
        scion = next(p for p in parents if p['relationship'] == 'scion')
        return scion['generation'], scion.get('generation_type', 'clonal')
```
**Gilt fuer Anbaukontext:** Alle -- besonders relevant fuer Zuchtprogramme Indoor

---

## Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: VPD (Vapor Pressure Deficit) fehlt als Bewurzelungsparameter

**Anbaukontext:** Indoor
**Fehlende Parameter:** VPD (kPa) im `PropagationEvent` und `RootingProtocol`
**Begruendung:** VPD ist der entscheidende Parameter fuer die Bewurzelungsphase, nicht Luftfeuchtigkeit allein. Ein Steckling ohne Wurzeln kann kaum Wasser aufnehmen und ist vollstaendig auf minimale Transpiration angewiesen. Das Zusammenspiel von Temperatur und Luftfeuchtigkeit bestimmt den Transpirationsdruck:

- **Optimaler VPD fuer Bewurzelung:** 0,2--0,5 kPa (sehr niedrig = kaum Transpiration)
- **VPD > 0,8 kPa:** Stecklinge welken, Bewurzelungsrate sinkt drastisch
- **VPD < 0,2 kPa:** Kondensation, Botrytis-Risiko, Damping-Off

Dome-Humidity allein (aktuell: `dome_humidity_percent`) ist ohne Temperaturangabe nicht aussagekraeftig. Bei 85% rH und 22 Grad C ergibt sich ein VPD von ca. 0,40 kPa (gut), aber bei 85% rH und 28 Grad C ein VPD von ca. 0,57 kPa (grenzwertig).

**Formulierungsvorschlag:**
```python
# Ergaenzung in PropagationEvent und RootingProtocol:
target_vpd_kpa: Optional[float] = Field(None, ge=0.1, le=2.0,
    description="Ziel-VPD waehrend Bewurzelung (optimal: 0.2-0.5 kPa)")

# Berechnete Validierung:
@model_validator(mode='after')
def validate_vpd_consistency(self):
    """Warnung wenn VPD aus Temperatur+Humidity nicht im Zielbereich."""
    if self.dome_humidity_percent and self.heat_mat_celsius:
        # Tetens-Formel fuer Saettigungsdampfdruck
        es = 0.6108 * math.exp((17.27 * self.heat_mat_celsius) /
                                (self.heat_mat_celsius + 237.3))
        vpd = es * (1 - self.dome_humidity_percent / 100)
        if vpd > 0.8:
            logger.warning(f"VPD {vpd:.2f} kPa zu hoch fuer Bewurzelung")
    return self
```

---

### U-002: Temperaturzonen-Differenzierung bei Bewurzelung fehlt

**Anbaukontext:** Indoor
**Fehlende Parameter:** Differenzierung Luft- vs. Substrat-/Wurzelzonentemperatur
**Begruendung:** Das Feld `heat_mat_celsius` (Waermematte) gibt die Substrattemperatur an, aber die Lufttemperatur ist ein separater, ebenso kritischer Parameter. Fuer erfolgreiche Bewurzelung ist ein Temperaturgefaelle entscheidend:

- **Wurzelzone:** 22--25 Grad C (Optimum fuer Zellteilung und Kallusbildung)
- **Luft/Spross:** 20--22 Grad C (leicht kuehler als Wurzelzone)
- **Differenz:** Wurzelzone 2--4 Grad C waermer als Luft ist ideal ("Bottom Heat")

Ohne dieses Gefaelle bilden Stecklinge primaer Sprosswachstum statt Wurzeln.

**Formulierungsvorschlag:**
```python
# PropagationEvent / RootingProtocol ergaenzen:
heat_mat_celsius: Optional[float] = Field(None, ge=15, le=35,
    description="Substrattemperatur (Waermematte) -- Wurzelzonentemperatur")
air_temperature_celsius: Optional[float] = Field(None, ge=10, le=35,
    description="Lufttemperatur ueber dem Dome/um die Stecklinge")

# Validierung:
@model_validator(mode='after')
def validate_bottom_heat(self):
    if self.heat_mat_celsius and self.air_temperature_celsius:
        diff = self.heat_mat_celsius - self.air_temperature_celsius
        if diff < 0:
            logger.warning("Substrat kaelter als Luft -- Bottom Heat empfohlen")
        if diff > 8:
            logger.warning(f"Temperaturdifferenz {diff}C zu gross -- Risiko Wurzelfaeule")
    return self
```

---

### U-003: Zimmerpflanzen-Vermehrungsmethoden fehlen weitgehend

**Anbaukontext:** Zimmerpflanzen
**Fehlende Parameter:** Zahlreiche Vermehrungsmethoden, die im Zimmerpflanzenbereich standard sind
**Begruendung:** Das Dokument erwaehnt 6 Vermehrungsmethoden (`cutting, seed_sowing, division, layering, grafting, tissue_culture`), aber typische Zimmerpflanzen-Spezifika fehlen:

1. **Blattstecklinge (leaf_cutting):** Begonien, *Sansevieria*, Sukkulenten -- komplett andere Methodik als Triebstecklinge. Ein Blatt bildet an der Schnittflaeche Adventivwurzeln und -sprosse. Erfordert andere Parameter (kein Hormon noetig, laengere Bewurzelungszeit, hoehere Lichttoleranz).

2. **Kindel/Ableger (offsets):** *Chlorophytum* (Gruenlilie), *Aloe*, *Agave*, *Pilea peperomioides* -- Ableger, die von der Mutterpflanze natuerlich gebildet und bei genuegender Groesse abgetrennt werden. Kein Hormon, keine Dome-Humidity, minimaler Aufwand.

3. **Bulbillen/Brutknospen (bulbils):** Einige Liliengewaechse, *Kalanchoe* (Brutblatt) -- asexuelle Reproduktionskoerper.

4. **Stengel-/Stammstecklinge (stem_section):** *Dracaena*, *Dieffenbachia*, *Yucca* -- nicht Triebspitze, sondern Stammsegmente mit schlafenden Augen. Werden horizontal auf Substrat gelegt. Voellig andere Methodik als apikale Stecklinge.

5. **Wasserstecklinge (water_propagation):** *Pothos*, *Philodendron*, *Tradescantia* -- Standard-Zimmerpflanzen-Vermehrung. Das Medium "water" existiert zwar, aber ein Protokoll fuer Wasserglas-Vermehrung (kein Dome, Raumtemperatur, Wasserstandskontrolle) fehlt.

6. **Rhizomteilung:** *Calathea*, *Maranta*, *Zamioculcas* -- spezifischer als generische "division" (Rhizom, nicht Wurzelstock).

**Formulierungsvorschlag:**
```python
class PropagationMethod(str, Enum):
    CUTTING = "cutting"                 # Triebspitzen-Steckling (apikal)
    STEM_SECTION = "stem_section"       # Stammsegment-Steckling (nodal/internodal)
    LEAF_CUTTING = "leaf_cutting"       # Blattsteckling (Begonia, Sansevieria)
    SEED_SOWING = "seed_sowing"         # Aussaat
    DIVISION = "division"               # Teilung (Wurzelstock, Rhizom, Horst)
    OFFSET = "offset"                   # Kindel/Ableger (Chlorophytum, Aloe)
    LAYERING = "layering"               # Absenker
    AIR_LAYERING = "air_layering"       # Abmoosen (Ficus, Monstera) -- Indoor-Klassiker!
    GRAFTING = "grafting"               # Veredelung
    TISSUE_CULTURE = "tissue_culture"   # Gewebekultur
    BULBIL = "bulbil"                   # Brutknospe/Bulbille
```

Insbesondere **Abmoosen (air_layering)** ist eine der wichtigsten Indoor-Vermehrungsmethoden fuer grosse Zimmerpflanzen wie *Monstera deliciosa*, *Ficus elastica*, *Ficus lyrata* und wird aktuell nicht abgebildet.

---

### U-004: Bewurzelungshormon-Konzentrationsbereiche sind nicht spezies-/methodenspezifisch validiert

**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Spezies-spezifische Hormonkonzentrations-Empfehlungen und Warnungen
**Begruendung:** Das Feld `hormone_concentration_ppm` erlaubt 0--50000 ppm, was biologisch problematisch ist:

- **IBA fuer krautige Stecklinge (Tomate, Basilikum):** 500--1500 ppm (Pulver) oder 50--200 ppm (Loesungstauchverfahren). Bei >3000 ppm Phytotoxizitaet (Stengelbasis-Nekrose).
- **IBA fuer halbverholzte Stecklinge (Cannabis, Rosen):** 1000--3000 ppm.
- **IBA fuer verholzte Stecklinge (Obstbaeume):** 3000--8000 ppm.
- **NAA:** Generell niedrigere Konzentrationen als IBA, hoehere Phytotoxizitaet.
- **IBA+NAA-Mix:** Synergistischer Effekt, daher geringere Einzelkonzentrationen.

50000 ppm ist in keinem Szenario sinnvoll und wuerde jeden Steckling toeten.

**Formulierungsvorschlag:**
```python
hormone_concentration_ppm: Optional[float] = Field(None, ge=0, le=10000,
    description="Bewurzelungshormon-Konzentration in ppm")

# Validierung im PropagationEngine:
HORMONE_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    'iba': {
        'herbaceous': (500, 2000),     # Krautige Stecklinge
        'semi_woody': (1000, 4000),    # Halbverholzt
        'woody': (3000, 8000),         # Verholzt
    },
    'naa': {
        'herbaceous': (250, 1000),
        'semi_woody': (500, 2000),
        'woody': (1000, 4000),
    },
}
```

---

### U-005: IPM-Integration bei Vermehrung fehlt

**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Verbindung zwischen PropagationEvent und IPM-System (REQ-010)
**Begruendung:** Die Vermehrungsphase ist ein kritisches Fenster fuer Schaedlings- und Krankheitseintrag:

1. **Schnittwerkzeug-Hygiene:** Krankheitsuebertragung (Fusarium, TMV, Viroide) ueber kontaminierte Scheren/Messer ist der haeufigste Infektionsweg bei vegetativer Vermehrung. Das Dokument erwaehnt dies nicht.

2. **Damping-Off** ist als `failure_reason` korrekt erfasst, aber die Verknuepfung zu REQ-010 fehlt (welcher Erreger? Pythium, Rhizoctonia, Fusarium? Welche Bekaempfungsmassnahme?).

3. **Quarantaene-Phase:** Neue Stecklinge (insbesondere zugekaufte oder aus externer Quelle) sollten eine Quarantaene-Phase durchlaufen, bevor sie in den Bestand integriert werden. Fehlt als Konzept.

4. **Virus-Freiheits-Status:** Bei hochwertigen Mutterpflanzen (priority: "critical") sollte der Virus-Status dokumentiert werden. Virusfreie Mutterpflanzen sind ein Kernkonzept in der professionellen Vermehrung (virus-indexed stock).

**Formulierungsvorschlag:**
```python
# Ergaenzung in PropagationEvent:
tool_sterilization_method: Optional[Literal[
    'flame', 'alcohol_70', 'bleach_10', 'virkon', 'none'
]] = Field(None, description="Sterilisationsmethode fuer Schnittwerkzeug")
quarantine_required: bool = Field(default=False,
    description="Quarantaene-Phase vor Bestandsintegration")
quarantine_days: Optional[int] = Field(None, ge=1, le=30,
    description="Quarantaene-Dauer in Tagen")

# Ergaenzung in MotherPlantConfig:
virus_status: Optional[Literal[
    'untested', 'virus_indexed_clean', 'virus_detected', 'unknown'
]] = Field(default='untested',
    description="Virus-Freiheits-Status der Mutterpflanze")
last_virus_test_date: Optional[datetime] = None
```

---

### U-006: Stecklingstyp-Differenzierung fehlt

**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Stecklingstyp (apikal, nodal, internodal, Fersensteckling, etc.)
**Begruendung:** Verschiedene Stecklingstypen haben fundamental unterschiedliche Bewurzelungsraten und erfordern unterschiedliche Protokolle:

- **Apikal (Kopfsteckling):** Enthaelt das Apikalmeristem, hoechste Bewurzelungsrate bei den meisten Arten (hohe endogene Auxin-Produktion)
- **Nodal (Knotensteckling):** Stammsegment mit mindestens einem Knoten (Auge). Standard bei *Pothos*, *Philodendron*, *Monstera*
- **Internodal:** Stammsegment zwischen Knoten. Nur bei bestimmten Arten moeglich (z.B. *Dracaena*)
- **Fersensteckling (heel cutting):** Seitentrieb mit "Ferse" vom Hauptstamm. Hoehere Bewurzelungsrate bei schwer bewurzelbaren Arten
- **Laubholzsteckling / Hartholzsteckling:** Verholztes Material, laengere Bewurzelungszeit, andere Hormonkonzentrationen

**Formulierungsvorschlag:**
```python
class CuttingType(str, Enum):
    APICAL = "apical"           # Kopfsteckling mit Triebspitze
    NODAL = "nodal"             # Knotensteckling
    INTERNODAL = "internodal"   # Steckling zwischen Knoten
    HEEL = "heel"               # Fersensteckling
    SOFTWOOD = "softwood"       # Krautiger/weicher Trieb
    SEMI_HARDWOOD = "semi_hardwood"  # Halbverholzt
    HARDWOOD = "hardwood"       # Verholzt (Wintersteckling)

# Ergaenzung in PropagationEvent (nur wenn event_type == 'cutting'):
cutting_type: Optional[CuttingType] = None
node_count: Optional[int] = Field(None, ge=1, le=10,
    description="Anzahl Nodien am Steckling")
cutting_length_cm: Optional[float] = Field(None, ge=1, le=50,
    description="Stecklingslaenge in cm")
```

---

### U-007: Substrat-Integration bei Vermehrung fehlt

**Anbaukontext:** Indoor, Hydroponik
**Fehlende Parameter:** Verknuepfung zwischen `PropagationEvent.medium` und REQ-019 (Substratverwaltung)
**Begruendung:** Das Bewurzelungsmedium (`RootingMedium`) ist ein separates Enum ohne Verbindung zur Substratverwaltung (REQ-019). Dies fuehrt zu Inkonsistenzen:

1. Das Vermehrungsmedium wird nicht als `SubstrateBatch` getrackt, obwohl es einen pH-/EC-Wert und eine Qualitaet hat.
2. Steinwolle-Plugs fuer Stecklinge vs. Steinwolle-Slabs fuer die Produktion koennten ueber dieselbe Substrat-Infrastruktur verwaltet werden.
3. Die Uebergabe vom Vermehrungsmedium zum Produktionssubstrat (Transplant) ist nicht abgebildet.

**Formulierungsvorschlag:**
```python
# Optionale Verknuepfung:
medium_substrate_key: Optional[str] = Field(None,
    description="Referenz auf substrates._key (REQ-019) -- "
                "optional, fuer detailliertes Substrat-Tracking")
medium_ph: Optional[float] = Field(None, ge=3.0, le=9.0,
    description="pH des Bewurzelungsmediums bei Stecklingssetzung")
medium_ec_ms: Optional[float] = Field(None, ge=0.0, le=3.0,
    description="EC des Bewurzelungsmediums -- sollte niedrig sein (0.2-0.6 mS)")
```

---

### U-008: Lichtspektrum-Angaben fuer Bewurzelung fehlen

**Anbaukontext:** Indoor
**Fehlende Parameter:** Lichtspektrum (Blau-/Rot-Anteil) waehrend Bewurzelung
**Begruendung:** Das Feld `light_ppfd` gibt nur die Intensitaet an. Fuer die Bewurzelung ist das Lichtspektrum jedoch relevant:

- **Blaulicht-dominant (400-500 nm):** Foerdert kompakten Wuchs und Wurzelbildung bei Stecklingen. Hemmt Streckungswachstum, das Energie von der Bewurzelung abzieht.
- **Rotlicht-dominant (600-700 nm):** Foerdert Streckungswachstum und Photosynthese, aber kann bei Stecklingen zu Lasten der Wurzelbildung gehen.
- **Fernrot (730 nm):** Sollte minimiert werden waehrend der Bewurzelung (Phytochrom-Balance zugunsten von Pfr).

Professionelle Propagation-Stationen verwenden spezifische Spektren fuer die Bewurzelungsphase.

**Formulierungsvorschlag:**
```python
# Ergaenzung in RootingProtocol:
light_spectrum: Optional[Literal[
    'blue_dominant', 'balanced', 'red_dominant', 'full_spectrum', 'natural'
]] = Field(None,
    description="Empfohlenes Lichtspektrum waehrend Bewurzelung "
                "(blue_dominant empfohlen fuer vegetative Stecklinge)")
```

---

## Zu Ungenau -- Praezisierung noetig

### P-001: RootingProtocol `light_ppfd` ohne obere Grenzwertwarnung

**Vage Anforderung:** `light_ppfd: int = Field(ge=0, le=500)` (`REQ-017`, ~Zeile 663)
**Problem:** 500 umol/m2/s ist fuer unbewurzelte Stecklinge viel zu hoch. Stecklinge ohne funktionales Wurzelsystem koennen die Transpiration bei hoher Lichtintensitaet nicht ausgleichen und welken. Die obere Grenze sollte differenziert sein:

- Bewurzelung unter Dome: 50--150 umol/m2/s PPFD (optimal)
- Akklimatisierungsphase (Dome entfernt): 150--300 umol/m2/s
- > 300 umol/m2/s: Nur bei Pflanzen mit bereits etabliertem Wurzelsystem

**Messbare Alternative:**
```python
light_ppfd: int = Field(ge=0, le=300,
    description="Lichtintensitaet in umol/m2/s PPFD -- "
                "unter Dome: 50-150, Akklimatisierung: 150-300")
# Warnung in der Engine:
if protocol.dome_humidity_percent and protocol.dome_humidity_percent > 70:
    # Unter Dome: max 150 PPFD empfohlen
    if protocol.light_ppfd > 150:
        warnings.append("PPFD > 150 unter Dome -- Welkerisiko bei unbewurzelten Stecklingen")
```

---

### P-002: `mother_recovery_days` pauschal fuer alle Vermehrungsmethoden

**Vage Anforderung:** `mother_recovery_days: int = Field(default=14, ge=1, le=90)` (`REQ-017`, ~Zeile 549)
**Problem:** Die Erholungszeit haengt nicht nur von der Spezies ab, sondern auch von der Art und Intensitaet der Entnahme:

| Entnahme-Typ | Typische Erholung | Begruendung |
|-------------|-------------------|-------------|
| Apikaler Steckling | 14-21 Tage | Verlust der Apikaldominanz, Pflanze muss Seitentriebe foerdern |
| Seitentrieb (Geiztrieb, Tomate) | 5-7 Tage | Minimale Verletzung, wird ohnehin entfernt |
| Blattsteckling | 3-5 Tage | Einzelnes Blatt, geringer Stress |
| Stammsteckling (Monstera) | 21-30 Tage | Groessere Wundflaehe, Verholzung |
| Teilung | 14-30 Tage | Wurzelschock |

**Messbare Alternative:**
```python
# Erholungszeit als Methoden-spezifischer Wert:
mother_recovery_days: dict[str, int] = Field(
    default={'cutting': 14, 'division': 21, 'layering': 7},
    description="Erholungszeit in Tagen pro Vermehrungsmethode"
)
```

---

### P-003: Seed-Daten Bewurzelungsprotokolle nur fuer 3 Spezies

**Vage Anforderung:** 4 Seed-Protokolle: Cannabis, Tomate, Basilikum, generische Aussaat (`REQ-017`, ~Zeile 1030-1036)
**Problem:** Das System deklariert "Fokus: Beides" (Indoor + Outdoor), aber die Seed-Protokolle decken nur Cannabis, Tomate und Basilikum ab. Fuer ein Vermehrungsmanagement fehlen mindestens:

- **Zimmerpflanzen-Stecklinge:** *Monstera deliciosa*, *Philodendron*, *Pothos* (Epipremnum), *Ficus* (Abmoosen)
- **Kraeuterstecklinge:** Rosmarin (*Salvia rosmarinus*), Thymian, Lavendel -- alle halbverholzt, andere Methodik als Basilikum
- **Sukkulenten-Blattstecklinge:** *Echeveria*, *Crassula*, *Sedum* -- ohne Hormon, ohne Dome, langsame Bewurzelung
- **Veredelungs-Protokolle:** Tomaten-Veredelung auf Unterlage (wichtigste Veredelung indoor)

**Messbare Alternative:** Mindestens 8--10 Seed-Protokolle fuer die wichtigsten Vermehrungskategorien, nicht nur 4.

---

### P-004: Inzuchtkoeffizient-Berechnung (`calculate_inbreeding_coefficient`) biologisch vereinfacht

**Vage Anforderung:** Inzuchtkoeffizient basierend auf wiederkehrenden Vorfahren (`REQ-017`, ~Zeile 915-936)
**Problem:** Die Berechnung `repeated_ancestors / total_ancestors` ist keine anerkannte Methode zur Inzuchtschaetzung. Der Standard ist Wrights Inzuchtkoeffizient (F), der auf der Wahrscheinlichkeit basiert, dass zwei Allele an einem Locus von demselben Vorfahren stammen (Identity by Descent). Die vereinfachte Methode liefert keine vergleichbaren Werte und kann zu Fehl-Interpretationen fuehren.

**Messbare Alternative:** Entweder Wrights Pfadkoeffizient-Methode implementieren oder die Funktion explizit als "vereinfachte Verwandtschaftsschaetzung" (nicht Inzuchtkoeffizient) kennzeichnen und die Reparatur des Namens vornehmen:
```python
def calculate_relatedness_estimate(self, lineage_tree: dict) -> float:
    """
    Vereinfachte Verwandtschafts-Schaetzung basierend auf
    wiederkehrenden Vorfahren. KEIN Wright-Inzuchtkoeffizient (F).
    Dient als Indikator fuer genetische Vielfalt in Zuchtprogrammen.
    Werte > 0.25: Warnung wegen moeglicher Inzuchtdepression.
    """
```

---

## Hinweise & Best Practices

### H-001: Mykorrhiza-Inokulierung als Bewurzelungs-Booster

Professionelle Indoor-Vermehrung setzt zunehmend auf arbuskulaere Mykorrhiza-Pilze (AMF) als Bewurzelungshilfe. Dies ist als optionaler Parameter im Protokoll sinnvoll:
```python
mycorrhiza_inoculation: Optional[bool] = Field(default=False,
    description="Arbuskulaere Mykorrhiza-Inokulation bei Stecklingssetzung")
```
Studien zeigen 20--40% hoehere Bewurzelungsraten bei AMF-inokulierten Cannabis- und Tomaten-Stecklingen (Colla et al., 2015).

### H-002: Stecklingsqualitaet als Parameter dokumentieren

Die Qualitaet des Stecklingsmaterials ist der wichtigste Einflussfaktor auf die Bewurzelungsrate. Folgende Parameter sollten optional erfassbar sein:
- Stecklingslaenge (cm)
- Anzahl Nodien
- Blattzahl (ganz/halbiert)
- Position an der Mutterpflanze (apikal vs. basal vs. medial)
- Stengeldurchmesser (mm)
- Verholzungsgrad

### H-003: Umwelt-Logging waehrend der Bewurzelungsphase

Fuer die Optimierung der Bewurzelungsprotokolle ist ein automatisches Umwelt-Logging (via REQ-005 Sensorik) waehrend der Bewurzelungsphase wertvoll. Die Verknuepfung PropagationEvent -> Standort (Slot) -> Sensordaten (TimescaleDB) wuerde eine datengetriebene Protokoll-Optimierung ermoeglichen.

### H-004: Saison-Abhaengigkeit der Bewurzelungsrate

Auch indoor variieren Bewurzelungsraten saisonal, da Lichtqualitaet, Luftfeuchtigkeit und Pflanzenphysiologie durch die Jahreszeit beeinflusst werden:
- **Fruehling:** Hoechste natuerliche Auxin-Produktion, beste Bewurzelungsraten
- **Sommer:** Hoehere Temperaturen koennen VPD erhoehen, mehr Damping-Off
- **Herbst/Winter:** Reduzierte Wachstumsrate, laengere Bewurzelungszeiten
- Unter vollstaendig kontrolliertem Indoor-Klima (CEA) ist dieser Effekt reduziert, aber nicht eliminiert

Das RootingProtocol sollte optional eine Saison-Empfehlung enthalten.

### H-005: Batch-Groesse bei Kreuzungen (seed_sowing mit Vater)

Bei gezielten Kreuzungen (Szenario 6) ist die Erwartung, dass alle 20 Samen F1-Hybriden sind, nur korrekt, wenn die Bestaeubung kontrolliert war (Isolierung, Hand-Bestaeubung). Bei offener Bestaeubung koennen Selbstbestaeubungen oder Fremdbestaeubungen die Population verunreinigen. Das System sollte ein Feld `pollination_control: Literal['isolated', 'hand_pollinated', 'open_pollinated']` auf dem SeedSowingRequestValidator anbieten.

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|--------------------|-----------|
| PPFD (umol/m2/s) | Ja | 50-150 (Bewurzelung), 150-300 (Akklimatisierung) | Hoch |
| VPD (kPa) | NEIN | 0.2-0.5 kPa (Bewurzelung) | Hoch |
| Lufttemperatur (C) | NEIN (nur Waermematte) | 20-22 C (Luft) | Hoch |
| Substrattemperatur (C) | Ja (heat_mat) | 22-25 C | -- |
| Dome-Humidity (rH%) | Ja | 80-95% (Start), stufenweise senken | -- |
| EC Bewurzelungsmedium (mS/cm) | NEIN | 0.2-0.6 mS/cm | Mittel |
| pH Bewurzelungsmedium | NEIN | 5.5-6.5 (mediumabhaengig) | Mittel |
| Lichtspektrum | NEIN | Blau-dominant empfohlen | Mittel |
| Stecklingslaenge (cm) | NEIN | art-/methodenspezifisch | Niedrig |
| DLI (mol/m2/d) | NEIN | 2-5 mol/m2/d (Bewurzelung) | Niedrig |
| CO2 (ppm) | NEIN | ambient 400 ppm (Bewurzelung nicht CO2-limitiert) | Niedrig |

---

## Querverweise zu anderen REQs

### REQ-003 Phasensteuerung -- Integration

Die Abhaengigkeit "Stecklinge starten in seedling-Phase" (Zeile 1058) ist korrekt, aber die Uebergabe sollte praeziser definiert werden:

| Vermehrungsmethode | Start-Phase | Begruendung |
|-------------------|-------------|-------------|
| cutting | seedling | Steckling hat bereits Blaetter, ueberspringt Keimung |
| seed_sowing | germination | Samen muss keimen |
| division | vegetative | Geteilte Pflanze hat bereits Wurzeln und Blaetter |
| layering | vegetative | Bewurzelter Absenker ist vollentwickelt |
| grafting | (behaelt aktuelle Phase) | Veredelung aendert die Phase nicht |
| tissue_culture | seedling | Aehnlich wie Steckling nach Akklimatisierung |
| offset | seedling | Kindel ist klein, braucht Etablierung |
| leaf_cutting | germination | Muss zuerst Adventivwurzeln und -sprosse bilden |

### REQ-013 Pflanzdurchlauf -- Integration

Die batch_feeds_run-Verknuepfung (PropagationBatch -> PlantingRun) ist gut modelliert. Ergaenzend sollte:
- Der PlantingRun den `source_type: 'propagation'` kennen (neben 'purchased', 'existing')
- Die Herkunft (Klon/Samen/Teilung) im PlantingRunEntry abgebildet sein
- Die PlantingRun-Erstellung optional direkt aus der Batch-Finalisierung moeglich sein (nicht nur Verweis auf existierenden Run)

### REQ-010 IPM -- Integration

Wie in U-005 beschrieben fehlt die Verbindung zum IPM-System. Zusaetzlich:
- PropagationEvents sollten optional einen Schaedlings-/Krankheits-Check als Voraussetzung haben (Mutterpflanze muss IPM-Status "clean" haben fuer priority="critical")
- Failure-Reason "damping_off" sollte einen automatischen IPM-Eintrag (Inspektion) ausloesen

### REQ-019 Substratverwaltung -- Integration

Wie in U-007 beschrieben fehlt die Verknuepfung. Das Bewurzelungsmedium ist ein Substrat und sollte optional ueber REQ-019 verwaltbar sein.

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Bewurzelungshormon-Konzentrationen | Hartmann & Kester's Plant Propagation | ISBN 978-0134480893 |
| Zimmerpflanzen-Vermehrung | RHS Propagation | rhs.org.uk |
| Cannabis-Klontechnik | Ed Rosenthal, Marijuana Horticulture | -- |
| Veredelungs-Kompatibilitaet | USDA Horticultural Research Lab | ars.usda.gov |
| Mykorrhiza-Inokulation | Colla et al. (2015), Scientia Horticulturae | doi.org/10.1016/j.scienta.2015.09.052 |
| VPD-Grundlagen fuer Propagation | Apogee Instruments / LI-COR | apogeeinstruments.com |
| Somatische Mutationen in Klonlinien | D'Amato (1997), Mutation Research | -- |

---

## Glossar

- **PPFD** (Photosynthetic Photon Flux Density): Mass fuer die photosynthetisch nutzbare Lichtmenge in umol/m2/s -- der korrekte Wert fuer Pflanzenwachstum (nicht Lux)
- **VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa -- beschreibt den "Durst" der Luft, abhaengig von Temperatur und Luftfeuchtigkeit. Kritisch fuer unbewurzelte Stecklinge
- **IBA** (Indol-3-Buttersaeure): Synthetisches Auxin, Standard-Bewurzelungshormon. Foerdert Adventivwurzelbildung an Stecklingen
- **NAA** (Naphthylessigsaeure): Synthetisches Auxin, staerker und phytotoxischer als IBA
- **Kallus** (Callus): Undifferenziertes Wundgewebe, das sich an der Schnittstelle eines Stecklings bildet, bevor Adventivwurzeln entstehen
- **Somatische Mutation:** Mutation in einer Koerperzelle (nicht Keimzelle), die bei vegetativer Vermehrung an Nachkommen weitergegeben wird
- **Epigenetische Drift:** Veraenderungen im Genexpressionsmuster ohne DNA-Sequenzaenderung, akkumulierend ueber Klon-Generationen
- **Apikal:** Die Triebspitze betreffend. Apikaldominanz = Hemmung von Seitentrieben durch das Hormon Auxin aus der Triebspitze
- **Adventivwurzel:** Wurzel, die nicht aus der Primaerwurzel, sondern aus Sprossgewebe entsteht (z.B. an der Schnittstelle eines Stecklings)
- **F1-Hybride:** Erste Filialgeneration einer Kreuzung zweier genetisch verschiedener Elternlinien. Gleichmaessiger Phaenotyp, haeufig Heterosis (Wuchskraft)
- **Phytotoxizitaet:** Giftwirkung einer Substanz auf Pflanzengewebe (z.B. zu hohe Hormonkonzentration)
- **Abmoosen (Air Layering):** Vermehrungsmethode, bei der ein Trieb an der Pflanze verwurzelt wird, bevor er abgetrennt wird. Ideal fuer grosse Zimmerpflanzen
- **Meristem:** Pflanzliches Bildungsgewebe mit undifferenzierten, teilungsfaehigen Zellen. Meristem-Kultur erzeugt virusfreie Pflanzen
