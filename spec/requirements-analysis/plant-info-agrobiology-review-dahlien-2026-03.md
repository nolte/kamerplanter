# Agrarbiologisches Review: Pflanzen-Informationsdokumente — Dahlien, Tigridia, Petunia
**Erstellt von:** Agrarbiologie-Experte
**Datum:** 2026-03-04
**Fokus:** Botanische Korrektheit, Phasenmodellierung, Duengungsempfehlungen, IPM-Daten, Mischkultur, Ueberwinterungsprofile, CSV-Import-Eignung
**Analysierte Dokumente:**
1. `spec/ref/plant-info/dahlia_hapet_daydream.md` — Dahlie 'Hapet Daydream'
2. `spec/ref/plant-info/dahlia_pinnata_great_silence.md` — Dahlie 'Great Silence'
3. `spec/ref/plant-info/dahlia_x_hybrida_lavender_perfection.md` — Dahlie 'Lavender Perfection'
4. `spec/ref/plant-info/dahlia_x_hybrida_armateras.md` — Dahlie 'Armateras'
5. `spec/ref/plant-info/dahlia_embassy.md` — Dahlie 'Embassy'
6. `spec/ref/plant-info/tigridia_pavonia.md` — Pfauenblume / Tigerblume
7. `spec/ref/plant-info/petunia_x_hybrida.md` — Garten-Petunie

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Ueberwiegend korrekt; 3 kritische und 9 wesentliche Einzelfehler |
| Taxonomische Praezision | 3/5 | Inkonsistente Nomenklatur zwischen den Dahlien-Dokumenten ist das groesste strukturelle Problem |
| Phasenparameter-Plausibilitaet | 4/5 | PPFD/DLI/VPD-Werte gut kalibriert; Luecken in Dormanz-Phasen |
| Duengungsempfehlungen | 4/5 | NPK-Verhaeltnisse und Grundprinzipien korrekt; EC-Angaben fuer Freiland z.T. unklar anwendbar |
| IPM-Vollstaendigkeit | 4/5 | Solide Abdeckung; Bodenstruktursschaedlinge (Drahtwurm) nicht bei allen Dahlien erwaehnt |
| Mischkultur-Konsistenz | 3/5 | Cross-Dokument-Asymmetrien; Tagetes-Dahlie-Beziehung nur einseitig dokumentiert |
| Ueberwinterungsprofile | 4/5 | Knollenzyklus gut modelliert; Tigridia-Lagertemperatur weicht von Dahlie ab (korrekt) |
| KA-Import-Eignung (REQ-012) | 3/5 | CSV-Zeilen konsistent aber mit kritischem Nomenklatur-Konflikt zwischen Dokumenten |

**Gesamteinschaetzung:** Die 7 Pflanzendokumente zeigen eine solide fachliche Grundlage mit guten Detailangaben zu Knollenkultur, Ueberwinterung und Duengung. Das groesste strukturelle Problem ist die inkonsistente Taxonomie der Dahlien: Drei Dokumente verwenden verschiedene wissenschaftliche Namen fuer denselben Elternarten-Komplex (Dahlia pinnata, Dahlia x hybrida, Dahlia x pinnata). Dies fuehrt zu Importkonflikten in der Kamerplanter-Datenbank. Die Photoperiodismus-Beschreibung bei Dahlien ist korrekt, erfordert aber eine Praezisierung zur Tuberisierungssteuerung. Tigridia pavonia ist exzellent dokumentiert. Petunia x hybrida ist vollstaendig und praxistauglich.

---

## Kritische Fehler — Sofortiger Korrekturbedarf

### K-001: Inkonsistente Taxonomie der Dahlien — fuehrt zu Datenbankkonflikt

**Betroffene Dokumente:**
- `dahlia_hapet_daydream.md`: Wissenschaftlicher Name `Dahlia pinnata` (CSV-Zeile, Sektion 8.1)
- `dahlia_pinnata_great_silence.md`: Elternart `Dahlia × pinnata Cav.` (Sektion 1.1)
- `dahlia_x_hybrida_lavender_perfection.md`: Wissenschaftlicher Name `Dahlia x hybrida` (Sektion 1.1)
- `dahlia_x_hybrida_armateras.md`: Wissenschaftlicher Name `Dahlia pinnata`, Synonyme `Dahlia x hybrida` (Sektion 1.1)
- `dahlia_embassy.md`: Wissenschaftlicher Name `Dahlia pinnata (Hybride)` (Sektion 1.1)

**Problem:** Fuenf Dokumente verwenden drei unterschiedliche wissenschaftliche Namen fuer dieselbe Elternart: `Dahlia pinnata`, `Dahlia × pinnata` und `Dahlia x hybrida`. Damit werden beim CSV-Import je nach Normalisierungslogik zwischen 2 und 3 separate Species-Eintraege angelegt, obwohl alle denselben Genotyp referenzieren. Dies zerstoert die Cultivar-Elternbeziehungen im ArangoDB-Graphen.

