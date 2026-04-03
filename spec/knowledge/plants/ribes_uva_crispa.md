# Stachelbeere — Ribes uva-crispa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Ribes uva-crispa, Plantura Stachelbeeren-Düngung, Floragard Ribes uva-crispa, RHS Gooseberry

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ribes uva-crispa | `species.scientific_name` |
| Volksnamen (DE/EN) | Stachelbeere, Stachelbeerstrauch; Gooseberry | `species.common_names` |
| Familie | Grossulariaceae | `species.family` → `botanical_families.name` |
| Gattung | Ribes | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; Blüten frostempfindlich (Spätfröste problematisch); Norddeutschland geeignet | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Kaukasus | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklingsvermehrung) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (je nach Sorte und Reife) | `species.harvest_months` |
| Blütemonate | 3, 4 (frühe Blüte; Spätfrostgefahr beachten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (Früchte essbar) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Dornen! Schutzhandschuhe beim Ernten und Schneiden empfohlen. Sorte 'Captivator' und 'Hinnonmäki' nahezu dornenlos.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Winterschnitt), 6 (Sommerschnitt zur Belüftung) | `species.pruning_months` |

**Schnittkonzept:** Erhaltungsschnitt: Nur 6–10 kräftige, gut verteilte Triebe stehen lassen. Äste über 4 Jahre alt entfernen. Jährlich 2–3 älteste Triebe bodennah herausnehmen; ebenso viele Jungtriebe als Ersatz stehen lassen. Offene Strauchform für bessere Belüftung (Mehltau-Prophylaxe).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 120–150 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, durchlässige Gartenerde; pH 6,0–6,5; leicht sauer; gute Drainage | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzelung (Steckling) | 42–60 | 1 | false | false | low |
| Jungpflanze (1.–2. Jahr) | 365–730 | 2 | false | false | medium |
| Blüte (Frühjahr) | 14–21 | 3 | false | false | low |
| Fruchtentwicklung | 60–90 | 4 | false | true | medium |
| Ernte | 14–28 | 5 | false | true | high |
| Sommerruhe & Rückschnitt | 30–60 | 6 | false | false | high |
| Winterruhe | 90–120 | 7 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Jungpflanze | 2:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | – | 2 |
| Blüte | 1:2:2 | 1.0–1.4 | 6.0–6.5 | 120 | 50 | – | 2 |
| Fruchtentwicklung | 1:2:3 | 1.2–1.6 | 6.0–6.5 | 140 | 60 | – | 2 |
| Ernte/Reife | 0:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | – | 1 |
| Winterruhe | 0:0:1 | 0.4–0.6 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland, bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Beerenobst-Dünger | Compo Bio | organisch | 60–80 g/m² | Februar, April | medium_feeder |
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März | N-Grundversorgung |
| Kompost | eigen | organisch | 3–4 L/m² | März, Oktober | Bodenverbesserung |
| Obstbaum-Langzeitdünger | Substral Osmocote | slow_release | 50 g/m² | April | medium_feeder |

#### Mineralisch (bei Mangel)

| Produkt | Marke | Typ | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----------|-----------------|--------|
| Kaliumsulfat | Kali&Salz | mineral | 30 g/m² | 1 | Herbst (Winterhärtung) |
| Traubendünger | Compo | mineral | nach Etikett | 1 | Fruchtentwicklung |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| Februar (Vegetationsbeginn) | N-betont | Hornspäne + Kompost | je 60 g/m² + 3L/m² | Vor Austrieb |
| April (nach Blüte) | ausgewogen | Beerenobst-Dünger | 60 g/m² | Nach Blütenfall |
| Ende Juli | KEIN N | Kaliumsulfat | 30 g/m² | Letzter Dünger! |

### 3.3 Besondere Hinweise zur Düngung

