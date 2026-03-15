# Weinrebe — Vitis vinifera

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-Kölle Weintrauben, Plantura Weinreben düngen, Gaertnernwir Weinrebe, Naturadb Vitis vinifera, Hausgarten Weintrauben

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Vitis vinifera | `species.scientific_name` |
| Volksnamen (DE/EN) | Weinrebe, Weintraube; Grape Vine | `species.common_names` |
| Familie | Vitaceae | `species.family` → `botanical_families.name` |
| Gattung | Vitis | `species.genus` |
| Ordnung | Vitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C (europäische Sorten); PIWI-Sorten (pilzwiderstandsfähig) besser für Norddeutschland; auf Reblaus-resistente Unterlagen achten | `species.hardiness_detail` |
| Heimat | Vorderasien, Kaukasus, Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge oder veredelte Pflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 9, 10 (September–Oktober; für Norddeutschland frühe Sorten wählen) | `species.harvest_months` |
| Blütemonate | 6 (Juni; unscheinbar, windbestäubt/selbstfruchtbar) | `species.bloom_months` |

**Für Norddeutschland:** Früh reifende Sorten wählen — 'Lakemont' (kernlos, früh), 'Phoenix', 'Regent', 'Birstaler Muskat'. PIWI-Sorten (pilzwiderstandsfähig) stark empfohlen: 'Regent', 'Johanniter', 'Solaris' (weniger Fungizidbehandlungen nötig).

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, grafting | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Holzige Stecklinge im Winter (Dezember–Februar), 3–5 Augen lang. Bewurzelung im Gewächshaus. Veredelung auf Reblaus-resistente Unterlagen (SO4, 125 AA, Teleki 5C) schützt vor Reblaus.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Früchte (für Hunde und Katzen; Nierenversagen!) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Unbekannte Verbindungen (nephrotoxisch für Hunde/Katzen) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe (für Hunde/Katzen) / none (für Menschen) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG:** Weintrauben sind für Hunde und Katzen HOCHGIFTIG (Nierenversagen auch bei kleinen Mengen). Zugang unbedingt unterbinden!

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 1, 2, 3 (Januar–März, im laublosen Zustand; VOR dem Saftfluss) | `species.pruning_months` |

**KRITISCH:** Schnitt im laublosem Zustand (Dezember–Februar). Trauben wachsen NUR an einjährigen Trieben, die auf zweijährigem Holz stehen. Einjährige Fruchttriebe auf 2–3 Augen zurückschneiden. Je nach Erziehungsform (Einstiel, Mehrstiel, Halbbogen). Starker Rückschnitt = weniger Trauben, aber bessere Qualität.