**Fachliche Einordnung:** Der aktuelle botanische Konsens (nach APG IV, POWO, World Flora Online) behandelt die Gartendahlie als Kultivarkomplex mit *Dahlia pinnata* Cav. als Typusart. Der Name *Dahlia × hybrida* ist eine Handesbezeichnung ohne formalen Nomenklaturstatus. *Dahlia × pinnata* ist eine Hybridnothoart-Schreibweise, die in einigen Gartenbauquellen vorkommt, aber nicht dem korrekten Nomenklaturstandard entspricht — das Zeichen `×` kennzeichnet nur Hybridursprung, nicht eine eigene Art. Fuer Gartendahlien-Sorten gilt: Elternart = *Dahlia pinnata*, Sorte = Cultivar-Name.

**Korrekte Formulierung (einheitlich fuer alle 5 Dokumente):**
```
Wissenschaftlicher Name (Elternart): Dahlia pinnata Cav.
Sortenname (Cultivar): [Sortenname]
Synonyme: Dahlia variabilis Willd. (veraltet), Dahlia x hybrida (Handelsbezeichnung)
```

**CSV-Einheitlichkeit:** Alle fuenf CSV-Zeilen muessen denselben `scientific_name: Dahlia pinnata` verwenden, da sonst beim Import 3 konkurrierende Species-Eintraege entstehen.

**Auswirkung:** Importkonflikt REQ-012; fehlerhafte Graphstruktur in ArangoDB; Cultivar-zu-Species-Kanten werden auf verschiedene Knoten verteilt.

---

### K-002: Tuberisierungssteuerung bei Dahlien — Photoperiodismus unvollstaendig beschrieben

**Betroffene Dokumente:** Alle fuenf Dahlia-Dokumente (Sektion 1.1, Photoperiode)

**Problem:** Alle fuenf Dokumente beschreiben Dahlien korrekt als Kurztagspflanzen fuer die Blueteninitiierung. Es fehlt jedoch der entscheidende zweite Aspekt: Die Knollenbildung (Tuberisierung) wird EBENFALLS durch Kurztag gefoerdert, laeuft aber physiologisch unabhaengig von der Blueteninitiierung. Wichtiger noch: Dahlien koennen auch unter Langtag bluehen, wenn die Temperatur stimmt — der Kurztagseffekt ist bei Dahlien schwaecher ausgepragt als bei klassischen Kurztagspflanzen wie Chrysanthemen oder Schlumbergera. Praeziser: Dahlien sind fakultative Kurztagspflanzen mit Thermoperiodizitatswirkung.

Die Beschreibung in `dahlia_hapet_daydream.md` (Sektion 1.1): "Dahlien sind Kurztagspflanzen — Blühinduktion durch Nächte > 10–11 h" ist korrekt fuer die Tuberisierung, aber fuer die Bluetenbildung genuegen 12 h Nacht (entspricht 12 h Tageslicht) als Schwellenwert, nicht erst > 10–11 h Nacht (= weniger als 13–14 h Tageslicht). Die Zahlen sind in einigen Dokumenten uneinheitlich (10-11 h Nacht vs. < 14 h Tageslicht).

**Korrekte Formulierung:**
```
Photoperiode: short_day (fakultativ)
Blueteninitiierung: Nachtlaenge > 12 h (= Taglaenge < 12 h) foerdert Bluetenbildung;
Dahlien bluehen jedoch auch unter Langtagbedingungen wenn geniigend gross;
Tuberisierung (Knollenaufbau): eindeutig kurztaggesteuert (Nacht > 12 h)
Schwellenwert fuer Blueteninitiierung: Nachtlaenge ca. 12 h (nicht 10–11 h wie teilweise angegeben)
```

**Auswirkung auf Phasenmodell (REQ-003):** Photoperiodismus-gesteuerte Phasenubergaenge muessen den korrekten Schwellenwert (12 h Nacht) verwenden; die angegebenen 10–11 h Nacht wuerden den Zeitpunkt um 1–3 Wochen verschieben.

---

### K-003: Tigridia pavonia — Wurzeltyp 'bulbous' fachlich unkorrekt

**Dokument:** `tigridia_pavonia.md`, Sektion 1.1, Zeile 21

**Problem:** Der Wurzeltyp ist als `bulbous` (Zwiebelpflanze) angegeben. Tigridia pavonia bildet jedoch keine echte Zwiebel (Tunica-Zwiebel mit Zwiebelschalen wie Tulpe oder Narzisse), sondern eine **Korm** (Corm = solides Speicherorgan ohne Schichten). Korrekter Wurzeltyp ist `corm`. Der Text selbst erwaehnt dies korrekt in der Notiz nach der Tabelle ("Es handelt sich botanisch korrekt um eine Knolle (Corm), nicht um eine echte Zwiebel"), aber der Feldwert `bulbous` widerspricht dieser eigenen Beschreibung direkt.

