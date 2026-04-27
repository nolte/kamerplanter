# Spezifikation: REQ-031 - KI-Assistent & Wissensvermittlung

```yaml
ID: REQ-031
Titel: KI-Assistent & Wissensvermittlung (RAG-basiert)
Kategorie: KI & Beratung
Fokus: Beides
Technologie: Python 3.14+, FastAPI, Celery, ArangoDB, Redis, PostgreSQL 17 + pgvector 0.8, ONNX Embedding Service, bge-reranker-v2-m3, React 19, TypeScript 5.9, MUI 7, Ollama / Anthropic / OpenAI-kompatible APIs
Status: Entwurf
Version: 2.0
Abhängigkeit: REQ-001 v5.0 (Stammdaten), REQ-003 v1.0 (Phasensteuerung), REQ-004 v3.1 (Düngung), REQ-005 v2.3 (Sensorik), REQ-006 v2.7 (Aufgabenplanung), REQ-009 v1.0 (Dashboard), REQ-011 v1.0 (Adapter-Pattern), REQ-013 v2.0 (Pflanzdurchlauf), REQ-021 v1.0 (Erfahrungsstufen), REQ-022 v2.4 (Pflegeerinnerungen), REQ-023 v1.7 (Auth), REQ-024 v1.4 (Mandantenverwaltung), REQ-025 v1.0 (DSGVO), REQ-027 v1.2 (Light-Modus), NFR-007 (LLM-Sicherheit), NFR-011 (Retention)
Wird benoetigt von: REQ-033 v1.1 (MCP-Server), REQ-035 (Fachbegriff-Glossar), REQ-036 (Diagnose-Assistent)
```

## Versionshistorie

| Version | Datum | Aenderung |
|---------|-------|-----------|
| 1.0 | 2026-03-28 | Initialer Entwurf: pgvector-im-Backend, MiniLM-L6-v2, Ollama/OpenAI/Anthropic Adapter, TipCardsPanel, AiChatDrawer |
| **2.0** | **2026-04-25** | **Major Refactor: Knowledge Service als externes Microservice, multilingual-e5-large + Hybrid Search + bge-reranker, Backend wird zum duennen KnowledgeServiceAdapter, neue Features "Warum?"-Buttons (`POST /ai/explain`) und expliziter Tipp-des-Tages, dreistufiger Feature-Toggle (Deployment / Tenant / User-Consent), Light-Modus-Verhalten, Multilingual-Vorbereitung, neuer Consent-Typ `ai_tenant_data_access`, Abgrenzung zu REQ-033/REQ-035/REQ-036** |
| 2.2 | 2026-04-27 | **W-011 (KI-Fallback offline):** §1 Klarstellung — regelbasierte Fallback-Tipps gelten **backend-seitig** bei Knowledge-Service-Ausfällen, nicht für Frontend-Offline-Phasen. Frontend-Offline behandelt KI-Features als Online-only (UI-NFR-012 R-042a). Verhindert Drift durch dupliziertes Mini-Regelwerk im Frontend. |
| 2.1 | 2026-04-27 | **ADR-002 (W-006 Tenant-Species im KI-Kontext):** Genus/Family-Fallback in `AiContextBuilder.resolve_species_for_ks()` ergaenzt — tenant-eigene Species werden via `parent_species_key` → Genus → Family auf KS-aufloesbare Werte gemappt. `QuestionContext` erweitert um `cultivar_hint` und `confidence`-Felder. Antwortstruktur (§5.5) liefert `confidence`, `fallback_species`, `cultivar_hint` an Frontend. `<AIResponse>`-Komponente bekommt sichtbares Confidence-Badge bei `low`. |

## 1. Business Case

**User Story (Casual User — Tipp-Karten):** "Als Zimmerpflanzen-Besitzer ohne Fachkenntnisse moechte ich auf der Detailseite meiner Pflanze kontextabhaengige Pflegehinweise als kompakte Karten sehen — damit ich sofort weiß, was zu tun ist, ohne in Foren oder Buechern nachschlagen zu muessen."

**User Story (Casual User — Tipp des Tages):** "Als Casual-User moechte ich beim Oeffnen des Dashboards einen einzelnen, fuer mich relevanten KI-Tipp sehen — damit ich mit einem Blick weiss, worauf ich heute achten sollte, ohne mich durch Listen zu klicken."

**User Story (Grower — Diagnose):** "Als erfahrener Grower moechte ich bei ungewoehnlichen Symptomen eine KI-gestuetzte Analyse mit konkreten Handlungsempfehlungen erhalten — damit ich schnell die Ursache identifiziere und Ernteverluste vermeide."

**User Story (Grower — "Warum?"-Buttons):** "Als Grower moechte ich auf einer KI-generierten Pflegeaufgabe oder einem Phasenuebergangs-Vorschlag einen 'Warum?'-Button finden — damit ich auf Wunsch in 1-2 Saetzen erfahre, warum das System mir genau diese Empfehlung gibt, und entscheiden kann, ob ich folge."

**User Story (Self-Hosted-Nutzer — Datenschutz):** "Als Self-Hosted-Nutzer moechte ich den KI-Assistenten vollstaendig lokal betreiben koennen (Ollama + lokales Modell) — damit keine meiner Pflanzen- und Messdaten an externe Cloud-Dienste uebertragen werden."

**User Story (Pro-Nutzer — Chat):** "Als fortgeschrittener Nutzer moechte ich einen Chat-Dialog mit KI-Kontext fuehren koennen, in dem das System meine aktuelle Pflanzenphase, Messwerte und Duengehistorie kennt — damit ich komplexe Fragen wie 'Soll ich in Woche 4 der Bluete den PK-Boost schon starten?' beantworten lassen kann."

**User Story (Datenschutz-bewusster Nutzer):** "Als datenschutzbewusster Nutzer moechte ich transparent sehen, welche Daten an welchen KI-Provider gesendet werden, ob meine Pflanzdaten als Kontext mitgesendet werden und meine Einwilligung jederzeit widerrufen koennen — damit ich die Kontrolle ueber meine Daten behalte."

**User Story (Tenant-Admin — Provider und Feature-Toggle):** "Als Tenant-Admin moechte ich auf Tenant-Ebene entscheiden koennen, ob KI-Funktionen fuer meinen Tenant aktiviert sind, und welche Provider verwendet werden — damit ich KI fuer einen Schul- oder Kindergartens-Tenant deaktivieren oder fuer einen Profi-Tenant gezielt einen leistungsfaehigen Cloud-Provider freischalten kann."

**User Story (Light-Modus-Nutzer):** "Als anonymer Light-Modus-Nutzer moechte ich KI-gestuetzte Wissens-Antworten zu Fachbegriffen (z. B. 'Was ist VPD?') bekommen, aber keine personalisierten Tipps — damit die Anwendung auch ohne Login einen Mehrwert bietet, ohne meinen Sitzungs-Context an Cloud-Provider zu senden."

**Beschreibung:**

REQ-031 v2.0 stellt einen KI-gestuetzten Assistenten in Kamerplanter bereit, der ueber das eigenstaendige **Knowledge Service Microservice** (`src/knowledge-service/`) eine kuratierte, RAG-basierte Wissensvermittlung anbietet und in der App vier sichtbare Funktionen liefert:

1. **Tipp-Karten (Pflanzen-/Run-Kontext)** — wie v1.0, ueberarbeitet auf Knowledge-Service-Backend
2. **Tipp des Tages (Dashboard)** — neuer expliziter Use-Case, on-first-load lazy
3. **"Warum?"-Buttons (Aufgaben, Erinnerungen, Phasenwechsel)** — neuer Endpoint, kontext-injiziert
4. **Chat-Dialog (kontextbewusst)** — wie v1.0, ueberarbeitet auf Knowledge-Service-Backend

Die strukturierte Diagnose-Funktion (Multi-Step-Form, Symptom-Katalog) wird in **REQ-036** ausgelagert und nutzt REQ-031 nur als Wissens-Backend. Die Fachbegriff-Tooltips werden in **REQ-035** ausgelagert. Die externe MCP-Schnittstelle ist in **REQ-033** beschrieben.

**Grundprinzipien (revidiert):**

- **Wissens-Backend als Microservice:** Die RAG-Pipeline (Embedding, Hybrid Search, Reranking, LLM-Adapter) lebt in `src/knowledge-service/` als eigenstaendiger FastAPI-Service mit eigener PostgreSQL+pgvector-Persistenz. Das Kamerplanter-Backend ruft den Knowledge Service ueber HTTP auf — analog dem Adapter-Pattern aus REQ-011.
- **Optional auf drei Ebenen:** Deployment-Flag (Operator) → Tenant-Setting (Tenant-Admin) → User-Consent (Endnutzer). Jede Ebene kann KI separat abschalten.
- **Local-First moeglich, Cloud-Provider freiwillig:** Default-Konfiguration laeuft mit Ollama lokal. Cloud-Provider sind optional und erfordern explizite Einwilligung (REQ-025, neuer Consent-Purpose `ai_cloud_processing`).
- **Tenant-Daten-Zugriff explizit:** Wenn KI-Antworten Pflanzendaten des Nutzers als Kontext nutzen, ist der Consent-Typ `ai_tenant_data_access` erforderlich. Reine Wissensfragen (z. B. "Was ist VPD?") erfordern diesen Consent NICHT.
- **Quellenpflicht:** Jede LLM-Antwort enthaelt Verweise auf die zitierten Knowledge-Chunks (`source_key`, `source_type`, `score`). Frontend rendert sie aufklappbar.
- **Klares KI-Labeling:** Jede generierte Antwort traegt einen sichtbaren KI-Badge inkl. Modell-Angabe und Datum. Nutzer wissen jederzeit, dass eine KI gesprochen hat.
- **Tenant-Daten-Indikator:** Wenn die Antwort Tenant-Kontext enthaelt, zeigt das UI einen separaten Indikator ("Diese Antwort nutzt Daten deiner Pflanze X").
- **Multilingual-Vorbereitung:** Wissensbasis liefert `language`-Metadaten pro Chunk (heute "de", spaeter "en"). Antwortet ein Provider in falscher Sprache, kennzeichnet das Frontend dies als Hinweis. Knowledge Service akzeptiert bereits `prompt_language` und `doc_language` als Parameter.
- **Graceful Degradation:** Bei nicht erreichbarem Knowledge Service oder Provider werden **backend-seitig** regelbasierte Fallback-Tipps generiert (Zugriff auf ArangoDB-Stammdaten + statische Regelbasis im Service-Layer). Die App bleibt nutzbar — der Fehlerfall wird vom Frontend transparent aufgefangen. <!-- W-011 -->
- **Frontend-Offline (UI-NFR-012):** KI-Features sind generell **online-only** — wenn das Frontend offline ist, zeigt die UI fuer KI-Tipps/Chat/Daily-Tip einen "Online erforderlich"-Hinweis statt einer KI-Antwort. Die regelbasierten Fallback-Tipps oben gelten ausdruecklich nur fuer Backend-seitige Knowledge-Service-Ausfaelle, nicht fuer Frontend-Offline-Phasen. Begruendung: Frontend hat keinen ArangoDB-Zugriff fuer Tenant-Kontext und keine Embeddings; ein dedupliziertes Mini-Regelwerk im Frontend wuerde Drift erzeugen (UI-NFR-012 R-042a). <!-- W-011 -->
- **Erfahrungsstufen-sensitiv:** Beginner sehen vereinfachte Karten, Chat ist ab Intermediate verfuegbar, Expert-Nutzer erhalten technische Details und Quellen-Anker per Default offen (REQ-021).

