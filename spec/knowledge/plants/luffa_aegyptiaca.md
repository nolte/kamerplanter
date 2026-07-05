# Schwammgurke -- Luffa aegyptiaca

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Plantura, fryd.app, Floraspora, Freudengarten, Lubera, OMAFRA, NC State Extension, Missouri Botanical Garden, ForwardPlant

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Luffa aegyptiaca | `species.scientific_name` |
| Volksnamen (DE/EN) | Schwammgurke; Luffagurke; Schwammkürbis; Luffa; Loofah; Sponge Gourd; Smooth Luffa; Egyptian Cucumber | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` -> `botanical_families.name` |
| Gattung | Luffa | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | — (einjährig; keine mehrjährige Blühstrategie) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | short_day (Bluetenbildung wird durch kuerzerenr Tage ausgeloest; tropischer Ursprung) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 (Cucurbitaceae/Gurkengewaechse sind C3-Pflanzen) | `species.photosynthesis_type` |
| GDD-Basistemperatur (degC) | 10 (Wuchs-GDD-Basis der Hauptwuchsphase, analog Cucurbitaceae/Gurke; unterhalb ~10 degC praktisch keine Entwicklung) | `species.base_temp` |
| Dormanz erforderlich | false (einjaehrige tropische Art ohne Ruhephase) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (tropischer Ursprung; Bluete kurztag-gesteuert, kein Kaeltebedarf) | `lifecycle_configs.vernalization_required` |
| Kritische Tageslaenge (h) | 12 (echter Kurztagblueher; weibliche Blueten werden unterhalb ~12 h gefoerdert) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Sehr frostempfindlich. Braucht 150--200 frostfreie Tage fuer Schwammreife. In Mitteleuropa (Zone 7--8) nur im Gewaechshaus oder bei sehr fruehzeitiger Vorkultur (Feb/Maerz) erfolgreich kultivierbar. | `species.hardiness_detail` |
| Heimat | Tropisches Asien (Indien, Suedostasien); Nordafrika | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible (jung); fiber_plant; sustainable_sponge; ornamental | `species.traits` |

**Verwendung:** Junge Fruechte (unter 15 cm) sind als Gemuese essbar (asiatische Kueche). Ausgereifte Fruechte liefern den natuerlichen Luffa-Schwamm (Fasergeruest = Xylem). Die Pflanze ist damit Nahrungspflanze UND Industrierohstoff.

**Synonym:** *Luffa cylindrica* (L.) Roem. — weitgehend synonym; POWO bevorzugt *L. aegyptiaca*; in wissenschaftlichen Quellen weiterhin als *L. cylindrica* anzutreffen.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai. Sehr fruehe Vorkultur entscheidend fuer Schwammreife!

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8--10 (Aussaat Februar/Maerz -- sehr frueh; lange Kulturdauer!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (nur in Zone 8+; Boden mind. 20 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 (nur in warmen Gebieten oder Gewaechshaus) | `species.direct_sow_months` |
| Erntemonate | 9; 10 (fuer Schwamm: Fruechte muessen vollstaendig ausreifen und trocknen) | `species.harvest_months` |
| Bluetemonate | 7; 8 (Kurztagspflanze; bluetet erst bei abnehmender Taglaenge) | `species.bloom_months` |

**Kritischer Hinweis:** In Mitteleuropa bluetet Luffa oft erst im August/September (wenn Tage kuerzter werden), was die Zeit fuer Fruchtentwicklung und Schwammreife stark einschraenkt. Fuer Schwammernte unbedingt Gewaechshaus oder Folientunnel verwenden.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate (Waermekeimer; empfindlich beim Verpflanzen; lange Kulturdauer) | `species.propagation_difficulty` |

**Keimhinweise:**
- Samen vor Aussaat 24--48 Stunden in lauwarmem Wasser einweichen (foerdert Keimung)
- Optimale Keimtemperatur: 24--30 degC (Heizmatte empfohlen)
- Keimdauer: 7--14 Tage (nach Einweichen schneller)
- Einzelaussaat in 9-cm-Toepfe oder Jiffy-Toepfe (keine Pikierung)
- Saattiefe: 1.5--2 cm; Samen seitlich legen
- Substrat: Locker, gut drainiert, naehrstoffarm

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (junge Fruechte essbar; reife Fruechte nicht mehr) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaf; seed (Saatgut enthaelt Saponine -- nicht in grossen Mengen essen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Cucurbitacine (Blaetter; Samen); Luffin (Samen -- Ribosom-inhibierendes Protein; nicht direkt giftig bei normaler Exposition) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Trichome auf Blaettern und Stengeln verursachen Hautreizungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7; 8 | `species.pruning_months` |

**Triebfuehrung:**
- Haupttrieb bis 2--3 m aufleiten; dann entspitzen (foerdert Seitentriebe)
- Seitentriebe tragen weibliche Blueten (Hauptertragstraeger)
- Seitentriebe auf 3--4 Blaetter kuerzen
- Im Gewaechshaus (Mitteleuropa): Bluetentriebe ab August/September maximieren fuer Fruchtansatz

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in 15--20 L Behaelter; aber Rank-Konstruktion bis 3 m noetig) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15--30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 35 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 200--600 (rankende Kletterpflanze; braucht Kletterstruktur) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100--300 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60--100 in der Reihe; 150--200 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no (zu grosse Wuchshoehe; zu wenig Licht; Bestaeubungsprobleme) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Suedbalkon mit starker Rank-Konstruktion; grosse Kuebelanlage) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (in Mitteleuropa zwingend fuer Schwammreife; Kalthaus mind. Mai--Oktober) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Luffa ist aggressiver Kletterer; braucht Drahtgeruest oder Ranknetz 3--5 m hoch) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, lockere, sehr gut drainierte Erde mit hohem Kompostanteil (30%). Sandige Anteile foerdern Drainage. pH 6.5--7.5. | -- |

### 1.7 Umgebungs-Physiologie & Standortqualitaet

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | 30 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | 60 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun (mind. 6 h, optimal 8--10 h direkte Sonne) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 45--90 (Hauptwurzeln flach, aber bei tiefem Giessen tiefreichend; Boden 30--45 cm lockern) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz | moderate (bildet bei Flutung Aerenchym/Adventivwurzeln, mag aber keine Dauer-Staunaesse; Faeulnisgefahr) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant (als Veredelungsunterlage salztolerant; reduziert Na-Transport in den Spross) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN -- keine belegten Maas-Hoffman-Schwellenwerte (a) fuer Luffa aegyptiaca verfuegbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN -- keine belegten Maas-Hoffman-Slope-Werte (b) fuer Luffa aegyptiaca verfuegbar --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min--max) | 6.0--7.5 | `species.soil_ph_preference` |

**Hinweis (Lichtkompensationspunkt):** Wert als Spanne aus Cucurbitaceae-Analogie (Gurken-Bestand: gemessener Kompensationspunkt ~32--86 umol/m2/s); fuer die einzelne, sonnenadaptierte Luffa-Pflanze konservativ 30--60 umol/m2/s angesetzt (reiner Kompensationspunkt = Netto-Photosynthese 0, KEINE Saettigungswerte). Lichtsaettigung liegt deutlich hoeher (vgl. §2.2 PPFD-Ziele).

**Hinweis (Salztoleranz):** Klasse aus Veredelungsstudien (Luffa als salztolerante Unterlage) abgeleitet; quantitative ECe-Schwelle/Slope fehlen in der Literatur und sind daher als DATEN FEHLEN markiert. Bezugsgroesse waere Substrat-ECe (Saettigungsextrakt), nicht die Giesswasser-EC.

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 24 (§1.3; Gardenersbasics/Jerra's Garden bestätigen 24–30°C bzw. 70–90°F) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 30 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1.5 (§1.3: 1,5–2 cm, seitlich gelegt) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (§1.3: 7–14 Tage nach Einweichen; Gardenersbasics/Superseeds bestätigen 7–10 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (bei kühler, trockener Lagerung 3–5 Jahre) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light (zwei artspezifische Studien zu *Luffa cylindrica*/*aegyptiaca* zeigen, dass Dunkelheit die Keimung/den Sämlingsvigor hemmt) | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak, scarification (24–48 h Einweichen Standard; bei hartschaligen/"stubborn" Samen zusätzliches Anritzen der Samenschale empfohlen) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 97–106 (großes, flaches Kürbisgewächs-Samenkorn, 14×7 mm) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Einzelaussaat je Pflanzstelle/Topf (§1.6: 60–100 cm in der Reihe, 150–200 cm Reihenabstand) statt Flächen-/Reihensaat; kein sinnvoller Flächendichte-Wert --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
1. §1.3 dieses Steckbriefs (bereits zitierte Quellen: Keimtemperatur 24–30°C, Saattiefe 1,5–2 cm, Keimdauer 7–14 Tage nach Einweichen) — Cross-Check
2. [Gardeners Basics — How to Start Luffa Seeds Indoors](https://www.gardenersbasics.com/tools/blog/how-to-start-luffa-seeds-indoors-gardeners-basics) — Keimtemperatur 75–85°F (24–29°C), Keimdauer 7–21 Tage
3. [Jerra's Garden — How to Grow & Quickly Germinate Luffa](https://www.jerrasgarden.com/blogs/gardening-info-growing-guides/how-to-grow-quickly-germinate-luffa-seeds) — Einweichen 24 h, Anritzen der Samenschale bei hartnäckigen Samen (Skarifikation)
4. [Study of Effect of Temperature, Water, Light and Darkness on Seed Germination in Luffa Cylindrical L.](https://www.academia.edu/97099183/Study_of_Effect_of_Temperature_Water_Light_and_Darkness_on_Seed_Germination_in_Luffa_Cylindrical_L) — Dunkelheit hemmt Keimung/Sämlingsvigor (positiv photoblastisch)
5. [The Effects of Light and Temperature on Germination and Growth of Luffa aegyptiaca (ResearchGate)](https://www.researchgate.net/publication/230356554_The_Effects_of_Light_and_Temperature_on_Germination_and_Growth_of_Luffa_aegyptiaca) — Optimaltemperatur 25–30°C, Lichteinfluss auf Keimung
6. [SurvivalGardenSeeds — Luffa Gourd Seeds](https://survivalgardenseeds.com/products/luffa-or-loofah-seed-for-planting) — Keimfähigkeitsdauer 3–5 Jahre bei kühler, trockener Lagerung
7. [Kellogg Garden Organics — How to Grow Luffa Plants](https://kellogggarden.com/blog/gardening/how-to-grow-luffa-plants/) — Keimfähigkeitsdauer, Saatgutlagerung
8. Rani, N. et al. — [SEEDS AND SEEDLINGS CHARACTERISTICS OF SPONGE GOURD (LUFFA CYLINDRICA (L.) ROEM.)](https://www.researchgate.net/publication/319910758_SEEDS_AND_SEEDLINGS_CHARACTERISTICS_OF_SPONGE_GOURD_LUFFA_CYLINDRICA_L_ROEM) — 100-Korn-Masse 10,59 g (≈ TKG 105,9 g), Samengröße 14×7 mm
9. [Engineering properties of luffa (L. Cylindrica) seed relevant to the processing machineries](https://www.researchgate.net/publication/325284239_Engineering_properties_of_luffa_L_Cylindrica_seed_relevant_to_the_processing_machineries) — Einzelsamenmasse Ø 97,3 mg (≈ TKG 97,3 g), Gewichtsverteilung
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 7--14 | 1 | false | false | low |
| Saemling (seedling) | 21--35 | 2 | false | false | low |
| Vegetativ (vegetative) | 42--70 | 3 | false | false | medium |
| Bluete (flowering) | 21--35 | 4 | false | true (jung-Gemuese) | medium |
| Fruchtentwicklung (fruit_development) | 30--50 | 5 | false | true (jung-Gemuese) | medium |
| Trocknung/Schwamm-Reife (sponge_ripening) | 21--42 | 6 | true | true (Schwamm) | high |

**Hinweis:** Die Kulturdauer von Aussaat bis Schwamm-Ernte betraegt 150--200 Tage. Fuer die Gemuese-Nutzung (junge Fruechte) ist Ernte bereits ab Fruchtentwicklung nach ca. 80--100 Tagen moeglich.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer; mit Erde bedecken) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--32 (Heizmatte unbedingt noetig!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 22--26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.7 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 (feuchteliebende Keimphase; Schwelle deutlich ueber dem Zielkorridor) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 26--30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht/Vollsonne; kein Schattenwert) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (feucht; keine Staunaesse) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (lange Tage halten Pflanze in vegetativem Wachstum) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 24--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 27--30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht/Vollsonne) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 (Vollsonne; Luffa ist sehr lichtbeduerftigt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 22--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (lange Tage = rein vegetativ; so lange wie moeglich fuer Biomasse-Aufbau) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 26--35 (optimal 28--32; Waermebedarf sehr hoch!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 20--25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 (oberer Zielwert + ca. 0.4 kPa; stomataerer Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 28--32 (Netto-Photosynthese maximal; Abfall ab ~36 degC) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Vollsonne/Gewaechshaus) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 600--1200 (Gewaechshaus-CO2-Anreicherung sinnvoll) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--13 (kuerzere Tage loesen Bluete aus -- ab Juli/August in Mitteleuropa automatisch) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.2 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 28--32 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Vollsonne/Gewaechshaus) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Bestaeubungshinweis:** Weibliche Blueten (mit kleiner Frucht am Ansatz) oeffnen sich morgens und sind nur wenige Stunden empfaengnisbereit. Im Gewaechshaus manuelle Bestaeubung oder Hummeln unbedingt noetig.

#### Phase: Fruchtentwicklung (fruit_development)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 18--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 26--35 (hohe Waerme foerdert Faserbildung im Inneren) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--2.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 28--32 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Vollsonne/Gewaechshaus) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 600--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Schwamm-Reife (sponge_ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--13 (Herbst; abnehmende Tage okay) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--55 (trocken fuer Schwammtrocknung!) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45--60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.5--2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.9 (oberer Zielwert + ca. 0.4 kPa; trockene Reifephase, hohe Toleranz) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 26--30 (kuehlere Herbstphase) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Vollsonne/Gewaechshaus) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7--14 (wenig giessen; Fruechte sollen abtrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Ernte-Indikatoren (Schwamm):**
- Schale braun und trocken; rasselt beim Schuetteln (Samengeraeusch)
- Frucht leicht; Innen-Faser sichtbar wenn man auf die Schale drueckt
- Schale loest sich leicht von Fasergeruest
- Gesamtgewicht der Frucht deutlich reduziert gegenueber gruener Phase
- Bei Kalteinbruch Fruechte ernten und weitertocknen lassen (drinnen)

**Schwamm-Aufbereitung:** Schale in kaltem Wasser einweichen (2--4 h); dann abschaelen; Samen ausspuelen; ggf. bleichen (H2O2 3% fuer 30 min); trocknen. Fertig!

### 2.3 Naehrstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 (Spalten Mn/Zn/Cu/Mo ergaenzt; Standard-Cucurbitaceae-Mikronaehrstoffbereiche) -->
| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0-0-0 | 0.0 | 6.5--7.5 | -- | -- | -- | -- | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.8--1.2 | 6.5--7.0 | 80 | 30 | 20 | 2 | 0.5 | 0.2 | 0.05 | 0.05 |
| Vegetativ | 3-1-2 | 1.4--2.2 | 6.5--7.0 | 120 | 50 | 30 | 3 | 0.8 | 0.3 | 0.08 | 0.05 |
| Bluete | 2-2-3 | 1.8--2.6 | 6.5--7.0 | 150 | 60 | 30 | 3 | 0.8 | 0.3 | 0.08 | 0.05 |
| Fruchtentwicklung | 1-2-4 | 2.0--3.0 | 6.5--7.0 | 150 | 60 | 35 | 2 | 1.0 | 0.4 | 0.1 | 0.05 |
| Schwamm-Reife | 0-1-2 | 0.8--1.5 | 6.5--7.0 | 80 | 40 | -- | 1 | 0.5 | 0.2 | 0.05 | 0.05 |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 7--14 Tage | Keimblaetter entfaltet |
| Saemling -> Vegetativ | manual | 21--35 Tage | 3--4 echte Blaetter; Auspflanzen nach Frost |
| Vegetativ -> Bluete | event_based | -- | Taglaenge < 13 h (automatisch ab Juli/August in Mitteleuropa) |
| Bluete -> Fruchtentwicklung | event_based | -- | Bestaeubung; Fruchtansatz sichtbar |
| Fruchtentwicklung -> Schwamm-Reife | time_based / conditional | 30--50 Tage | Frucht > 30 cm; Schwarz-gelbe Schale |
| Schwamm-Reife -> Ernte | conditional | -- | Schalen-Trocknung und Rasseln |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Gewaechshaus/Topf)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag | Canna | supplement | Ca+Mg | 0.12 | 2 | alle |
| Terra Vega | Canna | base | 3-1-4 | 0.18 | 3 | Vegetativ |
| Terra Flores | Canna | base | 2-2-4 | 0.18 | 3 | Bluete; Frucht |
| PK 13/14 | Canna | booster | 0-13-14 | 0.10 | 5 | Fruchtentwicklung |

#### Organisch (Freiland/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (tief eingraben) | heavy_feeder |
| Hornspäne | Oscorna | organisch (N-Langzeit) | 100--150 g/m2 | Mai (Auspflanzen) | Vegetativphase |
| Brennnesseljauche | Eigenerzeugung | organisch (N) | 1:10, 2 L/Pflanze | Jun--Jul alle 14 Tage | Vegetativ |
| Beinwelljauche | Eigenerzeugung | organisch (K) | 1:10, 2 L/Pflanze | Jul--Sep alle 14 Tage | Bluete; Frucht |
| Tomaten-/Kuerbisduenger | Neudorff / COMPO BIO | organisch | 30--50 ml / 10 L | woechentlich Jul--Sep | heavy_feeder |

### 3.2 Duengungsplan

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base (ml/L) | Booster (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|-------------|----------------|----------|
| 1--2 | Saemling | 0.6--1.0 | 6.5 | 0.2 | 0.4 | -- | Schwache Duengung; nur Keimsubstrat |
| 3--6 | Vegetativ (Vorkultur) | 1.2--1.8 | 6.5 | 0.4 | 0.8 Vega | -- | Aufbau starker Pflanzenmasse |
| 7--12 | Vegetativ (Freiland/GWH) | 1.8--2.2 | 6.5 | 0.5 | 1.0 Vega | -- | Maximale N-Versorgung |
| 13--15 | Bluete | 1.8--2.6 | 6.5 | 0.5 | 0.8 Flores | -- | Auf Flores umstellen |
| 16--20 | Fruchtentw. | 2.0--3.0 | 6.5 | 0.5 | 0.8 Flores | 0.3 PK | Kali-Boost fuer Faserbildung |
| 21--25 | Schwamm-Reife | 0.8--1.5 | 6.5 | 0.2 | 0.4 Flores | -- | Stark reduzieren |

### 3.3 Mischungsreihenfolge

1. Wasser temperieren (22--26 degC; Luffa mag warmes Wasser!)
2. CalMag (VOR Sulfaten!)
3. Base A (Terra Vega oder Flores A)
4. Base B (Terra Flores B)
5. PK-Booster (nur in Fruchtphase)
6. pH-Korrektur (Luffa: pH 6.5--7.5; IMMER zuletzt)

### 3.4 Besondere Hinweise zur Duengung

- **Waerme = Wachstum:** Luffa ist einer der waermebeduerftigen Kulturpflanzen. Unterhalb 20 degC praktisch kein Wachstum; unterhalb 15 degC Stresssymptome. Naehrstoffgaben erst bei ausreichender Waerme wirksam.
- **Ab Bluete Kalium erhoehen:** Kalium foerdert die Faserbildung im Fruchtinneren -- essentiell fuer Schwammqualitaet.
- **Erste 3 Wochen organisch:** In der Anzucht (Keimung bis erste Wochen Saemling) reichen sehr geringe organische Konzentrationen. Zu viele Naehrstoffe in der Fruehphase foerdern Wurzelfaeule.
- **CO2-Anreicherung im GWH:** Luffa reagiert sehr gut auf erhoehte CO2-Konzentrationen (800--1200 ppm) mit stark verbessertem Wachstum -- dies macht die Pflanze interessant fuer professionelle Gewaechshaus-Kultur.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | herb_tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--4 (gleichmaessig feucht; Staunaesse vermeiden) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Warmes Wasser (> 20 degC). Kaltes Wasser stresst die Pflanze stark! Blaetter trockenhalten. Keine Staunaesse. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7--10 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; 1x pikieren, 1x Endtopf) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Aussaat | Samen einweichen (24 h); Einzeltoepfe; Heizmatte 28 degC | hoch |
| Maerz | Vorkultur | In groessere Toepfe umsetzen; Licht 14--16 h; Waerme halten | hoch |
| Apr | Weitertopfen | In 15-L-Toepfe; Rank-Konstruktion vorbereiten | hoch |
| Mai | Auspflanzen | Erst nach Eisheiligen und Bodentemperatur > 20 degC | hoch |
| Jun | Aufleiten | Triebe aufleiten; Haupttrieb nach 2--3 m entspitzen | hoch |
| Jul | Bluete/Bestaeubung | Manuelle Bestaeubung morgens; Hummeln einsetzen | hoch |
| Aug | Fruchtentwicklung | Fruechte am Netz stuetzen (koennen sehr schwer werden!) | hoch |
| Sep | Schwamm-Reife | Giessen reduzieren; Truechte trocknen lassen | hoch |
| Okt | Ernte | Vor Frost: alle Fruechte ernten; auch halbtrockene aufbewahren | hoch |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Gurkenkaefer | Diabrotica spp. | Lochfrass; gelbe-braune Flecken; Virusvektoren | leaf | vegetative; flowering | medium |
| Spinnmilbe | Tetranychus urticae | Gespinste; stippenartige Blaettervergilbung | leaf | vegetative; fruit_development | medium |
| Blattlaeuse | Aphis gossypii | Honigtau; Triebdistortion; Virusvektoren | leaf; shoot | seedling; vegetative | easy |
| Thripse | Frankliniella occidentalis | Silbrige Blattflecken; Bluetenschaeden | flower; leaf | flowering | medium |
| Kuerbiskaefer | Acalymma vittatum | Lochfrass; Blaetter | leaf | vegetative | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Podosphaera xanthii) | Weisser Belag auf Blaettern; Blaetter sterben ab | dry_warm; poor_airflow; shade | 5--10 | vegetative; flowering |
| Falscher Mehltau | oomycete (Pseudoperonospora cubensis) | Gelbliche Flecken; grauer Belag Blattunterseite | cool_wet; high_humidity | 4--8 | vegetative; fruit_development |
| Fusarium-Welke | fungal (Fusarium oxysporum) | Welke; Stengel-Verbräunung; Pflanze stirbt ab | contaminated_soil | 14--28 | vegetative; fruit_development |
| Alternaria-Blattflecken | fungal (Alternaria cucumerina) | Braun-schwarze konzentrische Flecken | warm_wet | 3--7 | vegetative; fruit_development |
| Zucchini-Gelbmosaik-Virus (ZYMV) | viral | Mosaikgelbe Blaetter; Fruchtdeformationen | aphid_vectors | 7--14 | alle |
| Phytophthora-Faeule | oomycete | Stengel- und Wurzelfaeule | waterlogging | 3--7 | seedling; vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10--20 | 10--14 |
| Aphidoletes aphidimyza | Blattlaeuse | 5--10 | 14--21 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Bombus terrestris | Bestaeubung | 1 Volk / 150--200 m2 | -- |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoelextrakt | biological | Azadirachtin | 0.3--0.5% abends spruehen | 3 | Spinnmilben; Blattlaeuse; Thripse |
| Netzschwefel | chemical | Schwefel | Stauben / Spruehen | 14 | Echter Mehltau |
| Kaliumbicarbonat | approved_organic | Kaliumbicarbonat | 0.5--1.0% spruehen | 0 | Mehltau-Praevention |
| Kupfer-Fungizid | approved_organic | Kupfer | 0.3% spruehen nach Regen | 7 | Falscher Mehltau; Alternaria |
| Tropfbewaesserung | cultural | -- | Blaetter trocknen | 0 | Mehltau-Praevention |
| Belichtungsoptimierung | cultural | -- | Schatten minimieren | 0 | Mehltau-Praevention (Licht kritisch!) |

### 5.5 Resistenzen der Art

<!-- DATEN FEHLEN -- Keine zuverlaessigen Daten zu sortenspezifischen Resistenzen bei Luffa aegyptiaca verfuegbar -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kuerbisgemaechse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Leguminosen (Bohnen; Erbsen); Gruenduengung; Salat |
| Empfohlene Nachfrucht | Feldsalat; Moehren; Zwiebeln (Schwachzehrer) |
| Anbaupause (Jahre) | 3--4 Jahre (Fusarium und Bodenpilze; gleiche Standorte vermeiden) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.7 | Windschutz; Kletterhilfe; aehnliche Waermeansprueche | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Ablenkung; Bestaeubungsfoerderung | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeubungsanlocken | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.6 | Thripse-Abwehr; Aromafoerderung | `compatible_with` |
| Buschbohnen | Phaseolus vulgaris | 0.6 | N-Fixierung; Bodenbeschattung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Andere Cucurbitaceae | Cucumis sativus; Cucumis melo; Cucurbita spp. | Gleiche Schaderreger; Mehltau; Blaettlaeuse als Virusvektoren; Bestaeubungskonkurrenz | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gemeinsame Bodenpilze (Fusarium; Phytophthora) | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung durch Fenchel-Exsudate | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Cucurbitaceae | `shares_pest_risk` | Echter Mehltau (Podosphaera xanthii); Falscher Mehltau; ZYMV; Spinnmilben; Gurkenkaefer; Fusarium | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Luffa aegyptiaca |
|-----|-------------------|-------------|-------------------------------------|
| Rippen-Luffa | Luffa acutangula | Gleiche Gattung; aehnliche Kultur | Essbarer (vor allem als Gemuese); kuerzeere Kulturdauer |
| Gurke | Cucumis sativus | Gleiche Familie; Kletterpflanze | Kuerzeere Kulturdauer; weniger Waermebedarf; bekannter im Anbau |
| Zucchini | Cucurbita pepo | Gleiche Familie | Viel einfacher; kuerzere Kulturdauer; kein Spezial-Equipment |

---

## 8. Sorten / Cultivars

| Sorte | Typ | Kulturdauer (Tage) | Fruchtlaenge (cm) | Verwendung | Besonderheiten |
|-------|-----|--------------------|-------------------|-----------|----------------|
| Luffa aegyptiaca Standard | Grundsorte | 150--180 | 30--60 | Schwamm; Gemuese (jung) | Klassischer Anbau; grosse Schwaemme |
| Vietnamese Early | Fruehsorte | 120--140 | 25--40 | Gemuese; Schwamm | Kuerzere Kulturdauer; fuer Mitteleuropa besser geeignet |
| Smooth Luffa (Chinese) | Asiatischer Typ | 130--160 | 30--50 | Gemuese bevorzugt | Zartes Fleisch; haeufig in der asiatischen Kueche |
| Short Luffa | Kompaktsorte | 120--150 | 15--25 | Gemuese und Schwamm | Kompaktere Fruechte; einfachere Handhabung |
| Goa Bean Luffa | Tropischer Typ | 150--180 | 40--70 | Schwamm | Sehr grosser Schwamm; wenig praktisch fuer Mitteleuropa |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity
Luffa aegyptiaca,Schwammgurke;Luffagurke;Luffa;Loofah;Sponge Gourd,Cucurbitaceae,Luffa,annual,short_day,vine,fibrous,7a;7b;8a;8b;9a;9b;10a;10b,-0.1,Tropisches Asien; Nordafrika,limited,15,35,400,200,80,no,limited,true,true,heavy_feeder,tender
```

