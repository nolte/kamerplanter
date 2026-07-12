# Berechnungen

Der Bereich **Berechnungen** bündelt fünf eigenständige Rechenwerkzeuge für Klima, Wachstum, Beleuchtung und Anbauplanung. Du brauchst dafür keine angelegte Pflanze oder einen Pflanzdurchlauf — trage einfach Werte ein oder wähle sie aus vorgegebenen Optionen, und Kamerplanter berechnet serverseitig das Ergebnis.

---

## Voraussetzungen

- Menüpunkt: **Pflanzen → Berechnungen** (Seite `/pflanzen/calculations`).
- Der Menüpunkt erscheint standardmäßig ab der [Erfahrungsstufe „Experte"](onboarding.md#schritt-1-erfahrungsstufe-wahlen). Bei einer niedrigeren Stufe blendest du ihn über das Modul **„Kalkulatoren (VPD/GDD/EC)"** in den [Modul-Einstellungen](module-visibility.md) manuell mit „Immer ein" ein.
- Für den Sonnenstand-Rechner: mindestens ein angelegter [Standort](locations-substrates.md) mit hinterlegten GPS-Koordinaten, falls du die Koordinaten nicht von Hand eingeben möchtest.

!!! note "Eigenständige Rechner, kein Bezug zu deinen Pflanzen"
    Die Ergebnisse dieser Seite fließen nicht automatisch in deine Pflanzdaten, Nährstoffpläne oder Phasenregeln ein — sie sind Überschlagswerkzeuge zum schnellen Nachrechnen. Automatische Phasenübergänge auf Basis von GDD konfigurierst du stattdessen direkt in den Stammdaten einer Pflanzenart, siehe [Wachstumsphasen](growth-phases.md).

Einen eigenen Rechner für Nährlösungen und Verdünnung (EC-Budget, Wasser-Mischer) findest du getrennt unter **Düngung → Nährstoff-Berechnungen** — dazu mehr in der [Dünge-Logik](fertilization.md#wasser-mischer-und-ec-budget-rechner).

---

## VPD-Rechner

Das Dampfdruckdefizit (VPD — Vapor Pressure Deficit) beschreibt, wie „durstig" die Luft ist, und ist der wichtigste Einzelwert für die Transpiration deiner Pflanzen. Der Rechner berechnet das aktuelle VPD aus Temperatur und Luftfeuchtigkeit und zeigt an, ob der Wert für die gewählte Wachstumsphase optimal, zu niedrig oder zu hoch ist.

**Eingaben:**

- **Wachstumsphase** — eine Auswahlliste (Sämling, Vegetativ, Blüte, Spülung, Reife, Ruhephase). Nach der Auswahl zeigt das Feld direkt das für diese Phase optimale VPD-Zielband an.
- **Temperatur** und **Luftfeuchtigkeit** — jeweils als Zahlenfeld mit zusätzlichem Schieberegler zur schnellen Anpassung, inklusive Einheit (°C bzw. %).

Das Ergebnis zeigt den berechneten VPD-Wert in kPa, eine Einordnung (optimal/zu niedrig/zu hoch) sowie das Zielband deiner gewählten Phase.

!!! tip "Hintergrund zur Formel und den Zielwerten je Phase"
    Eine ausführliche Erklärung der VPD-Berechnung (Tetens-Näherung) und aller Zielkorridore je Wachstumsphase findest du im Guide [VPD-Optimierung](../guides/vpd-optimization.md).

---

## GDD-Rechner

Wachstumsgradtage (GDD — Growing Degree Days) summieren die nutzbare Wärme, die eine Pflanze seit einem Startpunkt erfahren hat, und sind ein zuverlässigerer Reifeindikator als reine Kalendertage.

**Eingaben:**

- **Basistemperatur** — die Temperaturschwelle, unterhalb derer eine Pflanze nicht wächst. Ein Zahlenfeld sowie Schnellauswahl-Chips mit typischen Werten je Pflanzengruppe (Kühljahreszeit, Salat, Tomate, Mais, Warmjahreszeit) übernehmen den passenden Wert direkt in das Feld.
- **Tagestemperaturen** — eine editierbare Zeilenliste mit Tiefst- und Höchstwert pro Tag. Über **Tag hinzufügen** ergänzt du weitere Tage, über das Papierkorb-Symbol entfernst du einzelne Zeilen (mindestens eine Zeile bleibt erhalten). Liegt der Höchstwert einer Zeile unter dem Tiefstwert, markiert Kamerplanter die Zeile als ungültig und die Berechnung ist erst nach Korrektur möglich.

Das Ergebnis zeigt die akkumulierten GDD über alle eingetragenen Tage sowie die Anzahl der berücksichtigten Tage.

!!! tip "Basistemperaturen, Beispielrechnung und Vergleich zu Kalendertagen"
    Eine Tabelle mit Basistemperaturen häufiger Pflanzenarten, eine Schritt-für-Schritt-Beispielrechnung und der Vergleich zwischen GDD und reiner Kalenderzeit stehen im Guide [GDD-Berechnung](../guides/gdd-calculation.md). <!-- REQ-003 -->

---

## Photoperioden-Übergang & DLI-Rechner

Dieser Rechner plant einen schrittweisen Übergang der täglichen Belichtungsdauer (zum Beispiel beim Umstellen von der vegetativen Phase in die Blüte) und berechnet für jeden Übergangstag zusätzlich das Tageslichtintegral (DLI — Daily Light Integral), also die über den Tag summierte Lichtmenge.

**Eingaben:**

- **Aktuelle** und **Ziel-Belichtungsdauer** — je ein Schieberegler von 0 bis 24 Stunden.
- **Übergangstage** — die Anzahl der Tage, über die der Wechsel gestreckt werden soll.
- **Lichtintensität (PPFD)** — die Photosynthetische Photonenflussdichte (PPFD) deiner Beleuchtung in µmol/m²/s. Trage den Wert direkt ein oder nutze die Schnellauswahl-Chips für typische Phasenwerte (200/400/600). Ohne eigene Eingabe würde die Berechnung sonst stillschweigend mit einem Standardwert rechnen — das Feld macht diesen Wert jetzt sichtbar und anpassbar.
- **Licht Ein** — die Uhrzeit, zu der die Beleuchtung täglich angeht.

Das Ergebnis ist eine Tabelle mit einer Zeile pro Übergangstag: Belichtungsdauer, Ein-/Ausschaltzeit und das daraus berechnete DLI in mol/m²/d.

!!! example "Beispiel: Umstellung auf 12/12"
    Aktuelle Belichtungsdauer 18 h, Ziel 12 h, 7 Übergangstage: Kamerplanter verteilt die Reduzierung gleichmäßig über die 7 Tage und zeigt dir für jeden Tag die passende Ein-/Ausschaltzeit sowie das DLI bei deiner eingetragenen PPFD.

---

## Stellplatz-Kapazität

Schätzt, wie viele Pflanzen bei einem gegebenen Pflanzabstand auf eine Fläche passen — nützlich bei der Planung eines neuen Beets, Zeltes oder Tisches.

**Eingaben:**

- **Fläche** in m².
- **Pflanzabstand** in cm — ein Auswahlfeld mit typischen Reihenabständen (10–60 cm), das zusätzlich freie Eingaben eigener Werte erlaubt.

Das Ergebnis zeigt drei Kennzahlen als Kacheln: die maximal mögliche Anzahl Pflanzen, einen empfohlenen Optimalbereich sowie die Pflanzen pro m².

---

## Sonnenstand-Rechner

Berechnet Sonnenaufgang, Sonnenuntergang, Morgen- und Abenddämmerung sowie die Tageslänge für einen Ort und ein Datum — hilfreich zur Planung von Aussaatterminen oder Freiland-Beleuchtungszeiten.

**Eingaben:**

- **Standort übernehmen** (optional) — erscheint nur, wenn du bereits mindestens einen Standort mit GPS-Koordinaten angelegt hast. Wählst du einen Standort aus, füllt Kamerplanter Breitengrad, Längengrad und Zeitzone automatisch mit dessen hinterlegten Werten.
- **Breitengrad** und **Längengrad** — falls du keinen Standort übernimmst oder die Koordinaten anpassen willst.
- **Datum** — ein Datumsfeld, standardmäßig auf heute vorbelegt.
- **Zeitzone** — ein Auswahlfeld mit allen IANA-Zeitzonen (z. B. `Europe/Berlin`) statt eines Freitextfelds, sodass keine ungültige Zeitzone eingetragen werden kann.

Das Ergebnis zeigt Sonnenaufgang, Sonnenuntergang, Morgen- und Abenddämmerung sowie die berechnete Tageslänge in Stunden.

!!! tip "Standort statt manueller Koordinaten"
    Lege deinen Garten oder dein Grow-Zelt einmalig als [Standort](locations-substrates.md) mit GPS-Koordinaten und Zeitzone an — danach genügt im Sonnenstand-Rechner ein Klick auf **Standort übernehmen**, statt Koordinaten jedes Mal von Hand nachzuschlagen.

---

## Häufige Fragen

??? question "Warum sehe ich den Menüpunkt „Berechnungen" nicht?"
    Der Menüpunkt ist standardmäßig erst ab der Erfahrungsstufe „Experte" sichtbar. Stelle entweder deine [Erfahrungsstufe](onboarding.md) auf „Experte", oder blende das Modul „Kalkulatoren (VPD/GDD/EC)" gezielt über die [Modul-Einstellungen](module-visibility.md) ein, ohne die restliche Oberfläche umzustellen.

??? question "Wirkt sich eine Berechnung auf meine Pflanzendaten aus?"
    Nein. Alle fünf Rechner sind eigenständige Überschlagswerkzeuge — sie lesen keine Pflanzendaten und schreiben auch keine Ergebnisse in deine Pflanzen, Nährstoffpläne oder Phasenregeln zurück. Für automatische GDD-basierte Phasenübergänge hinterlegst du die Schwellenwerte direkt in den Stammdaten einer Pflanzenart.

??? question "Wo finde ich den EC-Rechner für Nährlösungen?"
    Der Nährstoff-Rechner (Mischprotokoll, Flächendosierung, Wasser-Mischer, EC-Budget-Rechner) liegt auf einer eigenen Seite unter **Düngung → Nährstoff-Berechnungen** — Details dazu in der [Dünge-Logik](fertilization.md#wasser-mischer-und-ec-budget-rechner).

??? question "Warum wird beim Sonnenstand-Rechner keine Standortauswahl angezeigt?"
    Die Standortauswahl erscheint nur, wenn mindestens ein [Standort](locations-substrates.md) mit hinterlegten GPS-Koordinaten existiert. Ohne passenden Standort trägst du Breitengrad, Längengrad und Zeitzone einfach manuell ein.

---

## Siehe auch

- [VPD-Optimierung (Guide)](../guides/vpd-optimization.md)
- [GDD-Berechnung (Guide)](../guides/gdd-calculation.md)
- [Wachstumsphasen](growth-phases.md)
- [Standorte und Substrate](locations-substrates.md)
- [Dünge-Logik](fertilization.md)
- [Module & Funktionen](module-visibility.md)
