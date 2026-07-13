# Himbeere — Rubus idaeus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** NaturaDB Rubus idaeus, Baumschule Weber, Baumschule Newgarden, Plantura Himbeere

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rubus idaeus | `species.scientific_name` |
| Volksnamen (DE/EN) | Himbeere, Gemeine Himbeere; Raspberry | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Rubus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (ausdauernd, blüht wiederholt über mehrere Jahre) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: keine 2 unabhängig belegten Wuchs-/Phänologie-Basistemperaturen auffindbar; Literatur nennt nur Wuchs-Optimum ~18 °C und GDH-Chill-Unit-Modelle, keine sauber abgesicherte GDD-Basis --> | `species.base_temp` |
| Typische Lebensdauer (Jahre) | 10–15 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation/Kältebedarf erforderlich (chilling, nicht echte Vernalisation) | true | `lifecycle_configs.vernalization_required` |
| Mindest-Kältetage (chilling, min days) | 35–56 (≈ 5–8 Wochen Endodormanz-Bruch; sortenabhängig ~600–800 Chill-Units) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: Primocane-/Herbstsorten tagneutral (day_neutral); nur Floricane-Sommersorten fakultativer Kurztag (~15 h), sortenabhängig — kein einheitlicher Stundenwert für die Art belegbar --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −25 °C; in Norddeutschland problemlos; Sommerhimbeeren benötigen anderen Schnitt als Herbsthimbeeren | `species.hardiness_detail` |
| Heimat | Europa, Asien | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Befruchter erforderlich (requires pollinator) | false | `species.requires_pollinator` |
| Kreuzbefruchtungsgruppe (pollinator group) | — (selbstfruchtbar/self-fertile; keine pomologische Gruppe) | `species.pollinator_group` |
| Empfohlene Befruchter-Sorten (compatible pollinators) | — (selbstfruchtbar; alle gängigen Sorten sind self-fertile) | `species.compatible_pollinators` |

Hinweis (Freitext): Himbeere ist selbstfruchtbar (self-fertile) und benötigt keinen Befruchter (Pollenspender-Sorte). Blüten sind selbstbestäubend, jedoch verbessert Insektenbestäubung (Bienen/Hummeln) Fruchtgröße und -ansatz deutlich (90–95 % der Bestäubung durch Bienen). Die Insekten-Hinweise gehören NICHT in `compatible_pollinators` (dort nur Cultivar-Sorten).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Pflanzung von Wurzelausläufern) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (vegetative Vermehrung üblich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (Sommerhimbeere), 8, 9, 10 (Herbsthimbeere) | `species.harvest_months` |
| Blütemonate | 5, 6 (Sommerhimbeere), 7, 8 (Herbsthimbeere) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Stacheln) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Sommerhimbeere: nach Ernte fruktifizierende Ruten bodennah abschneiden; Herbsthimbeere: Ende Februar/März alle Ruten bodennah abschneiden) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (Sommerhimbeere nach Ernte), 2, 3 (Herbsthimbeere im Winter/Frühjahr) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (große Kübel, min. 40 L) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50 cm in Reihe, 150–200 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Drahtrahmen oder Pfosten 1,5 m hoch) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humose, leicht saure Erde pH 5,5–6,5; kein Kalk; Mulch auf Oberfläche | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt aus ≥2 seriösen Quellen belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt aus ≥2 seriösen Quellen belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: Himbeere nicht in FAO-29-/USDA-Maas-Hoffman-Tabellen gelistet; nur qualitative Einstufung "sensitive" belegt, kein numerischer Maas-Hoffman-a-Wert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-b-Wert für Himbeere publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

