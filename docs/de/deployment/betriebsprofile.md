# Betriebsprofile

Kamerplanter ist modular aufgebaut. Du entscheidest selbst, welche Komponenten du brauchst — von einer schlanken Installation auf dem Raspberry Pi bis zum vollständigen Multi-Tenant-Setup auf Kubernetes. Diese Seite hilft dir, das richtige Profil für deinen Anwendungsfall zu finden.

---

## Komponentenübersicht

Jede Kamerplanter-Installation besteht aus einem **Kern** (immer erforderlich) und **optionalen Komponenten**, die du je nach Bedarf aktivierst.

### Kern (immer aktiv)

| Komponente | Aufgabe |
|------------|---------|
| **Backend** (FastAPI) | REST-API, Geschäftslogik, Phasensteuerung, Düngeplanе |
| **Frontend** (React) | Web-Oberfläche |
| **ArangoDB** | Primäre Datenbank (Dokumente + Graph-Abfragen) |
| **Valkey** (Redis-kompatibel) | Cache und Celery-Broker |
| **Celery Worker + Beat** | Hintergrundaufgaben (Pflegeerinnerungen, Datenanreicherung, KI-Tipps) |

### Optionale Komponenten

| Komponente | Aufgabe | Ressourcenbedarf | Konfiguration |
|------------|---------|------------------|---------------|
| **Betriebsmodus** | `light` = kein Login, ein Nutzer; `full` = JWT-Auth, Multi-Tenant | — | `KAMERPLANTER_MODE` |
| **KI-Assistent** | Pflegetipps, Diagnosen, Empfehlungen per Sprachmodell | 2--8 GB RAM (lokal) | `AI_DEFAULT_PROVIDER` |
| **Ollama** | Lokale Ausführung von Sprachmodellen (kein Datentransfer) | 4--16 GB RAM, optional GPU | Docker-Profil `ollama` |
| **Knowledge Service** | RAG-Pipeline: Wissensbasis durchsuchen, Kontext anreichern | 512 MB RAM | Eigenes Deployment |
| **VectorDB** (pgvector) | Vektorspeicher für RAG-Embeddings | 256 MB RAM | `VECTORDB_ENABLED` |
| **Embedding Service** | ONNX-basierte Embedding-Berechnung (kein PyTorch) | 512 MB RAM | Eigenes Deployment |
| **Reranker Service** | Cross-Encoder Re-Ranking für höhere RAG-Präzision (ADR-007) | 1,5–4 GB RAM | `RERANKER_URL` |
| **TimescaleDB** | Zeitreihendaten von Sensoren, automatisches Downsampling | 256--512 MB RAM | `TIMESCALEDB_ENABLED` |
| **Home Assistant** | Sensor- und Aktor-Integration (Temperatur, Luftfeuchte, Lampen) | Extern | `HA_URL` + `HA_ACCESS_TOKEN` |
| **Externe Datenanreicherung** | Pflanzendaten von GBIF und Perenual automatisch ergänzen | — | `PERENUAL_API_KEY` |

---

## Profile im Überblick

Die folgende Matrix zeigt fünf vordefinierte Profile. Jedes Profil ist eine Empfehlung — du kannst jederzeit einzelne Komponenten hinzufügen oder weglassen.

| | Minimal | Hobby | Standard | Profi | SaaS |
|---|:---:|:---:|:---:|:---:|:---:|
| **Infrastruktur** | Docker Compose | Docker Compose | Docker Compose / K8s | Kubernetes | Kubernetes |
| **Betriebsmodus** | Light | Light | Full | Full | Full |
| **KI-Assistent** | — | Ollama (lokal) | Ollama (lokal) | Ollama + Cloud-Fallback | Cloud (OpenAI / Anthropic) |
| **Knowledge Service + RAG** | — | — | Optional | Ja | Ja |
| **Reranker Service** | — | — | Optional | Optional | Ja |
| **TimescaleDB** | — | — | Optional | Ja | Ja |
| **Home Assistant** | — | Optional | Optional | Ja | Optional |
| **Externe Anreicherung** | — | Optional | Ja | Ja | Ja |
| **Celery Worker** | Ja | Ja | Ja | Ja | Ja |
| **Zielgruppe** | Raspberry Pi, Ausprobieren | Hobby-Gärtner, Home-Server | Engagierte Hobbyisten, kleine Gemeinschaftsgärten | Indoor-Growing, große Gemeinschaftsgärten | Managed Hosting, mehrere Mandanten |
| **RAM gesamt** | ~1 GB | ~3 GB | ~4 GB | ~6 GB | ~8 GB |

