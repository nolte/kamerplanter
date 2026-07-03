# Kornelkirsche — Cornus mas

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Kornelkirsche, Gartenrat Kornelkirsche, Gartenratgeber Kornelkirsche, Naturadb Cornus mas

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cornus mas | `species.scientific_name` |
| Volksnamen (DE/EN) | Kornelkirsche, Herlitze, Cornel; Cornelian Cherry | `species.common_names` |
| Familie | Cornaceae | `species.family` → `botanical_families.name` |
| Gattung | Cornus | `species.genus` |
| Ordnung | Cornales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 5 | `species.base_temp` |
| Lebensdauer (Jahre) | 100–200 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich (chilling) | true | `lifecycle_configs.vernalization_required` |
| Chilling Mindest-Tage (chilling min days) | <!-- DATEN FEHLEN --> | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | — (tagneutral / day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; absolut zuverlässig in ganz Norddeutschland; einer der frühblühendsten Sträucher | `species.hardiness_detail` |
| Heimat | Südeuropa, Kleinasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Bestäuber erforderlich (requires pollinator) | false | `species.requires_pollinator` |
| Kreuzbefruchtungsgruppe (pollinator group) | — (keine pomologische Gruppe für Wildobst) | `species.pollinator_group` |
| Empf. Befruchter-Sorten (compatible pollinators) | — | `species.compatible_pollinators` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Bestäubungshinweis:** Cornus mas ist nur teilweise selbstfruchtbar (partially self-fertile). Eine einzelne Pflanze setzt Früchte an, der Fruchtbehang steigt jedoch deutlich, wenn eine zweite, andere Cornus-mas-Sorte (Cultivar) als Pollenspender in der Nähe steht — daher für Ertragsanbau zwei verschiedene Sorten pflanzen. Insektenbestäubung: die frühen Blüten (Februar/März) sind eine der ersten Bienen- und Wildbienenweiden des Jahres; Honig- und Wildbienen übernehmen den Pollentransfer. Es existiert keine numerierte pomologische Kreuzbefruchtungsgruppe wie bei Apfel/Birne, daher bleibt `pollinator_group` leer.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge oder Kauf) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 8, 9 (August–September; rote, steinfrüchtige Früchte) | `species.harvest_months` |
| Blütemonate | 2, 3 (Februar–März; VOR dem Laubaustrieb — Phänologischer Indikator!) | `species.bloom_months` |

**Phänologischer Indikator:** Die Blüte der Kornelkirsche im Februar/März ist ein klassisches Zeichen des Vorfrühlings. Einer der frühesten Bienenweide-Sträucher des Jahres.

**Ernte:** Früchte erst ernten wenn vollreif (tiefrot) — unreif sehr sauer/adstringierend. Verarbeitung zu Marmelade, Likör, Mus. Frisch ähnlich wie Sauerkirschen.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (reife Früchte essbar) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6 (nach Blüte im Juni) oder 8 (nach Ernte) | `species.pruning_months` |

**Hinweis:** Schnitt NUR direkt nach der Blüte (nicht im Winter — Knospen für nächstes Jahr sitzen an altem Holz). Verjüngungsschnitt alle 5–8 Jahre; älteste Triebe bodennah entfernen. Toleriert aber starken Rückschnitt gut.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–600 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–500 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–400 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale, leicht kalkhaltige Gartenerde; pH 6,5–8,0; gut durchlässig | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | <!-- DATEN FEHLEN --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.5–8.0 | `species.soil_ph_preference` |

