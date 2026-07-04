# Kalender

Der Kalender zeigt alle geplanten und vergangenen Aktivitäten in einer zentralen Ansicht: Aufgaben, Phasenübergänge, Gießvorschau, Termine für Integrierten Pflanzenschutz (IPM), Ernten und Tankwartungen — wahlweise als Monatsraster, Liste, Phasen-Timeline, Aussaatkalender oder Saisonübersicht. Ereignisse lassen sich als iCal-Feed in externe Kalender-Apps abonnieren.

---

## Voraussetzungen

- Mindestens eine aktive Pflanze oder ein aktiver Pflanzdurchlauf
- Für externe Kalender-Integration: Ein Kalender-Feed muss eingerichtet sein

---

## Die Kalenderansicht öffnen

Klicke in der Navigation auf **Kalender**. Die Ansicht öffnet standardmäßig in der Monatsansicht.

---

## Die fünf Ansichten

Oben im Kalender wechselst du über Tabs zwischen fünf Ansichten:

| Tab | Beschreibung |
|-----|-------------|
| **Monatsansicht** | Monatsraster mit bis zu drei Ereignissen pro Tag; weitere werden als „+N" zusammengefasst |
| **Listenansicht** | Tabellarische Liste aller im aktuellen Monat gefilterten Ereignisse, sortierbar |
| **Phasen-Timeline** | Balkendiagramm der Phasenwechsel je Pflanzdurchlauf/Pflanze im aktuellen Monat |
| **Aussaatkalender** | Wochengenauer Anbaukalender für Freilandpflanzen über das ganze Jahr |
| **Saisonübersicht** | 12-Monats-Kachelraster mit Aussaat-, Ernte- und Blüte-Anzahl pro Monat |

!!! note "Keine Wochen- oder Tagesansicht"
    Kamerplanter bietet aktuell keine dedizierte Wochen- oder Tagesansicht. Für einen engen Zeitraum nutzt du am besten die Listenansicht.

---

## Ereignis-Kategorien und Farbkodierung

Jede der elf Ereignis-Kategorien hat eine eigene Farbe für schnelle visuelle Orientierung. Über die Filter-Chips oberhalb des Kalenders blendest du einzelne Kategorien ein oder aus:

| Kategorie | Beschreibung |
|-----------|-------------|
| Training | High-/Low-Stress-Training (HST/LST)-Maßnahmen |
| Schnitt | Rückschnitt, Entlaubung |
| Umtopfen | Umtopf-Termine |
| Düngung | Düngeereignisse |
| Pflanzenschutz | IPM-Inspektionen und Behandlungen |
| Ernte | Geplante und durchgeführte Ernten |
| Wartung | Allgemeine Pflegeaufgaben |
| Phasenwechsel | Geplante oder durchgeführte Phasenwechsel |
| Tankwartung | Wasserwechsel, Kalibrierungen |
| Gießplan-Vorschau | Vorausberechnete Gießtermine aus aktiven Gießplänen |
| Sonstiges | Freie/benutzerdefinierte Ereignisse |

<!-- Quelle: src/frontend/src/pages/kalender/CalendarPage.tsx (ALL_CATEGORIES) -->

---

## Ereignisse filtern

In der Monats-, Listen- und Phasen-Timeline-Ansicht stehen zwei Filter zur Verfügung:

- **Kategorie**: Klicke auf einen Kategorie-Chip, um ihn ein- oder auszublenden. Mehrere Kategorien lassen sich gleichzeitig kombinieren.
- **Pflanze / Durchlauf**: Der Filterbaum am rechten Rand (ab Tablet-Breite) listet alle Pflanzdurchläufe mit ihren Pflanzen zum Ankreuzen.

Für den Aussaatkalender und die Saisonübersicht steht stattdessen ein **Standort**-Filter zur Verfügung.

!!! note "Keine Prioritäts- oder Status-Filter"
    Ein Filter nach Priorität oder nach Status (offen/erledigt/überfällig) existiert im Kalender nicht. Diese Filter findest du stattdessen in der [Aufgaben-Übersicht](tasks.md).

---

## Ereignisse ansehen

Klicke in der Monatsansicht auf ein einzelnes Ereignis, um ein Detail-Popover mit Titel, Kategorie, Datum und Beschreibung zu öffnen. Bei Gießplan-Vorschau-Ereignissen zeigt das Popover zusätzlich Ziel-EC, Ziel-pH und die anzumischenden Dünger; über **Gegossen** bestätigst du den Gießvorgang direkt aus dem Popover heraus.

Klicke auf einen Tag mit mehreren Ereignissen, um alle Ereignisse dieses Tages in einem Tages-Popover zu sehen — Phasenwechsel werden dabei nach Pflanzdurchlauf gruppiert.

