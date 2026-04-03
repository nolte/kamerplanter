# Herzblatt-Philodendron — Philodendron hederaceum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/how-to-care-for-heartleaf-philodendron/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-philodendron), [ASPCA](https://www.aspca.org/), [Healthy Houseplants](https://www.healthyhouseplants.com/), [Soltech](https://soltech.com/products/heartleaf-philodendron-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Philodendron hederaceum | `species.scientific_name` |
| Volksnamen (DE/EN) | Herzblatt-Philodendron, Kletterphilodendron; Heartleaf Philodendron, Sweetheart Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Philodendron | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–26°C. Sehr empfindlich gegenüber Kälte und Zugluft. | `species.hardiness_detail` |
| Heimat | Tropisches Mittelamerika und Karibik (Mexiko, Jamaika, Brasilien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** *Philodendron hederaceum* ist die korrekte Bezeichnung für den weit verbreiteten "Kletterphilodendron" oder "Herzblattphilodendron". Früher oft als *P. scandens* oder *P. oxycardium* geführt — diese Namen sind synonymisch. Im Handel auch als "Brasil" (variegierte Sorte) oder "Lemon Lime" bekannt. Verwechslungsgefahr mit Epipremnum aureum (Efeutute) — beide sehen ähnlich aus, sind aber getrennte Gattungen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor nicht) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–3 Knoten und mindestens 2 Blättern. Bewurzelung in Wasser (2–4 Wochen) oder direkt in feuchtem Substrat. Sehr hohe Erfolgsrate. Jeder Steckling sollte mindestens einen Knoten unterhalb der Wasseroberfläche haben.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft kann Kontaktdermatitis auslösen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 (hängend/kletternd bis 200+) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (optional — Moosstab fördert größere Blätter) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, durchlässige Einheitserde mit 20–30% Perlite. pH 6.0–7.0. Guter Wasserabzug wichtig. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.2 | 6.0–7.0 | 100 | 40 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Schwachzehrer — alle 4 Wochen in der Wachstumsphase reicht. Überdüngung führt zu braunen Blattspitzen. Im Winter kein Dünger.

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
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, gelbe Punkte | leaf | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Achseln | leaf, stem | easy |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | root | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Wurzeln | Überbewässerung |
| Blattflecken | bacterial | Braune, nasse Flecken | Wasser auf Blättern |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Nematoden | biological | Gießen (Steinernema feltiae) | 0 Tage | Trauermücke |
| Systeminsektizid | chemical | Stäbchen | 14 Tage | Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Efeutute | Epipremnum aureum | Sehr ähnliche Hängepflanze | Noch robuster, verträgt mehr Vernachlässigung |
| Velvet Philodendron | Philodendron micans | Gleiche Gattung | Samtartige, dunkel-bronzefarbene Blätter |
| Philodendron Brasil | Philodendron hederaceum 'Brasil' | Sorte mit Variegation | Dekorativere Blätter mit gelbgrünen Streifen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Philodendron hederaceum,"Herzblatt-Philodendron;Kletterphilodendron;Heartleaf Philodendron",Araceae,Philodendron,perennial,day_neutral,vine,aerial,"10a;10b;11a;11b","Tropisches Mittelamerika",yes,2-10,15,20-200+,40-100,yes,limited,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Brasil,Philodendron hederaceum,"ornamental;variegated;yellow_green",clone
Lemon Lime,Philodendron hederaceum,"ornamental;chartreuse_leaves",clone
```

**Hinweis:** Micans (Philodendron micans) wird in neuerer Literatur teils als eigene Art geführt und ist in Sektion 7 als "Ähnliche Art" aufgelistet — daher kein Cultivar-Eintrag hier.

---

## Quellenverzeichnis

1. [Smart Garden Guide — Heartleaf Philodendron](https://smartgardenguide.com/how-to-care-for-heartleaf-philodendron/) — Pflegehinweise
2. [The Sill — Philodendron Care](https://www.thesill.com/blogs/plants-101/how-to-care-for-philodendron) — Praxiswissen
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Soltech — Heartleaf Philodendron](https://soltech.com/products/heartleaf-philodendron-care) — Lichtanforderungen
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/heartleaf-philodendron-plant-care-guide/) — Ganzjahrespflege
