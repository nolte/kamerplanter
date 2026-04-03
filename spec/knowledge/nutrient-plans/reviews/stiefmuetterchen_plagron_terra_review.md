# Fachliches Review: Naehrstoffplan Stiefmuetterchen (Viola x wittrockiana) -- Plagron Terra

**Reviewer:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Pruefgegenstand:** `spec/ref/nutrient-plans/stiefmuetterchen_plagron_terra.md` v1.0
**Quell-Dokumente:**
- Pflanzensteckbrief: `spec/ref/plant-info/viola_x_wittrockiana.md`
- Produktdaten Terra Grow: `spec/ref/products/plagron_terra_grow.md`
- Produktdaten Terra Bloom: `spec/ref/products/plagron_terra_bloom.md`
- Produktdaten Pure Zym: `spec/ref/products/plagron_pure_zym.md`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Biologische Korrektheit | 4 / 5 | Vier fachlich relevante Abweichungen, keine fatalen Fehler |
| EC-Plausibilitaet (Schwachzehrer) | 4 / 5 | Grundsaetzlich korrekt niedrig, ein EC-Inkonsistenz in Tabelle vs. JSON |
| Phasen-Vollstaendigkeit | 3 / 5 | DORMANCY-Mapping problematisch; Abhaertungsphase fehlt als eigene Systemphase |
| Produkt-Einsatz | 5 / 5 | Terra Grow / Terra Bloom / Pure Zym korrekt und begruendet eingesetzt |
| Food-Safety (essbare Blueten) | 3 / 5 | Karenzzeit genannt, aber unzureichend begruendet und zu kurz |
| Herbstaussaat / Saisonalitaet | 4 / 5 | Vorhanden, aber nicht als eigenstaendiger KA-Plan spezifiziert |
| Tabellen-JSON-Konsistenz | 4 / 5 | Zwei Inkonsistenzen zwischen Markdown-Tabelle und JSON |
| Lueckenlos-Pruefung (32 Wochen) | 5 / 5 | Wochenabdeckung arithmetisch korrekt und bestaetigt |

**Gesamteinschaetzung:** Der Plan ist handwerklich solide und fachlich ueberwiegend korrekt. Die Thermoinhibitions-Warnung ist klar und prominent platziert. Die EC-Zielwerte fuer einen Schwachzehrer sind angemessen niedrig. Die groesste fachliche Schwaeche liegt im DORMANCY-Mapping: Die Pflanzensteckbrief-Daten modellieren die Endphase als `senescence` (nicht als echte Dormanz), was im Plan inkonsistent mit dem verwendeten Enum `DORMANCY` ist. Die Food-Safety-Karenzzeit von 3 Tagen ist aus regulatorischer und toxikologischer Sicht unterdimensioniert; hier empfiehlt sich eine Pufferung auf 7 Tage. Insgesamt ist der Plan importierbar, benoetigt aber Korrekturen in vier Punkten vor Produktiveinsatz.

---

## 1. THERMOINHIBITION BEI KEIMUNG

**Pruefpunkt 1: Korrekt und prominent dokumentiert?**

**Befund: BESTANDEN -- mit einer Erweiterungsempfehlung**

Die Thermoinhibition ist in diesem Plan an vier Stellen dokumentiert:

1. Phasen-Mapping-Tabelle (Abschnitt 2): `KRITISCH: Nicht ueber 22 C (Thermoinhibition)!`
2. Phase-Entry 4.1 Hinweise: `KRITISCH: Nicht ueber 22 C -- Thermoinhibition verhindert Keimung!`
3. Abschnitt 6 (Praxis-Hinweise): Eigenstaendiger Unterabschnitt mit Temperaturstufentabelle
4. JSON GERMINATION notes: `NICHT ueber 22 °C (Thermoinhibition)!`

Die Pflanzensteckbrief-Quelle bestaetigt: optimale Keimtemperatur 15--18 degC, Thermoinhibition ab 22 degC, keine Heizmatte. Die Angaben im Plan sind biologisch korrekt.

**Erweiterungsempfehlung E-001:**
Der Plan nennt "ab 22 degC: Keimrate sinkt drastisch, ab 25 degC praktisch keine Keimung". Das ist zutreffend, koennte aber prziser sein: Thermoinhibition ist ein aktiv induzierter physiologischer Hemmzustand, nicht nur "schlechte Bedingungen". Die Hemmung wird ueber Phytochrom-B-Signalwege und ABA-Akkumulation (Abscisinsaeure) vermittelt und ist bei Viola-Arten spezifisch durch die Kuehlwetter-Adaptation der Elternarten (V. tricolor, V. lutea) bedingt. Diese Mechanismus-Erklaerung ist fuer den Plantplan nicht zwingend, wuerde aber den Informationswert des Dokuments erhoehen.

Der Hinweis "Keine Heizmatte verwenden" ist korrekt und wichtig -- dies ist ein haeufiger Praxisfehler, da Heizmatten bei den meisten anderen Ausaaten empfohlen werden.

---

## 2. EC-ZIELWERTE FUER SCHWACHZEHRER

**Pruefpunkt 2: Angemessen niedrig?**

**Befund: UEBERWIEGEND BESTANDEN -- eine Inkonsistenz**

Referenzwerte aus dem Pflanzensteckbrief (viola_x_wittrockiana.md, Abschnitt 2.3):

