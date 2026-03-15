# Rotklee — Trifolium pratense

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Samenhaus.de Rotklee, Demonet-kleeluzplus Steckbrief Rotklee, Samen.de Rotklee im Fruchtwechsel, Plantura Gründüngung im Herbst

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Trifolium pratense | `species.scientific_name` |
| Volksnamen (DE/EN) | Rotklee, Wiesenklee; Red Clover, Meadow Clover | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Trifolium | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Keimling frostempfindlich; etablierte Pflanzen absolut winterhart | `species.hardiness_detail` |
| Heimat | Europa, Westasien; weltweit kultiviert | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -21 (Frühjahrssaat ab März möglich bei leichtem Frost) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5, 8, 9 | `species.direct_sow_months` |
| Erntemonate | — (Gründüngung: Einarbeitung Aug–Sep; Futterpflanze: 5, 6, 7, 8, 9) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (essbar; Blüten und Blätter) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Phytoöstrogene (Isoflavone) — relevant für schwangere Tiere bei großen Mengen | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kleepollenallergie möglich) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8 (Mahd regt Nachaustrieb an) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5–10 (Flächenansaat: 20–30 g/m²) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (Gründüngung auf Beeten; keine Topfkultur) | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Rosette/Jungpflanze | 28–42 | 2 | false | false | medium |
| Vegetatives Wachstum | 30–60 | 3 | false | true | high |
| Blüte & Samenreife | 42–60 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | — (Niederschlag ausreichend) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | — | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.0 | – | – | – | – |
| Wachstum | 0:1:1 (KEIN N; fixiert selbst) | 0.6–1.0 | 6.0–7.0 | 80 | 30 | – | 1 |
| Blüte/Samenreife | 0:1:2 | 0.5–0.8 | 6.0–7.0 | 60 | 30 | – | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Gründüngungsleistung

| Parameter | Wert |
|-----------|------|
| N-Fixierung (gesamt) | 260–420 kg N/ha/Jahr (Spross + Wurzel) |
| N-Fixierung (für Folgekultur verfügbar) | 60–150 kg N/ha |
| Einarbeitungszeitpunkt | Vollblüte bis Beginn Samenreife (maximaler N-Gehalt) |
| Einarbeitungstiefe | 15–20 cm; gut einmischen |
| Wartezeit vor Folgekultur | 3–4 Wochen nach Einarbeitung |
| Frostgare (Winterzwischenfrucht) | Friert ab → kein Einarbeiten nötig; Mulch bleibt |

### 3.2 Empfohlene Begleitdüngung

**KEIN Stickstoff düngen!** Rotklee fixiert N selbst über Rhizobium-Symbiose. Bei sehr armen Böden einmalig P und K zur Saatbettbereitung:

| Produkt | Marke | Typ | Ausbringrate | Saison | Hinweis |
|---------|-------|-----|-------------|--------|---------|
| Superphosphat oder Rohphosphat | Hauert | mineral/organisch | 30–40 g/m² | vor Aussaat | Nur auf P-armen Böden |
| Kaliumsulfat | – | mineral | 20–30 g/m² | vor Aussaat | Nur auf K-armen Böden |
| Rhizobium-Impfpräparat | Raiffeisen Saatgut | biologisch | nach Herstellerangabe | zur Aussaat | Auf unbekannten Böden empfohlen |

### 3.3 Besondere Hinweise zur Düngung

