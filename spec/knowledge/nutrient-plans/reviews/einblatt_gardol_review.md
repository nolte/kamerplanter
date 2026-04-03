# Fachliches Review: Naehrstoffplan Spathiphyllum wallisii -- Gardol Gruenpflanzenduenger

**Reviewer:** Agrarbiologie-Experte (Zimmerpflanzen / Indoor-Anbau)
**Datum:** 2026-03-01
**Dokument unter Pruefung:** `spec/knowledge/nutrient-plans/einblatt_gardol.md` v1.0
**Referenzdokumente:**
- Pflanzensteckbrief: `spec/knowledge/plants/spathiphyllum_wallisii.md`
- Produktdaten: `spec/knowledge/products/gardol_gruenpflanzenduenger.md`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 3 / 5 | Kritische Dosierungsinkonsistenz mit Produktdatenblatt, Mg-Abweichung in Blutephase |
| Vollstaendigkeit | 4 / 5 | Fe-Versorgung nicht als Zielwert dokumentiert; sonst gut abgedeckt |
| Konsistenz Tabellen/Fliesstext/JSON | 4 / 5 | Eine Phasen-Inkonsistenz September/Oktober zwischen Monatstabelle und Phasen-Mapping |
| Giesswerte | 4 / 5 | Giessintervall-Basis liegt am oberen Rand; Dormancy-Override korrekt |
| Toxizitaetshinweise | 5 / 5 | Vollstaendig und praezise; geht ueber Steckbrief hinaus |
| Schwachzehrer-Konformitaet | 4 / 5 | EC-Grenze korrekt kommuniziert; Dosierungs-Referenzrahmen klaerungsbeduertig |

**Gesamteinschaetzung:** Der Plan ist in Grundstruktur und Sicherheitshinweisen stark. Die groesste fachliche Schwachstelle ist eine Inkonsistenz zwischen der internen Dosierungstabelle (volle Dosis = 4 ml/L) und den Hersteller-Anwendungsangaben im Produktdatenblatt (Zimmerpflanzendosis ca. 1 ml/L). Dadurch stimmt der Referenzrahmen "halbe Dosis = 2 ml/L" nicht mit dem Produktdatenblatt ueberein. Ausserdem weicht der Mg-Zielwert in der Blutephase vom Steckbrief ab, und die Eisen-Versorgung wird trotz explizitem Fe-Zielwert im Steckbrief nicht als messbarer Parameter gefuehrt. Die Phosphor-Unterversorgung in der Blutephase ist korrekt identifiziert, aber die Handlungsempfehlung ist zu weich.

---

## Kritische Befunde (Sofortiger Korrekturbedarf)

### K-001: Dosierungs-Referenzrahmen stimmt nicht mit Produktdatenblatt ueberein

**Fundstelle:** Abschnitt 4, Tabelle "EC-Beitrag Gardol Gruenpflanzenduenger" (Zeile ~114-118)

**Problem:** Der Nahrstoffplan definiert:
- Viertel-Dosis: 1,0 ml/L
- Halbe Dosis: 2,0 ml/L
- Volle Dosis: 4,0 ml/L

Das Produktdatenblatt (Abschnitt 3.1) nennt als Zimmerpflanzendosierung "1/4 Dosierkappe auf 5 L Wasser". Bei einer Dosierkappe von ca. 20 ml ergibt das 5 ml / 5 L = 1,0 ml/L als die Hersteller-Zimmerpflanzendosierung -- also genau das, was der Plan als "Viertel-Dosis" bezeichnet. Die Bezeichnung "volle Dosis" mit 4,0 ml/L entspricht der 4-fachen Herstellerempfehlung fuer Zimmerpflanzen (Freiland-Dosierung).

Konsequenz: Wenn Nutzer im System die Bezeichnung "halbe Dosis" lesen, koennte sie auf Basis der Hersteller-Packungsbeilage 0,5 ml/L vermuten -- was die korrekte Spathiphyllum-Dosis von 2,0 ml/L deutlich unterschreitet.

**Korrekte Formulierung:**
Dosierungsbezeichnungen an Hersteller-Referenz verankern. Da das Produktdatenblatt die Dosierkappe als ~20 ml annimt und 1/4 Kappe / 5L als Zimmerpflanzendosis:
- "Herstellerdosis Zimmer (1/4 Kappe / 5L)" = ~1,0 ml/L (entspricht Plan-Vierteldosis)
- "Empfohlene Dosis Spathiphyllum" = 2,0 ml/L = doppelte Herstellerdosis Zimmer (aufgrund des sehr geringen EC-Beitrags von 0,06 mS/cm/ml/L bei diesem Produkt vertretbar, aber muss begruendet werden)
- Alternativ: Explizit schreiben "2 ml/L (entspricht 1/2 Dosierkappe auf 5L)"

