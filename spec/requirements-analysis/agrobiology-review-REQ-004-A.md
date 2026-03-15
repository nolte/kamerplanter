# Agrarbiologisches Anforderungsreview — REQ-004-A EC-Budget-Kalkulation

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Indoor-Anbau, Hydroponik, Coco, Soilless — EC-Budget-Berechnung, Wassermischung, Dünger-Dosierung
**Analysiertes Dokument:** `spec/req/REQ-004-A_EC-Budget-Kalkulation.md` (v1.0)
**Kontext-Dokumente:** `spec/req/REQ-004_Duenge-Logik.md` (v3.2), `spec/req/REQ-002_Standortverwaltung.md` (v4.2), `src/backend/app/domain/engines/water_mix_engine.py`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Mathematische Korrektheit | 4/5 | Grundformeln korrekt, aber pH-Mischung und Temperaturabhängigkeit fehlen |
| Biologische Korrektheit der EC-Limits | 3/5 | Coco-Obergrenzen zu niedrig, Living Soil-Logik problematisch |
| CalMag-Korrekturlogik | 3/5 | Konzept korrekt, Zielwerte unvollstaendig, Ca/Mg-Verhaeltnis unklar |
| Vollstaendigkeit der Einflussfaktoren | 3/5 | Temperaturabhaengigkeit, Salzakkumulation, Substrat-CEC fehlen |
| Dosierungsalgorithmus | 2/5 | NPK-Summen-Gewichtung ist wissenschaftlich nicht haltbar |
| Sicherheitslimits | 4/5 | Sinnvoll, aber EC_max_absolute 3.0 mS/cm zu niedrig fuer Stammloesung |
| Praktische Umsetzbarkeit | 4/5 | Pipeline-Konzept solide, API-Design gut durchdacht |

**Gesamteinschaetzung:** REQ-004-A beschreibt eine handwerklich gut strukturierte Berechnungspipeline mit korrekten Grundformeln fuer die Wassermischung und das EC-Budget-Konzept. Der groesste fachliche Mangel liegt im Dosierungsalgorithmus (Stufe 3): Die proportionale Verteilung nach NPK-Gesamtsumme bildet nicht ab, wie Ionen tatsaechlich zur elektrischen Leitfaehigkeit beitragen — und fuehrt in der Praxis zu signifikanten Abweichungen vom Ziel-EC. Darueber hinaus fehlen drei praxisrelevante Korrekturfaktoren vollstaendig: Temperaturabhaengigkeit des EC-Werts, Salzakkumulation im Substrat und die Kationenaustauschkapazitaet (CEC) erdgebundener Substrate. Die EC-Obergrenzen fuer Coco sind nach aktuellem Forschungsstand zu konservativ. Alle Punkte sind behebbar ohne Architekturanpassung.

---

## Fachlich Falsch — Sofortiger Korrekturbedarf

### F-001: NPK-Summen-Gewichtung bildet EC-Beitrag physikalisch falsch ab

**Anforderung (Stufe 3, §5.2):**
```
npk_weight_i = N_i + P_i + K_i
share_i = npk_weight_i / total_npk
ec_allocation_i = EC_net * share_i
```

**Problem:** Die elektrische Leitfaehigkeit einer Nährlösung haengt von der Ionenkonzentration und der spezifischen Ionenleitfaehigkeit der geloesten Salze ab, nicht von der NPK-Prozentangabe auf dem Etikett. Ein Dünger mit `N=5, P=0, K=1` (NPK-Summe 6) und ein Dünger mit `N=2, P=1, K=6` (NPK-Summe 9) haben fundamental unterschiedliche EC-Beitraege pro Milliliter — nicht wegen ihrer NPK-Summe, sondern wegen ihrer Salzformen (Kaliumnitrat vs. Monokaliumphosphat vs. Calciumnitrat). Stickstoff liegt je nach Produkt als Nitrat (NO3-), Ammonium (NH4+) oder Harnstoff vor. Nitrat fuehrt bei gleicher ppm-Zahl zu deutlich mehr EC als Harnstoff, der un-ionisiert ist.

Konkret: Im Praxisbeispiel erhaelt Flora Gro (N=2, P=1, K=6, npk=9) die gleiche EC-Zuteilung wie Flora Bloom (N=0, P=5, K=4, npk=9), obwohl beide Produkte bei gleicher ml/L-Dosierung unterschiedliche EC-Beitraege haben. Das Ergebnis ist falsch — die tatsaechliche EC wird je nach Produktkombination stark vom Zielwert abweichen.

**Korrekte Alternative:** Der einzige zuverlaessige Ansatz ist `ec_contribution_per_ml` direkt zu verwenden, um Dosierungen zu berechnen. Das Feld ist bereits im Datenmodell vorhanden (`Fertilizer.ec_contribution_per_ml`). Der Algorithmus soll das verfuegbare EC-Budget auf Basis der tatsaechlichen EC-Beitraege verteilen, nicht auf Basis der NPK-Etiketten.

**Korrekter Algorithmus — Option A: Gleichgewichtsansatz mit Verhaeltnis-Fixierung**

Wenn ein Nutzer ein bestimmtes Hersteller-Rezept (z.B. GHE Drain-to-Waste 3-2-1 ml/L) als Startpunkt hat, soll das EC-Budget dazu genutzt werden, den Gesamtmassstab zu ermitteln:

```
Gegebenes Verhaeltnis: d_1 : d_2 : d_3 = r_1 : r_2 : r_3  (aus NutrientPlan)
EC_beitrag_bei_skalierung_k = k * (r_1 * ec_1 + r_2 * ec_2 + r_3 * ec_3)

k = EC_net / (r_1 * ec_1 + r_2 * ec_2 + r_3 * ec_3)

d_i = k * r_i
```

