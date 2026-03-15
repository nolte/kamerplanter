# Agrarbiologisches Review: Nährstoffplan Erdbeere (einmaltragend) / Plagron Terra

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Outdoor-Topfkultur, Fruchtgemüse/Obstpflanze, Erdkultur, saisonaler Anbau
**Analysierte Dokumente:**
- `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md` (v1.0)
- `spec/ref/products/plagron_terra_grow.md` (v1.0)
- `spec/ref/products/plagron_terra_bloom.md` (v1.0)
- `spec/ref/products/plagron_pk_13_14.md` (v1.0)
- `spec/ref/products/plagron_power_roots.md` (v1.0)
- `spec/ref/products/plagron_pure_zym.md` (v1.0)
- `spec/ref/products/plagron_sugar_royal.md` (v1.0)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Botanische Korrektheit | 5/5 | Nomenklatur, Sortennennung und Lebensformzuordnung korrekt |
| Phasen-Mapping-Qualitaet | 3/5 | Grundstruktur agronomisch plausibel, aber FLUSHING-Timing und SEEDLING-Mapping haben Schwaechen |
| NPK-Produktwahl | 4/5 | Terraline fuer Erdbeere geeignet; PK 13-14 fuer Erdbeere konzeptionell falsch platziert |
| EC-Budget-Korrektheit | 4/5 | Konservative EC-Werte erdbeergerecht; Leitungswasser-Basis-EC-Bandbreite zu eng angegeben |
| Dosierungslogik | 3/5 | Terra Grow Maximaldosis (4 ml/L) nicht erdbeeroptimiert; Sugar Royal 9-0-0 in HARVEST-Phase pruefenswert |
| Erdbeer-spezifische Hinweise | 4/5 | Vernalisation, Auslaeufer, Frostschutz gut; Botrytis-Praevention, Calcium-Bedarf fehlen |
| Vollstaendigkeit Praxishinweise | 3/5 | Bestaeuber fehlen; Bewasserungsverhalten bei Regen nicht adressiert; Chlorempfindlichkeit fehlt |
| Praktische Umsetzbarkeit | 4/5 | Jahresplan und ASCII-Chart gut lesbar; Jahresverbrauch korrekt berechnet |

**Gesamteinschaetzung:** Der Nährstoffplan ist fuer eine erste Version gut strukturiert und in den agronomischen Grundzuegen korrekt. Die Entscheidung fuer konservative EC-Werte ist fuer die salzempfindliche Erdbeere richtig. Die groessten Schwaechen liegen in der Verwendung von PK 13-14 (ein Cannabis-/Hochertrag-Booster mit 1,5 ml/L Standarddosierung) fuer eine Kulturpflanze mit EC-Toleranz unter 1,5 mS/cm, in der fehlenden Calcium-Modellierung trotz bekannter Calcium-Sensitivitaet der Erdbeere (Bluetenendenfaeule) sowie im Fehlen von Botrytis-Praevention und Bestaeubungshinweisen fuer Topfpflanzen auf Balkon/Terrasse. Die FLUSHING-Phase im August ist kalendarisch problematisch (Hochsommerhitze, Trockenstress). Insgesamt ist der Plan mit gezielten Korrekturen fuer den Produktivbetrieb geeignet.

---

## Findings

### E-001: PK 13-14 Dosierung inkompatibel mit Erdbeer-EC-Toleranz

**Schweregrad:** Kritisch

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 4.4 und EC-Budget-Tabelle (Zeile ~108)

**Problem:**
Das Referenzdokument `spec/ref/products/plagron_pk_13_14.md` gibt als Standarddosierung **1,5 ml/L** an, als intensive Anwendung **2,0 ml/L** und als vorsichtige Anwendung fuer empfindliche Sorten **1,0 ml/L**. Der EC-Beitrag bei 1,5 ml/L betraegt laut PK-Dokument ~0,4--0,6 mS/cm extra. Das PK 13-14 wurde jedoch im Plan auf **0,5 ml/L** reduziert, was ungefaehr 0,15 mS/cm EC-Beitrag entspricht -- weit unter der Produktspezifikation.

Das grundlegende Problem: PK 13-14 ist ein Booster-Produkt, das **fuer Cannabis und hochertragige Kulturen mit EC-Toleranzen von 1,8--2,4 mS/cm** konzipiert ist. Das Produktdokument beschreibt explizit Zielsorten (Indica, Sativa, Hybrid, Autoflowering) und spricht von "Bluetenexplosion", "Trichom-Dichte", "Cannabinoid-Synthese" und "15--25% Ertragssteigerung" -- Konzepte, die fuer Erdbeeren nicht relevant sind.

Fuer *Fragaria x ananassa* im Topf gelten folgende wissenschaftlich belegte Grenzwerte:
- Optimale EC der Naehrloesung: **0,8--1,4 mS/cm**
- Kritische Oberkante: **1,5--1,8 mS/cm** (Ertragsverlust, Blattrollen, Spitzenverbrennung)
- Schaedliche EC: **> 2,0 mS/cm** (osmotischer Stress, Ertragseinbruch)

Das Produkt PK 13-14 ist in seiner Konzeption und seinem Dosierungsrahmen nicht fuer Erdbeeren geeignet. Ein P/K-Boost zu Blutebeginn ist zwar biologisch korrekt (Erdbeere benoetigt erhoehtes P und K zur Fruchtbildung), sollte aber mit einem erdbeergeeigneten Mittel erfolgen.

