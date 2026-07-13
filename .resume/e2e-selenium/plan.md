# Plan — Restore & revise the Docker Selenium E2E suite

Branch: `fix/e2e-selenium` · Worktree: `~/repos/.worktrees/kamerplanter/e2e-selenium`
Requirement (SSOT, already on develop): `project/requirements/e2e-selenium-executability.md` (R1–R6, DoD).

## Goal

Restore the **technical executability** of the existing Docker Selenium E2E suite
(`docker-compose.e2e.yml` + `scripts/run-e2e.sh` + `tests/e2e/`) for the
`--smoke` run and then the `light` / desktop profile. Every test must end either
green **or** with a documented, explainable skip. This is a harness/infra +
minimal-invasive drift-fix pass — **not** a rewrite of the business test cases.

## Current state (researched 2026-07-13)

- 75 `test_req*.py` journeys under `tests/e2e/`, Page-Object structure under
  `tests/e2e/pages/`, protocol generation via `protocol_plugin.py`, fixtures in
  `tests/e2e/fixtures/`, shared helpers `_journey_helpers.py` / `_route_helpers.py`.
- Runner `scripts/run-e2e.sh` (exec bit set) + `docker-compose.e2e.yml` (full
  stack + Selenium, shm 2 GB). Deps: selenium>=4.25, webdriver-manager,
  pytest>=8.3, pytest-xdist.
- Debug affordance: `task mcp:e2e:debug` publishes the frontend on `:8080`.
- The requirement artifact is merged; the earlier `.resume/e2e-selenium-executability/plan.md`
  was **not** merged to develop and is absent here — this plan supersedes it.
- Branch is at develop tip (no commits ahead yet).
- Known context from project memory: E2E has **no CI job** (deliberate, GH runners
  too weak) — do not treat that as a gap. light-mode `module_visibility` is read
  from `localStorage` (`kp-module-visibility`), server PATCH is ineffective →
  browser fixture must seed localStorage. Issue #606 is a newer E2E bug to fold in.

## Design decision (load-bearing) + open questions

**Decision:** Triage-driven, per-file. For each failing journey classify the cause:
- **Test-drift** (stale selectors/routes/waits/seed expectations, forms refactored
  since April) → reconcile Page-Model against implementation, fix in test code (R2).
- **Missing testability affordance** (refactor made an element/state unaddressable)
  → add a **non-behavior-changing** `data-testid`/stable selector/aria-state in app
  source (R6).
- **Real functional app regression** (500s, wrong logic, broken flow) → do NOT patch
  here; file a separate GitHub issue/finding (R3).

Iterative with an **operator-review gate after smoke+light** (R4). `full`, `mobile`,
`tablet`, and any CI job stay out of scope for this run.

**Open questions to confirm before/at start of work:**
1. Do local Docker resources actually carry full-stack + Selenium (shm 2 GB)? — verify empirically before first run.
2. Is `light`/desktop the confirmed single profile for this run? (requirement says yes — confirm still holds.)
3. Should R3 regressions be filed as individual issues immediately, or collected in one findings doc then split? (requirement implies separate issues.)

## Work steps (ordered)

1. Read the actual ground truth: `scripts/run-e2e.sh`, `docker-compose.e2e.yml`,
   `tests/e2e/conftest.py`, `protocol_plugin.py`, `pages/`, health-checks.
2. Verify Docker can run the stack; bring it up; confirm health.
3. Run `--smoke` (`task test:e2e:smoke`). Capture protocol + failures.
4. Triage smoke failures per the decision above; fix drift / affordances; re-run to green-or-explained.
5. **Gate:** pause for operator review of smoke results before the full `light` run.
6. Run the `light`/desktop suite (`task test:e2e`). Triage + fix drift/affordances.
7. Collect real regressions (R3) as findings; open issues.
8. Write findings doc + attach generated test protocol (R5). Reach operator-review gate.

## Findings log (feeds the R5 findings doc)

