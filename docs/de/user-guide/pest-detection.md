# Schädlingserkennung per Foto

Mit der Schädlingserkennung kannst du ein Foto deiner Pflanze aufnehmen und erhalten eine konfidenz-gewichtete **Einschätzung**, ob Schädlinge oder typische Schadbilder erkennbar sind — und welche Schädlinge dahinterstecken könnten. Aus einem Befund kannst du direkt eine Befallskontrolle im [Pflanzenschutz (IPM)](pest-management.md) anlegen.

!!! warning "Einschätzung — keine sichere Bestimmung"
    Die Schädlingserkennung ist ein Hilfsmittel, kein Diagnosegerät. Das System gibt immer einen **Disclaimer** aus. Jedes Ergebnis ist eine Einschätzung auf Basis von Bilddaten — prüfe den Befund bitte selbst, bevor du mit einer Behandlung beginnst. Eine automatische Behandlung erfolgt **niemals**.

!!! note "Optionales Feature — Betreiber-Aktivierung erforderlich"
    Die Schädlingserkennung ist standardmäßig deaktiviert und muss vom Betreiber eingerichtet werden. Ist kein Adapter aktiv, ist der Button „Auf Schädlinge prüfen" ausgeblendet — alle anderen Funktionen laufen uneingeschränkt weiter. **Betreiber** finden die Einrichtungsanleitung im Abschnitt [Schädlingserkennung aktivieren](admin.md#schaedlingserkennung-aktivieren).

!!! note "Nur im Full-Modus verfügbar"
    Die Schädlingserkennung ist an einen angemeldeten Pflanzen-Kontext gebunden. Im **[Light-Modus](light-mode.md)** (anonymer Zugang) ist die Funktion nicht verfügbar — du siehst stattdessen den Hinweis „Bitte anmelden, um die Schädlingserkennung zu nutzen".

---

## Voraussetzungen

- Angemeldetes Benutzerkonto (kein Light-Modus)
- Mindestens eine angelegte Pflanze in deinem Mandanten
- Die Schädlingserkennung muss vom Betreiber aktiviert sein (Adapter konfiguriert)
- Bei Cloud-Erkennung (Kindwise, optional): einmalige Einwilligung für den Zweck `pest_detection_cloud`

---

## Zwei Erkennungsmodi

Das System nutzt zwei sich ergänzende Verfahren, die je nach konfiguriertem Adapter aktiv sind:

| Modus | Wann geeignet | Was wird erkannt |
|-------|--------------|-----------------|
| **Direkt-Detektion** | Du siehst winzige Tiere direkt auf der Pflanze | Schädlinge/Nützlinge als Objekte, mit markierten Fundstellen im Bild |
| **Schadbild / Symptom** | Du siehst Schäden, aber kein Insekt (Gespinste, Honigtau, Saugschäden) | Schadmuster, aus denen der wahrscheinliche Verursacher abgeleitet wird |

!!! tip "Schadbild-Erkennung ist der robustere Einstieg"
    Schädlinge wie Spinnmilben oder Thripse sind oft winzig und auf Fotos kaum zu erkennen. Die Schadbild-Erkennung arbeitet auch dann zuverlässig, wenn das Tier selbst nicht sichtbar ist.

---

## Schädlingsprüfung starten

Die Schädlingsprüfung startest du auf der **Detailseite einer Pflanze**:

### Schritt 1: Pflanze öffnen

1. Öffne das Seitenmenü und klicke auf **Stammdaten** oder **Pflanzdurchläufe**
2. Wähle die Pflanze aus, die du untersuchen möchtest
3. Du befindest dich jetzt auf der Pflanzen-Detailseite

### Schritt 2: Prüfung starten

Klicke auf die Schaltfläche **Auf Schädlinge prüfen** auf der Pflanzen-Detailseite.

!!! note "Button nicht sichtbar?"
    Ist der Button nicht sichtbar, hat der Betreiber deiner Instanz die Schädlingserkennung nicht aktiviert. Wende dich an den Administrator.

### Schritt 3: Foto aufnehmen oder hochladen

Der Dialog „Schädlingsprüfung" öffnet sich. Du hast drei Möglichkeiten:

