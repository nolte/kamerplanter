# Rote Johannisbeere — Ribes rubrum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Johannisbeeren, Pflanzen-Kölle Johannisbeere, Lubera Johannisbeeren, IVA Johannisbeere

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ribes rubrum | `species.scientific_name` |
| Volksnamen (DE/EN) | Rote Johannisbeere, Ahlbeere (Norddeutschland); Red Currant, Ribes | `species.common_names` |
| Familie | Grossulariaceae | `species.family` → `botanical_families.name` |
| Gattung | Ribes | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–7b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis -30°C; in Norddeutschland absolut zuverlässig; spät blühend → wenig Spätfrostgefahr | `species.hardiness_detail` |
| Heimat | Europa (West- und Mitteleuropa) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Pflanzung als Containerpflanze Okt–Mär) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7 (Traube für Traube ernten, wenn komplett rot) | `species.harvest_months` |
| Blütemonate | 4, 5 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Auslichtungsschnitt nach der Ernte; 6–10 kräftige Äste stehen lassen) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8, 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–180 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 120–150 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, mäßig feuchte Gartenerde; pH 5,5–6,5; sandiger Lehm | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–150 | 1 | false | false | high |
| Austrieb | 14–28 | 2 | false | false | medium |
| Blüte | 14–21 | 3 | false | false | medium |
| Fruchtentwicklung | 42–56 | 4 | false | false | medium |
| Reife | 14–21 | 5 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–4000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |
| Austrieb | 2:1:1 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 2 |
| Blüte | 1:2:1 | 1.0–1.4 | 6.0–6.5 | 100 | 40 | — | 2 |
| Fruchtentwicklung | 1:2:3 | 1.2–1.8 | 6.0–6.5 | 120 | 50 | — | 2 |
| Reife | 0:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 30 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Beerendünger organisch | Compo Sana | organisch | 50–60 g/m² | Feb.–Ende Apr. | Johannisbeere, Stachelbeere |
| Kompost | eigen | organisch | 3–5 L/m² | Herbst | alle |
| Hornspäne | Oscorna | organisch-N | 60–80 g/m² | Februar | Frühjahrs-Schub |
| Obstbaumdünger | Neudorff Azet | organisch | 80–100 g/m² | März, Mai | Beerensträucher |

### 3.2 Besondere Hinweise zur Düngung

