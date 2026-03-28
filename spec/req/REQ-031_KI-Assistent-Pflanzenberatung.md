# Spezifikation: REQ-031 - KI-Assistent & Pflanzenberatung

```yaml
ID: REQ-031
Titel: KI-Assistent & Pflanzenberatung
Kategorie: KI & Beratung
Fokus: Beides
Technologie: Python, FastAPI, Celery, ArangoDB, TimescaleDB (pgvector), Redis, React, TypeScript, MUI, Ollama, OpenAI API
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-001 v5.0 (Stammdaten), REQ-003 v1.0 (Phasensteuerung), REQ-004 v3.1 (Dünge-Logik), REQ-005 v2.3 (Sensorik), REQ-011 v1.0 (Adapter-Pattern), REQ-013 v2.0 (Pflanzdurchlauf), REQ-021 v1.0 (Erfahrungsstufen), REQ-023 v1.7 (Auth), REQ-024 v1.4 (Mandantenverwaltung), REQ-025 v1.0 (DSGVO)
```

## 1. Business Case

**User Story (Casual User — Tipp-Karten):** "Als Zimmerpflanzen-Besitzer ohne Fachkenntnisse moechte ich auf der Detailseite meiner Pflanze kontextabhaengige Pflegehinweise als kompakte Karten sehen — damit ich sofort weiß, was zu tun ist, ohne in Foren oder Buechern nachschlagen zu muessen."

**User Story (Grower — Diagnose):** "Als erfahrener Grower moechte ich bei ungewoehnlichen Symptomen (gelbe Blaetter, EC-Drift, VPD-Abweichung) eine KI-gestuetzte Analyse mit konkreten Handlungsempfehlungen erhalten — damit ich schnell die Ursache identifiziere und Ernteverluste vermeide."

**User Story (Self-Hosted-Nutzer — Datenschutz):** "Als Self-Hosted-Nutzer moechte ich den KI-Assistenten vollstaendig lokal betreiben koennen (Ollama + lokales Modell) — damit keine meiner Pflanzen- und Messdaten an externe Cloud-Dienste uebertragen werden."

**User Story (Pro-Nutzer — Chat):** "Als fortgeschrittener Nutzer moechte ich einen Chat-Dialog mit KI-Kontext fuehren koennen, in dem das System meine aktuelle Pflanzenphase, Messwerte und Duengehistorie kennt — damit ich komplexe Fragen wie 'Soll ich in Woche 4 der Bluete den PK-Boost schon starten?' beantworten lassen kann."

**User Story (Datenschutz-bewusster Nutzer):** "Als datenschutzbewusster Nutzer moechte ich transparent sehen, welche Daten an welchen KI-Provider gesendet werden und meine Einwilligung jederzeit widerrufen koennen — damit ich die Kontrolle ueber meine Daten behalte und DSGVO-konform handeln kann."

**User Story (Admin — Provider-Konfiguration):** "Als Tenant-Admin moechte ich per Einstellungsseite zwischen verschiedenen KI-Providern wechseln koennen (Ollama, OpenAI, Anthropic) und eigene API-Keys hinterlegen — damit ich den besten Kompromiss aus Qualitaet, Kosten und Datenschutz fuer meinen Anwendungsfall waehlen kann."

**Beschreibung:**

Das Feature integriert einen KI-gestuetzten Assistenten in das bestehende Kamerplanter-System. Der Assistent liefert kontextbezogene Pflegehinweise (Tipp-Karten), eine interaktive Chat-Funktion und diagnostische Analyse auf Basis der vorhandenen Stamm- und Messdaten. Die Architektur nutzt das etablierte Adapter-Pattern (REQ-011) fuer austauschbare Provider-Backends und **Retrieval-Augmented Generation (RAG)** ueber die eigene ArangoDB-Wissensbasis.

**Grundprinzipien:**

- **Local-First:** Vollstaendig ohne externe API-Keys nutzbar (Ollama + lokale Modelle). Cloud-Provider sind optional und erfordern explizite Konfiguration.
- **Adapter-Pattern:** Austauschbare Provider-Backends ueber eine einheitliche `IAiProvider`-Schnittstelle — analog zum `ExternalSourceAdapter` in REQ-011.
- **RAG ueber eigene Daten:** Die Wissensbasis besteht ausschliesslich aus Kamerplanter-Stammdaten und Nutzer-Pflanzdaten. Keine allgemeine Internetsuche, keine halluzinierten Fakten.
- **Consent-basiert:** Externe Cloud-APIs (OpenAI, Anthropic) erfordern explizite DSGVO-Einwilligung (REQ-025). Lokale Provider benoetigen keinen Consent.
- **Graceful Degradation:** Bei fehlendem oder ausgefallenen Provider werden regelbasierte Fallback-Tips generiert — das System ist nie ohne Empfehlungen.
- **Kontext-bewusst:** Jede Antwort kennt die aktuelle Phase, EC/pH-Werte, Messdaten, aktive IPM-Events und die Pflegehistorie des Nutzers.
- **Erfahrungsstufen-sensitiv:** Beginner sehen vereinfachte Tipp-Karten, Chat ist ab Intermediate verfuegbar, Expert-Nutzer erhalten technische Details (REQ-021).

### 1.1 Provider-Architektur

| Prio | Provider | Typ | Datenschutz-Level | API-Key | Kosten | Empfohlene Modelle |
|------|----------|-----|-------------------|---------|--------|--------------------|
| 1 | **Ollama (lokal)** | Lokale Inference | Keine Datenweitergabe | Nicht erforderlich | Kostenlos (eigene Hardware) | `llama3.2:3b`, `gemma3:4b`, `mistral:7b` |
| 2 | **llama.cpp HTTP Server** | Lokale Inference | Keine Datenweitergabe | Nicht erforderlich | Kostenlos (eigene Hardware) | Beliebig (GGUF-Format) |
| 3 | **OpenAI API** | Cloud | Datenuebertragung an OpenAI (USA) | Erforderlich | Pay-per-Token | `gpt-4o-mini`, `gpt-4o` |
| 4 | **Anthropic Claude API** | Cloud | Datenuebertragung an Anthropic (USA) | Erforderlich | Pay-per-Token | `claude-haiku-3-5`, `claude-sonnet-4` |
| 5 | **OpenAI-kompatible APIs** | Cloud oder Lokal | Abhaengig vom Anbieter | Abhaengig vom Anbieter | Variabel | LM Studio, vLLM, Together AI, Mistral AI |

**Abgrenzung zu REQ-029:**
- REQ-029 **identifiziert unbekannte** Pflanzen anhand von **Bildern** (Plant.id, PlantNet).
- REQ-031 **beraet** zu bekannten Pflanzen auf Basis von **Stammdaten, Messwerten und Kontext** (LLM-basiert).
- Beide sind unabhaengig voneinander nutzbar. Synergie: REQ-029-Diagnose kann als Kontext in REQ-031-Chat einfliessen.

### 1.2 Request-Flow

```
Nutzer stellt Frage / oeffnet Pflanze
        |
        v
+---------------------+
|  Frontend           |---> TipCardsPanel oder AiChatDrawer
|  (React/MUI)        |
+---------------------+
        |
        v  REST API (SSE fuer Streaming)
+---------------------+
|  API-Layer          |---> /api/v1/t/{slug}/ai/...
|  (FastAPI Router)   |---> Auth + Consent-Check + Rate-Limit
+---------------------+
        |
        v
+---------------------+
|  AiAssistantService |---> Orchestrierung
|  (Business Logic)   |
+---------------------+
        |
   +----+----+
   |         |
   v         v
+----------+ +------------------+
| Context  | | RagRetriever     |
| Builder  | | (pgvector Search)|
+----------+ +------------------+
   |         |
   v         v
+---------------------+
|  System-Prompt       |---> Kontext + RAG-Chunks + Chat-History
|  zusammenbauen       |
+---------------------+
        |
        v
+---------------------+
|  IAiProvider         |---> Ollama / OpenAI / Anthropic / llama.cpp
|  (Adapter)           |
+---------------------+
        |
        v
+---------------------+
|  Antwort parsen      |---> Tips (JSON) oder Chat-Text (Streaming)
|  cachen + speichern  |
+---------------------+
        |
        v
   Antwort an Frontend
```

### 1.3 Provider-Konfiguration (Beispiel)

```json
{
  "_key": "ollama-local",
  "tenant_key": null,
  "provider_type": "ollama",
  "display_name": "Lokales Modell (Ollama)",
  "base_url": "http://ollama:11434",
  "model_name": "llama3.2:3b",
  "api_key_encrypted": null,
  "requires_consent": false,
  "is_active": true,
  "is_default": true,
  "max_tokens": 1024,
  "temperature": 0.3,
  "timeout_seconds": 30,
  "created_at": "2026-03-28T00:00:00Z",
  "updated_at": "2026-03-28T00:00:00Z"
}
```

## 2. RAG-Architektur (Retrieval-Augmented Generation)

Das System nutzt **Retrieval-Augmented Generation**, um Antworten auf der eigenen Wissensbasis zu gruenden und Halluzinationen zu minimieren. Die Wissensbasis wird nicht mit allgemeinem Internet-Wissen vermischt.

### 2.1 Wissensbasis-Quellen (4 Ebenen)

| Ebene | Datenquelle | Umfang | Personenbezug | Aktualisierung |
|-------|-------------|--------|---------------|----------------|
| 1. **Globale Stammdaten** | Species, Cultivar, GrowthPhase, NutrientProfile, Pest, Disease | Tenant-unabhaengig | Kein Personenbezug | Woechentlich (Celery) |
| 2. **Regelwissen** | VPD-Zielwerte, EC-Grenzen je Phase, Mischsicherheitsregeln, Phasenuebergangs-Bedingungen | Fest kodiert (YAML) | Kein Personenbezug | Bei Deployment |
| 3. **Tenant-Kontext** | Aktiver PlantingRun, Phase, Messwerte (EC, pH, VPD), aktive IPM-Events, letzte FeedingEvents | Tenant-scoped | Indirekt (Nutzer-Aktivitaet) | Echtzeit (pro Anfrage) |
| 4. **Nutzer-Pflanzdaten** | Pflegehistorie, Ernteresultate, CareConfirmations, PlantDiaryEntry | Tenant- + User-scoped | Ja (Consent erforderlich) | Echtzeit (pro Anfrage) |

**Ebene 1 + 2** werden als Vektoren in pgvector eingebettet (offline, Celery Task).
**Ebene 3 + 4** werden zur Laufzeit als strukturierter Kontext in den System-Prompt injiziert.

### 2.2 Vektorisierung

- **Embedding-Modell:** `sentence-transformers/all-MiniLM-L6-v2` (384 Dimensionen, lokal, kein API-Key, ~23 MB Modellgroesse)
- **Vektorspeicher:** pgvector-Extension auf TimescaleDB (bereits im Stack, kein zusaetzlicher Service)
- **Einzubettende Inhalte:**

