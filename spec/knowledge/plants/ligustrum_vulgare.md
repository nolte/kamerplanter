# Gewöhnlicher Liguster — Ligustrum vulgare

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** MOOWY Liguster, Pflanzen-Kölle Liguster, Plantura Liguster düngen, Lubera Liguster, OBI Liguster

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ligustrum vulgare | `species.scientific_name` |
| Volksnamen (DE/EN) | Gewöhnlicher Liguster, Rainweide; Common Privet | `species.common_names` |
| Familie | Oleaceae | `species.family` → `botanical_families.name` |
| Gattung | Ligustrum | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; L. vulgare heimisch in Deutschland; L. ovalifolium (Japanischer Liguster) nur bis -15°C | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Südwestasien | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze/Heckenpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (intensiv duftend; Pollen allergisierend) | `species.bloom_months` |

**Hinweis:** Die Blüten sind intensiv süß duftend, können aber Allergiker belasten. Beeren (schwarze Steinfrüchte, September–Oktober) sind GIFTIG.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge im Sommer (Juli/August) von halbverholzten Trieben, 15–20 cm lang. Sehr leicht zu bewurzeln.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Beeren (alle Teile mäßig giftig; Beeren am giftigsten) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Ligustrin, Syringin, Oleosid | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

**Hinweis:** Schwarze Beeren im Herbst locken Kinder an — Vergiftung durch Erbrechen, Durchfall, Herzrhythmusstörungen. Kinder-Haushalte: Liguster ohne Beerenbildung wählen (regelmäßiger Schnitt verhindert Beeren).

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 6, 8 (nach Blüte + Sommerrückschnitt); optional auch 3 | `species.pruning_months` |

**Hinweis:** Liguster verträgt starken Rückschnitt sehr gut. Formschnitt 2–3 Mal im Jahr: Juni (nach Blüte), August, optional März. Für dichte Hecke: junge Pflanzen stark schneiden. Nur NICHT in der Brutzeit (April–Juli) schneiden (Vogelschutz §39 BNatSchG) — außer notwendige Pflegeschnitte.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–500 (ungeschnitten bis 5 m) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–50 (Hecke: 3–5 Pflanzen/m) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale, lehmige Gartenerde; pH 5,5–7,5; toleriert viele Böden | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | high |
| Vegetatives Wachstum | 90–120 | 2 | false | false | high |
| Blüte | 20–30 | 3 | false | false | high |
| Nachblüte / Beerenreife | 60–90 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (nach Etablierung trockenheitstolerant) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 5.5–7.5 | 100 | 50 | — | 2 |
| Vegetativ | 2:1:2 | 1.0–1.4 | 5.5–7.5 | 120 | 60 | — | 2 |
| Blüte | 1:1:1 | 0.8–1.2 | 5.5–7.5 | 100 | 50 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch/Mineralisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Heckendünger (stickstoffreich) | Compo/Neudorff | organisch-mineralisch | 80–100 g/m² | April, Juni | Heckenwachstum |
| Hornspäne | Oscorna | organisch | 60–80 g/m² | April | Stickstoff für Wachstum |
| Kompost (reif) | eigen | organisch | 4–6 L/m² | März/Oktober | Bodenverbesserung |
| Patentkali | ICL Specialty Fertilizers | mineralisch | 30–40 g/m² | August | Triebausreifung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| April | Austrieb | Heckendünger oder Hornspäne | 80 g/m² | Starke Düngung fördert Wachstum für Heckenaufbau |
| Juni | Wachstum | optional: Nachdüngung | 40 g/m² | Bei trägem Wachstum |
| August | Abreife | Kalibetonter Dünger | 30 g/m² | Triebausreifung vor Winter |

### 3.3 Besondere Hinweise zur Düngung

