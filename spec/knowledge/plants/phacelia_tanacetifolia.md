# Bienenfreund / Phacelia — Phacelia tanacetifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Phacelia Wikipedia, Gartenjournal.net Phacelia, Samen.de Phacelia, Agrarshop-online.com Phacelia, NCSU Extension, USDA NRCS, PMC9694782, Cover Crops Canada, GoSeed, Springer (Plant & Soil), Epic Gardening, Wiley (siehe Quellenverzeichnis)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Phacelia tanacetifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Bienenfreund, Rainfarn-Phazelie, Büschelschön; Lacy Phacelia, Blue Tansy, Fiddleneck | `species.common_names` |
| Familie | Boraginaceae | `species.family` → `botanical_families.name` |
| Gattung | Phacelia | `species.genus` |
| Ordnung | Boraginales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: keine belegte Wuchs-GDD-Basis; Literatur nennt nur Keim-/Emergenzschwelle ~3 °C, die nicht als Wuchsbasis verwendet werden darf --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebensdauer (Jahre) | — (annuell, nicht zutreffend) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht erforderlich) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: keine belegte Kurz-/Langtag-Einstufung; Blüte bei Staffelaussaat über sehr unterschiedliche Tageslängen (Mai–Sep) spricht für tagneutrale, temperaturgesteuerte Blüte → photoperiod_type=day_neutral --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterhärte-Detail | Jungpflanzen vertragen Fröste bis durchschnittlich −8 °C (Winterkill bei ~18 °F / −7,8 °C); als Gründüngung auch in Norddeutschland bis Oktober aussäbar | `species.hardiness_detail` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| Heimat | Nordamerika (Wüstenregionen Mexiko, Südkalifornien) | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (kälteverträglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5, 6, 7, 8, 9 (Staffelaussaat für Bienenweide) | `species.direct_sow_months` |
| Erntemonate | — (Gründüngung; Blüten für Bienen) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (je nach Aussaatzeitpunkt) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
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
| Kontaktallergen | true (Phacelia-Kontaktdermatitis möglich; Boraginaceae-Haare) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none (als Gründüngung: vor Samenreife einarbeiten) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (vor Einarbeitung als Gründüngung) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (als Bienenweide auf Balkon) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–15 (als Gründüngung dichter säen) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Gartenerde; pH 6,0–7,5; auch auf leichten Sandböden geeignet | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch belegter Kompensationspunkt; nur Sättigungs-/Vollsonnenangaben verfügbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch belegter Kompensationspunkt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 25–75 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert; Quellen nennen nur qualitativ "salinity rating low" --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

> **Hinweis (Freitext, nicht KA-Feld):** Phacelia ist sehr anpassungsfähig und toleriert Böden im weiten pH-Bereich 5,5–8,6; der oben genannte Vorzug 6,0–7,5 ist das Optimum (harmonisiert mit §1.6). Sie bevorzugt volle Sonne (Heimat: Wüstenregionen), verträgt aber Halbschatten und bleibt im Schatten länger grün — daher die Einstufung `partial_shade`. Pfahlwurzel mit dichten Faserwurzeln; Tiefenangaben in der Literatur reichen von 10 Zoll (~25 cm) bis ~75 cm.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | medium |
| Rosetten-Wachstum | 14–28 | 2 | false | false | high |
| Vegetativ | 21–35 | 3 | false | false | high |
| Blüte (Bienenweide) | 28–56 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (trockenverträglich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Als Gründüngungspflanze braucht Phacelia keine Düngung. Im Gegenteil: Auf nährstoffreichen Böden wächst sie üppig und kann stark werden. Gründüngungsfunktion: Die Pflanze bindet Nährstoffe im Aufwuchs und gibt diese beim Einarbeiten wieder frei. Phacelia ist nicht stickstoff-fixierend (keine Leguminose), verbessert aber die Bodenstruktur und schützt vor Erosion.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Trockenverträglich; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (kein Dünger) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Frühaussaat | Direktsaat in Reihen oder breitwürfig, 2 g/m² | hoch |
| Mai–Jun | Blüte beobachten | Bienenmagneten! Nicht mähen | niedrig |
| Jun–Aug | Einarbeitung (Gründüngung) | Vor Samenreife mulchen und einarbeiten | hoch |
| Aug–Sep | Nachsaat | Für Herbst-Bienenweide nochmals aussäen | mittel |

---

## 5. Schädlinge & Krankheiten

Phacelia ist sehr robust und praktisch schädlings- und krankheitsfrei — einer der Gründe für ihre Beliebtheit als Gründüngungspflanze.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Gründüngungspflanze |
| Empfohlene Vorfrucht | Starkzehrer (Kürbis, Mais, Kohlarten) |
| Empfohlene Nachfrucht | alle Hauptkulturen (Phacelia ist nicht familienverwandt mit Gemüsearten) |
| Anbaupause (Jahre) | keine — Phacelia ist in keiner Gemüsefamilie; universell einsetzbar |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Schwebfliegen-Anlocken (Nützlinge) | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Nützlingsförderung | `compatible_with` |
| Alle Gemüsearten | div. | 0.7 | Universelle Begleiter- und Gründüngungspflanze | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Phacelia |
|-----|-------------------|-------------|---------------------------|
| Gelbsenf | Sinapis alba | Gründüngung | Kreuzblütler; bietet andere Bodenverbesserung |
| Rotklee | Trifolium pratense | Gründüngung | Stickstoff-Fixierung! |
| Buchweizen | Fagopyrum esculentum | Gründüngung + Bienenweide | Essbar; schnellwachsend |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,bloom_months
Phacelia tanacetifolia,"Bienenfreund;Rainfarn-Phazelie;Büschelschön;Lacy Phacelia",Boraginaceae,Phacelia,annual,day_neutral,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.3,"Nordamerika",yes,8,20,90,40,12,no,yes,false,false,light_feeder,true,half_hardy,"3;4;5;6;7;8;9","5;6;7;8"
```

---

## Quellenverzeichnis

1. [Phacelia — Wikipedia](https://en.wikipedia.org/wiki/Phacelia) — Taxonomie
2. [Gartenjournal.net Phacelia](https://www.gartenjournal.net/phacelia) — Anbaupraxis, Verwendung
3. [Phacelia — Samen.de](https://samen.de/blog/phacelia-vielseitiger-helfer-im-garten.html) — Bienenweide, Gründüngung
4. [Agrarshop-online.com Phacelia](https://www.agrarshop-online.com/phacelia.php) — Aussaatraten, Agrarpraxis
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [NCSU Extension Gardener Plant Toolbox — Phacelia tanacetifolia](https://plants.ces.ncsu.edu/plants/phacelia-tanacetifolia/) — Vollsonne, Staunässe-Empfindlichkeit, Winterhärte bis 18 °F
6. [USDA NRCS Plant Guide — Lacy Phacelia (PHTA)](https://plants.sc.egov.usda.gov/DocumentLibrary/plantguide/pdf/pg_phta.pdf) — Wurzeltiefe 10–30 Zoll, Boden-pH 5,5–8,6, Standort
7. [Effect of Sowing Date on the Development of Lacy Phacelia (PMC9694782)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9694782/) — Emergenz ab ~3 °C, Frosttoleranz Jungpflanzen bis −8 °C, Phänologie
8. [Cover Crops Canada — Phacelia](https://covercrops.ca/phacelia/) — Salinity rating low (Salztoleranz), Schatten-/Spätfrosttoleranz, Drought
9. [GoSeed.com — Phacelia Cover Crop](https://goseed.com/cover-crops/phoenixphacelia/) — Boden-pH-Optimum, Kältetoleranz, Wurzelstruktur
10. [Springer (Plant and Soil) — Phacelia affects soil structure (taproot >70 cm)](https://link.springer.com/article/10.1007/s11104-019-04144-4) — Pfahlwurzel + dichte Faserwurzeln, Tiefe bis ~75 cm
11. [Epic Gardening — How to Grow Phacelia](https://www.epicgardening.com/phacelia/) — Staunässe-/Lodging-Empfindlichkeit, Vollsonne, Drought
12. [Wiley (Ecology & Evolution 2023) — C4 eudicots in Boraginaceae](https://onlinelibrary.wiley.com/doi/full/10.1002/ece3.10720) — C4 in Boraginaceae nur Euploca/Heliotropium; Phacelia = C3
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
