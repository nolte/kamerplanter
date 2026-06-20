# Pflanzenfoto-Galerie

Jede Pflanzeninstanz in Kamerplanter kann eine eigene Fotogalerie haben. So erkennst du deine Pflanzen auf einen Blick in der Liste wieder, und du kannst den Wachstumsverlauf über die Zeit festhalten — vom Sämling bis zur Ernte.

---

## Voraussetzungen

- Du bist in Kamerplanter angemeldet und hast mindestens eine Pflanzeninstanz angelegt.
- Zum Hochladen, Löschen und Titelbild-Setzen benötigst du die Rolle **Gärtner** oder **Admin** in deinem Mandanten. Als **Betrachter** kannst du die Galerie ansehen, aber keine Fotos hochladen oder löschen.

---

## Galerie öffnen

1. Öffne das Seitenmenü und navigiere zu deinen **Pflanzen**.
2. Klicke auf die gewünschte Pflanze, um die Detailseite zu öffnen.
3. Wähle den Tab **Fotos**.

Dort siehst du alle bisher hochgeladenen Fotos als Vorschaubilder (Thumbnails). Noch kein Foto vorhanden? Ein neutraler Platzhalter zeigt dir den leeren Zustand.

---

## Foto hochladen

Klicke im Tab „Fotos" auf **Foto hinzufügen**. Es öffnet sich ein Dialog mit drei Möglichkeiten:

=== "Kamera (Smartphone)"

    1. Tippe auf **Foto aufnehmen**.
    2. Dein Gerät öffnet die Kamera-App.
    3. Fotografiere deine Pflanze und bestätige das Foto.

=== "Kamera (Webcam, Desktop)"

    1. Klicke auf **Foto aufnehmen**.
    2. Dein Browser fragt nach der Erlaubnis, die Kamera zu verwenden — bestätige diese.
    3. Es öffnet sich eine Live-Vorschau deiner Webcam.
    4. Positioniere die Pflanze im Bild und klicke auf **Aufnehmen**.

=== "Datei hochladen"

    1. Klicke auf **Foto hochladen** oder ziehe eine Bilddatei per Drag & Drop in den markierten Bereich.
    2. Unterstützte Formate: JPEG, PNG, WebP (bis 25 MB pro Bild).

!!! tip "Tipps für gute Pflanzenfotos"
    - Fotografiere bei gutem Tageslicht oder nah an einer Lichtquelle.
    - Stelle die Kamera ruhig auf, damit das Bild scharf ist.
    - Ein übersichtlicher, ruhiger Hintergrund lässt die Pflanze besser erkennen.
    - Mehrere Fotos aus verschiedenen Winkeln oder aus verschiedenen Wachstumsstadien sind wertvoller als ein einzelnes Foto.

Nach dem Upload erscheint das Foto sofort in der Galerie. Das System erstellt automatisch kleinere Vorschauversionen des Bildes — dieser Vorgang läuft im Hintergrund und dauert nur wenige Sekunden.

