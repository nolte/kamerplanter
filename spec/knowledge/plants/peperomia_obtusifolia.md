# Baby-Gummipflanze — Peperomia obtusifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Joy Us Garden](https://www.joyusgarden.com/peperomia-obtusifolia-care/), [Gardenia.net](https://www.gardenia.net/plant/peperomia-obtusifolia), [Lively Root](https://www.livelyroot.com/blogs/plant-care/baby-rubber-plant-care), [Houseplant Central](https://houseplantcentral.com/peperomia-obtusifolia-care/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Peperomia obtusifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Baby-Gummipflanze, Stumpfblättrige Peperomie; Baby Rubber Plant, American Rubber Plant | `species.common_names` |
| Familie | Piperaceae | `species.family` → `botanical_families.name` |
| Gattung | Peperomia | `species.genus` |
| Ordnung | Piperales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | 12 | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutrale Art, kein photoperiodischer Blühtrigger --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 12°C, optimal 18–28°C. Verträgt typische Zimmertemperaturen sehr gut. | `species.hardiness_detail` |
| Heimat | Karibik, Zentral- und Südamerika — epiphytisch an Bäumen in tropischen Wäldern | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Peperomia obtusifolia hat halbsukkulente, dickfleischige Blätter und Stängel, die Wasser speichern — ähnlich wie Sukkulenten. Deshalb verträgt sie Trockenheit viel besser als Staunässe. Sie gehört zur zweitgrößten Gattung der Bedecktsamer (über 1.500 Arten). Als epiphytische Pflanze ist das Substrat sekundär, solange Drainage gut ist. Nicht mit Ficus elastica (echter Gummibaum) verwechseln.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Photosynthese):** Die Gattung Peperomia ist als CAM- bzw. CAM-cycling-Pflanze (Crassulacean Acid Metabolism) dokumentiert. P. obtusifolia betreibt eine fakultative/abgeschwächte CAM-cycling-Form mit charakteristischem mehrschichtigem wasserspeicherndem Epidermisgewebe (multiple epidermis); das mittlere Palisadengewebe übernimmt C3-Aktivität, das Schwammparenchym CAM-typische nächtliche CO₂-Fixierung. Einstufung `cam` gemäß Katalogregel (wasserspeichernde, halbsukkulente Art). Quellen: Journal of Experimental Botany (facultative CAM review), PMC (CAM in *Peperomia camptotricha*).

**Hinweis (GDD-Basis):** Die GDD-Basistemperatur von 12 °C ist aus der belegten Wachstums-/Schadensschwelle abgeleitet (Wachstumsstillstand und Zellschäden unterhalb ~12 °C; optimaler Wuchsbereich 18–28 °C). Es handelt sich NICHT um einen Keim-Basiswert. Konsistent mit der Mindesttemperatur 12 °C in §1.1 (Winterhärte-Detail) und §4.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
<!-- Quelle: growing-phase-auditor 2026-07 -->
| Blütemonate | 4, 5, 6, 7, 8, 9, 10, 11, 12 (kleine, unauffällige, kolbenförmige Spadix-Blüten; ganzjährig außer Jan–Mär, Schwerpunkt Frühling/Sommer) | `species.bloom_months` |
<!-- /Quelle: growing-phase-auditor 2026-07 -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, cutting_leaf, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (5–8 cm) im Wasser bewurzeln oder direkt in feuchtem Perlite/Substrat. Blattstecklinge funktionieren gut: Blatt mit Stiel abschneiden, in feuchtes Substrat stecken. Bewurzelung bei 22–24°C in 3–6 Wochen. Sehr zuverlässig.

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

**Hinweis:** Peperomia obtusifolia ist NICHT giftig — ideal für Haushalte mit Kindern und Haustieren. ASPCA listet die Pflanze als ungiftig.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kein regelmäßiger Rückschnitt nötig. Überlange Triebe im Frühjahr kürzen. Verblühte Blütenstände entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–4 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, luftige Mischung: Einheitserde mit 30% Perlite oder Orchideen-Mix. pH 6.0–7.0. Niemals schwere, dichte Erde. Kleiner Topf optimal — Peperomien mögen es eng. | — |

---

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert in seriösen Quellen --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert in seriösen Quellen --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 8–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten für diese Zierpflanze --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten für diese Zierpflanze --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis (Standortqualität):** Als immergrüne Unterwuchs-/Epiphytenart (understory) toleriert P. obtusifolia mittlere bis schattige Lichtverhältnisse (`shade`), wächst dort aber deutlich langsamer; direkte Vollsonne führt zu Blattverbrennung. Die flache, faserige Wurzel (8–15 cm, passend zur empfohlenen Min-Topftiefe 10 cm in §1.6) ist staunässeempfindlich (`sensitive`) — Hauptverlustursache ist Wurzelfäule durch stehendes Wasser. Salzempfindlich (`sensitive`): Düngersalze verursachen Blattrand-/Wurzelverbrennung; jährliches Durchspülen (Leaching) des Substrats empfohlen. Der pH-Vorzug 6.0–6.5 (leicht sauer) ist quellenbelegt; die in §1.6/§2.3 genannte Kultur-Toleranzspanne 6.0–7.0 bleibt als breiterer tolerierter Bereich gültig, der Optimum-Vorzug liegt im sauren Teil.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 4–12 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 40–120 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 60 | 25 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (halbe Dosis, 3×/Saison) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |
| Guano-Dünger | Gardol | organisch | 2 g/L Gießwasser | Frühjahr bis Sommer |

