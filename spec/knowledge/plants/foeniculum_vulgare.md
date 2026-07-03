# Knollenfenchel — Foeniculum vulgare var. azoricum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Fenchel, Samen.de Fenchel, Kraut&Rüben Fenchel, Bio-Gärtner Fenchel

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Foeniculum vulgare var. azoricum | `species.scientific_name` |
| Volksnamen (DE/EN) | Knollenfenchel, Gemüsefenchel, Fenchel; Florence Fennel, Finocchio | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Foeniculum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | biennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | monocarpic (blüht einmal, dann Absterben) | `lifecycle_configs.flowering_strategy` |
| Anbau-Zyklustyp (cultivation cycle type) | annual (Knollenernte vor der Blüte im 2. Jahr; verhindert Schossen/Monokarpie durch Ernte im 1. Jahr) | `lifecycle_configs.cultivation_cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | <!-- DATEN FEHLEN --> kein art-spezifischer Wuchs-/Phänologie-Basiswert aus 2 unabhängigen seriösen Quellen belegbar; verfügbar ist nur eine Keim-Basistemperatur (~5 °C, Kamkar et al.), die NICHT als Wuchs-GDD-Basis umetikettiert werden darf | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true (fakultativ; Kältereiz >5 Tage unter ~7 °C induziert Schossen — im Knollenanbau unerwünscht) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | 5 | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN --> Langtag-Schosser belegt (Langtag + Hitze beschleunigen das Schossen), aber kein quellenbelegter numerischer Schwellenwert in Stunden auffindbar | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt leichte Fröste bis -5°C; Kälteexposition (Vernalisation) fördert Schossen bei nachfolgendem Langtag → schossfeste Sorten bei früher Aussaat wählen | `species.hardiness_detail` |
| Heimat | Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | -0.5 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Wichtiger Hinweis:** Fenchel ist stark allelopathisch und hemmt viele Pflanzen durch Wurzelausscheidungen (v.a. Terpenoide). Im Mischkulturbeet immer am Rand platzieren oder im Einzelbeet.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat bevorzugt; Knollenfenchel verträgt Verpflanzen schlecht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (frühester Termin Mitte Mai; bei Frühaussaat Schießen-Gefahr) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6, 7 (ab Juni für beste Ergebnisse in Norddeutschland) | `species.direct_sow_months` |
| Erntemonate | 8, 9, 10 | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (zweijährige Pflanze: Blüte erst im 2. Jahr; bei früher Aussaat schießt sie durch) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Estragol (in großen Mengen kanzerogen; normale Küchenmengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Apiaceae-Kreuzallergie möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzreaktion mit Birken- und Beifußpollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, lockere Gartenerde; pH 6,0–7,5; tief durchlässig | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 40 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe, dS/m) | 1.26 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | 14.24 | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweise:**
- Der Lichtkompensationspunkt (light compensation point) ist als Spanne für C3-Blattgemüse angegeben (Netto-Photosynthese = 0). Der Sättigungsbereich liegt deutlich höher (Ziel-PPFD 300–600, siehe §2.2) und gehört NICHT in dieses Feld.
- Fenchel ist ein C3-Vollsonnenstandort-Gewächs; verträgt Halbschatten (partial_shade), liefert dort aber weniger Knollenmasse.
- Salztoleranz bezieht sich auf die Substrat-Sättigungsextrakt-Leitfähigkeit (ECe), nicht auf die Gießwasser-EC. Schwelle 1.26 dS/m und Slope 14.24 %/dS/m gelten für NaCl-Stress (Maas-Hoffman-Modell, Semiz & Suarez 2015); eine zweite Feldstudie nennt eine höhere Schwelle (2.64 dS/m, Slope 4.5 %), bestätigt aber die Einordnung als "moderately salt sensitive". Konservativer (niedrigerer) Schwellenwert eingetragen.
- pH-Vorzug quellentreu auf 6.0–7.0 gesetzt und mit §1.6 (Topf-pH 6,0–7,5) sowie §2.3 (Nährlösungs-pH 6.0–6.5) harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | low |
| Knollenentwicklung | 42–70 | 3 | false | false | medium |
| Reife | 14–21 | 4 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Knollenentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (Langtag fördert Schießen; Kurztagsarten für frühe Aussaat) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.6 | 6.0–6.5 | 80 | 30 | — | 2 | 0.5 | 0.1 | 0.05 | 0.05 |
| Knollenentwicklung | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 | 0.5 | 0.1 | 0.05 | 0.05 |
| Reife | 1:2:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 1 | 0.5 | 0.1 | 0.05 | 0.05 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo):** Es liegen keine art-spezifischen Knollenfenchel-Sollwerte aus 2 unabhängigen Quellen vor. Eingetragen sind allgemein anerkannte Gemüse-Hydroponik-Standardwerte (Penn State Extension; UF/IFAS CV216) → `nutrient_profiles.manganese_ppm` = 0.5, `nutrient_profiles.zinc_ppm` = 0.1, `nutrient_profiles.copper_ppm` = 0.05, `nutrient_profiles.molybdenum_ppm` = 0.05. In der Keimphase (EC 0) keine Mikronährstoffe.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Reifer Kompost | eigen | organisch | 3–5 L/m² | Frühjahr, Einarbeitung | medium_feeder |
| Horngrieß | Oscorna | organisch-N | 50–80 g/m² | Pflanzung | medium_feeder |
| Gemüsedünger organisch | Neudorff Azet | organisch | 60–80 g/m² | Vegetativ | Gemüse allg. |

### 3.2 Besondere Hinweise zur Düngung

Fenchel braucht mäßige Nährstoffe — auf zu nährstoffreichen Böden bildet er viel Kraut und wenig Knolle. Kompost als Grundversorgung reicht meist. Kaliumbetonung in der Knollenphase fördert aromatische Inhaltsstoffe. Kein mineralischer Stickstoff-Überschuss.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Feuchte; Trockenheit fördert Schießen; kein Wasser auf Knolle direkt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 6, 7, 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mai (ab 20.) | Direktsaat | Nach Eisheiligen; Reihenabstand 30 cm; 1–2 cm tief | hoch |
| Jun–Jul | Hauptaussaatzeit | Optimale Norddeutschland-Aussaat; schießfeste Sorten | hoch |
| Jun–Aug | Jäten + Vereinzeln | Auf 25–30 cm ausdünnen | mittel |
| Aug–Okt | Ernte | Bei Knollendurchmesser 8–10 cm; knapp über Boden abschneiden | hoch |
| Okt | Beetpflege | Reste kompostieren; kein Fenchel auf gleicher Fläche im Folgejahr | niedrig |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

Knollenfenchel wird in Mitteleuropa (USDA 6–8) als einjährige Kultur gezogen und ist frostempfindlich (half_hardy; verträgt nur leichten Frost bis ca. -5 °C). Eine echte Überwinterung der Pflanze im Freiland ist nicht vorgesehen. Geerntete Knollen lassen sich jedoch frostfrei einlagern; nicht abgeerntete Pflanzen können im Kübel frostfrei überwintert werden.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 2–10 (kühl, frostfrei; Knollenlagerung ca. 1–4 °C in feuchtem Sand) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell bis kühl-schattig (bei Kübelhaltung hell; reine Knollenlagerung dunkel) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam, nur Ballen leicht feucht halten | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** `frost_free` gewählt, weil die frostempfindliche Pflanze/Knolle frostfrei drinnen überwintert wird — nicht `dig_and_store` (das gilt für ausdauernde Knollen-/Zwiebelgewächse wie Dahlie/Gladiole, die jährlich wieder austreiben; Knollenfenchel treibt nach Einlagerung nicht erneut zur Knolle aus).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Möhrenfliege | Psila rosae | Larvenfraß an Knollenbasis | root, bulb | knollenentwicklung | difficult |
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen | shoot, leaf | seedling, vegetative | easy |
| Schnecken | Arion spp. | Fraß an Jungpflanzen | leaf | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Trockenheit + Wärme | 5–10 | vegetative |
| Fenchelfäule | bacterial | Braune, weiche Knollenteile | Verletzungen, Nässe | 3–7 | bulb |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Schwebfliegen (Syrphidae) | Blattläuse | natürlich anlocken durch Blüten | — |
| Schlupfwespen | Blattläuse | natürlich vorhanden | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Blattlaus-Schlupfwespe (Aphidius colemani) | Blattläuse (Aphis spp.) | 0,1–3 Tiere/m² (wöchentlich bis Etablierung) | 14 (mind. 2 Freilassungen im Wochenabstand) |
| Gallmücke (Aphidoletes aphidimyza) | Blattläuse (Aphis spp.) | 2–5 Puppen/m² (Wiederholung nach 2–4 Wochen) | 14–28 |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Feinmaschiges Netz | cultural | — | 0,9 mm Maschenweite ab Keimung | 0 | Möhrenfliege |
| Neemöl | biological | Azadirachtin | 0,5% Sprühlösung | 3 | Blattläuse |
| Schneckenkorn | chemical | Eisenphosphat | 5 g/m² | 0 | Schnecken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Doldenblütler (Apiaceae) |
| Empfohlene Vorfrucht | Leguminosen; Starkzehrer (Kohl) |
| Empfohlene Nachfrucht | Leguminosen, Zwiebelgewächse |
| Anbaupause (Jahre) | 2–3 Jahre; keine Apiaceae auf gleicher Fläche (Möhrenrost, Fenchelfäule) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kopfsalat | Lactuca sativa | 0.6 | Toleriert Fenchel-Geruch; Bodenschutz | `compatible_with` |
| Gurke | Cucumis sativus | 0.5 | Toleriert Fenchel besser als andere Gemüse | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Starke Wachstumshemmung durch Terpene | severe | `incompatible_with` |
| Kohl | Brassica spp. | Allelopathische Hemmung | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Fenchel hemmt Keimung | severe | `incompatible_with` |
| Bohne | Phaseolus vulgaris | Ertragsdepression | moderate | `incompatible_with` |
| Möhre | Daucus carota | Geteilter Schädling (Möhrenfliege) | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Wachstumshemmung | moderate | `incompatible_with` |

**Praxistipp:** Fenchel möglichst in einem eigenen Beet oder am Beetrand anpflanzen — die Allelopathie-Wirkung ist ausgeprägter als bei den meisten anderen Gemüsekräutern.

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Apiaceae | `shares_pest_risk` | Möhrenfliege, Selleriefliege | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Fenchel |
|-----|-------------------|-------------|---------------------------|
| Gewürzfenchel | Foeniculum vulgare var. vulgare | Gleiche Art, andere var. | Winterhart; kein Knollenfenchel; Samen/Kraut |
| Sellerie | Apium graveolens | Gleiche Familie | Besser in Mischkultur verträglich |
| Pastinake | Pastinaca sativa | Gleiche Familie | Winterhart; leicht anders im Anbau |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Foeniculum vulgare var. azoricum,"Knollenfenchel;Gemüsefenchel;Florence Fennel;Finocchio",Apiaceae,Foeniculum,biennial,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",-0.5,"Mittelmeerraum",limited,18,30,80,30,28,no,limited,false,false,medium_feeder,half_hardy,"5;6;7","8;9;10"
```

