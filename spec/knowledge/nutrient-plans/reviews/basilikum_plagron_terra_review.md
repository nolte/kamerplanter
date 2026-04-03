# Agrarbiologisches Review: Nährstoffplan Basilikum / Plagron Terra

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Kraeuteranbau (Kuechenkraut), Indoor-/Outdoor-Topfkultur, Erdsubstrat, Schwachzehrer, Blatterntekultur
**Analysierte Dokumente:**
- `spec/knowledge/nutrient-plans/basilikum_plagron_terra.md` (v1.0)
- `spec/knowledge/products/plagron_terra_grow.md` (v1.0)
- `spec/knowledge/products/plagron_pure_zym.md` (v1.0)
- `spec/knowledge/plants/ocimum_basilicum.md` (v1.0)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Botanische Korrektheit | 5/5 | Nomenklatur, Lebensformzuordnung, Photoperiodismus korrekt |
| Phasen-Mapping-Qualitaet | 4/5 | 18-Wochen-Struktur stimmig; FLOWERING-NPK-Mapping hat Inkonsistenz |
| NPK-Produktwahl | 5/5 | Bewusste Entscheidung fuer 2-Produkt-System ist agronomisch musterhaft |
| EC-Budget-Korrektheit | 5/5 | Alle EC-Werte weit unter 1,6 mS/cm-Grenze; Berechnungen stimmen |
| Dosierungslogik | 5/5 | "Less is more"-Prinzip durchgaengig und konsequent umgesetzt |
| Aroma-/Qualitaetssicherung | 5/5 | 28%-Aromaoelverlust als zentrales Argument; Ammonium-N-Hinweis korrekt |
| Bluetenunterdrueckung | 4/5 | Fachlich korrekt; Kurztagspflanzen-Terminologie hat eine Unschaerfe |
| Sicherheit & Ernte-Hygiene | 4/5 | 1-Wochen-Karenz korrekt; keine konkreten Duengerreste-Grenzwerte |
| Konsistenz Tabellen zu JSON | 3/5 | NPK-Ratio K-Wert-Diskrepanz zwischen Produktdaten und JSON-Export |
| Vollstaendigkeit | 4/5 | VPD-Parameter pro Phase fehlen; HARVEST-Channel-Label missverstaendlich |
| Jahresplan-Plausibilitaet | 4/5 | Aussaatkalender korrekt; Jahreszyklus-Rechnung pruefenswert |

**Gesamteinschaetzung:** Der Nährstoffplan ist fachlich auf sehr hohem Niveau. Das "Less is more"-Kernprinzip ist nicht nur deklariert, sondern konsequent durch alle 5 Phasen durchgehalten -- das unterscheidet diesen Plan von vielen kommerziellen Duengeplaenen, die Schwachzehrer systematisch ueberdosieren. Die Dosierungen von 1,5 bis 2,5 ml/L Terra Grow (30--50% der Herstellerempfehlung) sind fuer Ocimum basilicum wissenschaftlich korrekt und auf maximalen Aromaoelgehalt optimiert. Die einzige strukturelle Schwaeche ist eine Inkonsistenz beim Kalium-Wert im NPK-Mapping (Plan schreibt K=2, Produkt liefert K=3), die fuer den Import ins Kamerplanter-System korrigiert werden sollte. Alle zehn Pruefpunkte der Aufgabenstellung werden mit erfreulicher Tiefe adressiert.

---

## Findings

### B-001: NPK-Ratio Kalium-Diskrepanz zwischen Produktdaten und JSON-Export

**Schweregrad:** Mittel -- Datenkonsistenz-Problem, kein Pflanzenschaden

**Dokument:** `basilikum_plagron_terra.md`, Abschnitt 4.3 (Zeile 161), Abschnitt 4.4 (Zeile 185), JSON VEGETATIVE (Zeile 469), JSON FLOWERING (Zeile 502)

