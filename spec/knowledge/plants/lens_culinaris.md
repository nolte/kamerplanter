# Linse — Lens culinaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Royal Horticultural Society, Bayerische LfL Körnerleguminosen, University of Saskatchewan Lentil, FAO Lentil Crop Profile

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lens culinaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Linse, Speiselinse; Lentil, Common Lentil | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Lens | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4.5–5 | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN: quantitativer (nicht qualitativer) Langtag-Responder ohne scharfen Stunden-Schwellenwert; kritische Tageslänge ist genotyp-/temperaturabhängig und sinkt mit steigender Temperatur --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kälteverlträglich bis ca. -5°C im Keimlingsstadium; frühzeitige Aussaat möglich (März); Spätfröste nach Bestockung können Ertragseinbußen verursachen | `species.hardiness_detail` |
| Heimat | Vorderer Orient (Fruchtbarer Halbmond); domestiziert ca. 8.000–9.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Bestäuber erforderlich (requires pollinator) | false | `species.requires_pollinator` |
| Kreuzbefruchtungsgruppe (pollinator group) | — | `species.pollinator_group` |
| Empfohlene Befruchter-Sorten (compatible pollinators) | — | `species.compatible_pollinators` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**N-Fixierung:** Lens culinaris fixiert in Symbiose mit *Rhizobium leguminosarum* bv. viciae 50–100 kg N/ha. Impfung mit geeignetem Rhizobium-Impfstoff bei Erstanbau empfohlen. Die Pflanze produziert trotzdem essbare Körner — doppelter Nutzen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Photoperiode-Hinweis:** Linse ist ein *quantitativer* Langtag-Responder — lange Tage und Wärme beschleunigen die Blüte, sind aber nicht obligat. Es gibt keinen scharfen kritischen Stunden-Schwellenwert; die Reaktion folgt einem linearen Modell `1/f = a + bT + cP` (T = Temperatur, P = Photoperiode). `photoperiod_type=long_day` bleibt die korrekte Einstufung; ein obligates Kältebedürfnis (Vernalisation) besteht NICHT.

**GDD-Basistemperatur:** Die Wuchs-/Phänologie-Basis liegt bei ca. 4,5–5 °C (kühlsaisonale Leguminose). Kardinaltemperatur für Keimung/Emergenz: Basis 4,5 °C, Optimum ~22,9 °C, Maximum 40 °C. Nicht mit höheren Keim-Optima verwechseln.

