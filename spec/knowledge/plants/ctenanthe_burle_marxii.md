# Fischgräten-Gebetsblume — Ctenanthe burle-marxii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/ctenanthe-burle-marxii-care/), [Houseplant 411](https://www.houseplant411.com/houseplant/ctenanthe-plant-how-to-grow-care-for-ctenanthe-plants/), [Plant Care Today](https://plantcaretoday.com/ctenanthe-burle-marxii.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ctenanthe burle-marxii | `species.scientific_name` |
| Synonyme | Ctenanthe burle-marxii 'Amagris' (häufige Handelsform) | — |
| Volksnamen (DE/EN) | Fischgräten-Gebetsblume, Ctenanthe; Fishbone Prayer Plant, Never Never Plant, Bamburanta | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Ctenanthe | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Photosynthese-Typ | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Kritische Tageslänge (h) | — (tagneutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (tropische Art ohne Kältebedarf) | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Reagiert empfindlich auf Kälte unter 13°C. | `species.hardiness_detail` |
| Heimat | Brasilien — tropische Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Ctenanthe burle-marxii zeigt das für Marantaceen typische Fischgräten-Muster auf den blaugrünen Blättern mit silbergrauen Streifen — die Blattunterseite ist leuchtend magentafarben. Wie alle Marantaceen zeigt die Pflanze ausgeprägte Nyktinastie (Blätter falten sich nachts auf). Im Vergleich zu Calathea/Goeppertia-Arten gilt sie als etwas robuster und anspruchsloser. Benannt nach dem brasilianischen Landschaftsarchitekten Roberto Burle Marx.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Physiologie):** Marantaceen sind klassische tropische Schattenpflanzen mit C3-Photosynthese (C3) — CAM oder C4 kommen in dieser Familie nicht vor. Die GDD-Basistemperatur (base temp) ist als warmsaisonaler Standardwert von 10 °C angesetzt; konsistent mit der dokumentierten Mindesttemperatur von 15 °C (§1.1 Winterhärte-Detail) und dem wärmeliebenden, frostempfindlichen Charakter der Art. Es existieren keine artspezifischen Wuchs-/Phänologie-GDD-Studien; der Wert folgt der Warmsaison-Konvention für tropische Arten. Die Art ist tagneutral (day_neutral) — es gibt keine kritische Tageslänge für die Blühinduktion.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (kleine weiße Blüten bei älteren Pflanzen, selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Rhizom-Teilung beim Umtopfen im Frühjahr — Abschnitte mit mindestens 2–3 Blättern in feuchtes Substrat. Hohe Luftfeuchtigkeit nach der Teilung wichtig. Bewurzelung dauert 4–6 Wochen.

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
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt erforderlich. Nur komplett abgestorbene oder gelbe Blätter an der Basis entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 25–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no (zu empfindlich für direkte Sonne und Zugluft) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut drainierte, feuchtigkeitshaltende Erde. pH 6.0–7.0. Mix aus Einheitserde + Perlite (20%) + Kokosfaser (15%). Gute Drainage wichtig — keine Staunässe. | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–25 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | < 2 (Maas-Hoffman a; geschätzt aus Klasse, kein artspezifischer Messwert) <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.6–6.5 | `species.soil_ph_preference` |

**Hinweis:** Als Regenwald-Unterwuchsart (understory) ist *Ctenanthe burle-marxii* ausgesprochen schattentolerant (`shade`); echte Vollsonne (`full_sun`) verbrennt die Blätter. Der Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) liegt im für tropische Schatten-Herbarten typischen Bereich von 10–25 µmol/m²/s (allgemeiner Familien-/Funktionstyp-Wert, kein artspezifischer Messwert). Sättigungs- und Optimumwerte gehören NICHT in dieses Feld; die kulturelle PPFD-Empfehlung (80–250 µmol/m²/s, §2.2) liegt deutlich oberhalb des Kompensationspunkts. Marantaceen sind familienweit stark salzempfindlich (`sensitive`) und reagieren besonders auf Fluorid, Chlorid und harte Wassersalze mit Blattspitzennekrose — daher weiches, kalkarmes Wasser (§3.2/§4.1). Die ECe-Schwelle (Substrat-ECe nach Maas-Hoffman, NICHT Gießwasser-EC) ist konsistent mit der Klasse `sensitive` mit < 2 dS/m angesetzt, jedoch nicht artspezifisch belegt. Der Boden-pH-Vorzug von 5.6–6.5 (leicht sauer/acidic) ist quellentreu übernommen und überschneidet sich mit dem in §1.6/§2.3 genannten operativen Topf-pH-Korridor (6.0–7.0) im Band 6.0–6.5.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 60–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 60–180 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 50 | 20 | 0.5 | 0.3 | 0.1 | 0.05 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — | — | — | — | — | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Die Mn/Zn/Cu/Mo-Werte sind die für Zier-/Blattpflanzen üblichen Mikronährstoff-Zielkonzentrationen einer vollständigen Nährlösung (Hoagland-/Foliage-Plant-Standardbereich) und keine artspezifischen Messwerte für *Ctenanthe burle-marxii*. Als Schwachzehrer (light_feeder) ist die untere Spanne anzusetzen; eine separate Mikronährstoffdüngung ist bei Verwendung eines Volldüngers in der Regel nicht erforderlich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich, halbdosiert) | Wachstum |
| Zimmerpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis August, halbe Empfehlungsdosis. September bis März kein Dünger. Weiches, kalkarmes Wasser bevorzugen (Regenwasser oder gefiltertes Wasser). Kalkreiches Leitungswasser kann Blattspitzenbraun verursachen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser bevorzugt (Regenwasser, gefiltertes Wasser); Substrat gleichmäßig feucht halten; hohe Luftfeuchtigkeit notwendig (Luftbefeuchter oder Kieselsteinschale) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (September, vor erstem Frost / Nachttemperaturen < 13 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 6 (Juni, nach den Eisheiligen, nur halbschattiger/geschützter Standort) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (nie unter 13 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, ohne direkte Sonne (60–200 µmol/m²/s) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert; Substrat leicht feucht halten, Staunässe vermeiden | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** *Ctenanthe burle-marxii* ist nicht frosthart (`frost_free`) und wird ganzjährig als Zimmerpflanze gehalten. Ein Sommeraufenthalt im Freien ist nur an warmen, halbschattigen, windgeschützten Plätzen möglich; volle Sonne und Zugluft sind zu meiden. Vor Nachttemperaturen unter 13 °C zurück ins Haus (`move_indoors`). Hohe Luftfeuchtigkeit bleibt auch im Winterquartier wichtig — trockene Heizungsluft verursacht Blattspitzennekrosen. Kein echtes Einlagern/Trockenruhen wie bei Knollen (kein `dig_and_store`).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Blätter vergilben, braune Ränder | medium |
| Schmierlaus | Pseudococcus spp. | Weißwollige Flecken in Blattachseln | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen, deformierte Blätter | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke trotz feuchtem Substrat, braune Wurzeln | Staunässe |
| Blattflecken | fungal | Braune Flecken mit gelbem Rand | Nasses Laub, schlechte Belüftung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Luftbefeuchter, Kieselsteinschale | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Schmierläuse |
| Kaliseife | biological | Sprühen 1–2% | 0 Tage | Schmierläuse, Thrips |

### 5.4 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | ~20–50/m² je Freisetzung, bei Erstbefall wöchentlich wiederholen | 2 Wochen (bei 17–28 °C, > 60 % rF) |
| Australischer Marienkäfer / Schmierlausräuber | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 5–10 Käfer je befallene Pflanze (bzw. ~0.2–0.5/m²) | 3–4 Wochen (bei 18–27 °C, > 70 % rF) |
| Raubmilbe | Neoseiulus (Amblyseius) cucumeris | Thrips (Frankliniella occidentalis) | 50–100/m² je Freisetzung bzw. 1 Tütchen je 1–2 m² / Pflanze | 2–3 Wochen (warm, > 65 % rF) |

**Hinweis:** Die hohe Luftfeuchtigkeit, die *Ctenanthe burle-marxii* ohnehin benötigt, begünstigt die Etablierung aller drei Nützlinge (insbesondere *Phytoseiulus persimilis* und *Neoseiulus cucumeris*, die feucht-warme Bedingungen verlangen). Nützlingseinsatz nicht mit Neemöl/Kaliseife kombinieren — eine Spritzbehandlung mindestens 5–7 Tage vor der Freisetzung abschließen. Die Zuordnung folgt der korrekten Wirt-Spezifität: *Phytoseiulus persimilis* ist ein reiner Spinnmilben-Spezialist, *Cryptolaemus montrouzieri* frisst Schmier-/Wollläuse, *Neoseiulus cucumeris* bekämpft junge Thripslarven.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Klapperschlangen-Calathea | Goeppertia lancifolia | Marantaceae, ähnliches Muster | Etwas bekannter, gut verfügbar |
| Korbmarante | Goeppertia makoyana | Marantaceae, Gebetsblume | Pfauenmuster, Nyktinastie |
| Stromanthe Triostar | Stromanthe sanguinea | Marantaceae | Dreifarbiges Laub |
| Gewöhnliche Gebetsblume | Maranta leuconeura | Marantaceae | Kompakter, robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Ctenanthe burle-marxii,"Fischgräten-Gebetsblume;Ctenanthe;Fishbone Prayer Plant;Never Never Plant;Bamburanta",Marantaceae,Ctenanthe,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Brasilien (tropische Regenwälder)",yes,2-8,15,25-50,30-60,yes,no,false,light_feeder
```

---

## Quellenverzeichnis

1. [Smart Garden Guide — Ctenanthe burle-marxii](https://smartgardenguide.com/ctenanthe-burle-marxii-care/) — Pflegehinweise, Kulturdaten
2. [Houseplant 411 — Ctenanthe](https://www.houseplant411.com/houseplant/ctenanthe-plant-how-to-grow-care-for-ctenanthe-plants/) — Botanische Daten, Schädlinge
3. [Plant Care Today — Ctenanthe burle-marxii](https://plantcaretoday.com/ctenanthe-burle-marxii.html) — Pflegedetails
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [GardenDrum — Ctenanthe, the never never plants](https://gardendrum.com/2013/05/11/ctenanthe-the-never-never-plants/) — Marantaceae als schattenliebende Unterwuchs-Herbarten (shade_tolerance, C3-Habitatzuordnung)
6. [Pistils Nursery — A Guide to Prayer Plants (Marantaceae Indoors)](https://pistilsnursery.com/blogs/journal/a-guide-to-prayer-plants-how-to-grow-maranta-calathea-and-other-marantaceae-indoors) — Marantaceae-Unterwuchsphysiologie, Lichtansprüche
7. [Sterck et al. 2013, Journal of Ecology — Light compensation point in tropical forest understorey shrubs](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — Lichtkompensationspunkt schattentoleranter Unterwucharten (10–50 µmol/m²/s)
8. [rseco.org — Photosynthesis in sun and shade (Chap. 12.1)](https://rseco.org/book/export/html/257.html) — LCP-Bereiche Schattenpflanzen, T_opt C3-Schattenblätter
9. [Plant Care Today — Growing Ctenanthe Burle-Marxii](https://plantcaretoday.com/calathea-burle-marxii.html) — Boden-pH 5.6–6.5, Drainage, flache/fragile Rhizomwurzeln (effective_root_depth, soil_ph_preference)
10. [Greg.app — Ctenanthe Burle-Marxii Care](https://greg.app/plant-care/ctenanthe-burle-marxii) — pH-/Standortbestätigung
11. [Agri Farming — Calathea Brown Tips (Fluorid-/Salzempfindlichkeit Marantaceae)](https://www.agrifarming.in/calathea-brown-tips-fixes) — Salztoleranz-Klasse `sensitive`, Fluorid-/Chlorid-Empfindlichkeit
12. [Deep Green Permaculture — Indoor plants sensitive to fluoride](https://deepgreenpermaculture.com/2022/05/23/which-indoor-plants-are-sensitive-to-fluoride-in-tap-water/) — Marantaceae salzempfindlich (Bestätigung)
13. [Gardening Know How — Calathea Winter Care](https://www.gardeningknowhow.com/houseplants/calathea-plants/calathea-care-in-winter.htm) — Überwinterung, Mindesttemperatur 15 °C, frost_free
14. [PLNTS.com — Care tips for Ctenanthe (Never Never plant)](https://plnts.com/en/care/houseplants-family/ctenanthe) — Winterquartier 18–27 °C, Zugluft-/Kälteschutz
15. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Spinnmilben-Nützling, Ausbringrate, Etablierung
16. [KSU Extension MF3665 — Phytoseiulus persimilis](https://bookstore.ksre.ksu.edu/pubs/phytoseiulus-persimilis-biological-control-agent-of-the-twospotted-spider-mite_MF3665.pdf) — Freisetzungsrate/m², Bedingungen
17. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Schmierlaus-Nützling, Ausbringrate
18. [Koppert — Neoseiulus (Amblyseius) cucumeris](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/neoseiulus-cucumeris/) — Thrips-Nützling, Ausbringrate 50–100/m²
19. [Annals of Botany 2020 — PAR und R:FR unter Kronenschatten](https://academic.oup.com/aob/article/126/4/635/5650896) — R:FR im Unterwuchs (Far-Red-Fraction)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
