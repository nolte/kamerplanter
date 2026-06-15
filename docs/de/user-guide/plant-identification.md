# Pflanzen-Bilderkennung

Die Pflanzen-Bilderkennung in Kamerplanter ermöglicht es dir, eine unbekannte Pflanze anhand eines Fotos zu identifizieren — vollständig auf deiner eigenen Hardware, ohne Kosten und ohne dass dein Foto die Instanz verlässt.

---

## Voraussetzungen

- Kamerplanter-Instanz mit aktiviertem Inferenz-Service (siehe [Bilderkennung in Betrieb nehmen](../deployment/inference-service.md))
- Mindestens ein angelegtes [Stammdaten-Artprofil](plant-management.md) mit indexierten Referenzbildern
- Kamera, Smartphone-Upload oder Bilddatei (JPEG, PNG; max. 10 MB)

!!! tip "Funktioniert auch ohne Internet"
    Im Primärpfad läuft die Erkennung vollständig lokal. Kein externer API-Key, kein Datentransfer — auch in einem abgeschotteten Heimnetz.

---

## So erkennst du eine Pflanze

### Schritt 1: Bilderkennung öffnen

Klicke in der Navigation auf **Pflanze erkennen** oder öffne den Dialog über die Schaltfläche **"Pflanze identifizieren"** auf der Stammdaten-Seite.

!!! info "Screenshot folgt"
    Dieser Screenshot wird in einer zukünftigen Version ergänzt.

### Schritt 2: Foto aufnehmen oder hochladen

Wähle eine der drei Eingabemethoden:

=== "Webcam"

    Klicke auf **Kamera verwenden**. Der Browser fragt nach der Kamera-Berechtigung.
    Richte die Kamera auf die Pflanze und klicke auf **Aufnehmen**.

=== "Smartphone"

    Tippe auf **Foto aufnehmen**. Dein Smartphone öffnet die Kamera-App direkt.
    Fotografiere die Pflanze und bestätige das Bild.

=== "Datei hochladen"

    Ziehe eine Bilddatei in den markierten Bereich oder klicke auf **Datei auswählen**.
    Unterstützte Formate: JPEG, PNG (max. 10 MB).

!!! tip "Bessere Erkennungsqualität"
    Fotografiere ein einzelnes, gut beleuchtetes Organ (Blatt, Blüte, Frucht) möglichst ohne ablenkenden Hintergrund. Je klarer das Motiv, desto treffsicherer das Ergebnis.

### Schritt 3: Pflanzenorgan auswählen

Gib an, welchen Pflanzenteil du abgelichtet hast. Das verbessert die Treffsicherheit des Matchings.

| Organ | Wählen wenn... |
|-------|---------------|
| Blatt | Blatt, Blattstiel, Blattnerven |
| Blüte | Blüte, Knospe |
| Frucht | Frucht, Beere, Samen |
| Rinde / Stamm | Stamm, Ast, Borke |
| Wurzel | Wurzel, Rhizom |
| Gesamt | Gesamte Pflanze, mehrere Organe sichtbar |

### Schritt 4: Erkennung starten und Ergebnis auswerten

Klicke auf **Pflanze erkennen**. Die Erkennung dauert je nach Hardware wenige Sekunden.

Das System zeigt dir eine Vorschlagsliste mit den ähnlichsten Arten und einem Konfidenzwert (0–100 %).

!!! info "Screenshot folgt"
    Dieser Screenshot wird in einer zukünftigen Version ergänzt.

**Was die Konfidenzwerte bedeuten:**

| Konfidenzbereich | Bedeutung | Empfehlung |
|:----------------:|-----------|-----------|
| 85 % und höher | Hohe Übereinstimmung | Art direkt übernehmen |
| 50–84 % | Mäßige Übereinstimmung | Ergebnis prüfen und bestätigen |
| 10–49 % | Unsichere Übereinstimmung | Zweitmeinung einholen |
| Unter 10 % | Keine verlässliche Erkennung | Neue Aufnahme versuchen oder manuell suchen |

### Schritt 5: Ergebnis bestätigen

Klicke auf den Vorschlag, der am besten passt. Das System legt die Art **nicht automatisch an** — du entscheidest explizit, ob du die Pflanze mit dieser Art verknüpfst.

Klicke auf **Diese Art anlegen**, um direkt einen neuen Pflanzdurchlauf mit der erkannten Art zu starten.

---

## Wenn die Erkennung unsicher ist

Nicht alle Arten sind gleich gut im Referenz-Index vertreten. Das System kommuniziert Lücken offen:

!!! warning "Art ohne ausreichende Referenzbilder"
    Wenn für eine Art weniger als 5 Referenzbilder indexiert sind, erscheint sie **nicht** in der Vorschlagsliste — auch wenn sie vorhanden ist. In diesem Fall bietet das System an:

    - **Erneute Aufnahme** aus einem anderen Winkel oder mit anderem Organ
    - **Manuelle Suche** in den Stammdaten
    - **Zweitmeinung per Pl@ntNet** (nur mit deiner Einwilligung — sieh Abschnitt "Pl@ntNet-Fallback" weiter unten)

### Was du tun kannst

