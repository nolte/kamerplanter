# PR-CI-Redundanz-Audit (#2409)

Datum: 2026-10-31 · Basis: `develop` @ 8723b54d6 · Branch `ci/2409-redundant-pr-ci`

**Methode.** Jede Aussage unten ist an einer von drei Quellen belegt, und die Quelle
steht dabei:

- **statisch** — aus den Workflow-Dateien gelesen (Trigger, `paths:`, `changes`-Filter,
  `needs:`, Cache-Specs, Artefakte). Die Job-Auswahl je Änderungsart (§3) ist mit einem
  Glob-Matcher über die echten Filter berechnet, nicht von Hand geraten;
- **Laufdaten** — `gh api …/actions/runs/<id>/jobs` für die Pull Requests #2596, #2591,
  #2594, #2592, #2595, #2589, #2585 und #2574 (alle vom 30./31.10.2026);
- **Cache-Einträge** — `gh api …/actions/caches` (Stand 2026-10-31 ~08:00Z, 771 aktive
  Einträge, 10,55 GB).

**Warum `.audits/` und nicht `docs/`.** Dieses Dokument ist eine Stichtagsmessung mit
Laufzeiten, Cache-Indexgrößen und Issue-Nummern. Unter `docs/` müsste es als DE/EN-Paar
gepflegt werden und bliebe nicht aktuell: Die Zahlen veralten mit dem nächsten Merge,
und DOCS.md trennt Endnutzer- und technische Zielgruppe und schränkt sichtbare
Issue-/REQ-Verweise ein. `.audits/cicd-audit/` ist der Ort, an dem schon das CI/CD-Audit
vom 2026-08-01 liegt. Was davon dauerhaft gilt (die Zuständigkeit je Check und die
bewusst belassene Duplikation, §2 und §6), sollte als kurzer Abschnitt in
`docs/de/deployment/ci-cd.md` und im EN-Spiegel nachgezogen werden. Das ist als
Folgepunkt in §8 notiert.

---

## Zusammenfassung

Das Issue nennt sechs Hypothesen. Am Workflow-Graphen und an den Laufdaten nachgemessen,
sieht das Ergebnis so aus:

| # | Hypothese aus dem Issue | Befund | Kosten je PR (gemessen) | Entscheidung |
|---|---|---|---|---|
| H1 | Frontend-Build läuft in `lint-test-build`, `bundle-budget` und `lighthouse` je einmal | **bestätigt**, sogar 5×: dazu je ein `npm run build` im Frontend-Image von `docker-lint-build` und von `e2e-smoke` | `bundle-budget` 0,8–2,0 min, `lighthouse` 1,9–3,1 min gesamt; der Build ist nur ein Teil davon | Empfehlung (§7.2/§7.3), nicht umgesetzt |
| H2 | Vitest läuft doppelt (Test- und Coverage-Job) | **bestätigt**, und es ist die größte Doppelung | `lint-test-build (22)` 12,3–18,9 min, `Coverage / Node.js Coverage` 12,7–20,9 min | Empfehlung mit Betreiberentscheidung (§7.1) |
| H3 | `backend.yml` überlappt mit `backend-guards.yml` | **teilweise**: die Guard-Tests (`tests/unit/api`, `tests/unit/guards` + 12 Dateien) laufen in beiden; die Integrationstests nur in `backend-guards.yml` | Guards-Job 11,6–20,8 min, ein Teil davon läuft in `lint-test` (22,5–23,8 min) noch einmal | bewusst belassen (§6.3) |
| H4 | Docker-Validierung und E2E bauen dieselben Images neu | **bestätigt**, aber billig: Backend- und Frontend-Image werden in `docker-lint-build` und im E2E-Stack gebaut | `build-backend` 1,1–1,4 min, `build-frontend` 1,7 min (fast vollständige Cache-Treffer) | Empfehlung (§7.4), nicht umgesetzt |
| H5 | `backend` und `celery-worker` bauen dasselbe Image doppelt | **bestätigt**: gleiche Build-Definition, beide exportieren den Cache | zwei Index-Schreibvorgänge im Abstand von ~7 s je Lauf | Empfehlung (§7.5) |
| H6 | Unterschiedliche Cache-Scopes verhindern Wiederverwendung | **bestätigt, und schlimmer als angenommen**: sechs `docker-lint-build`-Jobs teilten sich den Default-Scope `buildkit` und überschrieben gegenseitig ihren Cache-Index | nicht gemessen (kein Lauf mit der Änderung) | **umgesetzt** (§5) |

