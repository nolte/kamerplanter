# KI-Assistent

!!! warning "Noch nicht implementiert"
    Die auf dieser Seite beschriebene KI-Assistent-**Oberfläche** (Chat-Panel, Tipp-Karten, Diagnose-Modus) ist geplant und noch nicht verfügbar; im Frontend ist sie noch nicht umgesetzt. Die Seite `KIAssistentPage` existiert bislang nur als Platzhalter ("Diese Funktion ist noch in Vorbereitung") und ist noch nicht in der Navigation verlinkt. Diese Dokumentation beschreibt das **geplante Verhalten** im Futur. Schon heute nutzbar ist die zugrunde liegende Wissensbasis direkt über die API — siehe nächster Abschnitt. <!-- REQ-031 -->

Der KI-Assistent wird kontextabhängige Pflegehinweise geben, bei der Diagnose von Problemen unterstützen und Fragen zu deinen Pflanzen beantworten — direkt auf Basis deiner eigenen Daten.

---

### Für technische Nutzer: KI-Antworten über die API

Dieser Abschnitt richtet sich an technische Nutzer und Self-Hoster. Auch ohne fertige Oberfläche steht die Wissensbasis bereits über zwei API-Endpunkte zur Verfügung:

| Endpunkt | Zweck |
|----------|-------|
| `GET /api/v1/knowledge/search` | Semantische Suche in der Wissensbasis (Pflanzenwissen, Guides) |
| `POST /api/v1/knowledge/ask` | Frage stellen — das System generiert eine Antwort aus der Wissensbasis, sofern ein KI-Provider konfiguriert ist |

!!! info "Nur über API / Betreiber-Konfiguration"
    Es gibt keine Chat-Oberfläche. Beide Endpunkte sind über die interaktive API-Dokumentation (`/docs`) direkt testbar; eine angemeldete Sitzung ist erforderlich. Details siehe [API-Referenz](../api/overview.md). Der Betreiber muss zusätzlich einen KI-Provider konfigurieren (siehe [KI-Provider einrichten](ai-providers.md)) — ohne Provider liefert `/ask` einen Fehler.

---

## Voraussetzungen (geplant)