Dabei sind `r_i` die relativen Verhaeltnisse der Dosierungen (aus dem NutrientPlan), `ec_i` der `ec_contribution_per_ml`-Wert jedes Duengers. Der Skalierungsfaktor `k` skaliert das gesamte Rezept auf das verfuegbare EC-Budget.

**Korrekter Algorithmus — Option B: Target-EC-Matching ohne Verhaeltnis-Fixierung**

Wenn kein Rezept vorgegeben ist, soll das System anhand der hinterlegten `ml_per_liter`-Werte im `NutrientPlanPhaseEntry` die tatsaechliche EC berechnen und bei Bedarf gleichmaessig skalieren:

```
EC_dosiert = sum(d_i * ec_i)   // tatsaechliche EC der geplanten Dosierungen
skalierung = EC_net / EC_dosiert

d_i_scaled = d_i * skalierung  // alle Dosierungen proportional skalieren
```

Option A ist fuer die Praxis empfehlenswerter, da Hersteller-Rezepte spezifische Verhaeltnisse vorgeben, die bei skalierter Gesamtmenge weiterhin ausgeglichen bleiben.

**Empfehlung:** Bestehenden NPK-Summen-Algorithmus entfernen, durch Option A ersetzen. NPK-Ratio auf dem NutrientPlanPhaseEntry bleibt als Zielwert-Definition erhalten, sollte aber nicht als Gewichtungsfaktor fuer die EC-Verteilung dienen.

**Anbaukontext:** Hydroponik, Coco, Indoor

---

### F-002: Lineare pH-Mischung ist physikalisch falsch ohne korrekten Hinweis

**Anforderung (§3.5):**
> Hinweis: lineare pH-Mischung ist Naeherung, pH ist logarithmisch

**Problem:** Der Hinweis ist vorhanden, aber das System fuehrt die Berechnung trotzdem linear aus. Das ist bei extremen pH-Unterschieden zwischen RO-Wasser (pH 6.5) und Leitungswasser (z.B. pH 8.2) erheblich falsch.

Beispiel: 50% RO-Wasser (pH 6.5) + 50% Leitungswasser (pH 8.2):
- Lineare Berechnung: pH = (6.5 + 8.2) / 2 = 7.35
- Korrekte logarithmische Berechnung:
  - [H+] RO = 10^(-6.5) = 3.16e-7 mol/L
  - [H+] Leitungswasser = 10^(-8.2) = 6.31e-9 mol/L
  - [H+] Mix = (3.16e-7 + 6.31e-9) / 2 = 1.61e-7 mol/L
  - pH Mix = -log10(1.61e-7) = 6.79
  - **Fehler durch lineare Naeherung: 0.56 pH-Einheiten** — das liegt ausserhalb der pH-Toleranz (±0.2) jedes Hydroponik-Systems

**Praktische Konsequenz:** Eine falsch berechnete pH-Vorschau fuehrt dazu, dass der Nutzer zu wenig pH-Down dosiert. Im Beispiel wuerde das System pH 7.35 anzeigen, der echte pH ist 6.79 — der Nutzer wuerde unnoetig pH-Down zugeben und versaeuert die Loesung.

**Korrekte Formel fuer die Implementierung:**
```python
import math

def mix_ph(ph_tap: float, ph_ro: float, ro_percent: float) -> float:
    ratio = ro_percent / 100.0
    h_tap = 10 ** (-ph_tap)
    h_ro = 10 ** (-ph_ro)
    h_mix = h_ro * ratio + h_tap * (1 - ratio)
    return -math.log10(h_mix)
```

**Empfehlung:** Die pH-Berechnung in `WaterMixCalculator.calculate_effective_water` auf logarithmische Mischung umstellen. Der bestehende Code in `water_mix_engine.py` (Zeile 62: `ph=round(ro.ph * ratio + tap.ph * tap_ratio, 2)`) ist falsch und muss korrigiert werden. Der Hinweis in der Spezifikation genuegt nicht.

**Anbaukontext:** Hydroponik, Coco, Indoor

---

### F-003: Absolute EC-Obergrenze 3.0 mS/cm blockiert Stammloesung

**Anforderung (§5.5):**
```
EC_max_absolute: 3.0 mS/cm  // Absolutes Obergrenze fuer Naehrtanks (TankEngine)
```

**Problem:** Die Anforderung bezieht sich auf Nährtanks im Sinne von REQ-014. REQ-014 §1 definiert aber explizit `stock_solution` als Tanktyp: "Konzentrierte A/B-Tanks (100x-200x) fuer automatisierte Dosierung (REQ-018). EC 50-200+ mS/cm." Eine Stammloesung hat einen EC von 50 bis ueber 200 mS/cm. Das Limit von 3.0 mS/cm wuerde bei Validierung jeden Stammloesung-Tank mit einem Fehler oder einer Warnung markieren.

**Empfehlung:** Das Limit `EC_max_absolute = 3.0 mS/cm` explizit auf Tank-Typen `nutrient`, `irrigation` und `recirculation` beschraenken. Fuer `stock_solution` und `reservoir` muss entweder kein EC-Limit gelten oder ein separater, viel hoeherer Grenzwert definiert werden (z.B. 250 mS/cm).

```python
EC_MAX_BY_TANK_TYPE = {
    "nutrient": 3.0,       # fertige Nährloesung
    "irrigation": 1.5,     # Giesswasser mit pH-Korrektur
    "recirculation": 3.0,  # Rezirkulation
    "reservoir": None,     # kein Limit (Rohwasser)
    "stock_solution": 250, # Konzentrat
}
```

