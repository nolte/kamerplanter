# Cannabis — Cannabis sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Athena Ag Cannabis Blog, Royal Queen Seeds (PPFD/PAR Guide), GrowerIQ Trichome Chart, Advanced Nutrients IPM Guide, Koppert US Cannabis Biologicals, PubMed (PMC8635921 NPK Flowering), Zamnesia NPK Ratios, 2Fast4Buds Autoflower Feeding, BIRC IPM for Cannabis Pests

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cannabis sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Cannabis, Hanf, Marihuana; Cannabis, Hemp, Marijuana | `species.common_names` |
| Familie | Cannabaceae | `species.family` -> `botanical_families.name` |
| Gattung | Cannabis | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day (Photoperiod-Typen); day_neutral (Autoflower-Typen) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 (über C3-Photosynthese-Modell in Feldstudien belegt) | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 (thermophile Hauptwuchsphase; konsistent mit REQ-007 gdd_to_harvest/flowering_start. Hinweis: der niedrigere Wert ~1 °C aus Faserhanf-Feldmodellen gilt nur für die Pre-Emergenz/Keimung, nicht für die GDD-Akkumulation der Wuchs-/Blütephase) | `species.base_temp` |
| Kritische Tageslaenge (critical day length, h) | 13.75–15 (sortenabhaengig; praktische Indoor-Umschaltgrenze 12 h Licht / 12 h Dunkel) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Outdoor-Anbau in Mitteleuropa nur April–Oktober moeglich. Frostschaden bereits ab 0°C, Erntenotwendigkeit vor erstem Frost. | `species.hardiness_detail` |
| Heimat | Zentralasien (Hindu Kush), Mittelasien | `species.native_habitat` |
| Allelopathie-Score | -0.3 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; medicinal; fiber | `species.traits` |