1. Versuche ein Foto eines anderen Pflanzenorgans (z.B. Blüte statt Blatt).
2. Achte auf gute Beleuchtung und einen neutralen Hintergrund.
3. Suche die Art manuell über **Stammdaten > Suche** nach wissenschaftlichem oder deutschem Namen.
4. Aktiviere den Pl@ntNet-Fallback für eine Zweitmeinung (siehe unten).

---

## Pl@ntNet-Fallback

Wenn die lokale Erkennung keine verlässlichen Ergebnisse liefert (Konfidenz unter dem Schwellenwert), kann das System optional **Pl@ntNet** als externe Zweitmeinung anfragen.

!!! warning "Dein Foto verlässt die Instanz"
    Bei Nutzung des Pl@ntNet-Fallbacks wird dein Foto an den externen Pl@ntNet-Dienst (Frankreich) übertragen. Pl@ntNet ist kostenlos (bis 500 Anfragen/Tag), aber dein Bild verlässt dabei dein Netzwerk.

    **Kamerplanter fragt vor der ersten Nutzung nach deiner ausdrücklichen Einwilligung.** Du kannst diese Einwilligung jederzeit unter **Einstellungen > Datenschutz** widerrufen.

### Pl@ntNet-Einwilligung erteilen

1. Öffne **Einstellungen > Datenschutz**.
2. Aktiviere **"Pl@ntNet-Fallback für Bilderkennung"**.
3. Lies den Datenschutzhinweis und bestätige.

Nach erteilter Einwilligung erscheint im Erkennungsdialog automatisch die Option **"Pl@ntNet befragen"**, wenn die lokale Konfidenz zu niedrig ist.

---

## Datenschutz auf einen Blick

| Aspekt | Primärpfad (lokal) | Pl@ntNet-Fallback |
|--------|:-----------------:|:-----------------:|
| Foto verlässt die Instanz | Nein | Ja |
| Foto wird gespeichert | Nein | Nein |
| Drittland-Transfer | Nein | Ja (Frankreich, EU) |
| Kosten | 0 € | 0 € (bis 500/Tag) |
| Einwilligung erforderlich | Nein | Ja |
| EXIF-Daten (GPS, Kameradaten) | Werden entfernt | Werden vor Transfer entfernt |

!!! note "Kein Bild wird gespeichert"
    Kamerplanter speichert dein Foto in keinem Fall dauerhaft. Das Bild wird nur während der Verarbeitung im Arbeitsspeicher gehalten und danach verworfen. Im Erkennungsprotokoll erscheint nur, welche Art erkannt wurde — kein Bild.

---

## Häufige Fragen

??? question "Warum liefert die Erkennung keine Ergebnisse für meine Pflanze?"
    Mögliche Ursachen: (1) Die Art ist in den Stammdaten nicht angelegt — dann kann auch kein Referenz-Index existieren. (2) Für die Art existieren weniger als 5 Referenzbilder (Abdeckungslücke). (3) Das Foto hat zu geringe Qualität. Versuche es mit einem schärferen Bild eines anderen Pflanzenorgans.

??? question "Wie genau ist die Erkennung?"
    Die Treffsicherheit hängt von der Qualität und Anzahl der Referenzbilder ab. Für gängige Zimmerpflanzen, Gemüse und Kräuter ist die Abdeckung hoch (80–90 %). Für exotische oder seltene Arten kann die Erkennung unsicherer sein. Das System zeigt dir den Konfidenzwert immer transparent an.

??? question "Kann die Erkennung Sorten (Cultivare) unterscheiden?"
    Nein. Die Erkennung arbeitet auf Artebene (Species), nicht auf Sortenebene. Der Grund: Lizenzfreie, sortengenaue Referenzbilder existieren nicht in ausreichender Menge. Wenn du eine bestimmte Sorte identifizieren möchtest, nutze die manuelle Suche in den Stammdaten.

??? question "Werden meine Fotos für das Training von KI-Modellen verwendet?"
    Nein. Kamerplanter verwendet deine Fotos ausschließlich für die aktuelle Erkennungsanfrage. Sie werden weder gespeichert noch für Training oder andere Zwecke genutzt.

??? question "Kann ich die Erkennung ohne Internetverbindung verwenden?"
    Ja — der Primärpfad (lokale DINOv2-Inferenz) funktioniert vollständig offline. Nur der Pl@ntNet-Fallback erfordert eine Internetverbindung, und nur wenn du ihn manuell aktiviert hast.

??? question "Ich habe versehentlich ein Foto mit GPS-Daten hochgeladen — wurde der Standort gespeichert?"
    Nein. Kamerplanter entfernt alle EXIF-Metadaten (einschließlich GPS-Koordinaten) automatisch vor jeder Verarbeitung. Standortdaten werden niemals ausgelesen oder gespeichert.

---

## Siehe auch

- [Stammdaten — Pflanzenarten anlegen](plant-management.md)
- [Pflanzdurchlauf starten](planting-runs.md)
- [Datenschutz (DSGVO)](privacy.md)
- [Bilderkennung in Betrieb nehmen (Deployment)](../deployment/inference-service.md)
- [Architektur der Bilderkennung](../architecture/ai-architecture.md#bilderkennung-dinov2)