---

## Quellenverzeichnis

1. [Plantura -- Luffagurke](https://www.plantura.garden/gemuese/gurken/luffagurke) -- Anbau; Pflege; Ernte in Mitteleuropa
2. [fryd.app -- Schwammgurke](https://fryd.app/lexikon/pflanzen/6864-schwammgurke) -- Sorten; Companion Planting
3. [Floraspora -- Luffa-Gurken anbauen](https://www.floraspora.de/post/luffa-gurke-anbauen-pflegen-ernten-verarbeiten-natuerliche-schwaemme) -- Anbauanleitung; Schwammaufbereitung
4. [Freudengarten -- Luffa anbauen](https://freudengarten.de/show/1305/luffa-schwammgurke-anbauen-pflanzen-pflegen) -- Praxis-Tipps; Vorkultur
5. [Lubera -- Luffa selber anbauen](https://www.lubera.com/ch/gartenbuch/luffa-gurken-selber-anbauen-p5196) -- Kultivierung; Ernte
6. [OMAFRA -- Luffa](https://www.omafra.gov.on.ca/CropOp/en/spec_veg/cucurbits/luffa.html) -- Ontario Ministry of Agriculture; Professioneller Anbau
7. [NC State Extension -- Luffa aegyptiaca](https://plants.ces.ncsu.edu/plants/luffa-aegyptiaca/) -- Botanische Grunddaten; Taxonomie
8. [Missouri Botanical Garden -- Luffa aegyptiaca](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=364305) -- Botanische Klassifikation
9. [ForwardPlant -- Luffa aegyptiaca Care Guide](https://www.forwardplant.com/plant-info/luffa-aegyptiaca/) -- Schädlinge; Krankheiten; Pflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
10. [J. Japan. Soc. Hort. Sci. -- Photoperiodic Responses Controlling Sex Expression of Flowers in Luffa and Lagenaria](https://www.jstage.jst.go.jp/article/jjshs1925/55/3/55_3_303/_article/-char/en) -- Kurztag-Reaktion; kritische Tageslaenge ~12 h fuer weibliche Blueten
11. [Oregon State CROPTIME / Pest Prophet -- Cucumber Growing Degree Day Model](https://blog.pestprophet.com/how-to-use-the-cucumber-growing-degree-day-model/) -- GDD-Basistemperatur 50 degF / 10 degC fuer Gurkengewaechse
12. [Penn State Extension / GreenUpside -- Lowest Temperature Cucumber Plants Can Tolerate](https://greenupside.com/what-is-the-lowest-temperature-cucumber-plants-can-tolerate/) -- Wachstumsverlangsamung unterhalb 10 degC (Basistemperatur-Bestaetigung)
13. [PMC -- Photosynthetic contribution and characteristics of cucumber stems and petioles](https://pmc.ncbi.nlm.nih.gov/articles/PMC8493697/) -- Cucurbitaceae als C3-Pflanzen
14. [PMC -- The complex character of photosynthesis in cucumber fruit](https://pmc.ncbi.nlm.nih.gov/articles/PMC5441898/) -- C3-Photosyntheseweg bei Gurke (Familien-Beleg)
15. [Annals of Botany -- Photosynthesis of Stands of Tomato, Cucumber and Sweet Pepper](https://academic.oup.com/aob/article-abstract/73/4/353/2587261) -- Lichtkompensationspunkt Gurken-Bestand ~32--86 umol/m2/s
16. [Frontiers in Plant Science -- Limiting Sites of Photosynthesis under Heat Stress in Cucumber and Luffa Rootstock](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2016.00746/full) -- Photosynthese-Optimum ~28--32 degC; Abfall ab 36 degC
17. [ScienceDirect -- Luffa rootstock enhances salt tolerance by reducing sodium transport](https://www.sciencedirect.com/science/article/abs/pii/S0269749122017353) -- Salztoleranz-Klasse (moderately_tolerant); Na-Transport-Reduktion
18. [PubMed -- Cortical Aerenchyma formation in Luffa cylindrica subjected to soil flooding](https://pubmed.ncbi.nlm.nih.gov/17921518/) -- Staunaesse-Adaption (Aerenchym/Adventivwurzeln) = moderate Toleranz
19. [Epic Gardening -- How to Plant, Grow, and Care for Luffa](https://www.epicgardening.com/growing-luffa/) -- Vollsonne; Boden 30--45 cm lockern (Wurzeltiefe)
20. [Osceola CSA -- Growing and Caring for Luffa Gourds](https://www.osceolacsa.farm/post/climbing-to-new-heights-how-to-grow-and-care-for-luffa-gourds) -- Boden-pH 6.0--7.5; Vollsonne 6--10 h
21. [Haifa Group -- Crop Guide: Nutrients for Cucumber](https://www.haifa-group.com/cucumber-0/crop-guide-nutrients-cucumber) -- Cucurbitaceae-Mikronaehrstoffbereiche Mn/Zn/Cu/Mo (ppm)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
