# Pre-Analyse #1741 — vier gemessene CI-Redundanzen

- Issue: https://github.com/nolte/kamerplanter/issues/1741 (Autor: nolte, Repository-Owner → vertrauenswürdig)
- Klassifikation: `infra` (primär), Begründung: ändert ausschließlich CI-Workflows, Lane-Manifeste und Guard-Tests; kein Produktcode.
  Nicht an `workflow-health-triage` abgegeben: kein roter Lauf, sondern eine Umbauentscheidung des Betreibers.
- Requirements-Gate: **Operator-Override** (Elternsitzung 2026-09-24) — das Issue trägt gemessene Akzeptanzkriterien.
- Route: direkt (ein Ergebnis, ein PR-Strang, kein Roadmap-Item).
- Spezialist: `nolte-shared:cicd-pipeline-design` (Workflow-Umbau) — in dieser Sitzung angewendet, nicht als
  separater Agent dispatcht, weil die Recorder-Schleife (push → `lane-inputs.yml` → Artefakt → commit) die
  Reihenfolge von Push und Aufzeichnung in einer Hand verlangt.

## Nachgemessene Behauptungen

| Behauptung | Befund | Beleg |
|---|---|---|
| (1) lint-test und Coverage laufen dieselben 12 579 Tests | **bestätigt** | Coverage-Job 107586214313: `collected 12579 items`, `12569 passed, 10 skipped`; lint-test 10 954+30+1 595 = 12 579 |
| (1) 10 Coverage-only-Skips | **erklärt** | `-rs` auf `git clone --depth 1`: 4× `test_applied_migration_sources_are_frozen.py` (kein vX.Y.Z-Tag), 4× `test_model_field_renames_have_migrations.py` (shallow), 1× `test_audit_oauth_links.py` (Commit fehlt), 1× `test_e2e_admin_env_containment.py:86` (auch in lint-test, Floor 1). Voll-Historie: 1 Skip |
| (2) Action baut implizit | **bestätigt, schärfer**: `hiberbee/github-action-skaffold@1.27.0` `src/index.js` `run()` führt `skaffold build` **bedingungslos** nach `command:` aus — per `command:` nicht abschaltbar; ersetzt durch eigene Composite-Action | Action-Quelltext am gepinnten SHA; Run-Log: 8 Images gebaut |
| (3) Frontend-lesende Tests = 3 Dateien | **teilweise falsch**: `test_deployed_build_check.py` liest kein Frontend; tatsächlich 12 Leser (Audit-Hook über unit/contracts/api außerhalb guards) | `scratchpad/s1741/spy.json` |
| (4) Bundle budget ohne Gate | **bestätigt** | `frontend.yml` Job ohne `needs`/`if` |

## Arbeitspakete

| ID | Problem | AK | Dateien |
|---|---|---|---|
| P1 | Coverage in lint-test falten | eine Testausführung, `--cov` + `--fail-under=60`, Manifest `backend--coverage` entfernt | backend.yml, lane-inputs, 3 Guards (stale Register/Texte) |
| P2 | skaffold build + Disk-Cleanup weg | kein Build, Kommentare wahr, Dev-Target-Entscheidung dokumentiert (fallen gelassen) | skaffold-verify.yml, lane-inputs.yml, `.github/actions/setup-skaffold` |
| P3 | Frontend-Pfade aus backend.yml | 12 Leser im required guards-Aufruf, Filter ohne `src/frontend/**`/`tests/e2e/*.py` | backend.yml, backend-guards.yml, Manifeste |
| P4 | Bundle budget gaten | `needs: changes` + `if:` | frontend.yml, Manifest-Gate |

Abhängigkeiten: P1 und P3 teilen backend.yml/Manifeste → eine Aufzeichnung nach allen Edits.
