# Thymian — Thymus vulgaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Thymian, NaturaDB Thymus vulgaris, Pflanzentanzen.de winterharte Kräuter

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Thymus vulgaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Thymian, Echter Thymian, Gartenthymian; Thyme, Garden Thyme | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Thymus | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −15 °C bis −20 °C je nach Sorte; in Norddeutschland ohne Schutz überwinterungsfähig; bei Kahlfrösten Vlies empfohlen | `species.hardiness_detail` |
| Heimat | Westliches Mittelmeer (Südfrankreich, Spanien) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Thymus vulgaris auffindbar; Keim-Basiswerte nicht als Wuchsbasis umetikettiert --> | `species.base_temp` |
| Lebensdauer (Jahre) | 3–5 (danach verholzend, Verjüngung/Neuanlage empfohlen) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (winterliche Wachstumsruhe in Mitteleuropa) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (Blüte GDD-/tageslängengesteuert, kein Kältebedarf zur Blühinduktion) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht erforderlich) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurztag-/Langtag-Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 | `species.direct_sow_months` |
| Erntemonate | 3, 4, 5, 6, 7, 8, 9, 10 (außerhalb des Winters) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false (in kleinen Mengen) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Thymol (antimikrobiell; in Medizindosen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (nach der Blüte; um 1/3) | `species.pruning_type` |
| Rückschnitt-Monate | 4, 7 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr viel Licht nötig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Magere, durchlässige Erde (Kräutererde + 30% Quarzsand/Kies); pH 6,0–8,0 | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP für Thymus vulgaris publiziert. Hinweis (Freitext): sonnen-adaptierte Arten liegen typischerweise bei ~20–100+ µmol/m²/s --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–40 (Pfahlwurzel mit feinem Faserwerk; meist flach) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (a) für Thymus vulgaris --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope (b) --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–8.0 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (Batch 11, Issue #301 seed-profile-backfill) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 15 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 21 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer; nur andrücken, Abdeckung von wenigen Millimetern verhindert die Keimung vollständig) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14 (unterer Wert; Spanne 14–28 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (Spanne 3–5) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light (photoblastisch) | `species.seed_profile.light_germination` |
| Vorbehandlung | keine | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 0.2 (Spanne 0.15–0.23; errechnet aus Saatgutkatalogdaten, z. B. 4.305 Korn/g bzw. ~170.000 Korn/oz) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Anzucht erfolgt praxisüblich oberflächlich in Schalen/Töpfen zur späteren Pikierung, keine belegte Freiland-Direktsaatdichte --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):** [Growing Thyme: A Complete Guide — Burpee](https://www.burpee.com/blog/thyme_article10024.html) und [Growing Thyme From Seed: A How-To Guide — Savvy Gardening](https://savvygardening.com/growing-thyme-from-seed/) (Keimtemperatur 15–21 °C, Keimdauer 14–28 Tage, Lichtkeimer, Oberflächenaussaat); [Growing Thyme from Seed: How to Plant and Harvest — Meadowlark Journal](https://meadowlarkjournal.com/blog/growing-thyme-from-seed) (Bestätigung Lichtkeimung, Saattiefe); [Vulgaris, Thyme Seed — UF Seeds](https://www.ufseeds.com/product/vulgaris-thyme-seed---1-ounce/THVUG-1oz.html) (4.305 Korn/g Katalogdaten) und allgemeine Saatgut-Viabilitätsreferenzen für Kräuter ([Seed Viability Chart — High Mowing Organic Seeds](https://www.highmowingseeds.com/blog/seed-viability-chart/), [Seed Storage Guidelines — Johnny's Selected Seeds](https://www.johnnyseeds.com/growers-library/reference-documents/seed-storage-guidelines.html)) für die Keimfähigkeitsdauer 3–5 Jahre.
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzeln | 21–42 | 1 | false | false | low |
| Aktives Wachstum (Apr–Okt) | 180–210 | 2 | false | true | high |
| Blüte | 21–42 | 3 | false | true | high |
| Winterruhe (Nov–Mär) | 120–150 | 4 | false | true (sparsam) | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (Volllsonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 (kritischer stomatärer Kollaps; oberhalb des 2.0-Ziels) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low (trockenheitstolerante Mittelmeerart) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland/Vollsonne, R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Einwurzeln | 1:2:1 | 0.5–0.7 | 6.0–7.5 | 50 | 25 | — | 1 | 0.5 | 0.3 | 0.1 | 0.05 |
| Aktives Wachstum | 1:1:1 | 0.7–1.0 | 6.0–8.0 | 70 | 35 | — | 1 | 0.8 | 0.3 | 0.1 | 0.05 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt, sehr sparsam)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 0.3 L/Pflanze | 1× im Frühjahr |

#### Mineralisch (bei Bedarf)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kräuter-Dünger | Compo | base | 10-4-10 | 3–5 g/Pflanze | 1× Frühjahr |

### 3.2 Besondere Hinweise zur Düngung

Thymian NICHT düngen — magrerem Boden entspricht höherem Thymolgehalt und intensiverem Aroma. Jährliche Frühjahrsgabe von etwas Kompost genügt vollständig. Bei zu viel Nährstoffen verliert er seinen typischen Geschmack.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gut abtrocknen lassen zwischen Gaben; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 (kaum düngen!) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–5 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Rückschnitt | Um 1/3 zurückschneiden, Holzige Triebe entfernen | hoch |
| Mai | Auspflanzen (Neupflanzung) | Nach Eisheiligen | mittel |
| Jun–Jul | Ernte & Rückschnitt nach Blüte | Nach der Blüte nochmals kürzen fördert neues Wachstum | mittel |
| Jun–Aug | Ernte | Junge Triebe regelmäßig ernten | mittel |
| Okt | Wintervorbereitung | Im Kübel: reinbringen oder schützen; im Beet: leichtes Mulchen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme | mulch (Laub oder Reisig) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover, prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | −15 (im Beet ohne Schutz möglich in Zone 7b) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste (bei Trockenheit) | leaf | summer (Hitze/Trockenheit) | medium |
| Thymian-Gallmücke | Jaapiella thymicola | Deformierte Blätter, Gallen | leaf | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Phytophthora) | Welke trotz feuchtem Substrat | Staunässe | 5–14 | all |
| Echter Mehltau | fungal | Weißlicher Belag | Feuchtigkeit + Wärme | 5–10 | vegetative |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit |
|----------|---------------------|----------------|--------------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–50 (kurativ; bei 20–25 °C und >60–70 % rF) | ~7–14 Tage (Generationszyklus 4–7 Tage bei 20–25 °C) |

Hinweis: Wirksam zwischen 13–27 °C, nicht über 30 °C; empfindlich gegen rF < 70 %. Für die Thymian-Gallmücke (Jaapiella thymicola) ist kein etablierter kommerzieller Nützling belegt — hier greifen kulturelle Maßnahmen (befallene Triebe entfernen).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Durchlüftung sicherstellen | cultural | — | Nicht zu dicht pflanzen | 0 | Mehltau, Wurzelfäule |
| Neemöl | biological | Azadirachtin | Sprühen, 0.3% | 3 | Spinnmilbe |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kohlgewächse | Brassica oleracea | 0.9 | Thymian-Duft vertreibt Kohlfliege und Weißling | `compatible_with` |
| Rosmarin | Salvia rosmarinus | 0.9 | Gleiche Standortansprüche | `compatible_with` |
| Erdbeere | Fragaria × ananassa | 0.8 | Schützt vor Schädlingen | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Thymian fördert Geschmack der Tomate | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Unterschiedliche Wasseransprüche | mild | `incompatible_with` |
| Minze | Mentha spicata | Minze breitet sich aus und überwächst Thymian | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Thymian |
|-----|-------------------|-------------|--------------------------|
| Zitronenthymian | Thymus citriodorus | Gleiche Gattung | Zitroniges Aroma; etwas frostempfindlicher |
| Breitblättriger Thymian | Thymus pulegioides | Gleiche Gattung | Robuster, stärker wüchsig |
| Oregano | Origanum vulgare | Gleiche Familie, ähnl. Aroma | Wüchsiger, einfacher in der Pflege |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Thymus vulgaris,"Thymian;Echter Thymian;Gartenthymian;Thyme",Lamiaceae,Thymus,perennial,day_neutral,shrub,fibrous,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.2,"Westliches Mittelmeer",yes,4,15,40,40,25,limited,yes,false,false,light_feeder,hardy,"3;4;5","3;4;5;6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Winterharte Kräuter — Plantura](https://www.plantura.garden/kraeuter/kraeuter-anbauen/winterharte-kraeuter) — Winterhärte
2. [Mehrjährige Kräuter — Hortica.de](https://hortica.de/mehrjaehrige-kraeuter-liste/) — Übersicht
3. [Pflanzentanzen.de Winterharte Küchenkräuter](https://pflanzentanzen.de/pflanzentipps/nutzpflanzen/kraeuter/winterharte-kraeuter/) — Praxis-Tipps
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
4. [NC State Extension — Thymus vulgaris Plant Toolbox](https://plants.ces.ncsu.edu/plants/thymus-vulgaris/) — Lichtbedarf (full sun), Boden-pH, Staunässe-Empfindlichkeit, Salztoleranz, Lebensform (woody perennial)
5. [PFAF — Thymus vulgaris Plant Database](https://pfaf.org/user/plant.aspx?LatinName=Thymus+vulgaris) — Schattenintoleranz (cannot grow in shade), pH (neutral/alkalisch), Staunässe-Empfindlichkeit, Pfahlwurzel, Winterhärte (−15 °C)
6. [Scientific Reports (Nature) — Salinity stress responses of Thymus vulgaris in hydroponics](https://www.nature.com/articles/s41598-025-00768-y) — Salztoleranz-Einstufung (moderately tolerant to severe salt stress)
7. [Gardenia.net — Thymus vulgaris](https://www.gardenia.net/plant/thymus-vulgaris) — produktive Lebensdauer (3–5 Jahre, Verjüngung)
8. [Cornell NYSIPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Raubmilbe gegen Spinnmilbe, Generationszyklus/Etablierungszeit
9. [Koppert — Spidex (Phytoseiulus persimilis)](https://www.koppert.com/spidex/) — Ausbringrate, Temperatur-/Feuchte-Fenster
10. [Cornell Greenhouse — Hydroponic Recipes (Resh/Cornell)](http://hort.cornell.edu/greenhouse/crops/factsheets/hydroponic-recipes.pdf) — Mikronährstoff-Richtwerte Mn/Zn/Cu/Mo
11. [Penn State Extension — Hydroponics Plant Nutrition (Mikronährstoffe)](https://extension.psu.edu/hydroponics-systems-and-principles-of-plant-nutrition-essential-nutrients-function-deficiency-and-excess) — Mikronährstoff-Richtwerte Mn/Zn/Cu/Mo
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Steckbrief-Erweiterung 2026-07 (Batch 11, Issue #301 seed-profile-backfill) -->
12. [Growing Thyme: A Complete Guide to Planting, Care, Harvest, and Maintenance — Burpee](https://www.burpee.com/blog/thyme_article10024.html) — Keimtemperatur, Keimdauer
13. [Growing Thyme From Seed: A How-To Guide for Beginners — Savvy Gardening](https://savvygardening.com/growing-thyme-from-seed/) — Lichtkeimung, Oberflächenaussaat
14. [Growing Thyme from Seed: How to Plant and Harvest — Meadowlark Journal](https://meadowlarkjournal.com/blog/growing-thyme-from-seed) — Bestätigung Lichtkeimung
15. [Vulgaris, Thyme Seed — UF Seeds](https://www.ufseeds.com/product/vulgaris-thyme-seed---1-ounce/THVUG-1oz.html) — Saatgutkatalogdaten (4.305 Korn/g)
16. [Seed Viability Chart — High Mowing Organic Seeds](https://www.highmowingseeds.com/blog/seed-viability-chart/) und [Seed Storage Guidelines — Johnny's Selected Seeds](https://www.johnnyseeds.com/growers-library/reference-documents/seed-storage-guidelines.html) — Keimfähigkeitsdauer Kräutersaatgut
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 -->
