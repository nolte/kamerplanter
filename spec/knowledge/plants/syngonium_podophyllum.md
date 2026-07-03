# Pfeilblatt, Dreieckspflanze — Syngonium podophyllum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/syngonium-podophyllum-arrowhead-vine-grow-care-tips), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/arrowhead-plant-syngonium-podophyllum-complete-care-guide-growing-tips/), [Old Farmer's Almanac](https://www.almanac.com/plant/arrowhead-plant-care-and-propagation-syngonium), [NC State Extension](https://plants.ces.ncsu.edu/plants/syngonium-podophyllum/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Syngonium podophyllum | `species.scientific_name` |
| Volksnamen (DE/EN) | Pfeilblatt, Dreieckspflanze, Arrowhead-Pflanze; Arrowhead Plant, Arrowhead Vine, Goosefoot Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Syngonium | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), keine echte Kurztag-/Langtag-Induktion → numerisches Stundenfeld bleibt leer --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Verträgt normale Zimmertemperaturen gut. | `species.hardiness_detail` |
| Heimat | Mexiko bis Bolivien — tropische Regenwälder, kletternd auf Bäumen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Syngonium verändert sein Blattbild mit dem Alter dramatisch — junge Pflanzen haben einfache pfeilförmige Blätter, ältere Exemplare entwickeln gelappte, fingerartige Blätter (3–9 Lappen). Für kompakten Wuchs und schöne Blattformen: Kletterschiene regelmäßig kappen oder hängende Triebe zurückschneiden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (unterhalb eines Knotens mit Luftwurzelansatz) in Wasser bewurzeln — 1–2 Wochen. Sehr zuverlässig. Alternativ direkt in feuchtes Substrat. Handschuhe empfohlen (Milchsaft).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft — kann Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Für kompakten Wuchs: Triebe regelmäßig kappen. Hängende oder kriechende Triebe kürzen, um jungblättrige, schönere Pflanzen zu erhalten. Handschuhe tragen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–180 (kletternd) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20% Perlite. pH 5.5–6.5. Gut feuchtigkeitshaltend aber nicht stauend. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert (Netto-Photosynthese = 0) für Syngonium podophyllum in seriösen Quellen auffindbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: s. o. --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: epiphytischer Kletterer mit flachem Adventivwurzelsystem; keine belegte cm-Spanne in seriösen Quellen --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Schwelle für diese Zierpflanze publiziert; qualitativ salzempfindlich (Salzakkumulation schädigt Wurzeln) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis:** Tropische Unterwuchs-Aroide; gedeiht in dappligem Halbschatten (partial shade) bis tiefem Schatten (deep shade), Vollsonne (full sun) verbrennt/bleicht das Laub. Salzempfindlich — Salzakkumulation aus Über­düngung führt zu braunen Blattspitzen; regelmäßiges Durchspülen (Flushing) und halbierte Düngerdosis empfohlen, Regen-/destilliertes Wasser ideal. Boden-pH 5.5–6.5 ist konsistent mit §1.6 (Substrat-Empfehlung) und §2.3 (Nährstoffprofile).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.60–0.70 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 5.5–6.5 | 80 | 30 | 0.3–0.5 | 0.04–0.10 | 0.02–0.05 | 0.01–0.05 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 5.5–6.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoff-Hinweis:** Die Mikronährstoff-Spannen Mn/Zn/Cu/Mo (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`) entsprechen den üblichen Richtwerten verdünnter Vollnährlösungen für leichtzehrende (light_feeder) Zierpflanzen (Hoagland-/Steiner-Niveau, an niedrige EC 0.6–1.0 mS angepasst). Kein artspezifischer Messwert für Syngonium podophyllum publiziert — Bereiche sind als sichere Standard-Versorgung zu verstehen, nicht als artspezifisch validierte Optima. In der Winterruhe (0:0:0) entfällt die Mikronährstoffgabe.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 4 ml/L (alle 4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen März bis September. Oktober bis Februar: kein Dünger. Stickstoffbetonte Formel für buschiges, farbiges Laub. Bei bunt-variegatierten Sorten: Weniger N (zu viel N macht Blätter grüner).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; gleichmäßig feucht halten, nicht austrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–22 (Minimum 15) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, kein direktes Sonnenlicht (dappliger Halbschatten / partial shade) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert, Substrat oben abtrocknen lassen, Staunässe vermeiden | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Nicht frosthart (frost_free) — reine Innen-/Kübelüberwinterung. Im Sommer kann die Pflanze im frostfreien Halbschatten auf Balkon/Terrasse stehen; vor dem ersten Herbstfrost (September–Oktober) ins frostfreie Innenquartier holen. Ab Mitte Mai (nach den Eisheiligen) wieder hinausstellen — zuvor schrittweise an Außenbedingungen gewöhnen (harden_off). Minimaltemperatur 15 °C; Wachstum verlangsamt unter 15 °C, Kälteschäden unter ~10 °C (konsistent mit §1.1 Winterhärte-Detail und base_temp 10 °C).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Thrips | Frankliniella spp. | Silbrige Streifen, deformierte Blätter | medium |
| Blattlaus | Aphididae | Kolonien an Triebspitzen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Blattflecken | fungal/bacterial | Braun-gelbe Flecken | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse, Thrips |
| Insektizidseife | biological | Sprühen | 3 Tage | Blattläuse, Thrips |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (pro m²) | Etablierungszeit |
|----------|--------------------|----------------|-----------------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 | 2–3 Wochen |
| Raubmilbe | Neoseiulus (Amblyseius) cucumeris | Thrips (Frankliniella spp.) | 100–400 | 3–4 Wochen |
| Schlupfwespe | Aphidius colemani | Blattlaus (Aphididae) | 0.25–4 | 2–3 Wochen |
| Marienkäfer (Australischer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | 2–10 | 3–4 Wochen |

**Hinweis:** Raubmilben (Phytoseiulus, Neoseiulus) und die parasitische Schlupfwespe Aphidius colemani benötigen für gute Etablierung > 60–70 % relative Luftfeuchte und 18–27 °C — im Innenraum ggf. Luftfeuchte anheben. Ausbringung sobald Befall erkannt, 2–3 Wiederholungen im Wochen-/Zweiwochenabstand. Cryptolaemus montrouzieri (Schmierlaus-Räuber) ist bei Zimmertemperatur über 20 °C am aktivsten.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Philodendron | Philodendron hederaceum | Gleiche Familie, Klettergewächs | Größer, robuster |
| Pothos | Epipremnum aureum | Gleiche Familie, Klettergewächs | Deutlich pflegeleichter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Syngonium podophyllum,"Pfeilblatt;Dreieckspflanze;Arrowhead Plant;Arrowhead Vine",Araceae,Syngonium,perennial,day_neutral,vine,aerial,"10a;10b;11a;11b","Mexiko bis Bolivien",yes,2-8,15,30-180,30-60,yes,limited,false,light_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Neon Robusta,Syngonium podophyllum,"ornamental;pink;compact",clone
Pixie,Syngonium podophyllum,"ornamental;compact;dwarf",clone
Imperial White,Syngonium podophyllum,"ornamental;variegated;white_green",clone
Strawberry Cream,Syngonium podophyllum,"ornamental;pink;variegated",clone
Albo-Variegatum,Syngonium podophyllum,"ornamental;variegated;white_splashed",clone
```

---

## Quellenverzeichnis

1. [Gardenia.net — Syngonium podophyllum](https://www.gardenia.net/plant/syngonium-podophyllum-arrowhead-vine-grow-care-tips) — Botanische Daten, Kulturdaten
2. [Healthy Houseplants — Arrowhead Plant](https://www.healthyhouseplants.com/indoor-houseplants/arrowhead-plant-syngonium-podophyllum-complete-care-guide-growing-tips/) — Schädlinge, Krankheiten
3. [Old Farmer's Almanac — Arrowhead Plant](https://www.almanac.com/plant/arrowhead-plant-care-and-propagation-syngonium) — Pflegehinweise
4. [NC State Extension — Syngonium podophyllum](https://plants.ces.ncsu.edu/plants/syngonium-podophyllum/) — Taxonomie, Heimat, Schatten-/Lichttoleranz (dappled/partial shade, avoid full sun)
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Henry Shaw Cactus & Succulent Society — C3, C4, CAM](https://hscactus.org/resources/digest/plant-info/c3-c4-cam/) — Photosynthese-Typ C3 (allgemein)
7. [Foliage Factory — Plant Stomata Explained](https://foliage-factory.com/blogs/plant-care/stomata-plant-function-explained) — Aroide (Monstera, Philodendron, Epipremnum, Syngonium) sind überwiegend C3, kein CAM
8. [PMC — Increasing leaf sizes of the vine *Epipremnum aureum* (Araceae): photosynthesis and respiration](https://pmc.ncbi.nlm.nih.gov/articles/PMC11974542/) — Unterwuchs-PPFD ~100, Sättigung ~1000 µmol/m²/s, T_opt-Kontext (Aroid-Vergleichsart)
9. [Soltech — Syngonium Care](https://soltech.com/products/syngonium-care) — Optimaltemperatur 18–27 °C, Wachstumsstopp bei Kälte (base_temp-Ableitung)
10. [INKBIRD — Syngonium Plant Care Guide](https://www.inkbird.com/blogs/growing/syngonium-plant-care-guide) — Kälteempfindlichkeit, Wachstum stoppt ~10 °C, Min. 15 °C
11. [GISD/IUCN — Syngonium podophyllum](https://www.iucngisd.org/gisd/speciesname/syngonium+podophyllum) — Heimat, Boden-pH 5.5–6.5, Tiefschatten-Toleranz, feucht/gut drainiert
12. [BackyardGardener — Syngonium podophyllum (Arrowhead Vine)](https://www.backyardgardener.com/plantname/syngonium-podophyllum-arrowhead-vine/) — Boden-pH 5.5–6.5, Part Shade/Dappled
13. [Healthy Houseplants — Arrowhead Plant](https://www.healthyhouseplants.com/indoor-houseplants/arrowhead-plant-syngonium-podophyllum-complete-care-guide-growing-tips/) — Salzempfindlichkeit (Salzakkumulation schädigt Wurzeln), Staunässe-Empfindlichkeit
14. [Biology Insights — Syngonium Fertilizer](https://biologyinsights.com/syngonium-fertilizer-how-to-choose-and-apply-it/) — Salzempfindlichkeit, halbierte Düngerdosis, Flushing
15. [bioRxiv — Understory light quality affects leaf pigments and leaf phenology](https://www.biorxiv.org/content/10.1101/829036v1.full) — R:FR im Tiefschatten ~0.42, Gaps ~0.86, offen ~1.2 (Far-Red-Fraction-Ableitung)
16. [Koppert — *Phytoseiulus persimilis*](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate 2–50/m², Etablierung/Klimabedingungen Spinnmilbe
17. [Koppert — *Cryptolaemus montrouzieri*](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate Schmierlaus-Räuber
18. [Koppert — *Aphidius colemani*](https://www.koppertus.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Ausbringrate/Temperaturoptimum Blattlaus-Parasitoid
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
