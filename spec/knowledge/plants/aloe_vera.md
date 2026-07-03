# Aloe vera — Aloe vera

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Old Farmer's Almanac](https://www.almanac.com/plant/aloe-vera), [South Dakota State University Extension](https://extension.sdstate.edu/aloe-vera-houseplant-how), [Bloomscape](https://bloomscape.com/plant-care-guide/aloe/), [ASPCA](https://www.aspca.org/), [Soltech](https://soltech.com/products/aloe-plant-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aloe vera | `species.scientific_name` |
| Volksnamen (DE/EN) | Echte Aloe, Aloe vera; Aloe Vera, True Aloe, Barbados Aloe | `species.common_names` |
| Familie | Asphodelaceae | `species.family` → `botanical_families.name` |
| Gattung | Aloe | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 5–25+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | Nicht zutreffend (tagneutral / day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 4°C (Kälteschäden unter 4°C, Erfrierung unter 0°C), optimal 15–29°C. | `species.hardiness_detail` |
| Heimat | Arabische Halbinsel (Jemen, Oman); weltweite Naturalisierung in trockenen Tropen/Subtropen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, medicinal | `species.traits` |

**Medizinische Hinweise:** Aloe-vera-Gel (inneres klares Gel) hat nachgewiesene Wirksamkeit bei Verbrennungen 1. und 2. Grades (Cochrane Review). Das äußere Blattgewebe (Latex/Alooin) ist dagegen oral giftig. Viele Fertigprodukte im Handel verwenden Gel nach industrieller Verarbeitung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt (Ableger-Vermehrung standard) | `species.direct_sow_months` |
| Erntemonate | Ganzjährig (Blätter nach Bedarf) | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (selten Indoor, nur bei sehr hellen Standorten; vereinzelt bereits ab Februar oder bis Juni) <!-- Quelle: growing-phase-auditor 2026-07 --> | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Primäre Methode ist die Ableger-Vermehrung: Kindpflanzen (Pups) an der Mutterpflanzenbasis bei 5–10 cm Höhe ablösen, 1–2 Tage Schnittstelle trocknen lassen, dann in trockenes Kakteensubstrat pflanzen. Samenvermehrung möglich aber langsam.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true (Blattlatex — Gel ist sicher, Latex nicht!) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves (nur Latex/Alooin im äußeren Blattgewebe; inneres Gel unbedenklich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | anthraquinones (alooin, aloe-emodin) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Latex kann Kontaktdermatitis auslösen bei empfindlichen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken (Latex):** Starke Diarrhö, Krämpfe, Elektrolytentgleisungen. Bei Tieren: Erbrechen, Durchfall, Lethargie. Das transparente innere Gel ist nicht giftig.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Äußere, abgestorbene oder beschädigte Blätter an der Basis entfernen. Blütenstand nach der Blüte abschneiden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt in DE | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer, windgeschützt, volle Sonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde oder Einheitserde mit 50% Perlite/Grobsand. Sehr durchlässig — kein Staunasser Topf. Terrakotta-Töpfe ideal für bessere Austrocknung. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (kein art-spezifischer Wert in seriöser Literatur belegbar; CAM-Pflanze mit atypischer Tag/Nacht-Gaswechsel-Dynamik) | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 20–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, dS/m) | <!-- DATEN FEHLEN --> (toleriert bis ~4 dS/m Bewässerungssalinität in Feldstudien, aber kein publizierter Maas-Hoffman-Schwellenwert) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–8.5 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | true | very high |
| Winterruhe (Wachstumsstillstand) | 120–150 | 2 | false | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–40 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–40 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | <!-- DATEN FEHLEN --> (kein publizierter art-spezifischer Schwellwert; CAM-Sukkulente mit nächtlicher Stomataöffnung, daher untypische VPD-Kopplung) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 21–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–35 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 20–35 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–3.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | <!-- DATEN FEHLEN --> (kein publizierter art-spezifischer Schwellwert) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 (P/K-betont für Sukkulenten) | 0.4–0.8 | 6.0–7.0 | 40 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
#### Mikronährstoffe je Phase

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Aktives Wachstum | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | — | — | — | — |

> Hinweis: Keine art-spezifischen Mikronährstoff-Zielwerte (Mn/Zn/Cu/Mo) für Aloe vera in seriöser Fachliteratur belegbar. Als extremer Schwachzehrer deckt Aloe vera ihren Mikronährstoffbedarf in der Regel über handelsüblichen Kakteen-/Sukkulentendünger (siehe 3.1), der diese Elemente in Spuren enthält. Werte daher als `DATEN FEHLEN` markiert statt geraten.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen & Sukkulenten Dünger | Compo | base | 4-6-7 | 3 ml/L (alle 8 Wochen) | Wachstum |
| Kakteen Dünger | Substral | base | 3-6-7 | 3 ml/L (alle 8 Wochen) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Aloe vera ist ein extremer Schwachzehrer. Nur 2–3 Düngergaben pro Wachstumssaison. Überdüngung führt zu schnellem, aber weichem, wenig wirkstoffreichem Blattwachstum. Niemals im Winter düngen. Für medizinische Nutzung des Gels minimale Düngung bevorzugen (natürlicherer Wuchs).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; Staunässe ist die häufigste Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Sommer vorbereiten | Standort mit vollem Sonnenlicht wählen oder Balkon | mittel |
| Apr | Gießen reaktivieren | Erste Wassergabe; Substrat auf Austrocknung prüfen | mittel |
| Apr–Jun | Ableger trennen | Kindpflanzen bei 5–10 cm Höhe ablösen | optional |
| Mai–Sep | Balkon möglich | Volle Sonne, windgeschützt; vor Starkregen schützen | optional |
| Sep | Einräumen | Vor ersten Nachtfrösten hereinholen | hoch |
| Okt–Mär | Winterruhe | Sehr wenig gießen, kein Dünger | hoch |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free (frostempfindliche Sukkulente — muss frostfrei drinnen überwintern; UI-Winterhärte-Ampel = rot) | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion | Einräumen ins Haus (frostfreier, heller Standort) | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | 9 (September, vor erstem Nachtfrost; spätestens Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion | Schrittweise nach draußen abhärten, Gießen reaktivieren | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–18 (Minimum 5 °C, ideal 13–20 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (Süd-/Ostfenster); je heller, desto besser | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | stark reduziert, ca. alle 4–6 Wochen (Gießintervall verdoppeln ggü. Sommer) | `overwintering_profiles.winter_quarter_watering` |

> Hinweis (Mitteleuropa, USDA 6–8): Aloe vera ist nicht frosthart und muss in Mitteleuropa ganzjährig als Kübel-/Zimmerpflanze gehalten und vor dem ersten Nachtfrost (meist September/Oktober) eingeräumt werden. Im Winterquartier kein Dünger; Staunässe unbedingt vermeiden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | leaf, stem | easy |
| Spinnmilbe | Tetranychus urticae | Punkte, Gespinste bei trockener Luft | leaf | medium |
| Wurzelschmierlaus | Rhizoecus spp. | Weißes Pulver an Wurzeln (sichtbar bei Umtopfen) | root | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Phytophthora, Fusarium) | Weiche braune Basis, Blätter werden gelb-braun | Überbewässerung, Staunässe, kalter Standort |
| Blattbasisfäule | bacterial | Weiche, verfärbte Blattbasis, Faulgeruch | Wasser in der Blattkrone + Kälte |
| Aloe Rust | fungal (Phakopsora spp.) | Orangebraune Flecken auf Blättern | Selten Indoor; hohe Luftfeuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |
| Umtopfen + Austrocknen | cultural | Faule Wurzeln entfernen, 3–5 Tage trocknen vor Rückpflanzen | 0 | Wurzelfäule |
| Staunässe beseitigen | cultural | Topf mit Abzugslöchern; Untersetzer leeren | 0 | Prävention Wurzelfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|--------------------|--------------------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10 Tiere/m² je Ausbringung, 2–3 Wiederholungen im Abstand von 1–2 Wochen | ca. 2–4 Wochen |
| Raubmilbe (predatory mite) | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m² je nach Befallsdichte, wöchentliche Wiederholung | ca. 2–4 Wochen |
| Raubmilbe (predatory mite, präventiv) | Neoseiulus californicus | Spinnmilben (präventiv, niedrige Dichte) | herstellerabhängig (typ. wenige Tiere/m² präventiv) | ca. 3–4 Wochen |

> Hinweis: Nützlingseinsatz ist v. a. im Gewächshaus/Wintergarten praktikabel; in der reinen Zimmerkultur etablieren sich Räuber oft schlecht. Raten und Etablierungszeiten stammen aus dem geschützten Anbau (Koppert, Cornell NYS IPM) und sind nicht aloe-spezifisch, sondern schädlingsspezifisch.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze in DE.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Bogenhanf | Dracaena trifasciata | 0.9 | Identische Pflegeanforderungen |
| Kakteen | diverse | 0.9 | Identische Substrat- und Gießanforderungen |
| Echeveria | Echeveria spp. | 0.8 | Gleiche Pflegeanforderungen |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Aloe vera |
|-----|-------------------|-------------|------------------------------|
| Tiger-Aloe | Gonialoe variegata (syn. Aloe variegata) | Verwandte Gattung | Kompakter, dekorativ gefleckte Blätter |
| Spiral-Aloe | Aloe polyphylla | Gleiche Gattung | Spektakuläre Spiralform |
| Haworthia | Haworthiopsis fasciata (syn. Haworthia fasciata) | Ähnliche Wuchsform | Mehr Schattenverträglich, ideal für dunkle Standorte |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Aloe vera,"Echte Aloe;Aloe vera;True Aloe;Barbados Aloe",Asphodelaceae,Aloe,perennial,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b",0.0,"Arabische Halbinsel (Jemen, Oman)",yes,2-10,15,30-90,30-80,yes,yes,false,false,light_feeder
```

---

## Quellenverzeichnis

1. [Old Farmer's Almanac — Aloe Vera](https://www.almanac.com/plant/aloe-vera) — Kulturempfehlungen
2. [South Dakota State University Extension](https://extension.sdstate.edu/aloe-vera-houseplant-how) — Haushaltsnutzung, Pflege
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Bloomscape — Aloe Care Guide](https://bloomscape.com/plant-care-guide/aloe/) — Pflegehinweise
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/aloe-vera-care-guide-growing-and-maintaining-this-healing-succulent/) — Ganzjahrespflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Springer/Planta — CAM in leaves of Aloe arborescens](https://link.springer.com/article/10.1007/BF00388361) — Beleg CAM-Photosynthese in der Gattung Aloe
7. [PubMed — Changes in CAM expression in Aloe vera during drought and salt stress](https://pubmed.ncbi.nlm.nih.gov/34780703/) — Beleg konstitutive CAM-Photosynthese bei Aloe vera, Salztoleranz
8. [Wikifarmer — Aloe Soil Requirements, Soil Preparation and Planting](https://wikifarmer.com/library/en/article/aloe-soil-requirements-soil-preparation-and-planting) — Wurzeltiefe (20–30 cm), Boden-pH (7.0–8.5), Staunässe, Drainage
9. [LeafyJournal — Aloe Vera Root System](https://leafyjournal.com/aloe-vera-root-system/) — Bestätigung flach-extensives Wurzelsystem 20–30 cm
10. [MedCrave — Aloe vera screens at suitable salinity and sodicity level](https://medcraveonline.com/HIJ/aloe-vera-aloe-barbadeenis-mll-screens-at-suitable-salinity-and-sodicity-level.html) — Salztoleranz bis ~4 dS/m (Biosaline)
11. [Taylor & Francis — Aloe vera long-term saline irrigation](https://www.tandfonline.com/doi/abs/10.1080/09064710.2015.1049653) — moderate Salztoleranz, physiologische Reaktion auf Salzstress
12. [PictureThis — Optimal Temperature for Aloe vera](https://www.picturethisai.com/care/temperature/Aloe_vera.html) — Optimaltemperatur/Photosynthese-T_opt 21–27 °C, Minimum 4 °C
13. [Horticulture.co.uk — Overwintering Aloe vera](https://horticulture.co.uk/aloe-vera/overwintering/) — Überwinterung, Mindesttemperatur (5 °C), Winterquartier
14. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Schmierläuse, Ausbringrate
15. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Nützling gegen Spinnmilben, Ausbringrate
16. [Cornell NYS IPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Etablierung/Einsatz Raubmilbe gegen Spinnmilben
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: growing-phase-auditor 2026-07 (Korrektur Blütemonate) -->
17. [gartenjournal.net — Aloe Vera Blütezeit](https://www.gartenjournal.net/aloe-vera-bluetezeit-2) — Blüte meist zeitiges Frühjahr März–Mai, selten bereits Februar
18. [florage.de — Aloe Vera Blüten](https://florage.de/blogs/pflanzenblog/aloe-vera-bluten) — Blütezeit März bis Juni
19. [gartengemeinschaft.de — Aloe Vera Blütezeit](https://www.gartengemeinschaft.de/aloe-vera-wann-ist-die-bluetezeit/) — Blüte ab März bis April, selten bereits Februar
20. [aloeveraland.at — Blüten & Blütenstände der Aloen](https://www.aloeveraland.at/de/blueten-bluetenstaende-aloen) — Blütezeit März bis Juni
<!-- /Quelle: growing-phase-auditor 2026-07 (Korrektur Blütemonate) -->