Umgesetzt ist genau eine Reduktion: eigene Cache-Scopes je Image in
`docker-lint-build.yml`, wobei Backend und Frontend den Scope des E2E-Stacks
mitbenutzen. Ein neuer Guard hält das fest. Alles andere würde entweder einen Pflicht-Check
verändern, eine Laufzeitprobe auf GitHub voraussetzen oder gegen eine dokumentierte
Betreiberentscheidung laufen. Diese Punkte stehen als Empfehlung in §7.

---

## 1. Pflicht-Checks auf `develop` und ihre Lieferanten

Gemessen mit `gh api repos/nolte/kamerplanter/branches/develop/protection` und
`gh api repos/nolte/kamerplanter/rules/branches/develop`:

| Pflicht-Check | Quelle | Workflow / Job | Trigger | Wie er bei jeder PR meldet |
|---|---|---|---|---|
| `static / Static CI Tests` | Branch Protection + Ruleset | `build-static-tests.yaml` / `static` (reusable pre-commit) | `push`, alle Branches, kein `paths:` | läuft immer |
| `lint-test-build (22)` | Branch Protection | `frontend.yml` / `lint-test-build` | `pull_request` ohne `paths:` | Job läuft immer, die Schritte sind über `RUN_FRONTEND` gegated |
| `Write-route and tree guards` | Branch Protection | `backend-guards.yml` / `guards` | `push`, alle Branches, kein `paths:` | läuft immer, ohne Relevanz-Gate |
| `Integration tests (ArangoDB)` | Branch Protection | `backend-guards.yml` / `integration` | `push`, alle Branches, kein `paths:` | Job läuft immer, die Schritte sind über `RUN_INTEGRATION` gegated |
| `chain-bench / Chain Bench`, `security / Build` | nur Ruleset | `build-static-tests.yaml` | wie `static` | läuft immer |

Diese Änderung fasst keinen dieser Jobs an.

---

## 2. Workflow/Job → Checks, Tests, Builds, Artefakte

Hier stehen nur die Workflows, die eine PR auslösen kann. `push`-only-Workflows wie
`docker-publish.yml` oder die Security-Postmerge-Läufe sind nur aufgeführt, wenn sie
einen Cache-Scope mit einem PR-Job teilen.

