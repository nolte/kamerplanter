# Naehrstoffplan: Chlorophytum comosum -- Gardol Gruenpflanzenduenger

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Chlorophytum comosum (light_feeder, perennial, Indoor/Erde)
> **Produkt:** Gardol Gruenpflanzenduenger NPK 6-4-6 (Bauhaus)
> **Erstellt:** 2026-03-01
> **Quellen:** spec/ref/plant-info/chlorophytum_comosum.md, spec/ref/products/gardol_gruenpflanzenduenger.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Chlorophytum comosum -- Gardol Gruenpflanzenduenger | `nutrient_plans.name` |
| Beschreibung | Ganzjahresplan fuer Chlorophytum comosum (Gruenlilie) in Erdsubstrat. Einzelduenger-Konzept mit Gardol Gruenpflanzenduenger (NPK 6-4-6). Schwachzehrer -- reduzierte Dosierung gegenueber Herstellerangabe. Saisonaler Rhythmus: Maerz--Oktober Duengung (halbe Dosis), November--Februar Pause. Fluorid-empfindlich: abgestandenes Leitungswasser oder Regenwasser bevorzugt. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | gruenlilie, spider-plant, zimmerpflanze, gruenpflanze, gardol, erde, indoor, anfaenger, schwachzehrer | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (100% Leitungswasser, abgestanden) | `nutrient_plans.water_mix_ratio_ro_percent` |

<!-- GL-001: Ca/Mg-Versorgung wird bei null (= Leitungswasser) durch das Wasser selbst gedeckt (dt. Durchschnitt ~100 ppm Ca, 15 ppm Mg). Bei RO-/Regenwasser ist ein CalMag-Supplement erforderlich. Abgestandenes Leitungswasser bevorzugt wegen Fluorid-/Chlor-Empfindlichkeit der Gruenlilie. -->
| Zyklus-Neustart ab Sequenz | 3 (VEGETATIVE) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 7 | `watering_schedule.interval_days` |
| Uhrzeit | 09:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Der Giessplan gilt als Basis. In der Bewurzelung (GERMINATION) verkuerzt sich das Intervall auf 3 Tage (kleine Toepfe, Substrat feucht halten). In der Ruheperiode (DORMANCY) verlaengert sich das Intervall auf 12 Tage ueber den `watering_schedule_override` der Phase-Entry. Wasser vor dem Giessen mindestens 24 Stunden abstehen lassen, damit Chlor und Fluorid ausgasen -- Chlorophytum comosum reagiert empfindlich auf Fluorid (braune Blattspitzen).

---

## 2. Phasen-Mapping

Chlorophytum comosum ist eine perenniale tropische Zimmerpflanze mit geringem Naehrstoffbedarf (Schwachzehrer). Die Gruenlilie-spezifischen Wachstumsphasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Gruenlilie-Phase | PhaseName (Enum) | Wochen | Zeitraum | Begruendung | is_recurring |
|------------------|-----------------|--------|----------|-------------|-------------|
| Bewurzelung (Kindel/Ableger) | GERMINATION | 1--3 | Nach Vermehrung | Kindel/Ableger etabliert Wurzeln, keine Duengung. GERMINATION als Platzhalter fuer vegetative Vermehrung (kein separates PROPAGATION-Enum). | false |
| Juvenil | SEEDLING | 4--12 | 9 Wochen nach Bewurzelung | Jungpflanze baut Blattmasse auf, Vierteldosis | false |
| Aktives Wachstum | VEGETATIVE | 13--44 | Saisonal, Maerz--Oktober | Hauptwachstumsphase mit halber Dosis (Schwachzehrer!) | true |
| Ruheperiode | DORMANCY | 45--60 | Saisonal, November--Februar | Kulturpraktische Ruhephase bei reduziertem Winterlicht, keine obligate Dormanz (dormancy_required: false). Keine Duengung, reduzierte Bewaesserung. | true |

**Nicht genutzte Phasen:**
- **FLOWERING:** Gruenlilien bluehen indoor gelegentlich (kleine weisse Blueten an Stolonen), aber dies ist kein Duengeziel und erfordert keine eigene Phase
- **FLUSHING:** Kein aktives Flushing noetig (Erdsubstrat, kein Hydro-Pre-Harvest). Stattdessen regelmaessige Salzspuelungen alle 3--4 Monate
- **HARVEST:** Keine Ernte (Zierpflanze)

