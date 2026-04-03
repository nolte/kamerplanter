# Stiefmuetterchen — Viola x wittrockiana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** University of Florida IFAS, Missouri Botanical Garden, NC State Extension, Hortipendium, ASPCA, Kamerplanter Spec REQ-001 v3.1 (Seed-Daten Zierpflanzen, AB-007, AB-012)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Viola x wittrockiana | `species.scientific_name` |
| Volksnamen (DE/EN) | Stiefmuetterchen, Gartenstiefmuetterchen; Garden Pansy, Pansy | `species.common_names` |
| Familie | Violaceae | `species.family` → `botanical_families.name` |
| Gattung | Viola | `species.genus` |
| Ordnung | Malpighiales | `botanical_families.order` |
| Wuchsform | `herb` | `species.growth_habit` |
| Wurzeltyp | `fibrous` (flaches, feinfaseriges Wurzelsystem) | `species.root_type` |
| Lebenszyklus | `biennial` (botanisch kurzlebig biennial/perennial, kulturell oft als Einjaehrige behandelt -- in Zone 7+ Ueberwinterung mit Fruehjahrsblute moeglich) | `lifecycle_configs.cycle_type` |
| Photoperiode | `day_neutral` (blüht bei kühlen Temperaturen unabhängig von Tageslänge; Thermoinhibition ab 22 °C hemmt sowohl Keimung als auch Blüte) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b, 10a, 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | `hardy` (übersteht leichten bis mässigen Frost bis ca. -10 °C; Hauptblüher im Frühling und Herbst) | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis ca. -10 °C. In milden Wintern (Zone 7+) überwinternd mit Blüte im zeitigen Frühjahr. Strenge Kahlfröste unter -15 °C können Pflanzen töten. Schneedecke schützt natürlich. | `species.hardiness_detail` |
| Heimat | Gartenherkunft (Hybride). Elternarten (V. tricolor, V. lutea, V. altaica) stammen aus Europa und Westasien. | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral — keine bekannten allelopathischen Wirkungen) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | `light_feeder` (Schwachzehrer — geringer Nährstoffbedarf; Überdüngung führt zu üppigem Laub auf Kosten der Blüte) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | `['ornamental', 'edible', 'bee_friendly']` (Blüten essbar und dekorativ; wichtiger Frühblütenspender für Bestäuber) | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Mitteleuropa (Zone 7–8), Bezugspunkt: letzter Frost Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 12 (Aussaat Januar–Februar für Frühjahrsblüher; AB-012: 12 statt 8 Wochen, da 8 Wochen zu kleine Pflanzen ergibt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | null (Direktsaat nicht praktikabel; Vorkultur ist Standard) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | null (alternativ: Freiland-Aussaat Juni–Juli für Herbstblüher, aber auch hier Vorkultur empfohlen) | `species.direct_sow_months` |
| Erntemonate | null (Zierpflanze, keine Ernte; `allows_harvest: false` auf allen Phasen) | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6, 9, 10 (Hauptblüte Frühling und Herbst; Sommerhitze unterbricht Blüte) | `species.bloom_months` |

<!-- AB-010: bloom_months enthaelt zwei getrennte Bluehperioden: Fruehjahr [3,4,5,6] und Herbst [9,10] mit einer Bluehpause im Juli/August (Thermoinhibition ab 25°C). Die Luecke im Array (kein 7,8) signalisiert, dass dies KEINE durchgehende Bluete ist. Die Kalenderansicht (REQ-015) muss Luecken im bloom_months-Array als separate Balken darstellen, nicht als durchgehenden Block. -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | `seed` | `species.propagation_methods` |
| Schwierigkeit | `easy` (zuverlässige Keimung bei korrekter Temperatur; Lichtkeimer, Thermoinhibition beachten) | `species.propagation_difficulty` |

**Keimhinweise (AB-007):**
- Optimale Keimtemperatur: 15–18 °C
- Minimale Keimtemperatur: 10 °C
- **Thermoinhibition ab 22 °C** — NICHT auf Heizmatte!
- Lichtkeimer: Samen nur leicht andrücken oder dünn mit Vermiculit bedecken
- Keimdauer: 10–14 Tage

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (nicht giftig) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (Cyclotide in Wurzeln nachgewiesen, in relevanten Pflanzenteilen keine toxikologische Relevanz) | `species.toxicity.toxic_compounds` |
| Schweregrad | `none` | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Insektenbestäubung, geringe Pollenfreisetzung in die Luft) | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA (als ungiftig gelistet), Kamerplanter REQ-001 Seed-Daten AB-015.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | `none` (kein Formschnitt; regelmässiges Ausputzen verblühter Blüten verlängert Blühdauer erheblich) | `species.pruning_type` |
| Rückschnitt-Monate | null | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (klassische Balkonkasten- und Topfpflanze) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1--3 (pro Pflanze) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 (flaches Wurzelsystem) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15--25 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15--25 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20--25 | `species.spacing_cm` |
| Indoor-Anbau | no (benötigt kühle Temperaturen, Indoor zu warm) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (ideal für Balkonkästen, Kübel und Schalen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (Überhitzungsgefahr, Thermoinhibition ab 22 °C) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humose, durchlässige Blumenerde. Staunässe unbedingt vermeiden. Balkonkästen mit Drainageschicht. | — |

**Hinweis:** Stiefmütterchen sind klassische Beet- und Balkonpflanzen. Sie eignen sich hervorragend für Balkonkästen, Pflanzschalen und niedrige Beeteinfassungen. Indoor-Kultur ist nicht empfehlenswert, da Stiefmütterchen kühle Temperaturen (10--18 °C) benötigen und ab 22 °C die Blüte eingestellt wird (Thermoinhibition).

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

Phasensequenz: **Annuelle Zierpflanze** (Keimung → Sämling → Vegetativ → Abhärtung → Blüte → Seneszenz). Kein Ernte-Schritt; `allows_harvest: false` auf allen Phasen. Die `hardening_off`-Phase ist obligatorisch bei Indoor-Voranzucht → Outdoor-Auspflanzung (AB-009).

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 10–14 | 1 | false | false | low |
| Sämling (seedling) | 28–42 | 2 | false | false | low |
| Vegetativ (vegetative) | 21–35 | 3 | false | false | medium |
| Abhärtung (hardening_off) | 7–14 | 4 | false | false | medium |
| Blüte (flowering) | 60–120 | 5 | false | false | medium |
| Seneszenz (senescence) | 14–28 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–100 (Lichtkeimer, diffuses Licht genügt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 4–6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–18 (**KRITISCH:** nicht über 22 °C — Thermoinhibition!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80–90 (Abdeckung/Dome) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80–90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null (Umgebung genügt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmässig feucht halten, Sprühen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10–20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–13 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1–2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Pikier-Übergang (AB-008):** Der Übergang Sämling → Vegetativ entspricht dem Pikieren. Nach dem Pikieren benötigen Stiefmütterchen 3–5 Tage Erholungszeit (erhöhte Luftfeuchtigkeit 70–80 %, gedämpftes Licht ca. 100 µmol/m²/s).

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 (Halbschatten bis volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 (kühle Temperaturen fördern kompakten Wuchs) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Abhärtung (hardening_off)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 (schrittweise Steigerung auf Aussenbedingungen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natürlich (Aussenklima) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–20 (schrittweise tiefere Nachttemperaturen tolerieren) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 3–10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 (Aussenluft) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (volle bis halbe Sonne; Halbschatten bei Sommerhitze) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natürlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–20 (optimal 15–18; bei dauerhaft über 25 °C lässt Blütenqualität drastisch nach) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–10 (kühle Nächte fördern Blütenbildung) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2–4 (witterungsabhängig) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Seneszenz (senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natürlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–30 (Sommerhitze löst Seneszenz aus) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3–5 (reduziert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 5.5–6.0 | — | — | — | — |
| Sämling | 1:1:1 | 0.5–0.8 | 5.5–6.0 | 60 | 30 | — | 1.5 |
| Vegetativ | 2:1:2 | 0.8–1.2 | 5.5–6.2 | 80 | 40 | 30 | 2.0 |
| Abhärtung | 1:1:2 | 0.6–1.0 | 5.5–6.2 | 70 | 35 | 25 | 1.5 |
| Blüte | 1:2:2 | 0.8–1.2 | 5.5–6.2 | 80 | 40 | 30 | 2.0 |
| Seneszenz | 0:0:0 | 0.0 | — | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung → Sämling | `time_based` | 10–14 Tage | Keimblätter sichtbar, Samenschale abgeworfen |
| Sämling → Vegetativ | `manual` | 28–42 Tage | 3–4 echte Blattpaare, Pikierung erfolgt |
| Vegetativ → Abhärtung | `manual` | 21–35 Tage nach Pikierung | Pflanze ausreichend gross (8–10 cm), Aussentemperaturen nachts über 0 °C |
| Abhärtung → Blüte | `time_based` | 7–14 Tage | Schrittweise Akklimatisierung abgeschlossen, Auspflanzung ins Freiland |
| Blüte → Seneszenz | `event_based` | 60–120 Tage | Sommerhitze dauerhaft über 25 °C; Blütenproduktion lässt deutlich nach |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Beet/Topf)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|----------------|--------|
| Blumendünger flüssig | Compo | Volldünger | 7-3-6 | ~0.08 | 3 | vegetativ, blüte |
| Balkonpflanzendünger | Substral (Scotts) | Volldünger | 7-5-6 | ~0.08 | 3 | vegetativ, blüte |
| CalMag | Canna | Supplement | 0-0-0 + 5 % Ca, 2 % Mg | ~0.05 | 2 | alle (nur bei kalkarmem Wasser) |

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | Bodenverbesserer | 2–3 L/m² | Frühjahr bei Pflanzung | Grundversorgung |
| Hornmehl (fein) | Oscorna / Neudorff | Langzeit-N | 40–60 g/m² | Frühjahr | Schwachzehrer (reduzierte Dosis) |
| Schafwollpellets | Plantura / Oscorna | Langzeit-Volldünger | 40–60 g/m² | Frühjahr | alle |
| Wurmkompost | eigen / diverse | Volldünger | 1–2 L/m² | bei Pflanzung | Topfkultur |

### 3.2 Düngungsplan (Beispiel: Topf-/Beetkultur)

| Woche | Phase | EC (mS) | pH | Dünger (ml/L) | Hinweise |
|-------|-------|---------|-----|----------------|----------|
| 1–2 | Keimung | 0.0 | 5.5–6.0 | nur Wasser | Kein Dünger — Nährstoff-vorgeladenes Aussaatsubstrat genügt |
| 3–6 | Sämling | 0.5–0.8 | 5.5–6.0 | 1–2 ml/L Volldünger (halbe Dosis) | Alle 2 Wochen, ab 2. echtem Blattpaar |
| 7–10 | Vegetativ | 0.8–1.2 | 5.5–6.2 | 2–3 ml/L Volldünger | Alle 14 Tage |
| 11–12 | Abhärtung | 0.6–1.0 | 5.5–6.2 | 1–2 ml/L K-betont | Kalium fördert Frosttoleranz |
| 13+ | Blüte | 0.8–1.2 | 5.5–6.2 | 2–3 ml/L Blühpflanzendünger | Alle 14 Tage, P-/K-betonte Formulierung |

### 3.3 Mischungsreihenfolge

> **Hinweis:** Bei Stiefmütterchen als Schwachzehrer sind die EC-Werte niedrig, daher ist das Ausfällungsrisiko gering. Trotzdem gilt die Standardreihenfolge:

1. CalMag (falls benötigt — nur bei kalkarmem Wasser oder Regenwasser)
2. Volldünger / Blühpflanzendünger
3. pH-Korrektur (IMMER zuletzt — Ziel pH 5.5–6.2)

### 3.4 Besondere Hinweise zur Düngung

- **Schwachzehrer:** Stiefmütterchen sind anspruchslos. Überdüngung (EC > 1.5 mS) führt zu üppigem, weichem Laub, geringerer Blütenbildung und erhöhter Anfälligkeit für Botrytis.
- **Kalium vor Winter:** Bei Herbstpflanzung für Überwinterung eine betont kaliumhaltige Düngung (K₂O) im Oktober geben — Kalium erhöht die Frosttoleranz durch verbesserten Zellturgor.
- **Eisen:** Bei Chlorose (gelbe Blätter mit grünen Blattadern) Eisenchelat nachliefern. Tritt besonders bei pH > 6.5 auf.
- **Keine Düngung im Hochsommer:** Wenn Pflanzen in Seneszenz gehen (Sommerhitze), nicht weiter düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `custom` (kein exakt passender Preset; am nächsten: `outdoor_perennial`, aber Stiefmütterchen sind einjährig kultiviert) | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 3 (bei Hitze und Topfkultur ggf. täglich) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 (im Winter stark reduzieren, nur bei Trockenheit und frostfreien Tagen) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | `top_water` | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | null (Leitungswasser problemlos) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 4, 5, 6, 9, 10 (Pause im Hochsommer und Winter) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | null (einjährig kultiviert — kein Umtopfen nötig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Aussaat Vorkultur | Für Frühjahrsflor: Aussaat in Schalen bei 15–18 °C. Lichtkeimer, NICHT zu warm! | hoch |
| Feb | Sämlinge pikieren | Pikieren ab 2. Blattpaar in Einzeltöpfe (7-cm). Temperatur weiter kühl halten. | hoch |
| Mär | Abhärtung + Pflanzung | Ab Mitte März schrittweise an Aussentemperaturen gewöhnen. Auspflanzung ins Freiland oder Kübel ab Ende März. | hoch |
| Apr | Blüte beginnt | Regelmässig giessen. Alle 14 Tage düngen. Verblühte Blüten konsequent ausputzen. | mittel |
| Mai | Hauptblüte | Weiter giessen und düngen. Ausputzen fördert Nachblüte. | mittel |
| Jun | Blüte lässt nach | Bei Hitze Standort mit Nachmittagsschatten wählen. Düngung reduzieren. | niedrig |
| Jul | Seneszenz | Bei Sommerkultur: Pflanzen werden schwach und längelig. Entsorgen und Beet für Sommerblüher räumen. Alternativ: Herbst-Aussaat starten. | niedrig |
| Aug | Herbst-Aussaat | Für Herbst-/Winterblüher: Aussaat Anfang August bei 15–18 °C. | hoch |
| Sep | Herbst-Pflanzung | Jungpflanzen (aus August-Aussaat oder Kaufware) ins Freiland setzen. Düngung starten. | hoch |
| Okt | Herbstblüte | Stiefmütterchen blühen erneut bei kühlen Temperaturen. Kaliumdüngung für Winterhärte geben. | mittel |
| Nov | Wintervorbereitung | Giessen stark reduzieren. Mulchen mit Laub oder Reisig bei strengem Frost empfehlenswert. | niedrig |
| Dez | Winterruhe | Nur bei Kahlfrost und Trockenheit giessen (an frostfreien Tagen). Schneedecke schützt natürlich. | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | `hardy` (in Zone 7+ überwintern Stiefmütterchen im Freiland) | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | `mulch` (leichte Abdeckung mit Laub oder Reisig bei Kahlfrost unter -10 °C) | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Massnahme | `uncover` (Mulch im Frühjahr entfernen, Düngung beginnen) | `overwintering_profiles.spring_action` |
| Frühlings-Massnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | null (Freiland) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | null | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | null | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | `minimal` (nur bei Kahlfrost und Trockenheit, an frostfreien Tagen) | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse (Aphids) | Myzus persicae, Aphis fabae | Verkrüppelte Triebspitzen, klebrige Blätter (Honigtau), Verfärbungen | leaf, flower | vegetative, flowering | easy |
| Schnecken (Slugs/Snails) | Arion vulgaris, Deroceras reticulatum | Lochfrass an Blättern und Blüten, Schleimspuren | leaf, flower | seedling, vegetative, flowering | easy |
| Trauermücken (Fungus Gnats) | Bradysia spp. | Kümmerlicher Wuchs bei Sämlingen, Larven an Wurzeln im feuchten Substrat | root | germination, seedling | medium |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Saugstellen auf Blütenblättern, Verkrüppelung | flower, leaf | flowering | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel (Botrytis) | `fungal` | Grau-braunes Pilzgeflecht auf Blüten und Blättern, Fäulnis | Hohe Luftfeuchtigkeit, zu dichter Stand, kühle Temperaturen | 3–7 | flowering |
| Echter Mehltau (Powdery Mildew) | `fungal` | Weisser, mehlartiger Belag auf Blattoberseiten | Trocken-warme Tage, kühle Nächte, schlechte Luftzirkulation | 5–10 | vegetative, flowering |
| Falscher Mehltau (Downy Mildew) | `fungal` | Gelbliche Flecken auf Blattoberseiten, grau-violetter Belag auf Blattunterseiten | Hohe Luftfeuchtigkeit, kühle Temperaturen, Blattnässe | 5–14 | vegetative, flowering |
| Stiefmütterchen-Welke (Black Root Rot) | `fungal` | Welke trotz Bewässerung, dunkle Verfärbung am Stängelgrund und an Wurzeln | Staunässe, kontaminiertes Substrat (Thielaviopsis basicola) | 7–14 | vegetative, flowering |
| Violetter Wurzelschimmel (Violet Root Rot) | `fungal` | Violetter Pilzbelag auf Wurzeln, Kümmerwuchs, Welke | Schwere, nasse Böden | 14–28 | vegetative, flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarven) | Blattläuse | 5–10 | 14 |
| Steinernema feltiae (Nematoden) | Trauermückenlarven | 500.000/m² | 7–14 |
| Phasmarhabditis hermaphrodita (Schneckennematoden) | Nacktschnecken | 300.000/m² | 7–14 |
| Coccinella septempunctata (Marienkäfer) | Blattläuse | 5–10 | 14–21 |
| Amblyseius cucumeris (Raubmilbe) | Thripse | 50–100 | 14–21 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | `biological` | Azadirachtin | Sprühen, 0.5 % Lösung | 0 (Zierpflanze) | Blattläuse, Thripse |
| Kaliseife (Schmierseife) | `biological` | Kaliumsalze von Fettsäuren | Sprühen, 2 % Lösung | 0 | Blattläuse |
| Rohmilch-Spritzung | `cultural` | Milchsäurebakterien | 1:9 mit Wasser verdünnt, wöchentlich | 0 | Echter Mehltau |
| Schneckenkorn (Eisen-III-Phosphat) | `chemical` | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m² | 0 (bienenungefährlich) | Schnecken |
| Ausreichender Pflanzabstand | `cultural` | — | Mindestens 20 cm Abstand | 0 | Botrytis, Mehltau (Luftzirkulation) |
| Befallene Teile entfernen | `cultural` | — | Sofort entsorgen (nicht kompostieren!) | 0 | Botrytis, Mehltau |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine dokumentierten natürlichen Resistenzen auf Artniveau | — | — |

Hinweis: Einige Cultivar-Serien (z.B. Matrix) zeigen erhöhte Hitzetoleranz, aber keine verifizierte Krankheitsresistenz.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (`light_feeder`) |
| Fruchtfolge-Kategorie | Veilchengewächse (Violaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Solanaceae, Cucurbitaceae) oder Hülsenfrüchtler (Fabaceae — N-Fixierung hinterlässt Reststickstoff) |
| Empfohlene Nachfrucht | Mittelzehrer (Apiaceae, Asteraceae) oder erneut Schwachzehrer |
| Anbaupause (Jahre) | 2–3 Jahre gleiche Stelle (Violaceae), um bodenbürtige Pilze (Thielaviopsis basicola) zu vermeiden |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Hornveilchen | Viola cornuta | 0.9 | Gleiche Familie, identische Pflege, Verlängerung der Blühdauer durch verschiedene Cultivars | `compatible_with` |
| Vergissmeinnicht | Myosotis sylvatica | 0.8 | Gemeinsamer Standortanspruch (Halbschatten, frisch), optische Ergänzung | `compatible_with` |
| Primel | Primula vulgaris | 0.8 | Gleiche Kühlklima-Anforderungen, optische Ergänzung im Frühjahr | `compatible_with` |
| Bellis (Tausendschön) | Bellis perennis | 0.8 | Gleicher Standort, Schwachzehrer, optische Ergänzung | `compatible_with` |
| Tulpe, Narzisse (Unterpflanzung) | Tulipa spp., Narcissus spp. | 0.7 | Stiefmütterchen bedecken Boden über Zwiebeln; Platzoptimierung; Bestäuber-Magnet | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.7 | Stiefmütterchen locken Bestäuber an; Bodenbedeckung im Frühjahr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sonnenblume | Helianthus annuus | Allelopathische Hemmstoffe können Wachstum kleiner Begleitpflanzen unterdrücken; extremer Nährstoff- und Lichtkonkurrent | `moderate` | `incompatible_with` |
| Kohlarten | Brassica oleracea spp. | Kohlweisslinge und Erdflöhe können auf Violaceae übergehen; Starkzehrer entziehen Nährstoffe | `mild` | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Solanaceae | `shares_pest_risk` | Myzus persicae (Grüne Pfirsichblattlaus) ist polyphag und befällt sowohl Viola als auch Solanaceae | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Stiefmütterchen |
|-----|-------------------|-------------|------------------------------|
| Hornveilchen | Viola cornuta | Sehr ähnlich, aber kleinblütiger und ausdauernder | Längere Blühdauer (März–Oktober durchgehend), hitzeverträglicher, echte Perenne |
| Wildes Stiefmütterchen | Viola tricolor | Wildform der Elternart, zierlich | Selbstaussaat, robuster, natürlicheres Erscheinungsbild, bienenfreundlicher |
| Primel (Kissenprimel) | Primula vulgaris | Ähnlicher Standort (kühl-feucht, Halbschatten) | Perennial, überwinternd, winterblühend (Februar–April) |
| Bellis (Tausendschön) | Bellis perennis | Gleicher Einsatzbereich (Frühjahrs-Beet) | Noch anspruchsloser und widerstandsfähiger; Selbstaussaat |
| Winter-Alpenveilchen | Cyclamen coum | Winterblüher für schattige Standorte | Blüht im Winter (Dezember–März), echtes Perennial, Knollengewächs |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,bloom_months,sowing_indoor_weeks_before_last_frost,traits
Viola x wittrockiana,Stiefmütterchen;Gartenstiefmütterchen;Garden Pansy;Pansy,Violaceae,Viola,biennial,day_neutral,herb,fibrous,6a;6b;7a;7b;8a;8b;9a;9b;10a;10b,0.0,Europa/Westasien (Hybride),hardy,light_feeder,3;4;5;6;9;10,12,ornamental;edible;bee_friendly
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type
Matrix Mixed,Viola x wittrockiana,PanAmerican Seed,--,compact;heat_tolerant;uniform;large_flower,f1_hybrid
Colossus Mixed,Viola x wittrockiana,Syngenta Flowers,--,extra_large_flower;early_flowering;compact,f1_hybrid
Swiss Giant Mixed,Viola x wittrockiana,--,--,large_flower;classic;vigorous,open_pollinated
Frizzle Sizzle Mixed,Viola x wittrockiana,PanAmerican Seed,--,ruffled_petals;compact;unique_form,f1_hybrid
Cats Mix,Viola x wittrockiana,--,--,whisker_markings;compact;early_flowering,f1_hybrid
```

---

## Quellenverzeichnis

1. University of Florida IFAS — Viola x wittrockiana Pansy: https://ask.ifas.ufl.edu/publication/FP609
2. Missouri Botanical Garden — Viola x wittrockiana: https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a616
3. NC State Extension — Viola x wittrockiana: https://plants.ces.ncsu.edu/plants/viola-x-wittrockiana/
4. Gardenia.net — Pansy Plant Profile: https://www.gardenia.net/plant/viola-wittrockiana
5. Hortipendium — Viola Schadbilder: https://www.hortipendium.de/Viola_Schadbilder
6. ASPCA — Toxic and Non-Toxic Plants: Pansy (als ungiftig gelistet)
7. Kamerplanter Spec REQ-001 v3.1 — Seed-Daten Zierpflanzen-Species (Keimtemperaturen AB-007, Voranzucht-Korrektur AB-012, Toxizität AB-015)
8. Kamerplanter Spec REQ-003 v2.2 — Phasensequenz Annuelle Zierpflanze (AB-008 Pikier-Übergang, AB-009 Abhärtung)
