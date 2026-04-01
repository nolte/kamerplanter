# Druckansichten & Export

Kamerplanter ermöglicht es Ihnen, wichtige Pflegedaten als druckfertige PDFs zu exportieren. Ob Nährstoffplan für den Growraum, Pflege-Checkliste für den täglichen Rundgang oder Infokarten für jeden Topf — gedruckte Unterlagen helfen dort, wo ein Smartphone unpraktisch oder unerwünscht ist.

---

## Voraussetzungen

- Sie sind als Mitglied eines Mandanten angemeldet (Rolle `viewer`, `grower` oder `admin`)
- Für den Nährstoffplan-Export: mindestens ein angelegter Nährstoffplan (→ [Dünge-Logik](fertilization.md))
- Für die Pflege-Checkliste: mindestens eine Pflanze mit aktivem Pflegeprofil (→ [Pflegeerinnerungen](care-reminders.md))
- Für Pflanzen-Infokarten: mindestens eine Pflanzinstanz (→ [Pflanzdurchläufe](planting-runs.md))

---

## Nährstoffplan drucken

Der Nährstoffplan als PDF enthält alle Phasen Ihres Mischplans auf einen Blick: welche Produkte Sie verwenden, wie viel von jedem Produkt pro Liter Wasser Sie einmessen müssen, in welcher Reihenfolge Sie mischen und welchen EC- und pH-Wert die fertige Lösung haben soll.

### Schritt 1: Nährstoffplan öffnen

1. Navigieren Sie im Menü zu **Dünge-Logik** → **Nährstoffpläne**.
2. Klicken Sie auf den Namen des Plans, den Sie drucken möchten.
3. Die Detailseite des Plans öffnet sich.

### Schritt 2: PDF erstellen

1. Klicken Sie in der oberen Toolbar auf das **Drucker-Icon**.
2. Der Download startet automatisch — Ihr Browser speichert die PDF-Datei.

### Schritt 3: Sprache wählen (optional)

Die PDF wird standardmäßig auf Deutsch erstellt. Wenn Sie eine englische Version benötigen, hängen Sie `?locale=en` an die Download-URL an oder wählen Sie im Dialog die Sprache "Englisch".

### Was ist im Nährstoffplan-PDF enthalten?

| Abschnitt | Inhalt |
|-----------|--------|
| Kopfzeile | Planname, Erstellungsdatum, Mandant |
| Phasen-Tabelle | Phase, EC-Ziel, pH-Ziel, NPK-Verhältnis |
| Mischanleitungen | Pro Phase: Produkt, ml pro Liter, Mischreihenfolge |
| Wasser-Konfiguration | Basis-EC des Leitungswassers, RO-Anteil in % |
| Hinweise | CalMag-Korrektur-Empfehlung, Spülprotokoll |

!!! tip "Tipp: Im Growraum aufhängen"
    Laminieren Sie das PDF und hängen Sie es neben Ihrem Mischtisch auf. So haben Sie alle Informationen zum Anmischen griffbereit, ohne das Smartphone in feuchter Umgebung zu benutzen.

!!! warning "Mischsicherheit beachten"
    Das PDF zeigt die Mischreihenfolge in der Reihenfolge an, die CalMag-Ausfällungen verhindert (CalMag immer vor Sulfaten). Weichen Sie nicht von dieser Reihenfolge ab.

---

## Pflege-Checkliste drucken

Die Pflege-Checkliste exportiert alle fälligen Pflegeaufgaben für einen gewählten Tag als druckbares PDF mit Checkboxen zum Abhaken. Ideal für den morgendlichen Rundgang durch Gewächshaus, Garten oder Wohnung.

### Schritt 1: Pflege-Dashboard öffnen

1. Navigieren Sie im Menü zu **Pflegeerinnerungen** → **Dashboard**.
2. Sie sehen alle aktuell fälligen und überfälligen Aufgaben.

### Schritt 2: Checkliste exportieren

1. Klicken Sie in der oberen Toolbar auf das **Drucker-Icon**.
2. Optional: Wählen Sie ein abweichendes Datum im erscheinenden Dialog (Standard: heute).
3. Klicken Sie auf **PDF erstellen**.
4. Der Download startet automatisch.

### Was ist in der Pflege-Checkliste enthalten?

