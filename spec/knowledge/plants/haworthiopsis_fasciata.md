# Zebra-Hauswurz — Haworthiopsis fasciata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Joy Us Garden](https://www.joyusgarden.com/zebra-succulent-care-a-beginners-haworthia-growing-guide/), [NC State Extension](https://plants.ces.ncsu.edu/plants/haworthiopsis-fasciata/), [Epic Gardening](https://www.epicgardening.com/haworthiopsis-fasciata/), [Succulents and Sunshine](https://www.succulentsandsunshine.com/types-of-succulents/haworthia-fasciata-zebra-plant/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Haworthiopsis fasciata | `species.scientific_name` |
| Synonyme | Haworthia fasciata (älterer, noch gebräuchlicher Name) | — |
| Volksnamen (DE/EN) | Zebra-Hauswurz, Zebra-Haworthia; Zebra Plant, Zebra Cactus, Zebra Haworthia | `species.common_names` |
| Familie | Asphodelaceae | `species.family` → `botanical_families.name` |
| Gattung | Haworthiopsis | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchsphase (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Haworthiopsis auffindbar --> | `species.base_temp` |
| Kritische Tageslänge (critical day length, h) | day_neutral (tagneutrale CAM-Sukkulente, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
<!-- Quelle: growing-phase-auditor 2026-07-03 — korrigiert von half_hardy auf tender: RHS-Hardiness-Rating H2 ("tolerant of low temperatures, but not surviving being frozen, 1–5°C"), NC State Extension ("not frost-tolerant"), Epic Gardening/GardenBeast/Joy Us Garden/Succulents and Sunshine (übereinstimmend: unter 30–40°F/-1 bis +4°C zwingend ins Haus holen, kein dauerhafter Freilandverbleib) — konsistent mit §4.3 hardiness_rating=frost_free/winter_action=move_indoors (siehe REQ-022 Beispiel "Zitrone im Kübel (tender) → move_indoors") -->
| Winterhaerte-Detail | Frostempfindlich (tender) — verträgt keinen dauerhaften Frost; kurzzeitig knapp unter 0°C (bis -1°C) im trockenen Zustand kompensierbar, danach Schäden. Mindesttemperatur 5°C dauerhaft, optimal 15–27°C. Bei Nässe deutlich frostempfindlicher. | `species.hardiness_detail` |
| Heimat | Südafrika (Ostkap-Provinz) — Felsen und Buschland | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Haworthiopsis fasciata ist eine der schattenverträglichsten Sukkulenten — ideal für Windowsills ohne direkte Mittagssonne. Verwechslungsgefahr mit Haworthia attenuata (ebenfalls als "Zebra-Haworthia" gehandelt) — bei H. fasciata sind die weißen Querstreifen glatter und punktförmig auf der Blattunterseite, bei H. attenuata sind sie rauer und auch auf der Blattoberseite. Sehr geeignet für Anfänger.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6 (weiß-rosa Röhrenblüten auf langen Stängeln) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) entstehen spontan an der Basis. Bei 4–5 cm Größe abtrennen, 1–2 Tage Schnittstelle trocknen lassen, in trockenes Kakteensubstrat pflanzen. Bewurzelung in 3–5 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
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
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–20 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–20 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde mit 30% Perlite. pH 6.5–7.5. Sehr gute Drainage. Flache Schalen bevorzugt. | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifisch gemessener LCP für Haworthiopsis aus zwei seriösen Quellen --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifisch gemessener LCP für Haworthiopsis aus zwei seriösen Quellen --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 5–12 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (ECe) für Haworthiopsis --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope für Haworthiopsis --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.5 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis (Steckbrief-Erweiterung 2026-06):** Haworthiopsis fasciata ist eine der schattenverträglichsten Sukkulenten (partial_shade) und gedeiht im natürlichen Habitat halbschattig unter größeren Pflanzen; direkte Mittagssonne führt zu Stressfärbung (rot/weiß). Als CAM-Sukkulente und ausgesprochener Schwachzehrer (light_feeder) reagiert sie empfindlich auf Bodenversalzung (sensitive): Salzanreicherung aus Überdüngung schädigt die Wurzeln und ist eine häufige Pflegefehler-Ursache. Flach-faserige Wurzeln in flachen Schalen; Staunässe wird nicht toleriert (sensitive). Der pH-Vorzug 6.0–7.5 (leicht sauer bis neutral) harmonisiert mit den pH-Angaben in §1.6 und §2.3.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Herbst) | 180–210 | 1 | false | false | very high |
| Sommer-Dormanz / Winterruhe | 90–120 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–Mai, September–November)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (VPD threshold, kPa) | 2.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (halbschattiger Naturstandort unter größeren Pflanzen; offenes Tageslicht ≈ 0.5, Unterwuchs höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sommer-Dormanz/Winterruhe (Juni–August, Dezember–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (VPD threshold, kPa) | 2.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (halbschattiger Naturstandort unter größeren Pflanzen; offenes Tageslicht ≈ 0.5, Unterwuchs höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.5–7.5 | 30 | 10 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Dormanz/Ruhe | 0:0:0 | 0.0 | 6.5–7.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Steckbrief-Erweiterung 2026-06):** Für die Mikronährstoffe Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) liegen keine art-spezifisch belegten ppm-Zielwerte für Haworthiopsis fasciata aus mindestens zwei seriösen Quellen vor; als ausgesprochener Schwachzehrer (light_feeder) wird die Pflanze mit stark verdünnter Lösung (EC 0.3–0.6 mS, ca. 1/4-Stärke) versorgt, in der Mikronährstoffe entsprechend im Spurenbereich liegen. Werte daher als DATEN FEHLEN markiert, um Halluzinationen zu vermeiden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (1–2×/Saison) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Extrem leichter Zehrer. Nur 1–2 Düngergaben pro Jahr im Frühjahr ausreichend. Kein Dünger im Sommer (Dormanz) und Winter. Überdüngung ist die häufigste Pflegefehler-Ursache.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 21–28 (Sommer = Halbdormanz) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; vollständig abtrocknen lassen vor nächstem Gießen; nicht auf die Blätter gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–5, 9–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (nach Eisheiligen, frostfreie Nächte) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–15 (Minimum 5; für Blühinduktion kühl 7–10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (helles Fensterbrett, Ost/West) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam (alle 4–6 Wochen, fast trocken halten) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis (Steckbrief-Erweiterung 2026-06):** Frostempfindliche immergrüne Kübel-/Zimmerpflanze, die frostfrei drinnen überwintert (frost_free). Toleriert kurzfristig -1 °C trocken, Dauer-Minimum 5 °C; daher im Freiland/Balkon vor dem ersten Frost (ca. Oktober in Mitteleuropa, USDA 6–8) ins Haus holen und nach den Eisheiligen (Mitte Mai) wieder hinausstellen. Kühle (7–10 °C), helle und trockene Überwinterung fördert die Frühjahrsblüte.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Weiche, braune Basis, Pflanze löst sich | Überwässerung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Intervall verlängern | 0 | Wurzelfäule (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse |

### 5.4 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 5–20 Käfer/m² (Erhaltung ab 1/m²), 2–3 Freilassungen im Abstand von 1–2 Wochen | 2–4 Wochen |
| Schlupfwespe (parasitoid) | Leptomastix dactylopii | Schmierläuse (Pseudococcus / Planococcus) | 2–5 Wespen/m², wiederholt bei 25–30 °C | 2–3 Wochen |
| Insektenpathogene Nematoden (entomopathogenic nematodes) | Steinernema feltiae | Trauermücken-Larven (Bradysia spp.) | ca. 0.5 Mio. Infektiosjuvenile/m² (50 Mio./100 m²), Substrat feucht halten | 1–2 Wochen |
| Raubmilbe (predatory mite) | Stratiolaelaps scimitus (syn. Hypoaspis miles) | Trauermücken-Larven (Bradysia spp.) | ca. 100–250 Milben/m² als Präventiv-Ausbringung in feuchtes Substrat | 2–3 Wochen |

**Hinweis (Steckbrief-Erweiterung 2026-06):** Nützling-Wirt-Zuordnung gemäß Biocontrol-Praxis: Cryptolaemus montrouzieri und Leptomastix dactylopii gegen Schmierläuse (Pseudococcus, Weichschädlinge), Steinernema feltiae und Stratiolaelaps scimitus gegen Trauermücken-Larven im Substrat. Ausbringraten variieren je nach Befallsdichte und Temperatur; bei Zimmerkultur reichen erhaltende Mengen am unteren Bereichsende. Substrat-Feuchtebedarf der Nematoden/Raubmilben mit der Trockenkultur der Sukkulente abstimmen (Ausbringung nach Gießgang).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Rauhe Haworthia | Haworthiopsis attenuata | Gleiche Gattung | Ähnliche Pflege, rauere Querstreifen |
| Aloe vera | Aloe vera | Gleiche Familie | Größer, medizinische Nutzung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Haworthiopsis fasciata,"Zebra-Hauswurz;Zebra-Haworthia;Zebra Plant;Zebra Cactus",Asphodelaceae,Haworthiopsis,perennial,day_neutral,herb,fibrous,"9b;10a;10b;11a;11b","Südafrika (Ostkap-Provinz)",yes,0.5-2,8,10-20,10-20,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Joy Us Garden — Zebra Succulent](https://www.joyusgarden.com/zebra-succulent-care-a-beginners-haworthia-growing-guide/) — Pflegehinweise
2. [NC State Extension — Haworthiopsis fasciata](https://plants.ces.ncsu.edu/plants/haworthiopsis-fasciata/) — Botanische Daten
3. [Epic Gardening — Haworthiopsis fasciata](https://www.epicgardening.com/haworthiopsis-fasciata/) — Kulturdaten
4. [Succulents and Sunshine — Haworthia fasciata](https://www.succulentsandsunshine.com/types-of-succulents/haworthia-fasciata-zebra-plant/) — Artunterschiede
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Wikipedia — Crassulacean acid metabolism (CAM)](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Photosynthese, Familien mit CAM (inkl. Liliaceae/Asphodelaceae-Sukkulenten)
7. [PMC — The genome sequence of Aloe vera reveals adaptive evolution of drought tolerance mechanisms](https://pmc.ncbi.nlm.nih.gov/articles/PMC7889978/) — CAM in Asphodelaceae (Aloe/Haworthia), PEPC/Malatenzym
8. [Springer/Planta — Crassulacean acid metabolism (CAM) in leaves of Aloe arborescens](https://link.springer.com/article/10.1007/BF00388361) — Nachweis CAM (Malatschwankung) bei Asphodelaceae
9. [NC State Extension — Haworthiopsis fasciata (Plant Toolbox)](https://plants.ces.ncsu.edu/plants/haworthiopsis-fasciata/) — Schatten-/Lichttoleranz (partial shade), Boden-pH-Spanne, Drainage, Reifegröße
10. [GardenBeast — Haworthiopsis Fasciata Guide](https://gardenbeast.com/haworthiopsis-fasciata-guide/) — Lichtbedarf (bright indirect, Halbschatten), Minimumtemperatur, Überwinterung
11. [Gardenia.net — Zebra Plant (Haworthiopsis fasciata)](https://www.gardenia.net/plant/haworthiopsis-fasciata) — Frosthärte, Überwinterung (frostfrei, < -1 °C ins Haus), kühle Blühinduktion
12. [Morgan Lawn & Landscape — Best Soil for Haworthia](https://morganlawnandlandscape.com/best-soil-for-haworthia/) — Boden-pH-Vorzug (leicht sauer bis neutral), Drainage/Inorganik-Anteil
13. [Healthy Houseplants — Haworthia Plant Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/haworthia-plant-care-guide-grow-these-charming-succulents/) — Salzempfindlichkeit (Schwachzehrer, Salzanreicherung schädigt Wurzeln)
14. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Schmierläuse, Ausbringrate/Wiederholung
15. [Bugs for Growers — Biocontrol of fungus gnats (S. feltiae, Stratiolaelaps)](https://blog.bugsforgrowers.com/natural-predators/entomopathogenic-nematodes/beneficial-nematodes/two-biocontrol-agents-for-effective-control-of-fungus-gnats/) — Nematoden/Raubmilben gegen Trauermücken, Ausbringraten
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07-03 -->
16. [RHS — Haworthiopsis fasciata](https://www.rhs.org.uk/plants/504897/haworthiopsis-fasciata/details) — Hardiness-Rating H2 ("tolerant of low temperatures, but not surviving being frozen, 1–5°C"), Blütezeit Sommer
17. [Joy Us Garden — Zebra Succulent](https://www.joyusgarden.com/zebra-succulent-care-a-beginners-haworthia-growing-guide/) — Frostgrenze 40°F, Blütezeit "late spring to early summer" (bestätigt Frostempfindlichkeit; Blütezeit-Angabe widerspricht z.T. anderen Quellen, siehe Report)
<!-- /Quelle: growing-phase-auditor 2026-07-03 -->
