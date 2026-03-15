# Willkommen bei Kamerplanter

Kamerplanter ist ein Pflanzenpflege-Management-System für den gesamten Lebenszyklus — von der Aussaat bis zur Ernte. Es unterstützt Gemüse, Kräuter, Zimmerpflanzen und Zierpflanzen mit Funktionen wie Nährstoffplanung, Phasenverfolgung, Sensorintegration und Pflegeerinnerungen.

---

## Was kann Kamerplanter?

<div class="grid cards" markdown>

-   **Stammdaten & Phasen**

    ---

    Verwalte Pflanzenarten, Sorten und botanische Familien. Verfolge jede Pflanze durch ihre Wachstumsphasen — von der Keimung bis zur Ernte.

    [:octicons-arrow-right-24: Benutzerhandbuch](user-guide/index.md)

-   **Nährstoffplanung**

    ---

    Plane Düngegaben mit EC-Budget-Kalkulation, Mischfolge-Validierung und Spülprotokollen. Unterstützt Leitungswasser, Umkehrosmose und gemischte Quellen.

    [:octicons-arrow-right-24: Dünge-Logik](user-guide/fertilization.md)

-   **Tankmanagement**

    ---

    Verwalte Wassertanks mit Füllstandsverfolgung, Wasserquellenprofile (Leitungswasser/RO) und automatischer Dosierungsberechnung.

    [:octicons-arrow-right-24: Tankmanagement](user-guide/tanks.md)

-   **Pflegeerinnerungen**

    ---

    Adaptive Bewässerungs- und Düngepläne mit 9 Pflegeprofil-Presets, saisonalem Bewusstsein und Lernfunktion aus Bestätigungen.

    [:octicons-arrow-right-24: Aufgaben & Erinnerungen](user-guide/tasks.md)

-   **Integrierter Pflanzenschutz (IPM)**

    ---

    Dreistufiges System (Prävention, Monitoring, Intervention) mit Karenzzeit-Überwachung, die Ernten bei aktiven Behandlungen blockiert.

    [:octicons-arrow-right-24: Pflanzenschutz](user-guide/pest-management.md)

-   **Kalender & Saisonüberblick**

    ---

    Aggregierte Ansicht aller Aufgaben, Phasen und Ereignisse mit iCal-Export. Aussaatkalender für Freilandanbau.

    [:octicons-arrow-right-24: Kalender](user-guide/calendar.md)

</div>

---

## Schneller Einstieg

=== "Docker Compose (einfach)"

    ```bash
    docker compose up --build
    ```

    Dies startet Backend, Frontend, ArangoDB und Redis.

    **Demo-Login:** `demo@kamerplanter.local` / `demo-passwort-2024`

=== "Skaffold (Entwicklung)"

    ```bash
    skaffold dev --trigger=manual --port-forward
    ```

    Skaffold ist das primäre Werkzeug für die lokale Entwicklung.

    [:octicons-arrow-right-24: Lokales Setup](development/local-setup.md)

---

## Projektgeschichte

!!! note "Entstehungsgeschichte"
    Dieses Projekt begann als **Vibe Coding Experiment** — entwickelt fast ausschließlich durch konversationelles KI-Prompting mit Claude Code. Spezifikationen, Architektur, Domain-Modelle, Backend, Frontend, Helm-Charts und Tests entstanden in diesem Stil. Was als Erkundung KI-assistierter Entwicklung begann, wuchs zu einer vollständigen landwirtschaftlichen Management-Plattform.

---

## Dokumentation navigieren

| Abschnitt | Beschreibung |
|-----------|-------------|
| [Erste Schritte](getting-started/index.md) | Installation, Schnellstart, erstes Deployment |
| [Benutzerhandbuch](user-guide/index.md) | Alle Funktionen für Endnutzer erklärt |
| [Architektur](architecture/index.md) | Systemdesign, Schichten, Datenmodelle |
| [Entwicklung](development/index.md) | Lokales Setup, Code-Standards, Tests |
| [API](api/index.md) | REST-API-Referenz, Authentifizierung |
| [Deployment](deployment/index.md) | Kubernetes, Helm, CI/CD |
| [Guides](guides/index.md) | Tiefgehende Anleitungen zu GDD, VPD, Nährstoffen |
| [ADR](adr/index.md) | Architecture Decision Records |