Die Unterscheidung ist fuer das Kamerplanter-Datenbankschema relevant: Wenn das System zwischen `bulbous`, `corm`, `tuberous` und `rhizome` unterscheidet, muss Tigridia korrekt als `corm` erfasst werden, um korrekte Pflegeempfehlungen (Lagerungstiefe, Ausgrabeverfahren, Reproduktionsmodus) zu generieren.

**Korrekte Formulierung:**
```
Wurzeltyp: corm (Korm — solides Speicherorgan; keine echte Zwiebel mit Schalen;
bildet jaehrlich Tochterkormen an der Basis)
```

**Auswirkung:** Falsches enum-value fuehrt zu falschen Pflegeempfehlungen bei Filterung nach Wurzeltyp; Knollen-Zyklus-Modell (REQ-022) muss den Corm-Zyklus korrekt abbilden.

---

## Wesentliche Maengel — Korrekturbedarf vor Produktionseinsatz

### M-001: Dahlie 'Hapet Daydream' — Sortenname in CSV-Zeile weicht vom Dokument ab

**Dokument:** `dahlia_hapet_daydream.md`, Sektion 8.1

**Problem:** Das Dokument bezeichnet die Art im Titel als "Dahlia 'Hapet Daydream'" (ohne Elternart), in Sektion 1.1 als Cultivar von Dahlia pinnata. Die CSV-Zeile in 8.1 traegt jedoch `scientific_name: Dahlia pinnata` — korrekt fuer die Elternart — und fuehrt den Cultivar-Namen in der Cultivar-CSV-Zeile (8.2). Das ist strukturell korrekt.

Jedoch: Der Bluetentyp wird im Dokument als "Dekorative Dahlie mit Tendenz zum Pompon/Ball-Typ" beschrieben, aber die Cultivar-CSV-Zeile traegt gleichzeitig `ball_type` und `decorative_type` als Traits. Das ADS (American Dahlia Society) klassifiziert eine Dahlie entweder als Ball (BA, BB), Pompon (P) oder Decorative (FD, ID) — die Klassen schliessen sich gegenseitig aus. 'Hapet Daydream' ist nach RHS-Angaben als Ball-Dahlie (BA: > 10 cm) eingestuft, nicht als Dekorative Dahlie.

**Korrekte Formulierung:**
```
Cultivar traits: ornamental;ball_type;bicolor;cutting_flower;heavy_feeder
(nicht: ball_type;decorative_type gleichzeitig)
ADS-Klasse: BA (Ball > 10 cm) oder BB (Ball 10–15 cm) — nach Quellenverifizierung
```

---

### M-002: Dahlie 'Great Silence' — Cultivar CSV-Zeile traegt falsche Werte fuer seed_type und photoperiod_type

**Dokument:** `dahlia_pinnata_great_silence.md`, Sektion 8.2

**Problem 1:** `seed_type: open_pollinated` ist fuer eine Cultivar-Dahlie wie 'Great Silence' fachlich unzutreffend. Sorten-Dahlien werden vegetativ (Knollenteilung, Stecklinge) vermehrt; 'open_pollinated' impliziert, dass der Saatgut samenfest und sortenecht reproduzierbar ist. Fuer vegetativ vermehrte Kultivar-Dahlien ist `seed_type: clone` korrekt (wie in `dahlia_hapet_daydream.md` richtig angegeben).

**Problem 2:** `photoperiod_type: day_neutral` in der Cultivar-CSV-Zeile ist fuer 'Great Silence' als Ueberschreibung des Elternart-Wertes inkonsistent. Die Elternart hat `short_day` — der Cultivar erbt diese Eigenschaft; ein Override zu `day_neutral` waere nur angebracht wenn 'Great Silence' sortenspezifisch tagneutral gezeuchtet wurde, was nicht dokumentiert ist. Der Eintrag sollte entweder fehlen (Elternart-Wert wird geerbt) oder mit `short_day` uebereinstimmen.

**Korrekte Formulierung:**
```csv
Great Silence,Dahlia pinnata,Peter Komen,2018,"informal_decorative;dark_blend;coral_pink;golden_center;long_stems;bee_friendly;cut_flower",90,,clone,
```
(seed_type = clone; photoperiod_type-Spalte leer lassen = Elternart-Wert erbt)

---

### M-003: Dahlie 'Lavender Perfection' — Substrat-pH-Empfehlung fuer Freiland zu hoch

**Dokument:** `dahlia_x_hybrida_lavender_perfection.md`, Sektion 1.6

**Problem:** Die Substrat-Empfehlung fuer den Topf gibt pH 6.0–7.0 an (korrekt), aber fuer das Freiland wird pH 6.5–7.5 empfohlen. Bei pH 7.5 treten bei Dahlien signifikante Mikronaehrstoffmangel auf — insbesondere Eisen (Fe) und Mangan (Mn) werden bei pH > 7.0 schwer verfuegbar. Dahlien sind kalkempfindlich; der Optimalbereich liegt bei pH 6.0–7.0 (nach American Dahlia Society), einige Quellen nennen 6.0–6.5 als ideal.