---

## Minimal

### Zielgruppe

Du willst Kamerplanter schnell ausprobieren oder hast nur wenige Zimmerpflanzen. Ein Raspberry Pi 4/5 oder ein alter Laptop reicht aus. Du brauchst weder Login noch KI.

### Voraussetzungen

- Docker + Docker Compose
- 1 GB freier RAM, 2 GB Speicherplatz
- Raspberry Pi 4 (2 GB), Raspberry Pi 5, NUC, Laptop

### Aktivierte Komponenten

- [x] Backend + Frontend
- [x] ArangoDB + Valkey
- [x] Celery Worker + Beat
- [ ] KI-Assistent
- [ ] TimescaleDB
- [ ] Home Assistant
- [ ] Knowledge Service / RAG

### Beispielkonfiguration

```yaml title="docker-compose.yml (Auszug)"
services:
  arangodb:
    image: arangodb:3.11
    # ...

  valkey:
    image: valkey/valkey:8-alpine
    # ...

  backend:
    build: ./src/backend
    environment:
      KAMERPLANTER_MODE: light
      AI_DEFAULT_PROVIDER: none
      TIMESCALEDB_ENABLED: "false"
      VECTORDB_ENABLED: "false"
    depends_on: [arangodb, valkey]

  celery-worker:
    build: ./src/backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on: [arangodb, valkey]

  celery-beat:
    build: ./src/backend
    command: celery -A app.tasks beat --loglevel=info
    depends_on: [arangodb, valkey]

  frontend:
    build: ./src/frontend
    environment:
      KAMERPLANTER_MODE: light
    depends_on: [backend]
```

### Was fehlt im Vergleich zum nächsten Profil?

Ohne KI-Assistent bekommst du keine automatischen Pflegetipps und Diagnosen. Du kannst Ollama jederzeit später hinzufügen, ohne Daten zu verlieren.

---

## Hobby

### Zielgruppe

Du hast 10--50 Pflanzen und einen Home-Server (NAS, alter Desktop, NUC). Du möchtest KI-gestützte Pflegetipps, aber deine Daten sollen dein Netzwerk nicht verlassen. Login brauchst du nicht — du bist der einzige Nutzer.

### Voraussetzungen

- Docker + Docker Compose
- 4 GB freier RAM (8 GB mit 7B-Modell), optional GPU
- Home-Server, NUC, Desktop-PC

### Aktivierte Komponenten

- [x] Backend + Frontend
- [x] ArangoDB + Valkey
- [x] Celery Worker + Beat
- [x] Ollama (lokales Sprachmodell)
- [ ] Knowledge Service / RAG (optional aktivierbar)
- [ ] TimescaleDB
- [ ] Home Assistant (optional)
- [ ] Externe Anreicherung (optional)

### Beispielkonfiguration

```yaml title="docker-compose.yml (Auszug)"
services:
  # ... Kern wie Minimal ...

  backend:
    build: ./src/backend
    environment:
      KAMERPLANTER_MODE: light
      AI_DEFAULT_PROVIDER: ollama
      AI_OLLAMA_URL: http://ollama:11434
      AI_OLLAMA_MODEL: gemma3:4b
      TIMESCALEDB_ENABLED: "false"
    depends_on: [arangodb, valkey]

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/models
    # GPU-Passthrough (optional):
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - capabilities: [gpu]
```

