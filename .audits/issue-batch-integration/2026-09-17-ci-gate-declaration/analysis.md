# Gruppe `2026-09-17-ci-gate-declaration`

Status: Analyse abgeschlossen · Write-Gate offen (Operator-Freigabe ausstehend)

Gemessen gegen `origin/develop` @ `0b4ce20bf` (2026-09-17). Transientes Artefakt.

## Die Frage

Welche Prüfungen, auf die `develop` sich verlässt, existieren nur außerhalb des Baums (Ruleset in der GitHub-UI, Build erst post-merge) oder gar nicht (lock-lose Python-Bäume, unbeobachtetes `tests/e2e`)?

## Die eine logische Änderung

Jede Prüfung, auf die `develop` sich verlässt, ist im Baum deklariert und läuft vor dem Merge: das inference-Image wird pre-merge gebaut, die zwei lock-losen Python-Bäume bekommen Locks und einen Beobachter, und die Ruleset-Kontexte haben eine versionierte Quelle.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1463** | `cicd` | thematische Kopplung (Spec-Topic `continuous-integration` §F „Artefakt pre-merge bauen") | `docker-lint-build.yml:135-138` lintet `src/inference-service/Dockerfile`, Build-Jobs Z. 140-260 ohne `build-inference-service`; `changes`-Filter Z. 32-66 hat keinen `inference-service`-Output, obwohl `on.paths` Z. 13 den Pfad führt; einzige Build-Evidenz `docker-publish.yml:599-600` (post-merge) |
| **#1464** | `chore`, `dependencies` | thematische Kopplung (§H „Interim benennt die Änderung, auf die es wartet") | `side-services.yml:203-225` pip-Install mit Verweis auf #1464; `scripts/ci/check_renovate_dashboard.py:125-128` `LOCKLESS_PYTHON_PROJECTS`; `renovate.json5:2-5` erbt `gh-plumbing//renovate-configs/common#v2.1.0` mit `:ignoreModulesAndTests`, lokal kein `ignorePaths` |
| **#1491** | `chore`, `cicd` | thematische Kopplung (dieselbe Klasse: Prüfung ohne versionierte Quelle) | Ruleset `17783737 default-branch-protection`, `source_type: Repository` → deklarierbar; `.github/settings.yml` hat kein `rulesets:`; Guard-Fixture `tests/unit/guards/fixtures/required_status_contexts_develop.yaml` |

Berührungsflächen sind **disjunkt** (`docker-lint-build.yml` / `side-services.yml`+`renovate.json5`+`src/libs` / `settings.yml`+Fixture) — die Kopplung ist die Klasse, nicht die Datei. Beide Befunde #1463/#1464 stammen aus dem CI/CD-Review der Gruppe `2026-09-16-uv-lock-chain`.

## Messung vs. Issue-Text

- #1480 (transformers 5) hängt **nicht** an #1463: `build-reranker-service` (`docker-lint-build.yml:235-249`) existiert pre-merge; das Loch betrifft nur inference.
- #1491: die Ruleset-Kontexte `security / Build` und `chain-bench / Chain Bench` entstehen in `build-static-tests.yaml:68` und `:75` (gh-plumbing `reusable-chain-bench.yaml@v2.1.0`). Ob die Probot-Settings-App `rulesets:` unterstützt, ist **nicht verifiziert** — zu messen (App-Version, Doku); Fallback: die zwei Kontexte in `required_status_checks.contexts` der Branch-Protection in `settings.yml` einfalten, Ruleset bleibt redundant bestehen.
- #1464: zwei Entscheidungen lagen vor der Gruppe; getroffen (Operator 2026-09-17): **Lock je Bibliothek + lokaler `ignorePaths`-Override.**

## Strukturbefund (§E)

**Klassen-Cluster.** Klasse: *eine Prüfung, die die Spec verlangt, existiert nur außerhalb des Baums oder gar nicht.* Sweep-Prädikat für den PR: (1) Check-Run-Namen auf dem develop-Head (`gh api repos/…/commits/<sha>/check-runs`) vs. deklarierende Workflow-Datei — jeder Name ohne Quelle im Baum ist ein Hit; (2) Renovate-Manager-Inventar (`task renovate:dry-run`) vs. Python-Bäume mit `pyproject.toml` — jeder Baum ohne Manager ist ein Hit.

## Stufe und Design

**Stufe 2** — ein Repo, kein veröffentlichter Vertrag (der `ignorePaths`-Override bleibt lokal, kein gh-plumbing-Eingriff).

1. **#1463:** `changes`-Output `inference-service`, Job `build-inference-service` nach dem Muster der sechs Nachbarn (gleicher Kontext wie `docker-publish.yml:599-600`, `push: false`, Cache). Nicht als Pflicht-Check (das ist eine Messentscheidung nach NFR-018 §4, wie bei den Nachbarn).
2. **#1464:** `uv.lock` (hash-komplett) für `src/libs/kp_vectordb` und `kp_errortracking` mit `[tool.uv].required-version` wie die Nachbarn; `side-services.yml` installiert `uv sync --locked`; `LOCKLESS_PYTHON_PROJECTS` wird **leer** und der Health-Check asserts das (kein Ausnahmeregister — NFR-009 §2.3 MUST); `renovate.json5` überschreibt `ignorePaths` so, dass `tests/e2e/**` beobachtet wird — **gemessen** per `task renovate:dry-run` (Extraktion zeigt die `tests/e2e`-Abhängigkeiten), und die Health-Lane-Fixture wird nach der Messung neu gezogen.
3. **#1491:** `rulesets:` in `settings.yml`, wenn die App es unterstützt (messen); sonst Einfalten. Fixture + Guard `test_required_contexts_are_unfiltered.py` decken die zwei Kontexte ab; Cross-Check Live ↔ Datei bleibt.

## Modus und Scheiben

**Modus B** — Sub-Branch je Mitglied auf `chore/2026-09-17-ci-gate-declaration`. Herauslösbar: #1464 (uv-Auflösung der zwei Libs kann scheitern; `ignorePaths`-Semantik der geerbten Config ist zu messen), #1491 (App-Support ungewiss). #1463 ist mechanisch.

Reihenfolge: **#1463 → #1491 → #1464.**

| Scheibe | Inhalt | Rot-zuerst / Nachweis |
|---|---|---|
| 1 | `build-inference-service` + `changes`-Output | Guard-Test: jede Dockerfile unter `src/`/`docker/`, die gelintet wird, hat einen Build-Job (heute: 1 Hit); `actionlint`; ein `workflow_dispatch`/PR-Lauf mit inference-Pfad-Änderung baut |
| 2 | Rulesets in `settings.yml` (oder Einfalten), Fixture, Guard | Guard rot mit der alten Fixture; Live-Cross-Check grün |
| 3 | zwei `uv.lock`, `side-services.yml`, `LOCKLESS_PYTHON_PROJECTS = ()`, `ignorePaths`-Override | Hash-Falsifizierer der Libs (Muster `test_lock_hash_verification.py`); Health-Check-Test rot bei nicht-leerer Liste; `task renovate:dry-run` zeigt `tests/e2e` im Inventar |

## Vollständigkeitsmatrix

| Issue | AK | Scheibe | Nachweis |
|---|---|---|---|
| #1463 | inference-Image baut pre-merge | 1 | PR-Check-Run auf dem Bündel-PR (Dockerfile-Touch) |
| #1463 | Lücke kann nicht zurückkommen | 1 | Guard „gelintet ⇒ gebaut" |
| #1464 | beide Libs hash-gelockt, CI installiert `--locked` | 3 | Falsifizierer + Lane grün |
| #1464 | `tests/e2e` beobachtet | 3 | Dry-Run-Inventar |
| #1491 | Ruleset-Kontexte versioniert | 2 | `settings.yml`-Diff + Guard |

## Verifikation

`actionlint`, `shellcheck`, `pytest tests/unit/guards --max-skipped 0` (mit gepinntem uv auf PATH), `task renovate:dry-run`, Docker-Build der inference-Lane lokal (`docker build` mit dem exakten Kontext aus dem Workflow). Review `cicd-pipeline-reviewer` (Read-only) auf dem Tip. Dispatch: `nolte-engineering:fullstack-developer`, sequenziell.
