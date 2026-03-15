# Kulturapfel — Malus domestica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-Kölle Apfelbaum, Compo Apfelbaum, Bio-Gärtner Apfelbäume, Naturadb Malus domestica

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Malus domestica | `species.scientific_name` |
| Volksnamen (DE/EN) | Kulturapfel, Apfelbaum, Apfel; Apple, Domestic Apple | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Malus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; Knospen frostempfindlich bei Spätfrost (-3 bis -5°C); in Norddeutschland Spätfrostlagen meiden; geschützte Sorten wählen | `species.hardiness_detail` |
| Heimat | Kasachstan (Wildform: Malus sieversii); Europa/Asien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Pflanzung als Containerbaum oder wurzelnackt; Herbst Oktober–November oder Frühjahr März–April) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9, 10, 11 (je nach Sorte: Frühsorten Juli/Aug; Spät-/Lagersorten Nov) | `species.harvest_months` |
| Blütemonate | 4, 5 | `species.bloom_months` |

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
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Kerne (Amygdalin → Blausäure; normale Menge unbedenklich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Amygdalin in Kernen (Apfelkerne in normalen Mengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Birkenpollenallergikern: Kreuzreaktion; OAS = Oral Allergy Syndrome) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Kahl-Schnitt im Winter; vor Austrieb) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 100–200 (Säulenapfel: 50–80 L) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 60 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 300–800 (je nach Unterlage; Zwergunterlage M9: 250–300 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–600 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 300–500 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (Spalierform: ja) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche Obstbaumerde; pH 5,5–6,5; gut drainiert; Schicht Kies am Boden | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 120–180 | 1 | false | false | high |
| Knospenauftrieb | 14–28 | 2 | false | false | low |
| Blüte | 10–21 | 3 | false | false | low |
| Fruchtentwicklung | 60–120 | 4 | false | false | medium |
| Reife | 14–28 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (Regen reicht meist; bei Trockenheit gießen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20000–50000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |
| Knospenauftrieb | 2:1:1 | — | 5.5–6.5 | 100 | 40 | — | 3 |
| Fruchtentwicklung | 1:2:2 | — | 5.5–6.5 | 150 | 60 | — | 3 |
| Reife | 0:1:2 | — | 5.5–6.5 | 100 | 40 | — | 2 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Obstbaumdünger organisch | Neudorff Azet | organisch | 100–150 g/m² Kronenfläche | März + Jul/Aug | Apfel, Birne, Pflaume |
| Kompost | eigen | organisch | 5–8 L/m² | Herbst/Frühjahr | alle |
| Hornspäne | Oscorna | organisch-N | 60–80 g/m² Kronenfläche | März | Frühjahrs-Trieb |

#### Mineralisch (ergänzend)

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Obstbaum-Dünger | Compo | mineralisch | 8-5-14 | 1 | Vegetativ |
| Bittersalz | — | Mg | 0-0-0+16Mg | 2 | Mg-Mangel |

### 3.2 Besondere Hinweise zur Düngung

Düngung ab März (Austrieb) und zweite Gabe Juli/August (Fruchtentwicklung). KEINE Düngung nach August — verhindert Holzreife und führt zu Frostschäden. Bei Kaliummangel platzen Früchte auf. Magnesium-Mangel zeigt sich als Scheckigkeit (Gelbblättrigkeit). Apfelbäume auf schwachen Unterlagen (M9) haben höheren Nährstoffbedarf.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14 (Jungbäume häufiger; Altbäume Regenabhängig) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Feuchte; Trockenheit in Fruchtphase → Fruchtfall; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 120 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Winterschnitt | Lichter Krone: Überkreuzendes Holz raus; Wassertriebe entfernen | hoch |
| Mär | Erste Düngung | Obstbaumdünger + Kompost | mittel |
| Apr–Mai | Blütenspritzung | Schorfschutz-Präventivspritzung wenn nötig | hoch |
| Jun | Junifruchtfall abwarten | Natürlicher Fruchtfall; dann ausdünnen auf 1 Frucht/Fruchtspur | mittel |
| Jul/Aug | Zweite Düngung | Obstbaumdünger | niedrig |
| Aug–Nov | Ernte | Sortentypisch; kein zu frühes Ernten | hoch |
| Nov | Mulchen | Kompost unter Krone einarbeiten | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Apfelwickler | Cydia pomonella | Maden im Kerngehäuse | fruit | fruiting | difficult |
| Apfelblütenstecher | Anthonomus pomorum | Nicht aufgehende Blüten (braun) | flower | flowering | medium |
| Blutlaus | Eriosoma lanigerum | Wolliges Gebilde an Rindenwunden | stem, bark | vegetative | easy |
| Frostspanner | Operophtera brumata | Lochfraß junger Blätter | leaf | vegetative | medium |
| Mehlige Apfelblattlaus | Dysaphis plantaginea | Rosarote Kolonien; Blattrollungen | leaf, shoot | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Apfelschorf | fungal (Venturia inaequalis) | Dunkelbraune Flecken; rissige Früchte | Feuchtigkeit bei Austrieb | 7–14 | vegetative, fruiting |
| Echter Mehltau | fungal (Podosphaera leucotricha) | Weißer Belag auf Jungtrieben | Trockenheit + Wärme | 5–10 | vegetative |
| Monilia-Fruchtfäule | fungal (Monilinia fructigena) | Braune Fäulnis mit Sporenringen | Fruchtläsionen | 3–7 | fruiting, ripening |
| Feuerbrand | bacterial (Erwinia amylovora) | Welke Triebe; Blüten braun; "Schäferhaken" | Wärme + Feuchtigkeit | 5–10 | flowering |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Meisen-Nistkasten | Apfelwickler, Frostspanner | 1–2 Kästen/Baum | — |
| Trichogramma | Apfelwickler-Eier | Karten-Aufhängung | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Wellpappe-Ringe | cultural | — | Fangring am Stamm (Aug–Sep) | 0 | Apfelwickler-Puppen |
| Kaolin-Spritzung | cultural | Kaolin | Weiße Schutzschicht | 0 | Apfelwickler, Blütenstecher |
| Granuloseviruspräparat (Madex) | biological | Cydia-Granulosevirus | Sprühen ab Eiablage | 0 | Apfelwickler |
| Kupfer-Kalk | chemical | Kupfer | Frühjahrsspritzung | 7 | Apfelschorf |
| Schwefelkalk | chemical | Ca-Polysulfide | Vor Austrieb | 14 | Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kernobst (Rosaceae) |
| Empfohlene Vorfrucht | — (Standzeit 40–80 Jahre) |
| Empfohlene Nachfrucht | Nach Rodung: mind. 5 Jahre Pause; Bodenaustausch bei Neupflanzung (Apfelmüdigkeit!) |
| Anbaupause (Jahre) | 10+ Jahre nach Rodemüdigkeit |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Apfelschorf-Vorbeugung (traditionell) | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.8 | Schädlingsabwehr; Bestäuber | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Ablenkung | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr am Stammfuß | `compatible_with` |
| Phacelia | Phacelia tanacetifolia | 0.8 | Bestäuber anlocken (Blütezeit Synergie) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Wacholde | Juniperus spp. | Zwischenwirt Birnengitterrost (Gymnosporangium spp.) | moderate | `incompatible_with` |
| Nussbaum | Juglans regia | Juglone-Ausscheidung hemmt Wachstum | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Apfelbaum |
|-----|-------------------|-------------|------------------------------|
| Birne | Pyrus communis | Kernobst, Rosaceae | Unterschiedliche Sorten; früherer Ertrag |
| Quitte | Cydonia oblonga | Kernobst | Robuster; weniger Schorfanfällig |
| Holunder | Sambucus nigra | Heimisches Gehölz | Pflegeleichter; Mehrwert Bienen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Malus domestica,"Kulturapfel;Apfelbaum;Apple;Domestic Apple",Rosaceae,Malus,perennial,long_day,tree,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Kasachstan, Europa",limited,150,60,800,600,400,no,limited,false,false,medium_feeder,hardy,"7;8;9;10;11","4;5",winter_pruning,"2;3"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Elstar,Malus domestica,sweet_tart;classic;high_yield,140,,open_pollinated
Cox Orange,Malus domestica,aromatic;classic;susceptible_scab,150,,open_pollinated
Holsteiner Cox,Malus domestica,regional_north_germany;large_fruit,155,,open_pollinated
Boskoop,Malus domestica,late;storage;tart,160,scab_tolerant,open_pollinated
Rewena,Malus domestica,scab_resistant;robust;organic,140,scab_resistant,open_pollinated
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle Apfelbaum](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-apfelbaum-richtig/) — Pflege, Düngung
2. [Compo Apfelbaum](https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/apfelbaum) — Anbau, Pflege
3. [Bio-Gärtner Apfelbäume](https://www.bio-gaertner.de/pflanzen/Apfelbaeume) — Ökologischer Anbau, Schädlinge
4. [Naturadb Malus domestica](https://www.naturadb.de/pflanzen/malus-domestica/) — Steckbrief
