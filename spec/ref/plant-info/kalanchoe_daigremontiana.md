# Brutblatt — Kalanchoe daigremontiana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/kalanchoe-daigremontiana/), [Get Busy Gardening](https://getbusygardening.com/mother-of-thousands-care/), [Gardenia.net](https://www.gardenia.net/plant/kalanchoe-daigremontiana-mother-of-thousands), [Gardeningknowhow.com](https://www.gardeningknowhow.com/houseplants/kalanchoe/growing-mother-of-thousands.htm), [UK Houseplants](https://www.ukhouseplants.com/plants/mother-of-thousands)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Kalanchoe daigremontiana | `species.scientific_name` |
| Synonyme | Bryophyllum daigremontianum (älterer Name, noch in Verwendung) | — |
| Volksnamen (DE/EN) | Brutblatt, Teufelsrückgrat; Mother of Thousands, Alligator Plant, Devil's Backbone | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Kalanchoe | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9b–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 5°C Kurzzeitig; typische Zimmerpflanze in Mitteleuropa | `species.hardiness_detail` |
| Heimat | Madagaskar (trockene Regenwälder und Felsplatten) | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit — Viviparie:** Kalanchoe daigremontiana bildet an den Blatträndern kleine Tochterbrut-Pflänzchen (Bulbillen) aus, die bei der Reife abfallen und sich selbständig einwurzeln. Diese Eigenschaft (Viviparie = lebend gebärend) macht die Pflanze zu einem der effizientesten Selbstvermehrar unter den Zimmerpflanzen. In warmen Klimazonen gilt sie als invasiv.