**Korrekturvorschlag:**
Option A: PK 13-14 vollstaendig aus dem Plan entfernen. Der erhoehte P/K-Bedarf zur Bluetephase wird bereits durch **Terra Bloom (NPK 2-2-4)** in voller Dosis (4 ml/L, EC-Beitrag 0,4 mS/cm) gedeckt.

Option B: Wenn PK 13-14 beibehalten werden soll, muss die Dosierung auf **0,3 ml/L** reduziert werden (EC-Beitrag ~0,09 mS/cm) und ein expliziter Warnhinweis eingefuegt werden: "Nur fuer Sorten mit erhoehter EC-Toleranz; bei Blattrandnekrosen sofort absetzen."

Option C: Ersetzen durch **Kali-Phosphat (KH2PO4)** in Kleinstdosierung oder durch ein fuer Beeren/Fruchtgemuese konzipiertes P/K-Supplement mit niedrigerem Konzentrationsniveau.

---

### E-002: FLUSHING im August agronomisch fragwuerdig

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 2 (Phasen-Mapping), Zeilen 51 und ~248

**Problem:**
Die FLUSHING-Phase ist auf Kalenderwochen 29--32 gelegt, was ca. **Anfang bis Ende August** entspricht -- dem heissesten Abschnitt des mitteleuropaeischen Sommers. In dieser Phase erhaelt die Pflanze laut Plan nur **klares Wasser im 5-Tage-Intervall** ("reduziert"). Das ist physiologisch problematisch:

1. **Hitze- und Trockenstress:** Bei 25--35 Grad C Aussentemperatur und Topfkultur (5 L Substrat) trocknet das Substrat unter Umstaenden innerhalb von 1--2 Tagen aus. Ein 5-Tage-Intervall kann in heissen August-Perioden zu Trockenstress und Blattwelke fuehren.

2. **Naehrstoffentzug nach der Ernte:** Einmaltragende Erdbeeren schliessen die Haupternte typischerweise Mitte bis Ende Juli ab (je nach Witterung). Nach der Ernte beginnt die Pflanze unmittelbar mit der **Kronenbildung fuer das naechste Jahr** -- ein aktiver Wachstumsprozess, der Stickstoff und Kalium benoetigt. Eine 4-woechige Duengungspause direkt nach der Ernte schwaecht die Regeneration.

3. **Biologische Bedeutung des Augusts fuer einmaltragende Sorten:** August bis September ist bei *Fragaria x ananassa* (Kurztagspflanze) eine kritische Periode fuer die **Blueteninitiierung der naechsten Saison**. Die Pflanze legt in dieser Zeit die Grundlage fuer die Bluetenanlage des Folgejahres. Stickstoff-Unterversorgung in dieser Phase reduziert nachweislich die Bluetenanzahl im naechsten Fruehling.

Das Konzept der FLUSHING-Phase stammt aus der Cannabis-Kultivierung (Substrat-Reset vor dem Einlagern), ist auf perennie Kulturpflanzen nicht direkt uebertragbar und ist fuer Erdbeeren in dieser Form kontraproduktiv.

**Korrekturvorschlag:**
Die FLUSHING-Phase entweder:
- A) Vollstaendig entfernen und direkt von HARVEST (Woche 23--28) zu VEGETATIVE Herbst (Woche 29--40) uebergehen, mit reduzierter Terra-Grow-Duengung von Beginn an.
- B) Auf 1--2 Wochen kuerzen (statt 4 Wochen) und als "Substrat-Reset" nach intensiver Bluetephase positionieren, nicht als generelle Naehrstoffpause.
- C) Den Giess-Override in der FLUSHING-Phase korrigieren: Bei Hochsommertemperaturen ist ein 5-Tage-Intervall ohne Duengung nicht sicher. Das Override sollte hitzeabhaengig formuliert sein: "Bei Temperaturen > 28 Grad C taeglich giessen, bei Temperaturen < 22 Grad C alle 3--4 Tage."

---

### E-003: Calcium vollstaendig unmodelliert trotz Erdbeer-spezifischer Risiken

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, alle Phasen (calcium_ppm: null)

**Problem:**
Saemtliche 8 Phasen weisen `calcium_ppm: null` aus. Dies ist fuer Erdbeeren fachlich nicht akzeptabel:

**Calcium-Bedarf bei Erdbeeren:**
- Calcium (Ca) ist bei Erdbeeren einer der wichtigsten Naehrstoffe fuer Fruchtqualitaet.
- Ca-Mangel verursacht **Bluetenendenfaeule** (Blossom End Rot) -- der haeufigste Naehrstoffschaden bei Erdbeeren im Topf.
- Ca wird ausschliesslich ueber den Massenstrom mit dem Transpirationsstrom transportiert (Xylemsaft, kein Phloem-Transport). Trockenstress oder hohe Luftfeuchtigkeit bremsen die Ca-Aufnahme auch bei ausreichendem Ca im Substrat.
- Optimaler Ca-Gehalt in der Naehrloesung: **80--150 ppm** waehrend Bluete und Fruchtreife.

