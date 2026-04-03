# Naehrstoffplan: Dill (Direktsaat) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Anethum graveolens (Schwachzehrer, Outdoor, annuell)
> **Produkte:** Plagron Terra Grow, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_grow.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/plants/anethum_graveolens.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Dill (Direktsaat) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Minimalistischer Naehrstoffplan fuer Dill (Schwachzehrer). Nur Terra Grow + Pure Zym. Schnelle Kultur (8--12 Wochen). Direktsaat ab April, Pfahlwurzel vertraegt kein Umtopfen! Staffelsaat alle 3--4 Wochen fuer kontinuierliche Ernte. Bewusst niedrige Dosierung -- ueberduengter Dill schmeckt fad. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | dill, anethum, gurkenkraut, plagron, terra, erde, kraeutergarten, schwachzehrer, outdoor, direktsaat, schnellkultur | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart -- Staffelsaat als neue Aussaat) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 08:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 3-Tage-Intervall als Basis. Dill vertraegt kurze Trockenheit besser als Staunaesse (Wurzelfaeule!). Nicht ueber das Kraut giessen (Mehltau-Gefahr). Maessig giessen.

---

## 2. Phasen-Mapping

Dill (Anethum graveolens) ist eine schnelle Saisonkultur mit kurzer Vegetationszeit (60--90 Tage). Die Pflanze neigt stark zum Schossen (Bluete) bei Hitze und langen Tagen. Fuer kontinuierliche Blatternten: Staffelsaat alle 3--4 Wochen. Direktsaat ist essentiell -- Pfahlwurzel vertraegt kein Pikieren!

**Kernprinzip:** Minimale Duengung. Dill ist ein Schwachzehrer. Zu viel Stickstoff foerdert weiches, geschmacksloses Kraut und beschleunigt das Schossen.

| Dill-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | ab Direktsaat (April) | Lichtkeimer, Samen nur leicht andruecken. 15--21 C. Keimdauer 7--14 Tage. | false |
| Saemling | SEEDLING | 3--4 | +2 Wochen | Vereinzeln auf 15--20 cm. Minimale Duengung. | false |
| Vegetativ / Blatternten | VEGETATIVE | 5--8 | +2 Wochen | HAUPTERNTEPHASE. Blattspitzen ernten. Halbe Dosis Terra Grow. Triebspitzen-Ernte verzoegert Schossen. | false |
| Bluete / Samenreife | FLOWERING | 9--11 | +4 Wochen | Dill schosst. Blueten sind Nuetzlingsanlocker (Schwebfliegen)! Dillsamen ernten oder Selbstaussaat zulassen. Keine Duengung. | false |
| Seneszenz | HARVEST | 12 | +3 Wochen | Kein Duenger. Samen von trockenen Dolden sammeln. Pflanze entfernen. | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (annuell, keine Winterruhe)
- **FLUSHING** entfaellt (minimale Dosierungen)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Nach 12 Wochen stirbt die Pflanze. Fuer Nachschub: Staffelsaat.

**Hinweis zu HARVEST:** Der KA-Enum "HARVEST" wird fuer die Seneszenz-Phase verwendet (Samenreife + Pflanzenentfernung).

**Lueckenlos-Pruefung:** 2 + 2 + 4 + 3 + 1 = 12 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Minimale Volumina (Schwachzehrer, Freiland).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Substrat gleichmaessig feucht. Lichtkeimer: Samen nur leicht andruecken oder duenn mit Sand bedecken (max. 0.5 cm). | `delivery_channels.notes` |
| method_params | drench (spray), 0.02 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> pH pruefen. NICHT ueberdosieren -- Dill braucht wenig! | `delivery_channels.notes` |
| method_params | drench, 0.2 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (duengerfrei) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Fuer Bluete- und Seneszenz-Phase. | `delivery_channels.notes` |
| method_params | drench, 0.1 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Dill

