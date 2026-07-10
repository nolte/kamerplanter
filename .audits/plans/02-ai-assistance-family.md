---
plan-type: implementation-plan
title: Umsetzungsplan KI-Assistenz-Familie (REQ-031/035/036/033)
epic: ai-assistance-family
covers: [REQ-031, REQ-035, REQ-036, REQ-033]
source-audit: spec/analysis/code-review-fable5-2026-07.md (GAP-B1)
status: ready
created: 2026-07-10
verified-against: develop
parallelizable: partial (REQ-031 blockt; 035‖036 parallel; 033 zuletzt)
specialist: fullstack-developer
---

## Ziel

Die vier Scaffolds der KI-Assistenz-Familie zu produktionsreifen Features ausbauen. Alle vier
Services werfen heute `NotImplementedError`; die Router sind leer; die Frontend-Pages sind
Platzhalter. Umzusetzen ist die vollständige, spec-konforme Implementierung von:

- **REQ-031** — KI-Assistent & Wissensvermittlung (RAG-basiert): Tipp-Karten, Tipp-des-Tages,
  „Warum?"-Buttons, kontextbewusster Chat (SSE). **Fundament** der Familie.
- **REQ-035** — KI-Fachbegriff-Glossar: kuratiertes 30-Begriffe-Skelett + RAG-On-Demand-Erklärung,
  `<TermTooltip>`, light-mode-fähig.
- **REQ-036** — Strukturierter KI-Diagnose-Assistent: Multi-Step-Wizard, Symptom-Katalog,
  Foto-Anhang, Top-3-Diagnose, IPM-Brücke.
- **REQ-033** — MCP-Server: kuratierte Tool-Palette (~30 Tools) als externe LLM-Schnittstelle,
  Service-Account-Auth, Permission-Matrix, Audit/Idempotenz.

Der Epic wird gestaffelt abgearbeitet: **REQ-031 baut das gemeinsame Fundament** (async
`KnowledgeServiceAdapter` mit Interface + Circuit-Breaker, `AiContextBuilder`, Consent-/Feature-Guards,
3-Stufen-Toggle, `<AIResponse>`-Hülle). REQ-035 und REQ-036 konsumieren dieses Fundament und laufen
danach parallel. REQ-033 (Aggregations-Layer über viele bestehende Services) kommt zuletzt.

## Ist-Stand (verifiziert 2026-07-10)

Verifikations-Evidenz aus `develop` (Datei-Reads + Grep). **Wichtige Korrektur zur Aufgaben-Annahme:**
Die LLM-Adapter existieren bereits — aber im **Knowledge-Service**, nicht im Backend. Per REQ-031
§1.2/§4.1 lebt die gesamte LLM-/RAG-Pipeline im Microservice; das Backend ist die dünne Tenant-,
Auth- und Kontext-Schicht und ruft den Knowledge-Service über HTTP. Das kritische Fundament ist
daher **nicht** ein Backend-LLM-Adapter, sondern der async, interface-basierte
`KnowledgeServiceAdapter` plus `AiContextBuilder`.

### REQ-031 — KI-Assistent (FUNDAMENT)

**Verdikt: Scaffold, Fundament fehlt komplett.**

Evidenz:
- `src/backend/app/domain/services/ki_assistent_service.py:16` — `KiAssistentService.answer()` wirft
  `NotImplementedError`. Konstruktor nimmt nur `llm_adapter`/`knowledge_client` als `Any`.
- `src/backend/app/api/v1/ki_assistent/router.py` — nur `APIRouter(prefix="/ki-assistent")`, keine
  Endpunkte. **Nicht in `main.py` registriert** (Grep leer).
- `src/backend/app/data_access/external/knowledge_service_client.py` (98 Z., echt) — **synchroner**
  `httpx`-Client (`.search/.ask/.classify/.health`), trägt bereits `internal_service_token` als
  Bearer. Aber: **kein Interface, kein async, kein Retry, kein Circuit-Breaker** (REQ-031 §4.1
  verlangt `IKnowledgeService` + `HttpKnowledgeServiceAdapter` mit `httpx.AsyncClient`, Retry ≤2 bei
  5xx, Circuit-Breaker 3-Fehler/60s).
- `src/knowledge-service/app/llm/` — **LLM-Adapter existieren bereits**: `ollama.py`, `anthropic.py`,
  `openai_compatible.py`, `interface.py`. Ebenso `prompt_engine.py`, `embedding.py`, `reranker.py`,
  `ingestor.py`. Der Microservice ist produktiv (REQ-031 §1.2).
- `src/backend/app/config/settings.py:243-251` — `knowledge_service_enabled=False`,
  `knowledge_service_url`, `internal_service_token` existieren. **Fehlt**: `ai_features_enabled`
  (Deployment-Flag, §1.3 Stufe 1), Timeout-/Circuit-Breaker-Werte.
- `src/backend/app/domain/engines/consent_engine.py:13` — `ConsentPurposeEngine.PURPOSES` enthält
  `core_functionality`, `error_tracking`, `hibp_check`, `external_enrichment`. **Fehlt**:
  `ai_tenant_data_access`, `ai_cloud_processing` (§1.3 Stufe 3).
- Frontend: `src/frontend/src/pages/ki-assistent/KIAssistentPage.tsx` (Platzhalter). **Kein**
  `src/frontend/src/components/ai/` (kein `<AIResponse>`, `<TipCardsPanel>`, `<DailyTipCard>`,
  `<WhyButton>`, `<AiChatDrawer>`).

Fehlt vollständig: `IKnowledgeService`-Interface + async `HttpKnowledgeServiceAdapter`,
`AiContextBuilder` (§4.2 inkl. ADR-002 Genus/Family-Fallback), `AiAssistantService`-Orchestrierung
(§4.3), `TipEngine`/`ExplainEngine` (§4.4/4.5), ArangoDB-Collections (`ai_provider_configs`,
`ai_conversations`, `ai_tip_cache`, `ai_audit_log` + Edges, §3), FeatureGuard/ConsentGuard/AuditLogger,
Endpunkte tenant/global/public (§5) inkl. SSE-Chat, `explain-templates`-YAMLs (§4.5),
Celery-Tasks (§4.6), Frontend-Komponenten (§6).

### REQ-035 — KI-Fachbegriff-Glossar

**Verdikt: Scaffold. Kleinste Spec (463 Z.), teilt Fundament mit REQ-031.**

