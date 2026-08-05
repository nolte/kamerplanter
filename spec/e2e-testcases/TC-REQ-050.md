---
req_id: REQ-050
title: KI-Analyse von Tagebuch-Einträgen (Nutzer markiert, externer Agent analysiert asynchron über MCP)
category: KI & Beratung
test_count: 27
coverage_areas:
  - Tagebuch-Tab an der Pflanzeninstanz (Anlegen, Bearbeiten, Löschen, Fotos, Markieren)
  - Mandantenweite Tagebuch-Übersicht (Spalten, fünf Analyse-Zustände, Hervorhebung completed)
  - Filter (nur mit Ergebnis, nur wartend) und Freitextsuche
  - Fremde Zeilen und Beobachter-Rechte (kein Markier-Schalter)
  - Markierung zurücknehmen (requested ja, in_progress nein)
  - Ergebnisdarstellung (Vorbehalt immer sichtbar, Konfidenz als Zahl und sprachliche Einordnung)
  - Zustand requested ohne Fortschrittsanzeige, Auffrischen-Schaltfläche
  - Modul-Abschaltbarkeit (REQ-042) und Navigationspunkt (REQ-021)
  - i18n DE/EN
generated: "2026-08-05"
version: "1.1"
---

# Testfälle REQ-050: KI-Analyse von Tagebuch-Einträgen

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-050 KI-Analyse von Tagebuch-Einträgen
v1.1**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine MCP-Werkzeugaufrufe,
JSON-RPC-Antworten, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle
Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale), sofern in einem Testfall nicht ausdrücklich
Englisch geprüft wird.

## Geltungsbereich

Abgedeckt sind die browser-beobachtbaren Akzeptanzkriterien AK-14, AK-15, AK-16, AK-17, AK-19,
AK-20, AK-27, AK-29, AK-30, AK-31 sowie AK-02 und AK-03 (Berechtigung und Rücknehmbarkeit der
Markierung, soweit über die Oberfläche beobachtbar). AK-01 ist in der Markier-Handlung aus AK-14
enthalten und wird dort mitgeprüft.

**Nicht** abgedeckt sind AK-04 bis AK-13 (der komplette MCP-Werkzeugvertrag —
`list_pending_diary_analyses`, `claim_diary_analysis`, `get_diary_entry`,
`get_diary_entry_photos`, `submit_diary_analysis` samt Lease-Fencing, Bild-Content-Auslieferung
und Nutzlast-Obergrenze), AK-18/AK-18a (das `GET .../diary`-Antwortschema und die serverseitige
`can_request_analysis`-Auswertung als Datenvertrag — ihre UI-Auswirkung ist indirekt über AK-15/16/17
und AK-19 mitgeprüft, aber das Schema selbst ist kein Browser-Artefakt), AK-21 bis AK-26
(Ergebnis-Überschreibung bei Wiederholungsanalyse, Werkzeug-Validierungsfehler,
Erasure-Anonymisierung, Datenauskunft-Inhalt, Light-Modus-Einwilligungsbefreiung,
Altdatenkompatibilität ohne Analyse-Felder) — siehe Abschnitt „Nicht abgedeckte
Akzeptanzkriterien" am Dokumentende für die Begründung je Kriterium.

## Hinweis zur Zustandsherstellung

Kamerplanter ruft selbst kein Sprachmodell auf (§3). Die Zustände `in_progress`, `completed` und
`failed` sind über die Oberfläche **nicht** erreichbar — sie entstehen ausschließlich, wenn ein
vom Nutzer betriebener externer Agent einen Eintrag über `claim_diary_analysis` beansprucht bzw.
über `submit_diary_analysis` ein Ergebnis zurückschreibt. Jeder Testfall, der einen dieser drei
Zustände als Vorbedingung braucht, hält deshalb ausdrücklich fest, **wie** der Zustand vor dem
eigentlichen Browser-Szenario herzustellen ist: über Seed-Daten (direktes Anlegen des Dokuments
mit den entsprechenden `analysis_*`-Feldern) oder über einen direkten, testseitig ausgeführten
Aufruf der betroffenen MCP-Werkzeuge außerhalb der Oberfläche. Nur `none` und `requested` sind
über reine Nutzerhandlung erreichbar (Markieren bzw. Entmarkieren).

---

## 1. Tagebuch-Tab an der Pflanzeninstanz

### TC-050-001: Tagebuch-Tab auf der Pflanzeninstanz-Detailseite sichtbar

**Requirement**: REQ-050 §2.5.1 — Erfassung an der Pflanzeninstanz, AK-14
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt (Rolle Gärtner oder Leitung)
- Mindestens eine Pflanzeninstanz existiert

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Pflanzeninstanz
2. Nutzer betrachtet die Tab-Leiste der Detailseite

