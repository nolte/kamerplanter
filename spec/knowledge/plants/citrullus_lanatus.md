# Wassermelone -- Citrullus lanatus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Plantura, Hortipendium, AgronoBlog, PlantFrand, Grove.eco, Gartenratgeber.net, Heimbiotop, OMAFRA (Ontario Ministry of Agriculture)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Citrullus lanatus | `species.scientific_name` |
| Volksnamen (DE/EN) | Wassermelone; Watermelon; Water Melon | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` -> `botanical_families.name` |
| Gattung | Citrullus | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | — (einjährig; keine mehrjährige Blühstrategie) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, degC) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | -- (einjaehrig; nicht zutreffend) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | -- (nicht zutreffend) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (h) | -- (tagneutral / day_neutral; keine kritische Tageslaenge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Extrem kaltempfindlich. Stirbt bei unter 10 degC ab; Frost sofort toedlich. Benoetigt 120 frostfreie Tage (Wachstumssaison). In Mitteleuropa nur im Gewaechshaus oder sehr warmen, geschuetzten Lagen zuverlaessig. | `species.hardiness_detail` |
| Heimat | Tropisches und suedliches Afrika (Kalahari-Wueste); heute weltweit angebaut | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; heat_tolerant; drought_tolerant (etablierte Pflanzen) | `species.traits` |

**Besonderheit:** Wassermelone benoetigt eine sehr lange, warme Vegetationsperiode (120--150 frostfreie Tage) und ist daher in Mitteleuropa (Zone 7--8) ohne Gewaechshaus oder Folientunnel schwierig anzubauen. Die Pflanze hat eine tiefe Pfahlwurzel, die in grosse Bodenfeuchte-Reserven reicht -- daher im Freiland relativ trockentolerant.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4--6 (Anzucht ab Anfang bis Mitte April; spaeter als Tomate beginnen!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (nur in Zone 8+ sinnvoll; Boden muss mind. 21 degC warm sein) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 (nur in suedlichen Gebieten) | `species.direct_sow_months` |
| Erntemonate | 8; 9 (in Mitteleuropa Gewaechshaus bevorzugt; Reife August--September) | `species.harvest_months` |
| Bluetemonate | 6; 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate (Waermekeimer; sehr empfindlich gegenueber Kaelte und Verpflanzen) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 24--30 degC (Heizmatte zwingend empfohlen)
- Minimale Keimtemperatur: 20 degC (langsame, ungleichaessige Keimung)
- Keimdauer: 5--10 Tage
- Aussaat in Einzeltoepfe (4 cm Jiffy oder Kokostablette) -- keine Pikierung!
- Samen 1.5--2 cm tief einpflanzen; quer oder flach einlegen foerdert Keimung
- Substrat: Naehrstoffarme Aussaaterde, gut drainiert

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft und Trichome koennen milde Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Wassermelonen-Saft kann bei Latex-Allergie orale Reaktionen ausloesen. Blaetter enthalten Cucurbitacin (leicht bitter) -- daher Blaetter nicht essen.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7 | `species.pruning_months` |

**Triebfuehrung:**
- Haupttrieb nach 5--6 Blaettern kappen (foerdert Seitentriebe mit weiblichen Blueten)
- Pro Pflanze max. 2--3 Fruechte zugelassen (groessere Qualitaet und Zucker)
- Im Gewaechshaus: senkrechte Erziehung an Draehten; Fruechte in Netzen aufhaengen
- Blaetter in Fruchtnaehe entfernen fuer bessere Luftzirkulation und Fruchtfaerbung

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (nur Minisorten <2 kg in Topf 30+ L; Standard-Wassermelonen benoetigen Freiland) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30--50 (nur fuer Minisorten) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 (Pfahlwurzel beachten!) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--50 (kriechend; Ranken bis 300 cm Laenge) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 150--300 (Ranktriebe im Freiland sehr ausladend) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80--120 in der Reihe; 150--200 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no (ausser sehr grosse Growzelte mit starker Beleuchtung; wenig praktikabel) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Minisorten; grosser Behaelter; senkrechte Erziehung mit Fruchtnetz) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (in Mitteleuropa fast zwingend fuer zuverlaessige Ernte) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (bei senkrechter Erziehung; starke Netze fuer Fruechte noetig -- bis 10 kg!) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr naehrstoffreiche, lockere, gut drainierte Erde. Sandanteile (25--30%) foerdern Drainage. pH 6.0--7.0. Grosse Mengen Kompost (30--40%). | -- |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualitaet

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | 30 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | 50 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 100--150 | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> -- (FAO/USDA fuehren Wassermelone nur qualitativ als "MS"; kein quantitativer Maas-Hoffman-Schwellenwert publiziert) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> -- (kein publizierter Maas-Hoffman-b-Wert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min--max) | 6.0--6.8 | `species.soil_ph_preference` |

**Hinweise:**
- **Lichtkompensationspunkt (light compensation point, LCP):** Fuer Wassermelone liegen keine direkt gemessenen Werte vor. Die angegebene Spanne 30--50 umol/m2/s ist aus eng verwandten Cucurbitaceae/Fruchtgemuese abgeleitet (Gurke ~51, Tomate ~53, Paprika ~35 umol/m2/s). Der Lichtsaettigungspunkt liegt deutlich hoeher (Messungen an Wassermelonen-Saemlingen bei 800 umol/m2/s) -- diese Saettigungswerte gehoeren NICHT in das LCP-Feld.
- **Salztoleranz:** Bezugsgroesse ist die Substrat-Saettigungsextrakt-Leitfaehigkeit (ECe), nicht die Giesswasser-EC. Wassermelone ist nur qualitativ als "moderately sensitive" (MS) eingestuft; FAO Annex 1 markiert Schwelle und Slope mit "--".
- **Boden-pH:** Harmonisiert mit der Topf-Substrat-Empfehlung in §1.6 (pH 6.0--7.0) und den Naehrstoffprofilen in §2.3 (pH 6.0--6.8). Optimum schmaler bei 6.0--6.8.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill, Batch 4) -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (degC) | 20 (langsame, ungleichmaessige Keimung It. S.1.3; peer-reviewte Untergrenze fuer nennenswerte Keimung ebenfalls ca. 20 degC) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (degC) | 35 (Keimrate/Wurzelentwicklung/Saemlingswachstum am besten bei 35 degC It. Temperaturstudie; praxisuebliche Zielspanne 24--32 degC) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 2.0 (1--2.5 cm It. Extension-Quellen; S.1.3 nennt 1.5--2 cm quer eingelegt) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 4 (4--12 Tage, waermeabhaengig; unterer Wert bei Optimaltemperatur) | `species.seed_profile.days_to_germination` |
| Keimfaehigkeitsdauer (Jahre) | 4 | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark (peer-reviewte Studie: nahezu 100% Keimung im Dunkeln bzw. unter Rot-/Weisslicht; anhaltendes Fernrot-/Blaulicht hemmt die Keimung ueber Phytochrom-Steuerung -- Standardpraxis ist ohnehin Erdbedeckung) | `species.seed_profile.light_germination` |
| Vorbehandlung | -- (keine Vorbehandlung erforderlich) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 70 (Sortenspanne ca. 50--100 g je 1000 Korn, abgeleitet aus 10--20 Samen/g; starke Sortenabhaengigkeit Standard- vs. Minisorten) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m2) | 0.6 (Endabstand 80--120 cm in der Reihe x 150--200 cm Reihenabstand It. S.1.6; entspricht ca. 1 Pflanze je 1.4--1.75 m2) | `species.seed_profile.sowing_density_per_m2` |

Quellen (S.1.8):
1. Interne Keiminfos S.1.3 dieses Dokuments (Keimtemperatur 24--30 degC optimal / 20 degC minimal, Keimdauer 5--10 Tage, Saattiefe 1.5--2 cm) -- bereits als Quelle im Dokument gefuehrt.
2. Thanos & Mitrakos -- Watermelon seed germination. 1. Effects of light, temperature and osmotica (Seed Science Research, Cambridge Core, peer-reviewed): Keimung nahezu 100% im Dunkeln/unter Rot-Weisslicht, Fernrotlicht hemmend (Phytochrom-Steuerung); Keimung im Dunkeln optimal bei 20--40 degC, im Licht Hemmung unter 20 degC: https://www.cambridge.org/core/services/aop-cambridge-core/content/view/2AF7194F428B67906E60842BA3B54BDD/S0960258500001288a.pdf/watermelon_seed_germination_1_effects_of_light_temperature_and_osmotica.pdf
3. Effects of temperature treatment on seed germination, root development and seedling growth of Citrullus lanatus (ResearchGate): 35 degC verbessert Keimrate, Wurzelentwicklung und Saemlingswachstum: https://www.researchgate.net/publication/342550436_Effects_of_temperature_treatment_on_seed_germination_root_development_and_seedling_growth_of_Citrullus_lanatus_watermelon
4. Farmers Stop -- Seeds Per Gram for Common Vegetables, Fruits and Others: Wassermelone ca. 10--20 Samen/g: https://www.farmersstop.com/blogs/news/seeds-per-gram-for-common-vegetables-fruits-and-others
5. Grow Organic -- Watermelon Seed Saving and Preservation Techniques: Keimfaehigkeit bis zu 5 Jahre bei kuehler, trockener, dunkler Lagerung: https://www.groworganic.com/blogs/articles/watermelon-seed-saving-and-preservation-techniques
6. Alabama Cooperative Extension System -- Considerations for Successful Watermelon Production: Endabstand/Reihenabstand fuer Standardsorten (Hills ca. 4 ft/122 cm, Reihen 6 ft/183 cm), bestaetigt Groessenordnung von S.1.6: https://www.aces.edu/blog/topics/crop-production/watermelon-production/
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill, Batch 4) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--10 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--35 | 3 | false | false | medium |
| Bluete (flowering) | 14--21 | 4 | false | false | medium |
| Fruchtentwicklung (fruit_development) | 35--60 | 5 | false | false | medium |
| Reife (ripening) | 14--21 | 6 | true | true | medium |

**Hinweis:** Die Kulturdauer von Aussaat bis Ernte betraegt 100--120 Tage (Minisorten) bis 130--160 Tage (grosse Standardsorten). Dies ist die laengste Kulturdauer aller gaengigen Gemuese.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer; leicht mit Erde bedecken) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 26--32 (optimal 28--30; sehr warmebeduerftiger Keimer!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 22--26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.7 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 26--28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (feucht; nie nass) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 24--28 (Wassermelonen sind waermebedueftiger als Gurken!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.1 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 26--28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 (Vollsonne kritisch; 8+ h direkte Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 22--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--32 (optimal 27--30) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 20--24 (Wassermelone mag warme Naechte; < 18 degC: Wachstumsstopp) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 27--30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 (Pfahlwurzel holt sich Wasser; nicht uebergiessen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 500--800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 25--40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 27--30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Bestaeubungshinweis:** Wassermelonen sind monoecieus (getrennt-geschlechtliche Blueten auf einer Pflanze). Maennliche Blueten erscheinen ca. 1--2 Wochen vor weiblichen. Im Gewaechshaus manuelle Bestaeubung (Pinsel) oder Hummeln noetig.

#### Phase: Fruchtentwicklung (fruit_development)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 500--800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 25--40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 28--35 (hohe Waerme foerdert Zuckereinlagerung!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 (Temperaturdifferenz > 10 degC foerdert Zucker signifikant) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2--2.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 28--32 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 600--800 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (Wasser regelmaessig aber nicht zu viel -- foerdert Zuckergehalt) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 800--1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Reife (ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--20 (starke Nachtabkuehlung = mehr Zucker) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45--60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.5--2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 27--30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7--14 (drastisch reduzieren! Letzte 10 Tage fast kein Wasser) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Ernte-Indikatoren:**
- Ranke (Tendrille) direkt am Fruchtstiel welkt/trocknet ab (zuverlaessigster Indikator!)
- Bodenfaerbung der Frucht (Auflagestelle) wechselt von weiss/gruen zu gelblich-creme
- Frucht gibt beim Klopfen einen dumpfen, hohlen Ton (kein helles "Plink")
- Stiel beginnt zu trocknen und sich zu verfaerben
- Fruchtschale verliert Glanz (matt statt glaenzend)

### 2.3 Naehrstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
Mikronaehrstoff-Spalten Mn/Zn/Cu/Mo ergaenzt (KA-Felder `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`). Die Spurenelement-Konzentrationen beziehen sich auf die Naehrloesung (mg/L = ppm) und liegen innerhalb der belegten Spannen: Mn 0.5--2, Zn 0.05--0.5, Cu 0.02--0.1, Mo 0.01--0.05 ppm. Referenzpunkte: klassische Hoagland-Loesung (Mn 0.5; Zn 0.05; Cu 0.02; Mo 0.01) und eine peer-reviewte Wassermelonen-Naehrloesung (modifizierte Steiner-Loesung: Mn ~0.62; Zn ~0.11; Cu ~0.02; Mo ~0.1). Phasenscaling analog zu Ca/Mg/S/Fe: in Keimung 0, Spitzenbedarf in Vegetativ--Fruchtentwicklung, in der Reife reduziert.

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.8--1.2 | 5.8--6.5 | 80 | 30 | 20 | 2 | 0.4 | 0.05 | 0.02 | 0.01 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 5.8--6.5 | 120 | 50 | 30 | 3 | 0.5 | 0.08 | 0.03 | 0.02 |
| Bluete | 2-2-3 | 1.6--2.4 | 5.8--6.5 | 150 | 50 | 30 | 3 | 0.5 | 0.08 | 0.03 | 0.02 |
| Fruchtentwicklung | 1-2-4 | 2.0--3.0 | 6.0--6.8 | 150 | 60 | 35 | 2 | 0.6 | 0.10 | 0.03 | 0.02 |
| Reife | 0-1-3 | 1.0--2.0 | 6.0--6.8 | 80 | 40 | -- | 1 | 0.3 | 0.05 | 0.02 | 0.01 |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--10 Tage | Keimblaetter vollstaendig entfaltet |
| Saemling -> Vegetativ | manual | 14--21 Tage | Umpflanzen in Endstandort nach letztem Frost |
| Vegetativ -> Bluete | event_based | 21--35 Tage | Erste maennliche Blueten sichtbar |
| Bluete -> Fruchtentwicklung | event_based | 10--14 Tage | Bestaeubung erfolgt; weibliche Fruchtansaetze wachsen |
| Fruchtentwicklung -> Reife | time_based / gdd_based | 35--60 Tage | GDD-Akkumulation; Tendrille-Trocknung |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Gewaechshaus)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag | Canna / Plagron | supplement | Ca+Mg | 0.10--0.15 | 2 | alle |
| Terra Vega | Canna | base | 3-1-4 | 0.20 | 3 | Vegetativ |
| Terra Flores | Canna | base | 2-2-4 | 0.20 | 3 | Bluete; Fruchtentwicklung |
| PK 13/14 | Canna | booster | 0-13-14 | 0.10 | 5 | Fruchtentwicklung (Hochphase) |

#### Organisch (Freiland/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 8--10 L/m2 | Fruehjahr (tief eingraben) | heavy_feeder |
| Hornspäne | Oscorna | organisch (N-Langzeit) | 100--150 g/m2 | Mai | Vegetativphase N-Versorgung |
| Tomaten-/Kuerbisduenger | COMPO BIO / Hauert | organisch | 30--50 ml / 10 L | woechentlich Jun--Aug | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10, 1.5 L/Pflanze | Jul--Aug | Fruchtentwicklung; Zucker |

### 3.2 Duengungsplan

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base (ml/L) | Booster (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|-------------|----------------|----------|
| 1--2 | Saemling | 0.6--1.0 | 5.8 | 0.3 | 0.4 Vega | -- | Nur Wasser erste 7 Tage |
| 3--5 | Vegetativ | 1.2--1.8 | 5.8 | 0.4 | 0.8 Vega | -- | EC steigern |
| 6--8 | Bluete | 1.6--2.4 | 6.0 | 0.5 | 0.8 Flores | -- | Auf Flores umstellen |
| 9--16 | Fruchtentw. | 2.0--3.0 | 6.0 | 0.5 | 0.8 Flores | 0.2--0.4 PK | Hoehere EC foerdert Zucker |
| 17--18 | Reife | 1.0--2.0 | 6.0 | 0.3 | 0.4 Flores | -- | Reduzieren; Wasseranteil erhoechen |
| Letzte 7--10 Tage | Reife | -- | -- | -- | -- | -- | Nur Wasser; foerdert Brix-Wert |

### 3.3 Mischungsreihenfolge

1. Wasser temperieren (20--24 degC)
2. CalMag (IMMER vor Sulfaten!)
3. Base A oder Terra Vega/Flores
4. PK-Booster (nur in Hochphase Fruchtentwicklung)
5. pH-Korrektur (IMMER zuletzt; Ziel: pH 5.8--6.5)

### 3.4 Besondere Hinweise zur Duengung

- **Wasser vor Ernte stark reduzieren:** Die letzten 10--14 Tage fast kein Giessen -- das ist der wichtigste Faktor fuer Zuckergehalt (Brix-Wert) und Aroma der Frucht.
- **Magnesium-Mangel:** Verbreitet bei Wassermelonen -- Interkosal-Chlorose der alten Blaetter. Bittersalz-Blattduengung (0.1% MgSO4) wirkt schnell.
- **Calcium:** Foerdert Zellwandstabilitaet; verhindert Fruchtplatzen bei unregelmaessiger Bewaesserung.
- **Stickstoff-Abbau:** Gegen Ende der Vegetativphase N reduzieren, K und P erhoehen -- foerdert weibliche Bluetenbildung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | herb_tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 3--5 (Pfahlwurzel holt tief; Oberflaechentrockenheit toleriert) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Warmes Wasser (20--24 degC). Blaetter trocknen halten (Mehltau-Praevention). Tropf-Bewaesserung optimal. Staunaesse vermeiden. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7--10 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; 1x in Endstandort) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb/Maerz | Planung | Sortenwahl; Saatgut bestellen; Gewaechshaus vorheizen | niedrig |
| Apr | Vorkultur | Aussaat in Einzeltoepfe 7--9 cm; Heizmatte 28 degC | hoch |
| Mai | Abhaerten + Auspflanzen | Behutsam abhaerten ab Mitte Mai; nach Eisheiligen auspflanzen | hoch |
| Mai/Jun | Triebfuehrung | Haupttrieb kappen nach 5--6 Blaettern; Seitentriebe aufleiten | hoch |
| Jun/Jul | Bestaeubung | Manuelle Bestaeubung oder Hummeln einsetzen | hoch |
| Jun/Jul | Fruchtausdunnung | Max. 2--3 Fruechte belassen; Fruchtnetz anbringen | hoch |
| Jul--Aug | Wasserreduktion | In der Reifephase Giessen stark reduzieren | hoch |
| Aug/Sep | Ernte | Reifeindikatoren pruefen; bei Reife sofort ernten | hoch |
| Sep | Saisonende | Beete raeumen; Samen trocknen fuer naechstes Jahr | niedrig |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste; stippenartige Blaettervergilbung; Trocken-Schaden | leaf | vegetative; fruit_development | medium |
| Blattlaeuse | Aphis gossypii; A. fabae | Honigtau; Wachstumshemmung; CMV-Uebertraeger | leaf; shoot | seedling; vegetative | easy |
| Thripse | Frankliniella occidentalis | Silbrige Blattflecken; Bluetenschaeden | flower; leaf | flowering | medium |
| Minierfliege | Liriomyza trifolii | Minen (gewundene helle Gangmuster) in Blaettern | leaf | vegetative | easy |
| Schnecken | Arion spp. | Blattfrass; Keimlingsfass | leaf | seedling; vegetative | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Podosphaera xanthii) | Weisser Belag auf Blattoberflaecte | dry_warm; poor_airflow | 5--10 | vegetative; flowering |
| Falscher Mehltau | oomycete (Pseudoperonospora cubensis) | Gelbliche Flecken; grauer Rasen Blattunterseite | cool_wet; high_humidity | 4--8 | vegetative; fruit_development |
| Anthraknose | fungal (Colletotrichum orbiculare) | Dunkle Blattflecken; Fruchtfaeule | warm_wet; high_humidity | 3--7 | flowering; fruit_development |
| Fusarium-Welke | fungal (Fusarium oxysporum f. sp. niveum) | Welke; Stengel-Verbräunung; Pflanze stirbt ab | contaminated_soil; warm | 14--28 | vegetative; fruit_development |
| Gurkenmosaik-Virus (CMV) | viral | Mosaik; Wuchsstoerungen; Fruchtdeformationen | aphid_vectors | 7--14 | alle |
| Phytophthora-Faeule | oomycete | Stengel- und Wurzelfaeule; Welke | waterlogging; cool_wet | 3--7 | seedling; vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10--20 | 10--14 |
| Aphidoletes aphidimyza | Blattlaeuse | 5--10 | 14--21 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Bombus terrestris (Hummel) | Bestaeubung | 1 Volk / 150 m2 | -- |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoelextrakt | biological | Azadirachtin | 0.3--0.5% abends spruehen | 3 | Spinnmilben; Blattlaeuse; Mehltau-Praevention |
| Netzschwefel | chemical | Schwefel | Stauben / Spruehen | 14 | Echter Mehltau |
| Kaliumbicarbonat | approved_organic | Kaliumbicarbonat | 0.5--1.0% spruehen | 0 | Mehltau-Praevention |
| Kupfer-Fungizid | approved_organic | Kupfer | 0.3--0.5% spruehen | 7 | Falscher Mehltau; Anthraknose |
| Tropfbewaesserung | cultural | -- | Blaetter trocknen halten | 0 | Mehltau-Praevention |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kuerbisgemaechse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Leguminosen (Bohnen; Erbsen; Klee); Gruenduengung |
| Empfohlene Nachfrucht | Spinat; Feldsalat; Zwiebeln; Moehren (Schwachzehrer) |
| Anbaupause (Jahre) | 3--4 Jahre (Fusarium bleibt lange im Boden) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Ablenkung; Bestaeubungsfoerderung | `compatible_with` |
| Mais | Zea mays | 0.7 | Windschutz; kein Naehrstoffkonflikt; Struktur | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeubungsanlocken | `compatible_with` |
| Bohnen (buschig) | Phaseolus vulgaris | 0.6 | N-Fixierung; Bodenbeschattung; kein Wasserkonflikt | `compatible_with` |
| Zwiebelgewaechse | Allium cepa; A. sativum | 0.6 | Pilzpraevention durch Schwefelverbindungen | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Andere Cucurbitaceae | Cucumis melo; Cucurbita spp.; Cucumis sativus | Gleiche Schaderreger; Mehltau; CMV; Konkurrenz um Bestaeubungsinsekten | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Phytophthora-Risiko geteilt; foerdert Bodenpilze | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Cucurbitaceae | `shares_pest_risk` | Mehltau (Podosphaera xanthii); CMV; Spinnmilben; Fusarium oxysporum | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Wassermelone |
|-----|-------------------|-------------|--------------------------------|
| Honigmelone | Cucumis melo var. inodorus | Gleiche Familie; aehnliche Kultur | Weniger Platz; einfacher in Mitteleuropa; mehr Sorten |
| Cantaloupe-Melone | Cucumis melo var. cantalupensis | Gleiche Familie | Kuerzere Kulturdauer; mehr Aroma; einfacher in GWH |
| Pepino-Melone | Solanum muricatum | Melonenartige Frucht | Mehrjaehrig; weniger Platz; andere Kultur |

---

## 8. Sorten / Cultivars

| Sorte | Typ | Kulturdauer (Tage) | Fruchtgewicht (kg) | Schale | Besonderheiten |
|-------|-----|------------------|--------------------|--------|----------------|
| Dumara F1 | Standard (gross) | 80--90 | 8--12 | Dunkelgruen gestreift | Robust; hoher Ertrag; klassisch |
| Sugar Baby | Minisorte | 70--80 | 2--4 | Dunkelgruen | Fuer Topf und kleinen Garten; gut fuer Mitteleuropa |
| Golden Midget | Minisorte | 65--75 | 2--3 | Gelbe Schale bei Reife (Anzeiger) | Schale verfaerbt sich als Reifeanzeiger |
| Crimson Sweet | Standard | 80--90 | 6--10 | Hell-dunkel gestreift | Klassische US-Sorte; sehr suesser roter Kern |
| Orangeglo | Heirloom | 85--100 | 5--9 | Hell gestreift | Oranges Fleisch; komplex-suesser Geschmack |
| Farao F1 | GWH-Sorte | 75--85 | 4--8 | Dunkelgruen | Fuer Gewaechshaus gezuechtet; Mitteleuropa geeignet |
| Mickylee | Mittelgross | 70--80 | 4--7 | Hellgruen gestreift | Sehr kompaktes Wachstum; trockentoleranter |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity
Citrullus lanatus,Wassermelone;Watermelon,Cucurbitaceae,Citrullus,annual,day_neutral,vine,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b,-0.1,Tropisches Afrika,limited,30,40,40,200,100,no,limited,true,true,heavy_feeder,tender
```

