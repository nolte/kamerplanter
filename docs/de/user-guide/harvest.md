# Erntemanagement

Das Erntemanagement begleitet Sie vom Erkennen der Erntereife über die Dokumentation des Erntebatches bis hin zur Qualitätsbewertung. Ein integriertes Sicherheitssystem prüft automatisch, ob laufende Pflanzenschutzbehandlungen die Ernte blockieren.

---

## Voraussetzungen

- Mindestens eine Pflanze in der Phase "Ernte" oder kurz davor (Blütephase)
- Alle aktiven Pflanzenschutzbehandlungen müssen ihre Karenzzeit eingehalten haben

---

## Erntereife erkennen

Kamerplanter zeigt für jede Pflanze eine Reifeprognose an, die auf der Anzahl Tage in der Blütephase und der Wachstumsgradtage (GDD) basiert. Diese Prognose ist ein Richtwert — die tatsächliche Entscheidung treffen Sie als Gärtner.

### Reifeindikatoren nach Pflanzentyp

**Blütenstände (z.B. Cannabis, Hopfen):**
- Trichom-Farbe unter der Lupe: Milchig-weiß = maximaler Wirkstoffgehalt, Bernstein = abnehmend
- Pistil-Färbung: > 70 % braun/orange
- Calyx-Schwellung: Voll entwickelt

**Fruchtgemüse (Tomate, Paprika, Gurke):**
- Farbumschlag von grün zur Sorten-Endfarbe
- Leichte Nachgiebigkeit beim Drücken
- Glänzende Schale

**Wurzelgemüse (Kartoffel, Möhre):**
- Mehr als 80 % totes Laub
- Harte, nicht-abreibbare Schale
- Sortenspezifische Größe erreicht

**Blattgemüse (Salat, Spinat):**
- Fester Kopfschluss bei Kopfsalaten
- Knackige Textur, kein bitterer Geschmack
- Vor Schossbildung ernten

---

## Karenzzeit-Prüfung (IPM-Sicherheitsgate)

!!! danger "Ernte bei aktiver Behandlung blockiert"
    Wenn eine Pflanzenschutzbehandlung noch innerhalb ihrer Karenzzeit (Pre-Harvest Interval) liegt, blockiert Kamerplanter die Ernte-Erstellung. Sie sehen eine klare Fehlermeldung mit dem Datum, ab dem die Ernte möglich ist.

Die Karenzzeit ist die Mindestwartezeit nach einer Pflanzenschutzbehandlung, bevor die Pflanze geerntet werden darf. Diese Zeiten sind gesetzlich geregelt und werden in Kamerplanter pro Behandlungsmittel hinterlegt.

**Beispiel:** Sie haben am 1. März ein Mittel mit 14 Tagen Karenzzeit ausgebracht. Eine Ernte ist frühestens am 15. März möglich. Wenn Sie am 10. März versuchen, einen Ernte-Batch zu erstellen, erscheint eine Fehlermeldung.

Mehr zur Karenzzeit: [Integrierter Pflanzenschutz (IPM)](pest-management.md)

---

## Ernte-Batch erstellen

### Schritt 1: Ernte starten

1. Öffnen Sie die Pflanze oder den Pflanzdurchlauf unter **Pflanzen** oder **Durchläufe**.
2. Klicken Sie auf **Ernte starten** oder **Ernte-Batch erstellen**.
3. Das System prüft automatisch alle Karenzzeiten. Falls eine Behandlung noch innerhalb der Karenzzeit liegt, erscheint eine Meldung.

### Schritt 2: Ernte-Details eingeben

| Feld | Beschreibung |
|------|-------------|
| Ernte-Datum | Datum der Ernte (Standard: heute) |
| Erntemethode | Kompletternte oder Teilernte |
| Frischmasse (g) | Gewicht des Ernteguts direkt nach der Ernte |
| Ernte-Typ | Blüte, Frucht, Blatt, Wurzel, Saatgut |
| Notizen | Beobachtungen, Besonderheiten |

**Erntemethoden:**
- **Kompletternte**: Die gesamte Pflanze wird geerntet. Die Pflanze wechselt anschließend in den Status "Abgeschlossen".
- **Teilernte** (gestaffelt): Nur Teile werden geerntet (z.B. zuerst die oberen Blütenstände). Die Pflanze bleibt aktiv für weitere Ernten.

### Schritt 3: Qualitätsbewertung (optional)

Tragen Sie optional eine Qualitätsbewertung ein:

| Bewertung | Beschreibung |
|-----------|-------------|
| A+ | Außergewöhnliche Qualität |
| A | Hohe Qualität, keine Mängel |
| B | Gute Qualität, kleinere Mängel |
| C | Akzeptable Qualität, deutliche Mängel |

Zusätzliche Felder (je nach Pflanzentyp):
- Aroma-Intensität (1–10)
- Optische Bewertung (1–10)
- Besonderheiten (z.B. "Keine Schädlingsschäden", "Leichter Botrytis-Befall an einer Rispe")

