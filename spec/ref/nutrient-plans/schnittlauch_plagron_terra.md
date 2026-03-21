# Naehrstoffplan: Schnittlauch (perennierend) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Allium schoenoprasum (Schwachzehrer, Outdoor, perennierend)
> **Produkte:** Plagron Terra Grow, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/allium_schoenoprasum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Schnittlauch (perennierend) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Perennierend-zyklischer Naehrstoffplan fuer Schnittlauch (Allium schoenoprasum). Schwachzehrer mit jaehrlichem Zyklus: Vegetativ (Maerz--Mai) -> Bluete (Juni--Juli) -> 2. Vegetativ (Juli--September) -> Dormanz (Oktober--Februar). Zyklus-Neustart ab Sequenz 3 (VEGETATIVE). Nur 2 Produkte: Terra Grow + Pure Zym. Kein Bloom-Duenger noetig. Schwefelversorgung durch Substrat ausreichend. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | schnittlauch, allium, chives, plagron, terra, erde, kraeutergarten, schwachzehrer, outdoor, perennierend, winterhart | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | 3 (VEGETATIVE -- nach Dormanz springt der Zyklus zurueck zur vegetativen Erntephase) | `nutrient_plans.cycle_restart_from_sequence` |

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

**Hinweis:** 3-Tage-Intervall als Basis. Schnittlauch mag gleichmaessige Feuchte, vertraegt aber kurze Trockenheit (bildet dann duenne Halme). In DORMANCY kein aktives Giessen noetig (Freiland: natuerlicher Niederschlag; Topf: nur Austrocknung verhindern).

---

## 2. Phasen-Mapping

Schnittlauch (Allium schoenoprasum) ist vollstaendig winterhart (bis -30 C) und mehrjaehrig. Die oberirdischen Teile sterben im Herbst ab, die Zwiebelbulben ueberwintern im Boden und treiben im Fruehjahr zuverlaessig neu aus. Der jaehrliche Zyklus wiederholt sich unbegrenzt. Alle 3--4 Jahre Horst teilen fuer kraeftigen Wuchs.

| Schnittlauch-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|--------------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--3 | Februar--Maerz (Erstaussaat) | Dunkelkeimer, Samen 1--2 cm tief. 18--25 C. Keimdauer 7--21 Tage. Nur bei Erstaussaat! Etablierte Pflanzen ueberspringen zu VEGETATIVE. | false |
| Saemling | SEEDLING | 4--8 | Maerz--April (Erstaussaat) | Junge Halme 3--5 cm. Viertel-Dosis Terra Grow. Nur bei Erstaussaat! | false |
| Vegetativ / Ernte | VEGETATIVE | 9--20 | Maerz--Mai (bzw. Neuaustrieb nach Dormanz) | HAUPTERNTEPHASE. Halbe Dosis Terra Grow + Pure Zym. Regelmaessiger Ernteschnitt (3 cm ueber Boden). Nach jedem Schnitt leicht nachduengen. | true |
| Bluete | FLOWERING | 21--24 | Juni--Juli | Essbare Kugelblueten (lila). Keine Duengung waehrend Bluete. Bluetenstaende entfernen fuer Blattqualitaet oder stehen lassen fuer Deko/Saatgut. Nach Bluete: kompletter Rueckschnitt -> kraeftiger 2. Austrieb. | true |
| Dormanz (Winter) | DORMANCY | 25--44 | Oktober--Februar | Oberirdische Teile sterben ab. Keine Duengung. Zwiebeln im Boden belassen. Kaltphase (6--8 Wochen <5 C) noetig fuer kraeftigen Fruehjahraustrieb (Vernalisation). | true |

**Nicht genutzte Phasen:**
- **HARVEST** wird nicht als separate Phase genutzt -- die Ernte findet in VEGETATIVE statt
- **FLUSHING** entfaellt (Schwachzehrer mit minimaler Salzbelastung)

**Zyklus-Neustart:** `cycle_restart_from_sequence: 3` (VEGETATIVE). Nach der Dormanz im Februar/Maerz treibt der Schnittlauch aus den Zwiebeln neu aus und der Zyklus springt zurueck zur vegetativen Erntephase.

