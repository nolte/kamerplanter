# ADR-010: BDD-Architektur für die E2E-Suite (pytest-bdd, TC-004-092 als Proof-of-Concept)

**Status:** Akzeptiert
**Datum:** 2026-07-25
**Entscheider:** Kamerplanter Development Team

## Kontext

Issue #761 stellte die Frage, ob die bestehende, rein Selenium-/Page-Object-basierte E2E-Suite (`tests/e2e/`, 722 Tests) durch eine Gherkin/BDD-Schicht ergänzt oder ersetzt werden soll, in der Testfälle direkt aus den TC-Dokumenten (`spec/e2e-testcases/`) ableitbar sind. Der Auftrag verlangte **keine** Meinung, sondern einen belastbaren Proof-of-Concept an genau einem Testfall — TC-004-092, „Ein Gießvorgang erscheint konsistent in globalem Gießprotokoll, Instanz-Gießprotokoll und Aufgabenverlauf" — plus eine Go/No-Go-Empfehlung, bewertet gegen sechs benannte Kriterien: Spec-↔-Test-Traceability, Authoring-Ergonomie, Integrationskosten, Reproduzierbarkeit, Reporting und Migrationspfad.

Die Randbedingung für alle Alternativen: kein zweiter Test-Runner. Die bestehende Suite kennt Fixtures, `pytest.ini`, zwei orthogonale Selektionsachsen (`req<NNN>` aus dem Dateinamen, `FEATURES` als Modul-Tupel), `--strict-markers`, `xdist`-Parallelität (`-n 4 --dist=loadfile`), JUnit-XML mit einer `tc_id`-Property und ein Markdown-Protokoll (`protokoll.md`) als menschenlesbaren Audit-Trail (NFR-008 §4.4). Jede BDD-Lösung musste sich dort einfügen, nicht danebenstellen.

Das Portfolio hat die Framework-Frage bereits vorentschieden: `spec/project/behavior-driven-development/` (im geteilten `claude-shared`-Repository) benennt Gherkin und die Cucumber-Familie als illustratives Referenzprofil. Die PoC hatte diese Vorentscheidung zu belegen, nicht neu zu eröffnen.

