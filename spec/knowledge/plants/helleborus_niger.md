# Christrose — Helleborus niger

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartendialog Christrose, OBI Christrose, Pflanzen-Kölle Helleborus, Gartenratgeber Christrosen, Zulauf Gartencenter Christrose

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Helleborus niger | `species.scientific_name` |
| Volksnamen (DE/EN) | Christrose, Weihnachtsrose, Schwarze Nieswurz; Christmas Rose | `species.common_names` |
| Familie | Ranunculaceae | `species.family` → `botanical_families.name` |
| Gattung | Helleborus | `species.genus` |
| Ordnung | Ranunculales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (ausdauernd, blüht wiederholt über mehrere Jahre) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 (krautige Ranunculaceae-Schattenstaude; kein CAM/C4-Mechanismus belegt) | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (critical day length, h) | — (tagneutral nach Vernalisation; keine kritische Tageslänge — Blühinduktion kältegesteuert, nicht photoperiodisch) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Kälteperiode für Blüteninduktion zwingend) | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage (min vernalization days) | ~42 (6 Wochen; Kältereiz von 2–6 Wochen bei 2–7 °C; 6 Wochen für zuverlässige Blühinduktion) | `lifecycle_configs.vernalization_min_days` |
| Lebensdauer (typical lifespan, Jahre) | 20–30 (sehr langlebig; bei gutem Standort Jahrzehnte) | `lifecycle_configs.typical_lifespan_years` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein belegter Wuchs-/Phänologie-Basiswert für Helleborus niger auffindbar | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; Blüten vertragen leichten Frost bis -5°C; bei strengem Frost hängen Blüten herunter, erholen sich aber | `species.hardiness_detail` |
| Heimat | Alpen, nördlicher Balkan, nördliche Apenninen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Teilung bevorzugt; Aussaat möglich) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (Aussaat direkt nach Samenreife im Sommer) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 7, 8 (frische Samen; Kaltkeimer braucht Winter) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 12, 1, 2, 3 (Dezember bis März; daher "Weihnachtsrose") | `species.bloom_months` |

**Hinweis:** Blüte mitten im Winter ist das Alleinstellungsmerkmal. Echter Helleborus niger blüht ab Dezember bei mildem Wetter; zuverlässig Januar bis März. Samen sind Kaltkeimer — brauchen Winterperiode für Keimung.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung nach der Blüte im März/April — sehr vorsichtig, da Helleborus Wurzelstörungen schlecht verträgt. Rhizomteilung nur alle 5–8 Jahre. Aussaat frischer Samen (Kaltkeimer) dauert 1–2 Jahre bis zum Keimen, dann weitere 3–4 Jahre bis zur ersten Blüte.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile; besonders Wurzelstock | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Helleborin, Helleborein, Protoanemonin, Ranunculin | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG:** Alle Teile sind stark giftig — beim Ein-/Umpflanzen unbedingt Handschuhe tragen. Frischer Saft verursacht schwere Hautreizungen und Blasen. Bei Einnahme: sofort Arzt aufsuchen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 1, 2 (Januar/Februar, VOR dem Blütenauftrieb) | `species.pruning_months` |

**Hinweis:** Altes Laub aus dem Vorjahr im Januar/Februar vor den neuen Blüten und dem Austrieb entfernen — sonst Sclerotinia-Pilz (Helleborus-Blattschwärze). Neues Laub nach der Blüte (März/April) stehen lassen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 8–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lehmige, kalkhaltige, humusreiche Erde; pH 6,5–7,5 (leicht alkalisch); gut wasserdurchlässig; Drainagschicht | — |

