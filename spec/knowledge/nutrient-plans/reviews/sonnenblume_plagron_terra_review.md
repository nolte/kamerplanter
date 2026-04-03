# Agrarbiologisches Review: Naehrstoffplan Sonnenblume -- Plagron Terra

**Reviewer:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Geprueftes Dokument:** `spec/knowledge/nutrient-plans/sonnenblume_plagron_terra.md`
**Pflanzensteckbrief:** `spec/knowledge/plants/helianthus_annuus.md`
**Geprueft gegen Produktdaten:**
- `spec/knowledge/products/plagron_terra_grow.md`
- `spec/knowledge/products/plagron_terra_bloom.md`
- `spec/knowledge/products/plagron_power_roots.md`
- `spec/knowledge/products/plagron_pure_zym.md`
- `spec/knowledge/products/plagron_sugar_royal.md`
- `spec/knowledge/products/plagron_green_sensation.md`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Biologische Korrektheit (Helianthus) | 4/5 | Starkzehrer-Logik, Bor-Fokus, Allelopathie korrekt; ein kritischer GS-Timing-Fehler |
| Produktkorrektheit (Dosierungen) | 3/5 | Terra Bloom Reduktion bei GS fehlt; EC-Budget zu konservativ fuer Starkzehrer |
| Vollstaendigkeit der Phasen | 4/5 | 22-Wochen-Lueckenlos-Pruefung bestanden; Seneszenz-Phase nicht abgebildet |
| Konsistenz Tabellen vs. JSON | 4/5 | Ein Feldfehler (boron_ppm null), ein Inkonsistenz bei GS als optional |
| Praktische Umsetzbarkeit | 4/5 | Giesswasser-Volumina plausibel; Hitze-Override korrekt; Kalenderplan stimmig |
| Produktreihenfolge (Mischung) | 5/5 | Mixing Priorities durchgaengig korrekt eingehalten |

**Gesamteinschaetzung:** Der Plan ist fachlich solide und fuer die Zielgruppe (Hobbygaertner, Freiland) gut geeignet. Die Kernentscheidungen -- Direktsaat, kein Duenger in GERMINATION, PK-Booster in FLOWERING, Duenger-Stopp 2-3 Wochen vor Ernte -- sind biologisch korrekt und agronomisch plausibel. Es gibt jedoch einen kritischen Produktfehler beim Green-Sensation-Timing, der nach Herstellervorgabe eine Korrekturforderung ist, sowie einen kalkulatorischen EC-Unterwurf in der Vegetativphase, der fuer einen Starkzehrer ein Wachstumslimit darstellt. Beide Punkte sind loesbar ohne Restrukturierung des Plans.

---

## Kritische Befunde (Sofortiger Korrekturbedarf)

### K-001: Green Sensation ab Woche 1 der Bluete -- Herstellervorgabe verletzt

**Fundstelle:** Abschnitt 4.4 FLOWERING, Delivery Channel `naehrloesung-bluete`, JSON-Block FLOWERING (`week_start: 13, week_end: 16`)

**Problem:** Der Plan setzt Green Sensation ab der ersten Bluetewoche ein (Woche 13 = Beginn FLOWERING). Das offizielle Plagron-Dosierungsschema und die Green-Sensation-Produktdaten (Abschnitt 3.1 und 5) sind explizit:

> "Fruehe Bluete (Woche 1-3): NICHT verwenden"
> "Start: Ab der 4. Bluetewoche (wenn Blueten deutlich sichtbar und sich vergroessernden)"
> "NICHT verwenden: Waehrend der Wachstumsphase oder in den ersten 3 Bluetewochen"

Fuer Helianthus annuus bedeutet das: Bei nur 4 Bluetwochen (Woche 13-16) duerfte Green Sensation fruehestens ab Woche 16 eingesetzt werden -- was praktisch nur noch eine einzige Anwendung erlaubt. Zu frueh angesetztes Green Sensation stellt eine PK-Ueberdosierung in der fruehen Blueteninitiationsphase dar und kann die Bluetenoeffnung und Pollenbildung beeintraechtigen -- genau die Entwicklungsphase, in der Bor (nicht PK) der limitierende Faktor ist.

**Biologische Begruendung:** In der fruehen Blüte (R1 bis R3 Stadium nach USDA-Skala) fokussiert die Sonnenblume auf die Entwicklung des Bluetenkorbs und die Pollenreife. Hohe P-Gaben (GS: 9% P2O5) koennen in dieser Phase die N-Aufnahme antagonistisch hemmen und die Chlorophyllsynthese (relevant fuer Samenbeluftung) stoeren. Die Hersteller-Empfehlung, erst ab sichtbarer Bluetengroessenzunahme anzusetzen, ist physiologisch korrekt.

