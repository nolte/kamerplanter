# Naehrstoffplan: Kopfsalat / Pfluecksalat -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Lactuca sativa (Mittelzehrer, Outdoor, annuell)
> **Produkte:** Plagron Terra Grow, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/lactuca_sativa.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Kopfsalat / Pfluecksalat -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Kopfsalat und Pfluecksalat (Lactuca sativa) bei Fruehjahrsaussaat. Plagron Terra-Linie mit 2 Produkten (Terra Grow + Pure Zym). Mittelzehrer mit kurzer Kulturdauer (6--10 Wochen). Nitratakkumulation vermeiden: kein N-betonter Duenger vor Ernte! Kein Terra Bloom noetig -- Salat wird vor Bluete geerntet. Annuell, kein Zyklus-Neustart. Staffelsaat alle 2--3 Wochen fuer kontinuierliche Ernte empfohlen. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | salat, kopfsalat, pfluecksalat, lattich, lettuce, plagron, terra, erde, outdoor, mittelzehrer, schwachzehrer | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 2 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 2-Tage-Intervall als Basis. Gleichmaessige Bodenfeuchte ist der wichtigste Pflegefaktor -- Trockenstress fuehrt zu Bitterkeit und Schiessen. Morgens giessen, nie ueber die Blaetter (Pilzgefahr). Bei Hitze (>22 C) taeglich giessen. In GERMINATION (1 Tag, Spruehen) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Salat (Lactuca sativa) ist eine kurzlebige annuelle Kultur. Kopfsalat wird als ganzer Kopf geerntet, Pfluecksalat erlaubt laufende Blatternte (Cut-and-Come-Again). Salat wird im Nutzanbau VOR der Bluete geerntet -- das "Schiessen" (Bluetenstielbildung) markiert das Kulturende (Blaetter werden bitter). Dieser Plan deckt eine Fruehjahrsaussaat ab (Indoor-Vorkultur Maerz, Auspflanzen April, Ernte Mai--Juni).

| Salat-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Anfang Maerz | Indoor-Vorkultur bei 12--16 C. Lichtkeimer! Samen nur leicht andruecken. NICHT ueber 25 C (Thermodormanz)! | false |
| Saemling | SEEDLING | 3--4 | Mitte--Ende Maerz | Pikierte Jungpflanzen. Viertel-Dosis Terra Grow. Kuehle Temperaturen (14--18 C) fuer kompakten Wuchs. | false |
| Vegetatives Wachstum | VEGETATIVE | 5--8 | April--Anfang Mai | Halbe Dosis Terra Grow + Pure Zym. Auspflanzen ins Freiland unter Vlies ab April. Aktiver Blattaufbau, Kopfbildung. | false |
| Ernte | HARVEST | 9--10 | Mai--Juni | Reduzierte Duengung (Viertel-Dosis). Nitrat-Reduktion vor Ernte! Kopfsalat: festen Kopf ernten. Pfluecksalat: aeussere Blaetter laufend ernten. | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Bluete = "Schiessen" ist unerwuenscht; Pflanze bei ersten Anzeichen entfernen)
- **FLUSHING** entfaellt (Schwachzehrer/Mittelzehrer mit geringer Salzbelastung)
- **DORMANCY** entfaellt (annuelle Kultur)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Der Plan laeuft einmalig durch (10 Wochen). Fuer kontinuierliche Ernte: Staffelsaat alle 2--3 Wochen als separate Pflanzdurchlaeufe anlegen.

**Lueckenlos-Pruefung:** 2 + 2 + 4 + 2 = 10 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Kleine Volumina (Mittelzehrer, kurze Kultur).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Leichtes Spruehen mit zimmerwarmem Wasser. Substrat gleichmaessig feucht, nicht nass. Lichtkeimer: nicht mit Erde bedecken! | `delivery_channels.notes` |
| method_params | drench (spray), 0.02 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> pH pruefen. Terra Grow puffert auf pH 6.0--6.5 (Selbstpufferung). Nie ueber die Blaetter giessen! | `delivery_channels.notes` |
| method_params | drench, 0.1--0.3 L pro Pflanze (je nach Groesse) | `delivery_channels.method_params` |