**Anbaukontext:** Hydroponik, Indoor

---

## Unvollstaendig — Wichtige Aspekte fehlen

### U-001: Temperaturabhaengigkeit des EC-Werts fehlt

**Anbaukontext:** Hydroponik, Indoor

**Problem:** EC-Messgeraete messen in der Regel bei einer Referenztemperatur von 25°C (EC@25). Nährlösungen haben in der Praxis Temperaturen zwischen 16°C und 28°C. Die meisten digitalen EC-Meter kompensieren automatisch auf 25°C (Temperature Compensation Coefficient, TCC = ca. 2% pro °C fuer waessrige Nährlösungen). Wenn aber:

1. Das Messgeraet ohne Temperaturkompensation misst, oder
2. Der Nutzer einen EC-Wert manuell eingibt, der bei einer anderen Temperatur gemessen wurde

dann ist `EC_measured != EC@25`. Konkret: Eine Lösung mit EC@25 = 2.0 mS/cm hat bei 18°C gemessene ca. 1.72 mS/cm (etwa 14% Abweichung). Ein Gärtner der bei kaltem Wasser (18°C) misst und 1.72 mS/cm abliest, wuerde aufduengen und landet am Ende bei EC@25 = 2.3 mS/cm — ausserhalb der Phasengrenzen.

**Fehlende Anforderungen:**
- Feld `measurement_temperature_celsius: Optional[float]` auf `FeedingEvent.measured_ec_before/after`
- Formel zur Temperaturkorrektur: `EC@25 = EC_measured / (1 + 0.02 * (T - 25))`, wobei T in °C
- Hinweis im UI wenn keine Temperaturkompensation aktiviert ist (z.B. bei manueller EC-Eingabe)
- Warnung wenn Nährlösung-Temperatur ausserhalb 18-22°C liegt (Algenwachstum >24°C, geloester Sauerstoff sinkt)

**Formulierungsvorschlag:**
```
EC_korrigiert_bei_25 = EC_gemessen / (1 + 0.02 * (T_gemessen - 25))
```

Wenn `T_gemessen` nicht bekannt: Das System zeigt einen Info-Hinweis: "Bitte messen Sie EC bei 25°C oder aktivieren Sie die automatische Temperaturkompensation Ihres Messgeraets."

---

### U-002: Salzakkumulation und Substrat-Pufferwirkung fehlen

**Anbaukontext:** Coco, Soil, Indoor

**Problem:** Die Berechnung behandelt die Nährlösung als isoliertes System. In der Praxis akkumulieren sich Salze im Substrat (Salt Build-Up). Folgende Effekte fehlen vollstaendig:

**Salzakkumulation (Salt Run-Away):**
- Bei jedem Giessvorgang bleibt ein Anteil der Nährsalze im Substrat
- Ohne regelmaessigen Drain-to-Waste oder Flush steigt der EC im Substrat ueber den EC der Nährlösung hinaus
- Faustregel Coco Drain-to-Waste: Ablauf-EC (runoff_ec) soll max. 10-15% ueber der Eingangs-EC liegen
- Bei `runoff_ec / input_ec > 1.3` ist ein Flush empfohlen, bei > 1.5 dringend noetig
- Das System erfasst `FeedingEvent.runoff_ec`, aber es gibt keine Warnlogik die auf akkumulierten Salzdruck hinweist

**Fehlende Anforderungen:**
- Runoff-EC-Ratio als abgeleiteter Wert: `runoff_ratio = runoff_ec / input_ec`
- Warnung wenn `runoff_ratio > 1.3` fuer drei aufeinanderfolgende Messungen
- Empfehlung fuer Flush-Intervall basierend auf Substrattyp und Runoff-Trend
- Dokumentation des EC-Drift-Trends in der Befüllungshistorie

**Substrat-CEC (Kationenaustauschkapazitaet):**
- Coco hat eine moderate CEC und puffert Kalzium und Magnesium vorab
- Frisches Coco bindet im ersten Durchlauf verstaerkt Ca2+ aus der Nährlösung ("Ca-Hunger von Coco")
- Das erklaert, warum frisches Coco grundsaetzlich mehr CalMag benoetigt als wiederverwertetes Coco
- Living Soil hat eine hohe CEC (Huminstoffe) — der EC der Nährlösung bildet die tatsaechliche Verfuegbarkeit im Substrat nicht ab

**Fehlende Anforderungen:**
- Flag `substrate_is_new: bool` oder `substrate_reuse_cycle: int` (bereits in REQ-019 als `reuse_count` vorhanden)
- Wenn `substrate_is_new` und Substrat=Coco: Erhoehte CalMag-Empfehlung fuer ersten Giesszyklus ("Coco buffern")
- Hinweis in der Spezifikation: "EC-Zielwerte gelten fuer die applizierte Nährlösung, nicht fuer den EC im Substrat. Der EC im Substrat kann je nach CEC und Giessstrategie erheblich abweichen."

---

### U-003: CalMag-Zielwerte unvollstaendig und Verhaeltnis nicht spezifiziert

**Anbaukontext:** Hydroponik, Coco, Indoor

**Problem:** Die Tabelle in §3.6 gibt phasenabhaengige Ca- und Mg-Zielwerte vor, hat aber zwei fachliche Luecken:

**Luecke 1: Substrat-Unterschiede fehlen**