---

## Trocknungsphase dokumentieren

Nach der Ernte durchläuft vieles (z.B. Kräuter, Cannabis) eine Trocknungsphase. Diese können Sie in Kamerplanter verfolgen:

1. Öffnen Sie den Ernte-Batch unter **Ernte**.
2. Klicken Sie auf **Trocknungsphase starten**.
3. Tragen Sie Startgewicht, Zielfeuchte und Lagerungsbedingungen ein.
4. Erfassen Sie regelmäßig das aktuelle Trockengewicht — Kamerplanter berechnet den Trocknungs-Fortschritt.

**Optimale Trockenbedingungen (Orientierung für Kräuter und Cannabis):**
- Temperatur: 18–22 °C
- Luftfeuchte: 45–55 % rH
- Dauer: 7–14 Tage

---

## Ertragskennzahlen und Auswertung

Nach Abschluss eines Ernte-Batches berechnet Kamerplanter automatisch:

- **Trockengewicht** (nach Eingabe des Endgewichts)
- **Trocknungsverlust** (% Gewichtsverlust durch Trocknung)
- **Ertrag pro m²** (g/m², bezogen auf die Anbaufläche)
- **Ertrag pro Pflanze** (g/Pflanze)
- **Ertrag pro Tag in der Blütephase**

Diese Kennzahlen helfen Ihnen, Ihre Anbautechnik über mehrere Zyklen zu verbessern.

!!! tip "Kennzahlen vergleichen"
    In der Ernte-Übersicht können Sie Batches vergleichen. So sehen Sie, welcher Pflanzdurchlauf, welches Substrat oder welcher Nährstoffplan den besten Ertrag geliefert hat.

---

## Vor-Ernte-Protokolle

### Spülphase (Flushing)

Einige Gärtner führen vor der Ernte einen Spülgang durch, um überschüssige Salze aus dem Substrat zu waschen. Kamerplanter bietet dieses Protokoll optional an.

!!! note "Flushing ist wissenschaftlich umstritten"
    Studien (u.a. University of Guelph, 2020) konnten keinen signifikanten Unterschied zwischen geflushten und nicht-geflushten Pflanzen nachweisen. Bei Living Soil wird Flushing ausdrücklich nicht empfohlen, da es das Mikrobiom schädigt.

1. Öffnen Sie die Pflanze.
2. Klicken Sie auf **Spülprotokoll starten**.
3. Das System empfiehlt eine Spüldauer abhängig vom Substrat.
4. Während des Spülens erhalten Sie Gieß-Aufgaben mit reinem, pH-adjustiertem Wasser.

Mehr zum Spülprotokoll: [Dünge-Logik](fertilization.md)

### Dunkelphase

Manche Gärtner halten eine Dunkelphase von 24–48 Stunden direkt vor der Ernte ein. Kamerplanter kann Sie daran erinnern:

1. Öffnen Sie den Pflanzdurchlauf.
2. Klicken Sie auf **Dunkelphase planen**.
3. Wählen Sie Datum und Dauer.
4. Eine Aufgabe wird erstellt: "Beleuchtung abschalten — Dunkelphase beginnt".

---

## Häufige Fragen

??? question "Kann ich eine Ernte rückgängig machen?"
    Nein. Ernte-Batches können nach dem Erstellen nicht gelöscht werden, da sie zur lückenlosen Dokumentation des Anbaus gehören. Sie können jedoch Notizen und Gewichtswerte nachträglich korrigieren.

??? question "Was passiert mit einer Pflanze nach der Kompletternte?"
    Die Pflanze wechselt automatisch in den Status "Abgeschlossen". Sie ist nicht mehr aktiv und erscheint nicht mehr in der Aufgaben-Queue. Die Stammdaten und die Phasenhistorie bleiben für die Auswertung erhalten.

??? question "Warum wird die Ernte blockiert, obwohl ich schon lange nicht mehr behandelt habe?"
    Prüfen Sie im Tab **Pflanzenschutz** (IPM) die Liste aller Behandlungen und ihre Karenzzeiten. Manchmal sind ältere Behandlungen noch eingetragen, deren Karenzzeit noch nicht abgelaufen ist. Wenn die Behandlung irrtümlich eingetragen wurde, können Sie sie unter Pflanzenschutz korrigieren.

??? question "Kann ich eine Teilernte mehrfach durchführen?"
    Ja. Bei gestaffelter Ernte können Sie beliebig viele Teilernte-Batches für eine Pflanze erstellen, bis Sie die Kompletternte abschließen oder die Pflanze manuell als abgeschlossen markieren.

---

## Siehe auch

- [Integrierter Pflanzenschutz (IPM)](pest-management.md)
- [Wachstumsphasen](growth-phases.md)
- [Dünge-Logik](fertilization.md)
- [Pflanzdurchläufe](planting-runs.md)
