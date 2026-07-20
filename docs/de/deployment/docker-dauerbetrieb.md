# Docker Compose Dauerbetrieb

Du hast Kamerplanter im [Schnellstart](docker-quickstart.md) ausprobiert und möchtest es jetzt dauerhaft betreiben? Diese Anleitung zeigt dir, wie du Kamerplanter auf einem eigenen Server einrichtest — zum Beispiel auf einem Raspberry Pi, einem NAS oder einem Heimserver.

---

## Unterschied zum Schnellstart

Im Schnellstart hast du Kamerplanter aus dem Quellcode gebaut (`docker compose up`). Für den Dauerbetrieb nutzt du stattdessen **fertig gebaute Images** — das ist schneller, braucht weniger Speicher und du musst den Quellcode nicht auf dem Server haben.

| | Schnellstart | Dauerbetrieb |
|---|---|---|
| Docker Compose Datei | `docker-compose.yml` | `docker-compose.release.yml` |
| Images | Werden lokal gebaut | Fertig aus der Registry |
| Quellcode nötig? | Ja | Nein |
| Neustart bei Absturz | Manuell | Automatisch |
| Geeignet für | Ausprobieren, Entwicklung | Dauerbetrieb |

---

## Voraussetzungen

- Ein Server mit Docker und Docker Compose (siehe [Installation](docker-installation.md))
- Mindestens 2 GB RAM (4 GB empfohlen)
- Stabile Netzwerkverbindung für den Download der Images

---

## 1. Projektdateien herunterladen

Du brauchst nur zwei Dateien vom Repository — nicht den gesamten Quellcode:

```bash
# Verzeichnis erstellen
mkdir -p ~/kamerplanter && cd ~/kamerplanter

# Die beiden benötigten Dateien herunterladen
curl -O https://raw.githubusercontent.com/nolte/kamerplanter/main/docker-compose.release.yml
curl -O https://raw.githubusercontent.com/nolte/kamerplanter/main/.env.example
```

---

## 2. Konfiguration erstellen

```bash
cp .env.example .env
```

Öffne die `.env`-Datei und setze **sichere Passwörter**:

```ini title=".env"
# Sichere Passwörter generieren: openssl rand -base64 24
ARANGO_ROOT_PASSWORD=hier-sicheres-passwort-einsetzen
ARANGODB_PASSWORD=hier-sicheres-passwort-einsetzen

# Standardwerte — nur bei Bedarf ändern
ARANGODB_DATABASE=kamerplanter
ARANGODB_USERNAME=root
REDIS_URL=redis://valkey:6379/0
DEBUG=false
REQUIRE_EMAIL_VERIFICATION=false
CORS_ORIGINS=["http://localhost:8080"]
```

!!! warning "Passwörter"
    Verwende **nicht** die Beispielpasswörter aus `.env.example`. Generiere sichere Passwörter, z.B. mit `openssl rand -base64 24`. Beide Passwort-Felder (`ARANGO_ROOT_PASSWORD` und `ARANGODB_PASSWORD`) müssen identisch sein.

### Drei zusätzliche Pflicht-Secrets (sonst startet das Backend nicht)

!!! danger "Ohne diese drei Werte bricht der Backend-Start ab"
    `.env.example` setzt `DEBUG=false` — der für einen Dauerbetrieb richtige Wert. Bei `DEBUG=false` prüft das Backend beim Start zusätzlich `JWT_SECRET_KEY`, `FERNET_KEY` und `ERASURE_TOMBSTONE_SALT` und bricht mit einer Fehlermeldung ab, wenn einer davon fehlt (Fail-Fast-Gate). `docker-compose.release.yml` reicht diese drei Variablen **nicht automatisch** an den Backend-Container durch — du musst sie selbst ergänzen.

Erzeuge die drei Werte und trage sie in deine `.env` ein:

```bash
# JWT_SECRET_KEY und ERASURE_TOMBSTONE_SALT (mind. 32 Zeichen)
openssl rand -hex 32

# FERNET_KEY (muss ein gültiger Fernet-Schlüssel sein)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```ini title=".env"
JWT_SECRET_KEY=<Ausgabe von openssl rand -hex 32>
FERNET_KEY=<Ausgabe des Fernet-Kommandos>
ERASURE_TOMBSTONE_SALT=<zweite Ausgabe von openssl rand -hex 32>
```

Lege zusätzlich eine `docker-compose.override.yml` neben `docker-compose.release.yml` an — Docker Compose lädt sie automatisch mit:

```yaml title="docker-compose.override.yml"
services:
  backend:
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      FERNET_KEY: ${FERNET_KEY}
      ERASURE_TOMBSTONE_SALT: ${ERASURE_TOMBSTONE_SALT}
  celery-worker:
    environment:
      FERNET_KEY: ${FERNET_KEY}
      ERASURE_TOMBSTONE_SALT: ${ERASURE_TOMBSTONE_SALT}
  celery-beat:
    environment:
      FERNET_KEY: ${FERNET_KEY}
      ERASURE_TOMBSTONE_SALT: ${ERASURE_TOMBSTONE_SALT}
```

Vollständige Übersicht aller Pflicht-Secrets je Funktion: [Konfigurationsmatrix — Pflicht-Secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

!!! warning "Ab jetzt beide Compose-Dateien angeben"
    Da du eine zusätzliche `docker-compose.override.yml` angelegt hast, muss ab hier jeder `docker compose`-Befehl **beide** Dateien referenzieren: `-f docker-compose.release.yml -f docker-compose.override.yml`. Alle folgenden Befehle auf dieser Seite gehen davon aus.

---

## 3. Version festlegen

In der Datei `docker-compose.release.yml` steht als Platzhalter `__VERSION__`. Ersetze ihn durch die gewünschte Version:

```bash
# Beispiel: Version 1.0.0 setzen
sed -i 's/__VERSION__/1.0.0/g' docker-compose.release.yml
```

??? note "Welche Version soll ich nehmen?"
    Verwende die neueste stabile Version. Die verfügbaren Versionen findest du auf der [Releases-Seite](https://github.com/nolte/kamerplanter/releases) des Projekts.

---

## 4. Starten

```bash
docker compose -f docker-compose.release.yml -f docker-compose.override.yml up -d
```

Prüfe den Status:

```bash
docker compose -f docker-compose.release.yml -f docker-compose.override.yml ps
```

Alle Dienste sollten nach 30–60 Sekunden als **running** oder **healthy** angezeigt werden.

---

## 5. Zugriff testen

Öffne im Browser:

- **Kamerplanter:** [http://dein-server:8080](http://localhost:8080)
- **API-Dokumentation:** [http://dein-server:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

Ersetze `dein-server` durch die IP-Adresse oder den Hostnamen deines Servers. Wenn du auf dem Server selbst arbeitest, funktioniert `localhost`.

---

## Automatischer Neustart

Die Release-Konfiguration enthält bereits `restart: unless-stopped` für alle Dienste. Das bedeutet:

- Nach einem Serverabsturz oder Neustart startet Docker die Dienste automatisch
- Dienste, die du bewusst mit `docker compose stop` anhältst, bleiben gestoppt

Damit Docker selbst nach einem Neustart automatisch startet:

```bash
sudo systemctl enable docker
```

---

## Updates durchführen

So aktualisierst du Kamerplanter auf eine neue Version:

```bash
cd ~/kamerplanter

# 1. Version in der Compose-Datei aktualisieren
sed -i 's/alte-version/neue-version/g' docker-compose.release.yml

# 2. Neue Images herunterladen und Dienste neu starten
docker compose -f docker-compose.release.yml -f docker-compose.override.yml pull
docker compose -f docker-compose.release.yml -f docker-compose.override.yml up -d

