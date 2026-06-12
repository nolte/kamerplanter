# Sojabohne — Glycine max

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, University of Illinois Extension Soybean, Bayerische LfL Soja, Iowa State University Extension, FAO Soybean Crop Profile

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Glycine max | `species.scientific_name` |
| Volksnamen (DE/EN) | Sojabohne, Soya; Soybean, Soya Bean | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Glycine | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Kritische Tageslänge (critical day length, h) | ~13 (Kurztag-Blüteninduktion; angepasste Genotypen mittlerer Breiten — Blüte wird ausgelöst, wenn die Tageslänge diesen Wert unterschreitet) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 5a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frost-empfindlich; Mindestkeimtemperatur 10°C (besser 15°C); stirbt bei -2°C ab; in Mitteleuropa als Sommerkorn ab Ende Mai bis Mitte Juli | `species.hardiness_detail` |
| Heimat | Ostasien (China, Japan); domestiziert ca. 3000 v. Chr. in China | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**N-Fixierung:** Sojabohne fixiert in Symbiose mit *Bradyrhizobium japonicum* 50–150 kg N/ha pro Saison — das bedeutet kaum N-Düngung nötig. Impfung des Saatgutes mit Bradyrhizobium dringend empfohlen, besonders bei Erstanbau auf dem Standort! Rückstände der Sojawurzel bereichern den Boden für Folgekulturen erheblich.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (optional; Direktsaat bevorzugt da Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 7–14 (Bodentemperatur mind. 10°C; besser 15°C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 9, 10 (Trockenbohne); 8, 9 (Edamame = grüne Sojabohne) | `species.harvest_months` |
| Blütemonate | 7, 8 | `species.bloom_months` |

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
| Giftige Pflanzenteile | Rohe Bohnen (Hämagglutinin, Trypsinhemmer; werden beim Kochen inaktiviert) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Hämagglutinin, Trypsin-Inhibitoren (roh); Isoflavone (hormonaktiv; relevant für bestimmte Personengruppen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (nur roh; nach Erhitzen unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis Sojaprotein-Allergie:** Soja zählt zu den 14 großen EU-Lebensmittelallergenen. Sojaprotein kann bei Allergikern starke Reaktionen auslösen. Nicht zu verwechseln mit der Pflanze selbst — die Pflanze im Garten ist unbedenklich.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 (Pfahlwurzel; breite Töpfe) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5–10 cm in der Reihe; 40–60 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leicht durchlässige, lehmige Erde; pH 6,0–6,8; gut drainiert; kein Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–120 (Pfahlwurzel kann 150–200 cm erreichen; ~70–95 % der Wurzelmasse und des Wasserentzugs liegen jedoch in den oberen ~30 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (salt tolerance threshold, dS/m) | 5.0 (Maas-Hoffman a; bezogen auf Substrat-Sättigungsextrakt-ECe, NICHT Gießwasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (salt tolerance slope, %/dS/m) | 20 (Maas-Hoffman b; Ertragsrückgang je dS/m oberhalb der Schwelle) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–6.8 | `species.soil_ph_preference` |

**Hinweis Lichtkompensationspunkt:** Für *Glycine max* ließen sich keine zwei unabhängigen, belastbaren PPFD-Messwerte des Blatt-Lichtkompensationspunktes finden; Feld daher als DATEN FEHLEN markiert. Belegt ist lediglich, dass die Lichtsättigung der Einzelblatt-Photosynthese erst bei rund 25 % des vollen Sonnenlichts (~500 µmol/m²/s PPFD) abzuflachen beginnt — das ist ein Sättigungs-, kein Kompensationswert und gehört nicht in das Kompensationspunkt-Feld.

**Hinweis Salztoleranz:** Soja gilt nach der Maas-Hoffman-Klassifikation der FAO als mäßig salztolerant (MT). Die ECe-Schwelle von 5,0 dS/m bezieht sich auf den Sättigungsextrakt des Wurzelmediums (Bodensalzgehalt), nicht auf die elektrische Leitfähigkeit der Nährlösung in §2.3 (EC in mS) — beide Größen dürfen nicht gleichgesetzt werden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling (V1–V3) | 14–21 | 2 | false | false | low |
| Vegetativ (V4–V6) | 21–42 | 3 | false | false | medium |
| Blüte (R1–R2) | 14–21 | 4 | false | false | low |
| Hülsenbildung (R3–R4) | 21–28 | 5 | false | true | medium |
| Samenreife (R5–R8) | 28–42 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.1 (kritischer Punkt deutlich oberhalb des Zielkorridors; feuchteliebende Keimphase → niedrige Schwelle) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 (Freiland-Sonnenlicht; nicht mit R:FR-Verhältnis verwechseln) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–3 (gleichmäßig feucht; kein Staunässe) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ (V4–V6)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | >13 (Langtagbedingungen verhindern vorzeitige Blüte; Kurztagpflanze) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 24–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.7 (kritischer stomatärer Kollaps oberhalb des Zielkorridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 26–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 (Freiland-Sonnenlicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blüte (R1–R2)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–38 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | ≤13 (Kurztagblüher; Blüteninduktion durch kürzere Tage) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 24–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.8 (oberhalb des Zielkorridors; höheres Trockenstress-Risiko mindert Hülsen-Setzrate) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 (Freiland-Sonnenlicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–5 (regelmäßige Bewässerung kritisch für Setzrate) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Samenreife (R5–R8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 (trocken = bessere Druschfähigkeit) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 2.2 (Abreifephase toleriert höhere VPD; Kollaps-Punkt oberhalb des Zielkorridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 (Freiland-Sonnenlicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 (Wasserreduktion zur Abreife) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mo (µg/L) |
|-------|----------------|---------|-----|----------|----------|---------|
| Keimung | 0:0:0 | 0.0 | 6.0–6.8 | — | — | — |
| Sämling | 0:1:1 | 0.4–0.8 | 6.0–6.8 | 60 | 25 | 10 |
| Vegetativ | 0:1:2 | 0.8–1.4 | 6.0–6.8 | 100 | 40 | 10 |
| Blüte | 0:2:2 | 1.0–1.6 | 6.0–6.8 | 100 | 50 | 10 |
| Reife | 0:1:1 | 0.6–1.0 | 6.0–6.8 | 60 | 30 | — |

**Hinweis:** Keine N-Düngung nötig bei funktionierender Bradyrhizobium-Symbiose! Molybdän (Mo) ist für die N-Fixierung im Knöllchen essentiell — bei Mo-Mangel bricht Fixierung zusammen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoff-Richtwerte (Blattgewebe-Sufficiency-Range, oberstes voll entwickeltes Trifoliat zur Blüte/frühen Hülse):** Diese Spurenelement-Zielbereiche gelten phasenübergreifend (vegetativ bis Hülsenbildung) und beziehen sich auf die Gewebekonzentration der Pflanze, NICHT auf die Düngerlösung der EC-Tabelle oben.

| Mikronährstoff | Sufficiency-Range (ppm) | KA-Feld |
|----------------|-------------------------|---------|
| Mangan (Mn) | 20–100 | `nutrient_profiles.manganese_ppm` |
| Zink (Zn) | 20–60 | `nutrient_profiles.zinc_ppm` |
| Kupfer (Cu) | 6–30 | `nutrient_profiles.copper_ppm` |
| Molybdän (Mo) | 1–5 | `nutrient_profiles.molybdenum_ppm` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Biologisch/Mineralisch

| Produkt | Marke | Typ | Ausbringrate | Phasen |
|---------|-------|-----|-------------|--------|
| Bradyrhizobium japonicum (Impfmittel) | diverse (Sojaculture, HiStick) | Saatgutimpfung | 250 ml/25 kg Saatgut | Vor Saat |
| Superphosphat / Triplesuperphosphat | diverse | mineralisch | 20–30 g/m² P₂O₅ | Grunddüngung |
| Kaliumsulfat | diverse | mineralisch | 15–25 g/m² K₂O | Grunddüngung |
| Molybdänblattdünger | diverse | Spurenelement | 0,1 g/L; 1× sprühen | Keimlingsstadium |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost (reif) | eigen | organisch | 3–5 L/m² | Herbst/Frühjahr |
| Hornmehl | diverse | organisch | 30–50 g/m² | Sparsam (N-Fixierung beachten!) |
| Kalkstein (gemahlen) | diverse | pH-Korrektur | je nach Bedarf | Herbst |

### 3.2 Mischungsreihenfolge (bei Flüssigdüngung)

> **Kritisch:** Bradyrhizobium-Impfmittel ist empfindlich gegen direkte Sonneneinstrahlung und chemische Dünger — Saat nach Impfung sofort einbringen!

1. Saatgut anfeuchten (Wasser)
2. Bradyrhizobium-Impfmittel auftragen und gut vermengen
3. Sofort bei bedecktem Himmel säen (Lichtempfindlichkeit der Bakterien)
4. KEINE chemischen Beizmittel gleichzeitig mit Bradyrhizobium verwenden

### 3.3 Besondere Hinweise zur Düngung

Sojabohne ist Stickstofflieferant, KEIN Stickstoffverbraucher. Übermäßige N-Düngung hemmt die symbiotische N-Fixierung — Knöllchen bleiben klein oder weiß statt rosa/rot. Ziel: Phosphor- und Kaliumversorgung sichern; N nur minimal bei Anlaufschwierigkeiten der Knöllchenbakterien.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4–7 | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | pH 6,0–6,8; kalkreiches Wasser kalibrieren | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 (P + K; kein N) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–8 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Planung / Saatgut | Bradyrhizobium-Impfmittel beschaffen; frühreife Sorte wählen | hoch |
| Mai | Aussaat | Ab 10°C Bodentemperatur; Direktsaat 2–3 cm tief; 5 cm Reihenabstand | hoch |
| Jun | Kontrolle Knöllchen | Erste Knöllchen 2–3 Wochen nach Auflauf prüfen (rosa innen = aktiv) | mittel |
| Jul–Aug | Blüte | Stress vermeiden; gleichmäßig gießen | hoch |
| Aug | Edamame-Ernte (optional) | Hülsen voll aber Körner noch grün; 65% Wassregehalt | mittel |
| Sep–Okt | Reifeernte | Hülsen braun; Blätter abgefallen; 15% Feuchte | hoch |
| Okt–Nov | Bodenbearbeitung | Wurzelrückstände einarbeiten; N-Depot für Folgekultur | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Bohnenblattlaus | Aphis fabae | Schwarze Kolonien; Honigtau | Blatt, Trieb | Vegetativ, Blüte |
| Sojakäfer / Bohnenkäfer | Acanthoscelides obtectus | Larven in Körnern; Lagerbefall | Korn | Lager |
| Thripse | Frankliniella occidentalis | Silberflecken; Blattdeformation | Blatt, Hülse | Blüte |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; Gelbflecken | Blatt | Hitzesommer |
| Weißer Stängelälchen | Ditylenchus dipsaci | Stängelverformung; Schäden | Stängel | Sämling |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Sklerotinia-Stängelfäule | fungal (Sclerotinia sclerotiorum) | Weißer Pilzrasen; Halmfäule | feucht; Fruchtfolge |
| Sojarost | fungal (Phakopsora pachyrhizi) | Braun-orangene Pusteln; Blattfall | warm-feucht; eingeschleppt |
| Bakterielle Pusteln | bacterial (Xanthomonas axonopodis) | Gelb-braune Blattflecken | warm; Nässe |
| Saatgutfäule | fungal (Pythium, Rhizoctonia) | Auflaufschäden; Keimlingsfäule | kalter, feuchter Boden |
| Mosaik (SMV) | viral (Soybean Mosaic Virus) | Mosaikflecken; Deformation | Blattlaus-Übertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) |
|----------|---------------|-------------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse | 1–3 |
| Florfliegenlarven (Chrysoperla carnea) | Blattläuse, Thripse | 5–10 |
| Amblyseius cucumeris | Thripse | 25–50 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Thripse |
| Schmierseife | biological | Kaliumoleat | Sprühen 2–3% | 1 | Blattläuse |
| Kupferfungizid | biological/chemical | Kupferhydroxid | Sprühen | 14 | Bakterielle Pusteln |
| Fungizid (Thiophanat) | chemical | Thiophanat-methyl | Sprühen | 14 | Sklerotinia |
| Weite Fruchtfolge | cultural | — | 3–4 Jahre Pause | 0 | Sklerotinia, Sojarost |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Heterodera glycines (Sojazysten-Nematode) | Schädling (sortenabhängig) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (kein N-Dünger nötig) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide (Weizen, Mais, Gerste) |
| Empfohlene Nachfrucht | Winterweizen, Mais, Kartoffel (profitieren vom N-Depot) |
| Anbaupause (Jahre) | 3–4 Jahre auf gleichem Standort (Sklerotinia, Nematoden) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.9 | Klassisches Soja-Mais-Gemenge; Mais-Stütze; N-Transfer | `compatible_with` |
| Sorghum | Sorghum bicolor | 0.8 | Trockenheitstolerantes Gemenge | `compatible_with` |
| Saflor | Carthamus tinctorius | 0.7 | Trockentolerantes Gemenge; Insektenweide | `compatible_with` |
| Tagetes | Tagetes erecta | 0.8 | Nematoden-Hemmung; Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Knoblauch | Allium sativum | Hemmt Knöllchenbildung (antibiotische Allicin-Wirkung) | moderate | `incompatible_with` |
| Zwiebel | Allium cepa | Gleiche antibiotische Wirkung auf Rhizobien | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Gleiche Familie; Sklerotinia-Risiko; N-Konkurrenz | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Fabaceae | `shares_pest_risk` | Sklerotinia, Aphanomyces, Bohnenkäfer | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Sojabohne |
|-----|-------------------|-------------|------------------------------|
| Ackerbohne | Vicia faba | Fabaceae; kühltolerant | Winteranbau möglich; frühere Ernte |
| Lupin (Süßlupine) | Lupinus albus / mutabilis | Fabaceae; N-Fixierung | Trockentoleranter; saure Böden |
| Schwarzaugenbohne | Vigna unguiculata | Fabaceae; tropische Hülsenfrucht | Hitzestressor; trockentoleranter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Glycine max,"Sojabohne;Soya;Soybean;Soya Bean",Fabaceae,Glycine,annual,short_day,herb,taproot,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Ostasien",limited,no,limited,false,false,nitrogen_fixer,true,tender,"5;6","8;9;10","7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Sultana,Glycine max,"early;edamame;medium_plant;mitteleuropa_adapted",90,open_pollinated
Moso,Glycine max,"grain_type;high_protein;early;mitteleuropa",95,open_pollinated
ES Mentor,Glycine max,"grain_type;high_yield;maturity_group_000",100,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS — Glycine max](https://plants.usda.gov/plant-profile/GLMA4) — Taxonomie
2. [Iowa State University Extension — Soybean Production](https://crops.extension.iastate.edu/soybean) — Phasen, Nährstoffe
3. [Bayerische LfL — Sojaanbau](https://www.lfl.bayern.de/ipz/leguminosen) — Mitteleuropa-Anbau
4. [FAO Soybean Crop Profile](https://www.fao.org) — Globale Anbausysteme
5. [Donau Soja Anbauleitfaden](https://www.donausoja.org) — Praxisempfehlungen für Europa
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RIPE / University of Illinois — A critical review on the improvement of photosynthetic carbon assimilation in C3 plants](https://ripe.illinois.edu/sites/ripe.illinois.edu/files/2018-06/A%20critical%20review%20on%20the%20improvement%20of%20photosynthetic%20carbon%20assimilation%20in%20C3%20plants%20using%20genetic%20engineering.pdf) — Soja als C3-Pflanze (Photosynthese-Typ)
7. [PMC — Soybean photosynthetic and biomass responses to CO₂ concentrations](https://pmc.ncbi.nlm.nih.gov/articles/PMC7475242/) — C3-Photosynthese, CO₂-Antwort (Photosynthese-Typ)
8. [NRCCA / Cornell — Calculating growing degree days](https://nrcca.cals.cornell.edu/crop/CA2/CA0209.php) — GDD-Basistemperatur 10 °C für warmliebende Kulturen inkl. Soja
9. [ScienceDirect — Base and upper temperature thresholds for GDD (Review)](https://www.sciencedirect.com/science/article/pii/S037837742500469X) — Soja-Tbase 7–10 °C, Tupper 30 °C
10. [USPTO — Soybean variety patent (Photoperiod section)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8772586) — Kurztagpflanze, kritische Tageslänge ~13 h für angepasste Genotypen, 9 Tage photoperiodisch unsensibel nach Auflauf
11. [OCL Journal — Genotypic differences in root traits of drought-avoiding soybean ideotypes](https://www.ocl-journal.org/articles/ocl/full_html/2022/01/ocl210095/ocl210095.html) — Wurzeltiefe (Pfahlwurzel bis 150–200 cm, Wassersaum oberer 30 cm)
12. [NC State Extension — Water Management in Soybeans](https://content.ces.ncsu.edu/north-carolina-soybean-production-guide/10-water-management-in-soybeans) — ~70 % Wasseraufnahme in oberen 30 cm (effektive Wurzeltiefe)
13. [Frontiers in Genetics — Prioritization and Evaluation of Flooding Tolerance Genes in Soybean](https://www.frontiersin.org/journals/genetics/articles/10.3389/fgene.2020.612131/full) — Soja staunässe-/flutungs-empfindlich (waterlogging tolerance)
14. [FAO — Annex 1: Crop salt tolerance data (Maas & Hoffman)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Soja ECe-Schwelle 5,0 dS/m, Slope 20 %/dS/m, Rating MT (moderately tolerant)
15. [IntechOpen — Salt Stress Responses and Tolerance in Soybean](https://www.intechopen.com/chapters/80766) — Soja mäßig salztolerant; Ertragsrückgang 20 %/dS/m über 5,0 dS/m
16. [MSU Extension — Managing soil pH for optimal soybean production](https://www.canr.msu.edu/news/managing_soil_ph_for_optimal_soybean_production) — Boden-pH-Vorzug 6,0–6,8; Vollsonne
17. [University of Wisconsin Soil Science Extension — Effect of Soil pH on Soybean Yield](https://extension.soils.wisc.edu/wcmc/effect-of-soil-ph-on-soybean-yield/) — Boden-pH-Optimum (Bestätigung pH 6,0–6,8)
18. [Frontiers in Plant Science — Phosphorus Nutrition Affects Temperature Response of Soybean Canopy Photosynthesis](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2018.01116/full) — Photosynthese-T_opt Soja 25–30 °C, reproduktiv ~28 °C
19. [ISHS — Optimum and sub-optimal temperature effects on stomata and photosynthesis of determinate soybeans](https://ishs.org/ishs-article/440_15/) — Photosynthese-Optimumtemperatur (Bestätigung T_opt)
20. [Annals of Botany / Zhen & Bugbee — Far-red light effects on plant photosynthesis](https://academic.oup.com/aob/article/135/3/589/7701832) — Far-Red-Fraction direktes Sonnenlicht ≈ 0,46 FR/(R+FR)
21. [SDSU Extension — Plant Nutrient Analysis: Do your soybeans have the right stuff?](https://extension.sdstate.edu/plant-nutrient-analysis-do-your-soybeans-have-right-stuff) — Blattgewebe-Sufficiency-Ranges Mn 30–100, Zn 25–60, Cu 6–20, Mo 1,0–5,0 ppm
22. [IntechOpen — Soybean Yield Responses to Micronutrient Fertilizers](https://www.intechopen.com/chapters/53893) — Referenz-Sufficiency-Ranges Cu 10–30, Zn 20–50, Mn 20–100, Mo ab 1 ppm (Blattgewebe zur Blüte)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
