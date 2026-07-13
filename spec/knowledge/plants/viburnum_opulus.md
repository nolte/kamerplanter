# Gewöhnlicher Schneeball — Viburnum opulus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartenheinz Gemeiner Schneeball, Lubera Schneeballstrauch, Plantura Schneeball, Naturadb Viburnum opulus, Gartenratgeber Schneeball

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Viburnum opulus | `species.scientific_name` |
| Volksnamen (DE/EN) | Gewöhnlicher Schneeball, Gemeiner Schneeball; Guelder-rose | `species.common_names` |
| Familie | Adoxaceae | `species.family` → `botanical_families.name` |
| Gattung | Viburnum | `species.genus` |
| Ordnung | Dipsacales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (ausdauernd, blüht wiederholt über mehrere Jahre) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 5 (Phänologie-Standard für Laubgehölze; Wuchs-/Austriebsbasis, budburst GDD referenced to 5 °C) | `species.base_temp` |
| Lebensdauer (Jahre) | 40+ (unter günstigen Bedingungen) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | true (winterliche Endodormanz; sommergrünes Laubgehölz) | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich | true (chilling — Endodormanz-Bruch durch Kältephase, keine echte Vernalisation) | `lifecycle_configs.vernalization_required` |
| Chilling Mindest-Tage | ca. 60–90 (Kältestratifikation ~5 °C; aus Samen-/Endodormanz-Studien) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral) — kein Kurz-/Langtagblüher, daher kein numerischer Stunden-Schwellwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; absolut winterhart in ganz Norddeutschland; einheimischer Wildstrauch | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Zentralasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Beeren für Wildvögel; rote Beeren Oktober–November giftig für Menschen) | `species.harvest_months` |
| Blütemonate | 5, 6 (Mai–Juni; weiße Doldenrispen) | `species.bloom_months` |

**Hinweis:** Viburnum opulus ist ein wichtiger Vogelnährgehölz — die roten Beeren werden von über 60 Vogelarten gefressen. Für Menschen und Haustiere giftig (roh; gekocht verarbeitet weniger problematisch).

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Halbverholzte Stecklinge im Juli/August, 15 cm lang, gut bewurzelnd. Absenker im Frühjahr.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Beeren (roh), Samen, Rinde; Blätter weniger | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Viburnin, Viopudsid (Cyanogene Glykoside) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Rohe Beeren verursachen Erbrechen und Durchfall. Nur wenige Beeren sind giftig — Kinder trotzdem fernhalten. Gekocht können Beeren verarbeitet werden (traditionell Marmelade in Osteuropa, mit Vorsicht).

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6 (nach der Blüte im Juni) | `species.pruning_months` |

**Hinweis:** Schneeball blüht auf vorjährigem Holz — Schnitt NUR direkt nach der Blüte. Kein Rückschnitt im Herbst oder Winter (vernichtet die Blütenknospen für nächstes Jahr). Verjüngungsschnitt alle 5–7 Jahre: älteste Triebe bodennah entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–500 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–400 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–300 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale, nährstoffreiche Gartenerde; pH 5,5–7,0; feuchtigkeitsspeichernd | — |

