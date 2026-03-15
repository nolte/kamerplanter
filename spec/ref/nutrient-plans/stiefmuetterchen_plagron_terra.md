# Naehrstoffplan: Stiefmuetterchen (Fruehjahrsaussaat) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Viola x wittrockiana (Schwachzehrer, Outdoor, annuell kultiviert)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Pure Zym
> **Erstellt:** 2026-03-01
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/viola_x_wittrockiana.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Stiefmuetterchen (Fruehjahrsaussaat) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Stiefmuetterchen (Viola x wittrockiana) bei Fruehjahrsaussaat im Februar. Plagron Terra-Linie mit 3 Produkten. Einfacher Schwachzehrer-Plan: Indoor-Aussaat Feb/Maerz, Abhaertung April, Hauptbluete Mai--Juli, Seneszenz durch Sommerhitze ab August. Annuell -- kein Zyklus-Neustart. Blueten essbar (ASPCA safe). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | stiefmuetterchen, viola, pansy, plagron, terra, erde, outdoor, schwachzehrer, essbare-blueten, zierpflanze | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 08:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 3-Tage-Intervall als Basis fuer Outdoor-Beet/Topf. Stiefmuetterchen moegen gleichmaessige Feuchte, aber keine Staunaesse. Bei Hitze (>20 C) alle 2 Tage, bei Regen laenger warten. In GERMINATION (1 Tag, Spruehen) und DORMANCY (minimal, nur bei Trockenheit) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Stiefmuetterchen (Viola x wittrockiana) sind botanisch kurzlebige Biennien, werden aber ueberwiegend als Annuelle kultiviert. Sie sind typische Kuehlwetter-Pflanzen: Bluete bei 10--20 C, Seneszenz durch Sommerhitze (>25 C). Dieser Plan deckt einen Fruehjahrsaussaat-Zyklus ab (Indoor-Aussaat Februar → Outdoor-Bluete April--Juli → Sommer-Hitzetod August).

| Stiefmuetterchen-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-------------------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Anfang Februar | Indoor-Aussaat bei 15--18 C, Lichtkeimer. NICHT ueber 22 C (Thermoinhibition)! Dunkel abdecken bis Keimung. | false |
| Saemling | SEEDLING | 3--8 | Mitte Feb--Mitte Maerz | Pikierte Jungpflanzen auf Fensterbank. Viertel-Dosis Terra Grow. Kuehle Temperaturen (15--18 C) fuer kompakten Wuchs. | false |
| Vegetatives Wachstum + Abhaertung | VEGETATIVE | 9--14 | Mitte Maerz--Ende April | Halbe Dosis Terra Grow + Pure Zym. Aktives Blattwachstum, Rosette bilden. Letzte 2 Wochen: Abhaertung draussen (schrittweise an Aussenklima gewoehnen). | false |
| Bluete | FLOWERING | 15--28 | Mai--Mitte Juli | Hauptbluete bei kuehlem Fruehjahr/Fruehsommer. Terra Bloom + Pure Zym. Verblühtes konsequent ausputzen (Deadheading)! Reduzierung ab Juli wenn Temperaturen steigen. | false |
| Seneszenz / Sommer-Hitzetod | DORMANCY | 29--32 | Mitte Juli--Mitte August | Keine Duengung. Pflanze geht bei Dauerhitze (>25 C) in Seneszenz. Selbstaussaat zulassen oder Pflanzen entfernen. | false |

**Nicht genutzte Phasen:**
- **HARVEST** entfaellt (Zierpflanze, keine Ernte; Blueten sind essbar, aber nicht als Ernte im KA-Sinne)
- **FLUSHING** entfaellt (Schwachzehrer mit minimaler Salzbelastung)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Der Plan laeuft einmalig durch (32 Wochen). Fuer Herbstaussaat mit Ueberwinterung siehe Abschnitt 6.

**Lueckenlos-Pruefung:** 2 + 6 + 6 + 14 + 4 = 32 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Kleine Volumina (Schwachzehrer, kleine Pflanzen).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Leichtes Spruehen mit zimmerwarmem Wasser. Substrat gleichmaessig feucht, nicht nass. | `delivery_channels.notes` |
| method_params | drench (spray), 0.02 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow → Pure Zym → pH pruefen. Hinweis: Terra Grow puffert die Loesung auf pH 6.0--6.5 (Selbstpufferung) -- aktive pH-Absenkung auf 5.8 erfordert ggf. geringen Einsatz von pH-Down. | `delivery_channels.notes` |
| method_params | drench, 0.2--0.4 L pro Pflanze (je nach Topfgroesse; bei Topfkultur bis zur Drainage giessen) | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom → Pure Zym → pH pruefen. Hinweis: Terra Bloom puffert die Loesung auf pH 6.0--6.5 (Selbstpufferung) -- aktive pH-Absenkung auf 5.8 erfordert ggf. geringen Einsatz von pH-Down. | `delivery_channels.notes` |
| method_params | drench, 0.2--0.4 L pro Pflanze (je nach Topfgroesse; bei Topfkultur bis zur Drainage giessen) | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Seneszenz-Phase, nur bei Trockenheit giessen. | `delivery_channels.notes` |
| method_params | drench, 0.1 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Stiefmuetterchen

