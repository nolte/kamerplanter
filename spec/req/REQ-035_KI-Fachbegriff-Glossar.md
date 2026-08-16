# Spezifikation: REQ-035 - KI-gestuetztes Fachbegriff-Glossar

```yaml
ID: REQ-035
Titel: KI-gestuetztes Fachbegriff-Glossar mit On-Demand-Erklaerungen
Kategorie: KI & Beratung
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Redis, React 19, TypeScript 5.9, MUI 7
Status: Entwurf
Version: 1.1 (Rechte-Vokabular auf REQ-049 §3.1/§3.4 umgestellt)
Abhängigkeit: REQ-021 v1.0 (Erfahrungsstufen), REQ-024 v1.4 (Mandantenverwaltung — fuer optionalen Tenant-Kontext), REQ-027 v1.2 (Light-Modus), REQ-031 v2.0 (KI-Assistent / Knowledge Service)
Wird benoetigt von: —
```

## Versionshistorie

| Version | Datum | Aenderung |
|---------|-------|-----------|
| 1.0 | 2026-04-25 | Initialer Entwurf — auf Basis Knowledge-Service-Realität (REQ-031 v2.0) |

## 1. Business Case

**User Story (Casual User — Fachbegriff im Tooltip):** "Als Zimmerpflanzen-Besitzer ohne Fachkenntnisse moechte ich neben Begriffen wie 'VPD', 'EC' oder 'Karenzzeit' ein kleines Fragezeichen sehen, das ich antippen kann, um in 1-2 Saetzen zu erfahren, was das ist und warum es wichtig ist — damit ich die App benutzen kann, ohne ein Fachwoerterbuch danebenzulegen."

**User Story (Beginner — Lernpfad):** "Als Anfaenger moechte ich, wenn ich in einer Erklaerung weitere Fachbegriffe finde, diese ebenfalls antippen koennen — damit ich mich von Begriff zu Begriff weiterhangeln kann, statt frustriert die App zu verlassen."

**User Story (Expert — Schnellnachschlage):** "Als erfahrener Nutzer moechte ich denselben Tooltip-Mechanismus nutzen koennen, aber technisch praeziser — z. B. konkrete Wertebereiche fuer VPD pro Phase — damit ich auch unterwegs Werte nachschlagen kann, ohne mich durch Beginner-Texte zu klicken."

**User Story (Light-Modus-Nutzer):** "Als anonymer Light-Modus-Nutzer moechte ich das Glossar ohne Login benutzen koennen — damit ich die Begriffswelt der App verstehen kann, bevor ich mich registriere."

**User Story (Konsistenz im Team-Tenant):** "Als Tenant-Admin eines Gemeinschaftsgartens moechte ich, dass alle Mitglieder dieselben Begriffsdefinitionen sehen — damit Diskussionen sich auf dieselbe Wortbasis stuetzen, statt jeder seine eigene Interpretation zu haben."

**Beschreibung:**

REQ-035 fuehrt ein **kuratiertes Glossar** mit ca. 30 Kerntermen ein, ergaenzt um eine **RAG-gestuetzte On-Demand-Erklaerung** ueber den bestehenden Knowledge Service (REQ-031 v2.0). Die Erklaerung wird auf die Erfahrungsstufe des Nutzers angepasst (Beginner / Intermediate / Expert) und ist im Light-Modus ohne Login verfuegbar.

Sichtbarer Mechanismus ist eine bestehende Frontend-Komponente `<HelpTooltip>`, die zu `<TermTooltip>` erweitert wird: Klick auf das Fragezeichen-Icon neben einem Begriff oeffnet ein kompaktes Popover mit der Erklaerung; Verlinkungen zu verwandten Begriffen sind klickbar und oeffnen den naechsten Tooltip.

**Grundprinzipien:**

