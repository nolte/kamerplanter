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

## Übersicht der Dashboard-Bereiche

### Aktive Pflanzen und Wachstumsphase

Der obere Bereich zeigt eine Übersicht aller aktiven Pflanzen mit ihrer aktuellen Wachstumsphase. Pflanzen sind farblich nach Phase kodiert:

- Hellgrün: Keimung / Sämling
- Grün: Vegetative Phase
- Violett: Blütephase
- Gelb: Erntephase
- Grau: Ruhephase (Dormanz)

Klicke auf eine Pflanze, um direkt zur Pflanzendetailseite zu gelangen.

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
- VPD-Anzeige mit Zielbereich
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

---

## Siehe auch

- [Dashboard personalisieren](dashboard-personalization.md) — Widgets auswählen, anordnen und konfigurieren
- [Aufgaben](tasks.md)
- [Kalender](calendar.md)
- [Tankmanagement](tanks.md)
- [Sensorik](sensors.md)
- [Wetterquellen je Standort](weather-sources.md) — Quelle für das Widget „Wettervorhersage" einrichten
- [Benachrichtigungen](notifications.md#frost-fruehwarnung) — Frost-Frühwarnung als aktive Benachrichtigung