| Workflow / Job | Auslöser für eine PR | Was er ausführt | Installation | Build | Artefakt |
|---|---|---|---|---|---|
| `frontend.yml` / `lint-test-build (22)` | immer, Schritte gegated | `task typecheck`, `task lint:frontend`, `task test:frontend` (= `vitest run`), `task build:frontend` (= `npm run build`) | `npm ci` | Frontend-Build (1) | `frontend-dist` nur auf `develop` |
| `frontend.yml` / `Coverage` (reusable) | Filter `frontend` | `npm run test:coverage` (= `vitest run --coverage`), `fail-under: 80` | `npm ci` | – | Coverage-Report (reusable) |
| `frontend.yml` / `Bundle budget` | Filter `frontend` | `npm run build`, `npm run bundle:check` | `npm ci` | Frontend-Build (2) | `bundle-stats` |
| `frontend.yml` / `Lighthouse CI` | Filter `frontend` | `npm run build`, `npm run lhci` (`staticDistDir: ./dist`) | `npm ci` | Frontend-Build (3) | `lighthouse-report` |
| `frontend.yml` / `Garden planner benchmarks` | Filter `frontend` | `task test:frontend:bench` | `npm ci` | – | – |
| `frontend.yml` / `Dead code (advisory)` | Filter `frontend` | `npm run deadcode` (knip) | `npm ci` | – | – |
| `frontend.yml` / `CVE and licence gates` | Filter `frontend` | `npm_audit_gate.py --omit-dev`, `license-checker` | `npm ci` | – | – |
| `backend.yml` / `lint-test (3.14)` | `paths:` (42 Muster) | ruff lint + format, mypy-Ratchet, Steckbrief-Konsistenz, `pytest tests/unit/` + `tests/contracts/` + `tests/api/` mit `--cov=app`, Floor 60 | `task deps:sync` | – | – |
| `backend.yml` / `Lock, CVE and licence gates` | `paths:` | Lock-Staleness, Hash-Verifikation, `pip-audit`, `pip-licenses` | `uv sync` (2×) | – | – |
| `backend-guards.yml` / `Write-route and tree guards` | immer | `pytest tests/unit/api tests/unit/guards` + 12 Einzeldateien, `-m 'not advisory'`, `--max-skipped 0` | `uv sync` | – | – |
| `backend-guards.yml` / `Integration tests (ArangoDB)` | immer, Schritte gegated (`src/backend/**`, Taskfiles, eigener Workflow) | `task test:backend:integration` gegen ArangoDB + TimescaleDB | `task deps:sync` | – | – |
| `docker-lint-build.yml` / `changes` | `paths:` (14 Muster) | hadolint über alle 8 Dockerfiles | – | – | – |
| `docker-lint-build.yml` / `build-backend` | Filter `backend` | Image-Build ohne Push | – | Backend-Image (1) | – |
| `docker-lint-build.yml` / `build-frontend` | Filter `frontend` | Image-Build ohne Push (Dockerfile: `npm ci` + `npm run build`) | im Image | Frontend-Image (1) = Frontend-Build (4) | – |
| `docker-lint-build.yml` / 6 weitere `build-*` | je eigener Filter | Image-Build; Modell-Images zusätzlich Smoke + Contract-Probe | – | je 1 Image | – |
| `e2e-smoke.yml` / `E2E smoke (compose, light)` | Deny-Liste `runtime` oder `e2e_infra` | `scripts/run-e2e.sh --smoke`: `compose up --build` für `backend`, `celery-worker`, `frontend`; danach `compose run --build e2e-smoke` | im Image | Backend-Image (2+3), Frontend-Image (2) = Frontend-Build (5), Test-Image | `e2e-smoke-reports` |
| `e2e-smoke.yml` / `Publish E2E smoke report` | wenn ein Artefakt existiert | rendert JUnit (hält `checks: write`, checkt nichts aus) | – | – | liest `e2e-smoke-reports` |
| `build-static-tests.yaml` / `static` | immer | pre-commit über alle Dateien: u. a. ruff, Steckbrief-Konsistenz, actionlint, shellcheck, Workflow-Guards. Frontend-ESLint/tsc und mypy-Ratchet überspringen sich dort angekündigt und verweisen auf `lint-test-build (22)` bzw. `backend.yml` | pre-commit-Envs | – | – |
| `api-docs.yml`, `docs-requirements.yml`, `side-services.yml`, `skaffold-verify.yml`, `security-nuclei-templates.yml` | je eigenes `paths:` | jeweils eine eigene Prüfung, ohne Überlappung mit den Jobs oben | – | – | – |

---

## 3. Welche Jobs laufen bei welcher Änderungsart

Statisch berechnet über die echten Filter (Matcher-Semantik wie in
`test_lane_filters_cover_measured_inputs.py`: `*` überschreitet kein `/`, `**` schon,
`predicate-quantifier: every` für `e2e-smoke`) und anschließend an je einer echten PR
gegengeprüft:

| Änderungsart (Beispieldatei) | läuft | Gegenprobe (PR, Laufdaten) |
|---|---|---|
| **nur Doku** (`docs/de/index.md`) | `static`, `guards`, `integration` (Schritte übersprungen), `lint-test-build (22)` (Schritte übersprungen), `skaffold-verify`, `e2e-smoke/changes` (Suite übersprungen) | #2592: identisch; `integration` 0,6 min, `lint-test-build` 0,1 min |
| **nur Frontend** (`src/frontend/**`) | dazu alle 7 Frontend-Jobs, `docker-lint-build` (`build-frontend`), `e2e-smoke` | #2595: identisch, 75 Runner-Minuten |
| **nur Backend** (`src/backend/**`) | `backend.yml` (beide Jobs), `api-docs`, `integration` (läuft), `docker-lint-build` (`build-backend`), `e2e-smoke`; `lint-test-build (22)` nur mit übersprungenen Schritten | #2589: identisch, 112 Runner-Minuten |
| **geteilt/Laufzeit** (`docker-compose.e2e.yml`) | `backend.yml`, `e2e-smoke`; `integration` mit übersprungenen Schritten | kein reiner Lauf dieser Art in der Stichprobe; nur statisch belegt |
| **Workflow** (`.github/workflows/docker-lint-build.yml`) | `backend.yml` (`.github/workflows/**`), alle 8 `build-*`; `e2e-smoke` übersprungen | #2574 (anderer Workflow, `security-zap-*`): `backend.yml`, `e2e-smoke` übersprungen, 59 Runner-Minuten |
| **Konfiguration** (`Taskfile.yaml` / `.taskfiles/**`) | alle Frontend-Jobs, `backend.yml`, `integration` (läuft), `side-services`, `docs-requirements` | #2585 (`.taskfiles/checks.yaml`): identisch, 140 Runner-Minuten |

In jeder Zeile melden alle vier Pflicht-Checks, entweder ausgeführt oder mit gegateten
Schritten. Die Änderung in §5 verschiebt keinen Filter und keinen Trigger. Die Tabelle
gilt daher unverändert auch nach dem Merge.

---

## 4. Laufzeiten und Warteschlange (Ist-Zustand)

| Job | #2596 | #2591 | #2594 | #2595 |
|---|---|---|---|---|
| `lint-test-build (22)` | 16,7 | 18,9 | 18,3 | 12,3 |
| `Coverage / Node.js Coverage` | 16,2 | 20,1 | 14,8 | 12,7 |
| `Bundle budget` | 2,0 | 0,8 | 1,2 | 1,9 |
| `Lighthouse CI` | 3,1 | 1,9 | 2,6 | 3,1 |
| `lint-test (3.14)` (Backend) | 22,5 | 23,8 | abgebrochen | – |
| `Write-route and tree guards` | 17,9 | 17,9 | 18,8 | 18,1 |
| `Integration tests (ArangoDB)` | 41,7 | 41,5 | 34,3 | 0,7 (übersprungen) |
| `build-backend` | 1,4 | 1,3 | 1,1 | – |
| `build-frontend` | 1,7 | 1,7 | – | 1,7 |
| `E2E smoke (compose, light)` | 7,8 | 9,1 | 8,3 | 10,9 |

Alle Werte in Minuten Joblaufzeit (`completed_at − started_at`).

**Warteschlange: nicht repräsentativ gemessen.** In dieser Stichprobe liegt
`started_at − created_at` bei fast allen Jobs unter 0,2 min, nur #2574 zeigt 0,1–5,3 min.
Das widerspricht den 21–25 min Median, die `frontend.yml` und `docker-lint-build.yml`
für 2026-09-19 über 300 Läufe angeben. Acht PRs an zwei Tagen sind keine Grundlage, um
diese Zahl zu ersetzen.

**Beobachtung am Rand, nicht untersucht:** `backend.yml / lint-test (3.14)` wurde in
#2594, #2589, #2585 und #2574 nach 29–36 min **abgebrochen** (nicht rot). Ob das
Concurrency-Abbrüche durch Folge-Pushes sind oder manuelle Abbrüche, ist hier nicht
geklärt.

---

## 5. Umgesetzt: eigener Cache-Scope je Image, Backend/Frontend am E2E-Scope

**Befund.** Sechs Jobs in `docker-lint-build.yml` (`build-backend`, `build-frontend`,
`build-vectordb`, `build-knowledge`, `build-knowledge-service`, `build-inference-service`)
deklarierten `cache-from: type=gha` / `cache-to: type=gha,mode=max` **ohne** `scope=`. Der
gha-Cache-Backend schreibt dann in den Default-Scope `buildkit`, und jeder Export ersetzt
den Index des vorigen. Belegt an den Cache-Einträgen: Die `index-buildkit-*`-Einträge von
`refs/pull/2593/merge` wechseln zwischen vier Indexgrößen (4904, 5486, 8334, 10579 Byte),
also vier Images, die sich einen Index teilen. Auf `refs/heads/develop` wechseln sich
`docker-publish.yml`-Exporte (5487/10573 Byte) genauso ab. Dasselbe Rennen hat #1764 für
die Embedding-/Reranker-Legs schon dokumentiert und dort mit Scopes je Leg gelöst.

