# KI-Assistent

Der KI-Assistent in Kamerplanter gibt Ihnen kontextabhängige Pflegehinweise, unterstützt bei der Diagnose von Problemen und beantwortet Fragen zu Ihren Pflanzen — direkt auf Basis Ihrer eigenen Daten.

---

## Voraussetzungen

- Mindestens ein angelegter Pflanzdurchlauf oder eine Pflanze
- Ein konfigurierter KI-Provider (siehe [KI-Provider einrichten](ai-providers.md))
- Für den Chat: Erfahrungsstufe **Intermediate** oder höher (siehe [Erfahrungsstufen](#erfahrungsstufen-und-ki-funktionen))

!!! tip "Kein API-Key nötig"
    Mit Ollama (lokal) können Sie den KI-Assistenten vollständig auf Ihrer eigenen Hardware betreiben — ohne Konto bei einem Cloud-Dienst und ohne Datenweitergabe.

---

## Tipp-Karten

Tipp-Karten sind kompakte Pflegehinweise, die automatisch auf der Detailseite Ihrer Pflanze oder Ihres Pflanzdurchlaufs erscheinen. Das System analysiert den aktuellen Zustand und gibt 2 bis 4 priorisierte Empfehlungen.

### Was Tipp-Karten anzeigen

Jede Karte zeigt:

- **Titel** — Knappe Zusammenfassung des Hinweises
- **Erklärung** — Was das System erkannt hat und warum es relevant ist
- **Empfehlung** — Was Sie konkret tun können
- **Priorität** — Kritisch, hoch, mittel oder niedrig (farblich markiert)

!!! info "Screenshot folgt"
    Dieser Screenshot wird in einer zukünftigen Version ergänzt.

### Wann werden Tipp-Karten aktualisiert?

Das System generiert täglich neue Tipp-Karten für alle aktiven Durchläufe. Zusätzlich werden Karten sofort neu generiert, wenn:

- Die Wachstumsphase wechselt
- Ein EC- oder pH-Wert außerhalb des Zielbereichs liegt
- Ein IPM-Ereignis (Schädlingsbefall, Krankheit) eingetragen wurde

!!! note "Zwischenspeicherung"
    Tipp-Karten werden für 4 Stunden gespeichert. Falls Sie eine Karte als erledigt markieren oder ablehnen, erscheint sie nicht erneut, bis sich der Zustand der Pflanze wesentlich ändert.

### Tipp-Karte ablehnen oder als erledigt markieren

Klicken Sie auf das Dreipunkt-Menü einer Karte:

- **Erledigt** — Der Hinweis wird als umgesetzt markiert und verschwindet
- **Nicht relevant** — Die Karte wird ausgeblendet; das System lernt daraus
- **Details** — Zeigt die Quellen, auf denen die Empfehlung basiert

---

## Chat-Funktion

Der Chat ermöglicht einen freien Dialog mit dem KI-Assistenten. Das System kennt dabei den vollständigen Kontext Ihrer Pflanze: aktuelle Phase, Messwerte (EC, pH, VPD), Düngehistorie und aktive Schädlingsereignisse.

!!! info "Verfügbarkeit"
    Die Chat-Funktion ist ab der Erfahrungsstufe **Intermediate** verfügbar. Beginner sehen nur Tipp-Karten.

### Chat öffnen

1. Öffnen Sie die Detailseite einer Pflanze oder eines Pflanzdurchlaufs
2. Klicken Sie auf **KI-Chat** (Symbol in der oberen Symbolleiste)
3. Das Chat-Panel öffnet sich seitlich

### Beispielfragen

Das System versteht Fragen in natürlicher Sprache. Einige Beispiele:

!!! example "Fragen die Sie stellen können"
    - "Meine unteren Blätter werden gelb — was kann das sein?"
    - "Soll ich in Woche 4 der Blüte den PK-Boost schon starten?"
    - "Der EC ist heute von 1.4 auf 1.8 gestiegen — muss ich spülen?"
    - "Wann ist der optimale Erntezeitpunkt für meine Sorte?"
    - "Die Luftfeuchtigkeit war heute 80 % — wie hoch ist mein Schimmelrisiko?"
    - "Kann ich Topping noch durchführen oder ist die Pflanze schon zu weit?"

### Antworten werden gestreamt

Antworten erscheinen Wort für Wort, sobald das Modell sie generiert. Sie müssen nicht auf die vollständige Antwort warten.

### Chat-Verlauf

Alle Gespräche werden gespeichert und sind unter **KI-Chat > Verlauf** abrufbar. Der Verlauf wird nach 90 Tagen automatisch gelöscht (DSGVO-Richtlinie).

!!! warning "Cloud-Provider und Datenschutz"
    Bei Nutzung von OpenAI oder Anthropic werden Ihre Pflanzdaten an externe Server übertragen. Beim ersten Öffnen des Chats mit einem Cloud-Provider wird Ihre Einwilligung abgefragt. Wenn Sie keine Daten weitergeben möchten, verwenden Sie Ollama (lokal).

---

## Diagnose-Modus

Der Diagnose-Modus ist für die gezielte Analyse bei konkreten Problemen gedacht. Sie beschreiben ein Symptom — das System analysiert es auf Basis Ihrer aktuellen Messwerte, der Pflegehistorie und der internen Wissensbasis.

### Diagnose starten

1. Öffnen Sie die Detailseite der betroffenen Pflanze
2. Klicken Sie auf **Diagnose** (oder öffnen Sie den Chat und tippen Sie das Symptom ein)
3. Beschreiben Sie das Problem möglichst genau

!!! example "Symptome die das System analysieren kann"
    - Gelbe oder braune Blätter (Verfärbungsmuster beschreiben: oben/unten, gleichmäßig/fleckig)
    - Verformte oder kleine Blätter
    - Schädlingszeichen (Gespinste, Fraßspuren, kleine Insekten)
    - EC-Drift (steigend oder fallend)
    - Ungewöhnlich langsames Wachstum
    - Wurzelverfärbungen

### Wie das System analysiert

Das System kombiniert:

1. **Ihren IST-Zustand** — Phase, aktuelle EC/pH/VPD-Werte, letzte Pflege-Ereignisse
2. **Stammdaten der Pflanzenart** — bekannte Empfindlichkeiten, Nährstoffbedarf pro Phase
3. **Wissensbasis** — kuratiertes Expertenwissen zu Symptomen, Ursachen und Gegenmaßnahmen

Das Ergebnis ist eine priorisierte Liste möglicher Ursachen mit konkreten Handlungsempfehlungen.

---

## Provider-Auswahl und Datenschutz

Sie können unter **Einstellungen > KI-Provider** wählen, welches System Ihre Anfragen bearbeitet.

| Provider | Datenweitergabe | API-Key | Kosten |
|----------|----------------|---------|--------|
| Ollama (lokal) | Keine | Nicht nötig | Kostenlos (eigene Hardware) |
| llama.cpp | Keine | Nicht nötig | Kostenlos (eigene Hardware) |
| OpenAI | Übertragung an OpenAI (USA) | Erforderlich | Pay-per-Token |
| Anthropic Claude | Übertragung an Anthropic (USA) | Erforderlich | Pay-per-Token |
| OpenAI-kompatibel | Abhängig vom Anbieter | Abhängig | Variabel |

!!! warning "Cloud-Provider erfordern DSGVO-Einwilligung"
    Bei der ersten Nutzung eines Cloud-Providers fragt Kamerplanter nach Ihrer Einwilligung zur Datenübertragung. Sie können diese Einwilligung jederzeit unter **Einstellungen > Datenschutz** widerrufen.

Wie Sie einen Provider einrichten, erklärt die Seite [KI-Provider einrichten](ai-providers.md).

---

## Erfahrungsstufen und KI-Funktionen

Die verfügbaren KI-Funktionen passen sich Ihrer eingestellten Erfahrungsstufe an.

| Funktion | Beginner | Intermediate | Expert |
|----------|:--------:|:------------:|:------:|
| Tipp-Karten (vereinfacht) | Ja | Ja | Ja |
| Tipp-Karten (technische Details) | — | Ja | Ja |
| Chat-Funktion | — | Ja | Ja |
| Diagnose-Modus | — | Ja | Ja |
| Quellen der Empfehlungen einsehen | — | — | Ja |
| Technische Kontextdaten im Chat | — | — | Ja |

Die Erfahrungsstufe können Sie jederzeit unter **Einstellungen > Erfahrungsstufe** ändern.

---

## Wenn kein KI-Provider verfügbar ist

Kamerplanter funktioniert auch ohne KI-Provider. In diesem Fall generiert das System regelbasierte Tipp-Karten auf Basis der Stammdaten und der aktuellen Phase — ohne Sprachmodell. Die Qualität ist geringer, aber das System ist nie ohne Empfehlungen.

!!! note "Regelbasierter Fallback"
    Der Fallback greift automatisch, wenn kein Provider konfiguriert ist oder der konfigurierte Provider nicht erreichbar ist. Sie sehen in diesem Fall das Symbol "Regelbasiert" auf den Tipp-Karten.

---

## Häufige Fragen

??? question "Werden meine Pflanzdaten für das Training von KI-Modellen verwendet?"
    Nein. Kamerplanter sendet Ihre Daten nur zur Beantwortung Ihrer konkreten Anfrage an den konfigurierten Provider. Eine Nutzung für Modell-Training ist vertraglich ausgeschlossen (OpenAI API, Anthropic API). Bei lokalen Providern (Ollama, llama.cpp) verlassen Ihre Daten Ihr Netzwerk nie.

??? question "Wie aktuell ist die Wissensbasis des KI-Assistenten?"
    Die Stammdaten (Pflanzenarten, Nährstoffprofile, Schädlingsdaten) werden wöchentlich neu indexiert. Die thematischen Guides (Expertenwissen zu Diagnose, Düngung, Umwelt) werden bei jedem Kamerplanter-Update gepflegt und aktualisiert.

??? question "Kann ich eigene Pflegehinweise oder Guides zur Wissensbasis hinzufügen?"
    Tenant-Admins können eigene Wissensbasen in YAML-Format hochladen. Diese werden automatisch in die RAG-Wissensbasis integriert. Wie das funktioniert, erklärt der Guide [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md).

??? question "Warum liefert der KI-Assistent manchmal unterschiedliche Antworten auf dieselbe Frage?"
    Sprachmodelle sind probabilistische Systeme — die Antworten variieren leicht. Die Faktenbasis (Ihre Messwerte, Stammdaten, Wissensbasis) ist immer gleich, aber die Formulierung und Gewichtung kann abweichen. Bei kritischen Entscheidungen (z.B. Erntezeitpunkt) empfehlen wir, mehrere Anfragen zu stellen und die Antworten zu vergleichen.

??? question "Der Assistent antwortet sehr langsam — was kann ich tun?"
    Bei lokalen Providern (Ollama) hängt die Geschwindigkeit von Ihrer Hardware ab. Tipps zur Optimierung: (1) GPU-Beschleunigung aktivieren, falls vorhanden. (2) Kleineres Modell verwenden (z.B. `llama3.2:3b` statt `gemma3:4b`). (3) Für Tipp-Karten ist die Geschwindigkeit weniger kritisch, da diese täglich im Hintergrund generiert werden.

---

## Siehe auch

- [KI-Provider einrichten](ai-providers.md)
- [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md)
- [KI-Architektur (Entwickler)](../architecture/ai-architecture.md)
- [Sensorik und Messdaten](sensors.md)
- [Dünge-Logik](fertilization.md)
