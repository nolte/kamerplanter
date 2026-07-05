# Oregano / Wilder Majoran — Origanum vulgare

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Oregano, Gartenrat.de Oregano, Bio-Gärtner Oregano, Naturadb Oregano

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Origanum vulgare | `species.scientific_name` |
| Volksnamen (DE/EN) | Oregano, Wilder Majoran, Dost; Oregano, Wild Marjoram | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Origanum | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-GDD-Basiswert; Origanum-Phänologiestudien nennen thermal time (°Cd), aber keine explizite Basistemperatur --> | `species.base_temp` |
| Lebensdauer (Jahre, lifespan) | 5–7 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (Blühinduktion erfolgt langtag-/photoperiodengesteuert, keine Kältepflicht zur Blüte) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h, critical day length) | <!-- DATEN FEHLEN: als Langtagblüher belegt, aber kein numerischer Stunden-Schwellwert für O. vulgare auffindbar --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Griechischer Oregano (ssp. hirtum) bis -15°C; Norddeutschland zuverlässig überwinternder Dauerstaude; mit Reisig-Abdeckung sicherer | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Vorderasien | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Aussaat Feb–Mär bei 18–22°C; sehr kleines Saatgut, nicht bedecken) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (frisch oder getrocknet; aromatischste kurz vor Blüte) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem, division | `species.propagation_methods` |
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
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Magere, kalkhaltige, durchlässige Kräutererde; pH 6,5–8,0; kein Torf; Drainagschicht | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein speziesspezifischer Kompensationspunkt (Netto-Photosynthese = 0) für O. vulgare belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein speziesspezifischer Kompensationspunkt für O. vulgare belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (verträgt lichten Halbschatten; volle Sonne maximiert Ölgehalt/Aroma) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–20 (flachwurzelnd/rhizomatös; Hauptwurzelmasse in den oberen 6–8 inches) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (Staunässe führt zu Wurzelfäule/Pythium; Drainage zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine sauberen Maas-Hoffman-Parameter für O. vulgare; verwandte O. onites zeigt bei 5 dS/m Substrat-Salinität 74–77% Ertragsverlust und Teilmortalität, ab 7 dS/m Totalausfall → Einstufung moderately_sensitive --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope für O. vulgare --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–8.0 (Optimum ~6.8; gedeiht auf kalkhaltigen, leicht alkalischen Böden) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 18 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 25 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer — Samen nur auf die Substratoberfläche streuen, nicht bedecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (Spanne 7–14 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 2 (Quellen uneinheitlich: 2–3 bzw. 3–5 Jahre bei kühler, trockener Lagerung; konservativer Ueberlappungswert gewählt) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | — (keine Vorbehandlung erforderlich) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 0.1 (sehr feines Saatgut; ca. 9.900–10.500 Samen/g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Oregano wird ueberwiegend in Anzuchtschalen/Zellplatten vorkultiviert und als Jungpflanze ausgepflanzt (siehe §1.2/§4.2); eine Flächen-Aussaatdichte fuer Direktsaat in Korn/m² ist in seriösen Quellen nicht dokumentiert --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Oreganosamen sind ausgesprochen fein (Staubsamen, TKG ~0.1 g) und Lichtkeimer — sie duerfen nur angedrueckt, keinesfalls mit Substrat bedeckt werden. Die Keimfaehigkeitsdauer wird in der Literatur uneinheitlich mit 2–3 bis 3–5 Jahren bei kuehler, trockener Lagerung angegeben; hier konservativ mit 2 Jahren markiert.

Quellen (§1.8): [Johnny's Selected Seeds — Growing Greek Oregano From Seed](https://www.johnnyseeds.com/growers-library/herbs/oregano/oregano-greek-key-growing-information.html); [True Leaf Market — Oregano Herb Growing Guide](https://trueleafmarket.com/pages/oregano-herb-growing-guide); [Eden Brothers — How to Plant Oregano Seeds](https://grow.edenbrothers.com/planting-guides/oregano-seeds/); [Richters — Getting Oregano Right](https://www.richters.com/show.cgi?page=MagazineRack%2FArticles%2Foregano.html); [Wikifarmer — Origanum vulgare: Oregano seeds](https://wikifarmer.com/library/en/article/origanum-vulgare-oregano-seeds); [Gardener's Path — How to Plant and Grow Oregano](https://gardenerspath.com/plants/herbs/grow-oregano/)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | low |
| Sämling | 21–35 | 2 | false | false | low |
| Vegetativ (Aufbau) | 42–90 | 3 | false | true | high |
| Blüte | 42–70 | 4 | false | true | high |
| Winterruhe | 90–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Aufbau)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa, stomatärer Kollaps) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-/Vollsonne-Anker; R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (ausgesprochen trockenverträglich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 7.0 | — | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.3–0.5 | 6.5–7.0 | 40 | 15 | — | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Vegetativ | 1:0:1 | 0.5–0.8 | 6.5–7.5 | 60 | 25 | — | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | 0:1:1 | 0.4–0.6 | 6.5–7.5 | 50 | 20 | — | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> **Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Für *Origanum vulgare* sind keine speziesspezifischen Phasen-Zielwerte (ppm) für Mangan, Zink, Kupfer und Molybdän aus seriösen Quellen belegt. Als Schwachzehrer auf mageren, kalkreichen Böden ist eine separate Mikronährstoff-Düngung in der Regel nicht erforderlich; bei hohem pH ist allenfalls auf Fe-/Mn-Verfügbarkeit zu achten. Werte daher als `<!-- DATEN FEHLEN -->` markiert (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Oregano ist Schwachzehrer und gedeiht auf mageren, kalkreichen Böden am besten. Auf fetten, nährstoffreichen Böden wächst er üppig, aber sein Aroma (Carvacrol, Thymol) ist deutlich schwächer. Maximal 1× jährlich im Frühjahr eine leichte organische Düngung. Niemals mineralischen Stickstoffdünger — macht Oregano wässrig und artenarm. Kalkgabe fördert das Aroma.

### 3.2 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kräuter-Dünger organisch | Neudorff Azet | organisch | 20–30 g/Pflanze | April | mediterrane Kräuter |
| Kompost (reif) | eigen | organisch | 0,5–1 L/Pflanze | April | alle Kräuter |

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 8 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Sehr trockenverträglich; eher zu wenig als zu viel; Staunässe ist fatal; leicht kalkig verträglich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 28 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Aussaat | Bei 18–22°C innen; Samen sehr klein, andrücken nicht eindecken | mittel |
| Apr | Zurückschneiden | Überwinterte Pflanzen auf neuen Austrieb kürzen | mittel |
| Mai (nach 15.) | Auspflanzen | Sonniger, magerer, kalkiger Standort | hoch |
| Jun–Aug | Ernte vor Blüte | Triebspitzen abschneiden; höchster Ölgehalt kurz vor/bei Blüte | hoch |
| Sep | Trocknen | Büschel kopfüber in warmem Luftzug trocknen | mittel |
| Okt | Winterschutz | Reisig über Pflanze legen; nicht herausschneiden | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

Oregano ist sehr robust. Starke Aromastoffe (Carvacrol, Thymol) wirken als natürliche Abwehr gegen die meisten Schädlinge.

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste (indoor/trocken) | leaf | vegetative (Trockenheit) | medium |
| Blattläuse | Aphis spp. | Kleine Kolonien (selten) | shoot | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 5–10 | vegetative |
| Wurzelfäule | fungal (Pythium spp.) | Welke, schwarze Wurzeln | Staunässe | 3–7 | alle |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|-------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | ca. 10–20/m² bei erstem Befall (Räuber:Beute ≈ 1:10–1:20) | 2–3 Wochen (Vermehrungsrate ~2× der Spinnmilbe) |
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphis spp.) | ca. 0,5–1/m² präventiv, höher bei Befall | 2–3 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphis spp.) | ca. 1–2/m² bei beginnendem Befall | 1–2 Wochen (optimal 21–25 °C, hohe Luftfeuchte) |

> **Hinweis:** Oregano ist durch seine ätherischen Öle (Carvacrol, Thymol) ohnehin schädlingsabweisend; Nützlingseinsatz ist nur bei Indoor-/Gewächshaus- oder Trockenstress-bedingtem Spinnmilben-/Blattlausbefall relevant. Aphidius/Aphidoletes wirken im Freiland weniger zuverlässig als im geschützten Anbau.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Mediterrane Kräuter (Lamiaceae) |
| Empfohlene Vorfrucht | Beliebig |
| Empfohlene Nachfrucht | Beliebig |
| Anbaupause (Jahre) | keine |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Aromaverbesserung; Schädlingsabwehr | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Möhrenfliegen-Abwehr durch Duft | `compatible_with` |
| Porree | Allium porrum | 0.8 | Gegenseitige Förderung | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.8 | Kräuterbeet; Schädlingsabwehr | `compatible_with` |
| Kohl | Brassica oleracea | 0.7 | Kohlweißling-Abwehr | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Bestäuber anlocken durch Blüten | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Fenchel hemmt Lamiaceae | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Oregano |
|-----|-------------------|-------------|---------------------------|
| Griechischer Oregano | Origanum vulgare ssp. hirtum | Unterart | Stärkeres Aroma; für Pizza-Küche |
| Majoran | Origanum majorana | Gleiche Gattung | Milder; wärmeliebender; einjährig |
| Thymian | Thymus vulgaris | Gleiche Familie | Ähnliche Standortansprüche; anderes Aroma |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Origanum vulgare,"Oregano;Wilder Majoran;Dost;Wild Marjoram",Lamiaceae,Origanum,perennial,long_day,herb,rhizomatous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.1,"Mittelmeerraum, Vorderasien",yes,6,15,60,50,35,yes,yes,false,false,light_feeder,hardy,"5;6;7;8;9","6;7;8;9"
```

---

## Quellenverzeichnis

1. [Plantura Oregano](https://www.plantura.garden/kraeuter/oregano/oregano-pflegen) — Pflege, Schnitt, Überwinterung
2. [Gartenrat.de Oregano](https://gartenrat.de/oregano/) — Anbau, Trocknen
3. [Bio-Gärtner Oregano](http://www.bio-gaertner.de/pflanzen/Oregano/Anbau) — Ökologischer Anbau
4. [Naturadb Origanum vulgare](https://www.naturadb.de/pflanzen/origanum-vulgare/) — Steckbrief, Eigenschaften
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [PFAF — Origanum vulgare](https://pfaf.org/user/plant.aspx?latinname=Origanum+vulgare) — Lebenszyklus (perennial), pH (mild sauer–leicht alkalisch), Schatten (full sun bis semi-shade), rhizomatöses Wurzelsystem, winterhart bis ~-20 °C / USDA 4–10
6. [SciELO — Floral transition in Origanum vulgare L. (photoperiodic regimes)](https://www.scielo.cl/scielo.php?script=sci_arttext&pid=S0718-58392014000300014) — Beleg Langtagblüher (long-day plant), Blühinduktion durch zunehmende Tageslänge, keine Kältepflicht
7. [ScienceDirect — Development in Origanum ssp.: phenological scale, thermal time requirements](https://www.sciencedirect.com/science/article/abs/pii/S0304423815000710) — phänologische Skala (V3→R6), thermal time (°Cd); kein expliziter Wuchs-GDD-Basiswert genannt
8. [VeggieHarvest — Oregano Growing and Harvest Information](https://veggieharvest.com/herbs/oregano-growing-and-harvest-information/) — Lebensdauer (perennial, ~5–6 Jahre), Replant-Intervall
9. [Hancioglu & Kurunç — Irrigation water salinity effects on oregano (Origanum onites L.)](https://www.sciencedirect.com/science/article/abs/pii/S0304423818309270) — Salztoleranz: 74–77 % Ertragsverlust bei 5 dS/m, Mortalität ab 5–7 dS/m (Einstufung moderately_sensitive)
10. [Sweetish Hill — How Deep Do Oregano Roots Grow?](https://sweetishhill.com/how-deep-do-oregano-roots-grow/) — flachwurzelnd, Hauptwurzelmasse obere 6–8 inches (15–20 cm)
11. [My City Garden — Container depth for growing herbs](https://www.my-city-garden.com/container-depth-growing-herbs/) — Mindest-Substrattiefe Oregano ~15 cm (6 inch), flaches Wurzelwerk
12. [ResearchGate — Temperature Effects on the Morphological Development of Origanum vulgare](https://www.researchgate.net/publication/387692693_Temperature_Effects_on_The_Morphological_Development_of_Origanum_vulgare) — moderate Temperaturen 22–25 °C optimal für Zellteilung/Wachstum (T_opt)
13. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Raubmilbe gegen Tetranychus urticae, Ausbringung/Etablierung
14. [UConn IPM — Biological Control of Aphids](https://ipm.cahnr.uconn.edu/wp-content/uploads/sites/3216/2022/12/2019Biologicalcontrolofaphidsfinal3.pdf) — Aphidius colemani / Aphidoletes aphidimyza gegen Blattläuse, Ausbringraten und Bedingungen
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: seed-profile-backfill 2026-07 -->
15. [Johnny's Selected Seeds — Growing Greek Oregano From Seed](https://www.johnnyseeds.com/growers-library/herbs/oregano/oregano-greek-key-growing-information.html) — Keimtemperatur 18–21 °C, Keimdauer 7–14 Tage, Lichtkeimer
16. [True Leaf Market — Oregano Herb Growing Guide](https://trueleafmarket.com/pages/oregano-herb-growing-guide) — Keimtemperatur 20–25 °C, Keimfähigkeitsdauer 2–3 Jahre
17. [Eden Brothers — How to Plant Oregano Seeds](https://grow.edenbrothers.com/planting-guides/oregano-seeds/) — Saattiefe max. 1/8 inch, Lichtkeimer (nicht bedecken)
18. [Richters — Getting Oregano Right](https://www.richters.com/show.cgi?page=MagazineRack%2FArticles%2Foregano.html) — Anbau-/Vermehrungspraxis, Vorkultur vs. Direktsaat
19. [Wikifarmer — Origanum vulgare: Oregano seeds](https://wikifarmer.com/library/en/article/origanum-vulgare-oregano-seeds) — Saatgutgewicht (~100 mg/1000 Samen), Keimfähigkeitsdauer 3–5 Jahre
20. [Gardener's Path — How to Plant and Grow Oregano](https://gardenerspath.com/plants/herbs/grow-oregano/) — Lichtkeimer-Bestätigung, Keimdauer 7–14 Tage bei 21 °C
<!-- /Quelle: seed-profile-backfill 2026-07 -->
