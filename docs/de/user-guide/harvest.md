# Erntemanagement

Das Erntemanagement begleitet dich von der Beobachtung der Erntereife über die Dokumentation der Erntecharge bis hin zur Qualitätsbewertung und den Ertragskennzahlen. Ein integriertes Sicherheitssystem prüft automatisch, ob laufende Pflanzenschutzbehandlungen die Ernte blockieren.

---

## Voraussetzungen

- Mindestens eine Pflanze in der Blütephase oder kurz vor der Ernte
- Alle aktiven Pflanzenschutzbehandlungen müssen ihre Karenzzeit eingehalten haben

---

## Erntereife erkennen

### Erwartetes Erntedatum

Für Pflanzen mit einer Erntephase zeigt Kamerplanter auf der Pflanzendetailseite ein **erwartetes Erntedatum** an. Es berechnet sich aus dem Pflanzdatum plus der Summe der geplanten Phasendauern (Wachstumsphasen-Verwaltung) und zeigt zusätzlich die verbleibenden Tage bzw. eine Überfälligkeits-Anzeige. Bei mehrjährigen Pflanzen oder Arten ohne definierte Erntephase erscheint kein Termin — hier hilft dir ausschließlich die Beobachtung vor Ort.

!!! info "Reife-Beobachtungssystem nur über API"
    Kamerplanter bietet zusätzlich ein Datenmodell für pflanzenspezifische Reife-Indikatoren (Trichome, Brix, Krautsterben, Farbe u. a.) mit Einzelbeobachtungen und einem gewichteten Reifegrad-Score. Dieses System ist vollständig über die API nutzbar, aber noch nicht an eine Oberfläche im Frontend angebunden — du kannst es aktuell nicht über Menüs bedienen. Bis zur Anbindung orientierst du dich an den folgenden manuellen Reifeindikatoren.

### Reifeindikatoren nach Pflanzentyp

Diese Richtwerte helfen dir bei der Einschätzung, unabhängig davon, ob du sie in Kamerplanter erfasst:

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

## Karenzzeit-Prüfung (Sicherheitsgate für Integrierten Pflanzenschutz, IPM)

!!! danger "Ernte bei aktiver Behandlung blockiert"
    Wenn eine Pflanzenschutzbehandlung noch innerhalb ihrer Karenzzeit (Pre-Harvest Interval, PHI) liegt, blockiert Kamerplanter die Erstellung der Erntecharge. Du siehst eine klare Fehlermeldung mit dem Wirkstoff und den verbleibenden Tagen.

Die Karenzzeit ist die Mindestwartezeit nach einer Pflanzenschutzbehandlung, bevor die Pflanze geerntet werden darf. Diese Zeiten sind gesetzlich geregelt und werden in Kamerplanter pro Behandlungsmittel hinterlegt.

**Beispiel:** Du hast am 1. März ein Mittel mit 14 Tagen Karenzzeit ausgebracht. Eine Ernte ist frühestens am 15. März möglich. Wenn du am 10. März versuchst, eine Erntecharge zu erstellen, blockiert das System die Erstellung.

Mehr zur Karenzzeit: [Integrierter Pflanzenschutz (IPM)](pest-management.md)

---

## Erntecharge erstellen

### Schritt 1: Charge anlegen

1. Öffne **Erntechargen** in der Navigation (`/ernte/batches`).
2. Klicke auf **Erntecharge erstellen**.
3. Das System prüft beim Speichern automatisch alle Karenzzeiten. Liegt eine Behandlung noch innerhalb der Karenzzeit, erscheint eine Fehlermeldung statt der neuen Charge.

### Schritt 2: Ernte-Details eingeben

| Feld | Beschreibung |
|------|-------------|
| Pflanze | Die zu erntende Pflanze |
| Chargen-ID | Optionale eigene Kennung, z.B. „ERNTE-2026-001" |
| Erntetyp | **Teilernte**, **Endernte** oder **Fortlaufend** |
| Erntedatum | Datum und Uhrzeit der Ernte (Standard: jetzt) |
| Nassgewicht (g) | Gewicht des Ernteguts direkt nach dem Schnitt |
| Erntehelfer | Wer hat geerntet? |
| Notizen | Beobachtungen, Besonderheiten |

