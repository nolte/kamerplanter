# Sojabohne — Glycine max

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, University of Illinois Extension Soybean, Bayerische LfL Soja, Iowa State University Extension, FAO Soybean Crop Profile

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Glycine max | `species.scientific_name` |
| Volksnamen (DE/EN) | Sojabohne, Soya; Soybean, Soya Bean | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Glycine | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frost-empfindlich; Mindestkeimtemperatur 10°C (besser 15°C); stirbt bei -2°C ab; in Mitteleuropa als Sommerkorn ab Ende Mai bis Mitte Juli | `species.hardiness_detail` |
| Heimat | Ostasien (China, Japan); domestiziert ca. 3000 v. Chr. in China | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**N-Fixierung:** Sojabohne fixiert in Symbiose mit *Bradyrhizobium japonicum* 50–150 kg N/ha pro Saison — das bedeutet kaum N-Düngung nötig. Impfung des Saatgutes mit Bradyrhizobium dringend empfohlen, besonders bei Erstanbau auf dem Standort! Rückstände der Sojawurzel bereichern den Boden für Folgekulturen erheblich.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (optional; Direktsaat bevorzugt da Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 7–14 (Bodentemperatur mind. 10°C; besser 15°C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 9, 10 (Trockenbohne); 8, 9 (Edamame = grüne Sojabohne) | `species.harvest_months` |
| Blütemonate | 7, 8 | `species.bloom_months` |

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
| Giftige Pflanzenteile | Rohe Bohnen (Hämagglutinin, Trypsinhemmer; werden beim Kochen inaktiviert) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Hämagglutinin, Trypsin-Inhibitoren (roh); Isoflavone (hormonaktiv; relevant für bestimmte Personengruppen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (nur roh; nach Erhitzen unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis Sojaprotein-Allergie:** Soja zählt zu den 14 großen EU-Lebensmittelallergenen. Sojaprotein kann bei Allergikern starke Reaktionen auslösen. Nicht zu verwechseln mit der Pflanze selbst — die Pflanze im Garten ist unbedenklich.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 (Pfahlwurzel; breite Töpfe) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5–10 cm in der Reihe; 40–60 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leicht durchlässige, lehmige Erde; pH 6,0–6,8; gut drainiert; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling (V1–V3) | 14–21 | 2 | false | false | low |
| Vegetativ (V4–V6) | 21–42 | 3 | false | false | medium |
| Blüte (R1–R2) | 14–21 | 4 | false | false | low |
| Hülsenbildung (R3–R4) | 21–28 | 5 | false | true | medium |
| Samenreife (R5–R8) | 28–42 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 (gleichmäßig feucht; kein Staunässe) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ (V4–V6)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | >13 (Langtagbedingungen verhindern vorzeitige Blüte; Kurztagpflanze) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 24–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blüte (R1–R2)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–38 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | ≤13 (Kurztagblüher; Blüteninduktion durch kürzere Tage) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 24–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–5 (regelmäßige Bewässerung kritisch für Setzrate) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Samenreife (R5–R8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 (trocken = bessere Druschfähigkeit) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–14 (Wasserreduktion zur Abreife) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mo (µg/L) |
|-------|----------------|---------|-----|----------|----------|---------|
| Keimung | 0:0:0 | 0.0 | 6.0–6.8 | — | — | — |
| Sämling | 0:1:1 | 0.4–0.8 | 6.0–6.8 | 60 | 25 | 10 |
| Vegetativ | 0:1:2 | 0.8–1.4 | 6.0–6.8 | 100 | 40 | 10 |
| Blüte | 0:2:2 | 1.0–1.6 | 6.0–6.8 | 100 | 50 | 10 |
| Reife | 0:1:1 | 0.6–1.0 | 6.0–6.8 | 60 | 30 | — |

**Hinweis:** Keine N-Düngung nötig bei funktionierender Bradyrhizobium-Symbiose! Molybdän (Mo) ist für die N-Fixierung im Knöllchen essentiell — bei Mo-Mangel bricht Fixierung zusammen.

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Biologisch/Mineralisch

| Produkt | Marke | Typ | Ausbringrate | Phasen |
|---------|-------|-----|-------------|--------|
| Bradyrhizobium japonicum (Impfmittel) | diverse (Sojaculture, HiStick) | Saatgutimpfung | 250 ml/25 kg Saatgut | Vor Saat |
| Superphosphat / Triplesuperphosphat | diverse | mineralisch | 20–30 g/m² P₂O₅ | Grunddüngung |
| Kaliumsulfat | diverse | mineralisch | 15–25 g/m² K₂O | Grunddüngung |
| Molybdänblattdünger | diverse | Spurenelement | 0,1 g/L; 1× sprühen | Keimlingsstadium |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost (reif) | eigen | organisch | 3–5 L/m² | Herbst/Frühjahr |
| Hornmehl | diverse | organisch | 30–50 g/m² | Sparsam (N-Fixierung beachten!) |
| Kalkstein (gemahlen) | diverse | pH-Korrektur | je nach Bedarf | Herbst |

### 3.2 Mischungsreihenfolge (bei Flüssigdüngung)

> **Kritisch:** Bradyrhizobium-Impfmittel ist empfindlich gegen direkte Sonneneinstrahlung und chemische Dünger — Saat nach Impfung sofort einbringen!

1. Saatgut anfeuchten (Wasser)
2. Bradyrhizobium-Impfmittel auftragen und gut vermengen
3. Sofort bei bedecktem Himmel säen (Lichtempfindlichkeit der Bakterien)
4. KEINE chemischen Beizmittel gleichzeitig mit Bradyrhizobium verwenden

### 3.3 Besondere Hinweise zur Düngung

Sojabohne ist Stickstofflieferant, KEIN Stickstoffverbraucher. Übermäßige N-Düngung hemmt die symbiotische N-Fixierung — Knöllchen bleiben klein oder weiß statt rosa/rot. Ziel: Phosphor- und Kaliumversorgung sichern; N nur minimal bei Anlaufschwierigkeiten der Knöllchenbakterien.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4–7 | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | pH 6,0–6,8; kalkreiches Wasser kalibrieren | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 (P + K; kein N) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–8 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Planung / Saatgut | Bradyrhizobium-Impfmittel beschaffen; frühreife Sorte wählen | hoch |
| Mai | Aussaat | Ab 10°C Bodentemperatur; Direktsaat 2–3 cm tief; 5 cm Reihenabstand | hoch |
| Jun | Kontrolle Knöllchen | Erste Knöllchen 2–3 Wochen nach Auflauf prüfen (rosa innen = aktiv) | mittel |
| Jul–Aug | Blüte | Stress vermeiden; gleichmäßig gießen | hoch |
| Aug | Edamame-Ernte (optional) | Hülsen voll aber Körner noch grün; 65% Wassregehalt | mittel |
| Sep–Okt | Reifeernte | Hülsen braun; Blätter abgefallen; 15% Feuchte | hoch |
| Okt–Nov | Bodenbearbeitung | Wurzelrückstände einarbeiten; N-Depot für Folgekultur | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Bohnenblattlaus | Aphis fabae | Schwarze Kolonien; Honigtau | Blatt, Trieb | Vegetativ, Blüte |
| Sojakäfer / Bohnenkäfer | Acanthoscelides obtectus | Larven in Körnern; Lagerbefall | Korn | Lager |
| Thripse | Frankliniella occidentalis | Silberflecken; Blattdeformation | Blatt, Hülse | Blüte |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; Gelbflecken | Blatt | Hitzesommer |
| Weißer Stängelälchen | Ditylenchus dipsaci | Stängelverformung; Schäden | Stängel | Sämling |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Sklerotinia-Stängelfäule | fungal (Sclerotinia sclerotiorum) | Weißer Pilzrasen; Halmfäule | feucht; Fruchtfolge |
| Sojarost | fungal (Phakopsora pachyrhizi) | Braun-orangene Pusteln; Blattfall | warm-feucht; eingeschleppt |
| Bakterielle Pusteln | bacterial (Xanthomonas axonopodis) | Gelb-braune Blattflecken | warm; Nässe |
| Saatgutfäule | fungal (Pythium, Rhizoctonia) | Auflaufschäden; Keimlingsfäule | kalter, feuchter Boden |
| Mosaik (SMV) | viral (Soybean Mosaic Virus) | Mosaikflecken; Deformation | Blattlaus-Übertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) |
|----------|---------------|-------------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse | 1–3 |
| Florfliegenlarven (Chrysoperla carnea) | Blattläuse, Thripse | 5–10 |
| Amblyseius cucumeris | Thripse | 25–50 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Thripse |
| Schmierseife | biological | Kaliumoleat | Sprühen 2–3% | 1 | Blattläuse |
| Kupferfungizid | biological/chemical | Kupferhydroxid | Sprühen | 14 | Bakterielle Pusteln |
| Fungizid (Thiophanat) | chemical | Thiophanat-methyl | Sprühen | 14 | Sklerotinia |
| Weite Fruchtfolge | cultural | — | 3–4 Jahre Pause | 0 | Sklerotinia, Sojarost |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Heterodera glycines (Sojazysten-Nematode) | Schädling (sortenabhängig) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (kein N-Dünger nötig) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide (Weizen, Mais, Gerste) |
| Empfohlene Nachfrucht | Winterweizen, Mais, Kartoffel (profitieren vom N-Depot) |
| Anbaupause (Jahre) | 3–4 Jahre auf gleichem Standort (Sklerotinia, Nematoden) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.9 | Klassisches Soja-Mais-Gemenge; Mais-Stütze; N-Transfer | `compatible_with` |
| Sorghum | Sorghum bicolor | 0.8 | Trockenheitstolerantes Gemenge | `compatible_with` |
| Saflor | Carthamus tinctorius | 0.7 | Trockentolerantes Gemenge; Insektenweide | `compatible_with` |
| Tagetes | Tagetes erecta | 0.8 | Nematoden-Hemmung; Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Knoblauch | Allium sativum | Hemmt Knöllchenbildung (antibiotische Allicin-Wirkung) | moderate | `incompatible_with` |
| Zwiebel | Allium cepa | Gleiche antibiotische Wirkung auf Rhizobien | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Gleiche Familie; Sklerotinia-Risiko; N-Konkurrenz | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Fabaceae | `shares_pest_risk` | Sklerotinia, Aphanomyces, Bohnenkäfer | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Sojabohne |
|-----|-------------------|-------------|------------------------------|
| Ackerbohne | Vicia faba | Fabaceae; kühltolerant | Winteranbau möglich; frühere Ernte |
| Lupin (Süßlupine) | Lupinus albus / mutabilis | Fabaceae; N-Fixierung | Trockentoleranter; saure Böden |
| Schwarzaugenbohne | Vigna unguiculata | Fabaceae; tropische Hülsenfrucht | Hitzestressor; trockentoleranter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Glycine max,"Sojabohne;Soya;Soybean;Soya Bean",Fabaceae,Glycine,annual,short_day,herb,taproot,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Ostasien",limited,no,limited,false,false,nitrogen_fixer,true,tender,"5;6","8;9;10","7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Sultana,Glycine max,"early;edamame;medium_plant;mitteleuropa_adapted",90,open_pollinated
Moso,Glycine max,"grain_type;high_protein;early;mitteleuropa",95,open_pollinated
ES Mentor,Glycine max,"grain_type;high_yield;maturity_group_000",100,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS — Glycine max](https://plants.usda.gov/plant-profile/GLMA4) — Taxonomie
2. [Iowa State University Extension — Soybean Production](https://crops.extension.iastate.edu/soybean) — Phasen, Nährstoffe
3. [Bayerische LfL — Sojaanbau](https://www.lfl.bayern.de/ipz/leguminosen) — Mitteleuropa-Anbau
4. [FAO Soybean Crop Profile](https://www.fao.org) — Globale Anbausysteme
5. [Donau Soja Anbauleitfaden](https://www.donausoja.org) — Praxisempfehlungen für Europa