- **Kuratiertes Skelett, KI-Tiefe:** Liste der Begriffe wird redaktionell gefuehrt (Synonym-Mapping, Alias-Aufloesung, Kategorie-Zuordnung). Der Erklaerungstext kommt vom Knowledge Service (RAG ueber `spec/knowledge/rag/`).
- **Erfahrungsstufen-Variante:** Pro Begriff wird der Knowledge Service mit explizitem `expertise_level`-Hinweis im Prompt aufgerufen. Beginner bekommen Alltagssprache, Expert bekommen Fachsprache mit Wertebereichen.
- **Caching:** Glossar-Antworten sind quasi-statisch und werden 7 Tage gecacht (Redis + ArangoDB).
- **Light-Modus-faehig:** Glossar ist Wissensvermittlung ohne Personenbezug. Es geht nicht durch die Tenant-Auth-Kette und braucht keinen Consent.
- **Multilingual-Vorbereitung:** Begriffe haben Alias-Listen pro Sprache (`label_de`, `label_en`, `aliases_de`, `aliases_en`). Auflosung von Alias zu kanonischem Slug ist sprachsensitiv. Antwort kommt in User-Locale.
- **Foundation fuer andere Features:** Begriffe-Slugs werden auch von REQ-006 (Aufgaben), REQ-022 (Pflegeerinnerungen) und REQ-009 (Dashboard) verwendet, damit ueberall dieselben Definitionen erscheinen.
- **Keine LLM-Halluzinationen:** Wenn der Knowledge Service zu einem Begriff keine ausreichenden Treffer (Score < 0.4) findet, liefert das Glossar einen redaktionellen Fallback-Text und kennzeichnet die Antwort als "Kurzdefinition (kein KB-Treffer)".

### 1.1 Abgrenzung zu benachbarten REQs

| REQ | Beziehung |
|-----|-----------|
| **REQ-031** v2.0 | Foundation. Glossar nutzt Knowledge Service via `KnowledgeServiceAdapter`. Antwortstruktur folgt `<AIResponse>`. |
| **REQ-027** Light-Modus | Glossar-Endpoints sind ohne Login erreichbar (`/api/v1/public/knowledge/term/{slug}`). |
| **REQ-021** Erfahrungsstufen | Antworten werden pro Stufe variiert. Im Light-Modus default Beginner. |
| **REQ-036** Diagnose-Assistent | Kann auf Glossar-Tooltips fuer Symptom-Bezeichnungen zurueckgreifen. |
| **REQ-006 / REQ-022 / REQ-009** | Konsumieren Glossar-Slugs in ihren UI-Texten — `<TermTooltip>` ist die universelle Anzeige. |

## 2. Datenmodell (ArangoDB)

### 2.1 Document Collection: `glossary_terms`

```json
{
  "_key": "vpd",
  "slug": "vpd",
  "labels": {
    "de": "VPD",
    "en": "VPD"
  },
  "long_labels": {
    "de": "Vapor Pressure Deficit (Wasserdampfdruck-Defizit)",
    "en": "Vapor Pressure Deficit"
  },
  "aliases": {
    "de": ["Wasserdampfdruck-Defizit", "Saettigungsdefizit"],
    "en": ["vapor pressure deficit", "saturation deficit"]
  },
  "category": "umwelt",
  "default_expertise_level": "beginner",
  "applicable_phases": ["seedling", "vegetative", "flowering"],
  "related_term_slugs": ["luftfeuchte", "blatttemperatur", "transpiration"],
  "fallback_text": {
    "de": "VPD steht fuer 'Wasserdampfdruck-Defizit'. Es beschreibt, wie 'durstig' die Luft ist und beeinflusst, wie schnell deine Pflanze ueber die Blaetter Wasser verliert. Niedrige VPD = feuchte Luft, hohe VPD = trockene Luft. Zielbereiche je Phase 0.8 - 1.5 kPa.",
    "en": "VPD stands for 'Vapor Pressure Deficit' and describes how 'thirsty' the air is, influencing how fast your plant transpires water through its leaves. Low VPD = humid air, high VPD = dry air. Target ranges per phase 0.8 - 1.5 kPa."
  },
  "rag_query_template": "Erklaere den Begriff '{label_de}' fuer einen {expertise_level} Pflanzenfreund. Gib eine 2-3 Satz Definition und einen praxisnahen Hinweis. Falls relevant: Wertebereiche pro Wachstumsphase.",
  "is_active": true,
  "created_at": "2026-04-25T00:00:00Z",
  "updated_at": "2026-04-25T00:00:00Z"
}
```

**Indexes:**
- Persistent Unique auf `slug`
- Persistent auf `category`
- Persistent auf `is_active`

### 2.2 Document Collection: `glossary_term_cache`

Cache-Schicht fuer LLM-Antworten pro Begriff/Sprache/Erfahrungsstufe (analog `ai_tip_cache` aus REQ-031):