**Quellen fuer Ca in diesem Plan:**
- Terra Grow und Terra Bloom sind **1-Komponenten-Systeme ohne deklariertes Calcium** in den Referenzdokumenten. Die Produktdaten listen kein Ca unter den Naehrstoffen.
- Plagron Terra Bloom enthaelt **Magnesium (0,8%)** -- kein Calcium.
- Typische Gartenerde enthaelt Ca, aber in Topfkultur mit intensiver Bewaesserung wird Ca ausgewaschen.

**Konsequenz:** Erdbeerpflanzen im Topf ohne explizite Ca-Duengung zeigen nach 1--2 Jahren typischerweise Ca-Mangelsymptome, besonders bei heissem Wetter und hoher Verdunstung.

**Korrekturvorschlag:**
1. In den Phasen FLOWERING und HARVEST sollte ein **Calcium-Supplement** (z.B. Calciumnitrat Ca(NO3)2, 0,5--1 g/L) ergaenzt werden.
2. Alternativ: **Kalkung des Substrats** vor der Saison als Jahres-Calcium-Versorgung dokumentieren (gemahlener Kalk, 2--3 g/L Substrat).
3. Im Praxis-Hinweisteil ein Symptom-Abschnitt einfuegen: "Wenn braune, eingesunkene Flecken an der Fruchtspitze (der Bluetenseite) sichtbar werden, ist dies Bluetenendenfaeule (Ca-Mangel oder Transport-Ca-Mangel durch Trockenstress). Massnahme: Taeglich giessen, Calciumnitrat 0,5 g/L."
4. Das Datenbankfeld `calcium_ppm` sollte in FLOWERING und HARVEST mit **80--120 ppm** befuellt werden.

---

### E-004: Sugar Royal (9-0-0 organischer Stickstoff) in HARVEST-Phase bedenklich

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 4.5 (HARVEST, Zeile ~244)

**Problem:**
Sugar Royal weist laut Produktdokument **8,5% organisch gebundenen Stickstoff** (NPK-Kurzformel 9-0-0) auf. Das Produktdokument selbst empfiehlt: "Verwendung in der Spuelphase: Sugar Royal enthaelt 8,5% organischen Stickstoff und sollte in der Spuelphase abgesetzt werden."

Im Erdbeer-Plan wird Sugar Royal jedoch noch bis **1 Woche vor der letzten Ernte** eingesetzt. Fuer eine essfaehige Frucht gelten andere Anforderungen als fuer Cannabis:

1. **Aminosaeureextrakt-Reste in der Frucht:** Obwohl der Stickstoff organisch gebunden ist und die Aminosaeuren ueber den Pflanzenstoffwechsel umgesetzt werden, ist die Anwendung eines Aminosaeure-Supplements wenige Tage vor der Ernte einer Lebensmittelfrucht fachlich pruefenswert. Das Produkt ist nicht fuer den Lebensmittelanbau deklariert.

2. **Stickstoff-Uberschuss in der Fruchtreife:** Erhoehter verfuegbarer Stickstoff waehrend der Fruchtreife verzoegert die Reife, fuehrt zu groesseren aber geschmacklich schwaecher Fruechten und kann den Zuckergehalt reduzieren. Bei einer Erdbeere, bei der suesses Aroma das zentrale Qualitaetsmerkmal ist, ist das kontraproduktiv.

3. **Produktdokumentation:** Das Plagron-Produktdokument erklaert explizit, dass Sugar Royal "Trockenstress simuliert" und die Harzproduktion foerdert -- beides konzeptuell irrelevant fuer eine Lebensmittelerdbeere.

**Korrekturvorschlag:**
Sugar Royal sollte in der HARVEST-Phase vollstaendig abgesetzt werden. Der Plan sieht das fuer die FLUSHING-Phase vor, aber die Logik gilt bereits fuer HARVEST:
- In HARVEST-Phase: Sugar Royal komplett entfernen aus den fertilizer_dosages.
- Wenn ein Aminosaeure-Supplement zur Geschmacksfoerderung gewuenscht ist: Auf eine lebensmittelgerechte Alternative umsteigen (z.B. Algenkalkduenger, Huminsaeuren ohne deklariertes N-Aminosaeure-Profil).
- Den Hinweis "Sugar Royal absetzen 1 Woche vor letzter Ernte" auf "Sugar Royal nicht in der Erntephase verwenden" aendern.

---

### E-005: Terra Grow volle Dosis (4 ml/L) gegenueber Produktspezifikation korrekt, aber fuer Erdbeere grenzwertig

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 4.3 (VEGETATIVE, Zeile ~188)

**Problem:**
Das Terra Grow Produktdokument nennt fuer "Wachstum Woche 2--4" eine Dosierung von **5,0 ml/L** als volle Dosis (Maximaldosierung laut Produktdatenblatt). Der Plan verwendet 4 ml/L und bezeichnet dies als "volle Dosis" -- das ist eine Reduktion auf 80% der Produktmaximalempfehlung.

Die Produktreferenz zeigt fuer das offizielle Plagron 100% TERRA Grow Schedule:
- Woche 1: 2,5 ml/10L -> 0,25 ml/L (nicht 2,5 ml/L!)

Hier liegt ein **Skalierungsfehler** in der Dosierungslesart vor. Das Plagron-Schema gibt Dosierungen in ml pro 10 Liter an. Die Produkttabelle im Referenzdokument listet:
- Woche 1: 25 ml/10L = **2,5 ml/L**
- Woche 2-4: 50 ml/10L = **5,0 ml/L**

