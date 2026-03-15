# Naehrstoffplan: Chicoree (Freiland + Treiberei) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Cichorium intybus (Mittelzehrer, Outdoor Freiland + Indoor Treiberei im Dunkeln)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/cichorium_intybus.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Chicoree (Freiland + Treiberei) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Zweiteiliger Plan fuer Chicoree (Cichorium intybus): Phase 1 Freiland (Mai--Oktober, Wurzelaufbau), Phase 2 Treiberei im Dunkeln (Nov--Dez, Etiolierung). Plagron Terra-Linie mit 3 Produkten. Mittelzehrer. Freiland-Direktsaat, dann Wurzeln roden und dunkel bei 15--18 degC treiben. Chicoreezapfen nach 3--4 Wochen erntereif. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | chicoree, zichorie, wegwarte, chicory, cichorium, plagron, terra, erde, outdoor, mittelzehrer, treiberei, etiolierung | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 4 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 4-Tage-Intervall als Basis fuer Freiland. Zichorie ist dank tiefer Pfahlwurzel sehr trockenheitsresistent -- uebermaessiges Giessen foerdert Faeulnis. In GERMINATION (2 Tage) und DORMANCY/HARVEST (Treiberei, 3 Tage) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Chicoree (Cichorium intybus) wird als biennial/annual kultiviert: Im 1. Jahr Wurzelaufbau (Freiland), dann Wurzeln roden und im Dunkeln treiben (Etiolierung). Die Treiberei produziert die typischen blassgelben Chicoreezapfen. Der Plan hat 2 deutliche Abschnitte: Freiland (Mai--Oktober) und Treiberei (November--Dezember).

| Chicoree-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|----------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--3 | Mai | Direktsaat Mai/Juni, Dunkelkeimer, 1--2 cm tief. Keimung 10--21 Tage. | false |
| Saemling | SEEDLING | 4--7 | Juni | Jungpflanzen mit Blattrosette. Vereinzeln auf 25--30 cm. Leichte Duengung. | false |
| Vegetatives Wachstum (Wurzelaufbau) | VEGETATIVE | 8--20 | Juli--Oktober | Hauptphase: Blattrosette + Pfahlwurzelaufbau. Maessige Duengung, K-Betonung fuer Wurzel. | false |
| Rodung + Treiberei-Vorbereitung | DORMANCY | 21--24 | Oktober--November | Wurzeln roden, Kraut auf 3 cm kuerzen, in Sand/Erde bei 15--18 degC im Dunkeln einstellen. KEINE Duengung. | false |
| Treiberei (Etiolierung) + Ernte | HARVEST | 25--28 | November--Dezember | Chicoreezapfen wachsen im Dunkeln aus der Wurzel. Nach 3--4 Wochen erntereif (15--20 cm). KEIN Licht! | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Bluete ist unerwuenscht im Chicoree-Anbau -- wuerde die Wurzel entwerten)
- **FLUSHING** entfaellt (Freiland + Treiberei ohne Salzakkumulation)

**Lueckenlos-Pruefung:** 3 + 4 + 13 + 4 + 4 = 28 Wochen, keine Luecken

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
| method_params | drench, 0.02 L pro Pflanzstelle | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow (frueher Wachstum) oder Terra Bloom (spaetes Wachstum, K-betont) + Pure Zym. Reihenfolge: Terra Grow/Bloom -> Pure Zym -> pH pruefen. | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Nur Wasser (Treiberei)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-treiberei | `delivery_channels.channel_id` |
| Label | Wasser Treiberei (dunkel) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | KEIN Duenger, KEIN Licht. Substrat (Sand/Erde) leicht feucht halten. Zu viel Wasser = Faeulnis. | `delivery_channels.notes` |
| method_params | drench, 0.1 L pro Wurzel | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Chicoree

