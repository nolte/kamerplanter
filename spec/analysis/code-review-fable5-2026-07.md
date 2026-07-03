# Code-Review & Umsetzungsplan — Kamerplanter (Fable 5, Juli 2026)

> **Erstellt:** 2026-07-03 · **Branch:** `chore/code-review-fable5` (von `origin/develop` @ `e4049335`)
> **Methodik:** Sechs parallele Fable-5-Review-Agenten über die drei Achsen
> **Sicherheitslücken**, **Implementierungslücken** und **Doppelter Code**, jeweils
> belegt mit `file:line` und Bezug zu `spec/req/` / `spec/nfr/`.
> **Scope:** `src/backend/app/` (~78k LOC / 627 Dateien), `src/frontend/src/` (379 TS/TSX),
> `src/knowledge-service/`, `src/inference-service/`, `helm/`, `.github/workflows/`.

Alle Pfade relativ zum Repo-Root.

---

## 1. Executive Summary

Die Codebasis ist insgesamt solide und diszipliniert: AQL-Queries nutzen überwiegend
`bind_vars`/`AQLBuilder` (keine echte Injection gefunden), Frontend-Tokens liegen nur im
Memory + HttpOnly-Cookie (kein `localStorage`, kein `dangerouslySetInnerHTML`), die
Kern-Algorithmen VPD (Tetens), GDD, Phase-Engine (Rückwärtssperre) und der Karenz-422-Pfad
sind fachlich korrekt.

Die relevanten Befunde konzentrieren sich auf **fünf Themen**:

| # | Thema | Schwere | Kern-Befund |
|---|-------|---------|-------------|
| 1 | **Zeitzonen-Bug in Sicherheits-Gates** | 🔴 Kritisch | tz-aware/naive-`datetime`-Mismatch → HTTP 500 statt 422 in Karenz-, Resistance- und HST-Prüfung |
| 2 | **DSGVO-/Retention-Lücken** | 🟠 Hoch | Datenexport wird nie dispatcht; NFR-011-Downsampling + Master-Task fehlen; Retention-Tasks ohne Retry |
| 3 | **Interne Microservices ohne Auth** | 🟠 Hoch | knowledge-/inference-service komplett unauthentifiziert; keine NetworkPolicies; `changeme`-Defaults ohne Fail-Fast |
| 4 | **Datenkorruptions-/Fachlogik-Bugs** | 🟠 Hoch | `species_key="placeholder"`-Überschreibung; EC-Budget-Pfad ohne pH-Reserve; area-based Dosing nicht berechnet |
| 5 | **Strukturelle Duplikation** | 🟡 Mittel | CRUD-/Mapping-/Fetch-Boilerplate; EC-/Mixing-Logik doppelt (Drift-Risiko) |

Die großen „Scaffold-REQs" (REQ-008/017/018/026/031/033/035/036) sind bewusst im Backlog
(`.audits/execution-roadmap.md`, Buckets D/E) — **kein neuer Handlungsbedarf**, aber das
Aggregat-Audit „72/72 = 100 %" ist irreführend (misst nur Artefakt-Präsenz, nicht Semantik).

---

## 2. Findings nach Achse

### 2.1 Sicherheit

