# E2E-Ergebnis-Review — Branch `feat/audit-bulk-phase-2` (Commit `56e0c718`)

**Lauf:** 2026-04-30 05:43:37 UTC · `task test:e2e` (Full Suite) · ~1 h 02 min · Headless Chrome via Selenium Hub
**Reports:** `test-reports/e2e/20260430_054337/` (Test-Artefakte) · `test-reports/e2e/20260430_054156/logs/` (Container-Logs)
**Reviewer:** `e2e-result-reviewer` (Agent), validiert gegen `spec/req/`, `spec/nfr/`, `spec/ui-nfr/`, `spec/e2e-testcases/`
**Vorbestehende Analyse:** [`test-reports/e2e/20260430_054337/analysis.md`](../../test-reports/e2e/20260430_054337/analysis.md) — punktuell präzisiert / widersprochen.

---

## Testlauf-Übersicht

| Feld | Wert |
|------|------|
| Branch | `feat/audit-bulk-phase-2` |
| Commit | `56e0c718` |
| App-Modus | **Light-Modus** (sichtbar im Banner aller Screenshots) |
| Gesamt | 679 |
| Bestanden | 418 |
| Fehlgeschlagen | **40** |
| Übersprungen | 221 |
| Screenshots | 523 (davon 25 `FAILURE_*`) |
| Protokoll-Tooling | **defekt** — Zähler `0/0/0`, Detail-Section leer; Wahrheit aus `checkpoint.jsonl` (469 Events) + pytest-stdout |

**Gesamtergebnis:** PR-Stand **nicht merge-fähig**. Mit Page-Object-Quick-Fixes für Cluster A und ≤ 5 weiteren trivialen Fixes lässt sich das Bild auf 2–3 echte Spec-Verstöße reduzieren. Davon ist **Cluster C (Privacy-Policy)** der einzige merge-blockierende Source-Code-Defekt.

---

## Cluster-für-Cluster-Validierung gegen die Specs

### Cluster A — Generischer `create-dialog`-Selector existiert nicht (28 Failures)

**`analysis.md`-Klassifikation:** P2 Test-Drift — **bestätigt**.

**Beweis:** Failure-Screenshots zeigen die Stammdaten-Create-Dialoge **vollständig sichtbar** (Titel, alle Pflichtfelder, Aktionsbuttons). Kein Spec-Verstoß. Dialoge werden vom Frontend korrekt gerendert, nur das Test-Page-Object sucht den nicht-existierenden generischen testid `create-dialog`.

| Frontend-testid (Quelle) | Test-Erwartung |
|---|---|
| `botanical-family-create-dialog` (`BotanicalFamilyCreateDialog.tsx:149`) | `create-dialog` |
| `species-create-dialog` (`SpeciesCreateDialog.tsx:141`) | `create-dialog` |
| `cultivar-create-dialog` (`CultivarCreateDialog.tsx:87`) | `create-dialog` |
| `growth-phase-dialog` (`GrowthPhaseDialog.tsx:118`) | `create-dialog` |

**Spec-Bezug:** REQ-001 § Stammdaten-CRUD und UI-NFR-010 (Pflegemasken) **erfüllt** — Dialoge zeigen Pflichtfeld-Markierungen, Helper-Texte, Aktionsbuttons in der Reihenfolge `Abbrechen | Erstellen`.

**Status der Quick-Fixes:** Im PR sind 4 Page-Object-Dateien bereits angepasst (`species_list_page.py`, `botanical_family_list_page.py`, `species_detail_page.py`, `expertise_level_page.py`). Re-Run-Erwartung: 28 Failures grün.

**Klassifikation:** **P2 Test-Drift, nicht merge-blockierend.**

---

### Cluster B — Backend-500-Cluster

#### B.1 — `POST /api/v1/t/{tenant}/tasks` → 500 für `category="watering"|"monitoring"`

**`analysis.md`-Klassifikation:** P0 Backend-Defekt. **WIDERSPRUCH — präzisiert auf P2 Test-Drift.**

**Beweis:**
- REQ-006 §2.7 verbindlich: `Training, Pruning, Ausgeizen, Transplanting, Feeding, IPM, Harvest, Observation, Maintenance, Care_reminder, Seasonal, Phenological`. **`watering` und `monitoring` sind nicht spezifiziert.**
- Backend-Pydantic-Enum (Backend-Log): `Input should be 'training', 'pruning', 'ausgeizen', 'transplant', 'feeding', 'ipm', 'harvest', 'observation', 'maintenance', 'care_reminder', 'seasonal' or 'phenological'` — **spec-konform**.
- `tests/e2e/conftest.py:350` (`category="watering"`) und `:358` (`category="monitoring"`) sind **zwei Test-Setup-Bugs**.

