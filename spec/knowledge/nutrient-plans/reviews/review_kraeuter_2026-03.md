# Agrarbiologisches Review: Naehrstoffplaene Petersilie, Schnittlauch, Dill / Plagron Terra

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-06
**Fokus:** Kraeuteranbau Outdoor/Indoor, Erdsubstrat, Schwachzehrer/Mittelzehrer, Blatterntekultur, Perennial-Zyklussteuerung
**Analysierte Dokumente:**
- `spec/ref/nutrient-plans/petersilie_plagron_terra.md` (v1.0)
- `spec/ref/nutrient-plans/schnittlauch_plagron_terra.md` (v1.0)
- `spec/ref/nutrient-plans/dill_plagron_terra.md` (v1.0)
- `spec/ref/plant-info/petroselinum_crispum.md`
- `spec/ref/plant-info/allium_schoenoprasum.md`
- `spec/ref/plant-info/anethum_graveolens.md`
- `spec/ref/products/plagron_terra_grow.md` (EC-Referenzwert 0,08 mS/cm pro ml/L)
- `spec/ref/products/plagron_pure_zym.md` (EC-Referenzwert 0,00 mS/cm pro ml/L)

---

## Gesamtbewertung

| Dimension | Petersilie | Schnittlauch | Dill | Kommentar |
|-----------|-----------|-------------|------|-----------|
| Botanische Korrektheit | 4/5 | 5/5 | 4/5 | Kleinere Fehler bei Keimtyp-Angabe (Petersilie) und NPK-Mapping (Dill) |
| Phasen-Mapping-Qualitaet | 5/5 | 5/5 | 5/5 | Alle drei Plaene lueckenlos und biologisch korrekt strukturiert |
| cycle_restart-Logik | -- | 5/5 | -- | Schnittlauch-Neustart auf Sequenz 3 (VEGETATIVE) ist fachlich musterhaft |
| NPK-Produktwahl | 5/5 | 5/5 | 4/5 | Dill: NPK-Ratio im VEGETATIVE-JSON weicht von Produktprofil ab |
| EC-Budget-Korrektheit | 5/5 | 5/5 | 5/5 | Alle EC-Berechnungen mathematisch korrekt, alle Werte artgerecht |
| Dosierungslogik | 5/5 | 5/5 | 5/5 | Schwachzehrer/Mittelzehrer-Differenzierung konsequent umgesetzt |
| Saisonplan-Plausibilitaet | 5/5 | 5/5 | 5/5 | Alle Kalenderangaben fuer Mitteleuropa korrekt und realistisch |
| Sicherheitshinweise | 5/5 | 5/5 | 5/5 | Toxizitaet (Katze/Hund), Verwechslungsgefahr, Kontaktallergen vollstaendig |
| Konsistenz Tabellen zu JSON | 4/5 | 5/5 | 3/5 | Dill: NPK-Ratio-Diskrepanz im JSON-Export |
| Vollstaendigkeit | 4/5 | 5/5 | 5/5 | Petersilie: Keimtyp-Widerspruch korrekturbeduerftig |

**Gesamteinschaetzung:** Alle drei Naehrstoffplaene sind fachlich auf hohem Niveau. Das Schwachzehrer/Mittelzehrer-Prinzip ist korrekt differenziert und konsequent durch alle Phasen durchgefuehrt. Dosierungen von 1,5 bis 2,5 ml/L Terra Grow (25--50% der Herstellerempfehlung) sind fuer Kuechenkraeuter wissenschaftlich korrekt und auf Aroma- und Qualitaetserhalt optimiert. Die Schnittlauch-Zyklus-Neustart-Logik ist agronomisch musterhaft umgesetzt. Drei korrekturbeduerftige Punkte: (1) ein Widerspruch im Keimtyp der Petersilie zwischen Steckbrief und Naehrstoffplan, (2) eine NPK-Ratio-Diskrepanz im Dill-JSON-Export und (3) eine botanische Unschaerfe beim Schnittlauch-Bluetetyp. Keiner dieser Punkte gefaehrdet die Pflanzensicherheit oder Erntequaltitaet.

---

## Findings