**Korrekte Formulierung:**
- Option A (agrobiologisch korrekt, aber eingeschraenkt): GS nur ab Woche 16 (letzte Bluetewoche), 1 Anwendung, 1 ml/L. Im JSON: `week_start: 16, week_end: 16` als separater Delivery Channel.
- Option B (empfohlen, biologisch sinnvoller fuer Sonnenblume): Green Sensation in den HARVEST-Phasen-Wochen 17-18 einsetzen, wenn die Samen aktiv gefuellt werden. Die Fruchtreife-/Samenbildungsphase profitiert direkt von hohem K (Kornfuellung, Oelgehalt) und P (ATP fuer Biosynthese). Dies entspricht dem Geist des GS-Einsatzes fuer Samenbildung.
- Option C (bei kuerzerer Bluete): Helianthus-spezifischen Hinweis ergaenzen, dass GS bei diesem Kulturtyp optional ist und besser in HARVEST eingesetzt wird.

**Empfehlung:** Option B umsetzen -- GS aus FLOWERING entfernen und als eigenstaendigen Delivery Channel in HARVEST (Woche 17-18, parallel zu reduziertem Terra Bloom) hinzufuegen.

---

### K-002: Terra Bloom Dosisreduktion bei Green Sensation fehlt

**Fundstelle:** Abschnitt 4.4 FLOWERING, Delivery Channel `naehrloesung-bluete`

**Aktueller Plan:**
- Terra Bloom: 5.0 ml/L (volle Dosis)
- Green Sensation: 1.0 ml/L

**Problem:** Die Terra Bloom Produktdaten (Abschnitt 3.1 und 8) fordern explizit:

> "Bei Einsatz von Green Sensation: Basisduenger (Terra Bloom / Cocos A+B) um ca. 20% reduzieren"
> "Bluete Woche 3-4 (mit Green Sensation): 4,0-4,5 ml/L (Reduziert wg. Green Sensation)"

Volle Terra-Bloom-Dosis (5.0 ml/L) + Green Sensation (1.0 ml/L) ohne Reduktion ergibt eine kombinierte PK-Konzentration, die die empfohlene Maximalbelastung fuer Erdsubstrat ueberschreitet und zu Salzakkumulation fuehren kann.

**EC-Kalkulation ohne Reduktion:**
- Terra Bloom 5.0 ml/L: 0.50 mS/cm
- Green Sensation 1.0 ml/L: 0.05 mS/cm
- Sugar Royal 1.0 ml/L: 0.02 mS/cm
- Pure Zym 1.0 ml/L: 0.00 mS/cm
- Basiswasser: ~0.50 mS/cm
- Gesamt: ~1.07 mS/cm (Plan-Angabe korrekt kalkuliert)

**EC-Kalkulation mit korrekter Reduktion (4.0 ml/L Terra Bloom):**
- Terra Bloom 4.0 ml/L: 0.40 mS/cm
- Green Sensation 1.0 ml/L: 0.05 mS/cm
- Restliche Additive: 0.02 mS/cm
- Basiswasser: ~0.50 mS/cm
- Gesamt: ~0.97 mS/cm

Anmerkung: Der Gesamt-EC bleibt in beiden Varianten im tolerierbaren Bereich (< 1.6 mS/cm), da Plagron-Produkte auf Erde moderate EC-Beitraege haben. Dennoch ist die Herstellervorgabe zur Reduktion ein Sicherheitsmerkmal fuer pH-Stabilitaet und Ionenbalance, die jenseits des reinen EC-Werts liegt.

**Korrekte Formulierung:**
```
Terra Bloom: 4.0 ml/L (reduziert wg. Green Sensation, Herstellervorgabe -20%)
Green Sensation: 1.0 ml/L
```

---

## Fachliche Ungenauigkeiten (Korrekturbedarf)

### U-001: EC-Budget VEGETATIVE zu konservativ fuer Starkzehrer

**Fundstelle:** Abschnitt 4.3 VEGETATIVE, EC-Budget-Zeile

**Aktueller Wert:** target_ec_ms 1.5, kalkuliertes Budget ~0.93 mS/cm

**Problem:** Das Plandokument setzt `target_ec_ms: 1.5` als Ziel-EC, berechnet aber selbst nur ~0.93 mS/cm unter der angegebenen Dosierung. Diese Diskrepanz von 0.57 mS/cm ist nicht erklaert. Fuer Helianthus annuus als Starkzehrer (Pflanzensteckbrief: EC 1.5-2.2 mS/cm in VEGETATIVE) ist 0.93 mS/cm das Minimum -- nicht das Optimum.

