# REQ-015-A Aussaatkalender -- Berechnungsregeln

> **Bezug:** REQ-015 Kalenderansicht, §3.8 Aussaatkalender-Modus
> **Version:** 1.2
> **Erstellt:** 2026-03-06
> **Status:** Entwurf

---

## 1. Zweck

Dieses Dokument praezisiert die Berechnungsregeln fuer die Zeitbalken im Aussaatkalender. Es klaert Prioritaeten, Randfaelle und das Zusammenspiel der Stammdaten-Felder, die in REQ-015 §3.8 referenziert werden.

---

## 2. Phasen-Uebersicht

Der Aussaatkalender zeigt pro Pflanze bis zu **vier Phasen** als horizontale Zeitbalken:

| Phase | Farbe | Hex | Datenquelle (REQ-001 Species) | Anzeige bei |
|-------|-------|-----|-------------------------------|-------------|
| Voranzucht (Indoor) | Gelb | `#FDD835` | `sowing_indoor_weeks_before_last_frost` | Alle mit Voranzucht-Daten |
| Direktsaat / Auspflanzen | Gruen | `#66BB6A` | `direct_sow_months` ODER `sowing_outdoor_after_last_frost_days` | Alle mit Aussaat-Daten |
| Wachstum | Blau | `#42A5F5` | *Berechnet* (Luecke zwischen Auspflanzen-Ende und Ernte/Bluete-Beginn) | Wenn Luecke > 1 Tag |
| Ernte | Orange | `#FFA726` | `harvest_months` | Nutzpflanzen (`allows_harvest: true`) |
| Bluete | Pink | `#EC407A` | `bloom_months` | Zierpflanzen (`allows_harvest: false` ODER `traits: ['ornamental']`) |

---

## 3. Berechnungsregeln je Phase

### 3.1 Voranzucht (Indoor Sowing)

**Datenquelle:** `species.sowing_indoor_weeks_before_last_frost` (Integer, Wochen)

**Berechnung:**
- `start_date = letzter_frost - (wochen * 7 Tage)`
- `end_date = letzter_frost - 1 Tag`
- Wenn `start_date` vor dem 1. Januar des Bezugsjahres liegt: auf 1. Januar kappen

**Bedingung:** Nur anzeigen wenn `sowing_indoor_weeks_before_last_frost` gesetzt ist (nicht `None`).

**Beispiel:** Paprika, 10 Wochen Voranzucht, letzter Frost 15. Mai
- Start: 6. Maerz, Ende: 14. Mai

### 3.2 Direktsaat / Auspflanzen (Outdoor Planting)

**Zwei Datenquellen -- eine hat Vorrang:**

| Prioritaet | Feld | Beschreibung | Balken-Berechnung |
|------------|------|-------------|-------------------|
| **1 (bevorzugt)** | `direct_sow_months` | Liste von Monaten (z.B. `[3, 4, 5, 6]`) | Pro zusammenhaengende Periode ein Balken: 1. des Startmonats bis letzter Tag des Endmonats |
| **2 (Fallback)** | `sowing_outdoor_after_last_frost_days` | Tage nach letztem Frost (z.B. `0`) | `start = letzter_frost + tage`, Dauer: 14 Tage |

**Regel: Wenn `direct_sow_months` vorhanden ist, wird `sowing_outdoor_after_last_frost_days` IGNORIERT.**

Begruendung: `direct_sow_months` liefert den praeziseren, monatsgenauen Aussaatzeitraum direkt aus den Stammdaten. `sowing_outdoor_after_last_frost_days` ist ein berechneter Naeherungswert relativ zum Frosttermin und dient nur als Fallback fuer Pflanzen ohne explizite Direktsaat-Monate.

**Nicht-zusammenhaengende Monate erzeugen mehrere Zeilen:**
Siehe §6 (Mehrere Aussaat-Perioden).

**Clipping bei Voranzucht-Ueberlappung:**
Wenn `direct_sow_months` zeitlich vor dem Ende der Voranzucht beginnen (z.B. Petersilie: Voranzucht Mitte Maerz bis Mitte Mai, Direktsaat ab Maerz), wird der Auspflanzen-Balken auf den Tag nach Ende der Voranzucht gekuerzt. Dadurch bleibt die chronologische Reihenfolge (§5.1) erhalten. Wenn eine `direct_sow_months`-Periode vollstaendig von der Voranzucht abgedeckt wird, entfaellt der Auspflanzen-Balken fuer diese Periode.