**Standort-Hinweise:** Cornus mas wächst von voller Sonne bis Halbschatten (full sun to partial shade); im lichten Gehölzschatten (light woodland) noch vital, jedoch nicht im Vollschatten — daher `partial_shade`. Die Art verlangt durchlässige, frische Böden und verträgt Staunässe schlecht (Quellen betonen durchgängig "well-drained"), daher Staunässe-Toleranz `sensitive`. Salzempfindlich: keine Eignung für Küstenexposition (maritime exposure) und kein Auftausalz (deicing salt) — Klasse `sensitive`. Boden-pH 6,5–8,0 (mäßig sauer bis alkalisch; toleriert sehr kalkhaltige Böden) — harmonisiert mit §1.6 (Substrat) und §2.3 (Nährstoffprofile). Für LCP, Wurzeltiefe in cm und Maas-Hoffman-Salzparameter (ECe-Schwelle, Slope) liegen keine zwei unabhängigen, art-spezifisch belegten Quellwerte vor; Wurzelsystem ist morphologisch ein Herzwurzler (heart root, mittlere Tiefe).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Winter/Frühjahr) | 21–42 | 1 | false | false | high |
| Vegetatives Wachstum | 120–150 | 2 | false | false | high |
| Fruchtreife | 60–90 | 3 | false | true | high |
| Winterruhe | 120–150 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum / Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (Sonne bis lichter Gehölzschatten; offenes Tageslicht ≈ 0.5, Halbschatten höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 3000–8000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Vegetativ | 2:1:1 | 0.6–1.0 | 6.5–8.0 | 100 | 50 | — | 2 |
| Fruchtreife | 1:1:2 | 0.6–1.0 | 6.5–8.0 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (Mn/Zn/Cu/Mo)** — Richtwerte einer ausgewogenen Mikronährstoff-Versorgung in der Nährlösung; für den anspruchslosen Schwachzehrer Cornus mas im Freiland selten dosierungsrelevant:

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) | KA-Feld |
|-------|----------|----------|----------|----------|---------|
| Vegetativ | 0.5 | 0.25 | 0.05 | 0.05 | `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` |
| Fruchtreife | 0.5 | 0.25 | 0.05 | 0.05 | `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` |
| Winterruhe | — | — | — | — | `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | organisch | 3–5 L/m² | März/Oktober | Bodenverbesserung |
| Holzasche | — | organisch-mineralisch | 100–200 g/m² | August | Kaliumversorgung, Fruchtreife |
| Hornspäne (bei Bedarf) | Oscorna | organisch | 30–50 g/m² | April | Nur bei Mangelsymptomen |

### 3.2 Besondere Hinweise zur Düngung

Kornelkirsche ist sehr anspruchslos — auf normalen Böden kaum Düngung nötig. Im Zweijahres-Rhythmus etwas Kompost einarbeiten reicht völlig. Keine intensive Düngung (führt zu übermäßigem Wachstum auf Kosten der Fruchtbildung). Holzasche im August fördert das Ausreifen und die Fruchtqualität.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 6.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; trockenheitstolerant nach Etablierung; in Dürreperioden gießen für besseren Fruchtansatz | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 180 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 28 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Blüte bewundern | Erste Bienenweide; keine Eingriffe | niedrig |
| Jun | Schnitt nach Blüte | Leicht formen; älteste Triebe entfernen | mittel |
| Aug–Sep | Ernte | Vollreife Früchte; Marmelade, Likör, Mus | mittel |
| Okt | Kompost | Kompostgabe | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme-Monat | — (keine Maßnahme nötig) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | uncover | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme-Monat | 3 (März) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | — (winterhart im Freiland; kein Quartier nötig) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | — (Freiland) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | — (Freiland; Niederschlag genügt) | `overwintering_profiles.winter_quarter_watering` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Überwinterungshinweis:** Cornus mas ist mit Winterhärte bis ca. −25 °C (USDA 4–8) voll frosthart und überwintert ohne Schutz dauerhaft am Standort (`hardiness_rating: hardy`, `winter_action: none`). Nur junge Topf-/Kübelexemplare profitieren in sehr kalten Lagen von einem Vlies (fleece) um den Topf gegen Durchfrieren des Wurzelballens; `spring_action: uncover` bezieht sich dann auf das Entfernen eines solchen optionalen Frostschutzes im März. Ein frostfreies Winterquartier ist nicht erforderlich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | vegetative (Frühjahr) | easy |

**Hinweis:** Kornelkirsche ist außergewöhnlich robust — Schädlinge und Krankheiten sind sehr selten.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Pilzbefall (Botrytis) | fungal | Grauschimmel | Feuchte, schlechte Luftzirkulation | 7–14 | Jungpflanzen |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |
| Standortverbesserung | cultural | — | Luftzirkulation verbessern | 0 | Pilze |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Blattlaus-Schlupfwespe (parasitic wasp) | Aphidius colemani | Blattläuse (Aphis spp.) | 0,25–4 Tiere/m², 3× im Wochenabstand | Mumien nach ~2–3 Wochen |
| Gallmücke (gall midge) | Aphidoletes aphidimyza | Blattläuse (Aphis spp.) | 1–10 Tiere/m² bzw. 2–5 Puppen/m², Wdh. nach 2–4 Wochen | ~1–2 Wochen |

**Hinweis:** Da der gelistete Schädling Blattläuse (Aphidoidea) sind, kommen blattlaus-spezifische Nützlinge zum Einsatz — die Schlupfwespe *Aphidius colemani* (parasitiert Blattläuse zu "Mumien") und die räuberische Gallmücke *Aphidoletes aphidimyza*. Wegen der außergewöhnlichen Robustheit von Cornus mas ist ein Nützlingseinsatz im Freiland praktisch nie nötig; relevant höchstens bei Jungpflanzen unter Glas. Ausbringraten/m² stammen aus dem Gewächshaus-Einsatz und sind im Freiland nur als Orientierung zu verstehen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Obstgehölze / Wildfrüchte |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft; 30–80 Jahre Standzeit möglich |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Schlehe | Prunus spinosa | 0.8 | Frühe Bienenweide kombiniert; heimische Mischhecke | `compatible_with` |
| Holunder | Sambucus nigra | 0.8 | Heimische Mischhecke; Vögel | `compatible_with` |
| Wildrose | Rosa canina | 0.7 | Heimische Mischhecke | `compatible_with` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,harvest_months
Cornus mas,"Kornelkirsche;Herlitze;Cornelian Cherry",Cornaceae,Cornus,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Südeuropa, Kleinasien",limited,45,40,500,400,300,no,no,false,false,light_feeder,false,hardy,"2;3","8;9"
```