**Botanische Grundlage:** Helianthus annuus transipiriert an Hitzetagen 3-5 Liter pro Pflanze und Tag. Bei dieser Wasseraufnahme werden Naehrstoffe massenfluss-dominiert transportiert (Massenfluss > Diffusion bei Makronaehrstoffen). Ein hoeherer EC der Loesung ist notwendig, um den Verduennungseffekt der hohen Wasseraufnahme zu kompensieren. Literaturbelegte EC-Optimalbereiche fuer Sonnenblume in Aktivwachstum: 1.5-2.0 mS/cm (Netto, nach Basiswasser-Abzug).

**Korrekte Formulierung:**
Die Diskrepanz zwischen target_ec und kalkuliertem Budget muss aufgeloest werden. Entweder:
1. Erhoehung der Terra Grow Dosis auf die volle Empfehlung, ODER
2. Absenkung des target_ec auf den tatstaechlich erreichbaren Wert (~0.9 mS/cm) mit Hinweis, dass bei hohem Basiswasser-EC der Naehrstoffbedarf des Starkzehrer ausreichend gedeckt ist, ODER
3. Erlaeuterung, dass target_ec 1.5 einen anzustrebenden Wert fuer Regionen mit kalkarmem Leitungswasser (EC 0.2-0.3) darstellt, der dann durch hoehere Terra Grow Dosis (7.5 ml/L) erreichbar ist.

**Agronomisch empfohlen:** Hinzufuegen einer Dosierungsstaffelung:
- Leitungswasser EC 0.5-0.7: Terra Grow 5.0 ml/L, gesamt ~0.9-1.1 mS/cm (tolerabel)
- Leitungswasser EC < 0.3 (weiches Wasser): Terra Grow 7.5 ml/L moeglich, gesamt ~1.4 mS/cm (optimal)

---

### U-002: boron_ppm im FLOWERING-JSON auf null gesetzt -- Widerspruch zum fachlichen Inhalt

**Fundstelle:** JSON-Block FLOWERING, Zeile `"boron_ppm": null`

**Problem:** Der Textinhalt des Plans hebt mehrfach hervor, dass Bor der kritischste Naehrstoff fuer Sonnenblumen ist (Abschnitte 4.4, 5 Bor-Management). Terra Bloom enthaelt 0.48% B, was bei 5.0 ml/L einer Borkonzentration von:
0.48 g/100g x Dichte x 5 ml/L = rechnerisch relevant

Das Plandokument erwaehnt im Abschnitt 4.4 sogar explizit `"Boron (ppm): Terra Bloom 0.48% B -- kritisch fuer Samenansatz"` als Tabellenzeile. Der JSON-Block hat aber `"boron_ppm": null`.

**Praeziser Befund:** Das KA-Datenfeld `boron_ppm` soll den Ziel-Borgehalt der Naehrloesung tragen, NICHT den Borgehalt des Duengers. Der tatstaechliche Borgehalt der fertigen Loesung bei 5.0 ml/L Terra Bloom waere korrekt als ppm-Wert zu hinterlegen (oder als Hinweis-Text), wenn das Datenmodell dieses Feld unterstuetzt. Solange der genaue ppm-Wert nicht berechnet werden kann (Dichte des Konzentrats nicht dokumentiert), ist null als Datenfeldwert zwar technisch defensiv korrekt, der in der Tabelle angefuegte Kommentar-Text ist jedoch irrefuehrend, da er den Anschein erweckt, `boron_ppm` sei befuellt.

**Korrekte Formulierung:**
Entweder den Tabellenkommentar entfernen (`| Boron (ppm) | Terra Bloom 0.48% B -- kritisch fuer Samenansatz |`) und nur in den notes belassen, oder den ppm-Wert aus Produktanalyse berechnen und eintragen.

---

### U-003: Power Roots Absetzung -- Timing-Feinheit nicht dokumentiert

**Fundstelle:** Abschnitt 4.3 VEGETATIVE (Power Roots 1.0 ml/L), Abschnitt 4.4 FLOWERING (Power Roots abgesetzt)

**Befund:** Der Plan setzt Power Roots korrekt ab Beginn FLOWERING ab. Das Power-Roots-Produktdatenblatt zeigt jedoch, dass Power Roots bis zur Mitte der Blute (Woche 1-3 der Bluetephase) sinnvoll eingesetzt werden kann, insbesondere um die Wurzeln waehrend des erhoehten Wasserstresses in der Blute zu unterstuetzen. Helianthus annuus hat einen besonders intensiven Transpirationsstress in der Blute (2-3 L/Pflanze/Tag bei Hitze).

