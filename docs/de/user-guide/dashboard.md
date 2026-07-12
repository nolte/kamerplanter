# Dashboard

!!! info "Teilweise implementiert"
    Das **Pflege-Dashboard** (fällige Aufgaben, Tank-Status) und die **Widget-Personalisierung** (Widgets auswählen, anordnen, in der Größe ändern) sind implementiert. **Erweiterte Analytik** (Ertrags-Trends, Sensor-Heatmaps, Verlaufsdiagramme) sind geplant aber noch nicht umgesetzt. <!-- REQ-009 -->

Das Dashboard ist die Startseite von Kamerplanter. Es gibt dir einen schnellen Überblick über deine Pflanzen, anstehende Aufgaben, aktive Warnungen und wichtige Kennzahlen — alles auf einen Blick, ohne durch einzelne Bereiche navigieren zu müssen. Du kannst die angezeigten Widgets vollständig [selbst zusammenstellen](dashboard-personalization.md).

---

## Voraussetzungen

- Mindestens eine angelegte Pflanze oder ein aktiver Pflanzdurchlauf

---

## Dashboard öffnen

Das Dashboard öffnet sich automatisch nach dem Anmelden. Du erreichst es jederzeit über das Kamerplanter-Logo oder den Navigationspunkt **Dashboard**.

---

## Panels als Navigationsziele nutzen {#panels-als-navigationsziele-nutzen}

Die meisten Panels sind mehr als eine reine Übersicht: Klicke oder tippe außerhalb des [Bearbeiten-Modus](dashboard-personalization.md) auf ein Panel, um direkt zur passenden Detail- oder Listenansicht zu wechseln. Ein kleiner Pfeil (Chevron) am rechten Rand zeigt dir, welche Panels navigierbar sind.

<!-- Quelle: src/frontend/src/config/dashboardWidgetCatalog.ts (Feld navigateTo) -->

| Panel | Führt dich zu |
|-------|----------------|
| Aufgaben heute · Pflegeerinnerungen | [Aufgaben](tasks.md) |
| Aktive Pflanzen · Pflanzenübersicht | [Pflanzenverwaltung](plant-management.md) |
| Tankstatus | [Tankmanagement](tanks.md) |
| Winterschutz | [Überwinterung](overwintering.md) |
| Pflanzenschutz-Warnungen | [Pflanzenschutz](pest-management.md) |
| Ernteprognose | [Erntemanagement](harvest.md) |
| Nächste Termine | [Kalender](calendar.md) |
| Phasen-Zeitleiste | [Phasensteuerung](growth-phases.md) |
| Einrichtungsfortschritt | [Onboarding-Wizard](onboarding.md) |

Zwei Panels bilden bewusst eine Ausnahme: **Schnellzugriff** ist selbst schon eine Kachelübersicht mit eigenen Sprungzielen, und **Wettervorhersage** bleibt eine reine Info-Anzeige ohne eigenes Sprungziel.

!!! tip "Im Bearbeiten-Modus deaktiviert"
    Solange du dein Dashboard im [Bearbeiten-Modus](dashboard-personalization.md) anpasst, sind alle Panels und ihre einzelnen Einträge vorübergehend nicht anklickbar — so verschiebst, änderst und konfigurierst du sie ungestört.

Ein Panel verlinkt dich nur dorthin, wo du auch tatsächlich hinnavigieren darfst: Ist das zum Panel gehörende [Modul ausgeblendet](module-visibility.md), erscheint das zugehörige Widget ohnehin nicht auf deinem Dashboard. Auf dem Smartphone ist das gesamte Panel (bzw. bei den Widgets mit Einzeleinträgen jede einzelne Zeile oder Kachel) dein Tippziel (mindestens 48×48 Pixel groß); am Desktop erreichst du jedes navigierbare Ziel auch per Tastatur (Tab-Taste) und öffnest es mit Enter.

### Direkt zu einzelnen Einträgen springen

Drei Widgets gehen noch einen Schritt weiter als die reine Panel-Navigation: Sie zeigen einzelne Einträge an und verlinken jeden davon direkt auf seine eigene Detailseite.

- **Pflanzenübersicht** (Kachelraster): Tippe oder klicke auf die Kachel einer einzelnen Pflanze, um direkt zu deren Pflanzendetailseite zu gelangen.
- **Aufgaben heute** und **Nächste Termine**: Tippe oder klicke auf eine einzelne Aufgabenzeile, um direkt zu deren Aufgabendetailseite zu gelangen. Der Widget **Aufgaben heute** zeigt dir dabei zusätzlich zu den Zählern jetzt auch die anstehenden Aufgaben als Liste.

Bei diesen drei Widgets öffnet ein Klick auf die freie Fläche des Panels keine Liste mehr — stattdessen führt dich ein eigenes Pfeil-Symbol oben im Widget-Kopf ("Liste öffnen") weiterhin zur zugehörigen Übersichtsseite, während jede Zeile bzw. Kachel dich direkt zum einzelnen Eintrag bringt.