---

## Quellenverzeichnis

1. [Plantura -- Wassermelone pflanzen](https://www.plantura.garden/gemuese/melonen/wassermelone-pflanzen) -- Anbauguide Mitteleuropa
2. [Plantura -- Wassermelonen duengen](https://www.plantura.garden/gemuese/melonen/wassermelone-duengen) -- Duengungsempfehlungen
3. [Hortipendium -- Wassermelone Erwerbsanbau](https://hortipendium.de/Wassermelone_Erwerbsanbau) -- Professioneller Anbau; EC; Sorten
4. [AgronoBlog -- Watermelon Citrullus lanatus Crop Management](https://agronoblog.com/agriculture/watermelon-citrullus-lanatus-crop-management/) -- Wachstumsphasen; Naehrstoffe; Schädlinge
5. [Grove.eco -- Citrullus lanatus Nachbarn](https://www.grove.eco/en/plants/citrullus-lanatus/) -- Companion Planting
6. [PlantFrand -- Citrullus lanatus](https://www.plantfrand.com/pflanzen/cucurbitaceae/citrullus-lanatus/) -- Botanische Grunddaten
7. [Gartenratgeber.net -- Wassermelonen](https://www.gartenratgeber.net/pflanzen/wassermelonen.html) -- Pflege und Anbau
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
8. [Optimization of ionic strength of nutrient solution for enhanced hydroponic watermelon yield and quality (PMC12271344)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12271344/) -- peer-reviewte Wassermelonen-Naehrloesung; Mikronaehrstoff-Zusammensetzung (Mn/Zn/Cu/Mo/Fe/B) der Steiner-basierten Loesung
9. [EnvirevoAgritech -- Optimizing Hydroponic Nutrient Requirements per Stage](https://envirevoagritech.com/optimizing-hydroponic-nutrients-requirements/) -- allgemeine Spurenelement-Obergrenzen (Mn bis ~2 ppm, Mo 0.02--0.05 ppm). Hinweis: Die dort genannten oberen Zn-/Cu-Werte (Zn bis 2, Cu bis 0.5 ppm) liegen im near-toxischen Bereich und sind KEINE Empfehlung; verbindlich sind die Tabellenwerte (Zn 0.05--0.10, Cu 0.02--0.03 ppm) auf Hoagland-Baseline (Quelle #10), belegte Arbeitsspannen Zn 0.05--0.5, Cu 0.02--0.1 ppm
10. [Hoagland-Loesung (Referenz-Naehrloesung)](https://en.wikipedia.org/wiki/Hoagland_solution) -- klassische Mikronaehrstoff-Baseline Mn 0.5; Zn 0.05; Cu 0.02; Mo 0.01 ppm
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