Eine Empfehlung bis pH 7.5 fuer das Freiland ist fuer Dahlien zu hoch und kann bei hartem Wasser und kalkhaltigem Boden zu chronischem Fe-Mangel und Chlorose fuehren.

**Korrekte Formulierung:**
```
Substrat-Empfehlung (Freiland): Lockerer, humusreicher, gut drainierter Boden;
pH 6.0–7.0 (Optimum 6.2–6.8). Bei pH > 7.0 treten Fe/Mn-Mangel auf.
Kalkhaltige Boeden mit Schwefel oder saurem Torf ansaeuern.
```

---

### M-004: Dahlie 'Armateras' — Nährstoffbedarf-Klassifizierung inkonsistent mit anderen Dahlien-Dokumenten

**Dokument:** `dahlia_x_hybrida_armateras.md`, Sektion 1.1 und 6.1

**Problem:** 'Armateras' wird als `medium_feeder` klassifiziert. Vier andere Dahlien-Dokumente klassifizieren vergleichbare Dahliengroessen als `heavy_feeder` (Hapet Daydream, Lavender Perfection, Embassy) oder begruenden `medium_feeder` nicht sortenspezifisch. Die Fruchtfolge-Einordnung in Sektion 6.1 bezeichnet den Naehrstoffbedarf ebenfalls als "Mittelzehrer (medium_feeder)", waehrend 'Great Silence' ebenfalls `medium_feeder` traegt.

Fachlich: Dahlien sind in der Praxis Starkzehrer, insbesondere waehrend der Bluete. Der American Dahlia Society-Duengungsguide bestaetigt hohen P- und K-Bedarf in der Bluetephase. Die `medium_feeder`-Klassifikation kann bei kleinbluetigen Sorten vertretbar sein, sollte aber wenn dann einheitlich fuer alle ahnlichen Sorten gelten. Groessenabhaengig: Kompakte Pom-Pom-Dahlien (< 8 cm Bluete) = medium_feeder; Dekorative und Ball-Dahlien (8–25 cm Bluete) = heavy_feeder.

Armateras mit 12–15 cm Bluetendurchmesser gehoert zur heavy_feeder-Gruppe.

**Korrekte Formulierung:**
```
nutrient_demand_level: heavy_feeder
Begruendung: Blütendurchmesser 12–15 cm, Wuchshöhe 90–110 cm,
kontinuierliche Schnittblumenproduktion erfordert intensive P/K-Versorgung
```

---

### M-005: Dahlie 'Embassy' — Züchter und Zuechtungsjahr fehlen ohne Quellenhinweis

**Dokument:** `dahlia_embassy.md`, Sektion 1.1.1

**Problem:** Die Felder `Züchter` und `Züchtungsjahr` enthalten `<!-- DATEN FEHLEN -->`. Das ist transparent, aber fuer den Datenbankimport unzureichend — es fehlt der Hinweis, ob diese Daten recherchiert und nicht gefunden wurden, oder noch nicht recherchiert wurden. Fuer einen Kamerplanter-Import wird empfohlen, nicht verfuegbare Daten mit `null` (statt offenem Platzhalter) zu kennzeichnen und einen Hinweis zu ergaenzen.

Zudem: Die Wuchshoehe von 'Embassy' wird mit 90–130 cm angegeben mit dem Hinweis "Quellen variieren". Der untere Wert stammt von ilovedahlia.com (90 cm), der obere von DutchGrown (127 cm / 50 Zoll). Dieser Wertebereich ist valide, sollte aber mit Quellenangabe dokumentiert sein.

**Korrektur:**
```csv
# Cultivar-CSV Embassy:
Embassy,Dahlia pinnata,null,null,"small_decorative;bicolor;purple_white;cut_flower",90,,clone
```

---

### M-006: Dahlien-Lagerungsfeuchte inkonsistent zwischen Dokumenten

**Betroffene Dokumente:**
- `dahlia_hapet_daydream.md`: Dormanz-Luftfeuchte 65–75 %
- `dahlia_pinnata_great_silence.md`: Dormanz-Luftfeuchte 80–90 %
- `dahlia_x_hybrida_lavender_perfection.md`: Dormanz-Luftfeuchte 70–90 %
- `dahlia_embassy.md`: Dormanz-Luftfeuchte 60–75 %

**Problem:** Die empfohlene Luftfeuchtigkeit fuer die Knollenlagerung variiert zwischen 60–75 % und 80–90 %, also um bis zu 30 Prozentpunkte. Fachlich: Zu niedrige Luftfeuchtigkeit (< 60–65 %) fuehrt zu Knollenaustrocknung und Schrumpeln; zu hohe Luftfeuchtigkeit (> 80–85 %) foerdert Botrytis-Faeulnis. Der praxisbewaehrte Bereich fuer Dahlienknollen liegt bei 60–75 % relativer Luftfeuchtigkeit (Longfield Gardens, American Dahlia Society, RHS). Der Wert 80–90 % in 'Great Silence' ist zu hoch und erhoht das Faeulnisrisiko.

