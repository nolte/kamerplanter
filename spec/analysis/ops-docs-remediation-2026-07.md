# Operations/Config Docs Audit & Remediation (2026-07)

**Issue:** #596 — central feature→config→resource matrix, reconcile ops docs vs code
**Scope:** `docs/{de,en}/deployment/betriebsprofile.md`, `docs/{de,en}/reference/environment-variables.md`, new `docs/{de,en}/deployment/konfigurationsmatrix.md`, `mkdocs.yml` nav
**Ground truth used:** `src/backend/app/config/settings.py`, `helm/kamerplanter/values.yaml` (+ `values-dev-ki.yaml`, `values-dev-recognition.yaml`), `.env.example`, `docker-compose.yml`, `src/knowledge-service/app/config.py` + `app/auth.py`, `src/inference-service/app/config.py` + `app/auth.py`, `src/backend/app/main.py` (`insecure_default_secrets`)

This is a remediation record for traceability (DOCS.md §1.1 item 4) — findings were fixed directly in the docs, not just reported.

---

## Central deliverable

New page **Konfigurationsmatrix / Configuration Matrix** (`docs/{de,en}/deployment/konfigurationsmatrix.md`), linked from `betriebsprofile.md`, `environment-variables.md`, and `mkdocs.yml` nav (between "Betriebsprofile" and "Kubernetes").

Covers, as per-feature rows with the six required columns (Funktion, benötigte Dienste, Aktivierung/Deaktivierung, Pflicht-Secrets, Ressourcenauswirkung, Startup-Gate):

- Pflanzenidentifikation (REQ-029 / REQ-029-A / REQ-048) — 5 rows
- Schädlingserkennung (REQ-044) — 5 rows
- CV-Krankheitsdiagnose (REQ-038) — 2 rows
- KI-Assistent + Knowledge Service + Sprachmodell-Provider (REQ-031 / REQ-035 / REQ-036) — 8 rows
- MCP-Server (REQ-033) — 1 row
- Wetter / Frost / Klimanormalen / ET₀ / Saison-Automatik (REQ-046 / REQ-041 / REQ-039 / REQ-037 / REQ-047) — 10 rows
- Sensorik & Zeitreihendaten (REQ-005) — 3 rows
- Umgebungssteuerung & Aktorik (REQ-018) — 3 rows
- Benachrichtigungssystem (REQ-030) — 6 rows
- InvenTree-Integration (REQ-016) — 2 rows
- Object Storage / Pflanzenfoto-Galerie (NFR-013 / REQ-034) — 4 rows
- Datenschutz, Multi-Tenancy, Betriebsmodus (REQ-023 / REQ-024 / REQ-025 / REQ-027) — 5 rows
- Externe Stammdatenanreicherung (REQ-011) — 3 rows
- mDNS/Zeroconf — 1 row
- plus a compact "Kern-Funktionen ohne eigenen Betreiber-Schalter" table listing the remaining ~19 REQs (001–004, 006–010, 012–015, 017, 019–022, 026, 028, 032, 042, 045, 048) that have no operator toggle at all

Total: **~40 REQ-IDs represented** (either with a detailed per-feature row, or explicitly listed as "no operator switch" — nothing silently omitted). Two REQs (REQ-040 OpenFarm/Growstuff enrichment, REQ-043 holistic health assessment) are flagged `!!! warning "Noch nicht implementiert"` since their spec status is "Entwurf" and no code/config exists to document.

Also added: a "Pflicht-Secrets je aktivierter Funktion" section consolidating all three processes' startup-gate checks (`src/backend/app/main.py::insecure_default_secrets`, `src/knowledge-service/app/auth.py::check_insecure_config`, `src/inference-service/app/auth.py::check_insecure_config`), and a "Zwei getrennte Ebenen" section explicitly delimiting operator env-gates from per-user `module_visibility` (REQ-021/042), with a Mermaid diagram.

---

## Seed defects A–I — disposition