**Empfehlung:** Den Jahresverbrauch und die EC-Beitragstabelle auf konsistente Referenz "Herstellerdosierung = 1 ml/L" umstellen und die Spathiphyllum-Empfehlung explizit als Abweichung von der Herstellerempfehlung kennzeichnen oder die Dosierungsbezeichnungen umbenennen.

**Prioritaet:** Hoch -- betrifft alle vier Phasendefinitionen und die Jahresverbrauchsrechnung.

---

### K-002: Mg-Zielwert in FLOWERING weicht vom Steckbrief ab

**Fundstelle:** Abschnitt 4.3, Tabelle Phase FLOWERING, Zeile `magnesium_ppm` (~Zeile 181)

**Problem:** Der Steckbrief (Abschnitt 2.3, Naehrstoffprofile) fordert explizit:
- Bluete: Mg 25 ppm

Der Nahrstoffplan dokumentiert:
- FLOWERING: `magnesium_ppm: 40.0` (Ca) und `magnesium_ppm: 20.0`

Der Wert 20 ppm entspricht dem VEGETATIVE-Zielwert, nicht dem erhoehten Bluete-Zielwert von 25 ppm.

**Biologische Begruendung fuer 25 ppm Mg in Blutephase:** Magnesium ist Zentralatom des Chlorophylls und gleichzeitig Cofaktor der ATP-Synthase. In der Blutephase steigt der Energiebedarf fuer die Blutensynthese, was einen erhoehten Mg-Bedarf erklaert. Zudem foerdert Mg die Phosphor-Mobilisierung -- bei ohnehin niedrigem P durch Gardol 6-4-6 ist eine ausreichende Mg-Versorgung umso wichtiger.

**Korrekte Formulierung:** `magnesium_ppm: 25.0` in Phase FLOWERING (Angleichung an Steckbrief), sowohl in der Markdowntabelle als auch im JSON-Block (Zeile ~381).

**Prioritaet:** Mittel -- die Abweichung von 5 ppm bei Leitungswasserversorgung ist in der Praxis vernachlaessigbar, aber die Inkonsistenz zwischen Plan und Steckbrief ist ein Datenfehler der beim Import korrigiert werden muss.

---

## Wichtige Hinweise (Kein fachlicher Fehler, aber Verbesserungsbedarf)

### H-001: Fe-Versorgung nicht als Zielwert dokumentiert

**Fundstelle:** Abschnitte 4.2 und 4.3 (VEGETATIVE und FLOWERING Phase-Entries)

**Problem:** Der Steckbrief (Abschnitt 2.3) definiert explizit:
- Aktives Wachstum: Fe 1 ppm
- Bluete: Fe 1 ppm

Im Nahrstoffplan werden pro Phase `calcium_ppm` und `magnesium_ppm` gefuehrt, aber kein Eisenwert. Das KA-Datenmodell unterstuetzt `iron_ppm` nach Steckbrief-Definition -- ob das Feld im Phasen-Eintrag-Modell verfuegbar ist, muss gegen `src/backend/app/domain/models/nutrient_plan.py` geprueft werden.

**Fachliche Begruendung:** Eisen-Mangel ist bei Spathiphyllum ein reales Risiko -- typisches Symptom ist intervenoese Chlorose (Blaetter vergilben zwischen den Blattadern, Adern bleiben gruen). Gardol 6-4-6 enthaelt "chelatierte Spurenelemente wahrscheinlich inkl. Fe" (Produktdatenblatt Abschnitt 2.2), aber ohne Mengenangabe. Bei Leitungswasser ist Fe-Versorgung in der Regel ausreichend (0,1-0,3 mg/L); bei RO-Wasser koennte Fe-Mangel auftreten.

**Empfehlung:** Im Hinweistext der VEGETATIVE- und FLOWERING-Phasen explizit erwaehnen: "Eisen-Zielwert: 1 ppm (aus Gardol-Spurenelementen und Leitungswasser). Bei Chlorose-Symptomen (intervenoese Blattvergilbung) Fe-EDTA-Chelat supplementieren (0,1 ml/L)." Falls `iron_ppm` als Datenbankfeld vorhanden ist, als `iron_ppm: 1.0` erganzen.

**Prioritaet:** Mittel

---

### H-002: Phosphor-Unterversorgung in FLOWERING -- Handlungsempfehlung zu weich

**Fundstelle:** Abschnitt 4.3, Hinweistext FLOWERING (~Zeile 182)

