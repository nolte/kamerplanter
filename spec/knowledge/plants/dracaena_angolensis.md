# Zylindrische Sansevierie, Afrikanischer Speer — Dracaena angolensis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/sansevieria-cylindrica-african-spear-snake-plant), [NC State Extension](https://plants.ces.ncsu.edu/plants/dracaena-angolensis/), [Epic Gardening](https://www.epicgardening.com/sansevieria-cylindrica/), [Garden Beast](https://gardenbeast.com/sansevieria-cylindrica-guide/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dracaena angolensis | `species.scientific_name` |
| Synonyme | Sansevieria cylindrica (bis 2017 gültiger Name), Sansevieria cylindrica var. patula | — |
| Volksnamen (DE/EN) | Zylindrische Sansevierie, Afrikanischer Speer, Speerpflanze; African Spear, Cylindrical Snake Plant, Spear Sansevieria, Elephant Grass | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Dracaena | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-Basiswert für Dracaena angolensis auffindbar --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 20–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–27°C. | `species.hardiness_detail` |
| Heimat | Angola, tropisches Afrika — trockene Savanne, Felsstandorte | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, air_purifying | `species.traits` |

**Hinweis:** Dracaena angolensis ist die umbenannte Sansevieria cylindrica — seit 2017 werden alle Sansevieria-Arten botanisch zu Dracaena gezählt (Christenhusz et al.). Im Handel wird die Pflanze noch häufig unter dem alten Namen verkauft. Die runden, speerartigen Blätter (bis 180 cm hoch) wachsen aufrecht und unverzweigt — vollständig anders als die flachen Blätter der bekannteren Dracaena trifasciata (Schwiegermutterzunge). In der Wohnung oft zu dekorativen Zöpfen oder Bündeln geflochten verkauft. Sehr robust und pflegeleicht.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht kaum in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Offset-Ableger (Kindel) vom Mutterrhizom trennen. Blattstücke (5–10 cm) in Kakteenerde stecken — Bewurzelung in 4–8 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (Blätter, Saft) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
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
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–180 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde oder Einheitserde + 40% Sand/Perlite. pH 5.5–7.0. Sehr gute Drainage ist essentiell — Staunässe ist die einzige ernsthafte Bedrohung. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein publizierter Netto-Kompensationspunkt für Dracaena angolensis/Sansevieria belegt --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Schwellenwert (a) für die Art belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope (b) für die Art belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Die Art ist sehr anpassungsfähig an die Lichtmenge — sie bevorzugt volle Sonne bzw. helles Licht (bis ~6 h direkte Sonne verträglich), toleriert aber auch Halbschatten und niedrige Lichtmengen bei reduziertem Wachstum (`partial_shade` bildet die Schattentoleranz ab, nicht die optimale Lichtstufe). Das Wurzelsystem ist flach und rhizombildend; sandige, durchlässige Substrate bzw. Felsspalten. Hohe Salz- und Trockentoleranz (geeignet für Küstenstandorte), aber sehr empfindlich gegen Staunässe — Wurzelfäule durch Überwässerung ist die Haupt-Todesursache. Der pH-Vorzug 6.0–6.5 liegt innerhalb der in §1.6/§2.3 genannten breiteren Kulturspanne pH 5.5–7.0.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe (sehr langsam) | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 (heller bis halbschattiger Standort; offenes Tageslicht ≈ 0.5, Halbschatten leicht höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–300 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 (heller bis halbschattiger Standort; offenes Tageslicht ≈ 0.5, Halbschatten leicht höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.5–0.9 | 5.5–7.0 | 60 | 25 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.2 | 5.5–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Für Dracaena angolensis sind keine artspezifisch belegten Mikronährstoff-Zielwerte (Mn/Zn/Cu/Mo in ppm) publiziert. Als leichter Zehrer (`light_feeder`) deckt ein vollständiger Grünpflanzen-/Sukkulentendünger mit Spurenelementen den Bedarf; Werte daher als `DATEN FEHLEN` markiert statt generische Hydrokultur-Richtwerte fachlich falsch der Art zuzuschreiben.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen-/Succulent-Dünger | Compo | base | 5-3-8 | 3 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis September. Oktober bis März kein Dünger. Die Pflanze überlebt problemlos jahrelang ohne Düngung — regelmäßiges Umtopfen in frisches Substrat alle 3–4 Jahre ist ausreichend.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat vollständig austrocknen zwischen Güssen; im Winter fast kein Wasser — 1x pro Monat reicht; Staunässe ist die einzige Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mitte Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–18 (Minimum 10, nicht kälter) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, südorientiertes Fenster | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam, ca. 1× pro Monat; Substrat fast trocken halten | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Nicht frosthart (`frost_free`). Die Pflanze wird als frostempfindliche Kübel-/Zimmerpflanze frostfrei drinnen überwintert. Vor dem ersten Frost (spätestens bei nächtlichen Temperaturen nahe 10 °C, i. d. R. Oktober) ins Haus holen; im Frühjahr nach den Eisheiligen (Mitte Mai) wieder hinaus, ggf. abhärten. Im Winterquartier hell und kühl (10–18 °C) stellen und nur minimal gießen — moderat kühle, frostfreie Nächte (13–16 °C) fördern eine gesunde Ruhephase, ohne die Kälteschwelle zu unterschreiten. Die Mindesttemperatur liegt bei ~10 °C; bereits Temperaturen unter ~10 °C verursachen Kälteschäden, weshalb die Ruhephasen-Nachttemperaturen klar darüber gehalten werden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Pseudococcus spp. | Wollflecken an Blattbasis | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste bei Trockenheit | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzel-/Stängelfäule | fungal | Braun-weiche Stängelbasis | Staunässe (einzige häufige Ursache) |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Drastische Reduktion | 0 | Fäule (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen | 0 | Wollschildläuse |
| Neemöl | biological | Sprühen 0.5% | 0 | Alle Schädlinge |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit |
|----------|--------------------|--------------------|---------------------|-------------------|
| Australischer Marienkäfer (mealybug destroyer) | Cryptolaemus montrouzieri | Wollschildläuse (Pseudococcus spp., Pseudococcidae) | 2–10 | 4–8 Wochen |
| Raubmilbe (predatory mite) | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 6–10 (bis 50 bei Starkbefall) | 2–3 Wochen |

**Hinweis:** Beide Nützlinge benötigen Temperaturen über ~18 °C und ausreichende Aktivität des Schädlings; Ausbringung 1–3× im Abstand von 1–2 Wochen wiederholen. Bei Zimmerkultur ist mechanische/kulturelle Bekämpfung (§5.3) meist ausreichend; Nützlinge lohnen sich v. a. bei größeren Beständen oder im Gewächshaus. Hinweis zur Zuordnung: *Cryptolaemus* bekämpft Schmierläuse/Wollläuse (Pseudococcidae) — *Aphytis*-Schlupfwespen wären hier fachlich falsch (diese parasitieren Panzer-/Deckelschildläuse der Diaspididae, die an dieser Art nicht typisch sind).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Schwiegermutterzunge | Dracaena trifasciata | Gleiche Gattung | Flache Blätter, bunter |
| Echeveria | Echeveria elegans | Sukkulente, ähnliche Pflegeansprüche | Kompakt, für Fensterbrett |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Dracaena angolensis,"Zylindrische Sansevierie;Afrikanischer Speer;Speerpflanze;African Spear;Cylindrical Snake Plant;Sansevieria cylindrica",Asparagaceae,Dracaena,perennial,day_neutral,herb,rhizomatous,"9a;9b;10a;10b;11a;11b","Angola, tropisches Afrika",yes,5-20,20,60-180,30-90,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Sansevieria cylindrica](https://www.gardenia.net/plant/sansevieria-cylindrica-african-spear-snake-plant) — Botanische Daten
2. [NC State Extension — Dracaena angolensis](https://plants.ces.ncsu.edu/plants/dracaena-angolensis/) — Aktuelle Nomenklatur
3. [Epic Gardening — Sansevieria cylindrica](https://www.epicgardening.com/sansevieria-cylindrica/) — Kulturdaten
4. [Garden Beast — Sansevieria cylindrica](https://gardenbeast.com/sansevieria-cylindrica-guide/) — Pflegehinweise
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig — Saponine)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [ScienceDirect — Relationships between leaf succulence and Crassulacean acid metabolism in the genus Sansevieria (Asparagaceae)](https://www.sciencedirect.com/science/article/abs/pii/S0367253019304931) — Peer-reviewed Beleg für CAM-Photosynthese bei Sansevieria/Dracaena (7 von 10 untersuchten Arten CAM)
7. [EarthOne — How To Grow Dracaena angolensis](https://earthone.io/plant/dracaena%20angolensis) — Boden-pH-Vorzug (6.5), Lichtbedarf, Trockentoleranz
8. [PlantCareToday — Snake Plant Soil / Sansevieria Cylindrica Care](https://plantcaretoday.com/sansevieria-cylindrica.html) — Substrat, pH (leicht sauer 6.0–6.5), Staunässe/Wurzelfäule, Lichtansprüche
9. [Sansevieria Plant Botanical Guide — Taxonomy & Leaf Science](https://sansevieriaplant.com/blog/sansevieria-plant-botanical-guide/) — Salz-/Trockentoleranz, flaches Rhizom-Wurzelsystem, CAM-Trockenadaption
10. [Gardenia.net — Snake Plant Care & Best Varieties](https://www.gardenia.net/guide/snake-plant-care-best-varieties) — Salztoleranz, Küstentauglichkeit
11. [GardenBeast — Sansevieria Cylindrica Guide (African Spear)](https://gardenbeast.com/sansevieria-cylindrica-guide/) — Überwinterung, Mindesttemperatur 10 °C, Winterruhe, kühle Nachttemperaturen
12. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Wollläuse, Ausbringrate/Etablierung
13. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Nützling gegen Spinnmilben, Ausbringrate
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