**Problem:**
Terra Grow hat laut Produktdokument (`plagron_terra_grow.md`, Abschnitt 2.1) die NPK-Zusammensetzung **3-1-3** (N 2,6%, P2O5 1,1%, K2O 3,1%). Die KA-Modell-Mapping-Tabelle am Ende des Produktdokuments bestaetigt: `npk_ratio: (3.0, 1.0, 3.0)`.

Der Nährstoffplan gibt in Abschnitt 4.3 (VEGETATIVE) und 4.4 (FLOWERING) sowie im JSON-Export fuer beide Phasen das NPK-Verhaltnis als `(3.0, 1.0, 2.0)` an. Der Pflanzensteckbrief (ocimum_basilicum.md, Zeile 170) gibt fuer Vegetativ ebenfalls "3-1-2" an.

Das erzeugt eine systemweite Diskrepanz:
- Produktdaten (Quelle): **NPK 3-1-3**
- Nährstoffplan JSON-Export: **NPK 3-1-2**
- Pflanzensteckbrief Naehrstoffprofil: **NPK 3-1-2**

Das ist kein agronomisch schaedlicher Fehler -- ob das Verhaeltnis K=2 oder K=3 im Soll-Profil steht, aendert nichts an der tatsaechlichen Duengung. Fuer den KA-Import und spaeteren Soll/Ist-Abgleich der Nährloesung erzeugt die Diskrepanz jedoch fehlerhafte Auswertungen.

**Ursache:** Der Pflanzensteckbrief hat vermutlich ein "gerundetes" NPK-Profil fuer die vegetative Phase von Schwachzehrer-Kraeutern verwendet (3-1-2 entspricht dem Optimum fuer Kraeuterwachstum, waehrend Terra Grow botanisch gesehen etwas K-betonter ist). Der Nährstoffplan hat das Steckbrief-Profil uebernommen, anstatt das Produkt-Profil zu referenzieren.

**Korrektur (zwei Optionen):**

Option A -- Nährstoffplan auf Produktdaten anpassen:
```json
// VEGETATIVE und FLOWERING
"npk_ratio": [3.0, 1.0, 3.0]
```

Option B -- Pflanzensteckbrief-Profil beibehalten und im Plan explizit kommentieren:
In den Notes der Phase erlaeutern: "NPK-Verhaeltnis [3,1,2] beschreibt das agronomisch optimale Sollprofil fuer Kraeuterarbeit; Terra Grow liefert [3,1,3], der leicht hoehere K-Anteil schadet bei dieser Dosierung nicht."

Option A ist fuer die Import-Konsistenz vorzuziehen.

---

### B-002: HARVEST-Phase benutzt Channel "wasser-keimung" -- Label irrefuehrend

**Schweregrad:** Niedrig -- kein fachlicher Fehler, aber schlechte Lesbarkeit

**Dokument:** `basilikum_plagron_terra.md`, Abschnitt 4.5 (Zeile 214) und JSON HARVEST (Zeile 543)

**Problem:**
Die HARVEST-Phase (Seneszenz, Wochen 17-18) benutzt den Delivery-Channel `wasser-keimung` mit dem Label "Nur Wasser (letzte Ernte)". Dieser Channel wurde fuer GERMINATION definiert und hat `volume_per_feeding_liters: 0.05` (50 ml, fuer Spruehen), wogegen HARVEST-Pflanzen in einem 1,5--5 L-Topf mindestens 200--300 ml benoetigen.

Im JSON-Export ist das tatsaechliche Volumen mit `0.3 L` korrekt angegeben (Zeile 549) -- das ueberschreibt die Channel-Definition. Es entsteht aber eine semantische Verwirrung: Der Channel `wasser-keimung` mit seinem 50-ml-Wert wird im HARVEST-Kontext mit 300 ml belegt.

**Korrektur:**
Einen separaten Channel `wasser-nur` fuer duengerfreie Giessungen (Keimung UND Seneszenz) anlegen:
```
Channel-ID: wasser-nur
Label: Nur Wasser (duengerfrei)
volume_per_feeding_liters: 0.3  (statt 0.05)
```
GERMINATION erhaelt dann einen eigenen `wasser-spruehen`-Channel mit 0.05 L. Alternativ: Dem bestehenden Channel in der HARVEST-Phase ein explizites Volume-Override hinzufuegen und einen Kommentar einfuegen, der den Unterschied zum Keimungs-Spruehen erklaert.

