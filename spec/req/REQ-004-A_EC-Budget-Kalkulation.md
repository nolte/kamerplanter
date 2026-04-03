# Spezifikation: REQ-004-A — EC-Budget-Kalkulation

```yaml
ID: REQ-004-A
Titel: EC-Budget-Kalkulation — Wassermischung und Dünger-Dosierung
Kategorie: Bewässerung & Düngung
Bezug: REQ-004 (Dünge-Logik), REQ-002 (Standort/WaterSource), REQ-014 (Tankmanagement)
Technologie: Python, Pydantic, ArangoDB
Status: Entwurf
Version: 1.1 (Agrarbiologie-Review eingearbeitet)
```

<!-- Quelle: Agrarbiologie-Review spec/analysis/agrobiology-review-REQ-004-A.md -->

## 1. Überblick

Dieses Dokument formalisiert die mathematische Berechnungspipeline, die den gesamten EC-Fluss von der Wasseraufbereitung bis zur fertigen Nährlösung beschreibt. Es konsolidiert die in REQ-004, REQ-002 und REQ-014 verteilten EC-bezogenen Anforderungen in ein einheitliches Berechnungsmodell.

**Kernproblem:** Ein Gärtner hat Leitungswasser mit bekanntem EC-Wert und möchte durch Beimischung von Osmosewasser einen definierten Basis-EC erreichen. Dieser Basis-EC bestimmt das verfügbare EC-Budget für die Düngerdosierung. Die ausgewählten Dünger müssen so dosiert werden, dass die EC-Obergrenze der aktuellen Wachstumsphase nicht überschritten wird.

**Berechnungspipeline (3 Stufen):**

```
┌─────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│ STUFE 1                 │     │ STUFE 2                  │     │ STUFE 3                  │
│ Wassermischung          │ ──▶ │ EC-Budget-Berechnung     │ ──▶ │ Dünger-Dosierung         │
│                         │     │                          │     │                          │
│ EC_tap + EC_ro → EC_mix │     │ EC_target - EC_mix       │     │ EC_net → ml/L pro Dünger │
│                         │     │ = EC_net                 │     │ Σ(EC_i) ≤ EC_net         │
└─────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

---

## 2. Definitionen und Symbole

| Symbol | Einheit | Beschreibung |
|--------|---------|-------------|
| `EC_tap` | mS/cm | EC-Wert des Leitungswassers (aus `TapWaterProfile.ec_ms`, REQ-002) |
| `EC_ro` | mS/cm | EC-Wert des Osmosewassers (aus `RoWaterProfile.ec_ms`, REQ-002; typisch 0.02–0.05) |
| `EC_mix` | mS/cm | EC-Wert des gemischten Ausgangswassers (Ergebnis Stufe 1) |
| `EC_target` | mS/cm | Ziel-EC der fertigen Nährlösung inkl. Dünger (aus `DeliveryChannel.target_ec_ms` oder `NutrientPlanPhaseEntry`) |
| `EC_net` | mS/cm | Verfügbares EC-Budget für Düngerdosierung (= `EC_target − EC_mix`) |
| `EC_max` | mS/cm | Absolute EC-Obergrenze der aktuellen Phase/Substrat-Kombination |
| `r` | % (0–100) | Osmose-Anteil im Mischwasser (`water_mix_ratio_ro_percent`) |
| `ec_i` | mS/cm pro ml/L | EC-Beitrag des Düngers i pro ml/L (`Fertilizer.ec_contribution_per_ml`) |
| `d_i` | ml/L | Dosierung des Düngers i in ml pro Liter Wasser |
| `V` | Liter | Zielvolumen der Nährlösung |
| `EC_ph` | mS/cm | Geschätzter EC-Beitrag durch pH-Korrektur (typisch 0.02–0.05 mS) |

---

## 3. Stufe 1 — Wassermischung (Ziel-EC des Ausgangswassers)

### 3.1 Problemstellung

Ein Gärtner hat Leitungswasser mit einem bekannten EC-Wert (`EC_tap`) und eine Osmoseanlage, die nahezu reines Wasser produziert (`EC_ro`). Durch Mischung beider Wasserquellen soll ein gewünschter Basis-EC (`EC_mix`) erreicht werden, der als Ausgangspunkt für die Düngerdosierung dient.

### 3.2 Vorwärtsberechnung — EC des Mischwassers

**Gegeben:** `EC_tap`, `EC_ro`, Osmose-Anteil `r` (0–100%)

**Gesucht:** `EC_mix`

**Formel:**

```
EC_mix = EC_ro × (r / 100) + EC_tap × (1 − r / 100)
```

**Beispiel:**
- Leitungswasser: `EC_tap = 0.50 mS/cm`
- Osmosewasser: `EC_ro = 0.02 mS/cm`
- Osmose-Anteil: `r = 70%`

```
EC_mix = 0.02 × 0.7 + 0.50 × 0.3
       = 0.014 + 0.15
       = 0.164 mS/cm
```

### 3.3 Rückwärtsberechnung — Benötigter Osmose-Anteil

**Gegeben:** `EC_tap`, `EC_ro`, gewünschter `EC_mix`

**Gesucht:** Osmose-Anteil `r`

**Formel (umgestellte Mischungsgleichung):**

```
r = (EC_tap − EC_mix) / (EC_tap − EC_ro) × 100
```

**Randbedingungen:**
- `EC_ro < EC_mix ≤ EC_tap` (sonst ist die Mischung nicht möglich)
- `0 ≤ r ≤ 100` (Ergebnis muss im gültigen Bereich liegen)
- Falls `EC_tap ≤ EC_ro`: Kein Osmose-Wasser nötig, Leitungswasser ist bereits reiner → `r = 0`
- Falls `EC_mix < EC_ro`: Ziel-EC unerreichbar, selbst 100% Osmose reicht nicht → Fehler/Warnung

**Beispiel:**
- Leitungswasser: `EC_tap = 0.80 mS/cm`
- Osmosewasser: `EC_ro = 0.02 mS/cm`
- Gewünschter Basis-EC: `EC_mix = 0.20 mS/cm`

```
r = (0.80 − 0.20) / (0.80 − 0.02) × 100
  = 0.60 / 0.78 × 100
  = 76.9%
