# Estragon — Artemisia dracunculus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Ellis Garten Estragon, Plantura Estragon pflegen, Gartenrat Estragon, Hausgarten Estragon, Kiepenkerl Estragon

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Artemisia dracunculus | `species.scientific_name` |
| Volksnamen (DE/EN) | Estragon, Bertram, Dragon; Tarragon | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Artemisia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Französischer Estragon: winterhart bis -11°C; in Norddeutschland Frostschutz nötig; Russischer Estragon (var. inodorus): robuster bis -25°C, aber schlechteres Aroma | `species.hardiness_detail` |
| Heimat | Zentralasien, Sibirien | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: keine artspezifisch publizierte GDD-Basis aus zwei seriösen Quellen belegbar --> | `species.base_temp` |
| Lebensdauer (Jahre, perennial) | 3–5 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (keine Blüh-Vernalisation belegt) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral; kein echter Kurz-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**WICHTIG:** Es gibt zwei Varietäten mit SEHR unterschiedlicher Qualität:
- **Artemisia dracunculus var. sativus** (Französischer Estragon): Intensiv aromatisch (Anis, Fenchel); STERIL (keine Samen); nur durch Stecklinge/Teilung vermehrbar
- **Artemisia dracunculus** (Russischer Estragon): Milderes, oft bitteres Aroma; bildet Samen; aus Samen züchtbar; robuster