Die Aufgaben sind nach Dringlichkeit gruppiert:

| Gruppe | Beschreibung |
|--------|-------------|
| Überfällig | Aufgaben, die vor dem gewählten Datum hätten erledigt werden sollen |
| Heute fällig | Aufgaben, die am gewählten Datum fällig sind |
| Demnächst fällig | Aufgaben der nächsten drei Tage (als Vorausschau) |

Jede Zeile enthält: Pflanzenname, Standort, fällige Pflegeaktion und eine leere Checkbox zum handschriftlichen Abhaken. Unterhalb jeder Pflanzenkarte gibt es Platz für Notizen.

!!! example "Beispiel: Checkliste für eine Urlaubsvertretung"
    Drucken Sie vor einem Urlaub die Checkliste für jeden Tag der Abwesenheit aus (mehrere Drucke mit verschiedenen Datumsangaben). Heften Sie die Blätter zusammen — Ihre Vertretung hat sofort eine klare tägliche Aufgabenliste.

---

## Pflanzen-Infokarten drucken

Pflanzen-Infokarten sind kompakte Kärtchen mit einem QR-Code, der direkt zur jeweiligen Pflanze in der App führt. Sie können selbst festlegen, welche Informationen auf der Karte erscheinen und in welchem Layout Sie drucken möchten.

### Was ist ein QR-Code auf der Karte?

Jede gedruckte Karte enthält einen QR-Code. Wenn Sie diesen Code mit einer Smartphone-Kamera scannen, öffnet sich direkt die Detailseite der Pflanze in Kamerplanter. So können Sie im Gewächshaus oder Garten sofort nachschlagen, in welcher Phase die Pflanze ist, wann zuletzt gegossen wurde und welche Aufgaben anstehen.

!!! note "Hinweis: App-Zugang erforderlich"
    Der QR-Code führt zu einer URL in Ihrer Kamerplanter-Instanz. Zum Öffnen muss auf dem Smartphone eine aktive Anmeldung in der App vorhanden sein.

### Einzelne Pflanze: Infokarte drucken

1. Öffnen Sie eine Pflanze unter **Pflanzdurchläufe** → Pflanz-Instanz → Detailansicht.
2. Klicken Sie auf das **QR-Code-Icon** in der Toolbar.
3. Der Konfigurationsdialog öffnet sich.

### Mehrere Pflanzen: Sammelausdruck

1. Navigieren Sie zur Pflanzenliste unter **Pflanzdurchläufe** → **Alle Pflanzen**.
2. Setzen Sie die Checkboxen links neben den gewünschten Pflanzen.
3. Klicken Sie in der Toolbar auf **Etiketten drucken** (QR-Code-Icon).
4. Der Konfigurationsdialog öffnet sich mit allen ausgewählten Pflanzen.

### Konfigurationsdialog

Der Dialog besteht aus vier Bereichen:

#### 1. Pflanzenauswahl

Hier sehen Sie die ausgewählten Pflanzen. Sie können weitere Pflanzen hinzufügen oder einzelne aus der Auswahl entfernen.

#### 2. Felder auswählen

Wählen Sie, welche Informationen auf jeder Karte gedruckt werden sollen:

| Feld | Standard | Beschreibung |
|------|----------|-------------|
| Pflanzenname | An | Anzeigename bzw. Sortenname |
| Wissenschaftlicher Name | An | Botanischer Name in Kursivschrift |
| Gattung / Familie | Aus | Taxonomische Einordnung |
| Pflanzdatum | An | Datum der Pflanzung |
| Aktuelle Phase | Aus | z.B. Vegetativ, Blüte |
| Standort | Aus | Raum, Zone oder Slot-Bezeichnung |
| Sorte | Aus | Sortenname, falls hinterlegt |
| Kurzhinweis | Aus | Freitext, z.B. "Kein Kalk" oder "Von unten gießen" |
| QR-Code | Immer an | Kann nicht abgewählt werden |

#### 3. Layout wählen

| Layout | Karten pro Blatt | Empfohlen für |
|--------|-----------------|---------------|
| Einzelkarte (A6) | 1 | Pflanzstecker, laminierte Karten |
| 2×4-Raster (A4) | 8 | Growraum-Beschriftung, Standardgebrauch |
| 3×3-Raster (A4) | 9 | Viele kleine Karten, Gemeinschaftsgarten |

