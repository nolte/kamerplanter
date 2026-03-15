# Agrarbiologisches Review: Nährstoffplan Tomate / Plagron Terra + PK 13-14

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Indoor-Vorkultur + Outdoor Freiland/Gewächshaus, Erdkultur, Starkzehrer, saisonaler Anbau
**Analysierte Dokumente:**
- `spec/ref/nutrient-plans/tomate_plagron_terra.md` (v1.0)
- `spec/ref/plant-info/solanum_lycopersicum.md` (v1.0)
- `spec/ref/products/plagron_terra_grow.md` (v1.0)
- `spec/ref/products/plagron_terra_bloom.md` (v1.0)
- `spec/ref/products/plagron_power_roots.md` (v1.0)
- `spec/ref/products/plagron_pure_zym.md` (v1.0)
- `spec/ref/products/plagron_sugar_royal.md` (v1.0)
- `spec/ref/products/plagron_pk_13_14.md` (v1.0)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Botanische Korrektheit | 5/5 | Nomenklatur korrekt, Starkzehrer-Klassifikation und Fruchtfolge-Hinweise exemplarisch |
| Phasen-Mapping-Qualitaet | 5/5 | 6 Phasen lueckenlos, 28-Wochen-Arithmetik stimmt exakt, Kalender-Mapping plausibel |
| NPK-Produktwahl | 4/5 | Terra-Linie geeignet; PK 13-14 Timing und Dosierung korrekt angepasst; SEEDLING fehlt Power-Roots-Phase-Ende-Abgrenzung |
| EC-Budget-Korrektheit | 5/5 | Erdkultur-EC konservativ und korrekt erklaert; Leitungswasser-Basis transparent kommuniziert |
| BER-Praevention | 4/5 | Detaillierter BER-Abschnitt, Calcium korrekt modelliert in FLOWERING/HARVEST; Magnesium-Modellierung fehlt |
| K:N-Verhaeltnis Fruchtphase | 4/5 | Terra Bloom 2-2-4 liefert K2O 3.9% vs N 2.1% (Ratio ~1.86:1); knapp unter 2:1-Mindestanforderung |
| PK 13-14 Timing & Dosierung | 5/5 | 0.5 ml/L in 1 Woche (W15-16) korrekt auf Tomate angepasst; Hintergrunderklaerung vollstaendig |
| Sugar Royal HARVEST-Absetzung | 5/5 | Korrekt abgesetzt; Begruendung fachlich praezise (organischer N verschlechtert Fruchtqualitaet) |
| Produktreihenfolge / Mixing | 4/5 | Grundsaetzlich korrekt; CalMag vor Sulfaten nicht ausfuellungsrelevant da Terra-Linie kein separates CalMag -- aber Hinweis fehlt |
| FLUSHING-Phase | 5/5 | Saisonal korrekt platziert (September), Ethylen-Nachreifehinweis fachlich richtig, 2-Wochen-Dauer angemessen |
| Ausgeizen (Geiztriebe) | 5/5 | Detailliert, richtig: Hand statt Messer, TMV-Hinweis, Wochenrhythmus, Toppen ab August |
| Toxizitaet / Sicherheit | 5/5 | Solanin/Tomatin, Tierarten, Kontaktallergen, gruene vs. reife Fruechte korrekt differenziert |
| Jahresverbrauch-Kalkulation | 5/5 | Formel transparent, Ergebnis plausibel; Kostenabschaetzung PK 13-14 akkurat |
| Tabellen-JSON-Konsistenz | 4/5 | Weitgehend konsistent; 2 geringfuegige Abweichungen identifiziert (siehe T-008, T-009) |

**Gesamteinschaetzung:** Der Naehrstoffplan ist agronomisch sehr gut ausgearbeitet und stellt einen der vollstaendigsten und fachlich korrektesten Referenzplaene im Kamerplanter-Projekt dar. Die BER-Praevention ist hervorragend dokumentiert, das Ausgeiz-Kapitel ist vorbildlich, und die angepasste PK 13-14 Dosierung (0.5 ml/L statt der Cannabis-ueblichen 1.5 ml/L) zeigt tiefes pflanzenspezifisches Verstaendnis. Die groessten Schwachstellen sind das leicht unter 2:1 liegende K:N-Verhaeltnis in der HARVEST-Phase durch Terra Bloom 2-2-4, die fehlende Magnesium-Modellierung in den Phaseneintragen sowie ein inhaltlicher Widerspruch in der Mixing-Reihenfolge im FLOWERING-JSON. Alle Befunde sind loesbar ohne Grundstruktur-Aenderung.

---

## Findings

### T-001: K:N-Verhaeltnis in HARVEST-Phase minimal unter 2:1-Schwellenwert

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.5 (HARVEST, Zeile ~243); `spec/ref/plant-info/solanum_lycopersicum.md`, Abschnitt 3.4 (Zeile ~261)

**Problem:**
Der Pflanzensteckbrief formuliert klar: "K:N-Verhaeltnis ab Fruchtphase mindestens 2:1 fuer optimalen Geschmack." Terra Bloom liefert laut Produktdatenblatt:
- N gesamt: 2.1%
- K2O: 3.9%

Das K:N-Verhaeltnis errechnet sich als K:N = 3.9 / 2.1 = **1.857:1** -- das liegt knapp unter dem geforderten Minimum von 2:1.

Hinzu kommt der Stickstoff-Beitrag aus Pure Zym (0-0-0, kein N) -- das ist korrekt, aber der Sachverhalt der Unterschreitung des K:N-Minimums durch das Basisprodukt ist real.

Der Plan beschreibt im HARVEST-Abschnitt den K:N-Vorteil mit dem Hinweis "Terra Bloom liefert hohes K (3.9% K2O vs. 2.1% N), was Geschmack und Fruchtfestigkeit optimiert" -- das ist qualitativ korrekt, aber die 2:1-Schwelle aus dem eigenen Steckbrief wird quantitativ nicht erreicht.

