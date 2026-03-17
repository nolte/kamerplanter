# Installation

Bevor du Kamerplanter starten kannst, brauchst du Docker auf deinem Rechner. Diese Seite erklärt dir, was Docker ist, wie du es installierst und wie du prüfst, ob alles bereit ist.

---

## Was ist Docker?

Docker ist ein Werkzeug, das Anwendungen in sogenannten **Containern** ausführt. Ein Container enthält alles, was eine Anwendung braucht — du musst keine Programmiersprachen, Datenbanken oder andere Software selbst installieren. Docker erledigt das für dich.

Kamerplanter nutzt Docker, um fünf Dienste (Benutzeroberfläche, Backend, Datenbank, Cache und Hintergrundaufgaben) zusammen zu starten. Du brauchst dafür nur einen einzigen Befehl.

---

## Voraussetzungen

| Was | Minimum | Empfohlen |
|-----|---------|-----------|
| Betriebssystem | Windows 10/11, macOS 12+, Linux (Ubuntu 22.04+, Debian 12+) | Linux |
| Arbeitsspeicher (RAM) | 2 GB frei | 4 GB frei |
| Festplatte | 3 GB frei | 5 GB frei |
| Internetverbindung | Zum erstmaligen Herunterladen der Container-Images | — |

---

## Docker installieren

=== "Windows"

    1. Lade **Docker Desktop** herunter: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
    2. Starte die heruntergeladene Datei und folge dem Installationsassistenten
    3. Nach der Installation startet Docker Desktop automatisch — du erkennst es am Wal-Symbol in der Taskleiste
    4. Öffne ein **Terminal** (PowerShell oder Eingabeaufforderung) und prüfe die Installation:

    ```powershell
    docker --version
    docker compose version
    ```

    !!! tip "WSL 2 erforderlich"
        Docker Desktop unter Windows benötigt WSL 2 (Windows Subsystem for Linux). Der Installationsassistent richtet WSL 2 automatisch ein, falls es noch nicht vorhanden ist. Möglicherweise ist ein Neustart erforderlich.

=== "macOS"

    1. Lade **Docker Desktop** herunter: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
    2. Öffne die `.dmg`-Datei und ziehe Docker in den Programme-Ordner
    3. Starte Docker aus dem Programme-Ordner — beim ersten Start fragt macOS nach Berechtigungen
    4. Öffne ein **Terminal** und prüfe die Installation:

    ```bash
    docker --version
    docker compose version
    ```

=== "Linux (Ubuntu/Debian)"

    Installiere Docker Engine über das offizielle Repository:

    ```bash
    # Paketliste aktualisieren
    sudo apt-get update

    # Abhängigkeiten installieren
    sudo apt-get install -y ca-certificates curl

    # Dockers GPG-Schlüssel hinzufügen
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Docker-Repository hinzufügen
    echo "deb [arch=$(dpkg --print-architecture) \
      signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Docker installieren
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli \
      containerd.io docker-compose-plugin

    # Deinen Benutzer zur docker-Gruppe hinzufügen (damit du kein sudo brauchst)
    sudo usermod -aG docker $USER
    ```

    !!! warning "Neu anmelden"
        Nach dem Hinzufügen zur `docker`-Gruppe musst du dich **ab- und wieder anmelden** (oder den Rechner neu starten), damit die Änderung wirksam wird.

    Prüfe die Installation:

    ```bash
    docker --version
    docker compose version
    ```

=== "Raspberry Pi"

    Der Raspberry Pi 4 (oder neuer) mit mindestens 4 GB RAM eignet sich gut für Kamerplanter. Verwende **Raspberry Pi OS (64-Bit)**.

    ```bash
    # Docker über das offizielle Installationsskript installieren
    curl -fsSL https://get.docker.com | sudo sh

    # Deinen Benutzer zur docker-Gruppe hinzufügen
    sudo usermod -aG docker $USER
    ```

    Nach Ab- und Wiederanmeldung:

    ```bash
    docker --version
    docker compose version
    ```

---

## Installation prüfen

Wenn Docker korrekt installiert ist, solltest du ungefähr folgende Ausgaben sehen:

```
$ docker --version
Docker version 27.x.x, build xxxxxxx

$ docker compose version
Docker Compose version v2.x.x
```

Die genauen Versionsnummern können abweichen — wichtig ist, dass beide Befehle ohne Fehlermeldung funktionieren.

!!! success "Bereit!"
    Docker ist installiert? Dann geht es weiter mit dem [Schnellstart](quickstart.md).

---

## Fehlerbehebung

??? question "docker: command not found"
    Docker ist nicht installiert oder nicht im Systempfad. Unter Windows/macOS: Stelle sicher, dass Docker Desktop gestartet ist (Wal-Symbol in der Taskleiste). Unter Linux: Führe die Installation erneut aus.

??? question "permission denied while trying to connect to the Docker daemon socket"
    Unter Linux: Dein Benutzer ist nicht in der `docker`-Gruppe. Führe `sudo usermod -aG docker $USER` aus und melde dich neu an.

??? question "Docker Desktop startet nicht unter Windows"
    Prüfe, ob WSL 2 installiert ist: Öffne PowerShell als Administrator und führe `wsl --install` aus. Nach einem Neustart sollte Docker Desktop starten.

---

## Siehe auch

- [Schnellstart](quickstart.md) — Kamerplanter in 5 Minuten starten
- [Erstes Deployment](first-deployment.md) — Dauerhaft auf eigenem Server betreiben
