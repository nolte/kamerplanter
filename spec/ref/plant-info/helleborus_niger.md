# Christrose — Helleborus niger

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartendialog Christrose, OBI Christrose, Pflanzen-Kölle Helleborus, Gartenratgeber Christrosen, Zulauf Gartencenter Christrose

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Helleborus niger | `species.scientific_name` |
| Volksnamen (DE/EN) | Christrose, Weihnachtsrose, Schwarze Nieswurz; Christmas Rose | `species.common_names` |
| Familie | Ranunculaceae | `species.family` → `botanical_families.name` |
| Gattung | Helleborus | `species.genus` |
| Ordnung | Ranunculales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Kälteperiode für Blüteninduktion zwingend) | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; Blüten vertragen leichten Frost bis -5°C; bei strengem Frost hängen Blüten herunter, erholen sich aber | `species.hardiness_detail` |
| Heimat | Alpen, nördlicher Balkan, nördliche Apenninen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Teilung bevorzugt; Aussaat möglich) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (Aussaat direkt nach Samenreife im Sommer) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 7, 8 (frische Samen; Kaltkeimer braucht Winter) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 12, 1, 2, 3 (Dezember bis März; daher "Weihnachtsrose") | `species.bloom_months` |

**Hinweis:** Blüte mitten im Winter ist das Alleinstellungsmerkmal. Echter Helleborus niger blüht ab Dezember bei mildem Wetter; zuverlässig Januar bis März. Samen sind Kaltkeimer — brauchen Winterperiode für Keimung.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung nach der Blüte im März/April — sehr vorsichtig, da Helleborus Wurzelstörungen schlecht verträgt. Rhizomteilung nur alle 5–8 Jahre. Aussaat frischer Samen (Kaltkeimer) dauert 1–2 Jahre bis zum Keimen, dann weitere 3–4 Jahre bis zur ersten Blüte.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile; besonders Wurzelstock | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Helleborin, Helleborein, Protoanemonin, Ranunculin | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG:** Alle Teile sind stark giftig — beim Ein-/Umpflanzen unbedingt Handschuhe tragen. Frischer Saft verursacht schwere Hautreizungen und Blasen. Bei Einnahme: sofort Arzt aufsuchen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 1, 2 (Januar/Februar, VOR dem Blütenauftrieb) | `species.pruning_months` |

**Hinweis:** Altes Laub aus dem Vorjahr im Januar/Februar vor den neuen Blüten und dem Austrieb entfernen — sonst Sclerotinia-Pilz (Helleborus-Blattschwärze). Neues Laub nach der Blüte (März/April) stehen lassen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 8–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lehmige, kalkhaltige, humusreiche Erde; pH 6,5–7,5 (leicht alkalisch); gut wasserdurchlässig; Drainagschicht | — |

