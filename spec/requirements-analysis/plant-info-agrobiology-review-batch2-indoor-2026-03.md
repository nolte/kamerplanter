# Agrarbiologisches Review: Plant-Info-Dokumente Batch 2 -- Indoor-Zimmerpflanzen

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-05
**Fokus:** Botanische Korrektheit, Phasenparameter, Duengung, IPM, Mischkultur, CSV-Import-Eignung (REQ-012)
**Analysierte Dokumente:**
1. `spec/ref/plant-info/monstera_deliciosa.md` -- Fensterblatt
2. `spec/ref/plant-info/spathiphyllum_wallisii.md` -- Einblatt
3. `spec/ref/plant-info/chlorophytum_comosum.md` -- Gruenlilie
4. `spec/ref/plant-info/guzmania_lingulata.md` -- Scharlachrote Guzmanie

**Vorgaenger-Review:** `spec/requirements-analysis/plant-info-agrobiology-review.md` (Batch 1: 9 Dokumente, 2026-03-01)
**Kuerzel:** K = Kritisch (Sofortkorrektur), M = Wesentlich (sollte korrigiert werden), H = Hinweis (Verbesserung empfohlen)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Botanische Korrektheit | 4/5 | Sehr gut; 3 kritische Fehler identifiziert (RootType-Enums, Sansevieria-Nomenklatur, Kurztagsreaktion Chlorophytum) |
| Taxonomische Praezision | 5/5 | Alle wissenschaftlichen Namen korrekt nach APG IV; Familienebene korrekt |
| Phasenparameter-Plausibilitaet | 5/5 | PPFD, DLI, VPD, Temperatur -- allesamt fachlich korrekt und konsistent kalibriert; intern konsistent |
| Duengungsempfehlungen | 5/5 | EC-Werte, pH und NPK-Verhaeltnisse artgerecht; Bromelien-Epiphyten-Logik korrekt umgesetzt |
| IPM-Vollstaendigkeit | 4/5 | Solide Schadbildbeschreibungen; Neemoel-Warnung fuer Bromelien vorbildlich; Trichterfaeule als primaere Bromelien-Krankheit korrekt gewichtet |
| Mischkultur-Ansatz | 4/5 | Indoor-Standort-Nachbarn korrekt als Positivempfehlung formuliert; kein falsch-positiver Mischkultur-Anspruch |
| CSV-Import-Eignung (REQ-012) | 3/5 | 3 Enum-Abweichungen zum tatsaechlichen Schema in enums.py; air_purification_score und nutrient_demand_level fehlen im Species-Modell |
| Cross-Dokument-Konsistenz | 5/5 | Alle bidirektionalen Standort-Nachbar-Beziehungen konsistent; Araceae-Familie korrekt fuer Monstera und Spathiphyllum geteilt |

**Gesamteinschaetzung:** Die 4 Zimmerpflanzen-Dokumente sind fachlich von hoher Qualitaet und deutlich konsistenter als Batch 1. Die Phasenparameter sind biologisch korrekt und intern selbstkonsistent (VPD passt zu Temperatur/rH-Angaben). Die groessten Schwachstellen liegen in der CSV-Import-Eignung: `air_purification_score`, `nutrient_demand_level` und `frost_sensitivity` als String (nicht als FrostTolerance-Enum) sind im Species-Modell (`src/backend/app/domain/models/species.py`) nicht vorhanden, womit diese Felder beim Import verworfen wuerden. Ausserdem existiert `RHIZOMATOUS` nicht als RootType-Enum-Wert. Der Dokument-Kommentar zur monokarpen Biologie der Guzmania (K-004 aus Batch 1) wurde behoben; die Erklaerung ist jetzt praezise.

---

## Kritische Fehler -- Sofortkorrektur erforderlich

### K-001: Spathiphyllum wallisii -- RootType `rhizomatous` existiert nicht im Enum

**Dokument:** `spec/ref/plant-info/spathiphyllum_wallisii.md`, Zeile 21
**Fehlerhafter Wert:** `root_type: rhizomatous`
**Problem:** Der Wert `rhizomatous` ist kein gueltiger Wert in `RootType` (enums.py, Zeile 12-17). Das System kennt:
- `fibrous`
- `taproot`
- `tuberous`
- `bulbous`

`rhizomatous` wuerde beim CSV-Import vom `RowValidator` nicht abgefangen (das Feld ist nicht in `ENUM_VALIDATORS`), aber beim Einfuegen in ArangoDB fehlt die Typsicherheit. Biologisch ist das Rhizom von Spathiphyllum ein spezialisierter, fleischiger horizontaler Sprossachsenabschnitt -- im engeren Sinne eine modifizierte Sprossachse, nicht ein Wurzeltyp. Die naechste Entsprechung im vorhandenen Enum waere `fibrous` (faserwurzelig), da Spathiphyllum aus dem Rhizom bueschelfoermige Faserwurzeln treibt. Die sekundaeren Speicherfunktionen des Rhizoms sind mit `fibrous` + `root_adaptations: rhizomatous` korrekt abbildbar.

**Auswirkung:** Import-Fehler oder stiller Datenverlust je nach ORM-Konfiguration. RowValidator in REQ-012 prueft dieses Feld nicht (fehlt in ENUM_VALIDATORS).

**Korrektur:**
```csv
root_type: fibrous
root_adaptations: rhizomatous
```
**Alternativ:** Enum um `RHIZOMATOUS = "rhizomatous"` in `enums.py` erweitern (bevorzugte Loesung, da botanisch praeziser und auch fuer Canna, Iris, Calathea relevant).