**Empfehlung:** Fachlich nicht falsch, aber eine suboptimale Vereinfachung. Ein Hinweis waere wert: "Power Roots kann optional die ersten 2 Wochen der FLOWERING-Phase weitergefuehrt werden (bis Woche 14), um Wurzeln bei Hitzebelastung zu unterstuetzen."

---

### U-004: Sugar Royal -- Startzeitpunkt in VEGETATIVE nicht klar abgegrenzt

**Fundstelle:** Abschnitt 4.3 VEGETATIVE (Sugar Royal 1.0 ml/L als `optional: true`)

**Befund:** Das Sugar-Royal-Produktdatenblatt gibt an: "Saemling/Steckling: 0 -- noch nicht verwenden" und "Wachstum ab Woche 2: 1.0 ml/L". Der Plan setzt Sugar Royal korrekt ab VEGETATIVE ein (Woche 6), was nach den ersten Wachstumswochen liegt. Allerdings ist Sugar Royal im VEGETATIVE-JSON als `"optional": true` markiert, aber im SEEDLING-JSON gar nicht vorhanden.

**Praeziser Befund:** Im Jahresplan (Tabelle Abschnitt 5) zeigt die Spalte Sugar Royal fuer Juni `"-- -> 1.0"` (anlaufend), was korrekt ist. Der Jahresplan-ASCII-Chart zeigt aber `".=="` fuer Sugar Royal startend im Juni -- das sollte gegen den Monat Mai-Ende geprueft werden, da VEGETATIVE erst in Woche 6 beginnt. Bei Direktsaat Mitte Mai: Woche 1-2 = Mai (spaet), Woche 3-5 = Ende Mai bis Mitte Juni (SEEDLING), Woche 6 = ca. 18. Juni. Das passt zur Darstellung.

**Einschaetzung:** Fachlich korrekt, kein Handlungsbedarf.

---

## Hinweise und Prazisierungen

### H-001: Phasenmapping -- fehlende SENESCENCE-Phase des Pflanzensteckbriefs

**Fundstelle:** Abschnitt 2 Phasen-Mapping

**Hinweis:** Der Pflanzensteckbrief (helianthus_annuus.md) definiert 6 Phasen, darunter eine eigenstaendige SENESCENCE-Phase (7-14 Tage, "terminal: true"). Der Naehrstoffplan bildet nur 5 KA-Phasen ab und fasst Fruchtreife und Seneszenz in einer HARVEST-Phase zusammen (Woche 17-22). Der Duenger-Stopp in Woche 20 ist inhaltlich eine implizite SENESCENCE-Abbildung.

**Bewertung:** Fuer einen Naehrstoffplan ist diese Vereinfachung agronomisch vertretbar -- die Seneszenz braucht keinen eigenen Duengeeintrag. Allerdings fehlt ein expliziter Hinweis, dass die Wochen 20-22 der HARVEST-Phase agrobiologisch der SENESCENCE entsprechen. Dieser Hinweis wuerde die Konsistenz mit dem Pflanzensteckbrief verbessern.

**Empfehlung:** In den HARVEST-Phasenhinweisen erwaehnen: "Woche 20-22 entspricht der Seneszenz-Phase (terminal) des Pflanzensteckbriefs. Die Pflanze stellt aktives Wachstum ein, Naehrstoffe werden aus den Blaettern in die Samen mobilisiert."

---

### H-002: Giessvolumen GERMINATION -- 0.1 L pro Pflanzstelle sehr gering

**Fundstelle:** Abschnitt 3.1 Wasser Keimung, method_params `volume_per_feeding_liters: 0.1`

**Hinweis:** 100 ml pro Pflanzstelle beim taeglichen Giessen in GERMINATION ist physiologisch zutreffend fuer eine einzelne Aussaatstelle. Bei Direktsaat in gewachsenen Boden (keine Topfkultur) ist der Wasseranspruch jedoch standortabhaengig. Bei verdichteten Boeden oder nach Regen kann weniger noetig sein, bei sandigen Boeden kann mehr benoetigt werden. Der Wert ist als Mindestwert fuer die Saattiefe (2-3 cm) zu verstehen.

**Einschaetzung:** Kein Fehler -- der Hinweis "Boden gleichmaessig feucht halten" im channel-notes ist ausreichend. Optional koennte "100-300 ml je nach Bodenbeschaffenheit" praezisiert werden.

---

### H-003: pH-Ziel FLOWERING vs. VEGETATIVE -- Absenkung biologisch korrekt

**Fundstelle:** Abschnitt 4.3 VEGETATIVE (target_ph 6.5), Abschnitt 4.4 FLOWERING (target_ph 6.3)

