# Blut-Storchschnabel — Geranium sanguineum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Storchschnabel, Pflanzen-Kölle Storchschnabel, Baldur-Garten Storchschnabel, Native Plants Geranium sanguineum

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Geranium sanguineum | `species.scientific_name` |
| Volksnamen (DE/EN) | Blut-Storchschnabel, Blutroter Storchschnabel; Bloody Cranesbill | `species.common_names` |
| Familie | Geraniaceae | `species.family` → `botanical_families.name` |
| Gattung | Geranium | `species.genus` |
| Ordnung | Geraniales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 5 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; sehr robust; in Norddeutschland problemlos; halbimmergrün (Laub bleibt bei mildem Winter) | `species.hardiness_detail` |
| Heimat | Europa, Westasien; heimisch in Deutschland (Kalkfelsen, Trockenrasen) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebensdauer (Jahre) | 10–15 (langlebige Staude; Teilung alle 3–5 Jahre zur Verjüngung) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | true (Hemikryptophyt; oberirdisch einziehende Winterruhe) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (keine Kältebedürftigkeit für Blühinduktion; treibt jährlich aus Rhizom) | `lifecycle_configs.vernalization_required` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral; blüht über Tageslängenänderung Mai–Oktober) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5 | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Wildkraut; Blätter essbar) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 (lange Blütezeit mit Herbstfärbung) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (Blätter und Blüten essbar; Heilpflanze) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (nach Erstblüte; fördert Zweitblüte) | `species.pruning_months` |

