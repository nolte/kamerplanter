# Naehrstoffplan: Spathiphyllum wallisii -- Gardol Gruenpflanzenduenger

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Spathiphyllum wallisii (light_feeder, perennial, Indoor/Erde)
> **Produkt:** Gardol Gruenpflanzenduenger NPK 6-4-6 (Bauhaus)
> **Erstellt:** 2026-03-01
> **Quellen:** spec/ref/plant-info/spathiphyllum_wallisii.md, spec/ref/products/gardol_gruenpflanzenduenger.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Spathiphyllum wallisii -- Gardol Gruenpflanzenduenger | `nutrient_plans.name` |
| Beschreibung | Ganzjahresplan fuer Spathiphyllum wallisii (Einblatt) in Erdsubstrat. Einzelduenger-Konzept mit Gardol Gruenpflanzenduenger (NPK 6-4-6) in halber Dosis. Saisonaler Rhythmus: Maerz--Oktober Duengung (halbe Dosis, 21-Tage-Intervall), November--Februar Pause. Schwachzehrer -- EC unter 1,0 mS/cm halten, Ueberdüngung ist der haeufigste Pflegefehler. GIFTIG fuer Katzen, Hunde und Kinder. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | spathiphyllum, einblatt, peace-lily, zimmerpflanze, gruenpflanze, gardol, erde, indoor, anfaenger, schwachzehrer, schattenvertraeglich | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (100% Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |

<!-- SP-001: Ca/Mg-Versorgung wird bei null (= Leitungswasser) durch das Wasser selbst gedeckt (dt. Durchschnitt ~100 ppm Ca, 15 ppm Mg). Bei RO-/Regenwasser ist ein CalMag-Supplement erforderlich. Spathiphyllum ist chlor- und fluoridempfindlich -- abgestandenes Leitungswasser oder Regenwasser bevorzugen. -->
| Zyklus-Neustart ab Sequenz | 2 (VEGETATIVE) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 7 | `watering_schedule.interval_days` |
| Uhrzeit | 09:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Der Giessplan gilt als Basis. In der Etablierungsphase (GERMINATION) verkuerzt sich das Intervall auf 5 Tage, in der Ruheperiode (DORMANCY) verlaengert es sich auf 9 Tage ueber den `watering_schedule_override` der Phase-Entry. Spathiphyllum zeigt Welke (haengende Blaetter) als natuerliches Durst-Signal -- Pflanze erholt sich nach dem Giessen innerhalb weniger Stunden. Trotzdem nicht warten bis zur Welke, da wiederholter Trockenstress die Pflanze schwaecht. Chlor- und fluoridempfindlich: abgestandenes Leitungswasser (mind. 24h) oder Regenwasser verwenden.

---

## 2. Phasen-Mapping

Spathiphyllum wallisii ist eine perenniale tropische Zimmerpflanze. Sie ist einer der wenigen Schwachzehrer, die bei wenig Licht zur Bluete kommen koennen. Die Spathiphyllum-spezifischen Wachstumsphasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Spathiphyllum-Phase | PhaseName (Enum) | Wochen | Zeitraum | Begruendung | is_recurring |
|---------------------|-----------------|--------|----------|-------------|-------------|
| Etablierung (nach Teilung/Kauf) | GERMINATION | 1--4 | Nach Teilung/Kauf | Pflanze etabliert Wurzeln nach Teilung oder Standortwechsel, keine Duengung. GERMINATION als Platzhalter fuer vegetative Vermehrung (Teilung, kein separates PROPAGATION-Enum). | false |
| Aktives Wachstum | VEGETATIVE | 5--36 | Saisonal, Maerz--Oktober | Hauptwachstumsphase mit halber Dosis Gardol alle 21 Tage | true |
| Bluete | FLOWERING | 37--44 | Innerhalb der Wachstumssaison, optional | Optionale Bluetephase bei ausreichend indirektem Licht. Gardol 6-4-6 ist akzeptabel (ideales NPK waere 2:3:2, Abweichung fuer Erdkultur tolerierbar). Halbe Dosis beibehalten. | true |
| Ruheperiode | DORMANCY | 45--62 | Saisonal, November--Februar | Kulturpraktische Ruhephase bei reduziertem Winterlicht, keine obligate Dormanz (dormancy_required: false). Keine Duengung, reduzierte Bewaesserung. | true |

**Nicht genutzte Phasen:**
- **SEEDLING:** Spathiphyllum wird durch Teilung vermehrt, nicht aus Samen -- eine separate Jungpflanzenphase entfaellt. Geteilte Pflanzen sind bereits adult und gehen nach Etablierung direkt in VEGETATIVE.
- **FLUSHING:** Kein aktives Flushing noetig (Erdsubstrat, kein Hydro-Pre-Harvest). Stattdessen regelmaessige Substratspuelung (alle 2--3 Monate).
- **HARVEST:** Keine Ernte (Zierpflanze).

**Saisonaler Zyklus:** Nach dem Erstdurchlauf (Woche 1--62) wiederholen sich VEGETATIVE, FLOWERING (optional) und DORMANCY jaehrlich (`cycle_restart_from_sequence: 2`). Die einmalige Anfangsphase (GERMINATION) wird nur beim Erstdurchlauf durchlaufen. FLOWERING ist in jedem Jahreszyklus optional -- die Bluete tritt nur bei ausreichend Licht ein (DLI > 5 mol/m2/Tag ueber mehrere Wochen).

**Lueckenlos-Pruefung:** 1--4 | 5--36 | 37--44 | 45--62 (4 + 32 + 8 + 18 = 62 Wochen, keine Luecken)

---

## 3. Delivery Channels

Zwei DRENCH-Kanaele: ein Nur-Wasser-Kanal fuer die Etablierungsphase und ein Duengungskanal fuer die aktiven Phasen.

### 3.1 Channel: wasser-etablierung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-etablierung | `delivery_channels.channel_id` |
| Label | Nur Wasser (Etablierung) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Nur klares, abgestandenes Wasser, kein Duenger. DRENCH = von oben giessen (entspricht top_water-Methode aus dem Pflegeprofil). Kein frisches Leitungswasser -- Chlor-/Fluoridempfindlichkeit. | `delivery_channels.notes` |

#### DRENCH-Parameter (DrenchParams)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Giessen (L) | 0.2 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 0,2 L Giesswasser fuer eine frisch geteilte oder neu gekaufte Spathiphyllum (Topf 12--15 cm). Substrat gleichmaessig feucht halten, nicht nass -- Staunaesse fuehrt bei Spathiphyllum schnell zu Rhizomfaeule.

### 3.2 Channel: drench-giessduengung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | drench-giessduengung | `delivery_channels.channel_id` |
| Label | Giessduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Duenger ins Giesswasser einruehren, nur auf feuchtes Substrat giessen. DRENCH = Duenger im Giesswasser von oben ausbringen (entspricht top_water-Methode aus dem Pflegeprofil). Abgestandenes Leitungswasser oder Regenwasser verwenden. | `delivery_channels.notes` |

#### DRENCH-Parameter (DrenchParams)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Duengung (L) | 0.4 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 0,4 L Giessloessung pro Duengung fuer eine mittelgrosse, etablierte Spathiphyllum (Topf 14--18 cm). Bei groesseren Exemplaren (20+ cm Topf, Sorte 'Sensation') auf 0,6--0,8 L erhoehen.

---

## 4. Dosierung pro Phase

### EC-Beitrag Gardol Gruenpflanzenduenger

Geschaetzter EC-Beitrag: **~0,06 mS/cm pro ml/L** (Herstellerangabe fehlt, Schaetzung basierend auf NPK 6-4-6 und mineralischer Formulierung). **Status: nicht am physischen Produkt verifiziert.** Tatsaechlicher EC-Beitrag koennte bis 0,10 mS/cm/ml/L betragen. EC-Zielwerte konservativ auf 0,5 mS/cm gesetzt, um bei hartem Leitungswasser Spielraum zu lassen.

| Dosierung | ml/L | EC-Beitrag (geschaetzt) |
|-----------|------|-------------------------|
| Viertel-Dosis | 1,0 | ~0,06 mS/cm |
| Halbe Dosis | 2,0 | ~0,12 mS/cm |
| Volle Dosis | 4,0 | ~0,24 mS/cm |

**Dosierungsreferenz:** Die Gardol-Packungsbeilage empfiehlt fuer Zimmerpflanzen "1/4 Dosierkappe auf 5 L Wasser" (~1 ml/L). Die in diesem Plan verwendete "halbe Dosis" (2 ml/L) entspricht der doppelten Hersteller-Zimmerpflanzendosis. Aufgrund des sehr geringen EC-Beitrags von ~0,06 mS/cm pro ml/L ist dies fuer Spathiphyllum vertretbar und bleibt sicher unter der 1,0-mS/cm-Grenze.

**WICHTIG -- Schwachzehrer-Grenze:** Spathiphyllum ist ein Schwachzehrer. Die Gesamt-EC der Giessloessung (Basis-Wasser + Duenger) darf **1,0 mS/cm nicht ueberschreiten**. Bei Leitungswasser mit typisch 0,3--0,7 mS/cm bedeutet das maximal halbe Dosis (2 ml/L, EC-Beitrag ~0,12 mS/cm). EC ueber 1,0 mS/cm verursacht Blattrandnekrosen (braune Blattspitzen) -- dies ist der haeufigste Pflegefehler bei Spathiphyllum. Im Gegensatz zur Monstera (medium_feeder, volle Dosis moeglich) wird bei Spathiphyllum **immer** nur halbe Dosis verwendet.

### 4.1 GERMINATION -- Etablierung (Woche 1--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Frisch geteilte oder neu gekaufte Pflanze nur mit klarem, abgestandenem Wasser giessen. Substrat gleichmaessig feucht halten, nicht nass -- Staunaesse fuehrt bei Spathiphyllum schnell zu Rhizomfaeule (Phytophthora). 5-Tage-Intervall bei 20--24 C. In kuehlen Raeumen (18 C) auf 7 Tage verlaengern. Fingerprobe vorrangig: obere 2--3 cm feucht = kein Giessen noetig. Welke-Signal beachten, aber nicht provozieren. Nach Teilung: frische Schnittstellen 1h antrocknen lassen, Handschuhe tragen (Calciumoxalat). | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (Substrat gleichmaessig feucht, Richtwert fuer warme Bedingungen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-etablierung**

| Feld | Wert |
|------|------|
| channel_id | wasser-etablierung |
| application_method | drench |
| target_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| target_ph | 6.0 (Substrat-pH-Optimum 5,5--6,5; Leitungswasser muss fuer Erdkultur nicht pH-korrigiert werden) |
| fertilizer_dosages | [] (leer) |

### 4.2 VEGETATIVE -- Aktives Wachstum (Woche 5--36)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 36 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1.5, 1, 1.5) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 40 (aus Leitungswasser, nicht Gardol) | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 20 (aus Leitungswasser, nicht Gardol) | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis (2 ml/L) alle 21 Tage. NPK-Zielverhaeltnis aus Steckbrief 3:1:2 -- Gardol liefert 1,5:1:1,5 (6-4-6), Abweichung fuer Erdkultur bei Schwachzehrern akzeptabel. Ca 40 ppm und Mg 20 ppm werden bei mittelhartem Leitungswasser automatisch gedeckt -- Gardol liefert kein Ca/Mg. Bei weichem Wasser oder Osmosewasser CalMag-Supplement (0,3 ml/L) erforderlich, dabei EC-Grenze 1,0 mS/cm einhalten. Eisen-Zielwert: 1 ppm (aus Gardol-Spurenelementen und Leitungswasser). Bei Chlorose-Symptomen (intervenoese Blattvergilbung, Blaetter vergilben zwischen den Adern) Fe-EDTA-Chelat supplementieren (0,1 ml/L). Im Maerz mit Viertel-Dosis (1 ml/L) starten, ab April halbe Dosis. Im Oktober auf Viertel-Dosis reduzieren. Alle 2--3 Monate Substratspuelung mit 2x Topfvolumen klarem Wasser (Salzspuelung). Bei braunen Blattspitzen zuerst Ueberdüngung pruefen, dann Luftfeuchtigkeit, dann Wasserqualitaet (Chlor/Fluor). | `phase_entries.notes` |

**Delivery Channel: drench-giessduengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| target_ph | 6.0 (Substrat-pH-Optimum 5,5--6,5) |
| Gardol ml/L | 2.0 (halbe Dosis) |
| EC-Beitrag | ~0,12 mS/cm |
| Gardol optional | false |

**Hinweis:** Im Uebergang (Maerz, Oktober) Viertel-Dosis (1 ml/L) verwenden. Siehe Jahresplan in Abschnitt 5 fuer monatsweise Abstufung. EC-Zielwert 0,5 mS/cm bezieht sich auf die Gesamtloesung inkl. Basis-Wasser-EC (konservativ gesetzt, da EC-Beitrag von Gardol nicht verifiziert). Bei Leitungswasser mit 0,3--0,4 mS/cm ergibt halbe Dosis Gardol ca. 0,4--0,5 mS/cm gesamt -- sicher unter der 1,0-mS/cm-Grenze.

### 4.3 FLOWERING -- Bluete (Woche 37--44)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 37 | `phase_entries.week_start` |
| week_end | 44 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1.5, 1, 1.5) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 40 (aus Leitungswasser, nicht Gardol) | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 25 (aus Leitungswasser, erhoehter Bedarf in der Bluetephase) | `phase_entries.magnesium_ppm` |
| Hinweise | Optionale Phase -- tritt nur bei ausreichend indirektem Licht ein (DLI > 5 mol/m2/Tag ueber mehrere Wochen). Im System event-basiert ausgeloest (nicht streng sequenziell) -- die Wochennummern 37--44 dienen als Fallback-Zeitfenster, falls kein Lichtsensor den DLI-Trigger meldet. Biologischer Bluetezeitraum: April--August. Halbe Dosis (2 ml/L) alle 21 Tage beibehalten. NPK-Ideal fuer Bluete waere 2:3:2 (erhoehtes P), aber Gardol 6-4-6 (1,5:1:1,5) ist akzeptabel -- der Bluetenausloeser bei Spathiphyllum ist primaer das Lichtniveau, nicht die Duengung. Wer optimale Blutenbedingungen anstrebt: Im Fruehjahr (Maerz--April) 4--6 Wochen lang auf einen Bluetenduenger mit erhoehtem P-Anteil wechseln (z.B. COMPO Bluetenduenger NPK 3-4-5, halbe Dosis), danach zurueck auf Gardol. Eisen-Zielwert: 1 ppm (aus Gardol-Spurenelementen und Leitungswasser). Bei Chlorose-Symptomen (intervenoese Blattvergilbung) Fe-EDTA-Chelat supplementieren (0,1 ml/L). Mg erhoht auf 25 ppm (Steckbrief-Vorgabe Bluetephase) -- Mg ist Zentralatom des Chlorophylls und Cofaktor der ATP-Synthase, erhoehter Bedarf fuer Bluetensynthese. Bei kommerziellem Anbau wird Gibberellinsaeure (GA3) zur Blueteinduktion eingesetzt -- im Hobbybereich nicht erforderlich. Verblühte Bluetenstaende an der Basis abschneiden. Pollenallergie-Hinweis: Spadix produziert Pollen, bei Allergikern vor dem Oeffnen entfernen. | `phase_entries.notes` |

