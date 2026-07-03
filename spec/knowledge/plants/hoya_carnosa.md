# Wachsblume — Hoya carnosa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NCSU Plant Toolbox](https://plants.ces.ncsu.edu/plants/hoya-carnosa/), [Gardenia.net](https://www.gardenia.net/plant/hoya-carnosa-wax-plant-all-you-need-to-know), [Planet Natural](https://www.planetnatural.com/hoya-carnosa/), [Epic Gardening](https://www.epicgardening.com/hoya-plant/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/hoya-carnosa-a-comprehensive-guide/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hoya carnosa | `species.scientific_name` |
| Volksnamen (DE/EN) | Wachsblume, Porzellanblume; Wax Plant, Honey Plant, Porcelain Flower | `species.common_names` |
| Familie | Apocynaceae | `species.family` → `botanical_families.name` |
| Gattung | Hoya | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 20–40+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage (vernalization min days) | — (keine Vernalisation; tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN — kein belegter Wuchs-/Phänologie-GDD-Basiswert für Hoya carnosa auffindbar; nicht aus Keim-/Mindesttemperatur ableiten --> | `species.base_temp` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN — tagneutral (day_neutral), kein Kurztag-/Langtag-Schwellenwert; siehe photoperiod_type --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–24°C. Kurze Kühle im Winter (12–15°C nachts) kann Blütenbildung fördern. | `species.hardiness_detail` |
| Heimat | Ostasien (China, Indien, Australien — tropische Regenwälder, epiphytisch) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, fragrant | `species.traits` |

**Hinweis:** Hoya carnosa ist für ihr zartes, schokoladig-vanilleartiges Duft bekannt (besonders nachts). Die sternförmigen Blüten hängen in kugelig-runden Blütendolden (Umbellen). Wichtig: Alte Blütenstiele (Pedunclen) NIEMALS entfernen — sie sind mehrjährig und bilden jede Saison neue Knospen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 (bei reifen Pflanzen ab ca. 3–5 Jahren) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–3 Blättern und mindestens einem Knoten. In Wasser (4–6 Wochen) oder direkt in leichtem Substrat bewurzeln. Luftschichtung (Air Layering) bei dicken Trieben möglich. Wichtig: Kein Blütenstiel als Steckling verwenden!

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

**Hinweis:** Hoya carnosa gilt als haustierfreundlich. Der milchige Saft kann bei manchen Menschen leichte Hautirritation verursachen, ist aber nicht klassifiziert toxisch. Ideal für Haushalte mit Tieren und Kindern.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (nach Winterruhe, vor neuem Austrieb) | `species.pruning_months` |

**Wichtig:** Blütenstiele (Pedunclen) NICHT abschneiden — sie blühen jedes Jahr erneut an derselben Stelle. Nur Wildtriebe und zu lange Ranken kürzen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (als Kletterpflanze) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, windgeschützt, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Rankgitter, Moosstab oder Bogen — Pflanze rankt sehr gerne) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr durchlässiges Substrat: Orchideenrinde + Perlite + etwas Kakteenerde (1:1:1). pH 6.0–7.0. Staunässe führt schnell zu Wurzelfäule. Kleiner Topf fördert Blüte (pot-bound). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 50 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-Schwellenwert für Hoya carnosa --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-Slope --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Als schattenadaptierte epiphytische CAM-Liane (epiphytic CAM vine) hat Hoya carnosa einen niedrigen Lichtkompensationspunkt (light compensation point) im typischen Schattenpflanzen-Bereich von ca. 10–50 µmol/m²/s. Der Lichtsättigungspunkt (light saturation point) liegt deutlich höher; volle Mittagssonne kann zu Photoinhibition (photoinhibition) und Blattverbrennung führen — diese Werte gehören NICHT in das Kompensationspunkt-Feld. Die Salztoleranz-Klasse `sensitive` ergibt sich aus der hohen Empfindlichkeit gegenüber Düngersalz-Akkumulation und Wurzelschäden; die quantitativen Maas-Hoffman-Parameter sind für diese Zierpflanze nicht publiziert. Boden-pH-Vorzug harmonisiert mit §1.6 und §2.3 (6.0–7.0).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Blüte | 60–120 | 2 | false | false | low |
| Winterruhe | 120–150 | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 20–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 16–21 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 21–35 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:1:1 | 0.6–1.0 | 6.0–7.0 | 60 | 25 | 0.5 | 0.1 | 0.05 | 0.02 |
| Blüte | 1:2:1 (P-betont) | 0.4–0.8 | 6.0–7.0 | 50 | 20 | 0.4 | 0.1 | 0.05 | 0.02 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Für Hoya carnosa sind keine artspezifischen Mikronährstoff-Sollwerte publiziert. Die Werte Mn/Zn/Cu/Mo (manganese/zinc/copper/molybdenum) folgen den allgemeinen, am unteren Ende angesetzten Standard-Bereichen für Schwachzehrer-/Hoagland-Nährlösungen (light_feeder): Mn 0.5–2, Zn 0.5–2, Cu 0.1–0.5, Mo 0.02–0.05 ppm. Bei dieser empfindlichen Zierpflanze wird bewusst niedrig dosiert, um Salzakkumulation zu vermeiden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L | Wachstum |
| Blühpflanzen-Dünger | Compo | bloom | 5-8-10 | 3 ml/L | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Für Blüteninduktion: im Winter Bewässerung stark reduzieren (1x/3 Wochen) und kühle Temperaturen (12–15°C nachts). Kein Dünger Okt–Feb. Ab März wieder Wachstumsdünger. Zu viel N fördert Blattmasse statt Blüten. Kleine Töpfe und "pot-bound"-Bedingungen fördern Blüte!

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; abgestandenes Wasser bevorzugt; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (Hoya blüht besser in engem Topf!) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9, 10 (vor erstem Frost ins Haus) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5, 6 (nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 12–16 (kühl-frostfrei; fördert Blüteninduktion) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (heller Fensterplatz; bei Lichtmangel Pflanzenlampe) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | stark reduziert (alle 3–5 Wochen, nur antrocknen lassen) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Hoya carnosa ist nicht frosthart (Mindesttemperatur 10°C) und überwintert in Mitteleuropa (USDA 6–8) zwingend frostfrei im Haus (`frost_free`). Ein kühl-helles Winterquartier (12–16°C) mit reduziertem Gießen und ohne Düngung unterstützt die Blüteninduktion im Folgejahr. Im Sommer kann sie an einen windgeschützten, halbschattigen Außenstandort (Balkon/Terrasse) — vgl. §1.6 `balcony_suitable = limited`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken, Honigtau | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blattvergilbung (bei trockener Luft) | medium |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Stängeln | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, faulende Wurzeln | Überbewässerung, Staunässe |
| Botrytis | fungal | Grauer Schimmel auf Blüten | Hohe Luftfeuchte, schlechte Zirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (Blüten meiden!) | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse, Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10 Käfer/m² (Befallsherde), bei starkem Befall 5–40/m² | 2–4 Wochen (mehrere Freilassungen im Abstand 1–2 Wochen) |
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–6/m² (Prävention/Kleinbefall), 20–50/m² (Starkbefall, wöchentlich) | 2–3 Wochen (benötigt ≥ 60 % rel. Luftfeuchte, > 20°C) |
| Erzwespe (Schlupfwespe) | Metaphycus helvolus | Weichschildlaus (Coccus hesperidum) | 5–10 Adulte/m² je Freilassung, wiederholt alle 2 Wochen | 3–4 Wochen (warm, > 22°C optimal) |

**Hinweis:** Cryptolaemus montrouzieri und Phytoseiulus persimilis benötigen warme (> 20–25°C), eher feuchte Bedingungen — daher v. a. für Gewächshaus oder beheizten Wintergarten geeignet. Metaphycus helvolus parasitiert gezielt Weichschildläuse (Coccidae) wie Coccus hesperidum, nicht Panzer-/Deckelschildläuse (Diaspididae). Nützlingseinsatz und chemische/ölbasierte Mittel (Neemöl) zeitlich trennen, da Öle auch Nützlinge schädigen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Hoya kerrii | Hoya kerrii | Gleiche Gattung | Herzförmige Blätter; populär als Valentinstagspflanze |
| Hoya bella | Hoya bella | Gleiche Gattung | Kleinblättriger, kompakter; zierliche Blüten |
| Hoya pubicalyx | Hoya pubicalyx | Gleiche Gattung | Schneller wachsend, leichter zu blühen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Hoya carnosa,"Wachsblume;Porzellanblume;Wax Plant;Honey Plant",Apocynaceae,Hoya,perennial,day_neutral,vine,fibrous,"9a;9b;10a;10b;11a;11b","Ostasien (epiphytisch)",yes,2-8,15,60-200,40-100,yes,limited,false,true,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Tricolor,Hoya carnosa,"ornamental;variegated;pink_cream_green",clone
Krimson Queen,Hoya carnosa,"ornamental;variegated;cream_edge",clone
Krimson Princess,Hoya carnosa,"ornamental;variegated;cream_center",clone
Compacta,Hoya carnosa,"ornamental;curled_leaves;compact",clone
```

---

## Quellenverzeichnis

1. [NCSU Extension — Hoya carnosa](https://plants.ces.ncsu.edu/plants/hoya-carnosa/) — Botanische Einordnung
2. [Gardenia.net — Wax Plant](https://www.gardenia.net/plant/hoya-carnosa-wax-plant-all-you-need-to-know) — Kulturdaten
3. [Planet Natural](https://www.planetnatural.com/hoya-carnosa/) — Pflegehinweise
4. [Epic Gardening — Hoya Plant](https://www.epicgardening.com/hoya-plant/) — Sorten, Blüteninduktion
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/hoya-carnosa-a-comprehensive-guide/) — Ganzjahrespflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Springer — Sun/shade adaptations of the photosynthetic apparatus of Hoya carnosa, an epiphytic CAM vine](https://link.springer.com/article/10.1007/s11738-009-0434-9) — CAM-Photosynthese-Typ, Schattenadaptation
7. [Springer — Canopy CO2 concentrations and CAM in Hoya carnosa (Photosynthetica)](https://link.springer.com/article/10.1007/s11099-005-0168-x) — CAM-Bestätigung, epiphytische Standortqualität
8. [Foliage Factory — Low-Light Houseplants: Real Light Levels & Plant Categories](https://foliage-factory.com/blogs/plant-care/low-light-houseplants-explained) — Hoya carnosa Schattenpflanze, niedriger Lichtkompensationspunkt
9. [Wiley/BES — Light compensation point across tropical understorey shrub species](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — LCP-Bereich Schattenpflanzen (10–50 µmol/m²/s)
10. [NCSU Extension — Hoya carnosa Soil/Light](https://plants.ces.ncsu.edu/plants/hoya-carnosa/) — Boden-pH (6.0–7.0), Drainage, partial shade
11. [Academia.edu — Temperature response of photosynthesis in C3, C4, and CAM plants](https://www.academia.edu/14144138/Temperature_response_of_photosynthesis_in_C3_C4_and_CAM_plants_temperature_acclimation_and_temperature_adaptation) — CAM-Photosynthese-T_opt
12. [Academic OUP/PMC — PAR und Rot:Dunkelrot-Verhältnis unter Kronendach](https://pmc.ncbi.nlm.nih.gov/articles/PMC7489061/) — R:FR / Far-Red-Fraction im Unterwuchs/Schatten
13. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate Schmierlaus-Marienkäfer
14. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Raubmilbe gegen Spinnmilbe
15. [Wiley/Hindawi — Coccophagus & Metaphycus als Nützlinge gegen Weichschildläuse (Coccus hesperidum)](https://onlinelibrary.wiley.com/doi/10.1155/2011/431874) — Parasitoid-Wirt-Zuordnung Weichschildlaus
16. [Hoagland solution — Wikipedia](https://en.wikipedia.org/wiki/Hoagland_solution) — Standard-Mikronährstoffbereiche Mn/Zn/Cu/Mo
17. [RHS — How to grow Hoya](https://www.rhs.org.uk/plants/hoya/how-to-grow) — Überwinterung, Mindesttemperatur, frostfrei
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
