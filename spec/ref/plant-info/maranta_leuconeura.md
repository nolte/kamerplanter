# Pfeilwurz, Gebet-Pflanze — Maranta leuconeura

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [PLNTS.com](https://plnts.com/en/care/houseplants-family/maranta), [Gardenia.net](https://www.gardenia.net/plant/maranta-leuconeura-prayer-plant-grow-care-tips), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/prayer-plant-maranta-leuconeura-care-guide/), [Old Farmer's Almanac](https://www.almanac.com/plant/prayer-plant-care-how-grow-healthy-happy-maranta), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Maranta leuconeura | `species.scientific_name` |
| Volksnamen (DE/EN) | Pfeilwurz, Gebet-Pflanze; Prayer Plant | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Maranta | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Sehr empfindlich gegen Zugluft und Temperaturschwankungen. | `species.hardiness_detail` |
| Heimat | Tropisches Brasilien — Unterwuchs tropischer Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Gebet-Pflanze zeigt Nyktinastie — abends falten sich die Blätter senkrecht wie Gebetshände zusammen, morgens öffnen sie sich wieder. Dieses Verhalten ist ein guter Indikator für die Pflanzengesundheit: Wenn Blätter nachts geschlossen bleiben, ist etwas nicht in Ordnung. Gehört zur selben Familie wie Goeppertia (Calathea) und hat ähnliche Anforderungen — weicht aber im Detail ab (toleranter gegenüber weniger perfekten Bedingungen als echte Calatheas).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (kleine weiß-violette Blüten; in Zimmerkultur selten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen im Frühjahr ist am zuverlässigsten. Stängelstecklinge (5–8 cm, unterhalb eines Knotens) in Wasser bewurzeln (2–4 Wochen) oder direkt in feuchtes Perlite/Substrat stecken.

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

**Hinweis:** Maranta leuconeura ist nicht giftig — ASPCA listet die Pflanze als sicher für Katzen, Hunde und Kinder. Ideal für Haushalte mit Haustieren.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kein regelmäßiger Rückschnitt nötig. Abgestorbene oder beschädigte Blätter an der Basis entfernen. Überlange Triebe bei Bedarf kürzen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, feuchtigkeitshaltende aber gut durchlässige Erde: Einheitserde mit 20% Perlite + 10% Kokoserde. pH 5.5–6.5. Kein Kalk im Substrat. Mischung sollte Feuchtigkeit halten ohne zu verdichten. | — |

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
| Licht PPFD (µmol/m²/s) | 50–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 60–180 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.5–6.5 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 5.5–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideen-Dünger | Compo | base | 7-5-6 | 3 ml/L (halbe Dosis, alle 4 Wochen) | Wachstum |
| Zimmerpflanzen-Flüssigdünger | Substral | base | 7-3-7 | 3 ml/L (halbe Dosis) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen März bis September — immer mit halber Konzentration. Kein Dünger Oktober bis Februar. Fluorid im Wasser oder Dünger schadet der Pflanze (Blattspitzenverbrennung). Weiches Wasser oder destilliertes Wasser empfohlen. Fluoridhaltige Dünger meiden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser zwingend. Regen- oder destilliertes Wasser bevorzugt. Fluorid schadet (Blattspitzenverbrennung). | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben (häufig bei trockener Luft) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Thrips | Frankliniella spp. | Silbrig-glänzende Streifen, Blätter deformiert | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken mit gelbem Hof | Nasses Laub |
| Echter Mehltau | fungal | Weißer Belag | Geringe Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Erhöhte Luftfeuchtigkeit | cultural | Humidifier, Kiesschale mit Wasser | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Sprühen | 3 Tage | Thrips, Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Calathea/Goeppertia | Goeppertia orbifolia | Gleiche Familie | Noch spektakuläreres Blattmuster |
| Stromanthe | Stromanthe thalia | Gleiche Familie | Robuster, weniger anspruchsvoll |
| Ctenanthe | Ctenanthe burle-marxii | Gleiche Familie | Toleranter bei Trockenheit |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Maranta leuconeura,"Pfeilwurz;Gebet-Pflanze;Prayer Plant",Marantaceae,Maranta,perennial,day_neutral,herb,rhizomatous,"11a;11b;12a","Tropisches Brasilien",yes,1-5,12,15-30,30-60,yes,no,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Erythroneura,Maranta leuconeura,"ornamental;red_veins;herringbone_pattern",clone
Kerchoveana,Maranta leuconeura,"ornamental;rabbit_tracks;green_spots",clone
Massangeana,Maranta leuconeura,"ornamental;dark_green;silver_midrib",clone
```

---

## Quellenverzeichnis

1. [PLNTS.com — Maranta Care](https://plnts.com/en/care/houseplants-family/maranta) — Ganzjahrespflege
2. [Gardenia.net — Maranta leuconeura](https://www.gardenia.net/plant/maranta-leuconeura-prayer-plant-grow-care-tips) — Botanische Daten
3. [Healthy Houseplants — Prayer Plant](https://www.healthyhouseplants.com/indoor-houseplants/prayer-plant-maranta-leuconeura-care-guide/) — Schädlinge, Kulturdaten
4. [Old Farmer's Almanac — Prayer Plant](https://www.almanac.com/plant/prayer-plant-care-how-grow-healthy-happy-maranta) — Pflegehinweise
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
