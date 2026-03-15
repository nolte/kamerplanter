# Naehrstoffplan: Moehre (Direktsaat Fruehjahr) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Daucus carota subsp. sativus (Schwachzehrer/Mittelzehrer, Outdoor, Direktsaat)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/daucus_carota.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Moehre (Direktsaat Fruehjahr) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Moehren (Nantes-Typ) bei Direktsaat im Fruehling. Plagron Terra-Linie mit 3 Produkten. Schwachzehrer-Strategie mit Kalium-Betonung (Wurzelgemuese). KEIN frischer organischer Duenger (Beinigkeit!). Terra Bloom statt Terra Grow in der Hauptwachstumsphase wegen K>N-Anforderung. Annuell, Direktsaat Maerz--April, Ernte Juli--Oktober. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | moehre, karotte, carrot, daucus, plagron, terra, erde, outdoor, schwachzehrer, wurzelgemuese, direktsaat | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 3-Tage-Intervall als Basis fuer Freiland-Direktsaat. Moehren brauchen gleichmaessige Feuchtigkeit -- Schwankungen (trocken-nass) verursachen Aufplatzen der Wurzeln. In GERMINATION (1 Tag, leichtes Spruehen) und HARVEST (5 Tage, reduziert) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Moehren (Daucus carota subsp. sativus) sind botanisch zweijaerig, werden aber als einjaehrige Kultur im 1. Jahr vor der Bluete geerntet (Speicherwurzel). Typischer Nantes-Typ: 70--90 Tage bis Erntereife. Direktsaat ab Maerz, kein Pikieren/Umtopfen (Pfahlwurzel!).

| Moehren-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|---------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--3 | Maerz (frueh) | Direktsaat ab 5 degC Bodentemperatur. Langsame Keimung (10--21 Tage). Boden MUSS gleichmaessig feucht bleiben. | false |
| Saemling | SEEDLING | 4--6 | Maerz--April | Keimblaetter + erste gefiederte Blaetter. Vereinzeln auf 3--5 cm Abstand. Kein Duenger. | false |
| Vegetatives Wachstum (Blatt + Wurzelaufbau) | VEGETATIVE | 7--14 | April--Juni | Hauptwachstumsphase: Blattrosette + Speicherwurzelbildung. K-betonte Duengung (Terra Bloom). | false |
| Erntereife | HARVEST | 15--18 | Juli--August | Wurzeln haben volle Groesse und Farbe. Duengung einstellen. Ernte bei trockenem Wetter. | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Ernte vor Bluete im 1. Jahr; Bluete ist unerwuenscht = Schossen)
- **FLUSHING** entfaellt (Schwachzehrer mit minimaler Salzbelastung im Freiland)
- **DORMANCY** entfaellt (annuell kultiviert)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Der Plan laeuft einmalig durch (18 Wochen). Fuer Staffelsaat (Sukzession) neuen Durchlauf starten.