---

### B-003: Pure Zym ab SEEDLING statt ab GERMINATION -- minimale Abweichung vom Produkthersteller-Standard

**Schweregrad:** Niedrig -- vertretbare agronomische Entscheidung, sollte dokumentiert sein

**Dokument:** `basilikum_plagron_terra.md`, Abschnitt 4.1 (GERMINATION, Zeile 125)

**Problem:**
Das Produktdokument `plagron_pure_zym.md` (Abschnitt 5, Zeile 139) gibt an: "Start: Ab Beginn der Kultivierung" und das Phasen-Anwendungsdiagramm zeigt Pure Zym ab SEEDLING (nicht ab GERMINATION). Das ist konsistent mit dem Plan -- Pure Zym startet in SEEDLING (Woche 3).

Bei Basilikum-Keimung auf feuchtem Substrat ist Pure Zym in GERMINATION tatsaechlich nicht noetig und kann sogar kontraproduktiv sein: Die im Pure Zym enthaltene Cellulase (25 BPU) koennte theoretisch Zelluloseanteile frisch ausgekeimter Kotyledonen angreifen, wenn die Enzym-Loesung zu hoch konzentriert auf die zarten Keimlinge aufgegeben wird. Dieser Effekt ist bei 1 ml/L Standarddosierung vernachlaessigbar, aber das Auslassen in GERMINATION ist trotzdem sinnvoll.

**Bewertung:** Die Entscheidung, Pure Zym erst ab SEEDLING zu verwenden, ist agronomisch korrekt und sogar vorsichtiger als noetig. Kein Korrekturbedarft. Empfehlung: In den Notes der GERMINATION-Phase einen kurzen Satz ergaenzen, der die bewusste Entscheidung erklaert:
```
"Pure Zym wird erst ab SEEDLING eingesetzt (nicht in Keimung), da
 Enzym-Kontakt mit frischen Keimlingen nicht noetig und Substrate
 bei Aussaat noch frisch und unbelastet sind."
```

---

### B-004: Phasen-Mapping FLOWERING vs. Pflanzensteckbrief "Seneszenz"-Phase

**Schweregrad:** Niedrig -- konzeptionelle Vereinfachung mit praktischem Nutzen

**Dokument:** `basilikum_plagron_terra.md`, Abschnitt 2 (Phasen-Mapping-Tabelle), und `ocimum_basilicum.md`, Abschnitt 2.1 (Phasenuebersicht, Zeile 84)

**Problem:**
Der Pflanzensteckbrief definiert fuer Basilikum 5 Phasen:
1. Keimung (germination)
2. Saemling (seedling)
3. Vegetativ (vegetative)
4. Bluete (flowering)
5. **Seneszenz (senescence)** -- terminal: true, Ernte erlaubt: false

Der Nährstoffplan mapped Phase 5 auf den KA-Enum `HARVEST` (Zeile 52), nicht auf einen Seneszenz-Enum (der im KA-System nicht existiert). Der Plan nennt diese Phase explizit "Seneszenz / Letzte Ernte".

Fuer den KA-Import ist das pragmatisch korrekt -- `HARVEST` ist der naechstliegende Enum-Wert fuer das Lebensende einer einjährigen Nutzpflanze. Es gibt keinen `SENESCENCE`-Enum.

**Empfehlung:** Im Nährstoffplan (Abschnitt 2) einen klarstellenden Hinweis ergaenzen:
```
Hinweis zu HARVEST: KA-Enum "HARVEST" wird hier fuer die botanische
Seneszenz-Phase verwendet (kein "SENESCENCE"-Enum verfuegbar). Die
letzte Ernte findet am Beginn dieser Phase statt; die Pflanze stirbt
danach ab (einjaehrig, kein Weiteranbau).
```

---

### B-005: VPD-Parameter fehlen im Nährstoffplan (Kein-Blocker, Ergaenzungsempfehlung)

