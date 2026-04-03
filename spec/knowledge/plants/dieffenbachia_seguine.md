# Dieffenbachie — Dieffenbachia seguine

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/dieffenbachia-seguine/), [Planet Natural](https://www.planetnatural.com/dieffenbachia/), [Gardeners.com](https://www.gardeners.com/blogs/houseplant-encyclopedia/dieffenbachia-care-9747), [Poison Control](https://www.poison.org/articles/dieffenbachia-and-philodendron-202), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dieffenbachia seguine | `species.scientific_name` |
| Volksnamen (DE/EN) | Dieffenbachie, Stumme Bohne; Dumb Cane, Leopard Lily | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Dieffenbachia | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–30°C. Empfindlich gegen Zugluft und Kälte. | `species.hardiness_detail` |
| Heimat | Tropisches Amerika (Karibik, Mittel- und Südamerika — feuchte Tropenwälder) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**SICHERHEITSHINWEIS:** Dieffenbachia enthält Calciumoxalat-Raphiden (Nadelkristalle). Bei Kontakt mit Mund und Zunge: starkes Brennen, Schwellung, vorübergehender Sprachverlust (daher "Dumb Cane"). In schweren Fällen können Atemwege schwellen — ärztliche Behandlung erforderlich! Kinder und Tiere MÜSSEN von dieser Pflanze ferngehalten werden. NIEMALS ohne Handschuhe umtopfen oder schneiden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 4, 5, 6 (Spadix/Kolbenblüte, selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stängelstücke (5–10 cm, mit mind. 1 Auge) horizontal in feuchtes Substrat legen oder aufrecht einpflanzen. Bewurzelung bei 22–26°C in 3–6 Wochen. Handschuhe tragen! Alternativ: Basis-Triebe teilen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap (alle Pflanzenteile) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides, proteolytic_enzymes | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Saft — Handschuhe obligatorisch) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kahle Stiele (untere Blätter fallen mit der Zeit ab) auf 5–10 cm kürzen — treiben neu aus. HANDSCHUHE und Schutzbrille verwenden, Saft nicht in Augen/Mund. Schnittwerkzeug danach reinigen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–180 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20–30% Perlite. pH 6.0–7.0. Hohe organische Substanz bevorzugt. Gute Drainage unerlässlich. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 17–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–6.5 | 100 | 40 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Guano-Flüssigdünger | Gardol | organisch | 4 ml/L | Wachstum |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Stickstoffbetonte Formel fördert das üppige, große Laub. Bei schlechtem Licht: Düngermenge reduzieren (Pflanze kann Nährstoffe nicht verwerten).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; hartes Wasser führt zu Blattrandnekrosen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, gelbe Flecken | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Blattlaus | Aphididae | Kolonien, Honigtau, Deformation | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, fauliger Geruch | Staunässe |
| Blattflecken | fungal/bacterial | Braune/gelbe Flecken | Nasses Laub, Luftzirkulation schlecht |
| Botrytis | fungal | Grauschimmel | Hohe Feuchtigkeit, schlechte Belüftung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (HANDSCHUHE!) | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus, Schmierlaus |
| Drainage verbessern | cultural | Topf/Substrat wechseln | 0 | Wurzelfäule |
| Luftzirkulation | cultural | Ventilator aufstellen | 0 | Botrytis, Blattflecken |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kompakte Dieffenbachie | Dieffenbachia compacta | Gleiche Gattung | Kleiner, kompakter |
| Büscheldieffenbachie | Dieffenbachia maculata | Gleiche Gattung | Auffällige Blattmusterung |
| Philodendron | Philodendron hederaceum | Ähnliches Erscheinungsbild | Weniger gefährlich bei Kontakt |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Dieffenbachia seguine,"Dieffenbachie;Stumme Bohne;Dumb Cane;Leopard Lily",Araceae,Dieffenbachia,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Tropisches Amerika",yes,5-15,20,60-180,50-100,yes,no,false,medium_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Camille,Dieffenbachia seguine,"ornamental;cream_center;green_edges",clone
Compacta,Dieffenbachia seguine,"ornamental;compact;green_white",clone
Tropic Snow,Dieffenbachia seguine,"ornamental;large;cream_variegated",clone
```

---

## Quellenverzeichnis

1. [NC State Extension — Dieffenbachia seguine](https://plants.ces.ncsu.edu/plants/dieffenbachia-seguine/) — Botanische Daten, Kulturdaten
2. [Planet Natural — Dieffenbachia](https://www.planetnatural.com/dieffenbachia/) — Pflegehinweise
3. [Gardeners.com — Dieffenbachia Care](https://www.gardeners.com/blogs/houseplant-encyclopedia/dieffenbachia-care-9747) — Licht, Gießen
4. [Poison Control — Dieffenbachia and Philodendron](https://www.poison.org/articles/dieffenbachia-and-philodendron-202) — Toxizitätsdetails
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