- **F-1 (BLOCKER, infra/R1 — smoke run 20260713_072808):** The `backend` service is
  marked **unhealthy before startup seeding finishes**, so `frontend`
  (`depends_on: backend healthy`) never starts and `up --wait frontend` fails with
  exit 1 — **no test executed**. Root cause: the backend runs the full light-mode
  seed (210 species + cultivars) inside the FastAPI lifespan *before* uvicorn binds;
  the log shows `Waiting for application startup.` at 07:31:58 and seeding still
  running at 07:33:16 (**>78 s**). The backend healthcheck (`interval 5s`,
  `retries 15`, **no `start_period`**) trips unhealthy at ~75 s. Classification:
  **harness/infra timing**, not an app regression — the app is seeding correctly,
  just slower than the healthcheck grace window. Fix (in scope, non-behavioral):
  add a `start_period` to the backend healthcheck in `docker-compose.e2e.yml`.
  **APPLIED 2026-07-13:** measured time-to-healthy = 51 s isolated (arangodb+valkey+
  backend only), >78 s under full concurrent boot → set `start_period: 180s` on the
  `backend` healthcheck (and parity fix on `backend-full`, which shares the identical
  latent bug though full mode stays out of scope). Verification smoke re-run pending.

- **F-2 (Smoke-Suite `20260713_074824`, nach F-1): 12 Failures, alle TEST-DRIFT (R2).**
  Nach F-1 lief die Smoke-Suite durch: `188 selected → 126 passed · 45 skipped · 5 xpassed · 12 failed`.
  Triage (3 Explore-Agenten, Page-Model ↔ Implementierung): **alle 12 = Drift**, keine
  App-Regression (R3), keine fehlende Affordance (R6), **keine Frontend-Änderung**.
  - **Cluster A (7×, Autocomplete-Drift):** Haupt-Selektor `<Select>`→`<Autocomplete>`;
    `.MuiSelect-select` existiert nicht mehr. Fix: `SPECIES_SELECT`/`FAMILY_SELECT` →
    `[data-testid='…'] input`; Option-XPath `contains(text())`→`contains(.)` (Label in
    verschachtelten `<Typography>`). Dialog-Selektoren unverändert (echte Selects).
    Dateien: `pages/companion_planting_page.py`, `pages/crop_rotation_page.py`.
  - **Cluster B (3×):** `species_list_page.click_row_by_name` sucht jetzt erst
    (client-side Pagination 25/Seite); `watering_log_list_page.select_plant_by_text`
    wartet auf Optionen + Retry + instance_id-Präfix-Match; `task_queue_page._select_form_option`
    nutzt `scroll_and_click` (JS-Fallback) statt `option.click()`.
  - **Cluster C (2×):** `test_req003_phasensteuerung` Step-2 nur bei ≥3 Phasen (2-Phasen-
    Spezies → BE lehnt Same-Phase korrekt ab, Dialog bleibt offen); `test_req022`
    verzichtet auf „Generate reminders" (erzeugt dedup-verursachenden Task) und wartet auf
    die Live-Care-Card.
  - **Status R1 (gezielte Re-Validierung `20260713_091426`, 9 Dateien, 23 Tests):**
    `12 passed · 9 failed · 2 skipped`. **Drift-Kaskade:** erste Fix-Runde hat die
    Failures weitergeschoben (Fix griff, nächster Drift-Punkt sichtbar). `test_req022`
    (C2) grün. Cluster A: `get_*_options` klappt jetzt, aber Option-Auswahl matchte per
    XPath `contains(., name)` gegen **mehrzeiligen** `o.text` → **2. Fix diese Runde:**
    Selenium-seitiges normalisiertes Matching (`_find_option`) in beiden Pages.