### 1.1 Architekturueberblick

```
+-----------------------+      +------------------------+
|  Frontend (React)     |      | LLM-Client (extern)    |
|  - TipCardsPanel      |      | (REQ-033 MCP-Server)   |
|  - DailyTipCard       |      +-----------+------------+
|  - WhyButton + Drawer |                  |
|  - AiChatDrawer       |                  |
|  - AIResponse-Hülle   |                  |
+-----------+-----------+                  |
            | REST (JSON, SSE für Chat)    |
            v                              |
+-----------------------+                  |
|  Kamerplanter Backend |                  |
|  /api/v1/.../ai/...   |                  |
|                       |                  |
|  AiAssistantService   |                  |
|    + ContextBuilder   |  <-- Tenant-Daten aus ArangoDB (Plant, Phase, Sensor, IPM)
|    + ConsentGuard     |  <-- REQ-025
|    + FeatureGuard     |  <-- 3-Stufen-Toggle
|    + AuditLogger      |  <-- ai_audit_log
|                       |                  |
|  KnowledgeServiceAdapter (HTTP)          |
+-----------+-----------+                  |
            |                              |
            v                              v
+-----------------------------------------------------+
|  Knowledge Service Microservice                     |
|  (src/knowledge-service/, eigenes Helm-Release)     |
|                                                     |
|  /search   /ask   /classify   /ingest   /health     |
|                                                     |
|  EmbeddingEngine (multilingual-e5-large, ONNX)      |
|  HybridSearch (Vector 0.4 + BM25 0.6) + RRF (k=60)  |
|  RerankerEngine (bge-reranker-v2-m3, 20 -> 5)       |
|  PromptEngine (typ-spezifische DE/EN-Prompts)       |
|  LlmAdapter (Ollama | Anthropic | OpenAI-kompat.)   |
|                                                     |
|  PostgreSQL 17 + pgvector 0.8 (1024-dim)            |
|  Knowledge YAMLs (spec/knowledge/rag/, 9 Cats,      |
|  ~267 Chunks, 87.4% RAG-Eval-Score Stand 2026-04)   |
+-----------------------------------------------------+
```

**Kerntrennung:**

- **Knowledge Service** ist ein **autonomes Microservice**. Es kennt weder Kamerplanter-Tenants noch Nutzer noch Pflanzen-Detaildaten. Sein Vertrag ist: "Frage rein, Antwort + Quellen raus."
- **Kamerplanter-Backend** ist die **Tenant-, Auth- und Kontext-Schicht**. Es entscheidet, ob ein Aufruf zulaessig ist, reichert die Frage mit Tenant-Kontext an, ruft den Knowledge Service, persistiert Konversationen und Audit-Eintraege.
- **Frontend** zeigt Antworten mit klarem KI-Labeling und Quellenangaben.

### 1.2 Bestehender Knowledge Service (Stand 2026-04)

Der Microservice unter `src/knowledge-service/` ist bereits implementiert und produktiv im Cluster:

| Komponente | Realisierung |
|------------|--------------|
| Embedding | `multilingual-e5-large` (1024 Dim), ONNX-Runtime in eigenem Embedding-Service-Pod, CPU-only |
| Vector Store | PostgreSQL 17 + pgvector 0.8, Tabelle `knowledge_chunks`, IVFFlat-Index `vector_cosine_ops` |
| Volltextindex | tsvector mit Umlaut-Varianten (ae/oe/ue + Umlaute) |
| Retrieval | Hybrid Search (Vector-Score 0.4 + BM25-Score 0.6) + Reciprocal Rank Fusion (k=60) |
| Reranker | `bge-reranker-v2-m3` (eigener Pod), 20 Kandidaten -> Top 5 |
| LLM-Adapter | `app/llm/ollama.py`, `app/llm/anthropic.py`, `app/llm/openai_compatible.py` |
| Default-LLM | `gemma3:12b` via Ollama (Empfehlung Stand 2026-04, 87.4% RAG-Eval-Score) |
| Knowledge | `spec/knowledge/rag/**/*.yaml`, 9 Kategorien (diagnostik, duengung, bewaesserung, umwelt, ipm, phasen, outdoor/companion_planting, pflege, allgemein/anfaenger), 267 Chunks |
| Endpoints | `GET /search`, `POST /ask`, `POST /classify`, `POST /ingest`, `GET /health`, `GET /ready` |
| Multilingual | `prompt_language` und `doc_language` Parameter in `/search` und `/ask` (de/en/all) |

REQ-031 v2.0 dokumentiert diese Realitaet als verbindlichen Zustand. Aenderungen am Knowledge Service erfolgen ueber separate Pull Requests gegen `src/knowledge-service/` und werden in dessen eigener README dokumentiert; sie aendern dann die Tabelle in §1.2.

<!-- Quelle: Knowledge-Service-Realität 2026-04, RAG-Eval Report 2026-04-07 -->

### 1.3 Drei-Stufen-Feature-Toggle (revidiert v2.0)

KI-Funktionen sind auf drei Ebenen zuschaltbar. Nur wenn alle drei zustimmen, ist eine konkrete KI-Funktion fuer einen konkreten Nutzer aktiv:

```
[1] Deployment-Flag         AI_FEATURES_ENABLED  (Helm value, Operator)
                                        |
                                  true? +------> nein -> komplette KI-API liefert HTTP 404 (so als gaebe es sie nicht)
                                        |
                                        v
[2] Tenant-Setting          tenant.settings.ai_features_enabled  (Tenant-Admin via UI)
                                        |
                                  true? +------> nein -> KI-Endpoints liefern HTTP 403 + i18n-Hinweis
                                        |
                                        v
[3] User-Consent            ConsentRecord per ProcessingPurpose
                                        |
                       welcher Endpoint?+
                                        |
       ----------------+-----------------+----------------+
       |               |                 |                |
   Wissensfrage    "Warum?"         Pflanzen-Tipp     Cloud-Provider
   (Glossar,       (mit Tenant-     (Plant/Run-       (statt lokal)
   factual,        Kontext)         Kontext)
   ohne Tenant-
   daten)
       |               |                 |                |
   KEIN Consent    ai_tenant_data    ai_tenant_data   ai_cloud_processing
   noetig          _access           _access          (zusaetzlich zu den
                                                       anderen)
```

**Default-Werte:**

| Ebene | Default | Begruendung |
|-------|---------|-------------|
| `AI_FEATURES_ENABLED` | `false` | Operator muss aktiv einschalten — KI-Komponenten brauchen Ressourcen |
| `tenant.settings.ai_features_enabled` | `false` | Opt-in pro Tenant — Schulen, Kindergarten, Behoerden bleiben out-of-the-box ohne KI |
| `ai_tenant_data_access` Consent | nicht erteilt | Datensparsamkeit — Wissensfragen ohne Kontext brauchen keinen Consent |
| `ai_cloud_processing` Consent | nicht erteilt | DSGVO — Cloud-Provider sind Drittland-Datenuebermittlung |

### 1.4 Abgrenzung zu benachbarten REQs

| REQ | Beziehung |
|-----|-----------|
| **REQ-029** (Bilderkennung) | Komplementaer. REQ-029 identifiziert unbekannte Pflanzen / Krankheiten per Bild. REQ-031 beraet auf Basis von Text + Stammdaten. Beide unabhaengig nutzbar. Synergie: REQ-029-Ergebnis kann als Kontext in REQ-031-Chat einfliessen, REQ-036 verwendet REQ-029 fuer optionale Foto-Analyse. |
| **REQ-030** (Notifications) | Komplementaer. REQ-030 stellt Notifications zu (HA, E-Mail, etc.). REQ-031 generiert KI-Tipps; relevante Tipps koennen als Notification verschickt werden — der entsprechende Notification-Typ wird von REQ-030 spezifiziert. |
| **REQ-033** (MCP-Server) | REQ-033 ist die externe LLM-Schnittstelle. Tool `search_plant_knowledge` ruft denselben Knowledge Service wie REQ-031. Tool-Antworten enthalten dieselben Quellen-Referenzen. |
| **REQ-035** (Fachbegriff-Glossar) | Baut auf REQ-031 auf. Glossar nutzt `POST /knowledge/term/{slug}` (definiert in REQ-035), das intern den Knowledge Service `/ask` mit fixer Frage-Vorlage aufruft. Light-mode-faehig. |
| **REQ-036** (Diagnose-Assistent) | Baut auf REQ-031 auf. Strukturierte Diagnose-Form mit Symptom-Katalog. Endgueltige LLM-Auswertung erfolgt ueber den Knowledge Service. |
| **REQ-027** (Light-Modus) | Im Light-Modus sind nur Wissensfragen ohne Tenant-Kontext (Glossar via REQ-035, allgemeine Fachfragen) verfuegbar. Tipp-Karten und "Warum?"-Buttons sind ausgeblendet, weil sie Tenant-Kontext brauchen. |

## 2. RAG-Architektur (Knowledge Service)

Diese Sektion fasst die Architektur des Knowledge Service zusammen, soweit sie fuer das Verstaendnis von REQ-031 noetig ist. Detaillierte Implementierungsdokumentation lebt in `src/knowledge-service/README.md`.

### 2.1 Wissensbasis-Quellen (4 Ebenen)

| Ebene | Datenquelle | Personenbezug | Wo gespeichert |
|-------|-------------|---------------|----------------|
| 1. **Globale Stammdaten** | Species, Cultivar, GrowthPhase, Pest, Disease (read-only Sicht) | Kein Personenbezug | Knowledge Service-Index (vektorisierte Snapshots) |
| 2. **Kuratierte Knowledge-Base** | YAMLs unter `spec/knowledge/rag/` (9 Kategorien) | Kein Personenbezug | Knowledge Service-Index |
| 3. **Tenant-Kontext** | Aktiver PlantingRun, Phase, Messwerte (EC, pH, VPD), aktive IPM-Events, letzte FeedingEvents | Indirekt | Im Backend pro Anfrage gebaut, als `context`-Objekt an Knowledge Service uebergeben |
| 4. **Nutzer-Pflanzdaten** | Pflegehistorie, Ernteresultate, CareConfirmations, PlantDiaryEntry | Ja (Consent erforderlich) | Im Backend pro Anfrage gebaut, als Teil von `context` uebergeben — NUR wenn `ai_tenant_data_access` Consent vorhanden |