**WICHTIG: Dill ist ein Schwachzehrer.** Minimale Duengung genuegt. Ziel-EC der Gesamtloesung: **0.3--0.6 mS/cm** (inkl. Basis-Wasser). **EC ueber 0.8 mS/cm vermeiden.** Bei hartem Leitungswasser (>0.5 mS/cm) gar nicht duengen -- Kompost im Boden genuegt!

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ |

**Warum nur 2 Produkte und minimale Dosierung?** Dill waechst in der Natur auf mageren Boeden. Zu viel Stickstoff = weiches, geschmacksloses Kraut mit reduzierten Aromaoel. Terra Grow liefert die minimale Grundversorgung. Pure Zym haelt das Substrat gesund.

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
| Hinweise | Direktsaat ins Freiland ab Bodentemperatur 8 C (April). Lichtkeimer: Samen nur leicht andruecken oder duenn mit feinem Sand bedecken (max 0.5 cm). NICHT pikieren oder umtopfen -- Pfahlwurzel! Reihenabstand 25--30 cm. Keimdauer 7--14 Tage. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.00 + ~0.4 (Wasser) = **~0.4 mS/cm** (nur Wasser)

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
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Vereinzeln auf 15--20 cm Abstand. Nur bei sichtbarem Naehrstoffmangel duengen -- gut mit Kompost versorgter Boden braucht oft keine zusaetzliche Duengung. 1x duengen genuegt. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.4  |
| reference_ec_ms | 0.4  |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Pure Zym ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + ~0.4 (Wasser) = **~0.52 mS/cm**

### 4.3 VEGETATIVE -- Blatternten (Woche 5--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | **HAUPTERNTEPHASE.** Halbe Dosis Terra Grow (2.0 ml/L) + Pure Zym. Blattspitzen ernten (verzoegert Schossen). Dosierung bewusst niedrig -- ueberdungter Dill schmeckt fad! Kalium foerdert Aromaoelproduktion und Standfestigkeit (K im 3-1-3-Profil ausreichend). Alle 3 Wochen 1x duengen (max. 2 Duengungen in dieser Phase). Halbschattiger Standort verzoegert Schossen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.0 (halbe Dosis, Schwachzehrer) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.16 (TG 2.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.56 mS/cm** -- unter 0.8 mS/cm Schwachzehrer-Limit

### 4.4 FLOWERING -- Bluete / Samenreife (Woche 9--11)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 11 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Dill schosst -- zentraler Bluetenstaengel mit Dolden. **Nuetzlingsmagnet:** Bluehender Dill zieht Schwebfliegen, Schlupfwespen und Marienkaefer an -- im Mischkulturbeet einige Pflanzen bluehen lassen! Dillsamen (Dillfruchte) koennen geerntet werden wenn braun und trocken. Blaetter werden derber und weniger aromatisch. | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser)

### 4.5 HARVEST -- Seneszenz (Woche 12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 12 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger. Samen von trockenen Dolden sammeln (Samen in Tuete schuetteln). Pflanze entfernen oder fuer Selbstaussaat stehen lassen -- Dill saeht sich bereitwillig selbst aus. Pflanzenreste kompostieren. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (reduziert) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser)

---

## 5. Jahresplan (Staffelsaat-Zyklen)

Dill ist annuell mit kurzer Kulturzeit (12 Wochen). Durch Staffelsaat alle 3--4 Wochen kann die Versorgung ueber die Saison sichergestellt werden.

### 5.1 Staffelsaat-Kalender

| Aussaat | Startmonat | Blatternten | Samenreife | Bemerkung |
|---------|-----------|-------------|------------|-----------|
| 1. Satz | April | Juni | Juli | Erster Satz, Direktsaat ab 8 C Bodentemperatur |
| 2. Satz | Mai | Juli | August | Nach Eisheiligen, sicherster Termin |
| 3. Satz | Juni | August | September | Halbschatten waehlen (verzoegert Schossen) |
| 4. Satz | Juli | September | Oktober | Letzte Chance, kurze Blatterntezeit |