**Bestäubung:** Linse ist strikt selbstbestäubend (cleistogam — Bestäubung erfolgt vor dem Öffnen der Blüte; < 1 % Fremdbefruchtung) und selbstfertil. Daher `requires_pollinator=false`; keine Kreuzbefruchtungsgruppe und keine Befruchter-Sorten erforderlich (Felder bleiben leer). Eine Bestäubung durch Insekten ist nicht nötig.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Historische Bedeutung:** Linse ist eine der ältesten Kulturpflanzen der Menschheit und stand an der Wiege der Landwirtschaft im Nahen Osten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat bevorzugt; Pfahlwurzel schlecht umpflanzbar) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (Frühsaat ab Mitte März möglich; kältetolerante Art) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 | `species.direct_sow_months` |
| Erntemonate | 7, 8 (Trockenernte); 6, 7 (Grünernte / grüne Linsen) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

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
| Giftige Pflanzenteile | Rohe Linsen (Lektine, Trypsinhemmer; werden beim Kochen inaktiviert) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Phytinsäure (mindert Mineralstoffaufnahme; durch Einweichen reduzierbar) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (nach Kochen völlig unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (kleine Pflanze; aber Pfahlwurzel) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5 cm in der Reihe; 30–40 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | limited (niedrige Sorten stehen; höhere können lagern) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, durchlässige Erde; pH 6,0–8,0; kalkverträglich; kein Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein belastbarer artspezifischer Lens-culinaris-Messwert aus ≥2 unabhängigen Quellen --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein belastbarer artspezifischer Lens-culinaris-Messwert aus ≥2 unabhängigen Quellen --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 40–60 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | 1.5–2 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: keine konsolidierte Maas-Hoffman-Slope (b) für Lens culinaris belegt; Linse fehlt in den FAO-Salztoleranztabellen --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–8.0 | `species.soil_ph_preference` |

**Hinweise zur Standortqualität:**
- **Licht:** Linse ist eine ausgesprochene Volllicht-Kultur (full sun, ≥ 6–8 h direkte Sonne); nicht schattenverträglich (stark/leggy/blühschwach im Schatten). Sättigungs-, Photoinhibitions- und Optimum-PPFD-Werte gehören NICHT ins LCP-Feld.
- **Wurzeltiefe:** Relativ flaches Pfahlwurzelsystem (~0,6 m); ~59 % des Wurzelvolumens in 0–20 cm, ~21 % in 20–40 cm, ~16 % in 40–60 cm. Daher die Spanne 40–60 cm als effektive Wurzelzone.
- **Staunässe:** Sehr empfindlich — Staunässe führt rasch zu Wurzelfäulen; daher durchlässige, gut drainierte Böden zwingend.
- **Salz:** Salzempfindlich (sensitive) — nur auf nicht-salinen Böden anbaubar. Bei ECe ≈ 2 dS/m (Substrat-ECe, nicht Gießwasser-EC) bereits ~20 % Ertragsminderung, bei 3 dS/m 90–100 %. Konsistent mit Klasse `sensitive` (Schwelle < 2 dS/m).
- **pH:** Vorzug pH 6,0–8,0 (kalkverträglich, leicht alkalisch ideal), harmonisiert mit §1.6 und den Nährstoffprofilen §2.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–12 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 21–42 | 3 | false | false | high |
| Blüte | 21–35 | 4 | false | false | low |
| Hülsenansatz | 14–21 | 5 | false | true | medium |
| Reife | 21–35 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–4 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtagpflanze) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–10 (trockenheitstolerante Pflanze) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 (trocken für Ernte) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.2–2.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–21 (Wasserreduktion) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | Zn (ppm) | Cu (ppm) | Mo (ppm) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–8.0 | — | — | — | — | — | — |
| Sämling | 0:1:1 | 0.4–0.8 | 6.0–8.0 | 60 | 20 | 0.5 | 0.05 | 0.05 | 0.05 |
| Vegetativ | 0:1:2 | 0.6–1.2 | 6.0–8.0 | 80 | 30 | 0.5 | 0.1 | 0.05 | 0.05 |
| Blüte | 0:2:2 | 0.8–1.4 | 6.0–8.0 | 80 | 40 | 0.5 | 0.1 | 0.05 | 0.05 |
| Reife | 0:1:1 | 0.4–0.8 | 6.0–8.0 | 60 | 20 | 0.5 | 0.05 | 0.05 | 0.05 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoff-Hinweis:** Mn/Zn/Cu/Mo sind Fertigations-Zielkonzentrationen (Lösung), keine Gewebe-/Korngehalte. Werte folgen etablierten Hydroponik-Standardbereichen (Mn 0,5; Zn 0,05–0,1; Cu 0,05; Mo 0,05 ppm). **Molybdän (Mo)** ist für die N-Fixierung der *Rhizobium*-Knöllchen essentiell (Nitrogenase-Cofaktor) und daher bei Linse besonders zu beachten (vgl. §3.2).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Biologisch

| Produkt | Marke | Typ | Ausbringrate | Phasen |
|---------|-------|-----|-------------|--------|
| Rhizobium leguminosarum (Impfmittel) | diverse | Saatgutimpfung | 250 ml/25 kg Saatgut | Vor Saat |
| Kompost | eigen | organisch | 3–4 L/m² | Herbst/Frühjahr |

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Superphosphat | diverse | mineralisch | 0-46-0 | 15–20 g/m² | Grunddüngung |
| Kaliumsulfat | diverse | mineralisch | 0-0-50 | 10–15 g/m² | Grunddüngung |

### 3.2 Besondere Hinweise zur Düngung