**Lueckenlos-Pruefung:** 3 + 5 + 12 + 4 + 20 = 44 Wochen, keine Luecken (Erstjahr). Ab 2. Jahr: 12 + 4 + 20 = 36 Wochen (+ 16 Wochen = 52 Wochen Gesamtjahr).

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Kleine Volumina (Schwachzehrer).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Substrat gleichmaessig feucht halten. Dunkelkeimer: Samen 1--2 cm tief. | `delivery_channels.notes` |
| method_params | drench (spray), 0.02 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> pH pruefen. Terra Grow puffert auf pH 6.0--6.5 (Selbstpufferung). Schnittlauch bevorzugt pH 6.0--7.0. | `delivery_channels.notes` |
| method_params | drench, 0.2--0.3 L pro Pflanze/Horst | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Fuer Bluete- und Dormanz-Phase. | `delivery_channels.notes` |
| method_params | drench, 0.1 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Schnittlauch

Schnittlauch ist ein Schwachzehrer. Ziel-EC der Gesamtloesung: **0.3--0.7 mS/cm** (inkl. Basis-Wasser). Leitungswasser liefert typisch 0.2--0.5 mS/cm. Bei hartem Wasser (>0.5 mS/cm) Duengerdosis um 30--50% reduzieren. **EC ueber 0.8 mS/cm vermeiden.**

**pH-Hinweis:** Terra Grow puffert die Naehrloesung auf pH 6.0--6.5. Schnittlauch bevorzugt pH 6.0--7.0 -- passt hervorragend.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ (durchgehend) |

**Warum kein Bloom-Duenger?** Schnittlauchblueten werden fuer die Blattqualitaet eher entfernt. Wenn sie stehen bleiben (Deko, Saatgut), braucht die Pflanze keinen P-K-Boost -- Schwachzehrer mit moderater Bluete.

### 4.1 GERMINATION -- Keimung (Woche 1--3)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 3 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Nur bei Erstaussaat. Dunkelkeimer: Samen 1--2 cm mit Erde bedecken. 18--25 C. Keimdauer 7--21 Tage. Substrat gleichmaessig feucht halten. Alternative: Horst-Teilung etablierter Pflanzen (einfacher, sofort erntereif). | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.00 + ~0.4 (Wasser) = **~0.4 mS/cm** (nur Wasser)

### 4.2 SEEDLING -- Saemling (Woche 4--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Nur bei Erstaussaat. Viertel-Dosis Terra Grow (1.5 ml/L). Junge Halme 3--5 cm hoch. Noch keine Ernte. Alle 3--4 Wochen duengen (Schwachzehrer -- seltene Duengung genuegt). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis, Schwachzehrer) |
| Pure Zym ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + ~0.4 (Wasser) = **~0.52 mS/cm**

### 4.3 VEGETATIVE -- Erntephase (Woche 9--20)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 20 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | **HAUPTERNTEPHASE.** Halbe Dosis Terra Grow (2.0 ml/L) + Pure Zym. Bewusst niedrig dosiert (Schwachzehrer). Ernteschnitt 3 cm ueber Boden. Nach jedem Ernteschnitt leicht nachduengen. 2--3 komplette Rueckschnitte pro Saison moeglich. Bluetenknospen frueh entfernen fuer Blattqualitaet. Alle 3--4 Wochen duengen. Im 2. Austrieb (nach Bluete/Rueckschnitt, Juli--September) identische Dosierung. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.0 (halbe Dosis, Schwachzehrer) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.16 (TG 2.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.56 mS/cm** -- unter 0.8 mS/cm Schwachzehrer-Limit

### 4.4 FLOWERING -- Bluete (Woche 21--24)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 21 | `phase_entries.week_start` |
| week_end | 24 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung waehrend der Bluete. Lila Kugelblueten sind essbar (Salat, Kraeuteressig). Fuer Blatternte: Bluetenstaende frueh entfernen, da nach der Bluete die Halmqualitaet nachlasst. Nach Abschluss der Bluete: kompletten Rueckschnitt durchfuehren -> kraeftiger 2. Austrieb (zurueck zu VEGETATIVE). Zur Saatgutgewinnung: Blueten ausreifen lassen. | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser)

### 4.5 DORMANCY -- Winterruhe (Woche 25--44)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 25 | `phase_entries.week_start` |
| week_end | 44 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Oberirdische Teile sterben ab -- nicht abschneiden, Naehrstoffe wandern zurueck in die Zwiebel! Keine Duengung. Zwiebeln im Boden belassen (winterhart bis -30 C). Topf: draussen lassen oder frostfrei bei 0--5 C. Kaltphase (6--8 Wochen <5 C) noetig fuer kraeftigen Fruehjahraustrieb (Vernalisation). Leichte Kompost- oder Laubmulchschicht optional. | `phase_entries.notes` |
| Giessplan-Override | Intervall 14 Tage (Topf: gelegentlich kontrollieren; Freiland: natuerlicher Niederschlag) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser)

