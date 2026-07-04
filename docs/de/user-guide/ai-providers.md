# KI-Provider einrichten

!!! info "Provider-Konfiguration erfolgt über Betreiber-Env-Vars, nicht über die Oberfläche"
    Es gibt keine Klickstrecke "Einstellungen > KI-Provider" in der Kamerplanter-Oberfläche. Der KI-Provider wird ausschließlich über **Umgebungsvariablen am Knowledge-Service** konfiguriert (`src/knowledge-service/app/config.py`) — das ist eine Betreiber-Aufgabe (Helm-Values / `.env` / Kubernetes-Secret), keine Nutzer-Einstellung. Diese Seite erklärt die Einrichtung für Selbsthoster und Plattformbetreiber. Die Ollama-Installationsanleitungen und Hardware-Empfehlungen weiter unten gelten unverändert.

Kamerplanter unterstützt mehrere KI-Provider, die je nach Hardware, Datenschutzanforderungen und Budget gewählt werden können. Diese Seite erklärt, wie jeder Provider eingerichtet und am Knowledge-Service konfiguriert wird.

---

## Voraussetzungen

- Kamerplanter (inkl. Knowledge-Service) ist deployt
- Zugriff auf die Umgebungsvariablen-Konfiguration des Knowledge-Service (Helm `values.yaml`, `.env`-Datei oder Kubernetes-Secret) — Betreiber-Rolle

---

## Übersicht der relevanten Umgebungsvariablen

| Variable | Beschreibung | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `anthropic`, `ollama` oder `openai_compatible` | `ollama` |
| `LLM_API_URL` | Basis-URL des Providers (bei Ollama/OpenAI-kompatibel) | `http://ollama:11434` |
| `LLM_API_KEY` | API-Key (bei Anthropic/OpenAI-kompatibel, falls erforderlich) | leer |
| `LLM_MODEL` | Modellname | `gemma3:12b` |
| `LLM_MAX_TOKENS` | Maximale Antwortlänge | `2048` |
| `LLM_TEMPERATURE` | Kreativität der Antworten (0.0–1.0) | `0.1` |

!!! warning "RAM-Hinweis zum Default-Modell"
    Der Default `gemma3:12b` benötigt deutlich mehr RAM/VRAM als kleinere Modelle (siehe Hardware-Tabelle unten). Auf kleinerer Hardware sollte `LLM_MODEL` explizit auf ein passendes Modell gesetzt werden (z.B. `llama3.2:3b` oder `gemma3:4b`).

## Übersicht der Provider