### 3.3 Naehrloesung Ernte (reduziert)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-ernte | `delivery_channels.channel_id` |
| Label | Ernte-Duengung reduziert (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Reduzierte Terra Grow Dosis + Pure Zym. Nitrat-Akkumulation vermeiden! Letzte Duengung mind. 7 Tage vor Ernte. | `delivery_channels.notes` |
| method_params | drench, 0.1--0.3 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Salat

Salat ist ein Mittelzehrer (Kopfsalat) bis Schwachzehrer (Schnittsalat) und reagiert empfindlich auf Ueberduengung. Ziel-EC der Gesamtloesung: **0.4--0.8 mS/cm** (inkl. Basis-Wasser). EC ueber 1.6 mS/cm fuehrt zu Salzstress. Leitungswasser liefert typisch 0.2--0.6 mS/cm. Bei hartem Wasser (>0.5 mS/cm) Duengerdosis um 25--50% reduzieren. **Wichtig:** Uebermaessige N-Duengung fuehrt zu Nitrat-Akkumulation in den Blaettern (gesundheitlich bedenklich, EU-Grenzwerte beachten). Kein N-betonter Duenger in der letzten Woche vor Ernte!

**pH-Hinweis:** Terra Grow puffert die Naehrloesung auf pH 6.0--6.5 (Selbstpufferung). Salat bevorzugt pH 5.8--6.5 -- passt optimal.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ, Ernte (reduziert) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Ernte (durchgehend) |

### 4.1 GERMINATION -- Keimung (Woche 1--2)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 2 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Indoor-Vorkultur in feuchte Aussaaterde. **Lichtkeimer** -- Samen nur leicht andruecken, nicht mit Erde bedecken (duenn mit Vermiculit bestreuen ist ok). Temperatur 12--16 C optimal, maximal 25 C. **KRITISCH: Ueber 25 C Thermodormanz** -- Keimung wird gehemmt! Bei Sommeraussaat: Saatgut 24 h im Kuehlschrank lagern. Abdeckung (Klarsichtfolie/Dome) fuer hohe Luftfeuchtigkeit (80--90%). Keimdauer 5--10 Tage. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichtes Spruehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.00 + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

### 4.2 SEEDLING -- Saemling (Woche 3--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren ab 2. echtem Blattpaar in Einzeltoepfe (6--8 cm). Kuehle Temperaturen (14--18 C) fuer kompakten Wuchs -- waermere Temperaturen foerdern laengeliges Wachstum und fruehes Schiessen. Alle 14 Tage duengen. Pure Zym wird bewusst erst ab VEGETATIVE eingesetzt -- in der Saemlings-Phase ist noch kein abbaubares organisches Substratmaterial vorhanden. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Pure Zym ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + ~0.4 (Wasser) = **~0.52 mS/cm** ✓

### 4.3 VEGETATIVE -- Wachstum + Kopfbildung (Woche 5--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis Terra Grow (2.5 ml/L) + Pure Zym. Aktiver Blattaufbau, Kopfbildung bei Kopfsalat. NPK 3:1:2 foerdert Blattwachstum. Auspflanzen ins Freiland ab April unter Vlies/Fruehbeet. Pflanzabstand: 25--30 cm (Kopfsalat), 15--20 cm (Pfluecksalat). **Tipburn-Praevention:** Ausreichende Luftzirkulation und moderate Luftfeuchtigkeit -- Ca-Transport in innere Blaetter sicherstellen. Alle 14 Tage duengen. Bei Temperaturen ueber 22 C: Halbschatten-Standort waehlen, Mulchen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.5 (halbe Dosis) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.20 (TG 2.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.60 mS/cm** ✓

### 4.4 HARVEST -- Ernte (Woche 9--10)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 10 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierte Terra Grow Dosis (1.5 ml/L) + Pure Zym. **Nitrat-Reduktion:** N-Zufuhr bewusst reduzieren, um Nitratgehalt in den Blaettern zu senken. Letzte Duengung mindestens 7 Tage vor geplanter Ernte. Kopfsalat: Ganzen Kopf morgens ernten (hoechster Wassergehalt, knackigste Blaetter). Pfluecksalat: Aeussere Blaetter laufend ernten, Herz stehen lassen. Bei erstem Anzeichen von Schiessen (Bluetenstiel bildet sich): Pflanze sofort ernten -- Blaetter werden bitter. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-ernte**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis, Nitrat-Reduktion) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.52 mS/cm** ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Fruehjahrsaussaat-Zyklus, Start Anfang Maerz. Fuer kontinuierliche Ernte: Staffelsaat alle 2--3 Wochen von Maerz bis August.

| Monat | KA-Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|---------------|-----------------|----------|
| Maerz (frueh) | GERMINATION | -- | -- | 0.4 | spray taegl. |
| Maerz (spaet) | SEEDLING | 1.5 | -- | 0.5 | alle 14d |
| April | VEGETATIVE | 2.5 | 1.0 | 0.6 | alle 14d |
| Mai | VEG->HARVEST | 2.5->1.5 | 1.0 | 0.6->0.5 | alle 14d |
| Juni | HARVEST | 1.5->0 | 1.0 | 0.5->0.4 | alle 14d->-- |

```
Monat:        |Mär(f)|Mär(s)|Apr  |Mai  |Jun  |
KA-Phase:     |GERM  |SEED  |VEG  |V->H |HARV |
Terra Grow:   |---   |#--   |##-  |##>#-|#->--|
Pure Zym:     |---   |---   |===  |===  |===  |

Legende: --- = nicht verwendet, #-- = Viertel-Dosis,
         ##- = halbe Dosis, === = volle Phase-Dosis
```

### Jahresverbrauch (geschaetzt)

Bei einem Kopfsalat (25 cm Topf/Beet), 0.15 L Giessloessung pro Duengung, Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (1 Duengung x 1.5ml/L x 0.15L + 2 Duengungen x 2.5ml/L x 0.15L + 1 Duengung x 1.5ml/L x 0.15L) = 0.23 + 0.75 + 0.23 = 1.2 ml | **~1.5 ml** |
| Pure Zym | (3 Duengungen x 1.0ml/L x 0.15L) = 0.45 ml | **~0.5 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche Terra Grow reicht fuer hunderte Salat-Saisons. Sinnvoll nur in Kombination mit anderen Pflanzen.

**Hochrechnung 10 Salatkoepfe:** Bei 10 Pflanzen ca. 15 ml Terra Grow + 5 ml Pure Zym pro Satz.

---

## 6. Salat-spezifische Praxis-Hinweise

### Substrat

- Humose, naehrstoffreiche, lockere Erde, pH 6.0--7.0
- Gleichmaessige Feuchtigkeit ist entscheidend -- Staunaesse vermeiden
- Fuer Aussaat: naehrstoffarme Aussaaterde (feinkruemelig)
- Topfgroesse: 3--5 L pro Kopf, Balkonkasten geeignet
- Topftiefe: mind. 15 cm

### Thermodormanz (Keimung)

- Bei Temperaturen ueber 25 C wird die Keimung gehemmt (Thermodormanz)
- Bei Sommeraussaat: Saatgut 24 h im Kuehlschrank lagern
- Optimaler Bereich: 12--16 C, Keimung in 5--10 Tagen
- Abendaussaat im Sommer kann helfen (kuehle Nachttemperaturen)

### Schiessen (Bluetenbildung)

- **Haeufigste Ursache fuer Kulturverlust:** Hohe Temperaturen (>22 C tags, >16 C nachts) und Langtag (>14 h) loesen Schiessen aus
- Pflanze bildet Bluetenstiel -- Blaetter werden bitter und ungeniessbar
- **Praevention:** Kuehler Standort (Halbschatten im Sommer), gleichmaessige Bewasserung, schossresistente Sorten (z.B. 'Kagraner Sommer', 'Salad Bowl')
- Bei Schiessen: Pflanze sofort entfernen, nicht weiter duengen

### Tipburn (Blattrandnekrose)

- Haeufiges physiologisches Problem, besonders bei Indoor-Anbau und Gewaechshaus
- Ursache: Ca-Mangel in schnell wachsenden inneren Blaettern -- oft NICHT Calciummangel im Boden, sondern geringe Transpiration (hohe Luftfeuchtigkeit, wenig Luftbewegung)
- **Praevention:** Luftzirkulation sicherstellen (kleiner Ventilator), moderate Luftfeuchtigkeit (55--70%), gleichmaessig giessen
- Terra Grow liefert kein Calcium -- bei bekanntem Ca-Mangel: Leitungswasser verwenden (enthaelt Calcium) oder Algenkalk ins Substrat einarbeiten

### Nitrat-Akkumulation

- **Gesundheitlich relevant:** EU-Grenzwert fuer Salat 3000--5000 mg NO3/kg Frischgewicht (saisonal/sortenabhaengig)
- Uebermaessige N-Duengung erhoet den Nitratgehalt
- **Massnahmen:** EC unter 0.8 mS/cm halten, letzte Duengung 7 Tage vor Ernte, morgens ernten (Nitratgehalt am niedrigsten nach Sonnenschein-Tag)
- Pfluecksalat: aeussere, aeltere Blaetter haben weniger Nitrat als innere, junge Blaetter

### Staffelsaat (Sukzessionssaat)

- Alle 2--3 Wochen eine neue Reihe saeen fuer lueckenlose Ernte von April bis November
- Fruehjahrssorten (Maerz--Mai): 'Maikoenig', 'Attractie'
- Sommersorten (Juni--August, hitzetolerant): 'Kagraner Sommer', 'Salad Bowl', Batavia-Typen
- Herbstsorten (August--Oktober): 'Grazer Krauthaeuptel'

### Schaedlinge

- **Schnecken:** Hauptfeind Nr. 1! Schneckenzaun, Schneckenkorn (Eisen-III-Phosphat), Vliesabdeckung
- **Blattlaeuse:** Ab Fruehling moeglich (insb. Nasonovia ribisnigri -- Nr-Gen-resistente Sorten waehlen). Kaliseife-Spritzung (2% Loesung)
- **Falscher Mehltau:** Feuchte, kuehle Witterung. Nie ueber Blaetter giessen, Pflanzabstand einhalten

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Kopfsalat / Pfluecksalat \u2014 Plagron Terra",
  "description": "Saisonplan fuer Kopfsalat und Pfluecksalat (Lactuca sativa) bei Fruehjahrsaussaat. Plagron Terra-Linie mit 2 Produkten. Indoor-Vorkultur Maerz, Auspflanzen April, Ernte Mai\u2013Juni. Mittelzehrer, 10 Wochen. Nitratakkumulation vermeiden: N-Reduktion vor Ernte.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["salat", "kopfsalat", "pfluecksalat", "lattich", "lettuce", "plagron", "terra", "erde", "outdoor", "mittelzehrer"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 2,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 7.2 NutrientPlanPhaseEntry (4 Eintraege)

#### GERMINATION

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 2,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Indoor-Vorkultur bei 12\u201316 \u00b0C. Lichtkeimer \u2014 Samen nur leicht andruecken. NICHT ueber 25 \u00b0C (Thermodormanz)! Substrat feucht halten, leicht spruehen.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 1,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-keimung",
      "label": "Spr\u00fchwasser Keimung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Leichtes Spr\u00fchen, Substrat gleichm\u00e4\u00dfig feucht. Lichtkeimer!",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.02}
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
  "week_start": 3,
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow. Pikierte Jungpflanzen bei k\u00fchlen 14\u201318 \u00b0C. Alle 14 Tage d\u00fcngen. Pure Zym erst ab VEGETATIVE.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung S\u00e4mling (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis. Salzempfindlich \u2014 weniger ist mehr.",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.15}
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
  "week_start": 5,
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Halbe Dosis Terra Grow + Pure Zym. Aktiver Blattaufbau, Kopfbildung. Auspflanzen ins Freiland ab April. Tipburn-Pr\u00e4vention: Luftzirkulation sicherstellen. Alle 14 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow halbe Dosis + Pure Zym. Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 pH pr\u00fcfen. Nie \u00fcber die Bl\u00e4tter gie\u00dfen!",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.15}
    }
  ]
}
```

#### HARVEST

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "harvest",
  "sequence_order": 4,
  "week_start": 9,
  "week_end": 10,
  "is_recurring": false,
  "npk_ratio": [2.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Reduzierte Terra Grow Dosis (Viertel-Dosis). Nitrat-Reduktion vor Ernte! Letzte D\u00fcngung mind. 7 Tage vor Ernte. Kopfsalat morgens ernten. Pfl\u00fccksalat: \u00e4u\u00dfere Bl\u00e4tter laufend ernten.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-ernte",
      "label": "Ernte-D\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierte Terra Grow Dosis + Pure Zym. Nitrat-Akkumulation vermeiden!",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.15}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Lactuca sativa | `spec/ref/plant-info/lactuca_sativa.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Ungiftig:** Salat ist fuer Katzen, Hunde und Kinder unbedenklich
- Lactucin im Milchsaft hat leicht sedierende Wirkung -- in Kultursorten vernachlaessigbar gering
- Keine besonderen Haustier- oder Kinderwarnungen erforderlich

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- **Lebensmittel-Hinweis:** Mindestens 7 Tage nach letzter Duengung warten, bevor Salat geerntet wird (Nitrat-Reduktion, Salzpassage durch Substrat)

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
3. Lactuca sativa Pflanzendaten: `spec/ref/plant-info/lactuca_sativa.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