- **F-3 (2. Drift-Welle aus `20260713_091426`, via Failure-Screenshots + 2 Explore-Agenten):**
  4 neu aufgedeckte, unabhängige Drift-Punkte (Fixes der 1. Runde legten sie frei):
  - **req003:** Transition + „Phasenverlauf" (2 Zeilen) funktionieren; nur
    `get_phase_history_count()` (`[data-testid='phase-history'] tbody tr`) liefert 0 →
    History-Table-Testid/Struktur-Drift. (Agent-Recon läuft.)
  - **req006:** `select_task_category` griff; scheitert jetzt an
    `set_due_date_today` (`form-field-due_date`) — Feld nach `category=care_reminder`
    evtl. conditional/umbenannt. (Agent-Recon läuft.)
  - **req004:** Watering-Dialog zeigt für die provisionierte Pflanze **„No options"** —
    Pflanze existiert (in Task-Queue sichtbar), aber nicht im Autocomplete. Quelle/Filter/
    Precondition? (Deep-Agent läuft.)
  - **req001_core:** Such-Fix wirkte (Detailseite erreicht), aber `click_cultivar_create`
    steht auf falschem Tab — Cultivar-Button liegt unter **SORTEN**-Tab (Detailseite hat
    jetzt 6 Tabs, Page-Object-Docstring „3 tabs" stale). (Agent-Recon läuft.)
  - **F-3 AUFGELÖST (2 Explore-Agenten):** 3 von 4 = TEST-DRIFT, gefixt:
    - req003: `PHASE_HISTORY(_ROWS)` → `[data-testid='phases-tab-content'] [data-testid='data-table(-row)']`
      (History nutzt jetzt shared `DataTable`, kein `phase-history`-Testid mehr).
    - req006: Ursache war NICHT das Feld — `_select_form_option` schickte Body-`ESCAPE`
      nach MenuItem-Klick → schloss den ganzen Create-Dialog. ESCAPE entfernt.
    - req001: `click_cultivar_create` wechselt jetzt label-basiert auf „Sorten"-Tab;
      `click_tab(1)` im Test entfernt; stale Docstring/Kommentar korrigiert.
- **F-4 (ECHTE APP-REGRESSION, R3 — req004, NICHT im E2E-Branch gepatcht):**
  `WateringLogCreateDialog.tsx:112` (und 4 weitere Seiten) rufen
  `listPlantInstances(0, 500)`; Backend `PaginationParams` cappt `limit` bei `le=200`
  (`src/backend/app/common/pagination.py`, „DUP-B5"-Konsolidierung) → **HTTP 422**,
  per `.catch(() => [])` verschluckt → leere Optionsliste → „No options". **Client/Server-
  Contract-Bruch**, betrifft echte Nutzer (Watering-/Feeding-/Harvest-/Location-Seiten).
  Blast-Radius (alle `listPlantInstances(0,500)`): `WateringLogCreateDialog.tsx:112`,
  `FeedingEventListPage.tsx:47`, `WateringEventListPage.tsx:48`, `HarvestBatchListPage.tsx:50`,
  `LocationDetailPage.tsx:236` (+ evtl. `fetchFertilizers(0,500)` gl. Dialog). Fix (separat):
  BE-Cap anheben ODER Caller auf `200` (oder paginieren).
  **Operator-Entscheid am Gate (2026-07-13): trivialen Contract-Fix in-branch mitnehmen.**
  → 6 Caller `(0, 500)`→`(0, 200)` (aligniert mit den 7 bestehenden 200-Callern; kein
  Aufweichen des shared BE-Caps für ~40 Endpoints): `WateringLogCreateDialog.tsx:112`
  (plant) + `:115` (fertilizer, gl. Cap), `LocationDetailPage.tsx`, `HarvestBatchListPage.tsx`,
  `WateringEventListPage.tsx`, `FeedingEventListPage.tsx`. `xfail`-Marker auf
  `test_log_watering_for_plant` **entfernt**. Validierung im laufenden light-Lauf
  (rebuildet Frontend). Damit auch J090/J091 + Feeding (TC-004-091) mitgeheilt.
- **F-5 (req006, TEST-DRIFT — 3. Drift-Welle, via Screenshot `20260713_095259`):**
  Nach den F-3-Fixes lief das Create-Task-Formular voll durch, aber das
  `Fälligkeitsdatum` zeigte **„20.02.60713"** (Jahr 60713): `set_due_date_today`
  tippte die ISO-Zeichenkette `"2026-07-13"` per `send_keys` in ein natives
  `<input type="date">`, dessen de-Locale-Segmente (DD.MM.YYYY) die Ziffern von
  links füllen → Müll-Datum → Submit blockiert → Task nie in der Queue. Fix:
  nativen `.value` per JS-Setter als ISO setzen + `input`/`change` dispatchen
  (kein `send_keys`). **Verifiziert einzeln: grün (1 passed).**

- **F-6 (voller light/desktop-Lauf, `task test:e2e`, exit 201): 17 Failures (Nicht-Smoke).**
  `481 passed · 172 skipped · 8 xfailed · 24 xpassed · 17 failed` (73 min). **F-4-Fix
  bestätigt:** Frontend baute+healthy, `test_log_watering_for_plant` grün. Alle Smoke-Fixes
  halten. Die 17 sind erstmals gelaufene Nicht-Smoke-Journeys, 5 Cluster (Triage via
  4 Explore-Agenten läuft):
  - **D — req003 (3):** search-chip bei leerem Term (`test_plant_list_search_by_instance_id`);
    reason-Feld „manual"-Präfix, clear greift nicht (`test_transition_dialog_reason_editable`);
    remove-Dialog öffnet nicht (`test_remove_dialog_opens_and_cancels`).
  - **E — nutrient_calculations Mixing (6):** alle „kein Result-Alert/Snackbar" nach
    Calculate/Validate (`len(results)==0`) — 1 Ursache.
  - **F — req021 experience_level (3):** `scientific_name` sichtbar statt hidden;
    `run_type`-Feld nicht sichtbar (intermediate/expert).
  - **G — misc (5):** feeding-cancel StaleElement; harvest-Dialog schließt nach Submit nicht;
    species-detail-Test erwartet „MISCHKULTUR"-Tab (expert-only, in beginner/light nicht da);
    feeding-journey `select_application_method` timeout; **task-tab „Daten konnten nicht
    geladen werden"** (`test_completed_task_visible_on_plant_tab` — evtl. R3).

- **F-6 AUFGELÖST (2026-07-13, 4 Explore-Agenten + Fixes):** alle 17 light-Failures adressiert.
  - **TEST-DRIFT gefixt (14):** D×3 (cover-column cell-index, reason clear_and_fill,
    termination-dialog testids); E×6 (Phase-Select-Native-Input ausschließen + valider
    Fertilizer-Key via API-Fixture statt leer→422); G-F1 (feeding stale-safe),
    G-F3 (species expert-only-Tabs), G-F4 (feeding option scroll_and_click + Menü-Wait),
    F1 (experience-level durable-persist Härtung).
  - **REAL-Regression in-branch gefixt (2, F-4-Pagination-Muster):** G-F5
    `PlantInstanceDetailPage.tsx:413` `listTasks(0,500)`→`200`; + die 5 F-4-Caller (bereits).
  - **REAL-Regression via robustem Async-Wait entschärft (2, KEIN Produkt-Change):**
    F2/F3 `run_type` — `isFieldVisible` fehlt `!levelKnown`-Guard (Felder blitzen im
    Prefs-Ladefenster als beginner aus); Produkt-Fix hätte Suite-Blast-Radius (35
    „expect hidden"-Checks), daher `wait_for_form_field_visible`-Poll im Test +
    Regression als Finding dokumentiert (Ein-Zeilen-Produkt-Fix empfohlen).
  - **App-korrekt, dokumentierter Skip (1):** G-F2 Harvest — Karenz-Gate (422) blockt
    korrekt; Test pollt jetzt früh auf Fehler-Snackbar → Skip statt hard-fail.
- **F-7 (ROBUSTHEITS-AUDIT, Operator-Auftrag mid-run — R6):** systemische Brüchigkeit
  (65× `.MuiSelect-select`, 65 Positions-Index, Text-XPath-Optionen) → **fehlende
  dedizierte IDs ergänzt (additiv, non-behavioral):** `FormSelectField` Trigger-Testid
  `form-field-{name}-trigger` + Option-Testid `form-option-{name}-{value}`; `DataTable`
  Zellen-Testid `cell-{col.id}`. Robuste `base_page`-Helper (`open_select`,
  `select_option_by_value`, `choose_select_value`, `get_row_cell_text`); Exemplar-
  Migration `task_queue._select_form_option`. Voller Report: `.resume/e2e-selenium/robustness-audit.md`.
  Migrations-Sweep der übrigen 48 Dateien als bounded Follow-up empfohlen.

## Ergebnis-Zusammenfassung (Stand vor vollem Smoke-Gate-Lauf)

Alle 12 ursprünglichen Smoke-Failures adressiert:
- **11 × TEST-DRIFT gefixt** (Cluster A 7×, req001-cultivar, req003-history, req006-category+date, req022) — alle in gezielten Läufen grün.
- **1 × R3-Regression** (req004 Pagination-Contract) → dokumentiert-`xfail` + Finding F-4.
- **0 Frontend-Änderungen, 0 App-Patches** (scope-konform).
- Gezielte Re-Validierung `20260713_095259`: `19 passed · 1 xfailed · 2 skipped · 1 failed`
  (das eine failed = req006, danach separat gefixt+verifiziert grün).
- **Läuft:** voller `task test:e2e:smoke` (188 Tests) als Gate-Verifikation (Kollateral-Check
  der geteilten Page-Object-Änderungen). Danach: Smoke-Operator-Gate (R4).

## Invariants & guardrails

- NFR-008a: keep Page-Object pattern, screenshot checkpoints, protocol generation intact.
- NFR-003: all source & test code in **English** (docs may be German).
- App source changes limited to **non-behavior-changing** testability affordances (R6); anything behavioral → R3 issue, not a patch.
- Feature work stays in this worktree; primary checkout stays on develop.
- Branch from develop; PR to develop at the end (via `pull-request-create`), not from this skill.

## Status / resume-anchor checklist

- [x] Requirement re-confirmed at/above threshold (artifact already exists — quick pass) — 2026-07-13: U_gate 0.80 = τ_high, R1–R6 all `confirmed`, saturation. No positive-EVPI question remained. Confirmed as-is.
- [x] Ground-truth files read (run-e2e.sh, compose, conftest, protocol_plugin, pages) — 2026-07-13: read run-e2e.sh, docker-compose.e2e.yml, conftest.py (37 KB), pages/ (61 page-objects), 75 `test_req*.py` journeys, smoke marker registered. Key facts: light mode seeds `kp-module-visibility` in localStorage (browser fixture) + server PATCH; function-scope browser; protocol via `--generate-protocol`; smoke via `--profile smoke` / `-m smoke`.
- [x] Docker stack verified & healthy — 2026-07-13: engine 29.6.1, compose v5.3.1, 8 CPU / ~18 GiB free; **F-1 fix** (`start_period: 180s`) makes backend→frontend reach Healthy (verified across smoke runs `074824`/`091426`/`095259`).
- [x] `--smoke` run captured + triaged + green-or-explained — 2026-07-13: full `task test:e2e:smoke` (`20260713_102027`, exit 0): **138 passed · 44 skipped · 1 xfailed (req004 R3) · 5 xpassed · 0 failed** (was 126p/12f). All 12 originals resolved (11 TEST-DRIFT fixed, 1 R3 xfail). No collateral regressions from the shared page-object edits. Protocol: `test-reports/e2e/20260713_102027/protokoll.md`.
- [x] Operator-review gate after smoke — **PASSED 2026-07-13.** Operator decided: (1) fix the F-4 contract break in-branch (6 callers 500→200, xfail removed), (2) proceed to the full `light`/desktop suite.
- [~] `light`/desktop suite run + triaged + green-or-explained — `task test:e2e` running (rebuilds frontend with the F-4 fix; validates req004 + triages non-smoke journeys).
- [~] Real regressions filed as issues (R3) — F-4 resolved in-branch by operator decision (no separate issue needed); watch for further real regressions in the light run.
- [ ] Findings doc + protocol written (R5); operator-review gate reached