**Problem:** Der Plan erkennt korrekt, dass das NPK-Ideal fuer Blute 2:3:2 waere (erhoehtes P), aber Gardol 6-4-6 liefert 1,5:1:1,5. Der Phosphor-Anteil ist in der Blutephase um den Faktor 3 unter dem Ideal. Die Formulierung "ist akzeptabel" ohne Alternativangebot ist fuer einen Referenz-Nahrstoffplan zu vage.

**Fachliche Begruendung:** Bei Spathiphyllum ist der Blutenausloeser primaer photomorphogenetisch (Lichtniveau DLI > 5), nicht nutritiv -- das ist korrekt so im Plan beschrieben. Dennoch unterstuetzt erhoehtes P/K die Qualitaet und Haltbarkeit der Spatha (weisses Hochblatt) und des Spadix. Ein niedrig-P-Produkt wie Gardol 6-4-6 ist akzeptabel, aber nicht optimal.

**Empfehlung:** Konkreten Handlungsweg fuer Nutzer erganzen:
"Wer optimale Blutenbedingungen anstrebt: Im Fruehjahr (Maerz-April) 4-6 Wochen lang auf einen Bluetenduenger mit erhoehtem P-Anteil (z.B. COMPO Bluetenduenger NPK 3-4-5 oder aehnlich) wechseln. Halbe Dosis einhalten. Danach zurueck auf Gardol Gruenpflanzenduenger."

**Prioritaet:** Niedrig bis mittel (beeinflusst Bluetenhaeuigkeit, nicht Pflanzenueberleben)

---

### H-003: Inkonsistenz Phasen-Mapping September/Oktober zwischen Monatstabelle und Textdiagramm

**Fundstelle:** Abschnitt 5, Jahresplan Tabelle (~Zeile 234-235) vs. ASCII-Diagramm (~Zeile 249)

**Problem:** In der Monatstabelle (Abschnitt 5) sind August und September als "FLOWERING/VEG" gefuehrt, Oktober als "VEGETATIVE". Das ASCII-Diagramm zeigt:
```
KA-Phase: |DOR|DOR|VEG|VEG|VEG|VEG|VEG|FLO|FLO|VEG|DOR|DOR|
```
August = FLO, September = FLO, Oktober = VEG.

Im Phasen-Mapping (Abschnitt 2) deckt FLOWERING Woche 37-44 ab. Woche 37 beginnt ungefaehr Mitte September (bei Jahresbeginn = Maerz, Woche 5 = Mitte April, dann: Woche 37 = 32 Wochen spaeter = ca. Mitte November). Das ergibt rechnerisch: FLOWERING faellt in den Zeitraum November bis Januar -- was biologisch falsch ist (Spathiphyllum bluht typisch Fruehling bis Sommer).

Der eigentliche Widerspruch liegt darin, dass die absoluten Wochennummern (37-44) bei einem Jahresstart im Maerz nicht mit den Kalendermonaten Juli-September uebereinstimmen. Das Phasen-Mapping mit Wochennummern ist steckbriefkonforme Dauer-Angabe (32 Wochen VEGETATIVE), setzt aber einen Startmonat voraus der nicht explizit definiert ist.

**Korrekte Formulierung:** Klarstellen, dass Wochennummern relativ zum Jahreszyklusbeginn (=Maerz) gezaehlt werden. Woche 37 = Woche 37 ab Maerz = Mitte November. Das widerspricht dem Bluetezeitraum Fruehjahr-Sommer aus dem Steckbrief (bloom_months: 4, 5, 6, 7, 8).

Entweder:
(a) FLOWERING auf Woche 9-20 verschieben (= Mai bis August bei Maerz-Start), oder
(b) Explizit dokumentieren, dass der FLOWERING-Block im System event-basiert (nicht sequenziell-zeitbasiert) ausgeloest wird und die Wochennummern 37-44 nur als Pufferzeitraum dienen.

**Prioritaet:** Mittel -- betrifft die systemseitige Phasensteuerung (REQ-003)

---

### H-004: Steckbrief-Widerspruch Kontaktallergen-Flag wird nicht aufgeloest

**Fundstelle:** Sicherheitshinweise Abschnitt 7 (~Zeile 465)

**Problem:** Der Steckbrief (`spathiphyllum_wallisii.md`, Abschnitt 1.4) setzt `contact_allergen: false`, beschreibt aber gleichzeitig "Calciumoxalat-Raphiden koennen Kontaktdermatitis und brennendes Gefuehl ausloesen". Das ist ein fachlicher Widerspruch im Steckbrief selbst.

Der Nahrstoffplan kommuniziert korrekt "Handschuhe tragen -- Pflanzensaft enthaelt Calciumoxalat-Raphiden und kann Kontaktdermatitis ausloesen", geht also ueber den Steckbrief hinaus.