---

## Übersicht der Dashboard-Bereiche

### Pflanzenübersicht

Das Widget **Pflanzenübersicht** zeigt jede deiner aktiven Pflanzen als eigene Karte: Name (oder Sortenname, falls du der Pflanze keinen eigenen Namen gegeben hast), aktuelle Wachstumsphase, Standort und — sofern vorhanden — den nächsten fälligen Termin. Pflanzen mit einer offenen Aufgabe oder Pflegeerinnerung sind zusätzlich klar markiert: ein farbiger Rahmen, ein Hinweis-Symbol und der Text-Badge „Offene Aufgabe" zeigen dir das auch dann, wenn du Farben nicht unterscheiden kannst. <!-- REQ-009 -->

Über die Filterleiste oberhalb der Karten schränkst du die Übersicht ein — nach **Phase**, **Standort** oder danach, ob eine **offene Aufgabe** vorliegt. Mehrere Filter lassen sich kombinieren; leere Ergebnisse zeigen dir einen entsprechenden Hinweis.

Mit dem Umschalter daneben wählst du das Kartenformat:

- **Detailliert** — größere Karten mit Sorte, Standort und nächstem Termin zusätzlich zu Name und Phase
- **Kompakt** — mehr, schmalere Karten mit nur Name, Phase und Aufgaben-Hinweis

Deine Wahl wird in deinem Browser gespeichert und bleibt auch nach einem Neuladen erhalten.

Klicke oder tippe auf eine Karte, um direkt zur Pflanzendetailseite zu gelangen.

### Anstehende Aufgaben

Der Aufgaben-Block zeigt die nächsten fälligen Aufgaben, sortiert nach Dringlichkeit:

- Überfällige Aufgaben erscheinen rot markiert oben in der Liste
- Heute fällige Aufgaben erscheinen orange
- Aufgaben der nächsten 7 Tage erscheinen in der Standardfarbe

Klicke auf eine Aufgabe, um sie zu öffnen oder direkt als erledigt zu markieren.

!!! tip "Schnell abhaken direkt im Dashboard"
    Für einfache Aufgaben wie "Gießen bestätigt" kannst du direkt im Dashboard-Widget auf das Häkchen-Symbol klicken, ohne die Aufgabe zu öffnen.

### Warnungen und Hinweise

Der Warnungs-Block zeigt aktive Meldungen, die Aufmerksamkeit benötigen:

- **Rot (kritisch)**: Ernte blockiert durch Karenzzeit, Sensor ausgefallen, Tank leer
- **Orange (Warnung)**: Überfällige Aufgaben, EC außerhalb Zielbereich, Sonde-Kalibrierung fällig
- **Blau (Info)**: Empfehlungen, Hinweise auf bevorstehende Phasenübergänge

Klicke auf eine Warnung, um direkt zum betroffenen Bereich zu gelangen.

### Schnellübersicht der Tanks

Falls du Tanks konfiguriert hast, zeigt das Dashboard den aktuellen Zustand deiner Tanks:
- Füllstand in % oder Liter
- Aktueller EC-Wert (mit Ampel-Indikator: grün = im Zielbereich, gelb = Abweichung, rot = außerhalb)
- pH-Wert (mit Ampel-Indikator)
- Nächster Wasserwechsel

### Wettervorhersage und Frost-Frühwarnung {#wettervorhersage-und-frost-fruehwarnung}

