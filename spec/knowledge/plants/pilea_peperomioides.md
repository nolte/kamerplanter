# Chinesische Geldpflanze — Pilea peperomioides

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [BBC Gardeners World](https://www.gardenersworld.com/house-plants/how-to-grow-pilea-peperomioides/), [Savvy Gardening](https://savvygardening.com/pilea-peperomioides-care/), [PLNTS.com](https://plnts.com/en/care/houseplants-family/pilea), [The Little Botanical](https://thelittlebotanical.com/how-to-care-for-the-chinese-money-plant/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pilea peperomioides | `species.scientific_name` |
| Volksnamen (DE/EN) | Chinesische Geldpflanze, Bauchnabelpflanze; Chinese Money Plant, Pancake Plant, UFO Plant | `species.common_names` |
| Familie | Urticaceae | `species.family` → `botanical_families.name` |
| Gattung | Pilea | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutrale Art (day_neutral); kein Kurztag-/Langtag-Schwellenwert anwendbar --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 13–30°C. Sehr anpassungsfähig an normale Zimmertemperaturen. | `species.hardiness_detail` |
| Heimat | Südchina (Yunnan-Provinz) — feuchte Bergwälder auf 1500–3000 m ü.M. | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Pilea peperomioides erlangte ihre Popularität durch Weitergabe von Stecklingen unter Pflanzenenthusiasten — ursprünglich verbreitete ein norddeutscher Missionar die Pflanze in Europa in den 1970ern. Die charakteristischen runden, tellerförmigen Blätter an langen Stielen sind unverwechselbar. Die Pflanze dreht sich zum Licht — regelmäßiges Drehen verhindert einseitiges Wachstum.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Photosynthese):** Klassifizierung als **C3** (`photosynthesis_type = c3`). Eine peer-reviewte Studie (Holtum et al., *Functional Plant Biology* 48(7):683–690, 2020) weist nach, dass die semi-sukkulenten Blätter CO₂ im Licht **nahezu ausschließlich über C3** assimilieren; lediglich eine schwach ausgeprägte, fakultative CAM-Aktivität (low-level CAM, nächtliche Apfelsäure-Akkumulation) tritt unter Trockenstress auf. Da der C3-Weg dominiert und CAM nicht der Hauptmodus ist, wird hier `c3` gesetzt (nicht `cam`). Praktische Folge: keine sukkulententypische CAM-Trockenheitstoleranz unterstellen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6 (kleine, unauffällige Blüten; Blüte als Zimmerpflanze selten, oft erst nach kühlerer Überwinterung) | `species.bloom_months` |
<!-- Quelle: growing-phase-auditor 2026-07 — Korrektur von [3,4,5] auf [5,6]: 3 unabhängige Quellen (selbst.de, palmenmann.de, gartenjournal.net) bestätigen Blütebeginn Mai, Verlängerung bis Juni durch 2 Quellen (selbst.de, palmenmann.de) gestützt; keine Quelle belegt März/April-Blüte. Konfidenz: GESICHERT (3/3 für Mai). -->


### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) entstehen spontan an der Basis oder am Stängel — bei 5–7 cm ablösen (mit scharfem Messer), kurz trocknen lassen, in Wasser oder feuchtem Substrat bewurzeln. Sehr einfach und zuverlässig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Pilea peperomioides ist nicht giftig — ideal für Haushalte mit Kindern und Haustieren.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt nötig. Ableger bei Bedarf entfernen, damit Mutterpflanze nicht zu dicht wird.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–50 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, gut durchlässige Einheitserde mit 20% Perlite. pH 6.0–7.0. Kokosfaser-basierte Mischungen funktionieren gut. Kleiner Topf bevorzugt — mag nicht zu viel Erdvolumen. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: kein quantitativer Maas-Hoffman-Schwellenwert (Substrat-ECe) für Pilea peperomioides in seriösen Quellen belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Als Unterwuchs-Art (understory) schattenverträglich, aber kein Tiefschatten — `partial_shade` (helles indirektes Licht, kein direkter Mittagssonnenstand). Der Lichtkompensationspunkt schattentoleranter krautiger Unterwuchspflanzen liegt typisch bei 10–50 µmol/m²/s; für Pilea ist die untere Spanne (10–30) plausibel. Angegeben ist ausschließlich der Kompensationspunkt (Netto-Photosynthese = 0), **nicht** der Sättigungspunkt. Flaches, mattenartiges Faserwurzelsystem ohne Tiefgang → kleine, flache Töpfe bevorzugt. Stark staunässe- und salzempfindlich: Überdüngung führt zu Salzkruste/Wurzelbrand; gelegentliches Durchspülen (Flushing) des Substrats empfohlen. Bezugsgröße einer etwaigen Salzschwelle wäre Substrat-ECe (Sättigungsextrakt), nicht die Gießwasser-EC. pH-Vorzug 6.0–7.0 stimmt mit §1.6 und §2.3 überein.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–250 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 4–10 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 13–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 | 0.4 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.25 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.08 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | — | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 4 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen März bis September. Kein Dünger Oktober bis Februar. Überdüngung → kahle Stiele (sog. "leggy"), kleine Blätter. Helles Licht ist wichtiger als Dünger für große, gesunde Blätter.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; abgestandenes Wasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Düngung starten | Erste Düngergabe nach dem Winter | mittel |
| Apr–Sep | Regelmäßig drehen | Topf jede Woche um 90° drehen für gleichmäßiges Wachstum | mittel |
| Apr–Sep | Ableger entnehmen | Kindpflanzen ab 5 cm Höhe ablösen | optional |
| Sep | Düngung beenden | — | niedrig |
| Okt–Feb | Reduzieres Gießen | Substrat zwischen Güssen mehr antrocknen lassen | mittel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (Sep–Okt, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 13–18 (Minimum 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (heller Fensterplatz, ggf. Pflanzenlicht) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam, Substrat zwischen Güssen antrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Pilea peperomioides ist nicht frosthart (`frost_free`): Sie wird als Kübel-/Zimmerpflanze frostfrei drinnen überwintert — kein Ausgraben/Einlagern von Knollen (kein `dig_and_store`), kein Mulch/Vlies im Freien. Mindesttemperatur 10°C (konsistent mit §1.1 Winterhärte-Detail). Ein optionaler Sommer-Aufenthalt im Halbschatten auf Balkon/Terrasse ist möglich; Ausräumen erst nach den Eisheiligen (Mitte Mai), Einräumen vor dem ersten Herbstfrost.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Trauermücke | Bradysia spp. | Larven in Substrat, Adulte fliegend | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, gelbe Punkte (bei trockener Luft) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Überbewässerung |
| Blattflecken | fungal/bacterial | Braun-gelbe Flecken | Nasses Laub, schlechte Zirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke |
| Nematoden | biological | Gießen | 0 | Trauermücke (Larven) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Nematoden (Trauermücken-Nematode) | Steinernema feltiae | Trauermücke (Larven), Bradysia spp. | ~250.000 Inf.-Juvenile/m² Substratoberfläche (≈ 500–1.000/Topf), ins Gießwasser | Larvenbefall innerhalb weniger Tage reduziert; Wiederholung alle 1–2 Wochen |
| Raubmilbe (Bodenraubmilbe) | Stratiolaelaps scimitus (syn. Hypoaspis miles) | Trauermücke (Larven/Puppen) | ~100–250/m² Substratoberfläche, auf das Substrat ausstreuen | dauerhafte Bodenpopulation; Wirkung über 2–4 Wochen aufbauend |
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | ~10–30/m² (1–3/sq ft) präventiv, 5–10/sq ft bei Befall | Entwicklungszyklus ~9 Tage bei 20°C; Befallsreduktion in 2–3 Wochen |
| Australischer Marienkäfer (Schmierlauszerstörer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | ~2–10/m² je Freilassung, 2–3 kleinere Gaben im Abstand 1–2 Wochen | benötigt Schmierlaus-Kolonien als Nahrung; Etablierung über mehrere Wochen/Generationen |

**Hinweis:** Nützlingseinsatz im Zimmer ist v. a. gegen Trauermücken (Nematoden/Raubmilben) praktikabel und etabliert. *Phytoseiulus persimilis* benötigt hohe Luftfeuchte (~70% im Bestand) zum Schlüpfen — bei trockener Zimmerluft ist die Wirkung gegen Spinnmilben begrenzt; ggf. mit Luftbefeuchtung kombinieren. *Cryptolaemus* überwintert in unseren Breiten nicht im Freien und ist eher für Gewächshaus/Wintergarten geeignet.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Pilea cadierei | Pilea cadierei | Gleiche Gattung | Silbermuster auf Blättern |
| Pilea mollis | Pilea mollis | Gleiche Gattung | Samtartige Textur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Pilea peperomioides,"Chinesische Geldpflanze;Bauchnabelpflanze;Chinese Money Plant;UFO Plant",Urticaceae,Pilea,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Südchina (Yunnan-Provinz)",yes,1-5,12,20-50,20-50,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [BBC Gardeners World — Chinese Money Plant](https://www.gardenersworld.com/house-plants/how-to-grow-pilea-peperomioides/) — Pflegehinweise
2. [Savvy Gardening](https://savvygardening.com/pilea-peperomioides-care/) — Kulturdaten
3. [PLNTS.com — Pilea Care](https://plnts.com/en/care/houseplants-family/pilea) — Ganzjahrespflege
4. [The Little Botanical](https://thelittlebotanical.com/how-to-care-for-the-chinese-money-plant/) — Praxiswissen
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Holtum et al. (2020): Low-level CAM photosynthesis in Pilea peperomioides, Functional Plant Biology 48(7):683–690](https://www.publish.csiro.au/fp/fulltext/FP20151) — Photosynthese-Typ: C3-dominant mit fakultativer Low-Level-CAM (peer-reviewed)
7. [PubMed 33287950 — Low-level CAM in Pilea peperomioides](https://pubmed.ncbi.nlm.nih.gov/33287950/) — Bestätigung Photosynthese-Klassifizierung
8. [Wikipedia — Pilea peperomioides](https://en.wikipedia.org/wiki/Pilea_peperomioides) — Heimat (Yunnan, Unterwuchs/understory), Standort
9. [pilea.com — Choosing the Best Soil / Pot Guide](https://www.pilea.com/post/choosing-the-best-soil-for-pilea-peperomioides) — pH 6.0–7.0, flaches Faserwurzelsystem, Staunässe-Empfindlichkeit
10. [House Plant Journal — Pilea fertilizer burn](https://www.houseplantjournal.com/houseplant-qa/pilea-might-have-fertilizer-burn/) — Salzempfindlichkeit, Salzkruste/Wurzelbrand bei Überdüngung
11. [ScienceDirect — Light compensation point overview](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/compensation-point) — LCP schattentoleranter Unterwuchspflanzen 10–50 µmol/m²/s
12. [Craine & Reich (2005): Leaf-level light compensation points in shade-tolerant woody seedlings, New Phytologist](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2005.01420.x) — niedrige LCP-Werte schattentoleranter Arten
13. [UNH/Dickson (2018): Managing nutrient solutions for hydroponic crops (PDF)](https://www.negreenhouse.org/uploads/9/4/8/2/94821076/dickson_2018_negc_nutrient_and_ph_for_hydroponics.pdf) — Mikronährstoff-ppm (Fe 1.75, Mn 0.38, Zn 0.25, Cu 0.08, Mo 0.05)
14. [GrowerTalks (2022): Nutritional Tips for Tropical Foliage Plants](https://www.growertalks.com/Article/?articleid=25993) — Mikronährstoff-Hierarchie tropischer Blattpflanzen (Fe>Mn>B>Zn>Cu>Mo)
15. [RHS — Biological control in the garden](https://www.rhs.org.uk/prevention-protection/biological-control-garden) — Nützling-Wirt-Zuordnungen (S. feltiae, Hypoaspis, Phytoseiulus)
16. [Jagdale et al. (2004): Steinernema feltiae against fungus gnats, Biological Control 29:296](https://www.sciencedirect.com/science/article/abs/pii/S1049964403001646) — Ausbringrate S. feltiae (~2,5×10⁵/m²)
17. [Cornell NYSIPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate (1–3/sq ft) & Entwicklungszeit
18. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Schmierlaus-Bekämpfung, Freilassungsrate
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
19. [selbst.de — Ufopflanze pflegen und vermehren](https://www.selbst.de/ufopflanze-pflegen-und-vermehren-74894.html) — Blütezeit Mai bis Juni
20. [palmenmann.de — Pilea: Informationen und Tipps](https://www.palmenmann.de/pflanzenwissen/blog/pilea-die-wichtigsten-informationen-und-tipps-rund-um-pflege-und-vermehrung) — Blütezeit Mai bis Juli, Blütenbildung durch kühle Überwinterung (≥12°C) begünstigt
21. [gartenjournal.net — Pilea peperomioides pflegen](https://www.gartenjournal.net/pilea) — Blüte im Frühjahr (Mai) nach kühler Überwinterung (5–10°C bzw. 10–15°C)
22. [RHS — Pilea peperomioides](https://www.rhs.org.uk/plants/13015/pilea-peperomioides/details) — Hardiness-Rating H1C ("tender evergreen perennial"), bestätigt `frost_sensitivity: tender`
<!-- /Quelle: growing-phase-auditor 2026-07 -->