### 5.2 Monats-Uebersicht (Beispiel: Aussaat April)

| Monat | KA-Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|---------------|-----------------|----------|
| April | GERM | -- | -- | 0.4 | taeglich Spruehen |
| Mai | SEED->VEG | 1.5->2.0 | -->1.0 | 0.4->0.5 | 1x3Wo |
| Juni | VEG | 2.0 | 1.0 | 0.5 | 1x3Wo |
| Juli | FLOWERING | -- | -- | 0.4 | nur Wasser |
| August | HARVEST | -- | -- | 0.4 | minimal |

```
Monat (1. Satz Apr):  |Apr|Mai|Jun|Jul|Aug|
KA-Phase:              |GER|S→V|VEG|FLO|HAR|
Terra Grow:            |---|#--|##-|---|---|
Pure Zym:              |---|---|===|---|---|

Legende: --- = nicht verwendet, #-- = Viertel-Dosis,
         ##- = halbe Dosis, === = volle Phase-Dosis
```

### 5.3 Jahresverbrauch (geschaetzt)

Bei einem 12-Wochen-Zyklus, 1 Pflanze, 0.2 L Giessloessung pro Duengung:

| Produkt | Formel | Verbrauch/Zyklus |
|---------|--------|------------------|
| Terra Grow | (1x1.5ml + 2x2.0ml) x 0.2L = (1.5 + 4.0) x 0.2 = 1.1 ml | **~1 ml** |
| Pure Zym | (2x1.0ml) x 0.2L = 0.4 ml | **~0.5 ml** |

**Kosten-Schaetzung:** Nahezu vernachlaessigbar. Eine 1L-Flasche Terra Grow reicht fuer ca. 900 Dill-Zyklen.

Bei 4 Staffelsaat-Zyklen pro Jahr: ~4 ml Terra Grow, ~2 ml Pure Zym.

---

## 6. Dill-spezifische Praxis-Hinweise

### Substrat

- Durchlaessige, humusreiche, leicht sandige Erde, pH 5.5--6.5
- Nicht zu naehrstoffreich (Schwachzehrer!)
- Gut mit Kompost versorgt vor der Saat -- dann kaum Duengung noetig
- Staunaesse vermeiden (Wurzelfaeule)

### Direktsaat -- kein Pikieren!

- **Dill hat eine empfindliche Pfahlwurzel -- NICHT pikieren oder umtopfen!**
- Immer direkt am Endstandort saeen
- Reihenabstand 25--30 cm, in der Reihe 15--20 cm (nach Vereinzeln)
- Topfkultur nur bedingt geeignet (Zwerg-Sorten wie 'Fernleaf' bevorzugen, Topf mind. 20 cm tief)

### Schossen verzoegern

- **Wichtigstes Kulturproblem:** Dill neigt stark zum Schossen (Bluete)
- Halbschatten waehlen (verlaengert vegetative Phase)
- Regelmaessig Blattspitzen ernten (hemmt Bluetenbildung)
- Hitze ueber 30 C beschleunigt Schossen dramatisch
- Kuehle Temperaturen (18--22 C) verzoegern Schossen
- Schosstolerante Sorten waehlen ('Fernleaf', 'Dukat', 'Hera')
- **Beste Strategie:** Staffelsaat alle 3--4 Wochen statt einzelne Pflanzen laenger halten

### Nuetzlingsanlocker

- Bluehender Dill ist einer der besten Nuetzlingsanlocker im Garten
- Schwebfliegen, Schlupfwespen, Marienkaefer werden angelockt
- Im Mischkulturbeet immer einige Pflanzen bluehen lassen
- Klassische Partnerschaft mit Gurke (Kompatibilitaets-Score 0.9)

### Mischkultur