**Befund:** Die pH-Absenkung von 6.5 auf 6.3 in der FLOWERING-Phase ist biologisch korrekt und begruendet: Phosphor ist im pH-Bereich 6.0-6.5 am besten verfuegbar; in der Blüte wird mehr P benoetigt (Samenbildung, ATP-Produktion). Die Absenkung um 0.2 pH-Einheiten optimiert die P-Verfuegbarkeit ohne die Bor-Aufnahme zu gefahrden (Bor: optimale Verfuegbarkeit pH 5.0-7.5, kein enger Bereich).

**Einschaetzung:** Fachlich korrekt, kein Handlungsbedarf. Positiv vermerkt.

---

### H-004: Allelopathie-Warnung -- vollstaendig und korrekt

**Fundstelle:** Abschnitte 5 und 6.5 (Allelopathie-Warnung, Fruchtfolge)

**Befund:** Die Allelopathie-Warnung ist fachlich korrekt:
- Heliannuol A-E als Wirkstoffe korrekt benannt
- 4-6 Wochen Kompostierungszeit korrekt (Literatur: Macias et al. 2003)
- Fruchtfolge 3-4 Jahre Asteraceae-Pause korrekt
- Empfindliche Nachkulturen (Salat, Kopfsalat) korrekt benannt -- konsistent mit dem Pflanzensteckbrief (Kompatibilitaet 6.3)
- Empfehlung, Pflanzenreste nicht sofort einzuarbeiten: korrekt

Einzige Ergaenzung aus dem Pflanzensteckbrief, die im Naehrstoffplan nicht explizit auftaucht: Weizen als empfindliche Nachkultur. Dies waere eine sinnvolle Ergaenzung in Abschnitt 6.4 Fruchtfolge.

**Einschaetzung:** Fachlich vollstaendig und korrekt. Positiv vermerkt.

---

### H-005: Toxizitaet und Sicherheitshinweise -- vollstaendig

**Fundstelle:** Abschnitt 6 Sicherheitshinweise

**Befund:** Der Plan benennt korrekt:
- Sonnenblume nicht giftig fuer Katzen, Hunde, Kinder (konsistent mit Pflanzensteckbrief)
- Pollenallergie (Asteraceae/Kompositen-Kreuzreaktion) korrekt erwaehnt
- Konzentrat-Hinweis fuer Plagron-Fluessigduenger korrekt

Konsistenz mit dem Pflanzensteckbrief: Der Steckbrief unterscheidet `contact_allergen: false` (keine echte Allergie durch Behaarung) und `pollen_allergen: true`. Der Naehrstoffplan bildet dies korrekt ab.

**Einschaetzung:** Fachlich korrekt und vollstaendig. Positiv vermerkt.

---

### H-006: Kalium-Versorgung fuer Stengelfestigkeit -- korrekt und vollstaendig

**Fundstelle:** Abschnitt 6.3 Kalium fuer Stengelfestigkeit

**Befund:** Die K-Versorgungskette ist korrekt dargestellt:
- Terra Grow 3-1-3: K2O 3.1% -- liefert K in SEEDLING/VEGETATIVE
- Terra Bloom 2-2-4: K2O 3.9% -- liefert K in FLOWERING/HARVEST
- Green Sensation 0-9-10: K2O 10% -- PK-Booster verstaerkt K in FLOWERING

Kalium ist entscheidend fuer Zellturgor und damit fuer die Stengelfestigkeit, die Sonnenblumen fuer das Tragen von Bluetenkoepfen bis 30-40 cm Durchmesser benoetigen. Die Empfehlung, Stuetzstaebe ab 1 m Hoehe zu setzen, ist unabhaengig von der K-Versorgung und korrekt -- mechanische Unterstuetzung kann chemische Massnahmen nicht ersetzen, aber ergaenzen.

**Einschaetzung:** Fachlich korrekt und praxisrelevant. Positiv vermerkt.

---

### H-007: Bor-Management -- im Kern korrekt, aber VEGETATIVE-Luecke unzureichend adressiert

**Fundstelle:** Abschnitt 6.2 Bor-Management

**Befund:** Das Bor-Management ist insgesamt gut durchdacht:
- Terra Bloom als primaere Bor-Quelle (0.48% B) korrekt hervorgehoben
- Notfall-Blattspritzung Borsaeure 150 ppm korrekt (Literaturwert: 100-200 ppm Borsaeure-Loesung als Notmassnahme)
- Warnung vor engen Mangel-Toxizitaets-Grenzwerten korrekt
- Vorbeugender Borax-Einsatz im Boden (1 g/m²) korrekt als Option fuer bekannte Mangelstandorte