**Standort:** Halbschatten bis Schatten; ideal unter Laubbäumen (Sonnenschutz im Sommer durch Laub; Licht im Winter/Frühjahr). Kalkhaltige Böden bevorzugt.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade (Waldrand-/Unterholzstaude; verträgt auch volle Sonne bei feuchtem Boden) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–50 (tiefwurzelnd; Rhizomwurzeln bis ~60 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (verträgt keine nassen/staunassen Böden; Drainage zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant (auf mehreren Listen salztoleranter Schattenstauden geführt) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> kein Maas-Hoffman-Schwellenwert (a) für Helleborus belegt | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein Maas-Hoffman-Slope (b) für Helleborus belegt | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.5–7.5 (neutral bis leicht alkalisch; kalkhaltige Böden bevorzugt) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: seed-profile-backfill 2026-07 (Batch 7) -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 4 (Kältereiz-Phase, zwingend für die Keimung cotyledon-reifer Embryonen) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 25 (Warmphase zur Embryo-Entwicklung bis Torpedo-Stadium, vor dem Kältereiz) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.3 (nur leicht mit feinem Substrat/Grit bedecken, ca. 0,2–0,6 cm je nach Quelle) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 180 (unterer Wert von 6–18 Monaten Gesamtdauer inkl. zweistufiger Warm-Kalt-Stratifikation — kein einfacher linearer Keimprozess, siehe Hinweis) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 0.5 (sehr kurzlebig: <15 % Keimfähigkeit nach 6 Monaten bei Raumtemperatur; im Kühlschrank bei 4 °C bis ca. 9 Monate verlängerbar — daher am besten frisch aussäen) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | indifferent (kein strikter Photoblastismus dokumentiert; Zuchtbetriebe empfehlen dünne Abdeckung, die noch Lichtdurchlass erlaubt) | `species.seed_profile.light_germination` |
| Vorbehandlung | cold_stratification (zwingende Kältebehandlung bei 2–7 °C für ≥8 Wochen nach Warmphase; siehe §1.1 Vernalisations-Hinweis — hier keimungsspezifisch, nicht identisch mit der Vernalisation der ausgewachsenen Pflanze) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: keine belastbare TKM-Angabe für Helleborus niger aus ≥2 unabhängigen Quellen auffindbar --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Christrose ist eine Garten-/Topfstaude ohne Reihen-/Feld-Direktsaat; keine Flächendichte-Angabe anwendbar --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Helleborus niger zeigt morphophysiologische Dormanz — die Samen durchlaufen zunächst eine Warmphase (20–25 °C) zur Embryo-Reifung bis zum Torpedo-Stadium, danach einen zwingenden Kältereiz (2–7 °C, ≥8 Wochen) bis zum Cotyledon-Stadium, erst danach erfolgt die eigentliche Keimung. Die häufig genannte Zeitspanne „6–18 Monate" bildet diesen gesamten zweistufigen Prozess ab, nicht eine einfache Keimdauer bei konstanter Temperatur.

Quellen (§1.8):
1. [Whitman et al./ScienceDirect — Temperatures affecting embryo development and seed germination of Christmas Rose (Helleborus niger) after sowing](https://www.sciencedirect.com/science/article/abs/pii/S0304423805002852) — Warm-/Kaltphasen-Temperaturen, Embryo-Entwicklungsstadien
2. [Gardener's Path — How to Grow Hellebores from Seed](https://gardenerspath.com/plants/flowers/hellebore-seed-planting-tips/) — Keimdauer 6–18 Monate, Saattiefe, Frischsaat-Empfehlung
3. [Barnhaven — Sowing hellebore seed](https://www.barnhaven.com/en/content/20-hellebore-sowing-instructions) — Saattiefe/Abdeckung, Stratifikationsschema
4. [Your Flowers Guide — Growing hellebores from seed: the two-year journey](https://yourflowersguide.com/hellebore/hellebores-from-seed-two-year-journey-first-blooms/) — Keimfähigkeitsverlust, Lagerungs-/Frischeempfehlung

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Winter) | 60–90 | 1 | false | false | high |
| Vegetatives Wachstum (Frühjahr) | 60–90 | 2 | false | false | medium |
| Vegetativ (Sommer/Ruhephase) | 90–120 | 3 | false | false | high |
| Blütenanlage (Herbst) | 30–60 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Winter)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 (Halbschatten; Winterlicht) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 (natürliche Winter-Tageslänge; tagneutral — Blühinduktion kältegesteuert, keine Kurztag-Anforderung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 2–10 (Winterblüher; verträgt kurze Minusgrade) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | -5–5 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.2–0.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 (kritischer Punkt stomatären Kollaps; deutlich oberhalb Ziel-Oberkante) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 10–15 (kühlliebend; Winterblattphase) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 (unter laublosem Winter-/Vorfrühlingsbaumdach nahe offenem Tageslicht ≈ 0.5; kahle Äste heben FR minimal) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetatives Wachstum (Frühjahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (kritischer Punkt stomatären Kollaps; deutlich oberhalb Ziel-Oberkante) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 (kühl-temperierte C3-Schattenstaude; Wuchsmaximum bei kühlen Tagestemperaturen ~14 °C) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 (zunehmend beschattet bei einsetzendem Laubaustrieb des Baumdaches; Unterwuchs unter Laub höher als offenes Tageslicht ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Blüte (Winter) | 0:0:0 (keine Düngung) | 0.0 | 6.5–7.5 | — | — | — | — | — | — | — | — |
| Vegetativ Frühjahr | 1:1:1 | 0.6–1.0 | 6.5–7.5 | 100 | 40 | — | 2 | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN |
| Vegetativ Sommer | 1:1:1 | 0.4–0.8 | 6.5–7.5 | 80 | 40 | — | 1 | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN |
| Blütenanlagenphase | 0:1:1 | 0.4–0.8 | 6.5–7.5 | 80 | 30 | — | 1 | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN |

<!-- DATEN FEHLEN --> Keine Helleborus-niger-spezifischen Mikronährstoff-Lösungswerte (Mn/Zn/Cu/Mo, `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`) aus seriösen Quellen belegt; Spalten als Platzhalter angelegt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (gut verrottet) | eigen | organisch | 2–3 L/m² | Februar/März, August | Bodenverbesserung + Nährstoffe |
| Kalkhaltiger Dünger (Hornmehl + Kalk) | diverse | organisch | 20–30 g/m² | März | pH-Stabilisierung + N |
| Stauden-Langzeitdünger (niedrig dosiert) | Compo | organisch-mineralisch | 30–40 g/m² | März | light_feeder |
| Urgesteinsmehl (Basalt) | diverse | mineralisch | 100–200 g/m² | Frühjahr | Mineralstoffversorgung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| Feb–Mär | Vor/Nach Blüte | Kompost einarbeiten | 2–3 L/m² | Altes Laub vorher entfernen |
| Mär | Frühjahr | Niedrig dosierter Langzeitdünger | 30 g/m² | Zweite Düngung: August |
| Aug | Sommer | Nochmals Kompost oder Langzeitdünger | einmalig | Fördert Blütenanlage |

### 3.3 Besondere Hinweise zur Düngung

Christrosen sind Schwachzehrer und brauchen kaum Düngung. Ein unter Laubbäumen gepflanzter Helleborus versorgt sich durch das jährliche Laub weitgehend selbst. Kalkhaltige Böden sind wichtig — bei zu saurem Boden regelmäßig kälken. Keine Stickstoffgaben im Hochsommer oder Herbst.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; leicht kalkhaltig bevorzugt; kein Staunässe; im Sommer mäßig feucht | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2–3, 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 60 (nur alle 5–8 Jahre teilen; Wurzelstörungen vermeiden) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Altes Laub entfernen | VOR den Blüten; beugt Blattschwärze vor | hoch |
| Jan–Mär | Blüte genießen | Schutzglas bei extremem Frost | niedrig |
| Mär | Düngung | Kompost einarbeiten nach Blüte | mittel |
| Apr–Mai | Neues Laub belassen | Nicht schneiden! | — |
| Jul–Aug | Zweite Düngung | Kompost oder Langzeitdünger; Blütenanlagen | mittel |
| Okt–Nov | Standort wählen | Christrosen NICHT verpflanzen (Standorttreue!) | — |

**WICHTIG:** Christrosen sind sehr standorttreu und mögen keine Störungen — einmal gepflanzt 10–20 Jahre nicht mehr umsetzen.

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 1 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien; Honigtau; Ameisenpräsenz | leaf, shoot | nach Blüte (Frühjahr) | easy |
| Dickmaulrüssler | Otiorhynchus sulcatus | Buchtige Blattrandfraßstellen; Larven fressen Wurzeln | leaf, root | Herbst/Winter (Larven) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Helleborus-Blattschwärze | fungal (Coniothyrium hellebori) | Schwarze Flecken auf Blättern; Blätter welken | Altes Laub nicht entfernt; feuchte Bedingungen | 14–21 | alle |
| Helleborus-Ringspot-Virus | viral (HRV) | Hellgrüne Ringmuster, Blattdeformation | Blattläuse-Übertragung | — | alle |

**Blattschwärze-Vorbeugung:** Altes Laub IMMER im Januar/Februar vor dem Blütenauftrieb vollständig entfernen — das ist die wichtigste Pflegemaßnahme!

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Heterorhabditis bacteriophora (Nematoden) | Dickmaulrüssler-Larven | nach Herstellerangabe | 7–14 (Bodentemperatur >12°C) |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Altes Laub entfernen | cultural | — | Januar/Februar; vor Blütenauftrieb | 0 | Blattschwärze (Prävention) |
| Kupfer-Fungizid | chemical | Kupferoxydul | Sprühen bei ersten Symptomen | 14 | Blattschwärze |
| Nematoden (Steinernema kraussei) | biological | Nematoden | Gießen; ab 5°C Bodentemperatur | 0 | Dickmaulrüssler-Larven |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Gartenstauden |
| Anbaupause (Jahre) | Mehrjährig; Standort 10–20 Jahre; sehr standorttreu |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Schneeglöckchen | Galanthus nivalis | 0.9 | Gleiche Blütezeit; zusammen Winterflor | `compatible_with` |
| Winterlinge | Eranthis hyemalis | 0.9 | Gleiche Winterblüte; ergänzende gelbe Farbe | `compatible_with` |
| Farn | Dryopteris filix-mas | 0.8 | Gleicher Schattenstandort; sommerliche Laubkonkurrenz minimal | `compatible_with` |
| Hosta | Hosta spp. | 0.8 | Gleicher Schattenstandort; Sommerlaub ergänzt | `compatible_with` |
| Efeu (als Bodendecker) | Hedera helix | 0.7 | Bodendecker; schützt Wurzeln vor Austrocknung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| — | — | Keine bekannten Unverträglichkeiten; standorttreu | — | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Helleborus niger |
|-----|-------------------|-------------|-------------------------------------|
| Lenzrose | Helleborus orientalis | Gleiches Genus | Größere Farbvielfalt; mehr Sorten; blüht Feb–April |
| Schneeglöckchen | Galanthus nivalis | Gleiche Saison | Vollständig winterhart; einfache Pflege |
| Stiefmütterchen | Viola x wittrockiana | Winterblüher | Einjährig; einfache Beschaffung |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Helleborus niger,"Christrose;Weihnachtsrose;Christmas Rose",Ranunculaceae,Helleborus,perennial,day_neutral,herb,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Alpen, Balkan",yes,12,25,35,40,35,no,yes,false,false,light_feeder,false,hardy,"12;1;2;3"
```

---

## Quellenverzeichnis

1. [Gartendialog — Christrose Pflege](https://www.gartendialog.de/christrose-pflege/) — Standort, Schnitt, Blattschwärze
2. [OBI — Christrose pflanzen und pflegen](https://www.obi.de/magazin/garten/pflanzen/beetpflanzen/christrose) — Übersicht
3. [Pflanzen-Kölle — Christrose Pflegeratgeber](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-christrose-richtig/) — IPM, Düngung
4. [Gartenratgeber.net — Christrosen](https://www.gartenratgeber.net/pflanzen/christrosen-schneerosen-lenzrosen.html) — Kulturdaten
5. [Zulauf Gartencenter — Christrose](https://www.zulauf.ch/de/ratgeber/news/christrosen-helleborus) — Boden, Pflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Helleborus niger (Christmas rose)](https://www.rhs.org.uk/plants/8575/helleborus-niger/details) — Boden-pH (alkaline/neutral), Halbschatten, Wuchshöhe/-breite, "moist but well-drained"
7. [MSU Floriculture — Vernalization (parts 3 & 4)](https://www.canr.msu.edu/resources/vernalization-part-4) — Vernalisationsbedarf, day-neutral nach Kälte bei Stauden
8. [ScienceDirect — Flower development and effects of cold treatment on flowering of Helleborus niger](https://www.sciencedirect.com/science/article/pii/S030442381200026X) — Kälteperiode 2–6 Wochen bei 2–7 °C zur Blühinduktion
9. [Journal of Environmental Horticulture — Day/Night Temperatures Influence Growth and Photosynthesis of Helleborus](https://jeh.kglmeridian.com/view/journals/jenh/28/3/article-p179.xml) — Wuchs-/Photosynthese-Optimum bei kühlen Temperaturen (~14/10 °C)
10. [ScienceDirect Topics — Compensation Point](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/compensation-point) — Lichtkompensationspunkt Schattenpflanzen (Spanne)
11. [Gardener's Path — Salt-Tolerant Shade Perennials](https://gardenerspath.com/how-to/shade/7-outstanding-salt-tolerant-shade-perennials/) — Helleborus als salztolerante Schattenstaude
12. [White Flower Farm — Salt Tolerant Plants](https://www.whiteflowerfarm.com/salt-tolerant) — Helleborus auf Salztoleranz-Liste
13. [BBC Gardeners' World — How to grow hellebores](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-hellebores/) — staunässeempfindlich; tiefwurzelnd
14. [Gardener's Path — Divide and Transplant Hellebores](https://gardenerspath.com/how-to/propagation/divide-transplant-hellebores/) — Wurzeltiefe 30–45 cm, bis ~60 cm
15. [Plant Delights — Hellebores Beginner's Guide](https://www.plantdelights.com/blogs/marketing/hellebores-a-beginners-guide-to-growing-lenten-roses) — sehr langlebig (20+ Jahre), tiefwurzelnd
16. [Zhen & Bugbee 2022, New Phytologist — Photosynthesis in sun and shade: importance of far-red photons](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.18375) — Far-Red-Fraction Anker offenes/beschattetes Lichtmilieu
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
