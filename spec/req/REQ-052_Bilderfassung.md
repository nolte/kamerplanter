# Spezifikation: REQ-052 - Bilderfassung

```yaml
ID: REQ-052
Titel: Bilderfassung (Kamera, Datei, Normalisierung, Vorschau — der gemeinsame Baustein aller bildverarbeitenden Anforderungen)
Kategorie: Querschnitt & Erfassung
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: React 19, TypeScript 6, MediaDevices API, Canvas, Flutter (geplant)
Status: Entwurf
Priorität: Hoch
Version: 1.0
Datum: 2026-08-16
Tags: [capture, camera, upload, normalization, exif, client-neutral, cross-cutting]
Abhängigkeit: NFR-013 v1.4 (Object Storage — Attachments, Renditions, Mime-Whitelist, Größenlimit), REQ-029 v1.1 (Bilderkennung — Ursprung des Erfassungsdialogs), REQ-029-A v1.2 (§0.1.1 Punkt 4 — Webcam und Smartphone als Bildquelle), REQ-034 v1.2 (Foto-Galerie — parametrierbare Normalisierung), REQ-025 v1.6 (DSGVO — Standortdaten in Bildern), REQ-024 v1.7 / REQ-049 v1.4 (Rollen), REQ-027 (Light-Modus), UI-NFR-001 (Responsive), UI-NFR-002 (Barrierefreiheit)
Wird benötigt von: REQ-029, REQ-034, REQ-038, REQ-043, REQ-044, REQ-051, REQ-010
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-08-16 | Erstfassung. Die Bilderfassung war bis hierher **§4.1 einer Anforderung über KI-Pflanzenidentifikation** (REQ-029) — historisch, weil REQ-029 zuerst da war, nicht fachlich. Sechs Anforderungen berufen sich inzwischen darauf. Diese Anforderung übernimmt REQ-029 §4.1 (Erfassungswege) und REQ-034 §2.2 (Wiederverwendung und parametrierbare Normalisierung), führt die auf zwei Dokumente verstreuten Normalisierungsparameter (1280 px/0.85 gegen 2048 px/0.9) in **einem** Profilbegriff zusammen und schließt vier bislang nirgends spezifizierte Lücken: Kamerawahl und Berechtigungsablehnung, HEIC/HEIF von iOS-Geräten, Mehrfachauswahl, und der native Kamerapfad, den REQ-051 §7.2 fordert, ohne dass es einen Ort gäbe, an dem er steht. |

---

## 0. Verhältnis zu bestehenden Spezifikationen

Diese Anforderung erfindet **keinen** neuen Erfassungsweg und **kein** neues Speicherkonzept. Sie
beschreibt an einem Ort, was heute in zwei Dokumenten steht und von sechs weiteren zitiert wird.

| Dokument | Was es liefert | Verhältnis zu REQ-052 |
|----------|----------------|----------------------|
| **REQ-029** | Erfassungsdialog als Teil der Pflanzenidentifikation (§4.1), clientseitiger EXIF-Strip (§5.4) | **Wandert hierher.** REQ-029 behält Adapter, Engine, Consent und die Ergebnisdarstellung und verweist für die Erfassung. |
| **REQ-029-A** | §0.1.1 Punkt 4: Webcam und Smartphone sind verbindliche Bildquellen | Die Festlegung bleibt dort; REQ-052 ist ihre Ausführung. |
| **REQ-034** | Wiederverwendung derselben drei Wege, höhere Auflösung für Galeriefotos (§2.2) | **Wandert hierher** als Profil `gallery` (§3). REQ-034 behält Zuordnung, Titelbild, Metadaten. |
| **NFR-013** | `attachments`, Mime-Whitelist, 25-MB-Grenze, Renditions 128/512/1280 px WebP, serverseitiger EXIF-Strip | Übernimmt **ab dem Upload**. REQ-052 endet mit der Datei, die hochgeladen wird. |
| **REQ-025** | Standortdaten und Gerätekennungen als personenbezogene Daten | Begründet, warum EXIF **clientseitig** fällt und nicht erst am Server (§5). |
| **REQ-038 / REQ-043 / REQ-044 / REQ-051 / REQ-010** | Verwendungen | Konsumenten. Sie beschreiben **was** mit dem Bild geschieht, nicht wie es entsteht. |

### 0.1 Was aus REQ-029 und REQ-034 hierher wandert

| Bisher | Jetzt | Inhalt |
|--------|-------|--------|
| REQ-029 §4.1 (Zeilen „Kamera-Button", „Datei-Upload") | §2 | Die drei Erfassungswege |
| REQ-029 §5.4 | §5 | Clientseitiger EXIF-Strip |
| REQ-034 §2.2 | §2, §3 | Wiederverwendung und parametrierbare Normalisierung |
| REQ-029 §4.1 (Zeilen „Organ-Auswahl", „Ergebnis-Liste", „Auswahl-Button", „Manuelle Suche", „Krankheitsdiagnose") | bleibt REQ-029 | Fachlogik der Identifikation — **keine** Erfassung |

**Die Trennlinie verläuft an der Datei.** Alles, was zu einer hochladbaren, normalisierten Datei
führt, steht hier. Alles, was danach mit ihr geschieht — an welche API sie geht, welche Organe
auswählbar sind, wie das Ergebnis aussieht —, bleibt in der jeweiligen Fach-Anforderung. Der Grund
ist der Anlass dieser Anforderung: Sechs Fach-Anforderungen brauchen dieselbe Datei und
unterscheiden sich vollständig in dem, was sie damit tun.

---

## 1. Business Case

### 1.1 User Stories

> **Als Zimmerpflanzen-Besitzerin am Laptop** möchte ich meine Pflanze mit der eingebauten Kamera
> fotografieren, ohne vorher ein Foto auf der Festplatte zu suchen.

> **Als Gärtner im Gewächshaus** möchte ich mit dem Telefon fotografieren und dabei die
> **Rückkamera** bekommen, nicht die Selfie-Kamera — und ich möchte das Bild sehen, bevor ich es
> abschicke, weil im Gegenlicht jedes zweite unbrauchbar ist.

> **Als iPhone-Nutzerin** möchte ich, dass meine Fotos funktionieren, ohne dass ich vorher etwas
> umstellen muss. (Das Gerät liefert HEIC — §4.)

> **Als Nutzer, der die Kameraerlaubnis versehentlich verweigert hat**, möchte ich einen
> verständlichen Hinweis und den Datei-Upload als Ausweg, statt einer Schaltfläche, die nichts tut.

> **Als datenschutzbewusster Nutzer** möchte ich sicher sein, dass der Aufnahmeort mein Gerät nicht
> verlässt — auch dann nicht, wenn das Bild an einen Erkennungsdienst geht.

> **Als Nutzer der Mobil-App** möchte ich dieselben Erfassungswege wie im Browser, mit der nativen
> Kamera statt einer Web-Ansicht.

### 1.2 Warum die Erfassung eine eigene Anforderung braucht

Der Erfassungsbaustein wird heute von **sechs** Anforderungen konsumiert:

| Anforderung | Verwendung | Verweist heute auf |
|-------------|-----------|--------------------|
| REQ-029 | Artbestimmung | eigenes §4.1 |
| REQ-034 | Foto-Galerie an der Pflanze | REQ-029 §4.1 |
| REQ-038 | CV-Pflanzendiagnose | „wird aus dem `PlantIdentificationDialog` wiederverwendet" |
| REQ-043 | Gesundheits-Einschätzung | `HealthAssessmentDialog`, wiederverwendet |
| REQ-044 | Schädlingserkennung | `PestScanButton`, wiederverwendet |
| REQ-051 | Tagebuch-Fotos | REQ-034 §2.2 |
| REQ-010 v1.4 | nutzerbeigesteuerte Schädlingsfotos | REQ-034 |

Sechs Konsumenten und keine eigene Quelle ist genau die Lage, aus der Drift entsteht. Sie ist
bereits eingetreten und **messbar**:

- Die **Normalisierungsparameter** stehen in zwei Dokumenten mit verschiedenen Werten
  (REQ-029: 1280 px, REQ-034: 2048 px) und ohne gemeinsamen Begriff, unter dem man sie
  nachschlägt. Im Code liegen beide Paare bereits nebeneinander in `imageNormalization.ts`
  (`MAX_EDGE`/`JPEG_QUALITY` gegen `GALLERY_MAX_EDGE`/`GALLERY_JPEG_QUALITY`) — die Umsetzung hat
  die Vereinheitlichung vorweggenommen, die Spezifikation nicht.
- **HEIC/HEIF** ist in `SUPPORTED_TYPES` der Umsetzung enthalten und in NFR-013 §5.2 als
  Mime-Typ zugelassen, aber in **keiner** Anforderung als Erfassungsfall beschrieben. Ein
  iPhone-Foto ist der Normalfall, nicht der Sonderfall.
- **Kamerafehler** — Erlaubnis verweigert, keine Kamera vorhanden, Browser kann es nicht — sind im
  Code als `WebcamError` mit vier Werten klassifiziert und in keiner Anforderung genannt.
- Der **native Kamerapfad** für die Mobil-App wird von REQ-051 §7.2 gefordert und ist nirgends
  spezifiziert.

### 1.3 Scope-Abgrenzung

**Innerhalb:** die drei Erfassungswege, Kamerawahl und Lebenszyklus des Kamerastreams,
Berechtigungs- und Fehlerbehandlung, Vorschau und Verwerfen, Formatannahme inklusive HEIC,
Normalisierungsprofile, clientseitiger EXIF-Strip, Mehrfachauswahl, Barrierefreiheit der
Erfassung, Client-Neutralität für Web und Mobile.

**Außerhalb:**

- **Was mit dem Bild geschieht.** Upload-Endpunkt, Speicherung, Renditions und serverseitiger
  EXIF-Strip sind NFR-013; Erkennung, Diagnose und Zuordnung sind die jeweilige
  Fach-Anforderung.
- **Bildbearbeitung.** Kein Zuschneiden, Drehen, Aufhellen oder Filtern. Ein Erfassungsbaustein,
  der bearbeitet, verändert Belegmaterial; wer ein besseres Bild will, macht ein neues.
  (§10, O-61 hält die Frage für das Zuschneiden offen, weil sie bei Blattfotos wiederkehrt.)
- **Videoaufnahme** und Serienbilder.
- **Automatische Auslösung** — keine Erfassung ohne Nutzerhandlung, in keinem Modus.

---

## 2. Die drei Erfassungswege

> Übernommen aus REQ-029 §4.1 und REQ-034 §2.2.

Jede bildverarbeitende Oberfläche bietet **dieselben drei Wege** an, in dieser Reihenfolge:

| # | Weg | Technik | Primär für |
|---|-----|---------|-----------|
| 1 | **Live-Kamera** | `navigator.mediaDevices.getUserMedia()` mit Live-Vorschau und Auslöser | Desktop, Kiosk, Tablet |
| 2 | **Gerätekamera** | `<input type="file" accept="image/*" capture="environment">` | Smartphone |
| 3 | **Datei-Upload** | Dateiauswahl und Drag & Drop | Desktop, nachträglich hochgeladene Bilder |

**Weg 2 ist kein Ersatz für Weg 1, sondern der mobile Normalfall.** `capture="environment"` übergibt
an die System-Kamera-App; das Ergebnis ist ein Foto in Gerätequalität mit der Bedienung, die der
Nutzer kennt. `getUserMedia()` auf demselben Gerät lieferte eine schlechtere Vorschau in einem
Browser-Rahmen. Umgekehrt ist Weg 2 am Desktop nutzlos.

**Welcher Weg angeboten wird, entscheidet die Fähigkeit, nicht die Bildschirmbreite.** Weg 1
erscheint, wenn `navigator.mediaDevices?.getUserMedia` existiert; Weg 2, wenn das Gerät
Zeigereingabe per Berührung meldet. Eine Entscheidung nach Breite verstecke die Kamera auf einem
schmalen Desktop-Fenster und böte sie auf einem Tablet ohne Kamera an. Weg 3 ist **immer**
vorhanden — er ist der Rückfall für jeden Fehlerzustand aus §6.

### 2.1 Vorschau und Verwerfen

Ein erfasstes Bild wird **immer** zuerst angezeigt, nie direkt abgeschickt. Der Nutzer sieht das
Bild in der Größe, in der es hochgeladen wird, und hat zwei Handlungen: übernehmen oder verwerfen
und neu aufnehmen.

**Warum verbindlich:** Im Gewächshaus, im Gegenlicht und mit erdigen Fingern ist ein
unbrauchbares Bild der Regelfall. Ein Ablauf ohne Vorschau erzeugt einen Anhang, den jemand
später löschen muss — und bei der Erkennung zusätzlich einen bezahlten Fremdaufruf auf ein Foto,
das der Nutzer nie sehen wollte.

Die Vorschau zeigt das **normalisierte** Bild (§3), nicht das Rohbild. Sonst verspricht sie eine
Qualität, die nicht ankommt.

### 2.2 Mehrfachauswahl

Wo die konsumierende Anforderung mehrere Bilder erlaubt (Tagebuch bis 5, Galerie unbegrenzt),
nimmt Weg 3 mehrere Dateien in einem Vorgang entgegen. Die Wege 1 und 2 liefern **je ein** Bild
pro Auslösung — mehrfach nacheinander möglich.

Die Obergrenze gehört der konsumierenden Anforderung, nicht diesem Baustein; sie wird ihm als
Parameter übergeben. Wird sie überschritten, werden die überzähligen Bilder **benannt abgelehnt**
und nie still verworfen (AK-64). Ein still gekürzter Mehrfach-Upload ist die Fehlerklasse, gegen
die auch NFR-013 und REQ-050 §4.4 argumentieren.

---

## 3. Normalisierung: zwei Profile, ein Begriff

Vor dem Upload wird jedes Bild clientseitig normalisiert: längste Kante begrenzen, als JPEG neu
kodieren, Metadaten verlieren (§5). Die Parameter dafür bilden **benannte Profile** — bis hierher
standen sie namenlos in zwei Anforderungen.

| Profil | Längste Kante | JPEG-Qualität | Verwendung | Begründung |
|--------|---------------|---------------|-----------|------------|
| `recognition` | 1280 px | 0.85 | REQ-029 Artbestimmung, REQ-038 CV-Diagnose, REQ-043, REQ-044 | Die Erkennungsdienste normalisieren ohnehin auf diese Größenordnung; mehr Pixel kosten Bandbreite und Zeit, ohne die Trefferquote zu verbessern, und halten die Nutzlast unter dem 5-MB-Limit der Fremd-API |
| `gallery` | 2048 px | 0.9 | REQ-034 Foto-Galerie, REQ-051 Tagebuch, REQ-010 Referenzbilder | Diese Bilder dokumentieren die Pflanze über Monate und werden später vergrößert betrachtet; sie auf Erkennungsgröße zu stauchen verlöre genau das, wofür sie aufgenommen wurden |

**Die Profile sind der einzige Ort, an dem diese Zahlen stehen.** Eine Fach-Anforderung wählt ein
Profil; sie nennt keine Pixelwerte. Bis v1.0 nannte REQ-029 1280 px und REQ-034 2048 px, ohne dass
ein Leser erkennen konnte, ob das zwei Fälle desselben Bausteins sind oder zwei Bausteine — und
ohne dass eine Änderung an einer Stelle die andere erreicht hätte.

**Ein drittes Profil ist eine Entscheidung, keine Feinabstimmung.** Wer eine neue Verwendung mit
eigenen Werten will, ergänzt hier eine Zeile mit Begründung. Ein Aufrufer, der `maxEdge` frei
übergibt, hebt die Vereinheitlichung wieder auf.

**Die Obergrenze der hochzuladenden Datei** ist `STORAGE_MAX_FILE_SIZE_MB` (NFR-013 §5.2, Vorgabe
25 MB) und wird nach der Normalisierung geprüft, nicht davor: Ein 40-MB-Rohfoto ist nach dem
Profil `gallery` regelmäßig unter 2 MB, und es vorher abzulehnen wiese genau die Bilder ab, die
moderne Telefone liefern.

---

## 4. Welche Formate angenommen werden

Angenommen werden `image/jpeg`, `image/png`, `image/webp`, `image/heic` und `image/heif` — dieselbe
Menge, die NFR-013 §5.2 für Foto-Kategorien zulässt.

**HEIC/HEIF ist der iOS-Normalfall und muss ausdrücklich funktionieren.** Ein iPhone liefert seit
iOS 11 standardmäßig HEIC. Die Normalisierung nach §3 kodiert ohnehin als JPEG neu, löst das
Problem also — **sofern der Browser das Bild dekodieren kann**. Safari kann es, Firefox und Chrome
unter Windows und Linux überwiegend nicht.

**Festlegung:** Schlägt die Dekodierung fehl, wird das Bild **unverändert** hochgeladen und die
Konvertierung dem Server überlassen (NFR-013 §5.2 nennt die serverseitige Konvertierung
ausdrücklich als empfohlen). Der Nutzer bekommt einen Hinweis, dass das Bild in Originalgröße
übertragen wird, und keine Fehlermeldung.

**Warum nicht ablehnen:** Eine Ablehnung träfe den Nutzer für eine Eigenschaft seines Geräts, die
er nicht kennt und nicht ändern will, in einem Ablauf, in dem er nichts falsch gemacht hat. Der
Preis ist eine größere Übertragung in einem Randfall — deutlich billiger als ein Foto, das nicht
ankommt.

**Nicht angenommen** werden Animationen (GIF, animiertes WebP) und Vektorformate. Ein bewegtes
Bild als Pflanzenbeleg ist keine gewollte Verwendung, und SVG ist ein Ausführungsvektor, kein
Foto.

---

## 5. EXIF fällt auf dem Gerät, nicht erst am Server

> Übernommen aus REQ-029 §5.4.

Die Normalisierung nach §3 zeichnet das Bild auf ein `<canvas>` und liest es zurück. Dabei gehen
**alle** Metadaten verloren — Aufnahmeort, Gerätekennung, Aufnahmezeit, Orientierung. Das ist keine
Nebenwirkung, sondern der Zweck.

**Warum clientseitig, obwohl der Server ohnehin strippt.** Der serverseitige Strip (NFR-013 §6.4)
ist die zweite Verteidigungslinie, nicht die erste. Drei Gründe verlangen die erste:

1. **Bei der Erkennung verlässt das Bild die Instanz.** REQ-029-A §0.1.1 Punkt 2 macht Pl@ntNet
   in Phase 1 zum Primärpfad; das Foto geht an einen Dritten. Ein Strip, der erst am eigenen
   Server liefe, käme für diesen Weg zu spät.
2. **`STORAGE_STRIP_EXIF` ist abschaltbar** (NFR-013 §6.4). Eine Instanz, die es abschaltet, um
   Aufnahmedaten zu behalten, dürfte damit nicht zugleich die Standortdaten jedes
   Erkennungsuploads freilegen.
3. **Der Aufnahmeort einer Zimmerpflanze ist die Wohnanschrift.** REQ-025 behandelt
   Standortangaben als personenbezogenes Datum; sie gar nicht erst zu übertragen ist die
   Datenminimierung, die Art. 5(1)(c) verlangt.

**Folge, die zu kennen ist:** Die Aufnahmezeit aus dem Bild steht danach nicht mehr zur Verfügung.
REQ-034 §2.1 zieht daraus bereits die richtige Konsequenz — `taken_on` ist ein **vom Nutzer
pflegbares** Feld mit dem Upload-Zeitpunkt als Rückfall, nicht ein aus EXIF gelesener Wert. Jede
künftige Anforderung, die „das Aufnahmedatum" braucht, muss denselben Weg gehen.

**Die Orientierung geht mit.** Ein Bild, dessen Ausrichtung nur im EXIF-Feld stand, erscheint nach
dem Strip gedreht. Die Normalisierung muss die Orientierung deshalb **vor** dem Verwerfen
anwenden und in die Pixel schreiben (AK-63) — sonst löst der Datenschutzmechanismus einen sichtbaren
Darstellungsfehler aus, und der nächste Bearbeiter behebt ihn, indem er den Strip abschaltet.

---

## 6. Fehlerzustände der Kamera

Die Live-Kamera (Weg 1) kann auf vier unterscheidbare Arten nicht verfügbar sein. Jede hat einen
eigenen Text und **immer** denselben Ausweg: Datei-Upload.

| Zustand | Ursache | Was der Nutzer sieht |
|---------|---------|---------------------|
| `permission_denied` | Erlaubnis verweigert oder unsicherer Kontext (`NotAllowedError`, `SecurityError`) | „Kamerazugriff ist nicht erlaubt" plus gerätespezifischer Hinweis, wo sich das ändern lässt |
| `not_found` | keine Kamera vorhanden oder Wunschkamera nicht erfüllbar (`NotFoundError`, `OverconstrainedError`) | „Keine Kamera gefunden" |
| `unsupported` | `navigator.mediaDevices` fehlt (alter Browser, kein HTTPS) | Weg 1 wird **gar nicht erst angeboten** |
| `unknown` | alles Übrige | „Die Kamera konnte nicht gestartet werden" |

**`unsupported` wird nicht als Fehler gezeigt, sondern durch Weglassen behandelt.** Eine
Schaltfläche anzubieten, die zuverlässig scheitert, ist schlechter als keine Schaltfläche.

**Die Erlaubnis wird nie vorab erfragt.** Der Browser-Dialog erscheint erst, wenn der Nutzer die
Kamera anfordert — nicht beim Öffnen der Seite. Eine Anfrage ohne erkennbaren Anlass wird
weggeklickt, und die Ablehnung ist danach gerätepersistent.

### 6.1 Der Kamerastream wird immer freigegeben

Beim Beenden der Erfassung, beim Verlassen der Ansicht und beim Verwerfen werden **alle** Tracks
gestoppt. Die Kamera-Anzeige des Geräts muss erlöschen.

**Warum das eine Anforderung und keine Implementierungsdetail ist:** Eine laufende Kamera, deren
Anzeige leuchtet, obwohl der Nutzer die Ansicht verlassen hat, ist unabhängig von jeder Absicht
ein Vertrauensbruch — und auf Mobilgeräten zusätzlich ein Akkuverbrauch, der der App zugerechnet
wird. Der Fall entsteht nicht durch Vergessen im Normalablauf, sondern beim Abbruch: Navigation
zurück, Dialog per Escape geschlossen, Komponente durch einen Fehler entfernt (AK-62).

### 6.2 Kamerawahl

Angefordert wird die **Rückkamera** (`facingMode: environment`); ist sie nicht erfüllbar, wird auf
eine beliebige Kamera zurückgefallen, statt zu scheitern. Auf einem Laptop mit nur einer
Frontkamera ist genau das der Normalfall.

Eine Auswahlliste aller Kameras gibt es in v1.0 nicht (§10, O-62). Die Gerätenamen sind vor der
Erlaubniserteilung leer, danach herstellerabhängig kryptisch — eine Liste aus `camera2 0, facing
back` hilft niemandem.

---

## 7. Barrierefreiheit und Bedienung

Gilt zusätzlich zu UI-NFR-002.

- Alle drei Wege sind **per Tastatur** erreichbar und auslösbar; der Auslöser ist eine
  Schaltfläche, kein Klick auf das Videobild.
- Die Live-Vorschau trägt eine Textalternative, die ihren Zweck benennt, nicht ihren Inhalt
  („Kameravorschau" — das Bild ist nicht beschreibbar, solange es sich bewegt).
- Zustandswechsel — Kamera gestartet, Bild aufgenommen, Fehler — werden **angesagt**
  (`aria-live`), nicht nur farblich gezeigt. Ohne das bemerkt ein Screenreader-Nutzer die Aufnahme
  nicht.
- Der Auslöser und die Handlungen „übernehmen"/„verwerfen" erfüllen die Touch-Zielgrößen aus
  `spec/ui-nfr/`. Die Erfassung ist die Handlung, die am häufigsten mit erdigen oder nassen
  Fingern ausgeführt wird.
- **Kein Zeitdruck.** Es gibt keinen Selbstauslöser und keine Aufnahme, die nach n Sekunden von
  selbst geschieht.

---

## 8. Client-Neutralität: Web und Mobile

### 8.1 Was für beide Clients gilt

Verbindlich, unabhängig von der Plattform:

1. **Dieselben drei Wege**, dieselbe Reihenfolge, dieselben Profile aus §3.
2. **EXIF fällt auf dem Gerät** (§5) — in beiden Clients, nicht nur im Browser.
3. **Vorschau vor dem Abschicken** (§2.1).
4. **Der Upload-Vertrag ist derselbe**: Der Client erhält eine `attachment_id` und referenziert
   sie; er kennt kein Storage-Backend, keinen Bucket, keine Region (NFR-013 §2.4).
5. **Die Obergrenze der Bildanzahl kommt von der konsumierenden Anforderung**, nicht vom
   Erfassungsbaustein.

### 8.2 Was der mobile Client zusätzlich braucht

| Thema | Anforderung |
|-------|-------------|
| **Native Kamera** | Weg 1 und Weg 2 fallen auf Mobile zusammen: Es gibt eine native Kamera-Ansicht statt `getUserMedia` plus `capture`-Attribut. Die drei Wege reduzieren sich sichtbar auf **zwei** — Kamera und Fotobibliothek |
| **Berechtigungen** | Kamera und Fotobibliothek sind getrennte Systemberechtigungen und werden **einzeln** und erst bei Bedarf angefragt. Eine dauerhaft verweigerte Berechtigung führt in die Systemeinstellungen, nicht in eine Sackgasse |
| **HEIC** | Das native Bilddekodieren beherrscht HEIC; der Rückfall „unverändert hochladen" aus §4 greift auf Mobile nicht |
| **Orientierung** | Das Gerät liefert die Aufnahmeorientierung getrennt vom Bild; sie ist vor dem Verwerfen der Metadaten in die Pixel zu schreiben (§5) |
| **Bandbreite** | Die Normalisierung geschieht **vor** der Übertragung, nicht am Server. Im Mobilnetz ist das der Unterschied zwischen 1,5 MB und 40 MB je Foto |
| **Kein Hintergrund-Upload** | v1.0 sagt keinen Upload nach dem Verlassen der Ansicht zu (§10, O-63) |

### 8.3 Was ausdrücklich nicht zugesagt wird

**Keine Offline-Erfassung.** Ein aufgenommenes Bild, das nicht hochgeladen werden kann, geht
verloren; es gibt keine Warteschlange. Der Grund ist derselbe wie in REQ-051 §7.3: Eine
Warteschlange ohne Konfliktmodell für den zugehörigen Datensatz erzeugt Datenverlust, den der
Nutzer für Synchronisation hält. Ein Client **darf** eine unabgeschickte Aufnahme lokal halten,
solange er sie nicht als gespeichert ausweist.

---

## 9. Berechtigungen und Betriebsmodi

Die Erfassung selbst kennt **keine** eigene Rechteprüfung — sie erzeugt eine Datei im Arbeitsspeicher
des Clients. Geprüft wird beim **Upload** und beim **Verknüpfen**, und zwar von der konsumierenden
Anforderung:

| Handlung | Rolle |
|----------|-------|
| Erfassungsdialog öffnen | Alle Rollen |
| Bild hochladen und verknüpfen | Ab Gärtner |
| Bild entfernen | Nur Leitung (REQ-049 §2.3) |

Ein Beobachter bekommt den Erfassungsdialog **gar nicht erst angeboten** — eine Aufnahme, deren
Upload anschließend abgewiesen wird, ist eine vorgetäuschte Fähigkeit.

Zusätzlich gilt die Herkunftsregel aus SEC-003: Ein Gärtner darf nur Attachments referenzieren,
die er selbst hochgeladen hat; die Leitung ist ausgenommen (REQ-034, REQ-051 §3.3).

**Im Light-Modus (REQ-027)** funktioniert die Erfassung unverändert; es gibt dort nur einen Nutzer,
und die Einschränkungen greifen nicht. Der Einwilligungsvorbehalt für die **Erkennung**
(`plant_identification`, REQ-029-A §0.1.1 Punkt 2) betrifft nicht die Erfassung, sondern den
Versand an den Dritten — er wird geprüft, wenn das Bild die Instanz verlässt, nicht wenn es
entsteht.

---

## 10. Akzeptanzkriterien

| ID | Kriterium |
|----|-----------|
| **AK-60** | Jede bildverarbeitende Oberfläche bietet dieselben drei Erfassungswege in derselben Reihenfolge an (§2). Weg 1 erscheint nur bei vorhandenem `getUserMedia`, Weg 2 nur auf Geräten mit Berührungseingabe, Weg 3 **immer**. |
| **AK-61** | Ein erfasstes Bild wird vor dem Abschicken in der Größe angezeigt, in der es hochgeladen wird — also **nach** der Normalisierung —, und lässt sich verwerfen. Kein Ablauf schickt ein Bild ohne diesen Schritt ab. |
| **AK-62** | Nach Beenden, Verlassen oder Verwerfen ist **jeder** Track des Kamerastreams gestoppt und die Kamera-Anzeige des Geräts erloschen. Der Nachweis umfasst die Abbruchpfade (Zurück-Navigation, Escape, Entfernen der Komponente durch einen Fehler), nicht nur den Normalablauf. |
| **AK-63** | Ein Bild, dessen Ausrichtung ausschließlich im EXIF stand, wird nach der Normalisierung **richtig herum** angezeigt und hochgeladen: Die Orientierung wird vor dem Verwerfen der Metadaten in die Pixel geschrieben. |
| **AK-64** | Werden mehr Bilder ausgewählt, als die konsumierende Anforderung zulässt, werden die überzähligen **benannt abgelehnt**. Eine stille Kürzung ist ein Fehlschlag des Kriteriums. |
| **AK-65** | Ein hochgeladenes Bild enthält **keine** EXIF-Daten — insbesondere keine GPS-Koordinaten und keine Gerätekennung —, und zwar unabhängig von `STORAGE_STRIP_EXIF`. Der Nachweis erfolgt an der Datei, die das Gerät verlässt, nicht an der gespeicherten. |
| **AK-66** | Die Profile aus §3 sind die einzige Quelle der Normalisierungsparameter. Ein Test weist die **Abwesenheit** frei übergebener Pixelwerte an den Aufrufstellen nach — wird `maxEdge` irgendwo direkt gesetzt, ist die Vereinheitlichung aufgehoben, ohne dass ein Verhaltenstest anschlägt. |
| **AK-67** | Ein HEIC-Bild, das der Browser dekodieren kann, wird normalisiert; eines, das er nicht dekodieren kann, wird **unverändert** hochgeladen — mit Hinweis auf die Originalgröße, nicht mit einer Fehlermeldung. In keinem Fall wird es abgewiesen. |
| **AK-68** | Die vier Kamera-Fehlerzustände aus §6 sind sichtbar voneinander unterschieden und benennen jeweils den Datei-Upload als Ausweg. `unsupported` bietet Weg 1 gar nicht erst an. |
| **AK-69** | Die Kameraerlaubnis wird erst angefragt, wenn der Nutzer die Kamera anfordert — nicht beim Öffnen der Ansicht. |
| **AK-70** | Alle drei Wege sind per Tastatur bedienbar; Start, Aufnahme und Fehler werden über `aria-live` angesagt (§7). |
| **AK-71** | Ein Beobachter bekommt keinen Erfassungsdialog angeboten (§9). |
| **AK-72** | Die Größenprüfung gegen `STORAGE_MAX_FILE_SIZE_MB` erfolgt **nach** der Normalisierung. Ein 40-MB-Rohfoto, das normalisiert unter der Grenze liegt, wird angenommen. |
| **AK-73** | Web- und Mobile-Client verwenden dieselben Profile und denselben Upload-Vertrag; keiner der beiden kennt Storage-Backend, Bucket oder Region. |

---

## 11. Offene Punkte

| Nr. | Frage | Entscheider | Status |
|-----|-------|-------------|--------|
| O-60 | Soll ein drittes Profil `thumbnail_only` entstehen für Verwendungen, die das Original nie brauchen (etwa eine reine Beleg-Aufnahme an einer Aufgabe)? v1.0 hat zwei Profile. | Produkt | offen |
| O-61 | Soll **Zuschneiden** vor dem Upload angeboten werden? §1.3 schließt Bildbearbeitung aus, aber bei Blattfotos für die Diagnose ist der Zuschnitt fachlich sinnvoll — REQ-038 und REQ-044 profitierten. Die Grenze zwischen „Ausschnitt wählen" und „Beleg verändern" ist zu ziehen. | Produkt | offen |
| O-62 | Soll bei mehreren Kameras eine **Auswahl** angeboten werden? v1.0 nimmt die Rückkamera mit Rückfall (§6.2); die Gerätenamen sind vor der Erlaubniserteilung leer und danach herstellerabhängig unlesbar. | Produkt | offen |
| O-63 | Soll die Mobil-App einen **Hintergrund-Upload** bekommen, der nach dem Verlassen der Ansicht weiterläuft? v1.0 sagt ihn nicht zu (§8.2). | Produkt | offen |
| O-64 | Soll die HEIC-Konvertierung auf dem Server verbindlich werden, statt „empfohlen" (NFR-013 §5.2)? Der Rückfall aus §4 hängt heute an einer Empfehlung, nicht an einer Zusage. | DevOps + Produkt | offen |

---

**Dokumenten-Ende**
**Version:** 1.0
**Status:** Entwurf