**Unzureichend adressiert:** Die VEGETATIVE-Phase (Woche 6-12) ist die kritische Risikoperiode fuer Bormangel: Stengel wachsen 5-10 cm pro Tag, der B-Bedarf fuer Zellwandsynthese ist maximal. Terra Grow enthaelt Bor, aber die genaue Menge ist in den Produktdaten als `<!-- DATEN FEHLEN -->` markiert. Der Plan erwaehnt dies als "Risikophase" (korrekt), gibt aber keine Schwellenwerte fuer den praezisen Interventionszeitpunkt an.

**Empfehlung:** Folgenden Hinweis in Abschnitt 6.2 ergaenzen: "Praeventive Bodenboranreicherung (Borax 1 g/m² einarbeiten) vor der Aussaat ist besonders bei sandigen, ausgelaugten Boeden und bei Anbau in Regionen mit bekanntem Bormangel (Norddeutsche Tiefebene, ausgelaugte Sandboeden) empfohlen. Der optimale Bor-Bodengehalt fuer Sonnenblumen liegt bei 0.5-1.0 mg B/kg Boden (Heisswasser-loesliches B)."

---

## Konsistenzpruefung: Tabellen vs. JSON

| Pruefpunkt | Tabellen-Angabe | JSON-Angabe | Status |
|------------|----------------|-------------|--------|
| GERMINATION NPK | (0,0,0) | [0.0, 0.0, 0.0] | Konsistent |
| GERMINATION EC | 0.0 | target_ec_ms: 0.0 | Konsistent |
| SEEDLING Terra Grow | 2.5 ml/L | ml_per_liter: 2.5 | Konsistent |
| SEEDLING target_ec | 0.8 | target_ec_ms: 0.8 | Konsistent |
| SEEDLING NPK | (2,1,1) | [2.0, 1.0, 1.0] | Konsistent |
| VEGETATIVE Terra Grow | 5.0 ml/L | ml_per_liter: 5.0 | Konsistent |
| VEGETATIVE target_ec | 1.5 | target_ec_ms: 1.5 | Konsistent (aber EC-Budget-Luecke, s. U-001) |
| VEGETATIVE NPK | (3,1,2) | [3.0, 1.0, 2.0] | Konsistent |
| FLOWERING Terra Bloom | 5.0 ml/L | ml_per_liter: 5.0 | Konsistent (aber Reduktionspflicht, s. K-002) |
| FLOWERING Green Sensation | 1.0 ml/L | ml_per_liter: 1.0 | Konsistent (aber Timing-Fehler, s. K-001) |
| FLOWERING target_ec | 1.6 | target_ec_ms: 1.6 | Konsistent |
| FLOWERING NPK | (1,2,3) | [1.0, 2.0, 3.0] | Konsistent |
| FLOWERING boron_ppm | Tabelle: "0.48% B -- kritisch" | JSON: null | Inkonsistent (s. U-002) |
| HARVEST Terra Bloom Woche 17-19 | 3.0 ml/L | ml_per_liter: 3.0 | Konsistent |
| HARVEST target_ec | 1.0 | target_ec_ms: 1.0 | Konsistent |
| HARVEST NPK | (0,1,3) | [0.0, 1.0, 3.0] | Konsistent |
| Sugar Royal FLOWERING optional | Als optional markiert (Tabelle) | "optional": true | Konsistent |
| Green Sensation FLOWERING optional | Als nicht-optional (Kernprodukt) | "optional": false | Konsistent -- aber Timing-Fehler (K-001) |

**Ergebnis:** 16/17 Tabellen-JSON-Paare konsistent. Ein struktureller Widerspruch (boron_ppm null vs. Tabellen-Kommentar).

---

## Lueckenlos-Pruefung (22 Wochen)

| Phase | Wochen | Beginn | Ende | Luecken? |
|-------|--------|--------|------|----------|
| GERMINATION | 1-2 | 1 | 2 | -- |
| SEEDLING | 3-5 | 3 | 5 | -- |
| VEGETATIVE | 6-12 | 6 | 12 | -- |
| FLOWERING | 13-16 | 13 | 16 | -- |
| HARVEST | 17-22 | 17 | 22 | -- |

**Summe:** 2 + 3 + 7 + 4 + 6 = **22 Wochen. Keine Luecken. Kein Ueberlapp.**

Planangabe "2 + 3 + 7 + 4 + 6 = 22 Wochen" ist korrekt -- der Planer gibt 7 Wochen fuer VEGETATIVE an, was mit week_start=6 und week_end=12 uebereinstimmt (12-6+1 = 7 Wochen). Plausibel fuer Helianthus annuus mit Direktsaat Mitte Mai und Samenernte September/Oktober in Mitteleuropa (Zone 7-8).

---

