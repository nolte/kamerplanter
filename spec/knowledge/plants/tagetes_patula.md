# Studentenblume — Tagetes patula

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** NABU Tagetes, Gartenjournal.net Tagetes, Compo Tagetes, Insektensaatgut.de Tagetes

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tagetes patula | `species.scientific_name` |
| Volksnamen (DE/EN) | Studentenblume, Aufrechte Tagetes, Französische Tagetes; French Marigold | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Tagetes | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; nach den Eisheiligen auspflanzen; stirbt bei ersten Frost | `species.hardiness_detail` |
| Heimat | Mexiko, Guatemala | `species.native_habitat` |
| Allelopathie-Score | 0.4 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 (Asteraceae-Forb; kein C4-/CAM-Syndrom belegt) | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 1.1 (Entwicklungs-/Blührate-Basistemperatur Tmin nach Blanchard & Runkle bzw. MSU-Modellierung; NICHT Keim-Basis) | `species.base_temp` |
| Lebensdauer (Jahre) | — (einjährig/annual; Feld nur für perennial relevant) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization) | false (tagneutral, kein Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurz-/Langtag-Schwellenwert; quantitative Kurztagsreaktion ohne echten kritischen Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Vorkultur März/April) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Blüten für Insekten; als Nematodenbekämpfung mind. 3 Monate stehen lassen) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, flowers | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | thiophene_derivatives, essential_oils (Thiophen-Derivate und aetherische Oele; ASPCA: Tagetes als toxisch fuer Hunde und Katzen gelistet) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (kutane Irritation, milde Gastroenteritis bei Verschlucken) | `species.toxicity.severity` |
| Kontaktallergen | true (ätherische Öle können bei Korbblütler-Allergie reagieren) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Korbblütler-Allergie) | `species.allergen_info.pollen_allergen` |

