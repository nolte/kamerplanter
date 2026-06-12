# Calla, Weiße Calla — Zantedeschia aethiopica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/zantedeschia-aethiopica-calla-lily), [University of Florida IFAS](https://edis.ifas.ufl.edu/publication/FP065), [RHS — Royal Horticultural Society](https://www.rhs.org.uk/plants/zantedeschia/aethiopica/details), [ASPCA](https://www.aspca.org/), [NC State Extension](https://plants.ces.ncsu.edu/plants/zantedeschia-aethiopica/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Zantedeschia aethiopica | `species.scientific_name` |
| Synonyme | Calla aethiopica, Richardia africana | — |
| Volksnamen (DE/EN) | Calla, Weiße Calla, Zimmercalla, Sumpfcalla; Calla Lily, Arum Lily, White Arum Lily, Garden Calla | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Zantedeschia | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Photosynthese-Typ | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (°C) | 7 (Kühlzehrer; Wachstum kommt < 7–10 °C praktisch zum Erliegen, optimaler Wuchs bei 13–18 °C) | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral, kein Kurztag-/Langtag-Blüher --> | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (tropisch-subtropische Herkunft, kein Kältebedarf für Blüte) | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — im Kübel bei Frost reinbringen. Im Freiland in Zone 8+ mit Mulchschutz möglich. Rhizom verträgt kurze Fröste bis –5°C, aber keine Dauerfröste. | `species.hardiness_detail` |
| Heimat | Südafrika, Lesotho — feuchte Standorte, Flussufer, Sümpfe | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Calla ist botanisch kein Verwandter echter Lilien — sie gehört zur Araceae-Familie (Aronstabgewächse). Das weiße "Blütenblatt" ist kein Blütenblatt, sondern ein Hochblatt (Spatha), der eigentliche Blütenkolben (Spadix) ist der gelbe Stift im Inneren. GIFTIG — alle Pflanzenteile enthalten Calciumoxalat-Raphiden und sind für Haustiere und Kinder gefährlich (starke Schleimhautreizung, selten lebensbedrohlich). Bevorzugt feuchte bis nasse Standorte; im Topf darf das Substrat nie austrocknen. Sommerdormanz bei Trockenheit möglich, ist aber nicht obligat.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt (Rhizom-Pflanzung im Frühling) | `species.direct_sow_months` |
| Erntemonate | Entfällt (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6 (Hauptblütezeit Frühling bis Frühsommer) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Rhizomteilung beim Umtopfen im Herbst oder Frühjahr. Seitentriebe (Tochterpflanzen) vom Mutterrhizom trennen und einzeln einpflanzen. Bewurzelung schnell. Samenvermehrung möglich aber langsam (2–3 Jahre bis erste Blüte).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (alle Teile inkl. Rhizom, Spatha, Blätter) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (Calciumoxalat-Raphiden: starke Schleimhautreizung, Speichelfluss, Erbrechen; selten lebensbedrohlich) | `species.toxicity.severity` |
| Kontaktallergen | true (Pflanzensaft kann Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Sicherheitshinweis:** Sofort Tierarzt/Arzt kontaktieren bei Aufnahme. Beim Umtopfen Handschuhe tragen — Pflanzensaft ist ein Kontaktallergen. Symptome: Brennen im Mund, Speichelfluss, Erbrechen, Schwellungen der Schleimhäute.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (verblühte Blütenstände, Sommer nach der Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten bis Sonne, vor Frost schützen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Feuchtigkeitshaltende, humusreiche Erde. pH 6.0–6.5. Einheitserde + 20% Kokosfaser. Niemals austrocknen lassen — Calla liebt konstant feuchtes Substrat. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert; als schattenverträgliche Araceae-Understory-Art niedriger LCP zu erwarten --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade (Vollsonne bei kühlen Sommern bis Halbschatten; tiefer Schatten = kaum Blüte) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–40 (flach wurzelndes Rhizom; Topftiefe ab 20 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | tolerant (Sumpf-/Uferpflanze; wächst in stehendem Wasser bis ~30 cm Tiefe) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant (verträgt salzhaltige Küstenluft; Blattspitzen-Nekrosen bei Substrat-Versalzung) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (Substrat-ECe) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 (schwach sauer bis neutral) | `species.soil_ph_preference` |

**Hinweis (Standortqualität):** Z. aethiopica ist eine ausgesprochene Feucht-/Nasszeiger-Art und gehört zu den wenigen Zierpflanzen, die echte Staunässe und sogar dauerhaft stehendes Wasser am Teichrand vertragen (Korb bis max. 30 cm Wassertiefe). Die Salztoleranz bezieht sich auf die salzhaltige Küstenluft im natürlichen Habitat; ein quantitativer Substrat-ECe-Schwellenwert nach Maas-Hoffman ist für die Art nicht publiziert. Der pH-Vorzug (6.0–7.0) harmonisiert mit der Substrat-Empfehlung in §1.6 (6.0–6.5) und den Phasen-pH-Werten in §2.3 (6.0–6.5), die im unteren Teil dieser Spanne liegen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe / Einzug (Oktober–Februar) | 90–120 | 1 | false | false | medium |
| Austrieb / Vorblüte (Februar–März) | 30–45 | 2 | false | false | low |
| Hauptblüte (März–Juni) | 60–90 | 3 | false | false | medium |
| Nach der Blüte / Sommer (Juli–September) | 60–90 | 4 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 5–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| DLI (mol/m²/Tag) | 2–6 | `requirement_profiles.dli_target_mol` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 10–15 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.45–0.55 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 21–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptblüte (März–Juni)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 16–22 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.45–0.55 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–6.5 | — | — | — | — | — | — |
| Austrieb/Vorblüte | 3:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 30 | 0.5–1.0 | 0.05–0.10 | 0.02–0.05 | 0.01–0.05 |
| Hauptblüte | 1:2:2 | 1.0–1.8 | 6.0–6.5 | 100 | 40 | 0.5–1.0 | 0.05–0.10 | 0.02–0.05 | 0.01–0.05 |
| Nach der Blüte | 1:1:2 | 0.6–1.0 | 6.0–6.5 | 60 | 20 | 0.5–1.0 | 0.05–0.10 | 0.02–0.05 | 0.01–0.05 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoff-Hinweis:** Mn/Zn/Cu/Mo (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`) folgen den allgemeinen Standard-Nährlösungsbereichen (Hoagland-/Steiner-Niveau); für Z. aethiopica sind keine artspezifischen Mikronährstoff-Zielwerte publiziert. In der Winterruhe (NPK 0:0:0) entfällt die Mikronährstoffgabe.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Flüssigdünger | Compo | base | 5-8-10 | 5 ml/L (alle 2 Wochen) | Blüte |
| Universaldünger | Substral | base | 7-3-7 | 5 ml/L | Austrieb |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | – | organisch | 50–80 g/Topf | Frühjahr |
| Kompost | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Mittelzehrer. Düngung von März bis August, alle 2 Wochen. In der Blütephase phosphat- und kalibetonten Dünger verwenden. Nach der Blüte bis Oktober reduzieren. Winterruhe ohne Dünger. Calla verträgt keine Trockenheit — Substrat während der Wachstumsphase immer feucht halten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat während der Wachstumsperiode konstant feucht halten — Calla liebt Wasser; in der Ruhephase stark reduzieren oder trockenstellen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Blattläuse | Aphis spp. | Klebrige Blätter, Honigtau, deformierte Blüten | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen auf Blättern | medium |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Weiche Rhizomfäule | bacterial (Pectobacterium spp.) | Fauliger Geruch, Rhizom braun-weich | Überfeuchte, hohe Temperaturen |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmelbelag auf Spatha/Blättern | Hohe Feuchtigkeit, schlechte Belüftung |
| Stängelfäule | fungal | Stängelbasis einschnürt sich, Welke | Überfeuchte, Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Befallene Teile entfernen | cultural | Sofort abschneiden und entsorgen | 0 | Grauschimmel, Fäulen |
| Bessere Belüftung | cultural | Abstand zwischen Pflanzen vergrößern | 0 | Grauschimmel (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Blattläuse, Thrips |
| Backpulverlösung | biological | Sprühen 0.5% | 0 | Grauschimmel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Blattlaus-Schlupfwespe | Aphidius colemani | Blattläuse (Aphis spp.) | 1–3 Tiere/m² je Freilassung, 2–3× im Wochenabstand | ~2 Wochen (Mumienbildung), 2 überlappende Generationen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphis spp.) | 1–5 Larven/m² | 1–2 Wochen |
| Raubmilbe (Thrips) | Neoseiulus (Amblyseius) cucumeris | Thrips (Frankliniella occidentalis), Larvenstadien | 100–200 Tiere/m² (präventiv), bis 400/m² (kurativ) | 3–4 Wochen |
| Raubmilbe (Spinnmilbe) | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 5–20 Tiere/m² je nach Befall | ~2 Wochen (bei < 30 °C, > 60 % rF) |

**Hinweis (Nützlingseinsatz):** Bei Z. aethiopica sind die drei relevanten Schädlinge (Blattläuse, Westlicher Blütenthrips, Gemeine Spinnmilbe) mit etablierten Nützlingen biologisch bekämpfbar — am wirksamsten unter Glas/im Wintergarten. Phytoseiulus persimilis braucht für die Etablierung ausreichende Luftfeuchte (> 60 %), die für die feuchteliebende Calla ohnehin günstig ist. Thrips-Raubmilben wirken nur gegen die Larvenstadien; gegen adulte Thrips ergänzend Blaufallen oder Orius-Raubwanzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zier-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Farbige Calla | Zantedeschia elliotiana | Gleiche Gattung | Gelbe/bunte Blüten, kompakter |
| Spathiphyllum | Spathiphyllum wallisii | Araceae, weiße Spatha | Pflegeleichter, weniger giftig |
| Anthurium | Anthurium andraeanum | Araceae, ähnliche Spatha | Langanhaltende Blüte, Indoor |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Zantedeschia aethiopica,"Calla;Weiße Calla;Zimmercalla;Sumpfcalla;Calla Lily;Arum Lily",Araceae,Zantedeschia,perennial,day_neutral,herb,rhizomatous,"8a;8b;9a;9b;10a;10b;11a","Südafrika, Lesotho",yes,5-15,20,60-120,40-80,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Zantedeschia aethiopica](https://www.gardenia.net/plant/zantedeschia-aethiopica-calla-lily) — Botanische Daten, Kulturbedingungen
2. [University of Florida IFAS](https://edis.ifas.ufl.edu/publication/FP065) — Wissenschaftliche Daten, Schädlinge
3. [RHS — Zantedeschia aethiopica](https://www.rhs.org.uk/plants/zantedeschia/aethiopica/details) — Winterhärte, Pflege
4. [NC State Extension — Zantedeschia aethiopica](https://plants.ces.ncsu.edu/plants/zantedeschia-aethiopica/) — Kulturdaten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (stark giftig — Calcium-Oxalate)
6. [PFAF — Plants For A Future: Zantedeschia aethiopica](https://pfaf.org/user/Plant.aspx?LatinName=Zantedeschia+aethiopica) — Boden-pH (schwach sauer/neutral/basisch), Schattentoleranz (Halbschatten bis Vollsonne), Feuchte-/Wassertoleranz (Wasser bis 30 cm Tiefe) <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
7. [PlantZAfrica / SANBI — Zantedeschia aethiopica](https://pza.sanbi.org/zantedeschia-aethiopica) — Habitat (Sumpf/Uferpflanze), Guttation/Staunässe, salzhaltige Küstenluft, Höhenverbreitung <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
8. [Gardenia.net — Zantedeschia aethiopica (White Calla Lily)](https://www.gardenia.net/plant/zantedeschia-aethiopica) — Lichtbedarf (Vollsonne/Halbschatten je nach Sommerklima), Frosthärte (–5 bis –10 °C), Mindesttemperatur Kübel 7–10 °C <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
9. [University of Florida IFAS — Warm Climate Production Guidelines for Zantedeschia (ENHFL04-001)](https://hort.ifas.ufl.edu/floriculture/pdfs/crop_production/Callas_ENHFL04-001.pdf) — Temperaturpräferenz (kühl, helle Bedingungen, kühle Nächte) <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
10. [Wikipedia — Zantedeschia (Frosthärte/Temperaturschwellen)](https://en.wikipedia.org/wiki/Zantedeschia) — Wachstums-/Frostschwelle, Wuchsschwelle ~10 °C, Kältehärte-Cultivare <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
11. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Nützling Spinnmilbe, Ausbringrate/Etablierung <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
12. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate/Etablierungszeit Spinnmilben-Raubmilbe <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
13. [Koppert — Neoseiulus (Amblyseius) cucumeris](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/neoseiulus-cucumeris/) — Thrips-Raubmilbe, Ausbringrate/Etablierung <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
14. [Hoagland solution / Standard-Nährlösung (Wikipedia)](https://en.wikipedia.org/wiki/Hoagland_solution) — Standard-Mikronährstoffbereiche Mn/Zn/Cu/Mo (ppm) <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