**Erwartete Ergebnisse**:
- Ein Tab „Tagebuch" ist in der Tab-Leiste sichtbar, neben dem Foto-Galerie-Tab
- Beim Klick auf den Tab öffnet sich die Liste der Tagebuch-Einträge dieser einen Pflanze,
  chronologisch absteigend

**Nachbedingungen**:
- Tagebuch-Tab ist aktiv

**Tags**: [req-050, diary, tab, plant-instance, navigation, ak-14]

---

### TC-050-002: Neuen Tagebuch-Eintrag mit Foto anlegen

**Requirement**: REQ-050 §2.5.1, AK-14
**Priority**: Critical
**Category**: Formular
**Preconditions**:
- Tagebuch-Tab einer Pflanzeninstanz ist geöffnet
- Nutzer hat eine gültige Bilddatei verfügbar

**Testschritte**:
1. Nutzer klickt auf „Eintrag hinzufügen"
2. Nutzer wählt den Eintragstyp (z. B. „Problem")
3. Nutzer trägt Titel und Freitext ein
4. Nutzer ergänzt mindestens ein Tag und einen Messwert
5. Nutzer hängt über den Datei-Upload ein Foto an
6. Nutzer speichert den Eintrag

**Erwartete Ergebnisse**:
- Der neue Eintrag erscheint zuoberst in der chronologisch absteigenden Liste
- Typ, Titel, Freitext, Tag und Messwert sind am Eintrag sichtbar
- Das angehängte Foto ist als Vorschau am Eintrag sichtbar
- Der Analyse-Zustand des neuen Eintrags ist „nicht markiert"

**Nachbedingungen**:
- Ein zusätzlicher Tagebuch-Eintrag im Zustand `none` existiert an dieser Pflanze

**Tags**: [req-050, diary, formular, anlegen, foto, ak-14]

---

### TC-050-003: Sechstes Foto an einem Tagebuch-Eintrag wird abgelehnt

**Requirement**: REQ-050 §2.5.1 — „bis zu 5 Fotos", AK-14
**Priority**: Medium
**Category**: Validierung
**Preconditions**:
- Ein Tagebuch-Eintrag mit bereits 5 angehängten Fotos ist geöffnet (im Bearbeiten-Modus)

**Testschritte**:
1. Nutzer versucht, ein sechstes Foto an den Eintrag anzuhängen

**Erwartete Ergebnisse**:
- Der Upload-Bereich für weitere Fotos ist deaktiviert oder eine verständliche Meldung erscheint
  (z. B. „Maximal 5 Fotos je Eintrag")
- Es wird kein sechstes Foto übernommen

**Nachbedingungen**:
- Der Eintrag bleibt bei 5 Fotos

**Tags**: [req-050, diary, validation, photos, boundary, ak-14]

---

### TC-050-004: Tagebuch-Eintrag bearbeiten

**Requirement**: REQ-050 §2.5.1, AK-14
**Priority**: High
**Category**: Formular
**Preconditions**:
- Ein selbst verfasster Tagebuch-Eintrag existiert

**Testschritte**:
1. Nutzer öffnet die Bearbeiten-Aktion des Eintrags
2. Nutzer ändert den Titel und den Freitext
3. Nutzer speichert die Änderung

**Erwartete Ergebnisse**:
- Der Eintrag zeigt den geänderten Titel und Freitext
- Eine Bestätigungsmeldung erscheint

**Nachbedingungen**:
- Der Eintrag ist dauerhaft geändert

**Tags**: [req-050, diary, formular, bearbeiten, ak-14]

---

### TC-050-005: Tagebuch-Eintrag löschen

**Requirement**: REQ-050 §2.5.1, AK-14
**Priority**: Critical
**Category**: Formular
**Preconditions**:
- Ein selbst verfasster Tagebuch-Eintrag existiert

**Testschritte**:
1. Nutzer öffnet die Löschen-Aktion des Eintrags
2. Nutzer bestätigt die Sicherheitsabfrage

**Erwartete Ergebnisse**:
- Der Eintrag verschwindet aus der Liste des Tagebuch-Tabs
- Eine Bestätigungsmeldung erscheint

**Nachbedingungen**:
- Der Eintrag existiert nicht mehr an dieser Pflanze

**Tags**: [req-050, diary, formular, loeschen, ak-14]

---

### TC-050-006: Fotos im Eintrag als Vorschau mit Lightbox bei Klick

**Requirement**: REQ-050 §2.5.1 — „Fotos als Vorschau (512-px-Rendition), Lightbox bei Klick"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Ein Tagebuch-Eintrag mit mindestens 2 Fotos existiert

**Testschritte**:
1. Nutzer betrachtet den Eintrag im Tagebuch-Tab
2. Nutzer klickt auf eines der Foto-Vorschaubilder

**Erwartete Ergebnisse**:
- Die Fotos sind am Eintrag als Vorschaubilder sichtbar
- Ein Klick öffnet eine Lightbox mit dem Foto in größerer Ansicht
- Die Lightbox lässt sich schließen (X oder Klick außerhalb)

**Nachbedingungen**:
- Lightbox geschlossen, Tagebuch-Tab weiter sichtbar

**Tags**: [req-050, diary, lightbox, photos, ak-14]

---

### TC-050-007: Eintrag über den Schalter „Analysieren" zur Analyse markieren

**Requirement**: REQ-050 §2.1, §2.5.1, AK-14, AK-01
**Priority**: Critical
**Category**: Formular
**Preconditions**:
- Ein selbst verfasster Tagebuch-Eintrag im Zustand `none` existiert
- Nutzer hat Schreibrecht (Rolle Gärtner oder Leitung) und die Einwilligung `diary_ai_analysis`
  ist erteilt

**Testschritte**:
1. Nutzer öffnet den Tagebuch-Tab der Pflanze
2. Nutzer klickt am Eintrag auf den Schalter „Analysieren"

**Erwartete Ergebnisse**:
- Der Analyse-Zustand des Eintrags wechselt sichtbar auf „wartet auf Analyse"
- Der Schalter zeigt jetzt „Markierung zurücknehmen" an

**Nachbedingungen**:
- Der Eintrag befindet sich im Zustand `requested`

**Tags**: [req-050, diary, mark-for-analysis, ak-14, ak-01]

---

## 2. Mandantenweite Tagebuch-Übersicht — Struktur & Zustände

### TC-050-008: Übersicht listet Einträge aller Pflanzen chronologisch mit allen Spalten

**Requirement**: REQ-050 §2.5.2, AK-15
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Mindestens zwei Pflanzeninstanzen mit je mindestens einem Tagebuch-Eintrag existieren im
  angemeldeten Mandanten

**Testschritte**:
1. Nutzer navigiert zur Tagebuch-Übersicht (`/tagebuch`)

**Erwartete Ergebnisse**:
- Einträge **aller** Pflanzen des Mandanten erscheinen in einer gemeinsamen Liste, chronologisch
  absteigend nach Erfassungsdatum
- Jede Zeile zeigt Datum, Pflanze (verlinkt auf deren Detailseite), Art, Eintragstyp, Titel bzw.
  Auszug, Fotoanzahl mit Miniaturvorschau des ersten Fotos, und eine Analyse-Spalte

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, overview, listenansicht, ak-15]

---

### TC-050-009: Übersicht unterscheidet alle fünf Analyse-Zustände sichtbar voneinander

**Requirement**: REQ-050 §2.5.2 — Zustandstabelle, AK-16
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Fünf Tagebuch-Einträge desselben Mandanten mit je einem der fünf Analyse-Zustände existieren:
  - `none`: über die Oberfläche unmarkiert angelegt
  - `requested`: über die Oberfläche markiert (Schalter „Analysieren")
  - `in_progress`: **über Seed-Daten oder einen direkten Aufruf von `claim_diary_analysis`**
    hergestellt, da über die Oberfläche nicht erreichbar
  - `completed`: **über Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis`** mit
    `status: completed` hergestellt
  - `failed`: **über Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis`** mit
    `status: failed` hergestellt

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer betrachtet die Analyse-Spalte der fünf Zeilen

**Erwartete Ergebnisse**:
- Jeder der fünf Zustände zeigt eine optisch eindeutig unterscheidbare Darstellung (z. B. eigene
  Farbe/eigenes Icon je Zustand), keine zwei Zustände sehen gleich aus
- `none` zeigt einen neutralen Hinweis „nicht markiert"
- `requested` zeigt „wartet auf Analyse"
- `in_progress` zeigt „wird analysiert" mit dem Zeitpunkt des Beanspruchens
- `completed` zeigt einen deutlich hervorgehobenen „Ergebnis vorhanden"-Zustand
- `failed` zeigt einen Fehlerhinweis

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, overview, states, ak-16]

---

### TC-050-010: Zustand `completed` ist hervorgehoben und zeigt die Zusammenfassung als Vorschau

**Requirement**: REQ-050 §2.5.2 — „deutlich hervorgehoben, mit der Zusammenfassung als einzeilige
Vorschau", AK-16
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Ein Tagebuch-Eintrag im Zustand `completed` mit gesetzter Zusammenfassung existiert — **über
  Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis` hergestellt**

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer betrachtet die Zeile des `completed`-Eintrags

**Erwartete Ergebnisse**:
- Die Zeile ist visuell klar vom Normalzustand abgesetzt (z. B. Hervorhebung, „Ergebnis
  vorhanden"-Kennzeichnung)
- Die erste Zeile der Analyse-Zusammenfassung ist direkt in der Übersicht als einzeilige Vorschau
  lesbar, ohne dass der Eintrag geöffnet werden muss
- Die vollständige Befundliste und die Maßnahmen erscheinen **nicht** in der Übersichtszeile

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, overview, completed, ak-16]

---

### TC-050-011: Zustand `failed` zeigt Fehlerhinweis und Möglichkeit zur erneuten Markierung

**Requirement**: REQ-050 §2.5.2 — Zustandstabelle `failed`, AK-16
**Priority**: High
**Category**: Zustandsanzeige
**Preconditions**:
- Ein selbst verfasster Tagebuch-Eintrag im Zustand `failed` mit gesetztem Fehlertext existiert —
  **über Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis` mit
  `status: failed` hergestellt**

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer betrachtet die Zeile des `failed`-Eintrags

**Erwartete Ergebnisse**:
- Ein Fehlerhinweis mit der gemeldeten Ursache ist sichtbar
- Eine Möglichkeit, den Eintrag erneut zur Analyse zu markieren, ist an der Zeile vorhanden

**Nachbedingungen**:
- Kein Status geändert, bis der Nutzer die erneute Markierung auslöst

**Tags**: [req-050, diary, overview, failed, ak-16]

---

## 3. Filter und Freitextsuche

### TC-050-012: Filter „nur mit Ergebnis" zeigt ausschließlich `completed`-Einträge

**Requirement**: REQ-050 §2.5.2 — Filter „nach Analyse-Zustand … insbesondere „nur mit
Ergebnis"", AK-17
**Priority**: Critical
**Category**: Filter
**Preconditions**:
- Mandant hat Tagebuch-Einträge in mehreren Analyse-Zuständen, darunter mindestens einen
  `completed`-Eintrag (Zustandsherstellung wie in TC-050-009 beschrieben)

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer wählt den Filter „nur mit Ergebnis"

**Erwartete Ergebnisse**:
- Die Liste zeigt ausschließlich Einträge im Zustand `completed`
- Einträge in anderen Zuständen verschwinden aus der Liste

**Nachbedingungen**:
- Filter bleibt aktiv, bis er zurückgesetzt wird

**Tags**: [req-050, diary, filter, completed, ak-17]

---

### TC-050-013: Filter „nur wartend" zeigt ausschließlich `requested`-Einträge

**Requirement**: REQ-050 §2.5.2 — Filter „insbesondere … nur wartend", AK-17
**Priority**: Critical
**Category**: Filter
**Preconditions**:
- Mandant hat Tagebuch-Einträge in mehreren Analyse-Zuständen, darunter mindestens einen
  `requested`-Eintrag (über die Oberfläche markiert)

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer wählt den Filter „nur wartend"

**Erwartete Ergebnisse**:
- Die Liste zeigt ausschließlich Einträge im Zustand `requested`

**Nachbedingungen**:
- Filter bleibt aktiv, bis er zurückgesetzt wird

**Tags**: [req-050, diary, filter, requested, ak-17]

---

### TC-050-014: Freitextsuche über Titel und Text findet passende Einträge

**Requirement**: REQ-050 §2.5.2 — „Freitextsuche über Titel und Text", AK-17
**Priority**: High
**Category**: Suche
**Preconditions**:
- Ein Tagebuch-Eintrag mit einem eindeutigen Stichwort im Titel oder Freitext existiert (z. B.
  „Staunässe")

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer gibt das eindeutige Stichwort in das Suchfeld ein

**Erwartete Ergebnisse**:
- Nur Einträge, deren Titel oder Text das Stichwort enthält, bleiben in der Liste
- Einträge ohne Treffer verschwinden

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, search, ak-17]

---

## 4. Fremde Einträge, Beobachter und Rücknehmbarkeit

### TC-050-015: Fremde Zeile in der Übersicht zeigt den Zustand, aber keinen Markier-Schalter

**Requirement**: REQ-050 §2.5.2, §7.2, AK-19
**Priority**: Critical
**Category**: Berechtigung
**Preconditions**:
- Gemeinschaftsgarten-Mandant mit mindestens zwei Mitgliedern
- Nutzer hat Rolle Gärtner (nicht Leitung)
- Ein Tagebuch-Eintrag eines **anderen** Mitglieds im Zustand `none` existiert

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht
2. Nutzer betrachtet die Zeile des fremden Eintrags

**Erwartete Ergebnisse**:
- Die Zeile zeigt den Analyse-Zustand des fremden Eintrags normal an
- An dieser Zeile ist **kein** Schalter „Analysieren" bzw. keine Markier-Aktion bedienbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, overview, foreign-entry, permissions, ak-19]

---

### TC-050-016: Beobachter sieht Zustand und Ergebnis, kann aber weder im Tab noch in der
Übersicht markieren

**Requirement**: REQ-050 §6 — Berechtigungsmatrix, AK-02
**Priority**: Critical
**Category**: Berechtigung
**Preconditions**:
- Nutzer mit Rolle „Beobachter" im Mandanten
- Ein Tagebuch-Eintrag mit Analyse-Ergebnis (Zustand `completed`, Zustandsherstellung wie in
  TC-050-009) existiert an einer Pflanze dieses Mandanten

**Testschritte**:
1. Beobachter öffnet den Tagebuch-Tab der betreffenden Pflanze und betrachtet den Eintrag
2. Beobachter öffnet die mandantenweite Tagebuch-Übersicht und betrachtet dieselbe Zeile

**Erwartete Ergebnisse**:
- An beiden Orten sind Analyse-Zustand und -Ergebnis lesbar
- An beiden Orten ist **kein** Schalter „Analysieren" bzw. „Markierung zurücknehmen" bedienbar,
  weder am eigenen noch an fremden Einträgen

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, permissions, viewer, ak-02]

