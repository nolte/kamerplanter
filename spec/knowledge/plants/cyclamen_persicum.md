# Alpenveilchen — Cyclamen persicum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/cyclamen-care-guide-how-to-grow-and-maintain-cyclamen-plants/), [Missouri Botanical Garden](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a444), [UK Houseplants](https://www.ukhouseplants.com/plants/cyclamen), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cyclamen persicum | `species.scientific_name` |
| Volksnamen (DE/EN) | Alpenveilchen; Cyclamen, Persian Cyclamen, Florist's Cyclamen | `species.common_names` |
| Familie | Primulaceae | `species.family` → `botanical_families.name` |
| Gattung | Cyclamen | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert auffindbar; verfügbare Quellen nennen nur das Photosynthese-Optimum (~16 °C), nicht die GDD-Basis --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 3–10 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Sommerdormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender <!-- Quelle: growing-phase-auditor 2026-07 (Korrektur: war half_hardy) --> | `species.frost_sensitivity` |
| Winterhaerte-Detail | Frostempfindlich (tender) — nicht winterhart, verträgt keinen dauerhaften Frost; laut NC State Extension und Missouri Botanical Garden nur bis USDA Zone 9 kultivierbar (schwere Fröste töten die Pflanze). Kältestress setzt bereits unter 4°C (40°F) ein (verlangsamtes Wachstum, Blütenausfall, welkes Laub). Mindesttemperatur im Kübel 5°C. Bevorzugt kühle Temperaturen (10–18°C) in der Blütezeit. <!-- Quelle: growing-phase-auditor 2026-07 (Korrektur: war "Halbfrosthart... bis -5°C") --> | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Naher Osten (Türkei, Israel) — felsige Hänge | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Das Alpenveilchen ist eine klassische Winterblüte (Oktober–März) und bevorzugt kühle Temperaturen — im typisch warmen Zimmer (>20°C) geht es schnell ein. Idealer Standort: kühler Fensterplatz (12–16°C), keine direkte Mittagssonne. Nach der Blütezeit zieht es ins Sommer-Dormanzstadium ein (Blätter welken, Knollen im kühlen Keller lagern) und kann im Herbst neu austreiben — allerdings schwieriger als für Anfänger erwartet.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 10, 11, 12, 1, 2, 3 (Herbst bis Frühjahr) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Vermehrung durch Samen möglich aber zeitaufwändig (12–18 Monate bis zur blühfähigen Pflanze). Samen bei Dunkelheit, 18–20°C, Keimung in 4–6 Wochen. Praxistipp: Kaufpflanzen in Gärtnereien sind effizienter.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | tubers (Knollen — stark giftig), leaves, flowers (schwächer) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins (Cyclamin, Cyclamiretin) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Besonders die Knollen sind giftig und können Erbrechen, Durchfall und Herzrhythmusstörungen verursachen. Aus Reichweite von Haustieren und Kindern halten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4, 5 (verblühte Stiele und gilbende Blätter entfernen — drehen, nicht schneiden) | `species.pruning_months` |

