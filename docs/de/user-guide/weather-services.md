# Wetterdienste konfigurieren

Als Platform-Admin legst du hier die **instanzweiten Standardeinstellungen** für die öffentlichen Wetterdienste fest, die allen Standorten in [Wetterquellen je Standort](weather-sources.md) zur Auswahl stehen: Open-Meteo, der Deutsche Wetterdienst (DWD) und OpenWeatherMap. <!-- REQ-046 -->

!!! note "Nur für Platform-Admins"
    Die Wetterdienste-Einstellungen sind ausschließlich für Nutzer mit der Plattform-Rolle **admin** zugänglich. Im Light-Modus ist die Seite ohne Login direkt erreichbar, da dort der einzige Nutzer der Instanz als Betreiber gilt.

---

## Voraussetzungen

- Plattform-Rolle **admin** (Full-Modus) oder Light-Modus-Betrieb
- Zugang über **Konto-Einstellungen > Wetterdienste**

---

## Wo du die Einstellungen findest

1. Öffne **Konto-Einstellungen** (Klick auf dein Profilbild oben rechts).
2. Wähle den Tab **Wetterdienste** — er erscheint an derselben Stelle wie der Tab **Speicher**, direkt daneben.

Die Seite zeigt drei Bereiche: eine Karte pro Wetterdienst, den globalen OpenWeatherMap-Schlüssel und die allgemeinen Abruf-Einstellungen.

---

## Wetterdienste aktivieren und anpassen

Für jeden der drei Dienste — **Open-Meteo**, **Deutscher Wetterdienst (DWD)** und **OpenWeatherMap** — zeigt eine eigene Karte:

| Feld | Beschreibung |
|------|-------------|
| **Aktiviert** | Schalter, ob der Dienst instanzweit zur Auswahl steht. Deaktivierst du einen Dienst, verschwindet er sofort aus der Auswahlliste im Wetterquelle-Dialog jedes Standorts — bereits eingerichtete Quellen dieses Diensts liefern ab dann keine neuen Daten mehr, bis der Dienst hier wieder aktiviert wird. |
| **Basis-URL (optional)** | Überschreibt die Standard-Adresse des Diensts. Leer lassen, um die Standard-Adresse zu verwenden. |
| **Quellenangabe** | Der Attributions-Text, den Kamerplanter im Wetterquellen-Dialog und auf der Vorschau anzeigt (z. B. die Lizenzangabe von Open-Meteo). |

!!! info "Was ist eine Basis-URL-Override?"
    Die Basis-URL ist die Adresse, unter der Kamerplanter den Wetterdienst im Hintergrund erreicht (z. B. `https://api.open-meteo.com/v1/forecast`). Eine **Override** (Überschreibung) ist nur in Sonderfällen nötig — etwa wenn du eine selbst gehostete Spiegelinstanz eines Dienstes betreibst oder in einer abgeschotteten Netzwerkumgebung einen internen Proxy vorschalten musst. Für den normalen Betrieb lässt du das Feld leer.

### Verbindung testen

Klicke bei einem Dienst auf **Testen**, um die Erreichbarkeit sofort zu prüfen — unabhängig davon, ob bereits ein Standort diesen Dienst nutzt. Kamerplanter fragt testweise Wetterdaten für einen Referenzpunkt ab und zeigt:

- **Dienst erreichbar** — inklusive einer kurzen Vorschau der nächsten drei Tage (Minimal-/Maximaltemperatur, Niederschlag)
- **Dienst nicht erreichbar** — mit einer möglichst konkreten Fehlermeldung (z. B. Zeitüberschreitung oder ein ungültiger Schlüssel)

!!! tip "Wann testen?"
    Teste einen Dienst direkt nach dem Setzen einer Basis-URL-Override oder nach dem Eintragen des globalen OpenWeatherMap-Schlüssels — so erkennst du Tippfehler oder Erreichbarkeitsprobleme sofort, statt erst wenn ein Standort später keine Wetterdaten mehr erhält.

---

## Globaler OpenWeatherMap-Schlüssel (Fallback)

OpenWeatherMap ist der einzige der drei Dienste, der einen persönlichen API-Schlüssel benötigt. Damit nicht jeder Standort zwingend einen eigenen Schlüssel besitzen muss, kannst du hier einen **instanzweiten Fallback-Schlüssel** hinterlegen.

**So funktioniert der Fallback:** Legt ein Nutzer an seinem Standort eine OpenWeatherMap-Quelle an und trägt dort keinen eigenen Schlüssel ein, verwendet Kamerplanter automatisch den hier hinterlegten globalen Schlüssel. Hat ein Standort dagegen einen eigenen Schlüssel gesetzt, hat dieser **Vorrang** vor dem globalen Fallback.

!!! info "Der Schlüssel bleibt geheim"
    Der globale Schlüssel wird verschlüsselt gespeichert und **nie im Klartext angezeigt** — weder in der Oberfläche noch in einer API-Antwort. Ein Statuschip zeigt lediglich „Schlüssel gespeichert" oder „Kein Schlüssel" an. Lässt du das Eingabefeld beim Speichern leer, bleibt ein bereits gespeicherter Schlüssel unverändert erhalten. Über das Augen-Symbol kannst du deine gerade eingegebene Eingabe vor dem Speichern noch einmal im Klartext prüfen.