### P-001: Keimtyp-Widerspruch Petersilie -- Dunkelkeimer vs. Lichtkeimer

**Schweregrad:** Hoch -- fachlicher Widerspruch zwischen verlinktem Steckbrief und Naehrstoffplan; kann zu Keimversagen fuehren

**Dokument:** `petersilie_plagron_terra.md`, Abschnitt 2 (Zeile 48); `petroselinum_crispum.md`, Abschnitt 1.3 (Zeile 56)

**Problem:** Der Naehrstoffplan deklariert Petersilie explizit als Dunkelkeimer ("**DUNKELKEIMER:** Samen 0.5 cm mit Erde bedecken"). Der verlinkte Steckbrief `petroselinum_crispum.md` klassifiziert dieselbe Art dagegen als Lichtkeimer ("**Lichtkeimer** -- Samen nur leicht mit Erde bedecken (max. 0.5 cm) oder nur andruecken"). Beide Dokumente empfehlen 0,5 cm Saattiefe, widersprechen sich aber beim Keimtyp, was fuer den Nutzer verwirrend ist.

**Fachlicher Befund:** Die biologische Wahrheit ist differenziert. Petersilie (*Petroselinum crispum*) ist in der Fachliteratur uneinheitlich eingestuft. Die Hauptquelle fuer die Keim-Verzoegerung ist nicht Lichtmangel, sondern die Furanocumarine in der Samenschale (keimhemmende Substanzen). Beim Einweichen (24h) und einer Abdeckung von 0,5 cm keimt Petersilie mit oder ohne Licht vergleichbar. Die Praxis-Empfehlung von 0,5 cm Abdeckung ist fuer beide Klassifikationen identisch -- der Widerspruch ist in der Benennung, nicht in der Handlungsempfehlung.

**Empfehlung:** Im Naehrstoffplan den Begriff "Dunkelkeimer" ersetzen durch "bedeckt saeen (0,5 cm -- keimhemmende Furanocumarine in der Samenschale erfordern Bodenkontakt, Licht ist kein entscheidender Faktor)". Alternativ: Steckbrief auf "fakultativ bedeckt saeen" anpassen. Die 24h-Einweich-Empfehlung ist korrekt und sollte in beiden Dokumenten konsistent stehen.

**Auswirkung auf Naehrstoffplan:** Gering -- die Dosierungslogik ist nicht betroffen. Nur die Erlaeuterungsnotizen (notes-Felder) sind inkonsistent.

---

### P-002: Schnittlauch -- cycle_restart_from_sequence korrekt und vorbildlich

**Schweregrad:** Keine Korrektur noetig -- positiver Befund zur Dokumentation

**Dokument:** `schnittlauch_plagron_terra.md`, Abschnitt 1 (Zeile 23)

**Bewertung:** Die Verwendung von `cycle_restart_from_sequence: 3` (VEGETATIVE) ist fachlich exakt korrekt. Schnittlauch (*Allium schoenoprasum*) ist vollstaendig winterhart (bis -30 degC), treib nach der Vernalisation (6--8 Wochen < 5 degC) jedes Fruehjahr aus den Zwiebeln neu aus. Die Keimungs- und Saemlings-Phasen (sequence_order 1 und 2) laufen nur beim Erstanbau ab und werden ab dem 2. Jahr ubersprungen. Der Neustart direkt auf VEGETATIVE (sequence_order 3) spiegelt die biologische Realitaet exakt ab: etablierte Horste starten im Maerz/April unmittelbar als erntereife Pflanzen, ohne die Jugendphase erneut zu durchlaufen. Die is_recurring-Flags auf VEGETATIVE, FLOWERING und DORMANCY (alle true) sind ebenfalls korrekt.

**Besonders hervorzuheben:** Die Erlaeuterung zum Hinweis, dass im Herbst die Halme NICHT abgeschnitten werden sollen ("Naehrstoffe wandern zurueck in die Zwiebel"), ist eine praxisrelevante und biologisch korrekte Anweisung, die in vielen kommerziellen Pflegeanweisungen fehlt.

---

### P-003: Dill -- NPK-Ratio-Diskrepanz im VEGETATIVE-JSON-Export

