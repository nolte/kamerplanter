# Schwarzer Holunder — Sambucus nigra

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-Kölle Holunder, LWG Bayern Holunder, Native Plants Sambucus nigra, DCM Holunder

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Sambucus nigra | `species.scientific_name` |
| Volksnamen (DE/EN) | Schwarzer Holunder, Fliederbeere, Hollerbusch; Black Elderberry, Elder | `species.common_names` |
| Familie | Adoxaceae | `species.family` → `botanical_families.name` |
| Gattung | Sambucus | `species.genus` |
| Ordnung | Dipsacales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; in Norddeutschland absolut winterhart; wächst heimisch | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Westasien; heimisch in Deutschland | `species.native_habitat` |
| Allelopathie-Score | -0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge; Samen Kälteperiode nötig) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7 (Holunderblüten), 8, 9, 10 (Beeren vollreif, August–Oktober) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (cremeweißer Duft; Phänologischer Indikator für Maisanbau) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true (rohe Beeren und alle anderen Pflanzenteile außer Blüten) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Blätter, Rinde, Wurzeln; rohe unreife Beeren; Kerne | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Sambunigin, Sambunigrin (Cyanogene Glykoside); Sambucin (Rinde) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (rohe Beeren: Übelkeit, Erbrechen; gekocht unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Holunderpollen sind häufiges Allergen) | `species.allergen_info.pollen_allergen` |

**Wichtige Hinweise:**
- Reife schwarze Beeren MÜSSEN erhitzt werden (Saft, Marmelade) — roh giftig
- Blüten können roh als Holunderblütensirup oder Holunderküchle verwendet werden
- Blüten-Zeitraum Phänologischer Indikator: Holunderblüte = Mais aussäen (Bauernregel)

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (vor Austrieb) | `species.pruning_months` |

**Hinweis:** Holunder verträgt harte Rückschnitte gut. Für kompaktere Wuchsform alljährlich stark zurückschneiden. Für Beernertrag: nur auslichten, nicht zurückschneiden (blüht an Vorjahrestrieben). Für Holunderblütensirup: Blütenstände regelmäßig ernten fördert Neubildung.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 50–80 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–700 (je nach Schnitt) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–500 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–400 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, humusreiche, feuchte Erde; pH 5,5–7,0; verträgt auch feuchte Standorte | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | medium |
| Triebwachstum/Blattentfaltung | 28–42 | 2 | false | false | high |
| Blüte (Holunderblüten) | 21–35 | 3 | false | true | high |
| Fruchtentwicklung | 60–90 | 4 | false | false | high |
| Ernte (Beeren) | 21–42 | 5 | false | true | high |
| Winterruhe | 90–120 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte & Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 5000–15000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahr/Auswuchs | 2:1:2 | 1.0–1.4 | 5.5–7.0 | 100 | 50 | – | 2 |
| Blüte | 1:2:2 | 1.0–1.4 | 5.5–7.0 | 100 | 50 | – | 2 |
| Fruchtentwicklung | 1:1:3 | 0.8–1.2 | 5.5–7.0 | 100 | 50 | – | 1 |
| Herbst | 0:1:2 | 0.5–0.8 | – | – | – | – | – |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Obstbaum- oder Gehölzdünger | Neudorff Bio | organisch | 60–80 g/m² | Frühjahr | medium_feeder |
| Kompost | eigen | organisch | 4–6 L/m² | März, Oktober | Bodenverbesserung |
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März | N-Grundversorgung |

### 3.2 Besondere Hinweise zur Düngung

Holunder ist ausgesprochen genügsam. Auf nährstoffreichen Gartenböden ist oft keine Düngung nötig. Wächst natürlich an stickstoffreichen Standorten (Komposthaufen, Stallmist, Wegränder). Kompost-Mulch im Frühjahr und Herbst ausreichend. Organische Düngung bevorzugen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; verträgt auch feuchte Standorte; mag gleichmäßige Feuchtigkeit | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 (1–2× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–5 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Winterschnitt | Vor Austrieb; Formschnitt oder Auslichten | mittel |
| Mär | Düngung | Kompost + Hornspäne | niedrig |
| Jun | Blütenernten | Dolden abschneiden für Sirup/Frittieren | mittel |
| Aug–Okt | Beernernten | Wenn Beeren tief schwarz; gesamte Rispen abschneiden | hoch |
| Okt | Kompost-Mulch | Schützende Schicht um den Strauch | niedrig |

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
| Holunderblattlaus | Aphis sambuci | Dichte Kolonien an Triebspitzen; Triebe deformieren | shoot | spring | easy |
| Kirschessigfliege | Drosophila suzukii | Einstiche in reifende Beeren; Fäulnis | fruit | fruiting | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Virosen | viral (diverse) | Mosaik, Chlorose | Blattläuse, Werkzeug | – | alle |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 5–10 | vegetative |
| Grauschimmel (Früchte) | fungal (Botrytis) | Faulige Rispen | Feuchte nach Reife | 3–7 | fruiting |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |
| Marienkäfer | biological | natürlich | Fördern | 0 | Blattläuse |
| Befallene Triebe entfernen | cultural | – | Sofort | 0 | Virosen |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Narzissen | Narcissus spp. | 0.7 | Frühjahrsblüte vor Holunder-Laubaustrieb | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Soll Blattläuse abschrecken | `compatible_with` |
| Brennnessel | Urtica dioica | 0.7 | Nützlingsförderung (Schmetterlingspflanzen) | `compatible_with` |

### 6.2 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Waldhimbeere | Rubus idaeus | Holunder überbietet durch schnelles Wachstum | mild | `incompatible_with` |
| Gemüsebeete direkt daneben | diverse | Beschattung; Wurzelkonkurrenz | moderate | `incompatible_with` |

---

## 7. Phänologische Bedeutung

| Phänologisches Ereignis | Bedeutung für Garten |
|------------------------|---------------------|
| Holunderblüte (Frühsommer, Anfang Juni) | Traditionelle Aussaatzeit für Mais; Bodentemperatur ausreichend |
| Holunderbeerenreife (Spätsommer) | Herbstarbeiten beginnen; letzte Ernte-Saison |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Sambucus nigra,"Schwarzer Holunder;Fliederbeere;Hollerbusch;Black Elderberry",Adoxaceae,Sambucus,perennial,long_day,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",-0.2,"Europa, Nordafrika, Westasien",limited,65,50,700,500,300,no,no,false,false,medium_feeder,false,hardy,"5;6;7"
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle Holunder](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-holunder-richtig/) — Pflege, Schnitt
2. [LWG Bayern Schwarzer Holunder](https://www.lwg.bayern.de/gartenakademie/gartendokumente/infoschriften/085865/index.php) — Fachliches Steckbrief
3. [Native Plants Sambucus nigra](https://www.native-plants.de/1293/schwarzer-holunder) — Wildpflanzen-Steckbrief
4. [DCM Holunder im Garten](https://cuxin-dcm.de/hobby/gartentipps/holunder-im-garten-sorten-pflege-ernte-rezepte-so-gelingt-der-anbau) — Ernte, Sorten
