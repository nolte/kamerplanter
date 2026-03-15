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
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
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
| Substrat-Empfehlung (Topf) | Magere bis normale Gartenerde; pH 5,5–7,0; KEIN frischer Mist/Kompost (fördert Blatt, hemmt Blüte) | — |

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