```json
{
  "_key": "uuid",
  "term_slug": "vpd",
  "language": "de",
  "expertise_level": "beginner",
  "answer_text": "VPD steht fuer Vapor Pressure Deficit ...",
  "sources": [
    { "source_key": "umwelt/vpd-optimierung#einfuehrung", "source_type": "care_rule", "title": "VPD-Einfuehrung", "score": 0.91, "language": "de" }
  ],
  "language_mismatch_warning": false,
  "model_name": "gemma3:12b",
  "provider_type": "ollama",
  "kb_version": "ks-1.4.2-idx-20260420",
  "is_fallback": false,
  "generated_at": "2026-04-25T10:00:00Z",
  "valid_until": "2026-05-02T10:00:00Z"
}
```

**Indexes:**
- Persistent Unique auf `term_slug + language + expertise_level + kb_version`
- Persistent auf `valid_until` (Cleanup)

Hot-Cache zusaetzlich in Redis: Schluessel `glossary:term:{slug}:{language}:{expertise_level}`, TTL 7 Tage.

### 2.3 Initial-Begriffsliste (v1.0 Pflicht-Set)

Mindestens diese 30 Slugs sind in der ersten Auslieferung enthalten:

| Kategorie | Slugs |
|-----------|-------|
| **umwelt** | vpd, ppfd, dli, photoperiode, hysterese, blatttemperatur, transpiration |
| **duengung** | ec, ph, npk, calmag, ro-wasser, runoff, flush |
| **bewaesserung** | drainage, substrat, frequenz |
| **phasen** | gdd, stretch, topping, fim, lst |
| **outdoor** | mischkultur, fruchtfolge, companion-planting, sukzession, gruenduengung, eisheilige, phaenologie, winterhaerte |
| **ipm** | karenz, karenzzeit |

Begriffsliste wird in `spec/knowledge/glossary/seed_terms.yaml` versioniert und beim Deployment durch ein Seed-Skript geladen.

## 3. Backend-API

### 3.1 Tenant-scoped (`/api/v1/t/{tenant_slug}/knowledge/`)

| Methode | Pfad | Beschreibung | Berechtigung | Consent |
|---------|------|-------------|--------------|---------|
| `GET` | `/term/{slug}` | Erklaerung zu einem Begriff. Query: `?expertise=beginner|intermediate|expert&language=de|en` | Alle Rollen | — (kein Tenant-Daten-Zugriff) |
| `GET` | `/terms` | Liste aller aktiven Begriffe (slug + label + category). Query: `?category=&language=` | Alle Rollen | — |

Diese Endpunkte sind unter Tenant-Pfad erreichbar fuer einheitliches Routing, aber sie nutzen KEINE Tenant-Daten — der Knowledge-Service-Aufruf erfolgt strikt mit `context = null`.

### 3.2 Light-Modus (`/api/v1/public/knowledge/`)

| Methode | Pfad | Beschreibung | Auth | Rate-Limit |
|---------|------|-------------|------|------------|
| `GET` | `/term/{slug}` | wie 3.1, ohne Auth | keine | 30/min pro IP |
| `GET` | `/terms` | wie 3.1, ohne Auth | keine | 10/min pro IP |

Im Light-Modus wird Default-Expertise `beginner` angenommen, Default-Language aus `Accept-Language`-Header (de oder en).