**Saisonaler Zyklus:** Nach dem Erstdurchlauf (Woche 1--60) wiederholen sich VEGETATIVE und DORMANCY jaehrlich (`cycle_restart_from_sequence: 3`). Die einmaligen Anfangsphasen (GERMINATION, SEEDLING) werden nur beim Erstdurchlauf durchlaufen.

**Lueckenlos-Pruefung:** 1--3 | 4--12 | 13--44 | 45--60 (3 + 9 + 32 + 16 = 60 Wochen, keine Luecken)

---

## 3. Delivery Channels

Zwei DRENCH-Kanaele: ein Nur-Wasser-Kanal fuer duengerfreie Phasen und ein Giessduengungs-Kanal.

### 3.1 Kanal: wasser-bewurzelung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-bewurzelung | `delivery_channels.channel_id` |
| Label | Nur Wasser (Bewurzelung) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Nur klares, abgestandenes Wasser (mind. 24h) -- kein Duenger. Fuer Kindel-Bewurzelung in kleinen Toepfen (8--10 cm). DRENCH = von oben giessen (entspricht top_water-Methode). Fluorid-Sensitivitaet beachten: Regenwasser oder abgestandenes Leitungswasser bevorzugt. | `delivery_channels.notes` |

**DRENCH-Parameter:**

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Giessen (L) | 0.10 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 0,1 L Giessvolumen fuer kleine Kindel-Toepfe (8--10 cm). Das geringe Volumen verhindert Staunaesse, die bei der Bewurzelung von Kindeln zur Faeulnis fuehren kann.

### 3.2 Kanal: drench-giessduengung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | drench-giessduengung | `delivery_channels.channel_id` |
| Label | Giessduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Duenger ins abgestandene Giesswasser einruehren, nur auf feuchtes Substrat giessen. DRENCH = Duenger im Giesswasser von oben ausbringen (entspricht top_water-Methode aus dem Pflegeprofil). Wasser immer mindestens 24h abstehen lassen (Fluorid-/Chlor-Empfindlichkeit). | `delivery_channels.notes` |

**DRENCH-Parameter:**

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Duengung (L) | 0.3 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 0,3 L Giessloessung pro Duengung fuer eine etablierte Gruenlilie (Topf 14--18 cm). Bei groesseren Exemplaren (20+ cm Topf, z.B. Haengeampel) auf 0,5 L erhoehen. Fuer Jungpflanzen gelten reduzierte Volumina (siehe Phaseneintraege).

---

## 4. Dosierung pro Phase

### EC-Beitrag Gardol Gruenpflanzenduenger

Geschaetzter EC-Beitrag: **~0,06--0,10 mS/cm pro ml/L** (Herstellerangabe fehlt; Vergleichswert COMPO Gruenpflanzen- und Palmenduenger 7-3-6: ~0,08--0,10. Konservative Planung mit unterer Grenze 0,06).

| Dosierung | ml/L | EC-Beitrag (geschaetzt) |
|-----------|------|-------------------------|
| Vierteldosis | 1,0 | ~0,06 mS/cm |
| Halbe Dosis | 2,0 | ~0,12 mS/cm |

**Hinweis zur Dosierung:** Chlorophytum comosum ist ein Schwachzehrer und extrem salzempfindlich. Die maximale Dosierung in diesem Plan betraegt die halbe Hersteller-Empfehlung (2 ml/L statt 4 ml/L). Ueberduengung zeigt sich schnell durch braune Blattspitzen und weisse Salzkrusten auf der Erdoberflaeche. EC-Werte ueber 0,6 mS/cm (Gesamtloesung) sollten vermieden werden.

**Hinweis zur EC-Differenz:** Die EC-Zielwerte beziehen sich auf die Gesamtloesung inkl. Basis-Wasser-EC. Leitungswasser liefert typisch 0,3--0,7 mS/cm. In Erdsubstrat wird der fehlende EC-Anteil durch Naehrstoffreserven im Boden gedeckt -- eine exakte EC-Steuerung wie in Hydroponik ist nicht erforderlich. Bei einem Schwachzehrer wie der Gruenlilie ist ein niedriger Gesamt-EC sogar erwuenscht.

