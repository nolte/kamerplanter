---
req_id: REQ-054
title: Automatische Anbauplanung (Bedarfserfassung, Beetbelegung je Saison, Teilplan, Erklärung, Annahme, Druckfassung)
category: Planung & Empfehlung
test_count: 28
coverage_areas:
  - Planung starten, Geltungsbereich, Profilwahl, Leerzustand
  - Bedarfserfassung (Menge, Rest auffüllen, Bestand, Vorjahr übernehmen)
  - Beete prüfen (Historie-Ampel, Bodengefahren, Nacherfassung)
  - Ergebnisansicht (Vorschlagsebene, Zu besprechen, Erklärsatz, Symbol-Breakdown, Warum nicht Beet X)
  - Teilplan und least-bad-Angebot
  - Fixierung, Warnungen an Beetkachel, Gewächshaus-Hinweis, Bodengefahr
  - Frostmodell, Bestand verteilt, Vor-/Nachkultur, Gründüngung, Dauerkultur, Rankhilfe, Historie-Lücke, Profile
  - Annehmen (je Beet, alle, Dialog, reserviert ohne Positionen, Ersetzen/behalten, veralteter Vorschlag, Schreibrechte)
  - Smartphone 390 × 844 (Liste, Warnung vor Annehmen, alle annehmen)
  - Druckfassung (PDF)
generated: "2026-10-04"
version: "1.2"
---

# Testfälle REQ-054: Automatische Anbauplanung

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-054 Automatische Anbauplanung v1.2**,
ausschließlich aus der Perspektive eines Nutzers im Browser. Keine Endpunkte, HTTP-Statuscodes,
Collection-Namen oder Datenbankabfragen erscheinen in den Testschritten. Alle Aussagen beschreiben,
was der Nutzer sieht, anklickt, antippt, eintippt und auf dem Bildschirm erwartet.
`data-testid`-Werte aus AP-UX-008 stehen in Klammern ausschließlich als Lokator-Hinweis.

Die UI-Sprache ist **Deutsch** (Standard-Locale). UI-Texte in Anführungszeichen sind Platzhalter
aus REQ-054 und werden bei der Umsetzung gegen die tatsächlichen i18n-Texte abgeglichen
(`pages.cropPlanning.*`, `enums.planningProfile.*`, `enums.unallocatedReason.*`,
`enums.soilHazard.*`). Profilnamen: „Ausgewogen", „Boden schonen", „Gesund halten",
„Viel Ernte", „Wenig Arbeit".

Jeder Testfall nennt das **Gerät**:

- **Desktop** — Viewport ≥ md (z. B. 1440 × 900): Bedarfserfassung, Gewichte, Drag, Breakdown
- **Smartphone 390 × 844** — Liste lesen, Warnung vor dem Annehmen, „alle annehmen"; Bedarfserfassung,
  Gewichte und Drag sind auf Mobil bewusst nicht verfügbar (AP-UX-007)

## Geltungsbereich

Abgedeckt sind die browser-beobachtbaren Akzeptanzkriterien **AP-ACC-008, 009, 011, 012, 013, 018
und 027** (E- und I-Kriterien mit sichtbarer Wirkung; die I-Kriterien sind auf ihre Wirkung in
der Oberfläche reduziert, der Datenvertrag wird in Integrationstests geprüft).

Zusätzlich haben die Unit-Kriterien **AP-ACC-001, 003, 004, 005, 007, 016, 017, 019, 020, 022,
023, 025** ein **sichtbares Gegenstück** als eigenen E2E-Fall mit Seed-Daten (z. B. Warnung an der
Beetkachel, least-bad-Angebot in der Seitenleiste, Gründüngungs-Vorschlag gestrichelt auf dem Plan).
Das Unit-Kriterium selbst (Rechenwert, Breakdown-Zahl, Codes) bleibt in Unit-Tests; der E2E-Fall
prüft nur, was der Nutzer sieht. AP-ACC-002 ist über den Wiederholungslauf in TC-054-006 sichtbar
mit abgedeckt.

