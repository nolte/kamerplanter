# Stromanthe Triostar — Stromanthe sanguinea

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/how-to-care-for-stromanthe-triostar/), [Bloomscape](https://bloomscape.com/plant-care-guide/stromanthe/), [UK Houseplants](https://www.ukhouseplants.com/plants/stromanthe), [Plant Care Today](https://plantcaretoday.com/stromanthe-plant-care.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Stromanthe sanguinea | `species.scientific_name` |
| Synonyme | Stromanthe thalia (im Handel gelegentlich) | — |
| Volksnamen (DE/EN) | Stromanthe Triostar, Sanguinea; Triostar Stromanthe, Never Never Plant, Prayer Plant | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Stromanthe | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurz-/Langtag-Trigger --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Reagiert empfindlich auf Kälte und Zugluft. | `species.hardiness_detail` |
| Heimat | Brasilien — tropische Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Cultivargruppe "Triostar" hat dreifarbiges Laub (Weiß, Rosa, Grün — Unterseite leuchtendes Magenta/Rot). Beeindruckend farbig und zeigt wie alle Marantaceen Nyktinastie (Blätter falten sich nachts auf). Ähnliche Pflegeanforderungen wie Calathea/Goeppertia — hohes Luftfeuchtigkeitsbedürfnis, weiches Wasser. Nicht ganz so empfindlich wie Calathea-Arten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (weiß-rote kleine Blüten bei älteren Pflanzen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen im Frühjahr — Rhizomabschnitte mit 2–3 Blättern in feuchtes Substrat. Hohe Luftfeuchtigkeit nach der Teilung wichtig.

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
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no (zu empfindlich) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut drainierte, feuchtigkeitshaltende Erde. pH 6.0–6.5. Mix aus Einheitserde + Perlite (20%) + Kokosfaser (20%). <!-- Quelle: Steckbrief-Erweiterung 2026-06: pH 6.0–6.5 (slightly acidic) harmonisiert --> | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 50 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 100 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt ist aus eng verwandten Marantaceen abgeleitet (Calathea makoyana ≈ 50, C. insignis ≈ 100 µmol/m²/s); Stromanthe sanguinea ist wie diese eine Regenwald-Unterwuchspflanze (understory). Der Lichtsättigungspunkt liegt bei diesen Arten deutlich höher (≈ 400–600 µmol/m²/s); direkte Vollsonne führt zu Blattbleiche/Verbrennung. Salztoleranz: Marantaceen sind ausgesprochen empfindlich gegen Salze, Chlorid, Fluorid und hartes/kalkhaltiges Gießwasser (Blattspitzennekrose) — daher Einstufung `sensitive`; keine belegten Maas-Hoffman-Schwellenwerte (ECe-Bezug) verfügbar.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–250 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–6.5 | 50 | 20 | 0.5 | 0.05 | 0.02 | 0.05 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–6.5 | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06: Mikronährstoffe Mn/Zn/Cu/Mo + pH 6.0–6.5 harmonisiert. Mn `nutrient_profiles.manganese_ppm`, Zn `nutrient_profiles.zinc_ppm`, Cu `nutrient_profiles.copper_ppm`, Mo `nutrient_profiles.molybdenum_ppm` -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich, halbdosiert) | Wachstum |
| Zimmerpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis August, halbe Empfehlungsdosis. September bis März kein Dünger. Weiches Wasser (Regenwasser, gefiltertes Wasser) bevorzugen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser bevorzugt (Regenwasser, gefiltertes Wasser); Substrat gleichmäßig feucht; hohe Luftfeuchtigkeit (Luftbefeuchter, Kieselsteinschale) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (September, vor erster Nachtkühle < 15 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 6 (Juni, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–20 (nie unter 15) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (kein direktes Sonnenlicht) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert, Substrat nur leicht feucht halten | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Stromanthe sanguinea ist nicht frosthart (USDA 10–11) und wird in Mitteleuropa (USDA 6–8) ganzjährig als Zimmerpflanze gehalten bzw. frostfrei drinnen überwintert. Eine Sommer-Aufstellung im Halbschatten draußen ist möglich, erfordert aber zwingend das Einräumen vor Temperaturen unter 15 °C. Im Winterquartier sinken Lichtangebot und Wachstum; trotzdem hohe Luftfeuchtigkeit (50–70 %) sicherstellen, da Heizungsluft Blattspitzennekrose auslöst. Keine Knollen-/Ausgrabe-Einlagerung (kein `dig_and_store`), da rhizombildende, immergrüne Pflanze.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben, braune Ränder | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |
| Blattflecken | fungal | Braune Flecken | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Luftbefeuchter, Kieselsteinschale | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|----------------|--------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 2–10 pro m² (kuratives Niveau bis 20/m²), ggf. wöchentlich wiederholen | 1–3 Wochen |
| Neoseiulus (Amblyseius) cucumeris (Raubmilbe) | Thrips (Frankliniella occidentalis) | 50–100 pro m² bzw. Tütchen (sachets) am Trieb | 2–4 Wochen |
| Cryptolaemus montrouzieri (Australischer Marienkäfer) | Schmierlaus (Pseudococcus spp.) | 5–10 pro m² (bei starkem Befall bis 40/m²), 1–3 Ausbringungen im Abstand von 1–2 Wochen | 3–4 Wochen |

**Hinweis:** Nützlingseinsatz ist für Einzel-Zimmerpflanzen schwierig (offene Wohnumgebung) und eignet sich vor allem für Gewächshaus oder Pflanzenvitrine/-fenster. Raubmilben (Phytoseiulus, cucumeris) benötigen hohe Luftfeuchtigkeit (> 60 %) — bei Stromanthe ohnehin gegeben. Phytoseiulus persimilis ist hochspezialisiert auf Tetranychus urticae und stirbt nach Beutevertilgung aus; Neoseiulus cucumeris kann sich über Pollen länger halten und vorbeugend eingesetzt werden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Goeppertia orbifolia | Goeppertia orbifolia | Marantaceae, Zimmerpflanze | Große runde Blätter, etwas robuster |
| Korbmarante | Goeppertia makoyana | Marantaceae, Zimmerpflanze | Pfauenmuster, Nyktinastie |
| Ctenanthe | Ctenanthe burle-marxii | Marantaceae | Weniger empfindlich |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Stromanthe sanguinea,"Stromanthe Triostar;Sanguinea;Triostar Stromanthe;Never Never Plant",Marantaceae,Stromanthe,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Brasilien (tropische Regenwälder)",yes,2-8,15,40-90,30-60,yes,no,false,light_feeder
```

---

## Quellenverzeichnis

1. [Smart Garden Guide — Stromanthe Triostar](https://smartgardenguide.com/how-to-care-for-stromanthe-triostar/) — Pflegehinweise
2. [Bloomscape — Stromanthe](https://bloomscape.com/plant-care-guide/stromanthe/) — Kulturdaten
3. [UK Houseplants — Stromanthe](https://www.ukhouseplants.com/plants/stromanthe) — Schädlinge, Pflege
4. [Plant Care Today — Stromanthe](https://plantcaretoday.com/stromanthe-plant-care.html) — Botanische Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Biochemical and Physiological Characteristics of Photosynthesis in Plants of Two Calathea Species (PMC5877565)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5877565/) — Lichtkompensations-/Sättigungspunkte verwandter Marantaceen (C. makoyana 50 / C. insignis 100 µmol/m²/s), Schattenpflanzen-Physiologie
7. [Soltech — Stromanthe Triostar Plant Care](https://soltech.com/products/stromanthe-triostar-care) — Boden-pH (slightly acidic), bright indirect light, keine Staunässe, Mindesttemperatur 15 °C
8. [Greg — Triostar Stromanthe Winter Care](https://greg.app/triostar-stromanthe-winter-care/) — Überwinterung, Mindesttemperatur 15 °C, Winter-Luftfeuchtigkeit
9. [Healthy Houseplants — Stromanthe Triostar Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/stromanthe-triostar-care-guide-tips-for-growing-this-colorful-tropical-plant/) — Boden-pH 6.0–6.5, Standortbedingungen
10. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Nützling gegen Spinnmilben, Ausbringrate
11. [Koppert — Neoseiulus (Amblyseius) cucumeris](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/neoseiulus-cucumeris/) — Nützling gegen Thrips, Ausbringrate
12. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Schmierläuse, Ausbringrate
13. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringraten Raubmilbe (University Extension)
14. [Marantaceae — Wikipedia](https://en.wikipedia.org/wiki/Marantaceae) — Familie als tropische C3-Unterwuchsstauden (understory)
15. [All Things Lighting — Far-Red Lighting and the Phytochromes](https://www.allthingslighting.org/far-red-lighting-and-the-phytochromes/) — R:FR-Verhältnis Sonne (≈1.3) vs. Unterwuchs/Schatten (≤0.4), Grundlage Far-Red-Fraction
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