**Fachliche Einordnung:** Calciumoxalat-Raphiden sind mechanische Irritanzien (nicht immunologische Allergene im Sinne einer IgE-vermittelten Typ-I-Reaktion). Das erklaert das `contact_allergen: false` im technischen Sinne. Der Sicherheitshinweis im Plan ist trotzdem korrekt und notwendig. Empfehlung: Im Steckbrief das Feld um `mechanical_irritant: true` erganzen, um die Unterscheidung zu dokumentieren. Im Nahrstoffplan den Hinweis beibehalten -- er ist biologisch korrekt und schutzt Nutzer.

**Prioritaet:** Niedrig (Steckbrief-Bug, nicht Plan-Bug)

---

### H-005: Gardol-Dosierkappe Volumen nicht verifiziert -- EC-Schaetzung unsicher

**Fundstelle:** Produktdaten Abschnitt 3.1 mit Kommentar `<!-- DOSIERKAPPENVOLUMEN FEHLT -- ANNAHME CA. 20 ML PRO KAPPE -->`, sowie Plan Abschnitt 4 EC-Schaetzung

**Problem:** Der EC-Beitrag von ~0,06 mS/cm pro ml/L ist eine Schaetzung. Das Produktdatenblatt selbst kennzeichnet `ec_contribution_per_ml` als fehlend. Der Plan baut auf dieser Schaetzung die gesamte EC-Logik auf (target_ec_ms 0,6 mS/cm bei 2 ml/L + Leitungswasser 0,4-0,5 mS/cm = 0,5-0,6 mS/cm gesamt).

Bei einem tatsaechlichen EC-Beitrag von 0,10 mS/cm/ml/L (oberes Ende der Schaetzspanne aus dem Produktdatenblatt) waere die Gesamt-EC bei 2 ml/L und hartem Leitungswasser (0,7 mS/cm):
0,7 + 2 x 0,10 = 0,9 mS/cm -- noch unterhalb der 1,0 mS/cm-Grenze, aber eng.

**Empfehlung:** Messung am physischen Produkt durchfuehren (EC-Meter, 2 ml/L in destilliertem Wasser). Bis zur Verifikation den EC-Zielwert auf 0,5 mS/cm (statt 0,6) konservativ setzen, um Spielraum fuer hartes Leitungswasser zu lassen. Den Status "EC-Beitrag nicht verifiziert" im Dokument behalten und als offenen Datenpunkt kennzeichnen.

**Prioritaet:** Mittel

---

## Positiv hervorgehobene Aspekte

### P-001: Schwachzehrer-Grenze korrekt und prominent kommuniziert

Die 1,0-mS/cm-Grenze wird an drei Stellen (Metadata-Beschreibung, EC-Tabelle, VEGETATIVE-Hinweis) konsistent kommuniziert und mit dem haeufigsten Symptom (braune Blattspitzen) verknuepft. Das ist fachlich korrekt und benutzerfreundlich.

### P-002: Chlor-/Fluoridempfindlichkeit vollstaendig integriert

Die Wasserqualitaets-Anforderung (abgestandenes Leitungswasser 24h oder Regenwasser) ist in Giessplan, Channel-Hinweisen und Phasennotizen konsistent praesent. Das ist bei Spathiphyllum besonders wichtig und wird in vielen Referenzplanen vernachlaessigt.

### P-003: Salzspuelungs-Protokoll fachlich korrekt

Drei Salzspuelungen pro Jahr (Juni, Oktober, November) mit 2x Topfvolumen klar formuliert. Fuer einen Schwachzehrer mit niedriger Dosierung bei gleichzeitig 21-Tage-Intervall ist die Akkumulationsrate gering -- trotzdem ist die Empfehlung korrekt und beugt dem haeufigsten Langzeitproblem vor.

### P-004: Toxizitaetshinweise uebertreffen Steckbrief

Der Sicherheitsabschnitt (Abschnitt 7) ist ausfuehrlicher als der Steckbrief. Besonders wertvoll: der Hinweis auf Drainage-Wasser als Gefahrenquelle fuer Haustiere (Trinken der gedungten Loessung in der Unterschale), der in keinem Standardsteckbrief vorkommt. Giftnotrufzentralen korrekt angegeben.

### P-005: Perennial-Zykluslogik korrekt modelliert

`cycle_restart_from_sequence: 2` mit GERMINATION als einmalige Erstphase (is_recurring: false) und VEGETATIVE/FLOWERING/DORMANCY als jaehrlich wiederkehrende Sequenz ist fachlich und datentechnisch korrekt. Die Unterscheidung zwischen obligater Dormanz (dormancy_required: false aus Steckbrief) und kulturpraktischer Ruhephase wird klar kommuniziert.