Etablierte Ligusterhecken brauchen kaum Düngung — Mulchen reicht oft. Nur für schnellen Aufbau junger Hecken intensiver düngen. Kein Dünger nach August (Triebe sollen ausreifen).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; nach Etablierung sehr trockenheitstolerant; neu gepflanzte Hecken: erste 2 Jahre regelmäßig wässern | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 (kein Umtopfen nötig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Düngung | Heckendünger einarbeiten | mittel |
| Apr | Pflanzung möglich | Container-Pflanzen ganzjährig; Frühjahr ideal | mittel |
| Jun | Formschnitt 1 | Nach der Blüte; auf gewünschte Form bringen | hoch |
| Aug | Formschnitt 2 | Sommerrückschnitt; für dichte Hecke | hoch |
| Sep–Okt | Beeren reifen | Dekorativ; GIFTIG; ggf. entfernen (Kinder/Haustiere) | mittel |
| Mär | Optionaler Rückschnitt | Starker Verjüngungsschnitt wenn nötig | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien; Honigtau; Rußtau | leaf, shoot | vegetative (Frühjahr) | easy |
| Raupen (Ligusterrüsselkäfer) | Otiorhynchus ligustici | Fraß an Blättern; Larven an Wurzeln | leaf, root | vegetative | medium |
| Thripse | Thrips tabaci | Silbrige Flecken; Blattdeformation | leaf | vegetative (Sommer) | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Blattfleckenkrankheit | fungal (Cercospora ligustri) | Braune Flecken mit gelbem Rand | Feuchtigkeit, schlechte Luftzirkulation | 7–14 | vegetative |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 7–10 | vegetative (Sommer) |
| Liguster-Triebsterben | fungal | Triebe sterben ab; Rindenflecken | Frost, Verletzungen | 14–21 | nach Winter |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |
| Marienkäfer | Blattläuse | natürliche Förderung | sofort |
| Heterorhabditis bacteriophora | Rüsselkäfer-Larven | nach Herstellerangabe | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse, Thripse |
| Schnitt verbessert Luftzirkulation | cultural | — | Hecke innen auslichten | 0 | Blattflecken, Mehltau |
| Pyrethrum | biological | Pyrethrine | Sprühen | 3 | Raupen, Blattläuse |
| Fungizid (Kupfer) | chemical | Kupferoxydul | Sprühen | 14 | Blattflecken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Gehölze / Heckenpflanzen |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Weißdorn | Crataegus monogyna | 0.8 | Heimische Mischhecke; Insektenvielfalt | `compatible_with` |
| Holunder | Sambucus nigra | 0.8 | Heimische Mischhecke; Vögel | `compatible_with` |
| Schlehe | Prunus spinosa | 0.9 | Heimische Mischhecke; Dornenschutz | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fichte / Kiefer | Pinus, Picea spp. | Sehr unterschiedliche pH- und Nährstoffansprüche | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ligustrum vulgare |
|-----|-------------------|-------------|--------------------------------------|
| Japanischer Liguster | Ligustrum ovalifolium | Gleiches Genus | Immergrün; dichter; aber weniger winterhart |
| Hainbuche | Carpinus betulus | Heimische Heckenpflanze | Behält Laub über Winter; herbstliche Färbung |
| Feldahorn | Acer campestre | Heimische Heckenpflanze | Schöne Herbstfärbung; robust |
| Ilex | Ilex aquifolium | Immergrüne Hecke | Immergrün; dekorativ; aber langsamer Wuchs |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Ligustrum vulgare,"Gewöhnlicher Liguster;Rainweide;Common Privet",Oleaceae,Ligustrum,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",-0.1,"Europa, Nordafrika, Südwestasien",limited,30,40,300,150,40,no,no,false,false,medium_feeder,false,hardy,"5;6;7"
```

---

## Quellenverzeichnis

1. [MOOWY — Liguster pflanzen](https://moowy.de/liguster-pflanzen/) — Pflege, Schnitt
2. [Pflanzen-Kölle — Liguster Ratgeber](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-liguster-richtig/) — IPM, Übersicht
3. [Plantura — Liguster düngen](https://www.plantura.garden/gehoelze/liguster/liguster-hecken-duengen) — Düngung
4. [Lubera — Liguster](https://www.lubera.com/de/gartenbuch/liguster-pflege-schneiden-vermehren-p2560) — Schnitt, Vermehrung
5. [OBI — Liguster](https://www.obi.de/magazin/garten/pflanzen/heckenpflanzen/steckbrief-liguster) — Steckbrief
