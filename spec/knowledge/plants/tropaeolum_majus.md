# Große Kapuzinerkresse — Tropaeolum majus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Bio-Gärtner Kapuzinerkresse, Naturadb Tropaeolum, Samen.de Kapuzinerkresse, Gartenratgeber Kapuzinerkresse

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tropaeolum majus | `species.scientific_name` |
| Volksnamen (DE/EN) | Große Kapuzinerkresse, Kapuzinerkresse; Garden Nasturtium, Indian Cress | `species.common_names` |
| Familie | Tropaeolaceae | `species.family` → `botanical_families.name` |
| Gattung | Tropaeolum | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig und wiederholt blühend; frostempfindlich und daher als einjährige Kultur gezogen (cultivation_cycle_type=annual)) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: nur Keim-/Kardinaltemperaturen (~7 °C unterer Keimschwellwert) belegt, keine validierte Wuchs-GDD-Basis --> | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | — (einjährig, tropische Anden-Herkunft ohne Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | — (tagneutral; photoperiod_type=day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 9a–11b (als einjährige in Zone 4–8) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Keine Frosttoleranz; stirbt bei erster Frostnacht; nach Eisheiligen (15. Mai) auspflanzen | `species.hardiness_detail` |
| Heimat | Peru, Kolumbien (Anden) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (Vorkultur ab April bei 18–20°C; Stecklinge sind empfindlich) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (nach Eisheiligen; Direktsaat bevorzugt) | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Blätter, Blüten, Samen alle essbar) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

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
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (Glucosinolate = Senföle in Küchenmengen unbedenklich; antibiotikaähnliche Wirkung) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (rankende Sorten brauchen mehr) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–40 (buschig) bis 300 (rankend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (rankende Sorten) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Magere bis normale Gartenerde; pH 6,1–7,8 (Optimum 6,5–7,5); KEIN frischer Mist/Kompost (fördert Blatt, hemmt Blüte) <!-- Quelle: Steckbrief-Erweiterung 2026-06: pH-Spanne quellentreu auf 6,1–7,8 harmonisiert (PFAF/NCSU/RHS), vormals unterbelegte 5,5 entfernt --> | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifisch gemessener LCP für Tropaeolum majus belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifisch gemessener LCP für Tropaeolum majus belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Schwellwerte (a) für T. majus publiziert; Klasse sensitive ≈ <2 dS/m --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope (b) für T. majus publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6,1–7,8 | `species.soil_ph_preference` |

> **Hinweise:** Schatten-/Sonnentoleranz = wächst in voller Sonne bis Halbschatten; in Halbschatten deutlich reduzierter Blütenansatz (Blüte verlangt volle Sonne). Salztoleranz: *T. majus* gilt in peer-reviewed Studien als salzempfindlich (salt-sensitive); ECe-Bezug = Substrat-Sättigungsextrakt, nicht Gießwasser-EC. Staunässe-Toleranz sensitive: gute Drainage ist zwingend, Nässe fördert Wurzelfäule, dennoch keine Trockenheit (dislikes drought).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 13 (unterhalb 55 °F/13 °C verlangsamt sich die Keimung deutlich) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 25 (kultivierbarer Bereich bis 27 °C; Optimum 18–21 °C) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1.3 (ca. 1/2 Zoll; Samen benötigen Dunkelheit) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (Spanne 7–14 Tage je nach Bodentemperatur) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (Spanne 3–5 Jahre bei kühler, trockener, dunkler Lagerung) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark (Samen benötigen Dunkelheit zur Keimung; Ball-Seed-Produktionsdaten führen Nasturtium ohne "Germination Lighting"-Vermerk aber mit Pflicht-Abdeckung) | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak; scarification (harte Samenschale; Einweichen 12–24 h in lauwarmem Wasser ODER Anritzen/Anschleifen beschleunigt die Keimung; beides optional, da Keimung auch ohne Vorbehandlung zuverlässig erfolgt) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 115 (grobkörniger Samen; Ball-Seed-Katalog nennt 8 Samen/g ≈ 125 g/1000 Korn, Herstellerangaben ~9,26 Samen/g ≈ 108 g/1000 Korn — Mittelwert) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: keine Reihen-/Flächen-Direktsaat üblich; Kapuzinerkresse wird einzeln im Pflanzabstand 25–30 cm gesetzt (siehe §1.6), keine Massen-/Reihendichte publiziert --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Kapuzinerkresse hat für eine Sommerblume ungewöhnlich große, harte Samen (ähnlich Erbsengröße). Ball Horticultural führt in der professionellen Seed-Crop-Information-Tabelle für "Nasturtium" eine Keimtemperatur von 65–70 °F (18–21 °C) mit Pflicht-Abdeckung ("Cover Seed: Yes") — konsistent mit der Dunkelkeim-Anforderung mehrerer Konsumentenquellen. Nach dem Auflaufen sollten die Keimlinge sofort Licht erhalten.

Quellen (§1.8): [Ball Horticultural Company — Seed Crop Information Guide (Nasturtium-Zeile: 220 Samen/oz, 8 Samen/g, Cover Seed: Yes, 65–70 °F)](https://www.panamseed.com/media/culture/pas/seedcropchart_ball.pdf); [Biology Insights — How to Germinate Nasturtium Seeds](https://biologyinsights.com/how-to-germinate-nasturtium-seeds/); [Plant Grower World — Nasturtium Seed Germination Time Secrets Revealed](https://plantgrowerworld.com/nasturtium-germination-time-secrets-revealed/); [Almanac — Planting and Growing Nasturtiums from Seed](https://www.almanac.com/plant/nasturtiums); [Territorial Seed — Night And Day Nasturtium Seed](https://territorialseed.com/products/nasturtium-night-and-day); [Seed to Fork — Nicking Nasturtium Seeds (Scarification)](https://seedtofork.com/nicking-nasturtium/); [Fontana Seeds — Everything you need to know about Nasturtium Seeds (Soak/Presoak)](https://www.fontanaseeds.com/pages/everything-you-need-to-know-about-nasturtium-seeds); [Gardenek — How to Collect and Store Nasturtium Seeds (Viability 3–5 Jahre)](https://gardenek.com/how-to-collect-and-store-nasturtium-seeds/); [Meadowlark Journal — How to Harvest Nasturtium Seeds](https://meadowlarkjournal.com/blog/harvest-nasturtium-seeds); [nimrod.bio — Seeds Per Gram Chart](https://www.nimrod.bio/wp-content/uploads/2020/09/seedsPerGram.pdf)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ | 21–35 | 3 | false | true | high |
| Blüte + Ernte (Dauerflorenz) | 90–150 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte + Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland/Vollsonne, R:FR≈1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Kapuzinerkresse auf mageren Böden halten! Auf nährstoffreichen Böden oder nach Düngung → viel Blattwerk, kaum Blüten. Das Magerkeits-Prinzip: Stress fördert Blüte (evolutionäre Reaktion auf Bedrohung). KEIN Stickstoffdünger. Ältere Böden auf denen keine Düngung stattfand sind ideal. Bei extrem armen Böden allenfalls sehr gereifter Kompost.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Mäßig feucht; Trockenheit fördert Blüte; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (kein Dünger) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (als Blattlaus-Indikator täglich beobachten) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Vorkultur (optional) | Direktsaat im Topf bei 18°C | niedrig |
| Mai (nach 15.) | Direktsaat/Auspflanzen | 2–3 Samen je Stelle; 2 cm tief | hoch |
| Jun–Okt | Ernte | Blüten, Knospen, Blätter täglich | mittel |
| Jun–Okt | IPM-Monitoring | Blattläuse als Bioindikator! Schaden erkennen, Nützlinge beobachten | hoch |
| Okt | Samen ernten | Grüne unreife Samen: in Essig einlegen (Kapern-Ersatz) | mittel |
| Nov | Abräumen | Frostfrei; kompostieren | niedrig |

---

## 5. Schädlinge & Krankheiten

**Bioindikator-Funktion:** Kapuzinerkresse zieht Blattläuse an. Das ist ihre wichtigste IPM-Funktion: Sie wirkt als Ablenkkultur (Trap Crop). Blattläuse bevorzugen Kapuzinerkresse und lassen benachbarte Kulturen in Ruhe. Regelmäßig beobachten — Blattlausbefall an Kapuzinerkresse zeigt an, dass Blattläuse im Garten aktiv sind.

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schwarze Bohnenlaus | Aphis fabae | Massive Kolonien; honigauer Belag | shoot, leaf | vegetative, flowering | easy |
| Kohlweißling | Pieris brassicae | Lochfraß durch Raupen | leaf | vegetative, flowering | easy |
| Mehlige Kohlblattlaus | Brevicoryne brassicae | Wachspuder-Blattläuse | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | fungal | Weiße Blattunterseite | Feuchtigkeit | 5–10 | vegetative |

### 5.3 IPM-Strategie: Trap Crop

**Empfehlung:** Kapuzinerkresse bewusst als Ablenkkultur in der Nähe von Bohnen, Tomaten und Kohl pflanzen. Bei Blattlausbefall an Kapuzinerkresse → Befallene Triebe abschneiden und entsorgen ODER Blattläuse stehen lassen und Marienkäfer anlocken (natürliche Regulation).

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Blattlaus-Schlupfwespe (parasitic wasp) | Aphidius colemani | Schwarze Bohnenlaus (Aphis fabae) u. a. Blattläuse | 0,25–4 Tiere/m² je Freilassung, mind. 3× im Wochenabstand | erste Mumien (mummies) nach 10–14 Tagen |
| Gallmücke (predatory gall midge) | Aphidoletes aphidimyza | Blattläuse (Aphis fabae, Brevicoryne brassicae) | 1–10 Tiere/m² je Freilassung, wöchentlich bis Kontrolle | Larvenfraß ab wenigen Tagen, Etablierung 1–2 Wochen |

> **Hinweise:** *Aphidius colemani* und *Aphidoletes aphidimyza* sind beide gegen Blattläuse wirksam und kombinierbar. *Aphidoletes* NICHT zusammen mit Florfliegen (*Chrysoperla carnea*) ausbringen — Florfliegenlarven fressen die Gallmückenlarven. Bei dichten Blattlauskolonien wirkt die Gallmücke schneller als die Schlupfwespe. Ratenangaben gelten für Gewächshaus-/geschützten Anbau (Koppert); im Freiland fördern Trap-Crop-Effekt und natürliche Marienkäfer-Zuwanderung die Regulation zusätzlich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Einjährige Begleitpflanzen |
| Empfohlene Vorfrucht | beliebig |
| Empfohlene Nachfrucht | beliebig |
| Anbaupause (Jahre) | keine |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Bohne | Phaseolus vulgaris | 0.9 | Blattlaus-Ablenkung; Bestäuber anlocken | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Blattlaus-Trap; Bodendecker | `compatible_with` |
| Brokkoli | Brassica oleracea var. italica | 0.8 | Kohlweißling-Ablenkung; Trap Crop | `compatible_with` |
| Kartoffel | Solanum tuberosum | 0.8 | Blattlaus-Ablenkung | `compatible_with` |
| Rose | Rosa spp. | 0.9 | Blattlaus-Ablenkung; optisch kombinierbar | `compatible_with` |
| Erbse | Pisum sativum | 0.8 | Bodendecker; Blattlaus-Ablenkung | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Bestäuber anlocken; Bodenbeschattung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Kapuzinerkresse |
|-----|-------------------|-------------|-----------------------------------|
| Zwerg-Kapuzinerkresse | Tropaeolum minus | Gleiche Gattung | Kompakter; Topfkultur besser geeignet |
| Kapernkresse | Tropaeolum peregrinum | Gleiche Gattung | Filigraner; feingliederig; kletternd |
| Borretsch | Borago officinalis | Begleitpflanze | Blaue Blüten; Bienenmagnet; essbar |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Tropaeolum majus,"Große Kapuzinerkresse;Kapuzinerkresse;Garden Nasturtium;Indian Cress",Tropaeolaceae,Tropaeolum,annual,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b",0.2,"Peru, Kolumbien",yes,8,20,300,100,28,limited,yes,false,true,light_feeder,tender,"5;6","6;7;8;9;10","6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Bio-Gärtner Kapuzinerkresse](https://www.bio-gaertner.de/Pflanzen/Kapuzinerkresse) — Anbau, Verwendung, Mischkultur
2. [Naturadb Tropaeolum majus](https://www.naturadb.de/pflanzen/tropaeolum-majus/) — Steckbrief, Eigenschaften
3. [Samen.de Kapuzinerkresse Bioindikator](https://samen.de/blog/kapuzinerkresse-natuerlicher-bioindikator-im-garten.html) — IPM-Funktion
4. [Gartenratgeber Kapuzinerkresse](https://www.gartenratgeber.net/pflanzen/kapuzinerkresse.html) — Pflege, Anbau
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — Tropaeolum majus garden nasturtium](https://www.rhs.org.uk/plants/85362/tropaeolum-majus/details) — Standort (volle Sonne/leichter Schatten), magere Böden, Blütephysiologie
6. [NC State Extension — Tropaeolum majus](https://plants.ces.ncsu.edu/plants/tropaeolum-majus/) — Lichtbedarf, Boden-pH (sauer–alkalisch), Drainage, Drought/Neglect-Toleranz
7. [PFAF — Tropaeolum majus](https://pfaf.org/user/Plant.aspx?LatinName=Tropaeolum+majus) — Boden-pH, Lichtbedarf, Feuchte (dislikes drought), gut drainierter Boden
8. [Gardenia.net — Tropaeolum majus (Nasturtium)](https://www.gardenia.net/plant/tropaeolum-majus-nasturtium) — Boden-pH-Optimum 6,5–7,5, volle Sonne/Halbschatten
9. [MDPI Plants 2025 — Growth, Gas Exchange and Phytochemical Quality of Nasturtium under Salinity](https://www.mdpi.com/2223-7747/14/3/301) — peer-reviewed: T. majus salzempfindlich (salt-sensitive)
10. [PMC — Salicylic Acid, Nicotinamide and Proline mitigate salt stress in Tropaeolum majus](https://pmc.ncbi.nlm.nih.gov/articles/PMC12030097/) — peer-reviewed: Salzempfindlichkeit, Salzstress-Schäden
11. [Greg.app — Garden Nasturtium Roots](https://greg.app/garden-nasturtium-roots/) — fibröses, flaches Wurzelsystem, Wurzeltiefe 15–30 cm
12. [Koppert — Aphidius colemani (parasitic wasp)](https://www.koppertus.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Ausbringrate 0,25–4/m², Mumien nach 10–14 Tagen
13. [Koppert — Aphidoletes aphidimyza (predatory gall midge)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/aphidoletes-aphidimyza/) — Ausbringrate 1–10/m², Inkompatibilität mit Chrysoperla
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