### 3.2 Besondere Hinweise

Extrem leichter Zehrer. Nur 2–3 Düngergaben pro Saison (März–August) — immer mit halber Konzentration. Überdüngung führt zu Wurzelverbrennung und Blattverlust. Kein Dünger September bis Februar. Frisches Substrat beim Umtopfen versorgt die Pflanze für mehrere Monate ausreichend.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; zwischen Güssen gut abtrocknen lassen (halbsukkulente Blätter) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (September, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (min. 12) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; ggf. Pflanzenlampe bei <100 µmol/m²/s | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam, Substrat zwischen Güssen gut abtrocknen lassen (Intervall 14–21 Tage) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** P. obtusifolia ist nicht frosthart (zero frost tolerance) und muss frostfrei als Zimmerpflanze überwintern (`frost_free`). Schon unter ~12 °C drohen Zellschäden, unter 0 °C irreversibler Frosttod. Eine im Sommer auf Balkon/Terrasse stehende Pflanze rechtzeitig im September einräumen und erst nach den Eisheiligen (Mitte Mai) wieder ins Freie stellen. Keine Knolleneinlagerung — die Pflanze überwintert grün und aktiv-verlangsamt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Trauermücke | Bradysia spp. | Larven in Substrat, Adulte fliegend | easy |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, fauler Stamm | Überbewässerung, Staunässe |
| Cercospora-Blattflecken | fungal | Braune Flecken mit gelbem Hof | Nasses Laub, schlechte Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke (Adulte) |
| Nematoden (Steinernema feltiae) | biological | Gießen | 0 | Trauermücke (Larven) |
| Neemöl | biological | Sprühen 0.5% | 0 | Spinnmilbe, Schmierläuse |
| Substrat trockener halten | cultural | Gießintervall erhöhen | 0 | Trauermücke (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|----------------|--------------|------------------|
| Raubmilbe *Stratiolaelaps scimitus* (syn. *Hypoaspis miles*) | Trauermücke (*Bradysia* spp., Larven) | 100–500 Tiere/m² | 2–3 Wochen |
| Nematode *Steinernema feltiae* | Trauermücke (*Bradysia* spp., Larven) | 0.5 Mio./m² (Gießanwendung) | 1–2 Wochen |
| Australischer Marienkäfer *Cryptolaemus montrouzieri* | Schmierlaus (*Pseudococcus* spp.) | 1 Käfer / 2 Pflanzen (leichter Befall) bis 5–10/Pflanze (starker Befall) | 3–4 Wochen |
| Raubmilbe *Phytoseiulus persimilis* | Spinnmilbe (*Tetranychus urticae*) | 2–50 Tiere/m² (ab Erstbefall, ggf. 1–2× wöchentlich wiederholen) | 1–3 Wochen |

**Hinweis:** Nützlingseinsatz an Zimmerpflanzen ist bei vereinzeltem Befall meist Overkill — primär für Gewächshaus-/Bestandskultur oder bei stärkerem Befall sinnvoll. *Phytoseiulus persimilis* benötigt >60 % rel. Luftfeuchte und 20–27 °C, um Spinnmilben zuverlässig zu überholen. *Cryptolaemus* und *Phytoseiulus* sind temperatur- und feuchteabhängig; *Stratiolaelaps* und *Steinernema* wirken im Substrat gegen Trauermückenlarven und ergänzen die in §5.3 gelisteten Gelbtafeln (gegen Adulte). Nützling-Wirt-Zuordnung fachlich geprüft (keine Vermischung Schild-/Weichlaus).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Gerippte Peperomie | Peperomia caperata | Gleiche Gattung | Interessante Blattstruktur |
| Wassermelonen-Peperomie | Peperomia argyreia | Gleiche Gattung | Dekoratives Wassermelonenmuster |
| Hänge-Peperomie | Peperomia scandens | Gleiche Gattung | Hängend, für Ampeln |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Peperomia obtusifolia,"Baby-Gummipflanze;Stumpfblättrige Peperomie;Baby Rubber Plant",Piperaceae,Peperomia,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Karibik, Zentral- und Südamerika",yes,1-4,10,15-30,20-40,yes,limited,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Variegata,Peperomia obtusifolia,"ornamental;variegated;green_cream",clone
Gold Tip,Peperomia obtusifolia,"ornamental;variegated;yellow_green",clone
```

---

## Quellenverzeichnis

1. [Joy Us Garden — Peperomia obtusifolia](https://www.joyusgarden.com/peperomia-obtusifolia-care/) — Pflegehinweise, Düngung
2. [Gardenia.net — Peperomia obtusifolia](https://www.gardenia.net/plant/peperomia-obtusifolia) — Botanische Daten
3. [Lively Root — Baby Rubber Plant](https://www.livelyroot.com/blogs/plant-care/baby-rubber-plant-care) — Kulturdaten
4. [Houseplant Central](https://houseplantcentral.com/peperomia-obtusifolia-care/) — Ganzjahrespflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Journal of Experimental Botany — Facultative crassulacean acid metabolism (CAM) plants](https://academic.oup.com/jxb/article/65/13/3425/2877513) — CAM/fakultative CAM in Piperaceae (Photosynthese-Typ)
7. [PMC — Crassulacean Acid Metabolism and CAM Modifications in *Peperomia camptotricha*](https://pmc.ncbi.nlm.nih.gov/articles/PMC1064456/) — CAM-cycling, mehrschichtige Epidermis, Gewebe-Arbeitsteilung in Peperomia
8. [Clemson HGIC — Peperomia Indoor Plant Care](https://hgic.clemson.edu/factsheet/peperomia-peperomia-spp-indoor-plant-care-and-growing-guide/) — Schattentoleranz, Düngung, Salzempfindlichkeit (University Extension)
9. [Almanac — How to Grow Peperomia](https://www.almanac.com/plant/how-grow-peperomia-plants-colorful-easy-care-houseplants-every-space) — Salzaufbau/Leaching, Düngung
10. [Gardener's Supply — How to Care for Peperomia](https://www.gardeners.com/blogs/houseplant-encyclopedia/peperomia-care-9694) — pH-Vorzug 6.0–6.6, gut drainierendes Substrat
11. [Bloomsprouts — Soil for Peperomia](https://bloomsprouts.com/soil-for-peperomia/) — pH 6.0–6.5, Wurzelraum, Staunässe/Wurzelfäule
12. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Spinnmilben-Raubmilbe
13. [Cornell NYSIPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Etablierung/Ausbringung (University)
14. [ARBICO Organics — Stratiolaelaps scimitus (Hypoaspis miles)](https://www.arbico-organics.com/product/fungus-gnat-predator-stratiolaelaps-scimitus-hypoaspis-miles/beneficial-insects-predators-parasites) — Trauermücken-Raubmilbe Ausbringrate
15. [Anatis Bioprotection — Stratiolaelaps scimitus](https://anatisbioprotection.com/en/produit/stratiolaelaps-scimitus/) — Ausbringrate 100–500/m² gegen Trauermückenlarven
16. [peperomiaobtusifolia.com — Temperature Tolerance](https://peperomiaobtusifolia.com/blog/peperomia-obtusifolia-temperature-tolerance/) — Mindesttemperatur/Frostempfindlichkeit (Überwinterung)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
17. [gartenjournal.net — Zwergpfeffer](https://www.gartenjournal.net/zwergpfeffer) — Blütezeit April–Dezember, Vermehrung, Frostempfindlichkeit
18. [Plantura — Peperomia obtusifolia](https://www.plantura.garden/zimmerpflanzen/peperomia/peperomia-obtusifolia) — Blütezeit April–Dezember, Lebenszyklus (mehrjährig), Dormanz (keine ausgesprochene Ruhephase), Vermehrung (Kopfstecklinge)
19. [gardify.de — Fleischige Peperomie](https://gardify.de/pflanze/1058/Fleischige-Peperomie) — Blütezeit April–Dezember, Frostempfindlichkeit (Z10, <15°C), Wuchsform immergrün
20. [Missouri Botanical Garden — Plant Finder: Peperomia obtusifolia](http://www.missouribotanicalgarden.org/plantfinder/PlantFinderDetails.aspx?taxonid=285088) — Seasonal bloomer, USDA-Zonen 10–12, evergreen, Stecklings-/Blattvermehrung (University-Quelle)
21. [Planet Natural — Peperomia Obtusifolia Care Guide](https://www.planetnatural.com/peperomia-obtusifolia/) — Keine formale Dormanzphase, Frostempfindlichkeit <12.7°C, Stecklings-/Blattvermehrung
22. [The Sill — Peperomia obtusifolia Care Guide](https://www.thesill.com/blogs/plants-101/how-to-care-for-baby-rubber-plant-peperomia-obtusifolia) — Lebenszyklus (perennial), Vermehrung (Stecklinge, Blatt, Wasser)
23. [beetfreunde.de — Fleischige Peperomie/Zwergpfeffer](https://www.beetfreunde.de/magazin/fleischige-peperomie-zwergpfeffer/) — Vermehrung (Blatt-/Kopfstecklinge)
24. [peperomiaobtusifolia.com — Dividing Peperomia Obtusifolia](https://peperomiaobtusifolia.com/blog/divide-peperomia-obtusifolia-guide/) — Teilung (division) als Vermehrungsmethode
<!-- /Quelle: growing-phase-auditor 2026-07 -->
