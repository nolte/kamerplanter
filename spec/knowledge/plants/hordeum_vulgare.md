# Gerste — Hordeum vulgare

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Bayerische LfL Gerste, University of California Cooperative Extension, DLG-Merkblätter Getreideanbau, Royal Horticultural Society

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hordeum vulgare | `species.scientific_name` |
| Volksnamen (DE/EN) | Gerste, Saat-Gerste; Common Barley, Cultivated Barley | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Hordeum | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4.5 | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true (nur Wintergerste) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | 30–45 | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN --> (Langtag-quantitativ, keine scharfe Schwelle belegt) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweise §1.1:** Gerste ist ein gemäßigtes C3-Getreide (kein C4/CAM). Die GDD-Basistemperatur 4,5 °C ist die in Mitteleuropa übliche Wuchs-Basis für Wintergetreide (Weizen/Gerste/Roggen/Hafer); alternativ wird in nordamerikanischen Modellen (NDAWN/ND State) 0 °C als phänologisch best-fit-Basis verwendet — dieser 0-°C-Wert ist eine Modellkonvention, NICHT die hier eingetragene agronomische Wuchs-Basis. Gerste ist eine Langtagpflanze (long-day): Sie blüht quantitativ früher bei zunehmender Tageslänge, hat aber keine scharfe kritische Tageslänge wie ein obligater Kurztag-/Langtagblüher — daher `critical_day_length_hours` als DATEN FEHLEN markiert. Wintergerste hat eine fakultative bis obligate Vernalisationsanforderung (Kältereiz ca. 3–12 °C, Optimum ~9 °C, sortenabhängig im Mittel ~32 Tage, bis ~45 Tage); Sommergerste benötigt keine Vernalisation (`vernalization_required` daher sortentypabhängig). `dormancy_required = false`: Gerste durchläuft keine vegetative Ruhephase im Lebenszyklus; eine reine Samen-Nachreife-/Keimruhe (seed dormancy) nach der Ernte ist davon zu trennen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sommergerste: frostempfindlich; Wintergerste: winterhart bis -15°C (unter Schneedecke), ohne Schnee bis -10°C; Vernalisation (Vernalization) für Wintergerste notwendig | `species.hardiness_detail` |
| Heimat | Vorderer Orient (Fruchtbarer Halbmond); domestiziert ca. 10.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Pollenpartner erforderlich (requires pollinator) | false | `species.requires_pollinator` |
| Pollenpartner-Gruppe (pollinator group) | — (leer; Selbstbefruchter) | `species.pollinator_group` |
| Kompatible Befruchtersorten (compatible pollinators) | — (leer; Selbstbefruchter) | `species.compatible_pollinators` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Bestäubung:** Gerste ist überwiegend selbstbefruchtend (autogam, ~99 % Selbstbefruchtung; oft kleistogam = die Blüte bestäubt sich im geschlossenen Zustand). Sie ist kein Obst-Fremdbefruchter und benötigt KEINEN Pollenpartner (`requires_pollinator = false`); `pollinator_group` und `compatible_pollinators` bleiben daher leer (pomologische Kreuzbefruchtungsgruppen und Befruchtersorten sind hier nicht anwendbar). Eine geringe windvermittelte Fremdbefruchtung (0–10 %) ist möglich, spielt für die Befruchtungssicherheit aber keine Rolle.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -28 (Sommergerste ab Mitte März; Wintergerste September–Oktober) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Sommergerste); 9, 10 (Wintergerste) | `species.direct_sow_months` |
| Erntemonate | 7 (Sommergerste); 6, 7 (Wintergerste) | `species.harvest_months` |
| Blütemonate | 5, 6 (Wintergerste); 6, 7 (Sommergerste) | `species.bloom_months` |

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
| Giftige Pflanzenteile | — (Nahrungsmittel; Malz, Graupen, Mehl; Bier-Rohstoff) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Gluten (Zöliakie-Relevant; Hordein-Gluten) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (außer Zöliakie/Glutenunverträglichkeit) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen; Mai–Juli-Flug) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stoppelbearbeitung nach Drusch) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (Katzengras / Sprossen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 (Einzelhalm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Drillsaat Reihenabstand 12–15 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (Sprossen/Gerstengras) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte nährstoffarme Erde; pH 6,0–7,5; gut drainiert | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point) min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt (light compensation point) max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 100–150 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | 8.0 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (% Ertragsrückgang pro dS/m) | 5.0 | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweise §1.7:** Der Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) ist für *Hordeum vulgare* nicht aus zwei unabhängigen, art-spezifischen quantitativen Quellen belegbar und daher als DATEN FEHLEN markiert (Studien nennen für Gerste primär einen Lichtsättigungspunkt von ca. 400 µmol/m²/s sowie einen relativ — ca. 73 % — niedrigeren Kompensationspunkt als Weizen, ohne absoluten µmol-Wert für Gerste). Schattentoleranz: Gerste ist auf Vollsonne (`full_sun`, ≥ 6 h direkte Sonne) gezüchtet und braucht volles Licht für maximalen Ertrag; sie ist allerdings ein vergleichsweise schattenakklimatisierungsfähiges Getreide (physiologische Anpassung, geringere Dunkelatmung), was sie toleranter als Weizen macht — dies bleibt jedoch Freitext und ändert die Standort-Einstufung `full_sun` nicht. Effektive Wurzeltiefe nach FAO-56 (Tabelle 22) Zr = 1,0–1,5 m. Staunässe: Gerste reagiert empfindlich (`sensitive`) bereits auf kurzzeitige Vernässung (Ertragsverluste bis ~70 %). Salztoleranz nach Maas & Hoffman (1977): Schwellen-ECe 8,0 dS/m (gemessen als Substrat-ECe des Sättigungsextrakts, NICHT als Gießwasser-EC), Slope 5,0 %/dS/m, Klassifikation „tolerant" — Gerste zählt zu den salztolerantesten annuellen Kulturen; der ECe-Wert > 6 dS/m ist mit der Klasse `tolerant` konsistent. Der pH-Vorzug 6,0–7,5 ist quellentreu (Gerste bevorzugt 6,0–8,0, ist aber empfindlich gegen sauren Boden pH < 5) und mit den pH-Angaben in §1.6 und §2.3 derselben Datei harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 4–8 | 1 | false | false | high |
| Bestockung | 14–35 | 2 | false | false | high |
| Schossen | 21–35 | 3 | false | false | medium |
| Ährenschieben / Blüte | 10–18 | 4 | false | false | low |
| Abreife | 21–35 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 12–17 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.1 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 14–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–6 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Schossen

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Ährenschieben / Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