**Lueckenlos-Pruefung:** 3 + 3 + 8 + 4 = 18 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Kleine Volumina (Schwachzehrer, Freiland).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Feiner Spruehstrahl, Samen nicht ausschwemmen. Boden gleichmaessig feucht halten (Abdeckung mit Vlies/Brett bis Keimung). | `delivery_channels.notes` |
| method_params | drench (spray), 0.02 L pro Pflanzstelle | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum (K-betont)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum-k | `delivery_channels.channel_id` |
| Label | Wachstumsduengung K-betont (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom (K-betont, 2-2-4) statt Terra Grow (3-1-3), da Wurzelgemuese K>N benoetigt. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. Nicht ueber das Kraut giessen (Alternaria-Risiko). | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Laufmeter Reihe | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Erntephase -- Duengung einstellen fuer bessere Lagerfaehigkeit. 2--3 Tage vor Ernte nicht giessen. | `delivery_channels.notes` |
| method_params | drench, 0.3 L pro Laufmeter Reihe | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Moehren

Moehren sind im Steckbrief als Mittelzehrer (medium_feeder) klassifiziert, reagieren aber empfindlich auf Ueberduengung -- besonders N-Ueberangebot foerdert Kraut auf Kosten der Wurzelbildung. Fuer den Plagron-Terra-Plan wird daher eine **Schwachzehrer-Strategie** gewaehlt: EC-Ziel **0.4--0.8 mS/cm** (inkl. Basis-Wasser). **Kalium ist der wichtigste Naehrstoff** -- foerdert Wurzelentwicklung, Geschmack, Farbe und Lagerfaehigkeit. Deshalb Terra Bloom (2-2-4, K-betont) statt Terra Grow (3-1-3, N-betont).

**KEIN frischer organischer Duenger!** Foerdert Beinigkeit (verzweigte, missgeformte Wurzeln) und lockt Moehrenfliegen an.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Bloom (2-2-4) | 0.10 | 20 | Vegetativ (K-betont fuer Wurzelbildung) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ (Substratpflege) |

**Warum Terra Bloom statt Terra Grow:** Terra Grow liefert NPK 3-1-3 mit N-Betonung -- kontraproduktiv fuer Wurzelgemuese. Terra Bloom liefert NPK 2-2-4 mit K>N, was dem Steckbrief-Ideal (NPK 1-1-2 vegetativ, 0-1-2 Ernte) naeher kommt. Der N-Anteil von Terra Bloom (2.1%) ist ausreichend, aber nicht uebermaessig.

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
| Hinweise | Direktsaat in feine, steinfreie, lockere Erde. Samen nur 1 cm tief (Lichtkeimer). Saatrillen 1--2 cm tief, Reihenabstand 25--30 cm. Boden MUSS 10--21 Tage gleichmaessig feucht bleiben -- Austrocknung fuehrt zu lueckigem Aufgang. Vliesabdeckung empfohlen. KEIN Duenger. Keimtemperatur 10--20 degC (optimal 15 degC). | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichtes Spruehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 4--6)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 6 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keimblaetter sichtbar (fadenfoermig, untypisch). Vereinzeln auf 3--5 cm Abstand, sobald Pflanzen 3--5 cm hoch sind. Kein Duenger -- Boden liefert Grundversorgung. Boden gleichmaessig feucht halten, nicht austrocknen lassen. | `phase_entries.notes` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.3 VEGETATIVE -- Blatt- und Wurzelaufbau (Woche 7--14)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 7 | `phase_entries.week_start` |
| week_end | 14 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Hauptwachstumsphase: Blattrosette und Speicherwurzel bilden sich parallel. Terra Bloom 2.0 ml/L (K-betont, NPK 2-2-4) + Pure Zym. Alle 14 Tage duengen. Steckbrief empfiehlt NPK 1-1-2 -- Terra Bloom liefert K>N, was fuer Wurzelgemuese passt. N bewusst niedrig halten -- ueppiges Kraut auf Kosten der Wurzel vermeiden! Anhaeufeln (Erde an Wurzelschulter ziehen) verhindert Vergruenen. Gleichmaessig giessen -- Schwankungen verursachen Aufplatzen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum-k**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| target_ph | 6.5 |
| Terra Bloom ml/L | 2.0 (Schwachzehrer-Dosis, K-betont) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.20 (TB 2.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.60 mS/cm** ✓

**EC-Abweichung vom Steckbrief:** Steckbrief-Optimum vegetativ: 0.8--1.4 mS/cm. Der Zielwert 0.6 mS/cm liegt bewusst darunter -- konservative Schwachzehrer-Strategie, da N-Ueberduengung bei Moehren die Wurzelbildung hemmt und Lagerfaehigkeit verschlechtert.

### 4.4 HARVEST -- Erntereife (Woche 15--18)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 15 | `phase_entries.week_start` |
| week_end | 18 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Duengung 4 Wochen vor Ernte einstellen verbessert Lagerfaehigkeit. 2--3 Tage vor Ernte nicht giessen. Erntezeitpunkt: Wurzeldurchmesser 2--4 cm (sortenabhaengig), volle Ausfaerbung. Bei trockenem Wetter ernten. Kraut abdrehen (nicht schneiden). Lagerung: 0--2 degC, 95% Luftfeuchtigkeit (in Sand einschlagen). | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (reduziert) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Direktsaat-Zyklus, Start Anfang Maerz (Nantes-Typ, ca. 90 Tage bis Ernte).

| Monat | KA-Phase | Terra Bloom ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|------------------|---------------|-----------------|----------|
| Maerz | GERM | -- | -- | 0.4 | spray taegl. |
| April | SEED->VEG | -->2.0 | -->1.0 | 0.4->0.6 | alle 14d |
| Mai | VEG | 2.0 | 1.0 | 0.6 | alle 14d |
| Juni | VEG | 2.0 | 1.0 | 0.6 | alle 14d |
| Juli | VEG->HARV | 2.0->0 | 1.0->-- | 0.6->0.4 | alle 14d->-- |
| August | HARVEST | -- | -- | 0.4 | minimal |

```
Monat:        |Mär|Apr|Mai|Jun|Jul|Aug|
KA-Phase:     |GER|S→V|VEG|VEG|V→H|HAR|
Terra Bloom:  |---|-->|===|===|#--|---|
Pure Zym:     |---|-->|===|===|#--|---|

Legende: --- = nicht verwendet, --> = Start,
         === = volle Phase-Dosis, #-- = auslaufend
```

### Jahresverbrauch (geschaetzt)

Bei 1 Laufmeter Moehrenreihe (ca. 20--25 Pflanzen), 0.5 L Giessloessung pro Duengung, Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Bloom | (8 Duengungen x 2.0ml/L x 0.5L) = 8.0 ml | **~8 ml** |
| Pure Zym | (8 Duengungen x 1.0ml/L x 0.5L) = 4.0 ml | **~4 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche reicht fuer hunderte Laufmeter Moehrenreihe. Sinnvoll nur in Kombination mit anderen Pflanzen.

---

## 6. Moehren-spezifische Praxis-Hinweise

### KEIN frischer organischer Duenger!

- **Kritischster Punkt:** KEIN frischer Stallmist, KEIN frischer Kompost direkt an Moehren
- Frische organische Substanz verursacht **Beinigkeit** (verzweigte, gespaltene, missgeformte Wurzeln)
- Frischer Mist lockt die **Moehrenfliege** (Psila rosae) an
- Nur gut abgelagerten Kompost im Herbst VOR der Saison einarbeiten
- Plagron Terra-Produkte als mineralische Ergaenzung vermeiden dieses Problem

### Boden-Vorbereitung

- Boden tiefgruendig lockern (mind. 30 cm)
- Steine, Wurzelreste und grobe Erdklumpen entfernen (sonst krumme Moehren)
- Fein kruemelig harken -- je feiner, desto glatter die Wurzeln
- Leicht sandige Boeden sind ideal; schwere Tonboeden mit Sand verbessern
- pH 6.0--7.0 (Moehren vertragen leicht saure bis neutrale Boeden)

### Moehrenfliege (Psila rosae)

- **Hauptschaedling!** Rostbraune Fraessgaenge in der Wurzel
- **Kulturschutznetz** (Maschenweite 0.8 mm) ist die beste Massnahme -- direkt nach Saat aufspannen
- **Mischkultur mit Zwiebeln:** Abwechselnde Reihen Moehren/Zwiebeln -- Duftverwirrung
- Nicht bei Windstille ernten/jaeten -- der Geruecksausstoss lockt die Fliege an
- Spaete Aussaat (ab Juni) reduziert Befall der 1. Fliegen-Generation

### Staffelsaat (Sukzession)

- Alle 3--4 Wochen nachsaeen (Maerz--Juli) fuer kontinuierliche Ernte (Juni--November)
- Fruehoehren (Nantes): 70--90 Tage, Lagersorten (Flakkee): 120--150 Tage
- Spaete Saetze (Juli) koennen bei Mulchschutz bis November im Boden bleiben

### Anhaeufeln

- Erde an die Wurzelschulter ziehen, wenn die Krone aus dem Boden ragt
- Verhindert Vergruenen (gruene Schulter enthalt Solanin-aehnliche Bitterstoffe)
- Gleichzeitig Unkrautunterdrueckung

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "M\u00f6hre (Direktsaat Fr\u00fchjahr) \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr M\u00f6hren (Nantes-Typ) bei Direktsaat. Plagron Terra-Linie, 2 Produkte. K-betonte Schwachzehrer-Strategie (Terra Bloom statt Terra Grow). KEIN frischer organischer D\u00fcnger. 18 Wochen (M\u00e4rz\u2013August).",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["m\u00f6hre", "karotte", "carrot", "daucus", "plagron", "terra", "erde", "outdoor", "schwachzehrer", "wurzelgem\u00fcse", "direktsaat"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 3,
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
  "week_end": 3,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Direktsaat in feine, steinfreie Erde. Lichtkeimer, nur 1 cm tief. Boden 10\u201321 Tage gleichm\u00e4\u00dfig feucht halten. Vliesabdeckung empfohlen. KEIN D\u00fcnger.",
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
      "notes": "Kein D\u00fcnger. Feiner Spr\u00fchstrahl, Samen nicht ausschwemmen.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
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
  "week_end": 6,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Vereinzeln auf 3\u20135 cm Abstand. Kein D\u00fcnger \u2014 Boden liefert Grundversorgung. Boden gleichm\u00e4\u00dfig feucht halten.",
  "delivery_channels": [
    {
      "channel_id": "wasser-keimung",
      "label": "Spr\u00fchwasser S\u00e4mling",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Gleichm\u00e4\u00dfige Feuchtigkeit.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.03}
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
  "week_start": 7,
  "week_end": 14,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom 2 ml/L (K-betont f\u00fcr Wurzelbildung) + Pure Zym. Alle 14 Tage d\u00fcngen. N bewusst niedrig \u2014 \u00fcppiges Kraut auf Kosten der Wurzel vermeiden! Anh\u00e4ufeln bei sichtbarer Wurzelschulter. Gleichm\u00e4\u00dfig gie\u00dfen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum-k",
      "label": "Wachstumsd\u00fcngung K-betont (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Pure Zym. Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 pH pr\u00fcfen. Nicht \u00fcber das Kraut gie\u00dfen (Alternaria).",
      "target_ec_ms": 0.6,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 2.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
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
  "week_start": 15,
  "week_end": 18,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. 4 Wochen vor Ernte einstellen f\u00fcr bessere Lagerf\u00e4higkeit. 2\u20133 Tage vor Ernte nicht gie\u00dfen. Bei trockenem Wetter ernten, Kraut abdrehen.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 5,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Erntephase)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Nur bei Trockenheit gie\u00dfen. Vor Ernte 2\u20133 Tage Pause.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Daucus carota subsp. sativus | `spec/ref/plant-info/daucus_carota.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Speicherwurzel essbar und unbedenklich** fuer Menschen und Haustiere
- **Kraut:** Enthaelt Furanocumarine -- phototoxisch bei Hautkontakt + Sonnenlicht (Photodermatitis). Bei der Gartenarbeit (Ernten, Jaeten) koennen Furanocumarine auf die Haut gelangen. Bei anschliessender Sonnenexposition: Roetung, Blasenbildung, langanhaltende Pigmentierung. **Schutzmassnahme:** Bei intensiver Krautarbeit Handschuhe und Langarm tragen, oder Arbeiten auf Abendstunden verlegen.
- **Falcarinol** im Kraut kann Kontaktdermatitis ausloesen -- Handschuhe bei Empfindlichkeit
- **Kreuzallergie:** Ca. 10% der Birkenpollenallergiker reagieren auf rohe Moehren (Orales Allergiesyndrom)
- ASPCA: Daucus carota als ungiftig fuer Katzen und Hunde gelistet

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- **Essbare-Wurzel-Hinweis:** Duengung 4 Wochen vor Ernte einstellen

---

## Quellenverzeichnis

1. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
2. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
3. Daucus carota Pflanzendaten: `spec/ref/plant-info/daucus_carota.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