**Agronomische Einordnung:**
Das Verhaeltnis 1.86:1 ist in der Praxis grenzwertig, aber nicht kritisch -- Tomaten reagieren auf Werte zwischen 1.5:1 und 3:1 ohne starke Qualitaetseinbussen. Der echte Geschmacks- und Fruchtqualitaetseffekt setzt unterhalb von ~1.5:1 ein. Die 2:1-Empfehlung ist eine praxiserprobte Faustformel, kein physiologischer Grenzwert. Dennoch besteht ein interner Widerspruch zwischen Steckbrief und Planumsetzung.

Bei 5 ml/L Terra Bloom (FLOWERING) hat man K:N = 1.86. Wenn der Nutzer wie empfohlen auf 4 ml/L in HARVEST reduziert, aendert sich das Verhaeltnis nicht (beide Naehrstoffe werden proportional reduziert). Das K:N bleibt konstant bei 1.86:1.

**Korrekturvorschlag:**
Option A: Den Zielwert im Steckbrief von "mindestens 2:1" auf "mindestens 1.8:1" praezisieren, mit Ergaenzung "Terra Bloom 2-2-4 liefert 1.86:1 -- ausreichend, jedoch koennen ergaenzende K-Quellen (Kaliumsulfat, Beinwell-Jauche) das Verhaeltnis auf >2:1 anheben."

Option B: Einen optionalen K-Booster erwaehnen: "Bei gewuenschtem K:N > 2:1 koennen 0.5 g/L Kaliumsulfat (K2SO4) zur Giessloessung zugegeben werden (EC-Beitrag ca. +0.08 mS/cm)."

Option C (minimal): Im HARVEST-Phasen-Hinweistext ergaenzen: "Terra Bloom liefert K:N von ~1.86:1 -- unterhalb der 2:1-Empfehlung aus dem Steckbrief, aber in der Praxis ausreichend fuer guten Geschmack. Wer 2:1 exakt erreichen moechte: Kaliumsulfat (0.3 g/L) ergaenzen."

---

### T-002: Magnesium vollstaendig unmodelliert (magnesium_ppm: null in allen Phasen)

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitte 4.2 bis 4.5 (alle Phasen, `magnesium_ppm: null`)

**Problem:**
Saemtliche 4 aktiven Duengungsphasen (SEEDLING, VEGETATIVE, FLOWERING, HARVEST) weisen `magnesium_ppm: null` auf. Dies ist fuer Tomaten als Starkzehrer nicht vollstaendig:

Magnesium ist bei Tomaten aus zwei Gruenden praxisrelevant:
1. **Chlorophyll-Synthese:** Mg ist das Zentralatom des Chlorophylls. Mg-Mangel fuehrt zu intervenoser Chlorose (Blattadern bleiben gruen, Blattflaechen vergilben), ein haeufiges Problem bei Tomaten in der Spaetbluete und Fruchtphase.
2. **Fruchtqualitaet:** Mg spielt als Cofaktor bei der Enzyme der Kohlenhydrat-Synthese (Saccharose, Zucker in Fruechten) eine Rolle. Mg-Mangel reduziert Zuckergehalt und Geschmack.

Terra Bloom liefert laut Produktdatenblatt **0.8% Mg** -- das ist vorhanden und relevant. Der Plan erwaehnt Mg nirgendwo explizit als Zielparameter. Der Pflanzensteckbrief (Abschnitt 2.3) gibt fuer Phase Bluete 60 ppm Mg und fuer Fruchtreife 60 ppm Mg als Zielwerte an.

Bei 5 ml/L Terra Bloom und 1 Liter Giessloessung: 0.8% Mg x 5 ml/L = 0.04 g/L = 40 mg/L = 40 ppm Mg. Das liegt unter den vom Steckbrief empfohlenen 60 ppm -- Leitungswasser deckt typisch 10-20 ppm Mg ab, was die Gesamtversorgung auf ca. 50-60 ppm bringt. Das ist knapp ausreichend, sollte aber dokumentiert sein.

**Konsequenz bei hartem Leitungswasser (hoher Ca-Anteil):** Calcium und Magnesium konkurrieren um dieselben Aufnahmetransporter. Hartes Leitungswasser (>200 mg/L Ca) kann die Mg-Aufnahme hemmen. Bei kalkreichen Regionen kann ein Mg-Supplement notwendig werden.

**Korrekturvorschlag:**
1. In FLOWERING und HARVEST das Feld `magnesium_ppm` auf **40-60** setzen (Terra Bloom 0.8% liefert ~40 ppm bei 5 ml/L; Leitungswasser-Ergaenzung bringt auf ~55 ppm).
2. Im Praxis-Hinweis erwaehnen: "Mg-Mangel (intervenoese Chlorose an aelteren Blaettern) bei kalkreichen Boden/Wasser: 1x monatlich Bittersalz-Blattspritzmittel (2 g/L MgSO4) oder Bittersalz ins Giesswasser (1 g/L)."
3. Im Jahresplan-Abschnitt (Abschnitt 5) die Mg-Versorgung durch Terra Bloom kurz erwaehnen.

---

### T-003: Mixing-Reihenfolge im FLOWERING-JSON widerspruechilich zu Delivery-Channel-Hinweis

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 3.3 (Delivery Channel naehrloesung-bluete, Zeile ~96) vs. Abschnitt 8.2 FLOWERING JSON (Zeile ~608)

**Problem:**
Im Delivery-Channel-Hinweis (Abschnitt 3.3) wird als Mischungsreihenfolge angegeben:
> "Terra Bloom -> Pure Zym -> Sugar Royal -> (PK 13-14 nur W15-16) -> pH pruefen"

Im FLOWERING-JSON (Abschnitt 8.2, delivery_channels notes) lautet die Reihenfolge hingegen:
> "Terra Bloom -> PK 13-14 -> Pure Zym -> Sugar Royal -> pH pruefen"

Diese beiden Angaben sind inkonsistent: Im einen Fall wird PK 13-14 ans Ende gesetzt (nach Pure Zym und Sugar Royal), im anderen unmittelbar nach Terra Bloom vor den Additiven.