Evidenz:
- `src/backend/app/domain/services/glossar_service.py:15` — `GlossarService.explain()` wirft
  `NotImplementedError`. Konstruktor nimmt nur `knowledge_client`.
- `src/backend/app/api/v1/glossar/` — Router-Package existiert (Scaffold). Nicht registriert.
- Frontend: `src/frontend/src/pages/ki-glossar/GlossarPage.tsx` (Platzhalter). `<HelpTooltip>`
  **existiert** als Foundation unter `src/frontend/src/components/common/HelpTooltip.tsx` (+ Test) —
  REQ-035 §5.1 erweitert diese zu `<TermTooltip>`.

Fehlt: `glossary_terms` + `glossary_term_cache` Collections/Repo (§2), `GlossaryService.get_term`
Cache-First + KB-Fallback (§4.1), `GlossarySeedService` aus
`spec/knowledge/glossary/seed_terms.yaml` (§4.2, ≥30 Begriffe §2.3), Endpunkte tenant/light/admin
(§3), Celery-Cleanup + Reingest-Invalidation (§4.3), `<TermTooltip>` + `<GlossaryPage>` (§5).

### REQ-036 — KI-Diagnose-Assistent

**Verdikt: Scaffold. Zusätzliche Abhängigkeit REQ-029 (Vision).**

Evidenz:
- `src/backend/app/domain/services/diagnose_service.py:16` — `DiagnoseService.diagnose()` wirft
  `NotImplementedError`. Konstruktor nimmt `llm_adapter`/`vision_engine`.
- `src/backend/app/api/v1/diagnose/` — Scaffold-Router. Nicht registriert.
- REQ-029-Vision-Infrastruktur teilweise vorhanden: `data_access/external/pest_inference_client.py`,
  `inference_service_client.py`, `domain/interfaces/pest_detection_adapter.py`,
  `domain/engines/pest_detection_engine.py`, `object_storage_adapter.py` (MinIO für Foto-Anhänge).
- Frontend: `src/frontend/src/pages/ki-diagnose/DiagnosePage.tsx` (Platzhalter). Kein
  `src/frontend/src/components/diagnosis/`.

Fehlt: `symptoms` + `diagnosis_sessions` Collections + Status-State-Machine (§2), `SymptomCatalog`
+ Seed aus `spec/knowledge/symptoms/seed_symptoms.yaml` (≥30, §4.1), `DiagnosisService` (§4.2),
`DiagnosisAnalysisEngine` (§4.3, JSON-Output-Zwang + Retry), `ImageRecognitionDispatcher` (§4.4,
Bridge zu REQ-029), Diagnose-Prompt-Templates (`spec/knowledge/diagnosis-prompts/`), Endpunkte (§3),
Celery-Tasks (§4.5), Frontend `<DiagnosisWizard>`/`<DiagnosisResultsPanel>`/`<DiagnosisHistoryList>`
(§5).

### REQ-033 — MCP-Server

**Verdikt: Scaffold. Aggregations-Layer, härteste Voraussetzungen (Service-Accounts + Permissions).**

Evidenz:
- `src/backend/app/mcp_server/server.py:23` — `MCPServer.serve()` wirft `NotImplementedError`.
  `register_tool`/`list_tools` existieren als Stub-Registry.
- `src/backend/app/api/v1/mcp/router.py` — nur `APIRouter(prefix="/mcp")`, leer. `tests/unit/mcp_server/`
  existiert als Test-Package-Stub.
- Voraussetzungen teilweise da: `src/backend/app/domain/models/user.py:10,25` — `AccountType =
  Literal["user", "service"]`, `account_type` existiert (REQ-023 v1.10 Service-Accounts).
  `src/backend/app/core/permissions.py` — `ResourceType`/`Action`/`_RBAC`-Matrix +
  `require_permission(...)`-Dependency existieren. **Fehlt**: `mcp.read`/`mcp.write`/`mcp.setup`
  als Permissions; `POST /auth/service-accounts/validate` (REQ-033 §5, Grep leer).
- REQ-033 nennt eigenes Code-Layout `src/mcp-server/` (eigener Prozess/Helm-Release, §4.1). Das
  Backend-Scaffold liegt aber unter `src/backend/app/mcp_server/`. **Design-Entscheidung offen**
  (siehe WP-033): eigenständiger Service vs. Backend-eingebettet.

Fehlt: Tool-Registry + `ToolBase`/`WriteToolBase` (§4.2), ~30 Tools (§2.1-2.4, wrappen bestehende
Backend-Endpunkte), DryRun/Idempotency/Bulk/Macro-Semantik (§2, §4.2.1), Auth-Interceptor +
PermissionGuard (§4.3/4.4), `mcp_audit_log` + `mcp_idempotency_record` Collections (§3), HTTP+SSE-
Discovery (§5), fehlende Backend-Aggregat-Endpunkte (§5-Tabelle: `plants/bulk`, `locations/bulk`,
`harvest/readiness`, `plants/{key}/archive`, `plants/{key}/location`, `privacy/mcp-activity`).

## Arbeitspakete

Ein WP-Block je REQ. Jeder WP ist selbst intern staffelbar; die WP-Reihenfolge untereinander steht
in „Reihenfolge & Parallelisierung".

---

### WP-031 — REQ-031 KI-Assistent (Fundament) [BLOCKER für 035/036/033]

**Problem.** `KiAssistentService.answer()` und alle KI-Endpunkte fehlen. Es gibt keinen async,
interface-basierten Zugang zum Knowledge-Service, keinen Kontext-Builder, keine Consent-/Feature-
Guards, keine `<AIResponse>`-Hülle. Ohne diese gemeinsame Basis können REQ-035/036/033 nicht
konsistent (Quellenpflicht, KI-Labeling, 3-Stufen-Toggle, Audit) gebaut werden.

**Umzusetzen.**
- **Fundament — KnowledgeServiceAdapter (§4.1):** `domain/interfaces/knowledge_service.py` mit ABC
  `IKnowledgeService` (`search`, `ask`, `health_check`), DTOs `KnowledgeChunk`, `QuestionContext`,
  `AskResult`. Impl `data_access/external/knowledge_service_adapter.py`
  (`HttpKnowledgeServiceAdapter`) auf `httpx.AsyncClient`, Timeout `AI_KNOWLEDGE_SERVICE_TIMEOUT_S`
  (default 60), Retry ≤2 bei 5xx, Circuit-Breaker (3 Fehler/60s → 60s unhealthy). Wrappt bzw.
  ersetzt den bestehenden synchronen `knowledge_service_client.py`; Bearer-Token-Weitergabe
  beibehalten.
