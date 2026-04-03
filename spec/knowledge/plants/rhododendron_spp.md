# Rhododendron — Rhododendron spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Deutsche Rhododendron-Gesellschaft, Lubera Rhododendron düngen, Plantura Rhododendron düngen, Pflanzen-Kölle Rhododendron, Love the Garden Rhododendron

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rhododendron spp. | `species.scientific_name` |
| Volksnamen (DE/EN) | Rhododendron, Alpenrose; Rhododendron | `species.common_names` |
| Familie | Ericaceae | `species.family` → `botanical_families.name` |
| Gattung | Rhododendron | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b (sortenabhängig) | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Viele Sorten winterhart bis -25°C; Spätfrostgefahr für Knospen! Norddeutschland Zone 7b–8a: geeignet mit windgeschütztem Standort | `species.hardiness_detail` |
| Heimat | Asien (Himalaya, China), Amerika, Europa | `species.native_habitat` |
| Allelopathie-Score | -0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis:** Rhododendron hat ausgeprägte Allelopathie durch Phenole — Bodenanreicherung mit Laubabwurf hemmt Nachbarpflanzen unter dem Strauch.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge oder Kauf als Containerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 4, 5, 6 (sortenabhängig; Einjährig-Frühblüher April, Hauptblüte Mai) | `species.bloom_months` |

**WICHTIG für Norddeutschland:** Spätfrostgefahr nach den Eisheiligen (Mitte Mai) kann Knospen schädigen. Spätblühende Sorten oder geschützter Standort wählen.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Stecklinge im Sommer (Juli/August); Bewurzelung dauert 6–12 Monate. Absenker einfacher. Aussaat extrem langsam (5–10 Jahre bis zur Blüte). Kauf als Containerpflanze empfohlen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile, besonders Blätter | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Grayanotoxine (Andromedotoxine), Arbutin | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG:** Alle Pflanzenteile stark giftig (Grayanotoxine wirken auf Herzmuskel und Nervensystem).

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (direkt nach der Blüte) | `species.pruning_months` |