=== "Kamera (Smartphone)"

    1. Tippe auf **Foto aufnehmen**
    2. Dein Gerät öffnet die Kamera-App
    3. Fotografiere den betroffenen Bereich der Pflanze — gut sichtbare Stellen mit Auffälligkeiten
    4. Bestätige das Foto

=== "Kamera (Webcam, Desktop)"

    1. Klicke auf **Foto aufnehmen**
    2. Dein Browser fragt nach Erlaubnis, die Kamera zu verwenden — bestätige diese
    3. Es öffnet sich eine Live-Vorschau deiner Webcam
    4. Positioniere den betroffenen Bereich im Bild und klicke auf **Aufnehmen**

=== "Datei hochladen"

    1. Klicke auf **Foto hochladen** oder ziehe eine Bilddatei per Drag & Drop in den markierten Bereich
    2. Wähle eine JPEG- oder PNG-Datei (maximal 8 MB)

!!! tip "Tipps für ein aussagekräftiges Foto"
    - Fotografiere den **betroffenen Bereich** direkt: sichtbare Tiere, Gespinste, klebrige Beläge oder Blattverfärbungen
    - Gutes Licht ist entscheidend — Tageslicht oder eine direkte Leuchte nah am Objekt
    - Halte die Kamera ruhig und nah genug heran, damit Einzelheiten sichtbar sind
    - Für winzige Tiere: nutze die Makro-Funktion deines Smartphones oder zoome nah heran

### Schritt 4: Ergebnis abwarten