**Warnzeichen:** Weinreben "bluten" bei zu spätem Schnitt (Saftfluss). Das ist nicht direkt schädlich, aber kräftezehrend — besser im Januar/Februar schneiden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–600 (rankend; sortenabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–400 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 150–250 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Mineralarmes, tiefgründiges Substrat; pH 6,0–7,5; durchlässig; Splitt/Kies-Anteil für Mineralisierung; Drainageschicht | — |

**Norddeutschland:** Spalier an Südwand empfohlen für maximale Wärmeausbeute. Gewächshaus oder Folientunnel verlängert die Saison und schützt vor Pilzkrankheiten (weniger Niederschlag auf Laub).

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Austrieb | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum | 60–90 | 2 | false | false | medium |
| Blüte | 7–14 | 3 | false | false | medium |
| Fruchtreife (Véraison bis Ernte) | 60–90 | 4 | false | true | high |
| Holzreife / Winterruhe | 90–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 (vollsonnig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 30–50 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 5000–15000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 5000–15000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Austrieb | 2:1:1 | — | 6.0–7.5 | 100 | 50 | — | 3 |
| Vegetativ | 2:1:2 | — | 6.0–7.5 | 120 | 60 | — | 3 |
| Fruchtreife | 1:1:3 | — | 6.0–7.5 | 80 | 50 | — | 2 |
| Holzreife | 0:1:2 | — | 6.0–7.5 | 60 | 40 | — | 1 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch/Mineralisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (gut verrottet) | eigen | organisch | 3–5 L/m² | Herbst/Frühjahr | Bodenverbesserung |
| Hornspäne | Oscorna | organisch | 50–70 g/m² | März–April | Stickstoff |
| Kaliumsulfat (Sulfate of Potash) | diverse | mineralisch | 30–50 g/m² | September | Holzreife; Fruchtqualität |
| Basaltmehl | diverse | mineralisch | 100–200 g/m² | Frühjahr | Mineralversorgung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| März–Apr | Austrieb | Kompost + Hornspäne | 3 L/m² + 50 g/m² | Pflanzung: Kompost in Pflanzloch |
| Sep | Holzreife | Kaliumsulfat | 40 g/m² | Holzreife fördern; Winterfestigkeit |
| KEIN | Stickstoff nach Jul | — | — | Stickstoff erhöht Blattkrankheiten |

### 3.3 Besondere Hinweise zur Düngung

Kein stickstoffreicher Dünger ab Juli — weiche Triebe sind anfällig für Peronospora und Oidium. Weinreben auf mineralarmem Boden auspflanzen (fördert Aromaentwicklung). Kali im September stärkt die Holzreife und Frostresistenz.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Sparsam gießen — Trockenstress fördert Aroma; kein Staunässe; Tröpfchenbewässerung ideal (Laub trockenhaltend) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–6, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Rückschnitt | Im laublosen Zustand; VOR dem Saftfluss | hoch |
| März–Apr | Pflanzung möglich | Containerware; Spalier vorbereiten | mittel |
| Jun | Fungizidbehandlung | Besonders bei Regen; PIWI-Sorten: weniger | hoch |
| Jul–Aug | Einblättern | Blätter um Trauben entfernen (Auslichten) | mittel |
| Sep–Okt | Ernte | Vollreife; Zucker messen (Oechsle-Grad) | hoch |
| Sep | Kali-Düngung | Holzreife | mittel |
| Nov | Bodenbearbeitung | Kompost einarbeiten; Rebe mulchen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 1 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

**Hinweis für Norddeutschland:** Winterschutz empfehlenswert in Zone 7b — Stammbereich mulchen; junge Pflanzen und Kübelpflanzen einwickeln oder in Schutzraum. Bei starkem Frost (unter -15°C): Gefrierschäden an Holz möglich.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Reblaus | Daktulosphaira vitifoliae | Gallen an Blättern; Wurzelgallen → Absterben | root, leaf | alle | difficult |
| Traubenwickler | Lobesia botrana | Larven in Trauben; Schimmeleintritt | fruit | Fruchtreife | medium |
| Spinnmilben | Panonychus ulmi | Rötlichbraune Blätter; Gespinste | leaf | vegetative (Hitze) | medium |
| Rebzikade | Empoasca vitis | Blattrandverbräunung ("Vergilbungskrankheit") | leaf | vegetative | difficult |

**Reblaus:** Ausschließlich auf veredelten Unterlagen (SO4, Teleki 5C) pflanzen — absoluter Schutz vor Reblaus. Europäische Sorten auf eigener Wurzel (Freilandreben ohne Unterlage) sind extrem anfällig.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Peronospora (Falscher Mehltau) | fungal-like (Plasmopara viticola) | Ölflecken auf Blättern; weißes Sporenlager unten; Trauben verdorren | Feuchtigkeit > 10 mm; Temp >12°C | 5–15 (3 Ausbrüche/Jahr) | vegetative, fruiting |
| Oidium (Echter Mehltau) | fungal (Erysiphe necator) | Weißlich-grauer Belag; Reißen der Beerenoberfläche | Trocken-warm; schlechte Luftzirkulation | 7–14 | vegetative, fruiting |
| Botrytis-Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel auf reifen Trauben | Feuchtigkeit; enge Bestandsstruktur | 3–7 | Fruchtreife |

**PIWI-Sorten:** Pilzwiderstandsfähige Sorten (Regent, Johanniter, Solaris, Phoenix, Lakemont) brauchen deutlich weniger Fungizidbehandlungen — ideal für ökologischen Anbau in Norddeutschland.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Typhlodromus pyri (Raubmilbe) | Spinnmilben | natürliche Ansiedlung | 14–28 |
| Trichogramma brassicae | Traubenwickler-Eier | nach Herstellerangabe | 7–14 |
| Lacewings / Chrysoperla | diverse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schwefel-Präparate | chemical | Schwefel | Sprühen alle 10–14 Tage | 14 | Oidium |
| Kupfer-Präparate | chemical | Kupferoxydul | Max. 3 kg Cu/ha/Jahr | 14 | Peronospora |
| Kaliumhydrogencarbonat | biological | KHCO3 | Sprühen | 0 | Oidium (schwach) |
| Einblättern / Auslichten | cultural | — | Luftzirkulation verbessern | 0 | Botrytis, Oidium |
| PIWI-Sortenwahl | cultural | — | Bei Pflanzung | 0 | Peronospora, Oidium |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| PIWI-Sorten (Regent, Johanniter): Peronospora-/Oidium-resistent | Krankheit | `resistant_to` |
| Veredelung auf SO4/Teleki: Reblaus-resistent | Schädling | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kletterpflanzen / Weichenobst |
| Anbaupause (Jahre) | Mehrjährig; Standort 20–50 Jahre |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Lavendel | Lavandula angustifolia | 0.8 | Bestäuber; Spinnmilbenabwehr; trockener Standort | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr | `compatible_with` |
| Wilde Möhre | Daucus carota | 0.7 | Schwebfliegen anlocken (Nützlinge) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kohl-Arten | Brassica spp. | Fördert Botrytis durch hohe Feuchtigkeit in Nachbarschaft | mild | `incompatible_with` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,harvest_months
Vitis vinifera,"Weinrebe;Weintraube;Grape Vine",Vitaceae,Vitis,perennial,day_neutral,vine,taproot,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Vorderasien, Kaukasus, Mittelmeerraum",yes,45,50,500,300,200,no,yes,true,true,medium_feeder,false,hardy,"6","9;10"
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle — Weintrauben](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-weintrauben-richtig/) — Pflege, Schnitt
2. [Plantura — Weinreben düngen](https://www.plantura.garden/obst/weintrauben/weinreben-duengen) — Düngung
3. [Gaertnernwir — Weinrebe](https://gaertnernwir.de/weinrebe-vitis-vinifera/) — Schädlinge, Krankheiten
4. [Naturadb — Vitis vinifera](https://www.naturadb.de/pflanzen/vitis-vinifera/) — Steckbrief
5. [Hausgarten — Weintrauben](https://www.hausgarten.net/weintrauben-vitis/) — Pflege umfassend