**Ebene 1 + 2** werden vom Knowledge Service intern als Vektoren gehalten. Ebene 1 wird durch einen periodischen `POST /ingest` aktualisiert (s. §4.6). Ebene 2 wird mit Deployment ausgerollt und bei Aenderungen durch erneuten `/ingest` neu indexiert.

**Ebene 3 + 4** werden zur Laufzeit im Backend zusammengestellt (`AiContextBuilder`) und ueber das `context`-Feld der Knowledge-Service-API beigegeben. Das `context`-Feld entspricht dem `QuestionContext`-Schema des Microservice (`species`, `phase`, `substrate`, `ec`, `ph` — siehe `src/knowledge-service/app/schemas.py`).

### 2.2 Retrieval-Strategie (im Knowledge Service)

1. Frage wird vom Embedding-Service in 1024-dim-Vektor verwandelt (multilingual-e5-large, mit `query: ` Prefix gemaess E5-Konvention).
2. Hybrid Search: Vector-Score (`<=>` Cosine) gewichtet 0.4, BM25-Score gewichtet 0.6.
3. Reciprocal Rank Fusion (k=60) merged beide Ranglisten.
4. Top 20 Kandidaten gehen in den Reranker (`bge-reranker-v2-m3`).
5. Top 5 finale Chunks werden als Kontext in den LLM-Prompt eingefuegt.
6. Antwort enthaelt finale Chunks als `sources` mit `source_key`, `source_type`, `title`, `score`, `language`.

Optionaler `doc_language`-Filter (de/en/all) beschraenkt die Vektor-Suche auf Chunks der gewuenschten Sprache.

### 2.3 Multilingual-Vorbereitung

Heute sind alle Knowledge-Chunks deutschsprachig (`language: "de"`). Die API-Vertraege auf beiden Seiten unterstuetzen bereits Mehrsprachigkeit:

| Komponente | Status |
|------------|--------|
| Knowledge Service `AskRequest.doc_language` | umgesetzt (de / en / all) |
| Knowledge Service `AskRequest.prompt_language` | umgesetzt (de / en) — bestimmt System-Prompt-Sprache |
| Knowledge Service `KnowledgeChunkResponse.language` | umgesetzt — pro Chunk |
| Embedding-Modell | bereits multilingual (e5-large) — Englisch-Suche funktioniert technisch sofort, sobald englische Chunks indexiert sind |
| YAMLs `spec/knowledge/rag/**/*.yaml` | nur Deutsch — englische Varianten werden in einer separaten zukuenftigen Iteration ergaenzt (kein Spec-Bruch) |

Solange keine englischen Chunks vorhanden sind, antwortet der Knowledge Service bei englischer User-Locale entweder weiterhin auf Basis deutscher Chunks (wenn `doc_language="all"`) oder liefert keine Treffer (wenn `doc_language="en"`). Das Backend setzt deshalb pro Anfrage:

- `prompt_language` = User-Locale (de oder en)
- `doc_language` = `"all"` (bis EN-Chunks verfuegbar sind, danach `prompt_language`)
- Liefert die Antwort in einer anderen Sprache als die User-Locale, fuegt das Backend eine Markierung `language_mismatch_warning: true` hinzu, die das Frontend rendert ("Antwort auf Deutsch, weil die englische Wissensbasis noch im Aufbau ist.").

## 3. Datenmodell (Backend-Seite)

Die Vektordatenbank lebt im Knowledge Service. Im Kamerplanter-Backend werden lediglich KI-spezifische Tenant-/Nutzer-Daten persistiert.

### 3.1 Document Collections (ArangoDB)

**`ai_provider_configs`** — Provider-Konfigurationen (unveraendert ggu. v1.0, ergaenzt um `language_default`):