**Eisheiligen-Verzoegerung (nur bei Fallback-Berechnung):**
- Wenn `frost_sensitivity == 'sensitive'` UND der berechnete Auspflanz-Start vor den Eisheiligen liegt:
  `start = max(start, eisheilige_date + 1 Tag)`
- Gilt nur fuer `sowing_outdoor_after_last_frost_days`, NICHT fuer `direct_sow_months` (dort ist die Frostempfindlichkeit bereits in den Stammdaten beruecksichtigt)

### 3.3 Wachstum (Growth)

**Keine eigene Datenquelle -- rein berechnet.**

Die Wachstumsphase fuellt die zeitliche Luecke zwischen dem Ende der Aussaat/Pflanzung und dem Beginn der Ernte/Bluete.

**Berechnung:**
1. Bestimme `source_end` = spaetestes Ende aller Auspflanzen-Balken. Wenn keine Auspflanzen-Balken existieren, nimm das Ende der Voranzucht-Balken als Fallback.
2. Bestimme `target_start` = fruehester Beginn aller Ernte- oder Bluete-Balken, die NACH `source_end` liegen.
3. `growth_start = source_end + 1 Tag`
4. `growth_end = target_start - 1 Tag`
5. Nur anzeigen wenn `growth_start < growth_end` (Luecke mindestens 2 Tage)

**Kein Wachstums-Balken wenn:**
- Auspflanzen und Ernte direkt aneinander grenzen oder ueberlappen
- Keine Auspflanzen-Daten UND keine Voranzucht-Daten vorhanden
- Keine Ernte-/Bluete-Daten vorhanden

**Bei mehreren Aussaat-Perioden (§6):** Jede Periode berechnet ihren eigenen Wachstums-Balken unabhaengig.

**Jahresuebergreifende Perioden (Herbstaussaat → Sommerernte):**
Wenn die Ernte-/Bluete-Monate chronologisch VOR den Aussaat-Monaten im Kalender liegen (z.B. Winterweizen: Aussaat Okt/Nov, Ernte Jul/Aug), handelt es sich um eine jahresuebergreifende Kultur. Die Ernte gehoert zum Anbauzyklus des Vorjahres. In diesem Fall:
- Ein Wachstums-Balken wird vom **1. Januar bis zum Tag vor der Ernte** eingefuegt
- Die Ernte-/Bluete-Balken werden normal dargestellt
- Die Aussaat-Balken (Herbst) starten einen neuen Zyklus fuer das Folgejahr

Beispiel Winterweizen im Kalender 2026:
```
🔵🔵🔵🔵🔵🔵🟠🟠··🟢🟢··
Jan-Jun: Wachstum (vom Vorjahres-Zyklus)
Jul-Aug: Ernte
Okt-Nov: Aussaat (fuer Folgejahr-Ernte)
```

### 3.4 Ernte (Harvest)

**Datenquelle:** `species.harvest_months` (Liste von Monaten, z.B. `[7, 8, 9, 10]`)

**Berechnung:** Pro zusammenhaengende Periode ein Balken:
- `start_date = 1. des Startmonats`
- `end_date = letzter Tag des Endmonats`

**Nicht-zusammenhaengende Monate:** Analog zu `direct_sow_months` werden getrennte Balken erzeugt.

**Jahresuebergreifende Ernte (Wrap-around):** Manche Kulturen haben Erntemonate, die ueber die Jahresgrenze gehen (z.B. Porree `harvest_months = [8, 9, 10, 11, 12, 1, 2, 3]`). Die Funktion `_split_into_periods()` erkennt dies automatisch: Wenn sowohl Monat 1 als auch Monat 12 in der Liste enthalten sind und beide zu zusammenhaengenden Gruppen gehoeren, werden sie zu einer einzigen Wrap-around-Periode zusammengefuegt (z.B. `(8, 3)` statt `(1, 3)` und `(8, 12)` getrennt).

Fuer die Darstellung im Jahreskalender wird ein Wrap-around-Balken am 31. Dezember abgeschnitten:
- `start_date = 1. des Startmonats` (z.B. 1. August)
- `end_date = 31. Dezember` (Jahresende)
- Die Fortsetzung der Ernte (z.B. Januar-Maerz) erscheint im Kalender des Folgejahres.