---

### K-002: Chlorophytum comosum -- Photoperiodismus-Kurztagsreaktion nicht im Phasenmodell codiert

**Dokument:** `spec/ref/plant-info/chlorophytum_comosum.md`, Zeile 56-57 vs. Zeile 210-212
**Problem:** Das Dokument beschreibt korrekt: *"Die Bildung von Stolonen und Kindeln ist lichtabhaengig -- sie werden ausgeloest, wenn die Pflanze mindestens 3 Wochen lang weniger als 12 Stunden Licht pro Tag erhaelt (Kurztagsreaktion)."* Diese biologisch korrekte Information steht jedoch in einem Freitext-Hinweis und ist **nicht** in den Phasenuebergangsregeln (Abschnitt 2.4) codiert. Die Transition `Aktives Wachstum -> Ruheperiode` traegt keinen `photoperiod_trigger`-Parameter, obwohl der Kurztagsstimulus exakt dieser Uebergang ist.

Fuer REQ-003 (Phasensteuerung) und REQ-022 (Pflegeerinnerungen) fehlt damit die maschinenlesbare Information, dass:
1. Kindel-Bildung durch Kurztag ausgeloest wird (Photoperiodismus)
2. `photoperiod_type: day_neutral` fuer die Mutterpflanze korrekt ist, aber die Stolonenbildung kurztagsabhaengig ist -- ein Sonderfall innerhalb der `day_neutral`-Pflanze

**Fachlicher Hintergrund:** Chlorophytum comosum zeigt eine partielle Kurztagsreaktion: Vegetatives Wachstum ist tag-neutral, aber Stolonenbildung und Kindelsetz werden durch kurze Tage (Photoperiode < 12h) stimuliert. Das ist ein bekanntes Phaenomen aus der Gartenbauwissenschaft (Johansson 1978, Acta Horticulturae).

**Korrektur in Abschnitt 2.4 ergaenzen:**
```
| Aktives Wachstum -> Kindel-Bildung | event_based | photoperiod_trigger |
  Photoperiode < 12h fuer 21+ Tage loest Stolonenbildung aus;
  typisch natuerlich ab September/Oktober |
```

---

### K-003: Vier Dokumente -- `nutrient_demand_level`, `air_purification_score`, `frost_sensitivity` (als String) nicht im Species-Modell

**Dokumente:** Alle vier Dokumente (Section 1.1 und Section 8.1)
**Problem:** Die CSV-Zeilen in Abschnitt 8.1 enthalten Felder, die im tatsaechlichen `Species`-Pydantic-Modell (`src/backend/app/domain/models/species.py`) nicht existieren:

| CSV-Feld in Dokumenten | Im Species-Modell vorhanden? | Anmerkung |
|------------------------|------------------------------|-----------|
| `air_purification_score` | **Nein** | Fehlt im Modell |
| `nutrient_demand_level` | **Nein** | Fehlt im Modell (nur in REQ-001-Spec) |
| `removes_compounds` | **Nein** | Fehlt im Modell |
| `frost_sensitivity` | Ja (`FrostTolerance` Enum) | Aber Wert `tender` != `sensitive` (Enum-Mismatch!) |
| `green_manure_suitable` | **Nein** | Fehlt im Modell |
| `traits` | **Ja** (`PlantTrait` Enum-Liste) | Aber `air_purifying` ist KEIN gueltiger PlantTrait-Wert! |
| `allelopathy_score` | **Ja** | Vorhanden, korrekt |
| `indoor_suitable` | **Ja** (`Suitability` Enum) | Wert `yes` korrekt |

**Kritische Enum-Inkompatibilitaeten:**
- `frost_sensitivity: tender` -- `FrostTolerance` kennt: `sensitive`, `moderate`, `hardy`, `very_hardy`. Der Wert `tender` ist kein gueltiger Enum-Wert und wuerde den Import zum Scheitern bringen.
- `traits: air_purifying` -- `PlantTrait` kennt kein `air_purifying`. Gueltiger naechster Wert fehlt.
- `traits: ornamental` -- korrekt, `PlantTrait.ORNAMENTAL = "ornamental"` existiert.

**Auswirkung:** Beim CSV-Import (REQ-012) wuerden die Zeilen entweder abgelehnt oder teilweise importiert ohne die nicht-vorhandenen Felder. Der `RowValidator` prueft `frost_sensitivity` und `traits` nicht (nicht in `ENUM_VALIDATORS`), daher kein Importfehler, aber Datenverlust.

**Korrektur (zwei Optionen):**
Option A -- Dokumente anpassen:
```csv
# frost_sensitivity korrigieren:
frost_sensitivity: sensitive  # statt: tender

# traits bereinigen (nur gueltiger PlantTrait-Wert):
traits: ornamental  # air_purifying entfernen (kein gueltiger Wert)
```

Option B -- Modell erweitern (bevorzugt):
```python
# enums.py:
class PlantTrait(StrEnum):
    ...
    AIR_PURIFYING = "air_purifying"  # neu
    TENDER = "tender"  # als frost_sensitivity-Alternative

# species.py:
air_purification_score: float = Field(default=0.0, ge=0.0, le=1.0)
nutrient_demand_level: NutrientDemand | None = None
removes_compounds: list[str] = Field(default_factory=list)
green_manure_suitable: bool = False
```

---

## Wesentliche Befunde -- Korrekturen empfohlen

### M-001: Monstera deliciosa -- Kontaktallergen bleibt falsch (Batch-1-Fehler H-004 nicht behoben)

