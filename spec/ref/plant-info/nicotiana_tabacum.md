# Tabak — Nicotiana tabacum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, University of Kentucky College of Agriculture Tobacco Production, FAO Tobacco Crop Profile, North Carolina State University Extension, Royal Horticultural Society

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Nicotiana tabacum | `species.scientific_name` |
| Volksnamen (DE/EN) | Tabak, Virginischer Tabak; Common Tobacco, Virginia Tobacco | `species.common_names` |
| Familie | Solanaceae | `species.family` → `botanical_families.name` |
| Gattung | Nicotiana | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b (als Jahrespflanze in 5a–11b kultivierbar) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frost-empfindlich; stirbt bei Frost ab; in Mitteleuropa als einjährige Sommerkultur; Vorkultur im Warmhaus ab März–April; Auspflanzung nach letztem Frost | `species.hardiness_detail` |
| Heimat | Südamerika (Bolivien, Argentinien, Andenregion) | `species.native_habitat` |
| Allelopathie-Score | -0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Allelopathie-Hinweis:** Tabak-Wurzelsekrete (Solanesol, Chlorogensäure) hemmen benachbarte Pflanzen. Außerdem akkumuliert Nicotiana tabacum Tabak-Mosaik-Virus (TMV) — gefährlicher Vektori für benachbarte Solanaceen (Tomate, Paprika, Aubergine). Nicht neben Solanaceen pflanzen!