Der klassische Test `test_req004_watering_cross_view_consistency.py` (aus PR #763, Schwester-Issue #760) diente als Vergleichsbasis und blieb während der gesamten PoC unverändert bestehen — ein Ersetzen vor dem Go/No-Go hätte die PoC ihres Zwecks beraubt.

## Entscheidung

Wir führen **pytest-bdd** als BDD-Schicht **über** der bestehenden Selenium/Page-Object-Suite ein, mit Gherkin-Szenarien unter `tests/e2e/features/*.feature` und Step-Bindungen in eigenen `test_req<NNN>_*_bdd.py`-Modulen, die ausschließlich über die vorhandenen Page-Objects auf den Browser zugreifen.

**Go, qualifiziert** — nicht als pauschale Migration aller ~90 REQ-004-Testfälle, sondern:

1. **Go** für neu zu schreibende E2E-Testfälle, deren Verhalten sich in einem einzigen, deklarativen Szenario mit klaren Given/When/Then-Grenzen fassen lässt (typischerweise: ein Nutzer-Workflow, eine Konsistenzaussage über mehrere Views).
2. **Go** für die maschinelle Traceability-Prüfung (`scripts/check_bdd_traceability.py`) als eigenständiges, wiederverwendbares Werkzeug — unabhängig vom BDD-Anteil der Suite.
3. **No-Go** für eine pauschale, kurzfristige Migration der bestehenden 722 klassischen Tests. Die Integrationskosten (vier vorab unentdeckte Defekte, siehe unten) und der gemessene Wiederverwendungs-Ertrag rechtfertigen eine geplante, schrittweise Migration entlang neuer/geänderter Testfälle, kein Big-Bang.
4. **No-Go** für `behave` oder einen zweiten Test-Runner (siehe Abwägung unten).

Der bestehende klassische Test bleibt bestehen; beide Implementierungen von TC-004-092 laufen dauerhaft parallel als Doppelnutzungsnachweis für die geteilten Page-Objects.

## Begründung

### 1. Spec-↔-Test-Traceability

Jedes BDD-Szenario trägt einen `@TC-<REQ>-<NNN>`-Tag (hier `@TC-004-092`), der über den JUnit-`tc_id`-`user_property`-Kanal und die `protokoll.md`-Zeile bis in den Report durchgereicht wird. `scripts/check_bdd_traceability.py` verifiziert diese Bindung **maschinell und in beiden Richtungen**: ein Tag, der auf keine `## TC-<id>: <Titel>`-Überschrift unter `spec/e2e-testcases/` trifft, ist ein Fehler (`orphan tag`); ein Szenario ohne Tag ebenso (`untagged scenario`). Die Rückrichtung — ein deklarierter Testfall ohne Szenario — ist bewusst **kein** Fehler, sondern eine informative Zählung: Automatisierungs-Abdeckung wächst über Zeit.

Der ehrliche Befund dazu: Der Check wurde bewusst **nicht** auf die docstring-basierten TC-IDs der klassischen Tests ausgeweitet (`TC-REQ-004-W001`-Form). `tests/e2e/README.md` dokumentiert offen, dass diese Test-deklarierten IDs bereits heute von den Spec-IDs (`TC-004-NNN`) abgedriftet sind — eine Ausweitung des Checks würde sofort eine Masse an Bestandsbefunden melden, nicht weil BDD etwas kaputt macht, sondern weil die Drift schon vorher da war. Das ist genau das Argument **für** die BDD-Traceability, nicht dagegen: der Tag-Mechanismus verhindert, dass dieselbe Drift für neue Szenarien erneut entsteht, weil sie durch einen aktiven Gate erzwungen wird, statt sich auf Docstring-Disziplin zu verlassen.

### 2. Authoring-Ergonomie

Die Gherkin-Sprache ist Englisch — eine operative Entscheidung (2026-07-24), begründet mit NFR-003 (Quellcode ist Englisch) und der Lesbarkeit im gesamten, mehrsprachig arbeitenden Portfolio. Für deutschsprachige, nicht-technische Mitwirkende ist das ein realer Mehraufwand: ein Gärtner, der einen Testfall aus `spec/e2e-testcases/TC-REQ-004.md` (Deutsch) prüfen will, muss die englische `.feature`-Datei lesen — die Brücke zwischen beiden ist ausschließlich der `@TC-004-092`-Tag, keine Übersetzung. Das ist ein bewusster Kompromiss, kein Nebeneffekt.

Dass Sprache allein keine Garantie für saubere Fachsprache ist, zeigt der beratende Lektorat-Durchlauf über das Szenario (P2): 0 kritische Befunde, aber eine echte Vokabular-Drift zwischen „care task" und „watering task" im ersten Entwurf — ein Fehler, den eine reine Code-Review (Diff-Betrachtung von Python-Assertions) nicht gefangen hätte, weil er in Prosa steckt, nicht in Logik. Alle vier Befunde (1 Warning, 3 Suggestions) wurden übernommen.

Die Schrittvokabular ist inzwischen vollständig parametrisiert (siehe Migrationspfad unten): Zahlen und Tage sind reguläre Ausdrücke, keine literalen Werte im Steptext. Das senkt die Ergonomie-Hürde für das *Lesen* eines Szenarios weiter — ein Leser ohne Selenium-Kenntnis kann `Given the plant has 1 watering task due` verstehen und für einen abweichenden Fall (`3 watering tasks due`) unverändert wiederverwenden, ohne eine neue Bindung zu schreiben.

### 3. Integrationskosten

Dies ist der schwerste Befund der PoC und wird hier bewusst nicht kleingeredet: **vier eigenständige Defekte** mussten behoben werden, bevor ein einziges Szenario laufen konnte — alle im Auditprotokoll (`.audits/issue-orchestrate/761/analysis.md`) empirisch belegt.

- **Hazard A** — `pytest-bdd` übersetzt jeden Gherkin-Tag ungeprüft in einen pytest-Marker (`getattr(pytest.mark, tag)`, ohne Auto-Registrierung). Unter `--strict-markers` erzeugt ein einziger unregistrierter Tag **keinen** fehlschlagenden Einzeltest, sondern einen **Collection-Fehler, der den gesamten Lauf mit Exit-Code 2 abbricht** — alle 722 bestehenden Tests liefen dann überhaupt nicht. Beobachtet: `Failed: 'TC-004-092' not found in markers configuration option`.
- **Hazard B** — `pytest-bdd` überschreibt `scenario_wrapper.__doc__` bedingungslos mit `"<feature>: <scenario>"`, ohne `functools.wraps`. Der Docstring-Kanal, über den die klassischen Tests ihre TC-ID an JUnit und `protokoll.md` liefern, ist damit für BDD-Szenarien strukturell tot.
- **Hazard C** — unbeauftragt entdeckt, sicherheitskritisch für die Akzeptanzkriterien: `item.location[0]` zeigt für ein pytest-bdd-Szenario in die site-packages statt auf das aufrufende Modul. Die REQ-Achse, die `conftest.py` daraus ableitet, griff dadurch **still ins Leere** — `-m watering` fand das Szenario, `-m req004` **nicht**, ohne jede Fehlermeldung. Ein Akzeptanzkriterium wäre unbemerkt verfehlt worden.
- **Toter Hook** — ein `pytest_bdd_after_step`-Hook, im Step-Modul (`test_*.py`) selbst definiert, wird von pytests Plugin-Manager nie registriert und feuert nie; er muss in `conftest.py` stehen, wo pytest automatisch registrierte Plugins sucht.

Dazu ein Nebenbefund, der die Reporting-Bewertung berührt: Die TC-ID muss unter `-n 4 --dist=loadfile` explizit über `checkpoint.jsonl` an den xdist-Controller durchgereicht werden — ohne das wäre sie im Direktlauf korrekt und im CI-Parallellauf lautlos verschwunden, eine Fehlerklasse, die lokal nie auffällt.

Jeder dieser vier Defekte ist inzwischen behoben (Tag-Registrierung mit Schema-Guard in `pytest_configure`, TC-ID-Ableitung über den Marker- statt Docstring-Kanal, `item.path.name` statt `item.location[0]`, Hook-Verschiebung nach `conftest.py`) und in `tests/e2e/README.md` dokumentiert. Das ändert aber nichts an der Kernaussage: **keiner dieser vier Defekte ist in der pytest-bdd-Dokumentation offensichtlich**, jeder wurde nur durch den realen Integrationsversuch sichtbar. Wer BDD ohne diesen Erfahrungsschatz einführt, tritt dieselben vier Fallen erneut.

### 4. Reproduzierbarkeit

Das Szenario lief im containerisierten Stack grün, wiederholt, und parallel unter `-n 4 --dist=loadfile` auf getrennten Workern neben dem klassischen Test — kollisionsfrei, dank eindeutiger Instanz-ID pro Lauf. Es ist selbstprovisionierend: keine Abhängigkeit von vorab geladenen Seed-Daten, kein `pytest.skip` (NFR-008a). Die Verifikation (`nolte-engineering:e2e-test-reviewer`, P6-final) bestätigte alle sieben geforderten Nachweise: BDD-Solo-Lauf, klassischer Solo-Lauf, jeweilige Wiederholung, Parallellauf, JUnit-`tc_id` nach dem xdist-Merge, Protokoll-Eintrag, korrekte Screenshot-Anzahl.

### 5. Reporting

Die JUnit-`tc_id`-Property überlebt den xdist-Merge. `protokoll.md` listet das Szenario mit der Testfall-ID `TC-004-092` (dabei wurde nebenbei ein vorbestehender, unabhängig vom BDD-Anteil existierender Bug behoben: `protocol_plugin.py` prüfte bislang nur das Muster `TC-REQ-\d{3}-\d{3}`, die tatsächlich verwendete Form `TC-004-092` fehlte daher schon vorher in jedem Protokoll — auch dem des klassischen Tests aus PR #763).

Ein echter, spezifisch dem BDD-Layer zurechenbarer Vorteil: Die Screenshots werden nicht mehr per Hand im Testkörper platziert (`screenshot("TC-004-092_view1-global", …)`, wie im klassischen Test), sondern automatisch aus dem Gherkin-Steptext abgeleitet, über den `pytest_bdd_after_step`-Hook. Der finale Lauf erzeugte **exakt 9 Screenshots** für 1 `When`- und 8 `Then`-Schritte, keinen für die drei `Given`-Schritte — der Hook filtert korrekt auf `step.type` (den aufgelösten Typ), nicht auf `step.keyword` (das literale Gherkin-Wort, das bei einem fortgesetzten `And`-Given fälschlich `"And"` trägt und ohne die Korrektur die Vorbedingungs-Zeile mitfotografiert hätte).

### 6. Migrationspfad

Die Schätzung stützt sich auf eine **gemessene**, nicht geschätzte Kennzahl aus dem Review-Durchlauf: Vor der Parametrisierung kodierten 5 von 9 Steps eine feste Zahl oder ein festes Datum direkt im Steptext, und 5 von 9 Bindungen waren ausschließlich für TC-004-092 brauchbar. Nach der Parametrisierung sind **0 von 11 Bindungen** bespoke, **9 von 11** sind wörtlich wiederverwendbar. Die verbleibenden 2 sind auf eine reine, ungedüngte Bewässerung spezialisiert — das ist ein anderes fachliches Verhalten (kein Düngekanal beteiligt), keine Duplikation von Infrastruktur.

**Ableitung für die ~90 REQ-004-Fälle:** Unter der Annahme, dass ein substanzieller Teil der übrigen Fälle Varianten desselben Musters sind (andere Mengen, andere Anwendungsmethode, andere Ausgangszustände der Gießprotokolle) — eine Annahme, keine Messung —, deckt der bestehende Wortschatz (Bewässerungsmenge, Anwendungsmethode, Tages-Token, Zähl-Deltas) einen erheblichen Anteil ohne neue Bindungen ab. Neue Bindungen sind dort nötig, wo ein fachlich neues Konzept eingeführt wird (z. B. Düngekanäle, EC-Werte, Tank-Bezug) — nicht dort, wo nur ein Parameter variiert. Eine seriöse Aufwandsschätzung braucht dennoch eine Sichtung der ~90 Fälle nach genau dieser Trennung (Parameter-Variante vs. neues Konzept), bevor eine Personentage-Zahl genannt werden kann; diese Sichtung ist selbst ein sinnvolles nächstes Arbeitspaket, kein Teil dieser PoC.

### `pytest-bdd` vs. `behave`

`pytest-bdd` wurde gewählt, weil es die bestehende Toolchain **wiederverwendet statt verdoppelt**: dieselben Fixtures (`conftest.py`), dieselbe `pytest.ini`, dieselben zwei Selektionsachsen, dieselbe `xdist`-Parallelität, dieselben Page-Objects, dasselbe JUnit-/Protokoll-Reporting. `behave` ist ein eigenständiger Runner mit eigenem Fixture-Modell (Environment-Hooks statt pytest-Fixtures) und hätte jeden dieser Bausteine gegabelt — eine zweite Konfigurationsquelle, eine zweite Parallelisierungslösung, ein zweites Reporting. Das Portfolio hat diese Präferenz mit `spec/project/behavior-driven-development/` bereits als Referenzprofil hinterlegt; die PoC bestätigt sie empirisch, statt sie neu zu verhandeln.

## Konsequenzen

### Positiv

- Neue Testfälle mit klarer Given/When/Then-Struktur können als lesbares, aus der Spec ableitbares Gherkin-Szenario entstehen, maschinell auf Spec-Traceability geprüft.
- Der Traceability-Check (`scripts/check_bdd_traceability.py`) ist unabhängig nutzbar und deckt schon heute eine reale Lücke ab (Docstring-Drift bei den klassischen Tests), die vorher unsichtbar war. Diese Drift wurde in Issue #771 durch eine gemeinsame SSOT (`tests/e2e/_gherkin.py`) behoben, die beide Parser seither nutzen.
- Automatisch aus dem Steptext abgeleitete Screenshots senken den Pflegeaufwand künftiger Szenarien gegenüber hand-platzierten `screenshot(...)`-Aufrufen.
- Die Reusability-These ist nicht behauptet, sondern gemessen: 9 von 11 Bindungen sind nach Parametrisierung wörtlich wiederverwendbar.

### Negativ

- Vier nicht in der pytest-bdd-Dokumentation offensichtliche Integrations-Hazards (A–C plus toter Hook) mussten selbst gefunden werden; jedes künftige Team, das diesen Weg ohne diese PoC ginge, würde dieselben Fallen erneut treffen, sofern die hier entstandenen Guards (Tag-Registrierung, Marker-Kanal, `item.path.name`, Hook-Standort) nicht als verbindliches Muster übernommen werden.
- Englische Gherkin-Prosa in einem primär deutschsprachig dokumentierten Projekt erhöht die Einstiegshürde für nicht-technische, deutschsprachige Mitwirkende; die einzige Brücke ist der TC-ID-Tag.
- Zwei parallele Implementierungen derselben Testfälle (klassisch + BDD) bedeuten während einer Übergangsphase doppelte Wartung, falls nicht diszipliniert auf geteilte Helfer/Fixtures (`_journey_helpers.py`, `conftest.py`) konsolidiert wird.
- Der Traceability-Check ist bewusst **nicht** in einen CI-Gate eingebunden (nur `static` ist required auf diesem Repository) — er kann drift-frei bleiben, ohne dass das je durchgesetzt wird, wenn niemand ihn manuell aufruft.

### Wichtigster Nebenbefund — kein BDD-Thema, sondern ein CI-Gate-Thema

Der bedeutsamste Fund der gesamten PoC hat nichts mit BDD zu tun: **TC-004-092 hatte noch nie erfolgreich bestanden.** Der klassische Test wurde über PR #763 gemergt, während dessen `E2E smoke (compose, light)`-Check **rot** war — der Merge kam durch, weil auf diesem Repository ausschließlich `static` ein required Check ist. Der reale Lauf im containerisierten Stack deckte einen echten Backend-Defekt auf: `find_open_care_task(..., include_completed_today=True)` in `care_reminder_service.py` matcht per Docstring auch heute *abgeschlossene* Aufgaben — also genau die Aufgabe, die dieselbe Aufrufkette (`_complete_pending_care_task`) wenige Zeilen zuvor selbst geschlossen hatte. `ensure_next_watering_task` fand dadurch immer eine „erfüllende" Aufgabe und legte die Folgeaufgabe nie an, wodurch die Gießvorgangs-Kohärenz in View 3 nie zustande kam — für die BDD- **und** die klassische Implementierung gleichermaßen.

Der Defekt betraf **drei** Code-Pfade: die Dashboard-Bestätigung, die Gießprotokoll-Eintragung und `POST /tasks/{key}/complete` (`tenant_router.py`). Der Fix übergibt die soeben geschlossene Aufgabe explizit als `just_completed_task` an `ensure_next_watering_task`, sodass die Dedup-Prüfung zwischen „es existiert bereits eine erfüllende Aufgabe" und „die Aufgabe, die ich selbst gerade abgeschlossen habe" unterscheiden kann — ohne die Idempotenz-Regel aus Issue #509 (eine heute bereits bestätigte Erinnerung darf nicht sofort neu materialisieren) für andere Aufrufer aufzuweichen. Zwei neue Tests sichern die #509-Regel für alle anderen Aufrufer ab.

Dieser Fund ist ein Argument über den CI-Gate — der rote, aber nicht required E2E-Smoke-Check —, nicht über BDD. Er wird hier festgehalten, weil er sonst untergeht: Ohne den realen, containerisierten BDD-Lauf wäre der Defekt nicht in dieser PoC, sondern erst beim nächsten Vorfall aufgefallen.

### Folgemaßnahmen

- Migration weiterer TC-004-Fälle nach BDD ist ein eigenes, nachgelagertes Roadmap-Item — abhängig von der oben skizzierten Sichtung „Parameter-Variante vs. neues Konzept", nicht Teil dieser Entscheidung.
- Die vier hier gefundenen Integrations-Guards (Tag-Registrierung mit Schema-Prüfung, Marker-basierte TC-ID-Ableitung, `item.path.name` statt `item.location[0]`, Hook-Standort in `conftest.py`) sind als verbindliches Muster in `tests/e2e/README.md` dokumentiert und gelten für jedes künftige `.feature`-Modul.
- Der rote `E2E smoke (compose, light)`-Check auf `develop` ist mit dieser PoC miterledigt (der zugrunde liegende Backend-Defekt ist behoben); die Frage, ob dieser Check künftig required werden soll, bleibt ein eigener Entscheid außerhalb dieses ADR.

## Referenzen

- Issue #761 — `test(e2e): PoC — BDD E2E architecture driven from TC docs (TC-004-092 as first scenario)`
- `.audits/issue-orchestrate/761/analysis.md` — Orchestrierungs-Audit-Trail mit allen empirischen Befunden (Hazards A–C, BDR-001 bis BDR-010, Migrations-Kennzahlen)
- `tests/e2e/features/watering_cross_view_consistency.feature` — das Gherkin-Szenario
- `tests/e2e/test_req004_watering_cross_view_consistency_bdd.py` — die Step-Bindungen
- `tests/e2e/test_req004_watering_cross_view_consistency.py` — der klassische Vergleichstest
- `scripts/check_bdd_traceability.py` — der maschinelle Spec-↔-Test-Abgleich
- `tests/e2e/README.md` — Selektionsachsen, Tag-Schema, TC-ID-Ableitungsreihenfolge
- `spec/e2e-testcases/TC-REQ-004.md` — TC-004-092
- Issue #509 — Idempotenz-Regel für heute bereits bestätigte Erinnerungen
- PR #763 — klassische Implementierung von TC-004-092 (Schwester-Issue #760)
