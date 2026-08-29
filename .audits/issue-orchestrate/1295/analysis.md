# #1295 — actionlint + shellcheck als blockierende Gates: Analyse & Umsetzungsplan

**Issue:** [#1295](https://github.com/nolte/kamerplanter/issues/1295) —
„ci: adopt actionlint + shellcheck — three workflows already reason about a linter that never runs"
**Autor:** `nolte` (Repository-Owner → vertrauenswürdiger Autor; Issue-Text darf Arbeitspakete formen)
**Labels:** `enhancement`, `cicd` · **Milestone:** keiner · **Assignee:** keiner · **Kommentare:** 0
**Klassifikation:** `feature-request` (sekundär `infra`) — vom Operator bestätigt
**Anforderungsartefakt (autoritativ):** `project/requirements/ci-actionlint-shellcheck.md`, `U_gate = 0.88`,
Termination `saturation` — R1–R6 und A1/A2 sind der Vertrag und werden hier **nicht neu hergeleitet**
**Arbeitskopie:** `feat/ci-actionlint-shellcheck` (Worktree), abgezweigt von `origin/develop`
**Zustand des Codes bei der Messung:** `78785f87b` („fix(security): stop the nightly Nuclei command from being truncated by a comment (#1294)")
**Datum der Messung:** 2026-08-29
**Prozess-Spec:** `spec/project/issue-orchestration/` — single-source in
`claude-shared/spec/project/issue-orchestration/de.md`; die Abwesenheit unter `spec/project/`
dieses Repos ist eine bewusste Projektentscheidung, keine verletzte Vorbedingung

---

## 0. Methode und Beleg-Konvention

Jede tragende Behauptung ist entweder **[gemessen]** — mit dem Kommando oder der
`file:line`, die sie stützt — oder ausdrücklich **[nicht belegt]**, mit der Beobachtung,
die sie entscheiden würde, und der Feststellung, dass sie nicht gemacht wurde
(`spec/claude/claim-provenance/`).

Der Grund für diese Strenge steht im Anforderungsartefakt selbst: die zentrale Behauptung
des Issues („It overlaps SC2215") war **falsch**, und ein Plan, der sie geerbt hätte, hätte
einen funktionierenden Wächter zurückgebaut. Alle im Auftrag übergebenen Messwerte wurden
in dieser Sitzung **erneut gemessen**, keiner übernommen.

Über die Vorgabe hinaus wurden vier Dinge gemessen, die den Plan verändert haben:
die Abdeckungsgrenze **durch das echte Gate** statt durch nacktes shellcheck (§2.4),
die Verdrahtung **end-to-end ausgeführt** (§2.5), die Renovate-Zuständigkeit für
`rev:`-Pins (§2.6) und die Asymmetrie der Schweregrad-Schwellen (§2.7).

---

## 1. Prüfung der Ausgangshypothese

Die Hypothese des Auftrags lautete: **ein** kohärenter PR-Strang, ~drei abhängige Pakete
(Findings räumen → beide Tools gepinnt und blockierend verdrahten → Arbeitsteilung im
Docstring festhalten), Paket 2 abhängig von Paket 1.

**Ergebnis: im Kern bestätigt, in vier Punkten geschärft. Keine Refutation.**

| Hypothese | Befund |
|---|---|
| Ein PR-Strang, kein Roadmap-Item | **bestätigt** — vier Dateien, eine Ebene (CI/Tooling), kein neues REQ/NFR, jedes Akzeptanzkriterium testbar |
| Paket 2 hängt von Paket 1 ab | **bestätigt und belegt** — der shellcheck-Hook ist auf dem heutigen Baum **rot** (§2.5). Präzisierung: nur die shellcheck-Hälfte trägt diese Abhängigkeit; die actionlint-Hälfte ist heute schon grün (§2.2) |
| A1 (pre-commit statt eigener Actions-Job) trägt R3 | **bestätigt** — `rev:`-Pin + Renovate-Abdeckung belegt (§2.6); A1 muss **nicht** revidiert werden |
| Drei Pakete | **geschärft auf vier** — R6 ist kein Formalakt, sondern ein eigenes Paket mit eigenem Entwurfsproblem (§2.4/§4, WP-4) |

Vier Schärfungen, die die Hypothese nicht enthielt:

1. **Die R6-Demonstration ist konfundiert.** Der bestehende `commented_continuation`-Wächter
   feuert auf die #1010-Form bereits heute (§2.4). Ein naives „Form wiedereinsetzen, Lane wird
   rot" beweist über die neue actionlint-Hälfte **nichts** — die Lane wäre auch ohne sie rot.
   Das ist exakt die Fehlerklasse „Test erreicht die Regel über einen ANDEREN Pfad als die
   Produktion". WP-4 muss deshalb *attribuierbar* entworfen werden.
2. **Es gibt heute keinen einzigen `language: docker_image`-Hook** in diesem Repo (§2.8).
   Die Verdrahtung führt eine neue lokale Voraussetzung ein (laufender Docker-Daemon beim
   Committen). Das ist eine Entscheidung, keine Nebensache — Q2.
3. **Die Schweregrad-Schwellen sind asymmetrisch.** Das gebündelte shellcheck in actionlint
   läuft auf Default-Schwelle und meldet `info` (§2.7), während R2/A2 für die `*.sh`-Hälfte
   `--severity=warning` setzt. `.github/workflows/**` wird also **strenger** gegated als
   `scripts/**`. Zu benennen, nicht als Symmetrie anzunehmen.
4. **`task check` kennt die neuen Gates nicht.** Seine Kategorie „custom gates" ist eine
   handgepflegte Liste von sieben Skripten (§2.9); `pre-commit`-Hooks laufen dort gar nicht.
   Nicht von R1–R6 gefordert → Q4, nicht erfundenes Paket.

---

## 2. Gemessener Ist-Zustand

### 2.1 Die Ausgangslage des Issues ist unverändert wahr

**[gemessen]** `grep -rn "actionlint" .pre-commit-config.yaml .github/ Taskfile.yml scripts/`
→ Exit 1, **null Treffer**. actionlint kommt im Repo nicht vor.

**[gemessen]** `grep -rn "shellcheck" …` → genau **drei** Treffer, alle Kommentarzeilen,
keine Ausführung:

- `.github/workflows/e2e-smoke.yml:191`
- `.github/workflows/security-nuclei-nightly.yml:181`
- `.github/workflows/e2e-nightly.yml:106`

### 2.2 actionlint über den heutigen Baum: null Findings

**[gemessen]** `docker run --rm -v "$PWD:/repo" -w /repo docker.io/rhysd/actionlint:1.7.12`
→ **Exit 0**, keine Ausgabe. Image-Digest
`sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667`,
gebündeltes shellcheck **0.11.0**.

Kontrolle gegen Vakuität: dieselbe Konfiguration meldet auf einer Sonde mit der
#1010-Form `SC2215` (§2.4, Sonde A). Das Gate ist also nicht deshalb still, weil es nichts tut.

### 2.3 shellcheck über die eigenen Skripte: genau drei Findings

**[gemessen]** Die Menge der eigenen Shell-Skripte im Index umfasst **21** Dateien.

**[gemessen]** `docker run … docker.io/koalaman/shellcheck:v0.11.0 -S warning <alle 21>` → Exit 1:

| Datei | Code | Befund |
|---|---|---|
| `scripts/dev-teardown.sh:7` | SC2034 (warning) | `RED='\033[0;31m'` — belegt: `GREEN`/`YELLOW`/`NC` werden in `info()`/`warn()` benutzt, `RED` in keiner Funktion |
| `scripts/run-e2e.sh:33` | SC2155 (warning) | `export UID GID="$(id -g)"` maskiert den Exit-Status von `id -g` |
| `scripts/worktree_add.sh:69` | SC2088 (warning) | `"~/"*) root="$HOME/${root#\~/}" ;;` — **False Positive**; der Kommentar zwei Zeilen darüber (`worktree_add.sh:66-67`) sagt ausdrücklich, dass der Code das führende `~` selbst expandiert |

**Keine weiteren Findings.** Insbesondere keine aus `src/backend/.venv/**` oder
`**/node_modules/**` — siehe §2.5, warum das unter der pre-commit-Form automatisch gilt.

### 2.4 Die Abdeckungsgrenze — gemessen durch das echte Gate, in beide Richtungen

Vier Sonden-Workflows, jede durch **beide** Prüfer geschickt: durch
`docker.io/rhysd/actionlint:1.7.12` (also das gebündelte shellcheck 0.11.0, die Konfiguration,
die das Gate tatsächlich fahren wird) und durch
`python3 scripts/check_workflow_gate_integrity.py --scan-root <sondenverzeichnis>`.

| Sonde | Zeile nach dem Kommentar | actionlint + shellcheck | `commented_continuation` |
|---|---|---|---|
| A | `-tags exposure` (ein Flag) | **SC2215:warning** | **Finding** |
| B | `dest.txt` als zweites Argument von `cp` | **SC2225:error** | **Finding** |
| C | `positional_arg` an ein unbekanntes Kommando | **still** | **Finding** |
| D | `sort results.txt > results.txt` (SC2094, keine Continuation) | **SC2094:info** ×2 | **still** |

**[gemessen]** Sonden A–C: `actionlint` Exit 1 mit zwei Findings (A, B), C fehlt in der Ausgabe.
Wächter auf demselben Verzeichnis: `3 site(s)`, alle drei Sonden benannt.
**[gemessen]** Sonde D allein: `actionlint` Exit 1 (zweimal SC2094 auf `info`),
Wächter Exit 0 (`OK — 0 justified site(s)`).

Daraus folgen **zwei** Aussagen, und die zweite hatte der Auftrag nicht:

- **Für die Continuation-Form ist der Wächter eine echte Obermenge.** Sonde C zeigt, dass
  Retirement Abdeckung *verlöre*. Das belegt R5 und widerlegt die Formulierung des Issues
  („It overlaps SC2215") als unvollständig — sie ist der Grund, dass R5 überhaupt eine
  Anforderung ist.
- **In der Gegenrichtung sind die beiden disjunkt.** Sonde D ist ein shellcheck-Fund, den der
  Wächter nicht sieht. **Genau darauf muss WP-4 seine Attribution stützen** — nur so beweist
  die Demonstration, dass die *actionlint*-Hälfte lebt, und nicht bloß, dass der seit #1294
  bestehende Wächter noch funktioniert.

### 2.5 Die Verdrahtung wurde ausgeführt, nicht nur entworfen

Größte Unbekannte des Plans war, ob die pre-commit-Form (A1) überhaupt trägt. Sie wurde
**ausgeführt** — mit einer Konfiguration im Scratchpad, ohne eine Repo-Datei anzufassen:

```yaml
# Scratchpad-Sonde — NUR Messung, nicht die vorgeschlagene Endfassung
repos:
  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.12
    hooks: [{id: actionlint-docker}]
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks: [{id: shellcheck, args: [--severity=warning]}]
```

**[gemessen]** `pre-commit run -c <scratchpad>/probe-config.yaml --all-files` (pre-commit 4.5.0):

```
Lint GitHub Actions workflow files.......................................Passed
ShellCheck v0.11.0.......................................................Failed
```

mit exakt den drei Findings aus §2.3 und **keinen** weiteren. Damit ist belegt:

- Beide Hooks laufen in dieser Form; die Dateiübergabe funktioniert.
- Die actionlint-Hälfte ist ab Tag 1 grün → sie kann sofort blockierend gestellt werden.
- Die shellcheck-Hälfte ist ab Tag 1 **rot** → **WP-2 hängt belegt von WP-1 ab**.
- Die geforderten Ausschlüsse (`.venv`, `node_modules`) treten **automatisch** ein:
  `pre-commit --all-files` arbeitet über den Index, und **[gemessen]** kein einziger
  der 4284 indizierten Pfade liegt unter `node_modules/` oder `.venv/`. Es braucht kein
  `exclude:`-Muster. *Kehrseite, die in den Kommentarblock gehört:* der Ausschluss ist eine
  Folge davon, dass diese Bäume nicht im Index stehen — eine spätere Glob-basierte
  Task-Variante hätte ihn nicht.
- **[gemessen]** Der `types: [shell]`-Satz von pre-commit deckt sich hier mit den 21 `*.sh`:
  ein Scan über alle 4284 indizierten Dateien fand **0** Dateien mit Shell-Shebang ohne
  `.sh`-Endung. Der Hook fasst also keine unerwarteten Dateien an.

**[gemessen]** Laufzeit `actionlint-docker` über den ganzen Baum bei warmem Image: **1,04 s**.

### 2.6 Pinning und wer die Bumps besitzt (R3)

**[gemessen]** Die `.pre-commit-hooks.yaml` von `rhysd/actionlint` (via `gh api`) definiert:

```yaml
- id: actionlint-docker
  language: docker_image
  entry: docker.io/rhysd/actionlint:1.7.12    # kein `latest`
```

und `koalaman/shellcheck-precommit`:

```yaml
- id: shellcheck
  language: docker_image
  entry: docker.io/koalaman/shellcheck:v0.11.0
```

Der gewählte `rev:` bestimmt also den Image-Tag; ein Upstream-Release kann die Lane nicht
über Nacht rot färben. **[gemessen]** Neuestes actionlint-Release: `v1.7.12` (2026-03-30).
**[gemessen]** `koalaman/shellcheck-precommit` hat keine *Releases*, nur Tags; jüngster Tag `v0.11.0`.

**[gemessen]** Renovates `pre-commit`-Manager ist in diesem Repo **aktiv**: PR
[#1079](https://github.com/nolte/kamerplanter/pull/1079) „chore(deps): update pre-commit hook
python-jsonschema/check-jsonschema to v0.38.0", gemergt 2026-08-09. R3s Wartungsgeschichte
(„Renovate besitzt die Bumps") ist damit belegt und nicht bloß erhofft.

### 2.7 Die Schweregrad-Schwellen sind asymmetrisch

**[gemessen]** Sonde D: actionlint meldet `SC2094:info` und geht auf **Exit 1**. Die
gebündelte shellcheck-Integration läuft also auf shellcheck-Default (bis `style`/`info`
hinunter), während R2/A2 für die `*.sh`-Hälfte `--severity=warning` als Boden setzt.

**[nicht belegt]** Ob actionlint einen Schalter hat, um die Schwelle des gebündelten
shellcheck anzuheben. Die Beobachtung, die das entscheiden würde: `actionlint -h` gegen
1.7.12 lesen bzw. `.github/actionlint.yaml` gegen die Doku prüfen — **nicht gemacht**.
Folge für den Plan: WP-2 muss die Asymmetrie im Kommentarblock **benennen**; sie ist heute
folgenlos (§2.2: null Findings auf der strengeren Schwelle), aber der nächste Workflow-Edit
kann an einer `info`-Regel scheitern, während dieselbe Konstruktion in einem `.sh` durchgeht.

### 2.8 Verdrahtungsumfeld

**[gemessen]** Die required Checks auf `develop` sind
`["static / Static CI Tests", "lint-test-build (22)"]`
(`gh api repos/nolte/kamerplanter/branches/develop/protection`). Ein pre-commit-Hook ist
damit **automatisch** blockierend; es ist **keine** Änderung an der Branch-Protection nötig,
und R1/R2 („die required `static` lane SHALL fail") sind allein durch die Hook-Aufnahme erfüllt.

**[gemessen]** `.github/workflows/build-static-tests.yaml` ruft
`nolte/gh-plumbing/.github/workflows/reusable-pre-commit.yaml@d51e51ec…` (v2.0.0) auf; deren
Job `static` läuft auf `ubuntu-latest` mit `actions/setup-python` und `pre-commit/action@v3.0.1`
(also `pre-commit run --all-files`). Kein projektspezifisches Setup, keine installierten
Projekt-Abhängigkeiten — was zur `language: docker_image`-Form passt, die nichts davon braucht.

**[nicht belegt]** Dass auf dem Runner dieses reusable Workflows ein Docker-Daemon verfügbar
ist. Indiz, kein Beweis: **[gemessen]** dieses Repo fährt `docker run` auf `ubuntu-latest` in
`security-zap-nightly.yml:139` und `security-zap-postmerge.yml:154`. Die Beobachtung, die es
entscheiden würde: ein tatsächlicher Lauf der `static`-Lane mit den Hooks — **nicht gemacht**,
und genau das leistet WP-4.

**[gemessen]** `.pre-commit-config.yaml` enthält heute **keinen** `language: docker`- oder
`docker_image`-Hook (`grep -n "language: docker"` → NONE), und keines der als `entry`
verwendeten Skripte (`frontend_hook.sh`, `nuclei_validate_hook.sh`, `guard_nested_worktree.sh`,
`guard_resume_files.sh`) ruft Docker auf. → Q2.

### 2.9 Lokale Aggregate

**[gemessen]** `.taskfiles/checks.yaml:62` — `task precommit` ist `pre-commit run --all-files`.
Die neuen Hooks landen dort **automatisch**.

**[gemessen]** `.taskfiles/checks.yaml:109` — `task check` ruft pre-commit **nicht** auf; seine
Kategorie „custom gates" ist eine handgeschriebene Liste von sieben `python3 scripts/check_*.py`,
und sein `desc:` spricht von „den sieben custom source-tree gates". Die neuen Gates wären dort
abwesend. Nicht von R1–R6 gefordert → **Q4**.

### 2.10 Kein Vorlauf, keine Kollision

**[gemessen]** `gh pr list --search "actionlint OR shellcheck"` → 10 gemergte CI-PRs, keiner
führt eines der Tools ein. `gh pr list --state open --search "1295"` → leer. Kein
selbstauflösender Merge, kein paralleler `issue-orchestrate`-Lauf.

### 2.11 Ein Detail, das WP-1 kippen könnte — geprüft und entschärft

`scripts/run-e2e.sh:33` ist `export UID GID="$(id -g)"`. In bash ist `UID` readonly, und die
naheliegende Sorge ist, dass `export UID` scheitert und `${UID:-1000}` in
`docker-compose.e2e.yml` (Zeilen 181, 208, 235, 403, 448, 478, 508, 538) still auf den Default
fällt.

**[gemessen]** Ein bash-Lauf mit exakt dieser Zeile unter `set -uo pipefail` liefert `rc=0`,
und `UID` **und** `GID` stehen danach in der Umgebung. Kein latenter Defekt; die
SC2155-Reparatur muss lediglich beides exportiert lassen. Das Akzeptanzkriterium von WP-1
prüft genau das.

---

## 3. Scope

### In Scope

- `actionlint` (mit shellcheck-Integration) über `.github/workflows/**`, versionsgepinnt,
  blockierend in der required `static` lane (R1, R3)
- `shellcheck` über die 21 eigenen `*.sh`, Boden `warning`, versionsgepinnt, blockierend (R2, R3, A2)
- Räumen der drei gemessenen Findings **vor** der Scharfschaltung, SC2088 als Suppression
  **mit Begründung** (R4)
- Erhalt von `commented_continuation` und die gemessene Arbeitsteilung in seinem Docstring (R5)
- Ausgeführter, **attribuierbarer** Nachweis, dass beide Hälften rot werden können (R6)

### Explizit out of Scope

- `src/backend/.venv/**`, `**/node_modules/**` (Fremdcode — unter der pre-commit-Form ohnehin
  automatisch draußen, §2.5)
- jeder nicht-Shell-Linter (yamllint, hadolint, …)
- jede inhaltliche Workflow-Änderung über das hinaus, was die Gates erzwingen — und das ist
  **[gemessen]** nichts: actionlint ist auf dem heutigen Baum still (§2.2)
- Anheben des shellcheck-Bodens auf `info`/`style` (A2: additive, getrennte Entscheidung)
- Fortschreiben von NFR-003 (→ Q1) und von `task check` (→ Q4)
- Retirement des `commented_continuation`-Wächters — durch Messung (§2.4, Sonde C) und durch
  R5 ausgeschlossen

### Routing-Empfehlung

**Ein gebundener, direkt umzusetzender PR-Strang. Keine Weiterleitung in die formale
`roadmap → feature → sprint`-Pipeline.** Begründung: ein einziges Ergebnis
(„Workflow- und Shell-Linting ist erzwungen"), vier berührte Dateien auf einer Ebene, kein
neues REQ/NFR, kein Datenmodell, keine Migration, kein UI-Anteil — und **jedes** der sechs
Requirements lässt sich als beobachtbares Kriterium formulieren (§4). Kein Paket musste als
Routing-Signal markiert werden.

---

## 4. Arbeitspakete

| ID | Problem | Akzeptanzkriterium (beobachtbar) | Dateien | Spezialist | Abhängigkeiten |
|---|---|---|---|---|---|
| **WP-1** | Die drei gemessenen shellcheck-Findings stehen dem Scharfschalten im Weg (R4) | shellcheck 0.11.0 mit `-S warning` über alle 21 eigenen `*.sh` → **Exit 0, keine Ausgabe**. Zusätzlich unverändertes Verhalten von `run-e2e.sh`: nach der geänderten Zeile stehen **beide** Variablen in der Umgebung (`env` zeigt je eine `UID=`- und eine `GID=`-Zeile). Die SC2088-Suppression trägt eine Begründung in derselben Zeile bzw. dem Kommentarblock darüber | `scripts/dev-teardown.sh`, `scripts/run-e2e.sh`, `scripts/worktree_add.sh` | `fullstack-developer` | — |
| **WP-2** | Beide Tools laufen nirgends; drei Workflows argumentieren über einen Linter, der nie lief (R1, R2, R3) | `pre-commit run --all-files` auf der Repo-Config **grün**, und die beiden neuen Hooks erscheinen namentlich in der Ausgabe (nicht `(no files to check) Skipped`). Beide `rev:` sind exakte Tags (`v1.7.12`, `v0.11.0`), kein `latest`, kein Floating-Branch. Der shellcheck-Hook trägt `args: [--severity=warning]`. Der Kommentarblock benennt: (a) warum blockierend ab Tag 1 statt advisory, (b) die Schweregrad-Asymmetrie aus §2.7, (c) dass `.venv`/`node_modules` über die Nicht-Indizierung ausgeschlossen sind und nicht über ein `exclude:`, (d) den Querverweis auf `commented_continuation` | `.pre-commit-config.yaml` | `fullstack-developer` | **WP-1** (belegt: der shellcheck-Hook ist auf dem heutigen Baum rot, §2.5) |
| **WP-3** | Nach R5 bleiben zwei Prüfer über einer Form; ohne notierte Arbeitsteilung ist das undokumentierte Duplizierung — und das Issue selbst behauptet fälschlich vollständige Überlappung (R5) | Der Docstring von `scan_continuations` nennt die **gemessene** Tabelle aus §2.4: shellcheck deckt den Flag-Fall (`SC2215`) und Kommandos bekannter Arität (`SC2225`) ab und ist beim generischen positionalen Fall **still**; deshalb bleibt der Wächter. Er nennt die Sonden reproduzierbar (Form, nicht nur Ergebnis). `python3 scripts/check_workflow_gate_integrity.py` weiterhin Exit 0 und `pytest tests/unit/test_workflow_gate_integrity_check.py -q` (aus `src/backend`) grün — der Test pinnt Verhalten, nicht Docstring-Text (`test_workflow_gate_integrity_check.py:166`) | `scripts/check_workflow_gate_integrity.py` (Docstring von `scan_continuations`, ~Zeile 241) | `fullstack-developer` | — (disjunkt zu WP-1/WP-2; parallel dispatchbar) |
| **WP-4** | R6 fordert den **ausgeführten** Nachweis; naiv ausgeführt ist er durch den bestehenden Wächter konfundiert und beweist über actionlint nichts | Drei ausgeführte Läufe, deren Ausgabe im PR festgehalten wird, danach vollständig zurückgenommen (sauberer Arbeitsbaum): **(a)** #1010-Form in einen Workflow eingesetzt → der **actionlint**-Hook scheitert und nennt `SC2215` **mit dem Dateinamen**; **(b)** eine shellcheck-only-Form ohne Continuation (§2.4, Sonde D: `sort f > f`, SC2094) eingesetzt → **nur** der actionlint-Hook scheitert, `check_workflow_gate_integrity.py` bleibt Exit 0 — das ist der Teil, der die Rotfärbung der neuen Hälfte **zuschreibbar** macht; **(c)** ein absichtliches `warning`-Finding in einem `*.sh` → der shellcheck-Hook scheitert. Mindestens ein Lauf muss über `pre-commit run --all-files` gehen (derselbe Pfad, den `pre-commit/action` in der Lane fährt); die CI-Beobachtung der `static`-Lane auf dem gepushten Branch schließt die offene Frage aus §2.8 (Docker auf dem Runner) und ist **verpflichtend, bevor der PR mergt** | keine dauerhaft (transiente Injektion, zurückgenommen); Nachweis-Ausgabe in die PR-Beschreibung | `fullstack-developer` — **kein dedizierter Spezialist**, siehe unten | **WP-2** |
| **WP-5** *(bedingt, nur nach Freigabe von Q4)* | `task check` führt pre-commit nicht aus; seine „custom gates" sind sieben handgepflegte Skriptaufrufe — die neuen Gates wären im lokalen Aggregat abwesend und „nicht gemessen" sähe aus wie „bestanden" | `task check` führt die beiden neuen Gates aus und weist sie in der Tabelle aus; ein absichtliches Finding lässt `task check` fehlschlagen. Der `desc:`-Text nennt keine stale Anzahl mehr | `.taskfiles/checks.yaml` | `fullstack-developer` | WP-2 · **blockiert auf Q4** |

### Zur Spezialisten-Zuordnung

Zugeordnet wurde nach **Fähigkeitsbeschreibung** der zum Planungszeitpunkt vorhandenen Agenten
und Skills, nicht nach einer eingefrorenen Namensliste.

- WP-1 bis WP-3 sind Quelltext- und Konfigurationsänderungen gegen den erkannten Stack des
  Projekts → `fullstack-developer` („turns a sharply-scoped requirement into production-ready,
  runnable code … against the consuming project's own tech stack, layout, and quality bar").
  Deckt sich mit der dokumentierten Projektpräferenz für Quellcode-Arbeit.
- **WP-4 hat keinen passenden Spezialisten.** `quality-gate-enforcer` wäre thematisch am
  nächsten, ist aber ausdrücklich read-only („audits the wiring, **never runs it**") und damit
  für einen Nachweis, dessen ganzer Sinn die Ausführung ist, disqualifiziert. Das
  `quality-gate`-Skill fährt das Gate, aber nicht die dafür nötige, wieder zurückgenommene
  Defekt-Injektion. Zuordnung daher an `fullstack-developer` (hat `Bash`), mit dieser Lücke
  ausdrücklich vermerkt.
- **Optional, nach WP-2/WP-4:** `quality-gate-enforcer` als read-only Nachprüfung der neuen
  Verdrahtung. Nicht von R1–R6 gefordert, kein Paket.

### Abhängigkeitsordnung (DAG)

```
WP-1 ──► WP-2 ──► WP-4
                    ▲
WP-3 (unabhängig)   │
                    │
WP-5 (bedingt) ─────┘   … nur falls Q4 bejaht; hängt an WP-2
```

- **WP-1 → WP-2**: belegt, nicht angenommen (§2.5). Nur die shellcheck-Hälfte trägt sie;
  die actionlint-Hälfte ist heute grün. Da beide Hälften dieselbe Datei bearbeiten, bleiben
  sie **ein** Paket — ein Split würde zwei Pakete auf `.pre-commit-config.yaml` kollidieren lassen.
- **WP-3** berührt eine andere Datei als WP-1/WP-2 und ist zu beiden nebenläufig dispatchbar.
  Weiche Kopplung: WP-2s Kommentarblock verweist auf den Docstring; ein Reviewer sollte beide
  im selben PR sehen.
- **WP-4** braucht die scharfe Verdrahtung und ist deshalb strikt letztes Paket.

---

## 5. Risiken

| # | Risiko | Beleg | Bewertung |
|---|---|---|---|
| **RK-1** | Die beiden Hooks wären die **ersten** `language: docker_image`-Hooks des Repos; lokales Committen setzt dann einen laufenden Docker-Daemon voraus | **[gemessen]** `grep -n "language: docker" .pre-commit-config.yaml` → NONE | Vertretbar: Docker ist für `task dev` (kind) und die E2E-Suite ohnehin Voraussetzung. Die `files:`-Filter der Hooks begrenzen den lokalen Anfall auf Commits, die Workflows oder `*.sh` berühren. **Trotzdem eine Entscheidung → Q2** |
| **RK-2** | Der `rev:` bindet einen Image-**Tag** (`1.7.12`, `v0.11.0`), keinen Digest; ein neu gepushter Tag verschöbe das Werkzeug unbemerkt | **[gemessen]** upstream `.pre-commit-hooks.yaml` beider Repos | Rest-Risiko, bewusst. Die Alternative (lokaler Hook mit digest-gepinntem `docker run`) verlöre die belegte Renovate-Abdeckung (§2.6) und damit R3s Wartungsgeschichte. Der gemessene Digest steht in §2.2 als Referenz |
| **RK-3** | Schweregrad-Asymmetrie: `.github/workflows/**` wird auf shellcheck-Default (bis `info`) gegated, `*.sh` nur ab `warning` | **[gemessen]** §2.7, Sonde D (`SC2094:info` → Exit 1) | Heute folgenlos (null Findings). Muss im Kommentarblock stehen, sonst liest der nächste Autor Symmetrie hinein |
| **RK-4** | Die R6-Demonstration ist durch den bestehenden Wächter konfundiert und beweist naiv ausgeführt nichts über die neue Hälfte | **[gemessen]** §2.4, Sonden A und D | Durch WP-4s Teil (b) adressiert. Wird WP-4 abgekürzt, ist R6 **vakuös erfüllt** — dieselbe Klasse, wegen der #1010 drei Wochen überlebte |
| **RK-5** | „Null Findings heute" ist eine Aussage über das heutige Regelwerk; ein gepinnter Bump mit neuen Regeln landet als roter Renovate-PR | Anforderungsartefakt, Residual-Risiko zu R3 | Beabsichtigter Tausch (roter PR statt rote Nacht). Nicht mitigieren, benennen |
| **RK-6** | Zusätzliche Laufzeit in der required Lane; `strict: true` multipliziert das über den Merge-Train | **[gemessen]** 1,04 s (actionlint, warmes Image). **[nicht belegt]**: der Kalt-Pull in CI — die Beobachtung wäre der erste `static`-Lauf mit den Hooks, **nicht gemacht** | Klein. Beide Images sind schlank; WP-4s CI-Beobachtung liefert die Zahl nebenbei |
| **RK-7** | Zwei Prüfer über einer breit geteilten Invariante bleiben stehen (R5) | Anforderungsartefakt, Residual-Risiko zu R5 | Genau deshalb ist WP-3 kein Beiwerk: die gemessene Sondentabelle im Docstring ist das, was den Erhalt von undokumentierter Duplizierung unterscheidet |

---

## 6. Offene Fragen an den Operator

| # | Frage | Warum sie nicht geraten wurde | Vorbelegung, falls keine Antwort kommt |
|---|---|---|---|
| **Q1** | Soll die Tools-Matrix in `spec/nfr/NFR-003_Code-Standard-Linting.md:335` um actionlint/shellcheck ergänzt werden? **[gemessen]** sie listet heute Ruff/mypy/ESLint/Prettier und kennt weder Shell- noch Workflow-Linting | Von R1–R6 nicht gefordert; die Scope-Grenze des Anforderungsartefakts nennt Spec-Pflege nicht. Eine Spec-Änderung zu erfinden wäre Scope-Erweiterung am Gate vorbei | **Nein** — außerhalb dieses Strangs; ggf. eigenes Issue |
| **Q2** | `language: docker_image` (Vorschlag) oder `language: golang` bzw. `system`? | Gemessene Konsequenz, kein Geschmack: `golang` pinnt über den `rev` nur **actionlint** und nimmt shellcheck von `PATH` — dessen Version wäre dann die des Runner-Images und damit **ungepinnt**, was R3 verletzt. `system` pinnt gar nichts. Preis von `docker_image` ist RK-1 | **`docker_image`** — die einzige belegte Form, die R3 für **beide** Werkzeuge erfüllt. A1 muss dafür **nicht** revidiert werden |
| **Q3** | SC2034 in `scripts/dev-teardown.sh:7`: `RED` löschen oder eine `error()`-Hilfsfunktion ergänzen, die es benutzt? | R4 schreibt für dieses Finding keine Disposition vor (anders als für SC2088); das Issue nennt es „cosmetic" und „one deletion" | **Löschen** — folgt dem Wortlaut des Issues, kleinster Eingriff. **[gemessen]** `GREEN`/`YELLOW`/`NC` werden in `info()`/`warn()` benutzt, `RED` in keiner Funktion |
| **Q4** | Sollen die neuen Gates auch in `task check` erscheinen (→ WP-5)? **[gemessen]** `task check` fährt pre-commit nicht; seine „custom gates" sind sieben handgepflegte Aufrufe und sein `desc:` nennt die Zahl „sieben" | Nicht von R1–R6 gefordert. Es ist aber genau die Lücke, vor der `task check`s eigener Kommentar warnt („SKIPPED IS FAIL"): `task precommit` deckt die Hooks ab, `task check` nicht — zwei lokale Aggregate mit verschiedener Antwort | **Ja empfohlen**, aber als **bedingtes** WP-5 geführt und ohne Freigabe nicht dispatchen |

**Keine blockierende Vorbedingung.** Das Anforderungsartefakt liegt vor und ist
operator-bestätigt (`U_gate = 0.88 > τ_high = 0.8`), die Konventionen des Repos sind erkannt,
und die einzige echte Unbekannte der Hypothese — ob die pre-commit-Form trägt — wurde
ausgeführt (§2.5) statt vermutet. Q1–Q4 sind Feinschnitt, keine Sperren; Q4 hält lediglich
WP-5 zurück.

---

## 7. Was ausdrücklich **nicht** belegt ist

| Behauptung | Beobachtung, die sie entscheiden würde | Status |
|---|---|---|
| Der Runner des reusable `static`-Workflows hat einen Docker-Daemon | Ein `static`-Lauf mit den Hooks auf dem gepushten Branch | **nicht gemacht** — WP-4 liefert es; Indiz: `docker run` auf `ubuntu-latest` in zwei Workflows dieses Repos |
| actionlint kann die Schwelle des gebündelten shellcheck anheben | `actionlint -h` gegen 1.7.12 / `.github/actionlint.yaml`-Doku | **nicht gemacht** — folgenlos, solange der Baum auf der strengeren Schwelle still ist (§2.2) |
| Der Kalt-Image-Pull kostet die `static`-Lane wenig | Laufzeit des ersten CI-Laufs mit den Hooks | **nicht gemacht** — fällt in WP-4 an |
| Die vorgeschlagenen Hook-Einträge in ihrer **Endfassung** (Kommentarblock, `files:`-Filter) verhalten sich wie die Sonde | Ausführung nach WP-2 | **nicht gemacht** — gemessen wurde die minimale Sondenfassung aus §2.5; sie wurde bewusst nicht ins Repo geschrieben, weil Planen und Umsetzen hier getrennt sind |
| `-S warning` ist der richtige Boden | Nichts wurde über das `info`/`style`-Band gemessen | **nicht gemacht** — A2 des Anforderungsartefakts, ausdrücklich als spätere additive Entscheidung geführt |

## Operator decisions (route gate, 2026-08-29)

Recorded per `spec/project/issue-orchestration/` §Route — the route is an explicit,
operator-confirmed gate, and the four open questions were answered at the same turn.

| Gate / question | Decision | Consequence |
|---|---|---|
| **Route** | **Implement directly** | One PR strand; no roadmap item. Proceed to operation 5 (dispatch in DAG order). |
| **Q1** — extend NFR-003's tool matrix | **No** (default, stated to the operator and not contested) | Out of scope; a follow-up issue if wanted. |
| **Q2** — hook mechanism | **`language: docker_image`** | The only measured form that pins *both* tools (R3). Accepted cost: these become the repository's first `docker_image` hooks, so a local commit then requires a running Docker daemon. |
| **Q3** — SC2034 in `dev-teardown.sh:7` | **Delete `RED`** (default, stated and not contested) | Matches the issue's wording. |
| **Q4** — add the gates to `task check` | **Yes — WP-5 is in scope** | Closes the divergence `task check`'s own comment warns about ("SKIPPED IS FAIL"). |

**Specialist resolution (runtime lookup, not inherited from the plan).** The
`nolte-shared` agent catalog was enumerated at dispatch time: all 18 entries are
reviewers or scanners, none implements. The implementing specialists come from
`nolte-engineering`. WP-1, WP-2, WP-3 and WP-5 route to
`nolte-engineering:fullstack-developer`. **WP-4 has no matching specialised agent** —
`quality-gate-enforcer` is the nearest by subject but is read-only by its own
description ("audits the wiring, never runs it"), which disqualifies it for a
demonstration whose entire point is execution. WP-4 is therefore generalist
remediation and the PR's Risk / rollout notes must say so.

### WP-3 — result (dispatched to `nolte-engineering:fullstack-developer`)

**Done.** `scripts/check_workflow_gate_integrity.py`, +23 / −0 lines, docstring only
(`--numstat` = `23 0`, so a behavioural change is excluded by construction).

The specialist **re-measured the probe table rather than inheriting it** — which the
brief demanded, because the table is the package's entire content. It held, and was
sharpened on three points that were not in the brief:

- Probe C stays silent **even under `--enable=all`** (exit 0). This closes the obvious
  rebuttal that some optional check merely needs enabling: there is none.
- The boundary was additionally measured **end-to-end through actionlint**, not only
  through bare shellcheck — that is the path the repository will actually run, since
  actionlint extracts `run:` blocks and prepends a wrapper. Identical result: probes A
  and B are reported, C produces no line.
- Counter-check on the structural claim: `scan_continuations` fires **identically on
  all three probes**, so "shellcheck keys on what follows, this guard keys on the
  structure" is established rather than asserted.

**Correction carried into the docstring.** The brief's phrasing implied case C goes
unnoticed. It does not: the truncated command still runs, exits 127 and reddens the
step, exactly as in A and B. The difference is purely **static** — only in C is there
no signal *before* it lands. The docstring says "no static signal at all", not "silent".

**Gate:** guard exits 0 ("19 justified site(s)"); 26/26 unit tests pass; ruff check and
ruff format clean.

**Carried forward to WP-2 (established, from this run):** `actionlint` requires a git
repository in the working directory — without one it exits 3 before checking anything.
Relevant to how the hook is invoked.

### WP-1 — result (dispatched to `nolte-engineering:fullstack-developer`)

**Done**, no refutation of the dispositions: all three findings were nits, none hid a
defect. `shellcheck 0.11.0 --severity=warning` over the same 21 files, same invocation:
**exit 1 with three findings → exit 0 with none**. Rot-zuerst by construction, so the
green is not vacuous.

**One instruction of this orchestration was wrong, and the specialist caught it.** WP-1's
brief and R4 both read as if `# shellcheck disable=SC2088` belonged immediately above
`worktree_add.sh:69`. Placed there it **breaks the file** — `SC1124` ("directives are
only valid in front of complete commands like `case` statements, not individual case
branches") plus `SC1073`. It belongs before the whole `case` (line 67), which then also
covers the `"~")` branch: a precision loss the tool forces rather than a choice. R4 in
`project/requirements/ci-actionlint-shellcheck.md` has been corrected accordingly, so the
false instruction does not survive in the durable artifact.

**AK 2 was proved through the production path, with a negative control.** The claim at
risk was that `export UID GID="$(id -g)"` must keep both variables reaching the eight
`user: "${UID:-1000}:${GID:-1000}"` interpolations in `docker-compose.e2e.yml`. Rather
than reading the file, the specialist ran the **real** `scripts/run-e2e.sh --smoke` with a
`docker` stub first on `PATH` that dumps its own process environment — verbatim the
environment compose interpolates from:

| run | UID/GID seen by compose |
|---|---|
| post-fix | `GID=1000`, `UID=1000` |
| pre-fix (`git show HEAD:…`) | identical → behaviour preserved |
| **mutant** (`export GID` only) | `GID=1000` alone → the oracle notices the absence |

Without the third row the positive result would certify nothing.

**Gate:** shellcheck 21/21 clean; `bash -n` on all three scripts; `pre-commit run --files`
green including `no CI gate that cannot fail (NFR-018 §2)`.

**Process finding, recorded against this orchestration rather than the package.** WP-1 and
WP-3 were dispatched **concurrently into one shared worktree**. They happened to touch
disjoint files, so nothing was lost — but the repository's own rule is that writing agents
on a shared tree run sequentially, and WP-1's report is what surfaced it. Remaining
dispatches in this run are sequential.

### WP-2 — result (dispatched to `nolte-engineering:fullstack-developer`)

**Done.** `.pre-commit-config.yaml` only, +102 / −0: `rhysd/actionlint@v1.7.12`
(`actionlint-docker`) and `koalaman/shellcheck-precommit@v0.11.0` (`--severity=warning`),
placed after `workflow-gate-integrity`, its closest thematic neighbour.

**Acceptance met on the sharpened criterion, not on "green".** `CI=true pre-commit run
--all-files` → exit 0, 47/47 `Passed`, and both new hooks appear **by name**:

    actionlint + bundled shellcheck over .github/workflows/ (#1295)....Passed
    ShellCheck v0.11.0.................................................Passed

A bare run without `CI` exits 1 on `frontend-eslint`, `frontend-tsc`, `nuclei-validate` —
**pre-existing and environmental**: those hooks refuse to claim a check they cannot run
(#814) when `node_modules` and `nuclei` are absent. `CI=true` is the lane's real
environment, not a weakened gate.

**Non-vacuity controls, all measured:** the pinned actionlint image reports `SC2215` on the
#1010 form (so the shellcheck integration is live, not merely configured); `types: [shell]`
selects exactly the 21 own `*.sh` and no extensionless indexed file has a shell shebang;
actionlint selects the 24 files under `.github/workflows/`; `shellcheck --severity=warning`
over all 21 scripts exits 0, so R4's precondition holds and the gate may be armed; the
severity asymmetry was reproduced (`sort f > f` → actionlint exit 1 at `info`, the same
construct in a `.sh` exit 0 at `warning`) and is named in the comment block; both upstream
hooks resolve to literal tags at those revs, never `latest`.

**Refinement of a fact this orchestration carried in, not a refutation.** "actionlint needs
a git repository, else exit 3" holds only for a mount with **no `.git` marker at all**
(reproduced: exit 3, `no project was found`, nothing checked — a silent-green shape if the
exit code is ever swallowed). It needs a marker, not a resolvable repository: with this
worktree's `.git` *file* pointing at a gitdir absent inside the container, actionlint checks
normally. Recorded in the hook's comment block, because it is a live hazard for anyone
re-wiring this as a `docker run` in a Taskfile.

**Accepted residual (RK-2), named in the comment block:** `rev:` binds an image *tag*, not a
digest. Digest-pinning would require a local hook and forfeit the Renovate coverage R3's
maintenance story rests on (#1079 precedent).

**Raised for the verify gate:** these are the repository's first `docker_image` hooks — two
third-party images pulled by tag during a *required* check. That is a new supply-chain
surface and the reason `security-review` runs before the PR opens.

### WP-5 — result (dispatched to `nolte-engineering:fullstack-developer`)

**Done, and the hypothesis was partially refuted.** `.taskfiles/checks.yaml` only, +81 / −5:
a new `check:workflow-shell-lint` target that delegates to the pre-commit hooks
(`pre-commit run --all-files <hook-id>` per hook), wired into `task check` as its own
category, table row and summand.

Both options the brief offered were rejected, each against a measurement. Hand-written
`docker run` invocations: the pins, the file selection (`types: [shell]`, `files:`) and the
`--severity=warning` floor live in `.pre-commit-config.yaml` and are maintained there by
Renovate — a second copy would be a second truth, and would additionally have to know
WP-2's exit-3 trap. Delegating wholesale to `task precommit`: the suite is 47 hooks and
includes `ESLint (frontend)`, `TypeScript check (frontend)` (already separate table
categories — one tool, two verdicts) and `Nuclei template validate` (needs a local binary).
The per-hook form keeps one truth without the suite explosion, and it fails loudly on
drift: `pre-commit run no-such-hook-id --all-files` exits 1 with `No hook with id …`, so a
renamed hook cannot silently stop running. Additionally measured, unprompted: pre-commit
returns **exit 0** on `(no files to check)` — the vacuous green `task check`'s own comment
rejects — so the target treats `Skipped` as FAIL.

**Falsification executed, three probes.** (a) An injected `SC2155` in `scripts/dev-setup.sh`
moved the table row PASS → **FAIL** → PASS and the target's exit code 0 → 1 → 0, with file
and line in the output; `custom gates (7)` stayed PASS in both, so the reddening is
attributable to the new category. (b) Probe D (`sort probe.txt > probe.txt` in a workflow
`run:` block) rather than the #1010 form, precisely because the #1010 form is confounded:
actionlint exit 1 with `SC2094:info`, while `check_workflow_gate_integrity.py` stayed exit
0 — only the new half sees it, and the threshold asymmetry is thereby reproduced live.
(c) The `Skipped` branch, reached by changing exactly one line of the shipped script
(mechanically verified: `differing lines: 1`).

**Self-reported error, recorded because it is the expensive class.** The specialist's *first*
probe put `--files README.md` before the hook id; `--files` takes `nargs='*'` and swallowed
it, so pre-commit ran the whole suite, whose output is full of foreign `Skipped` lines. The
branch would have fired even had the named hook passed — "the test reaches the rule by a
different path than production". Only the corrected probe certifies anything.

**Acceptance met in part — the residual is stated, not glossed.** "…then reverting makes
`task check` pass again" was **not** observed: `task check` reports FAIL in this worktree for
pre-existing environment reasons (no `src/frontend/node_modules`; `boto3` absent from the
active interpreter → 3 failures in `test_s3_adapter.py`, a known local gap). What *was*
observed is the PASS→FAIL→PASS transition and exit 0→1→0 of
`task check:workflow-shell-lint`, i.e. exactly the command `task check` runs. That this row
feeds the aggregate exit code is **constructive** (`overall=$(( … + shelllint ))`, one line
in the diff) and **unestablished by measurement**. The observation that would settle it:
`(cd src/frontend && npm ci)` plus `boto3` in the active interpreter, then one clean and one
injected `task check`. The second half was not done because it would install into the user's
global asdf environment outside this worktree.

**Tree unchanged after the probes:** `git status --porcelain -uall` and `--numstat` identical
to the starting state; WP-1/WP-2/WP-3 diffs byte-for-byte intact.

### WP-4 — result (generalist remediation, no matching specialised agent)

**Executed, zero permanent diff.** All three probes ran through the lane's real invocation,
`CI=true pre-commit run --all-files`. Baseline before any injection: **47 hooks, all
`Passed`, none `Skipped`** — including the three that refuse to run without `CI` (#814).

| Probe | injection | lane | who reported |
|---|---|---|---|
| 1 — the #1010 form | comment between continued lines in `security-nuclei-nightly.yml` | exit 1 | **both**: `workflow-gate-integrity` (`:202 … runs truncated`) *and* `actionlint-docker` (`SC2215`) |
| D — attributable | `sort probe.txt > probe.txt` in `backend.yml` | exit 1 | **only** `actionlint-docker` (`SC2094:info` ×2); the guard measured separately at exit 0 **before** the lane run |
| 3 — shell | this branch's own SC2155 fix reverted in `run-e2e.sh` | exit 1 | **only** `ShellCheck v0.11.0`; actionlint `Passed` |

Probe 1 is labelled confounded, as designed. It was **deconfounded** by running the new half
in isolation — `CI=true pre-commit run actionlint-docker --all-files` → `Failed`, exit 1 —
which establishes that actionlint catches the #1010 form on its own, independently of the
pre-existing guard.

**Partial refutation of R6's reading, produced unprompted and at the fracture line.** The
third variant from `scan_continuations`' docstring — a bare positional after the comment —
was pushed through the lane, where it had previously only been measured against the image:
`actionlint-docker` → **`Passed`**; `workflow-gate-integrity` → **`Failed`**. So R6 is true
as worded but must not be read as "actionlint catches the #1010 form": which half carries it
depends on what follows the `#`. R6 in `project/requirements/ci-actionlint-shellcheck.md`
has been corrected accordingly. The same run establishes **R5's complementarity through the
lane**, upgrading it from an image-level to a lane-level claim.

**Restoration verified three ways:** `git status --porcelain -uall` and `git diff --numstat`
identical to baseline; `sha256sum -c` clean over all four touched files; and the final full
lane run is **byte-identical in all 47 verdict lines** to the baseline run (`cmp` OK).
Rollback was done from pre-saved copies rather than `git checkout`, which would have
destroyed this branch's uncommitted work in `run-e2e.sh`.

**Not measured, stated rather than glossed:** the **cold-pull cost** of the two
`docker_image` hooks in the `static` lane. Both images were warm locally (~0.87 s / ~0.91 s
warm, measured in WP-2). This is the one cost of the change for which no figure exists; the
observation that would settle it is the first CI run of the `static` lane on this branch.