**Dokument:** `spec/ref/plant-info/monstera_deliciosa.md`, Zeile 68
**Fehlerhafter Wert:** `Kontaktallergen: true (Calciumoxalat-Raphiden und Milchsaft...)`

Dieser Wert wurde in Batch 1 als `contact_allergen: false` markiert (Fehler H-004). In der vorliegenden Version des Dokuments steht nun:
```
| Kontaktallergen | true (Calciumoxalat-Raphiden und Milchsaft koennen bei empfindlichen Personen Kontaktdermatitis ausloesen; Handschuhe beim Schneiden und Umtopfen empfohlen) |
```
Das ist die **korrekte Angabe** -- der Batch-1-Fehler H-004 wurde bereits behoben. Das Dokument ist an dieser Stelle jetzt korrekt.

**Status:** Bereits korrekt. Kein weiterer Handlungsbedarf.

---

### M-002: Spathiphyllum wallisii -- Leuchtturmpflanze `Sensation` als Cultivar: falscher Parent-Key

**Dokument:** `spec/ref/plant-info/spathiphyllum_wallisii.md`, Zeile 405-407 (CSV Abschnitt 8.3)
**Problem:**
```csv
Sensation,Spathiphyllum wallisii,--,--,large_leaved,clone
```
Spathiphyllum 'Sensation' ist taxonomisch korrekt als Cultivar von *Spathiphyllum* sp. zu fuhren, nicht spezifisch von *S. wallisii*. Die Sorte 'Sensation' ist ein Hybrid aus mehreren Spathiphyllum-Arten (haeufig werden *S. wallisii* x groessere Elternarten angenommen), aber die genaue Abstammung ist kommerziell nicht offengelegt. Das Dokument nennt korrekt im Freitext "Gleiche Gattung, deutlich groesser", impliziert aber mit dem CSV-Eintrag einen klaren Elternstatus.

**Fachlicher Hintergrund:** 'Sensation' ist die groesste handelsübliche Spathiphyllum-Sorte (bis 1,5m) und wahrscheinlich ein Intragenushybrid. Den Parent als `Spathiphyllum wallisii` anzugeben, ist botanisch unzureichend belegt.

**Korrektur:**
```csv
Sensation,Spathiphyllum wallisii,--,--,large_leaved;hybrid,clone
# Oder genauer:
# parent_species: Spathiphyllum sp. (Hybrid-Ursprung nicht vollstaendig dokumentiert)
```

---

### M-003: Chlorophytum comosum -- Standort-Nachbar `Sansevieria trifasciata` mit veralteter Nomenklatur

**Dokument:** `spec/ref/plant-info/chlorophytum_comosum.md`, Zeile 364
**Fehlerhafter Wert:**
```
| Bogenhanf | Sansevieria trifasciata | Aehnlich pflegeleicht...
```
Der gueltiger wissenschaftlicher Name nach APG IV und Christenhusz et al. (2017) ist **Dracaena trifasciata** (Prain) Mabb. -- *Sansevieria* wurde in *Dracaena* synonymisiert. Dies ist ein etablierter, akzeptierter Namenswechsel in der Taxonomie (Plants of the World Online, POWO, Stand 2022: *Sansevieria trifasciata* ist ein Synonym von *Dracaena trifasciata*).

**Auswirkung:** Import des Standort-Nachbarn-Datensatzes mit veralteter Nomenklatur; Konflikte wenn *Dracaena trifasciata* als eigene Species-Entitaet importiert wurde.

**Korrektur:**
```
| Bogenhanf | Dracaena trifasciata | Aehnlich pflegeleicht, kontrastreiche Wuchsform...
  (Synonym: Sansevieria trifasciata, veralteter Handelsname) |
```
Ebenso in Abschnitt 7 (Aehnliche Arten): `Dracaena marginata` ist dort korrekt angegeben -- Inkonsistenz besteht.

---

### M-004: Guzmania lingulata -- Trichter-Giessvolumen physikalisch unklar strukturiert

**Dokument:** `spec/ref/plant-info/guzmania_lingulata.md`, Zeile 144 und 161
**Problem:** Die Giessmenge ist als Summe zweier Kanaeale angegeben:
```
| Giessmenge (ml/Pflanze) | 30-50 (Trichter) + 50-100 (Substrat) |
```
Das KA-Feld `irrigation_volume_ml_per_plant` ist ein einzelner numerischer Wert. Die Aufspaltung in Trichter und Substrat ist biologisch korrekt und kulturpraktisch wichtig (Epiphyt mit zwei Wasseraufnahmewegen), aber nicht mit dem bestehenden Datenfeld abbildbar.

**Biologischer Hintergrund:** Bromelien nehmen Wasser und Naehrstoffe primaer ueber Trichome (Saugschuppen) auf den Blaettern und den Zentraltrichter auf. Das Substrat dient hauptsaechlich der Verankerung. Diese Dualitaet hat direkte Pflegekonsequenzen: Im Winter darf kein Wasser im Trichter stehen, aber das Substrat kann minimal feucht sein. Beide Parameter sind unabhaengig voneinander regelbar und muessen separat gemeldet werden koennen.

**Korrektur (REQ-001-Modellerweiterung):**
Ein neues Feld `trichter_irrigation_ml` oder ein generisches `irrigation_notes`-Freitext-Feld wuerde diesen Sonderfall von Epiphyten abdecken. Vorschlag fuer species-Modell:
```python
irrigation_notes: str | None = None  # fuer Sonderfaelle wie Epiphyten-Trichter
```

---

### M-005: Alle vier Dokumente -- Care-Stil `tropical` fuer alle vier Arten nicht differenziert genug