**Agronomische Beurteilung der Mischungsreihenfolge:**
PK 13-14 ist ein mineralisches Phosphat-Kalium-Konzentrat. Terra Bloom enthaelt ebenfalls Phosphor und Kalium sowie Magnesium und Eisenchelate. Die Reihenfolge der Zugabe zwischen diesen mineralischen Produkten ist weniger kritisch als bei organisch-mineralischen Systemen (wo CalMag vor Sulfaten gehen muss). Dennoch ist die korrekte fachliche Reihenfolge:

1. Wasser vorlegen (Raumtemperatur)
2. Terra Bloom einruehren (Basisduenger, Prioritaet 20)
3. PK 13-14 einruehren (Booster, mineralisch, Prioritaet 30 -- laut Produktdaten)
4. Power Roots (Prioritaet 60 -- nur wenn noch in dieser Phase verwendet)
5. Sugar Royal (Prioritaet 65)
6. Pure Zym (Prioritaet 70)
7. pH-Kontrolle und Korrektur (immer als letzter Schritt!)

Die korrekte Reihenfolge (Basisduenger vor Boostern vor organischen Additiven) entspricht dem FLOWERING-JSON, nicht dem Delivery-Channel-Text.

**Korrekturvorschlag:**
Delivery-Channel-Text in Abschnitt 3.3 korrigieren auf:
> "Reihenfolge: Terra Bloom -> PK 13-14 (nur W15-16) -> Pure Zym -> Sugar Royal -> pH pruefen"

Damit stimmen Tabelle und JSON ueberein.

---

### T-004: Power Roots Absetzpunkt in FLOWERING unklar -- ein oder zwei Wochen?

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.4 (FLOWERING, Zeile ~217); `spec/ref/products/plagron_power_roots.md`, Abschnitt 3.1

**Problem:**
Der Plan beschreibt in FLOWERING-Notes: "Power Roots absetzen." Dies ist korrekt -- Power Roots ist fuer Wachstum und fruehe Bluete konzipiert. Das Produktdokument gibt als Absetzpunkt "Ende 3. Bluetewoche" an und zeigt im offiziellen Plagron-Schema Power Roots bis Woche 5 (erste Bluetewoche) und Absetzen in Woche 6.

Im Tomaten-Plan wird FLOWERING als Gesamtphase (Wochen 13-17, ca. 5 Wochen Blute) angesetzt. Die Notes sagen "absetzen" -- aber in welcher Woche der FLOWERING-Phase? Am Beginn (Woche 13)? Am Ende der ersten 3 Wochen (Woche 15-16)? Das bleibt unklar.

Im Jahresplan (Abschnitt 5) zeigt die ASCII-Grafik Power Roots bis Mai (VEG->FLOW-Uebergang), also bis zur FLOWERING-Phasengrenze -- also tatsaechlich in Woche 12, nicht in der FLOWERING-Phase. Das widerspricht der Notes-Aussage "Power Roots absetzen" in der FLOWERING-Phase (die impliziert, dass Power Roots zu Beginn von FLOWERING noch laueft und dann abgesetzt wird).

Die fertilizer_dosages im FLOWERING-JSON enthalten Power Roots nicht -- d.h. Power Roots laueft laut JSON schon ab dem ersten Tag von FLOWERING nicht mehr. Das ist die strengste Interpretation und biologisch vertretbar, aber unklar dokumentiert.

**Korrekturvorschlag:**
Im FLOWERING-Phasen-Hinweis praezisieren: "Power Roots wird nicht mehr in der FLOWERING-Phase eingesetzt (Abschluss mit Ende VEGETATIVE, Woche 12). Alternativ koennen die ersten 2 Wochen von FLOWERING noch Power Roots (1 ml/L) enthalten -- dann aus fertilizer_dosages optional entfernen und als Uebergangsoption erlaeutern."

Jahresplan-ASCII-Grafik ggf. anpassen: "==>" fuer Power Roots zeigt Ende April/Anfang Mai -- das entspricht VEGETATIVE-Ende, was konsistent mit dem JSON ist.

---

### T-005: Calcium-Foliarspray als CalMag beschrieben -- Produkt nicht spezifiziert

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.4 (FLOWERING, Zeile ~217) und Abschnitt 6 (BER-Praevention)

**Problem:**
Der Plan empfiehlt an zwei Stellen ein "CalMag-Foliarspray 0.5% an erster Fruchttraube" zur BER-Praevention. "CalMag" ist kein generisches Produkt, sondern ein Produktgattungsname (CANNA CalMag Agent, General Hydroponics CALiMAGic etc.). Im Plagron-Terra-Kontext gibt es kein CalMag-Supplement in der Produktlinie.

Terra Bloom enthaelt 0.8% Mg, aber kein deklariertes Calcium. Damit ist die Terra-Linie fuer Erdkultur auf den Calcium-Gehalt des Leitungswassers und des Substrats angewiesen.

Fuer Foliarspray-BER-Praevention ist der korrekte Wirkstoff **Calciumchlorid (CaCl2)** oder **Calciumnitrat (Ca(NO3)2)** -- je nach Verfuegbarkeit:
- CaCl2: 0.5 g/L als Foliarspray direkt auf junge Fruechte (nicht auf Blaetter); Calcium wird transporter-unabhaengig direkt in Frucht aufgenommen
- Ca(NO3)2: 1.0 g/L ins Giesswasser; traegt etwas Stickstoff mit sich (in Fruchtphase beachten)

Das Wort "CalMag" ohne Produktangabe ist fuer Einsteiger verwirrend und laesst unklar, welches Produkt oder welcher Wirkstoff gemeint ist.