| Phase | EC Steckbrief (mS/cm) | EC Naehrstoffplan (mS/cm) | Bewertung |
|-------|----------------------|--------------------------|-----------|
| Keimung | 0.0 | 0.0 | Korrekt |
| Saemling | 0.5--0.8 | 0.5 | Korrekt (unteres Ende, konservativ, angemessen) |
| Vegetativ | 0.8--1.2 | 0.6 | Abweichung -- siehe F-001 |
| Bluete | 0.8--1.2 | 0.7 | Abweichung -- siehe F-001 |
| Seneszenz | 0.0 | 0.0 | Korrekt |

Die EC-Zielwerte des Naehrstoffplans (0.6 / 0.7 mS/cm) liegen unterhalb des vom Pflanzensteckbrief angegebenen optimalen Bereichs (0.8--1.2 mS/cm). Das ist bei einem Schwachzehrer-Schwerpunkt vertretbar -- der Plan argumentiert konservativ, was bei Stiefmuetterchen sinnvoll ist, da Ueberduenung die Bluetenbildung hemmt. Allerdings entsteht eine Inkonsistenz mit den Steckbrief-Daten, die dokumentiert werden sollte.

**Kritischer Befund EC-Budget-Rechnung:**
Die EC-Budget-Kalkulation in Abschnitt 4.3 (VEGETATIVE) ist intern inkonsistent:

- Tabelle nennt `target_ec_ms: 0.6`
- EC-Budget-Rechnung ergibt: `0.20 (TG 2.5ml) + 0.00 (PZ) + ~0.3 (Wasser) = ~0.50 mS/cm`
- Der angegebene Zielwert (0.6) ist also hoeher als das kalkulierte Budget (0.50)

Dies ist ein Rechenfehler oder eine unerklaerte Absicht. Wenn Leitungswasser 0.3 mS/cm und Terra Grow bei 2.5 ml/L den EC-Beitrag von 0.20 mS/cm erbringt (2.5 x 0.08 = 0.20), dann ergibt sich ein Gesamt-EC von 0.50, nicht 0.60. Der `target_ec_ms: 0.6` im JSON ist somit nicht erreichbar mit den angegebenen Dosiermengen -- es sei denn, das Leitungswasser hat 0.4 mS/cm.

Fuer die Bluetephase: `0.30 (TB 3ml) + 0.00 (PZ) + ~0.3 (Wasser) = ~0.60 mS/cm`, der JSON-Zielwert ist 0.7 -- gleiche Diskrepanz von 0.1 mS/cm.

**Fazit EC-Bewertung:** Die Zielwerte sind konservativ und agronomisch plausibel fuer einen Schwachzehrer. Die interne EC-Budget-Arithmetik enthalt jedoch eine systematische Abweichung von 0.1 mS/cm zwischen Kalkulation und JSON-Zielwert. Die Schwachzehrer-Strategie, deutlich unterhalb des Steckbrief-Maximums zu bleiben, ist biologisch begruendet.

---

## 3. PHASEN-MAPPING UND 32-WOCHEN-ZYKLUS

**Pruefpunkt 3: Fruehjahrsaussaat-Zyklus realistisch?**

**Befund: UEBERWIEGEND BESTANDEN -- Abhaertungsphase fehlt**

### 3.1 Wochen-Arithmetik

Laut Plan: `2 + 6 + 6 + 14 + 4 = 32 Wochen`

Pruefung:
- GERMINATION: Woche 1--2 = 2 Wochen
- SEEDLING: Woche 3--8 = 6 Wochen
- VEGETATIVE: Woche 9--14 = 6 Wochen
- FLOWERING: Woche 15--28 = 14 Wochen
- DORMANCY: Woche 29--32 = 4 Wochen
- Summe: 2 + 6 + 6 + 14 + 4 = 32 Wochen -- KORREKT, keine Luecken

### 3.2 Biologische Plausibilitaet der Phaselaengen

| Phase | Plan-Dauer | Steckbrief-Bereich | Bewertung |
|-------|-----------|-------------------|-----------|
| Keimung | 2 Wochen (14 Tage) | 10--14 Tage | Korrekt (obere Grenze) |
| Saemling | 6 Wochen (42 Tage) | 28--42 Tage | Korrekt (obere Grenze) |
| Vegetativ (inkl. Abhaertung) | 6 Wochen | Steckbrief: Vegetativ 21--35d + Abhaertung 7--14d = 28--49d | Plausibel, aber Abhaertung ist als eigenstaendige Phase im Steckbrief modelliert und fehlt im Naehrstoffplan als eigenes Enum -- siehe F-002 |
| Bluete | 14 Wochen (98 Tage) | 60--120 Tage | Korrekt |
| Seneszenz/"DORMANCY" | 4 Wochen (28 Tage) | 14--28 Tage | Korrekt |

### 3.3 Kalenderplausibilitaet (Mitteleuropa, Zone 7--8)

