# ADR-011: E2E-Smoke als Merge-Gate für `develop`

**Status:** Akzeptiert
**Datum:** 2026-07-26
**Entscheider:** Kamerplanter Development Team

## Kontext

Issue #773 stellte die Frage, ob der Job `E2E smoke (compose, light)` (Workflow `e2e-smoke.yml`, Compose-basiert, Ausführung von `scripts/run-e2e.sh --smoke`) den Merge nach `develop` blockieren soll.

Auslöser war ein konkreter Vorfall: PR #763 wurde gemergt, während `E2E smoke (compose, light)` **rot** war — mit der Assertion „TC-004-092 FAIL (View 3): exactly one new pending '— watering' follow-up task must exist, found 0". `develop` trug danach einen dauerhaft roten E2E-Check, und der zugrunde liegende Backend-Defekt blieb unentdeckt, bis Issue #770 das Szenario gezielt fuhr und ihn aufdeckte. Weder Code-Review noch Merge-Gate fingen den Defekt ab, weil auf diesem Repository ausschließlich `static / Static CI Tests` als required Kontext registriert war.

Eine Verifikation der Ausgangslage über die GitHub-API (nicht über die UI) bestätigte zwei Befunde:

1. `develop` führte tatsächlich nur einen einzigen required Kontext (`static / Static CI Tests`), bei `strict: true` und `enforce_admins: true` mit 0 erforderlichen Approvals.
2. `.github/settings.yml` hatte über die gesamte Historie **nie** einen `branches:`-Block. Der live in GitHub erzwungene Zustand existierte also ausschließlich im GitHub-eigenen State — entgegen `spec/project/pull-request-workflow` §74/§119, die eine As-Code-Deklaration der required Checks verlangen.