**Korrekte Mapping-Empfehlung:**
- `"E2E: Zimmerpflanzen gießen"` → `category="care_reminder"` (REQ-022 ordnet Gießen `care_reminder` zu).
- `"E2E: pH-Werte prüfen"` → `category="observation"` (REQ-006 §2.7 listet pH/EC-Ablesung explizit unter Observation).

**Klassifikation:** **P2 Test-Drift, nicht merge-blockierend. Backend ist spec-konform und nicht zu ändern.**

#### B.2 — `POST /api/v1/t/{tenant}/tasks/generate-care-reminders` → 500 (Celery `request_stack.push` AttributeError)

**`analysis.md`-Klassifikation:** P0 Backend-Defekt — **bestätigt**.

**Beweis (Code):** `src/backend/app/api/v1/tasks/tenant_router.py:371` ruft `generate_due_care_reminders()` direkt auf — eine `@celery.task`-dekorierte Funktion. Ohne aktiven Worker-Bind crasht `request_stack.push`.

**Spec-Bezug:** REQ-022 §Generierung von Pflegeerinnerungen erlaubt synchrones Triggern. Implementation verletzt **NFR-006** (API-Fehlerbehandlung — kein 500 für vorhersehbare Pfade).

**Visueller Befund:** `FAILURE_test_dashboard_empty_state_shows_success_message.png` zeigt **TaskQueuePage mit 4 sichtbaren Tasks** "Diese Woche" — entgegen der `analysis.md`-Annahme. Die wenigen erfolgreichen `category="maintenance"`-Inserts aus dem Seed (B.1 hatte einen verbleibenden gültigen Pfad) füllen das Dashboard. Kein Empty-State trotz Test-Erwartung.

**Korrekte Spec-Klärung:** Nicht nur der "1-Zeilen-Fix `result.apply().get()`" — auch ein expliziter Fehler-Handler ist nötig (NFR-006 Patterns: 503/202 statt 500 für asynchron triggernde Endpoints).

**Klassifikation:** **P0 Backend-Defekt, MERGE-BLOCKIEREND für REQ-022 §Care-Reminder-Manual-Trigger.**

#### B.3 — `POST /api/v1/t/{tenant}/nutrient-plans` → 500 bei `reference_substrate_type=None`

**`analysis.md`-Klassifikation:** P0 Backend-Defekt. **Teilweise bestätigt — Spec-Klärung erforderlich.**

REQ-004 v3.1 (per Memory-Snapshot) führt "Substrat-unabhängige Pläne" als optionales Feature ein. Wenn das tatsächlich Spec-Stand ist, muss `reference_substrate_type` `Optional` sein. Wenn nicht, ist das Test-Setup falsch.

**Klassifikation:** **P0 oder P2 (Spec-abhängig), nicht akut merge-blockierend** (kein E2E-Test schlägt direkt durch).

#### B.4 — `POST /api/v1/ipm/diseases` → 500 bei `affected_plant_parts=['Bluete']`

**`analysis.md`-Klassifikation:** "Test-Fixture sendet Deutsch statt Enum-Wert". **Bestätigt.**

**Klassifikation:** **P3 Test-Bug, nicht merge-blockierend.**

---

### Cluster C — Privacy-Policy-Endpoint im Light-Modus deaktiviert (1 Failure)

**`analysis.md`-Klassifikation:** P0 Backend-Drift, "Router-Mount fehlt". **PRÄZISIERT: Modus-Gating-Bug.**

**Eigenständig recherchierter Befund:**
- `src/backend/app/api/v1/router.py:60–69` registriert den Privacy-Router **nur bei `kamerplanter_mode == "full"`**:
  ```python
  if settings.kamerplanter_mode == "full":
      from app.api.v1.privacy.router import router as privacy_router
      ...
      api_router.include_router(privacy_router)
  ```
- Der E2E-Lauf verwendet **Light-Modus** (sichtbar in jedem Failure-Screenshot).
- REQ-025 §3.6 fordert `GET /privacy/policy` als **anonym/public** erreichbar (DSGVO Art. 13/14 Hinweispflicht).

