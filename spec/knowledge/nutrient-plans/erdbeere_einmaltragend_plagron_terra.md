# Naehrstoffplan: Erdbeere (einmaltragend) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Fragaria x ananassa (einmaltragend, Mittelzehrer, Topf/Kuebel outdoor)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-01
> **Quellen:** spec/ref/products/plagron_terra_*.md, spec/ref/products/plagron_power_roots.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_sugar_royal.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Erdbeere (einmaltragend) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Jahresplan fuer einmaltragende Erdbeeren im Topf/Kuebel (Balkon, Terrasse). Plagron Terra-Linie mit 5 Produkten. Saisonaler Zyklus: Maerz--Oktober Duengung, November--Februar Winterruhe. Erster Durchlauf mit Bewurzelungs-/Etablierungsphase, ab Jahr 2 zyklisch. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.1 | `nutrient_plans.version` |
| Tags | erdbeere, fragaria, einmaltragend, plagron, terra, erde, outdoor, topf, balkon | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | 3 (VEGETATIVE Fruehjahr) | `nutrient_plans.cycle_restart_from_sequence` |

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

**Hinweis:** 2-Tage-Intervall als Sommerbasis (5L-Topf trocknet bei Sonne schnell aus). Bei Hitze (>25 C) taeglich giessen, bei Regen laenger warten. In GERMINATION (2 Tage, override identisch), DORMANCY (14 Tage) und FLUSHING (5 Tage) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Einmaltragende Erdbeeren sind perenniale Pflanzen mit saisonalem Fruchtzyklus. Typische Sorten: Senga Sengana, Korona, Elsanta, Honeoye. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Erdbeeren-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-----------------|-----------------|--------|----------------|-------------|-------------|
| Auspflanzen | GERMINATION | 1--3 | Mitte Maerz | Topfpflanze aus Gaertnerei einpflanzen, Wurzeln etablieren | false |
| Eingewoehnung | SEEDLING | 4--8 | April | Jungpflanze (aus Gaertnerei) etabliert sich, halbe Basisdosis. Funktional: Eingewoehnung, nicht botanischer Saemling. | false |
| Fruehjahrs-Wachstum | VEGETATIVE | 9--16 | Mai--Mitte Juni | Aktives Blattwachstum, Auslaeufertrieb, volle Duengung | true |
| Bluete | FLOWERING | 17--22 | Mitte Juni--Mitte Juli | Bluetenbildung, Umstellung auf P+K-betont (Terra Bloom) | true |
| Fruchtreife + Ernte | HARVEST | 23--28 | Mitte Juli--Ende August | Fruchtreife, reduzierte Duengung, Ernte | true |
| Nachernte-Spuelung | FLUSHING | 29--30 | Anfang September | Salzreste ausspuelen, Substrat regenerieren (2 Wochen genuegen) | true |
| Herbst-Regeneration | VEGETATIVE | 31--40 | Mitte September--Mitte November | Kronenbildung + Kurztagsreaktion: abnehmende Tageslaenge (<12h) initiiert Bluetenanlage fuer naechste Saison. Reduzierte Duengung. | true |
| Winterruhe | DORMANCY | 41--52 | Mitte November--Mitte Maerz | Keine Duengung, Topf frostgeschuetzt abstellen | true |

**Nicht genutzte Phasen:**
- **SEEDLING** entfaellt ab Jahr 2 (Pflanze ist etabliert)
- **GERMINATION** entfaellt ab Jahr 2 (kein Neupflanzen)

**Saisonaler Zyklus:** Nach dem Erstdurchlauf (Woche 1--52) wiederholen sich VEGETATIVE → FLOWERING → HARVEST → FLUSHING → VEGETATIVE → DORMANCY jaehrlich (`cycle_restart_from_sequence: 3`). Die einmaligen Anfangsphasen (GERMINATION, SEEDLING) werden nur beim Erstdurchlauf durchlaufen. **Maerz-Start (Folgejahre):** Der Zyklus beginnt ab Jahr 2 direkt mit VEGETATIVE (Sequenz 3) im Maerz. Die Pflanze startet nach der Winterruhe mit reduzierter Duengung (2.5 ml/L Terra Grow, halbe Dosis) und steigert auf volle 4 ml/L sobald aktiver Neuaustrieb sichtbar ist (ca. 2--3 Wochen nach Wiederaustrieb).

