# Kornelkirsche — Cornus mas

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Kornelkirsche, Gartenrat Kornelkirsche, Gartenratgeber Kornelkirsche, Naturadb Cornus mas

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cornus mas | `species.scientific_name` |
| Volksnamen (DE/EN) | Kornelkirsche, Herlitze, Cornel; Cornelian Cherry | `species.common_names` |
| Familie | Cornaceae | `species.family` → `botanical_families.name` |
| Gattung | Cornus | `species.genus` |
| Ordnung | Cornales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; absolut zuverlässig in ganz Norddeutschland; einer der frühblühendsten Sträucher | `species.hardiness_detail` |
| Heimat | Südeuropa, Kleinasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge oder Kauf) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 8, 9 (August–September; rote, steinfrüchtige Früchte) | `species.harvest_months` |
| Blütemonate | 2, 3 (Februar–März; VOR dem Laubaustrieb — Phänologischer Indikator!) | `species.bloom_months` |

**Phänologischer Indikator:** Die Blüte der Kornelkirsche im Februar/März ist ein klassisches Zeichen des Vorfrühlings. Einer der frühesten Bienenweide-Sträucher des Jahres.

**Ernte:** Früchte erst ernten wenn vollreif (tiefrot) — unreif sehr sauer/adstringierend. Verarbeitung zu Marmelade, Likör, Mus. Frisch ähnlich wie Sauerkirschen.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (reife Früchte essbar) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6 (nach Blüte im Juni) oder 8 (nach Ernte) | `species.pruning_months` |

**Hinweis:** Schnitt NUR direkt nach der Blüte (nicht im Winter — Knospen für nächstes Jahr sitzen an altem Holz). Verjüngungsschnitt alle 5–8 Jahre; älteste Triebe bodennah entfernen. Toleriert aber starken Rückschnitt gut.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–600 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–500 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–400 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale, leicht kalkhaltige Gartenerde; pH 6,5–8,0; gut durchlässig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Winter/Frühjahr) | 21–42 | 1 | false | false | high |
| Vegetatives Wachstum | 120–150 | 2 | false | false | high |
| Fruchtreife | 60–90 | 3 | false | true | high |
| Winterruhe | 120–150 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum / Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 3000–8000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Vegetativ | 2:1:1 | 0.6–1.0 | 6.5–8.0 | 100 | 50 | — | 2 |
| Fruchtreife | 1:1:2 | 0.6–1.0 | 6.5–8.0 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | organisch | 3–5 L/m² | März/Oktober | Bodenverbesserung |
| Holzasche | — | organisch-mineralisch | 100–200 g/m² | August | Kaliumversorgung, Fruchtreife |
| Hornspäne (bei Bedarf) | Oscorna | organisch | 30–50 g/m² | April | Nur bei Mangelsymptomen |

### 3.2 Besondere Hinweise zur Düngung

Kornelkirsche ist sehr anspruchslos — auf normalen Böden kaum Düngung nötig. Im Zweijahres-Rhythmus etwas Kompost einarbeiten reicht völlig. Keine intensive Düngung (führt zu übermäßigem Wachstum auf Kosten der Fruchtbildung). Holzasche im August fördert das Ausreifen und die Fruchtqualität.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 6.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; trockenheitstolerant nach Etablierung; in Dürreperioden gießen für besseren Fruchtansatz | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 180 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 28 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Blüte bewundern | Erste Bienenweide; keine Eingriffe | niedrig |
| Jun | Schnitt nach Blüte | Leicht formen; älteste Triebe entfernen | mittel |
| Aug–Sep | Ernte | Vollreife Früchte; Marmelade, Likör, Mus | mittel |
| Okt | Kompost | Kompostgabe | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | vegetative (Frühjahr) | easy |

**Hinweis:** Kornelkirsche ist außergewöhnlich robust — Schädlinge und Krankheiten sind sehr selten.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Pilzbefall (Botrytis) | fungal | Grauschimmel | Feuchte, schlechte Luftzirkulation | 7–14 | Jungpflanzen |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |
| Standortverbesserung | cultural | — | Luftzirkulation verbessern | 0 | Pilze |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Obstgehölze / Wildfrüchte |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft; 30–80 Jahre Standzeit möglich |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Schlehe | Prunus spinosa | 0.8 | Frühe Bienenweide kombiniert; heimische Mischhecke | `compatible_with` |
| Holunder | Sambucus nigra | 0.8 | Heimische Mischhecke; Vögel | `compatible_with` |
| Wildrose | Rosa canina | 0.7 | Heimische Mischhecke | `compatible_with` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,harvest_months
Cornus mas,"Kornelkirsche;Herlitze;Cornelian Cherry",Cornaceae,Cornus,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Südeuropa, Kleinasien",limited,45,40,500,400,300,no,no,false,false,light_feeder,false,hardy,"2;3","8;9"
```

---

## Quellenverzeichnis

1. [Plantura — Kornelkirsche](https://www.plantura.garden/obst/kornelkirschen/kornelkirsche-pflanzenportrait) — Anbau, Pflege
2. [Gartenrat — Kornelkirsche](https://gartenrat.de/kornelkirsche/) — Kulturdaten
3. [Gartenratgeber — Kornelkirsche](https://www.gartenratgeber.net/pflanzen/kornelkirsche-herlitze.html) — Düngen, Schnitt
4. [Naturadb — Cornus mas](https://www.native-plants.de/946/kornelkirsche) — Steckbrief