**Standort:** Halbschatten bis Schatten; ideal unter Laubbäumen (Sonnenschutz im Sommer durch Laub; Licht im Winter/Frühjahr). Kalkhaltige Böden bevorzugt.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Winter) | 60–90 | 1 | false | false | high |
| Vegetatives Wachstum (Frühjahr) | 60–90 | 2 | false | false | medium |
| Vegetativ (Sommer/Ruhephase) | 90–120 | 3 | false | false | high |
| Blütenanlage (Herbst) | 30–60 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Winter)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 (Halbschatten; Winterlicht) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 (Kurztagspflanze) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 2–10 (Winterblüher; verträgt kurze Minusgrade) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | -5–5 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.2–0.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetatives Wachstum (Frühjahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Blüte (Winter) | 0:0:0 (keine Düngung) | 0.0 | 6.5–7.5 | — | — | — | — |
| Vegetativ Frühjahr | 1:1:1 | 0.6–1.0 | 6.5–7.5 | 100 | 40 | — | 2 |
| Vegetativ Sommer | 1:1:1 | 0.4–0.8 | 6.5–7.5 | 80 | 40 | — | 1 |
| Blütenanlagenphase | 0:1:1 | 0.4–0.8 | 6.5–7.5 | 80 | 30 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (gut verrottet) | eigen | organisch | 2–3 L/m² | Februar/März, August | Bodenverbesserung + Nährstoffe |
| Kalkhaltiger Dünger (Hornmehl + Kalk) | diverse | organisch | 20–30 g/m² | März | pH-Stabilisierung + N |
| Stauden-Langzeitdünger (niedrig dosiert) | Compo | organisch-mineralisch | 30–40 g/m² | März | light_feeder |
| Urgesteinsmehl (Basalt) | diverse | mineralisch | 100–200 g/m² | Frühjahr | Mineralstoffversorgung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| Feb–Mär | Vor/Nach Blüte | Kompost einarbeiten | 2–3 L/m² | Altes Laub vorher entfernen |
| Mär | Frühjahr | Niedrig dosierter Langzeitdünger | 30 g/m² | Zweite Düngung: August |
| Aug | Sommer | Nochmals Kompost oder Langzeitdünger | einmalig | Fördert Blütenanlage |

### 3.3 Besondere Hinweise zur Düngung

Christrosen sind Schwachzehrer und brauchen kaum Düngung. Ein unter Laubbäumen gepflanzter Helleborus versorgt sich durch das jährliche Laub weitgehend selbst. Kalkhaltige Böden sind wichtig — bei zu saurem Boden regelmäßig kälken. Keine Stickstoffgaben im Hochsommer oder Herbst.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; leicht kalkhaltig bevorzugt; kein Staunässe; im Sommer mäßig feucht | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2–3, 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 60 (nur alle 5–8 Jahre teilen; Wurzelstörungen vermeiden) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Altes Laub entfernen | VOR den Blüten; beugt Blattschwärze vor | hoch |
| Jan–Mär | Blüte genießen | Schutzglas bei extremem Frost | niedrig |
| Mär | Düngung | Kompost einarbeiten nach Blüte | mittel |
| Apr–Mai | Neues Laub belassen | Nicht schneiden! | — |
| Jul–Aug | Zweite Düngung | Kompost oder Langzeitdünger; Blütenanlagen | mittel |
| Okt–Nov | Standort wählen | Christrosen NICHT verpflanzen (Standorttreue!) | — |

**WICHTIG:** Christrosen sind sehr standorttreu und mögen keine Störungen — einmal gepflanzt 10–20 Jahre nicht mehr umsetzen.

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 1 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien; Honigtau; Ameisenpräsenz | leaf, shoot | nach Blüte (Frühjahr) | easy |
| Dickmaulrüssler | Otiorhynchus sulcatus | Buchtige Blattrandfraßstellen; Larven fressen Wurzeln | leaf, root | Herbst/Winter (Larven) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Helleborus-Blattschwärze | fungal (Coniothyrium hellebori) | Schwarze Flecken auf Blättern; Blätter welken | Altes Laub nicht entfernt; feuchte Bedingungen | 14–21 | alle |
| Helleborus-Ringspot-Virus | viral (HRV) | Hellgrüne Ringmuster, Blattdeformation | Blattläuse-Übertragung | — | alle |

**Blattschwärze-Vorbeugung:** Altes Laub IMMER im Januar/Februar vor dem Blütenauftrieb vollständig entfernen — das ist die wichtigste Pflegemaßnahme!

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Heterorhabditis bacteriophora (Nematoden) | Dickmaulrüssler-Larven | nach Herstellerangabe | 7–14 (Bodentemperatur >12°C) |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Altes Laub entfernen | cultural | — | Januar/Februar; vor Blütenauftrieb | 0 | Blattschwärze (Prävention) |
| Kupfer-Fungizid | chemical | Kupferoxydul | Sprühen bei ersten Symptomen | 14 | Blattschwärze |
| Nematoden (Steinernema kraussei) | biological | Nematoden | Gießen; ab 5°C Bodentemperatur | 0 | Dickmaulrüssler-Larven |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Gartenstauden |
| Anbaupause (Jahre) | Mehrjährig; Standort 10–20 Jahre; sehr standorttreu |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Schneeglöckchen | Galanthus nivalis | 0.9 | Gleiche Blütezeit; zusammen Winterflor | `compatible_with` |
| Winterlinge | Eranthis hyemalis | 0.9 | Gleiche Winterblüte; ergänzende gelbe Farbe | `compatible_with` |
| Farn | Dryopteris filix-mas | 0.8 | Gleicher Schattenstandort; sommerliche Laubkonkurrenz minimal | `compatible_with` |
| Hosta | Hosta spp. | 0.8 | Gleicher Schattenstandort; Sommerlaub ergänzt | `compatible_with` |
| Efeu (als Bodendecker) | Hedera helix | 0.7 | Bodendecker; schützt Wurzeln vor Austrocknung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| — | — | Keine bekannten Unverträglichkeiten; standorttreu | — | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Helleborus niger |
|-----|-------------------|-------------|-------------------------------------|
| Lenzrose | Helleborus orientalis | Gleiches Genus | Größere Farbvielfalt; mehr Sorten; blüht Feb–April |
| Schneeglöckchen | Galanthus nivalis | Gleiche Saison | Vollständig winterhart; einfache Pflege |
| Stiefmütterchen | Viola x wittrockiana | Winterblüher | Einjährig; einfache Beschaffung |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Helleborus niger,"Christrose;Weihnachtsrose;Christmas Rose",Ranunculaceae,Helleborus,perennial,day_neutral,herb,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Alpen, Balkan",yes,12,25,35,40,35,no,yes,false,false,light_feeder,false,hardy,"12;1;2;3"
```

---

## Quellenverzeichnis

1. [Gartendialog — Christrose Pflege](https://www.gartendialog.de/christrose-pflege/) — Standort, Schnitt, Blattschwärze
2. [OBI — Christrose pflanzen und pflegen](https://www.obi.de/magazin/garten/pflanzen/beetpflanzen/christrose) — Übersicht
3. [Pflanzen-Kölle — Christrose Pflegeratgeber](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-christrose-richtig/) — IPM, Düngung
4. [Gartenratgeber.net — Christrosen](https://www.gartenratgeber.net/pflanzen/christrosen-schneerosen-lenzrosen.html) — Kulturdaten
5. [Zulauf Gartencenter — Christrose](https://www.zulauf.ch/de/ratgeber/news/christrosen-helleborus) — Boden, Pflege
