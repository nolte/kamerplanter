# Kalender

Der Kalender zeigt alle geplanten und vergangenen Aktivitäten in einer zentralen Ansicht: Aufgaben, Phasenübergänge, Gießereignisse, IPM-Inspektionen und Tankwartungen. Feeds lassen sich als iCal-Link in Google Calendar, Apple Calendar oder Thunderbird abonnieren.

---

## Voraussetzungen

- Mindestens eine aktive Pflanze oder einen aktiven Pflanzdurchlauf
- Für externe Kalender-Integration: Ein Kalender-Feed muss eingerichtet sein

---

## Die Kalenderansicht öffnen

Klicken Sie in der Navigation auf **Kalender**. Die Kalenderansicht öffnet sich in der Monatsansicht.

---

## Ansichtsmodi

Der Kalender bietet vier Ansichtsmodi, zwischen denen Sie oben rechts wechseln können:

| Modus | Beschreibung |
|-------|-------------|
| **Monat** | Gesamtübersicht des Monats mit Ereignissen pro Tag |
| **Woche** | Detaillierte Wochenansicht mit Zeitachse |
| **Tag** | Alle Ereignisse eines Tages in der Tagesdetailansicht |
| **Liste** | Tabellarische Listenansicht aller kommenden Ereignisse |

Für den täglichen Überblick empfiehlt sich die **Wochen-** oder **Listenansicht**.

---

## Ereignis-Kategorien und Farbkodierung

Jede Ereignis-Kategorie hat eine eigene Farbe für schnelle visuelle Orientierung:

| Farbe | Kategorie | Beschreibung |
|-------|----------|-------------|
| Blau | Aufgaben | Alle geplanten Pflegeaufgaben |
| Grün | Phasenübergänge | Geplante oder durchgeführte Phasenwechsel |
| Türkis | Gießereignisse | Dokumentierte Gießvorgänge |
| Orange | IPM / Pflanzenschutz | Inspektionen und Behandlungen |
| Rot | Ernten | Geplante und durchgeführte Ernten |
| Grau | Tankwartung | Wasserwechsel, Kalibrierungen |

---

## Ereignisse filtern

Für große Gärten mit vielen Pflanzen kann der Kalender schnell unübersichtlich werden. Nutzen Sie die Filter-Leiste oben:

- **Kategorie**: Nur bestimmte Ereignistypen anzeigen
- **Standort (Location)**: Nur Ereignisse eines bestimmten Bereichs
- **Pflanze / Durchlauf**: Nur Ereignisse einer Pflanze oder eines Durchlaufs
- **Priorität**: Nur kritische oder hohe Priorität
- **Status**: Nur offene, erledigte oder überfällige Aufgaben

!!! tip "Filter kombinieren"
    Sie können mehrere Filter gleichzeitig aktiv haben. So sehen Sie z.B. nur die kritischen offenen Aufgaben für "Growzelt A" in der nächsten Woche.

---

## Aufgabe direkt aus dem Kalender heraus erledigen

Klicken Sie auf ein Aufgaben-Ereignis im Kalender. Ein kompaktes Panel öffnet sich mit:

- Titel und Beschreibung der Aufgabe
- Zugehörige Pflanze(n)
- Schaltfläche **Erledigt markieren**

So können Sie Aufgaben direkt im Kalender abhaken, ohne zur Aufgaben-Listenansicht wechseln zu müssen.

---

## Neue Aufgabe aus dem Kalender erstellen

1. Klicken Sie auf einen leeren Tag oder eine leere Zeitstelle im Kalender.
2. Ein Schnellerstellungs-Dialog öffnet sich.
3. Geben Sie Titel, Typ und Pflanzenzuordnung ein.
4. Klicken Sie auf **Erstellen** — die Aufgabe erscheint sofort im Kalender.

---

## Kalender in externe Apps exportieren (iCal)

Sie können Ihren Kamerplanter-Kalender in externe Kalender-Apps abonnieren. So erhalten Sie Erinnerungen auf Ihrem Smartphone, auch wenn Sie die Kamerplanter-App nicht geöffnet haben.

!!! note "Nur lesen — keine bidirektionale Synchronisation"
    Der iCal-Feed ist nur lesbar. Änderungen in Google Calendar oder Apple Calendar werden nicht an Kamerplanter zurückgespiegelt. Neue Aufgaben erstellen Sie weiterhin in Kamerplanter.

### Schritt 1: Kalender-Feed einrichten

1. Navigieren Sie zu **Kalender → Feeds** (Tab oben rechts im Kalender).
2. Klicken Sie auf **Neuer Feed**.
3. Geben Sie dem Feed einen Namen (z.B. "Mein Hauptkalender" oder "Nur Growzelt A").

### Schritt 2: Feed konfigurieren