**Schweregrad:** Mittel -- Datenkonsistenz-Problem fuer den Kamerplanter-Import

**Dokument:** `dill_plagron_terra.md`, Abschnitt 4.3 (Tabellen-Zeile npk_ratio), JSON VEGETATIVE (Zeile 435)

**Problem:** In der Phasen-Tabelle (Markdown) ist das NPK-Verhaeltnis fuer die VEGETATIVE-Phase korrekt mit **(2, 1, 2)** angegeben -- ein angepasstes Profil gegenueber dem Terra-Grow-Produktprofil (3-1-3), das die bewusst niedrige Dosierung und den Schwachzehrer-Charakter von Dill widerspiegelt. Im JSON-Export derselben Phase ist jedoch `"npk_ratio": [2.0, 1.0, 2.0]` angegeben, was inhaltlich stimmt. Die Diskrepanz liegt woanders: Der notes-Text der Phase schreibt "Kalium foerdert Aromaoelproduktion" und erwaehnt das 3-1-3-Produktprofil als Referenz, waehrend das npk_ratio 2-1-2 die effektive Naehrstoffaufnahme (verdunnte Dosis) darstellt -- das ist fachlich vertretbar, aber sollte im Dokument explizit als "effektives NPK der Gesamtloesung" vs. "NPK-Verhaeltnis des Produktes" unterschieden und kommentiert werden.

**Praezisierung:** Terra Grow hat das Produktprofil 3-1-3. Bei 2,0 ml/L (halbe Dosis eines 5 ml/L-Produktes) bleibt das N:P:K-Verhaeltnis 3:1:3 -- es aendert sich nicht durch Verduennung. Die Angabe von 2-1-2 ist daher konzeptionell eine Vereinfachung, die Dill als "weniger N-intensiv" als das Produktprofil kommunizieren soll, biologisch aber nicht dem tatsaechlichen Verhaeltnis entspricht.

**Empfehlung:** Entweder das npk_ratio konsistent auf [3.0, 1.0, 3.0] setzen (Produktprofil, wie bei Schnittlauch und Petersilie gemacht) und die niedrige Gesamtversorgung ueber die EC-Angabe und ml/L-Dosis kommunizieren -- oder in einer Code-Anmerkung erklaeren, dass das angegebene NPK-Ratio das gewuenschte Aufnahmeverhaeltnis der Pflanze (nicht das Produktprofil) darstellt.

---

### P-004: Schnittlauch -- Bluetentyp-Beschreibung leicht unschaerft

**Schweregrad:** Niedrig -- Terminologie-Unschaerfe ohne praktische Auswirkung

**Dokument:** `schnittlauch_plagron_terra.md`, Abschnitt 4.4 (FLOWERING), notes-Feld

**Problem:** Der Naehrstoffplan beschreibt: "Keine Duengung waehrend der Bluete. Lila Kugelblueten sind essbar." Die Bluete wird als Grund fuer Duengungsstopp angegeben, ohne die physiologische Begruendung zu nennen. Beim Steckbrief `allium_schoenoprasum.md` steht korrekt: NPK-Bluete = 2-2-2 (EC 1,0--1,4 mS). Das Naehrstoffplan-Dokument waehlt bewusst 0-0-0 fuer die FLOWERING-Phase, was fuer einen Schwachzehrer vertretbar ist, da:
(a) Schnittlauchblueten biologisch kein P-K-Boost brauchen (kein Frucht-/Samenansatz angestrebt),
(b) die Halm-Qualitaet nach der Bluete sowieso nachlasst und ein Rueckschnitt folgt,
(c) die kurze Bluetezeit (3--4 Wochen) ohne Duengung ueberbruckt wird.

Die Entscheidung ist also vertretbar, wuerde aber von einer kurzen Begruendung profitieren: "Keine Duengung waehrend der Bluete, da keine Samenreife angestrebt und Bluetezeit kurz -- die Zwiebelspeicher reichen fuer die Bluephase aus."

**Empfehlung:** Im notes-Feld der FLOWERING-Phase eine Erklaerung ergaenzen, warum 0-0-0 trotz aktivem Pflanzenwachstum ausreicht.