- Mindestens ein angelegter Pflanzdurchlauf oder eine Pflanze
- Ein konfigurierter KI-Provider (siehe [KI-Provider einrichten](ai-providers.md))
- Für den Chat: Erfahrungsstufe **Intermediate** oder höher (siehe [Erfahrungsstufen](#erfahrungsstufen-und-ki-funktionen))

!!! tip "Kein API-Key nötig"
    Mit Ollama (lokal) wird sich der KI-Assistent vollständig auf eigener Hardware betreiben lassen — ohne Konto bei einem Cloud-Dienst und ohne Datenweitergabe.

---

## Geplante Funktionen im Überblick

### Tipp-Karten

Tipp-Karten sollen als kompakte Pflegehinweise automatisch auf der Detailseite einer Pflanze oder eines Pflanzdurchlaufs erscheinen. Das System wird den aktuellen Zustand analysieren und 2 bis 4 priorisierte Empfehlungen anzeigen (Titel, Erklärung, Empfehlung, Priorität). Neue Karten sollen täglich sowie sofort bei Phasenwechsel, EC-/pH-Abweichung oder neuem IPM-Ereignis generiert werden. Karten sollen sich als erledigt oder nicht relevant markieren lassen.

### Chat-Funktion

Der Chat soll einen freien Dialog mit dem KI-Assistenten ermöglichen. Das System soll dabei den vollständigen Kontext der Pflanze kennen: aktuelle Phase, Messwerte (EC, pH, VPD), Düngehistorie und aktive Schädlingsereignisse. Antworten sollen gestreamt (Wort für Wort) erscheinen. Die Chat-Funktion soll ab Erfahrungsstufe **Intermediate** verfügbar sein; Beginner sollen nur Tipp-Karten sehen.

!!! example "Beispielfragen, die künftig gestellt werden können"
    - "Meine unteren Blätter werden gelb — was kann das sein?"
    - "Soll ich in Woche 4 der Blüte den PK-Boost schon starten?"
    - "Der EC ist heute von 1.4 auf 1.8 gestiegen — muss ich spülen?"
    - "Wann ist der optimale Erntezeitpunkt für meine Sorte?"

### Diagnose-Modus

Der Diagnose-Modus soll die gezielte Analyse bei konkreten Problemen ermöglichen: Symptom beschreiben, System analysiert es auf Basis der aktuellen Messwerte, der Pflegehistorie und der internen Wissensbasis. Das Ergebnis soll eine priorisierte Liste möglicher Ursachen mit konkreten Handlungsempfehlungen sein.

---

## Provider-Auswahl und Datenschutz (geplant)

Sobald die Oberfläche verfügbar ist, wird sich unter **Einstellungen > KI-Provider** auswählen lassen, welches System die Anfragen bearbeitet. Bis dahin erfolgt die Provider-Wahl ausschließlich über Betreiber-Konfiguration (siehe [KI-Provider einrichten](ai-providers.md)).

| Provider | Datenweitergabe | API-Key | Kosten |
|----------|----------------|---------|--------|
| Ollama (lokal) | Keine | Nicht nötig | Kostenlos (eigene Hardware) |
| llama.cpp | Keine | Nicht nötig | Kostenlos (eigene Hardware) |
| OpenAI-kompatibel | Abhängig vom Anbieter | Abhängig | Variabel |
| Anthropic Claude | Übertragung an Anthropic (USA) | Erforderlich | Pay-per-Token |

!!! warning "Cloud-Provider und Datenschutz"
    Bei Nutzung eines Cloud-Providers werden Pflanzdaten an externe Server übertragen. Sobald die UI verfügbar ist, wird beim ersten Öffnen des Chats mit einem Cloud-Provider eine Einwilligung abgefragt werden. Wer keine Daten weitergeben möchte, sollte Ollama (lokal) einsetzen.

---

## Erfahrungsstufen und KI-Funktionen (geplant) {#erfahrungsstufen-und-ki-funktionen}

Die verfügbaren KI-Funktionen sollen sich an die eingestellte Erfahrungsstufe anpassen.

| Funktion | Beginner | Intermediate | Expert |
|----------|:--------:|:------------:|:------:|
| Tipp-Karten (vereinfacht) | Ja | Ja | Ja |
| Tipp-Karten (technische Details) | — | Ja | Ja |
| Chat-Funktion | — | Ja | Ja |
| Diagnose-Modus | — | Ja | Ja |
| Quellen der Empfehlungen einsehen | — | — | Ja |
| Technische Kontextdaten im Chat | — | — | Ja |

---

## Verhalten ohne konfigurierten KI-Provider

Kamerplanter wird auch ohne KI-Provider funktionieren. In diesem Fall soll das System regelbasierte Tipp-Karten auf Basis der Stammdaten und der aktuellen Phase generieren — ohne Sprachmodell. Die Qualität wird geringer sein, das System soll aber nie ohne Empfehlungen bleiben.

---

## Häufige Fragen

??? question "Werden meine Pflanzdaten für das Training von KI-Modellen verwendet?"
    Nein. Kamerplanter wird Daten nur zur Beantwortung einer konkreten Anfrage an den konfigurierten Provider senden. Eine Nutzung für Modell-Training ist vertraglich ausgeschlossen (OpenAI API, Anthropic API). Bei lokalen Providern (Ollama, llama.cpp) verlassen Daten das eigene Netzwerk nie.

??? question "Wie aktuell ist die Wissensbasis, die `/knowledge/ask` heute schon nutzt?"
    Die Stammdaten (Pflanzenarten, Nährstoffprofile, Schädlingsdaten) werden wöchentlich neu indexiert. Die thematischen Guides werden bei jedem Kamerplanter-Update gepflegt und aktualisiert.

??? question "Kann ich eigene Pflegehinweise oder Guides zur Wissensbasis hinzufügen?"
    Tenant-Admins können eigene Wissensbasen in YAML-Format hochladen. Diese werden automatisch in die RAG-Wissensbasis integriert. Wie das funktioniert, erklärt der Guide [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md).

??? question "Wann kommt die Chat-Oberfläche?"
    Ein konkreter Termin ist nicht festgelegt. Der Fortschritt lässt sich am Backlog/Issue-Tracker des Projekts verfolgen. <!-- REQ-031 -->

---

## Siehe auch

- [KI-Provider einrichten](ai-providers.md)
- [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md)
- [KI-Architektur (Entwickler)](../architecture/ai-architecture.md)
- [Sensorik und Messdaten](sensors.md)
- [Dünge-Logik](fertilization.md)
