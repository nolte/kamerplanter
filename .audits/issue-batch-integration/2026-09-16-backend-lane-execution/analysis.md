# Gruppe `2026-09-16-backend-lane-execution`

Status: wartet auf Operator-Freigabe (Write-Gate nach `spec/project/issue-batch-integration/` §D)

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

## Offene Fragen an den Operator

1. **Darf die Integration-Lane ein Pflicht-Check werden**, oder bleibt sie advisory
   wie Nuclei/ZAP? Die Branch-Protection verlangt heute genau zwei Checks (`static /
   Static CI Tests`, `lint-test-build (22)`); ein dritter verlängert bei
   `strict: true` jeden Merge-Zug. Empfehlung: **advisory für zwei Wochen**, dann auf
   gemessener Historie entscheiden (NFR-018 §4), wie bei Nuclei.
2. **Skip-Floor als harte Zahl je Tier oder als `0` überall mit Marker-Ausnahmen?**
   Eine harte Zahl ist ehrlich über den Ist-Zustand (unit: 1); `0` mit
   `@pytest.mark.skip(reason=…)` als einziger legitimer Skip-Form zwingt jeden Skip an
   einen Grund. Empfehlung: harte Zahl **und** `-rs` im Fehler — die Zahl ist
   nachprüfbar, der Grund lesbar.