**Bedingung:** Nur bei Nutzpflanzen (`allows_harvest: true`). Wenn `allows_harvest: false`, wird stattdessen `bloom_months` fuer den Bluete-Balken verwendet (siehe 3.5).

### 3.5 Bluete (Flowering)

**Datenquelle:** `species.bloom_months` (Liste von Monaten, z.B. `[7, 8, 9, 10]`)

**Berechnung:** Identisch zu Ernte (3.4), aber mit Phase `flowering` und Farbe Pink.

**Bedingung:** Nur bei Zierpflanzen, erkannt durch:
- `allows_harvest: false` ODER
- `traits` enthaelt `'ornamental'`

**Bluehpause:** Nicht-zusammenhaengende Monate (z.B. Stiefmuetterchen `bloom_months = [3, 4, 5, 6, 9, 10]`) erzeugen mehrere Bluete-Balken mit sichtbarer Luecke dazwischen.

---

## 4. Frosttermin-Konfiguration

Die Frosttermine werden auf Site-Level konfiguriert (REQ-002) und vom Aussaatkalender gelesen:

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|-------------|
| `last_frost_date_avg` | `date` | 15. Mai | Durchschnittlicher letzter Frost |
| `first_frost_date_avg` | `date` | 5. Oktober | Durchschnittlicher erster Frost (Herbst) |
| `eisheilige_date` | `date` | 15. Mai | Eisheilige -- vertikale Markierung im Kalender |

**Eisheiligen-Linie:** Wird als vertikale gestrichelte Linie (rot) im Kalender dargestellt. Rein visuell -- beeinflusst die Balken-Berechnung nur bei `sowing_outdoor_after_last_frost_days` mit `frost_sensitivity == 'sensitive'`.

**Heute-Markierung:** Vertikale Hervorhebung der aktuellen Kalenderwoche (nur wenn das angezeigte Jahr dem aktuellen Jahr entspricht).

---

## 5. Reihenfolge und Lueckenfreiheit der Balken

### 5.1 Chronologische Reihenfolge (links nach rechts)

Die Balken einer Pflanze muessen in chronologischer Reihenfolge erscheinen:

```
Voranzucht (gelb) -> Auspflanzen (gruen) -> Wachstum (blau) -> Ernte (orange) / Bluete (pink)
```

### 5.2 Lueckenfreier Ablauf (Kernregel)

**Die Phasen bilden eine zusammenhaengende Zeitlinie ohne Luecken.** Zwischen aufeinanderfolgenden Phasen darf kein leerer Zeitraum entstehen:

- **Voranzucht → Auspflanzen:** Der Auspflanzen-Balken beginnt am Tag nach dem Ende der Voranzucht, oder die Balken ueberlappen sich (bei `direct_sow_months` die schon waehrend der Voranzucht beginnen).
- **Auspflanzen → Wachstum:** Der Wachstums-Balken schliesst nahtlos an das Ende des Auspflanzen-Balkens an (`growth_start = source_end + 1 Tag`).
- **Wachstum → Ernte/Bluete:** Der Wachstums-Balken endet am Tag vor dem Ernte-/Bluete-Beginn (`growth_end = target_start - 1 Tag`).
- **Auspflanzen → Ernte (ohne Wachstum):** Wenn Auspflanzen und Ernte direkt aneinander grenzen oder ueberlappen, entfaellt der Wachstums-Balken — die Phasen schliessen trotzdem lueckenlos aneinander.

> **Prinzip:** Der Wachstums-Balken existiert *ausschliesslich* als Lueckenfueller. Sobald es eine zeitliche Luecke zwischen Auspflanzen-Ende und Ernte-/Bluete-Beginn gibt, wird sie durch den Wachstums-Balken geschlossen. Es gibt keine Phase, in der "nichts passiert".

### 5.3 Ueberlappungen

Wenn Voranzucht und Direktsaat-Monate sich zeitlich ueberlappen (z.B. Voranzucht endet Mitte Mai, Direktsaat beginnt ab Mai), ueberlappt der gruene Balken den gelben. Das Frontend zeigt pro Wochenzelle nur den ersten passenden Balken (`find`-Semantik) -- die Reihenfolge der Balken im Array bestimmt die Prioritaet bei Ueberlappungen.