### 4.1 GERMINATION -- Bewurzelung Kindel/Ableger (Woche 1--3)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 3 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Kindel/Ableger nur mit klarem, abgestandenem Wasser giessen. Substrat gleichmaessig feucht halten, nicht nass -- die sich entwickelnden Knollenwurzeln (Rhizotuberkeln) faulen bei Staunaesse. 3-Tage-Intervall gilt fuer kleine Toepfe (8--10 cm) bei 20--24 C. In kuehlen Raeumen auf 5 Tage verlaengern. Fingerprobe vorrangig: obere 1--2 cm feucht = kein Giessen noetig. Bewurzelung in Wasser: Kindel in Wasserglas mit abgestandenem Wasser, Wurzeln bilden sich in 1--2 Wochen -- Giessplan entfaellt. Wasser woechentlich wechseln. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (Substrat konstant feucht, Richtwert fuer warme Bedingungen) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, aber Nur-Wasser-Channel fuer Giessplan

| Feld | Wert |
|------|------|
| channel_id | wasser-bewurzelung |
| application_method | drench |
| target_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| target_ph | 6.0 (Substrat-pH-Optimum, nicht Giesswasser-pH; Leitungswasser muss fuer Erdkultur nicht pH-korrigiert werden) |
| fertilizer_dosages | [] (leer) |

### 4.2 SEEDLING -- Juvenil (Woche 4--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 1, 1) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 30 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 15 | `phase_entries.magnesium_ppm` |
| Hinweise | Giessvolumen: 0,2 L pro Giessgang (Topf 10--12 cm; bei groesseren Toepfen auf 0,3 L erhoehen). Giessintervall 7 Tage (Fingertest: obere 2 cm trocken). Duengung nur alle 21 Tage: Vierteldosis Gardol (1 ml/L) ins Giesswasser. An den 2 anderen Giessterminen klares Wasser ohne Duenger. Jungpflanze baut Wurzelsystem und Blattmasse auf. Gruenlilie ist ein Schwachzehrer -- erst nach sichtbarem Neuzuwachs (5+ Blaetter) ueberhaupt duengen. Eisenbedarf ca. 1 ppm (Steckbrief). Ca/Mg-Bedarf gering, wird durch Leitungswasser gedeckt. Bei Fluorid-bedingten braunen Blattspitzen: auf Regenwasser umstellen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 7 Tage (Giessintervall; Duengung nur alle 21 Tage, an 2 von 3 Giessungen klares Wasser) | `phase_entries.watering_schedule_override` |

**Delivery Channel: drench-giessduengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.4 |
| target_ph | 6.0 (Substrat-pH-Optimum) |
| Gardol ml/L | 1.0 (Vierteldosis) |
| EC-Beitrag | ~0,06 mS/cm |
| Gardol optional | false |