Chicoree ist ein Mittelzehrer. Der Plan teilt sich in 2 Abschnitte: Freiland (EC 0.4--0.8 mS/cm, maessige Duengung) und Treiberei (EC 0.0, keine Duengung). N massvoll dosieren -- Ueberangebot erhoet Nitratgehalt in Blaettern und hemmt Wurzelentwicklung. Kalium foerdern fuer Wurzelaufbau (wichtig fuer Treiberei-Qualitaet).

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, fruehes Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | spaetes Vegetativ (K-Betonung fuer Wurzel) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ (durchgehend) |

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
| Hinweise | Direktsaat Mai/Juni, 1--2 cm tief (Dunkelkeimer). Reihenabstand 30--40 cm. Keimung 10--21 Tage bei 18--20 degC. Boden gleichmaessig feucht halten. KEIN Duenger. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 4--7)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 7 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Vereinzeln auf 25--30 cm Abstand. Viertel-Dosis Terra Grow (1.5 ml/L). Blattrosette bildet sich. Unkraut jaeten. Alle 14 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| target_ph | 6.5 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |

**EC-Budget:** 0.12 (TG 1.5ml) + ~0.4 (Wasser) = **~0.52 mS/cm** ✓

### 4.3 VEGETATIVE -- Wurzelaufbau (Woche 8--20)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 8 | `phase_entries.week_start` |
| week_end | 20 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Hauptwachstumsphase: Blattrosette und Pfahlwurzel bauen sich auf. Woche 8--12: Terra Grow 2.5 ml/L (halbe Dosis) + Pure Zym. Ab Woche 13: Umstellung auf Terra Bloom 2.5 ml/L (K-betont fuer Wurzeleinlagerung) + Pure Zym. Alle 14 Tage duengen. N massvoll -- erhoet sonst Nitrat in Blaettern. Beetstaendige Aeussere-Blaetter-Ernte moeglich (Herzblatter stehen lassen). Wenn Bluetenstaengel erscheinen: sofort entfernen (Wurzel wird sonst holzig). Ab Woche 18 Duengung einstellen (4 Wochen vor Rodung). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum (frueher Abschnitt W8--12)**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| target_ph | 6.5 |
| Terra Grow ml/L | 2.5 (halbe Dosis, W8--12) |
| Pure Zym ml/L | 1.0 |

