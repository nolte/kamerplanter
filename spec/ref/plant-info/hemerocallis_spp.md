# Taglilie — Hemerocallis spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Lubera Taglilien, Gartenratgeber Taglilien, Taglilien-Hemerocallis.de, COMPO Taglilien, Gartenjournal Taglilien düngen

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hemerocallis spp. | `species.scientific_name` |
| Volksnamen (DE/EN) | Taglilie; Daylily | `species.common_names` |
| Familie | Asphodelaceae | `species.family` → `botanical_families.name` |
| Gattung | Hemerocallis | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -35°C; in ganz Norddeutschland problemlos ohne jede Schutzmaßnahme | `species.hardiness_detail` |
| Heimat | China, Korea, Japan | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Rhizomteilung bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; essbare Knospen/Blüten in Asien) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (sortenabhängig; Früh-/Spät-/Remontierend) | `species.bloom_months` |

**Hinweis:** Jede einzelne Blüte hält nur einen Tag (daher "Taglilie"). Durch viele Blütenansätze je Stiel und remontierende Sorten kann die Blütezeit des Bestandes über 4–6 Wochen reichen.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Rhizomteilung im Frühjahr oder nach der Blüte (August). Jedes Teilstück mit mindestens 2–3 Triebknospen und Wurzeln. Alle 4–5 Jahre verjüngen — ältere Horste blühen schlechter.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile für Katzen (nephrotoxisch!) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | unbekannte Verbindungen (nephrotoxisch für Katzen) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe (für Katzen) / none (für Menschen, Hunde) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG:** Hemerocallis-Arten sind für KATZEN extrem giftig (Nierenversagen) — alle Pflanzenteile! Bei Katzenhaushalten unbedingt auf sichere Alternativen ausweichen oder Zugang unterbinden.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (Herbst nach Blüte) oder 3 (Frühjahr) | `species.pruning_months` |