---

## 5. Jahresplan (Monat-fuer-Monat)

Perennierend -- wiederholt sich jaehrlich ab dem 2. Jahr.

| Monat | KA-Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|---------------|-----------------|----------|
| Maerz | VEG (Neuaustrieb) | 2.0 | 1.0 | 0.6 | alle 3-4 Wo |
| April | VEG | 2.0 | 1.0 | 0.6 | alle 3-4 Wo |
| Mai | VEG | 2.0 | 1.0 | 0.6 | alle 3-4 Wo |
| Juni | FLOWERING | -- | -- | 0.4 | nur Wasser |
| Juli | FLO->VEG | -->2.0 | -->1.0 | 0.4->0.6 | alle 3-4 Wo |
| August | VEG (2. Austrieb) | 2.0 | 1.0 | 0.6 | alle 3-4 Wo |
| September | VEG | 2.0 | 1.0 | 0.6 | alle 3-4 Wo |
| Oktober | DOR | -- | -- | 0.4 | minimal |
| Nov--Feb | DOR | -- | -- | 0.4 | minimal |

```
Monat:        |Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|Jan|Feb|
KA-Phase:     |VEG|VEG|VEG|FLO|F→V|VEG|VEG|DOR|DOR|DOR|DOR|DOR|
Terra Grow:   |===|===|===|---|→==|===|===|---|---|---|---|---|
Pure Zym:     |===|===|===|---|→==|===|===|---|---|---|---|---|

Legende: --- = nicht verwendet, === = volle Phase-Dosis,
         →== = Uebergang zu voller Dosis
```

### Jahresverbrauch (geschaetzt)

Bei einem Schnittlauch-Horst im 3--5 L Topf, 0.2 L Giessloessung pro Duengung, Duengung alle 3--4 Wochen:

| Produkt | Formel | Verbrauch/Jahr |
|---------|--------|----------------|
| Terra Grow | (7 Duengungen x 2.0ml/L x 0.2L) = 2.8 ml | **~3 ml** |
| Pure Zym | (7 Duengungen x 1.0ml/L x 0.2L) = 1.4 ml | **~1.5 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche Terra Grow reicht fuer ueber 300 Schnittlauch-Jahre. Sinnvoll nur in Kombination mit anderen Pflanzen.

---

## 6. Schnittlauch-spezifische Praxis-Hinweise

### Substrat

- Naehrstoffreiche, humose, durchlaessige Kraeutererde, pH 6.0--7.0
- Lehmhaltige Erde wird toleriert
- Topfgroesse: 3--5 L pro Horst
- Gute Drainage, Staunaesse vermeiden
- Alle 3--4 Jahre Horst teilen (verhindert Vergreisung, foerdert kraeftigen Wuchs)

### Ernte-Technik

- **3 cm ueber Boden schneiden** -- nie tiefer, sonst Wachstumspunkt beschaedigt
- Nach dem Schnitt treibt Schnittlauch aus den Zwiebelbulben neu aus
- 2--3 komplette Rueckschnitte pro Saison moeglich
- Erste Ernte ab 15 cm Halmhoehe
- Morgenernte bevorzugt (hoechster Aromaoelgehalt)
- Blueten ebenfalls erntbar (essbar, Deko, Kraeuteressig)

### Schwefelversorgung

- Alle Allium-Arten brauchen Schwefel fuer Aromastoffe (Allicin, Thiosulfinate)
- Terra Grow enthaelt keine spezifische Schwefelquelle
- **Loesung:** Kompost im Fruehjahr einarbeiten (liefert Schwefel organisch), oder optional 0.5 g/L Bittersalz (Magnesiumsulfat) ins Giesswasser 1x/Monat

### Schnittlauch-Rost (Puccinia allii)

- Haeufigste Krankheit: orangebraune Rostpusteln auf Halmen
- Befallene Halme sofort abschneiden und im Restmuell entsorgen (nicht kompostieren)
- Gute Luftzirkulation, nicht zu dicht pflanzen
- Schachtelhalmbruehe praeventiv alle 14 Tage

### Treibkultur (Winter-Ernte)

