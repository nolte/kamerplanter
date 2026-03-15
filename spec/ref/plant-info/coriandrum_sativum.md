# Koriander — Coriandrum sativum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Koriander pflanzen, COMPO Koriander, Gartenratgeber Koriander, Kiepenkerl Koriander, Fryd Koriander pflanzen

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Coriandrum sativum | `species.scientific_name` |
| Volksnamen (DE/EN) | Koriander, Korianderkraut; Coriander, Cilantro | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Coriandrum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | — (einjährig) | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt Leichtfrost bis ca. -5 °C; Aussaat ab April möglich; Herbstaussaat (September) für Überwinterung in milden Regionen; neigt bei langen Tagen und Wärme schnell zum Schossen | `species.hardiness_detail` |
| Heimat | Vorderasien, Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (keine Vorkultur; Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5, 6, 7, 8 (gestaffelt für kontinuierliche Ernte) | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9, 10 (Blätter; Samen August–Oktober) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (weiße Doldenblüten; nach Schossen) | `species.bloom_months` |

**Sukzession:** Alle 3–4 Wochen nachsäen für kontinuierliche Blatternte. Koriander schosst schnell bei Wärme und langen Tagen — Schossen verringert Blattqualität (bitterer, weniger aromatisch).

**Nutzung:** Blätter = Frischkraut (Koriandergrün/Cilantro); Samen = Gewürz (Koriandersamen). Verschiedene Geschmacksprofile.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Koriander mag keine Verpflanzung (Pfahlwurzel). IMMER direkt säen, nicht vorziehen. Samenbeerenpaare (Doppelfrüchte) vor Aussaat auftrennen für bessere Keimung.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine (ätherische Öle; Linalool, Decyl-Aldehyd) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

**Hinweis:** Kontaktallergie möglich (Apiaceae-Querreaktion). Licht-Sensibilisierung durch Furanocumarine bei empfindlichen Personen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Keine Rückschnittmaßnahmen — Ernte durch Blätterernten (äußere Blätter). Bei Schossen: Blütenstand abschneiden verzögert Schossen etwas. Für Samenernte: Schossen erwünscht.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, durchlässige Kräutererde; pH 6,0–7,0; kein Staunässe; dünn säen | — |

**Für Blatternte:** Halbschattiger Standort bevorzugen (verzögert Schossen). **Für Samenernte:** Vollsonniger Standort.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Jungpflanze | 14–21 | 2 | false | false | low |
| Vegetatives Wachstum (Ernte) | 30–60 | 3 | false | true | medium |
| Schossen / Blüte | 14–21 | 4 | false | true (Samen) | high |
| Samenreife | 21–35 | 5 | true | true (Samen) | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum (Blatternte)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 (halbschattig bis Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (kurze Tage verzögern Schossen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — |
| Vegetativ / Ernte | 1:0:1 | 0.4–0.8 | 6.0–7.0 | 60 | 30 | — | 1 |
| Blüte / Samen | 0:1:1 | 0.4–0.8 | 6.0–7.0 | 40 | 20 | — | 1 |

**Hinweis:** Zu viel Dünger verringert das Aroma! Koriander braucht mageren Boden für bestes Aroma. Kompost vor der Aussaat reicht völlig.

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | organisch | 1–2 L/m² | Vor Aussaat | Startdüngung |
| Kräuterdünger (niedrig dosiert) | Compo | organisch-mineralisch | 1/4 Empfehldosis | 1x im Monat | Topfkulturen |

### 3.2 Besondere Hinweise zur Düngung

Koriander im Beet braucht keinen extra Dünger — Kompost vor der Aussaat reicht. Im Topf monatlich sehr niedrig dosierter Kräuterdünger. Zu viel Stickstoff = kräftiger Wuchs, aber deutlich weniger Aroma.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig feucht; kein Staunässe; kein Laub benetzen bei Mehltaugefahr | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig; nicht umpflanzen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr–Mai | Erste Aussaat | Ab Mitte April (Direktsaat); ab Mitte Mai sicher | mittel |
| Apr–Aug | Nachsaaten | Alle 3–4 Wochen; gestaffelte Ernte | mittel |
| Laufend | Ernte | Äußere Blätter; Triebspitzen | hoch |
| Bei Schossen | Entscheidung | Blütenstand entfernen (Blätter) ODER stehen lassen (Samen) | mittel |
| Aug–Sep | Samenernte | Wenn Hüllen braun; Stiele trocknen lassen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schwarze Bohnenlaus | Aphis fabae | Kolonien an Triebspitzen; Honigtau | shoot | vegetative | easy |
| Weichwanzen | Lygus spp. | Saugschäden; Blattdeformation | leaf, shoot | vegetative | medium |
| Grüne Zikade | Empoasca spp. | Stippling (Punktfraß) auf Blättern | leaf | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trocken + warm; zu eng | 5–10 | vegetative |
| Falscher Mehltau (Doldenwelke) | fungal-like | Gelblich-braune Blätter; Dolden welken | Regenjahre; Feuchtigkeit | 7–14 | vegetative |
| Gelbwelke | bacterial (Pseudomonas) | Gelbe Blätter; Welken | Staunässe | 5–10 | alle |

**Hauptschutz:** Ausreichend Abstand (25–30 cm); gute Luftzirkulation; nicht zu viel gießen.

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Ausreichend Pflanzabstand | cultural | — | 25–30 cm Reihenabstand | 0 | Mehltau, Faulnis |
| Neemöl | biological | Azadirachtin | 0.5%; abends; Wartezeit bis Ernte! | 3 | Blattläuse |
| Insektenseife | biological | Kaliumsalze | Sprühen | 0 | Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Kräuter / Apiaceae |
| Empfohlene Vorfrucht | Starkzehrer (Tomate, Kohl); Mittelzehrer |
| Empfohlene Nachfrucht | beliebig |
| Anbaupause (Jahre) | 3–4 Jahre zwischen Apiaceae (Karotte, Petersilie, Fenchel) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Gegenseitige Nützlingsförderung; Thrips-Abwehr | `compatible_with` |
| Kohl-Arten | Brassica oleracea | 0.8 | Schutz vor Kohlweißling | `compatible_with` |
| Thymian | Thymus vulgaris | 0.7 | Aromatische Abschirmung gegen Schädlinge | `compatible_with` |
| Oregano | Origanum vulgare | 0.7 | Gleiche Standortansprüche; Aromatische Synergie | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Alelopathische Hemmung; schlechte Nachbarschaft | moderate | `incompatible_with` |
| Liebstöckel | Levisticum officinale | Apiaceae-Familie; teilen Krankheiten/Schädlinge | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Hemmende Wirkung auf viele Kräuter | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Apiaceae | `shares_pest_risk` | Doldenwelke, Möhrenfliege (Psila rosae) | `shares_pest_risk` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months
Coriandrum sativum,"Koriander;Korianderkraut;Coriander;Cilantro",Apiaceae,Coriandrum,annual,long_day,herb,taproot,,0.1,"Vorderasien, Mittelmeerraum",yes,3,20,45,25,27,yes,yes,false,false,light_feeder,false,half_hardy,"4;5;6;7;8","5;6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Plantura — Koriander pflanzen](https://www.plantura.garden/kraeuter/koriander/koriander-pflanzen) — Standort, Aussaat
2. [COMPO — Koriander](https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/koriander) — Pflege, Düngung
3. [Gartenratgeber — Koriander](https://www.gartenratgeber.net/pflanzen/koriander.html) — Anbau, Pflege
4. [Kiepenkerl — Koriander Kulturanleitung](https://www.kiepenkerl.de/kulturanleitungen/koriander/) — Aussaatdaten
5. [Fryd — Koriander pflanzen](https://fryd.app/magazin/koriander-pflanzen) — Mischkultur