| Quell-Collection | Chunk-Inhalt | Geschaetzte Chunks |
|------------------|--------------|--------------------|
| `species` | Wissenschaftlicher Name, Familie, Gattung, Beschreibung, Pflegeanforderungen | ~500 |
| `cultivars` | Sortenname, Genetik, spezifische Eigenschaften | ~1.000 |
| `growth_phases` | Phasenname, Dauer, VPD-Ziele, Licht-/Temperatur-Anforderungen | ~200 |
| `pests` | Name, Symptome, Bekaempfungsmethoden | ~100 |
| `diseases` | Name, Symptome, Behandlung, Praevention | ~100 |
| `care_rules` (YAML) | Regelbasierte Entscheidungslogik (EC-Grenzen, VPD-Bereiche, Phasentipps) | ~200 |

- **Chunk-Groesse:** 512 Tokens, Overlap: 64 Tokens
- **Aktualisierung:** Woechentlich via Celery-Task (`reindex_vector_chunks`)

### 2.3 Retrieval-Strategie

1. Nutzer-Frage (oder Kontext-Beschreibung fuer Tips) wird mit demselben Embedding-Modell vektorisiert
2. Cosine-Similarity-Suche auf `ai_vector_chunks` (pgvector `<=>` Operator)
3. Optionaler `source_type`-Filter (z.B. nur `pest` + `disease` bei Diagnose-Fragen)
4. Top-K Chunks (Standard: 5) werden als Kontext in den System-Prompt eingefuegt
5. Chunk-Referenzen (`source_key`, `source_type`) werden in der Antwort mitgeliefert (Transparenz)

## 3. Datenmodell-Erweiterung

### 3.1 Neue Document Collections (ArangoDB)

**`ai_provider_configs` — Provider-Konfigurationen:**

Tenant-scoped fuer Tenant-eigene API-Keys, `tenant_key = null` fuer System-Defaults (Platform-Admin).

