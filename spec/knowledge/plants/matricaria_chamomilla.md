# Echte Kamille — Matricaria chamomilla

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Plantura Kamille pflanzen, Naturadb Matricaria chamomilla, TLLLR Anbautelegramm Echte Kamille, Samen.de Kamille Begleitpflanze und Kamillenanbau, Gartenrat.de Echte Kamille, Oekolandbau.de Kamille, ESCOP Monograph Chamomillae Flos

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Matricaria chamomilla | `species.scientific_name` |
| Synonyme | Matricaria recutita L.; Chamomilla recutita (L.) Rauschert | — |
| Volksnamen (DE/EN) | Echte Kamille, Feldkamille, Kamillenblume; German Chamomile, Common Chamomile | `species.common_names` |
| Familie | Asteraceae | `species.family` -> `botanical_families.name` |
| Gattung | Matricaria | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 (krautiger Korbblütler; nicht sukkulent, nicht C4/CAM) | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual (Sommerannuelle); kann bei Herbstsaat ueberwintert werden (Winterannuelle) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur Wuchs (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für M. chamomilla in zwei unabhängigen Quellen auffindbar; veröffentlichte GDD-Studien (z.B. CSIR-IHBT Palampur) nennen die verwendete Basistemperatur nicht. Keimtemperaturen (15–20°C) sind als Wuchs-GDD-Basis NICHT zulässig. --> | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false (einjährig; Samen keimen ohne Kältestratifikation, 7–14 Tage bei 15–20°C) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (qualitativer Langtagblüher — Blüte wird durch Tageslänge ausgelöst, nicht durch Kältereiz) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht zutreffend, da keine Vernalisation erforderlich) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 14 (Langtagblüher; Blühinduktion oberhalb ~14 h Tageslänge — konsistent mit Phasenübergangs-Trigger §2.4) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy (Herbstrosetten ueberleben bis -15°C; Fruehjahressaamlinge hingegen nur half_hardy) | `species.frost_sensitivity` |
| Winterhaerte-Detail | Herbstgesaete Kamille overwinteren als Rosette bis -15°C. Fruehjahrsgesaete Pflanzen sterben nach Bluete und Samenreife ab. | `species.hardiness_detail` |
| Heimat | Suedost- und Mitteleuropa, Westasien; heute weltweit eingebürgert | `species.native_habitat` |
| Allelopathie-Score | 0.3 (leicht positiv allelopathisch auf Nachbarpflanzen) | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | medicinal; edible; aromatic; companion | `species.traits` |

**Taxonomische Besonderheit:** Matricaria chamomilla und Matricaria recutita werden in der Literatur haeufig synonym verwendet. Die aktuelle Nomenklatur bevorzugt M. chamomilla. Nicht zu verwechseln mit der Geruchlosen Kamille (Tripleurospermum inodorum) die keine aetherischen Oele enthaelt.

