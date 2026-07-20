# Dahlie Armateras — Dahlia pinnata 'Armateras'

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:**
> - [dutch-bulbs.com — Dahlie Armateras Produktseite](https://dutch-bulbs.com/de/dahlie-armateras/)
> - [BULBi UK — Armateras Cultivar Details](https://bulbi.co.uk/armateras-z40374-config)
> - [American Dahlia Society — Nutrients for Dahlias](https://www.dahlia.org/docsinfo/articles/nutrients-for-dahlias/)
> - [Swan Island Dahlias — Fertilizing Tips](https://www.dahlias.com/blog/growing-tips/dahlia-fertilizing-tips/)
> - [ASPCA — Toxic and Non-Toxic Plants: Dahlia](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dahlia)
> - [UC IPM — Managing Pests in Gardens: Dahlia](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html)
> - [RHS — How to grow dahlias](https://www.rhs.org.uk/plants/dahlia/growing-guide)
> - [Old Farmer's Almanac — Dahlias: How to Plant, Grow, and Care](https://www.almanac.com/plant/dahlias)
> - [Floret Flowers — How to Grow Dahlias](https://www.floretflowers.com/resources/how-to-grow-dahlias/)
> - [Gardeners Path — Dahlia Companion Plants](https://gardenerspath.com/plants/flowers/dahlia-companion-plants/)
> - [Gardening Know How — Dahlia Pests and Diseases](https://www.gardeningknowhow.com/ornamental/bulbs/dahlia/dahlia-pests-and-diseases.htm)
> - [Overwintering Dahlias — Flourish Flower Farm](https://www.flourishflowerfarm.com/blog/overwintering-dahlias)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

**Hinweis zu Taxonomie und Sortenname:** "Armateras" ist eine eingetragene Sorte (Cultivar) der Garten-Dahlie, gezüchtet von A.C. Koot, Niederlande (2012). Der korrekte botanische Name der Elternart ist *Dahlia pinnata* Cav. (Synonym: *Dahlia variabilis* Willd.). In der Handelspraxis und bei Züchtern wird häufig *Dahlia x hybrida* verwendet, da moderne Gartenformen vielfache interspezifische Hybriden darstellen. Der blütendekorative Typ "Dekorative Dahlie" entspricht der ADS-Klassifikation "Decorative".

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name (Art) | Dahlia pinnata | `species.scientific_name` |
| Sortenname (Cultivar) | Armateras | `cultivar.name` |
| Synonyme | Dahlia x hybrida, Dahlia variabilis | `species.scientific_name` (Hinweis) |
| Volksnamen (DE/EN) | Dahlie Armateras, Garten-Dahlie; Dahlia Armateras, Garden Dahlia | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Dahlia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | `bulb_geophyte` (krautartig, aus Knollenwurzel austreibend) <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher herb) --> | `species.growth_habit` |
| Wurzeltyp | `tuberous` (Knollenwurzeln als Speicherorgane, die winterlich ausgegraben werden) | `species.root_type` |
| Lebenszyklus | `perennial` (botanisch mehrjährig durch Knollen; in Mitteleuropa kulturell als Sommerblüher behandelt — Knollen müssen frostfrei überwintert werden) | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | `short_day` (fakultativ; Blüteninitiierung bei Nachtlänge > 12 h gefördert, Dahlien blühen jedoch auch unter Langtagbedingungen; Tuberisierung eindeutig kurztaggesteuert bei Nacht > 12 h) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen (Freiland ganzjährig) | 8b, 9a, 9b, 10a, 10b, 11a, 11b (Knollen überwintern im Boden) | `species.hardiness_zones` |
| USDA Zonen (Sommerblüher, Knollen ausgraben) | 5a–8a (Mitteleuropa-Standard: Knollen im Herbst ausgraben und frostfrei einlagern) | — Hinweis |
| Frostempfindlichkeit | `tender` (Knollen sterben bei Bodenfrost; oberirdische Teile bereits bei leichtem Frost -1 °C) | `species.frost_sensitivity` |
| Winterhärte-Detail | Oberirdische Triebe sterben ab -1 °C. Knollen überstehen im Boden nur in Zone 8b+ (milte Winter ohne Dauerfrost). In Mitteleuropa (Zone 6–7): Knollen im Oktober ausgraben, bei 4–8 °C frostfrei und dunkel einlagern. | `species.hardiness_detail` |
| Heimat (Elternart) | Mexiko, Mittelamerika, Hochlagen der Kordilleren | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral — keine belegten allelopathischen Wirkungen bei Dahlia pinnata) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | `heavy_feeder` (Starkzehrer — Blütendurchmesser 12–15 cm erfordert intensive P/K-Versorgung; N-Überschuss hemmt Blüte massiv) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | `['ornamental', 'bee_friendly']` (wichtige Bienenweide im Hochsommer; ornamental als Schnittblume und Beetpflanze) | `species.traits` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | `c3` (krautige Staude der Asteraceae; kein C4-/CAM-Stoffwechsel — Standardweg für nahezu alle Zierstauden) | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 (Wuchs-GDD-Basis der Hauptwuchsphase; wärmeliebende Art mexikanischer Herkunft, Auspflanzen erst bei Bodentemperatur ≥ 15 °C, aktives Wachstum 21–27 °C — konventionelle Warm-Season-Basis; **kein artspezifischer Phänologie-Basiswert publiziert**, Wert folgt der agronomischen Warm-Season-Konvention 10 °C) | `species.base_temp` |
| Lebensdauer (Jahre) | viele Jahre / klonal quasi unbegrenzt durch jährliche Knollenteilung; einzelne Mutterknolle nur 1–2 Jahre produktiv, Sorte überdauert durch Teilung Jahrzehnte | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (Knollen durchlaufen jährlich eine Ruheperiode/Dormanz vor Wiederaustrieb; im Winterlager keine Belichtung, kaum Feuchte nötig) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tropisch-subtropische Herkunft; KEIN Kältebedarf für Blühinduktion — Dormanz wird durch Kälte erzwungen, nicht physiologisch benötigt) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (entfällt, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 12 (bezieht sich auf die Tuberisierung/Knollenbildung: Photoperiode ≤ 10–12 h fördert Knollenansatz, > 16 h hemmt ihn; Blüteninitiierung ist tagneutral bis fakultativ-kurztägig und nicht obligat photoperiodisch) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Sortenspezifische Merkmale (Cultivar Armateras):**

| Merkmal | Wert |
|---------|------|
| Blütentyp | Dekorativ (Decorative) — vollgefüllte, symmetrisch angeordnete Blütenblätter |
| Blütenfarbe | Kräftiges Pink mit gelbem Zentrum, das langsam zu Creme verblasst |
| Blütendurchmesser | 12–15 cm |
| Wuchshöhe | 90–110 cm |
| Züchter | A.C. Koot (Niederlande) |
| Züchtungsjahr | 2012 |
| Verwendung | Beet, Schnittblume, Kübel (mit min. 20 L) |

### 1.2 Aussaat- & Erntezeiten

Mitteleuropa (Zone 6–7), Bezugspunkt: letzter Frost Mitte April bis Mitte Mai (je nach Region).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Knollen ab März in Töpfen vorkeimen, dann nach letztem Frost auspflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktpflanzung nach letztem Frost (Tage) | 0 (direkt nach letztem Frost, wenn Boden auf 10 °C erwärmt) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5 (Mai — nach letztem Frost direkt ins Freiland) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9, 10 (Schnittblumen-Ernte Juli bis Frost; Knollen-Ernte Oktober nach dem ersten Frost) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 (Juli bis erster Herbstfrost; Dauerspitzblüher) | `species.bloom_months` |

**Hinweis Vorziehen:** Knollen können ab Ende Februar/März in flachen Kästen mit Kokoserde im Gewächshaus oder hellen Fensterplatz vorgetrieben werden. Sobald Triebe 5–10 cm zeigen, in endgültige Töpfe oder nach dem letzten Frost ins Beet setzen.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | `cutting_stem` (Stecklinge vom Vorgetriebenen — einfachste Methode für rasante Vermehrung), `division` (Knollenteilung beim Auspflanzen), `seed` (aus Samen möglich, aber Sorteneigenschaften nicht erhalten — nur Artmerkmale) | `species.propagation_methods` |
| Schwierigkeit | `easy` (Stecklinge und Teilung sind auch für Einsteiger sehr zuverlässig) | `species.propagation_difficulty` |

**Knollenteilung (Division):**
- Zeitpunkt: Frühjahr beim Vorkeimen (März/April)
- Jedes Knollenstück muss mindestens ein gut erkennbares "Auge" (Triebknospe) tragen
- Schnittstellen mit Holzkohlepulver oder Pflanzenkohle behandeln, um Fäulnis zu verhindern
- Geteilte Knollen 24 h trocknen lassen vor dem Einpflanzen

**Stecklinge:**
- Von vorgetriebenen Knollen: Triebe bei 10–15 cm Länge abschneiden
- In feuchtes Perlite oder Kokoserde stecken, bei 18–22 °C und hoher Luftfeuchte
- Bewurzelung nach 2–3 Wochen

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (mild) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (mild) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (Dahlia sind für Menschen als sicher eingestuft; Blüten sogar essbar) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Pflanzenteile (Blätter, Stängel, Knollen) für Hunde und Katzen mild giftig; Knollen haben höchste Konzentration | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Phototoxische Polyacetylen-Verbindungen (ungenau identifiziert laut ASPCA); können Hautirritation bei Lichtexposition auslösen | `species.toxicity.toxic_compounds` |
| Schweregrad | `mild` (milde gastrointestinale Symptome: Speichelfluss, Erbrechen, Durchfall; Dermatitis bei Hautkontakt möglich) | `species.toxicity.severity` |
| Kontaktallergen | true (phototoxische Polyacetylene können bei empfindlichen Personen Kontaktdermatitis auslösen, besonders beim Knollen-Handling) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Insektenbestäubung, Pollen nicht windgetragen) | `species.allergen_info.pollen_allergen` |

Quellen: ASPCA Toxic and Non-Toxic Plants (Dahlia — toxic to dogs and cats), Wag Walking (mild GI symptoms).

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | `after_harvest` (laufendes Ausputzen verblühter Blüten verlängert Blütezeit erheblich; "Deadheading" ist zentrale Pflegemaßnahme; kein formaler Winterschnitt — Stängel werden beim Ausgraben der Knollen auf 10–15 cm zurückgeschnitten) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8, 9, 10 (kontinuierliches Deadheading von Juli bis Frost) | `species.pruning_months` |

**Wichtige Pflegeschnitte:**
- **Entspitzen (Pinching):** Bei 30–40 cm Wuchshöhe Haupttrieb über dem 3. Blattpaar einkürzen — fördert buschigen Wuchs und mehr Blütenstiele. Zeitpunkt: ca. 4–5 Wochen nach Auspflanzen.
- **Deadheading (Verblühtes entfernen):** Blüten nach dem Verblühen bis zum nächsten Blattpaar zurückschneiden. Verhindert Samenbildung, fördert Neuaustrieb.
- **Abtriebsschnitt im Herbst:** Nach dem ersten Frost Stängel auf 10–15 cm zurückschneiden, bevor Knollen ausgegraben werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | `yes` (für Armateras mit 90–110 cm Wuchshöhe: Kübel min. 20 L, besser 30 L empfohlen) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 (Knollen brauchen Tiefe, kein Staunässe-Risiko) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 90–110 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–70 (Reihenabstand mind. 60 cm für ausreichende Luftzirkulation) | `species.spacing_cm` |
| Indoor-Anbau | `no` (braucht Vollsonne; Indoor nur zur Vorkultur im Frühjahr) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | `yes` (windgeschützter, vollsonniger Balkon; große Kübel min. 20 L; Gießhäufigkeit erhöht sich stark) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (kein Gewächshaus nötig; nur für Vorkultur im Frühjahr nützlich) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (bei 90–110 cm Wuchshöhe und dekorativen Blüten: Bambusstäbe oder Pflanzstäbe dringend empfohlen; ohne Stütze knicken Stängel bei Wind und Regen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, nährstoffreiche Kübelpflanzenerde mit 20–30 % Perlite-Anteil; pH 6.0–7.0; kein Staunässerisiko — Ablaufloch zwingend | — |
| Substrat-Empfehlung (Freiland) | Lockerer, humusreicher, gut durchlässiger Gartenboden; pH 6.0–7.0; schwere Tonböden mit Sand und Kompost verbessern | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 20 (sonnenadaptierte C3-Pflanze; Netto-Photosynthese = 0; **kein dahlienspezifischer Messwert publiziert** — Spanne aus C3-Sonnenpflanzen-Literatur, höhere Atmung als Schattenpflanzen) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 40 (oberes Ende für sonnenadaptierte C3-Blätter bei warmen Temperaturen; steigt mit Temperatur durch höhere Atmung) | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | `full_sun` (RHS: „warm, sheltered, sunny spot"; Floret: mind. 6 h direkte Sonne täglich; in Vollschatten kein Gedeihen, in Halbschatten vergeilt und blüht spärlich) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–45 (flaches Feeder-Wurzelsystem dicht unter der Oberfläche; Wurzeln strahlen bis ~45 cm seitlich aus, Knollen 10–15 cm tief) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | `sensitive` (RHS: „may rot in waterlogged soil"; Knollen faulen bei stehender Nässe — free-draining zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | `sensitive` (Glycophyt; Zierpflanze ohne Salztoleranz, reagiert mit Blattrand-Nekrosen und Wuchsdepression auf Salzstress) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> (kein artspezifischer Maas-Hoffman-Schwellenwert a für Dahlia publiziert; qualitativ in die salzempfindliche Klasse <2 dS/m Substrat-ECe einzuordnen, aber kein belegter Zahlenwert) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> (kein Maas-Hoffman-Slope b für Dahlia publiziert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.5–7.0 (optimaler Vorzug leicht sauer bis neutral; liegt innerhalb der im Dokument genannten tolerierten Spanne 6.0–7.0 in §1.6/§2.3 — Vorzug ⊂ Toleranz, kein Widerspruch) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
### 1.8 Saatgut & Keimung (Seed Profile)

<!-- SECTION MISSING: seed_profile — vegetativ vermehrt (Dahlia 'Armateras' ist eine benannte Cultivar-Sorte; §1.3 dokumentiert Stecklinge und Knollenteilung als Standardvermehrung. Der Praxis-Hinweis in §1.3 stellt explizit fest, dass Samenvermehrung "Sorteneigenschaften nicht erhalten" kann — nur die botanischen Artmerkmale, nicht die Cultivar-Identität "Armateras". Eine echte Aussaat-/Keim-Metadatenerhebung für diese benannte Sorte wäre daher irreführend und unterbleibt.) -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

Dahlien aus Knollen durchlaufen jährlich einen klar abgegrenzten Zyklus von der Knollen-Aktivierung bis zur Knollen-Einlagerung. Als Sommerblüher in Mitteleuropa gibt es keine klassische "Keimphase" bei Direktsaat — stattdessen treibt die Knolle aus.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Knollenaustreibung | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum | 28–42 | 2 | false | false | medium |
| Knospenbildung | 14–21 | 3 | false | false | medium |
| Blüte | 56–84 | 4 | false | true | high |
| Seneszenz & Knollenreife | 21–30 | 5 | true | true | medium |

**Gesamtzyklus Mitteleuropa:** ca. 140–200 Tage (Mai bis Oktober/November)

### 2.2 Phasen-Anforderungsprofile

#### Phase: Knollenaustreibung (ca. Mitte April – Mitte Mai)

Knolle treibt nach dem Auspflanzen aus. Kein Gießen bis erste Triebe sichtbar — Fäulnisgefahr.

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 (Freiland/Vorkultur heller Platz) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (natürliches Tageslicht Mai) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 (kein Frost!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 (kritischer Punkt stomatären Kollaps, deutlich oberhalb des Zielkorridors; feuchteliebende Austriebsphase → niedrigere Schwelle als spätere Phasen) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | `medium` (C3-Staude mit normalem stomatärem Regelverhalten; weiches Jungtriebgewebe reagiert empfindlich auf Trockenstress) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 (C3-Optimum der Netto-CO₂-Assimilation) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland-Vollsonne; Zhen & Bugbee: direkte Solarstrahlung ≈ 0.46–0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 (Freiland-Ambientwert) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 0 (NICHT gießen bis Austrieb sichtbar!) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 (erst nach erstem Triebdurchbruch minimal gießen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetatives Wachstum (ca. Mai – Juni)

Intensive Wachstumsphase, Laubaufbau. Entspitzen (Pinching) bei 30–40 cm.

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–900 (Vollsonne bevorzugt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (natürliches Tageslicht Juni) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ~0.4 kPa; stomatärer Kollaps bei kräftigem Laubaufbau) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | `medium` (C3-Staude; üppiges weiches Laub bei guter N-Versorgung trockenstressempfindlich) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 (C3-Optimum der Netto-CO₂-Assimilation) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland-Vollsonne; Zhen & Bugbee ≈ 0.46–0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (nach Bedarf; Fingertest: obere 5 cm trocken = gießen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 (je nach Topfgröße/Freiland) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Knospenbildung (ca. Juni – Juli)

Knospenansatz, wichtige Phase für Blütenqualität. Erster Düngereinsatz mit Fokus auf P und K.

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.9–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (oberer Zielwert + ~0.4 kPa; etabliertes Gewebe toleriert höhere Schwelle) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | `medium` (C3-Staude; stabile Knospenphase, aber Trockenstress mindert Knospenqualität) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 (C3-Optimum der Netto-CO₂-Assimilation) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland-Vollsonne; Zhen & Bugbee ≈ 0.46–0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (Wasserbedarf steigt durch Knospenentwicklung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 750–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (ca. Juli – Oktober)

Hauptblühzeit mit kontinuierlichem Deadheading. Höchster Wasserverbrauch. Regelmäßige Schnittblumen-Ernte möglich.

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 (natürliches Tageslicht Juli bis Oktober) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 (zu hohe Luftfeuchte fördert Botrytis in Blüten!) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 (oberer Zielwert + ~0.4 kPa; höchste Toleranzschwelle der Vollblühphase, darüber stomatärer Kollaps und Blüten-/Knospenabwurf) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | `medium` (C3-Staude; bei extremer Hitze/Trockenheit Blütenschäden, aber kein CAM-Schutzmechanismus) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 (C3-Optimum der Netto-CO₂-Assimilation) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland-Vollsonne; Zhen & Bugbee ≈ 0.46–0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–3 (heiße Sommertage: täglich; Daumen-/Fingertest entscheidend) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 (stark abhängig von Temperatur und Topfgröße) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Seneszenz & Knollenreife (Oktober – November, nach erstem Frost)

Pflanze zieht nach erstem Frost ein. Knollen weiter reifen lassen, dann ausgraben. Einlagerung für Winter.

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 (Tageslicht reduziert sich natürlich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 9–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 8–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 0–10 (kurzzeitiger leichter Frost ok für Reifung, Dauerfrost schädigt Knollen) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | null (nicht anwendbar — Knollen ohne aktiven Gaswechsel; kein Steuerungsparameter) | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | null (nicht anwendbar — Pflanze zieht ein, kein aktiver stomatärer Gaswechsel mehr) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | `low` (einziehende/seneszente Pflanze; physiologische Aktivität minimal, Trockenheit sogar erwünscht für Knollenreife) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 (C3-Optimum, nur für verbleibendes aktives Restlaub relevant) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland-Vollsonne; Zhen & Bugbee ≈ 0.46–0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (stark reduziert; Knollenreifung wird durch Trockenheit gefördert) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Knollenaustreibung | 0:0:0 (kein Dünger — Knolle hat ausreichend Reserven) | 0.0 | 6.0–7.0 | — | — | — | — |
| Vegetatives Wachstum | 1:1:1 bis 2:1:1 (leicht N-betont für Blattaufbau) | 0.8–1.2 | 6.0–7.0 | 80–120 | 30–50 | — | — |
| Knospenbildung | 1:2:2 (P und K für Knospenansatz und Stängelstärke) | 1.0–1.4 | 6.0–7.0 | 100–150 | 40–60 | — | — |
| Blüte | 1:3:3 bis 0:2:3 (N minimal, viel P und K für Blütenqualität und Knollenaufbau) | 0.8–1.2 | 6.0–7.0 | 80–120 | 30–50 | — | — |
| Seneszenz & Knollenreife | 0:0:0 (kein Dünger — Reifung ohne zusätzliche Nährstoffe) | 0.0 | 6.0–7.0 | — | — | — | — |

**Wichtigster Grundsatz:** Zu viel Stickstoff (N) ist der häufigste Düngungsfehler bei Dahlien. Übermäßiges N führt zu üppigem, weichem Laub, schwachen Stängeln, wenigen oder gar keinen Blüten und schlecht gelagerten Knollen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (Mn/Zn/Cu/Mo):**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Knollenaustreibung | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Vegetatives Wachstum | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Knospenbildung | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Seneszenz & Knollenreife | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

Hinweis: Für *Dahlia pinnata* sind keine art- bzw. phasenspezifischen Sollwerte (ppm) für Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) in seriösen Quellen (Extension/peer-reviewed) publiziert. Die Mikronährstoffversorgung erfolgt in der Praxis über ausgewogene Volldünger/organische Grunddüngung; daher hier `<!-- DATEN FEHLEN -->` statt erfundener Zahlenwerte (KA-Felder `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/Bedingung | Bedingungen |
|------------|---------|----------|-------------|
| Knollenaustreibung → Vegetatives Wachstum | time_based | 14–28 Tage | Erste grüne Triebe 5–10 cm über Boden sichtbar |
| Vegetatives Wachstum → Knospenbildung | event_based | 28–42 Tage | Erste Knospenanlagen sichtbar (Blütenstiele mit kleinen Knospen) |
| Knospenbildung → Blüte | event_based | 14–21 Tage | Erste Blüte öffnet sich |
| Blüte → Seneszenz & Knollenreife | event_based | nach erstem Frost | Erste Fröste schwärzen Laub; Stängel auf 10–15 cm kürzen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

**Grundprinzip für Dahlien:** Niedrig-Stickstoff-Düngung ist entscheidend. NPK-Verhältnis sollte N stets deutlich unter P und K halten. Zu viel N = viel Laub, kaum Blüten.

#### Mineralisch (Kübel/Gartenboden)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen | Hinweis |
|---------|-------|-----|-----|-----------|--------|---------|
| Blaukorn / Nitrophoska Classic | Compo / BASF | Granulat | 12-12-17+2 | 20–30 g/m² (einmalig beim Pflanzen einarbeiten) | Vegetativ | Einmalige Grunddüngung — danach auf Low-N umstellen |
| Blühpflanzen-Dünger flüssig | Compo Sana / Substral | Flüssig | 5-6-7 oder ähnlich | 5 ml/L alle 2 Wochen | Knospe, Blüte | Fertig-Produkt für Einsteiger |
| Hakaphos Blau (Blühpflanzendünger) | Compo Expert | Wasserlöslich | 5-15-30 | 1–2 g/L alle 14 Tage | Knospe, Blüte | Professioneller P/K-Booster für starke Blüte |
| Tomaten-/Fruchtdünger | Compo / Manna | Flüssig | ~4-6-8 bis 3-9-6 | 5–10 ml/L alle 2 Wochen | Knospe, Blüte | Gute Alternative — niedrig-N mit mehr P/K |

#### Organisch (Outdoor/Freiland/Beet)

| Produkt | Marke | Typ | Ausbringrate | Zeitpunkt | Geeignet für |
|---------|-------|-----|-------------|-----------|-------------|
| Hornspäne (langsam löslich) | Oscorna / Hauert / alle Marken | Organisch, N-Lieferant | 50–70 g/m² | Frühjahr beim Pflanzen einarbeiten | Vegetativphase (langsame N-Freisetzung) |
| Kompost (reif) | eigen / Gartencenter | Bodenverbesserer + Nährstoffe | 3–4 L/m² | Herbst/Frühjahr einarbeiten | Grunddüngung für alle Phasen |
| Schafwollpellets | diverse | Organisch, N+K | 100–150 g/m² | Frühjahr einarbeiten | Vegetativ; langsame Freisetzung über Saison |
| Beinwelljauche (Symphytum officinale) | selbst herstellen (1:20 verdünnt) | Organisch, K-betont | 1:20 verdünnt, alle 2 Wochen | ab Knospenbildung | Blüte/Knospe; Kaliumreich, perfekt für Dahlien |
| Algendünger flüssig | Algofeed / Neudorff Algoflor | Organisch-flüssig | 10–20 ml/L alle 2 Wochen | Knospe, Blüte | Ausgewogen, Spurenelemente, bioaktive Substanzen |

### 3.2 Düngungsplan (Freiland-Organisch)

| Zeitraum | Phase | Maßnahme | Produkt | Menge | Hinweise |
|---------|-------|----------|---------|-------|----------|
| Frühjahr (April/Mai) | Boden vorbereiten | Einarbeiten | Reifkompost | 3–4 L/m² | Vor dem Pflanzen 20 cm tief einarbeiten |
| Frühjahr (April/Mai) | Boden vorbereiten | Einarbeiten | Hornspäne | 50–70 g/m² | Mit Kompost gemeinsam einarbeiten |
| Mai–Juni | Vegetatives Wachstum | 1. Düngung | Balanced liquid (z.B. Algendünger) | Wie Etikett | Erst wenn Triebe 15–20 cm — nicht vor Etablierung |
| Juni–Juli | Knospenbildung | Umstellen auf Low-N | Beinwelljauche oder Tomatendünger | 1:20 verdünnt alle 2 Wo | N-betonten Dünger jetzt EINSTELLEN |
| Juli–Oktober | Blüte | P/K-Düngung | Beinwelljauche oder Hakaphos Blau | 1:20 / 1–2 g/L alle 2 Wo | Kontinuierlich bis Ende September |
| Oktober | Seneszenz | Düngung einstellen | — | — | Keine Düngung — Knollenreifung |

### 3.3 Mischungsreihenfolge (Freiland / flüssige Anwendung)

Für Dahlien im Freiland wird typischerweise keine komplexe Hydro-Mischsequenz benötigt. Bei Einsatz mehrerer flüssiger Produkte gilt:

1. Wasser in Gießkanne/Tank
2. Flüssige organische Grunddünger (z.B. Algendünger)
3. Jauchen/Brühen (Beinwelljauche)
4. pH prüfen (Ziel 6.0–7.0 für Freiland; bei normalem Gartenboden meist nicht nötig)

**Nie direkt mischen:** Beinwelljauche nicht unverdünnt — immer 1:20 mit Wasser verdünnen.

### 3.4 Besondere Hinweise zur Düngung

**Der größte Fehler: Zu viel Stickstoff.** Hochstickstoffige Rasendünger oder Allzweckdünger mit hohem N-Anteil fördern weiches Laub, schwache Stängel und verhindert Blütenbildung. Dahlia-Knollen liefern beim Austrieb bereits ausreichend N-Reserven.

**EC-Zielwerte (Topfkultur):** Bei Dahlien im Kübel maximal EC 1.4 mS — über 1.6 mS können Wachstumshemmungen auftreten. Grundsätzlich gilt: lieber zu wenig als zu viel.

**Kübel vs. Freiland:** Im Kübel ist regelmäßigere Flüssigdüngung nötig, da Nährstoffe schneller ausgewaschen werden. Im Freiland reichen organische Grunddüngung + Jauche.

**Knollenqualität für nächstes Jahr:** Gute Knollenbildung (für die Überwinterung und das nächste Jahr) erfordert ab August eine klare Reduzierung von N und Beibehaltung von K. Unterernährte Knollen überwintern schlecht.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `custom` (Dahlien haben einen sehr spezifischen Jahreszyklus mit Einlagerungsphase, der keinem der Standard-Presets entspricht; outdoor_annual_veg am nächsten) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–3 (etablierte Pflanzen im Hochsommer; Kübel oft täglich) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (Dahlien werden im Winter eingelagert — kein Gießen der eingelagerten Knollen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | `top_water` (von oben, gleichmäßig; Blätter nicht benetzen, Botrytis-Risiko) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | null (normales Leitungswasser ist geeignet; Regenwasser bevorzugt für Kübel) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 (alle 2 Wochen flüssige Nachbefruchtung ab Knospenphase) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 6, 7, 8, 9 (Juni bis September; kein Dünger in Austreibungs- und Seneszenzphase) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (frisches Substrat jedes Frühjahr beim Wiedereinpflanzen der Knollen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wöchentliche Sichtprüfung während der Saison; besonders auf Blattläuse und Spinnmilben) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Freilandpflanze; Luftfeuchte für Botrytis-Prävention indirekt relevant — Abstand einhalten, Blätter trocken halten) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Knollen kontrollieren | Eingelagerte Knollen auf Fäulnis/Austrocknung prüfen; bei Fäulnis befallene Stellen herausschneiden, Wunde mit Holzkohle behandeln | hoch |
| Feb | Planung | Saatgutbestellung, Pflanzenplanung, Standortwahl; erste Stecklinge von vorgetriebenen Knollen möglich (Frühbeet/Gewächshaus) | niedrig |
| Mär | Knollen vorkeimen | Knollen in flache Schalen mit leicht feuchter Erde flach einlegen, bei 15–18 °C im Hellen antreiben | mittel |
| Apr | Vorkeimen / Pikieren | Vorgekeimte Knollen in 3–5 L Töpfe umsetzen; Stecklinge von Trieben schneiden und bewurzeln; KEIN Frost mehr ab Ende April! | hoch |
| Mai | Auspflanzen | Nach letztem Frost (Zone 7: ca. 15. Mai) ins Beet oder endgültige Kübel setzen; Stützen einschlagen; nicht gießen bis Trieb sichtbar (Freiland) | hoch |
| Mai/Jun | Entspitzen (Pinching) | Bei 30–40 cm Wuchshöhe Haupttrieb über dem 3. Blattpaar einkürzen — fördert buschigen Wuchs mit mehr Blütenstielen | hoch |
| Jun | Vegetativpflege | Regelmäßig gießen; erste leichte Düngung; Stützen aufbinden; Schädlingskontrolle | mittel |
| Jul | Knospen- und Blütenpflege | Deadheading beginnen; auf Blattläuse und Spinnmilben achten; P/K-Düngung; regelmäßig gießen | hoch |
| Aug | Blütenhauptpflege | Wöchentliches Deadheading; Schnittstecklinge möglich für schnelle Blüte; Bewässerung in Hitze erhöhen | hoch |
| Sep | Blütenpflege | Weiter Deadheading; N-Düngung einstellen; Knollenaufbau durch K-Düngung fördern | mittel |
| Okt | Knollen ausgraben | Nach ersten Frost (schwarz-braune Blätter) Stängel auf 10–15 cm kürzen; Knollen vorsichtig ausgraben; 5–7 Tage trocknen | hoch |
| Nov | Einlagern | Getrocknete Knollen in Kisten mit leicht feuchtem Torf, Kokoserde oder Zeitungspapier einlagern; 4–8 °C, dunkel, frostfrei | hoch |
| Dez | Winterlagerung | Knollen kontrollieren; bei zu trockener Lagerung leicht anfeuchten; auf Mäusebefall achten | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | `dig_and_store` (Knollen müssen ausgegraben und frostfrei gelagert werden — zwingend für Mitteleuropa Zone 5–8a) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | `dig_store` (Ausgraben + trocknen + kühle Lagerung) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober — nach erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | `replant` (Knollen im März vorkeimen, ab Mai auspflanzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 (Vorkeimen März), 5 (Auspflanzen Mai) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 4 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | `dark` (kein Licht nötig und gewünscht während Ruheperiode) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | `none` (Knollen werden NICHT gegossen — nur Lagersubstrat leicht feucht halten, ca. 70–85 % relative Feuchte) | `overwintering_profiles.winter_watering` |

**Ausgrabe-Protokoll (Knollen-Zyklus):**

1. Nach ersten Frost (Laub schwarz/braun) warten — 1–2 Tage stehen lassen für ersten Kälteimpuls
2. Stängel auf 10–15 cm zurückschneiden
3. Klumpen vorsichtig mit Grabegabel (nicht Spaten!) lockern und herausheben
4. Erde abschütteln, NICHT abwaschen
5. 5–7 Tage kopfüber oder liegend bei 15–18 °C trocknen
6. Beschriftung mit wasserfestem Marker direkt auf Stängel (Sortenname!)
7. Einlegen in Kisten mit leicht feuchtem Vermiculite, Torf oder Kokoserde; kein feuchtes Sägemehl (Fäulnis)
8. Lagerung: 4–8 °C, dunkel, frostfrei; monatliche Kontrolle auf Fäulnis und Austrocknung

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis fabae, Macrosiphum rosae u.a. | Verkrüppelte Triebe, klebrige Honigtausekrete, Rußtau-Pilz als Folge, Ameisen-Hochfrequenz | leaf, stem, bud | vegetative, budding | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste an Blattunterseiten, gelbliche Tüpfelung auf Blättern; besonders bei Hitze und Trockenheit | leaf | flowering, budding | medium |
| Thripse | Frankliniella occidentalis | Silbrige Schabspuren auf Blättern und Blütenblättern, verkrüppelte Blüten, verkorkte Stellen | leaf, flower | budding, flowering | difficult |
| Ohrwürmer | Forficula auricularia | Unregelmäßige Fraßlöcher in Blütenblättern (nächtlich); zeigen auch positive Wirkung durch Blattlaus-Fraß | flower | flowering | medium |
| Nackschnecken | Arion rufus u.a. | Fraßspuren an jungen Trieben und Blättern, Schleimspuren; besonders an Jungpflanzen und feuchten Nächten | leaf, stem | sprouting, vegetative | easy |
| Raupen (Eulenfalter) | Agrotis spp. | Triebe und Blütenstiele angefressen oder abgebissen (Erdeulen unterirdisch), Fraßlöcher in Blättern | leaf, stem | vegetative, budding | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau (Oidium) | fungal | Weißer, mehlig-pudrig wirkender Belag auf Blättern und Trieben; Blätter vergilben und fallen ab | warm_days_cool_nights, dry_leaves, poor_airflow | 5–10 | vegetative, budding, flowering |
| Grauschimmel (Botrytis) | fungal | Grau-braune Flecken mit pelzigem Schimmelrasen; befällt Blüten zuerst; bei feuchtem Wetter rasch | high_humidity, wet_weather, dense_planting | 3–7 | budding, flowering |
| Dahlien-Mosaikvirus (DMV) | viral | Mosaik-Verfärbungen (hell-dunkel-grün gemustert), verformte Blätter, Wuchshemmung, verkümmerte Blüten | Blattläuse als Überträger | — (systemisch) | alle (persistent) |
| Verticillium-Welke | fungal | Einseitiges Welken von Trieben, braune Gefäßbündelung im Querschnitt; befällt Gefäßsystem | contaminated_soil, infected_tubers | 7–21 | vegetative, budding |
| Knollen-Fäulnis (Fusarium, Pythium) | fungal | Braune, weiche, faulige Stellen an Knollen; meistens in Lagerung oder bei Staunässe | overwatering, stagnant_water, poor_drainage | 5–14 | sprouting (bei Lagerung) |
| Bakterienwelke | bacterial | Plötzliches Welken ganzer Triebe; schleimig-fauliger Geruch; Gefäßbündelbraunung | contaminated_soil, high_temp | 3–7 | vegetative, flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse | 3–5 (Freilassung) | 7–14 |
| Florfliegenlarven (Chrysoperla carnea) | Blattläuse, Thripse | 5–10 | 14 |
| Schlupfwespe (Aphidius colemani) | Blattläuse | 5–10 | 14–21 |
| Raubmilbe (Phytoseiulus persimilis) | Spinnmilben | 10–20 | 7–14 |
| Nematoden (Steinernema feltiae) | Erdeulen-Larven, Thripse im Boden | 1 Mio./m² | 7 |
| Igel / Kröten | Nacktschnecken | — (Förderung durch Unterschlupf) | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl (Azadirachtin-haltig) | biological | Azadirachtin | Sprühen, 1–2 % Lösung mit Emulgator abends | 3 | Blattläuse, Spinnmilben, Thripse, Mehltau (vorbeugend) |
| Insektizide Seife (Kaliseife) | biological | Kaliumseife | Sprühen, 1–2 % abends | 1 | Blattläuse, Spinnmilben, Wollläuse |
| Backpulver-Spray (Natriumbicarbonat) | cultural | NaHCO₃ | 1 TL/L + Spritzer Öl, wöchentlich | 0 | Echter Mehltau (vorbeugend und kurativ) |
| Schachtelhalmbrühe | biological | Kieselsäure | 1:5 verdünnt, wöchentlich | 0 | Mehltau-Prävention, Zellwandstärkung |
| Schneckenkorn (Eisenphosphat) | biological | Eisenphosphat (III) | 5 g/m² auf Erde verteilen | 0 | Nacktschnecken (für Haustiere unbedenklich) |
| Pyrethrum | chemical | Pyrethrin (nat.) | Nach Etikett, abends | 3 | Blattläuse, Thripse, Spinnmilben |
| Fungizid Kupfer | chemical | Kupferoktanoat | Nach Etikett, 2–3× im Abstand von 7–10 Tagen | 3 | Botrytis, Echter Mehltau |
| Abstand einhalten | cultural | — | Pflanzabstand mind. 60–70 cm | 0 | Botrytis, Mehltau (Prävention) |
| Befallene Blüten/Triebe entfernen | cultural | — | Sofortiges Entfernen und Entsorgung (nicht kompostieren) | 0 | Botrytis, Virusverbreitung |

### 5.5 Resistenzen der Art

*Dahlia pinnata* (und damit auch Armateras) hat keine bekannte Resistenz gegen gängige Pathogene. Die Sorte ist für normalen Befall anfällig. Durch Standortwahl (Vollsonne, Luftzirkulation) und hygienische Maßnahmen (Deadheading, sauberes Werkzeug) lässt sich das Risiko deutlich reduzieren.

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| keine bekannte Resistenz | — | — |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Korbblütler (Asteraceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte (Fabaceae: Bohne, Erbse — liefern N), Gründüngung (Phacelia, Tagetes als Nematoden-Unterdrücker) |
| Empfohlene Nachfrucht | Zwiebeln (Allium) oder Salat (Asteraceae-freie Nachfolger bevorzugen); bei Tagetes als Vorfrucht: stark nematodenbefallene Böden sanieren |
| Anbaupause (Jahre) | 3–4 Jahre (gleiche Stelle meiden, um Verticillium-Akkumulation zu verhindern) |

**Hinweis:** Dahlien werden in der Praxis oft an festen Beetplätzen kultiviert, da Knollen jährlich ausgegraben werden. Bei jährlicher Knollenentfernung und Bodenerneuerung (Kompost) ist eine strikte Fruchtfolge weniger kritisch als bei Stauden oder im Freilandanbau verbleibenden Arten.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes (Studentenblume) | Tagetes patula, T. erecta | 0.9 | Nematoden-Abwehr durch Wurzelexsudate; Thripse-Ablenkung; Bestäuber-Attraktion; ähnliche Kulturansprüche | `compatible_with` |
| Kapuzinerkresse (Trap crop) | Tropaeolum majus | 0.8 | Fangt Blattläuse als Lockpflanze ab (Trap crop); Blüten essbar; lockerer Wuchs | `compatible_with` |
| Salbei | Salvia officinalis | 0.7 | Schädlingsabwehrender Duft; Bestäuber-Attraktion; ergänzende Optik | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bestäuber-Attraktion; aromatische Abwehr von Schädlingen; ähnlicher Wassergehalt | `compatible_with` |
| Snapdragons (Löwenmaul) | Antirrhinum majus | 0.7 | Füllt Lücken; gleiche Kulturansprüche; attraktive Farbkombination; kein Konkurrenzeffekt | `compatible_with` |
| Kosmeen | Cosmos bipinnatus | 0.8 | Leicht und luftig; ähnliche Ansprüche; Bestäuber; Botrytis-Prävention durch Luftzirkulation | `compatible_with` |
| Verbene | Verbena bonariensis | 0.7 | Niedrig, bildet Bodendecker; Bestäuber; harmoniert ästhetisch mit Dahlien | `compatible_with` |
| Stauden-Salbei | Salvia nemorosa | 0.7 | Kompakter Wuchs füllt Vordergrund; Bestäuber-Attraktion; Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Bekannte allelopathische Wirkung: Fenchel hemmt viele Kulturen durch Wurzel- und Blattexsudate | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gleiche Bodenschädlinge (Verticillium, Rhizoctonia); erhöhtes Krankheitsrisiko bei direkter Nachbarschaft oder in der Fruchtfolge | moderate | `incompatible_with` |
| Gladiolen | Gladiolus spp. | Gleiche Schädlinge (Thripse, vor allem Gladiolen-Thrips Thrips simplex), gegenseitige Befallsverstärkung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Asteraceae (Korbblütler) | `shares_pest_risk` | Echter Mehltau (Erysiphe cichoracearum), Blattläuse; Dahlien und Sonnenblumen können gleiche Schädlingspopulationen nähren | `shares_pest_risk` |
| Solanaceae (Nachtschattengewächse) | `shares_pest_risk` | Verticillium-Welke, Botrytis; nicht als Vorfrucht/Nachfolger empfohlen | `shares_pest_risk` |
| Fabaceae (Hülsenfrüchtler) | `family_compatible_with` | Stickstofffixierung im Vorjahr verbessert Bodenstickstoff | `family_compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Dahlia x hybrida 'Armateras' |
|-----|-------------------|-------------|------------------------------|
| Kleine Kugel-Dahlie (Pompon) | Dahlia pinnata (Pompon Group) | Kompakter, kleiner; gleiche Kulturbedingungen | Windstabiler (kleinere Blüten), weniger Stützbedarf, gut für Topf |
| Eintriebige Schmuckdahlie | Dahlia pinnata (Single-flowered) | Offene, ungefüllte Blüten | Bienenweidewert deutlich höher (zugängliche Pollen); pflegeleichter |
| Halskrausen-Dahlie (Collarette) | Dahlia pinnata (Collarette Group) | Ähnliche Höhe | Gut für Bienen; ästhetisch eigenständig; etwas widerstandsfähiger |
| Mexikanische Dahlie | Dahlia coccinea | Botanische Wildart; ähnliche Kulturbedingungen | Robuster, weniger krankheitsanfällig; wichtige Nektarquelle für Schmetterlinge |
| Tithonia (Mexikanische Sonnenblume) | Tithonia rotundifolia | Gleiches Farbspektrum (Orange), ähnliche Höhe | Extrem hitze- und trockenheitstolerant; geringerer Pflegeaufwand |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,frost_sensitivity,hardiness_detail,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,pruning_type,pruning_months,bloom_months,harvest_months,sowing_indoor_weeks_before_last_frost,sowing_outdoor_after_last_frost_days,propagation_methods,propagation_difficulty,traits
Dahlia pinnata,Dahlie;Garden Dahlia,Asteraceae,Dahlia,perennial,short_day,herb,tuberous,"8b;9a;9b;10a;10b",tender,"Knollen sterben bei Bodenfrost; in Mitteleuropa (Zone 5–8a) jährlich ausgraben und frostfrei bei 4–8 °C einlagern",0.0,"Mexiko, Mittelamerika",yes,25,30,110,60,65,no,yes,false,true,heavy_feeder,false,after_harvest,"7;8;9;10","7;8;9;10","7;8;9;10",5,0,"cutting_stem;division;seed",easy,"ornamental;bee_friendly"
```

### 8.2 Cultivar CSV-Zeile

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Armateras,Dahlia pinnata,A.C. Koot,2012,"decorative;full_double;pink;cut_flower",90,,clone
```

---

## Anhang: Knollen-Zyklus (REQ-022 Überwinterungsmanagement)

Dahlien-Knollen folgen einem klar strukturierten 6-Phasen-Jahreszyklus, der in REQ-022 (Knollen-Zyklus) explizit modelliert ist:

| Status | Zeitraum | Beschreibung |
|--------|---------|-------------|
| `stored` | November – März | Knollen ruhen trocken-kühl in Kisten/Säcken (4–8 °C, dunkel) |
| `pre_sprouting` | März – April | Knollen treiben in Schalen vor; erste Augen sichtbar |
| `planted` | Mai – Juni | Knollen im Beet oder Kübel; Vegetativwachstum |
| `flowering` | Juli – Oktober | Blütezeit; regelmäßiges Deadheading; Schnittblumenernte |
| `digging` | Oktober | Ausgraben nach erstem Frost; Abtrocknen; Beschriftung |
| `drying` | Oktober – November | 5–7 Tage Abtrocknen bei Raumtemperatur vor Einlagerung |

---

## Quellenverzeichnis

1. [Dutch Bulbs — Dahlie Armateras Produktseite](https://dutch-bulbs.com/de/dahlie-armateras/) — Sortenbeschreibung, Züchter A.C. Koot 2012, Pflanztiefe, Auspflanzmonat
2. [BULBi UK — Armateras](https://bulbi.co.uk/armateras-z40374-config) — Blütenfarbe, Blütendurchmesser, Wuchshöhe
3. [Hues Flower Farm — Armatera Potted Dahlia](https://www.hues.flowers/product/armatera-potted-dahlia-/157) — Verwendung als Topf-/Beetpflanze
4. [B2B.seklos.lt — Dahlia Armateras](https://b2b.seklos.lt/en/plants-and-seedlings/flower-bulbs/to-be-planted-in-spring/dahlia/dahlia-armateras-8714665099775-529894.html) — Pflanztiefe 10–12 cm, Pflanzmonat April/Mai
5. [American Dahlia Society — Nutrients for Dahlias](https://www.dahlia.org/docsinfo/articles/nutrients-for-dahlias/) — NPK-Empfehlungen, Düngefehler N-Überschuss
6. [Swan Island Dahlias — Fertilizing Tips](https://www.dahlias.com/blog/growing-tips/dahlia-fertilizing-tips/) — Düngungsplan und Timing
7. [ASPCA — Dahlia](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dahlia) — Toxizität für Katzen und Hunde (mild giftig)
8. [UC IPM — Dahlia Pest Management](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html) — Schädlings- und Krankheitsübersicht, Behandlungsmethoden
9. [RHS — How to Grow Dahlias](https://www.rhs.org.uk/plants/dahlia/growing-guide) — Allgemeine Kulturanleitung, Überwinterung
10. [Old Farmer's Almanac — Dahlias](https://www.almanac.com/plant/dahlias) — Pflanzzeitpunkt, Gießverhalten, Überwintern
11. [Floret Flowers — How to Grow Dahlias](https://www.floretflowers.com/resources/how-to-grow-dahlias/) — Pinching, Deadheading, Knollenproduktion
12. [Gardeners Path — Dahlia Companion Plants](https://gardenerspath.com/plants/flowers/dahlia-companion-plants/) — Mischkultur-Empfehlungen
13. [Gardening Know How — Dahlia Pests and Diseases](https://www.gardeningknowhow.com/ornamental/bulbs/dahlia/dahlia-pests-and-diseases.htm) — Schädlings-/Krankheitsliste
14. [Flourish Flower Farm — Overwintering Dahlias](https://www.flourishflowerfarm.com/blog/overwintering-dahlias) — Ausgrabe- und Lagerungsprotokoll
15. [Epic Gardening — Dahlia Companion Plants](https://www.epicgardening.com/dahlia-companion-plants/) — Mischkultur-Analyse
16. [Greg App — Dahlia Lifecycle](https://greg.app/dahlias-lifecycle/) — Wachstumsphasen-Überblick
17. [Wag Walking — Dahlia Poisoning in Cats](https://wagwalking.com/cat/condition/dahlia-poisoning-1) — Symptome Dahlia-Vergiftung Katzen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
18. [MSU Extension — Reducing time to flower in dahlias](https://www.canr.msu.edu/news/reducing-time-to-flower-in-dahlias) — Dahlien als tagneutral/fakultativ-kurztägig; Photoperiode und Blütezeit
19. [Dahlia Doctor — How Temperature & Day Length Impact Dahlia Growth & Tubers](https://www.dahliadoctor.com/blogs/second-blog/timing-is-everything-how-temperature-and-day-length-affect-dahlia-growth-and-tuber-formation) — Tuberisierung kurztaggesteuert (10–12 h fördert, >16 h hemmt); Temperaturoptimum Knollenbildung
20. [Epic Gardening — Do Dahlias Like Full Sun, Partial Shade?](https://www.epicgardening.com/dahlias-sun-or-shade/) — Sonnenbedarf 6–8 h, flaches Feeder-Wurzelsystem (~45 cm seitlich), Staunässe-Intoleranz
21. [Longfield Gardens — What Soil Do Dahlias Grow Best In?](https://www.longfield-gardens.com/blogs/dahlia-care/what-soil-do-dahlias-grow-best-in) — Boden-pH-Vorzug 6.5–7.0
22. [Greeny Gardener — pH For Dahlias](https://greenygardener.com/ph-for-dahlias/) — pH-Vorzug 6.5–7.0 (Zweitbeleg)
23. [Longfield Gardens — Soil Temperature for Planting / Temperature to Grow Dahlias](https://www.longfield-gardens.com/blogs/dahlia-care/what-temperature-do-dahlias-need-to-grow) — Min-Bodentemperatur 15 °C, aktives Wachstum 21–27 °C (Warm-Season-Einordnung, GDD-Basis)
24. [Longfield Gardens — How Many Years Do Dahlia Tubers Last?](https://www.longfield-gardens.com/blogs/dahlia-care/how-many-years-do-dahlia-tubers-last) — Knollen-Lebensdauer, klonale Vermehrung über Jahrzehnte durch Teilung
25. [Longfield Gardens — Are Dahlia Plants Annuals or Perennials? / Winter dormancy](https://www.longfield-gardens.com/blogs/dahlia-care/are-dahlia-plants-perennials-or-annuals) — Dormanz erforderlich, KEINE Vernalisation (tropische Herkunft)
26. [Zhen & Bugbee (2022), New Phytologist — Photosynthesis in sun and shade: the surprising importance of far-red photons](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.18375) — FR-Fraction direkter Solarstrahlung ≈ 0.46–0.5
27. [Wiley/PCE — The temperature response of C3 and C4 photosynthesis (Sage & Kubien 2007)](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1365-3040.2007.01682.x) — C3-Photosynthese-Optimum 25–30 °C
28. [ScienceDirect — Compensation Point overview](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/compensation-point) — Lichtkompensationspunkt sonnenadaptierter C3-Pflanzen ~20–50 µmol/m²/s
29. [Frontiers in Plant Science — Response of ornamental plants to salinity](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12343571/) — Salztoleranz-Klassifikation Zierpflanzen (sensitive 0–3 dS/m ECe); Glycophyten salzempfindlich
30. [RHS — How to grow dahlias (Growing Guide)](https://www.rhs.org.uk/plants/dahlia/growing-guide) — Vollsonne, free-draining, „may rot in waterlogged soil" (Sonnen-/Staunässe-Beleg)
31. [Floret Flowers — How to Grow Dahlias](https://www.floretflowers.com/resources/how-to-grow-dahlias/) — Vollsonne mind. 6 h, free-draining (Zweitbeleg Sonne/Drainage)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
