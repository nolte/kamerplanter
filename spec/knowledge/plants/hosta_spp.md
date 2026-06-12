# Funkie — Hosta spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Lubera Hosta, Pflanzen-Kölle Funkien, Gartenrat.de Funkien, Baldur-Garten Funkien

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hosta spp. (Sammelbezeichnung für Garten-Funkien; häufigste: H. plantaginea, H. sieboldiana, H. fortunei) | `species.scientific_name` |
| Volksnamen (DE/EN) | Funkie, Herzlilie; Hosta, Plantain Lily | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Hosta | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 (Schatten-/Unterwuchsstaude, kein CAM/C4) | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Hosta auffindbar; Keimwerte nicht als Wuchsbasis umetikettiert --> | `species.base_temp` |
| Lebensdauer (Jahre) | 20–30+ (langlebige Staude, oft Jahrzehnte am Standort) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (Winterruhe; oberirdische Teile sterben ab) | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich (vernalization/chilling) | true (Chilling/Endodormanz-Bruch, KEINE echte Vernalisation) | `lifecycle_configs.vernalization_required` |
| Vernalisation/Chilling Mindest-Tage | 70–84 (≈ 600–700 h unter 4 °C, ≈ 10–12 Wochen; Minimum ~30 Tage < 4 °C) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: Art ist tagneutral (day_neutral), kein Kurztag-/Langtag-Blühreiz; numerisches Stunden-Feld bleibt leer --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; oberirdische Teile sterben ab; Rhizom überwintert sicher; in Norddeutschland absolut problemlos | `species.hardiness_detail` |
| Heimat | Ostasien (Japan, Korea, China) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Teilung bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Blätter jung essbar in asiatischer Küche) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (H. sieboldiana: Jun; H. plantaginea: Aug–Sep, duftend) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Teile für Katzen und Hunde (ASPCA-Liste) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Saponine (für Tiere; beim Menschen in normalen Mengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (Tiere: Erbrechen, Durchfall) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11, 3 | `species.pruning_months` |

**Hinweis:** Abgestorbenes Laub im Herbst oder Frühjahr bodennah entfernen. Blütenstände nach Verblühen abschneiden (verhindert Energie-Verlust durch Samenbildung). Im März trockenes altes Laub vor dem Neuaustrieb entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 (je nach Größe der Sorte) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–120 (stark sortabhängig: Zwerge 15 cm bis Riesen 120 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–150 (stark sortabhängig) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–80 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut wasserhaltende Erde; pH 6,0–7,0; gute Drainage; kein Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 8 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 16 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–30 (flacheres System als typische Stauden; max. ~30 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (gleichmäßig feucht, aber drainiert; Staunässe tötet das Rhizom) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (verträgt geringe Streusalzbelastung; bei Anhäufung Stress) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (a) für Hosta auffindbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope (b) für Hosta auffindbar --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 (leicht sauer; harmonisiert mit §1.6 / §2.3) | `species.soil_ph_preference` |

**Hinweis (Freitext):** Lichtsättigung tritt bei Hosta erst sehr hoch ein — Studien zeigen keine Sättigung der Netto-Photosynthese im Bereich 100–1200 µmol/m²/s bei akklimatisierten Pflanzen; der oben angegebene Wert ist ausschließlich der Kompensationspunkt (Netto-Photosynthese = 0), nicht der Sättigungspunkt. Streusalz: Bei vorhandenem Streusalz-Eintrag salzärmere Auftaumittel (Calcium-/Magnesiumchlorid, CMA) statt NaCl bevorzugen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum | 60–90 | 2 | false | false | medium |
| Blüte | 21–42 | 3 | false | false | medium |
| Herbstrückzug | 30–60 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum (Haupt-Schaupflanzungsphase)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 (Schatten bis Halbschatten; KEIN direktes Mittagssonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 (kritischer Punkt stomatären Kollaps; oberer Zielwert 1.0 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high (mesophytische Schattenstaude; reagiert empfindlich auf trockene Luft) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 (kühl-feuchte Optimaltemperatur) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 (Unterwuchs/Schatten; R:FR erniedrigt) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Hinweis:** Variegierte (buntblättrige) Sorten brauchen mehr Licht als grünblättrige. H. plantaginea verträgt mehr Sonne als andere Arten. Je grüner das Blatt, desto tiefer der Schatten verträglich.

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | – | 2 | 0.5 | 0.05 | 0.05 | 0.05 |
| Vegetatives Wachstum | 2:1:2 | 1.0–1.4 | 6.0–6.5 | 100 | 50 | – | 2 | 0.5 | 0.1 | 0.05 | 0.05 |
| Blüte | 1:2:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | – | 1 | 0.3 | 0.05 | 0.03 | 0.03 |
| Herbstrückzug | 0:1:2 | 0.4–0.6 | – | – | – | – | – | – | – | – | – |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – | – | – | – | – |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis zu Mikronährstoffen (Mn/Zn/Cu/Mo):** Die angegebenen ppm-Werte entsprechen üblichen Standard-Mikronährstoff-Zielkonzentrationen einer ausgewogenen Nährlösung (Hoagland-typisch) und sind nicht Hosta-spezifisch belegt; sie dienen als Richtwerte für `medium_feeder`-Stauden. In humusreicher Freilanderde werden Mikronährstoffe i.d.R. ausreichend nachgeliefert.

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 3–5 L/m² | März, Oktober | Bodenverbesserung |
| Hornmehl | Oscorna | organisch | 30–50 g/m² | April | N-Grundversorgung |
| Stauden-Langzeitdünger | Substral Osmocote | slow_release | 30 g/m² | April | medium_feeder |
| Flüssig-Blumendünger | Substral | organisch-mineral | 5 ml/10L alle 14 Tage | April–August | Topf |

### 3.2 Besondere Hinweise zur Düngung

Hosta ist ein moderat zehrender Standlauber. Kompostgaben im Frühjahr und Herbst reichen für Freilandpflanzen. Im Topf alle 2–3 Wochen schwach flüssig düngen. Kein Dünger nach August (Holzreife; Ruhevorbereitung). Überversorgung mit N macht Blätter weniger dekorativ und weich (Schnecken-Anlass).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | temperate | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; feuchter Boden gewünscht; kein Staunässe; gleichmäßige Feuchtigkeit | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 (alle 3 Jahre teilen wenn zu dicht) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wegen Schnecken!) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Altes Laub entfernen | Vor dem Austrieb; Schneckenbarriere legen | hoch |
| Apr | Düngung | Hornmehl + Kompost; gut einarbeiten | hoch |
| Apr | Schneckenschutz | SOFORT bei Austrieb; Schnecken fressen junge Triebe | hoch |
| Mai–Jun | Blattentfaltung | Hauptdekorationsphase beginnt | – |
| Jun–Aug | Blüte | Blütenstände nach Verblühen abschneiden | mittel |
| Aug | Letzte Düngung | Kein N; eventuell K für Winterhärtung | niedrig |
| Okt–Nov | Laub abschneiden | Bodennah; kompostieren | niedrig |
| Alle 3–5 J. | Teilung | Wenn Horst zu groß wird; im Frühjahr oder Herbst | niedrig |

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
| Schnecken | Arion spp., Limax spp. | Löcher in Blättern; manchmal kompletter Kahlfraß junger Triebe | leaf, shoot | spring (Austrieb) | easy |
| Blattläuse | Aphis spp. | Selten; Kolonien an Triebspitzen | shoot | spring | easy |
| Dickmaulrüssler | Otiorhynchus sulcatus | Buchtige Fraßstellen am Blattrand | leaf | vegetative | medium |

**Wichtig:** Schnecken sind DAS Hauptproblem bei Hosta. Weichblättrige Sorten wie H. plantaginea werden besonders bevorzugt. Festblättrige Sorten (H. sieboldiana 'Elegans') mit dicken Blättern sind deutlich schneckenresistenter.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Virosen (HVX — Hosta Virus X) | viral | Mosaikmuster auf Blättern; Deformation; Farbveränderung | Infiziertes Werkzeug; Säfte | — | alle |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel | Feuchte, Staunässe | 3–7 | spring, autumn |
| Blattflecken | fungal (Phyllosticta spp.) | Braune Flecken | Feuchte | 7–14 | vegetative |

**Warnung:** Hosta Virus X (HVX) ist durch Saft übertragbar. Werkzeug desinfizieren zwischen Teilungen (10% Bleiche oder Ethanol). Infizierte Pflanzen sofort entfernen und vernichten.

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schneckenkorn (Eisenphosphat) | biological | Eisenphosphat | Ausstreuen abends | 0 | Schnecken |
| Kupferband | cultural | Kupfer | Um Beet oder Topf | 0 | Schnecken |
| Werkzeug desinfizieren | cultural | Ethanol | Vor jeder Teilung | 0 | HVX |
| Infizierte Pflanzen entfernen | cultural | – | Sofort; vernichten | 0 | HVX |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (Wiss. Name) | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|-----------------------|----------------|--------------|-------------------|
| Phasmarhabditis hermaphrodita (parasitischer Nematode, "Nemaslug") | Schnecken (Arion/Limax spp.) | ~300.000 Infektionsjuvenile/m² (Feldspanne 50.000–600.000/m²) | Schnecken sterben in 4–21 Tagen; ~6 Wochen Schutzwirkung |
| Steinernema kraussei / Heterorhabditis megidis (entomopathogene Nematoden) | Dickmaulrüssler-Larven (Otiorhynchus sulcatus) | ~23.000–50.000 Infektionsjuvenile/m² (Boden) | Larven sterben in wenigen Tagen; Boden > 5–9 °C (S. kraussei kälteaktiv) nötig |
| Aphidius colemani (Schlupfwespe) | Blattläuse (Aphis spp.) | 0,25–4 Tiere/m² je Freilassung, ≥ 2–3 Freilassungen im Wochenabstand | Mumienbildung nach ~10–14 Tagen; mehrere Generationen zur Etablierung |
| Aphidoletes aphidimyza (Gallmücke, räuberische Larve) | Blattläuse (Aphis spp.) | ~0,5–1 Tier/m² (Hotspots höher), wöchentlich bis etabliert | Larven aktiv nach ~3–7 Tagen; Etablierung über mehrere Wochen |

**Hinweis:** Schnecken-Nematoden und Dickmaulrüssler-Nematoden mit Wasser ins feuchte Substrat einschlämmen; Bodentemperatur und Feuchte beachten. Aphidius/Aphidoletes wirken primär in geschütztem Anbau / Topfkultur an befallenen Trieben.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Farn | Dryopteris filix-mas | 0.9 | Gleiche Schattenstandorte; optisch ergänzend | `compatible_with` |
| Waldgeißbart | Aruncus dioicus | 0.8 | Gleicher Standort; ergänzende Höhe | `compatible_with` |
| Astilbe | Astilbe spp. | 0.9 | Gleiche Feuchtestandorte; Blütenergänzung | `compatible_with` |
| Maiglöckchen | Convallaria majalis | 0.7 | Frühling-Vorläufer | `compatible_with` |
| Storchschnabel | Geranium spp. | 0.8 | Bodendecker; Lückenschluss | `compatible_with` |

### 6.2 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sonnenhungrige Stauden | diverse | Hosta braucht Schatten; keine Konkurrenz mit Sonnenstauden am gleichen Standort | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Hosta spp. |
|-----|-------------------|-------------|-------------------------------|
| Funkie (Duft) | Hosta plantaginea | Gleiche Gattung | Duftende Blüten (August–September); mehr Sonne |
| Riesen-Funkie | Hosta sieboldiana 'Elegans' | Gleiche Gattung | Sehr groß; schneckenresistenter |
| Astilbe | Astilbe spp. | Gleicher Standort | Für Feuchtestandorte; Blütenakzente |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Hosta spp.,"Funkie;Herzlilie;Hosta;Plantain Lily",Asparagaceae,Hosta,perennial,day_neutral,herb,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Ostasien, Japan, Korea, China",yes,20,25,120,150,60,no,yes,false,false,medium_feeder,false,hardy,"6;7;8"
```

---

## Quellenverzeichnis

1. [Lubera Hosta pflanzen](https://www.lubera.com/de/gartenbuch/hosta-pflanzen-p3346) — Kultivierung, Standort
2. [Pflanzen-Kölle Funkien](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-funkien-richtig/) — Pflege, Schnecken
3. [Gartenrat.de Funkien](https://gartenrat.de/funkien/) — Pflege-Anleitung
4. [Baldur-Garten Funkien](https://www.baldur-garten.de/onion/content/pflege-tipps/blumenzwiebeln/funkien) — Teilung, Pflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [SDSU Extension — Hosta: A Shade-loving Perennial](https://extension.sdstate.edu/hosta-shade-loving-perennial) — Schattentoleranz, Standort, Photosynthese-Typ (C3 Schattenstaude)
6. [Garden Design — Hostas: How to Grow & Care](https://www.gardendesign.com/plants/hosta.html) — Wurzeltiefe (~30 cm), Schatten, langlebige Staude
7. [BBC Gardeners' World — How to grow hostas](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-hostas/) — Standort, gleichmäßig feucht/drainiert (Staunässe-Empfindlichkeit)
8. [Home for the Harvest — Do hostas like acid soil?](https://homefortheharvest.com/do-hostas-like-acid-soil/) — Boden-pH ~6,0 (leicht sauer)
9. [ScienceDirect — Light Compensation (Übersicht)](https://www.sciencedirect.com/topics/engineering/light-compensation) — Lichtkompensationspunkt C3-/Schattenpflanzen (8–16 µmol/m²/s)
10. [Springer / In Vitro Cell. Dev. Biol. — Hosta 'Blue Vision' Net-Photosynthese](https://link.springer.com/article/10.1079/IVP2003414) — keine Lichtsättigung 100–1200 µmol/m²/s (Schattenakklimatisierung)
11. [Rewela Hostas — Hosta Dormancy & Autumn Colour](https://www.rewelahostas.com/post/hosta-dormancy-autumn-colour) — Winterruhe/Chilling-Bedarf
12. [Plant Addicts — Hosta Winter Care](https://plantaddicts.com/hosta-winter-care/) — Chilling ~600–700 h < 4 °C, Mindest-Dormanz ~30 Tage
13. [Greg.app — Hosta lancifolia Temperature](https://greg.app/hosta-lancifolia-temperature/) — Optimaltemperatur 18–24 °C
14. [Bugs for Growers — Biological control of black vine weevil](https://bugsforgrowers.com/collections/biological-control-of-black-vine-weevil) — Steinernema/Heterorhabditis gegen Otiorhynchus-Larven, Ausbringrate
15. [Nematodes Direct — Nemaslug (Phasmarhabditis hermaphrodita)](https://www.nematodesdirect.co.uk/nemaslug/8-nemaslug) — Schnecken-Nematode ~300.000/m², ~6 Wochen Wirkung
16. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Blattlaus-Schlupfwespe, Ausbringrate/Etablierung
17. [Sound Horticulture — Aphid Tech Sheet (Aphidius/Aphidoletes)](https://soundhorticulture.com/pages/aphids) — Freilassungsraten Aphidius/Aphidoletes
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
