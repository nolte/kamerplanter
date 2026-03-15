# Brombeere — Rubus fruticosus agg.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Brombeeren düngen, Gartenratgeber Brombeere, Lubera Brombeeren, Ellis-Garten Brombeere

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rubus fruticosus agg. | `species.scientific_name` |
| Volksnamen (DE/EN) | Brombeere; Blackberry, Bramble | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Rubus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; dornenlose Sorten etwas frostempfindlicher; Norddeutschland problemlos | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Westasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Pflanzung aus Containerpflanzen März–April oder Oktober) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (keine Direktsaat; Containerpflanzen) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (je nach Sorte; frühe Sorten ab Juli, späte bis Oktober) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
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
| Rückschnitt-Typ | after_harvest (zweijährige Ruten nach Ernte bodennah entfernen; einjährige Ruten für Folgejahr) | `species.pruning_type` |
| Rückschnitt-Monate | 8, 9, 10 (nach Ernte der Sommerfrüchte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 150–200 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Spalier oder Drahtrahmen; Ruten bis 3 m lang) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, durchlässige Erde; pH 5,5–6,5; sandiger Lehm ideal | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–150 | 1 | false | false | high |
| Austrieb | 21–35 | 2 | false | false | medium |
| Vegetativ (Rutenwachstum) | 60–90 | 3 | false | false | high |
| Blüte | 21–42 | 4 | false | false | medium |
| Fruchtreife | 28–56 | 5 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Rutenwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 (trockentoleranter als Himbeere) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |
| Austrieb | 2:1:1 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 2 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 |
| Blüte | 1:2:2 | 1.2–1.8 | 6.0–6.5 | 120 | 50 | — | 2 |
| Fruchtreife | 1:3:3 | 1.0–1.5 | 6.0–6.5 | 100 | 40 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Obstbaumdünger organisch | Neudorff Azet | organisch | 100–150 g/m² | Frühjahr (März) | Beerensträucher |
| Kompost | eigen | organisch | 3–5 L/m² | Frühjahr/Herbst | alle |
| Hornspäne | Oscorna | organisch-N | 80–100 g/m² | März | medium_feeder |
| Kali-Magnesia (Patentkali) | K+S | mineralisch | 40–60 g/m² | Mai | Fruchtentwicklung |

#### Mineralisch (bei Bedarf)

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Beeren-Dünger | Compo | mineralisch | 7-3-10+2 | 1 | Blüte, Frucht |
| Bittersalz | — | Mg-Supplement | 0-0-0+16Mg | 2 | bei Mg-Mangel |

### 3.2 Besondere Hinweise zur Düngung

