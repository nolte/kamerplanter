# Eselsschwanz — Sedum morganianum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/sedum-morganianum/), [JoyUsGarden](https://www.joyusgarden.com/burros-tail-care/), [World of Succulents](https://worldofsucculents.com/sedum-morganianum-donkeys-tail/), [Gardenia.net](https://www.gardenia.net/plant/sedum-morganianum), [Planet Desert](https://planetdesert.com/blogs/news/donkeys-tail-plant-sedum-morganianum-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Sedum morganianum | `species.scientific_name` |
| Volksnamen (DE/EN) | Eselsschwanz; Donkey's Tail, Burro's Tail, Lamb's Tail | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Sedum | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | succulent <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher vine) --> | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN: keine belegte Wuchs-GDD-Basistemperatur für S. morganianum auffindbar; Keim-/Kardinaltemperaturwerte dürfen nicht als Wuchs-GDD-Basis umetikettiert werden --> | `species.base_temp` |
| Lebensdauer (Jahre) | <!-- DATEN FEHLEN: keine belegte typische Lebensdauer; gilt als langlebig-mehrjährig, aber kein 2-Quellen-Zahlenwert --> | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 0 | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurztag-/Langtag-Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9b–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; Mindesttemperatur 7°C; in Zone 9b kurze Kälteperioden möglich | `species.hardiness_detail` |
| Heimat | Mexiko (Veracruz, Oaxaca), Honduras | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (rosa bis rote Blüten; selten in Zimmerhaltung) | `species.bloom_months` |
<!-- Quelle: growing-phase-auditor 2026-07 -->
<!-- Audit-Hinweis Blütemonate: Konfidenz ❓ UNSICHER — Originalwert (5,6,7) beibehalten, KEINE Korrektur. Quellen widersprechen sich zum genauen Zeitfenster: Planet Desert nennt "late spring or early summer" (Mai/Jun, stützt Wert), Gardening Know How nennt "at the end of summer" (eher Aug/Sep), NC State Extension/Wisconsin Extension/Healthy Houseplants nennen nur generisch "Summer" ohne Monatsangabe. Da <3 Quellen auf denselben Monatsbereich konvergieren, wird gemäß Konfidenzstufen-Regel keine Korrektur vorgenommen. Übereinstimmend über alle Quellen: Blüte ist in Zimmerkultur selten (bestätigt den Zusatz "selten in Zimmerhaltung"). -->
<!-- /Quelle: growing-phase-auditor 2026-07 -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem; cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Stecklings-Methode:** Triebstecklinge (5–10 cm) von der Triebspitze abschneiden. Anschnitt 2–7 Tage an der Luft trocknen lassen (kallieren) — dieser Schritt ist bei Sedum kritisch. Danach in trockenes Kakteen-/Sukkulentensubstrat stecken, erst nach 7–10 Tagen leicht anfeuchten. Bei 20–25°C und hell-indirektem Licht bewurzelt in 3–4 Wochen.