Die Analyse dauert in der Regel 2–10 Sekunden. Das System zerlegt dein Foto intern in überlappende Kacheln (sogenanntes „Tiling"), um auch winzige Objekte zu erfassen — daher kann die Verarbeitung etwas länger dauern als bei der Pflanzenbestimmung.

---

## Ergebnis verstehen

### Befunde mit Fundstellen

Wurden Schädlinge oder Schadmuster erkannt, siehst du:

- **Markierte Bereiche** im Foto: farbige Rahmen (Direkt-Detektion) oder hervorgehobene Regionen (Schadbild)
- **Name des Schädlings** (Allgemeinname und ggf. Artname)
- **Erkennungsmodus**: „Tier erkannt" oder „Schadbild"
- **Einschätzungsstärke** in Prozent — wie sicher das System ist
- **Mapping zum IPM-System**: wenn der erkannte Schädling in den Pflanzenschutz-Stammdaten bekannt ist, erscheint ein Direktlink sowie der Link **Mehr über diesen Schädling**, der dich zur [Schädlings-Detailseite](pest-detail.md) mit Steckbrief, Referenzbildern und Gegenmaßnahmen führt

!!! warning "Einschätzungsstärke kritisch lesen"
    Unter realen Bedingungen liegen die Erkennungsraten je nach Schädlingsart und Bildqualität bei rund 60–70 %. Das System zeigt die Einschätzungsstärke transparent an. Hohe Werte (>75 %) sprechen für einen klaren Befund; niedrige Werte sollten zur eigenen Sichtprüfung animieren.

### Wenn keine Schädlinge erkannt wurden

Zeigt das System „Keine Schädlinge erkannt", bedeutet das **nicht**, dass die Pflanze befallsfrei ist. Das Foto könnte unscharf sein, der befallene Bereich außerhalb des Bildausschnitts liegen, oder der Schädling zu winzig für die verfügbare Bildauflösung sein.

> Kein Befund ist kein Beweis für Schädlingsfreiheit.

Klicke auf **Neues Foto aufnehmen** und versuche es mit einem klareren Bild oder einem anderen Bildausschnitt.

### Abstention: „Keine sichere Erkennung"

Wenn die Einschätzungsstärke aller gefundenen Hinweise unter der internen Sicherheitsschwelle liegt, zeigt das System:

> „Keine sichere Erkennung — bitte die Pflanze manuell prüfen."

Das ist das **korrekte Verhalten bei Unsicherheit**: das System macht lieber keine Aussage, als eine überkonfidente Fehlaussage zu treffen. In diesem Fall empfiehlt sich eine manuelle Inspektion über das [IPM-System](pest-management.md).

### Nützling erkannt — nicht bekämpfen

Erkennt das System einen **Nützling** (z. B. Marienkäfer-Larve, Florfliege, Raubmilbe), zeigt es den Hinweis:

> „Das ist vermutlich ein Nützling — bitte nicht bekämpfen."

Nützlinge werden **nie** als zu bekämpfender Schädling dargestellt. Das System meldet sie in einer eigenen Kategorie, damit du deine natürlichen Helfer nicht versehentlich eliminierst.

---

## Nächste Schritte nach der Erkennung

### Inspektion anlegen (empfohlen)

Der wichtigste Folgeschritt ist eine manuelle Befallskontrolle im IPM-System. Klicke auf **Inspektion anlegen** unterhalb des Ergebnisses.

Das System legt eine [IPM-Inspektion](pest-management.md) mit dem erkannten Schädling als Vorausfüllung an. Du prüfst die Pflanze dann selbst und bestätigst oder korrigierst den Befund im Inspektionsformular.

!!! danger "Keine automatische Behandlung"
    Die Schädlingserkennung löst **niemals** automatisch eine Behandlung aus. Das Karenz-Gate (gesetzliche Wartefrist zwischen Behandlung und Ernte) bleibt in jedem Fall aktiv. Alle Behandlungsentscheidungen triffst du selbst über das [IPM-System](pest-management.md).

### Feedback geben (Human-in-the-Loop)

Direkt unter dem Ergebnis stehen drei Feedback-Schaltflächen:

| Schaltfläche | Bedeutung |
|-------------|-----------|
| **Stimmt** | Das Ergebnis ist korrekt — du hast den genannten Schädling tatsächlich gefunden |
| **Falsch** | Das Ergebnis ist falsch — du siehst keinen Schädling oder einen anderen |
| **War ein Nützling** | Das als Schädling gemeldete Tier ist tatsächlich ein Nützling |

Dein Feedback verbessert die Erkennungsqualität im Laufe der Zeit und hilft dabei, das Indoor-Schädlings-Modell zu verbessern.

---

## Erkennungsverlauf

Du kannst alle bisherigen Schädlingsprüfungen für eine Pflanze einsehen:

1. Öffne die Pflanzen-Detailseite
2. Wechsle zum Tab **Schädlings-Verlauf** (oder scrolle im Abschnitt „Schädlingserkennung" nach unten)

Der Verlauf zeigt Datum, Erkennungsmodus, Befunde und dein Feedback. **Fotos werden nicht gespeichert** — nur der Fingerabdruck des Bildes (Hash) bleibt als Rückverfolgungsmerkmal, ohne dass das Originalbild wiederhergestellt werden kann.

!!! note "Aufbewahrungsdauer"
    Erkennungseinträge werden nach einer konfigurierbaren Frist automatisch gelöscht (Standard: 90 Tage). Die genaue Frist legt der Betreiber fest.

---

## Datenschutz und Einwilligungen

### Self-Hosted-Erkennung (Standard)

Wenn dein Betreiber ausschließlich die **lokale Schädlingserkennung** aktiviert hat, verlässt dein Foto die Kamerplanter-Instanz **nicht**. Es ist keine gesonderte Einwilligung erforderlich. EXIF-Metadaten (GPS-Koordinaten, Kameramodell) werden vor jeder Verarbeitung entfernt.

### Cloud-Erkennung (Kindwise — optional, opt-in)

Wenn dein Betreiber zusätzlich die **Cloud-Erkennung** (Kindwise) aktiviert hat, ist diese standardmäßig **deaktiviert** und erfordert deine ausdrückliche Einwilligung:

- Beim ersten Klick auf „Auf Schädlinge prüfen" (mit aktivem Cloud-Adapter) erscheint ein Einwilligungs-Dialog
- Ohne deine Zustimmung sendet das System **kein Foto** an einen externen Dienst
- Die Einwilligung ist freiwillig — du kannst sie jederzeit widerrufen

**Was du wissen solltest:**
- Das Foto wird an den Kindwise-Dienst (Brno, Tschechien — EU) übertragen und nach der Analyse verworfen
- EXIF-Daten werden vor der Übertragung zweifach entfernt (Frontend + Backend)
- Der Zweck ist `pest_detection_cloud` und erscheint in deinen Datenschutzeinstellungen

**Einwilligung widerrufen:**

1. Klicke oben rechts auf dein Profilbild
2. Wähle **Konto-Einstellungen** > **Datenschutz**
3. Klicke unter **Einwilligungen** neben **Schädlingserkennung (Cloud)** auf **Widerrufen**

Nach dem Widerruf wird ausschließlich der lokale Adapter verwendet (sofern aktiviert) oder der Button ist ausgeblendet.

---

## Häufige Fragen

??? question "Warum sehe ich keinen Button „Auf Schädlinge prüfen"?"
    Der Button ist ausgeblendet, wenn der Betreiber deiner Kamerplanter-Instanz die Schädlingserkennung nicht aktiviert hat oder kein Adapter konfiguriert ist. Wende dich an den Administrator. Alle anderen Funktionen laufen uneingeschränkt weiter.

??? question "Werden meine Fotos gespeichert?"
    Nein. Das Foto wird ausschließlich zur Analyse genutzt und sofort danach verworfen. Gespeichert wird nur das Erkennungsergebnis und ein anonymer Fingerabdruck des Bildes (SHA-256-Hash) — aus dem das Originalbild nicht wiederhergestellt werden kann.

??? question "Was bedeutet „Keine sichere Erkennung"?"
    Das System hat im Foto Hinweise gefunden, ist sich aber nicht sicher genug, um eine konkrete Aussage zu treffen. Das ist kein Fehler, sondern gewolltes Verhalten (Abstention): lieber keine Aussage als eine falsche. Prüfe die Pflanze selbst oder lege eine manuelle IPM-Inspektion an.

??? question "Das System hat einen Schädling erkannt — muss ich jetzt behandeln?"
    Nein. Das Ergebnis ist eine Einschätzung, kein Behandlungsauftrag. Prüfe die Pflanze zunächst selbst und lege bei Bedarf eine Inspektion über das IPM-System an. Ob und womit behandelt wird, entscheidest allein du — das System schlägt höchstens eine Behandlung vor und beachtet dabei die Karenzzeiten.

??? question "Kann die Erkennung einen Nützling als Schädling melden?"
    Das System hat eine eigene Kategorie für Nützlinge (Marienkäfer, Florfliegen, Raubmilben usw.) und meldet sie explizit mit dem Hinweis „Nützling — nicht bekämpfen". Ein Nützling wird nie in der Kategorie „Schädling" gelistet. Falls du dennoch eine Fehlzuordnung siehst, nutze den Feedback-Button „War ein Nützling" — das verbessert das Modell direkt.

??? question "Wie zuverlässig ist die Erkennung?"
    Unter realen Bedingungen ist die Erkennungsrate deutlich geringer als unter Laborbedingungen. Realistisch sind rund 60–70 % korrekte Erkennung — abhängig von Bildqualität, Schädlingsart und Befall. Das System ist als **Früherkennungs-Hilfsmittel** gedacht, nicht als verlässlicher Einzelnachweis. Ein Befund sollte immer durch eine eigene Sichtprüfung bestätigt werden.

??? question "Was unterscheidet die Schädlingserkennung von der Pflanzenbestimmung?"
    Die [Pflanzenbestimmung per Foto](plant-identification.md) erkennt die **Art** einer unbekannten Pflanze. Die Schädlingserkennung analysiert ein Foto einer **bekannten Pflanze** auf Befall und Schadbilder. Beide Funktionen nutzen unterschiedliche Modelle und Adapter.

??? question "Ich habe die Schädlingserkennung im Light-Modus ausprobiert und sie ist nicht verfügbar — warum?"
    Die Schädlingserkennung benötigt einen angemeldeten Nutzer und einen Pflanzen-Kontext (welche Pflanze wird untersucht?). Der Light-Modus bietet keinen solchen Kontext. Melde dich an, um die Funktion zu nutzen.

---

## Siehe auch

- [Pflanzenschutz (IPM)](pest-management.md) — Inspektionen, Behandlungen, Karenzzeiten
- [Schädlings-Detailseite](pest-detail.md) — Steckbrief, Referenzbilder, Gegenmaßnahmen und Nützlinge pro Schädling
- [Pflanze per Foto identifizieren](plant-identification.md) — Artbestimmung unbekannter Pflanzen
- [Datenschutz & DSGVO](privacy.md) — Einwilligungen und Betroffenenrechte
- [Pflanzenfoto-Galerie](plant-photos.md) — Fotos zur Pflanze speichern
