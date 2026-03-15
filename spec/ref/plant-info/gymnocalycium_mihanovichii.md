# Mondkaktus — Gymnocalycium mihanovichii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/gymnocalycium-mihanovichii/), [Gardenia.net](https://www.gardenia.net/plant/gymnocalycium-mihanovichii-moon-cactus-grow-care-guide), [Wikipedia — Gymnocalycium](https://en.wikipedia.org/wiki/Gymnocalycium_mihanovichii), [Succulents and Sunshine](https://www.succulentsandsunshine.com/types-of-succulents/gymnocalycium-mihanovichii-moon-cactus/), [MasterClass Moon Cactus Care](https://www.masterclass.com/articles/moon-cactus-care-guide)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Gymnocalycium mihanovichii | `species.scientific_name` |
| Volksnamen (DE/EN) | Mondkaktus, Bunter Pfropfkaktus; Moon Cactus, Ruby Ball Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Gymnocalycium | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 10°C; Zimmerpflanze | `species.hardiness_detail` |
| Heimat | Paraguay, Bolivien, Nordargentinien (Unterholz-Kaktus; wächst natürlich im Schatten größerer Pflanzen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit — Veredelung:** Der im Handel erhältliche "Mondkaktus" ist ein veredelter Kaktus — ein Gymnocalycium mihanovichii 'Hibotan' (chlorophyll-freie Mutante in Rot, Orange, Gelb oder Violett) wird auf einen grünen Pfropfunterlage-Kaktus (häufig Hylocereus undatus = Drachenfrucht-Kaktus) aufgepfropft. Der bunte Scion ist vollständig von der Unterlage abhängig (kein Chlorophyll). Lebensdauer: 3–5 Jahre, da die Unterlage (Hylocereus) oft schneller wächst als der Scion.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 4, 5, 6 (rosa bis weiße Blüten der Unterlage oder Scion) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | grafting; offset | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Vermehrung:** Die bunte Hibotan-Mutante ist ohne Pfropfunterlage nicht lebensfähig. Pfropfen erfordert sterile Bedingungen, scharfes Messer und passendes Trägermaterial (Hylocereus-Unterlage). Manche Exemplare bilden Kindel, die ebenfalls gepfropft werden können. Heimvermehrung für den normalen Hobbybereich schwierig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine; Stacheln können zu mechanischen Verletzungen führen | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Bei zu schnellem Wachstum der Unterlage kann der Scion neu gepfropft werden (Repfropfen).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.3–1 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–15 (Gesamthöhe inkl. Pfropfkaktus) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 5–10 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Handelsübliche Kakteenerde; pH 6.0–7.0; exzellente Drainage obligatorisch; nie Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung (nach Kauf) | 14–28 | 1 | false | false | medium |
| Vegetativ | 90–365 | 2 | false | false | high |
| Blüte | 14–28 | 3 | false | true | high |
| Winterruhe | 60–90 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 (Substrat vollständig trocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 20–40 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.5–3.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–30 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 10–30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetativ | 0:1:1 | 0.3–0.6 | 6.0–7.0 | 40 | 20 |
| Blüte | 0:1:2 | 0.3–0.5 | 6.0–7.0 | 30 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kaktusdünger | Compo | Flüssigdünger | 2-6-12 | 1 ml/L alle 4 Wochen | Vegetativ |
| Kakteendünger granuliert | Substral | slow release | 5-10-18 | 1 Msp./Monat | Vegetativ |

### 3.2 Besondere Hinweise zur Düngung

Sehr sparsam düngen — maximal einmal pro Monat während der Wachstumsphase (April bis September). Im Winter überhaupt kein Dünger. Überdüngung führt zum Platzen der Pfropfnaht oder zu übermäßigem Wachstum der Unterlage (die dann den Scion überwächst).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 12 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; Substrat zwischen den Gaben vollständig austrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Kein Wasser (fast); kühler, heller Standort | niedrig |
| Mär | Aufwecken | Erstmals leicht wässern; Standort prüfen | mittel |
| Apr–Sep | Aktive Phase | Alle 10–14 Tage gießen; einmal/Monat düngen | mittel |
| Okt | Abdrosseln | Gießen einstellen; Winterstandort vorbereiten | mittel |
| Nov–Dez | Winterruhe | Kühler (10–15°C), hell; minimal wässern | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollmasse an Pfropfnaht und Areolen | medium |
| Wurzelmilben | Rhizoglyphus echinopus | Wachstumsstillstand, Substrat verkrustet | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Fäule Pfropfnaht | fungal/bakteriell | Schwarze, eingesunkene Stelle an Naht | Staunässe, Verletzungen |
| Wurzelfäule | fungal | Weiche Unterlage, Welke | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol | mechanical | Isopropylalkohol | Wattestäbchen | 0 | Wollläuse |
| Stumpf-Abtrennen | cultural | — | Faulige Stellen steril abschneiden; Holzkohle | 0 | Fäule |
| Substrat erneuern | cultural | — | Topf komplett neu | 0 | Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mammillaria | Mammillaria spp. | 0.8 | Gleiche Familie, gleiche Pflege | `compatible_with` |
| Opuntia | Opuntia microdasys | 0.7 | Gleiche Familie | `compatible_with` |
| Echeveria | Echeveria elegans | 0.7 | Sukkulente, ähnliche Pflege | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Gymnocalycium (grün) | Gymnocalycium mihanovichii | Die Wildform ist robust und chlorophyllhaltig | Ohne Pfropfung lebensfähig; langlebiger |
| Stachelloser Kaktus | Astrophytum myriostigma | Ähnlich klein, dekorativ | Kein Pfropfen nötig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Gymnocalycium mihanovichii,Mondkaktus;Bunter Pfropfkaktus;Moon Cactus,Cactaceae,Gymnocalycium,perennial,day_neutral,herb,fibrous,10a;10b;11a;11b;12a;12b,0.0,"Paraguay, Bolivien, Argentinien",yes,0.5,8,15,10,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [NC State Extension — Gymnocalycium mihanovichii](https://plants.ces.ncsu.edu/plants/gymnocalycium-mihanovichii/) — Botanische Einordnung
2. [Gardenia.net — Moon Cactus](https://www.gardenia.net/plant/gymnocalycium-mihanovichii-moon-cactus-grow-care-guide) — Kulturdaten
3. [Wikipedia — Gymnocalycium mihanovichii](https://en.wikipedia.org/wiki/Gymnocalycium_mihanovichii) — Taxonomie, Pfropfung
4. [Succulents and Sunshine — Moon Cactus](https://www.succulentsandsunshine.com/types-of-succulents/gymnocalycium-mihanovichii-moon-cactus/) — Pflegehinweise
5. [MasterClass — Moon Cactus Care Guide](https://www.masterclass.com/articles/moon-cactus-care-guide) — Vermehrung, Schädlinge
