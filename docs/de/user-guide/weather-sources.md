# Wetterquellen je Standort

Für jeden Freiland- oder Gewächshaus-Standort legst du fest, woher Kamerplanter seine Wetterdaten bezieht: von einem öffentlichen Wetterdienst oder aus deiner eigenen Home-Assistant-Installation. Du kannst mehrere Quellen hinterlegen und priorisieren, sodass bei Ausfall der bevorzugten Quelle automatisch eine andere einspringt. <!-- REQ-046 -->

!!! tip "Vorhersage und Frost-Frühwarnung im Dashboard"
    Sobald du hier mindestens eine Quelle eingerichtet hast, zeigt das Dashboard-Widget „Wettervorhersage" die abgeholte Tagesvorhersage direkt an (Minimal-/Maximaltemperatur je Tag, inklusive [Herkunfts-Kennzeichnung](#herkunft-der-wetterdaten-erkennen)) — und warnt dich proaktiv vor, wenn im Vorhersage-Zeitraum eine Frostnacht erwartet wird. Details dazu unter [Dashboard: Wettervorhersage und Frost-Frühwarnung](dashboard.md#wettervorhersage-und-frost-fruehwarnung) und [Benachrichtigungen: Frost-Frühwarnung](notifications.md#frost-fruehwarnung). <!-- REQ-046 -->

---

## Voraussetzungen

