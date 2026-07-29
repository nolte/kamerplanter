# REQ-004 — BDD-Migrations-Triage der E2E-Testfälle

**Erstellt:** 2026-07-29
**Auftrag:** Issue [#774](https://github.com/nolte/kamerplanter/issues/774) — Folgearbeitspaket aus ADR-010
**Gegenstand:** alle 92 Testfälle in `spec/e2e-testcases/TC-REQ-004.md`
**Referenzfall:** TC-004-092 (`tests/e2e/features/watering_cross_view_consistency.feature`, Bindungen in `tests/e2e/test_req004_watering_cross_view_consistency_bdd.py`)
**Art des Dokuments:** Messung, kein Umsetzungsvorschlag. Es wurde kein Testcode und keine `.feature`-Datei geschrieben.

---

## Kurzfassung

Die Hochrechnung, die ADR-010 §6 ausdrücklich als **Annahme** markiert hat, **trägt nicht**.

Von den 91 verbleibenden REQ-004-Testfällen ist **kein einziger** eine Parametervariante des
Referenzfalls. Der Grund ist strukturell und nicht überraschend, sobald man das TC-Dokument als
Ganzes liest: TC-004-092 ist der **einzige** Testfall in `TC-REQ-004.md`, der die Kopplung
Gießvorgang → Gießprotokoll → Aufgabenverlauf beschreibt. Es gibt keine zweite Zeile derselben
Melodie, die man mit anderen Zahlen singen könnte. Die gemessenen „9 von 11 Bindungen wörtlich
wiederverwendbar" sind eine **fallinterne** Kennzahl (derselbe Fall mit anderen Mengen/Daten), keine
**fallübergreifende** — und die ADR hat aus der ersten auf die zweite geschlossen.

Was die Messung **stattdessen** zeigt und was die Migrationsfrage rettet: Wiederverwendung existiert
sehr wohl, aber entlang einer anderen Achse — **innerhalb thematischer Gruppen**. Die Runoff-Analyse
(TC-004-045/046/047) ist ein Bilderbuchfall: der erste Fall kostet ca. 5 Bindungen, die beiden
anderen je eine Szenario-Zeile. Dasselbe gilt für Ca/Mg (081/082), Foliar (049/050/051), die
WaterMix-Rechnungen und die Katalog-/Listen-Fälle. Die Reusability-These der ADR ist also nicht
falsch, sondern **falsch verankert**: Startpunkt einer Migration darf nicht der Referenzfall sein,
sondern muss die jeweils erste Fallgruppe sein.

| Kategorie | Anzahl | Anteil |
|---|---:|---:|
| **A** — Parametervariante bestehender Bindungen | **1** | 1 % |
| **B** — neue Bindungen, bekanntes Konzept | **30** | 33 % |
| **C** — neues Domänenkonzept | **41** | 45 % |
| **D** — für BDD ungeeignet | **20** | 22 % |
| **Summe** | **92** | 100 % |

Die einzige A-Zählung ist TC-004-092 selbst, also der bereits implementierte Referenzfall.
**A unter den verbleibenden 91 Fällen = 0.**

---

## 1. Messgrundlage

### 1.1 Das bestehende Step-Vokabular

Die vollständige heute existierende BDD-Sprache von REQ-004 (Stand `develop`):

| # | Typ | Steptext (parametrisiert) |
|---|---|---|
| 1 | Given | a plant whose care profile schedules watering tasks |
| 2 | Given | the plant has `<n>` watering tasks due |
| 3 | Given | the plant has `<n>` completed watering tasks |
| 4 | When | the gardener records a **plain** watering of `<n>` litres for the plant |
| 5 | Then | the tenant-wide watering log holds `<n>` waterings for the plant, dated `<day>` |
| 6 | Then | that watering is recorded as a **plain** watering, with no fertilizer involved |
| 7 | Then | that watering links back to the plant it was recorded for |
| 8 | Then | the plant's own watering log has gained `<n>` entries of `<n>` litres, dated `<day>` |
| 9 | Then | both watering logs agree on the day the plant was watered |
| 10 | Then | `<n>` watering tasks have been completed, dated `<day>` |
| 11 | Then | `<n>` follow-up watering tasks are due |
| 12 | Then | the task summary bar reports `<n>` more done tasks and as many active tasks as before |

**Befund am Rande (Zahlendrift in ADR-010):** ADR-010 §6 und die Konsequenzen-Sektion sprechen von
„**0 von 11** Bindungen bespoke, **9 von 11** wörtlich wiederverwendbar". Nachgezählt sind es
**12** Bindungen (3 `@given`, 1 `@when`, 8 `@then` in
`test_req004_watering_cross_view_consistency_bdd.py`), und das Szenario hat entsprechend 12 Schritte.
Fallspezifisch sind die beiden mit **plain** markierten (Nr. 4 und 6) — also **10 von 12**. Am
Verhältnis ändert das fast nichts (82 % → 83 %); an der Nachprüfbarkeit einer als „gemessen"
ausgewiesenen Zahl schon. Empfehlung: bei der ADR-Fortschreibung mitkorrigieren.

### 1.2 Was schon da ist (und die Kosten senkt)

Die Migrationskosten liegen **nur** in der Step-Schicht, nicht in der Page-Object-Schicht. Für große
Teile von REQ-004 existieren Page-Objects bereits und sind durch 100 klassische REQ-004-E2E-Tests
belegt eingefahren:

| Bereich | Page-Object | Vorhanden? |
|---|---|---|
| Düngemittel-Katalog + Detail | `fertilizer_list_page.py`, `fertilizer_detail_page.py` | ja (32 / 30 Methoden) |
| Nährstoffplan Liste + Detail | `nutrient_plan_list_page.py`, `nutrient_plan_detail_page.py` | ja (34 Methoden), inkl. Validierungs-Tab |
| Rechner, Flushing, Runoff, Mischsicherheit | `nutrient_calculations_page.py` | ja (32 Methoden), inkl. `fill_flushing`, `fill_runoff_analysis`, `fill_mixing_safety` |
| FeedingEvent-Liste + Dialog | `feeding_event_list_page.py` | ja (36 Methoden) |
| Gießprotokoll global + Detail | `watering_log_list_page.py`, `watering_log_detail_page.py` | ja |
| **Gantt-Diagramm** | — | **nein** |
| **Multi-Channel Delivery** | — | **nein** |

Die beiden Lücken sind die teuersten Bereiche — und ausgerechnet Gantt ist vollständig in Kategorie
D gelandet (siehe unten), müsste für eine BDD-Migration also gar nicht erst gebaut werden.

### 1.3 Klassifikationsregeln (damit die Einordnung nachprüfbar ist)

Damit „B" und „C" nicht Geschmackssache sind, gilt durchgängig:

- **A** — jeder Schritt des Falls ist mit einer der 12 Bindungen aus §1.1 formulierbar, nur mit
  anderen Parameterwerten. Keine einzige neue Bindung. Aufwand ≈ eine Szenario-Zeile.
- **B** — der Fall beschreibt eine **generische Anwendungsinteraktion** (Liste, Filter, Suche,
  Anlegen/Ändern/Löschen einer Entität über einen Dialog, Navigation, Zuordnung einer Beziehung,
  Export, Auth-Redirect). Neue Bindungen ja — aber jede ist die gleiche Mechanik gegen ein anderes
  Substantiv. Wer sie schreibt, muss die App kennen, nicht die Agronomie.
- **C** — die Aussage des Falls ruht auf einer **REQ-004-eigenen Fachregel oder Berechnung**
  (EC-/pH-Budget, Dosierungsableitung, Mischreihenfolge und Verträglichkeit, Wassermischverhältnisse,
  Flushing-Zeitpläne, Runoff-Diagnose, Vorratsreichweite, Foliar-Phasenregeln, Channel-Semantik,
  Plan-Validierung). Die Bindung muss ein Fachverhalten modellieren, nicht nur ein Feld ablesen.
- **D** — die Aussage ist **ausschließlich** Präsentation (Spalten-Sichtbarkeit, Farbe, Balken,
  gestrichelte Linie, Tooltip-Geometrie) **oder** eine Eingabe-Ablehnung durch eine reine
  Feldregel (Pflichtfeld, Wertebereich, Eindeutigkeit, Enum-Whitelist) ohne Zustandsänderung und
  ohne fachlich abgeleiteten Wert.

Die Trennlinie B/C ist damit: **Substantiv oder Regel?** Ein neues Substantiv (Entität, Feld, Liste)
ist B. Eine neue Regel (Schwelle, Sortierung, Ableitung, Berechnung) ist C.

---

## 2. Verteilung

| Kategorie | Anzahl | Szenarien, die daraus entstünden | neue Step-Bindungen (geschätzt) |
|---|---:|---:|---:|
| A — Parametervariante | 1 | 0 (bereits implementiert) | 0 |
| B — neue Steps, bekanntes Konzept | 30 | 30 | 30–35 (geteilt über alle 30) |
| C — neues Domänenkonzept | 41 | 41 | 60–70 (in 11 Konzeptgruppen) |
| D — für BDD ungeeignet | 20 | 0 | 0 |
| **Summe** | **92** | **71** | **90–105** |

---

## 3. Belege

### 3.1 Kategorie A — 1 Fall

- **TC-004-092** — der Referenzfall selbst. Er *ist* das Vokabular; jede andere Zahl und jeder
  andere Tag laufen ohne neue Bindung.

Für die Migrationsfrage zählt A **null**: es gibt keinen zweiten Fall im Dokument, der die
Watering-Log-↔-Task-Kopplung beschreibt. Der nächstliegende Kandidat, **TC-004-089**, verlangt bereits
ein vorher angelegtes Düngemittel und einen Gießvorgang **mit** Düngemittel/Kanal — Schritt 4 und 6
des Vokabulars sind auf den *reinen* Gießvorgang festgelegt, also wären neue Bindungen fällig. Er ist
damit B, nicht A. Das ist der engste Beinahe-Treffer im ganzen Dokument.

### 3.2 Kategorie B — 30 Fälle

Vollständig: 001, 002, 003, 004, 005, 006, 008, 009, 010, 012, 013, 014, 015, 017, 020, 024, 025,
027, 048, 052, 053, 054, 055, 057, 068, 084, 085, 089, 090, 091.

Belege:

- **TC-004-002 (Düngemittel-Filter nach Typ)** — „Nutzer wählt Filter-Chip Typ = Basis-Dünger, nur
  Typ `base` wird angezeigt, Chip erscheint, Anzahl sinkt." Das ist zeilenweise dieselbe Mechanik
  wie Bindung 5 des Vokabulars (Liste öffnen, filtern, Zeilen zählen, Zellwerte prüfen), nur gegen
  eine andere Entität. Eine parametrische Bindung
  `When the gardener filters <facet> by <value>` bedient 002, 003, 004, 013, 014, 053 gleichzeitig.
- **TC-004-024 (Nährstoffplan einer PlantInstance zuweisen)** — Beziehung setzen und im Tab
  wiederfinden. Kein Fachwissen im Steptext nötig: „the gardener assigns plan `<name>` to plant
  `<id>`" / „plant `<id>` follows plan `<name>`". Dieselbe Bindung trägt 025 (Wechsel) mit.
- **TC-004-084 (CRUD erfordert Authentifizierung)** — „Given the visitor is not signed in / When
  opening `<route>` / Then they land on the login page / Then after signing in they land back on
  `<route>`". Ein Lehrbuch-Given/When/Then, und die Bindungen sind über REQ-004 hinaus für jedes
  andere REQ nutzbar — der einzige B-Fall mit Wiederverwendung außerhalb von REQ-004.

Wichtig für die Schätzung: die 30 B-Fälle teilen sich **einen** Satz von rund 30–35 generischen
Bindungen (Liste/Filter/Suche/Dialog-CRUD/Beziehung/Auth/Export). Der erste B-Fall kostet 4–6
Bindungen, der zwanzigste im Schnitt weniger als eine.

### 3.3 Kategorie C — 41 Fälle

Vollständig: 011, 019, 021, 022, 023, 026, 028, 029, 030, 031, 032, 033, 034, 035, 036, 037, 038,
039, 040, 041, 042, 043, 044, 045, 046, 047, 049, 050, 051, 070, 071, 074, 075, 076, 077, 078, 079,
081, 082, 083, 088.

Belege:

- **TC-004-031 (Misch-Reihenfolge im Protokoll korrekt sortiert)** — die Aussage ist eine
  *Reihenfolge*, abgeleitet aus `mixing_priority` über mehrere Dünger, plus feste Rahmenschritte
  („Wasser vorbereiten", „pH-Korrektur", „Finale Messung"). Im Vokabular existiert nichts, das eine
  geordnete Schrittfolge behaupten könnte. Neue Bindung, neue Semantik.
- **TC-004-045 (Runoff-Analyse — Salzakkumulation)** — Input-EC 1.6 / Runoff-EC 2.8 → Status
  `SALT_BUILDUP`, Differenz +1.2 mS, Gesamtgesundheit `CRITICAL`, Handlungsempfehlung. Diagnose statt
  Anzeige: die Bindung muss Status-Enum, Differenz und Empfehlung als Fachbegriffe kennen.
- **TC-004-083 (Volles Praxisbeispiel — 50 L Nährlösung)** — Osmose-Anteil ≈ 75,5 %, 37,75 L RO +
  12,25 L Leitungswasser, CalMag-Defizit, Enddosierungen 6,79 / 4,52 / 2,26 ml/L bei erhaltenem
  Verhältnis 3:2:1, finale EC ≈ 1,80 mS, 8 Mischschritte. Der teuerste Einzelfall des Dokuments —
  er zieht aber nach: er nutzt fast das komplette Bindungsinventar der Gruppen 5 und 6 (§4).

Entscheidend ist die **Gruppenstruktur** von C, nicht die Zahl 41. Die 41 Fälle verteilen sich auf
11 Konzeptgruppen (§4); innerhalb einer Gruppe ist der zweite und dritte Fall so billig wie ein
A-Fall.

### 3.4 Kategorie D — 20 Fälle

Vollständig: 007, 016, 018, 056, 058, 059, 060, 061, 062, 063, 064, 065, 066, 067, 069, 072, 073,
080, 086, 087.

Belege:

- **TC-004-064 (Gantt-Lücken-Erkennung)** — „Woche 3 erscheint als leere Spalte mit grauem
  Hintergrund; die Lücke ist visuell klar von belegten Wochen unterscheidbar." Es gibt kein
  fachliches *When* — der Nutzer öffnet nur einen Tab —, und das *Then* ist eine Aussage über
  Hintergrundfarbe. Gherkin würde hier eine Prosa-Hülle um eine Pixelbehauptung legen. Die gesamte
  Gantt-Gruppe (061–067, **7 Fälle**) ist aus demselben Grund D.
- **TC-004-058 (Gießplan Intervall — Grenzwert 0 abgelehnt)** — Feld auf 0, Speichern, Fehlermeldung
  „Intervall muss mindestens 1 Tag betragen." Keine Zustandsänderung, kein abgeleiteter Wert, eine
  Bereichsregel auf einem Formularfeld. Ebenso 007, 016, 018, 056, 059, 072, 073.
- **TC-004-086 (Düngemittel-Liste auf Tablet — Spalten ausgeblendet)** — reine
  Viewport-abhängige Sichtbarkeit. Das klassische Muster (Fenstergröße setzen, Spaltenköpfe lesen)
  ist kürzer und ehrlicher als jedes Szenario.

**Nicht** in D gelandet, obwohl es auf den ersten Blick ähnlich aussieht: **TC-004-070**
(Tank-Safe-Ablehnung im Fertigation-Channel). Auslöser ist kein Feldconstraint, sondern ein
Datenattribut einer *anderen* Entität (`fertilizer.tank_safe = false`) mit agronomischer Begründung
(Tropfer verstopfen, Biofilm) — das ist eine Fachregel und damit C. Diese Grenze trennt 070/071/074
(C) sauber von 072/073 (D) innerhalb derselben Spec-Gruppe.

---

## 4. Konzeptgruppen in C — welche Bindungen geteilt würden

Diese Tabelle ist der eigentliche Planungswert des Dokuments: sie macht sichtbar, welches Vokabular
geteilt wird, statt es pro Fall neu zu erfinden.

| # | Konzept | Fälle | Anz. | neue Bindungen (geschätzt) | Kernvokabular |
|---|---|---|---:|---:|---|
| 1 | Vorratsreichweite / Lagerbestand | 011 | 1 | 4 | `Given the fertilizer has <n> ml in stock` · `Given an average consumption of <n> ml per week` · `Then the catalog flags it as low on stock` · `Then the detail page warns the supply lasts less than <n> weeks` |
| 2 | Dosierungszuweisung & Mischreihenfolge im Plan | 019, 026 | 2 | 5 | `Given phase <name> uses <fertilizer> at <n> ml/L with mixing priority <n>` · `Then the phase lists its fertilizers in mixing order` · `Then the current dosages for the plant are <table>` |
| 3 | Plan-Validierung & Klon | 021, 022, 023 | 3 | 6 | `When the gardener validates the plan` · `Then the validation reports the missing mandatory phases <list>` · `Then the validation reports an EC-budget deviation of <n> mS` · `Then the clone carries version 1 and the same phase entries` |
| 4 | Nährlösungs-Berechnung & Mischprotokoll | 028–033 | 6 | 9 | `Given a target volume of <n> L at <n> mS and pH <n>, from base water of <n> mS` · `When the gardener calculates the mix` · `Then the mixing protocol lists <table> in order` · `Then a <severity> incompatibility between <a> and <b> is flagged` · `Then the dose of <fertilizer> is capped at <n> ml/L` |
| 5 | Wassermischung & EC-Budget (WaterMix, EC@25, Ca/Mg) | 034–037, 076–079, 081–083 | 11 | 12 | `Given a site whose tap water has <n> mS, <n> ppm Ca, <n> ppm Mg, <n> ppm chlorine` · `Given the site has no RO system` · `When the gardener sets the RO share to <n> %` · `Then the recommended RO share is <n> %` · `Then the mixed water measures <n> mS` · `Then a <kind> warning appears` · `Then the CalMag deficit is <n> ppm` · `Then the target is reported physically unreachable` · `Then the EC normalised to 25 °C is <n> mS` |
| 6 | NED-Dosierungsrechner (Referenzdosierung, Skalierung, Quelle) | 038–042 | 5 | 7 | `Given the plan's reference dosages are <table>` · `When the gardener opens the dosage calculator for site <name>` · `Then the calculated dosages keep the reference ratio` · `Then each dosage states its source` · `Then the reference dosages stay unchanged with a hint to add a water profile` |
| 7 | Flushing-Protokoll | 043, 044 | 2 | 5 | `Given the plant is <n> days from harvest on <substrate> at <n> mS` · `When the gardener opens the flushing protocol` · `Then the flush plan spans <n> days in the stages <table>` · `Then the protocol reports it is too late` |
| 8 | Runoff-Analyse | 045, 046, 047 | 3 | 5 | `When the gardener analyses a runoff of <n> mS from an input of <n> mS` · `When the gardener analyses <n> L of runoff from <n> L applied` · `Then the EC status is <status>` · `Then the runoff share is <n> %` · `Then the overall health is <status>` |
| 9 | Foliar-Warnung nach Phase/Woche | 049, 050, 051 | 3 | 6 | `Given the plant is in flowering week <n>` · `Given the feeding event is linked to an emergency treatment` · `When the gardener picks the foliar application method` · `Then a <severity> foliar notice appears` · `Then no foliar warning appears` · `Then the feeding event stays savable` |
| 10 | Multi-Channel-Delivery-Regeln | 070, 071, 074, 075 | 4 | 8 | `Given the phase entry has a <method> channel` · `When the gardener adds <fertilizer> to the channel` · `Then the channel rejects it as not tank-safe` · `Then a foliar EC warning appears` · `Then validation warns <fertilizer> is used in <n> channels` · `When the gardener converts the phase entry to multi-channel` · `Then a synthetic drench channel carries the legacy fertilizers` |
| 11 | Organische Freiland-Empfehlung nach Zehrerklasse | 088 | 1 | 5 | `Given a <demand-level> plant in <substrate>` · `Given the gardener's expertise level is <level>` · `Then the EC/pH mixing logic is hidden` · `Then the recommendation lists <table>` |
| | **Summe** | | **41** | **72 brutto / ~60–70 netto** | Gruppen 5 und 6 teilen die Site-/Wasserprofil-`Given`s; die Warn-`Then`s der Gruppen 4, 5, 6, 9, 10 lassen sich auf eine gemeinsame parametrische Form `Then a <severity> notice reads <text>` bringen. |

Ablesbar an dieser Tabelle: **Gruppe 5 ist mit 11 Fällen die lohnendste Einstiegsgruppe**
(12 Bindungen für 11 Szenarien ≈ 1,1 pro Fall), **Gruppen 1 und 11 sind die unwirtschaftlichsten**
(4 bzw. 5 Bindungen für je einen einzigen Fall).

---

## 5. Aufwand — in Szenarien und Bindungen

Bewusst **nicht** in Personentagen. Eine PT-Zahl bräuchte eine gemessene Durchsatzrate
(Bindungen/Tag) aus mehr als einem PoC-Fall; die gibt es nicht (siehe Lücke L3).

**Vollmigration A+B+C (D bleibt klassisch):**

- **71 Szenarien** (1 davon existiert bereits → 70 neu)
- **90–105 neue Step-Bindungen** zusätzlich zu den 12 bestehenden
- **2 fehlende Page-Object-Familien** — Multi-Channel-Delivery (für 068, 070–075) sowie ein
  CSV-Download-Helfer (054). Gantt bräuchte keines, weil vollständig D.
- **20 Fälle bleiben unangetastet** in der klassischen Suite.

**Verteilung des Aufwands über die Zeit** — das ist der planungsrelevante Teil:

| Migrationsphase | Fälle | neue Bindungen | Bindungen je Fall |
|---|---:|---:|---:|
| Erster Fall je Konzeptgruppe (11 Gruppen in C) | 11 | ~45 | 4,1 |
| Erster Satz generischer B-Bindungen | ~6 | ~25 | 4,2 |
| Alle übrigen C-Fälle | 30 | ~20 | 0,7 |
| Alle übrigen B-Fälle | 24 | ~8 | 0,3 |

Rund **70 % der Bindungen entstehen in den ersten ~17 Fällen**, also in weniger als einem Viertel des
Umfangs. Eine schrittweise Migration entlang neuer/geänderter Testfälle — genau der Weg, den ADR-010
beschlossen hat — zahlt erst ab dem zweiten Fall einer Gruppe ein. Wer eine Gruppe anfasst, sollte
sie deshalb ganz nehmen; wer einen Einzelfall aus einer neuen Gruppe migriert, zahlt den vollen
Gruppenpreis für einen einzigen Fall.

**Zum Vergleich der Grundgesamtheit:** die klassische REQ-004-Suite umfasst heute 100 E2E-Tests in
8 Modulen. Die Abbildung Test↔TC-ID ist wegen der in ADR-010 §1 dokumentierten Docstring-Drift
(zwei parallele ID-Schemata: `TC-004-NNN` und `TC-REQ-004-NNN`) **nicht** verlässlich fallgenau
auflösbar — siehe Lücke L1.

---

## 6. Trägt die ADR-010-Annahme?

**Nein — die Annahme in der vorliegenden Form ist widerlegt.**

ADR-010 §6 formuliert: *„Unter der Annahme, dass ein substanzieller Teil der übrigen Fälle Varianten
desselben Musters sind (andere Mengen, andere Anwendungsmethode, andere Ausgangszustände der
Gießprotokolle) — eine Annahme, keine Messung —, deckt der bestehende Wortschatz […] einen
erheblichen Anteil ohne neue Bindungen ab."*

Gemessen:

1. **Der Anteil ist 0 von 91, nicht „substanziell".** Kein anderer REQ-004-Testfall variiert
   TC-004-092. Die Watering-Log-↔-Aufgaben-Kopplung kommt im gesamten TC-Dokument genau einmal vor.
2. **Der bestehende Wortschatz deckt außerhalb seines Falls nichts ab.** Alle 12 Bindungen sind an
   Gießprotokoll, Gießaufgaben und Pflanzen-Detailtabs gebunden. Die drei größten Themenblöcke von
   REQ-004 — Nährstoffplanung, EC-Budget-/Wasserrechnung, Multi-Channel-Delivery — teilen mit ihnen
   kein einziges Substantiv.
3. **Die 9-von-11-Kennzahl wurde auf die falsche Achse projiziert.** Sie misst, dass *derselbe* Fall
   mit anderen Zahlen und Tagen ohne neue Bindung läuft. Das ist wahr und wertvoll — es ist der
   Unterschied zwischen einer Bindung, die man für Fall 2 wegwerfen muss, und einer, die bleibt. Es
   sagt aber nichts über einen *anderen* Fall aus. Genau diesen Sprung hat die ADR gemacht, und
   genau ihn hat sie korrekterweise als Annahme gekennzeichnet.

**Was von der These trägt:** die Wiederverwendungs-Mechanik selbst. Sie greift, sobald man sie
gruppenweise misst: 41 C-Fälle brauchen nur ~60–70 Bindungen (1,6 je Fall), 30 B-Fälle nur ~30–35
(1,1 je Fall), und innerhalb einer Gruppe fällt der Grenzpreis auf 0–1 Bindung. Der Referenzfall war
für diese Aussage schlicht das falsche Fundament — er ist ein Einzelstück, kein Prototyp einer
Familie.

**Folge für die ADR:** §6 („Migrationspfad") und der zugehörige Konsequenzen-Punkt sollten
fortgeschrieben werden (Amend, nicht Supersede — die Entscheidung selbst bleibt richtig): die
Hochrechnung auf ~90 Fälle ist zu streichen und durch die Gruppenverteilung dieses Dokuments zu
ersetzen. Der No-Go gegen eine pauschale Migration wird durch die Messung **gestärkt**, nicht
geschwächt.

---

## 7. Empfehlung

**Keine Vollmigration von REQ-004. Migration nur gruppenweise, und nur anlassbezogen.**

1. **Nicht migrieren: die 20 D-Fälle.** Sie sind im klassischen Muster kürzer und aussagekräftiger.
   Besonders die Gantt-Gruppe (061–067): 7 Fälle, deren Aussagen Farben, Balken und Tooltip-Inhalte
   sind. Ein Gherkin-Szenario darüber wäre Prosa ohne Erkenntnisgewinn — und würde nebenbei ein
   Gantt-Page-Object erzwingen, das heute niemand braucht.
2. **Nicht migrieren, solange kein fachlicher Anlass besteht: die 30 B-Fälle.** Sie laufen heute
   klassisch, sind billig zu warten, und ihr BDD-Mehrwert (Lesbarkeit für Nicht-Techniker) ist bei
   „Filter anwenden, Zeilen zählen" gering. Ausnahme: **084/085** (Auth, Tenant-Scope) — deren
   Bindungen wären REQ-übergreifend wiederverwendbar; wenn irgendwo generische BDD-Bindungen
   entstehen sollen, dann hier.
3. **Migrieren, wenn eine Gruppe ohnehin angefasst wird: C-Gruppen mit ≥ 3 Fällen** — konkret
   Gruppe 5 (11 Fälle), Gruppe 4 (6), Gruppe 6 (5), Gruppe 10 (4), sowie 3, 8, 9 (je 3). Dort ist
   das Verhältnis Bindungen:Szenarien ≤ 1,7, und die Fachregeln (EC-Schwellen, Mischreihenfolge,
   Foliar-Fenster, Ca/Mg-Bänder) sind genau die Aussagen, bei denen ein Gärtner den Testfall
   gegenlesen können sollte. Das ist der Ort, an dem BDD in diesem Projekt tatsächlich zahlt.
4. **Nie einzeln migrieren: C-Gruppen mit 1–2 Fällen** (1, 2, 7, 11). 4–5 Bindungen für einen
   einzigen Fall — dafür ist der klassische Test das ehrlichere Werkzeug.
5. **Reihenfolge, falls ein Roadmap-Item entsteht:** Gruppe 8 (Runoff) zuerst als kleinster
   vollständiger Gruppenbeweis (3 Fälle, ~5 Bindungen, Page-Object existiert bereits), danach
   Gruppe 5. Damit wird die Gruppen-These an einer echten Gruppe verifiziert, bevor der teuerste
   Block angefasst wird — dieselbe Vorsicht, die ADR-010 beim Einzelfall walten ließ.

---

## 8. Lücken — was diese Messung nicht leisten kann

- **L1 — Automatisierungsstand pro Testfall nicht auflösbar.** Die klassische REQ-004-Suite hat
  100 Tests, aber zwei parallele ID-Schemata (`TC-004-NNN` in den Spec-Überschriften,
  `TC-REQ-004-NNN` in vielen Docstrings), deren Nummern **nicht** aufeinander abbildbar sind
  (dokumentiert in ADR-010 §1 und `tests/e2e/README.md`). Die Aussage „Fall X ist bereits
  klassisch automatisiert" ist deshalb pro Fall nicht belastbar. Für die Triage ist das folgenlos —
  klassifiziert wurde der **Testfall**, nicht sein Automatisierungsstand —, für eine
  Migrationsreihenfolge wäre es zu klären.
- **L2 — Bindungszahlen je Gruppe sind Konstruktionsschätzungen, keine Messungen.** Sie entstanden
  durch Entwurf des Steptexts je Fall (§4) und Zusammenlegen gleichlautender Schritte, nicht durch
  Implementierung. Erfahrungswert aus TC-004-092: der Entwurf lag dort bei 9 Schritten, implementiert
  wurden 12 — ein Aufschlag von rund 30 %. Die Spannen in §5 tragen diesen Aufschlag bereits, aber
  eine Abweichung nach oben um denselben Faktor ist nicht ausgeschlossen.
- **L3 — Keine Personentage.** Es existiert genau **ein** implementierter BDD-Fall. Aus n = 1 lässt
  sich keine Durchsatzrate ableiten, und die vier Integrations-Hazards aus ADR-010 §3 sind
  Einmalkosten, die die Messung an TC-004-092 zusätzlich verzerren. Eine PT-Zahl wäre hier eine
  erfundene Zahl. Frühestens nach der ersten vollständig migrierten Gruppe (Empfehlung 5) ist sie
  begründbar.
- **L4 — Grenzfälle B/C und C/D.** Die Regel aus §1.3 entscheidet jeden Fall eindeutig, aber bei
  fünf Fällen liegt die Entscheidung nahe an der Linie und ist im Text begründet: 017
  (Phase-Entry-CRUD → B, obwohl EC/pH/NPK-Felder trägt), 023 (Klon → C wegen der
  Deep-Copy-Gleichheitsaussage), 041 (Quell-Feld → C wegen der NED-Ableitung, obwohl die
  Unterscheidung teils über Farbe erfolgt), 060 (Fertigation im Plan-Gießplan → D als
  Enum-Whitelist, obwohl fachlich als REQ-014-Abgrenzung begründet), 069 (Channel-Bereich für
  Beginner ausgeblendet → D als reine Sichtbarkeit, obwohl von der Erfahrungsstufe abgeleitet).
  Selbst wenn alle fünf kippten, änderte sich die Kernaussage in §6 nicht — A bliebe 0.
- **L5 — Zahlendrift in ADR-010 (§1.1).** „11 Bindungen" gegen 12 tatsächliche. Bei der
  ADR-Fortschreibung mitzukorrigieren.

---

## Referenzen

- Issue #774 — `chore(e2e): triage the REQ-004 test cases for BDD migration effort (ADR-010 follow-up)`
- `docs/de/adr/010-bdd-e2e-architektur-pytest-bdd.md` — §6 Migrationspfad (die geprüfte Annahme)
- `spec/e2e-testcases/TC-REQ-004.md` — die 92 klassifizierten Testfälle
- `tests/e2e/features/watering_cross_view_consistency.feature` — das Referenzszenario
- `tests/e2e/test_req004_watering_cross_view_consistency_bdd.py` — die 12 Referenz-Bindungen
- `tests/e2e/README.md` — Selektionsachsen, Tag-Schema, dokumentierte TC-ID-Drift
- `scripts/check_bdd_traceability.py` — maschineller Spec-↔-Test-Abgleich

---

## Anhang — Klassifikation aller 92 Testfälle

| TC | Titel (gekürzt) | Kat. | Begründung |
|---|---|:--:|---|
| 004-001 | Düngemittel-Liste aufrufen | B | Listenmechanik gegen andere Entität |
| 004-002 | Filter nach Typ | B | Filtermechanik, nur anderer Wert |
| 004-003 | Filter nach Tank-Sicherheit | B | Filtermechanik; `tank_safe` nur als Wert |
| 004-004 | Filter kombinieren (AND) | B | Filtermechanik |
| 004-005 | Filter zurücksetzen | B | Filtermechanik |
| 004-006 | Düngemittel erstellen — Happy Path | B | Dialog-CRUD |
| 004-007 | Erstellen — Pflichtfeld-Validierung | D | Feldconstraint, keine Zustandsänderung |
| 004-008 | Detail — Planverwendung (Reverse Lookup) | B | Beziehungsliste + Link |
| 004-009 | Detail — kein Plan zugeordnet | B | Leerzustand derselben Beziehung |
| 004-010 | Lagerbestand erfassen | B | Entitäts-CRUD über Dialog |
| 004-011 | Niedrigbestand-Warnung | C | Regel: Reichweite < 2 Wochen aus Verbrauch |
| 004-012 | Nährstoffplan-Liste | B | Listenmechanik |
| 004-013 | Filter nach Substrattyp | B | Filtermechanik |
| 004-014 | Filter nach Tags | B | Filtermechanik |
| 004-015 | Plan erstellen — Happy Path | B | Dialog-CRUD |
| 004-016 | Plan erstellen — Name leer | D | Feldconstraint |
| 004-017 | Phase-Entry hinzufügen | B | Dialog-CRUD, Feld-Rundlauf (Grenzfall, L4) |
| 004-018 | week_end < week_start abgelehnt | D | Feldconstraint |
| 004-019 | Dünger einer Phase-Entry zuweisen | C | Regel: Sortierung nach `mixing_priority` |
| 004-020 | Dünger-Dosierung löschen | B | CRUD-Löschung |
| 004-021 | Plan-Vollständigkeit — Pflichtphasen | C | Validator-Regel |
| 004-022 | EC-Budget-Validierung (±0.3 mS) | C | Berechnung + Toleranzregel |
| 004-023 | Plan klonen (Deep Copy) | C | Regel: Versionsreset + Struktur-Gleichheit (Grenzfall, L4) |
| 004-024 | Plan einer PlantInstance zuweisen | B | Beziehung setzen |
| 004-025 | Plan-Zuweisung wechseln | B | Beziehung ersetzen |
| 004-026 | Aktuelle Dosierungen ableiten | C | Ableitung aus Plan + Phase, sortiert |
| 004-027 | Plan löschen | B | CRUD-Löschung mit Bestätigung |
| 004-028 | Berechnungsseite — Formular + Protokoll | C | EC-Budget-Berechnung |
| 004-029 | Basis-EC > Ziel-EC — Warnung | C | Fachregel |
| 004-030 | EC-Obergrenze überschritten | C | Fachregel je Substrat/Phase |
| 004-031 | Misch-Reihenfolge sortiert | C | Regel: geordnete Schrittfolge |
| 004-032 | Inkompatibilitätswarnung | C | Regel: Verträglichkeit + Schweregrad |
| 004-033 | Einzeldünger-Sicherheitslimit | C | Regel: max ml/L, Kappung |
| 004-034 | Mischverhältnis-Empfehlung | C | RO-Anteil, Headroom, Alternativen |
| 004-035 | Kein Osmose-System | C | Regel-Verzweigung Basis-EC = Leitungswasser |
| 004-036 | Chlorwarnung | C | Schwellenregel 0.5 ppm |
| 004-037 | CalMag-Empfehlung | C | Defizitberechnung |
| 004-038 | Dosierungsrechner — mit Wasserprofil | C | NED-Skalierung + EC-Budget-Visualisierung |
| 004-039 | Kein Wasserprofil (Fallback) | C | Regel NED-08 |
| 004-040 | Proportionserhaltung bei Skalierung | C | Regel NED-07 |
| 004-041 | `source`-Feld sichtbar | C | NED-Herkunftsableitung (Grenzfall, L4) |
| 004-042 | RO ≥ 80 % — pH-Puffer-Warnung | C | Schwellenregel NED-09 |
| 004-043 | Flushing-Protokoll — Coco | C | Zeitplanableitung aus Substrat + Resttagen |
| 004-044 | Flushing zu spät — TOO_LATE | C | Regel: Mindestdauer je Substrat |
| 004-045 | Runoff — SALT_BUILDUP | C | Diagnoseregel |
| 004-046 | Runoff-Prozentsatz zu niedrig | C | Diagnoseregel (Gruppenvariante zu 045) |
| 004-047 | Runoff — optimaler Bereich | C | Diagnoseregel (Gruppenvariante zu 045) |
| 004-048 | Feeding-Event erfassen | B | Dialog-CRUD |
| 004-049 | Foliar-Warnung Blüte ab Woche 2 | C | Phasen-/Wochenregel |
| 004-050 | Foliar Blüte Woche 1 — nur INFO | C | dieselbe Regel, andere Schwelle |
| 004-051 | Foliar-Warnung bei IPM-Notfall unterdrückt | C | Ausnahmeregel über Behandlungsbezug |
| 004-052 | FeedingEvent — Zeitraum-Filter | B | Filtermechanik + URL-Persistenz |
| 004-053 | FeedingEvent — Run-Filter | B | Filtermechanik |
| 004-054 | FeedingEvent — CSV-Export | B | Export-Mechanik (Download-Helfer nötig) |
| 004-055 | Gießplan Wochentage-Modus erstellen | B | Formular-Rundlauf |
| 004-056 | Wochentage — Duplikat abgelehnt | D | Eindeutigkeits-Constraint |
| 004-057 | Gießplan Intervall-Modus erstellen | B | Formular-Rundlauf |
| 004-058 | Intervall 0 abgelehnt | D | Bereichs-Constraint |
| 004-059 | Intervall 90 ok / 91 abgelehnt | D | Bereichs-Constraint (Grenzwert) |
| 004-060 | Fertigation im Plan-Gießplan abgelehnt | D | Enum-Whitelist (Grenzfall, L4) |
| 004-061 | Gantt-Tab öffnen | D | Diagramm-Rendering (Achse, Balkenfarben) |
| 004-062 | Gantt-Dünger-Zeilen + Beschriftung | D | Diagramm-Rendering |
| 004-063 | Gantt-Hover-Tooltip | D | Tooltip-Rendering |
| 004-064 | Gantt-Lücken-Erkennung | D | Rendering (graue Spalte) |
| 004-065 | Gantt-Überlappung — Warnung | D | Rendering (roter Rahmen/Stapelung) |
| 004-066 | Gantt-Modus A — einjährig | D | Rendering (linearer Zeitstrahl) |
| 004-067 | Gantt-Modus B — saisonaler Zyklus | D | Rendering (gestrichelte Linie, ↻) |
| 004-068 | Channel hinzufügen — Fertigation | B | Wizard-CRUD einer Entität (Page-Object fehlt) |
| 004-069 | Channel für Beginner ausgeblendet | D | reine Sichtbarkeit (Grenzfall, L4) |
| 004-070 | Tank-Safe-Validierung (MCD-V01) | C | Fachregel über Fremdattribut |
| 004-071 | Foliar EC-Limit > 1.0 mS (MCD-V04) | C | Fachschwelle, speicherbar |
| 004-072 | Channel-ID Duplikat (MCD-V08) | D | Eindeutigkeits-Constraint |
| 004-073 | Maximum 10 Channels (MCD-V12) | D | Kardinalitäts-Constraint |
| 004-074 | Cross-Channel Dünger-Duplikat (MCD-V20) | C | kanalübergreifende Ableitung |
| 004-075 | Legacy → Multi-Channel konvertieren | C | Migrationssemantik (synthetischer Channel) |
| 004-076 | Wassermischung — Vorwärtsrechnung | C | Formel EC_mix |
| 004-077 | Osmose-Anteil — Rückwärtsrechnung | C | Umkehrformel |
| 004-078 | Osmose-Ziel unerreichbar | C | physikalische Randbedingung |
| 004-079 | Temperaturkorrektur EC@25 | C | Normierungsberechnung |
| 004-080 | EC@25 — kein Temperaturwert (Hinweis) | D | Hinweistext ohne abgeleiteten Wert |
| 004-081 | Ca/Mg-Verhältnis zu niedrig | C | Bandregel < 2.0 |
| 004-082 | Ca/Mg-Verhältnis zu hoch | C | Bandregel > 5.0 |
| 004-083 | Volles Praxisbeispiel — 50 L | C | vollständige 3-Stufen-Pipeline |
| 004-084 | Düngemittel-CRUD erfordert Auth | B | Auth-Redirect-Mechanik (REQ-übergreifend nutzbar) |
| 004-085 | Plan nur im eigenen Tenant sichtbar | B | Tenant-Scoping der Liste |
| 004-086 | Düngemittel-Liste auf Tablet | D | Viewport-abhängige Spalten-Sichtbarkeit |
| 004-087 | FeedingEvent-Liste auf Tablet | D | Viewport-abhängige Spalten-Sichtbarkeit |
| 004-088 | Organische Düngung Freiland | C | Ableitung aus Zehrerklasse + Erfahrungsstufe |
| 004-089 | Journey — Gießvorgang protokollieren | B | Gießvorgang **mit** Düngemittel/Kanal → neue Bindungen |
| 004-090 | Journey — Gießprotokoll-Detail | B | Detailansicht + „zuletzt gegossen" |
| 004-091 | Journey — FeedingEvent erfassen | B | Dialog-CRUD (Doppelung zu 048) |
| 004-092 | Journey — Cross-View-Konsistenz | **A** | **Referenzfall — ist das Vokabular** |
