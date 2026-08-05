# Tagebuch

Halte an jeder Pflanze fest, was dir auffällt — mit Fotos, Tags und Messwerten — und behalte über alle Pflanzen hinweg im Blick, wo eine KI-Einschätzung dazu bereits vorliegt. Optional kannst du einzelne Einträge zur Analyse durch deinen eigenen KI-Agenten markieren.

---

## Voraussetzungen

- Du bist angemeldet (oder nutzt den [Light-Modus](light-mode.md) auf einem lokalen Gerät) und hast mindestens eine Pflanzeninstanz angelegt.
- Zum Anlegen, Bearbeiten, Löschen und Markieren von Einträgen benötigst du die Rolle **Gärtner** oder **Leitung** in deinem Mandanten. Als **Beobachter** kannst du alle Einträge und Analyse-Ergebnisse lesen, aber nichts davon anlegen oder markieren.
- Für das Markieren zusätzlich: die Einwilligung „Einzelne Tagebuch-Einträge dürfen von meinem KI-Agenten analysiert werden" (im Light-Modus automatisch erteilt, siehe [Light-Modus](#light-modus) unten).
- Für die Analyse selbst brauchst du einen **eigenen, selbst betriebenen KI-Agenten** — ohne ihn bleibt ein markierter Eintrag einfach liegen (siehe [Kamerplanter führt die Analyse nicht selbst aus](#kamerplanter-fuehrt-die-analyse-nicht-selbst-aus)).

---

## Was ist das Tagebuch?

Das Tagebuch gibt es an zwei Stellen mit unterschiedlicher Aufgabe:

| | Ort | Aufgabe |
|---|-----|---------|
| **Erfassung** | Tab **Tagebuch** an der Detailseite einer Pflanze | Einträge dieser einen Pflanze anlegen, bearbeiten, löschen, mit Fotos versehen und zur Analyse markieren |
| **Sichtung** | Seite **Tagebuch** in der Navigation (alle Pflanzen deines Gartens) | Alle Einträge aller Pflanzen zusammen sehen, filtern und den Analyse-Stand auf einen Blick prüfen |

Diese Trennung ist Absicht: Du erfasst dort, wo du die Pflanze gerade vor dir hast, und du sichtest dort, wo du alle Pflanzen zusammen siehst — ohne Pflanze für Pflanze durchklicken zu müssen.

---

## Einen Eintrag an einer Pflanze anlegen

1. Öffne das Seitenmenü und navigiere zu deinen **Pflanzen**.
2. Klicke auf die gewünschte Pflanze, um die Detailseite zu öffnen.
3. Wähle den Tab **Tagebuch**.
4. Klicke auf **Eintrag anlegen**.

Im Dialog trägst du ein:

- **Art des Eintrags** — Beobachtung, Problem, Meilenstein, Messung, Foto oder Notiz.
- **Titel** — optional; ohne Titel wird die Art des Eintrags angezeigt.
- **Beschreibung** — der einzige Pflichtwert; beschreibe frei, was du beobachtest.
- **Tags** — freie Stichworte, mit Enter bestätigt.
- **Messwerte** — optionale Zahlen oder Kurzangaben, z. B. Höhe in cm oder Blattanzahl.
- **Fotos** — bis zu **5 Fotos** je Eintrag, aufgenommen per Webcam, Smartphone-Kamera oder als Datei-Upload.

!!! note "Datenschutz: EXIF-Daten"
    Fotos werden vor dem Hochladen verkleinert und von EXIF-Metadaten befreit — dazu gehören GPS-Koordinaten, Kameramodell und Aufnahmezeitpunkt.

Neue Einträge erscheinen chronologisch absteigend, der jüngste zuerst.

### Eintrag bearbeiten oder löschen

Jeder Eintrag im Tab „Tagebuch" trägt eigene Schaltflächen zum Bearbeiten und Löschen — vorausgesetzt, du hast Schreibrechte in diesem Mandanten.

!!! warning "Löschen ist endgültig"
    Beim Löschen eines Eintrags werden auch alle angehängten Fotos und ein vorhandenes Analyse-Ergebnis mitgelöscht. Das lässt sich nicht rückgängig machen.

---

## Alle Einträge im Überblick: die Tagebuch-Übersicht {#alle-eintraege-im-ueberblick}

Über den Navigationspunkt **Tagebuch** erreichst du eine Liste, die die Einträge **aller** Pflanzen deines Gartens chronologisch absteigend zusammenführt:

| Spalte | Inhalt |
|--------|--------|
| Datum | Erfassungszeitpunkt des Eintrags |
| Pflanze | Name der Pflanzeninstanz, verlinkt auf deren Detailseite |
| Art | Wissenschaftlicher bzw. gebräuchlicher Name |
| Typ | Beobachtung, Problem, Meilenstein, Messung, Foto oder Notiz |
| Titel / Auszug | Titel, sonst der Anfang der Beschreibung |
| Fotos | Anzahl angehängter Fotos mit Miniaturvorschau |
| Analyse | Der Analyse-Zustand, siehe unten |

Du kannst filtern und sortieren — unter anderem:

- **Nach Analyse-Zustand**, mit den beiden häufigsten Schnellfiltern direkt sichtbar: **„Nur mit Ergebnis"** und **„Nur wartend"**.
- Nach Pflanze, Art, Eintragstyp, Tag und Zeitraum. Auf kleinen Bildschirmen sind diese zusätzlichen Filter hinter **„Weitere Filter"** eingeklappt.
- Über die **Freitextsuche**, die Titel und Beschreibung aller Einträge durchsucht — nicht nur die gerade angezeigte Seite.
- Nach Erfassungsdatum (Vorgabe) oder Analyse-Zeitpunkt.

Ein Klick auf eine Zeile öffnet den vollständigen Eintrag samt Fotos und — falls vorhanden — dem Analyse-Ergebnis. Die Übersicht lädt sich nicht von selbst neu; nutze die Schaltfläche **Aktualisieren**, um den aktuellen Stand zu holen.

!!! note "In einem Gemeinschaftsgarten siehst du auch fremde Einträge"
    Die Übersicht ist mandantenweit: In einem Gemeinschaftsgarten erscheinen dort auch Einträge anderer Mitglieder. Markieren darfst du trotzdem nur deine eigenen — fremde Zeilen zeigen den Analyse-Zustand, aber keine Schaltfläche zum Markieren (Ausnahme: Rolle Leitung, siehe [Wer darf markieren?](#wer-darf-markieren)).

---

## Einen Eintrag zur KI-Analyse markieren

Öffne einen Eintrag — im Tab „Tagebuch" der Pflanze oder in der Übersicht — und klicke auf **Analysieren**. Der Eintrag wechselt in den Zustand „Wartet auf Analyse". Solange dieser Zustand andauert, kannst du die Markierung über **Markierung zurücknehmen** wieder aufheben; sobald ein Agent den Eintrag übernommen hat, geht das nicht mehr.

Es wird **nie** automatisch etwas analysiert — es gibt keinen Automatismus, keine Voreinstellung „alles analysieren" und keinen Regelsatz, der Einträge nach Stichwort auswählt. Jeden Eintrag markierst du einzeln, aus freien Stücken.

### Kamerplanter führt die Analyse nicht selbst aus {#kamerplanter-fuehrt-die-analyse-nicht-selbst-aus}

!!! warning "Ohne deinen eigenen Agenten passiert nichts"
    Kamerplanter ruft selbst **kein** Sprachmodell auf — es gibt in deiner Instanz weder einen Modellschlüssel noch einen ausgehenden Aufruf noch dadurch entstehende Kosten. Die eigentliche Analyse übernimmt ein **externer Agent, den du selbst betreibst** und der deine markierten Einträge über deinen eigenen API-Schlüssel abholt. Ohne einen laufenden Agenten bleibt ein markierter Eintrag im Zustand „Wartet auf Analyse" stehen — dauerhaft, bis du einen Agenten startest. Das ist eine bewusste Eigenschaft dieser Funktion, kein Fehler: Deine Instanz bleibt dadurch ohne Modellschlüssel und ohne Netzausgang betreibbar.

    Ein passendes Agenten-Rezept liegt in einem eigenen, von Kamerplanter getrennten Repository. Wenn du deinen eigenen Agenten aufsetzen willst, findest du die technische Schnittstelle dazu unter [MCP-Server](../api/mcp-server.md).

!!! note "Keine Zusage über die Bearbeitungsdauer"
    „Wartet auf Analyse" heißt genau das — es gibt keinen Fortschrittsbalken und keine Schätzung, wie lange es dauert. Das hängt allein davon ab, wann dein Agent das nächste Mal läuft.

### Wer darf markieren?

- **Beobachter** dürfen Einträge und Ergebnisse lesen, aber nicht markieren.
- **Gärtner** dürfen nur Einträge markieren, die sie **selbst verfasst haben**.
- **Leitung** darf jeden Eintrag im Mandanten markieren, auch die anderer Mitglieder.

Diese Einschränkung gilt zusätzlich zur Einwilligung — beides muss zutreffen, damit sich ein Eintrag markieren lässt: die passende Rolle bzw. Autorschaft **und** die erteilte Einwilligung „Einzelne Tagebuch-Einträge dürfen von meinem KI-Agenten analysiert werden". Fehlt eine der beiden Voraussetzungen, bleibt die Schaltfläche entweder verborgen oder die Anfrage wird abgelehnt.

### Die fünf Analyse-Zustände

| Zustand | Bedeutung |
|---------|-----------|
| Nicht markiert | Für diesen Eintrag wurde keine Analyse angefordert. |
| Wartet auf Analyse | Markiert, aber noch von keinem Agenten übernommen — ohne Zusage, wann das geschieht. |
| Wird analysiert | Ein Agent hat den Eintrag übernommen und wertet ihn gerade aus. |
| Ergebnis vorhanden | Die Analyse ist abgeschlossen; das Ergebnis steht am Eintrag. |
| Analyse fehlgeschlagen | Der Agent hat einen Fehler gemeldet; du kannst die Markierung erneut setzen. |

---

## Was in die Analyse eingeht

Analysiert wird der **gesamte Eintrag**, nicht nur ein einzelnes Foto: Titel und Beschreibung, Eintragstyp und Tags, die erfassten Messwerte, alle angehängten Fotos sowie der Pflanzenkontext (Art, Sorte, aktuelle Phase, Standort, Pflanzdatum) — denn dieselbe Verfärbung ist an einem Sämling anders zu bewerten als an einer Pflanze in der Blüte.

!!! note "Nur verkleinerte Bildfassungen, nie das Original"
    An deinen Agenten und weiter an dein Sprachmodell gehen ausschließlich verkleinerte Bildfassungen ohne EXIF-Daten — niemals das Originalfoto und niemals Aufnahmeort oder Gerätekennung.

---

## Das Ergebnis lesen

Sobald eine Analyse abgeschlossen ist, zeigt der Eintrag:

1. Eine **Zusammenfassung** als Erstes.
2. Eine aufklappbare **Befundliste** — je Befund eine Bezeichnung, eine Konfidenz und eine Begründung. Die Konfidenz erscheint immer als Zahl **und** in Worten (z. B. „72 % — eher wahrscheinlich"), weil eine nackte Prozentzahl eine Genauigkeit vortäuscht, die ein Sprachmodell nicht hat.
3. **Empfohlene Maßnahmen** als Liste.
4. Eine **Herkunftsangabe**: verwendetes Modell, Rezeptversion, Zeitpunkt der Analyse und welche Fotos tatsächlich ausgewertet wurden.

!!! warning "Der Vorbehalt ist immer sichtbar"
    „Diese Einschätzung stammt von einem Sprachmodell, ist eine Hypothese und ersetzt keine fachliche Prüfung." — dieser Hinweis steht bei jedem Ergebnis, nicht versteckt hinter einem Aufklapp-Element. Ein Analyse-Ergebnis ist eine Einschätzung, keine Diagnose, und ersetzt keine eigene fachliche Prüfung.

---

## Erneut analysieren

Bei einem abgeschlossenen oder fehlgeschlagenen Eintrag kannst du **Erneut analysieren** wählen. Das setzt den Eintrag zurück auf „Wartet auf Analyse"; ein neues Ergebnis **überschreibt** das vorherige vollständig — eine Historie mehrerer Analysen gibt es aktuell nicht.

---

## Tagebuchfotos und Galerie-Fotos

Fotos an einem Tagebuch-Eintrag sind eine **eigene, getrennte Kategorie** — unabhängig von den Fotos der [Pflanzenfoto-Galerie](plant-photos.md). Ein Galerie-Foto zeigt den Wachstumsverlauf einer Pflanze über die Zeit; ein Tagebuchfoto gehört zu genau einem Eintrag und dessen Beobachtung. Beide Bereiche sind unabhängig voneinander nutzbar und teilen sich weder Fotos noch das 5-Fotos-Limit des Tagebuchs.

---

## Einwilligung verwalten oder widerrufen

Die Einwilligung „Einzelne Tagebuch-Einträge dürfen von meinem KI-Agenten analysiert werden" findest du im Tab **Einwilligungen** des Datenschutz-Bereichs (Profilbild oder Initialen oben rechts → **Datenschutz**) — siehe [Datenschutz (DSGVO) — Einwilligungen verwalten](privacy.md#einwilligungen-verwalten-art-7-dsgvo).

Ein Widerruf wirkt sofort: Du kannst danach keine neuen Einträge mehr markieren. Bereits vorliegende Analyse-Ergebnisse bleiben davon unberührt und weiterhin sichtbar.

---

## Light-Modus

Im [Light-Modus](light-mode.md) gibt es keine Benutzerkonten und damit auch keinen Einwilligungsmechanismus — die Einwilligung zur KI-Analyse gilt dort automatisch als erteilt. Ebenso entfällt die Einschränkung „nur eigene Einträge markieren": In einer Light-Instanz gehören ohnehin alle Einträge demselben System-Nutzer.

---

## Für technische Nutzer / Self-Hoster {#fuer-technische-nutzer-self-hoster}

Damit dein eigener Agent Einträge abholen, beanspruchen und Ergebnisse zurückschreiben kann, braucht er einen persönlichen API-Schlüssel (**Kontoeinstellungen → API-Schlüssel → Anlegen**) und Zugriff auf fünf dafür vorgesehene MCP-Werkzeuge. Der vollständige Werkzeug-Vertrag mit Fehlercodes und der Konfigurationsvariable für die maximale Bild-Nutzlast steht unter [MCP-Server — Tagebuch-Analyse](../api/mcp-server.md#tagebuch-analyse-externe-agenten).

---

## Modul ein- oder ausblenden

Das Tagebuch ist ein eigenes, abschaltbares Modul (`diary`, Kategorie „Pflege & Planung", standardmäßig ab der Erfahrungsstufe Einsteiger eingeblendet). Du kannst es wie jedes nicht-essenzielle Modul aus- oder wieder einblenden — siehe [Module & Funktionen](module-visibility.md).

---

## Häufige Fragen

??? question "Ich habe einen Eintrag markiert, aber es passiert nichts. Woran liegt das?"
    Das ist erwartetes Verhalten. Kamerplanter analysiert nicht selbst — dafür braucht es einen von dir betriebenen Agenten. Solange keiner läuft, bleibt der Eintrag im Zustand „Wartet auf Analyse" stehen. Sobald du deinen Agenten startest, holt er markierte Einträge selbstständig ab.

??? question "Wie lange dauert eine Analyse?"
    Dafür gibt es keine Zusage. Es hängt allein davon ab, wann dein eigener Agent läuft — nicht von Kamerplanter.

??? question "Kann ich Einträge anderer Mitglieder in einem Gemeinschaftsgarten markieren?"
    Nur mit der Rolle Leitung. Mit der Rolle Gärtner kannst du ausschließlich Einträge markieren, die du selbst verfasst hast.

??? question "Werden meine Originalfotos an ein Sprachmodell übertragen?"
    Nein. Es gehen ausschließlich verkleinerte Bildfassungen ohne EXIF-Daten hinaus — nie das Original, nie Aufnahmeort oder Gerätekennung.

??? question "Ist das Analyse-Ergebnis eine verlässliche Diagnose?"
    Nein. Es ist eine Hypothese eines Sprachmodells und ersetzt keine fachliche Prüfung. Dieser Vorbehalt steht bei jedem Ergebnis sichtbar dabei.

??? question "Was passiert mit einem vorhandenen Ergebnis, wenn ich die Einwilligung widerrufe?"
    Es bleibt erhalten und sichtbar. Der Widerruf verhindert nur, dass du künftig neue Einträge markierst.

??? question "Warum sehe ich in der Übersicht Einträge, die nicht von mir sind?"
    Die Tagebuch-Übersicht ist mandantenweit — in einem Gemeinschaftsgarten zeigt sie die Einträge aller Mitglieder. Das entspricht der generellen Sichtbarkeit innerhalb eines Gartens: Alle Mitglieder sehen dieselben Daten, unabhängig von ihrer Rolle (siehe [Rollen & Berechtigungen](../reference/roles-and-permissions.md)).

??? question "Kann ich eine laufende Analyse abbrechen?"
    Nein. Solange ein Agent den Eintrag bereits übernommen hat (Zustand „Wird analysiert"), lässt sich die Markierung nicht mehr zurücknehmen. Zurücknehmen geht nur, solange der Eintrag noch „Wartet auf Analyse" ist.

---

## Siehe auch

- [Pflanzenfoto-Galerie](plant-photos.md) — Wachstumsverlauf einer Pflanze in Fotos festhalten
- [Datenschutz (DSGVO)](privacy.md) — Einwilligungen, Aufbewahrung und deine Rechte
- [Module & Funktionen](module-visibility.md) — Funktionsbereiche gezielt ein- oder ausblenden
- [Rollen & Berechtigungen](../reference/roles-and-permissions.md) — wer in deinem Garten was darf
- [Pflanzdurchläufe](planting-runs.md) — Gruppenmanagement für Pflanzen
- [MCP-Server](../api/mcp-server.md) — technische Schnittstelle für einen eigenen Analyse-Agenten