**Blattsteckling:** Einzelne Blättchen vorsichtig (mit Drehbewegung ohne Abreißen der Blattbasis) abnehmen. Auf trockenes Substrat legen, nicht eingraben. Bewurzelung und Bildung von Rosettenkindeln in 4–8 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein eigentlicher Rückschnitt. Beschädigte oder zu lange Triebe können jederzeit eingekürzt werden. Abgefallene Blättchen sind unvermeidlich und können zur Vermehrung genutzt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–30 (hängend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 (hängende Triebe bis 90 cm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteen-/Sukkulentenerde mit zusätzlich 30% Perlit; pH 6.0–7.0; exzellente Drainage obligatorisch | — |

**Gefäß-Empfehlung:** Hängeampeln oder hohe Töpfe ideal, damit die langen Triebe herabhängen können. Terrakotta-Töpfe fördern schnellere Substrataustrocknung (positiv für Sedum).

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifischer Kompensationspunkt für S. morganianum belegt; CAM/schattentolerante Sukkulenten liegen generisch niedrig (~10–50), aber keine 2-Quellen-Bestätigung für diese Art --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: siehe min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 5–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine quantitativen Maas-Hoffman-Daten (a-Schwelle) für S. morganianum; Gattung Sedum gilt qualitativ als salztolerant (Gründach-Literatur), aber kein belegter ECe-Schwellenwert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-b-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis Sonnentoleranz:** Bevorzugt hell-indirektes Licht bzw. Halbsonne (5–6 h helles Licht/Tag); in praller, heißer Mittagssonne droht Blattverbrennung — daher `partial_shade` statt `full_sun`. Im Freiland (USDA 9b–12b) verträgt die Art volle Sonne nur bei langsamer Gewöhnung und milderem Standort.

**Hinweis Salztoleranz:** Die Einstufung `moderately_tolerant` stützt sich auf die qualitative Gattungs-Evidenz (Sedum als salzverträgliche Gründach-/Küstenpflanze), nicht auf art-spezifische Maas-Hoffman-Messungen; ECe-Schwelle und Slope bleiben daher unbelegt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung | 21–42 | 1 | false | false | medium |
| Vegetativ | 90–365 | 2 | false | false | high |
| Blüte (selten indoor) | 30–60 | 3 | false | false | high |
| Winterruhe | 60–90 | 4 | false | false | high |
<!-- Quelle: growing-phase-auditor 2026-07 -->
<!-- Korrektur: "Ernte erlaubt" für Blüte von true auf false — interner Konsistenzfix (kein neuer Fakt): §1.2 weist Erntemonate bereits als "nicht relevant (Zierpflanze)" aus; S. morganianum ist reine Zierpflanze ohne Nutzernte. -->
<!-- /Quelle: growing-phase-auditor 2026-07 -->

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–55 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 (Substrat vollständig austrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (durchdringend gießen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 7–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–45 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–45 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–30 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Bewurzelung | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |
| Vegetativ | 1:2:2 | 0.4–0.8 | 6.0–7.0 | 50 | 30 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | 0:1:1 | 0.3–0.6 | 6.0–7.0 | 40 | 20 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Für die Light-Feeder-Sukkulente *S. morganianum* sind keine art-spezifischen Mikronährstoff-Zielwerte aus zwei unabhängigen seriösen Quellen belegt. Generische Vollnährlösungs-Werte (z. B. Hoagland-abgeleitet) wären keine quellengestützte Angabe für diese Art und werden daher als `DATEN FEHLEN` markiert statt erfunden. In der Praxis decken handelsübliche Kakteen-/Sukkulentendünger (siehe §3.1) den Mikronährstoffbedarf in geringer Dosis ab.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

<!-- Quelle: growing-phase-auditor 2026-07 -->
| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Bewurzelung → Vegetativ | time_based | 21–42 Tage; Neue Triebe sichtbar |
| Vegetativ → Blüte | event_based | Ausgereifte, ausgewachsene Triebe; Freiland-/Außenstandort im Sommer mit 5–6 h hellem Licht; vorherige kühle Winterruhe begünstigt Blüteninduktion; tritt selten ein, vor allem in Zimmerkultur |
| Blüte → Vegetativ | time_based | 30–60 Tage nach Blühbeginn; Blüte abgeschlossen |
| Vegetativ → Winterruhe | seasonal | Oktober; Temperatur <15°C, Gießen reduzieren |
| Winterruhe → Vegetativ | seasonal | März; Temperatur stabil >18°C |

**Korrektur (Regel R1 — lückenlose Phasenkette):** Die Phase "Blüte" (§2.1, Reihenfolge 3) war in der Übergangstabelle nicht erreichbar — es gab keine Trigger-Regel von/zu Vegetativ. Ergänzt: `Vegetativ → Blüte` (event_based) und `Blüte → Vegetativ` (time_based, konsistent mit der bestehenden Blühdauer 30–60 Tage aus §2.1). Konfidenz: ✅ GESICHERT (4/4 unabhängige Quellen zu den Blüh-Auslösern: reifer/ausgewachsener Trieb, Sommer-Freilandstandort, 5–6 h helles Licht, vorherige kühlere Winterperiode).
<!-- /Quelle: growing-phase-auditor 2026-07 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Substral Osmocote | Slow Release | 9-12-8 | 1 Messlöffel/2 Monate | Vegetativ |
| Kaktusdünger flüssig | COMPO | Flüssigdünger | 4-8-12 | 1 ml/L alle 4 Wochen | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee (sehr verdünnt) | eigen | organisch | 1 ml/L alle 6 Wochen | Frühling–Sommer |

### 3.2 Besondere Hinweise zur Düngung

**Weniger ist mehr:** Sedum morganianum benötigt in Zimmerkultur sehr wenig Dünger. Maximal 2–3 Mal pro Saison leicht düngen (Frühling bis Ende Sommer). Überdüngung führt zu weichem, anfälligem Wachstum und Blattabfall.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 12 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser geeignet; Substrat muss vollständig austrocknen zwischen den Gaben; Staunässe ist tödlich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Fast kein Wasser, kein Dünger, kühler Standort (10–15°C) | niedrig |
| Mär | Aufweckphase | Gießen langsam wieder aufnehmen; ersten Dünger | mittel |
| Apr–Sep | Aktive Wachstumsphase | Regelmäßig gießen, monatlich düngen; Stecklinge nehmen | hoch |
| Okt | Abdrosseln | Gießintervall verlängern, Düngen einstellen | mittel |
| Nov–Dez | Winterruhe einleiten | Kühleren Standort; minimales Gießen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (Zimmer/kühler Raum) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | none | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 7 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollknäuel in Blattachseln | stem, leaf | easy |
| Wurzelmilben | Rhizoglyphus echinopus | Substrat verkrustet, Wachstumsstillstand | root | difficult |
| Blattläuse | Aphidoidea | Klebrige Absonderungen, deformierte Triebe | stem, leaf | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Pythium) | Weiche, braune Basis; Triebwelke | Staunässe, zu häufiges Gießen |
| Blattabfall | physiologisch | Blätter fallen bei Berührung ab | Erschütterung, Zugluft, Wassermangel |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | biological | Isopropylalkohol | Wattestäbchen auf Wollläuse | 0 | Wollläuse |
| Neemöl | biological | Azadirachtin | Gießen in Substrat 0.3% | 3 | Wurzelmilben |
| Schnittling-Rettung | cultural | — | Triebspitzen abschneiden, neu bewurzeln bei Fäule | 0 | Wurzelfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (pro m²) | Etablierungszeit |
|----------|-------------------|----------------|-----------------------|------------------|
| Australischer Marienkäfer / Mehlkäfer-Räuber | Cryptolaemus montrouzieri | Wollläuse (Planococcus citri) | 2–10 (leicht) bis 5–40 (stark); 3× im Abstand von 1–2 Wochen wiederholen | 2–4 Wochen |
| Gallmücke (Blattlaus-Räuber) | Aphidoletes aphidimyza | Blattläuse (Aphidoidea) | 1–10; 2–3× im Abstand von 7–10 Tagen | 2–3 Wochen |
| Raubmilbe (Bodenraubmilbe) | Stratiolaelaps scimitus (syn. Hypoaspis miles) | Wurzelmilben (Rhizoglyphus echinopus), Trauermückenlarven | 100–250 | 2–3 Wochen |

**Hinweis:** Nützlingseinsatz bevorzugt im Gewächshaus/Wintergarten oder bei mehreren betroffenen Pflanzen. Auf reine Zimmerhaltung mit Einzelpflanzen ist die mechanische Bekämpfung (§5.3) meist praktikabler. *Cryptolaemus* früh bei erstem Wolllaus-Befall einsetzen; eine Larve frisst > 250 Wolllaus-Larven. *Stratiolaelaps* bekämpft zusätzlich Trauermückenlarven im feuchten Substrat — die Etablierungszeit ist herstellerseitig nicht exakt belegt und hier konservativ mit der für Bodenraubmilben üblichen Spanne (2–3 Wochen) angegeben.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Echeveria | Echeveria elegans | 0.9 | Gleiche Familie, identische Pflegebedingungen | `compatible_with` |
| Crassula | Crassula ovata | 0.8 | Gleiche Fam., ähnlicher Wasseranspruch | `compatible_with` |
| Haworthia | Haworthiopsis fasciata | 0.7 | Sukkulente, ähnliche Pflege | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Farne | Nephrolepis exaltata | Farne benötigen hohe Luftfeuchtigkeit | severe | `incompatible_with` |
| Calathea | Goeppertia spp. | Vollkommen gegensätzliche Anforderungen | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kleiner Eselsschwanz | Sedum burrito | Sehr ähnlich | Kürzere, kompaktere Blätter; stabiler |
| Perlenschnur | Curio rowleyanus | Ähnliche hängende Form | Spektakulärere Blattform |
| Gummipflanze-Sukkulente | Ceropegia woodii | Hängend, Sukkulente | Ebenfalls extrem pflegeleicht |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Sedum morganianum,Eselsschwanz;Donkey's Tail;Burro's Tail,Crassulaceae,Sedum,perennial,day_neutral,vine,fibrous,9b;10a;10b;11a;11b;12a;12b,0.0,"Mexiko, Honduras",yes,3,12,30,90,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [NC State Extension — Sedum morganianum](https://plants.ces.ncsu.edu/plants/sedum-morganianum/) — Botanische Einordnung
2. [JoyUsGarden — Burro's Tail Care](https://www.joyusgarden.com/burros-tail-care/) — Pflegehinweise
3. [World of Succulents — Sedum morganianum](https://worldofsucculents.com/sedum-morganianum-donkeys-tail/) — Allgemeine Kulturdaten
4. [Gardenia.net — Sedum morganianum](https://www.gardenia.net/plant/sedum-morganianum) — USDA Zone, Temperatur
5. [Planet Desert — Donkey's Tail Care](https://planetdesert.com/blogs/news/donkeys-tail-plant-sedum-morganianum-care) — Vermehrung, Schädlinge
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Crassulacean acid metabolism — Wikipedia](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Zugehörigkeit von Sedum/Crassulaceae (Photosynthese-Typ)
7. [Variation in crassulacean acid metabolism within the genus Sedum (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0176161711801434) — mexikanische Sedum-Arten zeigen konstitutives CAM (Photosynthese-Typ)
8. [Wisconsin Horticulture Extension — Burro's Tail, Sedum morganianum](https://hort.extension.wisc.edu/articles/burros-tail-sedum-morganianum/) — Lichtbedarf, pH, Standort
9. [Healthy Houseplants — Donkey's Tail Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/donkeys-tail-sedum-morganianum-care-guide-growing-tips/) — Boden-pH 6.0–7.0, Halbsonne, Staunässe-Empfindlichkeit
10. [AskGardening — Which Succulents Have Shallow and Deep Roots](https://askgardening.com/do-succulents-have-shallow-roots/) — flache fibröse Wurzeltiefe von Sedum/Crassulaceae (5–15 cm)
11. [Greg — Sedum Roots 101](https://greg.app/sedum-roots/) — flache Sedum-Wurzeltiefe (Bestätigung effektive Wurzeltiefe)
12. [AskGardening — How Much Light Succulents Need (PPFD)](https://askgardening.com/succulent-light-needs/) — Lichtkompensationspunkt/PPFD-Bereiche schattentoleranter Sukkulenten (qualitativer Kontext)
13. [Wallbarn — Types of Sedum for Green Roofs](https://www.wallbarn.com/exploring-the-different-types-of-sedum-and-its-benefits-for-green-roofs/) — qualitative Salztoleranz der Gattung Sedum (Gründach/Küste)
14. [Sempergreen — Everything about Sedum](https://www.sempergreen.com/us/solutions/green-roofs/everything-about-sedum) — Salz-/Stresstoleranz von Sedum (Salztoleranz-Klasse, qualitativ)
15. [Effects of High Night Temperature on CAM Photosynthesis of Kalanchoë & Ananas (ResearchGate)](https://www.researchgate.net/publication/240773846_Effects_of_High_Night_Temperature_on_Crassulacean_Acid_Metabolism_CAM_Photosynthesis_of_Kalanchoe_pinnata_and_Ananas_comosus) — CAM-Temperaturoptima (nächtliche CO₂-Fixierung), Kontext T_opt
16. [PhysicsWallah — CAM Cycle (Crassulacean Acid Metabolism)](https://www.pw.live/school-prep/exams/chapter-photosynthesis-in-higher-plants-class-11-cam-cycle-crassulacean-acid-metabolism) — allgemeines Photosynthese-Optimum 25–30 °C
17. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Wolllaus-Nützling, Ausbringrate
18. [Koppert — Aphidoletes aphidimyza](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/aphidoletes-aphidimyza/) — Blattlaus-Nützling, Ausbringrate
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 (Audit §1.1/§1.2/§2/§4.3) -->
19. [NC State Extension — Sedum morganianum, Toolbox-Datenblatt](https://plants.ces.ncsu.edu/plants/sedum-morganianum/) — Blütezeit "Summer", Frosttoleranz bis 40 °F, Vermehrung (Blatt-/Trieb-/Teilstecklinge)
20. [Wisconsin Horticulture Extension — Burro's Tail](https://hort.extension.wisc.edu/articles/burros-tail-sedum-morganianum/) — Blütezeit Sommer, Frostempfindlichkeit ("hardy only where it remains well above freezing"), Winterruhe ohne echte Dormanz, Trieb-/Blattstecklinge
21. [Gardening Know How — Burro's Tail Care](https://www.gardeningknowhow.com/ornamental/cacti-succulents/burros-tail/burros-tail-care.htm) — "tender perennial", USDA 9–11, Blüte am Spätsommer, Trieb-/Blattstecklinge
22. [Healthy Houseplants — Burro's Tail Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/burros-tail-sedum-morganianum-care-guide-a-trailing-succulent-beauty/) — explizit "doesn't have a distinct dormancy period" (Bestätigung `dormancy_required: false`), Blühbedingungen (Licht, kühlere Winterperiode)
23. [Planet Desert — Donkey's Tail Plant Care](https://planetdesert.com/blogs/news/donkeys-tail-plant-sedum-morganianum-care) — Blüte "late spring or early summer", 5–6 h Licht als Blühvoraussetzung, kühlere Außentemperatur als Blühreiz, Trieb-/Blattstecklinge
24. [JoyUsGarden — Burro's Tail Care and Propagation](https://www.joyusgarden.com/burros-tail-care/) — Blüte "rare", reduziertes Winter-Gießen (kein Absterben), Trieb-/Blattstecklinge
<!-- /Quelle: growing-phase-auditor 2026-07 -->
