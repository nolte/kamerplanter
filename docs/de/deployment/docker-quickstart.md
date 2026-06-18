# Docker Compose Schnellstart

In 5 Minuten von Null zur laufenden Kamerplanter-Instanz mit deinen ersten Pflanzen.

!!! info "Voraussetzung"
    Docker und Docker Compose müssen installiert sein. Falls nicht, folge zuerst der [Installationsanleitung](docker-installation.md).

---

## 1. Repository herunterladen

Lade den Quellcode herunter und wechsle in das Verzeichnis:

```bash
git clone https://github.com/nolte/kamerplanter.git
cd kamerplanter
```

??? note "Kein Git installiert?"
    Du kannst das Repository auch als ZIP-Datei herunterladen: Gehe auf die [GitHub-Seite](https://github.com/nolte/kamerplanter), klicke auf den grünen **Code**-Button und wähle **Download ZIP**. Entpacke die Datei und öffne ein Terminal im entpackten Ordner.

---

## 2. Konfiguration erstellen

Kopiere die Beispiel-Konfiguration und passe die Passwörter an:

```bash
cp .env.example .env
```

Öffne die Datei `.env` in einem Texteditor und ändere mindestens die Passwörter:

```ini title=".env"
# Sichere Passwörter setzen (mindestens 12 Zeichen empfohlen)
ARANGO_ROOT_PASSWORD=dein-sicheres-passwort    # (1)!
ARANGODB_PASSWORD=dein-sicheres-passwort        # (2)!
```

1. Das Passwort für die Datenbank. Wähle ein sicheres Passwort — es wird nicht im Browser angezeigt.
2. Muss identisch mit `ARANGO_ROOT_PASSWORD` sein.

!!! tip "Sicheres Passwort generieren"
    Unter Linux/macOS kannst du ein zufälliges Passwort erzeugen:

    ```bash
    openssl rand -base64 24
    ```

    Kopiere die Ausgabe und setze sie als Passwort in der `.env`-Datei ein.

Die übrigen Einstellungen kannst du zunächst auf den Standardwerten belassen.

---

## 3. Kamerplanter starten

Starte alle Dienste mit einem einzigen Befehl:

```bash
docker compose up -d
```

Docker lädt beim ersten Start die benötigten Images herunter. Das kann je nach Internetverbindung **2–5 Minuten** dauern. Bei weiteren Starts geht es deutlich schneller.

Prüfe, ob alle Dienste laufen:

```bash
docker compose ps
```

Du solltest fünf Dienste sehen, alle mit dem Status **running** oder **healthy**:

```
NAME                  STATUS
kamerplanter-arangodb-1        running (healthy)
kamerplanter-valkey-1          running (healthy)
kamerplanter-backend-1         running (healthy)
kamerplanter-celery-worker-1   running
kamerplanter-celery-beat-1     running
kamerplanter-frontend-1        running (healthy)
```

??? question "Ein Dienst zeigt 'unhealthy' oder 'restarting'?"
    Warte 30 Sekunden und führe `docker compose ps` erneut aus — manche Dienste brauchen etwas länger zum Starten. Falls das Problem bestehen bleibt, prüfe die Logs:

    ```bash
    docker compose logs backend
    ```

---

## 4. Kamerplanter im Browser öffnen

Öffne deinen Browser und gehe zu:

**:point_right: [http://localhost:8080](http://localhost:8080)**

Da Kamerplanter standardmäßig im **Light-Modus** startet, gibt es keinen Login-Bildschirm — du landest direkt im Onboarding-Wizard.

---

## 5. Erste Einrichtung

Beim ersten Öffnen startet Kamerplanter automatisch den Onboarding-Wizard. Er führt dich in wenigen Minuten durch Erfahrungsstufe, Standort und die Wahl eines Starter-Kits (z. B. "Fensterbrett-Kräuter" oder "Zimmerpflanzen-Starter"). Alles ist selbsterklärend und im Detail beschrieben auf der Seite [Onboarding-Wizard](../user-guide/onboarding.md).

---

## Geschafft!

Dein Kamerplanter läuft. Von hier aus kannst du:

- **Pflanzen ansehen** und den Wachstumsstatus verfolgen
- **Aufgaben prüfen**, die das Starter-Kit angelegt hat
- **Standorte anpassen** — Räume umbenennen, weitere hinzufügen
- **Weitere Pflanzen anlegen** — über das Menü "Stammdaten"

---

## Optionale Profile (KI, Sensordaten)

Der Basis-Start mit `docker compose up -d` reicht für den vollständigen Pflanzen-, Aufgaben- und Pflegebetrieb. Zusätzliche Funktionen — KI-Wissensassistent und Sensordaten-Historie — können über optionale **Docker Compose Profile** zugeschaltet werden.

!!! note "Profile sind additiv und kombinierbar"
    Jedes Profil erweitert die Basis um zusätzliche Dienste. Du kannst mehrere Profile gleichzeitig aktivieren.

### Übersicht der Profile

| Profil | Was es startet | Wofür | Nötiger `.env`-Schalter |
|--------|---------------|-------|------------------------|
| `vectordb` | PostgreSQL + pgvector (Port 5433) + Reranker-Service (Port 8081) | KI-/RAG-Wissensassistent — semantische Suche in der Wissensdatenbank | `VECTORDB_ENABLED=true` |
| `ollama` | Ollama LLM-Server (Port 11434) | Lokale LLM-Inferenz für den Wissensassistenten, als Alternative zu einer Cloud-API | `LLM_PROVIDER=ollama` und `LLM_API_URL=http://ollama:11434` |
| `timescaledb` | TimescaleDB (Port 5432) | Zeitreihen-Speicherung von Sensordaten (Messwert-Historie, automatisches Downsampling) | `TIMESCALEDB_ENABLED=true` |

### Beispiel-Befehle

**Nur Basis (Standard — kein Profil nötig):**

```bash
docker compose up -d
```

**KI-Wissensassistent mit lokalem LLM (Ollama):**

```bash
docker compose --profile vectordb --profile ollama up -d
```

Aktiviere anschließend die Dienste in der `.env`:

```ini title=".env"
VECTORDB_ENABLED=true
LLM_PROVIDER=ollama
LLM_API_URL=http://ollama:11434
LLM_MODEL=llama3.2          # Beliebiges auf Ollama verfügbares Modell
```

!!! tip "Modell beim ersten Start herunterladen"
    Ollama lädt das Modell beim ersten Aufruf herunter. Abhängig vom Modell sind das **4–15 GB** — plane entsprechend Disk-Speicher ein.

**KI-Wissensassistent mit Cloud-LLM (z. B. Anthropic):**

```bash
docker compose --profile vectordb up -d
```

```ini title=".env"
VECTORDB_ENABLED=true
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-20250514
```

**Sensordaten-Historie:**

```bash
docker compose --profile timescaledb up -d
```

```ini title=".env"
TIMESCALEDB_ENABLED=true
```

### Ressourcenbedarf der Profile

!!! warning "Ollama braucht deutlich mehr Ressourcen"
    LLM-Modelle sind groß. Rechne für ein kleineres Modell (z. B. `llama3.2`) mit mindestens **8 GB RAM** und **5 GB freiem Speicherplatz**. Größere Modelle benötigen entsprechend mehr. Ohne dedizierte GPU läuft die Inferenz auf der CPU — das ist langsamer, aber funktioniert.

| Profil | Zusätzlicher RAM (typisch) | Zusätzlicher Speicher |
|--------|--------------------------|----------------------|
| `vectordb` | ~512 MB | ~500 MB |
| `ollama` | 8–16 GB (je nach Modell) | 5–30 GB (je nach Modell) |
| `timescaledb` | ~256 MB | wächst mit Sensordaten |

---

## Nützliche Befehle

| Befehl | Was er tut |
|--------|-----------|
| `docker compose up -d` | Alle Basisdienste starten |
| `docker compose --profile vectordb --profile ollama up -d` | Basis + KI-Profile starten |
| `docker compose --profile timescaledb up -d` | Basis + Sensordaten-Profil starten |
| `docker compose stop` | Alle Dienste anhalten (Daten bleiben erhalten) |
| `docker compose down` | Alle Dienste stoppen und Container entfernen (Daten bleiben erhalten) |
| `docker compose down -v` | Alles stoppen **und Daten löschen** (Neuanfang) |
| `docker compose logs -f backend` | Backend-Logs live verfolgen |
| `docker compose ps` | Status aller Dienste anzeigen |

!!! warning "Daten löschen"
    Der Befehl `docker compose down -v` löscht alle gespeicherten Daten unwiderruflich. Verwende ihn nur, wenn du einen kompletten Neuanfang möchtest.

---

## Zugangspunkte

### Standard (immer verfügbar)

| Dienst | URL | Beschreibung |
|--------|-----|-------------|
| Benutzeroberfläche | [http://localhost:8080](http://localhost:8080) | Die Kamerplanter-App |
| API-Dokumentation | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interaktive API-Referenz (Swagger UI) |
| Datenbank-UI | [http://localhost:8529](http://localhost:8529) | ArangoDB Web-Interface (für Fortgeschrittene) |

### Optional (nur mit aktiviertem Profil)

| Dienst | URL | Profil | Beschreibung |
|--------|-----|--------|-------------|
| Reranker-Service | [http://localhost:8081](http://localhost:8081) | `vectordb` | Cross-Encoder für RAG-Qualität |
| Ollama | [http://localhost:11434](http://localhost:11434) | `ollama` | Lokaler LLM-Server (API) |

---

## Siehe auch

- [Onboarding-Wizard](../user-guide/onboarding.md) — Ausführliche Beschreibung aller Wizard-Schritte
- [Light-Modus](../user-guide/light-mode.md) — Was der Light-Modus genau bedeutet
- [Erstes Deployment](docker-dauerbetrieb.md) — Kamerplanter dauerhaft auf eigenem Server betreiben
