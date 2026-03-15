# Wachsbegonie, Eisbegonie — Begonia semperflorens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net — Wax Begonia](https://www.gardenia.net/genus/begonia-semperflorens-cultorum-wax-begonia), [Smart Garden Guide](https://smartgardenguide.com/wax-begonia-care/), [Garden Design](https://www.gardendesign.com/plants/wax-begonia.html), [UMN Extension](https://extension.umn.edu/flowers/begonia), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Begonia semperflorens | `species.scientific_name` |
| Synonyme | Begonia semperflorens-cultorum (Hybridgruppe im Handel) | — |
| Volksnamen (DE/EN) | Wachsbegonie, Eisbegonie, Immerblühende Begonie; Wax Begonia, Bedding Begonia, Ever-Flowering Begonia | `species.common_names` |
| Familie | Begoniaceae | `species.family` → `botanical_families.name` |
| Gattung | Begonia | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 1 (als Annuelle) oder 3–5 (als Zimmerpflanze überwintert) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Als Einjährige kultiviert oder bei mindestens 10°C überwintern. | `species.hardiness_detail` |
| Heimat | Brasilien — tropische Regenwaldränder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Wachsbegonie gehört zu den vielseitigsten Balkonpflanzen Deutschlands — sie verträgt Sonne bis Halbschatten und blüht pausenlos von Mai bis Frost. Der Name "Wachsbegonie" bezieht sich auf den wachsartig glänzenden Blätter. Bronzeblättrige Sorten vertragen mehr Sonne als grünblättrige. Als Zimmerpflanze kann sie auch im Winter weiterblühen. Botanisch handelt es sich meist um Kultivare und Hybriden aus verschiedenen brasilianischen Wildarten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 12–16 (Aussaat Januar/Februar, Samen sehr klein — Stecklinge bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (bis Frost) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge 5–7 cm in Wasser bewurzeln (4–6 Wochen) oder direkt in feuchtes Substrat. Samen extrem fein (staubkornfein) — Aussaat auf Oberfläche ohne Abdecken.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (besonders unterirdische Teile/Wurzeln) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides (besonders Wurzeln/Rhizome) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (leichter Rückschnitt für kompakteren Wuchs) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–45 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Hauptanwendung!) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, gut drainierte Blumenerde. pH 5.5–6.5. Fertige Begonienerde oder Einheitserde + 20% Perlite. Leicht feucht halten. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung/Jungpflanze | 20–40 | 1 | false | false | low |
| Wachstum/Hauptblüte (Frühling–Herbst) | 150–180 | 2 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum/Hauptblüte (Mai–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.2–0.4 | 5.5–6.5 | — | — |
| Wachstum/Blüte | 1:2:2 | 0.8–1.5 | 5.5–6.5 | 70 | 30 |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Flüssigdünger | Compo | base | 5-8-10 | 5 ml/L (alle 14 Tage) | Blüte |
| Balkonpflanzen-Dünger | Substral | base | 5-8-11 | 5 ml/L | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Blaukorn | – | mineralisch Langzeit | 3–5 g/L Substrat | einmalig beim Einpflanzen |

### 3.2 Besondere Hinweise

Mittelzehrer. Alle 14 Tage ab Mai bis September. Phosphat-betonter Dünger fördert Blütenbildung. NIE auf trockenes Substrat düngen — zuerst leicht angießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; NIE auf Blätter gießen (Pilzanfälligkeit); zwischen Güssen leicht antrocknen lassen; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Pseudococcus spp. | Wollflecken | easy |
| Weiße Fliege | Trialeurodes vaporariorum | Fliegen aufsteigen beim Berühren | easy |
| Blattläuse | Aphis spp. | Klebrige Triebe | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter matt | medium |
| Thrips | Frankliniella occidentalis | Silbrige Streifen | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Trockene Luft, Nachtfeuchte |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel | Feuchte, dichte Bepflanzung |
| Pythium Wurzelfäule | fungal | Welke, braune Wurzeln | Überwässerung |
| Bakterienblattkrankheit | bacterial | Wassergetränkte Flecken | Spritzwasser, Verletzungen |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| NIE auf Blätter gießen | cultural | Gießtechnik anpassen | 0 | Mehltau, Grauschimmel (Prävention) |
| Befallene Teile entfernen | cultural | Sofort abschneiden | 0 | Alle Pilzerkrankungen |
| Neemöl | biological | Sprühen 0.3% | 0 | Spinnmilben, Blattläuse |
| Insektizidseife | biological | Sprühen 1% | 0 | Schmierläuse, Thrips |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Balkon-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Königsbegonie | Begonia rex-cultorum | Gleiche Gattung | Ausgezeichnetes Blattwerk |
| Knollenbegonie | Begonia tuberhybrida | Gleiche Gattung | Größere Blüten |
| Fleißiges Lieschen | Impatiens walleriana | Ähnliche Nutzung | Mehr Schattentoleranz, tierfreundlich |
| Pelargonium | Pelargonium zonale | Ähnliche Nutzung | Sonnenliebend, sehr robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Begonia semperflorens,"Wachsbegonie;Eisbegonie;Immerblühende Begonie;Wax Begonia;Bedding Begonia",Begoniaceae,Begonia,annual,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b","Brasilien",yes,2-8,15,20-50,20-45,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Wax Begonia](https://www.gardenia.net/genus/begonia-semperflorens-cultorum-wax-begonia) — Botanische Daten, Kulturbedingungen
2. [Smart Garden Guide — Wax Begonia](https://smartgardenguide.com/wax-begonia-care/) — Pflegehinweise
3. [Garden Design — Wax Begonias](https://www.gardendesign.com/plants/wax-begonia.html) — Standort, Sorten
4. [UMN Extension — Begonia](https://extension.umn.edu/flowers/begonia) — Schädlinge, Krankheiten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (leicht giftig — Calcium-Oxalate)