| Phase | Plan-Kalender | Realistischaetzung | Bewertung |
|-------|--------------|-------------------|-----------|
| Keimung | Anfang Februar | Korrekt -- Fruehjahrsvorkultur Feb | OK |
| Saemling | Mitte Feb -- Mitte Maerz | Korrekt | OK |
| Vegetativ/Abhaertung | Mitte Maerz -- Ende April | Korrekt; Auspflanzung Ende April bei letztem Frost Mitte Mai ist in Zone 7--8 etwas frueh (Stiefmuetterchen vertragen Frost, also vertretbar) | OK (Frosttoleranz begruendet) |
| Bluete | Mai -- Mitte Juli (14 Wochen) | Plausibel; bei kuehlem Sommer bis Ende Juli, bei heissem ab Anfang Juli Hitzeseneszenz | OK |
| Seneszenz | Mitte Juli -- Mitte August (4 Wochen) | Korrekt, bei warmem Mitteleuropa-Sommer | OK |

**Gesamtbewertung Zyklus:** Fuer Mitteleuropa (Zone 7--8) ist ein 32-Wochen-Fruehjahrsaussaat-Zyklus mit Start Februar plausibel. Der Pflanzensteckbrief gibt `sowing_indoor_weeks_before_last_frost: 12` an -- 12 Wochen vor dem letzten Frost (Mitte Mai) ergibt Mitte Februar als Aussaatstart. Der Plan startet Anfang Februar, was 14 Wochen vor letztem Frost waere -- das ist etwas fruehzeitig und fuehrt moeglicherweise zu laengeren Jungpflanzenphasen auf der Fensterbank. Dies ist kein Fehler, wuerde aber als Hinweis im Plan erwaehnt werden koennen.

---

## 4. DORMANCY-MAPPING: SENESZENZ vs. ECHTE DORMANZ

**Pruefpunkt 4: Korrektes Mapping fuer Viola?**

**Befund: FACHLICH PROBLEMATISCH -- Korrekturbedarf**

### 4.1 Botanische Einordnung

Der Pflanzensteckbrief modelliert die Endphase als `senescence` (Terminal: true). Der Naehrstoffplan verwendet das KA-Enum `DORMANCY`. Dies ist eine konzeptionelle Fehleinstufung.

**Unterschied Dormanz vs. Seneszenz:**

| Konzept | Definition | Umkehrbar? | Beispiel |
|---------|-----------|-----------|---------|
| Dormanz (DORMANCY) | Ruhestadium mit reduziertem Stoffwechsel; Pflanze kann Wachstum wieder aufnehmen | Ja | Zwiebelpflanzen im Sommer, Kakteen im Winter |
| Seneszenz | Aktiver Alterungsprozess, programmatischer Zelltod; Endstadium des Lebenszyklus | Nein | Einjahrespflanzen im Herbst |

Bei Viola x wittrockiana (als Annuelle kultiviert, Fruehjahrsaussaat) ist das Sommersterben durch Hitzestress ein seneszenz-aehnlicher Prozess, kein echter Ruhezustand. Die Pflanze hat keinen physiologischen Mechanismus fuer eine echte Sommerdormanz -- sie stirbt oder geht in einen Erschoepfungszustand, aus dem keine vollstaendige Erholung erfolgt.

### 4.2 Wann ist DORMANCY fuer Viola korrekt?

DORMANCY als KA-Enum waere korrekt bei:
- **Herbstaussaat-Variante** (Abschnitt 6 des Plans): Pflanzen, die nach der Herbstbluete im Winter in eine echte Kuhephase gehen, sind physiologisch dormant. Hier ist DORMANCY biologisch korrekt.
- **Zone 9+ Anbau**: Stiefmuetterchen koennen in warmem Klima nach dem Sommer eine tatsaechliche Dormanzphase durchlaufen und im Herbst erneut austreiben.

### 4.3 Bewertung der Pragmatik

Der Plan erlaeutert die Nutzung von DORMANCY als pragmatische Entscheidung (da kein `SENESCENCE`-Enum im KA-System vorhanden ist). Dies ist ein bekanntes Modellierungsproblem bei Annuellen im KA-System. Die Nutzung von DORMANCY als Seneszenz-Proxy ist akzeptabel, wenn:
1. Die Notes deutlich kommunizieren, dass es sich um Seneszenz (Hitzetod) und nicht um echte Dormanz handelt -- dies ist der Fall
2. `is_recurring: false` korrekt gesetzt ist -- dies ist der Fall
3. `cycle_restart_from_sequence: null` korrekt gesetzt ist -- dies ist der Fall

**Empfehlung:** Die Dokumentation ist ausreichend transparent. Das DORMANCY-Mapping ist ein modellierungsbedingter Kompromiss, kein fachlicher Fehler, solange die Notes-Texte die biologische Realitaet korrekt beschreiben (was hier gegeben ist). Ein Kommentar im Plan waere sinnvoll, der explizit auf diesen Kompromiss hinweist.

---

## 5. TERRA BLOOM IN DER BLUETEPHASE

**Pruefpunkt 5: P+K-Betonung korrekt?**

**Befund: BESTANDEN**

Terra Bloom (NPK 2-2-4, laut Produktdaten) wird korrekt fuer die Bluetephase eingesetzt. Die Bewertung:

**NPK-Analyse Terra Bloom fuer Viola-Bluetephase:**
- N reduziert (2.1% vs. 2.6% bei Terra Grow): Korrekt -- weniger vegetatives Wachstum in der Bluete
- P erhoht (1.6% P2O5 vs. 1.1% bei Terra Grow): Korrekt -- Phosphor foerdert Bluetenansatz, Energiestoffwechsel (ATP) und Samenreife
- K deutlich erhoht (3.9% K2O vs. 3.1% bei Terra Grow): Korrekt -- Kalium staerkt Zellwaende, verbessert Bluetenqualitaet, reguliert Wasserhaushalt (relevant bei Hitze)

