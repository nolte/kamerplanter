# Eselsschwanz — Sedum morganianum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/sedum-morganianum/), [JoyUsGarden](https://www.joyusgarden.com/burros-tail-care/), [World of Succulents](https://worldofsucculents.com/sedum-morganianum-donkeys-tail/), [Gardenia.net](https://www.gardenia.net/plant/sedum-morganianum), [Planet Desert](https://planetdesert.com/blogs/news/donkeys-tail-plant-sedum-morganianum-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Sedum morganianum | `species.scientific_name` |
| Volksnamen (DE/EN) | Eselsschwanz; Donkey's Tail, Burro's Tail, Lamb's Tail | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Sedum | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9b–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; Mindesttemperatur 7°C; in Zone 9b kurze Kälteperioden möglich | `species.hardiness_detail` |
| Heimat | Mexiko (Veracruz, Oaxaca), Honduras | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (rosa bis rote Blüten; selten in Zimmerhaltung) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem; cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Stecklings-Methode:** Triebstecklinge (5–10 cm) von der Triebspitze abschneiden. Anschnitt 2–7 Tage an der Luft trocknen lassen (kallieren) — dieser Schritt ist bei Sedum kritisch. Danach in trockenes Kakteen-/Sukkulentensubstrat stecken, erst nach 7–10 Tagen leicht anfeuchten. Bei 20–25°C und hell-indirektem Licht bewurzelt in 3–4 Wochen.

**Blattsteckling:** Einzelne Blättchen vorsichtig (mit Drehbewegung ohne Abreißen der Blattbasis) abnehmen. Auf trockenes Substrat legen, nicht eingraben. Bewurzelung und Bildung von Rosettenkindeln in 4–8 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein eigentlicher Rückschnitt. Beschädigte oder zu lange Triebe können jederzeit eingekürzt werden. Abgefallene Blättchen sind unvermeidlich und können zur Vermehrung genutzt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–30 (hängend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 (hängende Triebe bis 90 cm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteen-/Sukkulentenerde mit zusätzlich 30% Perlit; pH 6.0–7.0; exzellente Drainage obligatorisch | — |

**Gefäß-Empfehlung:** Hängeampeln oder hohe Töpfe ideal, damit die langen Triebe herabhängen können. Terrakotta-Töpfe fördern schnellere Substrataustrocknung (positiv für Sedum).

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung | 21–42 | 1 | false | false | medium |
| Vegetativ | 90–365 | 2 | false | false | high |
| Blüte (selten indoor) | 30–60 | 3 | false | true | high |
| Winterruhe | 60–90 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–55 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 (Substrat vollständig austrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (durchdringend gießen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 7–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–45 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–45 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–2.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–30 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Bewurzelung | 0:0:0 | 0.0 | 6.0–7.0 | — | — |
| Vegetativ | 1:2:2 | 0.4–0.8 | 6.0–7.0 | 50 | 30 |
| Blüte | 0:1:1 | 0.3–0.6 | 6.0–7.0 | 40 | 20 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Bewurzelung → Vegetativ | time_based | 21–42 Tage; Neue Triebe sichtbar |
| Vegetativ → Winterruhe | seasonal | Oktober; Temperatur <15°C, Gießen reduzieren |
| Winterruhe → Vegetativ | seasonal | März; Temperatur stabil >18°C |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Substral Osmocote | Slow Release | 9-12-8 | 1 Messlöffel/2 Monate | Vegetativ |
| Kaktusdünger flüssig | COMPO | Flüssigdünger | 4-8-12 | 1 ml/L alle 4 Wochen | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee (sehr verdünnt) | eigen | organisch | 1 ml/L alle 6 Wochen | Frühling–Sommer |

### 3.2 Besondere Hinweise zur Düngung

**Weniger ist mehr:** Sedum morganianum benötigt in Zimmerkultur sehr wenig Dünger. Maximal 2–3 Mal pro Saison leicht düngen (Frühling bis Ende Sommer). Überdüngung führt zu weichem, anfälligem Wachstum und Blattabfall.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 12 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser geeignet; Substrat muss vollständig austrocknen zwischen den Gaben; Staunässe ist tödlich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Fast kein Wasser, kein Dünger, kühler Standort (10–15°C) | niedrig |
| Mär | Aufweckphase | Gießen langsam wieder aufnehmen; ersten Dünger | mittel |
| Apr–Sep | Aktive Wachstumsphase | Regelmäßig gießen, monatlich düngen; Stecklinge nehmen | hoch |
| Okt | Abdrosseln | Gießintervall verlängern, Düngen einstellen | mittel |
| Nov–Dez | Winterruhe einleiten | Kühleren Standort; minimales Gießen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (Zimmer/kühler Raum) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | none | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 7 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollknäuel in Blattachseln | stem, leaf | easy |
| Wurzelmilben | Rhizoglyphus echinopus | Substrat verkrustet, Wachstumsstillstand | root | difficult |
| Blattläuse | Aphidoidea | Klebrige Absonderungen, deformierte Triebe | stem, leaf | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Pythium) | Weiche, braune Basis; Triebwelke | Staunässe, zu häufiges Gießen |
| Blattabfall | physiologisch | Blätter fallen bei Berührung ab | Erschütterung, Zugluft, Wassermangel |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | biological | Isopropylalkohol | Wattestäbchen auf Wollläuse | 0 | Wollläuse |
| Neemöl | biological | Azadirachtin | Gießen in Substrat 0.3% | 3 | Wurzelmilben |
| Schnittling-Rettung | cultural | — | Triebspitzen abschneiden, neu bewurzeln bei Fäule | 0 | Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Echeveria | Echeveria elegans | 0.9 | Gleiche Familie, identische Pflegebedingungen | `compatible_with` |
| Crassula | Crassula ovata | 0.8 | Gleiche Fam., ähnlicher Wasseranspruch | `compatible_with` |
| Haworthia | Haworthiopsis fasciata | 0.7 | Sukkulente, ähnliche Pflege | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Farne | Nephrolepis exaltata | Farne benötigen hohe Luftfeuchtigkeit | severe | `incompatible_with` |
| Calathea | Goeppertia spp. | Vollkommen gegensätzliche Anforderungen | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kleiner Eselsschwanz | Sedum burrito | Sehr ähnlich | Kürzere, kompaktere Blätter; stabiler |
| Perlenschnur | Curio rowleyanus | Ähnliche hängende Form | Spektakulärere Blattform |
| Gummipflanze-Sukkulente | Ceropegia woodii | Hängend, Sukkulente | Ebenfalls extrem pflegeleicht |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Sedum morganianum,Eselsschwanz;Donkey's Tail;Burro's Tail,Crassulaceae,Sedum,perennial,day_neutral,vine,fibrous,9b;10a;10b;11a;11b;12a;12b,0.0,"Mexiko, Honduras",yes,3,12,30,90,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [NC State Extension — Sedum morganianum](https://plants.ces.ncsu.edu/plants/sedum-morganianum/) — Botanische Einordnung
2. [JoyUsGarden — Burro's Tail Care](https://www.joyusgarden.com/burros-tail-care/) — Pflegehinweise
3. [World of Succulents — Sedum morganianum](https://worldofsucculents.com/sedum-morganianum-donkeys-tail/) — Allgemeine Kulturdaten
4. [Gardenia.net — Sedum morganianum](https://www.gardenia.net/plant/sedum-morganianum) — USDA Zone, Temperatur
5. [Planet Desert — Donkey's Tail Care](https://planetdesert.com/blogs/news/donkeys-tail-plant-sedum-morganianum-care) — Vermehrung, Schädlinge