Stiefmuetterchen sind Schwachzehrer und reagieren empfindlich auf Ueberduengung. Ziel-EC der Gesamtloesung: **0.3--0.8 mS/cm** (inkl. Basis-Wasser). Leitungswasser liefert typisch 0.2--0.6 mS/cm. Bei hartem Wasser (>0.5 mS/cm) Duengerdosis um 25--50% reduzieren. **Wichtig:** Ueberduengung fuehrt zu ueppigem, weichem Laub auf Kosten der Bluete und erhoehter Botrytis-Anfaelligkeit.

**pH-Hinweis:** Terra Grow und Terra Bloom puffern die Naehrloesung auf pH 6.0--6.5 (Selbstpufferung). Der Zielwert `target_ph: 5.8` liegt knapp unterhalb dieses Pufferbereichs -- in der Praxis wird die Loesung ohne aktive pH-Absenkung eher bei pH 6.0--6.2 liegen, was fuer Stiefmuetterchen im Toleranzbereich (Steckbrief: pH 5.5--6.2) ist. Aktive pH-Absenkung mit pH-Down ist optional.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Bluete (durchgehend) |

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
| Hinweise | Aussaat in feuchte Aussaaterde. Lichtkeimer: Samen nur leicht andruecken, nicht mit Erde bedecken (duenn mit Vermiculit bestreuen ist ok). Temperatur 15--18 C. **KRITISCH: Nicht ueber 22 C** -- Thermoinhibition verhindert Keimung! Keine Heizmatte verwenden. Abdeckung (Klarsichtfolie/Dome) fuer gleichmaessige Luftfeuchtigkeit (80--90%). Keimdauer 10--14 Tage. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichtes Spruehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 5.8 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.00 + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

### 4.2 SEEDLING -- Saemling (Woche 3--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren ab 2. echtem Blattpaar in Einzeltoepfe (7 cm). Nach Pikieren 3--5 Tage erhoehte Luftfeuchtigkeit und gedaempftes Licht. Temperatur weiterhin kuehle 15--18 C halten -- waermere Temperaturen fuehren zu laengeligem, instabilem Wuchs. Indoor auf heller Fensterbank (Ost/West). Alle 14 Tage duengen. Pure Zym wird bewusst erst ab VEGETATIVE eingesetzt -- in der Saemlings-Phase ist noch kein abbaubares organisches Substratmaterial vorhanden (frische Aussaaterde). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| target_ph | 5.8 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis, Schwachzehrer) |
| Pure Zym ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + ~0.4 (Wasser) = **~0.52 mS/cm** ✓