```

→ **76.9% Osmosewasser, 23.1% Leitungswasser** ergibt einen Basis-EC von 0.20 mS/cm.

### 3.4 Volumenberechnung

Für ein Zielvolumen `V` Liter:

```
V_ro  = V × (r / 100)          // Liter Osmosewasser
V_tap = V × (1 − r / 100)      // Liter Leitungswasser
```

**Beispiel:** 50 Liter Nährlösung mit `r = 76.9%`:
```
V_ro  = 50 × 0.769 = 38.45 L Osmosewasser
V_tap = 50 × 0.231 = 11.55 L Leitungswasser
```

### 3.5 Analoge Berechnung für weitere Wasserparameter

Die gleiche lineare Mischungsformel gilt für alle **Mineralien-Parameter** des `TapWaterProfile` (REQ-002):

```
Parameter_mix = Parameter_ro × (r / 100) + Parameter_tap × (1 − r / 100)
```

| Parameter | RO-Default | Mischung | Bedeutung |
|-----------|-----------|----------|-----------|
| `alkalinity_ppm` | 0 | Linear | Karbonathärte / Pufferkapazität |
| `calcium_ppm` | 0 | Linear | Calcium-Gehalt → relevant für CalMag-Korrektur |
| `magnesium_ppm` | 0 | Linear | Magnesium-Gehalt → relevant für CalMag-Korrektur |
| `chlorine_ppm` | 0 | Linear | Chlor → relevant für biologische Dünger |
| `chloramine_ppm` | 0 | Linear | Chloramin → Aktivkohle nötig |
| `gh_ppm` | 0 | Linear | Gesamthärte |

**Wichtig:** Da RO-Wasser für alle Mineralien-Parameter ≈ 0 gilt, vereinfacht sich die Formel zu:

```
Parameter_mix ≈ Parameter_tap × (1 − r / 100)
```

Dies bedeutet: Bei 70% Osmose-Anteil enthält das Mischwasser nur noch ~30% des Calcium-/Magnesium-Gehalts des Leitungswassers → CalMag-Supplement wird nötig (siehe §3.6).

### 3.5a pH-Mischung — Logarithmische Berechnung

<!-- Quelle: Agrarbiologie-Review F-002 -->

**pH ist eine logarithmische Skala und darf NICHT linear gemischt werden.** Die lineare Näherung (`pH_mix = pH_ro × r + pH_tap × (1-r)`) erzeugt bei typischen pH-Unterschieden zwischen RO-Wasser (pH 6.5) und Leitungswasser (pH 8.2) Fehler von bis zu 0.5 pH-Einheiten — weit außerhalb der Mess-Toleranz von ±0.2 pH.

**Korrekte Formel:**

```
[H⁺]_tap = 10^(−pH_tap)
[H⁺]_ro  = 10^(−pH_ro)
[H⁺]_mix = [H⁺]_ro × (r / 100) + [H⁺]_tap × (1 − r / 100)

pH_mix = −log₁₀([H⁺]_mix)
```

**Rechenbeispiel:** 50% RO (pH 6.5) + 50% Leitungswasser (pH 8.2):
- Linear (FALSCH): `pH = (6.5 + 8.2) / 2 = 7.35`
- Logarithmisch (KORREKT): `[H⁺]_mix = (3.16×10⁻⁷ + 6.31×10⁻⁹) / 2 = 1.61×10⁻⁷` → `pH = 6.79`
- **Fehler durch lineare Näherung: 0.56 pH-Einheiten**

**Implementierung:**
```python
import math

def mix_ph(ph_tap: float, ph_ro: float, ro_percent: float) -> float:
    ratio = ro_percent / 100.0
    h_tap = 10 ** (-ph_tap)
    h_ro = 10 ** (-ph_ro)
    h_mix = h_ro * ratio + h_tap * (1 - ratio)
    return round(-math.log10(h_mix), 2)
```

**Einschränkung:** Auch die logarithmische Formel ist eine Näherung, da sie die Pufferkapazität (Alkalinität) des Leitungswassers nicht berücksichtigt. Wasser mit hoher Alkalinität (> 200 ppm CaCO₃) puffert den pH stärker als die reine H⁺-Konzentration erwarten lässt. Der berechnete pH ist daher eine Orientierung — **Messung nach Mischung ist obligatorisch**.

### 3.6 CalMag-Korrektur aus Mischwasser

Wenn der effektive Calcium- oder Magnesium-Gehalt des Mischwassers unter den Zielwerten der aktuellen Wachstumsphase liegt, empfiehlt das System eine CalMag-Supplementierung:

```
Ca_deficit = max(0, Ca_target − Ca_mix)
Mg_deficit = max(0, Mg_target − Mg_mix)
```

Wobei `Ca_mix = Ca_tap × (1 − r / 100)` und `Mg_mix = Mg_tap × (1 − r / 100)`.

**Schwellenwerte für CalMag-Empfehlung:**
- `Ca_deficit > Ca_threshold[substrat][phase]` ODER `Mg_deficit > Mg_threshold[substrat][phase]` → CalMag-Supplement empfohlen
- Die CalMag-Dosierung trägt zum EC bei und muss in das EC-Budget (Stufe 2) eingerechnet werden
- Falls EC-Budget nicht ausreicht: _"CalMag empfohlen, aber EC-Budget reicht nicht aus. Erhöhen Sie EC_target oder Osmose-Anteil."_

<!-- Quelle: Agrarbiologie-Review U-003 — Substratabhängige Zielwerte, Ca/Mg-Verhältnis -->

**Substrat- und phasenabhängige Ca/Mg-Zielwerte:**

| Phase | Ca (Hydro) | Ca (Coco) | Mg (Hydro) | Mg (Coco) |
|-------|-----------|-----------|-----------|-----------|
| Seedling | 80 ppm | 60 ppm | 30 ppm | 20 ppm |
| Vegetative | 150 ppm | 120 ppm | 50 ppm | 40 ppm |
| Flowering | 120 ppm | 100 ppm | 40 ppm | 30 ppm |

**Hintergrund:** Coco hat eine moderate Kationenaustauschkapazität (CEC) und puffert Ca²⁺ vorab — die Pflanze kann Ca auch aus dem Substrat beziehen, weshalb die externen Zielwerte niedriger liegen als bei reiner Hydroponik. Frisches Coco bindet im ersten Durchlauf verstärkt Ca²⁺ ("Ca-Hunger von Coco") — bei `substrate_reuse_count = 0` sollte die CalMag-Empfehlung um 20% erhöht werden.

**Ca/Mg-Verhältnis-Validierung:**

Das ideale Ca:Mg-Verhältnis in der Nährlösung liegt bei **3:1 bis 4:1** (ppm). Ein gestörtes Verhältnis verursacht Nährstoff-Antagonismus:

```
Ca_Mg_ratio = (Ca_mix + Ca_calmag_supplement) / (Mg_mix + Mg_calmag_supplement)

IF Ca_Mg_ratio < 2.0:
    WARNING: "Ca/Mg-Verhältnis ({ratio:.1f}:1) zu niedrig — Ca-Aufnahmehemmung möglich.
              Verwenden Sie ein CalMag-Produkt mit höherem Ca-Anteil."
IF Ca_Mg_ratio > 5.0:
    WARNING: "Ca/Mg-Verhältnis ({ratio:.1f}:1) zu hoch — Mg-Aufnahmehemmung möglich.
              Reduzieren Sie die CalMag-Dosierung oder ergänzen Sie Magnesium separat."
