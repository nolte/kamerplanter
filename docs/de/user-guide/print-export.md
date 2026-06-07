# Druckansichten & Export

Kamerplanter ermöglicht es dir, wichtige Pflegedaten als druckfertige PDFs zu exportieren. Ob Nährstoffplan für den Growraum, Pflege-Checkliste für den täglichen Rundgang oder Infokarten für jeden Topf — gedruckte Unterlagen helfen dort, wo ein Smartphone unpraktisch oder unerwünscht ist.

---

## Voraussetzungen

- Du bist als Mitglied eines Mandanten angemeldet (Rolle `viewer`, `grower` oder `admin`)
- Für den Nährstoffplan-Export: mindestens ein angelegter Nährstoffplan (→ [Dünge-Logik](fertilization.md))
- Für die Pflege-Checkliste: mindestens eine Pflanze mit aktivem Pflegeprofil (→ [Pflegeerinnerungen](care-reminders.md))
- Für Pflanzen-Infokarten: mindestens eine Pflanzinstanz (→ [Pflanzdurchläufe](planting-runs.md))

---

## Nährstoffplan drucken

Der Nährstoffplan als PDF enthält alle Phasen deines Mischplans auf einen Blick: welche Produkte du verwendest, wie viel von jedem Produkt pro Liter Wasser du einmessen musst, in welcher Reihenfolge du mischst und welchen EC- und pH-Wert die fertige Lösung haben soll.

### Schritt 1: Nährstoffplan öffnen

1. Navigiere im Menü zu **Dünge-Logik** → **Nährstoffpläne**.
2. Klicke auf den Namen des Plans, den du drucken möchtest.
3. Die Detailseite des Plans öffnet sich.

### Schritt 2: PDF erstellen

1. Klicke in der oberen Toolbar auf das **Drucker-Icon**.
2. Der Download startet automatisch — dein Browser speichert die PDF-Datei.

### Schritt 3: Sprache wählen (optional)

Die PDF wird standardmäßig auf Deutsch erstellt. Wenn du eine englische Version benötigst, hänge `?locale=en` an die Download-URL an oder wähle im Dialog die Sprache "Englisch".

### Was ist im Nährstoffplan-PDF enthalten?

| Abschnitt | Inhalt |
|-----------|--------|
| Kopfzeile | Planname, Erstellungsdatum, Mandant |
| Phasen-Tabelle | Phase, EC-Ziel, pH-Ziel, NPK-Verhältnis |
| Mischanleitungen | Pro Phase: Produkt, ml pro Liter, Mischreihenfolge |
| Wasser-Konfiguration | Basis-EC des Leitungswassers, RO-Anteil in % |
| Hinweise | CalMag-Korrektur-Empfehlung, Spülprotokoll |

!!! tip "Tipp: Im Growraum aufhängen"
    Laminiere das PDF und hänge es neben deinem Mischtisch auf. So hast du alle Informationen zum Anmischen griffbereit, ohne das Smartphone in feuchter Umgebung zu benutzen.

!!! warning "Mischsicherheit beachten"
    Das PDF zeigt die Mischreihenfolge in der Reihenfolge an, die CalMag-Ausfällungen verhindert (CalMag immer vor Sulfaten). Weiche nicht von dieser Reihenfolge ab.

---

## Pflege-Checkliste drucken

Die Pflege-Checkliste exportiert alle fälligen Pflegeaufgaben für einen gewählten Tag als druckbares PDF mit Checkboxen zum Abhaken. Ideal für den morgendlichen Rundgang durch Gewächshaus, Garten oder Wohnung.

### Schritt 1: Pflege-Dashboard öffnen

1. Navigiere im Menü zu **Pflegeerinnerungen** → **Dashboard**.
2. Du siehst alle aktuell fälligen und überfälligen Aufgaben.

### Schritt 2: Checkliste exportieren

1. Klicke in der oberen Toolbar auf das **Drucker-Icon**.
2. Optional: Wähle ein abweichendes Datum im erscheinenden Dialog (Standard: heute).
3. Klicke auf **PDF erstellen**.
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
    Drucke vor einem Urlaub die Checkliste für jeden Tag der Abwesenheit aus (mehrere Drucke mit verschiedenen Datumsangaben). Hefte die Blätter zusammen — deine Vertretung hat sofort eine klare tägliche Aufgabenliste.

---

## Pflanzen-Infokarten drucken

Pflanzen-Infokarten sind kompakte Kärtchen mit einem QR-Code, der direkt zur jeweiligen Pflanze in der App führt. Du kannst selbst festlegen, welche Informationen auf der Karte erscheinen und in welchem Layout du drucken möchtest.

### Was ist ein QR-Code auf der Karte?

Jede gedruckte Karte enthält einen QR-Code. Wenn du diesen Code mit einer Smartphone-Kamera scannst, öffnet sich direkt die Detailseite der Pflanze in Kamerplanter. So kannst du im Gewächshaus oder Garten sofort nachschlagen, in welcher Phase die Pflanze ist, wann zuletzt gegossen wurde und welche Aufgaben anstehen.

!!! note "Hinweis: App-Zugang erforderlich"
    Der QR-Code führt zu einer URL in deiner Kamerplanter-Instanz. Zum Öffnen muss auf dem Smartphone eine aktive Anmeldung in der App vorhanden sein.

