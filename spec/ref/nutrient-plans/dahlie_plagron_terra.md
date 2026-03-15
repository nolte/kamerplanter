# Naehrstoffplan: Dahlie -- Plagron Terra + PK 13-14

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Dahlia pinnata / Dahlia x hybrida (Starkzehrer, Outdoor, perennierend via Knolle)
> **Cultivare:** Armateras, Hapet Daydream, Lavender Perfection, Great Silence, Embassy (alle 5 teilen diesen Plan)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, PK 13-14
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_power_roots.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_pk_13_14.md, spec/ref/plant-info/dahlia_x_hybrida_armateras.md, spec/ref/plant-info/dahlia_embassy.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Dahlie -- Plagron Terra + PK 13-14 | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Dahlien (dekorative, halbgefuellte und Kaktus-Typen) mit Knollen-Vorkultur ab Maerz und Freilandkultur ab Mai. Plagron Terra-Linie mit 5 Produkten inkl. PK 13-14 Bluetenbooster. Starkzehrer mit hohem P/K-Bedarf in der Bluete und niedrigem N-Bedarf. Perennierend via Knolleneinlagerung (DORMANCY = frostfreie Trockenlagerung 4--8 degC). Zyklus-Neustart ab Sequenz 1 (Vorkeimen). 32 Wochen aktive Saison (Maerz--Oktober) + 20 Wochen Dormanz. Geeignet fuer alle 5 Cultivare: Armateras, Hapet Daydream, Lavender Perfection, Great Silence, Embassy. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | dahlie, dahlia, asteraceae, plagron, terra, pk-13-14, erde, outdoor, starkzehrer, zierpflanze, knollengewaeechs, schnittblume | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | 1 (perennierend via Knolle -- Neustart bei Vorkeimen im Fruehling) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 2 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 2-Tage-Intervall als Basis fuer Beet/Kuebel im Sommer. Dahlien brauchen gleichmaessige Feuchte, vertragen aber keine Staunaesse. In GERMINATION (Vorkeimen, 5 Tage, minimal), FLOWERING (bei Hitze taeglich) und DORMANCY (kein Wasser) ueber `watering_schedule_override` angepasst. Kuebelpflanzen (min. 20 L) bei Hitze >28 degC taeglich giessen.

---

## 2. Phasen-Mapping

Dahlien aus Knollen durchlaufen jaehrlich einen klar abgegrenzten Zyklus. Als Starkzehrer mit hohem P/K-Bedarf in der Bluete ist der haeufigste Duengungsfehler zu viel Stickstoff -- dies fuehrt zu ueppigem Laub, schwachen Staengeln und wenigen Blueten. Alle 5 Cultivare (Armateras 90--110 cm, Hapet Daydream 100--120 cm, Lavender Perfection 100--120 cm, Great Silence 90--100 cm, Embassy 80--100 cm) folgen dem gleichen Naehrstoffschema.

| Dahlie-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|--------------|-----------------|--------|----------------|-------------|-------------|
| Vorkeimen / Knollenaustreibung | GERMINATION | 1--4 | Maerz--Anfang April | Knollen in feuchter Erde antreiben bei 15--18 degC. Kein Duenger -- Knolle hat Reserven. NICHT giessen bis Austrieb sichtbar! | false |
| Vegetatives Wachstum + Abhaertung | VEGETATIVE | 5--12 | April--Mitte Juni | N-betonte Wachstumsphase. Entspitzen (Pinching) bei 30--40 cm. Abhaertung + Auspflanzen nach Eisheiligen (Mitte Mai). Ca fuer Staengelstabilitaet. | false |
| Knospenbildung + Bluete | FLOWERING | 13--26 | Mitte Juni--Ende September | Umstellung auf P/K-betont. PK 13-14 in Woche 15--16 (peak Knospenansatz). Deadheading essentiell! Hoher K-Bedarf fuer Bluetenqualitaet und Knollenaufbau. N minimal. | false |
| Seneszenz + Knollenreife | HARVEST | 27--30 | Oktober | Kein Duenger. Pflanze nach erstem Frost einziehen lassen. Knollen ausgraben, trocknen, beschriften. | false |
| Knollen-Ueberwinterung (Dormanz) | DORMANCY | 31--52 | November--Februar | Knollen frostfrei lagern bei 4--8 degC, dunkel, trocken. Kein Wasser, kein Duenger. Monatliche Kontrolle auf Faeulnis. | true |