| Provider | Typ | Datenschutz | Kosten | Empfehlung |
|----------|-----|-------------|--------|------------|
| [Ollama](#ollama-lokal-empfohlen) | Lokal | Keine Datenweitergabe | Kostenlos | Self-Hosted |
| [llama.cpp HTTP Server](#llamacpp-http-server) | Lokal | Keine Datenweitergabe | Kostenlos | Fortgeschrittene |
| [OpenAI API](#openai-api) | Cloud | Übertragung an OpenAI (USA) | Pay-per-Token | Beste Qualität |
| [Anthropic Claude API](#anthropic-claude-api) | Cloud | Übertragung an Anthropic (USA) | Pay-per-Token | Beste Qualität |
| [OpenAI-kompatible APIs](#openai-kompatible-apis) | Lokal oder Cloud | Abhängig | Variabel | Fortgeschrittene |

!!! tip "Empfehlung für den Einstieg"
    Bei Self-Hosting: Starte mit **Ollama + gemma3:4b**. Das Modell läuft auf den meisten Desktop-Rechnern ab 2020 ohne GPU und gibt keine Daten weiter.

---

## Ollama (lokal, empfohlen)

Ollama ist ein Programm, das Sprachmodelle lokal auf einem Rechner oder Server ausführt. Keine Daten verlassen das Netzwerk.

### Hardware-Anforderungen

| Hardware | RAM | Empfohlenes Modell | Antwortzeit (Tipp-Karten) |
|----------|-----|--------------------|--------------------------|
| Raspberry Pi 5, ältere NUCs | 8 GB | `llama3.2:3b` | 15–30 Sekunden |
| Desktop/Laptop ab 2020 | 16 GB | `gemma3:4b` | 10–20 Sekunden |
| Grafikkarte 6–8 GB VRAM (GTX 1060, RX 580) | — | `mistral:7b` | 2–5 Sekunden |
| Grafikkarte 12 GB VRAM (RTX 3060) | — | `llama3.1:8b` | 1–3 Sekunden |
| Grafikkarte 16 GB VRAM und mehr | — | `mistral-small:22b` | 2–5 Sekunden |

!!! note "Warum kleine Modelle gut funktionieren"
    Kamerplanter sendet einen präzisen Kontext (aktuelle Phase, EC/pH/VPD, Pflegehistorie) direkt ans Modell. Ein 4B-Modell mit konkretem Kontext liefert bessere Pflanzen-Tipps als ein 70B-Modell ohne Kontext.

### Ollama installieren

=== "Linux"

    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

    Der Ollama-Dienst startet automatisch und ist unter `http://localhost:11434` erreichbar.

=== "macOS"

    Lade den Installer von [ollama.com/download](https://ollama.com/download) herunter und öffne die `.dmg`-Datei.

    Nach der Installation erscheint das Ollama-Symbol in der Menüleiste.

=== "Windows"

    Lade den Installer von [ollama.com/download](https://ollama.com/download) herunter und führe ihn aus.

    Ollama läuft als Hintergrunddienst und ist unter `http://localhost:11434` erreichbar.

=== "Docker"

    ```bash
    docker run -d --name ollama \
      -p 11434:11434 \
      -v ollama_data:/root/.ollama \
      ollama/ollama
    ```

    Mit GPU-Unterstützung (NVIDIA):

    ```bash
    docker run -d --name ollama \
      --gpus all \
      -p 11434:11434 \
      -v ollama_data:/root/.ollama \
      ollama/ollama
    ```

### Modell herunterladen

Öffne ein Terminal und lade das empfohlene Modell herunter:

```bash
# Empfehlung für die meisten Nutzer (16 GB RAM)
ollama pull gemma3:4b

# Für Rechner mit wenig RAM (8 GB)
ollama pull llama3.2:3b

# Für GPU-Nutzer mit 8+ GB VRAM
ollama pull mistral:7b
```

!!! tip "Modell testen"
    Prüfe, ob Ollama funktioniert:
    ```bash
    ollama run gemma3:4b "Welche Temperatur benötigt Basilikum in der Keimungsphase?"
    ```

### Am Knowledge-Service konfigurieren

Setze folgende Umgebungsvariablen des Knowledge-Service (z.B. in den Helm-Values oder der `.env`-Datei) und starte den Dienst neu:

```bash
LLM_PROVIDER=ollama
LLM_API_URL=http://ollama:11434   # oder die IP/den Service-Namen des Ollama-Hosts
LLM_MODEL=gemma3:4b
```

!!! warning "Ollama auf einem anderen Host"
    Wenn Ollama auf einem anderen Rechner läuft (z.B. einem NAS), muss `LLM_API_URL` auf die IP-Adresse bzw. den DNS-Namen dieses Rechners zeigen. Port 11434 muss aus dem Netzwerk des Knowledge-Service erreichbar sein.

---

## llama.cpp HTTP Server

llama.cpp ist eine Alternative zu Ollama für fortgeschrittene Nutzer, die GGUF-Modelle direkt aus der Hugging-Face-Community oder eigenen Quellen nutzen möchten.

### Server starten

```bash
# llama.cpp HTTP Server (nach Kompilierung)
./llama-server \
  --model /pfad/zum/modell.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 4096
```

### Am Knowledge-Service konfigurieren

llama.cpp bietet eine OpenAI-kompatible API, daher wird der Provider `openai_compatible` verwendet:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_URL=http://localhost:8080   # Basis-URL OHNE /v1 — der Adapter hängt /v1/chat/completions selbst an
LLM_API_KEY=                        # leer lassen
LLM_MODEL=local                     # oder der Name des geladenen GGUF-Modells
```

---

## OpenAI API

OpenAI bietet hochwertige Cloud-Modelle. Pflanzdaten werden für jede Anfrage an OpenAI-Server in den USA übertragen.

!!! warning "Datenschutzhinweis"
    Bei Nutzung der OpenAI API werden Pflanzdaten (Phase, Messwerte, Sortenname, Düngehistorie) an OpenAI in den USA übertragen. Der Betreiber ist dafür verantwortlich, Nutzer:innen darüber in der Datenschutzerklärung der Instanz zu informieren.

### API-Key erstellen

1. Öffne [platform.openai.com](https://platform.openai.com).
2. Melde dich an (oder registriere dich).
3. Navigiere zu **API keys**.
4. Klicke auf **Create new secret key**.
5. Kopiere den Key (er wird nur einmal angezeigt).

### Am Knowledge-Service konfigurieren

Es gibt keinen eigenen `openai`-Providerwert — OpenAI wird über `openai_compatible` mit der OpenAI-Basis-URL angesprochen:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_URL=https://api.openai.com   # Basis-URL OHNE /v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

### Empfohlene Modelle

| Modell | Stärken | Kosten (ca.) |
|--------|---------|-------------|
| `gpt-4o-mini` | Schnell, günstig, gut für einfache Diagnosen | ~$0,001 pro Anfrage |
| `gpt-4o` | Beste Qualität, komplexe Zusammenhänge | ~$0,01 pro Anfrage |

---

## Anthropic Claude API

Anthropic Claude ist eine Alternative zu OpenAI mit starken Analysefähigkeiten. Auch hier werden Daten an Server in den USA übertragen.

!!! warning "Datenschutzhinweis"
    Analog zur OpenAI API: Pflanzdaten werden bei jeder Anfrage an Anthropic-Server in den USA übertragen. Der Betreiber ist für die entsprechende Information in der Datenschutzerklärung verantwortlich.

### API-Key erstellen

1. Öffne [console.anthropic.com](https://console.anthropic.com).
2. Melde dich an (oder registriere dich).
3. Navigiere zu **API Keys**.
4. Klicke auf **Create Key**.
5. Kopiere den Key.

### Am Knowledge-Service konfigurieren

```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-20250514   # Standardwert im Adapter, falls LLM_MODEL nicht gesetzt wird
```

### Empfohlene Modelle

| Modell | Stärken | Kosten (ca.) |
|--------|---------|-------------|
| `claude-haiku-4-5` | Sehr schnell, günstig | ~$0,001 pro Anfrage |
| `claude-sonnet-4-6` | Präzise Diagnosen, nuancierte Antworten | ~$0,008 pro Anfrage |

---

## OpenAI-kompatible APIs

Viele lokale und Cloud-Dienste bieten eine OpenAI-kompatible API. Dazu gehören:

- **LM Studio** — GUI-Anwendung für lokale Modelle (Windows/macOS/Linux)
- **vLLM** — Hochperformante Inference für Server
- **Together AI** — Cloud-Dienst mit Open-Source-Modellen
- **Mistral AI** — Cloud-Dienst mit Mistral-Modellen
- **Groq** — Sehr schnelle Cloud-Inference

### Am Knowledge-Service konfigurieren

```bash
LLM_PROVIDER=openai_compatible
LLM_API_URL=<Basis-URL des Dienstes ohne /v1>   # z.B. http://localhost:1234 für LM Studio
LLM_API_KEY=<falls erforderlich, sonst leer>
LLM_MODEL=<Modellname>
```

!!! example "LM Studio Beispiel"
    LM Studio startet einen lokalen Server unter `http://localhost:1234`.
    `LLM_API_URL=http://localhost:1234`, `LLM_MODEL=lmstudio-community/gemma-3-4b-it-GGUF`.

---

## Provider-Priorität und Fallback

Der Knowledge-Service verwendet zum jetzigen Zeitpunkt **genau einen** konfigurierten Provider (`LLM_PROVIDER`) — es gibt keine Mehrfach-Konfiguration mit automatischem Failover zwischen mehreren Cloud-/Lokal-Providern.

Falls kein Provider erreichbar ist oder `POST /api/v1/knowledge/ask` fehlschlägt, greift der **regelbasierte Fallback** für Tipp-Karten (sobald diese Funktion verfügbar ist): Das System generiert Tipp-Karten auf Basis der Stammdaten und der aktuellen Phase — ohne Sprachmodell.

---

## Häufige Fragen

??? question "Kann ich verschiedene Provider für verschiedene Funktionen verwenden?"
    Nein, derzeit verwendet der Knowledge-Service immer den einen konfigurierten Provider (`LLM_PROVIDER`) für alle KI-Funktionen. Unterschiedliche Provider pro Funktion sind nicht vorgesehen.

??? question "Wie kann ich den Verbrauch bei Cloud-Providern kontrollieren?"
    OpenAI und Anthropic bieten in ihren Dashboards Verbrauchsübersichten und Budget-Limits.

??? question "Ollama startet nicht oder ist nicht erreichbar — was tun?"
    Prüfe: (1) Ist der Ollama-Dienst gestartet? (`systemctl status ollama` auf Linux). (2) Läuft Ollama auf Port 11434? (`curl http://localhost:11434`). (3) Ist das Modell heruntergeladen? (`ollama list`). (4) Zeigt `LLM_API_URL` auf den korrekten Host?

??? question "Das Modell antwortet auf Englisch statt Deutsch — was tun?"
    Der Knowledge-Service sendet standardmäßig alle Anfragen auf Deutsch (`RAG_PROMPT_LANGUAGE=de`). Das Modellverhalten hängt zusätzlich vom Modell selbst ab. Falls ein Modell trotzdem konsequent auf Englisch antwortet, hilft ein größeres Modell (`gemma3:4b` statt `llama3.2:3b`).

---

## Siehe auch

- [KI-Assistent](ai-assistant.md)
- [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md)
- [Umgebungsvariablen](../reference/environment-variables.md)
