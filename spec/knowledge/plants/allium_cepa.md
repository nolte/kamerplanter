# Küchenzwiebel — Allium cepa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Floragard Allium cepa, Bio-Gärtner.de Zwiebeln, Utopia.de, Samen.de Mischkultur

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Allium cepa | `species.scientific_name` |
| Volksnamen (DE/EN) | Küchenzwiebel, Speisezwiebel; Onion | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` → `botanical_families.name` |
| Gattung | Allium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
| Lebenszyklus | biennial (als Gemüse einjährig kultiviert) | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | monocarpic (blüht einmal, dann Absterben) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Steckzwiebeln überwintern im Boden bis −10 °C; Winterzwiebeln (Allium fistulosum-Hybriden) härter | `species.hardiness_detail` |
| Heimat | Zentralasien (Iran, Afghanistan) | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 5 (Zwiebelwachstum/Bulbing; konsistent mit kühl-Klasse) | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | true (echte Knollendormanz: Rest → Endodormanz → Ökodormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true (Blühinduktion im 2. Jahr durch Kälte; im Gemüseanbau einjährig kultiviert, Schossen unerwünscht) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | 60–120 (≈ 4 °C, 2–4 Monate) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | 13.75–14 (Langtag-Trigger der Zwiebelbildung/Bulbing) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat in Wärme ab Januar/Februar) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (verträgt leichten Frost) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Steckzwiebeln auch 3–4 und 9–10) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (Steckzwiebel Juli, Saatzwiebel August–September) | `species.harvest_months` |
| Blütemonate | 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, offset (Steckzwiebeln) | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (in normalen Mengen; roh große Mengen problematisch) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile für Katzen und Hunde (Thiosulfate) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | N-Propyl-Disulfid, Allicin (für Tiere) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (für Tiere: severe) | `species.toxicity.severity` |
| Kontaktallergen | true (Zwiebelwasser reizt Augen und Haut) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Balkonkästen für Schnittlauchzwiebeln) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–15 cm in Reihe, 25–30 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, nährstoffreiche Erde, pH 6,0–7,0; gute Drainage | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (keine artspezifischen Allium-cepa-Werte aus 2 unabhängigen Quellen) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (mind. 6–8 h direkte Sonne; im Schatten Blattmasse statt Zwiebel) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–45 (flachwurzelnd; Hauptwurzelmasse in den oberen 18–20 cm, Maximum bis ~60–76 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (flachwurzelnd, sehr empfindlich gegen nasse Böden/Hypoxie) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, dS/m) | 1.2 (Bezugsgröße: Substrat-Sättigungsextrakt-ECe, nicht Gießwasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | 16 (Ertragsrückgang je dS/m oberhalb der Schwelle) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.0 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | low |
| Sämling / Jungpflanze | 21–42 | 2 | false | false | low |
| Vegetativ (Blattwachstum) | 28–56 | 3 | false | false | medium |
| Zwiebelbildung | 28–56 | 4 | false | true | medium |
| Reife / Einzug | 14–21 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Blattwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag fördert Zwiebelbildung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 (kritischer Punkt des stomatären Kollaps, oberhalb des 0.8–1.3-Korridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht; nicht mit R:FR-Verhältnis verwechseln) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Zwiebelbildung & Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 (kritischer Punkt des stomatären Kollaps, oberhalb des 1.0–1.5-Korridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (Reife: Wasser reduzieren für Lagerqualität) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |
| Sämling | 2:1:1 | 0.8–1.2 | 6.0–7.0 | 80 | 30 | — | 2 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Vegetativ | 3:1:2 | 1.2–1.8 | 6.0–7.0 | 100 | 40 | 20 | 3 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Zwiebelbildung | 1:2:3 | 1.5–2.0 | 6.0–7.0 | 100 | 50 | 25 | 2 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Reife | 0:0:1 | 0.5–1.0 | 6.0–7.0 | — | — | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> Mikronährstoffe (Mn/Zn/Cu/Mo): Keine belegten artspezifischen ppm-Sollwerte für Zwiebel-Nährlösungen aus 2 unabhängigen seriösen Quellen verfügbar; Felder bleiben als `DATEN FEHLEN` markiert statt geschätzt zu werden. <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung → Sämling | time_based | 7–14 Tage | Keimblatt sichtbar |
| Sämling → Vegetativ | time_based | 21–42 Tage | Pflanze hat 2–3 Blätter, Pikierbereit |
| Vegetativ → Zwiebelbildung | event_based | Tageslänge >14h | Langtag-Trigger in Norddeutschland ab Juni |
| Zwiebelbildung → Reife | event_based | — | Laub knickt ein, wird gelblich |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|---------|--------|
| Zwiebel- und Knoblauch-Dünger | Compo | base | 7-5-10 | 40–60 g/m² | Pflanzung |
| Kali-Magnesia | K+S | supplement | 0-0-30+10MgO | 30 g/m² | Zwiebelbildung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–4 L/m² | Frühjahr |
| Hornspäne | Oscorna | organisch-N | 60–80 g/m² | Pflanzung |

### 3.2 Besondere Hinweise zur Düngung

Zwiebeln sind Mittelzehrer. Überdüngung (besonders Stickstoff) fördert Blattwachstum auf Kosten der Zwiebelbildung und verschlechtert die Lagerfähigkeit. Kein Frischdünger. Ab der Zwiebelbildungsphase Stickstoff reduzieren und Kalium erhöhen. Frischen Stallmist meiden — erhöht Fäulnis-Risiko.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Vorkultur (Saatzwiebel) | Aussaat in Anzuchtschalen bei 15–18 °C | mittel |
| Mär–Apr | Steckzwiebeln pflanzen | 5 cm tief, Spitze knapp über dem Boden | hoch |
| Apr | Jäten | Zwiebelfeind Nummer 1 ist Unkraut; regelmäßig jäten | hoch |
| Mai | Hackschicht aufrechterhalten | Lockere Oberfläche gegen Austrocknung | mittel |
| Jun | Langtag beobachten | Zwiebelbildung beginnt selbständig | niedrig |
| Jul | Frühzwiebeln ernten | Steckzwiebeln sind reif wenn Laub knickt | mittel |
| Aug | Haupternte | Saatzwiebeln ernten; 1–2 Wochen nachtrocknen lassen | hoch |
| Sep | Lagerung | Kühl, trocken, luftig einlagern (5–10 °C) | mittel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

Betrifft ausschließlich **Wintersteckzwiebeln** (Sorten wie 'Radar', 'Shakespeare'): Sie werden im Herbst gesteckt und überwintern im Freilandbeet, um eine frühe Ernte im Folgejahr zu liefern. Sommer-Steckzwiebeln und Saatzwiebeln werden dagegen im Sommer geerntet und trocken eingelagert (keine Überwinterung im Beet).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | hardy (überwintert im Beet bis ≈ −10 °C; Schutz bei strengerem Frost) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 (5 cm Mulch/Laub/Reisig bzw. Schutzvlies bei drohendem Frost; Mulch nicht an den Zwiebelhals) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | uncover | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (Abdeckung entfernen, sobald kein Dauerfrost mehr droht) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | im Beet (keine Einlagerung; verträgt bis ≈ −10 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | Freiland-Tageslicht (kommt mit winterlich wenig Licht aus) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | keine Zusatzbewässerung; Staunässe unbedingt vermeiden | `overwintering_profiles.winter_quarter_watering` |

**Steck-/Erntefenster:** Stecken Mitte September–Oktober; Ernte ab Ende Mai/Juni des Folgejahres.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Zwiebelfliege | Delia antiqua | Larven in Zwiebel, Fäulnis; gelbes Laub | root, stem | seedling, vegetative | difficult |
| Thripse | Thrips tabaci | Silbrige Streifen auf Laub, Wachstumsrückstand | leaf | vegetative | medium |
| Zwiebelblattlaus | Neotoxoptera formosana | Gekräuseltes Laub, Honigtau | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | fungal (Peronospora destructor) | Grauer Pilzrasen auf Laub, Einrollen | Feuchtigkeit, kühle Nächte | 7–14 | vegetative |
| Zwiebelbotrytis (Halsgrau) | fungal (Botrytis allii) | Grauer Belag am Blattansatz, Fäulnis | Feuchte, Verletzungen | 5–10 | ripening, storage |
| Zwiebelbrand | fungal (Urocystis cepulae) | Schwarze Streifen in Keimblättern | infizierter Boden | 7–21 | seedling |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinernema feltiae | Zwiebelfliegen-Larven | 500.000/m² | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Engmaschiges Netz ab Pflanzung | 0 | Zwiebelfliege, Thripse |
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 3 | Thripse, Blattläuse |
| Zwiebeln anhäufeln | cultural | — | Lockere Erdschicht über Zwiebeln | 0 | Zwiebelfliege |
| Fruchtfolge | cultural | — | 3 Jahre keine Lauchgewächse | 0 | Boden-Pathogene, Nematoden |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Lauchgewächse (Amaryllidaceae/Alliaceae) |
| Empfohlene Vorfrucht | Tomaten, Kohlarten (Starkzehrer) |
| Empfohlene Nachfrucht | Salat, Spinat, Möhren |
| Anbaupause (Jahre) | 3 Jahre selbe Familie |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Möhre | Daucus carota | 0.9 | Gegenseitige Schädlingsabwehr (Zwiebelfliege ↔ Möhrenfliege) | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Platzsparend, keine Konkurrenz | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Zwiebelduft hält Schädlinge fern | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Gegenseitig förderlich | `compatible_with` |
| Erdbeere | Fragaria × ananassa | 0.8 | Zwiebelduft hält Grauschimmel fern | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Erbse | Pisum sativum | Zwiebelduft hemmt Erbsenwachstum | moderate | `incompatible_with` |
| Bohne | Phaseolus vulgaris | Gegenseitige Wachstumshemmung | moderate | `incompatible_with` |
| Knoblauch | Allium sativum | Gleiche Familie, gleiche Schädlinge; zu dicht = Konkurrenz | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Zwiebel |
|-----|-------------------|-------------|--------------------------|
| Schalotte | Allium cepa var. ascalonicum | Fast identisch | Feineres Aroma, bessere Lagerfähigkeit |
| Lauch | Allium porrum | Gleiche Familie | Kältetoleranter, längere Erntezeit |
| Schnittlauch | Allium schoenoprasum | Gleiche Familie | Perennial, kein Aufwand für Knollen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Allium cepa,"Küchenzwiebel;Speisezwiebel;Onion",Amaryllidaceae,Allium,biennial,long_day,herb,bulbous,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.3,"Zentralasien",limited,15,20,60,15,12,no,limited,false,false,medium_feeder,half_hardy,"3;4","7;8;9"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Stuttgarter Riesen,Allium cepa,–,–,"classic;round;good_storage",120,,open_pollinated
Red Baron,Allium cepa,Bejo,–,"red;medium_early",110,,f1_hybrid
Sturon,Allium cepa,–,–,"long_storage;classic_round",120,,open_pollinated
```