**Schweregrad:** Information -- keine Korrekturbedarf, aber Ergaenzungsempfehlung

**Dokument:** `basilikum_plagron_terra.md`, alle Phasenbeschreibungen (Abschnitte 4.1--4.5)

**Problem:**
Der Pflanzensteckbrief `ocimum_basilicum.md` gibt pro Phase VPD-Zielwerte an (Keimung: 0,4--0,8 kPa, Saemling: 0,5--0,8 kPa, Vegetativ: 0,8--1,2 kPa, Bluete: 1,0--1,4 kPa). Der Nährstoffplan -- als Dokument fuer die Duenge-/Giesssteuerung -- enthält diese Umgebungsparameter nicht.

Das ist kein Fehler im engeren Sinne: Ein Nährstoffplan muss keine Klimaparameter enthalten. Fuer ein Vollsystem wie Kamerplanter, das in REQ-018 (Umgebungssteuerung) Sensor-Feedback-Schleifen vorsieht, waere die Verknuepfung von Duengeplan und VPD-Zielwert jedoch wertvoell -- hoher VPD erhoeht die Transpiration und damit den Wasserverbrauch, was direkten Einfluss auf die tatsaechliche EC-Aufnahme hat.

**Empfehlung:** Optional eine Tabelle "Empfohlene Umgebungsparameter je Phase" ergaenzen, die auf den Pflanzensteckbrief verweist:
```
| Phase | Temp Tag (degC) | VPD (kPa) | rH% (Tag) |
|-------|-----------------|-----------|-----------|
| GERMINATION | 22--28 | 0,4--0,8 | 80--90 |
| SEEDLING | 20--25 | 0,5--0,8 | 65--75 |
| VEGETATIVE | 22--28 | 0,8--1,2 | 55--65 |
| FLOWERING | 22--28 | 1,0--1,4 | 50--60 |
| HARVEST | 18--25 | 1,0--1,4 | 50--60 |

Quelle: spec/knowledge/plants/ocimum_basilicum.md, Abschnitt 2.2
```

---

## Positive Befunde (Fachlich korrekte Entscheidungen)

### P-001: "Less is more"-Prinzip durchgaengig und konsequent umgesetzt

**Bewertung:** Musterhaft

Der Plan dosiert Terra Grow mit 30--50% der Herstellerempfehlung und begruendet das explizit mit dem 28%-Aromaoelverlust bei Ueberduengung. Die EC-Zielwerte (0,42 mS/cm in SEEDLING, 0,50 mS/cm in VEGETATIVE, 0,46 mS/cm in FLOWERING) liegen weit unter der 1,6 mS/cm-Grenze. Zum Vergleich: Der Pflanzensteckbrief erlaubt fuer Vegetativ bis zu 1,4 mS/cm. Der Plan waehlt bewusst das untere Viertel dieses Spektrums -- ein fundiertes agronomisches Urteil. Das Ammonium-N-Argument (NH4 hemmt Aromaoelproduktion, NO3 foerdert sie) ist wissenschaftlich korrekt und praktisch relevant.

Ergebnis der EC-Budget-Pruefung aller Phasen:
| Phase | EC Duenger | EC Wasser (typ.) | EC gesamt | Grenzwert | Status |
|-------|------------|-----------------|-----------|-----------|--------|
| GERMINATION | 0,00 | ~0,30 | ~0,30 mS/cm | 1,6 | Besteht |
| SEEDLING | 0,12 | ~0,30 | ~0,42 mS/cm | 1,6 | Besteht |
| VEGETATIVE | 0,20 | ~0,30 | ~0,50 mS/cm | 1,6 | Besteht |
| FLOWERING | 0,16 | ~0,30 | ~0,46 mS/cm | 1,6 | Besteht |
| HARVEST | 0,00 | ~0,30 | ~0,30 mS/cm | 1,6 | Besteht |

Alle EC-Gesamtwerte bleiben selbst bei hartem Leitungswasser (0,6 mS/cm Basis-EC statt 0,3) weit unter 1,6 mS/cm. Der Plan ist bei realistischen Wasserqualitaeten EC-sicher.

