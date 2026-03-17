# Schnellstart

In 5 Minuten von Null zur laufenden Kamerplanter-Instanz mit deinen ersten Pflanzen.

!!! info "Voraussetzung"
    Docker und Docker Compose müssen installiert sein. Falls nicht, folge zuerst der [Installationsanleitung](installation.md).

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

Da Kamerplanter standardmäßig im **Light-Modus** startet, gibt es keinen Login-Bildschirm. Du landest direkt im Onboarding-Wizard.

---

## 5. Onboarding-Wizard durchlaufen

Der Wizard führt dich in fünf Schritten durch die Ersteinrichtung:

### Schritt 1: Erfahrungsstufe

Wähle, wie viel Erfahrung du mit Pflanzenpflege hast:

- **Einsteiger** — Zeigt dir nur die wichtigsten Funktionen. Gut zum Kennenlernen.
- **Mittelstufe** — Zusätzlich Düngung, Tanks und Sensorik.
- **Experte** — Alle Funktionen sichtbar.

Du kannst die Stufe jederzeit später ändern.

### Schritt 2: Umgebung & Standort

Beschreibe, wo deine Pflanzen stehen — z.B. "Küchenfenster" oder "Südbalkon". Kamerplanter nutzt diese Information, um passende Starter-Kits vorzuschlagen.

### Schritt 3: Starter-Kit wählen

Wähle ein vorkonfiguriertes Szenario. Das Starter-Kit legt automatisch passende Pflanzenarten, Wachstumsphasen und Düngepläne an.

| Starter-Kit | Für wen? |
|-------------|----------|
| Fensterbrett-Kräuter | Basilikum, Petersilie & Co. auf der Fensterbank |
| Zimmerpflanzen-Starter | Die beliebtesten Zimmerpflanzen |
| Haustierfreundliche Zimmerpflanzen | Ungiftige Pflanzen für Haushalte mit Tieren |
| Balkon-Tomaten | Tomaten auf dem Balkon ziehen |
| Sukkulenten & Kakteen | Pflegeleichte Sukkulenten |
| Mediterrane Kräuter | Rosmarin, Thymian, Oregano |
| Balkon-Chillis | Chili-Anbau auf dem Balkon |
| Gemüsebeet | Gemüse im Außenbeet |
| Indoor Growzelt | Kontrollierter Indoor-Anbau |

### Schritt 4: Pflanzen & Favoriten

Lege fest, wie viele Pflanzen du von jeder Art anlegen möchtest, und markiere deine Lieblingspflanzen als Favoriten.

### Schritt 5: Zusammenfassung

Prüfe die Zusammenfassung und klicke auf **Abschließen**. Kamerplanter erstellt alles automatisch und leitet dich zum Dashboard weiter.

---

## Geschafft!

Dein Kamerplanter läuft. Von hier aus kannst du:

- **Pflanzen ansehen** und den Wachstumsstatus verfolgen
- **Aufgaben prüfen**, die das Starter-Kit angelegt hat
- **Standorte anpassen** — Räume umbenennen, weitere hinzufügen
- **Weitere Pflanzen anlegen** — über das Menü "Stammdaten"

---

## Nützliche Befehle

| Befehl | Was er tut |
|--------|-----------|
| `docker compose up -d` | Alle Dienste starten |
| `docker compose stop` | Alle Dienste anhalten (Daten bleiben erhalten) |
| `docker compose down` | Alle Dienste stoppen und Container entfernen (Daten bleiben erhalten) |
| `docker compose down -v` | Alles stoppen **und Daten löschen** (Neuanfang) |
| `docker compose logs -f backend` | Backend-Logs live verfolgen |
| `docker compose ps` | Status aller Dienste anzeigen |

!!! warning "Daten löschen"
    Der Befehl `docker compose down -v` löscht alle gespeicherten Daten unwiderruflich. Verwende ihn nur, wenn du einen kompletten Neuanfang möchtest.

---

## Zugangspunkte

| Dienst | URL | Beschreibung |
|--------|-----|-------------|
| Benutzeroberfläche | [http://localhost:8080](http://localhost:8080) | Die Kamerplanter-App |
| API-Dokumentation | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interaktive API-Referenz (Swagger UI) |
| Datenbank-UI | [http://localhost:8529](http://localhost:8529) | ArangoDB Web-Interface (für Fortgeschrittene) |

---

## Siehe auch

- [Onboarding-Wizard](../user-guide/onboarding.md) — Ausführliche Beschreibung aller Wizard-Schritte
- [Light-Modus](../user-guide/light-mode.md) — Was der Light-Modus genau bedeutet
- [Erstes Deployment](first-deployment.md) — Kamerplanter dauerhaft auf eigenem Server betreiben