---

### TC-050-017: Markierung im Zustand `requested` ist über „Markierung zurücknehmen" rücknehmbar

**Requirement**: REQ-050 §2.2 — Übergang `requested → none`, AK-03
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Ein selbst verfasster Tagebuch-Eintrag im Zustand `requested` existiert (über die Oberfläche
  markiert, siehe TC-050-007)

**Testschritte**:
1. Nutzer öffnet den Tagebuch-Tab und betrachtet den markierten Eintrag
2. Nutzer klickt auf „Markierung zurücknehmen"

**Erwartete Ergebnisse**:
- Der Analyse-Zustand wechselt sichtbar zurück auf „nicht markiert"
- Der Schalter zeigt wieder „Analysieren" an

**Nachbedingungen**:
- Der Eintrag befindet sich wieder im Zustand `none`

**Tags**: [req-050, diary, unmark, ak-03]

---

### TC-050-018: Markierung im Zustand `in_progress` ist NICHT zurücknehmbar

**Requirement**: REQ-050 §2.2 — Übergang `requested → none` gilt „nur solange nicht
beansprucht", AK-03
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Ein selbst verfasster Tagebuch-Eintrag im Zustand `in_progress` existiert — **über Seed-Daten
  oder einen direkten Aufruf von `claim_diary_analysis` hergestellt**, da dieser Zustand über die
  Oberfläche nicht erreichbar ist

