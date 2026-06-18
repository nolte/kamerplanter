# Aufgaben und Pflegeerinnerungen

Kamerplanter erstellt automatisch Aufgaben aus Workflows und Pflegeprofilen und erinnert dich rechtzeitig an alle anfallenden Pflegearbeiten. Du behältst jederzeit die volle Kontrolle: Aufgaben können angepasst, neu erstellt und flexibel verwaltet werden.

---

## Voraussetzungen

- Mindestens eine angelegte Pflanze oder ein aktiver Pflanzdurchlauf
- Pflegeprofile werden automatisch vorgeschlagen, können aber auch manuell konfiguriert werden

---

## Aufgaben in der Übersicht

Die Aufgaben-Übersicht findest du über **Aufgaben** in der Navigation. Die Ansicht zeigt:

- **Heute fällig**: Aufgaben, die heute erledigt werden sollten
- **Überfällig**: Aufgaben, die ihr Fälligkeitsdatum überschritten haben (rot markiert)
- **Kommende Woche**: Aufgaben der nächsten 7 Tage
- **Alle Aufgaben**: Vollständige Liste mit Filter- und Sortiermöglichkeiten

Jede Aufgabe zeigt:
- Typ (Gießen, Düngen, Inspektion, Ernte usw.)
- Zugehörige Pflanze(n) oder Pflanzdurchlauf
- Priorität (Niedrig / Normal / Hoch / Kritisch)
- Fälligkeitsdatum

---

## Aufgaben-Typen

Kamerplanter unterscheidet zwischen manuell erstellten Aufgaben und automatisch generierten Aufgaben:

**Automatisch generierte Aufgaben entstehen durch:**
- Gießplan (basierend auf eingestelltem Intervall oder Substratfeuchte)
- Pflegeprofil-Engine (Erinnerungen für Düngen, Umtopfen, Reinigung)
- Phasenübergänge (Aufgabe "Zur nächsten Phase wechseln prüfen")
- Tankwartung (Wasserwechsel, Kalibrierung)
- IPM-Inspektionspläne (Schädlingskontrolle)
- Sensorausfälle ("Sensor XY prüfen")
- Saisonale Trigger (Frostschutz, Überwinterung)

**Manuell erstellbare Aufgaben:**
- Beliebige Einzelaufgaben (Freitext)
- Aufgaben aus Workflow-Templates

---

## Eine manuelle Aufgabe erstellen

### Schritt 1: Neue Aufgabe anlegen

Klicke in der Aufgaben-Übersicht auf **Aufgabe erstellen** (oben rechts).

### Schritt 2: Aufgabe beschreiben

| Feld | Beschreibung |
|------|-------------|
| Titel | Kurze, prägnante Beschreibung |
| Beschreibung | Ausführliche Details und Anweisungen |
| Typ | Kategorie (Gießen, Düngen, Inspektion, Training, Ernte, Sonstiges) |
| Priorität | Niedrig / Normal / Hoch / Kritisch |
| Fälligkeitsdatum | Wann muss die Aufgabe erledigt sein? |
| Pflanze / Durchlauf | Zuordnung zu Pflanze(n) oder Pflanzdurchlauf |
| Tags | Freie Schlagwörter (z.B. "dringend", "mit-partner-besprechen") |

### Schritt 3: Optional: Erinnerung einrichten

Aktiviere die Erinnerungsfunktion, um vor Fälligkeit eine Benachrichtigung zu erhalten.

### Schritt 4: Speichern

Die Aufgabe erscheint sofort in der Aufgaben-Übersicht und im Kalender.

---

## Aufgabe als erledigt markieren

### Einzelne Aufgabe abschließen

1. Öffne die Aufgabe durch Klick auf den Titel.
2. Klicke auf **Erledigt markieren**.
3. Optional: Trage ein Erledigungsdatum und eine Notiz ein.
4. Bestätige.

### Aufgabe direkt aus der Listenansicht abhaken

Klicke auf das Häkchen-Symbol neben einer Aufgabe in der Liste. Die Aufgabe wird sofort als erledigt markiert.