---

### P-005: Petersilie -- EC-Budget-Korrektheit (vollstaendige Verifikation)

**Schweregrad:** Keine Korrektur noetig -- vollstaendige Pruefung aller EC-Werte

**Dokument:** `petersilie_plagron_terra.md`, Abschnitt 4

**Verifikation aller EC-Berechnungen:**

| Phase | Terra Grow ml/L | Pure Zym ml/L | EC-Beitrag TG | EC-Beitrag PZ | EC-Basis-Wasser | EC gesamt (Rechnung) | EC gesamt (Dokument) | Status |
|-------|----------------|--------------|--------------|--------------|----------------|---------------------|---------------------|--------|
| GERMINATION | 0 | 0 | 0,00 | 0,00 | ~0,40 | ~0,40 | ~0,40 | KORREKT |
| SEEDLING | 1,5 | 0 | 0,12 | 0,00 | ~0,40 | ~0,52 | ~0,52 | KORREKT |
| VEGETATIVE | 2,5 | 1,0 | 0,20 | 0,00 | ~0,40 | ~0,60 | ~0,60 | KORREKT |
| HARVEST | 2,0 | 1,0 | 0,16 | 0,00 | ~0,40 | ~0,56 | ~0,56 | KORREKT |
| DORMANCY | 0 | 0 | 0,00 | 0,00 | ~0,40 | ~0,40 | ~0,40 | KORREKT |

Alle fuenf EC-Budgets sind mathematisch korrekt (EC/ml-Referenz: Terra Grow 0,08 mS/cm, Pure Zym 0,00 mS/cm). Die Ziel-EC-Werte von 0,5--0,6 mS/cm sind fuer einen Mittelzehrer in Erdsubstrat biologisch korrekt -- deutlich unter dem hydroponischen Optimum (1,2--1,8 mS/cm gemaess Steckbrief), was die organische Pufferwirkung des Erdsubstrats angemessen beruecksichtigt. Kein Korrekturbedarf.

---

### P-006: Schnittlauch -- EC-Budget-Korrektheit (vollstaendige Verifikation)

**Schweregrad:** Keine Korrektur noetig

**Dokument:** `schnittlauch_plagron_terra.md`, Abschnitt 4

**Verifikation aller EC-Berechnungen:**

| Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (Rechnung) | EC gesamt (Dokument) | Status |
|-------|----------------|--------------|---------------------|---------------------|--------|
| GERMINATION | 0 | 0 | ~0,40 | ~0,40 | KORREKT |
| SEEDLING | 1,5 | 0 | ~0,52 | ~0,52 | KORREKT |
| VEGETATIVE | 2,0 | 1,0 | ~0,56 | ~0,56 | KORREKT |
| FLOWERING | 0 | 0 | ~0,40 | ~0,40 | KORREKT |
| DORMANCY | 0 | 0 | ~0,40 | ~0,40 | KORREKT |

EC von 0,56 mS/cm in der VEGETATIVE-Phase liegt deutlich unter dem Schwachzehrer-Limit von 0,8 mS/cm (Steckbrief: EC-Limit 2,0 mS im Hydroponik, Erd-Aequivalent ca. 0,6--0,8 mS). Korrekt und sicher. Kein Korrekturbedarf.

---

### P-007: Dill -- EC-Budget-Korrektheit (vollstaendige Verifikation)

**Schweregrad:** Keine Korrektur noetig

**Dokument:** `dill_plagron_terra.md`, Abschnitt 4

**Verifikation aller EC-Berechnungen:**

| Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (Rechnung) | EC gesamt (Dokument) | Status |
|-------|----------------|--------------|---------------------|---------------------|--------|
| GERMINATION | 0 | 0 | ~0,40 | ~0,40 | KORREKT |
| SEEDLING | 1,5 | 0 | ~0,52 | ~0,52 | KORREKT |
| VEGETATIVE | 2,0 | 1,0 | ~0,56 | ~0,56 | KORREKT |
| FLOWERING | 0 | 0 | ~0,40 | ~0,40 | KORREKT |
| HARVEST (Seneszenz) | 0 | 0 | ~0,40 | ~0,40 | KORREKT |

