# KI-Provider einrichten

Kamerplanter unterstützt mehrere KI-Provider, die du je nach Hardware, Datenschutzanforderungen und Budget wählen kannst. Diese Seite erklärt, wie du jeden Provider einrichtest und in Kamerplanter konfigurierst.

---

## Voraussetzungen

- Kamerplanter ist installiert und läuft
- Du hast Zugriff auf **Einstellungen > KI-Provider** (Tenant-Admin oder eigene Einstellungen)

---

## Übersicht der Provider

| Provider | Typ | Datenschutz | Kosten | Empfehlung |
|----------|-----|-------------|--------|------------|
| [Ollama](#ollama-lokal-empfohlen) | Lokal | Keine Datenweitergabe | Kostenlos | Self-Hosted |
| [llama.cpp HTTP Server](#llamacpp-http-server) | Lokal | Keine Datenweitergabe | Kostenlos | Fortgeschrittene |
| [OpenAI API](#openai-api) | Cloud | Übertragung an OpenAI (USA) | Pay-per-Token | Beste Qualität |
| [Anthropic Claude API](#anthropic-claude-api) | Cloud | Übertragung an Anthropic (USA) | Pay-per-Token | Beste Qualität |
| [OpenAI-kompatible APIs](#openai-kompatible-apis) | Lokal oder Cloud | Abhängig | Variabel | Fortgeschrittene |

!!! tip "Empfehlung für den Einstieg"
    Wenn du Kamerplanter selbst hostest: Starte mit **Ollama + gemma3:4b**. Das Modell läuft auf den meisten Desktop-Rechnern ab 2020 ohne GPU und gibt keine Daten weiter.

---

## Ollama (lokal, empfohlen)

Ollama ist ein Programm, das Sprachmodelle lokal auf deinem Rechner oder Server ausführt. Keine Daten verlassen dein Netzwerk.

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

### In Kamerplanter konfigurieren

1. Öffne **Einstellungen > KI-Provider**.
2. Klicke auf **Provider hinzufügen**.
3. Wähle **Ollama**.
4. Trage die URL ein: `http://localhost:11434` (oder die IP deines Servers).
5. Wähle das Modell aus der Dropdown-Liste (oder tippe `gemma3:4b` ein).
6. Klicke auf **Speichern** und anschließend auf **Verbindung testen**.

!!! warning "Ollama auf einem anderen Rechner"
    Wenn Ollama auf einem anderen Rechner läuft (z.B. einem NAS), ersetze `localhost` durch die IP-Adresse dieses Rechners. Stelle sicher, dass Port 11434 im Netzwerk erreichbar ist.

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

### In Kamerplanter konfigurieren

1. Öffne **Einstellungen > KI-Provider**.
2. Klicke auf **Provider hinzufügen**.
3. Wähle **OpenAI-kompatibel** (llama.cpp bietet eine OpenAI-kompatible API).
4. Trage die URL ein: `http://localhost:8080`.
5. Lasse das API-Key-Feld leer.
6. Trage als Modellname `local` oder den Namen deines GGUF-Modells ein.
7. Klicke auf **Verbindung testen**.

---

## OpenAI API

OpenAI bietet hochwertige Cloud-Modelle. Deine Pflanzdaten werden für jede Anfrage an OpenAI-Server in den USA übertragen.

!!! warning "Datenschutzhinweis"
    Bei Nutzung der OpenAI API werden deine Pflanzdaten (Phase, Messwerte, Sortenname, Düngehistorie) an OpenAI in den USA übertragen. Beim ersten Chat mit einem Cloud-Provider fragt Kamerplanter nach deiner DSGVO-Einwilligung. Du kannst diese jederzeit unter **Einstellungen > Datenschutz** widerrufen.

### API-Key erstellen

1. Öffne [platform.openai.com](https://platform.openai.com).
2. Melde dich an (oder registriere dich).
3. Navigiere zu **API keys**.
4. Klicke auf **Create new secret key**.
5. Kopiere den Key (er wird nur einmal angezeigt).

### In Kamerplanter konfigurieren

1. Öffne **Einstellungen > KI-Provider**.
2. Klicke auf **Provider hinzufügen**.
3. Wähle **OpenAI**.
4. Füge deinen API-Key ein.
5. Wähle das Modell:
   - **gpt-4o-mini** — günstig, schnell, gut für Tipp-Karten
   - **gpt-4o** — beste Qualität, höhere Kosten
6. Klicke auf **Speichern**.

### Empfohlene Modelle

| Modell | Stärken | Kosten (ca.) |
|--------|---------|-------------|
| `gpt-4o-mini` | Schnell, günstig, gut für einfache Diagnosen | ~$0,001 pro Anfrage |
| `gpt-4o` | Beste Qualität, komplexe Zusammenhänge | ~$0,01 pro Anfrage |

---

## Anthropic Claude API

Anthropic Claude ist eine Alternative zu OpenAI mit starken Analysefähigkeiten. Auch hier werden Daten an Server in den USA übertragen.

!!! warning "Datenschutzhinweis"
    Analog zur OpenAI API: Deine Pflanzdaten werden bei jeder Anfrage an Anthropic-Server in den USA übertragen. DSGVO-Einwilligung erforderlich.

### API-Key erstellen

1. Öffne [console.anthropic.com](https://console.anthropic.com).
2. Melde dich an (oder registriere dich).
3. Navigiere zu **API Keys**.
4. Klicke auf **Create Key**.
5. Kopiere den Key.

### In Kamerplanter konfigurieren

1. Öffne **Einstellungen > KI-Provider**.
2. Klicke auf **Provider hinzufügen**.
3. Wähle **Anthropic**.
4. Füge deinen API-Key ein.
5. Wähle das Modell:
   - **claude-haiku-4-5** — schnell, günstig, gut für Tipp-Karten
   - **claude-sonnet-4-6** — sehr gute Analysequalität
6. Klicke auf **Speichern**.

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

### In Kamerplanter konfigurieren

1. Öffne **Einstellungen > KI-Provider**.
2. Klicke auf **Provider hinzufügen**.
3. Wähle **OpenAI-kompatibel**.
4. Trage die **Base-URL** des Dienstes ein (z.B. `http://localhost:1234/v1` für LM Studio).
5. Trage einen **API-Key** ein, falls der Dienst einen erfordert (bei lokalen Diensten oft leer lassen).
6. Trage den **Modellnamen** ein.
7. Klicke auf **Verbindung testen**.

!!! example "LM Studio Beispiel"
    LM Studio startet einen lokalen Server unter `http://localhost:1234/v1`.
    Modellname: Der Name des geladenen Modells, z.B. `lmstudio-community/gemma-3-4b-it-GGUF`.

---

## Provider-Priorität und Fallback

Wenn du mehrere Provider konfiguriert hast, kannst du einen als **Standard** festlegen. Bei nicht erreichbarem Standard-Provider wechselt das System auf den nächsten aktiven Provider.

Falls kein Provider verfügbar ist, greift der **regelbasierte Fallback**: Das System generiert Tipp-Karten auf Basis der Stammdaten und der aktuellen Phase — ohne Sprachmodell.

---

## Häufige Fragen

??? question "Kann ich verschiedene Provider für verschiedene Funktionen verwenden?"
    Derzeit verwendet Kamerplanter immer den konfigurierten Standard-Provider für alle KI-Funktionen. Unterschiedliche Provider pro Funktion (z.B. lokal für Chat, Cloud für Diagnose) sind für eine zukünftige Version geplant.

??? question "Wie kann ich den Verbrauch bei Cloud-Providern kontrollieren?"
    OpenAI und Anthropic bieten in ihren Dashboards Verbrauchsübersichten und Budget-Limits. Tipp-Karten werden täglich im Hintergrund generiert und gecacht (4 Stunden), was den Verbrauch stark reduziert.

??? question "Ollama startet nicht oder ist nicht erreichbar — was tun?"
    Prüfe: (1) Ist der Ollama-Dienst gestartet? (`systemctl status ollama` auf Linux). (2) Läuft Ollama auf Port 11434? (`curl http://localhost:11434`). (3) Ist das Modell heruntergeladen? (`ollama list`).

??? question "Das Modell antwortet auf Englisch statt Deutsch — was tun?"
    Das Systemverhalten hängt vom Modell ab. Kamerplanter sendet alle Anfragen auf Deutsch und weist das Modell an, auf Deutsch zu antworten. Falls das Modell trotzdem auf Englisch antwortet, versuche ein größeres Modell (`gemma3:4b` statt `llama3.2:3b`).

---

## Siehe auch

- [KI-Assistent verwenden](ai-assistant.md)
- [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md)
- [Umgebungsvariablen](../reference/environment-variables.md)