# 3. Alte, nicht mehr benötigte Images aufräumen (optional)
docker image prune -f
```

!!! tip "Daten bleiben erhalten"
    Deine Pflanzen, Standorte und alle anderen Daten werden in Docker Volumes gespeichert und überleben Updates problemlos.

---

## Datensicherung

Die Daten von Kamerplanter liegen in zwei Docker Volumes:

- `arangodb_data` — Alle Pflanzen, Standorte, Aufgaben und Konfigurationen
- `valkey_data` — Cache und Aufgaben-Warteschlange (nicht kritisch, wird automatisch neu aufgebaut)

### Sicherung erstellen

```bash
# ArangoDB-Daten sichern
docker compose -f docker-compose.release.yml -f docker-compose.override.yml exec arangodb \
  arangodump --server.password "$ARANGO_ROOT_PASSWORD" \
  --output-directory /tmp/backup --overwrite true

# Backup aus dem Container kopieren
docker compose -f docker-compose.release.yml -f docker-compose.override.yml cp \
  arangodb:/tmp/backup ./backup-$(date +%Y%m%d)
```

### Sicherung wiederherstellen

```bash
# Backup in den Container kopieren
docker compose -f docker-compose.release.yml -f docker-compose.override.yml cp \
  ./backup-20260317 arangodb:/tmp/backup

# Daten wiederherstellen
docker compose -f docker-compose.release.yml -f docker-compose.override.yml exec arangodb \
  arangorestore --server.password "$ARANGO_ROOT_PASSWORD" \
  --input-directory /tmp/backup --overwrite true
```

!!! tip "Regelmäßige Backups"
    Richte einen Cronjob ein, der die Sicherung automatisch durchführt — zum Beispiel täglich um 3:00 Uhr nachts. So verlierst du im schlimmsten Fall maximal einen Tag an Daten.

---

## Zugriff von anderen Geräten

Standardmäßig ist Kamerplanter nur über den Server selbst erreichbar. Um von Smartphone, Tablet oder anderen Rechnern im Heimnetz zuzugreifen:

1. Finde die IP-Adresse deines Servers:

    ```bash
    hostname -I
    ```

2. Öffne auf dem anderen Gerät den Browser und gehe zu `http://<IP-Adresse>:8080`

3. Passe die CORS-Einstellung in `.env` an, damit die API Anfragen von der neuen Adresse akzeptiert:

    ```ini title=".env"
    CORS_ORIGINS=["http://localhost:8080","http://192.168.1.100:8080"]
    ```

4. Starte die Dienste nach der Änderung neu:

    ```bash
    docker compose -f docker-compose.release.yml -f docker-compose.override.yml up -d
    ```

---

## Nächste Schritte

- [Onboarding-Wizard](../user-guide/onboarding.md) — Deine ersten Pflanzen einrichten
- [Benutzerhandbuch](../user-guide/index.md) — Alle Funktionen im Detail
- [Kubernetes-Deployment](../deployment/kubernetes.md) — Für professionelle Umgebungen mit Hochverfügbarkeit

---

## Fehlerbehebung

??? question "Die Seite lädt nicht (Verbindung abgelehnt)"
    Prüfe, ob alle Dienste laufen: `docker compose -f docker-compose.release.yml -f docker-compose.override.yml ps`. Falls der Frontend-Dienst nicht läuft, prüfe die Logs: `docker compose -f docker-compose.release.yml -f docker-compose.override.yml logs frontend`.

??? question "Backend meldet 'Connection refused' zur Datenbank"
    ArangoDB braucht beim ersten Start etwas länger. Warte 30 Sekunden und prüfe erneut. Falls der Fehler bleibt: Stimmen die Passwörter in `.env` überein? `ARANGO_ROOT_PASSWORD` und `ARANGODB_PASSWORD` müssen identisch sein.

??? question "Zugriff von anderem Gerät funktioniert nicht"
    Prüfe: (1) Sind beide Geräte im gleichen Netzwerk? (2) Stimmt die IP-Adresse? (3) Ist die CORS-Einstellung in `.env` angepasst? (4) Blockiert eine Firewall Port 8080?

??? question "Wie viel Speicherplatz braucht Kamerplanter langfristig?"
    Die Docker-Images belegen ca. 2 GB. Die Datenbank wächst je nach Nutzung — für einen typischen Heimanwender mit bis zu 100 Pflanzen bleiben die Daten unter 100 MB. Sensorik-Daten können bei aktivierter Aufzeichnung schneller wachsen.