#### Backend / Auth
- **[SEC-B1]** JWT-Decode ohne Algorithmus-Allowlist — `domain/engines/token_engine.py:46`. `authlib_jwt.decode(token, secret)` schränkt `alg` nicht ein (Algorithm-Confusion-Fläche). *Fix:* feste Whitelist `["HS256"]`. — **Mittel**
- **[SEC-B2]** Kein `type=="access"`-Claim-Check beim Access-Decode — `token_engine.py:43-60`. Fremd-JWT mit gleichem Secret würde akzeptiert. — **Niedrig**
- **[SEC-B7]** `except (DecodeError, Exception)` zu breit — `token_engine.py:50`. Verschleiert Bugs als Auth-Fehler. — **Niedrig**
- **[SEC-B3]** SSRF: externe HTTP-Clients ohne `validate_server_side_url` — `data_access/external/ha_client.py:10-19` (tenant-konfigurierbare `base_url` + mitgesendeter HA-Token!), analog `kindwise_pest_adapter.py`, `perenual_adapter.py`, `gbif_adapter.py`. Die Media-Clients machen es korrekt vor. — **Mittel** (ha_client), Rest zu verifizieren
- **[SEC-B4]** Tenant-Isolation opt-in statt erzwungen — `base_repository.py:48-49` (`if tenant_key:`). `get_all()` ohne `tenant_key` liefert **alle** Tenants → ein vergessener Parameter = Cross-Tenant-Leak. Router übergeben aktuell korrekt, aber Absicherung liegt allein beim Aufrufer. — **Mittel** (REQ-024)
- **[SEC-B5]** `LIMIT {offset},{limit}` per f-String statt bind_vars — `ipm_repository.py:57,99,174,239`, `harvest_repository.py:25,85`, `task_repository.py:53,288` u.a. Aktuell durch `int`+`Query(le=200)` nicht ausnutzbar, aber Disziplin-Bruch. `phase_sequence_repository.py:32` macht es korrekt. — **Niedrig**
- **[SEC-B6]** Collection-/Feldnamen per f-String — durchgängig `data_access/arango/*`; Werte gebunden, Namen aus Konstanten → aktuell kein Injection-Pfad, aber fragil. — **Info**

#### Infrastruktur / Microservices
- **[INF-S1]** knowledge-service **komplett ohne Auth** — `src/knowledge-service/app/main.py:98-103,135,163,203`. `/ingest` triggert synchrone Re-Indizierung (DoS), `/ask` verbrennt unauth. LLM-Ressourcen (600s-Timeout). Backend-Proxy ist zwar auth-geschützt, aber jeder Pod erreicht den Service direkt. — **Hoch** (NFR-001 §6, REQ-023)
- **[INF-S2]** inference-service ebenfalls ohne Auth — `src/inference-service/app/main.py:1-14`. Kompromittierter Pod kann Referenz-Embeddings löschen. — **Mittel**
- **[INF-S3]** Keine NetworkPolicies im Helm-Chart trotz `HELM.md`-Pflicht — `helm/kamerplanter/` (0 Treffer). Verschärft INF-S1/S2; DBs clusterweit erreichbar. — **Mittel**
- **[INF-S4]** `changeme`-Default-Passwörter ohne Fail-Fast — `src/knowledge-service/app/config.py:14`, `src/inference-service/app/config.py:20`. Backend hat Startup-Gate (`main.py:44-61`), die Microservices starten kommentarlos gegen Postgres. — **Mittel**
- **[INF-S5]** Backend-Fail-Fast prüft nur 3 Secrets + per `DEBUG=true` abschaltbar — `main.py:44-52`; ungeprüft: `fernet_key` (`settings.py:158`, OIDC-Verschlüsselung). — **Niedrig**
- **[INF-S6]** Third-Party-Actions nur Tag- statt SHA-gepinnt — `docker-publish.yml`, `security-nuclei-*.yml:69/183`, `claude.yml:31`. Kein `pull_request_target` (gut), `claude.yml` korrekt author-gegated. — **Niedrig**
- **[INF-S7]** Prompt-Injection-Fläche im RAG-Pfad weich abgesichert — `src/knowledge-service/app/prompt_engine.py:195-201`. Frage + Client-`context` ohne Delimiter-Härtung; Wirkung begrenzt, aber via INF-S1 unkontrolliert. — **Niedrig**

#### Frontend
- **[FE-S1]** OAuth-Access-Token per URL-Query-Parameter — `pages/auth/OAuthCallbackPage.tsx:24-28`. JWT landet in History/Proxy-Logs/Referrer, widerspricht REQ-023. *Fix:* HttpOnly-Refresh-Cookie + `refreshAccessToken()`, mind. `history.replaceState`. — **Hoch**
- **[FE-S2]** `/admin/*`-Routen ohne Rollen-Gate auf Route-Ebene — `routes/AppRoutes.tsx:236-253`. Nur `ProtectedRoute` (Login); Backend blockt, aber UI-Defense-in-Depth fehlt (`usePlatformAdmin` existiert). — **Mittel**
- **[FE-S3]** Ungeprüfter `error`-Query-Param direkt gerendert — `OAuthCallbackPage.tsx:17-21,42-44`. Kein XSS (React escaped), aber Phishing-Text-Injektion + nicht i18n. — **Niedrig**
- **[FE-S4]** OAuth-Provider-Slug unkodiert in Redirect-URL — `pages/auth/LoginPage.tsx:125`. *Fix:* `encodeURIComponent`. — **Niedrig**