KEINE Stickstoffdüngung bei funktionierender Rhizobium-Symbiose. Kalziumversorgung wichtig (pH-neutraler bis leicht alkalischer Boden ideal). Phosphormangel hemmt Knöllchenbildung. Spurenelement Molybdän (Mo) für N-Fixierung essentiell.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 (trockenheitstolerant) | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 28 (P + K nur) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Planung | Rhizobium-Impfmittel bestellen; Saat vorbereiten | mittel |
| Mär–Apr | Aussaat | Frühsaat ab März; 3–4 cm tief; 5 cm Abstand | hoch |
| Apr–Mai | Kontrolle | Knöllchenbildung prüfen; Unkraut hacken | mittel |
| Jun | Grünernte (optional) | Grüne Hülsen mit Körnern für Frischgenuss | niedrig |
| Jul–Aug | Trockenernte | Hülsen braun; Pflanzen absterben; Drusch | hoch |
| Aug | Bodenbearbeitung | Wurzeln einarbeiten; N-Depot | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Blattläuse | Aphis fabae, Acyrthosiphon pisum | Kolonien; Virustransmission | Blatt, Trieb | Alle |
| Linsenrüssler | Sitona crinitus | Fraß an Blatträndern; Larven in Wurzelknöllchen | Blatt, Knöllchen | Sämling |
| Erbsenwickler | Cydia nigricana | Larven in Hülsen / Körnern | Hülse | Blüte, Reife |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Brennfleckenkrankheit | fungal (Colletotrichum truncatum) | Dunkelbraune Flecken; Stängelläsionen | feucht-warm |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Pilzrasen | hohe Luftfeuchte; kühl |
| Sklerotinia-Fäule | fungal (Sclerotinia sclerotiorum) | Weiße Myzel-Läsionen | feuchte Bedingungen |
| Aszochyta-Blattflecken | fungal (Ascochyta lentis) | Gelblich-braune Blattflecken | feucht |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Linsenrüssler |
| Pyrethrin | biological | Pyrethrine | Sprühen | 3 | Blattläuse |
| Trichoderma-Beizmittel | biological | Trichoderma harzianum | Saatgutbeize | 0 | Saatgutfäulen |
| Weite Fruchtfolge | cultural | — | 3–4 Jahre Pause | 0 | Sklerotinia, Aszochyta |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Blattlaus-Schlupfwespe | Aphidius ervi | Erbsenblattlaus (Acyrthosiphon pisum) — große Blattlausart | ~0,25–0,5 Tiere/m²; mind. 2 Freilassungen im Abstand von 1 Woche | 2–3 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (u. a. Aphis fabae, A. pisum) | ~1–2 Larven/m²; 1–3 Wiederholungen im 1–2-Wochen-Takt | 2–3 Wochen |

