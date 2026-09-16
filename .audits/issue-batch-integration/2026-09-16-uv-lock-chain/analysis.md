# Gruppe `2026-09-16-uv-lock-chain`

Status: freigegeben 2026-09-16 · Umsetzung startet, sobald ein Entwickler-Slot frei ist

Gemessen gegen `origin/develop` @ `87c82ae25` (2026-09-16).

## Die Frage, auf die die Research-Phase gescoped war

Misst irgendetwas die Reichweite der uv-Migration aus #1377 — und welche Python-Installs
laufen heute noch außerhalb eines hashtragenden Locks?

## Die eine logische Änderung

Die uv-Migration aus #1377 erreicht die vier verbliebenen Python-Ausnahmen und wird
selbstprüfend, sodass ein Abdriften der Renovate-Manager-Inventur oder ein nicht
hashverifizierter Install auffällt, statt still zu bleiben.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1374** | `chore`, `dependencies` | Abhängigkeitskette | #1383s Akzeptanzkriterium 1 verlangt eine Lane, die rötet, wenn `poetry` in der Manager-Inventur erscheint. `renovate.json5:101-105` hält fest, dass genau die zwei Side-Service-`pyproject.toml` heute vom `poetry`-Manager gelesen werden — die AK ist unerfüllbar, solange #1374 nicht gelaufen ist |
| **#1383** | `chore`, `cicd`, `dependencies` | Abhängigkeitskette | dito; zusätzlich überlappende Fläche `renovate.json5` (`:101-118`) und `.github/workflows/docker-lint-build.yml` |

## Was gemessen wurde, und wo der Issue-Text danebenliegt

### Die uv-Pins: acht Stellen, ein Wert, kein Einzelpunkt der Wahrheit

`grep -rn "uv==" .github/workflows/` liefert **acht** Treffer, alle `0.12.15`
(`backend.yml:161,231,274,319,357`, `backend-guards.yml:115`, `api-docs.yml:51`,
`release-publish.yml:97`). `src/backend/pyproject.toml:116` trägt
`required-version = "==0.12.15"`. Renovate hält sie über die Gruppe `uv toolchain`
(`renovate.json5:118`) gemeinsam — PR #1447 hat alle acht zusammen gehoben. Das
funktioniert, ist aber ein Gruppen-Versprechen, kein Mechanismus: Eine neunte Stelle,
die jemand ohne die Gruppe anlegt, driftet unbemerkt.

**Abweichung vom Issue-Text:** #1383 zählt „seven `pip install 'uv=='` lines across
three workflows". Heute sind es acht Zeilen in vier Workflows. Und
`backend.yml:357` ist keine gewöhnliche Zeile: Sie ist der `install-command`-Input des
wiederverwendeten `nolte/gh-plumbing`-Coverage-Workflows. Ein `astral-sh/setup-uv`-Step
kann **nicht** in dessen Job eingefügt werden; diese Zeile verschwindet nur, wenn
gh-plumbing einen uv-Modus bekommt (Repository-Grenze) — **oder** der Install-Befehl
die Version aus `pyproject.toml` liest statt sie zu literalisieren. Letzteres ist in
diesem Repository machbar und erfüllt das Kriterium „`grep uv==` leer".

`astral-sh/setup-uv` ist heute **nirgends** im Einsatz.

### `debugpy` — der eine Install außerhalb des Locks

`src/backend/Dockerfile:72`: `uv pip install debugpy`. Bestätigt.

### Die Side-Services — vier `requirements.txt`, aber nur zwei `pyproject.toml`

| Service | `requirements.txt` | `pyproject.toml` | Dockerfile-Installs |
|---|---|---|---|
| `src/inference-service` | ja | **ja** | `:20-22` Builder (ungelockt, `onnx onnxscript`), `:39` `-r requirements.txt`, `:50` `watchfiles` |
| `src/knowledge-service` | ja | **ja** | `:15` `-r requirements.txt`, `:20` `watchfiles` |
| `docker/embedding-service` | ja | **nein** | `:17` Builder (`huggingface-hub sentencepiece`), `:79` `-r requirements.txt` |
| `docker/reranker-service` | ja | **nein** | `:14` Builder (`huggingface-hub optimum[onnxruntime] sentencepiece`), `:48` `-r requirements.txt` |