Der Plan verwendet 4 ml/L (80% der vollen Produktdosis), was fuer die salzempfindliche Erdbeere tatsaechlich sinnvoll ist. Das EC-Budget-Ergebnis von ~0,75 mS/cm ist plausibel und liegt innerhalb des empfohlenen Toleranzbereichs. Die Bezeichnung als "volle Dosis" ist jedoch irrefuehrend -- es ist eine reduzierte Dosis.

Fuer einmaltragende Erdbeeren im Topf empfehlen spezialisierte Erdbeer-Duengungsrichtlinien (z.B. Gartenakademie Rheinland-Pfalz, RHS Strawberry Growing Guide) folgende Stickstoff-Werte:
- Vegetative Phase: **0,8--1,2 g N/Pflanze/Woche** im Topf
- Bei 5L-Topf und 4 ml/L Terra Grow (2,6% N Gesamt): ~0,1 g N/L x 1L/Giessvorgang x 2-3 Giessungen/Woche = **0,2--0,3 g N/Woche** -- das ist innerhalb des Toleranzbereichs, eher im unteren Drittel.

**Korrekturvorschlag:**
1. Die 4 ml/L als "reduzierte Dosis (80% von Plagron-Empfehlung, erdbeeroptimiert)" bezeichnen statt "volle Dosis".
2. Einen Hinweis ergaenzen: "Terra Grow wird bewusst auf 4 ml/L begrenzt (statt Produkt-Maximum 5 ml/L), da Erdbeeren salzempfindlich sind (kritische EC: 1,5 mS/cm). Nur bei erkennbarem N-Mangel (Gelbfaerbung aelterer Blaetter) auf max. 5 ml/L erhoehen."

---

### E-006: Bewasserungsintervall 3 Tage als Sommerbasis risikobehaftet

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 1.1 (Giessplan) und Hinweistext Zeile ~36

**Problem:**
Der Standard-Giesspplan sieht ein **3-Tage-Intervall** vor mit dem Hinweis "Bei Hitze (>30 Grad C) taeglich giessen". Fuer einen **5-Liter-Topf aus Kunststoff im Sommer auf Balkon/Terrasse mit direkter Sonneneinstrahlung** ist dieses Intervall in der Standardkonfiguration zu lang:

Empirische Messwerte aus der Balkonpflanzen-Praxis:
- 5L Kunststofftopf, Aussentemperatur 22--26 Grad C, halbschattig: Substrat trocknet in ~2--3 Tagen durch
- 5L Kunststofftopf, Aussentemperatur 28--35 Grad C, sonnig: Substrat trocknet in **< 24 Stunden** durch
- 5L Terracotta-Topf, 26 Grad C: noch schneller (Verdunstung ueber Topfwand)

Erdbeeren reagieren extrem empfindlich auf Trockenstress waehrend Bluetbildung und Fruchtentwicklung:
- Trockenstress im Bluetstadium fuehrt zu reduziertem Fruchtansatz und Fruchtfall
- Trockenstress waehrend Fruchtreife fuehrt zu kleinen, suessen aber wenigen Fruechten -- oder zu Fruchtfaeule bei anschliessender Ueberbewasserung (Wechselfeuchtigkeit)
- Die Hitzegrenze von 30 Grad C ist zu hoch: **ab 25 Grad C** sollten Erdbeeren im 5L-Topf taeglich gegossen werden

**Korrekturvorschlag:**
Den Standard-Giesspplan-Hinweis praezisieren:
- "3-Tage-Intervall gilt bei kuehleren Perioden (< 22 Grad C) und grosem Topf (>= 8L). Bei 5L-Topf im Hochsommer: Bei Temperaturen > 22 Grad C taeglich giessen. Die Fingerkuppe-Methode hat Vorrang vor dem Kalender: Ist die oberste Schicht (2 cm) trocken, giessen."
- Alternativ: Einen **sensorbasierten Bewasserungshinweis** als Primaermethode einfuehren und das Kalender-Intervall als Fallback-Orientierung.
- Das Standard-Intervall von 3 Tagen auf 2 Tage anpassen, mit Hinweis "bei kuehlem Wetter auf 3 Tage verlaengern".

---

### E-007: Grauschimmel (Botrytis cinerea) als kritisches Erdbeer-Risiko nicht erwaehnt

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 6 (Praxis-Hinweise)

**Problem:**
*Botrytis cinerea* (Grauschimmel) ist der **wichtigste Pathogen bei Erdbeerfruchten** -- sowohl im Freiland als auch im Topf. In mitteleuropaeischen Sommern mit Regenperioden ist Grauschimmel auf reifen und ueberreifen Erdbeerfruchten endemisch. Ein Nährstoffplan fuer Erdbeertopfpflanzen ohne Botrytis-Prävention ist unvollstaendig.

Relevante Fakten zu Botrytis bei Topferdbeeren:
- *Botrytis* sporuliert ab 65% relativer Luftfeuchtigkeit (rH) und gedeiht bei 15--25 Grad C
- Blueten sind besonders anfaellig (Infektionspforte), Fruechte mit Beschaedigungen noch mehr
- Befeuchtetes Blattwerk und Naechte mit hoher Luftfeuchtigkeit (typisch Mai--Juli in Mitteleuropa) foerdern die Ausbreitung
- Schwaechung durch Naehrstoff-Ungleichgewichte (zu viel N, zu wenig K/Ca) erhoehen die Anfaelligkeit