Brombeere: Düngung ab Mitte August einstellen! Spätdüngung fördert weiches Holz, das weniger frostfest ist. Im Frühjahr N-betonte Startdüngung, ab Blüte Kaliumbetonung für Fruchtqualität. Bei Magnesium-Mangel (gelbe Blätter zwischen grünen Adern) 10–15 g Bittersalz/m² als Blattdünger.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Feuchte in Blüte und Fruchtreife; Trockenheit führt zu kleinen Früchten | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 5 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Freilandpflanze) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Frühjahrsschnitt | Alte Ruten aus Vorjahr auf 30 cm kürzen falls nicht im Herbst; neue Ruten leicht kürzen | hoch |
| Mär | Frühjahrs-Düngung | Hornspäne + Kompost einarbeiten; Mulchschicht erneuern | mittel |
| Mai | Ruten anheften | Neue Triebe am Spalier anleiten | mittel |
| Jul–Sep | Ernte | Reife Früchte täglich aufsammeln; verhindert Botrytis | hoch |
| Aug–Okt | Schnitt nach Ernte | Abgeerntete 2-jährige Ruten bodennah entfernen | hoch |
| Okt–Nov | Mulchen | 8–10 cm organischer Mulch; schützt Wurzeln | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (draußen) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Brombeerrüssler | Anthonomus rubi | Blüten-/Knospenfraß | flower | flowering | medium |
| Blattläuse | Aphis idaei / A. ruborum | Kolonien an Triebspitzen | shoot, leaf | vegetative | easy |
| Spinnmilbe | Tetranychus urticae | Silbrige Blätter (Trockenheit) | leaf | fruiting | medium |
| Himbeerkäfer | Byturus tomentosus | Maden in Früchten | fruit | fruiting | difficult |
| Schnecken | Arion spp. | Fraß an jungen Trieben | shoot | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel | fungal (Botrytis cinerea) | Pelziger grauer Belag auf Früchten | Feuchtigkeit, enge Pflanzung | 3–7 | fruiting |
| Brombeerrost | fungal (Phragmidium violaceum) | Orange Sporenpusteln, Blattfall | Feuchtigkeit | 7–14 | vegetative |
| Ruten-Sterben | fungal (Leptosphaeria coniothyrium) | Absterbende Ruten mit violetten Flecken | Wunden, Feuchtigkeit | 14–21 | vegetative |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 5–10 | vegetative |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer | Blattläuse | natürlich einladen | — |
| Ohrwurm (Forficula) | Blattläuse | natürlich fördern | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Luftzirkulation verbessern | cultural | — | Ausreichender Abstand; Tote Ruten entfernen | 0 | Botrytis, Mehltau |
| Mulchen | cultural | — | 8–10 cm; verhindert Spritzinfektionen | 0 | Pilzkrankheiten |
| Schwefelkalk | chemical | Ca-Polysulfide | Winterspritzung (Feb.) | 14 | Mehltau, Rost |
| Kupferpräparate | chemical | Kupfer | Sprühen bei Befall | 7 | Ruten-Sterben |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Beerenobst (Rosaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte; Gründüngung |
| Empfohlene Nachfrucht | Nach Rodung: 3–4 Jahre Pause; dann Gemüse oder andere Obstarten |
| Anbaupause (Jahre) | Nach Rodung mind. 5 Jahre (Bodenpilze, Verticillium) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Pilzkrankheiten-Abwehr | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr am Rand | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Ablenkung; Bodendecker | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Himbeere | Rubus idaeus | Geteilte Krankheiten + Schädlinge; konkurrierend | severe | `incompatible_with` |
| Tomate | Solanum lycopersicum | Verticillium (geteilter Bodenpilz) | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Verticillium; geteilte Schädlinge | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Rosaceae | `shares_pest_risk` | Botrytis, Brombeerrost, Rutensterben, Rüssler | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Brombeere |
|-----|-------------------|-------------|------------------------------|
| Himbeere | Rubus idaeus | Gleiche Gattung | Frühere Ernte; zarteres Aroma |
| Boysenbeere | Rubus × loganobaccus 'Boysen' | Brombeere-Himbeere-Hybride | Süßer; feines Aroma |
| Loganbeere | Rubus × loganobaccus | Hybride | Säuerlicher; für Marmelade |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Rubus fruticosus agg.,"Brombeere;Blackberry;Bramble",Rosaceae,Rubus,perennial,long_day,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Europa, Nordafrika",limited,50,40,300,200,175,no,limited,false,true,medium_feeder,hardy,"7;8;9","5;6;7",after_harvest,"8;9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Navaho,Rubus fruticosus agg.,thornless;upright;high_yield,75,open_pollinated
Thornfree,Rubus fruticosus agg.,thornless;classic,80,open_pollinated
Loch Ness,Rubus fruticosus agg.,thornless;large_fruit;robust,75,open_pollinated
```

---

## Quellenverzeichnis

1. [Plantura Brombeeren düngen](https://www.plantura.garden/obst/brombeeren/brombeeren-duengen) — Düngung, Nährstoffe
2. [Gartenratgeber Brombeere](https://www.gartenratgeber.net/pflanzen/brombeere-im-garten-pflegen.html) — Pflege, Schnitt
3. [Lubera Brombeeren](https://www.lubera.com/de/gartenbuch/brombeeren-pflanzen-p2114) — Anbauanleitung, Sorten
4. [Ellis-Garten Brombeere](https://www.ellis-garten.de/brombeeren-rubus-fruticosus-steckbrief-pflege-verwendung/) — Steckbrief, Verwendung