!!! tip "Adaptive Zeitpläne"
    Kamerplanter lernt aus deinen Erledigungsmustern. Wenn du eine Gießaufgabe konsequent einen Tag früher abhakst, passt das System das Intervall automatisch an (bis zu ±30 % Abweichung vom Ursprungsintervall).

---

## Mehrere Aufgaben auf einmal bearbeiten

Wenn viele Aufgaben gleichzeitig anfallen, kannst du sie gebündelt bearbeiten, statt jede einzeln anzufassen.

1. Klicke in der Aufgaben-Übersicht oben rechts auf **Mehrere auswählen**. (Der Button erscheint, sobald mindestens eine Aufgabe vorhanden ist.)
2. Neben jeder Aufgabe erscheint eine Auswahl-Checkbox. Hake die gewünschten Aufgaben an — oder nutze **Alle auswählen** in der Aktionsleiste.
3. Wähle in der Aktionsleiste die gewünschte Sammelaktion:
    - **Abschließen** — alle markierten Aufgaben werden als erledigt markiert.
    - **Überspringen** — alle markierten Aufgaben werden übersprungen.
    - **Löschen** — alle markierten Aufgaben werden entfernt.
4. Über **Abbrechen** verlässt du den Auswahlmodus wieder, ohne etwas zu ändern.

---

## Workflow-Templates nutzen

Workflow-Templates sind vordefinierte Aufgaben-Pakete für häufige Pflegeszenarien. Ein Template instantiieren bedeutet: Das System erstellt aus dem Template eine Reihe konkreter Aufgaben für deine Pflanze oder deinen Durchlauf.

### Schritt 1: Template auswählen

Navigiere zu **Aufgaben → Workflow-Templates**. Du siehst vordefinierte System-Templates:

**Indoor-Templates:**
- Cannabis SOG (Sea of Green)
- Cannabis SCROG (Screen of Green)
- Nährlösung-Wechsel (Hydroponik)
- Sonden-Kalibrierung

**Zimmerpflanzen-Templates:**
- Tropische Grünpflanze (Standard)
- Orchidee (Phalaenopsis)
- Kaktus / Sukkulente
- Calathea / Marante
- Umtopf-Workflow
- Überwinterungs-Workflow

**Freiland-Templates:**
- Frostschutz-Workflow
- Abhärtungs-Workflow (Indoor → Outdoor)
- Frühjahrs-Beetvorbereitung
- Voranzucht-Workflow
- Saisonende-Workflow (Herbst)
- Rosen-Jahrespflege

### Schritt 2: Template auf Pflanze oder Durchlauf anwenden

1. Klicke auf **Template anwenden** neben dem gewünschten Template.
2. Wähle die Zielpflanze(n) oder den Pflanzdurchlauf.
3. Wähle ein Startdatum.
4. Das System berechnet automatisch alle Fälligkeitsdaten basierend auf dem Template und der Wachstumsphase.
5. Bestätige — alle Aufgaben werden angelegt.

### Eigene Templates erstellen

Wenn du eine Abfolge von Aufgaben öfter nutzt:

1. Navigiere zu **Aufgaben → Workflow-Templates → Neues Template**.
2. Gib dem Template einen Namen und eine Beschreibung.
3. Füge Aufgaben hinzu (Titel, Typ, Tage nach Start).
4. Speichere. Das Template steht nun für alle deine Pflanzen zur Verfügung.

---

## Pflegeprofile und automatische Erinnerungen

Pflegeprofile definieren das grundlegende Pflegeverhalten einer Pflanze: Wie oft gießen? Wie oft düngen? Wann neu eintopfen?

### Pflegeprofil einsehen und anpassen

1. Öffne eine Pflanze und wechsle zum Tab **Pflege**.
2. Das System schlägt automatisch ein Pflegeprofil basierend auf der Pflanzenart vor.
3. Klicke auf **Profil bearbeiten**, um die Intervalle anzupassen.

**Einstellbare Parameter:**
- Gieß-Intervall (Tage) oder Modus (nach Substratfeuchte)
- Dünge-Intervall (Wochen)
- Umtopf-Intervall (Monate)
- Saisonale Multiplizitäten (z.B. weniger gießen im Winter)

### Vordefinierte Pflegestile

