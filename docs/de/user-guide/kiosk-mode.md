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
    Der Kiosk-Modus befindet sich im Ausbau. Diese Seite beschreibt den aktuell verfügbaren Funktionsumfang (Startseite, durchgängige Kiosk-Oberfläche, Aktivierung, kontrastreiche Darstellung, Inaktivitäts-Warnung, Bestätigen durch Gedrückthalten, Schnellauswahl im Gießprotokoll). Weitere Ausbaustufen sind im Abschnitt [Was noch folgt](#was-noch-folgt) beschrieben.

---

## Kiosk-Modus aktivieren

### Schritt 1: Einstellungen öffnen

Klicke oben rechts auf dein **Profilbild** bzw. deine Initialen und wähle **Einstellungen**. Öffne die Gruppe **Anzeige & Verhalten** und dort den Abschnitt **Kiosk-Modus**.

### Schritt 2: Kiosk-Modus einschalten

Aktiviere den Schalter **Kiosk-Modus aktivieren**. Die App wechselt sofort in den Kiosk-Modus — ein Neuladen der Seite ist nicht nötig. Beim Einschalten aktiviert das System automatisch die kontrastreiche Darstellung (siehe [Kontrastreiche Darstellung](#kontrastreiche-darstellung)).

Über die Schaltfläche **Kiosk-Startseite öffnen** gelangst du direkt zur Startseite unter `/kiosk`.

!!! tip "Einstellung bleibt erhalten"
    Der Kiosk-Modus übersteht ein Neuladen der Seite. Im Light-Modus wird die Einstellung im Browser gespeichert (`localStorage`), im Full-Modus zusätzlich in deinem Konto — sie steht dir dort also auch nach einer Anmeldung auf einem anderen Gerät wieder zur Verfügung, sobald die Serverdaten geladen sind.

---

## Die Kiosk-Startseite

Sobald der Kiosk-Modus aktiv ist, führt dich der permanente **Start**-Button jederzeit zur Kiosk-Startseite (`/kiosk`) zurück. Sie zeigt vier große Kacheln für die wichtigsten Aufgaben sowie eine Status-Übersicht.

### Schnellzugriff-Kacheln

| Kachel | Aktion |
|--------|--------|
| **Pflanze bestimmen** | Öffnet die Foto-basierte Pflanzenerkennung |
| **Bewässerung erfassen** | Öffnet das Gießprotokoll |
| **Rundgang starten** | Öffnet die Aufgaben-Warteschlange für den nächsten Rundgang |
| **Problem melden** | Öffnet die Schädlings-/Problemerkennung per Foto |

!!! note "Kein QR-Scanner"
    Die Kachel **Pflanze bestimmen** erkennt eine Pflanze per Foto — sie liest keine QR-Codes. QR-Etiketten öffnest du mit der Kamera-App deines Geräts.

### Aktueller Status

Unterhalb der Kacheln zeigt die Startseite die Anzahl deiner offenen Aufgaben sowie eventuelle Warnungen (z. B. überfällige Aufgaben) auf einen Blick.

---

## Der ganze Kiosk bleibt ein Kiosk

Solange der Kiosk-Modus aktiv ist, bleiben auch die Seiten, die du über eine Kachel öffnest, in der Kiosk-Oberfläche. Statt Menü und Brotkrumen-Navigation siehst du oben eine Leiste mit drei Schaltflächen:

| Schaltfläche | Wirkung |
|--------------|---------|
| **Zurück** | Geht eine Seite zurück. Gibt es keine vorherige Seite, landest du auf der Kiosk-Startseite. |
| **Start** | Springt zur Kiosk-Startseite. |
| **Kiosk verlassen** | Beendet den Kiosk-Modus. Halte die Schaltfläche dafür 2 Sekunden gedrückt. |

Auch die automatische [Inaktivitäts-Warnung](#automatische-inaktivitats-warnung) läuft auf diesen Seiten weiter und bringt dich nach Ablauf zur Kiosk-Startseite zurück.

---

## Kritische Aktionen durch Gedrückthalten bestätigen

Bei Aktionen, die sich nicht rückgängig machen lassen (zum Beispiel Löschen), reicht im Kiosk-Modus kein einzelner Tipp. Halte die Bestätigungsschaltfläche **2 Sekunden** gedrückt. Eine Füllung zeigt den Fortschritt; lässt du vorher los, wird nichts ausgeführt. Der Hinweis „Zum Bestätigen 2 Sekunden gedrückt halten" steht direkt am Dialog. **Abbrechen** und die Bestätigung liegen bewusst weit auseinander, damit du nicht versehentlich die falsche Schaltfläche triffst.

Mit der Tastatur bestätigst du direkt mit der Eingabe- oder Leertaste — ein Gedrückthalten ist dort nicht nötig.

### Doppel-Tipps werden abgefangen

Ein versehentlicher Doppel-Tipp löst nur eine Aktion aus: Berührungen, die kurz nacheinander (innerhalb von etwa 0,3 Sekunden) erfolgen, zählen als eine.

---

## Schnellauswahl im Gießprotokoll

Im Kiosk-Modus bietet das Dialogfenster **Gießvorgang erfassen** für EC und pH der Gießlösung große Auswahlkacheln unter dem Eingabefeld, sodass du keine Zahlen tippen musst:

| Messwert | Kacheln |
|----------|---------|
| EC | 1,0 · 1,5 · 2,0 · 2,5 · 3,0 |
| pH | 5,5 · 5,8 · 6,0 · 6,2 · 6,5 |

Passt keiner der Werte, wähle **Manuell** und gib den Wert frei ein. Die Werte nach dem Gießen und die Ablaufwerte gibst du immer frei ein. Mehr zum Formular findest du im [Gießprotokoll](watering-log.md#gievorgang-manuell-erfassen).

---

## Kontrastreiche Darstellung

Die kontrastreiche Darstellung (High-Contrast-Design) verwendet reines Schwarz-Weiß mit besonders starkem Kontrast (WCAG AAA — die höchste Barrierefreiheits-Stufe der Web Content Accessibility Guidelines, mindestens 7:1 Kontrastverhältnis für Text) und verzichtet auf feine Grautöne, Schatten und Farbverläufe. Das verbessert die Lesbarkeit erheblich, etwa bei direkter Sonneneinstrahlung im Gewächshaus.

Sie ist standardmäßig aktiv, sobald du den Kiosk-Modus einschaltest. Du kannst sie aber auch **unabhängig** vom Kiosk-Modus nutzen — zum Beispiel für den Balkon bei hellem Tageslicht: Aktiviere dazu in den Einstellungen im Abschnitt **Kiosk-Modus** (Gruppe **Anzeige & Verhalten**) separat den Schalter **Kontrastreiches Design verwenden**.

---

## Automatische Inaktivitäts-Warnung

Damit an einer fest installierten Kiosk-Station keine Eingaben eines vorherigen Nutzers offen stehen bleiben, erkennt der Kiosk-Modus Inaktivität automatisch:

1. Nach **120 Sekunden** ohne Berührung erscheint ein großflächiges Warn-Overlay mit der Frage „Noch aktiv?" und einem Countdown.
2. Reagierst du nicht, kehrt die App nach weiteren **30 Sekunden** automatisch zur Kiosk-Startseite zurück. Hast du gerade etwas eingegeben und noch nicht gespeichert, steht in der Warnung, dass diese Eingaben dann verworfen werden.
3. Tippst du auf **Weiter arbeiten**, wird die Warnung geschlossen und der Inaktivitäts-Timer beginnt von vorn.

Jede Berührung des Bildschirms außerhalb der Warnung setzt den Inaktivitäts-Timer ebenfalls zurück, ebenso das Scrollen. Solange ein Foto für die Pflanzen- oder Schädlingserkennung hochgeladen wird, pausiert der Timer.

!!! warning "Warnung lässt sich nicht wegtippen"
    Das Warn-Overlay lässt sich nicht durch Tippen daneben oder mit der Escape-Taste schließen — nur über die Schaltfläche **Weiter arbeiten**. Das verhindert, dass die Warnung versehentlich übersehen wird.

---

## Kiosk-Modus verlassen

Halte in der Kiosk-Kopfleiste **Kiosk verlassen** 2 Sekunden gedrückt; ein kurzes Antippen beendet den Kiosk-Modus nicht, damit ihn niemand versehentlich verlässt. Mit der Tastatur genügt die Eingabe- oder Leertaste. Du kehrst zum Dashboard zurück, und der Kiosk-Modus wird deaktiviert (die kontrastreiche Darstellung bleibt erhalten, wenn du sie zuvor separat aktiviert hattest). Alternativ beendest du ihn über den Tab **Kiosk-Modus** in den Kontoeinstellungen; solange der Kiosk-Modus aktiv ist, steht dort statt des Schalters ebenfalls eine Schaltfläche zum Gedrückthalten.

Solange der Kiosk-Modus aktiv ist, bleiben der Kiosk-Badge und die Schaltflächen **Zurück**, **Start** und **Kiosk verlassen** permanent sichtbar — auch wenn du über eine Kachel in einen anderen Bereich der App navigierst.

---

## Was noch folgt

!!! note "Noch nicht implementiert"
    Weitere geplante Ausbaustufen des Kiosk-Modus sind aktuell noch nicht umgesetzt und werden in Zukunft ergänzt: Schnellauswahl-Kacheln für weitere Messwerte (z. B. Temperatur und Luftfeuchtigkeit) sowie ein Bildschirmschoner-Modus nach der automatischen Rückkehr zur Startseite. <!-- UI-NFR-019 -->

---

## Häufige Fragen

??? question "Kann ich den Kiosk-Modus auch im Light-Modus nutzen?"
    Ja. Im Light-Modus wird deine Einstellung lokal im Browser des Geräts gespeichert — ideal für ein fest installiertes Tablet, das dauerhaft an einem Standort bleibt.

??? question "Wirkt sich der Kiosk-Modus auf andere Geräte oder Nutzer aus?"
    Im Full-Modus ist die Einstellung an dein Konto gebunden und wird zusätzlich serverseitig gespeichert. Andere Mitglieder deines Gartens sind davon nicht betroffen — jede Person aktiviert den Kiosk-Modus für sich selbst.

??? question "Kann ich mit dem Kiosk-Gerät QR-Etiketten scannen?"
    Einen eingebauten QR-Scanner gibt es nicht. Öffne QR-Etiketten mit der Kamera-App deines Geräts; die Kachel **Pflanze bestimmen** arbeitet mit Fotos.

---

## Siehe auch

- [Light-Modus](light-mode.md)
- [Gießprotokoll](watering-log.md)
- [Pflanze per Foto identifizieren](plant-identification.md)
- [Schädlinge per Foto erkennen](pest-detection.md)
- [Aufgaben](tasks.md)
- [Konto & Anmeldung](account.md)