### 3.3 Platform-Admin (`/api/v1/admin/knowledge/`)

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/terms` | Liste mit Inactive | Platform-Admin |
| `POST` | `/terms` | Neuen Begriff anlegen | Platform-Admin |
| `PUT` | `/terms/{slug}` | Begriff editieren | Platform-Admin |
| `DELETE` | `/terms/{slug}` | Soft-Delete (`is_active=false`) | Platform-Admin |
| `POST` | `/terms/{slug}/cache/invalidate` | Cache fuer einen Begriff invalidieren (z. B. nach KB-Reingest) | Platform-Admin |
| `POST` | `/terms/cache/invalidate-all` | Kompletten Glossar-Cache invalidieren | Platform-Admin |

### 3.4 Antwortstruktur

```json
{
  "slug": "vpd",
  "label": "VPD",
  "long_label": "Vapor Pressure Deficit (Wasserdampfdruck-Defizit)",
  "category": "umwelt",
  "answer_text": "...",
  "expertise_level": "beginner",
  "language": "de",
  "language_mismatch_warning": false,
  "sources": [
    { "source_key": "...", "source_type": "...", "title": "...", "score": 0.91, "language": "de" }
  ],
  "related_terms": [
    { "slug": "luftfeuchte", "label": "Luftfeuchte" },
    { "slug": "blatttemperatur", "label": "Blatttemperatur" }
  ],
  "is_fallback": false,
  "model_name": "gemma3:12b",
  "provider_type": "ollama",
  "uses_tenant_data": false,
  "uses_cloud_provider": false,
  "kb_version": "ks-1.4.2-idx-20260420",
  "generated_at": "2026-04-25T10:00:00Z"
}
```

`is_fallback=true` signalisiert, dass die Antwort aus `glossary_terms.fallback_text` stammt (kein ausreichender RAG-Treffer); Frontend rendert dann "Kurzdefinition (kein KB-Treffer)" als Hinweis.

## 4. Backend-Komponenten

### 4.1 GlossaryService

`src/backend/app/domain/services/glossary_service.py`. Methoden:

- `get_term(slug, language, expertise_level)` — Cache-First, Fallback-Logik
- `list_terms(category=None, language="de")` — Liste fuer Browser/Sitemap
- `invalidate_cache(slug=None)` — Platform-Admin

**Ablauf von `get_term`:**

1. Slug normalisieren (Lowercase, Aliase ueber `glossary_terms.aliases.{language}` aufloesen).
2. Begriff aus `glossary_terms` laden; wenn nicht vorhanden -> HTTP 404.
3. Cache-Check: Redis-Hot, dann ArangoDB-Persist.
4. Cache-Hit -> Antwort mit `is_fallback=cached.is_fallback`, ohne LLM-Aufruf.
5. Cache-Miss -> KnowledgeServiceAdapter aufrufen:
   - Frage = Templating der `rag_query_template` mit `label_de`, `expertise_level`
   - `prompt_language` = User-Locale, `doc_language` = "all"
   - `top_k` = 5
   - `context` = null (KEIN Tenant-Daten-Zugriff)
6. Wenn `len(answer.sources) == 0` ODER `max_score < 0.4`:
   - Antwort = `glossary_terms.fallback_text.{language}`
   - `is_fallback=true`
7. Sonst: Antwort uebernehmen, `is_fallback=false`
8. Cache schreiben (Redis 7d, ArangoDB 7d).
9. Audit-Eintrag `ai_audit_log` mit `endpoint=glossary`, `uses_tenant_data=false`.

### 4.2 GlossarySeed

`src/backend/app/domain/services/glossary_seed_service.py`. Liest `spec/knowledge/glossary/seed_terms.yaml` und upserted Begriffe in `glossary_terms` (idempotent). Wird beim Backend-Start als Migration-Hook aufgerufen.

### 4.3 Celery-Tasks

| Task | Schedule | Zweck |
|------|----------|-------|
| `glossary.cleanup_expired_cache` | taeglich 02:45 UTC | Loescht `glossary_term_cache` mit `valid_until < now()` |
| `glossary.invalidate_after_reingest` | nach `ai.knowledge_service_ingest` (chained) | Invalidates kompletten Glossar-Cache; nachfolgende Anfragen regenerieren mit neuem KB-Index |

## 5. Frontend-Komponenten (React/MUI)

### 5.1 `<TermTooltip>`

Pfad: `src/frontend/src/components/glossary/TermTooltip.tsx`

Erweiterung der bestehenden `<HelpTooltip>` Foundation:

- **Trigger:** kleines Fragezeichen-Icon (`HelpOutlineIcon`, 14px) neben einem Begriff in der UI. Optional umschliessbar als Wrapper: `<TermTooltip slug="vpd">VPD</TermTooltip>` rendert "VPD ❓" mit dem Icon nach dem Wort.
- **Klickverhalten:** Klick oeffnet ein MUI `Popover` (max-width 360px, ueber Tap-Bereich).
- **Loading:** Skeleton-Placeholder.
- **Inhalt:**
  - Header: `long_label` + Sprach-Flag (wenn !=Locale).
  - Body: `answer_text`.
  - "Quellen"-Accordion (eingeklappt fuer Beginner, offen fuer Expert).
  - "Verwandte Begriffe": Inline-Chips, Klick oeffnet naechsten Tooltip (Stack-Navigation, Back-Button im Popover).
  - Footer: KI-Badge + Disclaimer + (bei Fallback) Hinweis.
- **Fetch:** `GET /api/v1/t/{slug}/knowledge/term/{slug}` (oder `/api/v1/public/knowledge/term/{slug}` im Light-Modus).
- **Cache im Frontend:** SWR-Caching, 7-Tage TTL via Redux Toolkit Query.
- **i18n:** alle Eigentexte ueber `pages.glossary.tooltip.*`.

### 5.2 `<GlossaryPage>`

Pfad: `src/frontend/src/pages/glossar/GlossaryPage.tsx`

Eigene Browse-Seite unter `/glossar`. Zeigt alle Begriffe gruppiert nach Kategorie. Klick auf einen Begriff oeffnet eine Detailansicht (volle Erklaerung, gleicher Inhalt wie Tooltip, aber als ganze Seite mit besserer Lesbarkeit). Im Light-Modus erreichbar als `/public/glossar`.

### 5.3 Integration in bestehende Seiten

`<TermTooltip>` ersetzt sukzessive die statischen `<HelpTooltip>`-Aufrufe in:

- Dashboard-Karten (REQ-009)
- Pflanzen-Detailseiten (REQ-001)
- Substrat-Editor (REQ-019)
- Duenge-Plan-Editor (REQ-004)
- IPM-Dialoge (REQ-010)
- Erfahrungsstufen-Onboarding (REQ-021)
- Sensor-Karten (REQ-005)

Die Migration der bestehenden Tooltips ist nicht Teil von REQ-035 (separate UX-Aufgabe), aber das Pattern wird in v1.0 mit mindestens 5 exemplarischen Stellen gezeigt.

## 6. Sicherheit & Datenschutz (REQ-025, NFR-007)

- **Keine PII:** Glossar-Aufrufe enthalten weder Tenant- noch User-Daten.
- **Audit-Log:** Aufrufe werden in `ai_audit_log` mit `endpoint=glossary`, `uses_tenant_data=false`, `uses_cloud_provider=false` (im lokalen Default) erfasst. Retention 30 Tage (NFR-011).
- **Rate-Limit Light-Modus:** 30 GET/min pro IP fuer `/term/{slug}`, 10 GET/min fuer `/terms`. Token-Bucket via Redis. Bei Ueberschreitung HTTP 429 mit `Retry-After`-Header.
- **Cloud-Provider-Hinweis:** Wenn ein Tenant einen Cloud-Provider als Default hat, geht auch der Glossar-Aufruf an den Cloud-Provider — daher ist im Light-Modus AUSSCHLIESSLICH der lokale Default-Provider verwendbar (Konfiguration: `AI_PUBLIC_PROVIDER_KEY` zeigt auf einen lokalen System-Default-Provider).
- **Prompt-Injection-Schutz (NFR-007):** Slug ist eine kontrollierte Whitelist; freier User-Input fliesst NICHT in den LLM-Prompt. Damit ist Prompt-Injection ueber den Glossar-Endpoint nicht moeglich.

## 7. Multilingual

| Aspekt | Status v1.0 |
|--------|-------------|
| `glossary_terms.labels` | de + en obligatorisch |
| `glossary_terms.fallback_text` | de + en obligatorisch |
| `glossary_terms.aliases` | de obligatorisch, en optional |
| `glossary_terms.rag_query_template` | jetzt nur de (Knowledge Service kann via `prompt_language` antworten) |
| LLM-Antwort | folgt `prompt_language` der Anfrage |
| Aliase-Aufloesung | sprachsensitiv (en-Anfrage matcht en-Aliase) |

Sobald englische Knowledge-Chunks im Knowledge Service verfuegbar sind, profitiert das Glossar automatisch — kein Spec-Bruch.

## 8. Akzeptanzkriterien

### Definition of Done

- [ ] **`glossary_terms`-Collection** angelegt, Indexes vorhanden.
- [ ] **Mindestens 30 Begriffe** aus §2.3 sind seedded und ueber `GET /knowledge/terms` abrufbar.
- [ ] **`GlossaryService.get_term`** implementiert mit Cache-First-Logik und KB-Fallback.
- [ ] **Tenant-scoped Endpoints** funktionsfaehig, ohne dass Tenant-Daten in Knowledge-Service-Aufrufen erscheinen (Test mocked KS und assertet `context = null`).
- [ ] **Light-Modus-Endpoints** funktionsfaehig, mit Rate-Limit pro IP.
- [ ] **Platform-Admin-Endpoints** fuer Term-CRUD und Cache-Invalidation.
- [ ] **`<TermTooltip>`** im Frontend implementiert, in mind. 5 Bestandsseiten integriert.
- [ ] **`<GlossaryPage>`** auf `/glossar` (Tenant) und `/public/glossar` (Light-Modus) verfuegbar.
- [ ] **Cache** in Redis (7d) + ArangoDB (7d) funktional, Invalidation bei KB-Reingest.
- [ ] **Audit-Log** schreibt jeden Aufruf, ohne PII.
- [ ] **i18n** vollstaendig DE + EN fuer Tooltip-Eigentexte.
- [ ] **Erfahrungsstufen-Variante** funktioniert: Beginner-Antwort vs. Expert-Antwort sind unterschiedlich (verifiziert ueber Snapshot-Tests gegen mocked KS).
- [ ] **Fallback-Pfad** wird bei `max_score < 0.4` ausgeloest, Antwort markiert mit `is_fallback=true`.
- [ ] **Vitest-Tests** fuer `<TermTooltip>` (Loading, Loaded, Error, Fallback, Related-Term-Stack-Navigation).

### Testszenarien

**Szenario 1: Beginner schaut VPD nach (lokal, Tenant)**
```
GIVEN: User Erfahrungsstufe = beginner, Locale = de
  AND: Tenant hat ai_features_enabled=true, Default-Provider Ollama lokal
  AND: Cache leer
