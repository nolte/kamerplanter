# Brokkoli — Brassica oleracea var. italica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Brokkoli, Compo Brokkoli, Meine-Ernte Brokkoli, Hortipendium Brokkoli Pflanzenschutz

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. italica | `species.scientific_name` |
| Volksnamen (DE/EN) | Brokkoli, Broccoli; Broccoli, Calabrese | `species.common_names` |
| Familie | Brassicaceae | `species.family` → `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt leichte Fröste bis -5°C; Herbstbrokkoli winterhart bis -8°C; Jungpflanzen frostempfindlich | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Kleinasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkultur März–April; Auspflanzen ab Mai) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (Sommerbrokkoli); 6, 7 (Herbstbrokkoli) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (Sommerbrokkoli); 9, 10, 11 (Herbstbrokkoli) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 (bei Vernachlässigung schießt die Pflanze durch) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (Glucosinolate nur in großen Mengen problematisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Seitentriebe bilden sich nach Hauptkopf-Ernte für Nachernten) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8, 9, 10 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche Gartenerde mit Kompost; pH 6,0–7,0; gut wasserspeichernd | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 4–7 | 1 | false | false | medium |
| Sämling | 21–35 | 2 | false | false | low |
| Vegetativ | 28–42 | 3 | false | false | medium |
| Kopfbildung | 14–28 | 4 | false | true | medium |
| Reife/Nachernten | 21–42 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–5 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kopfbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.1 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 2:1:1 | 0.6–0.8 | 6.0–6.5 | 100 | 40 | — | 2 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 6.0–6.5 | 150 | 60 | — | 3 |
| Kopfbildung | 2:2:3 | 1.4–2.0 | 6.0–6.5 | 150 | 60 | — | 2 |
| Reife | 1:2:3 | 1.0–1.5 | 6.0–6.5 | 100 | 40 | — | 1 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung → Sämling | time_based | 5–7 Tage | Keimblätter sichtbar |
| Sämling → Vegetativ | time_based | 21–35 Tage | 4–6 echte Blätter; Pikieren/Auspflanzen |
| Vegetativ → Kopfbildung | event_based | — | Erster Kopfansatz sichtbar |
| Kopfbildung → Reife | event_based | — | Kopf kompakt, Knospen noch geschlossen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna/Compo | organisch-N | 80–120 g/m² | Pflanzung + 4 Wochen danach | heavy_feeder |
| Bio-Kohlkraft | Compo Sana | organisch | 100–150 g/m² | Frühjahr | Kohlgemüse |
| Kompost | eigen | organisch | 5–8 L/m² | Herbst/Frühjahr | alle |
| Vinasse-Flüssigdünger | Oscorna Animalin | organisch-flüssig | 30 ml/10 L Gießwasser | Vegetativ | heavy_feeder |

#### Mineralisch (bei Mangel)

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Blaukorn | Compo | mineralisch | 12-12-17+2 | 1 | Vegetativ |
| Kali-Magnesia (Patentkali) | K+S | mineralisch-K+Mg | 0-0-30+10 Mg | 1 | Kopfbildung |
| Kalkstickstoff | Perlka | mineralisch-N | 20-0-0 | 1 | Bodenvor. |

### 3.2 Düngungsplan

| Woche | Phase | Maßnahme | Produkt | Menge | Hinweise |
|-------|-------|----------|---------|-------|----------|
| 0 | Pflanzung | Grunddüngung | Kompost + Hornspäne | 6 L/m² + 100 g/m² | Einarbeiten |
| 4–5 | Vegetativ | Nachdüngung | Hornspäne oder Vinasse | 80 g/m² oder 30 ml/10L | Stickstoff-Schub |
| 8–10 | Kopfbildung | Kaliumgabe | Patentkali | 40 g/m² | Kaliumbedarf hoch |

### 3.3 Besondere Hinweise zur Düngung

Brokkoli ist Starkzehrer mit hohem N-Bedarf. Bei Stickstoffmangel: gelbe Blätter ab unten; bei zu viel N: übermäßiges Blattwachstum, lockere Köpfe. Bor-Mangel führt zu Hohlstiel — 1–2 g Borax/m² kann helfen. Kalkgabe bei saurem Boden wichtig: Kohlhernie (Plasmodiophora brassicae) tritt bevorzugt bei pH < 6,5 auf. Kalk auf 7,0–7,5 anheben.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig feucht; kein Benetzen der Köpfe (Fäulnis); Bodenfeuchte halten | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5, 6, 7, 8, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Vorkultur | Aussaat bei 15–18°C; Pikieren nach 14 Tagen | hoch |
| Mai (nach 15.) | Auspflanzen | Nach Eisheiligen; 40–50 cm Abstand | hoch |
| Mai–Jun | Abdecken | Insektenschutznetz sofort nach Pflanzung! | hoch |
| Jun–Aug | Gleichmäßig gießen | Wasserst.-schwankungen führen zu Rissen | mittel |
| Jul–Okt | Ernte + Nachernte | Hauptkopf ernten; Seitensprosse folgen | hoch |
| Okt–Nov | Beetvorbereitung | Gründüngung oder Kompost einarbeiten | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweißling | Pieris brassicae / P. rapae | Lochfraß, Raupen | leaf | vegetative, heading | easy |
| Kohleule | Mamestra brassicae | Fraßschäden, Nachtfalter-Raupen | leaf, head | heading | medium |
| Blattlaus | Brevicoryne brassicae | Graue Kolonien; Wachsbeschlag | leaf, shoot | seedling, vegetative | easy |
| Kohlfliege | Delia radicum | Welke, Fraß an Wurzeln und Strunk | root, stem | seedling, vegetative | difficult |
| Raupen | Plutella xylostella (Rapszüngler) | Minierfraß innen | leaf | vegetative | difficult |
| Schnecken | Arion spp. | Fraßschäden an Blättern | leaf | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kohlhernie | Plasmodiophora brassicae | Wurzelgallen, Welke | pH < 6.5, Staunässe | 14–21 | alle |
| Falscher Mehltau | Peronospora parasitica | Weißliche Blattflecken unten, gelbe oben | Feuchtigkeit, Wärme | 5–10 | seedling, vegetative |
| Ringfleckenkrankheit | Mycosphaerella brassicicola | Konzentrische braune Ringe | Feuchtigkeit | 7–14 | vegetative, heading |
| Grauschimmel | Botrytis cinerea | Fäulnis an Kopf und Stiel | Staunässe, Wunden | 3–5 | heading |
| Adernschwärze | Xanthomonas campestris | Schwarze Blattadern, V-förmige Flecken | Wärme + Feuchtigkeit | 5–10 | vegetative, heading |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Trichogramma brassicae | Kohlweißling (Eier) | 5–10 Karten | 7–14 |
| Bacillus thuringiensis (Dipel) | Raupen allg. | Sprühanwendung 0,5–1% | sofort |
| Schlupfwespe (Cotesia glomerata) | Kohlweißling-Raupen | natürlich vorhanden | — |
| Igel, Kröten | Schnecken | natürliche Einwanderer | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Ab Pflanzung; Maschenweite ≤ 0,8 mm | 0 | Kohlfliege, Weißling |
| Bacillus thuringiensis | biological | Bt-Toxin | Sprühen; abends (Raupen aktiv) | 0 | Raupen |
| Rapsöl-Emulsion | biological | Pflanzenöl | 1% Lösung sprühen | 0 | Blattläuse |
| Kalkstickstoff (Vorbeugung) | cultural | CaCN₂ | Boden-pH heben vor Pflanzung | — | Kohlhernie-Prophylaxe |
| Schneckenkorn | biological | Eisenphosphat (Ferramol) | 5 g/m² streuen | 0 | Schnecken |
| Pyrethrum | biological | Pyrethrine | Sprühen; nur Notfall | 3 | Blattläuse, Raupen |

### 5.5 Resistenzen

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Sorten-Resistenz Kohlhernie (CR-Sorten) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Kohlgewächse (Brassicaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte (Leguminosen: Erbse, Bohne) |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Spinat, Zwiebeln) oder Gründüngung (Phacelia) |
| Anbaupause (Jahre) | 3–4 Jahre; kein Kreuzblütler auf selber Fläche |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sellerie | Apium graveolens | 0.8 | Kohlfliegen-Abwehr; gegenseitig förderlich | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Nützlinge anlocken; lockert Boden | `compatible_with` |
| Mangold | Beta vulgaris subsp. vulgaris | 0.7 | Bodenbeschattung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Bodenschutz; schwaches Untergewächs | `compatible_with` |
| Thymian | Thymus vulgaris | 0.8 | Kohlfliegen-Abwehr durch Duft | `compatible_with` |
| Kamille | Matricaria chamomilla | 0.7 | Nützlingsförderung; Bodengesundheit | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Blumenkohl | Brassica oleracea var. botrytis | Gleiche Schädlinge + Kohlhernie-Risiko | severe | `incompatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | Gleiche Familie; Krankheitsdruck | severe | `incompatible_with` |
| Rosenkohl | Brassica oleracea var. gemmifera | Gleiche Schädlinge; selbe Familie | severe | `incompatible_with` |
| Erdbeere | Fragaria × ananassa | Kein gegenseitiger Nutzen; Bodenkonkurrenz | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Brassicaceae | `shares_pest_risk` | Kohlhernie, Kohlweißling, Kohlfliege | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Brokkoli |
|-----|-------------------|-------------|------------------------------|
| Blumenkohl | Brassica oleracea var. botrytis | Gleiche Familie, ähnliche Kultur | Wärmer; Norddeutschland schwieriger |
| Romanesco | Brassica oleracea var. botrytis Romanesco | Visuell spektakulär | Feineres Aroma; ähnliche Ansprüche |
| Kohlrabi | Brassica oleracea var. gongylodes | Gleiche Familie | Schneller reife (50–60 Tage); Topfkultur |
| Grünkohl | Brassica oleracea var. sabellica | Gleiche Familie | Extrem winterhart; Norddeutschland-Klassiker |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Brassica oleracea var. italica,"Brokkoli;Broccoli;Calabrese",Brassicaceae,Brassica,annual,long_day,herb,taproot,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Mittelmeerraum, Kleinasien",limited,25,30,90,60,45,no,limited,false,false,heavy_feeder,half_hardy,"5;6","7;8;9;10;11"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Marathon F1,Brassica oleracea var. italica,large_head;heat_tolerant,70,clubroot_resistant,hybrid
Calabrese,Brassica oleracea var. italica,classic;high_yield,75,,open_pollinated
Cleopatra F1,Brassica oleracea var. italica,early;compact,60,,hybrid
```

---

## Quellenverzeichnis

1. [Plantura Brokkoli](https://www.plantura.garden/gemuese/brokkoli/brokkoli-pflanzenportrait) — Anbau, Sorten, Erntezeiten
2. [Compo Brokkoli](https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/brokkoli) — Pflege, Düngung
3. [Hortipendium Brokkoli Pflanzenschutz](https://www.hortipendium.de/Brokkoli_Pflanzenschutz) — IPM, Schädlinge, Krankheiten
4. [Meine-Ernte Brokkoli](https://www.meine-ernte.de/pflanzen-a-z/gemuese/brokkoli/) — Aussaat, Pflanzzeiten, Mischkultur