---

## Quellenverzeichnis

1. [Plantura Fenchel](https://www.plantura.garden/gemuese/fenchel/fenchel-anpflanzen) — Anbau, Aussaat, Mischkultur
2. [Samen.de Fenchel](https://samen.de/blog/fenchel-erfolgreich-anbauen-umfassender-leitfaden-von-der-aussaat-bis-zur-ernte.html) — Anbaupraxis, Norddeutschland
3. [Kraut&Rüben Knollenfenchel](https://www.krautundrueben.de/steckbrief-knollenfenchel) — Steckbrief, Sortenempfehlungen
4. [Bio-Gärtner Fenchel](https://www.bio-gaertner.de/Pflanzen/Fenchel) — Ökologischer Anbau
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — How to grow Florence Fennel](https://www.rhs.org.uk/vegetables/florence-fennel/grow-your-own) — Standort (Vollsonne), Boden, Staunässe-Empfindlichkeit, Schossneigung
6. [Wisconsin Horticulture — Fennel, Foeniculum vulgare](https://hort.extension.wisc.edu/articles/fennel-foeniculum-vulgare/) — Biennie/Einjährigkeit, Schossen durch Vernalisation + Langtag + Trockenheit
7. [USU Extension — How to Grow Fennel in Your Garden](https://extension.usu.edu/yardandgarden/research/fennel-in-the-garden) — Vollsonne, pH 6,0–7,0, gleichmäßige Feuchte, Schossen
8. [Semiz & Suarez (2015) — Yield response of fennel (Foeniculum vulgare Mill.) to irrigation with saline water, Acta Agriculturae Scandinavica B](https://www.tandfonline.com/doi/full/10.1080/09064710.2014.888469) — Maas-Hoffman-Salztoleranz (Schwelle 1.26 dS/m, Slope 14.24 %/dS/m), Klassifikation "moderately salt sensitive"
9. [Performance of Fennel under Saline Water Irrigation (semi-arid), ResearchGate](https://www.researchgate.net/publication/305442895) — zweite Salztoleranz-Studie (Schwelle 2.64 dS/m, Slope 4.5 %)
10. [Kamkar et al. — Influence of Temperature on Seed Germination Response of Fennel](https://www.researchgate.net/publication/269994571_Influence_of_Temperature_on_Seed_Germination_Response_of_Fennel) — Keim-Basistemperatur ~5 °C (Kardinaltemperaturen der Keimung; KEIN Wuchs-GDD-Wert)
11. [Harvest to Table — How to Plant and Grow Florence Fennel](https://harvesttotable.com/how_to_grow_florence_fennel/) — optimale Wachstumstemperatur 15–24 °C, Schossen durch Hitze/Langtag, Wurzeltiefe/Topftiefe
12. [Grow Organic — Overwintering Fennel](https://www.groworganic.com/blogs/articles/overwintering-fennel-a-comprehensive-guide) — frostfreie Überwinterung, Knollen-Lagerung (kühl, feucht)
13. [Penn State Extension — Hydroponics: Essential Nutrients](https://extension.psu.edu/hydroponics-systems-and-principles-of-plant-nutrition-essential-nutrients-function-deficiency-and-excess) — allgemeine Gemüse-Mikronährstoff-Richtwerte (Mn/Zn/Cu/Mo)
14. [UF/IFAS CV216 — Nutrient Solution Formulation for Hydroponic Tomatoes](https://edis.ifas.ufl.edu/publication/CV216) — Mikronährstoff-Standardkonzentrationen Gemüse
15. [Sound Horticulture / PMC — Aphidius colemani & Aphidoletes aphidimyza Ausbringraten](https://soundhorticulture.com/pages/aphids) — Nützling-Ausbringraten gegen Blattläuse (0,1–3 Tiere bzw. 2–5 Puppen/m²)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 (cycle_type/cultivation_cycle_type-Korrektur) -->
16. [RHS — Foeniculum vulgare var. azoricum details](https://www.rhs.org.uk/plants/158862/foeniculum-vulgare-var-azoricum/details) — "A biennial plant..."; botanischer Lebenszyklus biennial, Blüte Hochsommer/Spätsommer
17. [NC State Extension Gardener Plant Toolbox — Foeniculum vulgare](https://plants.ces.ncsu.edu/plants/foeniculum-vulgare/) — Art als "herbaceous perennial", "normally grown as an annual"; Bestätigung Anbau-Praxis ≠ botanischer Zyklus
18. [Almanac.com — Fennel: Planting, Growing, and Harvesting Fennel Bulbs](https://www.almanac.com/plant/fennel) — "Florence fennel is biennial but grown as an annual for bulbs. Left in the ground, it will flower and set fennel seeds in year two."
19. [Gardenia.net — Fennel Bulb (Foeniculum vulgare var. azoricum)](https://www.gardenia.net/plant/foeniculum-vulgare-var-azoricum-fennel-bulb) — "the biennial bulging fennel grown as an annual for eating"
<!-- /Quelle: growing-phase-auditor 2026-07 (cycle_type/cultivation_cycle_type-Korrektur) -->