| Phase | Ca_target (ppm) | Mg_target (ppm) |
|-------|----------------|-----------------|
| Seedling | 80 | 30 |
| Vegetative | 150 | 50 |
| Flowering | 120 | 40 |

Diese Werte gelten in dieser Hoehe ausschliesslich fuer Hydroponik (DWC, NFT). Fuer Coco gelten andere Zielwerte:

| Phase | Ca (Hydro) | Ca (Coco) | Mg (Hydro) | Mg (Coco) |
|-------|-----------|-----------|-----------|-----------|
| Seedling | 80 ppm | 60 ppm | 30 ppm | 20 ppm |
| Vegetative | 150 ppm | 120 ppm | 50 ppm | 40 ppm |
| Flowering | 120 ppm | 100 ppm | 40 ppm | 30 ppm |

Hintergrund: In Coco puffert das Substrat Ca2+, sodass die Pflanze mehr Ca aus dem Substrat beziehen kann als bei reiner Hydroponik. Bei zu hoher externer Ca-Zufuhr entsteht antagonistischer Antagonismus mit Mg (Ca blockiert Mg-Aufnahme).

**Luecke 2: Ca/Mg-Verhaeltnis wird nicht geprueft**

Das ideale Ca:Mg-Verhaeltnis in der Nährlösung liegt bei 3:1 bis 4:1 (ppm). Wenn ein CalMag-Supplement nur das Ca-Defizit ausgleicht aber das Mg-Defizit ignoriert (oder umgekehrt), kann das Verhaeltnis in einen antagonistischen Bereich geraten:
- Ca:Mg > 5:1 → Mg-Aufnahmehemmung (Magnesiummangel-Symptome trotz ausreichend Mg)
- Ca:Mg < 2:1 → Ca-Aufnahmehemmung

**Ergaenzende Anforderung:**
```
Ca_Mg_ratio = Ca_mix / Mg_mix  (nach CalMag-Zugabe)
WENN Ca_Mg_ratio < 2.0 ODER Ca_Mg_ratio > 5.0:
    WARNUNG: "Ca/Mg-Verhaeltnis ({ratio:.1f}:1) ausserhalb des optimalen Bereichs (3:1 bis 4:1).
             Ueberpruefen Sie die CalMag-Dosierung."
```

**Luecke 3: Schwellenwert fuer CalMag-Empfehlung zu pauschal**

```
Ca_deficit > 10 ppm ODER Mg_deficit > 5 ppm → CalMag-Supplement empfohlen
```

Diese Schwelle gilt unabhaengig vom Substrat und der Phase. Ein Coco-Gärtner in der Seedling-Phase mit RO-Wasser hat immer ein Ca-Defizit > 10 ppm — die Empfehlung waere dauerhaft an, auch wenn die EC-Budgetlage es nicht erlaubt. Die Empfehlung sollte den EC-Spielraum einbeziehen:

```
WENN Ca_deficit > Ca_threshold[substrat][phase]
    UND EC_calmag_minimum ≤ EC_net_verbleibend:
    CalMag-Supplement empfehlen
SONST WENN Ca_deficit > Ca_threshold:
    INFO: "CalMag empfohlen, aber EC-Budget reicht nicht aus. Erhoehen Sie EC_target oder Osmose-Anteil."
```

---

### U-004: Silizium fehlt als separate Dosierungskategorie vor CalMag

**Anbaukontext:** Hydroponik, Coco, Indoor

**Problem:** REQ-004 (§1 Kritische Misch-Reihenfolge) definiert Silizium-Zusaetze als ersten Schritt vor CalMag: "Silizium-Zusaetze (pH-instabil, zuerst!)". REQ-004-A erwaehnt Silizium jedoch an keiner Stelle.

Silizium (SiO4²⁻, Kieselsaure) wird als Kaliumsilikat-Loesung (z.B. Plagron Silic Rock, Aptus Silic Boost) zugegeben. Es hat folgende EC-relevante Eigenschaften:
- Traeght zum EC bei (je nach Produkt ca. 0.05-0.15 mS/cm pro ml/L)
- Muss **vor** CalMag und allen anderen Duengern zugegeben werden, weil es bei direktem Kontakt mit Ca2+ oder Mg2+ ausfallt (Calciumsilikat, wasserunloeslich)
- Erhoeht temporaer den pH erheblich (typisch +0.5 bis +1.5 pH), was die nachfolgende pH-Korrektur beeinflusst
- EC-Beitrag muss als eigenstaendige Vorkategorie wie CalMag vor der NPK-Verteilung abgezogen werden

**Fehlende Anforderungen:**
- Kategorisierung `Fertilizer.type = 'silicate'` (oder Erweiterung des bestehenden Enum `['base', 'supplement', 'booster', 'biological', 'ph_adjuster']` um `'silicate'`)
- Silizium wird mit `mixing_priority = 1` (hoechste Prioritaet, noch vor CalMag) erfasst
- EC-Budget-Abzug fuer Silizium vor CalMag und NPK-Verteilung:
  ```
  EC_silicate = d_si * ec_si
  EC_net_nach_silizium = EC_net - EC_silicate
  EC_net_nach_calmag = EC_net_nach_silizium - EC_calmag
  // Verbleibendes Budget fuer NPK-Dünger
  ```
- Warnung wenn Silizium nach CalMag in der Misch-Reihenfolge erscheint

---

### U-005: Organische Dünger ohne EC-Beitrag werden nicht korrekt ins Budget einbezogen

**Anbaukontext:** Coco, Soil, Indoor

**Problem:** §5.4 beschreibt Dünger ohne EC-Beitrag als biologische Zusaetze die mit `d_i = 0` in der EC-Berechnung beruecksichtigt werden, aber nach Herstellerangabe dosiert werden. Das ist fachlich unvollstaendig:

Organische Fluessigdünger (Fischemulsion, Wurmhumus-Extrakt, Brennnesseljauche) haben einen messbaren EC-Beitrag — dieser ist jedoch sehr variabel und hersteller-/chargenabhaengig. Typische Werte:
- Fischemulsion (5-1-1): ca. 0.08 mS pro ml/L
- Brennnesseljauche (verduennt 1:10): ca. 0.03-0.05 mS pro ml/L
- Komposttee: 0.01-0.1 mS pro ml/L (sehr variabel, abhaengig von Ausgangssubstrat)

Diese Dünger werden als "ec_contribution_per_ml = 0" erfasst weil der genaue Wert unbekannt ist — aber ihr tatsaechlicher EC-Beitrag laesst den Gesamt-EC der Loesung steigen. Das Dokument gibt keine Empfehlung wie damit umzugehen ist.

**Empfehlung:**
- Neues Feld `ec_contribution_uncertain: bool` fuer Dünger mit unbekanntem aber nicht-null EC-Beitrag
- Wenn `ec_contribution_uncertain = True`: Zusaetzliche EC-Reserve im Budget einplanen (empirisch 0.1-0.2 mS als Pauschalpuffer)
- Warnung im UI: "EC-Beitrag dieses organischen Duengers ist variabel und nicht im EC-Budget berechnet. Messen Sie den EC nach Zugabe."
- Mess-Aufforderung in den Mischprotokoll-Schritten: "EC messen und protokollieren" nach jedem organischen Zusatz

---

### U-006: pH-EC-Wechselwirkung bei pH-Down/Up unvollstaendig

**Anbaukontext:** Hydroponik, Indoor

**Problem:** §4.3 schaetzt den EC-Beitrag von pH-Adjustern pauschal mit 0.03 mS/cm pro ml/L. Das ist eine grobe Naeherung ohne Bezug auf das spezifische Produkt.

Tatsaechliche EC-Beitraege gaengiger pH-Adjuster:
- pH-Down (Phosphorsaeure H3PO4, 85%): ca. 0.10-0.15 mS pro ml/L
- pH-Down (Zitronensaeure): ca. 0.05-0.08 mS pro ml/L
- pH-Up (Kaliumhydroxid KOH): ca. 0.12-0.18 mS pro ml/L
- pH-Up (Kaliumbicarbonat KHCO3): ca. 0.08-0.12 mS pro ml/L

Phosphorsaeure-basiertes pH-Down fuehrt dem System gleichzeitig Phosphat zu, was den Phosphor-Spiegel erhoeht (relevant bei hohem P-Niveau in der Blutephase). Kaliumhydroxid-basiertes pH-Up erhoet den Kaliumgehalt.

**Empfehlung:**
- pH-Adjuster als regulaere `Fertilizer`-Eintraege mit `type = 'ph_adjuster'` und definiertem `ec_contribution_per_ml`
- NPK-Zusatzeintrag fuer Phosphorsaeure (Phosphateintrag) und KOH (Kaliumeintrag)
- Die pauschale Reserve-Berechnung in §4.3 als Fallback beibehalten, wenn kein pH-Adjuster-Produkt definiert ist

---

## Zu Ungenau — Praezisierung noetig

### P-001: EC-Obergrenzen fuer Coco und Living Soil sind fachlich ueberholt

**Anforderung (§4.2):**
```
coco: Seedling 0.6-0.8, Vegetative 1.2-1.6, Flowering 1.4-1.8
living_soil: Seedling 0.0-0.4, Vegetative 0.4-0.8, Flowering 0.6-1.0
```

**Problem Coco:** Die Obergrenzen fuer Coco liegen zu niedrig verglichen mit dem aktuellen Stand der Praxis und der Literatur. Coco hat eine sehr gute Pufferwirkung und erlaubt hoehere EC-Werte als Erde, aber niedrigere als Hydroponik (DWC). Aktuelle Empfehlungen fuehrender Coco-Hersteller (Plagron, Canna, Dutch Pro):

| Phase | Empfehlung Spezifikation | Tatsaechlicher Praxisbereich |
|-------|--------------------------|------------------------------|
| Seedling (Coco) | 0.6-0.8 mS | 0.8-1.0 mS (Hersteller) |
| Vegetative (Coco) | 1.2-1.6 mS | 1.6-2.0 mS (Coco + gute Drainage) |
| Flowering (Coco) | 1.4-1.8 mS | 1.8-2.4 mS (Blüte-Boost-Phase) |

Niedrige EC in Coco ist praxisschaaedlich: Coco wird oft 2-4x taeglich gewaessert (Saettp-und-Drainageprinzip), und bei jeder Drainage gehen Nährsalze verloren. Eine EC von 1.4 mS in der Blutephase fuehrt bei Coco mit 30% Drain-to-Waste zu chronischem Nährstoffmangel.

**Problem Living Soil:** Ein EC-Wert nahe 0 fuer Living Soil Lösungen ist korrekt — aber die Anforderung sollte erklaeren, **warum**: Living Soil ist ein biologisch aktives System. Mineralische Nährsalze stören das Mikrobiom, das durch Mineralisation organischer Substanz die Nährstoffe bereitstellt. Ein EC von 0 bedeutet nicht "Pflanze bekommt nichts", sondern "Nährstoffe kommen aus dem Boden, nicht aus der Giessloesung". Dieser konzeptionelle Unterschied fehlt in der Spezifikation vollstaendig.