**Rechtlicher Hinweis:** Anbau von Tabak für den Eigenbedarf ist in Deutschland erlaubt, jedoch steuerlich komplex (Tabaksteuer). Gewerblicher Anbau bedarf einer Genehmigung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 (Tabakanzucht dauert lange; sehr kleines Saatgut) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14–21 (nur Gewächshaus; zu feines Saatgut für Freiland-Direktsaat) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Vorkultur im Warmhaus) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (Blattern von unten nach oben) | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (Rispenpflanze; gekappt = Sucker-Triebe; Geiz entfernen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Saatgut-Hinweis:** Tabaksamen sind extrem klein (10.000–20.000 Samen/g). Nicht eingraben — Samen benötigen Licht zur Keimung (Lichtkeimer). Auf feuchtes Substrat streuen; Folie oder Glas drüber; 25–30°C.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | ALLE Teile (besonders frische Blätter; Grüner Tabak-Vergiftung bei Verarbeitern) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Nikotin (0,5–8% in Blättern; stark giftig; LD50 40–60 mg für Erwachsene); Anabasin, Nornicotikin (weitere Alkaloide) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Grüner-Tabak-Krankheit = Green Tobacco Sickness; Nikotinaufnahme durch Haut bei feuchten Blättern) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**KRITISCHE SICHERHEITSWARNUNG:** Nikotin ist eines der giftigsten Alkaloide bekannt. Bei der Verarbeitung von Tabakblättern IMMER wasserdichte Handschuhe tragen — Nikotin wird über feuchte Haut resorbiert. Grüner-Tabak-Krankheit (Übelkeit, Erbrechen, Tachykardie) ist bei Tabakerntearbeitern bekannt. Pflanze außerhalb der Reichweite von Kindern und Tieren halten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Topping = Rispenkappung; Geizen = Sucker entfernen) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (Topping wenn 50–75% der gewünschten Blätter entwickelt) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 (große, tiefe Töpfe für volle Blatentwicklung) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–250 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–80 × 90–100 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (Gewächshaus; sehr lichtbedürftig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (windgeschützt; sonnig) | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, nährstoffreiche Erde; pH 5,8–6,5; leicht sauer; durchlässig; Substrat wie für Tomaten | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–21 | 1 | false | false | low |
| Sämling | 28–42 | 2 | false | false | low |
| Vegetativ / Rosette | 21–42 | 3 | false | false | medium |
| Streckungsphase | 21–35 | 4 | false | false | medium |
| Blüte / Topping | 14–21 | 5 | false | true | medium |
| Blatternte | 35–60 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 (Lichtkeimer; Licht nötig!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75–90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2 (feucht halten; nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 24–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–1000 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ / Streckung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 26–34 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 800–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blatterntefase

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 30–45 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 26–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 800–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | K-Betonung |
|-------|----------------|---------|-----|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 5.8–6.2 | — | — | — |
| Sämling | 2:1:2 | 0.6–1.0 | 5.8–6.2 | 60 | 25 | mittel |
| Vegetativ | 3:1:3 | 1.2–1.8 | 5.8–6.5 | 120 | 50 | hoch |
| Streckung | 2:1:4 | 1.4–2.2 | 5.8–6.5 | 150 | 60 | sehr hoch |
| Blatternte | 1:1:3 | 1.0–1.6 | 5.8–6.5 | 100 | 50 | hoch |

**Besonderheit:** Tabak hat einen extrem hohen Kalium-Bedarf — Kalium beeinflusst Verbrennungseigenschaften und Blattqualität. Chlorid-freies Kalium (K₂SO₄) verwenden, da Chlorid die Blattqualität mindert.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Sämling | time_based | 10–21 Tage; 2 Keimblätter entwickelt |
| Sämling → Vegetativ | time_based | 28–42 Tage; 5–6 echte Blätter; Pikierung |
| Vegetativ → Streckung | time_based | 21–42 Tage; Pflanzung ins Freiland; Streckung setzt ein |
| Streckung → Blatternte | event_based | Topping (Rispenentfernung); Seitenaustriebe kappen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Gewächshaus)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15–0.25 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.15–0.20 | 4 | vegetativ |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10–0.15 | 4 | streckung, ernte |
| CalMag | diverse | supplement | 2-0-0 | 0.15–0.20 | 2 | alle |
| Kaliumsulfat K2SO4 | diverse | supplement | 0-0-50 | 0.10–0.15 | 5 | streckung |

#### Organisch / Freiland

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 4–6 L/m² | Vor Pflanzung |
| Hornmehl | diverse | organisch | 60–100 g/m² | Vor Pflanzung |
| Kaliumsulfat (granuliert) | diverse | mineralisch | 20–30 g/m² | Grunddüngung + Streckung |
| Leachate / Wurmtee | diverse | organisch | 1:10 verdünnt | 2× wöchentlich |

### 3.2 Mischungsreihenfolge

1. Silikat-Zusätze (falls verwendet)
2. CalMag
3. Flora Micro / Base A
4. Flora Gro oder Flora Bloom (je Phase)
5. Kaliumsulfat (separat auflösen)
6. pH-Korrektur (IMMER zuletzt)

### 3.3 Besondere Hinweise zur Düngung

Hoher Kalium-Bedarf — KEIN Kaliumchlorid (KCl) verwenden (Chlorid verschlechtert Verbrennungseigenschaften). Calcium essentiell für Blattqualität. Übermäßige N-Düngung ergibt rohen, scharfen Tabak mit schlechten Brenneigenschaften — N in der Abreife reduzieren.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser bevorzugt (EC <0.3 mS); pH 5,8–6,5 | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7–14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Saatgutaussaat | Sehr feines Saatgut auf feuchtes Substrat streuen; 25–30°C; Lichtkeimer | hoch |
| Apr | Pikierung | Sämlinge pikieren wenn 3–4 cm groß; einzeln in 6-cm-Töpfe | hoch |
| Mai–Jun | Abhärtung / Auspflanzung | Langsam abhärten; nach letztem Frost auspflanzen | hoch |
| Jul | Topping | Rispe kappen wenn 50–75% der Blätter erwünscht; sofort Geizen (Sucker entfernen) | hoch |
| Jul–Aug | Blatternten | Unterste reife Blätter (gelb-grün) zuerst ernten; ca. 2–3 Blätter/Woche | hoch |
| Aug–Sep | Letzte Ernte | Obere Blätter noch unreifer; trocknen separat | mittel |
| Sep–Okt | Trocknung | Blätter aufhängen; 30–40°C; 4–8 Wochen | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Tabakblattlaus | Myzus persicae | Kolonien; virusübertrager; Vergilbung | Blatt, Trieb | Sämling, Vegetativ |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; Gelbflecken; Austrocknung | Blatt | Streckung, Ernte |
| Minierfliege | Liriomyza trifolii | Minen/Gänge in Blättern | Blatt | Vegetativ |
| Tabakraupen | Manduca sexta, M. quinquemaculata | Großer Fraß; Kotklumpen | Blatt | Blüte, Ernte |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau; Rußtau | Blatt | Alle (Gewächshaus) |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Tabak-Mosaik-Virus (TMV) | viral | Mosaikflecken; Blasen; Wuchshemmung | mechanische Übertragung |
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißgrauer Belag | trocken-warm |
| Blauer Schimmel | fungal (Peronospora tabacina) | Gelbliche Flecken oben; blauer Belag unten | kühl-feucht |
| Braunfleckigkeit | fungal (Alternaria alternata) | Braune Flecken; Blattfall | alt/geschwächt; feucht |
| Schwarzbeinigkeit | fungal (Pythium, Rhizoctonia) | Halsnekrose; Keimlingsfäule | übermäßige Nässe |

**WICHTIG — TMV:** Tabak-Mosaik-Virus überlebt in Tabakprodukten (Zigaretten!). Nie Tabak verarbeitende Personen sollten ohne Handwaschen Tabakpflanzen anfassen. TMV kann auf Tomaten, Paprika, Auberginen übertragen werden.

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5–10 | 14–21 |
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Aphidius colemani | Blattläuse | 3–5 | 14 |
| Steinernema carpocapsae | Tabakraupen (Boden) | 50 Nematoden/m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Spinnmilben |
| Pyrethrin | biological | Pyrethrine | Sprühen | 3 | Blattläuse, Weiße Fliege |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen | 14 | Mehltau, Blauer Schimmel |
| Spinosad | biological | Spinosad | Sprühen | 3 | Tabakraupen |
| Kupferfungizid | biological/chemical | Kupferhydroxid | Sprühen | 7 | Blauer Schimmel |
| Bacillus thuringiensis | biological | Bt var. kurstaki | Sprühen | 0 | Tabakraupen |
| Befallenes Material entfernen | cultural | — | Sofortentfernung | 0 | TMV, Viruskrankheiten |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Wildtyp-TMV Resistenz (sortenabhängig; N-Gen) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Solanaceen (Solanaceae) |
| Empfohlene Vorfrucht | Getreide, Gräser, Hülsenfrüchte |
| Empfohlene Nachfrucht | Getreide; KEINE Solanaceen (TMV-Risiko); KEIN Kohl |
| Anbaupause (Jahre) | 4 Jahre vor erneuten Solanaceen (TMV, Nematoden) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Fangpflanze; schützt Tabak | `compatible_with` |
| Tagetes | Tagetes erecta / patula | 0.7 | Nematoden-Abwehr; Bestäuber | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.6 | Thrips-Abwehr (anekdotisch) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | TMV-Vektorrisiko; gleiche Krankheiten | severe | `incompatible_with` |
| Paprika | Capsicum annuum | TMV-Vektorrisiko; gleiche Familie | severe | `incompatible_with` |
| Aubergine | Solanum melongena | Gleiche Familie; gleiche Schädlinge/Krankheiten | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gleiche Familie; Nematoden; TMV | severe | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Solanaceae | `shares_pest_risk` | TMV, Blattläuse (Myzus persicae), Spinnmilben | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tabak |
|-----|-------------------|-------------|------------------------|
| Bauern-Tabak | Nicotiana rustica | Gleiche Gattung | Höherer Nikotingehalt; robuster |
| Ziertabak | Nicotiana alata / sylvestris | Gleiche Gattung | Keine Nikotinproduktion; Zierpflanze |
| Ziertabak | Nicotiana x sanderae | Gattung | Farbenfrohe Hybriden; Zierwert |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Nicotiana tabacum,"Tabak;Virginischer Tabak;Common Tobacco;Virginia Tobacco",Solanaceae,Nicotiana,annual,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b",-0.3,"Südamerika",limited,limited,limited,true,false,heavy_feeder,false,tender,"3;4","7;8;9","7;8;9"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Virginia Gold,Nicotiana tabacum,"virginia_flue_cured;golden_leaf;high_sugar",100,open_pollinated
Burley KY14,Nicotiana tabacum,"burley_type;air_cured;high_nicotine",110,open_pollinated
Oriental Izmir,Nicotiana tabacum,"oriental_type;aromatic;small_leaf;sun_cured",120,open_pollinated
```

---

## Quellenverzeichnis

1. [University of Kentucky — Tobacco Production Guide](https://tobacco.ca.uky.edu) — Anbaupraxis, Düngung
2. [USDA PLANTS — Nicotiana tabacum](https://plants.usda.gov/plant-profile/NITA2) — Taxonomie
3. [FAO Tobacco Crop Profile](https://www.fao.org/tobacco) — Globale Anbausysteme
4. [North Carolina State University Extension — Tobacco IPM](https://entomology.ces.ncsu.edu) — IPM, Schädlinge
5. [RHS — Growing Tobacco as a Garden Plant](https://www.rhs.org.uk) — Gartenkultur
