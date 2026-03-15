# Brautstrauch (Madagaskarjasmin) — Stephanotis floribunda

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Balcony Garden – Stephanotis](https://thebalconygarden.co/blogs/news/caring-for-madagascar-jasmine), [Greg App – Stephanotis](https://greg.app/plant-care/stephanotis-floribunda), [Weekand – Stephanotis Care](https://www.weekand.com/home-garden/article/care-stephanotis-18054398.php), [Pflanzenfreunde – Stephanotis](https://www.pflanzenfreunde.com/stephanotis.htm)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Stephanotis floribunda | `species.scientific_name` |
| Volksnamen (DE/EN) | Brautstrauch, Madagaskarjasmin; Madagascar Jasmine, Bridal Wreath, Wax Flower | `species.common_names` |
| Familie | Apocynaceae | `species.family` → `botanical_families.name` |
| Gattung | Stephanotis | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostfrei; Temperaturen unter 12°C hemmen Wachstum dauerhaft | `species.hardiness_detail` |
| Heimat | Madagaskar | `species.native_habitat` |
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
| Blütemonate | 5, 6, 7, 8 (weiße, duftende Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Alkaloide (Milchsaft) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft kann Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
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
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–500 (Kletterpflanze) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gut drainierte, nährstoffreiche Zimmerpflanzenerde; keine Staunässe; Rankgitter oder Drahtrahmen; Topf NICHT umstellen (Knospenfall!) | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | medium |
| Knospenbildung | 30–60 | 2 | false | false | low |
| Blüte | 60–90 | 3 | false | false | low |
| Vegetativ (Sommer/Herbst) | 90–120 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.1 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Knospenbildung | 1:2:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | — | 2 |
| Blüte | 1:2:3 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Knospenbildung | time_based | — | Frühjahr, Temperaturanstieg |
| Knospenbildung → Blüte | time_based | 30–60 Tage | Knospen deutlich sichtbar — Topf NICHT mehr bewegen! |
| Blüte → Vegetativ | time_based | 60–90 Tage | Blüten verblüht |
| Vegetativ → Winterruhe | time_based | 90–120 Tage | Herbst, Temperaturabfall |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Compo | base | 4-6-8 | 5 ml/L | 1 | knospenbildung, blüte |
| Zimmerpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | — | organisch | 30 g/Topf | Frühjahr | medium_feeder |
| Langzeitdünger | Osmocote | organisch/langsam | 5 g/L Substrat | Apr–Jun | medium_feeder |

### 3.2 Besondere Hinweise zur Düngung

**Kritischer Hinweis:** Stephanotis floribunda reagiert extrem empfindlich auf Standortveränderungen — bei der Knospenbildung und während der Blüte den Topf NICHT drehen oder umstellen, da dies Knospenfall auslöst! Auch Zugluft und Temperaturschwankungen während der Blüte vermeiden. Die Überwinterung bei 12–15°C ist der Schlüssel für reichliche Blütenbildung im Folgejahr.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser bevorzugt; zimmertemperiert | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (12–15°C), wenig gießen, heller Standort | hoch |
| Feb | Knospenbeobachtung | Temperaturen erhöhen, Knospen erscheinen | mittel |
| Mär | Vorsichtige Pflege | Topf NICHT bewegen, Knospenfall vermeiden | hoch |
| Apr | Düngung | Erste Düngergabe, Licht sichern | hoch |
| Mai–Aug | Blütezeit | Regelmäßig gießen, nicht umstellen | hoch |
| Sep | Rückschnitt | Nach Blüte, Triebe um 1/3 kürzen | mittel |
| Okt | Einwintern | Kühl stellen (12–15°C) | hoch |
| Nov–Dez | Winterruhe | Minimal gießen, kein Dünger | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 12 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 16 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schildläuse | Coccus hesperidum | Braune Schuppen, klebrige Blätter | stem | alle | difficult |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Spinnmilben | Tetranychus urticae | Gespinste, gelbe Blattflecken | leaf | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Knospenfall | physiological | Knospen fallen vor dem Öffnen ab | movement, draft, temperature_change | — | flowering |
| Wurzelfäule | fungal | Welke Pflanze | overwatering | 7–14 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Cryptolaemus montrouzieri | Wollläuse, Schildläuse | 1–2/Pflanze | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Schildläuse, Spinnmilben |
| Alkohol | mechanical | Isopropanol 70% | Wattestäbchen | 0 | Schildläuse, Wollläuse |

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

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Stephanotis floribunda |
|-----|-------------------|-------------|------------------------------|
| Pink Jasmin | Jasminum polyanthum | Kletterpflanze, duftend | Robuster, einfacher zu pflegen |
| Hoya | Hoya carnosa | Gleiche Familie, Wachsblumen | Pflegeleichter, toleranter |
| Gardenie | Gardenia jasminoides | Intensiver Duft | Kein Kletterer, kompakter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Stephanotis floribunda,Brautstrauch;Madagaskarjasmin;Madagascar Jasmine,Apocynaceae,Stephanotis,perennial,short_day,vine,fibrous,10a;10b;11a;11b,0.0,Madagaskar,yes,10,20,500,200,—,yes,limited,true,true
```

---

## Quellenverzeichnis

1. [Balcony Garden – Stephanotis Care](https://thebalconygarden.co/blogs/news/caring-for-madagascar-jasmine) — Pflegeanleitung
2. [Greg App – Stephanotis floribunda](https://greg.app/plant-care/stephanotis-floribunda) — Care Data
3. [Weekand – How to Care for Stephanotis](https://www.weekand.com/home-garden/article/care-stephanotis-18054398.php) — Kulturtipps
4. [Pflanzenfreunde – Stephanotis](https://www.pflanzenfreunde.com/stephanotis.htm) — DE Anleitung