- **Fundament — AiContextBuilder (§4.2 + ADR-002):** `base_context: QuestionContext` (nur PII-freie
  Stammwerte species/phase/substrate/ec/ph) IMMER; `extended_context` NUR bei Consent
  `ai_tenant_data_access`. `resolve_species_for_ks()` mit Genus/Family-Fallback + `cultivar_hint` +
  `ConfidenceLevel` (high/medium/low/none). Keine direkt-personenbezogenen Felder (NFR-007).
- **Fundament — 3-Stufen-Toggle (§1.3):** Settings-Flag `AI_FEATURES_ENABLED` (default false → KI-API
  liefert 404); Tenant-Setting `ai_features_enabled` (default false → 403 `ai.disabled_for_tenant`);
  Consent-Purposes `ai_tenant_data_access` + `ai_cloud_processing` in `consent_engine.py.PURPOSES`
  ergänzen. `FeatureGuard.require_ai_enabled(tenant)` + `ConsentGuard.require_consent(user, purpose)`.
- **Datenmodell (§3):** ArangoDB-Collections `ai_provider_configs`, `ai_conversations` (Retention 90d),
  `ai_tip_cache`, `ai_audit_log` (Retention 30d, nur Hash+Länge, kein Klartext) + Indexes; Edges
  `ai_tip_references_plant/run`, `ai_conversation_about`, `ai_audit_about`; Tenant-Settings-Sub-Objekt
  (`ai_features_enabled`, `ai_default_provider_key`, `ai_allow_cloud_providers`, `ai_daily_tip_enabled`).
  Migration im versionierten Framework (`schema_migrations`, ADR-005).
- **AiAssistantService (§4.3):** `get_tips`, `get_daily_tip`, `explain`, `chat` (SSE),
  `dismiss_tip`/`mark_tip_acted_on`, `delete_conversation` (Art. 17), `configure_provider`/
  `list_providers`. Ablauf pro Aufruf: FeatureGuard → ConsentGuard → AuditLogger.start → Logik
  (Cache → Context → KS-Aufruf) → AuditLogger.complete.
- **TipEngine (§4.4) + ExplainEngine (§4.5):** Cache-TTL 4h Redis / 24h ArangoDB; Daily-Tip-Cache
  bis Mitternacht Tenant-Zeitzone mit Aspekt-Auswahl (warning → milestone → Saison → Beginner);
  `ExplainEngine` lädt Question-Templates aus `spec/knowledge/explain-templates/*.yaml`, füllt Slots,
  ruft `/ask`. Backend-seitiger regelbasierter Fallback bei KS-Ausfall (W-011).
- **Provider-Schutz (§4.7):** API-Keys Fernet-verschlüsselt in `api_key_encrypted` (nutze
  bestehende `encryption_engine.py`); niemals in Log/Fehler/Audit.
- **API (§5):** Tenant-scoped (`/api/v1/t/{slug}/ai/`): `/tips`, `/tips/refresh`, `/tips/{key}/dismiss`,
  `/tips/{key}/acted-on`, `/daily-tip`(+dismiss), `/explain`, `/conversations` (+`/{key}`, `/messages`
  SSE `text/event-stream`, DELETE), `/providers` (CRUD + `/health`), `/settings` (GET/PUT). Global
  (`/api/v1/ai/`): `system-providers`, `knowledge-service/ingest`, `knowledge-service/health`
  (Platform-Admin). Public/Light (`/api/v1/public/ai/`): `ask` (Rate-Limit 10/min/IP, `context=null`),
  `health`. HTTP-Codes: 404 (Stufe 1), 403 `ai.disabled_for_tenant` (Stufe 2), 403 `consent_required`
  + `consent_purpose` (Stufe 3). Antwortschema §5.5. Router in `main.py` registrieren.
- **Celery (§4.6):** `ai.refresh_planting_run_tips` (06:00 UTC), `ai.cleanup_expired_conversations`
  (02:30), `ai.cleanup_expired_audit_log` (02:35), `ai.health_check_providers` (15 min, Prometheus-
  Gauge), `ai.knowledge_service_ingest` (So 03:00).
- **Frontend (§6):** `components/ai/AIResponse.tsx` (Pflicht-Hülle: KI-Badge + Modell-Tooltip,
  Sprach-Badge, Tenant-Daten-Indikator, Cloud-Indikator, Confidence-Badge ADR-002, Quellen-Accordion
  erfahrungsstufen-abhängig, Disclaimer). `TipCardsPanel.tsx`, `DailyTipCard.tsx`, `WhyButton.tsx` +
  `WhyDrawer.tsx`, `AiChatDrawer.tsx` (SSE-Streaming). Ausbau `pages/ki-assistent/KIAssistentPage.tsx`.
  Online-only-Verhalten (UI-NFR-012), Erfahrungsstufen-Sensitivität (REQ-021). i18n DE+EN.

**Betroffene Dateien.**
- Backend (neu): `domain/interfaces/knowledge_service.py`,
  `data_access/external/knowledge_service_adapter.py`, `domain/services/ai_context_builder.py`,
  `domain/services/ai_assistant_service.py` (ersetzt/erweitert `ki_assistent_service.py`),
  `domain/engines/ai_tip_engine.py`, `domain/engines/ai_explain_engine.py`,
  `domain/guards/{feature_guard,consent_guard}.py`, `domain/services/ai_audit_logger.py`,
  `domain/models/ai_*.py`, `data_access/repositories/ai_*_repository.py`,
  `api/v1/ki_assistent/router.py` (+ public/global-Router), `tasks/ai_tasks.py`,
  `spec/knowledge/explain-templates/*.yaml`.
- Backend (ändern): `config/settings.py` (`ai_features_enabled`, Timeout/CB-Werte),
  `domain/engines/consent_engine.py` (2 Purposes), `main.py` (Router-Registrierung), Celery-beat-Config,
  `migrations/`.