**KRITISCH — Blüte:** Spätfröste bei BBCH 49–55 (Ährenschieben) können erhebliche Ertragsausfälle verursachen. Keine Bodenatmosphäre-Kältewellen in dieser Phase.

#### Phase: Abreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 (trocken = Qualitätserhalt) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.2–2.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–21 (Wasserreduktion) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm)<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5–7.5 | — | — | — | — | — | — |
| Bestockung | 3:1:2 | 0.8–1.2 | 6.5–7.5 | 80 | 30 | 20–150 | 18–70 | 4.5–15 | 0.1–2.0 |
| Schossen | 3:1:2 | 1.2–1.8 | 6.5–7.5 | 100 | 40 | 20–150 | 18–70 | 4.5–15 | 0.1–2.0 |
| Blüte | 1:2:2 | 1.0–1.5 | 6.5–7.5 | 80 | 40 | 20–150 | 18–70 | 4.5–15 | 0.1–2.0 |
| Abreife | 0:1:2 | 0.6–1.0 | 6.5–7.5 | 60 | 25 | 20–150 | 18–70 | 4.5–15 | 0.1–2.0 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweise §2.3 (Mikronährstoffe):** Die Mn/Zn/Cu/Mo-Werte sind die Gewebe-Sufficiency-Bereiche (plant tissue sufficiency ranges) für Kleingetreide (Small Grain: Gerste, Hafer, Roggen, Weizen) nach SERA-6/SCSB-394 und mappen auf `nutrient_profiles.manganese_ppm` / `nutrient_profiles.zinc_ppm` / `nutrient_profiles.copper_ppm` / `nutrient_profiles.molybdenum_ppm`. Sie gelten von „Seedling to Tillering / Jointing to Flag Leaf" bis „Flag Leaf Maturity" gleich und sind daher über die Düngephasen konstant; in der Keimung erfolgt keine Düngung (—). Plausibilitätsabgleich mit MSU E-486 (Mn 30–200, Zn 30–100, Cu 8–20, Mo 0,8–5 ppm) konsistent in derselben Größenordnung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Bestockung | time_based | 4–8 Tage; Coleoptile sichtbar (BBCH 09) |
| Bestockung → Schossen | time_based | 14–35 Tage; Haupttrieb 1 cm erhoben (BBCH 30) |
| Schossen → Blüte | time_based | 21–35 Tage; Fahnenblatt sichtbar (BBCH 37–39) |
| Blüte → Abreife | time_based | 10–18 Tage; Korn milchreif (BBCH 71) |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Ammoniumnitrat (AHL) | diverse | Flüssig-N | 28-0-0 | 15–25 kg N/ha | Schossen |
| Nitrophoska perfekt | Compo | Granulat | 15-5-20 | 30–50 g/m² | Frühsaat |
| Triple-Superphosphat | diverse | Granulat | 0-46-0 | 10–15 g/m² | Grunddüngung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Rinderdung (pelletiert) | diverse | organisch | 60–100 g/m² | Herbst/Frühjahr |
| Kompost | eigen | organisch | 3–5 L/m² | Herbst-Grunddüngung |
| Hornmehl | diverse | organisch | 50–80 g/m² | Frühsaat |