```json
{
  "_key": "uuid",
  "tenant_key": "string | null",
  "provider_type": "ollama | anthropic | openai_compatible",
  "display_name": "string",
  "base_url": "string",
  "model_name": "string",
  "api_key_encrypted": "string | null",
  "requires_consent": "boolean",
  "is_active": "boolean",
  "is_default": "boolean",
  "max_tokens": "int (default: 2048)",
  "temperature": "float (default: 0.1)",
  "timeout_seconds": "int (default: 60)",
  "language_default": "de | en (default: de)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Indexes:**
- Persistent auf `tenant_key`
- Persistent Unique auf `tenant_key + is_default` WHERE `is_default = true`

**`ai_conversations`** — Chat-Verlaeufe (unveraendert struktur, Retention-Default 90 Tage, NFR-011):

```json
{
  "_key": "uuid",
  "tenant_key": "string",
  "user_key": "string",
  "title": "string | null",
  "context_type": "plant_instance | planting_run | general | term | explain",
  "context_key": "string | null",
  "provider_key": "string",
  "model_name": "string",
  "language": "de | en",
  "message_count": "int",
  "messages": [
    {
      "role": "user | assistant | system",
      "content": "string",
      "timestamp": "datetime",
      "source_chunks": [
        {"source_key": "string", "source_type": "string", "score": "float", "language": "string"}
      ]
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime",
  "expires_at": "datetime"
}
```

**`ai_tip_cache`** — Gecachte Tipp-Karten und "Warum?"-Erklaerungen:

```json
{
  "_key": "uuid",
  "tenant_key": "string",
  "context_type": "plant_instance | planting_run | general | daily | explain",
  "context_key": "string",
  "tip_type": "care | warning | optimization | diagnosis | milestone | explanation",
  "priority": "critical | high | medium | low",
  "title": "string",
  "body": "string",
  "action_url": "string | null",
  "sources": [
    {"source_key": "string", "source_type": "string", "score": "float", "language": "string"}
  ],
  "language": "de | en",
  "language_mismatch_warning": "boolean (default: false)",
  "uses_tenant_data": "boolean (default: false)",
  "provider_key": "string",
  "model_name": "string",
  "generated_at": "datetime",
  "valid_until": "datetime",
  "dismissed_at": "datetime | null",
  "dismissed_by": "string | null",
  "acted_on_at": "datetime | null"
}
```

Neue Felder ggu. v1.0:
- `tip_type: explanation` — fuer "Warum?"-Antworten
- `context_type: daily` — fuer Tipp des Tages
- `context_type: explain` — fuer "Warum?"-Antworten
- `language` und `language_mismatch_warning` — Multilingual-Vorbereitung
- `sources` als strukturierte Liste statt nur `source_chunks: string[]` — enthaelt jetzt source_type, score und language pro Quelle
- `uses_tenant_data` — fuer den UI-Indikator

**`ai_audit_log`** (NEU) — Audit-Eintraege fuer alle KI-Aufrufe (NFR-007, NFR-011):

```json
{
  "_key": "uuid",
  "tenant_key": "string",
  "user_key": "string | null",
  "endpoint": "string",
  "context_type": "string | null",
  "context_key": "string | null",
  "question_hash": "string (sha256 ueber Frage)",
  "answer_length": "int",
  "model_name": "string",
  "provider_type": "string",
  "kb_version": "string (Knowledge-Service-Version + Index-Hash)",
  "language": "string",
  "uses_tenant_data": "boolean",
  "uses_cloud_provider": "boolean",
  "latency_ms": "int",
  "status": "ok | denied | provider_error | knowledge_service_error | timeout",
  "error_class": "string | null",
  "created_at": "datetime"
}
```

Retention 30 Tage (NFR-011). Inhalte (Frage / Antwort) werden NICHT im Klartext geloggt — nur Hash und Laenge. Auskunftsexport (REQ-025) liefert die Audit-Daten gehasht.

**`ai_tenant_settings`** (NEU) — KI-Einstellungen pro Tenant (Stufe 2 des Feature-Toggles):

Tenant-Settings sind kein eigenes Document, sondern leben als Sub-Objekt am `tenants`-Document (REQ-024):

```json
{
  // ... bestehendes tenants-Doc ...
  "settings": {
    // ... andere Settings ...
    "ai_features_enabled": "boolean (default: false)",
    "ai_default_provider_key": "string | null",
    "ai_allow_cloud_providers": "boolean (default: false)",
    "ai_daily_tip_enabled": "boolean (default: true wenn ai_features_enabled)"
  }
}
```

### 3.2 Edge Collections (ArangoDB)

```
ai_tip_references_plant   ai_tip_cache -> plant_instances
ai_tip_references_run     ai_tip_cache -> planting_runs
ai_conversation_about     ai_conversations -> plant_instances | planting_runs
ai_audit_about            ai_audit_log -> plant_instances | planting_runs (optional)
```

### 3.3 Verzicht auf eigene Vektor-Tabellen im Backend

Im Gegensatz zu v1.0 enthaelt das Backend KEINE Tabelle `ai_vector_chunks` mehr. Vektoren leben ausschliesslich im Knowledge Service (PostgreSQL+pgvector). Der Backend-Code spricht den Knowledge Service ueber HTTP an. TimescaleDB im Kamerplanter-Backend wird damit von der KI-Last entkoppelt.

## 4. Technische Umsetzung (Backend)

### 4.1 KnowledgeServiceAdapter (neu)

Backend-Komponente in `src/backend/app/data_access/external/knowledge_service_adapter.py`. Implementiert ein Interface aus `src/backend/app/domain/interfaces/knowledge_service.py`:

```python
class IKnowledgeService(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
    ) -> list[KnowledgeChunk]: ...

    @abstractmethod
    async def ask(
        self,
        question: str,
        *,
        top_k: int = 10,
        context: QuestionContext | None = None,
        doc_language: str | None = None,
        prompt_language: str | None = None,
    ) -> AskResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

Default-Implementierung `HttpKnowledgeServiceAdapter` nutzt `httpx.AsyncClient` mit Timeout (`AI_KNOWLEDGE_SERVICE_TIMEOUT_S`, default 60), Retry-Logik (max 2 Wiederholungen bei `5xx`) und circuit-breaker-aehnlichem Verhalten (nach 3 Fehlern in 60s wird der Adapter fuer 60s als unhealthy markiert).

### 4.2 AiContextBuilder (vereinfacht)

Liefert ein `QuestionContext` und einen optionalen erweiterten Context-Block (Pflegehistorie, IPM-Events). Trennt strikt zwischen:

- **`base_context: QuestionContext`** — wird IMMER an den Knowledge Service uebermittelt, enthaelt nur Stammwerte (species, phase, substrate, ec, ph). Diese Felder enthalten keine PII.
- **`extended_context: dict | None`** — wird NUR an den Knowledge Service uebermittelt, wenn der User den Consent `ai_tenant_data_access` erteilt hat. Enthaelt zusaetzliche Felder (letzte_pflege, aktive_ipm_events, juengste_diary_einträge, etc.).

Der Context-Builder darf KEINE Felder mit direktem Personenbezug aufnehmen (Tenant-Name, Nutzername, E-Mail) — siehe NFR-007 §LLM-Sicherheit.

<!-- Quelle: ADR-002 / W-006 -->
**4.2.1 Genus/Family-Fallback fuer tenant-eigene Species (ADR-002)**

Tenant-eigene Species (`origin='tenant'`, REQ-001) sind **nicht im Knowledge-Service-Index** vorhanden — Schicht 1 (globale Stammdaten) und Schicht 2 (kuratierte YAMLs) decken sie nicht ab. Ohne Fallback wuerde der KS keine relevanten Chunks finden und generische oder irrelevante Antworten liefern.

**Fallback-Hierarchie** (durchgaengig vom AiContextBuilder vor dem KS-Aufruf):

```python
def resolve_species_for_ks(species: Species) -> tuple[str, str | None, ConfidenceLevel]:
    """ADR-002: Mapped tenant-eigene Species auf einen KS-aufloesbaren Wert.

    Returns:
        (ks_species_value, cultivar_hint, confidence_level)
    """
    if species.origin != "tenant":
        # Globale Species — direkt nutzen
        return (species.scientific_name, None, ConfidenceLevel.HIGH)

    # Tenant-Species: Fallback in Reihenfolge
    if species.parent_species_key:
        # Stufe 1: parent_species (empfohlene Konfiguration, REQ-001)
        parent = species_repo.get(species.parent_species_key)
        if parent and parent.origin != "tenant":
            return (
                parent.scientific_name,
                species.common_names[0] if species.common_names else None,
                ConfidenceLevel.MEDIUM,
            )

    if species.genus:
        # Stufe 2: Genus-Fallback (z.B. "Solanum sp.")
        return (
            f"{species.genus} sp.",
            species.scientific_name or species.common_names[0] if species.common_names else None,
            ConfidenceLevel.LOW,
        )

    if species.family:
        # Stufe 3: Family-Fallback (selten — Solanaceae)
        return (species.family, species.scientific_name, ConfidenceLevel.LOW)

    # Stufe 4: Keine botanische Information — KS-Aufruf entfaellt,
    # Antwort kommt regelbasiert aus Backend-Fallback (REQ-031 §1)
    return (None, species.scientific_name, ConfidenceLevel.NONE)
```

Das `QuestionContext`-Objekt wird um zwei optionale Felder erweitert:

```python
class QuestionContext(BaseModel):
    species: str | None              # ks-aufloesbar (global, Genus, Family) oder None
    cultivar_hint: str | None        # NEU (ADR-002): tenant-eigener Name als unstrukturierter Hint
    confidence: ConfidenceLevel      # NEU (ADR-002): high | medium | low | none
    phase: str | None
    substrate: str | None
    ec: float | None
    ph: float | None
    # ... bestehende Felder
```

**Verhalten im Knowledge Service:** Der KS wird nicht angepasst — er sieht weiterhin ein `species`-Feld und macht seinen normalen Hybrid-Search. Das `cultivar_hint`-Feld wird in den LLM-Prompt eingebettet (`"Der Anwender bezieht sich auf eine eigene Sortennote namens '{cultivar_hint}'. Behandle die Antwort als allgemeine Information zu '{species}', erwähne nicht, dass die Sortennote nicht in der Datenbank ist."`).

**UI-Wirkung:** Antworten mit `confidence: low` werden in der UI mit einem sichtbaren Badge versehen (REQ-031 §6, neu unten). Anwender wird informiert, dass die Antwort allgemein und nicht sortenspezifisch ist.
<!-- /Quelle: ADR-002 / W-006 -->

### 4.3 AiAssistantService (Orchestrierung)

Service-Klasse in `src/backend/app/domain/services/ai_assistant_service.py`. Methoden:

| Methode | Zweck |
|---------|-------|
| `get_tips(tenant_key, context_type, context_key, user_key)` | Tipp-Karten fuer Plant/Run, Cache-First, Fallback regelbasiert |
| `get_daily_tip(tenant_key, user_key)` | Ein einziger Tipp fuer das Dashboard, on-first-load lazy, Cache bis Mitternacht Tenant-Zeitzone |
| `explain(tenant_key, user_key, *, subject_type, subject_key, question_template_id)` | "Warum?"-Antwort fuer eine konkrete Aufgabe / Erinnerung / Phasentransition |
| `chat(tenant_key, user_key, message, conversation_key=None, ...)` | Chat-Turn (SSE-streaming) |
| `dismiss_tip(tip_key, ...)` / `mark_tip_acted_on(tip_key, ...)` | UI-Aktionen |
| `delete_conversation(conversation_key, ...)` | DSGVO Art. 17, sofortige Loeschung |
| `configure_provider(...)` / `list_providers(...)` | Provider-CRUD |

Vor jedem Aufruf laeuft die Reihenfolge:

1. `FeatureGuard.require_ai_enabled(tenant_key)` — wirft `AiDisabledError` (HTTP 403) wenn Stufe 1 oder 2 deaktiviert
2. `ConsentGuard.require_consent(user_key, purpose)` — wirft `ConsentRequiredError` (HTTP 403, mit `consent_purpose` im Body) wenn benoetigter Consent fehlt
3. `AuditLogger.start(...)` — bereitet Audit-Eintrag vor (status=pending)
4. Eigentliche Logik — Cache-Check, KontextBuild, KnowledgeService-Aufruf
5. `AuditLogger.complete(...)` — schreibt Audit-Eintrag final

### 4.4 TipEngine (ueberarbeitet)

Wesentliche Aenderungen:

- Default-Cache-TTL bleibt 4h (Redis) / 24h (ArangoDB).
- RAG-Retrieval erfolgt nicht mehr lokal, sondern via `KnowledgeServiceAdapter.ask(...)`.
- Prompt fuer "Generiere 2-4 Tipps" wandert in den `PromptEngine` des Knowledge Service ALS NEUER PROMPT-TYP (`"tips"`) — die Spec dafuer liegt im Knowledge-Service-Repo, REQ-031 verlangt nur den Endpunkt-Vertrag.
- Fallback-Logik (regelbasiert) bleibt im Backend, weil sie Tenant-Daten kennt.

**`get_daily_tip(...)`** ist eine neue Methode mit eigenem Cache-Schluessel `ai:daily-tip:{tenant_key}:{date_local}` (TTL: bis Mitternacht Tenant-Zeitzone). Sie waehlt einen Tenant-spezifischen Aspekt:

1. Hat der Tenant Pflanzen mit auffaelligen Werten (EC out-of-range, VPD ausser Ziel, ueberfaellige Tasks)? -> warning-Tipp
2. Sonst: Hat eine Pflanze einen kommenden Phasenuebergang? -> milestone-Tipp
3. Sonst: Saison-Tipp basierend auf User-Locale + Hemisphaere
4. Sonst: Allgemeiner Beginner-/Optimierungs-Tipp aus der Knowledge Base

### 4.5 ExplainEngine (NEU)

Neue Komponente `src/backend/app/domain/engines/ai_explain_engine.py`. Generiert "Warum?"-Antworten zu konkreten Subjekten (Task / Reminder / Phase-Transition / FeedingEvent).

Ein **Question-Template** ist ein YAML-Eintrag in `spec/knowledge/explain-templates/` mit:

```yaml
- id: care_reminder_watering
  applies_to: care.watering
  question_de: |
    Warum sollte ich {{plant_display}} jetzt giessen?
    Pflanze: {{species}} in Phase {{phase}}, Substrat {{substrate}}.
    Letzter Giesstermin: {{last_watering_iso}}.
    Aktuelles Substratgewicht-Delta: {{substrate_weight_delta}}%.
  question_en: |
    Why should I water {{plant_display}} now?
    Plant: {{species}} in phase {{phase}}, substrate {{substrate}}.
    Last watering: {{last_watering_iso}}.
    Current substrate weight delta: {{substrate_weight_delta}}%.
  expected_length_words_max: 80
```

Templates sind versioniert und werden mit dem Backend-Code mitgeliefert. Vorteil: kuratiertes, deterministisches Frageschema; das LLM bekommt kompakte, klare Fragen statt Freitext.

`ExplainEngine.explain(...)`:

1. Template laden anhand `question_template_id` (z. B. `care_reminder_watering`).
2. Slots aus dem Backend-Kontext fuellen (Plant, Phase, History).
3. KnowledgeService `/ask` aufrufen mit `prompt_language` = User-Locale.
4. Antwort cachen unter `ai:explain:{tenant_key}:{template_id}:{plant_state_hash}` (TTL 24h).
5. Audit-Log mit `endpoint=explain`, `context_type=...`, etc.

### 4.6 Celery-Tasks

| Task | Schedule | Zweck |
|------|----------|-------|
| `ai.refresh_planting_run_tips` | taeglich 06:00 UTC | Generiert Tipps fuer alle aktiven Runs aller Tenants mit `ai_features_enabled=true` |
| `ai.cleanup_expired_conversations` | taeglich 02:30 UTC | Entfernt `ai_conversations` mit `expires_at < now()` |
| `ai.cleanup_expired_audit_log` | taeglich 02:35 UTC | Entfernt `ai_audit_log` aelter als 30 Tage |
| `ai.health_check_providers` | alle 15 Minuten | Health-Check fuer alle aktiven Provider, exportiert Prometheus-Gauge `ai_provider_healthy{provider_key=...}` |
| `ai.knowledge_service_ingest` | woechentlich Sonntag 03:00 UTC | Triggert `POST /ingest` am Knowledge Service zur Aktualisierung der Stammdaten-Snapshots |

### 4.7 Provider-Konfiguration und API-Key-Schutz

API-Keys werden mit Fernet (symmetrisch, K8s-Secret als Master-Key) verschluesselt in `api_key_encrypted` abgelegt. Schluessel werden in keinem Log, in keiner Fehlermeldung und in keinem Audit-Eintrag erwaehnt — auch nicht teilweise. Der `display_name` darf den Provider-Namen enthalten, NICHT aber Schluesselfragmente.

## 5. API-Endpunkte (FastAPI, Backend)

Alle KI-Endpunkte sind unter dem Pfadpraefix `/api/v1/.../ai/` erreichbar. Sie liefern HTTP 404 zurueck, wenn `AI_FEATURES_ENABLED=false`. Sie liefern HTTP 403 mit Body `{ "detail": "ai.disabled_for_tenant" }`, wenn die Tenant-Stufe deaktiviert ist. Sie liefern HTTP 403 mit Body `{ "detail": "consent_required", "consent_purpose": "..." }` bei fehlendem Consent.

### 5.1 Tenant-scoped (`/api/v1/t/{tenant_slug}/ai/`)

**Tipp-Karten:**

| Methode | Pfad | Beschreibung | Berechtigung | Consent |
|---------|------|-------------|--------------|---------|
| `GET` | `/tips` | Aktuelle Tipps fuer Kontext (`?context_type=&context_key=`) | Viewer, Grower, Admin | `ai_tenant_data_access` |
| `POST` | `/tips/refresh` | Tipps neu generieren (force) | Grower, Admin | `ai_tenant_data_access` |
| `POST` | `/tips/{key}/dismiss` | Tip wegklicken | Viewer, Grower, Admin | — |
| `POST` | `/tips/{key}/acted-on` | Tip als umgesetzt markieren | Grower, Admin | — |

**Tipp des Tages (NEU):**

| Methode | Pfad | Beschreibung | Berechtigung | Consent |
|---------|------|-------------|--------------|---------|
| `GET` | `/daily-tip` | Ein einziger personalisierter Tipp fuer Dashboard | Viewer, Grower, Admin | `ai_tenant_data_access` |
| `POST` | `/daily-tip/dismiss` | Heutigen Daily-Tip wegklicken | Viewer, Grower, Admin | — |

**"Warum?" / Explain (NEU):**

| Methode | Pfad | Beschreibung | Berechtigung | Consent |
|---------|------|-------------|--------------|---------|
| `POST` | `/explain` | Erklaert eine konkrete Empfehlung. Body: `{ subject_type: "task"|"reminder"|"phase_transition"|"feeding_event", subject_key: "...", question_template_id: "..." }` | Viewer, Grower, Admin | `ai_tenant_data_access` |

**Chat (unveraendert, ergaenzt um `language`):**

| Methode | Pfad | Beschreibung | Berechtigung | Consent |
|---------|------|-------------|--------------|---------|
| `GET` | `/conversations` | Liste der Konversationen | Grower, Admin | `ai_tenant_data_access` |
| `POST` | `/conversations` | Neue Konversation starten (`{ context_type, context_key?, language? }`) | Grower, Admin | `ai_tenant_data_access` |
| `GET` | `/conversations/{key}` | Konversation laden | Grower, Admin | `ai_tenant_data_access` |
| `POST` | `/conversations/{key}/messages` | Nachricht senden (SSE Streaming) | Grower, Admin | `ai_tenant_data_access` (+ ggf. `ai_cloud_processing`) |
| `DELETE` | `/conversations/{key}` | DSGVO Art. 17, sofortige Loeschung | Grower, Admin | — |

**Provider-Konfiguration (Tenant-eigene Keys):**

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/providers` | Provider auflisten (Tenant + System-Defaults) | Grower, Admin |
| `POST` | `/providers` | Neuen Provider konfigurieren | Admin |
| `PUT` | `/providers/{key}` | Aktualisieren | Admin |
| `DELETE` | `/providers/{key}` | Soft-Delete | Admin |
| `GET` | `/providers/{key}/health` | Health testen (proxied an KnowledgeService) | Grower, Admin |

**Tenant-Settings (NEU):**

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/settings` | Aktuelle KI-Einstellungen des Tenants | Viewer, Grower, Admin |
| `PUT` | `/settings` | KI-Einstellungen aendern (`ai_features_enabled`, `ai_default_provider_key`, `ai_allow_cloud_providers`, `ai_daily_tip_enabled`) | Admin |

### 5.2 Globale Endpunkte

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/api/v1/ai/system-providers` | System-Default-Provider verwalten | Platform-Admin |
| `POST` | `/api/v1/ai/system-providers` | Anlegen | Platform-Admin |
| `PUT` | `/api/v1/ai/system-providers/{key}` | Aktualisieren | Platform-Admin |
| `POST` | `/api/v1/ai/knowledge-service/ingest` | Manuelles Reingest des Knowledge Service ausloesen | Platform-Admin |
| `GET` | `/api/v1/ai/knowledge-service/health` | Health des Knowledge Service | Platform-Admin |

### 5.3 Light-Modus Endpunkte (REQ-027)

Im Light-Modus existieren KEINE Tenants und kein User-Login. KI-Nutzung beschraenkt sich auf rein wissensbezogene Anfragen ohne Personenbezug:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/api/v1/public/ai/ask` | Frei formulierte Frage gegen die Wissensbasis. KEIN Tenant-Kontext, KEIN extended_context. Mit Rate-Limit pro IP (10/min). | keine |
| `GET` | `/api/v1/public/ai/health` | Knowledge-Service-Verfuegbarkeit | keine |

`/api/v1/public/ai/ask` setzt im Knowledge-Service-Aufruf strikt `context = null`. Antworten enthalten weder Tenant- noch User-bezogene Daten. Die Glossar-Endpoint aus REQ-035 baut auf demselben Light-Pfad auf.

### 5.4 Streaming-Response (SSE)

Der Chat-Endpunkt `POST /conversations/{key}/messages` liefert die LLM-Antwort als Server-Sent-Events (`text/event-stream`) Token-fuer-Token. Streaming ist transparent durchgereicht — sowohl der Knowledge Service als auch die LLM-Adapter unterstuetzen Streaming. Andere Endpunkte (`/tips`, `/daily-tip`, `/explain`) liefern komplette JSON-Antworten mit Spinner-Anzeige im Frontend.

**Begruendung der UX-Entscheidung:** Tipp-Karten und "Warum?"-Antworten sind kurz und werden gecacht — Spinner ist akzeptabel und macht die Antwort kompakter. Chat-Antworten sind potentiell laenger und profitieren von Streaming.

### 5.5 Antwortstruktur

Jede LLM-Antwort des Backends folgt einem gemeinsamen Schema:

```json
{
  "answer_text": "string",
  "sources": [
    { "source_key": "string", "source_type": "string", "title": "string", "score": 0.87, "language": "de" }
  ],
  "language": "de",
  "language_mismatch_warning": false,
  "uses_tenant_data": true,
  "uses_cloud_provider": false,
  "confidence": "high",                              // ADR-002: high | medium | low | none
  "fallback_species": null,                          // ADR-002: bei tenant-Species der genutzte Fallback-Wert
  "cultivar_hint": null,                             // ADR-002: tenant-eigener Sortenname (Anzeige im UI)
  "model_name": "gemma3:12b",
  "provider_type": "ollama",
  "kb_version": "ks-1.4.2-idx-20260420",
  "generated_at": "2026-04-25T10:15:00Z"
}
```

Frontend rendert das mit einer einheitlichen `<AIResponse>`-Komponente (s. §6.1).

## 6. Frontend-Komponenten (React/MUI)

### 6.1 `<AIResponse>` (NEU, gemeinsame Huelle)

Pfad: `src/frontend/src/components/ai/AIResponse.tsx`

Pflicht-Wrapper fuer alle KI-generierten Inhalte (Tipps, Daily Tip, "Warum?"-Antworten, Chat-Bubbles). Eigenschaften:

- **KI-Badge oben links:** kleiner Chip mit Icon `SparkleIcon` und Text "KI-generiert" (i18n `common.ai.badge`). Tooltip beim Hover: Modell + Provider.
- **Sprach-Badge** (nur bei `language_mismatch_warning=true`): Hinweis "Antwort auf Deutsch — englische Wissensbasis im Aufbau".
- **Tenant-Daten-Indikator** (nur bei `uses_tenant_data=true`): kleiner Chip "Nutzt deine Pflanzendaten" mit Tooltip-Erklaerung und Link zu Datenschutz-Einstellungen.
- **Cloud-Provider-Indikator** (nur bei `uses_cloud_provider=true`): Chip "Verarbeitet via Cloud-Provider [Name]".
- **Confidence-Badge (ADR-002, nur bei `confidence='low'`):** Sichtbarer Chip "Allgemeine Information" mit Tooltip: "Diese Antwort basiert auf allgemeiner Datenlage zu {fallback_species}, nicht auf deiner spezifischen Sorte '{cultivar_hint}'. Tenant-eigene Sorten haben keine eigene Wissensbasis." — kein Blocker, nur Information. <!-- W-006 -->
- **Antwort-Body:** Kinder-Komponente.
- **Quellen-Footer:** Aufklappbarer `Accordion` mit Liste der Quellen-Chunks (Titel, Kategorie, Score, Sprach-Flag). Bei Beginner-Erfahrungsstufe zugeklappt, bei Expert offen (REQ-021).
- **Disclaimer-Footer:** Kleiner grauer Text "KI-Antworten koennen fehlerhaft sein. Bei kritischen Entscheidungen Quellen pruefen." (i18n `common.ai.disclaimer`).

Alle KI-Antworten in der App **muessen** durch diese Huelle gerendert werden. Code-Reviews lehnen KI-Inhalte ohne `<AIResponse>`-Wrapper ab.

### 6.2 `<TipCardsPanel>` (ueberarbeitet)

Pfad: `src/frontend/src/components/ai/TipCardsPanel.tsx`

Wesentliche Aenderungen ggu. v1.0:

- Jede Karte ist eine `<AIResponse>` mit kompaktem Body.
- Erfahrungsstufe Beginner: Quellen-Footer ist eingeklappt und Karten sind kompakter (max 2 statt 4).
- "Mehr erfahren"-Button startet Chat-Drawer mit dem aktiven Tip als Initial-Kontext.
- Sichtbarkeit gebunden an Stufe-2-Toggle (Tenant-Setting). Wenn Tenant `ai_features_enabled=false`, wird das Panel komplett ausgeblendet (kein leerer Container).

### 6.3 `<DailyTipCard>` (NEU)

Pfad: `src/frontend/src/components/ai/DailyTipCard.tsx`

Eigene Karte am Top des Dashboards (REQ-009), eigene Position (nicht im TipCardsPanel-Grid):

- Laedt einmalig pro Session via `GET /api/v1/t/{slug}/ai/daily-tip`.
- Wird durch `<AIResponse>` gerendert (KI-Badge sichtbar).
- "Schliessen"-Button (X) ruft `POST /daily-tip/dismiss` und blendet die Karte fuer den Rest des Tages aus (Persistenz via API + Local-Storage).
- Empty-State (wenn KI-deaktiviert oder Knowledge-Service down): nicht sichtbar.
- Sichtbarkeit: ab Beginner.

### 6.4 `<WhyButton>` und `<WhyDrawer>` (NEU)

Pfade:
- `src/frontend/src/components/ai/WhyButton.tsx`
- `src/frontend/src/components/ai/WhyDrawer.tsx`

`<WhyButton>` ist ein kleiner Icon-Button (`HelpOutlineIcon`) mit Tooltip "Warum?". Wird auf folgenden Komponenten platziert:

| Komponente | Template-ID | Quelle (REQ) |
|------------|-------------|--------------|
| `TaskCard` (Aufgabenliste) | `task_explain` | REQ-006 |
| `CareReminderCard` (Pflege-Dashboard) | `care_reminder_{type}` (z. B. `care_reminder_watering`) | REQ-022 |
| `PhaseTransitionSuggestionCard` | `phase_transition_explain` | REQ-003 |
| `FeedingEventSuggestionCard` | `feeding_event_explain` | REQ-004 |

Klick oeffnet `<WhyDrawer>` (rechter MUI Drawer, 360px). Drawer:

1. Zeigt Spinner mit Text "KI denkt nach…" waehrend `POST /ai/explain` laeuft.
2. Rendert Antwort als `<AIResponse>`.
3. Footer: "Diese Empfehlung folgen" (Primary-Action wenn anwendbar) und "Schliessen".

Sichtbarkeit gebunden an Stufe-2 + Stufe-3 (Consent). Wenn Stufe-2 false: Button unsichtbar. Wenn Stufe-2 true aber Consent fehlt: Button sichtbar, Klick oeffnet Consent-Dialog statt Drawer.

### 6.5 `<AiChatDrawer>` (ueberarbeitet)

Wesentliche Aenderungen:

- Bubbles werden durch `<AIResponse>` gerendert.
- Im Footer: aktueller Provider + Modell + KB-Version (Chips).
- Wenn `language_mismatch_warning` in der letzten Antwort: persistenter Banner oben "Antwort in Deutsch — englische Wissensbasis im Aufbau".
- Cloud-Provider-Wechsel (z. B. Default ist Ollama, User waehlt manuell OpenAI fuer eine Frage): Confirm-Dialog "Diese Frage geht an [Provider] in [Land]. Fortfahren?" mit Persist-Option "Diese Wahl fuer diese Konversation merken".

### 6.6 `<AiProviderSettingsPage>` (ueberarbeitet)

Tab in `AccountSettingsPage`. Aenderungen:

- Neue Sektion oben: **Tenant-KI-Einstellungen** (nur fuer Admin sichtbar):
  - Toggle `ai_features_enabled`
  - Toggle `ai_allow_cloud_providers`
  - Toggle `ai_daily_tip_enabled`
  - Auswahl `ai_default_provider_key`
- Neue Sektion: **Knowledge-Service-Status** (nur Platform-Admin):
  - URL, Health, Index-Version, letzter Reingest
- Provider-CRUD wie v1.0, mit Hinweis dass Cloud-Provider erst bei `ai_allow_cloud_providers=true` waehlbar sind.

### 6.7 `<AiConsentDialog>` (erweitert)

Drei Consent-Typen, wahlweise einzeln oder kombiniert:

- `ai_tenant_data_access` — Pflanzendaten als Kontext
- `ai_cloud_processing` — Cloud-Provider statt lokal

Dialog beschreibt jeden Punkt einzeln, mit Checkboxen pro Punkt. Ablehnung eines Punkts blockiert nur die entsprechenden Endpoints, andere bleiben nutzbar. Einwilligungen werden als `ConsentRecord` (REQ-025) persistiert.

### 6.8 Integration in bestehende Seiten

| Seite | Komponente | Bedingung |
|-------|-----------|-----------|
| `Dashboard` (REQ-009) | `DailyTipCard` (oben) + `TipCardsPanel` (allgemein) | Stufe 1+2 aktiv |
| `PlantingRunDetailPage` | `TipCardsPanel` (kontext-spezifisch) | Stufe 1+2 aktiv |
| `PlantInstanceDetailPage` | `TipCardsPanel` (kontext-spezifisch) | Stufe 1+2 aktiv |
| `Pflege-Dashboard` (REQ-022) | `<WhyButton>` auf jeder `CareReminderCard` | Stufe 1+2 aktiv |
| `Aufgabenliste` (REQ-006) | `<WhyButton>` auf jeder KI-erzeugten oder workflow-erzeugten Task | Stufe 1+2 aktiv |
| `MainLayout` | FAB / AppBar-Button fuer `AiChatDrawer` | Stufe 1+2 aktiv und User Intermediate+ |
| `AccountSettingsPage` | Tab "KI-Assistent" (`AiProviderSettingsPage`) | Stufe 1 aktiv |

## 7. DSGVO & Datenschutz (REQ-025)

### 7.1 Consent-Anforderungen (revidiert)

| Endpoint-Klasse | Consent | Begruendung |
|-----------------|---------|-------------|
| Wissensfrage ohne Tenant-Kontext (Light-Modus, Glossar via REQ-035) | Keiner | Frage und Antwort enthalten keine personenbezogenen Daten |
| Tipp-Karten, Daily Tip, "Warum?"-Buttons, Chat | `ai_tenant_data_access` | Antwort wird auf Basis der Pflanzdaten des Tenants generiert |
| Nutzung eines Cloud-Providers | `ai_cloud_processing` (zusaetzlich) | Drittland-Datenuebermittlung, nichtlokales Inference-Backend |

Local-Provider (Ollama, llamacpp) erfordern KEIN `ai_cloud_processing`.

### 7.2 Datensparsamkeit im Knowledge-Service-Prompt

Der `context`-Block, der an den Knowledge Service uebermittelt wird, darf NICHT enthalten:

- Tenant-Name oder Tenant-Slug
- Nutzername, E-Mail, Telefonnummer, Adresse
- IP-Adresse oder Geraete-Identifikatoren
- Freitext-Kommentare aus PlantDiaryEntries (potentielle PII)

Erlaubt sind:

- Wissenschaftlicher Pflanzenname
- Phase und Phasen-Tag
- Substrat-Typ
- Numerische Messwerte (EC, pH, VPD)
- Aggregierte Zaehler ("3 ueberfaellige Tasks")

Diary-Eintraege werden nur als anonymisierte Aggregate ("zuletzt vor 5 Tagen gegossen") in den `extended_context` aufgenommen — niemals der Originaltext.

### 7.3 Consent-Widerruf

Bei Widerruf:

- `ai_tenant_data_access` widerrufen: Tipps werden ausgeblendet, "Warum?"-Buttons unsichtbar, Chat verweigert neue Nachrichten (`HTTP 403`). Bestehende Konversationen bleiben sichtbar (kein Personenbezug-Verlust durch Loeschung). Caches werden invalidiert.
- `ai_cloud_processing` widerrufen: Cloud-Provider werden bis zum naechsten Browser-Refresh aus der Auswahl entfernt; aktive SSE-Streaming-Antwort wird unterbrochen.

### 7.4 Retention (NFR-011)

| Datentyp | Default-Retention | Cleanup |
|----------|------------------|---------|
| `ai_conversations` | 90 Tage (Min: 30) | `ai.cleanup_expired_conversations` taeglich |
| `ai_tip_cache` | 7 Tage (`valid_until`) | per Cache-TTL |
| `ai_audit_log` | 30 Tage (Min: 14) | `ai.cleanup_expired_audit_log` taeglich |
| `ai_provider_configs` | Permanent | manuelles Loeschen |
| Knowledge-Service `knowledge_chunks` | Permanent (kein Personenbezug) | Reingest ueberschreibt |

### 7.5 DSGVO Art. 17 (Loeschrecht)

- `DELETE /conversations/{key}` loescht sofort.
- DSGVO-Loeschung eines Users (REQ-025): kaskadiert auf alle `ai_conversations`, `ai_tip_cache` (sofern `dismissed_by` oder `tenant_key` zum User-Tenant gehoert), `ai_audit_log` (User-Eintraege werden anonymisiert: `user_key` -> null, Hashes bleiben).

### 7.6 Auskunftsrecht (Art. 15)

Auskunftsexport enthaelt:

- Alle `ai_conversations` des Users (inkl. Messages)
- Alle `ai_tip_cache`-Eintraege, die der User dismissed oder als acted-on markiert hat
- Alle `ai_audit_log`-Eintraege des Users der letzten 30 Tage (gehasht, ohne Frage-/Antwort-Klartext)
- Erteilte und widerrufene `ConsentRecord` zu `ai_*` Purposes

KI-generierte Tipps gelten als abgeleitete Daten (Art. 4 Nr. 1 DSGVO eng ausgelegt). Sie werden im Export NUR aufgefuehrt, wenn der User explizit auf sie reagiert hat (dismissed/acted-on); sonst sind sie ephemerer Cache.

## 8. Helm Chart Erweiterungen

### 8.1 Knowledge Service als eigenes Helm-Release

Der Knowledge Service hat ein eigenes Helm-Chart `helm/kamerplanter-knowledge-service/`. Es wird unabhaengig vom Backend ausgerollt und kann separat skaliert werden. Backend-Werte:

```yaml
# helm/kamerplanter/values.yaml (Backend-Controller)
controllers:
  main:
    containers:
      main:
        env:
          AI_FEATURES_ENABLED: "false"            # Stufe 1 — Operator
          AI_KNOWLEDGE_SERVICE_URL: "http://kamerplanter-knowledge-service:8090"
          AI_KNOWLEDGE_SERVICE_TIMEOUT_S: "60"
          AI_PUBLIC_RATE_LIMIT_PER_MIN: "10"      # Light-Modus public endpoint
```

### 8.2 Optional: Ollama-Pod

Bleibt wie in v1.0 (siehe §8.1 v1.0), aber im Knowledge-Service-Chart anstatt im Backend-Chart:

```yaml
# helm/kamerplanter-knowledge-service/values.yaml
ollama:
  enabled: false
  image: { repository: ollama/ollama, tag: latest }
  persistence: { models: { size: 30Gi } }
  resources:
    requests: { cpu: "1", memory: 8Gi }
    limits: { memory: 16Gi }
```

Modellempfehlungen und Hardware-Tabellen aus v1.0 §1.1.1 bleiben in Kraft, aber der Default-LLM ist jetzt `gemma3:12b` statt `llama3.2:3b` (siehe §1.2). Fuer ressourcenschwache Umgebungen bleibt `gemma3:4b` der empfohlene Fallback.

### 8.3 Embedding- und Reranker-Service

Bereits im Cluster vorhanden:
- `kamerplanter-ki-embedding-service:8080` (multilingual-e5-large, ONNX)
- `kamerplanter-ki-reranker-service:8081` (bge-reranker-v2-m3)

Beide werden vom Knowledge Service angesprochen, NICHT vom Backend. Backend muss sie nicht kennen.

### 8.4 pgvector

Lebt in der Knowledge-Service-Postgres-Instanz, NICHT mehr im TimescaleDB des Backends. TimescaleDB des Backends wird damit von KI-Last entkoppelt.

## 9. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Auth-Anforderungen gemaess REQ-023 v1.7 (Auth) und REQ-024 v1.4 (RBAC).

**Standardregel:** Alle Tenant-scoped Endpunkte erfordern JWT + Tenant-Mitgliedschaft. Light-Modus-Endpunkte sind ohne Auth, aber rate-limited.

| Ressource/Endpoint-Gruppe | Viewer | Grower | Admin | Platform-Admin |
|---------------------------|--------|--------|-------|----------------|
| Tipps lesen / dismiss / acted-on | Ja | Ja | Ja | — |
| Tipps refresh | — | Ja | Ja | — |
| Daily Tip | Ja | Ja | Ja | — |
| Explain | Ja | Ja | Ja | — |
| Chat | — | Ja | Ja | — |
| Chat loeschen | — | Ja (eigene) | Ja (alle im Tenant) | — |
| Provider lesen | — | Ja | Ja | — |
| Provider konfigurieren | — | — | Ja | — |
| Tenant-KI-Settings lesen | Ja | Ja | Ja | — |
| Tenant-KI-Settings schreiben | — | — | Ja | — |
| System-Provider verwalten | — | — | — | Ja |
| Knowledge-Service-Reingest / Health | — | — | — | Ja |
| `/api/v1/public/ai/ask` | Anonym (Light-Modus) | — | — | — |

**ExpertiseLevel-Einschraenkungen (REQ-021):**

- **Beginner:** Nur `TipCardsPanel` + `DailyTipCard` + `<WhyButton>` (Antworten in einfacher Sprache, Quellen eingeklappt). Kein Chat-Zugang. Provider-Settings nicht sichtbar.
- **Intermediate:** Alle Beginner-Features + `AiChatDrawer` + Provider-Settings (lesen).
- **Expert:** Alle Features. Quellen sind in `<AIResponse>` per Default ausgeklappt.

## 10. Abhaengigkeiten

### 10.1 Direkte Abhaengigkeiten (MUSS vorhanden sein)

- **REQ-001** v5.0 — Species/Cultivar als Indexierungs-Quelle fuer Knowledge Service
- **REQ-011** v1.0 — Adapter-Pattern als Vorbild
- **REQ-023** v1.7 — Auth + Service Accounts (letztere fuer REQ-033)
- **REQ-024** v1.4 — Mandantenverwaltung + Permission-Matrix
- **REQ-025** v1.0 — DSGVO + ConsentRecord
- **NFR-007** — LLM-Sicherheit (Prompt-Injection-Schutz, PII-Stripping)
- **NFR-011** — Retention

### 10.2 Optionale Abhaengigkeiten (Synergie)

- **REQ-003**, **REQ-004**, **REQ-005**, **REQ-006**, **REQ-010**, **REQ-013**, **REQ-022** — Liefern Tenant-Kontext fuer Tipp- und Explain-Engines.
- **REQ-009** (Dashboard) — Hostet `DailyTipCard` und Allgemein-`TipCardsPanel`.
- **REQ-021** — Bestimmt UI-Ausspielung pro Erfahrungsstufe.
- **REQ-027** — Light-Modus-Endpunkte.
- **REQ-029** — Bilderkennung; ihr Ergebnis kann optional als `extended_context` in einer `/explain`- oder Chat-Anfrage genutzt werden.
- **REQ-030** — Notifications; Tipps koennen optional als Notification verschickt werden.

### 10.3 REQs, die REQ-031 v2.0 voraussetzen

- **REQ-033** v1.1 (MCP-Server) — `search_plant_knowledge` Tool ruft denselben Knowledge Service.
- **REQ-035** (Glossar) — Glossar-Endpoint nutzt Knowledge-Service ueber dieselbe Adapter-Schicht.
- **REQ-036** (Diagnose) — Diagnose-Engine nutzt Knowledge-Service ueber dieselbe Adapter-Schicht.

### 10.4 Systemabhaengigkeiten

- **Knowledge Service** (`src/knowledge-service/`) — eigenstaendiger FastAPI-Microservice
- **PostgreSQL 17 + pgvector 0.8** — im Knowledge-Service-Pod
- **Embedding-Service** (`kamerplanter-ki-embedding-service:8080`)
- **Reranker-Service** (`kamerplanter-ki-reranker-service:8081`)
- **ArangoDB** — Persistenz von Provider-Configs, Conversations, Tip-Cache, Audit-Log
- **Redis** — Hot-Cache fuer Tipps und Daily-Tip
- **Celery + Redis** — Periodische Tasks
- **httpx** — HTTP-Client gegen Knowledge Service

### 10.5 Externe Abhaengigkeiten (alle optional)

- **Ollama** — lokale LLM-Inference
- **Anthropic Claude API** — Cloud
- **OpenAI / OpenAI-kompatible APIs** — Cloud (LM Studio, vLLM, Together AI, Mistral AI)

## 11. Akzeptanzkriterien

### Definition of Done (DoD)

- [ ] **KnowledgeServiceAdapter** im Backend implementiert und alle KI-Endpunkte sprechen NUR ueber diesen Adapter mit dem Knowledge Service (kein direkter pgvector-Zugriff im Backend).
- [ ] **Drei-Stufen-Toggle** funktioniert: `AI_FEATURES_ENABLED=false` -> alle Endpunkte 404; Tenant-Setting false -> 403 mit `ai.disabled_for_tenant`; fehlender Consent -> 403 mit `consent_required` und `consent_purpose`.
- [ ] **TipCardsPanel** zeigt Tipps fuer Plant/Run, alle gerendert in `<AIResponse>` mit Quellen-Footer.
- [ ] **DailyTipCard** auf Dashboard generiert genau einen Tipp pro Tag pro Tenant, Cache bis Mitternacht Tenant-Zeitzone.
- [ ] **WhyButton + WhyDrawer** auf TaskCard, CareReminderCard, PhaseTransitionSuggestionCard, FeedingEventSuggestionCard funktional, mit kuratierten Frage-Templates.
- [ ] **AiChatDrawer** ueberarbeitet: nutzt KnowledgeServiceAdapter, SSE-Streaming, neue `<AIResponse>`-Huelle.
- [ ] **AiProviderSettingsPage** zeigt neue Tenant-KI-Settings-Sektion.
- [ ] **AiConsentDialog** unterstuetzt drei Consent-Typen (`ai_tenant_data_access`, `ai_cloud_processing`).
- [ ] **Light-Modus-Endpunkte** (`/api/v1/public/ai/*`) liefern Wissensantworten ohne Tenant-Kontext, mit Rate-Limit pro IP.
- [ ] **Multilingual-Felder** (`language`, `language_mismatch_warning`) in allen Antworten gesetzt; UI rendert Sprach-Badge.
- [ ] **Audit-Log** (`ai_audit_log`) fuer jeden KI-Aufruf mit gehashter Frage; KEIN Klartext.
- [ ] **PII-Stripping** im Context-Builder (Test: Tenant-Name, Nutzername, Diary-Freitext erscheinen NIE im Knowledge-Service-Aufruf).
- [ ] **Graceful Degradation**: Knowledge Service nicht erreichbar -> Backend liefert regelbasierte Fallback-Tipps und HTTP 200 (statt 5xx); im Audit-Log status=`knowledge_service_error`.
- [ ] **Retention-Tasks**: `cleanup_expired_conversations`, `cleanup_expired_audit_log` laufen taeglich und entfernen abgelaufene Eintraege.
- [ ] **Reingest-Task**: `ai.knowledge_service_ingest` triggert wochentlich `POST /ingest` am Knowledge Service.
- [ ] **i18n**: Alle Texte in DE und EN, inkl. KI-Badge, Disclaimer, Tenant-Daten-Indikator, Cloud-Provider-Indikator, Consent-Dialog-Texte.
- [ ] **Testabdeckung Backend**: Unit-Tests fuer Engines, Services, Adapter (mit gemocktem Knowledge Service); Integrationstest mit echtem Knowledge Service in Test-Compose.
- [ ] **Testabdeckung Frontend**: Vitest-Tests fuer `<AIResponse>`, `<DailyTipCard>`, `<WhyButton>`, ueberarbeitete `<TipCardsPanel>`.

### Testszenarien

**Szenario 1: Drei-Stufen-Toggle (Stufe 1 deaktiviert)**
```
GIVEN: AI_FEATURES_ENABLED=false
WHEN: GET /api/v1/t/demo/ai/tips
THEN:
  - HTTP 404 Not Found
  - Frontend rendert TipCardsPanel nicht (kein leerer Container)
  - kein Audit-Eintrag (Endpoint existiert quasi nicht)
```

**Szenario 2: Drei-Stufen-Toggle (Stufe 2 deaktiviert)**
```
GIVEN: AI_FEATURES_ENABLED=true
  AND: tenant.settings.ai_features_enabled=false
WHEN: GET /api/v1/t/demo/ai/tips
THEN:
  - HTTP 403 Forbidden, body: { detail: "ai.disabled_for_tenant" }
  - Audit-Eintrag mit status=denied
  - Frontend rendert Hinweis "KI ist fuer diesen Tenant nicht aktiviert"
```

**Szenario 3: Wissensfrage im Light-Modus**
```
GIVEN: KAMERPLANTER_MODE=light
  AND: AI_FEATURES_ENABLED=true
  AND: Knowledge Service verfuegbar
WHEN: POST /api/v1/public/ai/ask  body={ "question": "Was ist VPD?" }
THEN:
  - HTTP 200 mit AnswerResponse
  - context an Knowledge Service ist null (kein Tenant-Kontext)
  - response.uses_tenant_data == false
  - response.uses_cloud_provider == false (Default-Provider lokal)
  - kein User-Login noetig
```

**Szenario 4: Tipp-Karten mit Tenant-Kontext und Default-Provider Ollama**
```
GIVEN: Tenant "home" hat ai_features_enabled=true
  AND: User "anna" hat Consent ai_tenant_data_access erteilt
  AND: PlantingRun "tomate-2026" in Phase flowering, EC=1.8, pH=6.2
  AND: Default-Provider ist ollama:gemma3:12b (lokal)
WHEN: GET /api/v1/t/home/ai/tips?context_type=planting_run&context_key=tomate-2026
THEN:
  - HTTP 200, 2-4 Tipps
  - jeder Tipp hat sources mit source_key/source_type/score/language
  - response.uses_tenant_data == true
  - response.uses_cloud_provider == false
  - <AIResponse>-Huelle zeigt Tenant-Daten-Indikator
  - Audit-Log: status=ok, uses_tenant_data=true, uses_cloud_provider=false
```

**Szenario 5: "Warum?"-Button auf Pflegeerinnerung**
```
GIVEN: User hat Care-Reminder "Monstera giessen, faellig heute"
  AND: Stufe 1+2 aktiv, Consent ai_tenant_data_access vorhanden
WHEN: User klickt <WhyButton>
THEN:
  - WhyDrawer oeffnet mit Spinner
  - POST /api/v1/t/.../ai/explain body={ subject_type: "reminder", subject_key: "...", question_template_id: "care_reminder_watering" }
  - Backend laedt Template, fuellt Slots (species, phase, last_watering_iso, substrate_weight_delta)
  - Knowledge Service liefert Antwort + Quellen
  - Drawer zeigt Antwort in <AIResponse> mit Quellen-Footer
  - Cache-Schluessel ai:explain:home:care_reminder_watering:{plant_state_hash} gesetzt
WHEN: User klickt erneut binnen 24h
THEN:
  - Sofortantwort aus Cache (Latency < 50ms)
```

**Szenario 6: Daily Tip on-first-load**
```
GIVEN: User oeffnet Dashboard zum ersten Mal heute
  AND: Stufe 1+2 aktiv, Consent vorhanden, Tenant hat 3 Pflanzen
WHEN: Frontend ruft GET /api/v1/t/.../ai/daily-tip
THEN:
  - Backend prueft Cache fuer ai:daily-tip:{tenant_key}:{date_local}
  - Cache-Miss -> Generierung
  - Auswahl-Heuristik findet "Pflanze X EC out-of-range"
  - LLM generiert Warning-Tipp
  - Response: tip_type=warning, language=de, uses_tenant_data=true
  - Cache mit TTL bis Mitternacht Tenant-Zeitzone gesetzt
WHEN: User dismissed via POST /daily-tip/dismiss
THEN:
  - Cache wird invalidiert; LocalStorage-Flag setzt UI-Sichtbarkeit auf false bis morgen
```

**Szenario 7: Cloud-Provider mit Consent**
```
GIVEN: Tenant erlaubt Cloud-Provider (ai_allow_cloud_providers=true)
  AND: Default-Provider ist anthropic:claude-haiku-3-5
  AND: User hat Consent ai_tenant_data_access aber NICHT ai_cloud_processing
WHEN: User sendet Chat-Nachricht
THEN:
  - HTTP 403 Body { detail: "consent_required", consent_purpose: "ai_cloud_processing" }
  - Frontend oeffnet AiConsentDialog mit Cloud-Provider-Erklaerung
  - User stimmt zu -> ConsentRecord wird gespeichert
  - Frontend wiederholt Anfrage automatisch
  - Antwort wird via SSE gestreamt, response.uses_cloud_provider=true
  - <AIResponse> zeigt Cloud-Provider-Indikator
```

**Szenario 8: Knowledge Service nicht erreichbar (Graceful Degradation)**
```
GIVEN: Knowledge-Service-Pod ist down
  AND: Stufe 1+2 aktiv, Consent vorhanden
WHEN: GET /api/v1/t/.../ai/tips
THEN:
  - KnowledgeServiceAdapter wirft KnowledgeServiceUnavailable
  - TipEngine faellt zurueck auf _rule_based_fallback
  - Generiert Warning-Tipp basierend auf EC/VPD-Werten ohne LLM
  - HTTP 200 mit Fallback-Tipps
  - response.model_name = "rule-based"
  - response.uses_cloud_provider = false
  - <AIResponse> zeigt KI-Badge mit Hinweis "Regelbasiert — KI-Wissensbasis derzeit nicht erreichbar"
  - Audit-Log: status=knowledge_service_error
```

**Szenario 9: Multilingual — englische Frage gegen deutsche KB**
```
GIVEN: User-Locale = "en", doc_language = "all"
  AND: Knowledge Service hat aktuell nur deutsche Chunks
WHEN: POST /api/v1/t/.../ai/explain (Template englisch)
THEN:
  - Knowledge Service liefert deutsche Chunks als sources
  - LLM antwortet mit prompt_language=en — Antwort auf Englisch
  - Backend setzt language_mismatch_warning=false (Antwort und Locale matchen, nur Quellen-Sprache differiert)
WHEN: doc_language=en (kuenstlich, fuer Test)
THEN:
  - Knowledge Service liefert leere Treffer
  - Backend faellt auf Fallback zurueck
  - language_mismatch_warning=true
  - <AIResponse> zeigt Sprach-Badge
```

**Szenario 10: PII-Stripping**
```
GIVEN: Tenant-Name = "Anna's Garten", User-Name = "Anna Mueller"
  AND: PlantDiaryEntry mit Freitext "Heute hat Anna gegossen, sehr gut"
  AND: User stellt Chat-Frage "Wie geht es meiner Tomate?"
WHEN: Backend baut context und uebermittelt an Knowledge Service
THEN:
  - context.species = "Solanum lycopersicum"
  - context.phase = "flowering"
  - context.ec = 1.8
  - context enthaelt KEIN "Anna", "Mueller", "Anna's Garten"
  - extended_context (falls aktiv) enthaelt "letzter_diary_eintrag_alter_tage": 0 (NICHT den Freitext)
  - Test mocked Knowledge Service und assertet Inhalt der Anfrage
```

**Szenario 11: Audit-Log ohne PII**
```
WHEN: Beliebiger KI-Aufruf laeuft
THEN:
  - ai_audit_log-Eintrag entsteht
  - question_hash ist sha256 ueber die Frage
  - Frage und Antwort erscheinen NICHT im Klartext im Eintrag
  - kb_version wird mitgeschrieben (z. B. "ks-1.4.2-idx-20260420")
WHEN: User ruft Auskunftsexport (REQ-025) ab
THEN:
  - Audit-Eintraege erscheinen mit gehashter Frage und Laenge, ohne Frage-Klartext
```

**Szenario 12: DSGVO-Loeschung des Users**
```
GIVEN: User "anna" mit 5 Conversations, 12 dismissed Tipps, 87 Audit-Eintraegen
WHEN: User triggert DSGVO-Loeschung (REQ-025)
THEN:
  - alle 5 Conversations werden hard-deleted
  - 12 Tipp-Cache-Eintraege mit dismissed_by=anna werden anonymisiert (dismissed_by=null)
  - 87 Audit-Eintraege werden anonymisiert (user_key=null), Hashes bleiben fuer Statistik
  - structlog: "ai_user_data_purged" ohne PII
```

**Szenario 13: Erfahrungsstufen-Sensitivitaet**
```
GIVEN: User ist Beginner
WHEN: TipCardsPanel laedt Tipps
THEN:
  - max 2 Karten statt 4
  - <AIResponse> Quellen-Footer ist eingeklappt
  - Body-Text in einfacher Sprache (Knowledge Service erhaelt expertise_level="beginner" als Hinweis im Prompt)
  - keine Fachbegriffe ohne Erklaerung
  - Chat-Drawer NICHT zugaenglich (FAB ausgeblendet)
GIVEN: User ist Expert
WHEN: TipCardsPanel laedt Tipps
THEN:
  - bis zu 4 Karten
  - <AIResponse> Quellen-Footer ist offen
  - Body enthaelt technische Werte (EC, VPD-Zahlen etc.)
```

**Szenario 14: Reingest-Task**
```
GIVEN: ai.knowledge_service_ingest laeuft Sonntag 03:00 UTC
WHEN: Task ausgefuehrt
THEN:
  - Backend ruft POST /ingest am Knowledge Service
  - Antwort enthaelt files=N, chunks=M
  - structlog: "ai_kb_reingest_done", files=N, chunks=M
  - Bei Fehler: Retry maximal 1x mit 30 Min Delay; danach Pager-Alert
```

## 12. Migration von v1.0

Da REQ-031 v1.0 noch nicht implementiert war (Status "Entwurf" mit `Wird benoetigt von: Keine bestehende REQ`), gibt es keinen Code-Migrationspfad. v2.0 ersetzt v1.0 vollstaendig als Implementierungsgrundlage. Der Knowledge Service unter `src/knowledge-service/` ist bereits konform zu v2.0.

Folgende Backend-Komponenten werden mit der Implementierung von v2.0 NEU angelegt (keine bestehenden zu migrieren):

- `app/data_access/external/knowledge_service_adapter.py`
- `app/domain/interfaces/knowledge_service.py`
- `app/domain/services/ai_assistant_service.py`
- `app/domain/engines/ai_context_builder.py`
- `app/domain/engines/ai_tip_engine.py`
- `app/domain/engines/ai_explain_engine.py`
- `app/domain/repositories/ai_*` (Provider, Conversation, Tip-Cache, Audit-Log)
- `app/api/v1/ai/` (Router fuer Tenant-scoped + Light-Modus + Global)
- `app/tasks/ai_tasks.py`

Folgende Frontend-Komponenten werden NEU angelegt:

- `src/components/ai/AIResponse.tsx`
- `src/components/ai/TipCardsPanel.tsx`
- `src/components/ai/DailyTipCard.tsx`
- `src/components/ai/WhyButton.tsx`
- `src/components/ai/WhyDrawer.tsx`
- `src/components/ai/AiChatDrawer.tsx`
- `src/components/ai/AiConsentDialog.tsx`
- `src/pages/einstellungen/AiProviderSettingsPage.tsx`

## 13. Offene Punkte

- **Englischer Knowledge-Base-Aufbau:** Wann werden YAMLs unter `spec/knowledge/rag/` ins Englische uebersetzt? Vorschlag: nach erstem produktiven Einsatz, mit Translator-Agent oder kuratierter Uebersetzung.
- **Pro-Tenant-Cost-Tracking:** Cloud-Provider-Aufrufe sollten pro Tenant pro Monat sichtbar sein (Token-Counter im Audit-Log -> Aggregation). In v2.0 als Nice-to-have, nicht im DoD.
- **A/B-Testing alternativer LLMs:** Wechsel auf Qwen2.5:14b oder Mistral-Nemo:12b zur Verbesserung der RAG-Eval-Score; gehoert in den Knowledge-Service-Backlog, nicht in REQ-031.
- **Notification-Integration:** Wann wird ein "Daily Tip" als REQ-030-Notification verschickt (z. B. morgens an HA)? Erfordert Co-Spec mit REQ-030; nicht in v2.0.
- **Foto-Anhang im Chat:** REQ-029 liefert Bilderkennung. Soll der Chat-Drawer Foto-Uploads erlauben, deren Erkennungs-Ergebnis als Kontext in den Chat einfliesst? Vorschlag: in eigenem Folge-REQ.