**Nicht genutzte Phasen:**
- **SEEDLING** entfaellt (Knollenkultur, keine Saemlings-Phase)
- **FLUSHING** entfaellt (Freiland/Kuebel mit Erdsubstrat -- Salze werden durch Regen/Giessen natuerlich ausgespuelt)

**Knollen-Zyklus:** `cycle_restart_from_sequence: 1`. Nach DORMANCY startet der Zyklus neu bei GERMINATION (Vorkeimen). Die Knolle ist das Ueberdauerungsorgan.

**Lueckenlos-Pruefung:** 4 + 8 + 14 + 4 + 22 = 52 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Groessere Volumina als bei Schwachzehrern (Starkzehrer, grosse Pflanzen).

### 3.1 Wasser Vorkeimen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-vorkeimen | `delivery_channels.channel_id` |
| Label | Wasser Vorkeimen (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Erst giessen wenn erste Triebe sichtbar (5--10 cm). Vorher: Substrat nur leicht feucht halten, NICHT durchnaessen -- Faeulnisgefahr! | `delivery_channels.notes` |
| method_params | drench, 0.1--0.3 L pro Knolle (nach Austrieb) | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Power Roots + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> pH pruefen. Nie ueber Blaetter giessen (Botrytis-Risiko). | `delivery_channels.notes` |
| method_params | drench, 0.5--2.0 L pro Pflanze (je nach Topf-/Beetgroesse) | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym + PK 13-14 (nur W15--16) ins Giesswasser. Reihenfolge: Terra Bloom -> PK 13-14 -> Pure Zym -> pH pruefen. PK 13-14 nur 2 Wochen! Danach sofort absetzen. | `delivery_channels.notes` |
| method_params | drench, 1.0--3.0 L pro Pflanze (bei Hitze und grossen Kuebeln mehr) | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Seneszenz/Knollenreife-Phase und Dormanz. | `delivery_channels.notes` |
| method_params | drench, 0.3--1.0 L pro Pflanze (reduziert) | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Dahlien

Dahlien sind Starkzehrer, tolerieren aber im Vergleich zu Tomaten geringere EC-Werte. Ziel-EC der Gesamtloesung: **0.8--1.4 mS/cm** (inkl. Basis-Wasser). EC ueber 1.6 mS/cm kann Wachstumshemmungen verursachen (Steckbrief). Leitungswasser liefert typisch 0.2--0.6 mS/cm. **Wichtig:** Zu viel Stickstoff ist der haeufigste Duengungsfehler bei Dahlien -- N-Ueberschuss foerdert weiches Laub, schwache Staengel und verhindert Bluetenbildung.

**pH-Hinweis:** Terra Grow und Terra Bloom puffern die Naehrloesung auf pH 6.0--6.5 (Selbstpufferung). Dahlien bevorzugen pH 6.0--7.0 (Steckbrief) -- die Plagron-Pufferung liegt im optimalen Bereich. Aktive pH-Korrektur ist in der Regel nicht noetig.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete |
| Power Roots (0-0-2) | 0.01 | 60 | Vegetativ (Wurzelentwicklung nach Pflanzung) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Bluete (durchgehend) |
| PK 13-14 (0-13-14) | 0.25 | 30 | Nur Woche 15--16 (Knospenansatz-Boost) |

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
| Hinweise | Knollen ab Maerz in flachen Schalen/Toepfen mit leicht feuchter Erde antreiben. 15--18 degC, heller Platz (Fensterbank, Gewaechshaus). **NICHT giessen bis Austrieb sichtbar!** Faeulnisgefahr bei nasser Knolle. Knolle hat ausreichend Naehrstoffreserven -- kein Duenger noetig. Knollenteilung moeglich: jedes Stueck muss mind. 1 Auge (Triebknospe) tragen, Schnittflaeche mit Holzkohlepulver behandeln, 24 h trocknen lassen. Stecklinge bei 10--15 cm Trieblaenge moeglich. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (minimal, erst nach Austrieb) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-vorkeimen**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 VEGETATIVE -- Wachstum + Abhaertung (Woche 5--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 100 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 40 | `phase_entries.magnesium_ppm` |
| Hinweise | Volle Dosis Terra Grow (5 ml/L) + Power Roots + Pure Zym. Kraeftiger Laub- und Staengelaufbau. **Calcium wichtig fuer Staengelstabilitaet** -- Terra Grow + Leitungswasser liefern Ca; bei weichem Wasser (<0.3 mS/cm) optionaler CaMg-Zusatz. **Entspitzen (Pinching):** Bei 30--40 cm Wuchshoehe Haupttrieb ueber dem 3. Blattpaar einkuerzen -- foerdert buschigen Wuchs mit mehr Bluetenstielen. **Abhaertung:** Ab Woche 9 (ca. Mitte April) vorgezogene Pflanzen schrittweise nach draussen stellen. **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai, Woche 11) ins Beet oder endgueltige Kuebel (min. 20 L). Stuetzstaebe einschlagen! Pflanzabstand 60--70 cm fuer Luftzirkulation. Alle 7 Tage duengen (Starkzehrer). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.8 |
| target_ph | 6.5 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.81 mS/cm** ✓

**Hinweis Erdkultur:** Die berechnete EC der Giessloessung (~0.8 mS/cm) liegt bewusst moderat. Erdsubstrat puffert und speichert Naehrstoffe. Bei wuechsigen Pflanzen (Armateras, Lavender Perfection) kann auf 6 ml/L TG gesteigert werden (~0.9 mS/cm). NPK 3:1:3 liefert ausreichend N fuer Blattaufbau, K fuer Staengelstaerke.

### 4.3 FLOWERING -- Knospenbildung + Bluete (Woche 13--26)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 26 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 80--120 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 30--50 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) bei ersten Knospen. Power Roots absetzen. Pure Zym weiter. **PK 13-14 (0.75 ml/L) NUR in Woche 15--16** -- einmaliger P/K-Boost waehrend peak Knospenansatz. Danach sofort absetzen! **KRITISCH: N minimal halten!** Steckbrief empfiehlt NPK 1:3:3 bis 0:2:3 in Bluete -- Terra Bloom liefert 2:2:4, was etwas mehr N enthaelt als ideal. Daher KEIN Sugar Royal (9-0-0) verwenden -- der organische N wuerde Blattwachstum foerdern und Bluete hemmen. **Deadheading ist entscheidend:** Verbluehtes konsequent bis zum naechsten Blattpaar zurueckschneiden. Ohne Ausputzen bildet die Pflanze Samen und stellt die Bluete ein. **K-Bedarf:** Hoher Kaliumbedarf fuer Bluetenqualitaet, Farbintensitaet und Knollenaufbau. Terra Bloom K2O 3.9% liefert dies. Ab September (Woche 23--26) Dosis auf 3 ml/L reduzieren -- Pflanze bereitet sich auf Seneszenz vor, K weiterhin fuer Knollenstabilisierung. Alle 7--10 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.9 |
| target_ph | 6.5 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| PK 13-14 ml/L | 0.75 (NUR Woche 15--16!) |

**EC-Budget (ohne PK):** 0.50 (TB 5.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.90 mS/cm** ✓
**EC-Budget (mit PK, W15--16):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.19 (PK 0.75ml) + ~0.4 (Wasser) = **~1.09 mS/cm** ✓
**EC-Budget (reduziert, W23--26):** 0.30 (TB 3.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm** ✓

**Hinweis PK 13-14:** Der Bluetebooster wird bei Dahlien in moderater Dosis (0.75 ml/L statt 1.5 ml/L bei Cannabis) eingesetzt. Dahlien profitieren vom P/K-Schub fuer den Knospenansatz, aber die EC-Grenze von 1.4 mS/cm darf nicht ueberschritten werden. Bei hartem Wasser (>0.5 mS/cm) PK-Dosis auf 0.5 ml/L reduzieren.

### 4.4 HARVEST -- Seneszenz + Knollenreife (Woche 27--30)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 27 | `phase_entries.week_start` |
| week_end | 30 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Pflanze nach erstem Frost einziehen lassen -- Laub wird schwarz/braun. 1--2 Tage stehen lassen fuer Kaelteimpuls. Staengel auf 10--15 cm zurueckschneiden. **Ausgrabe-Protokoll:** (1) Klumpen vorsichtig mit Grabegabel (NICHT Spaten!) lockern und herausheben. (2) Erde abschuetteln, NICHT abwaschen. (3) 5--7 Tage kopfueber bei 15--18 degC trocknen. (4) Beschriftung mit wasserfestem Marker (Sortenname!) -- bei 5 Cultivaren unverzichtbar. (5) Tochterknollen identifizieren und separieren. HARVEST-Phase wird im KA-Sinne fuer die Schnittblumenernte waehrend FLOWERING und fuer die Knollenernte am Saisonende verwendet. | `phase_entries.notes` |
| Giessplan-Override | Intervall 7 Tage (stark reduziert, Knollenreifung durch Trockenheit gefoerdert) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.5 DORMANCY -- Knollen-Ueberwinterung (Woche 31--52)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 31 | `phase_entries.week_start` |
| week_end | 52 | `phase_entries.week_end` |
| is_recurring | true | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Knollen frostfrei lagern bei 4--8 degC, dunkel. Lagermedium: leicht feuchtes Vermiculite, Kokoserde oder Zeitungspapier. **KEIN Wasser.** Monatliche Kontrolle: (1) Faeulnis -- befallene Stellen herausschneiden, mit Holzkohle behandeln. (2) Austrocknung -- bei zu trockener Lagerung Umgebungsluft leicht anfeuchten (NICHT die Knollen direkt). (3) Vorzeitiges Austreiben -- bei >10 degC moeglich, Lagertemperatur pruefen. (4) Maeusebefall ausschliessen. Dieser Schritt ist bei allen 5 Cultivaren identisch. | `phase_entries.notes` |
| Giessplan-Override | Intervall 0 Tage (kein Giessen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: (keiner -- kein Wasser, kein Duenger)**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | null |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.0 (trocken gelagert) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Perennierend via Knolle. Saisonplan Maerz--Oktober aktiv + November--Februar Dormanz. Zyklus-Neustart jaehrlich.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | PK 13-14 ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|----------------|-----------------|----------|
| Maerz | GERMINATION | -- | -- | -- | -- | -- | 0.4 | min. alle 5d |
| April | GERM->VEG | -->5.0 | -- | 1.0 | -->1.0 | -- | 0.4->0.8 | alle 7d |
| Mai | VEGETATIVE | 5.0 | -- | 1.0 | 1.0 | -- | 0.8 | alle 7d |
| Juni | VEG->FLO | 5.0->-- | -->5.0 | 1.0->-- | 1.0 | -- | 0.8->0.9 | alle 7d |
| Juli | FLOWERING | -- | 5.0 | -- | 1.0 | 0.75** | 0.9->1.1 | alle 7--10d |
| August | FLOWERING | -- | 5.0 | -- | 1.0 | -- | 0.9 | alle 7--10d |
| September | FLO->HARV | -- | 3.0->0 | -- | 1.0->-- | -- | 0.7->0.4 | alle 10d->-- |
| Oktober | HARVEST | -- | -- | -- | -- | -- | 0.4 | min. alle 7d |
| Nov--Feb | DORMANCY | -- | -- | -- | -- | -- | 0.0 | kein Wasser |

**PK 13-14 NUR ca. 2 Wochen im Juli (Woche 15--16, peak Knospenansatz).

```
Monat:       |Mär  |Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |Okt  |Nov--Feb|
KA-Phase:    |GERM |G→VEG|VEG  |V→FLO|FLOW |FLOW |F→HAR|HARV |DORMANZ|
Terra Grow:  |---  |-->==|===  |==→--|---  |---  |---  |---  |-------|
Terra Bloom: |---  |---  |---  |-->==|===  |===  |##→--|---  |-------|
Power Roots: |---  |===  |===  |==→--|---  |---  |---  |---  |-------|
Pure Zym:    |---  |-->==|===  |===  |===  |===  |==→--|---  |-------|
PK 13-14:    |---  |---  |---  |---  |=*=  |---  |---  |---  |-------|

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         --> = Start, =*= = nur 2 Wochen in diesem Monat
         ##→ = auslaufend/reduziert
```

### Jahresverbrauch (geschaetzt)

Bei einer Dahlie im 20--30L-Kuebel, 1.0--1.5 L Giessloessung pro Duengung, Duengung alle 7 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (8 Wo x 1/Wo x 5ml/L x 1.0L) = 40 ml | **~40 ml** |
| Terra Bloom | (12 Wo x 1/Wo x 5ml/L x 1.5L + 4 Wo x 1/Wo x 3ml/L x 1.5L) = 90 + 18 = 108 ml | **~110 ml** |
| Power Roots | (8 Wo x 1/Wo x 1ml/L x 1.0L) = 8 ml | **~8 ml** |
| Pure Zym | (20 Wo x 1/Wo x 1ml/L x 1.25L) = 25 ml | **~25 ml** |
| PK 13-14 | (2 Wo x 1/Wo x 0.75ml/L x 1.5L) = 2.25 ml | **~2.5 ml** |

**Kosten-Schaetzung:** Eine Dahlie verbraucht maessig Duenger. Bei 1L-Flaschen: Terra Bloom reicht fuer ca. 9 Pflanzen-Saisons, Terra Grow fuer ca. 25. PK 13-14 (1L-Flasche) reicht fuer ca. 400 Pflanzen-Saisons.

**Hochrechnung 5er-Beet (alle Cultivare):** Bei 5 Pflanzen ca. 200 ml Terra Grow + 550 ml Terra Bloom + 40 ml Power Roots + 125 ml Pure Zym + 12.5 ml PK 13-14 pro Saison.

---

## 6. Dahlie-spezifische Praxis-Hinweise

### Cultivar-Unterschiede

Alle 5 Cultivare teilen diesen Naehrstoffplan. Sortentypische Anpassungen:

| Cultivar | Wuchshoehe | Besonderheit | Anpassung |
|----------|-----------|--------------|-----------|
| Armateras | 90--110 cm | Dekorativ, Pink/Gelb, 12--15 cm Blueten | Standard-Dosierung |
| Hapet Daydream | 100--120 cm | Grossbluemig, Lachs/Koralle | Bei >120 cm: Stuetzstab verstaerken |
| Lavender Perfection | 100--120 cm | Dekorativ, Lavendel, 15--20 cm Blueten | Groesste Blueten -- K-Bedarf ggf. leicht erhoehen (6 ml/L TB) |
| Great Silence | 90--100 cm | Kaktus-Typ, Rosa/Creme | Kompakter, Standard-Dosierung |
| Embassy | 80--100 cm | Seerose-Typ, elegant | Kompaktester Cultivar, etwas weniger Giessvolumen |

### Substrat

- Naehrstoffreiche, humose Erde mit 20--30% Perlite fuer Drainage
- pH 6.0--7.0 (Plagron-Pufferung passt optimal)
- Kuebel: min. 20 L, besser 30 L; Ablaufloch zwingend
- Freiland: lockerer, humusreicher Gartenboden; schwere Tonboeden mit Sand und Kompost verbessern
- Pflanztiefe: Knolle 8--10 cm tief

### Stickstoff-Falle (WICHTIG)

**Der groesste Fehler bei Dahlienduengung:** Zu viel Stickstoff!

- Hochstickstoffige Rasenduenger oder Allzweckduenger mit hohem N-Anteil foerdern weiches Laub, schwache Staengel und verhindern Bluetenbildung
- Kein Sugar Royal (9-0-0) verwenden -- der organische N ist kontraproduktiv
- Ab Knospenbildung (FLOWERING) N-Anteil so niedrig wie moeglich halten
- Terra Bloom NPK 2-2-4 liefert noch etwas N, was fuer Basisversorgung reicht

### Entspitzen (Pinching)

- Bei 30--40 cm Wuchshoehe Haupttrieb ueber dem 3. Blattpaar einkuerzen
- Foerdert buschigen Wuchs mit deutlich mehr Bluetenstielen
- Zeitpunkt: ca. 4--5 Wochen nach Auspflanzen (Ende Mai / Anfang Juni)
- **Alle 5 Cultivare** profitieren vom Entspitzen

### Deadheading (Ausputzen)

- Verbluehte Blueten sofort bis zum naechsten Blattpaar zurueckschneiden
- Verhindert Samenbildung -- Pflanze investiert Energie in neue Blueten statt Samenreife
- Kann die Bluetezeit um Wochen verlaengern
- Bei Schnittblumen-Nutzung: Stiele mit scharfem Messer schneiden (nicht brechen)

### Knollen-Ueberwinterung (Zusammenfassung)

1. Nach erstem Frost Staengel auf 10--15 cm zurueckschneiden
2. Klumpen mit Grabegabel vorsichtig herausheben
3. Erde abschuetteln (nicht abwaschen)
4. 5--7 Tage kopfueber bei 15--18 degC trocknen
5. Beschriftung (Sortenname!) -- bei 5 Cultivaren unverzichtbar
6. In Kisten mit leicht feuchtem Vermiculite/Kokoserde einlagern
7. Lagerung: 4--8 degC, dunkel, frostfrei
8. Monatliche Kontrolle auf Faeulnis und Austrocknung

### Schaedlinge und Krankheiten

- **Blattlaeuse:** Haeufigster Schaedling. Kaliseife-Spritzung (2% Loesung) bei Befall
- **Schnecken:** Hauptfeind bei Jungpflanzen. Eisenphosphat-Schneckenkorn
- **Ohrwuermer:** Fressen an Bluetenblaettern (nachts). Umgedrehte Blumentoepfe als Fallen
- **Botrytis:** Grauschimmel bei feuchtem Wetter. Gute Luftzirkulation (60--70 cm Abstand)
- **Echter Mehltau:** Weisser Belag. Backpulver-Spray (1 TL/L + Spritzer Oel)
- **Knollenfaeule:** Wichtigste Krankheit in der Lagerung. Praeventiv: gut trocknen vor Einlagerung

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Dahlie \u2014 Plagron Terra + PK 13-14",
  "description": "Saisonplan f\u00fcr Dahlien (dekorative, halbgef\u00fcllte und Kaktus-Typen) mit Knollen-Vorkultur ab M\u00e4rz und Freilandkultur ab Mai. Plagron Terra-Linie mit 5 Produkten inkl. PK 13-14 Bl\u00fctebooster. Starkzehrer, perennierend via Knolle. 32 Wochen aktive Saison + 20 Wochen Dormanz. Geeignet f\u00fcr Cultivare: Armateras, Hapet Daydream, Lavender Perfection, Great Silence, Embassy.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["dahlie", "dahlia", "asteraceae", "plagron", "terra", "pk-13-14", "erde", "outdoor", "starkzehrer", "zierpflanze", "knollengew\u00e4chs", "schnittblume"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 1,
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
  "notes": "Knollen ab M\u00e4rz in T\u00f6pfen antreiben bei 15\u201318\u00b0C. NICHT gie\u00dfen bis Austrieb sichtbar! Knolle hat ausreichend Reserven. F\u00e4ulnisgefahr bei nasser Knolle. Knollenteilung m\u00f6glich (jedes St\u00fcck mind. 1 Auge).",
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
      "target_ph": 6.5,
      "fertilizer_dosages": [],
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
  "sequence_order": 2,
  "week_start": 5,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": 100,
  "magnesium_ppm": 40,
  "notes": "Volle Dosis Terra Grow (5 ml/L) + Power Roots + Pure Zym. Kr\u00e4ftiger Laub- und St\u00e4ngelaufbau. Calcium f\u00fcr St\u00e4ngelstabilit\u00e4t. Entspitzen bei 30\u201340 cm. Abh\u00e4rtung ab Woche 9. Auspflanzen nach Eisheiligen (Mitte Mai). St\u00fctzst\u00e4be einschlagen. Alle 7 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + Power Roots + Pure Zym. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.8,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
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
  "sequence_order": 3,
  "week_start": 13,
  "week_end": 26,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 100,
  "magnesium_ppm": 40,
  "notes": "Umstellung auf Terra Bloom (5 ml/L). Power Roots absetzen. PK 13-14 (0.75 ml/L) NUR in Woche 15\u201316 als Knospenansatz-Boost. Danach sofort absetzen! Kein Sugar Royal (N-\u00dcberschuss hemmt Bl\u00fcte). Deadheading konsequent durchf\u00fchren. Ab September (W23\u201326) Terra Bloom auf 3 ml/L reduzieren. Alle 7\u201310 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Pure Zym + PK 13-14 (nur W15\u201316!). Reihenfolge: Terra Bloom \u2192 PK 13-14 \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.9,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pk_13_14_key>", "ml_per_liter": 0.75, "optional": true, "_comment": "NUR Woche 15-16, danach absetzen!"}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.5}
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
  "week_start": 27,
  "week_end": 30,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Pflanze nach erstem Frost einziehen lassen. St\u00e4ngel auf 10\u201315 cm k\u00fcrzen. Knollen ausgraben, 5\u20137 Tage trocknen, beschriften (Sortenname!), einlagern.",
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
      "label": "Nur Wasser (Seneszenz)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Stark reduziertes Gie\u00dfen. Knollenreifung durch Trockenheit f\u00f6rdern.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
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
  "week_start": 31,
  "week_end": 52,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Knollen frostfrei lagern bei 4\u20138\u00b0C, dunkel. Kein Wasser, kein D\u00fcnger. Lagermedium: Vermiculite, Kokoserde oder Zeitungspapier. Monatliche Kontrolle auf F\u00e4ulnis/Austrocknung. Zyklus-Neustart im Fr\u00fchling bei Vorkeimen.",
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
| Fertilizer: Power Roots | `spec/ref/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: PK 13-14 | `spec/ref/products/plagron_pk_13_14.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Dahlia pinnata | `spec/ref/plant-info/dahlia_x_hybrida_armateras.md` | `species.scientific_name` |
| Cultivar: Armateras | `spec/ref/plant-info/dahlia_x_hybrida_armateras.md` | `cultivar.name` |
| Cultivar: Embassy | `spec/ref/plant-info/dahlia_embassy.md` | `cultivar.name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Mild giftig fuer Haustiere:** Dahlien sind laut ASPCA mild giftig fuer Katzen und Hunde (Phototoxische Polyacetylen-Verbindungen). Symptome: Speichelfluss, Erbrechen, Durchfall, Kontaktdermatitis
- **Fuer Menschen unbedenklich:** Dahlienblueten sind essbar und werden als Dekoration verwendet
- **Kontaktallergen:** Phototoxische Polyacetylene koennen bei empfindlichen Personen Kontaktdermatitis ausloesen, besonders beim Knollen-Handling. Handschuhe empfohlen
- **Stiele NICHT schneiden:** Geiztriebe und Schnittblumen mit der Hand abknipsen oder mit scharfem Messer -- Scheren koennen Krankheiten uebertragen (TMV, Bakterien)

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- PK 13-14 ist stark konzentriert -- Dosierung genau einhalten, Ueberdosierung fuehrt zu Wurzelschaeden

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/ref/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
5. Plagron PK 13-14 Produktdaten: `spec/ref/products/plagron_pk_13_14.md`
6. Dahlia pinnata 'Armateras' Pflanzensteckbrief: `spec/ref/plant-info/dahlia_x_hybrida_armateras.md`
7. Dahlia 'Embassy' Pflanzensteckbrief: `spec/ref/plant-info/dahlia_embassy.md`
8. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
9. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
