# Kentia-Palme — Howea forsteriana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/kentia-palm-howea-forsteriana-care-guide-and-plant-information/), [Gardenia.net](https://www.gardenia.net/plant/howea-forsteriana-kentia-palm-grow-and-care-tips), [Gardening Know How](https://www.gardeningknowhow.com/houseplants/kentia-palm/howea-forsteriana-kentia-palm.htm), [NC State Extension](https://plants.ces.ncsu.edu/plants/howea-forsteriana/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Howea forsteriana | `species.scientific_name` |
| Volksnamen (DE/EN) | Kentia-Palme, Paradiespalme; Kentia Palm, Sentry Palm, Paradise Palm | `species.common_names` |
| Familie | Arecaceae | `species.family` → `botanical_families.name` |
| Gattung | Howea | `species.genus` |
| Ordnung | Arecales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 50–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — toleriert kurze Fröste bis -3°C (25°F). Mindesttemperatur 5°C, optimal 18–27°C. | `species.hardiness_detail` |
| Heimat | Lord-Howe-Insel (Australien) — subtropischer Regenwald | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Kentia-Palme ist die eleganteste und robusteste Zimmerpalme — seit dem Viktorianischen Zeitalter eine beliebte Innenraumpflanze. Sie toleriert niedrige Lichtverhältnisse besser als fast alle anderen Palmen und stellt keine hohen Ansprüche. Wächst sehr langsam (6–12 cm/Jahr) und kann Jahrzehnte im gleichen Topf verbringen. Schlüsselschwäche: empfindlich gegenüber Fluorid und Salzansammlungen im Substrat — Leitungswasser über Nacht stehen lassen oder gefiltertes Wasser verwenden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nicht zuverlässig in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Nur durch Samen vermehrbar (keine Teilung oder Stecklinge). Samen langsam in warmem Substrat (25–30°C) säen, Keimung 3 Monate bis zu mehreren Jahren. Kommerziell werden mehrere Sämlinge pro Topf gesetzt für einen buschigeren Wuchs.

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

**Hinweis:** ASPCA listet Howea forsteriana als nicht giftig für Katzen und Hunde. Eine der haustierfreundlichsten Palmen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Nur vollständig abgestorbene, braune Wedel an der Basis entfernen. Niemals grüne oder noch teilweise grüne Wedel schneiden — das schadet der Pflanze dauerhaft.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 (indoor, sehr langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gute, lockere Palmenerde oder Einheitserde mit 20% Perlite. pH 6.0–7.0. Gute Drainage. Nicht zu häufig umtopfen — mag leicht beengte Wurzeln. | — |

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
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 12–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Palmen-Dünger | Compo | base | 7-3-7 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Langzeitdünger-Stäbchen | Compo | organisch-mineralisch | 3–4 Stäbchen/Topf | Frühjahr |

### 3.2 Besondere Hinweise

Alle 2 Wochen März bis September. Oktober bis Februar: kein Dünger (Düngung im Winter schadet). Nur halbe Empfehlungsdosis verwenden — Kentia ist empfindlich gegen Überdüngung und Salzansammlungen. Wasser über Nacht stehen lassen (Chlor + Fluorid reduzieren) oder gefiltertes/destilliertes Wasser verwenden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Fluoridarmes Wasser (gefiltertes oder abgestandenes Leitungswasser); zu viel Fluorid/Salz verursacht braune Blattspitzen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (sehr langsam wachsend) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben und vertrocknen | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Wedelbasisachseln | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Blattstielen | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Wedel, weiche Stängelbasis | Staunässe |
| Fluorid-/Salztoxizität | physiologisch | Braune Blattspitzen | Fluorid/Salz im Gießwasser |
| Blattflecken | fungal | Braune Flecken mit gelbem Rand | Nasses Laub, Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |
| Gefiltertes Wasser | cultural | Wasserquelle wechseln | 0 | Fluoridtoxizität (Prävention) |
| Weniger gießen | cultural | Gießintervall verlängern | 0 | Wurzelfäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Stubenpalme | Chamaedorea elegans | Arecaceae, kompaktere Palme | Viel kleiner, für beengte Räume |
| Areka-Palme | Dypsis lutescens | Arecaceae, ähnlicher Look | Schneller wachsend, buschiger |
| Livistona-Palme | Livistona rotundifolia | Arecaceae, Fächerpalme | Runde Wedel, andere Textur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Howea forsteriana,"Kentia-Palme;Paradiespalme;Kentia Palm;Sentry Palm",Arecaceae,Howea,perennial,day_neutral,tree,fibrous,"9b;10a;10b;11a;11b","Lord-Howe-Insel (Australien)",yes,10-30,30,150-300,80-150,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Kentia Palm](https://www.healthyhouseplants.com/indoor-houseplants/kentia-palm-howea-forsteriana-care-guide-and-plant-information/) — Pflegehinweise, Fluoridsensitivität
2. [Gardenia.net — Howea forsteriana](https://www.gardenia.net/plant/howea-forsteriana-kentia-palm-grow-and-care-tips) — Botanische Daten, USDA-Zonen
3. [Gardening Know How — Kentia Palm](https://www.gardeningknowhow.com/houseplants/kentia-palm/howea-forsteriana-kentia-palm.htm) — Allgemeine Pflege
4. [NC State Extension — Howea forsteriana](https://plants.ces.ncsu.edu/plants/howea-forsteriana/) — Wissenschaftliche Basisdaten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
