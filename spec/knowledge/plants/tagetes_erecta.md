# Aufrechte Studentenblume — Tagetes erecta

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Royal Horticultural Society, University of Florida IFAS Extension, USDA PLANTS Database, Rodale Institute Companion Planting, Colorado State University Extension

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tagetes erecta | `species.scientific_name` |
| Volksnamen (DE/EN) | Aufrechte Studentenblume, Afrikanische Studentenblume, Azteken-Ringelblume; African Marigold, Aztec Marigold, Big Marigold | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Tagetes | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b (als Einjährige in 2a–11b kultivierbar) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; stirbt bei Frost; in Mitteleuropa als robuste einjährige Sommerblume nach letztem Frost (Mitte Mai) bis Oktober; selbstaussaat in milden Wintern möglich | `species.hardiness_detail` |
| Heimat | Mexiko, Mittelamerika (Azteken-Kulturpflanze) | `species.native_habitat` |
| Allelopathie-Score | 0.5 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**IPM-Schlüsselpflanze:** Tagetes erecta ist eine der wichtigsten Begleitpflanzen im Gemüsegarten. Alpha-Terthienyl in den Wurzeln hemmt Wurzel-Nematoden (Meloidogyne spp.) wirksam — nachgewiesen in Feldversuchen. Blüten-Duftstoffe (Terpengemisch) wirken auf viele Schädlinge abstoßend oder verwirrend. Blüten locken Schwebefliegen, Marienkäfer und andere Nützlinge an.

