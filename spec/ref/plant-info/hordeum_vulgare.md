# Gerste — Hordeum vulgare

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Bayerische LfL Gerste, University of California Cooperative Extension, DLG-Merkblätter Getreideanbau, Royal Horticultural Society

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hordeum vulgare | `species.scientific_name` |
| Volksnamen (DE/EN) | Gerste, Saat-Gerste; Common Barley, Cultivated Barley | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Hordeum | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sommergerste: frostempfindlich; Wintergerste: winterhart bis -15°C (unter Schneedecke), ohne Schnee bis -10°C; Vernalisation (Vernalization) für Wintergerste notwendig | `species.hardiness_detail` |
| Heimat | Vorderer Orient (Fruchtbarer Halbmond); domestiziert ca. 10.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -28 (Sommergerste ab Mitte März; Wintergerste September–Oktober) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Sommergerste); 9, 10 (Wintergerste) | `species.direct_sow_months` |
| Erntemonate | 7 (Sommergerste); 6, 7 (Wintergerste) | `species.harvest_months` |
| Blütemonate | 5, 6 (Wintergerste); 6, 7 (Sommergerste) | `species.bloom_months` |

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
| Giftige Pflanzenteile | — (Nahrungsmittel; Malz, Graupen, Mehl; Bier-Rohstoff) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Gluten (Zöliakie-Relevant; Hordein-Gluten) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (außer Zöliakie/Glutenunverträglichkeit) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen; Mai–Juli-Flug) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stoppelbearbeitung nach Drusch) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (Katzengras / Sprossen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 (Einzelhalm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Drillsaat Reihenabstand 12–15 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (Sprossen/Gerstengras) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte nährstoffarme Erde; pH 6,0–7,5; gut drainiert | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 4–8 | 1 | false | false | high |
| Bestockung | 14–35 | 2 | false | false | high |
| Schossen | 21–35 | 3 | false | false | medium |
| Ährenschieben / Blüte | 10–18 | 4 | false | false | low |
| Abreife | 21–35 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.1 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–6 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Schossen

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Ährenschieben / Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

**KRITISCH — Blüte:** Spätfröste bei BBCH 49–55 (Ährenschieben) können erhebliche Ertragsausfälle verursachen. Keine Bodenatmosphäre-Kältewellen in dieser Phase.

#### Phase: Abreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 (trocken = Qualitätserhalt) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.2–2.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 10–21 (Wasserreduktion) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5–7.5 | — | — |
| Bestockung | 3:1:2 | 0.8–1.2 | 6.5–7.5 | 80 | 30 |
| Schossen | 3:1:2 | 1.2–1.8 | 6.5–7.5 | 100 | 40 |
| Blüte | 1:2:2 | 1.0–1.5 | 6.5–7.5 | 80 | 40 |
| Abreife | 0:1:2 | 0.6–1.0 | 6.5–7.5 | 60 | 25 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Bestockung | time_based | 4–8 Tage; Coleoptile sichtbar (BBCH 09) |
| Bestockung → Schossen | time_based | 14–35 Tage; Haupttrieb 1 cm erhoben (BBCH 30) |
| Schossen → Blüte | time_based | 21–35 Tage; Fahnenblatt sichtbar (BBCH 37–39) |
| Blüte → Abreife | time_based | 10–18 Tage; Korn milchreif (BBCH 71) |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Ammoniumnitrat (AHL) | diverse | Flüssig-N | 28-0-0 | 15–25 kg N/ha | Schossen |
| Nitrophoska perfekt | Compo | Granulat | 15-5-20 | 30–50 g/m² | Frühsaat |
| Triple-Superphosphat | diverse | Granulat | 0-46-0 | 10–15 g/m² | Grunddüngung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Rinderdung (pelletiert) | diverse | organisch | 60–100 g/m² | Herbst/Frühjahr |
| Kompost | eigen | organisch | 3–5 L/m² | Herbst-Grunddüngung |
| Hornmehl | diverse | organisch | 50–80 g/m² | Frühsaat |

### 3.2 Besondere Hinweise zur Düngung

Gerste reagiert sehr sensibel auf N-Überdüngung (Lagergefahr). Braugerste: Niedrige N-Düngung (max. 80 kg N/ha) für niedrigen Proteingehalt (Brauqualität erfordert <11,5% Protein). Futtergerste: Höherer N-Einsatz möglich. Auf kalkreichen Böden gut geeignet (pH-Toleranz bis 8,0).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Sep–Okt | Wintergerste-Saat | Saattiefe 3–5 cm; Drillsaat; gute Saatbettvorbereitung | hoch |
| Mär–Apr | Sommergerste-Saat | Frühsaat ab März; Drillsaat | hoch |
| Apr–Mai | Wachstumskontrolle | Schädlinge und Krankheiten überwachen | mittel |
| Mai | N-Düngung Schossen | Stickstoffgabe für Vegetationsschub | mittel |
| Jun–Jul | Ernte Wintergerste | Bei Körnerfeuchte 14–15%; Drusch | hoch |
| Jul–Aug | Ernte Sommergerste | Drusch; Nachtrocknung bei Feuchtigkeit | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Blattlaus | Rhopalosiphum padi, Sitobion avenae | Kolonie auf Blättern; BYDV-Übertragung | Blatt, Ähre | Schossen, Blüte |
| Getreidehähnchen | Oulema melanopus | Blattfraß; Streifenmuster | Blatt | Schossen |
| Fritfliege | Oscinella frit | Totes Herz; Triebausfall | Trieb | Keimung |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Netzfleckenkrankheit | fungal (Pyrenophora teres) | Braune Netzflecken auf Blättern | hohe Feuchte; kühl |
| Echter Mehltau | fungal (Blumeria graminis f.sp. hordei) | Weißgrauer mehligerBelag | trocken-warm |
| Gelbrost | fungal (Puccinia striiformis) | Gelbe Streifen; Sporenlager | kühl-feucht |
| Zwergsteinbrand | fungal (Tilletia controversa) | Schwarze Sporenstatt Korn | Saatgut; Boden |
| Blattdürre | fungal (Rhynchosporium commune) | Wasserdurchtränkte Flecken → braun | feuchte Witterung |
| Gelbverzwergungsvirus BYDV | viral | Gelbfärbung; Zwergwuchs; Ertragsverlust bis 50% | Blattlaus-Übertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling |
|----------|---------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse |
| Brackwespe (Aphidius ervi) | Getreideblattläuse |
| Laufkäfer (Carabidae) | Fritfliege, Getreideblattläuse |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Fungizid (Azol) | chemical | Prothioconazol | Sprühen BBCH 31–39 | 35 | Netzflecken, Rost, Mehltau |
| Saatgutbeizung | chemical | Tebuconazol | Beize | — | Brandkrankheiten, Streifenkrankheit |
| Pyrethroid | chemical | Deltamethrin | Sprühen bei Befallsbeginn | 14 | Blattläuse, Hähnchen |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Mehltau, Gelbrost, Netzflecken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Getreide (Poaceae) |
| Empfohlene Vorfrucht | Raps, Hülsenfrüchte, Kartoffel, Rübe |
| Empfohlene Nachfrucht | Winterweizen, Winterraps, Leguminosen |
| Anbaupause (Jahre) | 2–3 Jahre Pause vor erneutem Getreide auf gleicher Fläche |

**Besonderheit:** Gerste ist empfindlicher gegenüber Getreidemüdigkeit (Getreidezysten-Nematoden) als Hafer. Maximale Getreideanteile in der Fruchtfolge: 50–60%. Wintergerste eignet sich als frühe Vorfrucht für Gemüse (Ernte im Juni/Juli).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Erbse | Pisum sativum | 0.8 | Gersten-Erbsen-Gemenge; N-Fixierung; gegenseitige Stützung | `compatible_with` |
| Kleearten | Trifolium spp. | 0.8 | Untersaat; Bodenschutz nach Ernte; N-Fixierung | `compatible_with` |
| Wicke | Vicia sativa | 0.8 | Gemengepartner; erhöhter Proteingehalt | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Weizen | Triticum aestivum | Gleiche Schädlinge und Krankheiten; Konkurrenz | moderate | `incompatible_with` |
| Hafer | Avena sativa | Gleiche Schädlinge; weniger Komplementarität | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Gerste |
|-----|-------------------|-------------|-------------------------|
| Weizen | Triticum aestivum | Getreide; Sommerform | Höherer Backwert; Glutengehalt |
| Hafer | Avena sativa | Getreide; anspruchsloser | Sanierungsfrucht; glutenfrei |
| Triticale | × Triticosecale | Getreidekreuzung | Robuster; höhere Erträge auf schwachen Böden |
| Roggen | Secale cereale | Wintergetreide | Extremster Wintertolerant; sandig-saure Böden |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Hordeum vulgare,"Gerste;Saat-Gerste;Common Barley;Cultivated Barley",Poaceae,Hordeum,annual,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.1,"Vorderer Orient",limited,limited,limited,false,false,medium_feeder,false,half_hardy,"3;4;9;10","6;7","5;6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Barke,Hordeum vulgare,"two_row;malting_quality;winter_hardy",95,certified
Scarlett,Hordeum vulgare,"two_row;malting_barley;high_yield",100,certified
Quench,Hordeum vulgare,"two_row;spring_barley;malting",90,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS Database — Hordeum vulgare](https://plants.usda.gov/plant-profile/HOVU) — Taxonomie, Verbreitung
2. [Bayerische LfL — Gerste](https://www.lfl.bayern.de/ipz/getreide/023693/index.php) — Anbauempfehlungen
3. [University of California Cooperative Extension — Barley](https://ucanr.edu) — Nährstoffbedarf, IPM
4. [DLG Merkblätter Getreide](https://www.dlg.org) — Pflanzenschutz, Krankheiten
5. [Saaten-Union Sortenkatalog Gerste](https://www.saaten-union.de) — Sorteneigenschaften, Brauqualität
