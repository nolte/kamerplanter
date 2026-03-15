# Flammendes Schwert — Vriesea splendens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Guide to Houseplants – Vriesea splendens](https://www.guide-to-houseplants.com/vriesea-splendens.html), [Joyus Garden – Vriesea Care](https://www.joyusgarden.com/vriesea-plant-care-tips/), [Bromeliads.info – Vriesea](https://www.bromeliads.info/bromeliad-vriesea/), [Gartenheinz – Flammendes Schwert](https://www.gartenheinz.de/pflanzen/zimmerpflanzen-pflege/bromelien-pflege/flammendes-schwert/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Vriesea splendens | `species.scientific_name` |
| Volksnamen (DE/EN) | Flammendes Schwert, Vriesea; Flaming Sword Bromeliad | `species.common_names` |
| Familie | Bromeliaceae | `species.family` → `botanical_families.name` |
| Gattung | Vriesea | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Ausschließlich Zimmerpflanze; keine Temperaturen unter 10°C | `species.hardiness_detail` |
| Heimat | Trinidad, Venezuela, Guayana (tropisches Südamerika) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit:** Bromeliaceae-Typus mit Zentraltrichter (Phytotelmata — natürlicher Wasserspeicher in der Blattrosette). Nach der einmaligen Blüte stirbt die Mutterpflanze ab und bildet Kindel (offsets) für die Vermehrung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | variabel, einmalig nach ca. 3–5 Jahren | `species.bloom_months` |

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
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Luftiges Bromelien- oder Orchideensubstrat; locker und durchlässig; Epiphyt — braucht kaum Substrat | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Jugendphase (Rosetten-Aufbau) | 730–1460 (2–4 Jahre) | 1 | false | false | medium |
| Blütenaustrieb | 30–60 | 2 | false | false | low |
| Blüte | 60–180 | 3 | false | false | medium |
| Absterben Mutterpflanze + Kindel | 180–365 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Jugendphase (Vegetativ)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (in Trichter) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (in Trichter) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Jugendphase | 1:1:1 | 0.2–0.5 | 5.5–6.5 | 40 | 20 | — | 1 |
| Blütenaustrieb | 0:1:1 | 0.2–0.4 | 5.5–6.5 | 30 | 20 | — | 1 |
| Blüte | 0:0:0 | 0.0 | — | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Jugendphase → Blütenaustrieb | time_based | 730–1460 Tage | Pflanze ausreichend groß; Blütenstiel erscheint |
| Blütenaustrieb → Blüte | time_based | 30–60 Tage | Blütenähre voll entwickelt |
| Blüte → Absterben | time_based | 60–180 Tage | Kindel erscheinen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Bromelien-Dünger | Bayer | base | 2-2-2 + Spurenelemente | 1/4 der Normaldosis | 1 | jugendphase |
| Orchideendünger | Substral | base | 5-5-5 | halbe Dosierung | 1 | jugendphase |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Guano-Dünger (stark verdünnt) | — | organisch | 0.5 ml/L | Apr–Sep | light_feeder |

### 3.2 Besondere Hinweise zur Düngung

**Kritischer Hinweis:** Bromeliaden werden NIE über das Substrat gedüngt — ausschließlich stark verdünnter Dünger (1/4 der Normaldosis) wird in den zentralen Wassertrichter gegeben. Das Substrat versorgt die Pflanze kaum mit Nährstoffen — Bromeliaden sind Epiphyten und nehmen Nährstoffe über ihre Blätter und den Trichter auf. Den Trichter alle 4–6 Wochen komplett ausspülen (Bakterienvermeidung), dann mit frischem kalkarmem Wasser und minimalem Dünger befüllen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser in den Trichter; kein Wasser direkt ins Substrat | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Wenig Wasser | Trichter halbvoll halten, reduziertes Sprühen | niedrig |
| Mär | Wachstum anregen | Temperatur erhöhen, Wasser auffrischen | mittel |
| Apr | Düngung beginnen | Sehr verdünnter Bromelien-Dünger in Trichter | mittel |
| Mai–Sep | Wachstum | Trichter immer mit Wasser gefüllt halten | hoch |
| Aug | Blüteinduktion | Ethylen-Behandlung möglich (Apfel neben Pflanze) | niedrig |
| Okt | Kindel beobachten | Nach Blüte erscheinen Kindel — abtrennen wenn 10 cm | mittel |
| Nov–Dez | Ruhe | Kühlerer Standort, weniger Wasser | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Feine Gespinste auf Blattunterseite | leaf | alle | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen | stem, leaf | alle | difficult |
| Wollläuse | Pseudococcus spp. | Wollbelag im Trichter | center | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Trichterfäule | bacterial/fungal | Faule, stinkende Trichtermasse | stagnant_water, overwatering | 7–14 | alle |
| Wurzelfäule | fungal | Welke Pflanze, schwarze Wurzeln | overwatering | 7–21 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Trichter ausspülen | cultural | Wasser | Alle 4–6 Wochen | 0 | Trichterfäule |
| Neemöl | biological | Azadirachtin | Auf Blätter (nicht in Trichter!) | 0 | Spinnmilben |
| Alkohol | mechanical | Isopropanol 70% | Wattestäbchen auf Schädlinge | 0 | Schildläuse, Wollläuse |

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
| Guzmania | Guzmania lingulata | 0.9 | Gleiche Bromelien-Familie, gleiche Pflege | `compatible_with` |
| Tillandsia | Tillandsia spp. | 0.8 | Epiphyten, gleiche Familie | `compatible_with` |
| Orchideen | Phalaenopsis spp. | 0.7 | Ähnliche Standortanforderungen | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Vriesea splendens |
|-----|-------------------|-------------|------------------------------|
| Guzmania | Guzmania lingulata | Bromeliade, Rosette | Leuchtende Farben, häufiger im Handel |
| Aechmea | Aechmea fasciata | Bromeliade | Silbergraue Blätter, längere Blütezeit |
| Tillandsia | Tillandsia cyanea | Bromeliade | Kompakter, ohne Substrat kultivierbar |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Vriesea splendens,Flammendes Schwert;Vriesea;Flaming Sword,Bromeliaceae,Vriesea,perennial,day_neutral,herb,aerial,10a;10b;11a;11b;12a;12b,0.0,Trinidad Venezuela,yes,3,12,60,60,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [Guide to Houseplants – Vriesea splendens](https://www.guide-to-houseplants.com/vriesea-splendens.html) — Indoor Care Guide
2. [Joyus Garden – Vriesea Care Tips](https://www.joyusgarden.com/vriesea-plant-care-tips/) — Pflegetipps
3. [Bromeliads.info – Vriesea](https://www.bromeliads.info/bromeliad-vriesea/) — Bromeliad-Expertise
4. [Gartenheinz – Flammendes Schwert](https://www.gartenheinz.de/pflanzen/zimmerpflanzen-pflege/bromelien-pflege/flammendes-schwert/) — DE Pflegeanleitung
5. [Pflanzenfreunde – Vriesea](https://www.pflanzenfreunde.com/lexika/bromelien/vriesea.htm) — Kulturtipps