```json
{
  "_key": "uuid",
  "tenant_key": "string | null",
  "provider_type": "ollama | llamacpp | openai | anthropic | openai_compatible",
  "display_name": "string",
  "base_url": "string",
  "model_name": "string",
  "api_key_encrypted": "string | null",
  "requires_consent": "boolean",
  "is_active": "boolean",
  "is_default": "boolean",
  "max_tokens": "int (default: 1024)",
  "temperature": "float (default: 0.3)",
  "timeout_seconds": "int (default: 30)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Indexes:**
- Persistent Index auf `tenant_key` (Tenant-Filterung)
- Persistent Index auf `provider_type` (Typ-Abfrage)
- Persistent Unique Index auf `tenant_key` + `is_default` WHERE `is_default == true` (ein Default pro Tenant)

**`ai_conversations` — Chat-Verlaeufe:**

Tenant-scoped, DSGVO-Retention (Standard: 90 Tage).

```json
{
  "_key": "uuid",
  "tenant_key": "string",
  "user_key": "string",
  "title": "string | null",
  "context_type": "plant_instance | planting_run | general | diagnosis",
  "context_key": "string | null",
  "provider_key": "string",
  "model_name": "string",
  "message_count": "int",
  "messages": [
    {
      "role": "user | assistant | system",
      "content": "string",
      "timestamp": "datetime",
      "source_chunks": ["vector_id1", "vector_id2"]
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime",
  "expires_at": "datetime"
}
```

**Indexes:**
- Persistent Index auf `tenant_key` + `user_key` (Nutzer-Konversationen)
- Persistent Index auf `expires_at` (Retention-Cleanup)
- Persistent Index auf `context_type` + `context_key` (Kontext-Suche)

**`ai_tip_cache` — Gecachte Tipp-Karten:**

Redis fuer Hot-Cache (4h TTL), ArangoDB fuer Persistenz (7 Tage).

```json
{
  "_key": "uuid",
  "tenant_key": "string",
  "context_type": "plant_instance | planting_run | phase | general",
  "context_key": "string",
  "tip_type": "care | warning | optimization | diagnosis | milestone",
  "priority": "critical | high | medium | low",
  "title": "string",
  "body": "string",
  "action_url": "string | null",
  "source_chunks": ["vector_id1", "vector_id2"],
  "provider_key": "string",
  "model_name": "string",
  "generated_at": "datetime",
  "valid_until": "datetime",
  "dismissed_at": "datetime | null",
  "dismissed_by": "string | null",
  "acted_on_at": "datetime | null"
}
```

**Indexes:**
- Persistent Index auf `tenant_key` + `context_type` + `context_key` (Kontext-Abfrage)
- Persistent Index auf `valid_until` (Ablauf-Cleanup)
- Persistent Index auf `priority` (Sortierung)

### 3.2 Neue Tabelle (TimescaleDB / pgvector)

**`ai_vector_chunks` — Vektordatenbank fuer RAG:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE ai_vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(64) NOT NULL,   -- 'species', 'cultivar', 'growth_phase', 'care_rule', 'pest', 'disease'
    source_key VARCHAR(128) NOT NULL,   -- ArangoDB _key der Quell-Entitaet
    chunk_index INT NOT NULL DEFAULT 0, -- Position innerhalb eines Dokuments (bei mehreren Chunks)
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,     -- all-MiniLM-L6-v2: 384 Dimensionen
    metadata JSONB DEFAULT '{}',        -- z.B. {"family": "Solanaceae", "phase": "flowering"}
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- IVFFlat-Index fuer schnelle Cosine-Similarity-Suche
CREATE INDEX idx_ai_vector_chunks_embedding
    ON ai_vector_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Funktionaler Index fuer Source-Filterung
CREATE INDEX idx_ai_vector_chunks_source
    ON ai_vector_chunks (source_type, source_key);

-- Unique Constraint: Ein Chunk pro Source + Index
CREATE UNIQUE INDEX idx_ai_vector_chunks_unique
    ON ai_vector_chunks (source_type, source_key, chunk_index);
```

### 3.3 Neue Edge Collections (ArangoDB)

```
// Edge Collection: ai_tip_references_plant (ai_tip_cache -> plant_instances)
//   Verbindet einen Tip mit der referenzierten Pflanze
//   Felder: created_at

// Edge Collection: ai_tip_references_run (ai_tip_cache -> planting_runs)
//   Verbindet einen Tip mit dem referenzierten Pflanzdurchlauf
//   Felder: created_at

// Edge Collection: ai_conversation_about (ai_conversations -> plant_instances / planting_runs)
//   Verbindet eine Konversation mit ihrem Kontext-Objekt
//   Felder: context_type, created_at
```

### 3.4 AQL-Beispielabfragen

**Aktuelle Tips fuer einen PlantingRun:**
```aql
FOR tip IN ai_tip_cache
    FILTER tip.tenant_key == @tenant_key
       AND tip.context_type == "planting_run"
       AND tip.context_key == @run_key
       AND tip.valid_until > DATE_NOW()
       AND tip.dismissed_at == null
    SORT tip.priority == "critical" ? 0 :
         tip.priority == "high" ? 1 :
         tip.priority == "medium" ? 2 : 3 ASC,
         tip.generated_at DESC
    LIMIT 4
    RETURN tip
```

**Konversationen eines Nutzers:**
```aql
FOR conv IN ai_conversations
    FILTER conv.tenant_key == @tenant_key
       AND conv.user_key == @user_key
    SORT conv.updated_at DESC
    LIMIT @limit
    RETURN {
        _key: conv._key,
        title: conv.title,
        context_type: conv.context_type,
        message_count: conv.message_count,
        model_name: conv.model_name,
        updated_at: conv.updated_at
    }
```

**Provider-Konfiguration mit Fallback (Tenant -> Global):**
```aql
LET tenant_providers = (
    FOR p IN ai_provider_configs
        FILTER p.tenant_key == @tenant_key AND p.is_active == true
        RETURN p
)
LET global_providers = (
    FOR p IN ai_provider_configs
        FILTER p.tenant_key == null AND p.is_active == true
        RETURN p
)
LET all_providers = APPEND(tenant_providers, global_providers)
FOR p IN all_providers
    SORT p.is_default DESC
    RETURN DISTINCT p
```

**Abgelaufene Konversationen (DSGVO-Cleanup):**
```aql
FOR conv IN ai_conversations
    FILTER conv.expires_at < DATE_NOW()
    RETURN conv._key
```

## 4. Technische Umsetzung (Python)

### 4.1 Provider-Interface

```python
# app/domain/interfaces/ai_provider.py

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Einzelne Nachricht in einer Chat-Konversation."""

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime | None = None


class AiResponse(BaseModel):
    """Antwort eines KI-Providers."""

    content: str
    model: str
    provider_type: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    response_time_ms: int | None = None


class IAiProvider(ABC):
    """Abstraktes Interface fuer KI-Provider.

    Jeder Provider (Ollama, OpenAI, Anthropic, etc.) implementiert
    dieses Interface. Neue Provider koennen ohne Aenderung am
    bestehenden Code hinzugefuegt werden (Adapter-Pattern, REQ-011).
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AiResponse:
        """Sendet eine Chat-Anfrage und gibt die vollstaendige Antwort zurueck."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Sendet eine Chat-Anfrage und streamt die Antwort Token-fuer-Token."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Prueft ob der Provider erreichbar und funktionsfaehig ist."""
        ...
```

### 4.2 Adapter-Implementierungen

**Dateistruktur:**
```
app/data_access/ai/
    __init__.py
    ollama_adapter.py
    llamacpp_adapter.py
    openai_adapter.py
    anthropic_adapter.py
    openai_compatible_adapter.py
    provider_registry.py
```

**OllamaAdapter (`data_access/ai/ollama_adapter.py`):**
```python
import time

import httpx
import structlog

from app.domain.interfaces.ai_provider import AiResponse, ChatMessage, IAiProvider

logger = structlog.get_logger()


class OllamaAdapter(IAiProvider):
    """Adapter fuer Ollama (lokale LLM-Inference).

    Dokumentation: https://github.com/ollama/ollama/blob/main/docs/api.md
    Endpunkt: POST /api/chat
    Streaming: POST /api/chat mit stream=true
    Kein API-Key erforderlich, keine Datenweitergabe.
    """

    def __init__(self, base_url: str, model_name: str, timeout_seconds: int = 30) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout = timeout_seconds

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AiResponse:
        start = time.monotonic()
        payload = {
            "model": self._model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return AiResponse(
            content=data.get("message", {}).get("content", ""),
            model=self._model_name,
            provider_type="ollama",
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            total_tokens=(data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0),
            response_time_ms=elapsed_ms,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self._model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        import json
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
```

**OpenAiAdapter (`data_access/ai/openai_adapter.py`):**
```python
import time

import structlog

from app.domain.interfaces.ai_provider import AiResponse, ChatMessage, IAiProvider

logger = structlog.get_logger()


class OpenAiAdapter(IAiProvider):
    """Adapter fuer OpenAI API (GPT-4o-mini, GPT-4o).

    Erfordert API-Key und DSGVO-Einwilligung (Cloud-Provider).
    Nutzt das offizielle openai Python SDK (async client).
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        timeout_seconds: int = 30,
    ) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self._model_name = model_name

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AiResponse:
        start = time.monotonic()

        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        choice = response.choices[0]
        usage = response.usage

        return AiResponse(
            content=choice.message.content or "",
            model=response.model,
            provider_type="openai",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            response_time_ms=elapsed_ms,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def health_check(self) -> bool:
        try:
            await self._client.models.retrieve(self._model_name)
            return True
        except Exception:
            return False
```

**AnthropicAdapter (`data_access/ai/anthropic_adapter.py`):**
```python
class AnthropicAdapter(IAiProvider):
    """Adapter fuer Anthropic Claude API (Haiku, Sonnet).

    Erfordert API-Key und DSGVO-Einwilligung (Cloud-Provider).
    Nutzt das offizielle anthropic Python SDK (async client).
    Besonderheit: System-Prompt wird separat uebergeben (nicht als Message).
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-haiku-3-5",
        timeout_seconds: int = 30,
    ) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout_seconds)
        self._model_name = model_name

    async def chat(self, messages: list[ChatMessage], *, max_tokens: int = 1024, temperature: float = 0.3) -> AiResponse:
        # Anthropic: system prompt separat, nicht in messages
        system_prompt = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        start = time.monotonic()
        response = await self._client.messages.create(
            model=self._model_name,
            system=system_prompt or "",
            messages=chat_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return AiResponse(
            content=response.content[0].text,
            model=response.model,
            provider_type="anthropic",
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            response_time_ms=elapsed_ms,
        )

    # chat_stream und health_check analog
```

**LlamaCppAdapter (`data_access/ai/llamacpp_adapter.py`):**
```python
class LlamaCppAdapter(IAiProvider):
    """Adapter fuer llama.cpp HTTP Server.

    Implementiert das OpenAI-kompatible Interface (/v1/chat/completions).
    Kein API-Key erforderlich, lokale Inference.
    """

    # Nutzt OpenAI-kompatibles Interface via httpx
    # POST {base_url}/v1/chat/completions
```

**OpenAiCompatibleAdapter (`data_access/ai/openai_compatible_adapter.py`):**
```python
class OpenAiCompatibleAdapter(IAiProvider):
    """Generischer Adapter fuer OpenAI-kompatible APIs.

    Unterstuetzt: LM Studio, vLLM, Together AI, Mistral AI, Groq.
    Nutzt das openai Python SDK mit custom base_url.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout_seconds: int = 30,
    ) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_seconds,
        )
        self._model_name = model_name

    # chat, chat_stream, health_check analog zu OpenAiAdapter
```

### 4.3 Provider-Registry

```python
# app/data_access/ai/provider_registry.py

from typing import ClassVar

import structlog

from app.domain.interfaces.ai_provider import IAiProvider

logger = structlog.get_logger()


class AiProviderRegistry:
    """Registry fuer KI-Provider-Adapter.

    Analog zur AdapterRegistry in REQ-011.
    Registriert Provider-Typen und instanziiert sie anhand der Konfiguration.
    """

    _providers: ClassVar[dict[str, type[IAiProvider]]] = {}

    @classmethod
    def register(cls, provider_type: str):
        """Dekorator zum Registrieren eines Provider-Adapters."""
        def decorator(provider_cls: type[IAiProvider]) -> type[IAiProvider]:
            cls._providers[provider_type] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def create(cls, provider_type: str, **kwargs) -> IAiProvider:
        """Instanziiert einen Provider anhand des Typs und der Konfiguration."""
        provider_cls = cls._providers.get(provider_type)
        if not provider_cls:
            raise KeyError(
                f"Unknown AI provider type '{provider_type}'. "
                f"Available: {list(cls._providers.keys())}"
            )
        return provider_cls(**kwargs)

    @classmethod
    def available_types(cls) -> list[str]:
        return list(cls._providers.keys())
```

### 4.4 RAG-Retriever

```python
# app/domain/engines/ai_rag_retriever.py

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class RagChunk(BaseModel):
    """Ein Chunk aus der Vektordatenbank mit Similarity-Score."""

    chunk_id: str
    source_type: str
    source_key: str
    chunk_text: str
    similarity_score: float
    metadata: dict = {}


class RagRetriever:
    """Retrieval-Engine fuer RAG auf Basis von pgvector.

    Nutzt sentence-transformers (lokal) fuer Embedding-Generierung
    und pgvector auf TimescaleDB fuer Similarity-Search.
    """

    def __init__(self, timescale_pool, embedding_model_name: str = "all-MiniLM-L6-v2") -> None:
        self._pool = timescale_pool
        self._model_name = embedding_model_name
        self._model = None  # Lazy-loaded

    def _get_model(self):
        """Lazy-Load des Embedding-Modells (einmalig, ~23 MB)."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def embed_text(self, text: str) -> list[float]:
        """Generiert ein Embedding fuer den gegebenen Text (lokal, kein API-Key)."""
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def retrieve(
        self,
        query: str,
        *,
        source_types: list[str] | None = None,
        top_k: int = 5,
    ) -> list[RagChunk]:
        """Sucht die relevantesten Chunks fuer eine Anfrage.

        1. Query-Embedding via SentenceTransformer (lokal)
        2. pgvector Cosine-Similarity-Suche auf ai_vector_chunks
        3. Optionaler source_type Filter
        4. Gibt top_k Chunks mit Scores zurueck
        """
        query_embedding = await self.embed_text(query)

        # pgvector Cosine-Distance: 1 - cosine_similarity
        # Operator <=> gibt Distanz zurueck, wir wollen Similarity
        sql = """
            SELECT id, source_type, source_key, chunk_text, metadata,
                   1 - (embedding <=> $1::vector) AS similarity_score
            FROM ai_vector_chunks
        """
        params = [str(query_embedding)]
        conditions = []

        if source_types:
            placeholders = ", ".join(f"${i+2}" for i in range(len(source_types)))
            conditions.append(f"source_type IN ({placeholders})")
            params.extend(source_types)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY embedding <=> $1::vector LIMIT $" + str(len(params) + 1)
        params.append(top_k)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        return [
            RagChunk(
                chunk_id=str(row["id"]),
                source_type=row["source_type"],
                source_key=row["source_key"],
                chunk_text=row["chunk_text"],
                similarity_score=row["similarity_score"],
                metadata=row["metadata"] or {},
            )
            for row in rows
        ]

    async def index_chunk(
        self,
        source_type: str,
        source_key: str,
        chunk_text: str,
        chunk_index: int = 0,
        metadata: dict | None = None,
    ) -> str:
        """Indexiert einen neuen Chunk in der Vektordatenbank."""
        embedding = await self.embed_text(chunk_text)

        sql = """
            INSERT INTO ai_vector_chunks (source_type, source_key, chunk_index, chunk_text, embedding, metadata)
            VALUES ($1, $2, $3, $4, $5::vector, $6)
            ON CONFLICT (source_type, source_key, chunk_index)
            DO UPDATE SET chunk_text = $4, embedding = $5::vector, metadata = $6, updated_at = now()
            RETURNING id
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, source_type, source_key, chunk_index, chunk_text, str(embedding), metadata or {})
            return str(row["id"])
```

### 4.5 Context-Builder

```python
# app/domain/engines/ai_context_builder.py

from pydantic import BaseModel
import structlog

logger = structlog.get_logger()


class PlantContext(BaseModel):
    """Aggregierter Kontext einer PlantInstance fuer den System-Prompt."""

    species_name: str
    cultivar_name: str | None = None
    family_name: str | None = None
    current_phase: str | None = None
    phase_day: int | None = None
    latest_ec_ms: float | None = None
    latest_ph: float | None = None
    latest_vpd_kpa: float | None = None
    latest_temperature_c: float | None = None
    latest_humidity_pct: float | None = None
    active_ipm_events: list[str] = []
    last_feeding_events: list[dict] = []
    open_tasks: list[str] = []
    run_key: str | None = None
    run_name: str | None = None


class RunContext(BaseModel):
    """Aggregierter Kontext eines PlantingRun fuer den System-Prompt."""

    run_name: str
    species_name: str
    cultivar_name: str | None = None
    current_phase: str | None = None
    phase_day: int | None = None
    plant_count: int = 0
    latest_ec_ms: float | None = None
    latest_ph: float | None = None
    latest_vpd_kpa: float | None = None
    latest_temperature_c: float | None = None
    active_ipm_events: list[str] = []
    last_feeding_events: list[dict] = []
    nutrient_plan_name: str | None = None
    open_tasks: list[str] = []


class AiContextBuilder:
    """Baut strukturierten Kontext fuer KI-Anfragen auf.

    Aggregiert Daten aus verschiedenen ArangoDB-Collections
    in ein kompaktes Format fuer den System-Prompt.
    """

    def __init__(self, db) -> None:
        self._db = db

    async def build_plant_context(self, plant_instance_key: str, tenant_key: str) -> PlantContext:
        """Aggregiert den vollstaendigen Kontext einer Pflanze.

        Laedt: PlantInstance, Species, Cultivar, aktuelle Phase,
        letzte 5 FeedingEvents, letzte Messwerte, aktive IPM-Events,
        offene Tasks.
        """
        # AQL-Query aggregiert alle relevanten Daten in einem Aufruf
        aql = """
        LET plant = DOCUMENT(CONCAT("plant_instances/", @plant_key))
        LET species = FIRST(
            FOR s IN species
                FOR e IN instance_of_species
                    FILTER e._from == plant._id AND e._to == s._id
                    RETURN s
        )
        LET cultivar = FIRST(
            FOR c IN cultivars
                FOR e IN instance_of_cultivar
                    FILTER e._from == plant._id AND e._to == c._id
                    RETURN c
        )
        LET current_phase = FIRST(
            FOR ph IN phase_histories
                FOR e IN plant_in_phase
                    FILTER e._from == plant._id AND e._to == ph._id
                    SORT ph.started_at DESC
                    LIMIT 1
                    RETURN ph
        )
        LET feeding_events = (
            FOR fe IN feeding_events
                FOR e IN feeding_for_plant
                    FILTER e._to == plant._id
                    SORT fe.applied_at DESC
                    LIMIT 5
                    RETURN { ec_ms: fe.ec_ms, ph: fe.ph, applied_at: fe.applied_at }
        )
        LET ipm_events = (
            FOR te IN treatment_applications
                FOR e IN treatment_on_plant
                    FILTER e._to == plant._id AND te.status == "active"
                    RETURN te.treatment_name
        )
        RETURN {
            species_name: species.scientific_name,
            cultivar_name: cultivar.name,
            family_name: species.family,
            current_phase: current_phase.phase,
            phase_day: current_phase ? DATE_DIFF(current_phase.started_at, DATE_NOW(), "day") : null,
            last_feeding_events: feeding_events,
            active_ipm_events: ipm_events
        }
        """
        cursor = await self._db.aql.execute(aql, bind_vars={"plant_key": plant_instance_key})
        result = await cursor.next()
        return PlantContext(**result) if result else PlantContext(species_name="Unbekannt")

    async def build_run_context(self, run_key: str, tenant_key: str) -> RunContext:
        """Aggregiert den vollstaendigen Kontext eines Pflanzdurchlaufs."""
        # Analog zu build_plant_context, aber Run-zentriert
        ...

    def format_system_prompt(self, context: PlantContext | RunContext, language: str = "de") -> str:
        """Erstellt den System-Prompt aus dem aggregierten Kontext.

        Sprache wird aus den User-Preferences abgeleitet (REQ-021).
        Der Prompt enthaelt KEINE PII (Nutzername, Tenant-Name).
        """
        if language == "de":
            prompt = "Du bist ein erfahrener Pflanzenberater im Kamerplanter-System.\n"
            prompt += "Antworte praeise, praktisch und auf Deutsch.\n\n"
        else:
            prompt = "You are an experienced plant advisor in the Kamerplanter system.\n"
            prompt += "Answer precisely, practically and in English.\n\n"

        prompt += "=== Aktueller Pflanzenkontext ===\n"

        if isinstance(context, PlantContext):
            prompt += f"Art: {context.species_name}\n"
            if context.cultivar_name:
                prompt += f"Sorte: {context.cultivar_name}\n"
            if context.current_phase:
                prompt += f"Phase: {context.current_phase} (Tag {context.phase_day})\n"
            if context.latest_ec_ms is not None:
                prompt += f"EC: {context.latest_ec_ms} mS/cm\n"
            if context.latest_ph is not None:
                prompt += f"pH: {context.latest_ph}\n"
            if context.latest_vpd_kpa is not None:
                prompt += f"VPD: {context.latest_vpd_kpa} kPa\n"
            if context.active_ipm_events:
                prompt += f"Aktive IPM-Events: {', '.join(context.active_ipm_events)}\n"
        elif isinstance(context, RunContext):
            prompt += f"Durchlauf: {context.run_name}\n"
            prompt += f"Art: {context.species_name}\n"
            prompt += f"Pflanzen: {context.plant_count}\n"
            if context.current_phase:
                prompt += f"Phase: {context.current_phase} (Tag {context.phase_day})\n"

        prompt += "\n=== Anweisungen ===\n"
        prompt += "- Beziehe dich auf den obigen Kontext.\n"
        prompt += "- Gib konkrete, umsetzbare Empfehlungen.\n"
        prompt += "- Nenne Grenzwerte und Referenzbereiche wenn relevant.\n"
        prompt += "- Wenn du dir unsicher bist, sage es ehrlich.\n"

        return prompt
```

### 4.6 Tip-Engine

```python
# app/domain/engines/ai_tip_engine.py

from datetime import datetime, timedelta, timezone
from enum import StrEnum

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class TipType(StrEnum):
    """Typ eines KI-generierten Tips."""
    CARE = "care"
    WARNING = "warning"
    OPTIMIZATION = "optimization"
    DIAGNOSIS = "diagnosis"
    MILESTONE = "milestone"


class TipPriority(StrEnum):
    """Prioritaet eines Tips."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AiTip(BaseModel):
    """Ein einzelner KI-generierter Tip."""
    tip_type: TipType
    priority: TipPriority
    title: str
    body: str
    action_url: str | None = None
    source_chunks: list[str] = []


class TipEngine:
    """Generiert kontextbezogene Tips fuer Pflanzen und Durchlaeufe.

    Nutzt den KI-Provider fuer LLM-basierte Tips mit RAG-Kontext.
    Bei Provider-Ausfall oder -Fehlen werden regelbasierte Fallback-Tips
    generiert (Graceful Degradation).
    """

    def __init__(
        self,
        context_builder: "AiContextBuilder",
        rag_retriever: "RagRetriever",
        tip_cache_repo: "AiTipCacheRepository",
        provider_config_repo: "AiProviderConfigRepository",
        redis_client,
    ) -> None:
        self._context_builder = context_builder
        self._rag_retriever = rag_retriever
        self._tip_cache_repo = tip_cache_repo
        self._provider_config_repo = provider_config_repo
        self._redis = redis_client

    async def generate_tips(
        self,
        context_type: str,
        context_key: str,
        tenant_key: str,
        *,
        force_refresh: bool = False,
    ) -> list[AiTip]:
        """Generiert Tips fuer einen gegebenen Kontext.

        Ablauf:
        1. Cache-Check (Redis 4h TTL, ArangoDB 24h)
        2. Kontext aufbauen via ContextBuilder
        3. RAG-Retrieval (top 3 relevante Chunks)
        4. Provider aus Konfiguration laden
        5. Strukturiertes Prompt senden (JSON-Output-Format)
        6. Tips parsen, validieren, cachen
        7. Bei Provider-Fehler: regelbasierte Fallback-Tips
        """
        # 1. Cache-Check
        if not force_refresh:
            cache_key = f"ai:tips:{tenant_key}:{context_type}:{context_key}"
            cached = await self._redis.get(cache_key)
            if cached:
                import json
                return [AiTip(**t) for t in json.loads(cached)]

            cached_db = await self._tip_cache_repo.find_valid_tips(
                tenant_key, context_type, context_key
            )
            if cached_db:
                return cached_db

        # 2. Kontext aufbauen
        if context_type == "plant_instance":
            context = await self._context_builder.build_plant_context(context_key, tenant_key)
        elif context_type == "planting_run":
            context = await self._context_builder.build_run_context(context_key, tenant_key)
        else:
            context = None

        # 3. RAG-Retrieval
        query = self._build_tip_query(context)
        rag_chunks = await self._rag_retriever.retrieve(query, top_k=3)

        # 4. Provider laden
        try:
            provider_config = await self._provider_config_repo.get_default(tenant_key)
            provider = AiProviderRegistry.create(
                provider_config["provider_type"],
                base_url=provider_config["base_url"],
                model_name=provider_config["model_name"],
                # api_key entschluesseln wenn vorhanden
            )
        except Exception:
            logger.warning("ai_provider_unavailable", tenant_key=tenant_key)
            return await self._rule_based_fallback(context)

        # 5. Prompt zusammenbauen
        system_prompt = self._context_builder.format_system_prompt(context)
        system_prompt += "\n\n=== Wissensbasis ===\n"
        for chunk in rag_chunks:
            system_prompt += f"- {chunk.chunk_text}\n"

        system_prompt += """
=== Aufgabe ===
Generiere 2-4 praxisnahe Tips als JSON-Array. Jeder Tip hat:
- "tip_type": "care" | "warning" | "optimization" | "diagnosis" | "milestone"
- "priority": "critical" | "high" | "medium" | "low"
- "title": kurzer Titel (max 60 Zeichen)
- "body": Erklaerung + Handlungsempfehlung (max 200 Zeichen)

Antworte NUR mit dem JSON-Array, kein anderer Text.
"""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content="Generiere aktuelle Tips fuer diese Pflanze."),
        ]

        # 6. Provider aufrufen
        try:
            response = await provider.chat(messages, max_tokens=512, temperature=0.3)
            tips = self._parse_tips(response.content, rag_chunks)
        except Exception as exc:
            logger.error("ai_tip_generation_failed", error=str(exc))
            tips = await self._rule_based_fallback(context)

        # 7. Cachen
        await self._cache_tips(tips, tenant_key, context_type, context_key)
        return tips

    async def _rule_based_fallback(self, context: PlantContext | RunContext | None) -> list[AiTip]:
        """Deterministischer Fallback ohne KI.

        Generiert regelbasierte Tips anhand der bekannten Grenzwerte:
        - EC zu hoch/niedrig -> Warnung
        - VPD ausserhalb Zielbereich -> Empfehlung
        - Phasentransition ueberfaellig -> Hinweis
        - Naechste Pflege-Aktion -> Info
        """
        tips = []

        if context is None:
            return [AiTip(
                tip_type=TipType.CARE,
                priority=TipPriority.LOW,
                title="Willkommen bei Kamerplanter",
                body="Lege deine erste Pflanze an, um personalisierte Tips zu erhalten.",
            )]

        if isinstance(context, (PlantContext, RunContext)):
            # EC-Warnung
            if context.latest_ec_ms is not None:
                if context.latest_ec_ms > 2.5:
                    tips.append(AiTip(
                        tip_type=TipType.WARNING,
                        priority=TipPriority.HIGH,
                        title="EC-Wert zu hoch",
                        body=f"EC liegt bei {context.latest_ec_ms} mS/cm. Ueberduengung moeglich. Spuelen oder mit Frischwasser verduennen.",
                    ))
                elif context.latest_ec_ms < 0.5 and context.current_phase not in ("germination", "seedling"):
                    tips.append(AiTip(
                        tip_type=TipType.WARNING,
                        priority=TipPriority.MEDIUM,
                        title="EC-Wert niedrig",
                        body=f"EC liegt bei {context.latest_ec_ms} mS/cm. Naehrstoffversorgung pruefen.",
                    ))

            # VPD-Warnung
            if context.latest_vpd_kpa is not None:
                if context.latest_vpd_kpa > 1.6:
                    tips.append(AiTip(
                        tip_type=TipType.WARNING,
                        priority=TipPriority.HIGH,
                        title="VPD zu hoch",
                        body=f"VPD bei {context.latest_vpd_kpa} kPa. Luftfeuchtigkeit erhoehen oder Temperatur senken.",
                    ))
                elif context.latest_vpd_kpa < 0.4:
                    tips.append(AiTip(
                        tip_type=TipType.WARNING,
                        priority=TipPriority.MEDIUM,
                        title="VPD zu niedrig",
                        body=f"VPD bei {context.latest_vpd_kpa} kPa. Schimmelgefahr. Lueften oder Entfeuchter einsetzen.",
                    ))

            # Phasen-Tipp
            if context.current_phase and context.phase_day:
                tips.append(AiTip(
                    tip_type=TipType.CARE,
                    priority=TipPriority.LOW,
                    title=f"Tag {context.phase_day} in {context.current_phase}",
                    body="Pruefen ob die Pflanze bereit fuer die naechste Phase ist.",
                ))

            # Aktive IPM-Events
            if context.active_ipm_events:
                tips.append(AiTip(
                    tip_type=TipType.DIAGNOSIS,
                    priority=TipPriority.HIGH,
                    title="Aktive Schaedlingsbehandlung",
                    body=f"{len(context.active_ipm_events)} aktive IPM-Massnahmen. Behandlungsfortschritt pruefen.",
                ))

        return tips if tips else [AiTip(
            tip_type=TipType.CARE,
            priority=TipPriority.LOW,
            title="Alles im gruenen Bereich",
            body="Keine auffaelligen Werte. Weiter so!",
        )]

    def _parse_tips(self, response_text: str, rag_chunks: list) -> list[AiTip]:
        """Parst die LLM-Antwort (JSON-Array) in AiTip-Objekte."""
        import json
        try:
            # Versuche JSON direkt zu parsen
            data = json.loads(response_text)
            if not isinstance(data, list):
                data = [data]
            chunk_ids = [c.chunk_id for c in rag_chunks]
            return [
                AiTip(
                    tip_type=t.get("tip_type", "care"),
                    priority=t.get("priority", "medium"),
                    title=t.get("title", "")[:60],
                    body=t.get("body", "")[:200],
                    source_chunks=chunk_ids,
                )
                for t in data[:4]  # Max 4 Tips
            ]
        except json.JSONDecodeError:
            logger.warning("ai_tip_parse_failed", response=response_text[:200])
            return []

    async def _cache_tips(
        self,
        tips: list[AiTip],
        tenant_key: str,
        context_type: str,
        context_key: str,
    ) -> None:
        """Cached Tips in Redis (4h) und ArangoDB (24h)."""
        import json
        cache_key = f"ai:tips:{tenant_key}:{context_type}:{context_key}"
        await self._redis.setex(
            cache_key,
            timedelta(hours=4),
            json.dumps([t.model_dump() for t in tips]),
        )
        await self._tip_cache_repo.save_tips(tips, tenant_key, context_type, context_key)

    def _build_tip_query(self, context: PlantContext | RunContext | None) -> str:
        """Baut eine Suchanfrage fuer RAG-Retrieval aus dem Kontext."""
        if context is None:
            return "allgemeine Pflanzenpflege Tips"

        parts = [context.species_name if hasattr(context, "species_name") else "Pflanze"]
        if hasattr(context, "current_phase") and context.current_phase:
            parts.append(f"Phase {context.current_phase}")
        if hasattr(context, "active_ipm_events") and context.active_ipm_events:
            parts.append("Schaedlingsbehandlung")
        return " ".join(parts) + " Pflege Empfehlung"
```

### 4.7 Assistant-Service

```python
# app/domain/services/ai_assistant_service.py

from datetime import datetime, timedelta, timezone

import structlog

from app.domain.engines.ai_context_builder import AiContextBuilder
from app.domain.engines.ai_rag_retriever import RagRetriever
from app.domain.engines.ai_tip_engine import AiTip, TipEngine
from app.domain.interfaces.ai_provider import ChatMessage

logger = structlog.get_logger()


class ChatResponse(BaseModel):
    """Antwort auf eine Chat-Nachricht."""

    conversation_key: str
    content: str
    model: str
    provider_type: str
    source_chunks: list[str] = []
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class AiAssistantService:
    """Orchestrierungs-Service fuer den KI-Assistenten.

    Koordiniert ContextBuilder, RagRetriever, Provider und Persistenz.
    Erzwingt Consent-Checks fuer Cloud-Provider (REQ-025).
    Implementiert Tenant-Isolation (REQ-024).
    """

    def __init__(
        self,
        context_builder: AiContextBuilder,
        rag_retriever: RagRetriever,
        tip_engine: TipEngine,
        conversation_repo: "AiConversationRepository",
        provider_config_repo: "AiProviderConfigRepository",
        consent_service: "ConsentService",
    ) -> None:
        self._context_builder = context_builder
        self._rag_retriever = rag_retriever
        self._tip_engine = tip_engine
        self._conversation_repo = conversation_repo
        self._provider_config_repo = provider_config_repo
        self._consent_service = consent_service

    async def chat(
        self,
        tenant_key: str,
        user_key: str,
        message: str,
        conversation_key: str | None = None,
        context_type: str = "general",
        context_key: str | None = None,
    ) -> ChatResponse:
        """Fuehrt einen Chat-Turn mit dem KI-Assistenten durch.

        Ablauf:
        1. Provider laden + Consent-Check (Cloud-Provider)
        2. Bestehende Conversation laden oder neu erstellen
        3. Kontext aufbauen (falls context_key gesetzt)
        4. RAG-Retrieval fuer aktuelle Frage
        5. Messages zusammenbauen (System + History + RAG + User)
        6. Provider.chat() aufrufen
        7. Conversation speichern
        8. Response zurueckgeben
        """
        # 1. Provider + Consent
        provider_config = await self._provider_config_repo.get_default(tenant_key)
        if provider_config["requires_consent"]:
            has_consent = await self._consent_service.check_consent(
                user_key, "ai_cloud_processing"
            )
            if not has_consent:
                raise ConsentRequiredError(
                    "ai_cloud_processing",
                    f"DSGVO-Einwilligung fuer {provider_config['display_name']} erforderlich.",
                )

        provider = AiProviderRegistry.create(
            provider_config["provider_type"],
            base_url=provider_config["base_url"],
            model_name=provider_config["model_name"],
            api_key=self._decrypt_key(provider_config.get("api_key_encrypted")),
        )

        # 2. Conversation
        if conversation_key:
            conversation = await self._conversation_repo.get(conversation_key, tenant_key)
        else:
            conversation = await self._conversation_repo.create(
                tenant_key=tenant_key,
                user_key=user_key,
                context_type=context_type,
                context_key=context_key,
                provider_key=provider_config["_key"],
                model_name=provider_config["model_name"],
            )

        # 3. Kontext
        context = None
        if context_key:
            if context_type == "plant_instance":
                context = await self._context_builder.build_plant_context(context_key, tenant_key)
            elif context_type == "planting_run":
                context = await self._context_builder.build_run_context(context_key, tenant_key)

        # 4. RAG
        rag_chunks = await self._rag_retriever.retrieve(message, top_k=5)

        # 5. Messages
        system_prompt = self._context_builder.format_system_prompt(context) if context else ""
        system_prompt += "\n\n=== Wissensbasis ===\n"
        for chunk in rag_chunks:
            system_prompt += f"- {chunk.chunk_text}\n"

        messages = [ChatMessage(role="system", content=system_prompt)]
        # Chat-History (letzte 10 Nachrichten)
        for msg in conversation.get("messages", [])[-10:]:
            if msg["role"] != "system":
                messages.append(ChatMessage(role=msg["role"], content=msg["content"]))
        messages.append(ChatMessage(role="user", content=message))

        # 6. Provider aufrufen
        response = await provider.chat(messages)

        # 7. Conversation speichern
        now = datetime.now(tz=timezone.utc)
        await self._conversation_repo.append_messages(
            conversation["_key"],
            [
                {"role": "user", "content": message, "timestamp": now.isoformat()},
                {
                    "role": "assistant",
                    "content": response.content,
                    "timestamp": now.isoformat(),
                    "source_chunks": [c.chunk_id for c in rag_chunks],
                },
            ],
        )

        # 8. Response
        return ChatResponse(
            conversation_key=conversation["_key"],
            content=response.content,
            model=response.model,
            provider_type=response.provider_type,
            source_chunks=[c.chunk_id for c in rag_chunks],
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
        )

    async def get_tips(
        self,
        tenant_key: str,
        context_type: str,
        context_key: str,
        *,
        force_refresh: bool = False,
    ) -> list[AiTip]:
        """Delegiert an TipEngine."""
        return await self._tip_engine.generate_tips(
            context_type, context_key, tenant_key, force_refresh=force_refresh
        )

    async def dismiss_tip(self, tip_key: str, tenant_key: str, user_key: str) -> None:
        """Markiert einen Tip als weggeklickt."""
        await self._tip_engine._tip_cache_repo.dismiss(tip_key, tenant_key, user_key)

    async def mark_tip_acted_on(self, tip_key: str, tenant_key: str) -> None:
        """Markiert einen Tip als umgesetzt."""
        await self._tip_engine._tip_cache_repo.mark_acted_on(tip_key, tenant_key)

    async def delete_conversation(self, conversation_key: str, tenant_key: str, user_key: str) -> None:
        """Loescht eine Konversation sofort (DSGVO Art. 17 Loeschrecht)."""
        await self._conversation_repo.delete(conversation_key, tenant_key, user_key)
        logger.info("ai_conversation_deleted", conversation_key=conversation_key, user_key=user_key)

    async def configure_provider(
        self,
        tenant_key: str,
        provider_data: dict,
    ) -> dict:
        """Erstellt oder aktualisiert eine Provider-Konfiguration."""
        if provider_data.get("api_key"):
            provider_data["api_key_encrypted"] = self._encrypt_key(provider_data.pop("api_key"))
        return await self._provider_config_repo.upsert(tenant_key, provider_data)

    def _encrypt_key(self, api_key: str) -> str:
        """Verschluesselt einen API-Key fuer die Speicherung."""
        # Fernet-Verschluesselung mit K8s-Secret als Master-Key
        ...

    def _decrypt_key(self, encrypted_key: str | None) -> str | None:
        """Entschluesselt einen gespeicherten API-Key."""
        if not encrypted_key:
            return None
        # Fernet-Entschluesselung
        ...
```

### 4.8 Celery-Tasks

```python
# app/tasks/ai_tasks.py

from celery import shared_task

import structlog

logger = structlog.get_logger()


@shared_task(
    name="ai.generate_daily_tips",
    bind=True,
    max_retries=2,
    default_retry_delay=600,
)
def generate_daily_tips(self) -> dict:
    """Generiert Tips fuer alle aktiven PlantingRuns (taeglich, 06:00 UTC).

    Iteriert ueber alle Tenants und aktive Runs, generiert 2-4 Tips
    pro Run via TipEngine. Bei Provider-Fehler werden regelbasierte
    Fallback-Tips generiert.
    """
    import asyncio
    from app.dependencies import get_ai_assistant_service, get_planting_run_repo

    async def _generate():
        service = get_ai_assistant_service()
        run_repo = get_planting_run_repo()
        active_runs = await run_repo.find_active_runs()

        results = {"total": 0, "success": 0, "fallback": 0, "error": 0}
        for run in active_runs:
            results["total"] += 1
            try:
                tips = await service.get_tips(
                    run["tenant_key"], "planting_run", run["_key"]
                )
                if tips:
                    results["success"] += 1
            except Exception as exc:
                results["error"] += 1
                logger.error("daily_tip_generation_failed", run_key=run["_key"], error=str(exc))

        return results

    return asyncio.run(_generate())


@shared_task(
    name="ai.reindex_vector_chunks",
    bind=True,
    max_retries=1,
    default_retry_delay=1800,
)
def reindex_vector_chunks(self) -> dict:
    """Reindexiert die Vektordatenbank (woechentlich).

    Laedt alle Species, Cultivars, GrowthPhases, Pests und Diseases
    aus ArangoDB, erzeugt Embeddings und speichert sie in pgvector.
    """
    import asyncio
    from app.dependencies import get_rag_retriever, get_species_repo

    async def _reindex():
        retriever = get_rag_retriever()
        # Species, Cultivars, Pests, Diseases aus ArangoDB laden
        # Fuer jede Entitaet: Text zusammenbauen, in 512-Token-Chunks teilen,
        # embedden und in ai_vector_chunks speichern (UPSERT)
        ...

    return asyncio.run(_reindex())


@shared_task(name="ai.cleanup_expired_conversations")
def cleanup_expired_conversations() -> dict:
    """Loescht abgelaufene Konversationen (taeglich, DSGVO-Compliance).

    Entfernt alle Konversationen deren expires_at < now().
    Loescht auch zugehoerige Edge-Dokumente.
    """
    import asyncio
    from app.dependencies import get_conversation_repo

    async def _cleanup():
        repo = get_conversation_repo()
        deleted = await repo.delete_expired()
        logger.info("ai_conversations_cleanup", deleted_count=deleted)
        return {"deleted": deleted}

    return asyncio.run(_cleanup())


@shared_task(name="ai.health_check_providers")
def health_check_providers() -> dict:
    """Prueft Provider-Availability (alle 15 Minuten).

    Testet alle aktiven Provider via health_check().
    Aktualisiert den Status in ai_provider_configs.
    Exportiert Ergebnis als Prometheus-Gauge.
    """
    import asyncio
    from app.dependencies import get_provider_config_repo

    async def _check():
        repo = get_provider_config_repo()
        configs = await repo.find_all_active()
        results = {}

        for config in configs:
            try:
                provider = AiProviderRegistry.create(
                    config["provider_type"],
                    base_url=config["base_url"],
                    model_name=config["model_name"],
                )
                healthy = await provider.health_check()
                results[config["_key"]] = healthy
            except Exception:
                results[config["_key"]] = False

        return results

    return asyncio.run(_check())
```

### 4.9 Celery-Beat Schedule

```python
# In app/celery_config.py (Ergaenzung)

CELERY_BEAT_SCHEDULE = {
    # ... bestehende Tasks ...

    "ai-generate-daily-tips": {
        "task": "ai.generate_daily_tips",
        "schedule": crontab(hour=6, minute=0),  # 06:00 UTC taeglich
    },
    "ai-reindex-vectors-weekly": {
        "task": "ai.reindex_vector_chunks",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sonntag 03:00 UTC
    },
    "ai-cleanup-conversations-daily": {
        "task": "ai.cleanup_expired_conversations",
        "schedule": crontab(hour=2, minute=30),  # 02:30 UTC taeglich
    },
    "ai-health-check-providers": {
        "task": "ai.health_check_providers",
        "schedule": 900.0,  # Alle 15 Minuten
    },
}
```

## 5. API-Endpunkte (FastAPI)

### 5.1 Tenant-scoped Endpunkte (`/api/v1/t/{tenant_slug}/ai/`)

**Provider-Konfiguration:**

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/providers` | Liste aller konfigurierten Provider (Tenant + System-Defaults) | Grower, Admin |
| `POST` | `/providers` | Neuen Provider konfigurieren (Tenant-eigener API-Key) | Admin |
| `PUT` | `/providers/{key}` | Provider-Konfiguration aktualisieren | Admin |
| `DELETE` | `/providers/{key}` | Provider deaktivieren (Soft-Delete) | Admin |
| `GET` | `/providers/{key}/health` | Provider-Availability testen | Grower, Admin |

**Tips:**

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/tips` | Aktuelle Tips fuer Kontext (`?context_type=&context_key=`) | Viewer, Grower, Admin |
| `POST` | `/tips/refresh` | Tips neu generieren (force_refresh) | Grower, Admin |
| `POST` | `/tips/{key}/dismiss` | Tip wegklicken | Viewer, Grower, Admin |
| `POST` | `/tips/{key}/acted-on` | Tip als umgesetzt markieren | Grower, Admin |

**Chat:**

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/conversations` | Liste der Chat-Verlaeufe des Nutzers | Grower, Admin |
| `POST` | `/conversations` | Neue Konversation starten | Grower, Admin |
| `GET` | `/conversations/{key}` | Konversation laden (mit Messages) | Grower, Admin |
| `POST` | `/conversations/{key}/messages` | Neue Nachricht senden (SSE Streaming-Response) | Grower, Admin |
| `DELETE` | `/conversations/{key}` | Konversation loeschen (DSGVO Art. 17) | Grower, Admin |

### 5.2 Globale Endpunkte (Platform-Admin)

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/api/v1/ai/system-providers` | System-Default-Provider verwalten | Platform-Admin |
| `POST` | `/api/v1/ai/system-providers` | System-Default-Provider erstellen | Platform-Admin |
| `PUT` | `/api/v1/ai/system-providers/{key}` | System-Default-Provider aktualisieren | Platform-Admin |
| `POST` | `/api/v1/ai/reindex` | Vektordatenbank komplett neu aufbauen | Platform-Admin |
| `GET` | `/api/v1/ai/reindex/status` | Reindex-Status abfragen | Platform-Admin |

**Gesamt: 16 Endpunkte** (11 Tenant-scoped + 5 Global)

### 5.3 Streaming-Response (SSE)

Der Chat-Endpunkt `POST /conversations/{key}/messages` unterstuetzt **Server-Sent Events (SSE)** fuer Echtzeit-Streaming:

```python
from fastapi.responses import StreamingResponse


@router.post("/conversations/{key}/messages")
async def send_message(
    key: str,
    body: ChatMessageRequest,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    service: AiAssistantService = Depends(get_ai_assistant_service),
):
    """Sendet eine Nachricht und streamt die Antwort via SSE."""

    async def event_stream():
        async for token in service.chat_stream(
            tenant_key=tenant.key,
            user_key=user.key,
            message=body.content,
            conversation_key=key,
            context_type=body.context_type,
            context_key=body.context_key,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

## 6. Frontend-Komponenten (React/MUI)

### 6.1 TipCardsPanel

**Pfad:** `src/frontend/src/components/ai/TipCardsPanel.tsx`

**Beschreibung:** Widget mit 2-4 Tipp-Karten, eingebaut in PlantingRunDetailPage, PlantInstanceDetailPage und Dashboard.

**Verhalten:**
- Laedt Tips via `GET /ai/tips?context_type=&context_key=`
- MUI `Card`-Komponenten mit Icon nach Typ:
  - `warning` → Warning-Icon (gelb/orange)
  - `care` → WaterDrop-Icon (blau)
  - `optimization` → TrendingUp-Icon (gruen)
  - `diagnosis` → BugReport-Icon (rot)
  - `milestone` → EmojiEvents-Icon (gruen)
- Priority-Anzeige als farbiger Balken am Kartenrand
- Dismiss-Button (X) pro Karte → `POST /tips/{key}/dismiss`
- "Mehr erfahren"-Button → oeffnet AiChatDrawer mit vorgetragenem Kontext
- `LoadingSkeleton` waehrend Generierung (MUI Skeleton, 4 Karten-Platzhalter)
- `EmptyState` wenn keine Tips vorhanden ("Keine Empfehlungen verfuegbar")
- Erfahrungsstufe Beginner: Vereinfachte Darstellung (kein "Mehr erfahren")
- Alle Texte via i18n: `pages.aiAssistant.tips.*`

### 6.2 AiChatDrawer

**Pfad:** `src/frontend/src/components/ai/AiChatDrawer.tsx`

**Beschreibung:** Slide-in Chat-Drawer von rechts, verfuegbar ab ExpertiseLevel `intermediate`.

**Verhalten:**
- MUI `Drawer` (anchor: right, Breite: 420px Desktop, 100% Mobile)
- Chat-Verlauf mit Bubbles:
  - User-Nachrichten: rechts, primaere Hintergrundfarbe
  - Assistent-Nachrichten: links, Surface-Hintergrundfarbe
- Streaming-Anzeige: Typing-Indicator (animierte Punkte) waehrend der Antwortgenerierung, dann Token-fuer-Token einblenden via SSE (`EventSource`)
- Kontextbadge oben im Drawer: "Chat ueber: Tomate Run #3" (mit Link zum Kontext)
- Modell-Anzeige im Footer: "Ollama - llama3.2:3b" (Chip, kleine Schrift)
- Konversationsliste: Hamburger-Menu fuer aeltere Konversationen
- Neue Konversation: "+" Button
- Konversation loeschen: Kontextmenu mit ConfirmDialog
- Tastatur: Enter sendet Nachricht, Shift+Enter fuer Zeilenumbruch
- Double-Submit-Schutz: Sende-Button disabled waehrend Streaming
- i18n: `pages.aiAssistant.chat.*`
- ExpertiseLevel Check: Nicht sichtbar fuer Beginner (REQ-021)

### 6.3 ProviderSettingsPage

**Pfad:** `src/frontend/src/pages/einstellungen/AiProviderSettingsPage.tsx`

**Beschreibung:** Verwaltung der KI-Provider-Konfigurationen.

**Verhalten:**
- Erreichbar unter `/einstellungen/ki-provider` (nur Admin/Grower, intermediate+)
- DataTable mit Providern:
  - Spalten: Name, Typ, Modell, Status (Chip: Aktiv/Inaktiv), Health (Chip: Online/Offline), Default (Stern-Icon)
  - Zeilenklick oeffnet Edit-Dialog
- "Provider hinzufuegen"-Dialog:
  - Schritt 1: Typ-Auswahl (Radio-Buttons mit Beschreibung + Datenschutz-Level)
  - Schritt 2: Dynamisches Formular je nach Typ:
    - Ollama: `base_url`, `model_name`
    - OpenAI: `api_key` (Password-Feld), `model_name` (Select: gpt-4o-mini, gpt-4o)
    - Anthropic: `api_key`, `model_name` (Select: claude-haiku-3-5, claude-sonnet-4)
    - OpenAI-kompatibel: `base_url`, `api_key`, `model_name`
  - Schritt 3: Erweiterte Einstellungen (`max_tokens`, `temperature`, `timeout_seconds`)
- Test-Button pro Provider: "Verbindung testen" → `GET /providers/{key}/health`
- Hinweis bei Cloud-Providern (MUI Alert, severity=info):
  "Daten werden an [Name] uebertragen. Dies erfordert eine DSGVO-Einwilligung aller Nutzer."
- Default-Provider setzen (Stern-Icon klickbar)
- Alle Texte via i18n: `pages.settings.aiProviders.*`

### 6.4 Consent-Dialog fuer Cloud-Provider

**Pfad:** `src/frontend/src/components/ai/AiConsentDialog.tsx`

**Beschreibung:** DSGVO-Einwilligungsdialog, erscheint automatisch beim ersten Chat mit Cloud-Provider.

**Verhalten:**
- MUI `Dialog` mit:
  - Titel: "KI-Assistent — Datenverarbeitung durch [Provider]"
  - Erklaerungstext: Welche Daten, wohin, warum
  - Checkbox: "Ich stimme der Verarbeitung meiner Pflanzendaten durch [Provider] zu."
  - Link zu Datenschutz-Einstellungen
- Ablehnung → Fallback auf lokalen Provider (falls vorhanden) oder Fehlermeldung
- Einwilligung wird als `ConsentRecord` gespeichert (REQ-025)
- i18n: `pages.aiAssistant.consent.*`

### 6.5 Integration in bestehende Seiten

| Seite | Komponente | Bedingung |
|-------|-----------|-----------|
| `PlantingRunDetailPage` | `TipCardsPanel` | Immer sichtbar (auch Beginner) |
| `PlantInstanceDetailPage` | `TipCardsPanel` | Immer sichtbar (auch Beginner) |
| `Dashboard` (REQ-009) | `TipCardsPanel` (allgemeine Tips) | Immer sichtbar |
| `MainLayout` (Sidebar/AppBar) | FAB oder AppBar-Button fuer `AiChatDrawer` | Ab Intermediate |
| `AccountSettingsPage` | Tab "KI-Assistent" | Alle |

## 7. DSGVO & Datenschutz (REQ-025)

### 7.1 Consent-Anforderungen

| Provider-Typ | Consent erforderlich | Consent-Purpose | Datenweitergabe |
|-------------|---------------------|-----------------|-----------------|
| Ollama (lokal) | Nein | — | Keine |
| llama.cpp (lokal) | Nein | — | Keine |
| OpenAI API | Ja | `ai_cloud_processing` | Pflanzenkontext + Chat-Nachrichten an OpenAI (USA) |
| Anthropic API | Ja | `ai_cloud_processing` | Pflanzenkontext + Chat-Nachrichten an Anthropic (USA) |
| OpenAI-kompatibel | Abhaengig | `ai_cloud_processing` (wenn Cloud) | Abhaengig vom Anbieter |

### 7.2 Datensparsamkeit im System-Prompt

Der System-Prompt fuer externe Provider darf **NICHT** enthalten:
- Tenant-Name oder Tenant-Slug
- Nutzername, E-Mail oder andere PII
- IP-Adressen oder Hostnames
- API-Keys oder Secrets
- Interne System-IDs (`_key`, `_id`)

Erlaubt im System-Prompt (Pflanzendaten, kein Personenbezug):
- Artname, Sortenname, Familie
- Phase, Tag in Phase
- Messwerte (EC, pH, VPD, Temperatur)
- Aktive IPM-Events (Name, nicht Nutzer-Kontext)
- Naehrstoffplan-Werte

### 7.3 Consent-Entzug

Bei Widerruf des Consents `ai_cloud_processing`:
1. Laufende Streaming-Antwort wird unterbrochen
2. Provider-Auswahl wird auf lokal zurueckgesetzt
3. Bestehende Konversationen bleiben erhalten (keine Bilddaten)
4. Weitere Cloud-Anfragen werden blockiert (HTTP 403 + Consent-Hinweis)
5. Nutzer kann Consent jederzeit erneut erteilen

### 7.4 Retention (NFR-011)

| Datentyp | Aufbewahrungsfrist | Cleanup-Mechanismus |
|----------|-------------------|---------------------|
| Chat-Konversationen | 90 Tage (konfigurierbar, Minimum: 30 Tage) | Celery-Task `cleanup_expired_conversations` (taeglich) |
| Tip-Cache | 7 Tage | `valid_until`-basiert, Celery-Cleanup |
| Provider-Konfigurationen | Permanent (kein Personenbezug) | Manuelles Loeschen |
| Vektordatenbank-Chunks | Permanent (Stammdaten, kein Personenbezug) | Reindex ueberschreibt |

### 7.5 DSGVO Art. 17 (Loeschrecht)

- `DELETE /conversations/{key}` loescht die Konversation **sofort** (nicht erst bei naechstem Cleanup)
- Alle zugehoerigen Edge-Dokumente (`ai_conversation_about`) werden mitgeloescht
- Redis-Cache-Eintraege fuer die Konversation werden invalidiert
- Loeschung wird geloggt (structlog, ohne PII im Log)

## 8. Helm Chart Erweiterungen

### 8.1 Neuer Controller: Ollama (optional)

```yaml
# helm/kamerplanter/values.yaml (Ergaenzung)

ollama:
  enabled: false  # Default: deaktiviert — explizite Aktivierung erforderlich
  controllers:
    main:
      containers:
        main:
          image:
            repository: ollama/ollama
            tag: latest
          env:
            OLLAMA_MODELS: /models
            OLLAMA_HOST: "0.0.0.0:11434"
          resources:
            requests:
              cpu: 500m
              memory: 4Gi
            limits:
              memory: 8Gi
          probes:
            liveness:
              spec:
                httpGet:
                  path: /api/tags
                  port: 11434
                initialDelaySeconds: 30
                periodSeconds: 30
            readiness:
              spec:
                httpGet:
                  path: /api/tags
                  port: 11434
                initialDelaySeconds: 10
                periodSeconds: 10
  service:
    main:
      ports:
        http:
          port: 11434
  persistence:
    models:
      enabled: true
      size: 20Gi
      accessMode: ReadWriteOnce
      mountPath: /models
```

### 8.2 Backend-Umgebungsvariablen

```yaml
# helm/kamerplanter/values.yaml (Backend-Controller Ergaenzung)

controllers:
  main:
    containers:
      main:
        env:
          # KI-Assistent Konfiguration
          AI_DEFAULT_PROVIDER: "none"  # "ollama" | "llamacpp" | "openai" | "anthropic" | "none"
          OLLAMA_BASE_URL: "http://kamerplanter-ollama:11434"
          AI_EMBEDDING_MODEL: "all-MiniLM-L6-v2"
          AI_TIPS_CACHE_TTL_HOURS: "4"
          AI_CONVERSATION_RETENTION_DAYS: "90"
          # Cloud-Provider API-Keys via K8s Secrets (NICHT in values.yaml)
          # OPENAI_API_KEY: secretKeyRef: ...
          # ANTHROPIC_API_KEY: secretKeyRef: ...
```

### 8.3 pgvector Extension

TimescaleDB benoetigt die pgvector Extension. Aktivierung via Init-Container oder Migration-Job:

```yaml
# Migration-Job (einmalig bei Erstinstallation)
initContainers:
  - name: pgvector-init
    image: timescale/timescaledb:latest-pg16
    command:
      - psql
      - -h
      - $(TIMESCALE_HOST)
      - -U
      - $(TIMESCALE_USER)
      - -d
      - $(TIMESCALE_DB)
      - -c
      - "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 8.4 Sentence-Transformers Modell

Das Embedding-Modell (`all-MiniLM-L6-v2`, ~23 MB) wird beim ersten Start automatisch heruntergeladen und im Backend-Container gecacht. Bei Air-Gapped-Deployments:

```yaml
# Optional: Modell als Volume vorinstallieren
persistence:
  models:
    enabled: true
    size: 1Gi
    mountPath: /app/.cache/torch/sentence_transformers
```

## 9. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt dokumentiert die Auth-Anforderungen
> gemaess REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung).

**Standardregel:** Alle Endpunkte erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Viewer | Grower | Admin | Platform-Admin |
|---------------------------|--------|--------|-------|----------------|
| Tips lesen | Ja | Ja | Ja | — |
| Tips dismiss/acted-on | Ja | Ja | Ja | — |
| Tips refresh | — | Ja | Ja | — |
| Chat (Conversations) | — | Ja | Ja | — |
| Chat loeschen (DSGVO) | — | Ja (eigene) | Ja (alle im Tenant) | — |
| Provider lesen | — | Ja | Ja | — |
| Provider konfigurieren | — | — | Ja | — |
| System-Provider verwalten | — | — | — | Ja |
| Reindex Vektordatenbank | — | — | — | Ja |

**ExpertiseLevel-Einschraenkungen (REQ-021):**
- **Beginner:** Nur TipCardsPanel sichtbar. Kein Chat-Zugang, keine Provider-Einstellungen.
- **Intermediate:** TipCardsPanel + AiChatDrawer. Provider-Einstellungen sichtbar (lesen).
- **Expert:** Alle Features. Voller Zugang zu Provider-Konfiguration.

## 10. Abhaengigkeiten

### 10.1 Direkte Abhaengigkeiten (MUSS vorhanden sein)

- **REQ-001** v5.0 (Stammdatenverwaltung) — Species, Cultivar als Wissensbasis fuer RAG
- **REQ-011** v1.0 (Adapter-Pattern) — Architektur-Vorbild fuer IAiProvider + Registry
- **REQ-023** v1.7 (Auth) — `user_key` fuer Conversations, JWT-Validierung
- **REQ-024** v1.4 (Mandantenverwaltung) — `tenant_key` fuer Isolation, `require_permission()`

### 10.2 Optionale Abhaengigkeiten (Synergie)

- **REQ-003** v1.0 (Phasensteuerung) — Phase als Kontext-Input fuer Tips
- **REQ-004** v3.1 (Duenge-Logik) — EC/pH-Abweichungen als Diagnose-Trigger
- **REQ-005** v2.3 (Sensorik) — Messwerte (VPD, Temperatur) als Kontext
- **REQ-010** v1.0 (IPM) — Aktive Schaedlingsbehandlungen als Kontext
- **REQ-013** v2.0 (Pflanzdurchlauf) — PlantingRun als primaerer Tip-Kontext
- **REQ-021** v1.0 (Erfahrungsstufen) — UI-Anpassung pro Level
- **REQ-022** v2.3 (Pflegeerinnerungen) — Tips ergaenzen Pflegeerinnerungen
- **REQ-025** v1.0 (DSGVO) — ConsentRecord fuer Cloud-Provider, Retention

### 10.3 Systemabhaengigkeiten

- **ArangoDB** — Persistenz von Provider-Configs, Conversations, Tip-Cache
- **TimescaleDB + pgvector** — Vektordatenbank fuer RAG
- **Redis** — Hot-Cache fuer Tips (4h TTL), Celery-Broker
- **Celery + Redis** — Periodische Tasks (daily tips, reindex, cleanup, health)
- **sentence-transformers** — Lokales Embedding-Modell (Python-Paket)
- **httpx** — Async HTTP-Client fuer Ollama/llama.cpp
- **openai** — Python SDK fuer OpenAI + kompatible APIs (optional)
- **anthropic** — Python SDK fuer Anthropic Claude API (optional)
- **cryptography (Fernet)** — API-Key-Verschluesselung

### 10.4 Externe Abhaengigkeiten (alle optional)

- **Ollama** — Lokale LLM-Inference (Docker-Image, kein API-Key)
- **OpenAI API** — Cloud-LLM (API-Key erforderlich, kostenpflichtig)
- **Anthropic API** — Cloud-LLM (API-Key erforderlich, kostenpflichtig)
- **Netzwerkzugang** — Nur fuer Cloud-Provider erforderlich

### 10.5 Wird benoetigt von

- Keine bestehende REQ haengt von REQ-031 ab (vollstaendig optional)
- Zukuenftiges REQ-009 (Dashboard) kann TipCardsPanel integrieren

## 11. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **IAiProvider-Interface:** Abstraktes Provider-Interface mit `chat()`, `chat_stream()`, `health_check()` implementiert
- [ ] **Mindestens 3 Adapter:** OllamaAdapter, OpenAiAdapter, AnthropicAdapter funktionsfaehig
- [ ] **Provider-Registry:** Neue Provider durch Registrierung anbindbar, ohne bestehenden Code zu aendern
- [ ] **RAG-Pipeline:** pgvector-basierte Vektordatenbank mit sentence-transformers Embedding funktionsfaehig
- [ ] **TipEngine:** Generiert 2-4 kontextbezogene Tips pro Anfrage
- [ ] **Regelbasierter Fallback:** Funktioniert ohne jeglichen KI-Provider
- [ ] **Chat mit Streaming:** SSE-basierte Streaming-Antworten im Frontend
- [ ] **Consent-Check:** Cloud-Provider blockiert ohne DSGVO-Einwilligung
- [ ] **Tenant-Isolation:** Conversations und Provider-Configs sind tenant-scoped
- [ ] **DSGVO-Loeschrecht:** `DELETE /conversations/{key}` loescht sofort
- [ ] **Celery-Tasks:** Taeglich Tips + Cleanup, woechentlich Reindex, 15-min Health-Check
- [ ] **Frontend-Komponenten:** TipCardsPanel, AiChatDrawer, ProviderSettingsPage, ConsentDialog
- [ ] **ExpertiseLevel-Integration:** Beginner nur Tips, Chat ab Intermediate
- [ ] **i18n:** Alle Texte in DE und EN
- [ ] **REST-Endpunkte:** 16 Endpunkte (11 Tenant-scoped + 5 Global)
- [ ] **Testabdeckung:** Unit-Tests fuer alle Adapter (gemockte Responses), Engines und Services

### Testszenarien:

**Szenario 1: Ollama lokal verfuegbar — Tips werden generiert**
```
GIVEN: Ollama laeuft lokal auf http://ollama:11434 mit Modell "llama3.2:3b"
  AND: Provider-Config "ollama-local" ist als Default konfiguriert (is_default=true)
  AND: PlantingRun "Tomate-2026" ist aktiv in Phase "flowering", Tag 12
  AND: Letzte EC-Messung: 1.8 mS/cm, pH: 6.2
WHEN: Frontend ruft GET /api/v1/t/{slug}/ai/tips?context_type=planting_run&context_key=run_key auf
THEN:
  - TipEngine baut PlantingRun-Kontext auf
  - RAG-Retrieval findet relevante Chunks (z.B. "Tomate Bluete VPD-Ziele")
  - Ollama generiert 2-4 Tips als JSON-Array
  - Tips werden in Redis (4h TTL) und ArangoDB (24h) gecacht
  - Response enthaelt Tips mit tip_type, priority, title, body
```

**Szenario 2: Kein Provider konfiguriert — regelbasierte Fallback-Tips**
```
GIVEN: AI_DEFAULT_PROVIDER = "none"
  AND: Keine Provider in ai_provider_configs eingetragen
  AND: PlantingRun "Basilikum-2026" ist aktiv, EC = 3.2 mS/cm (zu hoch)
WHEN: Frontend ruft GET /tips auf
THEN:
  - TipEngine erkennt: kein Provider verfuegbar
  - _rule_based_fallback() wird aufgerufen
  - Generiert Warning-Tip: "EC-Wert zu hoch" mit priority "high"
  - Kein LLM-Aufruf erfolgt
  - Response wird normal gecacht
```

**Szenario 3: OpenAI konfiguriert, kein Consent — Fehlermeldung mit Fallback**
```
GIVEN: Provider "openai-gpt4o" ist als Default konfiguriert (requires_consent=true)
  AND: Nutzer hat KEINEN Consent "ai_cloud_processing" erteilt
  AND: Ollama ist als Fallback-Provider vorhanden (is_default=false)
WHEN: Nutzer startet Chat-Nachricht
THEN:
  - ConsentService.check_consent() gibt false zurueck
  - ConsentRequiredError wird geworfen
  - Frontend zeigt AiConsentDialog
  - Bei Ablehnung: System wechselt auf Ollama-Provider
  - Bei Zustimmung: ConsentRecord wird gespeichert, Chat wird fortgesetzt
```

**Szenario 4: Chat-Nachricht mit Pflanzen-Kontext**
```
GIVEN: Nutzer hat Conversation offen fuer PlantingRun "Cannabis-Bluete-R3"
  AND: Run ist in Phase "flowering", Tag 28
  AND: Letzte EC: 2.1 mS/cm, VPD: 1.1 kPa
WHEN: Nutzer fragt "Soll ich den PK-Boost schon starten?"
THEN:
  - ContextBuilder aggregiert Run-Kontext (Phase, EC, VPD)
  - RAG findet Chunks zu "Cannabis flowering PK-Boost Timing"
  - System-Prompt enthaelt Phase, Tag, Messwerte — KEIN Nutzername/Tenant
  - Provider-Antwort bezieht sich auf Tag 28 Flowering und aktuelle EC
  - Conversation wird mit User- und Assistant-Nachricht aktualisiert
```

**Szenario 5: Provider-Health-Check — inaktiver Provider wird nicht verwendet**
```
GIVEN: Ollama-Provider ist konfiguriert und als Default gesetzt
  AND: Ollama-Container ist gestoppt (Port 11434 nicht erreichbar)
WHEN: health_check_providers Celery-Task laeuft
THEN:
  - OllamaAdapter.health_check() gibt false zurueck
  - Provider-Status wird als "unhealthy" markiert
  - Prometheus-Gauge "ai_provider_healthy" wird auf 0 gesetzt
  - Naechste Tip-Anfrage faellt auf regelbasierten Fallback zurueck
```

**Szenario 6: Tip-Cache-Hit — keine neue LLM-Anfrage**
```
GIVEN: Tips fuer PlantingRun "run_123" wurden vor 2 Stunden generiert
  AND: Redis-Cache enthaelt gueltige Tips (TTL 4h)
WHEN: Frontend ruft GET /tips?context_type=planting_run&context_key=run_123 auf
THEN:
  - TipEngine findet Cache-Hit in Redis
  - Kein ContextBuilder-Aufruf, kein RAG-Retrieval, kein LLM-Aufruf
  - Gecachte Tips werden direkt zurueckgegeben
  - Response-Time < 50ms
```

**Szenario 7: Conversation loeschen (DSGVO Art. 17)**
```
GIVEN: Nutzer hat Conversation "conv_abc" mit 15 Nachrichten
WHEN: Nutzer ruft DELETE /conversations/conv_abc auf
THEN:
  - Conversation wird sofort aus ArangoDB geloescht (kein Soft-Delete)
  - Edge "ai_conversation_about" wird mitgeloescht
  - Redis-Cache fuer diese Conversation wird invalidiert
  - structlog-Eintrag: "ai_conversation_deleted" (ohne Nachrichteninhalte)
  - Response: HTTP 204 No Content
```

**Szenario 8: Vektordatenbank leer (erstes Setup) — Fallback**
```
GIVEN: TimescaleDB ai_vector_chunks-Tabelle ist leer (frische Installation)
  AND: Ollama-Provider ist konfiguriert und erreichbar
WHEN: Frontend ruft GET /tips auf
THEN:
  - RAG-Retrieval findet keine Chunks (leere Tabelle)
  - System-Prompt enthaelt nur Pflanzen-Kontext, keine RAG-Wissensbasis
  - Ollama generiert Tips nur auf Basis des Kontext (ohne RAG)
  - ODER bei niedrigem Konfidenz-Level: regelbasierte Fallback-Tips
  - Hinweis im Response: "Wissensbasis wird aufgebaut (naechster Reindex: Sonntag 03:00)"
```

**Szenario 9: Streaming — Antwort wird Token-fuer-Token angezeigt**
```
GIVEN: Nutzer hat aktive Conversation mit Ollama-Provider
WHEN: Nutzer sendet POST /conversations/{key}/messages mit Nachricht
THEN:
  - Server antwortet mit Content-Type: text/event-stream
  - Tokens werden einzeln als SSE-Events gesendet: "data: {"token": "Das"}\n\n"
  - Frontend zeigt Typing-Indicator, dann Token-fuer-Token die Antwort
  - Letztes Event: "data: [DONE]\n\n"
  - Conversation wird erst nach vollstaendiger Antwort in ArangoDB gespeichert
```

**Szenario 10: Mehrmandantenfaehigkeit — Tenant-Isolation**
```
GIVEN: Tenant A hat 5 Conversations und eigenen OpenAI-Provider
  AND: Tenant B hat 3 Conversations und nutzt System-Default Ollama
WHEN: Nutzer von Tenant B ruft GET /conversations auf
THEN:
  - Nur die 3 Conversations von Tenant B werden zurueckgegeben
  - Provider-Liste zeigt: System-Default Ollama (kein OpenAI von Tenant A)
  - Tips von Tenant A sind nicht sichtbar
  - AQL-Queries filtern immer auf tenant_key
```

**Szenario 11: ExpertiseLevel Beginner — nur TipCards, kein Chat**
```
GIVEN: Nutzer hat ExpertiseLevel "beginner" (REQ-021)
  AND: KI-Provider ist konfiguriert und verfuegbar
WHEN: Nutzer oeffnet PlantingRunDetailPage
THEN:
  - TipCardsPanel wird angezeigt (vereinfacht: kein "Mehr erfahren"-Button)
  - AiChatDrawer-FAB ist nicht sichtbar
  - Provider-Einstellungen sind nicht im Menue
  - API-Endpunkte /conversations/* geben 403 bei Beginner-Level zurueck
```

**Szenario 12: Cloud-Provider-Timeout — Fehler-Handling mit Fallback**
```
GIVEN: OpenAI ist als Default-Provider konfiguriert
  AND: OpenAI API antwortet nicht innerhalb von 30 Sekunden (Timeout)
  AND: Ollama ist als Fallback-Provider vorhanden
WHEN: Nutzer sendet Chat-Nachricht
THEN:
  - httpx.TimeoutException wird gefangen
  - structlog.warning("ai_provider_timeout", provider="openai", timeout_seconds=30)
  - Automatischer Fallback auf Ollama-Provider
  - Antwort wird ueber Ollama generiert (ggf. langsamere/kuerzere Antwort)
  - UI zeigt Hinweis: "Antwort vom lokalen Modell (Cloud-Provider nicht verfuegbar)"
```

**Szenario 13: API-Key-Verschluesselung**
```
GIVEN: Admin konfiguriert OpenAI-Provider mit API-Key "sk-abc123..."
WHEN: Provider wird gespeichert
THEN:
  - API-Key wird mit Fernet (Master-Key aus K8s Secret) verschluesselt
  - ai_provider_configs enthaelt api_key_encrypted (nicht Klartext)
  - GET /providers gibt api_key_encrypted NICHT zurueck (nur "has_api_key: true")
  - Bei Provider-Nutzung wird der Key entschluesselt und an den Adapter uebergeben
```

**Szenario 14: Gleichzeitige Tip-Generierung (Concurrency)**
```
GIVEN: Celery-Task "generate_daily_tips" laeuft fuer 50 aktive Runs
WHEN: Nutzer fragt gleichzeitig Tips fuer denselben Run an
THEN:
  - Redis-Lock verhindert doppelte Generierung fuer denselben Kontext
  - Zweite Anfrage wartet auf Cache oder nutzt Lock-Timeout-Fallback
  - Kein doppelter LLM-Aufruf fuer identischen Kontext
```

---

**Hinweise fuer RAG-Integration:**
- Keywords: KI-Assistent, Chat, Pflanzenberatung, Tips, LLM, Ollama, OpenAI, Anthropic, RAG, Vektordatenbank, pgvector, Embedding, Streaming, SSE
- Fachbegriffe: Retrieval-Augmented Generation, Cosine-Similarity, Adapter-Pattern, Graceful Degradation, Consent, Provider-Registry, System-Prompt, Token-Streaming
- Verknuepfung: Nutzt REQ-011 (Adapter-Pattern), REQ-023/024 (Auth/Tenant), REQ-025 (DSGVO). Liefert Kontext-Tips fuer REQ-003 (Phase), REQ-004 (Duengung), REQ-010 (IPM), REQ-022 (Pflege).