### 4.3 VEGETATIVE -- Wachstum + Abhaertung (Woche 9--14)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 14 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis Terra Grow (2.5 ml/L) + Pure Zym. Aktiver Rosettenaufbau, Blattwachstum. NPK 2:1:2 fuer kompakten Wuchs. Ab Woche 13 (ca. Mitte April): schrittweise Abhaertung draussen beginnen -- erst stundenweise, dann ganztags, schliesslich nachts. Stiefmuetterchen vertragen leichten Frost (bis -5 C), daher fruehe Abhaertung moeglich. In den letzten 2 Wochen (Abhaertung): Keine Dosierungserhoehung, aber K-Betonung foerderlich -- Terra Grow liefert K im 3-1-3-Profil ausreichend (Steckbrief empfiehlt NPK 1:1:2 fuer Abhaertung). Auspflanzung ins Freiland/Kuebel ab Ende April. Alle 14 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| target_ph | 5.8 |
| Terra Grow ml/L | 2.5 (halbe Dosis) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.20 (TG 2.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.60 mS/cm** ✓

**EC-Abweichung vom Steckbrief:** Der Zielwert 0.6 mS/cm liegt bewusst unterhalb des Steckbrief-Optimums (0.8--1.2 mS/cm) -- konservative Schwachzehrer-Strategie, da Ueberduenung bei Stiefmuetterchen die Bluetenbildung hemmt und Botrytis-Anfaelligkeit erhoht.

### 4.4 FLOWERING -- Bluete (Woche 15--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 15 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Terra Bloom 3.0 ml/L + Pure Zym. P+K-betontes Profil foerdert Bluetenbildung. Der hohe Boranteil in Terra Bloom (0.48%) unterstuetzt die Pollenkeimung. **Deadheading ist entscheidend:** Verblühtes konsequent ausputzen -- dies verlaengert die Bluetezeit um Wochen! Ohne Ausputzen bildet die Pflanze Samen und stellt die Bluete ein. Ab Mitte Juli (Wochen 25--28) bei steigenden Temperaturen Dosis auf 2.0 ml/L reduzieren und Halbschatten-Standort waehlen. Alle 14 Tage duengen. **Mg-Versorgung:** Terra Bloom enthaelt 0.8% MgO -- bei Schwachzehrern ausreichend. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.7 |
| target_ph | 5.8 |
| Terra Bloom ml/L | 3.0 |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.30 (TB 3ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm** ✓

**EC-Abweichung vom Steckbrief:** Der Zielwert 0.7 mS/cm liegt bewusst unterhalb des Steckbrief-Optimums (0.8--1.2 mS/cm) -- konservative Schwachzehrer-Strategie. Bei hartem Wasser (>0.5 mS/cm) Duengerdosis weiter reduzieren.

### 4.5 DORMANCY -- Seneszenz / Sommer-Hitzetod (Woche 29--32)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 29 | `phase_entries.week_start` |
| week_end | 32 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Sommerhitze (dauerhaft >25 C) loest Seneszenz aus: Pflanzen werden laengelig, Blueten werden kleiner und seltener, Blaetter vergilben. Dies ist der natuerliche Lebenszyklusabschluss bei Fruehjahrsaussaat. **Optionen:** (1) Pflanzen entfernen und Beet fuer Sommerblueher raeumen. (2) Selbstaussaat zulassen -- reife Samenkapseln oeffnen sich und verteilen Samen, die im Herbst oder naechstem Fruehling keimen. (3) Bei kuehlen Sommern (selten) kann die Bluete bis Herbst weitergehen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (minimal, nur bei Trockenheit) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Fruehjahrsaussaat-Zyklus, Start Anfang Februar.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|---------------|-----------------|----------|
| Feb | GERM→SEED | -- → 1.5 | -- | -- | 0.3→0.4 | spray → alle 14d |
| Maerz | SEED→VEG | 1.5→2.5 | -- | --→1.0 | 0.4→0.5 | alle 14d |
| April | VEG | 2.5 | -- | 1.0 | 0.5 | alle 14d |
| Mai | FLOWERING | -- | 3.0 | 1.0 | 0.6 | alle 14d |
| Juni | FLOWERING | -- | 3.0 | 1.0 | 0.6 | alle 14d |
| Juli | FLO→DOR | -- | 2.0→0 | 1.0→-- | 0.5→0.3 | alle 14d→-- |
| August | DORMANCY | -- | -- | -- | 0.3 | minimal |

```
Monat:        |Feb|Mär|Apr|Mai|Jun|Jul|Aug|
KA-Phase:     |G→S|S→V|VEG|FLO|FLO|F→D|DOR|
Terra Grow:   |---|#--|##-|---|---|---|---|
Terra Bloom:  |---|---|---|===|===|#--|---|
Pure Zym:     |---|---|===|===|===|#--|---|

Legende: --- = nicht verwendet, #-- = Viertel-Dosis,
         ##- = halbe Dosis, === = volle Phase-Dosis
         #-- bei Bloom = auslaufend/reduziert
```

### Jahresverbrauch (geschaetzt)

Bei einem Stiefmuetterchen im 1.5L-Topf/Beet, 0.2 L Giessloessung pro Duengung, Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (3 Duengungen x 1.5ml/L x 0.2L + 3 Duengungen x 2.5ml/L x 0.2L) = 0.9 + 1.5 = 2.4 ml | **~2.5 ml** |
| Terra Bloom | (6 Duengungen x 3.0ml/L x 0.2L + 2 Duengungen x 2.0ml/L x 0.2L) = 3.6 + 0.8 = 4.4 ml | **~4.5 ml** |
| Pure Zym | (11 Duengungen x 1.0ml/L x 0.2L) = 2.2 ml | **~2 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche jedes Produkts reicht fuer hunderte Stiefmuetterchen-Saisons. Sinnvoll nur in Kombination mit anderen Pflanzen oder bei grossflaechiger Bepflanzung.

**Hochrechnung 10er-Balkonkasten (1m):** Bei 10 Pflanzen ca. 25 ml Terra Grow + 45 ml Terra Bloom + 20 ml Pure Zym pro Saison.

---

## 6. Stiefmuetterchen-spezifische Praxis-Hinweise

### Substrat

- Naehrstoffarme bis maessig geduengte Blumenerde, pH 5.5--6.2
- Leicht durchlaessig: 10--20% Perlite oder Sand einmischen
- Staunaesse vermeiden -- flaches Wurzelsystem fault schnell
- Fuer Aussaat: spezielle Aussaaterde (naehrstoffarm, feinkruemelig)
- Topfgroesse: 1--1.5 L pro Pflanze, Balkonkasten ca. 20 cm Abstand

### Thermoinhibition (Keimung)

- **Kritischster Punkt des gesamten Plans:** Keimtemperatur MUSS unter 22 C bleiben
- Bei Zimmertemperatur >22 C: Aussaatschale an kuehles Fenster stellen (Nordseite) oder in kuehlen Raum (Keller, Garage)
- **Keine Heizmatte!** (anders als bei den meisten anderen Pflanzen)
- Optimaler Bereich: 15--18 C, Keimung in 10--14 Tagen
- Bei 10--15 C: Keimung langsamer (14--21 Tage) aber zuverlaessig
- Ab 22 C: Keimrate sinkt drastisch, ab 25 C praktisch keine Keimung

### Deadheading (Ausputzen)

- **Wichtigste Pflegemassnahme bei Stiefmuetterchen:** Verblühte Blueten sofort abknipsen
- Mit Daumen und Zeigefinger den Stiel unterhalb der verwelkten Bluete abbrechen
- Verhindert Samenbildung -- Pflanze investiert Energie in neue Blueten statt Samenreife
- Kann die Bluetezeit um 4--8 Wochen verlaengern
- Alternativ bei gewuenschter Selbstaussaat: ab Ende Juni einige Samenkapseln ausreifen lassen

### Essbare Blueten

- Stiefmutterchenbluten sind essbar und ungiftig (ASPCA safe)
- Verwendung: Salatdekoration, Eisdekoration, kandierte Blueten, Tee
- **Wichtig:** Nur ungeduengte Blueten ernten (mind. 7 Tage nach letzter Duengung -- 2--3 Giesszyklen fuer vollstaendige Salzpassage)
- Keine Blueten verwenden, die mit Pflanzenschutzmitteln behandelt wurden
- Nur eigene, nachweislich unbehandelte Pflanzen verwenden (Kaufware oft mit Pestiziden)

### Hitzestress und Standort

- Stiefmuetterchen sind Kuehle-Liebhaber: optimal bei 10--20 C Tagestemperatur
- Ab 25 C Dauertemperatur beginnt die Seneszenz (laengelige Triebe, kleine Blueten)
- Standort im Spaetfruehling/Fruehsommer: Morgensonne + Nachmittagsschatten ideal
- Bei Balkonkaesten Suedseite meiden ab Juni -- Ost- oder Westseite bevorzugen
- Kuehle Naechte (unter 15 C) foerdern die Bluetenbildung stark

### Herbstaussaat mit Ueberwinterung (alternativer Zyklus)

Fuer einen laengeren Bluete-Zeitraum kann alternativ im Spaetsommer/Herbst ausgesaet werden:

1. **August:** Aussaat indoor bei 15--18 C (identisch zu Fruehjahr)
2. **September--Oktober:** Saemling + Vegetativ, Auspflanzung ins Freiland
3. **Oktober--November:** Erste Herbstbluete bei kuehlen Temperaturen
4. **November--Februar:** Winterruhe (DORMANCY), Mulchschutz bei Kahlfrost unter -10 C
5. **Maerz--Juli:** Kraeftige Fruehjahrs-Hauptbluete (staerker als bei Fruehjahrsaussaat, da Pflanze etabliert ist), dann Sommer-Seneszenz

Kalium-betonte Duengung im Oktober (K-Emphasis) verbessert die Frosttoleranz fuer die Ueberwinterung. Dieser alternative Zyklus ist in KA als separater NutrientPlan abzubilden.

### Botrytis-Praevention (Grauschimmel)

Botrytis cinerea ist die wichtigste Krankheit bei Stiefmuetterchen, besonders bei kuehler, feuchter Witterung:

- **Luftzirkulation:** Ausreichend Pflanzabstand (20 cm), nicht zu eng bepflanzen
- **Giessen:** Morgens giessen, nie ueber die Blueten giessen, Blaetter sollen ueber Tag abtrocknen
- **Befallene Teile:** Sofort entfernen und entsorgen (nicht kompostieren)
- **Substratpflege:** Pure Zym hilft, abgestorbenes organisches Material abzubauen und reduziert so den Naehrboden fuer Pilze

### Schaedlinge

- **Schnecken:** Hauptfeind im Outdoor-Beet, besonders bei Jungpflanzen. Schneckenkorn (Eisen-III-Phosphat) oder Schneckennematoden einsetzen.
- **Blattlaeuse:** Ab Fruehling moeglich. Kaliseife-Spritzung (2% Loesung) bei Befall.
- **Trauermücken:** Bei Indoor-Aussaat in feuchtem Substrat. Gelbtafeln + Steinernema-Nematoden.

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Stiefmütterchen (Frühjahrsaussaat) — Plagron Terra",
  "description": "Saisonplan für Stiefmütterchen (Viola x wittrockiana) bei Frühjahrsaussaat. Plagron Terra-Linie mit 3 Produkten. Indoor-Aussaat Feb/März, Hauptblüte Mai–Juli, Seneszenz durch Sommerhitze ab August. Schwachzehrer, annuell kultiviert. Blüten essbar.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["stiefmütterchen", "viola", "pansy", "plagron", "terra", "erde", "outdoor", "schwachzehrer", "essbare-blüten", "zierpflanze"],
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
  "notes": "Aussaat bei 15–18 °C, Lichtkeimer. NICHT über 22 °C (Thermoinhibition)! Keine Heizmatte. Substrat feucht halten, leicht sprühen.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 1,
    "preferred_time": "08:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-keimung",
      "label": "Sprühwasser Keimung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein Dünger. Leichtes Sprühen, Substrat gleichmäßig feucht.",
      "target_ec_ms": 0.0,
      "target_ph": 5.8,
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
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow. Pikierte Jungpflanzen auf kühler Fensterbank (15–18 °C). Alle 14 Tage düngen. Pure Zym erst ab VEGETATIVE — in Sämlingsphase noch kein abbaubares organisches Substratmaterial vorhanden.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsdüngung (Gießkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis. Schwachzehrer — weniger ist mehr.",
      "target_ec_ms": 0.5,
      "target_ph": 5.8,
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
  "week_end": 14,
  "is_recurring": false,
  "npk_ratio": [2.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Halbe Dosis Terra Grow + Pure Zym. Aktiver Rosettenaufbau. Ab Woche 13 Abhärtung draußen beginnen. In den letzten 2 Wochen (Abhärtung): K-Betonung förderlich — Terra Grow liefert K im 3-1-3-Profil ausreichend. Auspflanzung Ende April. Alle 14 Tage düngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsdüngung (Gießkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow halbe Dosis + Pure Zym. Reihenfolge: Terra Grow → Pure Zym → pH prüfen. Terra Grow puffert auf pH 6.0–6.5 (Selbstpufferung).",
      "target_ec_ms": 0.6,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.5, "optional": false},
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
  "week_start": 15,
  "week_end": 28,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom 3 ml/L + Pure Zym. P+K-betont für Blütenbildung. Verblühtes konsequent ausputzen (Deadheading)! Ab Mitte Juli bei Hitze auf 2 ml/L reduzieren. Alle 14 Tage düngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Blütendüngung (Gießkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Pure Zym. Reihenfolge: Terra Bloom → Pure Zym → pH prüfen. Terra Bloom puffert auf pH 6.0–6.5 (Selbstpufferung).",
      "target_ec_ms": 0.7,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
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
  "week_start": 29,
  "week_end": 32,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Seneszenz durch Sommerhitze. Keine Düngung. Pflanze entfernen oder Selbstaussaat zulassen. Nur bei Trockenheit gießen.",
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
      "notes": "Kein Dünger. Nur bei Trockenheit gießen.",
      "target_ec_ms": 0.0,
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
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Viola x wittrockiana | `spec/ref/plant-info/viola_x_wittrockiana.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Ungiftig:** Stiefmuetterchen sind fuer Katzen, Hunde und Kinder unbedenklich (ASPCA safe)
- **Essbare Blueten:** Blueten sind essbar und werden als Lebensmittel-Garnitur verwendet
- Keine besonderen Haustier- oder Kinderwarnungen erforderlich

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- **Essbare-Blueten-Hinweis:** Mindestens 7 Tage nach letzter Duengung warten, bevor Blueten zum Verzehr geerntet werden (2--3 Giesszyklen fuer vollstaendige Salzpassage durch das Substrat)

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
4. Viola x wittrockiana Pflanzendaten: `spec/ref/plant-info/viola_x_wittrockiana.md`
5. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
6. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