Über **Details anzeigen** springst du von einem Ereignis zur zugehörigen Aufgabe oder Pflanze.

!!! note "Kein direktes Abhaken oder Erstellen im Kalender"
    Der Kalender selbst bietet keine Schaltfläche „Erledigt markieren" für normale Aufgaben (das gilt nur für Gießvorschau-Ereignisse) und auch keinen Schnellerstellungs-Dialog für neue Aufgaben. Beides erledigst du in der [Aufgaben-Übersicht](tasks.md).

---

## Phasen-Timeline

Die Phasen-Timeline zeigt für jeden Pflanzdurchlauf und jede Einzelpflanze eine Zeile mit farbigen Balken pro Wachstumsphase im aktuell angezeigten Monat. Balken werden je nach Status unterschiedlich dargestellt (abgeschlossen / aktuell / geplant). Über die Filter **Durchläufe filtern** und **Pflanzen filtern** blendest du einzelne Gruppen aus.

---

## Aussaatkalender (Freiland)

Für Freilandgärtner bietet Kamerplanter einen wochengenauen Aussaatkalender über das ganze Kalenderjahr.

### Aufbau

Jede Zeile zeigt eine Art mit ihren Anbau-Balken über 52 Wochen:

| Balken | Bedeutung |
|--------|-----------|
| Voranzucht | Aussaat drinnen (vor dem letzten Frost) |
| Auspflanzen | Direktsaat oder Auspflanzen ins Beet |
| Wachstum | Zeitraum zwischen Aussaat/Auspflanzen und Ernte/Blüte, automatisch aus Lücken befüllt |
| Ernte | Erntefenster |
| Blüte | Blühfenster (bei Zierpflanzen anstelle von Ernte) |

Über die Kategorie-Chips (z.B. Gemüse, Küchenkraut, Balkonpflanze, Zwiebel-/Knollenpflanze) filterst du die angezeigten Arten. Mit dem Stern-Symbol markierst du Favoriten — die Option **Nur Favoriten** blendet den Rest aus. Über das Lupen-Symbol öffnest du die Art-Detailseite. Eine gestrichelte Linie markiert die **Eisheiligen** (Standard: 15. Mai), ein hervorgehobener Streifen die aktuelle Woche.

<!-- Quelle: src/backend/app/domain/engines/sowing_calendar_engine.py -->

!!! tip "Vorrangregeln der Terminberechnung"
    - Sind für eine Art explizite **Direktsaat-Monate** hinterlegt, haben sie Vorrang vor der Berechnung „Tage nach letztem Frost".
    - Bei **frostempfindlichen** Arten wird der Auspflanz-Termin automatisch nicht vor die Eisheiligen gelegt.
    - Die **Wachstum**-Balken werden automatisch in die Lücke zwischen Aussaat/Auspflanzen und Ernte/Blüte eingefügt, sofern keine expliziten Wachstumsmonate hinterlegt sind.

### Jahr und Standort wählen

Über die Jahresnavigation oben im Kalender wechselst du das angezeigte Kalenderjahr; über den Standort-Filter beschränkst du die Anzeige auf einen Standort.

!!! info "Frostdaten nur über die API konfigurierbar"
    Der letzte Frosttermin und die Eisheiligen werden aktuell **nicht** über ein Formularfeld am Standort gepflegt — es gibt kein entsprechendes Eingabefeld im Standort-Formular. Ohne eigene Angabe verwendet Kamerplanter feste Standardwerte für Mitteleuropa (1. Mai letzter Frost, 15. Mai Eisheilige). Wer eigene Werte hinterlegen möchte, kann das aktuell nur über die technische API tun.

---

## Saisonübersicht

Die Saisonübersicht zeigt ein Kachelraster mit allen zwölf Monaten des gewählten Jahres. Jede Kachel nennt die Anzahl an Aussaat-, Ernte- und Blüh-Ereignissen aus dem Aussaatkalender für diesen Monat; der aktuelle Monat ist hervorgehoben. Ein Klick auf eine Kachel springt in die Monatsansicht für diesen Monat.

!!! note "Aufgaben-Anzahl noch nicht befüllt"
    Die Kachel zeigt zusätzlich ein Feld „Aufgaben" — dieses ist aktuell immer 0, da die zugrunde liegende Aggregation von Aufgaben pro Monat noch nicht angebunden ist.

---

## Kalender in externe Apps exportieren (iCal)

Du kannst deinen Kamerplanter-Kalender in externe Kalender-Apps abonnieren. So erhältst du Erinnerungen auf deinem Smartphone, auch wenn du die Kamerplanter-App nicht geöffnet hast.

!!! note "Nur lesen — keine bidirektionale Synchronisation"
    Der iCal-Feed ist nur lesbar. Änderungen in Google Calendar oder Apple Calendar werden nicht an Kamerplanter zurückgespiegelt. Neue Aufgaben erstellst du weiterhin in Kamerplanter.