### 3.2 Besondere Hinweise zur Düngung

Gerste reagiert sehr sensibel auf N-Überdüngung (Lagergefahr). Braugerste: Niedrige N-Düngung (max. 80 kg N/ha) für niedrigen Proteingehalt (Brauqualität erfordert <11,5% Protein). Futtergerste: Höherer N-Einsatz möglich. Auf kalkreichen Böden gut geeignet (pH-Toleranz bis 8,0).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Sep–Okt | Wintergerste-Saat | Saattiefe 3–5 cm; Drillsaat; gute Saatbettvorbereitung | hoch |
| Mär–Apr | Sommergerste-Saat | Frühsaat ab März; Drillsaat | hoch |
| Apr–Mai | Wachstumskontrolle | Schädlinge und Krankheiten überwachen | mittel |
| Mai | N-Düngung Schossen | Stickstoffgabe für Vegetationsschub | mittel |
| Jun–Jul | Ernte Wintergerste | Bei Körnerfeuchte 14–15%; Drusch | hoch |
| Jul–Aug | Ernte Sommergerste | Drusch; Nachtrocknung bei Feuchtigkeit | hoch |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung (nur Wintergerste)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11–2 (Nov–Feb) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | <!-- DATEN FEHLEN --> (Feldgetreide: Andüngung/Schröpfen, kein passender Enum-Wert) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (März) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | — (Freilandüberwinterung, kein Quartier) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | — (Freiland, natürliches Tageslicht) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | — (Freiland, Niederschlag) | `overwintering_profiles.winter_quarter_watering` |