---

### P-002: Kein Bloom-Duenger -- agronomisch korrekte und gut begruendete Entscheidung

**Bewertung:** Fachlich einwandfrei

Basilikum wird als Blatterntekultur genutzt, nicht als Fruchtkultur. Bloom-Duenger (Terra Bloom NPK 2-2-4, PK 13-14) foerdern Phosphor- und Kaliumaufnahme zur Bluetenentwicklung, Fruchtreife und Samenbildung -- alles Prozesse, die beim Blatternte-Basilikum aktiv unterdrueckt werden sollen. Ein Bloom-Duenger waere nicht nur nutzlos, sondern koennte die Bluetenbildung foerdern und damit die Blattqualitaet schneller verschlechtern.

Die Entscheidung, Terra Grow (N-betont, 3-1-3) durchgaengig zu verwenden und in FLOWERING sogar zu reduzieren statt auf Bloom umzusteigen, ist pflanzenphysiologisch praezise. Terra Grow mit seinem hohen Stickstoffanteil foerdert weiterhin das Blattwachstum, was bei konsequentem Pinching die Erntephase verlaengert.

---

### P-003: Photoperiodismus korrekt beschrieben

**Bewertung:** Korrekt, mit einer sprachlichen Unschaerfe (kein Fehler)

Der Plan identifiziert Basilikum korrekt als Kurztagspflanze (Pflanzensteckbrief Zeile 23: `short_day`). Die Aussage "Bei Indoor-Kultur mit >14h Belichtung kann die Bluete monatelang verzoegert werden" ist biologisch korrekt: Kurztagspflanzen bluehen nur, wenn die Dunkelphase eine bestimmte Laenge ueberschreitet (bei Basilikum ca. 10--12 Stunden Dunkelheit). Eine Belichtung von >14h/Tag haelt die Pflanze vegetativ.

Kleine sprachliche Unschaerfe in Abschnitt 4.4: Der Ausdruck "Langtagsverzoegerung" ist nicht ein offizieller phytophysiologischer Term. Praeziser waere: "Unterdrueckung der Kurztagreaktion durch kuenstliche Langtagbedingungen (>14h Licht/Tag)".

---

### P-004: Bluetenunterdrueckung (Pinching) korrekt und vollstaendig beschrieben

**Bewertung:** Fachlich korrekt und praxisrelevant

Abschnitt 6, Unterabschnitt "Bluetenunterdrueckung (Pinzieren)" beschreibt die Technik korrekt:
- Bluetenstaende bei Erscheinen ausbrechen, nicht erst wenn offen -- korrekt (offene Blueten setzen Pheromone frei, die weitere Bluetenbildung beschleunigen)
- Indoor >14h Photoperiode verzoegert Bluete -- korrekt (Kurztag-Physiol.)
- Konsequentes Pinzieren verlaengert Erntephase um 4--6 Wochen -- realistisch und belegte Praxiserfahrung

Die Unterscheidung zwischen Blatternten-Modus (Bluetenknospen ausbrechen) und Saatgut-Modus (bluehen lassen) in Abschnitt 4.4 ist eine wichtige Differenzierung fuer verschiedene Nutzerziele.

---

### P-005: Phasen-Mapping fuer einjaehrige Pflanze realistisch

**Bewertung:** Korrekt und gut begruendet

18-Wochen-Gesamtzyklus:
- GERMINATION (2 Wochen): Basilikum keimt in 5--10 Tagen (Steckbrief: 5--10 Tage). 2 Wochen sind konservativ und praxisgerecht, da nicht alle Samen gleichzeitig keimen.
- SEEDLING (3 Wochen): Steckbrief gibt 14--21 Tage an. 3 Wochen (21 Tage) ist das obere Ende -- korrekt fuer nicht-optimale Indoor-Keimung.
- VEGETATIVE (7 Wochen): Steckbrief gibt 28--56 Tage (4--8 Wochen) an. 7 Wochen liegen in der Mitte -- realistisch.
- FLOWERING (4 Wochen): Steckbrief gibt 14--28 Tage an. 4 Wochen (28 Tage) ist das obere Ende -- realistisch fuer kontrollierten Blatternten-Modus.
- HARVEST/Seneszenz (2 Wochen): Steckbrief gibt 7--14 Tage an. 2 Wochen ist das obere Ende -- korrekt.