---

## Quellenverzeichnis

1. [Zwiebeln — Der Bio-Gärtner](https://www.bio-gaertner.de/Pflanzen/Zwiebeln) — Anbaupraxis, Bio-Tipps
2. [Zwiebeln pflanzen — Utopia.de](https://utopia.de/ratgeber/zwiebeln-pflanzen-anbauzeit-pflege-und-ernte_76710/) — Anbauzeit, Pflege
3. [Zwiebel-Mischkultur — Samen.de](https://samen.de/blog/mischkultur-mit-zwiebeln-optimale-partnerpflanzen.html) — Mischkultur-Partner
4. [Floragard Allium cepa](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/gemuese/allium-cepa) — Pflegehinweise
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [FAO — Annex 1: Crop salt tolerance data](https://www.fao.org/4/y4263e/y4263e0e.htm) — Salztoleranz Zwiebel: ECe-Schwelle 1.2 dS/m, Slope 16 %/dS/m, Klasse "sensitive" (nach Maas & Hoffman 1977)
6. [Shannon & Grieve — Tolerance of vegetable crops to salinity (USDA-ARS)](https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P1567.pdf) — Bestätigung Salztoleranz-Parameter Allium cepa (Maas-Hoffman-Modell)
7. [Bulbing in Onions: Photoperiod and Temperature Requirements (Annals of Botany)](https://academic.oup.com/aob/article-abstract/78/4/423/2587501) — kritische Tageslänge ~13.75 h, Bulbing-Schwellenwerte
8. [Growth responses of tropical onion cultivars based on growing degree days (ResearchGate)](https://www.researchgate.net/publication/264893889) — GDD-Basistemperatur ≈ 5 °C für Zwiebelwachstum, C3-Photosynthese
9. [Screening of Onion Genotypes for Waterlogging Tolerance (Frontiers in Plant Science, PMC8766973)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8766973/) — Staunässe-Empfindlichkeit (flachwurzelnd), optimale Wachstumstemperatur 20–25 °C
10. [The root systems of onion and Allium fistulosum (WUR / edepot 121472)](https://edepot.wur.nl/121472) — Wurzeltiefe: Hauptmasse obere 18–20 cm, Maximum bis ~76 cm
11. [Vernalization Responses in Onion — Pre-flowering and Reproductive Phases (ResearchGate)](https://www.researchgate.net/publication/327572392) — Vernalisation (4 °C, 3–4 Monate) als Blühinduktion
12. [A Short Review on Onion Bulb Dormancy Metabolism (Juniper Publishers)](https://juniperpublishers.com/aibm/AIBM.MS.ID.555915.php) — Knollendormanz: Rest → Endodormanz → Ökodormanz
13. [UMN Extension — Growing onions in home gardens](https://extension.umn.edu/vegetables/growing-onions) — Vollsonne-Bedarf, Boden-pH 6.0–7.0
14. [Wintersteckzwiebeln: Anbau & Pflege (beetfreunde.de)](https://www.beetfreunde.de/magazin/wintersteckzwiebeln/) — Überwinterung im Beet bis −10 °C, Mulch/Vlies-Schutz, Steck-/Erntefenster
15. [Wintersteckzwiebeln — ÖKO-TEST](https://www.oekotest.de/freizeit-technik/Wintersteckzwiebeln-Jetzt-pflanzen-im-Fruehjahr-ernten_15838_1.html) — Bestätigung Überwinterungspraxis und Frosttoleranz
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