EC-Maximum von 0,56 mS/cm liegt unter dem Steckbrief-Limit von 1,2 mS/cm fuer Dill-Hydroponik. Fuer Erdsubstrat-Direktsaat ist das angemessen niedrig. Kein Korrekturbedarf.

---

### P-008: Petersilie -- Phasen-Mapping und Lueckenlos-Pruefung

**Schweregrad:** Keine Korrektur noetig -- positiver Befund

**Dokument:** `petersilie_plagron_terra.md`, Abschnitt 2

**Pruefung:**

| Phase | Wochen | Enum | Dauer | Summe |
|-------|--------|------|-------|-------|
| GERMINATION | 1--4 | germination | 4 Wochen | 4 |
| SEEDLING | 5--10 | seedling | 6 Wochen | 10 |
| VEGETATIVE | 11--24 | vegetative | 14 Wochen | 24 |
| HARVEST | 25--36 | harvest | 12 Wochen | 36 |
| DORMANCY | 37--44 | dormancy | 8 Wochen | 44 |
| **Gesamt** | | | | **44 Wochen** |

Kein Lueck, kein Ueberlapp. Die Entscheidung, FLOWERING wegzulassen und direkt von VEGETATIVE zu HARVEST uebergehen (Bluete erst im unerwuenschten 2. Jahr), ist botanisch korrekt und praxisgerecht fuer eine 1-Jahr-Blattkultur. Die DORMANCY-Phase ist fachlich diskutierbar (Petersilie macht keine echte Dormanz im physiologischen Sinne, sondern ein verlangsamtes Winterwachstum) -- aber fuer die Softwarelogik eines "Saisonendes" ist die Klassifikation pragmatisch korrekt.

Die Entscheidung `cycle_restart_from_sequence: null` (kein Neustart) ist fuer Petersilie als 1-Jahr-Blattkultur korrekt. Im 2. Jahr waere die Pflanze biologisch unbrauchbar (Schossen, bittere Blaetter). Neues Saatgut als neuer Plan-Durchlauf ist der richtige Ansatz.

**Saisonplan Mitteleuropa:** Aussaat Maerz indoor, Auspflanzung nach Eisheiligen (Mitte Mai), Ernte Mai--November, Saisonende Dezember -- alle Angaben fuer Mitteleuropa (Zone 7--8) korrekt.

---

### P-009: Schnittlauch -- Phasen-Mapping und Lueckenlos-Pruefung

**Schweregrad:** Keine Korrektur noetig

**Dokument:** `schnittlauch_plagron_terra.md`, Abschnitt 2

**Pruefung Erstjahr:**

| Phase | Wochen | Enum | Dauer | Summe |
|-------|--------|------|-------|-------|
| GERMINATION | 1--3 | germination | 3 Wochen | 3 |
| SEEDLING | 4--8 | seedling | 5 Wochen | 8 |
| VEGETATIVE | 9--20 | vegetative | 12 Wochen | 20 |
| FLOWERING | 21--24 | flowering | 4 Wochen | 24 |
| DORMANCY | 25--44 | dormancy | 20 Wochen | 44 |
| **Gesamt** | | | | **44 Wochen** |

Kein Lueck, kein Ueberlapp. Lueckenlos-Pruefung bestanden.

**Pruefung Folgejahr (cycle_restart auf Seq 3):** VEGETATIVE (12 Wo) + FLOWERING (4 Wo) + DORMANCY (20 Wo) = 36 Wochen. Das entspricht einem realen Jahresrhythmus (Maerz--Oktober aktiv, Oktober--Februar Dormanz). Biologisch und kalendarisch korrekt.

**Saisonplan Mitteleuropa:** Neuaustrieb Maerz, Haupternte Maerz--Mai, Bluete Juni--Juli, 2. Austrieb Juli--September, Dormanz Oktober--Februar -- alle Angaben stimmen mit dem realen Schnittlauch-Jahresrhythmus in Mitteleuropa ueberein.

---

### P-010: Dill -- Phasen-Mapping und Lueckenlos-Pruefung