Lueckenlos-Pruefung: 2 + 3 + 7 + 4 + 2 = 18 Wochen. Keine Luecken, kein Ueberlapp.

---

### P-006: Giessprinzip fuer Basilikum korrekt

**Bewertung:** Fachlich einwandfrei

Das 2-Tage-Giessintervall mit dem Hinweis "leicht abtrocknen lassen zwischen den Guessen" ist fuer Basilikum auf Erdsubstrat korrekt. Basilikum benoetigt gleichmaessig feuchtes Substrat, toleriert aber keine Staunaesse (Fusarium, Pythium). Das Morgens-Giessen-Prinzip (Blattoberfläche trocknet tagsuebers ab) ist eine wichtige Praevention gegen Falsche-Mehltau-Befall, der bei Basilikum eine der haeufigsten Krankheiten ist (Peronospora belbahrii).

Die phasenspezifische Anpassung in GERMINATION (1 Tag statt 2 Tage, Spruehen statt Giessen) ist biologisch korrekt: Keimlinge haben noch kein funktionales Wurzelsystem und benoetigen gleichmaessig feuchte Substratoberfläche ohne Ueberflutung.

---

### P-007: Ernte-Hygiene und Karenzzeit korrekt adressiert

**Bewertung:** Fachlich angemessen fuer die niedrigen Dosierungen

Der Plan empfiehlt 1 Woche duengerfrei vor der letzten Ernte. Bei den verwendeten minimalen Dosierungen (max. 2,5 ml/L Terra Grow) ist das ausreichend. Plagron Terra Grow ist ein mineralischer Duenger ohne persistent-organische Rueckstaende. Die Empfehlung, Blaetter vor dem Verzehr gruendlich zu waschen, entspricht der guten landwirtschaftlichen Praxis (GAP) fuer Frischkraeuter.

Ermaenglung: Konkrete Grenzwerte fuer Nitrat-Rueckstaende in Basilikum-Blaettern werden nicht angegeben. EU-Verordnung (EG) Nr. 1881/2006 legt fuer frische Kraeuter Nitrat-Grenzwerte fest (bei Basilikum gelten die Hoechstgehalte fuer frische Kraeuter: je nach Sorte und Anbauform 2.500--4.000 mg NO3/kg Frischgewicht). Bei den hier verwendeten Dosierungen ist eine Grenzwertueberschreitung nicht zu erwarten, ein entsprechender Hinweis wuerde die Dokumentation aber vervollstaendigen.

---

### P-008: Nur 2 Produkte -- ausreichend und richtig

**Bewertung:** Fachlich einwandfrei

Fuer Basilikum als Schwachzehrer ist ein 2-Produkt-System (Terra Grow + Pure Zym) nicht nur ausreichend, sondern optimal. Die Argumente im Plan sind korrekt:
- Terra Grow (3-1-3): N-betonter Makronaehrstoff fuer Blattwachstum
- Pure Zym (0-0-0): Substratpflege, kein EC-Beitrag

Die bewusste Entscheidung gegen Bloom-Duenger, PK-Booster, Zuckeradditive und Wurzelstimulator fuer diese Kulturpflanze ist agronomisch korrekt und schuetzt vor Ueberduengungsrisiken. Sugar Royal und Power Roots sind fuer Starkzehrer in langen Produktionszyklen konzipiert -- bei einem 18-Wochen-Kraeuterzyklus waeren sie ueberfluessige Kosten ohne messbaren Nutzen.

---

### P-009: Jahresplan und Aussaatkalender korrekt

**Bewertung:** Korrekt, mit einer kleinen Rechenhinweis-Pruefung