**Testschritte**:
1. Nutzer öffnet den Tagebuch-Tab bzw. die Tagebuch-Übersicht und betrachtet den
   `in_progress`-Eintrag

**Erwartete Ergebnisse**:
- Es ist **kein** „Markierung zurücknehmen"-Schalter an diesem Eintrag bedienbar — weder als
  aktiver Button noch als deaktivierter, anklickbar wirkender Button; die Rücknahme-Aktion ist
  vollständig abwesend oder eindeutig gesperrt dargestellt
- Der Zustand „wird analysiert" bleibt unverändert sichtbar

**Nachbedingungen**:
- Der Eintrag verbleibt im Zustand `in_progress`

**Tags**: [req-050, diary, unmark, in-progress, negative, ak-03]

---

## 5. Ergebnisdarstellung

### TC-050-019: Vorbehalt ist in der Ergebnisdarstellung immer sichtbar, nicht hinter einem
Aufklapp-Element versteckt

**Requirement**: REQ-050 §2.4, §2.5.3 — „Der Vorbehalt ist immer sichtbar, nicht aufklappbar
versteckt", AK-20
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Ein Tagebuch-Eintrag im Zustand `completed` mit gesetztem `disclaimer` existiert — **über
  Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis` hergestellt**

**Testschritte**:
1. Nutzer öffnet die Detailansicht des Eintrags (aus dem Tagebuch-Tab oder aus der Übersicht)
2. Nutzer betrachtet den Vorbehaltstext, **ohne** auf ein Element zu klicken oder etwas
   aufzuklappen
3. Nutzer klappt die Befundliste auf und wieder zu (sofern diese aufklappbar ist)
4. Nutzer prüft ausdrücklich, ob der Vorbehaltstext ein eigenes Aufklapp-Symbol
   (Chevron/„Mehr anzeigen") trägt

**Erwartete Ergebnisse**:
- Der Vorbehaltstext ist bereits beim Öffnen der Ansicht vollständig sichtbar, ohne jede
  Nutzerinteraktion
- Das Auf- und Zuklappen der Befundliste ändert die Sichtbarkeit des Vorbehalts **nicht**
- Der Vorbehaltstext trägt **kein** eigenes Aufklapp-Element — es gibt keinen Zustand, in dem der
  Vorbehalt eingeklappt oder verborgen ist

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, disclaimer, absence-check, ak-20]

---

### TC-050-020: Konfidenz eines Befunds wird als Zahl UND sprachlich eingeordnet dargestellt

**Requirement**: REQ-050 §2.5.3 — „Die Konfidenz wird als Zahl und sprachlich eingeordnet
dargestellt; eine nackte Prozentzahl allein erfüllt das Kriterium nicht", AK-30
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Ein Tagebuch-Eintrag im Zustand `completed` mit einem Befund der Konfidenz `0.72` existiert —
  **über Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis` hergestellt**

