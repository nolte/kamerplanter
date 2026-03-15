# Schwedischer Efeu — Plectranthus verticillatus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/plectranthus-verticillatus-swedish-ivy-grow-care-guide), [Epic Gardening](https://www.epicgardening.com/swedish-ivy/), [UK Houseplants](https://www.ukhouseplants.com/plants/swedish-ivy), [Wikipedia — Plectranthus verticillatus](https://en.wikipedia.org/wiki/Plectranthus_verticillatus), [Gardener's Supply](https://www.gardeners.com/blogs/gardening-tips/swedish-ivy-care-9728)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Plectranthus verticillatus | `species.scientific_name` |
| Volksnamen (DE/EN) | Schwedischer Efeu, Kreuzblume; Swedish Ivy, Creeping Charlie | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Plectranthus | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 7°C; typische Zimmerpflanze; in Mitteleuropa nur indoor | `species.hardiness_detail` |
| Heimat | Südafrika, Australien (eingebürgert) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis zur Taxonomie:** Plectranthus verticillatus ist trotz des Volksnamens "Schwedischer Efeu" weder mit Efeu (Hedera) verwandt noch in Schweden heimisch. Der Name entstand, weil die Pflanze in Schweden seit Jahrzehnten sehr populär ist.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 9, 10, 11 (kleine weiß-lila Blüten; Kurztagspflanze) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Stecklinge:** Eine der am einfachsten zu vermehrenden Zimmerpflanzen. Triebspitzen (5–8 cm, 2–3 Internodien) abschneiden, untere Blätter entfernen. Im Wasserglas oder direkt in Anzuchtsubstrat (Torf/Perlit 1:1) bewurzeln. Im Wasser sind nach 1–2 Wochen erste Wurzeln sichtbar; im Substrat dauert es 2–3 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannten | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

**Hinweis:** Regelmäßiges Einkürzen (Pinching / Entspitzen) fördert buschiges Wachstum und verhindert "Vergeilung" (etioliertes Wachstum). Triebspitzen können als Stecklinge genutzt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 (hängend bis 60 cm lang) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Qualitäts-Zimmerpflanzenerde mit guter Drainage; pH 6.0–7.0; kein reines Torf | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung | 14–21 | 1 | false | false | medium |
| Vegetativ | 60–365 | 2 | false | false | high |
| Blüte (Herbst) | 30–60 | 3 | false | false | high |
| Winterruhe | 60–90 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (feucht, nie nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Bewurzelung | 0:0:0 | 0.0 | 6.0–7.0 | — | — |
| Vegetativ | 3:1:2 | 0.8–1.2 | 6.0–7.0 | 80 | 40 |
| Blüte | 1:2:2 | 0.6–1.0 | 6.0–7.0 | 60 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Flüssigdünger Grünpflanzen | Compo | Flüssigdünger | 6-3-6 | 3 ml/L, alle 14d | Vegetativ |
| NPK 14-14-14 Langzeitdünger | Osmocote | Slow Release | 14-14-14 | 3 g/Topf/3 Monate | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Brennnesselbrühe (verdünnt) | eigen | organisch | 10 ml/L | Apr–Sep |
| Kompost (beim Umtopfen) | eigen | organisch | 20% Beimischung | Frühling |

### 3.2 Besondere Hinweise zur Düngung

Mittelzehrend, aber sehr anpassungsfähig. Im Sommer alle 14 Tage leicht düngen. Von November bis Februar Düngepause. Zu starke Düngung führt zu weichen, hängenden Trieben und Anfälligkeit für Krankheiten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser geeignet; nicht zu kalt; gleichmäßige Feuchtigkeit bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Rückschnitt | Triebe auf 1/3 kürzen, Stecklinge abnehmen; Umtopfen | hoch |
| Apr–Sep | Aktive Wachstumsphase | Regelmäßig wässern und düngen; monatlich Triebspitzen kürzen | mittel |
| Okt–Nov | Blüte | Wenig eingreifen; verblühte Triebe entfernen | niedrig |
| Dez–Jan | Winterruhe | Gießen reduzieren; kein Dünger; heller, kühler Standort | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollknäuel in Blattachseln | easy |
| Blattläuse | Aphidoidea | Triebspitzen verformt, Honigtau | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbliche Blätter | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Pythium) | Welke, schwarze Wurzeln | Staunässe |
| Echter Mehltau | fungal | Weißer Belag | Trockene Luft, schlechte Belüftung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Blattläuse, Wollläuse |
| Isopropanol | biological | Isopropylalkohol | Wattestäbchen | 0 | Wollläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tradescantia | Tradescantia zebrina | 0.8 | Ähnliche Anforderungen, ähnliche Wuchsform | `compatible_with` |
| Chlorophytum | Chlorophytum comosum | 0.7 | Robuste Nachbarn, gleiche Pflege | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sukkulenten | diverse | Gegensätzliche Wasseransprüche | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Silber-Plektranthus | Plectranthus argentatus | Gleiche Gattung | Dekoratives Silberblattmuster |
| Mosaikpflanze | Fittonia albivenis | Ähnliche Wuchsform | Dekorativere Blätter |
| Tradescantia | Tradescantia zebrina | Ähnliche Hängepflanze | Farbiger, raschwüchsiger |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Plectranthus verticillatus,Schwedischer Efeu;Swedish Ivy;Creeping Charlie,Lamiaceae,Plectranthus,perennial,day_neutral,herb,fibrous,10a;10b;11a;11b,0.0,"Südafrika, Australien",yes,3,12,30,90,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Gardenia.net — Plectranthus verticillatus](https://www.gardenia.net/plant/plectranthus-verticillatus-swedish-ivy-grow-care-guide) — Allgemeine Kulturdaten
2. [Epic Gardening — Swedish Ivy](https://www.epicgardening.com/swedish-ivy/) — Pflegehinweise, Schädlinge
3. [UK Houseplants — Swedish Ivy](https://www.ukhouseplants.com/plants/swedish-ivy) — Temperatur, Gießen
4. [Wikipedia — Plectranthus verticillatus](https://en.wikipedia.org/wiki/Plectranthus_verticillatus) — Taxonomie, Herkunft
5. [Gardener's Supply — Swedish Ivy Care](https://www.gardeners.com/blogs/gardening-tips/swedish-ivy-care-9728) — Kulturhinweise