| Einstellung | Beschreibung |
|-------------|-------------|
| Name | Anzeigename in der externen App |
| Kategorien | Welche Ereignistypen soll der Feed enthalten? |
| Standort-Filter | Nur Ereignisse eines bestimmten Bereichs |
| Priorität-Filter | Nur ab einer bestimmten Priorität |

### Schritt 3: Feed-URL kopieren

Nach dem Speichern erscheint eine `webcal://`-URL. Kopieren Sie diese URL.

### Schritt 4: In externem Kalender abonnieren

=== "Google Calendar"

    1. Öffnen Sie Google Calendar auf dem Desktop.
    2. Links unter "Andere Kalender" klicken Sie auf das Plus-Symbol.
    3. Wählen Sie **Per URL**.
    4. Fügen Sie die `webcal://`-URL ein.
    5. Klicken Sie auf **Kalender hinzufügen**.

=== "Apple Calendar (macOS)"

    1. Öffnen Sie Apple Calendar.
    2. Klicken Sie auf **Ablage → Neues Kalenderabonnement**.
    3. Fügen Sie die `webcal://`-URL ein.
    4. Klicken Sie auf **Abonnieren**.

=== "Thunderbird (Lightning)"

    1. Öffnen Sie Thunderbird.
    2. Im Kalender-Tab klicken Sie auf **Neuer Kalender**.
    3. Wählen Sie **Im Netzwerk**.
    4. Wählen Sie **iCalendar (ICS)** und fügen Sie die URL ein.
    5. Klicken Sie auf **Weiter** und vergeben Sie einen Namen.

=== "Android (Standard-Kalender)"

    1. Installieren Sie eine App wie **ICSx5** aus dem Play Store.
    2. Fügen Sie die `webcal://`-URL als neues Abonnement hinzu.

### Feed aktualisieren oder löschen

Feeds können jederzeit bearbeitet oder gelöscht werden unter **Kalender → Feeds**. Beim Löschen wird der Feed-Link ungültig — er muss in der externen App ebenfalls entfernt werden.

---

## Aussaatkalender (Freiland)

Für Freilandgärtner bietet Kamerplanter einen integrierten Aussaatkalender, der zeigt, wann Voranzucht, Direktsaat und Auspflanzen für Ihre Pflanzen sinnvoll sind.

### Aussaatkalender öffnen

Klicken Sie im Kalender oben auf **Aussaatkalender** (Tab).

Der Aussaatkalender zeigt:
- **Voranzucht-Zeitfenster** (Indoor): Wann Samen drinnen vorziehen
- **Direktsaat-Zeitfenster**: Wann Direktsaat ins Beet möglich ist
- **Auspflanzen**: Wann vorgezogene Pflanzen raus können
- **Erwartete Erntezeit**: Auf Basis der Wachstumsdauer der Sorte

### Frosttermin konfigurieren

Damit der Aussaatkalender korrekte Termine berechnet, hinterlegen Sie den letzten Frosttermin für Ihren Standort:

1. Öffnen Sie **Einstellungen → Standort** oder öffnen Sie die Site-Detailseite.
2. Tragen Sie unter **Frostdaten** den mittleren letzten Frosttermin für Ihren Standort ein (z.B. "15. April" für Mitteleuropa).
3. Das System berechnet alle Aussaatdaten relativ zu diesem Datum.

---

## Häufige Fragen

??? question "Warum sehe ich eine Aufgabe im Kalender, die ich schon abgehakt habe?"
    Abgehakte Aufgaben werden standardmäßig nicht ausgeblendet, sondern als erledigt markiert angezeigt. Aktivieren Sie im Filter **Nur offene Aufgaben**, um erledigte auszublenden.

??? question "Kann ich wiederkehrende Ereignisse im Kalender anlegen?"
    Ja, aber nur über Pflegeprofile und Workflow-Templates — nicht direkt im Kalender. Ein Pflegeprofil mit wöchentlichem Düngeintervall erstellt automatisch wiederkehrende Aufgaben, die im Kalender erscheinen.

??? question "Wie oft aktualisiert sich der iCal-Feed?"
    Der iCal-Feed wird bei jeder Abfrage durch die externe App in Echtzeit generiert. Die Aktualisierungsfrequenz hängt von der externen Kalender-App ab — Google Calendar aktualisiert ca. alle 24 Stunden, Apple Calendar alle 12 Stunden.

??? question "Kann ich den Kalender auf mehrere Personen im Garten aufteilen?"
    Ja. Sie können mehrere Feeds mit unterschiedlichen Filtern (z.B. nach Standort oder Kategorie) anlegen und an verschiedene Personen weitergeben. Jedes Mitglied des Mandanten erhält so seinen personalisierten Kalender-Feed.

---

## Siehe auch

- [Aufgaben](tasks.md)
- [Dashboard](dashboard.md)
- [Pflanzdurchläufe](planting-runs.md)
