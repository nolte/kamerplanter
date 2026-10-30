# Gartenplan

Der Gartenplan zeigt deinen Garten von oben: Beete und Gartenobjekte wie Wege, Zäune und Bäume im richtigen Maßstab. Hier zeichnest du, verschiebst und bepflanzt Beete, siehst auf einen Blick, wo etwas zu tun ist, und sicherst oder druckst den Plan.

---

## Voraussetzungen

- Ein Standort (Site) in deinem Garten. Wie du ihn anlegst, steht unter [Standorte und Substrate](locations-substrates.md).
- Zum Ansehen genügt jede Rolle. Zum Zeichnen und Speichern brauchst du mindestens die Rolle „grower" (Gärtner:in), siehe [Wer darf was](#wer-darf-was).
- Ein Plan, der eine Gartengrenze hat (siehe [Die Gartengrenze](#die-gartengrenze)).

## Den Gartenplan öffnen

Öffne unter **Standorte** den Standort und klicke auf **Gartenplan öffnen**. Die Seite trägt die Adresse `/standorte/sites/<Schlüssel>/plan`. Auf einem schmalen Bildschirm (unter 600 Pixel Breite) öffnet sie direkt im [Feldmodus](#feldmodus-im-garten); sonst startet der Planungsmodus. Über **Feldmodus** bzw. **Planungsmodus** oben auf der Seite wechselst du jederzeit.

Der Planungsmodus zeigt links oder oben die Werkzeugleiste, in der Mitte den Plan, rechts das Eigenschaften-Feld und unter dem Plan die [Beetliste](#beetliste-im-gartenplan). Mit der Schaltfläche **Als Liste anzeigen** wechselst du zur Listenansicht desselben Plans, die ohne Maus und Zeichenfläche auskommt.

### Die Gartengrenze {#die-gartengrenze}

Jeder Plan hat eine Gartengrenze: den Umriss deines Gartens als Rechteck oder Vieleck. Beete und Gartenobjekte müssen ganz innerhalb liegen. Ein Standort ohne Grenze und ohne eingezeichnete Objekte zeigt statt des Editors den Hinweis **Noch kein Gartenplan**.

!!! warning "Teilweise verfügbar: Gartengrenze"
    Die Oberfläche hat noch kein Werkzeug, mit dem du die Gartengrenze zeichnest. Den ersten Plan legst du über die Programmierschnittstelle an (siehe [Für technische Nutzer / Self-Hoster](#fur-technische-nutzer-self-hoster)) oder du spielst eine Sicherung ein (siehe [Plan exportieren und Sicherung einspielen](#plan-export-import)). Ist die Grenze einmal da, ändert sich nur noch ihre Nordrichtung im Editor: Das Kompass-Feld stellt ein, wo geografisch Norden auf dem Plan liegt. <!-- REQ-053 GP-FR-013, GP-FR-015 -->

### Wer darf was {#wer-darf-was}

Deine Rolle gilt immer für den Garten (Mandanten), in dem du gerade arbeitest.

| Tätigkeit | viewer (Beobachter:in) | grower (Gärtner:in) | lead (Leitung) |
|-----------|:----------------------:|:-------------------:|:--------------:|
| Plan ansehen, Beetliste, Feldmodus lesen | ja | ja | ja |
| Export als PDF, SVG und Sicherung (JSON) | ja | ja | ja |
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

### Werkzeuge und Formen

Die Werkzeugleiste bietet vier Werkzeuge und die Vorlagenwahl:

| Werkzeug | Was es tut |
|----------|-----------|
| **Auswählen** | Klicken wählt ein Objekt, ein Rahmen wählt mehrere, mit der Umschalttaste fügst du Objekte hinzu. Gewählte Objekte verschiebst du durch Ziehen. |
| **Ansicht verschieben** | Zieht die Ansicht, ohne etwas zu ändern. |
| **Beet zeichnen** | Zeichnet ein neues Beet. |
| **Objekt: Gartenobjekt zeichnen** | Zeichnet ein Gartenobjekt wie Weg, Zaun oder Baum. |
| **Aus Vorlage** | Setzt ein Beet aus einer [Vorlage](#beetvorlagen). |

Als **Form** wählst du Rechteck, Kreis, Vieleck oder Linie. Das Rechteck ziehst du auf (mit der Umschalttaste wird es ein Quadrat), den Kreis ziehst du vom Mittelpunkt nach außen. Beim Vieleck und bei der Linie klickst du Punkt für Punkt; mit **Fertig**, der Eingabetaste oder einem Klick auf den ersten Punkt schließt du das Vieleck, die Linie beendest du mit **Fertig** oder der Eingabetaste. Die Rücktaste nimmt den letzten Punkt zurück, **Esc** verwirft die Form.

Zu jedem Objekt zeigt der Plan Breite, Länge (beim Kreis den Durchmesser) und Fläche. **Mit Maßen hinzufügen** legt ein Beet oder Objekt mit eingetippten Maßen an, auch ohne Zeichnen.

Ein gewähltes Objekt hat Griffe: Die Ecken ändern die Größe, der Drehgriff dreht das Objekt. Das **Drehraster** rastet beim Drehen alle 15, 45 oder 90 Grad ein; mit gehaltener Alt-Taste drehst du frei. Bei einem Vieleck fügst du über **Punkt einfügen** einen Punkt hinzu und entfernst einen mit **Punkt löschen**.

### Mit der Maus

- Klicken wählt, Ziehen verschiebt, ein Rahmen über freier Fläche wählt alles, was ganz im Rahmen liegt (gesperrte Objekte nicht).
- Mit **Strg** (am Mac **Cmd**) und dem Mausrad zoomst du stufenlos um den Zeiger; liegt der Fokus auf dem Plan, genügt das Mausrad. Ein einfaches Mausrad blättert die Seite.
- Ein Rechtsklick auf ein Objekt (auf dem Touchscreen die Schaltfläche **⋯** im Eigenschaften-Feld) öffnet die Aktionen des Objekts: Bearbeiten, Duplizieren, In den Vordergrund, In den Hintergrund, Sperren.
- Mit gehaltener **Alt**-Taste schaltest du das Einrasten kurz aus.

### Auf dem Touchscreen

- Mit **zwei Fingern** verschiebst und zoomst du den Plan.
- Ein Objekt wählst du mit einem Tipp. Zum Verschieben hältst du den Finger etwa eine halbe Sekunde auf dem Objekt; ein Ring zeigt, dass es nun bewegt wird. Wischst du früher, verschiebst du stattdessen die Ansicht.
- **Mehrfachauswahl** schaltest du als Schaltfläche ein. Dann tippst du Objekte an oder ziehst über freier Fläche einen Rahmen.
- Beim Zeichnen schiebst du den Plan mit zwei Fingern, bis das Fadenkreuz auf dem gewünschten Punkt liegt, und tippst auf **Punkt setzen**. **Rückgängig** nimmt den Punkt zurück, **Fertig** schließt die Form, **Abbrechen** verwirft sie. Sehr breite Berührungen (eine Handfläche) und ein zweiter Finger unmittelbar nach dem ersten ignoriert der Plan.

### Mit der Tastatur

Der Plan ist ohne Maus bedienbar. Die Schaltfläche **Tastaturhilfe** (oder die Taste **?**) listet alle Tasten. Die wichtigsten:

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

- **Raster:** Die Rasterstufen sind 1 cm, 5 cm, 10 cm, 25 cm, 50 cm und 1 m. Bei kleinem Zoom zeichnet der Plan nur die Stufen, deren Linien weit genug auseinander liegen. Mit **Raster anzeigen** (oder **G**) blendest du die Linien aus; das Einrasten bleibt davon unberührt.
- **Einrasten:** Der Schalter **Einrasten** lässt Objekte beim Verschieben, Zeichnen und Ziehen der Griffe am Raster und an Ecken und Kanten anderer Objekte einrasten.
- **Längeneinheit:** Du wählst Meter oder Zentimeter für alle Maßangaben im Editor. Gespeichert wird immer in Metern.
- **Zoom:** Die festen Stufen sind 25, 50, 100, 200 und 400 Prozent; **Anpassen** zeigt den ganzen Plan. Der Maßstabsbalken zeigt, wie lang eine Strecke auf dem Plan ist.
- **Kompass:** Stelle den **Nordwinkel** ein, damit der Plan weiß, wo geografisch Norden liegt: durch Drehen des Zifferblatts, mit den Pfeiltasten oder durch Eintippen (0 bis unter 360 Grad im Uhrzeigersinn; 0 heißt: Norden ist oben). Der Kompass im Handy liefert magnetisch Nord; Kamerplanter übernimmt ihn deshalb nie automatisch.
- **Übersichtskarte:** siehe [Im Gartenplan schneller arbeiten](#plan-komfort).

### Eigenschaften und Listenansicht

Das **Eigenschaften**-Feld zeigt zum gewählten Beet oder Objekt Name, Typ, Position (x nach rechts, y nach oben, in Metern), Maße und Drehung gegen den Uhrzeigersinn. Du änderst die Werte direkt; über **Sperren** schützt du ein Objekt vor versehentlichem Verschieben. Bei einem Beet findest du hier auch **Bepflanzen**, die Sonnen-Kacheln und die Zahl der offenen und überfälligen Aufgaben mit einem Sprung zum Pflege-Tab. Bei einem Vieleck listet das Feld die Punkte.

Die Listenansicht zeigt dieselben Objekte als Liste mit Bereichen, Beeten und Gartenobjekten. Zu jedem Eintrag gibt es Verschieben-Schaltflächen, die Eingabe einer Zielposition und Löschen. Sie ist die Alternative für Bildschirmleser und für alle, die nicht zeichnen wollen.

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

Änderungen im Editor werden zuerst nur lokal angewandt. Die Leiste über dem Plan zeigt den Stand: **Ungespeicherte Änderungen (n)**, **Speichern …**, **Gespeichert**, **Konflikt** oder **Speichern fehlgeschlagen**. **Speichern** (oder **Strg + S**) schickt alle offenen Änderungen in einem Schritt zum Server: Entweder werden alle übernommen oder keine. Der Schalter **Automatisch speichern** erledigt das für dich, siehe unten.

- **Rückgängig und Wiederholen** (Strg + Z, Strg + Umschalt + Z) gelten für die letzten 100 Schritte. Der Verlauf gilt nur für diese Sitzung: Lädst du die Seite neu, ist er weg.
- **Konflikt:** Hat jemand anderes den Plan gespeichert, während du daran gearbeitet hast, nimmt der Server deine Änderungen nicht an. Ein Dialog nennt, wer zuletzt geändert hat. Du kannst deine Änderungen vorher als Kopie (JSON) herunterladen und dann **Neu laden**. Beim Neuladen gehen deine ungespeicherten Änderungen und der Rückgängig-Verlauf verloren.
- **Abgelehnt:** Verletzt eine Änderung eine Regel, lehnt der Server das ganze Speichern ab und die Meldung nennt die Stelle. Häufige Gründe: Zwei Beete überlappen sich, ein Objekt ragt aus der Gartengrenze, auf einem Beet wachsen noch Pflanzen (Löschen erst nach dem Räumen), mehr als 500 Änderungen sind offen, oder der Plan hat sein Limit von 500 Standorten und Objekten zusammen erreicht. Korrigiere die genannte Stelle oder mache sie rückgängig; deine übrigen Änderungen bleiben erhalten.
- **Löschen:** Solange du nicht gespeichert hast, kannst du Löschen rückgängig machen. Nach dem Speichern nicht mehr. Der Dialog nennt vorher, was mit gelöscht wird.

## Ein Beet bepflanzen {#ein-beet-bepflanzen}

Wähle ein Beet und klicke im Eigenschaften-Feld auf **Bepflanzen**. Es öffnet sich der Pflanzdialog, den du auch aus der Beetansicht kennst. Du wählst Art und Sorte, siehst Hinweise zu Fruchtfolge, Nachbarn und Standort, legst die Anordnung fest (Raster, Reihen, Versetzt, Fläche oder Freie Positionen), siehst eine Vorschau und planst die Pflanzung oder erfasst sie sofort. Mit der Rolle „grower" ist das möglich, das Beet muss im Plan stehen und darf nicht stillgelegt sein. Die Schritte stehen unter [Beet bepflanzen](locations-substrates.md#beet-bepflanzen).

Pflanzen erscheinen auf dem Plan als Marker. Die Zustandsebene beschreibt der Abschnitt [Pflanzenzustand und Filter](#pflanzenzustand-und-filter).

## Beetliste im Gartenplan {#beetliste-im-gartenplan}

Unter dem Plan auf der Gartenplan-Seite listet eine Tabelle deine Beete: Name (als Link zur Beetansicht), Typ, Fläche, Status, Zuständige, Pflanzen, offene Aufgaben (mit überfälligen) und nächste Fälligkeit. Stillgelegte Beete sind standardmäßig ausgeblendet. Der Schalter **Meine Beete** filtert auf deine Beete und setzt voraus, dass dir Beete zugewiesen sind.

Klickst du auf eine Zeile oder drückst die Eingabetaste, wird das Beet im Plan ausgewählt und die Ansicht zoomt darauf. Die Zahl in der Spalte „Offene Aufgaben" ist ein Link zum Pflege-Tab des Beets. Ab der Rolle „grower" findest du über der Tabelle die Schaltfläche **Aufgaben auf mehreren Beeten erledigen** (siehe [Pflege am Beet](locations-substrates.md#pflege-am-beet)).

## Feldmodus im Garten {#feldmodus-im-garten}

Der Feldmodus ist für das Smartphone im Beet gedacht: große Schaltflächen (mindestens 64 Pixel), starker Kontrast für Sonnenlicht und nur das, was du draußen brauchst. Auf einem schmalen Bildschirm (unter 600 Pixel Breite) öffnet die Gartenplan-Seite direkt im Feldmodus. Auf jedem Gerät wechselst du über **Feldmodus** bzw. **Planungsmodus** oben auf der Seite; die Adresse trägt dann `?mode=field` bzw. `?mode=plan`.

**Meine Beete · heute fällig.** Der Feldmodus startet mit der Liste deiner Beete. Beete, die dir zugewiesen sind, stehen oben (markiert mit **Meins**), danach Beete mit überfälligen oder heute fälligen Aufgaben, dann die übrigen nach ihrer nächsten Fälligkeit. Überfällig ist eine Aufgabe, deren Fälligkeitstag vor dem heutigen Tag liegt; eine Aufgabe, die heute fällig ist, zählt noch nicht als überfällig. Stillgelegte Beete fehlen in der Liste. Der Tab **Karte** zeigt den Plan ohne Werkzeuge, Raster und Griffe. Mit **Vergrößern**, **Verkleinern** und **Ganzer Plan** änderst du die Ansicht. Tippst du auf ein Beet oder knapp daneben, zoomt die Karte auf das Beet und öffnet es.

**Das Beet-Blatt.** Ein Tipp auf ein Beet öffnet unten ein Blatt mit dem Namen des Beets, dem Schnellprotokoll, den Aufgaben und den Pflanzen. Die Aufgaben stehen in der Reihenfolge **Überfällig**, **Heute fällig**, **Später**. Die Pflanzen siehst du nach Art, Anzahl und Phase gruppiert; die Phasenfarbe hat immer einen schwarzen Rand und den Namen daneben.

- **Erledigt** öffnet den kurzen Dialog mit den freiwilligen Feldern (Menge, Notiz). **Fertig** speichert. Das sind zwei Tipps nach der Beetauswahl. Ein doppelter Tipp zählt nur einmal, und die Schaltflächen bleiben gesperrt, bis die Antwort da ist.
- **Schnellprotokoll:** **Gegossen**, **Gesät** und **Gejätet/Gemulcht** speichern mit einem Tipp einen Pflegeeintrag. **Geerntet** und **Notiz** öffnen das kurze Formular (Menge bzw. Text; für die Notiz kannst du die Spracheingabe deiner Tastatur nutzen). **Gepflanzt** öffnet den Pflanzdialog mit eingeschaltetem **Ich habe schon gepflanzt**; die Pflanzen entstehen sofort. Das geht nur bei einem Beet, das im Plan eingezeichnet ist.
- Nach **Erledigt** und nach jedem Schnellprotokoll siehst du acht Sekunden lang **Rückgängig**. Damit nimmst du den Eintrag zurück.
- **Pflanzen zeigen** listet die einzelnen Pflanzen einer Gruppe. **Position korrigieren** verschiebt eine Pflanze mit den Pfeilen in 10-cm-Schritten; ziehen kannst du den Marker erst, nachdem du ihn eine halbe Sekunde gehalten hast. **Foto** nimmt ein Bild für die Galerie der Pflanze auf.

Löschen, Beet räumen, Export und Import gibt es im Feldmodus nicht – dafür wechselst du in den Planungsmodus. Wer die Rolle „viewer" hat, sieht Aufgaben und Pflanzen nur lesend. Dein Browser merkt sich Mandant, Standort, Tab und Kartenausschnitt, nicht dein Konto; meldet sich jemand anderes auf dem Gerät an, beginnt der Feldmodus für diese Person neu. Zeigt ein gemerkter Kartenausschnitt auf dem aktuellen Bildschirm kaum noch etwas vom Plan – etwa nach dem Drehen des Smartphones –, öffnet die Karte mit dem ganzen Plan.

!!! warning "Noch nicht implementiert"
    Ohne Verbindung zeigt der Feldmodus einen Hinweis und sperrt **Erledigt** und das Schnellprotokoll; Einträge werden noch nicht zwischengespeichert und später gesendet. Fotos hängen vorerst an einer Pflanze, nicht am Beet. Für **Gepflanzt** gibt es kein **Rückgängig**. Die Hilfe per GPS und der QR-Code am Beet folgen später. Die Ebene „Zuletzt gegossen" gibt es nur im Planungsmodus. <!-- REQ-053 GP-UX-020…031, GP-FR-149 -->

## Ebenen und Standortbedingungen {#ebenen-und-standortbedingungen}

Ebenen blendest du in der Gruppe **Ebenen** der Ansichtsleiste ein und aus. Deine Wahl merkt sich der Browser; sie gilt nur für dich.

| Ebene | Zeigt | Zu Beginn |
|-------|-------|-----------|
| Raster | Rasterlinien (Taste **G**) | an |
| **Bewässerungszonen anzeigen** | Zonen als Umriss mit Schraffur über ihren Beeten | aus |
| **Zuletzt gegossen anzeigen** | Tage seit dem letzten erfassten Gießen je Beet als Schraffur | aus |
| **Unterlage anzeigen** | Das Hintergrundbild (nur sichtbar, wenn der Standort eine Unterlage hat) | an |
| **Sonnenfenster anzeigen** | Wann die direkte Sonne ein Beet erreicht | aus |
| **Drainage anzeigen** | Wie gut ein Beet Wasser ableitet | aus |
| **Frostrisiko anzeigen** | Gering, normal oder hoch je Beet | aus |
| **Pflanzenzustand anzeigen** | Phase, Ring und Zeichen jeder Pflanze | aus |

Die Legende unter der Ansichtsleiste erklärt jede eingeschaltete Ebene. Die Schraffur der Zonen und der Zustandsebenen unterscheidet sich im Muster, nicht nur in der Farbe.

Die Ebene **Zuletzt gegossen** zeigt nur den Abstand zum letzten erfassten Gießen in vier Stufen (0 bis 1, 2 bis 3, 4 bis 7, mehr als 7 Tage). Ob ein Beet Wasser braucht, sagt sie nicht. Ein Beet ohne erfasstes Gießen bleibt ohne Schraffur.

### Sonnenfenster, Drainage und Frostrisiko {#sonnenfenster-drainage-frostrisiko}

Die Werte pflegst du am Beet: Sonne, Sonnenzeit und Laubschatten in den Sonnen-Kacheln (siehe [Sonne und Schatten am Beet](locations-substrates.md#sonne-und-schatten-am-beet)), die Drainage im Bodenprofil. Die Ebenen zeigen diese Angaben auf dem ganzen Plan.

**Ebenen Sonnenfenster, Drainage und Frostrisiko im Gartenplan.** In der Ebenen-Gruppe der Ansichtsleiste blendest du drei weitere Ebenen ein: **Sonnenfenster anzeigen** (wann die direkte Sonne das Beet erreicht), **Drainage anzeigen** (schlecht, mittel, gut) und **Frostrisiko anzeigen** (gering, normal, hoch). Jeder Wert hat ein eigenes Muster, du erkennst ihn also auch ohne Farbe. Das Muster siehst du immer; sobald du so weit hineinzoomst, dass die Beetnamen erscheinen, kommt am unteren Beetrand ein kleines Symbol für den Wert dazu, sofern das Beet dafür Platz hat; die Legende unter der Ansichtsleiste erklärt jede eingeschaltete Ebene. Ein Beet ohne erfassten Wert bleibt ohne Muster. Alle drei Ebenen sind zu Beginn aus, und deine Wahl merkt sich der Browser für dich. Die Frost-Ebene zeigt das gespeicherte Frostrisiko; maßgeblich für die Überwinterung bleibt die Frostexposition. <!-- REQ-053 GP-FR-169, GP-FR-047 -->

### Pflanzenzustand und Filter {#pflanzenzustand-und-filter}

Was Scheibe, Ring und Zeichen an einer Pflanze bedeuten, steht unter [Pflanzenzustand und Pflanzen-Info](locations-substrates.md#pflanzenzustand). Im Gartenplan gilt für die Ebene:

**Ebene Pflanzenzustand und Filter im Gartenplan.** Mit **Pflanzenzustand anzeigen** in derselben Ebenen-Gruppe siehst du den Zustand deiner Pflanzen, ohne ein Beet zu öffnen. Zoomst du nah genug an ein Beet, dass die einzelnen Pflanzen erscheinen, trägt jede Pflanze Scheibe, Ring und Zeichen wie im Tab **Plan** des Beets: Die Farbe zeigt die Wachstumsphase, der Ring den Stand der Pflanzung, das Zeichen oben rechts den dringendsten Handlungsbedarf. Weiter herausgezoomt fasst jedes Beet seine Pflanzen zu einem Kreis mit Zahl zusammen; hast du ein Beet vorher schon nah genug gesehen, kennt Kamerplanter seine Zustände: Dann zeigt der Kreis das dringendste Zeichen, und der Vorleser nennt die Zahl aller Pflanzen des Beets und wie viele davon Handlungsbedarf haben. Daneben liegt der Schalter **Nur Pflanzen mit Handlungsbedarf zeigen**: Er blendet alle Pflanzen aus, deren Zustand bekannt ist und die kein Zeichen tragen. Eine Pflanze, deren Zustand noch nicht geladen ist, bleibt sichtbar. Der Kreis eines Beets zeigt dann nur die Pflanzen, die übrig bleiben, und verschwindet erst, wenn alle Zustände des Beets bekannt sind und keine Pflanze Handlungsbedarf hat; das Beet selbst bleibt sichtbar, und der Vorleser nennt weiter die Zahl aller Pflanzen. Solange die Ebene aus ist, ist der Schalter gesperrt; du erreichst ihn trotzdem mit der Tabulatortaste, und der Vorleser sagt dir, warum er gesperrt ist. Die Legende unter der Ansichtsleiste erklärt Ringe und Zeichen und listet die Farben der Wachstumsphasen der Pflanzen, deren Zustände geladen sind, alphabetisch in deiner Sprache. Kamerplanter lädt die Zustände nur, solange die Ebene an ist, und nur für die Beete, die du gerade nah genug siehst, höchstens vier Beete gleichzeitig. Jedes Beet lädt einmal und neu, wenn du zum Tab zurückkehrst, den Plan speicherst oder eine neuere Fassung des Plans lädt, und nachdem du im Bewässerungsbereich eine Zone geändert oder eine Gießrunde erfasst hast. Die Ebene und der Filter sind zu Beginn aus; deine Wahl merkt sich der Browser. Die Info-Blase beim Überfahren einer Pflanze bleibt dem Tab **Plan** des Beets vorbehalten. <!-- REQ-053 GP-UX-061, GP-UX-060 -->

!!! warning "Teilweise verfügbar: Pflanzenzustand"
    **Frostgefahr** erscheint noch nicht als Zeichen, auch wenn die Ebene **Frostrisiko** den gespeicherten Wert zeigt. **Fälliges Gießen** entsteht bisher nur aus einer Gießaufgabe, die heute fällig ist, nicht aus dem Bewässerungsbedarf. <!-- REQ-053 GP-UX-060, GP-FR-190 -->

## Bewässerungszonen und Gießrunde {#bewasserungszonen}

Eine **Bewässerungszone** fasst Beete eines Standorts zusammen, die gemeinsam gegossen werden, etwa an einem Tropfschlauch oder unter einem Regner. Ein Beet gehört zu höchstens einer Zone. Der Standort kann bis zu 500 Zonen haben.

Klicke auf **Bewässerungszonen verwalten**, um den Zonen-Bereich zu öffnen.

1. **Zone anlegen:** Klicke auf **Neue Zone**. Gib einen Namen ein, wähle die **Art der Bewässerung** (Von Hand, Tropfbewässerung, Regner, Perlschlauch oder Staubewässerung) und eine Farbe. Optional trägst du eine Wasserquelle (ein Gartenobjekt vom Typ Wasserquelle), den Durchfluss in Litern pro Minute und einen Hinweis zum Zeitplan ein.
2. **Beete zuordnen:** Hake die Beete an oder übernimm die Auswahl vom Plan mit **Auswahl vom Plan übernehmen**. Ein Beet, das schon in einer anderen Zone liegt, wechselt in diese; die Oberfläche sagt es dir. Beete und Wasserquellen, die du noch nicht gespeichert hast, stehen erst nach dem Speichern des Plans zur Auswahl.
3. **Zone speichern.** Lesen dürfen alle Mitglieder; ändern ab der Rolle „grower", löschen nur die Leitung. Löschst du eine Zone, bleiben die Beete unverändert und gehören danach zu keiner Zone; das Gießprotokoll bleibt erhalten.

**Stand der Zone.** Zu jeder Zone zeigt Kamerplanter, wann zuletzt gegossen wurde, das nächste geplante Gießen, den **Bedarf heute** (netto und brutto, mit Wirkungsgrad aus der Zone oder als Richtwert der Bewässerungsart), den **Verbrauch der letzten 30 Tage** mit seiner Herkunft sowie Hinweise, etwa wie lange die Wasserquelle bei diesem Tagesbedarf reicht.

**Gießrunde protokollieren.** Wenn du eine ganze Zone gegossen hast, öffnet **Gießrunde protokollieren** einen Dialog: Du gibst die **Gesamtmenge in Litern** an (größer als 0, höchstens 100 000) und wählst die **Verteilung**: **Nach Beetfläche** (jedes Beet bekommt einen Anteil nach seiner Fläche; Beete ohne Fläche bleiben außen vor) oder **Zu gleichen Teilen**. Kamerplanter schreibt für jedes Beet einen Gießeintrag ins Pflegeprotokoll. Die Menge ist verteilt, nicht gemessen; das Protokoll kennzeichnet das so.

!!! info "Nur über API / Betreiber-Konfiguration: Technische Kopplung"
    Die Kopplung einer Zone an einen Aktor oder an eine Home-Assistant-Entität für den Durchfluss pflegen nur Mitglieder mit dem Verwaltungsbereich `technical`, und zwar über die API. Beim Zurückspielen einer Sicherung werden diese Verknüpfungen nie übernommen. Siehe [Für technische Nutzer / Self-Hoster](#fur-technische-nutzer-self-hoster).

## Beetvorlagen {#beetvorlagen}

Eine Beetvorlage legt Form, Maße, Beettyp und Höhe eines Beets fest, damit du dieselbe Form nicht jedes Mal neu zeichnest. Kamerplanter bringt Standardgrößen mit, zum Beispiel Beet 1 × 1 m, 2 × 1 m, 3 × 1,2 m und 4 × 1,2 m, Hochbeet 1,2 × 2,4 m und 2 × 1 × 0,8 m sowie Kübel mit 0,3, 0,4 und 0,5 m Durchmesser. Eigene Vorlagen gehören zu deinem Garten.

- **Platzieren:** **Aus Vorlage** in der Werkzeugleiste, siehe [Im Gartenplan schneller arbeiten](#plan-komfort).
- **Speichern:** Wähle genau ein Beet und klicke auf **Als Vorlage speichern**. Pflanzen, Aufgaben und Notizen gehören nicht dazu. Ein Garten kann bis zu 200 eigene Vorlagen haben; ist die Grenze erreicht, löschst du erst eine nicht mehr benötigte.
- **Rollen:** Vorlagen legen Gärtner und die Leitung an; löschen darf nur die Leitung.

## Unterlage zum Abzeichnen {#unterlage}

Mit einer **Unterlage** legst du ein Foto, eine Skizze oder ein Luftbild unter den Plan und zeichnest die Beete darauf ab.

1. Klicke auf **Unterlage** und wähle ein Bild (JPEG, PNG oder WebP). Der Plan braucht dafür schon eine Gartengrenze.
2. **Eichen:** Klicke im Bild zwei Punkte an, deren Abstand du kennst, und gib den Abstand in Metern an. Daraus rechnet Kamerplanter den Maßstab (Pixel pro Meter).
3. **Lage:** Lege fest, wo die obere linke Ecke des Bildes auf dem Plan liegt, drehe das Bild bei Bedarf gegen den Uhrzeigersinn und stelle die Deckkraft ein.
4. **Speichern.** Mit **Unterlage entfernen** löschst du Bild und Eichung wieder; du müsstest beides neu anlegen.

Ein Standort hat höchstens eine Unterlage, und alle Mitglieder sehen dieselbe. Ob du sie anzeigst, entscheidest du für dich mit der Ebene **Unterlage anzeigen**. Setzen und entfernen dürfen Gärtner und die Leitung. Die Unterlage liegt unter allen Objekten, steht nicht in der JSON-Sicherung und kommt nur dann in den PDF-Druck, wenn die API-Abfrage es ausdrücklich verlangt (der Export-Dialog bietet das nicht an). Luftbilder können verraten, wo du wohnst: Gib einen Plan mit Unterlage nur weiter, wenn du das willst.

## Änderungsprotokoll {#anderungsprotokoll}

Kamerplanter schreibt zu jedem Plan ein Änderungsprotokoll: Löschungen und Änderungen der Gartengrenze mit Zeitpunkt und Namen des Bearbeiters, außerdem die Stände, die ein Ersetzen beim Import überschrieben hat (siehe [Plan exportieren und Sicherung einspielen](#plan-export-import)). Einträge werden ein Jahr lang aufbewahrt. Das Protokoll hat in der Oberfläche keine eigene Seite; es ist über die API lesbar (siehe [Für technische Nutzer / Self-Hoster](#fur-technische-nutzer-self-hoster)).

Was an einem einzelnen Beet geschah, steht in dessen Historie: den Zeitstrahl der Fruchtfolge und die Liste aller Pflegeeinträge und Pflanzungen beschreibt [Historie des Beets](locations-substrates.md#historie-des-beets).

## Plan exportieren und Sicherung einspielen {#plan-export-import}

Auf der Gartenplan-Seite öffnet **Export & Import** zwei Dialoge.

**Plan exportieren** gibt es als PDF (Plan im Maßstab zum Ausdrucken), als SVG (Vektorgrafik) und als Sicherung (JSON). Du wählst Papier, Ausrichtung, Maßstab und die Ebenen; eine Vorschau zeigt, was herauskommt. Mit **Automatisch** nimmt Kamerplanter den feinsten Maßstab, der aufs Blatt passt, und schlägt A3 vor, wenn A4 zu grob würde. Passt ein fest gewählter Maßstab nicht aufs Blatt, sagt dir der Dialog das und lässt dich einen gröberen Maßstab oder A3 wählen. Auf dem Handy gibt es nur PDF und Sicherung mit den Standardoptionen. Der Export enthält keine Namen von Mitgliedern und keine Zuweisungen.

Im PDF und in der SVG zeigt jede Pflanze ihren Zustand wie im Plan: die Scheibe in der Farbe ihrer Wachstumsphase, einen Ring für ihren Stand (ein dicker Ring heißt *in Ernte*) und höchstens ein Zeichen für das Dringendste, etwa ein Dreieck für einen offenen Befund oder einen Tropfen, wenn Gießen fällig ist. Die Legende listet die Wachstumsphasen, Ringe und Zeichen, die auf dem Plan vorkommen. Von den Wachstumsphasen nennt sie höchstens die sechs mit den meisten Pflanzen; gibt es mehr, fasst ein Eintrag wie „+3 weitere Phasen“ den Rest zusammen, damit der Plan im gewählten Maßstab auf die Seite passt. Ein langer Phasenname wird mit „…“ gekürzt. Pflanzen einer Art mit eigener Phasenfolge tragen dieselbe Farbe wie im Plan. Ab 2 000 Pflanzen zeigt jedes Beet stattdessen nur die Zahl seiner Pflanzen. <!-- REQ-053 GP-UX-005, GP-UX-059, GP-UX-060 -->

Die **Sicherung** enthält Beete, Gartenobjekte, Pflanzplätze, Bodenprofile, Standortmerkmale und die Gartengrenze, aber keine Pflanzen und keine Aufgaben. Hast du im Plan Beete oder Gartenobjekte ausgewählt, kannst du die Sicherung auf **Nur die Auswahl** oder auf **Auswahl mit allem darunter** beschränken. Eine solche Teil-Sicherung enthält keine Gartengrenze; Verweise auf Dinge, die nicht in der Datei stehen, entfallen. Lesen darf sie jede Rolle.

**Sicherung einspielen** führt in drei Schritten durch den Import. Das darf nur die Leitung.

1. **Datei wählen:** Die Datei darf höchstens 5 MB groß sein. Kamerplanter prüft sie sofort, ohne etwas zu schreiben.
2. **Prüfbericht:** Du siehst, wie viel angelegt und gelöscht würde, welche Verweise nicht übernommen werden (zum Beispiel eine Bewässerungszone, die es hier nicht gibt) und welche Probleme die Datei hat, etwa überlappende Beete. Bei Problemen geht es nicht weiter.
3. **Modus:** *Hinzufügen* legt die Sicherung zusätzlich zum bestehenden Plan an. *Ersetzen* tauscht den Plan dieses Standorts aus. Dafür tippst du den Namen des Standorts ein. Vorher speichert Kamerplanter den bisherigen Plan als Snapshot im Änderungsprotokoll. Lade dir zur Sicherheit trotzdem vorher eine aktuelle Sicherung herunter.

Im Modus *Hinzufügen* kannst du alle Formen der Datei um einen Abstand verschieben (nach rechts und nach oben, in Metern), etwa um ein Beet an eine andere Stelle zu setzen. Mit **Wohin geht die Datei?** sagst du, ob die Datei aus diesem Standort, aus einem anderen Standort oder aus einem anderen Garten-Konto stammt. Für die beiden letzten gilt: Verweise, die nicht in der Datei stehen, werden nie gegen diesen Standort aufgelöst, sondern entfallen und stehen im Prüfbericht. Aus einem anderen Konto wird nichts gelesen, die Datei ist der Transportweg; du brauchst die Leitungsrolle in dem Konto, in das du einspielst.

**Früheren Stand wiederherstellen:** Im ersten Schritt des Imports öffnet dieser Knopf die Liste der Pläne, die ein *Ersetzen* überschrieben hat (ein Jahr lang aufbewahrt, höchstens die 20 neuesten je Standort, nur für die Leitung). Du wählst einen Stand, siehst den Prüfbericht und tippst den Namen des Standorts. Vorher speichert Kamerplanter den jetzigen Plan selbst als Stand, die Wiederherstellung lässt sich also zurücknehmen. Bewässerungszonen, die der Stand nicht nennt, werden dabei entfernt, und technische Zonen-Kopplungen (Aktor, Home-Assistant-Durchfluss) werden nicht wiederhergestellt; die richtest du danach neu ein. Das *Hinzufügen* legt keinen Stand an.

!!! warning "Beete mit aktiven Pflanzen"
    Ein Beet, in dem eine Pflanze steht, wird nie gelöscht. Solange es solche Beete gibt, weist *Ersetzen* die Datei ab. Wählst du die Option, diese Beete zu behalten, bleiben sie samt den Standorten darüber bestehen, und der Rest wird ersetzt.

**Neue Saison aus dem Vorjahr:** Im Menü **Export & Import** legt **Neue Saison aus dem Vorjahr …** für jedes Beet ohne aktive Pflanzen die Plätze des Vorjahres als freie Slots neu an (nur die Leitung, im selben Standort). Du gibst das Jahr der neuen Saison an; die Plätze stammen aus Abschlüssen des Jahres davor. Zuerst prüft Kamerplanter und zeigt je Beet, was passiert: Beete mit aktiven Pflanzen und stillgelegte Beete werden übersprungen und stehen im Bericht, ebenso ein Beet, das mit den neuen Plätzen über 2 000 Slots käme. Plätze, die schon als freier Slot da sind, werden nicht doppelt angelegt. Zonen, Pflanzen, Anbaudurchläufe und die Historie bleiben unverändert; Fruchtfolge- und Mischkultur-Hinweise nutzen weiter die Belegung des Vorjahres. Mit **„Hier stand …“ anzeigen** blendest du je Beet die Pflanzenfamilie des Vorjahres ein, nur zur Orientierung. Erst **Freie Slots anlegen** schreibt, in einem Schritt mit Eintrag im Änderungsprotokoll; hat sich der Plan seit der Prüfung geändert, prüfst du erneut. <!-- REQ-053 GP-FR-171 -->

Alle Schlüssel werden beim Einspielen neu vergeben. Verknüpfungen zu Home Assistant und zu Aktoren übernimmt Kamerplanter nie; die richtest du danach neu ein. Wer gerade ungespeicherte Änderungen am Plan hat, speichert oder verwirft sie zuerst. Im Feldmodus sind Export und Import ausgeblendet.

## Für technische Nutzer / Self-Hoster {#fur-technische-nutzer-self-hoster}

Dieser Abschnitt ist für alle, die den Plan über die API anlegen oder eine Installation betreiben. Alle Pfade liegen unter `/api/v1/t/{slug}/`.

- **Ersten Plan anlegen:** `PUT /sites/{key}/plan/boundary` mit der Gartengrenze (Rechteck oder Vieleck), optional `north_angle_deg`. Der erste Aufruf legt den Plan an.
- **Plan lesen:** `GET /sites/{key}/plan`. **Änderungsprotokoll lesen:** `GET /sites/{key}/plan/audit`.
- **PDF mit Unterlage:** `GET /print/garden-plan/{site_key}?underlay=true`.
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
