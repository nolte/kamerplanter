# Amaryllis (Ritterstern) — Hippeastrum hybridum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Pflanzen-Kölle – Amaryllis Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-amaryllis-richtig/), [Hortipendium – Hippeastrum Hybride](https://hortipendium.de/Hippeastrum_Hybride), [Intratuin – Amaryllis Pflege](https://www.intratuin.de/pflanzenlexikon/amaryllis-hippeastrum-pflege), [Lubera – Hippeastrum](https://www.lubera.com/de/gartenbuch/amaryllis-p3258)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hippeastrum hybridum | `species.scientific_name` |
| Volksnamen (DE/EN) | Amaryllis, Ritterstern; Amaryllis, Knight's Star Lily | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` → `botanical_families.name` |
| Gattung | Hippeastrum | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Zwiebeln frostfrei einlagern; keine Temperaturen unter +5°C | `species.hardiness_detail` |
| Heimat | Tropisches und subtropisches Südamerika | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-GDD-Basiswert für Hippeastrum auffindbar; Keim-/Schadtemperaturen nicht als Wuchsbasis umetikettiert --> | `species.base_temp` |
| Lebensdauer (Jahre) | 25–50 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (keine obligate Vernalisation; Kühllagerung dient der Blühterminsteuerung, nicht der Vernalisation) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis:** Im Handel wird die Pflanze oft als "Amaryllis" verkauft, ist aber botanisch korrekt Hippeastrum. Die echte Amaryllis (Amaryllis belladonna) ist eine südafrikanische Art und in Mitteleuropa kaum im Handel.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zwiebelpflanze, Haus) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 12, 1, 2, 3 (Weihnachts-/Winterblüher, je nach Einpflanzdatum) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, division, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |
<!-- Quelle: growing-phase-auditor 2026-07 — `seed` ergänzt (Brutzwiebeln/offset weiterhin Standardmethode für Hobbygärtner, `easy`); Samenvermehrung als botanisch belegte Zusatzmethode (3/3 Quellen: RHS, Univ. Wisconsin Extension, Gardener's Path), jedoch mehrjährig (3–6 Jahre bis Blüte) und daher nicht schwierigkeitsrelevant für `propagation_difficulty` -->


### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, besonders die Zwiebel (stark giftig!) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Lycorin, Hippeastrin (Alkaloide) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (nach Verblühen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–70 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–35 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, gut drainierte Zimmerpflanzenerde; enge Topfwahl (Zwiebel passt gut rein); oberes Zwiebeldrittel soll aus der Erde schauen | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point) min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP-Messwert für Hippeastrum in 2 unabhängigen seriösen Quellen belegt --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 20–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-a-Wert (Substrat-ECe) für Hippeastrum belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-b-Wert für Hippeastrum belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis zur Standort-Physiologie:** Hippeastrum ist eine C3-Pflanze (kein CAM/Sukkulent — Spaltöffnungen öffnen tagsüber, schließen nachts; belegt durch Gaswechselmessungen, NYBG/PMC9232429). Die effektive Wurzeltiefe von 20–30 cm leitet sich aus der empfohlenen Mindest-Topftiefe (≥ 30 cm für gutes Wurzelwachstum, RHS/Sarah Raven) und der fleischigen Zwiebelwurzelbasis ab. Die UF/IFAS-EDIS-Publikation FP255 stuft die Boden-Salztoleranz ausdrücklich als „poor" ein (→ `sensitive`); ein abweichender „high"-Eintrag einer Demo-Garten-Sortenliste wurde zugunsten der primären EDIS-Quelle verworfen. Der Boden-pH-Vorzug (6.0–6.5) ist mit den pH-Angaben in §2.3 und §3.2 harmonisiert; Quellen nennen Spannen bis 6.0–7.0 (RHS/Gardener's Path), der engere Korridor bleibt quellentreu zum bestehenden Dokument.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einpflanzen/Austrieb | 14–28 | 1 | false | false | low |
| Blüte | 21–42 | 2 | false | false | medium |
| Blattphase (Aufbau) | 120–180 | 3 | false | false | medium |
| Ruhephase (Einziehen) | 60–90 | 4 | false | false | high |
| Trockenlagerung | 60–90 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Einpflanzen/Austrieb

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (heller bis halbschattiger Standort; offenes Tageslicht ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blattphase (Aufbau) — Frühjahr bis Sommer

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 21–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (heller bis halbschattiger Standort; offenes Tageslicht ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Ruhephase/Trockenlagerung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | — | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | — | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 0 (trocken lagern!) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Einpflanzen/Austrieb | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — | — |
| Blüte | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — | — |
| Blattphase | 2:1:3 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 | <!-- DATEN FEHLEN: kein artspezifischer Mn-Wert für Hippeastrum belegt --> | <!-- DATEN FEHLEN: kein artspezifischer Zn-Wert für Hippeastrum belegt --> | <!-- DATEN FEHLEN: kein artspezifischer Cu-Wert für Hippeastrum belegt --> | <!-- DATEN FEHLEN: kein artspezifischer Mo-Wert für Hippeastrum belegt --> |
| Ruhephase | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 — Mikronährstoff-Spalten Mn/Zn/Cu/Mo ergänzt; keine Hippeastrum-spezifischen ppm-Werte in 2 unabhängigen seriösen Quellen belegbar -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Einpflanzen → Blüte | time_based | 14–28 Tage | Blütenstängel erscheint |
| Blüte → Blattphase | time_based | 21–42 Tage | Blüten verblüht, Blätter wachsen |
| Blattphase → Ruhephase | manual | 120–180 Tage | Herbst, Blätter einziehen lassen |
| Ruhephase → Einpflanzen | time_based | 60–90 Tage | Neue Einpflanzung Okt–Nov |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Compo | base | 4-6-8 | 5 ml/L | 1 | blattphase (ab Mai) |
| Zwiebelblumendünger | Substral | base | 6-9-12 | 5 ml/L | 1 | blattphase |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | — | organisch | 1 TL/Topf | Apr–Jun | medium_feeder |
| Guano Blumendünger | Gardol | organisch | 2 ml/L | Mai–Aug | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| Okt–Dez | Einpflanzen/Blüte | 0.0 | — | Kein Dünger |
| Jan–Mär | Blüte | 0.0 | — | Kein Dünger |
| Apr–Sep | Blattphase | 1.0–1.5 | 6.2 | Alle 2 Wochen, Zwiebel aufbauen |
| Okt | Einziehen | — | — | Dünger einstellen, Wasser einstellen |
| Nov–Dez | Trockenphase | — | — | Komplett trocken und dunkel |

### 3.3 Mischungsreihenfolge

1. Wasser
2. Flüssigdünger

### 3.4 Besondere Hinweise zur Düngung

Der Schlüssel zu einer guten Wiederblüte liegt in der Blattphase (April–September): Jetzt müssen ausreichend Nährstoffe für die Zwiebel eingelagert werden. Wer die Pflanze im Sommer üppig düngt und viel Licht gibt, wird im Winter mit prächtigen Blüten belohnt. Ab September Düngung einstellen, ab Oktober Wasser schrittweise reduzieren, bis komplett einziehen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0 (Ruhezeit!) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; keine Staunässe; obere Zwiebelhälfte trocken halten | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Blütezeit | Blühende Pflanze hell und warm halten | niedrig |
| Feb–Mär | Verblüht | Blütenschaft entfernen (tief am Ansatz), Blätter stehen lassen | mittel |
| Apr | Düngung beginnen | Blätter wachsen, Zwiebel aufbauen | hoch |
| Mai–Sep | Blattphase | Hell, warm, regelmäßig gießen und düngen | hoch |
| Sep | Düngung einstellen | Blätter beginnen gelb zu werden | mittel |
| Okt | Einziehen | Blätter zurückschneiden, Topf dunkel und trocken stellen | hoch |
| Nov | Ruhezeit | Komplett trocken, dunkel, 10–15°C | hoch |
| Okt–Nov | Einpflanzen | Neue Zwiebeln einpflanzen oder Überständige herausnehmen | hoch |

### 4.3 Überwinterung (Knollen-Zyklus)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | dig_and_store | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | dig_store | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | replant | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 10 (Einpflanzen im Herbst für Winterblüte) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schmierläuse | Planococcus citri | Weißer Wollbelag an Zwiebel | bulb, stem | alle | medium |
| Wollläuse | Pseudococcus spp. | Weißes Gespinst in Blattachseln | stem, leaf | vegetative | medium |
| Spinnmilben | Tetranychus urticae | Gelbliche, gesprenkelte Blätter | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Roter Brenner (Stagonospora-Fäule) | fungal (Stagonospora curtisii) | Rote Flecken auf Zwiebel, Blättern, Stängel | overwatering, high_humidity | 7–21 | alle |
| Zwiebelfäule | fungal | Weiche, braune Zwiebel | overwatering | 7–14 | ruhephase |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Belag | high_humidity | 3–7 | blüte |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Schmierläuse, Wollläuse | 1–2 Käfer/Pflanze | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Schmierläuse, Spinnmilben |
| Alkohol (70%) | mechanical | Isopropanol | Wattestäbchen | 0 | Schmierläuse |
| Kupferfungizid | chemical | Kupferhydroxid | Zwiebeln einlegen vor Einpflanzen | 0 | Roter Brenner |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zwiebelpflanze, Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Hippeastrum hybridum |
|-----|-------------------|-------------|------------------------------|
| Narzisse | Narcissus papyraceus | Zwiebelpflanze, Winterblüher | Draußen möglich, gärtnerisch eingeplant |
| Belladonnalilie | Amaryllis belladonna | Gleiche Familie | Kräftigere Farben, südafrikanisch |
| Lilie | Lilium hybridum | Große Blüten, Zwiebel | Sommerblühend, draußen kultivierbar |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Hippeastrum hybridum,Amaryllis;Ritterstern;Knight's Star Lily,Amaryllidaceae,Hippeastrum,perennial,day_neutral,herb,bulbous,9a;9b;10a;10b;11a;11b,0.0,Tropisches Südamerika,yes,3,20,70,35,—,yes,no,false,true
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle – Amaryllis Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-amaryllis-richtig/) — Vollständige Pflegeanleitung
2. [Hortipendium – Hippeastrum Hybride](https://hortipendium.de/Hippeastrum_Hybride) — Botanik, Krankheiten
3. [Intratuin – Amaryllis Pflege](https://www.intratuin.de/pflanzenlexikon/amaryllis-hippeastrum-pflege) — Jahreszyklus
4. [Lubera – Hippeastrum](https://www.lubera.com/de/gartenbuch/amaryllis-p3258) — Kulturtipps
5. [Pflanzenfreunde – Hippeastrum](https://www.pflanzenfreunde.com/lexika/knollenpflanzen/hippeastrum.htm) — Schädlinge
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [UF/IFAS EDIS FP255 – Hippeastrum x hybridum Amaryllis](https://ask.ifas.ufl.edu/fp255) — Standortrating: Licht (part shade/part sun), Bodensalztoleranz „poor" → sensitive, Trockentoleranz moderat, Wuchsrate langsam
7. [NC State Extension Gardener Plant Toolbox – Hippeastrum](https://plants.ces.ncsu.edu/plants/hippeastrum/) — Lichtexposition (Vollsonne bis Halbschatten), Drainage (gut drainiert nötig), USDA-Zonen, Wuchshöhe
8. [NYBG Research Guides – Houseplant Care: Amaryllis (Hippeastrum)](https://libguides.nybg.org/hippeastrum) — Lichtbedarf, Substrat, Pflanzdtiefe, Photosynthese-Rolle der Blätter
9. [PMC9232429 – Non-invasive assessment of leaf aerenchyma in Hippeastrum and its relation to plant water status](https://pmc.ncbi.nlm.nih.gov/articles/PMC9232429/) — Gaswechsel/Spaltöffnungsverhalten (tagsüber offen, nachts geschlossen) → C3-Physiologie, kein CAM
10. [University of Illinois Extension – How to take care of amaryllis and get them to rebloom](https://extension.illinois.edu/blogs/good-growing/2021-12-03-how-take-care-amaryllis-and-get-them-rebloom) — Dormanz optional (nicht obligat), Ruheperiode 8–12 Wochen, Blühterminsteuerung
11. [University of Wisconsin Horticulture – Amaryllis, Hippeastrum](https://hort.extension.wisc.edu/articles/amaryllis-hippeastrum/) — Temperaturen (Lagerung 10–12 °C, Optimum), Dormanz nicht erforderlich, Pflegezyklus
12. [Amarylia – How Many Years Can an Amaryllis Actually Bloom?](https://amarylia.com/blogs/news/how-many-years-can-an-amaryllis-actually-bloom) — Lebensdauer der Zwiebel (25 Jahre, Erbstücke 50+ Jahre)
13. [RHS – Hippeastrum Growing Guide](https://www.rhs.org.uk/plants/hippeastrum/growing-guide) — Topftiefe ≥ 30 cm, Wurzelraum, Pflege
14. [Gardener's Path – What Type of Soil Does Amaryllis Need?](https://gardenerspath.com/plants/flowers/amaryllis-soil/) — Boden-pH 6.0–7.0, Drainage, Substratmischung
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor Audit 2026-07 -->
15. [RHS – Hippeastrum Growing Guide](https://www.rhs.org.uk/plants/hippeastrum/growing-guide) — Vermehrung durch Samen (Aussaat Frühjahr, 21°C, bis 6 Jahre bis Blüte) und Brutzwiebeln (offsets, 3–4 Jahre bis Blüte); Blüte „winter to spring", Pflanzung Okt–Jan
16. [University of Wisconsin Horticulture – Amaryllis, Hippeastrum](https://hort.extension.wisc.edu/articles/amaryllis-hippeastrum/) — Drei Vermehrungswege bestätigt: „separating offsets, dividing bulbs, and growing from seed"; Dormanz optional (nicht obligat), nur zur Blühterminsteuerung
17. [Gardener's Path – How to Grow Amaryllis (Hippeastrum) from Seed](https://gardenerspath.com/plants/flowers/propagate-amaryllis-seed/) — Samenvermehrung möglich, 3–5 Jahre bis zur ersten Blüte, Handbestäubung/Samenernte beschrieben
