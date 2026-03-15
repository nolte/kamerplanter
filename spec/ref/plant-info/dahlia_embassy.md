# Dahlie Embassy — Dahlia 'Embassy'

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:** ilovedahlia.com (Dahlia-Spezialist), DutchGrown, BULBi.nl, Bulbs4you, American Dahlia Society (ADS), UC IPM, Longfield Gardens, Dahlia Doctor (dahliadoctor.com), Old Farmer's Almanac, Gardening Know How, Penn State Extension, ASPCA Giftpflanzenliste

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dahlia pinnata Cav. | `species.scientific_name` |
| Volksnamen (DE/EN) | Dahlie; Dahlia | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Dahlia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | `herb` (krautig, aufrecht, buschig) | `species.growth_habit` |
| Wurzeltyp | `tuberous` (Knollenstaude mit verzweigten Speicherwurzeln) | `species.root_type` |
| Lebenszyklus | `perennial` (botanisch ausdauernd; in Mitteleuropa als Knollenstaude behandelt, die jährlich ausgegraben wird) | `lifecycle_configs.cycle_type` |
| Photoperiode | `short_day` (fakultativ; Blüteninitiierung bei Nachtlänge > 12 h gefördert, Dahlien blühen jedoch auch unter Langtagbedingungen; Tuberisierung eindeutig kurztaggesteuert bei Nacht > 12 h; vegetatives Wachstum bei Langtag > 16 h) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a (winterhart im Boden); 3a–7b (jährlich ausgraben und einlagern) | `species.hardiness_zones` |
| Frostempfindlichkeit | `tender` (frostempfindlich — Knollen erfrieren bereits bei leichtem Frost unter 0 °C im Boden; Laub schwärzt beim ersten Frost) | `species.frost_sensitivity` |
| Winterhärte-Detail | Knollen überstehen im Boden maximal -3 °C kurzzeitig. In Mitteleuropa (Zone 6–7) sind Knollen nach dem ersten Frost auszugraben und frostfrei bei 4–10 °C einzulagern. In Zone 8+ kann eine dicke Mulchschicht (15–20 cm) Schutz bieten. | `species.hardiness_detail` |
| Heimat | Mexiko, Mittelamerika (Hochland, 1500–3000 m ü. NN) | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral — keine bekannten allelopathischen Wirkungen auf Nachbarpflanzen) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | `heavy_feeder` (Starkzehrer — benötigt nährstoffreichen Boden und regelmäßige Düngung für optimale Blühleistung und Knollenentwicklung) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | `['ornamental', 'bee_friendly']` (wichtiger Insektenmagnet; Pollen- und Nektarlieferant für Bienen und Hummeln von Mitte Sommer bis Frost) | `species.traits` |

**Hinweis zur Taxonomie:** Der korrekte wissenschaftliche Name der Garten-Dahlie ist botanisch umstritten. *Dahlia pinnata* Cav. (1791) gilt als Typusart der Gartendahlien-Hybriden. Ältere Literatur verwendet *Dahlia variabilis* Desf. Als Hybridkomplex wird oft *Dahlia × hybrida* verwendet. Für Kamerplanter-Import: `Dahlia pinnata` als Arten-Datensatz, `Embassy` als separater `Cultivar`-Datensatz mit `parent_species: Dahlia pinnata`.

### 1.1.1 Cultivar-Stammdaten: Embassy

| Feld | Wert | KA-Feld |
|------|------|---------|
| Sortenname | Embassy | `cultivar.name` |
| Elternart | Dahlia pinnata | `cultivar.parent_species` |
| Züchter | <!-- DATEN FEHLEN --> | `cultivar.breeder` |
| Züchtungsjahr | <!-- DATEN FEHLEN --> | `cultivar.breeding_year` |
| ADS-Klassifikation | SD (Small Decorative — Kleindekordahlie) | — |
| Blütenfarbe | Tiefpurpurrot mit weißer Unterseite (Bicolor-Effekt); vollgefüllt | — |
| Blütendurchmesser | ca. 10 cm (4 Zoll) | — |
| Wuchshöhe Cultivar | 90–130 cm (Angaben variieren: ca. 50 Zoll / 127 cm bei dutchgrown.com, ca. 90 cm bei ilovedahlia.com) | — |
| Traits | `['ornamental', 'bee_friendly', 'cut_flower']` | `cultivar.traits` |
| Samentyp | `clone` (vegetative Vermehrung via Knollenteilung/Stecklinge; Sorten-Dahlien sind nicht sortenecht aus Samen) | `cultivar.seed_type` |
| Photoperiode Cultivar | — (kein Cultivar-Override; erbt `short_day` der Elternart Dahlia pinnata) | `cultivar.photoperiod_type` |

### 1.2 Aussaat- & Erntezeiten

Mitteleuropa (Zone 7–8), Bezugspunkt: letzter Frost Mitte Mai (ca. 15. Mai).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkultur ab April im Haus; Knollen direkt im Topf vortreiben, NICHT aus Samen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Knollen erst nach den Eisheiligen (15.–20. Mai) in den Boden setzen) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (Auspflanzen: Mai nach letztem Frost, noch bis Anfang Juni möglich) | `species.direct_sow_months` |
| Erntemonate | null (Zierpflanze — `allows_harvest: false`; Knollenernte zum Einlagern: 10, 11) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 (Blüte von Mitte Juli bis zum ersten Frost; Höchstleistung August–September) | `species.bloom_months` |

**Hinweis:** Knollenvoranzucht (Treiben) ab April in einem hellen, frostfreien Raum bei 15–18 °C beschleunigt die erste Blüte um 2–4 Wochen gegenüber der Direktpflanzung der ruhenden Knolle.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | `division` (Knollenteilung im Frühjahr), `cutting_stem` (Stecklinge von vorgetriebenen Knollen März–April) | `species.propagation_methods` |
| Schwierigkeit | `moderate` (Knollenteilung: einfach, aber jedes Segment braucht mindestens ein Auge/"Eye". Stecklinge: leicht anspruchsvoller — Bewurzelung bei 18–22 °C mit Anzuchterde) | `species.propagation_difficulty` |

