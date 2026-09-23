# Group pre-analysis: 2026-09-23-erasure-anonymisation

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Was muss geschehen, damit beide Kontolöschpfade (Admin-Delete und
Self-Service Art. 17) das deklarierte Lösch-/Anonymisierungsinventar tatsächlich
ausführen — und welche der in #1663 behaupteten Voraussetzungen treffen nach v0056
(PR #1674) noch zu?

**The group's single logical change, in one sentence:** Both account-deletion paths
execute the declared erasure inventory — deletions, anonymisation rules and audit
pseudonymisation — through one shared executor that filters each step by a declared
user field.

**Out of scope:**
- #1666 (Task-Lebenszyklus, Celery-Autoretry, Rate-Limit der Download-Route) — andere
  logische Änderung; wird nach dem Merge einzeln bearbeitet, Befund 1 wird dann neu
  gemessen (verschwindet voraussichtlich, sobald `retention_worker` ausgeführt wird).
- Die drei nur in der Spec existierenden Collections (`duty_rotations`,
  `seasonal_cycles`, `plant_diary_analyses`) — kein Code, also nichts zu anonymisieren
  (siehe Structural finding).
- Art. 15 / Export — durch #1662 geliefert.

**Tier:** 2 — ein Repository, keine veröffentlichte API-Vertragsänderung (Admin-Route und
Privacy-Routen behalten Request/Response-Form).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1663 | security | dependency chain (Voraussetzung für #1664 und #1645) | `ErasureStep` ohne Nutzerfeld: `domain/models/privacy.py:208-221`; Regeln: `domain/engines/erasure_engine.py:46-131` |
| #1664 | security | shared touch surface (`erasure_engine.py`, Inventar-Ausführung) | `UserService.delete_account_permanently` (`domain/services/user_service.py:105-133`) führt nur `account_cascade` + Memberships aus, keine Anonymisierung |
| #1645 (Rest: Art.-17-Executor) | security | dependency chain (in #1645-Kommentar auf #1663 blockiert) | `_finalize_erasure` (`domain/services/privacy_service.py:1074-1145`) löscht/anonymisiert nichts in ArangoDB, markiert `partially_completed` solange `steps_for("retention_worker")` nicht leer |

**Dependency ordering:** #1663 → #1664 → #1645 (linear).

**Shared touch surface:** `src/backend/app/domain/models/privacy.py`,
`src/backend/app/domain/engines/erasure_engine.py`, der neue gemeinsame Executor im
Data-Access-Layer, `scripts/check_privacy_inventory.py`,
`docs/{de,en}/guides/data-retention.md`.

## Measured premises (member-cause verification)

Behauptete Ursachen aus den Issues, gegen `develop` @ 047acb316 gemessen:

| Claim | Issue | Messung | Ergebnis |
|---|---|---|---|
| Fünf Aufbewahrungspflichten ohne Regel | #1663 | `grep -rln "duty_rotation\|aggregate_computed_by\|plant_diary_analys\|seasonal_cycle" src/backend/app` → keine Ausgabe | **teilweise widerlegt**: 3 von 5 existieren nur in der Spec. `QualityAssessment.assessed_by` ist Freitext (`models/harvest.py:90`, kein Key-Feld); `YieldMetric` trägt kein Nutzerfeld (`models/harvest.py:104-115`) → nichts zu anonymisieren |
| `ErasureStep` hat kein Nutzerfeld | #1663 | `sed -n 208,221p domain/models/privacy.py` → Felder `collection, kind, executor, note` | **bestätigt** |
| Regeln keyen auf Freitext | #1663/#1664 | `erasure_engine.py:46-131` | **überholt** durch #1674: Regeln keyen auf `harvested_by_key`/`applied_by_key`/`inspected_by_key`, Freitext wird via `clear_fields` geleert |
| Admin-Delete wendet keine Anonymisierung an | #1664 | `user_service.py:105-133`; `grep -rn "compute_tombstone_hash" src/backend/app` → nur Docstrings | **bestätigt**, und breiter: **kein** Laufzeitpfad wendet `ANONYMIZE_COLLECTIONS` oder die Audit-Pseudonymisierung an; der Admin-Pfad lässt zusätzlich die `retention_worker`-Dokumente (Consents, Export-Requests, …) verwaist zurück |
| Pseudonymisierung von `erasure_requests.user_key` muss nach Filterschritten laufen | #1663 | `erasure_engine.py:258-268` | **bestätigt** als deklarierte Reihenfolge (`_anonymize_collections` → `_pseudonymize_audit_collections` → `users`), aber nicht ausgeführt und nicht getestet |

## Mode decision

**Mode:** A — single strand

**Reason:** Lineare Abhängigkeitskette. #1663 und #1664 sind Voraussetzung bzw. Kern
des gemeinsamen Executors und damit nicht entfernbar, ohne die Gruppe aufzulösen; das
einzig realistisch entfernbare Mitglied ist das Ende der Kette (#1645), und das Ende
eines linearen Strangs lässt sich durch Zurücksetzen der Tail-Commits entfernen. Die
Mitglieder bearbeiten dieselben Dateien — Sub-Branches würden nur Konflikte erzeugen.

## Structural finding

**Cluster shape:** class cluster

**Root cause or defect class:** *Deklariertes Inventar ohne Ausführungspfad.* Regeln,
Schritte und Reihenfolge sind vollständig deklariert und durch einen Guard abgesichert,
aber kein Laufzeitpfad erreicht sie. Dieselbe Klasse wie #1645 (Executor-Gerüste) und
der entfernte April-Audit-Layer (zählte Gerüste als 100 %).

**Process finding:** Der #1622-Guard (`scripts/check_privacy_inventory.py` R1–R4) prüft
die **Konsistenz der Deklaration** (Namen, Executor-Literale), nicht dass ein
Ausführungspfad jeden deklarierten Schritt erreicht. Bereits als claude-shared#660
erfasst (Audit-Anforderung „Ausführungspfad erreicht deklarierten Umfang").

**Preventive change (in dieser Gruppe):**
1. Guard-Regel R5: jeder `document`/`edge`-Schritt und jede `AnonymizationRule`
   deklariert ein Nutzerfeld, das auf dem Modell existiert.
2. Reichweiten-Integrationstest: ein Nutzer mit genau einer Zeile in jeder deklarierten
   Collection wird gelöscht; der Test zählt pro deklariertem Schritt die tatsächlich
   gelöschten/anonymisierten Zeilen und schlägt fehl, wenn ein Schritt 0 erreicht.
   Status-Felder werden nicht gelesen.

**Recurrence fed to the portfolio loop:** Klasse „declared scope, unexecuted" — 3.
Vorkommen (April-Audit-Layer, #1645, diese Gruppe); Zuführung über claude-shared#660,
kein neues Issue.

## Design (Kurzfassung)

- `ErasureStep` erhält `user_field: str | None` (Pflicht für `edge`/`document`; bei Edges
  `_from`/`_to`).
- **Ein** Executor im Data-Access-Layer (neben `ArangoUserRepository.delete`, das heute
  schon `build_erasure_plan(key).steps` für `account_cascade` abläuft) führt einen Plan
  in deklarierter Reihenfolge aus: Löschschritte filtern per `user_field`,
  `_anonymize_collections` wendet `ANONYMIZE_COLLECTIONS` an (`marker` /
  `tombstone_hash` + `clear_fields`), `_pseudonymize_audit_collections` hasht zuletzt
  vor `users`. Rückgabe: Zeilenzahlen pro Schritt.
- Beide Pfade rufen denselben Service-Einstieg: der Admin-Route (`router.py:256`) und
  `_finalize_erasure`. `completed` wird nur gesetzt, wenn der Executor alle Slices
  ausgeführt hat; Zählungen werden geloggt.
- `find_active_for_user`-Rest aus #1645: mit echtem Executor bleibt
  `partially_completed` nur bei Fehlern; Entscheidung siehe offene Frage 3.

## Completeness matrix

| Member | Source | Migration | Spec | Tests | Docs | Guard / CI config |
|---|---|---|---|---|---|---|
| #1663 | `privacy.py` `ErasureStep.user_field`; `erasure_engine.py` `DELETE_STEPS` mit Nutzerfeldern; Regel für `quality_assessments` je nach Frage 1; check: `task test:backend` (unit) | nur falls Frage 1 = Key-Feld: `v0057` stempelt `assessed_by_key` (wie v0056, kein Backfill); check: `task test:backend:integration` (Migrationstest) — sonst not applicable | `spec/req/REQ-025` §ANONYMIZE_COLLECTIONS-Kopie (:353-420) an Code angleichen; NFR-011 doppelte ID R-19 (:86 vs. :175) auflösen; 3 spec-only Collections als „nicht implementiert" markieren; check: `pre-commit run --files <spec>` | `test_privacy_engines.py`: jede Regel/jeder Schritt adressiert existierendes Feld; check: `task test:backend` | not applicable — Nutzerfeld ist internes Inventar | `check_privacy_inventory.py` R5 + `test_privacy_inventory_check.py` Rot-zuerst; check: `pre-commit run privacy-inventory --all-files` |
| #1664 | Gemeinsamer Executor (data_access) + Admin-Route ruft ihn; check: `task test:backend` | not applicable — keine Schemaänderung | not applicable — NFR-011/REQ-025 beschreiben das Verhalten bereits | Integration: Nutzer mit je 1 Zeile pro Retained-Collection, Admin-Delete, kein Feld löst mehr auf den Key auf (Zeilen lesen, nicht Status); check: `task test:backend:integration` | `docs/{de,en}/guides/data-retention.md` §Mindestaufbewahrung: `user_key = null` → tatsächliche Form (`anon_…`-Hash bzw. `_anonymized`) ; check: `task docs` (mkdocs strict) | `.github/lane-inputs/*` falls neue Dateien in gemessenen Lanes: Neu-Aufnahme via `scripts/ci/lane_inputs.py`; check: `test_lane_filters_cover_measured_inputs.py` |
| #1645 | `_finalize_erasure` ruft den Executor; `completed` nur bei voller Ausführung; check: `task test:backend` | not applicable | REQ-025 AK-08a unverändert erfüllt (Kategorien); not applicable für Text | `test_privacy_executor_truthfulness.py` angepasst; Reichweiten-Integrationstest über den Self-Service-Pfad inkl. Reihenfolge (Audit-Hash nach Filterschritten); check: `task test:backend:integration` | not applicable — Doku-Änderung liegt bei #1664 (gleiche Seite) | not applicable — dieselbe Guard-Änderung wie #1663 |

## Risks

- **Datenverlust durch falschen Filter** (höchstes Risiko): ein falsches `user_field`
  löscht fremde Zeilen oder Aufbewahrungspflichtiges. Gegenmittel: Reichweitentest mit
  einem **zweiten** Nutzer, dessen Zeilen unverändert bleiben müssen.
- **Reihenfolgefehler**: Audit-Hash vor Filterschritten → zweiter Durchlauf findet
  nichts, Pflicht bleibt still offen. Gegenmittel: Test prüft Reihenfolge über
  Zeilenzählungen.
- **Admin-Pfad löscht künftig mehr** (Consents, Export-Requests, Pest-Detections): gewollt
  laut Inventar, aber Verhaltensänderung einer laufenden Route.
- **#1666 Befund 1** kann sich ändern (weniger `partially_completed`); nach Merge neu messen.

## Operator decisions (write gate, 2026-09-23)

1. `QualityAssessment.assessed_by`: **server-gesetztes `assessed_by_key` + Migration v0057**
   analog zu v0056, kein Backfill; Altzeilen bleiben `attribution_gap`. Freitext wird per
   `clear_fields` geleert, keine Freitext-Regel daneben.
2. Spec-only Collections: **nur in der Spec als nicht implementiert markieren**, keine
   Platzhalterregeln im Code.
3. `find_active_for_user`: **`partially_completed` blockiert** einen neuen Antrag.
4. Artefakt freigegeben (Schreib-Gate) mit Mode A, Reihenfolge #1663 → #1664 → #1645.

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|

## Deviations

| Member | Kind | What changed |
|---|---|---|