- Ein Standort vom **Typ** **Außenbereich** oder **Gewächshaus** — den Typ legst du direkt im Standort-Formular fest (siehe [Standorte & Substrate](locations-substrates.md#grunddaten-ausfüllen)). Bei den übrigen Typen (Innenbereich, Fensterbrett, Balkon, Growzelt) erscheint der Abschnitt „Wetterquelle" nicht, da du dort ohnehin über [Sensoren](sensors.md) oder Home Assistant misst.
- **GPS-Koordinaten** (Breiten- und Längengrad) für diesen Standort — ebenfalls direkt im Standort-Formular editierbar. Fehlen sie, zeigt Kamerplanter stattdessen einen Hinweis, dass zuerst die Koordinaten ergänzt werden müssen.
- Deine Rolle im Mandanten ist **Gärtner** oder **Admin** (siehe [Mandanten & Gärten](tenants.md#rollen-und-berechtigungen)) — als **Beobachter** kannst du die Konfiguration nur ansehen, nicht ändern.
- Für die Home-Assistant-Option zusätzlich: ein hinterlegtes Home-Assistant-Zugangstoken (siehe [Home Assistant Integration](../guides/home-assistant-integration.md#tokens-einrichten)).

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

Wähle den gewünschten Dienst aus der Liste. Wählst du **OpenWeatherMap**, kannst du zusätzlich deinen persönlichen API-Schlüssel eintragen (den du kostenlos auf der Website von OpenWeatherMap anlegen kannst).

!!! info "Dein API-Schlüssel bleibt geheim"
    Der OpenWeatherMap-Schlüssel wird verschlüsselt gespeichert und dir später nie im Klartext angezeigt — nur ein Hinweis „Schlüssel hinterlegt" bestätigt, dass er gespeichert ist. Bearbeitest du die Quelle später, lässt du das Feld einfach leer, um den gespeicherten Schlüssel unverändert beizubehalten.

!!! tip "Kein eigener Schlüssel zur Hand?"
    Lässt du das Schlüssel-Feld leer, funktioniert OpenWeatherMap trotzdem, sofern dein Instanz-Betreiber einen **globalen Fallback-Schlüssel** hinterlegt hat (instanzweite Einstellung unter **Wetterdienste**, siehe [Wetterdienste konfigurieren](weather-services.md)). Ist weder ein eigener noch ein globaler Schlüssel vorhanden, meldet der Verbindungstest einen Fehler.

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

## Klima am Standort

Direkt unterhalb der Wetterquellen zeigt Kamerplanter bei Freiland- und Gewächshaus-Standorten mit hinterlegten GPS-Koordinaten zusätzlich den Abschnitt **Klima am Standort** – zwölf langjährige Monatsmittelwerte (**Klimanormalen**) für Durchschnitts- und Tiefsttemperatur, Niederschlag und Solarstrahlung, dargestellt als Diagramm und als Tabelle. <!-- REQ-041 -->

!!! tip "Was sind Klimanormalen?"
    Eine Klimanormale ist weder ein aktueller Messwert noch eine Vorhersage, sondern ein langjähriger Durchschnitt – also z. B. „im Januar liegt die Durchschnittstemperatur an diesem Ort normalerweise bei -1 °C". Solche Werte helfen bei Entscheidungen, die über den aktuellen Tag hinausgehen: Wann wird an diesem Standort üblicherweise ausgesät? Wie viel Regen fällt im Schnitt in einem trockenen Sommermonat? Übersteht eine Pflanze den Winter an diesem Standort typischerweise im Freien? Klimanormalen sind damit eine **Reanalyse** – siehe die Erklärung dieser Herkunfts-Kennzeichnung oben unter [Herkunft der Wetterdaten erkennen](#herkunft-der-wetterdaten-erkennen).

Datenquelle ist der satelliten- und modellgestützte Reanalyse-Dienst **NASA POWER** der NASA-Erdbeobachtung – wie die anderen öffentlichen Wetterdienste ohne Anmeldung und ohne API-Schlüssel nutzbar. Kamerplanter ruft die Klimanormalen für jeden berechtigten Standort automatisch einmal monatlich im Hintergrund ab; unmittelbar nach dem Anlegen eines Standorts mit GPS-Koordinaten kann es daher einen Moment dauern, bis der Abschnitt erstmals Werte zeigt. Solange keine Daten vorliegen, erscheint an dieser Stelle ein entsprechender Hinweis anstelle von Diagramm und Tabelle.

---

## Attribution der Wetterdaten

Kamerplanter zeigt unterhalb der Quellenliste bzw. unterhalb des Klima-Diagramms die Herkunftsnachweise der genutzten Dienste an: Deutscher Wetterdienst (nach der Geodatennutzungsverordnung, GeoNutzV), Open-Meteo (Lizenz CC BY 4.0), OpenWeatherMap gemäß dessen Nutzungsbedingungen sowie – für die Klimanormalen im Abschnitt „Klima am Standort" – NASA POWER (Lizenz CC BY 4.0).

---

## Häufige Fragen

??? question "Warum ist die Option „Home Assistant" ausgegraut?"
    Home Assistant ist als Wetterquelle nur wählbar, wenn du zuvor ein Home-Assistant-Zugangstoken in deinen Kontoeinstellungen hinterlegt hast. Der Dialog verlinkt dich direkt dorthin. Home Assistant ist optional — alle Wetterfunktionen laufen auch vollständig ohne Home Assistant, allein mit einem öffentlichen Dienst wie Open-Meteo.

??? question "Muss ich Home Assistant nutzen, um Wetterdaten zu bekommen?"
    Nein. Open-Meteo funktioniert ohne Anmeldung, ohne API-Schlüssel und ohne eigene Hardware. Home Assistant ist eine zusätzliche Option für alle, die bereits eine eigene Wetterstation oder Wetter-Integration betreiben.

??? question "Was passiert, wenn keine meiner Quellen erreichbar ist?"
    Dann bleiben für diesen Zeitraum keine neuen Wetterdaten für den Standort verfügbar. Prüfe in diesem Fall über **Quelle testen**, welche Quelle den Fehler verursacht, und aktiviere bei Bedarf eine zusätzliche Rückfallquelle.

??? question "Wo sehe ich die eigentliche Wettervorhersage für meinen Standort?"
    Im Dashboard-Widget „Wettervorhersage" (siehe [Dashboard](dashboard.md#wettervorhersage-und-frost-fruehwarnung)) — es zeigt die Tagesvorhersage (Minimal-/Maximaltemperatur, Herkunfts-Kennzeichnung) deines ersten Freiland- oder Gewächshaus-Standorts mit hinterlegten GPS-Koordinaten sowie eine Frost-Frühwarnung, sobald im Vorhersage-Zeitraum eine Frostnacht erwartet wird. Über **Quelle testen** bekommst du zusätzlich direkt bei der Einrichtung eine Vorschau der nächsten drei Tage.

??? question "Kann ich denselben Wetterdienst zweimal hinzufügen?"
    Nein, jeder Anbieter lässt sich nur einmal je Standort hinzufügen. Möchtest du zwei unterschiedliche Perspektiven vergleichen, kombiniere stattdessen zum Beispiel einen öffentlichen Dienst mit deiner Home-Assistant-Quelle.

??? question "Warum zeigt „Klima am Standort" noch keine Werte?"
    Die Klimanormalen werden automatisch im Hintergrund abgeholt, sobald ein Freiland- oder Gewächshaus-Standort GPS-Koordinaten hat – das kann nach dem Anlegen oder Ergänzen der Koordinaten etwas dauern, da die monatliche Hintergrund-Abholung nicht sofort nach dem Speichern läuft. Prüfe zunächst, ob Koordinaten hinterlegt sind; sind sie es, ist einfach noch kein Durchlauf erfolgt.

??? question "Muss ich den Abschnitt „Klima am Standort" selbst einrichten?"
    Nein. Er erscheint automatisch für jeden Freiland- oder Gewächshaus-Standort mit hinterlegten GPS-Koordinaten – eine eigene Quelle wie bei der Wettervorhersage musst du dafür nicht anlegen.

---

## Siehe auch

- [Standorte & Substrate](locations-substrates.md) — Standort-Typ anlegen und GPS-Koordinaten setzen
- [Wetterdienste konfigurieren](weather-services.md) — instanzweite Vorgaben, globaler OpenWeatherMap-Fallback-Schlüssel (Platform-Admin)
- [Sensorik und Messdaten](sensors.md) — weitere Datenquellen für Klima- und Substratwerte
- [Home Assistant Integration](../guides/home-assistant-integration.md) — Zugangstoken einrichten
- [Dashboard personalisieren](dashboard-personalization.md) — das Widget „Wettervorhersage"
- [Dashboard: Wettervorhersage und Frost-Frühwarnung](dashboard.md#wettervorhersage-und-frost-fruehwarnung)
- [Benachrichtigungen: Frost-Frühwarnung](notifications.md#frost-fruehwarnung)
- [Klimazonen & Winterhärte](../guides/climate-zones.md)