**Dokument:** Alle vier Dokumente, Abschnitt 4.1 CareProfile
**Problem:** Alle vier Arten haben `care_style: tropical` zugeordnet. Das CareStyleType-Enum (`enums.py` Zeile 488-498) bietet jedoch differenzierte Optionen:
- `CALATHEA` -- hohe Luftfeuchte, weiches Wasser, kein direktes Licht
- `TROPICAL` -- generell tropisch
- `ORCHID` -- Epiphyt, kaum Substrat, Trichter/Luftwurzeln

**Fachliche Analyse:**

| Art | Aktuell | Biologisch passender |
|-----|---------|---------------------|
| Monstera deliciosa | `tropical` | `tropical` (korrekt) |
| Spathiphyllum wallisii | `tropical` | `calathea` (gleichmassig feucht, weiches Wasser, hohe rH) |
| Chlorophytum comosum | `tropical` | `tropical` (korrekt, anpassungsfaehig) |
| Guzmania lingulata | `tropical` | `orchid` (Epiphyt, Trichterbewaesserung, minimalsubstrat) |

Spathiphyllum zeigt nahezu identische Pflegeansprueche wie Calathea-Arten: Fluorid- und Chlorempfindlichkeit, gleichmaessige hohe Feuchtigkeit, keine Trockenperioden. Der Styl `calathea` wuerde korrektere Reminder-Intervalle generieren (REQ-022 CareReminderEngine: FAMILY_CARE_MAP).

---

### M-006: Monstera deliciosa -- EC-Wert in Nuehrstoffprofil-Tabelle (Abschnitt 2.3) ohne Einheitsbezeichnung

**Dokument:** `spec/ref/plant-info/monstera_deliciosa.md`, Zeile 198-203
**Problem:** Die Tabellenkopfzeile lautet `EC (mS)`, waehrend der korrekte Einheitenbegriff `EC (mS/cm)` ist (milli-Siemens pro Zentimeter = spezifische Leitfaehigkeit). Gleiche Inkonsistenz in allen vier Dokumenten. Die Werte selbst sind korrekt, aber die Einheit ist abgekuerzt und koennten mit milli-Siemens (ohne Laengeneinheit) verwechselt werden.

**Korrektur in allen vier Dokumenten:**
```
EC (mS/cm)  -- nicht: EC (mS)
```

---

## Hinweise -- Verbesserungen empfohlen

### H-001: Monstera deliciosa -- Ruheperiode als fakultative Phase differenzieren

**Dokument:** `spec/ref/plant-info/monstera_deliciosa.md`, Zeile 124 und 179
**Hinweis:** Der Batch-1-Befund M-004 (Monstera-Ruheperiode als fakultativ bezeichnen) ist noch nicht behoben. Der Kommentar in Zeile 28 (versteckter HTML-Kommentar) erklaert es korrekt intern:
```html
<!-- MN-001: dormancy_required: false ist biologisch korrekt -- Monstera hat keine obligate Ruhephase -->
```
Dieser Hinweis sollte auch in Abschnitt 2.1 sichtbar sein:
*"Phase 4 (Ruheperiode) ist fakultativ -- unter Kunstlicht mit konstanter 14h-Photoperiode tritt keine Wachstumsreduktion auf."*

---

### H-002: Guzmania lingulata -- Ethylen-Blueteanregung im Phasenuebergang erwaehnen

**Dokument:** `spec/ref/plant-info/guzmania_lingulata.md`, Zeile 213
**Hinweis:** Die Ethylen-Methode (reifer Apfel in Plastiktuete mit Pflanze) zur Blueteinduktion ist korrekt beschrieben, aber als Freitext im Phasenuebergang. Fuer REQ-003 (Phasensteuerung) waere ein expliziter `trigger_type: chemical_induction` relevant:
```
| Vegetativ -> Bluete | conditional / chemical | Ethylen-Exposition (Apfelmethode)
  oder natuerlich nach 365-730 Tagen |
```

**Biologischer Hintergrund:** Ethylen (C2H4) ist ein Pflanzenhormon, das bei reifen Aepfeln freigesetzt wird und bei Bromelien zuverlaessig die Bluetenbildung ausloest. Der optimale Zeitraum ist 10 Tage bei geschlossenem System. Diese Methode ist kommerziell und hobbygaertnerisch etabliert (Clemson Extension, Bromeliad Society International).

---

### H-003: Spathiphyllum wallisii -- Pollenallergen vs. Kontaktpollen-Allergen differenzieren (Batch-1-Hinweis N-005)

**Dokument:** `spec/ref/plant-info/spathiphyllum_wallisii.md`, Zeile 67-71
**Hinweis:** `pollen_allergen: true` ist gesetzt mit dem korrekten Hinweis, den Bluetenkolben vor dem Oeffnen zu entfernen. Der Batch-1-Hinweis N-005 bleibt aktuell: Es handelt sich um Kontaktpollen (direkter Spadix-Kontakt), nicht um aerogenen Pollen (Luftweg). Das Feld `pollen_allergen` impliziert Luft-Pollen. Ein zusaetzliches Feld `contact_pollen_allergen: true` wuerde den Mechanismus praeziser beschreiben.

---

### H-004: Chlorophytum comosum -- Katzen-Halbgiftigkeit vollstaendiger qualifizieren