**Standort:** Sonne bis Halbschatten; feuchte bis nasse Böden; ideal an Teichrändern oder Gewässernähe. Heimisch in Erlenbrüchen und Feuchtgehölzen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch gemessener Wert für V. opulus belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch gemessener Wert für V. opulus belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade (gedeiht in lichtem Halbschatten; reichste Blüte/Fruchtbildung in voller Sonne) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: nur qualitativ belegt ("tieferes Wurzelsystem mit Reife"), keine quantitative Spanne aus seriöser Quelle --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | tolerant (verträgt zeitweise gesättigte/nasse Böden; native Feuchtgehölzart aus Erlenbrüchen) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive (salzempfindlich; vor Streusalz/Salzspray schützen) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe, Maas-Hoffman a) | <!-- DATEN FEHLEN: kein quantitativer Maas-Hoffman-Schwellwert für V. opulus belegt (qualitativ: sensitive) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m, Maas-Hoffman b) | <!-- DATEN FEHLEN: kein quantitativer Maas-Hoffman-Slope für V. opulus belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–8.0 (anpassungsfähig; mild sauer bis basisch; sehr saure Böden ungünstig; harmonisiert mit §1.6 Topf-Empfehlung pH 5,5–7,0 als engerer Kultur-Optimalbereich) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- SECTION MISSING: seed_profile — vegetativ vermehrt (Begründung: §1.3 nennt ausschließlich cutting_stem und layering als Vermehrungsmethoden; `seed` ist nicht gelistet. Zwar keimt Viburnum opulus aus Samen mit doppelter (warm+cold) Morphophysiologischer Dormanz, siehe PMC3119608 in Quelle 12 der bestehenden §1.7-Belege, doch die gartenbauliche Standardvermehrung dieser Art erfolgt praxisweit über Stecklinge/Absenker — daher entfällt gemäß Klassifikations-Regel (maßgeblich §1.3) die Seed-Profile-Sektion.) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | high |
| Blüte | 21–30 | 2 | false | false | high |
| Vegetatives Wachstum | 90–120 | 3 | false | false | high |
| Beerenreife | 60–90 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (deutlich oberhalb des Zielkorridors; kritischer Punkt stomatären Schließens ≈ oberer Zielwert 0.9 + ~0.3) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 (gemäßigtes C3-Laubgehölz) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Vollsonne ≈ 0.5; im Halbschatten unter Laub höher 0.6–0.8) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 3000–8000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Blüte/Vegetativ | 1:1:1 | 0.6–1.0 | 5.5–7.0 | 80 | 40 | — | 2 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |

<!-- Hinweis: Für V. opulus liegen keine artspezifischen Mikronährstoff-Zielkonzentrationen (Mn/Zn/Cu/Mo in ppm) aus seriösen Quellen vor; als genügsamer Schwachzehrer auf normalem Gartenboden ist eine gezielte Mikronährstoff-Düngung nicht erforderlich. -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | organisch | 4–6 L/m² | März/Oktober | Bodenverbesserung |
| Mulch (Rindenmulch) | diverse | organisch | 5–8 cm Schicht | Frühjahr | Feuchtigkeitsspeicher |
| Hornspäne (bei Bedarf) | Oscorna | organisch | 30–50 g/m² | April | Nur bei Mangelsymptomen |

### 3.2 Besondere Hinweise zur Düngung

