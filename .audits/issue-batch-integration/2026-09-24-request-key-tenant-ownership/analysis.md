# Group pre-analysis: 2026-09-24-request-key-tenant-ownership

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges.

## Scope of this analysis

**Research question:** Welche Routen verwenden einen Key aus dem Request (Pfad oder Body), der auf einen mandantengebundenen Datensatz zeigt, ohne dessen Mandanten gegen den Aufrufer zu prüfen?

**The group's single logical change, in one sentence:** Every route that accepts a key to a tenant-owned record verifies that the record belongs to the caller's tenant (or the global catalogue where the union rule applies) before reading or storing it.

**Out of scope:** Reine Listen-Lesepfade (durch #1712 abgeleitet und abgesichert); Plattform-Admin-Routen.

**Tier:** 2 — ein Repository; API-Antworten ändern sich nur für fremde/unbekannte Keys (404/422 wie bei unbekannten).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1713 | security | thematic coupling (class cluster) | Schreibpfade speichern `fertilizers_used`-Keys ohne Mandantenprüfung (Befund aus #1712) |
| #1714 | security | thematic coupling (class cluster) | `GET /executions/{key}`, `POST /executions/{key}/tasks` lesen die Execution per Key ohne Owner-Prüfung (Befund aus #1712) |

**Dependency ordering:** unabhängig; #1714 zuerst (kleiner, gleiche Datei wie #1712-Nacharbeit), dann #1713.

**Shared touch surface:** `app/common/task_entity_guard.py` / Owner-Auflösung, Service-Schicht der Task- und Gießpfade, `test_tenant_scoped_reads_are_derived.py` (Kategorie `anchored`).

## Mode decision

**Mode:** A — zwei kleine, unabhängige Änderungen derselben Klasse; keine unsichere Akzeptanz, die Entfernbarkeit verlangt.

## Structural finding

**Cluster shape:** class cluster — „Key aus dem Request ohne Eigentumsprüfung“.

**Root cause or defect class:** Der #1708-Guard erlaubt By-Key-Lesezugriffe als `anchored` und erwartet die Eigentumsprüfung im Service; er kann nicht beweisen, dass sie stattfindet. Schreibpfade, die fremde Keys *speichern*, prüft kein Guard.

**Process finding:** Die Kategorie `anchored` ist unbewiesen (73/111 Aufrufergraph-Fehltreffer, dokumentiert in #1712). Preventive change in dieser Gruppe: prüfen, ob `anchored` einen Witness verlangen kann (Funktion ruft By-Key-Read und Owner-Check), wie `verified`-Ausnahmen; Entscheidung in #1714 festhalten.

**Recurrence fed to the portfolio loop:** „Guard opt-in am Aufrufort“ — bekannte Klasse (Memory: #948, #1402, #1704); kein neues Issue, Zuführung über dieses Bundle.

## Completeness matrix

| Member | Source | Tests | Guard | Spec | Docs |
|---|---|---|---|---|---|
| #1714 | Execution-Routen lösen Owner (Entity → Tenant) auf, 404 bei fremd/verwaist; check: `task test:backend` | Zwei-Mandanten-Routentests rot zuerst; check: pytest integration | `anchored`-Witness-Entscheidung; check: guard tests | not applicable — REQ-006 beschreibt Mandantentrennung bereits | not applicable — kein nutzersichtbares Verhalten außer 404 |
| #1713 | jede Schreibstelle für Dünger-Keys prüft Sichtbarkeit (eigene + globale Union), 422 wie unbekannt; check: `task test:backend` | Zwei-Mandanten-Test je Schreibpfad rot zuerst | Entscheidung zu einem Schreib-Gegenstück zum #1708-Guard; check: guard tests oder Begründung | not applicable — REQ-004/REQ-024 unverändert | not applicable |

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #1714 | fullstack-developer | Zwei-Mandanten-Routentests vor/nach | `3 failed, 2 passed` (`assert 200 == 404`, `assert 201 == 404`) → `52 passed` |
| #1714 | fullstack-developer | `anchored`-Witness gemessen | 115 anchored; 88 request-erreichbar; starker Witness 27/88, loser 67/88 → Regel wäre bei 61 bzw. 21 korrekten Stellen rot → **nicht eingeführt**, Zahlen im Guard-Docstring |
| #1713 | fullstack-developer | Routen je Pfad fremd/unbekannt/eigen/global vor/nach | `10 failed, 20 passed` → `30 passed` |
| #1713 | fullstack-developer | Write-Side-Guard gegen alte Services | `1 failed, 7 passed` (`create_event builds ['FeedingEvent'] and reaches no fertilizer visibility check`) → grün |
| Gruppe | fullstack-developer | `tests/unit tests/api` auf finalem HEAD | `12395 passed, 20 skipped` |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #1713 | local adaptation | Unbekannte Dünger-Keys wurden bisher still gespeichert → jetzt 422 (gleiche Antwort wie fremd). Kanal-Zuweisung/Inkompatibilität behalten ihre 404-Semantik. Ein `MagicMock`-Double, das jeden Key als unsichtbar meldete, auf die echte Form korrigiert. |
| #1714 | local adaptation | `anchored`-Witness-Regel gemessen und verworfen (zu viele korrekte Stellen rot); Entscheidung im Guard-Docstring. |