Zur Entscheidungsreife wurde die Datenlage von `E2E smoke (compose, light)` gemessen, nicht geschätzt: 13 Läufe in Folge grün seit 2026-07-25 (alle davor gescheiterten Läufe gehen auf den in #770 behobenen Defekt zurück), reale Laufzeit rund 11 Minuten. Der zweite E2E-Workflow, `e2e-nightly.yml` (5-Profil-Vollmatrix: light, full, mobile, tablet, full-mobile), lag demgegenüber bei 14 von 14 Läufen rot; Issue #746 ist offen, PR #759 ist nicht gemergt. Die im ursprünglichen Issue genannte Stabilisierungs-Voraussetzung betrifft also die Nightly-Profile — nicht den hier zu entscheidenden Gate-Kandidaten.

## Entscheidung

`E2E smoke (compose, light)` wird zusätzlich zu `static / Static CI Tests` als required Kontext auf `develop` registriert (`.github/settings.yml`, `strict: true`, `enforce_admins: true`).

Die Auswahl, **wann** die Suite überhaupt läuft, erfolgt über eine deny-by-default-Allowlist laufzeit-inerter Pfade (`docs/`, `spec/`, `project/`, `.audits/`, `.resume/`, `.claude/`, `styles/`, `*.md`, `.github/**` außer `e2e-*.yml`, `mkdocs.yml`, `.vale.ini`, `LICENSE`, `.gitignore`, `CODEOWNERS`, `Taskfile.yaml`, `.pre-commit-config.yaml`), ausgewertet in einem vorgeschalteten `changes`-Job (`dorny/paths-filter`) mit Job-Level-`if:` auf dem `smoke`-Job — **nicht** über einen Pfadfilter am Trigger.

Der Grund für dieses Conditional statt eines Trigger-Pfadfilters: Ein required Check, dessen Workflow durch einen Pfadfilter am `pull_request`-Trigger gar nicht erst startet, meldet nie einen Status und lässt den Pull Request dauerhaft auf „Expected — waiting for status to be reported" stehen — bei `enforce_admins: true` gibt es dafür keinen Override. GitHub rät deshalb ausdrücklich davon ab, Pfadfilter auf required Workflows anzuwenden. Ein per Job-Level-Conditional übersprungener Job meldet dagegen korrekt `Success`. Die Falle ist nicht hypothetisch: 11 der letzten 30 gemergten Pull Requests (37 %) hätten den Check bei einem reinen Trigger-Pfadfilter nie erzeugt.

Das Gate wird sofort mit diesem Pull Request scharf geschaltet, ohne auf die Nightly-Stabilisierung (#759, #768) zu warten — deren Ausgang betrifft ein anderes, weiterhin advisory bleibendes Profil.

## Konsequenzen

### Positiv

- Der Fehlermodus aus #763 — ein rot gemergter E2E-Check, der einen realen Backend-Defekt verdeckt — kann sich nicht mehr wiederholen, ohne dass der Merge blockiert.
- Die required-Checks-Konfiguration existiert jetzt als Code (`.github/settings.yml`, `branches:`-Block) statt nur im GitHub-State — behebt den zweiten Befund aus dem Kontext.
- Löst R2 aus `project/requirements/e2e-ci-selenium.md` ab, das E2E-Checks bewusst non-required hielt, solange das Flake-Verhalten unbekannt war; diese Guard-Bedingung ist durch die Messreihe beantwortet.

### Negativ

- PRs, die mindestens einen laufzeitrelevanten Pfad berühren, erhalten rund 11 Minuten zusätzliche Merge-Latenz. Gemessen am Korpus der letzten 45 gemergten PRs überspringen 33 % die Suite vollständig (Allowlist greift).
- Wegen `strict: true` wird nach jedem Merge nach `develop` jeder verbleibende offene PR `BEHIND` und muss neu bauen. Gemessen: 8 von 12 Dependency-PRs lösen die E2E-Suite aus; ein Renovate-Batch von 5 PRs kostet dadurch rund 55 Minuten statt rund 10 Minuten. Dieser Trade-off wird bewusst akzeptiert — die Entlastung über eine Merge Queue ist in ein eigenes Folge-Issue ausgelagert, nicht Teil dieser Entscheidung.
- Die Allowlist ist sicherheitsrelevant, nicht nur eine Performance-Optimierung: Ein *fehlender* Eintrag kostet nur einen unnötigen, rund 11-minütigen Lauf (fail-safe). Ein *fälschlich aufgenommener* Laufzeitpfad schaltet das Gate dagegen still grün (fail-open). Die Liste muss bei jeder neuen Top-Level-Verzeichnisstruktur überprüft werden.
- Das Conditional selbst ist fail-safe konstruiert: Die Suite wird **nur** übersprungen, wenn der Selektions-Job erfolgreich lief *und* den Diff als inert gemeldet hat. Schlägt er fehl, wird sie ausgeführt. Das ist load-bearing — `always()` sorgt lediglich dafür, dass die Bedingung überhaupt ausgewertet wird, es macht sie nicht wahr. Ohne die explizite Prüfung auf `needs.changes.result` wären die Outputs eines fehlgeschlagenen Jobs leere Strings, der Job würde übersprungen, und ein übersprungener Job meldet den required Check als `Success` — das Gate ginge grün, ohne dass die Suite je lief.

### Rollback-Regel

Schlägt der required Check binnen 7 Tagen zweimal fehl, ohne dass sich der Fehlschlag reproduzierbar auf eine Codeänderung zurückführen lässt, wird der Kontext über einen **regulären Pull Request** gegen `.github/settings.yml` entfernt — kein Einzelfall-Bypass, `enforce_admins` bleibt `true`.

## Bewertete Alternativen

| Kriterium | Komplexitäts-/Größen-Score | Gelernte Testauswahl | Coverage-basierte TIA | Pfadfilter ersatzlos entfernen | Duplikat-Workflow (gleicher Job-Name) | Merge Queue | Status quo (nur dokumentieren) | **Gewählt** |
|---|---|---|---|---|---|---|---|---|
| Wirkung im 45-PR-Korpus | nur 4/45 PRs zusätzlich erkannt (~1 min im Mittel), dabei genau die heikelsten Fälle (#718, #747, #716) übersehen | unbekannt — kein historischer Korpus vorhanden | unbekannt — eigenes Vorhaben | 100 % (jeder PR läuft), aber ohne Erkenntnisgewinn auf reinen Docs-PRs | technisch möglich, aber fragil | adressiert Latenz, nicht Selektion | kein Gate — Fehlermodus aus #763 bleibt bestehen | Suite läuft bei 67 % der PRs, keine Fehlurteile bei riskanten Änderungen |
| Datengrundlage | Größe korreliert nicht mit Risiko (Nagappan & Ball, ICSE 2005: absolute Churn ist kein tragfähiger Prädiktor, nur relative Churn — und selbst die sagt Defektdichte, nicht Testabdeckung voraus) | braucht großen Korpus historischer Testausgänge (Machalica et al.); kamerplanter hat ~3 Tage E2E-CI-Historie | braucht Coverage aus dem System under Test — instrumentierte Container über Prozessgrenzen | keine Datengrundlage nötig | keine Datengrundlage nötig | keine Datengrundlage nötig | keine Datengrundlage nötig | deny-by-default, keine statistische Kalibrierung nötig |
| Betriebsrisiko | Fehlurteile bei Tenant-relevanten Änderungen | keine ausreichende Datenbasis vorhanden | eigenständiges Vorhaben, beantwortet zudem die falsche Frage („welche Tests" statt „läuft die Suite") | ~11 min auf jedem PR, auch Docs-only | zwei Workflows mit demselben Job-Namen; eine Umbenennung bricht das Gate still | greift in geerbten `automerge`-Workflow aus `gh-plumbing` ein — eigenes Outcome | Fehlermodus aus #763 bleibt bestehen | fail-safe bei fehlendem Eintrag, fail-open-Risiko bekannt und dokumentiert |
| Entscheidung | verworfen | verworfen | verworfen (eigenes Vorhaben) | verworfen | verworfen | ausgelagert (Folge-Issue) | verworfen | **gewählt** |

Detailbegründungen:

- **Komplexitäts-/Größen-Score statt Allowlist:** an einem Prototyp gegen die letzten 45 gemergten PRs gemessen. Der Ertrag gegenüber der einfachen Allowlist beträgt nur 4 von 45 PRs zusätzlich (rund 1 Minute im Mittel), dafür trifft er Fehlurteile bei genau den heikelsten Änderungen — #718 (1 Datei, 1 Zeile, Tenant-Prüfung), #747 (Tenant-Ownership) und #716 wären ungetestet durchgelaufen. Größe korreliert nicht mit Risiko.
- **Gelernte Testauswahl** (Machalica et al., Predictive Test Selection): setzt einen großen Korpus historischer Testausgänge voraus; kamerplanter hat rund 3 Tage E2E-CI-Historie — zu wenig zur Kalibrierung.
- **Coverage-basierte Test-Impact-Analyse** (Datadog TIA, pytest-testmon): bräuchte Coverage aus dem System under Test, also instrumentierte Container über Prozessgrenzen hinweg. Ein eigenständiges Vorhaben, das zudem die feinere Frage „welche der Tests" beantwortet, während hier ein binäres Gate anstand.
- **Pfadfilter ersatzlos entfernen** (Suite läuft auf jedem PR): die einfachste Variante, kostet aber rund 11 Minuten auch auf reinen Docs-PRs ohne jeden Erkenntnisgewinn.
- **Duplikat-Workflow mit identischem Job-Namen** (der von GitHub ebenfalls dokumentierte Weg): verworfen, weil zwei Workflows denselben Job-Namen führen müssten und eine spätere Umbenennung das Gate still bricht.
- **Merge Queue:** adressiert die Latenz-Konsequenz wirksam, greift aber in den geerbten `automerge`-Workflow aus `gh-plumbing` ein — ein eigenständiges Outcome mit eigenem Issue, nicht Teil dieser Entscheidung.
- **Status quo beibehalten und nur dokumentieren:** verworfen, weil der Fehlermodus aus #763 dann unverändert bestehen bliebe.

## Referenzen

- Issue #773 — Ausgangsfrage, ob `E2E smoke (compose, light)` required werden soll
- PR #763 — rot gemergter E2E-Check, Auslöser dieser Entscheidung
- Issue #770 — deckte den zugrunde liegenden Backend-Defekt auf (dokumentiert in ADR-010)
- `project/requirements/e2e-smoke-merge-gate.md` — vollständige, operator-bestätigte Anforderungslage (R1–R10)
- `project/requirements/e2e-ci-selenium.md` — R2, als abgelöst markiert
- `.github/workflows/e2e-smoke.yml` — `changes`-Job (`dorny/paths-filter`) + Job-Level-`if:` am `smoke`-Job
- `.github/settings.yml` — `branches:`-Block für `develop` mit beiden required Kontexten
- `spec/project/pull-request-workflow` §74/§77/§119 — As-Code-Pflicht für required Checks, Rollback-Verfahren
- Issue #746, PR #759, PR #768 — Nightly-Stabilisierung, außerhalb dieses Scopes
- Nagappan, N.; Ball, T. (2005): „Use of Relative Code Churn Measures to Predict System Defect Density", ICSE 2005
- Machalica, M. et al. (2019): „Predictive Test Selection", ICSE-SEIP 2019

---

## Nachtrag 2026-07-28 — Merge-Train-Latenz gemessen und bewusst akzeptiert (#792)

Die oben unter „Konsequenzen" akzeptierte Latenz wurde nachgemessen, weil die
Schätzung aus #773 aus der PR-Historie abgeleitet war. Fenster
2026-07-27 15:00 – 2026-07-28 17:00, in dem 14 PRs nach `develop` gemergt wurden:

**60 `e2e-smoke`-Läufe.** Allein ein Renovate-Container-Digest-Bump
(`renovate/ollama-ollama-latest`) verursachte **10** davon — 7 abgeschlossen,
3 durch die nächste Aktualisierung abgebrochen, zusammen rund 110 Minuten
Runner-Zeit für eine Änderung, die sich zwischen den Läufen nie unterschied.
Jeder Neulauf war `strict: true`, das auf den Merge eines *anderen* PRs reagierte.

Der eigentliche Kostentreiber ist damit `strict: true`, nicht das Gate selbst.

**Bewertete Optionen (#792):**

- **Merge Queue** — behält die Garantie und beseitigt die serielle Last, weil sie
  das projizierte Merge-Ergebnis prüft. Blockiert an einer repo-übergreifenden
  Voraussetzung: `nolte/gh-plumbing`s `reusable-automerge.yaml` (gepinnt auf
  `bab4f9d29`) trägt keinen `merge_group`-Trigger und mergt selbst über
  `pascalgn/automerge-action` — eine Queue mergt ebenfalls selbst, beides
  schließt sich aus. Der Portfolio-Commons bräuchte zuerst einen Queue-Modus.
- **`strict: true` abschalten** — beseitigt die Kosten sofort und lokal, gibt aber
  genau die Zusage auf, für die es existiert: dass ein allein grüner PR auch im
  Merge grün bleibt.
- **Kosten akzeptieren** — gewählt.

**Begründung:** Es handelt sich um unbeaufsichtigte Maschinenzeit, nicht um
Betreuerzeit. Erneut zu bewerten, sobald das PR-Aufkommen so steigt, dass das
Driftfenster — wie lange `develop` und die offenen PRs auseinanderlaufen — echte
Konflikte erzeugt statt nur Neuläufe. Die Zahl steht zusätzlich als Kommentar
neben `strict: true` in `.github/settings.yml`, wo sie beim nächsten Eingriff in
den Branch-Schutz gelesen wird.
