# Forsythie — Forsythia × intermedia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Forsythia × intermedia, Plantura Forsythie, Pflanzen-Kölle Forsythie, Lubera Forsythien

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Forsythia × intermedia | `species.scientific_name` |
| Volksnamen (DE/EN) | Forsythie, Goldflieder; Border Forsythia | `species.common_names` |
| Familie | Oleaceae | `species.family` → `botanical_families.name` |
| Gattung | Forsythia | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Blütenknospen in strengen Wintern schädigt (unter -25°C); in Norddeutschland absolut winterhart | `species.hardiness_detail` |
| Heimat | Hybrid aus China/Korea-Arten; kultiviert seit 19. Jh. | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklingsvermehrung) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Phänologischer Indikator — Frühlingsbote) | `species.harvest_months` |
| Blütemonate | 3, 4 (vor dem Laubaustrieb — gelbe Blüten am kahlen Holz) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 (direkt nach der Blüte) | `species.pruning_months` |

**KRITISCH:** Forsythie blüht am vorjährigen Holz (Triebe des Vorjahres tragen die Blütenknospen). Schnitt IMMER direkt nach der Blüte (April/Mai). Schnitt im Herbst oder Winter entfernt die bereits angelegten Blütenknospen → keine Blüte im Folgejahr. Alle 2 Jahre altes Holz bodennah kappen für Verjüngung.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 150–250 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 150–200 (Hecke: 100 cm Pflanzabstand) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, humusreiche Erde; pH 6,0–7,5; durchlässig; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Frühjahr) | 14–28 | 1 | false | false | medium |
| Triebwachstum (Sommer) | 90–120 | 2 | false | false | high |
| Knospenanlage (Herbst) | 60–90 | 3 | false | false | high |
| Winterruhe | 90–120 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Triebwachstum (Sommer — für nächste Blüte entscheidend)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Blüte | 0:1:1 | 0.8–1.2 | 6.5–7.0 | 80 | 40 | – | 1 |
| Triebwachstum | 2:1:2 | 1.0–1.4 | 6.5–7.0 | 100 | 50 | – | 2 |
| Knospenanlage | 1:1:3 | 0.8–1.2 | 6.5–7.0 | 80 | 50 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 3–5 L/m² | Mai (nach Blüte), Oktober | Bodenverbesserung |
| Stauden- und Gehölzdünger | Neudorff Bio | organisch | 60–80 g/m² | Mai | medium_feeder |
| Hornspäne | Oscorna | organisch | 50–70 g/m² | Mai | N-Triebwachstum |
| Kaliumsulfat | Hauert | mineral | 30 g/m² | September | K-Winterhärtung |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| Mai (direkt nach Blüte) | N-betont | Hornspäne + Kompost | 60 g/m² + 3L/m² | Fördert neue Triebe für Blüte nächstes Jahr |
| September | K-betont | Kaliumsulfat | 30 g/m² | Kein N — Holzreife sicherstellen |

### 3.3 Besondere Hinweise zur Düngung

Forsythie braucht nur 1–2× jährlich Düngung. Wichtig: Die neuen Triebe, die nach der Blüte wachsen, tragen im nächsten Jahr die Blütenknospen — gute Stickstoffversorgung direkt nach der Blüte fördert kräftige neue Triebe und damit die Folgeblüte.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; verträgt Trockenheit gut nach Etablierung | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 120 (1–2× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Freilandgehölz) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Blüte beobachten | Phänologischer Indikator: Forsythienblüte = Kartoffeln legen | niedrig |
| Apr–Mai | Rückschnitt NACH Blüte | Alte Holz alle 2 Jahre bodennah; Formschnitt bei Hecken | hoch |
| Mai | Düngung | Hornspäne + Kompost direkt nach Schnitt | hoch |
| Sep | Herbst-Kaliumgabe | Kaliumsulfat für Holzreife | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis gossypii | Kolonien an Triebspitzen | shoot | vegetative | easy |
| Blattkäfer | Chrysomelidae spp. | Löcher in Blättern (Fensterfraß) | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 7–10 | vegetative (Spätsommer) |
| Monilia-Zweigsterben | fungal (Monilia spp.) | Welkende Triebe | Feuchte nach Blüte | 7–14 | flowering |
| Forsythiengallmücke | Contarinia spp. | Gallen auf Knospen | – | 14–21 | spring |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Befallene Triebe entfernen | cultural | – | Sofort | 0 | Monilia, Gallen |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse, Blattkäfer |
| Kupferfungizid | chemical | Kupferhydroxid | Vor Blüte bei Befallsgeschichte | 7 | Monilia |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Narzissen | Narcissus spp. | 0.9 | Klassische Frühjahrskombination | `compatible_with` |
| Tulpen | Tulipa spp. | 0.9 | Blühen zur gleichen Zeit; optisch harmonisch | `compatible_with` |
| Haselnuss | Corylus avellana | 0.7 | Ergänzende Strauchschicht | `compatible_with` |
| Flieder | Syringa vulgaris | 0.7 | Folgeblüte; ergänzt Saisonabfolge | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Forsythia × intermedia |
|-----|-------------------|-------------|------------------------------------------|
| Schneeforsythie | Abeliophyllum distichum | Verwandt; weiße Blüten | Weiße Variante; seltener; Rarität |
| Koreanische Forsythie | Forsythia ovata | Gleiche Gattung | Kompakter; Blütenknospen frosthartes |
| Zaubernuss | Hamamelis mollis | Ähnliche Blütezeit | Herbst-/Winterblüte zusätzlich; Duft |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Forsythia × intermedia,"Forsythie;Goldflieder;Border Forsythia",Oleaceae,Forsythia,perennial,long_day,shrub,fibrous,"5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Kultivierter Hybrid",limited,40,40,300,250,150,no,limited,false,false,medium_feeder,false,hardy,"3;4"
```

---

## Quellenverzeichnis

1. [Naturadb Forsythia × intermedia](https://www.naturadb.de/pflanzen/forsythia-x-intermedia/) — Steckbrief, Winterhärte
2. [Plantura Forsythie](https://www.plantura.garden/gehoelze/forsythie/schneeforsythie) — Pflege, Schnitt
3. [Pflanzen-Kölle Forsythie](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-forsythie-richtig/) — Pflege, Düngung
4. [Lubera Forsythien](https://www.lubera.com/de/gartenbuch/forsythien-p2431) — Anbau, Vermehrung
