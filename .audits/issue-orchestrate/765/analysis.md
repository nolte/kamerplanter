---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 765
classification: feature-request
secondary-classes: [infra, docs]
route: direct
status: draft
created: 2026-07-26
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #765 — Attach the OpenAPI document as a release asset (generated at release build, never checked in)
- **URL**: https://github.com/nolte/kamerplanter/issues/765
- **Labels**: enhancement, cicd, backend
- **Autor / Trust**: `nolte` (Repository-Owner, `admin`-Permission) → **trusted author** nach
  `spec/claude/trusted-author-injection-guard/`; die Checkboxen im Issue-Body dürfen als
  Arbeitsauftrag gelesen werden. Keine Kommentare vorhanden.
- **Linked items**: PR #766 (gemergt — entfernte den eingecheckten Snapshot, gitignorete ihn und
  baute die `api-docs`-CI-Lane auf Export+Lint on-the-fly um). `closedByPullRequestsReferences`: leer.
- **Prior art checked**: kein Eintrag unter `project/features/`, kein `project/roadmap.md`-Item,
  kein offener PR referenziert #765. Kein Artefakt unter `project/requirements/`.

### Gegroundete Ist-Lage (Repo-Oberfläche)

| Artefakt | Zustand |
|---|---|
| `src/backend/scripts/export_openapi.py` | vorhanden, reproduzierbar (`--out`, `--check`, sortierte Keys, deterministisch); validiert zusätzlich die Tag-Deklaration gegen `app/api/v1/openapi_tags.py` |
| `Taskfile.yaml` → `openapi:export` | vorhanden (`dir: src/backend`, `python -m scripts.export_openapi --out openapi.json`) |
| `.gitignore:89-90` | `src/backend/openapi.json` ignoriert — Build-Artefakt, nie eingecheckt |
| `.github/workflows/api-docs.yml` | exportiert + spectral-lintet + lädt Workflow-Artefakt `openapi` hoch. **Referenz-Installpfad**: `pip install --require-hashes -r requirements.txt` + `pip install --no-deps -e .` auf Python 3.14 |
| `.github/workflows/release-publish.yml` | delegiert **vollständig** an `nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml@bab4f9d…` (v1.1.26). Das reusable ist fremdverwaltet und **nicht änderbar** → der Asset-Upload muss als **eigener Job im kamerplanter-Workflow** ergänzt werden |
| Reusable-Verhalten | checkt explizit `ref: develop` aus, resolved genau **einen** Draft mit `inputs.tag`, prüft dessen `target_commitish` gegen `origin/develop`, und flippt am Ende `draft=false` (außer bei `dry_run`). `inputs.asset-filename` ist **HACS-spezifisch** und kein generischer Asset-Hook. `auto-align` ist hier nicht gesetzt (Default `false`) |
| Offener Draft | `v0.0.24` |

### Auslöser mit erhöhter Priorität — die Doku behauptet die Funktion bereits

Drei Stellen behaupten heute schon, der Release-Build hänge das Dokument als Asset an, **obwohl er
das nicht tut**. PR #766 hat den Zielzustand vorweggeschrieben:

- `docs/de/api/overview.md:31` — „… der Release-Build hängt es als Release-Asset an."
- `docs/en/api/overview.md:31` — „… the release build attaches it as a release asset."
- `Taskfile.yaml:97-98` und der Modul-Docstring von `src/backend/scripts/export_openapi.py`

Die Doku-Aufgabe ist damit **nicht** „eine Behauptung erfinden", sondern „den Download-Ort
ergänzen und die bestehende Behauptung wahr machen".

## Classification

- **Primary class**: `feature-request`
- **Secondary class(es)**: `infra`, `docs`
- **Rationale**: Das Issue fügt der Release-Pipeline eine neue Fähigkeit hinzu (Asset-Publikation);
  es ist keine Remediation eines roten Workflows, deshalb greift der `infra`-Kurzschluss nach
  `workflow-health-triage` bewusst **nicht**.

## Scope

- **In scope** (Operator-Entscheidung, 2026-07-26):
  1. `.github/workflows/release-publish.yml` um Export + Anhängen von `openapi.json` an das Release erweitern.
  2. `docs/de/api/overview.md` + `docs/en/api/overview.md` auf den stabilen Release-Asset-Downloadlink zeigen lassen.