### P-006: Volle GERMINATION-Nutzung fur Vermehrungskontext korrekt erklaert

Die Verwendung von GERMINATION als Platzhalter-Phase fuer "Etablierung nach Teilung" ist systemseitig der einzig verfuegbare Enum-Wert. Die Begruendung im Plan ist transparent und korrekt -- es wird nicht verschwiegen, dass die Phase eigentlich keimungsbiologisch nicht zutrifft.

---

## Vollstaendigkeitspruefung: Wochen-Lueckenlosigkeit

Aus dem Dokument (Abschnitt 2, letzte Zeile):
> 1-4 | 5-36 | 37-44 | 45-62 (4 + 32 + 8 + 18 = 62 Wochen)

Pruefung:
- GERMINATION: Woche 1-4 = 4 Wochen (korrekt)
- VEGETATIVE: Woche 5-36 = 32 Wochen (korrekt)
- FLOWERING: Woche 37-44 = 8 Wochen (korrekt)
- DORMANCY: Woche 45-62 = 18 Wochen (korrekt)
- Gesamt: 4 + 32 + 8 + 18 = 62 Wochen
- Lucken: Keine (Woche 4 endet, Woche 5 beginnt; 36 endet, 37 beginnt; usw.)
- Ueberlappungen: Keine

**Befund: Lueckenlos und ueberlappungsfrei. Korrekt.**

Anmerkung zu den 62 Wochen: 62 Wochen entsprechen ca. 14,3 Monaten. Jaehrlicher Zyklus (nach Erstdurchlauf) umfasst VEGETATIVE (32W) + FLOWERING (8W, optional) + DORMANCY (18W) = 58 Wochen = ca. 13,3 Monate. Das ist leicht mehr als ein Kalenderjahr (52 Wochen). Bei `cycle_restart_from_sequence: 2` wird der Erstdurchlauf mit Woche 1-62 korrekt als Sonderfall behandelt; der jaehrliche Wiederkehrzyklus ab Sequenz 2 startet dann neu ab Woche 1 -- die internen Wochennummern der Phase-Entries werden dann relativ interpretiert. Diese Logik muss gegen die Implementierung in REQ-003 geprueft werden.

---

## Konsistenzpruefung: Tabellen vs. Fliesstext vs. JSON

| Pruefpunkt | Tabelle | Fliesstext | JSON | Befund |
|-----------|---------|-----------|------|--------|
| GERMINATION week_start/end | 1-4 | "Woche 1-4" | 1-4 | Konsistent |
| VEGETATIVE NPK | (1.5, 1, 1.5) | "1,5:1:1,5 (6-4-6)" | [1.5, 1.0, 1.5] | Konsistent |
| VEGETATIVE ml/L | 2.0 | "2 ml/L (halbe Dosis)" | 2.0 | Konsistent |
| VEGETATIVE target_ec_ms | 0.6 | "EC-Zielwert 0,6 mS/cm" | 0.6 | Konsistent |
| VEGETATIVE Ca | 40 ppm | "Ca 40 ppm aus Leitungswasser" | 40.0 | Konsistent |
| VEGETATIVE Mg | 20 ppm | "Mg 20 ppm aus Leitungswasser" | 20.0 | Konsistent |
| FLOWERING Mg | 20 ppm | Steckbrief: 25 ppm | 20.0 | INKONSISTENZ mit Steckbrief (K-002) |
| DORMANCY intervall_days | 9 | "9-Tage-Intervall" | 9 | Konsistent |
| DORMANCY fertilizer_dosages | [] | "Keine Duengung" | [] | Konsistent |
| Jahresplan Oktober | VEG, 1 ml/L | "Viertel-Dosis" | (nur Tabelle) | Konsistent intern |
| ASCII-Diagramm Sep | FLO | Monatstabelle: FLO/VEG | nicht im JSON | Leichte Inkonsistenz (H-003) |
| Toxizitaet Katze/Hund | true/true | "GIFTIG fuer Katzen, Hunde" | (kein JSON) | Konsistent mit Steckbrief |
| volume_per_feeding GERMINATION | 0.2 L | "0,2 L fuer Topf 12-15 cm" | 0.20 | Konsistent |
| volume_per_feeding VEGETATIVE | 0.4 L | "0,4 L fuer Topf 14-18 cm" | 0.4 | Konsistent |

---

## Giesswerte-Pruefung gegen Steckbrief