**Spec-Verstoß:** Nicht "Endpoint fehlt komplett", sondern "Endpoint hinter falschem Modus-Gate". DSGVO-Hinweispflicht gilt auch im Light-Modus, weil dort Daten verarbeitet werden. Mindestens der `/privacy/policy`-Sub-Pfad muss aus dem `if mode == "full"`-Block heraus.

**Klassifikation:** **P0 Backend-Spec-Drift, MERGE-BLOCKIEREND.** Fix-Owner Backend, ~5-Zeilen-Patch.

**Spec-Lücke detektiert:** REQ-025 sagt nicht explizit, ob im Light-Modus alle DSGVO-Endpoints erreichbar sein müssen. Empfehlung: Spec-Ergänzung mit explizitem Modus-Verhalten (siehe L-2/L-3 unten).

---

### Cluster D — Pflege-Dashboard-Routing-Drift / fehlender PrintButton (3 Failures)

**`analysis.md`-Klassifikation:** P1 Frontend-Spec-Drift "REQ-032 §2.2". **WIDERSPRUCH — Spec-Lücke statt klarer Verstoß.**

**Eigenständige Recherche:**
- `src/frontend/src/routes/AppRoutes.tsx:276` — `<Route path="pflege" element={<Navigate to="/aufgaben/queue" replace />} />` ist beabsichtigt (Code-Kommentar `{/* REQ-022 Pflege — merged into aufgaben/queue */}`).
- REQ-032 §6.1: "Platzierung: In der Toolbar / Aktionsleiste der jeweiligen Detail- oder Listenansicht". **Es ist nicht spezifiziert, an welcher konkreten URL die `care_checklist`-Druckansicht hostet.**
- §5 listet `GET /api/v1/t/{slug}/print/care-checklist` als Backend-Endpunkt — vermutlich vorhanden, aber UI-Aufrufstelle offen.

**Eigentliches Problem:** Die TaskQueuePage hat **keinen** `<PrintButton/>` für `template_type='care_checklist'` eingebunden. `PrintButton.tsx` mit `data-testid='print-button'` existiert, ist aber nicht auf `/aufgaben/queue` gemountet.

**Klassifikation:** **P1 Spec-Lücke + Frontend-Drift**. Empfehlung: REQ-032 §2.2/§6.1 ergänzen mit `Aufrufstelle: /aufgaben/queue`. Spec-Klärung in PR-Issue erforderlich.

---

### Cluster E — TaskSection `task-section-week` vs. `task-section-thisWeek` (1 Failure)

**`analysis.md`-Klassifikation:** P2 Test-Drift — **bestätigt, präzisiert**.

**Beweis:**
- Frontend `TaskQueuePage.tsx:853`: `data-testid={'task-section-${group}'}` mit `group ∈ {'overdue','today','thisWeek','future'}`.
- Test-Page-Object `tests/e2e/pages/task_queue_page.py:48`: `TASK_SECTION_WEEK = (... 'task-section-week')` — sucht das non-existente `week`.
- Page-Object `pages/pflege_dashboard_page.py:31, :134` ist **schon korrekt** auf `task-section-thisWeek`. Nur `task_queue_page.py` ist drift.

**Test scheitert nur, weil B.1 die "watering"/"monitoring"-Tasks rauskickt und nur Maintenance-Tasks (im "Diese Woche"-Bucket) übrigbleiben.**

**Klassifikation:** **P2 Test-Drift, trivial, nicht merge-blockierend.**

---

### Cluster F — Route-Reachability-Skip-Heuristik defekt (8 Failures)

**`analysis.md`-Klassifikation:** P3 Test-Bug — **bestätigt + Frontend-UX-Hint ergänzt**.

**Eigenständige Recherche:**
- `AppRoutes.tsx:711` — Catch-All `path="*"` → `<Suspense fallback={<LoadingSkeleton variant="card" />}><NotFoundPage /></Suspense>`.
- `src/frontend/src/pages/NotFoundPage.tsx` rendert `ErrorPage` mit `data-testid="error-page"`, `<Typography variant="h1">{statusCode}</Typography>` (= "404"-Text) und i18n-Titel.
- **ErrorPage setzt jedoch kein `<title>` in `<head>`** (kein React-Helmet, kein `document.title`-Update).
- Test-Skip prüft `"404" in browser.title` — schlägt fehl, weil `<title>` der statische `<title>Kamerplanter</title>` aus `index.html` bleibt.