Kamerplanter kennt neun Pflegestile, die automatisch aus der Pflanzenfamilie abgeleitet werden:

| Pflegestil | Typische Pflanzen | Besonderheit |
|-----------|------------------|-------------|
| Tropisch | Monstera, Philodendron, Ficus | Hohe Luftfeuchtigkeit, regelmäßiges Gießen |
| Mediterran | Rosmarin, Thymian, Lavendel | Trockenheitsresistent, selten gießen |
| Sukkulente / Kaktus | Kakteen, Echeverien, Aloe | Seltenes Gießen, Winterruhe |
| Orchidee | Phalaenopsis, Dendrobium | Tauchbad statt Gießen, Temperatur-Drop |
| Farn | Farne, Calathea | Hohe Luftfeuchte, kein Staunass |
| Gemüse (Starkzehrer) | Tomate, Kürbis, Paprika | Intensive Düngung, regelmäßig gießen |
| Gemüse (Schwachzehrer) | Kräuter, Salat, Radieschen | Kaum Dünger, mäßig wässern |
| Cannabis | Cannabis | Phasenabhängige Bewässerung und Düngung |
| Hydroponik | Alle Hydro-Pflanzen | EC/pH-Kontrolle, Reservoirwechsel |

---

## Aufgaben filtern und sortieren

In der Aufgaben-Übersicht stehen folgende Filter zur Verfügung:

- **Nach Status**: Offen / Erledigt / Überfällig
- **Nach Typ**: Gießen, Düngen, Inspektion, Ernte, Training, Sonstiges
- **Nach Pflanze oder Durchlauf**
- **Nach Standort**
- **Nach Priorität**
- **Nach Tags**

Klicke auf den Filter-Button oben in der Liste, um die Filter-Leiste ein- oder auszublenden.

---

## Häufige Fragen

??? question "Wie viele automatische Aufgaben erstellt Kamerplanter pro Tag?"
    Das hängt von der Anzahl deiner Pflanzen und aktiven Pflegeprofilen ab. Kamerplanter bündelt mehrere Aufgaben wenn möglich (z.B. "Alle Pflanzen in Zelt A gießen" statt einzelner Gieß-Aufgaben pro Pflanze). Du kannst in den Einstellungen konfigurieren, ob Aufgaben pro Pflanze oder pro Standort gebündelt werden.

??? question "Kann ich eine automatisch erstellte Aufgabe löschen?"
    Ja. Du kannst jede Aufgabe unabhängig von ihrer Herkunft löschen. Wenn du eine Aufgabe eines laufenden Pflegeplans löschst, erstellt Kamerplanter beim nächsten Planungsdurchlauf (täglich) eine neue Aufgabe — sofern das Pflegeprofil noch aktiv ist.

??? question "Was passiert mit den Aufgaben, wenn ich eine Pflanze entferne?"
    Wenn du eine Pflanze entfernst, werden ihre noch offenen Aufgaben (offen, in Bearbeitung, ruhend) automatisch aus der Warteschlange entfernt — sie sind nach dem Entfernen der Pflanze nicht mehr relevant. Bereits erledigte, übersprungene oder fehlgeschlagene Aufgaben bleiben als Verlauf erhalten. Für entfernte Pflanzen werden außerdem keine neuen automatischen Aufgaben (z. B. Pflegeerinnerungen oder Spül-Hinweise) mehr erzeugt.

??? question "Was bedeutet die rote Markierung bei überfälligen Aufgaben?"
    Eine rote Markierung bedeutet, dass eine Aufgabe ihr Fälligkeitsdatum überschritten hat. Das ist ein Hinweis, keine automatische Eskalation. Kamerplanter eskaliert überfällige Aufgaben nach 48 Stunden in der Priorität auf "Kritisch".

??? question "Kann ich Aufgaben an andere Mitglieder meines Mandanten zuweisen?"
    Ja, wenn du in einem Gemeinschaftsgarten (mit mehreren Mitgliedern) arbeitest. Öffne die Aufgabe und weise sie über das Feld **Zuständig** einem Mitglied zu.

---

## Siehe auch

- [Kalender](calendar.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Integrierter Pflanzenschutz](pest-management.md)
