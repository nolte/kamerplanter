# Stubenpalme — Chamaedorea elegans

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/chamaedorea-elegans-parlor-palm), [OurHouseplants](https://www.ourhouseplants.com/plants/parlour-palm), [Greenery Unlimited](https://greeneryunlimited.co/blogs/plant-care/neanthe-bella-palm-care), [Joy Us Garden](https://www.joyusgarden.com/neanthe-bella-palm-care-tips-for-this-table-top-palm/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Chamaedorea elegans | `species.scientific_name` |
| Volksnamen (DE/EN) | Stubenpalme, Bergpalme; Parlor Palm, Neanthe Bella Palm | `species.common_names` |
| Familie | Arecaceae | `species.family` → `botanical_families.name` |
| Gattung | Chamaedorea | `species.genus` |
| Ordnung | Arecales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–27°C. Verträgt normale Zimmertemperaturen sehr gut. | `species.hardiness_detail` |
| Heimat | Mexiko, Guatemala, Belize — tropische Bergregenwälder, Unterwuchs | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | benzene, formaldehyde, trichloroethylene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Stubenpalme (Neanthe Bella) ist eine der wenigen echten Palmen, die auch bei weniger Licht gedeiht und damit ideal für Innenräume ist. NASA Clean Air Study bestätigt gute Luftreinigungseigenschaften. Wichtig: Palmen mögen keine drastischen Standortwechsel und sollten nicht von stark wechselnden Lichtverhältnissen ausgesetzt werden. Wächst sehr langsam.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (gelbe Rispenkätzchen; bei adulten Pflanzen in Zimmerkultur möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Ausschließlich über Samen. Frische Samen (nicht älter als 3 Monate) bei 27–32°C und feuchtem Substrat. Keimung in 3–6 Monate. Kein vegetativer Vermehrungsweg. Im Handel erhältliche Pflanzen stammen aus Samen-Kultivierung.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Früchte/Fruchtsaft kann leichte Hautreizungen verursachen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Chamaedorea elegans ist NICHT giftig — ASPCA listet die Pflanze als sicher für Katzen, Hunde und Kinder.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Abgestorbene oder braune Wedel an der Basis entfernen. Niemals grüne Wedel schneiden — Palmen können nicht nachwachsen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (indoor, sehr langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–120 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Palmenerde oder Einheitserde mit 20% Perlite + 10% Sand. pH 6.0–7.0. Gute Drainage unerlässlich. Nie umtopfen wenn nicht notwendig (Palmen sind störungssensitiv). | — |

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
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:3 (K-betont, typisch für Palmen) | 0.6–1.0 | 6.0–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Palmen-Dünger | Compo | base | 5-3-7 | 5 ml/L (monatlich) | Wachstum |
| Zimmerpflanzen-Flüssigdünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Monatlich März bis September. Oktober bis Februar: kein Dünger. Palmen brauchen etwas mehr Kalium und Magnesium als typische Zimmerpflanzen. Fluorid schadet (Blattspitzenverbrennung) — kalkfreies Wasser bevorzugt. Spezielle Palmendünger sind empfehlenswert.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes, weiches Wasser bevorzugt (Fluorid schadet!); Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Wedel | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Hohe Luftfeuchtigkeit | cultural | Regelmäßig sprühen | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kentia-Palme | Howea forsteriana | Palme, Zimmerkultur | Robuster bei niedrigen Temperaturen |
| Areca-Palme | Dypsis lutescens | Palme, Zimmerkultur | Schneller wachsend |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Chamaedorea elegans,"Stubenpalme;Bergpalme;Parlor Palm;Neanthe Bella Palm",Arecaceae,Chamaedorea,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Mexiko, Guatemala, Belize",yes,3-15,20,60-200,40-120,yes,limited,false,light_feeder,0.6
```

---

## Quellenverzeichnis

1. [Gardenia.net — Chamaedorea elegans](https://www.gardenia.net/plant/chamaedorea-elegans-parlor-palm) — Botanische Daten, Kulturdaten
2. [OurHouseplants — Parlour Palm](https://www.ourhouseplants.com/plants/parlour-palm) — Detaillierte Pflegehinweise
3. [Greenery Unlimited — Neanthe Bella Palm](https://greeneryunlimited.co/blogs/plant-care/neanthe-bella-palm-care) — Pflegehinweise
4. [Joy Us Garden — Neanthe Bella Palm](https://www.joyusgarden.com/neanthe-bella-palm-care-tips-for-this-table-top-palm/) — Praxiswissen
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