**Einheitliche Empfehlung fuer alle Dahlia-Dokumente:**
```
Dormanz-Luftfeuchtigkeit: 60–75 % rH
(zu trocken < 60% = Knollen schrumpeln; zu feucht > 80% = Botrytis-Faulnis)
```

---

### M-007: Tigridia pavonia — Lagerungstemperatur korrekt aber begruendungsbeduerftig

**Dokument:** `tigridia_pavonia.md`, Sektion 4.3

**Problem (minor):** Die Lagerungstemperatur fuer Tigridia-Kormen (10–13 °C) ist korrekt und weicht bewusst von den Dahlia-Werten (4–10 °C) ab. Dies ist fachlich richtig: Tigridia stammt aus mexikanischen Hochlagen mit milderen Wintern als die Dahlia-Hochlagen und toleriert keine so kalten Lagertemperaturen. Bei < 8–10 °C werden Tigridia-Kormen geschaedigt.

Der Unterschied sollte im Dokument explizit begruendet werden, da Nutzer moeglicherweise annehmen, beide Knollentypen koennen gleich gelagert werden (was bei Dahlien mit 4–10 °C zu Tigridia-Schaeden fuehren wuerde, falls gemeinsam gelagert).

**Empfohlene Ergaenzung:**
```
Hinweis: Tigridia-Kormen NICHT gemeinsam mit Dahlienknollen bei 4–8 °C lagern.
Tigridia benoetigt 10–13 °C; tiefere Temperaturen schadigen die Kormen.
Idealer Lagerort: frostfreier Keller oder Schlafzimmer (15 °C kuehl, nicht kalt).
```

---

### M-008: Petunia x hybrida — Allelopathie-Score 0.2 ohne Quellenbeleg

**Dokument:** `petunia_x_hybrida.md`, Sektion 1.1

**Problem:** Der Allelopathie-Score von 0.2 ist der einzige nicht-neutrale Wert (alle anderen Dokumente haben 0.0) und ist ohne Quellenangabe. Petunien sind nicht als signifikant allelopathisch bekannt. Die klebrigen Trichome produzieren zwar Sekretion, aber keine belegten allelopathischen Verbindungen, die das Wachstum von Nachbarpflanzen hemmen. Ein Score von 0.2 impliziert eine geringe aber messbare allelopathische Wirkung — dieser sollte entweder belegt oder auf 0.0 zurueckgesetzt werden.

**Empfehlung:**
```
Allelopathie-Score: 0.0 (keine belegte allelopathische Wirkung)
ODER: 0.2 mit Quellenangabe (z.B. Studiennachweis zu Petunia-Allelopathie)
```

---

### M-009: Petunia x hybrida — Mischkultur-Empfehlung Tomate fachlich problematisch

**Dokument:** `petunia_x_hybrida.md`, Sektion 6.2

**Problem:** Petunia x hybrida und Tomate (Solanum lycopersicum) werden als gute Nachbarn mit Score 0.8 gelistet. Die Begruendung: "Petunien locken Bestäuber an; Bestäubungsförderung für Tomatenblüten." Dies ist fachlich korrekt fuer die Bestaeuberfoerderung.

Jedoch: Beide gehoeren zur Familie Solanaceae und teilen denselben Schaedlings- und Erregersatz (Myzus persicae, Frankliniella, Thripse, Fusarium, Pythium, TSWV). Die Sektion 6.4 ("Familien-Kompatibilitaet") benennt korrekterweise `rotation_conflict` und `shares_pest_risk` fuer Solanaceae-interne Kombinationen. Diese Information steht im Widerspruch zur positiven Bewertung von 0.8 in 6.2.

Fachlich korrekt waere: Petunien und Tomaten koennen als Begleitpflanzen kombiniert werden (Bestaeuberfoerderung ist real), aber der hohe Kompatibilitaets-Score von 0.8 uebersieht das geteilte Schadensrisiko. Empfehlenswert: Score 0.5–0.6 mit explizitem IPM-Hinweis.

**Korrekte Formulierung:**
```
| Tomate | Solanum lycopersicum | 0.5 | Bestäubungsförderung durch Petunia-Blüten (nachgewiesen);
ABER: geteilte Solanaceae-Schädlinge (Thripse, Myzus persicae, Pythium);
geteiltes TSWV-Übertragungsrisiko; nur empfehlen wenn gutes IPM-Management | `compatible_with` |
Hinweis: Score bewusst niedrig wegen geteiltem Krankheitsspektrum
```

---

## Geringfuegige Hinweise und Verbesserungsvorschlaege