**Rechtlicher Hinweis:** In Deutschland ist der Anbau zu Genusszwecken seit April 2024 im privaten Rahmen nach dem Konsumcannabisgesetz (KCanG) in begrenztem Umfang erlaubt (max. 3 Pflanzen pro Person, nur fuer Personen ueber 18). Die spezifischen Regelungen sind laenderabhaengig. Kamerplanter dient ausschliesslich der Anbauunterstuetzung im gesetzlich zulaessigen Rahmen.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7–8) Outdoor sowie ganzjaehrig Indoor.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 2–4 (Indoor-Keimung; Auspflanzen nach den Eisheiligen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14–21 (nur Outdoor) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5 (nach Eisheiligen); Indoor ganzjaehrig | `species.direct_sow_months` |
| Erntemonate | 9; 10 (Outdoor Photoperiod); Indoor ganzjaehrig je nach Anbausystem | `species.harvest_months` |
| Bluetemonate | 8; 9 (Outdoor); Indoor je nach Lichtsteuerung | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 22–28°C
- Keimdauer: 1–5 Tage (in feuchtem Tuch oder Jiffy-Peat-Pellets)
- Saattiefe: 0.5–1 cm (in feuchter Erde oder direkt in Anzuchtwuerfel)
- Stecklinge (Klone): Aus vegetativen Mutterpflanzen, Bewurzelung in 7–14 Tagen in Coco oder Steinwolle; ideal mit Bewurzelungsgel (z.B. Clonex)

**Samentypen:**
- **Regulaer (Regular):** Unveredelt, zeigt 50% maennliche / 50% weibliche Pflanzen. Nur weibliche Pflanzen bilden Bluetenstande. Muss sexiert werden.
- **Feminisiert (Feminized):** Genetisch zu >99% weiblich. Standard fuer den Hobbygaertner.
- **Autoflower (Automatisch):** Bluete wird durch Alter (nicht Lichtperiode) ausgeloest. Basis: *Cannabis ruderalis* x *sativa/indica*. Kuerzer (60–85 Tage Gesamtlaufzeit), weniger ertragreich, robuster. Kein Lichtumschalten noetig.

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (psychoaktive THC-Verbindungen; gastrointestinale und neurologische Symptome) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (THC-Vergiftung; ASPCA-Warnung) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true (Blueten und Harz mit THC; Kinder reagieren viel empfindlicher als Erwachsene) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | flowers; leaves; resin; all_parts | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | THC (Tetrahydrocannabinol); CBD; Terpene | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (abhaengig von THC-Gehalt und Tier-/Koerpermasse) | `species.toxicity.severity` |
| Kontaktallergen | true (Harz und Trichome koennen Kontaktdermatitis ausloesen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Pollen von maennlichen Pflanzen koennen Pollenallergie ausloesen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7 (waehrend Vegetationsphase; kein Rueckschnitt in Bluete!) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 11–25 (Autoflower: 11–15 L; Photoperiod: 18–25 L) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 60–300 (sortenabhaengig; Autoflower: 60–100 cm; Photoperiod Sativa: 150–300 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–120 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80–120 | `species.spacing_cm` |
| Indoor-Anbau | yes (Hauptanbauform in DE; vollstaendige Kontrolle ueber Umgebung) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sichtschutz erforderlich; Autoflower oder kompakte Sorten) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (optimale Kombination aus Schutz und natuerlichem Licht) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (bei Sativa-dominierten Sorten und bei SCROG) | `species.support_required` |
| Substrat-Empfehlung (Topf) | **Coco/Perlite (60/40)** fuer Hydroponik mit haeufigerem Giessen; **Cannabis-Erde** (z.B. Biobizz Light Mix, Plagron Lightmix) fuer Boden-Anbau; **Steinwolle/Rockwool** fuer Advanced Hydro. pH-Puffer beachten. | -- |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> nicht belegt (keine zwei unabhaengigen serioesen Quellen mit konkretem LCP-Wert fuer Cannabis sativa) | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (min. 6–8 h direkte Sonne; hohe Lichttoleranz bis ~2000 µmol/m²/s) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–60 (im Topf/Beet aktive Hauptwurzelzone; ~50% der Wurzelbiomasse in oberen 20–50 cm, Pfahlwurzel im Freiland bis >130 cm) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz (waterlogging tolerance) | sensitive (Wurzeln benoetigen Sauerstoff; Staunaesse fuehrt zu Wurzelfaeule) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (signifikante Biomassereduktion ab ECe ~4 dS/m) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | ~2 (Biomasse bis ~2 dS/m kaum reduziert; ab 4 dS/m deutliche Einbussen — kein offizieller Maas-Hoffman-Wert) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> nicht belegt (kein offizieller Maas-Hoffman-Slope fuer Cannabis sativa publiziert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.0 (Erde); Coco/Hydro 5.5–6.1 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

#### Photoperiod-Typ (Standard-Sorten)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 1–5 | 1 | false | false | low |
| Saemling (seedling) | 7–14 | 2 | false | false | low |
| Vegetativ (vegetative) | 21–63 (Indoor steuerbar; Outdoor variiert) | 3 | false | false | medium |
| Vorblüte / Streckphase (pre-flowering) | 7–14 | 4 | false | false | medium |
| Hauptblüte (flowering) | 42–70 (sortenabhaengig) | 5 | false | false | medium |
| Reifung / Spaetbluete (late_flowering) | 7–14 | 6 | false | false | high |
| Ernte / Trocknung (harvest) | 7–14 (Schnitt und Haengen) | 7 | true | true | high |

#### Autoflower-Typ (Cannabis ruderalis-Hybriden)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 1–5 | 1 | false | false | low |
| Saemling | 7–10 | 2 | false | false | low |
| Vegetativ | 14–21 (kuerzere Vegphase; Autoflower typisch) | 3 | false | false | medium |
| Bluete (auto-triggered) | 35–56 | 4 | false | false | medium |
| Reife | 7–14 | 5 | true | true | high |

**Gesamtlaufzeit Autoflower:** 60–90 Tage ab Keimung.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–75 (kein Direktlicht; gedaempft) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–5 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 18 (Indoor) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | Substrat durch Sprueher feucht halten; kein aktives Giessen bis zur Wurzelbildung | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 (Sprueher) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (Seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 18 (Photoperiod); 18–20 (Autoflower) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 18/6 (Photoperiod); 18–20 (Autoflower) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 800–1200 (CO2-Anreicherung lohnt sich ab 400+ PPFD) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Coco); 2–3 (Erde) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vorblüte / Streckphase (Pre-Flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 35–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12/12 (Umschalten auf Bluete bei Photoperiod) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 1000–1500 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptbluete (Flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 38–50 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12/12 (Photoperiod); unveraendert (Autoflower) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 1000–1500 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Coco); 2–3 (Erde) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 600–1200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Spaetbluete / Reifung (Late Flowering)

**Ziel dieser Phase: Terpene aufbauen, Trichome reifen lassen, Flush vorbereiten.**

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 35–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12/12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 (Temperaturgefaelle foerdert Terpene und Anthocyan-Faerbung) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 35–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 35–45 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–1.6 (nicht ueber 1.8 kPa) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 800–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (weniger giessen; Flush-Phase) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
#### Ergaenzende Klimaphysiologie je Phase (VPD, T_opt, Far-Red)

VPD-Schwelle (`vpd_threshold_kpa`) = oberer kritischer VPD-Wert je Phase; daraus abgeleitet aus den oben gelisteten VPD-Zielen. Photosynthese-Temperatur-Optimum (`photosynthesis_temp_opt_c`) ist artweit (nicht phasenspezifisch unterschiedlich belegbar).

| Phase | VPD-Schwelle (kPa) | VPD-Sensitivitaet | Photosynthese-T_opt (°C) | Far-Red-Fraction FR/(R+FR) |
|-------|--------------------|-------------------|--------------------------|----------------------------|
| Keimung / Saemling | 0.8 | high | 25–35 | <!-- DATEN FEHLEN --> |
| Vegetativ | 1.2 | medium | 25–35 | <!-- DATEN FEHLEN --> |
| Vorblüte / Streckphase | 1.4 | medium | 25–35 | <!-- DATEN FEHLEN --> |
| Hauptbluete | 1.6 | high | 25–35 | <!-- DATEN FEHLEN --> |
| Spaetbluete / Reifung | 1.6 (nicht > 1.8) | high | 25–35 | <!-- DATEN FEHLEN --> |

- `requirement_profiles.vpd_threshold_kpa` — oberer VPD-Grenzwert je Phase
- `requirement_profiles.vpd_sensitivity` — high in Bluete (Botrytis-/Bud-Rot-Risiko bei hoher Feuchte), high in Keimung (Austrocknungsgefahr), sonst medium
- `requirement_profiles.photosynthesis_temp_opt_c` — 25–35 °C breites Plateau; Drug-Typen optimal 30–35 °C, Faser-Typen ~30 °C (artweit, peer-reviewed)
- `requirement_profiles.far_red_fraction` — <!-- DATEN FEHLEN --> kein artspezifischer physiologischer Sollwert pro Phase belegbar; Far-Red wirkt sortenabhaengig (Shade-Avoidance/Emerson-Effekt), publizierte Spektren sind Beleuchtungsempfehlungen, kein Pflanzenbedarf
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0 | — | — | — | — |
| Saemling | 2:1:1 | 0.4–0.8 | 5.8–6.2 | 80 | 30 | 20 | 2 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 5.8–6.2 | 150 | 50 | 30 | 3 |
| Vorblüte | 2:2:2 | 1.5–2.0 | 5.8–6.2 | 130 | 50 | 30 | 2 |
| Hauptbluete | 1:3:4 | 1.6–2.2 | 6.0–6.5 | 120 | 60 | 40 | 2 |
| Spaetbluete | 0:2:3 | 1.0–1.6 | 6.0–6.5 | 80 | 40 | 30 | 1 |
| Flush (2 Wo. vor Ernte) | 0:0:0 | 0.0–0.4 | 6.0 | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronaehrstoffe (Spurenelemente) je Phase — elementare Konzentration in der Naehrloesung (ppm):**

Spannen decken Cannabis-spezifische Empfehlungen (NCSU, Bluetephase) und allgemeine Hydroponik-Sufficiency-Bereiche ab. Werte gelten fuer veg./Bluete; in Keimung/Flush entfaellt die Spurenduengung (—).

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Saemling | 0.3–0.6 | 0.1–0.3 | 0.05–0.1 | 0.03–0.07 |
| Vegetativ | 0.5–1.0 | 0.2–0.5 | 0.1–0.2 | 0.05–0.1 |
| Vorblüte | 0.5–1.0 | 0.2–0.5 | 0.1–0.2 | 0.05–0.1 |
| Hauptbluete | 0.5–0.9 | 0.1–0.3 | 0.1–0.18 | 0.075–0.1 |
| Spaetbluete | 0.3–0.6 | 0.1–0.2 | 0.05–0.15 | 0.05–0.08 |

KA-Felder: `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm`, `nutrient_profiles.molybdenum_ppm`
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis pH:** Coco/Hydro: 5.5–6.1; Erde: 6.0–7.0.

### 2.4 Phasenubergangsregeln

| Von -> Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung -> Saemling | time_based | 1–5 Tage | Keimwurzel (Taproot) sichtbar; Kotyledonen entfaltet |
| Saemling -> Vegetativ | time_based | 7–14 Tage | 2–3 echte Blattpaare; gesundes Gruengewebe |
| Vegetativ -> Vorblüte | event_based | — | **Photoperiod:** Umschalten auf 12/12; **Autoflower:** nach ~21 Tagen automatisch |
| Vorblüte -> Hauptbluete | time_based | 7–14 Tage | Erste weisse Haare (Pistillen) sichtbar; Bluetenzentren formen sich |
| Hauptbluete -> Spaetblüte | conditional | 42–70 Tage | Pistillen werden braun/orange (>50%); Trichome trueb |
| Spaetbluete -> Ernte | event_based | — | Trichome 70–90% trueb + 10–20% bernstein; keine klaren Trichome mehr |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco) — Dreiteiligsystem General Hydroponics

| Produkt | Marke | Typ | NPK | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Flora Micro | General Hydroponics | base | 5-0-1 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 4 | veg, pre-flower |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 4 | flower, late |
| CALiMAGic | General Hydroponics | supplement | 1-0-0+Ca+Mg | 2 | alle |
| Liquid KoolBloom | General Hydroponics | booster | 0-10-10 | 5 | peak flowering |
| Dry KoolBloom | General Hydroponics | booster | 2-45-28 | 5 | flush-start |

#### Mineralisch (Indoor/Coco) — Canna

| Produkt | Marke | Typ | Mischprioritaet | Phasen |
|---------|-------|-----|-----------------|--------|
| Canna Coco A+B | Canna | base | 3+4 | alle (Coco) |
| CannaZym | Canna | supplement | 2 | alle |
| Cannazol PK 13/14 | Canna | booster | 5 | Woche 6–7 Bluete |
| Cannaboost | Canna | stimulator | 5 | Hauptbluete |

#### Organisch (Erde / Outdoor)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Biobizz Grow | Biobizz | organisch-fluessig | 2–4 ml/L | Vegetativ |
| Biobizz Bloom | Biobizz | organisch-fluessig | 2–4 ml/L | Bluete |
| Biobizz TopMax | Biobizz | organisch-booster | 1–4 ml/L | Hauptbluete |
| Hornspäne | Oscorna | organisch-N | 80–120 g/pot (als Topsubstrat) | Vegetativ |
| Bat Guano (Fledermausdung) | diverse | organisch-P | 2–5 g/L Substrat | Bluete |
| Wurmhumus | FoxFarm/eigen | organisch | 10–20% Substratanteil | Grundsubstrat |

### 3.2 Duengungsplan (Beispiel Coco/Hydro, ml/L)

| Woche | Phase | EC (mS) | pH | Flora Micro | Flora Gro | Flora Bloom | CalMag | Hinweise |
|-------|-------|---------|-----|-------------|-----------|-------------|--------|----------|
| 1 | Keimung | 0.0–0.4 | 5.8–6.0 | — | — | — | — | Nur RO/weiches Wasser |
| 2 | Saemling | 0.4–0.6 | 5.8–6.0 | 0.5 | 0.5 | 0.5 | 0.5 | 25% Stärke |
| 3–4 | Vegphase Early | 0.8–1.2 | 5.8–6.0 | 1.5 | 1.5 | 0.5 | 1.0 | N-dominiert |
| 5–7 | Vegphase Late | 1.2–1.8 | 5.8–6.2 | 2.0 | 2.5 | 1.0 | 1.0 | Auf Bluete vorbereiten |
| 8 | Streckphase | 1.5–2.0 | 5.9–6.2 | 2.0 | 1.5 | 2.0 | 1.0 | 12/12 umschalten |
| 9–11 | Hauptbluete | 1.8–2.2 | 6.0–6.5 | 2.0 | 0.5 | 3.0 | 1.0 | PK-Booster ab Wo. 10 |
| 12–13 | Spaetbluete | 1.4–1.8 | 6.0–6.5 | 1.5 | — | 2.5 | 0.5 | N reduzieren |
| 14–15 | Flush | 0.0–0.4 | 6.0 | — | — | — | — | Nur Wasser; Chlorophyll auswaschen |

### 3.3 Mischungsreihenfolge (Kritisch — Ausfaellungen vermeiden)

> **Ausfaellungen entstehen wenn Ca-Ionen auf Sulfate/Phosphate treffen. Reihenfolge strikt einhalten!**

1. Silikat-Additive (falls verwendet) — separat aufloesen
2. CalMag / Ca+Mg-Supplement — als erstes in Reservoir
3. Flora Micro (oder Base A) — Ca + Mikro
4. Flora Gro (oder N-Quelle)
5. Flora Bloom (oder PK-Quelle — Phosphate NACH Calcium!)
6. Booster / Zusaetze
7. pH-Korrektur (pH Down = Phosphorsaeure/Salpetersaeure; IMMER zuletzt)

### 3.4 Besondere Hinweise zur Duengung

**Flush-Protokoll:** 1–2 Wochen vor der Ernte nur reines Wasser geben (EC 0.0–0.4 mS). Ziel: Restnaehrstoffe aus Substrat und Pflanze auswaschen. Geschmack und Rauchqualitaet werden verbessert. Nicht benoetigt bei gut angelegten organischen Erdmischungen.

**Autoflower-Besonderheit:** Maximal 70–80% der empfohlenen Duengermenge fuer Photoperiod-Sorten. Autoflower reagieren empfindlicher auf Ueberduengung (Naehrstoffverbrennungen, "Nutrient Burn").

**Calcium-Magnesium-Verhaeltnis:** Idealverhaeltnis Ca:Mg = 3:1. CalMag immer zugeben bei RO-Wasser (EC < 0.2 mS). Symptom Ca-Mangel: braune Ränder, Blattverbiegung. Symptom Mg-Mangel: intervenöse Chlorose (Blattmitte gruen, Adern gelb).

---

## 4. Trainingstechniken (Training)

**Wichtig fuer das Kamerplanter-Phasenmodell:** Trainingstechniken sind phasengebunden (HST Validator). Aggressive Techniken nur in der Vegetationsphase anwenden.

### 4.1 Low Stress Training (LST) — Vegetativ

Aeste horizontal binden und dabei den Kronenaufbau abflachen (flacher Canopy). Keine Wunden. Ausfuehren ab Woche 2–3 der Vegetationsphase.

- **Ziel:** Mehr Lichttreffer auf tiefere Internodien, mehr gleichgroesse Bluetenpunkte
- **Geeignet fuer:** Alle Typen inkl. Autoflower
- **KA-Phasenbeschraenkung:** Nur in `vegetative`; fortfuehren bis Bluetewoche 2

### 4.2 Topping — Vegetativ (Photoperiod only)

Haupttrieb abschneiden, zwei Co-Tops entstehen. 2–4x wiederholbar.

- **Ziel:** Buschige Pflanze mit gleichmaessig hohen Bluetenpunkten
- **Geeignet fuer:** Nur Photoperiod; kein Topping bei Autoflower (zu wenig Erholungszeit)
- **KA-Phasenbeschraenkung:** Nur in `vegetative`; VERBOTEN in `pre_flowering` und spaeter

### 4.3 FIM-Methode (F*ck I Missed) — Vegetativ

Aehnlich wie Topping, aber nur 80% des Haupttriebs werden entfernt. Erzeugt 3–4 neue Triebe.

### 4.4 SCROG (Screen of Green) — Vegetativ & Blüte-Woche 1–2

Ein horizontales Netz (Maschenweite 5x5 cm) wird 20–30 cm ueber die Pflanzen gespannt. Aeste werden durch das Netz gezogen. Gleichmaessige Lichtverteilung.

- **Ziel:** Maximaler Ertrag pro Quadratmeter
- **KA-Phasenbeschraenkung:** Aufbau in `vegetative`, finale Einflechtung in `pre_flowering`

### 4.5 Defoliation — Blütewoche 3 & 6

Gezieltes Entfernen grosser Schirmblätter (Fan Leaves) die Bluetenpunkte verdecken.

- **Woche 3 Bluete:** Moderate Defoliation der unteren 30% der Pflanze
- **Woche 6 Bluete:** Erneute Defoliation der Schattenblatter
- **Nie mehr als 30% der Blattmasse auf einmal entfernen!**

---

## 5. Ernte, Trocknung & Curing

### 5.1 Ernte-Indikatoren

**Trichom-Analyse (bevorzugte Methode, Juwelierslupe 30–60x oder USB-Mikroskop):**

| Trichom-Status | Bedeutung | Erntezeitpunkt |
|---------------|-----------|----------------|
| Klar (clear) | Unreif; THC noch nicht vollstaendig aufgebaut | Noch warten |
| Trueb/milchig (cloudy/milky) | Maximaler THC-Gehalt; energetische, klare Wirkung | Erntebeginn moeglich |
| Bernsteinfarben (amber) | THC degradiert zu CBN; beruhigende, koerperliche Wirkung | Spaeter Erntepunkt |
| **Optimal** | **70–90% trueb + 10–20% bernstein; keine klaren** | **Richtwert fuer Hybridtypen. Sativa-dominant: bis 30% bernstein akzeptabel. Indica-dominant: bereits bei 10–15% bernstein erntbar fuer leichtere Wirkung.** |

**Optische Sekundaer-Indikatoren:**
- Pistillen (Haare): >80% haben von weiss zu braun/orange gewechselt
- Kelchblaetter ("Calyxes") sind gut aufgebluehen und dicht
- Obere Blaetter beginnen zu vergilben (natuerliches N-Flush)
- Aroma ist vollstaendig und intensiv entwickelt

### 5.2 Trocknungsprotokoll

**Ziel: Langsame Trocknung fuer maximalen Terpenerhalt**

| Parameter | Empfehlung | Hinweis |
|-----------|-----------|---------|
| Temperatur | 15–18°C | Hohere Temperaturen beschleunigen, vernichten aber Terpene |
| Luftfeuchtigkeit | 50–60% relative Feuchte | Zu trocken = Knistern; zu feucht = Schimmel |
| Luftstrom | Leichte Zirkulation (kein Direktwind auf Buds) | Direktwind trocknet ungleichmaessig |
| Dauer | 7–14 Tage (abhaengig von Bud-Dichte und Luftfeuchte) | Bereit wenn Stiele beim Biegen knacken (nicht knicken) |
| Licht | Dunkelheit | Licht degradiert THC (UV-Strahlung) |
| Aufhaengen | Aeste kopfueber aufhaengen | Maximale Luft-Zirkulation |

**Schnelltrocknung (Notfall):** Buds einzeln in Brown-Paper-Bag, taeglich wenden, 3–5 Tage. Qualitaetsverlust durch Chlorophyll-Einschluss (gruener, rauher Geschmack).

### 5.3 Curing-Protokoll (Reifung)

**Curing = kontrollierte Fermentation im hermetisch verschlossenen Behälter**

| Phase | Dauer | Aktion | Ziel |
|-------|-------|--------|------|
| Einlagern | Tag 1 | Buds in Weckglaeser (Boveda 62% RH Packs) | Feuchtigkeitsausgleich |
| Burping-Phase | Woche 1–2 | Taeglich 5–10 min Glas oeffnen | CO2 austreiben; Chlorophyll abbauuen |
| Reifungsphase | Woche 2–4 | Glas wöchentlich kurz oeffnen | Terpene entwickeln sich weiter |
| Lagerung | >4 Wochen | Kuehl, dunkel, <20°C | Qualitaet haelt sich 12–24 Monate |

**Ziel-Feuchte im Glas:** 58–62% (Boveda 62% Packs als Referenz/Puffer).

### 5.4 Ertragsschaetzung

| Anbausystem | Ertragsbereich | Einheit |
|-------------|---------------|---------|
| Indoor, Erde, 400W HPS | 250–400 | g/m² |
| Indoor, Coco, 600W HPS | 400–600 | g/m² |
| Indoor, LED 600W, SCROG | 500–800 | g/m² |
| Outdoor, Mitteleuropa | 50–200 | g/Pflanze |
| Outdoor, Greenhouse | 200–600 | g/Pflanze |
| Autoflower Indoor | 30–100 | g/Pflanze |

---

## 6. Schädlinge & Krankheiten

### 6.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste auf Unterseite; gelbe Punkte auf Blatt | leaf (underside) | vegetative, flowering | medium |
| Hanf-Rostmilbe (Hemp Russet Mite) | Aculops cannibicola | Blaetter rollen sich ein; braune Raender; kein Gespinst; Haare auf Blaettern/Stielen; Blattdeformation | leaf, stem | vegetative, early_flower | difficult |
| Thrips | Frankliniella occidentalis | Silberne Raspelspuren; schwarze Kotkruempel | leaf | vegetative | medium |
| Blattlaus (Gruene Pfirsichlaus) | Myzus persicae | Honigau, Rußtau; Kolonien an Triebspitzen | leaf, shoot | seedling, vegetative | easy |
| Trauermücke (Larven) | Sciaridae (Bradysia spp.) | Larven fressen Wurzeln; Wachstumshemmung; Adulte um Substrat | root | all | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Honigau; kleine weisse Fliegen | leaf | vegetative, flowering | easy |

### 6.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel / Bud Rot | Botrytis cinerea | Graues Myzel in Bud-Zentren; braune Faeulnis | >60% rLF; schlechte Luftzirkulation; Verletzungen | 3–7 | flowering, late_flowering |
| Echter Mehltau | Golovinomyces spadiceus (syn. G. ambrosiae auf Cannabis) | Weisser, pudriger Belag auf Blattoberfläche | Trockene Luft Tage + schwuele Naechte | 5–10 | vegetative, pre_flowering |
| Wurzelfaeule | Pythium spp. | Braune, schleimige Wurzeln; Welke trotz feuchtem Substrat | Ueberwaesserung; stehendes Wasser; Sauerstoffmangel | 3–10 | all |
| Fusarium-Welke | Fusarium oxysporum | Stiel braun innen; Welke von einem Ast aus | Schlechte Drainage; Naehrstoffimbalancen | 7–14 | vegetative, flowering |
| Hop Latent Viroid (HLVd) | Viroid | Kleines Wachstum; geringe Trichodichte; "Dudding" | Kontaminierte Werkzeuge; infizierte Klone | latent (Wochen) | alle |

### 6.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10–20 | 7–14 |
| Neoseiulus californicus | Spinnmilbe, Russet Mite | 10–25 | 14–21 |
| Amblyseius swirskii | Thrips (Larven), Weiße Fliege | 25–50 | 14 |
| Orius laevigatus | Thrips | 2–5 | 14–21 |
| Dalotia coriaria (Rove Beetle) | Trauermücken-Larven | 5–10 | 14 |
| Steinernema feltiae | Trauermücken-Larven (Nematoden) | 500.000/m² | sofort |
| Encarsia formosa | Weiße Fliege | 3–5 | 21 |
| Aphidoletes aphidimyza | Blattlaeuse | 2–5 | 7–14 |

### 6.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen (0.5–1% + Emulgator), Blaetter oben/unten; nur in veg. | 7 | Milben, Blattlaeuse, Thrips |
| Pyrethrum / Spinosad | biological | Pyrethrine/Spinosyn A+D | Sprühen abends; max. 2x/Woche | 3 | Thrips, Blattlaeuse |
| Kaliumsulfat-Seife (Insektenseife) | biological | Kaliumseife | Sprühen; direkt auf Insekten | 1 | Blattlaeuse, Weiße Fliege |
| Schwefelkalzium (LiMO) | biological | Calciumpolysulfid | Sprühen; foerdert Immunsystem; bis Woche 3 Bluete | 14 | Echter Mehltau, Milben |
| Bacillus amyloliquefaciens | biological | Bacterium | Substrat-Drench + Blattspray | 0 | Echter Mehltau, Botrytis (vorbeugen) |
| Trichoderma harzianum | biological | Fungus | Substrat-Einarbeitung; Bewurzelung | 0 | Wurzelfaeule (Pythium, Fusarium) |
| Luft-Management | cultural | — | RLF < 50% in Bluete; Lueftung erhoehen | 0 | Botrytis, Echter Mehltau |
| Diatomeenerde | physical | Kieselgur | Substrat-Oberfläche bestäuben | 0 | Trauermücken, Kriechinsekten |

### 6.5 Resistenzen

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Botrytis-Resistenz bei Sorten mit kompaktem Bud-Aufbau | varietal | `resistant_to` |
| Echter-Mehltau-Resistenz (einige Sativa-Landrace Sorten) | varietal | `resistant_to` |

---

## 7. Fruchtfolge & Mischkultur

### 7.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Cannabaceae (eigene Familie; keine enge Verwandtschaft zu Gemuese) |
| Empfohlene Vorfrucht | Gruenduengung (Leguminosen: Klee, Lupippe) oder Schwachzehrer |
| Empfohlene Nachfrucht | Kreuzblütler oder Gruenduengung |
| Anbaupause (Jahre) | 2–3 Jahre (Pythium, Fusarium-Ruhezeiten) |

### 7.2 Mischkultur — Gute Nachbarn (Outdoor)

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr im Boden; Thrips-Ablenkung; Bestäuber | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Schlaedlings-Repellenz durch aetherische Oele; verbessert Aroma (anekdotisch) | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bestäuber anlocken; Milben-Abwehr durch Duft | `compatible_with` |
| Kamille | Matricaria chamomilla | 0.7 | Bodengesundheit; Nützlingsfoerderung; Antifungal | `compatible_with` |
| Bohne (Stangenbohne) | Phaseolus vulgaris | 0.6 | N-Fixierung im Boden; Bodenleben-Foerderung | `compatible_with` |

### 7.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmstoffe verlangsamen Wachstum | moderate | `incompatible_with` |
| Nachtschatten-Gemuese (Tomate, Paprika) | Solanaceae | Geteilte Schaedlinge (Thrips, Weiße Fliege, Spinnmilbe); Phytophthora-Risiko | moderate | `incompatible_with` |

### 7.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Urticaceae (Nessel) | `shares_pest_risk` | Spinnmilbe, Trauermücken | `shares_pest_risk` |

---

## 8. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Cannabis sativa |
|-----|-------------------|-------------|------------------------------|
| Cannabis indica | Cannabis indica | Nah verwandt; oft als Sortentyp betrachtet | Kompaktere Wuchsform; kuerzer Bluetezeit; Indica-typische Wirkung |
| Cannabis ruderalis | Cannabis ruderalis | Autoflower-Basis | Automatisches Blueten; extrem schnell; winterhaerter |
| Hanf (Faserhanf) | Cannabis sativa (Industriehanf) | Selbe Art; anderer Zuchtzweck | Hohe THC-freie Sorten (CBD); legal angebaut; Faserproduktion |

---

## 9. Bekannte Sorten (Cultivar-Beispiele)

### Photoperiod — Sativa-dominiert

| Sorte | Typ | Bluetezeit (Tage) | THC-Gehalt | Besonderheit |
|-------|-----|-------------------|-----------|-------------|
| Amnesia Haze | Sativa 70% | 70–80 | 20–24% | Zitrusaroma; hohe Ertraege; SCROG-geeignet |
| Jack Herer | Sativa 55% | 56–70 | 18–22% | Spicy-Harz; Named nach Cannabis-Aktivist; Classics |
| Durban Poison | Sativa 100% | 56–63 | 20% | Landrace; Suedafrika; Anisaroma |

### Photoperiod — Indica-dominiert

| Sorte | Typ | Bluetezeit (Tage) | THC-Gehalt | Besonderheit |
|-------|-----|-------------------|-----------|-------------|
| Northern Lights | Indica 90% | 56–63 | 18–20% | Robuste Klassikerin; Anfaenger-freundlich; kompakt |
| White Widow | Hybrid 60%I | 56–63 | 20–25% | Dichte Trichome; harzige Blueten; sehr populaer |
| OG Kush | Hybrid 75%I | 56–63 | 19–26% | Erdiges Pineterpenprofil; haeufige Zuchtbasis |

### Autoflower

| Sorte | Typ | Gesamtlaufzeit (Tage) | THC-Gehalt | Besonderheit |
|-------|-----|----------------------|-----------|-------------|
| Critical Auto | Indica Auto | 65–70 | 14–18% | Sehr hoch ertragreich; Anfaengertauglich |
| Girl Scout Cookies Auto | Hybrid Auto | 70–80 | 20–22% | Suss-erdiges Aroma; kompakt; auch Balkon |
| Bruce Banner Auto | Sativa Auto | 75–85 | 24–27% | Sehr hoch THC; fuer erfahrene Zuechter |

### CBD-Sorten (THC < 0.3%)

| Sorte | Typ | CBD-Gehalt | THC | Besonderheit |
|-------|-----|-----------|-----|-------------|
| CBD Charlotte's Angel | Sativa/CBD | 15–20% | <0.3% | Legaler Anbau; medizinisch; Vollspektrum |
| Finola (Faserhanf) | Industriehanf | 0.5–1% CBD | <0.3% | Samenstress; schnell; Lebensmittel |
| Santhica 70 | Faserhanf | <0.5% CBD | <0.1% | EU-zertifizierte Sorte; Faserproduktion |

---

## 10. CSV-Import-Daten (KA REQ-012 kompatibel)

### 10.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Cannabis sativa,Cannabis;Hanf;Marihuana,Cannabaceae,Cannabis,annual,short_day,herb,taproot,8a;8b;9a;9b;10a;10b;11a;11b,-0.3,Zentralasien,yes,11–25,30,60–300,50–120,80–120,yes,limited,true,true,heavy_feeder
```

### 10.2 Cultivar CSV-Zeilen

```csv
name,parent_species,cycle_type,photoperiod_type,days_to_maturity,traits,seed_type,notes
Northern Lights,Cannabis sativa,annual,short_day,56–63,compact;indica_dominant;beginner_friendly,feminized,Classic indoor indica; 18-20% THC
Amnesia Haze,Cannabis sativa,annual,short_day,70–80,sativa_dominant;high_yield;terpene_rich,feminized,20-24% THC; SCROG suitable
Critical Auto,Cannabis sativa,annual,day_neutral,65–70,autoflower;indica_dominant;high_yield,autoflowering feminized,14-18% THC; beginner friendly autoflower
White Widow,Cannabis sativa,annual,short_day,56–63,hybrid;heavy_trichomes;high_yield,feminized,20-25% THC; very popular classic
CBD Charlotte's Angel,Cannabis sativa,annual,short_day,60–70,cbd_dominant;medicinal;legal,feminized,15-20% CBD; THC <0.3%
```

---

## Quellenverzeichnis

1. Athena Ag — Cannabis Veg and Flowering Stage Blog — https://www.athenaag.com/blog/cannabis-veg-stage / https://www.athenaag.com/blog/cannabis-flowering-stage
2. Royal Queen Seeds — PPFD PAR Lumens Cannabis Guide — https://www.royalqueenseeds.com/blog-ppfd-par-lumens-and-foot-candle-for-growing-cannabis-n1460
3. GrowerIQ — Trichome Harvest Chart Cannabis — https://groweriq.ca/2023/08/26/ultimate-guide-to-cannabis-trichome-development-trichome-harvest-chart/
4. PubMed (PMC) — NPK Optimierung Cannabis Flowering, PMC8635921 — https://pmc.ncbi.nlm.nih.gov/articles/PMC8635921/
5. Koppert US — Cannabis Biologicals IPM — https://www.koppertus.com/crops/ornamentals/cannabis/
6. BIRC — IPM for Cannabis Pests, Vol. XXXVI Nr. 5/6 — https://www.birc.org/IPMPCannabis.pdf
7. Zamnesia — NPK Ratios Cannabis — https://www.zamnesia.com/grow-weed/308-npk-ratios
8. WeedSeeds.com — Training Guide LST SCROG Topping — https://www.weedseeds.com/learn/growing/training/
9. MarijuanaSeedsForSale — Harvest Timing Trichomes Curing — https://marijuanaseedsforsale.com/growing-cultivation/harvesting-cannabis/
10. 2Fast4Buds — Autoflower Feeding Schedule — https://2fast4buds.com/news/best-feeding-schedule-for-autoflowering-plants
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
11. Tang et al. 2017, GCB Bioenergy (Wiley) — Hemp (Cannabis sativa L.) leaf photosynthesis in relation to nitrogen content and temperature — C3-Photosynthese-Modell, T_opt-Plateau 25–35 °C — https://onlinelibrary.wiley.com/doi/full/10.1111/gcbb.12451
12. ResearchGate / Annals of Applied Biology (van der Werf 1995 u.a.) — Development of a hemp simulation model & effect of temperature on leaf appearance — GDD-Basistemperatur ~1 °C (Feld) — https://www.researchgate.net/publication/248891523_Development_of_a_hemp_Cannabis_sativa_L_simulation_model_1General_introduction_and_the_effect_of_temperature_on_the_pre-emergent_development_of_hemp
13. Frontiers in Plant Science (PMC8367441) — Photoperiodic Flowering Response of Hemp Cultivars — kritische Tageslaenge ~13:45–15 h, sortenabhaengig — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8367441/
14. PMC (PMC3550580) — Temperature response of photosynthesis in drug and fiber varieties of Cannabis sativa L. — Photosynthese-T_opt 30–35 °C (Drug), ~30 °C (Faser) — https://pmc.ncbi.nlm.nih.gov/articles/PMC3550580/
15. Amaducci et al. — Characterisation of hemp (Cannabis sativa L.) roots under different growing conditions — Wurzeltiefe, 50% Biomasse in oberen 20–50 cm — https://www.votehemp.com/wp-content/uploads/2018/09/Characterisation_of_hemp_Cannabis_sativa_roots_under_different_growing_conditions.pdf
16. ScienceDirect — Effect of saline irrigation on fiber hemp growth (PMC10978745) — Biomassereduktion ab ECe 4 dS/m — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10978745/
17. USDA-ARS — Plant Salt Tolerance (Maas & Grattan), Salt tolerance of crops — Klassifikationsrahmen ECe/Slope — https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf
18. Royal Queen Seeds (USA) — The Perfect pH Value for a Cannabis Plant — Boden-pH 6.0–7.0, Hydro 5.5–6.1 — https://www.royalqueenseeds.com/us/blog-the-perfect-ph-value-for-a-cannabis-plant-n87
19. FloraFlex / Dutch Passion — Sunlight requirements for outdoor cannabis — full_sun, min. 6–8 h direkte Sonne — https://floraflex.com/default/blog/post/understanding-sunlight-requirements-for-outdoor-cannabis-plants
20. Cannabis Business Times (NCSU-Daten, Whipker et al.) — When Micronutrients Become Macro Problems — Mn/Zn/Cu/Mo ppm-Bereiche Bluete — https://www.cannabisbusinesstimes.com/columns/cultivation-matters/article/15693675/when-micronutrients-become-macro-problems
21. Penn State Extension — Hydroponics Systems: Nutrient Solution Programs and Recipes — allgemeine Mikronaehrstoff-Sufficiency-Bereiche — https://extension.psu.edu/hydroponics-systems-nutrient-solution-programs-and-recipes
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