---

## Quellenverzeichnis

1. [Plantura — Kornelkirsche](https://www.plantura.garden/obst/kornelkirschen/kornelkirsche-pflanzenportrait) — Anbau, Pflege
2. [Gartenrat — Kornelkirsche](https://gartenrat.de/kornelkirsche/) — Kulturdaten
3. [Gartenratgeber — Kornelkirsche](https://www.gartenratgeber.net/pflanzen/kornelkirsche-herlitze.html) — Düngen, Schnitt
4. [Naturadb — Cornus mas](https://www.native-plants.de/946/kornelkirsche) — Steckbrief
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Plants For A Future — Cornus mas](https://pfaf.org/user/plant.aspx?latinname=Cornus+mas) — pH-Spanne (mäßig sauer bis sehr alkalisch), Schattentoleranz (Halbschatten, kein Vollschatten), Herzwurzler, keine maritime Exposition
6. [The Morton Arboretum — Cornelian-cherry Dogwood](https://mortonarb.org/plant-and-protect/trees-and-plants/cornelian-cherry-dogwood/) — Licht (full sun/partial shade), alkalitolerant, urbantolerant außer Auftausalz, GDD-Phänologie-Tracking
7. [NC State Extension — Cornus mas](https://plants.ces.ncsu.edu/plants/cornus-mas/) — pH-Bereich, Lichtexposition, Drainage/Bodenarten
8. [Missouri Botanical Garden — Cornus mas](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=c290) — Standort, full sun to part shade, alkalitolerant
9. [Penn State Extension — When Corneliancherry Dogwood Blooms](https://extension.psu.edu/when-corneliancherry-dogwood-blooms-spring-is-not-far-behind) — Frühblüher-Phänologie, Auftausalz-Empfindlichkeit
10. [Plantura UK — Cornelian cherry overview](https://plantura.garden/uk/fruits/cornelian-cherry/cornelian-cherry-overview) — Lebensdauer (>100 Jahre), Wuchsrate
11. [Uncommon Fruit (UW-Madison CIAS) — Cornelian Cherry](https://uncommonfruit.cias.wisc.edu/cornelian-cherry/) — Teil-Selbstfruchtbarkeit, Kreuzbestäubung zweier Sorten empfohlen, Bienenweide
12. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Nützling gegen Blattläuse, Ausbringrate, Etablierung (Mumien)
13. [Koppert — Aphidend (Aphidoletes aphidimyza)](https://www.koppert.com/aphidend/) — Räuber-Gallmücke gegen Blattläuse, Ausbringrate
14. [Wikipedia / GDD5-Phänologie temperate Gehölze](https://en.wikipedia.org/wiki/Growing_degree-day) — GDD-Basistemperatur 5 °C als Standard-Wuchs-/Phänologie-Basis temperater Laubgehölze
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