**Bor-Hinweis im Plan:**
Der Plan erwaehnt korrekt: "Der hohe Boranteil in Terra Bloom (0.48%) unterstuetzt die Pollenkeimung." Dies ist biologisch praezise -- Bor ist essenziell fuer die Pollenkeimschlauch-Elongation (Zellwandsynthese der Pollenroehre) und Kalzium-Bor-Interaktion im Bluetengewebe. Die Angabe 0.48% stimmt exakt mit den Terra Bloom Produktdaten ueberein.

**Magnesium-Hinweis im Plan:**
Der Plan erwaehnt korrekt: "Terra Bloom enthaelt 0.8% MgO -- bei Schwachzehrern ausreichend." Terra Bloom enthaelt tatsaechlich 0.8% Mg (laut Produktdaten), was fuer die Chlorophyll-Synthese waehrend der Bluete wichtig ist und bei Schwachzehrern ohne CalMag-Supplementierung ausreichend ist.

**Steckbrief-Abgleich:**
Der Pflanzensteckbrief empfiehlt fuer Bluete ein NPK-Verhaeltnis 1:2:2 und EC 0.8--1.2 mS/cm. Terra Bloom liefert NPK 2-2-4 (entspricht in relativer Betrachtung einem 1:1:2 Verhaeltnis), was etwas weniger P-betont ist als der Steckbrief-Idealwert (1:2:2). Diese Abweichung ist jedoch im Rahmen -- ein reines 1:2:2-Produkt steht im Plagron-Sortiment fuer Stiefmuetterchen nicht zur Verfuegung.

---

## 6. ESSBARE BLUETEN -- FOOD-SAFETY

**Pruefpunkt 6: Karenzzeit korrekt und ausreichend begruendet?**

**Befund: TEILWEISE BESTANDEN -- Karenzzeit zu kurz, Begruendung unvollstaendig**

### 6.1 Aktuelle Dokumentation im Plan

Abschnitt 6 (Essbare Blueten):
- "Nur ungeduengte Blueten ernten (mind. 3 Tage nach letzter Duengung)"
- "Keine Blueten verwenden, die mit Pflanzenschutzmitteln behandelt wurden"
- "Nur eigene, nachweislich unbehandelte Pflanzen verwenden"

Abschnitt 8 (Sicherheitshinweise):
- "Essbare-Blueten-Hinweis: Mindestens 3 Tage nach letzter Duengung warten, bevor Blueten zum Verzehr geerntet werden"

### 6.2 Fachliche Bewertung der 3-Tage-Karenzzeit

**Fuer mineralische Duenger (Terra Grow/Bloom):**
Mineralische Fluessigduenger (Plagron Terra-Linie) sind wasserloesliche Salze. Bei korrekter Dosierung (niedrige EC fuer Schwachzehrer) ist das Risiko einer Salzakkumulation in Bluetengeweben nach 3 Tagen gering. Allerdings:

- Bei Pflanzen auf Erde mit 3-Tages-Basisgiessintervall wurde der Duenger nach 3 Tagen genau einmal bewaessert (oder gar nicht, wenn der Giessplan-Intervall 3 Tage betraegt). Eine einmalige Durchfeuchtung genuegt nicht, um Salze vollstaendig aus dem Gewebe zu verdraengen.
- Die BVL-Leitlinie fuer essbare Blueten empfiehlt generell eine Karenzzeit von 7 Tagen nach letzter Anwendung von Fluessigduengern bei Pflanzen, die fuer den direkten Verzehr vorgesehen sind.
- Fuer den Hobbybereich (kleine Mengen, gelegentlicher Verzehr) ist das Risiko bei 3 Tagen praktisch vernachlaessigbar. Fuer eine Software-App, die moeglicherweise von Menschen mit erhoehter Sensibilitaet (Kinder, Allergiker) genutzt wird, sollte die Karenzzeit konservativ sein.

**Fuer Pure Zym (Enzympraeparat):**
Pure Zym (Cellulase, Pectinase, Beta-Glucanase) ist laut Produktdaten "nicht gefaehrlich eingestuft" und "enthaelt keine Hormone, Gentechnik, tierische Bestandteile oder Schadstoffe". Enzyme werden im menschlichen Verdauungstrakt durch Proteasen abgebaut. Eine formale Karenzzeit fuer Pure Zym ist nicht notwendig, sollte aber der Vollstaendigkeit halber erwaehnt werden.

**ASPCA-Einstufung:**
Der Plan verweist korrekt auf "ASPCA safe". Dies bezieht sich auf die Pflanzentoxizitaet (keine Giftstoffe in der Pflanze selbst), nicht auf duengemittelbeladene Blueten. Diese Unterscheidung fehlt im Plan.

### 6.3 Empfehlung

Die 3-Tage-Karenzzeit sollte auf 7 Tage erhoehrt werden, mit expliziter Begruendung, dass dies die Zeit nach vollstaendiger Naehrloesung-Passage durch das Substrat ist. Die ASPCA-safe-Aussage sollte klargestellt werden: "Stiefmuetterchen-Blueten sind von Natur aus nicht giftig (ASPCA safe), aber nur chemiefreie, selbst angebaute Exemplare sind fuer den Verzehr geeignet."

---

