# Errötendes Bromeliad — Neoregelia carolinae

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Neoregelia](https://www.gardenia.net/genus/neoregelia-blushing-bromeliad-grow-care-guide), [Bromeliads.info – Neoregelia carolinae](https://www.bromeliads.info/bromeliad-plant-growing-specifications-neoregelia-carolinae-tricolor/), [Joyus Garden – Neoregelia](https://www.joyusgarden.com/neoregelia-plant-care-tips/), [NC State Extension – Neoregelia](https://plants.ces.ncsu.edu/plants/neoregelia/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Neoregelia carolinae | `species.scientific_name` |
| Volksnamen (DE/EN) | Errötendes Bromeliad; Blushing Bromeliad, Cartwheel Bromeliad | `species.common_names` |
| Familie | Bromeliaceae | `species.family` → `botanical_families.name` |
| Gattung | Neoregelia | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | epiphyte | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | monocarpic (blüht einmal, dann Absterben) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-GDD-Basiswert für Neoregelia auffindbar --> | `species.base_temp` |
| Lebensdauer (Jahre) (lifespan) | 3–7 (monokarp: stirbt nach einmaliger Blüte ab, Fortbestand über Kindel) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (entfällt) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) (critical day length) | — (tagneutral, entfällt) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Ausschließlich Zimmerpflanze; keine Temperaturen unter 10°C | `species.hardiness_detail` |
| Heimat | Brasilien (Atlantischer Regenwald) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit:** Typische Tank-Bromeliade (Phytotelmata). Vor der einmaligen Blüte färbt sich die Herzrosette leuchtend rot — dies gibt der Art den Namen "Errötende Bromeliade". Nach der Blüte stirbt die Mutterpflanze ab und bildet Kindel (Ableger).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | variabel, einmalig nach 3–5 Jahren (bei Rötung des Herzens) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | nach Blüte (variabel) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Orchideen- oder Bromeliensubstrat; luftig und durchlässig; pH 5.5–6.5; minimales Substrat (Epiphyt) | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein quantitativer Kompensationspunkt für Neoregelia in zwei seriösen Quellen belegt; Literatur nennt nur qualitativ "low light-compensation point" für Schatten-CAM-Bromelien --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) (effective root depth) | 5–10 (flaches Ankerwurzelsystem; Epiphyt, Wurzeln dienen nur der Verankerung) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (Substrat: scharf drainiert halten, sonst Wurzel-/Trichterfäule; Trichter selbst hält dauerhaft Wasser) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe, Maas-Hoffman a) | <!-- DATEN FEHLEN: keine belegte Maas-Hoffman-Schwelle für Neoregelia; Quellen belegen nur qualitativ Salzempfindlichkeit --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m, Maas-Hoffman b) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) (soil pH preference) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweise:** Neoregelia ist ein epiphytischer CAM-Schattenspezialist des atlantischen Regenwald-Unterwuchses: helles indirektes Licht bis Halbschatten optimal, überlebt auch nahezu Vollschatten, verträgt jedoch keine direkte Mittagssonne. Salzempfindlichkeit zeigt sich als Blattspitzen-Nekrose (tip burn) bei salzhaltigem oder enthärtetem Wasser; Regen-/Destillatwasser bevorzugt (Wasser-pH 4.0–7.0). Die Staunässe-Empfindlichkeit bezieht sich auf das Substrat (Wurzelfäule), nicht auf den wassergefüllten Blatttrichter (Phytotelma), der dauerhaft gefüllt bleiben soll.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Jugendphase (Rosettenaufbau) | 730–1825 (2–5 Jahre) | 1 | false | false | medium |
| Blüteinduktion (Rötung) | 30–60 | 2 | false | false | low |
| Blüte | 60–120 | 3 | false | false | high |
| Absterben + Kindel | 180–365 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Jugendphase (Vegetativ)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) (vpd threshold) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) (photosynthesis temp opt) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (Trichter befüllen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Jugendphase | 1:1:1 | 0.2–0.4 | 5.5–6.5 | 30 | 15 | — | 0.5 | <!-- DATEN FEHLEN: keine artspezifischen Mn-ppm für Neoregelia belegt --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüteinduktion | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
| Blüte | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Mikronährstoff-Werte (Mn/Zn/Cu/Mo) nur als artspezifische ppm einzutragen, sobald durch ≥2 seriöse Quellen belegt. Literatur belegt für Bromelien nur relative Verhältnisse zu Fe in Mehrnährstoffdüngern, keine absoluten Neoregelia-Sollwerte. -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Jugendphase → Blüteinduktion | time_based | 730–1825 Tage | Herzrosette beginnt sich rot zu färben |
| Blüteinduktion → Blüte | time_based | 30–60 Tage | Herz vollständig rot |
| Blüte → Absterben | time_based | 60–120 Tage | Kindel erscheinen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Bromelien-Dünger | Plantiflex | base | 2-2-2 | 1/4 Normaldosis | 1 | jugendphase |
| Orchideendünger | Substral | base | 5-5-5 | 1/4 Normaldosis | 1 | jugendphase |

### 3.2 Besondere Hinweise zur Düngung

Neoregelia ist wie alle Tank-Bromeliaden ein Epiphyt — Düngung ausschließlich stark verdünnt in den Wassertrichter (1/4 der Normaldosis eines Bromelien- oder Orchideendüngers). Substrat NICHT düngen. Trichter alle 4–6 Wochen komplett ausspülen (sauberes Wasser in/aus Trichter kippen) um Bakterienbildung zu verhindern. Mehr Licht = intensivere Rotfärbung des Herzens.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser in den Trichter; Regenwasser ideal | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterpflege | Trichter halbvoll, reduziertes Gießen | niedrig |
| Mär | Frühjahrspflege | Mehr Licht, Trichter auffrischen | mittel |
| Apr | Düngung beginnen | Stark verdünnt in Trichter | mittel |
| Mai–Sep | Wachstum | Trichter immer gefüllt halten, Licht sichern | hoch |
| Okt | Trichter kontrollieren | Auf Trichterfäule prüfen | mittel |
| Nov–Dez | Ruhephase | Trichter halbvoll, minimal gießen | niedrig |
| Laufend | Kindel beobachten | Nach Rötung des Herzens Kindel erwarten | mittel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | Sep–Okt (bevor Nachttemperaturen unter 12 °C fallen) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | Mai–Jun (nach Eisheiligen, stabil > 15 °C) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 12–18 (nie unter 10 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell; helles indirektes Licht, kein direktes Mittagslicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert; Trichter halbvoll, Substrat fast trocken halten | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Neoregelia carolinae ist in Mitteleuropa (USDA 6–8) nicht winterhart und wird als frostfreie Zimmer-/Kübelpflanze ganzjährig drinnen oder nur im Hochsommer geschützt draußen gehalten. Entscheidend ist eine Mindesttemperatur von 10 °C; Kälte unter 10 °C verursacht Blattschäden. Kein Kältebedarf zur Blühinduktion (keine Vernalisation/Dormanz).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schildläuse | Coccus spp. | Braune Schuppen | stem, leaf | alle | difficult |
| Blattläuse | Aphis spp. | Deformierte Triebe | stem | vegetative | easy |
| Thripse | Frankliniella occidentalis | Silbrige Streifen | leaf | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Trichterfäule | bacterial/fungal | Fauliger Geruch, braune Trichtermasse | stagnant_water | 7–14 | alle |
| Wurzelfäule | fungal | Welke Pflanze | overwatering | 7–21 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Amblyseius cucumeris | Thripse | 50–100 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Trichter ausspülen | cultural | Wasser | Alle 4–6 Wochen | 0 | Trichterfäule |
| Neemöl | biological | Azadirachtin | Auf Blätter (nicht Trichter) | 0 | Schildläuse, Thripse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze, Epiphyt |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Vriesea | Vriesea splendens | 0.9 | Gleiche Familie, gleiche Pflege | `compatible_with` |
| Guzmania | Guzmania lingulata | 0.9 | Gleiche Familie | `compatible_with` |
| Orchideen | Phalaenopsis spp. | 0.7 | Ähnliche Standortanforderungen | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Neoregelia carolinae |
|-----|-------------------|-------------|------------------------------|
| Guzmania | Guzmania lingulata | Bromeliade, leuchtende Farben | Häufiger im Handel |
| Vriesea | Vriesea splendens | Bromeliade, Schwerblüte | Eindrucksvolle Blütenähre |
| Aechmea | Aechmea fasciata | Bromeliade | Silbrig-grüne Blätter, robust |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Neoregelia carolinae,Errötendes Bromeliad;Blushing Bromeliad,Bromeliaceae,Neoregelia,perennial,day_neutral,epiphyte,aerial,10a;10b;11a;11b,0.0,Brasilien Atlantischer Regenwald,yes,3,10,40,70,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [Gardenia.net – Neoregelia Care Guide](https://www.gardenia.net/genus/neoregelia-blushing-bromeliad-grow-care-guide) — Vollständige Pflege
2. [Bromeliads.info – Neoregelia carolinae](https://www.bromeliads.info/bromeliad-plant-growing-specifications-neoregelia-carolinae-tricolor/) — Wachstumsspezifikationen
3. [Joyus Garden – Neoregelia Care](https://www.joyusgarden.com/neoregelia-plant-care-tips/) — Pflegetipps
4. [NC State Extension – Neoregelia](https://plants.ces.ncsu.edu/plants/neoregelia/) — Wissenschaftliche Grundlage
5. [House Plants Expert – Blushing Bromeliad](https://houseplantsexpert.com/blushing-bromeliad.html) — Indoor Care Guide
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [IntechOpen – CAM Photosynthesis in Bromeliads and Agaves](https://www.intechopen.com/chapters/45242) — Beleg CAM-Stoffwechsel bei Neoregelia (N. eltoniana, N. pineliana, N. spectabilis als Typ-III-Tankbromelien); qualitativ "low light-compensation point" für Schatten-CAM-Bromelien
7. [ScienceDirect – Does seasonal drought affect C3 and CAM tank-bromeliads from Campo Rupestre differently?](https://www.sciencedirect.com/science/article/abs/pii/S0367253021001250) — Beleg CAM bei Tank-Bromelien (u. a. Neoregelia)
8. [Missouri Botanical Garden – Neoregelia carolinae f. tricolor](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=291611) — Standort (part shade/bright indirect, überlebt nahezu Vollschatten), scharfe Drainage (Staunässe-Empfindlichkeit), USDA 10–11, Überwinterung im Container
9. [Gardenia.net – Neoregelia (Blushing Bromeliad)](https://www.gardenia.net/genus/neoregelia-blushing-bromeliad-grow-care-guide) — Licht/Halbschatten, Salzempfindlichkeit, Wasser-pH 4.0–7.0
10. [Bromeliad Paradise – Bromeliad Care Spotlight: Neoregelia](https://bromeliadparadise.com/blogs/care/bromeliad-care-spotlight-neoregelia) — Salzempfindlichkeit (kein enthärtetes/salzhaltiges Wasser), Blattspitzen-Nekrose
11. [Plant Care Today – Neoregelia Care](https://plantcaretoday.com/neoregelia-bromeliad.html) — flaches Ankerwurzelsystem, kleine Töpfe, Idealtemperaturen 21 °C Tag / 12–15 °C Nacht
12. [Plant Ecology (Springer) – Light microhabitats, growth and photosynthesis of an epiphytic bromeliad in a tropical dry forest](https://link.springer.com/article/10.1007/s11258-004-5802-3) — Lichtmikrohabitate des Unterwuchses (30–59 % des Umgebungs-PFD optimal) als Beleg für Halbschatten-Einstufung
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