**Visueller Beweis:** Alle 8 Failure-Screenshots der Reachability-Tests zeigen nur Skeleton-Rectangles — d.h. der Suspense-Fallback wurde im Screenshot festgehalten, der Lazy-Chunk für NotFoundPage war noch nicht fertig.

**Doppel-Diagnose:**
1. Test-Bug: Skip-Heuristik nutzt instabile `browser.title`-Prüfung.
2. Frontend-UX-Hint: `wait_for_element((By.CSS_SELECTOR, "[data-testid='error-page']"))` würde die Skip-Logik robust machen.

**Klassifikation:** **P3 Test-Bug + P3 Frontend-UX-Hint, nicht merge-blockierend.**

---

### Cluster G — MUI-Number-Input vs. Selenium `clear()` (1 Failure)

**`analysis.md`-Klassifikation:** P3 Test-Bug — **bestätigt + App-Bug-Aspekt ergänzt**.

**Visueller Beweis:** `FAILURE_test_rotation_dialog_supports_four_year_wait.png` zeigt das Wartezeit-Feld mit Wert **"34"**, Helper-Text "Mindestwartezeit in Jahren … (1–10)".

**Eigenständige Recherche:**
- Frontend `CropRotationPage.tsx:170–179`: TextField mit `slotProps={{ htmlInput: { min: 1, max: 10 } }}`, aber `onChange={(e) => setWaitYears(Number(e.target.value))}` ohne Capping. **HTML5-`max=10` greift nur beim Form-Submit, nicht beim Tippen** — React-State akzeptiert `34`.
- Test-Code: `el.clear(); el.send_keys("4")`. React-State steht auf Default `3`, `clear()` cleart den DOM-Value, aber MUI-Component-State wurde nicht invalidiert. Erstes send_keys-`4` wird angefügt → Display "34".

**Doppel-Diagnose:**
1. Test-Bug: `clear()` ist für MUI/React-Number-Inputs unzuverlässig. Helper `clear_and_type(el, value)` mit `Ctrl+A → Delete → send_keys`.
2. App-UX-Hint: `setWaitYears(Math.max(1, Math.min(10, Number(e.target.value))))` Client-Capping.

**Klassifikation:** **P3 Test-Bug + P4 UX-Polish, nicht merge-blockierend.**

---

### Cluster H — Seed-YAML-Schema-Drift (Backend-Boot, kein direkter Test-Failure)

**`analysis.md`-Klassifikation:** Spec→Code-Drift — **bestätigt**.

5 Seed-YAML-Dateien werfen `yaml_seed_error`:
- `plant_info_indoor_1.yaml` — `Species` hat kein Feld `is_toxic`
- `plant_info_indoor_4.yaml` — `Species` hat kein Feld `hardiness_detail`
- `plant_info_outdoor_1.yaml` — `Cultivar.days_to_maturity=0`, min=1
- `plant_info_outdoor_3.yaml` — `RequirementProfile.irrigation_frequency_days=0`, min>0
- `plant_info_supplement_1.yaml` — `Species.recommended_container_volume_l` Int statt String

REQ-001 v5.0 (Outdoor-Garden-Review G-001) ergänzt Species mit `is_toxic` und `hardiness_detail`. Backend-Modell hinkt der Spec hinterher.

**Klassifikation:** **P1 Spec→Code-Drift Backend, nicht akut merge-blockierend für E2E, aber Datenqualitätsproblem.**

---

## Spec-Lücken & Mehrdeutigkeiten

| # | REQ/NFR | Lücke / Mehrdeutigkeit | Empfohlene Klärung |
|---|---|---|---|
| L-1 | REQ-006 §2.7 | Keine `watering`-Kategorie; Mehrdeutigkeit für reine Gieß-Aufgaben ohne Düngung | Klarstellung: "Gießen ohne Dünger → `care_reminder`; mit Nährlösung → `feeding`" — oder neue Kategorie `watering` aufnehmen |
| L-2 | REQ-025 §3.6 | "Public access" nicht eindeutig auf Light-Modus übertragen | Ergänzung: "Privacy-Policy-Endpoint ist auch im Light-Modus erreichbar (DSGVO Hinweispflicht)" |
| L-3 | REQ-027 (Light-Modus) | Welche DSGVO-Endpoints sind im Light-Modus aktiv? | Klare Auflistung in REQ-027 §Mode-Matrix |
| L-4 | REQ-032 §2.2/§6.1 | Aufrufstelle für `care_checklist`-PrintButton nicht explizit | §6.1 ergänzen mit `Aufrufstellen` pro Template-Typ |
| L-5 | REQ-004 v3.1 | `reference_substrate_type` Pflicht oder Optional? | Spec/Code-Sync: Field optional + dokumentierter Default |
| L-6 | REQ-001 v5.0 | Felder `is_toxic`, `hardiness_detail` nicht im Backend-Modell | Backend-PR mit Modell-Migration |