Beim Raster-Layout sind Schnittmarken an den Kartenrändern gedruckt, damit Sie exakt schneiden können.

!!! tip "Tipp: QR-Code-Größe"
    Die Mindestgröße für zuverlässiges Scannen beträgt 20 × 20 mm. Beim 3×3-Raster ist der QR-Code bereits kleiner — testen Sie den Druck mit einem Smartphone-Scan, bevor Sie alle Karten ausschneiden.

#### 4. Vorschau und Download

Im unteren Bereich des Dialogs sehen Sie eine schematische Vorschau einer Karte mit den gewählten Feldern. Klicken Sie auf **PDF herunterladen**, um den Export zu starten.

---

## Tipps für den Praxiseinsatz

!!! tip "Laminieren für das Gewächshaus"
    Karten, die dauerhaft im Gewächshaus oder im Freien verwendet werden, sollten laminiert werden. Laminierhüllen in A6 und kleineren Formaten sind günstig im Bürobedarf erhältlich.

!!! tip "Wetterfeste Beetstecker"
    Drucken Sie die Karten auf etwas stärkerem Papier (120–160 g/m²) und stecken Sie sie in handelsübliche Pflanzen-Steckhalter aus Kunststoff oder Metall.

!!! tip "Schnittmarken nutzen"
    Beim Raster-Layout zeigt der Ausdruck dünne Schnittmarken an den Kartenrändern. Verwenden Sie ein Schneidlineal und einen Cutter für saubere Kanten — eine Schere führt auf langen geraden Schnitten oft zu leichten Versätzen.

---

## Häufige Fragen

??? question "Kann ich die Sprache des PDFs ändern?"
    Ja. Alle PDFs sind in Deutsch und Englisch verfügbar. Beim Nährstoffplan-PDF und der Pflege-Checkliste können Sie im Download-Dialog die Sprache wählen. Bei Pflanzen-Infokarten wird die Sprache der aktuellen App-Oberfläche verwendet.

??? question "Welches Papierformat verwendet das PDF?"
    Alle PDFs sind standardmäßig für A4 Hochformat optimiert, mit Ausnahme der Einzelkarte (A6). Das Papierformat ist fest vorgegeben und kann derzeit nicht geändert werden. Drucken Sie aus dem Betriebssystem-Dialog auf das korrekte Format.

??? question "Der QR-Code funktioniert nicht. Was kann ich tun?"
    Prüfen Sie zunächst, ob Sie auf Ihrem Smartphone in Kamerplanter angemeldet sind. Die URL im QR-Code zeigt auf Ihre eigene Kamerplanter-Instanz — wenn die App nicht erreichbar ist (z.B. weil Sie nur im lokalen Netzwerk arbeiten), kann der QR-Code außerhalb dieses Netzwerks nicht geöffnet werden.
    Wenn Sie im Homeoffice oder unterwegs scannen möchten, muss Ihre Kamerplanter-Instanz öffentlich erreichbar sein oder über ein VPN verbunden sein.

??? question "Kann ich eigene Felder zu den Infokarten hinzufügen?"
    Derzeit können Sie aus den acht vordefinierten Feldern wählen und ein freies Kurzhinweis-Textfeld nutzen. Vollständig benutzerdefinierte Felder sind für eine zukünftige Version geplant.

??? question "Kann ich den Nährstoffplan auch als CSV exportieren?"
    Der CSV-Export ist in Planung. Aktuell ist nur der PDF-Export für Nährstoffpläne verfügbar. Über die interaktive API-Dokumentation (`/docs`) können Sie bereits jetzt die Rohdaten des Plans als JSON abrufen.

??? question "Sind die PDFs barrierefrei?"
    Ja. Alle generierten PDFs enthalten ein Dokumenttitel-Tag, das Sprachattribut und sind als Tagged PDF strukturiert, was die Lesbarkeit für Screenreader verbessert.

---

## Siehe auch

- [Dünge-Logik](fertilization.md) — Nährstoffpläne anlegen und verwalten
- [Pflegeerinnerungen](care-reminders.md) — Pflegeprofile und fällige Aufgaben
- [Pflanzdurchläufe](planting-runs.md) — Pflanzinstanzen verwalten
- [Tankmanagement](tanks.md) — Nährlösungen anmischen