### 2.2 Domänenlogik-Korrektheit

- **[DOM-1]** 🔴 **Karenz-Gate crasht bei tz-aware Zeitstempeln** — `domain/services/ipm_service.py:266` + `domain/engines/safety_interval_engine.py:28-32`, auch `harvest_service.create_harvest_batch`. Naives `datetime.now()` vs. tz-aware `applied_at` aus Persistenz → `TypeError`/HTTP 500 statt sauberem 422-Block. *Fix:* durchgängig `datetime.now(UTC)` + geparste `applied_at` auf UTC normalisieren. — **Kritisch** (REQ-010)
- **[DOM-2]** 🔴 Gleiche tz-Falle in Resistance-Manager (`resistance_engine.py:32,74`) und HST-Recovery (`hst_validator.py:211,221,229`). HST rechnet zusätzlich in Lokalzeit → `days_remaining` um TZ-Offset verfälscht. — **Hoch** (REQ-010/003)
- **[DOM-3]** LineageEngine vollständig gestubbt — `domain/engines/lineage_engine.py:23-27` (`NotImplementedError`). Graft-Kompatibilität (Genus/Family) + `descended_from`-Traversal fehlen. — **Hoch** (REQ-017, Backlog Bucket D)
- **[DOM-4]** Flächenbasierte Dosierung (g/m², L/m²) nirgends berechnet — Felder in `domain/models/nutrient_plan.py:38-39`, aber keine Engine-Nutzung. — **Mittel** (REQ-004 W-013)
- **[DOM-5]** `NutrientSolutionCalculator` reserviert kein pH-/CalMag-EC — `domain/engines/nutrient_engine.py:35`, live über `api/v1/nutrient_calculations/router.py:50`. Parallel zum korrekten `EcBudgetCalculator` aktiver Pfad ohne pH-Reserve-Abzug → über-konzentrierte Lösung. — **Mittel** (REQ-004-A)
- **[DOM-6]** CalMag-Erkennung nur per Namens-Substring — `nutrient_engine.py:294,305,325`. „Cal-Mag"/„CaliMagic" werden nicht erkannt → CalMag-vor-Sulfat-Prüfung still übersprungen. *Fix:* an strukturierte Felder binden. — **Niedrig**

### 2.3 Implementierungslücken (Backend)

**Neue, nicht dokumentierte Code-Findings:**
- **[GAP-B5]** 🟠 DSGVO-Datenexport wird nie asynchron verarbeitet — `domain/services/privacy_service.py:170` (`# TODO celery dispatch`). Task existiert (`tasks/retention_tasks.py:33`), wird aber nie dispatcht → Export-Requests bleiben liegen (Art.-15-Risiko). — **Hoch** (REQ-025/NFR-011)
- **[GAP-B9]** 🟠 `PlantingRun.update_entry` defaultet `species_key` still auf `"placeholder"` — `api/v1/planting_runs/tenant_router.py:170`. Partial-Update ohne `species_key` überschreibt bestehenden Wert mit Dummy (Datenkorruption). — **Mittel→Hoch** (REQ-013)
- **[GAP-B8]** E-Mail-Digest-Task ist No-Op — `tasks/notification_tasks.py:349`. Läuft täglich 07:00, sendet nichts. — **Mittel** (REQ-030)
- **[GAP-B16]** Kalender-Aggregation traversiert PhaseSequence-Edges noch nicht — `domain/engines/calendar_aggregation_engine.py:19`. — **Niedrig** (REQ-015/003)

