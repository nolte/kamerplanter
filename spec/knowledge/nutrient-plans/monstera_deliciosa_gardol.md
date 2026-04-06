# Naehrstoffplan: Monstera deliciosa -- Gardol Gruenpflanzenduenger

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Monstera deliciosa (medium_feeder, perennial, Indoor/Erde)
> **Produkt:** Gardol Gruenpflanzenduenger NPK 6-4-6 (Bauhaus)
> **Erstellt:** 2026-03-01
> **Quellen:** spec/knowledge/plants/monstera_deliciosa.md, spec/knowledge/products/gardol_gruenpflanzenduenger.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Monstera deliciosa -- Gardol Gruenpflanzenduenger | `nutrient_plans.name` |
| Beschreibung | Ganzjahresplan fuer Monstera deliciosa in Erdsubstrat. Einzelduenger-Konzept mit Gardol Gruenpflanzenduenger (NPK 6-4-6). Saisonaler Rhythmus: Maerz--Oktober Duengung, November--Februar Pause. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.2 | `nutrient_plans.version` |
| Tags | monstera, zimmerpflanze, gruenpflanze, gardol, erde, indoor, anfaenger | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (100% Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |

<!-- MN-008: Ca/Mg-Versorgung wird bei null (= Leitungswasser) durch das Wasser selbst gedeckt (dt. Durchschnitt ~100 ppm Ca, 15 ppm Mg). Bei RO-/Regenwasser ist ein CalMag-Supplement erforderlich. -->
| Zyklus-Neustart ab Sequenz | 3 (VEGETATIVE) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 7 | `watering_schedule.interval_days` |
| Uhrzeit | 09:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Der Giessplan gilt als Basis. In der Ruheperiode (DORMANCY) verlaengert sich das Intervall auf 10--14 Tage ueber den `watering_schedule_override` der Phase-Entry.

---

## 2. Phasen-Mapping

Monstera deliciosa ist eine perenniale tropische Zimmerpflanze. Die Monstera-spezifischen Wachstumsphasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Monstera-Phase | PhaseName (Enum) | Wochen | Zeitraum | Begruendung | is_recurring |
|----------------|-----------------|--------|----------|-------------|-------------|
| Bewurzelung | GERMINATION | 1--4 | Nach Vermehrung | Steckling/Teilung etabliert Wurzeln, keine Duengung. GERMINATION als Platzhalter fuer vegetative Vermehrung (kein separates PROPAGATION-Enum). | false |
| Juvenil | SEEDLING | 5--16 | 3 Monate nach Bewurzelung | Jungpflanze baut Blattmasse auf, reduzierte Duengung | false |
| Aktives Wachstum | VEGETATIVE | 17--48 | Saisonal, Maerz--Oktober | Hauptwachstumsphase mit voller Duengung | true |
| Ruheperiode | DORMANCY | 49--66 | Saisonal, November--Februar | Kulturpraktische Ruhephase bei reduziertem Winterlicht, keine obligate Dormanz (dormancy_required: false). Keine Duengung, reduzierte Bewaesserung. | true |

**Nicht genutzte Phasen:**
- **FLOWERING:** Monstera blueht indoor nicht (Bluete erst nach 3+ Jahren unter Tropenbedingungen)
- **FLUSHING:** Kein aktives Flushing noetig (Erdsubstrat, kein Hydro-Pre-Harvest)
- **HARVEST:** Keine Ernte (Zierpflanze)

**Saisonaler Zyklus:** Nach dem Erstdurchlauf (Woche 1--66) wiederholen sich VEGETATIVE und DORMANCY jaehrlich (`cycle_restart_from_sequence: 3`). Die einmaligen Anfangsphasen (GERMINATION, SEEDLING) werden nur beim Erstdurchlauf durchlaufen.

**Lueckenlos-Pruefung:** 1--4 | 5--16 | 17--48 | 49--66 (4 + 12 + 32 + 18 = 66 Wochen, keine Luecken)

---

## 3. Delivery Channel

Einzelner DRENCH-Kanal fuer manuelle Giessduengung.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | drench-giessduengung | `delivery_channels.channel_id` |
| Label | Giessduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Duenger ins Giesswasser einruehren, nur auf feuchtes Substrat giessen. DRENCH = Duenger im Giesswasser von oben ausbringen (entspricht top_water-Methode aus dem Pflegeprofil). | `delivery_channels.notes` |

### 3.1 DRENCH-Parameter (DrenchParams)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Duengung (L) | 0.5 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 0,5 L Giessloessung pro Duengung fuer eine mittelgrosse, etablierte Monstera (Topf 18--24 cm). Bei groesseren Exemplaren (30+ cm Topf) auf 1,0--1,5 L erhoehen. Fuer Stecklinge und Jungpflanzen gelten reduzierte Volumina (siehe Phaseneintraege).

---

## 4. Dosierung pro Phase

### EC-Beitrag Gardol Gruenpflanzenduenger

Geschaetzter EC-Beitrag: **~0,06 mS/cm pro ml/L** (Herstellerangabe fehlt, Schaetzung basierend auf NPK 6-4-6 und mineralischer Formulierung).

| Dosierung | ml/L | EC-Beitrag (geschaetzt) |
|-----------|------|-------------------------|
| Halbe Dosis | 2,0 | ~0,12 mS/cm |
| 3/4 Dosis | 3,0 | ~0,18 mS/cm |
| Volle Dosis | 4,0 | ~0,24 mS/cm |

**Hinweis zur EC-Differenz:** Die EC-Zielwerte der Monstera-Profile (z.B. 0,8--1,4 mS/cm fuer VEGETATIVE) beziehen sich auf die Gesamtloesung inkl. Basis-Wasser-EC. Leitungswasser liefert typisch 0,3--0,7 mS/cm. In Erdsubstrat wird der fehlende EC-Anteil durch Naehrstoffreserven im Boden gedeckt -- eine exakte EC-Steuerung wie in Hydroponik ist nicht erforderlich.

### 4.1 GERMINATION -- Bewurzelung (Woche 1--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Steckling nur mit klarem Wasser giessen. Substrat feucht halten, nicht nass. 3-Tage-Intervall gilt fuer kleine Toepfe (8--10 cm) bei 22--25 C. In kuehlen/feuchten Raeumen auf 5--7 Tage verlaengern. Fingerprobe vorrangig: obere 1--2 cm feucht = kein Giessen noetig. Bewurzelung in Wasser: Giessplan entfaellt. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (Substrat konstant feucht, Richtwert fuer warme Bedingungen) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, aber Nur-Wasser-Channel fuer Giessplan

| Feld | Wert |
|------|------|
| channel_id | wasser-bewurzelung |
| application_method | drench |
| target_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| reference_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| target_ph | 6.0 (Substrat-pH-Optimum, nicht Giesswasser-pH; Leitungswasser muss fuer Erdkultur nicht pH-korrigiert werden) |
| fertilizer_dosages | [] (leer) |

### 4.2 SEEDLING -- Juvenil (Woche 5--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 1, 1) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 40 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 20 | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis alle 14 Tage. Pflanze baut Wurzelsystem und erste Blaetter auf. Eisenbedarf ca. 1 ppm (Steckbrief) -- bei Gardol voraussichtlich gedeckt (chelatiertes Fe unbestaetigt). Bei intervenoeser Chlorose: Fe-EDDHA Chelat 0,05 ml/L alle 4 Wochen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 14 Tage (Duengung + Bewaesserung kombiniert; bei trockener Heizungsluft zwischen den Terminen mit klarem Wasser befeuchten) | `phase_entries.watering_schedule_override` |

**Delivery Channel: drench-giessduengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| reference_ec_ms | 0.6 |
| target_ph | 6.0 (Substrat-pH-Optimum) |
| Gardol ml/L | 2.0 (halbe Dosis) |
| EC-Beitrag | ~0,12 mS/cm |
| Gardol optional | false |

### 4.3 VEGETATIVE -- Aktives Wachstum (Woche 17--48)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 17 | `phase_entries.week_start` |
| week_end | 48 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1.5, 1, 1.5) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 80 (aus Leitungswasser, nicht Gardol) | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 40 (aus Leitungswasser, nicht Gardol) | `phase_entries.magnesium_ppm` |
| Eisen (ppm) | 2 (Steckbrief-Richtwert) | `phase_entries.notes` (strukturiert: micro_nutrients) |
| Hinweise | Volle Dosis woechentlich (April--September), halbe Dosis 14-taegig (Maerz, Oktober). NPK-Verhaeltnis 1,5:1:1,5 entspricht Gardol 6-4-6 Produktrealitaet (biologisches Ideal waere 3:1:2, Abweichung fuer Erdkultur akzeptabel). Ca 80 ppm und Mg 40 ppm werden bei mittelhartem Leitungswasser automatisch gedeckt -- Gardol liefert kein Ca/Mg. Bei weichem Wasser oder Osmosewasser CalMag-Supplement (0,5 ml/L) erforderlich. Eisenbedarf 2 ppm -- bei Gardol voraussichtlich gedeckt (chelatiertes Fe unbestaetigt). Bei intervenoeser Chlorose (Blattadern gruen, Blattflaeche gelb): Fe-EDDHA Chelat 0,1 ml/L alle 4 Wochen; Substrat-pH kontrollieren (>6,5 blockiert Fe-Aufnahme). Alle 6--8 Wochen eine Giessung ohne Duenger mit 1,5--2x Normalvolumen (Salzspuelung). | `phase_entries.notes` |