### Einzelne Pflanze: Infokarte drucken

1. Öffne eine Pflanze unter **Pflanzdurchläufe** → Pflanz-Instanz → Detailansicht.
2. Klicke auf das **QR-Code-Icon** in der Toolbar.
3. Der Konfigurationsdialog öffnet sich.

### Mehrere Pflanzen: Sammelausdruck

1. Navigiere zur Pflanzenliste unter **Pflanzdurchläufe** → **Alle Pflanzen**.
2. Setze die Checkboxen links neben den gewünschten Pflanzen.
3. Klicke in der Toolbar auf **Etiketten drucken** (QR-Code-Icon).
4. Der Konfigurationsdialog öffnet sich mit allen ausgewählten Pflanzen.

### Konfigurationsdialog

Der Dialog besteht aus vier Bereichen:

#### 1. Pflanzenauswahl

Hier siehst du die ausgewählten Pflanzen. Du kannst weitere Pflanzen hinzufügen oder einzelne aus der Auswahl entfernen.

#### 2. Felder auswählen

Wähle, welche Informationen auf jeder Karte gedruckt werden sollen:

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

Beim Raster-Layout sind Schnittmarken an den Kartenrändern gedruckt, damit du exakt schneiden kannst.

!!! tip "Tipp: QR-Code-Größe"
    Die Mindestgröße für zuverlässiges Scannen beträgt 20 × 20 mm. Beim 3×3-Raster ist der QR-Code bereits kleiner — teste den Druck mit einem Smartphone-Scan, bevor du alle Karten ausschneidest.

#### 4. Vorschau und Download

Im unteren Bereich des Dialogs siehst du eine schematische Vorschau einer Karte mit den gewählten Feldern. Klicke auf **PDF herunterladen**, um den Export zu starten.

---

## Tipps für den Praxiseinsatz

!!! tip "Laminieren für das Gewächshaus"
    Karten, die dauerhaft im Gewächshaus oder im Freien verwendet werden, sollten laminiert werden. Laminierhüllen in A6 und kleineren Formaten sind günstig im Bürobedarf erhältlich.

!!! tip "Wetterfeste Beetstecker"
    Drucke die Karten auf etwas stärkerem Papier (120–160 g/m²) und stecke sie in handelsübliche Pflanzen-Steckhalter aus Kunststoff oder Metall.

!!! tip "Schnittmarken nutzen"
    Beim Raster-Layout zeigt der Ausdruck dünne Schnittmarken an den Kartenrändern. Verwende ein Schneidlineal und einen Cutter für saubere Kanten — eine Schere führt auf langen geraden Schnitten oft zu leichten Versätzen.

---

## Häufige Fragen

??? question "Kann ich die Sprache des PDFs ändern?"
    Ja. Alle PDFs sind in Deutsch und Englisch verfügbar. Beim Nährstoffplan-PDF und der Pflege-Checkliste kannst du im Download-Dialog die Sprache wählen. Bei Pflanzen-Infokarten wird die Sprache der aktuellen App-Oberfläche verwendet.

??? question "Welches Papierformat verwendet das PDF?"
    Alle PDFs sind standardmäßig für A4 Hochformat optimiert, mit Ausnahme der Einzelkarte (A6). Das Papierformat ist fest vorgegeben und kann derzeit nicht geändert werden. Drucke aus dem Betriebssystem-Dialog auf das korrekte Format.

??? question "Der QR-Code funktioniert nicht. Was kann ich tun?"
    Prüfe zunächst, ob du auf deinem Smartphone in Kamerplanter angemeldet bist. Die URL im QR-Code zeigt auf deine eigene Kamerplanter-Instanz — wenn die App nicht erreichbar ist (z.B. weil du nur im lokalen Netzwerk arbeitest), kann der QR-Code außerhalb dieses Netzwerks nicht geöffnet werden.
    Wenn du im Homeoffice oder unterwegs scannen möchtest, muss deine Kamerplanter-Instanz öffentlich erreichbar sein oder über ein VPN verbunden sein.

??? question "Kann ich eigene Felder zu den Infokarten hinzufügen?"
    Derzeit kannst du aus den acht vordefinierten Feldern wählen und ein freies Kurzhinweis-Textfeld nutzen. Vollständig benutzerdefinierte Felder sind für eine zukünftige Version geplant.

??? question "Kann ich den Nährstoffplan auch als CSV exportieren?"
    Der CSV-Export ist in Planung. Aktuell ist nur der PDF-Export für Nährstoffpläne verfügbar. Über die interaktive API-Dokumentation (`/docs`) kannst du bereits jetzt die Rohdaten des Plans als JSON abrufen.

??? question "Sind die PDFs barrierefrei?"
    Ja. Alle generierten PDFs enthalten ein Dokumenttitel-Tag, das Sprachattribut und sind als Tagged PDF strukturiert, was die Lesbarkeit für Screenreader verbessert.

---

## Siehe auch

- [Dünge-Logik](fertilization.md) — Nährstoffpläne anlegen und verwalten
- [Pflegeerinnerungen](care-reminders.md) — Pflegeprofile und fällige Aufgaben
- [Pflanzdurchläufe](planting-runs.md) — Pflanzinstanzen verwalten
- [Tankmanagement](tanks.md) — Nährlösungen anmischen
