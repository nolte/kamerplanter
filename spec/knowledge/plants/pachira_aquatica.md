# Glückskastanie — Pachira aquatica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Old Farmer's Almanac](https://www.almanac.com/plant/money-tree-plant-pachira-aquatica-care-guide), [Guide to Houseplants](https://www.guide-to-houseplants.com/money-tree-plant.html), [Soltech](https://soltech.com/products/money-tree-care), [Gardenia.net](https://www.gardenia.net/plant/pachira-aquatica-money-tree), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pachira aquatica | `species.scientific_name` |
| Volksnamen (DE/EN) | Glückskastanie, Malabar-Kastanie, Pachira; Money Tree, Guiana Chestnut, Saba Nut | `species.common_names` |
| Familie | Malvaceae | `species.family` → `botanical_families.name` |
| Gattung | Pachira | `species.genus` |
| Ordnung | Malvales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 30–200+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein publizierter Wuchs-/Phänologie-GDD-Basiswert für Pachira aquatica; Mindestwuchstemperatur ~10–12 °C ist KEINE GDD-Basis und wird daher nicht umetikettiert --> | `species.base_temp` |
| Kritische Tageslänge (critical day length, h) | <!-- entfällt: tagneutral (day_neutral), kein Kurztag-/Langtag-Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–29°C. Robust und tolerant gegenüber typischer Zimmertemperatur. | `species.hardiness_detail` |
| Heimat | Mexiko bis Nordbolivien — tropische Sumpfwälder, Flussufer | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Pachira aquatica ist in der Feng-Shui-Tradition ein Glückssymbol (5 Blättchen = 5 Elemente). Der im Handel übliche geflochtene Stamm (Braided Trunk) entsteht durch Verdrehen mehrerer Jungpflanzen. Problem: Mit zunehmender Dicke können sich die Stämme gegenseitig einschnüren. Alternativ: Einzelstämmige Exemplare ohne Flechtung. In der Natur ein Sumpfbewohner — daher verträgt Pachira kurzzeitig Staunässe besser als viele andere Zimmerpflanzen, leidet aber dennoch darunter.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nicht in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (15–20 cm, halbholzig) bei 25–30°C und hoher Luftfeuchtigkeit. Bewurzelung in 4–8 Wochen. Samen bei 25–30°C, Keimung in 2–4 Wochen.

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

