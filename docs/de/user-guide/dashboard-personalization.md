<!-- Quelle: src/frontend/src/config/dashboardWidgetCatalog.ts, src/frontend/src/pages/DashboardPage.tsx, src/frontend/src/pages/auth/DashboardSettingsTab.tsx, src/frontend/src/i18n/locales/de/translation.json -->

# Dashboard personalisieren

Du stellst dir dein [Dashboard](dashboard.md) selbst zusammen: Wähle aus einem Katalog von Widgets aus, ordne sie per Drag-and-Drop an, ändere ihre Größe und konfiguriere einzelne Widgets — ganz nach deinem eigenen Bedarf. <!-- REQ-045 -->

---

## Voraussetzungen

- Du bist angemeldet (oder nutzt den [Light-Modus](light-mode.md) auf einem lokalen Gerät).
- Mindestens ein Widget muss für dich verfügbar sein — manche Widgets setzen ein eingeblendetes [Modul](module-visibility.md) voraus.

---

## Zwei Wege zur Personalisierung

Du kannst dein Dashboard auf zwei gleichwertigen Wegen anpassen:

| Fläche | Wo | Besonderheit |
|--------|-----|-------------|
| **Einstellungen → Dashboard** | Kontoeinstellungen, Tab „Dashboard" | Vollständig tastaturbedienbar: Widgets an-/abwählen, per Buttons anordnen und in der Größe ändern, konfigurieren, zurücksetzen |
| **Bearbeiten-Modus** | Direkt auf der Dashboard-Seite | Widgets per Maus oder Touch verschieben und in der Größe ändern (Drag-and-Drop) |

Beide Flächen speichern dieselbe Einstellung — Änderungen aus der einen Fläche siehst du sofort in der anderen.

!!! tip "Direkter Einstieg vom Dashboard aus"
    Klicke im Dashboard-Header auf das Zahnradsymbol **„Widgets verwalten"**, um direkt zum Tab „Dashboard" in den Einstellungen zu springen.

Beim allerersten Besuch des Dashboards zeigt dir ein einmaliger Hinweis, dass du dein Dashboard anpassen kannst. Du kannst ihn über das Schließen-Symbol ausblenden — er erscheint danach nicht mehr.

---

## Widgets in den Einstellungen an- und abwählen

### Schritt 1: Einstellungen öffnen

1. Klicke oben rechts auf dein **Profilbild** oder das Nutzer-Symbol.
2. Wähle **Kontoeinstellungen**.
3. Wechsle zum Tab **Dashboard**.

### Schritt 2: Widget auswählen