### H-001: VPD-Wert fuer Dormanz-Phase fehlt in mehreren Dokumenten

**Betroffene Dokumente:** `dahlia_hapet_daydream.md` (Dormanz-Phase), `dahlia_x_hybrida_armateras.md` (Seneszenz-Phase), `dahlia_embassy.md` (Dormanz-Phase) — alle markiert mit `<!-- DATEN FEHLEN -->`

**Bewertung:** Der VPD-Wert (Vapor Pressure Deficit) fuer die Lagerungsphase ist in der Praxis nicht steuerbar und nicht relevant fuer eingelagerte Knollen ohne aktiven Gaswechsel. Die Platzhalter sind korrekt als "nicht anwendbar" zu behandeln. Empfehlung: Einheitlich `null` oder `"--"` verwenden statt `<!-- DATEN FEHLEN -->`, da letzteres einen Recherchebedarf impliziert der nicht besteht.

**Empfehlung:**
```
VPD-Ziel (Dormanz): null (nicht anwendbar — Knollen ohne aktiven Gaswechsel; kein Steuerungsparameter)
```

---

### H-002: Dahlie 'Embassy' — Naehrstoffbedarf heavy_feeder aber trait 'fragrant' unbelegt

**Dokument:** `dahlia_embassy.md`, Sektion 1.1

**Problem:** Das Trait `fragrant` wird in der Embassy-Beschreibung aufgelistet, ohne dass eine Quelle oder Begruendung angegeben wird. Nicht alle Dahlien-Sorten sind duftend. 'Embassy' ist eine Small Decorative-Sorte; solide Quellen fuer Duft bei dieser Sorte fehlen. Im Zweifel sollte `fragrant` entfernt oder mit einem Quellenhinweis versehen werden.

**Empfehlung:** `fragrant` aus den Traits entfernen, bis eine zuverlassige Quelle den Duft von 'Embassy' bestaetigt.

---

### H-003: Tigridia pavonia — Echter Mehltau-Erreger als Sphaerotheca sp. veraltet

**Dokument:** `tigridia_pavonia.md`, Sektion 5.2

**Problem:** Der Echter Mehltau an Tigridia wird als `Sphaerotheca sp.` bezeichnet. Dieser Gattungsname ist nach aktueller Taxonomie (Species Fungorum, Index Fungorum) obsolet. Die meisten ehemaligen Sphaerotheca-Arten wurden in die Gattung Podosphaera uebertragen. Fuer Iridaceae ist der Erreger in der Regel `Podosphaera xanthii` oder verwandte Arten.

**Korrekte Formulierung:**
```
Erreger: Podosphaera xanthii oder Erysiphe sp. (Iridaceae-spezifisch;
alter Name Sphaerotheca sp. ist taxonomisch obsolet)
```

---

### H-004: Cross-Dokument-Asymmetrie in Mischkultur — Tagetes

**Betroffene Dokumente:** Alle fuenf Dahlien-Dokumente listen Tagetes als guten Nachbarn (Score 0.8–0.9). Im bereits vorhandenen Dokument `viola_x_wittrockiana.md` und anderen Plant-Info-Dokumenten ist die Dahlie aber nicht als Partner von Tagetes gelistet.

**Empfehlung:** Da dies eine systemuebergreifende Asymmetrie ist, sollte das `compatible_with`-Graphkanten-System in Kamerplanter symmetrische Edges erzwingen oder das Fehlen einer Rueckbeziehung explizit als "asymmetrisch eingetragen" markieren. Dies ist kein Fehler in den vorliegenden Dokumenten, aber ein Hinweis fuer die Import-Validierung (REQ-012).

---

### H-005: Petunia x hybrida — Photoperiodismus-Einschraenkung fuer einzelne Sorten fehlt

**Dokument:** `petunia_x_hybrida.md`, Sektion 1.1

**Hinweis:** Das Dokument korrekt vermerkt: `day_neutral (die meisten Sorten; einige Sorten reagieren schwach langtagig)`. Einige Grandiflora-Petunia-Sorten zeigen tatsaechlich schwache Langtagsreaktion (beschleunigte Bluetenbildung unter langen Tagen). Dieser Hinweis ist fachlich korrekt und positiv zu bemerken. Fuer den Import koennte ein `photoperiod_type: day_neutral` mit einer Notiz genuegen; Sortenspezifika auf Cultivar-Ebene dokumentieren.

---

### H-006: Dahlia-Dokumente — Ohrwurm als Schadling: ambivalente Einordnung

**Betroffene Dokumente:** `dahlia_hapet_daydream.md`, `dahlia_pinnata_great_silence.md`, `dahlia_x_hybrida_armateras.md`