**Hinweis:** Verblühte Stiele und gelbe Blätter nicht abschneiden, sondern durch Drehen an der Basis herausreißen — das verhindert, dass Stümpfe faulen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (kühler, geschützter Standort, kein Frost, kein Regen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, gut durchlässige Blumenerde mit 20% Perlite. pH 5.5–6.5. Nicht zu viel Erde über der Knolle (obere Knollenhälfte herausschauen lassen). | — |

---

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: kein validierter Maas-Hoffman-Schwellenwert (ECe) für Cyclamen persicum publiziert; Praxis-Richtwert ist Substrat-EC (Sättigungspaste) ≤ 1, was die Einstufung "sensitive" stützt, aber keine belegte Maas-Hoffman a darstellt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein publizierter Maas-Hoffman-Slope (b) für Cyclamen persicum --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis:** Cyclamen persicum ist eine schattenverträgliche Unterholz-Staude (shade-adapted understory herb) mit niedrigem Lichtkompensationspunkt (light compensation point) — sie behauptet sich im Halbschatten unter Baumkronen. Der angegebene Bereich nennt ausschließlich den Kompensationspunkt (Netto-Photosynthese = 0); der Sättigungspunkt (light saturation point) liegt deutlich höher und ist hier bewusst nicht eingetragen. Die Knolle besitzt keine schützende Korkschicht, sondern nur eine dünne, durchlässige Epidermis und ist dadurch besonders empfindlich gegen osmotischen Schock durch lösliche Salze (salt-sensitive); Gärtner halten die Substrat-EC (Sättigungspaste, nicht Gießwasser-EC) bei oder unter 1 dS/m. Staunässe (waterlogging) führt rasch zu Knollen-/Kronenfäule (crown rot).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 15 (ISHS: Optimum bei 15°C im Dunkeln; keine Keimung bei 5°C) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 20 (Keimung oberhalb 20°C stark gehemmt bzw. ausbleibend; praxisübliche Anzucht bei 18–20°C) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1 (Praxis-Empfehlung ~0,6–1,3 cm mit feiner Vermiculit-/Substratschicht abgedeckt — ausreichend um Dunkelheit sicherzustellen) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 30 (30–60 Tage, unterer Wert; stark temperatur- und frischeabhängig) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 2 (Trockenlagerung erhält hohe Keimfähigkeit über mind. 2 Jahre bei -30°C bis +20°C; Praxisempfehlung: Aussaat innerhalb 1 Jahres für beste Ergebnisse) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak (Einweichen 12–24 Std. in lauwarmem Wasser vor Aussaat verbessert Wasseraufnahme und Keimrate) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: keine Quelle mit TKG-Wert für Cyclamen persicum gefunden --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Einzelsaat in Schalen/Töpfen, keine Reihen-/Flächenkultur mit dokumentierter Aussaatdichte --> | `species.seed_profile.sowing_density_per_m2` |

> **Hinweis:** Cyclamen persicum ist ein ausgeprägter Dunkelkeimer — bereits sehr geringe Dauerbelichtung hemmt die Keimung (kontinuierliche Weißlichtbestrahlung wirkt inhibitorisch, auch bei niedriger Bestrahlungsstärke). Nach Keimung müssen Sämlinge zügig ans Licht (helles, indirektes Licht), da Dunkelheit danach zu Vergeilung führt. Dies harmonisiert mit der bereits in §1.3 dokumentierten Praxis (18–20°C, Dunkelheit, 4–6 Wochen).

**Quellen (§1.8):**
- [ISHS — Characteristics of Cyclamen persicum Mill. Seed Germination](https://www.ishs.org/ishs-article/261_45) — Optimum 15°C im Dunkeln, keine Keimung bei 5°C oder über 20°C, Dauerlicht-Inhibition
- [trailingpetunia.com — Cyclamen Seed Germination Secrets: Temperature, Light & Moisture Tips](https://www.trailingpetunia.com/blogs/news/cyclamen-seed-germination-secrets-temperature-light-moisture-tips) — Dunkelkeimer, 18–20°C praxisüblich, Keimdauer 30–60 Tage
- [Outside Pride — Planting Instructions for Cyclamen Seeds](https://www.outsidepride.com/resources/planting/cyclamen-planting/) und [Wilson Garden Pots — The Complete Guide to Growing Cyclamen from Seed](https://www.wilsongardenpots.com/a/growing-cyclamen-from-seed) — Saattiefe ¼–½ Zoll, Einweichen vor Aussaat
- [Missing Henry Mitchell — Cyclamen from seed: Presoaking method](https://missinghenrymitchell.com/2013/12/23/cyclamen-from-seed-presoaking-method/) und [Cyclamen Society — Growing from Seed](https://www.cyclamen.org/cyclamen-society-seeds-distribution/propagation/) — Einweichen 12–24 Std. vor Aussaat
- [PMC — Storage-related Studies zur Keimfähigkeit von Cyclamen-Samen bei -30°C bis +20°C](https://www.ncbi.nlm.nih.gov/pmc/) und [trailingpetunia.com — When to Plant Cyclamen Seeds for Best Germination Rates](https://www.trailingpetunia.com/blogs/news/when-to-plant-cyclamen-seeds-for-best-germination-rates) — Keimfähigkeitsdauer ≥2 Jahre bei Trockenlagerung, Praxisempfehlung Aussaat binnen 1 Jahr
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Vegetatives Wachstum (Herbst) | 30–60 | 1 | false | false | medium |
| Blütezeit (Winter) | 60–120 | 2 | false | false | low |
| Sommerdormanz (Mai–September) | 120–150 | 3 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum / Blütezeit (Oktober–März)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 14–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sommerdormanz (Mai–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 (kühles Halbdunkel) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–18 (kühler Keller oder Kühlraum) | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 21–42 (sehr wenig) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetativ/Blüte | 1:2:2 | 0.4–0.8 | 5.5–6.5 | 50 | 20 |
| Sommerdormanz | 0:0:0 | 0.0 | 5.5–6.5 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Vollnährlösung, aktive Phase):** Die folgenden Spurenelement-Zielwerte (micronutrients) sind kein cyclamen-spezifischer Forschungswert, sondern entsprechen den etablierten Floriculture-Vollnährlösungs-Richtwerten (Hoagland-abgeleitet); bei salzempfindlichem Cyclamen am unteren Ende anwenden.

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Vegetativ/Blüte | 0.5 | 0.05 | 0.02 | 0.01 |
| Sommerdormanz | — | — | — | — |

KA-Felder: `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm`, `nutrient_profiles.molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 2 ml/L (alle 2–3 Wochen) | Blütezeit |
| Zimmerpflanzen-Dünger | Compo | base | 7-3-6 | 2 ml/L | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Beim Umtopfen im Herbst |

### 3.2 Besondere Hinweise

Alle 2–3 Wochen während der aktiven Wachstums-/Blütezeit (Oktober–März), halbe Dosis. Im Sommer (Dormanz) nicht düngen. Stickstoffarme, P-K-reiche Formel für Blütenbildung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 28–42 (Dormanz — sehr wenig) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.2 (Winter = Hauptblütezeit = mehr gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water (von unten! Wasser NIE auf Knolle/Blattachsen) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; Unterbewässerung von unten (Knolle nicht nass machen — Fäulnis!); Erde zwischen Güssen leicht antrocknen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 10–3 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jedes Jahr im Herbst, Knollen herausnehmen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung (Sommerdormanz)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | dig_and_store | `overwintering_profiles.hardiness_rating` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 — korrigiert von needs_protection auf dig_and_store: die Knolle wird nach der Blüte eingezogen und trocken eingelagert (winter_action dig_store), das passende Enum ist dig_and_store -->
| Winter-Maßnahme | dig_store (nach Blüte einziehen lassen, Knolle trocken lagern) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 5 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | replant (im Herbst neu einpflanzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 9 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Alpenveilchen-Milbe | Phytonemus pallidus | Deformierte Blüten und Blätter, verkümmerte Knospen | difficult |
| Blattläuse | Myzus persicae | Klebrige Blätter, deformierte Triebe | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Grauschimmel (Botrytis) | fungal | Grauer Schimmelbelag auf Blüten und Blättern | Nasses Laub, zu feuchte Luft, Staunässe |
| Knollenfäule | fungal | Weiche, braune Knollenbasis | Gießen von oben, Staunässe |
| Fusarium-Welke | fungal | Einseitiges Welken | Belastetes Substrat |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Von unten gießen | cultural | Gießtechnik ändern | 0 | Botrytis, Knollenfäule (Prävention) |
| Gut belüften | cultural | Standort mit Luftzirkulation | 0 | Botrytis (Prävention) |
| Kupfermittel | biological | Sprühen 0.1% | 3 Tage | Botrytis |
| Abgestorbene Blüten entfernen | cultural | Täglich kontrollieren | 0 | Botrytis (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Neoseiulus (Amblyseius) cucumeris | Alpenveilchen-Milbe (Phytonemus pallidus) | 50–100/m² (Räuber:Beute ≥ 1:10, früh ausbringen) | 2–4 Wochen |
| Schlupfwespe | Aphidius colemani | Blattläuse (Myzus persicae) | 0.25–4/m², wöchentlich bis Mumien sichtbar | 2–3 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Myzus persicae), bei höherem Befall | 1–4/m², ergänzend zu Aphidius | 2–3 Wochen |
| Nematode | Steinernema feltiae | Trauermücken-Larven (Bradysia spp.) | ~0.5 Mio./m² Substratoberfläche (Bodengießen) | < 1 Woche (Larvenabtötung in ~48 h) |
| Raubmilbe (Boden) | Stratiolaelaps scimitus (Hypoaspis miles) | Trauermücken-Larven (Bradysia spp.) | 100–250/m² auf der Substratoberfläche | 2–3 Wochen |

**Hinweis:** Raubmilben können die Alpenveilchen-Milbe nicht vollständig tilgen — entscheidend ist die frühe Ausbringung bei niedrigem Befall (Räuber:Beute mindestens 1:10). Gegen Trauermücken wirkt die Kombination aus Nematoden (rasche Larvenabtötung) und Boden-Raubmilbe (dauerhafte Unterdrückung) am besten.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmer-/Balkonpflanze (saisonale Winterblüte).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Efeu-Alpenveilchen | Cyclamen hederifolium | Gleiche Gattung | Frosthart (USDA 5–9), für den Garten |
| Primel | Primula acaulis | Primulaceae, Winterblüte | Günstiger, einfacher zu halten |
| Kalanchoe | Kalanchoe blossfeldiana | Winterblüte | Pflegeleichter, mehr Farbvielfalt |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Cyclamen persicum,"Alpenveilchen;Cyclamen;Persian Cyclamen",Primulaceae,Cyclamen,perennial,day_neutral,herb,tuberous,"9a;9b;10a;10b;11a","Mittelmeerraum, Naher Osten",yes,0.5-3,12,15-30,15-30,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Cyclamen Care](https://www.healthyhouseplants.com/indoor-houseplants/cyclamen-care-guide-how-to-grow-and-maintain-cyclamen-plants/) — Pflegehinweise, Dormanz
2. [Missouri Botanical Garden — Cyclamen persicum](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a444) — Botanische Daten
3. [UK Houseplants — Cyclamen](https://www.ukhouseplants.com/plants/cyclamen) — Kulturdaten, Schädlinge
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig — Saponine)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [NC State Extension Gardener Plant Toolbox — Cyclamen](https://plants.ces.ncsu.edu/plants/cyclamen/) — Lichtbedarf / Schattenverträglichkeit (part shade to full shade), Standort
6. [Pacific Bulb Society — Cyclamen Tubers](https://www.pacificbulbsociety.org/pbswiki/index.php/CyclamenTubers) — Knollenbau, flaches Wurzelsystem (Wurzeln an der Knollenunterseite)
7. [RHS — Cyclamen Growing Guide](https://www.rhs.org.uk/plants/cyclamen/growing-guide) — Pflanztiefe der Knolle (flach), Wurzeltiefe
8. [Cafe Planta — Temperature Tolerance of Cyclamen](https://cafeplanta.com/a/blog/the-temperature-tolerance-of-cyclamen-a-comprehensive-guide) — Kühle Optimaltemperatur, Knospenausfall > 21 °C
9. [ResearchGate — Root-Zone Cooling Improves Growth of Cyclamen persicum under Heat Stress](https://www.researchgate.net/publication/270586317_Root-Zone_Cooling_Improves_Growth_of_Cyclamen_persicum_under_Heat_Stress) — Netto-CO₂-Assimilation maximal bei ~16 °C Wurzelzonentemperatur (Photosynthese-Optimum)
10. [Greenhouse Grower — 5 Things You Should Know About Growing Cyclamen](https://www.greenhousegrower.com/production/plant-culture/blooming-potted-production/5-things-you-should-know-about-growing-cyclamen/) — Salzempfindlichkeit, Substrat-EC ≤ 1, osmotischer Schock der Knolle
11. [UMass Extension Floriculture — Water Quality: Salinity, Sodium and Chloride](https://www.umass.edu/agriculture-food-environment/greenhouse-floriculture/fact-sheets/umass-extension-floriculture-water-quality-project-i-salinity) — Salinität / EC-Management in der Floriculture
12. [My Garden NZ — Watering Cyclamen: Overwatering Signs](https://www.mygarden.co.nz/watering-cyclamen-frequency-methods-overwatering-signs/) — Staunässe-Empfindlichkeit, Knollen-/Kronenfäule
13. [University of Arkansas — Greenhouse Mineral Nutrition (Unit 08)](https://greenhouse.hosted.uark.edu/Unit08/Printer_Friendly.html) — Floriculture-Mikronährstoff-Richtwerte (Mn/Zn/Cu/Mo)
14. [Greenhouse Grower — Understanding Plant Nutrition: Micronutrients](https://www.greenhousegrower.com/production/fertilization/understanding-plant-nutrition-fertilizers-and-micronutrients/) — Mikronährstoff-Verhältnisse in Nährlösungen
15. [Royal Brinkman — Cyclamen Mite Control](https://royalbrinkman.com/knowledge-center/crop-protection-disinfection/pests/cyclamen-mite) — Biologische Bekämpfung Alpenveilchen-Milbe (Amblyseius/Neoseiulus cucumeris)
16. [PubMed — Biological control of strawberry tarsonemid mite Phytonemus pallidus using Neoseiulus (Amblyseius)](https://pubmed.ncbi.nlm.nih.gov/11508527/) — Räuber:Beute-Verhältnis 1:10 für N. cucumeris gegen P. pallidus
17. [Sound Horticulture — Aphidius colemani](https://soundhorticulture.com/products/aphidius-colemani) — Ausbringrate Schlupfwespe gegen Blattläuse (0.25–4/m²)
18. [Bugs for Growers — Beneficial Nematodes & Predatory Mites for Fungus Gnats](https://blog.bugsforgrowers.com/natural-predators/entomopathogenic-nematodes/beneficial-nematodes/two-biocontrol-agents-for-effective-control-of-fungus-gnats/) — Steinernema feltiae + Stratiolaelaps scimitus gegen Trauermücken (Bradysia)
19. [Grokipedia — Compensation point](https://grokipedia.com/page/Compensation_point) — Lichtkompensationspunkt schattentoleranter Unterholz-Kräuter (10–50 µmol/m²/s)
20. [The Practical Planter — Soil and Fertilizer for Cyclamen](https://thepracticalplanter.com/soil-and-fertilizer-for-cyclamen/) — Boden-pH-Vorzug 5.5–6.5
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: growing-phase-auditor 2026-07 -->
21. [NC State Extension Gardener Plant Toolbox — Cyclamen persicum (species-specific)](https://plants.ces.ncsu.edu/plants/cyclamen-persicum/) — "frost tender", nur winterhart USDA Zone 9–11, Basis der `frost_sensitivity: tender`-Korrektur
22. [Cafe Planta — Cyclamen Cold Tolerance: What Temperature Is Too Cold?](https://cafeplanta.com/blogs/resources/cyclamen-cold-tolerance) — Kältestress ab < 4 °C (40 °F), Frost besonders schädlich
23. [Cyclamen Society — FAQs](https://www.cyclamen.org/faqs/) — C. persicum "not completely frost hardy", muss bei hartem Winter ins Haus geholt werden
<!-- /Quelle: growing-phase-auditor 2026-07 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
24. [ISHS — Characteristics of Cyclamen persicum Mill. Seed Germination](https://www.ishs.org/ishs-article/261_45) — Keimtemperatur-Optimum, Dunkelkeim-Anforderung
25. [trailingpetunia.com — Cyclamen Seed Germination Secrets](https://www.trailingpetunia.com/blogs/news/cyclamen-seed-germination-secrets-temperature-light-moisture-tips) — Praxis-Keimtemperatur, Keimdauer
26. [Outside Pride — Planting Instructions for Cyclamen Seeds](https://www.outsidepride.com/resources/planting/cyclamen-planting/) — Saattiefe
27. [Missing Henry Mitchell — Cyclamen from seed: Presoaking method](https://missinghenrymitchell.com/2013/12/23/cyclamen-from-seed-presoaking-method/) — Einweich-Vorbehandlung
28. [trailingpetunia.com — When to Plant Cyclamen Seeds for Best Germination Rates](https://www.trailingpetunia.com/blogs/news/when-to-plant-cyclamen-seeds-for-best-germination-rates) — Keimfähigkeitsdauer, Lagerempfehlung
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