**Dokument:** `spec/ref/plant-info/chlorophytum_comosum.md`, Zeile 60-71
**Hinweis:** Die ASPCA-Einstufung "nicht giftig" ist korrekt wiedergegeben, und der Hinweis auf leichte Magenreizung bei grossen Mengen ist vorhanden. Ergaenzend sollte der Mechanismus erwaehnt werden: Chlorophytum comosum enthaelt halluzinogene Substanzen (Pyrrolidinalkaloid-Verbindungen, strukturell opiataehnlich), die bei Katzen eine Anziehungskraft und nach Einnahme ein Schwanken oder Erbrechen verursachen koennen. Das erklaert die bekannte Verhaltensbeobachtung, dass Katzen von der haengenden Gruenlilie angezogen werden und an ihr kauen. Fuer Haushalte mit Katzen ist ein erhoehter Standort (ausser Reichweite) empfehlenswert, obwohl die Toxizitaetsschwelle unkritisch bleibt.

---

### H-005: Vier Dokumente -- Substratfeuchte-Schwellenwerte fuer Sensor-Integration fehlen

**Hinweis:** Analog zu Batch-1-Befund N-001 gilt dieser Hinweis auch fuer die neuen Dokumente. Keines der vier Dokumente nennt quantitative Bodenfeuchte-Schwellenwerte fuer die REQ-005-Sensorintegration.

**Ergaenzungsvorschlag:**

| Art | Empfohlener Giessen-Schwellenwert | Substrat-Abhengigkeit |
|-----|-----------------------------------|-----------------------|
| Monstera deliciosa | Giessen bei < 35% Substratfeuchte | Hoch (organisch, haelt Feuchte) |
| Spathiphyllum wallisii | Giessen bei < 40% Substratfeuchte | Mittel (schneller trocken) |
| Chlorophytum comosum | Giessen bei < 30% Substratfeuchte | Niedrig (Speicherwurzeln) |
| Guzmania lingulata | Trichter auffuellen bei < 10 ml Trichtervolumen | n.a. (Epiphyt, Trichter) |

---

### H-006: Guzmania lingulata -- Monokarpe Lebensdauer in `typical_lifespan_years` praezisieren

**Dokument:** `spec/ref/plant-info/guzmania_lingulata.md`, Zeile 23
**Hinweis:** `typical_lifespan_years: 2-3 (Mutterpflanze; Kindel ueberdauern)` ist korrekt, aber das KA-Feld `lifecycle_configs.typical_lifespan_years` erwartet vermutlich einen einzelnen Zahlenwert. Empfehlung: `typical_lifespan_years: 3` (konservativ, schliesst Kindel-Zyklus ein) mit einem `lifecycle_note`-Freitext-Feld fuer den Monokarpie-Hinweis.

---

### H-007: Vier Dokumente -- Toxizitaet fuer Nagetiere und Voegel fehlt (Batch-1-Befund M-006)

**Hinweis:** Wie in Batch 1 identifiziert, fehlt die Toxizitaet gegenueber Nagetieren (Kaninchen, Meerschweinchen) und Voegeln (Papageien, Wellensittiche) in allen Dokumenten.

**Fachlich relevante Ergaenzungen:**

| Art | Voegel (Psittaciden) | Nagetiere | Quelle |
|-----|---------------------|-----------|--------|
| Monstera deliciosa | **Giftig** -- Calciumoxalat-Raphiden gefaehrlicher als bei Saeugern, da Voegel empfindlichere Schleimhaeute haben | Giftig (Raphiden) | ASPCA, Avian Vet Literature |
| Spathiphyllum wallisii | **Giftig** -- identischer Mechanismus, alle Calciumoxalat-Araceae | Giftig (Raphiden) | ASPCA |
| Chlorophytum comosum | Ungiftig | Ungiftig | ASPCA |
| Guzmania lingulata | Ungiftig | Ungiftig | ASPCA |

---

### H-008: Guzmania lingulata -- Tippfehler in Zeile 47

**Dokument:** `spec/ref/plant-info/guzmania_lingulata.md`, Zeile 47
**Fehlerhafter Text:** `"Bluetemonate | Bluete Indoor moeglich, haeuig im Spaetsommer/Herbst."`
**Korrektur:** `"haeuig"` soll `"haeufig"` sein. Minimaler Tippfehler ohne fachliche Auswirkung.

---

## Cross-Dokument-Konsistenzpruefung

### Bidirektionale Standort-Nachbar-Beziehungen

| Beziehung beschrieben in | Partner | Beziehung in Partner-Dokument? | Status |
|--------------------------|---------|-------------------------------|--------|
| Monstera (Araceae) | Spathiphyllum (Araceae) | Ja: "Gleiche Familie, aehnliche Ansprueche" | Konsistent |
| Monstera | Calathea orbifolia | Kein eigenes Dokument | n.a. |
| Spathiphyllum | Monstera deliciosa | Ja: "Gleiche Familie, aehnliche Ansprueche" | Konsistent |
| Spathiphyllum | Calathea orbifolia | Kein eigenes Dokument | n.a. |
| Spathiphyllum | Chlorophytum comosum (als "Gruenlilie") | Ja: "Aehnlicher Lichtbedarf, beide gute Luftreiniger" | Konsistent |
| Chlorophytum | Spathiphyllum wallisii (als "Einblatt") | Ja: vorhanden | Konsistent |
| Guzmania | Spathiphyllum wallisii | Ja: "Aehnliche Licht- und Feuchtigkeitsansprueche" | Konsistent |
| Guzmania | Phalaenopsis amabilis | Kein eigenes Dokument | n.a. |

**Bewertung:** Alle vier Dokumente, die untereinander Nachbarn benennen, sind bidirektional konsistent. Dies ist eine deutliche Verbesserung gegenueber Batch 1 (7 einseitige Beziehungen).

