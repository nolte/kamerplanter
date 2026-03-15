# Liebliche Weigelie — Weigela florida

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** HeimHelden Weigelie, Lubera Weigelie, Gartenratgeber Weigelie, Gartenrat Weigelie, Naturadb Weigela florida

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Weigela florida | `species.scientific_name` |
| Volksnamen (DE/EN) | Liebliche Weigelie, Weigelie; Weigela | `species.common_names` |
| Familie | Caprifoliaceae | `species.family` → `botanical_families.name` |
| Gattung | Weigela | `species.genus` |
| Ordnung | Dipsacales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; in Norddeutschland problemlos; in ersten Jahren Frostschutz im Wurzelbereich empfehlenswert | `species.hardiness_detail` |
| Heimat | China, Korea, Japan | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6 (Hauptblüte Mai–Juni); 8, 9 (oft Nachblüte nach Schnitt) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Halbverholzte Stecklinge im Juli; holzige Stecklinge im Oktober/November. Sehr leicht bewurzelnd.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6 (direkt nach der Blüte) | `species.pruning_months` |

**Hinweis:** Weigelie blüht an vorjährigem Holz — Schnitt NUR direkt nach der Blüte (Juni). Ein beherzter Rückschnitt direkt nach der Blüte regt kräftige Neutriebe an, die im nächsten Jahr blühen. Kann auch einen leichten Nachblüteeffekt im Spätsommer auslösen. KEIN Schnitt im Herbst/Winter.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 35 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–250 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 100–150 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Gartenerde; pH 5,5–7,0; gut durchlässig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | medium |
| Blüte | 21–42 | 2 | false | false | medium |
| Vegetatives Wachstum | 90–120 | 3 | false | false | high |
| Winterruhe | 120–150 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 5.5–7.0 | 100 | 50 | — | 2 |
| Blüte/Vegetativ | 1:1:2 | 0.8–1.2 | 5.5–7.0 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Gehölzdünger | Compo | organisch-mineralisch | 80–100 g/m² | März/April | medium_feeder |
| Hornspäne | Oscorna | organisch | 50–70 g/m² | April | N-Startdüngung |
| Kompost (reif) | eigen | organisch | 3–5 L/m² | März/Oktober | Bodenverbesserung |
| Kalibetonter Dünger | ICL/Compo | mineralisch | 30–40 g/m² | August | Triebausreifung |

### 3.2 Besondere Hinweise zur Düngung

Einmalige organische Düngung im Frühjahr reicht. Keine Düngung nach August (Triebe müssen ausreifen). Im Kübel alle 3–4 Wochen Flüssigdünger (Mai–Juli).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; nur bei Trockenheit gießen; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Düngung | Organischer Dünger einarbeiten | mittel |
| Jun | Schnitt nach Blüte | Beherzt schneiden; fördert Nachblüte + nächstjährige Blüte | hoch |
| Aug | Kalibetonter Dünger | Triebausreifung | mittel |
| Nov | Winterschutz (Jungpflanzen) | Mulchen im Wurzelbereich | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien; eingerollte Blätter; Honigtau | leaf, shoot | vegetative (trocken, warm) | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste; gelbliche Punkte | leaf | vegetative (Hitze) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 7–10 | vegetative (Sommer) |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Wasserstrahl | cultural | — | Gegen Blattläuse; kräftiger Strahl | 0 | Blattläuse |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse, Spinnmilben |
| Ausreichend gießen | cultural | — | Trockenheit vermeiden | 0 | Blattläuse vorbeugend |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Ziersträucher |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Forsythie | Forsythia x intermedia | 0.8 | Ergänzende frühe Blütezeiten; ähnliche Schnittansprüche | `compatible_with` |
| Flieder | Syringa vulgaris | 0.8 | Ergänzende Blüten; ähnliche Pflege | `compatible_with` |
| Deutzie | Deutzia spp. | 0.9 | Gleiche Blütezeit; ähnliche Ansprüche | `compatible_with` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Weigela florida,"Liebliche Weigelie;Weigelie;Weigela",Caprifoliaceae,Weigela,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"China, Korea, Japan",yes,30,35,200,180,130,no,yes,false,false,medium_feeder,false,hardy,"5;6"
```

---

## Quellenverzeichnis

1. [HeimHelden — Weigelie](https://www.heimhelden.de/weigelie) — Standort, Pflege, Schädlinge
2. [Lubera — Weigelie](https://www.lubera.com/de/gartenbuch/weigelie-schneiden-und-vermehren-tipps-zu-sorten-und-bluetezeit-p3046) — Schnitt, Sorten
3. [Gartenratgeber — Weigelie](https://www.gartenratgeber.net/pflanzen/weigelie.html) — Düngen, Schnitt
4. [Gartenrat — Weigelie](https://gartenrat.de/weigelie/) — Pflege
5. [Naturadb — Weigela florida](https://www.naturadb.de/pflanzen/weigela-florida/) — Steckbrief