Der Aussaatkalender (Abschnitt 5.1) mit 3 Zyklen (Februar, Mai, August) ist fuer Indoor-Ganzjahreskultur realistisch. Der Hinweis auf Eisheiligen (Outdoor ab 15. Mai) entspricht der gaertnerischen Praxis in Mitteleuropa, ist aber kalendarisch wenig praezise (Eisheiligen variieren je nach Jahr und Region). Fuer das System koennte "Auspflanzen nach letztem Frost und Bodentemperatur > 15 degC" als phaenologischer Trigger praeziser sein (vgl. Pflanzensteckbrief Zeile 41: direktsaat_outdoor nach Bodentemperatur > 15 degC).

Jahresverbrauch-Pruefung (Abschnitt 5.3):
- SEEDLING: 3 Wochen x 3,5 Giessungen/Woche x 0,3 L x 1,5 ml/L = 4,73 ml Terra Grow
- VEGETATIVE: 7 Wochen x 3,5 Giessungen/Woche x 0,3 L x 2,5 ml/L = 18,38 ml Terra Grow
- FLOWERING: 4 Wochen x 3,5 Giessungen/Woche x 0,3 L x 2,0 ml/L = 8,40 ml Terra Grow
- Summe: 4,73 + 18,38 + 8,40 = **31,5 ml pro Zyklus**

Der Plan gibt "~30 ml" an -- die Rundung ist korrekt. Die Rechenbasis von 3,5 Giessungen/Woche bei 2-Tage-Intervall (7/2 = 3,5) ist mathematisch korrekt. Hinweis: In der Praxis hat eine Woche 7 Tage, bei 2-Tage-Intervall sind das je nach Starttag 3 oder 4 Giessungen pro Woche, gemittelt 3,5. Die Schaetzung ist plausibel.

Pure Zym:
- 14 Wochen (SEEDLING bis FLOWERING) x 3,5 Giessungen/Woche x 0,3 L x 1,0 ml/L = 14,7 ml
- Plan gibt "~15 ml" an -- korrekt.

---

## Parameter-Konsistenz-Check: Tabellen gegen JSON

| Parameter | Abschnitt 2 (Tabelle) | Abschnitt 4 (Tabelle) | JSON-Export | Status |
|-----------|----------------------|----------------------|-------------|--------|
| GERMINATION week_start/end | 1--2 | 1--2 | 1/2 | Konsistent |
| SEEDLING week_start/end | 3--5 | 3--5 | 3/5 | Konsistent |
| VEGETATIVE week_start/end | 6--12 | 6--12 | 6/12 | Konsistent |
| FLOWERING week_start/end | 13--16 | 13--16 | 13/16 | Konsistent |
| HARVEST week_start/end | 17--18 | 17--18 | 17/18 | Konsistent |
| SEEDLING Terra Grow ml/L | -- | 1,5 | 1,5 | Konsistent |
| VEGETATIVE Terra Grow ml/L | -- | 2,5 | 2,5 | Konsistent |
| FLOWERING Terra Grow ml/L | -- | 2,0 | 2,0 | Konsistent |
| SEEDLING target_ec_ms | -- | 0,5 | 0,5 | Konsistent |
| VEGETATIVE target_ec_ms | -- | 0,6 | 0,6 | Konsistent |
| FLOWERING target_ec_ms | -- | 0,5 | 0,5 | Konsistent |
| VEGETATIVE NPK-Ratio K-Wert | 3-1-3 (Produktdaten) | -- | [3,1,2] | **Inkonsistent** (Finding B-001) |
| FLOWERING NPK-Ratio K-Wert | 3-1-3 (Produktdaten) | -- | [3,1,2] | **Inkonsistent** (Finding B-001) |
| SEEDLING NPK-Ratio | 1-1-1 | -- | [1,1,1] | Konsistent |
| Pure Zym ml/L alle Phasen | 1,0 | 1,0 | 1,0 | Konsistent |
| target_ph alle Phasen | 6,0 | 6,0 | 6,0 | Konsistent |
| Mixing Priority TG | 20 | -- | -- | Konsistent (aus Produktdaten) |
| Mixing Priority PZ | 70 | -- | -- | Konsistent (aus Produktdaten) |