**Testschritte**:
1. Nutzer öffnet die Detailansicht des Eintrags
2. Nutzer klappt die Befundliste auf
3. Nutzer betrachtet die Konfidenzangabe des Befunds

**Erwartete Ergebnisse**:
- Die Konfidenz erscheint **als Zahl** (z. B. „72 %")
- Zusätzlich erscheint **eine sprachliche Einordnung** (z. B. „mittlere Sicherheit" /
  „wahrscheinlich") in unmittelbarer Nähe zur Zahl
- Eine Darstellung, die **nur** die Prozentzahl ohne begleitenden sprachlichen Begriff zeigt,
  erfüllt diesen Testfall **nicht**

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, confidence, ak-30]

---

### TC-050-021: Sprachliche Einordnung der Konfidenz unterscheidet niedrige und hohe Werte

**Requirement**: REQ-050 §2.5.3, AK-30
**Priority**: High
**Category**: Validierung
**Preconditions**:
- Zwei Tagebuch-Einträge im Zustand `completed` existieren: einer mit einem Befund der Konfidenz
  `0.15` (sehr niedrig), einer mit einem Befund der Konfidenz `0.95` (sehr hoch) — **jeweils über
  Seed-Daten oder einen direkten Aufruf von `submit_diary_analysis` hergestellt**

**Testschritte**:
1. Nutzer öffnet die Detailansicht des Eintrags mit der niedrigen Konfidenz und betrachtet die
   Befundliste
2. Nutzer öffnet die Detailansicht des Eintrags mit der hohen Konfidenz und betrachtet die
   Befundliste

**Erwartete Ergebnisse**:
- Beide Befunde zeigen sowohl die Zahl als auch eine sprachliche Einordnung
- Die sprachliche Einordnung unterscheidet sich erkennbar zwischen niedriger und hoher Konfidenz
  (z. B. „geringe Sicherheit" vs. „hohe Sicherheit") — sie ist nicht in beiden Fällen derselbe
  Text

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, confidence, boundary-value, ak-30]

