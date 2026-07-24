<!-- REQ-030 -->
# Benachrichtigungen

Kamerplanter kann dich über fällige Pflegeaufgaben, Sensor-Alarme, Tankfüllstände und andere wichtige Ereignisse informieren — nicht nur beim Öffnen der App, sondern aktiv über einen oder mehrere Kanäle deiner Wahl. Diese Seite zeigt dir das Benachrichtigungs-Center und wie du die vier verfügbaren Zustellkanäle einrichtest.

---

## Voraussetzungen

- Ein Kamerplanter-Konto mit Zugriff auf **Einstellungen → Benachrichtigungen** (`/settings#notifications`)
- Für den Kanal **Home Assistant**: eine bereits eingerichtete Home-Assistant-Verbindung (siehe [Home Assistant Integration](../guides/home-assistant-integration.md))
- Für den Kanal **Browser-Push**: eine Kamerplanter-Instanz mit aktiviertem Web-Push (siehe [Browser-Push einrichten](../guides/browser-push-setup.md)) — das richtet dein Betreiber einmalig ein
- Für den Kanal **Apprise**: mindestens eine gültige Apprise-URL des gewünschten Diensts (z. B. Telegram, ntfy, Gotify)

---

## Das Benachrichtigungs-Center {#das-benachrichtigungs-center}

Oben rechts in der App zeigt das **Glocken-Symbol** an, wie viele ungelesene Benachrichtigungen es gibt. Ein Klick öffnet die Benachrichtigungsliste als Seitenleiste.

1. **Öffnen** — Klicke auf das Glocken-Symbol. Die Zahl auf dem Symbol aktualisiert sich automatisch etwa jede Minute.
2. **Lesen** — Ein Klick auf eine Benachrichtigung markiert sie als gelesen und öffnet — falls vorhanden — die zugehörige Seite (z. B. die Pflege-Übersicht bei einer Gieß-Erinnerung).
3. **Alle als gelesen markieren** — Über die Schaltfläche **Alle gelesen** oben in der Seitenleiste.
4. **Mehr laden** — Die Liste zeigt zunächst die neuesten 20 Einträge; über **Mehr laden** blätterst du weiter zurück.

Jede Karte ist links farblich nach Dringlichkeit markiert:

| Farbe | Dringlichkeit |
|-------|---------------|
| Rot | Kritisch (z. B. Frostwarnung) |
| Orange | Hoch |
| Blau | Normal |
| Grau | Niedrig |

!!! note "Ungelesen-Zähler unabhängig vom Zustellkanal"
    Eine Benachrichtigung erscheint im Benachrichtigungs-Center, sobald sie erzeugt wurde — unabhängig davon, ob die Zustellung über einen externen Kanal (siehe unten) erfolgreich war. So verpasst du auch dann nichts, wenn z. B. Home Assistant gerade nicht erreichbar ist.

---

## Immer aktuell: Benachrichtigungen folgen ihrer Quelle {#immer-aktuell}

Ändert sich die zugrunde liegende Aufgabe oder Pflegeerinnerung, zieht die passende Benachrichtigung im Center automatisch nach — ohne dass du sie manuell aufräumen musst:

- **Termin verschoben** — verschiebst du eine Aufgabe auf ein neues Datum, zeigt die zugehörige Benachrichtigung sofort das neue Fälligkeitsdatum.
- **Neu zugewiesen** — weist du eine Aufgabe einem anderen Mitglied zu, erhält diese Person eine neue Zuweisungs-Benachrichtigung; deine eigene Fällig-Benachrichtigung für diese Aufgabe verschwindet dabei.
- **Gelöscht** — löschst du eine Aufgabe, verschwindet auch ihre Benachrichtigung aus dem Center.
- **Erledigt** — schließt du eine Aufgabe ab, gilt die zugehörige Benachrichtigung automatisch als erledigt und zählt nicht mehr im Ungelesen-Zähler.
- **Gieß-Intervall geändert** — änderst du das Intervall einer Pflegeerinnerung (z. B. Gießen), aktualisiert sich die bestehende Erinnerungs-Benachrichtigung mit dem neuen Termin; es entsteht keine zweite, doppelte Erinnerung für dieselbe Pflanze und denselben Erinnerungstyp.
- **Pflege bestätigt** — bestätigst du eine Pflegeaufgabe (z. B. über die Pflege-Übersicht), gilt die zugehörige Benachrichtigung ebenfalls sofort als erledigt.

