# Radieschen -- Raphanus sativus var. sativus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-02
> **Quellen:** PFAF, RHS, USDA Plant Guide, UMN Extension, Utah State Extension, Plantura, Hortipendium, COMPO, fryd.app, Koppert, ASPCA

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Raphanus sativus var. sativus | `species.scientific_name` |
| Volksnamen (DE/EN) | Radieschen; Radish; Monatsrettich | `species.common_names` |
| Familie | Brassicaceae | `species.family` -> `botanical_families.name` |
| Gattung | Raphanus | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (schosst bei Langtagsbedingungen >14h) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a; 3a; 4a; 5a; 6a; 7a; 8a; 9a; 10a | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Frosthart bis ca. -5 degC. Keimung ab 5 degC Bodentemperatur. Jungpflanzen vertragen leichte Froeste (-2 degC). Kein Winteranbau moeglich, aber sehr fruehe Aussaat (Maerz) und spaete Herbstaussaat (September) problemlos. | `species.hardiness_detail` |
| Heimat | Vorderasien, oestlicher Mittelmeerraum (vermutlich von Raphanus raphanistrum domestiziert) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false (Oelrettich R. sativus var. oleiformis hingegen ja) | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai. Radieschen sind Sukzessionskultur -- alle 2--3 Wochen nachsaeen fuer kontinuierliche Ernte.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | -- (Direktsaat bevorzugt, Vorkultur nicht ueblich da Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (Direktsaat bereits 6--8 Wochen VOR letztem Frost moeglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 6; 7; 8; 9 | `species.direct_sow_months` |
| Erntemonate | 4; 5; 6; 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 5; 6; 7 (nur bei ungewolltem Schossen -- Bluete ist unerwuenscht) | `species.bloom_months` |

**Aussaat-Details:**
- Frueheste Aussaat im Freiland: Anfang Maerz (Vliesabdeckung empfohlen)
- Sommerpause: Juli--August kann problematisch sein (Schossgefahr bei Hitze und Langtag >14h)
- Herbstaussaat: August--September (kuerzere Tage verhindern Schossen)
- Sukzession: Alle 2--3 Wochen nachsaeen fuer kontinuierliche Ernte

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 15--20 degC
- Minimale Keimtemperatur: 5 degC (langsame Keimung, 10--14 Tage)
- Maximale Keimtemperatur: 30 degC (Keimrate sinkt, Schossgefahr steigt)
- Keimdauer: 3--7 Tage (bei 15--20 degC)
- Saattiefe: 1--2 cm
- Saatabstand: 3--5 cm in der Reihe, 10--15 cm Reihenabstand
- Lichtkeimer: Nein (Dunkelkeimer, leicht mit Erde bedecken)
- Substrat: lockere, steinfreie Erde ohne frische organische Duengung
- Direktsaat ist Standard -- Vorkultur nicht empfohlen (Pfahlwurzel vertraegt kein Umpflanzen)

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (enthaelt Senfoele/Glucosinolate, aber nicht toxisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Hinweis: Radieschen sind vollstaendig ungiftig. Senfoele (Isothiocyanate) verursachen die Schaerfe, sind aber gesundheitsfoerdernd (antimikrobiell, antioxidativ). Blaetter sind essbar und naehrstoffreich (Salat, Pesto). Hunde und Katzen koennen Radieschen in kleinen Mengen fressen -- groessere Mengen koennen durch Senfoele leichte Magen-Darm-Reizungen verursachen.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Kein Rueckschnitt erforderlich. Bei zu dichter Aussaat Saemling auf 3--5 cm vereinzeln (Ausdünnen), damit die Knollen genuegend Platz haben. Schossende Pflanzen sofort entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--5 (Balkonkasten ab 15 cm Tiefe genuegt) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 15--25 (Blattrosette) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 8--15 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5 (in der Reihe), 10--15 (Reihenabstand) | `species.spacing_cm` |
| Indoor-Anbau | limited (moeglich auf heller Fensterbank, aber Knolle bleibt oft klein) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (ideal fuer Balkonkaesten und Kuebel, schnelle Ernte) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (freilandtauglich, Gewaechshaus nur fuer Treiberei im Fruehjahr) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, durchlaessige Gemueseerde ohne grobe Stuecke. Keine frische organische Duengung (Mist), da dies zu deformierten Knollen und Maden fuehrt. Leicht sandige Beimischung foerdert glatte Knollenbildung. | -- |

**Hinweis:** Radieschen sind das ideale Einsteigergemuese: schnelle Ernte (3--4 Wochen), anspruchslos, platzsparend. Perfekt als Lueckenfueller zwischen Hauptkulturen (Markierungssaat fuer langsam keimende Moehren) und als Vorkultur/Nachkultur. Bei Temperaturen ueber 25 degC und Langtag (>14h) steigt die Schossgefahr -- dann Sorten mit geringer Schossneigung waehlen oder Aussaat-Pause einlegen.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 3--7 | 1 | false | false | low |
| Saemling (seedling) | 7--10 | 2 | false | false | low |
| Knollenbildung (vegetative) | 14--21 | 3 | false | false | medium |
| Erntereife (ripening) | 3--7 | 4 | true | true | medium |

Hinweis: Die Gesamtkulturzeit betraegt nur 22--35 Tage (sortenabhaengig). Fruehlingsradieschen (Cherry Belle, Saxa) sind am schnellsten (22--28 Tage). Spaetere Sorten (Riesenbutter, Eiszapfen) benoetigen 30--40 Tage. Ueberreife Radieschen werden holzig und pelzig -- Erntezeitpunkt nicht verpassen!

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer bis Keimblaetter erscheinen), dann 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0, dann 5--8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0, dann 10--12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--20 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht halten, nie staunass) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 (Kurztagsbedingungen bevorzugt gegen Schossen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: In dieser Phase werden die Keimblaetter entfaltet und die ersten echten Blaetter gebildet. Zu dichtstehende Saemling jetzt auf 3--5 cm vereinzeln (Ausdünnen).

#### Phase: Knollenbildung (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 (Langtag >14h foerdert Schossen statt Knollenbildung!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (gleichmaessig! Trockenstress fuehrt zu holzigen, pelzigen Knollen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Die kritischste Phase -- hier entscheidet sich Knollengroesse und -qualitaet. Gleichmaessige Wasserversorgung ist essentiell: Wechsel zwischen nass und trocken fuehrt zu Platzern und Pelzigkeit. Temperaturen ueber 25 degC beschleunigen das Schossen und verhindern gute Knollenbildung. Kühle Nachttemperaturen (8--12 degC) foerdern die Knollenentwicklung.

#### Phase: Erntereife (ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Erntereife erkennen: Knolle ragt leicht aus der Erde, Durchmesser 2--3 cm (sortenabhaengig). Nicht zu lange warten -- ueberreife Radieschen werden holzig, schwammig und bitter. Ernte am besten morgens, Blaetter sofort abdrehen (ziehen Feuchtigkeit aus der Knolle). Lagerung: gekuehlt in feuchtem Tuch 5--7 Tage.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.6 | 6.0--6.8 | 60 | 30 | 20 | 1 |
| Knollenbildung | 1-2-3 | 0.8--1.2 | 6.0--6.8 | 80 | 40 | 30 | 2 |
| Erntereife | 0-1-2 | 0.6--0.8 | 6.0--6.8 | 60 | 30 | 20 | 1 |

Hinweis: Radieschen sind Schwachzehrer und benoetigen nur minimale Duengung. Zu viel Stickstoff fuehrt zu ueppigem Laub auf Kosten der Knollenbildung -- das ist der haeufigste Anfaengerfehler! Kalium foerdert Knollenbildung und Geschmack. Bor-Mangel fuehrt zu hohlen, rissigen Knollen (Bor-Gehalt im Giesswasser beachten).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 3--7 Tage | Keimblaetter (Kotyledonen) voll entfaltet |
| Saemling -> Knollenbildung | time_based | 7--10 Tage nach Keimung | 2--4 echte Blaetter, Hypokotyl beginnt zu verdicken |
| Knollenbildung -> Erntereife | time_based | 14--21 Tage | Knolle 2--3 cm Durchmesser, ragt leicht aus der Erde |

GDD-Hinweis: Basistemperatur 4.4 degC. Ca. 300--400 GDD bis Erntereife (sortenabhaengig). Fruehe Sorten (Cherry Belle, Saxa): ~300 GDD. Spaetere Sorten (Riesenbutter, Eiszapfen): ~400 GDD.

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Flora Micro | General Hydroponics | base | 5-0-1 (+Ca 5%) | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Saemling |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10 | 4 | Knollenbildung |
| Hakaphos Gruen 20-5-10 | COMPO Expert | base | 20-5-10 | ~0.15 | 3 | Saemling (sparsam!) |
| Hakaphos Naranja 15-5-30 | COMPO Expert | base | 15-5-30 | ~0.14 | 3 | Knollenbildung |

Hinweis: Hydroponische Radieschen-Kultur ist moeglich aber unueblich. EC 1.0--1.6 mS (niedrig halten!), pH 6.0--7.0. NFT- oder Ebb-Flood-Systeme geeignet, Substratkultur (Kokos, Perlite) bevorzugt da Wurzelknolle Platz braucht.

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 (Beetvorbereitung im Herbst/Fruehjahr) | Herbst/Fruehjahr | light_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 20--40 g/m2 (nur bei sichtbarem N-Mangel!) | Fruehjahr | light_feeder |
| Bio-Universalduenger (fluessig) | COMPO BIO | organisch | 10--20 ml / 10 L Giesswasser | alle 3--4 Wochen | light_feeder |
| Holzasche | Eigenerzeugung | organisch (K-betont) | 50--100 g/m2 (nur unbehandelt!) | Fruehjahr | light_feeder |

**Wichtig:** Radieschen brauchen normalerweise KEINE Zusatzduengung wenn das Beet im Vorjahr fuer eine Starkzehrer-Kultur (Tomate, Kohl, Kuerbis) geduengt wurde. Die Restnaehrstoffe genuegen fuer Schwachzehrer. Frischer Stallmist ist verboten -- foerdert Madenbefall und deformierte Knollen!

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Radieschen Freiland -- Standard")

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| 1 | Keimung | 0.0 | 6.0--7.0 | Nur Wasser. Boden sollte durch Vorkultur-Duengung ausreichend versorgt sein. |
| 2 | Saemling | 0.0--0.4 | 6.0--6.8 | Keine Duengung noetig. Bei sehr magerem Boden: 1x duenn Bio-Fluessigduenger (halbe Dosis). |
| 3--4 | Knollenbildung | 0.4--0.8 | 6.0--6.8 | Optional 1x Kalium-betonte Duengung (Holzasche-Aufguss oder Bio-Universalduenger halbe Dosis). |
| 5 | Erntereife | 0.0 | 6.0--7.0 | Keine Duengung. Ernte. |

### 3.3 Mischungsreihenfolge

Fuer die unkomplizierte Freilandkultur von Radieschen ist keine spezielle Mischungsreihenfolge erforderlich. Bei hydroponischer Kultur:

1. Wasser temperieren (15--20 degC)
2. CalMag (falls Wasser kalkarm)
3. Base A (Flora Micro / Calcium + Mikronaehrstoffe)
4. Base B (Flora Bloom / Phosphor + Kalium)
5. pH-Korrektur (IMMER als letzter Schritt)

### 3.4 Besondere Hinweise zur Duengung

- **Stickstoff-Ueberschuss ist der haeufigste Fehler:** Zu viel N fuehrt zu ueppigem Blattwerk, spindligen Wurzeln, geringer Knollenbildung und erhoehter Anfaelligkeit fuer Schaedlinge. Radieschen als Schwachzehrer brauchen fast keine Duengung!
- **Bor-Mangel:** Fuehrt zu hohlen, rissigen Knollen mit braunem Kerngewebe. In bor-armen Boeden 1 g Borax pro 10 m2 einarbeiten. Kalkreiche Boeden fixieren Bor -- pH-Wert unter 7.0 halten.
- **Kalium foerdert Knollenqualitaet:** Sorgt fuer knackige, aromatische Knollen mit guter Lagerfaehigkeit. Holzasche oder Kalimagnesia bei Kaliummangel.
- **Kalk:** Radieschen bevorzugen leicht sauren bis neutralen Boden (pH 6.0--7.0). Auf sauren Boeden (pH <5.5) kalken -- dies schuetzt auch gegen Kohlhernie (Plasmodiophora brassicae).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Keine besonderen Anforderungen. Leitungswasser geeignet. Gleichmaessige Feuchtigkeit ist wichtiger als Wasserqualitaet. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | -- (normalerweise keine Duengung noetig) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig, Direktsaat, kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | -- | -- | -- |
| Feb | Beetvorbereitung | Boden lockern, Kompost einarbeiten (2--3 L/m2). Keine frische organische Duengung! | niedrig |
| Marz | 1. Aussaat (Fruehjahr) | Direktsaat ab Bodentemperatur 5 degC. Vliesabdeckung beschleunigt Keimung und schuetzt vor Erdfloh. Reihenabstand 10--15 cm, 1--2 cm tief. | hoch |
| Apr | Sukzessionssaat + Ernte 1 | Alle 2--3 Wochen nachsaeen. Erste Maerz-Aussaat jetzt erntereif. Regelmaessig giessen! | hoch |
| Mai | Fortlaufende Aussaat + Ernte | Weiter sukzessiv saeen. Erdfloh-Kontrolle (Kulturschutznetz!). Vereinzeln auf 3--5 cm falls zu dicht. | hoch |
| Jun | Aussaat + Ernte | Achtung: Schossgefahr bei Hitze + Langtag. Schattierung oder Pause erwaegen. Schossfeste Sorten waehlen. | mittel |
| Jul | Sommerpause erwaegen | Bei >25 degC und >14h Taglaenge schossen viele Sorten. Pause oder schattigen Standort waehlen. | niedrig |
| Aug | Herbstaussaat starten | Ab Mitte August wieder guenstige Bedingungen (kuerzere Tage, kuehlere Naechte). Sukzessiv nachsaeen. | hoch |
| Sep | Letzte Aussaat + Ernte | Letzte Aussaat Anfang September. Herbsternte bis Oktober. Vliesabdeckung bei fruehen Froesten. | mittel |
| Okt | Letzte Ernte | Restliche Radieschen ernten vor Dauerfrost. Beet fuer Gruenduengung oder Winter-Mulch vorbereiten. | mittel |
| Nov | -- | -- | -- |
| Dez | -- | -- | -- |

### 4.3 Ueberwinterung

Nicht anwendbar -- Radieschen sind eine schnellwuechsige Jahreskultur mit nur 3--5 Wochen Kulturdauer. Keine Ueberwinterung moeglich oder sinnvoll.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Erdfloh (Flea Beetle) | Phyllotreta spp. (P. nemorum, P. undulata, P. nigripes) | Zahlreiche kleine runde Loecher in Blaettern (Siebfrassbild), Blaetter sehen wie Schrotschuss aus | leaf | germination, seedling, vegetative | easy |
| Kleine Kohlfliege (Cabbage Root Fly) | Delia radicum | Maden in der Knolle, blaeulich-welke Blaetter, Kuemmerwuchs, weiche Stellen an der Knolle | root, stem | vegetative, ripening | medium |
| Blattlaeuse (Aphids) | Brevicoryne brassicae (Mehlige Kohlblattlaus), Myzus persicae | Kolonie-Bildung auf Blattunterseiten, Blattkraeuselung, Honigtau | leaf | seedling, vegetative | easy |
| Kohldrehherzmücke (Swede Midge) | Contarinia nasturtii | Herzblatt-Verdrehung, verkrueppeltes Wachstum, deformierte Knolle | leaf, stem | seedling, vegetative | difficult |
| Schnecken (Slugs/Snails) | Arion spp., Deroceras spp. | Schleimspuren, Loch- und Randfrassbild an Blaettern und Knollen | leaf, root | germination, seedling | easy |
| Kohlweissling-Raupe (Cabbage White) | Pieris rapae, Pieris brassicae | Frassgaenge an Blaettern, Kotkrümel, Skelettierung | leaf | vegetative | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kohlhernie (Clubroot) | protist (Plasmodiophora brassicae) | Knollige Verdickungen an Wurzeln, Welke bei Sonne, Kuemmerwuchs, Vergilbung | acidic_soil, waterlogging, warm_wet_soil | 14--21 | vegetative, ripening |
| Falscher Mehltau (Downy Mildew) | oomycete (Hyaloperonospora parasitica) | Gelbe Flecken auf Blattoberseite, grau-violetter Pilzrasen auf Blattunterseite | high_humidity, cool_wet_weather | 5--10 | seedling, vegetative |
| Alternaria-Blattflecken (Alternaria Leaf Spot) | fungal (Alternaria raphani, A. brassicicola) | Dunkelbraune runde Flecken mit konzentrischen Ringen auf Blaettern | warm_humid, rain_splash | 5--7 | vegetative |
| Schwarzfaeule (Black Rot) | bacterial (Xanthomonas campestris pv. campestris) | V-foermige Vergilbung vom Blattrand, schwarze Blattadern | warm_humid, contaminated_seed | 7--14 | vegetative |
| Umfallkrankheit (Damping Off) | fungal (Pythium spp., Rhizoctonia solani) | Saemling knickt am Stengelfuss um, verfault | waterlogging, cold_wet_soil | 3--5 | germination, seedling |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinernema feltiae (Nematode) | Kleine Kohlfliege (Bodenstadien) | 500.000/m2 | 7--14 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Aphidius colemani (Schlupfwespe) | Blattlaeuse (Myzus persicae) | 1--2 | 14--21 |
| Bacillus thuringiensis (Bt) | Kohlweissling-Raupen | Spritzung | 3--5 |
| Ferramol (Eisen-III-Phosphat) | Schnecken | 5 g/m2 | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz (Mesh 0.8 mm) | cultural | -- | Netz direkt nach Aussaat aufspannen, bis Ernte belassen | 0 | Erdfloh, Kohlfliege, Kohlweissling (effektivste Massnahme!) |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 5--7 Tage | 3 | Erdfloh, Blattlaeuse |
| Gesteinsmehl (Urgesteinsmehl) | cultural | Silikat | Blaetter bestueben, nach Regen erneuern | 0 | Erdfloh (Fraesshemmung durch raue Oberfläche) |
| Kalken (Kalkstickstoff/Calciumcarbonat) | cultural | CaCO3 | pH auf 7.0--7.5 anheben, Einarbeitung vor Aussaat | 0 | Kohlhernie (Praevention) |
| Bacillus thuringiensis (Bt kurstaki) | biological | Bt-Protein | Spritzung alle 7--10 Tage | 0 | Kohlweissling-Raupen |
| Mulchen / Schneckenzaun | cultural | -- | Beetumrandung, Sägemehl, Kaffeesatz | 0 | Schnecken |
| Heisswasser-Saatgutbehandlung | cultural | -- | Saatgut 20 Min. in 50 degC Wasser, dann trocknen | 0 | Alternaria, Schwarzfaeule (Praevention) |

### 5.5 Resistenzen der Art

Radieschen als Art haben keine bemerkenswerten Resistenzen. Aufgrund der sehr kurzen Kulturzeit (3--5 Wochen) koennen viele Krankheiten die Pflanze nicht vollstaendig befallen -- die Geschwindigkeit ist der beste Schutz.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Kohlhernie | Krankheit | Einzelne Cultivare mit Clubroot-Toleranz (z.B. Crispo F1) | `resistant_to` |
| Falscher Mehltau | Krankheit | Einzelne Cultivare (F1-Hybriden) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Kreuzbluetler (Brassicaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae -- N-Fixierung), Nachtschattengewaechse (Solanaceae), Kuerbisgewaechse (Cucurbitaceae) |
| Empfohlene Nachfrucht | Nachtschattengewaechse (Tomate, Paprika), Doldenbluetler (Moehre, Petersilie), Kuerbisgewaechse |
| Anbaupause (Jahre) | 3--4 Jahre fuer Brassicaceae auf gleicher Flaeche (Kohlhernie-Sporen ueberdauern 7+ Jahre im Boden!) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Moehre | Daucus carota | 0.9 | Klassische Mischkultur: Radieschen als Markierungssaat (keimen schnell, markieren langsam keimende Moehren-Reihen). Moehrenfliege wird durch Radieschen-Geruch irritiert. | `compatible_with` |
| Erbse | Pisum sativum | 0.9 | N-Fixierung der Erbse kommt Radieschen zugute, gute Raumnutzung | `compatible_with` |
| Buschbohne | Phaseolus vulgaris | 0.8 | N-Fixierung, Radieschen als Vorkultur geerntet bevor Bohne Platz braucht | `compatible_with` |
| Kopfsalat | Lactuca sativa | 0.8 | Kein Naehrstoffkonkurrent, gute Raumnutzung, Bodenbeschattung | `compatible_with` |
| Spinat | Spinacia oleracea | 0.8 | Aehnliche Ansprueche (kühl, feucht), Saponin-Abgabe foerdert Naehrstoffverfuegbarkeit | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Radieschen als Vorkultur im Tomatenbeet, andere Pflanzenfamilie, keine gemeinsamen Schaedlinge | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.8 | Radieschen zwischen Erdbeer-Reihen als Lueckenfueller, keine Konkurrenz | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Lockt Blattlaeuse als Opferpflanze weg von Radieschen, Bestauber anlocken | `compatible_with` |
| Mangold | Beta vulgaris subsp. vulgaris | 0.7 | Andere Familie, gute Raumnutzung | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.8 | Verschiedene Pflanzenfamilien, gute Raumnutzung, Petersilie vertreibt Erdfloh | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.6 | Gleiche Ansprueche, aber Vorsicht: gleiche Familie = gemeinsame Schaedlinge (Erdfloh!) | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Ysop | Hyssopus officinalis | Wuchshemmung durch aetherische Oele, allelopathische Wirkung | moderate | `incompatible_with` |
| Agastache (Duftnessel) | Agastache spp. | Wuchshemmung, allelopathische Wirkung | moderate | `incompatible_with` |
| Gurke | Cucumis sativus | Erhoehter Schaedlingsdruck, Naehrstoffkonkurrenz (umstritten -- einige Quellen sehen keine Probleme) | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Brassicaceae (mit sich selbst: Kohl, Rettich, Rucola, Senf, Pak Choi) | `shares_pest_risk` | Erdfloh, Kohlfliege, Kohlhernie, Falscher Mehltau, Alternaria | `shares_pest_risk` |

**Wichtig:** Niemals Radieschen nach anderen Kreuzbluetlern (Kohl, Rucola, Rettich, Senf, Meerrettich) auf die gleiche Flaeche setzen! Kohlhernie-Sporen ueberleben 7+ Jahre im Boden. Oel-Rettich als Gruenduengung zaehlt ebenfalls als Kreuzbluetler und verletzt die Anbaupause!

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Radieschen |
|-----|-------------------|-------------|------------------------------|
| Rettich (weiss/schwarz) | Raphanus sativus var. niger / var. longipinnatus | Gleiche Art, groessere Wurzelknolle | Laenger lagerfaehig (Winterrettich), mehr Ertrag pro Pflanze |
| Mairübe (Navet) | Brassica rapa subsp. rapa | Gleiche Familie, aehnliche Kultur | Groessere Knolle, vielseitigere Verwendung (roh + gekocht) |
| Teltower Ruebchen | Brassica rapa subsp. rapa (Teltower Gruppe) | Gleiche Familie, kleine Knolle | Delikatesse, nussiger Geschmack |
| Kohlrabi | Brassica oleracea var. gongylodes | Gleiche Familie, Sprossknollen-Gemuese | Groesser, laenger lagerfaehig, mehr Naehrstoffe |
| Rote Bete | Beta vulgaris subsp. vulgaris | Aehnliche Nutzung (runde Knolle, roh/gekocht) | Andere Familie (keine Kohlhernie), hoeherer Naehrwert, laenger lagerfaehig |
| Kresse (Gartenkresse) | Lepidium sativum | Gleiche Familie, aehnlich schnelle Kultur | Noch schneller (7--10 Tage), Indoor-Fensterbank-Kultur |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Raphanus sativus var. sativus,Radieschen;Radish;Monatsrettich,Brassicaceae,Raphanus,annual,long_day,herb,taproot,2a;3a;4a;5a;6a;7a;8a;9a;10a,0.1,"Vorderasien, oestlicher Mittelmeerraum",yes,3,15,15-25,8-15,5,limited,yes,false,false,light_feeder,hardy,3;4;5;6;7;8;9,4;5;6;7;8;9;10
```

### 8.2 BotanicalFamily CSV (falls noetig)

```csv
name,order,description
Brassicaceae,Brassicales,"Kreuzbluetler -- grosse Familie mit ca. 3.700 Arten, darunter Kohl, Rettich, Raps, Senf, Rucola. Viele wichtige Gemuesepflanzen. Gemeinsames Merkmal: Glucosinolate (Senfoele). Anfaellig fuer Kohlhernie und Erdfloh."
```

Hinweis: Brassicaceae ist moeglicherweise bereits als Botanical Family in Kamerplanter vorhanden (z.B. ueber Brassica oleracea Kohl-Arten). Vor Import pruefen!

### 8.3 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Cherry Belle,Raphanus sativus var. sativus,,1949,round;red;fast_maturing;bolt_resistant,22,none,open_pollinated
Saxa 3,Raphanus sativus var. sativus,,~1900,round;red;early;compact,25,none,open_pollinated
Riesenbutter,Raphanus sativus var. sativus,,,round;red;large_bulb;mild,30,none,open_pollinated
French Breakfast 3,Raphanus sativus var. sativus,,~1880,elongated;red_white;aromatic;classic,28,none,open_pollinated
Eiszapfen (White Icicle),Raphanus sativus var. sativus,,,elongated;white;mild_peppery;long_root,35,none,open_pollinated
Pernot,Raphanus sativus var. sativus,,,round;red;bolt_resistant;summer_suitable,25,none,open_pollinated
Sora,Raphanus sativus var. sativus,,,round;red;uniform;commercial,24,downy_mildew_tolerance,open_pollinated
Rudi,Raphanus sativus var. sativus,,,round;red;bolt_resistant;autumn_suitable,28,none,open_pollinated
Viola,Raphanus sativus var. sativus,,,round;purple;decorative;mild,28,none,open_pollinated
Zlata,Raphanus sativus var. sativus,,,round;yellow;mild;unusual_color,30,none,open_pollinated
```

---

## Quellenverzeichnis

1. PFAF (Plants For A Future) -- Raphanus sativus: https://pfaf.org/user/plant.aspx?LatinName=Raphanus+sativus
2. RHS (Royal Horticultural Society) -- Growing radishes: https://www.rhs.org.uk/vegetables/radishes/grow-your-own
3. USDA Plant Guide -- Raphanus sativus: https://plants.usda.gov/DocumentLibrary/plantguide/pdf/pg_rasa2.pdf
4. Utah State Extension -- Radishes in the Garden: https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=1287&context=extension_curall
5. UMN Extension -- Growing Radishes: https://extension.umd.edu/resource/growing-radishes-home-garden
6. Hortipendium -- Radieschen und Rettich Pflanzenschutz: https://www.hortipendium.de/Radieschen_und_Rettich_Pflanzenschutz
7. Plantura -- Radieschensorten: https://www.plantura.garden/gemuese/radieschen/radieschensorten
8. COMPO -- Radieschen saeen & ernten: https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/radieschen
9. fryd.app -- Mischkultur mit Radieschen: https://samen.de/blog/mischkultur-mit-radieschen-erfolgreicher-gemueseanbau.html
10. Koppert Biological Systems -- Cruciferous crop pests: https://www.koppertbio.at/
11. PSU PlantVillage -- Radish diseases: https://plantvillage.psu.edu/topics/radish/infos
12. Gardening Know How -- Radish diseases: https://www.gardeningknowhow.com/edible/vegetables/radish/treating-radish-diseases.htm
13. PNW Pest Management Handbooks -- Radish downy mildew: https://pnwhandbooks.org/plantdisease/host-disease/radish-raphanus-sativus-downy-mildew
14. IGWorks -- Hydroponic Radish: https://igworks.com/blogs/growing-guides/growing-hydroponic-radish
15. Almanac -- How to Grow Radishes: https://www.almanac.com/plant/radishes