**Korrekturvorschlag:**
Formulierung praezisieren:
- "CalMag-Foliarspray 0.5%" ersetzen durch "Calciumchlorid-Foliarspray (0.5 g CaCl2 pro Liter Wasser) direkt auf junge Fruechte, NICHT auf Blaetter"
- Alternativ-Formulierung: "Bei weichem Leitungswasser (<0.4 mS/cm): Calciumnitrat (Ca(NO3)2) 0.5 g/L ins Giesswasser. Hinweis: Calciumnitrat enthaelt N -- in der Fruchtphase sparsam dosieren."
- Im BER-Praeventions-Abschnitt (Abschnitt 6) den Unterschied CalMag (Ca+Mg-Ergaenzung fuer Hydroponik) vs. Calcium-Supplement (BER-Praevention) erklaeren.

---

### T-006: SEEDLING-Phase -- Pure Zym und Sugar Royal-Startpunkt inkonsistent zwischen Text und Jahresplan

**Schweregrad:** Gering (Konsistenzfehler)

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.2 (SEEDLING, Zeile ~162) vs. Abschnitt 5 (Jahresplan, Zeile ~297)

**Problem:**
In den SEEDLING-Phase-Notes (Abschnitt 4.2) steht: "Noch kein Pure Zym oder Sugar Royal noetig." Das SEEDLING-JSON (Abschnitt 8.2) enthaelt korrekt keine fertilizer_dosages fuer Pure Zym oder Sugar Royal.

Im Jahresplan (Abschnitt 5, Monatstabelle) zeigt der April-Eintrag fuer den Uebergang SEEDLING->VEG: "1.0*" fuer sowohl Pure Zym als auch Sugar Royal -- mit der Fussnote: "*Pure Zym und Sugar Royal ab VEGETATIVE-Phase (ca. Mitte April)."

Die ASCII-Grafik zeigt fuer Pure Zym und Sugar Royal in April das Zeichen "-->==", was Start waehrend April bedeutet. Der SEEDLING-Endpunkt ist Woche 6 (Ende Maerz / Anfang April), VEGETATIVE beginnt in Woche 7 (Anfang bis Mitte April).

Das ist im Wesentlichen korrekt, aber die April-Monatstabellen-Zeile zeigt Pure Zym und Sugar Royal mit voller Dosis (1.0*), waehrend der Plan suggeriert, dass diese erst mit Beginn VEGETATIVE starten. Ein Nutzer der April-Zeile liest moeglicherweise, er solle Pure Zym schon im SEEDLING-April einsetzen.

**Korrekturvorschlag:**
Die April-Zeile des Jahresplans praezisieren: "April" in zwei Teilzeilen aufteilen ("April frueh (SEEDLING)" und "April spaet (VEG)") oder die Fussnote staerker hervorheben: "*ab VEGETATIVE, ca. 15. April (Wochen-Ende 6). In der ersten April-Haelfte (SEEDLING) noch nicht einsetzen."

---

### T-007: FLUSHING-Phase -- target_ec_ms: 0.0 mit Pure Zym (EC-neutrale Substanz) semantisch pruefenswert

**Schweregrad:** Gering

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.6 (FLUSHING), Abschnitt 8.2 FLUSHING JSON (Zeile ~679)

**Problem:**
Sowohl in der Delivery-Channel-Tabelle (Abschnitt 4.6) als auch im FLUSHING-JSON ist `target_ec_ms: 0.0` gesetzt. Pure Zym (0-0-0) liefert tatsaechlich EC = 0.0 mS/cm als eigenen Beitrag.

Das EC-Budget im Text (Zeile ~284) wird korrekt berechnet als: "0.00 (PZ) + ~0.4 (Wasser) = ~0.4 mS/cm".

Das `target_ec_ms: 0.0` im JSON bezieht sich offensichtlich auf den Duenger-EC (0.0 = kein Duenger-Beitrag), nicht auf die Gesamt-Giessloesungs-EC. Fuer ein automatisiertes System, das `target_ec_ms` als Gesamt-EC interpretiert, wuerde 0.0 bedeuten, destilliertes Wasser zu verwenden -- was mit Leitungswasser nicht erreichbar ist.

Vergleiche: In GERMINATION ist ebenfalls `target_ec_ms: 0.0` gesetzt, was analog verwendet wird. Das ist intern konsistent, aber systemaergiebig pruefenswert.

**Korrekturvorschlag:**
Konsistent mit dem Monstera-Review (MN-004): `target_ec_ms: 0.0` fuer Duenger-freie Phasen auf `null` setzen, mit `notes`-Hinweis: "Kein Duenger -- Gesamt-EC entspricht Leitungswasser-EC (~0.3-0.5 mS/cm)." Oder: REQ-004 klaert, ob `target_ec_ms` Duenger-EC oder Gesamt-EC bedeutet.

---

### T-008: HARVEST-Phase NPK-Verhaeltnis (2-2-4) entspricht FLOWERING -- semantisch korrekt, aber pruefenswert

**Schweregrad:** Hinweis (konzeptionell)

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.5 (HARVEST); `spec/ref/plant-info/solanum_lycopersicum.md`, Abschnitt 2.3

**Problem:**
Die HARVEST-Phase setzt `npk_ratio: [2.0, 2.0, 4.0]` -- identisch mit der FLOWERING-Phase. Das tatsaechlich verwendete Produkt (Terra Bloom) hat NPK 2-2-4, was korrekt ist.

Jedoch: Der Pflanzensteckbrief (Abschnitt 2.3) definiert fuer Phase "Fruchtreife" ein NPK-Zielverhaeltnis von **1-2-4** -- mit niedrigerem N-Anteil als in der Bluete. Der Plan bildet die HARVEST-Phase mit Steckbrief-Phase "Fruchtreife" ab, setzt aber NPK 2-2-4 statt 1-2-4.

Terra Bloom 2-2-4 (N 2.1%, P2O5 1.6%, K2O 3.9%) liefert faktisch ein Verhaeltnis naeher an 2:1.5:4 als an 1:2:4. Das Steckbrief-Ideal 1:2:4 wuerde einen hoeheren Phosphor- und niedrigeren N-Anteil erfordern -- erreichbar z.B. mit Haifa Fertigator-Produkten oder spezifischen Tomaten-Duengern. Mit der Terra-Linie als 1-Komponenten-System ist das Steckbrief-Ideal nicht exakt erreichbar.