**Dokumentierte offene DRIFTs (Backlog-Referenz, verifiziert offen):**
- **[GAP-B2]** REQ-013 SuccessionPlan — 0 Code-Treffer (Issue #299). **Hoch**
- **[GAP-B3]** REQ-022 OverwinteringProfile + Winterhärte-Ampel — nur Reminder-Enums (`common/enums.py:754`) gelandet (Issue #299). **Hoch**
- **[GAP-B4]** REQ-018 Aktorik nur Scaffold — `domain/services/actuator_service.py:17,20` (`NotImplementedError`). **Hoch** (Roadmap D, 31 %)
- **[GAP-B6]** REQ-008 Post-Harvest Platzhalter — `post_harvest_service.py:23,27`. **Mittel**
- **[GAP-B7]** REQ-017 Propagation/Lineage Stubs — `propagation_service.py:17,20` (vgl. DOM-3). **Mittel**
- **[GAP-B10]** REQ-027 Mode-Switch offen — `onboarding_service.py:238`. **Mittel**
- **[GAP-B11..B15]** REQ-026 Aquaponik, REQ-016 InvenTree, REQ-031/033/035/036 KI-Familie, REQ-029/043 Vision-Reste — bewusste Future-Scaffolds. **Niedrig**

**Audit-Hygiene:**
- **[GAP-B1]** Coverage-Audit-Aggregat „100 %" irreführend — misst Artefakt-Präsenz, nicht Semantik. Warnbox auf alle Scaffold-REQs ausweiten.
- **[GAP-B17]** Veraltete Drift-Marker: REQ-014 (`_ms`-Suffix in `tank_service.py:125,242`) und REQ-015 (CF-005 `calendar_service.py:308-313`, iCal-Token `calendar/tenant_router.py:38`) sind im Code **bereits geschlossen** → MEMORY/Audit aktualisieren.

### 2.4 Implementierungslücken (Frontend)

- **[FE-L1]** „Als Vorlage kopieren"-Buttons sind Attrappen — `pages/aufgaben/WorkflowDetailPage.tsx:570-576`, `pages/duengung/NutrientPlanDetailPage.tsx:1055-1061` (Info-Toast, kein Effekt). *Fix:* disablen + Tooltip. — **Mittel** (UI-NFR-018 R-015)
- **[FE-L2]** REQ-001-v5.0-`origin`-Feld in 8+ Seiten als TODO gestubbt (identischer Kommentar kopiert). *Fix:* zentraler `resolveOrigin(entity)`-Helper. — **Mittel**
- **[FE-L3]** ~15 Nebenladungen schlucken Fehler stumm (`.catch(() => {})`) — u.a. `LoginPage.tsx:35` (OAuth-Buttons verschwinden kommentarlos!), `AccountSettingsPage.tsx:256,260,264`. *Fix:* `useAsyncOptions`-Hook mit error/empty-State. — **Mittel**
- **[FE-L4]** Hardcodierte, nicht übersetzte Strings — `AdminEditTenantPage.tsx:193`, `AdminEditUserPage.tsx:191`, `CalculationsPage.tsx:166`. — **Niedrig**
- **[FE-L5]** Redux-Slices setzen rohe englische Fallback-Fehlertexte (`'Failed to load …'`) die die DE-UI durchreicht — ~10 Slices. — **Niedrig**
- **[FE-L6]** Feste Pagination-Obergrenze 200 bei 39 „Alle laden"-Aufrufen — ab dem 201. Datensatz fehlen Einträge kommentarlos. — **Niedrig**
- **[FE-L7]** `window.confirm` statt `ConfirmDialog` für DSGVO-Account-Löschung — `AccountSettingsPage.tsx:522,529`. — **Niedrig**

### 2.5 Doppelter Code

#### Backend (größter Hebel: DUP-B1+B2+B3 → data_access −30–40 %)
- **[DUP-B1]** Typisierte CRUD-Wrapper über `BaseArangoRepository` in ~40 Repos (~500–800 LOC). *Fix:* `BaseArangoRepository[TModel]` generisch mit `_model_cls`. — **Hoch**
- **[DUP-B2]** Multi-Collection-Repos reimplementieren Base-CRUD von Hand — `ipm_repository.py:70-129`, `harvest_repository.py:33-174` (~150 LOC). — **Mittel**
- **[DUP-B3]** Handgeschriebene Ein-Feld-AQL trotz `find_by_field`/`AQLBuilder` — `oidc_config_repository.py:19,38,43`, `tenant_repository.py:19` (byte-identisch), DSGVO-Zwillinge `data_export_repository.py:37-67` ≈ `processing_restriction_repository.py:66-98`. — **Mittel**
- **[DUP-B4]** Response-Mapping-Idiom `Resp(key=m.key or "", **m.model_dump(...))` in 30 Routern (~100 Stellen). *Fix:* `to_response(model, Cls)` oder `model_config(from_attributes=True)`. — **Mittel**
- **[DUP-B5]** Pagination-Query-Parameter 39× kopiert. *Fix:* `PaginationParams`-Dependency. — **Mittel**
- **[DUP-B6]** Get-or-raise-`NotFoundError`-Block 118× in Services (~350 LOC). *Fix:* `get_or_raise(key)` auf Base-Repo. — **Mittel**
- **[DUP-B7]** ⚠️ Fertilizer-Anreicherung + `mixing_priority`-Fallback `50` dreifach — `nutrient_plan_service.py:301-311`, `dosage_calculation_engine.py:462-525`. **Fachlich riskant** (Mischreihenfolge soll aus einer Stelle emergieren). — **Mittel**
- **[DUP-B8]** ⚠️ EC-Budget „Ziel − Basis" in zwei Engines mit divergierenden Formeln — `ec_budget_engine.py:193` vs. `dosage_calculation_engine.py:248`. **Drift-Risiko** (vgl. DOM-5). — **Mittel**
- **[DUP-B10]** Kaskadierende Edge-Löschung kopiert — `ipm_repository.py:50-52,88-91`, `data_export_repository.py:69-72`. *Fix:* `base.delete_edges` um `direction` erweitern. — **Niedrig**
- **[DUP-B9]** DI-Factory-Boilerplate 121 `get_*`-Zweizeiler — niedriger Impact (explizite DI = Lesbarkeit). — **Niedrig**

#### Infrastruktur
- **[INF-D1]** `vectordb/`-Schicht doppelt in knowledge- + inference-service (inkl. `changeme`-Default). *Fix:* gemeinsames internes Paket. — **Mittel**
- **[INF-D2]** `asyncio.run`-Bridge + try/log/raise 9× in `tasks/*.py`, 4× wortgleich in `retention_tasks.py`. *Fix:* `run_async_task(name)`-Decorator. — **Niedrig**

#### Frontend
- **[FE-D1]** `usePagination` gibt Objekt ohne `useMemo` zurück — `hooks/usePagination.ts:31-35` (**verletzt PFLICHT-Konvention**). — **Mittel**
- **[FE-D2]** `useApiError` ohne `useMemo` — `hooks/useApiError.ts:114`. — **Niedrig**
- **[FE-D3]** Identischer Response-Interceptor doppelt — `api/client.ts:30-41` + `:63-74`. — **Niedrig**
- **[FE-D4]** Manuelles Fetch-Boilerplate (`load`+`loading`+`error`+`eslint-disable`) in ~29 Seiten — Hauptquelle der 40+ `eslint-disable`. *Fix:* `useFetch(key, fetcher)`-Hook. — **Mittel**
- **[FE-D5]** ~10 fast identische List-Slices. *Fix:* `createListSlice`-Factory (behebt zugleich FE-L5). — **Niedrig**
- **[FE-D6]** Monolithische Detail-Seiten (1.400–1.800 Z., 30–54 `useState`) — `SpeciesDetailPage.tsx`, `NutrientPlanDetailPage.tsx`, `WorkflowDetailPage.tsx`. *Fix:* Sektions-Komponenten + `react-hook-form`. — **Niedrig**

---

## 3. Umsetzungsplan (priorisiert)

Reihenfolge nach **Risiko × Aufwand**. Jedes Arbeitspaket (AP) ist eigenständig PR-fähig.
Aufwand: S = < ½ Tag, M = ½–2 Tage, L = > 2 Tage.

### 🔴 P0 — Sofort (Korrektheit / ausnutzbar)

| AP | Inhalt | Findings | Aufwand |
|----|--------|----------|---------|
| **AP-1** | **Zeitzonen-Härtung der Sicherheits-Gates.** Karenz-, Resistance- und HST-Berechnung durchgängig auf `datetime.now(UTC)` + UTC-normalisierte `applied_at` umstellen. Regressionstest mit tz-aware-Fixture, der heute HTTP 500 auslöst. | DOM-1, DOM-2 | M |

> AP-1 ist der wichtigste Punkt: ein realer Endnutzer-Pfad (Ernte anlegen bei laufender
> Karenz) liefert heute 500 statt der spezifizierten 422-Sperre.

### 🟠 P1 — Hoch (Sicherheit / DSGVO / Datenintegrität)

| AP | Inhalt | Findings | Aufwand |
|----|--------|----------|---------|
| **AP-2** | **DSGVO-Export dispatchen.** `send_task`-Aufruf Service→Celery in `privacy_service.py:170` ergänzen; veralteten TODO in `:358` entfernen; Retry/Backoff für Retention-Tasks (`autoretry_for`). | GAP-B5, INF-L3 | S |
| **AP-3** | **`species_key`-Placeholder-Bug.** Partial-Update in `planting_runs/tenant_router.py:170` so umbauen, dass fehlendes `species_key` den Bestand behält (bzw. 422), statt `"placeholder"` zu schreiben. | GAP-B9 | S |
| **AP-4** | **Microservice-Auth + Fail-Fast.** Shared-Secret/Service-Token-Header in knowledge- + inference-service prüfen; `changeme`-Default-Gate analog Backend-`main.py:44-61`; `fernet_key` in Backend-Gate aufnehmen. | INF-S1, INF-S2, INF-S4, INF-S5 | M |
| **AP-5** | **SSRF-Schließung.** `validate_server_side_url` in `ha_client` (tenant-konfigurierte URL + Token!) und allen Clients mit konfigurierbarem Ziel vor dem Request. | SEC-B3 | S |
| **AP-6** | **JWT-Härtung.** Feste Algorithmus-Allowlist `["HS256"]`, `type=="access"`-Claim-Check, engerer Exception-Catch im `token_engine`. | SEC-B1, SEC-B2, SEC-B7 | S |
| **AP-7** | **OAuth-Token nicht mehr über URL.** Callback auf HttpOnly-Refresh-Cookie + `refreshAccessToken()` umstellen; `error`-Param whitelisten + i18n; `encodeURIComponent(slug)`. | FE-S1, FE-S3, FE-S4 | M |

### 🟡 P2 — Mittel (Funktionslücken, Hardening, Refactoring mit Hebel)

| AP | Inhalt | Findings | Aufwand |
|----|--------|----------|---------|
| **AP-8** | **Tenant-Isolation erzwingen.** Für tenant-scoped Collections `tenant_key` verpflichtend (kein `None`-Default) oder Repo-seitig hart erzwingen; Aufrufer-Audit. | SEC-B4 | M |
| **AP-9** | **NetworkPolicies** (Default-Deny + gezielte Ingress) für knowledge-/inference-/embedding-Service + DBs. | INF-S3 | M |
| **AP-10** | **EC-/Mischlogik konsolidieren.** `nutrient_calculations`-Endpoint auf `EcBudgetCalculator`/`DosageCalculationEngine` umstellen (pH-Reserve + CalMag-Abzug); EC-net in **eine** Funktion; CalMag-Erkennung an strukturierte Felder. | DOM-5, DOM-6, DUP-B7, DUP-B8 | M |
| **AP-11** | **Flächenbasierte Dosierung** (g/m² × Fläche, g/Pflanze × Anzahl) als Service. | DOM-4 | M |
| **AP-12** | **Frontend-Attrappen entschärfen** (Buttons disablen/ausblenden) + `resolveOrigin`-Helper + `useAsyncOptions` mit Fehlerzustand (fixt verschwindende OAuth-Buttons). | FE-L1, FE-L2, FE-L3 | M |
| **AP-13** | **E-Mail-Digest** real implementieren (`list_users_with_digest_enabled` + Zustellung). | GAP-B8 | M |
| **AP-14** | **`useMemo`-Konventionsverstöße** + Response-Interceptor-Dedup. | FE-D1, FE-D2, FE-D3 | S |
| **AP-15** | **Base-Repository generisch** (`BaseArangoRepository[TModel]`, `get_or_raise`, `find_by_field`+sort/limit, `delete_edges`+direction); Multi-Collection-Repos + Ein-Feld-Queries darauf migrieren. | DUP-B1, B2, B3, B6, B10 | L |

### 🟢 P3 — Niedrig (Aufräumen, Konsistenz)

| AP | Inhalt | Findings | Aufwand |
|----|--------|----------|---------|
| **AP-16** | i18n-Fehlertexte in Slices (Codes/Keys statt Klartext) + `createListSlice`-Factory; Hardcoded-Strings auf `t()`. | FE-L4, FE-L5, FE-D5 | M |
| **AP-17** | `PaginationParams`-Dependency (Backend) + `fetchAllPages`/Server-Autocomplete (Frontend); `LIMIT @offset,@limit` bind_vars. | DUP-B5, SEC-B5, FE-L6 | M |
| **AP-18** | `to_response`-Helper + `run_async_task`-Decorator + `vectordb/`-Paket-Dedup; `window.confirm`→`ConfirmDialog`. | DUP-B4, INF-D1, INF-D2, FE-L7 | M |
| **AP-19** | GitHub-Actions auf SHA pinnen; RAG-Prompt-Delimiter-Härtung. | INF-S6, INF-S7 | S |
| **AP-20** | Detail-Seiten in Sektions-Komponenten + `react-hook-form` zerlegen (schrittweise). | FE-D6 | L |

### 📋 Audit-Hygiene (kein Code)
- **AP-21** — Drift-Marker für REQ-014/REQ-015 in MEMORY + `.audits/` als **geschlossen** markieren (GAP-B17); Coverage-Audit-Warnbox auf alle Scaffold-REQs ausweiten (GAP-B1). — S

### ⏭️ Bewusst im Backlog (kein AP)
LineageEngine/Propagation (DOM-3/GAP-B7, REQ-017), SuccessionPlan (GAP-B2), OverwinteringProfile
(GAP-B3), Aktorik (GAP-B4, REQ-018), Post-Harvest (GAP-B6), Mode-Switch (GAP-B10), NFR-011-Downsampling
(INF-L1/L2), KI-Familie/Aquaponik/InvenTree (GAP-B11..B15) → `.audits/execution-roadmap.md` Buckets D/E.
Bei Umsetzung von REQ-017 **DOM-3 direkt mitnehmen**.

---

## 4. Empfohlene Reihenfolge

1. **AP-1** (P0) als erster, isolierter PR — höchstes Nutzer-Risiko, klein.
2. **AP-2 + AP-3** (DSGVO/Datenintegrität, je S) — schnell, hoher Schutzwert.
3. **AP-4 + AP-5 + AP-6** (Security-Bündel) — vor dem nächsten Prod-Deploy.
4. **AP-7** (OAuth) parallel im Frontend.
5. P2 nach Kapazität; **AP-15** (Base-Repo) als Refactoring-Fundament, das viele spätere APs verkleinert.

---

## 5. Bereits sauber (verifiziert)
- AQL durchgängig `bind_vars`/`AQLBuilder`, kein `eval/exec/pickle/verify=False/shell=True`, YAML nur `safe_load`.
- Frontend: kein `dangerouslySetInnerHTML`/`innerHTML`, kein `console.log` in Prod, `rel="noopener"` auf allen `target=_blank`, Access-Token nur im Memory.
- VPD (Tetens, kPa), GDD (`max(0,(Tmax+Tmin)/2−Tbase)`), Phase-Engine (Rückwärtssperre), Karenz-`422`-Mapping korrekt.
- REQ-025-Retention-Fenster (Export-Expiry, 90d-Hard-Delete, E-Mail-TTL, IP-Anonymisierung Auth) real verdrahtet.
- Kein `pull_request_target`; `claude.yml` author-gegated; Backend-Knowledge-Proxy auth-geschützt; Tenant-Auflösung einheitlich per Dependency.

---

*Report generiert durch parallele Fable-5-Review-Agenten (6 Achsen). Alle Findings mit
`file:line` belegt; „zu verifizieren"-Marker kennzeichnen Punkte, die vor Umsetzung
kurz gegenzuprüfen sind.*
