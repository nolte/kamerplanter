# Gartenrose — Rosa spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-Kölle Rosen, Gartenratgeber Rosen, Hortipendium Rosen, Grafin-von-Zeppelin Rosen

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rosa spp. | `species.scientific_name` |
| Volksnamen (DE/EN) | Gartenrose, Edelrose, Rose; Garden Rose | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Rosa | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b (je nach Art/Sorte) | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Je nach Sorte unterschiedlich: moderne Edelrosen bis -15°C; robuste Strauchrosen bis -25°C; Norddeutschland Zone 7b–8a: Hybridteerosen brauchen Winterschutz; Strauchrose gut überwinternder | `species.hardiness_detail` |
| Heimat | Nordhalbkugel (Europa, Asien, Nordamerika) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Pflanzung wurzelnackter Rosen: Herbst Oktober–November oder März–April) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9, 10 (je nach Sorte; Hagebutten Oktober–Dezember) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (je nach Sorte; einmalig/öfterblühend) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, grafting | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Dornen (physikalische Verletzung) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Pollenallergikern) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (Hauptschnitt Frühjahr); 6, 7, 8, 9 (Deadheading öfterblühender Sorten) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 50–300 (je nach Sorte) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50–100 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Kletterrosen; Hochstamm-Rosen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Rosenerde; pH 6,0–6,5; humusreich; gut drainiert | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–150 | 1 | false | false | high |
| Austrieb | 21–35 | 2 | false | false | medium |
| Vegetativ | 28–42 | 3 | false | false | medium |
| Erste Blüte | 21–42 | 4 | false | true | medium |
| Nachblüte (öfterblühend) | 28–56 | 5 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |
| Austrieb | 2:1:1 | 1.0–1.5 | 6.0–6.5 | 100 | 40 | — | 3 |
| Vegetativ | 3:1:2 | 1.5–2.0 | 6.0–6.5 | 150 | 50 | — | 3 |
| Blüte | 1:2:2 | 1.5–2.2 | 6.0–6.5 | 150 | 60 | — | 2 |
| Nachblüte | 1:2:3 | 1.2–1.8 | 6.0–6.5 | 120 | 50 | — | 2 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Rosendünger organisch | Compo Bio | organisch | 100–150 g/Pflanze | März, Mai, Anfang Juli | Rosen |
| Hornspäne | Oscorna | organisch-N | 80–100 g/Pflanze | März | Frühjahrs-Schub |
| Kompost | eigen | organisch | 3–5 L/Pflanze | Herbst (Mulch) | alle |
| Algenkalk | Neudorff Algenkalk | Kalk | 100–150 g/m² | Herbst | pH-Stabilisierung |

#### Mineralisch (ergänzend)

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Rosendünger | Compo | mineralisch | 7-5-11 | 1 | Vegetativ, Blüte |
| Bittersalz | — | Mg-Supplement | 0-0-0+16Mg | 2 | bei Mg-Mangel (Gelbblättrigkeit) |

### 3.2 Düngungsplan

