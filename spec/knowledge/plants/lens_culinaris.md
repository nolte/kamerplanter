# Linse — Lens culinaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Royal Horticultural Society, Bayerische LfL Körnerleguminosen, University of Saskatchewan Lentil, FAO Lentil Crop Profile

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lens culinaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Linse, Speiselinse; Lentil, Common Lentil | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Lens | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kälteverlträglich bis ca. -5°C im Keimlingsstadium; frühzeitige Aussaat möglich (März); Spätfröste nach Bestockung können Ertragseinbußen verursachen | `species.hardiness_detail` |
| Heimat | Vorderer Orient (Fruchtbarer Halbmond); domestiziert ca. 8.000–9.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**N-Fixierung:** Lens culinaris fixiert in Symbiose mit *Rhizobium leguminosarum* bv. viciae 50–100 kg N/ha. Impfung mit geeignetem Rhizobium-Impfstoff bei Erstanbau empfohlen. Die Pflanze produziert trotzdem essbare Körner — doppelter Nutzen.

**Historische Bedeutung:** Linse ist eine der ältesten Kulturpflanzen der Menschheit und stand an der Wiege der Landwirtschaft im Nahen Osten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat bevorzugt; Pfahlwurzel schlecht umpflanzbar) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (Frühsaat ab Mitte März möglich; kältetolerante Art) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 | `species.direct_sow_months` |
| Erntemonate | 7, 8 (Trockenernte); 6, 7 (Grünernte / grüne Linsen) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

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
| Giftige Pflanzenteile | Rohe Linsen (Lektine, Trypsinhemmer; werden beim Kochen inaktiviert) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Phytinsäure (mindert Mineralstoffaufnahme; durch Einweichen reduzierbar) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (nach Kochen völlig unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (kleine Pflanze; aber Pfahlwurzel) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5 cm in der Reihe; 30–40 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | limited (niedrige Sorten stehen; höhere können lagern) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, durchlässige Erde; pH 6,0–8,0; kalkverträglich; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–12 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 21–42 | 3 | false | false | high |
| Blüte | 21–35 | 4 | false | false | low |
| Hülsenansatz | 14–21 | 5 | false | true | medium |
| Reife | 21–35 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–4 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtagpflanze) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 (trockenheitstolerante Pflanze) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 (trocken für Ernte) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.2–2.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 10–21 (Wasserreduktion) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–8.0 | — | — |
| Sämling | 0:1:1 | 0.4–0.8 | 6.0–8.0 | 60 | 20 |
| Vegetativ | 0:1:2 | 0.6–1.2 | 6.0–8.0 | 80 | 30 |
| Blüte | 0:2:2 | 0.8–1.4 | 6.0–8.0 | 80 | 40 |
| Reife | 0:1:1 | 0.4–0.8 | 6.0–8.0 | 60 | 20 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Biologisch

| Produkt | Marke | Typ | Ausbringrate | Phasen |
|---------|-------|-----|-------------|--------|
| Rhizobium leguminosarum (Impfmittel) | diverse | Saatgutimpfung | 250 ml/25 kg Saatgut | Vor Saat |
| Kompost | eigen | organisch | 3–4 L/m² | Herbst/Frühjahr |

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Superphosphat | diverse | mineralisch | 0-46-0 | 15–20 g/m² | Grunddüngung |
| Kaliumsulfat | diverse | mineralisch | 0-0-50 | 10–15 g/m² | Grunddüngung |

### 3.2 Besondere Hinweise zur Düngung