**Hinweis:** Rhododendron bildet Knospen auf altem Holz — Schnitt NUR direkt nach der Blüte (Mai/Juni). Nicht im Winter oder Spätsommer schneiden. Verwelkte Blüten ("Verblühtes auslichten") sofort entfernen, um Kraft für neue Knospen zu sparen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 35 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 50–300 (sortenabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–300 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80–200 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Saure Rhododendronerde; pH 4,0–5,5; torfarme Alternative: Nadelerde + Kokosfaser + Perlite; KEIN Kalk! | — |

**pH-KRITISCH:** pH >6,0 führt zu Chlorose (Eisenmangel). Regelmäßig pH messen!

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | low |
| Blüte | 21–42 | 2 | false | false | low |
| Vegetatives Wachstum | 60–90 | 3 | false | false | medium |
| Knospendifferenzierung (Sommer) | 60–90 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 (Halbschatten; kein direktes Mittagssonnen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Blüte | 1:2:1 | 0.6–1.0 | 4.0–5.5 | 50 | 30 | — | 3 |
| Vegetativ/Knospendiff. | 1:1:1 | 0.6–1.0 | 4.0–5.5 | 60 | 40 | — | 3 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

**WARNUNG:** KEIN Kalk, KEIN kalkhaltiger Dünger, KEIN Leitungswasser in Kalkregionen → Chlorose!

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Spezialdünger Rhododendron

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Rhododendron Langzeitdünger | Compo | mineralisch-sauer wirkend | 80–100 g/m² | Mai + August | Ansäuernde Wirkung |
| Lubera Rhododendron Dünger | Lubera | organisch-mineralisch | nach Herstellerangabe | Mai + August | light_feeder |
| Schüco Azaleen-Dünger | Schüco | mineralisch | nach Herstellerangabe | Mai + August | Azaleen, Rhododendron |
| Gebrauchte Kaffeesätze | — | organisch | 50–100 g/m² | monatlich | pH-Absenkung |
| Regenwasser | — | Wasser | — | ganzjährig | KEIN Leitungswasser in Kalkregionen |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| Mai | Nach Blüte | Rhododendron-Langzeitdünger | 80 g/m² | Erste Düngung NACH der Blüte, nicht davor |
| August | Knospendiff. | Rhododendron-Dünger (Herbsttypus mit P+K) | einmalig | Letzte Düngung bis Ende August! |
| KEIN Dünger | Ab September | — | — | Sonst keine Knospendifferenzierung |

### 3.3 Besondere Hinweise zur Düngung

Rhododendron ist ein Schwachzehrer — zu viel Dünger schadet. Düngung ERST nach der Blüte (Mai/Juni), NICHT davor. Kein Dünger nach Ende August. Leitungswasser mit hohem Kalkgehalt unbedingt vermeiden — Regenwasser oder entkalktes Wasser verwenden.

**Chlorose-Behandlung:** Bei gelblichen Blättern (Eisen-/Mangan-Mangel durch zu hohen pH): Flüssiges Eisenchelat sprühen + pH des Substrats senken (Schwefelsäure in Gießwasser: 1 ml 96%ige Schwefelsäure auf 10 L Wasser).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | KEIN hartes Leitungswasser; Regenwasser bevorzugt; pH des Wassers maximal 6,0; weiches Wasser zwingend | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr–Mai | pH-Kontrolle | Boden-pH messen; ggf. ansäuern | hoch |
| Mai–Jun | Blüte | Verblühte Blütenstände ausbrechen (nicht schneiden!) | hoch |
| Mai | Düngung 1 | Rhododendron-Langzeitdünger | mittel |
| Aug | Düngung 2 | Letzte Düngung; P+K-betont | mittel |
| Aug | Gießkontrolle | Trockenstress vermeiden — Knospen fallen sonst | hoch |
| Nov | Wintervorbereitung | Mulchen; Windschutz für empfindliche Sorten | mittel |
| Ganzjährig | Wasser-Qualität | Nur Regenwasser oder weiches Wasser | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

**Hinweis:** Rhododendron im Winter an frostklaren Sonnentagen gießen (Frosttrockne vermeiden). Windschutz durch Vlies bei empfindlichen Sorten. Kübelpflanzen an frostfreien Ort stellen (unbeheiztes Gewächshaus; Garage) oder tief einwickeln.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Rhododendron-Zikade | Graphocephala fennahi | Blattflecken; überträgt Knospenfäule | leaf | vegetative (Aug–Sep) | medium |
| Dickmaulrüssler | Otiorhynchus sulcatus | Buchtige Blattrandfraßstellen; Larven fressen Wurzeln | leaf, root | ganzjährig | medium |
| Rhododendron-Spinnmilbe | Oligonychus ilicis | Rötliche Verfärbung; Gespinste | leaf | vegetative (Hitze/Trockenheit) | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Rhododendron-Knospenfäule | fungal (Seifertia azaleae, übertragen durch Zikade) | Knospen werden braun, trocknen ein | Zikaden-Befall im Sommer | — | Herbst (Erscheinung) |
| Phytophthora-Wurzelfäule | fungal-like (Phytophthora cinnamomi) | Welken; braune Wurzeln; Absterben | Staunässe | 14–28 | alle |
| Chlorose | Physiologisch (Fe, Mn Mangel) | Blätter vergilben zwischen grünen Blattadern | pH zu hoch | — | alle |

**Zikade → Knospenfäule:** Zikade bekämpfen (Insektizid Juli–September) = Knospenfäule verhindern!

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Heterorhabditis bacteriophora | Dickmaulrüssler-Larven | nach Herstellerangabe | 7–14 (>12°C Bodentemperatur) |
| Phytoseiulus persimilis | Spinnmilbe | 10–20 | 14–21 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gelbtafeln | cultural | — | Aufhängen Juli–September | 0 | Rhododendron-Zikade fangen |
| Neemöl | biological | Azadirachtin | 0.5% sprühen; abends | 3 | Zikade, Spinnmilbe |
| Nematoden (Heterorhabditis) | biological | Nematoden | Gießen auf Boden | 0 | Dickmaulrüssler-Larven |
| Eisenchelat | biological | Fe-EDTA / Fe-EDDHA | Flüssig sprühen oder gießen | 0 | Chlorose |
| Drainage verbessern | cultural | — | Bodenlockerung; Hochbeet | 0 | Phytophthora-Vorbeugung |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Moorbeetsträucher |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Astilbe | Astilbe chinensis | 0.9 | Gleiche pH-Ansprüche; Halbschatten | `compatible_with` |
| Heidelbeere | Vaccinium corymbosum | 0.9 | Gleiche saure Bodenbedingungen (pH 4–5) | `compatible_with` |
| Farn | Dryopteris filix-mas | 0.8 | Gleicher Halbschatten-Standort | `compatible_with` |
| Pieris | Pieris japonica | 0.9 | Gleiche Ericaceae-Familie; gleiche Bedingungen | `compatible_with` |
| Hosta | Hosta spp. | 0.8 | Gleicher Halbschatten; toleriert leicht sauren Boden | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kalksträucher (Flieder, Forsythie) | Syringa, Forsythia | Entgegengesetzte pH-Ansprüche (Rhodo: sauer; diese: neutral/basisch) | severe | `incompatible_with` |
| Gemüsekulturen (allgemein) | diverse | Allelopathische Wirkung durch Rhododendron-Blattabfall | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Ericaceae | `shares_pest_risk` | Dickmaulrüssler, Phytophthora | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Rhododendron spp. |
|-----|-------------------|-------------|--------------------------------------|
| Pieris | Pieris japonica | Ericaceae; ähnliche Standortansprüche | Dekoratives Frühjahrsaustrieb rot; ähnlich pflegend |
| Lorbeer-Rose | Kalmia latifolia | Ericaceae; ähnlich | Einheimischer in NA; exotische Blüten |
| Azalee (laubwerfend) | Rhododendron luteum | Gleiches Genus; laubabwerfend | Wunderschöner Herbstfarbe; herrlicher Duft |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Rhododendron spp.,"Rhododendron;Alpenrose",Ericaceae,Rhododendron,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",-0.3,"Asien, Amerika, Europa",yes,40,35,200,200,120,no,yes,false,false,light_feeder,false,hardy,"4;5;6"
```

---

## Quellenverzeichnis

1. [Deutsche Rhododendron-Gesellschaft](https://www.rhodo.org/wissenswertes) — Wissenswertes, Zikade, Knospenfäule
2. [Lubera — Rhododendron düngen](https://www.lubera.com/de/gartenbuch/rhododendron-duengen-p4888) — Düngung, pH
3. [Plantura — Rhododendron düngen](https://www.plantura.garden/gehoelze/rhododendron/rhododendron-duengen) — Dünger, Zeitpunkt
4. [Pflanzen-Kölle — Rhododendron](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-rhododendron-richtig/) — Dickmaulrüssler, Schnitt
5. [Love the Garden — Rhododendron Pflege](https://www.lovethegarden.com/de-de/artikel/rhododendron-pflege) — Standort, Chlorose