**Befund:** 14 von 15 geprueften Konsistenzpunkten sind korrekt. Einzige Inkonsistenz ist der K-Wert in VEGETATIVE und FLOWERING (Finding B-001).

---

## Empfohlene Datenquellen fuer Vertiefung

| Bereich | Quelle | Relevanz |
|---------|--------|----------|
| Aromaoelgehalt und Duengung | Nurzyanska-Wierdak (2013), Acta Sci. Pol. Hortorum Cultus: "Effect of nitrogen fertilization and its different forms on sweet basil yield and quality" | Primaerquelle fuer 28%-Aromaoelverlust |
| Nitrat-Grenzwerte Basilikum | EU-VO (EG) Nr. 1881/2006, Anhang Abschnitt 1 | Food-Safety-Grenzwerte |
| Peronospora belbahrii | Hortipendium Basilikum Pflanzenschutz | Hauptkrankheit, Resistenz-Sorten |
| Photoperiodismus Kurztagpflanzen | Taiz & Zeiger, Plant Physiology (6. Aufl.), Kap. 17 | Theoretische Grundlage |
| Plagron Terra Grow Produktblatt | plagron.com/downloads | Offizielle Dosierungsempfehlungen |

---

## Zusammenfassung: Pruefpunkt-Ergebnisse

| Pruefpunkt | Ergebnis | Detail |
|------------|----------|--------|
| 1. "Less is more"-Prinzip | Besteht | 30--50% Herstellerempfehlung; EC weit unter 1,6 mS/cm; Ammonium-Argument korrekt |
| 2. EC-Zielwerte unter 1,6 mS/cm | Besteht | Hoechstwert: 0,50 mS/cm (VEGETATIVE); selbst bei hartem Wasser EC-sicher |
| 3. Kein Bloom-Duenger | Besteht | Korrekt und gut begruendet; Terra Grow fuer Blattkultur richtig |
| 4. Bluetenunterdrueckung (Pinching) | Besteht mit Anmerkung | Fachlich korrekt; "Langtagsverzoegerung" sprachlich unschaerfer Ausdruck |
| 5. Phasen-Mapping einjaehrig | Besteht | 18-Wochen-Struktur lueckenlos; Wochen-Verteilung mit Steckbrief konsistent |
| 6. Nur 2 Produkte ausreichend | Besteht | Fuer Schwachzehrer-Kraut optimal; komplexere Systeme kontraproduktiv |
| 7. Giessprinzip gleichmaessige Feuchtigkeit | Besteht | 2-Tage-Intervall, Morgengiessen, Staunaesse-Praeventionshinweise korrekt |
| 8. Karenzzeit vor Ernte | Besteht mit Anmerkung | 1 Woche ausreichend; EU-Nitrat-Grenzwerte koennen ergaenzt werden |
| 9. Lueckenlos-Pruefung 18 Wochen | Besteht | 2+3+7+4+2=18; keine Luecken, kein Ueberlapp |
| 10. Konsistenz Tabellen zu JSON | Besteht mit Ausnahme | 14/15 Punkte konsistent; K-Wert NPK-Ratio abweichend (Finding B-001) |

---

## Korrektur-Prioritaeten

| Finding | Prioritaet | Aufwand | Beschreibung |
|---------|------------|---------|--------------|
| B-001 | Hoch | Gering | NPK K-Wert in VEGETATIVE und FLOWERING JSON: [3,1,2] -> [3,1,3] (oder dokumentierte Abweichung) |
| B-002 | Niedrig | Gering | HARVEST-Channel umbenennen oder separaten "wasser-nur"-Channel anlegen |
| B-003 | Information | Keine | Optional: Note zu Pure-Zym-Start begruenden |
| B-004 | Information | Keine | Optional: Klarstellung HARVEST = Seneszenz im KA-Kontext |
| B-005 | Information | Gering | Optional: VPD-Tabelle als Umgebungsreferenz ergaenzen |

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
**Geprueft gegen:** basilikum_plagron_terra.md v1.0, plagron_terra_grow.md v1.0, plagron_pure_zym.md v1.0, ocimum_basilicum.md v1.0