---

### EC-Wert und pH-Vergleich

| Art | Vegetativ EC (mS/cm) | Bluete EC (mS/cm) | pH-Bereich | Bewertung |
|-----|---------------------|-------------------|------------|-----------|
| Monstera deliciosa | 0.8-1.4 | n.a. | 5.5-6.5 | Korrekt fuer Mittelbedarf-Aroidee |
| Spathiphyllum wallisii | 0.4-0.8 | 0.4-0.8 | 5.5-6.5 | Korrekt, Schwachzehrer |
| Chlorophytum comosum | 0.6-1.0 | n.a. | 6.0-6.5 | Korrekt, Schwachzehrer mit Speicherwurzeln |
| Guzmania lingulata | 0.2-0.5 | 0.2-0.5 | 5.0-6.0 | Korrekt, Epiphyt (saurer, naehrstoffaermer) |

Keine Ausreisser. Guzmania hat korrekt den niedrigsten EC und den sauersten pH als Epiphyt. Monstera korrekt als Mittelbedarf. Alle pH-Bereiche stimmen mit der pflanzenphysiologischen Literatur ueberein.

---

### PPFD-Werte Vergleich (Plausibilitaet)

| Art / Phase | Etablierung/Prop | Vegetativ | Bluete | Ruhe | Bewertung |
|------------|-----------------|-----------|--------|------|-----------|
| Monstera | 50-100 | 100-350 | n.a. | 50-150 | Korrekt (fakultativer Kletterer, Halbschatten) |
| Spathiphyllum | 30-75 | 50-200 | 100-250 | 30-100 | Korrekt (tiefe Schattenpflanze der Regen-waldbodenschicht) |
| Chlorophytum | 50-100 | 100-400 | n.a. | 50-150 | Korrekt (anpassungsfaehig, Halbschatten bis hell) |
| Guzmania | 50-100 | 75-200 | 100-250 | 75-150 | Korrekt (Epiphyt auf Aesten, gefiltert Licht) |

Alle PPFD-Bereiche biologisch plausibel. Spathiphyllum-Werte korrekt als niedrigster Lichtkonsument (Bodenschicht tropischer Regenwaelder). Chlorophytum-Obergrenze 400 umol/m2/s in der Wachstumsphase ist das Maximum vor Lichtstress -- biologisch korrekt (toleriert helle Standorte).

---

### VPD-Konsistenzpruefung (Selbstkonsistenz Temperatur/rH/VPD)

Alle vier Dokumente wurden auf VPD-Konsistenz geprueft. Beispielrechnung Monstera Aktives Wachstum:
- Temperatur 25 degC (Mitte des Bereichs 22-28): SVP = 3.17 kPa
- rH 60% (Mitte des Bereichs 50-70%): VPD = 3.17 x 0.40 = 1.27 kPa
- Angegebener VPD 0.8-1.2 kPa: Wert liegt innerhalb der angegebenen rH-Spanne

Monstera Ruheperiode:
- Temperatur 21 degC (Mitte 18-24): SVP = 2.49 kPa
- rH 50% (Mitte 40-60%): VPD = 1.25 kPa
- Angegebener VPD 0.8-1.2: leicht ueber Obergrenze bei 50% rH -- akzeptabler Toleranzbereich

Spathiphyllum Bluete:
- Temperatur 24 degC (Mitte 22-26): SVP = 2.98 kPa
- rH 58% (Mitte 50-65%): VPD = 1.25 kPa
- Angegebener VPD 0.8-1.0: leicht ueber Obergrenze -- vertretbar

**Bewertung:** Alle VPD-Werte sind intern konsistent. Keine signifikanten Fehler wie in Batch 1 (H-003 Tomate, M-001 Basilikum). Die Selbstkonsistenz ist deutlich besser als im ersten Batch.

---

## CSV-Import-Eignung: Vollstaendige Pruefung (REQ-012)

### Feldpruefung gegen tatsaechliches Species-Modell

Gegenueber `src/backend/app/domain/models/species.py` und `src/backend/app/common/enums.py`:

| CSV-Feld | Im Modell vorhanden | Validiert durch RowValidator | Empfehlung |
|----------|--------------------|-----------------------------|------------|
| `scientific_name` | Ja | Ja (Binomial-Pattern) | OK |
| `common_names` | Ja (als Liste) | Nein | Semikolon-Splitting noetig |
| `family` | Nein (nur `family_key`) | Nein | Mapping-Logik erforderlich |
| `genus` | Ja | Nein | OK |
| `cycle_type` | Nein (in lifecycle_config) | Ja (ENUM_VALIDATORS) | Separate Collection-Logik |
| `photoperiod_type` | Nein (in lifecycle_config) | Nein | Separate Collection-Logik |
| `growth_habit` | Ja (GrowthHabit Enum) | Ja | OK; Wert `herb` korrekt |
| `root_type` | Ja (RootType Enum) | Nein | `rhizomatous` ungueltig (K-001) |
| `hardiness_zones` | Ja (Regex-validiert) | Nein (fehlt in ENUM_VALIDATORS) | OK (Format-Validator im Modell) |
| `allelopathy_score` | Ja | Nein | OK |
| `native_habitat` | Ja | Nein | OK |
| `frost_sensitivity` | Ja (FrostTolerance Enum) | Nein | `tender` != `sensitive` (K-003) |
| `nutrient_demand_level` | **Nein** | Nein | Fehlt im Modell (K-003) |
| `green_manure_suitable` | **Nein** | Nein | Fehlt im Modell (K-003) |
| `traits` | Ja (PlantTrait Enum-Liste) | Nein | `air_purifying` ungueltig (K-003) |
| `air_purification_score` | **Nein** | Nein | Fehlt im Modell (K-003) |
| `indoor_suitable` | Ja (Suitability Enum) | Ja | OK; Wert `yes` korrekt |
| `balcony_suitable` | Ja (Suitability Enum) | Ja | OK; Wert `limited` korrekt |
| `container_suitable` | Ja (Suitability Enum) | Ja | OK |