Praevention, die im Plan haette erwaehnt werden sollen:
- **Luft-Zirkulation:** Topf nicht dicht an Waende stellen
- **Ernte-Frequenz:** Reife Fruechte taeglich kontrollieren und ernten (Botrytis-Praevention durch Entfernen ueberreifer Fruechte)
- **Blattdichte reduzieren:** Alte, absterbende Blaetter entfernen (sind Botrytis-Reservoire)
- **Bewaesserung:** Morgens giessen (Blattwerk trocknet bis zum Abend); Naesse auf Blueten und Fruechten vermeiden

**Korrekturvorschlag:**
In Abschnitt 6 (Praxis-Hinweise) einen neuen Unterabschnitt "Grauschimmel-Praevention" einfuegen:
```
Grauschimmel-Praevention (Botrytis cinerea):
- Wichtigster Erdbeer-Pathogen, besonders bei feuchter Witterung
- Vorbeugemassnahmen: taeglich reife Fruechte ernten, absterbende Blaetter sofort entfernen,
  morgens giessen (nicht abends), Topf nicht in Windschatten stellen
- Bei sichtbarem Grauschimmel: befallene Pflanzenteile sofort entfernen und in Muell (nicht Kompost)
- Keine chemischen Fungizide auf essenden Fruechten; Backpulver-Loesung (1 TL/L Wasser) kann
  als vorbeugende Blattspritzmittel auf Blueten und unreifen Fruechten eingesetzt werden
```

---

### E-008: Bestaeubungshinweise fuer Balkon-/Terrassenkultur fehlen

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 6 (Praxis-Hinweise)

**Problem:**
Erdbeerblueten sind selbst-fertile (selbstbestaeubend), benoetigen aber fuer optimale Fruchtbildung physikalische Pollenbewegung -- sei es durch Wind oder durch Insekten. Bei Topfpflanzen auf Balkonen oder in Innenhoefen kann die Bestaeubung eingeschraenkt sein:

- Windstille Lage (umbaut), hohe Etage (wenig Wildbienen)
- Fruehe Bluetephase (Mai/Juni): Bestaeubungsinsekten noch selten
- Einzelne Pflanze: kein Fremdpollen-Boost moeglich

Symptome mangelhafter Bestaeubung: kleinfoermige, deformierte Fruechte ("Knoepfchen") oder ausbleibender Fruchtansatz trotz Blueten.

**Korrekturvorschlag:**
Kurzhinweis in Abschnitt 6 ergaenzen: "Bestaeubung: Erdbeerblueten sind selbstfertil, aber physikalische Pollenbewegung verbessert Fruchtansatz. Bei windstiller Lage oder fehlendem Insektenbesuch: Blueten leicht mit Finger oder Pinsel beruehren, um Pollen zu verteilen (Handbestaeubung)."

---

### E-009: Leitungswasser-EC-Bandbreite unterschaetzt

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 4 (EC-Budget, Zeile ~108)

**Problem:**
Der Plan gibt an: "Leitungswasser liefert typisch 0,3--0,5 mS/cm, daher max. ~0,5 mS/cm EC-Beitrag durch Duenger."

Die Leitungswasser-EC in deutschen Staedte und Regionen variiert erheblich:
- Weiche Regionen (Bayern Alpenvorland, Schwarzwald): 0,2--0,4 mS/cm
- Mittlere Regionen: 0,3--0,6 mS/cm
- Hartwasserregionen (Muenchen Innenstadt, Rhein-Ruhr-Gebiet): **0,6--1,0 mS/cm**
- Extremwerte: bis 1,2 mS/cm in kalkharten Regionen

In einem Hartwasser-Haushalt mit Leitungswasser-EC von 0,8 mS/cm und Terra Grow 4 ml/L (EC-Beitrag ~0,32 mS/cm) ergibt sich eine Gesamt-EC von ~1,12 mS/cm -- noch innerhalb des Toleranzbereichs. Mit Power Roots (0,01) + Sugar Royal (0,02) und der gesamten VEGETATIVE-Loesung landet man bei ~1,15 mS/cm.

Das ist zwar noch tolerierbar, aber der Plan koennte in Hartwasserregionen unerwartete Naehrstoffblockaden durch Kalk-Phosphat-Faellung verursachen.

**Korrekturvorschlag:**
Den Bandbreitenhinweis erweitern: "Leitungswasser-EC variiert regional stark: 0,2--1,0+ mS/cm. In Hartwasser-Regionen (EC > 0,6 mS/cm) Terra-Grow-Dosis auf 3 ml/L reduzieren oder 50% Regenwasser / Osmosewasser beimischen. Bei EC-Wert des Leitungswassers unbekannt: Wasserversorger anfragen oder EC-Messgeraet verwenden."

---

### E-010: Chlor-Empfindlichkeit und Leitungswasserbehandlung nicht erwaehnt

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, allgemein

**Problem:**
Erdbeeren und das verwendete Enzym-Supplement Pure Zym zeigen eine Empfindlichkeit gegenueber freiem Chlor im Leitungswasser:

- Das Pure Zym Produktdokument empfiehlt explizit: "Stark chlorhaltiges Wasser kann Enzyme inaktivieren. Bei chloriertem Leitungswasser empfiehlt sich 24h Abstehen lassen."
- Erdbeerwurzeln sind vergleichsweise chlorempfindlich; bei hoeheren Chlorgehalten (> 0,5 mg/L Cl2) koennen Wurzelspitzen und Feinwurzeln geschaedigt werden.
- In deutschen Leitungsnetzen liegt der Chlorgehalt zwischen 0,1 und 0,3 mg/L (erlaubter Grenzwert nach TrinkwV: 0,6 mg/L), in Extremfaellen nach Leitungssanierungen kurzzeitig hoeher.

**Korrekturvorschlag:**
Einen Satz in Abschnitt 6 ergaenzen: "Leitungswasser idealerweise 12--24 Stunden in offenem Behaelter abstehen lassen, bevor Pure Zym zugefuegt wird (Chlor verdunstet, Enzymaktivitaet bleibt erhalten). Alternativ: Wasser vom Morgen fuer die Abend-Duengung vorbereiten."

---

### E-011: Einmaltragende Sorten sind Kurztagspflanzen -- Phasen-Mapping erwaehnt das nicht explizit

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 2 (Phasen-Mapping)

**Problem:**
Einmaltragende Erdbeersorten (*Fragaria x ananassa*, Gruppen: Kurztagssorten und indifferente Sorten) induzieren Bluetenknospen im **Herbst unter kurzen Taglaengen** (Kurztagsreaktion, typisch < 12--14 Stunden Licht, je nach Sorte und Temperatur). Die Blueteninitiierung geschieht im August--Oktober, die eigentliche Bluetenentwicklung erfolgt dann im naechsten Fruehling nach der Vernalisation.

Der Plan erwaehnt Vernalisation korrekt (Abschnitt 6, Kaeltebedurfnis), aber die **Kurztagsreaktion** und deren Bedeutung fuer die Herbst-Regenerations-Phase wird nicht explizit adressiert:

- Bei Topfpflanzen unter Dachueberstand oder in hellem Innenhof koennte kuenstliche Beleuchtung die Kurztagreaktion hemmen.
- Das ist in der Praxis selten ein Problem fuer Outdoor-Topfpflanzen, sollte aber kurz erwaehnt werden.
- Wichtiger: Die VEGETATIVE Herbst-Phase (Woche 33--40, September/Oktober) ist aus phytohormonaler Sicht nicht nur "Kronenbildung", sondern aktive **Blueteninitiierungsphase**. Adaequate K-Versorgung (aus Terra Grow, NPK 3-1-3) unterstuetzt die Kronenbildung, aber die Bedeutung dieser Phase fuer den Fruchtertrag des Folgejahres sollte hervorgehoben werden.

**Korrekturvorschlag:**
Im Phasen-Mapping-Abschnitt fuer VEGETATIVE (Herbst, Sequenz 7) einen Hinweis ergaenzen: "Einmaltragende Erdbeeren sind Kurztagspflanzen: In den kuerzer werdenden Tagen (September--Oktober) wird die Bluetenanlage fuer die naechste Saison gebildet. Ausreichende Naehrstoffversorgung (v.a. K aus Terra Grow) in dieser Phase ist direkt ausschlaggebend fuer den Fruchtertrag des naechsten Fruehlings."

---

### E-012: SEEDLING-Bezeichnung fuer Topfpflanze aus Gaertnerei unpassend

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 2 (Phasen-Mapping), Zeile ~47

**Problem:**
Die SEEDLING-Phase (Wochen 4--8, April) wird beschrieben als "Jungpflanze baut Blattrosette und Wurzelsystem auf". Der Hinweis in Abschnitt 1 (Metadata) beschreibt jedoch den Anwendungsfall als "Topfpflanze aus Gaertnerei einpflanzen" -- also ein Einkauf einer bereits etablierten Pflanze (typischerweise 6--12 Wochen alte Jungpflanze aus dem Gartenmarkt im Fruehling).

Eine im Gartencenter gekaufte Erdbeerpflanze ist kein Saemlling. Sie hat bereits ein vollstaendiges Wurzelsystem, 4--8 echte Blaetter und in manchen Faellen bereits erste Bluetenknospen. Die Duengungsstrategie einer Jungpflanze (halbe Dosis Terra Grow, Power Roots als Bewurzelungsstimulator) ist technisch korrekt fuer die Eingewoehnungsphase, aber die semantische Bezeichnung als SEEDLING ist irrefuehrend.

**Korrekturvorschlag:**
In den Hinweistext der Phase (notes) einfuegen: "Diese Phase gilt fuer Gartencenter-Jungpflanzen (nicht fuer Saemling). Zur Unterscheidung: Der Plan startet mit Phase GERMINATION (Topfens/Einpflanzen) und SEEDLING (Eingewoehnung), auch wenn die Pflanze bereits eine etablierte Jungpflanze ist. Die Bezeichnungen entsprechen dem REQ-003 Enum und sind funktional, nicht botanisch zu verstehen." Alternativ koennte der Plan-Name fuer SEEDLING auf "Eingewoehnung" umgestellt werden, sofern das Datenmodell freie Labeling-Felder erlaubt.

---

### E-013: Jahres-Giessplan Maerz -- Power Roots statt Halbdosis in Monatstabelle

**Schweregrad:** Gering (Konsistenzfehler)

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 5 (Jahresplan, Zeile ~332)