**Schweregrad:** Keine Korrektur noetig

**Dokument:** `dill_plagron_terra.md`, Abschnitt 2

**Pruefung:**

| Phase | Wochen | Enum | Dauer | Summe |
|-------|--------|------|-------|-------|
| GERMINATION | 1--2 | germination | 2 Wochen | 2 |
| SEEDLING | 3--4 | seedling | 2 Wochen | 4 |
| VEGETATIVE | 5--8 | vegetative | 4 Wochen | 8 |
| FLOWERING | 9--11 | flowering | 3 Wochen | 11 |
| HARVEST (Seneszenz) | 12--12 | harvest | 1 Woche | 12 |
| **Gesamt** | | | | **12 Wochen** |

Kein Lueck, kein Ueberlapp. 12-Wochen-Zyklus entspricht der realen Kulturzeit von Anethum graveolens (60--90 Tage = 8--13 Wochen). Die Dokumentation der Staffelsaat-Strategie (4 Saetze April--Juli) ist agronomisch korrekt und das einzig praxistaugliche Konzept fuer kontinuierliche Dillernte.

Die Verwendung von HARVEST fuer die Seneszenz-Phase ist eine pragmatische Entscheidung (kein SENESCENCE-Enum verfuegbar) -- fachlich vertretbar, wenn die notes-Felder die biologische Bedeutung klar erlaeutern (was hier der Fall ist).

**Saisonplan Mitteleuropa:** Direktsaat ab 8 degC Bodentemperatur (ca. April), Staffelernten April--Oktober -- korrekt fuer Mitteleuropa.

---

### P-011: Dosierungsvergleich Schwachzehrer vs. Mittelzehrer -- fachliche Angemessenheit

**Schweregrad:** Keine Korrektur noetig -- positiver Befund zur Dokumentation

**Alle drei Dokumente:** Abschnitt 4

**Bewertung der Dosierungslogik:**

| Pflanze | Zehrer-Typ | VEGETATIVE ml/L | Max EC gesamt | Steckbrief-Limit (Hydro) | Beurteilung |
|---------|-----------|----------------|--------------|--------------------------|-------------|
| Petersilie | Mittelzehrer | 2,5 (halbe Dosis) | 0,60 mS | 1,2--1,8 mS | Korrekt: Erd-Substrat erhaelt signifikante Pufferkapazitaet, 0,60 mS angemessen |
| Schnittlauch | Schwachzehrer | 2,0 (halbe Dosis) | 0,56 mS | <2,0 mS | Korrekt: unter Limit, aromaerhaltend |
| Dill | Schwachzehrer | 2,0 (halbe Dosis) | 0,56 mS | <1,2 mS | Korrekt: unter Limit, Aroma/Schoss-Profil optimal |

Die Petersilie erhaelt die hoechste Dosis (als Mittelzehrer) -- korrekt. Schnittlauch und Dill erhalten identische Dosen, obwohl Dill gemaess Steckbrief ein etwas niedrigeres EC-Limit hat (1,2 vs. 2,0 mS im Hydro). Da beide Plaene mit 0,56 mS weit unter beiden Limits bleiben, ist die Gleichsetzung im Erdsystem unbedenklich.

Die Entscheidung, fuer alle drei Kraeuter Terra Grow + Pure Zym (kein Terra Bloom) zu verwenden, ist korrekt: alle drei werden als Blattkultur und nicht fuer Frucht- oder Samenproduktion gefuehrt. Ein Bloom-Duenger wuerde die unerwuenschte Bluetenbildung (Petersilie, Dill) foerdern oder bei Schnittlauch unnoetige P-K-Belastung erzeugen.

---

### P-012: Petersilie -- Dunkelkeimer-Begruendung mit Furanocumarin korrekt

**Schweregrad:** Keine Korrektur noetig -- Qualitaets-Verifikation

**Dokument:** `petersilie_plagron_terra.md`, Abschnitt 4.1 und 6