**Lueckenlos-Pruefung:** 3 + 5 + 8 + 6 + 6 + 2 + 10 + 12 = 52 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Verschiedene Kanaele fuer unterschiedliche Produktkombinationen.

### 3.1 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow → Power Roots → Pure Zym → Sugar Royal → pH pruefen | `delivery_channels.notes` |
| method_params | drench, 1.0 L pro Giessen | `delivery_channels.method_params` |

### 3.2 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom → Pure Zym → Sugar Royal → pH pruefen | `delivery_channels.notes` |
| method_params | drench, 1.0 L pro Giessen | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Optionales Pure Zym fuer Substratpflege. | `delivery_channels.notes` |
| method_params | drench, 0.5 L pro Giessen | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Erdbeeren

Erdbeeren sind salzempfindlich. Ziel-EC der Gesamtloesung: **0.5--1.0 mS/cm** (inkl. Basis-Wasser). Leitungswasser liefert typisch 0.2--1.0 mS/cm (je nach Region). Bei weichem Wasser (<0.3 mS/cm) ist mehr EC-Spielraum fuer Duenger; bei hartem Wasser (>0.6 mS/cm) Dosierung reduzieren. **Hartwasser-Hinweis:** Ab 0.7 mS/cm Basiswasser die Duengerdosis um 25% reduzieren.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Bewurzelung bis fruehe Bluete |
| Pure Zym (0-0-0) | 0.00 | 70 | Durchgehend |
| Sugar Royal (9-0-0) | 0.02 | 65 | Wachstum bis Bluete (nicht in HARVEST) |

### 4.1 GERMINATION -- Auspflanzen (Woche 1--3)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 3 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Frisch getopfte Erdbeere nur mit Wasser + Wurzelstimulator giessen. Substrat gleichmaessig feucht halten. Vorgeduengte Blumenerde liefert Grundversorgung fuer 2--4 Wochen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage (Substrat konstant feucht) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | Power Roots 1 ml/L (optional), Pure Zym 1 ml/L (optional) |

**EC-Budget:** 0.01 (PR) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

### 4.2 SEEDLING -- Etablierung (Woche 4--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis Terra Grow. Pflanze baut Blattrosette und Wurzelsystem auf. Power Roots foerdert Wurzelentwicklung. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.5 (halbe Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.20 (TG 2.5ml) + 0.01 (PR) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.6 mS/cm** ✓

