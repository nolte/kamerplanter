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
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
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
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (Trichter befüllen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Jugendphase | 1:1:1 | 0.2–0.4 | 5.5–6.5 | 30 | 15 | — | 0.5 |
| Blüteinduktion | 0:0:0 | 0.0 | — | — | — | — | — |
| Blüte | 0:0:0 | 0.0 | — | — | — | — | — |

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
Neoregelia carolinae,Errötendes Bromeliad;Blushing Bromeliad,Bromeliaceae,Neoregelia,perennial,day_neutral,herb,aerial,10a;10b;11a;11b,0.0,Brasilien Atlantischer Regenwald,yes,3,10,40,70,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [Gardenia.net – Neoregelia Care Guide](https://www.gardenia.net/genus/neoregelia-blushing-bromeliad-grow-care-guide) — Vollständige Pflege
2. [Bromeliads.info – Neoregelia carolinae](https://www.bromeliads.info/bromeliad-plant-growing-specifications-neoregelia-carolinae-tricolor/) — Wachstumsspezifikationen
3. [Joyus Garden – Neoregelia Care](https://www.joyusgarden.com/neoregelia-plant-care-tips/) — Pflegetipps
4. [NC State Extension – Neoregelia](https://plants.ces.ncsu.edu/plants/neoregelia/) — Wissenschaftliche Grundlage
5. [House Plants Expert – Blushing Bromeliad](https://houseplantsexpert.com/blushing-bromeliad.html) — Indoor Care Guide
