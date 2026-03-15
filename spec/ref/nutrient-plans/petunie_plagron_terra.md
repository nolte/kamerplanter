# Naehrstoffplan: Petunie -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Petunia x hybrida (Mittelzehrer bis Starkzehrer, Outdoor, annuell in Mitteleuropa)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_grow.md, spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_sugar_royal.md, spec/ref/plant-info/petunia_x_hybrida.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Petunie -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Garten-Petunien (Petunia x hybrida) mit Indoor-Voranzucht ab Februar und Freilandkultur ab Mai. Plagron Terra-Linie mit 4 Produkten. Mittelzehrer bis Starkzehrer (heavy_feeder laut Steckbrief) mit hohem P/K-Bedarf in der Dauerbluete und kritischem Eisenbedarf. Annuell in Mitteleuropa -- kein Zyklus-Neustart. Balkonkasten, Ampel und Beet. Dauerbluete Mai--Oktober. Mitte-Sommer-Rueckschnitt (Juli) foerdert zweite Bluetenwelle. Ungiftig (ASPCA safe). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | petunie, petunia, solanaceae, plagron, terra, erde, outdoor, balkon, ampel, mittelzehrer, starkzehrer, zierpflanze, dauerblueher | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 2 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 2-Tage-Intervall als Basis fuer Balkonkasten/Kuebel. Petunien haben hohen Wasserbedarf -- an heissen Sommertagen (>28 degC) taeglich giessen, Ampeln ggf. morgens und abends. In GERMINATION (1 Tag, Spruehen) und DORMANCY (Seneszenz, minimal) ueber `watering_schedule_override` angepasst. Morgens giessen, Blueten moeglichst nicht benetzen (Botrytis-Risiko).

---

## 2. Phasen-Mapping

Petunia x hybrida ist in Mitteleuropa eine annuelle Zierpflanze mit langer Dauerbluete (Mai--Oktober). Laut Steckbrief heavy_feeder mit kritischem Eisenbedarf. Der haeufigste Naehrstoffmangel ist Eisenchlorose (gelbe Blaetter bei gruenen Adern) bei pH > 6.2. Substrat-pH unter 6.2 halten! Mitte-Sommer-Rueckschnitt um 1/3 foerdert kraeftigen Neuaustrieb und zweite Bluetenwelle.

| Petunie-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|---------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Anfang Februar | Indoor-Aussaat bei 22--24 degC. Lichtkeimer! Samen nur andruecken, nicht bedecken. Abdeckung (Dome) fuer 80--95% Luftfeuchte. | false |
| Saemling | SEEDLING | 3--8 | Mitte Feb--Ende Maerz | Pikieren nach 1. Laubblattpaar. Halbe Dosis Terra Grow. Kuehle Nachttemperaturen (15--18 degC) fuer kompakten Wuchs. | false |
| Vegetatives Wachstum + Abhaertung | VEGETATIVE | 9--14 | April--Mitte Mai | Volle Dosis Terra Grow + Pure Zym + Sugar Royal. Umtopfen in Endgefaesse. Abhaertung ab Mitte April. Auspflanzen nach Eisheiligen (ca. 15. Mai). | false |
| Dauerbluete | FLOWERING | 15--36 | Mitte Mai--Mitte Oktober | P/K-betonte Duengung mit Terra Bloom + Pure Zym + Sugar Royal. Woechentlich duengen! Eisenchelat bei Chlorose. Mitte Juli: Rueckschnitt um 1/3 fuer Neuaustrieb. | false |
| Seneszenz / Frostende | DORMANCY | 37--40 | Mitte Oktober--Anfang November | Keine Duengung. Pflanze stirbt bei erstem Frost ab. Optional: Stecklinge fuer Ueberwinterung abnehmen (September). | false |

**Nicht genutzte Phasen:**
- **HARVEST** entfaellt (Zierpflanze, keine Ernte)
- **FLUSHING** entfaellt (Freiland/Kuebel mit Erdsubstrat)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Der Plan laeuft einmalig durch (40 Wochen). Fuer Ueberwinterung via Stecklinge siehe Abschnitt 6.

