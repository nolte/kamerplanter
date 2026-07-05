# Wetterquellen je Standort

Für jeden Freiland- oder Gewächshaus-Standort legst du fest, woher Kamerplanter seine Wetterdaten bezieht: von einem öffentlichen Wetterdienst oder aus deiner eigenen Home-Assistant-Installation. Du kannst mehrere Quellen hinterlegen und priorisieren, sodass bei Ausfall der bevorzugten Quelle automatisch eine andere einspringt. <!-- REQ-046 -->

!!! note "Teilweise verfügbar: Vorhersage-Anzeige"
    Die Quellen-Konfiguration, die Verbindungsprüfung und die automatische, priorisierte Datenabholung im Hintergrund sind vollständig umgesetzt. Eine eigene Ansicht, die die abgeholte Vorhersage laufend anzeigt (z. B. im Dashboard-Widget „Wettervorhersage"), gibt es noch nicht — dort findest du aktuell nur einen Link zu dieser Einrichtung. Werte siehst du bereits jetzt über die [Verbindung testen](#quelle-testen)-Funktion. <!-- REQ-046 -->

---

## Voraussetzungen

- Ein Standort vom Typ **Außenbereich** (Freiland) oder **Gewächshaus** — bei Indoor-Standorten (Growzelt, Zimmer, Balkon …) erscheint der Abschnitt „Wetterquelle" nicht, da du dort ohnehin über [Sensoren](sensors.md) oder Home Assistant misst.
- **GPS-Koordinaten** für diesen Standort. Ohne hinterlegte Koordinaten zeigt Kamerplanter stattdessen einen Hinweis, dass zuerst die Koordinaten ergänzt werden müssen.
- Deine Rolle im Mandanten ist **Gärtner** oder **Admin** (siehe [Mandanten & Gärten](tenants.md#rollen-und-berechtigungen)) — als **Beobachter** kannst du die Konfiguration nur ansehen, nicht ändern.
- Für die Home-Assistant-Option zusätzlich: ein hinterlegtes Home-Assistant-Zugangstoken (siehe [Home Assistant Integration](../guides/home-assistant-integration.md#tokens-einrichten)).

!!! info "Für technische Nutzer"
    GPS-Koordinaten sind derzeit nur über die API editierbar — im Standort-Formular gibt es dafür noch kein Eingabefeld. Details dazu unter [Standorte & Substrate](locations-substrates.md#eine-neue-site-anlegen).

---

## Wetterquelle hinzufügen

### Schritt 1: Zum Standort navigieren

Öffne unter **Standorte** deinen Freiland- oder Gewächshaus-Standort. Am Ende der Detailseite findest du den Abschnitt **Wetterquelle**.

### Schritt 2: Quelle hinzufügen öffnen

Klicke auf **Quelle hinzufügen**. Ein Dialog öffnet sich mit einer Auswahl zwischen zwei Arten von Wetterquellen: **Öffentlicher Dienst** und **Home Assistant**.

### Schritt 3a: Öffentlichen Wetterdienst wählen (Standardweg)

Für die meisten Freiland-Gärtner ist ein öffentlicher Wetterdienst der einfachste Weg — er funktioniert sofort, ohne eigene Hardware:

| Wetterdienst | Anmeldung nötig? | Hinweis |
|--------------|:---:|--------|
| **Open-Meteo** | Nein | Empfohlen — kostenlos, weltweit, keine Registrierung nötig. |
| **Deutscher Wetterdienst (DWD)** | Nein | Beste Abdeckung im deutschsprachigen Raum. |
| **OpenWeatherMap** | Ja | Weltweit, benötigt einen eigenen API-Schlüssel. |

Wähle den gewünschten Dienst aus der Liste. Wählst du **OpenWeatherMap**, trägst du zusätzlich deinen persönlichen API-Schlüssel ein (den du kostenlos auf der Website von OpenWeatherMap anlegen kannst).

!!! info "Dein API-Schlüssel bleibt geheim"
    Der OpenWeatherMap-Schlüssel wird verschlüsselt gespeichert und dir später nie im Klartext angezeigt — nur ein Hinweis „Schlüssel hinterlegt" bestätigt, dass er gespeichert ist. Bearbeitest du die Quelle später, lässt du das Feld einfach leer, um den gespeicherten Schlüssel unverändert beizubehalten.

### Schritt 3b: Oder Home Assistant als Quelle nutzen

Hast du bereits Wettersensoren oder eine Wetter-Integration in Home Assistant, kannst du diese stattdessen verwenden. Die Option **Home Assistant** ist nur wählbar, wenn du zuvor ein Home-Assistant-Zugangstoken hinterlegt hast — fehlt es, ist die Option ausgegraut und verlinkt dich direkt zu den passenden Einstellungen.

Wähle anschließend eine der zwei Betriebsarten:

=== "Eine Wetter-Entität"
    Die einfachere Wahl, wenn deine Home-Assistant-Installation bereits eine fertige `weather.*`-Entität liefert (z. B. über die Met.no-Integration). Wähle die passende Entität aus der Liste — Kamerplanter übernimmt daraus Temperatur, Niederschlag und weitere Werte automatisch.

=== "Einzelne Sensoren zuordnen"
    Ordne stattdessen einzelne `sensor.*`-Entitäten den passenden Wetterfeldern zu, gruppiert nach **Temperatur** (Minimum, Maximum, aktuell), **Niederschlag & Wind** (Niederschlag, Windgeschwindigkeit, Windböen) und **weitere Messwerte** (Luftfeuchte, Luftdruck). Du musst nicht jedes Feld zuordnen — mindestens ein zugeordneter Sensor genügt.

!!! tip "Wann welche Betriebsart?"
    Nutze **eine Wetter-Entität**, wenn du sie zur Verfügung hast — sie liefert eine fertige Tagesvorhersage mit einem Klick. Nutze **einzelne Sensoren**, wenn du eigene Wetterstation-Sensoren (z. B. eine private Wetterstation) einbinden möchtest, aber keine vorgefertigte `weather.*`-Entität hast.

### Schritt 4: Quelle testen {#quelle-testen}

Bevor du speicherst, kannst du jede Quelle über das Kolben-Symbol **Quelle testen** prüfen — auch bereits gespeicherte Quellen. Kamerplanter prüft die Erreichbarkeit und zeigt dir, sofern GPS-Koordinaten hinterlegt sind, eine Vorschau der nächsten drei Tage (Minimal-/Maximaltemperatur, Niederschlag) inklusive der [Herkunfts-Kennzeichnung](#herkunft-der-wetterdaten-erkennen). Ist die Quelle nicht erreichbar, erscheint eine Fehlermeldung anstelle der Vorschau.

### Schritt 5: Weitere Quellen hinzufügen und priorisieren

Du kannst beliebig viele Quellen hinterlegen — zum Beispiel Open-Meteo als Hauptquelle und Home Assistant als Ergänzung. Jeder Eintrag zeigt seine Position in der Liste als Nummer (**#1** = höchste Priorität). Über die Pfeil-Symbole **nach oben** und **nach unten** änderst du die Reihenfolge.

**Priorität und Rückfallebene (Fallback) verstehen:** Kamerplanter versucht zuerst die Quelle mit der höchsten Priorität (#1). Ist sie gerade nicht erreichbar, springt automatisch die nächste aktive Quelle in der Liste ein — ohne dass du selbst eingreifen musst. Über den Schalter neben jedem Eintrag kannst du eine Quelle vorübergehend deaktivieren, ohne sie zu löschen.

!!! example "Beispiel: Zwei Quellen als Absicherung"
    Du trägst zuerst **Open-Meteo** ein (Priorität #1) und danach eine **Home-Assistant-Wetterstation** (Priorität #2). Läuft Open-Meteo normal, nutzt Kamerplanter dessen Vorhersage. Ist der Dienst einmal nicht erreichbar, greift automatisch deine Home-Assistant-Quelle.

### Schritt 6: Speichern

Klicke auf **Speichern**, um deine gesamte Quellenliste zu übernehmen. Möchtest du eine bestehende Quelle nachträglich bearbeiten, öffne sie über das Zahnrad-Symbol — beachte dabei, dass sich Art (öffentlich/Home Assistant) und Anbieter nach dem Anlegen nicht mehr ändern lassen. Um zu wechseln, lösche die Quelle über das Papierkorb-Symbol und lege sie neu an.

---

## Herkunft der Wetterdaten erkennen {#herkunft-der-wetterdaten-erkennen}

Bei jedem Wert zeigt dir Kamerplanter, wie dieser zustande gekommen ist:

| Kennzeichnung | Bedeutung |
|---------------|-----------|
| **Vorhersage** | Ein berechneter Erwartungswert für ein zukünftiges Datum — noch keine Messung. |
| **Ist-Wert** | Ein tatsächlich gemessener Wert, zum Beispiel von einem Home-Assistant-Sensor — kein Schätzwert. |
| **Reanalyse** | Historische, aus Wettermodellen abgeleitete Daten der Vergangenheit — weder eine Live-Messung noch eine Vorhersage. |

!!! tip "Warum das wichtig ist"
    Ein Ist-Wert von deinem eigenen Sensor spiegelt exakt die Bedingungen an deinem Standort wider. Eine Vorhersage stammt dagegen von der nächstgelegenen Wetterstation des Dienstes und kann leicht von deinem tatsächlichen Standort abweichen (z. B. bei einer geschützten Lage oder einem Mikroklima).

---

## Attribution der Wetterdaten

Kamerplanter zeigt unterhalb der Quellenliste die Herkunftsnachweise der genutzten Dienste an: Deutscher Wetterdienst (nach der Geodatennutzungsverordnung, GeoNutzV), Open-Meteo (Lizenz CC BY 4.0) sowie OpenWeatherMap gemäß dessen Nutzungsbedingungen.

---

## Häufige Fragen

??? question "Warum ist die Option „Home Assistant" ausgegraut?"
    Home Assistant ist als Wetterquelle nur wählbar, wenn du zuvor ein Home-Assistant-Zugangstoken in deinen Kontoeinstellungen hinterlegt hast. Der Dialog verlinkt dich direkt dorthin. Home Assistant ist optional — alle Wetterfunktionen laufen auch vollständig ohne Home Assistant, allein mit einem öffentlichen Dienst wie Open-Meteo.

??? question "Muss ich Home Assistant nutzen, um Wetterdaten zu bekommen?"
    Nein. Open-Meteo funktioniert ohne Anmeldung, ohne API-Schlüssel und ohne eigene Hardware. Home Assistant ist eine zusätzliche Option für alle, die bereits eine eigene Wetterstation oder Wetter-Integration betreiben.

??? question "Was passiert, wenn keine meiner Quellen erreichbar ist?"
    Dann bleiben für diesen Zeitraum keine neuen Wetterdaten für den Standort verfügbar. Prüfe in diesem Fall über **Quelle testen**, welche Quelle den Fehler verursacht, und aktiviere bei Bedarf eine zusätzliche Rückfallquelle.

??? question "Wo sehe ich die eigentliche Wettervorhersage für meinen Standort?"
    Eine durchgehende Vorhersage-Ansicht ist noch nicht umgesetzt. Aktuell bekommst du über **Quelle testen** eine Vorschau der nächsten drei Tage; das Dashboard-Widget „Wettervorhersage" verlinkt bislang nur auf diese Einrichtungsseite.

??? question "Kann ich denselben Wetterdienst zweimal hinzufügen?"
    Nein, jeder Anbieter lässt sich nur einmal je Standort hinzufügen. Möchtest du zwei unterschiedliche Perspektiven vergleichen, kombiniere stattdessen zum Beispiel einen öffentlichen Dienst mit deiner Home-Assistant-Quelle.

---

## Siehe auch

- [Standorte & Substrate](locations-substrates.md) — Standorte anlegen und GPS-Koordinaten
- [Sensorik und Messdaten](sensors.md) — weitere Datenquellen für Klima- und Substratwerte
- [Home Assistant Integration](../guides/home-assistant-integration.md) — Zugangstoken einrichten
- [Dashboard personalisieren](dashboard-personalization.md) — das Widget „Wettervorhersage"
- [Klimazonen & Winterhärte](../guides/climate-zones.md)