Hinweis (Freitext): Himbeere ist flachwurzelnd (rhizomatös, Hauptwurzelmasse im oberen Bodenbereich) und steht in der Sonne bis zum Halbschatten; volle Sonne gibt den höchsten Ertrag, leichter Schatten wird toleriert. Staunässe begünstigt Phytophthora-Wurzelfäule (P. rubi) — durchlässiger Boden ist Pflicht. Als salzempfindliche Beere (sensitive berry, Chlorid-Toleranz nur ~120 ppm) reagiert sie früh auf salzhaltiges Gieß-/Bodenmilieu. Der pH-Vorzug 5.5–6.5 ist mit §1.6 und §2.3 derselben Datei harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe / Dormanz | 90–120 | 1 | false | false | high |
| Neuaustrieb | 21–42 | 2 | false | false | medium |
| Vegetativ (Rutenbildung) | 60–90 | 3 | false | false | high |
| Blüte | 21–28 | 4 | false | false | medium |
| Fruchtreife | 28–56 | 5 | false | true | high |
| Nachblüte / Erholungsphase | 30–60 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ & Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (deutlich oberhalb des Zielkorridors; stomatärer Kollaps-Punkt) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 (Optimum ~18 °C; oberhalb ~25 °C sinkende Netto-Photosynthese) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland/Vollsonne, R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |
| Neuaustrieb | 3:1:2 | 1.0–1.5 | 5.5–6.5 | 100 | 50 | — | 3 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 5.5–6.5 | 120 | 60 | — | 3 |
| Fruchtreife | 1:2:3 | 1.0–1.5 | 5.5–6.5 | 100 | 50 | — | 2 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
Mikronährstoffe je Phase (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`):

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Neuaustrieb | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Vegetativ | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Fruchtreife | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

Hinweis (Freitext): Für Himbeere wurden keine phasenspezifischen Mikronährstoff-Zielkonzentrationen (Mn/Zn/Cu/Mo in ppm) aus mindestens zwei unabhängigen seriösen Quellen gefunden; Werte daher als DATEN FEHLEN markiert statt geschätzt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–5 L/m² | Frühjahr (Mulch-Schicht) |
| Hornspäne | Oscorna | organisch-N | 60–80 g/m² | Frühjahr |
| Heidelbeer-/Rhododendrondünger | diverse | organisch-sauer | nach Herstellerangabe | Frühjahr + Sommer |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Beerensträucher-Dünger | Compo | base | 10-4-20 | 60–80 g/m² | Frühjahr |
| Schwefelsaures Kali | diverse | supplement | 0-0-50+18S | 20–30 g/m² | Fruchtreife |

### 3.2 Besondere Hinweise zur Düngung

Himbeeren bevorzugen leicht saure Böden (pH 5,5–6,5) — daher schwefelsaure Dünger statt Kalk. Mulchschicht aus Rindenmulch oder Stroh stabilisiert Bodenfeuchtigkeit und Bodenstruktur. Stickstoffbetonung im Frühjahr fördert Rutenbildung. Kalium-Schwerpunkt zur Fruchtreife.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies Wasser bevorzugt (erhöht pH); Regenwasser ideal | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Dauerpflanze; Verjüngung alle 8–10 Jahre) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Schnitt (Herbsthimbeere) | Alle Ruten bodennah abschneiden | hoch |
| Mär | Frühjahrsdüngung | Hornspäne + Kompost einarbeiten | hoch |
| Apr | Mulchen | 5–8 cm Stroh oder Rindenmulch | mittel |
| Mai–Jun | Triebpflege | Überschüssige Wurzelausläufer entfernen | mittel |
| Jun–Aug | Schnitt (Sommerhimbeere nach Ernte) | Abgeerntete zweijährige Ruten bodennah entfernen | hoch |
| Jun–Aug | Ernte | Täglich reife Früchte ernten | hoch |
| Sep–Okt | Ernte (Herbsthimbeere) | Herbstsorten bis Frost ernten | hoch |
| Nov | Wintervorbereitung | Junge Ruten an Spalier befestigen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (im Beet); Ruten ggf. mit Vlies | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune (Herbsthimbeere: alle Ruten) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2, 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Himbeerkäfer | Byturus tomentosus | Larven in Früchten (Made in der Frucht) | fruit | flowering, ripening | difficult |
| Blattlaus | Amphorophora idaei | Kolonien, Kräuselung, Virusübertragung | leaf, stem | vegetative | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Gelbpunkte (bei Trockenheit) | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel auf Früchten | Feuchtigkeit, Verletzungen | 3–7 | ripening |
| Echter Mehltau | fungal (Sphaerotheca macularis) | Weißer Belag auf Blättern | Trockene Tage | 7–14 | vegetative |
| Rutenkrankheit (Didymella) | fungal | Violette Flecken an Ruten, Absterben | Verletzungen, Feuchtigkeit | 14–21 | all |
| Himbeer-Ringfleckenvirus | viral | Mosaikmuster, Verkümmerung | Blattlausübertragung | — | all |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer | Blattläuse | 5–10 | 7–14 |
| Phytoseiulus persimilis | Spinnmilbe | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Befallene Ruten entfernen | cultural | — | Befallene Ruten sofort abschneiden | 0 | Rutenkrankheit |
| Kaolin-Ton | cultural | Kaolin | Sprühen auf Früchte | 0 | Himbeerkäfer |
| Pyrethrum | biological | Pyrethrin | Sprühen | 1 | Blattläuse, Himbeerkäfer |
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 3 | Blattläuse, Spinnmilbe |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Rosengewächse (Rosaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte oder Gründüngung |
| Empfohlene Nachfrucht | — (Dauerpflanze, Standzeit 10–15 Jahre) |
| Anbaupause (Jahre) | 5–7 Jahre nach Roden (Bodenmüdigkeit!) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Schützt vor Pilzkrankheiten | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Insektenabwehr, Bestäuberanlocken | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Gleiche Pilzkrankheiten möglich | moderate | `incompatible_with` |
| Tomate | Solanum lycopersicum | Gleiche Viren und Pilze | moderate | `incompatible_with` |
| Brombeere | Rubus fruticosus | Gleiche Schädlinge; Hybridisierung möglich | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Himbeere |
|-----|-------------------|-------------|---------------------------|
| Brombeere | Rubus fruticosus | Gleiche Gattung | Stärker, höherer Ertrag |
| Taybeere | Rubus fruticosus × idaeus | Hybrid | Größere Früchte, weniger Schädlinge |
| Stachelbeere | Ribes uva-crispa | Beerensträucher | Frühere Reifezeit |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Rubus idaeus,"Himbeere;Gemeine Himbeere;Raspberry",Rosaceae,Rubus,perennial,day_neutral,shrub,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",-0.1,"Europa, Asien",limited,50,40,200,100,50,no,limited,false,true,medium_feeder,hardy,"6;7;8;9;10","5;6;7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type,berry_type
Meeker,Rubus idaeus,WSU,1967,"high_yield;firm_fruit",–,,open_pollinated,summer_bearing
Autumn Bliss,Rubus idaeus,HRI East Malling,1983,"autumn;primocane",–,,open_pollinated,autumn_bearing
Glen Ample,Rubus idaeus,SCRI,1996,"spine_free;large_fruit",–,,open_pollinated,summer_bearing
```

---

## Quellenverzeichnis

1. [NaturaDB Rubus idaeus](https://www.naturadb.de/pflanzen/rubus-idaeus/) — Stammdaten
2. [Baumschule Weber Rubus idaeus](https://www.weber-baumschule.de/de-de/artikel/394/rubus-idaeus) — Pflegehinweise
3. [Baumschule Newgarden Himbeere](https://www.baumschule-newgarden.de/obst-fruechte/himbeere-rubus-idaeus/) — Sortenwahl
4. [Plantura Himbeere](https://www.plantura.garden/) — Schnittanleitung
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [PFAF — Rubus idaeus](https://pfaf.org/user/Plant.aspx?LatinName=Rubus+idaeus) — Selbstfruchtbarkeit (self-fertile), Schattentoleranz (Halbschatten/Vollsonne), Boden-pH 6–6.5
6. [USDA ARS — Raspberries / Pollinating Insect Research](https://www.ars.usda.gov/pacific-west-area/logan-ut/pollinating-insect-biology-management-systematics-research/docs/raspberries/) — Selbstfruchtbarkeit, Bienenbestäubung (90–95 %)
7. [Seeds of Diversity — Raspberries & Blackberries (Rubus)](https://seeds.ca/pollinator/bestpractices/raspberries.html) — selbstbestäubend, Bestäuberbeitrag
8. [AHDB/ProjectBlue — A Review of Dormancy and Chilling Requirements in Raspberries (2015)](https://projectblue.blob.core.windows.net/media/Default/Horticulture/Publications/A%20Review%20of%20Dormancy%20and%20Chilling%20Requirements%20in%20Raspberries.pdf) — Chilling-Anforderung, Endodormanz (5–8 Wochen Kälte)
9. [ISHS — Endodormancy and required chill units for raspberry canes](https://ishs.org/ishs-article/1133_39/) — Chill-Units je Sorte
10. [Sønsteby & Heide — Photoperiod & Temperature, Annual-Fruiting Red Raspberry (Semantic Scholar)](https://www.semanticscholar.org/paper/Effects-of-Photoperiod-and-Temperature-on-Growth,-S%C3%B8nsteby-Heide/a1fc6f043f9c483c8fe0edfd1589d68f0f21f1fa) — Primocane day-neutral, Floricane fakultativer Kurztag, Wuchs-Optimum ~18 °C, Rückgang > 25 °C
11. [MDPI Foods 2025 — Increased Temperature Effects on Raspberry cv. Heritage](https://www.mdpi.com/2304-8158/14/7/1201) — Temperatur-Optimum und Photosynthese-Rückgang oberhalb 25 °C
12. [USU Extension — Managing Saline and Sodic Soils / DPIRD NSW Salinity tolerance](https://www.dpird.nsw.gov.au/__data/assets/pdf_file/0005/523643/Salinity-tolerance-in-irrigated-crops.pdf) — Himbeere als salzempfindliche Beere (sensitive), Chlorid-Toleranz ~120 ppm
13. [Oregon State Extension — Growing Raspberries / OSU Phytophthora Root Rot](https://ohioline.osu.edu/factsheet/plpath-fru-14) — Staunässe-Empfindlichkeit, Phytophthora rubi bei Vernässung, flaches Wurzelsystem
14. [GardenOracle — Growing Red Raspberries: Rubus idaeus](https://gardenoracle.com/images/rubus-idaeus.html) — Wurzeltiefe (12–18 inch ≈ 30–45 cm), Vollsonne/Halbschatten
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