WHEN: GET /api/v1/t/home/knowledge/term/vpd?expertise=beginner&language=de
THEN:
  - GlossaryService laedt term "vpd" aus glossary_terms
  - KnowledgeServiceAdapter.ask wird aufgerufen mit:
    - question = "Erklaere den Begriff 'VPD' fuer einen beginner Pflanzenfreund. ..."
    - prompt_language = "de"
    - doc_language = "all"
    - context = null
  - Antwort hat sources mit max_score >= 0.4
  - Antwort cached in Redis 7d und ArangoDB
  - Response: is_fallback=false, language=de, expertise_level=beginner, related_terms=[luftfeuchte, blatttemperatur, transpiration]
  - <AIResponse> rendert KI-Badge und Quellen-Footer (eingeklappt)
```

**Szenario 2: Begriff existiert nicht in der KB (Fallback)**
```
GIVEN: glossary_terms enthaelt "exotic-term-xyz" mit fallback_text gesetzt
  AND: Knowledge Service hat keine relevanten Chunks (max_score < 0.4)
WHEN: GET /api/v1/t/home/knowledge/term/exotic-term-xyz
THEN:
  - GlossaryService faellt zurueck auf glossary_terms.fallback_text.de
  - Response: is_fallback=true
  - sources = []
  - <AIResponse> rendert Hinweis "Kurzdefinition (kein KB-Treffer)"
