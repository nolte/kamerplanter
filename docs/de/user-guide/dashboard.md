# Dashboard

!!! info "Teilweise implementiert"
    Das **Pflege-Dashboard** (faellige Aufgaben, Tank-Status) ist implementiert. **Erweiterte Analytik** (Ertrags-Trends, Sensor-Heatmaps, Verlaufsdiagramme) sind geplant aber noch nicht umgesetzt (REQ-009).

Das Dashboard ist die Startseite von Kamerplanter. Es gibt Ihnen einen schnellen Überblick über Ihre Pflanzen, anstehende Aufgaben, aktive Warnungen und wichtige Kennzahlen — alles auf einen Blick, ohne durch einzelne Bereiche navigieren zu müssen.

---

## Voraussetzungen

- Mindestens eine angelegte Pflanze oder ein aktiver Pflanzdurchlauf

---

## Dashboard öffnen

Das Dashboard öffnet sich automatisch nach dem Anmelden. Sie erreichen es jederzeit über das Kamerplanter-Logo oder den Navigationspunkt **Dashboard**.

---

## Übersicht der Dashboard-Bereiche

### Aktive Pflanzen und Wachstumsphase

Der obere Bereich zeigt eine Übersicht aller aktiven Pflanzen mit ihrer aktuellen Wachstumsphase. Pflanzen sind farblich nach Phase kodiert:

- Hellgrün: Keimung / Sämling
- Grün: Vegetative Phase
- Violett: Blütephase
- Gelb: Erntephase
- Grau: Ruhephase (Dormanz)

Klicken Sie auf eine Pflanze, um direkt zur Pflanzendetailseite zu gelangen.

### Anstehende Aufgaben

Der Aufgaben-Block zeigt die nächsten fälligen Aufgaben, sortiert nach Dringlichkeit:

- Überfällige Aufgaben erscheinen rot markiert oben in der Liste
- Heute fällige Aufgaben erscheinen orange
- Aufgaben der nächsten 7 Tage erscheinen in der Standardfarbe

Klicken Sie auf eine Aufgabe, um sie zu öffnen oder direkt als erledigt zu markieren.

!!! tip "Schnell abhaken direkt im Dashboard"
    Für einfache Aufgaben wie "Gießen bestätigt" können Sie direkt im Dashboard-Widget auf das Häkchen-Symbol klicken, ohne die Aufgabe zu öffnen.

### Warnungen und Hinweise

Der Warnungs-Block zeigt aktive Meldungen, die Aufmerksamkeit benötigen:

- **Rot (kritisch)**: Ernte blockiert durch Karenzzeit, Sensor ausgefallen, Tank leer
- **Orange (Warnung)**: Überfällige Aufgaben, EC außerhalb Zielbereich, Sonde-Kalibrierung fällig
- **Blau (Info)**: Empfehlungen, Hinweise auf bevorstehende Phasenübergänge

Klicken Sie auf eine Warnung, um direkt zum betroffenen Bereich zu gelangen.

### Schnellübersicht der Tanks

Falls Sie Tanks konfiguriert haben, zeigt das Dashboard den aktuellen Zustand Ihrer Tanks:
- Füllstand in % oder Liter
- Aktueller EC-Wert (mit Ampel-Indikator: grün = im Zielbereich, gelb = Abweichung, rot = außerhalb)
- pH-Wert (mit Ampel-Indikator)
- Nächster Wasserwechsel

---

## Pflegeerinnerungen-Dashboard

Neben dem Hauptdashboard gibt es eine spezielle **Pflege-Ansicht**, die Ihre Pflanzen nach Dringlichkeit der nächsten Pflegeaktion gruppiert:

- **Sofort**: Pflanzen, deren Pflegeintervall heute abläuft oder überschritten wurde
- **Heute**: Pflanzen, die heute Aufmerksamkeit benötigen
- **Diese Woche**: Pflanzen mit Pflegebedarf in den nächsten 7 Tagen
- **Kein Bedarf**: Pflanzen ohne geplante Pflegeaktion in nächster Zeit

Diese Ansicht ist besonders nützlich für Menschen mit vielen Zimmerpflanzen, die schnell sehen möchten, welche Pflanze heute Wasser oder Dünger braucht.

---

## Dashboard-Anpassung nach Erfahrungsstufe

Das Dashboard passt sich Ihrer Erfahrungsstufe an (einstellbar unter **Konto → Einstellungen → Erfahrungsstufe**):

**Einsteiger:**
- Vereinfachte Ansicht mit Fokus auf Pflegeaufgaben
- Keine technischen Kennzahlen (EC, VPD)
- Freundliche Formulierungen ("Ihre Tomaten brauchen Wasser")

**Mittelstufe:**
- Alle Pflegeaufgaben plus Tankzustand
- EC und pH als Zahlen (ohne Tiefenanalyse)
- Ernte-Prognosen

**Experte:**
- Vollständige Kennzahlen-Ansicht
- VPD-Anzeige mit Zielbereich
- Ertragstrends und Vergleiche

!!! tip "Alle Felder anzeigen"
    In jeder Erfahrungsstufe können Sie mit dem Toggle **"Alle Felder anzeigen"** (oben rechts im Dashboard) vorübergehend zur vollständigen Ansicht wechseln, ohne Ihre Erfahrungsstufe dauerhaft zu ändern.

---

## Häufige Fragen

??? question "Warum sehe ich keine Sensordaten im Dashboard?"
    Sensordaten erscheinen nur im Dashboard, wenn mindestens ein Sensor konfiguriert und aktiv ist. Falls Sie keine Smart-Home-Integration haben, nutzen Sie manuelle Messungen — diese erscheinen ebenfalls im Dashboard, sind aber mit einem "Manuell"-Label versehen.

??? question "Kann ich das Dashboard anpassen oder Widgets neu anordnen?"
    Eine vollständige Drag-and-Drop-Anpassung des Dashboards ist für eine zukünftige Version geplant. Aktuell passt sich das Dashboard automatisch basierend auf Ihrer Erfahrungsstufe und dem Umfang Ihrer Einrichtung an.

??? question "Warum erscheinen manche Pflanzen nicht im Dashboard?"
    Das Dashboard zeigt nur **aktive** Pflanzen (nicht abgeschlossene, nicht entfernte). Pflanzen in einem abgeschlossenen Pflanzdurchlauf erscheinen nicht mehr. Falls eine aktive Pflanze nicht erscheint, prüfen Sie, ob sie im richtigen Mandanten ist.

---

## Siehe auch

- [Aufgaben](tasks.md)
- [Kalender](calendar.md)
- [Tankmanagement](tanks.md)
- [Sensorik](sensors.md)