**Hinweis:** *Aphidius ervi* parasitiert gezielt größere Blattläuse wie die Erbsenblattlaus; *Aphidoletes aphidimyza* deckt ein breites Blattlaus-Spektrum ab und ergänzt die Schlupfwespe bei hohem Befallsdruck. Früher Einsatz (vor Populationsexplosion) zu Saisonbeginn entscheidend. Beide gegen die in §5.1 gelisteten Blattläuse.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide (Weizen, Gerste); Wintergetreide |
| Empfohlene Nachfrucht | Winterweizen, Mais, Raps (profitieren vom N-Depot) |
| Anbaupause (Jahre) | 4–5 Jahre auf gleichem Standort (Sklerotinia-Dauerformen) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Gerste | Hordeum vulgare | 0.8 | Klassisches Gerste-Linsen-Gemenge; Gerste stützt Linse | `compatible_with` |
| Leindotter | Camelina sativa | 0.7 | Stützfunktion; Ölpflanze | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Insektenanlockung; Begleitpflanze | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Knoblauch | Allium sativum | Hemmt Rhizobium-Knöllchenbildung | moderate | `incompatible_with` |
| Zwiebel | Allium cepa | Gleiche antibiotische Wirkung | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Gleiche Familie; gleiche Pathogene (Ascochyta); Konkurrenz | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Linse |
|-----|-------------------|-------------|------------------------|
| Erbse | Pisum sativum | Fabaceae; ähnliche Kultur | Höherer Ertrag; mehr Sorten |
| Kichererbse | Cicer arietinum | Fabaceae; Naher Osten | Hitze- und Trockentoleranter |
| Ackerbohne | Vicia faba | Fabaceae; kältetoleranter | Größere Bohne; höherer Ertrag |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Lens culinaris,"Linse;Speiselinse;Lentil;Common Lentil",Fabaceae,Lens,annual,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Vorderer Orient",limited,no,limited,false,limited,nitrogen_fixer,true,half_hardy,"3;4;5","7;8","5;6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Aldina,Lens culinaris,"green_lentil;medium_early;mitteleuropa_adapted",90,open_pollinated
Precosa,Lens culinaris,"red_lentil;peeled;high_yield",100,certified
Anicia,Lens culinaris,"beluga_type;black;gourmet",110,open_pollinated
```

---

## Quellenverzeichnis

1. [USDA PLANTS — Lens culinaris](https://plants.usda.gov/plant-profile/LECU7) — Taxonomie
2. [University of Saskatchewan — Lentil Production](https://www.usask.ca) — Anbaupraxis
3. [Bayerische LfL — Körnerleguminosen](https://www.lfl.bayern.de/ipz/leguminosen) — Mitteleuropa
4. [FAO Lentil Crop Profile](https://www.fao.org) — Globale Anbausysteme, Nährstoffe
5. [Royal Horticultural Society — Lentils](https://www.rhs.org.uk) — Gartenbau-Empfehlungen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Summerfield et al. — Effects of Temperature and Photoperiod on Flowering in Lentils, Annals of Botany 56(5):659](https://academic.oup.com/aob/article/56/5/659/191276) — Photoperiode (quantitativer Langtag-Responder), Temperatur-Photoperiode-Blühmodell
7. [Characterization of responses to temperature and photoperiod for time to flowering in a world lentil collection, Theor. Appl. Genet.](https://link.springer.com/article/10.1007/BF00224386) — quantitative Photoperiodik, kritische Tageslänge temperaturabhängig
8. [Cardinal temperatures and thermal time required for emergence of lentil, Legume Research LR-266](https://arccjournals.com/journal/legume-research-an-international-journal/LR-266) — GDD-Kardinaltemperaturen (Basis 4,5 °C, Optimum 22,9 °C, Maximum 40 °C)
9. [Photothermal Quotient — Thermal Index for Lentil Phenology, Legume Research LR-4949](https://arccjournals.com/journal/legume-research-an-international-journal/LR-4949) — Phänologie-GDD mit Basistemperatur 5 °C
10. [Frontiers in Plant Science — Root Traits, Nodulation and Root Distribution in Lens culinaris](https://www.frontiersin.org/articles/10.3389/fpls.2017.01632/full) — Wurzelverteilung 0–60 cm, effektive Wurzeltiefe
11. [Government of Saskatchewan — Red Lentils / Pulse Crops](https://www.saskatchewan.ca/business/agriculture-natural-resources-and-industry/agribusiness-farmers-and-ranchers/crops-and-irrigation/field-crops/pulse-crop-bean-chickpea-faba-bean-lentils/red-lentils) — flaches Wurzelsystem ~0,6 m, Standortqualität
12. [Salt stress in pulses: global research review (IJGPB)](https://www.isgpb.org/journal/index.php/IJGPB/article/download/431/32) — Salzempfindlichkeit, ECe-Schwelle ~2 dS/m, Maas-Hoffman-Einordnung
13. [Feedipedia — Lentil (Lens culinaris)](https://www.feedipedia.org/node/284) — Staunässe-/Salzempfindlichkeit, pH-Spektrum, Wuchsform
14. [Wikifarmer — Lentil Soil Requirements / Growing Lentils](https://wikifarmer.com/library/en/article/lentil-soil-requirements-soil-preparation-and-planting) — Boden-pH 6,0–8,0, Volllichtbedarf, Staunässe-Empfindlichkeit
15. [Canadian Food Inspection Agency — The Biology of Lens culinaris (Lentil)](https://inspection.canada.ca/en/plant-varieties/plants-novel-traits/applicants/directive-94-08/biology-documents/lens-culinaris-medikus-lentil) — strikte Selbstbestäubung (Cleistogamie), < 1 % Fremdbefruchtung
16. [Plants For A Future — Lens culinaris](https://pfaf.org/user/plant.aspx?LatinName=Lens+culinaris) — selbstfertil, cleistogame Bestäubung
17. [Evergreen Growers Supply — Aphidius ervi (Parasitoid für große Blattläuse)](https://www.evergreengrowers.com/aphidius-ervi.html) — Nützling gegen Erbsenblattlaus
18. [Sound Horticulture — Aphidoletes aphidimyza](https://soundhorticulture.com/products/aphidoletes-aphidimyza) — Gallmücke gegen Blattläuse, Ausbringraten
19. [PMC — Pea Aphid Population Dynamics and Yield Loss on Lentil](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8707183/) — Acyrthosiphon pisum Hauptschädling der Linse
20. [PSU / Greenhouse Grower — Hydroponic micronutrient solution ranges](https://extension.psu.edu/hydroponics-systems-and-principles-of-plant-nutrition-essential-nutrients-function-deficiency-and-excess) — Fertigations-Standardbereiche Mn/Zn/Cu/Mo
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
