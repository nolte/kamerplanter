# Geweihfarn — Platycerium bifurcatum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Old Farmer's Almanac](https://www.almanac.com/plant/staghorn-fern-care-growing-platycerium-bifurcatum), [Gardenia.net](https://www.gardenia.net/plant/platycerium-bifurcatum-staghorn-fern), [NC State Extension](https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/), [Guide to Houseplants](https://www.guide-to-houseplants.com/staghorn-fern.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Platycerium bifurcatum | `species.scientific_name` |
| Volksnamen (DE/EN) | Geweihfarn, Hirschgeweihfarn; Staghorn Fern, Common Staghorn Fern, Elkhorn Fern | `species.common_names` |
| Familie | Polypodiaceae | `species.family` → `botanical_families.name` |
| Gattung | Platycerium | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart — Mindesttemperatur 5°C, optimal 16–24°C. Kurze Fröste bis -2°C werden nur ausnahmsweise toleriert; dauerhaft frostfreie Haltung erforderlich. | `species.hardiness_detail` |
| Heimat | Australien, Südostasien — epiphytisch auf Bäumen in tropischen/subtropischen Wäldern | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Geweihfarn ist ein Epiphyt (Aufsitzerpflanze) — er wächst natürlich auf Baumrinde, nicht in Erde. Zwei Blatttypen: Schildwedel (braun, schildförmig — wichtige Schutzstruktur, NIEMALS entfernen!) und Sporentragende Wedel (grün, geweihförmig). Am besten als Wandmontage auf Holz/Kork. In Töpfen entwickelt er schnell Wurzelfäule. Kann über 50 Jahre mit guter Pflege leben.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farn — keine Blüten, Sporenproduktion ganzjährig möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, spore | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) an der Pflanzenbasis bei 5–8 cm Größe vorsichtig mit Spatel abtrennen und auf ein neues Holzbrett montieren. Sporenvermehrung sehr langwierig (6–12 Monate bis zur erkennbaren Pflanze).

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

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Niemals die braunen Schildwedel entfernen — sie sind lebenswichtig für die Pflanze (Wasser- und Nährstoffspeicher, Wurzelschutz). Nur vollständig abgestorbene grüne Wedel entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Wandmontage stark bevorzugt) | `species.container_suitable` |
| Empf. Topfvolumen (L) | — (Montage auf 30×30 cm Holzbrett empfohlen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Wandmontage oder Hängekorb) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Epiphytisches Substrat: Sphagnum-Moos, Baumfarn-Chips, Kokoshäcksel. Niemals normale Erde. Bei Wandmontage: Sphagnum-Moos zwischen Pflanze und Brett. | — |

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
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–14 (Tauchbad 20 min) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 (Tauchbad) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 13–20 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 14–21 (Tauchbad) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.3–0.6 | 6.0–7.0 | 40 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L im Tauchwasser (monatlich) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Bananenblätter/Banane | Eigenherstellung | organisch | 1 reife Banane hinter Schildwedel legen | Frühjahr |
| Wurmhumus-Tee | Eigenherstellung | organisch | Im Tauchwasser verdünnt | Wachstum |

### 3.2 Besondere Hinweise

Monatliche Düngung im Wachstum, keine Düngung im Winter. Banane oder organische Materie hinter den Schildwedeln legen (natürliche Ernährungsweise). Niemals Dünger direkt auf die Wedel sprühen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | soak (Tauchbad 20 Minuten) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Raumtemperatur-Wasser; nach dem Tauchen gut abtropfen lassen — nie Wasser im Schildwedel stehenlassen (Fäulnis) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (nur wenn Pflanze Brett überwächst) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken zwischen Wedeln | medium |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Wedeln | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Schwarzfäule | fungal | Schwarze, weiche Stellen auf Schildwedeln | Staunässe nach Tauchen |
| Rhizoctonia-Fäule | fungal | Braune Flecken an Wedelbasis | Dauernasse Montagefläche |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (auf grüne Wedel) | 0 Tage | Schmierläuse, Schildlaus |
| Gut abtrocknen lassen | cultural | Nach Tauchbad vollständig trocknen | 0 | Fäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze (epiphytisch, Wandmontage).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Großer Geweihfarn | Platycerium superbum | Gleiche Gattung | Spektakulärer, bis 1,5 m Wedelbreite |
| Nestfarn | Asplenium nidus | Einfache Zimmerpflanze | Robuster, Topfhaltung möglich |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Platycerium bifurcatum,"Geweihfarn;Hirschgeweihfarn;Staghorn Fern;Elkhorn Fern",Polypodiaceae,Platycerium,perennial,day_neutral,herb,aerial,"10a;10b;11a;11b","Australien, Südostasien (epiphytisch)",limited,,, 30-90,30-90,yes,limited,true,light_feeder
```

---

## Quellenverzeichnis

1. [Old Farmer's Almanac — Staghorn Fern](https://www.almanac.com/plant/staghorn-fern-care-growing-platycerium-bifurcatum) — Pflegehinweise
2. [Gardenia.net — Platycerium bifurcatum](https://www.gardenia.net/plant/platycerium-bifurcatum-staghorn-fern) — Botanische Daten
3. [NC State Extension — Platycerium bifurcatum](https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/) — USDA-Zonen, Botanik
4. [Guide to Houseplants — Staghorn Fern](https://www.guide-to-houseplants.com/staghorn-fern.html) — Kulturdaten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