Abgeleitete Fälle ohne eigenes AP-ACC (jeweils als „abgeleitet aus §9.1" gekennzeichnet):
TC-054-001 (Planung starten, Schritt 1 / AP-UX-006), TC-054-002 (Geltungsbereich, Schritt 1 /
AP-FR-014), TC-054-003 (Bedarf erfassen, Schritt 2), TC-054-004 („Vorjahr übernehmen", Schritt 2),
TC-054-005 (Beete prüfen, Schritt 3), TC-054-012 (Gewächshaus-Fixierung, AP-UX-003),
TC-054-023 („Ersetzen oder behalten?", Schritt 7) und der Annahmedialog sowie das Muster
„reserviert, ohne Positionen" in TC-054-022 (Schritt 7).

**Nicht** abgedeckt sind die Kriterien AP-ACC-002 (nur als Nebenaspekt), 006, 010, 014, 015, 021,
024 und 026 — siehe „Nicht abgedeckte Akzeptanzkriterien" am Dokumentende.

## Hinweis zur Zustandsherstellung

Die Vorbedingungen sind nicht über die Oberfläche herstellbar und werden über **Seed-Daten**
(bzw. eine zweite Browser-Sitzung in TC-054-025) bereitgestellt. Testdaten-Mandant: Demo-Mandant mit
einer Outdoor-Site (Garten mit mindestens 6 Beeten), Rolle Leitung, sofern nicht anders genannt,
Saison 2026. Der **Seed-Satz „Planer"** umfasst:

| Beet | Zweck |
|------|-------|
| Beet 1 (4 m²) | Historie vollständig, Vorjahr 2025 Hülsenfrüchtler geerntet (Bohnen) |
| Beet 2 (4 m²) | Historie vollständig, Vorjahr 2025 Nachtschattengewächse (Tomaten), Kohl 2024 |
| Beet 3 (4 m²) | Historie fehlt (keine Einträge), Erdbeeren als Dauerkultur auf 2 m² |
| Beet 4 (4 m²) | Historie lückenhaft (nur 2024 und 2025, 2022/2023 ohne Eintrag) |
| Beet 5 (4 m²) | Bodengefahr „Kohlhernie" (bestätigt 2022), Historie vollständig |
| Beet 6 (4 m²) | Rankhilfe in 0,3 m Entfernung, Historie vollständig |
| Beet 7 (4 m²) | Gewächshausbeet, unbeheizt |
| Parzelle P1 / P2 | zwei Parzellen mit unterschiedlichen Schreibrechten (nur TC-054-025) |

Site-Frostdaten: letzter mittlerer Frost 20. April, Frost-Sicherheitsdatum („Eisheilige") 15. Mai.
Zum Grad der Historie-Vollständigkeit gilt: ein nie gestarteter, nur geplanter Run aus 2025 gilt
nicht als Anbau (nicht Teil dieser Fälle).

---

## 1. Planung starten und Bedarf erfassen

### TC-054-001: Planung starten — Leerzustand, Profile, Optionen

**Requirement**: abgeleitet aus §9.1 Schritt 1; AP-UX-006, AP-UX-008, AP-FR-014
**AP-ACC**: —
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed-Satz „Planer"; Nutzer eingeloggt (Rolle Leitung)
- Es existiert noch keine Planung für Saison 2026

**Testschritte**:
1. Nutzer öffnet den Gartenplan und klickt „Saison planen"
2. Nutzer liest den Leerzustand (`planning-request-page`)
3. Nutzer öffnet die Profilauswahl und liest die fünf Profile
4. Nutzer liest die Schalter „Vor-/Nachkultur und Gründüngung zulassen" und „geplante Beete einbeziehen"

**Erwartete Ergebnisse**:
- Der Leerzustand erklärt in zwei Sätzen, was der Planer braucht (Pflanzenliste, Beete mit Historie);
  Fachbegriffe haben eine Glossar-Erklärung
- Die Profile „Ausgewogen", „Boden schonen", „Gesund halten", „Viel Ernte" und „Wenig Arbeit" stehen
  mit je einem Erklärsatz zur Auswahl; „Ausgewogen" ist vorbelegt
- „Vor-/Nachkultur und Gründüngung zulassen" ist standardmäßig an, „geplante Beete einbeziehen" aus
- Die Rückblick-Jahre sind mit der größten Anbaupause der Bedarfe vorbelegt (leer: Standardwert 4)
- Es gibt kein Anfängerprofil

**Nachbedingungen**:
- Nichts ist angelegt; keine Runs, kein Vorschlag

**Tags**: [req-054, planung-starten, profil, leerzustand, desktop, abgeleitet-9-1]

---

### TC-054-002: Geltungsbereich wählen — Beete außerhalb werden nie beplant

**Requirement**: abgeleitet aus §9.1 Schritt 1; AP-FR-014
**AP-ACC**: —
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path / Berechtigung
**Preconditions**:
- Nutzer ist einer eigenen Parzelle (Beet 1 und Beet 2) zugewiesen; Beet 3–7 sind Gemeinschaftsbeete
- Seed-Satz „Planer" mit Bedarf 4 Pflanzen Tomate `must`

**Testschritte**:
1. Nutzer klickt „Saison planen" und öffnet die Auswahl des Geltungsbereichs (`planning-scope-select`)
2. Nutzer liest die Angebote und wählt „Meine Parzellen"
3. Nutzer fügt die Pflanze Tomate hinzu und klickt „Berechnen" (`planning-run-button`)
4. Nutzer sieht sich die Ergebnisansicht an

**Erwartete Ergebnisse**:
- Angeboten werden „Gemeinschaftsbeete", „Meine Parzellen" und „Ausgewählte Beete"
- Im Vorschlag werden nur Beet 1 und Beet 2 belegt; Beet 3–7 erscheinen nicht als Belegung
- Beete außerhalb des Bereichs sind auf dem Plan sichtbar, aber ohne Vorschlagsfarbe
- Gibt es für dieselbe Saison bereits angenommene Pflanzungen anderer Planungen in Beet 1 oder 2,
  nennt die Seitenleiste einen Hinweis zur Überschneidung

**Nachbedingungen**:
- Ein Vorschlag liegt als Dokument vor, nichts ist angenommen

**Tags**: [req-054, geltungsbereich, scope, desktop, abgeleitet-9-1]

---

### TC-054-003: Bedarf erfassen — Menge, „Rest auffüllen", Priorität, Bestand

**Requirement**: abgeleitet aus §9.1 Schritt 2; §5.1
**AP-ACC**: —
**Gerät**: Desktop
**Priority**: High
**Category**: Formular
**Preconditions**:
- Planung gestartet, Geltungsbereich gewählt
- Art Tomate hat einen Richtwert je Person, Art Zucchini nicht

**Testschritte**:
1. Nutzer fügt die Pflanze Tomate hinzu (`planning-demand-row-<key>`), Menge 6, Einheit „Stück",
   Priorität „Muss"
2. Nutzer fügt Zucchini hinzu und prüft, ob eine Mengenhilfe angeboten wird
3. Nutzer fügt Salat hinzu, wählt die Mengeneinheit „Rest auffüllen" und lässt die Obergrenze leer
4. Nutzer trägt bei Salat eine Obergrenze von 3 m² ein
5. Nutzer markiert bei Tomate „vorgezogen/gekauft, verfügbar ab" und wählt den 10. Mai
6. Nutzer aktiviert „am gleichen Platz wie letztes Jahr" bei Zucchini

**Erwartete Ergebnisse**:
- Bei Tomate erscheint ein „Richtwert je Person", der nur die Menge vorbelegt; bei Zucchini ist die
  Mengenhilfe ausgeblendet
- „Rest auffüllen" ohne Obergrenze ist nicht übernehmbar; ein Hinweis verlangt die Obergrenze
- Nach Eingabe der Obergrenze ist die Zeile gültig; der Hinweistext erklärt „nimmt, was nach den
  anderen Pflanzen übrig bleibt"
- Bei Tomate steht „verfügbar ab 10. Mai" sichtbar in der Zeile
- Alle Zeilen bleiben in der Liste erhalten

**Nachbedingungen**:
- Eine Bedarfsliste mit drei Zeilen; nichts berechnet

**Tags**: [req-054, bedarf, rest-auffuellen, bestand, desktop, abgeleitet-9-1]

---

### TC-054-004: „Vorjahr übernehmen" — tatsächliche Pflanzungen, Dauerkulturen übersprungen

**Requirement**: abgeleitet aus §9.1 Schritt 2 (F-17); Gegenstück zu AP-ACC-016
**AP-ACC**: AP-ACC-016 (sichtbarer Teil: Hinweis „nicht übernommen")
**Gerät**: Desktop
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Seed-Satz „Planer": 2025 wurden Tomaten (Beet 2) und Bohnen (Beet 1) gepflanzt; Beet 3 trägt
  Erdbeeren als Dauerkultur (seit 2024)
- Für 2025 existiert außerdem ein nie gestarteter Plan-Run mit Kohl

**Testschritte**:
1. Nutzer öffnet die Bedarfserfassung und klickt „Vorjahr übernehmen"
2. Nutzer liest die zwei angebotenen Quellen und wählt „Was tatsächlich gepflanzt wurde"
3. Nutzer liest die übernommene Liste und den Hinweis
4. Nutzer wiederholt die Aktion mit der Quelle „Plan des Vorjahres"

**Erwartete Ergebnisse**:
- Angeboten werden „Was tatsächlich gepflanzt wurde" (Standard) und „Plan des Vorjahres"
- Mit der ersten Quelle erscheinen Tomate und Bohne, nicht der nie gestartete Kohl
- Ein Hinweis lautet sinngemäß „1 Dauerkultur nicht übernommen"; Erdbeere steht nicht in der Liste
- Mit der Quelle „Plan des Vorjahres" erscheint auch der geplante Kohl

**Nachbedingungen**:
- Bedarfsliste entspricht der gewählten Quelle; keine Pflanzungen angelegt

**Tags**: [req-054, vorjahr-uebernehmen, dauerkultur, desktop, abgeleitet-9-1, ap-acc-016]

---

### TC-054-005: Beete prüfen — Historie-Ampel, Bodengefahr, Wasserzugang, Nacherfassung

**Requirement**: abgeleitet aus §9.1 Schritt 3; §5.3, §5.4; Gegenstück zu AP-ACC-001 (Hinweis „Historie fehlt")
**AP-ACC**: AP-ACC-001 (sichtbarer Teil)
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed-Satz „Planer", Geltungsbereich alle Beete, Bedarf Tomate 6 Stück `must`

**Testschritte**:
1. Nutzer geht im Planungsablauf zum Schritt „Beete prüfen"
2. Nutzer liest die Zeilen für Beet 1, Beet 3, Beet 4 und Beet 5
3. Nutzer klickt „Vorjahre nacherfassen" bei Beet 3

**Erwartete Ergebnisse**:
- Beet 1 zeigt die Historie-Ampel „vollständig", Beet 4 „lückenhaft", Beet 3 „fehlt"
- Beet 5 zeigt die Bodengefahr „Kohlhernie" mit Text
- Je Zeile sind Wasserzugang und Rankhilfe sichtbar
- Der Link „Vorjahre nacherfassen" führt zur Nacherfassung des Beets
- Ein Hinweis nennt „n von m Beeten ohne oder mit lückenhafter Historie — Vorjahre nacherfassen
  verbessert den Plan"

**Nachbedingungen**:
- Keine Änderung an den Beeten

**Tags**: [req-054, beete-pruefen, historie, ampel, desktop, abgeleitet-9-1, ap-acc-001]

---

## 2. Ergebnisansicht, Erklärung und Bearbeiten

### TC-054-006: Berechnen — Vorschlagsebene, Fruchtfolge-Wahl, „Zu besprechen", wiederholbar

**Requirement**: REQ-054 §9.1 Schritte 4–5; AP-UX-001, AP-UX-008; AP-FR-001
**AP-ACC**: AP-ACC-001 (sichtbares Gegenstück), AP-ACC-002 (Nebenaspekt)
**Gerät**: Desktop
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Seed-Satz „Planer" (nur Beet 1, 2, 3 im Geltungsbereich), Profil „Ausgewogen"
- Bedarf Tomate 6 Stück `must`

**Testschritte**:
1. Nutzer klickt „Berechnen" (`planning-run-button`)
2. Nutzer betrachtet die Ergebnisansicht (`planning-proposal-page`) und die Ebene „Vorschlag"
3. Nutzer klickt das Beet mit der Tomate an und liest den Satz
4. Nutzer liest die Seitenleiste „Zu besprechen" (`proposal-discuss-list`)
5. Nutzer startet die Planung mit unveränderter Eingabe erneut

**Erwartete Ergebnisse**:
- Die Gartenübersicht zeigt die Ebene „Vorschlag"; Beete sind in der Artfarbe je Fenster gefärbt
- Die Tomate liegt in Beet 1 (letztes Jahr Hülsenfrüchtler), nicht in Beet 2 (Nachtschatten 2025)
- Beet 3 trägt einen Hinweis, dass keine Historie vorliegt
- „Zu besprechen" listet die Beete mit Warnungen oder knappem Abstand zur Alternative und nennt den
  Hinweis zu Beeten ohne Historie
- Der erneut berechnete Vorschlag zeigt dieselbe Belegung wie der erste
- Der Hinweis „mit Wissensstand vom … berechnet" ist sichtbar

**Nachbedingungen**:
- Vorschläge liegen als Dokument vor; keine Pflanzungen angelegt

**Tags**: [req-054, ergebnis, vorschlag, fruchtfolge, desktop, ap-acc-001, ap-acc-002]

---

### TC-054-007: Erklärsatz, Symbol-Breakdown und „Details für Fortgeschrittene"

**Requirement**: REQ-054 §8.2 AP-FR-011, AP-FR-015; §9.2 AP-UX-002
**AP-ACC**: AP-ACC-011
**Gerät**: Desktop
**Priority**: Critical
**Category**: Erklärbarkeit
**Preconditions**:
- Vorschlag aus TC-054-006 liegt vor; UI-Stufe „Einsteiger"

**Testschritte**:
1. Nutzer klickt Beet 1 an
2. Nutzer liest den Erklärsatz
3. Nutzer liest die Kriterienliste darunter
4. Nutzer klickt „Details für Fortgeschrittene"

**Erwartete Ergebnisse**:
- Der Satz begründet die Wahl mit deutschen Familien- bzw. Trivialnamen (z. B. „Tomaten sind
  Starkzehrer und profitieren davon, dass hier letztes Jahr Bohnen standen …"), mit dem Warum
- Je Kriterium steht ein Symbol (gut/neutral/schlecht) **und** ein Kurztext, nicht nur Farbe
- Die Liste hat keine Spalte „Gewicht" und zeigt keine Zahlen
- Erst unter „Details für Fortgeschrittene" erscheinen Zahlen und Gewichte
- Eine Vorgabe des Nutzers (Fixierung, „gleicher Platz") erscheint als „Vorgabe", nicht als Pluspunkt
- Der Gesamtscore erscheint hier nicht

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, erklaerung, breakdown, symbole, desktop, ap-acc-011]

---

### TC-054-008: „Warum nicht Beet 2?" und Verschiebe-Vorschau mit Score-Differenz und Warnung

**Requirement**: REQ-054 §9.1 Schritte 5–6; AP-FR-004
**AP-ACC**: AP-ACC-011
**Gerät**: Desktop
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Vorschlag aus TC-054-006 (Tomate in Beet 1; Beet 2 hatte 2025 Nachtschatten)

**Testschritte**:
1. Nutzer klickt Beet 1 an und öffnet „Warum nicht Beet 2?"
2. Nutzer liest den Hauptunterschied
3. Nutzer wählt „Hierhin verschieben" für Beet 2 und beobachtet die Vorschau, ohne zu speichern
4. Nutzer verwirft die Verschiebung
5. Nutzer zieht die Belegung stattdessen per Drag auf Beet 2

**Erwartete Ergebnisse**:
- „Warum nicht Beet 2?" nennt als Hauptunterschied, dass die Anbaupause für Nachtschattengewächse
  nicht eingehalten ist
- Die Vorschau zeigt vor dem Speichern die Score-Differenz und eine Warnung zur verletzten Anbaupause
- Nach dem Verwerfen bleibt die Belegung in Beet 1
- Beim Drag auf Beet 2 prüft der Planer sofort, zeigt die Warnung und die Score-Differenz und
  markiert die Belegung als „Vorgabe" mit Warnsymbol an der Beetkachel

**Nachbedingungen**:
- Vorschlag enthält nach Schritt 5 eine Belegung mit Warnung in Beet 2

**Tags**: [req-054, warum-nicht, drag, vorschau, desktop, ap-acc-011]

---

## 3. Teilplan, Fixierung und Warnungen

### TC-054-009: Teilplan — unerfüllbarer Bedarf steht mit Grund und least-bad-Angebot daneben

**Requirement**: REQ-054 §8.3 AP-FR-016; AP-FR-012; AP-UX-001
**AP-ACC**: AP-ACC-012; Gegenstück zu AP-ACC-003
**Gerät**: Desktop
**Priority**: Critical
**Category**: Fehler / Teilplan
**Preconditions**:
- Seed-Satz „Planer" mit Geltungsbereich nur Beet 2, Beet 4 und Beet 5, in denen in den letzten 3 Jahren
  Kohlgewächse standen (Anbaupause 4 Jahre) bzw. Bodengefahr vorliegt
- Bedarf: Kohl `must`, zusätzlich Salat `want` und Möhre `want` (beide erfüllbar)

**Testschritte**:
1. Nutzer klickt „Berechnen"
2. Nutzer liest die Seitenleiste (`proposal-unallocated-list`)
3. Nutzer betrachtet die Plananzeige der übrigen Bedarfe

**Erwartete Ergebnisse**:
- Der Vorschlag trägt den Teilplan-Status (z. B. „Teilplan — 1 Bedarf nicht unterbringbar"), nicht
  „nicht lösbar"
- Salat und Möhre sind regulär belegt
- Kohl steht in der Seitenleiste mit dem Grund (z. B. „Kein Beet ohne Fruchtfolge-Konflikt") und mit
  bis zu drei Angeboten, z. B. „Trotzdem in Beet 2 (Anbaupause fehlt 1 Jahr)"
- Ein Hinweis nennt die Historie-Lücken mit Link „Vorjahre nacherfassen"
- Auf dem Plan ist keine Kohl-Belegung eingezeichnet

**Nachbedingungen**:
- Nichts angelegt; Vorschlag im Status Teilplan

**Tags**: [req-054, teilplan, unallocated, least-bad, desktop, ap-acc-012, ap-acc-003]

---

### TC-054-010: least-bad-Angebot annehmen — Neuberechnung mit Warnung, Rest bleibt

**Requirement**: REQ-054 §8.3 AP-FR-016; §9.1 Schritt 6
**AP-ACC**: AP-ACC-012; Gegenstück zu AP-ACC-004
**Gerät**: Desktop
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Teilplan aus TC-054-009

**Testschritte**:
1. Nutzer klickt in der Seitenleiste „Trotzdem in Beet 2 (Anbaupause fehlt 1 Jahr)"
2. Nutzer wartet, bis der Vorschlag neu berechnet ist
3. Nutzer klickt Beet 2 an

**Erwartete Ergebnisse**:
- Der Vorschlag wird neu berechnet; Salat und Möhre bleiben wie zuvor belegt
- Kohl liegt nun in Beet 2 und ist als „Vorgabe" gekennzeichnet; kein Pluspunkt dafür im Breakdown
- Die Belegung trägt eine Warnung zur fehlenden Anbaupause, ebenso die Beetkachel (Warnsymbol mit Text)
- „Zu besprechen" enthält Beet 2 und der Kohl steht nicht mehr unter „nicht unterbringbar"
- Nach dem Annehmen (siehe TC-054-022) wird die Begründung als Hinweis an der Pflanzung festgehalten

**Nachbedingungen**:
- Vorschlag enthält eine Fixierung mit Übersteuerung

**Tags**: [req-054, least-bad, fixierung, warnung, desktop, ap-acc-012, ap-acc-004]

---

### TC-054-011: Fixierung gegen Fruchtfolge — Warnung an Belegung und Beetkachel

**Requirement**: REQ-054 §5.1 `pinned_location_key`, §6 H-07; AP-UX-003
**AP-ACC**: Gegenstück zu AP-ACC-004
**Gerät**: Desktop
**Priority**: High
**Category**: Validierung
**Preconditions**:
- Seed-Satz „Planer": Beet 2 hatte 2024 Kohl; Bedarf Kohl `must`

**Testschritte**:
1. Nutzer fügt Kohl hinzu und fixiert ihn auf Beet 2
2. Nutzer klickt „Berechnen"
3. Nutzer betrachtet Beet 2 auf dem Plan und klickt es an

**Erwartete Ergebnisse**:
- Kohl liegt in Beet 2 (die Fixierung wird nicht abgelehnt)
- An der Beetkachel steht ein Warnsymbol mit Text zur Anbaupause
- Die Belegung zeigt dieselbe Warnung und das Kennzeichen „Vorgabe"
- Im Breakdown gibt es keinen positiven Beitrag für die Fixierung

**Nachbedingungen**:
- Vorschlag im Status „vorgeschlagen" mit Warnung

**Tags**: [req-054, fixierung, warnung, beetkachel, desktop, ap-acc-004]

---

### TC-054-012: Fixierung im Gewächshaus — Hinweis ohne roten Alarm

**Requirement**: abgeleitet aus AP-UX-003 (F-12), §9.1 Schritt 6
**AP-ACC**: —
**Gerät**: Desktop
**Priority**: Medium
**Category**: Validierung
**Preconditions**:
- Beet 7 ist ein Gewächshausbeet; Tomate stand 2025 dort, Bedarf Tomate fixiert auf Beet 7

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer klickt Beet 7 an und liest den Hinweis

**Erwartete Ergebnisse**:
- Tomate liegt in Beet 7
- Der Hinweis lautet sinngemäß „typisch für Gewächshäuser — Boden getauscht? Dann Fruchtfolge
  zurücksetzen" und ist nicht als roter Alarm gestaltet (Info-Hinweis)
- Ein Angebot, die Fruchtfolge des Beets zurückzusetzen, ist erreichbar

**Nachbedingungen**:
- Keine Änderung an Beet 7

**Tags**: [req-054, gewaechshaus, fixierung, hinweis, desktop, abgeleitet-ap-ux-003]

---

### TC-054-013: Beet mit Bodengefahr — Kohl ausgeschlossen, Fixierung warnt

**Requirement**: REQ-054 §6 H-10; §5.2 `soil_hazards`
**AP-ACC**: Gegenstück zu AP-ACC-022
**Gerät**: Desktop
**Priority**: High
**Category**: Validierung
**Preconditions**:
- Beet 5 hat die bestätigte Bodengefahr „Kohlhernie" (2022); Anbaupause für Kohl wäre eingehalten
- Bedarf Kohl `must`; Geltungsbereich Beet 1, Beet 5

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer öffnet „Warum nicht Beet 5?" bei der Kohl-Belegung
3. Nutzer fixiert Kohl auf Beet 5 und berechnet neu

**Erwartete Ergebnisse**:
- Kohl liegt nicht in Beet 5; „Warum nicht Beet 5?" nennt die Bodengefahr (Kohlhernie) als Grund,
  nicht die Anbaupause
- Nach der Fixierung liegt Kohl in Beet 5 mit Warnung „dauerhafter Bodenerreger" an Belegung und
  Beetkachel

**Nachbedingungen**:
- Vorschlag mit Warnung

**Tags**: [req-054, bodengefahr, kohlhernie, ausschluss, desktop, ap-acc-022]

---

## 4. Zeit, Bestand, Fenster, Gründüngung

### TC-054-014: Frostempfindliche Tomate — Start nach Frost-Sicherheitsdatum, im Gewächshaus früher

**Requirement**: REQ-054 §5.5 Nr. 2, 3; §6 H-05
**AP-ACC**: Gegenstück zu AP-ACC-017
**Gerät**: Desktop
**Priority**: High
**Category**: Zeitliche Machbarkeit
**Preconditions**:
- Site: mittlerer letzter Frost 20. April, Frost-Sicherheitsdatum 15. Mai; Beet 1 Freiland, Beet 7
  unbeheiztes Gewächshaus (Offset −21 Tage)
- Bedarf Tomate 4 Stück `must`

**Testschritte**:
1. Nutzer berechnet den Vorschlag mit fixierter Tomate auf Beet 1
2. Nutzer liest das Fenster der Belegung
3. Nutzer fixiert die Tomate auf Beet 7 und berechnet neu

**Erwartete Ergebnisse**:
- Im Freiland beginnt die Belegung am 15. Mai (Hinweis „Frost-Sicherheitsdatum"), nicht am 27. April
- Im Gewächshaus beginnt sie am 24. April
- Ein Hinweis nennt, dass Jungpflanzen Anzuchtplatz ab einem Datum brauchen und verweist auf den
  Aussaatkalender („Tomaten aussäen ab … — siehe Aussaatkalender")

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, frost, eisheilige, gewaechshaus, fenster, desktop, ap-acc-017]

---

### TC-054-015: Bestand „vorgezogen" — 20 Tomaten werden auf drei Beete verteilt

**Requirement**: REQ-054 §5.1 `supply = in_hand`; §7.2 `effort`
**AP-ACC**: Gegenstück zu AP-ACC-005
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed-Satz „Planer" mit Geltungsbereich Beet 1, 2, 6 (je 4 m², 7 Pflanzen je Beet)
- Bedarf Tomate 20 Stück `must`, vorgezogen, verfügbar ab 10. Mai

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer zählt die Pflanzen je Beet und liest die Fenster
3. Nutzer klickt eine der Belegungen an und liest den Aufwand-Eintrag im Breakdown

**Erwartete Ergebnisse**:
- Alle 20 Pflanzen sind untergebracht, verteilt auf drei Beete (7 + 7 + 6); keine wird gekürzt
- Jede Belegung beginnt frühestens am 15. Mai (Frost-Sicherheitsdatum), nicht am 10. Mai
- Der Breakdown zeigt für „Arbeitsaufwand" ein schlechtes Symbol mit Text „auf 3 Beete verteilt"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, bestand, in-hand, verteilen, desktop, ap-acc-005]

---

### TC-054-016: Vor- und Nachkultur im selben Beet — gleiche Familie nicht in derselben Saison

**Requirement**: REQ-054 §8.1 AP-FR-008; §6 H-01, H-03
**AP-ACC**: Gegenstück zu AP-ACC-019
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path / Validierung
**Preconditions**:
- Seed-Satz „Planer" mit nur einem Beet im Geltungsbereich (Beet 1); Schalter „Vor-/Nachkultur zulassen" an
- Lauf A: Bedarf Frühsalat und Buschbohne; Lauf B: Bedarf Kohlrabi und Blumenkohl

**Testschritte**:
1. Nutzer berechnet Lauf A und betrachtet die Zeitleiste des Beets (`proposal-allocation-<location_key>-pre`, `…-main`)
2. Nutzer berechnet Lauf B

**Erwartete Ergebnisse**:
- Lauf A: Beet 1 trägt Salat als Vorkultur bis 15. Juni und Buschbohne als Hauptkultur ab 22. Juni
  (Pause zwischen den Fenstern sichtbar)
- Lauf B: Kohlrabi und Blumenkohl liegen nicht im selben Beet; eine der beiden Kulturen steht in
  der Seitenleiste als nicht unterbringbar mit Grund „gleiche Familie in der Saison"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, vorkultur, nachkultur, fenster, desktop, ap-acc-019]

---

### TC-054-017: Freies Beet im Herbst — Gründüngung gestrichelt auf dem Plan

**Requirement**: REQ-054 §8.1 AP-FR-008; §7.2 `soil_cover`; §9.1 Schritt 5
**AP-ACC**: Gegenstück zu AP-ACC-020
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Beet 2 hatte Kohl; die Hauptkultur im Vorschlag endet dort am 10. September, kein weiterer Bedarf
- Schalter „Vor-/Nachkultur und Gründüngung zulassen" an

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer betrachtet Beet 2 auf dem Plan (`proposal-cover-<location_key>`) und klickt es an
3. Nutzer schaltet „Vor-/Nachkultur und Gründüngung zulassen" aus und berechnet erneut

**Erwartete Ergebnisse**:
- Beet 2 zeigt für den Herbst einen gestrichelten Gründüngungs-Vorschlag (oder Mulch)
- Die vorgeschlagene Art ist nicht Senf (kein Kreuzblütler nach Kohl); der Satz begründet die Wahl
- Das Kriterium „Bodenbedeckung" steht im Breakdown auf „gut"
- Mit ausgeschaltetem Schalter fehlt der Vorschlag; „Bodenbedeckung" steht auf „schlecht"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, gruendeuengung, cover, gestrichelt, desktop, ap-acc-020]

---

### TC-054-018: Dauerkultur blockiert ihre Fläche ganzjährig

**Requirement**: REQ-054 §5.2 Bestandskulturen (F-03); §6 H-02, H-04
**AP-ACC**: Gegenstück zu AP-ACC-016
**Gerät**: Desktop
**Priority**: Medium
**Category**: Validierung
**Preconditions**:
- Beet 3 (4 m²) trägt Erdbeeren auf 2 m² seit 2024; Geltungsbereich nur Beet 3
- Bedarf Salat 3 m² `must`

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer liest die Seitenleiste

**Erwartete Ergebnisse**:
- Es werden nur 2 m² von Beet 3 belegt; der fehlende Rest (1 m²) steht in der Seitenleiste mit
  Grund „Fläche fehlt" und dem Hinweis, wie viel fehlt
- Die Erdbeerfläche ist auf dem Plan als belegt gekennzeichnet

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, dauerkultur, flaeche, desktop, ap-acc-016]

---

### TC-054-019: Stangenbohne bevorzugt das Beet mit Rankhilfe

**Requirement**: REQ-054 §7.2 `site_fit` (Rankhilfe)
**AP-ACC**: Gegenstück zu AP-ACC-025
**Gerät**: Desktop
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Beet 6 hat eine Rankhilfe in 0,3 m Entfernung, Beet 1 nicht; beide gleich geeignet
- Bedarf Stangenbohne 8 Stück

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer klickt die Belegung an und öffnet „Warum nicht Beet 1?"

**Erwartete Ergebnisse**:
- Stangenbohne liegt in Beet 6
- „Warum nicht Beet 1?" nennt „keine Rankhilfe" als Hauptunterschied
- Wird die Bohne auf Beet 1 fixiert, erscheint die Warnung „Rankhilfe fehlt"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, rankhilfe, site-fit, desktop, ap-acc-025]

---

### TC-054-020: Lückenhafte Historie — Warnung „nicht prüfbar", kein Bonus

**Requirement**: REQ-054 §5.4; §6 H-01
**AP-ACC**: Gegenstück zu AP-ACC-023
**Gerät**: Desktop
**Priority**: High
**Category**: Validierung
**Preconditions**:
- Beet 4: Historie nur 2024 und 2025; Bedarf Tomate (Pause 4 Jahre), Geltungsbereich nur Beet 4

**Testschritte**:
1. Nutzer berechnet den Vorschlag
2. Nutzer klickt Beet 4 an und liest die Warnung und den Satz

**Erwartete Ergebnisse**:
- Die Belegung trägt eine Warnung „Historie lückenhaft — Anbaupause nicht prüfbar" (Beetkachel und Belegung)
- Der Satz behauptet nicht, die Pause sei eingehalten
- Kein Bonus für lange Anbaupause im Breakdown
- „Zu besprechen" enthält Beet 4 mit Link „Vorjahre nacherfassen"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, historie-luecke, warnung, desktop, ap-acc-023]

---

### TC-054-021: Profil „Boden schonen" legt den Starkzehrer auf das besser versorgte Beet

**Requirement**: REQ-054 §7.3 Profile; §7.2 `nutrition`
**AP-ACC**: Gegenstück zu AP-ACC-007
**Gerät**: Desktop
**Priority**: Medium
**Category**: Profil
**Preconditions**:
- Zwei Beete im Geltungsbereich: Beet A mit niedriger Phosphor-Versorgung (Klasse A, ohne Düngung),
  Beet B mit ausreichender Versorgung (Klasse C); Bedarf Tomate (Starkzehrer)

**Testschritte**:
1. Nutzer berechnet mit „Boden schonen" und merkt sich das Beet der Tomate
2. Nutzer berechnet mit „Ausgewogen" und vergleicht
3. Nutzer klickt unter „Boden schonen" Beet B an und liest den Satz zur Nährstoffversorgung

**Erwartete Ergebnisse**:
- Unter „Boden schonen" liegt die Tomate auf Beet B (ausreichende Versorgung)
- Das gewählte Profil steht sichtbar am Vorschlag
- Der Satz nennt die Versorgung als Grund, ohne bei Überversorgung einen Vorteil zu behaupten

**Nachbedingungen**:
- Zwei Vorschläge für dieselbe Saison als Dokumente

**Tags**: [req-054, profil, boden-schonen, naehrstoffe, desktop, ap-acc-007]

---

## 5. Annehmen

### TC-054-022: Annehmen je Beet — Bestätigungsdialog, „reserviert, ohne Positionen", Rücknahme

**Requirement**: REQ-054 §9.1 Schritt 7; AP-UX-004; AP-API-Annahme
**AP-ACC**: AP-ACC-008 (sichtbare Wirkung); Dialogtext abgeleitet aus §9.1 Schritt 7
**Gerät**: Desktop
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Vorschlag mit 4 Belegungen und 1 Gründüngungs-Vorschlag, keine Warnungen

**Testschritte**:
1. Nutzer klickt bei Beet 3 „Annehmen" (`proposal-accept-button`)
2. Nutzer liest den Bestätigungsdialog und bestätigt
3. Nutzer betrachtet Beet 3 auf dem Plan
4. Nutzer klickt „alle annehmen" und bestätigt; dann erneut „alle annehmen"
5. Nutzer nimmt die Annahme eines Beets zurück

**Erwartete Ergebnisse**:
- Der Dialog lautet sinngemäß „Beet 3 wird für Tomaten reserviert (3,8 m², 10. Mai – 15. Okt.). Die
  Reihen legst du beim Bepflanzen fest."
- Nach Bestätigung zeigt Beet 3 das Muster „reserviert, ohne Positionen" (nicht „bepflanzt")
- Nach „alle annehmen" sind alle 4 Belegungen und die Gründüngung als geplant übernommen; der
  Vorschlag steht auf „angenommen"
- Das wiederholte „alle annehmen" erzeugt keine doppelten Einträge
- Jedes Beet erscheint in der Beetansicht mit Reservierung; in der Fruchtfolge des Beets steht der neue Eintrag
- Eine Annahme lässt sich, solange nicht begonnen, zurücknehmen; der Vorschlag bleibt als Dokument

**Nachbedingungen**:
- Geplante Pflanzungen mit reservierter Fläche und Zeitraum

**Tags**: [req-054, annehmen, dialog, reserviert, desktop, ap-acc-008, abgeleitet-9-1]

---

### TC-054-023: Bereits angenommene Pflanzungen derselben Saison — „Ersetzen oder behalten?"

**Requirement**: abgeleitet aus §9.1 Schritt 7 (F-17)
**AP-ACC**: —
**Gerät**: Desktop
**Priority**: Medium
**Category**: Konflikt
**Preconditions**:
- Für Saison 2026 existieren angenommene Pflanzungen aus Vorschlag 1 auf Beet 1 und Beet 2
- Vorschlag 2 derselben Saison liegt vor und belegt ebenfalls Beet 1

**Testschritte**:
1. Nutzer klickt bei Vorschlag 2 „Annehmen" für Beet 1
2. Nutzer liest die Rückfrage
3. Nutzer wählt „Behalten"
4. Nutzer wiederholt die Annahme und wählt „Ersetzen"

**Erwartete Ergebnisse**:
- Die Rückfrage „Ersetzen oder behalten?" erscheint
- Bei „Behalten" bleiben die bisherigen Reservierungen unverändert
- Bei „Ersetzen" gehen die neuen Reservierungen an die Stelle der alten; Beet 2 bleibt unberührt

**Nachbedingungen**:
- Je nach Wahl bleibt die alte oder gilt die neue Reservierung

**Tags**: [req-054, annahme, ersetzen, konflikt, desktop, abgeleitet-9-1]

---

### TC-054-024: Veralteter Vorschlag — Beet inzwischen anderweitig reserviert

**Requirement**: REQ-054 §6 H-04; AP-API Annahme
**AP-ACC**: AP-ACC-009 (sichtbare Wirkung)
**Gerät**: Desktop (zwei Browser-Sitzungen)
**Priority**: High
**Category**: Konflikt
**Preconditions**:
- Sitzung 1 hat einen Vorschlag mit Belegung in Beet 1 offen
- Sitzung 2 (andere Planung) hat danach eine Reservierung in Beet 1 **angenommen**

**Testschritte**:
1. In Sitzung 1: Nutzer klickt bei Beet 1 „Annehmen"
2. Nutzer liest die Meldung
3. Wiederholung: Vorschlag, bei dem in Sitzung 2 lediglich ein **nicht angenommener** Vorschlag auf Beet 1 liegt

**Erwartete Ergebnisse**:
- Schritt 1: Eine Meldung wie „Der Vorschlag ist veraltet — Beet 1 hat sich geändert" erscheint;
  Beet 1 wird nicht reserviert; das Angebot, neu zu berechnen, ist da
- Schritt 3: Die Annahme gelingt ohne Meldung (ein unangenommener Vorschlag blockiert nicht)

**Nachbedingungen**:
- Im Fall 1 keine neue Reservierung, im Fall 3 Beet 1 reserviert

**Tags**: [req-054, annahme, veraltet, konflikt, desktop, ap-acc-009]

---

### TC-054-025: Zwei Parzellen — Nutzer ohne Schreibrecht nimmt nur seine Beete an

**Requirement**: REQ-054 §9.1 Schritt 7; AP-FR-014; F-05
**AP-ACC**: AP-ACC-018
**Gerät**: Desktop (zwei Nutzer, zwei Browser-Sitzungen)
**Priority**: Critical
**Category**: Berechtigung
**Preconditions**:
- Nutzer A hat Schreibrecht nur an Parzelle P1; Nutzer B (Leitung) hat beide
- Vorschlag (von B erstellt) mit Belegungen in P1 und P2, Geltungsbereich beide

**Testschritte**:
1. Nutzer A öffnet den Vorschlag und klickt „alle annehmen"
2. Nutzer A liest den Dialog und die Meldung nach der Bestätigung
3. Nutzer B öffnet den Vorschlag und liest den Status der Beete

**Erwartete Ergebnisse**:
- P1 wird reserviert und zeigt „reserviert, ohne Positionen"
- Die Belegung in P2 bleibt „vorgeschlagen"; Nutzer A erhält einen Hinweis, dass für P2 kein
  Schreibrecht besteht
- Der Vorschlag steht auf „teilweise angenommen"
- Nutzer B sieht P1 reserviert und P2 weiter vorgeschlagen und kann P2 annehmen

**Nachbedingungen**:
- Nur P1 trägt Reservierungen

**Tags**: [req-054, annahme, schreibrechte, parzelle, desktop, zwei-nutzer, ap-acc-018]

---

## 6. Smartphone

### TC-054-026: Mobil — Belegung als Liste, Warnsymbol mit Text vor „Annehmen", Alternativen, Gewichte gesperrt

**Requirement**: REQ-054 §9.2 AP-UX-007
**AP-ACC**: AP-ACC-013
**Gerät**: Smartphone 390 × 844
**Priority**: Critical
**Category**: Mobil
**Preconditions**:
- Vorschlag mit einer Belegung mit Warnung (z. B. fixierter Kohl in Beet 2) und zwei Belegungen ohne Warnung
- Nutzer eingeloggt auf dem Smartphone

**Testschritte**:
1. Nutzer öffnet den Vorschlag
2. Nutzer liest die Liste von oben nach unten
3. Nutzer klappt bei einer Belegung die Alternativen auf
4. Nutzer sucht „Gewichte"

**Erwartete Ergebnisse**:
- Die Belegung ist eine Liste (Beet → Fenster → Art → Satz), keine Zeichenfläche
- Die Belegung mit Warnung zeigt ein Warnsymbol mit Text **über bzw. vor** der Schaltfläche „Annehmen"
- Alternativen sind aufklappbar
- „Gewichte" ist deaktiviert und erklärt, dass das nur am Desktop/Tablet geht
- Es gibt keine Bedarfserfassung und kein Drag

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-054, mobil, liste, warnung, smartphone, ap-acc-013]

---

### TC-054-027: Mobil — „alle annehmen" verlangt Bestätigung bei Warnung, Annehmen-Fläche ≥ 48 px

**Requirement**: REQ-054 §9.1 Schritt 7 (F-20); AP-UX-007
**AP-ACC**: AP-ACC-013
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Mobil
**Preconditions**:
- Vorschlag wie in TC-054-026 (1 Beet mit Warnung)

**Testschritte**:
1. Nutzer tippt bei einem Beet ohne Warnung auf „Annehmen"
2. Nutzer tippt auf „alle annehmen"
3. Nutzer liest die Bestätigung und bricht ab
4. Nutzer tippt erneut auf „alle annehmen" und bestätigt

**Erwartete Ergebnisse**:
- Die Schaltfläche „Annehmen" je Beet ist mindestens 48 px hoch und leicht zu treffen
- „alle annehmen" fragt „1 Beet mit Warnung" ab, bevor etwas reserviert wird
- Nach Abbruch bleibt alles „vorgeschlagen"
- Nach Bestätigung sind alle Beete reserviert

**Nachbedingungen**:
- Alle Beete reserviert

**Tags**: [req-054, mobil, alle-annehmen, bestaetigung, smartphone, ap-acc-013]

---

## 7. Druck

### TC-054-028: Druckfassung — „Zu besprechen" zuerst, ohne Scores und Nutzernamen

**Requirement**: REQ-054 §9.2 AP-UX-009
**AP-ACC**: AP-ACC-027
**Gerät**: Desktop
**Priority**: High
**Category**: Export
**Preconditions**:
- Vorschlag mit 2 Warnungen (Beete) und 1 nicht unterbringbaren Bedarf; Beetnamen und Nutzernamen im Mandanten vorhanden

**Testschritte**:
1. Nutzer klickt „Drucken" (`proposal-print-button`)
2. Nutzer öffnet die heruntergeladene PDF-Datei
3. Nutzer prüft Seitenformat, Reihenfolge und Inhalte

**Erwartete Ergebnisse**:
- Der Browser lädt ein PDF in A4 hochkant herunter
- Der Abschnitt „Zu besprechen" steht zuerst und hat 3 Einträge (2 Warnungen + 1 nicht unterbringbar)
- Danach folgen alle Beete mit Fenster, Art und Satz; Warnungen sind markiert
- Das PDF enthält keine Scores, keine Gewichte und keine Nutzernamen

**Nachbedingungen**:
- Datei heruntergeladen; Vorschlag unverändert

**Tags**: [req-054, druck, pdf, versammlung, desktop, ap-acc-027]

---

## Abdeckungs-Matrix

| AP-ACC | Kriterium (Kurzform) | Testfälle |
|--------|----------------------|-----------|
| AP-ACC-001 | Fruchtfolge: Tomate nach Bohnen, B3 ohne Historie (sichtbares Gegenstück) | TC-054-005, TC-054-006 |
| AP-ACC-002 | Determinismus (Nebenaspekt: Wiederholungslauf) | TC-054-006 |
| AP-ACC-003 | Teilplan Kohl (sichtbares Gegenstück) | TC-054-009 |
| AP-ACC-004 | Fixierung gegen Pause, Warnung, „Vorgabe" (sichtbares Gegenstück) | TC-054-010, TC-054-011 |
| AP-ACC-005 | 20 Pflanzen verteilt, ab Sicherheitsdatum (sichtbares Gegenstück) | TC-054-015 |
| AP-ACC-007 | „Boden schonen" vs. „Ausgewogen" (sichtbares Gegenstück) | TC-054-021 |
| AP-ACC-008 | Annehmen: Runs, Gründüngung, Wiederholung, „reserviert" | TC-054-022 |
| AP-ACC-009 | Veralteter Vorschlag | TC-054-024 |
| AP-ACC-011 | Satz, Symbol-Breakdown, Warum nicht, Verschiebe-Vorschau | TC-054-007, TC-054-008 |
| AP-ACC-012 | least-bad-Angebot in der Seitenleiste, Neuberechnung | TC-054-009, TC-054-010 |
| AP-ACC-013 | Mobil: Liste, Warnung vor Annehmen, „alle annehmen" | TC-054-026, TC-054-027 |
| AP-ACC-016 | Dauerkultur blockiert, „nicht übernommen" (sichtbares Gegenstück) | TC-054-004, TC-054-018 |
| AP-ACC-017 | Frost-Sicherheitsdatum, Gewächshaus (sichtbares Gegenstück) | TC-054-014 |
| AP-ACC-018 | Parzellen, Schreibrechte bei Annahme | TC-054-025 |
| AP-ACC-019 | Vor-/Nachkultur, gleiche Familie (sichtbares Gegenstück) | TC-054-016 |
| AP-ACC-020 | Gründüngung gestrichelt (sichtbares Gegenstück) | TC-054-017 |
| AP-ACC-022 | Bodengefahr (sichtbares Gegenstück) | TC-054-013 |
| AP-ACC-023 | Historie-Lücke (sichtbares Gegenstück) | TC-054-020 |
| AP-ACC-025 | Rankhilfe (sichtbares Gegenstück) | TC-054-019 |
| AP-ACC-027 | Druckfassung | TC-054-028 |
| (abgeleitet aus §9.1 Schritt 1) | Planung starten, Profile | TC-054-001 |
| (abgeleitet aus §9.1 Schritt 1, AP-FR-014) | Geltungsbereich | TC-054-002 |
| (abgeleitet aus §9.1 Schritt 2) | Bedarf erfassen | TC-054-003 |
| (abgeleitet aus §9.1 Schritt 2) | „Vorjahr übernehmen" | TC-054-004 |
| (abgeleitet aus §9.1 Schritt 3) | Beete prüfen | TC-054-005 |
| (abgeleitet aus AP-UX-003) | Gewächshaus-Fixierung | TC-054-012 |
| (abgeleitet aus §9.1 Schritt 7) | Annahmedialog, „reserviert, ohne Positionen", Ersetzen/behalten | TC-054-022, TC-054-023 |

## Nicht abgedeckte Akzeptanzkriterien

Diese Kriterien haben keinen eigenen browser-beobachtbaren Weg in diesem Zuschnitt und gehören
anderen Testebenen:

| AP-ACC | Kriterium (Kurzform) | Grund |
|--------|----------------------|-------|
| AP-ACC-002 | Determinismus, 20 Läufe byte-identisch | Unit-Test (nur Wiederholungslauf in TC-054-006 sichtbar) |
| AP-ACC-006 | Bohne/Zwiebel `severe`, Nachbarbeet 20/60 cm | Unit-Test der Regelentscheidung (Schwellen 30 cm); im Browser nur indirekt über Warnung/Grund |
| AP-ACC-010 | 150 Beete, 60 Bedarfe ≤ 60 s | Lastkriterium (I); Laufzeitmessung, kein Nutzer-Sichtprüfungsfall |
| AP-ACC-014 | Fremder Mandant / außerhalb Geltungsbereich abgelehnt | Sicherheits-/API-Vertrag (U) |
| AP-ACC-015 | Goldfälle (a)–(e) | Fixture-basierter Unit-Test, Scores nur mit Toleranz |
| AP-ACC-021 | Nur geplanter, nie gestarteter Run beeinflusst die Fruchtfolge nicht | Unit-Test; sichtbar nur als Nicht-Wirkung (indirekt in TC-054-004) |
| AP-ACC-024 | `timing` bei 10 vs. 20 Tagen Puffer | Unit-Test der Rechenregel |
| AP-ACC-026 | `rotation_future` lässt Beet für Kohl 2027 frei | Unit-Test der Planerentscheidung |

Die übrigen U-Kriterien (001, 003, 004, 005, 007, 016, 017, 019, 020, 022, 023, 025) bleiben
Unit-Tests; ihr sichtbares Gegenstück ist in der Abdeckungs-Matrix mit den E2E-Fällen verknüpft.

Nicht im MVP und daher nicht abgedeckt: Vergleich zweier Vorschläge (AP-UX-005), „Rest neu planen"
als eigene Funktion (AP-FR-007), Beetkommentare (AP-UX-010), H-11, KI-Prosa (AP-FR-013).

---

**Dokumenten-Ende**