**Delivery Channel: drench-giessduengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| target_ph | 6.0 (Substrat-pH-Optimum 5,5--6,5) |
| Gardol ml/L | 2.0 (halbe Dosis) |
| EC-Beitrag | ~0,12 mS/cm |
| Gardol optional | false |

### 4.4 DORMANCY -- Ruheperiode (Woche 45--62)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 45 | `phase_entries.week_start` |
| week_end | 62 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Saisonale Ruhephase November--Februar (kulturpraktisch, keine obligate Dormanz). Keine Duengung. 9-Tage-Intervall bei normaler Raumtemperatur (18--22 C). Spathiphyllum ist kaelteempfindlicher als Monstera -- Minimum 15 C, nicht unter 13 C. Bei kuehlen Winterstandorten (15--18 C) Giessintervall auf 10--12 Tage verlaengern. Fingerprobe vorrangig: obere 2--3 cm Substrat trocken = giessen. Substratspuelung zu Beginn der Ruhephase (November) mit 2x Topfvolumen klarem Wasser, um Salzreste der Aktivsaison auszuwaschen. Standort-Lichtcheck: bei sehr dunklem Winterstandort naeher ans Fenster ruecken (Nord- oder Ostfenster ausreichend). Luftfeuchtigkeit pruefen -- trockene Heizungsluft verursacht braune Blattspitzen, Luftbefeuchter oder Kiesbett empfohlen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 9 Tage (Richtwert bei 18--22 C; bei 15--18 C auf 10--12 Tage erhoehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, Nur-Wasser-Channel fuer Giessplan

| Feld | Wert |
|------|------|
| channel_id | wasser-etablierung |
| application_method | drench |
| target_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| target_ph | 6.0 (Substrat-pH-Optimum, nicht Giesswasser-pH) |
| fertilizer_dosages | [] (leer) |

---

## 5. Jahresplan (Monat-fuer-Monat)

Basierend auf einer etablierten Spathiphyllum (ab Jahr 2, saisonaler Zyklus VEGETATIVE / FLOWERING / DORMANCY).

| Monat | KA-Phase | Gardol ml/L | EC-Beitrag | Frequenz | Giessmenge (ml) | Aktion |
|-------|----------|-------------|------------|----------|-----------------|--------|
| Januar | DORMANCY | 0 | 0,00 | -- | 150--200 | Keine Duengung, Substrat trockener halten, Luftfeuchtigkeit pruefen |
| Februar | DORMANCY | 0 | 0,00 | -- | 150--200 | Keine Duengung, Licht nimmt langsam zu, ggf. Standort optimieren |
| Maerz | VEGETATIVE | 1,0 | ~0,06 | 21-taegig | 200--300 | Duengung starten mit Viertel-Dosis |
| April | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--400 | Halbe Dosis, Umtopfen wenn noetig (alle 18 Monate) |
| Mai | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--400 | Halbe Dosis, Hauptwachstum |
| Juni | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--400 | Halbe Dosis, Salzspuelung |
| Juli | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--400 | Halbe Dosis, moegliche Bluete |
| August | FLOWERING/VEG | 2,0 | ~0,12 | 21-taegig | 200--400 | Halbe Dosis, verblühte Bluetenstaende entfernen |
| September | FLOWERING/VEG | 2,0 | ~0,12 | 21-taegig | 200--300 | Halbe Dosis, letzte Vollduengung |
| Oktober | VEGETATIVE | 1,0 | ~0,06 | 21-taegig | 200--300 | Viertel-Dosis, Salzspuelung, Uebergang zur Ruhe |
| November | DORMANCY | 0 | 0,00 | -- | 150--250 | Duengung einstellen, Substratspuelung (2x Topfvolumen klares Wasser) |
| Dezember | DORMANCY | 0 | 0,00 | -- | 150--200 | Keine Duengung, minimale Bewaesserung |

**Salzspuelungen (3x/Jahr):** Juni (Mitte Aktivsaison), Oktober (Ende Aktivsaison), November (Start Ruhephase). Jeweils 2x normales Giessvolumen mit klarem, abgestandenem Wasser ohne Duenger. Drainagewasser pruefen -- wenn weiss/trueb: zusaetzliche Spuelung noetig. Salzspuelungen sind bei Schwachzehrern besonders wichtig, da bereits geringe Akkumulation zu Blattschaeden fuehrt. Symptome von Salzakkumulation: weisse Krusten auf Erdoberflaeche, braune Blattspitzen, verlangsamtes Wachstum trotz Duengung.

**Jahresverbrauch (geschaetzt):** Bei einer Pflanze und 0,4 L Giessloessung pro Duengung:

- Halbe Dosis (Apr--Sep): 6 Monate, 21-Tage-Intervall = ca. 8 Duengungen x 0,4 L x 2 ml/L = **6,4 ml**
- Viertel-Dosis (Maerz, Okt): 2 Monate, 21-Tage-Intervall = ca. 3 Duengungen x 0,4 L x 1 ml/L = **1,2 ml**
- **Gesamt: ~7,6 ml/Jahr** -- 1 L Flasche reicht fuer ca. 130 Spathiphyllum-Jahre (ca. 10 Pflanzen fuer 13 Jahre)

```
Monat:       |Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:    |DOR|DOR|VEG|VEG|VEG|VEG|VEG|FLO|FLO|VEG|DOR|DOR|
Gardol:      |---|---|...|###|###|###|###|###|###|...|---|---|
                   Viertel halb              halb Viertel
                   Dosis   Dosis             Dosis Dosis

Legende: --- = keine Duengung, ... = Viertel-Dosis (1 ml/L), ### = halbe Dosis (2 ml/L)
         DOR = DORMANCY, VEG = VEGETATIVE, FLO = FLOWERING (optional)
```

---

## 6. KA-Import-Daten

### 6.1 NutrientPlan

```json
{
  "name": "Spathiphyllum wallisii \u2014 Gardol Gr\u00fcnpflanzend\u00fcnger",
  "description": "Ganzjahresplan f\u00fcr Spathiphyllum wallisii (Einblatt) in Erdsubstrat. Einzeld\u00fcnger-Konzept mit Gardol Gr\u00fcnpflanzend\u00fcnger (NPK 6-4-6) in halber Dosis. Saisonaler Rhythmus: M\u00e4rz\u2013Oktober D\u00fcngung (21-Tage-Intervall), November\u2013Februar Pause. Schwachzehrer \u2014 EC unter 1,0 mS/cm halten. GIFTIG f\u00fcr Katzen, Hunde und Kinder.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["spathiphyllum", "einblatt", "peace-lily", "zimmerpflanze", "gruenpflanze", "gardol", "erde", "indoor", "anfaenger", "schwachzehrer", "schattenvertraeglich"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 2,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 7,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 6.2 NutrientPlanPhaseEntry (4 Eintraege)

#### GERMINATION

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Frisch geteilte oder neu gekaufte Pflanze nur mit klarem, abgestandenem Wasser gie\u00dfen. Substrat gleichm\u00e4\u00dfig feucht halten, nicht nass \u2014 Staun\u00e4sse f\u00fchrt bei Spathiphyllum schnell zu Rhizomf\u00e4ule (Phytophthora). 5-Tage-Intervall bei 20\u201324 \u00b0C. In k\u00fchlen R\u00e4umen (18 \u00b0C) auf 7 Tage verl\u00e4ngern. Fingerprobe vorrangig. Nach Teilung: frische Schnittstellen 1h antrocknen lassen, Handschuhe tragen (Calciumoxalat).",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 5,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-etablierung",
      "label": "Nur Wasser (Etablierung)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares, abgestandenes Wasser, kein D\u00fcnger. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode). Chlor-/fluoridempfindlich \u2014 Leitungswasser mind. 24h abstehen lassen.",
      "target_ec_ms": null,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.20
      }
    }
  ]
}
```

#### VEGETATIVE

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 2,
  "week_start": 5,
  "week_end": 36,
  "is_recurring": true,
  "npk_ratio": [1.5, 1.0, 1.5],
  "calcium_ppm": 40.0,
  "magnesium_ppm": 20.0,
  "notes": "Halbe Dosis (2 ml/L) alle 21 Tage. NPK-Ziel 3:1:2 (Steckbrief) \u2014 Gardol liefert 1,5:1:1,5 (6-4-6), Abweichung f\u00fcr Erdkultur bei Schwachzehrern akzeptabel. Ca/Mg aus Leitungswasser (nicht aus Gardol) \u2014 bei weichem Wasser/RO CalMag-Supplement (0,3 ml/L) erforderlich, EC-Grenze 1,0 mS/cm einhalten. Im M\u00e4rz Vierteldosis (1 ml/L), ab April halbe Dosis, im Oktober zur\u00fcck auf Vierteldosis. Alle 2\u20133 Monate Salzsp\u00fclung (2x Topfvolumen klares Wasser). Bei braunen Blattspitzen: 1. \u00dcberd\u00fcngung, 2. trockene Luft, 3. Chlor/Fluor im Wasser pr\u00fcfen.",
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode). Abgestandenes Leitungswasser oder Regenwasser verwenden.",
      "target_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 2.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.4
      }
    }
  ]
}
```

#### FLOWERING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flowering",
  "sequence_order": 3,
  "week_start": 37,
  "week_end": 44,
  "is_recurring": true,
  "npk_ratio": [1.5, 1.0, 1.5],
  "calcium_ppm": 40.0,
  "magnesium_ppm": 25.0,
  "notes": "Optionale Phase \u2014 tritt nur bei ausreichend indirektem Licht ein (DLI > 5 mol/m\u00b2/Tag). Im System event-basiert ausgel\u00f6st (nicht streng sequenziell) \u2014 Wochennummern 37\u201344 als Fallback-Zeitfenster. Biologischer Bl\u00fctezeitraum: April\u2013August. Halbe Dosis (2 ml/L) alle 21 Tage beibehalten. NPK-Ideal f\u00fcr Bl\u00fcte w\u00e4re 2:3:2 (erh\u00f6htes P), aber Gardol 6-4-6 ist akzeptabel \u2014 Bl\u00fctenausl\u00f6ser ist prim\u00e4r das Lichtniveau. F\u00fcr optimale Bl\u00fcte: Im Fr\u00fchjahr 4\u20136 Wochen Bl\u00fctenduenger (z.B. COMPO NPK 3-4-5, halbe Dosis). Eisen-Zielwert: 1 ppm (Gardol-Spurenelemente + Leitungswasser). Fe-EDTA bei Chlorose (0,1 ml/L). Mg erh\u00f6ht auf 25 ppm (Steckbrief-Vorgabe Bl\u00fctephase). Verbl\u00fchte Bl\u00fctenst\u00e4nde an der Basis abschneiden. Pollenallergie: Spadix bei Allergikern vor dem \u00d6ffnen entfernen.",
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode). Abgestandenes Leitungswasser oder Regenwasser verwenden.",
      "target_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 2.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.4
      }
    }
  ]
}
```