| Phase | Steckbrief Intervall (Tage) | Plan Basis-Intervall | Plan Override | Bewertung |
|-------|----------------------------|---------------------|---------------|-----------|
| Etablierung (GERMINATION) | 4-5 | 7 (Basis) | 5 (Override) | Korrekt: Override 5 liegt im Steckbrief-Bereich (4-5), Basis 7 wird durch Override ueberschrieben |
| Aktives Wachstum (VEGETATIVE) | 5-7 | 7 (Basis) | keiner | Akzeptabel: 7 liegt am oberen Rand des Steckbrief-Bereichs. Fuer einen "gleichmaessig feucht"-Typ wie Spathiphyllum waere 5-6 Tage als Basis geeigneter |
| Bluete (FLOWERING) | 5-7 | 7 (Basis) | keiner | Identisch mit VEGETATIVE -- gleiche Bewertung |
| Ruheperiode (DORMANCY) | 7-10 | 7 (Basis) | 9 (Override) | Korrekt: Override 9 liegt innerhalb des Steckbrief-Bereichs (7-10). Plan erweitert eigenstaendig auf 10-12 Tage bei kuehlerem Standort -- fachlich korrekt, aber ueber Steckbrief-Bereich hinausgehend |

**Giessmenge VEGETATIVE:** Steckbrief 150-400 ml; Plan Channel 0,4 L = 400 ml. Liegt am oberen Rand. Fuer Topf 14-18 cm akzeptabel, aber der Hinweis auf "groessere Exemplare 0,6-0,8 L" ist korrekt und wichtig.

---

## NPK-Verhaeltnis-Analyse

### VEGETATIVE

| | Plan | Steckbrief | Abweichung |
|--|------|-----------|------------|
| NPK-Verhaeltnis | 1.5 : 1 : 1.5 | 3 : 1 : 2 | N 50% unter Ideal, K entspricht 75% des Ideals |
| N-Betonung | ja (gleich K) | ja (N >> K) | Steckbrief fordert N-Betonung; Plan liefert N=K (ausgewogen) |
| P-Anteil | relativ hoch (P = 1 Teil auf 1.5 N) | niedrig (P = 0.33 auf 3 N) | Plan hat relativ hoeheres P als Steckbrief-Ideal |

**Bewertung:** Gardol 6-4-6 ist kein optimales Produkt fuer Spathiphyllum in der Wachstumsphase. Das Steckbrief-Ideal 3:1:2 beschreibt eine deutlich N-betontere Formulierung. Die Abweichung ist bei Erdkultur tolerierbar, da der Stickstoff aus organischen Duengerueckstaenden im Substrat erganzt wird. Die Aussage "Abweichung fuer Erdkultur bei Schwachzehrern akzeptabel" ist vertretbar, sollte aber durch den Satz erganzt werden: "Fuer optimales N-betontes Blattwachstum waere ein 7-3-6-Produkt (z.B. COMPO Gruenpflanzen- und Palmenduenger) die bessere Wahl."

### FLOWERING

| | Plan | Steckbrief | Abweichung |
|--|------|-----------|------------|
| NPK-Verhaeltnis | 1.5 : 1 : 1.5 | 2 : 3 : 2 | P-Anteil Faktor 3 zu niedrig |
| P-Anteil absolut | 33% des Gesamt-NPK | 43% des Gesamt-NPK | Erhebliche Unterversorgung |

**Bewertung:** Der P-Mangel in der Blutephase ist der groesste agronomische Kompromiss dieses Plans. Da der Blutenausloeser bei Spathiphyllum primaer photomorphogenetisch ist (DLI > 5), ist die Pflanze dennoch in der Lage zu bluehen. Die Bluten-Qualitaet und -Dauer koennte jedoch leiden. Handlungsempfehlung fehlt im Plan (H-002).

---

## Ca/Mg/Fe-Versorgungsanalyse

### Calcium (Ca)

- Steckbrief-Zielwert VEGETATIVE: 40 ppm; FLOWERING: 40 ppm
- Plan-Wert: 40 ppm in beiden Phasen -- korrekt
- Quelle: Leitungswasser (dt. Durchschnitt ~100 ppm Ca = 250 mg/L CaCO3 = ca. 100 mg/L Ca)
- Bewertung: Korrekt. Leitungswasser deckt Ca-Bedarf. Kommentar SP-001 ist fachlich korrekt.
- Hinweis fuer RO-Wasser: Korrekt im Plan adressiert (CalMag-Supplement-Empfehlung).

### Magnesium (Mg)

- Steckbrief VEGETATIVE: 20 ppm -- Plan: 20 ppm (korrekt)
- Steckbrief FLOWERING: 25 ppm -- Plan: 20 ppm (FEHLER -- K-002)
- Quelle: Leitungswasser (dt. Durchschnitt ~15 ppm Mg -- liegt etwas unter dem Steckbrief-Ziel von 20 ppm)
- Anmerkung: Der Plan setzt 20 ppm aus Leitungswasser, aber der deutsche Durchschnitt liegt bei ~10-15 ppm Mg. In Gebieten mit weichem Wasser (Muenchen, Hamburg) kann Mg knapp werden. Die Empfehlung CalMag bei weichem Wasser (0,3 ml/L) ist korrekt.