**Lueckenlos-Pruefung:** 2 + 6 + 6 + 22 + 4 = 40 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Groessere Volumina als bei Schwachzehrern (Mittelzehrer/Starkzehrer, Ampeln und Kuebel mit hohem Wasserverbrauch).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Leichtes Spruehen mit zimmerwarmem Wasser. Substrat gleichmaessig feucht, nicht nass. Abdeckung (Dome) fuer hohe Luftfeuchte. | `delivery_channels.notes` |
| method_params | drench (spray), 0.02 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym + Sugar Royal ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> Sugar Royal -> pH pruefen. Terra Grow puffert auf pH 6.0--6.5 (Selbstpufferung). pH unter 6.2 halten wegen Eisenverfuegbarkeit! | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze (je nach Topfgroesse; bei Ampeln bis zur Drainage giessen) | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym + Sugar Royal ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> Sugar Royal -> pH pruefen. Terra Bloom puffert auf pH 6.0--6.5. pH unter 6.2 halten! Terra Bloom enthaelt 0.21% Fe und 0.8% Mg -- bei Chlorose trotzdem Eisenchelat supplementieren. | `delivery_channels.notes` |
| method_params | drench, 0.5--1.0 L pro Pflanze (Ampeln deutlich mehr; bei Hitze bis zur Drainage) | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Seneszenz-Phase nach Frost, nur bei Trockenheit giessen. | `delivery_channels.notes` |
| method_params | drench, 0.2 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Petunien

Petunien sind laut Steckbrief Starkzehrer (heavy_feeder) mit EC-Optimum **1.2--2.0 mS/cm** in der Bluetephase. Der EC-Bereich ist hoeher als bei typischen Schwachzehrern. Leitungswasser liefert typisch 0.2--0.6 mS/cm. **Wichtig:** Petunien sind eisenbeduerftiger als die meisten Balkonpflanzen -- bei pH > 6.2 wird Eisen im Substrat unloeoslich (Chlorose). Substrat-pH unter 6.2 halten!

**pH-Hinweis:** Terra Grow und Terra Bloom puffern die Naehrloesung auf pH 6.0--6.5 (Selbstpufferung). Der Zielwert `target_ph: 5.8` liegt am unteren Rand des Pufferbereichs -- fuer Petunien ist ein niedrigerer pH (5.5--6.0) ausdruecklich gewuenscht wegen der Eisenverfuegbarkeit. Bei kalkreichem Wasser (>14 degdH) aktive pH-Absenkung mit pH-Down empfehlenswert.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Bluete (durchgehend) |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Bluete (Aminosaeuren, Chlorophyll-Stimulation) |

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
| Hinweise | Aussaat in feuchte Aussaaterde. **Lichtkeimer:** Samen nur andruecken, NICHT mit Erde bedecken. Temperatur 22--24 degC (Warmkeimer -- anders als Stiefmuetterchen!). Abdeckung (Klarsichtfolie/Dome) fuer 80--95% Luftfeuchte. Petuniensamen sind Staubsamen (extrem fein) -- Pille/Saatscheibe erleichtert die Handhabung. Keimdauer 7--14 Tage. Licht obligatorisch fuer Keimung (min. 50 umol/m2/s). | `phase_entries.notes` |
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
| Calcium (ppm) | 60 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 25 | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis Terra Grow (2.5 ml/L). Pikieren nach Entwicklung des 1. Laubblatts in 7--9 cm Einzeltoepfe. Nach Pikieren 3--5 Tage erhoehte Luftfeuchtigkeit (70--80%) und gedaempftes Licht (~100 umol/m2/s). Nachttemperaturen 15--18 degC fuer kompakten Wuchs. Pure Zym erst ab VEGETATIVE -- in der Saemlings-Phase noch kein abbaubares organisches Substratmaterial. Alle 14 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| target_ph | 5.8 |
| Terra Grow ml/L | 2.5 (halbe Dosis) |
| Pure Zym ml/L | -- (noch nicht) |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.20 (TG 2.5ml) + ~0.4 (Wasser) = **~0.60 mS/cm** ✓

**Hinweis:** EC 0.6 mS/cm liegt im unteren Steckbrief-Bereich (0.4--0.8 fuer Saemlinge). Petunien vertragen als Saemlinge bereits mehr als typische Schwachzehrer.

