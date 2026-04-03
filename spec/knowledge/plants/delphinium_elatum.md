# Rittersporn — Delphinium elatum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Delphinium elatum, Plantura Rittersporn, Pflanzen-Kölle Rittersporn, Baldur-Garten Rittersporn

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Delphinium elatum | `species.scientific_name` |
| Volksnamen (DE/EN) | Hoher Rittersporn, Garten-Rittersporn; Garden Delphinium, Candle Delphinium | `species.common_names` |
| Familie | Ranunculaceae | `species.family` → `botanical_families.name` |
| Gattung | Delphinium | `species.genus` |
| Ordnung | Ranunculales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–7b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; in Norddeutschland absolut winterhart; empfindlich gegen Spätfröste nach frühem Austrieb | `species.hardiness_detail` |
| Heimat | Gebirge Eurasiens (Alpen, Sibirien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 9 (Frischabsaat bevorzugt) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Samen giftig) | `species.harvest_months` |
| Blütemonate | 6, 7 (erste Blüte), 8, 9 (Zweitblüte nach Rückschnitt) | `species.bloom_months` |

**Hinweis Aussaat:** Samen verliert schnell Keimfähigkeit — möglichst frisch aussäen (max. 1 Jahr). Dunkelkeimer. Kaltstratifikation 1–2 Wochen im Kühlschrank verbessert Keimrate deutlich.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | ALLE Pflanzenteile (besonders Samen und Jungpflanzen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Diterpenoid-Alkaloide vom Norditerpene-Typ (Methyllycaconitin, Delphinin, Delsolin, Ajaconin) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Hautirritation bei manchen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Warnung:** Stark giftig — kann tödlich sein. Handschuhe bei der Arbeit mit der Pflanze. Besonders Kinder und Tiere schützen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (nach Erstblüte), 11 (Herbstschnitt) | `species.pruning_months` |

**Schnittkonzept:** Nach der ersten Blüte (Juli) auf 25–30 cm zurückschneiden → zweite Blüte im August/September. Im Herbst bodennah kürzen und leicht mulchen. Im Frühjahr altes Material entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 (Hybriden bis 200 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–80 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (hohe Rispen windbruchgefährdet; Staudenringe oder Bambusstäbe nötig) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, humusreiche, tiefgründige Erde; pH 6,5–7,5; gut wasserhaltend | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–21 | 1 | false | false | low |
| Sämling/Jungpflanze | 42–60 | 2 | false | false | low |
| Vegetatives Wachstum | 42–70 | 3 | false | false | medium |
| Erste Blüte | 28–42 | 4 | false | false | medium |
| Regeneration nach Rückschnitt | 21–35 | 5 | false | false | medium |
| Zweitblüte | 21–35 | 6 | false | false | medium |
| Winterruhe | 120–150 | 7 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Sämling | 1:1:1 | 0.5–0.8 | 6.5 | 60 | 30 | – | 1 |
| Vegetativ | 3:1:2 | 1.2–1.6 | 6.5–7.0 | 130 | 60 | – | 3 |
| Blüte | 1:2:2 | 1.4–1.8 | 6.5–7.0 | 150 | 70 | – | 2 |
| Regeneration | 2:1:2 | 1.0–1.4 | 6.5–7.0 | 120 | 60 | – | 2 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland, empfohlen)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Volldünger organisch | Neudorff Bio-Trissol | organisch | 80–100 g/m² | Frühjahr | heavy_feeder |
| Hornspäne | Oscorna | organisch | 80–120 g/m² | März–April | N-Grundversorgung |
| Kompost | eigen | organisch | 4–5 L/m² | März, Oktober | Bodenverbesserung |
| Blumendünger flüssig | Substral | organisch-mineral | 20 ml/10L alle 14 Tage | April–September | Topfkultur |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| März–April (Austrieb) | N-betont | Hornspäne + Kompost | je 80 g/m² + 4L/m² | Vor Stützen setzen |
| nach Blüte (Jul) | ausgewogen | Flüssigdünger | 14-täglich | Für zweite Blüte |
| Oktober | K-betont | Kompost | 3L/m² | Wintervorbereitung; KEIN N |

### 3.3 Besondere Hinweise zur Düngung

Rittersporn ist Starkzehrer und braucht reiche Böden. Vor dem Einpflanzen Boden gut mit Kompost anreichern (2–3 Schaufeln/Pflanzloch). Auf sandigen Norddeutschen Böden regelmäßige organische Grundversorgung nötig. Überdüngung mit N fördert weiche Triebe (Schneckenbefall, Windbruch). Ausgewogene Versorgung führt zu kompakteren, stärkeren Trieben.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; gleichmäßige Feuchte; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wegen Schnecken!) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Rückschnitt/Aufräumen | Alte Triebe entfernen; Schneckenbarriere legen | hoch |
| Mär–Apr | Düngung | Hornspäne + Kompost; einarbeiten | hoch |
| Apr | Stützen aufstellen | Staudenringe bei 20–25 cm Höhe; VOR Windschäden | hoch |
| Jun–Jul | Erste Blüte | Blütenstiele einzeln ausbinden bei Bedarf | mittel |
| Jul | Rückschnitt nach Blüte | Auf 25–30 cm; zweite Blüte fördern | hoch |
| Aug–Sep | Zweitblüte | Oft weniger üppig; Düngung unterstützt | mittel |
| Nov | Herbstschnitt | Bodennah; Mulchen mit Kompost | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schnecken | Arion spp. | Fraß an Jungpflanzen und Trieben | leaf, shoot | seedling, spring | easy |
| Blattläuse | Aulacorthum solani | Kolonien; Honigtau | shoot | vegetative | easy |
| Tausendfüßler | Blaniulus guttulatus | Fraß an Wurzeln | root | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal (Erysiphe spp.) | Weißer Belag auf Blättern | Trockenheit + warm | 5–10 | vegetative (Spätsommer) |
| Bakterienschwärze | bacterial (Pectobacterium carotovorum) | Schwarze, feuchte Faulstellen am Stängel | Kälte, Feuchtigkeit | 3–7 | spring, flowering |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel | Feuchte, dichter Stand | 3–7 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Laufkäfer | Schnecken, Larven | Natürlich fördern | – |
| Marienkäfer | Blattläuse | Freilassen | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schneckenkorn (Eisen-III-Phosphat) | biological | Eisenphosphat | Ausstreuen abends | 0 | Schnecken |
| Schmierseife | biological | Kaliumpalmitat | 1% sprühen | 1 | Blattläuse |
| Befallene Triebe sofort entfernen | cultural | – | Vernichten | 0 | Bakterienschwärze |
| Kupferfungizid | chemical | Kupferhydroxid | Sprühen bei Befallsdruck | 7 | Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Staude (Dauerkultur) |
| Anbaupause (Jahre) | Alle 4–5 Jahre teilen und verjüngen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Schwertlilie | Iris germanica | 0.8 | Gleiche Saison; ergänzende Höhe | `compatible_with` |
| Storchschnabel | Geranium spp. | 0.8 | Bodendecker; schützt Fußbereich | `compatible_with` |
| Schafgarbe | Achillea millefolium | 0.7 | Robuste Nachbarschaft; Nützlinge | `compatible_with` |
| Glockenblume | Campanula persicifolia | 0.8 | Gleiche Blütezeit; blaues Farbspiel | `compatible_with` |
| Lupine | Lupinus polyphyllus | 0.8 | Gleiche Saison; N-Fixierer | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Flammenblume | Phlox paniculata | Wurzelkonkurrenz; unterirdische Schäden | moderate | `incompatible_with` |
| Astern | Aster spp. | Wurzelkonkurrenz | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Delphinium elatum |
|-----|-------------------|-------------|-------------------------------------|
| Delphinium-Pacific-Hybriden | Delphinium × cultorum | Hybride Zuchtform | Üppigere Blüten; Farbvielfalt |
| Rittersporn einjährig | Consolida ajacis | Gleiche Familie | Selbstaussäend; leichter zu kultivieren |
| Akelei | Aquilegia vulgaris | Gleiche Familie | Anspruchsloser; selbstaussäend; weniger giftig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Delphinium elatum,"Hoher Rittersporn;Garten-Rittersporn;Garden Delphinium",Ranunculaceae,Delphinium,perennial,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b",0.0,"Gebirge Eurasiens",limited,25,40,200,80,70,no,limited,false,true,heavy_feeder,false,hardy,"6;7;8;9"
```

---

## Quellenverzeichnis

1. [Naturadb Delphinium elatum](https://www.naturadb.de/pflanzen/delphinium-elatum/) — Steckbrief, Winterhärte
2. [Plantura Rittersporn](https://www.plantura.garden/blumen-stauden/rittersporn/rittersporn-pflanzenportrait) — Portrait, Toxizität
3. [Pflanzen-Kölle Rittersporn Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-rittersporn-richtig/) — Pflege
4. [Baldur-Garten Rittersporn](https://www.baldur-garten.de/onion/content/pflege-tipps/gartenstauden/rittersporn) — Schnitt, Mischkultur