**Bewertung:** Die Erlaeuterung der Keimverzoegerung durch "keimhemmende Furanocumarine in der Samenschale" ist botanisch korrekt. Petroselinum crispum enthaelt Furanocumarine (Psoralen, Bergapten, Xanthotoxin) nicht nur als phototoxische Kontaktallergene, sondern tatsaechlich auch in der Testa (Samenschale) als Keimhemmer. Das 24h-Einweichen lost diese Hemmstoffe auf und verkuerzt die Keimdauer nachweislich um 5--10 Tage. Die angegebene Keimdauer von 14--28 Tagen ist korrekt und deckt sich mit den Steckbrief-Angaben (14--28 Tage). Der Hinweis, dass bei Austrocknung waehrend der Keimung keine Nachkeimung erfolgt ("Samen keimen nicht nach!"), ist biologisch korrekt -- Petersiliensamen sind nach dem Austrocknen waehrend der Quellung abgestorben.

---

### P-013: Mischkultur-Warnung Dill/Petersilie konsistent

**Schweregrad:** Keine Korrektur noetig -- positive Konsistenz-Pruefung

**Dokument:** `petersilie_plagron_terra.md` Abschnitt 6 (Mischkultur); `dill_plagron_terra.md` Abschnitt 6

**Bewertung:** Beide Naehrstoffplaene warnen korrekt vor der Kombination Petersilie/Dill (gleiche Familie Apiaceae, Allelopathie-Score 0,1/0,2, Kreuzbestaeubung moeglich). Diese Warnung ist biologisch korrekt und wird durch beide Steckbriefe bestaetigt (Dill als "schlechter Nachbar" fuer Petersilie und umgekehrt). Die Warnung im Petersilie-Plan ("Dill hemmt Petersilie -- Allelopathie") ist allerdings eine Vereinfachung: Die primaerenGruende sind Kreuzbestaeubung (verraenderte Samenqualitaet) und gemeinsame Schaedlinge (Moehrenfliege), weniger klassische Allelopathie im engeren Sinne. Fuer die Praxis ist die Warnung dennoch korrekt.

---

### P-014: Schnittlauch -- Schwefelversorgung und Allicin-Synthese

**Schweregrad:** Hinweis -- fachlich korrekt erwaehnt, aber unvollstaendig in der Loesungsbeschreibung

**Dokument:** `schnittlauch_plagron_terra.md`, Abschnitt 6 (Schwefelversorgung)

**Bewertung:** Der Naehrstoffplan weist korrekt darauf hin, dass Terra Grow keine spezifische Schwefelquelle enthaelt und empfiehlt Kompost oder Bittersalz (Magnesiumsulfat) als Ergaenzung. Das ist fachlich korrekt: Allium-Arten synthetisieren ihre charakteristischen Aromastoffe (Allicin, Thiosulfinate, N-Propyl-Disulfid) aus schwefelhaltigen Aminosaeuren (Allin), was eine ausreichende Schwefelversorgung voraussetzt. Terra Grow (3-1-3) deckt N, P, K ab, aber nicht spezifisch Schwefel.

**Praezisierung:** Bittersalz (MgSO4) als Schwefelquelle ist korrekt, liefert aber gleichzeitig Magnesium -- bei bereits magnesiumreichem Leitungswasser sollte das beachtet werden. Eine Alternative waere Kaliumsulfat (K2SO4, z.B. als Yara Mivena oder vergleichbare Gartenprodukte), das Schwefel ohne zusaetzliches Magnesium liefert. Die bestehende Empfehlung ist aber praktisch und fuer Hobbyanbau ausreichend.

---

### P-015: Dill -- Direktsaat-Empfehlung und Pfahlwurzel-Hinweis

**Schweregrad:** Keine Korrektur noetig -- positiver Befund

**Dokument:** `dill_plagron_terra.md`, Abschnitt 2 und 6

**Bewertung:** Die wiederholte, hervorgehobene Warnung "NICHT pikieren oder umtopfen -- Pfahlwurzel!" ist fachlich korrekt und praxisrelevant. Anethum graveolens entwickelt eine empfindliche Pfahlwurzel, die bei Verpflanzung fast immer beschaedigt wird und zu Wachstumsstockung oder Pflanzentod fuehrt. Die Bodentemperatur-basierte Saatempfehlung (ab 8 degC) statt eines festen Kalenderdatums ist agronomisch korrekt und Phaenoligen-konform. Der Steckbrief bestaetigt 8 degC als minimale Keimtemperatur. Fuer Mitteleuropa entspricht das typisch dem Zeitraum April (Friihjahrssaaten) bis Juli (letzte Staffelsaat). Korrekt.

