# Elefantenohr, Afrikanische Maske — Alocasia × amazonica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Garden Betty](https://gardenbetty.com/alocasia-polly/), [Smart Garden Guide](https://smartgardenguide.com/alocasia-amazonica-care/), [Bloomscape](https://bloomscape.com/plant-care-guide/alocasia/), [ASPCA](https://www.aspca.org/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-an-alocasia)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Alocasia × amazonica | `species.scientific_name` |
| Volksnamen (DE/EN) | Elefantenohr, Afrikanische Maske; African Mask Plant, Elephant Ear, Kris Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Alocasia | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wurzeltyp | rhizomatous | `species.root_type` |
| Wurzelanpassungen | tuberous (Rhizomknollen als Wasserspeicher) | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (saisonale Ruhephase im Winter häufig, besonders bei kühlem Standort) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> (keine zwei unabhängigen GDD-Basiswerte für Alocasia belegt; wärmeliebende Tropenpflanze, Wachstumsstillstand unter ~15 °C) | `species.base_temp` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Unter 15°C Wachstumsstillstand und mögliche Dormanz. | `species.hardiness_detail` |
| Heimat | Hybride Gartenzüchtung (Alocasia longiloba × Alocasia sanderiana, Südostasien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis Taxonomie:** Alocasia × amazonica ist eine Hybridpflanze, die in den 1950er Jahren in Florida gezüchtet wurde — trotz des Namens hat sie nichts mit dem Amazonas zu tun. Die Sorte 'Polly' ist die kompaktere Züchtung der × amazonica und heute die am häufigsten im Handel erhältliche Variante. Dormanz-Phasen (Blätter absterben, Knolle überwintert) sind normal und kein Anzeichen des Absterbens.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (selten Indoor; calla-ähnliche Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, offset | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Ableger (Kindknollen) an der Mutterknolle beim Umtopfen abtrennen. Jede Kindknolle mit eigenem Triebansatz einzeln einpflanzen. Bewurzelung bei 22–24°C Bodentemperatur und hoher Luftfeuchtigkeit (80%). Dormierende Knollen im Substrat belassen — sie treiben im Frühling neu aus.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, roots | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides, oxalate_crystals | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Calciumoxalat-Kristalle verursachen Hautreizungen und Kontaktdermatitis) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WICHTIG:** Alocasia ist für Kleinkinder und Haustiere besonders gefährlich. Die Calciumoxalat-Raphiden können schwere Schwellungen im Mund- und Rachenraum verursachen (Atemwegsschwellung möglich). Bei Verdacht auf Verschlucken sofort Arzt/Tierarzt aufsuchen. In Haushalten mit Kleinkindern oder Tieren möglichst auf andere Pflanzen ausweichen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Abgestorbene Blätter an der Stängelbasis abschneiden. Keine Stumpfe stehen lassen — können faulen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–12 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 ('Polly') bis 90+ | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, windgeschützt, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockeres, gut drainiertes Substrat: Einheitserde + 30% Perlite + 10% Orchideenrinde. pH 5.5–7.0. Guter Wasserabzug zwingend (kein Staunasser Topf!). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> (kein Maas-Hoffman-Schwellenwert für Alocasia/Colocasia in FAO-/USDA-Salztoleranztabellen gelistet) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–7.0 | `species.soil_ph_preference` |

**Hinweis Licht-Physiologie:** Der angegebene Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) ist der für schattentolerante Tropenwald-Unterwuchspflanzen (understory) typische Bereich; die nahe verwandte Art *Alocasia macrorrhiza* ist eine klassische Unterwuchs-Studienart mit ausgeprägter Schattenanpassung (niedriger Kompensationspunkt, niedrige Dunkelatmung). Die Lichtsättigung liegt davon getrennt deutlich höher (ca. 150–400 µmol/m²/s im aktiven Wachstum, siehe §2.2); bereits kurze direkte Mittagssonne führt zu Blattbleiche (Chlorose).

