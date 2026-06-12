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
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Blütenknospen in strengen Wintern schädigt (unter -25°C); in Norddeutschland absolut winterhart | `species.hardiness_detail` |
| Heimat | Hybrid aus China/Korea-Arten; kultiviert seit 19. Jh. | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein eindeutiger, durch zwei unabhängige Quellen belegter Wuchs-GDD-Basiswert auffindbar; verbreitete Bloom-Phänologie-Modelle nutzen Basis 10 °C (50 °F), das ist aber ein Blüh-Phänologie-Bezug, kein bestätigter Wuchs-GDD-Basiswert --> | `species.base_temp` |
| Lebensdauer (Jahre) | 25–40 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich (chilling) | true (Endodormanz-Bruch durch Kälte, kein klassischer Vernalisations-Blühschalter) | `lifecycle_configs.vernalization_required` |
| Vernalisation/Chilling Mindest-Tage | 42–56 (≈ 6–8 Wochen unter 7 °C; ≈ 600–1000 Chilling Hours) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral; Blühinduktion chilling- und wärmegesteuert, kein Kurz-/Langtag-Blühschalter) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine belegten Maas-Hoffman-Schwellenwerte (a) für Forsythia in seriösen Quellen --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope (b) für Forsythia --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

> **Hinweise:** Lichtkompensationspunkt als funktionstyp-typische Spanne für sonnen-/halbschattentolerante C3-Laubgehölze (Forsythia-spezifische Messwerte nicht publiziert); Lichtsättigung dieses Typs liegt deutlich höher (≈ 800–1000 µmol/m²/s) — diese Sättigungswerte gehören NICHT ins LCP-Feld. Schatten-/Sonnentoleranz: Forsythie toleriert Halbschatten (partial_shade), blüht aber in voller Sonne deutlich reicher → Einstufung `full_sun`. Salztoleranz: in Streusalz-/Straßenrand-Verzeichnissen mehrfach als salzverträglich gelistet (NC State, Küsten-/Roadside-Listen); eine Extension-Quelle führt Salz nicht als Stärke → daher konservativ `moderately_tolerant` statt `tolerant`; Bezugsgröße wäre Substrat-ECe, nicht Gießwasser-EC. Boden-pH-Vorzug quellentreu auf den in §1.6/§2.3 verwendeten Korridor 6,0–7,5 harmonisiert; die Art ist darüber hinaus pH-adaptiv (sauer bis alkalisch).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Blüte | 0:1:1 | 0.8–1.2 | 6.5–7.0 | 80 | 40 | – | 1 | 0.5 | 0.05 | 0.02 | 0.01 |
| Triebwachstum | 2:1:2 | 1.0–1.4 | 6.5–7.0 | 100 | 50 | – | 2 | 0.5 | 0.05 | 0.02 | 0.01 |
| Knospenanlage | 1:1:3 | 0.8–1.2 | 6.5–7.0 | 80 | 50 | – | 1 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – | – | – | – | – |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> **Mikronährstoffe (Mn/Zn/Cu/Mo):** Funktionstyp-typische Standard-Zielwerte einer ausgewogenen Nährlösung (Hoagland-/Universal-Gehölzdünger-Bereich); Forsythia-spezifische Bedarfsmessungen sind nicht publiziert. Werte gelten je `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`. In der Winterruhe keine Düngung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|--------------------|----------------|-----------------|------------------|
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphis gossypii) | 0,15–1 /m²/Woche | ~2 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphis gossypii) | 1–5 /m²/Woche | ~2 Wochen |

> **Hinweis:** Beide Nützlinge zielen auf die echten Blattläuse (Aphidina) ab — fachlich korrekte Wirt-Zuordnung. Bei Blattkäfern (Chrysomelidae) wirken diese Blattlaus-Antagonisten NICHT; dort bleibt das mechanische/biologische Absammeln bzw. Neemöl die Methode der Wahl. Ausbringung bevorzugt im warmen Halbjahr (Triebwachstumsphase), wiederholte Freilassung in 1–2-Wochen-Intervallen bis zur Etablierung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
Forsythia × intermedia,"Forsythie;Goldflieder;Border Forsythia",Oleaceae,Forsythia,perennial,day_neutral,shrub,fibrous,"5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Kultivierter Hybrid",limited,40,40,300,250,150,no,limited,false,false,medium_feeder,false,hardy,"3;4"
```

---

## Quellenverzeichnis

1. [Naturadb Forsythia × intermedia](https://www.naturadb.de/pflanzen/forsythia-x-intermedia/) — Steckbrief, Winterhärte
2. [Plantura Forsythie](https://www.plantura.garden/gehoelze/forsythie/schneeforsythie) — Pflege, Schnitt
3. [Pflanzen-Kölle Forsythie](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-forsythie-richtig/) — Pflege, Düngung
4. [Lubera Forsythien](https://www.lubera.com/de/gartenbuch/forsythien-p2431) — Anbau, Vermehrung
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — Forsythia × intermedia](https://www.rhs.org.uk/plants/94712/forsythia-intermedia/details) — Boden-pH (sauer/neutral/alkalisch), Sonne/Halbschatten, Winterhärte H5, Reifezeit 5–10 Jahre
6. [NC State Extension — Forsythia x intermedia](https://plants.ces.ncsu.edu/plants/forsythia-x-intermedia/) — pH-Spanne, Lichtbedarf (Vollsonne mehr Blüten), gute Drainage, Salzverträglichkeit
7. [University of Illinois Extension — Border Forsythia (Shrub Selector)](https://web.extension.illinois.edu/shrubselector/detail_plant.cfm?PlantID=393) — Vollsonne, alkalitolerant, gute Drainage; Salz nicht als Stärke geführt (Grundlage für konservative Klasse)
8. [Frontiers in Plant Science — Chilling, Photoperiod & Forcing in Temperate Woody Plants (2020)](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.00443/full) — Blühphänologie holziger Arten: chilling-/wärmegesteuert, kein Photoperioden-Blühschalter (Beleg day_neutral, Dormanz)
9. [UMN Extension — Forsythia](https://extension.umn.edu/trees-and-shrubs/forsythia) — Wuchszyklus, Knospenanlage im Spätsommer, Dormanzeintritt im Herbst
10. [Old Farmer's Almanac — Forsythia](https://www.almanac.com/plant/forsythia) / [The Plant Aide — Forsythia-Lebensdauer](https://www.theplantaide.com/articles/66923.html) — Lebensdauer 25–40 Jahre, Wurzeltiefe ca. 30–45 cm
11. [Koppert — Aphidoletes aphidimyza (Aphidend)](https://www.koppert.com/aphidend/) / [Sound Horticulture — Aphidius colemani Tech Sheet](https://soundhorticulture.com/pages/aphidius-colemani-tech-sheet) — Nützling-Ausbringraten und Etablierung gegen Blattläuse
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