!!! note "Datenschutz: EXIF-Daten"
    Beim Hochladen werden **alle EXIF-Metadaten entfernt** — dazu gehören GPS-Koordinaten, Kameramodell und Aufnahmezeitpunkt. Dein Standort und dein Gerät sind nicht mit dem gespeicherten Foto verknüpft. Mehr zum Umgang mit Fotos bei der Kontolöschung: [Datenschutz (DSGVO) — Fotos und Anhänge](privacy.md#fotos-und-anhange-object-storage).

### Foto-Limit

Pro Pflanzeninstanz können standardmäßig bis zu **50 Fotos** gespeichert werden. Der Betreiber kann diesen Wert über die Serverkonfiguration anpassen. Wenn du das Limit erreichst, erscheint eine Hinweismeldung — lösche ältere Fotos, um Platz für neue zu schaffen. Mehr zur Storage-Konfiguration für Betreiber: [Speicher konfigurieren](object-storage.md).

---

## Foto in Vollbild ansehen (Lightbox)

Klicke auf ein Foto in der Galerie, um es in der Vollbild-Ansicht zu öffnen. In der Lightbox kannst du mit den Pfeiltasten (oder Wischgesten auf dem Smartphone) zwischen den Fotos wechseln. Schließe die Lightbox mit **Esc** oder dem Schließen-Symbol.

---

## Titelbild setzen

Ein Titelbild erscheint als Vorschau im **Info-Tab** der Pflanzendetailseite und in der **Pflanzen-Listenansicht**. So erkennst du auf einen Blick, welche Pflanze es ist, ohne die Detailseite öffnen zu müssen.

So setzt du ein Titelbild:

1. Halte den Mauszeiger über das gewünschte Foto in der Galerie (oder drücke lange auf dem Smartphone).
2. Das Foto-Menü erscheint — klicke auf **Als Titelbild setzen**.
3. Das Foto wird mit einem kleinen Stern-Symbol als Titelbild markiert.

!!! tip "Kein Titelbild manuell gesetzt?"
    Solange du kein Titelbild manuell auswählst, verwendet das System das **erste Foto** in der Galerie als Vorschau. Pflanzen ohne jedes Foto zeigen einen neutralen Platzhalter.

---

## Foto löschen

So löscht du ein einzelnes Foto:

1. Halte den Mauszeiger über das Foto (oder drücke lange auf dem Smartphone).
2. Klicke im Foto-Menü auf **Löschen**.
3. Bestätige die Nachfrage — der Vorgang ist nicht rückgängig zu machen.

Das Foto, alle Vorschauversionen und die Verknüpfung mit der Pflanze werden vollständig entfernt. Es verbleiben keine Bilddaten im System.

!!! warning "Beim Löschen der Pflanze"
    Wenn du eine **Pflanzeninstanz löschst**, werden auch alle zugehörigen Fotos und Vorschaubilder automatisch vollständig entfernt.

---

## Optionaler Datenbeitrag zur Bilderkennung

Kamerplanter ermöglicht es, ein Foto einer korrekt bestimmten Pflanze als zusätzliche Referenz für die **self-hosted Bilderkennung** (DINOv2) beizusteuern. Das ist freiwillig, kuratiert und nur mit deiner ausdrücklichen Einwilligung aktiv.

!!! note "Noch nicht aktiv — Phase 2 der Bilderkennung"
    Der Datenbeitrag ist technisch vorbereitet, aber **erst aktiv, wenn die self-hosted Bilderkennung (Phase 2) auf deiner Instanz verfügbar ist**. Solange der Betreiber die self-hosted Erkennung nicht eingerichtet hat, hat diese Einstellung keinen Effekt.

### Wie funktioniert der Beitrag?

Wenn du einwilligst und die self-hosted Erkennung aktiv ist, werden Galerie-Fotos an Pflanzen mit bekannter Art automatisch als zusätzliche Referenz verarbeitet:

- Das Foto wird lokal analysiert und ein **Merkmals-Vektor** (Embedding) erstellt.
- Nur der Vektor wird für die Bilderkennung gespeichert — **nicht das Originalfoto**.
- Das Originalfoto bleibt ausschließlich in deiner Galerie.
- Dein Beitrag ist **nicht öffentlich** und verlässt die Kamerplanter-Instanz nicht.
- Neue Beiträge werden zuerst vom Platform-Admin geprüft, bevor sie die Erkennungsqualität beeinflussen.

### Einwilligung erteilen oder widerrufen

Die Einwilligung für den Datenbeitrag (`reference_contribution`) findest du in den Datenschutz-Einstellungen:

1. Klicke oben rechts auf dein Profilbild.
2. Wähle **Konto-Einstellungen** > **Datenschutz** > **Einwilligungen**.
3. Aktiviere oder deaktiviere **Beitrag zur Bilderkennung**.

Der Widerruf gilt sofort für alle zukünftigen Foto-Uploads. Bereits erzeugte Merkmals-Vektoren werden beim Widerruf und spätestens bei der Kontolöschung entfernt.

!!! note "Light-Modus"
    Im Light-Modus (anonymer Zugang ohne Login) ist der Datenbeitrag zur Bilderkennung nicht verfügbar, weil das dafür nötige Einwilligungs-System nicht aktiviert ist. Die Galerie funktioniert im Light-Modus vollständig.

---

## Häufige Fragen

??? question "Warum sehe ich keinen Tab „Fotos" an meiner Pflanze?"
    Der Tab erscheint immer auf der Detailseite einer Pflanzeninstanz. Falls er fehlt, prüfe, ob du eine **Pflanzeninstanz** geöffnet hast (nicht die Artseite unter Stammdaten). Artseiten zeigen Referenzbilder aus öffentlichen Datenbanken, aber keine persönliche Galerie.

??? question "Werden meine Fotos gespeichert?"
    Ja — das ist der Unterschied zur [Pflanzenerkennung per Foto](plant-identification.md), bei der das Foto bewusst nicht gespeichert wird. Galerie-Fotos werden dauerhaft in dem vom Betreiber konfigurierten Speicher abgelegt (lokales Dateisystem oder S3). Du kannst jedes Foto einzeln löschen.

??? question "Was passiert mit meinen Fotos, wenn ich meinen Account lösche?"
    Wenn du in einem **geteilten Mandanten** (z. B. einem Gemeinschaftsgarten) Fotos hochgeladen hast, bleiben diese als Teil des Pflanzendatensatzes erhalten — dein Name wird dabei entfernt (Anonymisierung). In einem **persönlichen Mandanten** entscheidet der Betreiber über die genaue Behandlung. Mehr Details: [Datenschutz (DSGVO) — Fotos und Anhänge](privacy.md#fotos-und-anhange-object-storage).

??? question "Wie viele Fotos kann ich pro Pflanze hochladen?"
    Standardmäßig bis zu **50 Fotos** pro Pflanzeninstanz. Der Betreiber kann diesen Wert konfigurieren.

??? question "Kann ich Fotos herunterladen?"
    Klicke in der Lightbox auf das Foto und nutze die Download-Option deines Browsers (rechte Maustaste → „Bild speichern"). Ein separater Download-Button ist in der aktuellen Version nicht vorhanden.

??? question "Warum sieht die Foto-Upload-Maske genauso aus wie bei der Bilderkennung?"
    Die Aufnahme-Benutzeroberfläche (Webcam / Smartphone-Kamera / Datei-Upload) ist dieselbe Komponente, die auch bei der Bilderkennung genutzt wird. Der Unterschied liegt im Ergebnis: Bei der Bilderkennung wird das Foto nach der Analyse verworfen. Bei der Galerie wird es dauerhaft gespeichert.

---

## Siehe auch

- [Stammdaten verwalten](plant-management.md) — Referenzbilder für Pflanzenarten (nicht Instanzfotos)
- [Pflanze per Foto identifizieren](plant-identification.md) — Art unbekannter Pflanzen bestimmen
- [Datenschutz (DSGVO)](privacy.md) — EXIF-Behandlung, Löschverhalten, Einwilligungen
- [Speicher konfigurieren](object-storage.md) — Betreiber-Dokumentation zum Storage-Backend
