# Monkey Mask Monstera — Monstera adansonii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/monstera-adansonii-swiss-cheese-plant), [Our Houseplants](https://www.ourhouseplants.com/plants/monstera-adansonii-monkey-mask), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/swiss-cheese-plant-monstera-adansonii-care-guide/), [Joy Us Garden](https://www.joyusgarden.com/monstera-adansonii-care-swiss-cheese-vine-growing-tips/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Monstera adansonii | `species.scientific_name` |
| Volksnamen (DE/EN) | Monkey Mask Monstera, Lochpflanze; Swiss Cheese Plant, Monkey Mask Plant, Five Holes Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Monstera | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10–40+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurztag-/Langtagblüher → kein numerischer Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 13°C, optimal 18–27°C. | `species.hardiness_detail` |
| Heimat | Mittel- und Südamerika — tropische Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Monstera adansonii ist die kleinblättrigere, kletternde Schwester von M. deliciosa. Die charakteristischen ovalen Löcher (Fenestrationen) entstehen durch natürliche Anpassung an Widerstandsreduzierung bei Wind. Sie klettert oder hängt — je nach Aufstellung. Gut geeignet für Hängeampeln oder als Kletterpflanze an einer Moosstange. Schneller wachsend als M. deliciosa.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nicht in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit einem Knoten (Node) in Wasser stellen — Bewurzelung in 4–6 Wochen. Dann in Substrat umtopfen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (Blätter, Stängel, Saft) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Saft kann Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (überlange Ranken kürzen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–400+ (klettend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Moosstock, Rankgitter) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20% Perlite. pH 5.5–7.0. Leicht feuchtigkeitshaltend. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 15 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: keine seriöse Quelle für Wurzeltiefe der Epiphyt-/Kletterart --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten für Monstera --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten für Monstera --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–7.0 | `species.soil_ph_preference` |

**Hinweis:** Monstera adansonii ist eine Unterwuchs-Aroidee (understory aroid) des tropischen Regenwaldes — angepasst an diffuses, gefiltertes Licht, nicht an Vollsonne. Der niedrige Lichtkompensationspunkt (5–15 µmol/m²/s) ist typisch für Schattenpflanzen mit geringer Atmungsrate. Unterhalb ~10 µmol/m²/s stagniert die Chlorophyllsynthese. Sättigung tritt deutlich oberhalb (≈ 200–400 µmol/m²/s) ein — diese Sättigungswerte gehören nicht in das LCP-Feld. Salzempfindlich (salt-sensitive): Düngersalze reichern sich an und führen zu Blattrandnekrosen (tip burn); daher Substrat regelmäßig spülen (flush).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.2 | 5.5–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 5.5–7.0 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
#### Mikronährstoffe je Phase

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Aktives Wachstum | <!-- DATEN FEHLEN: keine artspezifische Monstera-Quelle --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | — (keine Düngung) | — | — | — |

KA-Felder: `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm`, `nutrient_profiles.molybdenum_ppm`. Keine zwei unabhängigen, seriösen Quellen mit Monstera-spezifischen Mikronährstoff-Zielwerten (ppm) auffindbar — daher nicht eingetragen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 2–4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Hornspäne | – | organisch | 30 g/Topf | Frühjahr |

### 3.2 Besondere Hinweise

Alle 2–4 Wochen März bis September. Oktober bis Februar kein Dünger. Ausgewogene Formel. Nicht überdüngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; obere 2–3 cm Erde zwischen Güssen antrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (Minimum 13, nie < 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | Hell, diffus; ggf. Pflanzenlicht (12 h) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | Reduziert; obere 2–3 cm antrocknen lassen, alle 10–14 Tage | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Monstera adansonii ist nicht frosthart (frost_free) und überwintert frostfrei als Zimmer-/Kübelpflanze. In Mitteleuropa (USDA 6–8) ganzjährig drinnen oder im beheizten Wintergarten. Unter 10 °C drohen Kälteschäden (Blattnekrosen, Wachstumsstillstand). Ein Sommeraufenthalt im Halbschatten auf Balkon/Terrasse ist möglich, jedoch nach den Eisheiligen aus- und vor dem ersten Herbstfrost wieder einräumen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Blattflecken | fungal | Braune Flecken | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit |
|-----------------------|----------------|--------------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 2–50 (1–2× wöchentlich wiederholen) | 1–2 Wochen |
| Cryptolaemus montrouzieri (Marienkäfer/Australischer Marienkäfer) | Schmierlaus (Pseudococcus spp.) | 5–40 (3× im Abstand von 1–2 Wochen) | 3–4 Wochen |
| Metaphycus helvolus (Schlupfwespe) | Weichschildlaus (Coccus hesperidum) | 5–10 | 3–4 Wochen |

**Hinweis:** Nützlingseinsatz benötigt warme, humide Bedingungen (Cryptolaemus optimal 25–29 °C, 70–80 % rF) — daher im Innenraum/Wintergarten gut umsetzbar. Phytoseiulus persimilis ist auf echte Spinnmilben spezialisiert; bei trockener Heizungsluft Luftfeuchte > 50 % halten. Metaphycus helvolus parasitiert Weichschildläuse (Coccidae) wie Coccus hesperidum, nicht jedoch Panzer-/Deckelschildläuse (Diaspididae).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Fensterblatt | Monstera deliciosa | Gleiche Gattung | Größer, majestätischer |
| Pfeilblatt | Syngonium podophyllum | Araceae, Kletterpflanze | Kompakter, mehr Sorten |
| Epipremnum | Epipremnum aureum | Araceae, Kletterpflanze | Sehr robust, viele Sorten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Monstera adansonii,"Monkey Mask Monstera;Lochpflanze;Swiss Cheese Plant;Monkey Mask",Araceae,Monstera,perennial,day_neutral,vine,aerial,"10a;10b;11a;11b","Mittel- und Südamerika",yes,3-10,20,100-400,30-60,yes,limited,true,medium_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Monstera adansonii](https://www.gardenia.net/plant/monstera-adansonii-swiss-cheese-plant) — Botanische Daten
2. [Our Houseplants — Monstera adansonii](https://www.ourhouseplants.com/plants/monstera-adansonii-monkey-mask) — Kulturdaten
3. [Healthy Houseplants — Swiss Cheese Plant](https://www.healthyhouseplants.com/indoor-houseplants/swiss-cheese-plant-monstera-adansonii-care-guide/) — Pflegehinweise
4. [Joy Us Garden — Monstera adansonii](https://www.joyusgarden.com/monstera-adansonii-care-swiss-cheese-vine-growing-tips/) — Schädlinge, Propagation
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig — Calcium-Oxalate)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RareplantCare — Aroid Light & PPFD Guide](https://rareplantcare.com/aroid-light-ppfd-guide/) — Lichtkompensationspunkt, Schattenadaptation, PPFD-Bereiche für Aroideen
7. [Sterck et al. 2013, Journal of Ecology — Light compensation point in tropical forest understorey](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — niedrige LCP von Schattenpflanzen im Unterwuchs (peer-reviewed)
8. [Cafe Planta — Monstera adansonii Cold Tolerance](https://cafeplanta.com/blogs/resources/monstera-adansonii-cold-tolerance) — Mindesttemperatur, Kälteempfindlichkeit, Überwinterung
9. [MonsteraPlantResource — What pH Level Is Best for Monstera Plants](https://monsteraplantresource.com/what-ph-level-is-best-for-monstera-plants/) — Boden-pH-Vorzug 5.5–7.0
10. [CompleteGrow — Monstera Fertiliser & Care Guide](https://completegrow.com.au/garden-plant-care-home/monstera-fertiliser-care-guide/) — Salzempfindlichkeit, tip burn, Spülen bei Salzanreicherung
11. [Springer — Light Environments of Tropical Forests](https://link.springer.com/chapter/10.1007/978-94-009-7299-5_4) — R:FR-Verhältnis im Unterwuchs (Schatten R:FR ≈ 0.4 → FR-Fraction ≈ 0.6–0.7), peer-reviewed
12. [Yamori et al. 2013 — Temperature response of photosynthesis in C3, C4, and CAM plants](https://publish.uwo.ca/~dway4/files/Yamori%20et%20al.%202013.pdf) — T_opt der C3-Photosynthese, tropischer Bereich (peer-reviewed Review)
13. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Raubmilbe gegen Spinnmilben
14. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate/Etablierung Marienkäfer gegen Schmierläuse
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
