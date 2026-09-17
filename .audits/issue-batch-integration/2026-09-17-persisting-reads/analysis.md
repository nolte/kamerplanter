# Gruppe `2026-09-17-persisting-reads`

Status: Analyse abgeschlossen · Write-Gate offen (Operator-Freigabe ausstehend)

Gemessen gegen `origin/develop` @ `0b4ce20bf` (2026-09-17). Transientes Artefakt — wird vor dem Bündel-PR per `git rm` entfernt; der dauerhafte Nachweis ist der PR-Body.

## Die Frage, auf die die Research-Phase gescoped war

Welche GET-Handler erreichen heute eine Repository-Schreiboperation, warum, und was ist je Handler die Form, in der der Lesepfad frei von Persistenz wird — und welche dieser Schreibstellen tragen dasselbe ungefangene Insert-Rennen (Code 1200), das #1436/#1486 an anderer Stelle geschlossen haben?

## Die eine logische Änderung

Kein GET-Handler des Detektor-Inventars erreicht mehr eine Repository-Schreiboperation — Auto-Create-Singletons und Cache-/Tipp-Generierung wandern auf den Schreibpfad, wo ihr Insert-Rennen 1200 wie 1210 abgefangen wird — sodass `_PERSISTING_READ_FINDINGS` leer wird.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1461** | `bug`, `security`, `backend` | Anker | `src/backend/tests/unit/api/test_write_route_gates.py:294` `_PERSISTING_READ_FINDINGS` — 10 Einträge, unverändert seit dem Anlegen (verifiziert: #1486 hat nur `_GUARDED_PERSISTING_READS` um eine Senke erweitert) |
| **#1460** | `security`, `backend` | Abhängigkeitskette | Einträge 3+4 des Inventars sind `glossar.public_router.public_get_term` und `get_term`; #1461 ist ohne #1460 nicht schließbar |
| **#1458** | `bug`, `backend` | geteilte Berührungsfläche | `user_preference_service.py:93-98`, `onboarding_service.py:46-51`, `season_state_repository.py:46-56` — exakt die Zeilen, an denen die #1461-Einträge 5–8 (`get_onboarding_state`, `get_preferences`, `get_site_season_state`) repariert werden |

Kein gemeinsames Zeitfenster als Prädikat. Alle drei am 16.09. aus derselben Messung (AST-Detektor `_write_call_graph.py`) entstanden — das ist der Grund, warum sie dieselbe Fläche teilen, nicht das Prädikat.

## Was gemessen wurde, und wo der Issue-Text danebenliegt

### #1461 — das Inventar, Eintrag für Eintrag

| # | Handler | Senke (gemessen) | Befund |
|---|---|---|---|
| 1 | `auth.oauth_callback` | User-/Link-Erzeugung | GET ist **protokollbedingt** (OAuth-Redirect); REQ-023 nennt es. Kein Lesepfad — ein *Schreibpfad mit GET-Verb*. |
| 2 | `privacy.download_export` | `privacy_service.py:225-227` | Markiert den Export als abgeholt (Art.-15-Nachweis). Audit-Schreibung auf einem Read. |
| 3 | `glossar.public_router.public_get_term` | `glossary_service.py:108,131-135` `_generate → _store_cache → upsert` (`:338-340`) | anonym, 30/min; LLM-Aufruf je Cache-Miss → #1460 |
| 4 | `glossar.get_term` | dieselbe Kette | authentifiziert, gleiche Form |
| 5 | `ki_assistent.get_daily_tip` | Tipp-Generierung + Persistenz | `refresh_tips` (`tenant_router.py:105`, grower-gated) existiert bereits als Schreibpfad |
| 6 | `ki_assistent.get_tips` | dito | dito |
| 7 | `onboarding.get_onboarding_state` | `onboarding_service.py:46-51` `create()` bei Miss | Auto-Create-Singleton, Rennen 1200 ungefangen (#1458) |
| 8 | `preferences.get_preferences` | `user_preference_service.py:93-98` | dito |
| 9 | `dashboard.get_widget_catalog` | Katalog-Seed bei Miss | Seed gehört in den Start/Migration, nicht in den Read |
| 10 | `season.get_site_season_state` | `season_state_service.py:126` upsert; Celery `season_tasks.py:54` ruft dieselbe Methode | Der Task persistiert bereits; der GET muss es nicht |

**Abweichung vom Issue-Text:** #1461 behandelt alle zehn als eine Klasse „schreibende GET". Gemessen sind es **drei Formen**: (a) zwei protokoll-/nachweisbedingte Schreibungen (1, 2), die *bleiben* und einen begründeten, senkengebundenen Allowlist-Eintrag brauchen (Form von `_GUARDED_PERSISTING_READS`); (b) vier Auto-Create-Singletons (7, 8, 9, 10), bei denen der Read einen Default liefert und die *erste Schreibung* das Dokument anlegt; (c) vier Generierungen (3, 4, 5, 6), die auf einen expliziten Schreibpfad (POST/Celery) wandern. Die Regel des Detektors „Eintrag entfernen ist frei" macht jede Form einzeln mergebar.

### #1460 — der Mindestteil ist erledigt, die Entkopplung nicht

Der Inventar-Eintrag `test_write_route_gates.py:305-314` trägt bereits die korrigierte Begründung (kuratierter Katalog, Rate-Limit, Restrisiko Modellkosten). `tasks/glossary_tasks.py` hat nur `cleanup_expired_cache` (`:20`) und `invalidate_after_reingest` (`:29`) — ein Generierungs-Task existiert nicht. **Ein anonymer Aufrufer kann heute mit 30 Requests/min je Slug LLM-Kosten erzeugen.**

### #1458 — die Klasse hat inzwischen ein zweites Exemplar der Zielform

`_update_doc` (`base_repository.py:602-625`) und `_update_doc_fields` (`:628-660`) mappen nur 1202/1210; 1200 bleibt roh (500). **#1486 hat `create_edge` auf 1200 → `WriteConflictError` erweitert (`:928-933`) und `care_reminder_service.py:341` fängt `(DuplicateError, WriteConflictError)`** — der Issue-Text kennt nur das #1436-Exemplar. Das MCP-Vertragsregister `mcp/router.py:134-142` `_CONTRACT_ERROR_CODES` führt keinen Konflikt-Code (REQ-050).

## Strukturbefund über die Mitglieder hinweg (§E)

**Klassen-Cluster.** Zwei Klassen, beide aus MEMORY.md als teuerste geführt: *HTTP-Safe-Method persistiert* (#1461/#1460) und *Guard implementiert, Geschwister nie bedient* (#1458: 1200-Mapping in `create_edge`, nicht in `_insert_doc`/`_update_doc*`). Der Class-sweep des PRs läuft über beide: das Detektor-Inventar (muss leer werden) und `grep -rn "except DuplicateError" src/backend/app/` (jede Stelle, die ein Insert-Rennen fängt, fängt beide Codes).

Prozessbefund: keiner über #1456 hinaus.

## Stufe und Designentscheidungen (das *Wo*, vor dem *Wie*)

**Stufe 3** — veröffentlichte Verträge: REQ-023 (OAuth-Callback), NFR-006-Fehlerform (409 bei 1200), REQ-050 (MCP-Fehlercodes), anonyme Glossar-API.

Entscheidungen, die mit der Freigabe dieses Artefakts gelten:

1. **Form (a), Einträge 1+2:** bleiben als GET. Sie wandern aus `_PERSISTING_READ_FINDINGS` in `_GUARDED_PERSISTING_READS` mit **Senken-Menge** (nur die Audit-/Link-Collection) und einem Satz in REQ-023 §(OAuth) bzw. REQ-025 (Export-Nachweis), der die Schreibung auf dem GET *benennt*. Der Detektor prüft, dass keine andere Senke erreicht wird.
2. **Form (b), Einträge 7–10:** der GET liefert bei fehlendem Dokument den **Default ohne Persistenz** (`ETag`/`created: false` o. ä. nur, wenn ein Konsument es braucht — messen). Die erste Schreibung (`PUT`/`PATCH`) legt an: `upsert` bzw. `insert` mit Fang von 1200 **und** 1210 → Nachlese (Muster `care_reminder_service.py:341`). `get_widget_catalog`: Katalog wird beim Start/Seed angelegt (messen, wo `seed_*` heute läuft), der GET liest. `get_site_season_state`: der GET berechnet transient, nur der Celery-Task persistiert.
3. **Form (c), Einträge 3–6:** **kein GET generiert.** Glossar: Generierung läuft (i) nach Reingest über einen neuen Celery-Task `warm_glossary_cache` für den kuratierten Katalog (Hook in `invalidate_after_reingest`), (ii) auf Anforderung über `POST /t/{slug}/glossary/term/{slug}/generate` (grower, `require_permission('glossary', CREATE)`). Der anonyme GET liefert Cache **oder** die kuratierte Kurzdefinition ohne LLM-Anreicherung (404 nur, wenn der Slug nicht im Katalog ist). Tipps: `get_daily_tip`/`get_tips` lesen gespeicherte Tipps; leer → leere Antwort mit `refresh_available: true`; Generierung nur über das vorhandene `refresh_tips`.
4. **#1458:** `_insert_doc`, `_update_doc`, `_update_doc_fields` mappen 1200 → `WriteConflictError` (409, NFR-006 additiv); die drei Aufrufstellen fangen `(DuplicateError, WriteConflictError)`; MCP `_CONTRACT_ERROR_CODES` erhält `WRITE_CONFLICT` (REQ-050, additiv — kein bestehender Code ändert Bedeutung).

**Bewusst nicht in dieser Gruppe:** das `entity`-Vokabular (#1465, eigener Läufer, zuletzt im Zug).

## Modus und Scheiben

**Modus B** — Sub-Branch je Mitglied auf dem Gruppenbranch `fix/2026-09-17-persisting-reads`. Herauslösbarkeit ist real: #1460 braucht einen neuen Celery-Task (Designrisiko), Form (a) hängt an Spec-Sätzen, die der Review ablehnen kann. Kriterium: ein Mitglied wird herausgelöst, wenn sein Sub-Branch nach zwei Review-Runden nicht verifiziert ist; das Inventar behält dann seine Einträge (Teilfortschritt ist mergebar).

Reihenfolge: **#1458 → #1461 (Formen a, b, Tipps) → #1460 (Glossar)**. #1458 zuerst, weil die Singleton-Umbauten in #1461 an denselben Zeilen das 1200-Mapping bereits voraussetzen.

| Scheibe | Mitglied | Inhalt | Rot-zuerst |
|---|---|---|---|
| 1 | #1458 | 1200-Mapping in `_insert_doc`/`_update_doc`/`_update_doc_fields`; drei Aufrufstellen; MCP-Code | Unit: Fake-Collection wirft 1200 → alter Code 500, neu 409; Integration: zwei parallele Erst-Schreibungen |
| 2 | #1461 (a) | Einträge 1+2 in `_GUARDED_PERSISTING_READS` mit Senken-Menge; Spec-Sätze | Detektor rot, wenn eine zweite Senke erreichbar ist |
| 3 | #1461 (b) | Singletons 7–10: Default-Read, Schreibpfad legt an | Detektor rot vor dem Umbau; API-Test: GET ohne Dokument persistiert nichts (Collection-Count) |
| 4 | #1461 (c, Tipps) | `get_daily_tip`/`get_tips` lesen nur | Detektor; API-Test |
| 5 | #1460 | Glossar: Warm-up-Task, POST generate, GET liest | Detektor; anonymer GET auf Miss ruft kein LLM (Double zählt Aufrufe) |

## Vollständigkeitsmatrix

| Issue | Akzeptanzkriterium (aus dem Issue) | Scheibe | Nachweis |
|---|---|---|---|
| #1461 | Inventar leer oder jeder Rest-Eintrag senkengebunden begründet | 2–5 | `_PERSISTING_READ_FINDINGS == frozenset()` im Guard |
| #1461 | jede Entfernung hat einen Test, der die Schreibung auf dem GET rot zeigt | 3–5 | Detektor-Gegenprobe je Eintrag |
| #1460 | anonymer GET löst keine Generierung/Persistenz aus | 5 | LLM-Double-Zähler = 0 auf Miss |
| #1460 | Katalog bleibt anonym lesbar | 5 | API-Test 200 auf Katalog-Slug |
| #1458 | drei Stellen fangen 1200 | 1 | Unit-Tests rot-zuerst |
| #1458 | 1200 → 409 im Fehlervertrag, MCP-Code | 1 | Contract-Test |

## Verifikation

Je Scheibe: Rot-zuerst-Beweis (Gegenprobe per `cp`), Detektor-Lauf, `pytest tests/unit tests/api tests/contracts --max-skipped` je Tier, `tests/integration` gegen `arangodb:3.12`. Unabhängiger Review (`python-code-reviewer`, Read-only, eigener Kontext) auf dem Bündel-Tip vor dem PR; Class-sweep-Abschnitt im PR-Body.

Dispatch: `nolte-engineering:fullstack-developer` je Scheibe, sequenziell auf dem Gruppenbranch.