**Problem:**
Die Jahresplan-Tabelle (Abschnitt 5) zeigt fuer **Maerz** (etablierte Pflanze, Sequenz VEGETATIVE ab Jahr 2) folgendes: Terra Grow 2,5 ml/L, Power Roots 1,0 ml/L -- beides zusammen laeuft unter "VEGETATIVE". Der cycle_restart_from_sequence ist auf Sequenz 3 (VEGETATIVE Fruehjahr) gesetzt.

Ab Jahr 2 gibt es jedoch keine SEEDLING-Phase (kein "Einpflanzen" mehr). Der Jahresplan zeigt Maerz korrekt mit halbierter Terra-Grow-Dosis und Power-Roots als Anlaufdosierung. Das ist plausibel -- Terra Grow wird im Maerz niedrig gestartet weil das Wachstum noch verhalten ist, Power Roots unterstuetzt das Aufwachen der Wurzeln nach der Winterruhe.

Jedoch: Das Maerz-Profil entspricht **nicht** der definierten VEGETATIVE-Phase (Sequenz 3, 4,0 ml/L Terra Grow, kein besonderes Override). Das Maerz-Profil stammt aus dem SEEDLING-Override, der fuer ab Jahr 2 nicht mehr gilt. Es fehlt ein explizites Jahresstart-Override fuer die VEGETATIVE-Phase im ersten Monat (Maerz): "Start mit halbierter Dosis in den ersten 2--3 Wochen des Fruehlings".

**Korrekturvorschlag:**
Eine Klarstellung in der VEGETATIVE-Phase-Beschreibung ergaenzen: "Ab Jahr 2: Im Maerz mit halber Terra-Grow-Dosis (2,5 ml/L) beginnen und in den ersten 2--3 Wochen auf volle 4,0 ml/L steigern. Power Roots die ersten 4 Wochen des Fruehjahrs einsetzen (Wurzelaktivierung nach Winterruhe)."

---