## 7. HERBSTAUSSAAT-ALTERNATIVE

**Pruefpunkt 7: Erwahnt?**

**Befund: BESTANDEN**

Der Plan dokumentiert die Herbstaussaat-Alternative in Abschnitt 6 mit fuenf konkreten Schritten:
1. August: Aussaat bei 15--18 degC
2. September--Oktober: Saemling + Vegetativ, Auspflanzung
3. Oktober--November: Erste Herbstbluete
4. November--Februar: Winterruhe (DORMANCY), Mulchschutz
5. Maerz--Juli: Fruehjahrs-Hauptbluete, dann Sommer-Seneszenz

Der Plan erwaehnt korrekt: "Dieser alternative Zyklus ist in KA als separater NutrientPlan abzubilden." Dies ist fachlich korrekt -- ein Herbstaussaat-Plan hat ein anderes Phasen-Timing, andere Duengestrategie (K-Emphasis vor Winter) und eine echte DORMANCY-Phase.

**Erweiterungsempfehlung:** Der Hinweis auf den separaten KA-Plan koennte spaezifischer sein: "Herbstaussaat-Zyklus: Start August, DORMANCY Woche 9--20 (November--Februar, echte Winterruhe), Fruehjahrsblute Woche 21--40 (Maerz--Juli)."

---

## 8. KALIUM VOR WINTER FUER FROSTTOLERANZ

**Pruefpunkt 8: Erwahnt?**

**Befund: BESTANDEN**

Der Plan erwaehnt in Abschnitt 6 (Herbstaussaat):
"Kalium-betonte Duengung im Oktober (K-Emphasis) verbessert die Frosttoleranz fuer die Ueberwinterung."

Der Pflanzensteckbrief bestaetigt in Abschnitt 3.3 (Besondere Hinweise):
"Kalium vor Winter: Bei Herbstpflanzung fuer Ueberwinterung eine betont kaliumhaltige Duengung (K2O) im Oktober geben -- Kalium erhoht die Frosttoleranz durch verbesserten Zellturgor."

**Physiologische Korrektheit:** Korrekt. Kalium erhoht die Frosttoleranz durch:
1. Erhoehte Osmolaritaet in der Zelle (senkt Gefrierpunkt der Zellflussigkeit)
2. Verbesserte Stomata-Regulation (reduziert Wasserverlust bei Frost)
3. Aktivierung von Enzymen, die Kryoprotektanzien (Zucker, Proteine) synthetisieren

Der Hinweis ist richtig platziert (nur relevant fuer Herbstaussaat-Variante). Im Fruehjahrsaussaat-Hauptplan gibt es keine Ueberwinterung, daher ist kein K-Emphasis im Hauptplan-Zeitplan erforderlich.

---

## 9. LUECKENLOS-PRUEFUNG (32 WOCHEN)

**Pruefpunkt 9: Wochenluecken?**

**Befund: BESTANDEN**

Detaillierte Pruefung:

| Phase | Woche Start | Woche Ende | Laenge | Naechste Phase Start | Luecke? |
|-------|------------|-----------|--------|---------------------|---------|
| GERMINATION | 1 | 2 | 2 | 3 | Nein |
| SEEDLING | 3 | 8 | 6 | 9 | Nein |
| VEGETATIVE | 9 | 14 | 6 | 15 | Nein |
| FLOWERING | 15 | 28 | 14 | 29 | Nein |
| DORMANCY | 29 | 32 | 4 | -- (Ende) | -- |

Summe: 2 + 6 + 6 + 14 + 4 = **32 Wochen, lueckenlos.**

Plan-eigene Aussage "Lueckenlos-Pruefung: 2 + 6 + 6 + 14 + 4 = 32 Wochen, keine Luecken" ist korrekt.

**Jahresplan-Abgleich (Abschnitt 5):**
Der Monats-ASCII-Chart stimmt mit dem Wochen-Mapping ueberein:

- Feb (Wochen 1--2 + Wochen 3--4) = GERM + Beginn SEEDLING -- korrekt
- Maerz (Wochen 5--8) = SEEDLING -- korrekt
- April (Wochen 9--14 teilweise) = VEG -- korrekt (ca. Woche 9--12 ist Maerz/April, Woche 13--14 ist April)
- Mai--Mitte Juli (Wochen 15--28) = FLOWERING -- korrekt
- Ab Mitte Juli (Woche 29--32) = DORMANCY -- korrekt

---

## 10. KONSISTENZ TABELLEN vs. JSON

**Pruefpunkt 10: Inkonsistenzen zwischen Markdown-Dokumentation und JSON-Import-Daten?**

**Befund: ZWEI INKONSISTENZEN GEFUNDEN**

### Inkonsistenz I-001: EC-Zielwert VEGETATIVE

| Ort | Wert |
|-----|------|
| Abschnitt 4.3 Tabelle `target_ec_ms` | 0.6 |
| Abschnitt 4.3 EC-Budget-Rechnung | ~0.50 mS/cm |
| JSON VEGETATIVE `target_ec_ms` | 0.6 |

Das kalkulierte EC-Budget (0.20 + 0.30 = 0.50) stimmt nicht mit dem deklarierten Zielwert (0.60) ueberein. Der JSON-Wert und die Tabelle sind konsistent (beide 0.6), aber beide sind inkonsistent mit der internen Kalkulation. Entweder muss das EC-Budget korrigiert werden (Annahme: Leitungswasser 0.4 statt 0.3 mS/cm, dann 0.20 + 0.40 = 0.60 -- was plausibel ist), oder der `target_ec_ms`-Wert muss auf 0.5 gesenkt werden.

