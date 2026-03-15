# Lila Sauerklee, Glücksklee — Oxalis triangularis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Bloomscape](https://bloomscape.com/plant-care-guide/oxalis/), [Ohio Tropics](https://www.ohiotropics.com/2019/08/11/oxalis-triangularis-purple-shamrock/), [House Plant House](https://houseplanthouse.com/2018/10/09/oxalis-triangularis-dormancy/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Oxalis triangularis | `species.scientific_name` |
| Volksnamen (DE/EN) | Lila Sauerklee, Glücksklee, Dreiecksklee; Purple Shamrock, False Shamrock, Wood Sorrel | `species.common_names` |
| Familie | Oxalidaceae | `species.family` → `botanical_families.name` |
| Gattung | Oxalis | `species.genus` |
| Ordnung | Oxalidales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (sporadische Dormanz alle 2–7 Jahre) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — Zwiebeln im Boden überwintern in Zone 6+. Mindesttemperatur -15°C für kurze Fröste. Als Zimmerpflanze optimal bei 15–21°C. | `species.hardiness_detail` |
| Heimat | Brasilien, Argentinien — tropische und subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Oxalis triangularis ist bekannt für ihre photoperiodische Blattbewegung (Nyktinastie) — die lila Dreiblätter öffnen und schließen sich je nach Lichtverhältnissen. Die sporadische Dormanz kann den Besitzer erschrecken: die Pflanze zieht scheinbar vollständig ein und "stirbt" — tatsächlich erholen sich die Zwiebeln nach 2–4 Wochen Trockenheit vollständig. Oxalsäure (daher Oxalidaceae) macht die Pflanze für Haustiere leicht giftig.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6, 9, 10 (weiß-rosa Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Zwiebelknöllchen beim Umtopfen teilen und getrennt einpflanzen. Sehr einfach und erfolgreich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (mild bitter, kaum Menge verzehrt) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (Blätter, Stängel, Zwiebeln) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | oxalic_acid (Oxalsäure — kann Nierensteine bei übermäßigem Konsum fördern) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt nötig. Abgestorbene Stiele und Blätter abzupfen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, frosttolerante Zwiebeln) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20% Perlite. pH 6.0–7.0. Zwiebeln ca. 3 cm tief einpflanzen. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum | 180–365 (bis Dormanz) | 1 | false | false | medium |
| Dormanz (sporadisch) | 14–28 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–24 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 (kühle, dunkle Ecke) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 42–60 (fast gar nicht) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0–20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.4–0.8 | 6.0–7.0 | 40 | 15 |
| Dormanz | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 3 ml/L (monatlich) | Wachstum |
| Zimmerpflanzen-Dünger | Compo | base | 7-3-6 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatliche Düngung im aktiven Wachstum. Niemals während der Dormanz düngen. Halbe Empfehlungsdosis ausreichend.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.3 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; Substrat zwischen den Güssen leicht antrocknen lassen; bei Dormanz fast trocken lagern | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Kleine gelbe Punkte, Gespinste | medium |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |
| Blattläuse | Aphis spp. | Klebrige Ausscheidungen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Blattläuse |
| Sand auf Oberfläche | cultural | 1 cm Quarzsand | 0 | Trauermücke (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Grüner Sauerklee | Oxalis tetraphylla | Gleiche Gattung | Grüne Blätter, ähnliche Pflege |
| Maranta | Maranta leuconeura | Nyktinastie, ähnliches Blattverhalten | Nicht giftig für Haustiere |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Oxalis triangularis,"Lila Sauerklee;Glücksklee;Purple Shamrock;False Shamrock",Oxalidaceae,Oxalis,perennial,day_neutral,herb,bulbous,"6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a","Brasilien, Argentinien",yes,0.5-3,10,15-30,20-40,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Bloomscape — Oxalis Care Guide](https://bloomscape.com/plant-care-guide/oxalis/) — Pflegehinweise, Nyktinastie
2. [Ohio Tropics — Oxalis triangularis](https://www.ohiotropics.com/2019/08/11/oxalis-triangularis-purple-shamrock/) — Kulturdaten
3. [House Plant House — Oxalis Dormancy](https://houseplanthouse.com/2018/10/09/oxalis-triangularis-dormancy/) — Dormanz-Management
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (Oxalsäure — mild giftig für Haustiere)
