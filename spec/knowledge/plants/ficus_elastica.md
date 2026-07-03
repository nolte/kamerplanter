# Gummibaum — Ficus elastica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/how-to-care-for-a-rubber-plant-ficus-elastica/), [Joy Us Garden](https://www.joyusgarden.com/rubber-plant-growing-tips/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/rubber-plant-ficus-elastica-care-guide/), [Old Farmer's Almanac](https://www.almanac.com/plant/rubber-tree-plant-ficus-elastica-care-guide), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ficus elastica | `species.scientific_name` |
| Volksnamen (DE/EN) | Gummibaum, Kautschukbaum; Rubber Plant, Rubber Tree | `species.common_names` |
| Familie | Moraceae | `species.family` → `botanical_families.name` |
| Gattung | Ficus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> keine publizierte Wuchs-GDD-Basis für F. elastica; Mindesttemperatur 10 °C ist kein GDD-Basiswert | `species.base_temp` |
| Kritische Tageslänge (h) | Entfällt (tagneutral / day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 25–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 15–29°C. Deutlich robuster als F. benjamina und F. lyrata. | `species.hardiness_detail` |
| Heimat | Indien, Nepal, Myanmar, Südchina, Malaysia — tropische Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.7 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, trichloroethylene, benzene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Gummibaum ist robuster und verzeihender als seine Verwandten Ficus benjamina und F. lyrata. Er toleriert niedrigere Lichtverhältnisse, Standortwechsel und gelegentliches Vergessen beim Gießen besser. Die großen, glänzenden Blätter der Sorte 'Robusta' (dunkelgrün) und 'Burgundy' (fast schwarzrot) sind besonders dekorativ. NASA Clean Air Study bestätigte gute Luftreinigungseigenschaften.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nur in natürlichem Habitat) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (10–15 cm) bei 22–26°C und 80%+ Luftfeuchtigkeit bewurzeln. Schnittstelle kurz trocknen lassen (Milchsaft). Mit Plastikbeutel abdecken. Bewurzelung in 4–8 Wochen. Abmoosen (Luftabsenker) für dickere Stämme.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap (Milchsaft) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | ficin, ficusin, latex_sap | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Latex-Allergie Kreuzreaktion möglich — Handschuhe beim Schneiden!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4, 5 | `species.pruning_months` |