**Agronomische Einordnung:**
Das Verhaeltnis 2:1.5:4 (Terra Bloom bei 4 ml/L) ist fuer Tomate in der Fruchtphase praxistauglich. Die Abweichung vom 1:2:4-Ideal ist systembedingt (1-Komponenten-Duenger ohne P-separaten Boost). Bei einer Erdbeer-Studie (Haifa Group, 2019) wurde 1:1.5:3 als optimales Fruchtphasen-Verhaeltnis beschrieben -- Terra Bloom liegt nah daran.

**Korrekturvorschlag:**
`npk_ratio` in HARVEST entweder:
- Option A: Auf `[2.0, 2.0, 4.0]` belassen (Produktrealitaet Terra Bloom), aber in `notes` erlaeutern: "Terra Bloom liefert NPK 2-2-4; das Steckbrief-Ideal fuer Fruchtreife ist 1-2-4. Abweichung ist systembedingt (1-Komponenten-Produkt) und praxistauglich."
- Option B: Auf `[1.0, 2.0, 4.0]` setzen als Zielverhaeltnis-Annotation, mit Hinweis auf Steckbrief-Referenz und tatsaechlich geliefertem Verhaeltnis.

---

### T-009: Tabelle Delivery Channel 3.2 listet Sugar Royal in Mischungsreihenfolge -- fehlt im VEGETATIVE-JSON

**Schweregrad:** Gering (Konsistenzfehler)

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 3.2 (Delivery Channel naehrloesung-wachstum, Zeile ~85) vs. Abschnitt 8.2 VEGETATIVE JSON

**Problem:**
Der Delivery-Channel-Hinweis (Abschnitt 3.2) nennt als Mischungsreihenfolge:
> "Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen"

Das VEGETATIVE-JSON (Abschnitt 8.2) listet in `fertilizer_dosages` Sugar Royal mit `optional: true` -- korrekt. Das entspricht dem Text.

Jedoch: Im Tabelleneintrag des VEGETATIVE-Abschnitts (Abschnitt 4.3) wird Sugar Royal als "1.0 ml/L" ohne optional-Markierung aufgefuehrt. Im JSON ist es korrekt als `optional: true` markiert. Die Tabelle vermittelt den Eindruck, Sugar Royal sei Pflicht.

**Korrekturvorschlag:**
In der Tabelle (Abschnitt 4.3, VEGETATIVE Delivery Channel) Sugar Royal mit "(optional)" kennzeichnen, z.B.:
| Sugar Royal ml/L | 1.0 (optional) |

---

### T-010: Leitungswasser-EC-Bandbreite in EC-Budget-Einleitung unterschaetzt

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4 (EC-Budget-Einleitung, Zeile ~116)

**Problem:**
Die EC-Budget-Einleitung gibt an: "Leitungswasser liefert typisch 0.3--0.7 mS/cm (je nach Region)." Das ist eine realistische Bandbreite fuer weiche bis mittelharte Regionen, unterschaetzt aber Extremwerte:

- Weiche Regionen (Schwarzwald, Oberbayern Alpenrand): 0.1-0.3 mS/cm
- Mittelharte Regionen (norddeutsche Tiefebene): 0.3-0.6 mS/cm
- Hartwasserregionen (Muenchen Stadt, Rhein-Ruhr-Gebiet, Wien): 0.6-1.0 mS/cm
- Extremwerte in kalkharten Regionen: bis 1.2 mS/cm

Fuer Tomaten als Starkzehrer ist das weniger kritisch als bei der salzempfindlichen Erdbeere. Bei EC 1.0+ Leitungswasser und Terra Bloom 5 ml/L (EC-Beitrag ~0.5 mS/cm) ergibt sich eine Gesamt-EC von ~1.5 mS/cm -- noch im sicheren Bereich. Bei max. TB 6 ml/L und EC 1.0 Wasser: ~1.6 mS/cm, weiterhin sicher. Das ist kein kritisches Problem, aber eine Praezisierung waere hilfreich.

**Korrekturvorschlag:**
Bandbreite erweitern: "Leitungswasser liefert typisch 0.2--0.8 mS/cm (regionenabhaengig). In Hartwasserregionen (>0.7 mS/cm) Terra-Bloom-Dosis bei Bedarf auf 4 ml/L reduzieren oder 20-30% Regenwasser/Osmosewasser beimischen. EC des lokalen Leitungswassers beim Wasserversorger erfragen oder mit EC-Geraet messen."

---

### T-011: Bestaeubung unter Glas -- elektrische Zahnbuerste nicht als alleinige Methode kennzeichnen

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 4.4 (FLOWERING, Zeile ~217)

**Problem:**
Der Plan empfiehlt korrekt: "Bluetenstaende taeglich leicht schuetteln oder Vibrieren (elektr. Zahnbuerste) -- Tomaten sind Windbestaeuber."

Die Methode ist agronomisch richtig. Erwaehnenswert waere jedoch, dass:
1. **Handbestaeuber (kleine Massagegeraete, spezielle Tomaten-Vibrationsgeraete)** guenstiger und gezielter als Zahnbuersten sind
2. Im Gewaechshaus **Hummeln (Bombus terrestris)** als Standardbestaeuber eingesetzt werden, die den Pollen durch Vibration (Sonikation/Buzz-Bestaeubung) effektiv loesen -- fuer Gewachshaus-Nutzer relevant
3. **Ausloesen durch Luftbewegung** (kleiner Ventilator 5-10 Minuten taeglich) in vielen Faellen ausreicht und einfacher ist als manuelle Bestaeubung

Das sind Verbesserungen, kein Fehler.

**Korrekturvorschlag:**
Hinweis erweitern: "Bestaeubung unter Glas: Bluetenstaende taeglich bei geoeffneten Blueten (10-14 Uhr) leicht schuetteln oder mit Handbestaeuber/Vibrationsstab vibrieren. Alternativ: Kleiner Ventilator 5-10 Minuten Luftbewegung erzeugen (einfachste Methode). Im Gewaechshaus: Hummeln (Bombus terrestris) als Standardbestaeuber."