- Frontend (neu): `components/ai/{AIResponse,TipCardsPanel,DailyTipCard,WhyButton,WhyDrawer,AiChatDrawer}.tsx`,
  API-Layer + RTK-Query-Slice; (ändern): `pages/ki-assistent/KIAssistentPage.tsx`, Dashboard (REQ-009)
  für DailyTipCard, i18n-Ressourcen DE+EN.

**Akzeptanzkriterien.**
- `HttpKnowledgeServiceAdapter.ask()` ruft `/ask` async auf; bei 5xx erfolgt ≤2 Retry; nach 3 Fehlern
  in 60s liefert `health_check()` false (Circuit-Breaker), Unit-Test mit gemocktem httpx.
- Bei `AI_FEATURES_ENABLED=false` liefert jeder `/ai/`-Endpunkt HTTP 404 (Integrationstest).
- Bei `tenant.settings.ai_features_enabled=false` liefert `GET /tips` HTTP 403 `ai.disabled_for_tenant`.
- `GET /tips` ohne `ai_tenant_data_access`-Consent liefert 403 mit `consent_purpose`; mit Consent
  200 + `<AIResponse>`-konformes Schema (`answer_text`, `sources[]`, `uses_tenant_data`, `confidence`).
- Tenant-eigene Species (`origin='tenant'`) ohne `parent_species_key` löst Genus-Fallback aus:
  `QuestionContext.species="<Genus> sp."`, `confidence="low"`, `cultivar_hint` gesetzt (Unit-Test gegen
  `resolve_species_for_ks`).
- `ai_audit_log`-Eintrag enthält nur `question_hash` (sha256) + `answer_length`, keinen Klartext.
- Chat-Endpunkt liefert `Content-Type: text/event-stream`, Token-weise; `/tips`/`/daily-tip`/`/explain`
  liefern komplettes JSON.
- Public `POST /api/v1/public/ai/ask` sendet `context=null` an den KS (Test assertet Payload).
- `<AIResponse>` rendert KI-Badge; Vitest-Test: bei `confidence='low'` sichtbares „Allgemeine
  Information"-Badge; bei `uses_tenant_data=true` Tenant-Indikator.
- Cleanup-Task entfernt `ai_conversations` mit `expires_at < now()` und Audit-Einträge > 30d.
- Ruff/ESLint/tsc clean; pytest + vitest grün.

**Spezialist.** fullstack-developer.
**Aufwand.** L (Fundament + 4 Frontend-Feature-Bereiche + SSE + Datenmodell/Migration + Celery).
**Abhängigkeiten.** REQ-025 (Consent-Purposes), REQ-024 (Tenant-Settings), REQ-021 (Erfahrungsstufen),
REQ-027 (Light-Modus), NFR-007 (LLM-Sicherheit), NFR-011 (Retention), ADR-005 (Migration).
Voraussetzung für WP-035, WP-036, WP-033.

---

### WP-035 — REQ-035 KI-Fachbegriff-Glossar

**Problem.** `GlossarService.explain()` fehlt; kein kuratiertes Begriffs-Skelett, kein Cache, keine
`<TermTooltip>`. Ohne Glossar fehlt die light-mode-fähige Wissensvermittlung und die universelle
Begriffs-Anzeige, die REQ-006/009/022/036 konsumieren.

**Umzusetzen.**
- **Datenmodell (§2):** Collections `glossary_terms` (Unique-Slug, Index category/is_active) und
  `glossary_term_cache` (Unique `term_slug+language+expertise_level+kb_version`, Index `valid_until`);
  Repos.
- **Seed (§2.3, §4.2):** `spec/knowledge/glossary/seed_terms.yaml` mit ≥30 Slugs (vpd, ppfd, dli,
  photoperiode, hysterese, ec, ph, npk, calmag, ro-wasser, runoff, flush, drainage, substrat, frequenz,
  gdd, stretch, topping, fim, lst, mischkultur, fruchtfolge, companion-planting, sukzession,
  gruenduengung, eisheilige, phaenologie, winterhaerte, karenz, karenzzeit …) mit `labels`/`long_labels`/
  `aliases` DE+EN, `fallback_text` DE+EN, `rag_query_template`, `related_term_slugs`. Idempotenter
  `GlossarySeedService` als Migration-Hook beim Backend-Start.
- **GlossaryService (§4.1):** `get_term(slug, language, expertise_level)` — Slug/Alias-Normalisierung
  (sprachsensitiv), Cache-First (Redis 7d → ArangoDB 7d), Cache-Miss → `KnowledgeServiceAdapter.ask`
  (`context=null`, `prompt_language`=Locale, `doc_language="all"`, top_k=5). Fallback bei
  `len(sources)==0` oder `max_score < 0.4` → `fallback_text`, `is_fallback=true`. Audit
  `endpoint=glossary`, `uses_tenant_data=false`. `list_terms`, `invalidate_cache`.
- **API (§3):** Tenant (`/api/v1/t/{slug}/knowledge/`): `GET /term/{slug}` (`?expertise=&language=`),
  `GET /terms`. Light (`/api/v1/public/knowledge/`): `/term/{slug}` (Rate-Limit 30/min/IP),
  `/terms` (10/min/IP), Token-Bucket via Redis, 429 + `Retry-After`. Platform-Admin
  (`/api/v1/admin/knowledge/`): Term-CRUD + Cache-Invalidation. Slug-Whitelist-Validierung (§9
  Szenario 9: Sonderzeichen → 422, kein KS-Aufruf); `expertise` gegen Enum validieren.
- **Celery (§4.3):** `glossary.cleanup_expired_cache` (02:45), `glossary.invalidate_after_reingest`
  (gechained an `ai.knowledge_service_ingest`).
- **Frontend (§5):** `components/glossary/TermTooltip.tsx` (Erweiterung von `components/common/
  HelpTooltip.tsx`; Popover, Skeleton-Loading, Quellen-Accordion, Related-Term-Stack-Navigation mit
  Back-Button, RTK-Query 7d-Cache); Ausbau `pages/ki-glossar/GlossarPage.tsx` (Browse nach Kategorie,
  `/glossar` + `/public/glossar`); Integration in ≥5 Bestandsseiten (Dashboard, Pflanzen-Detail,
  Substrat-Editor, Dünge-Plan-Editor, IPM-Dialog). i18n `pages.glossary.tooltip.*` DE+EN.