**Korrekturregel fuer Living Soil:** Anstatt eines EC-Limits sollte gelten: Bei `substrate_type = 'living_soil'` soll das System:
1. Keine EC-Budget-Berechnung durchfuehren (kein Dünger-Dosierungsalgorithmus)
2. Stattdessen auf REQ-004 §Organische Freiland-Düngung verweisen (Komposttee, g/m², Top Dress)
3. Einen Informationstext anzeigen: "Living Soil arbeitet mit biologischer Mineralisation. EC-basierte Dosierung ist nicht geeignet. Verwenden Sie das organische Düngeprogramm."

**Korrigierte EC-Obergrenzen-Tabelle:**

| Substrat | Seedling | Vegetative | Flowering | Flush |
|----------|----------|------------|-----------|-------|
| `hydro_solution` (DWC/NFT) | 0.8-1.2 | 1.6-2.4 | 1.8-2.8 | 0.0 |
| `coco` | 0.8-1.0 | 1.6-2.0 | 1.8-2.4 | 0.0 |
| `soil` | 0.4-0.6 | 0.8-1.4 | 1.0-1.6 | 0.0 |
| `living_soil` | Nicht anwendbar | Nicht anwendbar | Nicht anwendbar | — |

Anmerkung: Bei DWC-Systemen (Deep Water Culture) koennen erfahrene Gärtner in der Blütephase bis 3.0 mS/cm gehen. Die Obergrenze ist aber von der Sorte, der Wassertemperatur und dem Sauerstoffgehalt abhaengig und soll als "erweitert" gekennzeichnet sein.

---

### P-002: Sicherheitslimit 20 ml/L pro Dünger ist zu hoch fuer konzentrierte Produkte

**Anforderung (§5.5):**
```
max_ml_per_liter: 20 ml/L  // Absolutes Maximum pro Duenger
```

**Problem:** 20 ml/L ist fuer viele handelsübliche Dünger eine extreme Ueberdosierung. Gaengige Hochkonzentrat-Produkte (z.B. General Hydroponics FloraSeries, Canna Terra Flores) werden in der Praxis mit 2-8 ml/L dosiert. 20 ml/L wuerde bei den meisten Produkten zu schwerem osmotischem Stress fuehren und potentiell zum Absterben der Pflanzen.

Das Limit ist nur sinnvoll fuer sehr schwach konzentrierte organische Dünger (z.B. verdünnte Jauche 1:10 mit 5 ml/L Zugabe) oder Substrate-Zusaetze wie Enzyme.

**Empfehlung:** Das Limit von 20 ml/L durch ein produktabhaengiges Limit ersetzen:

```
Fertilizer.max_dose_ml_per_liter: Optional[float]  // vom Hersteller angegeben
SYSTEM_ABSOLUTE_MAX: 20 ml/L  // nur als Systemweite Obergrenze wenn kein Hersteller-Limit
```

Wenn das `max_dose_ml_per_liter`-Feld im Fertilizer-Katalog hinterlegt ist, wird dieses Limit fuer die Warnung verwendet. Das System-Maximum von 20 ml/L gilt nur als Catchall fuer Produkte ohne Herstellerangabe.

---

### P-003: EC_tolerance von 0.3 mS/cm ist fuer Seedlings zu gross

**Anforderung (§5.3):**
```
EC_tolerance = 0.3 mS/cm (konfigurierbar)
```

**Problem:** Eine Toleranz von 0.3 mS/cm ist fuer Kemlinge und Jungpflanzen (EC-Ziel: 0.6-1.0 mS/cm) zu gross. Wenn das Ziel 0.8 mS betraegt und die Toleranz 0.3 mS, koennte die Nährloesung 1.1 mS haben bevor eine Warnung erscheint — das entspricht bereits einer Ueberdosierung von 37.5% gegenueber dem Seedling-Zielwert.

**Empfehlung:** Relative Toleranz statt absoluter Toleranz, oder phasenabhaengige Toleranz:

```python
EC_TOLERANCE_ABSOLUTE = 0.1   # Seedling (enger Bereich, hohe Empfindlichkeit)
EC_TOLERANCE_ABSOLUTE = 0.2   # Vegetative
EC_TOLERANCE_ABSOLUTE = 0.3   # Flowering, Fruchtgemüse
```

Oder als relativer Ansatz:
```
EC_tolerance_relative = EC_target * 0.10  # ±10% des Zielwerts
EC_tolerance = max(0.1, EC_tolerance_relative)  # Mindest-Toleranz 0.1 mS
```

---

### P-004: Flush-EC von 0.0 mS ist zu absolut formuliert

**Anforderung (§4.2):**
```
Flush: 0.0 (alle Substrate)
```

**Problem:** EC = 0.0 bedeutet reines RO-Wasser ohne jegliche Ionen. In der Praxis wird selbst beim Flushen kein absolut reines Wasser verwendet, da:

1. Voellig ionenfreies Wasser (EC 0.0) erzeugt einen extremen osmotischen Gradienten, der Wurzelzellen schrumpfen laesst (Turgor-Verlust)
2. pH-Korrektur des Flush-Wassers ist noetig (RO-Wasser ist oft mild sauer, pH 5.5-6.5 ist in Ordnung)
3. Ein milder Enzymatiker (z.B. Plagron Plant Wash) im Flush-Wasser ist gaengige Praxis und fuehrt zu EC 0.01-0.05 mS

**Korrekte Formulierung:**
```
Flush: EC 0.0-0.3 mS/cm
```
Erlaubt pH-Korrektur und Enzymzusatz, ohne Mineral-Dünger. Das REQ-004 FlushingProtocol sollte diese Spannbreite definieren.