**Abweichung vom Issue-Text:** #1374 spricht von „give each service a
`pyproject.toml`", als hätte keiner eines. Zwei haben eines (und genau die liest der
`poetry`-Manager); zwei haben keines. Zusätzlich gibt es **fünf** ungelockte
`pip install`-Zeilen in Builder-Stufen, die das Issue nicht nennt — Modell-Konvertierung
(`onnx`, `optimum`) und Dev-Reloader (`watchfiles`). Ein Lock, der nur
`requirements.txt` ersetzt, ließe diese fünf offen; die Akzeptanzbedingung „installs
from a hash-bearing lock" wäre dann halb wahr.

### Taskfile und CI laufen verschiedene Interpreter

`.taskfiles/backend.yaml:16,22,28,71,77,83` rufen bare `ruff` / `python -m pytest` vom
Host-`PATH`. `backend.yml:162` prependet `.venv/bin`. Das Projektgedächtnis hält fest,
dass der globale Interpreter 28 Tests **lautlos** überspringen lässt (#1434). Bestätigt.

### Der Renovate-Health-Check: die Form existiert schon

`release-lag.yml:39-46` — geplanter Lauf, dedupliziertes Issue statt roter Status
(`:37`). Das ist die Vorlage für #1383 Punkt 1; sie muss nicht erfunden werden.

## Strukturbefund über die Mitglieder hinweg (§E)

**Klassifikation: Symptom-Cluster.** Grundursache: **#1377 hat den Backend-Baum auf
`uv.lock` gehoben, aber nichts misst die Reichweite dieser Regel.** Dieselbe Ursache
produzierte die sechs stummen Wochen des `pip-compile`-Managers (2026-08-02 bis 09-10),
den vakuösen Hash-Tamper-Test (sdist statt Wheel) und die vier Side-Services, die als
„Ausnahme" stehen blieben, ohne dass eine Ausnahmeliste existiert, die jemand
abarbeiten müsste.

Der Plan repariert die Ursache — eine Lane, die die Manager-Inventur **aufzählt** und
einen Falsifizierer, der die Hash-Behauptung **dauerhaft** prüft — und die vier
Side-Services als deren Konsequenz. Zwei Symptome zu flicken (vier Locks, acht Pins)
ließe die neunte Stelle und den fünften Service wieder unbemerkt.

### Prozessbefund

Keiner, der über #1456 hinausgeht. Die „Ausnahme ohne Ausnahmeliste" ist dieselbe
Klasse wie der Selbst-Widerruf im Kommentar: eine bekannte Lücke, die kein Gate trägt.
Wird als Kommentar an #1456 ergänzt.

## Stufe und Scheiben

**Stufe 2.** Kein veröffentlichter Vertrag ändert sich (die Images bleiben dieselben
Artefakte, nur ihr Bauweg ändert sich), keine Repository-Grenze wird überschritten —
der gh-plumbing-uv-Modus ist ausdrücklich außerhalb des Scopes.

**Unabhängig verifizierbare Scheiben**, in Abhängigkeitsreihenfolge:

1. **Scheibe 1 — #1374: vier Services auf `pyproject.toml` + `uv.lock`.** Für
   `embedding-service` und `reranker-service` entsteht das `pyproject.toml` neu; die
   Builder-Installs (`onnx`, `optimum[onnxruntime]`, `huggingface-hub`, `sentencepiece`)
   werden **Dependency-Gruppen** desselben Locks, `watchfiles` eine Dev-Gruppe.
   Dockerfiles installieren mit `uv sync --locked --no-dev` (Runtime) bzw. mit der
   Builder-Gruppe. `renovate.json5:101-105`: die `poetry`-Regel fällt, `pep621` mit
   `rangeStrategy: update-lockfile` übernimmt die vier. Prüfung: alle vier Images bauen
   lokal (`docker build`) und in `docker-lint-build.yml`.
2. **Scheibe 2 — #1383 Punkte 3 + 4: ein Pin, alles im Lock.** `astral-sh/setup-uv`
   digest-gepinnt mit `version-file: src/backend/pyproject.toml` ersetzt sieben
   `pip install 'uv=='`-Zeilen; die achte (`backend.yml:357`, Coverage-`install-command`)
   liest die Version aus `pyproject.toml`. `debugpy` wandert in die Dev-Gruppe des
   Backend-Locks, die Dockerfile-Zeile fällt. Prüfung: `grep -rn "uv==" .github/workflows/`
   leer; `grep -n "pip install" src/backend/Dockerfile` zeigt nichts außerhalb `uv sync`.
3. **Scheibe 3 — #1383 Punkt 2: der dauerhafte Hash-Falsifizierer.** Unit-Tier unter
   `tests/unit/guards/` (dort liegen bereits Guards über CI-Konfiguration), lauter Skip
   ohne `uv`, läuft im `Lock staleness`-Job (`backend.yml:210`). Kopiert
   `pyproject.toml` + `uv.lock`, verändert den Hash eines **Wheels, das installiert
   wird**, erwartet `uv sync --locked --no-install-project` ≠ 0; Positivkontrolle auf
   der unveränderten Kopie. Rot zuerst: gegen ein Lock ohne Hash-Prüfung (`uv lock
   --check` allein) muss der Test rot sein — das ist die Vakuumfalle aus #1377.
4. **Scheibe 4 — #1383 Punkt 1: die Renovate-Health-Lane.** Nach dem Muster von
   `release-lag.yml`: liest den Body von #12, rötet bzw. öffnet ein dedupliziertes Issue
   bei `WARN`/`ERROR` unter `## Repository Problems` oder wenn die Inventur nicht
   `pep621 → src/backend/pyproject.toml + uv.lock` **und** die vier Side-Services listet
   und `poetry` **nicht**. Der Parser ist eine Python-Funktion mit Unit-Tests, die eine
   Fixture-Kopie des Dashboards mit injiziertem Problem rot machen. Prüfung: der Test
   gegen die Fixture; die Lane selbst wird per `workflow_dispatch` einmal gefahren und
   die Ausgabe festgehalten.
5. **Scheibe 5 — #1383 Punkte 5 + 6: ein Interpreter, ein Dry-Run.** `lint:backend`,
   `test:backend:*` laufen über `uv run --locked`; `backend.yml` ruft `task deps:sync`
   statt den Befehl zu inlinen. `task renovate:dry-run` wickelt
   `renovate --platform=local --dry-run=full` mit ausgeschlossenen `.venv`/`node_modules`
   und wird in `docs/*/deployment/ci-cd.md` dokumentiert. Prüfung: `task test:backend:unit`
   ohne aktiviertes venv läuft mit dem gelockten pytest (Ausgabe des Interpreterpfads
   festhalten); `task renovate:dry-run` reproduziert die Inventur aus Scheibe 4.

## Modus

**Modus B — Sub-Branch je Mitglied.** Begründung: #1374s Abnahme ist **unsicher** —
vier Images, davon zwei mit ONNX-/Optimum-Resolution, die unter `uv` anders ausgehen
kann als unter `pip`. Scheitert ein Image-Build, muss #1374 herauslösbar sein, ohne
#1383s Selbstprüfung mitzureißen. Zwei Sub-Branches: `chore/1374-side-service-locks`
zuerst, dann `chore/1383-uv-chain-self-verifying`.

**Bekannte lokale Anpassung, falls #1374 herausgelöst wird:** Scheibe 4s
Inventur-Erwartung ändert sich (Side-Services bleiben unter `pip_requirements`,
`poetry` bleibt gelistet). Das entwertet kein Prädikat und keine Reihenfolge; es wird
im Artefakt festgehalten.

## Reihenfolge

1. **#1374** — der herauslösbare Kandidat zuerst, damit sein Ausgang feststeht, bevor
   Scheibe 4 die Inventur festschreibt.
2. **#1383** — Scheiben 2 → 3 → 4 → 5.

## Vollständigkeitsmatrix

Spalten wie in den Gruppen `write-route-guard` und `task-photo-refs` aus dem Repository
abgeleitet.

| Mitglied | Backend-Quellcode | Frontend-Quellcode | Spec | Tests | Doku | Config / Workflows | Generierter Katalog |
|---|---|---|---|---|---|---|---|
| **#1374** | *nicht zutreffend* — kein `app/`-Code; die Side-Services sind eigene Bäume | *nicht zutreffend* | `spec/nfr/NFR-009*.md` §2.3 — die Ausnahmeliste (heute: vier) wird leer; Prüfung: `task precommit` | *nicht zutreffend* — kein Test-Tier der Side-Services ändert sich; die Prüfung ist der Image-Build | `docs/*/deployment/` — falls eine Seite `requirements.txt` der Side-Services nennt (zu prüfen); sonst *nicht zutreffend* | 4× `pyproject.toml` + `uv.lock` (2 neu, 2 erweitert), 4× Dockerfile, `renovate.json5:101-105`; Prüfung: `docker build` je Image lokal + `docker-lint-build.yml` grün | *nicht zutreffend* |
| **#1383** | `src/backend/pyproject.toml` — `debugpy` in die Dev-Gruppe, `uv.lock` regeneriert; Prüfung: `uv sync --locked --extra dev` + `uv lock --check` | *nicht zutreffend* | `spec/nfr/NFR-009*.md` §6.1 — Hash-Verifikation als dauerhaft geprüfte Behauptung; Prüfung: `task precommit` | `tests/unit/guards/test_lock_hash_verification.py` (rot zuerst), `tests/unit/guards/test_renovate_dashboard_parser.py` (Fixture-Injektion rot); Prüfung: `pytest tests/unit/guards/` | `docs/de+en/development/testing/index.md` — Aktivierungsschritt fällt; `docs/de+en/deployment/ci-cd.md` — `task renovate:dry-run`; Prüfung: `task docs:build` (strict) | `backend.yml`, `backend-guards.yml`, `api-docs.yml`, `release-publish.yml` (setup-uv), neu `renovate-health.yml`, `src/backend/Dockerfile:72`, `.taskfiles/backend.yaml`, `renovate.json5:112-118`; Prüfung: `actionlint` (pre-commit) + `grep -rn "uv==" .github/workflows/` leer | *nicht zutreffend* |

## Risiken

- **ONNX/Optimum unter uv.** `optimum[onnxruntime]` und `onnxscript` haben enge
  Plattform-Marker; uv löst strenger als pip. Gegenmaßnahme: Scheibe 1 baut jedes Image
  lokal, bevor es committet wird, und ein Service, der nicht baut, wird als
  Herauslösung des Mitglieds behandelt (Modus B), nicht als Anlass, den Lock zu lockern.
- **`setup-uv` Digest-Pin und Renovate.** Der Action-Pin muss in die Gruppe
  `uv toolchain` (`renovate.json5:118`), sonst hebt Renovate Action und
  `required-version` getrennt und die Lane aus Scheibe 4 rötet zu Recht.
- **Der Coverage-`install-command`** (`backend.yml:357`) liest die Version zur Laufzeit
  aus `pyproject.toml`. Ein Tippfehler dort bricht die Coverage-Lane, nicht die
  Backend-Lane — sichtbar, aber an anderer Stelle. Das wird im Kommentar der Zeile gesagt.
- **Scheibe 5 ändert das Verhalten jedes lokalen `task test:backend:*`**: Wer heute ein
  fremdes venv aktiviert hat, bekommt danach das gelockte. Das ist der Zweck; es wird in
  `docs/*/development/testing/index.md` gesagt.

## Bewusst außerhalb des Scopes

- Ein **uv-Modus für `nolte/gh-plumbing`s `reusable-python-coverage.yaml`** —
  Repository-Grenze. Der Coverage-`install-command` bleibt, liest aber die Version aus
  `pyproject.toml`; das erfüllt „`grep uv==` leer" ohne gh-plumbing anzufassen. Wenn der
  Operator den Upstream-Modus will, ist das ein eigenes Issue dort.
- **Eine Workspace-Lock** über Backend + vier Services. #1374 nennt sie als Option; sie
  koppelt fünf Release-Zyklen aneinander und ist eine Architekturentscheidung, nicht
  eine Migration. Je Service ein Lock.
- **#1321** (Docker-Hub-Login der static-Lane) teilt die Fläche `.github/workflows/`,
  aber keine Capability; blockiert auf ein Secret.

## Operator-Entscheidungen (2026-09-16, vor der Umsetzung)

1. **Builder-Abhängigkeiten in den Lock: ja.** `onnx`, `onnxscript`, `optimum[onnxruntime]`,
   `huggingface-hub`, `sentencepiece` werden Dependency-Gruppen des jeweiligen
   Service-Locks, `watchfiles` eine Dev-Gruppe. Ein Image, das darunter nicht baut,
   löst das Mitglied heraus (Modus B), statt den Lock zu lockern.
2. **Health-Lane öffnet ein dedupliziertes Issue**, nach dem Muster von `release-lag.yml`,
   per Body-Marker dedupliziert. Kein bloßes Röten des Scheduled-Runs.
3. **Taskfile über `uv run --locked`.** Die ~0,3 s je Aufruf sind der Preis dafür, dass
   ein veraltetes venv nicht still weiterlaufen kann (#1434-Klasse).

## Ergebnisse je Scheibe

### Scheibe 1 — #1374 (Sub-Branch `chore/1374-side-service-locks`, 2026-09-16)

**Ergebnis: alle vier Images bauen. Keine Herauslösung nötig.** Insbesondere löst uv
sowohl `optimum[onnxruntime]` (reranker) als auch `torch`/`onnxscript` (inference) auf
Python 3.14 auf; das Risiko „ONNX/Optimum unter uv" hat sich nicht materialisiert.

#### Image-Builds (lokal, Kontext und Dockerfile-Pfad aus `docker-lint-build.yml`)

| Image | Kommando | Exit | Größe vorher | Größe nachher |
|---|---|---|---|---|
| knowledge-service | `docker build -f src/knowledge-service/Dockerfile src/knowledge-service` | **0** | 198 MB | 243 MB |
| knowledge-service (`--target dev`) | dito `--target dev` | **0** | — | 243 MB |
| inference-service | `docker build -f src/inference-service/Dockerfile src/inference-service` | **0** | 520 MB | 565 MB |
| inference-service (`--target dev`) | dito `--target dev` | **0** | — | 565 MB |
| embedding-service | `docker build -f docker/embedding-service/Dockerfile docker/embedding-service` | **0** | 927 MB | 972 MB |
| reranker-service | `docker build -f docker/reranker-service/Dockerfile docker/reranker-service --target bge-reranker-v2-m3` | **0** | nicht gemessen | 2660 MB |

Die „vorher"-Werte stammen aus einem Build des `HEAD`-Standes derselben Bäume
(`git archive HEAD <service> | tar -x` in ein Scratch-Verzeichnis). Für den Reranker
wurde darauf verzichtet: seine Download-Stufe zieht über `optimum` die CUDA-Wheels
(mehrere GB) ein zweites Mal, und der Wert ist aus den anderen dreien ableitbar.

**Gemessener Mehraufwand: +45 MB je Runtime-Image, in allen drei Messungen derselbe
Wert.** Er ist kein Abhängigkeitszuwachs, sondern das Backend-Muster: die statische
`uv`-Binary (`COPY --from=ghcr.io/astral-sh/uv:…`) liegt in der Runtime-Stufe und
`UV_COMPILE_BYTECODE=1` legt `.pyc` neben jede Datei. `src/backend/Dockerfile` trägt
denselben Aufschlag; die Vorgabe war, exakt diesem Muster zu folgen, statt eine zweite
Form zu erfinden. Wer die 45 MB wegoptimieren will (uv nur in einer Builder-Stufe, venv
per `COPY --from`), muss das für alle fünf Images gemeinsam entscheiden — sonst entsteht
genau die Divergenz, die dieses Mitglied schließt.

`hadolint` (lokal, dieselbe Version wie die Lane): alle vier Dockerfiles Exit 0.

#### Hash-Nachweis je Lock

`uv lock --check` in jedem Verzeichnis Exit 0; Zahl der Artefakt-URLs gleich der Zahl
der `hash = "sha256:…"`-Einträge, d. h. **kein Artefakt ohne Hash**:

| Lock | Pakete | URLs | Hashes |
|---|---|---|---|
| `src/inference-service/uv.lock` | 115 | 1094 | 1094 |
| `src/knowledge-service/uv.lock` | 44 | 438 | 438 |
| `docker/embedding-service/uv.lock` | 45 | 446 | 446 |
| `docker/reranker-service/uv.lock` | 70 | 639 | 639 |

Auch die `torch`-Wheels vom expliziten CPU-Index (`download.pytorch.org/whl/cpu`, per
`[tool.uv.sources]` nur für `torch`/`torchvision`) tragen Hashes; der Build-Log zeigt
`+ torch==2.14.0+cpu` aus dem Lock.

#### `grep -rn requirements.txt` — was übrig bleibt und warum

Alle vier Side-Service-Dateien sind gelöscht; **keine** Fundstelle zeigt mehr auf eine
von ihnen (`grep -rn "\(inference\|knowledge\|embedding\|reranker\)-service/requirements"`
ist leer). Die verbleibenden Treffer gehören zu anderen Bäumen und bleiben bewusst:

- `docs/requirements.txt` + `.taskfiles/docs.yaml`, `release-cd-deliver-docs.yml`,
  `.claude/…` — die MkDocs-Umgebung, ein eigener Baum, nicht Teil dieser Migration.
- `tests/e2e/requirements.txt` (+ `tests/e2e/Dockerfile`, `tests/e2e_selftest/README.md`,
  `.pre-commit-config.yaml`, `docs/*/development/testing/index.md`) — die E2E-Suite,
  ebenfalls ein eigener Baum; #1374 nennt sie nicht.
- `tools/rag-eval/README.md` — Anleitung eines Tool-Verzeichnisses ohne eigenes Image.
- `backend.yml:281-291` — `uv export --format requirements.txt` in eine **temporäre**
  Datei für `pip-audit`; das ist eine Ausgabe des Locks, kein Install-Eingang.
- `spec/analysis/*`, `project/requirements/*`, `.audits/*` — historische Analysen, die
  den alten Zustand beschreiben; sie werden nicht rückwirkend umgeschrieben.

#### Weitere Messungen und Abweichungen

1. **Die in der Vollständigkeitsmatrix erwartete „Ausnahmeliste" in NFR-009 §2.3
   existierte nicht.** §2.3 listete nur `Python (Backend, inkl. Dev-Extra)`; die vier
   Side-Services waren nirgends als Ausnahme benannt — genau der §E-Befund („Ausnahme
   ohne Ausnahmeliste"). Statt eine Liste zu leeren, wurde die Tabellenzeile um die
   Side-Services ergänzt und ein MUSS aufgenommen, das ausdrücklich sagt, dass es
   **keine** Ausnahme gibt, samt der bisherigen Lücke.
2. **`sentry-sdk[fastapi]` war in `requirements.txt` beider `src/`-Services deklariert,
   in ihrer `pyproject.toml` aber nicht.** Der `poetry`-Manager las also eine
   Dependency-Menge, die kein Image installierte, und das Image installierte eine, die
   Renovate nicht sah. Mit dem Lock aus der `pyproject.toml` wäre das Paket aus beiden
   Images verschwunden; es ist jetzt in `[project].dependencies` deklariert.
3. **Kein Doku-Treffer.** Keine Seite unter `docs/` nennt die Side-Service-Abhängigkeiten
   oder ihre `requirements.txt`; die uv-Beschreibungen in `docs/*/deployment/ci-cd.md`
   sprechen ausschließlich vom Backend. Doku-Spalte der Matrix: *nicht zutreffend*
   (gemessen, nicht angenommen).
4. **`renovate.json5`: die `poetry`-Regel fällt nicht weg, sie wird entgrenzt.**
   `matchFileNames: ['src/backend/**']` entfernt → `poetry` ist repository-weit
   deaktiviert. Eine pfad-gebundene Abschaltung ist genau das, was die Side-Services
   monatelang unter einem zweiten Manager ohne Lock ließ. Zusätzlich musste der
   **Custom-Manager für `required-version`** (`renovate.json5`, `managerFilePatterns`)
   um die vier neuen `pyproject.toml` erweitert werden — sonst hätten sie den uv-Pin
   getragen, ohne je von der Gruppe `uv toolchain` gehoben zu werden (#1296-Klasse).
   Das ist eine Fläche, die Scheibe 4 mitprüfen sollte.
5. **`inference-service` hat weiterhin keinen Build-Job in `docker-lint-build.yml`** (nur
   Lint; gebaut wird es in `docker-publish.yml`). Sein Lock/Dockerfile-Regress fiele also
   erst beim Publish auf. Unverändert gelassen — außerhalb dieser Scheibe, aber als
   Beobachtung festgehalten.
6. **`side-services.yml` installiert weiter `pip install -e '.[dev]'`.** Das Test-Toolchain
   liegt im `dev`-**Extra**, nicht in der `dev`-Dependency-Gruppe (die nur `watchfiles`
   für das Image trägt). Nur der Kommentar, der behauptete, der Service habe „no
   hash-locked dev requirements file", wurde korrigiert; die Umstellung auf
   `uv sync --locked` gehört zu #1383.
7. **Konsequenz für Scheibe 4:** die Inventur-Erwartung gilt in ihrer *starken* Form —
   `pep621` liest fünf `pyproject.toml` + `uv.lock`, `poetry` erscheint nicht mehr. Die in
   „Bekannte lokale Anpassung" beschriebene Abschwächung entfällt.

### Scheibe 2 — #1383 Punkte 3 + 4 (Sub-Branch `chore/1383-uv-chain-self-verifying`, 2026-09-16)

**Ergebnis: beide Akzeptanzkriterien erfüllt und beide dauerhaft geprüft.**

#### AK-Nachweis

```
$ grep -rn "uv==" .github/workflows/ ; echo "exit=$?"
exit=1

$ grep -n "pip install" src/backend/Dockerfile ; echo "exit=$?"
exit=1
```

Beide Greps waren **vor** der Scheibe nicht leer (acht bzw. zwei Treffer). Damit
die Greps nach dieser Scheibe nicht bloß Tatsachen über einen Nachmittag sind,
ist `src/backend/tests/unit/guards/test_uv_pin_is_single.py` dazugekommen: vier
Fälle, die (a) jede ausführbare Workflow-Zeile mit einer literalen uv-Version
roten lassen, (b) sicherstellen, dass der Sweep die vier interessanten Dateien
überhaupt liest (Absence-Checks fallen sonst offen auf), (c) verlangen, dass
mindestens ein `setup-uv`-Step existiert, und (d) prüfen, dass jeder davon
digest-gepinnt ist und auf eine `pyproject.toml` zeigt, die wirklich ein
`[tool.uv].required-version` trägt.

**Rot zuerst** (Vorzustand per `cp` wiederhergestellt, nicht `git stash`):

```
$ git show HEAD:.github/workflows/backend.yml > .github/workflows/backend.yml
$ pytest tests/unit/guards/test_uv_pin_is_single.py -q
E   AssertionError: A workflow names a uv version itself. … Offending lines:
E       .github/workflows/backend.yml:161: python -m pip install 'uv==0.12.15'
E       .github/workflows/backend.yml:231: run: python -m pip install 'uv==0.12.15'
E       .github/workflows/backend.yml:274: run: python -m pip install 'uv==0.12.15' 'pip-audit==2.10.1'
E       .github/workflows/backend.yml:319: python -m pip install 'uv==0.12.15'
E       .github/workflows/backend.yml:357: install-command: python -m pip install 'uv==0.12.15' && …
1 failed, 3 passed in 0.91s
```

**Mutationen** (je eine Zeile in `api-docs.yml`, danach per `cp` zurück):

| Mutation | Ergebnis |
|---|---|
| `version-file:` entfernt | rot — „no `version-file:` — the action would install the LATEST uv" |
| Digest-Pin durch `@v10` ersetzt | rot — „not pinned to a 40-character commit SHA" |
| unverändert | 4 passed |

#### Der Pin

`astral-sh/setup-uv@bec219d24cd3e171d82865faccec33120bb574f4 # v10.1.0` (Tag-Ref
über `gh api repos/astral-sh/setup-uv/git/ref/tags/v10.1.0` aufgelöst, Objekttyp
`commit`), mit `version-file: src/backend/pyproject.toml`, `enable-cache: true`
und `cache-dependency-glob: src/backend/uv.lock`. Sieben Stellen ersetzt
(`backend.yml` 4×, `backend-guards.yml`, `api-docs.yml`, `release-publish.yml`),
zwei weitere neu in `side-services.yml` — macht **sieben** `uses:`-Stellen im
Repository (die vier alten Backend-Stellen sind zu vier Steps geworden, die zwei
Side-Service-Steps sind neu).

Der Cache-Glob ist bewusst eng: die Default-Globs der Action wären
`**/pyproject.toml` + `**/uv.lock`, und seit #1374 gibt es fünf Locks, von denen
vier mit dem jeweiligen Job nichts zu tun haben.

#### Die achte Stelle — Repository-Grenze, gemessen statt behauptet

`backend.yml:357` ist der `install-command`-Input des Reusable-Workflows
`nolte/gh-plumbing/.github/workflows/reusable-python-coverage.yaml`. Ein
`uses:`-Step lässt sich dort nicht einfügen; der Aufrufer kann nur einen
Shell-Befehl übergeben. Der Befehl **liest** die Version jetzt, statt sie zu
wiederholen — `[tool.uv].required-version` ist bereits der exakte Specifier
`==<version>` und wird an den Paketnamen angehängt:

```
UV_SPEC="$(python -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["tool"]["uv"]["required-version"])')" && python -m pip install "uv$UV_SPEC" && …
```

Lokal gegen `src/backend/pyproject.toml` ausgeführt: `resolved package spec:
uv==0.12.15` — bitgleich mit dem vorherigen Literal. Ein uv-Modus für
`reusable-python-coverage.yaml` bleibt ausdrücklich außerhalb des Scopes
(eigenes Repository); wer ihn will, öffnet dort ein Issue.

#### `debugpy`

`"debugpy>=1.8.0,<2.0.0"` im Dev-**Extra** von `src/backend/pyproject.toml`
(nicht in einer eigenen Gruppe: das eine `uv sync --locked --extra dev`, das CI,
`task deps:sync` und die Dev-Stufe des Images ohnehin fahren, installiert es
dann mit, ohne einen zweiten Selektor). `uv lock` → `Added debugpy v1.8.22`.
Die Dockerfile-Zeile `uv pip install debugpy` ist weg.

```
$ docker build --target dev -t kp-backend-dev-1383 .   # 1:07 min
EXIT=0
$ docker run --rm --entrypoint python kp-backend-dev-1383 -c "import debugpy; print(debugpy.__version__, debugpy.__file__)"
1.8.22 /opt/venv/lib/python3.14/site-packages/debugpy/__init__.py
```

#### `side-services.yml` (Scheibe-1-Befund 6)

`knowledge-service` und `inference-service` installieren jetzt mit
`uv sync --locked --extra dev` plus `$GITHUB_PATH`-Prepend (die Taskfile-Ziele in
`.taskfiles/libs.yaml` rufen ein blankes `python -m pytest`). Lokal gemessen:
`uv sync --locked --extra dev` Exit 0 in beiden Bäumen, danach
`pytest tests/ -p no:cacheprovider` → **47 passed** (knowledge) bzw. **105
passed** (inference). Das `build`-Dependency-Group des inference-service
(torch/onnx) ist keine Default-Group und wird dabei nicht installiert — der Job
zahlt keinen torch-Download.

**Abweichung: `kp_vectordb` bleibt bei `pip install -e '.[dev]'`.** Der dritte
Job in dieser Datei ist keiner der vier Side-Services aus #1374 — `src/libs/
kp_vectordb/` ist eine geteilte Library und hat **kein** `uv.lock`. Es gibt also
nichts, wovon `--locked` synchronisieren könnte; einen fünften Lock anzulegen ist
eine Entscheidung über die Release-Form der Library, keine CI-Änderung. Im
Workflow-Kommentar festgehalten statt nebenbei gemacht.

#### `renovate.json5`

Der Action-Pin ist in dieselbe Gruppe `uv toolchain` gewandert
(`matchDatasources` um `github-tags`, `matchPackageNames` um
`astral-sh/setup-uv` erweitert). Das war **nötig**, nicht kosmetisch: die
Workflows tragen keine eigene uv-Version mehr, also würde ein separater
Action-Bump eine andere uv-Release installieren als die, die die Gruppe bewegt.
Die generische `github-actions`-Regel steht früher im Array, diese später — sie
gewinnt daher auf `groupName`; `automerge: false` steht explizit dabei, weil die
generische Regel minor/patch/digest automerged und hier der **Resolver** bewegt
wird, der fünf Lockfiles erzeugt.

Der Kommentar „referenced three times" war falsch und ist nachgezählt ersetzt:
**drei Arten von Stelle, 17 Stellen** — fünf `[tool.uv].required-version`, fünf
`ghcr.io/astral-sh/uv` in Dockerfiles, sieben `astral-sh/setup-uv@`.

Im Workflow-Regex-Manager ist die Alternative `uv` aus
`'(?<depName>pip-audit|pip-licenses|uv)=='` entfernt — sie kann nichts mehr
treffen, und eine tote Alternative hätte suggeriert, ein wiedereingeführtes
Literal sei weiterhin abgedeckt.

#### Doku

`docs/de/deployment/ci-cd.md` + EN-Spiegel und das `pip-audit`-Beispiel in
NFR-009 §4.1 zeigten noch `pip install 'uv==0.12.12'` — eine Version, die seit
#1447 nirgends mehr im Repository steht. Alle drei auf die neue Form umgestellt.

#### Gates

`pre-commit run actionlint-docker --all-files`: **Passed**.
`pre-commit run --all-files`: alles grün außer `nuclei-validate`, das mit
„nuclei is not on PATH" abbricht — eine Lücke der lokalen Umgebung, kein Befund
(der Hook verweigert bewusst ein grünes Ergebnis ohne Werkzeug).
`uv lock --check` Exit 0. `pytest tests/unit/guards` → 40 passed.
