# Gardenie — Gardenia jasminoides

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Care Guide](https://www.gardenia.net/guide/learn-how-to-grow-and-care-for-your-gardenia), [UK Houseplants – Gardenia](https://www.ukhouseplants.com/plants/gardenia-jasminoides), [Clemson HGIC – Gardenia](https://hgic.clemson.edu/factsheet/gardenia/), [Lubera – Gardenie](https://www.lubera.com/de/gartenbuch/gardenie-gardenia-jasminoides-pflege-ueberwintern-p3134)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Gardenia jasminoides | `species.scientific_name` |
| Volksnamen (DE/EN) | Gardenie; Cape Jasmine, Gardenia | `species.common_names` |
| Familie | Rubiaceae | `species.family` → `botanical_families.name` |
| Gattung | Gardenia | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für G. jasminoides auffindbar; Wachstum stoppt unterhalb ~15,5 °C (60 °F), aber dies ist kein validierter GDD-base --> | `species.base_temp` |
| Lebensdauer (Jahre, perennial) | 30–50 (Topfkultur deutlich kürzer, mit guter Pflege >10) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (kein Kältebedarf; immergrüne Subtropenart. Kühle Nächte ~13–17 °C fördern den Blütenansatz als Temperaturreiz, sind aber KEINE Vernalisation) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (day_neutral; Blühinduktion über Nachttemperatur, nicht Photoperiode) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 8a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | In Mitteleuropa reine Kübelpflanze; frostfrei überwintern bei 8–15°C; verträgt kurzzeitig Temperaturen bis ca. -5°C (Zone 8a), aber Blütenknospen erfrieren bereits bei leichtem Frost. Kalte Nächte (10–15°C) im Herbst sind für die Knospenbildung förderlich. | `species.hardiness_detail` |
| Heimat | China, Japan, Vietnam, Süd-/Ostasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 (intensiver Jasminduft) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, besonders Früchte | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Geniposid (Iridoid-Glykosid), Gardeniosid | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (nach Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 (in Natur bis 200 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–120 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Saure, humusreiche Rhododendronerde oder Azaleen-Substrat; pH 5.0–6.0 zwingend; sehr gute Drainage | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt für G. jasminoides in zwei unabhängigen Quellen belegt; als schattentolerante C3-Art ist ein niedriger LCP plausibel, aber nicht quantifiziert --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: siehe min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–45 (flaches, faseriges Wurzelsystem; Hauptmasse in den oberen ~30 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | moderate | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine belegte Maas-Hoffman-Schwelle; Quellen nennen nur qualitativ "poor salt tolerance" (sensitive), kein ECe-Wert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.0–6.0 | `species.soil_ph_preference` |

> Hinweis: Lichtsättigung/Optimum liegt klar oberhalb des Kompensationspunkts; Gardenie braucht helles indirektes Licht bzw. lichten Halbschatten (Morgensonne + Nachmittagsschatten), verträgt aber weder pralle Mittagssonne noch tiefen Schatten. Staunässe wird nur kurzzeitig toleriert ("occasionally wet"), dauerhaft nasse Wurzeln führen zu Wurzelfäule — daher `moderate` statt `tolerant`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | medium |
| Knospenbildung (Frühjahr) | 30–60 | 2 | false | false | low |
| Blüte | 60–120 | 3 | false | false | low |
| Vegetativ (Sommer/Herbst) | 90–120 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 (heller bis halbschattiger Standort; offenes Tageslicht ≈ 0.5, Halbschatten leicht höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 (heller bis halbschattiger Standort; offenes Tageslicht ≈ 0.5, Halbschatten leicht höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Winterruhe | 0:0:0 | 0.0 | 5.0–6.0 | — | — | — | — | — | — | — | — |
| Knospenbildung | 1:2:1 | 0.8–1.2 | 5.0–6.0 | 80 | 40 | — | 3 | 0.5 | 0.05 | 0.02 | 0.05 |
| Blüte | 1:2:2 | 1.0–1.5 | 5.0–6.0 | 80 | 40 | — | 3 | 0.5 | 0.05 | 0.02 | 0.05 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 5.0–6.0 | 100 | 50 | — | 3 | 0.5 | 0.05 | 0.02 | 0.05 |

> Mikronährstoff-Zielwerte (Mn/Zn/Cu/Mo) folgen den etablierten Hoagland-Nährlösungsstandards (Mn 0,5 · Zn 0,05 · Cu 0,02 · Mo 0,01–0,05 ppm) und sind auf die Fe-Zugabe (3 ppm, chelatiert) im sauren pH-Fenster 5,0–6,0 abgestimmt. Gardenie ist für Mn-Mangel (Blattvergilbung zwischen den Adern) bei zu hohem pH dokumentiert anfällig (UF/IFAS NutDef). `species.manganese/zinc/copper/molybdenum_ppm` → `nutrient_profiles.*`
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Knospenbildung | time_based | — | Frühjahr, wärmere Temperaturen |
| Knospenbildung → Blüte | time_based | 30–60 Tage | Knospen sichtbar |
| Blüte → Vegetativ | time_based | 60–120 Tage | Blüten verblüht |
| Vegetativ → Winterruhe | time_based | 90–120 Tage | Herbst, kühler Standort |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Kübel)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Rhododendron-Dünger | Compo | base | 12-4-8 + Fe-EDTA | 5 ml/L | 1 | alle aktiven |
| Azaleendünger | Substral | base | 7-4-9 | 5 ml/L | 1 | blüte, vegetativ |

#### Organisch (Kübel)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Rhododendron-Langzeitdünger | Cuxin | organisch | 50 g/10L Topf | Apr–Sep | medium_feeder |
| Eisendünger (chelat) | Sequestrene | supplement | 5 g/10L Topf | Bei Chlorose | Eisenmangel |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| Jan–Feb | Winterruhe | 0.0 | — | Kein Dünger |
| Mär–Mai | Knospenbildung | 0.8–1.2 | 5.5 | Alle 2 Wochen, Eisen-Dünger |
| Jun–Sep | Blüte/Vegetativ | 1.0–1.5 | 5.5 | Alle 2 Wochen |
| Okt | Einwintern | 0.0 | — | Letzte Düngung |

### 3.3 Besondere Hinweise zur Düngung

Gardenien sind **pH-Spezialisten** — der pH muss zwingend bei 5.0–6.0 liegen. Normales Leitungswasser (pH 7+) macht Nährstoffe, besonders Eisen, unlöslich. Regenwasser, enthärtetes Wasser oder leicht angesäuertes Wasser ist Pflicht. Chlorotische Blätter (gelb mit grünen Adern) = Eisenmangel durch falschen pH. Rhododendron-Dünger mit Eisenchelat ist erste Wahl.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser ZWINGEND; pH 5.0–6.0; Regenwasser ideal | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (12–15°C), wenig gießen | mittel |
| Feb | Knospenbeobachtung | Temperatur leicht erhöhen, Knospenbildung | mittel |
| Mär | Umtopfen | Bei Bedarf; neues saures Substrat | hoch |
| Apr | Düngung | Rhododendron-Dünger alle 2 Wochen | hoch |
| Jun–Sep | Blüte | Hoch-Luftfeuchte (>60%), regelmäßig gießen | hoch |
| Okt | Rückschnitt + Einwintern | Nach Blüte, kühl stellen | hoch |
| Nov–Dez | Winterruhe | Kühl, hell, minimal gießen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` | <!-- Quelle: Steckbrief-Erweiterung 2026-06: korrigiert von needs_protection → frost_free; frostempfindliche Kübelpflanze, die in Mitteleuropa frostfrei drinnen überwintert wird (winter_action=move_indoors), entspricht laut KA-Enum frost_free, nicht needs_protection. -->
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Weiße Fliege | Trialeurodes vaporariorum | Weiße Fliegen, Honigtau | leaf | alle | easy |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen | stem | alle | difficult |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, Gelbfleckigkeit | leaf | alle | medium |
| Blattläuse | Aphis spp. | Deformierte Triebe | stem | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | dry_leaves, poor_airflow | 5–10 | alle |
| Anthraknose | fungal | Braune Blattränder und -flecken | high_humidity | 7–14 | alle |
| Rußtau | fungal (sekundär) | Schwarzer Belag | Honigtau von Schädlingen | 7–14 | alle |
| Chlorose | physiological | Gelbe Blätter, grüne Adern | wrong_pH, iron_deficiency | — | alle |
| Knospenfall | physiological | Knospen fallen vor dem Öffnen ab | temperature_fluctuation, dry_air, movement | — | flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aphidius colemani | Blattläuse (Aphis spp.) | 0.5–1 | 14–21 |
| Cryptolaemus montrouzieri | Wollläuse (Pseudococcus spp.) | 2–5 | 21–28 |
| Metaphycus helvolus | Weichschildläuse (Coccus hesperidum) | 3–5 | 21–28 |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Wollläuse, Spinnmilben |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Blattläuse, Weiße Fliege |
| Eisendünger | cultural | EDTA-Fe | Gießen | 0 | Chlorose |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Gardenia jasminoides |
|-----|-------------------|-------------|------------------------------|
| Stephanotis | Stephanotis floribunda | Duftblüten | Kletterpflanze, einfacher |
| Jasmin | Jasminum polyanthum | Intensiver Duft | Robuster, schneller wüchsig |
| Kaffeepflanze | Coffea arabica | Gleiche Familie (Rubiaceae) | Dekorativ, einfacher zu pflegen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Gardenia jasminoides,Gardenie;Cape Jasmine,Rubiaceae,Gardenia,perennial,day_neutral,shrub,fibrous,8a;8b;9a;9b;10a;10b;11a;11b,0.0,China Japan Südostasien,yes,10,20,120,120,—,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Gardenia.net – Care Guide](https://www.gardenia.net/guide/learn-how-to-grow-and-care-for-your-gardenia) — Vollständige Pflegeanleitung
2. [UK Houseplants – Gardenia](https://www.ukhouseplants.com/plants/gardenia-jasminoides) — Detaillierter Guide
3. [Clemson HGIC – Gardenia](https://hgic.clemson.edu/factsheet/gardenia/) — University Extension Service
4. [Lubera – Gardenie Pflege](https://www.lubera.com/de/gartenbuch/gardenie-gardenia-jasminoides-pflege-ueberwintern-p3134) — DE Kulturtipps
5. [Pflanzenfreunde – Gardenien](https://www.pflanzenfreunde.com/gardenien.htm) — Schädlinge, Krankheiten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NC State Extension – Gardenia jasminoides Plant Toolbox](https://plants.ces.ncsu.edu/plants/gardenia-jasminoides/) — Standort (Licht: Dappled/Partial/Full Sun), Boden-pH (Acid <6.0), Drainage/Feuchte-Toleranz, flaches faseriges Wurzelsystem, immergrün
7. [University of Florida IFAS – Gardenia jasminoides Fact Sheet (ENH)](https://hort.ifas.ufl.edu/database/documents/pdf/shrub_fact_sheets/garjasa.pdf) — geringe Salztoleranz (sensitive), Standort, Wuchs
8. [RHS – How to grow gardenias](https://www.rhs.org.uk/plants/gardenia/how-to-grow) — Halbschatten, kein tiefer Schatten/keine pralle Sonne, keine Staunässe
9. [New York Botanical Garden – Houseplant Care: Gardenia](https://libguides.nybg.org/Gardenia) — Optimaltemperaturen Tag/Nacht, Nachttemperatur für Knospenansatz, Luftfeuchte >60 %, helles indirektes Licht
10. [UF/IFAS NutDef – Manganese Deficiency in Gardenia jasminoides](https://hort.ifas.ufl.edu/database/nutdef/pic27.shtml) — dokumentierte Mn-Mangel-Anfälligkeit
11. [Hoagland-Nährlösung – Mikronährstoff-Referenzkonzentrationen (Wikipedia / Grokipedia)](https://en.wikipedia.org/wiki/Hoagland_solution) — Standardwerte Mn 0,5 · Zn 0,05 · Cu 0,02 · Mo 0,01–0,05 ppm
12. [Renaissance Garden Guy – How Cold Hardy Are Gardenias](https://renaissancegardenguy.com/how-cold-hardy-are-gardenias-really/) — USDA 8–11, Kälteschäden < ~−7 °C (20 °F), Wachstumsoptimum 18–27 °C
13. [Gardenfine – Average Lifespan of Gardenia](https://www.gardenfine.com/are-gardenia-perennial/) — Lebensdauer mehrere Jahrzehnte (30–50 Jahre)
14. [ISHS Acta Hortic. 515.11 – Flower Initiation in Gardenia as Affected by Photoperiod and Night Temperature](https://ishs.org/ishs-article/515_11/) — Blühinduktion über Nachttemperatur (tagneutral), nicht Photoperiode
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