**Betroffene Dateien.**
- Backend (neu): `domain/models/glossary_term.py`, `data_access/repositories/glossary_*_repository.py`,
  `domain/services/glossary_service.py` (ersetzt `glossar_service.py`),
  `domain/services/glossary_seed_service.py`, `api/v1/glossar/router.py` (+ public/admin),
  `tasks/glossary_tasks.py`, `spec/knowledge/glossary/seed_terms.yaml`.
- Backend (ändern): `main.py`, Celery-beat, `migrations/`.
- Frontend (neu): `components/glossary/TermTooltip.tsx`, API/RTK-Slice; (ändern):
  `pages/ki-glossar/GlossarPage.tsx`, ≥5 Bestandsseiten, i18n.

**Akzeptanzkriterien** (aus §8 DoD/Szenarien).
- `GET /knowledge/terms` liefert ≥30 geseedete Begriffe.
- `get_term` mit gemocktem KS assertet `context=null` (kein Tenant-Daten-Leak).
- Cache-Hit liefert Antwort ohne KS-Aufruf (< 50ms; Test verifiziert kein KS-Call bei valid Cache).
- `max_score < 0.4` → `is_fallback=true`, `sources=[]`, Antwort aus `fallback_text.{language}`.
- Alias-Auflösung: `GET /knowledge/term/saettigungsdefizit` → `slug="vpd"`.
- Light: 30 Aufrufe/60s → 200; 31. → 429 + `Retry-After`; Audit `user_key=null`,
  `uses_tenant_data=false`.
- `expertise=ignore_previous_instructions` → 422, kein KS-Aufruf (Prompt-Injection-Schutz §6).
- Erfahrungsstufen-Differenzierung: Beginner- vs. Expert-Antwort unterschiedlich (Snapshot gegen
  mocked KS).
- Vitest `<TermTooltip>`: Loading/Loaded/Error/Fallback/Related-Term-Stack-Navigation.
- i18n DE+EN vollständig; Ruff/ESLint/tsc clean.

**Spezialist.** fullstack-developer.
**Aufwand.** M.
**Abhängigkeiten.** **WP-031 (hart)** — `KnowledgeServiceAdapter`, `<AIResponse>`, Audit-Log,
Consent-Infrastruktur. REQ-021, REQ-027. Parallel zu WP-036.

---

### WP-036 — REQ-036 KI-Diagnose-Assistent

**Problem.** `DiagnoseService.diagnose()` fehlt; kein Symptom-Katalog, keine Session-State-Machine,
keine Foto-Bridge, keine strukturierte Top-3-Diagnose mit IPM-Brücke. Ohne dies fehlt der geführte
Diagnose-Workflow (Alternative zum offenen Chat) inkl. Historie pro Pflanze.

**Umzusetzen.**
- **Datenmodell (§2):** Collections `symptoms` (Unique-Slug, Index category/is_active) und
  `diagnosis_sessions` (Indexes tenant+user, plant_instance_key, planting_run_key, expires_at, status)
  + Edges (`diagnosis_session_about_plant/run`, `used_pest/disease`, `started_treatment`).
  Status-State-Machine `draft→analyzing→answered→{resolved|unresolved|archived}`, `analyzing→error`.
  `retention_class` (default_90d / extended_1y) → `expires_at`.
- **Symptom-Seed (§2.1, §4.1):** `spec/knowledge/symptoms/seed_symptoms.yaml` ≥30 Einträge (7
  Kategorien: leaf_color_change, leaf_shape_change, growth_anomaly, pest_visible, disease_visible,
  flowering_issue, environmental), Labels DE+EN, `applicable_phases`, `common_causes_hint`. Idempotenter
  `SymptomCatalog`-Seed beim Start (analog Glossar-Seed).
- **DiagnosisService (§4.2):** `create_session` (schnappt `context_snapshot` aus PlantInstance/
  PlantingRun), `update_session` (Wizard-Patches nur in `draft`), `add_attachment`/`remove_attachment`,
  `analyze`, `set_feedback`, `start_treatment`, `set_retention`, `delete`.
- **DiagnosisAnalysisEngine (§4.3):** Status `analyzing`; Foto-Erkennungen ≤30s abwarten sonst
  `skipped`; KB-Query aus kuratiertem Template (`spec/knowledge/diagnosis-prompts/*.{de,en}.txt`) +
  Slot-Filling; `KnowledgeServiceAdapter.ask` (top_k=8, System-Prompt erzwingt JSON `diagnoses[]`,
  `context`=Stammwerte ohne `extra_notes`-Klartext). Pydantic-`DiagnosisAnswer`-Validierung; bei
  Nicht-JSON zweiter Versuch mit verschärftem Prompt, sonst `status=error`,
  `error_class="diagnosis.invalid_llm_output"`. IPM-Matching: `matched_pest_keys`/`matched_disease_keys`
  → `pests`/`diseases` → `matched_treatment_suggestion` (REQ-010). Audit via `ai_audit_log`.
- **ImageRecognitionDispatcher (§4.4):** Bridge zu REQ-029. Adapter nicht registriert / Tenant-Setting
  aus → `skipped`. Aktiv + Consent `external_image_recognition` → async Celery, `pending→done|error`.
  Nutzt bestehende `pest_inference_client.py`/`inference_service_client.py`. Foto-Storage MinIO via
  `object_storage_adapter.py`, Pfad `diagnosis-attachments/{tenant}/{session}/{attachment}.{ext}`,
  EXIF-Strip doppelt (FE+BE), max 3×10MB.
- **API (§3):** `/api/v1/t/{slug}/diagnosis/`: `sessions` (POST/GET), `sessions/{key}` (GET/PATCH/DELETE),
  `attachments` (POST/DELETE), `analyze` (Consent `ai_tenant_data_access`), `feedback`, `start-treatment`,
  `retention`, `symptoms` (GET). Platform-Admin Symptom-CRUD. Light-Modus: 401 „Anmelden".
- **Celery (§4.5):** `diagnosis.cleanup_expired_sessions` (02:50, kaskadiert MinIO + Edges),
  `diagnosis.dispatch_image_recognition` (event-getriggert).