!!! note "Nur das In-App-Center reagiert sofort"
    Diese Synchronisation betrifft das Benachrichtigungs-Center in der App. Bereits über einen externen Kanal (Home Assistant, E-Mail, Browser-Push, Apprise) zugestellte Nachrichten werden nicht nachträglich zurückgerufen oder erneut verschickt — nur die Anzeige im Center und der Ungelesen-Zähler folgen der Änderung sofort. <!-- REQ-030 -->

### Erledigt direkt aus der Benachrichtigung heraus

Bei Pflege-Benachrichtigungen (z. B. einer Gieß-Erinnerung) zeigt die Karte im Benachrichtigungs-Center zusätzlich eine Schaltfläche **Erledigt**. Ein Klick darauf:

1. bestätigt die zugrunde liegende Pflegeaufgabe — genauso, als hättest du sie über die Pflege-Übersicht bestätigt,
2. markiert die Benachrichtigung selbst als gelesen und erledigt, sodass sie sofort aus dem Ungelesen-Zähler verschwindet.

Das spart dir den Umweg über die Pflege-Übersicht: Du bestätigst direkt aus der Benachrichtigung heraus, in einem Schritt.

!!! tip "Fehlschlag wird automatisch rückgängig gemacht"
    Schlägt die Bestätigung fehl (z. B. wegen eines Verbindungsproblems), macht Kamerplanter die Markierung automatisch rückgängig und zeigt eine Fehlermeldung — die Schaltfläche **Erledigt** bleibt dann sichtbar, sodass du es erneut versuchen kannst.

Reine Aufgaben-Fällig- oder Zuweisungs-Benachrichtigungen ohne Pflegebezug zeigen die Schaltfläche **Erledigt** aktuell nicht; du bestätigst sie weiterhin über die Aufgabenliste.

---

## Die vier Zustellkanäle

Öffne **Einstellungen → Benachrichtigungen**, um Kanäle zu aktivieren. Jeder Kanal lässt sich unabhängig ein- und ausschalten. Sind mehrere Kanäle gleichzeitig aktiviert, wird jede Benachrichtigung an **alle** aktivierten Kanäle parallel zugestellt (kein Fallback auf einen "nächsten" Kanal bei Fehlschlag — schlägt ein Kanal fehl, erhalten die übrigen die Nachricht trotzdem).

Der Status-Chip neben jedem Kanal zeigt **Verfügbar** oder **Nicht konfiguriert**, je nachdem, ob der Kanal serverseitig eingerichtet ist.

### Home Assistant