---

### P-005: API-Response fuer /water-mix gibt ph als lineare Berechnung zurueck

**Anforderung (§10.2, Response-Beispiel):**
```json
"ph": 6.67
```

**Problem:** Der Response-Wert `ph: 6.67` ist das Ergebnis der linearen Mischungsberechnung (Fehler F-002). Das API-Beispiel perpetuiert den Fehler. Nach Korrektur auf logarithmische pH-Mischung wuerde dieser Wert anders sein und sollte im Beispiel aktualisiert werden.

---

## Hinweise und Best Practices

### H-001: Runoff-Monitoring als integraler Bestandteil der EC-Bilanz

Das System erfasst `FeedingEvent.runoff_ec` und `FeedingEvent.runoff_ph`, aber es gibt keine Logik, die Runoff-Daten mit der Eingabe-EC verknuepft und einen EC-Drift-Trend erkennt. Dies ist ein wesentliches Werkzeug fuer professionelles Coco- und Erde-Management:

- **Runoff-EC-Ratio:** `runoff_ec / input_ec` — zeigt Salzakkumulation oder Auswaschung an
- **pH-Drift im Runoff:** Indikator fuer Substrat-Versauerung (haeufig bei Coco ohne ausreichend CalMag) oder Alkalisierung (bei hartem Wasser mit hoher Alkalinitat)
- **Trend-Analyse ueber mehrere Giessevents:** Wenn Runoff-EC dauerhaft > Input-EC, Flush empfehlen

Empfehlung: Celery-Task der nach 3 aufeinanderfolgenden FeedingEvents mit `runoff_ratio > 1.3` eine Flush-Aufgabe erstellt (via REQ-006 Aufgabenplanung).

### H-002: Sauerstoffgehalt der Nährloesung (DO) als fehlende Dimension

Fuer Hydroponik-Systeme (DWC, NFT) ist der geloeste Sauerstoff (Dissolved Oxygen, DO) ein mindestens so wichtiger Parameter wie EC und pH. Er ist direkt von der Wassertemperatur abhaengig:

| Temperatur | DO-Saettigungswert |
|------------|-------------------|
| 18°C | 9.5 mg/L |
| 22°C | 8.7 mg/L |
| 25°C | 8.3 mg/L |
| 28°C | 7.8 mg/L |

Unterhalb von 5 mg/L O₂ entstehen anaerobe Zonen an der Wurzeloberflaeche, die Pythium-Wurzelfaeule (Oomycet, oft faelschlich als "Pilz" bezeichnet) foerdern. REQ-004-A sollte — im Zusammenhang mit der Temperaturangabe fuer die Wassermischung (§7 Mischprotokoll: "18-22°C") — einen Hinweis auf den optimalen DO-Bereich und dessen Temperaturabhaengigkeit enthalten.

### H-003: Mischprotokoll-Temperaturangabe ist korrekt, aber Begruendung fehlt

§7 Mischprotokoll schreibt "18-22°C" fuer das Ausgangswasser vor. Dies ist korrekt — bei tieferen Temperaturen loesen sich Nährsalze schlechter, bei hoeheren Temperaturen sinkt der DO. Die Anforderung sollte die Begruendung enthalten um zu verhindern, dass Implementierende diesen Wert als beliebig konfigurierbar behandeln.

### H-004: Empfohlene Datenquellen fuer ec_contribution_per_ml

Das Feld `Fertilizer.ec_contribution_per_ml` ist im System vorhanden, aber die Spezifikation gibt nicht an, wie Nutzer an diese Werte kommen. In der Praxis:
- Hersteller-Datenblaetter (z.B. Masterblend, GHE, Canna) enthalten oft EC-Tabellen mit mS/cm pro ml/L
- Eigene Messung: 1 ml/L in 1 L RO-Wasser auflösen, EC messen — exakteste Methode
- Forenbefunde (HydroponicsWorld, THCFarmer, Autoflower Network) als Naeherung

**Empfehlung:** Ein Seed-Datensatz fuer gaengige Dünger mit gemessenen `ec_contribution_per_ml`-Werten sollte im System enthalten sein (analog zu `seed_plagron.py` im Backend). Der Nutzer sollte diese Werte ueberschreiben koennen.

### H-005: Wasserhärte-Einheiten-Konfusion vermeiden

Das System verwendet `gh_ppm` und `alkalinity_ppm` (CaCO3-aequivalent). In deutschsprachigen Laendern ist jedoch der Wert in `°dH` (Deutsche Haerte) gebraeuchlicher:
- 1 °dH = 17.9 mg/L CaCO3 = 17.9 ppm CaCO3

Viele deutsche Trinkwasser-Analysen liefern die Carbonathaerte in `mmol/L` oder `°dH`. Das System sollte:
- Eine Umrechnungshilfe im Onboarding anbieten (`°dH × 17.9 = ppm CaCO3`)
- Oder beide Einheiten als Eingabeoption akzeptieren und intern in ppm CaCO3 umrechnen

---

## Parameter-Uebersicht: Fehlende oder fehlerhafte Werte