---

## 6. Zustand „wartet auf Analyse" und Auffrischen

### TC-050-022: Zustand `requested` liest sich als „wartet auf Analyse" — ohne
Fortschrittsanzeige

**Requirement**: REQ-050 §2.5.2, §3, AK-27
**Priority**: Critical
**Category**: Zustandsanzeige
**Preconditions**:
- Ein Tagebuch-Eintrag im Zustand `requested` existiert (über die Oberfläche markiert)

**Testschritte**:
1. Nutzer öffnet die Tagebuch-Übersicht und betrachtet die Zeile des `requested`-Eintrags
2. Nutzer öffnet zusätzlich die Detailansicht dieses Eintrags
3. Nutzer prüft ausdrücklich, ob irgendwo ein Fortschrittsbalken, eine Prozentanzeige, ein
   Spinner mit Restzeit oder eine sonstige Fortschrittsdarstellung zum Analyse-Zustand erscheint

**Erwartete Ergebnisse**:
- Der Zustand wird als Text „wartet auf Analyse" (oder sinngleich) dargestellt
- An **keiner** der beiden Stellen erscheint ein Fortschrittsbalken, eine Prozentanzeige oder eine
  Restzeit-/ETA-Angabe zum Analysefortschritt — die Abwesenheit ist ausdrücklich Teil dieses
  Testfalls, nicht nur die Anwesenheit des Textes

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, requested, absence-check, ak-27]

---

### TC-050-023: Auffrischen-Schaltfläche lädt den Analyse-Zustand ohne Seiten-Reload nach

**Requirement**: REQ-050 §2.5.4, AK-29
**Priority**: High
**Category**: Formular
**Preconditions**:
- Ein Tagebuch-Eintrag im Zustand `requested` ist in der Übersicht geöffnet
- Während die Übersicht geöffnet bleibt, wird der Zustand des Eintrags testseitig über einen
  direkten Aufruf von `claim_diary_analysis` und anschließend `submit_diary_analysis` auf
  `completed` geändert, **ohne** dass der Nutzer die Seite neu lädt

**Testschritte**:
1. Nutzer betrachtet die Zeile des Eintrags — Zustand zeigt „wartet auf Analyse"
2. (Im Hintergrund wechselt der Zustand testseitig auf `completed`, wie in den Vorbedingungen
   beschrieben)
3. Nutzer klickt auf die Auffrischen-Schaltfläche der Übersicht

**Erwartete Ergebnisse**:
- Vor dem Klick zeigt die Zeile weiterhin „wartet auf Analyse" (kein automatischer Push)
- Nach dem Klick zeigt dieselbe Zeile den neuen Zustand „Ergebnis vorhanden" mit Vorschau, ohne
  dass der Browser die Seite neu lädt

