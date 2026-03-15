# Pflaume — Prunus domestica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartenrat.de Pflaumenbaum, Lubera Pflaumenbaum, Gartenfreunde Pflaumen, Green24 Pflaumenbaum NPK

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Prunus domestica | `species.scientific_name` |
| Volksnamen (DE/EN) | Pflaume, Zwetschge; Plum, European Plum | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Prunus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4b–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Blüten (März–April) sehr frostempfindlich (-1°C); Norddeutschland geeignet | `species.hardiness_detail` |
| Heimat | Kultivierter Hybrid (wahrscheinlich Vorderasien/Kaukasus) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (veredelte Baumschulware) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9, 10 (je nach Sorte) | `species.harvest_months` |
| Blütemonate | 3, 4 (Spätfrostgefahr beachten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | grafting | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (Früchte; Kerne meiden) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Kerne (Amygdalin → Blausäure), Blätter | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Amygdalin (Cyanogenes Glycosid) in Kernen | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (Früchte sicher; Kerne nicht zerkauen) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzreaktion mit Birkenpollenallergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 8, 9 (nach Ernte; kein Winterschnitt — Schnittfäule) | `species.pruning_months` |

**KRITISCH:** Pflaumen NIEMALS im Winter schneiden — Scharkavirus (PPV) und Holzfäule dringen durch Wunden ein. Schnitt immer nach der Ernte (August–September) oder bei Sommerverhältnissen. Leitastschnitt in den ersten 3 Jahren für offene Krone.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 50–100 (nur Säulensorten) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 300–800 (je nach Unterlage) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 300–600 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 400–500 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreicher, kalkfreundlicher, humoser Boden; pH 6,0–7,5; gute Drainage | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Frühling) | 14–21 | 1 | false | false | low |
| Fruchtansatz | 28–42 | 2 | false | false | medium |
| Fruchtentwicklung | 60–90 | 3 | false | false | medium |
| Ernte-/Reifephase | 14–28 | 4 | false | true | high |
| Triebwachstum/Holzreife | 60–90 | 5 | false | false | high |
| Winterruhe | 90–120 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 30–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 10000–25000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Jungbaum (Aufbau) | 3:1:2 | 1.2–1.6 | 6.0–7.0 | 120 | 60 | – | 3 |
| Blüte | 1:3:2 | 1.0–1.4 | 6.0–7.0 | 140 | 70 | – | 2 |
| Fruchtentwicklung | 2:2:3 | 1.2–1.6 | 6.0–7.0 | 160 | 80 | – | 3 |
| Reife/Ernte | 1:1:2 | 0.8–1.2 | 6.0–7.0 | 120 | 60 | – | 2 |
| Triebwachstum/Holzreife | 1:1:3 | 0.8–1.2 | 6.0–7.0 | 100 | 50 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Obstbaum-Dünger | Compo Bio Obstbaum | organisch | 80–100 g/m² | März, Mai | medium_feeder |
| Hornspäne | Oscorna | organisch | 80–120 g/m² | März | N-Grundversorgung |
| Kompost | eigen | organisch | 5–8 L/m² | März, Oktober | Bodenverbesserung |
| Kaliumsulfat | Hauert | mineral | 40 g/m² | August | Fruchtqualität, Holzreife |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----------|-----------------|--------|
| NPK Obstbaum-Dünger | Substral Compo | mineral | 60–80 g/m² | 1 | März |
| Bittersalz (MgSO4) | Hauert | mineral | 20 g/m² | 2 | Bei Mg-Mangel (Chlorose) |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| März (Vegetationsbeginn) | N-ausgewogen | Hornspäne + Kompost | 100 g/m² + 6L/m² | Vor Blüte |
| Mai (nach Fruchtansatz) | P/K | Obstbaum-Dünger | 70 g/m² | Fruchtentwicklung fördern |
| August (nach Ernte) | K-betont | Kaliumsulfat | 40 g/m² | Holzreife; KEIN N mehr! |

### 3.3 Besondere Hinweise zur Düngung