**Hinweis Salztoleranz:** Die Einordnung als moderately_tolerant stützt sich auf Salinitätsversuche an der nah verwandten *Colocasia esculenta* (Taro, gleiche Familie, vergleichbare Wuchsform), die bis ~100 mM NaCl ohne wesentliche Wuchseinbußen toleriert und bis ~200 mM NaCl überlebt. Ein quantitativer Maas-Hoffman-Schwellenwert (a) bzw. Slope (b) ist für die Gattung nicht publiziert und bleibt daher offen. Bezugsgröße der Klasse: Substrat-ECe (saturated paste), nicht Gießwasser-EC. Im Topf gilt: Calciumoxalat-empfindliche Wurzeln reagieren empfindlich auf Salzakkumulation aus Überdüngung → regelmäßiges Durchspülen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–210 | 1 | false | false | low |
| Dormanz (Herbst/Winter — optional) | 60–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 5.5–7.0 | 100 | 50 | 0.5 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01–0.05 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Dormanz | 0:0:0 | 0.0 | 5.5–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Die Mikronährstoff-Zielwerte Mn/Zn/Cu/Mo entsprechen den Konzentrationen einer vollständigen Standard-Nährlösung (Hoagland-Referenz: Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.01–0.05 ppm) — generische Foliage-Plant-Richtwerte, keine Alocasia-spezifischen Messwerte. In der Dormanz wird nicht gedüngt (Nullprofil).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 2–4 Wochen in der Wachstumsphase. Im Herbst/Winter kein Dünger. Überdüngung führt zu Blattrandnekrosen. Stickstoff fördert großes, sattgrünes Laub.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser bevorzugt; Raumtemperatur; kein kaltes Leitungswasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 10 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor erstem Frost / Nachttemperaturen unter 15 °C hereinholen) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach den Eisheiligen, langsam abhärten) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–21 (frostfrei; unter 15 °C Dormanz, optimal ≥ 18 °C zur Dormanzvermeidung) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; bei Dormanz dunklerer Stand tolerierbar | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | stark reduziert (alle 14–21 Tage, Substrat nur leicht feucht halten — bei voller Dormanz alle 3–5 Wochen) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis Überwinterung:** Als nicht frosthartes (frost_free) Tropengewächs wird Alocasia × amazonica frostfrei im Haus überwintert — keine Frostschutz-Maßnahme im Freiland (kein Mulch/Vlies). Eine winterliche Ruhephase (Dormanz) mit Einziehen der Blätter ist normal: Die Rhizomknolle überwintert im Substrat und treibt im Frühjahr neu aus (nicht entsorgen!). Bei konstant ≥ 18–21 °C und ausreichend Licht kann die Dormanz ganz ausbleiben. Staunässe im kühlen Winterquartier ist die häufigste Verlustursache (Knollenfäule).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blattvergilbung | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Blattlaus | Aphididae | Kolonien an Neutrieben | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, faulende Knollen | Überbewässerung, Staunässe |
| Blattflecken | fungal/bacterial | Braune/schwarze Flecken | Wasser auf Blättern |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Luftfeuchtigkeit erhöhen | cultural | Befeuchter | 0 | Spinnmilbe (Prävention) |
| Umtopfen | cultural | Faule Teile entfernen | 0 | Wurzelfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 / m² je Ausbringung; bei Bedarf wöchentlich wiederholen | ab Befallsbeginn; kurativ, schnelle Reduktion |
| Australischer Marienkäfer | Cryptolaemus montrouzieri (Adulte) | Schmierläuse (Pseudococcus spp.) | 2–10 / m² je Ausbringung (Larven „Cryptobug-L": 5–40 / m²) | wirksam ab 16 °C, optimal 25–28 °C; Larven-Ausbringung 3× im Abstand 1–2 Wochen |

**Hinweis Nützlinge:** Im Innenraum/Wintergarten sind Raubmilben (Phytoseiulus persimilis) gegen Spinnmilben und der Marienkäfer Cryptolaemus montrouzieri gegen Schmierläuse die bewährten Nützlinge. Phytoseiulus arbeitet am besten bei hoher Luftfeuchtigkeit (> 60 %), die für Alocasia ohnehin gegeben ist. Bei starkem Spinnmilbenbefall zuerst Phytoseiulus einsetzen, anschließend für die Langzeitkontrolle Amblyseius-Arten ergänzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Zebrapflanze | Alocasia zebrina | Gleiche Gattung | Auffällige Zebrastreifen-Stängel |
| Colocasia | Colocasia esculenta | Gleiche Familie, ähnliche Wuchsform | Robuster, essbare Knolle (Taro) |
| Caladium | Caladium bicolor | Gleiche Familie | Farbenfrohere Blätter, Sommerkultur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Alocasia × amazonica,"Elefantenohr;Afrikanische Maske;African Mask Plant;Elephant Ear",Araceae,Alocasia,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Hybridgartenzüchtung (A. longiloba x A. sanderiana, Suedostasien)",yes,3-12,20,30-90,30-60,yes,limited,false,medium_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Polly,Alocasia × amazonica,"ornamental;compact;dark_leaves",clone
```

---

## Quellenverzeichnis

1. [Garden Betty — Alocasia Polly](https://gardenbetty.com/alocasia-polly/) — Pflegehinweise, Dormanz
2. [Smart Garden Guide](https://smartgardenguide.com/alocasia-amazonica-care/) — Wachstumsparameter
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Bloomscape — Alocasia Care Guide](https://bloomscape.com/plant-care-guide/alocasia/) — Pflegehinweise
5. [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-an-alocasia) — Praxiswissen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Sims & Pearcy (1989), Oecologia — Photosynthetic characteristics of *Alocasia macrorrhiza* and *Colocasia esculenta*](https://pubmed.ncbi.nlm.nih.gov/28312812/) — Unterwuchs-/Schatten-Physiologie der Gattung (light compensation point, Lichtakklimatisierung, T-Optimum); peer-reviewed
7. [ScienceDirect — Stable isotope (δ13C) and carbon-water relations of taro (*Colocasia esculenta*)](https://www.sciencedirect.com/science/article/abs/pii/S0176161718305431) — Beleg C3-Photosynthese-Typ (δ13C −23‰ bis −30‰) für nah verwandte Art
8. [MDPI Plants (2021) — Effects of Salinity on the Growth and Nutrition of Taro (*Colocasia esculenta*)](https://www.mdpi.com/2223-7747/10/11/2319) — Salztoleranz der Familie (bis ~100 mM NaCl ohne Wuchseinbuße, Überleben bis ~200 mM)
9. [FAO — Crop salt tolerance data (Annex 1, Maas-Hoffman)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Beleg, dass kein Maas-Hoffman-Schwellenwert für Taro/Colocasia tabelliert ist
10. [Soltech — Alocasia Polly Plant Care](https://soltech.com/products/alocasia-polly-care) — Boden-pH, Staunässe-Empfindlichkeit, Wurzelraum
11. [RHS / Wikipedia — Shade tolerance](https://en.wikipedia.org/wiki/Shade_tolerance) — Physiologie schattentoleranter Unterwuchspflanzen (niedriger Kompensationspunkt, Far-Red-Nutzung)
12. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Raubmilbe gegen Spinnmilben (2–50 / m²)
13. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate/Temperatur Marienkäfer gegen Schmierläuse
14. [Highland Moss — Alocasia Dormancy](https://highlandmoss.com/everything-you-need-to-know-about-alocasia-dormancy/) — Überwinterung, Dormanz-Auslöser, Wintergießen
15. [Smart Garden Guide — Alocasia Dormancy](https://smartgardenguide.com/alocasia-dormancy/) — Mindesttemperatur 15 °C, Dormanz-Pflege
16. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Standard-Mikronährstoffkonzentrationen Mn/Zn/Cu/Mo der Referenz-Nährlösung
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