- Gute Nachbarn: Gurke (0.9), Kohl (0.8), Salat (0.8), Zwiebel (0.7), Erbse (0.7), Bohne (0.7)
- Schlechte Nachbarn: Fenchel (streng!), Moehre (Kreuzbestaeubung), Basilikum (Wasserbeduerfnisse), Petersilie (gleiche Familie)

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Dill (Direktsaat) \u2014 Plagron Terra",
  "description": "Minimalistischer N\u00e4hrstoffplan f\u00fcr Dill (Schwachzehrer). Schnelle Kultur (12 Wochen). Direktsaat, kein Pikieren (Pfahlwurzel). Staffelsaat alle 3\u20134 Wochen. Nur Terra Grow + Pure Zym. Bewusst niedrige Dosierung \u2014 \u00fcberd\u00fcngter Dill schmeckt fad.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["dill", "anethum", "gurkenkraut", "plagron", "terra", "erde", "kr\u00e4utergarten", "schwachzehrer", "outdoor", "direktsaat", "schnellkultur"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "08:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 7.2 NutrientPlanPhaseEntry (5 Eintraege)

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
  "notes": "Direktsaat ab Bodentemperatur 8\u00b0C. Lichtkeimer: Samen nur leicht andr\u00fccken. NICHT pikieren (Pfahlwurzel). Keimdauer 7\u201314 Tage.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 2,
    "preferred_time": "08:00",
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
      "notes": "Kein D\u00fcnger. Substrat gleichm\u00e4\u00dfig feucht.",
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
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Vereinzeln auf 15\u201320 cm. Nur bei N\u00e4hrstoffmangel d\u00fcngen \u2014 Kompost im Boden gen\u00fcgt oft. Max. 1x d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis. Schwachzehrer \u2014 weniger ist mehr.",
      "target_ec_ms": 0.4,
      "reference_ec_ms": 0.4,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
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
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Haupterntephase. Halbe Dosis Terra Grow (2.0 ml/L) + Pure Zym. Blattspitzen ernten verz\u00f6gert Schossen. NICHT \u00fcberdosieren \u2014 \u00fcberd\u00fcngter Dill schmeckt fad! Alle 3 Wochen 1x d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Halbe Dosis Terra Grow + Pure Zym. NICHT \u00fcberdosieren!",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
    }
  ]
}
```

#### FLOWERING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flowering",
  "sequence_order": 4,
  "week_start": 9,
  "week_end": 11,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Dill schosst. Bl\u00fchender Dill = N\u00fctzlingsmagnet (Schwebfliegen, Schlupfwespen). Im Mischkulturbeet bl\u00fchen lassen. Dillsamen ernten wenn braun und trocken.",
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Bl\u00fcte)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Nur Wasser.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.1}
    }
  ]
}
```

#### HARVEST

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "harvest",
  "sequence_order": 5,
  "week_start": 12,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Seneszenz. Kein D\u00fcnger. Samen sammeln. Pflanze entfernen oder f\u00fcr Selbstaussaat stehen lassen. Pflanzenreste kompostieren.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 5,
    "preferred_time": "08:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Seneszenz)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Nur bei Trockenheit.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.1}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/knowledge/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Anethum graveolens | `spec/knowledge/plants/anethum_graveolens.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Ungiftig:** ASPCA listet Dill als ungiftig fuer Katzen und Hunde
- Als Kuechenkraut fuer Menschen unbedenklich
- **Kontaktallergie:** Furanocumarine im Pflanzensaft koennen bei empfindlichen Personen + Sonnenlicht phototoxische Reaktionen ausloesen (Apiaceae-typisch)
- **Kreuzallergie:** Sellerie-Beifuss-Gewuerz-Syndrom moeglich (selten)
- **Verwechslungsgefahr:** Bei Wildsammlung NICHT mit Schierling oder Hundspetersilie verwechseln (giftig!)

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
3. Dill Pflanzendaten: `spec/knowledge/plants/anethum_graveolens.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