**Erntetypen:**

- **Endernte**: Die gesamte Pflanze wird auf einmal geerntet.
- **Teilernte**: Nur ein Teil wird geerntet (z.B. zuerst die oberen Blütenstände). Du kannst beliebig viele Teilernte-Chargen für dieselbe Pflanze anlegen.
- **Fortlaufend**: Für „Cut & Come Again"-Kulturen (z.B. Pflücksalat, Basilikum), bei denen laufend kleine Mengen geerntet werden.

!!! note "Kein automatischer Status- oder Qualitätswechsel"
    Weder die Erntetyp-Auswahl noch das Anlegen einer Charge ändern automatisch den Status der Pflanze — auch nicht bei „Endernte". Du kannst für dieselbe Pflanze beliebig viele Teil- oder Fortlaufend-Chargen anlegen. Eine Qualitätsbewertung wird beim Anlegen der Charge ebenfalls nicht abgefragt; sie erfolgt separat (siehe unten). Wenn die Pflanze für dich fertig geerntet ist, beendest du ihren Lebenszyklus über die separate, explizite Aktion **Ernte abschließen** (siehe unten) — diese ändert den Status anders als das bloße Anlegen einer Charge sehr wohl, und zwar endgültig.

---

## Ernte abschließen (Endzustand der Pflanze)

Das Anlegen von Erntechargen dokumentiert, was du geerntet hast — es beendet aber, wie oben beschrieben, nicht den Lebenszyklus der Pflanze. Dafür gibt es die eigene Aktion **Ernte abschließen**.

### Was passiert dabei?

1. Öffne die Erntecharge und wechsle in den Tab **Details**.
2. Klicke im Abschnitt **Ernte abschließen** auf die gleichnamige Schaltfläche.
3. Bestätige den Dialog — er weist ausdrücklich darauf hin, dass der Schritt **nicht rückgängig gemacht werden kann**.

Nach der Bestätigung wechselt die Pflanze in ihren Endzustand „geerntet": Ihre Phasen-Historie wird geschlossen, ein belegter Stellplatz wird freigegeben, und die Pflanze verschwindet aus der aktiven Aufgaben-Warteschlange. Bereits erfasste Erntechargen, Qualitätsbewertungen und Ertragsdaten bleiben vollständig erhalten. Ein zweiter Klick auf eine bereits abgeschlossene Pflanze zeigt stattdessen einen Hinweis, dass sie bereits abgeschlossen ist, und ändert nichts mehr.

!!! danger "Nicht umkehrbar"
    Anders als bei Erntechargen oder Qualitätsbewertungen gibt es für den Ernte-Abschluss keine Korrektur- oder Rückgängig-Funktion. Nutze die Aktion erst, wenn du wirklich keine weiteren Teilernten oder Beobachtungen mehr für diese Pflanze planst.

Dieser Abschluss ist etwas anderes als **Pflanze entfernen** auf der Pflanzendetailseite: „Ernte abschließen" ist der empfohlene Weg für eine tatsächlich abgeschlossene Ernte und setzt zusätzlich den Erntegrund in der Historie der Pflanze. „Pflanze entfernen" bleibt für alle anderen Fälle verfügbar (z.B. eine Pflanze, die nicht geerntet wurde, sondern eingegangen ist oder abgegeben wurde).

!!! info "Nur über API: Ganzen Pflanzdurchlauf auf einmal abschließen"
    Gehört die Pflanze zu einem [Pflanzdurchlauf](planting-runs.md), lassen sich auch alle noch aktiven Pflanzen des gesamten Durchlaufs in einem Aufruf abschließen. Dafür gibt es aktuell **keine Schaltfläche in der Oberfläche** — die Funktion ist ausschließlich über die technische API erreichbar. Solange keine Oberfläche dafür existiert, schließt du Pflanzen eines Durchlaufs einzeln über ihre jeweilige Erntecharge ab.

