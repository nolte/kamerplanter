# Hafer — Avena sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Royal Horticultural Society, University of Minnesota Extension, DLG-Merkblätter Getreideanbau, Bayerische Landesanstalt für Landwirtschaft (LfL)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Avena sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Hafer, Saat-Hafer; Common Oat, Cultivated Oat | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Avena | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 5 | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | — (Sommerhafer ohne Kältebedarf; nur seltener Winterhafer vernalisationsabhängig) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (fakultativer Langtagblüher / facultative long-day, tagneutrale Schwelle nicht scharf definiert; keine kritische Tageslänge belegt) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Frühjahrs-Hafer kälteverträglich bis ca. -6°C im Saatgutstadium; Sommergetreide — friert bei strengem Winterfrost ab; Winterhafer (selten) bis -10°C; Herbstaussaat nur für Gründüngung (friert kontrolliert ab) | `species.hardiness_detail` |
| Heimat | Mittelmeer-Raum, Vorderasien (domestiziert ~2000 v. Chr.) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**Hinweis Gründüngung:** Hafer wird als Gründüngung (besonders Herbst-Hafer) sehr häufig eingesetzt. Friert kontrolliert ab, hinterlässt lockernde Biomasse und schützt vor Bodenerosion. Im Gemüsegarten wichtiger Fruchtfolge-Unterbrecher für Nematoden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat; Frühjahrssaat ab März möglich) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (kältetolerante Frühsaat ab März) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 (Sommerkorn); 8, 9 (Gründüngung-Herbstsaat) | `species.direct_sow_months` |
| Erntemonate | 7, 8 (Körnerernte); bei Gründüngung: Einarbeitung Oktober/November | `species.harvest_months` |
| Blütemonate | 6, 7 | `species.bloom_months` |

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
| Giftige Pflanzenteile | — (Nahrungsmittel; Haferflocken, Hafermehl) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen; starkes Allergen; Junibis August-Flug) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stroheinarbeitung oder Mulchen nach Drusch) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (nur Grasanbau/Katzengras-Nutzung) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 (Einzelhalm); 30–50 (Bestand) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Drillsaat: Reihenabstand 12–15 cm; Breitwurf möglich | `species.spacing_cm` |
| Indoor-Anbau | limited (Katzengras/Microgreens) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, nährstoffarme Erde; ph 6,0–7,0; durchlässig; keine schwere Gartenerde | — |