---

## Übersprungene Tests — Bewertung (221 Skips)

- **Auth-pflichtige Tests** im Light-Modus (`requires_auth`-Marker) — **berechtigt**, kein Coverage-Risiko (Light-Modus per Definition ohne Auth).
- **Listen-Operations-Tests, die leere Listen erwischen** — **partiell berechtigt, Coverage-Risiko**: ohne Seed-Daten werden Search/Sort-Pfade nicht getestet. Empfehlung: Seed-Daten erweitern statt skippen.
- **REQ-007 Harvest Readiness-Card-Tests** (TC-REQ-007-030/031/032) — **Coverage-Lücke**, nie ausgeführt.

---

## Cross-Screenshot UI-NFR-Compliance

| Bereich | Befund |
|---|---|
| **MUI-Theme-Konsistenz** | Hervorragend — alle Pages gleiches grünes Theme, gleiche Typografie, gleiche Spacing |
| **Sidebar** | Konsistent über alle Screenshots; aktive Route klar markiert |
| **Light-Modus-Banner** | Durchgehend sichtbar mit Schließen-Button (UI-NFR §Status-Banner) |
| **DataTable (NFR-010)** | Spalten-Header mit Sortier-Pfeilen, Suchfeld, Pagination, Showing-Count alle vorhanden |
| **Empty-States** | Klar, mit Hinweistext und "Filter zurücksetzen"-CTA (UI-NFR-010 §Empty-States) |
| **Validation-Feedback** | Pflichtfeld-Marker `*`, Helper-Texte mit Format-Beispielen |
| **Dialog-Modalität** | Zentriert, mit Backdrop, Aktionsbutton-Reihenfolge `Abbrechen \| Erstellen` (NFR-006-konform) |
| **i18n DE** | Vollständig — keine englischen Fallbacks, keine Raw-Keys |
| **Mobile/Touch** | **Aus diesem Lauf nicht prüfbar** — Lauf ist Desktop (1920×1080) |
| **Kiosk/A11y** | Aus Screenshots nur teilweise prüfbar — `aria-label`s im Code, visuelle A11y-Prüfung erfordert separate Tools |

**Kein UI-NFR-Verstoß sichtbar in Failure- und TC-Screenshots.**

---

## Priorisierte Handlungsliste

| # | Cluster | Owner | Priorität | Aufwand | Impact |
|---|---|---|---|---|---|
| 1 | **C** — Privacy-Policy-Endpoint im Light-Modus | Backend | **P0 — MERGE-BLOCKIEREND** | 5 Zeilen (`router.py:60–69`) | DSGVO-Compliance, REQ-025 §3.6 |
| 2 | **B.2** — Celery-Task-Sync-Crash | Backend | **P0** | 1 Zeile + Errorhandler | REQ-022 Care-Reminder-Manual-Trigger funktional |
| 3 | **A** — `create-dialog`-Selector-Drift | Tests | P2 | 4 Dateien (bereits gepatcht) | 28 Failures werden grün |
| 4 | **B.1** — `category="watering"`/`"monitoring"` im Test-Seed | Tests | P2 | `conftest.py:350,358` | Test-Seed funktioniert, B.1-Folgekaskade verschwindet |
| 5 | **E** — `TASK_SECTION_WEEK` → `thisWeek` | Tests | P2 | 1 Zeile (`task_queue_page.py:48`) | TC-REQ-006-012 grün |
| 6 | **B.4** — `'Bluete'` → `'flower'` in IPM-Test-Fixture | Tests | P3 | 1 Zeile in IPM-Test-Setup | Stiller 500 verschwindet |
| 7 | **G** — MUI-Number-Input clear() Helper | Tests | P3 | 1 Helper in `base_page.py` | TC-REQ-028-Rotation-Dialog grün |
| 8 | **F** — Skip-Heuristik mit `data-testid='error-page'` | Tests | P3 | 1 Helper + 8 Aufrufe | 8 Failures werden korrekt-skipped |
| 9 | **D** — PrintButton auf TaskQueuePage einhängen | Frontend + Spec | P1 | Spec-Klärung + 5 Zeilen Frontend | REQ-032 Pflege-Checkliste-Druck |
| 10 | **B.3** — `reference_substrate_type` Optional + Spec-Klärung | Backend + Spec | P1 (Spec-abhängig) | 2 Zeilen + Spec-Update | NutrientPlan-Setup grün |
| 11 | **H** — `is_toxic`, `hardiness_detail` Backend-Model | Backend | P1 | Migration + Model-Update | Seed-Datenqualität |
| 12 | **G (Frontend-Polish)** — Number-Input Client-Capping | Frontend | P4 | 1 Zeile `Math.max/min` | UX-Politur |
| 13 | **Protokoll-Tooling** — `protokoll.md`-Generator reparieren | Tooling | P2 | `tools/`-Skript-Bug | Reports werden für PR-Review nutzbar |