```

---

## 4. Stufe 2 — EC-Budget-Berechnung

### 4.1 Verfügbares EC-Budget

Das EC-Budget ist die Differenz zwischen dem Ziel-EC der fertigen Nährlösung und dem EC des Ausgangswassers:

```
EC_net = EC_target − EC_mix
```

**Randbedingungen:**
- `EC_net ≥ 0` — Falls `EC_mix ≥ EC_target`, ist kein Platz für Dünger. Das System gibt eine Warnung aus: _"Basis-EC des Wassers (X mS) erreicht oder überschreitet bereits den Ziel-EC (Y mS). Erhöhen Sie den Osmose-Anteil oder senken Sie den Ziel-EC."_
- `EC_net` muss Platz für **alle** geplanten Dünger plus geschätzten pH-Korrektur-EC lassen

### 4.2 EC-Obergrenze (EC_max)

Die absolute EC-Obergrenze wird durch die Kombination aus **Wachstumsphase** und **Substrattyp** bestimmt:

<!-- Quelle: Agrarbiologie-Review P-001 — Coco-Werte korrigiert, Living Soil als Sonderfall -->

| Substrat | Seedling | Vegetative | Flowering | Flush |
|----------|----------|------------|-----------|-------|
| `hydro_solution` (DWC/NFT) | 0.8–1.2 | 1.6–2.4 | 1.8–2.8 | 0.0–0.3 |
| `coco` | 0.8–1.0 | 1.6–2.0 | 1.8–2.4 | 0.0–0.3 |
| `soil` | 0.4–0.6 | 0.8–1.4 | 1.0–1.6 | 0.0–0.3 |
| `living_soil` | — | — | — | — |

**Anmerkungen:**
- **Coco** wird typisch 2–4× täglich bewässert (Sättigungs-/Drainage-Prinzip). Bei jeder Drainage gehen Nährsalze verloren, weshalb Coco höhere EC-Werte als Erde verträgt.
- **DWC-Systeme:** Erfahrene Gärtner können in der Blütephase bis 3.0 mS/cm gehen, abhängig von Sorte, Wassertemperatur und Sauerstoffgehalt. Die Obergrenze 2.8 mS ist konservativ.
- **Living Soil:** EC-basierte Dosierung ist bei Living Soil **nicht anwendbar**. Living Soil ist ein biologisch aktives System — Mineralische Nährsalze stören das Mikrobiom, das durch Mineralisation organischer Substanz die Nährstoffe bereitstellt. Das System zeigt statt EC-Budget die organische Düngungsempfehlung an (→ REQ-004 §Organische Freiland-Düngung: Komposttee, Top Dress, g/m²).
- **Flush:** EC 0.0–0.3 mS statt 0.0, da pH-Korrektur und enzymatische Zusätze (z.B. Plagron Plant Wash) einen minimalen EC-Beitrag haben. Völlig ionenfreies Wasser (EC 0.0) erzeugt extremen osmotischen Stress an der Wurzel.

**Validierungsregel:**

```
EC_target ≤ EC_max[substrat][phase]
```

Falls überschritten → Warnung (kein Hardblock): _"Ziel-EC (X mS) überschreitet die empfohlene Obergrenze (Y mS) für Phase Z auf Substrat W."_

### 4.3 Reserve für pH-Korrektur

pH-Adjuster (pH Down / pH Up) tragen ebenfalls zum EC bei. Das effektive EC-Budget für Dünger berücksichtigt diese Reserve:

```
EC_net_effective = EC_net − EC_ph_reserve
```

Wobei `EC_ph_reserve` geschätzt wird als:

```
EC_ph ≈ (ml_pH_Adjuster / V) × 0.03 mS/cm pro ml/L
```

Die tatsächliche pH-Korrektur-Menge hängt von der Alkalinität des Wassers ab (siehe REQ-004 §`_estimate_ph_adjustment`). Als konservative Schätzung:
- Weiches Wasser (Alkalinität < 50 ppm): `EC_ph_reserve = 0.02 mS`
- Mittleres Wasser (50–150 ppm): `EC_ph_reserve = 0.03 mS`
- Hartes Wasser (> 150 ppm): `EC_ph_reserve = 0.05 mS`

### 4.4 Temperaturkorrektur des EC-Werts (EC@25)

<!-- Quelle: Agrarbiologie-Review U-001 -->

EC-Messgeräte messen die Leitfähigkeit bei der aktuellen Wassertemperatur. Der Referenzwert ist **EC@25** (normiert auf 25°C). Die meisten digitalen EC-Meter kompensieren automatisch (Temperature Compensation Coefficient, TCC ≈ 2% pro °C). Wenn aber manuell gemessene Werte ohne Kompensation eingegeben werden, kann die Abweichung erheblich sein:

**Korrekturformel:**

```
EC@25 = EC_gemessen / (1 + 0.02 × (T_gemessen − 25))
```

**Beispiel:** Nährlösung bei 18°C, gemessene EC = 1.72 mS:
```
EC@25 = 1.72 / (1 + 0.02 × (18 − 25))
      = 1.72 / (1 − 0.14)
      = 1.72 / 0.86
      = 2.00 mS/cm
```

→ Der Gärtner misst 1.72 mS und glaubt, aufdüngen zu müssen. Tatsächlich hat die Lösung bei 25°C bereits 2.00 mS.

**Optionales Feld:** `measurement_temperature_celsius: Optional[float]` auf `TankState` und `FeedingEvent`. Wenn angegeben und Wert ≠ 25°C, zeigt das System den korrigierten EC@25-Wert an und verwendet diesen für alle Validierungen.

**UI-Hinweis:** Wenn keine Temperatur angegeben: _"EC-Wert wird als EC@25 interpretiert. Falls Ihr Messgerät keine automatische Temperaturkompensation hat, geben Sie die Wassertemperatur an."_

### 4.5 Salzakkumulation und Substrat-Pufferwirkung

<!-- Quelle: Agrarbiologie-Review U-002 -->

Die EC-Budget-Berechnung behandelt die Nährlösung als isoliertes System. In der Praxis akkumulieren sich Salze im Substrat (Salt Build-Up) über mehrere Gießzyklen:

**Runoff-EC-Ratio als Indikator:**

```
runoff_ratio = runoff_ec / input_ec
```

| runoff_ratio | Status | Maßnahme |
|-------------|--------|----------|
| 1.0–1.1 | Optimal | Keine Aktion |
| 1.1–1.3 | Leicht erhöht | Monitoring, ggf. mehr Drain-to-Waste |
| 1.3–1.5 | Flush empfohlen | System erstellt Flush-Aufgabe (REQ-006) |
| > 1.5 | Flush dringend | Warnung: _"Kritische Salzakkumulation"_ |

**Trend-Analyse:** Wenn 3 aufeinanderfolgende `FeedingEvent.runoff_ec / measured_ec_before`-Werte > 1.3: Celery-Task erstellt automatisch eine Flush-Aufgabe (via REQ-006 Aufgabenplanung).

**Substrat-CEC-Einfluss (Kationenaustauschkapazität):**
- **Coco (moderate CEC):** Puffert Ca²⁺ und Mg²⁺. Frisches Coco bindet im ersten Durchlauf verstärkt Ca²⁺ ("Ca-Hunger") — bei `Substrate.reuse_count = 0` empfiehlt das System eine um 20% erhöhte CalMag-Dosierung.
- **Perlite/Blähton (geringe CEC):** Kaum Pufferung, EC der Nährlösung = EC im Wurzelbereich.
- **Living Soil (hohe CEC):** EC der Gießlösung bildet die tatsächliche Nährstoff-Verfügbarkeit nicht ab → EC-Budget-Berechnung deaktiviert (siehe §4.2).

**Hinweis für die Spezifikation:** _"EC-Zielwerte gelten für die applizierte Nährlösung, nicht für den EC im Substrat. Der EC im Substrat kann je nach CEC und Gießstrategie erheblich abweichen. Regelmäßige Runoff-EC-Messung ist die einzige zuverlässige Methode zur Überwachung des tatsächlichen Nährstoffniveaus im Wurzelbereich."_

---

## 5. Stufe 3 — Dünger-Dosierung

### 5.1 Eingabeparameter

Für die Dosierungsberechnung werden benötigt:

| Parameter | Quelle | Beschreibung |
|-----------|--------|-------------|
| `EC_net` | Stufe 2 | Verfügbares EC-Budget |
| `V` | Benutzereingabe oder Tank | Zielvolumen in Liter |
| `fertilizers[]` | NutrientPlan / Benutzerauswahl | Liste der zu dosierenden Dünger |
| `fertilizers[i].ec_contribution_per_ml` | Fertilizer-Katalog | EC-Beitrag pro ml/L (mS/cm) |
| `fertilizers[i].npk_ratio` | Fertilizer-Katalog | NPK-Analysewerte in % |
| `fertilizers[i].mixing_priority` | Fertilizer-Katalog | Reihenfolge (1=zuerst) |

### 5.2 EC-basierte Rezept-Skalierung (Algorithmus)

<!-- Quelle: Agrarbiologie-Review F-001 — NPK-Summen-Gewichtung ersetzt durch EC-basierte Skalierung -->

**Warum nicht NPK-Gewichtung?** Die elektrische Leitfähigkeit einer Nährlösung hängt von der Ionenkonzentration und der spezifischen Ionenleitfähigkeit der gelösten Salze ab, **nicht** von der NPK-Prozentangabe auf dem Etikett. Stickstoff liegt je nach Produkt als Nitrat (NO₃⁻), Ammonium (NH₄⁺) oder Harnstoff vor — bei gleicher ppm-Zahl erzeugt Nitrat deutlich mehr EC als Harnstoff (un-ionisiert). Die alleinige Grundlage für die EC-Verteilung ist daher `Fertilizer.ec_contribution_per_ml` (gemessener EC-Beitrag pro ml/L).

#### Option A — Rezept-Skalierung (bevorzugt)

Wenn ein Nutzer ein Hersteller-Rezept oder eigene Dosierungsverhältnisse als Startpunkt hat (typischer Fall: NutrientPlan mit definierten `ml_per_liter`-Werten pro Dünger), wird das gesamte Rezept proportional auf das verfügbare EC-Budget skaliert:

**Schritt 1 — Referenz-EC des Rezepts berechnen:**

```
EC_rezept = Σ(r_i × ec_i)
```

Wobei `r_i` die geplanten Dosierungen (ml/L) aus dem NutrientPlan und `ec_i = Fertilizer.ec_contribution_per_ml`.

**Schritt 2 — Skalierungsfaktor:**

```
k = EC_net / EC_rezept
```

**Schritt 3 — Skalierte Dosierungen:**

```
d_i = k × r_i
```

**Schritt 4 — Gesamtvolumen:**

```
total_ml_i = d_i × V
```

**Vorteil:** Das Verhältnis zwischen den Düngern bleibt exakt erhalten (z.B. GHE Flora-Serie 3:2:1 bleibt 3:2:1), nur die Gesamtmenge wird angepasst. Hersteller-Rezepte sind auf ausgewogene NPK-Verhältnisse optimiert — die Skalierung erhält diese Balance.

#### Option B — Gleichverteilung ohne Rezept (Fallback)

Wenn keine Dosierungsverhältnisse vorgegeben sind (ad-hoc-Berechnung ohne NutrientPlan), wird das EC-Budget gleichmäßig auf alle Dünger mit `ec_contribution_per_ml > 0` verteilt:

```
n = Anzahl Dünger mit ec_i > 0
ec_allocation_i = EC_net / n
d_i = ec_allocation_i / ec_i
```

**Hinweis:** Option B ist eine Notfall-Näherung. In der Praxis sollte immer ein Rezept (Option A) verwendet werden, da Gleichverteilung NPK-Ungleichgewichte erzeugt.

### 5.3 Validierung — EC-Obergrenze nicht überschreiten

Nach der Berechnung aller Dosierungen muss validiert werden:

```
EC_calculated = EC_mix + Σ(d_i × ec_i) + EC_ph