**Toxizitäts-Warnung:** Alle Pflanzenteile enthalten Herzglykoside (Bufadienolide) — GIFTIG für Katzen, Hunde, Rinder und Menschen bei Einnahme. Herzsymptome möglich.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 1, 2, 3 (rötlich-lila Blüten; Kurztagspflanze; nach Blüte stirbt Mutterpflanze ab) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset; seed; cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Bulbillen-Vermehrung:** Die abfallenden Blattrandkindel können einfach auf feuchtes Substrat gesetzt werden. Ohne weiteres Zutun bewurzeln sie sich innerhalb von 1–2 Wochen. Extrem einfach; oft selbst-ansäend auf nahegelegenes Substrat.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile (Blätter, Stiel, Bulbillen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Bufadienolide (Bufacardenolid, Daigremontianin) — Herzglykoside | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Wichtig:** Tiere und Kleinkinder von der Pflanze fernhalten! Herzsymptome (Arrhythmie, Herzstillstand) bei Aufnahme größerer Mengen möglich.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Abgestorbene Blätter entfernen. Bulbillen (Kindel) regelmäßig abnehmen und verschenken oder entsorgen, falls kein Interesse an Ausbreitung.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (bei älteren Exemplaren durch Eigengewicht) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteen-/Sukkulentenerde; pH 6.0–7.5; sehr gute Drainage; Staunässe ist tödlich | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bulbillen-Etablierung | 14–28 | 1 | false | false | high |
| Vegetativ | 90–365 | 2 | false | false | high |
| Blüte (Kurztagsreaktion) | 30–60 | 3 | true | false | high |

**Hinweis zur Monokarpie:** Ältere Pflanzen sind monokarisch — nach der Blüte stirbt die Mutterpflanze ab. Junge Bulbillen nehmen ihre Stelle ein.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 35–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (Substrat vollständig trocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetativ | 1:2:2 | 0.4–0.8 | 6.0–7.5 | 50 | 25 |
| Blüte | 0:1:2 | 0.3–0.5 | 6.0–7.5 | 30 | 15 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kaktusdünger | Compo | Flüssigdünger | 2-6-12 | 1 ml/L alle 4 Wochen | Vegetativ |
| Sukkulentendünger granuliert | Substral | slow release | 9-12-8 | 1 Msp./2 Monate | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost (beim Umtopfen) | eigen | organisch | 10% Beimischung | Frühling |

### 3.2 Besondere Hinweise zur Düngung

Sehr genügsam — im Zweifelsfall lieber nicht düngen. Maximal einmal pro Monat während April bis September. Überdüngung führt zu weichem, hinfälligem Wuchs.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; Substrat zwischen den Gaben vollständig austrocknen lassen; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Mär | Blüte/Seneszenz | Blüte beobachten; Bulbillen sammeln; Mutterpflanze stirbt ab | mittel |
| Mär–Apr | Bulbillen einpflanzen | Gesammelten Nachwuchs einpflanzen | hoch |
| Apr–Sep | Aktive Wachstumsphase | Regelmäßig gießen; monatlich düngen | mittel |
| Okt | Abdrosseln | Gießen reduzieren; Dünger einstellen; Kurztagsphase beginnt | mittel |
| Okt–Dez | Blüteinduktion | Kurztagsperiode (max. 8–10h Licht) löst Blütenansatz aus | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winterquartier Temp min (°C) | 7 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollmasse in Blattachseln | easy |
| Blattläuse | Aphidoidea | Triebverformung, Honigtau | easy |
| Spinnmilben | Tetranychus urticae | Gelbliche Punkte, feine Gespinste | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Pythium) | Welke, schwarze Basis | Staunässe |
| Blattflecken | fungal | Braune Flecken | Feuchtigkeit auf Blättern |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | biological | Isopropylalkohol | Wattestäbchen | 0 | Wollläuse |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Blattläuse, Milben |
| Substrat erneuern | cultural | — | Kompletter Substratwechsel | 0 | Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kalanchoe blossfeldiana | Kalanchoe blossfeldiana | 0.8 | Gleiche Gattung, gleiche Pflege | `compatible_with` |
| Crassula | Crassula ovata | 0.7 | Gleiche Familie, ähnliche Pflege | `compatible_with` |
| Aloe | Aloe vera | 0.7 | Ähnliche Anforderungen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Farne | Nephrolepis exaltata | Völlig gegensätzliche Feuchtigkeitsanforderungen | severe | `incompatible_with` |
| Calathea | Goeppertia spp. | Brutblatt benötigt Trockenheit, Calathea feuchte Erde | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Mutter der Millionen | Kalanchoe delagoensis | Gleiche Gattung, ähnliche Vivipairie | Zylindrische Blätter, etwas kleinwüchsiger |
| Flammendes Kätchen | Kalanchoe blossfeldiana | Gleiche Gattung | Spektakulärere Blüte, nicht monokarpisch |
| Jadebaum | Crassula ovata | Gleiche Familie, Sukkulente | Langlebiger, keine Toxizität |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Kalanchoe daigremontiana,Brutblatt;Teufelsrückgrat;Mother of Thousands,Crassulaceae,Kalanchoe,perennial,short_day,herb,fibrous,9b;10a;10b;11a;11b,−0.1,Madagaskar,yes,3,15,90,40,yes,limited,false,true
```

---

## Quellenverzeichnis

1. [NC State Extension — Kalanchoe daigremontiana](https://plants.ces.ncsu.edu/plants/kalanchoe-daigremontiana/) — Botanische Einordnung, Toxizität
2. [Get Busy Gardening — Mother of Thousands](https://getbusygardening.com/mother-of-thousands-care/) — Pflegehinweise
3. [Gardenia.net — Kalanchoe daigremontiana](https://www.gardenia.net/plant/kalanchoe-daigremontiana-mother-of-thousands) — Kulturdaten
4. [Gardeningknowhow.com — Mother of Thousands](https://www.gardeningknowhow.com/houseplants/kalanchoe/growing-mother-of-thousands.htm) — Vermehrung
5. [UK Houseplants — Mother of Thousands](https://www.ukhouseplants.com/plants/mother-of-thousands) — Temperatur, Gießen