**Hinweis:** Verträgt Rückschnitt gut. Topping fördert Verzweigung. Schnittstellen mit Aktivkohle behandeln (Milchsausfluß). Im Frühjahr schneiden wenn die Pflanze aktiv wächst.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–300 (Indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer, frostfreie Monate, Halbschatten bis Sonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Qualitätserde mit 20% Perlite. pH 6.0–7.0. Gute Drainage wichtig. Schwere Erde vermeiden. | — |

### 1.7 Umgebungs-Physiologie & Standortqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–60 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> keine Maas-Hoffman-Schwelle für F. elastica publiziert | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein Maas-Hoffman-Slope publiziert | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Als Regenwald-Understory-Art (Unterwuchs) ist *Ficus elastica* schattenverträglich (shade-tolerant), gedeiht aber auch in hellem indirektem Licht bis lichtem Halbschatten — daher Einstufung `partial_shade` (PFAF: „semi-shade to no shade"). Der Lichtkompensationspunkt liegt im für schattentolerante Gehölze typischen Bereich von 10–50 µmol/m²/s (Craine & Reich 2005; Sterck et al. 2013); für *F. elastica* konservativ mit 10–25 µmol/m²/s angesetzt. Der Lichtsättigungspunkt (deutlich höher, mit Photoinhibition ab ≥ 400 µmol/m²/s laut MDPI-Lichtstress-Studie) gehört NICHT in das Kompensationspunkt-Feld. Staunässe-Empfindlichkeit ist hoch (Wurzelfäule-Risiko); die Salztoleranz ist allenfalls mäßig — Blattrand-Nekrosen durch Salzakkumulation aus Leitungswasser/Dünger sind dokumentiert, das Substrat sollte periodisch durchgespült werden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 6–12 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 35–55 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–7.0 | 100 | 40 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Mikronährstoff-Sollwerte (Mn/Zn/Cu/Mo) folgen der Hoagland-Standardrezeptur für Topf-/Zimmerpflanzen-Nährlösungen; keine F.-elastica-spezifischen Messwerte publiziert. Eisenmangel (interveinale Chlorose) tritt bei pH > 7.0 auf — daher pH-Korridor 6.0–7.0 einhalten. -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Bokashi | Eigenherstellen | organisch | 10% Substratanteil | Frühjahr |

### 3.2 Besondere Hinweise

Monatlich März bis Oktober düngen. November bis Februar: kein Dünger. Blätter reinigen (Staubtücher) — verstopfte Stomata hemmen Photosynthese und Luftreinigung. Stickstoffbetonte Formel für glänzendes, großes Laub.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; erste 2–5 cm Erde trocknen lassen vor nächstem Gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

*Ficus elastica* ist frostempfindlich (tender) und überwintert in Mitteleuropa (USDA 6–8) frostfrei im Innenraum. Im Sommer als Kübelpflanze ins Freie (Balkon/Terrasse, Halbschatten) zulässig, muss aber rechtzeitig vor dem ersten Frost wieder hereingeholt werden.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (min. 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; ggf. Pflanzenlampe | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert (Substrat antrocknen lassen) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Beim Hereinholen vor dem Frost an Halbschatten gewöhnen; abrupter Standortwechsel kann Blattfall auslösen. Im Winterquartier nicht düngen (vgl. §3.2). Beim Ausräumen im Frühjahr schrittweise an direkteres Licht abhärten (harden off), sonst Sonnenbrand auf den Blättern.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau, Rußtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, Blattverlust | Staunässe |
| Rußtau (Sekundär) | fungal | Schwarzer Belag auf Honigtau | Saugende Insekten |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |
| Insektizidseife | biological | Sprühen | 3 Tage | Weiße Fliege, Blattläuse |

### 5.4 Nützlinge (Biologische Bekämpfung)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 10–30 /m² | 2–3 Wochen |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 5–10 /m² | 3–4 Wochen |
| Schlupfwespe | Metaphycus helvolus | Weichschildlaus (Coccus hesperidum) | 5 /m², 3× im 14-Tage-Takt | 3–4 Wochen |
| Schlupfwespe | Encarsia formosa | Weiße Fliege (Trialeurodes vaporariorum) | 1–3 /m² (wöchentl. wdh.) | 2–4 Wochen |

**Hinweis:** Nützlingseinsatz ist v. a. im Gewächshaus/Wintergarten bei stabiler Luftfeuchte (> 60 %) erfolgreich; im trockenen Wohnraum etablieren sich die meisten Antagonisten schlecht. *Metaphycus helvolus* zielt auf Weichschildläuse (Coccidae, z. B. *Coccus hesperidum* aus §5.1) — NICHT auf Panzer-/Deckelschildläuse (dafür wären *Aphytis*-Arten zuständig). Vor Nützlingsausbringung keine Breitband-Insektizide einsetzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Geigenfeige | Ficus lyrata | Gleiche Gattung | Spektakulärere Blätter |
| Birkenfeige | Ficus benjamina | Gleiche Gattung | Kleiner, feiner Wuchs |
| Drachenbaum | Dracaena marginata | Großer Baum, tropisch | Noch pflegeleichter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Ficus elastica,"Gummibaum;Kautschukbaum;Rubber Plant;Rubber Tree",Moraceae,Ficus,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Indien, Nepal, Myanmar, Südchina, Malaysia",yes,10-30,30,100-300,60-150,yes,yes,false,medium_feeder,0.7
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Robusta,Ficus elastica,"ornamental;dark_green;large_leaves",clone
Burgundy,Ficus elastica,"ornamental;dark_red;almost_black",clone
Tineke,Ficus elastica,"ornamental;variegated;cream_green_pink",clone
Ruby,Ficus elastica,"ornamental;variegated;red_pink_white",clone
Doescheri,Ficus elastica,"ornamental;variegated;gray_cream",clone
```

---

## Quellenverzeichnis

1. [Smart Garden Guide — Ficus elastica](https://smartgardenguide.com/how-to-care-for-a-rubber-plant-ficus-elastica/) — Detaillierte Pflegehinweise
2. [Joy Us Garden — Rubber Plant](https://www.joyusgarden.com/rubber-plant-growing-tips/) — Kulturdaten, Sorten
3. [Healthy Houseplants — Ficus elastica](https://www.healthyhouseplants.com/indoor-houseplants/rubber-plant-ficus-elastica-care-guide/) — Schädlinge, Krankheiten
4. [Old Farmer's Almanac — Rubber Tree Plant](https://www.almanac.com/plant/rubber-tree-plant-ficus-elastica-care-guide) — Pflegehinweise
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [PFAF — Ficus elastica Plant Database](https://pfaf.org/user/Plant.aspx?LatinName=ficus+elastica) — Boden-pH (5.5–7.5), Bodentypen, Schatten-/Sonnentoleranz (semi-shade to no shade)
7. [UF/IFAS Fact Sheet ST-252 — Ficus elastica](https://hort.ifas.ufl.edu/database/documents/pdf/tree_fact_sheets/ficelaa.pdf) — Standort-/Licht-/Salztoleranz-Angaben, Wurzelsystem
8. [Healthy Houseplants — Ficus elastica Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/rubber-plant-ficus-elastica-care-guide/) — Boden-pH 6.0–6.5, Salzakkumulation/Spülen, Staunässe-Empfindlichkeit
9. [Greg — Best Soil for Rubber Plant](https://greg.app/rubber-plant-soil/) — pH-Vorzug 6.0–6.5, interveinale Chlorose (Eisenmangel) bei pH > 7.0
10. [MDPI AgriEngineering 6(3):188 — Light Stress Detection in Ficus elastica](https://www.mdpi.com/2624-7402/6/3/188) — schattentolerant, Lichtstress/Photoinhibition ab ≥ 400 µmol/m²/s
11. [Craine & Reich (2005), New Phytologist — Leaf-level light compensation points in shade-tolerant woody seedlings](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2005.01420.x) — LCP-Bereich schattentoleranter Gehölze (10–50 µmol/m²/s)
12. [Sterck et al. (2013), Journal of Ecology — Plasticity influencing the light compensation point in a tropical forest understorey](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — LCP tropischer Understory-Arten
13. [Zhen & Bugbee (2022), New Phytologist — Photosynthesis in sun and shade: the importance of far-red photons](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.18375) — Far-Red-Anteil: Vegetationsschatten > 50 % der Photonen, Bezugsgröße FR/(R+FR)
14. [Crous et al. (2022), New Phytologist — Temperature responses of photosynthesis in evergreen trees](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.17951) — T_opt tropischer C3-Bäume (16–32 °C, typ. 25–30 °C)
15. [Koppert — Cryptolaemus montrouzieri (Schmierlaus-Räuber)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate Schmierläuse
16. [Koppert — Phytoseiulus persimilis (Spinnmilben-Räuber)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Spinnmilben-Bekämpfung
17. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate 10–30 /m²
18. [University of Hertfordshire AERU — Metaphycus helvolus](https://sitem.herts.ac.uk/aeru/bpdb/Reports/2258.htm) — Weichschildlaus-Wirt (Coccus hesperidum), Rate 5 /m², 3 Freilassungen
19. [Applied Bio-nomics — Encarsia formosa](https://appliedbio-nomics.com/product/encarsia-formosa/) — Weiße-Fliege-Parasitoid, Ausbringrate
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