### 4.3 VEGETATIVE -- Fruehjahrs-Wachstum (Woche 9--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Terra Grow 4 ml/L (80% der Plagron-Empfehlung, reduziert fuer salzempfindliche Erdbeeren). Aktives Blattwachstum, Auslaeufertrieb (Auslaufer ab Mitte Mai entfernen fuer besseren Fruchtansatz). Sugar Royal ab Woche 2 fuer verbesserte Chlorophyllbildung. Power Roots bis Ende dieser Phase. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.8  |
| reference_ec_ms | 0.8  |
| target_ph | 6.0 |
| Terra Grow ml/L | 4.0 (80% der Plagron-Empfehlung) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.32 (TG 4ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.75 mS/cm** ✓

### 4.4 FLOWERING -- Bluete (Woche 17--22)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 17 | `phase_entries.week_start` |
| week_end | 22 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 80--120 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Boron (ppm) | null | `phase_entries.boron_ppm` |
| Hinweise | Umstellung auf Terra Bloom bei ersten Bluetenknospen. Erdbeeren profitieren stark vom hohen Boranteil (0.48%) in Terra Bloom fuer Pollenkeimung und Fruchtansatz. Power Roots absetzen. **Calcium-Ergaenzung empfohlen:** Terra Bloom liefert kein Ca -- bei weichem Wasser (<0.4 mS/cm) Calciumnitrat 0.5--1 g/L ergaenzen oder kalkhaltiges Giesswasser verwenden. Calciummangel fuehrt bei Erdbeeren zu Bluetenendfaeule (weiche, braune Fruchtspitzen). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.9  |
| reference_ec_ms | 0.9  |
| target_ph | 5.8 |
| Terra Bloom ml/L | 4.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.40 (TB 4ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.82 mS/cm** ✓

### 4.5 HARVEST -- Fruchtreife + Ernte (Woche 23--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 23 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 80--120 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom waehrend Fruchtreife. Kein Sugar Royal -- organischer Stickstoff (9-0-0) foerdert vegetatives Wachstum und verschlechtert Fruchtqualitaet (weichere Fruechte, hoehere Botrytis-Anfaelligkeit). Fruechte morgens ernten wenn trocken. Erdbeeren vor Bodenkontakt schuetzen (Stroh oder Topfrand). **Calcium weiter ergaenzen** -- Fruchtbildung hat hohen Ca-Transport-Bedarf, Bluetenendfaeule-Risiko steigt bei Hitze+unregelmaessigem Giessen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.7  |
| reference_ec_ms | 0.7  |
| target_ph | 5.8 |
| Terra Bloom ml/L | 3.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.30 (TB 3ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm** ✓

### 4.6 FLUSHING -- Nachernte-Spuelung (Woche 29--30)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 6 | `phase_entries.sequence_order` |
| week_start | 29 | `phase_entries.week_start` |
| week_end | 30 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Substrat mit klarem Wasser durchspuelen. Pure Zym weiter verwenden fuer Abbau abgestorbener Wurzeln und Substratregeneration. Alte Blaetter und Auslaufer entfernen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (reduziert) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

### 4.7 VEGETATIVE -- Herbst-Regeneration (Woche 31--40)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 7 | `phase_entries.sequence_order` |
| week_start | 31 | `phase_entries.week_start` |
| week_end | 40 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierte Duengung mit Terra Grow. Pflanze bildet neue Kronen fuer naechste Saison. Auslaufer abschneiden (ausser fuer Vermehrung). Ab Woche 38 Dosis halbieren. Ziel: kompakte, kraeftige Kronen fuer die Ueberwinterung. **Kurztagsreaktion:** Abnehmende Tageslaenge (<12h, ab ca. Mitte September) loest bei einmaltragenden Sorten die Bluetenanlage fuer die naechste Saison aus -- dieser Prozess ist essentiell und darf nicht durch Kunstlicht gestoert werden. **Mg-Ergaenzung:** Terra Grow enthaelt kein Magnesium -- bei Chlorosen (Blattaufhellung zwischen den Adern) Bittersalz 1 g/L oder Terra Bloom 2 ml/L als Mg-Quelle (0.8% MgO) ergaenzen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (Herbst, weniger Verdunstung) | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.0 |
| Terra Grow ml/L | 3.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.24 (TG 3ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.64 mS/cm** ✓

### 4.8 DORMANCY -- Winterruhe (Woche 41--52)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 8 | `phase_entries.sequence_order` |
| week_start | 41 | `phase_entries.week_start` |
| week_end | 52 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Topf frostgeschuetzt abstellen (Hauswand, Vlies, Styropor-Ummantelung). Substrat nicht voellig austrocknen lassen aber auch nicht nass halten. Einmaltragende Erdbeeren benoetigen Kaelteperiode (<7 C fuer 4--6 Wochen) fuer Blueteninitiierung naechste Saison. | `phase_entries.notes` |
| Giessplan-Override | Intervall 14 Tage (minimal, nur bei Trockenheit) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.3--0.4 (nur Wasser) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Basierend auf einer etablierten Pflanze (ab Jahr 2, zyklischer Betrieb ab Sequenz 3).

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|-----------------|----------|
| Jan | DORMANCY | -- | -- | -- | -- | -- | 0.3 | alle 14d |
| Feb | DORMANCY | -- | -- | -- | -- | -- | 0.3 | alle 14d |
| Maerz | VEGETATIVE | 2.5 | -- | 1.0 | 1.0 | -- | 0.6 | alle 3d |
| April | VEGETATIVE | 4.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | alle 2d |
| Mai | VEGETATIVE | 4.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | alle 2d |
| Juni | FLOWERING | -- | 4.0 | -- | 1.0 | 1.0 | 0.8 | alle 2d |
| Juli | HARVEST | -- | 3.0 | -- | 1.0 | -- | 0.7 | alle 2d |
| August | FLU→VEG | 2.0* | -- | -- | 1.0 | -- | 0.4→0.6 | alle 5d |
| September | VEGETATIVE | 3.0 | -- | -- | 1.0 | -- | 0.6 | alle 5d |
| Oktober | VEGETATIVE | 2.0 | -- | -- | 1.0 | -- | 0.5 | alle 5d |
| November | DORMANCY | -- | -- | -- | -- | -- | 0.3 | alle 14d |
| Dezember | DORMANCY | -- | -- | -- | -- | -- | 0.3 | alle 14d |

*August: 2 Wochen FLUSHING (nur Wasser+PZ), dann VEGETATIVE-Start mit Terra Grow 2 ml/L.

```
Monat:       |Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:    |DOR|DOR|VEG|VEG|VEG|FLO|HAR|F→V|VEG|VEG|DOR|DOR|
Terra Grow:  |---|---|###|===|===|---|---|---|##-|#--|---|---|
Terra Bloom: |---|---|---|---|---|===|##-|---|---|---|---|---|
Power Roots: |---|---|===|===|===|---|---|---|---|---|---|---|
Pure Zym:    |---|---|===|===|===|===|===|===|===|===|---|---|
Sugar Royal: |---|---|---|===|===|===|---|---|---|---|---|---|

Legende: --- = nicht verwendet, ### = halbe Dosis, === = volle Dosis
         ##- = auslaufend (abnehmend)
```

### Jahresverbrauch (geschaetzt)

Bei einer Erdbeerpflanze im 5L-Topf, 1.0 L Giessloessung pro Duengung:

| Produkt | Formel | Verbrauch/Jahr |
|---------|--------|----------------|
| Terra Grow | (8 Wo x 3.5/Wo x 4ml + 5 Wo x 1.5/Wo x 3ml + 5 Wo x 1.5/Wo x 2ml) = 149.5 ml | **~150 ml** |
| Terra Bloom | (6 Wo x 3.5/Wo x 4ml + 6 Wo x 3.5/Wo x 3ml) = 147 ml | **~150 ml** |
| Power Roots | (12 Wo x 3/Wo x 1ml) = 36 ml | **~35 ml** |
| Pure Zym | (28 Wo x avg. 2.5/Wo x 1ml) = 70 ml | **~70 ml** |
| Sugar Royal | (14 Wo x 3/Wo x 1ml) = 42 ml | **~40 ml** |

**Kosten-Schaetzung:** Bei 1L-Flaschen reicht das Sortiment fuer ca. 6--7 Erdbeerpflanzen-Jahre.

---

## 6. Erdbeer-spezifische Praxis-Hinweise

### Substrat

- Leicht saure Blumenerde (pH 5.5--6.5), ggf. mit Sand/Perlite fuer Drainage mischen
- Topfgroesse: min. 3 L pro Pflanze, ideal 5--8 L
- Drainage-Loecher essentiell -- Erdbeeren vertragen keine Staunaesse

### Auslaufer-Management

- **Fruchtoptimierung:** Auslaufer waehrend VEGETATIVE und FLOWERING konsequent abschneiden -- Energie soll in Fruchtbildung fliessen
- **Vermehrung:** Im Herbst (VEGETATIVE seq 7) ausgewaehlte Auslaufer bewurzeln lassen und als neue Pflanzen abtrennen

### Frostschutz (DORMANCY)

- Topf mit Vlies, Luftpolsterfolie oder Styropor ummanteln
- Wurzelbereich ist frostempfindlicher als bei Freiland-Erdbeeren (Topf friert schneller durch)
- Topf an geschuetzte Hauswand stellen (Suedseite)
- Bei Dauerfrost unter -10 C: Topf in frostfreien aber kuehlen Raum (0--5 C) stellen

### Kaeltebeduerfnis

- Einmaltragende Sorten benoetigen 4--6 Wochen unter 7 C (Vernalisation) fuer Blueteninitiierung
- Ohne ausreichende Kaelte: weniger Blueten, geringerer Ertrag naechste Saison
- NICHT den ganzen Winter im warmen Haus ueberwintern

### Botrytis-Praevention (Grauschimmel)

Botrytis cinerea ist die wichtigste Erdbeerkrankheit im Topfanbau. Praevention ueber Kulturfuehrung:

- **Luftzirkulation:** Nicht zu eng stellen, Blaetter im Fruchtbereich auslichten
- **Giessen:** Morgens giessen (Blaetter trocknen ueber Tag ab), nie ueber die Fruechte giessen
- **Ernte:** Reife Fruechte sofort ernten, beschaedigte/angefaulte Fruechte entfernen
- **Regen:** Bei Dauerregen Topf unter Dachvorsprung stellen oder Regenschutz
- **Stroh/Mulch:** Fruechte vom feuchten Substrat fernhalten (Topfrand nutzen oder Stroh unterlegen)
- **HARVEST-Phase:** Sugar Royal (organischer N) in HARVEST bewusst weggelassen -- uebermaessiger Stickstoff foerdert weiches Gewebe und erhoehte Botrytis-Anfaelligkeit

### Bestaeubung auf dem Balkon

Erdbeeren sind zwar selbstfruchtbar, aber fuer optimalen Fruchtansatz und gleichmaessige Fruchtform ist Insektenbestaeubung wichtig:

- **Bienenfreundlich:** Topf an besonnten, windgeschuetzten Platz (Bienen fliegen ab 12 C)
- **Handbestaeubung:** Bei wenig Insektenflug (Hochhaus, Nordbalkon): weichen Pinsel ueber offene Blueten streichen, ca. alle 2 Tage waehrend FLOWERING
- **Zeichen schlechter Bestaeubung:** Missgebildete, kleine oder einseitig entwickelte Fruechte

### Wasserqualitaet und Chlor

- **Chlorempfindlichkeit:** Erdbeerwurzeln reagieren empfindlich auf Chlor im Leitungswasser. Pure Zym (Enzyme) wird ebenfalls durch Chlor beeintraechtigt.
- **Empfehlung:** Giesswasser 24 Stunden in offener Kanne abstehen lassen -- Chlor entgast.  Alternativ: Aktivkohlefilter am Wasserhahn.
- **Besonders wichtig in:** GERMINATION und SEEDLING (empfindliche Jungwurzeln)

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Erdbeere (einmaltragend) \u2014 Plagron Terra",
  "description": "Jahresplan f\u00fcr einmaltragende Erdbeeren im Topf/K\u00fcbel. Plagron Terra-Linie mit 5 Produkten. Saisonaler Zyklus: M\u00e4rz\u2013Oktober D\u00fcngung, November\u2013Februar Winterruhe.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.1",
  "tags": ["erdbeere", "fragaria", "einmaltragend", "plagron", "terra", "erde", "outdoor", "topf", "balkon"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 3,
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

### 7.2 NutrientPlanPhaseEntry (8 Eintraege)

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
  "notes": "Frisch getopfte Erdbeere nur mit Wasser + Wurzelstimulator gie\u00dfen. Substrat gleichm\u00e4\u00dfig feucht halten.",
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
      "channel_id": "wasser-pur",
      "label": "Nur Wasser + Wurzelstimulator",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein Basisdünger. Power Roots + Pure Zym optional.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": true},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
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
  "notes": "Halbe Dosis Terra Grow. Pflanze baut Blattrosette und Wurzelsystem auf.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow halbe Dosis + Additive",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.5, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

#### VEGETATIVE (Fruehjahr)

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 3,
  "week_start": 9,
  "week_end": 16,
  "is_recurring": true,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Volle Dosis Terra Grow. Aktives Blattwachstum, Ausl\u00e4ufertrieb abschneiden. Sugar Royal f\u00fcr Chlorophyllstimulation. Power Roots bis Ende dieser Phase.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + alle Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 0.8,
      "reference_ec_ms": 0.8,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 4.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
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
  "week_start": 17,
  "week_end": 22,
  "is_recurring": true,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 100,
  "magnesium_ppm": null,
  "boron_ppm": null,
  "notes": "Umstellung auf Terra Bloom. Hoher Boranteil in Terra Bloom (0.48%) f\u00f6rdert Pollenkeimung und Fruchtansatz. Power Roots absetzen. Calcium-Erg\u00e4nzung empfohlen (Calciumnitrat 0.5\u20131 g/L bei weichem Wasser).",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive. Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 0.9,
      "reference_ec_ms": 0.9,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 4.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
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
  "week_start": 23,
  "week_end": 28,
  "is_recurring": true,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 100,
  "magnesium_ppm": null,
  "notes": "Reduzierter Terra Bloom. Kein Sugar Royal (organischer N verschlechtert Fruchtqualit\u00e4t). Fr\u00fcchte morgens ernten. Calcium weiter erg\u00e4nzen (Bl\u00fctenendfa\u0308ule-Risiko bei Hitze).",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom. Kein Sugar Royal (organischer N unerwuenscht waehrend Fruchtreife).",
      "target_ec_ms": 0.7,
      "reference_ec_ms": 0.7,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

#### FLUSHING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flushing",
  "sequence_order": 6,
  "week_start": 29,
  "week_end": 30,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Substrat mit klarem Wasser durchsp\u00fclen. Pure Zym f\u00fcr Substratregeneration. Alte Bl\u00e4tter und Ausl\u00e4ufer entfernen.",
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
      "label": "Substratsp\u00fclung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur Wasser + Pure Zym. Kein D\u00fcnger.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

#### VEGETATIVE (Herbst-Regeneration)

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 7,
  "week_start": 31,
  "week_end": 40,
  "is_recurring": true,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Reduzierter Terra Grow f\u00fcr Kronenbildung. Ausl\u00e4ufer abschneiden. Ab Woche 38 Dosis halbieren (2 ml/L). Mg-Erg\u00e4nzung bei Chlorosen: Bittersalz 1 g/L oder Terra Bloom 2 ml/L.",
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
      "channel_id": "naehrloesung-wachstum",
      "label": "Herbstd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Grow + Pure Zym. Kein Sugar Royal, kein Power Roots.",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

#### DORMANCY

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "dormancy",
  "sequence_order": 8,
  "week_start": 41,
  "week_end": 52,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Winterruhe. Keine D\u00fcngung. Topf frostgesch\u00fctzt abstellen. Substrat nicht v\u00f6llig austrocknen lassen. K\u00e4lteperiode (<7\u00b0C, 4\u20136 Wochen) f\u00fcr Bl\u00fcteninitiation erforderlich.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 14,
    "preferred_time": "10:00",
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
      "notes": "Kein D\u00fcnger. Nur bei Trockenheit gie\u00dfen.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Power Roots | `spec/ref/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Sugar Royal | `spec/ref/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/ref/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/ref/products/plagron_sugar_royal.md`
6. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
7. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.1
**Erstellt:** 2026-03-01
**Aktualisiert:** 2026-03-01 (Agrobiology-Review: E-001--E-014 eingearbeitet)
