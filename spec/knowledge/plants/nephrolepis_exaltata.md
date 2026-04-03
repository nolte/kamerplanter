# Schwertfarn — Nephrolepis exaltata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/boston-fern-nephrolepis-exaltata-bostoniensis/), [Our Houseplants](https://www.ourhouseplants.com/plants/boston-fern), [Gardenia.net](https://www.gardenia.net/plant/nephrolepis-exaltata), [BBC Gardeners World](https://www.gardenersworld.com/house-plants/how-to-grow-boston-fern/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Nephrolepis exaltata | `species.scientific_name` |
| Volksnamen (DE/EN) | Schwertfarn, Bostonfarn; Boston Fern, Sword Fern | `species.common_names` |
| Familie | Nephrolepidaceae | `species.family` → `botanical_families.name` |
| Gattung | Nephrolepis | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Wurzelanpassungen | stoloniferous (Ausläufer) | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart. Mindesttemperatur 5°C (Zimmerhaltung), optimal 16–24°C. Verträgt kurze Kälte bis 2°C, aber keine Dauertemperaturen unter 10°C. | `species.hardiness_detail` |
| Heimat | Tropisches und subtropisches Amerika, Westafrika, Ozeanien — feuchte Wälder und Bachränder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.8 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, xylene, toluene, benzene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Bostonfarn (*N. exaltata* 'Bostoniensis') ist eine der häufigsten Zimmerpflanzen weltweit und war in der NASA Clean Air Study einer der effektivsten Luftreiniger. Entscheidend ist absolute Luftfeuchtigkeitsstabilität — Heizungsluft (20–30% RH) tötet die Pflanze langfristig. Die häufigste Todesursache von Farnen in Innenräumen ist zu trockene Luft.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt (Sporenvermehrung sehr langsam) | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farne blühen nicht — Sporenbildung) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, offset, spore | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Einfachste Methode: Teilung beim Umtopfen — je 3–5 Wedel mit eigenem Wurzelballen. Ausläufer (Stolonenb) entwickeln sich an der Pflanzenbasis und können als eigenständige Pflanzen abgetrennt werden. Sporenvermehrung ist möglich, aber sehr zeitaufwendig (12+ Monate).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Sporen können Allergien auslösen) | `species.allergen_info.pollen_allergen` |

**Hinweis:** Farne gehören zu den haustierfreundlichsten Zimmerpflanzen. Für Pollenallergiker kann Sporenwolken beim Bewegen der Pflanze problematisch sein.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3 | `species.pruning_months` |

**Hinweis:** Gelbe und abgestorbene Wedel regelmäßig entfernen. Im Frühling Pflanze auf 5–10 cm zurückschneiden um dichten Neuwuchs anzuregen — Pflanze treibt zuverlässig neu aus.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 (Wedel hängen über den Topfrand) | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer, Halbschatten, windgeschützt; regelmäßiges Gießen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut wasserhaltige aber lockere Erde. Torffreie Variante: Kokosfaser + Perlite + Kompost (2:1:1). pH 5.0–6.5 (leicht sauer!). Ampelkultivierung beliebt. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 14–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.0–6.5 | 60 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 5.0–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L (halbe Dosis) | Wachstum |
| Farn-Dünger | Compo | base | 7-3-6 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost (reif) | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |
| Wurmhumus | Eigenherstellung | organisch | 15% | Umtopfen |

### 3.2 Besondere Hinweise

Farne sind Schwachzehrer. Nur halbierte Normaldosis verwenden. April bis September alle 4 Wochen. Kein Dünger Oktober bis März. Stickstoffbetonte Formel für dichtes, grünes Laub.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.8 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water (gleichmäßig, Substrat stets feucht halten) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser oder abgestandenes Leitungswasser. Regenwasser ideal. Kein kalkreiches Leitungswasser (Blattspitzennekrosen). | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 10 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Rückschnitt | Auf 5–10 cm zurückschneiden (fördert dichten Neuwuchs) | mittel |
| Mär | Umtopfen | Bei Bedarf in nächstgrößeren Topf | mittel |
| Apr | Düngung starten | Erste schwache Düngergabe | mittel |
| Apr–Sep | Gießen | Substrat gleichmäßig feucht; nie austrocknen lassen | hoch |
| Ganzjährig | Luftfeuchte | Luftbefeuchter; Kiesschale; Badezimmer geeignet | hoch |
| Sep | Düngung beenden | Letzte Düngergabe | niedrig |
| Okt–Mär | Weniger gießen | Substrat leicht trocknen lassen | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben (bei trockener Luft) | leaf | medium |
| Schildlaus | Coccus hesperidum | Braune, flache Schalen auf Wedelstielen | stem, leaf | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken an Wedelstiel-Ansätzen | stem | easy |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | root | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braun-verfärbte Wedel, fauler Geruch | Staunässe |
| Blattnekrose | physiologisch | Braune Blattspitzen/-ränder | Zu trockene Luft, Kalk im Gießwasser |
| Botrytis | fungal | Grauer Schimmel auf Wedeln | Schlechte Luftzirkulation, stagnierende Luft |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Befeuchter, Kiesschale | 0 | Spinnmilbe (Prävention) |
| Neemöl (vorsichtig) | biological | Schwach verdünnt, 0.3% — erst an einzelnem Wedel testen! | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |
| Drainage verbessern | cultural | Untersetzer leeren nach Gießen | 0 | Wurzelfäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Calathea | Goeppertia spp. | 0.8 | Ähnliche Feuchtigkeitsanforderungen |
| Spathiphyllum | Spathiphyllum wallisii | 0.8 | Gleiche Humidität, gegenseitige Luftbefeuchtung |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Venushaarfarn | Adiantum raddianum | Gleiche Ordnung | Zierlicher, für Badezimmer ideal |
| Hirschzungenfarn | Asplenium scolopendrium | Gleiche Ordnung | Robuster, verträgt weniger Luftfeuchte |
| Platycerium | Platycerium bifurcatum | Gleiche Ordnung (Epiphyt) | Wanddekoration möglich, epiphytisch |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Nephrolepis exaltata,"Schwertfarn;Bostonfarn;Boston Fern;Sword Fern",Nephrolepidaceae,Nephrolepis,perennial,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b","Tropisches Amerika",yes,3-15,15,30-90,60-150,yes,yes,false,light_feeder,0.8
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Bostoniensis,Nephrolepis exaltata,"ornamental;arching_fronds",clone
Fluffy Ruffles,Nephrolepis exaltata,"ornamental;compact;double_fronds",clone
Tiger Fern,Nephrolepis exaltata,"ornamental;variegated;yellow_green",clone
```

---

## Quellenverzeichnis

1. [Wisconsin Horticulture Extension — Boston Fern](https://hort.extension.wisc.edu/articles/boston-fern-nephrolepis-exaltata-bostoniensis/) — Kulturdaten, Humidität
2. [Our Houseplants](https://www.ourhouseplants.com/plants/boston-fern) — Pflege, Schädlinge
3. [BBC Gardeners World — Boston Fern](https://www.gardenersworld.com/house-plants/how-to-grow-boston-fern/) — Praxishinweise
4. [Gardenia.net](https://www.gardenia.net/plant/nephrolepis-exaltata) — Taxonomische Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
