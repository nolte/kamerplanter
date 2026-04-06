# Flieder — Syringa vulgaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Syringa vulgaris, Plantura Flieder düngen, Lubera Flieder, Pflanzen-Kölle Flieder

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Syringa vulgaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Gemeiner Flieder, Edelflieder; Common Lilac | `species.common_names` |
| Familie | Oleaceae | `species.family` → `botanical_families.name` |
| Gattung | Syringa | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–7b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; Vernalisierung nötig (Kälteperiode für Blüteninduktion); in Norddeutschland absolut winterhart | `species.hardiness_detail` |
| Heimat | Balkanhalbinsel (Südosteuropa); Bergwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Veredelung oder Stecklinge) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Schnittblume 5) | `species.harvest_months` |
| Blütemonate | 4, 5 (Phänologischer Indikator; Duft-Frühblüher) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, grafting | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (intensiver Blütenduft; bei empfindlichen Personen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (direkt nach Blüte) | `species.pruning_months` |

**KRITISCH:** Wie Forsythie blüht Flieder an diesjährigem Vorjahresholz. Schnitt DIREKT nach der Blüte (Mai/Juni). Verblühte Blütenstände sofort entfernen — verhindert Samenbildung, fördert Neuaustrieb mit Blütenknospen. Radikalschnitt aller 5–8 Jahre zur Verjüngung möglich.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 50–80 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–500 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–400 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–300 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, kalkhaltige Erde; pH 6,5–7,5; durchlässig; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Frühjahr) | 14–21 | 1 | false | false | medium |
| Triebwachstum (Sommer) | 90–120 | 2 | false | false | high |
| Knospenanlage (Herbst) | 60–90 | 3 | false | false | high |
| Vernalisierung/Winterruhe | 90–120 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Triebwachstum (Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 3000–8000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Blüte | 0:2:1 | 0.8–1.2 | 6.5–7.5 | 100 | 50 | – | 1 |
| Triebwachstum | 2:1:2 | 1.0–1.4 | 6.5–7.5 | 120 | 60 | – | 2 |
| Knospenanlage | 0:2:3 | 0.8–1.2 | 6.5–7.5 | 100 | 50 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 3–5 L/m² | Mai (nach Blüte), Oktober | Bodenverbesserung |
| Gehölzdünger | Neudorff Bio | organisch | 60–80 g/m² | Mai | medium_feeder |
| Hornspäne | Oscorna | organisch | 50 g/m² | Mai | N für neue Triebe |
| Phosphat-Dünger | Hauert Substral | organisch | 40 g/m² | Februar–März (vor Blüte) | Blütenförderung |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| Februar–März (Knospenschwellen) | P-betont | Phosphat-Dünger | 40 g/m² | Blütenentfaltung unterstützen |
| Mai (direkt nach Blüte) | N-betont | Hornspäne + Kompost | je 50 g/m² + 3L/m² | Neue Triebe für Blüte nächstes Jahr |
| August | KEIN N | Kaliumsulfat | 25 g/m² | Holzreife |

### 3.3 Besondere Hinweise zur Düngung

Flieder blüht sehr gerne auch ohne Düngung. Zu viel N fördert lange Triebe mit wenig Blüten. Phosphor-betonte Düngung im Frühjahr fördert Blütenreichtum. Wichtig: Ausreichend Kalk im Boden (pH über 6,5) — saure Böden korrektiv kalken.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; verträgt Kalk gut (pH 6,5–7,5); kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 120 (1–2× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | P-Dünger | Phosphat-betont vor Blüte | mittel |
| Apr–Mai | Blüte | Schnittblumen ernten (Knospen halb geöffnet) | niedrig |
| Mai | Rückschnitt nach Blüte | Verblühte Rispen sofort entfernen; Formschnitt | hoch |
| Mai | Düngung | Hornspäne + Kompost direkt nach Schnitt | hoch |
| Jun–Sep | Triebwachstum | Kräftige neue Triebe tragen nächste Blüte | – |
| Aug | Kaliumbereitstellung | Kaliumsulfat; kein N mehr | mittel |
| Nov | Ausreißer entfernen | Syringa bildet Wurzelausläufer — regelmäßig kontrollieren | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Fliederblattläuse | Aphis syriacae | Kolonien an Triebspitzen; Knospendeformation | shoot | spring | easy |
| Flieder-Miniermotte | Caloptilia syringella | Minen in Blättern (eingerollte Blätter) | leaf | vegetative | medium |
| Dickmaulrüssler | Otiorhynchus sulcatus | Buchtige Fraßstellen am Blattrand | leaf | vegetative | medium |
| Flieder-Gallmücke | Contarinia spp. | Gallen auf Blättern | leaf | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal (Microsphaera syringae) | Weißer Belag | Trockenheit | 5–10 | vegetative (Spätsommer) |
| Bakterienbrand | bacterial (Pseudomonas syringae pv. syringae) | Braune Flecken; Triebsterben | Kälte-Feuchte | 7–14 | spring |
| Phytophthora-Wurzelfäule | fungal (Phytophthora spp.) | Welken; braune Wurzeln | Staunässe | 14–28 | alle |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse, Motte |
| Befallene Triebe entfernen | cultural | – | Sofort vernichten | 0 | Bakterienbrand |
| Kupferfungizid | chemical | Kupferhydroxid | Frühjahr prophylaktisch | 7 | Bakterienbrand |
| Gute Drainage | cultural | – | Standortwahl; Hochbeet | 0 | Phytophthora |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Forsythie | Forsythia × intermedia | 0.9 | Gleiche Blütezeit (April/Mai); ergänzend | `compatible_with` |
| Tulpen | Tulipa spp. | 0.8 | Frühjahrskombination | `compatible_with` |
| Narzissen | Narcissus spp. | 0.8 | Gleichzeitige Frühjahrsblüte | `compatible_with` |
| Rosen | Rosa spp. | 0.7 | Folgeprogramm nach Flieder | `compatible_with` |

### 6.2 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Flieder (eigene Art) | Syringa vulgaris | Wurzelausläufer unterdrücken Nachbarpflanzen; rasch ausbreitend | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Syringa vulgaris |
|-----|-------------------|-------------|-------------------------------------|
| Hängender Flieder | Syringa reflexa | Gleiche Gattung | Hängende Blütentriebe; Rarität |
| Zwerg-Flieder | Syringa meyeri 'Palibin' | Gleiche Gattung | Kompakt (bis 150 cm); Kübel möglich |
| Japanischer Flieder | Syringa reticulata | Gleiche Gattung | Baumform; Spätblüher (Juni) |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Syringa vulgaris,"Gemeiner Flieder;Edelflieder;Common Lilac",Oleaceae,Syringa,perennial,long_day,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b",0.0,"Balkanhalbinsel, Südosteuropa",limited,65,50,500,400,250,no,no,false,false,medium_feeder,false,hardy,"4;5"
```

---

## Quellenverzeichnis

1. [Plantura Flieder düngen](https://www.plantura.garden/gehoelze/flieder/flieder-duengen) — Düngung, Pflege
2. [Lubera Flieder](https://www.lubera.com/de/gartenbuch/flieder-pflanzen-schneiden-vermehren-krankheiten-p2528) — Schnitt, Krankheiten
3. [Pflanzen-Kölle Flieder](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-flieder-richtig/) — Pflege
4. [Dekorationgarten Syringa vulgaris](https://www.dekorationgarten.com/gartenarbeit/syringa-vulgaris-anbau-pflege-schadlinge-und-krankheiten/) — Steckbrief, Schädlinge