---

### T-012: Fruchtfolge-Hinweis (3-4 Jahre Solanaceae-Pause) nicht auf Topfkultur kontextualisiert

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/tomate_plagron_terra.md`, Abschnitt 2 (Phasen-Mapping, Zeile ~56) und Abschnitt 6 (Fruchtfolge)

**Problem:**
Der Plan empfiehlt korrekt "3-4 Jahre Anbaupause fuer Solanaceae auf gleicher Flaeche". Dies ist fuer Freilandbeet- und Gewaechshaus-Bodenkultur absolut richtig.

Fuer Topfkultur (Kuebel, Geowebetaschen, Growbags) gilt dieses Prinzip jedoch nur eingeschraenkt:
- In der Topfkultur wird Substrat jedes Jahr erneuert (oder sollte erneuert werden)
- Das Fruchtfolge-Risiko (Phytophthora, Fusarium im Boden) gilt fuer wiederverwendetes Substrat
- Der Plan erwaehnt in der FLUSHING-Phase korrekt: "Substrat nicht wiederverwenden fuer Solanaceae (Krankheitsrisiko)"
- Fuer frisches Substrat im Topf ist die 3-4-Jahres-Regel nicht notwendig

Der fehlende Kontext-Unterschied (Freiland/Gewachshausboden vs. Topf mit frischem Substrat) kann Nutzer unnoetig verunsichern.

**Korrekturvorschlag:**
Im Fruchtfolge-Abschnitt erlaeutern: "3-4 Jahre Solanaceae-Pause gilt fuer Freiland- und Gewachshaus-Bodenkultur (Sporen ueberdauern im Boden). Bei Topfkultur mit jedes Jahr erneuertem Substrat (frische Erde) ist die Fruchtfolge-Pause nicht zwingend -- wichtig ist nur, das alte Substrat nicht fuer Solanaceae wiederzuverwenden."

---

## Konsistenzpruefung: Tabellen versus JSON

| Pruefpunkt | Tabellen-Eintrag | JSON-Eintrag | Status |
|------------|-----------------|--------------|--------|
| GERMINATION: target_ec_ms | 0.0 (Wasser) | 0.0 | Konsistent |
| SEEDLING: target_ec_ms | 0.6 | 0.6 | Konsistent |
| SEEDLING: Terra Grow ml/L | 1.5 | 1.5 | Konsistent |
| SEEDLING: Power Roots ml/L | 1.0 | 1.0 | Konsistent |
| VEGETATIVE: target_ec_ms | 1.5 | 1.5 | Konsistent |
| VEGETATIVE: Terra Grow ml/L | 5.0 | 5.0 | Konsistent |
| VEGETATIVE: Sugar Royal ml/L | 1.0 | 1.0 (optional: true) | Teils inkonsistent -- Tabelle ohne "optional" (T-009) |
| FLOWERING: target_ec_ms (ohne PK) | 1.8 | 1.8 | Konsistent |
| FLOWERING: Terra Bloom ml/L | 5.0 | 5.0 | Konsistent |
| FLOWERING: PK 13-14 ml/L | 0.5 | 0.5 | Konsistent |
| FLOWERING: mixing order | Terra Bloom -> PZ -> SR -> PK | Terra Bloom -> PK -> PZ -> SR | Widerspruch (T-003) |
| HARVEST: target_ec_ms | 1.5 | 1.5 | Konsistent |
| HARVEST: Terra Bloom ml/L | 4.0 | 4.0 | Konsistent |
| HARVEST: Pure Zym | 1.0 | 1.0 | Konsistent |
| HARVEST: Sugar Royal | -- (kein Eintrag) | Fehlt in fertilizer_dosages | Konsistent -- korrekt weggelassen |
| FLUSHING: target_ec_ms | 0.0 | 0.0 | Konsistent (pruefenswert nach T-007) |
| FLUSHING: Pure Zym ml/L | 1.0 | 1.0 | Konsistent |
| Sequenz-Arithmetik: 2+4+6+5+9+2 | 28 Wochen | week_start/week_end korrekt | Konsistent |

---

## Spezifische Pruefung der 12 Review-Punkte

| Nr. | Pruefpunkt | Ergebnis | Finding |
|-----|-----------|----------|---------|
| 1 | Starkzehrer-EC hoch genug? Nicht ueber 2.5 mS/cm? | Korrekt. Max. EC in Giessloessung ~1.05 mS/cm (mit PK). In Erdkultur korrekt dimensioniert. Drainagewasser-EC >2.5 als Alarmsignal dokumentiert. | -- |
| 2 | BER-Praevention -- Calcium und gleichmaessige Bewaesserung | Vorbildlich. Eigener BER-Abschnitt, DRENCH-Methode, Calcium ppm modelliert in FLOWERING/HARVEST. Physiologische Erklaerung (Ca-Transport, nicht Ca-Mangel) korrekt. | T-002 (Mg fehlt) |
| 3 | K:N-Verhaeltnis ab Fruchtphase mindestens 2:1 | Knapp verfehlt. Terra Bloom 2-2-4 liefert K:N = 3.9/2.1 = 1.86:1. Steckbrief-Anforderung 2:1 wird nicht ganz erreicht. | T-001 |
| 4 | PK 13-14 Timing -- nur 1 Woche in Peak-Bluete? | Korrekt und optimal angepasst. 0.5 ml/L (statt 1.5 ml/L) in Woche 15-16, d.h. 1 Woche in der Mitte der 5-woechigen FLOWERING-Phase. Hintergrunderklaerung vollstaendig. | -- |
| 5 | Sugar Royal in HARVEST korrekt weggelassen? | Korrekt und begruendet. "Organischer N foerdert vegetatives Wachstum und verschlechtert Fruchtqualitaet" -- fachlich richtig. | -- |
| 6 | 6 Produkte -- sinnvoll eingesetzt? Mixing-Reihenfolge? | Sinnvoll eingesetzt. Mixing-Reihenfolge hat 1 Widerspruch zwischen Text und JSON in FLOWERING. | T-003 |
| 7 | FLUSHING-Phase am Saisonende korrekt? | Korrekt. September, 2 Wochen, kein Duenger, Pure Zym, reduzierte Bewasserungsfrequenz (3 Tage), Nachreifehinweis (Ethylen-Apfel). | T-007 (minor) |
| 8 | Ausgeizen erwaehnt? | Vorbildlich. Eigener Abschnitt "Ausgeizen", korrekte Technik (Hand statt Messer, TMV-Risiko), Toppen-Zeitpunkt korrekt (Mitte August), determiniert vs. indeterminiert unterschieden. | -- |
| 9 | Solanin-Toxizitaet -- Sicherheitshinweise vollstaendig? | Vollstaendig. Solanin, Tomatin, gruene vs. reife Fruechte, Katzen, Hunde, Kinder, Kontaktdermatitis -- alle relevanten Kategorien abgedeckt. | -- |
| 10 | Phasen-Mapping 28 Wochen realistisch (Maerz-Oktober)? | Realistisch. Maerz-Aussaat Indoor, nach Eisheiligen ins Freiland, Haupternte Juli-August, Saisonende September entspricht mitteleuropaeischem Standard. | -- |
| 11 | Lueckenlos-Pruefung 28 Wochen | Korrekt. 2+4+6+5+9+2 = 28, keine Luecken, keine Ueberschneidungen. | -- |
| 12 | Konsistenz Tabellen <-> JSON | Weitgehend konsistent. 2 Abweichungen gefunden: Mixing-Reihenfolge FLOWERING (T-003), Sugar Royal optional-Flag in Tabelle nicht markiert (T-009). | T-003, T-009 |

---

## Positiv bewertete Aspekte

Die folgenden Elemente des Plans sind fachlich vorbildlich und verdienen explizite Hervorhebung:

**BER-Praevention: Beste-Klasse-Dokumentation**
Der BER-Abschnitt (Abschnitt 6, Zeile ~342) erklaert korrekt, dass Bluetenendfaeule eine Ca-Transportstoerrung ist, NICHT immer ein Ca-Mangel im Substrat. Diese Unterscheidung ist selbst in Fachliteratur fuer Hobby-Gaertner haeufig falsch dargestellt. Die fuenf Ursachen, die Praeventionsmassnahmen und die konkreten Massnahmen bei aufgetretenem BER sind vollstaendig und korrekt. Besonders gut: Der Hinweis, dass die naechste Fruchttraube normal sein kann ("Nicht in Panik verfallen"), entspricht agronomischer Praxis.

**Ausgeiz-Technik vollstaendig und fachlich korrekt**
Der Hinweis "mit der Hand abknipsen, NICHT mit Messer/Schere -- Krankheitsuebertragung (TMV, Bakterien)" ist korrekt und wird selbst in professionellen Anbauanleitungen haeufig vergessen. Der Toppen-Zeitpunkt (Mitte August, 6-8 Wochen vor Saisonende) ist praezise und praxisbewaehrt. Die Unterscheidung determiniert (nicht ausgeizen) vs. indeterminiert (ausgeizen) ist vollstaendig.

**Lycopin-Synthese und Temperatureffekte**
Der Hinweis "Ueber 30 degC wird Lycopin gehemmt -- Fruechte bleiben gelb/orange" und der Hinweis auf Pollensterilitaet bei >32 degC Tag / >25 degC Nacht sind physiologisch korrekt und fuer Indoor-/Gewaechshaus-Nutzer praxisrelevant.

**PK 13-14 tomatenkorrekt angepasst**
0.5 ml/L statt der Cannabis-Standarddosis 1.5 ml/L -- mit expliziter Erklaerung der Dosierungsanpassung -- zeigt, dass das Produkt nicht blindlings aus einem Cannabis-Template uebernommen wurde. Die Begruendung (Tomate profitiert vom P/K-Schub, aber kuerzere und sanftere Anwendung als Cannabis) ist fachlich korrekt.

**Phytophthora-Praevention vollstaendig**
DRENCH als Pflichtmethode, Mulch, Luftzirkulation, Mulchen, Regenschutz, Mischkultur mit Basilikum -- der Abschnitt Krautfaeule-Praevention ist vollstaendig und praxisgerecht.

**Nachreifehinweis (Ethylen-Trick)**
"Gruene Fruechte in Karton mit reifem Apfel nachreifen lassen (Ethylen-Trick)" -- korrekt. Reife Aepfel emittieren Ethylen, das die Lycopin-Synthese in gruenen Tomaten induziert. Physiologisch korrekt und praxisbewaehrt.

**Fruchtfolge-Anbaupause**
"3-4 Jahre Solanaceae-Pause" korrekt und vollstaendig mit Verwandten (Kartoffel, Paprika, Aubergine) und gutem Vor-/Nachfrucht-Repertoire.

**Substrat-Empfehlungen**
Mindest-Topfgroesse 10 L, ideal 20-40 L, pH 5.8-6.5, "Tief pflanzen" (Adventivwurzeln am Stamm) -- alle korrekt und wichtig.

**Jahresverbrauch-Kalkulation**
Formel-Berechnung transparent und korrekt. PK 13-14 Kommentar ("quasi unbegrenzt -- eine 1L-Flasche fuer 250 Pflanzen-Saisons") ist akkurat und humorvoll kommuniziert.

---

## Zusammenfassende Bewertungstabelle

| Finding | Titel | Schweregrad | Empfehlung |
|---------|-------|-------------|------------|
| T-001 | K:N-Verhaeltnis 1.86:1 leicht unter 2:1-Schwellenwert | Wichtig | Dokumentieren und/oder optionalen K-Booster erwaehnen |
| T-002 | Magnesium vollstaendig unmodelliert (magnesium_ppm: null) | Wichtig | magnesium_ppm in FLOWERING/HARVEST ergaenzen |
| T-003 | Mixing-Reihenfolge FLOWERING: Widerspruch Text vs. JSON | Wichtig | Text korrigieren: PK vor Pure Zym |
| T-004 | Power Roots Absetzpunkt in FLOWERING unklar | Hinweis | Zeitpunkt praezisieren |
| T-005 | CalMag-Foliarspray ohne Produktspezifikation | Hinweis | CaCl2 oder Ca(NO3)2 konkret benennen |
| T-006 | Pure Zym / Sugar Royal Start: Tabelle vs. Jahresplan inkonsistent | Gering | Fussnote staerker hervorheben |
| T-007 | target_ec_ms: 0.0 fuer Phasen ohne Duenger semantisch pruefenswert | Gering | null statt 0.0 erwaegen |
| T-008 | NPK-Verhaeltnis HARVEST (2-2-4) vs. Steckbrief-Ideal (1-2-4) | Hinweis | Systembedingte Abweichung dokumentieren |
| T-009 | Sugar Royal VEGETATIVE: Tabelle ohne optional-Markierung | Gering | "(optional)" in Tabelle ergaenzen |
| T-010 | Leitungswasser-EC-Bandbreite unterschaetzt | Hinweis | Obere Grenze auf 0.8 mS/cm anheben |
| T-011 | Bestaeubung: Ventilator-Methode und Hummeln nicht erwaehnt | Hinweis | Als Ergaenzung einfuegen |
| T-012 | Fruchtfolge-Pause nicht fuer Topfkultur kontextualisiert | Hinweis | Topfkultur mit frischem Substrat ausnehmen |

---

## Empfehlung: Dringlichkeit der Korrekturen

**Vor Produktivbetrieb zu korrigieren (Version 1.1):**
1. **T-003:** Mixing-Reihenfolge im Delivery-Channel-Text auf Terra Bloom -> PK 13-14 -> Pure Zym -> Sugar Royal korrigieren.
2. **T-001:** K:N-Verhaeltnis-Hinweis im HARVEST-Abschnitt erlaeutern (1.86:1 statt 2:1, Hintergrunderklaerung ergaenzen).
3. **T-002:** magnesium_ppm in FLOWERING und HARVEST auf 40-60 ppm setzen; Mg-Mangel-Symptomdokumentation ergaenzen.

**In Version 1.2 zu ergaenzen (Should-Have):**
4. **T-005:** Calcium-Foliarspray-Produkt konkretisieren (CaCl2 oder Ca(NO3)2).
5. **T-009:** Sugar Royal in VEGETATIVE-Tabelle als "(optional)" markieren.
6. **T-012:** Fruchtfolge-Hinweis fuer Topfkultur mit frischem Substrat differenzieren.

**Spaetere Version (Nice-to-Have):**
7-12: Alle Hinweis-Findings (T-004, T-006, T-007, T-008, T-010, T-011).

---

## Glossar (Tomate-spezifisch)

- **BER (Blossom End Rot / Bluetenendfaeule):** Physiologische Stoerung durch lokalen Calcium-Transportmangel in der sich entwickelnden Frucht. Sichtbar als braune, eingesunkene Flecken an der Bluetenseite (Unterseite) der Frucht. Ursache ist fast immer unregelmaessige Bewasserung oder zu hohe EC -- nicht Calciummangel im Substrat.
- **Solanin / Tomatin:** Glykoalkaloide in gruenen Teilen von Solanum lycopersicum. In reifen Fruechten auf unbedenkliche Spuren reduziert. Toxisch fuer Katzen, Hunde und bei groesseren Mengen fuer Kinder.
- **Indeterminiert (Stab-Tomate):** Wuchstyp mit unbegrenztem Apikalwachstum -- Pflanze waechst kontinuierlich und benoetigt Ausgeizen und Stuetzstab. Gegenteill: determiniert (Busch-Tomate), kein Ausgeizen noetig.
- **Ausgeizen:** Entfernen der Seitentriebe (Geiztriebe) aus den Blattachseln bei indeterminierten Tomaten. Verhindert unkontrollierten Buschhabitus, foerdert Fruchtgroesse und Luftzirkulation. Technik: Mit der Hand abknipsen bei 3-5 cm Laenge, nie mit Messer (TMV-Uebertragung).
- **Toppen:** Einmalige Entfernung der Wachstumsspitze des Haupttriebs ueber der obersten Bluetetraube, ab Mitte August. Konzentriert Pflanzenenergie in reifende Fruechte.
- **Lycopin:** Roter Carotinoid-Farbstoff in reifen Tomaten; Antioxidans. Synthese wird ab ~30 degC gehemmt (Fruechte bleiben gelb/orange). Wird durch DIF (positive Tagestemperatur-Nachttemperatur-Differenz) gefoerdert.
- **K:N-Verhaeltnis:** Quantitatives Verhaeltnis von Kalium zu Stickstoff in der Naehrstoffversorgung. In der Vegetationsphase ~1:1, ab Fruchtansatz mindestens 2:1 fuer optimale Fruchtqualitaet und Geschmack.
- **Phytophthora infestans:** Oomycet (Scheinpilz), Erreger der Kraut- und Braunfaeule. Wichtigster Tomatenpathogen im Freiland. Verbreitung durch Spritzwasser und hohe Luftfeuchtigkeit. Praeventiv: DRENCH-Bewaesserung, Mulch, keine Bewaesserung ueber Blaetter.
- **Ethylen-Trick:** Nachreifen gruener Tomaten in geschlossenem Karton zusammen mit reifen Aepfeln oder Bananen, die das Reifungshormon Ethylen (C2H4) emittieren und die Lycopin-Synthese in der grueenen Frucht auslosen.
- **GDD (Growing Degree Days / Wachstumsgradtage):** Kumulierte Waermeeinheiten oberhalb einer Basistemperatur (Tomate: 10 degC). Transition Vegetativ -> Bluete tritt bei GDD ~200-450 ein (sortenabhaengig).