**Vermehrungs-Details:**
- **Knollenteilung:** Im Frühjahr beim Vorkeimen: Knolle mit scharfem Messer so teilen, dass jedes Segment ein oder mehrere Augen (Knospen an der Kronenbasis) hat. Schnittstellen mit Holzkohle oder Schwefelpulver desinfizieren. Sofort pflanzen oder kurz antrocknen lassen.
- **Stecklinge:** Vorgetriebene Knollen (März) liefern 3–7 cm lange Triebe. Abschneiden knapp über der Knolle (nicht ausreißen), in Bewurzelungshormon tauchen, in Anzuchterde stecken. Bewurzelung nach 10–14 Tagen bei 20 °C Bodentemperatur.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (ASPCA: Dahlia spp. als giftig für Katzen gelistet — milde Magen-Darm-Beschwerden) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (ASPCA: Dahlia spp. als giftig für Hunde gelistet — milde Magen-Darm-Beschwerden) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (mild giftig bei großen Mengen; Kontaktdermatitis möglich; als mäßig giftig einzustufen) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Pflanzenteile, besonders Knollen und Blätter | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Sesquiterpenlactone (u.a. Dahlin), Polyacetylene | `species.toxicity.toxic_compounds` |
| Schweregrad | `mild` (Erbrechen, Durchfall, Hautreizung; selten ernsthafte Vergiftung) | `species.toxicity.severity` |
| Kontaktallergen | true (Sesquiterpenlactone können Kontaktdermatitis auslösen — besonders bei Dahlien-Enthusiasten; Handschuhe empfohlen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Asteraceae-Pollen allgemein leicht allergisierend; jedoch weniger problematisch als windbestäubende Arten da insektenbestäubt) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | `after_harvest` (Rückschnitt nach dem ersten Frost: Stiele auf 10–15 cm über dem Boden kürzen vor dem Ausgraben; während der Saison: regelmäßiges Deadheading für kontinuierliche Blüte) | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (Pinching/Entspitzen: Ende Mai–Anfang Juni bei 30–40 cm Wuchshöhe, fördert Verzweigung), 10 (Herbstschnitt vor dem Ausgraben) | `species.pruning_months` |