**Nachbedingungen**:
- Übersicht zeigt den aktuellen Zustand

**Tags**: [req-050, diary, refresh, ak-29]

---

## 7. Modul-Sichtbarkeit

### TC-050-024: Modul „diary" ist standardmäßig aktiv und der Navigationspunkt „Tagebuch"
sichtbar

**Requirement**: REQ-050 §9 O-07, AK-31
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt, Modul `diary` ist nicht deaktiviert (Standard)
- Nutzer befindet sich mindestens auf UI-Erfahrungsstufe Einsteiger

**Testschritte**:
1. Nutzer betrachtet die Hauptnavigation

**Erwartete Ergebnisse**:
- Ein Navigationspunkt „Tagebuch" ist sichtbar und führt zur Route `/tagebuch`
- Der Navigationspunkt ist bereits für Nutzer auf Stufe Einsteiger sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, navigation, module-visibility, ak-31]

---

### TC-050-025: Modul „diary" abgeschaltet — Navigationspunkt „Tagebuch" verschwindet

**Requirement**: REQ-050 §9 O-07 — „`core: false`", AK-31
**Priority**: Critical
**Category**: Modul-Sichtbarkeit
**Preconditions**:
- Nutzer hat das Modul `diary` in den Modul-Sichtbarkeits-Einstellungen (REQ-042) deaktiviert

**Testschritte**:
1. Nutzer öffnet die Modul-Sichtbarkeits-Einstellungen und schaltet „Tagebuch" ab
2. Nutzer betrachtet danach die Hauptnavigation
3. Nutzer versucht, die Route `/tagebuch` direkt aufzurufen

**Erwartete Ergebnisse**:
- Der Navigationspunkt „Tagebuch" ist in der Hauptnavigation **nicht** mehr vorhanden
- Der direkte Aufruf der Route führt nicht auf eine funktionsfähige Tagebuch-Übersicht (Redirect
  oder entsprechender Hinweis, je nach sonstigem Modul-Sperrverhalten des Systems)

**Nachbedingungen**:
- Modul bleibt abgeschaltet, bis der Nutzer es erneut aktiviert

**Tags**: [req-050, diary, module-visibility, disabled, ak-31]

---

## 8. Internationalisierung

### TC-050-026: Tagebuch-Oberfläche in Deutsch (Standard)

**Requirement**: REQ-050 AK-28 — „DE ist Vorgabe und Rückfallsprache"
**Priority**: Medium
**Category**: i18n
**Preconditions**:
- Nutzer hat keine abweichende UI-Sprache eingestellt (Standard-Locale)

**Testschritte**:
1. Nutzer öffnet den Tagebuch-Tab einer Pflanzeninstanz
2. Nutzer öffnet die Tagebuch-Übersicht

**Erwartete Ergebnisse**:
- Alle Tagebuch-Texte (Tab-Titel, Buttons, Spaltenüberschriften, Zustandsbezeichnungen,
  Vorbehalt) erscheinen auf Deutsch
- Kein roher i18n-Schlüssel ist sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, i18n, german, ak-28]

---

### TC-050-027: Tagebuch-Oberfläche in Englisch

**Requirement**: REQ-050 AK-28 — „Alle Oberflächentexte liegen in DE und EN vor"
**Priority**: Medium
**Category**: i18n
**Preconditions**:
- Nutzer hat die UI-Sprache auf Englisch umgestellt

**Testschritte**:
1. Nutzer öffnet den Tagebuch-Tab einer Pflanzeninstanz
2. Nutzer öffnet die Tagebuch-Übersicht

**Erwartete Ergebnisse**:
- Alle Tagebuch-Texte (Tab-Titel, Buttons, Spaltenüberschriften, Zustandsbezeichnungen,
  Vorbehalt) erscheinen auf Englisch
- Kein roher i18n-Schlüssel ist sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-050, diary, i18n, english, ak-28]

---

## Abdeckungs-Matrix

| AK | Kriterium (Kurzform) | Testfälle |
|----|----------------------|-----------|
| AK-01 | Markieren ist ausdrückliche Nutzerhandlung | TC-050-007 (miterfasst) |
| AK-02 | Beobachter liest, markiert/beansprucht/schreibt nicht zurück | TC-050-016 |
| AK-03 | Markierung in `requested` rücknehmbar, in `in_progress` nicht | TC-050-017, TC-050-018 |
| AK-14 | Tagebuch-Tab: anlegen/bearbeiten/löschen/Fotos/markieren | TC-050-001 bis TC-050-007 |
| AK-15 | Mandantenweite Übersicht mit Spalten | TC-050-008 |
| AK-16 | Fünf Zustände sichtbar unterschieden, `completed` hervorgehoben | TC-050-009, TC-050-010, TC-050-011 |
| AK-17 | Filter (nur mit Ergebnis, nur wartend) und Freitextsuche | TC-050-012, TC-050-013, TC-050-014 |
| AK-19 | Fremde Zeile zeigt Zustand, keinen Schalter | TC-050-015 |
| AK-20 | Vorbehalt immer sichtbar, nicht aufklappbar versteckt | TC-050-019 |
| AK-27 | `requested` = „wartet auf Analyse", ohne Fortschrittsbalken | TC-050-022 |
| AK-28 | Oberflächentexte DE und EN | TC-050-026, TC-050-027 |
| AK-29 | Auffrischen-Schaltfläche, kein Server-Push | TC-050-023 |
| AK-30 | Konfidenz als Zahl UND sprachlich eingeordnet | TC-050-020, TC-050-021 |
| AK-31 | Modul `diary` abschaltbar, Navigationspunkt verschwindet | TC-050-024, TC-050-025 |

