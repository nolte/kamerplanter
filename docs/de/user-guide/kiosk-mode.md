# Kiosk-Modus

Der Kiosk-Modus optimiert die Oberfläche für die Bedienung direkt am Standort — im Gewächshaus, im Growraum oder auf dem Balkon. Große Schaltflächen, eine vereinfachte Startseite und ein kontrastreiches Design machen die App auch mit Handschuhen, verschmutzten Händen oder bei direkter Sonneneinstrahlung bedienbar. <!-- UI-NFR-019 -->

---

## Voraussetzungen

- Du bist angemeldet (Full-Modus) oder nutzt eine lokale Instanz im [Light-Modus](light-mode.md).
- Der Kiosk-Modus eignet sich besonders für ein fest installiertes Tablet direkt im Gewächshaus oder Growraum.

---

## Wofür der Kiosk-Modus gedacht ist

In Gewächshaus und Growraum gelten besondere Bedingungen: Erde, Nährlösung und Wasser an den Händen, Handschuhe, die die Touch-Präzision verringern, sowie wechselnde Lichtverhältnisse — von greller Sonne bis dunklen Ecken. Der Kiosk-Modus stellt dafür eine eigene, reduzierte Bedienoberfläche bereit, damit du zentrale Aufgaben direkt vor Ort erledigen kannst, ohne zuerst Hände zu waschen oder Handschuhe auszuziehen.