**Pinching (Entspitzen):** Wenn die Pflanze 30–40 cm Höhe erreicht hat (ca. 3–4 Blattpaar-Etagen), den Haupttrieb über dem 3. Blattpaar abkneifen. Dies fördert 4–6 Seitentriebe statt eines dominanten Haupttriebs — deutlich mehr Blüten pro Pflanze. Einmalig durchführen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | `limited` (möglich in Kübeln ≥20 L; Standort vollsonnig; häufiges Gießen und Düngen nötig; Stütze erforderlich) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 (für 'Embassy' mit 90–130 cm Höhe) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 (Knollen und Wurzelsystem benötigen Tiefe) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 90–130 (Cultivar 'Embassy': ca. 90–127 cm, Quellen variieren; in der Mitte: ca. 110 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 (buschiger Wuchs, mit Pinching stärker verzweigt) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50–60 (Pflanzabstand; bei Dahlien dieser Größe 60 cm empfohlen für Luftzirkulation) | `species.spacing_cm` |
| Indoor-Anbau | `no` (Freilandpflanze; benötigt volle Sonne und Außenklima) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | `limited` (Kübel ≥20 L, sehr sonnige Lage; windzugefährdete Balkone problematisch wegen Staubbedarf) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (Freilandpflanze; Gewächshaus nur für Voranzucht und Knollenlagerung) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (bei 90–130 cm Wuchshöhe unbedingt Stab oder Bambusrohr setzen; Stürme brechen Stiele leicht) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, humusreiche Kübelpflanzenerde; 20–30 % Perlite oder grobem Sand für Drainage; pH 6.2–7.0. Drainagschicht im Topfboden obligatorisch. |  — |
| Substrat-Empfehlung (Beet) | Lockere, tiefgründige, gut durchlässige Gartenerde, reich an Humus; Ton- und Schwerstböden vorab mit Sand und Kompost verbessern; pH 6.5–7.0 | — |

---

## 2. Wachstumsphasen

Dahlia 'Embassy' ist eine Knollenstaude mit jährlichem Vegetationszyklus. In Mitteleuropa (Freilandanbau) gliedert sich die Wachstumsperiode in folgende Phasen. Der Knollenlagerungszeitraum (Winter) wird als `dormancy` modelliert.

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Entsorgung erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|--------------------|----------------|
| Dormanz (Knollenlager) | 120–150 (Nov–Mär) | 1 | false | false | false | high |
| Voranzucht / Austrieb | 21–42 (Apr) | 2 | false | false | false | low |
| Abhärtung / Auspflanzen | 7–14 (Mai) | 3 | false | false | false | low |
| Vegetativ | 28–56 (Mai–Jun) | 4 | false | false | false | medium |
| Blüte | 60–90 (Jul–Okt) | 5 | false | false | false | medium |
| Seneszenz / Knollenreife | 14–21 (Okt–Nov) | 6 | true | false | true | high |

**Hinweis zur Phasenmodellierung:** Da Dahlia pinnata eine perenniale Knollenstaude ist, wird `is_recurring: true` auf allen Phasen ab Phase 2 gesetzt. Die `dormancy`-Phase bildet die Winterruhe ab. `is_cycle_restart: true` gilt für den Übergang Seneszenz → Dormanz. `allows_disposal: true` in der Seneszenz-Phase (falls Knolle nicht weiterverwendet wird).

### 2.2 Phasen-Anforderungsprofile

#### Phase 1: Dormanz (Knollenlagerung, November–März)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 (dunkel lagern) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 4–10 (Lagertemperatur; nie unter 0 °C, nie über 12 °C) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–10 (gleichmäßig) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit (%) | 60–75 (mäßig feucht; zu trocken → Knollen schrumpeln; zu feucht → Fäulnis) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | null (nicht anwendbar — Knollen ohne aktiven Gaswechsel; kein Steuerungsparameter) | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | nicht relevant | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 0 (keine Bewässerung während Dormanz; gelegentlich Lagermedium leicht anfeuchten wenn Knollen schrumpeln) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 2: Voranzucht / Austrieb (April)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–250 (helles, indirektes Licht; Fensterbank Süd/West; kein direktes Mittagssonnenlicht zu Beginn) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (natürliches Tageslicht April) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 (kühl; zu warm → geile, schwache Triebe) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Außenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (mäßig feucht; Knolle nicht nass halten — Fäulnisgefahr) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 (je nach Topfgröße) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 3: Abhärtung / Auspflanzen (Mai, Hardening-Off)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (schrittweise Steigerung Sonnenlichtexposition über 7–14 Tage) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (natürliches Tageslicht Mai) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 (nach Frostende; min. 10 °C Bodentemperatur für Auspflanzen) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 (frostfrei; unter 5 °C zurückholen) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 (Außenklima) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–75 (Außenklima) | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Außenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 4: Vegetativ (Mai–Juni/Juli)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1200 (volle Sonne, ≥6 h direktes Sonnenlicht täglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag fördert vegetatives Wachstum; Blüteninitiierung beginnt wenn Nächte länger werden) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 (optimal 22–24 °C; über 30 °C hemmt Wachstum) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 (kühle Nächte fördern Knollenbildung) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 (Außenklima; gute Luftzirkulation wichtig gegen Mehltau) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Außenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (je nach Wetter; Substrat gleichmäßig feucht, nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 (stark wachsende Pflanze hat hohen Wasserbedarf; in Hitze täglich gießen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 5: Blüte (Juli–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1500 (maximale Sonnenexposition für beste Blüte; volle Sonne unerlässlich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 (kürzer werdende Tage signalisieren Blühbeginn) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 (optimal 22–25 °C; über 30 °C reduziert Blütenqualität) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 (kühle Nächte verlängern Blütedauer und intensivieren Farben) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 (hohe Luftfeuchte + schlechte Belüftung = Mehltau- und Botrytis-Risiko) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Außenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–3 (Hochsommer: täglich gießen möglich; immer morgens, nie abends — Botrytis-Prävention) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 (große Pflanze mit hoher Blühlast hat maximalen Wasserbedarf) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 6: Seneszenz / Knollenreife (Oktober–November)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (natürlich abnehmendes Herbstlicht) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 9–11 (Kurztagssignal verstärkt Knollenreifung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 8–16 (Herbsttemperaturen; Frost beendet Phase abrupt) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–8 (nahe Frost; bei Frostprognose sofort ausgraben) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–75 (Herbstklima) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Außenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (deutlich reduzieren; fördert Knollenreifung und -abhärtung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–700 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |
| Voranzucht | 1:1:1 | 0.4–0.8 | 6.2–6.8 | 60 | 30 | — | 2 |
| Abhärtung | 1:1:1 | 0.6–1.0 | 6.2–6.8 | 80 | 40 | — | 2 |
| Vegetativ | 3:1:2 | 1.0–1.6 | 6.2–7.0 | 120 | 50 | 30 | 3 |
| Blüte | 1:3:3 | 1.0–1.6 | 6.2–7.0 | 100 | 60 | 30 | 2 |
| Seneszenz | 0:0:2 | 0.4–0.8 | 6.2–7.0 | 40 | 20 | — | — |

**Wichtig:** Hoher Stickstoff in der Blüte- und Seneszenz-Phase führt zu weichem, fäulnisanfälligem Knollengewebe und stark reduzierter Blütenbildung. Kalium und Phosphor priorisieren.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage / Bedingung | Hinweis |
|------------|---------|-----------------|---------|
| Dormanz → Voranzucht | `time_based` + `manual` | Ende März / Anfang April | Knollen auf Schimmel und Fäulnis prüfen; nur gesunde Knollen vorziehen |
| Voranzucht → Abhärtung | `time_based` + `conditional` | 21–42 Tage; Triebe 5–10 cm | Nachttemperaturen außen dauerhaft über 5 °C |
| Abhärtung → Vegetativ | `manual` | 7–14 Tage Abhärtung | Nach den Eisheiligen (20. Mai); Bodenfrost ausgeschlossen |
| Vegetativ → Blüte | `event_based` | Erste Knospen sichtbar | Typisch Juli; bei kurzen Nächten (>14 h Tag) verzögert sich Blüte |
| Blüte → Seneszenz | `event_based` | Erster harter Frost (-2 °C); Laub schwärzt | Automatisch durch Frost oder manuell wenn Blühleistung nachlässt |
| Seneszenz → Dormanz | `manual` | 7–14 Tage nach Frost | Knollen ausgraben, trocknen, einlagern; `is_cycle_restart: true` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland/Beet — bevorzugte Methode)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | div. (z.B. Substral Naturen, Oscorna) | organisch | 80–100 g/m² | April (Pflanzung) | Stickstoff-Startversorgung |
| Kompost (reif) | eigen / Gartencenter | organisch | 3–5 L/m² | März/April (Einarbeitung) | Bodenverbesserung, Basisnährstoffe |
| Brennnesseljauche | eigen | organisch, flüssig | 1:10 verdünnt, 5 L/m² | Jun–Aug (alle 2 Wochen) | N+K in Vegetationsphase |
| Beinwell-Jauche | eigen | organisch, flüssig | 1:10 verdünnt, 3 L/m² | Jul–Sep (alle 2–3 Wochen) | K+P in Blütephase |
| Schafwollpellets | div. (z.B. Sheep Wool Pellets) | organisch | 50–70 g/m² | April | Langzeit-N, Wasserspeicherung |
| Algenkalk | div. (z.B. Calciumkalk von Oscorna) | mineralisch-organisch | 150 g/m² | Herbst oder Frühjahr | pH-Stabilisierung, Ca-Versorgung |

#### Mineralisch (Kübel / ergänzend im Beet)

