# Weizen — Triticum aestivum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Bayerische LfL Weizenanbau, BBCH-Skala Getreide (Zadoks-Skala), FAO Crop Profiles, DLG-Merkblätter Pflanzenschutz

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Triticum aestivum | `species.scientific_name` |
| Volksnamen (DE/EN) | Weichweizen, Weizen, Brotweizen; Common Wheat, Bread Wheat | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Triticum | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sommerweizen: Frühjahrssaat; Winterweizen winterhart bis -20°C (unter Schneedecke), ohne Schnee bis -12°C; Vernalisation erforderlich für Wintertypen; Spätfrost-Schäden bei BBCH 49–55 | `species.hardiness_detail` |
| Heimat | Vorderer Orient (Fruchtbarer Halbmond); Domestizierung ca. 10.000–8.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis:** Triticum aestivum ist das weltweit meistangebaute Getreide und das wichtigste Backgetreide Mitteleuropas. Unterschieden werden Sommerweizen (März–April Saat; Juli–August Ernte) und Winterweizen (Oktober Saat; Juli Ernte). Winterweizen dominiert in Mitteleuropa aufgrund höherer Erträge.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -42 (Sommerweizen ab März; Winterweizen Oktober) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Sommerweizen); 9, 10 (Winterweizen) | `species.direct_sow_months` |
| Erntemonate | 7, 8 | `species.harvest_months` |
| Blütemonate | 5, 6 (Winterweizen); 6, 7 (Sommerweizen) | `species.bloom_months` |

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
| Giftige Pflanzenteile | — (Hauptnahrungsmittel der Menschheit; Mehl, Brot) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Gluten (Gliadin + Glutenin); Zöliakie-Auslöser; Weizenallergie möglich | `species.toxicity.toxic_compounds` |
| Schweregrad | none (außer Glutenunverträglichkeit/Zöliakie) | `species.toxicity.severity` |
| Kontaktallergen | true (Bäckerasthma; Berufsallergen; Weizenmehlstaub) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen; starkes Sommerallergen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stoppelbearbeitung, Strohmanagement) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (Weizengras / Microgreens) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 70–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 (Einzelhalm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Drillsaat: Reihenabstand 10–15 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (Weizengras / Sprossen) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lehmige, nährstoffreiche Erde; pH 6,0–7,5; kalkverträglich | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | high |
| Bestockung | 20–60 | 2 | false | false | high |
| Schossen | 21–35 | 3 | false | false | medium |
| Ährenschieben / Blüte | 14–21 | 4 | false | false | low |
| Milch- / Teigreife | 14–21 | 5 | false | false | medium |
| Vollreife / Ernte | 7–14 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–85 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 (Winterweizen: kurze Tage für Vernalisation) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 8–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Schossen

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–38 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Ährenschieben / Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vollreife / Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 20–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 35–55 (trocken für Drusch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–2.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 (keine Bewässerung; Abreife trocken) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.5 | — | — | — |
| Bestockung | 3:1:2 | 0.8–1.4 | 6.0–7.5 | 80 | 30 | 20 |
| Schossen | 3:1:2 | 1.4–2.0 | 6.0–7.5 | 120 | 45 | 30 |
| Blüte | 1:2:2 | 1.2–1.8 | 6.0–7.5 | 100 | 50 | 25 |
| Reife | 0:1:2 | 0.6–1.0 | 6.0–7.5 | 60 | 30 | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Bestockung | time_based | 5–10 Tage; Keimblatt erscheint (BBCH 09–11) |
| Bestockung → Schossen | time_based | 20–60 Tage; nach Vernalisation; langer Tag (BBCH 30) |
| Schossen → Blüte | time_based | 21–35 Tage; Fahnenblatt voll entfaltet (BBCH 37) |
| Blüte → Reife | time_based | 14–21 Tage; Antheren sichtbar (BBCH 61); Korn setzt an |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kalkammonsalpeter (KAS) | diverse | Granulat | 27-0-0 | 40–60 g/m² | Schossen (EC 30) |
| Nitrophoska 12-12-17 | Compo | Granulat | 12-12-17 | 30–50 g/m² | Grunddüngung |
| Schwefel-Harnstoff | diverse | Granulat | 40-0-0+S | 25–40 g/m² | Schossen |
| Blattdünger Kalium | diverse | flüssig | 0-0-40 | 5–10 ml/L | Kornfüllungsphase |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 4–6 L/m² | Herbst-Grunddüngung |
| Rinderdung | diverse | organisch | 80–120 g/m² | Herbst |
| Hornmehl | diverse | organisch | 60–100 g/m² | Frühjahrssaat |
| Pflanzenkohle (Biochar) | diverse | Bodenverbesserer | 200–500 g/m² | Grunddüngung |

### 3.2 Besondere Hinweise zur Düngung

Weizen ist Starkzehrer mit dem höchsten N-Bedarf unter den Getreidearten (ca. 160–220 kg N/ha in der Landwirtschaft). Im Gartenbau gilt: Geteilte N-Gaben (Grunddüngung + Schossen-Gabe) verhindern Lagergefahr. Schwefel (S) ist wichtig für die Backqualität (Glutenbildung). Bei Bodenanalyse: pH 6,5–7,5 anstreben.

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
| Sep–Okt | Winterweizen-Saat | Optimales Saatfenster 1.–25. Oktober; Saattiefe 3–5 cm | hoch |
| Mär | Sommerweizen-Saat | Frühsaat ab Ende Februar/Anfang März | hoch |
| Apr | N-Düngung Grundgabe | Stickstoff zur Vegetationsphase | mittel |
| Mai | N-Düngung Schossen | Qualitätsstickstoff bei BBCH 30–32 | hoch |
| Jun | Fungizidkontrolle | Ährengesundheit sichern (BBCH 51–65) | mittel |
| Jul–Aug | Ernte | Körnerfeuchte 13–14%; Sofortdrusch bei Wetter | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Getreideblattlaus | Sitobion avenae | Kolonie auf Ähren; Honigtau; BYDV-Vektor | Ähre, Blatt | Schossen, Blüte |
| Getreidehähnchen | Oulema melanopus | Blattfraß in Streifen | Blatt | Schossen |
| Weizengallmücke | Sitodiplosis mosellana | Kleinkörnige Ähren; Kornabtrieb | Ähre | Blüte |
| Hessische Gallmücke | Mayetiola destructor | Halmnekrose; Blattverformung | Halm, Blatt | Bestockung |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Septoria-Blattdürre | fungal (Zymoseptoria tritici) | Hellbraune Flecken; Pyknidien | feucht-kühl |
| Gelbrost | fungal (Puccinia striiformis) | Gelbe Pustelstreifen | kühl-feucht |
| Braunrost | fungal (Puccinia triticina) | Braune Pusteln; Ertragsverlust | warm-feucht |
| Echter Mehltau | fungal (Blumeria graminis f.sp. tritici) | Weißgrauer Belag | trocken-warm |
| Ährenfusarium | fungal (Fusarium graminearum) | Weißähren; Mykotoxine (DON, ZEA) | feucht zu Blüte |
| Steinbrand | fungal (Tilletia caries) | Stinkende Sporenlager in Körnern | Saatgut |

**KRITISCH — Ährenfusarium:** Mykotoxine (Deoxynivalenol DON, Zearalenon ZEA) gefährden Lebensmittel- und Futterqualität. Monitoring und resistente Sorten zwingend. Befallenes Erntegut nicht für Nahrungsmittel verwenden.

### 5.3 Nützlinge

| Nützling | Ziel-Schädling |
|----------|---------------|
| Brackwespe (Aphidius ervi) | Getreideblattlaus |
| Marienkäfer (Coccinella spp.) | Blattläuse |
| Ohrwurm (Forficula auricularia) | Blattläuse, Eier |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Triazol-Fungizid | chemical | Tebuconazol | Sprühen BBCH 31–65 | 35 | Rost, Septoria, Ährenfusarium |
| Strobilurin-Fungizid | chemical | Azoxystrobin | Sprühen BBCH 32–49 | 35 | Rost, Mehltau, Septoria |
| Saatgutbeizung | chemical | Tebuconazol + Fludioxonil | Beize | — | Brandkrankheiten |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Rost, Septoria, Mehltau |
| Weite Fruchtfolge | cultural | — | Max. 50% Getreide | 0 | Halmbasiserkrankungen |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Getreide (Poaceae) |
| Empfohlene Vorfrucht | Raps (beste Vorfrucht!), Hülsenfrüchte, Zuckerrübe, Kartoffel |
| Empfohlene Nachfrucht | Raps, Sommergerste, Leguminosen |
| Anbaupause (Jahre) | 2 Jahre Pause empfohlen; maximal 50% Getreide in Fruchtfolge |

**Stoppelweizen (Weizen nach Weizen):** Stark erhöhtes Krankheitsrisiko (Septoria, Ährenfusarium, Halmbasis); vermeiden! Raps als Vorfrucht steigert Ertrag um 10–15% (Rapsvorfruchteffekt).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kleearten | Trifolium spp. | 0.8 | Untersaat; N-Fixierung; Erosionsschutz nach Ernte | `compatible_with` |
| Ackererbse | Pisum sativum | 0.7 | Gemengepartner (Weizen-Erbsen-Gemenge); N-Fixierung | `compatible_with` |
| Luzerne | Medicago sativa | 0.7 | Untersaat; tiefe Bodenlockerung; N-Fixierung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Gerste | Hordeum vulgare | Gleiche Pathogene (Mehltau, Rost); Konkurrenz | moderate | `incompatible_with` |
| Mais | Zea mays | Fusarium-Suszeptibilität beider; Inokulum-Anreicherung | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Weichweizen |
|-----|-------------------|-------------|-------------------------------|
| Dinkel | Triticum spelta | Engste Verwandtschaft (Unterart) | Robuster; Nischenmarkt; ohne Fusarium-Toleranz |
| Emmer | Triticum turgidum subsp. dicoccum | Urgetreide | Historisch; Nischenmarkt |
| Durum-Weizen | Triticum turgidum subsp. durum | Hartweizen | Nudelqualität; Mediterran |
| Triticale | × Triticosecale | Roggen-Weizen-Kreuzung | Robuster auf schwachen Böden |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Triticum aestivum,"Weichweizen;Weizen;Brotweizen;Common Wheat;Bread Wheat",Poaceae,Triticum,annual,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.2,"Vorderer Orient",limited,limited,limited,false,false,heavy_feeder,false,half_hardy,"3;4;9;10","7;8","5;6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Julius,Triticum aestivum,"winter_wheat;high_yield;good_baking_quality",270,septoria;yellow_rust,certified
RGT Sacramento,Triticum aestivum,"winter_wheat;high_yield;early",265,fusarium;yellow_rust,certified
Alixan,Triticum aestivum,"summer_wheat;baking_quality;medium_early",110,fusarium_tolerant,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS Database — Triticum aestivum](https://plants.usda.gov/plant-profile/TRAE) — Taxonomie
2. [Bayerische LfL — Winterweizenanbau](https://www.lfl.bayern.de/ipz/getreide) — Anbaupraxis, Sorten
3. [BBCH-Skala Getreide (Meier 2001)](https://www.bba.de) — Entwicklungsstadien
4. [DLG Merkblatt Ährenfusarium](https://www.dlg.org) — Mykotoxin-Risiko, Bekämpfung
5. [Saaten-Union Weizensortenkatalog](https://www.saaten-union.de) — Sortenbeschreibungen