Der empfohlene primäre Kanal für Nutzer mit Smart-Home-Anbindung. Voraussetzung: Dein Betreiber hat die Home-Assistant-Verbindung des Backends konfiguriert (siehe [Umgebungsvariablen](../reference/environment-variables.md#home-assistant-integration-req-005)).

Aktivierbare Optionen:

- **HA Persistent Notifications** — die Meldung erscheint als Banner im Home-Assistant-Frontend (Standard: an)
- **Mobile Push (Companion App)** — sendet an alle in Home Assistant registrierten Companion-App-Geräte (Standard: an)
- **Sprachansage (TTS)** — liest die Nachricht über eine ausgewählte Lautsprecher-Entity vor (z. B. `media_player.kueche`); standardmäßig deaktiviert und erfordert die Angabe der Entity-ID

Zusätzlich feuert Kamerplanter bei jeder Benachrichtigung ein Home-Assistant-Event (z. B. `kamerplanter_care_due`), mit dem du eigene HA-Automationen auslösen kannst — etwa eine Bewässerungsventil-Schaltung bei einer Gieß-Erinnerung.

!!! tip "Mehrere Erinnerungen werden gebündelt"
    Fallen mehrere Pflegeerinnerungen gleichzeitig an, fasst der Home-Assistant-Kanal sie zu einer einzigen Zusammenfassungs-Nachricht zusammen, statt dich mit vielen Einzelmeldungen zu überhäufen.

### E-Mail

Trage deine E-Mail-Adresse ein und wähle den Zustellmodus:

- **Sofort** — jede Benachrichtigung wird einzeln als E-Mail verschickt
- **Tägliche Zusammenfassung** — alle Benachrichtigungen des Tages werden in einer einzigen E-Mail gebündelt

Der Versand erfolgt über den vom Betreiber konfigurierten SMTP-Server (Mailversand-Server, siehe [Umgebungsvariablen — E-Mail](../reference/environment-variables.md#e-mail)). Ist keine SMTP-Verbindung eingerichtet, gibt der Entwicklungsmodus E-Mails nur im Backend-Log aus.

### Browser-Push (PWA)

Aktiviert Web-Push-Benachrichtigungen direkt im Browser oder in der als App installierten PWA (einer als App installierbaren Web-Anwendung) — auch wenn Kamerplanter gerade nicht geöffnet ist. Die Aktivierung erfolgt **pro Gerät**: Klicke auf **Auf diesem Gerät aktivieren** und erlaube die Browser-Berechtigung für Benachrichtigungen.

!!! info "Setup durch den Betreiber erforderlich"
    Browser-Push funktioniert nur, wenn dein Betreiber vorher ein VAPID-Schlüsselpaar (der technische Schlüssel für Web-Push) hinterlegt hat. Zeigt der Kanal **Nicht konfiguriert**, ist das noch nicht geschehen — siehe [Browser-Push einrichten](../guides/browser-push-setup.md).

Wird der Kanal in diesem Browser nicht unterstützt (z. B. älterer Browser) oder hast du Benachrichtigungen zuvor blockiert, zeigt die Seite einen entsprechenden Hinweis anstelle der Aktivieren-Schaltfläche. Über **Deaktivieren** entfernst du die Push-Registrierung dieses Geräts wieder.

### Apprise

Bindet über die Open-Source-Bibliothek [Apprise](https://github.com/caronc/apprise) mehr als 100 Messaging-Dienste an — etwa Telegram, Slack, Discord, ntfy, Gotify oder Pushover. Trage dazu eine oder mehrere **Apprise-URLs** ein (eine pro Zeile), zum Beispiel:

```
tgram://<bot-token>/<chat-id>
slack://<token-a>/<token-b>/<kanal>
gotify://<hostname>/<token>
```

Die genaue URL-Syntax für deinen gewünschten Dienst findest du in der [Apprise-Dokumentation](https://github.com/caronc/apprise/wiki). Kamerplanter selbst benötigt für diesen Kanal keine zusätzliche Konfiguration durch den Betreiber — die Ziel-URLs verwaltest du komplett selbst in deinen Benachrichtigungseinstellungen.

!!! warning "Voraussetzung für Betreiber: Apprise-Paket installieren"
    Der Apprise-Kanal ist serverseitig standardmäßig aktiv, benötigt aber das Python-Paket `apprise`, das nicht automatisch mit dem Backend-Image ausgeliefert wird. Ist es nicht installiert, zeigt der Kanal **Nicht konfiguriert** und Testnachrichten schlagen mit dem Hinweis "apprise package is not installed" fehl. Der Betreiber muss das Paket zusätzlich in das Backend-Image aufnehmen (`pip install apprise`).

---

## Testnachricht senden

Nach dem Aktivieren eines Kanals kannst du direkt in den Benachrichtigungseinstellungen prüfen, ob er funktioniert:

1. Aktiviere den gewünschten Kanal und speichere ggf. die zugehörigen Angaben (E-Mail-Adresse, Apprise-URLs, …).
2. Klicke bei diesem Kanal auf **Test senden**.
3. Eine Erfolgs- oder Fehlermeldung erscheint als kurze Benachrichtigung (Snackbar) am unteren Bildschirmrand.

Die Testnachricht selbst hat die niedrigste Dringlichkeitsstufe und erscheint nicht im Benachrichtigungs-Center.

---

## Ruhezeiten (Quiet Hours) {#ruhezeiten-quiet-hours}

Unter **Ruhezeiten** legst du ein tägliches Zeitfenster fest (Standard: 22:00–07:00), in dem Kamerplanter Benachrichtigungen **nicht über externe Kanäle** zustellt — die Nachricht wird trotzdem erzeugt und erscheint im Benachrichtigungs-Center, nur eben ohne Push, E-Mail, HA-Meldung oder Apprise-Versand während dieses Zeitfensters.

- **Sensor-Alarme** und **Frostwarnungen** ignorieren die Ruhezeiten immer und werden sofort über alle aktivierten Kanäle zugestellt — diese beiden Typen sind fest hinterlegt und nicht abschaltbar.
- Die Zeitzone für die Ruhezeiten ist aktuell fest auf `Europe/Berlin` eingestellt.

!!! warning "Noch nicht implementiert"
    Während der Ruhezeiten zurückgehaltene Benachrichtigungen werden nach Ablauf des Zeitfensters nicht automatisch nachträglich über die externen Kanäle zugestellt. Du siehst sie im Benachrichtigungs-Center, erhältst aber keinen nachträglichen HA-Push, keine E-Mail und keine Apprise-Nachricht dafür. Eine automatische Nachzustellung nach Ende der Ruhezeit wird in einer zukünftigen Version verfügbar sein.

---

## Zusammenfassung & Eskalation

### Zusammenfassung (Batching)

Mehrere gleichzeitig fällige Erinnerungen werden innerhalb eines Sammel-Zeitfensters (Standard: 30 Minuten, einstellbar von 1 bis 120 Minuten) zu einer Nachricht zusammengefasst, statt einzeln zuzustellen.

### Tägliche Zusammenfassung

Aktivierst du die **Tägliche Zusammenfassung**, erhältst du zusätzlich einmal täglich zur eingestellten Uhrzeit eine Übersicht aller anstehenden und überfälligen Pflegeaufgaben über den gewählten Kanal.

### Eskalation bei überfälligem Gießen

Bleibt eine Gieß-Erinnerung unbestätigt, wiederholt Kamerplanter sie mit steigender Dringlichkeit:

| Zeitpunkt | Dringlichkeit |
|-----------|---------------|
| +2 Tage überfällig | Hoch |
| +4 Tage überfällig | Kritisch |
| +7 Tage überfällig | Kritisch (letzte Erinnerung) |

Diese Eskalationstage sind fest vorgegeben und aktuell nicht individuell einstellbar; du kannst die Eskalation für Gieß-Erinnerungen aber komplett ein- oder ausschalten. Für andere Erinnerungstypen (Düngen, Umtopfen, Schädlingskontrolle) gibt es keine Eskalation.

---

## Frost-Frühwarnung {#frost-fruehwarnung}

Für deine Freiland- und Gewächshaus-Standorte prüft Kamerplanter einmal täglich die aktuelle Wettervorhersage und informiert dich proaktiv, wenn eine Frostnacht bevorsteht — bevor die Temperatur tatsächlich fällt. Die Benachrichtigung nennt den Standort, das erwartete Datum und die voraussichtliche Minimaltemperatur.

- **Dringlichkeit:** Hoch (orange) — sie erscheint wie jede andere Benachrichtigung im [Benachrichtigungs-Center](#das-benachrichtigungs-center) und wird über alle deine aktivierten Zustellkanäle zugestellt.
- **Keine Wiederholungs-Spam:** Für dieselbe Frostnacht an einem Standort erhältst du die Warnung genau **einmal**. Erst ein neuer oder ein noch früherer erwarteter Frosttermin löst eine neue Benachrichtigung aus.
- **Ruhezeiten gelten normal:** Anders als Sensor-Alarme unterliegt diese Frost-Frühwarnung deinen konfigurierten [Ruhezeiten](#ruhezeiten-quiet-hours) — wird sie während deiner Ruhezeiten erzeugt, erscheint sie zunächst nur im Benachrichtigungs-Center.

!!! note "Voraussetzungen"
    Die Frost-Frühwarnung setzt voraus, dass für den betroffenen Standort eine [Wetterquelle eingerichtet](weather-sources.md) ist und GPS-Koordinaten hinterlegt sind. Ohne diese Voraussetzungen bleibt die Warnung aus — dein bestehendes reaktives Frost-Signal aus der aktuell gemessenen Temperatur ist davon nicht betroffen.

Denselben Vorhersage-Zeitraum und dieselbe Minimaltemperatur siehst du außerdem direkt im Dashboard — siehe [Dashboard: Wettervorhersage und Frost-Frühwarnung](dashboard.md#wettervorhersage-und-frost-fruehwarnung).

---

## Häufige Fragen

??? question "Ich habe mehrere Kanäle aktiviert — bekomme ich jede Benachrichtigung mehrfach?"
    Ja, das ist so gewollt: Sind zum Beispiel Home Assistant und E-Mail beide aktiviert, erhältst du jede Benachrichtigung über beide Kanäle. Es gibt aktuell keine "Nur-primärer-Kanal"-Einstellung für einzelne Benachrichtigungstypen in der Oberfläche.

??? question "Kann ich für bestimmte Benachrichtigungstypen einen anderen Kanal wählen als für andere?"
    Nein, noch nicht über die Oberfläche. Du aktivierst Kanäle global für alle Benachrichtigungstypen. Eine feinere Steuerung pro Benachrichtigungstyp ist im Datenmodell vorbereitet, aber noch nicht in den Benachrichtigungseinstellungen bedienbar.

??? question "Warum zeigt Home Assistant 'Nicht konfiguriert', obwohl ich HA nutze?"
    Der Kanal prüft die Backend-Konfiguration der Home-Assistant-Verbindung deines Betreibers, nicht deine persönliche HA-Instanz. Wende dich an deinen Betreiber, falls diese Verbindung noch fehlt.

??? question "Ich sehe eine Benachrichtigung im Center, aber es kam keine Push-Nachricht an — warum?"
    Prüfe zuerst, ob die Nachricht während deiner konfigurierten Ruhezeiten erzeugt wurde (siehe oben) — dann wird sie bewusst nur im Center angezeigt. Prüfe andernfalls den Status-Chip des jeweiligen Kanals und sende eine Testnachricht.

---

## Siehe auch

- [Pflegeerinnerungen](care-reminders.md) — häufigste Quelle für Benachrichtigungen
- [Wetterquellen je Standort](weather-sources.md) — Voraussetzung für die Frost-Frühwarnung
- [Dashboard: Wettervorhersage und Frost-Frühwarnung](dashboard.md#wettervorhersage-und-frost-fruehwarnung)
- [Browser-Push einrichten](../guides/browser-push-setup.md) — VAPID-Setup für den PWA-Kanal
- [Home Assistant Integration](../guides/home-assistant-integration.md)
- [Umgebungsvariablen](../reference/environment-variables.md) — Referenz aller Kanal-Konfigurationsvariablen
- [Aufgaben](tasks.md)