| Produkt | Marke | Typ | NPK | EC-Beitrag (ml/L) | Mischpriorität | Phasen |
|---------|-------|-----|-----|------------------|----------------|--------|
| Blaukorn / Universaldünger | Compo Expert, Yara | Granulat | 12-12-17(+2Mg) | — | — | Vegetativ (Einarbeitung) |
| Blühpflanzendünger flüssig | Compo (Blaukorn flüssig) | flüssig | 3-4-8 | nach Anleitung | 1 | Blüte |
| Tomatendünger flüssig | Compo / Substral | flüssig | 3-4-8 | nach Anleitung | 1 | Blüte (P+K-betont) |
| Geranium- und Balkonpflanzendünger | Compo / Substral | flüssig | 3-4-8 | nach Anleitung | 1 | Blüte (Kübel) |
| CalMag-Supplement | Canna CalMag Agent / GHE CalMag | Supplement | — | 0.5–1.0 ml/L | 1 | Voranzucht, Vegetativ |

### 3.2 Düngungsplan (Freiland, organisch)

| Zeitraum | Phase | Maßnahme | Mittel | Menge | Hinweise |
|----------|-------|---------- |--------|-------|----------|
| März (Beetvorbereitung) | Dormanz → Voranzucht | Bodenverbesserung | Kompost | 3–5 L/m² | Flach einarbeiten (10–15 cm) |
| April (Pflanzung) | Voranzucht | Startdüngung | Hornspäne | 80 g/m² | In die Pflanzgrube einarbeiten |
| Mai–Juni | Vegetativ | Wachstumsschub | Brennnesseljauche 1:10 | alle 14 Tage | Bei trockenem Wetter morgens gießen |
| Juli–September | Blüte | Blütenförderung | Beinwell-Jauche 1:10 | alle 14–21 Tage | Kein Stickstoff mehr! P+K-Fokus |
| August–September | Blüte (Hochsommer) | Kaliumpush | Holzasche | 50 g/m² (Oberfläche) | Alternativ: Patentkali 30 g/m² |
| Oktober | Seneszenz | Düngung einstellen | — | — | Kein weiterer Dünger; Knollen härtung |
| November (nach Ausgraben) | Knollenlagerung | Boden nachbereiten | Kompost | 3 L/m² | Für nächstes Jahr vorbereiten |

### 3.3 Düngungsplan (Kübel, mineralisch-flüssig)

| Woche | Phase | Maßnahme | Mittel | Dosierung | Hinweise |
|-------|-------|---------- |--------|-----------|----------|
| 1–4 (Apr) | Voranzucht | Startdüngung | Universaldünger flüssig | halbe Dosis | Erst wenn erste echte Blätter sichtbar |
| 5–12 (Mai–Jun) | Vegetativ | Wachstumsförderung | Universaldünger | volle Dosis wöchentlich | Stickstoffbetont |
| 13–24 (Jul–Sep) | Blüte | Blütenförderung | Blühpflanzendünger / Tomatendünger | volle Dosis wöchentlich | Auf P+K-betonte Formel wechseln |
| 25–28 (Okt) | Seneszenz | Auslaufen lassen | — | — | Letzte Düngung 4 Wochen vor Frost |

### 3.4 Mischungsreihenfolge (Flüssigdünger im Kübel)

> **Kritisch:** Reihenfolge verhindert Ausfällungen.

1. Wasser (zimmerwarm, 18–20 °C)
2. CalMag-Supplement (bei Einsatz von Osmose-/weichem Wasser)
3. Flüssigdünger-Konzentrat
4. pH-Kontrolle und ggf. pH-Korrektur (Ziel: 6.2–7.0; IMMER zuletzt)

### 3.5 Besondere Hinweise zur Düngung

Dahlien reagieren sehr empfindlich auf Überdüngung mit Stickstoff: Zu viel N fördert üppiges Blattwachstum, produziert aber wenige und kleine Blüten sowie weiche, fäulnisanfällige Knollen im Herbst. Der Wechsel von einem stickstoffbetonten Dünger (Vegetativ) zu einem kalium-/phosphorbetonten Dünger (Blüte) ist entscheidend — spätestens wenn die ersten Knospen erscheinen.

Kalidüngung (Kaliumsulfat oder Patentkali) 4–6 Wochen vor dem Ausgraben fördert die Einlagerung von Reservestoffen in die Knollen und verbessert die Lagerfähigkeit erheblich.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

