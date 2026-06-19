# Pflanze per Foto identifizieren

Mit der Foto-Identifikation kannst du eine unbekannte Pflanze fotografieren und sofort erfahren, um welche Art es sich handelt — ohne botanische Vorkenntnisse. Das System analysiert dein Foto und schlägt die wahrscheinlichsten Arten mit Übereinstimmungswert vor. Du wählst den passenden Vorschlag aus und legst die Pflanze direkt im System an.

!!! note "Optionales Feature — Betreiber-Aktivierung erforderlich"
    Die Foto-Identifikation ist nur verfügbar, wenn der Betreiber deiner Kamerplanter-Instanz einen Pl@ntNet-API-Schlüssel konfiguriert hat. Ist das Feature nicht eingerichtet, sind die Kamera-Schaltflächen ausgeblendet — alle anderen Funktionen laufen uneingeschränkt weiter. **Betreiber** finden die Einrichtungsanleitung im Abschnitt [Pflanzenerkennung per Foto aktivieren](admin.md#pflanzenerkennung-per-foto-aktivieren).

!!! note "Verfügbar in beiden Deployment-Modi"
    Die Foto-Identifikation funktioniert sowohl im **Full-Modus** (mit Benutzerkonten) als auch im **[Light-Modus](light-mode.md)** (anonymer Zugang ohne Login). Der einzige Unterschied liegt im Datenschutz-Consent: Im Full-Modus wird deine Einwilligung als Consent-Record im Backend gespeichert und ist in den Datenschutzeinstellungen widerrufbar. Im Light-Modus wird die Einwilligung **clientseitig im Browser** eingeholt und gespeichert. Die Transparenzinformation (Foto geht an Pl@ntNet/Frankreich, EXIF-Metadaten werden entfernt, keine dauerhafte Speicherung) erscheint in beiden Modi vor dem ersten Upload.

---

## Voraussetzungen

- Zugang zu einer Kamerplanter-Instanz, auf der die Foto-Identifikation vom Betreiber eingerichtet wurde
- Einwilligung zur Bildübertragung (beim ersten Aufruf wird ein Einwilligungs-Dialog angezeigt)
- Ein Foto der Pflanze: Webcam, Smartphone-Rückkamera oder eine Bilddatei auf deinem Gerät (JPEG oder PNG, maximal 10 MB)

---

## Pflanze per Foto hinzufügen

Du kannst die Foto-Identifikation auf zwei Wegen starten:

**Weg 1 — Stammdaten-Übersicht:**
Öffne die Stammdaten-Übersicht über das Seitenmenü. Neben der Schaltfläche „Neue Pflanze" findest du die Schaltfläche **Per Foto hinzufügen**.

**Weg 2 — Onboarding-Wizard:**
Beim Einrichten deiner ersten Pflanze bietet der Onboarding-Wizard optional den Schritt „Pflanze fotografieren" an. Du kannst diesen Schritt überspringen und die Pflanze manuell anlegen.

---

## Foto aufnehmen oder hochladen

Sobald der Identifikations-Dialog geöffnet ist, hast du drei Möglichkeiten:

=== "Kamera (Smartphone)"

    1. Tippe auf **Foto aufnehmen**
    2. Dein Gerät öffnet die Kamera-App
    3. Fotografiere die Pflanze — am besten ein deutliches Blatt oder die gesamte Pflanze
    4. Bestätige das Foto

=== "Kamera (Webcam, Desktop)"

    1. Klicke auf **Foto aufnehmen**
    2. Dein Browser fragt nach der Erlaubnis, die Kamera zu verwenden — bestätige diese
    3. Es öffnet sich eine Live-Vorschau deiner Webcam
    4. Positioniere die Pflanze im Bild und klicke auf **Aufnehmen**

=== "Datei hochladen"

    1. Klicke auf **Foto hochladen** oder ziehe eine Bilddatei per Drag & Drop in den markierten Bereich
    2. Wähle eine JPEG- oder PNG-Datei (maximal 10 MB)

!!! tip "Tipps für ein gutes Foto"
    - Fotografiere bei gutem Licht — Tageslicht ist ideal
    - Halte die Kamera ruhig, damit das Bild scharf ist
    - Zeige möglichst ein einzelnes, gut sichtbares Blatt oder die Gesamtform der Pflanze
    - Vermeide Hintergründe mit vielen anderen Pflanzen

---

## Pflanzenteil angeben (optional)

Wenn du weißt, was auf dem Foto zu sehen ist, kannst du dem System einen Hinweis geben. Das verbessert die Erkennungsgenauigkeit:

| Auswahl | Beschreibung |
|---------|-------------|
| **Automatisch** | Das System erkennt selbst, was im Bild zu sehen ist (Standard) |
| **Blatt** | Ein einzelnes Blatt |
| **Blüte** | Eine Blume oder Blüte |
| **Frucht** | Eine Frucht oder Beere |
| **Rinde** | Baumrinde |
| **Ganze Pflanze** | Die gesamte Pflanze im Überblick |

!!! note "Anfängermodus"
    Im Anfänger-Modus (Standard für neue Nutzer) ist diese Auswahl ausgeblendet. Das System arbeitet automatisch. Erfahrene Nutzer können die Auswahl in den Kontoeinstellungen einblenden.

---

## Analyseergebnis auswerten

Nach dem Hochladen analysiert das System dein Foto — das dauert in der Regel 2–5 Sekunden. Anschließend siehst du eine Liste mit bis zu fünf Vorschlägen:

Jeder Vorschlag zeigt:

- **Wissenschaftlichen Namen** der Art (z. B. *Monstera deliciosa*)
- **Deutschen Allgemeinnamen** (z. B. Fensterblatt)
- **Übereinstimmung in Prozent** — wie sicher das System ist
- **Referenzbild** — ein Vergleichsfoto der vorgeschlagenen Art

!!! tip "Wie zuverlässig ist die Erkennung?"
    Eine Übereinstimmung von 85 % oder mehr bedeutet, dass das System sehr sicher ist. Zwischen 50 % und 85 % solltest du das Referenzbild sorgfältig vergleichen. Unter 50 % ist die Erkennung unsicher — nutze in diesem Fall die manuelle Suche.

### Wenn kein Pflanzenmaterial erkannt wurde

Zeigt das System die Meldung „Es konnte kein Pflanzenmaterial im Bild erkannt werden", liegt entweder kein Pflanzenanteil im Foto vor oder das Bild ist zu unscharf. Klicke auf **Neues Foto aufnehmen** und versuche es mit einem klareren Bild.

### Wenn die Erkennung unsicher ist

Sind alle Vorschläge mit weniger als 50 % Übereinstimmung angegeben, zeigt das System einen Hinweis auf die Unsicherheit. Klicke auf **Manuell suchen**, um die Art direkt über den Namen zu finden.

---

## Vorschlag auswählen und Pflanze anlegen

### Art ist bereits in der Datenbank vorhanden

Wenn die erkannte Art im System bekannt ist, erscheint die Schaltfläche **Diese Pflanze anlegen**:

1. Vergleiche das Referenzbild mit deiner Pflanze
2. Klicke auf **Diese Pflanze anlegen**
3. Ein Formular öffnet sich mit der vorausgefüllten Art — gib deiner Pflanze einen Namen (z. B. „Monstera Wohnzimmer")
4. Lege optional Standort und Substrat fest
5. Klicke auf **Anlegen**

Die Pflanze ist jetzt im System und bekommt automatisch passende Pflegevorschläge auf Basis der erkannten Art.

### Art ist noch nicht in der Datenbank

Falls die erkannte Art dem System unbekannt ist, siehst du den Hinweis „Diese Art ist noch nicht im System". Die Schaltfläche lautet dann **Art hinzufügen und Pflanze anlegen**:

1. Klicke auf **Art hinzufügen und Pflanze anlegen**
2. Das System legt die neue Art automatisch an (wissenschaftlicher Name, Familie, Gattung)
3. Lege anschließend deine Pflanze an wie oben beschrieben

!!! note "Neue Arten"
    Neu angelegte Arten haben zunächst nur die Grunddaten (Name, Familie, Gattung). Pflegedaten und weitere Informationen kannst du später in der Stammdaten-Verwaltung ergänzen oder über die externe Datenanreicherung abrufen.

---

## Identifikations-Verlauf

Du kannst alle deine bisherigen Foto-Identifikationen einsehen:

1. Öffne das Seitenmenü und klicke auf **Stammdaten**
2. Klicke oben auf den Tab **Identifikations-Verlauf**

Der Verlauf zeigt Datum, erkannte Art und Übereinstimmungswert jeder Anfrage. Fotos selbst werden nicht gespeichert — nur das Ergebnis und ein Prüfwert des Bildes (kein Rückschluss auf das Original möglich).

!!! note "Aufbewahrungsdauer"
    Verlaufseinträge werden nach 90 Tagen automatisch gelöscht.

---

## Tages-Limit erreicht

Pl@ntNet (Free-Tier) erlaubt maximal 500 Identifikationen pro Tag über die gesamte Instanz. Wenn dieses Limit erreicht ist, erscheint die Meldung:

> „Tages-Limit für Bilderkennung erreicht. Morgen wieder verfügbar."

Das Limit gilt für alle Nutzer der Instanz zusammen und erneuert sich täglich um Mitternacht (UTC). In der Zwischenzeit kannst du Pflanzen wie gewohnt manuell über die Artsuche anlegen.

---

## Einwilligung widerrufen oder zurücksetzen

Wenn du die Einwilligung zur Bildübertragung widerrufst, sind alle Kamera-Schaltflächen sofort ausgeblendet. Dein Identifikations-Verlauf (ohne Fotos) bleibt erhalten.

=== "Full-Modus"

    1. Klicke oben rechts auf dein Profilbild
    2. Wähle **Konto-Einstellungen** > **Datenschutz**
    3. Klicke unter **Einwilligungen** neben **Foto-Identifikation** auf **Widerrufen**

    Der Widerruf wird mit Zeitstempel im Backend gespeichert und gilt sofort. Du kannst die Einwilligung jederzeit erneut erteilen.

=== "Light-Modus"

    Im Light-Modus gibt es keine serverseitigen Datenschutz-Einstellungen. Die Einwilligung ist im **lokalen Browserspeicher** hinterlegt.

    1. Öffne die **Kontoeinstellungen** (oben rechts)
    2. Klicke auf **Foto-Identifikation** > **Einwilligung zurücksetzen**
    3. Beim nächsten Foto-Upload wird der Einwilligungs-Dialog erneut angezeigt

    Alternativ: Wenn du den Browser-Cache oder die Website-Daten löschst, wird die Einwilligung ebenfalls zurückgesetzt.

---

## Self-Hosted-Erkennung mit DINOv2

Alternativ zur Pl@ntNet-Erkennung kann die Bilderkennung **vollständig auf dem eigenen Server** laufen (REQ-029-A): Ein DINOv2-Modell erzeugt aus dem Foto einen Merkmals-Vektor und vergleicht ihn mit lizenzsauberen Referenzbildern der bekannten Arten. Vorteile: keine laufenden Kosten, kein Drittanbieter, **die Fotos verlassen die Instanz nicht**.

**Für dich als Nutzer ändert sich der Bedienablauf nicht** — derselbe Dialog, dieselbe Vorschlagsliste. Sobald der Betreiber die Self-Hosted-Erkennung aktiviert hat, wird sie automatisch bevorzugt; Pl@ntNet dient dann nur noch als Rückfalloption.

**Inbetriebnahme (Betreiber):** Die self-hosted Erkennung läuft in einem eigenen, optionalen Dienst (Inferenz-Service). Die vollständige Anleitung steht unter [Bilderkennung in Betrieb nehmen](../deployment/inference-service.md). Kurzfassung:

1. Dienst starten: `task dev:all` (oder `task dev:recognition` neben dem laufenden KI-Stack)
2. Referenz-Index befüllen: `task recognition:acquire` (lädt lizenzfreie Referenzbilder von GBIF/Wikimedia und indexiert sie)
3. Aktivieren: Backend-Umgebungsvariable `INFERENCE_SERVICE_ENABLED=true`

!!! warning "Reihenfolge beachten"
    Vor dem Befüllen des Index liefert die lokale Erkennung keine Treffer. Aktiviere `INFERENCE_SERVICE_ENABLED=true` erst nach dem Beschaffungslauf — Details auf der [Deployment-Seite](../deployment/inference-service.md).

---

## Referenzbilder und Erkennungsqualität

Das System zeigt dir bei jedem Vorschlag ein **Referenzbild** der erkannten Art zum Vergleich. Diese Referenzbilder stammen aus lizenzierten Botanik-Datenbanken (GBIF, Wikimedia Commons) und werden automatisch beschafft.

!!! note "Erkennbarkeit einzelner Arten"
    Für manche seltenen Arten stehen nur wenige Referenzbilder zur Verfügung. Ist die Erkennbarkeitsschwelle unterschritten, weist das System dich in der Ergebnisliste darauf hin. In diesem Fall liefert die manuelle Suche zuverlässigere Ergebnisse.

Platform-Admins können die Qualität des Referenz-Index verbessern, indem sie ungeeignete Bilder nach einem Sichttest abwählen. Mehr dazu: [Referenzbilder kuratieren](reference-image-curation.md).

---

## Häufige Fragen

??? question "Warum sehe ich keine Kamera-Schaltfläche?"
    Die Foto-Identifikation ist nur verfügbar, wenn der Betreiber deiner Kamerplanter-Instanz einen Pl@ntNet-API-Schlüssel konfiguriert hat. Wende dich an den Administrator deiner Instanz, wenn du diese Funktion nutzen möchtest.

??? question "Werden meine Fotos gespeichert?"
    Nein. Das Foto wird nur zur Analyse an Pl@ntNet übertragen und sofort nach der Antwort verworfen. Es wird weder auf dem Kamerplanter-Server noch bei Pl@ntNet dauerhaft gespeichert. Im System bleibt nur das Ergebnis der Erkennung und ein anonymer Prüfwert des Bildes.

??? question "Was ist Pl@ntNet?"
    Pl@ntNet ist ein von französischen Forschungseinrichtungen (CIRAD, INRAE, INRIA) betriebener Pflanzendienst. Die Identifikation erfolgt über eine API, an die dein Foto zur Analyse gesendet wird. Pl@ntNet speichert das Bild nicht dauerhaft. Die Nutzung erfordert deine ausdrückliche Einwilligung, weil das Foto kurzzeitig die Server des Anbieters in Frankreich (EU) erreicht.

??? question "Was passiert mit dem GPS-Standort in meinem Foto?"
    Vor der Übertragung werden alle EXIF-Metadaten entfernt — dazu gehören GPS-Koordinaten, Kameramodell und Aufnahmezeitpunkt. Pl@ntNet erhält nur die reinen Bilddaten.

??? question "Kann ich eine Pflanzenkrankheit per Foto erkennen?"
    Die Krankheitsdiagnose per Foto ist noch nicht in dieser Phase verfügbar. Für die Diagnose von Schädlingen und Krankheiten nutze bitte die [Pflanzenschutz (IPM)](pest-management.md)-Funktionen mit manueller Inspektion.

??? question "Ich habe die Pflanze falsch identifiziert — was jetzt?"
    Öffne die Pflanze in der Stammdaten-Übersicht und ändere die zugeordnete Art manuell. Gehe auf **Bearbeiten** und wähle eine andere Art aus der Suche.

---

## Siehe auch

- [Stammdaten verwalten](plant-management.md)
- [Onboarding-Wizard](onboarding.md)
- [Datenschutz & DSGVO](privacy.md)
- [Pflanzenschutz (IPM)](pest-management.md)
