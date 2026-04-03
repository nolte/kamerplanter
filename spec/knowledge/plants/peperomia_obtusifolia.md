# Baby-Gummipflanze — Peperomia obtusifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Joy Us Garden](https://www.joyusgarden.com/peperomia-obtusifolia-care/), [Gardenia.net](https://www.gardenia.net/plant/peperomia-obtusifolia), [Lively Root](https://www.livelyroot.com/blogs/plant-care/baby-rubber-plant-care), [Houseplant Central](https://houseplantcentral.com/peperomia-obtusifolia-care/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Peperomia obtusifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Baby-Gummipflanze, Stumpfblättrige Peperomie; Baby Rubber Plant, American Rubber Plant | `species.common_names` |
| Familie | Piperaceae | `species.family` → `botanical_families.name` |
| Gattung | Peperomia | `species.genus` |
| Ordnung | Piperales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 12°C, optimal 18–28°C. Verträgt typische Zimmertemperaturen sehr gut. | `species.hardiness_detail` |
| Heimat | Karibik, Zentral- und Südamerika — epiphytisch an Bäumen in tropischen Wäldern | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Peperomia obtusifolia hat halbsukkulente, dickfleischige Blätter und Stängel, die Wasser speichern — ähnlich wie Sukkulenten. Deshalb verträgt sie Trockenheit viel besser als Staunässe. Sie gehört zur zweitgrößten Gattung der Bedecktsamer (über 1.500 Arten). Als epiphytische Pflanze ist das Substrat sekundär, solange Drainage gut ist. Nicht mit Ficus elastica (echter Gummibaum) verwechseln.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (kleine, unauffällige Spadix-Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, cutting_leaf, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (5–8 cm) im Wasser bewurzeln oder direkt in feuchtem Perlite/Substrat. Blattstecklinge funktionieren gut: Blatt mit Stiel abschneiden, in feuchtes Substrat stecken. Bewurzelung bei 22–24°C in 3–6 Wochen. Sehr zuverlässig.

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

**Hinweis:** Peperomia obtusifolia ist NICHT giftig — ideal für Haushalte mit Kindern und Haustieren. ASPCA listet die Pflanze als ungiftig.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kein regelmäßiger Rückschnitt nötig. Überlange Triebe im Frühjahr kürzen. Verblühte Blütenstände entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–4 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, luftige Mischung: Einheitserde mit 30% Perlite oder Orchideen-Mix. pH 6.0–7.0. Niemals schwere, dichte Erde. Kleiner Topf optimal — Peperomien mögen es eng. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 4–12 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 40–120 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 60 | 25 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (halbe Dosis, 3×/Saison) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |
| Guano-Dünger | Gardol | organisch | 2 g/L Gießwasser | Frühjahr bis Sommer |

### 3.2 Besondere Hinweise

Extrem leichter Zehrer. Nur 2–3 Düngergaben pro Saison (März–August) — immer mit halber Konzentration. Überdüngung führt zu Wurzelverbrennung und Blattverlust. Kein Dünger September bis Februar. Frisches Substrat beim Umtopfen versorgt die Pflanze für mehrere Monate ausreichend.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; zwischen Güssen gut abtrocknen lassen (halbsukkulente Blätter) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Trauermücke | Bradysia spp. | Larven in Substrat, Adulte fliegend | easy |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, fauler Stamm | Überbewässerung, Staunässe |
| Cercospora-Blattflecken | fungal | Braune Flecken mit gelbem Hof | Nasses Laub, schlechte Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke (Adulte) |
| Nematoden (Steinernema feltiae) | biological | Gießen | 0 | Trauermücke (Larven) |
| Neemöl | biological | Sprühen 0.5% | 0 | Spinnmilbe, Schmierläuse |
| Substrat trockener halten | cultural | Gießintervall erhöhen | 0 | Trauermücke (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Gerippte Peperomie | Peperomia caperata | Gleiche Gattung | Interessante Blattstruktur |
| Wassermelonen-Peperomie | Peperomia argyreia | Gleiche Gattung | Dekoratives Wassermelonenmuster |
| Hänge-Peperomie | Peperomia scandens | Gleiche Gattung | Hängend, für Ampeln |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Peperomia obtusifolia,"Baby-Gummipflanze;Stumpfblättrige Peperomie;Baby Rubber Plant",Piperaceae,Peperomia,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Karibik, Zentral- und Südamerika",yes,1-4,10,15-30,20-40,yes,limited,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Variegata,Peperomia obtusifolia,"ornamental;variegated;green_cream",clone
Gold Tip,Peperomia obtusifolia,"ornamental;variegated;yellow_green",clone
```

---

## Quellenverzeichnis

1. [Joy Us Garden — Peperomia obtusifolia](https://www.joyusgarden.com/peperomia-obtusifolia-care/) — Pflegehinweise, Düngung
2. [Gardenia.net — Peperomia obtusifolia](https://www.gardenia.net/plant/peperomia-obtusifolia) — Botanische Daten
3. [Lively Root — Baby Rubber Plant](https://www.livelyroot.com/blogs/plant-care/baby-rubber-plant-care) — Kulturdaten
4. [Houseplant Central](https://houseplantcentral.com/peperomia-obtusifolia-care/) — Ganzjahrespflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