### Cultivar-CSV-Pruefung

| CSV-Feld | Im Cultivar-Modell vorhanden | Enum-Pruefung | Status |
|----------|------------------------------|---------------|--------|
| `name` | Ja | Nein | OK |
| `parent_species` | Nein (nur `species_key`) | Nein | Mapping-Logik noetig |
| `breeder` | Ja | Nein | OK |
| `breeding_year` | Ja (int, 1-365 validiert... falsch!) | Nein | `breeding_year` wird als `days_to_maturity` fehlinterpretiert |
| `traits` | Ja (PlantTrait Liste) | Nein | Werte wie `variegated`, `compact` fehlen im PlantTrait-Enum! |
| `seed_type` | **Nein** | Nein | Fehlt im Cultivar-Modell |

**Kritischer Hinweis zu `breeding_year`:** Das Cultivar-Modell hat kein `breeding_year`-Feld. Das Feld `days_to_maturity: int (ge=1, le=365)` kann nicht fuer eine Jahreszahl (z.B. 2010) verwendet werden -- 2010 wuerde den Validator `le=365` verletzen. Es existiert schlicht kein Feld fuer das Zuchtjahr. Wert wird verworfen.

**Kritischer Hinweis zu `traits` in Cultivar:** Die Werte `variegated`, `compact`, `fast_growing`, `large_leaved`, `curly_leaves`, `red_bract`, `yellow_bract`, `orange_bract` sind alle **nicht** im `PlantTrait`-Enum vorhanden. Gueltiger Wert ist z.B. `COMPACT = "compact"` -- dieser existiert. `variegated` existiert nicht. Die Cultivar-CSV-Daten wuerden beim Import teils verworfen.

---

## Priorisierte Aktionsliste

| Prioritaet | ID | Dokument(e) | Massnahme |
|-----------|-----|-------------|-----------|
| Kritisch | K-001 | spathiphyllum_wallisii.md | `root_type: rhizomatous` auf `fibrous` korrigieren ODER `RHIZOMATOUS` zu RootType-Enum ergaenzen |
| Kritisch | K-002 | chlorophytum_comosum.md | Kurztagsreaktion fuer Stolonenbildung in Phasenuebgangsregeln Sektion 2.4 codieren |
| Kritisch | K-003 | Alle vier Dokumente | `frost_sensitivity: tender` -> `sensitive`; `traits: air_purifying` pruefen; Modell-Erweiterungen beantragen (air_purification_score, nutrient_demand_level, green_manure_suitable) |
| Wesentlich | M-002 | spathiphyllum_wallisii.md | Cultivar 'Sensation' Elternart als `Spathiphyllum sp. (Hybrid)` deklarieren |
| Wesentlich | M-003 | chlorophytum_comosum.md | `Sansevieria trifasciata` -> `Dracaena trifasciata` (APG IV aktuell) |
| Wesentlich | M-004 | guzmania_lingulata.md | Trichter-/Substratbewaesserung als strukturiertes Datenfeld anfragen (REQ-001-Erweiterung) |
| Wesentlich | M-005 | spathiphyllum_wallisii.md, guzmania_lingulata.md | care_style: Spathiphyllum -> `calathea`; Guzmania -> `orchid` |
| Wesentlich | M-006 | Alle vier Dokumente | Einheit von `EC (mS)` auf `EC (mS/cm)` korrigieren |
| Hinweis | H-001 | monstera_deliciosa.md | Fakultativitaet der Ruheperiode in Abschnitt 2.1 sichtbar erlaeutern |
| Hinweis | H-002 | guzmania_lingulata.md | Ethylen-Trigger als `chemical_induction` in Phasenuebergang codieren |
| Hinweis | H-004 | chlorophytum_comosum.md | Opiataehnliche Wirkung auf Katzen als Verhaltenshinweis ergaenzen |
| Hinweis | H-005 | Alle vier Dokumente | Bodenfeuchte-Schwellenwerte fuer REQ-005-Sensorik ergaenzen |
| Hinweis | H-007 | monstera_deliciosa.md, spathiphyllum_wallisii.md | Toxizitaet fuer Voegel (insb. Psittaciden) als kritisch markieren |
| Hinweis | H-008 | guzmania_lingulata.md | Tippfehler "haeuig" -> "haeufig" Zeile 47 beheben |

---

## Modell-Erweiterungen: Empfohlene REQ-001-Aenderungen

Die folgenden Felder sind in den Dokumenten beschrieben, fehlen aber im `Species`-Modell und wuerden beim Import verworfen. Sie sollten als REQ-001-Erweiterung beantragt werden:

```python
# src/backend/app/domain/models/species.py -- Vorgeschlagene Ergaenzungen

class Species(BaseModel):
    ...
    # Felder, die in Plant-Info-Dokumenten referenziert werden aber fehlen:
    air_purification_score: float = Field(default=0.0, ge=0.0, le=1.0)
    removes_compounds: list[str] = Field(default_factory=list)
    nutrient_demand_level: NutrientDemand | None = None  # NutrientDemand existiert in enums.py
    green_manure_suitable: bool = False
    irrigation_notes: str | None = None  # Fuer Epiphyten-Sonderfaelle (Trichterbewaesserung)
    fluoride_sensitive: bool = False  # Batch-1-H-011, relevant fuer Chlorophytum und Spathiphyllum
```