**Allelopathie:** Positiver Allelopathie-Score — Tagetes fördert viele Nachbarn durch Schädlingsabwehr, hemmt aber einige empfindliche Arten (Hülsenfrüchte, Kohl in sehr dichter Nachbarschaft).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Anzucht im Warmhaus ab März) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 7–14 (Direktsaat einfach; warm genug) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Vorkultur); 5, 6 (Direktsaat Freiland) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Schnittblumen 6–10; Blüten essbar) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Blüten essbar; in der Küche als Safran-Ersatz und Salatzugabe verwendet) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Alpha-Terthienyl (nematodenfeindlich; in Wurzeln; kein Risiko für Menschen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Pyrethrum-Verwandtschaft; Asteraceae-Allergen; manche Personen reagieren auf Hautkontakt) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Korbblütler-Pollen; mäßig; August-Oktober) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Deadheading; verblühte Köpfe entfernen verlängert Blütezeit) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–40 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr lichtbedürftig; kaum Indoor möglich ohne Kunstlicht) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, leicht sandige Erde; pH 6,0–7,5; verträgt schwere Böden schlecht; Perlite-Anteil 15–20% | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 14–28 | 3 | false | false | high |
| Knospenansatz | 14–21 | 4 | false | false | high |
| Hauptblüte | 60–120 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 (Lichtkeimer; Licht hilfreich) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | >13 (lange Tage verhindern vorzeitige Blüte; Kurztagblüher) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptblüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | ≤13 (kürzere Tage ab August; Blüteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.6 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.5 | — | — |
| Sämling | 1:1:1 | 0.4–0.8 | 6.0–7.5 | 50 | 20 |
| Vegetativ | 2:1:1 | 0.6–1.0 | 6.0–7.5 | 70 | 25 |
| Blüte | 1:2:2 | 0.8–1.4 | 6.0–7.5 | 70 | 30 |

**Hinweis:** Tagetes ist ein Leichtezer — zu viel Dünger (v.a. N) erzeugt viel Blattwerk auf Kosten der Blüten. Lieber wenig düngen; Blütenqualität wichtiger als Wachstum.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Sämling | time_based | 5–10 Tage; Keimblätter sichtbar |
| Sämling → Vegetativ | time_based | 14–21 Tage; 2 echte Blattpaare |
| Vegetativ → Blüte | event_based | Kurztagbedingungen (≤13h) oder Pikierung/Auspflanzung Stress |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Blumendünger flüssig | Compo | Flüssig | 6-3-6 | 5 ml/L alle 2 Wochen | Blüte |
| Osmocote 3–4 Monate | Osmocote | Slow-Release | 14-13-13 | 3–5 g/L Substrat | Pflanzung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee | eigen | flüssig organisch | 1:10; 2×/Monat | Jun–Sep |
| Hornmehl | diverse | organisch | 2–3 g/L Substrat | Substrat-Mix |

### 3.2 Besondere Hinweise zur Düngung

Weniger ist mehr bei Tagetes. Gut angereicherte Gartenerde oder Kompost-basiertes Substrat reichen oft ohne Nachdüngung aus. Wöchentliche Flüssigdüngung im Balkonkasten sinnvoll (Auswaschung durch Gießen). Hohe P/K-Ratio fördert Blütenreichtum. Überdüngung mit N führt zu üppigem grünen Wachstum ohne Blüten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig; kein Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkwasser verträglich; pH-Toleranz bis 7,5 | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Anzucht | Im Warmhaus; 20–25°C; Direktsaat auf Substrat; 1 cm Erde; Licht | hoch |
| Apr–Mai | Pikierung / Abhärtung | In Einzel-Töpfe pikieren; langsam abhärten | mittel |
| Mai | Auspflanzung | Nach letztem Frost; sonniger Standort | hoch |
| Jun–Sep | Deadheading | Verblühte Köpfe regelmäßig abzwicken — verlängert Blüte bis Oktober | hoch |
| Aug | Saatgut gewinnen | Verwelkte Köpfe reifen lassen; Samen ernten und trocknen | niedrig |
| Sep–Okt | Saisonende | Nach erstem Frost; Pflanzen kompostieren; Beet räumen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; gelbliche Blätter bei Trockenheit | Blatt | Blüte (heiß-trocken) |
| Blattläuse | Macrosiphum euphorbiae | Kolonien; weniger häufig als bei anderen Arten | Trieb | Sämling |
| Tausendfüßer | Scutigerella immaculata | Wurzelfraß; Welke | Wurzel | Keimling |

**Hinweis:** Tagetes erecta ist generell robust und wenig schädlingsanfällig. Der intensive Duft hält viele Insekten fern. In der Praxis kaum IPM-Maßnahmen nötig.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißgrauer Belag | trocken-warm; Spätsommer |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Pilzbefall; feuchte Blüten | kühl-feucht; alte Blüten |
| Wurzelfäule | fungal (Pythium spp.) | Welke; Wurzelnekrose | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Spinnmilben, Blattläuse |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen | 14 | Echter Mehltau |
| Befallene Teile entfernen | cultural | — | Sofort | 0 | Grauschimmel |
| Drainage verbessern | cultural | — | Substrat anpassen | 0 | Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Leichtezer |
| Fruchtfolge-Kategorie | Einjährige Zierpflanze; Companion Plant |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | 2 Jahre empfohlen (Botrytis-Dauerformen) |

**Nematoden-Sanierung:** Tagetes erecta und T. patula wirken als biologische Nematizide. 3 Monate Tagetes-Anbau auf befallenen Flächen reduziert Meloidogyne-Populationen um 90%. Anschließend 4 Monate Brache für maximalen Effekt. Wissenschaftlich gut belegt (Ploeg & Maris 1999, Nematology).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.95 | Klassischer Companion: Nematoden-Schutz; Thrips-Abwehr; Bestäuber | `compatible_with` |
| Aubergine | Solanum melongena | 0.9 | Nematoden-Schutz für Aubergine | `compatible_with` |
| Paprika | Capsicum annuum | 0.9 | Nematoden-Schutz; Schädlingsabwehr | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Schwebefliegen-Anlockung; Bestäubung | `compatible_with` |
| Kürbis | Cucurbita spp. | 0.8 | Käferpopulations-Reduktion (anekdotisch); Nützlinge | `compatible_with` |
| Kohl | Brassica oleracea spp. | 0.8 | Schädlingsabwehr; Kohlweißling-Verwirrung | `compatible_with` |
| Karotte | Daucus carota | 0.7 | Möhrenfliegen-Verwirrung; Nützlinge | `compatible_with` |
| Rose | Rosa spp. | 0.8 | Blattlausabwehr; Blühharmonie | `compatible_with` |
| Sojabohne | Glycine max | 0.8 | Nematoden-Schutz; Schwebefliegen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Bohnen (Buschbohne) | Phaseolus vulgaris | Tagetes kann Bohnenentwicklung hemmen (Alpha-Terthienyl bei sehr dichtem Anbau) | mild | `incompatible_with` |
| Kohl (sehr dicht) | Brassica oleracea | Allelopathische Hemmung bei sehr dichtem Anbau möglich | mild | `incompatible_with` |

**Hinweis:** Die "schlechten Nachbarn" sind wissenschaftlich nicht eindeutig belegt. Bei normalem Pflanzenabstand (30 cm) kaum negative Effekte. Tagetes ist einer der universellsten Begleitpflanzen.

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Asteraceae (Korbblütler) | `shares_pest_risk` | Echter Mehltau, Grauschimmel, Spinnmilben | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tagetes erecta |
|-----|-------------------|-------------|----------------------------------|
| Französische Studentenblume | Tagetes patula | Gleiche Gattung | Kompakter; stärkere Nematoden-Wirkung (T. patula > T. erecta) |
| Feinblättrige Studentenblume | Tagetes tenuifolia | Gleiche Gattung | Stark duftend; feinblättrig; Küchen-Tagetes |
| Azteken-Ringelblume | Tagetes minuta | Gleiche Gattung | Stärkste Nematoden-Wirkung aller Tagetes |
| Ringelblume | Calendula officinalis | Asteraceae; Kompagnon | Winterhart als Aussaat; medizinisch; andere Wirkungsweise |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Tagetes erecta,"Aufrechte Studentenblume;Afrikanische Studentenblume;African Marigold;Aztec Marigold",Asteraceae,Tagetes,annual,short_day,herb,fibrous,"9a;9b;10a;10b;11a;11b",0.5,"Mexiko;Mittelamerika",yes,limited,yes,false,false,light_feeder,false,tender,"3;4;5;6","","6;7;8;9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Inca Gold,Tagetes erecta,"tall;large_flower;golden_yellow;cut_flower",55,hybrid
Vanilla,Tagetes erecta,"cream_white;unique_color;tall",60,open_pollinated
American Giant Mix,Tagetes erecta,"very_tall;mixed_colors;cut_flower",65,open_pollinated
```

---

## Quellenverzeichnis

1. [Royal Horticultural Society — Tagetes](https://www.rhs.org.uk/plants/tagetes) — Gartenpraxis, Mischkultur
2. [Rodale Institute — Companion Planting Guide](https://rodaleinstitute.org) — IPM, Nützlinge
3. [University of Florida IFAS — Marigold Production](https://edis.ifas.ufl.edu) — Gewächshauskultur
4. [Ploeg & Maris (1999) — Nematology 1(5)](https://brill.com/view/journals/nemy) — Wissenschaftliche Nematoden-Wirkung
5. [Colorado State University Extension — Companion Plants](https://extension.colostate.edu) — Mischkultur-Empfehlungen