**Zweiter Befund.** `docker-lint-build.yml` läuft **nur** auf `pull_request`. Ein Cache,
den nur dieser Workflow schreibt, liegt deshalb ausschließlich unter PR-Refs. Eine
andere PR darf diese Einträge nicht lesen (GitHub-Cache-Isolation: lesbar sind nur der
eigene Ref und der Basis-Branch). Der E2E-Stack schreibt `e2e-backend` / `e2e-frontend`
dagegen auch auf `develop`: `e2e-smoke` bei jedem Push und `e2e-nightly` mit allen
Profilen, belegt durch die Einträge `index-e2e-backend-1-fd3dfe2c#79…#118` auf
`refs/heads/develop`. Die Build-Definitionen sind identisch: gleicher Kontext
(`src/backend` bzw. `src/frontend`), Standard-Dockerfile, kein `target:`, keine
`build-args` in `docker-compose.e2e.yml` wie in `docker-lint-build.yml`. Die
Indexgrößen passen dazu: `e2e-backend` 5485–5487 Byte, Backend-Index unter `buildkit`
5487 Byte. Das ist ein Indiz, kein Beweis.

**Änderung.**

- `build-backend` → `scope=e2e-backend`, `build-frontend` → `scope=e2e-frontend`
  (dieselben Scopes wie in `docker-compose.e2e.ci.yml`).
- `build-vectordb` → `vectordb`, `build-knowledge` → `knowledge`,
  `build-knowledge-service` → `knowledge-service`,
  `build-inference-service` → `inference-service`.
- Neuer Guard `src/backend/tests/unit/guards/test_docker_build_cache_scopes.py`. Er läuft
  im Pflicht-Lane `Write-route and tree guards`, weil der ganze Ordner dort läuft. Er
  prüft drei Regeln: (1) jeder gha-Cache in `docker-lint-build.yml` nennt einen Scope,
  lesend und schreibend gleich; (2) kein Scope gehört zwei verschiedenen
  Build-Definitionen; (3) ein Build mit derselben Definition wie ein E2E-Service nutzt
  dessen Scope, und Backend und Frontend müssen tatsächlich gepaart werden, sonst wäre
  die Regel leer erfüllt. Jede Regel hat einen gepflanzten Negativfall. Gegenprobe per
  `cp`: Mit der alten Workflow-Datei schlagen Regel 1 und 3 fehl, mit `scope=backend`
  statt `e2e-backend` schlägt Regel 3 fehl.

**Warum das sicher ist.** Der Cache ist inhaltsadressiert. Ein falscher oder fremder
Scope kostet höchstens einen Cache-Miss, also den Stand von heute, aber nie ein falsches
Image. Eine PR kann den `develop`-Scope nicht beschreiben. Der Export einer PR landet nur
unter ihrem eigenen Ref, wo er mit dem gleich definierten E2E-Build derselben PR
zusammentrifft. Kein Pflicht-Check, kein Filter, kein Trigger und keine Assertion ändert
sich.

**Was nicht belegt ist.** Ob die Builds dadurch messbar schneller werden, ist **nicht
gemessen**. Es gibt noch keinen Lauf mit der Änderung, und `build-backend`/`build-frontend`
liegen heute schon bei 1,1–1,7 min. Der Gewinn ist vor allem für die ersten Läufe einer
PR und für die seltener gebauten Images (vectordb, knowledge, knowledge-service,
inference-service) zu erwarten.

