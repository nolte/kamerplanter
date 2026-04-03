# Naehrstoffplan: Radieschen (Direktsaat) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Raphanus sativus var. sativus (Schwachzehrer, Outdoor, Direktsaat)
> **Produkte:** Plagron Terra Bloom
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_bloom.md, spec/knowledge/plants/raphanus_sativus_var_sativus.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Radieschen (Direktsaat) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Minimalplan fuer Radieschen bei Direktsaat. Einfachster Naehrstoffplan im System: 4--6 Wochen Gesamtkultur, fast keine Duengung noetig. Optional 1x Terra Bloom in halber Dosis waehrend Knollenbildung. Schwachzehrer, Direktsaat Maerz--September, Sukzessionskultur. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | radieschen, radish, raphanus, plagron, terra, erde, outdoor, schwachzehrer, direktsaat, anfaenger, schnellkultur | `nutrient_plans.tags` |
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

**Hinweis:** 2-Tage-Intervall -- Radieschen brauchen gleichmaessige Feuchtigkeit fuer knackige, runde Knollen. Trockenstress fuehrt zu holzigen, pelzigen Knollen. In GERMINATION (1 Tag) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Radieschen (Raphanus sativus var. sativus) sind das schnellste Gemuese: 22--35 Tage von Aussaat bis Ernte. Typische Fruehlingssorte (Cherry Belle, Saxa): 22--28 Tage. Der Plan ist bewusst minimal -- Radieschen brauchen als Schwachzehrer normalerweise KEINE Duengung wenn der Boden im Vorjahr fuer Starkzehrer geduengt wurde.

| Radieschen-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|------------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1 | Woche 1 | Direktsaat 1--2 cm tief, Dunkelkeimer. Keimung in 3--7 Tagen. | false |
| Saemling + Knollenbildung | VEGETATIVE | 2--4 | Woche 2--4 | Schnelle Phase: Blaetter + Hypokotyl-Verdickung gleichzeitig. Optional 1x Terra Bloom. | false |
| Erntereife | HARVEST | 5 | Woche 5 | Knolle 2--3 cm Durchmesser. Sofort ernten -- Ueberreife = holzig! | false |

**Nicht genutzte Phasen:**
- **SEEDLING** wird in VEGETATIVE integriert (bei 4 Wochen Gesamtkultur ist eine separate Saemlingsphase unpraktisch)
- **FLOWERING** entfaellt (Bluete = Schossen = unerwuenscht)
- **FLUSHING**, **DORMANCY** entfallen

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Fuer Sukzessionssaat alle 2--3 Wochen neuen Durchlauf starten.

**Lueckenlos-Pruefung:** 1 + 3 + 1 = 5 Wochen, keine Luecken

---

## 3. Delivery Channels

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Wasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Boden gleichmaessig feucht halten. | `delivery_channels.notes` |
| method_params | drench, 0.01 L pro Pflanzstelle | `delivery_channels.method_params` |