```

**Szenario 3: Light-Modus (anonymer Aufruf)**
```
GIVEN: KAMERPLANTER_MODE=light
  AND: AI_PUBLIC_PROVIDER_KEY zeigt auf lokales Ollama
WHEN: GET /api/v1/public/knowledge/term/vpd  (kein Auth-Header)
THEN:
  - HTTP 200, Antwort wie Szenario 1
  - Audit-Log: user_key=null, tenant_key=null, uses_tenant_data=false, uses_cloud_provider=false
WHEN: 31 schnelle Aufrufe in 60s von derselben IP
THEN:
  - 30. Aufruf HTTP 200
  - 31. Aufruf HTTP 429 mit Retry-After-Header
```

**Szenario 4: Alias-Aufloesung**
```
GIVEN: Slug "vpd" hat Alias "saettigungsdefizit" in aliases.de
WHEN: GET /api/v1/.../knowledge/term/saettigungsdefizit?language=de
THEN:
  - GlossaryService loest Alias zu kanonischem Slug "vpd" auf
  - Response.slug = "vpd", Response.label = "VPD"
```

**Szenario 5: Cache-Hit ohne KS-Aufruf**
```
GIVEN: Cache enthaelt vpd:de:beginner mit valid_until in 5 Tagen
WHEN: GET .../knowledge/term/vpd?expertise=beginner&language=de
THEN:
  - Redis-Hit, KEINE KS-Anfrage
  - Latency < 50ms
  - Response identisch zum Cache-Inhalt
  - Audit-Log: status=ok, kb_version aus Cache uebernommen
