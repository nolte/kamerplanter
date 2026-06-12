# Zimmeraralie, Japanische Aralie — Fatsia japonica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/japanese-aralia-fatsia-japonica-complete-care-growing-guide/), [NC State Extension](https://plants.ces.ncsu.edu/plants/fatsia-japonica/), [Gardening Know How](https://www.gardeningknowhow.com/houseplants/aralia-plants/japanese-aralia-care.htm), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Fatsia japonica | `species.scientific_name` |
| Volksnamen (DE/EN) | Zimmeraralie, Japanische Aralie; Japanese Aralia, False Castor Oil Plant, Paperplant | `species.common_names` |
| Familie | Araliaceae | `species.family` → `botanical_families.name` |
| Gattung | Fatsia | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Fatsia japonica auffindbar; Keim-Kardinaltemperaturen wären nicht als Wuchsbasis übertragbar --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Typische Lebensdauer (Jahre) | 10–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | Entfällt — tagneutral (day_neutral), kein Kurz-/Langtagblüher | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — winterhart bis -10°C in Zone 8. Mindesttemperatur in Zimmerkultur 5°C. Bevorzugt kühle Bedingungen (10–20°C). | `species.hardiness_detail` |
| Heimat | Japan, Südkorea — gemäßigte Küstenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Fatsia japonica ist eine der wenigen Zimmerpflanzen, die kühle Temperaturen und Halbschatten bevorzugen — ideal für ungeheizte Treppenhäuser, Wintergärten und nordseitige Zimmer. Die großen, glänzenden Handblätter (bis 40 cm breit) sind sehr dekorativ. Im Freien winterhart bis ca. -10°C. Als Zimmerpflanze leidet sie bei Heizungswärme über 20°C und trockener Luft.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 10, 11, 12 (weiße Doldenblüten an älteren Pflanzen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge im Frühjahr/Sommer (10–15 cm, mit 2–3 Blättern) in feuchtes Substrat, leicht beheizen (20–22°C). Bewurzelung in 4–8 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, berries | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins, fatsin | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Saft kann Kontaktdermatitis verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** ASPCA listet Fatsia japonica als giftig für Katzen und Hunde (Saponine). Symptome bei Verschlucken: Erbrechen, Durchfall, Speichelfluss. Schweregrad gering bei normalen Kontaktmengen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Verträgt Rückschnitt gut — überlange Triebe im Frühjahr kürzen. Fördert buschigeren Wuchs.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–200 (indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–200 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, frosttolerant) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, humusreiche Einheitserde mit 20% Perlite. pH 6.0–7.0. Gut drainiert aber feuchtigkeitshaltend. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Lichtkompensationspunkt (light compensation point) für Fatsia japonica belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Lichtkompensationspunkt für Fatsia japonica belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: kein belegter Wert zur effektiven Wurzeltiefe (effective root depth) für Fatsia japonica --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein quantitativer Maas-Hoffman-Schwellenwert (ECe) für Fatsia japonica belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope für Fatsia japonica belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Fatsia japonica ist eine schattentolerante immergrüne Understory-Art und verträgt sogar tiefen Schatten (RHS: Vollsonne bis Vollschatten, Optimum Halbschatten); die hier eingetragene Toleranzstufe `shade` ist konservativ gewählt. Der **Lichtsättigungspunkt (light saturation point)** liegt laut Araus et al. (1986) bei ca. **175 µmol/m²/s** (gehört NICHT in das Kompensationspunkt-Feld, daher nur als Freitext). Maritim/küstennah ist die Art salzsprühtolerant (salt spray), aber kein Halophyt — daher Klasse `moderately_tolerant` ohne belegte ECe-Bodenschwelle. Boden-pH quellentreu mit §1.6 und §2.3 (6.0–7.0) harmonisiert; RHS führt zusätzlich allgemeine Toleranz von acid/neutral/alkaline.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterwachstum (langsam) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- DATEN FEHLEN: kein artspezifischer Photosynthese-Temperaturoptimumwert für Fatsia japonica belegt; Wachstumsoptimum 15–22 °C ist kein gemessenes T_opt --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: kein artspezifischer FR/(R+FR)-Messwert für Fatsia japonica belegt --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

#### Phase: Winterwachstum (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 60–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 5–15 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- DATEN FEHLEN: kein artspezifischer Photosynthese-Temperaturoptimumwert für Fatsia japonica belegt --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: kein artspezifischer FR/(R+FR)-Messwert für Fatsia japonica belegt --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winter | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Für Fatsia japonica liegen keine artspezifischen Mikronährstoff-Zielkonzentrationen (Mangan/Mn, Zink/Zn, Kupfer/Cu, Molybdän/Mo) aus seriösen Quellen vor; Spurenelemente werden in der Praxis über einen vollständigen Grünpflanzen-Volldünger abgedeckt (siehe §3.1). Daher als DATEN FEHLEN markiert statt aus allgemeinen Nährlösungs-Richtwerten hochgerechnet.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Zimmerpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | – | organisch | 40 g/Topf | Frühjahr |
| Kompost | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 2 Wochen April bis September. Oktober bis März kein Dünger. Überdüngung schadet — eher weniger als zu viel.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; gleichmäßig feucht halten; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering.winter_action` |
| Winter-Maßnahme Monat | 11 (November, vor erstem Dauerfrost) | `overwintering.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering.spring_action_month` |
| Winterquartier Temperatur (°C) | 5–15 (kühl, hell-frostfrei) | `overwintering.winter_quarter_temp_c` |
| Winterquartier Licht | hell bis halbschattig; kein direktes Heizungslicht nötig | `overwintering.winter_quarter_light` |
| Winterquartier Gießen | sparsam, nur antrocknen lassen; Staunässe strikt vermeiden | `overwintering.winter_quarter_watering` |

**Hinweis:** Fatsia japonica ist halbfrosthart (half_hardy). In USDA-Zone 8 (Mitteleuropa: geschützte Weinbaulagen) ist sie ausgepflanzt bis ca. -10 °C winterhart und kann dort mit Vlies (fleece) + Mulch im Beet bleiben. Als Kübel- bzw. Zimmerpflanze wird sie jedoch **frostfrei eingeräumt** (`frost_free`) — daher `move_indoors`/`move_outdoors`. Ideales Winterquartier: kühl (5–15 °C), hell, sparsam gegossen. Bei kurzfristigen Frösten im Freien ab unter -3 °C Vlies auflegen; Kübel an geschützte Hauswand stellen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Blattläuse | Aphis spp. | Klebrige Blätter, deformierte Triebe | easy |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau, kleine weiße Fliegen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit, warme Bedingungen |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Blattläuse, Schmierläuse, Weiße Fliege |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|----------------|--------------|------------------|
| Encarsia formosa (Schlupfwespe) | Weiße Fliege (Trialeurodes vaporariorum) | 1–10 / m² je Freilassung, wiederholt | 2–4 Wochen (optimal 20–25 °C) |
| Aphidius colemani (Schlupfwespe) | Blattläuse (Aphis spp.) | 0,5–3 / m² je Freilassung | 2–3 Wochen |
| Aphidoletes aphidimyza (Gallmücke) | Blattläuse (Aphis spp.) | 1–3 / m² je Freilassung | 2–3 Wochen |
| Cryptolaemus montrouzieri (Marienkäfer) | Schmierläuse (Pseudococcus spp.) | 5–10 / Pflanze (leichter Befall) | 3–4 Wochen |
| Metaphycus helvolus (Schlupfwespe) | Weichschildlaus (Coccus hesperidum) | 5–10 / Pflanze bzw. 10 / m², 2–3× im Abstand von 2–3 Wochen | 3–4 Wochen |
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilben (Tetranychus urticae) | 2–50 / m² je Freilassung, wöchentlich wiederholt | 1–3 Wochen (>60 % rF, 13–27 °C) |

**Hinweis:** Nützling-Wirt-Zuordnung fachlich getrennt: `Coccus hesperidum` ist eine **Weichschildlaus (Coccidae)** → Metaphycus/Coccophagus (NICHT Aphytis, das nur Panzer-/Deckelschildläuse der Diaspididae parasitiert). Encarsia formosa wirkt am besten ab 20 °C; bei kühler Fatsia-Überwinterung (<17 °C) ist die Weißfliegenkontrolle eingeschränkt. Phytoseiulus persimilis benötigt >60 % relative Luftfeuchte — bei trockener Heizungsluft Luftfeuchte erhöhen oder Amblyseius-Arten erwägen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — Zimmer-/Gartenpflanze (in milden Regionen auch Gartenpflanze).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Elefantenohr | Alocasia x amazonica | Großblättrig | Tropischer Look |
| Schefflera | Schefflera arboricola | Araliaceae | Kompakter, anspruchsloser |
| Monstera | Monstera deliciosa | Großblättrig, Zimmerpflanze | Beliebtere Zimmerpflanze |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Fatsia japonica,"Zimmeraralie;Japanische Aralie;Japanese Aralia;Paperplant",Araliaceae,Fatsia,perennial,day_neutral,shrub,fibrous,"8a;8b;9a;9b;10a;10b;11a","Japan, Südkorea",yes,10-30,25,80-200,80-200,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Fatsia japonica](https://www.healthyhouseplants.com/indoor-houseplants/japanese-aralia-fatsia-japonica-complete-care-growing-guide/) — Pflegehinweise
2. [NC State Extension — Fatsia japonica](https://plants.ces.ncsu.edu/plants/fatsia-japonica/) — Botanische Daten, USDA-Zonen
3. [Gardening Know How — Japanese Aralia](https://www.gardeningknowhow.com/houseplants/aralia-plants/japanese-aralia-care.htm) — Kulturdaten
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig für Katzen und Hunde, Saponine)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — Fatsia japonica](https://www.rhs.org.uk/plants/7147/fatsia-japonica/details) — Boden-pH (acid/neutral/alkaline), Sonnen-/Schattentoleranz (Vollsonne bis Vollschatten), Winterhärte H5, Maße
6. [Clemson HGIC — Fatsia](https://hgic.clemson.edu/factsheet/fatsia/) — Schattentoleranz (deep shade), Boden, Schädlinge, nützlingsfördernde Blüten
7. [Koppert — Encarsia formosa](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/encarsia-formosa/) — Ausbringrate Weiße Fliege (1–10/m²), Temperaturabhängigkeit
8. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Spinnmilben (2–50/m²), Luftfeuchte/Temperatur
9. [UC IPM — Metaphycus Parasitoids of Scale](https://ipm.ucanr.edu/natural-enemies/scale-insect-metaphycus-parasitoids/) — Metaphycus helvolus gegen Weichschildläuse, Indoor-Rate (10/m²)
10. [UC IPM — Coccophagus Parasitoid](https://ipm.ucanr.edu/natural-enemies/scale-insects-coccophagus-parasitoid/) — Parasitoid-Wirt-Spezifität Weichschildläuse vs. Panzerschildläuse
11. [PMC — Hedera helix Biological Flora (Metcalfe 2005)](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/j.1365-2745.2005.01021.x) — C3-Photosynthese in der Araliaceae (Hedera, Schwestergattung von Fatsia)
12. [Gardeners' World — Fatsia japonica](https://www.gardenersworld.com/house-plants/how-to-grow-fatsias/) — Frosthärte (-10 bis -12 °C), Winterschutz/Überwinterung
13. [Plantura — Fatsia japonica](https://plantura.garden/uk/houseplants/fatsia-japonica/fatsia-japonica-overview) — Überwinterung im Wintergarten (10–18 °C), Pflege
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
