# Grünkohl — Brassica oleracea var. sabellica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Grünkohl, Bio-Gärtner.de, Naturadb.de, LWK Niedersachsen

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. sabellica | `species.scientific_name` |
| Volksnamen (DE/EN) | Grünkohl, Braunkohl, Krauskohl; Kale, Curly Kale | `species.common_names` |
| Familie | Brassicaceae | `species.family` → `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | biennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (kein echter Kurz-/Langtagblüher; Blüte im 2. Jahr vernalisationsgesteuert, nicht über Tageslänge — Korpus-Konvention für vernalisationsgesteuerte Arten) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4–5 (kühlliebender Brassica/cole crop; Hauptwuchsphase) | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization) | true | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | 28–70 (4–10 Wochen Kältereiz bei 2–10 °C; primärer Blühauslöser, Langtag wirkt nur sekundär fördernd) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | — (kein echter Kurz-/Langtagblüher; Blüte vernalisationsgesteuert) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 2a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −15 °C; Frost verbessert das Aroma (Stärke → Zucker-Umwandlung); typische Norddeutschland-Pflanze | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Westeuropa (Atlantikküste) | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkultur April–Mai) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6, 7 | `species.direct_sow_months` |
| Erntemonate | 11, 12, 1, 2, 3 (nach dem ersten Frost am besten) | `species.harvest_months` |
| Blütemonate | 4, 5 (zweites Jahr) | `species.bloom_months` |

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
| Giftige Inhaltsstoffe | Goitrogene (bei übermäßigem Verzehr) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Blätter von unten nach oben ernten) | `species.pruning_type` |
| Rückschnitt-Monate | 11, 12, 1, 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (min. 30 L Kübel) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (bei hohen Sorten Stab empfohlen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche Erde, pH 6,5–7,5; regelmäßig düngen | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 40 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | 1.8 (Maas-Hoffman a; belegt für Brassica oleracea/Kopfkohl, gattungsgleicher Proxy) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 9.7 (Maas-Hoffman b; Brassica oleracea/Kopfkohl) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.5 | `species.soil_ph_preference` |

> **Hinweis Lichtkompensationspunkt:** Für var. sabellica wurde ein LCP von ~39 µmol/m²/s gemessen; C3-Blattgemüse liegen typisch bei 30–40 µmol/m²/s. Lichtsättigung liegt deutlich höher (mehrere hundert µmol/m²/s) und gehört nicht in das LCP-Feld.
> **Hinweis pH:** Toleranzspanne 6,0–7,5; gärtnerische Praxis-Untergrenze liegt bei pH 6,5 (Clubwurzel-/Kohlhernie-Prävention, Calciumverfügbarkeit), konsistent mit §1.6, §2.3 und der Kalkung in §3.2.
> **Hinweis Salztoleranz:** Bezugsgröße ist die Substrat-Sättigungsextrakt-Leitfähigkeit (ECe), nicht der Gießwasser-EC. Grünkohl selbst hat keinen publizierten eigenen Maas-Hoffman-Wert; übernommen vom gattungsgleichen Brassica oleracea (Kopfkohl, Rating MS).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | medium |
| Sämling | 21–42 | 2 | false | false | medium |
| Vegetativ (Rosette) | 60–90 | 3 | false | false | high |
| Ernte-/Winterphase | 90–150 | 4 | false | true | high |
| Blüte (2. Jahr) | 30–60 | 5 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ & Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 0–10 (Frost verbessert Aroma!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (stomatärer Kollaps deutlich oberhalb des Zielkorridors; kühl-/feuchteliebend) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–23 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht, Vollsonnen-Freilandkultur ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 (im Winter weniger) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 2:1:1 | 0.8–1.2 | 6.5–7.0 | 80 | 40 | — | 2 |
| Vegetativ | 3:1:2 | 1.5–2.0 | 6.5–7.5 | 150 | 60 | 20 | 3 |
| Ernte | 1:1:2 | 1.0–1.5 | 6.5–7.5 | 100 | 50 | — | 2 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase** (Ziel-Gewebegehalte/Versorgungsbereiche, Blattgewebe; Brassica/cole-crop-Versorgungsbereiche):

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) | KA-Feld |
|-------|----------|----------|----------|----------|---------|
| Sämling | 30–60 | 25–50 | 5–10 | 0.5–1 | `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` |
| Vegetativ | 30–200 | 30–100 | 8–20 | 0.8–5 | `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` |
| Ernte | 30–150 | 25–80 | 8–15 | 0.8–5 | `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` |

> **Hinweis:** Versorgungsbereiche (sufficiency ranges) aus Extension-Blattgewebe-Richtwerten für Brassica/Kohlgemüse (Mn 30–200, Zn 30–100, Cu 8–20, Mo 0,8–5 ppm; <20 ppm Mn/Zn bzw. <6 ppm Cu = Mangel). Mo ist für Brassicaceen besonders wichtig (Nitratreduktase); Mn-Überschuss >300 ppm ist toxisch.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | Oscorna | organisch-N | 80–120 g/m² | Pflanzung und Nachschub |
| Kompost | eigen | organisch | 5–8 L/m² | Frühjahr/vor Pflanzung |
| Brennnesseljauche | selbst | organisch-N | 1:10 verdünnt | Alle 3 Wochen Juli–Sep |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kohlgemüse-Dünger | Compo | base | 14-7-17 | 60–80 g/m² | Wachstumsphase |
| Kieserit | diverse | supplement | 0-0-0+27MgO | 30 g/m² | Magnesiummangel |

### 3.2 Besondere Hinweise zur Düngung

Grünkohl ist Starkzehrer mit hohem Stickstoff- und Calciumbedarf. Kalkung wichtig (pH >6,5) für Calciumverfügbarkeit und Clubwurzel-Prävention. Keine Düngung nach September — Frost-Aroma durch natürliche Zuckerspeicherung darf nicht durch überschüssigen N gestört werden. Schwefel unterstützt die Glucosinolat-Bildung (Abwehrstoffe).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Regelmäßige Feuchtigkeit; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Vorkultur | Aussaat in Anzuchttöpfe bei 15–20 °C | mittel |
| Jun–Jul | Auspflanzen | Jungpflanzen 50 cm Abstand setzen | hoch |
| Jul–Aug | Düngen | 2× Hornspäne + Kompost einarbeiten | hoch |
| Sep | Letzter Dünger | Kein Stickstoff mehr ab September | hoch |
| Nov | Erste Ernte | Nach erstem Frost die unteren Blätter ernten | mittel |
| Dez–Feb | Winterernte | Regelmäßig ernten; Frost verbessert Geschmack | hoch |
| Apr (2. Jahr) | Blüte / Entfernen | Plant läuft in Blüte; für Saatgut stehen lassen oder entfernen | niedrig |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 (ab konstant < 0 °C; 7–15 cm Stroh/Laub-Mulch um den Wurzelbereich) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | uncover | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | bleibt im Freiland; winterhart bis ca. −15 °C, robuste Sorten bis −20 °C | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | volles Tageslicht (Freiland) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam; nur frostfreie Tage, Staunässe vermeiden | `overwintering_profiles.winter_quarter_watering` |

> **Hinweis:** Grünkohl überwintert im Freiland (kein Einräumen). Blätter sind frosthart; die Wurzeln sind kälteempfindlicher und profitieren bei strengem Dauerfrost von Mulch oder zusätzlich einem Vlies (fleece). Frost wandelt Stärke in Zucker um und verbessert das Aroma — Ernte über den Winter ist erwünscht.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweißling | Pieris brassicae | Kahlfraß, grüne Raupen | leaf | vegetative | easy |
| Kohldrehherzgallmücke | Contarinia nasturtii | Deformation der Herzblätter | leaf, stem | seedling | difficult |
| Blattläuse (Mehlige Kohlblattlaus) | Brevicoryne brassicae | Weißlich-grauer Belag, Kolonien | leaf | vegetative | easy |
| Erdfloh | Phyllotreta spp. | Kleine Löcher in Blättern | leaf | seedling | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Clubwurzel (Kohlhernie) | protist (Plasmodiophora brassicae) | Knollenartige Wurzelwucherungen, Welke | saure Böden pH<6.5, feuchte Bedingungen | 14–21 | all |
| Falscher Mehltau | oomycete (Hyaloperonospora parasitica) | Gelbe Flecken oben, weißer Belag unten | Feuchtigkeit | 5–10 | seedling, vegetative |
| Alternaria-Blattflecken | fungal | Braune Flecken mit Gelbhof | Feuchtigkeit, Wärme | 7–14 | vegetative |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Trichogramma evanescens | Kohlweißling-Eier | 50 Schlupfwespen/m² | 7–14 |
| Marienkäfer | Kohlblattlaus | 5–10 | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Feinmaschig von Pflanzung bis Herbst | 0 | Kohlweißling, Erdfloh |
| Bt-Präparat (Dipel) | biological | Bacillus thuringiensis | Sprühen, 0.5–1% | 0 | Kohlweißling-Raupen |
| Kalkung | cultural | Branntkalk/Algenkalk | 100–200 g/m² | 0 | Clubwurzel (pH anheben) |
| Fruchtfolge | cultural | — | 4 Jahre keine Brassicaceen | 0 | Clubwurzel, Nematoden |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kreuzblütengewächse (Brassicaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte, Erbsen (N-Fixierer) |
| Empfohlene Nachfrucht | Möhren, Zwiebeln, Salat (Schwachzehrer) |
| Anbaupause (Jahre) | 3–4 Jahre keine Brassicaceen (Clubwurzel-Dauersporen!) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Zwiebeln | Allium cepa | 0.8 | Zwiebel-Duft hält Kohlschädlinge fern | `compatible_with` |
| Sellerie | Apium graveolens | 0.8 | Erdfloh-Abwehr | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Nützlingsförderung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Knoblauch | Allium sativum | Wachstumshemmung (mäßig) | mild | `incompatible_with` |
| Erdbeere | Fragaria × ananassa | Schlechte Verträglichkeit | mild | `incompatible_with` |
| Alle Brassicaceen | Brassica spp. | Gleiche Schädlinge, Clubwurzel | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Grünkohl |
|-----|-------------------|-------------|---------------------------|
| Schwarzkohl (Cavolo nero) | Brassica oleracea var. palmifolia | Sehr ähnlich | Feineres Aroma, dekorativer |
| Mangold | Beta vulgaris subsp. vulgaris | Winterhartes Blattgemüse | Kein Clubwurzel-Risiko; andere Familie |
| Federkohl (Baby Kale) | Brassica oleracea var. sabellica | Identisch | Junge Blätter als Salat ernten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Brassica oleracea var. sabellica,"Grünkohl;Braunkohl;Krauskohl;Kale;Curly Kale",Brassicaceae,Brassica,biennial,day_neutral,herb,fibrous,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",-0.1,"Mittelmeerraum, Westeuropa",limited,40,30,120,80,55,no,limited,false,false,heavy_feeder,hardy,"5;6;7","11;12;1;2;3"
```