### 4.3 VEGETATIVE -- Wachstum + Abhaertung (Woche 9--14)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 14 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 100 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 40 | `phase_entries.magnesium_ppm` |
| Hinweise | Volle Dosis Terra Grow (5 ml/L) + Pure Zym + Sugar Royal. Aktives Laub- und Triebwachstum. Ca-Betonung fuer Zellwandaufbau. Umtopfen in Endgefaesse (Balkonkasten, Ampel, Kuebel) mit guter Drainage (10--20% Perlite). Langzeitduenger optional beim Umtopfen untermischen. Ab Woche 11 (Mitte April): Abhaertung draussen beginnen -- Petunien sind NICHT frosthart, daher erst nach Eisheiligen (ca. 15. Mai) endgueltig auspflanzen. Pflanzabstand 25--40 cm. Alle 7--14 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.8 |
| target_ph | 5.8 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.40 (TG 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.82 mS/cm** ✓

**Hinweis:** EC 0.82 mS/cm liegt im Steckbrief-Bereich fuer Vegetativ (0.8--1.4 mS/cm). Bei wuechsigen Sorten (Wave, Supertunia) kann auf 6 ml/L TG gesteigert werden (~0.9 mS/cm).

### 4.4 FLOWERING -- Dauerbluete (Woche 15--36)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 15 | `phase_entries.week_start` |
| week_end | 36 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 2, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 120 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) + Pure Zym + Sugar Royal. K-betonte Duengung foerdert Bluetenansatz, Farbintensitaet und Bluetenmenge. **Woechentlich duengen!** Durch haeufiges Giessen werden Naehrstoffe aus dem begrenzten Substratvolumen staendig ausgewaschen. Terra Bloom enthaelt 0.21% Fe und 0.8% MgO -- bei Eisenchlorose (gelbe Blaetter, gruene Adern) trotzdem Eisenchelat (Fe-EDTA, 0.5--1 g/10 L) supplementieren. **Mitte-Sommer-Rueckschnitt (Juli, ca. Woche 23):** Triebe um ca. 1/3 zurueckschneiden -- foerdert kraeftigen Neuaustrieb und zweite Bluetenwelle ab August. Nach Rueckschnitt: einmalig Terra Grow (3 ml/L) statt Terra Bloom fuer Neuaustrieb, danach zurueck auf Terra Bloom. Deadheading bei Grandiflora-Typen; Multiflora/Wave-Typen sind weitgehend selbstreinigend. Ab Oktober (Woche 33--36) Dosis auf 3 ml/L reduzieren. Alle 7 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.9 |
| target_ph | 5.8 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.92 mS/cm** ✓
**EC-Budget (mit Eisenchelat bei Chlorose):** ~0.92 + ~0.05 = **~0.97 mS/cm** ✓
**EC-Budget (reduziert, W33--36):** 0.30 (TB 3.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.72 mS/cm** ✓

**Hinweis:** Der Steckbrief empfiehlt 1.2--2.0 mS/cm fuer die Bluetephase. Die berechnete EC (~0.9 mS/cm) liegt etwas darunter. Bei wuechsigen Sorten und weichem Wasser kann auf 6 ml/L TB gesteigert werden (~1.0 mS/cm). Bei Ampeln mit taeglichem Giessen ist woechentliche Duengung essenziell -- die Naehrstoffe werden durch das haeufige Giessen staendig ausgespuelt.

### 4.5 DORMANCY -- Seneszenz / Frostende (Woche 37--40)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 37 | `phase_entries.week_start` |
| week_end | 40 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Erster Frost (<0 degC) loest Seneszenz aus -- Pflanze stirbt ab, Laub wird braun/schwarz. Pflanze entfernen, Gefaesse reinigen. **Optional Ueberwinterung via Stecklinge:** 10 cm Triebspitzenstecklinge im September abnehmen, in Anzuchterde bewurzeln (18--20 degC), dann frostfrei bei 5--12 degC hell ueberwintern. Nur lohnend fuer vegetativ vermehrte Sorten (Surfinia, Supertunia), da F1-Saatgut nicht sortenecht nachzuziehen ist. | `phase_entries.notes` |
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

Annueller Zyklus, Start Anfang Februar.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|---------------|-----------------|-----------------|----------|
| Feb | GERM->SEED | -- -> 2.5 | -- | -- | -- | 0.4->0.6 | spray -> alle 14d |
| Maerz | SEEDLING | 2.5 | -- | -- | -- | 0.6 | alle 14d |
| April | SEED->VEG | 2.5->5.0 | -- | -->1.0 | -->1.0 | 0.6->0.8 | alle 14d->7d |
| Mai | VEG->FLO | 5.0->-- | -->5.0 | 1.0 | 1.0 | 0.8->0.9 | alle 7d |
| Juni | FLOWERING | -- | 5.0 | 1.0 | 1.0 | 0.9 | alle 7d |
| Juli | FLOWERING | 3.0* | 5.0 | 1.0 | 1.0 | 0.9 | alle 7d |
| August | FLOWERING | -- | 5.0 | 1.0 | 1.0 | 0.9 | alle 7d |
| September | FLOWERING | -- | 5.0 | 1.0 | 1.0 | 0.9 | alle 7d |
| Oktober | FLO->DOR | -- | 3.0->0 | 1.0->-- | 1.0->-- | 0.7->0.4 | alle 7d->-- |
| November | DORMANCY | -- | -- | -- | -- | 0.4 | minimal |

*Terra Grow 3.0 ml/L einmalig nach Mitte-Juli-Rueckschnitt fuer Neuaustrieb, danach zurueck auf Terra Bloom.

```
Monat:        |Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|
KA-Phase:     |G→S|SEE|S→V|V→F|FLO|FLO|FLO|FLO|F→D|DOR|
Terra Grow:   |--|#--|#→=|=→-|---|=*-|---|---|---|---|
Terra Bloom:  |---|---|---|→==|===|===|===|===|##→|---|
Pure Zym:     |---|---|→==|===|===|===|===|===|==→|---|
Sugar Royal:  |---|---|→==|===|===|===|===|===|==→|---|

Legende: --- = nicht verwendet, #-- = Viertel/halbe Dosis,
         ##- = halbe Dosis, === = volle Phase-Dosis,
         =*- = einmalig nach Rueckschnitt
         → = Uebergang
```

### Jahresverbrauch (geschaetzt)

Bei einer Petunie im 10L-Kuebel/Balkonkasten, 0.5 L Giessloessung pro Duengung, Duengung alle 7 Tage in der Bluete:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (3 x 2.5ml/L x 0.3L + 3 x 5.0ml/L x 0.4L + 1 x 3.0ml/L x 0.5L) = 2.25 + 6.0 + 1.5 = 9.75 ml | **~10 ml** |
| Terra Bloom | (22 x 5.0ml/L x 0.5L + 3 x 3.0ml/L x 0.5L) = 55 + 4.5 = 59.5 ml | **~60 ml** |
| Pure Zym | (25 x 1.0ml/L x 0.45L) = 11.25 ml | **~11 ml** |
| Sugar Royal | (25 x 1.0ml/L x 0.45L) = 11.25 ml | **~11 ml** |

**Kosten-Schaetzung:** Eine Petunie verbraucht maessige Duengermengen. Eine 1L-Flasche Terra Bloom reicht fuer ca. 16 Petunien-Saisons. Bei 6 Petunien im 1m-Balkonkasten: ca. 60 ml Terra Grow + 360 ml Terra Bloom + 66 ml Pure Zym + 66 ml Sugar Royal pro Saison.

---

## 6. Petunien-spezifische Praxis-Hinweise

### Substrat

- Hochwertige Balkon- und Kuebelpflanzenerde mit guter Drainage
- pH 5.5--6.2 (kritisch fuer Eisenverfuegbarkeit!)
- 10--20% Perlite fuer verbesserte Drainage
- Langzeitduenger beim Einpflanzen optional untermischen
- Ampeln: min. 10--20 L Substratvolumen
- Balkonkasten: 25 cm Abstand zwischen Pflanzen
- Kuebel: min. 5--15 L je nach Sortengroesse

### Eisenchlorose (WICHTIG)

**Das haeufigste Naehrstoffproblem bei Petunien:**

- Symptom: Juengere Blaetter werden gelb, Blattadern bleiben gruen (intervenale Chlorose)
- Ursache: Eisen wird bei pH > 6.2 im Substrat unloeoslich
- Praevention: Substrat-pH unter 6.2 halten; bei kalkreichem Wasser pH-Down verwenden
- Behandlung: Eisenchelat-Duenger (Fe-EDTA oder Fe-HEEDTA), 0.5--1 g/10 L als Giessloesung
- Terra Bloom enthaelt 0.21% Fe -- bei optimalen pH-Werten ausreichend, bei pH > 6.2 reicht das nicht
- Petunien gehoeren zusammen mit Calibrachoa und Pelargonien zu den eisenbeduertigsten Balkonpflanzen

### Mitte-Sommer-Rueckschnitt (Juli)

- Ca. Mitte Juli (Woche 23): Triebe um ca. 1/3 zurueckschneiden
- Foerdert kraeftigen Neuaustrieb und zweite Bluetenwelle ab August
- Grossblumige Grandiflora-Typen profitieren besonders
- Wave- und Multiflora-Typen: weniger aggressiv zurueckschneiden (nur Spitzen)
- Nach Rueckschnitt: einmalig N-betonte Duengung (Terra Grow 3 ml/L) fuer Neuaustrieb

### Wasserversorgung (kritisch bei Ampeln)

- Petunien in Ampeln und Kuebeln haben sehr hohen Wasserbedarf
- An heissen Sommertagen (>28 degC) taeglich giessen, ggf. morgens UND abends
- Morgens giessen -- Blueten moeglichst nicht benetzen (Botrytis-Risiko bei Grandiflora)
- Substrat darf nie komplett austrocknen (Welke-Schaeden oft irreversibel)
- Bei taeglichem Giessen werden Naehrstoffe staendig ausgewaschen -- daher woechentliche Duengung essenziell

### Ueberwinterung via Stecklinge (optional)

Fuer vegetativ vermehrte Sorten (Surfinia, Supertunia, Wave):

1. **September:** 10 cm Triebspitzenstecklinge abnehmen
2. **Bewurzeln:** In Anzuchterde bei 18--22 degC, 14--21 Tage
3. **Oktober--April:** Frostfrei bei 5--12 degC, hell (min. 6--8 Stunden indirektes Licht)
4. **Winter:** Alle 14 Tage sparsam giessen, kein Duenger
5. **Mai:** Abhaerten und nach Eisheiligen auspflanzen

**Hinweis:** F1-Hybrid-Saatgutsorten (Easy Wave etc.) koennen nicht sortenecht ueberwintert werden. Ueberwinterung lohnt sich hauptsaechlich fuer patentgeschuetzte vegetative Sorten.

### Schaedlinge und Krankheiten

- **Blattlaeuse (Myzus persicae, Aphis fabae):** Haeufigster Schaedling. Kaliseife-Spritzung (2% Loesung)
- **Weisse Fliege (Trialeurodes vaporariorum):** Gelbtafeln + Encarsia formosa als Nuetzling
- **Thripse (Frankliniella occidentalis):** Silbrig-graue Flecken auf Bluetenblaettern. Blautafeln
- **Spinnmilbe (Tetranychus urticae):** Bei Trockenheit/Hitze. Starker Wasserstrahl auf Blattunterseiten
- **Botrytis (Grauschimmel):** Besonders Grandiflora-Typen bei feuchter Witterung. Gute Luftzirkulation!
- **Pythium-Wurzelfaeule:** Ueberwasserung, schlechte Drainage. Substrat gut drainieren
- **Echter Mehltau:** Weisser Belag. Trockene warme Tage + kuehle Naechte
- **Petunia Vein Clearing Virus (PVCV):** Viruserkrankung, keine Heilung. Befallene Pflanzen entfernen

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Petunie \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Garten-Petunien (Petunia \u00d7 hybrida) mit Indoor-Voranzucht ab Februar. Plagron Terra-Linie mit 4 Produkten. Mittelzehrer bis Starkzehrer mit kritischem Eisenbedarf. Dauerbl\u00fcte Mai\u2013Oktober. Annuell in Mitteleuropa. Balkonkasten, Ampel und Beet.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["petunie", "petunia", "solanaceae", "plagron", "terra", "erde", "outdoor", "balkon", "ampel", "mittelzehrer", "starkzehrer", "zierpflanze", "dauerbl\u00fcher"],
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
  "notes": "Aussaat bei 22\u201324\u00b0C. Lichtkeimer \u2014 Samen nur andr\u00fccken, nicht bedecken. Abdeckung (Dome) f\u00fcr 80\u201395% Luftfeuchte. Staubsamen extrem fein. Keimdauer 7\u201314 Tage.",
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
      "notes": "Kein D\u00fcnger. Leichtes Spr\u00fchen, Substrat gleichm\u00e4\u00dfig feucht.",
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
  "calcium_ppm": 60,
  "magnesium_ppm": 25,
  "notes": "Halbe Dosis Terra Grow (2.5 ml/L). Pikieren nach 1. Laubblattpaar in 7\u20139 cm T\u00f6pfe. K\u00fchle N\u00e4chte 15\u201318\u00b0C f\u00fcr kompakten Wuchs. Alle 14 Tage d\u00fcngen. Pure Zym und Sugar Royal erst ab VEGETATIVE.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow halbe Dosis. Schwach starten, Jungpflanzen nicht \u00fcberd\u00fcngen.",
      "target_ec_ms": 0.6,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.5, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
  "calcium_ppm": 100,
  "magnesium_ppm": 40,
  "notes": "Volle Dosis Terra Grow (5 ml/L) + Pure Zym + Sugar Royal. Umtopfen in Endgef\u00e4\u00dfe. Abh\u00e4rtung ab Mitte April, Auspflanzen nach Eisheiligen (Mitte Mai). Pflanzabstand 25\u201340 cm. Alle 7\u201314 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + Pure Zym + Sugar Royal. Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.8,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.4}
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
  "week_end": 36,
  "is_recurring": false,
  "npk_ratio": [1.0, 2.0, 3.0],
  "calcium_ppm": 120,
  "magnesium_ppm": 50,
  "notes": "Terra Bloom 5 ml/L + Pure Zym + Sugar Royal. K-betonte D\u00fcngung f\u00fcr Bl\u00fctenansatz und Farbintensit\u00e4t. W\u00f6chentlich d\u00fcngen! Eisenchelat bei Chlorose supplementieren. Mitte Juli R\u00fcckschnitt um 1/3 f\u00fcr zweite Bl\u00fctenwelle. Ab Oktober auf 3 ml/L reduzieren.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Pure Zym + Sugar Royal. Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen. pH unter 6.2 halten (Eisenverf\u00fcgbarkeit)!",
      "target_ec_ms": 0.9,
      "target_ph": 5.8,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": false}
      ],
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
  "week_start": 37,
  "week_end": 40,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Seneszenz nach erstem Frost. Keine D\u00fcngung. Pflanze entfernen. Optional: Stecklinge f\u00fcr \u00dcberwinterung im September abnehmen (vegetative Sorten). Gef\u00e4\u00dfe reinigen und einlagern.",
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
      "label": "Nur Wasser (Seneszenz)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Nur bei Trockenheit gie\u00dfen.",
      "target_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
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
| Fertilizer: Sugar Royal | `spec/ref/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Petunia x hybrida | `spec/ref/plant-info/petunia_x_hybrida.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Ungiftig:** Petunien sind fuer Katzen, Hunde und Kinder unbedenklich (ASPCA safe)
- Klebrige Trichome der Blaetter koennen bei sensitiven Personen leichte Hautreizungen verursachen (mechanisch, nicht toxisch)
- Keine besonderen Haustier- oder Kinderwarnungen erforderlich

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- Sugar Royal kann bei Verschuettung stark riechen (Aminosaeuren)

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
4. Plagron Sugar Royal Produktdaten: `spec/ref/products/plagron_sugar_royal.md`
5. Petunia x hybrida Pflanzendaten: `spec/ref/plant-info/petunia_x_hybrida.md`
6. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
7. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