**Balken-Array-Reihenfolge (Prioritaet bei Ueberlappung):**
1. Voranzucht (indoor_sowing)
2. Auspflanzen (outdoor_planting)
3. Ernte / Bluete (harvest / flowering)
4. Wachstum (growth)

---

## 6. Mehrere Anbauzeitraeume (GrowingPeriod-Datenmodell)

### 6.1 Grundprinzip

Manche Arten koennen zu **mehreren, getrennten Zeitpunkten im Jahr** angebaut werden. Jeder Anbauzeitraum ist eine **eigenstaendige, in sich abgeschlossene Zeitlinie** von Voranzucht bis Ernte/Bluete.

Das Datenmodell unterstuetzt dies ueber eine **explizite Liste von `GrowingPeriod`-Objekten** pro Species:

```python
class GrowingPeriod(BaseModel):
    label: str = ""                                          # z.B. "Sommerweizen", "Winterporree"
    sowing_indoor_weeks_before_last_frost: int | None = None
    sowing_outdoor_after_last_frost_days: int | None = None
    direct_sow_months: list[int] = []
    harvest_months: list[int] = []
    bloom_months: list[int] = []
```

Jede `GrowingPeriod` enthaelt **alle Felder fuer eine vollstaendige Zeitlinie** (Voranzucht, Aussaat, Ernte/Bluete). Dadurch kann jede Periode unabhaengig ihre eigenen Balken berechnen.

| Typ | Beispiel | GrowingPeriods |
|-----|---------|----------------|
| Sommer-/Winteraussaat | Weizen | Period 1: `direct_sow=[3,4], harvest=[7,8]` (Sommerweizen), Period 2: `direct_sow=[10,11], harvest=[6,7]` (Winterweizen, jahresuebergreifend) |
| Sommer-/Winterernte | Porree | Period 1: `direct_sow=[2,3], harvest=[8,9,10,11]` (Sommerporree), Period 2: `direct_sow=[5,6], harvest=[12,1,2,3]` (Winterporree) |
| Staffelsaat (Sukzession) | Radieschen | Eine einzige Period: `direct_sow=[3..9], harvest=[4..10]` (zusammenhaengend) |

### 6.2 Abwaertskompatibilitaet (Legacy-Felder)

Species, die **keine expliziten `growing_periods`** definiert haben, verwenden weiterhin die flachen Felder auf Species-Ebene (`sowing_indoor_weeks_before_last_frost`, `direct_sow_months`, `harvest_months`, etc.). Die Engine konvertiert diese automatisch in eine einzelne `GrowingPeriod`:

```
Species ohne growing_periods:
  direct_sow_months = [3, 4, 5]
  harvest_months = [7, 8, 9]
  → Automatisch: growing_periods = [GrowingPeriod(direct_sow_months=[3,4,5], harvest_months=[7,8,9])]
```

**Regel:** Wenn `growing_periods` explizit gesetzt ist, werden die flachen Felder auf Species-Ebene **ignoriert**.

### 6.3 Darstellung als separate Zeilen

Jede `GrowingPeriod` erzeugt eine **eigene Kalender-Zeile**:

- Jede Zeile berechnet ihre Balken unabhaengig (eigener Voranzucht-, Auspflanzen-, Wachstums- und Ernte-/Bluete-Balken)
- Jede Zeile bekommt ein **Label-Suffix** im Anzeigenamen:
  - Bevorzugt: `period.label` (z.B. "Sommerweizen", "Winterporree")
  - Fallback: Automatischer Saison-Name basierend auf dem fruehesten Aussaat-Monat:
    - Startmonat 1--4: `(spring)`
    - Startmonat 5--8: `(summer)`
    - Startmonat 9--12: `(autumn)`
- Der `species_key` wird mit `_{index}` suffigiert (z.B. `weizen_0`, `weizen_1`)
- Bei **einer einzigen Periode** wird kein Suffix angezeigt (Normalfall)

### 6.4 Periodenspezifische Ernte/Bluete

Im Gegensatz zum alten Modell (§6.4 alt: `harvest_months` auf Species-Ebene fuer alle Perioden) hat jetzt **jede GrowingPeriod ihre eigenen `harvest_months`/`bloom_months`**:

- Sommerporree: `harvest_months = [8, 9, 10, 11]` — Ernte Aug–Nov
- Winterporree: `harvest_months = [12, 1, 2, 3]` — Ernte Dez–Mär (Wrap-around, §3.4)