**Hinweis:** Verblühte Blütenstiele entfernen. Im Herbst bodennah abschneiden oder im Frühjahr den alten Horst bereinigen. Das Laub kann für Winterschutz stehenbleiben.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–120 (sortenabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 45–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut durchlässige Gartenerde; pH 6,0–7,0; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | medium |
| Vegetatives Wachstum | 60–90 | 2 | false | false | high |
| Blüte | 30–45 | 3 | false | false | high |
| Nachblüte / Samenbildung | 30–60 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (sonnig bis halbschattig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 6.0–7.0 | 80 | 40 | — | 2 |
| Vegetativ | 1:1:1 | 1.0–1.4 | 6.0–7.0 | 100 | 50 | — | 2 |
| Blüte | 1:2:2 | 1.0–1.4 | 6.0–7.0 | 80 | 50 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

**Hinweis:** Optimales NPK-Verhältnis für Blütenentwicklung ist phosphor- und kaliumbetont (1:2:2) für Blütenbildung und Wurzelstärke.

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Stauden Langzeitdünger | Compo | organisch-mineralisch | 80–100 g/m² | April, Juni | medium_feeder |
| Blaukorn | Compo / Scotts | mineralisch | 40 g/m² | April + Juni | Schnelle Wirkung |
| Hornspäne | Oscorna | organisch | 40–60 g/m² | April | Stickstoffversorgung |
| Kompost (reif) | eigen | organisch | 3–5 L/m² | Oktober/Frühjahr | Bodenverbesserung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| April | Austrieb | Langzeitdünger oder Hornspäne | 80 g/m² | Erste Startdüngung |
| Juni | Vegetativ | Blütenfördernder Dünger (P-betont) | 40 g/m² | Blütenbildung fördern |
| Kein Dünger ab August | — | — | — | Abreife sicherstellen |

### 3.3 Besondere Hinweise zur Düngung

Taglilien sind pflegeleicht und brauchen keine intensive Düngung. Zweimalige Düngung im April und Juni reicht völlig aus. Kein Dünger im Herbst — sonst weiche Triebe mit Frostschäden. Frisch gepflanzte Knollen im ersten Jahr nur leicht düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 6.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; einmal eingewachsen sehr trockenheitstolerant; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 48 (alle 4 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Aufräumen | Altes Laub entfernen; Kompost einarbeiten | mittel |
| Apr | Düngung | Langzeitdünger oder Hornspäne | mittel |
| Jun | Nachdüngung | Phosphorbetonter Dünger | niedrig |
| Jun–Aug | Blüte | Verblühte Einzelblüten und Stiele entfernen | niedrig |
| Aug | Teilung möglich | Nach Blüte; verjüngt Horste | niedrig |
| Okt–Nov | Rückschnitt | Bodennah abschneiden; Laub kann bleiben | niedrig |
| Alle 4–5 J. | Rhizomteilung | Frühjahr oder nach Blüte; Blühleistung verbessern | mittel |

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
| Hemerocallis-Gallmücke | Contarinia quinquenotata | Verkümmerte, nicht öffnende Blüten; Madenbefall in Knospen | flower | flowering | difficult |
| Rote Spinnmilbe | Tetranychus urticae | Gelbliche Punkte auf Blättern; Gespinste | leaf | vegetative (Hitze) | medium |
| Blattläuse | Aphis spp. | Kolonien, Honigtau | shoot | vegetative (Frühjahr) | easy |
| Thripse | Thrips tabaci | Silbrige Flecken, deformierte Blüten | flower, leaf | flowering | difficult |

**Gallmücke:** Befallene Knospen sammeln und vernichten (NICHT kompostieren). Chemi: Pyrethrum bei starkem Befall.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Rost | fungal (Puccinia hemerocallidis) | Orangerote Sporenlager auf Blattunterseite | Feuchtigkeit | 7–14 | vegetative, flowering |
| Blattkrankheit (Cercospora) | fungal | Gelblich-braune Flecken | Feuchtigkeit, schlechte Luftzirkulation | 10–14 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 10–20 | 14–21 |
| Chrysoperla carnea | Blattläuse, Thripse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Befallene Knospen entfernen | cultural | — | Sofortiges Entfernen und Vernichten | 0 | Gallmücke |
| Neemöl | biological | Azadirachtin | 0.5%; abends sprühen | 3 | Spinnmilben, Blattläuse |
| Pyrethrum | biological | Pyrethrine | Sprühen bei starkem Befall | 3 | Gallmücke, Blattläuse |
| Netzschwefel | chemical | Schwefel | Sprühen | 14 | Rost |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Gartenstauden |
| Anbaupause (Jahre) | Mehrjährig; Standort 10–15 Jahre; alle 4–5 Jahre teilen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Phlox | Phlox paniculata | 0.9 | Gleiche Blütezeit; ergänzende Farben | `compatible_with` |
| Gänsekresse | Arabis caucasica | 0.8 | Polsterstaude; Lücken füllen; Frühjahrsblüher | `compatible_with` |
| Glockenblume | Campanula spp. | 0.8 | Ergänzende Blaufarben | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.8 | Bestäuber anlocken; gute Nachbarschaft | `compatible_with` |
| Taglilien-Mix | Hemerocallis-Sorten | 0.9 | Verschiedene Blütezeiten → verlängerte Blütesaison | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| — | — | Keine bekannten Unverträglichkeiten | — | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Hemerocallis spp. |
|-----|-------------------|-------------|--------------------------------------|
| Echte Lilie | Lilium spp. | Andere Familie (Liliaceae/Liliales); ähnliche Blütenform | Mehr Farbenvielfalt; aromatisch; aber aufwendiger |
| Agapanthus | Agapanthus africanus | Ähnlicher Habitus | Eleganteres Erscheinungsbild; aber weniger winterhart |
| Kniphofia | Kniphofia uvaria | Ähnlicher Habitus, schöne Blüten | Exotischer Charakter; ähnliche Pflegeanforderungen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Hemerocallis spp.,"Taglilie;Daylily",Asphodelaceae,Hemerocallis,perennial,long_day,herb,tuberous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"China, Korea, Japan",yes,20,25,100,70,50,no,yes,false,false,medium_feeder,false,hardy,"6;7;8"
```

---

## Quellenverzeichnis

1. [Lubera — Taglilien Pflege, Schneiden, Pflanzen](https://www.lubera.com/de/gartenbuch/taglilien-hemerocallis-pflege-schneiden-pflanzen-standort-p3254) — Steckbrief, Blütezeiten
2. [Gartenratgeber.net — Taglilien](https://www.gartenratgeber.net/pflanzen/taglilien.html) — NPK, Pflege
3. [Taglilien-Hemerocallis.de — Pflanzung und Pflege](https://www.taglilien-hemerocallis.de/taglilien-pflanzen.html) — Gallmücke, Schädlinge
4. [COMPO — Taglilien](https://www.compo.de/ratgeber/pflanzen/gartenpflanzen/taglilien) — Düngung
5. [Gartenjournal — Taglilien düngen](https://www.gartenjournal.net/taglilien-duengen) — NPK-Verhältnis