Die verfügbaren Widgets sind nach Kategorien gruppiert (siehe [Widget-Katalog](#widget-katalog) unten). Aktiviere den Schalter neben einem Widget, um es auf deinem Dashboard anzuzeigen — deaktiviere ihn, um es wieder zu entfernen.

Nicht verfügbare Widgets erscheinen ausgegraut mit einem Schloss-Symbol und einer Begründung, zum Beispiel „Modul ausgeblendet" oder „Im Light-Modus nicht verfügbar". Ein solches Widget lässt sich erst aktivieren, sobald die Voraussetzung erfüllt ist (z.B. das zugehörige Modul wieder eingeblendet wird).

### Schritt 3: Anordnung und Größe ändern (barrierefrei)

Im Bereich **„Anordnen & Größe"** siehst du deine aktiven Widgets als Liste. Zu jedem Widget stehen Buttons zur Verfügung:

- **Nach oben** / **Nach unten** — verschiebt das Widget in der Reihenfolge
- **Kleiner** / **Größer** — ändert die Größe innerhalb der für das Widget zulässigen Grenzen
- **Konfigurieren** (nur bei Widgets mit eigenen Einstellungen) — öffnet einen Konfigurationsdialog

Diese Buttons sind vollständig mit der Tastatur bedienbar und funktionieren identisch zum Drag-and-Drop im Bearbeiten-Modus.

!!! tip "Änderungen werden sofort gespeichert"
    Jede Änderung im Einstellungen-Tab wird sofort übernommen — es gibt keinen separaten Speichern-Button für diesen Bereich.

### Schritt 4: Für Desktop, Tablet und Mobil getrennt anpassen

Über den Umschalter **„Desktop / Tablet / Mobil"** wählst du, für welche Bildschirmgröße du die Reihenfolge und Größe gerade bearbeitest. So kannst du zum Beispiel auf dem Smartphone eine andere Anordnung festlegen als auf dem großen Bildschirm.

Hast du für ein kleineres Gerät noch nichts angepasst, übernimmt Kamerplanter automatisch die Desktop-Anordnung (einspaltig gestapelt). Mit dem Button **„Für alle übernehmen"** kopierst du die aktuell gewählte Anordnung auf die übrigen Bildschirmgrößen.

---

## Widgets direkt auf dem Dashboard anordnen (Bearbeiten-Modus)

Neben den Einstellungen kannst du dein Dashboard auch direkt anpassen:

### Schritt 1: Bearbeiten-Modus starten

Klicke auf der Dashboard-Seite oben rechts auf **„Bearbeiten"**.

### Schritt 2: Widgets verschieben und in der Größe ändern

- Ziehe ein Widget per Maus oder Touch an eine neue Position.
- Ziehe am Rand eines Widgets, um seine Größe zu ändern.
- Über den Umschalter **Desktop / Tablet / Mobil** legst du fest, für welche Bildschirmgröße die Änderung gilt.

Jedes Widget hat außerdem ein **Menü-Symbol (⋮)** mit denselben Aktionen wie im Einstellungen-Tab: Nach oben/unten, Größer/Kleiner, Konfigurieren, Entfernen. Dieses Menü ist die vollständige Tastaturalternative zum Ziehen mit der Maus.

!!! note "Auf dem Smartphone kein Drag-and-Drop"
    Auf kleinen Bildschirmen (unter 600 Pixel Breite) ist das Ziehen mit dem Finger deaktiviert. Nutze stattdessen das Menü-Symbol an jedem Widget oder passe die mobile Anordnung im Einstellungen-Tab an.

### Schritt 3: Speichern oder verwerfen

Klicke auf **„Speichern"**, um deine Änderungen zu übernehmen, oder auf **„Abbrechen"**, um sie zu verwerfen und zum zuletzt gespeicherten Zustand zurückzukehren.

---

## Widget-Katalog

Kamerplanter bietet aktuell 17 Widgets in vier Kategorien an. Welche Widgets für dich sichtbar sind, hängt von deiner Erfahrungsstufe, den eingeblendeten [Modulen](module-visibility.md) und deinem Betriebsmodus ([Light- oder Full-Modus](light-mode.md)) ab.

<!-- Quelle: src/frontend/src/config/dashboardWidgetCatalog.ts, src/frontend/src/i18n/locales/de/translation.json (dashboard.widgets.*), src/frontend/src/components/dashboard/widgets/WeatherForecastWidget.tsx -->

### Wesentliches

| Widget | Beschreibung |
|--------|-------------|
| Schnellzugriff | Direkte Kacheln zu häufig genutzten Bereichen. |
| Aufgaben heute | Heute fällige und überfällige Aufgaben. |
| Pflegeerinnerungen | Anstehende Pflegeerinnerungen. |
| Aktive Pflanzen | Überblick über deine aktiven Pflanzen. |
| Einrichtungsfortschritt | Dein Fortschritt bei der Ersteinrichtung (erscheint nur, solange das Onboarding nicht abgeschlossen ist). |

### Einblicke

| Widget | Beschreibung |
|--------|-------------|
| Tipp des Tages | Täglicher KI-Pflegetipp für deine Pflanzen. |
| Wettervorhersage | Tagesvorhersage (Minimal-/Maximaltemperatur, Herkunfts-Kennzeichnung) deines Freiland-/Gewächshaus-Standorts, inklusive [Frost-Frühwarnung](dashboard.md#wettervorhersage-und-frost-fruehwarnung), sobald du eine [Wetterquelle eingerichtet](weather-sources.md) hast. |
| Ernteprognose | Voraussichtliche Erntetermine (mit Zeitraum-Konfiguration). |
| Community-Aktivität | Aktivitäten aus deinen Gemeinschaftsgärten. |

### Anbau

| Widget | Beschreibung |
|--------|-------------|
| Winterschutz | Winterhärte-Ampel deiner Pflanzen, ergänzt um den [Saison-Zustand](season-automation.md) deiner Freiland-, Gewächshaus- und Balkon-Standorte (Live-Wetter, Klima-Schätzung oder Kalender) mit Frost-Countdown. |
| Pflanzenschutz-Warnungen | Aktuelle Schädlings- und Krankheitswarnungen. |
| Nächste Termine | Deine nächsten Kalendereinträge. |
| Phasen-Zeitleiste | Wachstumsphasen deiner Pflanzen im Zeitverlauf. |
| Pflanzenübersicht | Kachelübersicht all deiner Pflanzen. |

### Monitoring

| Widget | Beschreibung |
|--------|-------------|
| Sensor-Livewerte | Aktuelle Messwerte deiner Sensoren (mit Standort-Konfiguration). |
| Tankstatus | Füllstände deiner Nährlösungstanks. |
| VPD-Anzeige | Aktuelles Dampfdruckdefizit (VPD). |

!!! example "Beispiel: Widget mit eigener Konfiguration"
    Das Widget **Sensor-Livewerte** bietet einen Konfigurationsdialog, in dem du einen Standort einträgst. Klicke dazu im Einstellungen-Tab (oder im Bearbeiten-Modus-Menü) auf das Zahnrad-Symbol neben dem Widget.

---

## Default-Auswahl je Erfahrungsstufe

Ohne eigene Anpassung zeigt dein Dashboard eine sinnvolle Grundauswahl, die von deiner [Erfahrungsstufe](onboarding.md) abhängt:

- **Einsteiger:** Schnellzugriff, Aufgaben heute, Pflegeerinnerungen, Aktive Pflanzen, Tipp des Tages, Winterschutz, Wettervorhersage, Einrichtungsfortschritt
- **Mittelstufe:** alle Einsteiger-Widgets, zusätzlich Pflanzenschutz-Warnungen, Ernteprognose, Nächste Termine, Community-Aktivität
- **Experte:** alle Mittelstufe-Widgets, zusätzlich Sensor-Livewerte, Tankstatus, Phasen-Zeitleiste, VPD-Anzeige, Pflanzenübersicht

### Auf Standard zurücksetzen

Über den Button **„Auf Standard zurücksetzen"** (im Einstellungen-Tab) verwirfst du deine eigene Anpassung und erhältst wieder die zu deiner Erfahrungsstufe passende Grundauswahl.

---

## Wenn das Dashboard leer ist

Entfernst du alle Widgets, zeigt dir das Dashboard keine leere Seite, sondern einen Hinweis mit zwei Optionen:

- **„Widgets auswählen"** — führt dich direkt zum Einstellungen-Tab
- **„Standard wiederherstellen"** — stellt die Erfahrungsstufen-Grundauswahl wieder her

---

## Persistenz und Mandanten

Dein Dashboard-Layout wird pro Nutzer und pro [Mandant](tenants.md) gespeichert. Wechselst du zwischen mehreren Gärten, sieht jeder Mandant sein eigenes, unabhängiges Layout.

Im [Light-Modus](light-mode.md) — ohne Registrierung — wird dein Layout stattdessen im Browser-Speicher (localStorage) deines Geräts gesichert. Registrierst du dich später, übernimmt Kamerplanter dein lokales Layout einmalig automatisch in deinen Account.

---

## Barrierefreiheit

- Alle Aktionen (Widget an-/abwählen, Anordnen, Größe ändern, Konfigurieren) sind vollständig mit der Tastatur bedienbar — sowohl im Einstellungen-Tab als auch über das Menü-Symbol im Bearbeiten-Modus.
- Änderungen an der Reihenfolge oder Größe werden für Screenreader angesagt (z.B. „Sensor-Livewerte nach oben verschoben").
- Die Reihenfolge, in der Screenreader und Tastaturnavigation die Widgets vorlesen bzw. anspringen, folgt immer der sichtbaren Anordnung auf dem Bildschirm — auf jeder Bildschirmgröße.
- Bevorzugst du reduzierte Bewegungseffekte (Systemeinstellung „Bewegung reduzieren"), verzichtet der Bearbeiten-Modus auf Animationen beim Verschieben.

---

## Häufige Fragen

??? question "Warum sehe ich ein Widget nicht, obwohl ich es aktiviert habe?"
    Prüfe, ob das zugehörige Modul in den [Modul-Einstellungen](module-visibility.md) eingeblendet ist. Ein Widget, dessen Modul ausgeblendet wurde, bleibt in deiner Auswahl gespeichert, wird aber nicht angezeigt, solange das Modul ausgeblendet ist — sobald du es wieder einblendest, erscheint das Widget automatisch wieder.

??? question "Verliere ich meine Anpassung, wenn ich meine Erfahrungsstufe ändere?"
    Nein. Sobald du dein Dashboard einmal selbst angepasst hast, bleibt deine Auswahl unabhängig von der Erfahrungsstufe erhalten. Nur ohne eigene Anpassung folgt das Dashboard automatisch der Grundauswahl deiner aktuellen Erfahrungsstufe.

??? question "Kann ich für jede Bildschirmgröße eine komplett andere Widget-Auswahl treffen?"
    Nein. Welche Widgets angezeigt werden, ist für alle Bildschirmgrößen gleich — nur die Anordnung und Größe der Widgets kannst du für Desktop, Tablet und Mobil getrennt festlegen.

??? question "Sieht ein anderer Nutzer im selben Garten mein Dashboard-Layout?"
    Nein. Dein Dashboard-Layout ist eine persönliche Einstellung pro Nutzer und Mandant. Andere Mitglieder in deinem Garten haben ihre eigene, unabhängige Anordnung.

---

## Siehe auch

- [Dashboard](dashboard.md) — Übersicht über die Dashboard-Bereiche
- [Module & Funktionen](module-visibility.md) — steuert, welche Widgets überhaupt wählbar sind
- [Onboarding-Wizard](onboarding.md) — Erfahrungsstufe einstellen
- [Light-Modus](light-mode.md) — Kamerplanter ohne Login betreiben
- [Mandanten & Gärten](tenants.md) — Mehrere Gärten verwalten
- [Wetterquellen je Standort](weather-sources.md) — Quelle für das Widget „Wettervorhersage" einrichten