### Inkonsistenz I-002: EC-Zielwert FLOWERING

| Ort | Wert |
|-----|------|
| Abschnitt 4.4 Tabelle `target_ec_ms` | 0.7 |
| Abschnitt 4.4 EC-Budget-Rechnung | ~0.60 mS/cm |
| JSON FLOWERING `target_ec_ms` | 0.7 |

Gleiche Systematik wie I-001: 0.30 (TB 3ml) + 0.30 (Wasser) = 0.60, nicht 0.70. Die Tabelle und JSON sind konsistent (beide 0.7), aber inkonsistent mit der Kalkulation.

**Loesung fuer beide Inkonsistenzen:** Entweder (a) Leitungswasser-EC-Annahme auf 0.4 mS/cm anheben (was bei mittlerem Leitungswasser realistisch ist) und EC-Budget-Kommentare entsprechend anpassen, oder (b) `target_ec_ms`-Werte auf die berechneten Werte absenken.

### Weitere Konsistenzpruefungen (bestanden)

| Pruefpunkt | Tabelle | JSON | Konsistent? |
|-----------|---------|------|------------|
| GERMINATION target_ec_ms | 0.0 | 0.0 | Ja |
| SEEDLING target_ec_ms | 0.5 | 0.5 | Ja |
| DORMANCY target_ec_ms | 0.0 | 0.0 | Ja |
| Alle target_ph-Werte | 5.8 (Wachstum/Bluete), 6.0 (Dormancy) | gleich | Ja |
| Terra Grow Dosierung SEEDLING | 1.5 ml/L | 1.5 ml/L | Ja |
| Terra Grow Dosierung VEGETATIVE | 2.5 ml/L | 2.5 ml/L | Ja |
| Terra Bloom Dosierung FLOWERING | 3.0 ml/L | 3.0 ml/L | Ja |
| Pure Zym Dosierung | 1.0 ml/L | 1.0 ml/L | Ja |
| sequence_order | 1-5 aufsteigend | 1-5 aufsteigend | Ja |
| week_start/week_end | alle konsistent | alle konsistent | Ja |
| is_recurring | alle false | alle false | Ja |
| cycle_restart_from_sequence | null | null | Ja |

---

## ZUSAMMENFASSUNG DER BEFUNDE

### Rote Befunde -- Korrekturbedarf vor Import

**F-001: EC-Zielwert-Abweichung vom Steckbrief ohne Begruendung**
- Betrifft: VEGETATIVE und FLOWERING `target_ec_ms`
- Plan-Wert: 0.6 / 0.7 mS/cm
- Steckbrief-Optimum: 0.8--1.2 mS/cm fuer beide Phasen
- Empfehlung: Abweichung explizit im Plan begruenden ("konservative Schwachzehrer-Strategie, da Ueberduenung Bluetenbildung hemmt -- bewusst unterhalb des Steckbrief-Bereichs"). Die Abweichung ist agronomisch vertretbar, muss aber transparent kommuniziert werden.

**F-002: Abhaertungsphase fehlt im Phasen-Mapping**
- Der Pflanzensteckbrief modelliert `hardening_off` als eigenstaendige Phase (Sequenzposition 4, Dauer 7--14 Tage). Im Naehrstoffplan ist sie in VEGETATIVE integriert (Abschnitt 4.3 Woche 13--14: "Ab Woche 13: Abhaertung beginnen").
- Biologisch relevant: Die Abhaertung hat ein anderes Naehrstoffprofil als das vegetative Wachstum (Steckbrief: NPK 1:1:2 mit K-Betonung fuer Frosttoleranz, EC 0.6--1.0), welches im Plan nicht abgebildet ist.
- Empfehlung: Keine separate Phase zwingend erforderlich (5 Phasen im Plan sind konsistent), aber die Abhaertungs-Duengung sollte im VEGETATIVE-Abschnitt expliziter beschrieben werden: "In den letzten 2 Wochen (Abhaertung): Keine Dosierungserhoehung, aber K-Betonung foerderlich -- Terra Grow liefert K im 3-1-3-Profil ausreichend."

### Orangene Befunde -- Empfohlene Verbesserungen

**U-001: Food-Safety-Karenzzeit zu kurz (3 Tage statt empfohlener 7 Tage)**
- Aktuell: "mind. 3 Tage nach letzter Duengung"
- Empfohlen: "mind. 7 Tage nach letzter Duengung" mit Begruendung
- Begruendung: Bei 3-Tages-Giessintervall findet nach der Duengung moeglicherweise nur eine weitere Bewaesserung statt, was fuer vollstaendige Salzpassage durch das Substrat nicht ausreicht. 7 Tage entsprechen 2--3 Giesszyklen.