**Hinweis:** Ohrwuermer (Forficula auricularia) werden in `dahlia_x_hybrida_armateras.md` korrekt als ambivalent beschrieben: "zeigen auch positive Wirkung durch Blattlaus-Fraß". Die anderen Dokumente behandeln Ohrwuermer als reinen Schadling. Fachlich: Ohrwuermer fressen sowohl an Blueten- und Blattgewebe (Schadwirkung) als auch an Blattlaeuse und kleinen Weichkoerpern (Nutzwirkung). Die ambivalente Einordnung aus 'Armateras' ist die fachlich korrektere Darstellung und sollte in alle Dahlien-Dokumente uebertragen werden.

**Empfehlung:** In alle Dahlien-IPM-Sektionen den Hinweis ergaenzen: "Ohrwuermer sind ambivalent — Blattlauspraedatoren und Bluetenfrasser; Bekaempfung abwaegen."

---

### H-007: Nahrstoffprofile — Einheitlichkeit der NPK-Verhaeltnisse zwischen Dahlien-Dokumenten

**Betroffene Dokumente:** Alle fuenf Dahlien-Dokumente, Sektion 2.3

**Hinweis:** Die NPK-Verhaeltnisse fuer die Vollbluetephase variieren zwischen den Dokumenten:
- Hapet Daydream: 1:3:4
- Great Silence: 1:3:3
- Lavender Perfection: 0:2:3
- Armateras: 1:3:3 bis 0:2:3
- Embassy: (aus verkuerzter Darstellung nicht ablesbar)

Fachlich sind alle diese Verhaeltnisse plausibel (niedrig N, hoch P und K). Die Variation spiegelt unterschiedliche Quellen wider (ADS, Swan Island, Dahlia Doctor). Fuer die Datenbankimport-Konsistenz waere eine Standardisierung sinnvoll: z.B. Vollbluete bei allen Gartendahlien = `1:2:3 bis 0:2:3`. Sortenspezifische Abweichungen koennen auf Cultivar-Ebene ergan"zt werden.

---

## CSV-Import-Pruefung (REQ-012)

### Befunde fuer alle Dokumente

| Dokument | scientific_name | Cultivar-seed_type | Enum-Konsistenz | Kritische Felder leer | Bewertung |
|---------|----------------|-------------------|-----------------|----------------------|-----------|
| dahlia_hapet_daydream.md | Dahlia pinnata (Species) | clone (korrekt) | gut | VPD Dormanz | Bestanden mit Hinweisen |
| dahlia_pinnata_great_silence.md | Dahlia × pinnata (ABWEICHEND) | open_pollinated (FALSCH) | photoperiod_type Override fraglich | VPD Seneszenz | Fehler: seed_type, scientific_name |
| dahlia_x_hybrida_lavender_perfection.md | Dahlia x hybrida (ABWEICHEND) | cutting_stem;division (kein seed_type) | gut | VPD Dormanz | Fehler: scientific_name |
| dahlia_x_hybrida_armateras.md | Dahlia pinnata (korrekt) | open_pollinated (FRAGLICH fuer Cultivar) | gut | -- | Hinweis: seed_type pruefen |
| dahlia_embassy.md | Dahlia pinnata (korrekt) | clone (korrekt) | gut | Zuechter, Jahr | Bestanden mit Luecken |
| tigridia_pavonia.md | Tigridia pavonia (korrekt) | open_pollinated (korrekt fuer Artsorte) | gut | -- | Bestanden |
| petunia_x_hybrida.md | Petunia × hybrida (korrekt) | f1_hybrid, clone (korrekt) | gut | -- | Bestanden |

**Kritischer Import-Blocker:** Die abweichenden `scientific_name`-Werte in Dokument 2 (`Dahlia × pinnata`) und Dokument 3 (`Dahlia x hybrida`) verhindern die korrekte Zuordnung aller fuenf Dahlien-Cultivare zu einem einzigen Species-Datensatz. Vor dem Import muss K-001 behoben werden.

---

## Parameter-Uebersicht: Vollstaendigkeit der Messgroessen

| Parameter | Dahlien (5 Dok.) | Tigridia | Petunia | Fehlt |
|-----------|-----------------|----------|---------|-------|
| PPFD (uumol/m2/s) | vollstaendig | vollstaendig | vollstaendig | -- |
| DLI (mol/m2/d) | vollstaendig | vollstaendig | vollstaendig | -- |
| VPD (kPa) | Luecken in Dormanz | Dormanz: null | vollstaendig | Dormanz-VPD bei Dahlien |
| EC-Wert (mS/cm) | vorhanden | vorhanden | vorhanden | -- |
| pH | vorhanden | vorhanden | vorhanden | -- |
| rH% | vorhanden | vorhanden | vorhanden | -- |
| CO2 (ppm) | vollstaendig (400 ambient) | vollstaendig | vollstaendig | -- |
| Photoperiode (h) | vollstaendig | vollstaendig | vollstaendig | -- |
| Bodentemperatur Trigger | teils (Pflanzung > 10-12 °C) | vorhanden | fehlt | Petunie: kein Bodentrigger |

---

## Botanische Praezisierungs-Checkliste

