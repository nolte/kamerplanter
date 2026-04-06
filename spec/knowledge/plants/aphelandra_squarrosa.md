# Zebrapflanze (Glanzkölbchen) — Aphelandra squarrosa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [PLNTS.com – Aphelandra](https://plnts.com/de/care/houseplants-family/aphelandra), [Feey – Zebrapflanze](https://feey.ch/pages/zebrapflanze), [Plant Circle – Aphelandra](https://plantcircle.com/de-eu/blogs/plant-care-tips/aphelandra-care-tips), [Pflanzenfreunde – Aphelandra](https://www.pflanzenfreunde.com/aphelandra-glanzkoelbchen.htm)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aphelandra squarrosa | `species.scientific_name` |
| Volksnamen (DE/EN) | Zebrapflanze, Glanzkölbchen; Zebra Plant | `species.common_names` |
| Familie | Acanthaceae | `species.family` → `botanical_families.name` |
| Gattung | Aphelandra | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 11a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Ausschließlich als Zimmerpflanze; Temperaturen unter 13°C vermeiden | `species.hardiness_detail` |
| Heimat | Brasilien (Atlantischer Regenwald) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (gelbe Blütenähre, nach guter Pflege) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | nicht bekannt toxisch | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10 (nach Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 (in Natur bis 180 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut drainierte Zimmerpflanzenerde; hohe Luftfeuchtigkeit essenziell; kalkfreies Wasser verwenden | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 21–42 | 1 | false | false | low |
| Vegetativ | 150–240 | 2 | false | false | low |
| Blüte | 30–60 | 3 | false | false | medium |
| Ruhephase | 60–90 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | max. 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 1:1:1 | 0.5–0.8 | 6.0–6.5 | 80 | 40 | — | 1 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 |
| Blüte | 1:2:2 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 |
| Ruhephase | 0:0:0 | 0.0 | — | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 21–42 Tage | Neue Blätter |
| Vegetativ → Blüte | time_based | 150–240 Tage | Kurztagperiode Herbst |
| Blüte → Ruhephase | time_based | 30–60 Tage | Nach Verblühen |
| Ruhephase → Vegetativ | time_based | 60–90 Tage | Frühjahrsaustrieb |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Zimmerpflanzendünger | Compo | base | 7-4-7 | 5 ml/L | 1 | vegetativ, blüte |
| Blühpflanzendünger | Substral | base | 4-6-8 | 5 ml/L | 1 | blüte |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Pflanzendünger organisch | Biobizz Top Max | organisch | 2 ml/L | Apr–Sep | medium_feeder |
| Langzeitdünger | Osmocote | organisch/langsam | 3 g/L Substrat | Apr–Jun | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–4 | Etablierung | 0.5–0.8 | 6.2 | 2.5 | Hälfte der Normaldosis |
| 5–26 | Vegetativ | 1.0–1.5 | 6.2 | 5 | Alle 4–6 Wochen |
| 27–34 | Blüte | 1.0–1.5 | 6.2 | 5 | Phosphorlastig |
| Nov–Feb | Ruhephase | 0.0 | — | — | Kein Dünger |

### 3.3 Besondere Hinweise zur Düngung

Aphelandra ist empfindlich gegen Überdüngung. Kalkarmes oder weiches Wasser ist wichtig — Kalk verklebt die feinen Wurzeln und hemmt die Nährstoffaufnahme. Hohe Luftfeuchtigkeit (>60%) ist für die Gesundheit der Pflanze wichtiger als die Düngung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser zwingend; weiches Wasser oder Regenwasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Ruhephase | Warm halten (>18°C), wenig gießen | mittel |
| Mär | Umtopfen | Frisches Substrat; Stecklinge nehmen | hoch |
| Apr | Düngung beginnen | Schwache Düngergabe | mittel |
| Mai–Sep | Wachstum | Regelmäßig gießen, hohe Luftfeuchte sichern | hoch |
| Aug–Sep | Blüte | Blütenähre erscheint — Highlight der Pflanze | niedrig |
| Okt | Rückschnitt | Nach der Blüte zurückschneiden | mittel |
| Nov–Dez | Winterruhe | Warm, hell, wenig gießen, nicht düngen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbe Punkte auf Blättern | leaf | alle | medium |
| Blattläuse | Aphis spp. | Deformierte Triebspitzen | stem | vegetative | easy |
| Wollläuse | Pseudococcus spp. | Weißes Gespinst | stem, leaf | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Welke Blätter | overwatering | 7–14 | alle |
| Blattflecken | fungal | Gelblich-braune Flecken | overwatering, waterlogging | 7–14 | alle |
| Grauschimmel | fungal (Botrytis) | Grauer Belag | high_humidity + poor_airflow | 3–7 | flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Aphidius colemani | Blattläuse | 5–10 | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Spinnmilben, Wollläuse |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Blattläuse, Spinnmilben |

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

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Aphelandra squarrosa |
|-----|-------------------|-------------|------------------------------|
| Calathea | Goeppertia spp. | Markante Blattzeichnung | Einfacher in der Pflege |
| Fittonia | Fittonia albivenis | Auffällige Blattadern | Kleiner, pflegeleichter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Aphelandra squarrosa,Zebrapflanze;Glanzkölbchen;Zebra Plant,Acanthaceae,Aphelandra,perennial,short_day,shrub,fibrous,11a;11b;12a;12b,0.0,Brasilien Atlantischer Regenwald,yes,7,15,60,50,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [PLNTS.com – Aphelandra Pflege](https://plnts.com/de/care/houseplants-family/aphelandra) — Pflegetipps, Toxizität
2. [Feey – Zebrapflanze](https://feey.ch/pages/zebrapflanze) — Steckbrief
3. [Plant Circle – Aphelandra Care Tips](https://plantcircle.com/de-eu/blogs/plant-care-tips/aphelandra-care-tips) — Detaillierte Pflege
4. [Pflanzenfreunde – Aphelandra](https://www.pflanzenfreunde.com/aphelandra-glanzkoelbchen.htm) — Botanik, Kulturtipps
5. [Living at Home – Glanzkölbchen](https://www.livingathome.de/balkon-garten/blumen-im-haus/12778-rtkl-aphelandra-squarrosa-glanzkoelbchen) — Porträt