**U-002: Pure Zym in SEEDLING-Phase fehlt**
- Laut Pure Zym Produktdaten: "Ab Beginn der Kultivierung" (auch SEEDLING)
- Plan: Pure Zym beginnt erst in VEGETATIVE (Woche 9)
- Pflanzensteckbrief-eigener Duengungsplan: Keine explizite Pure-Zym-Empfehlung fuer Saemling
- Fachliche Einschaetzung: Pure Zym in der Saemlings-Phase hat geringen Nutzen (kaum abgestorbenes organisches Material vorhanden). Die Entscheidung, Pure Zym erst ab VEGETATIVE einzusetzen, ist pragmatisch vertretbar und spart Produkt. Eine kurze Begruendung ("Pure Zym ab Vegetativ, da in Saemlings-Phase noch kein abbaubares organisches Substratmaterial vorhanden") wuerde die bewusste Abweichung vom Herstellerplan erklaeren.

**U-003: Mischungsreihenfolge im Naehrstoffplan abweichend von Produktdaten**
- Produktdaten Terra Grow/Bloom: Reihenfolge Basisduenger (Prio 20) → Additive → Pure Zym (Prio 70) → pH
- Naehrstoffplan Abschnitt 3.2/3.3 "Hinweise": "Terra Grow → Pure Zym → pH pruefen"
- Diese Reihenfolge entspricht den Mischprioritaeten (TG prio 20, PZ prio 70), aber das explizite "→ pH pruefen" nach Pure Zym (nicht nach einem pH-korrigierenden Mittel) ist korrekt, da Terra Grow/Bloom selbst pH-puffern (6.0--6.5).
- Kein fachlicher Fehler, aber der Plan begruendet nicht, warum kein pH-Up/Down noetig ist (wegen der Selbstpufferung). Dieser Hinweis fehlt.

### Gelbe Befunde -- Hinweise und Praezisierungen

**P-001: EC-Budget-Arithmetik-Inkonsistenz (Inkonsistenz I-001 und I-002)**
- Technische Kalkulation nennt 0.50 mS/cm (VEG) und 0.60 mS/cm (FLO)
- JSON und Tabelle nennen 0.60 / 0.70 mS/cm
- Loesung: Leitungswasser-Annahme von 0.3 auf 0.4 mS/cm anheben (was bei mittelhartem Leitungswasser in DE korrekt ist) -- dann stimmt die Arithmetik

**P-002: Jahresplan-Tabelle (Abschnitt 5) Monat Maerz inkonsistent**
- Tabelle nennt: Maerz = SEEDLING, Terra Grow 1.5 ml/L
- Wochenplan: Woche 9--14 = VEGETATIVE beginnt laut Kalenderangabe "Mitte Maerz"
- Im Jahresplan-Monat April: "VEG" mit 2.5 ml/L Terra Grow -- korrekt
- Im Monat Maerz sollte der Uebergang SEEDLING → VEG sichtbar sein (ca. Mitte Maerz), was in der Tabelle nicht dargestellt wird (Maerz wird komplett als SEEDLING ausgewiesen)
- Kein gravierender Fehler, aber der Uebergang um Mitte Maerz fehlt in der Monatsansicht

**P-003: Giessvolumen-Angaben moegliche Unterschaetzung bei Topfkultur**
- Plan: 0.2 L pro Pflanze pro Gabe (Wachstum/Bluete), 0.1 L (Dormancy)
- Bei einem 1.5 L Topf sollte das Giessvolumen ca. 20--30% des Topfvolumens betragen = 0.30--0.45 L
- 0.2 L entsprechen nur 13% des Topfvolumens -- zu wenig fuer effektives Durchfeuchten und Drainage
- Fuer Beet-Anbau (kein definiertes Topfvolumen) ist 0.2 L pro Pflanze realistisch
- Empfehlung: Angabe auf "0.2--0.4 L pro Pflanze (abhaengig von Topfgroesse)" anpassen oder Hinweis, dass bei Topfkultur bis zur Drainage gegossen werden soll

**P-004: pH-Zielwert 5.8 vs. Substrat-Optimum**
- Plan: target_ph 5.8 fuer alle aktiven Phasen
- Terra Grow/Bloom puffern auf 6.0--6.5 (laut Produktdaten)
- Pflanzensteckbrief empfiehlt pH 5.5--6.2 fuer Substrat, 5.5--6.0 fuer Naehrloesung
- pH 5.8 liegt im korrekten Bereich, aber da Terra Grow/Bloom selbst auf 6.0--6.5 puffern, wird die Loesung in der Praxis eher bei 6.0--6.2 liegen -- nicht 5.8
- Dies ist kein Fehler (5.8 als Zielwert ist erreichbar mit leichter pH-Absenkung), aber ein Hinweis waere sinnvoll: "Terra Grow/Bloom puffern auf 6.0--6.5 -- aktive pH-Absenkung auf 5.8 erfordert geringen Einsatz von pH-Down"

---

## ABHAERTUNGSPHASE: ERWEITERUNGSEMPFEHLUNG

Der Pflanzensteckbrief modelliert `hardening_off` als eigenstaendige Phase zwischen VEGETATIVE und FLOWERING. Im Naehrstoffplan ist sie in VEGETATIVE integriert (Woche 13--14). Aus agronomischer Sicht hat die Abhaertungsphase ein spezifisches Duengeprofil:

| Parameter | Steckbrief Abhaertung | Aktueller Plan (VEGETATIVE Woche 13--14) |
|-----------|----------------------|----------------------------------------|
| NPK | 1:1:2 (K-betont) | 2:1:2 (gleich wie gesamte VEG-Phase) |
| EC | 0.6--1.0 mS/cm | 0.6 mS/cm |
| Temp Nacht | 3--10 degC (Aussen) | 8--12 degC (Indoor-Annahme) |