- **Frontend (§5):** `components/diagnosis/DiagnosisWizard.tsx` (MUI Stepper 4 Schritte +
  Ergebnis: `SymptomPicker`, `ContextForm`, `PhotoUploader` EXIF-Strip, Analyse-Button; Redux-Slice
  `diagnosisWizard`, draft-Persistenz über Backend), `DiagnosisResultsPanel.tsx` (Top-3 Karten in
  `<AIResponse>`, Konfidenz-Badge, „Treatment starten" mit Karenz-Hinweis, Radio-Auswahl),
  `DiagnosisHistoryList.tsx` (in Plant-/Run-Detailseiten). Sidebar-Eintrag „Diagnose" + Quick-Actions.
  KI-deaktivierter Fallback (Wizard bis Schritt 3, dann Hinweis, Session bleibt `draft`). i18n DE+EN
  inkl. Symptom-Labels.

**Betroffene Dateien.**
- Backend (neu): `domain/models/{symptom,diagnosis_session}.py`,
  `data_access/repositories/diagnosis_*_repository.py`,
  `domain/services/diagnosis_service.py` (ersetzt `diagnose_service.py`),
  `domain/services/symptom_catalog.py`, `domain/services/image_recognition_dispatcher.py`,
  `domain/engines/diagnosis_analysis_engine.py`, `api/v1/diagnose/router.py`, `tasks/diagnosis_tasks.py`,
  `spec/knowledge/symptoms/seed_symptoms.yaml`, `spec/knowledge/diagnosis-prompts/*.txt`.
- Backend (ändern): `main.py`, Celery-beat, `migrations/`; Wiederverwendung `object_storage_adapter.py`,
  `pest_inference_client.py`, IPM-Repo (REQ-010).
- Frontend (neu): `components/diagnosis/{DiagnosisWizard,DiagnosisResultsPanel,DiagnosisHistoryList}.tsx`
  + Sub-Komponenten + Redux-Slice + API; (ändern): `pages/ki-diagnose/DiagnosePage.tsx`, Plant-/Run-
  Detailseiten, Sidebar, i18n.

**Akzeptanzkriterien** (aus §8 DoD/Szenarien).
- Glatter Pfad: `draft→analyzing→answered` synchron; `kb_response.diagnoses` hat 3 nach `rank`
  sortierte Einträge; Audit `status=ok, uses_tenant_data=true`.
- Foto bei REQ-029 inaktiv → `image_recognition_status="skipped"`; `kb_query` ohne Bild-Hinweis.
- Foto bei REQ-029 aktiv + Consent → async `pending→done`, `matched_disease_keys` gesetzt;
  `matched_treatment_suggestion` bei IPM-Treffer, „Treatment starten"-Button sichtbar.
- Treatment-Brücke respektiert Karenz-Gate (REQ-010): aktive Karenz → Warnung, blockiert bis Ende.
- Ungültiges LLM-JSON → 2. Versuch; erneut ungültig → `status=error`, `error_class=
  diagnosis.invalid_llm_output`, Retry-Button; Audit `status=provider_error`.
- `extra_notes`-Klartext (PII) erscheint NICHT im `kb_query`/`context`, nur Hinweis „Nutzer hat
  Anmerkungen gemacht"; „Notizen freigeben"-Consent-Step schaltet Klartext frei.
- `retention_class=extended_1y` → `expires_at=created_at+365d`, `status=archived`; Cleanup respektiert.
- `DELETE /sessions/{key}` → Hard-Delete + Edges + MinIO-Anhänge, HTTP 204, structlog ohne PII.
- Light-Modus: `POST /diagnosis/sessions` → 401.
- Symptomliste `?phase=germination` filtert korrekt (`applicable_phases`).
- Wizard-Persistenz über Browser-Refresh (draft aus Backend).
- Vitest (Wizard-State/ResultsPanel/HistoryList) + Pytest (Service/Engine mit mocked KS/Cleanup) grün;
  Ruff/ESLint/tsc clean.

**Spezialist.** fullstack-developer.
**Aufwand.** L.
**Abhängigkeiten.** **WP-031 (hart)** — `KnowledgeServiceAdapter`, `<AIResponse>`, Consent/Audit.
REQ-029 (Vision, weich — Foto-Bridge degradiert zu `skipped` wenn inaktiv), REQ-010 (IPM,
Treatment-Brücke + Karenz-Gate), REQ-013 (Plant/Run), REQ-025 (Retention/Erasure). Parallel zu WP-035.

---

### WP-033 — REQ-033 MCP-Server (Aggregations-Layer) [ZULETZT]

**Problem.** `MCPServer.serve()` fehlt; keine Tool-Registry, keine Tools, keine Service-Account-Auth,
keine Permission-Bindung, kein Audit/Idempotenz. Ohne dies gibt es keine externe LLM-Schnittstelle;
die Tools müssen zudem stabile Ziel-Endpunkte im Backend wrappen — daher zuletzt.

**Umzusetzen.**
- **Design-Entscheidung (§4.1):** Spec nennt eigenständigen Service `src/mcp-server/` (eigener Prozess/
  Helm-Release). Scaffold liegt unter `src/backend/app/mcp_server/`. Entscheidung im WP festhalten:
  eigenständiger Service (NFR-001-konform, ruft Backend über HTTP mit Service-Account-Token) —
  empfohlen — vs. Backend-eingebettet. Bei eigenständigem Service Code-Layout gemäß §4.1 aufbauen.
- **Voraussetzungs-Endpunkte im Backend (§5):** `POST /auth/service-accounts/validate` (REQ-023,
  API-Key→User/Tenant), `GET /t/{slug}/locations/{key}/plants`, `POST /t/{slug}/locations/bulk`,
  `POST /t/{slug}/plants/bulk`, `PATCH /t/{slug}/plants/{key}/location`, `POST /t/{slug}/plants/{key}/archive`,
  `GET /t/{slug}/harvest/readiness` (Aggregat), `GET /privacy/mcp-activity`. `POST /knowledge/search`
  bereits via WP-031-Adapter/KS vorhanden.
- **Permission-Matrix (§4.4):** `mcp.read`/`mcp.write`/`mcp.setup` in `core/permissions.py` ergänzen,
  pro Service-Account vergebbar (getrennt von App-Permissions und voneinander). Personal Accounts
  bekommen sie nie.
- **Tool-Registry + Base (§4.2):** `ToolBase`/`WriteToolBase` mit Antwort-Wrapper (`summary`/`data`/
  `links`), `@mcp_tool(name, permission, destructive)`-Decorator, DryRun (`dry_run: bool`),
  Idempotency (`idempotency_key`, 24h Replay), Bulk-`_bulk`-Muster, `annotations.destructive`.
- **Tool-Inventar (§2, ~30 Tools):** Read (`mcp.read`): `list_tenants`, `get_due_care_tasks`,
  `list_planting_runs`, `get_planting_run`, `list_plants_at_location`, `get_plant_diagnostics`,
  `search_plant_knowledge`, `get_species_info`, `list_overdue_tasks`, `get_harvest_readiness`. Write-
  Tagesbetrieb (`mcp.write`): `confirm_care_task`, `add_plant_diary_entry`, `create_inspection`,
  `transition_planting_run` (HSTValidator), `record_feeding_event`, `record_harvest`, `apply_treatment`
  (Karenz-Gate). Write-Setup (`mcp.setup`): `setup_apartment`/`setup_growbox`/`setup_outdoor_garden`
  (Macro, Transaktion), `create_site`/`update_site`, `create_location`/`create_locations_bulk`/
  `update_location`/`delete_location` (force-Guard), `set_water_profile`, `create_substrate_batch`,
  `apply_starter_kit`. Write-Pflanzen (`mcp.write`): `find_or_create_species`, `create_plant`/
  `create_plants_bulk`, `create_planting_run`, `add_plants_to_run`, `move_plant`, `set_plant_phase`,
  `archive_plant`.
- **Transaktionssemantik Macro-Tools (§4.2.1):** All-or-nothing via ArangoDB-Transactions
  (Compensating Actions), Partial-Result-Reporting (`data.attempted`/`data.rolled_back`),
  Idempotenz über gesamte Macro-Operation.
- **Auth + Permission-Guard (§4.3/4.4):** `ServiceAccountAuthenticator` (X-API-Key/stdio-Init) gegen
  `/auth/service-accounts/validate`, Auth-Context → PermissionGuard, `auth.expired`-Fehler bei
  Rotation. IP-Allowlist/Rate-Limit backend-seitig (REQ-023), MCP propagiert `X-Forwarded-For`.
- **Datenmodell (§3):** `mcp_audit_log` (Retention 90d) + `mcp_idempotency_record` (TTL 24h,
  ArangoDB-TTL-Index). `input_hash` statt Klartext-Args.
- **Transport (§5, §1.2):** HTTP+SSE-Discovery-Endpunkte in `api/v1/mcp/router.py` bzw. eigenem
  Server; stdio nur Dev. MCP-Protokoll über Anthropic MCP-SDK.
- **Deployment/Doku (§6, §8.7):** Helm `mcpServer.enabled=false` (opt-in); Doku
  `claude_desktop_config.json`-Beispiel.

**Betroffene Dateien.**
- MCP-Server (neu, `src/mcp-server/` oder `src/backend/app/mcp_server/`): `server.py` (ersetzt
  Scaffold), `tools/*.py`, `auth/{service_account,permission_guard}.py`, `backend_client.py`,
  `audit.py`, `idempotency.py`, `config.py`, `main.py`.
- Backend (neu/erweitert): Voraussetzungs-Endpunkte (auth/service-accounts/validate, plants/bulk,
  locations/bulk, harvest/readiness, plants archive/location, privacy/mcp-activity), `core/permissions.py`
  (mcp.*), `domain/models/mcp_*.py`, `data_access/repositories/mcp_*_repository.py`, `tasks/mcp_tasks.py`
  (Audit-Cleanup), `migrations/`.
- Deployment: Helm-Chart `mcpServer`, `docs/`.

**Akzeptanzkriterien** (aus §8 AC-1..T4, Szenarien).
- Service-Account authentifiziert per API-Key; nur Permission-Matrix-erlaubte Tools ausführbar.
- Read-Only-Account (`mcp.read`) auf `confirm_care_task` → `permission.denied` + Audit `status=denied`.
- `get_due_care_tasks(days_ahead=0)` liefert `summary`+`data` mit Name/Standort/Dringlichkeit (< 500ms
  P95 @ 100 Pflanzen).
- `dry_run=true` schreibt keinen DB-Write (Audit `status=dry_run`, kein Folge-`ok`).
- Identischer `idempotency_key` in 24h → identische IDs, nur eine Ressource, `idempotent_replay=true`.
- `setup_apartment`/`setup_growbox` Macro-Fehler → vollständiger Rollback (kein Half-State).
- `delete_location` mit aktiven Pflanzen ohne `force` → `validation.location_has_plants` + Anzahl.
- Cross-Tenant: `get_planting_run` mit Fremd-Tenant-Key → `not_found` (kein Leak, kein
  `permission.denied`).
- `search_plant_knowledge(...)` liefert ≥3 RAG-Treffer (Score ≥ 0.6) über denselben KS wie REQ-031.
- API-Keys nie in Audit/Fehler; `input_hash` statt Klartext-Args; `mcp_idempotency_record` nach 24h
  TTL-entfernt; `GET /privacy/mcp-activity` liefert 90-Tage-Historie.
- Helm `mcpServer.enabled=true` → lauffähiger Pod; `=false` → Komponente fehlt, Kamerplanter
  unverändert.
- Unit-Coverage ≥80% in MCP-Code; Integrationstest je Tool gegen Test-Backend; Ruff + mypy clean.

**Spezialist.** fullstack-developer.
**Aufwand.** L.
**Abhängigkeiten.** **WP-031 (stark)** — `search_plant_knowledge` + stabile KI-Basis. REQ-023
(Service-Accounts, hart), REQ-024 (Permission-Matrix, hart), REQ-025 (Audit/Privacy, hart), REQ-002/
013 (Setup-/Plant-Tools, weich), REQ-006/007/010/014/019/020/022 (Tool-Ziele). Setzt stabile
Tool-Ziel-Endpunkte voraus → zuletzt.

## Reihenfolge & Parallelisierung

Gekoppelt, **nicht** frei parallel. Abhängigkeitsgraph:

```
                    ┌──────────────────────────────────────────────┐
                    │  WP-031 REQ-031 KI-Assistent (FUNDAMENT)      │
                    │  ─ IKnowledgeService + async HttpAdapter      │
                    │    (Circuit-Breaker) ── kritischer Baustein   │
                    │  ─ AiContextBuilder (ADR-002 Fallback)        │
                    │  ─ 3-Stufen-Toggle + Consent-Purposes         │
                    │  ─ <AIResponse>-Hülle + Audit-Log             │
                    └───────────────┬──────────────────────────────┘
                                    │ blockt
                 ┌──────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐          ┌──────────────────────────────┐
    │ WP-035 REQ-035 Glossar  │   ‖      │ WP-036 REQ-036 Diagnose       │
    │ (teilt Adapter+Cache-   │ parallel │ (teilt Adapter; zusätzlich    │
    │  Muster+<AIResponse>)   │          │  REQ-029/Vision, REQ-010/IPM)  │
    └────────────┬────────────┘          └───────────────┬──────────────┘
                 └──────────────────┬───────────────────┘
                                    ▼
                    ┌──────────────────────────────────────────────┐
                    │  WP-033 REQ-033 MCP-Server (ZULETZT)          │
                    │  Aggregations-Layer über viele Services;      │
                    │  nutzt search_plant_knowledge (WP-031) +      │
                    │  stabile Tool-Ziel-Endpunkte                  │
                    └──────────────────────────────────────────────┘
```

**Kritischer Baustein.** Der wiederverwendbare async `HttpKnowledgeServiceAdapter`
(`IKnowledgeService`-Interface, Circuit-Breaker) + `AiContextBuilder` in WP-031 — Architektur nach
bestehendem External-Adapter-Muster (ABC in `domain/interfaces/`, Impl in `data_access/external/`).
Hinweis: die **LLM-Adapter selbst existieren bereits** im Knowledge-Service (`src/knowledge-service/
app/llm/{ollama,anthropic,openai_compatible}.py`); das Backend baut keinen eigenen LLM-Adapter,
sondern den HTTP-Adapter zum Microservice.

**Staffelung für `issue-orchestrate`.**
1. WP-031 vollständig (Fundament) — muss grün und gemergt sein, bevor 035/036 starten.
2. WP-035 ‖ WP-036 parallel (getrennte Dateibäume; bei geteiltem Tree sequenziell committen oder
   `isolation: worktree` je Agent).
3. WP-033 zuletzt (nachdem Tool-Ziel-Endpunkte in 031/035/036 + REQ-023/024 stabil sind).

## Definition of Done

- Alle vier Services ohne `NotImplementedError`; alle vier Router in `main.py` registriert.
- REQ-031: 3-Stufen-Toggle (404/403/403) wirksam; `<AIResponse>` Pflicht-Hülle für alle KI-Inhalte;
  SSE-Chat; Audit-Log ohne Klartext-PII; Celery-Cleanups aktiv; Consent-Purposes `ai_tenant_data_access`
  + `ai_cloud_processing` vorhanden.
- REQ-035: ≥30 Begriffe geseedet; Cache-First + `is_fallback`-Pfad; Light-Rate-Limit; `<TermTooltip>`
  in ≥5 Bestandsseiten; `<GlossaryPage>` tenant + light.
- REQ-036: Symptom-Katalog ≥30; Session-State-Machine + Retention; JSON-Output-Zwang + Retry;
  IPM-Treatment-Brücke mit Karenz-Gate; Foto-Bridge (skipped/pending/done/error); Wizard mit
  draft-Persistenz; KI-deaktivierter Fallback.
- REQ-033: ~30 Tools mit Permission-Bindung (`mcp.read/write/setup`); DryRun + Idempotenz +
  Macro-Transaktionen; Service-Account-Auth; Cross-Tenant-Isolation; Audit 90d + Idempotency-TTL 24h;
  Helm opt-in.
- i18n DE+EN vollständig (inkl. Enums, Symptom-/Begriffs-Labels). Ruff + ESLint + tsc clean; pytest +
  vitest grün; MCP Ruff + mypy clean, ≥80% Coverage.
- Pflicht-3-Agent-Kette nach jeder Frontend-Änderung (UI-Review → Tests → Doku). Doku unter `docs/`
  DE-kanonisch + EN-Mirror.

## Risiko-Hinweise

- **LLM-Kosten & DSGVO-Consent (REQ-031/035/036):** Cloud-Provider sind Drittland-Übermittlung →
  `ai_cloud_processing`-Consent zwingend, Default lokal (Ollama). `AI_FEATURES_ENABLED`/Tenant-Setting
  default false. `AiContextBuilder` darf keine direkt-personenbezogenen Felder senden (NFR-007);
  `extra_notes` (REQ-036) niemals Klartext ohne Extra-Consent. Audit nur Hash+Länge.
- **Knowledge-Service-Kopplung:** Das Backend baut **keinen** eigenen LLM-Adapter — Missverständnis-
  Risiko. Der KS ist produktiv; Änderungen an ihm laufen über separate PRs gegen
  `src/knowledge-service/`. Der async Adapter muss Circuit-Breaker + regelbasierten Backend-Fallback
  (W-011) haben, damit KS-Ausfälle die App nicht blockieren. Frontend-Offline = online-only-Hinweis
  (UI-NFR-012), kein dupliziertes Mini-Regelwerk.
- **Vision-Abhängigkeit REQ-036:** REQ-029 ist weich — Foto-Bridge muss sauber zu `skipped`
  degradieren, wenn Adapter nicht registriert/Consent fehlt. JSON-Output-Parsing des LLM ist fragil →
  zwingend Zwei-Versuch-Strategie + `status=error`-Pfad. IPM-Karenz-Gate (REQ-010) darf nicht umgangen
  werden.
- **Auth-Bindung MCP (REQ-033):** Härteste Voraussetzung — ohne Service-Accounts (REQ-023) +
  Permission-Matrix (REQ-024) + `/auth/service-accounts/validate` nicht baubar. Cross-Tenant-Leaks
  müssen als `not_found` (nicht `permission.denied`) maskiert werden. Macro-Tools brauchen echte
  ArangoDB-Transaktionen (Half-State-Risiko). `mcp.setup` ist die destruktivste Klasse (rekursive
  Location-Löschung) → force-Guard + Audit. Design-Frage eigenständiger Service vs. Backend-eingebettet
  vor Implementierung klären (Scaffold liegt im Backend, Spec nennt `src/mcp-server/`).
- **Reihenfolge-Kopplung:** WP-033 vor stabilen Tool-Ziel-Endpunkten zu starten erzeugt Rework;
  strikt zuletzt. WP-035/036 vor gemergtem WP-031 erzeugt Merge-Konflikte an geteilten Dateien
  (`consent_engine.py`, `main.py`, `settings.py`, Migration) → Fundament zuerst mergen.