## Nicht abgedeckte Akzeptanzkriterien

Diese Kriterien haben keinen browser-beobachtbaren Weg in diesem Zuschnitt und gehören anderen
Testebenen (MCP-Werkzeug-/Backend-Tests):

| AK | Kriterium (Kurzform) | Grund |
|----|----------------------|-------|
| AK-04 | `list_pending_diary_analyses`-Vertrag (Sortierung, keine Bilder/Freitext) | reiner MCP-Werkzeugaufruf, kein UI-Element ruft dieses Werkzeug auf |
| AK-05 | `claim_diary_analysis` exklusiv, `conflict.already_claimed` | MCP-Werkzeugvertrag, agentenseitig |
| AK-06 | Lease-Ablauf macht Eintrag wieder beanspruchbar | MCP-Werkzeugvertrag; die *Folge* (Zustand wieder `requested`) ist über AK-16/AK-22 indirekt sichtbar, der Lease-Mechanismus selbst nicht |
| AK-07 | Bild-Content Base64/`image/webp` aus Renditions | MCP-Bild-Content, kein Browser-Artefakt |
| AK-08 | `payload.too_large` bei Obergrenze, keine stille Kürzung | MCP-Werkzeugvertrag |
| AK-09 | `thumbnail_pending` vs. `unavailable` | MCP-Werkzeugvertrag |
| AK-10 | `submit_diary_analysis` Lease-Validierung (`conflict.not_claimed`/`conflict.lease_expired`) | MCP-Werkzeugvertrag |
| AK-11 | Vorbehalt serverseitig gesetzt, auch ohne Agenten-Feld | Server-/Werkzeug-Verhalten; die *Sichtbarkeit* des gesetzten Vorbehalts ist über AK-20 (TC-050-019) geprüft, das serverseitige Erzwingen selbst nicht |
| AK-12 | Fremder Mandant/Eintrag liefert `not_found`, nie `permission.denied` | JSON-RPC-Fehlercode-Vertrag, kein UI-Zustand |
| AK-13 | Ohne Einwilligung `diary_ai_analysis` keine Markierung über MCP | MCP-Pfad; die Einwilligungsprüfung als UI-Vorbedingung ist implizit in TC-050-007 vorausgesetzt, nicht als eigener negativer MCP-Testfall geprüft |
| AK-18 | `GET .../diary`-Antwortschema (`DiaryOverviewResponse`) | API-Datenvertrag; UI-Auswirkung indirekt über TC-050-008/009/010 |
| AK-18a | `can_request_analysis` serverseitig ausgewertet | API-Feld; UI-Auswirkung indirekt über TC-050-015 (Schalter-Abwesenheit) |
| AK-21 | Wiederholungsanalyse überschreibt vorheriges Ergebnis vollständig | der Anstoß (erneut markieren) ist UI-sichtbar, der Vergleich zweier über MCP geschriebener Ergebnisse ist kein Browser-Vorgang |
| AK-22 | `submit_diary_analysis` weist ungültige Eingaben zurück | reine Werkzeug-Eingabevalidierung, kein Formular ruft dieses Werkzeug auf |
| AK-23 | Nutzerlöschung anonymisiert `created_by`/`analysis_requested_by`/`analysis_claimed_by` | Erasure-Verarbeitung (Celery), nicht in Echtzeit browser-auslösbar |
| AK-24 | Datenauskunft Art. 15 enthält Tagebuch-Eintrag samt Ergebnis | Export-Dateiinhalt, gehört zu REQ-025-Testfällen |
| AK-25 | Light-Modus: Markierung ohne Einwilligungsprüfung | laut Auftrag ausdrücklich nicht im Zuschnitt |
| AK-26 | Altdaten ohne Analyse-Felder bleiben lesbar, `analysis_state` gilt als `none` | Migrations-/Bestandsdatenverhalten; in der Oberfläche nicht von einem regulär im Zustand `none` angelegten Eintrag unterscheidbar |

---

**Dokumenten-Ende**