```

**Szenario 6: KB-Reingest invalidiert Cache**
```
GIVEN: Glossar-Cache enthaelt 30 Eintraege
WHEN: Platform-Admin triggert ai.knowledge_service_ingest
  AND: Anschliessend laeuft glossary.invalidate_after_reingest
THEN:
  - Alle 30 Cache-Eintraege werden geloescht (Redis + ArangoDB)
  - Naechster Aufruf regeneriert mit neuer kb_version
```

**Szenario 7: Verwandte-Begriff-Navigation**
```
GIVEN: User oeffnet TermTooltip fuer "vpd"
WHEN: User klickt im Tooltip auf related-term Chip "blatttemperatur"
THEN:
  - Tooltip-Stack push: aktueller Tooltip wird verdeckt, neuer Tooltip "blatttemperatur" oeffnet
  - Back-Button kehrt zu "vpd" zurueck (Stack pop)
WHEN: User klickt "Schliessen"
THEN:
  - Kompletter Tooltip-Stack wird geschlossen
```

**Szenario 8: Erfahrungsstufen-Differenzierung**
```
GIVEN: Begriff "ec" wird angefragt
WHEN: GET .../knowledge/term/ec?expertise=beginner
THEN:
  - Antwort enthaelt einfache Erklaerung ("EC misst, wie viele Naehrstoffe im Wasser sind")
  - Keine konkreten Wertebereiche pro Phase
WHEN: GET .../knowledge/term/ec?expertise=expert
THEN:
  - Antwort enthaelt konkrete Wertebereiche (z. B. "Vegetativ: 1.0-1.4 mS/cm, Bluete: 1.4-1.8 mS/cm")
  - Hinweise zu Substratabhaengigkeit (Hydro vs. Erde)
```

**Szenario 9: Prompt-Injection-Versuch ueber Slug**
```
GIVEN: User sendet GET /knowledge/term/<script>alert(1)</script>
WHEN: Endpoint verarbeitet
THEN:
  - URL-Decoding ergibt unzulaessigen Slug (enthaelt Sonderzeichen)
  - Backend lehnt mit HTTP 422 ab
  - KEIN KS-Aufruf
WHEN: User sendet GET /knowledge/term/vpd?expertise=ignore_previous_instructions
THEN:
  - expertise wird gegen Enum {beginner, intermediate, expert} validiert
  - Bei Mismatch HTTP 422
  - KEIN KS-Aufruf
```

**Szenario 10: Multilingual-Aufruf**
```
GIVEN: User-Locale = en, KB hat nur deutsche Chunks
WHEN: GET .../knowledge/term/vpd?language=en
THEN:
  - KS-Aufruf mit prompt_language=en, doc_language=all
  - LLM antwortet auf Englisch, basierend auf deutschen Quellen-Chunks
  - Response.language=en
  - Response.language_mismatch_warning=false (Antwort matcht Locale, nur Quellen-Sprache differiert)
WHEN: language=en und doc_language explizit "en" (kein Treffer)
THEN:
  - Fallback: glossary_terms.fallback_text.en
  - is_fallback=true
```

## 9. Offene Punkte

- **Mehr Begriffe:** v1.0 startet mit 30; Erweiterung auf ~80-100 nach erstem Feedback. Kuratierung redaktionell (kein Auto-Extraction aus KB-Texten).
- **Tooltip-Migration in Bestandsseiten:** ~50 bestehende `<HelpTooltip>`-Stellen sollen sukzessive durch `<TermTooltip>` abgeloest werden — eigener UX-Workstream.
- **Voice/TTS-Integration:** "Vorlesen"-Button im Tooltip fuer Accessibility (UI-NFR), nicht in v1.0.
- **Anonyme Beitraege:** Light-Modus-Nutzer koennten Verbesserungsvorschlaege fuer Begriffe einreichen (Crowdsourcing-Element). In v1.0 nicht enthalten.
