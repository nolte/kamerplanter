# Geigenfeige — Ficus lyrata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Bloomscape](https://bloomscape.com/plant-care-guide/fiddle-leaf-fig/), [Planet Natural](https://www.planetnatural.com/ficus-lyrata/), [Lively Root](https://www.livelyroot.com/blogs/plant-care/ficus-lyrata-fiddle-leaf-fig-care-guide), [Soltech](https://soltech.com/products/fiddle-leaf-fig-care), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ficus lyrata | `species.scientific_name` |
| Volksnamen (DE/EN) | Geigenfeige; Fiddle Leaf Fig | `species.common_names` |
| Familie | Moraceae | `species.family` → `botanical_families.name` |
| Gattung | Ficus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 25–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 12°C, optimal 18–24°C. Extrem empfindlich gegenüber Zugluft, Temperaturwechseln und Standortwechseln — führt zu Blattabwurf. | `species.hardiness_detail` |
| Heimat | Tropisches Westafrika (Sierra Leone bis DR Kongo — Regenwaldrandstreifen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Geigenfeige ist das Lieblingskind des Interior-Design-Instagram — und gleichzeitig eine der anspruchsvollsten Zimmerpflanzen. Der häufigste Fehler: Standort wechseln. Ficus lyrata hasst Ortswechsel und quittiert jeden mit massenweisem Blattabwurf. Einmal guten Platz gefunden — nie mehr bewegen. Helles Licht ist der Schlüsselfaktor; ohne ausreichend Licht stirbt die Pflanze langsam ab.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nur in natürlichem Habitat, nicht als Zimmerpflanze) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–3 Blättern bei 24–28°C und hoher Luftfeuchtigkeit (80%+). Abmoosen (Air Layering) ist zuverlässiger: Stamm anschneiden, feuches Sphagnum-Moos mit Folie umwickeln, nach 4–8 Wochen bewurzelt. Stecklinge im Wasser funktionieren selten gut. Sehr langsame Bewurzelung.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap (Milchsaft) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | ficin, ficusin (proteolytic_enzymes), latex_sap | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft — Latexallergie-Kreuzreaktion möglich; Handschuhe beim Schneiden/Umtopfen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Nur im Frühjahr schneiden, wenn die Pflanze aktiv wächst. Schnittstellen mit Aktivkohle oder Wundverschlussmittel behandeln (Milchsaft staut sich). Topping (Haupttrieb kappen) fördert buschigen Wuchs.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 (Indoor, langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–180 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Qualitätserde mit hohem organischen Anteil. 60% Einheitserde + 20% Perlite + 20% Kokoserde. pH 6.0–7.0. Tongefäße mit guter Drainage bevorzugt. Nicht zu oft umtopfen (stresst die Pflanze). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–7.0 | 100 | 40 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15–20% Substratanteil | Umtopfen |
| Bokashi-Kompost | Eigenherstellen | organisch | 10% Substratanteil | Umtopfen/Frühjahr |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Überdüngung führt zu Blattrandnekrosen und -verbrennung. Bei Blattflecken: Dünger für 2 Monate aussetzen. Stickstoff für sattgrüne Blätter — aber maßvoll. Zu viel N macht Blätter weich und anfällig.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser. Staunässe ist tödlich. Obere 5 cm Erde sollten zwischen Güssen antrocknen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Standort prüfen | Licht ausreichend? Ggf. Pflanzenlampe ergänzen | hoch |
| Mär | Düngung starten | Erste Düngergabe nach Winterpause | mittel |
| Apr | Umtopfen (falls nötig) | Nur bei wurzelgebunden, max. 2 cm größerer Topf | mittel |
| Apr | Blätter reinigen | Feuchtes Tuch — verstopfte Stomata hemmen Photosynthese | mittel |
| Mai–Sep | Regelmäßig gießen | Nie austrocknen lassen, nie Staunässe | hoch |
| Sep | Düngung beenden | — | niedrig |
| Okt–Feb | Weniger gießen | Substrat zwischen Güssen deutlich abtrocknen | hoch |
| Ganzjährig | Standort NICHT wechseln | Kritischste Pflegemaßnahme | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, gelbe Tupfen, trockene Blätter | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Stängeln | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Wolkenartige Fliegen beim Schütteln, Honigtau | easy |
| Blattlaus | Aphididae | Kolonien an Triebspitzen, Honigtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule (Phytophthora, Pythium) | fungal | Welke trotz feuchter Erde, schwarze Wurzeln, Blattverlust | Staunässe, schlechte Drainage |
| Bakterielle Blattflecken | bacterial | Braune, wässrige Flecken mit gelbem Hof | Nasses Laub, hohe Feuchtigkeit |
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Trockene Luft + feuchte Blätter |
| Physiologische Chlorose | physiological | Gelbe Blätter bei grünen Adern | Fe/Mg-Mangel, falscher pH |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10–20 | 14–21 |
| Cryptolaemus montrouzieri | Schmierlaus | 2–5 | 21–28 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | — | Wattestäbchen | 0 | Schildlaus, Schmierlaus |
| Insektizidseife | biological | Kaliseife | Sprühen | 3 | Blattläuse, Weiße Fliege |
| Drainage verbessern | cultural | — | Substrat + Topf wechseln | 0 | Wurzelfäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Birkenfeige | Ficus benjamina | Gleiche Gattung | Kleiner, anpassungsfähiger |
| Gummibaum | Ficus elastica | Gleiche Gattung | Robuster, weniger lichtbedürftig |
| Monstera | Monstera deliciosa | Großblättrig, tropisch | Deutlich pflegeleichter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Ficus lyrata,"Geigenfeige;Fiddle Leaf Fig",Moraceae,Ficus,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Tropisches Westafrika",yes,10-30,30,150-300,80-180,yes,no,false,medium_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Bambino,Ficus lyrata,"ornamental;compact;dwarf",clone
Little Fiddle,Ficus lyrata,"ornamental;compact",clone
```

---

## Quellenverzeichnis

1. [Bloomscape — Fiddle Leaf Fig](https://bloomscape.com/plant-care-guide/fiddle-leaf-fig/) — Pflegehinweise
2. [Planet Natural — Ficus lyrata](https://www.planetnatural.com/ficus-lyrata/) — Kulturdaten, Schädlinge
3. [Lively Root — Fiddle Leaf Fig](https://www.livelyroot.com/blogs/plant-care/ficus-lyrata-fiddle-leaf-fig-care-guide) — Lichtanforderungen
4. [Soltech — Fiddle Leaf Fig Care](https://soltech.com/products/fiddle-leaf-fig-care) — Lichtbedarf
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
