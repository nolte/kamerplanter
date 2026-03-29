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
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual (Sommerannuelle); kann bei Herbstsaat ueberwintert werden (Winterannuelle) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
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
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (Kamille ist trockenheitstoleranter als Gemuese) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Rosette | 1:1:1 | 0.4–0.6 | 6.0–7.0 | 60 | 25 | 10 | 1 |
| Vegetativ | 2:1:1 | 0.5–0.8 | 6.0–7.0 | 80 | 30 | 15 | 2 |
| Bluete | 1:1:2 | 0.4–0.7 | 6.0–7.0 | 60 | 30 | 10 | 1 |
| Samenreife | 0:1:1 | 0.3–0.5 | 6.0–7.0 | 40 | 20 | — | — |

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
