# Gardenie — Gardenia jasminoides

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Care Guide](https://www.gardenia.net/guide/learn-how-to-grow-and-care-for-your-gardenia), [UK Houseplants – Gardenia](https://www.ukhouseplants.com/plants/gardenia-jasminoides), [Clemson HGIC – Gardenia](https://hgic.clemson.edu/factsheet/gardenia/), [Lubera – Gardenie](https://www.lubera.com/de/gartenbuch/gardenie-gardenia-jasminoides-pflege-ueberwintern-p3134)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Gardenia jasminoides | `species.scientific_name` |
| Volksnamen (DE/EN) | Gardenie; Cape Jasmine, Gardenia | `species.common_names` |
| Familie | Rubiaceae | `species.family` → `botanical_families.name` |
| Gattung | Gardenia | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | In Mitteleuropa reine Kübelpflanze; frostfrei überwintern bei 8–15°C; verträgt kurzzeitig Temperaturen bis ca. -5°C (Zone 8a), aber Blütenknospen erfrieren bereits bei leichtem Frost. Kalte Nächte (10–15°C) im Herbst sind für die Knospenbildung förderlich. | `species.hardiness_detail` |
| Heimat | China, Japan, Vietnam, Süd-/Ostasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 (intensiver Jasminduft) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, besonders Früchte | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Geniposid (Iridoid-Glykosid), Gardeniosid | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (nach Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 (in Natur bis 200 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–120 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Saure, humusreiche Rhododendronerde oder Azaleen-Substrat; pH 5.0–6.0 zwingend; sehr gute Drainage | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | medium |
| Knospenbildung (Frühjahr) | 30–60 | 2 | false | false | low |
| Blüte | 60–120 | 3 | false | false | low |
| Vegetativ (Sommer/Herbst) | 90–120 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | 5.0–6.0 | — | — | — | — |
| Knospenbildung | 1:2:1 | 0.8–1.2 | 5.0–6.0 | 80 | 40 | — | 3 |
| Blüte | 1:2:2 | 1.0–1.5 | 5.0–6.0 | 80 | 40 | — | 3 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 5.0–6.0 | 100 | 50 | — | 3 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Knospenbildung | time_based | — | Frühjahr, wärmere Temperaturen |
| Knospenbildung → Blüte | time_based | 30–60 Tage | Knospen sichtbar |
| Blüte → Vegetativ | time_based | 60–120 Tage | Blüten verblüht |
| Vegetativ → Winterruhe | time_based | 90–120 Tage | Herbst, kühler Standort |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Kübel)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Rhododendron-Dünger | Compo | base | 12-4-8 + Fe-EDTA | 5 ml/L | 1 | alle aktiven |
| Azaleendünger | Substral | base | 7-4-9 | 5 ml/L | 1 | blüte, vegetativ |

#### Organisch (Kübel)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Rhododendron-Langzeitdünger | Cuxin | organisch | 50 g/10L Topf | Apr–Sep | medium_feeder |
| Eisendünger (chelat) | Sequestrene | supplement | 5 g/10L Topf | Bei Chlorose | Eisenmangel |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| Jan–Feb | Winterruhe | 0.0 | — | Kein Dünger |
| Mär–Mai | Knospenbildung | 0.8–1.2 | 5.5 | Alle 2 Wochen, Eisen-Dünger |
| Jun–Sep | Blüte/Vegetativ | 1.0–1.5 | 5.5 | Alle 2 Wochen |
| Okt | Einwintern | 0.0 | — | Letzte Düngung |

### 3.3 Besondere Hinweise zur Düngung

Gardenien sind **pH-Spezialisten** — der pH muss zwingend bei 5.0–6.0 liegen. Normales Leitungswasser (pH 7+) macht Nährstoffe, besonders Eisen, unlöslich. Regenwasser, enthärtetes Wasser oder leicht angesäuertes Wasser ist Pflicht. Chlorotische Blätter (gelb mit grünen Adern) = Eisenmangel durch falschen pH. Rhododendron-Dünger mit Eisenchelat ist erste Wahl.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser ZWINGEND; pH 5.0–6.0; Regenwasser ideal | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (12–15°C), wenig gießen | mittel |
| Feb | Knospenbeobachtung | Temperatur leicht erhöhen, Knospenbildung | mittel |
| Mär | Umtopfen | Bei Bedarf; neues saures Substrat | hoch |
| Apr | Düngung | Rhododendron-Dünger alle 2 Wochen | hoch |
| Jun–Sep | Blüte | Hoch-Luftfeuchte (>60%), regelmäßig gießen | hoch |
| Okt | Rückschnitt + Einwintern | Nach Blüte, kühl stellen | hoch |
| Nov–Dez | Winterruhe | Kühl, hell, minimal gießen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Weiße Fliege | Trialeurodes vaporariorum | Weiße Fliegen, Honigtau | leaf | alle | easy |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen | stem | alle | difficult |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, Gelbfleckigkeit | leaf | alle | medium |
| Blattläuse | Aphis spp. | Deformierte Triebe | stem | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | dry_leaves, poor_airflow | 5–10 | alle |
| Anthraknose | fungal | Braune Blattränder und -flecken | high_humidity | 7–14 | alle |
| Rußtau | fungal (sekundär) | Schwarzer Belag | Honigtau von Schädlingen | 7–14 | alle |
| Chlorose | physiological | Gelbe Blätter, grüne Adern | wrong_pH, iron_deficiency | — | alle |
| Knospenfall | physiological | Knospen fallen vor dem Öffnen ab | temperature_fluctuation, dry_air, movement | — | flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Wollläuse, Spinnmilben |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Blattläuse, Weiße Fliege |
| Eisendünger | cultural | EDTA-Fe | Gießen | 0 | Chlorose |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Gardenia jasminoides |
|-----|-------------------|-------------|------------------------------|
| Stephanotis | Stephanotis floribunda | Duftblüten | Kletterpflanze, einfacher |
| Jasmin | Jasminum polyanthum | Intensiver Duft | Robuster, schneller wüchsig |
| Kaffeepflanze | Coffea arabica | Gleiche Familie (Rubiaceae) | Dekorativ, einfacher zu pflegen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Gardenia jasminoides,Gardenie;Cape Jasmine,Rubiaceae,Gardenia,perennial,day_neutral,shrub,fibrous,8a;8b;9a;9b;10a;10b;11a;11b,0.0,China Japan Südostasien,yes,10,20,120,120,—,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Gardenia.net – Care Guide](https://www.gardenia.net/guide/learn-how-to-grow-and-care-for-your-gardenia) — Vollständige Pflegeanleitung
2. [UK Houseplants – Gardenia](https://www.ukhouseplants.com/plants/gardenia-jasminoides) — Detaillierter Guide
3. [Clemson HGIC – Gardenia](https://hgic.clemson.edu/factsheet/gardenia/) — University Extension Service
4. [Lubera – Gardenie Pflege](https://www.lubera.com/de/gartenbuch/gardenie-gardenia-jasminoides-pflege-ueberwintern-p3134) — DE Kulturtipps
5. [Pflanzenfreunde – Gardenien](https://www.pflanzenfreunde.com/gardenien.htm) — Schädlinge, Krankheiten