Constraint: EC_calculated ≤ EC_max
```

**Toleranzbereich:**

```
|EC_calculated − EC_target| ≤ EC_tolerance
```

Wobei `EC_tolerance = 0.3 mS/cm` (konfigurierbar, siehe `delivery_channel_engine.py`).

### 5.4 Priorisierte Vorkategorien und Sonderfälle

Die EC-Budget-Verteilung erfolgt in einer festen Reihenfolge. Vor der Rezept-Skalierung (§5.2) werden priorisierte Kategorien abgezogen:

<!-- Quelle: Agrarbiologie-Review U-004 — Silizium als eigene Budget-Kategorie -->

#### Misch-Reihenfolge und EC-Budget-Abzüge:

```
EC_net (gesamt)
  − EC_silicate     → Silizium-Supplemente (mixing_priority 0, ZUERST ins Wasser)
  − EC_calmag       → CalMag-Korrektur (mixing_priority 1–5)
  = EC_net_remaining → Verfügbar für Rezept-Skalierung (Base + Supplements)
  − EC_ph_reserve   → Reserve für pH-Korrektur (ZULETZT)
```

#### 1. Silizium-Supplemente (höchste Priorität)

Kaliumsilikat-Lösungen (z.B. Plagron Silic Rock, Aptus Silic Boost) müssen **als erstes** ins Wasser, da Silizium bei direktem Kontakt mit Ca²⁺ oder Mg²⁺ als wasserunlösliches Calciumsilikat (CaSiO₃) ausfällt. Silizium erhöht den pH temporär um +0.5 bis +1.5, was die nachfolgende pH-Korrektur beeinflusst.

```
EC_silicate = d_silicate × ec_silicate
EC_net_after_silicate = EC_net − EC_silicate
```

**Warnung:** Wenn ein Silizium-Produkt (`type = 'silicate'` oder `mixing_priority > mixing_priority_calmag`) nach CalMag in der Misch-Reihenfolge erscheint → _"WARNUNG: Silizium muss vor CalMag zugegeben werden! Ca²⁺-Silikat-Ausfällung."_

#### 2. CalMag-Korrektur (priorisiert)

CalMag wird vor der Rezept-Skalierung dosiert, wenn ein Ca/Mg-Defizit aus Stufe 1 erkannt wurde (siehe §3.6):

```
EC_calmag = d_calmag × ec_calmag
EC_net_remaining = EC_net_after_silicate − EC_calmag
```

#### 3. Rezept-Skalierung (Base-Nutrients + Supplements)

Das verbleibende EC-Budget wird auf die restlichen Dünger verteilt (§5.2 Option A oder B).

#### 4. pH-Adjuster (zuletzt)

<!-- Quelle: Agrarbiologie-Review U-006 -->

pH-Korrekturen werden nach allen Düngern zugegeben. Gängige pH-Adjuster haben produktspezifische EC-Beiträge:

| Produkt | Typischer EC-Beitrag pro ml/L |
|---------|------------------------------|
| pH-Down (Phosphorsäure H₃PO₄, 85%) | 0.10–0.15 mS |
| pH-Down (Zitronensäure) | 0.05–0.08 mS |
| pH-Up (Kaliumhydroxid KOH) | 0.12–0.18 mS |
| pH-Up (Kaliumbicarbonat KHCO₃) | 0.08–0.12 mS |

Wenn ein pH-Adjuster als `Fertilizer` mit `type = 'ph_adjuster'` und definiertem `ec_contribution_per_ml` erfasst ist, wird dessen exakter EC-Beitrag verwendet. Andernfalls greift die pauschale Schätzung aus §4.3.

**Hinweis:** Phosphorsäure-basiertes pH-Down führt dem System Phosphat zu (erhöht P-Spiegel). Kaliumhydroxid-basiertes pH-Up erhöht den Kalium-Spiegel. Bei hohem pH-Korrekturbedarf (hartes Wasser) sind diese Nebeneffekte relevant.

#### 5. Dünger ohne messbaren EC-Beitrag

<!-- Quelle: Agrarbiologie-Review U-005 -->

Biologische Zusätze (Mykorrhiza, Trichoderma, Enzyme) tragen nicht messbar zum EC bei (`ec_contribution_per_ml = 0`) und werden nach Herstellerangabe dosiert (Festdosierung statt EC-basiert).

**Organische Flüssigdünger mit unbekanntem EC-Beitrag:**

Organische Produkte (Fischemulsion, Wurmhumus-Extrakt, Komposttee) haben einen messbaren aber variablen EC-Beitrag (typisch 0.03–0.1 mS/ml/L). Da der exakte Wert chargenabhängig ist, werden sie mit `ec_contribution_per_ml = 0` erfasst, obwohl ihr tatsächlicher Beitrag nicht null ist.

Neues Feld: `Fertilizer.ec_contribution_uncertain: bool = False` — wenn `true`:
- Zusätzliche EC-Reserve von 0.1–0.2 mS im Budget einplanen
- Warnung im UI: _"EC-Beitrag dieses organischen Düngers ist variabel und nicht im EC-Budget berechnet. Messen Sie den EC nach Zugabe."_
- Mischprotokoll enthält nach dem Schritt: _"EC messen und protokollieren"_

### 5.5 Sicherheitslimits

<!-- Quelle: Agrarbiologie-Review F-003, P-002, P-003 -->

| Limit | Wert | Beschreibung |
|-------|------|-------------|
| `max_ml_per_liter` | `Fertilizer.max_dose_ml_per_liter` oder 20 ml/L (Fallback) | Produktspezifisches Maximum aus Herstellerangabe; System-Fallback 20 ml/L wenn nicht hinterlegt |
| `EC_tolerance` | Phasenabhängig (siehe unten) | Akzeptable Abweichung von Ziel-EC |
| `EC_max_by_tank_type` | Tank-Typ-abhängig (siehe unten) | Differenziert nach Tank-Typ statt globaler Obergrenze |
| `min_ec_contribution` | 0.01 mS/ml/L | Unter diesem Wert wird der Dünger als "kein EC-Beitrag" behandelt |

**EC-Obergrenze nach Tank-Typ (REQ-014):**

```
EC_MAX_BY_TANK_TYPE = {
    "nutrient":       3.0,    // Fertige Nährlösung
    "irrigation":     1.5,    // Gießwasser mit pH-Korrektur
    "recirculation":  3.0,    // Rezirkulation
    "reservoir":      None,   // Kein Limit (Rohwasser-Speicher)
    "stock_solution": 250.0,  // Konzentrat (100x–200x)
}
```

**Phasenabhängige EC-Toleranz:**

Die pauschale Toleranz von 0.3 mS/cm ist für Keimlinge zu groß (37.5% Abweichung bei Ziel 0.8 mS). Stattdessen relative Toleranz:

```
EC_tolerance = max(0.1, EC_target × 0.10)   // ±10% des Zielwerts, mindestens 0.1 mS
```

| Phase | EC_target (typisch) | Toleranz (±10%) |
|-------|--------------------|-----------------|
| Seedling | 0.8–1.0 mS | ±0.10 mS |
| Vegetative | 1.6–2.0 mS | ±0.16–0.20 mS |
| Flowering | 1.8–2.4 mS | ±0.18–0.24 mS |

**Produktspezifisches Dosierungslimit:**

Das Feld `Fertilizer.max_dose_ml_per_liter: Optional[float]` enthält die Herstellerangabe für die maximale Dosierung. Gängige Hochkonzentrat-Produkte werden mit 2–8 ml/L dosiert — 20 ml/L wäre bei den meisten Produkten eine schwere Überdosierung (osmotischer Stress). Das System-Maximum von 20 ml/L dient nur als Catchall für Produkte ohne Herstellerangabe (z.B. verdünnte Jauchen, Enzyme).

---

## 6. Gesamtformel — Zusammenfassung

### End-to-End-Berechnung in einem Durchlauf:

**Eingabe:**
- `EC_tap`, `EC_ro` (Wasserprofile)
- `EC_target` (Ziel-EC der Nährlösung)
- `V` (Zielvolumen)
- `fertilizers[]` (ausgewählte Dünger mit `ec_contribution_per_ml` und `npk_ratio`)

**Schritt 1 — Osmose-Anteil berechnen:**
```
r = (EC_tap − EC_target_base) / (EC_tap − EC_ro) × 100
```
Wobei `EC_target_base` der gewünschte Basis-EC des Wassers vor Düngerzugabe ist. Dieser kann entweder:
- **manuell** vom Nutzer festgelegt werden
- **automatisch** aus dem NutrientPlan (`water_mix_ratio_ro_percent`) abgeleitet werden
- **berechnet** werden als `EC_target − EC_net_desired`

**Schritt 2 — Mischwasser-EC:**
```
EC_mix = EC_ro × (r / 100) + EC_tap × (1 − r / 100)
```

**Schritt 3 — EC-Budget:**
```
EC_net = EC_target − EC_mix
```

**Schritt 4 — Priorisierte Vorkategorien abziehen:**
```
EC_net_after_si   = EC_net − (d_silicate × ec_silicate)   // falls Silizium vorhanden
EC_net_after_calmag = EC_net_after_si − (d_calmag × ec_calmag)   // falls CalMag nötig
EC_net_remaining  = EC_net_after_calmag − EC_ph_reserve
```

**Schritt 5 — Dünger dosieren (Rezept-Skalierung):**
```
EC_rezept = Σ(r_i × ec_i)                // EC des ungeskalierten Rezepts
k = EC_net_remaining / EC_rezept          // Skalierungsfaktor
Für jeden Dünger i im Rezept:
    d_i     = k × r_i
    total_i = d_i × V