### 4.3 VEGETATIVE -- Aktives Wachstum (Woche 13--44)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 44 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1.5, 1, 1.5) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 60 (aus Leitungswasser, nicht Gardol) | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 30 (aus Leitungswasser, nicht Gardol) | `phase_entries.magnesium_ppm` |
| Eisen (ppm) | 1.5 (Steckbrief-Richtwert) | `phase_entries.notes` (strukturiert: micro_nutrients) |
| Hinweise | Giessintervall 7 Tage (Fingertest: obere 2--3 cm trocken). Duengung nur alle 21 Tage: Halbe Dosis Gardol (2 ml/L) ins Giesswasser (April--September). An den 2 anderen Giessterminen klares Wasser ohne Duenger. Im Uebergang (Maerz, Oktober) Vierteldosis (1 ml/L). Das NPK-Verhaeltnis 1,5:1:1,5 (Gardol-Produktrealitaet) weicht vom pflanzenphysiologischen Ideal 3:1:2 ab. Bei der halben Herstellerdosierung (2 ml/L) betraegt der absolute N-Beitrag ca. 0,12 g/L -- dies liegt weit unterhalb toxischer Schwellen und ist fuer einen Schwachzehrer hinreichend. Wer das Idealverhaeltnis anstrebt, waehlt COMPO Gruenpflanzen- und Palmenduenger (7-3-6) oder Substral (7-3-5). Ca 60 ppm und Mg 30 ppm werden bei mittelhartem Leitungswasser automatisch gedeckt -- Gardol liefert kein Ca/Mg. Bei weichem Wasser oder Osmosewasser CalMag-Supplement (0,3 ml/L) erforderlich. Alle 3--4 Monate Salzspuelung mit 2x Normalvolumen klarem Wasser (Schwachzehrer: Salzakkumulation fuehrt schneller zu Schaeden als bei Starkzehrern). Stolonenbildung wird durch Kurztagsbedingungen (<12h Licht) ausgeloest -- kulturelle Eigenheit, keine Duengungsanpassung noetig. | `phase_entries.notes` |
| Giessplan-Override | Intervall 7 Tage (Giessintervall; Duengung nur alle 21 Tage, an 2 von 3 Giessungen klares Wasser) | `phase_entries.watering_schedule_override` |

**Delivery Channel: drench-giessduengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| target_ph | 6.0 (Substrat-pH-Optimum) |
| Gardol ml/L | 2.0 (halbe Dosis) |
| EC-Beitrag | ~0,12 mS/cm |
| Gardol optional | false |

**Hinweis:** Im Uebergang (Maerz, Oktober) Vierteldosis (1 ml/L) verwenden. Siehe Jahresplan in Abschnitt 5 fuer monatsweise Abstufung. Die halbe Dosis (2 ml/L) ist fuer einen Schwachzehrer die Maximaldosierung -- nicht steigern! EC-Zielwert 0,6 mS/cm bezieht sich auf die Gesamtloesung (Leitungswasser + Duenger). Bei hartem Leitungswasser (>0,7 mS/cm) wird der Zielwert bereits ohne Duenger ueberschritten -- in Erdkultur ist das bei einem Schwachzehrer unbedenklich, da die EC-Steuerung nur als Richtwert dient (kein Monitoring noetig). Bei weichem Wasser (0,3 mS/cm) ergibt halbe Dosis ca. 0,42 mS/cm gesamt -- sicher im optimalen Bereich.