<!-- Quelle: src/frontend/src/pages/ernte/HarvestBatchDetailPage.tsx, src/backend/app/domain/services/harvest_service.py (complete_harvest / complete_harvest_for_run), src/backend/app/api/v1/harvest/tenant_router.py -->

---

## Qualitätsbewertung

Öffne die Erntecharge und wechsle zum Tab **Qualität**, um eine Bewertung anzulegen.

| Feld | Beschreibung |
|------|-------------|
| Bewertet von | Name der bewertenden Person |
| Erscheinungsbewertung | 0–100 Punkte |
| Aromabewertung | 0–100 Punkte |
| Farbbewertung | 0–100 Punkte |
| Mängel | Frei eintragbare Schlagworte |
| Notizen | Zusätzliche Anmerkungen |

Kamerplanter berechnet daraus automatisch einen **Gesamt-Score (0–100)** und eine **Note**:

| Gesamt-Score | Note |
|--------------|------|
| ≥ 90 | A+ |
| ≥ 75 | A |
| ≥ 55 | B |
| ≥ 35 | C |
| < 35 | D |

Der Gesamt-Score gewichtet Erscheinung (30 %), Aroma (25 %) und Farbe (20 %) und zieht für erkannte Mängel Punkte ab.

<!-- Quelle: src/backend/app/domain/engines/quality_scoring_engine.py -->

!!! tip "Mängel-Schlagworte mit Punktabzug"
    Einige Mängel-Schlagworte werden vom System besonders stark gewertet, u.a. `mold` (Schimmel, −50), `hermaphrodite` (Zwitterblüten, −40), `pests` (Schädlinge, −30), `seeded` (samig, −25). Andere Schlagworte (`nutrient_burn`, `light_burn`: je −15; `foxtailing`, `discoloration`: je −10; `mechanical_damage`: −5) fallen weniger stark ins Gewicht. Unbekannte Schlagworte werden pauschal mit −5 bewertet.

---

## Trocknung dokumentieren

!!! note "Teilweise verfügbar"
    Kamerplanter bietet aktuell nur ein einzelnes Feld **Tatsächliches Trockengewicht (g)** im Bearbeiten-Tab der Erntecharge — du trägst es nach Abschluss der Trocknung manuell ein. Eine eigene Trocknungs-Workflow-Oberfläche mit Start-/Zielfeuchte, laufender Gewichtserfassung und automatischer Fortschritts- oder Trocknungsverlust-Berechnung ist als geplantes Feature spezifiziert, aber noch nicht gebaut. <!-- REQ-008 -->

Fachliche Anleitung zur Trocknung (Zielwerte für Temperatur, Luftfeuchte und Dauer) findest du im Nachernte-Guide.

Mehr dazu: [Nachernte: Trocknung, Curing & Lagerung](../guides/post-harvest.md)

---

## Ertragsmetriken

Öffne die Erntecharge und wechsle zum Tab **Ertrag**, um die Ertragsdaten manuell einzutragen:

| Feld | Beschreibung |
|------|-------------|
| Ertrag pro Pflanze (g) | Gesamtertrag dieser Pflanze |
| Ertrag pro m² (g) | Ertrag bezogen auf die Anbaufläche |
| Gesamtertrag (g) | Gesamtgewicht der Charge |
| Verschnitt (%) | Anteil Verschnitt am Gesamtertrag |
| Nutzbarer Ertrag (g) | Verwertbare Menge nach Verschnitt |

!!! note "Manuelle Eingabe — keine automatische Berechnung"
    Kamerplanter berechnet diese Werte nicht selbst aus Nass-/Trockengewicht oder Anbaufläche. Du trägst sie nach dem Wiegen und Verarbeiten selbst ein. Eine Vergleichs- oder Auswertungsansicht über mehrere Chargen und Pflanzdurchläufe hinweg ist noch nicht vorhanden — die Erntechargen-Übersicht listet Chargen nur tabellarisch.