### Eisen (Fe)

- Steckbrief-Zielwert VEGETATIVE und FLOWERING: Fe 1 ppm
- Plan: Kein iron_ppm-Wert dokumentiert (H-001)
- Gardol-Produkt: "chelatierte Spurenelemente wahrscheinlich inkl. Fe" ohne Mengenangabe
- Leitungswasser: 0,1-0,3 mg/L Fe (in der Regel ausreichend fuer 1 ppm Ziel)
- Risiko: Ohne Mengenangabe im Produkt kann nicht sicher gestellt werden, ob der Zielwert erreicht wird
- Empfehlung: Dokumentieren und ggf. Monitoring-Hinweis bei Chlorose-Symptomen erganzen

---

## Phasen-Mapping-Bewertung

### Korrekte Phasen-Nutzung

- GERMINATION als Etablierungsphase: Systemseitig korrekte Loesung (kein PROPAGATION-Enum), transparent begruendet.
- DORMANCY fuer kulturpraktische Ruhephase: Korrekt, obwohl `dormancy_required: false` im Steckbrief. Die Erklarung (saisonale Lichtreduktion als Ausloeser, nicht obligate physiologische Dormanz) ist biologisch korrekt.
- SEEDLING nicht genutzt: Korrekt (Teilungsvermehrung, keine Keimungsphase).
- FLUSHING nicht genutzt: Korrekt fuer Erdkultur-Zimmerpflanze.
- HARVEST nicht genutzt: Korrekt (Zierpflanze).

### Wochendauer-Plausibilitaet

| Phase | Plan (Wochen) | Steckbrief (Tage) | Umrechnung | Bewertung |
|-------|--------------|-------------------|------------|-----------|
| GERMINATION | 4 (28 Tage) | 14-30 Tage | 28 Tage | Am oberen Rand, korrekt |
| VEGETATIVE | 32 (224 Tage) | ca. 210 Tage | 224 Tage | Sehr nah am Steckbrief (210 Tage = 30 Wochen). 32 Wochen leicht laenger -- akzeptabel da Saison variiert |
| FLOWERING | 8 (56 Tage) | 30-60 Tage | 56 Tage | Korrekt, am oberen Rand des Steckbrief-Bereichs |
| DORMANCY | 18 (126 Tage) | ca. 120 Tage | 126 Tage | Korrekt |

**Befund: Alle Wochendauern sind steckbrief-konform oder liegen innerhalb akzeptabler Toleranz.**

### FLOWERING-Positionierung im Jahresverlauf (H-003 vertieft)

Das biologische Problem: Spathiphyllum bluht typisch April-August (bloom_months: 4,5,6,7,8 aus Steckbrief). Im sequenziellen Phasen-Modell des Plans erscheint FLOWERING nach 36 Wochen VEGETATIVE, also (bei Zyklusstart Maerz) im November -- biologisch falsch.

Loesungsoptionen:
1. **Systemseitige Loesung (empfohlen):** FLOWERING als event-basierte parallele Annotation behandeln (REQ-003 prufen ob Phase-States "overlapping" unterstuetzt werden), nicht als sequenzielle Phase.
2. **Planstruktur-Loesung:** VEGETATIVE auf 12-20 Wochen verkuerzen (Maerz-Juli), dann FLOWERING (Juli-September, 8 Wochen), dann VEGETATIVE (September-Oktober), dann DORMANCY. Das erfordert mehr Phase-Entries.
3. **Dokumentarische Loesung (minimal-invasiv):** Explizit dokumentieren dass FLOWERING im System event-basiert ausgeloest wird und die sequence_order 3 mit Wochen 37-44 nur als Fallback-Zeitfenster dient falls kein Lichtsensor den DLI > 5 Trigger meldet.

**Empfehlung: Option 3 als sofortiger Fix (ein Satz in phase_entries.notes erganzen), Option 1 als mittelfristige REQ-003-Anforderung dokumentieren.**

---

## Jahresverbrauchsrechnung -- Pruefung

Aus Abschnitt 5, Jahresverbrauch:
- Halbe Dosis (Apr-Sep): 6 Monate, 21-Tage-Intervall
  - 6 Monate x ~4,33 Wochen/Monat / 3 (Wochen pro 21-Tage-Intervall) = ~8,66 Duengungen
  - Plan sagt "ca. 8 Duengungen" -- leicht abgerundet, korrekt
  - 8 x 0,4 L x 2 ml/L = 6,4 ml -- korrekt