Das care_style-Preset `outdoor_annual_veg` ist für Dahlien nicht ideal, da sie Knollenstauden sind. Empfohlen wird `custom` mit folgenden Werten:

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `custom` (Dahlien folgen dem Knollen-Zyklus: Ausgraben, Einlagern, Vorziehen, Auspflanzen — kein Standard-Preset abbildbar; Knollen-Zyklus-Tracking per OverwinteringProfile) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 (Hochsommer; bei Hitze täglich) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0 (keine Bewässerung während Knollenlagerung) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | `top_water` (Von oben morgens gießen; Blüten und Blätter möglichst trocken lassen) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | null (Leitungswasser geeignet; pH-neutral bis leicht sauer bevorzugt) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 (alle 2 Wochen organische Jauche oder wöchentlich Flüssigdünger im Kübel) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–10 (April bis Oktober; Ende Oktober komplett einstellen) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jährlich neue Erde im Kübel; Knollen jedes Frühjahr einpflanzen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wöchentliche Sichtkontrolle, besonders auf Blattläuse, Ohrwürmer, Spinnmilben und Mehltau) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Freilandpflanze; hohe Luftfeuchtigkeit erhöht jedoch Mehltaurisiko) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Knollenkontrolle | Eingelagerte Knollen auf Schimmel, Fäulnis und Austrocknung prüfen. Verschrumpelte Knollen leicht anfeuchten. Befallene Stellen ausschneiden und mit Holzkohlepulver desinfizieren. | mittel |
| Feb | Knollenkontrolle | Zweite Sichtkontrolle. Saatgutkatalog für Neueinkäufe durchsehen. | niedrig |
| Mär | Beetvorbereitung | Kompost und Hornspäne in den Boden einarbeiten. Boden auflockern (30 cm tief). | hoch |
| Apr | Voranzucht starten | Knollen in Töpfe (mind. 3 L) mit feuchter, nicht nasser Anzuchterde setzen. Warm (18 °C) und hell stellen. | hoch |
| Mai | Auspflanzen | Nach den Eisheiligen (ab 20. Mai): Knollen/vorgezogene Pflanzen ins Freiland. Stützen setzen. Pflanzabstand 50–60 cm. Nicht angießen bis Triebe sichtbar. | hoch |
| Mai–Jun | Pinching (Entspitzen) | Bei 30–40 cm Wuchshöhe: Haupttrieb über dem 3. Blattpaar abkneifen. Fördert Verzweigung und deutlich mehr Blüten. Einmalig! | hoch |
| Jun | Stützen kontrollieren | Stäbe und Bindungen bei starkem Wachstum anpassen. Schädlingskontrolle. | mittel |
| Jul–Sep | Deadheading | Verblühte Blüten regelmäßig (1–2× wöchentlich) entfernen. Fördert kontinuierliche Nachblüte. | hoch |
| Aug | Hochsaison | Maximaler Wasserbedarf. Auf Mehltau prüfen. Blühpflanzendünger. | hoch |
| Sep | Herbstvorbereitung | Düngung reduzieren. Letzte Kalidüngung für Knollenreifung. Weiterhin Deadheading. | mittel |
| Okt | Herbstschnitt & Ausgraben | Nach dem ersten Frost: Stiele auf 10–15 cm kürzen. Knollen vorsichtig ausgraben (Spatengabel, nicht Spaten). 24 h umgedreht trocknen (Restwasser läuft aus Stiel). | hoch |
| Nov | Einlagern | Getrocknete Knollen in Kisten mit Kokoserde, trockenem Sand oder Sägemehl einlagern. Kühl (4–8 °C), dunkel, frostfrei. Einzeln beschriften! | hoch |
| Dez | Ruhephase | Knollen lagern. Keine Maßnahmen nötig außer monatlicher Kontrolle. | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | `dig_and_store` (Knollen ausgraben und frostfrei einlagern — in Mitteleuropa Zone 6–7 obligatorisch) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | `dig_store` (Ausgraben nach dem ersten Frost, Trocknen, Einlagern in Kokoserde/Sand) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, nach dem ersten harten Frost) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | `replant` (Knollen kontrollieren, teilen, und in Töpfe zum Vorziehen einpflanzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 (April, Voranzucht) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 4 (unter 4 °C besteht Erfrierungsgefahr) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 (über 10 °C beginnen Knollen frühzeitig zu treiben) | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | `dark` (dunkel lagern; Licht ist nicht nötig und nicht gewünscht während Dormanz) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | `none` (keine Bewässerung; Lagermedium nur minimal anfeuchten wenn Knollen sichtbar schrumpeln) | `overwintering_profiles.winter_watering` |

**Knollen-Zyklus-Status (REQ-022 OverwinteringProfile):**
Der Dahlienknolle-Jahreszyklus entspricht dem in REQ-022 definierten Knollen-Zyklus mit 6 Status-Phasen:
1. `in_ground` (Mai–Oktober: Pflanze wächst im Beet)
2. `dug_up` (Oktober: nach dem ersten Frost ausgraben)
3. `drying` (Oktober: 24–48 h trocknen, umgedreht aufgehängt)
4. `in_storage` (November–März: frostfrei eingelagert)
5. `pre_sprouting` (April: Voranzucht im Topf)
6. `hardening_off` (Mai: Abhärtung vor dem Auspflanzen)

**Lagerungsmethode im Detail:**
- Knollen in Kisten oder Plastikboxen mit Löchern einlagern
- Einbettungsmedium: trockene Kokoserde, Vermiculite, trockener Sand oder Sägemehl
- Knollen vollständig einbetten oder zumindest rundum bedecken
- Jede Knolle/Knollengruppe beschriften (Sortenname, Farbe, Datum)
- Monatliche Kontrolle auf Schimmel (abschneiden und Wunde desinfizieren) und Austrocknung

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------|-----------------|------------------------|
| Ohrwurm | Forficula auricularia | Unregelmäßige Fraßlöcher und Einbuchtungen an Blättern und Blütenblättern; Fraß meist nachts; Knospen können vollständig zerstört werden | leaf, flower | vegetative, flowering | medium (nachtaktiv) |
| Schwarze Bohnenlaus | Aphis fabae | Schwärzliche Blattlauskolonien besonders an Triebspitzen; Honigtau, Rußtaupilz; Verformung junger Blätter und Triebe | leaf, stem | vegetative, flowering | easy |
| Grüne Pfirsichlaus | Myzus persicae | Grünliche Läuse; Blattrollungen; Virusübertragung (Dahlia Mosaikvirus!) | leaf, stem | vegetative, flowering | medium |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste auf Blattunterseite; silbrig-bronzefarbene Flecken (Stippigkeit); bevorzugt bei Trockenheit und Hitze | leaf | vegetative, flowering | medium |
| Schnecken und Nacktschnecken | Deroceras reticulatum, Arion spp. | Fraßspuren an frisch ausgepflanzten Trieben und Knollen; besonders gefährlich nach der Pflanzung wenn Triebe durch den Boden kommen | leaf, stem, tuberous | vegetative (Jungpflanze) | medium |
| Erdraupen (Erdschnaken-Larven) | Tipula spp. | Fraß an Knollen und Stängelbasis unter der Erde; Pflanzen kollabieren plötzlich | root, tuberous | vegetative | difficult (unterirdisch) |
| Spargelfliege / Stängelbohrer | Ophiomyia kwansonis (Dahlienminierflieg) | Miniergänge im Stängel; Pflanzen welken plötzlich | stem | vegetative, flowering | difficult |
| Weichhautmilbe | Phytonemus pallidus | Verformte, bronzierte Triebspitzen; stunted growth; Blütendeformationen | leaf, flower | vegetative, flowering | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-----------------|
| Echter Mehltau | fungal (*Erysiphe cichoracearum* / *Sphaerotheca fuliginea*) | Weißer, mehliger Belag auf Blättern und Trieben; beginnt auf Blattoberseite; spätere Vergilbung und Blattfall | trockene Luft, warme Tage + kühle Nächte, schlechte Luftzirkulation | 5–10 | vegetative, flowering |
| Botrytis / Grauschimmel | fungal (*Botrytis cinerea*) | Grau-braune, filzige Schimmelschicht auf Blüten, Knospen und Stängeln; Knospen werden braun und öffnen sich nicht; bei Feuchtigkeit schnell ausbreitend | hohe Luftfeuchtigkeit, Regen, wenig Luftbewegung, verwelkte Pflanzenteile | 3–7 | flowering (besonders) |
| Sklerotinia-Stängelfäule | fungal (*Sclerotinia sclerotiorum*) | Weicher, wässriger Stängelbasisfäule; weißes Myzel und schwarze Sklerotien im Stängelinneren; Pflanze bricht zusammen | feuchter Boden, kühle Temperaturen | 7–14 | vegetative, flowering |
| Verticillium-Welke | fungal (*Verticillium dahliae*) | Einseitige Vergilbung und Welke; braune Verfärbung im Leitgewebe (Längsschnitt); bleibt im Boden | infizierter Boden, schlechte Drainage | 7–21 | vegetative, flowering |
| Dahlienmosaik-Virus | viral (*Dahlia mosaic virus*, DMV) | Mosaikfärbung, Blattdeformationen, Zwergwuchs; überträgt sich durch Blattläuse (aphid-vectored) und infizierte Knollen | Blattlausbefall; infizierte Stecklinge/Knollen | variabel | vegetative, flowering |
| Phytophthora-Stängelfäule | oomycete (*Phytophthora cryptogea*) | Schwärzliche, wässrige Fäule an Stängelbasis; besonders bei Jungpflanzen in nassem Boden | Staunässe, schwere Böden | 3–7 | seedling, vegetative |
| Knollenfäule (Lagerung) | fungal (*Botrytis*, *Fusarium*, *Rhizoctonia*) | Weiche, verfärbte Knollen im Lager; schlechter Geruch; schimmelige Stellen | zu nasse oder zu warme Lagerung, verletzte Knollen | variabel | dormancy |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|--------------------|------------------------|
| Marienkäfer (Siebenpunkt) | *Coccinella septempunctata* | natürliche Förderung durch Blühpflanzen | — (natürlich ansiedeln) |
| Chrysoperla carnea (Florfliege) | Blattläuse, Spinnmilben, Thripse | 5–10 Larven/m² | 14 |
| Phytoseiulus persimilis | Spinnmilben | 10–20/m² | 14–21 |
| Nematoden (*Steinernema feltiae*) | Erdraupen, Trauermücken, Sciariden | 500.000/m² | 7–14 |
| Parasitoide Wespen (*Aphidius colemani*) | Grüne Pfirsichlaus, andere Aphiden | 3–5/m² | 14–21 |
| Ohrwurmförderung | Ohrwurm als Nützling nutzen | Weidenkörbe mit Holzwolle als Nistmöglichkeit | — |

**Hinweis Ohrwurm:** Ohrwürmer sind bei Dahlien ambivalent — sie fressen Blütenblätter (Schaden), aber auch Blattläuse und Spinnmilben (Nutzen). Fallen-Einsatz (Tongefäße mit Holzwolle) ermöglicht gezielte Umsiedlung aus Blüten in andere Gartenbereiche.

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen, 0.3–0.5 % Emulsion, abends | 3 | Blattläuse, Spinnmilben, Mehltau (präventiv) |
| Kaliumbicarbonat | biological | Kaliumhydrogencarbonat (z.B. Vitisan) | Sprühen, 5 g/L | 0 | Echter Mehltau |
| Schwefelkalk (Calciumpolysulfid) | chemical | Schwefel-Calcium | Sprühen, Herbst/Winter auf Knollen | 14 | Mehltau, Schorfpilze |
| Kupferfungizid | chemical | Kupferhydroxid (z.B. Funguran) | Sprühen, 2.5 g/10 L | 14 | Botrytis, Phytophthora |
| Spinosad | biological | Spinosad (z.B. Conserve) | Sprühen | 3 | Ohrwürmer, Thripse |
| Diatomite (Kieselgur) | mechanical | — | Streuen um Pflanzen | 0 | Schnecken, Ohrwürmer |
| Bierschneckenfalle | mechanical | — | Schüssel mit Bier in Bodennähe | 0 | Schnecken |
| Kupfertape | mechanical | — | Um Töpfe und Beeteinfassung kleben | 0 | Schnecken |
| Mulchen | cultural | — | 5–8 cm Stroh- oder Rasenschnittmulch | 0 | Bodenpilze, Spritzwasser, Schnecken |
| Schnittgut sofort entfernen | cultural | — | Abgestorbene Pflanzenteile sofort kompostieren oder entsorgen (nicht auf Haufen stehen lassen) | 0 | Botrytis, Mehltau |
| Neem-Kuchen | biological | Azadirachtin | 200 g/m² in Boden einarbeiten | 0 | Nematoden im Boden, Larven |

**Hinweis Virusbefall:** Dahlienmosaik-Virus (DMV) ist nicht heilbar. Befallene Pflanzen sofort entfernen und vernichten (nicht kompostieren). Blattlausbekämpfung als wichtigste Präventivmaßnahme.

### 5.5 Resistenzen der Art/Sorte

| Resistenz gegen | Typ | Anmerkung | KA-Edge |
|----------------|-----|-----------|---------|
| Echter Mehltau | Krankheit | Keine bekannte Resistenz bei 'Embassy'; alle Dahlia-Sorten grundsätzlich anfällig | `resistant_to` |
| Verticillium dahliae | Krankheit | Keine bekannte Resistenz | — |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (`heavy_feeder`) |
| Fruchtfolge-Kategorie | Asteraceae-Zierstauden (Dahlien, Chrysanthemen, Tagetes) |
| Empfohlene Vorfrucht | Leguminosen (Fabaceae): Buschbohne, Erbse — Stickstoffanreicherung im Boden; oder Gründüngung (Phacelia, Lupine) |
| Empfohlene Nachfrucht | Schwachzehrer: Salat, Spinat, Rettich, Kräuter — profitieren von der Bodenbearbeitungstiefe durch Knollenentnahme; NICHT erneut Asteraceae |
| Anbaupause | 3–4 Jahre keine Dahlien (oder andere Asteraceae) auf derselben Fläche — verhindert Bodenmüdigkeit und Verticillium-Akkumulation |
| Besonderheit | Knollenausgraben im Herbst lockert den Boden auf 40 cm Tiefe — gute Vorfrucht für Tiefwurzler wie Möhren oder Pastinaken im Folgejahr |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|-----------------------|--------|---------|
| Tagetes (Studentenblume) | *Tagetes patula* / *T. erecta* | 0.9 | Nematoden-Abwehr im Boden; Weißmücken-Abwehr; Bestäuber anlocken; Farbharmonie | `compatible_with` |
| Basilikum | *Ocimum basilicum* | 0.7 | Angeblich Blattlaus-abschreckend durch Duft; Bestäuber anlocken | `compatible_with` |
| Kosmee / Schmuckkörbchen | *Cosmos bipinnatus* | 0.8 | Gleiche Kulturbedingungen (Sonne, Wärme); Bestäuber fördern; optische Ergänzung | `compatible_with` |
| Lavendel | *Lavandula angustifolia* | 0.8 | Aromatischer Schutz gegen Blattläuse; Bestäuber anlocken; passt zu sonnigen Standorten | `compatible_with` |
| Ringelblume | *Calendula officinalis* | 0.7 | Nematoden-Abschreckung; Blattläuse anlocken (Fangpflanze für Dahlien-Nachbarn) | `compatible_with` |
| Süßalyssum | *Lobularia maritima* | 0.8 | Lockt Schlupfwespen und andere Nützlinge an; Bodendecker reduziert Bodenfeuchte-Verdunstung | `compatible_with` |
| Antirrhineum (Löwenmaul) | *Antirrhinum majus* | 0.7 | Gleiche Kulturbedingungen; Lückenfüller im Vordergrund | `compatible_with` |
| Koriander | *Coriandrum sativum* | 0.7 | Blühen zieht Schlupfwespen an; Blattlausfeinde fördern | `compatible_with` |
| Artemisia (Silberraute) | *Artemisia ludoviciana* | 0.7 | Soll Schnecken abschrecken (Silberlaub); keine direkte Wachstumshemmung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Brokkoli | *Brassica oleracea* var. *italica* | Gleiche Schädlinge (Blattläuse, Mehltau); Nährstoffkonkurrenz; pH-Überschneidung; Krankheitsübertragung wahrscheinlicher | moderate | `incompatible_with` |
| Blumenkohl | *Brassica oleracea* var. *botrytis* | Gleicher Grund wie Brokkoli | moderate | `incompatible_with` |
| Kopfkohl / Weißkohl | *Brassica oleracea* var. *capitata* | Gleicher Grund wie Brokkoli; zudem extreme Nährstoffkonkurrenz da ebenfalls Starkzehrer | moderate | `incompatible_with` |
| Fenchel | *Foeniculum vulgare* | Allelopathische Wirkung des Fenchels hemmt viele Nachbarpflanzen; sendet Wachstumshemmstoff aus | severe | `incompatible_with` |
| Kartoffel | *Solanum tuberosum* | Teilen Verticillium-Risiko; Krautfäule (Phytophthora) kann übergreifen; konkurrierende unterirdische Raumansprüche | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Asteraceae (Korbblütler) | `shares_pest_risk` | Echter Mehltau, Verticillium, Schmierlaus, Chrysanthemen-Nematoden | `shares_pest_risk` |
| Brassicaceae (Kreuzblütler) | `shares_pest_risk` | Blattläuse (*Aphis fabae*), Mehltau | `shares_pest_risk` |
| Fabaceae (Hülsenfrüchtler) | `family_compatible_with` | Keine geteilten Risiken; Stickstoff-Fixierung bereichert den Boden für Dahlien | `family_compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art / Sorte | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Embassy |
|-------------|-------------------|-------------|---------------------------|
| Dahlien Pompon-Typ (z.B. 'Franz Kafka') | *Dahlia pinnata* (Pompon) | Gleiche Familie und Kultur | Kleinere Blüten (5–6 cm), kugelförmig; kompakterer Wuchs; wetterresistenter (Blüten halten länger) |
| Dahlia 'Bishop of Llandaff' | *Dahlia pinnata* (Einfach-Blütig) | Gleiche Kultur | Offene Blüten für Insekten besser zugänglich; dunkelrotes Laub; weniger Pflege |
| Tagetes (Großblumige Studentenblume) | *Tagetes erecta* | Gleiche Standortansprüche (Sonne) | Deutlich pflegeleichter; keine Knolle einzulagern; Einjährige; zudem nützlingsfördernd |
| Cosmos (Schmuckkörbchen) | *Cosmos bipinnatus* | Gleiche Blütezeit | Sehr leichte Kultur; kein Ausgraben nötig; selbst aussäend; für Anfänger besser geeignet |
| Rudbeckia (Sonnenhut) | *Rudbeckia hirta* | Ähnliche Blütezeit | Mehrjährig und winterhart; deutlich geringerer Pflegeaufwand; keine Knolle |
| Echinacea | *Echinacea purpurea* | Ähnliche Optik (Asteraceae) | Vollständig winterhart; Heilpflanze; keine Überwinterungsmaßnahmen nötig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,frost_sensitivity,hardiness_detail,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,propagation_methods,propagation_difficulty,pruning_type,pruning_months,bloom_months,direct_sow_months,sowing_indoor_weeks_before_last_frost,traits
Dahlia pinnata,"Dahlie;Dahlia",Asteraceae,Dahlia,perennial,short_day,herb,tuberous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a",tender,"Knollen erfrieren im Boden unter 0 °C. In Zone 3–7 jährlich ausgraben und frostfrei einlagern (4–10 °C). In Zone 8+ mit Mulchschutz (15–20 cm) möglich.",0.0,"Mexiko, Mittelamerika (Hochland 1500–3000 m ü. NN)",limited,20,40,90,50,55,no,limited,false,true,heavy_feeder,false,"division;cutting_stem",moderate,after_harvest,"5;10","7;8;9;10","5;6",4,"ornamental;bee_friendly"
```

### 8.2 Cultivar CSV-Zeile

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Embassy,Dahlia pinnata,,,"ornamental;bee_friendly;cut_flower",90,,clone
```

---

## 9. Datenlücken & Unsicherheiten

| Feld | Status | Anmerkung |
|------|--------|-----------|
| `cultivar.breeder` | FEHLT | Züchter nicht recherchierbar; Sorte 'Embassy' ist in mehreren Spezialkatalogen gelistet, Ursprung unbekannt |
| `cultivar.breeding_year` | FEHLT | Kein Datum in öffentlichen Quellen verfügbar |
| VPD-Werte Dormanz | FEHLT | Kein wissenschaftlicher Zielwert für Knollenlagerung verfügbar; wird nicht benötigt (keine Bewässerung) |
| Stängelbohrer / Dahlienminierflieg | UNSICHER | *Ophiomyia kwansonis* ist primär in Asien verbreitet; in Mitteleuropa seltener; Angabe als Vorwarnung |
| Genaue Wuchshöhe Embassy | UNSICHER | Quellen variieren: ilovedahlia.com nennt ca. 90 cm, dutchgrown.com nennt ~127 cm (50 Zoll). Mittelwert ~110 cm im Dokument verwendet. |
| ADS-Blütendurchmesser | LEICHT UNSICHER | 10 cm wird konsistent genannt; ADS-Klassifikation SD (Small Decorative) entspricht 10–15 cm Durchmesser |
| Photoperiod Embassy-Cultivar | ANNAHME | Embassy-spezifische Photoperiodendaten nicht verfügbar; Verhalten der Elternart Dahlia pinnata angewendet |

---

## Quellenverzeichnis

1. [ilovedahlia.com — Dahlia Embassy Produktseite](https://ilovedahlia.com/decorative-dahlia/small-decorative-dahlia/dahlia-embassy/) — Blütenfarbe, Typ, Grunddaten
2. [DutchGrown — Dahlia Embassy](https://www.dutchgrown.com/products/dahlia-embassy) — Wuchshöhe, Blütezeit
3. [BULBi.nl — Embassy](https://www.bulbi.nl/en/embassy) — Knollenanbieter, Grunddaten
4. [American Dahlia Society (ADS) — Classification & Handbook](https://www.dahlia.org/guide/form.html) — Formklassifikation (Small Decorative)
5. [ADS — Nutrients for Dahlias](https://www.dahlia.org/docsinfo/articles/nutrients-for-dahlias/) — NPK-Empfehlungen, Düngungslogik
6. [ADS — Digging, Dividing, and Storing Tubers](https://www.dahlia.org/docsinfo/articles/digging-dividing-and-storing-tubers/) — Überwinterung, Knollenbehandlung
7. [UC IPM — Managing Pests in Gardens: Dahlia](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html) — IPM, Schädlinge und Krankheiten
8. [Dahlia Doctor — The Dahlia Clock](https://www.dahliadoctor.com/blogs/second-blog/the-dahlia-clock-bringing-it-all-together) — Phasensteuerung, Photoperiode, Temperatur
9. [Dahlia Doctor — Temperature & Day Length](https://www.dahliadoctor.com/blogs/second-blog/timing-is-everything-how-temperature-and-day-length-affect-dahlia-growth-and-tuber-formation) — Wissenschaftliche Hintergründe zu Kurztagsreaktion und Knollenbildungstemperatur
10. [Longfield Gardens — Common Dahlia Pests and Diseases](https://www.longfield-gardens.com/article/common-dahlia-pests-and-diseases) — Schädlings-/Krankheitsübersicht
11. [Longfield Gardens — How to Overwinter Dahlias](https://www.longfield-gardens.com/article/how-to-overwinter-dahlias) — Überwinterungsdetails nach Zone
12. [Gardening Know How — How to Fertilize Dahlias](https://www.gardeningknowhow.com/ornamental/bulbs/dahlia/how-to-fertilize-dahlias.htm) — NPK-Empfehlungen praktisch
13. [Ohio Tropics — Best Fertilizer For Dahlia Plants](https://www.ohiotropics.com/2023/05/22/best-fertilizer-for-dahlia-plants/) — Produktempfehlungen, P+K-Fokus
14. [Old Farmer's Almanac — Dahlias](https://www.almanac.com/plant/dahlias) — Allgemeine Kulturanleitung
15. [Epic Gardening — 17 Best Dahlia Companion Plants](https://www.epicgardening.com/dahlia-companion-plants/) — Mischkulturempfehlungen
16. [House Digest — Dahlias Are A Bad Match](https://www.housedigest.com/1411401/dahlias-bad-match-in-garden-cauliflower-broccoli-cabbage/) — Unverträglichkeiten mit Brassicaceae
17. [Penn State Extension — Dahlia Diseases](https://extension.psu.edu/dahlia-diseases) — Pilzkrankheiten und Behandlung
18. [Penn State Extension — Don't Ditch Those Dahlias](https://extension.psu.edu/dont-ditch-those-dahlias-easy-tips-for-winter-storage) — Winterlagerung
19. [ASPCA — Toxic and Non-Toxic Plants: Dahlia](https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants) — Toxizitätsdaten für Haustiere
20. [NC State Extension — Dahlia Plant Toolbox](https://plants.ces.ncsu.edu/plants/dahlia/) — USDA-Härtezonen, Grunddaten