## Produkteinsatz-Analyse: Alle 6 Produkte

### Gesamtbewertung der 6 Produkte

| Produkt | Einsatzphasen | Biologische Begruendung | Reihenfolge korrekt? | Bewertung |
|---------|--------------|------------------------|---------------------|-----------|
| Terra Grow (3-1-3) | SEEDLING, VEGETATIVE | Wachstumsfoerderung (N), Pfahlwurzel (K, P), pH-Selbstpufferung | Ja (Priority 20) | Korrekt |
| Terra Bloom (2-2-4) | FLOWERING, HARVEST | PK-Umstellung, Bor (0.48%) fuer Pollenkeimung, Mg fuer Spaetbluete | Ja (Priority 20) | Korrekt (aber Reduktion fehlt, K-002) |
| Power Roots (0-0-2) | SEEDLING, VEGETATIVE | Wurzelstimulator (Humin, Kelpak) -- kritisch fuer Pfahlwurzelentwicklung bis 200 cm | Ja (Priority 60) | Korrekt |
| Pure Zym (0-0-0) | SEEDLING bis HARVEST W19 | Bodenbiologie, Enzymkatlyse -- sinnvoll bei Freilanderde mit hohem Organikanteil | Ja (Priority 70) | Korrekt |
| Sugar Royal (9-0-0) | VEGETATIVE, FLOWERING | Aminosaeuren fuer Chlorophyllstimulation, Aminosaeure-Chelate -- sinnvoll fuer Starkzehrer | Ja (Priority 65) | Korrekt; optionale Markierung in FLOWERING sachgerecht |
| Green Sensation (0-9-10) | FLOWERING | PK-Booster fuer Samenansatz und Kornfuellung | Ja (Priority 30) | Timing FALSCH (K-001); Dosisreduktion Terra Bloom fehlt (K-002) |

**Mischungsreihenfolge gesamt:** Die Mixing Priorities werden in allen drei Delivery Channels korrekt eingehalten:

- naehrloesung-wachstum: Terra Grow (20) -> Power Roots (60) -> Sugar Royal (65) -> Pure Zym (70) -- korrekt
- naehrloesung-bluete: Terra Bloom (20) -> Green Sensation (30) -> Sugar Royal (65) -> Pure Zym (70) -- korrekt
- wasser-keimung und wasser-pur: keine Duenger, korrekt

---

## Kalenderplan-Plausibilitaet (22 Wochen Mai-Oktober)

| Monat | Phase laut Plan | Agrobiologische Plausibilitaet |
|-------|----------------|-------------------------------|
| Mitte Mai | GERMINATION (Woche 1-2) | Korrekt: Direktsaat nach Eisheiligen (15. Mai), Bodentemperatur min. 10 Grad C |
| Ende Mai / Anfang Juni | SEEDLING (Woche 3-5) | Korrekt: 2-4 echte Blaetter nach 3 Wochen bei 20-25 Grad C -- Literaturbest. |
| Mitte Juni bis Ende Juli | VEGETATIVE (Woche 6-12) | Korrekt: Langste Phase, max. Sonnenstunden (Solstitium 21. Juni), explosives Wachstum |
| August | FLOWERING (Woche 13-16) | Korrekt: Sonnenblumen sind tagneutrale Kulturformen; Bluete im August bestaeubungsoptimal (Bienenflug, Hitze) |
| September / Anfang Oktober | HARVEST (Woche 17-22) | Korrekt: Samenreife September-Oktober; Duenger-Stopp Woche 20 (Anfang Oktober) passt zur natuerlichen Reife |
| Nach Oktober | Seneszenz / Pflanzenabgang | Korrekt: Einjaerig, kein Zyklus-Neustart |

**Einschaetzung:** Der Kalenderplan ist fuer Mitteleuropa (Zone 7-8, letzter Frost Mitte Mai) biologisch realistisch und gut abgestimmt.

---

## Duenger-Stopp Pruefung

**Plan:** Duenger-Stopp ab Woche 20 (2-3 Wochen vor Ernte, nur klares Wasser bis Woche 22)

**Biologische Begruendung:** Bei Samenernten gibt es kein verbraucherrelevantes Argument fuer einen Geschmacks-Flush (wie bei Cannabis). Der Duenger-Stopp bei Helianthus dient dem Zweck:
1. Reduzierung des Bodensalz-Akkumulationsrisikos (nach intensivem Starkzehrer-Sommer)
2. Verbesserung der Samenreife durch kontrollierten N-Entzug (Beschleunigung der Samentrocknung)
3. Foerderung der Seneszenz (erhoehte Ethylensynthese bei N-Entzug beschleunigt Blattvergelbung und Naehrstoffmobilisierung in Samen)

