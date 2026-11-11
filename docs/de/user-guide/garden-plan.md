# Gartenplan

Der Gartenplan zeigt deinen Garten von oben: Beete und Gartenobjekte wie Wege, Zäune und Bäume im richtigen Maßstab. Hier zeichnest du, verschiebst und bepflanzt Beete, siehst auf einen Blick, wo etwas zu tun ist, und sicherst oder druckst den Plan.

---

## Voraussetzungen

- Ein Standort (Site) in deinem Garten. Wie du ihn anlegst, steht unter [Standorte und Substrate](locations-substrates.md).
- Zum Ansehen genügt jede Rolle. Zum Zeichnen und Speichern brauchst du mindestens die Rolle „grower" (Gärtner:in), siehe [Wer darf was](#wer-darf-was).
- Ein Plan, der eine Gartengrenze hat (siehe [Die Gartengrenze](#die-gartengrenze)).

## Den Gartenplan öffnen

Öffne unter **Standorte** den Standort und klicke auf **Gartenplan öffnen**. Die Seite trägt die Adresse `/standorte/sites/<Schlüssel>/plan`. Auf einem schmalen Bildschirm (unter 600 Pixel Breite) öffnet sie direkt im [Feldmodus](#feldmodus-im-garten); sonst startet der Planungsmodus. Über **Feldmodus** bzw. **Planungsmodus** oben auf der Seite wechselst du jederzeit.

Der Planungsmodus ist eine Arbeitsfläche wie in einem Zeichenprogramm. Die Zeichenfläche bekommt so viel Platz wie möglich:

- **Kopfleiste:** Eine einzige Zeile über dem Plan. Sie enthält **Zurück** zum Standort, **Rückgängig** und **Wiederholen**, den Speicher-Stand mit **Speichern**, die Tabs **Plan**, **Liste** und **Beete**, den Wechsel in den Feldmodus und den Schalter für das Seitenpanel. Seltene Aktionen liegen im Menü **⋮** (Mehr): Tastaturhilfe, Unterlage, Alles auswählen, Export und Import und, wenn genau ein Beet gewählt ist, **Als Vorlage speichern**. Wird das Fenster schmaler, wandern zuerst der Schalter **Automatisch speichern**, dann der Feldmodus-Wechsel, der Panel-Schalter und zuletzt die Tabs ins Menü. **Speichern** bleibt immer sichtbar.
- **Tabs Plan · Liste · Beete:** **Plan** zeigt die Zeichenfläche, **Liste** denselben Plan als Liste (ohne Maus und Zeichenfläche bedienbar), **Beete** die [Beetliste](#beetliste-im-gartenplan). Der gewählte Tab steht in der Adresse (`?tab=plan`, `list` oder `beds`). Ein Link öffnet also direkt den richtigen Tab, und **Zurück** im Browser führt zum vorigen Tab. Beim Wechsel zwischen den Tabs bleiben ungespeicherte Änderungen, Auswahl und Ausschnitt erhalten, und es kommt keine Rückfrage.
- **Werkzeug-Leiste:** links neben der Zeichenfläche, senkrecht (siehe [Werkzeuge und Formen](#werkzeuge-und-formen)).
- **Zeichenfläche:** füllt die Höhe des Fensters. Zoom, **Anpassen**, Maßstabsbalken und die Übersichtskarte liegen in den Ecken über dem Plan.
- **Seitenpanel:** rechts, mit den Tabs **Eigenschaften**, **Ansicht**, **Ebenen** und **Zonen** (siehe [Eigenschaften, Seitenpanel und Listenansicht](#eigenschaften-und-listenansicht)). Ohne Auswahl ist es eingeklappt und nimmt keinen Platz weg.

**Auf Tablet und Telefon.** Ab 768 Pixel Breite steht das Seitenpanel neben dem Plan; der Plan wird schmaler und schiebt ein ausgewähltes Beet ins Bild. Unter 768 Pixeln wird die Werkzeug-Leiste zur Leiste unter dem Plan, und das Seitenpanel öffnet sich als Blatt von unten (halbe oder volle Höhe). In der Kopfleiste bleiben dann nur **Zurück**, der Speicher-Stand, **Speichern** und **⋮**; **Rückgängig** und **Wiederholen** stehen in der Leiste unter dem Plan. Mit einem Touchscreen siehst du die Touch-Leiste (Punkt setzen, Mehrfachauswahl) auf jeder Breite. <!-- REQ-053 GP-UX-063, GP-UX-064, GP-UX-065, GP-UX-067, GP-UX-068, GP-UX-069 -->

### Die Gartengrenze {#die-gartengrenze}

Jeder Plan hat eine Gartengrenze: den Umriss deines Gartens als Rechteck oder Vieleck. Beete und Gartenobjekte müssen ganz innerhalb liegen. Ein Standort ohne Grenze und ohne eingezeichnete Objekte zeigt statt des Editors den Hinweis **Noch kein Gartenplan**.

!!! note "Teilweise verfügbar: Gartengrenze"
    Die Oberfläche hat noch kein Werkzeug, mit dem du die Gartengrenze zeichnest. Den ersten Plan legst du über die Programmierschnittstelle an (siehe [Für technische Nutzer / Self-Hoster](#fur-technische-nutzer-self-hoster)) oder du spielst eine Sicherung ein (siehe [Plan exportieren und Sicherung einspielen](#plan-export-import)). Ist die Grenze einmal da, ändert sich nur noch ihre Nordrichtung im Editor: Das Kompass-Feld stellt ein, wo geografisch Norden auf dem Plan liegt. Auch **Grundriss zeichnen** im leeren [Wohnungsplan](#wohnungsplan) öffnet nur die leere Zeichenfläche; einen Umriss zeichnest du dort noch nicht. <!-- REQ-053 GP-FR-013, GP-FR-015, GP-FR-182 -->

### Wer darf was {#wer-darf-was}

Deine Rolle gilt immer für den Garten (Mandanten), in dem du gerade arbeitest.

| Tätigkeit | viewer (Beobachter:in) | grower (Gärtner:in) | lead (Leitung) |
|-----------|:----------------------:|:-------------------:|:--------------:|
| Plan ansehen, Beetliste, Feldmodus lesen | ja | ja | ja |
| Export als PDF, SVG, Sicherung (JSON) und Beetliste (CSV) | ja | ja | ja |
| Beete und Objekte zeichnen, verschieben, ändern, sperren, speichern | nein | ja | ja |
| Beete und Objekte löschen | nein | nein | ja |
| Bepflanzen, Aufgaben erledigen | nein | ja | ja |
| Bewässerungszonen anlegen und ändern, Gießrunde protokollieren | nein | ja | ja |
| Bewässerungszone löschen | nein | nein | ja |
| Beetvorlage speichern, Unterlage setzen oder entfernen | nein | ja | ja |
| Beetvorlage löschen | nein | nein | ja |
| Sicherung einspielen, früheren Stand wiederherstellen, neue Saison anlegen | nein | nein | ja |

!!! note "Hinweis"
    Der Editor blendet Werkzeuge nicht aus, die deine Rolle nicht darf. Der Server prüft beim Speichern. Ein Stapel von Änderungen, der auch nur eine Löschung enthält, wird als Ganzes abgelehnt, wenn du nicht die Rolle „lead" hast; du siehst dann die Meldung **Speichern nicht erlaubt** und machst die Änderung rückgängig. Lösche bei Bedarf nur als Leitung.

## Zeichnen und bearbeiten

### Werkzeuge und Formen {#werkzeuge-und-formen}

Die Werkzeug-Leiste links neben dem Plan bietet vier Werkzeuge. Jedes hat einen Tooltip; auf breiten Bildschirmen steht der Name daneben.

| Werkzeug | Was es tut |
|----------|-----------|
| **Auswählen** | Klicken wählt ein Objekt, ein Rahmen wählt mehrere, mit der Umschalttaste fügst du Objekte hinzu. Gewählte Objekte verschiebst du durch Ziehen. |
| **Ansicht verschieben** | Zieht die Ansicht, ohne etwas zu ändern. |
| **Beet zeichnen** ▸ | Zeichnet ein neues Beet. Das kleine Menü daneben bietet **Aus Vorlage** (ein Beet aus einer [Vorlage](#beetvorlagen) setzen) und **Mit Maßen hinzufügen**. |
| **Objekt: Gartenobjekt zeichnen** ▸ | Zeichnet ein Gartenobjekt wie Weg, Zaun, Baum, Rankhilfe, Kompost oder im Wohnungsplan Fenster, Tür, Möbel und Lampe. Das Menü daneben bietet **Mit Maßen hinzufügen**. |

Unter den Werkzeugen erscheint die **Auswahlgruppe** nur, solange etwas gewählt ist: **Drehraster** (15°, 45°, 90°), **Ausrichten** und **Löschen**.

!!! note "Teilweise verfügbar: Werkzeuge"
    Vier weitere Werkzeuge sind geplant, aber noch nicht gebaut: **Bereich**, **Pflanze setzen**, **Messen** und **Beschriftung**. Bis dahin legst du Bereiche über die Programmierschnittstelle oder eine Sicherung an und bepflanzt Beete über **Bepflanzen**. <!-- REQ-053 GP-UX-001, GP-UX-066, GP-UX-071, #2913 -->

Als **Form** wählst du Rechteck, Kreis, Vieleck oder Linie. Das Rechteck ziehst du auf (mit der Umschalttaste wird es ein Quadrat), den Kreis ziehst du vom Mittelpunkt nach außen. Beim Vieleck und bei der Linie klickst du Punkt für Punkt; mit **Fertig**, der Eingabetaste oder einem Klick auf den ersten Punkt schließt du das Vieleck, die Linie beendest du mit **Fertig** oder der Eingabetaste. Die Rücktaste nimmt den letzten Punkt zurück, **Esc** verwirft die Form.

Zu jedem Objekt zeigt der Plan Breite, Länge (beim Kreis den Durchmesser) und Fläche. **Mit Maßen hinzufügen** legt ein Beet oder Objekt mit eingetippten Maßen an, auch ohne Zeichnen.

Der Name eines Beets oder Objekts steht in seiner Mitte, bei einem Vieleck an der Stelle mit dem meisten Platz zu allen Rändern, damit er auch in einem Winkelbeet im Beet bleibt. Ist der Name zu lang, kürzt der Plan ihn mit „…“. Überdecken sich zwei Namen, bleibt der des größeren Objekts stehen. Im PDF und in der SVG steht der Name an derselben Stelle. <!-- REQ-053 GP-UX-047 -->

Ein gewähltes Objekt hat Griffe: Die Ecken ändern die Größe, der Drehgriff dreht das Objekt. Das **Drehraster** rastet beim Drehen alle 15, 45 oder 90 Grad ein; mit gehaltener Alt-Taste drehst du frei. Bei einem Vieleck fügst du über **Punkt einfügen** einen Punkt hinzu und entfernst einen mit **Punkt löschen**.

Die Maße des gewählten Objekts stehen außerhalb über seiner Oberkante und weichen den Griffen aus. Ist ein Objekt auf dem Bildschirm zu klein für Griffe, erscheint ein Hinweis mit **Zum Bearbeiten heranzoomen**: Der Plan zoomt um das Objekt herum so weit hinein, dass alle Griffe erscheinen. <!-- REQ-053 GP-UX-047, GP-UX-048 -->

### Mit der Maus

- Klicken wählt, Ziehen verschiebt, ein Rahmen über freier Fläche wählt alles, was ganz im Rahmen liegt (gesperrte Objekte nicht).
- Mit **Strg** (am Mac **Cmd**) und dem Mausrad zoomst du stufenlos um den Zeiger; liegt der Fokus auf dem Plan, genügt das Mausrad. Ein einfaches Mausrad blättert die Seite.
- Ein Rechtsklick auf ein Objekt (auf dem Touchscreen die Schaltfläche **⋯** im Eigenschaften-Feld) öffnet die Aktionen des Objekts: Bearbeiten, Duplizieren, In den Vordergrund, In den Hintergrund, Sperren. Für das Duplizieren gibt es keine Tastenkombination; die Kopie eines Beets hat keine Pflanzplätze.
- Mit gehaltener **Alt**-Taste schaltest du das Einrasten kurz aus.

### Auf dem Touchscreen

- Mit **zwei Fingern** verschiebst und zoomst du den Plan.
- Ein Objekt wählst du mit einem Tipp. Zum Verschieben hältst du den Finger etwa eine halbe Sekunde auf dem Objekt; ein Ring zeigt, dass es nun bewegt wird. Wischst du früher, verschiebst du stattdessen die Ansicht.
- **Mehrfachauswahl** schaltest du als Schaltfläche ein. Dann tippst du Objekte an oder ziehst über freier Fläche einen Rahmen.
- Beim Zeichnen schiebst du den Plan mit zwei Fingern, bis das Fadenkreuz auf dem gewünschten Punkt liegt, und tippst auf **Punkt setzen**. **Rückgängig** nimmt den Punkt zurück, **Fertig** schließt die Form, **Abbrechen** verwirft sie. Sehr breite Berührungen (eine Handfläche) und ein zweiter Finger unmittelbar nach dem ersten ignoriert der Plan.

### Mit der Tastatur

Der Plan ist ohne Maus bedienbar. **Tastaturhilfe** im Menü **⋮** (oder die Taste **?**) listet alle Tasten. Die wichtigsten:

| Taste | Wirkung |
|-------|---------|
| Pfeiltasten | Verschieben die Auswahl um einen Rasterschritt; ohne Auswahl scrollen sie die Ansicht |
| Umschalt + Pfeiltasten | Zehn Schritte auf einmal |
| Bild ab / Bild auf | Fokussieren das nächste oder vorherige Objekt |
| Eingabe / Leertaste | Wählt das fokussierte Objekt; Eingabe schließt auch ein Vieleck ab |
| Entf | Löscht die Auswahl nach Rückfrage |
| Esc | Bricht Laufendes ab, danach hebt es die Auswahl auf |
| Strg + A | Wählt alle nicht gesperrten Objekte |
| Strg + Z | Rückgängig |
| Strg + Umschalt + Z oder Strg + Y | Wiederholen |
| Strg + S | Speichern |
| + / − / 0 | Vergrößern, Verkleinern, ganzen Plan zeigen |
| G | Raster ein- oder ausblenden |

Tab verlässt den Plan; alle Objekte und Aktionen erreichst du in der Listenansicht. Die Einzeltasten **?**, **G**, **+**, **−** und **0** kannst du in der Tastaturhilfe ausschalten, falls sie dich stören. Am Anfang der Seite stehen Sprunglinks zur Objektliste, zum Plan und zum Eigenschaften-Feld.

### Raster, Einrasten, Zoom und Kompass

Raster, Einrasten, Längeneinheit und Kompass findest du im Seitenpanel im Tab **Ansicht**. Zoom und **Anpassen** liegen oben rechts auf der Zeichenfläche.

- **Raster:** Die Rasterstufen sind 1 cm, 5 cm, 10 cm, 25 cm, 50 cm und 1 m; ein neuer Gartenplan beginnt mit 10 cm, ein Wohnungsplan mit 5 cm. Bei kleinem Zoom zeichnet der Plan nur die Stufen, deren Linien weit genug auseinander liegen. Mit **Raster anzeigen** (oder **G**) blendest du die Linien aus; das Einrasten bleibt davon unberührt.
- **Einrasten:** Der Schalter **Einrasten** lässt Objekte beim Verschieben, Zeichnen und Ziehen der Griffe am Raster und an Ecken und Kanten anderer Objekte einrasten.
- **Längeneinheit:** Du wählst Meter oder Zentimeter für alle Maßangaben im Editor. Gespeichert wird immer in Metern.
- **Zoom:** Die festen Stufen sind 25, 50, 100, 200 und 400 Prozent; **Anpassen** zeigt den ganzen Plan. Der Maßstabsbalken zeigt, wie lang eine Strecke auf dem Plan ist.
- **Kompass:** Stelle den **Nordwinkel** ein, damit der Plan weiß, wo geografisch Norden liegt: durch Drehen des Zifferblatts, mit den Pfeiltasten oder durch Eintippen (0 bis unter 360 Grad im Uhrzeigersinn; 0 heißt: Norden ist oben). Der Kompass im Handy liefert magnetisch Nord; Kamerplanter übernimmt ihn deshalb nie automatisch.
- **Übersichtskarte:** siehe [Im Gartenplan schneller arbeiten](#plan-komfort).

### Eigenschaften, Seitenpanel und Listenansicht {#eigenschaften-und-listenansicht}

Das **Seitenpanel** hat vier Tabs:

| Tab | Inhalt |
|-----|--------|
| **Eigenschaften** | Das gewählte Beet oder Objekt (siehe unten). |
| **Ansicht** | Rasterstufe, Raster, Einrasten, Längeneinheit und Kompass. |
| **Ebenen** | Die [Ebenen](#ebenen-und-standortbedingungen) mit ihren Schaltern, der Filter für Handlungsbedarf, die Legende und die Zonenlegende. |
| **Zonen** | Die [Bewässerungszonen](#bewasserungszonen) verwalten. |

Wählst du etwas aus, öffnet sich das Panel auf **Eigenschaften**. Hebst du die Auswahl auf, klappt es wieder ein, wenn es sich durch die Auswahl geöffnet hatte. Hast du es selbst über den Panel-Schalter in der Kopfleiste geöffnet, bleibt es offen; hast du es selbst geschlossen, bleibt es zu, bis du es öffnest oder etwas Neues wählst. Ohne Auswahl öffnet es auf dem zuletzt benutzten Tab, beim ersten Mal auf **Ansicht**. Die Tabs erreichst du auch mit der Tastatur: Pfeiltasten wechseln den Tab.

Der Tab **Eigenschaften** zeigt zum gewählten Beet oder Objekt Name, Typ, Position (x nach rechts, y nach oben, in Metern), Maße und Drehung gegen den Uhrzeigersinn. Du änderst die Werte direkt; über **Sperren** schützt du ein Objekt vor versehentlichem Verschieben. Bei einem Beet findest du hier auch **Bepflanzen**, die Sonnen-Kacheln und die Zahl der offenen und überfälligen Aufgaben mit einem Sprung zum Pflege-Tab. Bei einem Vieleck listet das Feld die Punkte.

Bei einem Gartenobjekt zeigt der Tab die **Objekteigenschaften** seiner Art: bei einer **Rankhilfe** die Höhe, bei einem **Fenster** Brüstungshöhe, Verglasung und die Himmelsrichtung, die Kamerplanter aus der Lage in der Wand und dem Nordwinkel ableitet (nur lesend), bei einer **Tür** die Öffnungsrichtung, bei einer **Lampe** Art, Montagehöhe und einen Referenzwert für die Lichtstärke (Kamerplanter rechnet daraus noch nichts). Der Schalter **Außerhalb des Grundstücks** markiert ein Objekt wie Nachbars Baum: Es darf über die Gartengrenze hinausragen und wird als Kulisse gezeichnet. Ausschalten geht nur, wenn das Objekt ganz im Garten liegt. Die Objekt-Legende im Tab **Ebenen** erklärt die Zeichen aller Objektarten auf dem Plan. Bei **Kompost**, **Wasserquelle** und **Lager** gibt es außerdem den Abschnitt [Aufgaben](#aufgaben-an-gartenobjekten). <!-- REQ-053 GP-FR-180 -->

Der Tab **Liste** zeigt dieselben Objekte als Liste mit Bereichen, Beeten und Gartenobjekten. Zu jedem Eintrag gibt es Verschieben-Schaltflächen, die Eingabe einer Zielposition und Löschen. Sie ist die Alternative für Bildschirmleser und für alle, die nicht zeichnen wollen.

## Im Gartenplan schneller arbeiten {#plan-komfort}

Dieser Abschnitt beschreibt die Hilfen, die dir im Planungsmodus Handarbeit abnehmen.

**Beet aus einer Vorlage.** In der Werkzeugleiste setzt **Aus Vorlage** ein Beet mit einem Klick auf den Plan. Du wählst eine Vorlage, drehst sie bei Bedarf mit **Drehen** in 90-Grad-Schritten und klickst dorthin, wo das Beet liegen soll (bei einem Rechteck die untere linke Ecke, bei einem Kreis der Mittelpunkt). Eine gestrichelte Vorschau zeigt, wo es landet; sie wird rot, wenn das Beet dort nicht ganz in den Garten passt. Ohne Maus setzt **In die Bildmitte setzen** das Beet mit seiner Mitte in die Mitte der Ansicht. Das Beet bekommt Name, Typ, Form und Höhe der Vorlage und wird sofort gespeichert; ungespeicherte Änderungen speichert Kamerplanter vorher mit. Dieser Schritt lässt sich nicht mit **Rückgängig** zurücknehmen. Wenn du das Beet nicht willst, löschst du es. Mit **Esc** oder einem anderen Werkzeug beendest du die Vorlagenwahl.

**Standardgrößen.** Im Dialog **Mit Maßen hinzufügen** füllt eine Standardgröße Form, Maße, Beettyp und Höhe auf einen Schlag aus, zum Beispiel das Hochbeet 1,2 × 2,4 m, das Hochbeet 2 × 1 × 0,8 m oder einen Kübel. Du kannst danach jeden Wert noch ändern. Die Höhe ist optional.

**Als Vorlage speichern.** Ist genau ein Beet gewählt, speichert **Als Vorlage speichern** seine Form, seinen Typ und seine Höhe als eigene Vorlage deines Gartens. Pflanzen, Aufgaben und Notizen gehören nicht dazu, und Pflanzabstände oder Bodenwerte trägt die Vorlage nur, wenn du sie selbst einträgst. Vorlagen legen Gärtner und die Leitung an.

**Einrasten an anderen Objekten.** Beim Verschieben und Zeichnen rastet der Plan an Ecken und Kanten anderer Objekte ein, bevor er am Raster einrastet. Beim Verschieben rastet jede Ecke des Beets ein, auch wenn es gedreht ist, nicht nur die Stelle unter dem Mauszeiger: So legst du die rechte Kante eines Beets genau an die linke Kante des nächsten. Bei einem runden Beet rasten der Mittelpunkt und die vier Randpunkte ganz oben, unten, links und rechts ein. Ein grüner Ring zeigt den Punkt, der einrastet, eine grüne Linie die Kante, an der er liegt. Mit der Alt-Taste oder dem Schalter **Einrasten** schaltest du das Einrasten aus. Mit Stift und Finger ist der Fangbereich größer.

**Ausrichten und verteilen.** Hast du mindestens zwei Beete oder Objekte gewählt, richtet **Ausrichten** sie an der linken, rechten, oberen oder unteren Kante oder an der Mitte aus. Ab drei Objekten verteilt der Menüpunkt **Gleichmäßig verteilen** sie mit gleichen Abständen; die beiden äußersten Objekte bleiben dabei stehen. Gesperrte Objekte bleiben stehen und zählen nicht mit. Stehen die Objekte nebeneinander oder versetzt, verteilt Kamerplanter sie auch dann, wenn sie sich in dieser Richtung überschneiden. Würden zwei von ihnen dabei aufeinander liegen, etwa weil sie genau übereinander stehen, oder würde eines auf einem gesperrten Objekt landen, verteilt Kamerplanter nichts und sagt dir, warum. Jede dieser Aktionen ist ein einziger Schritt für **Rückgängig**.

**Übersichtskarte.** Ist der Garten sehr viel größer als der sichtbare Ausschnitt (mehr als das Vierfache), erscheint unten rechts im Plan eine kleine Karte mit dem Ausschnitt als Rechteck. Ein Klick darauf springt die Ansicht an diese Stelle. Mit der Tastatur bewegst du den Plan weiter mit den Pfeiltasten.

**Automatisch speichern.** Der Schalter **Automatisch speichern** neben **Speichern** sichert deine Änderungen zwei Sekunden nach der letzten Änderung. Er ist standardmäßig aus und gilt nur für dich in diesem Browser. Bei einem Konflikt oder einem abgelehnten Speichern pausiert er und sagt es dir. Im Feldmodus gibt es ihn nicht, dort wird jede Aktion sofort gesendet.

**Mehrfach duplizieren.** Über das Menü **⋯** oder das Kontextmenü legt **Mehrfach duplizieren** mehrere Kopien der gewählten Beete in einer Reihe an: Anzahl, Richtung, Abstand und ein Namensschema wie „Parzelle {n}" (bis zu 100 Kopien). Den Abstand gibst du in der Längeneinheit ein, die du für den Plan gewählt hast (m oder cm). Das ist praktisch für die Parzellen eines Gemeinschaftsgartens. Kamerplanter prüft vorher, ob die Kopien ganz in den Garten passen und ob die Höchstzahl von 500 Beeten und Objekten reicht; wenn nicht, entsteht nichts. Passt eine Kopie nicht in den Garten, nennt der Dialog die erste, die nicht passt. Alle Kopien lassen sich mit einem **Rückgängig** zurücknehmen. Pflanzplätze, Pflanzen und Aufgaben werden nicht mitkopiert; ein Pflanzraster legst du danach für jedes Beet an. <!-- REQ-053 GP-FR-025, GP-FR-029, GP-FR-043, GP-FR-044, GP-FR-045, GP-FR-154, GP-UX-004, GP-UX-014 -->

## Speichern, Konflikte und Rückgängig

Änderungen im Editor werden zuerst nur lokal angewandt. Die Kopfleiste zeigt den Stand (auf schmalen Bildschirmen als Zeichen mit Zähler): **Ungespeicherte Änderungen (n)**, **Speichern …**, **Gespeichert**, **Konflikt** oder **Speichern fehlgeschlagen**. **Speichern** (oder **Strg + S**) schickt alle offenen Änderungen in einem Schritt zum Server: Entweder werden alle übernommen oder keine. Der Schalter **Automatisch speichern** erledigt das für dich, siehe unten.

- **Rückgängig und Wiederholen** (Strg + Z, Strg + Umschalt + Z) gelten für die letzten 100 Schritte. Der Verlauf gilt nur für diese Sitzung: Lädst du die Seite neu, ist er weg.
- **Konflikt:** Hat jemand anderes den Plan gespeichert, während du daran gearbeitet hast, nimmt der Server deine Änderungen nicht an. Ein Dialog nennt, wer zuletzt geändert hat. Du kannst deine Änderungen vorher als Kopie (JSON) herunterladen und dann **Neu laden**. Beim Neuladen gehen deine ungespeicherten Änderungen und der Rückgängig-Verlauf verloren.
- **Abgelehnt:** Verletzt eine Änderung eine Regel, lehnt der Server das ganze Speichern ab und die Meldung nennt die Stelle. Häufige Gründe: Zwei Beete überlappen sich, ein Objekt ragt aus der Gartengrenze, auf einem Beet wachsen noch Pflanzen (Löschen erst nach dem Räumen), mehr als 500 Änderungen sind offen, oder der Plan hat sein Limit von 500 Standorten und Objekten zusammen erreicht. Korrigiere die genannte Stelle oder mache sie rückgängig; deine übrigen Änderungen bleiben erhalten.
- **Löschen:** Solange du nicht gespeichert hast, kannst du Löschen rückgängig machen. Nach dem Speichern nicht mehr. Der Dialog nennt vorher, was mit gelöscht wird.

## Ein Beet bepflanzen {#ein-beet-bepflanzen}

Wähle ein Beet und klicke im Eigenschaften-Feld auf **Bepflanzen**. Es öffnet sich der Pflanzdialog, den du auch aus der Beetansicht kennst. Du wählst Art und Sorte, siehst Hinweise zu Fruchtfolge, Nachbarn und Standort, legst die Anordnung fest (Raster, Reihen, Versetzt, Fläche oder Freie Positionen), siehst eine Vorschau und planst die Pflanzung oder erfasst sie sofort. Mit der Rolle „grower" ist das möglich, das Beet muss im Plan stehen und darf nicht stillgelegt sein. Die Schritte stehen unter [Beet bepflanzen](locations-substrates.md#beet-bepflanzen).

Pflanzen erscheinen auf dem Plan als Marker. Die Zustandsebene beschreibt der Abschnitt [Pflanzenzustand und Filter](#pflanzenzustand-und-filter).

**Rankhilfe.** Braucht eine Art eine Rankhilfe (etwa Erbse oder Stangenbohne), sagt dir der Pflanzdialog, welche Rankhilfen im Beet oder an seinem Rand eingezeichnet sind, mit ihrer Höhe. Ist keine eingezeichnet, weist er darauf hin; pflanzen kannst du trotzdem. Bei Arten ohne diese Angabe erscheint kein Hinweis. <!-- REQ-053 W-005 -->

### Säen, vereinzeln und nachpflanzen {#saen-vereinzeln-nachpflanzen}

Im Tab **Pflanzung** der Beetansicht gilt für Reihen und Flächen, die du direkt säst:

1. **Als gesät erfassen:** An einer geplanten Reihe oder Fläche erfasst du den Tag der Aussaat (höchstens ein Jahr zurück, nicht in der Zukunft). Es entstehen noch keine einzelnen Pflanzen; die Reihe steht unter **Gesät** mit ihrem Datum, und der Pflanzenzustand zeigt sie mit Saatpunkten.
2. **Vereinzeln:** Sobald die Sämlinge stehen, ziehst du die überzähligen heraus und tippst auf **Vereinzeln**. Der Dialog nimmt den Abstand aus dem Anbauplan, den du ändern kannst, und berechnet daraus mit der Reihenlänge oder Fläche die Zahl der Pflanzen. Fehlt ein Abstand, fragt er nach dem Abstand oder direkt nach der Zahl der stehen gebliebenen Pflanzen; Kamerplanter setzt keinen Wert von selbst ein. Danach sind die Pflanzen einzeln erfasst, die Reihe gilt nicht mehr als gesät, und das Pflegeprotokoll erhält einen Eintrag „Vereinzeln“.
3. **Nachpflanzen:** Ist eine Pflanze eingegangen (beim Entfernen als „eingegangen“ erfasst, nicht „abgestorben (planmäßig)“), steht ihr Platz unter **Ausgefallen**. **Nachpflanzen** öffnet den Bepflanzen-Dialog mit derselben Kultur und ihrem Abstand. Eine Pflanze, die am Ende ihrer Zeit abgeräumt wurde, gilt nicht als ausgefallen und bekommt kein **Nachpflanzen**.

!!! note "Teilweise verfügbar: Säen und Nachpflanzen"
    Gesäte Reihen und Flächen erscheinen im Tab **Pflanzung**, im Pflanzenzustand und in der Legende, aber noch nicht als Linie oder Fläche auf der Zeichenfläche und nicht im PDF oder in der SVG. Beim Nachpflanzen derselben Kultur warnt der Fruchtfolge-Hinweis derzeit vor der eingegangenen Pflanze selbst; prüfe den Hinweis dann mit Augenmaß. <!-- REQ-053 W-015, §11.3, #2888 -->

## Beetliste im Gartenplan {#beetliste-im-gartenplan}

Der Tab **Beete** (im Wohnungsplan **Pflanzplätze**) listet in einer Tabelle deine Beete: Name (als Link zur Beetansicht), Typ, Fläche, Status, Zuständige, Pflanzen, offene Aufgaben (mit überfälligen) und nächste Fälligkeit. Stillgelegte Beete sind standardmäßig ausgeblendet. Der Schalter **Meine Beete** filtert auf deine Beete und setzt voraus, dass dir Beete zugewiesen sind.

Klickst du auf eine Zeile oder drückst die Eingabetaste, wechselt die Seite in den Tab **Plan**, das Beet ist ausgewählt und die Ansicht zoomt darauf. Nach jedem Speichern zeigt die Liste den gespeicherten Stand. Die Zahl in der Spalte „Offene Aufgaben" ist ein Link zum Pflege-Tab des Beets. Ab der Rolle „grower" findest du über der Tabelle die Schaltfläche **Aufgaben auf mehreren Beeten erledigen** (siehe [Pflege am Beet](locations-substrates.md#pflege-am-beet)).

## Aufgaben an Gartenobjekten {#aufgaben-an-gartenobjekten}

Auch ein Kompost, eine Wasserquelle oder ein Lager braucht Arbeit: den Kompost umsetzen, die Regentonne winterfest machen, den Schuppen aufräumen. Wählst du ein solches Objekt im Plan, zeigt der Tab **Eigenschaften** den Abschnitt **Aufgaben** mit den offenen Aufgaben des Objekts, nach Fälligkeit sortiert. **Aufgabe anlegen** öffnet den Aufgaben-Dialog mit dem Objekt als Ziel; zur Wahl stehen die Arten, die zu einem Objekt passen: Wartung, Reinigung, Beobachtung, Abdecken und Aufdecken. Aufgaben „für jede Pflanze“ gibt es hier nicht, weil ein Objekt keine Pflanzen trägt. Andere Objekte wie Weg, Zaun oder Rankhilfe bekommen keine Aufgaben. Ein Objekt muss gespeichert sein, bevor es Aufgaben bekommt, und ohne Verbindung kannst du keine anlegen. Anlegen dürfen Mitglieder ab der Rolle „grower“. <!-- REQ-053 R-7.2, W-008 -->

## Wohnungsplan: Fensterbank, Regal und Zelt {#wohnungsplan}

Für einen Standort in der Wohnung (Standort-Art Innenraum, Fensterbank oder Growzelt) ist der Gartenplan ein **Wohnungsplan**. Du zeichnest und planst mit denselben Werkzeugen wie im Garten; einiges ist auf drinnen eingestellt:

- **Leerer Plan:** Statt „Noch kein Gartenplan“ steht **Noch kein Wohnungsplan** mit zwei Wegen: **Grundriss zeichnen** öffnet die leere Zeichenfläche, **Foto als Vorlage laden** öffnet sie mit dem Dialog für die [Unterlage](#unterlage). Ein Foto oder eine Skizze des Grundrisses, mit zwei Punkten auf echte Maße geeicht, ist der bequemste Einstieg.
- **Raster:** Ein neuer Wohnungsplan beginnt mit 5 cm statt 10 cm.
- **Objekte drinnen:** Unter **Gartenobjekt** findest du **Fenster** (als Linie in der Wand), **Tür**, **Möbel** (Fensterbank, Regal, Tisch) und **Lampe**. Ihre Eigenschaften stehen unter [Eigenschaften, Seitenpanel und Listenansicht](#eigenschaften-und-listenansicht).
- **Was drinnen fehlt:** Frost, Kaltluft, Wärmespeicher und Wind blendet Kamerplanter für Innenräume aus, ebenso die Frost-Ebene. Gespeicherte Werte bleiben erhalten.
- **Pflanzplätze:** Der Tab **Beete** heißt hier **Pflanzplätze** (in der Adresse bleibt `tab=beds`) und listet alles, worin du Pflanzen anordnen kannst: Zelte und Regale ebenso wie Kübel und Pflanzkästen. Ein Raum selbst ist kein Pflanzplatz.

**Sonne aus dem Fenster vorschlagen.** Ein Fenster kennt seine Himmelsrichtung, sobald es in der Wand liegt: Kamerplanter leitet sie aus der Lage im Plan und dem Nordwinkel ab und zeigt sie bei den Eigenschaften des Fensters, etwa „Südost, 135°“. Wählst du einen Pflanzplatz, bietet sein Sonnenabschnitt **Aus Fenster vorschlagen**. Ein Dialog zeigt die Fenster im Umkreis (Standard 1,5 m; den Umkreis stellst du je Standort ein), den vorgeschlagenen Wert für **Sonne am Beet** (morgens, mittags, nachmittags, ganztägig oder wechselnd) und Hinweise, etwa dass Verschattung durch Nachbarhäuser oder Bäume nicht berücksichtigt ist. Fenster zur sonnenabgewandten Seite bringen nur diffuses Licht und zählen nicht. **Abbrechen** ändert nichts. Erst **Übernehmen** schreibt den Wert; steht schon ein Wert da, heißt die Schaltfläche **Ersetzen**, und der Dialog sagt dir vorher, was ersetzt wird. Stunden und Laubschatten bleiben unverändert. Ohne GPS-Koordinaten des Standorts nimmt Kamerplanter die Nordhalbkugel an; zwischen den Wendekreisen gibt es keinen Vorschlag. <!-- REQ-053 GP-FR-180, GP-FR-181, GP-FR-182, GP-FR-183 -->

**Zelt-Regeln.** Auf der Seite eines Zelts oder Regals trägst du unter **Zelt-Regeln** einen eigenen **Nachbarschaftsfaktor** ein (er überschreibt den Wert des Gartens, etwa wenn Pflanzen bewusst ineinander wachsen) und die **Beleuchtung**: Höhe der Lampe und Abstand zu den Pflanzen. Kamerplanter speichert die Beleuchtung für eine spätere Lichtberechnung und rechnet daraus noch nichts. Stehen im selben Zelt Pflanzen, die laut ihren Phasenprofilen in ihrer aktuellen Phase unterschiedlich lange Lichttage brauchen, warnt die Seite: Eine Lampe hat nur einen Zeitplan. Ist für eine Phase keine Lichtdauer hinterlegt, sagt die Seite das, statt zu raten. Beim Bepflanzen warnt der Dialog, wenn ein Topf kleiner ist als das empfohlene Topfvolumen der Art. <!-- REQ-053 W-016 -->

!!! note "Teilweise verfügbar: Wohnungsplan"
    Einen Umriss der Wohnung zeichnest du noch nicht als eigene Grenze; nutze die Unterlage und zeichne Räume, Fensterbänke und Regale als Pflanzplätze oder Objekte. Die Warnung zum Lichtbedarf nennt die Phasen derzeit mit ihrem englischen Namen. Einige Beschriftungen sprechen drinnen noch vom „Garten“. <!-- REQ-053 GP-FR-182, #2890, #2889 -->

## Feldmodus im Garten {#feldmodus-im-garten}

Der Feldmodus ist für das Smartphone im Beet gedacht: große Schaltflächen (mindestens 64 Pixel), starker Kontrast für Sonnenlicht und nur das, was du draußen brauchst. Auf einem schmalen Bildschirm (unter 600 Pixel Breite) öffnet die Gartenplan-Seite direkt im Feldmodus. Auf jedem Gerät wechselst du über **Feldmodus** bzw. **Planungsmodus** oben auf der Seite; die Adresse trägt dann `?mode=field` bzw. `?mode=plan`.

**Meine Beete · heute fällig.** Der Feldmodus startet mit der Liste deiner Beete. Beete, die dir zugewiesen sind, stehen oben (markiert mit **Meins**), danach Beete mit überfälligen oder heute fälligen Aufgaben, dann die übrigen nach ihrer nächsten Fälligkeit. Überfällig ist eine Aufgabe, deren Fälligkeitstag vor dem heutigen Tag liegt; eine Aufgabe, die heute fällig ist, zählt noch nicht als überfällig. Stillgelegte Beete fehlen in der Liste. Der Tab **Karte** zeigt den Plan ohne Werkzeuge, Raster und Griffe. Mit **Vergrößern**, **Verkleinern** und **Ganzer Plan** änderst du die Ansicht. Tippst du auf ein Beet oder knapp daneben, zoomt die Karte auf das Beet und öffnet es.

**Das Beet-Blatt.** Ein Tipp auf ein Beet öffnet unten ein Blatt mit dem Namen des Beets (daneben sein Titelfoto, wenn es eines hat), dem Schnellprotokoll, den Aufgaben und den Pflanzen. Die Aufgaben stehen in der Reihenfolge **Überfällig**, **Heute fällig**, **Später**. Die Pflanzen siehst du nach Art, Anzahl und Phase gruppiert; die Phasenfarbe hat immer einen schwarzen Rand und den Namen daneben.

- **Erledigt** öffnet den kurzen Dialog mit den freiwilligen Feldern (Menge, Notiz). **Fertig** speichert. Das sind zwei Tipps nach der Beetauswahl. Ein doppelter Tipp zählt nur einmal, und die Schaltflächen bleiben gesperrt, bis die Antwort da ist.
- **Schnellprotokoll:** **Gegossen**, **Gesät** und **Gejätet/Gemulcht** speichern mit einem Tipp einen Pflegeeintrag. **Geerntet** und **Notiz** öffnen das kurze Formular (Menge bzw. Text; für die Notiz kannst du die Spracheingabe deiner Tastatur nutzen). **Gepflanzt** öffnet den Pflanzdialog mit eingeschaltetem **Ich habe schon gepflanzt**; die Pflanzen entstehen sofort. Das geht nur bei einem Beet, das im Plan eingezeichnet ist.
- Nach **Erledigt** und nach jedem Schnellprotokoll siehst du acht Sekunden lang **Rückgängig**. Damit nimmst du den Eintrag zurück.
- **Pflanzen zeigen** listet die einzelnen Pflanzen einer Gruppe. **Position korrigieren** verschiebt eine Pflanze mit den Pfeilen in 10-cm-Schritten; ziehen kannst du den Marker erst, nachdem du ihn eine halbe Sekunde gehalten hast. **Foto** nimmt ein Bild für die Galerie der Pflanze auf.
- **Foto vom Beet** nimmt ein Bild für die Galerie des ganzen Beets auf (siehe [Fotos des Beets](locations-substrates.md#fotos-des-beets)). Das erste Foto eines Beets wird sein Titelfoto. Ohne Verbindung speichert Kamerplanter das Foto auf deinem Gerät und lädt es hoch, sobald du wieder online bist (siehe [Was geht ohne Netz](#was-geht-ohne-netz)).

Löschen, Beet räumen, Export und Import gibt es im Feldmodus nicht – dafür wechselst du in den Planungsmodus. Wer die Rolle „viewer" hat, sieht Aufgaben und Pflanzen nur lesend. Dein Browser merkt sich Mandant, Standort, Tab und Kartenausschnitt, nicht dein Konto; meldet sich jemand anderes auf dem Gerät an, beginnt der Feldmodus für diese Person neu. Zeigt ein gemerkter Kartenausschnitt auf dem aktuellen Bildschirm kaum noch etwas vom Plan – etwa nach dem Drehen des Smartphones –, öffnet die Karte mit dem ganzen Plan.

Ohne Verbindung speichert der Feldmodus **Erledigt**, die **Notiz** und Fotos auf deinem Gerät und sendet sie, sobald du wieder online bist; die übrigen Knöpfe des Schnellprotokolls brauchen eine Verbindung. Was genau ohne Netz geht, steht unter [Was geht ohne Netz](#was-geht-ohne-netz).

!!! warning "Noch nicht implementiert"
    Für **Gepflanzt** wird es ein **Rückgängig** geben. Die Hilfe per GPS und der QR-Code am Beet folgen später. Die Ebene „Zuletzt gegossen" wird es nur im Planungsmodus geben. <!-- REQ-053 GP-UX-020…031, GP-FR-149 -->

## Was geht ohne Netz {#was-geht-ohne-netz}

Im Garten ist das Netz oft schwach. Kamerplanter merkt sich deshalb auf deinem Gerät, was du zuletzt geladen hast, und hebt auf, was du im Feldmodus ohne Verbindung erfasst. Oben in der Leiste siehst du jederzeit, ob du **Online** oder **Offline** bist.

### Lesen ohne Netz

Ohne Verbindung zeigt Kamerplanter dir den zuletzt geladenen Stand dieser Seiten:

- den Gartenplan eines Standorts,
- die Standortliste,
- im Feldmodus die Liste deiner Beete und das Beet-Blatt mit Aufgaben und Pflanzen,
- die Beetansicht mit dem Kopf des Beets und dem Tab **Plan**; die übrigen Tabs, etwa die Stammdaten unter **Details**, brauchen eine Verbindung.

Ein Banner sagt dir, von wann die Daten sind: „Ohne Verbindung: Du siehst den Stand von 14:05." Gemerkt wird ein Stand höchstens 15 Minuten lang. Hast du eine Seite in dieser Zeit nicht mit Verbindung geöffnet, zeigt Kamerplanter einen Hinweis statt der Daten, zum Beispiel „Dieser Plan ist ohne Verbindung nicht verfügbar". Öffne die Seite dann einmal mit Verbindung.

Ohne Verbindung kannst du den Plan nur ansehen: Zeichnen, Verschieben und Umsetzen sind gesperrt, ungespeicherte Änderungen bleiben erhalten. Am Beet sind Status, Sonne, Boden, Fruchtfolge und Fotos gesperrt, bis die Verbindung zurück ist.

### Erfassen ohne Netz

Im Feldmodus kannst du ohne Verbindung drei Dinge erfassen:

- **Erledigt** für eine Aufgabe,
- eine **Notiz** aus dem Schnellprotokoll,
- ein **Foto vom Beet** und das **Foto** einer Pflanze.

Kamerplanter speichert jeden Eintrag mit dem Zeitpunkt, zu dem du ihn erfasst hast, auf deinem Gerät. Sobald du wieder online bist, sendet die App die Einträge der Reihe nach, den ältesten zuerst, und zeigt den Fortschritt („Übertrage 2/5 Einträge …"), danach etwa „5 Einträge übertragen." Ein Eintrag kommt nur einmal an, auch wenn die App ihn nach einer abgerissenen Verbindung erneut sendet. **Rückgängig** nimmt einen Eintrag in den acht Sekunden danach wieder heraus.

- Pro Konto hebt dein Gerät höchstens 500 Einträge auf. Ist der Speicher voll, sagt dir die App das und nimmt nichts mehr an, bis du online warst.
- Fotos verkleinert die App vor dem Speichern auf höchstens 1 920 Pixel an der längeren Seite und speichert sie ohne Standortdaten (GPS) und Kameradaten.
- Solange Einträge warten, zeigt die Leiste oben, wie viele es sind, etwa **„3 nicht übertragen"**. Klappt das Senden nicht, versucht die App es mit wachsendem Abstand erneut. Nach fünf Versuchen, wenn der Server den Eintrag ablehnt oder wenn die Aufgabe inzwischen erledigt oder gelöscht ist, sendet sie ihn nicht mehr von selbst und sagt es dir. Ein Tipp auf die Anzeige öffnet **Nicht übertragene Einträge**: Dort entscheidest du je Eintrag zwischen **Erneut versuchen**, **Behalten** (der Eintrag bleibt zum Nachlesen auf dem Gerät und wird nicht noch einmal gesendet) und **Verwerfen**.
- Was nicht übertragen wird, löscht das Gerät irgendwann selbst: Wartende Einträge, die älter als ein Jahr sind, nimmt der Server nicht mehr an; nicht übertragene und behaltene Einträge verschwinden 90 Tage nach dem Erfassen. Die App sagt dir, wie viele es waren.

### Nur mit Verbindung

**Gegossen**, **Gesät**, **Gejätet/Gemulcht**, **Geerntet** und **Gepflanzt**, **Position korrigieren**, Sonne und Standortmerkmale, alles Zeichnen und Verschieben im Plan, Löschen, Export, Import und Beetvorlagen brauchen eine Verbindung. Ohne Verbindung sind diese Knöpfe gesperrt; nichts geht dabei verloren.

### Beim ersten Mal einmal neu laden

Öffnest du Kamerplanter auf einem Gerät zum ersten Mal oder nachdem du die Websitedaten gelöscht hast, lade die Seite einmal neu, solange du noch Verbindung hast. Erst danach hat dein Browser alles beisammen, was das Erfassen ohne Netz braucht.

### Abmelden und Garten wechseln

Meldest du dich ab, löscht Kamerplanter den gemerkten Stand auf diesem Gerät. Hast du noch Einträge, die nicht übertragen sind, fragt die App vorher nach: **Jetzt übertragen**, **Verwerfen und abmelden** oder **Abbrechen**. Ohne Verbindung geht **Jetzt übertragen** nicht; der Dialog sagt dir dann, warum. Wechselst du in einen anderen Garten, löscht Kamerplanter den gemerkten Stand ebenfalls; deine nicht übertragenen Einträge des bisherigen Gartens bleiben auf dem Gerät und werden gesendet, sobald du dorthin zurückkehrst. Was genau auf deinem Gerät liegt und wann es gelöscht wird, steht unter [Daten auf deinem Gerät](privacy.md#daten-auf-deinem-geraet).

## Kamerplanter auf dem Startbildschirm {#startbildschirm}

Du kannst Kamerplanter wie eine App auf den Startbildschirm deines Smartphones oder in die App-Liste deines Rechners legen. Sie öffnet sich dann in einem eigenen Fenster ohne Adressleiste. Kamerplanter blendet dafür keinen eigenen Hinweis ein; du nutzt das Menü deines Browsers:

- **Chrome oder Edge** (Android, Windows, macOS, Linux): Menü → **App installieren** bzw. **Zum Startbildschirm hinzufügen**.
- **Safari auf iPhone und iPad:** **Teilen** → **Zum Home-Bildschirm**.

Gibt es eine neue Version, erscheint unten das Banner **Neue Version verfügbar**. **Jetzt aktualisieren** lädt sie in allen offenen Fenstern; mit **Später** arbeitest du erst einmal weiter.

## Ebenen und Standortbedingungen {#ebenen-und-standortbedingungen}

Ebenen blendest du im Seitenpanel im Tab **Ebenen** ein und aus; jeder Schalter trägt seinen Namen. Deine Wahl merkt sich der Browser; sie gilt nur für dich. Das Raster ist keine Ebene dieser Gruppe: Es hat einen eigenen Schalter **Raster anzeigen** im Tab **Ansicht** (zu Beginn an, Taste **G**), siehe [Raster, Einrasten, Zoom und Kompass](#raster-einrasten-zoom-und-kompass).

| Ebene | Zeigt | Zu Beginn |
|-------|-------|-----------|
| **Bewässerungszonen anzeigen** | Zonen als Umriss mit Schraffur über ihren Beeten | aus |
| **Zuletzt gegossen anzeigen** | Tage seit dem letzten erfassten Gießen je Beet als Schraffur | aus |
| **Unterlage anzeigen** | Das Hintergrundbild (nur sichtbar, wenn der Standort eine Unterlage hat) | an |
| **Sonnenfenster anzeigen** | Wann die direkte Sonne ein Beet erreicht | aus |
| **Drainage anzeigen** | Wie gut ein Beet Wasser ableitet | aus |
| **Frostrisiko anzeigen** | Gering, normal oder hoch je Beet | aus |
| **Pflanzenzustand anzeigen** | Phase, Ring und Zeichen jeder Pflanze | aus |
| **Mischkultur anzeigen** | Linien zwischen benachbarten Pflanzen: gute, schlechte oder unbekannte Nachbarschaft | aus |

Die Legende im Tab **Ebenen** erklärt jede eingeschaltete Ebene; sie erscheint, sobald mindestens eine Ebene an ist. Im Wohnungsplan gibt es keine Frost-Ebene. Die Schraffur der Zonen und der Zustandsebenen unterscheidet sich im Muster, nicht nur in der Farbe.

Die Ebene **Zuletzt gegossen** zeigt nur den Abstand zum letzten erfassten Gießen in vier Stufen (0 bis 1, 2 bis 3, 4 bis 7, mehr als 7 Tage). Ob ein Beet Wasser braucht, sagt sie nicht. Ein Beet ohne erfasstes Gießen bleibt ohne Schraffur.

### Sonnenfenster, Drainage und Frostrisiko {#sonnenfenster-drainage-frostrisiko}

Die Werte pflegst du am Beet: Sonne, Sonnenzeit und Laubschatten in den Sonnen-Kacheln (siehe [Sonne und Schatten am Beet](locations-substrates.md#sonne-und-schatten-am-beet)), die Drainage im Bodenprofil. Die Ebenen zeigen diese Angaben auf dem ganzen Plan.

**Ebenen Sonnenfenster, Drainage und Frostrisiko im Gartenplan.** Im Tab **Ebenen** blendest du drei weitere Ebenen ein: **Sonnenfenster anzeigen** (wann die direkte Sonne das Beet erreicht), **Drainage anzeigen** (schlecht, mittel, gut) und **Frostrisiko anzeigen** (gering, normal, hoch). Jeder Wert hat ein eigenes Muster, du erkennst ihn also auch ohne Farbe. Das Muster siehst du immer; sobald du so weit hineinzoomst, dass die Beetnamen erscheinen, kommt am unteren Beetrand ein kleines Symbol für den Wert dazu, sofern das Beet dafür Platz hat; die Legende im Tab **Ebenen** erklärt jede eingeschaltete Ebene. Ein Beet ohne erfassten Wert bleibt ohne Muster. Alle drei Ebenen sind zu Beginn aus, und deine Wahl merkt sich der Browser für dich. Die Frost-Ebene zeigt das gespeicherte Frostrisiko; maßgeblich für die Überwinterung bleibt die Frostexposition. <!-- REQ-053 GP-FR-169, GP-FR-047 -->

### Pflanzenzustand und Filter {#pflanzenzustand-und-filter}

Was Scheibe, Ring und Zeichen an einer Pflanze bedeuten, steht unter [Pflanzenzustand und Pflanzen-Info](locations-substrates.md#pflanzenzustand). Im Gartenplan gilt für die Ebene:

**Ebene Pflanzenzustand und Filter im Gartenplan.** Mit **Pflanzenzustand anzeigen** im selben Tab siehst du den Zustand deiner Pflanzen, ohne ein Beet zu öffnen. Zoomst du nah genug an ein Beet, dass die einzelnen Pflanzen erscheinen, trägt jede Pflanze Scheibe, Ring und Zeichen wie im Tab **Plan** des Beets: Die Farbe zeigt die Wachstumsphase, der Ring den Stand der Pflanzung, das Zeichen oben rechts den dringendsten Handlungsbedarf. Weiter herausgezoomt fasst jedes Beet seine Pflanzen zu einem Kreis mit Zahl zusammen; hast du ein Beet vorher schon nah genug gesehen, kennt Kamerplanter seine Zustände: Dann zeigt der Kreis das dringendste Zeichen, und der Vorleser nennt die Zahl aller Pflanzen des Beets und wie viele davon Handlungsbedarf haben. Daneben liegt der Schalter **Nur Pflanzen mit Handlungsbedarf zeigen**: Er blendet alle Pflanzen aus, deren Zustand bekannt ist und die kein Zeichen tragen. Eine Pflanze, deren Zustand noch nicht geladen ist, bleibt sichtbar. Der Kreis eines Beets zeigt dann nur die Pflanzen, die übrig bleiben, und verschwindet erst, wenn alle Zustände des Beets bekannt sind und keine Pflanze Handlungsbedarf hat; das Beet selbst bleibt sichtbar, und der Vorleser nennt weiter die Zahl aller Pflanzen. Solange die Ebene aus ist, ist der Schalter gesperrt; du erreichst ihn trotzdem mit der Tabulatortaste, und der Vorleser sagt dir, warum er gesperrt ist. Die Legende im Tab **Ebenen** erklärt Ringe und Zeichen und listet die Farben der Wachstumsphasen der Pflanzen, deren Zustände geladen sind, alphabetisch in deiner Sprache. Kamerplanter lädt die Zustände nur, solange die Ebene an ist, und nur für die Beete, die du gerade nah genug siehst, höchstens vier Beete gleichzeitig. Jedes Beet lädt einmal und neu, wenn du zum Tab zurückkehrst, den Plan speicherst oder eine neuere Fassung des Plans lädt, und nachdem du im Bewässerungsbereich eine Zone geändert oder eine Gießrunde erfasst hast. Die Ebene und der Filter sind zu Beginn aus; deine Wahl merkt sich der Browser. Die Info-Blase beim Überfahren einer Pflanze bleibt dem Tab **Plan** des Beets vorbehalten. <!-- REQ-053 GP-UX-061, GP-UX-060 -->

!!! note "Teilweise verfügbar: Pflanzenzustand"
    **Frostgefahr** erscheint noch nicht als Zeichen, auch wenn die Ebene **Frostrisiko** den gespeicherten Wert zeigt. **Fälliges Gießen** entsteht bisher nur aus einer Gießaufgabe, die heute fällig ist, nicht aus dem Bewässerungsbedarf. <!-- REQ-053 GP-UX-060, GP-FR-190 -->

### Mischkultur auf dem Plan {#mischkultur-auf-dem-plan}

**Ebene Mischkultur im Gartenplan.** Mit **Mischkultur anzeigen** im Tab **Ebenen** siehst du, ob benachbarte Pflanzen sich vertragen. Zwischen zwei benachbarten belegten Plätzen eines Beets zieht der Plan eine Linie. Der Platz kann eine stehende Pflanze tragen oder eine Art, die eine laufende Pflanzung dort vorsieht. Die Art der Linie sagt, was bekannt ist:

| Linie | Bedeutung |
|-------|-----------|
| Durchgezogen, grün | Gute Nachbarn: Die Arten fördern sich. |
| Gestrichelt, rot | Schlechte Nachbarn: Die Arten hemmen sich. |
| Gepunktet, grau | Keine Angabe: Für dieses Paar ist keine Beziehung hinterlegt. |

Die Linien unterscheiden sich im Strich, nicht nur in der Farbe; du erkennst sie also auch in Graustufen. Zeigst du mit der Maus auf eine Linie, erscheint eine Karte. Sie nennt die beiden Arten, die das Urteil bestimmen, dazu den hinterlegten Grund oder eine kurze Erklärung, bei guten Nachbarn die Bewertung von 0,1 bis 1 und, falls bekannt, den Abstand. Auf dem Touchscreen tippst du die Linie an. Die Karte bleibt dann offen, bis du sie schließt oder woanders auf den Plan tippst. Ein Tipp auf eine Linie wählt das Beet darunter nicht aus, und ein Wisch, der auf einer Linie beginnt, verschiebt weiter den Plan. Trägt ein Platz mehr als acht Arten, bewertet der Plan nur die ersten acht; die Karte sagt es dir dann. Die Bewertung ist dieselbe wie im Pflanzdialog (**Bepflanzen**): Ist irgendein Artenpaar der beiden Plätze unverträglich, gilt das Paar als schlechte Nachbarschaft.

Die Linien erscheinen erst, wenn du so nah an ein Beet zoomst, dass die einzelnen Pflanzen sichtbar sind. Kamerplanter lädt sie nur, solange die Ebene an ist, und nur für die Beete, die du gerade so nah siehst, höchstens vier Beete gleichzeitig. Jedes Beet lädt einmal und neu, wenn du den Plan speicherst oder eine neuere Fassung lädt. Der Plan zeigt höchstens 500 Linien auf einmal, schlechte Nachbarn zuerst; sind mehr Paare im Bild, sagt dir das die Legende. Zoome dann näher heran. Die Ebene ist zu Beginn aus; deine Wahl merkt sich der Browser. <!-- REQ-053 GP-FR-134 -->

**Ohne Maus und Touch.** Die Linien selbst erreichst du nicht mit der Tab-Taste, damit der Plan nicht Hunderte Tabstopps bekommt. In der Legende der Ebene öffnest du stattdessen die **Liste der Nachbarpaare**. Sie nennt zu jedem Paar im Bild die Nachbarschaft in Worten, die beiden Arten, den Grund und die Bewertung, schlechte Nachbarn zuerst. Die Liste ist ein einziger Tabstopp; mit den Pfeiltasten scrollst du darin. <!-- REQ-053 GP-FR-134 -->

## Bewässerungszonen und Gießrunde {#bewasserungszonen}

Eine **Bewässerungszone** fasst Beete eines Standorts zusammen, die gemeinsam gegossen werden, etwa an einem Tropfschlauch oder unter einem Regner. Ein Beet gehört zu höchstens einer Zone. Der Standort kann bis zu 500 Zonen haben.

Die Zonen verwaltest du im Seitenpanel im Tab **Zonen**; **Bewässerungszonen verwalten** im Menü **⋮** öffnet ihn direkt.

1. **Zone anlegen:** Klicke auf **Neue Zone**. Gib einen Namen ein, wähle die **Art der Bewässerung** (Von Hand, Tropfbewässerung, Regner, Perlschlauch oder Staubewässerung) und eine Farbe. Optional trägst du eine Wasserquelle (ein Gartenobjekt vom Typ Wasserquelle), den Durchfluss in Litern pro Minute und einen Hinweis zum Zeitplan ein.
2. **Beete zuordnen:** Hake die Beete an oder übernimm die Auswahl vom Plan mit **Auswahl vom Plan übernehmen**. Ein Beet, das schon in einer anderen Zone liegt, wechselt in diese; die Oberfläche sagt es dir. Beete und Wasserquellen, die du noch nicht gespeichert hast, stehen erst nach dem Speichern des Plans zur Auswahl.
3. **Zone speichern.** Lesen dürfen alle Mitglieder; ändern ab der Rolle „grower", löschen nur die Leitung. Löschst du eine Zone, bleiben die Beete unverändert und gehören danach zu keiner Zone; das Gießprotokoll bleibt erhalten.

**Stand der Zone.** Zu jeder Zone zeigt Kamerplanter, wann zuletzt gegossen wurde, das nächste geplante Gießen, den **Bedarf heute** (netto und brutto, mit Wirkungsgrad aus der Zone oder als Richtwert der Bewässerungsart), den **Verbrauch der letzten 30 Tage** mit seiner Herkunft sowie Hinweise, etwa wie lange die Wasserquelle bei diesem Tagesbedarf reicht.

**Gießrunde protokollieren.** Wenn du eine ganze Zone gegossen hast, öffnet **Gießrunde protokollieren** einen Dialog: Du gibst die **Gesamtmenge in Litern** an (größer als 0, höchstens 100 000) und wählst die **Verteilung**: **Nach Beetfläche** (jedes Beet bekommt einen Anteil nach seiner Fläche; Beete ohne Fläche bleiben außen vor) oder **Zu gleichen Teilen**. Kamerplanter schreibt für jedes Beet einen Gießeintrag ins Pflegeprotokoll. Die Menge ist verteilt, nicht gemessen; das Protokoll kennzeichnet das so.

Als dritte **Verteilung** gibt es **Nach Bedarf**: Jedes Beet bekommt einen Anteil nach seinem berechneten Wasserbedarf an diesem Tag; Beete ohne Bedarf bleiben außen vor.

**Regen — übersprungen.** Hat es geregnet und du lässt die Runde ausfallen, tippst du im selben Dialog auf **Regen — übersprungen**. Kamerplanter schreibt dann für jedes Beet der Zone einen Regen-Eintrag ohne Menge ins Pflegeprotokoll. Offene Gieß-Aufgaben bleiben offen, und der Eintrag zählt nicht als gegossene Menge. <!-- REQ-053 GP-FR-117 -->

**Wasserquelle.** Wählst du im Plan ein Gartenobjekt vom Typ Wasserquelle, trägst du im Eigenschaften-Bereich die **Art der Wasserquelle**, das **Fassungsvermögen** in Litern (für Regentonne oder Zisterne) und den Tag **Zuletzt aufgefüllt** ein. Wie lange die Wasserquelle reicht, zeigt der Stand der Zone nur mit einem Fassungsvermögen. <!-- REQ-053 GP-FR-111 -->

!!! info "Nur über API: Technische Kopplung"
    Die Kopplung einer Zone an einen Aktor oder an eine Home-Assistant-Entität für den Durchfluss pflegen nur Mitglieder mit dem Verwaltungsbereich `technical`, und zwar über die API. Beim Zurückspielen einer Sicherung werden diese Verknüpfungen nie übernommen. Siehe [Für technische Nutzer / Self-Hoster](#fur-technische-nutzer-self-hoster).

## Beetvorlagen {#beetvorlagen}

Eine Beetvorlage legt Form, Maße, Beettyp und Höhe eines Beets fest, damit du dieselbe Form nicht jedes Mal neu zeichnest. Kamerplanter bringt Standardgrößen mit, zum Beispiel Beet 1 × 1 m, 2 × 1 m, 3 × 1,2 m und 4 × 1,2 m, Hochbeet 1,2 × 2,4 m und 2 × 1 × 0,8 m sowie Kübel mit 0,3, 0,4 und 0,5 m Durchmesser. Eigene Vorlagen gehören zu deinem Garten.

- **Platzieren:** **Aus Vorlage** in der Werkzeugleiste, siehe [Im Gartenplan schneller arbeiten](#plan-komfort).
- **Speichern:** Wähle genau ein Beet und klicke auf **Als Vorlage speichern**. Pflanzen, Aufgaben und Notizen gehören nicht dazu. Ein Garten kann bis zu 200 eigene Vorlagen haben; ist die Grenze erreicht, löschst du erst eine nicht mehr benötigte.
- **Teilen:** Im Bereich **Beet aus Vorlage** lädt **Exportieren** die gewählte Vorlage als JSON-Datei herunter, ohne Kennung deines Gartens, ohne Autor und ohne Notizen. So gibst du eine Vorlage an andere Gärten weiter. **Importieren** nimmt eine solche Datei (höchstens 256 KB) und prüft sie zuerst: Der Prüfbericht zeigt Name, Form, Höhe und Pflanzraster und welche Felder der Datei übergangen werden. Gibt es den Namen schon, schlägt Kamerplanter einen freien vor. Gespeichert wird erst, wenn du **Importieren** bestätigst. Kamerplanter liest Dateien der aktuellen und der vorigen Version; eine ältere Datei exportierst du neu.
- **Rollen:** Vorlagen legen und importieren Gärtner und die Leitung; löschen darf nur die Leitung.

## Unterlage zum Abzeichnen {#unterlage}

Mit einer **Unterlage** legst du ein Foto, eine Skizze oder ein Luftbild unter den Plan und zeichnest die Beete darauf ab.

1. Wähle im Menü **⋮** den Eintrag **Unterlage** und wähle ein Bild (JPEG, PNG oder WebP). Der Plan braucht dafür schon eine Gartengrenze.
2. **Eichen:** Klicke im Bild zwei Punkte an, deren Abstand du kennst, und gib den Abstand in Metern an. Daraus rechnet Kamerplanter den Maßstab (Pixel pro Meter).
3. **Lage:** Lege fest, wo die obere linke Ecke des Bildes auf dem Plan liegt, drehe das Bild bei Bedarf gegen den Uhrzeigersinn und stelle die Deckkraft ein.
4. **Speichern.** Mit **Unterlage entfernen** löschst du Bild und Eichung wieder; du müsstest beides neu anlegen.

Ein Standort hat höchstens eine Unterlage, und alle Mitglieder sehen dieselbe. Ob du sie anzeigst, entscheidest du für dich mit der Ebene **Unterlage anzeigen**. Setzen und entfernen dürfen Gärtner und die Leitung. Die Unterlage liegt unter allen Objekten, steht nicht in der JSON-Sicherung und kommt nur dann in den PDF-Druck, wenn die API-Abfrage es ausdrücklich verlangt (der Export-Dialog bietet das nicht an). Luftbilder können verraten, wo du wohnst: Gib einen Plan mit Unterlage nur weiter, wenn du das willst.

## Fruchtfolge-Matrix {#fruchtfolge-matrix}

Die Matrix zeigt für alle Beete eines Standorts auf einen Blick, was in den letzten Jahren dort stand. Du öffnest sie auf der Standortseite mit **Fruchtfolge-Matrix** (Adresse `/standorte/sites/<key>/rotation-matrix`). Jede Zeile ist ein Beet, jede Spalte ein Jahr, das aktuelle Jahr steht ganz rechts. Wie weit die Matrix zurückreicht, richtet sich nach den längsten Anbaupausen der Familien in den gezeigten Beeten, mindestens fünf, höchstens zehn Jahre.

In einer Zelle steht je Eintrag die Pflanzenfamilie als Kürzel mit Farbe und Muster, darunter die Zehrerklasse als Text und, wenn bekannt, die Saison. Farbe allein trägt die Familie nie: Kürzel und Muster unterscheiden sie auch im Graustufendruck. Die Legende unter der Tabelle nennt zu jedem Kürzel den vollen Namen. Gründüngung und Brache sind gekennzeichnet. Ein leeres Jahr zeigt einen Strich: Es ist nichts erfasst.

- **Nachtragen.** Mit der Rolle „grower" oder „lead" tippst du auf ein vergangenes Jahr und trägst im bekannten Dialog **Was stand hier?** nach, was dort wuchs (siehe [Historie des Beets](locations-substrates.md#historie-des-beets)). Das laufende Jahr nimmt die Matrix nicht entgegen; dort gilt, was im Beet gepflanzt ist. Beobachter („viewer") lesen die Matrix nur.
- **Zum Beet.** Der Name des Beets führt zur Beetansicht.
- **Beete ohne Prüfung.** Ein Beet, das von der Fruchtfolge-Prüfung ausgenommen oder ausgeschaltet ist, steht trotzdem in der Matrix, mit dem Hinweis am Namen. Seine Historie bleibt sichtbar.
- **Viele Beete.** Die Matrix lädt 50 Beete je Seite; **Weitere Beete laden** holt die nächsten, mit denselben Jahren. Sie liest höchstens 500 Beete nach Name; hat ein Standort mehr, steht ein Hinweis darunter.
- **Zukünftige Jahre.** Geplante Folgekulturen zeigt die Matrix noch nicht; sie endet im laufenden Jahr.

Die Matrix liest dieselben Daten wie der Zeitstrahl am Beet und rechnet nichts neu: Ein Feld der Matrix ist genau der Eintrag des Zeitstrahls für dasselbe Beet und Jahr. <!-- REQ-053 GP-FR-135 -->

## Änderungsprotokoll {#anderungsprotokoll}

Kamerplanter schreibt zu jedem Plan ein Änderungsprotokoll: Löschungen und Änderungen der Gartengrenze mit Zeitpunkt und Namen des Bearbeiters, außerdem die Stände, die ein Ersetzen beim Import überschrieben hat (siehe [Plan exportieren und Sicherung einspielen](#plan-export-import)). Einträge werden ein Jahr lang aufbewahrt. Das Protokoll hat in der Oberfläche keine eigene Seite; es ist über die API lesbar (siehe [Für technische Nutzer / Self-Hoster](#fur-technische-nutzer-self-hoster)).

Was an einem einzelnen Beet geschah, steht in dessen Historie: den Zeitstrahl der Fruchtfolge und die Liste aller Pflegeeinträge und Pflanzungen beschreibt [Historie des Beets](locations-substrates.md#historie-des-beets).

## Plan exportieren und Sicherung einspielen {#plan-export-import}

Auf der Gartenplan-Seite öffnen **Plan exportieren …** und **Sicherung einspielen …** im Menü **⋮** zwei Dialoge.

**Plan exportieren** gibt es als PDF (Plan im Maßstab zum Ausdrucken), als SVG (Vektorgrafik), als PNG (Bild) und als Sicherung (JSON). Du wählst Papier, Ausrichtung, Maßstab und die Ebenen (beim PDF zusätzlich **Beetliste als zweite Seite**); eine Vorschau zeigt, was herauskommt. Mit **Automatisch** nimmt Kamerplanter den feinsten Maßstab, der aufs Blatt passt, und schlägt A3 vor, wenn A4 zu grob würde. Passt ein fest gewählter Maßstab nicht aufs Blatt, sagt dir der Dialog das und lässt dich einen gröberen Maßstab oder A3 wählen. Auf dem Handy gibt es nur PDF und Sicherung mit den Standardoptionen. Der Export enthält keine Namen von Mitgliedern und keine Zuweisungen (die Parzellenliste im PDF und die Beetliste als CSV können sie auf Wunsch enthalten, siehe unten).

**Parzellenliste im PDF.** Mit **Parzellenliste als Zusatzseite** bekommt das PDF eine weitere Seite, etwa für den Vorstand oder den Verpächter: jedes Beet mit laufender Nummer in Plan-Reihenfolge und Name, dazu Fläche und Bewässerungszone. Erst wenn die Parzellenliste an ist, bietet der Dialog **Zuweisungen in die Parzellenliste aufnehmen** an. Das fügt eine Spalte mit den Namen der Mitglieder hinzu, denen ein Beet zugewiesen ist; das sind personenbezogene Daten, gib das PDF dann nur an Personen weiter, die sie sehen dürfen. Notizen und Kontodaten stehen nie darin. <!-- REQ-053 GP-FR-176 -->

**PNG (Bild)** erstellt dein Browser aus dem Plan, ohne den Server: der ganze Plan als Bild, zum Teilen in Nachrichten oder zum Einfügen in Dokumente. Er zeigt die Ebenen, die du im Plan eingeschaltet hast. Du wählst die **Auflösung** 1×, 2× oder 4×; vorgewählt ist 2×. 1× ist an der längeren Seite höchstens 1 200 Pixel groß, 2× und 4× sind schärfer, die Datei wird größer. Der Dialog nennt dir vorher die Größe in Pixeln. Wäre das Bild größer, als dein Browser zeichnen kann, nimmt Kamerplanter die größte mögliche Auflösung und sagt es dir. Das **Wasserzeichen „Kamerplanter · Datum"** in der rechten unteren Ecke ist eine Option und zu Beginn aus. Auf dem Handy gibt es PNG nicht. <!-- REQ-053 GP-FR-144 -->

**Beetliste (CSV)** gibt die Beete des Standorts als Tabelle aus, eine Zeile pro Beet, zum Weiterverarbeiten in deiner Tabellenkalkulation. Vorgewählt sind Name, Typ, Fläche, Status, Bodenart, Bewässerungszone und aktive Pflanzen; zusätzlich kannst du Standortmerkmale wie Sonneneinstrahlung, Frostrisiko oder Hangneigung ankreuzen. Wähle mindestens eine Spalte. Die **Excel-Variante** trennt die Spalten mit Semikolon und schreibt Zahlen mit Dezimalkomma, damit die Datei in deutschsprachigem Excel direkt als Tabelle aufgeht. Der Schalter **Zuweisungen einschließen** ist aus: Ohne ihn stehen keine Namen von Mitgliedern in der Datei. Schaltest du ihn ein, kommt eine Spalte mit den Namen der zugewiesenen Mitglieder dazu; das sind personenbezogene Daten, gib die Datei nur an Personen weiter, die sie sehen dürfen. Notizen und Kontodaten sind nie enthalten. Die Kopfzeile der Datei verwendet feste englische Spaltenkennungen (zum Beispiel `name`, `area_m2`, `frost_risk`, `assigned_to`), und Felder mit festen Werten wie Status, Bodenart oder Frostrisiko stehen als Kennwert in der Datei (zum Beispiel `active`, `loam`, `high`); Typ und Bewässerungszone erscheinen mit ihrem Namen. So bleibt die Datei unabhängig von der Spracheinstellung gleich aufgebaut. Eine Datei hat höchstens 2 000 Beete; bei mehr zeigt der Dialog eine Meldung. Auf dem Handy gibt es die Beetliste wie SVG nicht, nutze dafür einen größeren Bildschirm.

Im PDF und in der SVG zeigt jede Pflanze ihren Zustand wie im Plan: die Scheibe in der Farbe ihrer Wachstumsphase, einen Ring für ihren Stand (ein dicker Ring heißt *in Ernte*) und höchstens ein Zeichen für das Dringendste, etwa ein Dreieck für einen offenen Befund oder einen Tropfen, wenn Gießen fällig ist. Die Legende listet die Wachstumsphasen, Ringe und Zeichen, die auf dem Plan vorkommen. Von den Wachstumsphasen nennt sie höchstens die sechs mit den meisten Pflanzen; gibt es mehr, fasst ein Eintrag wie „+3 weitere Phasen“ den Rest zusammen, damit der Plan im gewählten Maßstab auf die Seite passt. Ein langer Phasenname wird mit „…“ gekürzt. Pflanzen einer Art mit eigener Phasenfolge tragen dieselbe Farbe wie im Plan. Ab 2 000 Pflanzen zeigt jedes Beet stattdessen nur die Zahl seiner Pflanzen. <!-- REQ-053 GP-UX-005, GP-UX-059, GP-UX-060 -->

Die **Sicherung** enthält Beete, Gartenobjekte, Pflanzplätze, Bewässerungszonen, Bodenprofile, Standortmerkmale und die Gartengrenze, aber keine Pflanzen und keine Aufgaben. Hast du im Plan Beete oder Gartenobjekte ausgewählt, kannst du die Sicherung auf **Nur die Auswahl** oder auf **Auswahl mit allem darunter** beschränken. Eine solche Teil-Sicherung enthält keine Gartengrenze; Verweise auf Dinge, die nicht in der Datei stehen, entfallen. Lesen darf sie jede Rolle.

**Sicherung einspielen** führt in drei Schritten durch den Import. Das darf nur die Leitung.

1. **Datei wählen:** Die Datei darf höchstens 5 MB groß sein. Kamerplanter prüft sie sofort, ohne etwas zu schreiben. Hast du stattdessen nur eine Beetliste in einer Tabelle, führt dich der Link **Beetliste importieren (CSV)** zum [CSV-Import](#beetliste-csv-import).
2. **Prüfbericht:** Du siehst, wie viel angelegt und gelöscht würde, welche Verweise nicht übernommen werden (zum Beispiel eine Bewässerungszone, die es hier nicht gibt) und welche Probleme die Datei hat, etwa überlappende Beete. Bei Problemen geht es nicht weiter.
3. **Modus:** *Hinzufügen* legt die Sicherung zusätzlich zum bestehenden Plan an. *Ersetzen* tauscht den Plan dieses Standorts aus. Dafür tippst du den Namen des Standorts ein. Vorher speichert Kamerplanter den bisherigen Plan als Snapshot im Änderungsprotokoll. Lade dir zur Sicherheit trotzdem vorher eine aktuelle Sicherung herunter.

Im Modus *Hinzufügen* kannst du alle Formen der Datei um einen Abstand verschieben (nach rechts und nach oben, in Metern), etwa um ein Beet an eine andere Stelle zu setzen. Mit **Wohin geht die Datei?** sagst du, ob die Datei aus diesem Standort, aus einem anderen Standort oder aus einem anderen Garten-Konto stammt. Für die beiden letzten gilt: Verweise, die nicht in der Datei stehen, werden nie gegen diesen Standort aufgelöst, sondern entfallen und stehen im Prüfbericht. Aus einem anderen Konto wird nichts gelesen, die Datei ist der Transportweg; du brauchst die Leitungsrolle in dem Konto, in das du einspielst.

Spielst du dieselbe Datei mehrmals mit *Hinzufügen* ein, legt jede Runde ihre Bewässerungszonen neu an; die Zonen der Datei erkennt Kamerplanter nicht wieder. Ein Standort hat höchstens 500 Zonen, darüber weist der Prüfbericht die Datei ab.

**Früheren Stand wiederherstellen:** Im ersten Schritt des Imports öffnet dieser Knopf die Liste der Pläne, die ein *Ersetzen* überschrieben hat (ein Jahr lang aufbewahrt, höchstens die 20 neuesten je Standort, nur für die Leitung). Du wählst einen Stand, siehst den Prüfbericht und tippst den Namen des Standorts. Vorher speichert Kamerplanter den jetzigen Plan selbst als Stand, die Wiederherstellung lässt sich also zurücknehmen. Bewässerungszonen, die der Stand nicht nennt, werden dabei entfernt, und technische Zonen-Kopplungen (Aktor, Home-Assistant-Durchfluss) werden nicht wiederhergestellt; die richtest du danach neu ein. Das *Hinzufügen* legt keinen Stand an.

!!! warning "Beete mit aktiven Pflanzen"
    Ein Beet, in dem eine Pflanze steht, wird nie gelöscht. Solange es solche Beete gibt, weist *Ersetzen* die Datei ab. Wählst du die Option, diese Beete zu behalten, bleiben sie samt den Standorten darüber bestehen, und der Rest wird ersetzt.

**Neue Saison aus dem Vorjahr:** Im Menü **⋮** legt **Neue Saison aus dem Vorjahr …** für jedes Beet ohne aktive Pflanzen die Plätze des Vorjahres als freie Slots neu an (nur die Leitung, im selben Standort). Du gibst das Jahr der neuen Saison an; die Plätze stammen aus Abschlüssen des Jahres davor. Zuerst prüft Kamerplanter und zeigt je Beet, was passiert: Beete mit aktiven Pflanzen und stillgelegte Beete werden übersprungen und stehen im Bericht, ebenso ein Beet, das mit den neuen Plätzen über 2 000 Slots käme. Plätze, die schon als freier Slot da sind, werden nicht doppelt angelegt. Zonen, Pflanzen, Anbaudurchläufe und die Historie bleiben unverändert; Fruchtfolge- und Mischkultur-Hinweise nutzen weiter die Belegung des Vorjahres. Mit **„Hier stand …“ anzeigen** blendest du je Beet die Pflanzenfamilie des Vorjahres ein, nur zur Orientierung. Erst **Freie Slots anlegen** schreibt, in einem Schritt mit Eintrag im Änderungsprotokoll; hat sich der Plan seit der Prüfung geändert, prüfst du erneut. <!-- REQ-053 GP-FR-171 -->

Alle Schlüssel werden beim Einspielen neu vergeben. Verknüpfungen zu Home Assistant und zu Aktoren übernimmt Kamerplanter nie; die richtest du danach neu ein. Wer gerade ungespeicherte Änderungen am Plan hat, speichert oder verwirft sie zuerst. Im Feldmodus sind Export und Import ausgeblendet.

## Beetliste aus einer CSV-Datei importieren {#beetliste-csv-import}

Hast du deine Beete schon in einer Tabelle, legst du sie mit einer CSV-Datei (Tabelle als Textdatei, eine Zeile pro Beet) auf einen Schlag im Gartenplan an. Das darf nur die Leitung. Du öffnest den Import im Menü **⋮** mit **Beetliste importieren (CSV) …** oder über den Link im ersten Schritt des Sicherung-Imports.

1. **Datei wählen:** Wähle deine CSV-Datei. Mit **Beispieldatei herunterladen** bekommst du eine Vorlage, die du in deiner Tabellenkalkulation ausfüllst. Kamerplanter prüft die Datei sofort, schreibt aber noch nichts.
2. **Prüfbericht:** Du siehst, wie viele Zeilen gültig sind, welche Beete (Name, Größe, Sonne) angelegt würden, welche Zeilen Fehler haben und welche Spalten der Import nicht kennt und übergeht. Fehler und Hinweise nennen Zeile und Spalte. Zeilen mit einem Fehler werden übersprungen, die übrigen kannst du trotzdem übernehmen. Ist keine Zeile gültig, korrigierst du die Datei und wählst sie erneut.
3. **Anlegen:** Mit **… Beete anlegen** entstehen die gültigen Beete. Sie sind danach im Plan markiert, sodass du sie gleich anordnen kannst.

!!! note "Hat sich der Plan geändert?"
    Hat jemand den Plan geändert, seit du die Datei geprüft hast, bricht Kamerplanter ab und schreibt nichts. Klicke auf **Erneut prüfen** und übernimm dann noch einmal.

### So muss die Datei aufgebaut sein

- Die erste Zeile ist die Kopfzeile mit den Spaltennamen. Die Spalten trennst du mit Semikolon (`;`).
- Pflichtspalten: `Name`, `Typ`, `Breite_m` und `Länge_m` (auch `Laenge_m`). Englisch heißen sie `name`, `type`, `width_m` und `length_m`.
- Optionale Spalten: `Sonne` (`sun`), `Bodenart` (`soil_texture`) und `Zone` (`irrigation_zone`). Weitere Spalten übergeht der Import und nennt sie im Bericht.
- Maße gibst du in Metern an, mit Komma oder Punkt als Dezimaltrenner (`2,5` oder `2.5`). Tausendertrennzeichen und Einheiten wie „m“ sind nicht erlaubt.
- `Typ` ist der Schlüssel eines Beettyps oder sein deutscher oder englischer Name, zum Beispiel „Hochbeet“. Ein Typ, der kein Beet ist (etwa „Gewächshaus“), ist ein Fehler.
- `Sonne` und `Bodenart` nehmen den Wert oder seine Bezeichnung. Ohne `Bodenart` bekommt das Beet kein Bodenprofil.
- `Zone` ist der Name einer Bewässerungszone desselben Standorts.
- Die Datei ist UTF-8-kodiert (ein BOM am Anfang ist erlaubt), höchstens 1 MB groß und hat höchstens 500 Zeilen und 100 Spalten. Wählst du in Excel „CSV UTF-8“, passt es.

Beginnt eine Zelle mit einem Formelzeichen (`=`, `+`, `-`, `@`, Tabulator oder Zeilenumbruch), entfernt Kamerplanter das Zeichen und zeigt dafür einen Hinweis. So kann eine Tabelle keine Formel in deinen Plan schleusen.

### Wo die Beete landen

Kamerplanter setzt die neuen Beete als Rechtecke in Reihen von der oberen linken Ecke der Gartengrenze aus, mit 0,5 m Abstand. Am Rand der Gartengrenze beginnt eine neue Reihe, bestehende Beete werden übersprungen. Findet ein Beet keinen Platz mehr, ist das ein Fehler in dieser Zeile. Ein Standort fasst höchstens 500 Beete und Gartenobjekte zusammen; überschreitet die Liste das, lehnt Kamerplanter die ganze Datei ab. Die genaue Lage legst du danach im Editor fest.

## Für technische Nutzer / Self-Hoster {#fur-technische-nutzer-self-hoster}

Dieser Abschnitt ist für alle, die den Plan über die API anlegen oder eine Installation betreiben. Alle Pfade liegen unter `/api/v1/t/{slug}/`.

- **Ersten Plan anlegen:** `PUT /sites/{key}/plan/boundary` mit der Gartengrenze (Rechteck oder Vieleck), optional `north_angle_deg`. Der erste Aufruf legt den Plan an.
- **Plan lesen:** `GET /sites/{key}/plan`. **Änderungsprotokoll lesen:** `GET /sites/{key}/plan/audit`.
- **PDF mit Unterlage:** `GET /print/garden-plan/{site_key}?underlay=true`. Die Parzellenliste fordert `parcel_list=true` an, die Namen der Zuweisungen zusätzlich `include_assignment=true`.
- **Beetvorlage austauschen:** `GET /bed-templates/{key}/export` und `POST /bed-templates/import` (mit `dry_run`).
- **Notschalter für das Offline-Arbeiten:** Mit `PWA_CACHING_ENABLED=false` meldet die App ihren Service Worker (das Hintergrundprogramm des Browsers für Offline-Betrieb und Push) beim nächsten Seitenaufruf ab und löscht den gemerkten Stand **und die noch nicht übertragenen Offline-Einträge** auf jedem Gerät. Nutze ihn nur, wenn das Offline-Arbeiten selbst Probleme macht; sag deinen Nutzern vorher, dass sie online gehen und ihre Einträge übertragen sollen. Siehe [Umgebungsvariablen](../reference/environment-variables.md).
- **Beetliste per API:** `POST /beds/import-csv` unter `/sites/{key}` mit der CSV-Datei als rohem Body (`dry_run` standardmäßig `true`). Routen, Berichtsfelder und Fehlercodes stehen in der [API-Referenz](../reference/api-reference.md#beetliste-aus-csv-importieren).
- **Geschwindigkeitsgrenzen** und Aufbewahrung stehen unter [Umgebungsvariablen](../reference/environment-variables.md).
- Aufbau, Stapel-Schnittstelle und Sicherungsformat sind unter [Gartenplan: Geometrie und Schnittstellen](../architecture/garden-plan.md) beschrieben; die Routen und Fehlercodes unter [API-Referenz](../reference/api-reference.md#gartenplan-pdf-svg-json-sicherung).

## Häufige Fragen

??? question "Was tue ich, wenn der Plan **Noch kein Gartenplan** zeigt?"
    Der Standort hat noch keine Gartengrenze. Lege sie über die API an oder spiele eine Sicherung ein, siehe [Die Gartengrenze](#die-gartengrenze).

??? question "Ich kann zeichnen, aber nicht speichern."
    Speichern erfordert mindestens die Rolle „grower". Mit der Rolle „viewer" lehnt der Server das Speichern ab.

??? question "Warum kann ich ein Beet nicht löschen?"
    Löschen darf nur die Leitung. Außerdem lehnt Kamerplanter das Löschen ab, solange auf dem Beet Pflanzen wachsen; räume das Beet zuerst.

??? question "Meine Änderungen sind nach dem Neuladen weg."
    Ungespeicherte Änderungen und der Rückgängig-Verlauf bleiben nicht über ein Neuladen erhalten. Speichere regelmäßig oder schalte **Automatisch speichern** ein.

??? question "Kann ich zwei Beete überlappend zeichnen?"
    Nein. Der Server lehnt überlappende Beete beim Speichern ab; verschiebe eines, bis sich beide nicht mehr berühren.

## Siehe auch

- [Standorte und Substrate](locations-substrates.md) — Beetansicht, Pflege, Historie, Sonne und Boden
- [Pflanzdurchläufe](planting-runs.md)
- [Gießprotokoll](watering-log.md)
- [Druckansichten und Export](print-export.md)
- [Rollen und Berechtigungen](../reference/roles-and-permissions.md)
- [Gartenplan: Geometrie und Schnittstellen](../architecture/garden-plan.md) — Technik