### E-014: Magnesium-Bedarf in Herbst-Regeneration nicht adressiert

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/erdbeere_einmaltragend_plagron_terra.md`, Abschnitt 4.7 (VEGETATIVE Herbst)

**Problem:**
Terra Grow (NPK 3-1-3) enthaelt **kein Magnesium**. Terra Bloom enthaelt Magnesium (0,8%), wird aber in der Herbst-Regenerationsphase nicht verwendet. Die Herbst-VEGETATIVE-Phase (September--Oktober) sieht ausschliesslich Terra Grow + Pure Zym vor.

Fuer einmaltragende Erdbeeren ist Magnesium in der Herbstphase relevant:
- Mg ist zentrales Element des Chlorophylls; Mg-Mangel zeigt sich als intervenoese Chlorose ("gelb zwischen gruenen Blattnerven") an aelteren Blaettern -- ein haeufiges Symptom bei Topferdbeeren im Spaetsommer/Herbst.
- Durch intensive Bewaesserung im Sommer wird Mg aus dem Substrat ausgewaschen.
- Terra Bloom wird nach der HARVEST-Phase abgesetzt, womit die Mg-Quelle entfaellt.

**Korrekturvorschlag:**
In der Herbst-VEGETATIVE-Phase eine Mg-Ergaenzung optional erwaehnen: "Wenn intervenoese Chlorose (gelb zwischen Blattnerven) an aelteren Blaettern sichtbar wird: Bittersalz (Magnesiumsulfat MgSO4) als Blattspritzung 1--2 g/L Wasser, einmalig. Alternativ: In den ersten 2 Wochen der Herbst-Phase noch 2 ml/L Terra Bloom beibehalten (enthaelt 0,8% Mg)."

---

## Zusammenfassende Bewertungstabelle

| Finding | Titel | Schweregrad | Status |
|---------|-------|-------------|--------|
| E-001 | PK 13-14 Dosierung inkompatibel mit Erdbeer-EC-Toleranz | Kritisch | Muss korrigiert werden |
| E-002 | FLUSHING im August agronomisch fragwuerdig | Wichtig | Sollte korrigiert werden |
| E-003 | Calcium vollstaendig unmodelliert | Wichtig | Sollte ergaenzt werden |
| E-004 | Sugar Royal (9-0-0) in HARVEST-Phase bedenklich | Wichtig | Sollte korrigiert werden |
| E-005 | Terra Grow 4 ml/L als "volle Dosis" irrefuehrend | Hinweis | Kann korrigiert werden |
| E-006 | Bewasserungsintervall 3 Tage als Sommerbasis zu lang | Wichtig | Sollte praezisiert werden |
| E-007 | Botrytis cinerea als Erdbeer-Hauptrisiko fehlt | Wichtig | Sollte ergaenzt werden |
| E-008 | Bestaeubungshinweise fehlen | Hinweis | Kann ergaenzt werden |
| E-009 | Leitungswasser-EC-Bandbreite unterschaetzt | Hinweis | Kann praezisiert werden |
| E-010 | Chlor-Empfindlichkeit nicht erwaehnt | Hinweis | Kann ergaenzt werden |
| E-011 | Kurztagsreaktion und Blueteninitiierungsphase nicht explizit | Hinweis | Kann ergaenzt werden |
| E-012 | SEEDLING-Bezeichnung fuer Gartencenter-Pflanze semantisch unpassend | Hinweis | Kann erlaeutert werden |
| E-013 | Maerz-Jahresplan inkonsistent mit cycle_restart_from_sequence | Gering | Kann praezisiert werden |
| E-014 | Magnesium in Herbst-Regenerationsphase fehlt | Hinweis | Kann ergaenzt werden |

---

## Positiv bewertete Aspekte

Die folgenden Elemente des Plans sind fachlich korrekt und verdienen explizite Erwaehnung:

**Vernalisation korrekt beschrieben:** Die Anforderung an eine Kaelteperiode (< 7 Grad C fuer 4--6 Wochen) fuer die Blueteninitiierung naechstes Jahr ist exakt und wichtig -- ein Aspekt, den viele Hobby-Gaertner nicht kennen. Die Empfehlung, die Topfpflanze nicht den ganzen Winter im warmen Haus zu halten, ist richtig.

**Boron-Hinweis bei Bluetenduengung:** Die Erwaehnung des hohen Boranteils (0,48%) in Terra Bloom und dessen Relevanz fuer Pollenkeimung und Fruchtansatz ist biologisch korrekt. Bor ist bei Erdbeeren tatsaechlich oft ein limitierender Faktor fuer den Fruchtansatz -- weniger bekannt, aber wichtig.

**Auslaeufer-Management differenziert:** Die Unterscheidung zwischen "Auslaufer abschneiden fuer Fruchtoptimierung" (Hauptsaison) und "Auslaufer zur Vermehrung nutzen" (Herbst) ist agronomisch richtig und vollstaendig.

**EC-Budget konservativ und erdbeergerecht:** Die Ziel-EC-Werte von 0,5--0,9 mS/cm sind fuer eine salzempfindliche Kulturpflanze wie Erdbeere korrekt dimensioniert. Besonders gut: Die Herabsetzung des Ziel-EC in der HARVEST-Phase auf 0,7 mS/cm.

**Frostschutz-Anleitung praxisnah:** Die Empfehlung zur Isolierung des Topfs (Vlies, Luftpolsterfolie, Styropor) und die Erklaerung, dass ein Topf schneller durchfriert als Freilandboden, sind korrekt und fuer Balkongartenbesitzer wichtig.

**Substrat-Empfehlungen korrekt:** pH 5,5--6,5, min. 3L Topf, Drainage-Loecher, Vermischung mit Sand/Perlite -- alles fachlich richtig.

**Plagron 100% TERRA Grow Schedule Kompatibilitaet:** Die Einbindung der Plagron-Produktlinie ist konsistent. Die Mischungsreihenfolge und Mixing Priorities sind korrekt aus den Produktdokumenten uebernommen.

**Jahresverbrauch korrekt berechnet:** Die Formel-Berechnung in Abschnitt 5 ist mathematisch korrekt und gut transparent. Die Kostenabschaetzung ("10 Erdbeerpflanzen-Jahre aus 1L-Flaschen") ist realistisch.

---

## Empfehlung: Dringlichkeit der Korrekturen

**Vor dem Produktivbetrieb zu korrigieren (Blocker):**
1. **E-001:** PK 13-14 aus dem Plan entfernen oder auf < 0,3 ml/L begrenzen mit explizitem Warnhinweis.
2. **E-003:** Calcium-Versorgung in FLOWERING und HARVEST ergaenzen (mindestens als Praxis-Hinweis).
3. **E-007:** Botrytis-Praeventionshinweise einfuegen (Lebensmittelsicherheits- und Ertragsfragen).

**In Version 1.1 zu ergaenzen (Should-Have):**
4. **E-002:** FLUSHING-Phase ueberarbeiten (kuerzen oder entfernen).
5. **E-004:** Sugar Royal aus HARVEST-Phase entfernen.
6. **E-006:** Bewasserungsintervall fuer Hochsommer praezisieren.

**Spaetere Version (Nice-to-Have):**
7--14: Alle Hinweis-Findings.

---

## Glossar (Erdbeer-spezifisch)

- **Einmaltragende Sorten (Kurztagssorten):** Erdbeer-Kultivare, die nur einmal pro Saison (Fruehjahr/Fruehsommer) Fruechte tragen. Gegensatz: remontante Sorten (mehrmaltragend, tagneutral).
- **Vernalisation:** Biologisch notwendige Kaelteperiode (mehrere Wochen unter ~ 7 Grad C) fuer die Ausloesung der Bluetenentwicklung im naechsten Fruehling. Bei Erdbeeren 4--8 Wochen.
- **Kurztagsreaktion:** Physiologischer Prozess, durch den einmaltragende Erdbeersorten bei Taglaengen < 12--14 Stunden (Herbst) Bluetenknospen anlegen.
- **Bluetenendenfaeule (Blossom End Rot):** Calcium-Transportmangel in der sich entwickelnden Frucht, sichtbar als braune, eingesunkene Stellen an der Fruchtspitze. Praeventiv durch regelmaessige Bewaesserung und Ca-Duengung.
- **Botrytis cinerea:** Grauschimmelpilz, wichtigstes Erdbeer-Pathogen. Befall zeigt sich als grauer Rasen auf reifen und ueberreifen Fruechten. Praeventiv durch Luftzirkulation und taegliches Ernten.
- **Kronenbildung:** Im Herbst bildet die Erdbeerpflanze neue, kurze Staemlinge (Kronen), aus denen im naechsten Jahr Bluetentriebe entstehen. Dieser Prozess benoetigt Naehrstoffe (v.a. K) und muss durch adaequate Herbst-Duengung unterstuetzt werden.