---

## Vor-Ernte-Protokolle

### Spülphase (Flushing)

Einige Gärtner führen vor der Ernte einen Spülgang durch, um überschüssige Salze aus dem Substrat zu waschen.

!!! note "Teilweise verfügbar"
    Es gibt keinen Button an der Pflanze, der ein Spülprotokoll startet oder automatisch Gieß-Aufgaben erzeugt. Kamerplanter bietet stattdessen einen eigenständigen **Spülungs-Rechner** unter den Nährstoff-Rechnern, der dir eine empfohlene Spüldauer abhängig vom Substrat nennt. Die Gieß-Aufgaben während des Spülens legst du wie gewohnt manuell an oder erledigst sie über dein bestehendes Gießprotokoll.

!!! note "Flushing ist wissenschaftlich umstritten"
    Studien (u.a. University of Guelph, 2020) konnten keinen signifikanten Unterschied zwischen geflushten und nicht-geflushten Pflanzen nachweisen. Bei Living Soil wird Flushing ausdrücklich nicht empfohlen, da es das Mikrobiom schädigt.

Mehr zum Spülungs-Rechner: [Dünge-Logik](fertilization.md)

### Dunkelphase

Manche Gärtner halten eine Dunkelphase von 24–48 Stunden direkt vor der Ernte ein.

!!! warning "Noch nicht implementiert"
    Eine geplante Dunkelphase mit automatischer Beleuchtungs-Aufgabe wird es in einer zukünftigen Version geben. Aktuell musst du dir die Beleuchtungszeiten selbst notieren oder eine eigene Aufgabe unter [Aufgaben](tasks.md) anlegen.

---

## Häufige Fragen

??? question "Kann ich eine Ernte rückgängig machen?"
    Nein. Erntechargen können nach dem Erstellen nicht gelöscht werden, da sie zur lückenlosen Dokumentation des Anbaus gehören. Du kannst jedoch Notizen und Gewichtswerte nachträglich korrigieren. Der separate Schritt **Ernte abschließen** lässt sich ebenfalls nicht rückgängig machen — prüfe vor der Bestätigung, ob wirklich keine weiteren Teilernten mehr geplant sind.

??? question "Wechselt eine Pflanze nach der Endernte automatisch ihren Status?"
    Nein. Das Anlegen einer Erntecharge mit Erntetyp „Endernte" ändert den Pflanzen-Status nicht automatisch. Wenn die Pflanze für dich fertig geerntet ist, beendest du ihren Lebenszyklus explizit über **Ernte abschließen** auf der Detailseite der Erntecharge (siehe oben). Erst danach verschwindet sie endgültig und unumkehrbar aus der aktiven Aufgaben-Warteschlange und der belegte Stellplatz wird frei; ihre Stammdaten und Historie bleiben erhalten.

??? question "Warum wird die Ernte blockiert, obwohl ich schon lange nicht mehr behandelt habe?"
    Prüfe im Tab **Pflanzenschutz** (IPM) die Liste aller Behandlungen und ihre Karenzzeiten. Manchmal sind ältere Behandlungen noch eingetragen, deren Karenzzeit noch nicht abgelaufen ist. Wenn die Behandlung irrtümlich eingetragen wurde, kannst du sie unter Pflanzenschutz korrigieren.

??? question "Kann ich eine Teilernte mehrfach durchführen?"
    Ja. Du kannst beliebig viele Teilernte-Chargen für eine Pflanze anlegen, z.B. um zuerst die oberen und später die unteren Blütenstände zu ernten.

---

## Siehe auch

- [Integrierter Pflanzenschutz (IPM)](pest-management.md)
- [Wachstumsphasen](growth-phases.md)
- [Dünge-Logik](fertilization.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Nachernte: Trocknung, Curing & Lagerung](../guides/post-harvest.md)
