# Zamioculcas — Zamioculcas zamiifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [New York Botanical Garden](https://libguides.nybg.org/ZZPlant), [Gardening Know How](https://www.gardeningknowhow.com/houseplants/zz-plant/caring-for-zz-plant.htm), [Garden Design ZZ Plant](https://www.gardendesign.com/houseplants/zz-plant.html), [ASPCA](https://www.aspca.org/), [Joy Us Garden](https://www.joyusgarden.com/zz-plant-care-tips/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Zamioculcas zamiifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Zamioculcas, Glücksfeder, Eternityplant; ZZ Plant, Zanzibar Gem, Eternity Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Zamioculcas | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Wurzelanpassungen | tuberous (sukkulente Rhizome/Knollen als Wasserspeicher) | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 8°C, optimal 18–26°C. Toleriert kurzzeitig 8°C ohne dauerhafte Schäden. | `species.hardiness_detail` |
| Heimat | Ostafrika (Tansania, Kenia, Malawi — trockene Regenwälder und Buschsavannen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Entfernte Schadstoffe | xylene, toluene, benzene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Zamioculcas ist monotypisch — die einzige Art in ihrer Gattung. Die sukkulenten Rhizome (Knollen) dienen als Wasser- und Nährstoffspeicher, weshalb die Pflanze extreme Trockenheit übersteht. Zu den genügsamsten Zimmerpflanzen überhaupt — ideal für Menschen, die ihre Pflanzen regelmäßig vergessen zu gießen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor extrem selten, bei reifen Pflanzen möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem, cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis Vermehrung:** (1) Teilung beim Umtopfen — schnellste Methode. (2) Stängelstecklinge in Wasser oder Substrat — Bewurzelung 2–3 Monate. (3) Einzelblattstecklinge — dauert am längsten (4–6 Monate bis zur Knollenbildung), bilden zuverlässig neue Knollen. Alle Methoden erfolgreich, aber Geduld erforderlich — Zamioculcas wächst generell langsam.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, roots | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_crystals | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Calciumoxalat-Kristalle bei Hautkontakt reizend — Handschuhe beim Umtopfen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt notwendig. Vergilbte oder beschädigte Triebe können an der Basis entfernt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 45–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Monate, kein Regen/Staunässe) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus-/Sukkulentenerde oder stark durchlässige Einheitserde (50% Erde + 50% Perlite/Grobsand). Guter Wasserabzug essentiell. Rhizome nicht vollständig mit Erde bedecken. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe (Wachstumsstillstand) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–55 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 30–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 2–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–45 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–45 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:1:1 | 0.4–0.8 | 6.0–7.0 | 60 | 20 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (halbe Dosis) | Wachstum |
| Zimmerpflanzen-Dünger (verdünnt) | Substral | base | 7-3-7 | 3 ml/L (1/3 Dosis) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |
| Hornspäne fein | Oscorna | organisch | 2 g/L Substrat | Frühling |

### 3.2 Besondere Hinweise

Zamioculcas ist ein extremer Schwachzehrer. Überdüngung schadet mehr als Unterdüngung. Maximal 3–4 Düngergaben pro Jahr. Niemals im Winter düngen. Bei verlangsamtem Wachstum (normal!) keine Düngersteigerung — Geduld ist gefragt.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; Staunässe unbedingt vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Gießen reaktivieren | Erste Wassergabe nach trockenen Wintermonaten | mittel |
| Apr | Düngung starten | Erste schwache Düngergabe | niedrig |
| Apr–Sep | Wässern | Substrat vollständig austrocknen lassen vor dem nächsten Gießen | hoch |
| Sep | Düngung beenden | Letzte Düngergabe des Jahres | niedrig |
| Okt–Feb | Sehr sparsammes Gießen | Rhizome speichern Wasser — 1x gießen pro Monat reicht | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Blattvergilbung | leaf | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | leaf, stem | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Rhizomfäule | fungal (Pythium, Phytophthora) | Gelbe Triebe, weiche Knollen, fauler Geruch | Überbewässerung, Staunässe |
| Blattflecken | bacterial/fungal | Braune, nasse Flecken | Wasser auf Blättern + Wärme |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Systeminsektizid | chemical | Stäbchen ins Substrat | 14 Tage | Schmierläuse |
| Umtopfen | cultural | Befallene Knollen auf Fäule prüfen, abfaulige Teile entfernen | 0 | Rhizomfäule |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Bogenhanf | Dracaena trifasciata | 0.9 | Identische Pflegeanforderungen |
| Aloe vera | Aloe vera | 0.9 | Gleiche Substrat- und Gießanforderungen |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Zamioculcas zamiifolia |
|-----|-------------------|-------------|------------------------------------------|
| Raven ZZ | Zamioculcas zamiifolia 'Raven' | Sorte mit fast schwarzen Blättern | Dramatische dunkle Blattfarbe |
| Bogenhanf | Dracaena trifasciata | Ähnliche Robustheit, anders geformt | Aufrechter Wuchs, sehr ähnliche Pflegeanforderungen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Zamioculcas zamiifolia,"Zamioculcas;Glücksfeder;ZZ Plant;Zanzibar Gem",Araceae,Zamioculcas,perennial,day_neutral,herb,rhizomatous,"9b;10a;10b;11a;11b",0.0,"Ostafrika (Tansania, Kenia)",yes,3-15,20,45-90,30-60,yes,limited,false,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Raven,Zamioculcas zamiifolia,"ornamental;black_leaves",clone
Zenzi,Zamioculcas zamiifolia,"ornamental;compact;curled_leaflets",clone
```

---

## Quellenverzeichnis

1. [New York Botanical Garden — ZZ Plant Guide](https://libguides.nybg.org/ZZPlant) — Botanische Hintergründe
2. [Gardening Know How — ZZ Plant](https://www.gardeningknowhow.com/houseplants/zz-plant/caring-for-zz-plant.htm) — Pflegehinweise
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Garden Design — ZZ Plant](https://www.gardendesign.com/houseplants/zz-plant.html) — Kulturdaten
5. [Patch Plants](https://www.patchplants.com/pages/plant-care/complete-guide-to-zamioculcas-zamiifolia-plant-care/) — Erfahrungswerte Pflege
