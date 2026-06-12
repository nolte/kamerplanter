# Kohlrabi — Brassica oleracea var. gongylodes

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Kohlrabi, Bio-Gärtner.de, LWK Niedersachsen, Beetfreunde.de

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. gongylodes | `species.scientific_name` |
| Volksnamen (DE/EN) | Kohlrabi, Oberrübe; Kohlrabi, Turnip Cabbage | `species.common_names` |
| Familie | Brassicaceae | `species.family` → `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | biennial (als Gemüse einjährig kultiviert) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4–5 (Kühljahres-/Kaltkultur; Wuchsoptimum 15–18 °C) | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true (Kältereiz < 11 °C löst Schossen aus; im Gemüsebau unerwünscht) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | 42–70 (6–10 Wochen 2–10 °C) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral bzgl. Knollenbildung; Schossen kälteinduziert, nicht photoperiodisch) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 2a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Jungpflanzen frostempfindlich; ausgewachsene Pflanzen überstehen −5 °C; Frühkohlrabi März–April mit Vlies | `species.hardiness_detail` |
| Heimat | Kultiviert (Wildform: Mittelmeerraum) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkultur Februar–März) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5, 6, 7, 8 (Staffelaussaat möglich) | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9, 10 (Frühsorten ab Mai) | `species.harvest_months` |
| Blütemonate | 5, 6 (zweites Jahr, falls nicht geerntet) | `species.bloom_months` |

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

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (mind. 10 L, kompakte Sorten) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 25–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche Kräutererde, pH 6,0–7,5; gleichmäßig feucht halten | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | 10–25 (typischer C3-Bereich; sonnenadaptierte Blätter im oberen Bereich) | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (verträgt Halbschatten, schosst dann aber leichter und bildet kleinere Knollen) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–45 (Flachwurzler; Feinwurzeln in den oberen 5–7 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 1.8 (Maas-Hoffman a; Bezug Substrat-ECe, nicht Gießwasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 9.7 (Maas-Hoffman b) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 (Optimum 6,5–7,0; harmonisiert mit §1.6/§2.3; höhere pH-Werte beugen Kohlhernie vor) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ / Knollenbildung | 30–60 | 3 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ & Knollenbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (stomatärer Kollaps oberhalb des Zielkorridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–18 (Kühljahres-/Kaltkultur; Wuchs- und Knollenbildungsoptimum) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht im Freiland) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (gleichmäßige Feuchte → kein Platzen der Knolle) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Sämling | 2:1:1 | 0.8–1.2 | 6.5–7.0 | 80 | 40 | — | 2 | 0.5 | 0.1 | 0.1 | 0.03 |
| Knollenbildung | 2:1:2 | 1.2–1.8 | 6.5–7.5 | 120 | 50 | 20 | 2 | 0.8 | 0.3 | 0.2 | 0.05 |<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
Mikronährstoffe Mn/Zn/Cu/Mo nach Standard-Nährlösungsempfehlungen für Gemüse/Brassicaceen (Mn `nutrient_profiles.manganese_ppm`, Zn `nutrient_profiles.zinc_ppm`, Cu `nutrient_profiles.copper_ppm`, Mo `nutrient_profiles.molybdenum_ppm`). Mo unterstützt die Nitratreduktase (N-Stoffwechsel) — bei Brassicaceen auf saurem Boden gelegentlich Mangelfaktor ("Whiptail" / Peitschenwuchs).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–4 L/m² | Vor der Aussaat |
| Hornmehl | Oscorna | organisch-N | 40–60 g/m² | Vor der Pflanzung |

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Gemüsedünger | Compo | base | 12-7-14 | 30–50 g/m² | Wachstum |

### 3.2 Besondere Hinweise zur Düngung

Kohlrabi ist Mittelzehrer und braucht keine intensive Düngung bei gutem Boden. Zu viel Stickstoff führt zu übermäßigem Blattwachstum. Gleichmäßige Wasserversorgung ist entscheidend — Trockenheit gefolgt von starker Bewässerung führt zum Platzen der Knolle. Kalkversorgung für Calciumaufnahme sicherstellen (verhindert Herzfäule).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig feucht — kein Austrocknen; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur | Aussaat in Anzuchttöpfe bei 15–18 °C | mittel |
| Apr | Auspflanzen (Frühsatz) | Mit Vlies vor Frost schützen | hoch |
| Mai–Jun | Jäten und Gießen | Unkrautfreihalten; gleichmäßig gießen | mittel |
| Jun–Jul | Ernte Frühsatz | Knolle bei 5–8 cm Durchmesser ernten | hoch |
| Jul–Aug | Nachsatz aussäen | Für Herbst-Kohlrabi | mittel |
| Sep–Okt | Herbst-Ernte | Spätsorten vor starkem Frost ernten | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweißling | Pieris brassicae / P. rapae | Kahlfraß, Kotspuren | leaf | vegetative | easy |
| Erdfloh | Phyllotreta spp. | Kleine Löcher (Schrotschuss-Muster) | leaf | seedling | medium |
| Mehlige Kohlblattlaus | Brevicoryne brassicae | Weißliche Kolonien, Kräuselung | leaf | vegetative | easy |
| Kohlfliege | Delia radicum | Larvenbefall an Wurzeln, Welke | root | seedling | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Clubwurzel (Kohlhernie) | protist (Plasmodiophora brassicae, Phytomyxea; KEIN Pilz) | Knollenartige Wurzelwucherungen | saurer Boden (pH < 6,5) | 14–21 | all |
| Falscher Mehltau | fungal | Gelbe Flecken, weißer Belag | Feuchtigkeit | 5–10 | seedling |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|-----------------------|---------------------|----------------|--------------|-------------------|
| Schlupfwespe (Trichogramma) | Trichogramma brassicae | Kohlweißling, Kohleule (Eier) | ~20–50 Wespen/m² (Eikarten), wöchentlich bei Falterflug | 1–2 Wochen |
| Brackwespe (Cotesia) | Cotesia glomerata | Kohlweißling-Raupen (Pieris brassicae) | Förderung durch Blühstreifen (Naturansiedlung) | 2–4 Wochen |
| Schlupfwespe (Diadegma) | Diadegma semiclausum | Kohlmotte (Plutella xylostella) | Naturansiedlung, Blühstreifen-Förderung | 2–4 Wochen |

Hinweis: Trichogramma wird als Eikarten ausgebracht und parasitiert die Falter-Eier vor dem Raupenschlupf — Timing am Flugbeginn entscheidend. Cotesia und Diadegma etablieren sich überwiegend durch Förderung mit Nektarpflanzen (selektive Blühstreifen) statt durch kommerzielle Freilassung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Feinmaschig | 0 | Kohlweißling, Kohlfliege, Erdfloh |
| Bt-Präparat | biological | Bacillus thuringiensis | Sprühen | 0 | Kohlweißling |
| Kalkung | cultural | Algenkalk | 100 g/m² | 0 | Clubwurzel |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kreuzblütengewächse (Brassicaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte, Erbsen |
| Empfohlene Nachfrucht | Möhren, Zwiebeln, Salat |
| Anbaupause (Jahre) | 3–4 Jahre keine Brassicaceen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sellerie | Apium graveolens | 0.8 | Gegenseitige Förderung, Erdfloh-Abwehr | `compatible_with` |
| Dill | Anethum graveolens | 0.8 | Nützlingsförderung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Platzsparend, Bodenbeschattung | `compatible_with` |
| Zwiebeln | Allium cepa | 0.7 | Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Schlechte Verträglichkeit | moderate | `incompatible_with` |
| Alle Brassicaceen | Brassica spp. | Gleiche Schädlinge, Clubwurzel | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Kohlrabi |
|-----|-------------------|-------------|---------------------------|
| Brokkoli | Brassica oleracea var. italica | Gleiche Familie | Höherer Nährwert, länger haltbar |
| Steckrübe | Brassica napus | Knollengemüse | Winterhärter, lagerfähiger |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Brassica oleracea var. gongylodes,"Kohlrabi;Oberrübe;Turnip Cabbage",Brassicaceae,Brassica,biennial,long_day,herb,fibrous,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Kultiviert (Wildform: Mittelmeerraum)",yes,15,20,50,40,28,no,yes,false,false,medium_feeder,half_hardy,"4;5;6;7;8","5;6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Plantura Kohlrabi](https://www.plantura.garden/gemuese/kohlrabi) — Anbau, Erntezeit, Pflege
2. [Beetfreunde.de Kohlgemüse](https://www.beetfreunde.de/magazin/kohlgemuese/) — Sortenüberblick
3. [LWK Niedersachsen](https://www.lwk-niedersachsen.de/) — Regionaler Anbau Norddeutschland
4. [Heimbiotop.de Brassica](https://www.heimbiotop.de/brassica.html) — Kohl-Übersicht
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Shannon & Grieve, USDA-ARS: Tolerance of vegetable crops to salinity](https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P1567.pdf) — Salztoleranz Kohl (ECe-Schwelle, Slope, Klasse moderately sensitive)
6. [Sanoubar et al. 2016, J. Sci. Food Agric.: Salinity thresholds of cabbage (Brassica oleracea)](https://scijournals.onlinelibrary.wiley.com/doi/abs/10.1002/jsfa.7097) — Bestätigung Maas-Hoffman-Schwellwerte
7. [ScienceDirect: Quantification of vernalization for kohlrabi (B. oleracea var. gongylodes)](https://www.sciencedirect.com/science/article/abs/pii/S0304423805800044) — Vernalisationsschwelle < 11 °C, Schoss-/Devernalisationsverhalten
8. [MSU Extension: Bolting in spring vegetables](https://www.canr.msu.edu/news/bolting-in-spring-vegetables) — Vernalisation Kohl/Kohlrabi 6–10 Wochen 2–10 °C
9. [SeedSavers: Growing Guide Kohlrabi](https://seedsavers.org/grow-kohlrabi/) — Kühljahreskultur, Standort, Aussaat
10. [Oregon State Univ., Oregon Vegetables: Cabbage](https://horticulture.oregonstate.edu/oregon-vegetables/cabbage-1) — Boden-pH, Wuchsoptimum, Standort
11. [Portland Nursery: Cabbage site requirements (PDF)](https://portlandnursery.com/docs/veggies/cabbage.pdf) — Lichtbedarf full sun, Bodenansprüche
12. [GrowItBuildIt: Mature root depth of common vegetables](https://growitbuildit.com/mature-root-depth-of-common-vegetables/) — Wurzeltiefe Kohl 30–45 cm, Flachwurzler
13. [ScienceDirect Topics: Compensation Point](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/compensation-point) — Lichtkompensationspunkt C3-Pflanzen
14. [ASHS HortTechnology: Far-red photons & light compensation point (tomato)](https://journals.ashs.org/view/journals/horttech/35/2/article-p186.xml) — Far-Red-Anteil, offenes Tageslicht ≈ 0,5
15. [UF/IFAS EDIS CV216: Nutrient Solution Formulation for Hydroponic crops](https://ask.ifas.ufl.edu/publication/CV216) — Mikronährstoff-Richtwerte (Mn/Zn/Cu/Mo ppm)
16. [Envirevo Agritech: Hydroponic nutrient requirements per stage](https://envirevoagritech.com/optimizing-hydroponic-nutrients-requirements/) — Bestätigung Mikronährstoff-Spannen
17. [Trichogramma Tech Sheet, Sound Horticulture](https://soundhorticulture.com/pages/trichogramma-tech-sheet) — Trichogramma-Ausbringrate Kohlweißling
18. [BIOCOMES EU: Cabbage moth biological control](https://www.biocomes.eu/pest/cabbage-moth) — Nützlinge Cotesia/Diadegma gegen Kohlschädlinge
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