Perioden ohne `harvest_months`/`bloom_months` (z.B. Winterweizen, Ernte erst im Folgejahr) zeigen nur Auspflanzen- und ggf. Wachstums-Balken.

### 6.5 Voranzucht pro Periode

Jede `GrowingPeriod` kann individuell `sowing_indoor_weeks_before_last_frost` setzen. Typischerweise hat nur die Fruehjahrs-Periode eine Voranzucht; Herbst-/Winterperioden verwenden Direktsaat.

### 6.6 Beispiele

**Weizen** (2 explizite Perioden):
```
Period 1: label="Sommerweizen", direct_sow=[3,4], harvest=[7,8]
Period 2: label="Winterweizen", direct_sow=[10,11], harvest=[6,7]

Weizen (Winterweizen)  🔵🔵🔵🔵🔵🟠🟠···🟢🟢··
                       Jan-----Mai Jun-Jul   Okt-Nov
Weizen (Sommerweizen)  ···🟢🟢🔵🔵🟠🟠·········
                          Mär-Apr Mai-Jun Jul-Aug
```
Winterweizen ist jahresuebergreifend: Die Ernte Jun/Jul gehoert zum Vorjahres-Zyklus (Aussaat Okt/Nov des Vorjahres). Die Aussaat Okt/Nov startet den naechsten Zyklus. Der Wachstums-Balken wird ab 1. Januar eingefuegt (§3.3).

**Porree** (2 explizite Perioden mit periodenspezifischer Ernte):
```
Period 1: label="Sommerporree", direct_sow=[2,3], harvest=[8,9,10,11]
Period 2: label="Winterporree", direct_sow=[5,6], harvest=[12,1,2,3]

Porree (Sommerporree)   ··🟢🟢🔵🔵🔵🔵🔵🟠🟠🟠🟠···········
Porree (Winterporree)   ·········🟢🟢🔵🔵🔵🔵🔵🔵🟠🟠🟠🟠··
```
(Winterporree Wrap-around: Ernte-Balken endet am 31. Dez, Fortsetzung Jan-Mär im Folgejahr)

**Radieschen** (1 Periode, zusammenhaengend):
```
Period 1: direct_sow=[3,4,5,6,7,8,9], harvest=[4,5,6,7,8,9,10]

Radieschen  ···🟢🟢🟢🟢🟢🟢🟢🟠🟠🟠🟠🟠🟠🟠···········
```
(Eine Periode -- eine Zeile, kein Suffix)

---

## 7. Pflanzen ohne Aussaat-Daten

Pflanzen, bei denen KEINES der folgenden Felder gesetzt ist, erscheinen NICHT im Aussaatkalender:

- `sowing_indoor_weeks_before_last_frost`
- `sowing_outdoor_after_last_frost_days`
- `direct_sow_months`
- `harvest_months`
- `bloom_months`

---

## 8. Zusammenfassung der Stammdaten-Felder (REQ-001 Species)

### 8.1 GrowingPeriod (bevorzugt)

| Feld | Typ | Beispiel | Wirkung im Aussaatkalender |
|------|-----|---------|---------------------------|
| `growing_periods` | `list[GrowingPeriod]` | siehe §6 | Eine Kalender-Zeile pro Periode |
| `growing_periods[].label` | `str` | `"Sommerweizen"` | Suffix im Anzeigenamen |
| `growing_periods[].sowing_indoor_weeks_before_last_frost` | `int \| None` | `10` | Gelber Voranzucht-Balken (pro Periode) |
| `growing_periods[].sowing_outdoor_after_last_frost_days` | `int \| None` | `0` | Gruener Auspflanzen-Balken (Fallback, pro Periode) |
| `growing_periods[].direct_sow_months` | `list[int]` | `[3, 4, 5, 6]` | Gruener Direktsaat-Balken (bevorzugt, pro Periode) |
| `growing_periods[].harvest_months` | `list[int]` | `[7, 8, 9, 10]` | Oranger Ernte-Balken (pro Periode) |
| `growing_periods[].bloom_months` | `list[int]` | `[6, 7, 8, 9]` | Pinker Bluete-Balken (pro Periode, Zierpflanzen) |

### 8.2 Legacy-Felder (Abwaertskompatibilitaet)

Wenn `growing_periods` leer ist, werden die folgenden Species-Level-Felder automatisch in eine einzelne `GrowingPeriod` konvertiert (siehe §6.2):