---

## Quellenverzeichnis

1. [Plantura Grünkohl](https://www.plantura.garden/gemuese/gruenkohl) — Anbau, Erntezeit, Pflege
2. [LWK Niedersachsen](https://www.lwk-niedersachsen.de/) — Regionaler Anbau
3. [NaturaDB Brassica oleracea](https://www.naturadb.de/pflanzen/brassica-oleracea/) — Botanische Daten
4. [Heimbiotop.de Kohl-Überblick](https://www.heimbiotop.de/brassica.html) — Kohlarten-Systematik
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Seed Savers — Cabbage, Broccoli, Kale and friends (Brassica oleracea)](https://www.seedsavers.org.au/2025/09/21/brassica-oleracea/) — Biennialität, Vernalisationsbedarf (Kältereiz zur Blühinduktion)
6. [Non-vernalization requirement in Chinese kale (BoFLC), PMC8866342](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8866342/) — Vernalisations-/FLC-Pathway bei B. oleracea, Photoperiode als sekundärer Auslöser
7. [OSU Extension EM 9305 — Vegetable degree-day models](https://extension.oregonstate.edu/catalog/em-9305-vegetable-degree-day-models-introduction-farmers-gardeners) — GDD-Basistemperatur cole crops (≈3–5 °C)
8. [GrowVeg — Vegetable Root Depths](https://www.growveg.com/guides/vegetable-root-depths-revealed-use-this-guide-to-make-smarter-planting-decisions/) — effektive Wurzeltiefe Kale (flach wurzelnd, 30–45 cm)
9. [FAO — Crop salt tolerance data (Annex 1)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Maas-Hoffman ECe-Schwelle 1,8 dS/m / Slope 9,7 %, Rating MS (Brassica oleracea/Kopfkohl)
10. [USDA-ARS — Tolerance of vegetable crops to salinity (Shannon & Grieve)](https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P1567.pdf) — Salztoleranz-Einstufung Brassica oleracea (moderately sensitive)
11. [Old Farmer's Almanac — Kale](https://www.almanac.com/plant/kale) — Boden-pH 6,0–7,5, Vollsonne, Staunässe-Empfindlichkeit
12. [Low intensity light treatment improves purple kale (var. sabellica) postharvest, PMC6819828](https://pmc.ncbi.nlm.nih.gov/articles/PMC6819828/) — Lichtkompensationspunkt var. sabellica ≈ 39 µmol/m²/s
13. [MDPI Plants 2020, 9(8), 960 — Photosynthesis in Chinese kale under varying light](https://www.mdpi.com/2223-7747/9/8/960) — C3-Photosynthese, LCP/Lichtsättigung B. oleracea
14. [MSU Extension E486 — Secondary and Micro-nutrients for Vegetable Crops](https://www.canr.msu.edu/resources/secondary_and_micro_nutrients_for_vegetable_and_field_crops_e486) — Blattgewebe-Versorgungsbereiche Mn/Zn/Cu/Mo
15. [PMC8306225 — Temperature/RH/CO₂ effects on kale growth & glucosinolates](https://pmc.ncbi.nlm.nih.gov/articles/PMC8306225/) — Photosynthese-Optimaltemperatur Grünkohl 20–23 °C
16. [ASHS JASHS 146(1) — Far-red Fraction metric (Kusuma & Bugbee)](https://journals.ashs.org/view/journals/jashs/146/1/article-p3.xml) — Far-Red-Fraction Tageslicht ≈ 0,33
17. [Savvy Gardening — Growing Kale in Winter](https://savvygardening.com/growing-kale-in-winter/) — Freiland-Überwinterung, Mulch/Vlies, Winterhärte −15 °C
18. [RusticWise — Growing Kale in Winter](https://rusticwise.com/growing-kale-in-winter/) — Überwinterung, Wurzelschutz, Winterernte
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