### 3.2 Naehrloesung Knollenbildung (optional)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-knolle | `delivery_channels.channel_id` |
| Label | Knollenduengung optional (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Optional: Terra Bloom halbe Dosis (K-betont fuer Knollenbildung). Nur bei magerem Boden. Bei normalem Gartenboden (Vorfrucht-geduengt) NICHT noetig. | `delivery_channels.notes` |
| method_params | drench, 0.2 L pro Laufmeter | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Erntephase. | `delivery_channels.notes` |
| method_params | drench, 0.1 L pro Laufmeter | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Radieschen

Radieschen sind klassische Schwachzehrer und brauchen normalerweise **KEINE Duengung**. Dieser Plan verwendet optional **1x Terra Bloom in halber Dosis** waehrend der Knollenbildung -- nur fuer magere Boeden. Ziel-EC: **0.4--0.6 mS/cm** (inkl. Basis-Wasser). **Zu viel Stickstoff ist der haeufigste Anfaengerfehler** -- fuehrt zu ueppigem Laub, spindligen Knollen.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Bloom (2-2-4) | 0.10 | 20 | Vegetativ (optional, 1x) |

### 4.1 GERMINATION -- Keimung (Woche 1)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 1 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Direktsaat 1--2 cm tief, Reihenabstand 10--15 cm. Dunkelkeimer. Keimung in 3--7 Tagen bei 15--20 degC. Boden gleichmaessig feucht halten. KEIN Duenger. KEIN frischer Stallmist (deformierte Knollen, Madenbefall). | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 VEGETATIVE -- Saemling + Knollenbildung (Woche 2--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 2 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Vereinzeln auf 3--5 cm bei zu dichter Saat. Optional 1x Terra Bloom 1.5 ml/L (halbe Dosis, K-betont) in Woche 3 -- NUR bei magerem Boden. Bei normalem Gartenboden (Starkzehrer-Vorfrucht geduengt) ist KEINE Duengung noetig. Gleichmaessig giessen! Trockenstress = holzige, pelzige Knollen. Temperaturen ueber 25 degC + Langtag >14h = Schossgefahr. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-knolle**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 1.5 (halbe Dosis, optional, 1x) |

**EC-Budget:** 0.15 (TB 1.5ml) + ~0.4 (Wasser) = **~0.55 mS/cm** ✓

### 4.3 HARVEST -- Erntereife (Woche 5)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 5 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Ernte wenn Knolle 2--3 cm Durchmesser hat und leicht aus der Erde ragt. NICHT zu lange warten -- ueberreife Radieschen werden holzig, schwammig und bitter. Ernte morgens, Blaetter sofort abdrehen (ziehen Feuchtigkeit aus der Knolle). Lagerung: gekuehlt in feuchtem Tuch 5--7 Tage. | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Sukzessionskultur: Alle 2--3 Wochen nachsaeen, Maerz--September. Jeder Satz dauert nur 4--5 Wochen.

| Monat | Aktion | Terra Bloom ml/L | EC gesamt (ca.) | Hinweise |
|-------|--------|------------------|-----------------|----------|
| Maerz | 1. Saat | -- (optional 1x 1.5) | 0.4 (0.55) | Vliesabdeckung, fruehe Sorten |
| April | 2.+3. Saat + Ernte 1 | -- (optional 1x 1.5) | 0.4 (0.55) | Sukzessionssaat alle 2--3 Wo |
| Mai | Fortlaufend | -- (optional 1x 1.5) | 0.4 (0.55) | Erdfloh-Kontrolle (Netz!) |
| Juni | Achtung Hitze | -- | 0.4 | Schossgefahr bei >25 degC + Langtag |
| Juli | Sommerpause erwaegen | -- | -- | Bei Hitze Pause oder Halbschatten |
| August | Herbstsaat starten | -- (optional 1x 1.5) | 0.4 (0.55) | Kuerzere Tage = weniger Schossen |
| September | Letzte Saat | -- | 0.4 | Vlies bei fruehen Froesten |

```
Satz-Zyklus (5 Wochen):
Woche:        |W1 |W2 |W3 |W4 |W5 |
KA-Phase:     |GER|VEG|VEG|VEG|HAR|
Terra Bloom:  |---|---|?--|---|---|

Legende: --- = nicht verwendet, ?-- = optional 1x halbe Dosis
```

### Jahresverbrauch (geschaetzt)

Bei 6--8 Sukzessionssaetzen pro Saison, je 1 Laufmeter, 0.2 L Giessloessung:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Bloom | (8 Saetze x 1 Duengung x 1.5ml/L x 0.2L) = 2.4 ml | **~2.5 ml** (wenn ueberhaupt) |

**Kosten-Schaetzung:** Vernachlaessigbar. Radieschen sind die sparsamste Kultur im gesamten System.

---

## 6. Radieschen-spezifische Praxis-Hinweise

### Warum fast keine Duengung?

- Radieschen sind **Schwachzehrer** mit nur 4--5 Wochen Kulturzeit
- In normal bewirtschaftetem Gartenboden genuegen die **Restnaehrstoffe der Vorkultur**
- **Stickstoff-Ueberschuss** ist der haeufigste Fehler: ueppiges Blattwerk, spindlige Knollen
- Dieser Plan nutzt Terra Bloom (K-betont, 2-2-4) nur als optionale Einmal-Gabe fuer magere Boeden

### Schossgefahr

- Temperaturen ueber 25 degC + Langtag (>14h) = Schossen (Pflanze bildet Bluetenstiel statt Knolle)
- **Sommerpause** Juli--August erwaegen oder schattigen Standort waehlen
- Schossfeste Sorten: 'Pernot', 'Rudi', 'Sora'
- Herbstaussaat (August--September) ist oft ergiebiger als Hochsommer

### Erdfloh (Phyllotreta spp.)

- **Hauptschaedling!** Zahlreiche kleine Loecher in Blaettern (Siebfrassbild)
- **Kulturschutznetz** (Maschenweite 0.8 mm) direkt nach Aussaat -- effektivste Massnahme
- Gesteinsmehl auf Blaetter stauben (Fraesshemmung)
- Neemoel 0.3--0.5% als Blattspruehung

### Ideale Nachbarschaft

- **Mit Moehren:** Radieschen als Markierungssaat (schnellkeimend, markiert langsam keimende Moehrenreihen)
- **Nach Starkzehrern:** Radieschen nutzen Restnaehrstoffe optimal
- **Vor Starkzehrern:** Radieschen hinterlassen gelockerten Boden

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Radieschen (Direktsaat) \u2014 Plagron Terra",
  "description": "Minimalplan f\u00fcr Radieschen. 5 Wochen Gesamtkultur, fast keine D\u00fcngung. Optional 1x Terra Bloom halbe Dosis. Einfachster Plan im System. Sukzessionskultur M\u00e4rz\u2013September.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["radieschen", "radish", "raphanus", "plagron", "terra", "erde", "outdoor", "schwachzehrer", "direktsaat", "anf\u00e4nger", "schnellkultur"],
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

### 7.2 NutrientPlanPhaseEntry (3 Eintraege)

#### GERMINATION

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 1,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Direktsaat 1\u20132 cm tief, Dunkelkeimer. Keimung in 3\u20137 Tagen. KEIN D\u00fcnger, KEIN frischer Mist.",
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
      "label": "Wasser Keimung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Boden gleichm\u00e4\u00dfig feucht.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.01}
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
  "week_start": 2,
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Optional 1x Terra Bloom 1.5 ml/L (halbe Dosis) in Woche 3 \u2014 NUR bei magerem Boden. Normalerweise keine D\u00fcngung n\u00f6tig. Vereinzeln auf 3\u20135 cm. Gleichm\u00e4\u00dfig gie\u00dfen!",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-knolle",
      "label": "Knollend\u00fcngung optional (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Optional, nur bei magerem Boden. Terra Bloom halbe Dosis, K-betont.",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 1.5, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
    }
  ]
}
```

#### HARVEST

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "harvest",
  "sequence_order": 3,
  "week_start": 5,
  "week_end": 5,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Ernte bei 2\u20133 cm Knollendurchmesser. Nicht zu lange warten \u2014 \u00fcberreif = holzig! Morgens ernten, Bl\u00e4tter sofort abdrehen.",
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Ernte)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.1}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Bloom | `spec/knowledge/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Raphanus sativus var. sativus | `spec/knowledge/plants/raphanus_sativus_var_sativus.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Vollstaendig ungiftig** fuer Menschen, Katzen und Hunde
- Senfoele (Isothiocyanate) verursachen die Schaerfe, sind aber gesundheitsfoerdernd
- Blaetter sind essbar und naehrstoffreich (Salat, Pesto)
- Hunde/Katzen koennen Radieschen in kleinen Mengen fressen

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Ausserhalb der Reichweite von Kindern aufbewahren

---

## Quellenverzeichnis

1. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
2. Raphanus sativus Pflanzendaten: `spec/knowledge/plants/raphanus_sativus_var_sativus.md`
3. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
4. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