Zwei Düngungen im Frühjahr: Ende Februar (Startdüngung) und Ende April (Fruchtentwicklungs-Düngung) mit je 50–60 g/m². Nach August keine Düngung mehr — Triebe sollen vor Winter ausreifen (Frostfestigkeit). Stickstoffbetonung im Frühjahr, Kaliumbetonung ab Blüte/Fruchtansatz.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Feuchte; Trockenheit führt zu Fruchtfall | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2, 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Erste Düngung | Hornspäne + Kompost einarbeiten | mittel |
| Feb–Mär | Pflanzschnitt | Zu dichte Äste entfernen; 6–10 kräftige Triebe stehen lassen | hoch |
| Apr | Zweite Düngung | NPK-Dünger bei Fruchtansatz | mittel |
| Jun–Jul | Ernte | Trauben vollständig ernten wenn rot; Vogelnetz! | hoch |
| Jul–Aug | Schnitt nach Ernte | 3-jährige Äste entfernen; Verjüngungsschnitt | hoch |
| Okt–Nov | Mulchen | Kompost als Mulchschicht 5–8 cm | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | — | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Johannisbeer-Blattlaus | Cryptomyzus ribis | Rote Blasen auf Blättern (Blattgallen) | leaf | flowering, fruiting | easy |
| Johannisbeergallmücke | Dasineura tetensi | Deformierte, eingerollte Triebspitzen | shoot | vegetative | medium |
| Johannisbeerglasflügler | Synanthedon tipuliformis | Welkende Äste; Larven im Mark | stem | vegetative | difficult |
| Vogelfraß | div. | Abgeerntete Trauben | fruit | ripening | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Säulenrost | fungal (Cronartium ribicola) | Orangefarbene Pusteln auf Blattunterseite | Kiefern als Zwischenwirt in der Nähe | 7–14 | vegetative, fruiting |
| Echter Mehltau | fungal (Sphaerotheca mors-uvae bei Stachelbeere) | Weißer Mehlbelag | Trockenheit + Wärme | 5–10 | vegetative |
| Weißfleckigkeit | fungal (Septoria ribis) | Weiße Flecken mit braunem Rand | Feuchtigkeit | 7–14 | vegetative, fruiting |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Belag auf Beeren | Feuchtigkeit, enge Pflanzung | 3–7 | fruiting |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Auslichtungsschnitt | cultural | — | Luftdurchströmung verbessern | 0 | Mehltau, Grauschimmel |
| Vogelnetz | cultural | — | Ab Fruchtansatz bis Ernte | 0 | Vogelfraß |
| Schwefelkalk (Dormanzspritzung) | chemical | Ca-Polysulfide | Februar/März (vor Austrieb) | 14 | Mehltau, Rost |
| Neemöl | biological | Azadirachtin | 0,5% Lösung bei Blattläusen | 3 | Blattläuse |
| Befallene Äste entfernen | cultural | — | Glasflügler: befallene Äste sofort raus | 0 | Glasflügler |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Beerenobst (Grossulariaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte; Gründüngung |
| Empfohlene Nachfrucht | Nach Rodung mind. 5 Jahre Pause (Pilze im Boden) |
| Anbaupause (Jahre) | 5–7 Jahre nach Rodung |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Pilzkrankheiten-Abwehr; Abschreckung | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.7 | Schädlingsabwehr | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr; Blattläuse-Abwehr | `compatible_with` |
| Weinraute | Ruta graveolens | 0.7 | Schädlingsabwehr (traditionell) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Stachelbeere | Ribes uva-crispa | Geteilte Schädlinge + Rostpilz | moderate | `incompatible_with` |
| Kiefern | Pinus spp. | Zwischenwirt für Säulenrost (Cronartium ribicola) | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Roter Johannisbeere |
|-----|-------------------|-------------|--------------------------------------|
| Weiße Johannisbeere | Ribes rubrum (weiße Sorten) | Gleiche Art | Süßer; weniger Säure |
| Schwarze Johannisbeere | Ribes nigrum | Gleiche Gattung | Intensiveres Aroma; mehr Vitamin C |
| Stachelbeere | Ribes uva-crispa | Gleiche Gattung | Größere Früchte; süßer |
| Jostabeere | Ribes × nidigrolaria | Hybride | Größere Früchte; robuster |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type
Ribes rubrum,"Rote Johannisbeere;Ahlbeere;Red Currant;Ribes",Grossulariaceae,Ribes,perennial,long_day,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b",0.0,"Europa",limited,50,40,180,150,135,no,limited,false,false,medium_feeder,hardy,"6;7","4;5",after_harvest
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Jonkheer van Tets,Ribes rubrum,early;large_berry;high_yield,65,open_pollinated
Red Lake,Ribes rubrum,classic;long_clusters,70,open_pollinated
Rovada,Ribes rubrum,late;very_long_clusters;mildew_tolerant,80,open_pollinated
```

---

## Quellenverzeichnis

1. [Plantura Johannisbeeren](https://www.plantura.garden/obst/johannisbeeren/johannisbeeren-pflanzen) — Anbau, Pflege
2. [Pflanzen-Kölle Johannisbeere](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-johannisbeeren-richtig/) — Pflege, Düngung
3. [Lubera Johannisbeeren](https://www.lubera.com/de/gartenbuch/johannisbeeren-pflanzen-p1304) — Anbauanleitung, Sorten
4. [IVA Johannisbeere](https://www.iva.de/iva-magazin/umwelt-verbraucher/johannisbeeren-im-garten) — Praxistipps
