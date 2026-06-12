# Brautstrauch (Madagaskarjasmin) — Stephanotis floribunda

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Balcony Garden – Stephanotis](https://thebalconygarden.co/blogs/news/caring-for-madagascar-jasmine), [Greg App – Stephanotis](https://greg.app/plant-care/stephanotis-floribunda), [Weekand – Stephanotis Care](https://www.weekand.com/home-garden/article/care-stephanotis-18054398.php), [Pflanzenfreunde – Stephanotis](https://www.pflanzenfreunde.com/stephanotis.htm)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Stephanotis floribunda | `species.scientific_name` |
| Volksnamen (DE/EN) | Brautstrauch, Madagaskarjasmin; Madagascar Jasmine, Bridal Wreath, Wax Flower | `species.common_names` |
| Familie | Apocynaceae | `species.family` → `botanical_families.name` |
| Gattung | Stephanotis | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- KORREKTUR: vormals short_day. S. floribunda ist photoperiodisch weitgehend tagneutral; dominanter Blühinduktionsfaktor sind kühle Nächte (~13–16 °C) im Winter, nicht die Tageslänge. Eine klassische Langtag-Einstufung mit kritischer Tageslänge ist nicht belegt. --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostfrei; Temperaturen unter 12°C hemmen Wachstum dauerhaft | `species.hardiness_detail` |
| Heimat | Madagaskar | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für S. floribunda auffindbar; Wachstum stagniert unter ~12–13 °C, aber das ist keine quellenbelegte GDD-Basis --> | `species.base_temp` |
| Lebensdauer (Jahre) | <!-- DATEN FEHLEN: Quellen beschreiben langlebige, mehrjährige Liane ("long-term plant"), nennen aber keinen belegten Jahreswert --> | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN --> (tagneutral; Blühinduktion temperaturgesteuert über kühle Nächte, keine belegte photoperiodische Schwelle) | `lifecycle_configs.critical_day_length_hours` |
<!-- Hinweis: S. floribunda ist Langtagblüher; Blüteninduktion ab ~14 h Photoperiode (oder 4 h Nachtunterbrechung). Der erforderliche 8–10-wöchige kühle Ruheabschnitt (cool rest, ~13–16 °C Nacht) ist eine kühletemperatur-gesteuerte Dormanz/Induktion, KEINE echte Vernalisation (kein Kältereiz <10 °C nötig) → dormancy_required=true, vernalization_required=false. Quellen: ourhouseplants, lifetips/Alibaba, Davis Floral Stephanotis Vine. -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (weiße, duftende Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Alkaloide (Milchsaft) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft kann Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10 (nach Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–500 (Kletterpflanze) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gut drainierte, nährstoffreiche Zimmerpflanzenerde; keine Staunässe; Rankgitter oder Drahtrahmen; Topf NICHT umstellen (Knospenfall!) | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifisch gemessener Kompensationspunkt (light compensation point) für S. floribunda in seriösen Quellen auffindbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: Quellen beschreiben flaches, feines, brüchiges Wurzelwerk und kleinen Topfbedarf, nennen aber keine belegte Wurzeltiefe in cm --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | <!-- DATEN FEHLEN: keine seriöse Salztoleranz-Einstufung für S. floribunda auffindbar --> | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-a-Wert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-b-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

<!--
Begründungen Sektion 1.7:
- shade_tolerance=partial_shade: helles, indirektes/gefiltertes Licht; in Madagaskar als Halbschatten unter lichtem Küstenwald-Kronendach; RHS "Full sun" gilt für Kultur unter Glas mit Schattierung vor heißer Sonne. Kein Tiefschatten (deep_shade) tolerierend ("not the plant for a shady/low light location"). Quellen: ourhouseplants, RHS, gardenia.
- waterlogging_tolerance=sensitive: Staunässe verursacht zuverlässig Wurzelfäule; Pflanze soll zwischen Wassergaben antrocknen. Quellen: yourflowersguide, plantgrowerworld, jardineriaon.
- soil_ph_preference 5.5–6.5: leicht sauer bis neutral; mit pH-Angaben in §2.3 (6.0–6.5) harmonisiert. RHS nennt zusätzlich Alkali-Toleranz (acid/neutral/alkaline), die dominante Kultur-Empfehlung ist jedoch leicht sauer (5.5–6.5). Quellen: lifetips/Alibaba (5.5–6.5), RHS, gardenia.
-->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | medium |
| Knospenbildung | 30–60 | 2 | false | false | low |
| Blüte | 60–90 | 3 | false | false | low |
| Vegetativ (Sommer/Herbst) | 90–120 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.1 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Winterruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — | — |
| Knospenbildung | 1:2:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | — | 2 | DF | DF | DF | DF |
| Blüte | 1:2:3 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 | DF | DF | DF | DF |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 | DF | DF | DF | DF |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Mikronährstoffe Mn/Zn/Cu/Mo (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`): DF = DATEN FEHLEN. Für S. floribunda sind keine art-spezifischen, quellenbelegten Mn/Zn/Cu/Mo-Sollwerte je Phase auffindbar. Generische Hydroponik-/Hoagland-Richtwerte wurden bewusst NICHT als art-spezifische Werte eingetragen (keine Halluzination). -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Knospenbildung | time_based | — | Frühjahr, Temperaturanstieg |
| Knospenbildung → Blüte | time_based | 30–60 Tage | Knospen deutlich sichtbar — Topf NICHT mehr bewegen! |
| Blüte → Vegetativ | time_based | 60–90 Tage | Blüten verblüht |
| Vegetativ → Winterruhe | time_based | 90–120 Tage | Herbst, Temperaturabfall |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Compo | base | 4-6-8 | 5 ml/L | 1 | knospenbildung, blüte |
| Zimmerpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | — | organisch | 30 g/Topf | Frühjahr | medium_feeder |
| Langzeitdünger | Osmocote | organisch/langsam | 5 g/L Substrat | Apr–Jun | medium_feeder |

### 3.2 Besondere Hinweise zur Düngung

**Kritischer Hinweis:** Stephanotis floribunda reagiert extrem empfindlich auf Standortveränderungen — bei der Knospenbildung und während der Blüte den Topf NICHT drehen oder umstellen, da dies Knospenfall auslöst! Auch Zugluft und Temperaturschwankungen während der Blüte vermeiden. Die Überwinterung bei 12–15°C ist der Schlüssel für reichliche Blütenbildung im Folgejahr.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser bevorzugt; zimmertemperiert | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (12–15°C), wenig gießen, heller Standort | hoch |
| Feb | Knospenbeobachtung | Temperaturen erhöhen, Knospen erscheinen | mittel |
| Mär | Vorsichtige Pflege | Topf NICHT bewegen, Knospenfall vermeiden | hoch |
| Apr | Düngung | Erste Düngergabe, Licht sichern | hoch |
| Mai–Aug | Blütezeit | Regelmäßig gießen, nicht umstellen | hoch |
| Sep | Rückschnitt | Nach Blüte, Triebe um 1/3 kürzen | mittel |
| Okt | Einwintern | Kühl stellen (12–15°C) | hoch |
| Nov–Dez | Winterruhe | Minimal gießen, kein Dünger | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 12 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 16 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schildläuse | Coccus hesperidum | Braune Schuppen, klebrige Blätter | stem | alle | difficult |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Spinnmilben | Tetranychus urticae | Gespinste, gelbe Blattflecken | leaf | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Knospenfall | physiological | Knospen fallen vor dem Öffnen ab | movement, draft, temperature_change | — | flowering |
| Wurzelfäule | fungal | Welke Pflanze | overwatering | 7–14 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Cryptolaemus montrouzieri | Wollläuse, Schildläuse | 1–2/Pflanze | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Schildläuse, Spinnmilben |
| Alkohol | mechanical | Isopropanol 70% | Wattestäbchen | 0 | Schildläuse, Wollläuse |

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

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Stephanotis floribunda |
|-----|-------------------|-------------|------------------------------|
| Pink Jasmin | Jasminum polyanthum | Kletterpflanze, duftend | Robuster, einfacher zu pflegen |
| Hoya | Hoya carnosa | Gleiche Familie, Wachsblumen | Pflegeleichter, toleranter |
| Gardenie | Gardenia jasminoides | Intensiver Duft | Kein Kletterer, kompakter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Stephanotis floribunda,Brautstrauch;Madagaskarjasmin;Madagascar Jasmine,Apocynaceae,Stephanotis,perennial,long_day,vine,fibrous,10a;10b;11a;11b,0.0,Madagaskar,yes,10,20,500,200,—,yes,limited,true,true
```

---

## Quellenverzeichnis

1. [Balcony Garden – Stephanotis Care](https://thebalconygarden.co/blogs/news/caring-for-madagascar-jasmine) — Pflegeanleitung
2. [Greg App – Stephanotis floribunda](https://greg.app/plant-care/stephanotis-floribunda) — Care Data
3. [Weekand – How to Care for Stephanotis](https://www.weekand.com/home-garden/article/care-stephanotis-18054398.php) — Kulturtipps
4. [Pflanzenfreunde – Stephanotis](https://www.pflanzenfreunde.com/stephanotis.htm) — DE Anleitung
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS – Stephanotis floribunda (bridal wreath)](https://www.rhs.org.uk/plants/17784/stephanotis-floribunda/details) — Boden-pH (acid/neutral/alkaline), Sonnenlage, Drainage, Hardiness H1B (10–15 °C)
6. [ourhouseplants – Stephanotis floribunda Guide](https://www.ourhouseplants.com/plants/stephanotis-floribunda) — Lichtbedarf, Schattenintoleranz, Winterruhe-Temperatur, Mindesttemperatur
7. [lifetips/Alibaba – Stephanotis floribunda Care: Grow & Bloom](https://lifetips.alibaba.com/plant-care/stephanotis-floribunda) — Langtag-Induktion (~14 h / Nachtunterbrechung), kühle Ruhephase (8–10 Wochen), pH 5.5–6.5
8. [Davis Floral Company – Stephanotis Vine (NCSU Hortscans, PDF)](https://hortscans.ces.ncsu.edu/uploads/s/t/stephano_51e40f167cb7b.pdf) — kommerzielle Kultur, Photoperiode/Nachtunterbrechung, Temperatur
9. [yourflowersguide – Stephanotis Plant Care & Growing Guide](https://yourflowersguide.com/stephanotis/) — Staunässe-/Wurzelfäule-Empfindlichkeit, Drainage
10. [Gardenia.net – Madagascar Jasmine (Stephanotis floribunda)](https://www.gardenia.net/plant/stephanotis-floribunda-madagascar-jasmine-grow-care-guide) — leicht saurer bis neutraler Boden, helles indirektes Licht
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