<!-- AB-015: Korrektur gemaess ASPCA Animal Poison Control -- Tagetes patula ist fuer Katzen und Hunde mild toxisch (Thiophen-Derivate, aetherische Oele). Symptome: Hautirritation, leichte Magen-Darm-Beschwerden. Fuer Menschen/Kinder unbedenklich (Blueten essbar). -->

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Deadheading fördert Nachblüte; nach 3 Monaten einarbeiten) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–35 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–25 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Erde; pH 5,5–7,0; gut drainiert | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> **Hinweis pH-Harmonisierung:** Die unter §1.7 belegte Spanne `soil_ph_preference` 6,0–7,5 (PFAF, UMN Extension, Missouri Botanical) liegt geringfügig höher als die ältere Topf-Substrat-Angabe 5,5–7,0 oben. Unterhalb pH 5,5 droht Mangan-/Eisen-Überschuss (Bronzefleckung der Blätter); der Optimumbereich ist pH 6,0–7,0.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt für Tagetes patula aus 2 unabhängigen seriösen Quellen belegt --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (mindestens 6 h direkte Sonne; in heißen Lagen etwas Nachmittagsschatten toleriert) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 (flachwurzelnde Beet-/Zwergform; Hauptdurchwurzelung in den oberen 15–30 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive (empfindlich gegen nasse Böden; Wurzelfäule bei Staunässe) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (Blüten-/Ertragsparameter reagieren empfindlicher als vegetative; Blattschäden ab Bewässerungs-EC 3,0 dS/m, deutliche Schäden bei 6,0 dS/m) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (Substrat-ECe) aus 2 unabhängigen Quellen; nur Bewässerungs-ECw-Effekte publiziert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6,0–7,5 (Optimum 6,0–7,0; verträgt mild sauer bis mild alkalisch) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–7 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 21–35 | 3 | false | false | high |
| Blüte (Dauerflorenz) | 90–120 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (quantitative Kurztagsreaktion: Kurztag beschleunigt Bluete, blueht aber auch bei Langtag) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 (kritischer Schwellenwert oberhalb des Ziel-Korridors; ~0.4 kPa über Oberkante 1.5) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium (mesophyte C3-Forb; kein Sukkulent/CAM) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 14–15 (instantanes Netto-Photosynthese-Optimum; ganztägige Wuchsleistung bei höheren Temperaturen bis ~30 °C, vgl. §2.2-Tagestemperatur) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland/Vollsonne, offenes Tageslicht; R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Tagetes braucht kaum Dünger. Auf mageren Böden blüht sie reicher. Auf überdüngten Böden bildet sie viel Laub und wenige Blüten. Die Nematoden-Bekämpfungswirkung entfaltet sich durch Wurzelausscheidungen (Thiophene) — diese werden durch mageren Boden und Stress gefördert. Für effektive Nematoden-Bekämpfung: Dicht pflanzen und mind. 8–12 Wochen stehen lassen; dann EINARBEITEN (nicht abräumen).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Moderat feucht; Blätter beim Gießen trocken halten | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (kein Dünger) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Vorkultur | Aussaat bei 20–22 °C im Haus | mittel |
| Mai (nach 15.) | Auspflanzen | Nach Eisheiligen; frostfrei | hoch |
| Jun–Sep | Deadheading | Verblühte Blüten entfernen; fördert Nachblüte | mittel |
| Jun–Aug | Nematoden-Einsatz | Für Nematoden-Bekämpfung dicht und flächig pflanzen | hoch |
| Aug–Sep | Einarbeitung | Als Gründüngung/Nematodenpflanze einarbeiten | mittel |
| Okt | Abräumen | Vor Frost abmähen; kompostieren | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste (bei Trockenheit) | leaf | flowering (Hitze) | medium |
| Blattläuse | div. Aphiidae | Kolonien (selten; Tagetes-Duft schützt) | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel | fungal (Botrytis cinerea) | Schimmel an Blüten | Feuchtigkeit, enge Bepflanzung | 3–7 | flowering |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit+Wärme | 5–10 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Nützling (beneficial) | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate / m² | Etablierungszeit |
|-----------------------|---------------------|----------------|-------------------|------------------|
| Raubmilbe (predatory mite) | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–50 je Ausbringung; bei erstem Befall, 1–2× wöchentlich wiederholen | 2–3 Wochen (Vermehrung ~2× schneller als Spinnmilbe; optimal 15–25 °C) |
| Schlupfwespe (parasitic wasp) | Aphidius colemani | Blattläuse (Aphididae) | 0,25–4 je Ausbringung; min. 3× wiederholen, vorbeugend wöchentlich | 2–3 Wochen bis Mumienbildung |
| Gallmücke (predatory midge) | Aphidoletes aphidimyza | Blattläuse (Aphididae, Befallsherde) | 2–5 (Puppen); alle 2–4 Wochen wiederholen | 1–2 Wochen bis Larvenschlupf |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Begleit- und Gründüngungspflanze |
| Empfohlene Vorfrucht | Nematoden-befallene Kulturen |
| Empfohlene Nachfrucht | Alle Hauptkulturen (Nematoden-Bekämpfung wirkt nach) |
| Anbaupause (Jahre) | keine |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Weiße Fliege-Abwehr; Bestäuber-Anlockung | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Nematoden-Abwehr; Bestäuber | `compatible_with` |
| Rose | Rosa spp. | 0.9 | Klassischer Begleiter; Schädlingsabwehr | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Nematoden-Abwehr | `compatible_with` |
| Kürbis | Cucurbita maxima | 0.8 | Nematoden-Schutz | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Bohne | Phaseolus vulgaris | Tagetes hemmt manche Bohnenarten | mild | `incompatible_with` |
| Kohl | Brassica oleracea | Schlechte Verträglichkeit | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tagetes patula |
|-----|-------------------|-------------|----------------------------------|
| Afrikanische Tagetes | Tagetes erecta | Gleiche Gattung | Größere Blüten; stärker durchwurzelnd gegen Nematoden |
| Ringelblume | Calendula officinalis | Bienenweide | Nicht in Asteraceae-Allergie-Fällen; andere Wirkung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,bloom_months
Tagetes patula,"Studentenblume;Aufrechte Tagetes;Französische Tagetes;French Marigold",Asteraceae,Tagetes,annual,day_neutral,herb,fibrous,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b",0.4,"Mexiko, Guatemala",yes,7,20,40,35,22,limited,yes,false,false,light_feeder,tender,"5;6","6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [NABU Tagetes](https://www.nabu.de/tiere-und-pflanzen/pflanzen/pflanzenportraets/zierpflanzen/04042.html) — Biologie, Nutzen
2. [Tagetes Nematoden — Gartenjournal.net](https://www.gartenjournal.net/tagetes-nematoden) — Nematoden-Bekämpfung
3. [Compo Tagetes](https://www.compo.de/ratgeber/pflanzen/gartenpflanzen/tagetes) — Pflege, Aussaat
4. [Kraut&Rüben Tagetes](https://www.krautundrueben.de/studentenblumen-tagetes-schuetzt-gemuese-vor-schaedlingen-201) — Mischkultur-Praxis
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [PFAF — Tagetes patula](https://pfaf.org/user/Plant.aspx?LatinName=Tagetes+patula) — Bodenansprüche (mild sauer/neutral/mild alkalisch), Lichtbedarf (Vollsonne, kein Schatten), Feuchte
6. [Missouri Botanical Garden — Tagetes patula](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a611) — Vollsonne, mittlerer Wasserbedarf, frostempfindlicher Annual, Blühzeit
7. [UMN Extension — Marigolds](https://extension.umn.edu/flowers/marigolds) — Boden-pH 6–7, Mangan-/Eisen-Überschuss unter pH 5,5
8. [Blanchard & Runkle — Quantifying the thermal flowering rates of 18 species of annual bedding plants (Scientia Horticulturae 2011)](https://www.sciencedirect.com/science/article/abs/pii/S0304423810005467) — Entwicklungs-Basistemperatur Tmin = 1,1 °C für Tagetes patula
9. [Moccaldi & Runkle — Modeling Temperature & DLI on Growth and Flowering of Salvia and Tagetes patula (JASHS 132(3) 2007)](https://journals.ashs.org/jashs/view/journals/jashs/132/3/article-p283.xml) — Temperatur-/DLI-Modell, Blührate, Basistemperatur-Bestätigung
10. [van Iersel — Temperature Effects on Photosynthesis, Growth & Maintenance Respiration of Marigold (ISHS Acta Hort.)](https://www.ishs.org/ishs-article/624_76) — Netto-Photosynthese-Optimum 14–15 °C, höhere Wuchsleistung bei ~30 °C
11. [Responses of Marigold Cultivars to Saline Water Irrigation (HortTechnology 2018 / USDA-ARS)](https://www.ars.usda.gov/ARSUserFiles/50820500/GPRG/2018PublicationsandSummaries/2018_Responses%20of%20Marigold%20Cultivars%20to%20Saline%20Water%20Irrigation.pdf) — Salzempfindlichkeit, Blattschäden ab ECw 3,0–6,0 dS/m
12. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Spinnmilben-Raubmilbe (2–50/m²), Anwendung
13. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) / [UConn IPM — Biological Control of Aphids](https://ipm.cahnr.uconn.edu/ipm-biological-control-of-aphids/) — Blattlaus-Nützlinge, Ausbringraten Aphidius/Aphidoletes
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