Rotklee deckt seinen Stickstoffbedarf vollständig über die Symbiose mit Bodenbakterien (Rhizobium leguminosarum bv. trifolii). Stickstoffdüngung ist kontraproduktiv — unterbindet die Symbiose. Wichtig: pH über 6,0 sicherstellen (Kalkung bei Bedarf), damit die Rhizobium-Bakterien aktiv sind.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 (Niederschlag reicht meist) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; pH 6,0–7,5; verträgt kurze Trockenheit | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (keine Düngung) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Gründüngungsplan im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Frühjahrssaat | 20–30 g/m²; 1 cm tief einharken; nach Ernte von Frühkulturen | hoch |
| Jun | Aufgang prüfen | Gleichmäßige Bedeckung sicherstellen; Lücken nachsäen | niedrig |
| Aug–Sep | Einarbeitung (Frühjahrssaat) | Vor der Vollblüte oder bei Vollblüte; Grünmasse eingraben | hoch |
| Aug–Sep | Herbstsaat (Überwinterung) | Für N-Hinterlassenschaft im Frühjahr; friert teilweise ab | mittel |
| Apr (Folgejahr) | Frühjahrseinarbeitung | Abgefrorene Masse einarbeiten oder mulchen | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kleespitzmaus | Apion apricans | Schotenrüssler; Samenzerstörung | flower, seed | flowering | difficult |
| Blattläuse | Aphis craccivora | Kolonien; Wachstumshemmung | shoot | seedling, vegetative | easy |
| Kleewürger | Cuscuta spp. | Parasitische Schlingpflanze | ganze Pflanze | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Kleekrebs | fungal (Sclerotinia trifoliorum) | Welken; weißes Myzel; schwarz-braune Sklerotien | Feuchte, Winter | 14–28 | Herbst/Winter |
| Echter Mehltau | fungal (Erysiphe trifolii) | Weißgrauer Belag | Trockenheit | 5–10 | vegetative |
| Kleerost | fungal (Uromyces trifolii) | Rostbraune Pusteln | Nässe | 7–14 | vegetative |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Fruchtfolge einhalten | cultural | – | 3–4 Jahre Pause | 0 | Kleekrebs |
| pH korrekt einstellen | cultural | – | Kalkung bei pH < 6,0 | 0 | allgemein |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (nitrogen_fixer) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kohl, Kürbis, Mais) oder Getreide |
| Empfohlene Nachfrucht | Alle Kulturen profitieren: Wintergetreide (+20–40% Ertrag), Kohl, Möhren |
| Anbaupause (Jahre) | 3–4 Jahre auf gleicher Fläche (Kleekrebs-Prävention) |

### 6.2 N-Hinterlassenschaft für Nachkulturen

| Folgekultur | N-Verfügbar (kg N/ha) | Empfehlung |
|------------|----------------------|------------|
| Winterweizen | 60–100 | N-Düngereinsparung bis 50% |
| Winterroggen | 50–80 | Ideale Nachfrucht |
| Kohlrabi/Brokkoli | 60–120 | Profitiert stark |
| Kartoffeln | 40–80 | Risiko Rhizoctonia beachten |

### 6.3 Mischkultur

Rotklee wird primär als Gründüngung in Fruchtwechselprogrammen eingesetzt, nicht in klassischer Mischkultur-Bepflanzung. Als Untersaat unter Sommergetreide oder Mais möglich.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Trifolium pratense |
|-----|-------------------|-------------|--------------------------------------|
| Weißklee | Trifolium repens | Gleiche Gattung | Niedrigwüchsiger; für Rasengründüngung; weniger Biomasse |
| Inkarnatklee | Trifolium incarnatum | Gleiche Gattung | Winterzwischenfrucht; tiefe Pfahlwurzel |
| Luzerne | Medicago sativa | Gleiche Familie | Mehrjährig; tiefere Wurzeln; höhere N-Fixierung |
| Gelbsenf | Sinapis alba | Gründüngung | Schnellwachsend; kein Kleekrebs-Risiko |
| Phacelia | Phacelia tanacetifolia | Gründüngung | Keine Brassicaceae-Krankheiten; Bienenweide |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Trifolium pratense,"Rotklee;Wiesenklee;Red Clover",Fabaceae,Trifolium,perennial,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",-0.1,"Europa, Westasien",no,,,60,40,8,no,no,false,false,nitrogen_fixer,true,hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Samenhaus.de Rotklee — Futterpflanze, Heilkraut und Gründüngung](https://www.samenhaus.de/gartenblog/rotklee-futterpflanze-heilkraut-und-gruenduengung) — Gründüngungsleistung
2. [Demonet-kleeluzplus Steckbrief Rotklee](https://www.demonet-kleeluzplus.de/mam/cms15/dateien/steckbrief_rotklee.pdf) — N-Fixierung, Anbaudaten
3. [Samen.de Rotklee im Fruchtwechsel](https://samen.de/blog/rotklee-im-fruchtwechsel-optimale-anbaufolge.html) — Fruchtfolge
4. [Plantura Gründüngung im Herbst](https://www.plantura.garden/gartenpraxis/gartenarbeiten/gruenduengung-im-herbst) — Anwendung
