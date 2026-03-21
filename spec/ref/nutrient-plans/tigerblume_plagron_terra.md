# Naehrstoffplan: Tigerblume -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Tigridia pavonia (Schwach-/Mittelzehrer, Outdoor, perennierend via Knolle)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/tigridia_pavonia.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Tigerblume -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Tigerblume (Tigridia pavonia) mit Knollen-Vorkultur ab Maerz und Freilandkultur ab Mai. Plagron Terra-Linie mit 3 Produkten. Schwach-/Mittelzehrer mit niedrigem Naehrstoffbedarf. Vorkeimen indoor Maerz--April, Auspflanzen nach Eisheiligen (Mitte Mai), kurze Bluetezeit Juli--September. Perennierend via Knolleneinlagerung (DORMANCY = frostfreie Trockenlagerung 10--13 degC). Zyklus-Neustart ab Sequenz 1 (Vorkeimen). 22 Wochen aktive Saison (Maerz--September) + 30 Wochen Dormanz. WICHTIG: Tigridia-Kormen bei 10--13 degC lagern, NICHT bei 4--8 degC wie Dahlien! | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | tigerblume, tigridia, pfauenblume, iridaceae, plagron, terra, erde, outdoor, schwachzehrer, zierpflanze, knollengewaeechs | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | 1 (perennierend via Knolle -- Neustart bei Vorkeimen im Fruehling) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 3-Tage-Intervall als Basis fuer Beet/Kuebel im Sommer. Tigridia bevorzugt gleichmaessige Feuchte, vertraegt aber keine Staunaesse (Knollenfaeule-Risiko). In GERMINATION (5 Tage, minimal, erst nach Austrieb), FLOWERING (bei Hitze alle 2 Tage) und DORMANCY (kein Wasser) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Tigridia pavonia ist ein perennierendes Knollengewaechs (Korm, nicht echte Zwiebel) der Familie Iridaceae. Die Mutterknolle erschoepft sich jaehrlich und wird durch 2--5 Tochterknollen ersetzt. Als Schwach-/Mittelzehrer ist der haeufigste Duengungsfehler zu viel Stickstoff -- dies foerdert Blattwachstum auf Kosten der Knollenentwicklung und Bluetenbildung. Jede Einzelbluete oeffnet nur einen einzigen Tag; in Gruppen gepflanzt (5--10 Knollen) bluehen ueber Wochen nacheinander neue Blueten auf.

| Tigridia-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|----------------|-----------------|--------|----------------|-------------|-------------|
| Vorkeimen / Knollenaustreibung | GERMINATION | 1--4 | Maerz--Anfang April | Knollen in feuchter Erde antreiben bei 15--18 degC. Kein Duenger -- Knolle hat Reserven. Erst giessen wenn Austrieb sichtbar! | false |
| Vegetatives Wachstum + Abhaertung | VEGETATIVE | 5--10 | April--Mitte Mai | Schwaches vegetatives Wachstum (Schwachzehrer). Niedrige Dosis Terra Grow. Abhaertung + Auspflanzen nach Eisheiligen (Mitte Mai). | false |
| Knospenbildung + Bluete | FLOWERING | 11--20 | Mitte Mai--Ende August | Umstellung auf P/K-betont. Terra Bloom in niedriger Dosis. Jede Einzelbluete haelt nur 1 Tag! Regelmaessig giessen. | false |
| Abreife + Knollenreife | HARVEST | 21--22 | September--Anfang Oktober | Kein Duenger. Laub vergilben lassen fuer Naehrstoffruecklagerung in die Knolle. Wasser reduzieren. | false |
| Knollen-Ueberwinterung (Dormanz) | DORMANCY | 23--52 | Oktober--Februar | Knollen ausgraben, trocknen, frostfrei lagern bei 10--13 degC. Kein Wasser, kein Duenger. Monatliche Kontrolle. | true |

**Nicht genutzte Phasen:**
- **SEEDLING** entfaellt (Knollenkultur, keine Saemlings-Phase)
- **FLUSHING** entfaellt (Freiland/Kuebel mit Erdsubstrat -- Salze werden durch Regen/Giessen natuerlich ausgespuelt)

**Knollen-Zyklus:** `cycle_restart_from_sequence: 1`. Nach DORMANCY startet der Zyklus neu bei GERMINATION (Vorkeimen). Die Knolle ist das Ueberdauerungsorgan. Mutterknolle erschoepft sich und wird durch 2--5 Tochterknollen ersetzt.