!!! tip "Modellwahl"
    Starte mit `gemma3:4b` — das läuft auf den meisten Rechnern ab 2020 ohne GPU. Details zur Modellwahl findest du unter [KI-Provider einrichten](../user-guide/ai-providers.md#ollama-lokal-empfohlen).

### Was fehlt im Vergleich zum nächsten Profil?

Ohne Full-Modus kannst du keine weiteren Nutzer einladen. Ohne TimescaleDB werden Sensordaten nicht langfristig gespeichert. Beides lässt sich später aktivieren.

---

## Standard

### Zielgruppe

Du bist engagierter Hobbyist oder betreibst einen kleinen Gemeinschaftsgarten. Mehrere Personen sollen eigene Konten haben. Du möchtest KI-Tipps und optional Sensordaten langfristig speichern.

### Voraussetzungen

- Docker Compose oder Kubernetes-Cluster
- 4--6 GB freier RAM
- Server, NUC oder kleiner K8s-Cluster

### Aktivierte Komponenten

- [x] Backend + Frontend
- [x] ArangoDB + Valkey
- [x] Celery Worker + Beat
- [x] Ollama (lokales Sprachmodell)
- [x] Externe Anreicherung (GBIF + Perenual)
- [ ] Knowledge Service / RAG (optional)
- [ ] TimescaleDB (optional)
- [ ] Home Assistant (optional)

### Beispielkonfiguration

=== "Docker Compose"

    ```yaml title="docker-compose.yml (Auszug)"
    services:
      # ... Kern + Ollama ...

      backend:
        build: ./src/backend
        environment:
          KAMERPLANTER_MODE: full
          AI_DEFAULT_PROVIDER: ollama
          AI_OLLAMA_URL: http://ollama:11434
          AI_OLLAMA_MODEL: gemma3:4b
          JWT_SECRET_KEY: ${JWT_SECRET_KEY}  # openssl rand -hex 32
          PERENUAL_API_KEY: ${PERENUAL_API_KEY}
          TIMESCALEDB_ENABLED: ${TIMESCALEDB_ENABLED:-false}
        depends_on: [arangodb, valkey]
    ```

=== "Helm Values"

    ```yaml title="values.yaml (Auszug)"
    controllers:
      backend:
        containers:
          main:
            env:
              KAMERPLANTER_MODE: full
              AI_DEFAULT_PROVIDER: ollama
              AI_OLLAMA_URL: http://ollama:11434
              AI_OLLAMA_MODEL: gemma3:4b
              TIMESCALEDB_ENABLED: "false"
    ```

!!! note "TimescaleDB nur bei Sensoren nötig"
    Wenn du keine Sensoren oder Home-Assistant-Anbindung planst, kannst du TimescaleDB weglassen. Manuelle Messwerte werden in ArangoDB gespeichert. TimescaleDB lohnt sich erst bei automatischer, hochfrequenter Datenerfassung.

### Was fehlt im Vergleich zum nächsten Profil?

Ohne TimescaleDB kein automatisches Downsampling von Sensordaten. Ohne Home Assistant keine automatische Sensorerfassung und Aktorsteuerung. Ohne Knowledge Service / RAG keine kontextangereicherten KI-Antworten aus der Wissensbasis.

---

## Profi

### Zielgruppe

Du betreibst professionelles Indoor-Growing oder einen großen Gemeinschaftsgarten mit Rollenverwaltung. Sensoren und Aktoren sind über Home Assistant angebunden. Du willst lückenlose Zeitreihen, KI-gestützte Diagnosen mit RAG-Kontext und Cloud-Fallback für das Sprachmodell.

### Voraussetzungen

- Kubernetes-Cluster (3+ Nodes empfohlen)
- 6--8 GB RAM für Kamerplanter-Pods
- Home Assistant Instanz im Netzwerk
- Optional: GPU-Node für schnellere KI-Inferenz

### Aktivierte Komponenten

- [x] Backend + Frontend
- [x] ArangoDB + Valkey
- [x] Celery Worker + Beat
- [x] Ollama + Cloud-Fallback (OpenAI oder Anthropic)
- [x] Knowledge Service + VectorDB + Embedding Service
- [x] Reranker Service (Cross-Encoder Re-Ranking)
- [x] TimescaleDB
- [x] Home Assistant
- [x] Externe Anreicherung (GBIF + Perenual)

### Beispielkonfiguration

```yaml title="values.yaml (Auszug)"
controllers:
  backend:
    containers:
      main:
        env:
          KAMERPLANTER_MODE: full
          AI_DEFAULT_PROVIDER: ollama
          AI_OLLAMA_URL: http://ollama:11434
          AI_OLLAMA_MODEL: mistral:7b
          AI_FALLBACK_PROVIDER: openai
          AI_OPENAI_API_KEY:
            secretKeyRef:
              name: kamerplanter-secrets
              key: openai-api-key
          TIMESCALEDB_ENABLED: "true"
          TIMESCALEDB_HOST: timescaledb
          HA_URL: http://homeassistant.home:8123
          HA_ACCESS_TOKEN:
            secretKeyRef:
              name: kamerplanter-secrets
              key: ha-access-token
          PERENUAL_API_KEY:
            secretKeyRef:
              name: kamerplanter-secrets
              key: perenual-api-key

  timescaledb:
    enabled: true

  knowledge-service:
    enabled: true
    containers:
      main:
        env:
          RERANKER_URL: "http://kamerplanter-ki-reranker-service:8081"
          RERANKER_INITIAL_K: "20"
          RERANKER_TOP_K: "5"

  reranker-service:
    enabled: true
    containers:
      main:
        env:
          RERANKER_MODEL: "bge-reranker-v2-m3"

  embedding-service:
    enabled: true

  vectordb:
    enabled: true
```

!!! warning "Secrets nicht in values.yaml"
    API-Keys und Tokens gehören in Kubernetes Secrets oder einen externen Secret-Manager (z.B. Sealed Secrets, External Secrets Operator). Verwende `secretKeyRef` in den Helm Values.

### Was fehlt im Vergleich zum nächsten Profil?

Im Profi-Profil betreibst du eine einzelne Instanz für deine Organisation. Das SaaS-Profil fügt Multi-Mandanten-Isolation, horizontale Skalierung und Cloud-KI als Primärprovider hinzu.

---

## SaaS / Multi-Tenant

### Zielgruppe

Du betreibst Kamerplanter als Plattform für mehrere unabhängige Mandanten (Gärten, Betriebe, Gemeinschaften). Jeder Mandant hat eigene Daten, Rollen und Einstellungen. Du brauchst horizontale Skalierung und zuverlässige Cloud-KI.

### Voraussetzungen

- Kubernetes-Cluster mit Autoscaling
- 8+ GB RAM für Kamerplanter-Pods
- Managed-Datenbank-Dienste empfohlen (ArangoDB Oasis, Managed PostgreSQL)
- Cloud-KI-Provider-Konto (OpenAI oder Anthropic)

### Aktivierte Komponenten

- [x] Backend + Frontend (mehrere Replicas)
- [x] ArangoDB + Valkey
- [x] Celery Worker (mehrere Replicas) + Beat
- [x] Cloud-KI (OpenAI / Anthropic)
- [x] Knowledge Service + VectorDB + Embedding Service
- [x] TimescaleDB
- [x] Externe Anreicherung (GBIF + Perenual)
- [ ] Home Assistant (optional, mandantenspezifisch)

### Beispielkonfiguration

```yaml title="values.yaml (Auszug)"
controllers:
  backend:
    replicas: 3
    containers:
      main:
        env:
          KAMERPLANTER_MODE: full
          AI_DEFAULT_PROVIDER: openai
          AI_OPENAI_MODEL: gpt-4o-mini
          TIMESCALEDB_ENABLED: "true"

  celery-worker:
    replicas: 2

  frontend:
    replicas: 2
```

!!! tip "Managed Datenbanken"
    Im SaaS-Betrieb empfiehlt sich der Einsatz von Managed-Datenbank-Diensten statt selbst betriebener Container. Das reduziert den Betriebsaufwand für Backups, Updates und Hochverfügbarkeit erheblich.

---

## Eigenes Profil zusammenstellen

Die Profile oben sind Empfehlungen. Du kannst jede Komponente einzeln aktivieren oder deaktivieren, indem du die entsprechenden Umgebungsvariablen setzt:

| Entscheidung | Variable | Werte |
|-------------|----------|-------|
| Login und Multi-Tenant? | `KAMERPLANTER_MODE` | `light` / `full` |
| KI-Pflegetipps? | `AI_DEFAULT_PROVIDER` | `ollama`, `llamacpp`, `openai`, `anthropic`, `openai-compatible`, `none` |
| Sensordaten-Zeitreihen? | `TIMESCALEDB_ENABLED` | `true` / `false` |
| RAG-Wissensbasis? | `VECTORDB_ENABLED` | `true` / `false` |
| Re-Ranking (höhere Präzision)? | `RERANKER_URL` | HTTP-URL des Reranker-Service (leer = deaktiviert) |
| Home Assistant? | `HA_URL` + `HA_ACCESS_TOKEN` | URL + Token (leer = deaktiviert) |
| Pflanzendaten-Anreicherung? | `PERENUAL_API_KEY` | API-Key (leer = nur GBIF) |

In Docker Compose aktivierst du optionale Dienste über Profile:

```bash
# Nur Kern:
docker compose up -d

# Mit Ollama und TimescaleDB:
docker compose --profile ollama --profile timescaledb up -d

# Mit RAG (Knowledge Service + VectorDB + Reranker):
docker compose --profile ollama --profile timescaledb --profile vectordb up -d
```

!!! note "Reranker im Docker-Compose-Profil `vectordb`"
    Der `reranker-service` ist dem Docker-Compose-Profil `vectordb` zugeordnet und wird zusammen mit Knowledge Service und VectorDB gestartet. Der Reranker ist ressourcenintensiver als Embedding Service und VectorDB — auf schwacher Hardware kann `RERANKER_URL` leer gelassen werden, um nur Hybrid Search ohne Re-Ranking zu nutzen.

Eine vollständige Liste aller Umgebungsvariablen findest du unter [Umgebungsvariablen](../reference/environment-variables.md).

---

## Entscheidungshilfe

Das folgende Flussdiagramm hilft dir, ein passendes Profil zu finden:

<!-- diagram-source: user-described — decision tree selecting a deployment profile by user count and feature needs -->
```mermaid
flowchart TD
    A[How many users?] -->|Just me| B{Do you need AI tips?}
    A -->|2-10 people| D{Kubernetes available?}
    A -->|10+ / tenants| G[SaaS / Multi-Tenant]

    B -->|No| C[Minimal]
    B -->|Yes| E[Hobby]

    D -->|No| F[Standard<br/>Docker Compose]
    D -->|Yes| H{Sensors / HA?}

    H -->|No| F2[Standard<br/>Kubernetes]
    H -->|Yes| I[Professional]
```

---

## Häufige Fragen

### Kann ich später auf ein größeres Profil wechseln?

Ja. Alle Profile nutzen dieselbe Datenbank. Du kannst jederzeit Komponenten hinzufügen (z.B. Ollama aktivieren, TimescaleDB starten, von Light auf Full wechseln), ohne Daten zu verlieren. Beim Wechsel von Light auf Full musst du einmalig ein Passwort für den bestehenden System-Benutzer setzen.

### Kann ich Ollama auf einem Raspberry Pi ausführen?

Ja, ab dem Raspberry Pi 5 mit 8 GB RAM. Verwende ein kleines Modell wie `llama3.2:3b`. Die Antwortzeiten liegen bei 15--30 Sekunden pro Tipp — akzeptabel, aber nicht schnell. Auf dem Raspberry Pi 4 ist die Leistung für größere Modelle nicht ausreichend.

### Brauche ich TimescaleDB, wenn ich keine Sensoren habe?

Nein. Ohne automatische Sensordatenerfassung (IoT/MQTT oder Home Assistant) bringt TimescaleDB keinen Vorteil. Manuelle Messwerte (pH, EC) werden in ArangoDB gespeichert. Du kannst TimescaleDB später aktivieren, wenn du Sensoren anbindest.

### Was passiert, wenn ich keinen KI-Provider konfiguriere?

Kamerplanter funktioniert vollständig ohne KI. Wenn `AI_DEFAULT_PROVIDER=none` gesetzt ist (oder kein Provider konfiguriert), werden die KI-Tipp-Karten in der Oberfläche nicht angezeigt. Alle regelbasierten Funktionen (Phasensteuerung, Düngepläne, Pflegeerinnerungen) arbeiten unabhängig vom KI-Provider.

---

## Siehe auch

- [Light-Modus](../user-guide/light-mode.md) — Details zum Betrieb ohne Authentifizierung
- [KI-Provider einrichten](../user-guide/ai-providers.md) — Ollama, OpenAI, Anthropic und andere Provider konfigurieren
- [Home Assistant Integration](../guides/home-assistant-integration.md) — Sensor- und Aktor-Anbindung
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Variablenreferenz
- [Kubernetes](kubernetes.md) — Cluster-Setup und Deployment
- [Infrastruktur — Skaffold-Profile](../architecture/infrastructure.md#skaffold-profile-und-module) — Skaffold-Module (`-m ki`) für den KI-Stack
