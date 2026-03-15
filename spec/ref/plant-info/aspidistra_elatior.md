# Schusterpalme, Gusseisenpflanze — Aspidistra elatior

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/aspidistra-elatior-cast-iron-plant-grow-and-care-tips), [Epic Gardening](https://www.epicgardening.com/cast-iron-plant/), [Ohio Tropics](https://www.ohiotropics.com/2019/05/12/cast-iron-plant-care-how-to-care-for-aspidistra-elatior/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aspidistra elatior | `species.scientific_name` |
| Volksnamen (DE/EN) | Schusterpalme, Gusseisenpflanze, Schildblatt; Cast Iron Plant, Bar Room Plant, Iron Plant | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Aspidistra | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 7a, 7b, 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — winterhart bis -15°C in Zone 7. Als Zimmerpflanze optimal bei 7–27°C. Sehr breite Temperaturtoleranz. | `species.hardiness_detail` |
| Heimat | Japan, China — schattige Bergwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Schusterpalme (kein tatsächlicher Verwandter von Palmen) ist die robusteste Zimmerpflanze überhaupt — daher der englische Name "Cast Iron Plant" (Gusseisenpflanze). Sie überlebt Vernachlässigung, Dunkel, Trockenheit und Staub, die andere Pflanzen töten würden. Sehr langsam wachsend (2–5 neue Blätter/Jahr). Der Name "Schusterpalme" stammt aus der Jahrhundertwende, als sie in schlecht beleuchteten Schusterwerkstätten und Wirtshäusern (daher auch "Bar Room Plant") stand.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (bodennah unscheinbare lila Blüten — in Zimmerkultur selten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Rhizom beim Umtopfen im Frühjahr teilen — mindestens 2–3 Blätter pro Abschnitt. In frisches Substrat pflanzen. Langsame Etablierung (1–2 Jahre bis volle Schönheit).

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

**Hinweis:** Kein Rückschnitt. Nur komplett abgestorbene braune Blätter an der Basis abzupfen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 45–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 45–90 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten bis Schatten, frosttoleranter Standort) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Einheitserde mit 20% Perlite. pH 5.5–7.0. Gute Drainage. Substrat darf zwischen Güssen antrocknen. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterwachstum (sehr langsam) | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterwachstum (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 30–150 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 7–18 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 14–28 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.5–0.9 | 5.5–7.0 | 60 | 25 |
| Winterwachstum | 0:0:0 | 0.0–0.2 | 5.5–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich) | Wachstum |
| Zimmerpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis September. Oktober bis März kein Dünger. Die Pflanze überlebt auch ohne jegliche Düngung mehrere Jahre — angebautes Wachstum erwünscht.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; Substrat zwischen Güssen leicht antrocknen — Staunässe ist die einzige ernsthafte Bedrohung | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (wächst sehr langsam) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken (selten) | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste bei sehr trockener Luft | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Braune weiche Stängelbasis | Staunässe (einziger häufiger Fehler) |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Gießintervall stark reduzieren | 0 | Wurzelfäule (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse, Spinnmilbe |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Goldfruchtpalme | Dypsis lutescens | Ähnliches "tropisches" Blattwerk | Schneller wachsend |
| Drachenbaum | Dracaena marginata | Ähnlich robust, Zimmerpflanze | Mehr Sorten, attraktivere Blattfärbung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Aspidistra elatior,"Schusterpalme;Gusseisenpflanze;Schildblatt;Cast Iron Plant;Bar Room Plant",Asparagaceae,Aspidistra,perennial,day_neutral,herb,rhizomatous,"7a;7b;8a;8b;9a;9b;10a;10b;11a","Japan, China",yes,5-20,15,45-90,45-90,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Aspidistra elatior](https://www.gardenia.net/plant/aspidistra-elatior-cast-iron-plant-grow-and-care-tips) — Botanische Daten
2. [Epic Gardening — Cast Iron Plant](https://www.epicgardening.com/cast-iron-plant/) — Kulturdaten
3. [Ohio Tropics — Aspidistra elatior](https://www.ohiotropics.com/2019/05/12/cast-iron-plant-care-how-to-care-for-aspidistra-elatior/) — Pflegehinweise
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