```

**Schritt 6 — Validierung:**
```
EC_final = EC_mix + EC_silicate + EC_calmag + Σ(d_i × ec_i) + EC_ph
ASSERT EC_final ≤ EC_max
ASSERT |EC_final − EC_target| ≤ max(0.1, EC_target × 0.10)
```

---

## 7. Praxisbeispiel — Vollständige Berechnung

### Ausgangslage:
- **Leitungswasser:** EC = 0.55 mS/cm, Ca = 120 ppm, Mg = 25 ppm
- **Osmosewasser:** EC = 0.02 mS/cm
- **Ziel-EC Nährlösung:** 1.8 mS/cm (Vegetative Phase, Coco)
- **Gewünschter Basis-EC:** 0.15 mS/cm
- **Zielvolumen:** 50 Liter

### Schritt 1 — Osmose-Anteil:
```
r = (0.55 − 0.15) / (0.55 − 0.02) × 100
  = 0.40 / 0.53 × 100
  = 75.5%
```

### Schritt 2 — Kontrollrechnung Mischwasser-EC:
```
EC_mix = 0.02 × 0.755 + 0.55 × 0.245
       = 0.0151 + 0.1348
       = 0.15 mS/cm ✓
```

### Schritt 3 — Wasservolumen:
```
V_ro  = 50 × 0.755 = 37.75 L Osmosewasser
V_tap = 50 × 0.245 = 12.25 L Leitungswasser
```

### Schritt 4 — CalMag-Check:
```
Ca_mix = 120 × 0.245 = 29.4 ppm    (Ziel: 150 ppm → Defizit 120.6 ppm)
Mg_mix = 25 × 0.245  = 6.1 ppm     (Ziel: 50 ppm → Defizit 43.9 ppm)
→ CalMag-Supplement nötig!
```

### Schritt 5 — EC-Budget:
```
EC_net = 1.80 − 0.15 = 1.65 mS/cm