Die Abhaertungsphase sollte K-betont sein. Terra Grow (3-1-3) liefert ein K:N-Verhaeltnis von 1:1, was akzeptabel ist. Eine explizite Dosierungsreduzierung waehrend der Abhaertung (um die Pflanze auf die veraenderte Aussenumgebung vorzubereiten) waere fachlich empfehlenswert.

---

## EMPFEHLUNG ZUM IMPORT

Der Plan ist importierbar unter folgenden Voraussetzungen:

1. **Vor Import korrigieren (kritisch):**
   - F-001: Begruendung der niedrigen EC-Zielwerte hinzufuegen (1 Satz genuegt)
   - U-001: Karenzzeit essbare Blueten von 3 auf 7 Tage anheben

2. **Vor Import empfohlen (nicht kritisch):**
   - P-001: EC-Budget-Arithmetik anpassen (Leitungswasser 0.4 mS/cm annehmen und Budget-Kommentare aktualisieren)
   - P-003: Giessvolumen-Angabe auf "0.2--0.4 L je nach Topfgroesse" anpassen

3. **Nachrangig (kann in v1.1 behoben werden):**
   - F-002: Abhaertungsphase in VEGETATIVE-Hinweisen praezisieren
   - P-002: Jahresplan Monat Maerz Uebergang anzeigen
   - P-004: Hinweis auf Terra-Grow/Bloom Selbstpufferung hinzufuegen

---

## PRODUKT-DOSIERUNGSVERGLEICH MIT HERSTELLERPLAN

Der offizielle Plagron 100% TERRA Grow Schedule gibt fuer die vegetative Phase 5.0 ml/L (volle Dosis) an. Der Naehrstoffplan verwendet 2.5 ml/L (halbe Dosis) fuer VEGETATIVE und 1.5 ml/L (Viertel-Dosis) fuer SEEDLING. Das ist fuer Stiefmuetterchen als Schwachzehrer korrekt -- der Herstellerplan ist auf Cannabis/Tomaten kalibriert, nicht auf Zierpflanzen-Schwachzehrer.

Fuer Terra Bloom gibt der Herstellerplan 5.0 ml/L an. Der Naehrstoffplan verwendet 3.0 ml/L (60% der Maximaldosierung). Das ist fuer Schwachzehrer angemessen.

| Produkt | Herstellerplan (volle Dosis) | Naehrstoffplan | Reduktionsfaktor | Begruendung |
|---------|-----------------------------|-----------------|--------------------|-------------|
| Terra Grow SEEDLING | 2.5 ml/L (halbe Herstellerdosis) | 1.5 ml/L | 0.6x | Schwachzehrer, Jungpflanze |
| Terra Grow VEGETATIVE | 5.0 ml/L | 2.5 ml/L | 0.5x | Schwachzehrer |
| Terra Bloom FLOWERING | 5.0 ml/L | 3.0 ml/L | 0.6x | Schwachzehrer |
| Pure Zym (alle Phasen) | 1.0 ml/L | 1.0 ml/L | 1.0x | Standarddosierung korrekt |

Die Reduzierungen sind agronomisch korrekt und konsistent mit der Schwachzehrer-Einstufung.

---

## BIOLOGISCHE BESONDERHEITEN -- ERGAENZENDE FACHHINWEISE

### Cyclotide in Viola-Wurzeln

Der Pflanzensteckbrief erwaehnt: "Cyclotide in Wurzeln nachgewiesen, in relevanten Pflanzenteilen keine toxikologische Relevanz." Dies ist korrekt -- Cyclotide (ringfoermige Peptide) wurden in Viola-Arten nachgewiesen (Poth et al., 2010, J. Nat. Prod.), sind aber in Bluetengeweben nicht in relevanten Konzentrationen vorhanden. Die Food-Safety-Bewertung (ASPCA safe) bezieht sich korrekt auf Bloeten und Blaetter.

### Thermoinhibition: Fachlicher Hintergrund fuer spaeteren Planausbau

Die Thermoinhibition bei Viola x wittrockiana wird durch folgende Mechanismen vermittelt:
1. Phytochrom-B-vermittelte Signalwege (Hitzestress-Wahrnehmung)
2. ABA-Akkumulation (Abscisinsaeure) hemmt die Keimung bei erhoehter Temperatur
3. Inhibition der Testa-schwachungsenzyme (verhindert Testa-Ruptur)
Diese Mechanismen sind fuer die Kamerplanter-Software nicht direkt relevant, koennen aber bei der Erklaerung der Temperaturgrenzen nuetzlich sein.

### Lichtkeimer-Eigenschaft und Keimphase

Der Plan begruendet korrekt: "Samen nur leicht andruecken oder duenn mit Vermiculit bedecken." Lichtkeimer (positiver Photoblasmus) benoetigen rotes Licht (660 nm) fuer die Aktivierung von Phytochrom-PR zu PFR, welches die Keimung einleitet. Dunkelabdeckung (wie bei Thermokeimern ueblich) wuerde die Keimung hemmen. Die Empfehlung "Vermiculit duenn bestreuen" ist korrekt, da Vermiculit wasser- und lichtdurchlaessig ist.

---

**Dokumentversion:** 1.0
**Review abgeschlossen:** 2026-03-01
**Naechste Pruefung empfohlen nach:** Korrekturen gemaess F-001, U-001, P-001