KEINE Stickstoffdüngung bei funktionierender Rhizobium-Symbiose. Kalziumversorgung wichtig (pH-neutraler bis leicht alkalischer Boden ideal). Phosphormangel hemmt Knöllchenbildung. Spurenelement Molybdän (Mo) für N-Fixierung essentiell.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 (trockenheitstolerant) | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 28 (P + K nur) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Planung | Rhizobium-Impfmittel bestellen; Saat vorbereiten | mittel |
| Mär–Apr | Aussaat | Frühsaat ab März; 3–4 cm tief; 5 cm Abstand | hoch |
| Apr–Mai | Kontrolle | Knöllchenbildung prüfen; Unkraut hacken | mittel |
| Jun | Grünernte (optional) | Grüne Hülsen mit Körnern für Frischgenuss | niedrig |
| Jul–Aug | Trockenernte | Hülsen braun; Pflanzen absterben; Drusch | hoch |
| Aug | Bodenbearbeitung | Wurzeln einarbeiten; N-Depot | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Blattläuse | Aphis fabae, Acyrthosiphon pisum | Kolonien; Virustransmission | Blatt, Trieb | Alle |
| Linsenrüssler | Sitona crinitus | Fraß an Blatträndern; Larven in Wurzelknöllchen | Blatt, Knöllchen | Sämling |
| Erbsenwickler | Cydia nigricana | Larven in Hülsen / Körnern | Hülse | Blüte, Reife |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Brennfleckenkrankheit | fungal (Colletotrichum truncatum) | Dunkelbraune Flecken; Stängelläsionen | feucht-warm |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Pilzrasen | hohe Luftfeuchte; kühl |
| Sklerotinia-Fäule | fungal (Sclerotinia sclerotiorum) | Weiße Myzel-Läsionen | feuchte Bedingungen |
| Aszochyta-Blattflecken | fungal (Ascochyta lentis) | Gelblich-braune Blattflecken | feucht |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Linsenrüssler |
| Pyrethrin | biological | Pyrethrine | Sprühen | 3 | Blattläuse |
| Trichoderma-Beizmittel | biological | Trichoderma harzianum | Saatgutbeize | 0 | Saatgutfäulen |
| Weite Fruchtfolge | cultural | — | 3–4 Jahre Pause | 0 | Sklerotinia, Aszochyta |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide (Weizen, Gerste); Wintergetreide |
| Empfohlene Nachfrucht | Winterweizen, Mais, Raps (profitieren vom N-Depot) |
| Anbaupause (Jahre) | 4–5 Jahre auf gleichem Standort (Sklerotinia-Dauerformen) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Gerste | Hordeum vulgare | 0.8 | Klassisches Gerste-Linsen-Gemenge; Gerste stützt Linse | `compatible_with` |
| Leindotter | Camelina sativa | 0.7 | Stützfunktion; Ölpflanze | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Insektenanlockung; Begleitpflanze | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Knoblauch | Allium sativum | Hemmt Rhizobium-Knöllchenbildung | moderate | `incompatible_with` |
| Zwiebel | Allium cepa | Gleiche antibiotische Wirkung | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Gleiche Familie; gleiche Pathogene (Ascochyta); Konkurrenz | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Linse |
|-----|-------------------|-------------|------------------------|
| Erbse | Pisum sativum | Fabaceae; ähnliche Kultur | Höherer Ertrag; mehr Sorten |
| Kichererbse | Cicer arietinum | Fabaceae; Naher Osten | Hitze- und Trockentoleranter |
| Ackerbohne | Vicia faba | Fabaceae; kältetoleranter | Größere Bohne; höherer Ertrag |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Lens culinaris,"Linse;Speiselinse;Lentil;Common Lentil",Fabaceae,Lens,annual,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Vorderer Orient",limited,no,limited,false,limited,nitrogen_fixer,true,half_hardy,"3;4;5","7;8","5;6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Aldina,Lens culinaris,"green_lentil;medium_early;mitteleuropa_adapted",90,open_pollinated
Precosa,Lens culinaris,"red_lentil;peeled;high_yield",100,certified
Anicia,Lens culinaris,"beluga_type;black;gourmet",110,open_pollinated
```

---

## Quellenverzeichnis

1. [USDA PLANTS — Lens culinaris](https://plants.usda.gov/plant-profile/LECU7) — Taxonomie
2. [University of Saskatchewan — Lentil Production](https://www.usask.ca) — Anbaupraxis
3. [Bayerische LfL — Körnerleguminosen](https://www.lfl.bayern.de/ipz/leguminosen) — Mitteleuropa
4. [FAO Lentil Crop Profile](https://www.fao.org) — Globale Anbausysteme, Nährstoffe
5. [Royal Horticultural Society — Lentils](https://www.rhs.org.uk) — Gartenbau-Empfehlungen