**Unterscheidungsmerkmal:** Echter Kamille: hohler Blutenboden (Rezeptakulum) — beim Durchschneiden erkennbar. Geruchlose Kamille: voller Bluetenboden.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7–8).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (moeglich; aber Direktsaat bevorzugt — Lichtkeimer!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (vertraegt leichte Froezte als Saemling; Herbstsaat Sept.–Okt. fuer Fruehjahresbluete) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5 (Fruehjahr); 9; 10 (Herbst fuer Ueberwinterung) | `species.direct_sow_months` |
| Erntemonate | 5; 6; 7 (Bluetenernte von Mai bis Juli; Haupternte Mitte Mai bis Mitte Juni) | `species.harvest_months` |
| Bluetemonate | 5; 6; 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 15–20°C
- Keimdauer: 7–14 Tage
- Saattiefe: Nur oberflächlich andrücken — Kamille ist ein **Lichtkeimer!** Nicht abdecken.
- Keimung erfolgt auch ohne Licht, aber Lichtkeimer-Status bedeutet: kein tiefes Einbetten; max. 2–3 mm Substrat druecken
- Selbstaussaat: Kamille saet sich bei guenstigem Standort reichlich selbst aus. Einmal eingebuergert, bleibt sie im Garten durch Selbstaussaat erhalten.

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false (ASPCA: nicht gelistet als toxisch; bei sehr grossen Mengen GI-Beschwerden moeglich) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false (leichte GI-Symptome bei grossen Mengen) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (medizinisch verwendet; Kamillen-Tee auch fuer Saeuglinge; bei Allergie gegen Asteraceae vorsichtig) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (ätherische Öle wie Bisabolol und Chamazulen sind therapeutisch; nicht toxisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Kreuzallergie bei Asteraceae-Allergie: Chrysanthemen, Ragweed; Kontaktdermatitis moeglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (kann bei Asteraceae-sensiblen Personen Pollenallergie ausloesen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | after_harvest | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7 (Blueten regelmaessig ernten verlaengert Bluetephase erheblich!) | `species.pruning_months` |

**Hinweis:** Regelmaessiges Ernten der Kamillenblüten (alle 2–3 Tage in der Hauptblütezeit) foerdert die Neubildung von Blueten und verlaengert die Ernte um Wochen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Topf ab 5 L; aber durch Selbstaussaat im Topf schlecht kontrollierbar) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 20–50 (sortenabhaengig und standortabhaengig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 15–20 (bei Direktsaat; Parzellen-Aussaat) | `species.spacing_cm` |
| Indoor-Anbau | limited (als Zimmerplanze wenig geeignet; zu sonnig noetig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (kleine Toepfe; Kräuterbalkon; volle Sonne) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Magere, durchlaessige Kraeutererde oder Sandgemisch; kein Kompost (zuviel Naehrstoffe senken aetherische Oelbildung!); pH 6.0–7.0 | -- |

**Wichtig:** Zu naehrstoffreiche Boeden foerdern das Blattwachstum auf Kosten der Bluete und der aetherischen Oelkonzentration. Magere, leicht sandige Boeden sind ideal fuer Arzneikamille. Im kommerziellen Anbau werden bewusst magere Boeden gewaehlt.

---

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein art-spezifischer Lichtkompensationspunkt für M. chamomilla in zwei unabhängigen Quellen messbar belegt. Generischer C3-Krautwert läge größenordnungsmäßig bei ~10–30 µmol/m²/s, ist aber nicht art-spezifisch verifiziert. --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN (siehe min) --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade (volle Sonne bevorzugt; verträgt leichten Halbschatten, blüht dort aber schwächer) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–40 (dünne Pfahlwurzel; Quellen uneinheitlich: teils flach/breit wurzelnd, teils bis ~30–46 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (braucht durchlässigen Boden; Staunässe fördert Pythium-Wurzelfäule, vgl. §6.2) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant (gedeiht in mäßig salzhaltigen Böden; Optimum bei ECe ≈ 2 dS/m, Toleranz in Studien bis ~9 dS/m, dann Ertragsrückgang) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine veröffentlichten Maas-Hoffman-a-Werte für M. chamomilla; Studien geben nur Salzstufen, keinen Schwellenwert nach Maas-Hoffman an. --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein veröffentlichter Maas-Hoffman-b-Wert (Slope) für M. chamomilla. --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–7.0 (leicht sauer bis neutral; PFAF/Tropical: 5.5–6.5 bevorzugt, tolerant 5–7; harmonisiert mit pH 6.0–7.0 in §1.6/§2.3) | `species.soil_ph_preference` |

**Hinweis Salztoleranz:** Bezugsgröße ist die Substrat-Sättigungsextrakt-Leitfähigkeit (ECe), nicht die Gießwasser-EC. Mäßiger Salzstress (um 2 dS/m) kann den Gehalt an ätherischen Ölen sogar leicht erhöhen, höhere Werte mindern Wuchs und Blütenbildung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | low |
| Rosette / Saemling | 21–42 | 2 | false | false | medium |
| Vegetativ | 14–28 | 3 | false | false | medium |
| Bluete / Ernte | 28–56 | 4 | false | true | high |
| Samenreife / Absterben | 14–28 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 (Lichtkeimer; braucht Licht fuer Keimung!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 (kritischer Punkt stomatären Kollaps; deutlich über Zielkorridor; feuchteliebende Keimphase → niedrige Schwelle) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high (Keimlinge sehr empfindlich gegen Austrocknung) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 (Kühljahreszeit-Art) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Vollsonne; R:FR ≈ 1.1–1.3) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (gleichmaessig feucht; nie Austrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–80 (sanftes Besprühen; Samen nicht wegschwemmen!) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Rosette / Saemling

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 6–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 (kritischer Punkt stomatären Kollaps; oberer Zielwert + ~0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–21 (Kühljahreszeit-Art) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Vollsonne; R:FR ≈ 1.1–1.3) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete / Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (volle Sonne bevorzugt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtagspflanze; kurze Tage verzoegern Bluete) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (kritischer Punkt stomatären Kollaps; oberer Zielwert + ~0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium (Blütephase trockenheitstoleranter) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 (kühlere Nächte um 15°C steigern Chamazulen-/Ölqualität) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Vollsonne; R:FR ≈ 1.1–1.3) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (Kamille ist trockenheitstoleranter als Gemuese) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |
| Rosette | 1:1:1 | 0.4–0.6 | 6.0–7.0 | 60 | 25 | 10 | 1 | 0.5 | 0.2 | 0.05 | 0.03 |
| Vegetativ | 2:1:1 | 0.5–0.8 | 6.0–7.0 | 80 | 30 | 15 | 2 | 0.6 | 0.3 | 0.05 | 0.05 |
| Bluete | 1:1:2 | 0.4–0.7 | 6.0–7.0 | 60 | 30 | 10 | 1 | 0.5 | 0.2 | 0.05 | 0.03 |
| Samenreife | 0:1:1 | 0.3–0.5 | 6.0–7.0 | 40 | 20 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoff-Hinweis:** Die Spalten Mn/Zn/Cu/Mo (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`) entsprechen üblichen Nährlösungs-Richtwerten für Schwachzehrer (Mn 0.5–2, Zn 0.5–2, Cu 0.1–0.5, Mo 0.02–0.05 ppm) am unteren Ende des Bereichs — es liegen keine art-spezifisch für *Matricaria chamomilla* publizierten Mikronährstoff-Zielwerte vor; die Angaben sind generische Hydrokultur-Normen (Hoagland/Steiner-Typ).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Naehrstoffhinweis:** Bei zu hohem EC (> 1.0 mS) oder reichlichem Kompostzusatz wächst die Kamille zwar ueppig, bildet aber weniger Blueten mit niedrigerem Gehalt an aetherischen Oelen (Bisabolol, Chamazulen). Fuer arzneiliche Zwecke mager duengen!

### 2.4 Phasenubergangsregeln

| Von -> Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung -> Rosette | time_based | 7–14 Tage | Keimblätter entfaltet; typisches Fiederblatt sichtbar |
| Rosette -> Vegetativ | time_based | 21–42 Tage | Pflanze verzweigt sich; aufrechter Wuchs beginnt |
| Vegetativ -> Bluete | event_based | — | Tageslänge > 14 Stunden; erste Knospen; Temperatur > 15°C |
| Bluete -> Samenreife | time_based | 28–56 Tage | Bluetenboden braun; Samen ausreifen |

---

## 3. Düngung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Organisch (Freiland / Kräutergarten) — bevorzugt

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif, sparsam) | eigen | organisch | 1–2 L/m² | Herbst-Einarbeitung | Bodenstruktur |
| Hornmehl | Oscorna | organisch-N | 20–30 g/m² | Fruehjahr einmalig | light_feeder |
| Gar kein Duenger | — | — | — | Bei gutem Boden | Aromasteigerung |

#### Mineralisch (nur bei Mangel)

| Produkt | Marke | Typ | NPK | Phasen |
|---------|-------|-----|-----|--------|
| Kräuterduenger | Compo Sana | mineralisch | 7-3-6 | Vegetativ |
| Kaliumsulfat | div. | K-Ergaenzung | 0-0-50 | Bluete (Aroma) |

### 3.2 Besondere Hinweise zur Düngung

Kamille benoetigt praktisch keine Duengung auf normalem Gartenboden. Ueberschuss an Stickstoff foerdert das Blattwachstum und mindert Bluetenbildung und aetherischen Oelgehalt. Auf sehr armen, sandigen Boeden geniugt eine einmalige sparliche Gabe von Hornmehl im Fruehjahr. Kompost aus eigenem Garten (gut verrottet) ist ausreichend.

**Fuer kommerzielle Kamille-Produktion (nach TLLLR):** N-Bedarfswert 40–60 kg/ha; Phosphor und Kalium gemaess Bodenanalyse. Ueberschuss an N senkt den Bisabolol-Gehalt.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 (trockenheitstoleranter als die meisten Kraeuter) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.3 (Herbstgesaete Rosetten brauchen wenig Wasser) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Regenwasser bevorzugt; kalkempfindlich; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | — (kein oder sehr seltenes Duengen; s.o.) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4 (wenn ueberhaupt: einmalig) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig; Umtopfen moeglich aber nicht noetig) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Mär–Apr | Fruehjahressaat | Direktsaat auf gut gelockertem Boden; Lichtkeimer nicht bedecken | hoch |
| Apr | Auflaufen pruefen | Keimung kontrollieren; Vogelschutz bei Saatvögeln | mittel |
| Apr–Mai | Ausduennen | Bei dichter Keimung auf 15 cm ausduennen | niedrig |
| Mai–Jul | Ernte | Taeglich bei voller Blüte (morgens); Kamillen-Sieb-Kamm verwenden | hoch |
| Mai–Jul | Trocknung | Bei 35–40°C trocknen (Doerrautomat oder Backofentuer aufhalten); max 4-6 Stunden | hoch |
| Jul | Samenernte | Letzte Blueten ausreifen lassen; Samen fuer naechstes Jahr sammeln oder Selbstaussaat foerdern | mittel |
| Sep–Okt | Herbstsaat | Optional: Saat fuer Ueberwinterung und fruehe Fruehjahrsbluete | mittel |

**Ernte-Tipp:** Kamillenblueten morgens nach dem Trocknen des Taus ernten, da der aetherische Oelgehalt am Vormittag am hoechsten ist. Vollstaendig geo[effnete Blueten (Zungenblüten waagerecht oder leicht nach unten) haben den hoechsten Wirkstoffgehalt.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung (Overwintering)

Nur relevant für **Herbstaussaat** (Sept.–Okt.): Diese Pflanzen überwintern als kompakte, gefiederte Blattrosette und blühen ab April — mehrere Wochen früher als frühjahrsgesäte Kamille. Frühjahrsgesäte Pflanzen sterben dagegen nach Blüte und Samenreife im Sommer ab (Sommerannuelle) und werden nicht überwintert.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | hardy (winterharte Rosette; übersteht in Zone 6–8 den Winter im Freiland) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch (lockere Laub-/Reisigmulchschicht über die Jungrosetten; schützt vor Kahlfrost) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 (November, vor erstem stärkeren Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | uncover (Mulch abräumen, sobald Wachstum wieder einsetzt) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (März, mit Wiederbeginn des Wachstums) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | — (Freilandüberwinterung; kein Quartier nötig, Rosetten frosthart bis ca. -15°C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | — (Freiland; volles Tageslicht) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam; nur bei Trockenheit ohne Schneedecke (Winter-Multiplikator 0.3, vgl. §4.1) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Die Rosetten sind grundsätzlich winterhart, profitieren in rauen Lagen (Zone 6 und kälter) aber von einer leichten Mulchabdeckung, die Kahlfrost und Wechselfrost-Auswinterung abpuffert. Topf-Herbstrosetten an eine geschützte, frostfreiere Hauswand stellen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Ernte-Verarbeitung

### 5.1 Ernte-Indikatoren

- Bluetooth-Zungenblüten (weiss) stehen waagerecht oder leicht nach unten gebogen (nicht aufrecht wie bei Knospe)
- Bluetenboden beim Betasten leicht weich und schwammig (hohl im Inneren — Erkennungsmerkmal der echten Kamille)
- Blueten leicht mit Fingern abstreifen oder Kammgeraet nutzen
- Fuer Tee: Alle 2–3 Tage ernten, da neue Blueten schnell nachkommen

### 5.2 Trocknung

| Parameter | Empfehlung |
|-----------|-----------|
| Temperatur | 35–40°C (max. 45°C; hoehere Temp. degradiert Bisabolol und Chamazulen) |
| Dauer | 3–6 Stunden im Doerrautomat; 24–48 Stunden bei Lufttrocknung (Schatten) |
| Lagerung | Luftdicht in Glasdosen; dunkel und kuehl; Haltbarkeit 1–2 Jahre |

---

## 6. Schaedlinge & Krankheiten

### 6.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kamillenglattkaefer | Olibrus aeneus | Fraß an Bluetenboden; inneres ausgefressene; Blüte unbrauchbar | flower | flowering | medium |
| Kamillenstaengelruesskaefer | Microplontus campestris | Stengel-Einlage; Verdickungen; Stengel bricht | stem | vegetative, flowering | difficult |
| Schwarze Bohnenlaus | Aphis fabae | Kolonien an Triebspitzen; Honigau | shoot, leaf | vegetative | easy |
| Blattlaeuse (verschiedene) | diverse Aphidae | Saugen an Trieben; Verkrüppelung | shoot | seedling, vegetative | easy |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; gelbe Stippen (nur bei Hitzestress/Topfkultur) | leaf | flowering | medium |

### 6.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | Erysiphe cichoracearum | Weisser Belag auf Blaettern | Trocken-Hitze + kühle Naechte | 5–10 | vegetative, flowering |
| Grauschimmel | Botrytis cinerea | Grauer Belag auf Blueten bei Naesse | hohe Feuchtigkeit, Verletzungen | 3–7 | flowering |
| Kamillenrost | Puccinia millefolii (selten) | Orangefarbene Pusteln | Feuchtes Wetter | 7–14 | vegetative |
| Pythium (Wurzelfaeule) | Pythium spp. | Auspflanzen fault; Damping off | Staunaesse; Uebernaesse | 3–5 | seedling |

### 6.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Standortwahl (Belueftung) | cultural | — | Locker saeen; nicht eng; Luftzirkulation | 0 | Mehltau, Grauschimmel |
| Neemöl | biological | Azadirachtin | 0.3% Spruehlosung; nicht auf offene Bluetueen! | 3 | Blattlaeuse, Spinnmilbe |
| Trocken halten | cultural | — | Nicht abends giessen; Belueftung | 0 | Grauschimmel |

**Hinweis:** Auf Kamillenfeldern sind chemische Behandlungen wegen der Bluete-Ernte nicht vertretbar. Kulturell-biologische Massnahmen und Sortenresistenz stehen im Vordergrund.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 6.4 Nützlinge (Biologische Bekämpfung)

Da chemischer Pflanzenschutz wegen der Blütenernte ausscheidet, eignen sich Nützlinge besonders — vor allem in Topf-/Gewächshauskultur und bei lokalen Befallsherden.

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|--------------------|----------------|-----------------|------------------|
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphis fabae u.a. Aphididae) | 0.25–4 Tiere/m²/Freilassung, ≥3× wiederholen | 2–3 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattlaus-Kolonien (Befallsherde) | 1–10 Tiere/m²/Freilassung, wöchentlich | 2–3 Wochen |
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m²/Freilassung, 1–2× wöchentlich | 2–4 Wochen |

**Hinweis:** Die Korbblütler-spezifischen Käfer/Rüssler (Kamillenglattkäfer *Olibrus aeneus*, Stängelrüssler *Microplontus campestris*) haben keine etablierten kommerziellen Antagonisten — hier bleiben Standortwahl, lockere Saat und Fruchtwechsel die wirksamsten Maßnahmen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 7. Fruchtfolge & Mischkultur

### 7.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Korbblütler (Asteraceae) |
| Empfohlene Vorfrucht | Alle; keine speziellen Ansprüche |
| Empfohlene Nachfrucht | Alle; Kamille als Bodenverbesserer |
| Anbaupause (Jahre) | 1–2 Jahre (Kamillenmüdigkeit; Selbstaussaat aber wuenschenswert) |

### 7.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Weißkohl | Brassica oleracea var. capitata | 0.8 | Nuetzlingsfoerderung; Bodengesundheit; Kohlfliegenabwehr | `compatible_with` |
| Brokkoli | Brassica oleracea var. italica | 0.8 | Gleicher Nutzen wie Kohl | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.7 | Nuetzlinge; Duft-Abwehr | `compatible_with` |
| Zwiebeln | Allium cepa | 0.8 | Bestaeuberanlockung; gegenseitige Foerderung | `compatible_with` |
| Kartoffel | Solanum tuberosum | 0.7 | Angeblich Wachstumsfoerderung (Gartenliteratur) | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Bodenschutz; Untersaat-Eignung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Gemeinsame Nuetzlingsfoerderung; harmonisch | `compatible_with` |

### 7.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Pfefferminze | Mentha x piperita | Gegenseitige chemische Hemmung der aetherischen Oele | moderate | `incompatible_with` |
| Andere Asteraceen (Chrysanthemen, Ringelblume) | Asteraceae spp. | Gleiche Schaedlinge; Konkurrenz; optisch aehnlich | mild | `incompatible_with` |

**Allelopathie-Hinweis:** Kamille wirkt auf viele Nachbarpflanzen leicht wachstumsfoerdernd (Allelopathie-Score +0.3). Besonders Zwiebeln und Kohl scheinen von der Nachbarschaft zu profitieren. Dies ist in der deutschen Gartenbauliteratur seit Jahrhunderten bekannt (Gertrud Franck, Riech Mischkultur).

### 7.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Asteraceae | `shares_pest_risk` | Kamillenglattkaefer, Aphidae | `shares_pest_risk` |

---

## 8. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Kamille |
|-----|-------------------|-------------|------------------------------|
| Roemische Kamille | Chamaemelum nobile | Aeusserlich aehnlich; Korbblütler | Ausdauernde Staude; dichter Rasen; kein Chamazulen; milderes Aroma |
| Geruchlose Kamille | Tripleurospermum inodorum | Optisch sehr aehnlich | Kein medizinischer Wert; haeufigstes Unkraut — verwechslungsgefaehrdet! |
| Hundskamille | Anthemis cotula | Aehnliches Aussehen; scharf riechend | Keine medizinische Wirkung; Kontaktallergen |
| Gelbe Kamille | Anthemis tinctoria | Giebe Bluetendolden; Korbblütler | Faerbepflanze; kein Kamillen-Aroma |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Matricaria chamomilla,Echte Kamille;Feldkamille;German Chamomile,Asteraceae,Matricaria,annual,long_day,herb,taproot,3a–9b,0.3,Suedosteuropa;Westasien,limited,5–10,15,20–50,15–30,15–20,limited,yes,false,false,light_feeder
```

### 9.2 Cultivar CSV-Zeilen

```csv
name,parent_species,days_to_maturity,traits,seed_type,notes
Bodegold,Matricaria chamomilla,70–90,high_bisabolol;large_flowers;aromatic,open_pollinated,Hochertragsssorte; hoher Bisabolol-Gehalt (>50%); fuer Heilkraeuter-Anbau
Zloty Lan,Matricaria chamomilla,65–85,compact;medium_flowers;oil_rich,open_pollinated,Polnische Anbausorte; kompakt; guter Oelgehalt
Lutea,Matricaria chamomilla,70–90,very_large_flowers;ornamental;aromatic,open_pollinated,Grosse Blueten; dekorativer Wert; auch als Zierpflanze
Bona,Matricaria chamomilla,60–80,early;compact;good_yield,open_pollinated,Fruehjahrssorte; schnelle Entwicklung; guter Feldaufbau
```

---

## Quellenverzeichnis

1. Plantura — Kamille pflanzen: Standort, Aussaat & Tipps — https://www.plantura.garden/kraeuter/kamille/kamille-pflanzen
2. Naturadb — Matricaria chamomilla — https://www.naturadb.de/pflanzen/matricaria-chamomilla/
3. TLLLR Thüringen — Anbautelegramm Echte Kamille — https://www.tlllr.de/www/daten/publikationen/anbautelegramm/at_kamille.pdf
4. Samen.de — Kamille als Begleitpflanze — https://samen.de/blog/kamille-als-begleitpflanze-positive-effekte-auf-andere-kulturen.html
5. Samen.de — Kamillenanbau: Herausforderungen meistern — https://samen.de/blog/kamillenanbau-herausforderungen-meistern-erfolge-ernten.html
6. Gartenrat.de — Echte Kamille Anbau und Pflege — https://gartenrat.de/echte-kamille/
7. Oekolandbau.de — Echte Kamille als Unkraut und Heilpflanze — https://www.oekolandbau.de/
8. ESCOP Monograph — Chamomillae Flos (Kamillenbluete) — European Scientific Cooperative On Phytotherapy

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
9. PFAF (Plants For A Future) — Matricaria recutita: pH-Vorzug (5.5–6.5, tolerant 5–7), Halbschatten-Toleranz, mäßige Salztoleranz, Niederschlagsbereich — https://pfaf.org/user/Plant.aspx?LatinName=Matricaria+recutita
10. Useful Tropical Plants — Matricaria chamomilla: pH, Sonnenstandort, dünne Pfahlwurzel, mäßig saline Böden — https://tropical.theferns.info/viewtropical.php?id=Matricaria+chamomilla
11. Wisconsin Horticulture (UW–Madison Extension) — German Chamomile, Matricaria chamomilla: einjährig, Vollsonne, flach/breit wurzelnd, Selbstaussaat — https://hort.extension.wisc.edu/articles/chamomile-matricaria-chamomilla/
12. Wikifarmer — German Chamomile Growing Conditions: Temperaturbereich 7–26°C, Wuchsoptimum 15–20°C, Vollsonne — https://wikifarmer.com/german-chamomile-growing-conditions/
13. MDPI Horticulturae 11(5):485 (2025) — Assessing Growth Performance and Agrometeorological Indices of Matricaria chamomilla L. (Western Himalaya): GDD-Akkumulation über Phänophasen (Basistemperatur nicht ausgewiesen) — https://www.mdpi.com/2311-7524/11/5/485
14. ResearchGate — Photoperiodic lighting of Matricaria (qualitativer Langtagblüher; Schossen + Blüte bei Langtag) — https://www.researchgate.net/publication/282830571_Photoperiodic_lighting_of_matricaria_tanacetum_parthenium
15. Nature Scientific Reports 14 (2024) / PMC11344756 — Impact of NaCl stress on Matricaria chamomilla: Salzstufen 1.84–8.96 dS/m, Optimum ~2 dS/m — https://pmc.ncbi.nlm.nih.gov/articles/PMC11344756/
16. ASHS J. Amer. Soc. Hort. Sci. 146(1) — Far-red Fraction metric: Vollsonne FR/(R+FR) ≈ 0.46–0.5, R:FR ≈ 1.1–1.3, Unterwuchs höher — https://journals.ashs.org/view/journals/jashs/146/1/article-p3.xml
17. Koppert — Aphidius colemani, Aphidoletes aphidimyza, Phytoseiulus persimilis: Ausbringraten/m² — https://www.koppertus.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/
18. Plantura — German chamomile care & propagation: Herbstaussaat überwintert als Rosette, Mulchschutz, Blüte ab April — https://plantura.garden/uk/herbs/chamomile/german-chamomile
19. Envirevo Agritech — Hydroponic micronutrient ranges (Mn/Zn/Cu/Mo ppm, generische Nährlösungsnormen) — https://envirevoagritech.com/optimizing-hydroponic-nutrients-requirements/
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