---

## Gesamtbewertung des Branches `feat/audit-bulk-phase-2`

**Empfehlung: NICHT MERGEN** im aktuellen Stand.

**Was tatsächlich Code im Branch broken ist (P0/P1):**
1. **Cluster C** — Privacy-Policy-Mode-Gate verletzt REQ-025/DSGVO. **Einziger merge-blockierender Defekt im Source-Code.**
2. **Cluster B.2** — Celery-Sync-Aufruf crasht REQ-022-Manual-Trigger. **Funktional blockiert, kein Daten-Risiko.**
3. **Cluster H** — Spec→Code-Drift bei REQ-001 v5.0 Species-Feldern. **Datenqualität, nicht akut.**
4. **Cluster B.3** — Spec-Klärung REQ-004 v3.1 erforderlich.

**Was nur Test-Drift ist (P2/P3 — 39 von 40 Failures):**
- Cluster A (28), B.1 (1), B.4 (1), E (1), G (1), F (8) — **alle 39 Failures sind in `tests/`-Verzeichnis fixbar, ohne Source-Code-Änderungen** (~95 % der Failures).

**Re-Run-Erwartung nach Tests-Fix (Pkt. 3-8 oben):**
- ~3-4 Failures übrig: Cluster C (P0 Backend), B.2 (P0 Backend), B.3 (P1 Spec-Klärung), D (P1 Spec/Frontend).

**Merge-Pfad-Vorschlag:**
1. **Sofortmaßnahme (vor Merge):** Cluster C fixen (5 Zeilen Backend), Cluster B.2 fixen (1 Zeile Backend + Error-Handler).
2. **Vor PR-Merge gleicher Branch:** Cluster A/B.1/B.4/E/G/F-Tests-Fixes pushen, Re-Run gegen den Branch durchführen, Resultat dokumentieren.
3. **Nach Merge in `develop`:** Cluster D als Spec-Issue + Folge-PR. Cluster B.3 + H als separate Backlog-Items.

**Operative Nachbesserungen (parallel zum Merge-Pfad):**
- `protokoll.md`-Generator-Bug ist ein lautloses Reporting-Problem (469 Events da, aber 0/0/0 angezeigt). Ohne Fix bleiben PR-Reviews auf Screenshots beschränkt.
- Konkurrierende Report-Verzeichnisse `054156`/`054337`/`054338` sollten in `run-e2e.sh` zusammengeführt werden.

---

## Pfade der relevanten Artefakte

| Zweck | Pfad |
|---|---|
| Test-Artefakte (Screenshots/checkpoint) | `test-reports/e2e/20260430_054337/` |
| Container-Logs | `test-reports/e2e/20260430_054156/logs/backend.log` |
| Vorhandene Cluster-Analyse | `test-reports/e2e/20260430_054337/analysis.md` |
| Privacy-Mode-Bug | `src/backend/app/api/v1/router.py:60–69` |
| Celery-Sync-Bug | `src/backend/app/api/v1/tasks/tenant_router.py:371` |
| TaskSection-Drift | `tests/e2e/pages/task_queue_page.py:48` |
| Test-Setup-Watering-Bug | `tests/e2e/conftest.py:350, :358` |
| Pflege-Routing | `src/frontend/src/routes/AppRoutes.tsx:276` |
| TaskQueue-PrintButton fehlt | `src/frontend/src/pages/aufgaben/TaskQueuePage.tsx:885 ff.` |
| Crop-Rotation-Number-Input | `src/frontend/src/pages/stammdaten/CropRotationPage.tsx:170–179` |
| NotFoundPage (kein document.title-Update) | `src/frontend/src/pages/ErrorPage.tsx` |
