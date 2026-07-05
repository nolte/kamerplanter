# Luzerne — Medicago sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Medicago sativa, Samen.de Luzerne Gründüngung, Demonet-kleeluzplus Steckbrief Luzerne, Transgen Luzerne

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Medicago sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Luzerne, Ewiger Klee; Alfalfa, Lucerne | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Medicago | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 5 | `species.base_temp` |
| Lebensdauer (Jahre) | 3–8 (in kalten Wintern länger; produktiver Bestand meist 3–5) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (Herbst-/Winterruhe der mehrjährigen Pflanze, photoperiod-/temperaturinduziert) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (Vernalisation beschleunigt Blüte um 2–16 Tage, ist aber nicht obligatorisch) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht erforderlich) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> (quantitativer Langtagblüher ohne scharfen kritischen Schwellenwert; Blüte über Maximal-Optimal-Photoperiode gesteuert) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; tief Pfahlwurzel bis 10 m; gut etablierte Pflanzen sehr winterhart | `species.hardiness_detail` |
| Heimat | Vorderasien (Iran, Zentralasien); weltweit kultiviert | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5, 8 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (Futterpflanze: 2–4 Schnitte/Jahr; Gründüngung: einarbeiten) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (essbar; Keime und Blätter beliebt) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Saponine in Samen (in normalen Mengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6, 7, 8 (Mahd regt Neuaustrieb an) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — (extrem tiefe Pfahlwurzel: >1 m) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5–15 (Flächenansaat: 15–20 g/m²) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (keine Topfkultur; Freilandeinsatz als Gründüngung) | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (kein artspezifischer Messwert aus seriösen Quellen belegt) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (schattenintolerant; Schattenmeider, < 50 % Vollsonne führt zu Wuchsdepression) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 90–300 (effektiv; Maximum bis 700–900 in tiefgründigen Böden) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (verträgt keine Staunässe/Bodenverdichtung; Wurzelfäule-Risiko) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 2.0 (Maas-Hoffman a; Bezug: Substrat-ECe im Sättigungsextrakt, nicht Gießwasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 7.3 (Maas-Hoffman b; Ertragsrückgang je dS/m über Schwelle) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug | 6.5–7.5 (unter 6.5 versagt Rhizobium-Symbiose; harmonisiert mit §1.6/§2.3) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 18 (praktikables Optimum 65–72°F laut Ag Proud/UC Davis-Quellen) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 25 (weitere Studien nennen Optimum 20–25°C bzw. 25–30°C; Keimung theoretisch auch nahe 0°C, aber dann sehr langsam — hier praktischer Optimalbereich) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.6–1.9 (0,6–1,2 cm auf mittleren/feinen Böden, bis 1,9 cm auf Sandböden; Übertiefe Aussaat = Haupt­ursache für Etablierungsausfall) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (7–14 Tage unter optimalen Bedingungen; bei 10°C ca. 3 Tage bis 50 % Keimung, nahe 0°C bis zu 15 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 5 (praktische Nutzungsgrenze für Aussaatgut); dokumentiertes Extrem: 81 % Keimfähigkeit nach 19 Jahren Lagerung im ungeheizten Lagerschuppen | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | indifferent (Aussaat wird durchgängig flach bedeckt/eingearbeitet empfohlen und keimt zuverlässig; kein Beleg für obligate Lichtkeimung) | `species.seed_profile.light_germination` |
| Vorbehandlung | scarification (45–73 % harte, wasserundurchlässige Samen je nach Herkunft; Handelssaatgut wird meist bereits mechanisch skarifiziert, bei selbst gewonnenem Saatgut zusätzliche Skarifikation empfohlen) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 2.3 (aus 190.000–230.000 Samen/lb bzw. ≈ 199.000/lb errechnet; zwei unabhängige Quellen im Bereich 2,2–2,5 g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 480–740 (errechnet aus praxisüblicher Drillsaat-Aussaatstärke 10–15 lb PLS/acre ≈ 1,1–1,7 g/m² ÷ TKG 2,3 g; bei Breitsaat/Übersaat entsprechend höher) | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
1. [US Forest Service FEIS — Medicago sativa, alfalfa](https://research.fs.usda.gov/feis/species-reviews/medsat) — Keimfähigkeitsdauer 81 % nach 19 Jahren Lagerung (ungeheizter Schuppen), ca. 200.000 Samen/lb
2. [Wisconsin Team Forage — Seeding Rate of Different Alfalfa Seed Lots](https://fyi.extension.wisc.edu/forage/seeding-rate-of-different-alfalfa-seed-lots/) — Cross-Check Seeds/lb (190.000–230.000, Ø ≈ 199.000/lb) → TKG ≈ 2,28 g
3. [Iowa State Extension — Establishing a New Stand of Alfalfa](https://crops.extension.iastate.edu/cropnews/2023/04/establishing-new-stand-alfalfa) — Saattiefe 1/4–1/2 Zoll (Lehm/Feinboden), 3/4 Zoll (Sand); Übertiefe Aussaat als Hauptausfallursache
4. [MSU Extension — Planting methods for successful alfalfa establishment](https://www.canr.msu.edu/news/planting_methods_for_successful_alfalfa_establishment) — Aussaatrate 10–15 lb PLS/acre (Drillsaat), 18–20 lb/acre (Breitsaat)
5. [Ag Proud — Maximize seeding yield: Plant early](https://www.agproud.com/articles/57380-maximize-seeding-yield-plant-early) — Keimtemperatur-Optimum 65–72°F (18–22°C); Keimung bis nahe 0°C möglich, aber stark verlangsamt (15 Tage bis 50 % Keimung bei 32°F)
6. [Scialert — Seed Scarification Methods and their Use in Forage Legumes](https://scialert.net/fulltext/?doi=rjss.2012.38.50) — 45–73 % harte Samen bei Luzerne je nach Herkunftsregion; mechanische Skarifikation als effektivste Methode
7. [ResearchGate — Germination and growth of old alfalfa (Medicago sativa L.) seeds on soil](https://www.researchgate.net/publication/249467314_Germination_and_growth_of_old_alfalfa_Medicago_sativa_L_seeds_on_soil) — Cross-Check Langzeit-Keimfähigkeit alten Saatguts
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Jungpflanze (1. Jahr) | 60–90 | 2 | false | false | medium |
| Etablierungsphase | 90–120 | 3 | false | false | high |
| Produktionsphase | fortlaufend (mehrjährig) | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Produktionsphase

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (vollsonnig optimal) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.0 (kritischer Punkt stomatären Kollaps; oberer Zielwert 1.6 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–28 (Wachstums-/Photosynthese-Optimum; Rückgang über 30 und unter 10) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-Vollsonne; R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | — (Niederschlag; sehr trockenheitsresistent durch Tiefwurzel) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | — | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5–7.5 | – | – | – | – |
| Jungpflanze | 0:1:1 (KEIN N; fixiert selbst) | 0.5–0.8 | 6.5–7.5 | 80 | 30 | – | 1 |
| Produktion | 0:1:2 | 0.6–1.0 | 6.5–7.5 | 120 | 50 | – | 2 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
Mikronährstoffe (Gewebe-Sufficiency-Ranges, Ganzpflanze zur Vollblüte; Bezug Produktionsphase):

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Produktion | 30–50 | 20–70 | 5–25 | 1–5 |

KA-Felder: `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm`, `nutrient_profiles.molybdenum_ppm`. Werte = ausreichende Gewebekonzentration (kritische Untergrenzen: Mn > 15, Zn > 12, Cu > 5, Mo > 0.8). Luzerne hat zudem einen relativ hohen Bor-Bedarf (B-Sufficiency 20–100 ppm).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Gründüngungsleistung

| Parameter | Wert |
|-----------|------|
| N-Fixierung (gesamt) | 300–600 kg N/ha/Jahr (Wurzel + Spross) |
| N-Fixierung (für Folgekultur verfügbar) | 100–200 kg N/ha |
| Einarbeitungszeitpunkt | Ende der Blüte; vor Samenreife (max. N-Gehalt) |
| Einarbeitungstiefe | 20–25 cm; Tiefpflügen sinnvoll |
| Wartezeit vor Folgekultur | 4–6 Wochen nach Einarbeitung |
| Gründüngungsleistung vs. Rotklee | Höher (mehr Biomasse, tiefere Wurzeln) |

### 3.2 Begleitdüngung

Grundsätzlich KEIN Stickstoff. Nur bei Anlage auf sehr armen Böden Startgabe P und K:

| Produkt | Marke | Typ | Ausbringrate | Saison | Hinweis |
|---------|-------|-----|-------------|--------|---------|
| Rohphosphat oder Superphosphat | – | mineral/organisch | 30–40 g/m² | vor Aussaat | Nur auf P-armen Böden |
| Kaliumsulfat | – | mineral | 20–30 g/m² | vor Aussaat | Nur auf K-armen Böden |
| Kalk | – | mineral | 100–200 g/m² | vor Aussaat | Bei pH < 6,5 unbedingt kalken |
| Rhizobium meliloti Impfpräparat | – | biologisch | nach Hersteller | zur Aussaat | Bei Erstanbau auf neuem Boden empfohlen |

### 3.3 Besondere Hinweise zur Düngung

Luzerne fixiert bis zu 600 kg N/ha/Jahr — mehr als alle anderen Leguminosen. pH-Wert MUSS über 6,5 liegen — bei saureren Böden funktioniert die Rhizobium-Symbiose nicht. Auf typischen norddeutschen Sandböden pH vor Anbau prüfen und ggf. kalken. Luzerne erschließt durch ihre bis zu 10 m tiefen Pfahlwurzeln Nährstoffe aus Schichten, die andere Pflanzen nicht erreichen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 (sehr trockenheitsresistent) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; verträgt Trockenheit sehr gut; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Gründüngungsplan im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Mai | Frühjahrsaussaat | Saatbett gut vorbereiten; pH prüfen; 15–20 g/m²; 1 cm tief | hoch |
| Mär–Apr | Kalkgabe (bei Bedarf) | Kohlensaurer Kalk; 100–200 g/m²; mindestens 4 Wochen vor Aussaat | hoch |
| Jun–Jul (1. Jahr) | Erste Mahd (optional) | Gründüngungssaison; oder wachsen lassen | niedrig |
| Aug–Sep | Einarbeitung (Gründüngung) | Vor Samenreife eingraben; 20–25 cm tief; Mulchen möglich | hoch |
| Sep | Herbstaussaat (Folgekultur) | Nach Einarbeitung 4–6 Wochen warten | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Luzerneblattkäfer | Hypera postica | Fraßschäden; Larvenfraß innen | leaf, stem | vegetative | medium |
| Blattläuse | Acyrthosiphon pisum | Kolonien; Welke | shoot | spring, summer | easy |
| Kleespitzmaus | Apion spp. | Samenfraß | flower, seed | flowering | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal (Erysiphe pisi) | Weißer Belag | Trockenheit | 5–10 | vegetative |
| Luzernewelke | fungal (Fusarium spp.) | Welken, Wurzelfäule | Staunässe | 14–21 | alle |
| Blattflecken | fungal (Pseudopeziza medicaginis) | Braune Flecken | Feuchte | 7–14 | vegetative |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Fruchtfolge (5–6 Jahre) | cultural | – | Keine Luzerne auf luzernemüdem Boden | 0 | Fusarium |
| pH korrekt einstellen | cultural | – | Kalkung bei pH < 6,5 | 0 | allgemein |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit |
|----------|--------------------|----------------|---------------------|------------------|
| Blattlaus-Schlupfwespe | Aphidius colemani | Blattläuse (z. B. Erbsenblattlaus Acyrthosiphon pisum) | 0,25–0,5 | wenige Tage bis Schlupf |
| Räuberische Gallmücke | Aphidoletes aphidimyza | Blattläuse (über 60 Arten) | 0,5–1,0 | wenige Tage bis Schlupf |

Hinweis: Vorbeugender Einsatz bei erstem Blattlaus-Befall; im Freiland-Gründüngungsbestand ist Nützlingseinsatz selten nötig, eher relevant unter Glas/Folie oder bei Samenvermehrung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (nitrogen_fixer) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide, Hackfrüchte |
| Empfohlene Nachfrucht | Alle Kulturen; besonders Getreide, Kohl, Rüben |
| Anbaupause (Jahre) | 5–6 Jahre auf gleicher Fläche (Luzernewelke-Prävention) |

### 6.2 N-Hinterlassenschaft für Nachkulturen

| Folgekultur | N-Verfügbar (kg N/ha) | Empfehlung |
|------------|----------------------|------------|
| Winterweizen | 100–200 | Stark reduzierter Düngebedarf |
| Mais | 100–150 | Ideale Vorkultur |
| Kohlrabi/Brokkoli | 120–200 | Sehr starker Effekt |
| Kartoffeln | 80–150 | Rhizoctonia-Risiko prüfen |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Medicago sativa |
|-----|-------------------|-------------|-----------------------------------|
| Rotklee | Trifolium pratense | Gleiche Familie; Gründüngung | Weniger Ansprüche an pH; auch saure Böden; kürzer |
| Inkarnatklee | Trifolium incarnatum | Gleiche Familie | Winterzwischenfrucht; frostgar |
| Weißklee | Trifolium repens | Gleiche Familie | Permanent; Untergrasansaat möglich |
| Gelbsenf | Sinapis alba | Gründüngung | Schnell; kein pH-Problem; nur einjährig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Medicago sativa,"Luzerne;Ewiger Klee;Alfalfa;Lucerne",Fabaceae,Medicago,perennial,long_day,herb,taproot,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",-0.1,"Vorderasien, Zentralasien",no,,,90,40,10,no,no,false,false,nitrogen_fixer,true,hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Naturadb Medicago sativa](https://www.naturadb.de/pflanzen/medicago-sativa/) — Steckbrief, Standort
2. [Samen.de Luzerne Gründüngung](https://samen.de/blog/luzerne-der-bodenverbesserer-im-garten.html) — Gründüngungsleistung
3. [Demonet-kleeluzplus Steckbrief Luzerne](https://www.demonet-kleeluzplus.de/mam/cms15/dateien/steckbrief_luzerne.pdf) — N-Fixierung, Anbaudaten
4. [Transgen Luzerne Lexikon](https://www.transgen.de/lexikon-nutzpflanzen/1861.luzerne.html) — Allgemein
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [FAO Land & Water — Alfalfa Crop Information](https://www.fao.org/land-water/databases-and-software/crop-information/alfalfa/en/) — GDD-Basistemperatur (~5 °C), Wachstums-Optimum ~25 °C, Wurzeltiefe, Wasseransprüche
6. [University of Minnesota Extension — Using GDD to plan early-season alfalfa harvests](https://extension.umn.edu/forage-harvest-and-storage/using-growing-degree-days-plan-early-season-alfalfa-harvests) — GDD-Basistemperatur 5 °C (Wuchsphase)
7. [Lorenzo et al. 2019, The Plant Journal — Shade delays flowering in Medicago sativa](https://onlinelibrary.wiley.com/doi/abs/10.1111/tpj.14333) — Langtag-Verhalten, Schattenintoleranz (< 50 % Vollsonne)
8. [Maron et al. 2022, Front. Plant Sci. — Shade Delayed Flowering and Decreased Reproductive Growth of Medicago sativa](https://pmc.ncbi.nlm.nih.gov/articles/PMC9203126/) — Schattenmeider, Vollsonnenbedarf
9. [Annals of Botany (Oxford) 2024 — Thriving in a salty future: salt stress adaptations in alfalfa](https://academic.oup.com/aob/article/134/7/1113/7746500) — Salztoleranz Maas-Hoffman: ECe-Schwelle 2,0 dS/m, Slope 7,3 %/dS/m, Klasse moderately sensitive
10. [USDA-ARS — Plant Salt Tolerance (Chapter 13)](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — Maas-Hoffman-Modell, Salztoleranz-Klassifikation Luzerne
11. [Feedipedia — Alfalfa (Medicago sativa)](https://www.feedipedia.org/node/275) — Wurzeltiefe (4–9 m), Staunässe-Empfindlichkeit, Bodenansprüche
12. [PMC — Photosynthesis & C3 classification / waterlogging stress in alfalfa](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6471898/) — C3-Photosynthese, Staunässe-Sensitivität
13. [Utah State University Extension — Alfalfa Nutrient Management Guide](https://extension.usu.edu/crops/research/alfalfa-nutrient-management-guide) — Mikronährstoff-Gewebe-Sufficiency (Mn, Zn, Cu, Mo, B)
14. [Montana State University — Nutrient Management Guide for Dryland and Irrigated Alfalfa](https://agresearch.montana.edu/wtarc/producerinfo/agronomy-nutrient-management/Alfalfa/NutrientManagementGuide.pdf) — Mikronährstoff-Sufficiency-Ranges (Mn 30–50, Zn 20–70, Cu 5–25, Mo 1–5 ppm)
15. [Front. Plant Sci. 2022 — Dormancy under lower temperature in Medicago sativa](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.872839/full) — Herbst-/Winterdormanz photoperiod-/temperaturinduziert; Vernalisation nicht obligatorisch
16. [US Forest Service FEIS — Medicago sativa](https://research.fs.usda.gov/feis/species-reviews/medsat) — Lebensdauer/Persistenz (3–8 Jahre, länger in kalten Wintern)
17. [Koppert / re-natur — Nützlinge gegen Blattläuse (Aphidius colemani, Aphidoletes aphidimyza)](https://www.koppertbio.de/nachrichten/unser-a-team-gegen-blattlaeuse/) — Ausbringraten, Etablierungszeit
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