---

## Zusammenfassung der Korrekturpunkte

| Finding | Pflanze | Typ | Prioritaet | Status |
|---------|---------|-----|-----------|--------|
| P-001 | Petersilie | Keimtyp-Widerspruch (Dunkelkeimer vs. Lichtkeimer) | Hoch | Korrektur empfohlen |
| P-003 | Dill | NPK-Ratio-Konzept (2-1-2 vs. Produktprofil 3-1-3) | Mittel | Klaerung/Kommentar empfohlen |
| P-004 | Schnittlauch | Begruendung fehlt fuer 0-0-0 in FLOWERING | Niedrig | Ergaenzung empfohlen |
| P-014 | Schnittlauch | Schwefelquelle: Bittersalz-Alternative erwaehnen | Niedrig | Ergaenzung optional |

**Keine sicherheitsrelevanten oder pflanzenschaedigenden Fehler gefunden.**

---

## Qualitaetsstaerken der drei Plaene (Best Practices)

1. **Schwachzehrer/Mittelzehrer-Differenzierung** ist konsequent durchgefuehrt und korrekt. Petersilie erhaelt mehr als Schnittlauch/Dill -- das entspricht der botanischen Realitaet.

2. **Schnittlauch cycle_restart auf Sequenz 3 (VEGETATIVE)** ist eine technisch elegante und biologisch praezise Umsetzung der Perennitaet im Kamerplanter-Datenmodell.

3. **Pure Zym (0,00 mS/cm)** wird gezielt als EC-neutrales Substrat-Enzym eingesetzt -- kein Risiko der Ueberduengung, gleichzeitig Substrat-Gesundheit gesichert.

4. **Giessintervall-Overrides** in GERMINATION (taeglich) und DORMANCY (5--14 Tage) sind biologisch korrekt und phasenspezifisch gut ausgestaltet.

5. **Vernalisation-Hinweise** beim Schnittlauch (6--8 Wochen < 5 degC fuer kraeftigen Fruehjahraustrieb) und der Hinweis, dass Halme im Herbst NICHT abgeschnitten werden sollen, sind fachlich exzellent.

6. **Staffelsaat-Dokumentation** beim Dill (4 Saetze April--Juli) ist die einzig praxistaugliche Strategie fuer kontinuierliche Dillernte und korrekt ausgearbeitet.

7. **Sicherheitshinweise** (Allium-Toxizitaet fuer Katze/Hund, Petersilie-Furanocumarine, Verwechslungsgefahr mit Schierling) sind vollstaendig und praezise.

8. **Allelopathie-Warnung Petersilie/Dill** ist in beiden Plaenen konsistent -- verhindert schlechte Mischkultur-Entscheidungen.

---

## Abschliessende Empfehlungen

1. **Sofort:** Keimtyp-Terminologie in `petersilie_plagron_terra.md` harmonisieren mit `petroselinum_crispum.md` (Finding P-001). Formulierungsvorschlag im Finding enthalten.

2. **Vor Import:** NPK-Ratio-Konzept in `dill_plagron_terra.md` VEGETATIVE-Phase klaeren (Finding P-003). Entweder auf [3.0, 1.0, 3.0] (Produktprofil) oder mit Erklaerungskommentar versehen.

3. **Optional:** Begruendungs-Notiz in Schnittlauch FLOWERING-Phase ergaenzen (Finding P-004).

4. **Optional:** Bittersalz-Alternative fuer Schwefelversorgung beim Schnittlauch erwaehnen (Finding P-014).

Die Plaene sind in ihrer Gesamtheit fuer den Kamerplanter-Import freigegeben. Die Korrekturen unter Punkt 1 und 2 sollten vor dem Import erfolgen, um Datenkonsistenz zu gewaehrleisten.
