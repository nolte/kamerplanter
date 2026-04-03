# Mosaik-Pflanze, Aderblatt — Fittonia albivenis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/fittonia-albivenis-nerve-plant-grow-and-care-tips), [Smart Garden Guide](https://smartgardenguide.com/nerve-plant-care/), [Soltech](https://soltech.com/products/nerve-plant-care), [Terrarium Tribe](https://terrariumtribe.com/terrarium-plants/fittonia-albivenis-nerve-plant/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Fittonia albivenis | `species.scientific_name` |
| Volksnamen (DE/EN) | Mosaik-Pflanze, Aderblatt, Filigranpflanze; Nerve Plant, Mosaic Plant, Net Plant | `species.common_names` |
| Familie | Acanthaceae | `species.family` → `botanical_families.name` |
| Gattung | Fittonia | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | groundcover | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 3–10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–26°C. Extrem empfindlich gegen Kälte, Zugluft und trockene Luft. | `species.hardiness_detail` |
| Heimat | Peru, Kolumbien, Ecuador — Unterwuchs tropischer Regenwälder, bodennah | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Fittonia ist der Drama-Queen unter den Zimmerpflanzen — sie lässt bei Trockenstress dramatisch die Blätter hängen (komplett kollabieren), erholt sich aber bei sofortiger Wässerung fast vollständig. Dieser "Fainting"-Effekt ist ein zuverlässiger Feuchtigkeits-Anzeiger. Ideal für Terrarien (feuchtes Mikroklima, kein Zugluft-Problem). Im normalen Zimmerklima ist konstante hohe Luftfeuchtigkeit die größte Herausforderung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (kleine, unauffällige gelb-weiße Blüten; werden oft entfernt um Blattenergie zu erhalten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (3–5 cm, 2–3 Blattpaare) im Wasser oder direkt in feuchtem Substrat bei hoher Luftfeuchtigkeit. Mit Plastikbeutel oder Glasglocke abdecken. Bewurzelung in 2–4 Wochen. Sehr einfach — Fittonia bewurzelt fast von selbst.

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

**Hinweis:** Fittonia albivenis ist nicht giftig — sicher für Haushalte mit Haustieren und Kindern.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Regelmäßiges Pinzen der Triebspitzen fördert dichten, kompakten Wuchs und verhindert leggy-Wuchs. Blütenstände entfernen (verbraucht Energie). Im Frühjahr auf Basis zurückschneiden bei ausgezehrter Pflanze.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–15 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Feuchtigkeitshaltende, gut durchlässige Torfmischung: Einheitserde + 10% Perlite + 10% Torf/Kokoserde. pH 6.0–7.0. Alternativ: Terrarium-Substrat mit hohem organischen Anteil. Klein-Töpfe bevorzugt. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.2–0.6 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 17–23 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.3–0.6 | 6.0–7.0 | 60 | 20 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 2 ml/L (Viertel-Dosis, alle 4 Wochen) | Wachstum |
| Orchideen-Dünger | Substral | base | 7-5-6 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Nur mit 1/4 der normalen Düngerkonzentration düngen. Alle 4–6 Wochen März bis August. Überdüngung führt schnell zu Salzschäden (braune Ränder). Oktober bis Februar: kein Dünger.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser. Untersetzer-Methode ideal — Boden nie nass lassen, aber nie vollständig austrocknen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben (bei trockener Luft) | medium |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | easy |
| Blattlaus | Aphididae | Kolonien, Honigtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke trotz feuchter Erde | Staunässe, schlechte Drainage |
| Botrytis | fungal | Grauschimmel auf Blättern | Übermäßige Feuchtigkeit, Luftstagnation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Humidifier | cultural | Luftfeuchtigkeit erhöhen | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Blattläuse |
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke (Adulte) |
| Nematoden | biological | Gießen | 0 | Trauermücke (Larven) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Weiße Aderblatt | Fittonia albivenis 'White Anne' | Gleiche Art | Weiße Adern, spektakulär |
| Rote Aderblatt | Fittonia albivenis 'Red Threads' | Gleiche Art | Rote Adern, intensiv |
| Maranta | Maranta leuconeura | Ähnliche Ansprüche (Marantaceae) | Größer, robuster |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Fittonia albivenis,"Mosaik-Pflanze;Aderblatt;Nerve Plant;Mosaic Plant",Acanthaceae,Fittonia,perennial,day_neutral,groundcover,fibrous,"11a;11b;12a","Peru, Kolumbien, Ecuador",yes,0.5-2,8,10-15,20-40,yes,no,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
White Anne,Fittonia albivenis,"ornamental;white_veins;compact",clone
Red Threads,Fittonia albivenis,"ornamental;red_veins;compact",clone
Pink Angel,Fittonia albivenis,"ornamental;pink_veins",clone
Skeleton,Fittonia albivenis,"ornamental;white_veins;large_leaf",clone
```

---

## Quellenverzeichnis

1. [Gardenia.net — Fittonia albivenis](https://www.gardenia.net/plant/fittonia-albivenis-nerve-plant-grow-and-care-tips) — Botanische Daten, Kulturdaten
2. [Smart Garden Guide — Nerve Plant](https://smartgardenguide.com/nerve-plant-care/) — Detaillierte Pflegehinweise
3. [Soltech — Nerve Plant Care](https://soltech.com/products/nerve-plant-care) — Lichtanforderungen
4. [Terrarium Tribe — Fittonia albivenis](https://terrariumtribe.com/terrarium-plants/fittonia-albivenis-nerve-plant/) — Terrarium-Kultivierung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