| Parameter | Status | Problem | Prioritaet |
|-----------|--------|---------|-----------|
| `ec_contribution_per_ml` als alleinige Gewichtungsgrundlage | Fehlt | NPK-Summen-Gewichtung ist falsch (F-001) | Hoch |
| pH-Mischungsformel (logarithmisch) | Falsch implementiert | Lineare Naeherung (F-002) | Hoch |
| `EC_max_absolute` Unterscheidung nach Tank-Typ | Fehlt | Stock Solution wird falsch behandelt (F-003) | Hoch |
| Temperaturkorrektur EC@25 | Fehlt | Messfehler bei Temperaturschwankungen (U-001) | Hoch |
| Runoff-EC-Ratio und Salzakkumulation | Fehlt | Kein Drift-Tracking (U-002) | Mittel |
| Substrat-CEC-Hinweis fuer frisches Coco | Fehlt | Praxisfehler bei Erstbefuellung (U-002) | Mittel |
| Ca/Mg-Verhaeltnis-Check | Fehlt | Antagonismus-Risiko (U-003) | Mittel |
| Substratabhängige Ca/Mg-Zielwerte | Fehlt | Einheitswerte fuer Hydro/Coco falsch (U-003) | Mittel |
| Silizium als eigene Budget-Kategorie | Fehlt | Ausfaellungsrisiko bei falscher Reihenfolge (U-004) | Mittel |
| `max_dose_ml_per_liter` pro Dünger | Fehlt | Pauschal-Limit 20 ml/L zu hoch (P-002) | Mittel |
| Phasenabhaengige EC-Toleranz | Zu pauschal | 0.3 mS bei Seedling zu gross (P-003) | Niedrig |
| Coco EC-Obergrenzen | Zu konservativ | Praxisbetrieb nicht abgedeckt (P-001) | Mittel |
| Living Soil Sonderlogik | Fehlt | EC-Budget nicht anwendbar (P-001) | Mittel |
| DO (geloester Sauerstoff) | Fehlt | Kritisch fuer Hydro-Systeme (H-002) | Niedrig |

---

## Zusammenfassende Korrekturprioritaeten

### Prioritaet 1 — Vor Implementierung korrigieren

1. **F-001** — Dosierungsalgorithmus auf EC-basierten Skalierungsansatz umstellen (NPK-Summen-Gewichtung entfernen)
2. **F-002** — pH-Mischungsformel in `water_mix_engine.py` auf logarithmische Berechnung korrigieren
3. **F-003** — `EC_max_absolute`-Limit nach Tank-Typ differenzieren

### Prioritaet 2 — Vor dem ersten produktiven Einsatz erwaendern

4. **U-001** — Temperaturabhaengigkeit des EC erwaehnen, `measurement_temperature` als optionales Feld hinzufuegen
5. **P-001** — EC-Obergrenzen-Tabelle fuer Coco anpassen, Living Soil als Sonderfall ausweisen
6. **U-003** — Ca/Mg-Verhaeltnis-Check ergaenzen und substratspezifische CalMag-Zielwerte differenzieren

### Prioritaet 3 — In weiterer Iteration

7. **U-002** — Salzakkumulation/Runoff-Monitoring-Logik spezifizieren
8. **U-004** — Silizium als eigenstaendige Misch-Kategorie mit Misch-Prioritaet 0 vor CalMag
9. **P-002** — `max_dose_ml_per_liter` als Fertilizer-Feld, Pauschal-Limit als Systemweiten Catchall

---

## Glossar (kontextspezifisch fuer dieses Dokument)

- **EC@25:** Elektrische Leitfaehigkeit normiert auf 25°C Wassertemperatur — der internationale Referenzwert fuer Nährlösungen. Abweichungen durch Temperatur werden mit einem Korrekturfaktor von ca. 2% pro °C ausgeglichen.
- **CEC (Kationenaustauschkapazitaet):** Faehigkeit eines Substrats, Kationen (Ca²⁺, Mg²⁺, K⁺, NH₄⁺) zu binden und gegen Protonen (H⁺) auszutauschen. Hoch bei Coco, sehr hoch bei Living Soil, gering bei Perlite/Blahton.
- **Salt Run-Away:** Progressive Anreicherung von Nährsalzen im Substrat ueber mehrere Giesszyklen — erkennbar am steigenden Runoff-EC-Verhaeltnis gegenueber der Eingabe-EC.
- **Runoff-EC-Ratio:** `runoff_ec / input_ec` — Indikator fuer Salzakkumulation im Substrat. Optimal 1.0-1.1; ab 1.3 Flush empfohlen; ab 1.5 dringend noetig.
- **DO (Dissolved Oxygen / geloester Sauerstoff):** Sauerstoffgehalt der Nährloesung in mg/L. Unter 5 mg/L entstehen anaerobe Bedingungen, die Wurzelfaeule foerdern. Optimal 7-9 mg/L, temperaturabhaengig.
- **Antagonismus (Nährstoffe):** Hemmung der Aufnahme eines Naehrstoffs durch zu hohe Konzentration eines anderen. Relevant: Ca blockiert Mg und K; K blockiert Ca und Mg; Fe blockiert Mn und Zn bei hohem pH.
- **Silizium-Ausfaellung:** Calciumsilikat (CaSiO₃) und Magnesiumsilikat sind wasserunloeslich. Wenn Kaliumsilikat-Loesung mit Ca²⁺ oder Mg²⁺ in Kontakt kommt, faellt ein weisser Niederschlag aus. Deshalb muss Silizium als erstes ins Wasser, vor CalMag.
- **TCC (Temperature Compensation Coefficient):** Korrekturfaktor fuer EC-Messgeraete, typisch ~2% pro °C. Die meisten digitalen EC-Meter kompensieren automatisch auf EC@25.
- **Drain-to-Waste (DTW):** Bewässerungsstrategie bei der das Drainagewasser nicht rezirkuliert wird. Typisch 10-30% Drainage zur Verhinderung von Salzakkumulation. Im Gegensatz zu Rezirkulations-Systemen (NFT, DWC).