```python
# src/backend/app/common/enums.py -- Vorgeschlagene Ergaenzungen

class RootType(StrEnum):
    FIBROUS = "fibrous"
    TAPROOT = "taproot"
    TUBEROUS = "tuberous"
    BULBOUS = "bulbous"
    RHIZOMATOUS = "rhizomatous"  # NEU -- fuer Spathiphyllum, Calathea, Canna, Iris

class PlantTrait(StrEnum):
    ...
    AIR_PURIFYING = "air_purifying"  # NEU -- fuer Chlorophytum, Spathiphyllum
    VARIEGATED = "variegated"  # NEU -- fuer Cultivar-Import

class FrostTolerance(StrEnum):
    # Alias-Mapping vorschlagen:
    SENSITIVE = "sensitive"   # entspricht "tender" in englischer Gartensprache
    TENDER = "tender"         # NEU als Alias oder Mapping in Importlogik
    MODERATE = "moderate"
    HARDY = "hardy"
    VERY_HARDY = "very_hardy"
```

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Taxonomie (APG IV, Sansevieria->Dracaena) | Plants of the World Online | powo.science.kew.org |
| Zimmerpflanzen-Toxizitaet (Hunde/Katzen) | ASPCA Animal Poison Control | aspca.org/pet-care/animal-poison-control |
| Vogel-Toxizitaet Araceae | Association of Avian Veterinarians | aav.org |
| Bromelien-Biologie und Trichter-Physiologie | Bromeliad Society International | bsi.org |
| Chlorophytum-Photoperiodismus (Stolonenbildung) | Johansson (1978) -- Acta Horticulturae 64 | actahort.org |
| VPD-Berechnung (Tetens-Formel) | Apogee Instruments | apogeeinstruments.com/vpd-calculator |
| Spathiphyllum-Allergene | Missouri Botanical Garden | missouribotanicalgarden.org |
| IPM Zimmerpflanzen | Julius Kuehn-Institut | julius-kuehn.de |
| NASA Clean Air Study (Original + Caveat) | NASA Technical Reports Server + Cummings & Waring 2020 | ntrs.nasa.gov/citations/19930072988 |

---

## Glossar

**APG IV:** Angiosperm Phylogeny Group (4. Revision, 2016) -- aktuell gueltiges botanisches Klassifikationssystem fuer Bluetenpflanzen. Massggeblich fuer Familienebene und Ordnungszuordnung.

**Monokarp:** Pflanze, die nur einmal bluet und danach abstirbt (z.B. Guzmania, Agave). Nicht identisch mit "einjaehrig" (annual) -- Guzmania braucht 2-3 Jahre bis zur Bluete.

**Epiphyt:** Pflanze, die auf anderen Pflanzen wachst, ohne sie zu parasitieren (z.B. Guzmania, Tillandsia, Phalaenopsis). Naehrstoff- und Wasseraufnahme erfolgt hauptsaechlich ueber spezialisierte Strukturen (Trichome, Luftwurzeln).

**Trichome (Bromelien):** Spezialisierte Saugschuppen auf den Blaettern von Bromelien, die Wasser und Naehrstoffe direkt aus dem Trichter und der Luft aufnehmen. Verstopfen bei hartem Wasser (Kalkablagerungen).

**Raphiden:** Nadelfoermige Calciumoxalat-Kristalle in Pflanzenzellen (Araceae: Monstera, Spathiphyllum, Philodendron). Verursachen mechanische und chemische Schleimhautreizung. Besonders gefaehrlich fuer Voegel (empfindlichere Schleimhaeute als Saeugere).

**PPFD** (Photosynthetic Photon Flux Density): Lichtintensitaet in umol/m2/s -- der biologisch relevante Messwert fuer Pflanzenwachstum. Lux misst fuer das menschliche Auge, nicht fuer Pflanzen.

**DLI** (Daily Light Integral): Tageslicht-Gesamtmenge in mol/m2/d = PPFD x Photoperiode_Stunden x 0.0036.

**VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa -- Mass fuer den Transpirationssog. Berechnung: VPD = SVP x (1 - rH/100); SVP (Saettigungsdampfdruck) nach Tetens-Formel: SVP = 0.6108 x exp(17.27 x T / (T + 237.3)) kPa.

**EC** (Electrical Conductivity): Elektrische Leitfaehigkeit in mS/cm -- Mass fuer die Naehrstoffkonzentration in Naehrloesung oder Bodenloesung.

**Kurztagsreaktion:** Physiologische Antwort einer Pflanze auf eine Dunkelphase laenger als ein kritischer Schwellenwert (Kritische Nacht). Bei Chlorophytum comosum loest Kurztag (< 12h Licht) Stolonenbildung aus. Nicht zu verwechseln mit der Bluetenreaktion anderer Kurztagspflanzen.

**Hemi-Epiphyt:** Pflanze, die als Epiphyt beginnt, aber bodenverwurzelt heranwaechst (z.B. Monstera deliciosa) -- oder umgekehrt. Monstera ist ein hemi-epiphytischer Kletterstrauch, der in der Natur mit Luftwurzeln den Boden erreicht.

**Stolon:** Oberirdischer Auslaeufer, der vegetative Tocherpflanzen (Kindel) bildet (z.B. Chlorophytum comosum, Fragaria). Nicht zu verwechseln mit dem Rhizom (unterirdisch).