**Hinweis:** Nach der Erstblüte (Juli) auf ca. 10 cm zurückschneiden — treibt kräftig neu aus und blüht bis in den Herbst weiter. Im Frühjahr (März) altes Laub entfernen. Selbstaussaat fördern oder durch Entfernen der Samenstände regulieren.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 (12–16 Stück/m²) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, mäßig nährstoffreiche Erde; pH 6,0–7,5; auch kalkhaltig; kein Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | — <!-- DATEN FEHLEN: kein art-spezifischer Messwert in seriösen Quellen --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | — <!-- DATEN FEHLEN: kein art-spezifischer Messwert in seriösen Quellen --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade (volle Sonne bis Halbschatten; in heißen Lagen Halbschatten bevorzugt) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 (flach-rhizomatöses, oberflächennahes Wurzelsystem; Teilungstiefe ca. 20–25 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive (Staunässe führt zu Wurzelasphyxie; gute Drainage zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | — <!-- DATEN FEHLEN: Quellen widersprüchlich (Dünenstandort vs. explizit "no salt tolerance") --> | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | — <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 (kalktolerant; harmonisiert mit §1.6 und §2.3) | `species.soil_ph_preference` |

**Hinweis:** Als Halbschatten-toleranter C3-Krautige passt sich *Geranium sanguineum* durch niedrigeren Lichtkompensationspunkt an Teilbeschattung an; präzise µmol-Werte liegen nicht art-spezifisch belegt vor. Natürliche Vorkommen auf Küstendünen deuten auf eine gewisse Sand- und Trockenstresstoleranz hin, eine belastbare Salztoleranz-Einstufung ist jedoch aus den verfügbaren Quellen nicht ableitbar.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | medium |
| Vegetatives Wachstum | 28–42 | 2 | false | false | high |
| Blüte (Frühjahr/Sommer) | 60–90 | 3 | false | false | high |
| Rückschnitt & Regeneration | 21–35 | 4 | false | false | high |
| Herbstblüte/-Färbung | 30–60 | 5 | false | false | high |
| Winterruhe | 120–150 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Hauptphase)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode (Stunden) | natürlich (tagneutral; keine künstliche Photoperiodensteuerung nötig) | `requirement_profiles.photoperiod_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (oberhalb des Zielkorridors; Punkt drohenden stomatären Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 (C3-Optimum kühl-gemäßigter Stauden) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (Freilandstandort Sonne bis Halbschatten; offenes Tageslicht/Vollsonne ≈ 0.5 nach Zhen & Bugbee, Halbschatten/Unterwuchs höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Frühjahrsaustrieb | 1:1:1 | 0.5–0.8 | 6.0–7.5 | 60 | 30 | – | 1 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5 | 0.05 | 0.03 | 0.05<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Blüte | 1:1:2 | 0.6–1.0 | 6.0–7.5 | 60 | 30 | – | 1 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5 | 0.05 | 0.03 | 0.05<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->– | – | – | –<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornmehl | Oscorna | organisch | 20–30 g/m² | März (einmalig) | light_feeder |
| Kompost (dünn) | eigen | organisch | 1–2 L/m² | März | Bodenverbesserung |

### 3.2 Besondere Hinweise zur Düngung

Geranium sanguineum ist ein ausgesprochener Schwachzehrer. Zu viel Dünger produziert übergroße Pflanzen mit wenig Blüten. Auf mageren Böden (Kalk, Sandstein) zeigt er seine beste Blütenfülle. Einmalige schwache organische Düngung im Frühjahr ausreichend — auf nährstoffreichen Gartenböden sogar gänzlich verzichtbar.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 (trockenheitsresistent nach Etablierung) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; sehr trockenheitstolerant; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 (einmalig im Jahr) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–4 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Aufräumen | Altes Laub entfernen; schwache Düngung | mittel |
| Mai–Jul | Blüte (erste) | Pinkfarbene bis blutrote Blüten | – |
| Jul | Rückschnitt | Auf 10 cm; fördert dichte neue Blattmasse und Herbstblüte | hoch |
| Aug–Okt | Herbstblüte + -färbung | Leuchtend rot-orange Herbstfärbung | – |
| Nov | Selbstaussaat regulieren | Samenstände entfernen falls keine Ausbreitung gewünscht | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

Geranium sanguineum ist sehr robust und hat kaum Schädlingsprobleme. Gelegentlich:

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | spring | easy |
| Raupen | div. Lepidoptera | Gelegentlicher Blattfraß | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

Kaum Krankheitsprobleme. Bei schlechten Standortbedingungen gelegentlich:

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + warm | 7–10 | vegetative (Spätsommer) |
| Grauschimmel | fungal (Botrytis) | Schimmel | Staunässe | 3–7 | autumn |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gute Drainage | cultural | – | Standortwahl | 0 | Grauschimmel |
| Rückschnitt (Luftzirkulation) | cultural | – | Juli | 0 | Mehltau |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|--------------------|----------------|------------------|------------------|
| Blattlaus-Schlupfwespe | Aphidius colemani | Blattläuse (Aphis spp.) | 0,25–4 Tiere/m² je Ausbringung (3× wiederholen) | 2–3 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphis spp.) | 1–10 Larven/m² je Ausbringung (wöchentlich bis Kontrolle) | 2–3 Wochen |

**Hinweis:** *Geranium sanguineum* ist sehr robust; Nützlinge nur bei tatsächlichem Befallsdruck (v. a. unter Glas/auf Balkon) ausbringen. Die Schlupfwespe *Aphidius colemani* parasitiert Blattläuse, die räuberische Gallmücke *Aphidoletes aphidimyza* frisst Blattlauskolonien — beide lassen sich kombinieren. Gegen gelegentlichen Raupenfraß (Lepidoptera) eignet sich *Bacillus thuringiensis* (biologisches Spritzmittel, kein Nützling im engeren Sinne).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rittersporn | Delphinium elatum | 0.9 | Fußraumbedeckung; ergänzende Höhe | `compatible_with` |
| Fetthenne | Sedum spp. | 0.8 | Gleiche trockene Standorte | `compatible_with` |
| Frauenmantel | Alchemilla mollis | 0.8 | Schattenbereich; ergänzend | `compatible_with` |
| Ziersalbei | Salvia nemorosa | 0.8 | Gleiche Trockenheitstolerantz; blauer Kontrast | `compatible_with` |
| Schafgarbe | Achillea millefolium | 0.8 | Gleiche Bedürfnisse; Nützlinge | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Geranium sanguineum |
|-----|-------------------|-------------|----------------------------------------|
| Wiesen-Storchschnabel | Geranium pratense | Gleiche Gattung | Höher (60 cm); blau-violett; mehr Schatten |
| Kleiner Storchschnabel | Geranium pusillum | Gleiche Gattung | Sehr kompakt; selbstaussäend | – |
| Himalaya-Storchschnabel | Geranium himalayense | Gleiche Gattung | Größere Blüten; robust | – |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Geranium sanguineum,"Blut-Storchschnabel;Blutroter Storchschnabel;Bloody Cranesbill",Geraniaceae,Geranium,perennial,day_neutral,herb,rhizomatous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Europa, Westasien",yes,8,20,40,60,35,no,yes,false,false,light_feeder,false,hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Plantura Storchschnabel](https://www.plantura.garden/blumen-stauden/storchschnabel/storchschnabel-pflanzen-pflegen) — Pflanzung, Pflege
2. [Pflanzen-Kölle Storchschnabel](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-storchschnabel-richtig/) — Pflege
3. [Baldur-Garten Storchschnabel](https://www.baldur-garten.de/onion/content/pflege-tipps/gartenstauden/storchschnabel) — Rückschnitt
4. [Native Plants Geranium sanguineum](https://www.native-plants.de/797/blut-storchschnabel) — Wildpflanzen-Steckbrief
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [NC State Extension — Geranium sanguineum](https://plants.ces.ncsu.edu/plants/geranium-sanguineum/) — Boden-pH (neutral 6.0–8.0), Licht (Sonne/Halbschatten), Drainage, USDA-Zonen
6. [Gardenia.net — Geranium sanguineum (Bloody Cranesbill)](https://www.gardenia.net/plant/geranium-sanguineum-bloody-cranesbill) — Standort, Kalk-/Sand-/Trockenheitstoleranz, Winterhärte
7. [Wikipedia — Geranium sanguineum](https://en.wikipedia.org/wiki/Geranium_sanguineum) — Hemikryptophyt/Dormanz, Dünen-/Kalkhabitat, Insektenbestäubung, Blütezeit Mai–Oktober, Wuchsmaße
8. [RHS — Geranium sanguineum](https://www.rhs.org.uk/plants/7926/geranium-sanguineum/details) — Standort, Winterhärte, Habitat (Küstendünen)
9. [Gardener's Path — Cranesbill Geranium Care](https://gardenerspath.com/plants/flowers/cranesbill-geranium/) — Lebensdauer langlebig, Teilung alle 3–5 Jahre, pH 6.0–6.5
10. [Wikipedia — Growing degree-day](https://en.wikipedia.org/wiki/Growing_degree-day) — GDD-Basistemperatur 5 °C für kühl-gemäßigte Pflanzen
11. [Iowa State Extension — Using Growing Degree Days](https://yardandgarden.extension.iastate.edu/how-to/using-growing-degree-days-manage-home-garden) — Basistemperatur-Konzept kühl-/warmsaisonale Arten
12. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Ausbringrate Blattlaus-Schlupfwespe
13. [Koppert — Aphidend (Aphidoletes aphidimyza)](https://www.koppert.com/aphidend/) — Ausbringrate räuberische Gallmücke
14. [Zhen & Bugbee 2020, Front. Plant Sci.](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.581156/full) — Far-Red-Anteil, Definition FR/(R+FR)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
