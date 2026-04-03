# Herbstanemone — Anemone hupehensis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-Kölle Herbstanemone, Lubera Herbstanemone, Naturadb Anemone hupehensis, Plantura Herbstanemonen, Gartenjournal Herbstanemone

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Anemone hupehensis | `species.scientific_name` |
| Volksnamen (DE/EN) | Herbstanemone, Chinesische Herbstanemone; Japanese Anemone | `species.common_names` |
| Familie | Ranunculaceae | `species.family` → `botanical_families.name` |
| Gattung | Anemone | `species.genus` |
| Ordnung | Ranunculales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | In den ersten 2–3 Jahren Frostschutz nötig; danach winterhart bis -20°C; in etabliertem Zustand problemlos in Norddeutschland | `species.hardiness_detail` |
| Heimat | China (Provinz Hubei) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Rhizomteilung bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Schnittblume möglich) | `species.harvest_months` |
| Blütemonate | 8, 9, 10 | `species.bloom_months` |

**Hinweis:** Die Herbstanemone ist eine der wichtigsten Spätsommerstauden — blüht wenn viele andere Stauden schon verblüht sind. Ideal für Naturgärten und Bienenweide bis Oktober.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Rhizomteilung im Frühjahr oder Herbst. Die Art breitet sich durch Ausläufer aus — kann als Bodendecker eingesetzt werden, aber auch invasiv werden. Wurzelstecklinge 5–8 cm lang im Winter möglich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile, besonders frische Pflanzenteile | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Protoanemonin (Ranunculaceae-typisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Beim Arbeiten Handschuhe tragen — Saft verursacht Hautreizungen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3 (Frühjahr vor Austrieb) | `species.pruning_months` |

**Hinweis:** Im Herbst NICHT schneiden — das alte Laub bietet natürlichen Winterschutz für junge Pflanzen. Im Frühjahr vor dem Neuaustrieb bodennah zurückschneiden. Verblühte Stiele können im Herbst nach dem ersten Frost entfernt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 (breitet sich aus) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut feuchtigkeitsspeichernde Erde; pH 6,0–7,0; keine Staunässe | — |

**Standort:** Halbschatten bis Schatten; bevorzugt unter Gehölzen; verträgt auch sonnige Standorte mit ausreichend Feuchte.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum | 90–120 | 2 | false | false | medium |
| Blüte | 45–60 | 3 | false | false | high |
| Nachblüte / Abreife | 20–30 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 (Halbschatten bis Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 (Kurztagspflanze für Blühinduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 2:1:1 | 0.6–1.0 | 6.0–7.0 | 80 | 40 | — | 2 |
| Vegetativ | 2:1:2 | 0.8–1.2 | 6.0–7.0 | 100 | 50 | — | 2 |
| Blüte | 1:2:2 | 0.8–1.2 | 6.0–7.0 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Stauden Langzeitdünger | Compo | organisch-mineralisch | 60–80 g/m² | April | medium_feeder |
| Hornspäne | Oscorna | organisch | 30–50 g/m² | April | Stickstoffversorgung |
| Kompost (reif) | eigen | organisch | 3–4 L/m² | März/Oktober | Bodenverbesserung |
| Blaukorn | Compo/Scotts | mineralisch | 30–40 g/m² | April + Juni | Schnelle Wirkung |

### 3.2 Besondere Hinweise zur Düngung

Einmalige organische Düngung im Frühjahr (April) reicht für die gesamte Saison aus. Zweite Gabe im Juni möglich (bis Ende Juli). Kein Dünger im Herbst. Im Topf alle 3–4 Wochen leicht flüssig düngen (Mai bis Juli).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 8.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Bodenfeuchte; kein Staunässe; in Trockenperioden regelmäßig gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 (alle 3 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Rückschnitt | Altes Laub bodennah entfernen | mittel |
| Apr | Düngung | Hornspäne + Kompost; junge Pflanzen: Winterschutz entfernen | mittel |
| Apr–Mai | Schneckenschutz | Frische Austriebe schützen | hoch |
| Aug–Okt | Blüte | Regelmäßig gießen bei Trockenheit | mittel |
| Nov | Winterschutz (Jungpflanzen) | Erste 2–3 Jahre: Reisig/Laub über Rhizome legen | hoch |
| Alle 3–5 J. | Rhizomteilung | Frühjahr; Ausläufer kontrollieren | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (Freiland) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

**Hinweis:** Nur in den ersten 2–3 Jahren nach der Pflanzung braucht die Herbstanemone Frostschutz. Danach vollständig winterhart in Norddeutschland. Schutz: Laub, Reisig oder Stroh über die Wurzeln legen.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schnecken | Arion rufus | Fraß an frischen Austrieben; Schleimspuren | shoot | Frühjahrsaustrieb | easy |
| Blattläuse | Aphis spp. | Selten; Kolonien an Triebspitzen | shoot | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Rhizomfäule | fungal (Phytophthora) | Welken; braune, faulige Rhizome | Staunässe | 14–21 | alle |
| Echter Mehltau | fungal | Weißer Belag (selten) | Trockenheit + Wärme | 7–10 | vegetative (Spätsommer) |

**Hinweis:** Herbstanemonen sind insgesamt sehr robust und kaum krankheitsanfällig. Staunässe ist die häufigste Ursache für Probleme.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinmehl (als Schneckenschutz) | Schnecken | Rand-Ausbringen | sofort |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schneckenkorn (Eisenphosphat) | biological | Eisen(III)-phosphat | 3–5 g/m² streuen | 0 | Schnecken |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |
| Bessere Drainage | cultural | — | Substrat verbessern; keine Mulde | 0 | Rhizomfäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Gartenstauden |
| Anbaupause (Jahre) | Mehrjährig; Standort 10+ Jahre; alle 3–5 Jahre teilen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Hosta | Hosta spp. | 0.9 | Gleiche Standortansprüche (Halbschatten, Feuchtigkeit) | `compatible_with` |
| Farn | Dryopteris filix-mas | 0.9 | Gleicher Schattenstandort; ergänzende Texturen | `compatible_with` |
| Astilbe | Astilbe chinensis | 0.8 | Gleiche Blütezeit; ergänzende Farben | `compatible_with` |
| Sedum | Hylotelephium spectabile | 0.7 | Blütezeit ergänzend; gleiche Blütefenster Herbst | `compatible_with` |
| Echinacea | Echinacea purpurea | 0.8 | Bestäuber fördern; ergänzende Farben | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| — | — | Keine bekannten Unverträglichkeiten | — | — |

**Hinweis:** Auf Ausbreitung achten — Herbstanemone kann sich durch Rhizome stark ausbreiten und schwächere Nachbarn verdrängen.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Anemone hupehensis |
|-----|-------------------|-------------|--------------------------------------|
| Hybridherbstanemone | Anemone x hybrida | Hybriden aus A. hupehensis + A. vitifolia | Größere Blüten; mehr Sorten; ähnliche Kultur |
| Rudbeckia | Rudbeckia fulgida | Ähnlicher Blütezeitraum (Herbst) | Trockenheitstoleranter; keine Toxizität |
| Sedum | Hylotelephium spectabile | Ähnliche Herbstblüte | Sehr pflegeleicht; kein Frostschutz nötig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Anemone hupehensis,"Herbstanemone;Chinesische Herbstanemone;Japanese Anemone",Ranunculaceae,Anemone,perennial,short_day,herb,rhizomatous,"5a;5b;6a;6b;7a;7b;8a;8b",0.0,"China (Hubei)",yes,15,25,100,70,50,no,limited,false,false,medium_feeder,false,half_hardy,"8;9;10"
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle — Herbst-Anemone](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-herbst-anemone-richtig/) — Pflege
2. [Lubera — Herbstanemone Pflege](https://www.lubera.com/de/gartenbuch/herbstanemone-pflege-standort-ueberwintern-p2774) — Standort, Überwintern
3. [Naturadb — Anemone hupehensis](https://www.naturadb.de/pflanzen/anemone-hupehensis/) — Steckbrief
4. [Plantura — Herbstanemonen](https://www.plantura.garden/blumen-stauden/anemonen/herbstanemonen) — Sorten, Pflege
5. [Gartenjournal — Herbstanemone](https://www.gartenjournal.net/herbstanemone) — Pflegetipps