| # | Defect | Status | Where fixed |
|---|---|---|---|
| A | `betriebsprofile.md` configured the AI assistant via non-existent `AI_DEFAULT_PROVIDER`/`AI_OLLAMA_URL`/`AI_OLLAMA_MODEL`/`AI_FALLBACK_PROVIDER`/`AI_OPENAI_*` | **Fixed** | All 5 profile example configs rewritten to use `AI_FEATURES_ENABLED` + `KNOWLEDGE_SERVICE_ENABLED`/`KNOWLEDGE_SERVICE_URL` (backend) and `LLM_PROVIDER`/`LLM_API_URL`/`LLM_API_KEY`/`LLM_MODEL` (Knowledge Service). Component-overview and decision tables corrected the same way. `betriebsprofile.md` DE+EN |
| B | `VECTORDB_ENABLED` documented as a backend feature switch | **Fixed** | Explicit `!!! warning` added in "Eigenes Profil zusammenstellen" clarifying it is a docker-compose-only profile flag with no effect on the backend; real switches (`INFERENCE_SERVICE_ENABLED`, `KNOWLEDGE_SERVICE_ENABLED`) documented instead. `betriebsprofile.md` DE+EN |
| C | Value drift: `IDENTIFICATION_MAX_IMAGE_SIZE_MB` doc=10/code=5; `IDENTIFICATION_RATE_LIMIT_PER_USER_DAY` doc=0/code=50 | **Fixed** | `environment-variables.md` DE+EN table rows + `.env` example comment corrected to match `settings.py` |
| D | Missing env-vars in the reference (14 named + adjacent ones) | **Fixed** | All 14 explicitly named vars added as proper rows: `ERASURE_TOMBSTONE_SALT`, `PRIVACY_HARD_DELETE_AFTER_DAYS`/`PRIVACY_EXPORT_RETENTION_HOURS`/`PRIVACY_EMAIL_CHANGE_TTL_HOURS`, full `TIMESCALEDB_*` block, `IDENTIFICATION_EXTERNAL_IN_LIGHT_MODE`, `PLANTNET_ENABLED`, `PLANT_ID_API_KEY`(+`_BASE_URL`), `INFERENCE_SERVICE_ENABLED`/`_URL`, `HA_ALLOW_PRIVATE_ENDPOINT`, `PWA_PUSH_ENDPOINT_ALLOWED_HOSTS`, `COOKIE_SECURE`, `APP_BASE_URL`, weather sub-toggles (`OPEN_METEO_ENABLED`/`DWD_ENABLED`/`OPENWEATHERMAP_ENABLED`), `STORAGE_TENANT_QUOTA_MB`, `STORAGE_MAX_PHOTOS_PER_INSTANCE`. Also added adjacent vars discovered missing during verification: `SESSION_TOKEN_EXPIRE_HOURS`, `IDENTIFICATION_HTTP_TIMEOUT`, `IDENTIFICATION_MAX_IMAGE_DIMENSION`, `STORAGE_STRIP_EXIF`, `PRIVACY_DATA_CONTROLLER_NAME`/`_EMAIL`, `WEATHER_DEFAULT_PUBLIC_SOURCE`. `environment-variables.md` DE+EN |
| E | Extend profile/resource coverage to the matrix features | **Fixed** | New Konfigurationsmatrix page (see above); `betriebsprofile.md` profile bundles corrected to include the Knowledge/Embedding/VectorDB trio wherever Ollama is listed (previously inconsistent — Ollama checked, Knowledge Service unchecked) |
| F | Surface concrete `values.yaml` requests/limits per feature | **Fixed** | Every matrix row with a dedicated pod cites the actual `resources.requests`/`resources.limits` from `values.yaml` (`inference-service` 250m/2 CPU · 512Mi/2Gi, `vectordb` 50m/500m · 128Mi/512Mi + 5Gi PVC, `timescaledb` commented-out chart default 250m/1 · 512Mi/1Gi + 10Gi, `backend-attachments` 20Gi PVC). Knowledge/Embedding/Reranker Service have **no** chart defaults in production (no pre-stubbed `enabled` block, unlike vectordb/inference-service) — this asymmetry is called out explicitly, and the cited resource orientation values are sourced from the Skaffold dev overlay `values-dev-ki.yaml` with that caveat stated. Also corrected `betriebsprofile.md`'s Embedding-Service RAM claim (was "512 MB", `values-dev-ki.yaml` shows 1.5–4Gi limit — matches the already-correct Reranker figure) |
| G | Delimit operator env-gates vs. per-user `module_visibility` | **Fixed** | Dedicated "Zwei getrennte Ebenen" / "Two separate on/off layers" section in the matrix, with a Mermaid diagram and an explicit statement that the layers act in series (env-gate first, module-visibility only affects what's already unlocked) |
| H | Central "mandatory secrets per enabled function" overview | **Fixed** | "Pflicht-Secrets je aktivierter Funktion" section; cross-linked from `environment-variables.md`'s new `ERASURE_TOMBSTONE_SALT`/`TIMESCALEDB_PASSWORD` rows |
| I | ADR gap for the deployment-profile / light-full architecture | **Logged, not closed** (as explicitly permitted by the issue) | `!!! note` in the matrix page + `konfigurationsmatrix.md`'s "Offene Architektur-Dokumentation" section; no new ADR authored — follow-up work |

---

## Additional drifts found and fixed during verification (beyond the seed list)

These were discovered while checking every doc claim against code per DOCS.md §9, and are fixed as part of the same remediation:

1. **`betriebsprofile.md` "Ollama + Cloud-Fallback" claim was fictional.** Neither the backend nor the Knowledge Service (`src/knowledge-service/app/config.py`, single `llm_provider` field) has any runtime fallback mechanism between providers — `LLM_PROVIDER` is one configured value. Rewrote the Professional/SaaS profile prose and added an explicit `!!! info "No automatic cloud fallback"` admonition.
2. **`FERNET_KEY` was documented as "Nein" (not required)**, but `insecure_default_secrets()` in `src/backend/app/main.py` checks it unconditionally (`if not settings.fernet_key: insecure.append(...)`), independent of whether OIDC is configured. Corrected to "Ja" with an explanatory note in `environment-variables.md`.
3. **`STORAGE_KEEP_EXIF_<CATEGORY>` does not exist as a real setting.** It only appears as a string inside a code comment/description in `src/backend/app/domain/engines/erasure_engine.py` (`StorageCleanupRule` description text), never as an actual per-category Pydantic field — `settings.py` only has a single global `storage_strip_exif: bool`. Replaced the fictional row with the real `STORAGE_STRIP_EXIF` variable. **Not fixed:** the misleading comment string in `erasure_engine.py` itself is out of this agent's write scope (source code, not docs) — flagged here for a backend follow-up.
4. **`AI_DEFAULT_PROVIDER` values list included `openai` as a bare value.** The Knowledge Service's `LLM_PROVIDER` only accepts `ollama`, `anthropic`, `openai_compatible` — a bare `openai` was never valid even under the old (fictional) naming. Corrected in the "Eigenes Profil zusammenstellen"/"Build Your Own Profile" table and the SaaS example.
5. **Hobby/Standard profile checklists were self-contradictory**: "Ollama (lokales Sprachmodell)" was checked while "Knowledge Service / RAG" was listed as optional/unchecked, even though the backend never talks to Ollama directly (only the Knowledge Service does, via `LLM_PROVIDER`). Fixed by making the Knowledge/Embedding/VectorDB trio a mandatory bundle wherever Ollama is listed, with an explanatory `!!! note`.
6. **`.env.example`-referenced `.env` snippet in `environment-variables.md`** omitted the two other unconditionally required secrets (`FERNET_KEY`, `ERASURE_TOMBSTONE_SALT`) — added alongside `JWT_SECRET_KEY`.

---

## Not remediated (explicitly out of scope for this issue)

- **`docs/{de,en}/architecture/ai-architecture.md`** describes a backend-side `IAiProvider` adapter interface (`OllamaAdapter`, `OpenAiAdapter`, `AnthropicAdapter`, …) at `app/domain/interfaces/ai_provider.py` — this file/class hierarchy **does not exist** in `src/backend/app/`; the actual provider logic lives entirely in the Knowledge Service. This is an architecture-documentation drift, not an operations/config drift, and `docs/architecture/` is not in issue #596's file scope (`docs/{de,en}/deployment/`, `reference/environment-variables.md`, `deployment/{helm,kubernetes,inference-service}.md`, `user-guide/{light-mode,module-visibility}.md`). Flagged here for a follow-up architecture-docs audit.
- **Site-wide German quotation-mark typography** (DOCS.md §10) — not touched, per that section's explicit "own PR, own review" rule.

---

## Verification

- `mkdocs build --strict` (via `.venv-docs/bin/mkdocs build --strict`, after `task docs:venv`/`docs:catalog`/`docs:fact-tables`): **exit 0, no errors**.
- All internal anchor links newly introduced in the touched pages were verified against the actual generated `site/**/index.html` `id=` attributes (not just assumed) — one broken anchor was found and fixed this way (`betriebsprofile.md#komponentenübersicht` → `#komponentenubersicht`, since the default Python-Markdown TOC slugifier strips diacritics via NFKD normalization rather than keeping Unicode word characters).
- DE/EN heading-structure parity checked with a line-by-line diff for `betriebsprofile.md`, `environment-variables.md`, and the new `konfigurationsmatrix.md` — identical count, order, and nesting level in both languages.