#### DORMANCY

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "dormancy",
  "sequence_order": 4,
  "week_start": 45,
  "week_end": 62,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Saisonale Ruhephase November\u2013Februar (kulturpraktisch, keine obligate Dormanz). Keine D\u00fcngung. 9-Tage-Intervall bei 18\u201322 \u00b0C, bei 15\u201318 \u00b0C auf 10\u201312 Tage verl\u00e4ngern. Minimum 15 \u00b0C (k\u00e4lteempfindlicher als Monstera). Fingerprobe: obere 2\u20133 cm trocken = gie\u00dfen. Substratsp\u00fclung einmalig im November (2x Topfvolumen klares Wasser). Luftfeuchtigkeit pr\u00fcfen \u2014 trockene Heizungsluft verursacht braune Blattspitzen.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 9,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-etablierung",
      "label": "Nur Wasser (Ruheperiode)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares, abgestandenes Wasser, kein D\u00fcnger. Reduziertes Volumen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": null,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.2
      }
    }
  ]
}
```

### 6.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Gardol Gruenpflanzenduenger | `spec/ref/products/gardol_gruenpflanzenduenger.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Spathiphyllum wallisii | `spec/ref/plant-info/spathiphyllum_wallisii.md` | Via `nutrient_plans` -> `uses_nutrient_plan` edge |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 7. Sicherheitshinweise