**Delivery Channel: drench-giessduengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.0 |
| reference_ec_ms | 1.0 |
| target_ph | 6.0 (Substrat-pH-Optimum) |
| Gardol ml/L | 4.0 (volle Dosis) |
| EC-Beitrag | ~0,24 mS/cm |
| Gardol optional | false |

**Hinweis:** Im Uebergang (Maerz, Oktober) halbe Dosis (2 ml/L) verwenden. Siehe Jahresplan in Abschnitt 5 fuer monatsweise Abstufung.

### 4.4 DORMANCY -- Ruheperiode (Woche 49--66)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 49 | `phase_entries.week_start` |
| week_end | 66 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Saisonale Ruhephase November--Februar (kulturpraktisch, keine obligate Dormanz). Keine Duengung. 12-Tage-Intervall bei normaler Raumtemperatur (18--22 C). Bei kuehleren Winterstandorten (15--18 C) auf 14 Tage verlaengern. Fingerprobe vorrangig: obere 4--5 cm Substrat trocken = giessen. Einmalige Substratspuelung zu Beginn der Ruhephase (November) mit 2x Topfvolumen klarem Wasser, um Salzreste der Aktivsaison auszuwaschen. Bei Bedarf im Januar wiederholen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 12 Tage (Richtwert bei 18--22 C; bei 15--18 C auf 14 Tage erhoehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, Nur-Wasser-Channel fuer Giessplan

| Feld | Wert |
|------|------|
| channel_id | wasser-dormancy |
| application_method | drench |
| target_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| reference_ec_ms | null (keine Duengung, Leitungswasser-EC 0,3--0,7 mS/cm) |
| target_ph | 6.0 (Substrat-pH-Optimum, nicht Giesswasser-pH) |
| fertilizer_dosages | [] (leer) |

---

## 5. Jahresplan (Monat-fuer-Monat)

Basierend auf einer etablierten Monstera (ab Jahr 2, saisonaler Zyklus VEGETATIVE / DORMANCY).

| Monat | KA-Phase | Gardol ml/L | EC-Beitrag | Frequenz | Giessmenge (ml) | Aktion |
|-------|----------|-------------|------------|----------|-----------------|--------|
| Januar | DORMANCY | 0 | 0,00 | -- | 200--300 | Keine Duengung, Substrat trockener halten |
| Februar | DORMANCY | 0 | 0,00 | -- | 200--300 | Keine Duengung, Licht nimmt langsam zu |
| Maerz | VEGETATIVE | 2,0 | ~0,12 | 14-taegig | 300--400 | Duengung starten mit halber Dosis |
| April | VEGETATIVE | 4,0 | ~0,24 | woechentlich | 300--500 | Volle Dosis, Wachstum beschleunigt |
| Mai | VEGETATIVE | 4,0 | ~0,24 | woechentlich | 400--500 | Hauptwachstum |
| Juni | VEGETATIVE | 4,0 | ~0,24 | woechentlich | 400--500 | Hauptwachstum, Hoechststand |
| Juli | VEGETATIVE | 4,0 | ~0,24 | woechentlich | 400--500 | Hauptwachstum |
| August | VEGETATIVE | 4,0 | ~0,24 | woechentlich | 400--500 | Hauptwachstum |
| September | VEGETATIVE | 4,0 | ~0,24 | woechentlich | 300--400 | Letzte Vollduengung (Steckbrief zeigt halbe Dosis ab Sep -- produktspezifisch, beides agronomisch korrekt) |
| Oktober | VEGETATIVE | 2,0 | ~0,12 | 14-taegig | 300--400 | Dosis reduzieren, Uebergang zur Ruhe |
| November | DORMANCY | 0 | 0,00 | -- | 200--300 | Duengung einstellen, Substratspuelung (2x Topfvolumen klares Wasser) |
| Dezember | DORMANCY | 0 | 0,00 | -- | 150--300 | Keine Duengung, minimale Bewaesserung |

**Salzspuelungen (3x/Jahr):** April (Start Aktivsaison), Juli (Mitte Aktivsaison), November (Start Ruhephase). Jeweils 1,5--2x normales Giessvolumen mit klarem Wasser ohne Duenger. Drainagewasser pruefen -- wenn weiss/trueb: zusaetzliche Spuelung noetig. Symptome von Salzakkumulation: weisse Krusten auf Erdoberflaeche, braune Blattspitzen, verlangsamtes Wachstum trotz Duengung.

**Jahresverbrauch (geschaetzt):** Bei einer Pflanze und 0,5 L Giessloessung pro Duengung:

- Volle Dosis (Apr--Sep): 6 Monate x 4 Duengungen/Monat x 0,5 L x 4 ml/L = **48 ml**
- Halbe Dosis (Maerz, Okt): 2 Monate x 2 Duengungen/Monat x 0,5 L x 2 ml/L = **4 ml**
- **Gesamt: ~52 ml/Jahr** -- 1 L Flasche reicht fuer ca. 19 Monstera-Jahre

```
Monat:       |Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:    |DOR|DOR|VEG|VEG|VEG|VEG|VEG|VEG|VEG|VEG|DOR|DOR|
Gardol:      |---|---|###|===|===|===|===|===|===|###|---|---|
                     halb  volle Dosis              halb
                     Dosis                          Dosis

Legende: --- = keine Duengung, ### = halbe Dosis (2 ml/L), === = volle Dosis (4 ml/L)
         DOR = DORMANCY, VEG = VEGETATIVE
```

---

## 6. KA-Import-Daten

### 6.1 NutrientPlan

```json
{
  "name": "Monstera deliciosa \u2014 Gardol Gr\u00fcnpflanzend\u00fcnger",
  "description": "Ganzjahresplan f\u00fcr Monstera deliciosa in Erdsubstrat. Einzeld\u00fcnger-Konzept mit Gardol Gr\u00fcnpflanzend\u00fcnger (NPK 6-4-6). Saisonaler Rhythmus: M\u00e4rz\u2013Oktober D\u00fcngung, November\u2013Februar Pause.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.2",
  "tags": ["monstera", "zimmerpflanze", "gruenpflanze", "gardol", "erde", "indoor", "anfaenger"],
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
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Steckling nur mit klarem Wasser gie\u00dfen. Substrat feucht halten, nicht nass. 3-Tage-Intervall gilt f\u00fcr kleine T\u00f6pfe (8\u201310 cm) bei 22\u201325 \u00b0C. In k\u00fchlen/feuchten R\u00e4umen auf 5\u20137 Tage verl\u00e4ngern. Fingerprobe vorrangig. Bewurzelung in Wasser: Gie\u00dfplan entf\u00e4llt.",
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
      "notes": "Nur klares Wasser, kein D\u00fcnger. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": null,
      "reference_ec_ms": null,
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
  "week_start": 5,
  "week_end": 16,
  "is_recurring": false,
  "npk_ratio": [1.0, 1.0, 1.0],
  "calcium_ppm": 40.0,
  "magnesium_ppm": 20.0,
  "notes": "Halbe Dosis alle 14 Tage. Pflanze baut Wurzelsystem und erste Bl\u00e4tter auf. Eisenbedarf ca. 1 ppm (Steckbrief). Bei trockener Heizungsluft zwischen D\u00fcngeterminen mit klarem Wasser befeuchten.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 14,
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
      "notes": "D\u00fcnger ins Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
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

#### VEGETATIVE

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 3,
  "week_start": 17,
  "week_end": 48,
  "is_recurring": true,
  "npk_ratio": [1.5, 1.0, 1.5],
  "calcium_ppm": 80.0,
  "magnesium_ppm": 40.0,
  "iron_ppm": 2.0,
  "notes": "Volle Dosis w\u00f6chentlich (April\u2013September), halbe Dosis 14-t\u00e4gig (M\u00e4rz, Oktober). NPK 1,5:1:1,5 = Gardol-Produktrealit\u00e4t (Ideal w\u00e4re 3:1:2, f\u00fcr Erdkultur akzeptabel). Ca/Mg aus Leitungswasser, nicht aus Gardol \u2014 bei weichem Wasser/RO CalMag-Supplement erforderlich. Fe 2 ppm Richtwert. Alle 6\u20138 Wochen Salzsp\u00fclung (1,5\u20132x Normalvolumen klares Wasser).",
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": 1.0,
      "reference_ec_ms": 1.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 4.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.5
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
  "week_start": 49,
  "week_end": 66,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Saisonale Ruhephase November\u2013Februar (kulturpraktisch, keine obligate Dormanz). Keine D\u00fcngung. 12-Tage-Intervall bei 18\u201322 \u00b0C, bei 15\u201318 \u00b0C auf 14 Tage verl\u00e4ngern. Fingerprobe: obere 4\u20135 cm trocken = gie\u00dfen. Substratsp\u00fclung einmalig im November (2x Topfvolumen klares Wasser).",
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
      "channel_id": "wasser-dormancy",
      "label": "Nur Wasser (Ruheperiode)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares Wasser, kein D\u00fcnger. Reduziertes Volumen. DRENCH = von oben gie\u00dfen (entspricht top_water-Methode).",
      "target_ec_ms": null,
      "reference_ec_ms": null,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.3
      }
    }
  ]
}
```

### 6.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Gardol Gruenpflanzenduenger | `spec/knowledge/products/gardol_gruenpflanzenduenger.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Monstera deliciosa | `spec/knowledge/plants/monstera_deliciosa.md` | Via `nutrient_plans` -> `uses_nutrient_plan` edge |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 7. Sicherheitshinweise

<!-- MN-015: Toxizitaetswarnung im Duengekontext -->

**Toxizitaet:** Monstera deliciosa ist giftig fuer Katzen, Hunde und Kinder (Calciumoxalat-Raphiden, Schweregrad moderat). Im Duengekontext beachten:

- **Drainage-Wasser:** Giessloessung mit Duenger in der Unterschale von Haustieren fernhalten (Trinken kann zu Magen-Darm-Reizung fuehren).
- **Stecklinge in Wasser:** Bewurzelungsglaeser auf dem Fensterbrett fuer Katzen unzugaenglich aufstellen.
- **Umtopfen:** Handschuhe tragen -- Pflanzensaft enthaelt Calciumoxalat-Raphiden und kann Kontaktdermatitis ausloesen.
- **Gardol-Konzentrat:** Mineralischer Fluessigduenger -- bei versehentlichem Kontakt durch Haustiere oder Kinder giftnotrufzentrale kontaktieren.

Die Toxizitaetsdaten der Pflanze sind im Steckbrief dokumentiert (vgl. `spec/knowledge/plants/monstera_deliciosa.md`, Abschnitt 1.4).

---

## Quellenverzeichnis

1. Monstera deliciosa Pflanzensteckbrief: `spec/knowledge/plants/monstera_deliciosa.md`
2. Gardol Gruenpflanzenduenger Produktdaten: `spec/knowledge/products/gardol_gruenpflanzenduenger.md`
3. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
4. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.2 (Agrarbiologisches Review MN-001--MN-015: npk_ratio Produktrealitaet, Fe-Bedarf, target_ec_ms null, SEEDLING watering_schedule_override, Ca/Mg-Herkunft, Salzspuelung, pH-/DRENCH-Klarstellung, Toxizitaetswarnung)
**Erstellt:** 2026-03-01