### Schritt 1: Kalender-Feed einrichten

1. Öffne den Bereich **iCal-Feeds** unten im Kalender.
2. Klicke auf **Feed erstellen**.
3. Gib dem Feed einen Namen (z.B. „Mein Hauptkalender"). Der Feed übernimmt beim Erstellen deine aktuell aktivierten Kategorie-Filter.

### Schritt 2: Feed-URL kopieren

Nach dem Speichern erscheint der Feed in der Liste mit seiner `webcal://`-URL. Klicke auf **URL kopieren**.

### Schritt 3: In externem Kalender abonnieren

=== "Google Calendar"

    1. Öffne Google Calendar auf dem Desktop.
    2. Links unter "Andere Kalender" klicke auf das Plus-Symbol.
    3. Wähle **Per URL**.
    4. Füge die `webcal://`-URL ein.
    5. Klicke auf **Kalender hinzufügen**.

=== "Apple Calendar (macOS)"

    1. Öffne Apple Calendar.
    2. Klicke auf **Ablage → Neues Kalenderabonnement**.
    3. Füge die `webcal://`-URL ein.
    4. Klicke auf **Abonnieren**.

=== "Thunderbird (Lightning)"

    1. Öffne Thunderbird.
    2. Im Kalender-Tab klicke auf **Neuer Kalender**.
    3. Wähle **Im Netzwerk**.
    4. Wähle **iCalendar (ICS)** und füge die URL ein.
    5. Klicke auf **Weiter** und vergib einen Namen.

=== "Android (Standard-Kalender)"

    1. Installiere eine App wie **ICSx5** aus dem Play Store.
    2. Füge die `webcal://`-URL als neues Abonnement hinzu.

### Feed-Token erneuern

Jeder Feed hat eine geheime, in der URL enthaltene Token-Kennung. Über **Token erneuern** generierst du eine neue Token-Kennung und damit eine neue Feed-URL.

!!! warning "Alter Link wird sofort ungültig"
    Sobald du den Token erneuerst, funktioniert die bisherige `webcal://`-URL nicht mehr — die externe App zeigt einen Fehler statt neuer Ereignisse. Trage die neue URL in jeder App nach, in der du den Feed abonniert hast. Nutze diese Funktion, wenn du einen Feed-Link versehentlich geteilt hast oder den Zugriff eines ehemaligen Mitglieds beenden willst.

### Feed löschen

Feeds können jederzeit unter **iCal-Feeds** gelöscht werden. Beim Löschen wird der Feed-Link ungültig — er muss in der externen App ebenfalls entfernt werden.

!!! info "Ablaufdatum nur über die API"
    Kamerplanter unterstützt intern ein optionales Ablaufdatum für Feeds — nach Ablauf liefert der Feed-Endpunkt einen Fehler (HTTP 410 „Gone") statt Ereignissen. Ein Ablaufdatum lässt sich aktuell nicht über die Oberfläche setzen, nur über die technische API.

---

## Häufige Fragen

??? question "Warum sehe ich eine Aufgabe im Kalender, die ich schon abgehakt habe?"
    Abgehakte Aufgaben werden im Kalender weiterhin angezeigt. Blende sie über die [Aufgaben-Übersicht](tasks.md) mit dem Status-Filter aus.

??? question "Kann ich wiederkehrende Ereignisse anlegen?"
    Ja — direkt beim Erstellen einer Aufgabe über das Feld **Wiederholung** (täglich/wöchentlich/zweiwöchentlich/monatlich), sichtbar ab der Erfahrungsstufe „Fortgeschritten". Zusätzlich erzeugen aktive Pflegeprofile automatisch wiederkehrende Gieß- und Düngeerinnerungen. Beide Quellen erscheinen im Kalender. Mehr dazu: [Aufgaben](tasks.md).

??? question "Wie oft aktualisiert sich der iCal-Feed?"
    Der iCal-Feed wird bei jeder Abfrage durch die externe App in Echtzeit generiert. Die Aktualisierungsfrequenz hängt von der externen Kalender-App ab — Google Calendar aktualisiert ca. alle 24 Stunden, Apple Calendar alle 12 Stunden.

??? question "Kann ich den Kalender auf mehrere Personen im Garten aufteilen?"
    Ja. Du kannst mehrere Feeds mit unterschiedlichen Kategorie-Filtern anlegen und die jeweilige URL an verschiedene Personen weitergeben.

---

## Siehe auch

- [Aufgaben](tasks.md)
- [Pflegeerinnerungen](care-reminders.md)
- [Dashboard](dashboard.md)
- [Pflanzdurchläufe](planting-runs.md)