### 1.7 Umgebungs-Physiologie & Standortqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | — (kein verlässlicher artspezifischer Wert aus ≥2 Quellen belegt) `<!-- DATEN FEHLEN -->` | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 50–95 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | moderate | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | — (FAO führt Hafer nur qualitativ als „Tolerant" ohne Maas-Hoffman-Schwellenwert) `<!-- DATEN FEHLEN -->` | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — (kein Maas-Hoffman-b-Wert publiziert) `<!-- DATEN FEHLEN -->` | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis Salztoleranz:** Die FAO-Klassifikation bewertet die Kornerträge von Hafer für die reife Kultur als „Tolerant" (T), liefert jedoch keine quantitativen Maas-Hoffman-Werte (Schwelle/Slope). Im Keim- und Sämlingsstadium (germination/seedling stage) reagiert Hafer dagegen deutlich empfindlicher auf Salz — frühe Phasen sollten mit geringerer Gießwasser-EC geführt werden. Bezugsgröße der Klasse ist die Substrat-Sättigungsextrakt-Leitfähigkeit (ECe), nicht die Gießwasser-EC.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: Seed-Profile-Backfill Batch 3 (2026-07-04) -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 4 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 30 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 3–5 (KA-Feld: 3) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 5–10 (KA-Feld: 5) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3–5 (KA-Feld: 3) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark | `species.seed_profile.light_germination` |
| Vorbehandlung | <!-- keine Vorbehandlung erforderlich --> | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 25–40 (starke sortenabhängige Schwankung; Nackthafer leichter, bespelzte Sorten schwerer) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 300–350 | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):** [NDSU Agriculture — Oat Production in North Dakota](https://ag.ndsu.edu/publications/crops/oat-production-in-north-dakota); [ScienceDirect — Germination response of Oat (Avena sativa L.) to temperature and salinity using halothermal time model](https://www.sciencedirect.com/science/article/pii/S2667064X23001306); [Agri Farming — Oats Seed Germination, Period, Temperature, Process](https://www.agrifarming.in/oats-seed-germination-period-temperature-process); [Alberta Grains — Thousand kernel weight](https://www.albertagrains.com/the-growing-point/articles-library/thousand-kernel-weight); [Alberta Agriculture — Using 1,000 Kernel Weight for Calculating Seeding Rates (Agdex 100/22-1)](https://www1.agric.gov.ab.ca/$department/deptdocs.nsf/all/agdex81/$file/100_22-1.pdf); [Iowa State Extension — Fine-Tune Oat Seeding Rate This Spring](https://crops.extension.iastate.edu/cropnews/2016/03/fine-tune-oat-seeding-rate-spring); [SARE — Wild Oat (Lichtinhibition bei kongenerischer Art)](https://www.sare.org/publications/manage-weeds-on-your-farm/wild-oat/); [eos.com — Oats: A Guide On How To Raise Productivity Of The Crop (Saattiefe nach Bodenart)](https://eos.com/crop-management-guide/oats-growth-stages/); [Johnny's Selected Seeds — Seed Viability & Storage Guidelines](https://www.johnnyseeds.com/growers-library/methods-tools-supplies/harvesting-handling-storage/seed-storage-guidelines.html).
<!-- /Quelle: Seed-Profile-Backfill Batch 3 (2026-07-04) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | high |
| Bestockung | 14–28 | 2 | false | false | high |
| Schossen / Schossung | 21–35 | 3 | false | false | medium |
| Rispenschieben / Blüte | 14–21 | 4 | false | false | medium |
| Abreife | 21–35 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 (Dunkelkeimer; Licht nicht nötig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | — | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | — | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 (gleichmäßig feucht) | `requirement_profiles.irrigation_frequency_days` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

#### Phase: Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

#### Phase: Schossen / Schossung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–21 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

#### Phase: Rispenschieben / Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–21 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

#### Phase: Abreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 (trocken für Drusch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–14 (Wasserreduktion für Abreife) | `requirement_profiles.irrigation_frequency_days` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 19–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — |
| Bestockung | 3:1:2 | 0.8–1.2 | 6.0–6.8 | 80 | 30 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->— `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->`<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Schossen | 3:1:2 | 1.2–1.8 | 6.0–6.8 | 100 | 40 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->— `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->`<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Blüte | 1:2:2 | 1.0–1.6 | 6.0–6.8 | 80 | 40 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->— `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->`<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Abreife | 0:1:2 | 0.6–1.0 | 6.0–6.8 | 60 | 30 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->— `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->` | — `<!-- DATEN FEHLEN -->`<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Es liegen keine hafer- und phasenspezifischen Sollkonzentrationen (target ppm) der Nährlösung aus ≥2 unabhängigen Quellen vor; daher sind die Felder als fehlend markiert. Als allgemeine Orientierung für Gräser/Getreide gilt die Hoagland-Standardlösung (Mn ≈ 0,5 ppm, Zn ≈ 0,05 ppm, Cu ≈ 0,02 ppm, Mo ≈ 0,01 ppm); diese Werte sind jedoch nicht artspezifisch validiert und gehören nicht ungeprüft in die KA-Felder.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Bestockung | time_based | 5–10 Tage; Keimblätter sichtbar (BBCH 09–10) |
| Bestockung → Schossen | time_based | 14–28 Tage; Haupttrieb aufrecht (BBCH 30) |
| Schossen → Blüte | time_based | 21–35 Tage; Rispe sichtbar (BBCH 51–59) |
| Blüte → Abreife | time_based | 14–21 Tage; Korn in Milchreife (BBCH 71+) |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Freiland/Garten)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Nitrophoska perfekt | Compo | Granulat | 15-5-20 | 30–50 g/m² | Bestockung |
| Blaukorn / Nitrophoska blau | Compo/Hauert | Granulat | 12-12-17 | 25–40 g/m² | Frühsaat |
| Harnstoff 46% | diverse | mineralisch | 46-0-0 | 10–15 g/m² | Schossen |

#### Organisch (Freiland/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | diverse | organisch | 50–80 g/m² | Frühsaat |
| Kompost | eigen | organisch | 3–5 L/m² | Herbst-Grunddüngung |
| Hühnermist (pelletiert) | diverse | organisch | 30–60 g/m² | Frühsaat |

### 3.2 Besondere Hinweise zur Düngung

Hafer ist anspruchsloser als Weizen — er wächst auf leichteren, auch leicht sauren Böden (pH 5,5–7,0). Als Gründüngung wird er OHNE Düngung ausgesät. Im Körnerkornanbau gilt: Hauptdüngung mit Stickstoff zur Aussaat bzw. zum Schossen; Kalium und Phosphor vorab als Grunddüngung. Kein übermäßiger N-Einsatz (Lagergefahr). Hafer hat einen relativ hohen Kaliumbedarf.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 (meist Regenwasser ausreichend) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (Sommergetreide; kein Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 21–28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Planung | Saatgut beschaffen; Bodenanalyse auswerten | niedrig |
| Mär | Frühsaat | Ab Mitte März; Drillsaat oder Breitwurf; Saattiefe 2–4 cm | hoch |
| Apr | Nachkontrolle | Auflauf prüfen; Unkraut hacken | mittel |
| Mai–Jun | N-Düngung | Stickstoffgabe zum Schossen (falls Körnerkorn-Ziel) | mittel |
| Jul–Aug | Ernte | Drusch bei Kornfeuchte 14–15%; oder Schlegeln als Gründüngung | hoch |
| Aug–Sep | Herbst-Gründüngung | Hafer nach Frühgemüse als Lückenfüller | mittel |
| Okt–Nov | Einarbeitung | Abgefrorene Haferpflanzen einarbeiten | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Blattlaus (Getreideblattlaus) | Rhopalosiphum padi, Sitobion avenae | Kolonien auf Blättern und Ähren; Honigtau | Blatt, Rispe | Schossen, Blüte |
| Fritfliege | Oscinella frit | Vergilbte Blätter; totes Herz; Triebausfall | Trieb | Keimung, Bestockung |
| Thripse | Limothrips cerealium | Silbergraue Flecken; Saugschäden | Blatt, Rispe | Blüte |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Kronenrost (Crown Rust) | fungal (Puccinia coronata) | Orangegelbe Pusteln auf Blattunterseite | hohe Luftfeuchte; warm |
| Flugbrand | fungal (Ustilago avenae) | Schwarze Sporenmasse statt Körner | Saatgutinfektion |
| Echter Mehltau | fungal (Blumeria graminis f.sp. avenae) | Weißgrauer Belag | trockene Wärme |
| Hafer-Rindenbrand | fungal (Ustilago kolleri) | Braune Rispe; Körner fehlen | Saatgutbefall |
| Gelbverzwergungsvirus (BYDV) | viral | Gelbfärbung; Zwergwuchs | Blattlausübertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling |
|----------|---------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse |
| Florfliegenlarven (Chrysoperla carnea) | Blattläuse |
| Brackwespe (Aphidius ervi) | Getreideblattläuse |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Beizung (Thiram) | chemical | Thiram | Saatgutbeizung | — | Brandkrankheiten |
| Pyrethrin-Sprühung | biological | Pyrethrine | Sprühen bei Blattlausbefall | 3 | Blattläuse, Thripse |
| Schwefelkalk | chemical | Schwefelkalk | Frühjahrsspritzung | 14 | Mehltau, Rost |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Kronenrost, Mehltau |
| Weite Fruchtfolge | cultural | — | 3–4 Jahre Pause | 0 | Pilzkrankheiten |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Haferzysten-Nematode (Heterodera avenae) | Schädling (sortenabhängig) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Getreide (Poaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte (Leguminosen), Kartoffel, Raps |
| Empfohlene Nachfrucht | Hülsenfrüchte, Gemüse (Starkzehrer), Winterweizen |
| Anbaupause (Jahre) | 2–3 Jahre Pause vor erneutem Getreideanbau (gleiche Familie) |

**Besonderheit:** Hafer gilt als "Gesunder" in der Getreidefruchtfolge — er unterbricht Weizenkrankheiten (kein geteilter Wirt für Weizenpathogene). Ideal nach Weizen oder Gerste als Sanierungsfrucht. Als Gründüngung nach Sommerkulturen sehr wertvoll — unterdrückt Unkraut, bindet Stickstoff im Aufwuchs, schützt vor Erosion.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Erbse | Pisum sativum | 0.9 | Hafer-Erbsen-Gemenge: klassische Kombination; Erbse fixiert N₂; Hafer stützt Erbse | `compatible_with` |
| Wicke | Vicia sativa | 0.9 | Wicke-Hafer-Gemenge: Stickstofflieferant; Futtergemenge | `compatible_with` |
| Phacelia | Phacelia tanacetifolia | 0.7 | Blühende Gründüngungsmischung; Bienenweide | `compatible_with` |
| Alexandrinerklee | Trifolium alexandrinum | 0.8 | Stickstoff-Untersaat; Bodenbedeckung nach Ernte | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Weizen | Triticum aestivum | Gleiche Krankheiten (einige Pathogene); Konkurrenz | moderate | `incompatible_with` |
| Gerste | Hordeum vulgare | Gleiche Schädlinge (Fritfliege, Blattläuse); Konkurrenz | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Poaceae (Getreide) | `shares_pest_risk` | Blattläuse, Fritfliege, Rost | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Hafer |
|-----|-------------------|-------------|------------------------|
| Gerste | Hordeum vulgare | Gleiche Familie; Sommergetreide | Frühreifer; auch als Wintergerste; Bierbrauerei |
| Winterroggen | Secale cereale | Getreide; Gründüngung | Überwintert; tiefere Wurzeln; anspruchsloser |
| Phacelia | Phacelia tanacetifolia | Gründüngungskultur | Keine Poaceae; universeller einsetzbar |
| Erbse | Pisum sativum | Gemengepartner | Stickstoffixierung; höherer Nahrungswert |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Avena sativa,"Hafer;Saat-Hafer;Common Oat;Cultivated Oat",Poaceae,Avena,annual,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.2,"Mittelmeer, Vorderasien",limited,limited,limited,false,false,medium_feeder,true,half_hardy,"3;4;5;8;9","7;8","6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Jumbo,Avena sativa,"high_yield;medium_tall;straw_stable",95,certified
Flämingsgold,Avena sativa,"husk_free;naked_oat;high_protein",100,certified
Zorro,Avena sativa,"early;crown_rust_tolerant",90,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS Database — Avena sativa](https://plants.usda.gov/plant-profile/AVSA) — Taxonomie, Verbreitung
2. [Bayerische LfL — Haferanbau](https://www.lfl.bayern.de/ipz/getreide/023694/index.php) — Anbauempfehlungen, Sorten
3. [DLG — Getreidekrankheiten und Schädlinge](https://www.dlg.org) — IPM, Resistenzen
4. [University of Minnesota Extension — Small Grains](https://extension.umn.edu/crops/small-grains) — Nährstoffbedarf, Phasen
5. [Saaten-Union Sortenbeschreibungen Hafer](https://www.saaten-union.de) — Sorteneigenschaften
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Frontiers in Plant Science — Advancing understanding of oat phenology for crop adaptation (2022)](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.955623/full) — Hafer als vernalisationsabhängiger Langtagblüher; Sommerhafer ohne Vernalisationsbedarf; Photoperiodik
7. [King & Bacon (1992), Crop Science — Vernalization Requirement of Winter and Spring Oat Genotypes](https://acsess.onlinelibrary.wiley.com/doi/10.2135/cropsci1992.0011183X003200030019x) — Sommerhafer reagiert nicht auf Vernalisation
8. [arXiv 2308.14520 — Crop progress monitoring (cumulated degree-days oat, base 5 °C)](https://arxiv.org/pdf/2308.14520) — GDD-Basistemperatur Hafer 5 °C
9. [FAO Water Reports 61 — Annex 1: Crop salt tolerance data (Maas-Hoffman)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Hafer-Kornertrag qualitativ „Tolerant" (T), kein Schwellen-/Slope-Wert
10. [Pitann et al. (2025), J. Agronomy & Crop Science — Waterlogging impact on oat yield](https://onlinelibrary.wiley.com/doi/10.1111/jac.70031) — moderate Staunässe-Toleranz; gute Erholung von Vernässung
11. [Springer, Plant and Soil — Waterlogging effects on root/shoot growth of winter oats](https://link.springer.com/article/10.1007/BF02220191) — Wurzeltiefe bis ~80–95 cm; O₂-Verfügbarkeit nach Tiefe
12. [PFAF — Avena sativa (Oats, Common oat)](https://pfaf.org/user/Plant.aspx?LatinName=Avena+sativa) — Lichtbedarf (volle Sonne), Standortpräferenzen
13. [RHS — Avena sativa (oat)](https://www.rhs.org.uk/plants/105559/avena-sativa/details) — Sonnenstellung, Boden-pH-Vorzug
14. [Hoagland solution — Wikipedia](https://en.wikipedia.org/wiki/Hoagland_solution) — allgemeine Mikronährstoff-Referenz (Mn/Zn/Cu/Mo), nicht artspezifisch
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