**Bewertung:** Der 2-3-woechen Duenger-Stopp ist biologisch korrekt und agronomisch sinnvoll. Der Zeitpunkt (Woche 20 = ca. Anfang Oktober) passt zur natuerlichen Reifeentwicklung. Positiv vermerkt.

---

## Zusammenfassung der Korrekturprioritaeten

| ID | Befund | Typ | Prioritaet | Aufwand |
|----|--------|-----|------------|---------|
| K-001 | Green Sensation ab Woche 1 Bluete -- Herstellervorgabe verletzt | Kritisch | Sofort | Mittel |
| K-002 | Terra Bloom Dosisreduktion bei GS fehlt | Kritisch | Sofort | Gering |
| U-001 | EC-Budget VEGETATIVE zu konservativ -- Erklaerungsluecke | Fachlich | Hoch | Gering |
| U-002 | boron_ppm im JSON null trotz Tabellen-Kommentar | Konsistenz | Hoch | Gering |
| U-003 | Power Roots Fortsetzung bis Woche 14 optional erwaehnen | Ergaenzung | Niedrig | Minimal |
| H-001 | Seneszenz-Mapping zum Steckbrief erwaehnen | Dokumentation | Niedrig | Minimal |
| H-007 | Bodenborgehalt-Schwellenwert fuer Interventionsentscheidung ergaenzen | Ergaenzung | Niedrig | Gering |

---

## Empfohlene Aenderungen am Dokument (Kurzfassung)

### 1. FLOWERING-Phase ueberarbeiten (K-001 + K-002)

**Delivery Channel naehrloesung-bluete -- neue Dosierungen:**

Woche 13-15 (fruehe bis mittlere Bluete -- ohne GS):
```
Terra Bloom: 5.0 ml/L
Sugar Royal: 1.0 ml/L
Pure Zym: 1.0 ml/L
target_ec_ms: 1.5
```

Woche 16 (spaete Bluete -- GS Einstieg gemaess Herstellervorgabe):
```
Terra Bloom: 4.0 ml/L (reduziert -20% wg. Green Sensation)
Green Sensation: 1.0 ml/L
Sugar Royal: 1.0 ml/L
Pure Zym: 1.0 ml/L
target_ec_ms: 1.5
```

**Alternative (agribiologisch bevorzugt, s. K-001 Option B):**

Green Sensation vollstaendig aus FLOWERING entfernen und in HARVEST (Woche 17-18) als zusaetzlichen Delivery Channel neben reduziertem Terra Bloom einfuegen:
```
Terra Bloom: 3.0 ml/L (reduziert)
Green Sensation: 1.0 ml/L (Kornfuellung, K-Versorgung)
Pure Zym: 1.0 ml/L
target_ec_ms: 1.0
```

### 2. Boron_ppm-Feld bereinigen (U-002)

Im JSON-Block FLOWERING: Tabellenzeile `| Boron (ppm) | Terra Bloom 0.48% B -- kritisch fuer Samenansatz |` in Tabelle entfernen; stattdessen nur in den phase notes belassen.

### 3. EC-Budget-Erklaerung ergaenzen (U-001)

In Abschnitt 4.3 nach der EC-Budget-Zeile ergaenzen:
"Hinweis: Der target_ec von 1.5 mS/cm wird bei mittlerem Leitungswasser-EC (0.5-0.7 mS/cm) mit der angegebenen Dosierung nicht erreicht. Fuer kalkarmeres Wasser (EC < 0.3) kann die Terra Grow Dosis auf 7.0 ml/L angehoben werden. Fuer Starkzehrer in voller Wachstumsphase sind 1.2-1.5 mS/cm Gesamt-EC anzustreben."

---

## Fazit

Der Naehrstoffplan fuer Helianthus annuus mit Plagron Terra-Produkten ist in seiner Grundstruktur fachlich korrekt und praxistauglich. Die kritischsten Fehler betreffen nicht die Pflanzenphysiologie, sondern die korrekte Anwendung der Produkte gemaess Herstellervorgabe (Green Sensation Timing, Terra Bloom Dosisreduktion). Diese Fehler sind mit minimalem Aufwand korrigierbar. Nach Korrektur der Befunde K-001 und K-002 ergibt sich ein Plan, der biologisch vollstaendig, produktkorrekt und fuer Hobbygaertner gut verstaendlich ist.

Die Behandlung der Allelopathie, des Bor-Managements, der Stickstoff-Disziplin (kein Frischmist, kein Sugar Royal in HARVEST) und des Duenger-Stopps vor der Samenernte ist auf dem aktuellen Stand der Praxis und der Fachliteratur.

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
