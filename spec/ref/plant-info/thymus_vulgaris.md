# Thymian — Thymus vulgaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Thymian, NaturaDB Thymus vulgaris, Pflanzentanzen.de winterharte Kräuter

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Thymus vulgaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Thymian, Echter Thymian, Gartenthymian; Thyme, Garden Thyme | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Thymus | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −15 °C bis −20 °C je nach Sorte; in Norddeutschland ohne Schutz überwinterungsfähig; bei Kahlfrösten Vlies empfohlen | `species.hardiness_detail` |
| Heimat | Westliches Mittelmeer (Südfrankreich, Spanien) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 | `species.direct_sow_months` |
| Erntemonate | 3, 4, 5, 6, 7, 8, 9, 10 (außerhalb des Winters) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false (in kleinen Mengen) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Thymol (antimikrobiell; in Medizindosen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (nach der Blüte; um 1/3) | `species.pruning_type` |
| Rückschnitt-Monate | 4, 7 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr viel Licht nötig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Magere, durchlässige Erde (Kräutererde + 30% Quarzsand/Kies); pH 6,0–8,0 | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzeln | 21–42 | 1 | false | false | low |
| Aktives Wachstum (Apr–Okt) | 180–210 | 2 | false | true | high |
| Blüte | 21–42 | 3 | false | true | high |
| Winterruhe (Nov–Mär) | 120–150 | 4 | false | true (sparsam) | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (Volllsonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Einwurzeln | 1:2:1 | 0.5–0.7 | 6.0–7.5 | 50 | 25 | — | 1 |
| Aktives Wachstum | 1:1:1 | 0.7–1.0 | 6.0–8.0 | 70 | 35 | — | 1 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt, sehr sparsam)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 0.3 L/Pflanze | 1× im Frühjahr |

#### Mineralisch (bei Bedarf)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kräuter-Dünger | Compo | base | 10-4-10 | 3–5 g/Pflanze | 1× Frühjahr |

### 3.2 Besondere Hinweise zur Düngung

Thymian NICHT düngen — magrerem Boden entspricht höherem Thymolgehalt und intensiverem Aroma. Jährliche Frühjahrsgabe von etwas Kompost genügt vollständig. Bei zu viel Nährstoffen verliert er seinen typischen Geschmack.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gut abtrocknen lassen zwischen Gaben; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 (kaum düngen!) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–5 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Rückschnitt | Um 1/3 zurückschneiden, Holzige Triebe entfernen | hoch |
| Mai | Auspflanzen (Neupflanzung) | Nach Eisheiligen | mittel |
| Jun–Jul | Ernte & Rückschnitt nach Blüte | Nach der Blüte nochmals kürzen fördert neues Wachstum | mittel |
| Jun–Aug | Ernte | Junge Triebe regelmäßig ernten | mittel |
| Okt | Wintervorbereitung | Im Kübel: reinbringen oder schützen; im Beet: leichtes Mulchen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy (Zone 7b) / needs_protection (Zone 7a) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch (Laub oder Reisig) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover, prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | −15 (im Beet ohne Schutz möglich in Zone 7b) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste (bei Trockenheit) | leaf | summer (Hitze/Trockenheit) | medium |
| Thymian-Gallmücke | Jaapiella thymicola | Deformierte Blätter, Gallen | leaf | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Phytophthora) | Welke trotz feuchtem Substrat | Staunässe | 5–14 | all |
| Echter Mehltau | fungal | Weißlicher Belag | Feuchtigkeit + Wärme | 5–10 | vegetative |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Durchlüftung sicherstellen | cultural | — | Nicht zu dicht pflanzen | 0 | Mehltau, Wurzelfäule |
| Neemöl | biological | Azadirachtin | Sprühen, 0.3% | 3 | Spinnmilbe |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kohlgewächse | Brassica oleracea | 0.9 | Thymian-Duft vertreibt Kohlfliege und Weißling | `compatible_with` |
| Rosmarin | Salvia rosmarinus | 0.9 | Gleiche Standortansprüche | `compatible_with` |
| Erdbeere | Fragaria × ananassa | 0.8 | Schützt vor Schädlingen | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Thymian fördert Geschmack der Tomate | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Unterschiedliche Wasseransprüche | mild | `incompatible_with` |
| Minze | Mentha spicata | Minze breitet sich aus und überwächst Thymian | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Thymian |
|-----|-------------------|-------------|--------------------------|
| Zitronenthymian | Thymus citriodorus | Gleiche Gattung | Zitroniges Aroma; etwas frostempfindlicher |
| Breitblättriger Thymian | Thymus pulegioides | Gleiche Gattung | Robuster, stärker wüchsig |
| Oregano | Origanum vulgare | Gleiche Familie, ähnl. Aroma | Wüchsiger, einfacher in der Pflege |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Thymus vulgaris,"Thymian;Echter Thymian;Gartenthymian;Thyme",Lamiaceae,Thymus,perennial,day_neutral,shrub,fibrous,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.2,"Westliches Mittelmeer",yes,4,15,40,40,25,limited,yes,false,false,light_feeder,hardy,"3;4;5","3;4;5;6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Winterharte Kräuter — Plantura](https://www.plantura.garden/kraeuter/kraeuter-anbauen/winterharte-kraeuter) — Winterhärte
2. [Mehrjährige Kräuter — Hortica.de](https://hortica.de/mehrjaehrige-kraeuter-liste/) — Übersicht
3. [Pflanzentanzen.de Winterharte Küchenkräuter](https://pflanzentanzen.de/pflanzentipps/nutzpflanzen/kraeuter/winterharte-kraeuter/) — Praxis-Tipps