Viburnum opulus ist ein genügsamer Einheimischer und braucht auf normalen Gartenböden KEINE gezielte Düngung. Mulchen reicht völlig. Zu viel Stickstoff schadet (weiche Triebe, mehr Schädlingsbefall). Nur bei sichtbaren Mangelsymptomen düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 6.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; mag feuchte Standorte; bei Trockenheit gießen; optimal an Gewässernähe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 180 (kaum nötig) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 (kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jun | Schnitt nach Blüte | Leicht formen; älteste Triebe entfernen | mittel |
| Sep–Nov | Beeren reifen | Dekorativ; für Vögel lassen | niedrig |
| Mär | Verjüngungsschnitt | Alle 5–7 Jahre; alte Triebe bodennah | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Frühjahrs-Maßnahme | none (keine Abdeckung zu entfernen; vollständig winterhart bis ca. -30 °C, bleibt im Freiland) | `overwintering_profiles.spring_action` |
| Winter-Maßnahme Monat | — (keine Schutzmaßnahme nötig) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme Monat | — (keine Maßnahme nötig) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | — (kein Winterquartier; freistehend im Beet) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | — (Freiland) | `overwintering_profiles.winter_quarter_light` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schneeball-Blattläuse | Aphis viburni | Starke Kolonien; zusammengerollte Blätter; Honigtau; Ameisen | leaf, shoot | vegetative (Mai–Juni) | easy |
| Viburnum-Blattfloh | Psyllidae | Wachsartige Ausscheidungen; Blattschäden | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 7–10 | vegetative (Sommer) |
| Blattflecken | fungal | Braune Flecken | Feuchtigkeit | 7–14 | vegetative |

**Blattläuse:** Schneeball-Blattläuse können massiv auftreten, schwächen aber selten die Pflanze ernsthaft. Starker Wasserstrahl zur Bekämpfung; Natürliche Feinde (Marienkäfer) fördern.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer | Blattläuse | natürliche Förderung | sofort |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Wasserstrahl | cultural | — | Kräftiger Strahl gegen Blattlauskolonien | 0 | Blattläuse |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |
| Sonniger Standort | cultural | — | Sonne reduziert Mehltau | 0 | Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Heimische Sträucher |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Holunder | Sambucus nigra | 0.9 | Heimische Mischhecke; Insekten, Vögel | `compatible_with` |
| Weißdorn | Crataegus monogyna | 0.9 | Heimische Mischhecke; Bienenweide | `compatible_with` |
| Faulbaum | Frangula alnus | 0.8 | Feuchter Standort; heimisch | `compatible_with` |
| Schlehe | Prunus spinosa | 0.8 | Heimische Mischhecke | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Viburnum opulus |
|-----|-------------------|-------------|-----------------------------------|
| Wolliger Schneeball | Viburnum lantana | Gleiches Genus | Trockener Standort; kalkliebend |
| Duftschneeball | Viburnum carlesii | Gleiches Genus | Herrlicher Duft; kleinere Form |
| Winterschneeball | Viburnum x bodnantense | Gleiches Genus | Winterblüher Oktober–März |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Viburnum opulus,"Gewöhnlicher Schneeball;Gemeiner Schneeball;Guelder-rose",Adoxaceae,Viburnum,perennial,day_neutral,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Europa, Nordafrika, Zentralasien",limited,45,40,400,300,250,no,no,false,false,light_feeder,false,hardy,"5;6"
```

---

## Quellenverzeichnis

1. [Gartenheinz — Gemeiner Schneeball](https://www.gartenheinz.de/pflanzen/straeucher/schneeball/gemeiner-schneeball/) — Steckbrief
2. [Lubera — Schneeballstrauch](https://www.lubera.com/de/gartenbuch/schneeballstrauch-pflanzen-pflegen-p2910) — Pflege
3. [Plantura — Gewöhnlicher Schneeball](https://www.plantura.garden/gehoelze/schneeball/gewoehnlicher-schneeball) — Standort, Pflege
4. [Naturadb — Viburnum opulus](https://www.naturadb.de/pflanzen/viburnum-opulus/) — Ökologischer Wert
5. [Gartenratgeber — Schneeball](https://www.gartenratgeber.net/pflanzen/schneeball-duftschneeball-winterschneeball.html) — Kulturdaten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Viburnum opulus (guelder rose)](https://www.rhs.org.uk/plants/18919/viburnum-opulus/details) — Standort, Boden, Sonne/Halbschatten, Winterhärte
7. [NC State Extension — Viburnum opulus](https://plants.ces.ncsu.edu/plants/viburnum-opulus/) — Licht (partial_shade), Boden-pH, USDA-Zonen, Feuchte-/Trockentoleranz
8. [PFAF — Viburnum opulus (Guelder Rose)](https://pfaf.org/user/Plant.aspx?LatinName=Viburnum+opulus) — Boden-pH 5.5–8.0, Standortökologie (zeitweise staunasse Lehmböden)
9. [Cornell Woody Plants Database — Viburnum opulus](https://woodyplants.cals.cornell.edu/plant/274) — Boden-pH 5.0–8.0, Feuchtetoleranz, Wuchsmaße, Lebensdauer
10. [Wisconsin Horticulture — Winter Salt Injury and Salt-tolerant Landscape Plants](https://hort.extension.wisc.edu/articles/winter-salt-injury-and-salt-tolerant-landscape-plants/) — Salzempfindlichkeit (Viburnum mit nackten Knospen sehr salzspray-anfällig)
11. [Gardens Illustrated — Viburnum (best to grow & when to prune)](https://www.gardensillustrated.com/plants/spring/viburnum-best-prune-care) — salzempfindlich, vor Salzspray schützen, Lebensdauer 40+ Jahre
12. [PMC — Deep simple epicotyl morphophysiological dormancy in Viburnum seeds](https://pmc.ncbi.nlm.nih.gov/articles/PMC3119608/) — Dormanz-/Chilling-Anforderung (Warm-/Kältestratifikation)
13. [Wikipedia — Growing degree-day](https://en.wikipedia.org/wiki/Growing_degree-day) — GDD-Konzept, Basistemperatur
14. [Klosterman et al. 2018 — Later springs green-up faster (Int. J. Biometeorology)](https://ecoss.nau.edu/wp-content/uploads/2018/11/Klosterman-et-al.-2018-International-Journal-of-Biometerology.pdf) — Laubgehölz-Budburst GDD referenziert auf 5 °C
15. [Zhen et al. 2022 — Photosynthesis in sun and shade: importance of far-red photons (New Phytologist)](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.18375) — R:FR ≈ 1.1 Vollsonne (FR-Fraction ≈ 0.5), höher im Unterwuchs
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