Hast du für einen deiner Freiland- oder Gewächshaus-Standorte eine [Wetterquelle eingerichtet](weather-sources.md), zeigt dir das Widget **Wettervorhersage** dessen Tagesvorhersage: Minimal- und Maximaltemperatur je Tag, jeweils mit der [Herkunfts-Kennzeichnung](weather-sources.md#herkunft-der-wetterdaten-erkennen) der zugrundeliegenden Quelle (z. B. Open-Meteo, DWD oder deine Home-Assistant-Wetterstation). Betreust du mehrere Standorte, zeigt das Widget den ersten Standort mit hinterlegten GPS-Koordinaten und einer eingerichteten Quelle; der Standortname wird dabei mit angezeigt.

Wird für diesen Standort innerhalb des Vorhersage-Zeitraums eine Frostnacht erwartet, erscheint zusätzlich eine deutlich hervorgehobene **Frost-Frühwarnung** mit dem erwarteten Datum und der voraussichtlichen Minimaltemperatur — schon bevor die Temperatur tatsächlich fällt. Über dieselbe Frostnacht informiert dich Kamerplanter zusätzlich aktiv per [Benachrichtigung](notifications.md#frost-fruehwarnung).

!!! tip "Frühwarnung statt Reaktion"
    Diese Frühwarnung ergänzt das bestehende, reaktive Frost-Signal, das auf einer aktuell gemessenen Temperatur beruht (z. B. über einen Sensor oder Home Assistant) — sie schützt dich zusätzlich davor, eine kommende Frostnacht erst zu bemerken, wenn es bereits zu spät für Schutzmaßnahmen ist.

Ohne eingerichtete Wetterquelle, ohne hinterlegte GPS-Koordinaten für den Standort oder solange dein Betreiber die Wettervorhersage-Funktion nicht aktiviert hat, zeigt das Widget stattdessen einen Hinweis mit einem Link zur Standort-Einrichtung.

---

## Pflegeerinnerungen-Dashboard

Neben dem Hauptdashboard gibt es eine spezielle **Pflege-Ansicht**, die deine Pflanzen nach Dringlichkeit der nächsten Pflegeaktion gruppiert:

- **Sofort**: Pflanzen, deren Pflegeintervall heute abläuft oder überschritten wurde
- **Heute**: Pflanzen, die heute Aufmerksamkeit benötigen
- **Diese Woche**: Pflanzen mit Pflegebedarf in den nächsten 7 Tagen
- **Kein Bedarf**: Pflanzen ohne geplante Pflegeaktion in nächster Zeit

Diese Ansicht ist besonders nützlich für Menschen mit vielen Zimmerpflanzen, die schnell sehen möchten, welche Pflanze heute Wasser oder Dünger braucht.

---

## Dashboard-Anpassung nach Erfahrungsstufe

Das Dashboard passt sich deiner Erfahrungsstufe an (einstellbar unter **Konto → Einstellungen → Erfahrungsstufe**):

**Einsteiger:**
- Vereinfachte Ansicht mit Fokus auf Pflegeaufgaben
- Keine technischen Kennzahlen (EC, VPD)
- Freundliche Formulierungen ("Deine Tomaten brauchen Wasser")

**Mittelstufe:**
- Alle Pflegeaufgaben plus Tankzustand
- EC und pH als Zahlen (ohne Tiefenanalyse)
- Ernte-Prognosen

**Experte:**
- Vollständige Kennzahlen-Ansicht
- Zusätzliche Panels: Tankstatus, Phasen-Zeitleiste, Pflanzenübersicht
- Ertragstrends und Vergleiche

!!! tip "Alle Felder anzeigen"
    In jeder Erfahrungsstufe kannst du mit dem Toggle **"Alle Felder anzeigen"** (oben rechts im Dashboard) vorübergehend zur vollständigen Ansicht wechseln, ohne deine Erfahrungsstufe dauerhaft zu ändern.

---

## Häufige Fragen

??? question "Warum sehe ich keine Sensordaten im Dashboard?"
    Sensordaten erscheinen nur im Dashboard, wenn mindestens ein Sensor konfiguriert und aktiv ist. Falls du keine Smart-Home-Integration hast, nutze manuelle Messungen — diese erscheinen ebenfalls im Dashboard, sind aber mit einem "Manuell"-Label versehen.

??? question "Kann ich das Dashboard anpassen oder Widgets neu anordnen?"
    Ja. Über den Tab **Einstellungen → Dashboard** oder den **Bearbeiten**-Modus direkt auf dem Dashboard kannst du Widgets auswählen, per Drag-and-Drop (oder tastaturbedienbar über Buttons) anordnen und in der Größe ändern. Details dazu findest du unter [Dashboard personalisieren](dashboard-personalization.md).

??? question "Warum erscheinen manche Pflanzen nicht im Dashboard?"
    Das Dashboard zeigt nur **aktive** Pflanzen (nicht abgeschlossene, nicht entfernte). Pflanzen in einem abgeschlossenen Pflanzdurchlauf erscheinen nicht mehr. Falls eine aktive Pflanze nicht erscheint, prüfe, ob sie im richtigen Mandanten ist.

??? question "Warum lässt sich ein Panel nicht anklicken?"
    Entweder befindet sich dein Dashboard gerade im [Bearbeiten-Modus](dashboard-personalization.md) — dort sind alle Panels vorübergehend inaktiv, damit du sie ungestört verschieben oder in der Größe ändern kannst — oder das Panel gehört zu den zwei bewussten Ausnahmen ohne eigenes Sprungziel: **Schnellzugriff** und **Wettervorhersage**.

---

## Siehe auch

- [Dashboard personalisieren](dashboard-personalization.md) — Widgets auswählen, anordnen und konfigurieren
- [Module & Funktionen](module-visibility.md) — steuert, welche Panels (und damit Sprungziele) überhaupt sichtbar sind
- [Aufgaben](tasks.md)
- [Kalender](calendar.md)
- [Tankmanagement](tanks.md)
- [Sensorik](sensors.md)
- [Wetterquellen je Standort](weather-sources.md) — Quelle für das Widget „Wettervorhersage" einrichten
- [Benachrichtigungen](notifications.md#frost-fruehwarnung) — Frost-Frühwarnung als aktive Benachrichtigung
