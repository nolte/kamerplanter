# Petersilie -- Petroselinum crispum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, Hortipendium, Wikipedia, gartenratgeber.net, garten-wissen.com, hauenstein-rafz.ch, schadbild.com, Koraylights, MDPI Agronomy, Michigan State University, Produce Grower

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Petroselinum crispum | `species.scientific_name` |
| Volksnamen (DE/EN) | Petersilie; Glatte Petersilie; Krause Petersilie; Peterle; Parsley; Garden Parsley | `species.common_names` |
| Familie | Apiaceae | `species.family` -> `botanical_families.name` |
| Gattung | Petroselinum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | biennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | monocarpic (blüht einmal, dann Absterben) | `lifecycle_configs.flowering_strategy` |
| Anbau-Zyklustyp (cultivation cycle type) | biennial | `lifecycle_configs.cultivation_cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- Bluetenbildung im 2. Jahr durch lange Tage ausgeloest; Vernalisation noetig) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 (krautige Apiaceae; weder C4 noch CAM) | `species.photosynthesis_type` |
| GDD-Basistemperatur (Wuchs, degC) | 4 (Tbase fuer den vollen Kulturzyklus; Tupper 27 degC; kuehlliebende Kultur -- NICHT der Keim-Basiswert) | `species.base_temp` |
| Dormanz erforderlich | false (Winterruhe ist umweltbedingt, nicht obligat; in Mitteleuropa oft einjaehrig als Blattkultur ohne echte Dormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Kaeltereiz fuer Bluetenbildung im 2. Jahr) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 42--56 (6--8 Wochen < 10 degC) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (h) | 14 (Langtagblueher -- Bluetenauslösung nach Vernalisation bei Tageslaengen > ca. 14 h) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | moderate | `species.frost_sensitivity` |
| Winterhaerte-Detail | Zweijaerig. Uebersteht leichte Froeste bis -8 degC mit Winterschutz (Reisig, Vlies). Im ersten Jahr Blattrosette, im zweiten Jahr Bluetenstiel. In Mitteleuropa oft als einjaehrige Blattkultur angebaut. Glatte Petersilie ist etwas winterhaerter als krause. | `species.hardiness_detail` |
| Heimat | Mittelmeerraum (Marokko, Algerien, Tunesien, Suedeuropa) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium (Mittelzehrer) | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8--10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat bereits ab Maerz moeglich, da Samen kaeltetolerant) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 6; 7 | `species.direct_sow_months` |
| Erntemonate | 5; 6; 7; 8; 9; 10; 11 | `species.harvest_months` |
| Bluetemonate | 6; 7 (nur im 2. Jahr) <!-- Quelle: growing-phase-auditor 2026-07 -- Korrektur von '6;7;8' auf '6;7'; 3 unabhaengige Quellen (garten-wissen.com, Kiepenkerl, NC State Extension/Missouri Botanical Garden) datieren die Bluete der Kulturpetersilie im 2. Jahr uebereinstimmend auf Juni/Juli, keine belegt eine Fortdauer bis August; siehe Quellen 21-23 --> | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | medium (langsame, unregelmaessige Keimung) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 18--22 degC
- Minimale Keimtemperatur: 5 degC (sehr langsame Keimung)
- Keimdauer: 14--28 Tage (notorisch langsam! Geduld noetig)
- **Lichtkeimer** -- Samen nur leicht mit Erde bedecken (max. 0.5 cm) oder nur andruecken
- Saatgut vor der Aussaat 24 Stunden in lauwarmem Wasser einweichen (beschleunigt die Keimung um ca. 7 Tage)
- Substrat gleichmaessig feucht halten, nicht austrocknen lassen
- Abdeckung mit Vlies oder Folie haelt die Feuchtigkeit
- Petersilie enthaelt keimhemmende Stoffe in der Samenschale (Furanocumarine) -- daher die lange Keimdauer

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (in groesseren Mengen) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (in groesseren Mengen) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (als Kuechenkraut in normalen Mengen unbedenklich) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaf; stem; seed (Samen enthalten die hoechste Konzentration) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Furanocumarine (Psoralen, Bergapten, Xanthotoxin) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (Photosensibilisierung bei hohen Dosen; fuer Menschen als Kuechenkraut unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | true (Furanocumarine koennen bei intensivem Hautkontakt + Sonnenlicht photoallergische Reaktionen ausloesen -- Wiesendermatitis) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Petroselinum crispum als giftig fuer Hunde, Katzen und Pferde. Toxische Prinzipien: Furanocumarine. Klinische Symptome: Photosensibilisierung (Sonnenbrand, Dermatitis). In normalen kulinarischen Mengen fuer Menschen unbedenklich. Schwangere sollten grosse Mengen Petersilie meiden (uterustonisierend).

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7; 8; 9; 10 | `species.pruning_months` |

Hinweis: Regelmaessiges Ernten der aeusseren Blaetter foerdert buschiges Nachwachsen. Immer die aeusseren Stiele zuerst ernten, das Herz (innere Triebe) stehen lassen. Im zweiten Jahr Bluetenstaende sofort entfernen, wenn Blatternte weiter gewuenscht wird (nach der Bluete werden die Blaetter bitter und hartfaserig).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (klassische Fensterbank- und Balkonpflanze) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 (Pfahlwurzel!) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 25--40 (1. Jahr), 60--90 (2. Jahr mit Bluetenstiel) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20--30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20--25 | `species.spacing_cm` |
| Indoor-Anbau | yes (sonnige Fensterbank, ganzjaehrig moeglich; Zusatzbelichtung im Winter empfohlen) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (sonniger bis halbschattiger Standort) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freiland und Topf genuegen) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose Kraeutererde, gut durchlaessig. Pfahlwurzel braucht tiefgruendiges Substrat. Staunaesse unbedingt vermeiden. pH 6.0--7.0. | -- |

**Hinweis:** Petersilie vertraegt Halbschatten besser als die meisten Kraeuter. Ideal fuer halbschattige Balkone und unter Baeumen/Strauchern. Supermarkt-Petersilie im Topf haelt selten lange -- besser aus Samen ziehen. Glatte Petersilie hat ein intensiveres Aroma als krause; krause Petersilie ist dekorativer und robuster gegen Regen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualitaet

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | 8 (C3-Schattenblatt, Netto-Photosynthese = 0) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | 20 (C3-Sonnenblatt) | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade (Vollsonne bis lichter Halbschatten; vertraegt Halbschatten besser als die meisten Kraeuter) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30--45 (flachwurzelnd trotz Pfahlwurzel; Hauptwurzelzone im oberen Profil) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz | sensitive (Pfahlwurzel fault bei Naesse leicht; Drainage zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive (Literatur: Wachstum/Chlorophyll bereits bei moderater Salinitaet reduziert; verwandte Apiaceae Moehre = sensitive) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN -- kein publizierter Maas-Hoffman-Schwellenwert fuer Petroselinum crispum; verwandte Moehre 1.0 dS/m (sensitive) als Orientierung --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN -- kein publizierter Maas-Hoffman-Slope fuer Petersilie --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min--max) | 6.0--7.0 (harmonisiert mit Substrat-Empfehlung §1.6) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 5 (sehr langsame Keimung; siehe §1.3) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 22 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.5 (Lichtkeimer -- nur duenn bedecken oder andruecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14 (Spanne 14--28 Tage; notorisch langsam und ungleichmaessig) | `species.seed_profile.days_to_germination` |
| Keimfaehigkeitsdauer (Jahre) | 1 (kurzlebiges Saatgut; deutliche Keimratenabnahme bereits im 2. Jahr) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak (24 h Einweichen in lauwarmem Wasser beschleunigt die Keimung um ca. 7 Tage) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 2.0 (Spanne ca. 1.5--2.2 g je nach Sorte/Quelle; entspricht ca. 475--650 Samen/g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 35 (Zielbestandsdichte nach Vereinzelung; Reihenabstand ~22.5 cm, Pflanzabstand ~12.5 cm gemaess §1.6) | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Petersiliensamen enthalten keimhemmende Furanocumarine in der Samenschale, was die notorisch lange und ungleichmaessige Keimdauer (2--4 Wochen) erklaert. Einweichen vor der Aussaat verkuerzt die Keimzeit spuerbar. Die Keimfaehigkeit laesst rascher nach als bei vielen anderen Doldenbluetlern -- frisches Saatgut (max. 1 Jahr alt) liefert deutlich zuverlaessigere Ergebnisse.

Quellen (§1.8): [BBC Gardeners' World Magazine -- How to Grow Parsley](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-parsley/); [Wisconsin Horticulture Extension -- Parsley, Petroselinum crispum](https://hort.extension.wisc.edu/articles/parsley-petroselinum-crispum/); [Wikifarmer -- Petroselinum crispum: Parsley seeds](https://wikifarmer.com/library/en/article/petroselinum-crispum-parsley-seeds); [A Way To Garden -- Estimating viability: how long do seeds last?](https://awaytogarden.com/estimating-viability-how-long-do-seeds-last/); [lovethegarden.com -- How to plant, grow and care for Parsley](https://www.lovethegarden.com/uk-en/article/parsley-petroselinum-crispum); [Southern Exposure Seed Exchange -- Parsley](https://www.southernexposure.com/categories/parsley/)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 14--28 | 1 | false | false | low |
| Saemling (seedling) | 21--35 | 2 | false | false | low |
| Vegetativ (vegetative) | 42--90 | 3 | false | true | medium |
| Dormanz (dormancy) | 90--120 (Winterruhe, 1. Jahr auf 2. Jahr) | 4 | false | false | high |
| Bluete (flowering) | 30--60 (nur 2. Jahr) | 5 | true | false | low |

Hinweis: Als zweijaerige Pflanze wird Petersilie meist nur im ersten Jahr als Blattkultur genutzt. Im zweiten Jahr schiesst sie in Bluete und die Blaetter werden bitter. Fuer kontinuierliche Ernte jaehrlich neu aussaeen.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50--100 (Lichtkeimer!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3--6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 (optimal 20) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 (stomataerer Kollaps deutlich oberhalb des feuchtigkeitsliebenden Keim-Korridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--20 (kuehlliebende C3-Kultur) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht-Spektrum) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht, nie austrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--40 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (optimal 250--350) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 (Kurztagbedingungen verzoegern Bluete und foerdern Blattwachstum) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ca. 0.4 kPa; stomataerer Kollaps/Welkegrenze) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55 (haeufig im lichten Halbschatten/unter Nachbarbestand -- leicht erhoeht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400--800 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Petersilie vertraegt Halbschatten gut und ist toleranter gegenueber weniger Licht als Basilikum. Staunaesse vermeiden (Pfahlwurzel fault leicht). Boden zwischen den Giessungen leicht abtrocknen lassen.

#### Phase: Dormanz (dormancy)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (reduziert, Wintertag) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- (natuerlich) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (Kurztag foerdert Vernalisation) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 0--10 (Vernalisation: 4--8 Wochen bei 0--10 degC noetig fuer Bluetenbildung im 2. Jahr) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -8 -- 5 (mit Winterschutz) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7--14 (stark reduziert, nur bei Trockenheit) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (Langtag loest Bluete aus nach Vernalisation) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 20--24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Bluetenstand im offenen Tageslicht, 2. Jahr) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Wenn Saatgutgewinnung gewuenscht, Bluetenstaende ausreifen lassen. Samen ernten, wenn sie braun und trocken sind. Fuer Blatternte: Bluetenstaende sofort entfernen. Nach der Bluete stirbt die Pflanze ab (zweijaerig).

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 5.8--6.2 | 60 | 30 | 20 | 2 | 0.3 | 0.1 | 0.02 | 0.01 |
| Vegetativ | 3-1-2 | 1.2--1.8 | 5.8--6.2 | 100 | 50 | 30 | 3 | 0.5--0.8 | 0.2 | 0.04 | 0.03 |
| Dormanz | 0-0-0 | 0.0 | 6.0 | -- | -- | -- | -- | -- | -- | -- | -- |
| Bluete | 1-2-2 | 1.0--1.4 | 5.8--6.2 | 80 | 40 | 25 | 2 | 0.4 | 0.15 | 0.03 | 0.02 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
Hinweis (Mikronaehrstoffe Mn/Zn/Cu/Mo): Die Spalten Mn `nutrient_profiles.manganese_ppm`, Zn `nutrient_profiles.zinc_ppm`, Cu `nutrient_profiles.copper_ppm`, Mo `nutrient_profiles.molybdenum_ppm` entsprechen den Standard-Zielkonzentrationen einer Blattgemuese-/Kraeuter-Naehrloesung (leichtzehrend, niedriger als Fruchtgemuese): Mn 0.5--1.0, Zn 0.05--0.5, Cu 0.02--0.05, Mo 0.01--0.05 ppm. Petersilie kann Mn bei niedrigem pH (< 5.8) ueberhoeht aufnehmen -- pH nicht unter 5.8 absenken. In Keim-/Dormanzphasen (nur Wasser) keine Mikronaehrstoff-Gabe.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

Hinweis: Petersilie ist ein Mittelzehrer mit hohem Stickstoffbedarf in der vegetativen Phase (Blattproduktion). EC im Hydro-/Cocoanbau: 1.2--1.8 mS. pH unter 5.8 vermeiden (Eisentoxizitaet). Kalium foerdert das Aroma der aetherischen Oele.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 14--28 Tage | Keimblaetter (Kotyledonen) voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 21--35 Tage | 3--4 echte Blattgruppen (dreiteilige Blaetter) |
| Vegetativ -> Dormanz | time_based / event_based | Ende Oktober (erster Frost) | Wachstum verlangsamt sich, Pflanze zieht sich teilweise zurueck |
| Dormanz -> Bluete | time_based | Nach Vernalisation (4--8 Wochen < 10 degC) + Langtag (2. Jahr) | Bluetenstiel waechst aus der Blattrosette |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10 | 5 | Bluete (2. Jahr) |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Kraeuterdunger (fluessig) | COMPO BIO | organisch | 20--30 ml / 10 L Giesswasser | Apr--Okt, alle 14 Tage | medium_feeder |
| Reifkompost | Eigenerzeugung | organisch | 3--4 L/m2 | Fruehjahr (Einarbeitung bei Pflanzung) | alle |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 50--80 g/m2 | Fruehjahr (Einarbeitung) | medium_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 0.5 L/m2 | Mai--September, alle 14 Tage | medium_feeder |
| Schachtelhalmbruehe | Eigenerzeugung | Pflanzenhilfsmittel | 1:5 verduennt, Blattspruehung | Mai--September, alle 14 Tage | alle (Pilzpraevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Petersilie Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--4 | Keimung | 0.0 | 6.0 | 0 | 0 | 0 | Nur Wasser, Keimung dauert 2--4 Wochen |
| 5--7 | Saemling | 0.4--0.8 | 5.8--6.0 | 0.2 | 0.3 | 0.3 | EC sehr langsam steigern |
| 8--12 | Vegetativ frueh | 1.0--1.4 | 5.8--6.0 | 0.3 | 0.6 | 0.6 | Stickstoff-betontes Wachstum |
| 13--20 | Vegetativ Haupternte | 1.4--1.8 | 5.8--6.0 | 0.3 | 0.8 | 0.8 | Regelmaessige Ernte, volle Dosierung |
| 20+ | Spaetphase | 1.0--1.4 | 6.0 | 0.2 | 0.6 | 0.6 | Bei nachlassendem Wachstum EC reduzieren |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Vega A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Mittelzehrer mit hohem N-Bedarf:** Petersilie braucht fuer die Blattproduktion viel Stickstoff. N-Mangel zeigt sich durch vergilbende aeltere Blaetter.
- **Kalium foerdert Aroma:** Ausreichende Kaliumversorgung steigert den Gehalt an aetherischen Oelen.
- **Eisenchlorose bei hohem pH:** Vergilbung junger Blaetter bei pH > 7.0. pH regelmaessig kontrollieren, ggf. mit saurem Duenger oder Eisenchelat korrigieren.
- **Organische Topfkultur:** Bio-Kraeuterdunger alle 2 Wochen genuegt. Brennnesseljauche als N-Lieferant ideal.
- **Keine Frischdungung!** Frischer Mist oder Gulle fuehrt zu ueblem Geschmack und foerdert die Moehrenfliege.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 (bei Ueberwinterung im Freiland stark reduzieren) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Zimmerwarmes Wasser (15--20 degC). Morgens giessen, nicht ueber die Blaetter (Septoria-Gefahr). Boden gleichmaessig feucht halten, aber Staunaesse vermeiden (Pfahlwurzel fault schnell). Kurzzeitige Trockenheit wird besser vertragen als Naesse. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4; 5; 6; 7; 8; 9; 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (zweijaerig; bei Topfkultur nach 4--6 Monaten in groesseren Topf umsetzen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Vorkultur starten | Aussaat in Schalen bei 18--22 degC, Lichtkeimer: Samen nur leicht bedecken, Keimdauer 2--4 Wochen | hoch |
| Marz | Direktsaat / Pikieren | Ab Maerz Direktsaat ins Freiland moeglich (Reihenabstand 20--25 cm), Vorkultur-Saemlinge pikieren | hoch |
| Apr | Pflanzung / Weitersaat | Vorgezogene Pflanzen ins Freiland setzen, Pflanzabstand 20--25 cm | hoch |
| Mai | Erntebeginn | Erste aeussere Blaetter ernten, immer Herz stehen lassen, regelmaessig hacken | hoch |
| Jun | Haupternte | Regelmaessige Ernte foerdert Nachwachsen, Duengung alle 14 Tage, auf Septoria achten | hoch |
| Jul | Ernte + Nachsaat | Ernte fortsetzen, Nachsaat fuer Herbst/Winterernte | hoch |
| Aug | Ernte + Schaedlingskontrolle | Auf Septoria-Blattflecken achten (braune Flecken mit schwarzen Punkten), befallene Blaetter sofort entfernen | hoch |
| Sep | Ernte fortsetzen | Letzte Ernte vor Wintereinbruch, evtl. Petersilie in Topf umsetzen und ins Haus holen | mittel |
| Okt | Winterschutz | Freiland-Petersilie mit Reisig oder Vlies abdecken | mittel |
| Nov--Feb | Winterruhe | Giessen nur bei Trockenheit, kein Duenger | niedrig |

### 4.3 Ueberwinterung

Petersilie ist zweijaerig und kann mit Winterschutz (Reisig, Vlies, Laub) im Freiland ueberwintern. Vertraegt Froeste bis -8 degC. Im Topf: Frostfrei stellen (5--10 degC, kuehler Flur, unbeheiztes Gewaechshaus). Im zweiten Fruehjahr treibt die Pflanze aus und schiesst dann relativ schnell in Bluete. Fuer durchgehende Blatternte: jaehrlich neu aussaeen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Bewertung | needs_protection (uebersteht Freiland-Winter nur mit Abdeckung; Topfkultur alternativ frostfrei einlagern) | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme + Monat | mulch (Reisig/Laub/Vlies); Oktober--November | `overwintering_profiles.winter_action` |
| Fruehjahrs-Massnahme + Monat | uncover; Maerz | `overwintering_profiles.spring_action` |
| Winterquartier Temperatur (degC) | 5--10 (kuehler, frostfreier Raum bei Topfueberwinterung) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, kuehl (kein Dunkellager -- bleibt immergruen) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Giessen | sparsam, nur bei Trockenheit (Winter-Multiplikator 3.0) | `overwintering_profiles.winter_quarter_watering` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Moehrenfliege (Carrot Fly) | Psila rosae | Rostbraune Fraessgaenge in der Wurzel, welkende Blaetter, Pflanze kuemmert | root | vegetative | medium |
| Blattlaeuse (Aphids) | Cavariella aegopodii, Semiaphis dauci | Gekraeuselte Blaetter, Honigtau, verkrueppelte Triebe | leaf, stem | vegetative | easy |
| Moehrenblattfloh | Trioza apicalis | Blattkraeuselung, Wuchshemmung, gelbliche Verfaerbung | leaf | seedling, vegetative | medium |
| Schnecken (Slugs/Snails) | Arion spp. | Lochfrass an jungen Blaettern, Schleimspuren | leaf | seedling, vegetative | easy |
| Drahtwuermer (Wireworm) | Agriotes spp. | Fraessgaenge in Pfahlwurzel, Pflanze welkt | root | vegetative | hard |
| Wurzelgallennematoden | Meloidogyne spp. | Knotige Verdickungen an Wurzeln, Wuchshemmung | root | vegetative | hard |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Septoria-Blattflecken (Septoria Leaf Spot) | fungal | Kleine gelbe Flecken, die sich zu hellbraunen Laesionen mit dunklem Rand vergroessern; schwarze Pyknidien (Sporenlager) in den Flecken | humid_conditions, rain_splash, overhead_watering | 7--14 | vegetative |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser, mehliger Belag auf Blattoberseiten | warm_dry_days_cool_nights | 7--14 | vegetative |
| Falscher Mehltau (Downy Mildew) | fungal (Oomycet) | Gelbe Flecken auf Blattoberseite, weisser/grauer Belag auf Unterseite | cool_humid_conditions | 5--10 | vegetative |
| Schwarzbeinigkeit (Damping Off) | fungal | Saemling knickt an Basis um, Staengel duenn und braun-schwarz | overwatering, cold_wet_soil | 2--5 | seedling |
| Apium-Y-Virus (Celery Yellow Spot) | viral | Gelbe Ringflecken auf Blaettern, Wuchsdeformationen | aphid_transmission | 14--28 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Aphidius colemani (Schlupfwespe) | Blattlaeuse | 2--5 | 14--21 |
| Steinernema feltiae (Nematode) | Moehrenfliege (Bodenstadien), Schnecken | 250.000/m2 | 7--14 |
| Coccinella septempunctata (Marienkaefer) | Blattlaeuse | 5--10 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetze | mechanical | -- | Netz (Maschenweite < 1.3 mm) ueber Bestand ab Aussaat | 0 | Moehrenfliege, Moehrenblattfloh |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Spruehung 1:5 verduennt, alle 14 Tage praeventiv | 0 | Septoria, Mehltau |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen und im Restmuell entsorgen | 0 | Septoria, Mehltau |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Mischkultur mit Zwiebeln | cultural | -- | Zwiebeln/Lauch als Nachbarn pflanzen | 0 | Moehrenfliege (Geruchstarnung) |
| Fruchtfolge (min. 3 Jahre) | cultural | -- | Keine Apiaceae auf gleicher Flaeche innerhalb von 3 Jahren | 0 | Septoria, Nematoden |

### 5.5 Resistenzen der Art

Petersilie (Petroselinum crispum) hat begrenzte natuerliche Resistenzen. Die bedeutendste Krankheit ist die Septoria-Blattfleckenkrankheit.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Septoria petroselini (Toleranz) | Krankheit | Einige Cultivare zeigen bessere Toleranz (keine vollstaendige Resistenz bekannt) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium) |
| Fruchtfolge-Kategorie | Doldenbleutler (Apiaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) oder Gruenduengung -- lockerer, stickstoffangereicherter Boden |
| Empfohlene Nachfrucht | Schwachzehrer (Radieschen, Feldsalat) oder Gruenduengung |
| Anbaupause (Jahre) | 3--4 Jahre fuer Apiaceae auf gleicher Flaeche (Septoria, Nematoden) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Petersilie wehrt Tomatenhornwurm ab, Tomate bietet Halbschatten | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.8 | Pilzabwehr durch Allicin, Nuetzlinge anlocken | `compatible_with` |
| Zwiebel | Allium cepa | 0.8 | Gegenseitige Schaedlingsabwehr (Moehrenfliege vs. Zwiebelfliege) | `compatible_with` |
| Radieschen | Raphanus sativus var. sativus | 0.8 | Schnelle Markierungssaat, verschiedene Wurzeltiefen | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.7 | Gute Bodennutzung, verschiedene Wurzeltiefen | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Gleiche Kultur, gute Raumnutzung, Nuetzlingsfoerderung | `compatible_with` |
| Mangold | Beta vulgaris subsp. vulgaris | 0.7 | Verschiedene Familien, gute Platznutzung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Moehre / Karotte | Daucus carota | Gleiche Familie, gemeinsame Schaedlinge (Moehrenfliege), Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Sellerie | Apium graveolens | Gleiche Familie, gemeinsame Schaedlinge und Krankheiten | moderate | `incompatible_with` |
| Dill | Anethum graveolens | Gleiche Familie, Kreuzbestaeubung moeglich (veraendert Geschmack der Samen), Naehrstoffkonkurrenz | mild | `incompatible_with` |
| Kopfsalat | Lactuca sativa | Konkurrenz um aehnliche Naehrstoffe, aehnliche Wuchshoehe | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Apiaceae (mit sich selbst) | `shares_pest_risk` | Moehrenfliege, Septoria, Nematoden, Apium-Y-Virus | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Petersilie |
|-----|-------------------|-------------|------------------------------|
| Koriander | Coriandrum sativum | Gleiche Familie (Apiaceae), aehnliche Kultur | Schnellere Keimung, andere Aromanuance |
| Kerbelkraut | Anthriscus cerefolium | Gleiche Familie, aehnliches Einsatzgebiet | Schattenvertraglicher, schnellere Ernte |
| Liebstoeckel | Levisticum officinale | Gleiche Familie, aehnliches Aroma | Mehrjaehrig, winterhart, weniger Pflegeaufwand |
| Sellerie (Blatt) | Apium graveolens var. secalinum | Gleiche Familie, aehnliche Verwendung | Aehnliches Aromaprofil |
| Schnittlauch | Allium schoenoprasum | Andere Familie, aehnliche Nutzung als Kuechenkraut | Mehrjaehrig, winterhart, pflegeleichter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Petroselinum crispum,Petersilie;Glatte Petersilie;Krause Petersilie;Peterle;Parsley;Garden Parsley,Apiaceae,Petroselinum,biennial,long_day,herb,taproot,5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.1,"Mittelmeerraum (Marokko, Algerien, Tunesien, Suedeuropa)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Gigante d'Italia,Petroselinum crispum,,,high_yield,75,,open_pollinated
Glatte Petersilie 'Einfache Schnitt',Petroselinum crispum,,,heirloom,70,,open_pollinated
Krause Petersilie 'Gruene Perle',Petroselinum crispum,,,compact;ornamental,75,,open_pollinated
Mooskrause 2,Petroselinum crispum,,,compact;ornamental,75,,open_pollinated
Wurzelpetersilie 'Halblange',Petroselinum crispum subsp. tuberosum,,,heirloom,90,,open_pollinated
Festival 68,Petroselinum crispum,,,high_yield;disease_resistant,70,,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Parsley: https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/parsley
2. Hortipendium -- Petersilie Pflanzenschutz: https://hortipendium.de/Petersilie_Pflanzenschutz
3. Wikipedia -- Petersilie: https://de.wikipedia.org/wiki/Petersilie
4. gartenratgeber.net -- Petersilie: https://www.gartenratgeber.net/pflanzen/petersilie.html
5. garten-wissen.com -- Petersilie: https://www.garten-wissen.com/pflanzen/petersilie/
6. schadbild.com -- Septoria an Petersilie: https://www.schadbild.com/gem%C3%BCse/petersilie/septoria-blattflecken/
7. oekolandbau.de -- Septoria-Blattflecken: https://www.oekolandbau.de/landwirtschaft/pflanze/grundlagen-pflanzenbau/pflanzenschutz/schaderreger/schadorganismen-im-gemuesebau/septoria-blattflecken-der-petersilie-septoria-petroselini/
8. MDPI Agronomy -- Parsley DLI Response: https://www.mdpi.com/2073-4395/9/7/389
9. Produce Grower -- Hydroponic Herb Yields: https://www.producegrower.com/article/hydroponic-production-primer-improve-culinary-herb-yields/
10. Koraylights -- Indoor cultivation PPFD and DLI: https://koraylights.com/how-much-light-do-your-plants-need-indoor-cultivation-ppfd-and-dli/
11. hauenstein-rafz.ch -- Petersilie: https://www.hauenstein-rafz.ch/de/pflanzenwelt/pflanzenportrait/diverse/Petersilie-Petrosilenum.php
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
12. Paredes et al. (2025), ScienceDirect -- Base/upper temperature thresholds for GDD (FAO56rev): Petersilie Tbase 4 degC, Tupper 27 degC (voller Kulturzyklus): https://www.sciencedirect.com/science/article/pii/S037837742500469X
13. Wikipedia -- Salt tolerance of crops (Maas-Hoffman-Klassifikation, Apiaceae-Verwandte): https://en.wikipedia.org/wiki/Salt_tolerance_of_crops
14. FAO -- Annex 1 Crop salt tolerance data (Moehre sensitive 1.0 dS/m, Sellerie MS 1.8 dS/m als Apiaceae-Orientierung): https://www.fao.org/4/y4263e/y4263e0e.htm
15. PMC -- Biochemical Changes in Two Parsley Varieties during Saline Stress (Petersilie salzsensitiv): https://pmc.ncbi.nlm.nih.gov/articles/PMC4499097/
16. GrowVeg -- Vegetable Root Depths (Petersilie flachwurzelnd, 30--46 cm): https://www.growveg.com/guides/vegetable-root-depths-revealed-use-this-guide-to-make-smarter-planting-decisions/
17. UMN Extension -- Growing parsley (pH 6.0--7.0, Vollsonne/Halbschatten): https://extension.umn.edu/vegetables/growing-parsley
18. ScienceDirect Topics -- Light Compensation Point (C3 8--16 umol/m2/s, Schattenblatt niedriger): https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/compensation-point
19. Annals of Botany / Oxford Academic -- Far-red light effects: FR-Fraction Vollsonne ~0.46--0.5, Halbschatten hoeher: https://academic.oup.com/aob/article/135/3/589/7701832
20. AlpHa Measure / Atlas Scientific -- Hydroponic micronutrient sufficiency ranges (Mn 0.5--1.0, Zn 0.05--0.5, Cu 0.02--0.05, Mo ~0.01--0.05 ppm): https://alpha-measure.com/hydroponic-nutrient-solution-monitoring-and-optimization/
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -- Korrektur Bluetemonate (6;7;8 -> 6;7) -->
21. garten-wissen.com -- Petroselinum crispum: Growing Timeline: https://www.garten-wissen.com/pflanzen/petersilie/ -- "Bluetezeit (Blooming - Year 2): Juni oder Juli"; "Aussaat: von Mitte Maerz bis Ende Juli"
22. Kiepenkerl -- Kulturanleitung Petersilie: https://www.kiepenkerl.de/kulturanleitungen/petersilie/ -- "Die Pflanze bluet im zweiten Jahr ... im Juni bzw. Juli"; Ernte 1. Jahr Maerz--Oktober, 2. Jahr Maerz--Juni/Juli (endet mit Bluetenbildung)
23. NC State Extension Gardener Plant Toolbox / Missouri Botanical Garden Plant Finder -- Petroselinum crispum: https://plants.ces.ncsu.edu/plants/petroselinum-crispum/ ; https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=276060 -- "Plants will bloom in the 2nd year ... in summer"; Samenbildung Juli--September (stuetzt Bluetebeginn Juni/Juli, keine Beleg fuer Bluete bis August)
<!-- Hinweis: Eine Einzelquelle (gartenjournal.net/petersilie-blueht) nennt abweichend "zwischen Juni und August" ohne Beleg/Zitat einer Primaerquelle; eine zweite Seite derselben Redaktion (gartenjournal.net/petersilie-mehrjaehrig) nennt dagegen "Juni und Juli" -- als interne Widerspruechlichkeit gewertet und durch die 3 uebereinstimmenden Quellen 21-23 fuer das Bluete-Ende Juli nicht entkraeftet. -->
<!-- /Quelle: growing-phase-auditor 2026-07 -->
<!-- Quelle: seed-profile-backfill 2026-07 -->
24. BBC Gardeners' World Magazine -- How to Grow Parsley: https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-parsley/ -- Keimdauer 3--4 Wochen, Saattiefe 1/4 inch, Einweichen ueber Nacht empfohlen
25. Wisconsin Horticulture Extension -- Parsley, Petroselinum crispum: https://hort.extension.wisc.edu/articles/parsley-petroselinum-crispum/ -- Keimtemperatur/-dauer, Anbauhinweise
26. Wikifarmer -- Petroselinum crispum: Parsley seeds: https://wikifarmer.com/library/en/article/petroselinum-crispum-parsley-seeds -- ca. 475--500 Samen/g (TKG ~2.0--2.1 g)
27. A Way To Garden -- Estimating viability: how long do seeds last?: https://awaytogarden.com/estimating-viability-how-long-do-seeds-last/ -- Petersiliensaatgut nur 1--2 Jahre keimfaehig
28. lovethegarden.com -- How to plant, grow and care for Parsley: https://www.lovethegarden.com/uk-en/article/parsley-petroselinum-crispum -- Reihenabstand 30 cm, Pflanzabstand 10--15 cm nach Vereinzelung
29. Southern Exposure Seed Exchange -- Parsley: https://www.southernexposure.com/categories/parsley/ -- Sortenkatalog, Samengewicht/-mengen je Packung
<!-- /Quelle: seed-profile-backfill 2026-07 -->