// Davon CalMag: z.B. CalMag Agent mit ec = 0.15 mS/ml/L, dosiert mit 1.0 ml/L
EC_calmag = 1.0 × 0.15 = 0.15 mS

EC_net_remaining = 1.65 − 0.15 = 1.50 mS    (für restliche Dünger)
EC_ph_reserve = 0.03 mS                       (mittelhartes Wasser nach Mischung)
EC_net_effective = 1.50 − 0.03 = 1.47 mS
```

### Schritt 6 — Dünger dosieren (Rezept-Skalierung):

Herstellerrezept (GHE Flora-Serie, Vegetative Coco): 3:2:1 ml/L

| Dünger | Rezept r_i (ml/L) | ec_i (mS/ml/L) | EC-Beitrag ungeskalt. |
|--------|------------------|-----------------|----------------------|
| Flora Micro (A) | 3.0 | 0.10 | 0.300 |
| Flora Gro (B) | 2.0 | 0.10 | 0.200 |
| Flora Bloom | 1.0 | 0.15 | 0.150 |
| **EC_rezept** | | | **0.650** |

```
Skalierungsfaktor: k = 1.47 / 0.650 = 2.262
```

| Dünger | r_i | k × r_i = d_i (ml/L) | EC-Beitrag (mS) | total (ml) |
|--------|-----|----------------------|-----------------|-----------|
| Flora Micro (A) | 3.0 | 6.79 | 0.679 | 339.5 |
| Flora Gro (B) | 2.0 | 4.52 | 0.452 | 226.0 |
| Flora Bloom | 1.0 | 2.26 | 0.339 | 113.0 |
| **Summe** | | | **1.470** | |

**Verhältnis erhalten:** 6.79 : 4.52 : 2.26 = 3 : 2 : 1 ✓

### Schritt 7 — Validierung:
```
EC_final = 0.15 (Wasser) + 0.15 (CalMag) + 0.679 + 0.452 + 0.339 + 0.03 (pH)
         = 1.80 mS/cm

Toleranz: max(0.1, 1.80 × 0.10) = 0.18 mS
Abweichung: |1.80 − 1.80| = 0.00 mS (< 0.18 Toleranz) ✓
EC_max (Coco, Vegetative) = 2.0 mS → 1.80 ≤ 2.0 ✓
```

### Mischprotokoll:
```
1. 37.75 L Osmosewasser + 12.25 L Leitungswasser mischen (18–22°C)
   → EC ≈ 0.15 mS, prüfen
   (18–22°C: Optimale Salzlöslichkeit, gelöster Sauerstoff >8.5 mg/L)
2. 50.0 ml CalMag Agent zugeben (1.0 ml/L), gründlich rühren
3. 339.5 ml Flora Micro (6.79 ml/L), rühren, 2 Min warten
4. 226.0 ml Flora Gro (4.52 ml/L), rühren
5. 113.0 ml Flora Bloom (2.26 ml/L), rühren
6. pH-Korrektur (pH Down), schrittweise zugeben
7. Finale Messung: EC 1.8 mS (±0.18), pH 5.8–6.2
```

---

## 8. Datenfluss im System

### 8.1 Woher kommen die Eingabewerte?

| Wert | Primärquelle | Fallback |
|------|-------------|----------|
| `EC_tap` | `Site.water_config.tap_water_profile.ec_ms` (REQ-002) | Manuelle Eingabe |
| `EC_ro` | `Site.water_config.ro_water_profile.ec_ms` (REQ-002) | Default: 0.02 mS |
| `r` (Osmose-%) | `NutrientPlan.water_mix_ratio_ro_percent` (REQ-004) | `TankFillEvent.water_mix_ratio_ro_percent` → Manuelle Eingabe |
| `EC_target` | `DeliveryChannel.target_ec_ms` (REQ-004) | `NutrientPlanPhaseEntry.target_ec_ms` |
| `ec_contribution_per_ml` | `Fertilizer.ec_contribution_per_ml` (REQ-004) | Herstellerangabe/Labormessung |
| `V` (Volumen) | `Tank.volume_liters` (REQ-014) | Benutzereingabe |

### 8.2 Wasserparameter-Kaskade (REQ-014)

Die 4-Stufen-Kaskade für `TankFillEvent` (REQ-014 §`resolve_water_defaults`):

```
1. EXPLICIT    → Werte direkt im TankFillEvent gesetzt
2. NUTRIENT_PLAN → NutrientPlan.water_mix_ratio_ro_percent
3. SITE_PROFILE  → Site.water_config (TapWaterProfile + RoWaterProfile)
4. MANUAL       → Benutzer gibt Werte manuell ein
```

### 8.3 Berechnungs-Trigger

Die EC-Budget-Kalkulation wird in folgenden Kontexten ausgelöst:

| Kontext | Trigger | Ausgabe |
|---------|---------|---------|
| **NutrientPlan-Validierung** | Speichern/Validieren eines Plans | EC-Budget-Check pro Phase-Entry / Channel |
| **NutrientSolutionCalculator** | API-Aufruf `POST /nutrient-calculations/calculate` | Vollständiges Mischprotokoll mit Dosierungen |
| **TankFillEvent** | Neue Tankbefüllung erstellen | EC-Budget-Check gegen Plan, Warnungen |
| **Gantt-Diagramm** | Darstellung des NutrientPlans | EC-Budget-Status pro Phase (✓/✗) |

---

## 9. Fehlerszenarien und Warnungen

### 9.1 EC-Budget erschöpft

```
IF EC_mix ≥ EC_target:
    WARNING: "Basis-EC ({EC_mix} mS) erreicht oder überschreitet Ziel-EC ({EC_target} mS).
              Erhöhen Sie den Osmose-Anteil (aktuell {r}%) oder senken Sie den Ziel-EC."
    → Dosierungsberechnung liefert leere Dosierungsliste
```

### 9.2 EC-Obergrenze überschritten

```
IF EC_final > EC_max:
    WARNING: "Berechnete EC ({EC_final} mS) überschreitet die Obergrenze ({EC_max} mS)
              für {phase} auf {substrate}. Reduzieren Sie die Düngerdosierung oder
              erhöhen Sie den Osmose-Anteil."
    → Kein Hardblock, aber visuelle Warnung im UI
```

### 9.3 Osmose-Ziel unerreichbar

```
IF EC_target_base < EC_ro:
    ERROR: "Gewünschter Basis-EC ({EC_target_base} mS) ist niedriger als der EC
            des Osmosewassers ({EC_ro} mS). Ziel ist physikalisch nicht erreichbar."
```

### 9.4 Kein Osmose-System

```
IF Site.water_config.has_ro_system == false:
    EC_mix = EC_tap (kein Mischen möglich)
    EC_net = EC_target − EC_tap
    INFO: "Kein Osmose-System vorhanden. Basis-EC = Leitungswasser-EC ({EC_tap} mS)."
```

### 9.5 Einzeldünger überschreitet Sicherheitslimit

```
IF d_i > 20 ml/L:
    WARNING: "Dosierung für {fertilizer_name} ({d_i} ml/L) überschreitet das
              Sicherheitslimit von 20 ml/L. Prüfen Sie den ec_contribution_per_ml-Wert
              oder reduzieren Sie den EC-Zielwert."
    → d_i wird auf 20 ml/L gekappt