| Monat | Phase | Maßnahme | Menge | Hinweise |
|-------|-------|----------|-------|----------|
| März | Austrieb | Kompost + Hornspäne | 3 L + 80 g/Pflanze | Einarbeiten |
| Mai | Blüte | Rosendünger | 100 g/Pflanze | vor erster Blüte |
| Anfang Juli | Nachblüte | Rosendünger | 80 g/Pflanze | letzter Termin! |
| Ab Juli | — | KEIN Dünger mehr | — | Holzreife vor Winter |

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Bodengießen; NIE Blätter befeuchten (Sternrußtau!); morgens gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 5, 7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Winterschutz entfernen | Kegel/Häufchen abtragen; Härtungsphase | hoch |
| Mär–Apr | Frühjahrsschnitt | Auf 3–5 Augen zurückschneiden; tote/kreuzendes Holz raus | hoch |
| Mär | Erste Düngung | Hornspäne + Kompost | mittel |
| Mai | Zweite Düngung | Rosendünger | mittel |
| Jun–Sep | Deadheading | Verblühte Blüten regelmäßig entfernen; fördert Nachblüte | mittel |
| Anf. Jul | Letzte Düngung | Rosendünger; danach kein Stickstoff mehr | hoch |
| Okt–Nov | Winterschutz | Veredelungsstelle 15–20 cm anbschütten; Kletterrose Reisig | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | earth_up | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (draußen mit Schutz) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaus | Macrosiphum rosae | Grüne/rote Kolonien an Triebspitzen | shoot | vegetative | easy |
| Rosenblattrollwespe | Blennocampa phyllocolpa | Eingerollte Blätter | leaf | vegetative | medium |
| Rosenzikade | Edwardsiana rosae | Helles Mosaik-Muster auf Blättern | leaf | vegetative, flowering | difficult |
| Spinnmilbe | Tetranychus urticae | Silbrige Blätter; feine Gespinste | leaf | flowering (Hitze) | medium |
| Rosenkäfer | Cetonia aurata | Fressen in Blüten | flower | flowering | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Sternrußtau | fungal (Diplocarpon rosae) | Schwarze Flecken mit Strahlen; Blattfall | Nässe auf Blättern | 7–14 | alle |
| Echter Mehltau | fungal (Sphaerotheca pannosa) | Weißer Belag auf jungen Blättern | Trocken+warm | 5–10 | vegetative, flowering |
| Falscher Mehltau | fungal (Peronospora sparsa) | Purpurne Flecken oben; weißgrau unten | Kühle Feuchtigkeit | 7–14 | alle |
| Grauschimmel | fungal (Botrytis cinerea) | Brauner Blütenfäulnis | Dauerregen | 3–7 | flowering |
| Rosenrost | fungal (Phragmidium mucronatum) | Orange-gelbe Pusteln | Feuchtigkeit | 7–14 | vegetative, flowering |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer | Blattläuse | natürlich einladen | — |
| Florfliege (Chrysoperla carnea) | Blattläuse | 5–10 | 14 |
| Schwebfliegen | Blattläuse | natürlich durch Begleitpflanzen | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Bodengießen | cultural | — | NIE Blätter befeuchten | 0 | Sternrußtau |
| Sternrußtau-Fallen-Blätter | cultural | — | Befallene Blätter sofort entfernen, nicht kompostieren | 0 | Sternrußtau |
| Neemöl | biological | Azadirachtin | 0,5% Sprühlösung | 3 | Blattläuse, Sternrußtau |
| Backpulver-Lösung | biological | Natriumbicarbonat | 15 g/L Sprühlösung | 0 | Echter Mehltau |
| Lavendel-/Knoblauch-Begleitung | cultural | — | Begleitpflanzen anbauen | 0 | Blattläuse |
| Fungizid (Kupfer) | chemical | Kupferoktanoat | Sprühen | 7 | Sternrußtau, Rost |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Gehölze (Rosaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte; Gründüngung (Neupflanzung nach alter Rose: Bodenaustausch!) |
| Empfohlene Nachfrucht | keine Rosaceae auf gleicher Stelle (Rosmüdigkeit) |
| Anbaupause (Jahre) | 5+ Jahre nach alter Rose (Rosmüdigkeit: Bodenpilze und Nematoden) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Lavendel | Lavandula angustifolia | 0.9 | Blattlaus-Abwehr; ästhetisch | `compatible_with` |
| Knoblauch | Allium sativum | 0.9 | Sternrußtau-Vorbeugung; Blattlaus-Abwehr | `compatible_with` |
| Salbei | Salvia officinalis | 0.8 | Schädlingsabwehr durch Duft | `compatible_with` |
| Tagetes | Tagetes patula | 0.9 | Nematoden; Blattlaus-Ablenkung | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Trap Crop | `compatible_with` |
| Katzenminze | Nepeta cataria | 0.8 | Blattlaus-Abwehr; Bestäuber | `compatible_with` |
| Thymian | Thymus vulgaris | 0.7 | Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung durch Terpene | moderate | `incompatible_with` |
| Buchsbaum | Buxus sempervirens | Nährstoffkonkurrenz; Schädlingsübertragung | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Rosa spp. |
|-----|-------------------|-------------|-------------------------------|
| Strauchrose | Rosa (Shrub Rose) | Robustere Arten | Winterhärter; Sternrußtau-resistent |
| Wildrosen | Rosa canina, R. rugosa | Gleiche Gattung | Sehr robust; Hagebutten; Bienenweide |
| Clematis | Clematis spp. | Klettergehölz | Pflegeleichter; kein Sternrußtau |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Rosa spp.,"Gartenrose;Rose;Garden Rose",Rosaceae,Rosa,perennial,long_day,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Nordhalbkugel",limited,40,40,300,200,75,no,limited,false,true,heavy_feeder,hardy,"5;6;7;8;9;10","5;6;7;8;9;10",spring_pruning,"3;4"
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle Rosen](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-rosen-richtig/) — Pflege, Düngung
2. [Gartenratgeber Rosen](https://www.gartenratgeber.net/pflanzen/rosen-buschrosen-strauchrosen.html) — Schnitt, Anbau
3. [Hortipendium Rosen im Garten](https://www.hortipendium.de/Rosen_im_Garten) — IPM, Krankheiten
4. [Grafin von Zeppelin Rosen](https://graefin-von-zeppelin.de/blogs/garten-tipps/rosen-rosa-pflanzen-pflege-standort) — Standort, Pflege