- Horste im November ausgraben und in Toepfe setzen
- 6--8 Wochen bei 0--5 C lagern (Vernalisation)
- Dann bei 15--20 C antreiben (helle Fensterbank)
- Frische Halme innerhalb von 2--3 Wochen
- Getriebene Horste nach der Ernte zurueck ins Freiland pflanzen

### Haustier-Warnung

- **Schnittlauch ist giftig fuer Katzen und Hunde!** N-Propyl-Disulfid schaedigt Erythrozyten (haemolytische Anaemie)
- Topfkultur auf der Fensterbank: von Haustieren fernhalten
- Weniger toxisch als Knoblauch/Zwiebel, aber bei regelmaessiger Aufnahme gefaehrlich

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Schnittlauch (perennierend) \u2014 Plagron Terra",
  "description": "Perennierend-zyklischer N\u00e4hrstoffplan f\u00fcr Schnittlauch (Allium schoenoprasum). Schwachzehrer, winterhart bis \u221230\u00b0C. J\u00e4hrlicher Zyklus: Vegetativ \u2192 Bl\u00fcte \u2192 Dormanz. Zyklus-Neustart ab VEGETATIVE. Nur Terra Grow + Pure Zym.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["schnittlauch", "allium", "chives", "plagron", "terra", "erde", "kr\u00e4utergarten", "schwachzehrer", "outdoor", "perennierend", "winterhart"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 3,
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
  "week_end": 3,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Nur bei Erstaussaat. Dunkelkeimer: Samen 1\u20132 cm tief. 18\u201325\u00b0C. Keimdauer 7\u201321 Tage. Alternative: Horst-Teilung etablierter Pflanzen.",
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
      "notes": "Kein D\u00fcnger. Substrat gleichm\u00e4\u00dfig feucht halten.",
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
  "week_start": 4,
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Nur bei Erstaussaat. Viertel-Dosis Terra Grow (1.5 ml/L). Junge Halme 3\u20135 cm. Noch keine Ernte. Alle 3\u20134 Wochen d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis. Schwachzehrer \u2014 weniger ist mehr.",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
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
  "week_start": 9,
  "week_end": 20,
  "is_recurring": true,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Haupterntephase. Halbe Dosis Terra Grow (2.0 ml/L) + Pure Zym. Ernteschnitt 3 cm \u00fcber Boden. Nach jedem Schnitt leicht nachd\u00fcngen. 2\u20133 Schnitte pro Saison. Alle 3\u20134 Wochen d\u00fcngen. Wiederholt sich j\u00e4hrlich nach Dormanz (Zyklus-Neustart).",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Halbe Dosis Terra Grow + Pure Zym. Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
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
  "week_start": 21,
  "week_end": 24,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Essbare Kugelbl\u00fcten (lila). Bl\u00fctenst\u00e4nde f\u00fcr Blattqualit\u00e4t entfernen oder f\u00fcr Deko stehen lassen. Nach Bl\u00fcte: kompletter R\u00fcckschnitt \u2192 kr\u00e4ftiger 2. Austrieb.",
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
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
    }
  ]
}
```

#### DORMANCY

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "dormancy",
  "sequence_order": 5,
  "week_start": 25,
  "week_end": 44,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Oberirdische Teile sterben ab \u2014 nicht abschneiden! N\u00e4hrstoffe wandern in die Zwiebel. Winterhart bis \u221230\u00b0C. Kaltphase 6\u20138 Wochen <5\u00b0C n\u00f6tig (Vernalisation). Im Fr\u00fchjahr Neuaustrieb \u2192 Zyklus-Neustart bei VEGETATIVE.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 14,
    "preferred_time": "08:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Winterruhe)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Freiland: nat\u00fcrlicher Niederschlag gen\u00fcgt. Topf: nur Austrocknung verhindern.",
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
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Allium schoenoprasum | `spec/ref/plant-info/allium_schoenoprasum.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Giftig fuer Katzen und Hunde!** N-Propyl-Disulfid schaedigt Erythrozyten (haemolytische Anaemie, Heinz-Koerper-Bildung)
- Weniger toxisch als Knoblauch oder Zwiebel, aber bei regelmaessiger Aufnahme gefaehrlich
- Fuer Menschen unbedenklich (etabliertes Nahrungsmittel)
- Topfkultur von Haustieren fernhalten
- Blueten sind essbar

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
3. Schnittlauch Pflanzendaten: `spec/ref/plant-info/allium_schoenoprasum.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
