# Aufgaben und Pflegeerinnerungen

Kamerplanter erstellt automatisch Aufgaben aus Workflows und Pflegeprofilen und erinnert Sie rechtzeitig an alle anfallenden Pflegearbeiten. Sie behalten jederzeit die volle Kontrolle: Aufgaben können angepasst, neu erstellt und flexibel verwaltet werden.

---

## Voraussetzungen

- Mindestens eine angelegte Pflanze oder ein aktiver Pflanzdurchlauf
- Pflegeprofile werden automatisch vorgeschlagen, können aber auch manuell konfiguriert werden

---

## Aufgaben in der Übersicht

Die Aufgaben-Übersicht finden Sie über **Aufgaben** in der Navigation. Die Ansicht zeigt:

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

Klicken Sie in der Aufgaben-Übersicht auf **Aufgabe erstellen** (oben rechts).

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

Aktivieren Sie die Erinnerungsfunktion, um vor Fälligkeit eine Benachrichtigung zu erhalten.

### Schritt 4: Speichern

Die Aufgabe erscheint sofort in der Aufgaben-Übersicht und im Kalender.

---

## Aufgabe als erledigt markieren

### Einzelne Aufgabe abschließen

1. Öffnen Sie die Aufgabe durch Klick auf den Titel.
2. Klicken Sie auf **Erledigt markieren**.
3. Optional: Tragen Sie ein Erledigungsdatum und eine Notiz ein.
4. Bestätigen Sie.

### Aufgabe direkt aus der Listenansicht abhaken

Klicken Sie auf das Häkchen-Symbol neben einer Aufgabe in der Liste. Die Aufgabe wird sofort als erledigt markiert.

!!! tip "Adaptive Zeitpläne"
    Kamerplanter lernt aus Ihren Erledigungsmustern. Wenn Sie eine Gießaufgabe konsequent einen Tag früher abhaken, passt das System das Intervall automatisch an (bis zu ±30 % Abweichung vom Ursprungsintervall).

---

## Workflow-Templates nutzen

Workflow-Templates sind vordefinierte Aufgaben-Pakete für häufige Pflegeszenarien. Ein Template instantiieren bedeutet: Das System erstellt aus dem Template eine Reihe konkreter Aufgaben für Ihre Pflanze oder Ihren Durchlauf.

### Schritt 1: Template auswählen

Navigieren Sie zu **Aufgaben → Workflow-Templates**. Sie sehen vordefinierte System-Templates:

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

1. Klicken Sie auf **Template anwenden** neben dem gewünschten Template.
2. Wählen Sie die Zielpflanze(n) oder den Pflanzdurchlauf.
3. Wählen Sie ein Startdatum.
4. Das System berechnet automatisch alle Fälligkeitsdaten basierend auf dem Template und der Wachstumsphase.
5. Bestätigen Sie — alle Aufgaben werden angelegt.

### Eigene Templates erstellen

Wenn Sie eine Abfolge von Aufgaben öfter nutzen:

1. Navigieren Sie zu **Aufgaben → Workflow-Templates → Neues Template**.
2. Geben Sie dem Template einen Namen und eine Beschreibung.
3. Fügen Sie Aufgaben hinzu (Titel, Typ, Tage nach Start).
4. Speichern Sie. Das Template steht nun für alle Ihre Pflanzen zur Verfügung.

---

## Pflegeprofile und automatische Erinnerungen

Pflegeprofile definieren das grundlegende Pflegeverhalten einer Pflanze: Wie oft gießen? Wie oft düngen? Wann neu eintopfen?

### Pflegeprofil einsehen und anpassen

1. Öffnen Sie eine Pflanze und wechseln Sie zum Tab **Pflege**.
2. Das System schlägt automatisch ein Pflegeprofil basierend auf der Pflanzenart vor.
3. Klicken Sie auf **Profil bearbeiten**, um die Intervalle anzupassen.

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

Klicken Sie auf den Filter-Button oben in der Liste, um die Filter-Leiste ein- oder auszublenden.

---

## Häufige Fragen

??? question "Wie viele automatische Aufgaben erstellt Kamerplanter pro Tag?"
    Das hängt von der Anzahl Ihrer Pflanzen und aktiven Pflegeprofilen ab. Kamerplanter bündelt mehrere Aufgaben wenn möglich (z.B. "Alle Pflanzen in Zelt A gießen" statt einzelner Gieß-Aufgaben pro Pflanze). Sie können in den Einstellungen konfigurieren, ob Aufgaben pro Pflanze oder pro Standort gebündelt werden.

??? question "Kann ich eine automatisch erstellte Aufgabe löschen?"
    Ja. Sie können jede Aufgabe unabhängig von ihrer Herkunft löschen. Wenn Sie eine Aufgabe eines laufenden Pflegeplans löschen, erstellt Kamerplanter beim nächsten Planungsdurchlauf (täglich) eine neue Aufgabe — sofern das Pflegeprofil noch aktiv ist.

??? question "Was bedeutet die rote Markierung bei überfälligen Aufgaben?"
    Eine rote Markierung bedeutet, dass eine Aufgabe ihr Fälligkeitsdatum überschritten hat. Das ist ein Hinweis, keine automatische Eskalation. Kamerplanter eskaliert überfällige Aufgaben nach 48 Stunden in der Priorität auf "Kritisch".

??? question "Kann ich Aufgaben an andere Mitglieder meines Mandanten zuweisen?"
    Ja, wenn Sie in einem Gemeinschaftsgarten (mit mehreren Mitgliedern) arbeiten. Öffnen Sie die Aufgabe und weisen Sie sie über das Feld **Zuständig** einem Mitglied zu.

---

## Siehe auch

- [Kalender](calendar.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Integrierter Pflanzenschutz](pest-management.md)