- Viertel-Dosis (Maerz, Okt): 2 Monate
  - 2 Monate x 4,33 Wochen/Monat / 3 = ~2,89 Duengungen
  - Plan sagt "ca. 3 Duengungen" -- korrekt
  - 3 x 0,4 L x 1 ml/L = 1,2 ml -- korrekt
- Gesamt: 7,6 ml/Jahr -- korrekt
- Hochrechnung: 1000 ml / 7,6 ml = 131,6 Jahre pro Pflanze (Plan sagt "ca. 130 Jahre") -- korrekt

**Jahresverbrauchsrechnung ist korrekt.**

---

## Offene Datenpunkte aus Produktdatenblatt (nicht Fehler des Plans)

Diese Luecken existieren im Produktdatenblatt und schraenken die Prazision des Nahrstoffplans ein. Sie sollten bei Gelegenheit durch Messung am physischen Produkt geschlossen werden:

| Datenpunkt | Status | Auswirkung auf Plan |
|-----------|--------|---------------------|
| EC-Beitrag pro ml/L (verifiziert) | Fehlt (Schaetzung 0,06) | target_ec_ms-Werte sind Naherungswerte |
| Dosierkappe Volumen (ml) | Fehlt (Annahme 20 ml) | Umrechnung auf ml/L basiert auf unverifizierten Annahmen |
| Spurenelement-Mengen (Fe, Mn, Zn ppm) | Fehlt | Fe-Versorgung kann nicht quantitativ bewertet werden |
| pH des Konzentrats / der Naehrloesung | Fehlt | pH-Effekt auf Substrat nicht quantifizierbar |
| Exakter Gehalt an organischem N | Unklar (Widerspruch in Produktdaten) | Bioavailabilitaet von N nicht sicher bewertbar |

---

## Zusammenfassende Massnahmen nach Prioritaet

### Prioritaet 1 -- Sofort korrigieren

1. **K-001:** Dosierungsbezeichnungen (Viertel/Halbe/Volle Dosis) an Herstellerreferenz verankern oder als explizite Plan-eigene Skala kennzeichnen. Nutzer muessen verstehen, dass "volle Dosis" im Plan nicht der Herstellerempfehlung fuer Zimmerpflanzen entspricht.

2. **K-002:** `magnesium_ppm` in Phase FLOWERING von 20 auf 25 ppm korrigieren -- sowohl in der Markdowntabelle (Abschnitt 4.3) als auch im JSON-Block (Abschnitt 6.2, FLOWERING).

### Prioritaet 2 -- In naechster Revision

3. **H-001:** Fe-Versorgungshinweis in VEGETATIVE und FLOWERING Phasen-Notizen erganzen. Falls das Datenmodell `iron_ppm` unterstuetzt: `iron_ppm: 1.0` in beide aktiven Phasen eintragen.

4. **H-002:** Konkrete Produktempfehlung fuer P-Supplementierung in der Blutephase erganzen (z.B. COMPO Bluetenduenger NPK 3-4-5 fuer 4-6 Wochen im Fruehjahr).

5. **H-003:** FLOWERING-Positionierung klarstellen: Entweder als event-basierte Phase dokumentieren (nicht sequenziell), oder Wochennummern an den biologischen Bluetezeitraum (Mai-September) anpassen.

### Prioritaet 3 -- Bei Gelegenheit

6. **H-004:** Steckbrief `contact_allergen: false` um Feld `mechanical_irritant: true` erganzen (Steckbrief-Korrektur, nicht Plan-Korrektur).

7. **H-005:** EC-Beitrag und Dosierkappe am physischen Gardol-Produkt verifizieren und Produktdatenblatt aktualisieren.

8. VEGETATIVE-Giessbasis-Intervall ggf. auf 5-6 Tage reduzieren (aktuell 7 Tage = oberer Steckbrief-Rand), besonders fuer den Sommer-Zeitraum mit hoeherem Verdunstungsdruck.

---

## Dateiverweise

- Analysierter Plan: `/home/nolte/repos/github/kamerplanter/spec/knowledge/nutrient-plans/einblatt_gardol.md`
- Pflanzensteckbrief: `/home/nolte/repos/github/kamerplanter/spec/knowledge/plants/spathiphyllum_wallisii.md`
- Produktdaten: `/home/nolte/repos/github/kamerplanter/spec/knowledge/products/gardol_gruenpflanzenduenger.md`
- Verwandter Review (Monstera): `/home/nolte/repos/github/kamerplanter/spec/analysis/agrobiology-review-monstera-nutrient-plan-2026-03.md`

---

**Review-Version:** 1.0
**Erstellt:** 2026-03-01
