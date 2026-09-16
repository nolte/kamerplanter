# Gruppe `2026-09-16-backend-lane-execution`

Status: freigegeben 2026-09-16 · Scheibe 1+2 (#1434-Rest) startbar · Scheibe 3 (#1432) nach Merge von PR #1459

Gemessen gegen `origin/develop` @ `87c82ae25` (2026-09-16).

## Die Frage, auf die die Research-Phase gescoped war

Wenn ein Backend-Test-Tier grün meldet — was beweist das darüber, ob es gelaufen ist?

## Die eine logische Änderung

Ein Backend-Testlauf schlägt fehl, wenn sein Tier nicht wirklich ausgeführt hat — in CI
für `tests/integration/`, lokal für den falschen Interpreter, und in jedem Tier für
eine Skip-Zahl über der bekannten.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1432** | `cicd`, `backend`, `test` | thematische Kopplung | `.github/workflows/backend.yml:197-208` benennt die Auslassung des Integration-Tiers samt Self-Skip-Begründung wörtlich: „would report green having tested almost nothing" |
| **#1434-Rest** | `backend`, `test` | thematische Kopplung | derselbe Satz für das Unit-Tier: der globale Interpreter lässt 28 Tests lautlos überspringen, nur 3 fallen laut (Projektgedächtnis, #1434) |

Beide Mitglieder ändern dieselbe Capability: die **Ausführungs-Zusicherung** der
Backend-Test-Tiers. Punkt 2 von #1434 (`importorskip`) ist durch #1435/#1439 erledigt
und **nicht** Mitglied; der Issue-Körper wurde per Kommentar am 2026-09-16 auf Punkt 1
und 3 geschrumpft.

## Was gemessen wurde

### Das Integration-Tier läuft in keinem Gate — und würde ohne Datenbank grün melden

- `grep -rn "arangodb" .github/workflows/` → **null Treffer.** Kein Workflow startet je
  einen ArangoDB-Service.
- `.taskfiles/backend.yaml:51-56`: „`tests/integration/` stays out and therefore runs
  LOCALLY ONLY … It would not go red without one: every module is
  `skipif(not ARANGO_AVAILABLE)`, so on a runner it would report green having skipped
  29 of 36 cases." `.taskfiles/checks.yaml:264-265` sagt dasselbe für `task check`.
- **Es gibt keine `tests/integration/conftest.py`.** 13 Module definieren je ihren
  **eigenen** `ARANGO_AVAILABLE`-Probe (`test_arango_integration.py:9`,
  `test_aql_reference_normalisation.py:37-43`, …). Der Self-Skip ist also 13-fach
  kopiert, nicht zentral — ein Modul, das die Probe vergisst, fällt bei fehlender DB
  laut, alle anderen still.
- 90 Tests in 11 Dateien (`grep -c "def test_"`), die zusammen die einzige Prüfung
  der Repository-/AQL-Schicht gegen eine echte Datenbank sind. Scheibe 1 der Gruppe
  `task-photo-refs` hat heute gemessen, was das bedeutet: 31 Fälle des
  Normalisierungs-Wächters überspringen sich ohne DB **lautlos**.

### Der Interpreter-Guard fehlt

`grep -n "sys.prefix\|VIRTUAL_ENV\|base_prefix" src/backend/tests/conftest.py` →
**null Treffer.** Die Suite hat keine Möglichkeit zu bemerken, dass sie im falschen
Interpreter läuft. Dass genau das 28 Tests lautlos überspringen lässt, ist gemessen
(#1434; die vier Entwickler-Läufe heute mussten je ein Worktree-venv anlegen, weil
das Primär-venv per Editable-Install den **falschen Baum** importiert hätte).

### Kein Skip-Floor in keinem Tier

`grep -n "addopts\|-rs\|--strict" src/backend/pyproject.toml` → null Treffer. Kein Tier
kennt seine erwartete Skip-Zahl; `backend.yml:200-201` hält die API-Tier-Zahl
(„480 passed, 0 skipped") nur als **Prosa** fest, nichts prüft sie.

### Abhängigkeit außerhalb der Gruppe: #1436

`tests/integration/test_care_task_dedup_concurrency.py` hat den Defekt aus #1436
gemessen (Verlierer eines Insert-Rennens bekam eine rohe `DocumentInsertError`). Der
Fix liegt als **PR #1459** vor, ist aber noch nicht gemergt. Eine Integration-Lane, die
vor diesem Merge scharf geht, rötet auf einen bekannten Defekt. Reihenfolge deshalb:
#1434-Rest zuerst, #1432 nach dem Merge von #1459 (Rebase des Integrationsbranches).

## Strukturbefund über die Mitglieder hinweg (§E)

**Klassifikation: Klassen-Cluster.** Defektklasse: **eine Lane, die grün meldet, ohne
gelaufen zu sein** — NFR-018 §1 („a check that cannot fail must not exist"). Drei
Formen in dieser Gruppe: das Tier läuft nirgends (#1432), der Interpreter ist ein
anderer als gedacht (#1434.1), Skips zählen wie Bestehen (#1434.3). Alle drei haben
denselben Beleg-Fehler: die Zahl der ausgeführten Tests ist nirgends ein Vertrag.

Verwandt, nicht Mitglied: #1406 (Opt-in-Liste der Seed-Schema-Hooks) und #1405
(Falsifizierbarkeits-Fähigkeit) tragen dieselbe Klasse mit disjunkter Fläche.

### Prozessbefund

Keiner über #1456 hinaus. Die drei Prosastellen, die das fehlende Tier ehrlich
benennen (`backend.yml:204`, `backend.yaml:51`, `checks.yaml:264`), sind die vierte
Fundstelle von #1456 — bereits dort geführt.

## Stufe und Scheiben

**Stufe 2.** CI-Verdrahtung und Test-Harness; kein veröffentlichter Vertrag, keine
Repository-Grenze.

**Unabhängig verifizierbare Scheiben:**

1. **Scheibe 1 — #1434-Rest, Teil a: der Interpreter-Guard.** Ein Session-Start-Hook in
   `tests/conftest.py`, der prüft, dass `app` aus **diesem** Baum importiert wird
   (`Path(app.__file__)` liegt unter dem Repo-Wurzelpfad der conftest) und dass der
   Interpreter ein Projekt-venv ist (`sys.prefix != sys.base_prefix`, oder `uv run`).
   Verletzung → **Session-Fehler mit Pfad und Erwartung**, kein Skip. Rot zuerst:
   `python3 -m pytest tests/unit -q` mit dem globalen Interpreter muss sofort laut
   scheitern, nicht 28 Tests überspringen.
2. **Scheibe 2 — #1434-Rest, Teil b: der Skip-Floor.** Eine pytest-Option
   `--max-skipped N` (conftest), die den Lauf rötet, wenn mehr Tests übersprungen
   wurden als deklariert. Jedes Tier-Target in `.taskfiles/backend.yaml` deklariert
   seine **gemessene** Zahl (heute: `unit` 1 — welcher? benennen —, `api` 0,
   `contracts` 0, `integration` 0). Rot zuerst: `tests/integration/` ohne DB mit
   `--max-skipped 0` → rot. Der Skip-Grund muss im Fehler stehen (`-rs`-Ausgabe
   einbetten), sonst weiß niemand, welcher Skip neu ist.
3. **Scheibe 3 — #1432: die Integration-Lane.** `backend.yml` bekommt einen Job mit
   `services: arangodb` (Image auf denselben Tag wie der Dev-Stack, per Digest gepinnt,
   in einer Renovate-Gruppe), Umgebungsvariablen so, wie die 13 Proben sie lesen, und
   `task test:backend:integration` (neu) mit `--max-skipped 0`. Die 13 Proben werden
   durch **eine** `tests/integration/conftest.py` ersetzt, die bei fehlender DB nicht
   skippt, sondern **fehlschlägt** — lokal bleibt ein Opt-out per Marker möglich, in
   CI nicht. Die drei Prosastellen (`backend.yml:204`, `backend.yaml:51`,
   `checks.yaml:264`) werden umgeschrieben. **Voraussetzung:** PR #1459 ist gemergt und
   in den Integrationsbranch rebased; die Lane läuft vor dem Scharfschalten dreimal
   per `workflow_dispatch`, die Ausgaben stehen im Artefakt.

**Verifikationsdurchgang durch einen fremden Kontext:** `code-review` gegen den Kopf
des Integrationsbranches nach Scheibe 3.

## Modus

**Modus B — Sub-Branch je Mitglied.** Begründung: #1432 hängt von etwas **außerhalb der
Gruppe** ab (Merge von PR #1459) und seine Abnahme ist unsicher — das Tier ist in CI
nie gelaufen; Flakes, die es dort zeigt, sind nicht Sache dieser Gruppe. #1432 muss
herauslösbar bleiben, ohne den Interpreter-Guard und den Skip-Floor mitzureißen.

## Reihenfolge

1. **#1434-Rest** (Scheiben 1 + 2) — unabhängig, sofort.
2. **#1432** (Scheibe 3) — nach Merge von #1459.

## Vollständigkeitsmatrix

Spalten wie in den anderen Gruppen aus dem Repository abgeleitet.

| Mitglied | Backend-Quellcode | Frontend-Quellcode | Spec | Tests | Doku | Config / Workflows | Generierter Katalog |
|---|---|---|---|---|---|---|---|
| **#1434-Rest** | *nicht zutreffend* — kein `app/`-Code | *nicht zutreffend* | `spec/nfr/NFR-008*.md` (Teststrategie) — Skip-Floor als Tier-Vertrag; Prüfung: `task precommit` | `tests/conftest.py` Interpreter-Guard + `--max-skipped`; Selbsttests unter `tests/unit/guards/`, die beide Mechanismen mit einem künstlichen Skip bzw. einem gefälschten `sys.prefix` rot machen (Mutationsbeweis); Prüfung: `pytest tests/unit/guards/` | `docs/de+en/development/testing/index.md` — Aktivierungsschritt wird durch den Guard erzwungen; Prüfung: `task docs:build` | `.taskfiles/backend.yaml` — `--max-skipped` je Tier; `backend.yml` — dieselben Zahlen; Prüfung: `actionlint` + ein Lauf je Tier mit Ausgabe | *nicht zutreffend* |
| **#1432** | *nicht zutreffend* | *nicht zutreffend* | `spec/nfr/NFR-008*.md` — Tier-Karte: Integration läuft in CI; Prüfung: `task precommit` | `tests/integration/conftest.py` ersetzt 13 Proben; Prüfung: `pytest tests/integration/ --max-skipped 0` gegen `docker run arangodb` lokal, Ausgabe | `docs/de+en/development/testing/index.md` — Tier-Karte; Prüfung: `task docs:build` | `backend.yml` neuer Job + `services:`, `.taskfiles/backend.yaml` neues Target, `checks.yaml:264` Prosa, `renovate.json5` Gruppe für das Service-Image; Prüfung: 3× `workflow_dispatch` grün mit `skipped=0` in der Ausgabe | *nicht zutreffend* |

## Risiken

- **Der Skip-Floor kann eine legitime Skip-Zahl einfrieren.** Wer einen neuen,
  begründeten Skip einführt, muss die Zahl im Taskfile heben — das ist gewollt: der
  Skip wird eine sichtbare Entscheidung. Die Fehlermeldung muss den neuen Skip-Grund
  nennen, sonst wird die Zahl blind gehoben.
- **Das Integration-Tier ist in CI nie gelaufen.** Timing-sensitive Tests
  (`test_care_task_dedup_concurrency.py`) können auf einem Runner anders ausgehen als
  lokal; das Projektgedächtnis hält fest, dass „lokal grün" solche Tests nicht
  entlastet. Deshalb drei Dispatch-Läufe vor dem Scharfschalten, und Modus B.
- **Der Interpreter-Guard darf `uv run` nicht ausschließen.** `uv run --locked` setzt
  `sys.prefix` auf das Projekt-venv; ein Guard, der nur `VIRTUAL_ENV` prüft, wäre unter
  `uv run` rot. Die Prüfung ist „`app` kommt aus diesem Baum", nicht „ein bestimmter
  Aktivierungsmechanismus".
- **Gruppe `uv-lock-chain` ändert `.taskfiles/backend.yaml` ebenfalls** (Scheibe 5,
  `uv run --locked`). Geteilte Fläche zwischen zwei Gruppen → die zweite, die mergt,
  rebased; die Zeilen sind disjunkt (Interpreter-Aufruf vs. pytest-Argumente).

## Bewusst außerhalb des Scopes

- **Flakes, die die neue Lane in `tests/integration/` sichtbar macht**, werden
  gemeldet, nicht in dieser Gruppe repariert; jeder ist ein eigenes Issue mit der
  Lane-Ausgabe als Beleg.
- **`tests/integration/` in `task check`** (die schnelle lokale Schleife) bleibt
  draußen — es braucht eine DB, und `checks.yaml:264` begründet das richtig; nur die
  Prosa „self-skips" wird angepasst.
- **Backend-`mypy` in ein Gate** (`checks.yaml:266-268`, 2124 vorbestehende Fehler) —
  dieselbe Klasse, eigenes Issue, nicht hier.
- #1405 und #1406 — dieselbe Defektklasse, disjunkte Fläche; Einzelläufer.

## Operator-Entscheidungen (2026-09-16, vor der Umsetzung)

1. **Die Integration-Lane wird sofort Pflicht-Check** — gegen die Empfehlung
   „advisory für zwei Wochen". Konsequenz: die drei `workflow_dispatch`-Läufe vor dem
   Scharfschalten sind nicht optional, und die Aufnahme in
   `required_status_checks.contexts` (Branch-Protection `develop`) ist Teil von
   Scheibe 3 — sie wird **nach** grünen Dispatch-Läufen gesetzt, nicht davor, und der
   `gh api`-Aufruf samt Antwort steht im Artefakt. Ein Flake im nie gelaufenen Tier
   blockiert damit sofort jeden Merge; das ist die bewusst akzeptierte Kante.
2. **Skip-Floor: harte gemessene Zahl je Tier + Skip-Gründe im Fehler.** Jeder neue
   Skip hebt die Zahl im Taskfile sichtbar; die Fehlermeldung nennt den neuen Grund.

## Ergebnisse je Scheibe

### Scheibe 1 — Interpreter-Guard (#1434 Punkt 1)

Umgesetzt auf `fix/1434-tier-execution-guards`. Prädikate in
`src/backend/tests/support/execution_guards.py`, Verdrahtung in
`src/backend/tests/conftest.py` (`pytest_configure` → `pytest.UsageError`).
Die Wurzel wird per Aufwärtssuche nach `pyproject.toml` bestimmt, nicht per
`parents[N]`.

**Rot zuerst — globaler Interpreter, vor dem Guard** (`python3 -m pytest tests/unit -q -rs`,
`sys.prefix == sys.base_prefix == /home/nolte/.asdf/installs/python/3.14.6`):

```
5 failed, 8596 passed, 1 skipped, 28 warnings, 27 errors in 440.32s (0:07:20)
SKIPPED [1] tests/unit/migrations/test_e2e_admin_env_containment.py:86: the file that is allowed to set them
```

**Befund, der die Issue-Diagnose korrigiert:** die im Issue und in dieser Analyse
zitierten „28 lautlos übersprungenen Tests" sind heute **nicht mehr
reproduzierbar**. #1435/PR #1439 hat die betroffenen `importorskip`-Aufrufe in
harte Importe überführt; der globale Interpreter fällt deshalb inzwischen laut
aus (27 Setup-Errors + 5 Failures, sämtlich `moto`/`boto3` fehlt), und es bleibt
**genau 1** Skip übrig — derselbe, den auch das Projekt-venv hat. Der verbleibende
Schaden ist damit nicht „stille Skips", sondern 7:20 min Laufzeit für ein
Ergebnis über den falschen Paketstand. Der Guard bleibt trotzdem richtig: er
beendet dasselbe Szenario **sofort** und benennt die Ursache, statt sie über 32
Einzelfehler zu verteilen.

**Grün danach — derselbe Aufruf, nach dem Guard** (Abbruch nach ~1 s, `exit=4`):

```
ERROR: This pytest session is running on the wrong interpreter (#1434).

  sys.executable    : /home/nolte/.asdf/installs/python/3.14.6/bin/python3

  1. the interpreter is not a virtual environment, so its packages are not
    the hash-verified set the lock installs.
    sys.prefix      : /home/nolte/.asdf/installs/python/3.14.6
    sys.base_prefix : /home/nolte/.asdf/installs/python/3.14.6
    Expected these to differ (any project virtual environment).

Run the suite from this checkout's own environment:
    cd src/backend
    uv sync --locked --extra dev      # or: task deps:sync
    .venv/bin/python -m pytest <tier>
`uv run --locked python -m pytest <tier>` is equivalent — measured on 2026-09-16,
it points sys.prefix at this project's .venv.
```

**Der zweite vorgesehene Rot-Fall trat nicht ein — gemessen, nicht angenommen.**
Die Erwartung war, dass das Primär-venv aus diesem Worktree per Editable-Install
den **fremden** Baum importiert. Unter pytest passiert das nicht: weil `tests/`
ein Paket ist, legt pytest die Paketwurzel `src/backend` **dieses** Worktrees auf
`sys.path[0]`, bevor die conftest importiert wird, und beschattet damit den
Editable-Finder. Gemessen mit einer Sonde in `tests/unit/`:

```
$ cd <worktree>; /home/nolte/repos/github/kamerplanter/src/backend/.venv/bin/python \
      -m pytest src/backend/tests/unit/test_zz_tmp_probe.py -q -s
APP: /home/nolte/repos/.worktrees/kamerplanter/g3-1434/src/backend/app/__init__.py
PREFIX: /home/nolte/repos/github/kamerplanter/src/backend/.venv
```

Der fremde Baum wird nur **außerhalb** von pytest importiert
(`cd /tmp && <primär-venv>/bin/python -c "import app"` →
`/home/nolte/repos/github/kamerplanter/src/backend/app/__init__.py`). Die
Baum-Prüfung des Guards ist damit korrekt, aber in der heutigen Pytest-Konfiguration
nicht die Prüfung, die das Primär-venv fängt; was es fängt, ist der #1435-Wächter
`test_this_environment_can_judge_the_rule_at_all`, der dort laut auf fehlendes
`jsonschema` fällt (das Primär-venv ist veraltet). Eine Prüfung „`sys.prefix`
liegt unter der Repo-Wurzel" wäre der Griff, der auch diesen Fall fängt — sie ist
**bewusst nicht** gebaut, weil sie genau die von den Risiken verbotene Form hätte
(„ein bestimmter Aktivierungsmechanismus") und ein legitimes venv außerhalb des
Baums abweisen würde. Offen als eigene Entscheidung.

**`uv run` bleibt zugelassen — gemessen, nicht angenommen:**

```
$ uvx --from 'uv==0.12.15' uv run --locked python -c "import sys, app; ..."
prefix: <worktree>/src/backend/.venv
base:   /home/nolte/.local/share/uv/python/cpython-3.14.2-linux-x86_64-gnu
app:    <worktree>/src/backend/app/__init__.py
$ uv run --locked python -m pytest tests/contracts -q --max-skipped 0   →  exit=0
```

**Mutationsbeweis** (Bedingungen in `interpreter_violation` invertiert:
`if resolved_app.is_relative_to(root)` und `if ... != ...`): die Session bricht
mit genau der Guard-Meldung ab, d. h. `tests/unit/guards/` wird als Ganzes rot.
Zweite Mutation (`pytest_configure` erhebt keinen `UsageError` mehr):

```
FAILED tests/unit/guards/test_execution_guards.py::TestInterpreterGuardIsWired::test_faked_system_prefix_aborts_the_session
FAILED tests/unit/guards/test_execution_guards.py::TestInterpreterGuardIsWired::test_faked_foreign_app_file_aborts_the_session
2 failed, 17 passed
```

### Scheibe 2 — Skip-Floor (#1434 Punkt 3)

`--max-skipped N` in `tests/conftest.py` (`pytest_addoption` +
`pytest_sessionfinish`, das `session.exitstatus` setzt); die Meldung bettet die
`-rs`-Zeilen gruppiert mit Zähler ein.

**Gemessene Skip-Zahlen je Tier** (2026-09-16, Projekt-venv, `pytest <tier> -q -rs`):

| Tier | Ausgabe | Skips | Grund |
|---|---|---|---|
| `tests/unit/` | `8628 passed, 1 skipped in 279.17s` | **1** | `tests/unit/migrations/test_e2e_admin_env_containment.py:86` — `test_no_other_configuration_file_sets_the_e2e_admin_credentials` ist über jede Konfigurationsdatei parametrisiert und überspringt die eine erlaubte (`the file that is allowed to set them`). Der Skip **ist** die Allowlist → dauerhaft |
| `tests/contracts/` | `27 passed in 0.95s` | **0** | — |
| `tests/api/` | `1342 passed in 176.25s` | **0** | — (die Prosa in `backend.yml` nannte 480 — der Tier ist seitdem gewachsen) |
| `tests/unit/api` + `tests/unit/guards` (Pflicht-Lane) | `361 passed in 17.82s` | **0** | — |
| `tests/integration/` ohne DB | `7 passed, 136 skipped in 162.76s` | **136** | 13 kopierte `ARANGO_AVAILABLE`-Proben |

**Rot zuerst — `tests/integration/` ohne DB mit `--max-skipped 0`** (`exit=1`,
vorher `exit=0`):

```
============================= skip floor exceeded ==============================
This run skipped 136 tests; the tier declares at most 0 (--max-skipped 0).
A skipped test reports like a passed one, so a tier that quietly stopped executing would otherwise be green (#1434).

  SKIPPED [10] .../tests/integration/test_aql_reference_normalisation.py:113: ArangoDB not available on localhost:8529
  SKIPPED [10] .../tests/integration/test_aql_reference_normalisation.py:124: ArangoDB not available on localhost:8529
  SKIPPED [1]  .../tests/integration/test_aql_reference_normalisation.py:135: ArangoDB not available on localhost:8529
  ...

If a skip above is new and justified, raise the number where the tier declares it
(.taskfiles/backend.yaml) in the same change that introduces it — that keeps the
skip a visible decision. If it is not justified, the tier stopped running
something it is meant to run.

7 passed, 136 skipped in 162.65s (0:02:42)
```

**Grün danach — die drei Tier-Targets mit ihrer deklarierten Zahl:**

```
task test:backend:unit       → 8647 passed, 1 skipped in 1054.07s   exit=0
task test:backend:contracts  →   27 passed in 1.91s                 exit=0
task test:backend:api        → 1342 passed in 190.00s               exit=0
KAMERPLANTER_MODE=full pytest tests/unit/api tests/unit/guards -q --max-skipped 0
                             →  361 passed in 16.77s                exit=0
```

**Mutationsbeweis** (in `skip_floor_violation`):

```
# `>` → `>=`  (d. h. `len(reasons) <= max_skipped` → `< max_skipped`)
FAILED ...TestSkipFloorViolation::test_no_skips_at_all_passes
FAILED ...TestSkipFloorViolation::test_exactly_the_declared_number_passes
FAILED ...TestSkipFloorEndToEnd::test_the_declared_number_keeps_the_run_green
3 failed, 16 passed

# Floor feuert nie
FAILED ...TestSkipFloorViolation::test_one_above_the_declared_number_fails
FAILED ...TestSkipFloorViolation::test_every_reason_is_named_so_the_new_skip_is_identifiable
FAILED ...TestSkipFloorViolation::test_identical_reasons_are_grouped_with_a_count_like_rs
FAILED ...TestSkipFloorEndToEnd::test_a_skip_above_the_floor_reddens_the_run_and_prints_the_reason
4 failed, 15 passed

# `session.exitstatus` wird nicht gesetzt (Verdrahtung statt Prädikat)
FAILED ...TestSkipFloorEndToEnd::test_a_skip_above_the_floor_reddens_the_run_and_prints_the_reason
1 failed, 18 passed
```

Die beiden Endpunkte der Vergleichsgrenze sind damit beidseitig festgenagelt:
Floor 1 bei genau 1 Skip muss **grün** bleiben, Floor 0 bei 1 Skip **rot** werden.

### Ruft CI die Targets oder inlined es pytest?

Gemessen (`grep -n "pytest\|task test" .github/workflows/*.yml .taskfiles/*.yaml`):

- **`backend.yml` ruft die Targets** (`task test:backend:unit` / `:contracts` /
  `:api`, Zeilen 187/195/208). Die Zahlen leben deshalb an **einer** Stelle,
  `.taskfiles/backend.yaml`; eine Umstellung ist nicht nötig.
- **`backend-guards.yml` inlined** (`pytest tests/unit/api tests/unit/guards -q`,
  Zeile 124) — die Pflicht-Lane. Dort ist `--max-skipped 0` in dieselbe Zeile
  gesetzt (gemessen 0 Skips). Eine Umstellung auf ein Target wäre möglich, ist
  hier aber **nicht** gemacht: die Lane ruft bewusst *Verzeichnisse* statt einer
  gepflegten Liste und mischt zwei Tier-Teilmengen mit eigener `KAMERPLANTER_MODE`-
  Umgebung; ein eigenes Target dafür wäre eine dritte Deklaration derselben
  Grenze. Falls der Operator die Zahl lieber im Taskfile hätte, ist das ein
  Einzeiler — ich habe es nicht ungefragt getan.
- **`.taskfiles/checks.yaml:341`** (`task check`, die schnelle lokale Schleife)
  inlined `python -m pytest tests/unit/ -q` **ohne** Floor. Bewusst gelassen:
  `task check` ist kein Gate, und eine vierte Kopie der Zahl wäre genau die
  Drift-Fläche, die der Vertrag vermeiden soll. Der Interpreter-Guard greift dort
  trotzdem.
- **`backend.yml` Coverage-Lane** (`reusable-python-coverage`) ruft `pytest` bar
  aus dem gesyncten `.venv` — venv, also vom Guard unberührt; ohne `--max-skipped`,
  weil sie die gesamte `testpaths` inkl. `tests/integration/` fährt.

### Scheibe 3 — die Integration-Lane (#1432)

Umgesetzt auf `fix/1432-integration-lane` (Modus B), auf dem PR #1459 (#1436)
enthalten ist.

#### Die neun Proben werden eine Regel

Gemessen, nicht übernommen: es sind **neun** Module mit eigener
`ARANGO_AVAILABLE`-Probe (`grep -rln ARANGO_AVAILABLE tests/integration/`), nicht
dreizehn wie oben geschätzt — verteilt auf 143 Fälle. Das zehnte Modul der Stufe,
`test_perennial_cycle_loop.py`, braucht **keinen** Server (reale Engines gegen
In-Memory-Repositories) und läuft heute wie morgen ungegatet; deshalb hängt das
Gate per `pytestmark = pytest.mark.usefixtures("arango_db")` an den Modulen, die
verbinden, und ist **nicht** autouse über dem Verzeichnis.

Die Adresse war in jeder Kopie ein Literal (`http://localhost:8529`,
`password="rootpassword"`). Jetzt liest `tests/support/arango_integration.py`
`ARANGODB_HOST` / `ARANGODB_PORT` / `ARANGODB_USERNAME` / `ARANGODB_PASSWORD` —
**die Namen von `Settings`** (`env_prefix: ""`), weil ein Teil der Module über ein
echtes `Settings(arangodb_database=…)` + `ArangoConnection` verbindet und der
andere Teil einen `ArangoClient` direkt öffnet. Nur mit denselben Namen zeigen
beide Wege auf denselben Server, wenn CI ihn verschiebt.

`tests/integration/conftest.py` hält die Semantik: `CI` gesetzt → **Fehler** mit
der versuchten Adresse; sonst Skip mit demselben Grund (und `--max-skipped 0` im
Target rötet auch den).

#### Rot zuerst

Vorher, heutiger Code ohne Datenbank (`pytest tests/integration/ -q -rs`,
`exit=0`):

```
7 passed, 136 skipped in 172.27s (0:02:52)
```

Nachher, derselbe Zustand mit `CI=1` (`exit≠0`):

```
7 passed, 136 errors in 23.66s
```

Jeder dieser Fehler trägt die Adresse:

```
ArangoDB did not answer at http://localhost:8529 (database '_system', user 'root'):
ConnectionAbortedError: Can't connect to host(s) within limit (3)
The integration tier measures the repository and AQL layer against a real server;
without one it measures nothing.
Start one with the digest the dev stack and the CI lane share:
    docker run -d --rm --name kp-it-arango -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
or run the dev stack (`task dev:core`). Point the tier elsewhere with
ARANGODB_HOST / ARANGODB_PORT / ARANGODB_USERNAME / ARANGODB_PASSWORD.
```

Nebenbefund, ungeplant und nützlich: der Lauf ohne DB kostet **23 s statt 172 s**.
Die alten Proben liefen zur **Importzeit**, einmal pro Modul, mit je drei
Verbindungs-Retries; die neue Prüfung läuft einmal pro Session.

Lokal ohne `CI` bleibt es ein Skip — gemessen an einem Modul: `1 skipped in 18.39s`
(`exit=0`), mit `CI=1` `1 error in 18.87s`.

#### Drei lokale Läufe gegen eine echte ArangoDB

Container: `arangodb:3.12@sha256:39bbca489179ea03f2b24b7ea4e4c4cb5258f6474f8c1c4d9bd65f7cd6d211a5`
(derselbe Digest wie `docker-compose.yml:24`), `ARANGO_ROOT_PASSWORD=rootpassword`,
`-p 8529:8529`. Aufruf je Lauf: `pytest tests/integration/ -q --max-skipped 0`.

```
Lauf 1:  143 passed, 3216 warnings in 107.09s (0:01:47)   exit=0
Lauf 2:  143 passed, 3216 warnings in 107.03s (0:01:47)   exit=0
Lauf 3:  143 passed, 3216 warnings in  90.88s (0:01:30)   exit=0
```

Skips = 0 in allen drei Läufen (pytest nennt Skips in der Zusammenfassung; hier
steht keine, und `--max-skipped 0` hätte jeden gerötet). **Kein Flake** — auch
nicht in `test_care_task_dedup_concurrency.py`, dem timing-sensitiven Modul, das
#1436 gemessen hat. Das entlastet die Lane auf einem Runner nicht (Projektgedächtnis:
„lokal grün entlastet timing-sensitive Tests nicht"); genau dafür sind die drei
`workflow_dispatch`-Läufe da.

Zusätzlich über das neue Target, das CI aufruft:

```
task test:backend:integration  →  143 passed, 3216 warnings in 44.45s   exit=0
```

Und die Gegenprobe, dass eine vorhandene DB unter `CI` grün bleibt (gegatetes und
ungegatetes Modul zusammen): `8 passed, 169 warnings in 7.15s`, `exit=0`.

#### Die Lane

`backend.yml` bekommt den Job `integration` mit
`name: Integration tests (ArangoDB)` — das ist der Status-Check-Kontext für die
Branch-Protection. Eigener Job statt eines Schritts in `lint-test`: ein
Service-Container, den die anderen drei Tiers nicht brauchen, würde jeden von
ihnen verlangsamen. Schritte wie die Nachbarn (digest-gepinntes Checkout,
`setup-python`, `setup-task`, `python -m pip install 'uv==0.12.15'` +
`uv sync --locked --extra dev` — die **heutige** Form, nicht die von der Gruppe
`uv-lock-chain` geplante), dazu ein begrenztes „Wait for ArangoDB" (60 × 2 s), das
den Fall „Container oben, antwortet nicht" benennt, statt ihn als 136 gleiche
Verbindungsfehler in pytest erscheinen zu lassen.

`workflow_dispatch:` war **nicht** vorhanden (`on:` trug nur `push`,
`pull_request`, `schedule`) und ist ergänzt — ohne das gibt es die drei Läufe vor
dem Scharfschalten nicht.

`paths:`-Filter: `tests/integration/**` und `app/data_access/**` liegen beide
unter dem bestehenden `src/backend/**`; die Lane wird also ausgelöst. Kein
Eintrag nötig, `.github/workflows/backend.yml` steht ohnehin schon in beiden
Filtern.

`actionlint` (pre-commit-Pin `v1.7.12`, `docker.io/rhysd/actionlint`): `exit=0`.

#### Renovate: gemessen statt angenommen

Die Gruppe `{{depName}} image` in `renovate.json5` matcht auf **Paketidentität
allein** (`matchDatasources: ['docker']` + `matchPackageNames: [… 'arangodb' …]`),
ohne `matchManagers` und ohne Dateifilter — genau deshalb wurde sie am 2026-09-10
umgebaut. Ob der Service-Container des Workflows überhaupt extrahiert wird, war
die offene Frage; sie ist jetzt beantwortet:

```
$ npx renovate@41 --platform=local --dry-run=extract
github-actions | .github/workflows/backend.yml | docker | 3.12 | sha256:39bbca489179ea03f2 | service
```

Der eingebaute `github-actions`-Manager liest `jobs.<id>.services.<id>.image`
inklusive Digest (`depType: service`). Der Lane-Digest landet damit im selben
Pull Request wie der compose-Digest; **eine Regel-Ergänzung in `renovate.json5`
war nicht nötig** — ergänzt ist nur der Kommentar, der diese Messung festhält
(`renovate-config-validator`: `Config validated successfully`). Der zunächst
gesetzte Marker-Kommentar `# renovate: datasource=docker depName=arangodb` ist
wieder **entfernt**: er gehört zum Custom-Regex-Manager für Image-Strings in
Workflow-`env:`-Werten und hätte einen Mechanismus behauptet, der hier nicht
arbeitet.

#### Falsifizierbarkeit der neuen Regel

`tests/unit/guards/test_integration_tier_gate.py` (16 Fälle, läuft in der
Pflicht-Lane `backend-guards.yml`, weil sie `tests/unit/guards/` ungefiltert
fährt):

- `CI`-Diskriminator über `true` / `1` / `TRUE` / `yes` und über beide
  Schreibweisen von „kein Build-Agent" (leer, nicht gesetzt);
- das Gate **end to end als Subprozess** gegen `127.0.0.1:1` (ein Port, auf dem
  nie etwas lauscht, damit der Lauf nicht davon abhängt, ob der Dev-Stack läuft):
  mit `CI` rot, ohne `CI` genau ein Skip mit der Adresse im Grund, mit
  `--max-skipped 0` auch dieser Skip rot, und das serverfreie Modul der Stufe
  bleibt ungegatet. Ein Gate, das implementiert, aber an keinem Modul verdrahtet
  wäre, rötet hier;
- zwei Absenz-Wächter gegen das Zurückkriechen der Kopien (kein Modul bindet
  `ARANGO_AVAILABLE`; kein Modul trägt die Adresse in einem **ausführbaren**
  String).

Das Messwerkzeug der beiden Absenz-Wächter liest den **Syntaxbaum**, nicht den
Text — und das ist nicht Kosmetik: die erste, substring-basierte Fassung meldete
`test_care_task_dedup_concurrency.py` als Verstoß, weil dessen **Docstring**
`localhost:8529` erklärt. Ein Wächter, der Prosa als Fund zählt, wird beim ersten
Fehlalarm aufgeweicht. Docstrings werden jetzt per Knoten-Identität
ausgeschlossen, f-Strings dagegen erfasst; `test_both_sweeps_can_see_a_violation_at_all`
pflanzt beide Formen und prüft zusätzlich, dass ein reines Prosa-Modul **kein**
Fund ist.

#### Offen für den Operator

Die Aufnahme in `required_status_checks.contexts` (Branch-Protection `develop`)
steht aus — sie folgt auf drei grüne `workflow_dispatch`-Läufe des Jobs
`Integration tests (ArangoDB)`, wie in den Operator-Entscheidungen festgelegt.