**EC-Budget (W8--12):** 0.20 (TG 2.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.60 mS/cm** ✓

**Delivery Channel: naehrloesung-wachstum (spaeter Abschnitt W13--17)**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.7 |
| target_ph | 6.5 |
| Terra Bloom ml/L | 2.5 (halbe Dosis, K-betont, W13--17) |
| Pure Zym ml/L | 1.0 |

**EC-Budget (W13--17):** 0.25 (TB 2.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.65 mS/cm** ✓

**W18--20:** Keine Duengung, nur Wasser (Vorbereitung auf Rodung).

### 4.4 DORMANCY -- Rodung + Treiberei-Vorbereitung (Woche 21--24)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 21 | `phase_entries.week_start` |
| week_end | 24 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | KEINE Duengung. Oktober/November: Wurzeln roden (vorsichtig ausgraben, nicht beschaedigen). Kraut auf 3 cm ueber der Wurzelkrone kuerzen. Seitenwurzeln entfernen. Wurzeln 1--2 Wochen bei 0--5 degC lagern (Vernalisation-Impuls, nicht zwingend fuer Witloof-Treiberei aber foerdert Zapfenbildung). Dann aufrecht in Eimer/Kiste mit feuchtem Sand oder Erde einstellen, 15--18 degC, ABSOLUT DUNKEL. | `phase_entries.notes` |
| Giessplan-Override | Intervall 7 Tage (minimal, Wurzellagerung) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-treiberei**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.5 HARVEST -- Treiberei + Ernte (Woche 25--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 25 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | KEINE Duengung, KEIN Licht! Chicoreezapfen (Chicons) wachsen aus der Wurzelkrone im Dunkeln. Substrat leicht feucht halten (nicht nass -- Faeulnisgefahr). Temperatur 15--18 degC. Ernte nach 3--4 Wochen bei 15--20 cm Laenge. Zapfen mit Messer an der Wurzelkrone abschneiden. Manche Wurzeln treiben ein zweites Mal (kleinere Zapfen). LICHT-EINFALL VERMEIDEN: Licht vergruent die Zapfen und macht sie bitter. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (leicht feucht) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-treiberei**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|---------------|-----------------|----------|
| Mai | GERM | -- | -- | -- | 0.4 | alle 2d |
| Juni | SEED | 1.5 | -- | -- | 0.5 | alle 14d |
| Juli | VEG | 2.5 | -- | 1.0 | 0.6 | alle 14d |
| August | VEG | 2.5 | -- | 1.0 | 0.6 | alle 14d |
| September | VEG | -- | 2.5 | 1.0 | 0.65 | alle 14d |
| Oktober | VEG->DOR | -- | -->0 | -->0 | 0.65->0.4 | alle 14d->-- |
| November | DOR->HARV | -- | -- | -- | 0.4 | treiberei |
| Dezember | HARVEST | -- | -- | -- | 0.4 | treiberei |

```
Monat:        |Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:     |GER|SEE|VEG|VEG|VEG|V→D|D→H|HAR|
Terra Grow:   |---|#--|##-|##-|---|---|---|---|
Terra Bloom:  |---|---|---|---|##-|#--|---|---|
Pure Zym:     |---|---|===|===|===|#--|---|---|

Legende: --- = nicht verwendet, #-- = Viertel-Dosis,
         ##- = halbe Dosis, === = volle Phase-Dosis
```

### Jahresverbrauch (geschaetzt)

Bei 10 Pflanzen, 0.4 L Giessloessung pro Duengung, Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (2 Dg x 1.5ml/L x 0.4L + 4 Dg x 2.5ml/L x 0.4L) x 10 = (1.2 + 4.0) x 10 = 52 ml | **~50 ml** |
| Terra Bloom | (4 Dg x 2.5ml/L x 0.4L) x 10 = 40 ml | **~40 ml** |
| Pure Zym | (10 Dg x 1.0ml/L x 0.4L) x 10 = 40 ml | **~40 ml** |

---

## 6. Chicoree-spezifische Praxis-Hinweise

### Treiberei im Dunkeln (Etiolierung)

- **Kernprozess:** Die gerodeten Wurzeln treiben im Dunkeln blassgelbe, zarte Blattzapfen (Chicons)
- **Temperatur:** 15--18 degC (zu warm = lockere Zapfen, zu kalt = langsam)
- **ABSOLUT DUNKEL:** Jeder Lichteinfall vergruent die Zapfen und macht sie bitter
- **Substrat:** Feuchter Sand oder Erde, Wurzeln aufrecht einstellen, Krone 2--3 cm ueber Substrat
- **Abdeckung:** Eimer umstuelpen, Karton ueberstuelpen, dunkler Kellerraum
- **Dauer:** 3--4 Wochen bis zur Ernte (15--20 cm Zapfenlaenge)
- **Zweittrieb:** Manche Wurzeln treiben nach dem Abschneiden nochmals (kleinere Zapfen)

### Beetvorbereitung Freiland

- Tiefgruendiger, humusreicher Boden (30 cm lockern, Pfahlwurzel braucht Platz)
- pH 6.0--7.0 (kalkvertraeglich)
- Kompost im Fruehjahr einarbeiten (3--4 L/m2)
- Sonniger Standort bevorzugt

### Bitterkeit kontrollieren

- Blaetter werden bei Hitze ueber 25 degC bitterer (Intybin-Konzentration steigt)
- Kuehle Temperaturen (15--18 degC) produzieren mildere Blaetter
- Treiberei im Dunkeln reduziert Bitterkeit stark (Etiolierung unterdrueckt Chlorophyll und Bitterstoffe)
- Blanching (Blaetter 30 Min in Eiswasser) reduziert Bitterkeit weiter

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer Asteraceae (Zichorie, Endivie, Sonnenblume, Radicchio)
- Ideale Vorfrucht: Starkzehrer (Kohl, Kartoffel)
- Ideale Nachfrucht: Schwachzehrer (Radieschen, Feldsalat)

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Chicor\u00e9e (Freiland + Treiberei) \u2014 Plagron Terra",
  "description": "Zweiteiliger Plan: Freiland-Wurzelaufbau (Mai\u2013Oktober) + Treiberei im Dunkeln (Nov\u2013Dez). Plagron Terra-Linie, 3 Produkte. Mittelzehrer. 28 Wochen Gesamtdauer.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["chicor\u00e9e", "zichorie", "wegwarte", "chicory", "cichorium", "plagron", "terra", "erde", "outdoor", "mittelzehrer", "treiberei", "etiolierung"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 4,
    "preferred_time": "07:00",
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
  "notes": "Direktsaat Mai/Juni, 1\u20132 cm tief (Dunkelkeimer). Reihenabstand 30\u201340 cm. Keimung 10\u201321 Tage. KEIN D\u00fcnger.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 2,
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
  "week_end": 7,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Vereinzeln auf 25\u201330 cm. Viertel-Dosis Terra Grow (1.5 ml/L). Alle 14 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung S\u00e4mling (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis.",
      "target_ec_ms": 0.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.4}
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
  "week_start": 8,
  "week_end": 20,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "W8\u201312: Terra Grow 2.5 ml/L + Pure Zym. Ab W13: Umstellung auf Terra Bloom 2.5 ml/L (K-betont f\u00fcr Wurzeleinlagerung) + Pure Zym. Alle 14 Tage d\u00fcngen. Ab W18 D\u00fcngung einstellen (4 Wochen vor Rodung). Bl\u00fctenst\u00e4ngel sofort entfernen!",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "W8\u201312: Terra Grow halbe Dosis. Ab W13: Terra Bloom halbe Dosis (K-betont). + Pure Zym. Ab W18: nur Wasser.",
      "target_ec_ms": 0.65,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 2.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.4}
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
  "week_start": 21,
  "week_end": 24,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Wurzeln roden, Kraut auf 3 cm k\u00fcrzen. 1\u20132 Wochen bei 0\u20135\u00b0C lagern. Dann in Sand/Erde bei 15\u201318\u00b0C im Dunkeln einstellen. KEINE D\u00fcngung.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 7,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-treiberei",
      "label": "Wasser Treiberei-Vorbereitung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Substrat minimal feucht halten.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
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
  "week_start": 25,
  "week_end": 28,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Treiberei im Dunkeln. KEIN D\u00fcnger, KEIN Licht! Chicor\u00e9ezapfen wachsen aus der Wurzelkrone. Ernte nach 3\u20134 Wochen bei 15\u201320 cm. Substrat leicht feucht halten.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-treiberei",
      "label": "Wasser Treiberei (dunkel)",
      "application_method": "drench",
      "enabled": true,
      "notes": "KEIN D\u00fcnger, KEIN Licht. Substrat leicht feucht.",
      "target_ec_ms": 0.0,
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
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Cichorium intybus | `spec/ref/plant-info/cichorium_intybus.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Ungiftig** fuer Menschen, Katzen und Hunde
- Alle Pflanzenteile essbar: junge Blaetter als Salat, Blueten als Dekoration, Wurzeln geroestet als Kaffee-Ersatz (Muckefuck)
- Bitterstoff Intybin ist nicht toxisch, regt aber den Gallenfluss an (medizinisch genutzt). **Kontraindikation:** Personen mit Gallensteinen oder Gallenwegsverschluss sollten groessere Mengen meiden (Gallenfluss-Stimulation kann Koliken ausloesen)
- **Kreuzallergie:** Asteraceae-Allergie (Beifuss, Kamille, Arnika) kann auf Chicoree kreuzreagieren -- Sesquiterpenlactone als Kontaktallergene. Bei bekannter Asteraceae-Allergie Vorsicht bei Hautkontakt mit Pflanzensaft
- Selten: Kontaktdermatitis durch Sesquiterpenlactone bei empfindlichen Personen (Asteraceae-typisch)

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- **Treiberei-Hinweis:** Bei der Treiberei wird KEIN Duenger verwendet -- die Chicoreezapfen ernaehren sich ausschliesslich aus der Speicherwurzel

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
4. Cichorium intybus Pflanzendaten: `spec/ref/plant-info/cichorium_intybus.md`
5. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
6. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