**Hinweis:** Pachira aquatica ist nicht giftig. Samen sind essbar (erinnern an Kastanien/Erdnüsse im Geschmack). ASPCA listet die Pflanze als ungiftig.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Verträgt Rückschnitt gut. Im Frühjahr überlange Triebe kürzen. Topping fördert buschigen Wuchs.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–250 (indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20% Perlite. pH 6.0–7.5. Gute Drainage. Leicht feuchtigkeitshaltend da aus Sumpfgebiet stammend. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP-Messwert für Pachira aquatica auffindbar; als schattentolerante Tropen-Unterwuchsart liegt der LCP literaturgestützt grob bei 10–50 µmol/m²/s (Craine & Reich 2005; Sterck et al. 2013), aber nicht artspezifisch belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: siehe min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | <!-- DATEN FEHLEN: keine quantitative Wurzeltiefe für Pachira aquatica in seriösen Quellen belegt --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | moderate | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Schwellwert (a) für Pachira aquatica publiziert; qualitativ als salzempfindlich belegt (Salzanreicherung → Blattrandnekrosen) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN: kein Slope-Wert publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.5 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis (Standortqualität):** Pachira aquatica ist eine schattentolerante Art mit ausgeprägter Lichtplastizität: Jungpflanzen wachsen im gefilterten Unterwuchs (understory), adulte Bäume erreichen die Vollsonne (full sun) der Kronenschicht — in Zimmerkultur entspricht das hellem, indirektem Licht. Als Sumpf-/Flussuferbewohner toleriert sie kurzzeitige bzw. saisonale Überflutung, leidet aber unter dauerhafter Staunässe (waterlogging) → `moderate`. Salzempfindlich (`sensitive`): Salzanreicherung durch Überdüngung oder hartes Gießwasser verursacht Blattrandnekrosen; periodisches Durchspülen (flushing) des Substrats empfohlen. Der pH-Vorzug 6.0–7.5 ist konsistent mit §1.6 (Substrat) und §2.3 (Nährstoffprofile).

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 30 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1.5 (ca. 1/2 inch; manche Anleitungen empfehlen stattdessen nur leichtes Bedecken an der Substratoberfläche) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14 (Spanne 2–4 Wochen) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | < 1 (sehr kurze Frischsaat-Lebensdauer von nur ca. 20–60 Tagen; Samen müssen kurz nach der Ernte ausgesät werden) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | <!-- DATEN FEHLEN: keine übereinstimmende Aussage zu Licht-/Dunkelkeimung gefunden — Quellen beschreiben nur "leicht bedecken und mit Folie/Glas abdecken", ohne Licht als Keimfaktor explizit zu nennen --> | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak (24 h Einweichen vor der Aussaat verbessert die Keimung) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: keine artspezifische Tausendkornmasse für die grossen, kastanienartigen Pachira-Samen in seriösen Quellen auffindbar --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- SECTION MISSING: kein Reihen-/Direktsaat-Feldanbau — Pachira aquatica wird einzeln je Topf ausgesät, keine Flächen-Aussaatdichte dokumentiert --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Pachira-Samen verlieren ihre Keimfähigkeit sehr schnell (Frischsaat-Prinzip) — bereits nach wenigen Wochen Lagerung sinkt die Keimrate drastisch; frisch geerntete oder schwimmfähige Samen (Floattest) sollten möglichst umgehend ausgesät werden. Vor der Aussaat 24 h in Wasser einweichen beschleunigt und vergleichmäßigt die Keimung.

Quellen (§1.8): [Epic Gardening — Money Tree Plant: Growing Pachira Aquatica](https://www.epicgardening.com/money-tree-plant/); [VIRIAR — Pachira aquatica (Malabar Chestnut, Money Tree): Complete Tree Growing](https://www.viriar.com/blogs/tree-encyclopedia/pachira-aquatica); [Greg.app — How Fast Your Pachira Will Grow](https://greg.app/pachira-lifecycle/); [ResearchGate — Germination of Pachira aquatica as a function of the storage treatments](https://www.researchgate.net/figure/Germination-of-Pachira-aquatica-as-a-function-of-the-storage-treatments-over-time_fig1_222666625); [Useful Tropical Plants — Pachira aquatica](https://tropical.theferns.info/viewtropical.php?id=Pachira+aquatica)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–24 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 26–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.5 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.5 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (micronutrients) je Phase — Mn/Zn/Cu/Mo (ppm):**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Aktives Wachstum | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

**Hinweis:** Für Pachira aquatica sind keine artspezifischen Mikronährstoff-Sollkonzentrationen (Mn/Zn/Cu/Mo) in seriösen Quellen belegt. Als Schwachzehrer (light feeder) deckt ein vollständiger Zimmerpflanzen-Flüssigdünger mit Spurenelementen den Bedarf; daher werden die Felder `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` als DATEN FEHLEN markiert statt mit generischen Hoagland-Werten überschrieben.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 4 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Monatlich März bis September. Oktober bis Februar: kein Dünger. Ausgeglichene Formel. Überdüngung führt zu Blattrandnekrosen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; obere 2–3 cm Erde zwischen Güssen abtrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (min. 10–12) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (bright indirect); ggf. Pflanzenlampe bei kurzen Tagen | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert; obere 2–3 cm abtrocknen lassen, ca. alle 10–14 Tage; Substrat nie ganz austrocknen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Pachira aquatica ist nicht frosthart (`frost_sensitivity: tender`, USDA 10–11) und überwintert in Mitteleuropa (USDA 6–8) zwingend frostfrei im Haus → `frost_free`. Eine sommerliche Balkon-/Terrassenkultur ist nur im Halbschatten und in den frostfreien Monaten (etwa Mitte Mai bis Anfang Oktober) möglich; davor/danach ins Winterquartier holen (`move_indoors`/`move_outdoors`). Keine echte Dormanz, aber temperatur-/lichtbedingt verlangsamtes Wachstum — daher Gießen und Düngung über Winter reduzieren.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, weicher Stamm | Staunässe |
| Anthraknose | fungal | Braune Flecken mit gelbem Rand | Nasses Laub, hohe Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|----------------|--------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 4–20/m² je Befall, wöchentlich 1–2× wiederholen | ca. 14 Tage (13–27 °C, > 70 % rF) |
| Cryptolaemus montrouzieri (Marienkäfer) | Schmierlaus (Pseudococcus spp.) | 2–3/m² (bis 10/m² bei Starkbefall) | 3–6 Wochen |
| Metaphycus helvolus (Schlupfwespe) | Weichschildlaus (Coccus hesperidum, Coccidae) | 5/m², 3× im 14-Tage-Abstand | 4–6 Wochen |

**Hinweis:** Die Zuordnung folgt der Wirtsspezifität: *Phytoseiulus persimilis* gegen Spinnmilben, *Cryptolaemus montrouzieri* gegen Schmierläuse, *Metaphycus helvolus* gegen Weichschildläuse (Coccidae, hier *Coccus hesperidum*). *Metaphycus*/*Cryptolaemus* wirken NICHT gegen Panzer-/Deckelschildläuse (Diaspididae) — dafür wären *Aphytis*-Arten zuständig, die bei Pachira jedoch nicht als Schädling gelistet sind. Nützlingseinsatz nur bei frostfreier Innen-/Gewächshauskultur sinnvoll; *Phytoseiulus* braucht hohe Luftfeuchte und mildes Klima.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Schefflera | Schefflera arboricola | Gefiedertes Laub, Baumform | Robuster bei wenig Licht |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Pachira aquatica,"Glückskastanie;Malabar-Kastanie;Pachira;Money Tree;Guiana Chestnut",Malvaceae,Pachira,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Mexiko bis Nordbolivien",yes,5-20,25,100-250,60-150,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Old Farmer's Almanac — Money Tree](https://www.almanac.com/plant/money-tree-plant-pachira-aquatica-care-guide) — Pflegehinweise
2. [Guide to Houseplants — Money Tree](https://www.guide-to-houseplants.com/money-tree-plant.html) — Kulturdaten
3. [Soltech — Money Tree Care](https://soltech.com/products/money-tree-care) — Lichtbedarf
4. [Gardenia.net — Pachira aquatica](https://www.gardenia.net/plant/pachira-aquatica-money-tree) — Botanische Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Missouri Botanical Garden — Pachira aquatica Plant Finder](https://www.missouribotanicalgarden.org/plantfinder/plantfinderdetails.aspx?taxonid=277941) — Lichtbedarf (full sun to part shade), Feuchte-/Überflutungstoleranz, Wuchshöhe
7. [NYBG Mertz Library — Money Tree Light/Shade](https://libanswers.nybg.org/faq/336073) — Schatten-/Lichtansprüche, Unterwuchs-Wachstumsmuster
8. [Farmonaut — Pachira aquatica Care: Soil & Aquatic Compost](https://farmonaut.com/blogs/pachira-aquatica-care-tips-plant-soil-aquatic-compost) — Staunässe-/Überflutungstoleranz (partial flooding, nicht dauerhaft)
9. [Get Busy Gardening — Money Tree Soil](https://getbusygardening.com/money-tree-soil/) — Boden-pH-Vorzug 6.0–7.5
10. [PlantsForAllSeasons — Common Problems Pachira aquatica](https://www.plantsforallseasons.co.uk/blogs/pachira-care/common-problems-and-solutions-for-pachira-aquatica-money-tree) — Salzempfindlichkeit (Salzanreicherung → Blattrandnekrosen)
11. [Healthy Houseplants — Money Tree Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/money-tree-pachira-aquatica-care-guide/) — Mindesttemperatur, Überwinterung, reduziertes Gießen
12. [Tan et al. 2017, Optimum temperature for photosynthesis (tropical forests ≈ 29 °C)](https://www.researchgate.net/publication/338511928_Optimum_temperature_for_photosynthesis_from_leaf-_to_ecosystem-scale) — Photosynthese-T_opt-Anker für tropische Bäume
13. [Craine & Reich 2005, New Phytologist — Leaf-level light compensation points in shade-tolerant woody seedlings](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2005.01420.x) — LCP-Größenordnung schattentoleranter Gehölze (literaturgestützter Kontext)
14. [Sterck et al. 2013, Journal of Ecology — Plasticity influencing the light compensation point in a tropical forest understorey](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — LCP-Plastizität tropischer Unterwuchsarten
15. [Koppert — Phytoseiulus persimilis (Spinnmilben-Raubmilbe)](https://www.koppert.com/spidex/) — Ausbringrate/Etablierung Nützling
16. [Metaphycus helvolus — Wikipedia / UCR Biocontrol (Coccus hesperidum)](https://en.wikipedia.org/wiki/Metaphycus_helvolus) — Weichschildlaus-Parasitoid, Ausbringrate 5/m²
17. [Interiorlandscaping — Biological Controls (Cryptolaemus, Metaphycus, Phytoseiulus)](http://www.interiorlandscaping.co.uk/Biologica.htm) — Nützling-Ausbringraten Innenraumkultur
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: seed-profile-backfill 2026-07 -->
18. [Epic Gardening — Money Tree Plant: Growing Pachira Aquatica](https://www.epicgardening.com/money-tree-plant/) — Saattiefe ~1/2 inch, 24h-Einweichen, Keimtemperatur 75–80 °F
19. [VIRIAR — Pachira aquatica (Malabar Chestnut, Money Tree): Complete Tree Growing](https://www.viriar.com/blogs/tree-encyclopedia/pachira-aquatica) — Keimtemperatur 20–30 °C, Keimdauer 2–3 Wochen
20. [Greg.app — How Fast Your Pachira Will Grow](https://greg.app/pachira-lifecycle/) — Keimdauer 2–4 Wochen
21. [ResearchGate — Germination of Pachira aquatica as a function of the storage treatments](https://www.researchgate.net/figure/Germination-of-Pachira-aquatica-as-a-function-of-the-storage-treatments-over-time_fig1_222666625) — sehr kurze Keimfähigkeitsdauer (20–60 Tage je nach Lagerung)
22. [Useful Tropical Plants — Pachira aquatica](https://tropical.theferns.info/viewtropical.php?id=Pachira+aquatica) — Samenmerkmale, Frischsaat-Empfehlung
<!-- /Quelle: seed-profile-backfill 2026-07 -->