### 4.4 DORMANCY -- Ruheperiode (Woche 45--60)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 45 | `phase_entries.week_start` |
| week_end | 60 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Saisonale Ruhephase November--Februar (kulturpraktisch, keine obligate Dormanz). Keine Duengung. 12-Tage-Intervall bei normaler Raumtemperatur (18--22 C). Bei kuehleren Winterstandorten (15--18 C) auf 14 Tage verlaengern. Fingerprobe vorrangig: obere 3--4 cm Substrat trocken = giessen. Die Knollenwurzeln (Rhizotuberkeln) speichern Wasser und ueberbruecken laengere Trockenperioden -- Uebergiessen ist die haeufigste Fehlerquelle. Salzspuelung einmalig zu Beginn der Ruhephase (November) mit 2x Topfvolumen klarem Wasser, um Salzreste der Aktivsaison auszuwaschen. Bei trockener Heizungsluft: Blaetter gelegentlich ueberbruehen (Spinnmilben-Praevention), aber Substrat nicht durchnaessen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 12 Tage (Richtwert bei 18--22 C; bei 15--18 C auf 14 Tage erhoehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, Nur-Wasser-Channel fuer Giessplan

| Feld | Wert |
|------|------|
| channel_id | wasser-bewurzelung |
| application_method | drench |
| target_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| target_ph | 6.0 (Substrat-pH-Optimum, nicht Giesswasser-pH) |
| fertilizer_dosages | [] (leer) |

---

## 5. Jahresplan (Monat-fuer-Monat)

Basierend auf einer etablierten Gruenlilie (ab Jahr 2, saisonaler Zyklus VEGETATIVE / DORMANCY).

| Monat | KA-Phase | Gardol ml/L | EC-Beitrag | Frequenz | Giessmenge (ml) | Aktion |
|-------|----------|-------------|------------|----------|-----------------|--------|
| Januar | DORMANCY | 0 | 0,00 | -- | 100--200 | Keine Duengung, Substrat trockener halten, Spinnmilben-Kontrolle |
| Februar | DORMANCY | 0 | 0,00 | -- | 100--200 | Keine Duengung, Licht nimmt langsam zu |
| Maerz | VEGETATIVE | 1,0 | ~0,06 | 21-taegig | 200--300 | Duengung starten mit Vierteldosis, Umtopfen wenn noetig |
| April | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--300 | Halbe Dosis, Wachstum beschleunigt, Salzspuelung |
| Mai | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--300 | Hauptwachstum |
| Juni | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--300 | Hauptwachstum, Hoechststand |
| Juli | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--300 | Hauptwachstum, Salzspuelung |
| August | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--300 | Hauptwachstum, Kindel abnehmen |
| September | VEGETATIVE | 2,0 | ~0,12 | 21-taegig | 200--300 | Letzte Vollduengung (halbe Dosis) |
| Oktober | VEGETATIVE | 1,0 | ~0,06 | 21-taegig | 150--250 | Dosis auf Viertel reduzieren, Uebergang zur Ruhe |
| November | DORMANCY | 0 | 0,00 | -- | 100--200 | Duengung einstellen, Salzspuelung (2x Topfvolumen klares Wasser) |
| Dezember | DORMANCY | 0 | 0,00 | -- | 100--200 | Keine Duengung, minimale Bewaesserung |

**Salzspuelungen (3x/Jahr):** April (Start Aktivsaison), Juli (Mitte Aktivsaison), November (Start Ruhephase). Jeweils 2x normales Giessvolumen mit klarem, abgestandenem Wasser ohne Duenger. Drainagewasser pruefen -- wenn weiss/trueb: zusaetzliche Spuelung noetig. Symptome von Salzakkumulation: weisse Krusten auf Erdoberflaeche, braune Blattspitzen, verlangsamtes Wachstum. Gruenlilien sind besonders salzempfindlich -- Salzspuelungen sind wichtiger als bei den meisten anderen Zimmerpflanzen.

**Jahresverbrauch (geschaetzt):** Bei einer Pflanze und 0,3 L Giessloessung pro Duengung:

- Halbe Dosis (Apr--Sep): 6 Monate x ca. 1,4 Duengungen/Monat (21-Tage-Intervall) x 0,3 L x 2 ml/L = **~5,0 ml**
- Vierteldosis (Maerz, Okt): 2 Monate x ca. 1,4 Duengungen/Monat x 0,3 L x 1 ml/L = **~0,8 ml**
- **Gesamt: ~6 ml/Jahr** -- 1 L Flasche reicht fuer ca. 170 Gruenlilie-Jahre

```
Monat:       |Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:    |DOR|DOR|VEG|VEG|VEG|VEG|VEG|VEG|VEG|VEG|DOR|DOR|
Gardol:      |---|---|...|###|###|###|###|###|###|...|---|---|
                   1/4   halbe Dosis (2 ml/L)      1/4
                   Dosis                           Dosis

Legende: --- = keine Duengung, ... = Vierteldosis (1 ml/L), ### = halbe Dosis (2 ml/L)
         DOR = DORMANCY, VEG = VEGETATIVE
```

---

## 6. KA-Import-Daten

### 6.1 NutrientPlan

```json
{
  "name": "Chlorophytum comosum \u2014 Gardol Gr\u00fcnpflanzend\u00fcnger",
  "description": "Ganzjahresplan f\u00fcr Chlorophytum comosum (Gr\u00fcnlilie) in Erdsubstrat. Einzeld\u00fcnger-Konzept mit Gardol Gr\u00fcnpflanzend\u00fcnger (NPK 6-4-6). Schwachzehrer \u2014 reduzierte Dosierung. Saisonaler Rhythmus: M\u00e4rz\u2013Oktober D\u00fcngung (halbe Dosis), November\u2013Februar Pause. Fluorid-empfindlich: abgestandenes Leitungswasser bevorzugt.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["gruenlilie", "spider-plant", "zimmerpflanze", "gruenpflanze", "gardol", "erde", "indoor", "anfaenger", "schwachzehrer"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 3,
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
  "week_end": 3,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Kindel/Ableger nur mit klarem, abgestandenem Wasser gie\u00dfen. Substrat gleichm\u00e4\u00dfig feucht halten, nicht nass \u2014 Knollenwurzeln faulen bei Staun\u00e4sse. 3-Tage-Intervall f\u00fcr kleine T\u00f6pfe (8\u201310 cm) bei 20\u201324 \u00b0C. In k\u00fchlen R\u00e4umen auf 5 Tage verl\u00e4ngern. Fingerprobe vorrangig. Bewurzelung in Wasser: Kindel in Wasserglas, Wurzeln in 1\u20132 Wochen \u2014 Gie\u00dfplan entf\u00e4llt.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-bewurzelung",
      "label": "Nur Wasser (Bewurzelung)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares, abgestandenes Wasser, kein D\u00fcnger. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode). Fluorid-empfindlich: Wasser mind. 24h abstehen lassen.",
      "target_ec_ms": null,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.10
      }
    }
  ]
}
```

#### SEEDLING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "seedling",
  "sequence_order": 2,
  "week_start": 4,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [1.0, 1.0, 1.0],
  "calcium_ppm": 30.0,
  "magnesium_ppm": 15.0,
  "notes": "Gie\u00dfintervall 7 Tage (Fingertest: obere 2 cm trocken). D\u00fcngung nur alle 21 Tage: Vierteldosis Gardol (1 ml/L) ins Gie\u00dfwasser. An den 2 anderen Gie\u00dfterminen klares Wasser ohne D\u00fcnger. Gie\u00dfvolumen: 0,2 L (Topf 10\u201312 cm). Jungpflanze baut Wurzelsystem und Blattmasse auf. Schwachzehrer \u2014 erst nach sichtbarem Neuzuwachs (5+ Bl\u00e4tter) d\u00fcngen. Eisenbedarf ca. 1 ppm. Ca/Mg aus Leitungswasser gedeckt. Bei Fluorid-bedingten braunen Blattspitzen: auf Regenwasser umstellen.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 7,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins abgestandene Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": 0.4,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 1.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.2
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
  "sequence_order": 3,
  "week_start": 13,
  "week_end": 44,
  "is_recurring": true,
  "npk_ratio": [1.5, 1.0, 1.5],
  "calcium_ppm": 60.0,
  "magnesium_ppm": 30.0,
  "iron_ppm": 1.5,
  "notes": "Gie\u00dfintervall 7 Tage (Fingertest: obere 2\u20133 cm trocken). D\u00fcngung nur alle 21 Tage: halbe Dosis Gardol (2 ml/L) ins Gie\u00dfwasser (April\u2013September). An den 2 anderen Gie\u00dfterminen klares Wasser ohne D\u00fcnger. Vierteldosis (M\u00e4rz, Oktober). NPK 1,5:1:1,5 = Gardol-Produktrealit\u00e4t (Ideal w\u00e4re 3:1:2, f\u00fcr Erdkultur akzeptabel). Ca/Mg aus Leitungswasser \u2014 bei weichem Wasser/RO CalMag-Supplement (0,3 ml/L) erforderlich. Schwachzehrer: halbe Dosis ist Maximum! Alle 3\u20134 Monate Salzsp\u00fclung. Stolonenbildung bei <12h Licht \u2014 keine D\u00fcngungs\u00e4nderung n\u00f6tig.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 7,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins abgestandene Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": 0.6,
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
        "volume_per_feeding_liters": 0.3
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
  "week_end": 60,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Saisonale Ruhephase November\u2013Februar (kulturpraktisch, keine obligate Dormanz). Keine D\u00fcngung. 12-Tage-Intervall bei 18\u201322 \u00b0C, bei 15\u201318 \u00b0C auf 14 Tage verl\u00e4ngern. Fingerprobe: obere 3\u20134 cm trocken = gie\u00dfen. Knollenwurzeln speichern Wasser \u2014 \u00dcbergie\u00dfen ist h\u00e4ufigste Fehlerquelle. Substratsp\u00fclung einmalig im November (2x Topfvolumen klares Wasser). Bei trockener Heizungsluft: Bl\u00e4tter gelegentlich \u00fcberbr\u00fchen (Spinnmilben-Pr\u00e4vention).",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 12,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-bewurzelung",
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
| Species: Chlorophytum comosum | `spec/ref/plant-info/chlorophytum_comosum.md` | Via `nutrient_plans` -> `uses_nutrient_plan` edge |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 7. Sicherheitshinweise

<!-- GL-010: Toxizitaetsbewertung im Duengekontext -->

**Toxizitaet:** Chlorophytum comosum ist laut ASPCA als ungiftig fuer Katzen, Hunde und Kinder eingestuft (Schweregrad: none). Im Duengekontext dennoch beachten:

- **Drainage-Wasser:** Giessloessung mit Duenger in der Unterschale von Haustieren fernhalten (auch wenn die Pflanze selbst ungiftig ist -- das Duengerkonzentrat kann Magen-Darm-Reizung verursachen).
- **Katzen-Attraktion:** Katzen werden haeufig von den haengenden Blaettern angezogen und kauen daran. Bei geduengten Pflanzen kann Duengerrueckstand auf den Blaettern sein -- nach dem Duengen Blaetter kurz abspuelen oder Pflanze ausser Reichweite stellen.
- **Gardol-Konzentrat:** Mineralischer Fluessigduenger -- bei versehentlichem Kontakt durch Haustiere oder Kinder Giftnotrufzentrale kontaktieren.

**Fluorid-Empfindlichkeit:** Chlorophytum comosum ist besonders empfindlich gegenueber Fluorid und Chlor im Leitungswasser. Dies aeussert sich in braunen Blattspitzen, die haeufigste Beschwerde bei Gruenlilie-Haltern. Im Duengekontext relevant:

- **Wasserquelle:** Leitungswasser mindestens 24 Stunden abstehen lassen, damit Chlor ausgast. Regenwasser oder gefiltertes Wasser ist ideal. Fluorid ausgast nicht vollstaendig -- bei hartem Fluorid-Problem auf Regenwasser umsteigen.
- **Duenger-Fluorid:** Manche Phosphatduenger enthalten Fluorid als Verunreinigung (Rohphosphat). Bei Gardol unbekannt -- im Zweifelsfall auf Bioduenger umsteigen.
- **Substrat-pH:** Bei pH >6,5 wird Fluorid staerker pflanzenverfuegbar. Substrat-pH im Bereich 6,0--6,5 halten.

**Salzempfindlichkeit:** Gruenlilien sind extrem salzempfindlich. Duengesalze akkumulieren im Substrat und verursachen:

- Braune Blattspitzen (haeufigste Ursache neben Fluorid)
- Weisse Krusten auf der Erdoberflaeche
- Wurzelschaeden bei laengerer Exposition
- Regelmaessige Salzspuelungen (alle 3--4 Monate) sind essenziell

**Keine Blattglaenzer:** Kein Blattglaenzer oder Blattreiniger auf Gruenlilie-Blaettern verwenden -- die feinen Blaetter vertragen das schlecht. Stattdessen bei Bedarf mit lauwarmem Wasser abbrausen.

Die Toxizitaetsdaten der Pflanze sind im Steckbrief dokumentiert (vgl. `spec/ref/plant-info/chlorophytum_comosum.md`, Abschnitt 1.4).

---

## Quellenverzeichnis

1. Chlorophytum comosum Pflanzensteckbrief: `spec/ref/plant-info/chlorophytum_comosum.md`
2. Gardol Gruenpflanzenduenger Produktdaten: `spec/ref/products/gardol_gruenpflanzenduenger.md`
3. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
4. PhaseName Enum: `src/backend/app/common/enums.py`
5. ASPCA Animal Poison Control -- Spider Plant: https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/spider-plant
6. NC State Extension -- Chlorophytum comosum: https://plants.ces.ncsu.edu/plants/chlorophytum-comosum/
7. Wisconsin Horticulture Extension -- Spider plant: https://hort.extension.wisc.edu/articles/spider-plant-chlorophytum-comosum/

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