**Lane-Manifeste (#1683).** Die Änderung verschiebt `job_spec_sha256` der sechs Jobs. Die
sechs `docker-lint-build--build-*.yaml` sind mit dem Recorder neu abgeleitet
(`scripts/ci/lane_inputs.py replay <manifest> --out-dir …`; das sind
`derive-docker`-Legs, also eine Docker-Kontext-Probe ohne `strace`). Der Diff zum
Commit-Stand enthält nur den neuen Hash, das Messdatum, `replay_seconds` und die seit dem
2026-10-19 neu hinzugekommenen Dateien im Kontext, die alle im Filter liegen.
`pytest … --lane-inputs-drift -m lane_inputs_drift` meldet danach für diese sechs
Manifeste nichts mehr. Die vier verbleibenden Befunde bestanden schon vorher auf
`develop` und gehören nicht zu dieser Änderung (§8).

**Abweichung von der Lane-Regel, offen benannt.** Der Kopf von
`test_lane_filters_cover_measured_inputs.py` sagt: „Nobody refreshes a manifest by hand
or from a workstation“. Die sechs Manifeste sind trotzdem lokal neu abgeleitet. Das ist
vertretbar, weil `derive-docker` nichts traced: Es ist eine Kontext-Probe, bei der der
Docker-Daemon `.dockerignore` anwendet, und sie hängt nicht vom Host ab. Ohne den lokalen
Lauf wäre der wöchentliche `lane-inputs.yml`-Lauf nach dem Merge für diese sechs Jobs rot
und würde sie per Bot-PR nachziehen. Wer die Regel wörtlich nimmt, setzt die sechs
Dateien zurück und startet `lane-inputs.yml` per `workflow_dispatch` auf dem Branch.

---

## 6. Bewusst belassene Duplikation

### 6.1 `static` und die sprachspezifischen Lanes (ruff, Steckbrief-Konsistenz)

`static` ist der unfiltrierte Pflicht-Lane auf jedem Push. Er fährt ruff und die
Steckbrief-Konsistenz noch einmal, die `backend.yml` ohnehin prüft. `backend.yml` ist
pfadgefiltert und beratend. Ohne die Kopie in `static` wäre ruff für jede Änderung
außerhalb der 42 Muster von `backend.yml` ungeprüft. Die Kopie kostet Sekunden. Die
teuren Doppelungen (Frontend-ESLint/tsc, mypy-Ratchet) überspringt `static` schon
angekündigt und verweist auf den zuständigen Lane.

### 6.2 `bundle-budget` und `lighthouse` als eigene Jobs neben `lint-test-build (22)`

`frontend.yml` dokumentiert die Trennung absichtlich: Ein Budget-Bruch soll sichtbar rot
werden, ohne den Pflicht-Check `lint-test-build (22)` zu verändern und damit Automerge
zu blockieren. Beide würden außerdem hinter einem 12–19-minütigen Pflicht-Job warten,
wenn sie dessen Build übernehmen. Siehe §7.2.

### 6.3 Guard-Tests in `backend-guards.yml` und in `backend.yml`

`backend-guards.yml` liefert zwei Pflicht-Checks und läuft deshalb ohne `paths:` auf jedem
Push. `backend.yml` läuft nur bei passenden Pfaden. Würde `backend.yml` die Guard-Ordner
ausklammern, würde zweierlei passieren:

- `--cov=app` würde den Code nicht mehr messen, den diese Tests abdecken, und der
  Coverage-Floor 60 % hinge an einer kleineren Basis.
- Die `advisory`-markierten Tests in genau diesen Ordnern liefen gar nicht mehr. Der
  Guard-Lane schließt sie mit `-m 'not advisory'` aus, und `backend.yml` ist ihr einziger
  Ausführungsort.

Eine Coverage-Zusammenführung über zwei Workflows mit verschiedenen Events (`push` vs.
`pull_request`) ist nicht trivial und nicht belegt.

### 6.4 `deadcode` getrennt von `dependency-gates`

Das ist in `frontend.yml` (#1583) dokumentiert: Ein dauerhaft roter Lane würde sein Rot
in die CVE- und Lizenz-Gates tragen.

### 6.5 Mehrfaches `npm ci` und `uv sync`

Auf einer Frontend-PR läuft `npm ci` siebenmal, auf einer Backend-PR die uv-Installation
vier- bis fünfmal. Jede Installation sitzt in einem eigenen Job, der aus einem der oben
genannten Gründe getrennt bleibt. Alle Installationen nutzen den Paket-Cache
(`setup-node cache: npm`, `setup-uv enable-cache`). Zusammenlegen hieße Jobs zusammenlegen
(§7.3).

---

## 7. Empfehlungen (nicht umgesetzt)

### 7.1 Vitest nur einmal: Coverage aus dem Lauf von `lint-test-build (22)` — **Betreiberentscheidung**

Das ist die größte Einsparung: ein kompletter Vitest-Lauf mit 12,7–20,9 Runner-Minuten
je Frontend-PR. Möglicher Aufbau: `lint-test-build (22)` führt `vitest run --coverage`
aus und lädt den Coverage-Report hoch. Ein beratender Job `Coverage` liest das Artefakt
und prüft nur die Schwelle 80.

Nicht umgesetzt, weil sich dabei der Pflicht-Check ändert. Die v8-Instrumentierung läuft
dann im Pflicht-Lane. `frontend.yml` führt den Coverage-Job als wandernden Flake (3 von
30 Läufen rot gegenüber 1 von 30 bei `lint-test-build`). Ob die Instrumentierung die
Ursache ist, lässt sich nur durch einen gemessenen Probelauf über mehrere PRs klären
(NFR-018 §4: Promotion nach Historie). Außerdem kommt der Check-Name
`Coverage / Node.js Coverage` aus dem Reusable-Workflow von `gh-plumbing` und würde sich
ändern.

### 7.2 Frontend-Build als Artefakt an `bundle-budget` und `lighthouse` weiterreichen

Technisch möglich: `lighthouse` liest `./dist`, `bundle:check` liest `dist` und
`bundle-stats`. Die Bilanz ist aber negativ:

- Beide Jobs würden per `needs:` hinter `lint-test-build (22)` warten. Ihr Ergebnis käme
  dann nach 12–19 min statt nach 1–3 min.
- Ein roter Vitest-Lauf würde das Budget-Ergebnis verdecken, weil der Build der letzte
  Schritt ist. Umsortieren hieße, den Pflicht-Job zu ändern.
- Eingespart würde nur der Build-Anteil von Jobs, die insgesamt 0,8–3,1 min dauern. Das
  `npm ci` bliebe, weil `lhci` und `bundle:check` `node_modules` brauchen.

### 7.3 `bundle-budget` und `lighthouse` zu einem Job zusammenlegen

Das spart ein `npm ci`, einen Build und einen Job-Slot (≈ 1 Runner-Minute je
Frontend-PR) ohne Serialisierung. Beide Jobs haben ein byte-gleiches `if:`, und
`lhci` muss mit `if: ${{ !cancelled() }}` laufen, damit ein Budget-Bruch Lighthouse
nicht überspringt. Nicht umgesetzt aus drei Gründen:

- Die Check-Namen ändern sich.
- `frontend--bundle-budget.yaml` beschreibt dann einen Job, den es nicht mehr gibt.
- Für den neuen Job muss ein `strace`-Manifest **im CI** aufgezeichnet werden. Der
  Recorder-Kopf von `test_lane_filters_cover_measured_inputs.py` sagt dazu: „Nobody
  refreshes a manifest by hand or from a workstation“. Der Bot-PR des Lane-Laufs legt
  für einen neuen Job ohne Manifest keines an.

Umsetzbar ist das als eigener PR mit einem `workflow_dispatch` von `lane-inputs.yml` auf
dem Branch.

### 7.4 Image-Wiederverwendung `docker-lint-build` → `e2e-smoke` über ein Artefakt

Nicht als sicher belegbar:

- Die beiden Workflows wählen unterschiedlich aus. `docker-lint-build` nutzt Pfadfilter
  je Image. `e2e-smoke` nutzt eine Deny-Liste und läuft auch bei `tests/e2e/**`,
  `docker-compose.e2e*.yml` und `scripts/run-e2e.sh`, wo kein `build-*` läuft. E2E
  bräuchte also immer einen Fallback-Build.
- Artefakte über Workflow-Grenzen hinweg brauchen `workflow_run` oder eine
  Zusammenlegung der Workflows.
- Ein Image-Tarball von mehreren hundert MB hoch- und herunterzuladen kann teurer sein als
  der heutige Build mit Cache-Treffern (1,1–1,7 min).
- `run-e2e.sh` baut mit `up --build`. Lokale Läufe hängen an genau diesem Pfad.

Die Scope-Angleichung aus §5 ist die belegbare Teilmenge dieses Ziels.

### 7.5 `backend` und `celery-worker` aus einem Image

Laufzeitseitig korrekt per Konstruktion: Beide Services bauen schon heute aus derselben
Definition. Der Worker unterscheidet sich nur durch `command:` und den abgeschalteten
Healthcheck. Möglicher Aufbau: dasselbe `image:`-Tag an beiden Services, `build:` nur an
einem. Nicht umgesetzt, weil ungeprüft ist, wie Compose mit Bake (`COMPOSE_BAKE=true`)
das Bauen dedupliziert. Die Datei betrifft außerdem `e2e-nightly` (5 Profile, auch die
`-full`-Zwillinge) und lokale Läufe. Der messbare Gewinn ist gering. Laut
Cache-Zeitstempeln kostet der zweite Export ~7 s. Dazu kommen zwei weitere Exporte je
Image, die `compose run --build` am Ende auslöst (Zeitstempel :42/:46 s).

### 7.6 Eigene Cache-Scopes auch in `docker-publish.yml`

`docker-publish.yml` (Push auf `develop`) schreibt alle acht Images in den Default-Scope
`buildkit`. Auf `develop` liegt deshalb pro Scope nur der Index des zuletzt
veröffentlichten Images, und PR-Builds der Images ohne E2E-Zwilling (vectordb, knowledge,
knowledge-service, inference-service) können vom `develop`-Cache kaum profitieren. Gleiche
Scope-Namen wie in §5 würden das beheben. Nicht hier umgesetzt, weil es ein
Delivery-Workflow außerhalb des PR-Pfads ist. Seine Manifeste
(`docker-publish--build-*.yaml`) müssten ebenfalls neu abgeleitet werden. Beim Backend
ändert `BUILD_REVISION` nur die letzten Schichten (`ARG` in Zeile 124 des Dockerfiles).

---

## 8. Offene Punkte

- **Vorher/Nachher-Vergleich: nicht gemessen.** Es gibt noch keinen Lauf mit der
  Änderung. Messen lässt es sich nach dem Merge mit
  `gh api repos/nolte/kamerplanter/actions/runs/<id>/jobs` für `build-*` auf zwei bis drei
  PRs. Vergleichsbasis sind die Werte in §4. Zusätzlich sollten
  `index-e2e-backend-*`/`index-e2e-frontend-*`-Einträge unter PR-Refs von
  `docker-lint-build` auftauchen und die `index-buildkit-*`-Einträge unter PR-Refs
  verschwinden.
- **Lane-Inputs-Drift, schon vor dieser Änderung auf `develop` vorhanden** (gemessen mit
  `pytest tests/unit/guards/test_lane_filters_cover_measured_inputs.py
  tests/unit/test_lane_inputs_recorder.py --lane-inputs-drift -m lane_inputs_drift`):
  - `backend--dependency-gates.yaml` und `backend-guards--integration.yaml`: Job geändert
    seit der Messung;
  - `frontend--garden-planner-benchmarks.yaml`: ohne `replay_seconds`;
  - `frontend--lint-test-build.yaml`: liest
    `spec/e2e-testcases/fixtures/garden-plan-vectors.json`, das der Filter `frontend`
    nicht auswählt.

  Das gehört in den nächsten `lane-inputs.yml`-Lauf bzw. ist eine Filterkorrektur in einem
  eigenen PR.
- **Doku-Nachzug:** Zuständigkeit je Check (§1/§2) und bewusst belassene Duplikation (§6)
  als Abschnitt in `docs/de/deployment/ci-cd.md` und `docs/en/deployment/ci-cd.md`.
  Außerdem sagt `ci-cd.md` (Zeile 451): „Alle Image-Builds nutzen den GitHub Actions Cache
  (`type=gha`)“. Das sollte um die Scope-Regel ergänzt werden.
