# Studentenblume — Tagetes patula

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** NABU Tagetes, Gartenjournal.net Tagetes, Compo Tagetes, Insektensaatgut.de Tagetes

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tagetes patula | `species.scientific_name` |
| Volksnamen (DE/EN) | Studentenblume, Aufrechte Tagetes, Französische Tagetes; French Marigold | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Tagetes | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; nach den Eisheiligen auspflanzen; stirbt bei ersten Frost | `species.hardiness_detail` |
| Heimat | Mexiko, Guatemala | `species.native_habitat` |
| Allelopathie-Score | 0.4 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Vorkultur März/April) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Blüten für Insekten; als Nematodenbekämpfung mind. 3 Monate stehen lassen) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, flowers | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | thiophene_derivatives, essential_oils (Thiophen-Derivate und aetherische Oele; ASPCA: Tagetes als toxisch fuer Hunde und Katzen gelistet) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (kutane Irritation, milde Gastroenteritis bei Verschlucken) | `species.toxicity.severity` |
| Kontaktallergen | true (ätherische Öle können bei Korbblütler-Allergie reagieren) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Korbblütler-Allergie) | `species.allergen_info.pollen_allergen` |

<!-- AB-015: Korrektur gemaess ASPCA Animal Poison Control -- Tagetes patula ist fuer Katzen und Hunde mild toxisch (Thiophen-Derivate, aetherische Oele). Symptome: Hautirritation, leichte Magen-Darm-Beschwerden. Fuer Menschen/Kinder unbedenklich (Blueten essbar). -->

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Deadheading fördert Nachblüte; nach 3 Monaten einarbeiten) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–35 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–25 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Erde; pH 5,5–7,0; gut drainiert | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–7 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 21–35 | 3 | false | false | high |
| Blüte (Dauerflorenz) | 90–120 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (quantitative Kurztagsreaktion: Kurztag beschleunigt Bluete, blueht aber auch bei Langtag) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Tagetes braucht kaum Dünger. Auf mageren Böden blüht sie reicher. Auf überdüngten Böden bildet sie viel Laub und wenige Blüten. Die Nematoden-Bekämpfungswirkung entfaltet sich durch Wurzelausscheidungen (Thiophene) — diese werden durch mageren Boden und Stress gefördert. Für effektive Nematoden-Bekämpfung: Dicht pflanzen und mind. 8–12 Wochen stehen lassen; dann EINARBEITEN (nicht abräumen).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Moderat feucht; Blätter beim Gießen trocken halten | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (kein Dünger) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Vorkultur | Aussaat bei 20–22 °C im Haus | mittel |
| Mai (nach 15.) | Auspflanzen | Nach Eisheiligen; frostfrei | hoch |
| Jun–Sep | Deadheading | Verblühte Blüten entfernen; fördert Nachblüte | mittel |
| Jun–Aug | Nematoden-Einsatz | Für Nematoden-Bekämpfung dicht und flächig pflanzen | hoch |
| Aug–Sep | Einarbeitung | Als Gründüngung/Nematodenpflanze einarbeiten | mittel |
| Okt | Abräumen | Vor Frost abmähen; kompostieren | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste (bei Trockenheit) | leaf | flowering (Hitze) | medium |
| Blattläuse | div. Aphiidae | Kolonien (selten; Tagetes-Duft schützt) | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel | fungal (Botrytis cinerea) | Schimmel an Blüten | Feuchtigkeit, enge Bepflanzung | 3–7 | flowering |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit+Wärme | 5–10 | vegetative |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Begleit- und Gründüngungspflanze |
| Empfohlene Vorfrucht | Nematoden-befallene Kulturen |
| Empfohlene Nachfrucht | Alle Hauptkulturen (Nematoden-Bekämpfung wirkt nach) |
| Anbaupause (Jahre) | keine |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Weiße Fliege-Abwehr; Bestäuber-Anlockung | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Nematoden-Abwehr; Bestäuber | `compatible_with` |
| Rose | Rosa spp. | 0.9 | Klassischer Begleiter; Schädlingsabwehr | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Nematoden-Abwehr | `compatible_with` |
| Kürbis | Cucurbita maxima | 0.8 | Nematoden-Schutz | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Bohne | Phaseolus vulgaris | Tagetes hemmt manche Bohnenarten | mild | `incompatible_with` |
| Kohl | Brassica oleracea | Schlechte Verträglichkeit | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tagetes patula |
|-----|-------------------|-------------|----------------------------------|
| Afrikanische Tagetes | Tagetes erecta | Gleiche Gattung | Größere Blüten; stärker durchwurzelnd gegen Nematoden |
| Ringelblume | Calendula officinalis | Bienenweide | Nicht in Asteraceae-Allergie-Fällen; andere Wirkung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,bloom_months
Tagetes patula,"Studentenblume;Aufrechte Tagetes;Französische Tagetes;French Marigold",Asteraceae,Tagetes,annual,day_neutral,herb,fibrous,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b",0.4,"Mexiko, Guatemala",yes,7,20,40,35,22,limited,yes,false,false,light_feeder,tender,"5;6","6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [NABU Tagetes](https://www.nabu.de/tiere-und-pflanzen/pflanzen/pflanzenportraets/zierpflanzen/04042.html) — Biologie, Nutzen
2. [Tagetes Nematoden — Gartenjournal.net](https://www.gartenjournal.net/tagetes-nematoden) — Nematoden-Bekämpfung
3. [Compo Tagetes](https://www.compo.de/ratgeber/pflanzen/gartenpflanzen/tagetes) — Pflege, Aussaat
4. [Kraut&Rüben Tagetes](https://www.krautundrueben.de/studentenblumen-tagetes-schuetzt-gemuese-vor-schaedlingen-201) — Mischkultur-Praxis