**Lueckenlos-Pruefung:** 4 + 6 + 10 + 2 + 30 = 52 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Kleine bis mittlere Volumina (Schwachzehrer, mittelgrosse Pflanzen 45--75 cm).

### 3.1 Wasser Vorkeimen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-vorkeimen | `delivery_channels.channel_id` |
| Label | Wasser Vorkeimen (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Erst giessen wenn erste Triebe sichtbar (5--10 cm). Vorher: Substrat nur leicht feucht halten, NICHT durchnaessen -- Faeulnisgefahr bei nasser Knolle! | `delivery_channels.notes` |
| method_params | drench, 0.1--0.2 L pro Knolle (nach Austrieb) | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> pH pruefen. Nie ueber Blaetter giessen (Pilzrisiko). Schwachzehrer -- niedrige Dosis! | `delivery_channels.notes` |
| method_params | drench, 0.2--0.5 L pro Pflanze (je nach Topf-/Beetgroesse) | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. P+K-betont fuer Bluetenbildung und Knollenaufbau. | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze (bei Hitze mehr) | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Abreife-Phase und vor dem Ausgraben. | `delivery_channels.notes` |
| method_params | drench, 0.2--0.3 L pro Pflanze (reduziert) | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Tigerblume

Tigridia pavonia ist ein Schwach-/Mittelzehrer. Ziel-EC der Gesamtloesung: **0.3--0.8 mS/cm** (inkl. Basis-Wasser). EC ueber 1.0 mS/cm kann Wachstumshemmungen verursachen. Leitungswasser liefert typisch 0.2--0.6 mS/cm. Bei hartem Wasser (>0.5 mS/cm) Duengerdosis um 25--50% reduzieren. **Wichtig:** Zu viel Stickstoff foerdert ueppiges Laub auf Kosten der Bluetenbildung und Knollenentwicklung -- der haeufigste Pflegefehler bei Tigridia.

**pH-Hinweis:** Terra Grow und Terra Bloom puffern die Naehrloesung auf pH 6.0--6.5 (Selbstpufferung). Tigridia bevorzugt pH 6.0--6.5 (Steckbrief) -- die Plagron-Pufferung liegt im optimalen Bereich. Aktive pH-Korrektur ist in der Regel nicht noetig.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Bluete (durchgehend) |

### 4.1 GERMINATION -- Vorkeimen / Knollenaustreibung (Woche 1--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Knollen ab Maerz in Toepfen (10 cm tief) mit leicht feuchter, sandiger Erde antreiben. 15--18 degC, heller Platz (Fensterbank). **Erst giessen wenn Austrieb sichtbar!** Faeulnisgefahr bei nasser Knolle. Knolle hat ausreichend Naehrstoffreserven -- kein Duenger noetig. Knollen 8--10 cm tief pflanzen, Spitze nach oben. Bei Voranzucht: 3--5 Knollen pro 10-L-Kuebel. Tochterknollen koennen einzeln gesetzt werden. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (minimal, erst nach Austrieb) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-vorkeimen**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.3 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

### 4.2 VEGETATIVE -- Wachstum + Abhaertung (Woche 5--10)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 10 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 60 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 20 | `phase_entries.magnesium_ppm` |
| Hinweise | Niedrige Dosis Terra Grow (2.0 ml/L, unter halbe Dosis) + Pure Zym. Schwachzehrer! Schwertfoermige Blaetter entfalten sich. **Abhaertung:** Ab Woche 8 (ca. Mitte April) vorgezogene Pflanzen schrittweise nach draussen stellen (7--14 Tage). **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai, Woche 10) ins Beet oder endgueltige Kuebel. Pflanzabstand 10--15 cm, in Gruppen von 5--10 Knollen fuer dekorativen Effekt. Volle Sonne! Alle 14 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.3 |
| Terra Grow ml/L | 2.0 (unter halbe Dosis, Schwachzehrer) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.16 (TG 2.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.56 mS/cm** -- ok

### 4.3 FLOWERING -- Knospenbildung + Bluete (Woche 11--20)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 11 | `phase_entries.week_start` |
| week_end | 20 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 60 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 30 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (2.5 ml/L) bei ersten Knospen. Pure Zym weiter. **KRITISCH: N minimal halten!** Steckbrief empfiehlt NPK 1:2:2 bis 0:2:2 in Bluete -- Terra Bloom liefert 2:2:4, was etwas mehr N enthaelt als ideal, aber bei niedriger Dosis tolerierbar. **Keine stickstoffbetonte Duengung!** Phosphor und Kalium sind die Schluessel zu reicher Bluete. Hoher K-Bedarf fuer Bluetenqualitaet und Knollenaufbau (Tochterknollen). Jede Einzelbluete oeffnet nur 1 Tag -- nicht erschrecken, naechste Knospe folgt. Ab September (Woche 18--20) Dosis auf 1.5 ml/L reduzieren -- Pflanze bereitet sich auf Abreife vor. Alle 14 Tage duengen. Morgens giessen, nie auf Blueten! | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.7  |
| reference_ec_ms | 0.7  |
| target_ph | 6.3 |
| Terra Bloom ml/L | 2.5 (niedrige Dosis, Schwachzehrer) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.25 (TB 2.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.65 mS/cm** -- ok
**EC-Budget (reduziert, W18--20):** 0.15 (TB 1.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.55 mS/cm** -- ok

### 4.4 HARVEST -- Abreife + Knollenreife (Woche 21--22)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 21 | `phase_entries.week_start` |
| week_end | 22 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Laub stehen lassen bis es vollstaendig vergilbt -- die Knolle benoetigt diese Zeit, um Reservestoffe zurueckzulagern. Erst dann Stiele auf 2--3 cm einkuerzen. **Ausgrabe-Protokoll:** (1) Nach Laubgelbfaerbung oder erstem Frost Knollen vorsichtig ausgraben. (2) Erde abschuetteln. (3) 2--4 Wochen luftig bei 15--20 degC trocknen. (4) Tochterknollen identifizieren und separieren. (5) Beschriftung mit Sortenname. HARVEST-Phase wird im KA-Sinne fuer die Knollenernte am Saisonende verwendet. | `phase_entries.notes` |
| Giessplan-Override | Intervall 7 Tage (stark reduziert, Knollenreifung durch Trockenheit gefoerdert) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.3 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

### 4.5 DORMANCY -- Knollen-Ueberwinterung (Woche 23--52)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 23 | `phase_entries.week_start` |
| week_end | 52 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Knollen frostfrei lagern bei **10--13 degC** (NICHT 4--8 degC wie Dahlien!), dunkel. Lagermedium: trockenes Saegemehl, Kokosfaser, Zeitungspapier oder Perlite. **KEIN Wasser.** Monatliche Kontrolle: (1) Faeulnis -- befallene Stellen herausschneiden, mit Holzkohle behandeln. (2) Austrocknung -- bei zu trockener Lagerung Umgebungsluft leicht anfeuchten (NICHT die Knollen direkt). (3) Vorzeitiges Austreiben -- bei >15 degC moeglich, Lagertemperatur pruefen. (4) Schimmel -- befallene Knollen separieren, Lagerung belueften. Tiefere Temperaturen (<10 degC) schaedigen die Kormen! | `phase_entries.notes` |
| Giessplan-Override | Intervall 0 Tage (kein Giessen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: (keiner -- kein Wasser, kein Duenger)**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | null |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.0 (trocken gelagert) -- ok

---

## 5. Jahresplan (Monat-fuer-Monat)

Perennierend via Knolle. Saisonplan Maerz--September aktiv + Oktober--Februar Dormanz. Zyklus-Neustart jaehrlich.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|---------------|-----------------|----------|
| Maerz | GERMINATION | -- | -- | -- | 0.4 | min. alle 5d |
| April | GERM->VEG | -->2.0 | -- | -->1.0 | 0.4->0.6 | alle 14d |
| Mai | VEG->FLO | 2.0->-- | -->2.5 | 1.0 | 0.6->0.7 | alle 14d |
| Juni | FLOWERING | -- | 2.5 | 1.0 | 0.7 | alle 14d |
| Juli | FLOWERING | -- | 2.5 | 1.0 | 0.7 | alle 14d |
| August | FLOWERING | -- | 2.5 | 1.0 | 0.7 | alle 14d |
| September | FLO->HARV | -- | 1.5->0 | 1.0->-- | 0.6->0.4 | alle 14d->-- |
| Oktober | HARVEST->DOR | -- | -- | -- | 0.4->0.0 | min.->kein Wasser |
| Nov--Feb | DORMANCY | -- | -- | -- | 0.0 | kein Wasser |

```
Monat:       |Maer |Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |Okt  |Nov--Feb|
KA-Phase:    |GERM |G->VE|V->FL|FLOW |FLOW |FLOW |F->HA|HA->D|DORMANZ|
Terra Grow:  |---  |-->##|##-->|---  |---  |---  |---  |---  |-------|
Terra Bloom: |---  |---  |-->##|###  |###  |###  |##-->|---  |-------|
Pure Zym:    |---  |-->==|===  |===  |===  |===  |==-->|---  |-------|

Legende: --- = nicht verwendet, ### = niedrige Dosis (Schwachzehrer)
         ##- = unter halbe Dosis, === = volle Phase-Dosis
         --> = Start, ##--> = auslaufend/reduziert
```

### Jahresverbrauch (geschaetzt)

Bei einer Tigridia-Gruppe (5 Knollen) im 10-L-Kuebel, 0.3 L Giessloessung pro Duengung, Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (3 Duengungen x 2.0ml/L x 0.3L) = 1.8 ml | **~2 ml** |
| Terra Bloom | (8 Duengungen x 2.5ml/L x 0.3L + 2 Duengungen x 1.5ml/L x 0.3L) = 6.0 + 0.9 = 6.9 ml | **~7 ml** |
| Pure Zym | (13 Duengungen x 1.0ml/L x 0.3L) = 3.9 ml | **~4 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche jedes Produkts reicht fuer hunderte Tigridia-Saisons. Sinnvoll nur in Kombination mit anderen Pflanzen.

---

## 6. Tigerblume-spezifische Praxis-Hinweise

### Substrat

- Locker-sandig-lehmige Erde (1:1:1 Gartenboden, Sand/Perlite, Kompost)
- pH 6.0--6.5 (Plagron-Pufferung passt optimal)
- Kuebel: min. 5--10 L, sehr gute Drainage zwingend
- Freiland: lockerer, gut drainierter Boden; schwere Tonboeden mit Sand verbessern
- Pflanztiefe: Knolle 8--10 cm tief, Spitze nach oben

### Stickstoff-Falle (WICHTIG)

**Haeufigster Pflegefehler bei Tigridia:** Zu viel Stickstoff!

- N-Ueberschuss foerdert ueppiges Blattwachstum statt Bluetenbildung
- Schwache Knollenentwicklung -- Tochterknollen werden kleiner
- Ab Knospenbildung (FLOWERING) N-Anteil so niedrig wie moeglich halten
- Terra Bloom NPK 2-2-4 liefert noch etwas N, was fuer Basisversorgung reicht
- Steckbrief empfiehlt NPK 1:2:2 bis 0:2:2 in Bluete

### Eintagsblueten

- Jede Einzelbluete oeffnet nur einen einzigen Tag -- das ist normal!
- In Gruppen gepflanzt (5--10 Knollen) bluehen nacheinander neue Blueten
- Hauptbluetezeit Juli--August, Nachbluete bis September moeglich
- Abgebluehte Bluetenstaengel NICHT entfernen -- naechste Knospen wachsen am gleichen Stiel

### Knollen-Ueberwinterung (Zusammenfassung)

1. Nach Laubgelbfaerbung oder erstem Frost Stiele auf 2--3 cm einkuerzen
2. Knollen vorsichtig ausgraben
3. Erde abschuetteln (nicht abwaschen)
4. 2--4 Wochen luftig bei 15--20 degC trocknen
5. Tochterknollen separieren und beschriften
6. In Kisten mit trockenem Saegemehl/Kokosfaser/Perlite einlagern
7. Lagerung: **10--13 degC**, dunkel, frostfrei (NICHT 4--8 degC wie Dahlien!)
8. Monatliche Kontrolle auf Faeulnis und Austrocknung

### Wuehlmaus-Schutz (Freiland)

- Wuehlmaeuse fressen Tigridia-Knollen gerne als Wintervorrat
- Pflanzkorb aus Kaninchendraht (Maschenweite 1 cm) ist die effektivste Vorbeugung
- Bei Freiland-Pflanzung immer Drahtkorb verwenden

### Schaedlinge und Krankheiten

- **Spinnmilben:** Bei Hitze > 30 degC und niedriger Luftfeuchte. Starker Wasserstrahl oder Neemoel (0.3--0.5%)
- **Blattlaeuse:** An Triebspitzen. Kaliseife-Spritzung (2% Loesung)
- **Thripse:** Silbergraue Flecken auf Bluetenblaettern. Schwer erkennbar. Orius-Raubwanzen
- **Knollenfaeule (Fusarium):** Wichtigste Krankheit. Praeventiv: gut trocknen vor Einlagerung, gut drainierendes Substrat
- **Botrytis:** Bei feuchtem Wetter. Gute Luftzirkulation (10--15 cm Abstand)

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Tigerblume \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Tigerblume (Tigridia pavonia) mit Knollen-Vorkultur ab M\u00e4rz und Freilandkultur ab Mai. Plagron Terra-Linie mit 3 Produkten. Schwach-/Mittelzehrer, perennierend via Knolle. 22 Wochen aktive Saison + 30 Wochen Dormanz. Kormen bei 10\u201313\u00b0C lagern (nicht 4\u20138\u00b0C).",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["tigerblume", "tigridia", "pfauenblume", "iridaceae", "plagron", "terra", "erde", "outdoor", "schwachzehrer", "zierpflanze", "knollengew\u00e4chs"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 1,
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

### 7.2 NutrientPlanPhaseEntry (5 Eintraege)

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
  "notes": "Knollen ab M\u00e4rz in T\u00f6pfen antreiben bei 15\u201318\u00b0C. Erst gie\u00dfen wenn Austrieb sichtbar! Knolle hat ausreichend Reserven. F\u00e4ulnisgefahr bei nasser Knolle. 8\u201310 cm tief pflanzen, Spitze nach oben.",
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
      "channel_id": "wasser-vorkeimen",
      "label": "Wasser Vorkeimen",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Erst gie\u00dfen wenn Triebe sichtbar (5\u201310 cm). Substrat nur leicht feucht.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.3,
      "fertilizer_dosages": [],
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
  "sequence_order": 2,
  "week_start": 5,
  "week_end": 10,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": 60,
  "magnesium_ppm": 20,
  "notes": "Niedrige Dosis Terra Grow (2 ml/L) + Pure Zym. Schwachzehrer! Schwertf\u00f6rmige Bl\u00e4tter entfalten sich. Abh\u00e4rtung ab Woche 8. Auspflanzen nach Eisheiligen (Mitte Mai). Gruppen von 5\u201310 Knollen. Alle 14 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow niedrige Dosis + Pure Zym. Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.3,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
  "week_start": 11,
  "week_end": 20,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 60,
  "magnesium_ppm": 30,
  "notes": "Umstellung auf Terra Bloom (2.5 ml/L). P+K-betont f\u00fcr Bl\u00fctenbildung und Knollenaufbau. N minimal halten! Jede Einzelbl\u00fcte \u00f6ffnet nur 1 Tag. Ab September auf 1.5 ml/L reduzieren. Alle 14 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom niedrige Dosis + Pure Zym. Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.7,
      "reference_ec_ms": 0.7,
      "target_ph": 6.3,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 2.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
  "week_start": 21,
  "week_end": 22,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Laub vergilben lassen f\u00fcr N\u00e4hrstoffr\u00fccklagerung in die Knolle. Stiele auf 2\u20133 cm k\u00fcrzen. Knollen ausgraben, 2\u20134 Wochen trocknen, Tochterknollen separieren, beschriften.",
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
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Abreife)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Stark reduziertes Gie\u00dfen. Knollenreifung durch Trockenheit f\u00f6rdern.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.3,
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
  "week_start": 23,
  "week_end": 52,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Knollen frostfrei lagern bei 10\u201313\u00b0C (NICHT 4\u20138\u00b0C wie Dahlien!), dunkel. Kein Wasser, kein D\u00fcnger. Lagermedium: trockenes S\u00e4gemehl, Kokosfaser, Perlite. Monatliche Kontrolle auf F\u00e4ulnis/Austrocknung. Zyklus-Neustart im Fr\u00fchling bei Vorkeimen.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 0,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 0,
    "times_per_day": 0
  },
  "delivery_channels": []
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Tigridia pavonia | `spec/ref/plant-info/tigridia_pavonia.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Nicht giftig laut ASPCA:** Tigridia pavonia ist nicht als giftig fuer Katzen oder Hunde gelistet
- **Rohe Knollen:** Koennen Mundschleimhaut-Irritationen verursachen (brennendes Gefuehl). Gekochte Knollen sind essbar (traditionelles Nahrungsmittel in Mexiko/Kolumbien)
- **Haustiere:** Bei Hunden, die Knollen ausgraben und roh verzehren, sind gastrointestinale Beschwerden moeglich
- **Kontaktdermatitis:** Nicht bekannt

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern und Haustieren aufbewahren

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
4. Tigridia pavonia Pflanzensteckbrief: `spec/ref/plant-info/tigridia_pavonia.md`
5. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
6. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