**Hinweise §4.3:** Nur Wintergerste überwintert im Freiland; sie ist `hardy` und übersteht unter geschlossener Schneedecke bis ca. -15 °C, ohne Schnee bis ca. -10 °C (siehe §1.1 Winterhärte-Detail). Eine aktive Winterschutz-Maßnahme ist im Feldbau nicht üblich (`winter_action = none`); die natürliche Schneedecke wirkt als Isolation. Im Frühjahr erfolgt keine der im Enum {uncover|move_outdoors|replant|prune|harden_off} hinterlegten Überwinterungs-Frühjahrsaktionen — die feldbauliche Frühjahrspflege (Startgabe N, ggf. Schröpfen/Walzen) lässt sich nicht verlustfrei auf das Enum abbilden, daher DATEN FEHLEN für `spring_action`. Es gibt kein frostfreies Winterquartier (Freilandüberwinterung) — die Quartier-Felder bleiben leer. Sommergerste ist nicht winterhart (`half_hardy`, siehe §1.1) und wird nicht überwintert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Blattlaus | Rhopalosiphum padi, Sitobion avenae | Kolonie auf Blättern; BYDV-Übertragung | Blatt, Ähre | Schossen, Blüte |
| Getreidehähnchen | Oulema melanopus | Blattfraß; Streifenmuster | Blatt | Schossen |
| Fritfliege | Oscinella frit | Totes Herz; Triebausfall | Trieb | Keimung |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Netzfleckenkrankheit | fungal (Pyrenophora teres) | Braune Netzflecken auf Blättern | hohe Feuchte; kühl |
| Echter Mehltau | fungal (Blumeria graminis f.sp. hordei) | Weißgrauer mehligerBelag | trocken-warm |
| Gelbrost | fungal (Puccinia striiformis) | Gelbe Streifen; Sporenlager | kühl-feucht |
| Zwergsteinbrand | fungal (Tilletia controversa) | Schwarze Sporenstatt Korn | Saatgut; Boden |
| Blattdürre | fungal (Rhynchosporium commune) | Wasserdurchtränkte Flecken → braun | feuchte Witterung |
| Gelbverzwergungsvirus BYDV | viral | Gelbfärbung; Zwergwuchs; Ertragsverlust bis 50% | Blattlaus-Übertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling |
|----------|---------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse |
| Brackwespe (Aphidius ervi) | Getreideblattläuse |
| Laufkäfer (Carabidae) | Fritfliege, Getreideblattläuse |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Fungizid (Azol) | chemical | Prothioconazol | Sprühen BBCH 31–39 | 35 | Netzflecken, Rost, Mehltau |
| Saatgutbeizung | chemical | Tebuconazol | Beize | — | Brandkrankheiten, Streifenkrankheit |
| Pyrethroid | chemical | Deltamethrin | Sprühen bei Befallsbeginn | 14 | Blattläuse, Hähnchen |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Mehltau, Gelbrost, Netzflecken |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.5 Nützlinge (Biologische Bekämpfung — Ausbringung)

| Nützling | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|---------------|-----------------|------------------|
| Zehrwespe (Aphidius colemani) | Blattläuse (Rhopalosiphum padi, Sitobion avenae) | 0,25–4 /m² je Freilassung, 3× wiederholen | Mumien nach ca. 2–3 Wochen sichtbar |
| Gallmücke (Aphidoletes aphidimyza) | Blattläuse (Rhopalosiphum padi, Sitobion avenae) | 1–10 /m² je Freilassung, wöchentlich bis Kontrolle | ca. 2–3 Wochen (Nachttemp. > 12 °C nötig) |