| Aspekt | Status | Korrekturbedarf |
|--------|--------|-----------------|
| APG IV Familieneinordnung Asteraceae | korrekt | -- |
| APG IV Familieneinordnung Iridaceae | korrekt | -- |
| APG IV Familieneinordnung Solanaceae | korrekt | -- |
| Dahlia-Gattungsname | korrekt | -- |
| Dahlia-Art (Dahlia pinnata) | inkonsistent (K-001) | kritisch |
| Hybridzeichen x vs. × | inkonsistent | Hinweis H-004 |
| Tigridia-Wurzeltyp | falsch (K-003) | kritisch |
| Petunia-Hybridzeichen × | korrekt im Titel | -- |
| Ordnungsebene Asterales, Asparagales, Solanales | korrekt | -- |
| Mehltau-Erreger Sphaerotheca (veraltet) | veraltet (H-003) | minor |

---

## Empfohlene Massnahmen (nach Prioritaet)

### Vor Import (zwingend)
1. **K-001 loesen:** Einheitlichen `scientific_name: Dahlia pinnata` in allen fuenf Dahlia-Dokumenten und CSV-Zeilen setzen.
2. **K-003 loesen:** `root_type: bulbous` in `tigridia_pavonia.md` auf `corm` aendern.
3. **M-002 loesen:** `seed_type` und `photoperiod_type` in `dahlia_pinnata_great_silence.md` CSV korrigieren.

### Vor Produktionseinsatz (empfohlen)
4. **M-003 loesen:** Freiland-pH-Empfehlung in 'Lavender Perfection' auf max. 7.0 begrenzen.
5. **M-004 loesen:** Naehrstoffbedarf 'Armateras' auf `heavy_feeder` angleichen.
6. **M-006 loesen:** Dormanz-Luftfeuchte-Werte auf 60–75 % vereinheitlichen.
7. **H-001 umsetzen:** `<!-- DATEN FEHLEN -->` in VPD-Dormanz-Feldern durch `null` ersetzen.

### Als Verbesserung (optional)
8. **M-008 klaeren:** Allelopathie-Score Petunia belegen oder auf 0.0 setzen.
9. **M-009 anpassen:** Tomate-Petunia-Kompatibilitaets-Score auf 0.5–0.6 senken.
10. **H-003 korrigieren:** Mehltau-Erreger Tigridia auf Podosphaera-Nomenklatur aktualisieren.
11. **H-006 angleichen:** Ohrwurm-Ambivalenz in alle Dahlien-Dokumente uebertragen.

---

## Empfohlene Quellen fuer Korrekturen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Dahlia-Taxonomie (aktuell) | Plants of the World Online (POWO) | powo.science.kew.org |
| Dahlia-Taxonomie (aktuell) | World Flora Online | worldfloraonline.org |
| ADS-Klassifikation | American Dahlia Society | dahlia.org/guide |
| Dahlia-Duengung | ADS Nutrients for Dahlias | dahlia.org/docsinfo/articles/nutrients-for-dahlias |
| Tigridia-Botanik | Pacific Bulb Society | pacificbulbsociety.org |
| Mehltau-Taxonomie (aktuell) | Index Fungorum | indexfungorum.org |
| Petunia-Allelopathie | MDPI Horticulturae | mdpi.com/2311-7324 |
| Toxizitaet | ASPCA Animal Poison Control | aspca.org/pet-care/animal-poison-control |
| Lagerung Dahlienknollen | Longfield Gardens | longfield-gardens.com/article/how-to-overwinter-dahlias |

---

## Glossar (fuer diesen Review-Kontext)

- **Korm (Corm):** Solides, unterirdisches Speicherorgan (z.B. Tigridia, Gladiole, Crocus) — keine Schichten wie bei echten Zwiebeln. Bildet jaehrlich Tochterkorme an der Basis.
- **Tuberkulose Knolle:** Aufgetriebene Speicherwurzel (z.B. Dahlie, Canna) — strukturell verschieden von Korm und Zwiebel.
- **Tuberisierung:** Bildung von Speicherknollen; bei Dahlien kurztagsgesteuerter Prozess.
- **Fakultative Kurztagspflanze:** Pflanze die unter Kurztag schneller bluet, aber auch unter Langtag bluehen kann — Dahlien gehoeren in diese Kategorie (im Gegensatz zu obligaten KT-Pflanzen wie Chrysantheme).
- **VPD (Vapor Pressure Deficit):** Dampfdruckdefizit in kPa — Mass fuer den "Durst" der Luft; nicht steuerbar bei eingelagerten Knollen.
- **APG IV:** Aktuelle Klassifikation der Bluetenpflanzen (Angiosperm Phylogeny Group IV, 2016) — verbindlicher Nomenklaturstandard.
- **ADS:** American Dahlia Society — staendige Klassifikationshoheit fuer Dahlientypen (Ball, Pompon, Decorative, Cactus etc.).