| Feld | Typ | Beispiel | Wirkung im Aussaatkalender |
|------|-----|---------|---------------------------|
| `sowing_indoor_weeks_before_last_frost` | `int \| None` | `10` | Gelber Voranzucht-Balken |
| `sowing_outdoor_after_last_frost_days` | `int \| None` | `0` | Gruener Auspflanzen-Balken (Fallback) |
| `direct_sow_months` | `list[int]` | `[3, 4, 5, 6]` | Gruener Direktsaat-Balken (bevorzugt) |
| `harvest_months` | `list[int]` | `[7, 8, 9, 10]` | Oranger Ernte-Balken |
| `bloom_months` | `list[int]` | `[6, 7, 8, 9]` | Pinker Bluete-Balken (Zierpflanzen) |

### 8.3 Species-Level-Felder (unabhaengig von Perioden)

| Feld | Typ | Beispiel | Wirkung im Aussaatkalender |
|------|-----|---------|---------------------------|
| `allows_harvest` | `bool` | `true` | Entscheidet: Ernte vs. Bluete |
| `frost_sensitivity` | `FrostTolerance` | `sensitive` | Eisheiligen-Verzoegerung (nur Fallback) |
| `traits` | `list[str]` | `['ornamental']` | Erkennung Zierpflanze |

---

## 9. Akzeptanzkriterien

### Balken-Berechnung

- [ ] Keine doppelten Auspflanzen-Balken: Wenn `direct_sow_months` vorhanden, wird `sowing_outdoor_after_last_frost_days` ignoriert
- [ ] Wachstums-Balken fuellt Luecke zwischen Auspflanzen-Ende und Ernte/Bluete-Beginn
- [ ] Kein Wachstums-Balken wenn keine Luecke existiert (Auspflanzen und Ernte grenzen an oder ueberlappen)
- [ ] Voranzucht-Balken korrekt berechnet aus `sowing_indoor_weeks_before_last_frost` und Frosttermin
- [ ] Auspflanzen-Balken wird auf nach Voranzucht-Ende gekuerzt wenn `direct_sow_months` vor Voranzucht-Ende beginnen
- [ ] Eisheiligen-Verzoegerung nur bei Fallback-Berechnung (`sowing_outdoor_after_last_frost_days`) fuer frostempfindliche Pflanzen
- [ ] Balken-Reihenfolge ist chronologisch (Voranzucht -> Auspflanzen -> Wachstum -> Ernte/Bluete)
- [ ] Phasen bilden eine zusammenhaengende Zeitlinie ohne Luecken — der Wachstums-Balken schliesst jede Luecke zwischen Auspflanzen-Ende und Ernte-/Bluete-Beginn
- [ ] Jahresuebergreifende `harvest_months` (z.B. Aug-Mär) erzeugen einen Balken bis 31. Dez (kein doppelter Jan-Mär-Balken im selben Jahr)
- [ ] Pflanzen ohne Aussaat-Daten erscheinen nicht im Kalender

### Mehrere Anbauzeitraeume (GrowingPeriod)

- [ ] Jede `GrowingPeriod` erzeugt eine eigene Kalender-Zeile mit eigenstaendiger Zeitlinie
- [ ] Perioden-Label wird als Suffix angezeigt (bevorzugt `period.label`, Fallback: Saison-Name)
- [ ] Bei einer einzigen Periode wird kein Suffix angezeigt
- [ ] Jede Periode berechnet eigene Voranzucht-, Auspflanzen-, Wachstums- und Ernte-/Bluete-Balken unabhaengig
- [ ] Periodenspezifische `harvest_months`/`bloom_months` werden korrekt berechnet (z.B. Sommerporree vs. Winterporree)
- [ ] Species ohne explizite `growing_periods` werden ueber Legacy-Felder automatisch in eine einzelne Periode konvertiert
- [ ] `species_key` wird mit `_{index}` suffigiert bei mehreren Perioden

### Zierpflanzen

- [ ] Zierpflanzen zeigen Bluete-Balken (pink) statt Ernte-Balken (orange)
- [ ] Bluehpause bei Zierpflanzen sichtbar (getrennte Bluete-Balken bei nicht-zusammenhaengenden `bloom_months`)
- [ ] Nicht-zusammenhaengende `harvest_months` oder `bloom_months` erzeugen separate Balken