Pflaumen sind empfindlicher als andere Obstbäume gegenüber Nährstoffüberdosierung. Zu viel N produziert weiches Holz und erhöht das Risiko von Kragenfäule und Gummifluss. Kein Stickstoff nach Juli. Bodenanalyse alle 3–4 Jahre empfehlenswert.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt; Regenwasser ideal; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 (2–3× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Erste Düngung | Hornspäne + Kompost vor Blüte | hoch |
| Mär–Apr | Blüte beobachten | Frostschutz bei Spätfrostwarnung (-1°C kritisch) | hoch |
| Mai | Zweite Düngung | Obstdünger nach Fruchtansatz | hoch |
| Mai–Jun | Fruchtausdünnung | Früchte auf 8–10 cm Abstand reduzieren (Regelmäßigkeit; Alternanz) | mittel |
| Jul–Okt | Ernte | Je nach Sorte; bei weicher Reife ernten | hoch |
| Aug | Schnitt nach Ernte | Auslichten; kranke Äste entfernen; Sommerwunden heilen besser | hoch |
| Aug | Letzte Kali-Düngung | Holzreife sichern | mittel |
| Nov | Scharka-Kontrolle | Auf Scharkavirus-Symptome achten (gelbe Ringe auf Früchten) | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Pflaumenwickler | Cydia funebrana | Madige Früchte; Larven in Frucht | fruit | fruiting | medium |
| Pflaumensägewespe | Hoplocampa flava | Vorzeitig fallende Früchte; Fraßgänge | fruit | fruiting | medium |
| Blattläuse | Brachycaudus helichrysi | Eingerollte Blätter; klebrige Ausscheidungen | leaf, shoot | spring | easy |
| Frostspanner | Operophtera brumata | Kahlfraß im Frühjahr | leaf | spring | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Scharkavirus (PPV) | viral (Plum Pox Virus) | Gelbe Ringe/Muster auf Früchten; Chlorose | Blattläuse übertragen | — | alle (latent) |
| Monilia-Fruchtfäule | fungal (Monilinia laxa) | Braune Fäule auf Früchten; Mumienfröchte | Feuchte, Wunden | 5–10 | fruiting |
| Kräuselkrankheit | fungal (Taphrina pruni) | Deformierte, aufgedunsene Früchte | Nässe im Frühjahr | 10–21 | spring |
| Schrotschusskrankheit | fungal (Stigmina carpophila) | Löcher in Blättern (wie Schrot) | Feuchtigkeit | 7–14 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Trichogramma-Schlupfwespen | Pflaumenwickler (Eier) | 3–5 Karten/Baum | sofort |
| Leimring | Frostspanner | 1 Ring/Stamm (Oktober) | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Trichogramma | biological | Parasitoide Wespe | Eiablage-Zeitpunkt | 0 | Pflaumenwickler |
| Leimring | cultural | Klebstoff | Am Stamm Oktober–März | 0 | Frostspanner |
| Kupferfungizid | chemical | Kupferhydroxid | Herbst (Laubfall) + Frühjahr | 7 | Schrotschuss, Monilia |
| Befallene Bäume roden | cultural | – | Bei Scharkavirus: sofort melden und roden | 0 | Scharkavirus |

**Wichtiger Hinweis:** Scharkavirus (PPV) ist eine meldepflichtige Pflanzenkrankheit in Deutschland. Befallene Bäume müssen gerodet werden. Resistente Sorten bevorzugen.

### 5.5 Resistenzen

| Sorte/Resistenz | Typ | Hinweis |
|----------------|-----|---------|
| 'Tegera' (Scharkatolerant) | Virus | Reduzierter PPV-Befall |
| 'Jojo' (Scharkafest) | Virus | Empfohlen für Deutschland |
| 'Ortenauer' | Monilia-tolerant | Weniger anfällig |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Dauergehölz (Rosaceae/Steinobst) |
| Anbaupause (Jahre) | 5+ Jahre Pflaume/Kirsche nach Pflaume (Bodenermüdung) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Lavendel | Lavandula angustifolia | 0.8 | Bestäuber; Schädlingsabwehr | `compatible_with` |
| Borretsch | Borago officinalis | 0.7 | Bestäuberanlocken | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Aphiden-Falle; Bodendecker | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematodenabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kirsche | Prunus avium | Scharkavirus-Übertragung möglich; geteilte Schädlinge | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Geteilte Bodenerkrankungen | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Rosaceae (Steinobst) | `shares_pest_risk` | PPV (Scharkavirus), Monilia, Spinnmilben | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Prunus domestica |
|-----|-------------------|-------------|-------------------------------------|
| Mirabelle | Prunus domestica subsp. syriaca | Gleiche Art | Kleinfrüchtig; robuster; alternanzarm |
| Reneklode | Prunus domestica subsp. italica | Gleiche Art | Fruchtig; frühreifend |
| Kirschpflaume | Prunus cerasifera | Gleiche Gattung | Sehr früh; winterhart; schön blühend |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Prunus domestica,"Pflaume;Zwetschge;Plum",Rosaceae,Prunus,perennial,long_day,tree,fibrous,"4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Vorderasien, Kultivierter Hybrid",limited,75,50,800,600,450,no,limited,false,false,medium_feeder,false,hardy,"3;4"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Jojo,Prunus domestica,,,"scharkafest;mittelspät",,,vegetatively_propagated
Tegera,Prunus domestica,,,"scharkafest;Topsorte",,,vegetatively_propagated
Hauszwetschge,Prunus domestica,,,"klassisch;spät;blau",,,vegetatively_propagated
Elena,Prunus domestica,,,"groß;frühreifend",,,vegetatively_propagated
```

---

## Quellenverzeichnis

1. [Gartenrat.de Pflaumenbaum](https://gartenrat.de/pflaumenbaum/) — Anbau, Pflege, Schnitt
2. [Lubera Pflaumenbaum pflanzen](https://www.lubera.com/de/gartenbuch/pflaumenbaum-zwetschgenbaum-pflanzen-p2252) — Pflanzung, Kulturdaten
3. [Gartenfreunde Pflaumen](https://www.gartenfreunde.de/gartenpraxis/pflanzenportraets/pflaumen-im-garten/) — Sorten, Krankheiten
4. [Gartenratgeber.net Pflaumenbaum](https://www.gartenratgeber.net/pflanzen/pflaumenbaum.html) — Allgemeine Pflege