!!! warning "Kostenkontrolle bei gemeinschaftlich genutzten Instanzen"
    Nutzt du den globalen Schlüssel auf einer Instanz mit mehreren Mandanten (z. B. einem Gemeinschaftsgarten), teilen sich alle Standorte ohne eigenen Schlüssel dasselbe Kontingent bei OpenWeatherMap. Bei vielen aktiven Standorten kann das schneller ausgeschöpft sein als bei einem einzelnen persönlichen Schlüssel. Prüfe bei Bedarf dein Nutzungskontingent direkt im OpenWeatherMap-Konto.

---

## Abruf-Einstellungen

| Feld | Beschreibung |
|------|-------------|
| **Zeitlimit** | Maximale Wartezeit **je Anfrage** an einen Wetterdienst in Sekunden (1–120) — nicht, wie oft Kamerplanter Wetterdaten abruft; das regelt das [Abrufintervall](#abrufintervall-und-manueller-abruf). Antwortet ein Dienst innerhalb dieser Zeit nicht, gilt die Abfrage als fehlgeschlagen und Kamerplanter versucht — sofern konfiguriert — die nächste Quelle in der Prioritätenliste des jeweiligen Standorts. |
| **Standard-Quelle** | Der öffentliche Wetterdienst, den Kamerplanter vorschlägt, wenn ein Standort noch keine eigene Prioritätenliste festgelegt hat. |

---

## Abrufintervall und manueller Abruf {#abrufintervall-und-manueller-abruf}

Kamerplanter holt die Wetterdaten aller Standorte in einem festen **Abrufintervall**: standardmäßig alle **6 Stunden**, also bis zu viermal am Tag. Kürzer als 6 Stunden geht nicht — das schont das Kontingent bezahlter Schlüssel wie OpenWeatherMap. Längere Intervalle (bis zu einer Woche) sind möglich.

- **Wann abgerufen wird:** Kamerplanter prüft zu jeder vollen Stunde, ob seit dem letzten erfolgreichen Abruf das Intervall vergangen ist, und ruft dann ab. Ein geändertes Intervall gilt ab der nächsten vollen Stunde, ohne Neustart.
- **Wenn ein Abruf fehlschlägt:** Ein Abruf gilt als erfolgreich, wenn er mindestens einen Standort mit Wetterdaten versorgt hat. Liefert kein einziger Standort Daten, versucht Kamerplanter es zur nächsten vollen Stunde erneut.
- **Was danach passiert:** Nach jedem erfolgreichen Abruf berechnet Kamerplanter sofort die [Frost-Frühwarnung](notifications.md#frost-fruehwarnung) und den [Bewässerungsbedarf](watering-log.md#vorgeschlagene-giessmenge) neu. Zusätzlich laufen beide einmal täglich am Morgen mit den zuletzt geholten Daten — so bleibt eine nahende Frostnacht auch bei einem langen Intervall oder einem Ausfall der Wetterdienste nicht unbemerkt.
- **Bei einem längeren Ausfall:** Schlagen drei Abrufe hintereinander fehl, schreibt das Backend eine Fehlermeldung (`weather_fetch_outage`) ins Protokoll.
- **Manueller Abruf:** Du kannst einen Abruf über alle Standorte auch sofort anstoßen. Er läuft im Hintergrund; das Ergebnis (Erfolg oder Fehler, Zeitpunkt, Zahl der Standorte und der Standorte mit Fehler) steht danach im Abrufstatus. Ein erfolgreicher manueller Abruf startet das Intervall neu. Läuft gerade ein Abruf, wird ein weiterer abgelehnt; nach einem manuellen Abruf musst du 10 Minuten warten, bevor du den nächsten startest. Ist die Wetterfunktion abgeschaltet, ist auch kein manueller Abruf möglich.
- **Abrufstatus:** Er nennt Zeitpunkt und Ergebnis des letzten erfolgreichen Abrufs und den nächsten geplanten Abruf.

!!! warning "Noch nicht implementiert"
    Eingabefeld für das Abrufintervall, Knopf „Jetzt abrufen" und Statusanzeige werden mit einer der nächsten Versionen auf dieser Seite erscheinen. Bis dahin setzt du das Intervall über die Umgebungsvariable `WEATHER_FETCH_INTERVAL_HOURS` oder als Plattform-Admin direkt über die Schnittstelle (siehe unten).

---

## Für technische Nutzer / Self-Hoster

Alle hier gesetzten Werte überschreiben die entsprechenden Umgebungsvariablen des Backends, solange sie über die Oberfläche gesetzt sind. Ist in der Datenbank kein Wert hinterlegt, gilt der Umgebungsvariablen-Standard:

| Umgebungsvariable | Standard | Entspricht Feld |
|---|---|---|
| `OPEN_METEO_ENABLED` | `true` | Open-Meteo → Aktiviert |
| `OPEN_METEO_BASE_URL` | `https://api.open-meteo.com/v1/forecast` | Open-Meteo → Basis-URL |
| `DWD_ENABLED` | `true` | DWD → Aktiviert |
| `DWD_BASE_URL` | `https://api.brightsky.dev` | DWD → Basis-URL |
| `OPENWEATHERMAP_ENABLED` | `true` | OpenWeatherMap → Aktiviert |
| `OPENWEATHERMAP_BASE_URL` | `https://api.openweathermap.org/data/2.5` | OpenWeatherMap → Basis-URL |
| `WEATHER_FETCH_TIMEOUT_S` | `20` | Zeitlimit |
| `WEATHER_FETCH_INTERVAL_HOURS` | `6` (Minimum `6`, Maximum `168`) | Abrufintervall |
| `WEATHER_DEFAULT_PUBLIC_SOURCE` | `open-meteo` | Standard-Quelle |

Ein per Oberfläche gesetzter Wert wirkt sofort, ohne Backend-Neustart. Eine über den UI-Editor auf leer zurückgesetzte Basis-URL löscht die Datenbank-Override wieder — es gilt danach erneut der Umgebungsvariablen-Standard.

!!! info "SSRF-Schutz bei Basis-URL-Overrides"
    Eine über die Oberfläche gesetzte Basis-URL wird serverseitig geprüft (Schema-Allowlist, keine privaten/internen Adressen), bevor sie gespeichert wird — dieselbe Prüfung wie bei den Speicher- und Home-Assistant-Einstellungen. Das verhindert, dass eine falsch konfigurierte Basis-URL das Backend zu einem unbeabsichtigten internen Ziel umleitet.

**Abrufintervall und manueller Abruf über die Schnittstelle** (nur Plattform-Admin):

| Aufruf | Wirkung |
|---|---|
| `PUT /api/v1/admin/weather-providers` mit `{"fetch_interval_hours": 12}` | Setzt das Abrufintervall; Werte unter `6` oder über `168` lehnt das Backend mit `422` ab. |
| `POST /api/v1/admin/weather-providers/fetch` | Stößt einen Abruf über alle Standorte an und antwortet sofort mit `202`. `409 WEATHER_FETCH_DISABLED` bei `WEATHER_ENABLED=false`; `409`, solange ein Abruf läuft; `429` mit `Retry-After` (Sekunden), solange seit dem letzten manuellen Abruf keine 10 Minuten vergangen sind; `503`, wenn Valkey oder der Task-Broker nicht erreichbar ist. |
| `GET /api/v1/admin/weather-providers/fetch-status` | Letzter Lauf, letzter erfolgreicher Lauf (Auslöser, Zeitpunkte, Standorte, Standorte mit Fehler), nächster geplanter Abruf (leer bei abgeschalteter Wetterfunktion), ob gerade ein Abruf läuft und in wie vielen Sekunden ein manueller Abruf wieder möglich ist. |

---

## Häufige Fragen

??? question "Was passiert mit bestehenden Standort-Wetterquellen, wenn ich einen Dienst hier deaktiviere?"
    Standorte, die diesen Dienst bereits als Wetterquelle eingerichtet haben, erhalten ab der Deaktivierung keine neuen Daten mehr über ihn. Die Konfiguration am Standort bleibt erhalten (nicht gelöscht) — aktivierst du den Dienst hier später wieder, funktioniert die Standort-Quelle ohne weiteres Zutun erneut.

??? question "Warum sehe ich keinen eigenen Schlüssel bei Open-Meteo oder DWD?"
    Open-Meteo und der Deutsche Wetterdienst benötigen keinen API-Schlüssel — beide Dienste sind ohne Anmeldung nutzbar. Nur OpenWeatherMap erfordert einen Schlüssel, entweder pro Standort oder über den globalen Fallback-Schlüssel auf dieser Seite.

??? question "Muss ich einen globalen Schlüssel hinterlegen?"
    Nein. Ohne globalen Schlüssel funktioniert OpenWeatherMap weiterhin — dann muss jeder Standort, der OpenWeatherMap nutzen möchte, seinen eigenen persönlichen Schlüssel im [Wetterquelle-Dialog](weather-sources.md) hinterlegen.

??? question "Wirkt sich eine Basis-URL-Override auf alle Standorte gleichzeitig aus?"
    Ja. Die Basis-URL gilt instanzweit für den jeweiligen Dienst und betrifft alle Standorte, die ihn als Quelle nutzen. Ein einzelner Standort kann die Basis-URL nicht individuell überschreiben.

---

## Siehe auch

- [Wetterquellen je Standort](weather-sources.md) — Wetterquellen pro Standort einrichten und priorisieren
- [Standorte & Substrate](locations-substrates.md) — Standort-Typ und GPS-Koordinaten setzen
- [Plattform-Admin](admin.md) — Gesamtübersicht Admin-Bereich
- [Speicher konfigurieren](object-storage.md) — analoge instanzweite Einstellung für Object Storage
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Variablen-Referenz