Kein Stickstoff nach Ende Juli — fördert übermäßiges Triebwachstum auf Kosten der Holzreife und Winterhärte. Magnesium-Chlorose bei sandigen Böden möglich — Bittersalz (Magnesiumsulfat, 15 g/m²) im April. Frühjahrsdüngung VOR dem Austrieb — nicht wenn schon Blätter entfaltet.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; gleichmäßige Feuchtigkeit bei Fruchtentwicklung wichtig | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 (2–3× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Winterschnitt | Öffnende Strauchform; 6–10 Triebe; älteste 2–3 bodennah entfernen | hoch |
| Feb | Erste Düngung | Hornspäne + Kompost vor Austrieb | hoch |
| Mär–Apr | Frostschutz Blüte | Vlies bei Spätfrostwarnung (Blüte ab -1°C geschädigt) | hoch |
| Apr | Zweite Düngung | Nach Blüte; Beerenobstdünger | mittel |
| Jun | Sommerschnitt | Seitentriebe auf 5 Blätter einkürzen; Mehltauprophylaxe | mittel |
| Jun–Aug | Ernte | Früchte bei Weichheit; für Marmelade kurz vor Reife | hoch |
| Jul | Letzter Dünger | Kaliumsulfat; KEIN N mehr | mittel |
| Okt–Nov | Mulchen | Kompostdecke um den Strauch | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Stachelbeerblattwespe | Nematus ribesii | Kahlfraß durch grüne Larven | leaf | vegetative | easy |
| Johannisbeerblasenlaus | Cryptomyzus ribis | Rote Blattauftreibungen (Blasen) | leaf | spring | medium |
| Stachelbeer-Glasflügler | Synanthedon tipuliformis | Bohrgänge im Holz; Zweige welken | bark, shoot | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Amerikanischer Stachelbeermehltau | fungal (Podosphaera mors-uvae) | Weißgrauer Belag auf Trieben, Blättern, Früchten | warmes, feuchtes Wetter | 5–10 | vegetative, fruiting |
| Sternrußtau | fungal (Drepanopeziza ribis) | Kleine gelbe Flecken → Blattfall | Feuchtigkeit | 7–14 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Schlupfwespen (diverse) | Blattwespenlarven | natürlich fördern | – |
| Ohrwürmer | Blattläuse, Larven | Nisthilfen aufhängen | – |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schwefel | biological | Schwefel | Stäuben/Spritzen ab Knospenaufbruch | 14 | Mehltau |
| Holzasche | cultural | K, Si | Oberflächliche Ausbringung | 0 | Mehltau (pilzhemmend) |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattwespe, Blattläuse |
| Offene Strauchform | cultural | – | Jährlicher Auslichtungsschnitt | 0 | Mehltau (Luftzirkulation) |
| Resistente Sorten | cultural | – | 'Hinnonmäki', 'Invicta', 'Pax' (mehltautolerant) | 0 | Mehltau |

### 5.5 Resistente Sorten

| Sorte | Resistenz | Besonderheit |
|-------|-----------|-------------|
| Hinnonmäki Rot/Gelb | Mehltautolerant | Fast dornenlos; Norddeutschland geeignet |
| Pax | Mehltautolerant | Wenige Dornen; großfrüchtig |
| Captivator | Tolerant | Nahezu dornenlos |
| Resistenta | Mehltauresistent | Ertragreich; Norddeutschland geeignet |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Dauergehölz (Grossulariaceae) |
| Empfohlene Nachbarschaft | Von Knoblauch, Lavendel, Tagetes profitieren |
| Anbaupause (Jahre) | Keine Neupflanzung nach Stachelbeere/Johannisbeere: 3 Jahre Pause |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Schädlingsabwehr; soll Mehltau reduzieren | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Schädlingsabwehr; Bestäuber anlocken | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematodenabwehr | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.6 | Unterschiedliche Wurzeltiefe; nutzt Halbschatten unter Strauch | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Geteilte Bodenerkrankungen | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Wirkung auf Ribes | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ribes uva-crispa |
|-----|-------------------|-------------|--------------------------------------|
| Rote Johannisbeere | Ribes rubrum | Gleiche Gattung | Weniger Dornen; frühere Ernte; einfachere Pflege |
| Schwarze Johannisbeere | Ribes nigrum | Gleiche Gattung | Mehr Vitamine; intensiveres Aroma |
| Jostabeere | Ribes × nidigrolaria | Kreuzung | Dornenlos; mehltautolerant; großfrüchtig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Ribes uva-crispa,"Stachelbeere;Stachelbeerstrauch;Gooseberry",Grossulariaceae,Ribes,perennial,long_day,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Europa, Nordafrika, Kaukasus",limited,40,40,150,150,130,no,limited,false,false,medium_feeder,false,hardy,"3;4"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hinnonmäki Rot,Ribes uva-crispa,,,"mehltautolerant;nahezu_dornenlos;mittelgroß",,,vegetatively_propagated
Hinnonmäki Gelb,Ribes uva-crispa,,,"mehltautolerant;nahezu_dornenlos;gelb",,,vegetatively_propagated
Captivator,Ribes uva-crispa,,,"nahezu_dornenlos;großfrüchtig",,,vegetatively_propagated
Resistenta,Ribes uva-crispa,,,"mehltauresistent;ertragreich",,,vegetatively_propagated
```

---

## Quellenverzeichnis

1. [Naturadb Ribes uva-crispa](https://www.naturadb.de/pflanzen/ribes-uva-crispa/) — Steckbrief, Standort
2. [Plantura Stachelbeeren düngen](https://www.plantura.garden/obst/stachelbeeren/stachelbeeren-duengen) — Düngung
3. [Floragard Ribes uva-crispa](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/beerenobst/ribes-uva-crispa) — Pflege, Schädlinge
4. [Gartendatenbank Ribes uva-crispa](http://www.gartendatenbank.de/wiki/ribes-uva_crispa) — Schnitt, Schädlinge, Krankheiten