<!-- SP-010: Toxizitaetswarnung im Duengekontext -->

**Toxizitaet:** Spathiphyllum wallisii ist **GIFTIG** fuer Katzen, Hunde und Kinder (Calciumoxalat-Raphiden, Schweregrad moderat). Im Duengekontext beachten:

- **Drainage-Wasser:** Giessloessung mit Duenger in der Unterschale von Haustieren fernhalten (Trinken kann zu Magen-Darm-Reizung fuehren). Drainage-Wasser nach 30 Minuten entfernen.
- **Umtopfen und Teilung:** Handschuhe tragen -- Pflanzensaft enthaelt Calciumoxalat-Raphiden (nadelfoermige Kristalle) und kann Kontaktdermatitis und brennendes Gefuehl auf der Haut ausloesen. Besonders bei der Teilung (Vermehrungsmethode) wird Pflanzensaft freigesetzt. Hinweis: Calciumoxalat-Raphiden sind mechanische Irritanzien (keine immunologischen Allergene im Sinne einer IgE-vermittelten Reaktion) -- der Steckbrief setzt daher `contact_allergen: false`, was technisch korrekt ist, obwohl Hautreizungen auftreten koennen.
- **Symptome bei Verschlucken (Mensch):** Brennen und Schwellung im Mund- und Rachenraum, Speichelfluss, Schluckbeschwerden, Erbrechen. Bei Kindern sofort Giftnotrufzentrale kontaktieren.
- **Symptome bei Haustieren:** Orale Reizung, Pfoten am Maul reiben, Speichelfluss, Appetitlosigkeit, Erbrechen. Giftnotrufzentrale fuer Tiere kontaktieren.
- **Pollen:** Die Bluetenkolben (Spadix) produzieren Pollen, der bei empfindlichen Personen allergische Reaktionen ausloesen kann. In Haushalten mit Pollenallergikern: Bluetenkolben vor dem Oeffnen abschneiden.
- **Gardol-Konzentrat:** Mineralischer Fluessigduenger -- bei versehentlichem Kontakt durch Haustiere oder Kinder Giftnotrufzentrale kontaktieren. Flasche ausserhalb der Reichweite von Kindern und Haustieren aufbewahren.

**Giftnotrufzentralen (Deutschland):**
- Berlin: 030 19240
- Muenchen: 089 19240
- Bonn: 0228 19240

Die Toxizitaetsdaten der Pflanze sind im Steckbrief dokumentiert (vgl. `spec/ref/plant-info/spathiphyllum_wallisii.md`, Abschnitt 1.4).

---

## Quellenverzeichnis

1. Spathiphyllum wallisii Pflanzensteckbrief: `spec/ref/plant-info/spathiphyllum_wallisii.md`
2. Gardol Gruenpflanzenduenger Produktdaten: `spec/ref/products/gardol_gruenpflanzenduenger.md`
3. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
4. PhaseName Enum: `src/backend/app/common/enums.py`
5. ASPCA Animal Poison Control -- Peace Lily: https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants/peace-lily

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