Beim Kauf unbedingt Sorte beachten — Stecklinge/Topfpflanzen sind meist Französ. Estragon.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge; Russischer: 6–8 Wochen Vorkultur) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (Französ. Estragon: keine Aussaat möglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5 (nur Russischer Estragon) | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (Triebspitzen und Blätter vor der Blüte am aromatischsten) | `species.harvest_months` |
| Blütemonate | 7, 8 (unscheinbar; beim Französ. Estragon selten) | `species.bloom_months` |

**Ernte-Tipp:** Triebspitzen und junge Blätter ernten (5–10 cm). Beste Aromaentwicklung vor/während der Blüte. Regelmäßige Ernte fördert buschigen Wuchs und verzögert Verholzung.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge im Mai/Juni (10–15 cm, halbreif). Rhizomteilung im Frühjahr alle 3–4 Jahre empfohlen (verjüngt die Pflanze). Französ. Estragon NIEMALS aus Samen (steril).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (in Küchenmengen sicher) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Estragol (bei sehr großen Mengen mutagen; in normalen Gewürzmengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10 (Herbst; auf 10–15 cm zurückschneiden für Winterschutz) | `species.pruning_months` |

**Hinweis:** Im Herbst (Oktober) auf 10–15 cm zurückschneiden. Kurzer Stumpf und Mulch/Reisig als Winterschutz für Französ. Estragon in Norddeutschland. Im Frühjahr (März) aufräumen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Kräutererde mit Sandanteil; pH 6,0–7,5; sehr gute Drainage; keine Nässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt aus zwei seriösen Quellen belegbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt aus zwei seriösen Quellen belegbar --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: Quellen nennen nur "flachwurzelnd/shallow", keine belegte cm-Spanne --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: kein Maas-Hoffman-a-Schwellenwert (Substrat-ECe) aus zwei seriösen Quellen belegbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-b-Wert aus zwei seriösen Quellen belegbar --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.5–7.5 | `species.soil_ph_preference` |

**Hinweis:** Estragon ist eine ausgesprochene Sonnenpflanze (full sun), verträgt in heißen Sommerlagen leichten Nachmittagsschatten. Flachwurzelnd (shallow-rooted) auf rhizombasierten, kriechenden Ausläufern; gegenüber Staunässe (waterlogging) ausgeprägt empfindlich (Wurzel-/Kronenfäule). NaCl-Salzstress reduziert Höhe, Trockenmasse, relativen Wassergehalt und Chlorophyll bereits bei moderaten Konzentrationen — Einstufung als mäßig salzempfindlich (moderately sensitive). Boden-pH-Vorzug neutral bis leicht alkalisch; harmoniert mit den pH-Angaben in §1.6/§2.3 (6,0–7,5), der hier ergänzte engere Vorzugskorridor 6,5–7,5 ist quellentreu (RHS/PFAF/Old Farmer's Almanac).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum (Ernte) | 60–90 | 2 | false | true | medium |
| Blüte (gering) | 14–28 | 3 | false | true | high |
| Herbstabreife | 30–45 | 4 | false | true | high |
| Winterruhe | 120–150 | 5 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum / Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (vollsonnig bis halbschattig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.20 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 (Mikronährstoff-Spalten Mn/Zn/Cu/Mo ergänzt) -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Frühjahrsaustrieb | 1:0:1 | 0.4–0.8 | 6.0–7.5 | 60 | 30 | — | 2 | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN |
| Vegetativ / Ernte | 1:0:1 | 0.4–0.8 | 6.0–7.5 | 60 | 30 | — | 2 | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN | DATEN FEHLEN |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |

> **Mikronährstoff-Hinweis:** Für Estragon (Schwachzehrer, light feeder) sind keine artspezifischen Sollkonzentrationen für Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) aus zwei unabhängigen seriösen Quellen belegbar; daher als `DATEN FEHLEN` markiert. KA-Felder: `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- DATEN FEHLEN -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif, wenig) | eigen | organisch | 1–2 L/m² | März | Startdüngung |
| Kräuterdünger (stark verdünnt) | Compo Kräuter | organisch-mineralisch | 1/4 Empfehldosis | alle 4–6 Wochen | Topfkultur |

### 3.2 Besondere Hinweise zur Düngung

Estragon ist ein ausgeprägt schwacher Zehrer — zu viel Dünger führt zu kräftigem Wuchs mit weniger Aroma. Im Beet reicht einmalige Kompostgabe im Frühjahr. Im Topf sehr niedrig dosiert alle 4–6 Wochen. Kein Dünger ab August (Triebe sollen ausreifen).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 8.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Eher trocken halten; keine Staunässe; Topfoberfläche abtrocknen lassen vor dem Gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 (alle 3 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Austrieb beobachten | Frostschutz entfernen; Kompost einarbeiten | mittel |
| Apr–Sep | Regelmäßige Ernte | Triebspitzen ernten; fördert buschigen Wuchs | hoch |
| Okt | Rückschnitt | Auf 10–15 cm zurückschneiden | hoch |
| Nov | Winterschutz | Reisig/Stroh über Wurzelbereich; Topf schützen | hoch |
| Alle 3 J. | Teilung | Frühjahr; verjüngt; Aroma verbessert sich | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 0 (frostfrei) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

**Norddeutschland-Empfehlung:** Französ. Estragon (var. sativus) lieber in Topf pflanzen und im Winter in frostfreie Umgebung (Garage, kühles Treppenhaus) stellen. Alternativ: Russischer Estragon (robuster) für Freiland.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | vegetative | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste; Blattvergilbung | leaf | vegetative (Hitze/Trockenheit) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trocken + warm | 7–10 | vegetative (Sommer) |
| Wurzelfäule | fungal (Pythium) | Welken; braune Wurzeln | Staunässe | 7–14 | alle |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gute Drainage | cultural | — | Substrat verbessern; kein Staunässe | 0 | Wurzelfäule |
| Neemöl | biological | Azadirachtin | 0.5% sprühen; nicht auf Ernteblätter | 3 | Spinnmilben, Blattläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilben (Tetranychus urticae) | 10–30 Stück/m² (Hotspot; bei Erstbefall, 1–2× wöchentlich wiederholen) | ca. 2–4 Wochen bis zur Bestandskontrolle |

**Hinweis:** *Phytoseiulus persimilis* ist ein spezialisierter Räuber der Gemeinen Spinnmilbe (two-spotted spider mite) und für Estragon bei Hitze-/Trockenheitsbefall (vegetative Phase) geeignet. Früh beim ersten Befallszeichen ausbringen (vor >4 Milben/Blatt) und frühestens 4 Wochen nach einem Breitband-Insektizid einsetzen. Koppert nennt 2–50 Stück/m² je Befallsdichte; Cornell/ARBICO ~10–32 Stück/m² (1–3+/sq ft) — die hier gewählte Spanne 10–30/m² liegt im belegten Konsens. Da *P. persimilis* sich rasch vermehrt und die Beute aufzehrt, sind Wiederholungseinführungen üblich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Kräuter / Asteraceae |
| Empfohlene Vorfrucht | beliebig |
| Anbaupause (Jahre) | Mehrjährig; Standort 3–4 Jahre; dann teilen und umpflanzen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Klassische Paarung; Aromasynergie; Schädlingsabwehr | `compatible_with` |
| Kopfsalat | Lactuca sativa | 0.8 | Estragon lockert Boden; Schutz vor Schnecken | `compatible_with` |
| Möhre | Daucus carota | 0.7 | Aromawirkung; Möhrenfliegen-Verwirrung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| — | — | Keine bekannten starken Unverträglichkeiten | — | — |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,harvest_months
Artemisia dracunculus,"Estragon;Bertram;Tarragon",Asteraceae,Artemisia,perennial,day_neutral,herb,rhizomatous,"5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Zentralasien, Sibirien",yes,8,20,100,50,45,limited,yes,false,false,light_feeder,false,half_hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Ellis Garten — Estragon](https://www.ellis-garten.de/estragon-steckbrief-pflege-verwendung-der-artemisia-dracunculus/) — Steckbrief, Verwendung
2. [Plantura — Estragon pflegen](https://www.plantura.garden/kraeuter/estragon/estragon-pflegen) — Pflege, Überwintern
3. [Gartenrat — Estragon](https://gartenrat.de/estragon/) — Anbau, Ernte
4. [Hausgarten — Estragon](https://www.hausgarten.net/kraeuter-und-gewuerze/kraeuter-gartenkraeuter/estragon-anbau-ernte-verwendung.html) — Kulturdaten
5. [Kiepenkerl — Estragon Kulturanleitung](https://www.kiepenkerl.de/kulturanleitungen/estragon/) — Aussaatdaten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Artemisia dracunculus (tarragon)](https://www.rhs.org.uk/plants/1632/artemisia-dracunculus/details) — Standort (full sun), gut durchlässiger Boden, pH-Vorzug
7. [PFAF — Artemisia dracunculus](https://pfaf.org/user/Plant.aspx?LatinName=Artemisia+dracunculus) — pH 6,5–7,8, Lichtansprüche, Trockenheitstoleranz, Lebensdauer
8. [USU Extension — French Tarragon in the Garden](https://extension.usu.edu/yardandgarden/research/french-tarragon-in-the-garden) — flachwurzelnd (shallow roots), Wurzel-/Kronenfäule bei Nässe
9. [The Old Farmer's Almanac — Tarragon](https://www.almanac.com/plant/tarragon) — pH 6,5–7,5, Standort, Pflege
10. [Fine Gardening — French Tarragon](https://www.finegardening.com/article/french-tarragon) — Kältebedarf/Dormanz (~2 Monate) zur Erhaltung der Produktivität
11. [ForwardPlant — Overwinter Artemisia dracunculus](https://www.forwardplant.com/care/overwinter/artemisia-dracunculus/) — Winterdormanz, Rückzug ins Rhizom
12. [ScienceDirect — Interaction of NaCl salinity and light intensity in Artemisia dracunculus L.](https://www.sciencedirect.com/science/article/abs/pii/S0305197823000443) — Salzempfindlichkeit (Höhe, Trockenmasse, Chlorophyll sinken unter NaCl)
13. [Zhen & Bugbee, ASHS JASHS 146(1) — Far-red Fraction Metric](https://journals.ashs.org/view/journals/jashs/146/1/article-p3.xml) — FR700-750/R600-700 ≈ 0,2 für direktes Sonnenlicht (offenes Tageslicht ≈ 0,5)
14. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate 2–50/m², Spinnmilben-Spezialist
15. [Cornell NYSIPM / ARBICO — Phytoseiulus persimilis](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate ~10–32/m² (1–3+/sq ft), Anwendungsstrategie
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