```

---

## 10. API-Integration

### 10.1 Bestehende Endpunkte (bereits implementiert)

| Endpunkt | Methode | Beschreibung |
|----------|---------|-------------|
| `POST /nutrient-calculations/calculate` | POST | NutrientSolutionCalculator — vollständige Dosierungsberechnung |
| `POST /nutrient-plans/{key}/validate` | POST | NutrientPlan-Validierung mit EC-Budget-Check |
| `POST /tanks/{key}/fill-events` | POST | TankFillEvent mit resolve_water_defaults |

### 10.2 Neuer Endpunkt — Osmose-Anteil-Berechnung

```
POST /api/v1/nutrient-calculations/water-mix
```

**Request:**
```json
{
    "tap_water_ec_ms": 0.55,
    "ro_water_ec_ms": 0.02,
    "target_base_ec_ms": 0.15,
    "target_volume_liters": 50.0,
    "tap_water_profile": {
        "ph": 7.2,
        "calcium_ppm": 120,
        "magnesium_ppm": 25,
        "alkalinity_ppm": 180,
        "chlorine_ppm": 0.3,
        "chloramine_ppm": 0.0
    }
}
```

**Response:**
```json
{
    "ro_percent": 75.5,
    "effective_ec_ms": 0.15,
    "volume_ro_liters": 37.75,
    "volume_tap_liters": 12.25,
    "effective_water_profile": {
        "ec_ms": 0.15,
        "ph": 6.53,
        "ph_note": "Logarithmisch berechnet, Messung nach Mischung empfohlen",
        "calcium_ppm": 29.4,
        "magnesium_ppm": 6.1,
        "alkalinity_ppm": 44.1,
        "chlorine_ppm": 0.07,
        "chloramine_ppm": 0.0
    },
    "calmag_correction": {
        "calcium_deficit_ppm": 120.6,
        "magnesium_deficit_ppm": 43.9,
        "needs_correction": true
    },
    "warnings": []
}
```

### 10.3 Neuer Endpunkt — EC-Budget-Vorschau

```
POST /api/v1/nutrient-calculations/ec-budget
```

**Request:**
```json
{
    "base_water_ec_ms": 0.15,
    "target_ec_ms": 1.80,
    "substrate_type": "coco",
    "phase": "vegetative",
    "fertilizer_keys": ["flora-micro", "flora-gro", "flora-bloom"],
    "calmag_key": "calmag-agent",
    "target_volume_liters": 50.0
}
```

**Response:**
```json
{
    "ec_budget_total": 1.65,
    "ec_calmag": 0.15,
    "ec_ph_reserve": 0.03,
    "ec_budget_fertilizers": 1.47,
    "ec_max_phase": 2.2,
    "dosages": [
        {
            "fertilizer_key": "calmag-agent",
            "product_name": "CalMag Agent",
            "ml_per_liter": 1.0,
            "total_ml": 50.0,
            "ec_contribution": 0.15,
            "is_calmag": true,
            "mixing_order": 1
        },
        {
            "fertilizer_key": "flora-micro",
            "product_name": "Flora Micro",
            "ml_per_liter": 4.20,
            "total_ml": 210.0,
            "ec_contribution": 0.42,
            "is_calmag": false,
            "mixing_order": 2
        }
    ],
    "ec_calculated": 2.01,
    "ec_deviation": 0.21,
    "ec_within_tolerance": true,
    "ec_within_phase_limit": true,
    "mixing_instructions": ["..."],
    "warnings": []
}
```

---

## 11. Bezug zu bestehenden Engines

| Engine | Datei | Relevanz |
|--------|-------|----------|
| `WaterMixCalculator` | `domain/engines/water_mix_engine.py` | Stufe 1 — Mischwasser-Berechnung (implementiert) |
| `WaterSourceValidator` | `domain/engines/water_mix_engine.py` | Validierung der Wasserprofile (implementiert) |
| `NutrientSolutionCalculator` | `domain/engines/nutrient_engine.py` | Stufe 3 — Dosierungsberechnung (implementiert) |
| `DeliveryChannelValidator` | `domain/engines/delivery_channel_engine.py` | EC-Budget-Check pro Channel (implementiert) |
| `TankEngine.resolve_water_defaults` | `domain/engines/tank_engine.py` | 4-Stufen-Kaskade (implementiert) |

**Erweiterungsbedarf:**
- `WaterMixCalculator`: pH-Berechnung auf logarithmische Formel umstellen (§3.5a), Rückwärtsberechnung (`calculate_ro_percent_for_target`) hinzufügen
- `NutrientSolutionCalculator`: NPK-Summen-Algorithmus durch Rezept-Skalierung ersetzen (§5.2), Silizium/CalMag-Priorisierung integrieren (§5.4)
- `DeliveryChannelValidator`: Phasenabhängige EC-Toleranz (§5.5)
- `TankEngine`: EC_max nach Tank-Typ differenzieren (§5.5)
- Neues Feld: `Fertilizer.max_dose_ml_per_liter`, `Fertilizer.ec_contribution_uncertain`
- Neuer Service-Layer: `WaterMixService` mit den beiden neuen API-Endpunkten (§10.2, §10.3)
- Runoff-Trend-Analyse: Celery-Task für automatische Flush-Empfehlung (§4.5)

---

## 12. UI-Anforderungen

### 12.1 Wassermischer-Widget (neues UI-Element)

Ein interaktives Widget auf der NutrientCalculations-Seite und im TankFillEvent-Dialog:

- **Eingabe:** EC des Leitungswassers, Ziel-Basis-EC (Slider oder Eingabefeld)
- **Ausgabe:** Osmose-Anteil in %, Volumen-Aufteilung (RO/Tap), effektive Wasserparameter
- **Echtzeit-Berechnung:** Bei Änderung der Eingabewerte aktualisiert sich das Ergebnis sofort
- **Vorbelegung:** Wenn `Site.water_config` vorhanden, werden `EC_tap` und `EC_ro` automatisch vorbelegt
- **CalMag-Hinweis:** Falls Ca/Mg-Defizit erkannt, Empfehlung als Info-Banner anzeigen

### 12.2 EC-Budget-Balken (visuell)

Ein horizontaler Balken, der das EC-Budget visualisiert:

```
|←── EC_mix ──→|←── CalMag ──→|←── Dünger A ──→|←── Dünger B ──→|←pH→| EC_max
0              0.15           0.30              0.72              1.35  1.38  2.2
```

- **Grün:** EC-Beiträge innerhalb des Budgets
- **Gelb:** EC nähert sich der Obergrenze (> 90% von EC_max)
- **Rot:** EC überschreitet EC_max

### 12.3 Expertise-Level-Abstufung (REQ-021)

| Element | Beginner | Intermediate | Expert |
|---------|----------|-------------|--------|
| Osmose-Anteil-Schieberegler | Versteckt | Sichtbar | Sichtbar |
| EC-Budget-Detailbalken | Versteckt | Vereinfacht | Vollständig |
| CalMag-Korrektur | Automatisch (kein UI) | Empfehlung sichtbar | Manuell überschreibbar |
| pH-EC-Reserve | Versteckt | Info-Text | Editierbar |
| Mischwasser-Detailprofil (Ca, Mg, Alk.) | Versteckt | Versteckt | Vollständige Tabelle |

---

## 13. Testszenarien

### 13.1 Unit-Tests (Engine-Level)

| Test | Eingabe | Erwartetes Ergebnis |
|------|---------|---------------------|
| Vorwärtsberechnung EC_mix | EC_tap=0.5, EC_ro=0.02, r=70 | EC_mix=0.164 |
| Rückwärtsberechnung r | EC_tap=0.8, EC_ro=0.02, EC_mix=0.2 | r=76.9% |
| pH logarithmisch | pH_tap=8.2, pH_ro=6.5, r=50 | pH_mix=6.79 (nicht 7.35!) |
| EC-Budget korrekt | EC_target=1.8, EC_mix=0.15 | EC_net=1.65 |
| Rezept-Skalierung | Rezept 3:2:1 ml/L, EC_net=1.47 | Skaliert auf 6.79:4.52:2.26, Verhältnis 3:2:1 erhalten |
| Gleichverteilung (Fallback) | 2 Dünger ohne Rezept, EC_net=1.0 | Jeweils 0.5 mS EC-Anteil |
| EC-Obergrenze | EC_final=2.5, EC_max=2.0 (Coco) | Warnung erzeugt |
| Kein EC-Budget | EC_mix=2.0, EC_target=1.8 | Leere Dosierungsliste + Warnung |
| Kein RO-System | has_ro_system=false, EC_tap=0.4 | EC_mix=EC_tap=0.4, r=0 |
| CalMag-Priorisierung | Ca_deficit=120, CalMag ec=0.15 | CalMag vor NPK-Düngern, EC_net reduziert |
| Silizium vor CalMag | Si mixing_priority=0, CalMag=1 | Si zuerst abgezogen, dann CalMag |
| Ca/Mg-Verhältnis | Ca=200, Mg=30 (Ratio 6.7:1) | Warnung: Ratio > 5.0, Mg-Hemmung |
| Sicherheitslimit (produktspez.) | d_i=12, Fertilizer.max_dose=8 | d_i gekappt auf 8 ml/L + Warnung |
| Sicherheitslimit (Fallback) | d_i=25, kein max_dose | d_i gekappt auf 20 ml/L + Warnung |
| Osmose-Ziel unerreichbar | EC_target_base=0.01, EC_ro=0.02 | Fehler: physikalisch unmöglich |
| EC-Temperaturkorrektur | EC_gemessen=1.72, T=18°C | EC@25=2.00 mS |
| Living Soil Bypass | substrate=living_soil | Keine EC-Budget-Berechnung, Verweis auf organische Düngung |
| Frisches Coco | reuse_count=0, Coco | CalMag-Empfehlung +20% erhöht |
| Organisch uncertain | ec_contribution_uncertain=true | EC-Reserve +0.15 mS, Messaufforderung im Protokoll |
| Phasenabhängige Toleranz | EC_target=0.8 (Seedling) | Toleranz = 0.10 mS (nicht 0.3) |

### 13.2 Integrationstests (API-Level)

| Test | Endpunkt | Assertion |
|------|----------|-----------|
| Water-Mix mit Site-Profil | `POST /water-mix` | Response enthält `ro_percent`, `volume_ro_liters`, `effective_water_profile` |
| EC-Budget mit CalMag | `POST /ec-budget` | `ec_calmag > 0`, CalMag in Dosierungen als erstes |
| TankFillEvent Kaskade | `POST /tanks/{key}/fill-events` | `water_defaults_source` korrekt gesetzt |
| NutrientPlan-Validierung | `POST /nutrient-plans/{key}/validate` | EC-Budget-Check pro Phase-Entry |

---

## 14. Implementierungshinweise

<!-- Quelle: Agrarbiologie-Review H-004, H-005 -->

### 14.1 Datenquellen für `ec_contribution_per_ml`

Das Feld `Fertilizer.ec_contribution_per_ml` ist der kritischste Eingabewert für die Dosierungsberechnung. Quellen in absteigender Genauigkeit:

1. **Eigene Messung:** 1 ml des Düngers in 1 L RO-Wasser auflösen, EC messen → exakteste Methode
2. **Hersteller-Datenblätter:** GHE, Canna, Plagron, Advanced Nutrients veröffentlichen EC-Tabellen
3. **Seed-Daten im System:** `seed_fertilizers.py` und `seed_plagron.py` enthalten vorbelegte Werte für gängige Produkte
4. **Community-Werte:** Hydro-Foren als Näherung (geringste Genauigkeit)

Der Nutzer kann alle Werte überschreiben. Selbst gemessene Werte werden im UI als "verifiziert" markiert.

### 14.2 Wasserhärte-Einheiten

In deutschsprachigen Ländern ist `°dH` (Deutsche Härte) gebräuchlicher als `ppm CaCO₃`:

```
1 °dH = 17.9 mg/L CaCO₃ = 17.9 ppm CaCO₃
```

Das System sollte im Onboarding (REQ-020) und bei der Wasserprofilerfassung beide Einheiten als Eingabe akzeptieren und intern in `ppm CaCO₃` umrechnen. Deutsche Trinkwasserberichte liefern häufig `mmol/L` oder `°dH`.

### 14.3 Mischprotokoll-Wassertemperatur

Die Vorgabe 18–22°C für das Ausgangswasser (§7 Mischprotokoll) ist fachlich begründet:
- **< 18°C:** Nährsalze lösen sich schlechter, besonders CalMag und Silikate
- **18–22°C:** Optimaler Bereich für Salzlöslichkeit und gelösten Sauerstoff (>8.5 mg/L)
- **> 22°C:** Gelöster Sauerstoff sinkt, Pythium-Risiko steigt (Wurzelfäule-Erreger, Oomycet)
- **> 26°C:** Kritisch für Hydroponik, anaerobe Wurzelzonen möglich

Dieser Wert ist keine beliebige Konfiguration, sondern eine agrobiologische Konstante.

---

## 15. Abgrenzung

| Aspekt | In diesem Dokument | Nicht in diesem Dokument |
|--------|-------------------|--------------------------|
| EC-Mischungsberechnung (linear) | ✓ Formal definiert | |
| pH-Mischungsberechnung (logarithmisch) | ✓ Formal definiert | |
| EC-Temperaturkorrektur (EC@25) | ✓ Spezifiziert | |
| Dünger-Dosierungsformel (Rezept-Skalierung) | ✓ Formal definiert | |
| EC-Obergrenze-Validierung (phasen-/substrat-/tanktyp-abhängig) | ✓ Formal definiert | |
| CalMag-Korrektur + Ca/Mg-Verhältnis-Check | ✓ Formal definiert | |
| Silizium-Priorisierung im EC-Budget | ✓ Formal definiert | |
| Salzakkumulation / Runoff-Monitoring | ✓ Spezifiziert | |
| Flushing-Protokoll | | REQ-004 FlushingProtocol |
| Organische Freiland-Düngung (g/m²) | | REQ-004 §Organische Freiland-Düngung |
| Living Soil Düngestrategie | Verweis (§4.2) | REQ-004 §Organische Freiland-Düngung |
| Misch-Sicherheit (Inkompatibilitäten) | | REQ-004 MixingSafetyValidator |
| Tank-Alerts (pH, Temp, Algen) | | REQ-014 TankEngine.check_alerts |
| WateringSchedule (Gießplan) | | REQ-004 WateringSchedule |
| Sensor-Datenerfassung | | REQ-005 Hybrid-Sensorik |
| Gelöster Sauerstoff (DO) | Hinweis (Mischprotokoll) | REQ-005/REQ-014 |