**Hinweise §5.5:** Diese Augmentations-Ausbringraten und Etablierungszeiten stammen aus der kommerziellen Schutzkultur (Gewächshaus/Folientunnel) und sind hier als Orientierung gelistet — *Hordeum vulgare* ist eine Freilandkultur, in der eine flächige Nützlings-Augmentation/m² praktisch unüblich und für Feldgerste nicht als belegter Praxiswert verfügbar ist (im Feld wirken die natürlichen Antagonisten aus §5.3: Marienkäfer, *Aphidius ervi*, Laufkäfer). Fachliche Wirt-Zuordnung: *Aphidius* (Zehrwespe) und *Aphidoletes* (Gallmücke) sind Blattlaus-Antagonisten und damit den Hauptschädlingen der Gerste (Getreideblattläuse, §5.1) korrekt zugeordnet — sie wirken NICHT gegen Getreidehähnchen oder Fritfliege.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Getreide (Poaceae) |
| Empfohlene Vorfrucht | Raps, Hülsenfrüchte, Kartoffel, Rübe |
| Empfohlene Nachfrucht | Winterweizen, Winterraps, Leguminosen |
| Anbaupause (Jahre) | 2–3 Jahre Pause vor erneutem Getreide auf gleicher Fläche |

**Besonderheit:** Gerste ist empfindlicher gegenüber Getreidemüdigkeit (Getreidezysten-Nematoden) als Hafer. Maximale Getreideanteile in der Fruchtfolge: 50–60%. Wintergerste eignet sich als frühe Vorfrucht für Gemüse (Ernte im Juni/Juli).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Erbse | Pisum sativum | 0.8 | Gersten-Erbsen-Gemenge; N-Fixierung; gegenseitige Stützung | `compatible_with` |
| Kleearten | Trifolium spp. | 0.8 | Untersaat; Bodenschutz nach Ernte; N-Fixierung | `compatible_with` |
| Wicke | Vicia sativa | 0.8 | Gemengepartner; erhöhter Proteingehalt | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Weizen | Triticum aestivum | Gleiche Schädlinge und Krankheiten; Konkurrenz | moderate | `incompatible_with` |
| Hafer | Avena sativa | Gleiche Schädlinge; weniger Komplementarität | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Gerste |
|-----|-------------------|-------------|-------------------------|
| Weizen | Triticum aestivum | Getreide; Sommerform | Höherer Backwert; Glutengehalt |
| Hafer | Avena sativa | Getreide; anspruchsloser | Sanierungsfrucht; glutenfrei |
| Triticale | × Triticosecale | Getreidekreuzung | Robuster; höhere Erträge auf schwachen Böden |
| Roggen | Secale cereale | Wintergetreide | Extremster Wintertolerant; sandig-saure Böden |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Hordeum vulgare,"Gerste;Saat-Gerste;Common Barley;Cultivated Barley",Poaceae,Hordeum,annual,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.1,"Vorderer Orient",limited,limited,limited,false,false,medium_feeder,false,half_hardy,"3;4;9;10","6;7","5;6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Barke,Hordeum vulgare,"two_row;malting_quality;winter_hardy",95,certified
Scarlett,Hordeum vulgare,"two_row;malting_barley;high_yield",100,certified
Quench,Hordeum vulgare,"two_row;spring_barley;malting",90,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS Database — Hordeum vulgare](https://plants.usda.gov/plant-profile/HOVU) — Taxonomie, Verbreitung
2. [Bayerische LfL — Gerste](https://www.lfl.bayern.de/ipz/getreide/023693/index.php) — Anbauempfehlungen
3. [University of California Cooperative Extension — Barley](https://ucanr.edu) — Nährstoffbedarf, IPM
4. [DLG Merkblätter Getreide](https://www.dlg.org) — Pflanzenschutz, Krankheiten
5. [Saaten-Union Sortenkatalog Gerste](https://www.saaten-union.de) — Sorteneigenschaften, Brauqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NDAWN — Barley Growing Degree Day Information (North Dakota State University)](https://ndawn.ndsu.nodak.edu/help-barley-growing-degree-days.html) — GDD-Basistemperatur Gerste (0 °C Modellbasis; Wuchsgrenze ~5,6 °C)
7. [Base and upper temperature thresholds for GDD — review (ScienceDirect, 2025)](https://www.sciencedirect.com/science/article/pii/S037837742500469X) — Basistemperatur 4,5 °C für Weizen/Gerste/Roggen/Hafer (Mitteleuropa)
8. [FAO Irrigation & Drainage Paper 56, Table 22 — Single Crop Coefficients & Rooting Depth](https://www.fao.org/4/x0490e/x0490e0e.htm) — Effektive Wurzeltiefe Gerste Zr 1,0–1,5 m
9. [FAO — Annex 1: Crop salt tolerance data (Y4263E)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Salztoleranz Gerste: ECe-Schwelle 8,0 dS/m, Slope 5,0 %/dS/m, „tolerant"
10. [USDA-ARS / USDA Agriculture Handbook 60 — Plant Salt Tolerance (Maas & Hoffman 1977)](https://www.handbook60.org/hb60/plants) — Maas-Hoffman-Salztoleranzparameter Getreide
11. [SERA-6 / SCSB-394 — Reference Sufficiency Ranges for Plant Analysis (Southern Region), Small Grain (Plank & Donohue)](https://aesl.ces.uga.edu/sera6/PUB/scsb394.pdf) — Gewebe-Sufficiency Mn 20–150, Zn 18–70, Cu 4,5–15, Mo 0,1–2,0 ppm
12. [MSU Extension E-486 — Secondary and Micronutrients for Vegetable and Field Crops](https://www.canr.msu.edu/resources/secondary_and_micro_nutrients_for_vegetable_and_field_crops_e486) — Plausibilitätsabgleich Mikronährstoff-Normalbereiche
13. [Cabrera-Bosquet et al. / Wheat & barley shade acclimation (Scientific Reports 2019)](https://www.nature.com/articles/s41598-019-46027-9) — Schattentoleranz/Vollsonne, Lichtkompensationspunkt relativ zu Weizen
14. [Wikifarmer — Barley Soil requirements](https://wikifarmer.com/library/en/article/barley-soil-preparation-soil-requirements-and-seeding-requirements) — Boden-pH-Vorzug 6,0–8,0, Empfindlichkeit gegen pH < 5
15. [Barley waterlogging tolerance (Taylor & Francis, 2023)](https://www.tandfonline.com/doi/full/10.1080/1343943X.2023.2246215) — Staunässeempfindlichkeit (sensitive), Ertragsverlust bis ~70 %
16. [Yamori et al. 2013 — Temperature response of photosynthesis in C3/C4/CAM (Review)](https://publish.uwo.ca/~dway4/files/Yamori%20et%20al.%202013.pdf) — C3-Photosynthese-T_opt gemäßigt; Gerste ~15 °C
17. [Influence of vernalization and daylength on flowering-time genes in barley (J. Exp. Bot. 2009)](https://academic.oup.com/jxb/article/60/7/2169/684156) — Gerste = Langtagpflanze; Vernalisationsanforderung Wintergerste
18. [Hybrids fine-tuning flowering time of winter barley (PMC 2022)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9011329/) — Vernalisations-Mindestdauer Wintergerste (~32 Tage Mittel, bis ~45 Tage)
19. [Zhen & Bugbee — Far-red fraction metric (J. ASHS 2021)](https://journals.ashs.org/view/journals/jashs/146/1/article-p3.xml) — Far-Red-Fraction offenes Tageslicht/direkte Sonne ≈ 0,46–0,5
20. [OGTR — The Biology of Hordeum vulgare L. (barley)](https://www.ogtr.gov.au/sites/default/files/2021-11/the_biology_of_hordeum_vulgare_l_barley_november_2021.pdf) — Autogamie/Selbstbefruchtung (~99 %), Kleistogamie, geringe Auskreuzung
21. [Koppert — Aphidius colemani / Aphidend (Aphidoletes aphidimyza)](https://www.koppert.com/aphidend/) — Nützling-Ausbringraten & Etablierungszeit (Blattlaus-Antagonisten)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