- **Out of scope**:
  - **Versionierter Asset-Name `openapi-<tag>.json`** (Issue-Checkbox 2, dort selbst als „Optionally"
    markiert): Der Operator hat sich für **ausschließlich `openapi.json`** entschieden. Konsequenz,
    die im PR festgehalten wird: der Dauerlink
    `https://github.com/nolte/kamerplanter/releases/latest/download/openapi.json` funktioniert
    (stabiler Asset-Name ist dafür Voraussetzung); ein Pin auf eine bestimmte Version geschieht über
    die Release-Detailseite des jeweiligen Tags, nicht über einen versionierten Dateinamen.
  - Die vier **deferred audit findings** aus dem Issue-Body (Request/Response-Beispiele,
    equivalent-path-Ambiguität bei `/api/v1/profiles/{…}/{…}`, Trailing-Slash `/api/v1/tenants/`,
    31 bewusst schemalose 2xx-Responses). Sie bleiben als Backlog im Issue-Text stehen.
    **Folge: Das Issue wird durch diesen PR NICHT geschlossen** — der PR referenziert es mit
    `Refs #765` statt `Closes #765`.
  - `task openapi:export` und die `api-docs`-CI-Lane bleiben unverändert (Issue-Checkbox 4 ist
    bereits erfüllt, „stays as-is").

## Requirements gate

- **Kein Artefakt unter `project/requirements/`** deckt #765 ab; `U_gate` damit unter `τ_high`.
- **Operator-Override erteilt (2026-07-26)** statt eines `requirements-elicit`-Laufs.
  Begründung: Das Issue ist bereits die verdichtete Ausgabe des API-Doku-Audits vom 2026-07-24 und
  als präzise Checkboxen-Liste formuliert; die Akzeptanzkriterien sind mechanisch prüfbar
  (liegt das Asset am Release, verlinkt die Doku es), nicht interpretationsbedürftig. Ein
  Elicitation-Interview hätte kein zusätzliches Verständnis erzeugt.

## Route

- **Decision**: `direct`
- **Rationale**: Ein kohärentes Outcome (das OpenAPI-Dokument ist für Konsumenten ohne Code-Checkout
  beziehbar), ein einzelner PR-Strang, kein neues oder umgehängtes Roadmap-Item. Der einzige Teil des
  Issues, der die Pipeline gerechtfertigt hätte — die equivalent-path-Ambiguität mit ihrem breaking
  Path-Change — ist explizit out of scope und bleibt als dokumentierter Backlog im Issue.

## Work packages

### P1 — Release-Build exportiert das OpenAPI-Dokument und hängt es als Release-Asset an

- **Problem statement**: `release-publish.yml` delegiert vollständig an ein fremdverwaltetes
  reusable Workflow, das keinen generischen Asset-Hook anbietet. Das Release wird heute ohne
  OpenAPI-Dokument veröffentlicht, obwohl Doku, Taskfile und Script-Docstring das Gegenteil behaupten.
- **Acceptance criteria**:
  1. `.github/workflows/release-publish.yml` erhält einen neuen Job (Arbeitsname `openapi-asset`),
     der `actions/checkout` mit **`ref: develop`** ausführt (identisch zum reusable, damit der Export
     aus demselben Baum stammt, der veröffentlicht wird), Python 3.14 mit
     `allow-prereleases: true` setzt und die Dependencies über den **gepinnten, hash-verifizierten**
     Pfad installiert: `pip install --require-hashes -r requirements.txt` gefolgt von
     `pip install --no-deps -e .` — byte-gleich zur `api-docs.yml`/`backend.yml`-Installwahrheit.
  2. Der Job exportiert mit `python -m scripts.export_openapi --out openapi.json` (Working Directory
     `src/backend`).
  3. Der Job lädt die Datei unter dem **stabilen** Namen `openapi.json` an das Release
     `${{ inputs.tag }}` hoch (`gh release upload "$TAG" openapi.json --clobber`), und **verifiziert
     anschließend**, dass das Asset am Release hängt (`gh release view "$TAG" --json assets` und
     `jq`-Prüfung auf den Namen) — ein stiller Upload-Fehlschlag darf den Job nicht grün lassen.
  4. Der Upload läuft **vor** dem Draft→Published-Flip: der bestehende `publish`-Job erhält
     `needs: openapi-asset`, damit das Release im Moment seiner Veröffentlichung bereits vollständig ist.
  5. Bei `inputs.dry_run == true` wird **exportiert, aber nicht hochgeladen** (der Export bleibt als
     Validierung erhalten, es entsteht keine sichtbare Nebenwirkung). Der Skip ist als
     Step-`if`-Bedingung sichtbar, nicht als stiller `continue-on-error`.
  6. Der Job deklariert die benötigten `permissions: contents: write` explizit auf Job-Ebene.
  7. Alle Third-Party-Actions sind per **Commit-SHA mit Versionskommentar** gepinnt, in exakt der
     Schreibweise der bestehenden Workflows (`actions/checkout@3d3c42e5…  # v7.0.1`,
     `actions/setup-python@5fda3b95…  # v7.0.0`).
  8. Ein erklärender Kommentarblock am Job begründet die Reihenfolge (`needs`), den
     `dry_run`-Skip und warum der Upload nicht im reusable liegt.
  9. Der bestehende Kommentarblock oben in `release-publish.yml` bleibt inhaltlich intakt.
  10. Der Workflow ist YAML-valide und `actionlint`-sauber; der required Check `static` bleibt grün.
- **Touched files / artifacts**: `.github/workflows/release-publish.yml`
- **Specialist**: `nolte-engineering:fullstack-developer`
  (Description nennt ausdrücklich „end-to-end across backend, frontend, **and infrastructure**";
  im Runtime-Katalog gibt es keinen dedizierten CI-Workflow-Autor. `workflow-health-triage` ist
  Remediation für *rote* Lanes, `bjw-common-deployment-generator` ist Helm-spezifisch, die
  `quality-gate-enforcer`/`deployment-bestpractices-reviewer` sind read-only Auditoren.)
- **Depends on**: none

### P2 — API-Doku benennt das Release-Asset als stabilen Download-Ort

- **Problem statement**: `docs/{de,en}/api/overview.md` nennen heute nur das *Workflow*-Artefakt und
  behaupten den Release-Asset-Anhang, ohne Konsumenten zu sagen, wo sie ihn abholen. Wer den Code
  nicht auscheckt, hat keine benannte Bezugsquelle.
- **Acceptance criteria**:
  1. Beide Sprachdateien nennen
     `https://github.com/nolte/kamerplanter/releases/latest/download/openapi.json`
     als stabilen Download-Ort für die jeweils letzte veröffentlichte Version.
  2. Beide erklären, dass ein Pin auf eine bestimmte Version über die Release-Detailseite des
     gewünschten Tags erfolgt (der Asset-Name ist bewusst versionslos — siehe Out-of-scope oben).
  3. Die drei Bezugswege sind unterscheidbar benannt: **lokal** (`task openapi:export`),
     **pro Backend-Änderung** (Workflow-Artefakt der `api-docs`-Lane, CI-intern) und
     **pro Release** (Release-Asset, der empfohlene Weg für externe Konsumenten).
  4. DE und EN sind inhaltlich paritätisch (`spec/style-guides/DOCS.md`: DE kanonisch, EN Spiegel);
     informelles „du" in DE beibehalten, Ton der Umgebung.
  5. Keine sonstigen Abschnitte der Overview-Seiten verändert.
  6. `mkdocs build --strict` läuft durch (kein neuer Link-/Nav-Fehler).
- **Touched files / artifacts**: `docs/de/api/overview.md`, `docs/en/api/overview.md`
- **Specialist**: `mkdocs-documentation` (projektlokaler Agent unter `.claude/agents/`; Description:
  mehrsprachige MkDocs-Material-Doku nach NFR-005 — genauere Passung als
  `nolte-shared:audience-doc-author`, das ein `audience-identify`-Artefakt voraussetzen würde)
- **Depends on**: P1 (die Doku beschreibt das Verhalten, das P1 herstellt; sachlich erst nach P1 wahr)

## Dependency ordering

`P1 → P2`

Sequenziell auch aus Werkzeuggründen: beide Pakete schreiben in denselben Worktree, parallele
schreibende Agenten auf einem geteilten Tree kollidieren.

## Risks

| Risiko | Mitigation |
|---|---|
| `gh release upload` gegen ein **Draft**-Release: Auflösung erfolgt über den Tag-Namen, der als Git-Ref zum Upload-Zeitpunkt noch **nicht existiert**. | `gh` löst Releases auch als Draft über `tagName` auf (dasselbe Verfahren nutzt das reusable in „Resolve draft"). AC 3 verlangt zusätzlich eine explizite **Verifikation** des angehängten Assets, damit ein Fehlschlag laut wird statt still. |
| Reihenfolge falsch herum: Upload nach dem Flip ⇒ Fenster, in dem das Release öffentlich, aber unvollständig ist — und `release:published` ist bereits kaskadiert. | AC 4: `publish` bekommt `needs: openapi-asset`. |
| Neuer Job schlägt fehl ⇒ **Release blockiert**. | Bewusst akzeptiert: ein Release ohne das Dokument, das Doku und Taskfile versprechen, ist der schlechtere Zustand. Kein `continue-on-error`. Der `dry_run`-Pfad exportiert weiterhin und deckt Export-Brüche vor dem echten Release auf. |
| Export läuft gegen den falschen Baum (Dispatch-Ref ≠ Release-Inhalt). | AC 1: expliziter `ref: develop` im Checkout, identisch zum reusable. |
| Doppelter Lauf / Re-Dispatch erzeugt Asset-Konflikt (422 „already_exists"). | `--clobber` beim Upload. |
| Sicherheit: der Job braucht `contents: write` und lädt in ein öffentliches Release. | Kein Secret im Export (`export_openapi.py` importiert die App mit gepinnten Env-Flags, schreibt reines JSON), keine neue Secret-Nutzung außer `GITHUB_TOKEN`. Der Diff berührt eine Workflow-Datei mit Schreibrechten ⇒ **`security-review` läuft vor dem PR** (Operation 6). |

## Open questions

Keine — die drei Entscheidungen (Scope, Requirements-Override, Asset-Name) sind vom Operator am
2026-07-26 getroffen und oben festgehalten.

## Dispatch log

2026-07-26 P1 dispatched to `nolte-engineering:fullstack-developer` — Job `openapi-asset` in
`.github/workflows/release-publish.yml` ergänzt (`ref: develop`-Checkout, hash-verifizierter
Install, Export, `gh release upload --clobber`, eigener Verify-Step mit `jq -e`-Assertion,
`if: ${{ !inputs.dry_run }}` auf Upload+Verify, `permissions: contents: write` auf Job-Ebene,
SHA-gepinnte Actions); `publish` erhielt `needs: openapi-asset`. Alle 12 AC erfüllt.
`actionlint` war lokal nur ein leerer asdf-Shim — vom Orchestrator via
`docker run rhysd/actionlint` nachgeholt: **exit 0, keine Findings**. Zusätzliche Annahme des
Spezialisten: `GH_REPO: ${{ github.repository }}` gesetzt (Muster aus `docker-publish.yml`),
akzeptiert.

2026-07-26 P2 dispatched to `mkdocs-documentation` — `docs/{de,en}/api/overview.md`: Abschnitt zu
„OpenAPI-Schema beziehen" umgebaut auf eine Drei-Wege-Tabelle (Weg / Adressat / Bezugsort) mit
`https://github.com/nolte/kamerplanter/releases/latest/download/openapi.json` als empfohlenem Weg,
plus Begründung des bewusst versionslosen Asset-Namens. Alle 7 AC erfüllt.
Zwei Orchestrator-Korrekturen: (a) der `mkdocs build --strict`-Fehlschlag des Spezialisten lag am
rohen Aufruf ohne die Generator-Deps — das Repo-Target ist `task docs:build`
(`deps: [docs:catalog, docs:fact-tables, docs:venv]`), vom Orchestrator nachgeholt: **exit 0**,
anschließend `mkdocs build --strict` separat **exit 0**; (b) der Schlusssatz behauptete
„jeder einzelne Release trägt seine eigene Kopie" — gilt erst ab Einführung des Assets, per
Rückfrage korrigiert auf „Releases, die vor der Einführung dieses Assets veröffentlicht wurden,
enthalten es nicht" (bewusst **ohne** Versionsnummer, weil release-drafter die nächste Version aus
den PR-Labels ableitet und dieser PR einen `feat`-Anteil trägt — v0.0.24 ist nicht garantiert).

## Verification (Operation 6)

| Gate | Ergebnis |
|---|---|
| `actionlint` (via `docker run rhysd/actionlint`) | exit 0, keine Findings — lokal war nur ein leerer asdf-Shim vorhanden |
| `pre-commit run --files <3 geänderte Dateien>` | exit 0 (entspricht dem einzigen required CI-Check `static` = `reusable-pre-commit`) |
| `task docs:build` | exit 0 |
| `mkdocs build --strict` | exit 0 |
| `security-review` (Skill, diff-scoped) | **keine Findings**. `inputs.tag` erreicht die Shell nur über `env:` und als gequotetes `"$TAG"` → keine Script-Injection; Trigger ausschließlich `workflow_dispatch` (Write-Zugriff nötig); `contents: write` job-scoped und minimal. Hinweis: das Skill sammelte den Diff fälschlich aus dem primären Checkout — der Worktree-Diff wurde manuell geprüft |
| `code-security-reviewer` (whole-repo OWASP) | **nicht dispatcht** — bewusste Entscheidung: der Diff fügt keinen Anwendungscode hinzu, die security-relevante Fläche sind 88 Zeilen Actions-YAML, die der diff-scoped `security-review` vollständig abdeckt |

**Härtungs-Notiz unterhalb der Meldeschwelle** (gehört in die PR-Risk-Notes, kein Blocker): der Job
führt Repo-Code aus (`pip install -e .`, App-Import), während er den `contents: write`-Token hält.
Kein neuer Angriffsvektor — `api-docs.yml` macht denselben Install seit #766 — aber eine Trennung
von Export- und Upload-Job wäre eine echte Härtung.