!!! note "Teilweise verfügbar: Kiosk-Modus"
    Der Kiosk-Modus befindet sich im Ausbau. Diese Seite beschreibt den aktuell verfügbaren Funktionsumfang (Startseite, Aktivierung, kontrastreiche Darstellung, Inaktivitäts-Warnung). Weitere Ausbaustufen sind im Abschnitt [Was noch folgt](#was-noch-folgt) beschrieben.

---

## Kiosk-Modus aktivieren

### Schritt 1: Kontoeinstellungen öffnen

Klicke oben rechts auf dein **Profilbild** bzw. deine Initialen und wähle **Kontoeinstellungen**. Wechsle zum Tab **Kiosk-Modus**.

### Schritt 2: Kiosk-Modus einschalten

Aktiviere den Schalter **Kiosk-Modus aktivieren**. Die App wechselt sofort in den Kiosk-Modus — ein Neuladen der Seite ist nicht nötig. Beim Einschalten aktiviert das System automatisch die kontrastreiche Darstellung (siehe [Kontrastreiche Darstellung](#kontrastreiche-darstellung)).

Über die Schaltfläche **Kiosk-Startseite öffnen** gelangst du direkt zur Startseite unter `/kiosk`.

!!! tip "Einstellung bleibt erhalten"
    Der Kiosk-Modus übersteht ein Neuladen der Seite. Im Light-Modus wird die Einstellung im Browser gespeichert (`localStorage`), im Full-Modus zusätzlich in deinem Konto — sie steht dir dort also auch nach einer Anmeldung auf einem anderen Gerät wieder zur Verfügung, sobald die Serverdaten geladen sind.

---

## Die Kiosk-Startseite

Sobald der Kiosk-Modus aktiv ist, führt dich der permanente **Home**-Button jederzeit zur Kiosk-Startseite (`/kiosk`) zurück. Sie zeigt vier große Kacheln für die wichtigsten Aufgaben sowie eine Status-Übersicht.

### Schnellzugriff-Kacheln

| Kachel | Aktion |
|--------|--------|
| **Pflanze scannen** | Öffnet die Foto-basierte Pflanzenerkennung |
| **Bewässerung erfassen** | Öffnet das Gießprotokoll |
| **Rundgang starten** | Öffnet die Aufgaben-Warteschlange für den nächsten Rundgang |
| **Problem melden** | Öffnet die Schädlings-/Problemerkennung per Foto |

### Aktueller Status

Unterhalb der Kacheln zeigt die Startseite die Anzahl deiner offenen Aufgaben sowie eventuelle Warnungen (z. B. überfällige Aufgaben) auf einen Blick.

---

## Kontrastreiche Darstellung

Die kontrastreiche Darstellung (High-Contrast-Design) verwendet reines Schwarz-Weiß mit besonders starkem Kontrast (WCAG AAA — die höchste Barrierefreiheits-Stufe der Web Content Accessibility Guidelines, mindestens 7:1 Kontrastverhältnis für Text) und verzichtet auf feine Grautöne, Schatten und Farbverläufe. Das verbessert die Lesbarkeit erheblich, etwa bei direkter Sonneneinstrahlung im Gewächshaus.

Sie ist standardmäßig aktiv, sobald du den Kiosk-Modus einschaltest. Du kannst sie aber auch **unabhängig** vom Kiosk-Modus nutzen — zum Beispiel für den Balkon bei hellem Tageslicht: Aktiviere dazu im Tab **Kiosk-Modus** der Kontoeinstellungen separat den Schalter **Kontrastreiches Design verwenden**.

---

## Automatische Inaktivitäts-Warnung

Damit an einer fest installierten Kiosk-Station keine Eingaben eines vorherigen Nutzers offen stehen bleiben, erkennt der Kiosk-Modus Inaktivität automatisch:

1. Nach **120 Sekunden** ohne Berührung erscheint ein großflächiges Warn-Overlay mit der Frage „Noch aktiv?" und einem Countdown.
2. Reagierst du nicht, kehrt die App nach weiteren **30 Sekunden** automatisch zur Kiosk-Startseite zurück.
3. Tippst du auf **Weiter arbeiten**, wird die Warnung geschlossen und der Inaktivitäts-Timer beginnt von vorn.

Jede Berührung des Bildschirms außerhalb der Warnung setzt den Inaktivitäts-Timer ebenfalls zurück.

!!! warning "Warnung lässt sich nicht wegtippen"
    Das Warn-Overlay lässt sich nicht durch Tippen daneben oder mit der Escape-Taste schließen — nur über die Schaltfläche **Weiter arbeiten**. Das verhindert, dass die Warnung versehentlich übersehen wird.

---

## Kiosk-Modus verlassen

Tippe in der Kiosk-Kopfleiste auf **Kiosk verlassen**. Du kehrst zum Dashboard zurück, und der Kiosk-Modus wird deaktiviert (die kontrastreiche Darstellung bleibt erhalten, wenn du sie zuvor separat aktiviert hattest). Alternativ schaltest du den Kiosk-Modus jederzeit über den Tab **Kiosk-Modus** in den Kontoeinstellungen aus.

Solange der Kiosk-Modus aktiv ist, bleiben der Kiosk-Badge und der Home-Button permanent sichtbar — auch wenn du über eine Kachel in einen anderen Bereich der App navigierst.

---

## Was noch folgt

!!! note "Noch nicht implementiert"
    Weitere geplante Ausbaustufen des Kiosk-Modus sind aktuell noch nicht umgesetzt und werden in Zukunft ergänzt: vereinfachte Sub-Formulare mit Schnellauswahl-Kacheln für häufige Messwerte (z. B. Leitfähigkeit (EC), pH-Wert, Temperatur), Touch-Debouncing gegen versehentliche Doppel-Tipps, ein verstärkter Bestätigungsschutz für kritische Aktionen (Long-Press) sowie ein Bildschirmschoner-Modus nach der automatischen Rückkehr zur Startseite. <!-- UI-NFR-019 -->

---

## Häufige Fragen

??? question "Kann ich den Kiosk-Modus auch im Light-Modus nutzen?"
    Ja. Im Light-Modus wird deine Einstellung lokal im Browser des Geräts gespeichert — ideal für ein fest installiertes Tablet, das dauerhaft an einem Standort bleibt.

??? question "Wirkt sich der Kiosk-Modus auf andere Geräte oder Nutzer aus?"
    Im Full-Modus ist die Einstellung an dein Konto gebunden und wird zusätzlich serverseitig gespeichert. Andere Mitglieder deines Gartens sind davon nicht betroffen — jede Person aktiviert den Kiosk-Modus für sich selbst.

??? question "Warum sehe ich weiterhin die reguläre Navigation, wenn ich über eine Kiosk-Kachel navigiere?"
    Manche Kacheln (z. B. „Pflanze scannen") führen dich in den regulären Bereich der App, damit du die volle Funktionalität dieser Seite nutzen kannst. Der Kiosk-Badge und der Home-Button bleiben dabei durchgängig sichtbar, damit du jederzeit zur Kiosk-Startseite zurückfindest.

---

## Siehe auch

- [Light-Modus](light-mode.md)
- [Gießprotokoll](watering-log.md)
- [Pflanze per Foto identifizieren](plant-identification.md)
- [Schädlinge per Foto erkennen](pest-detection.md)
- [Aufgaben](tasks.md)
- [Konto & Anmeldung](account.md)
