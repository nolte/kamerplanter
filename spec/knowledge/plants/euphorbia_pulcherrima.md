# Weihnachtsstern — Euphorbia pulcherrima

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Pflanzen-Kölle – Weihnachtsstern](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-weihnachtsstern-richtig/), [PlantFrand – Euphorbia pulcherrima](https://www.plantfrand.com/pflanzen/euphorbiaceae/euphorbia-pulcherrima/), [Feey – Weihnachtsstern](https://feey.ch/pages/weihnachtsstern), [Zimmerpflanzen-Portal](https://www.zimmerpflanzen-portal.de/weihnachtsstern-euphorbia-pulcherrima/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Euphorbia pulcherrima | `species.scientific_name` |
| Volksnamen (DE/EN) | Weihnachtsstern, Poinsettie; Poinsettia, Christmas Star | `species.common_names` |
| Familie | Euphorbiaceae | `species.family` → `botanical_families.name` |
| Gattung | Euphorbia | `species.genus` |
| Ordnung | Malpighiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | 5–10 (Wildform/Kübel; als Zimmerpflanze 2–3) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | ~12.25 (Blüteinduktion bei Photoperiode ≤ ca. 12¼ h bzw. Dunkelphase ≥ 11¾ h) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | In Mitteleuropa nur als Zimmerpflanze; Frostgrenze ca. +5°C | `species.hardiness_detail` |
| Heimat | Mexiko, Mittelamerika | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 11, 12, 1 (Kurztagspflanze, Weihnachtszeit) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, insbesondere Milchsaft (Latex) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Euphorbon (Diterpen-Ester), Milchsaft-Latex | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Der Milchsaft kann Hautreizungen und Schleimhautentzündungen verursachen. Die Toxizität wurde in der Vergangenheit überschätzt — für Erwachsene sind größere Mengen nötig für ernste Vergiftungserscheinungen. Bei Kindern und Haustieren dennoch Vorsicht geboten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 (in Natur bis 400 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Zimmerpflanzenerde; keine Staunässe; pH 6.0–6.5 | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Schwelle publiziert; Anbau-Empfehlung Substrat-EC 2.6–4.6 mS/cm (PourThru) ist kein ECe-Schwellenwert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.8–6.5 | `species.soil_ph_preference` |

> **Hinweis Licht:** Poinsettie ist im Freiland eine Halbschatten-Pflanze (partial_shade) und akklimatisiert sich in Innenräumen an niedrige Lichtintensitäten (bis ~10 µmol/m²/s); produktionsoptimal sind dagegen ~500 µmol/m²/s (PPFD). Ein artspezifischer Lichtkompensationspunkt-Zahlenwert (light compensation point, Netto-Photosynthese = 0) ist publiziert gemessen, aber ohne belastbare µmol-Angabe aus zwei unabhängigen Quellen — daher als DATEN FEHLEN markiert (keine Erfindung).
> **Hinweis Salz/pH:** Poinsettie reagiert empfindlich auf hohe lösliche Salze (soluble salts) im Substrat. Der Species-pH-Vorzug 5.8–6.5 (leicht sauer; gärtnerischer Standard für Poinsettien 5.5–6.5) ist der breitere Toleranzbereich; die engeren Empfehlungswerte in §1.6 (6.0–6.5) und §2.3 (6.0–6.5) liegen vollständig innerhalb dieses Bereichs (gemeinsame Schnittmenge 6.0–6.5) — kein Widerspruch.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Akklimatisierung | 14–21 | 1 | false | false | low |
| Vegetativ (Wachstum) | 180–210 | 2 | false | false | medium |
| Blüteinduktion (Kurztag) | 42–63 | 3 | false | false | low |
| Blüte/Hochblätter | 60–90 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum) — Frühjahr bis Herbst

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.40–0.50 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüteinduktion (Kurztag) — ab Oktober

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | max. 10 (strikt!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.9–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.40–0.50 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Akklimatisierung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->—<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | — | — | — |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.25 | 0.05 | 0.1 |
| Blüteinduktion | 1:2:3 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.25 | 0.05 | 0.2 |
| Blüte | 0:1:2 | 0.6–1.0 | 6.0–6.5 | 80 | 30 | — | 1 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.3<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.15 | 0.05 | 0.1 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> **Hinweis Mikronährstoffe:** Molybdän (Mo) ist beim Weihnachtsstern der kritischste Mikronährstoff; ein konstantes Feed-Programm (constant liquid feed) hält ~0.1–1.2 ppm Mo aufrecht (poinsettie-spezifisch erhöht), Blattgewebe-Zielwerte 1–5 ppm Mo. Mangan (Mn) liegt im CLF i.d.R. bei ~50 % des Eisengehalts; Blattgewebe-Sufficiency Mn 45–300 ppm, Zn 25–100 ppm, Cu 3–25 ppm, Mo 1–5 ppm. Die ppm-Werte oben beziehen sich auf die Düngerlösung (Feed-Solution), nicht auf Blattgewebe.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Akklimatisierung → Vegetativ | time_based | 14–21 Tage | Neue Blätter sichtbar |
| Vegetativ → Blüteinduktion | event_based | — | Tageslänge unter 10 Stunden (Anfang Oktober) |
| Blüteinduktion → Blüte | time_based | 42–63 Tage | Hochblätter färben sich |
<!-- Quelle: growing-phase-auditor 2026-07 -->
| Blüte/Hochblätter → Vegetativ | event_based | — | Rückschnitt nach Verblühen (Feb–März, auf ~15 cm; siehe §1.5/§4.3); Neuaustrieb ab April (Umtopfen, Düngung startet) — schließt den mehrjährig-polykarpen Blühzyklus für die nächste Saison |
<!-- /Quelle: growing-phase-auditor 2026-07 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Compo | base | 4-6-8 | 5 ml/L | 1 | blüteinduktion, blüte |
| Grünpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Blumendünger flüssig | Guano Kalong | organisch | 2 ml/L | Apr–Sep | medium_feeder |
| Langzeitdünger Stäbchen | Compo Sana | organisch/langsam | 1 Stäbchen alle 3 Monate | Apr–Sep | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–3 | Akklimatisierung | 0.0 | — | — | Kein Dünger, Stressvermeidung |
| 4–26 | Vegetativ | 1.0–1.5 | 6.2 | 5 | Monatlich düngen |
| Okt–Nov | Blüteinduktion | 0.8–1.2 | 6.2 | 5 | Alle 4 Wochen, phosphorlastig |
| Dez–Jan | Blüte | 0.6–1.0 | 6.2 | — | Kein Dünger nötig |

### 3.3 Mischungsreihenfolge

1. Wasser (Raumtemperatur, nie kalt)
2. Flüssigdünger

### 3.4 Besondere Hinweise zur Düngung

Der Weihnachtsstern ist als Kurztagspflanze auf exakt gesteuerte Beleuchtung angewiesen — für die Wiederblüte nach dem Kauf müssen ab Oktober täglich mindestens 14 Stunden vollständige Dunkelheit garantiert werden (auch künstliche Lichtquellen verhindern Blüteinduktion!). Düngung spielt gegenüber der Lichtsteuerung eine untergeordnete Rolle.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser, keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Blüte beobachten | Wenig gießen, nicht düngen, Zugluft vermeiden | niedrig |
| Feb | Rückschnitt vorbereiten | Blüte verblüht, Pflanze beginnt einzuziehen | mittel |
| Mär | Rückschnitt | Stark zurückschneiden (auf 15 cm), frische Erde | hoch |
| Apr | Umtopfen | In frisches Substrat, Düngung beginnen | hoch |
| Mai–Aug | Wachstum | Regelmäßig gießen und düngen, heller Standort | hoch |
| Sep | Wachstum beenden | Letzte Düngung | mittel |
| Okt | Kurztag-Behandlung | Ab 1. Oktober tägl. 14 Stunden Dunkelheit (Karton) | hoch |
| Nov | Blüteinduktion kontrollieren | Hochblätter müssen sich färben | hoch |
| Dez | Dekorativer Höhepunkt | Zimmerwarm, heller Standort, sparsam gießen | niedrig |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (spätestens wenn Außentemperatur < 10 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | prune | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (Rückschnitt auf ~15 cm; Sommerausstellung erst nach den Eisheiligen Mitte Mai) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (Blütephase); nicht unter 12 °C | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (Süd-/Ostfenster), kein direktes Mittagslicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam; Substrat antrocknen lassen, keine Staunässe | `overwintering_profiles.winter_quarter_watering` |

> **Hinweis:** Der Weihnachtsstern ist frostempfindlich (tender) und wird in Mitteleuropa (USDA 6–8) ausschließlich frostfrei als Zimmerpflanze überwintert (move_indoors), nicht ausgegraben/eingelagert. Im Sommer kann er ins Freie (move_outdoors) gestellt werden, sobald keine Nachtfröste mehr drohen; Rücktransport ins Haus, bevor die Temperatur unter ~10 °C fällt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Weiße Fliege | Trialeurodes vaporariorum | Weiße Fliegen bei Berühren, Honigtau | leaf | alle | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbfleckige Blätter | leaf | vegetative | medium |
| Schmierläuse | Pseudococcus longispinus | Weiße Wollflecken, Honigtau | stem, leaf | alle | medium |
| Trauermücken | Sciara spp. | Larven in Substrat | root | alle | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel (Botrytis) | fungal | Grauer Schimmelbelag | high_humidity, poor_airflow | 3–7 | flowering |
| Wurzelfäule | fungal | Welke Blätter, schwarze Wurzeln | overwatering | 7–14 | alle |
| Bakterielle Weichfäule | bacterial | Weiche, nasse Stellen am Stängel | waterlogging, wounds | 3–7 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Steinernema feltiae | Trauermückenlarven | 0.5 Mio. Nematoden/m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gelbkarten | mechanical | — | Aufhängen neben Pflanze | 0 | Weiße Fliege, Trauermücken |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Weiße Fliege, Spinnmilben |
| Pyrethrin | chemical | Pyrethrum | Sprühen nach Anweisung | 1 | Weiße Fliege, Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Euphorbia pulcherrima |
|-----|-------------------|-------------|------------------------------|
| Weihnachtskaktus | Schlumbergera truncata | Kurztagspflanze, Winterblüher | Langlebiger, pflegeleichter |
| Kalanchoe | Kalanchoe blossfeldiana | Kurztagspflanze, Winterblüher | Robuster, weniger anspruchsvoll |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Euphorbia pulcherrima,Weihnachtsstern;Poinsettie;Christmas Star,Euphorbiaceae,Euphorbia,perennial,short_day,shrub,fibrous,9a;9b;10a;10b;11a;11b,0.0,Mexiko Mittelamerika,yes,3,15,60,40,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle – Weihnachtsstern Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-weihnachtsstern-richtig/) — Pflege, Standort
2. [PlantFrand – Euphorbia pulcherrima](https://www.plantfrand.com/pflanzen/euphorbiaceae/euphorbia-pulcherrima/) — Botanik, Toxizität
3. [Feey – Weihnachtsstern](https://feey.ch/pages/weihnachtsstern) — Steckbrief, Überwinterung
4. [Zimmerpflanzen-Portal](https://www.zimmerpflanzen-portal.de/weihnachtsstern-euphorbia-pulcherrima/) — Schädlinge, Krankheiten
5. [Landwirtschaft BW – Nützlinge Weihnachtsstern](https://www.landwirtschaft-bw.de/site/pbs-bw-new/get/documents/MLR.LEL/PB5Documents/ltz_ka/Arbeitsfelder/Pflanzenschutz/N%C3%BCtzlinge/Zierpflanzenbau/Gesch%C3%BCtzter%20Anbau%20(Gew%C3%A4chshaus)/Sch%C3%A4dlinge%20und%20N%C3%BCtzlingseinsatz%20weihnachtsstern.pdf) — Biologischer Pflanzenschutz
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [UF/IFAS – Poinsettia Production Guidelines](https://hort.ifas.ufl.edu/floriculture/poinsettia/production_guidelines.shtml) — Basistemperatur, pH, Temperaturführung
7. [Aggie Horticulture (Texas A&M) – Poinsettia Cultural Characteristics](https://aggie-horticulture.tamu.edu/ornamental/the-texas-poinsettia-producers-guide/cultural-characteristics/) — Photoperiode, kritische Dunkelphase, Temperatur
8. [Aggie Horticulture (Texas A&M) – Poinsettia Nutrition](https://aggie-horticulture.tamu.edu/ornamental/the-texas-poinsettia-producers-guide/poinsettia-nutrition/) — Mikronährstoffe, Molybdän, Mangan
9. [ScienceDirect – Growth and development of poinsettia under reduced air temperature](https://www.sciencedirect.com/science/article/abs/pii/S0304423816303491) — GDD-Basistemperatur 10 °C, Wuchsoptima
10. [Greenhouse Grower – How to Manage the 3 M's of Poinsettias (Mn, Mo, Mg)](https://www.greenhousegrower.com/production/fertilization/how-to-manage-the-3-ms-of-poinsettias-manganese-molybdenum-and-magnesium/) — Mn/Mo-Bedarf, Blattgewebewerte
11. [UMass Extension – Fertilizer Recommendations for Poinsettias](https://www.umass.edu/agriculture-food-environment/greenhouse-floriculture/fact-sheets/fertilizer-recommendations-for-poinsettias) — Feed-pH, Mikronährstoff-Programm
12. [Greenhouse Grower – Producing Poinsettias Sustainably](https://www.greenhousegrower.com/crops/producing-poinsettias-sustainably/) — Substrat-EC/Salzempfindlichkeit
13. [HGTV – Poinsettia Care Through Winter and Beyond](https://www.hgtv.com/gardening/flowers-and-plants/poinsettia-care-through-winter-and-beyond) — Überwinterungstemperatur, frostfrei
14. [Oklahoma State University Extension – Poinsettia Care](https://extension.okstate.edu/fact-sheets/poinsettia-care) — Überwinterung, Rückschnitt, Standort
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
15. [Purdue University Extension – Reflowering Poinsettias](https://www.purdue.edu/hla/sites/yardandgarden/reflowering-poinsettias/) — Jährlicher Rückschnitt-/Wiederaustrieb-/Kurztag-Zyklus (Phasenrücksprung Blüte → Vegetativ)
16. [University of Maryland Extension – Poinsettias](https://extension.umd.edu/resource/poinsettias) — Rückschnitt April/Mai, Neuaustrieb, Pinzieren Juli, Kurztag-Induktion ab Oktober
<!-- /Quelle: growing-phase-auditor 2026-07 -->
