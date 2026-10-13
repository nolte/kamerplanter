---
req_id: REQ-055
title: Plant Identity / Plant Social (Profil, Verlauf, Link teilen, Mastodon verknüpfen, Freigabe, Garten-Konto, Betrieb)
category: Pflanzen-Profil & Social
test_count: 45
coverage_areas:
  - Profil anlegen im Link-Pfad (Leerer Zustand, 3 Schritte, Vorschau, Link kopieren, Haushalts-Default, Anstoß)
  - Verlauf mit Herkunftssymbolen, Foto zum Profil, Wochenrückblick
  - Link teilen und aufrufen (Jeder mit dem Link, Link neu erzeugen, Profil verbergen, Messenger-Vorschau, Für alle im Netz auffindbar)
  - Aufrufzähler, Jahresrückblick, Vorher/Nachher
  - Adresse ändern, Archiv bei entfernter Pflanze, Profil löschen, Cannabis-Sperre
  - Mit Mastodon verknüpfen (Vorschaltseite, Zustimmung, Mock-Login, Bestätigen, Kennzeichnung als automatisch, ungültiger Server, Trennen)
  - Was soll {Name} erzählen (zwei Ebenen, Erst fragen, Gleich erzählen, Einmal pro Woche, Tageslimit, Veröffentlichungsfenster, Burst-Pause)
  - Wartet auf dein OK (Freigeben, Sammelaktionen, Ablauf, 10-Posts-Angebot, Smartphone)
  - Veröffentlicht (Fehlertexte, Nochmal senden, Post löschen)
  - Garten-Konto im Organisations-Mandanten (Governance Leitung, Austritt)
  - Betrieb (ohne Social-Feature, Kill-Switch, Light-Modus)
generated: "2026-10-04"
version: "1.3"
---

# Testfälle REQ-055: Plant Identity / Plant Social

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-055 Plant Identity / Plant Social v1.3**,
ausschließlich aus der Perspektive eines Menschen im Browser. Keine Endpunkte, HTTP-Statuscodes,
Collection-Namen oder Datenbankabfragen erscheinen in den Testschritten. Alle Aussagen beschreiben,
was die Person sieht, anklickt, antippt, eintippt und auf dem Bildschirm erwartet.
`data-testid`-Werte aus PS-UX-012 stehen in Klammern ausschließlich als Lokator-Hinweis.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Sichtbare Texte in Anführungszeichen folgen
REQ-055 §25.1 / Anhang M und den normativen Wortlauten in PS-UX-002, -003, -006, -007, -008. Wo der
Wortlaut nicht normativ ist, sind sie Platzhalter, die bei der Umsetzung gegen die tatsächlichen
i18n-Texte abgeglichen werden (`pages.plantIdentity.*`, `pages.plantTimeline.*`, `pages.social.*`,
`pages.publicProfile.*`, `enums.postStatus.*`, `enums.postStatusReason.*`). Rollen heißen
Beobachter, Gärtner, Leitung (REQ-049).

Jeder Testfall nennt das **Gerät**:

- **Desktop** — Viewport ≥ md (z. B. 1440 × 900)
- **Smartphone 390 × 844** — Freigabe-Karten, „Foto zum Profil", Link teilen

Mastodon läuft in allen Fällen als **Mock-Server `plants.test`** (PS-NFR-051). Die Fälle beschreiben,
was die Person dort sieht (Login-Seite des Mocks, „Zustimmen", der Beitrag in der Zeitleiste des Mocks),
nicht die Schnittstelle dahinter.

## Geltungsbereich

Abgedeckt sind die browser-beobachtbaren Akzeptanzkriterien **PS-ACC-070 bis 077 und 085**
(E2E-Block) vollständig. Zusätzlich haben folgende I-/G-Kriterien ein **sichtbares Gegenstück**
als eigenen E2E-Fall: PS-ACC-001, 004, 005, 006, 007, 009 (Profil anlegen, Adresse ändern,
Archiv, Löschen, Cannabis), 016 und 039 (Jeder mit dem Link mit/ohne Link; Profil verbergen),
020 bis 024 (Erst fragen, Gleich erzählen, Wochenrückblick, Tageslimit, Burst-Pause), 029
(Post löschen), 035 (OK zur Übertragung), 040 bis 044 und 052 (Verknüpfen, Bestätigen,
Kennzeichnung als automatisch, Trennen), 045 bis 047 (Fehlertexte), 055, 057, 059 (ohne
Social-Feature, Kill-Switch, Light-Modus), 065 (Gärtner im Organisations-Mandanten), 068
(Austritt: Konto pausiert), 078 (Begriffs-Guard als Sichtprüfung des Link-Pfads), 079 (Foto zum
Profil sofort sichtbar), 083 (Veröffentlichungsfenster: „geplant für 12:00"). Das Unit-/
Integrationskriterium selbst (Antwortcodes, Felder, Zeitberechnung) bleibt in den jeweiligen
Testebenen; der E2E-Fall prüft nur, was die Person sieht.

UX-Anforderungen mit eigenem Fall: PS-UX-005 (zweistufiger Editor), PS-UX-006 (Sammelaktionen,
10-Posts-Angebot, Ablauf-Hinweis), PS-UX-008 (Vorschaltseite, „Lieber nicht"-Ausstieg),
PS-UX-014 (Anstoß), PS-UX-016 (Aufrufzähler), PS-UX-017 (Jahresrückblick), PS-UX-018
(Vorher/Nachher), PS-UX-019 (Messenger-Vorschau).

Abgeleitete Fälle ohne eigenes PS-ACC sind mit „abgeleitet aus …" gekennzeichnet.

**Nicht** abgedeckt sind die Kriterien am Dokumentende („Nicht abgedeckte Akzeptanzkriterien").

## Hinweis zur Zustandsherstellung

Die Vorbedingungen sind nicht über die Oberfläche herstellbar (Bestand, Betreiber-Schalter, Mock-
Verhalten, zweite Sitzung) und werden über **Seed-Daten** bzw. Mock-Konfiguration bereitgestellt.
Der **Seed-Satz „Profil"**:

| Person / Mandant | Zweck |
|------------------|-------|
| Lena (UZG-001), persönlicher Mandant, Erfahrungsstufe Anfänger, Modul „Pflanzen-Posts" nicht sichtbar | Monstera „Mona" (Art *Monstera deliciosa*), 3 Fotos, 12× gegossen, erster Eintrag März 2024, kein Profil. Kein Mastodon. |
| Julia (ZG-003), persönlicher Mandant, Erfahrungsstufe Fortgeschritten, Modul „Pflanzen-Posts" sichtbar, Zustimmung zur Übertragung an Mastodon noch nicht erteilt, sofern nicht anders genannt | Monstera „Mona" mit Profil (Stufe „Nur ich und mein Haushalt"). Mock-Server `plants.test` in der Serverliste. |
| Max (ZG-001), persönlicher Mandant | Pflanze der Gattung Cannabis „Greta". Betreiber-Einstellung zu regulierten Arten: gesperrt (Standard). |
| Tom (Leitung) und Aisha (Gärtnerin), Organisations-Mandant „Gemeinschaftsgarten" (ZG-004) | Freigabe-Regel: Leitung prüft (`review_by = lead`); Pflanze „Rosi" (Rose). Garten-Konto auf dem Mock verknüpft. |
| Plattform-Betreiber | Zugang zum Betreiber-Bereich „Pflanzen-Posts". |

Der Mock `plants.test` ist so konfigurierbar, dass er (a) ein Konto mit dem Kennzeichen „automatisch"
oder ohne liefert, (b) Beiträge annimmt oder zeitweise „nicht erreichbar" ist, (c) die Verknüpfung
aufhebt. Die Uhrzeit des Tests ist für die Fälle zu Zeitfenstern einfrierbar (Seed-Zeit 09:13,
Zeitzone der Pflanze Europa/Berlin). Einmalige Hinweise (Foto-Hinweis, Anstoß, 10-Posts-Angebot)
sind je Fall frisch zu erzeugen.

---

## 1. Profil anlegen — der Link-Pfad (Lena)

### TC-055-001: Leerer Zustand „Gib Mona ein Profil" mit Beispielkarte und Bestand

**Requirement**: REQ-055 §25.3 PS-UX-002 (Schritt „Leerer Zustand"); PS-UX-001
**PS-ACC**: PS-ACC-070 (erster Teil)
**Gerät**: Desktop
**Priority**: P1
**Category**: Happy Path
**Preconditions**:
- Seed-Satz „Profil", Lena eingeloggt, Erfahrungsstufe Anfänger; Modul „Pflanzen-Posts" ist nicht sichtbar
- Mona hat noch kein Profil

**Testschritte**:
1. Lena öffnet die Detailseite ihrer Monstera „Mona"
2. Lena betrachtet die Tab-Leiste
3. Lena öffnet den Tab „Profil" (`identity-empty-state`)
4. Lena liest Titel, Nutzensatz, Beispielkarte und den Hinweis zum Bestand
5. Lena klickt den Nebenlink „Was sehen andere?"

**Erwartete Ergebnisse**:
- Die Tabs „Profil" und „Verlauf" sind sichtbar, obwohl das Modul „Pflanzen-Posts" nicht sichtbar ist; der Tab „Veröffentlicht" fehlt
- Der Titel lautet „Gib Mona ein Profil"; der Nutzensatz lautet „Zeig Freunden, wie Mona wächst — mit einer Seite, die du per Link teilen kannst. Du entscheidest, was drauf steht."
- Eine als Beispiel gekennzeichnete Karte zeigt Foto, Name, „Seit März 2024" und zwei Verlaufseinträge
- Der Hinweis lautet „Dein Verlauf ist schon da: 3 Fotos, 12× gegossen, seit März 2024"
- Der Button „Profil anlegen" (`identity-create`) ist sichtbar
- „Was sehen andere?" zeigt den Satz zu Name, Art, Sorte und dem, was nie gezeigt wird (Wohnort, Sensorwerte, Dünger, Notizen, Lenas Name)
- Auf der Seite steht keines der Wörter Mastodon, Provider, Policy, Timeline, Handle, Slug

**Nachbedingungen**:
- Es ist noch kein Profil angelegt

**Tags**: [req055, ps-acc-070, ps-acc-078, ps-ux-001, ps-ux-002, leerer-zustand, link-pfad, lena, desktop]

---

### TC-055-002: Profil in 3 Schritten — „Jeder mit dem Link", Vorschau mit eigenem Foto, Link kopieren

**Requirement**: REQ-055 §25.3 PS-UX-002, PS-UX-003, PS-UX-004; PS-PRI-013
**PS-ACC**: PS-ACC-070, PS-ACC-001 (sichtbarer Teil), PS-ACC-078 (Sichtprüfung)
**Gerät**: Desktop
**Priority**: P1
**Category**: Happy Path / User Journey
**Preconditions**:
- Wie TC-055-001; Browser erlaubt Lesen der Zwischenablage durch den Test

**Testschritte**:
1. Lena klickt „Profil anlegen" (`identity-create`)
2. Schritt 1 (`identity-step-1`): Lena liest den vorbelegten Namen „Mona" und den Beispielsatz „So klingt Mona"; sie wechselt den Umschalter zwischen „Ich-Ton" und „sachlich" (`identity-tone-friendly`, `identity-tone-minimalist`) und bestätigt den Namen
3. Schritt 2 (`identity-step-2`): Lena liest die zwei vorderen Stufen und wählt „Jeder mit dem Link" (`identity-visibility-unlisted`)
4. Lena liest den Foto-Hinweis und bestätigt ihn
5. Schritt 3 (`identity-step-3`): Lena betrachtet die Vorschau und klickt „Link kopieren" (`identity-copy-link`)
6. Lena fügt den Inhalt der Zwischenablage in die Adresszeile eines neuen Tabs ein

**Erwartete Ergebnisse**:
- Der Beispielsatz wechselt mit dem Umschalter zwischen Ich-Ton und sachlicher Fassung
- Vorne stehen „Nur ich und mein Haushalt" (vorgewählt) und „Jeder mit dem Link"; „Für alle im Netz auffindbar" ist nicht sichtbar, sondern erst unter „Mehr Optionen"
- Bei „Jeder mit dem Link" steht: „Wer den Link hat, kann das Profil sehen — auch wenn er ihn weitergibt. Dein Name und dein Wohnort stehen nicht drin." und „Das sehen andere: Name, Art, Sorte, ‚Seit {Jahr}', deine Beschreibung, Fotos und Meilensteine, die du zeigst. Das sehen sie nie: Wohnort, Sensorwerte, Dünger, Notizen, dein Name." sowie „Den Link finden Suchmaschinen nicht. Wer ihn hat, kann ihn aber weitergeben."
- Beim ersten Mal erscheint einmalig: „Auf deinen Fotos können Fenster, Straßenschilder oder Personen zu sehen sein. Schau kurz drüber." ohne Pflicht-Kästchen
- Die Vorschau zeigt Lenas eigenes Foto von Mona, vor dem Speichern
- Die Adresse ist nicht sichtbar (nur unter „Mehr")
- Nach „Link kopieren" erscheint eine Bestätigung; die Zwischenablage enthält einen Link der Form `…/p/mona-monstera~…`
- Im neuen Tab öffnet sich das Profil von Mona mit Name, Art und „Seit März 2024", ohne Wohnort
- Auf allen drei Schritten und im Teilen-Dialog erscheint keines der Wörter Mastodon, Provider, Policy, Timeline, Handle, Slug, Identität, unlisted, Allowlist, Admin, Mitglied, Nutzer

**Nachbedingungen**:
- Mona hat ein Profil der Stufe „Jeder mit dem Link"; der Tab „Profil" zeigt die Profil-Karte statt des leeren Zustands

**Tags**: [req055, ps-acc-070, ps-acc-001, ps-acc-078, ps-ux-002, ps-ux-003, ps-ux-004, link-pfad, lena, desktop]
**Related**: TC-055-001, TC-055-009

---

### TC-055-003: Haushalts-Default — „Speichern" statt Link

**Requirement**: REQ-055 §25.3 PS-UX-002 Schritt 3
**PS-ACC**: abgeleitet aus PS-UX-002 (Schritt 3, Haushalts-Default); PS-ACC-001 (Standardstufe)
**Gerät**: Desktop
**Priority**: P2
**Category**: Happy Path / Variante
**Preconditions**:
- Seed-Satz „Profil", Lena, Mona ohne Profil

**Testschritte**:
1. Lena startet „Profil anlegen" und bestätigt in Schritt 1 den Namen
2. In Schritt 2 lässt sie „Nur ich und mein Haushalt" ausgewählt
3. Lena liest in Schritt 3 den Button und klickt ihn

**Erwartete Ergebnisse**:
- Der Foto-Hinweis erscheint nicht (nur bei Stufen jenseits des Haushalts)
- Der Button in Schritt 3 heißt „Speichern" (`identity-publish`); es gibt keinen Button „Link kopieren" und keinen „Teilen"-Button
- Nach dem Speichern zeigt der Tab „Profil" die Profil-Karte mit der Stufe „Nur ich und mein Haushalt" und keinen Link

**Nachbedingungen**:
- Mona hat ein Profil, das nur Lena und ihr Haushalt sehen

**Tags**: [req055, ps-acc-001, ps-ux-002, haushalt, lena, desktop, abgeleitet]

---

### TC-055-004: Anstoß nach dem ersten Foto — einmalig und abweisbar

**Requirement**: REQ-055 §25.3 PS-UX-014
**PS-ACC**: abgeleitet aus PS-UX-014
**Gerät**: Smartphone 390 × 844
**Priority**: P3
**Category**: Hinweis / Einmaligkeit
**Preconditions**:
- Lena mit Pflanze „Mona" ohne Profil, noch keinen Anstoß abgewiesen; Anstoß-Funktion beim Betreiber eingeschaltet (Standard)

**Testschritte**:
1. Lena lädt ein erstes Foto für Mona hoch
2. Lena liest den eingeblendeten Hinweis und tippt „Nicht jetzt" (oder das Schließen-Symbol)
3. Lena lädt ein zweites Foto hoch

**Erwartete Ergebnisse**:
- Nach dem ersten Foto erscheint ein abweisbarer Hinweis mit Vorschaubild von Mona: „Gib Mona ein Profil und teil es mit Freunden."
- Nach dem Abweisen verschwindet er
- Nach dem zweiten Foto erscheint kein weiterer Anstoß
- Der Hinweis ist ohne horizontales Scrollen lesbar

**Nachbedingungen**:
- Kein Profil angelegt, Anstoß dauerhaft abgewiesen

**Tags**: [req055, ps-ux-014, anstoss, lena, smartphone, abgeleitet]

---

### TC-055-005: Sichtprüfung der Begriffe im Link-Pfad

**Requirement**: REQ-055 §25.1 / Anhang M; PS-UX-013, PS-UX-015
**PS-ACC**: PS-ACC-078 (Sichtprüfung)
**Gerät**: Desktop
**Priority**: P2
**Category**: Textprüfung
**Preconditions**:
- Seed-Satz „Profil", Lena, Mona ohne Profil, UI-Sprache Deutsch

**Testschritte**:
1. Lena öffnet den Tab „Profil" und liest den leeren Zustand
2. Lena durchläuft die Schritte 1 bis 3 (bis zur Stufe „Jeder mit dem Link")
3. Lena öffnet nach dem Speichern „Mehr", den Teilen-Dialog und den Satz „Wer darf das sehen?"
4. Lena öffnet das Profil über den Link in einem neuen Tab
5. Lena sucht auf allen Ansichten nach den verbotenen Wörtern

**Erwartete Ergebnisse**:
- Überschriften lauten „Profil", „Verlauf", „Wer darf das sehen?", „Adresse"
- Stufen heißen „Nur ich und mein Haushalt", „Jeder mit dem Link", „Für alle im Netz auffindbar"
- Nirgends erscheinen Mastodon, Provider, Policy, Timeline, Handle, Slug, Identität, unlisted, Allowlist, Admin, Mitglied, Nutzer
- Wo Rollen vorkommen, heißen sie Beobachter, Gärtner, Leitung

**Nachbedingungen**:
- Profil von Mona liegt vor (Stufe „Jeder mit dem Link")

**Tags**: [req055, ps-acc-078, begriffe, anhang-m, ps-ux-013, ps-ux-015, lena, desktop]

---

### TC-055-006: Verlauf zeigt bisherige Ereignisse mit Herkunftssymbolen

**Requirement**: REQ-055 §10, §25.4 PS-UX-009, PS-UX-010
**PS-ACC**: PS-ACC-070 (letzter Teil), PS-ACC-010 (sichtbarer Teil)
**Gerät**: Desktop
**Priority**: P2
**Category**: Anzeige
**Preconditions**:
- Seed-Satz „Profil", Lena, Mona hat 3 Fotos, 12× Gießen, einen Phasenwechsel (zeitbasiert); Profil von Mona angelegt

**Testschritte**:
1. Lena öffnet den Tab „Verlauf" auf Monas Detailseite
2. Lena liest die obersten Zeilen und fährt mit der Maus über ein Datum und ein Herkunftssymbol
3. Lena nutzt die Filterleiste (`timeline-filter-<type>`) und wählt „Gegossen"
4. Lena prüft die Wer-sieht-es-Symbole an den Zeilen

**Erwartete Ergebnisse**:
- Der Verlauf ist absteigend nach Datum sortiert (`timeline-item-<event_key>`)
- Jede Zeile hat Typ-Symbol, Text, ein relatives Datum („vor 3 Tagen") mit absolutem Tooltip, ein Herkunftssymbol und ein Wer-sieht-es-Symbol
- Gießen und Tagebucheinträge tragen das Symbol „Mensch", der Phasenwechsel das Symbol „Kamerplanter"; ein Tooltip nennt die Herkunft
- Der Filter zeigt nur Gießen-Zeilen
- Bestandsereignisse sind als „nicht gezeigt" gekennzeichnet; es gibt keine Zeile „wartet auf dein OK"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req055, ps-acc-070, ps-acc-010, ps-ux-009, ps-ux-010, verlauf, lena, desktop]

---

### TC-055-007: „Foto zum Profil" — ein Tippen, sofort sichtbar

**Requirement**: REQ-055 §26 PS-UX-031
**PS-ACC**: PS-ACC-085, PS-ACC-079 (erster Teil)
**Gerät**: Smartphone 390 × 844
**Priority**: P1
**Category**: Happy Path / Mobil
**Preconditions**:
- Lena, Mona mit Profil der Stufe „Jeder mit dem Link"; Profil-Link in zweitem Browser-Kontext offen; Kamera im Test durch Bilddatei ersetzt

**Testschritte**:
1. Lena öffnet Monas Detailseite und tippt „Foto zum Profil" (`photo-to-profile`)
2. Lena nimmt ein Foto auf
3. Lena betrachtet die Vorschau und tippt „Zeigen"
4. Lena lädt im zweiten Kontext das Profil neu

**Erwartete Ergebnisse**:
- Zwischen Auslösen und Ergebnis liegen höchstens drei Tippen
- Es erscheint weder ein Alt-Text-Pflicht-Dialog noch eine Freigabe-Karte
- Das Foto ist ohne weiteren Dialog auf dem Profil sichtbar; der Beschreibungstext des Bildes ist vorbelegt und nachträglich änderbar
- In Lenas Verlauf steht ein Eintrag „Foto" mit dem Symbol „Mensch"

**Nachbedingungen**:
- Foto im Verlauf und auf dem Profil

**Tags**: [req055, ps-acc-085, ps-acc-079, ps-ux-031, foto-zum-profil, lena, smartphone]
**Related**: TC-055-008

---

### TC-055-008: Gießen erscheint nicht sofort — Wochenrückblick

**Requirement**: REQ-055 §12.2, §25.4 PS-UX-005
**PS-ACC**: PS-ACC-079 (zweiter Teil), PS-ACC-022 (sichtbares Gegenstück)
**Gerät**: Desktop
**Priority**: P2
**Category**: Standardverhalten
**Preconditions**:
- Lena, Mona mit Profil „Jeder mit dem Link", Profil im zweiten Kontext offen; Standard-Regel für Gießen ist „Einmal pro Woche"

**Testschritte**:
1. Lena trägt in der Pflege ein Gießen für Mona ein
2. Lena lädt im zweiten Kontext das Profil neu
3. Der Test setzt die Uhr hinter das Ende der Woche (Sonntag 18:00) und lädt das Profil neu

**Erwartete Ergebnisse**:
- Das Gießen erscheint nicht sofort auf dem Profil
- Im Verlauf steht es als „nicht gezeigt"
- Nach Wochenende erscheint auf dem Profil ein einziger Wochenrückblick „Diese Woche wurde ich dreimal gegossen." (mit der tatsächlichen Anzahl); in einer Woche ohne Gießen erscheint kein Wochenrückblick

**Nachbedingungen**:
- Ein Wochenrückblick auf dem Profil

**Tags**: [req055, ps-acc-079, ps-acc-022, wochenrueckblick, lena, desktop]

---

## 2. Link teilen und aufrufen

### TC-055-009: Link öffnet das Profil — ohne Link „nicht gefunden"

**Requirement**: REQ-055 §17.1, §23.6; PS-UX-011
**PS-ACC**: PS-ACC-039, PS-ACC-016 (Link-Reichweite), PS-ACC-058 (sichtbarer Teil: gleiche Fehlerseite)
**Gerät**: Desktop
**Priority**: P1
**Category**: Berechtigung / Privatsphäre
**Preconditions**:
- Mona hat ein Profil der Stufe „Jeder mit dem Link" (Link aus TC-055-002); zweiter, nicht eingeloggter Browser-Kontext

**Testschritte**:
1. Im zweiten Kontext öffnet der Test den Link mit Zusatz am Ende (`…/p/mona-monstera~…`)
2. Der Test öffnet dieselbe Adresse ohne den Zusatz (`…/p/mona-monstera`)
3. Der Test öffnet eine nie vergebene Adresse (`…/p/gibt-es-nicht`)
4. Der Test vergleicht die Seiten aus Schritt 2 und 3

**Erwartete Ergebnisse**:
- Mit Link zeigt das Profil ohne Navigation der App Header, Avatar, Name, botanischen Namen kursiv, „Seit …", Verlauf mit Fotos und die Fußzeile „Problem melden" (`public-profile`, `public-report`)
- Ohne den Zusatz erscheint die Seite „nicht gefunden"
- Die Seiten aus Schritt 2 und 3 sind sichtbar identisch; man kann nicht erkennen, dass die Adresse existiert
- Das Profil zeigt keinen Wohnort, keinen Namen von Lena und keine Notizen

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req055, ps-acc-039, ps-acc-016, ps-acc-058, link-reichweite, oeffentliches-profil, lena, desktop]
**Related**: TC-055-010, TC-055-011

---

### TC-055-010: „Link neu erzeugen" — alter Link ist ungültig

**Requirement**: REQ-055 §17.1, §25.2 (Mehr)
**PS-ACC**: PS-ACC-039 (zweiter Teil)
**Gerät**: Desktop
**Priority**: P2
**Category**: Berechtigung
**Preconditions**:
- Mona mit Profil „Jeder mit dem Link"; alter Link A bekannt

**Testschritte**:
1. Lena öffnet im Tab „Profil" „Mehr" und wählt „Link neu erzeugen"
2. Lena liest die Warnung und bestätigt
3. Lena kopiert den neuen Link B
4. Im zweiten Kontext öffnet der Test A, danach B

**Erwartete Ergebnisse**:
- Vor dem Bestätigen steht, dass der bisherige Link nicht mehr funktioniert
- A zeigt „nicht gefunden"; B zeigt das Profil
- Das Profil lässt beim Weiterklicken auf einen externen Link keine Herkunftsadresse mitlaufen (kein sichtbarer Effekt; nur über den geöffneten Link im Test nachprüfbar)

**Nachbedingungen**:
- Nur der neue Link funktioniert

**Tags**: [req055, ps-acc-039, link-neu-erzeugen, lena, desktop]

---

### TC-055-011: „Profil verbergen" — Seite nicht mehr erreichbar, Verlauf bleibt

**Requirement**: REQ-055 §19.2 PS-SOC-061, §9.5
**PS-ACC**: PS-ACC-016 (zweiter Teil: intern = nicht gefunden), PS-ACC-038 (Foto-Adresse ungültig)
**Gerät**: Desktop
**Priority**: P2
**Category**: Zustand / Berechtigung
**Preconditions**:
- Mona mit Profil „Jeder mit dem Link" und einem Foto auf dem Profil; Profil-Link und Foto-Adresse im zweiten Kontext bekannt

**Testschritte**:
1. Lena klickt im Tab „Profil" „Profil verbergen" (`identity-hide`) und bestätigt
2. Lena liest die neue Stufe
3. Im zweiten Kontext lädt der Test das Profil und die Adresse des Profilbildes neu
4. Lena öffnet den Tab „Verlauf"
5. Lena stellt über „Wer darf das sehen?" wieder „Jeder mit dem Link" ein

**Erwartete Ergebnisse**:
- „Profil verbergen" ist gut sichtbar und als umkehrbar beschriftet; getrennt davon steht „Profil löschen"
- Die Stufe steht auf „Nur ich und mein Haushalt"
- Profil und Bild liefern im zweiten Kontext „nicht gefunden"
- Der Verlauf ist unverändert vorhanden
- Nach Schritt 5 ist das Profil wieder erreichbar

**Nachbedingungen**:
- Profil wieder sichtbar mit Stufe „Jeder mit dem Link"

**Tags**: [req055, ps-acc-016, ps-acc-038, profil-verbergen, lena, desktop]

---

### TC-055-012: Link teilen auf dem Smartphone und Vorschau-Dialog „So sieht der Link in WhatsApp aus"

**Requirement**: REQ-055 §25.3 PS-UX-002 Schritt 3; §25.4 PS-UX-019
**PS-ACC**: PS-ACC-071 (Messenger-Vorschau, Link-Pfad)
**Gerät**: Smartphone 390 × 844
**Priority**: P2
**Category**: Happy Path / Mobil
**Preconditions**:
- Lena, Mona ohne Profil; Teilen-Funktion des Browsers fehlt im Test (Rückfall auf „Link kopieren")

**Testschritte**:
1. Lena legt das Profil an (Schritte 1 bis 3) mit „Jeder mit dem Link"
2. Lena tippt „Teilen" (`identity-share`)
3. Lena liest den Dialog „So sieht der Link in WhatsApp aus — ok?" und betrachtet die Vorschaukarte
4. Lena bestätigt mit „Ja, ok"
5. Der Test ruft den Link mit der Kopfzeile eines Link-Vorschau-Abrufers (Messenger) ab

**Erwartete Ergebnisse**:
- Weil die Teilen-Funktion fehlt, kopiert der Button den Link und zeigt eine Bestätigung
- Der Dialog zeigt Name und Avatar so, wie der Messenger sie anzeigen wird
- Nach „Ja, ok" zeigt die Vorschau des Messengers den Namen („Mona · Monstera deliciosa"), einen Textauszug und das Bild; ohne die Bestätigung zeigt sie das Bild nicht
- Alle Bedienelemente sind mit dem Daumen erreichbar, kein horizontales Scrollen

**Nachbedingungen**:
- Vorschau für den Link ist freigegeben

**Tags**: [req055, ps-acc-071, ps-ux-019, opengraph, teilen, lena, smartphone]

---

### TC-055-013: „Für alle im Netz auffindbar" mit Wer-sieht-was, Foto-Hinweis und Messenger-Vorschau

**Requirement**: REQ-055 §25.3, PS-UX-003, PS-UX-019; PS-PRI-013
**PS-ACC**: PS-ACC-071
**Gerät**: Desktop
**Priority**: P1
**Category**: Happy Path / Privatsphäre
**Preconditions**:
- Julia, Mona mit Profil „Nur ich und mein Haushalt"; Standort der Site ist hinterlegt; zweiter nicht eingeloggter Browser-Kontext

**Testschritte**:
1. Julia öffnet unter „Wer darf das sehen?" „Mehr Optionen" (`identity-visibility-public`)
2. Julia wählt „Für alle im Netz auffindbar"
3. Julia liest die erscheinenden Sätze und bestätigt den Foto-Hinweis
4. Julia kopiert den Link
5. Im zweiten Kontext öffnet der Test den Link ohne Zusatz
6. Der Test ruft den Link mit der Kopfzeile eines Messenger-Abrufers ab

**Erwartete Ergebnisse**:
- Es erscheint der Satz „Das sehen andere: …/Das sehen sie nie: …" und „Suchmaschinen finden das Profil erst, wenn du es unten erlaubst."
- Der Foto-Hinweis erscheint einmalig
- Das Profil ist im zweiten Kontext ohne Anmeldung erreichbar und zeigt Name, Art und „Seit …", keinen Standort
- Die Messenger-Vorschau zeigt Name und Avatar

**Nachbedingungen**:
- Stufe „Für alle im Netz auffindbar"; der Foto-Hinweis erscheint nicht mehr

**Tags**: [req055, ps-acc-071, ps-ux-003, ps-ux-019, oeffentlich, julia, desktop]

---

### TC-055-014: Aufrufzähler nur für Verwalter

**Requirement**: REQ-055 §25.3 PS-UX-016
**PS-ACC**: abgeleitet aus PS-UX-016
**Gerät**: Desktop
**Priority**: P3
**Category**: Anzeige / Privatsphäre
**Preconditions**:
- Mona mit Profil „Jeder mit dem Link"; Link wird vor dem Test dreimal aus dem zweiten Kontext aufgerufen

**Testschritte**:
1. Lena öffnet den Tab „Profil" und liest die Karte
2. Der Test öffnet im zweiten Kontext das Profil und blättert nach unten zur Fußzeile

**Erwartete Ergebnisse**:
- Lenas Karte zeigt „Dein Profil wurde 3-mal angesehen"
- Auf dem öffentlichen Profil steht kein Aufrufzähler und keine Angabe zu Besuchern

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req055, ps-ux-016, aufrufzaehler, lena, desktop, abgeleitet]

---

### TC-055-015: Jahresrückblick

**Requirement**: REQ-055 §25.3 PS-UX-017
**PS-ACC**: abgeleitet aus PS-UX-017
**Gerät**: Desktop
**Priority**: P3
**Category**: Anzeige / Opt-in
**Preconditions**:
- Mona mit Profil; im laufenden Jahr 14× gegossen, 2 neue Blätter, 5 Fotos; kein Mastodon

**Testschritte**:
1. Lena öffnet den Tab „Profil" und liest die Karte „Jahresrückblick"
2. Lena schaltet „Auf dem Profil zeigen" ein
3. Im zweiten Kontext lädt der Test das Profil neu

**Erwartete Ergebnisse**:
- Die Karte lautet sinngemäß „Mona wurde 2026 14× gegossen, hat 2 neue Blätter bekommen und 5 Fotos gesammelt"
- Vor dem Einschalten fehlt die Karte auf dem Profil; danach ist sie dort sichtbar
- Die Karte enthält nur Zahlen, keine Orte, keine Notizen

**Nachbedingungen**:
- Jahresrückblick auf dem Profil sichtbar

**Tags**: [req055, ps-ux-017, jahresrueckblick, lena, desktop, abgeleitet]

---

### TC-055-016: Vorher/Nachher

**Requirement**: REQ-055 §25.3 PS-UX-018
**PS-ACC**: abgeleitet aus PS-UX-018
**Gerät**: Desktop
**Priority**: P3
**Category**: Anzeige / Opt-in
**Preconditions**:
- Mona mit Profil; zwei auf dem Profil gezeigte Fotos im Abstand von einem Jahr

**Testschritte**:
1. Lena öffnet den Tab „Verlauf" und betrachtet den Vergleich
2. Lena schaltet „Auf dem Profil zeigen" ein
3. Im zweiten Kontext lädt der Test das Profil neu

**Erwartete Ergebnisse**:
- Der Verlauf zeigt „vor einem Jahr / heute" mit dem ältesten und dem neuesten gezeigten Foto
- Auf dem Profil erscheint der Vergleich erst nach dem Einschalten; es werden nur Fotos gezeigt, die Lena gezeigt hat
- Mit weniger als zwei gezeigten Fotos fehlt der Vergleich

**Nachbedingungen**:
- Vergleich auf dem Profil sichtbar

**Tags**: [req055, ps-ux-018, vorher-nachher, lena, desktop, abgeleitet]

---

## 3. Adresse, Archiv, Löschen, Cannabis

### TC-055-017: Adresse ändern — alter Link leitet weiter

**Requirement**: REQ-055 §9.3 Namensgebung, Slug-Historie; §25.2
**PS-ACC**: PS-ACC-004, PS-ACC-001 (Adressvorschlag)
**Gerät**: Desktop
**Priority**: P2
**Category**: Happy Path
**Preconditions**:
- Mona mit Profil „Für alle im Netz auffindbar" und Adresse `mona`; Julia

**Testschritte**:
1. Julia öffnet „Mehr" und das Feld „Adresse" (`identity-slug-input`) und liest den Vorschlag
2. Julia ändert die Adresse auf `monstera-mona` und speichert
3. Der Test öffnet im zweiten Kontext `…/p/mona` und danach `…/p/monstera-mona`

**Erwartete Ergebnisse**:
- Ein Hinweis erklärt, dass der alte Link noch etwa zwölf Monate weiterleitet
- `…/p/mona` leitet auf `…/p/monstera-mona` weiter und zeigt das Profil
- Die neue Adresse zeigt dasselbe Profil

**Nachbedingungen**:
- Neue Adresse gültig, alte leitet weiter

**Tags**: [req055, ps-acc-004, ps-acc-001, adresse, weiterleitung, julia, desktop]

---

### TC-055-018: Adresse ungültig, vergeben oder zu oft geändert

**Requirement**: REQ-055 §9.3; PS-PI-020
**PS-ACC**: PS-ACC-005, PS-ACC-003 (sichtbarer Teil), PS-ACC-002 (sichtbarer Teil)
**Gerät**: Desktop
**Priority**: P2
**Category**: Validierung
**Preconditions**:
- Julia, Mona mit Profil; eine Adresse `taken-one` ist von einem anderen Mandanten belegt; Mona hat 3 Adresswechsel in den letzten 30 Tagen

**Testschritte**:
1. Julia trägt nacheinander `-mona`, `ab`, `inbox` und `Mona!` in das Feld „Adresse" ein
2. Julia trägt `taken-one` ein und speichert
3. Julia trägt eine neue freie Adresse `mona-im-flur` ein und speichert

**Erwartete Ergebnisse**:
- Für jede ungültige Eingabe erscheint eine verständliche Meldung (zu kurz, ungültige Zeichen, reserviert); gespeichert wird nichts
- Bei `taken-one` erscheint „Diese Adresse ist schon vergeben" mit drei Vorschlägen zum Anklicken; die bisherige Adresse bleibt
- Beim vierten Wechsel innerhalb von 30 Tagen erscheint ein Hinweis, dass die Adresse zu oft geändert wurde, mit Zeitangabe, wann es wieder geht
- Die Meldungen enthalten die Wörter Slug und Handle nicht

**Nachbedingungen**:
- Adresse unverändert

**Tags**: [req055, ps-acc-005, ps-acc-003, ps-acc-002, adresse, validierung, julia, desktop]

---

### TC-055-019: Pflanze entfernt — Profil bleibt als Archiv lesbar

**Requirement**: REQ-055 §9.5 Zustandsmodell (archived)
**PS-ACC**: PS-ACC-006
**Gerät**: Desktop
**Priority**: P2
**Category**: Zustandsübergang
**Preconditions**:
- Mona mit Profil „Jeder mit dem Link" und der Regel „Gleich erzählen" für Neues Blatt; Julia

**Testschritte**:
1. Julia entfernt die Pflanze Mona (Pflanze beenden/entfernen)
2. Julia öffnet den Tab „Profil" der entfernten Pflanze
3. Der Test ruft im zweiten Kontext den Profil-Link auf

**Erwartete Ergebnisse**:
- Das Profil trägt eine Kennzeichnung „Archiv" mit der Lebensspanne (von … bis …)
- „Was soll Mona erzählen?" zeigt für alle Typen „Nicht erzählen", ohne dass Julia es einstellen musste
- Das Profil ist weiter erreichbar und zeigt die Lebensspanne

**Nachbedingungen**:
- Profil im Zustand Archiv

**Tags**: [req055, ps-acc-006, archiv, entfernte-pflanze, julia, desktop]

---

### TC-055-020: Profil löschen mit Bestätigung und Beiträgen auf Mastodon

**Requirement**: REQ-055 §9.5, §13.7, §19.1
**PS-ACC**: PS-ACC-007
**Gerät**: Desktop
**Priority**: P1
**Category**: Destruktive Aktion / Berechtigung
**Preconditions**:
- Mona mit Profil „Für alle im Netz auffindbar", verknüpftem Mastodon-Konto und 2 veröffentlichten Beiträgen; Julia ist Leitung ihres persönlichen Mandanten

**Testschritte**:
1. Julia öffnet „Mehr" und klickt „Profil löschen"
2. Julia liest den Dialog und lässt die Option „Beiträge bei Mastodon ebenfalls löschen" angehakt
3. Julia versucht zu bestätigen, ohne die Adresse einzutippen
4. Julia tippt die Adresse zur Bestätigung ein und bestätigt
5. Der Test lädt im zweiten Kontext das Profil und die Zeitleiste des Mocks
6. Julia legt für Mona sofort ein neues Profil mit derselben Adresse an

**Erwartete Ergebnisse**:
- Der Dialog nennt, was gelöscht wird, und bietet „Profil verbergen" als umkehrbare Alternative an
- Der Bestätigen-Button bleibt inaktiv, bis die Adresse stimmt
- Nach dem Löschen zeigt der Tab „Profil" wieder den leeren Zustand
- Das Profil liefert „nicht gefunden"; in der Zeitleiste des Mocks sind beide Beiträge verschwunden
- Beim Anlegen mit derselben Adresse erscheint ein Hinweis, dass sie erst nach 90 Tagen wieder vergeben werden kann
- Aisha als Gärtnerin sieht in einem Organisations-Mandanten keinen Button „Profil löschen"

**Nachbedingungen**:
- Profil gelöscht, Beiträge entfernt

**Tags**: [req055, ps-acc-007, ps-acc-008, loeschen, bestaetigung, julia, desktop]

---

### TC-055-021: Cannabis — Stufen „Link" und „auffindbar" gesperrt, Verknüpfen gesperrt

**Requirement**: REQ-055 §17.5, PS-PRI-040
**PS-ACC**: PS-ACC-077, PS-ACC-009
**Gerät**: Desktop
**Priority**: P1
**Category**: Berechtigung / Rechtliche Sperre
**Preconditions**:
- Max (ZG-001), Pflanze „Greta" der Gattung Cannabis; Betreiber-Einstellung zu regulierten Arten gesperrt

**Testschritte**:
1. Max öffnet den Tab „Profil" von Greta und legt ein Profil an
2. Max versucht in „Wer darf das sehen?", „Jeder mit dem Link" und „Für alle im Netz auffindbar" zu wählen
3. Max liest den Erklärtext
4. Max wählt „Nur ich und mein Haushalt" und speichert
5. Max öffnet den Tab „Verlauf"; Max versucht, bei einem Modul-Zugang „Mit Mastodon verknüpfen" zu starten

**Erwartete Ergebnisse**:
- „Jeder mit dem Link" und „Für alle im Netz auffindbar" sind deaktiviert und lassen sich nicht anklicken
- Ein Erklärtext nennt das Werbeverbot für Cannabis und enthält den Satz „Wenn das ein Irrtum ist, melde es"
- „Nur ich und mein Haushalt" ist wählbar und lässt sich speichern
- Der Verlauf funktioniert unverändert
- „Mit Mastodon verknüpfen" ist für Greta nicht startbar; ein Hinweis nennt denselben Grund

**Nachbedingungen**:
- Greta hat ein Profil nur für Max und den Haushalt

**Tags**: [req055, ps-acc-077, ps-acc-009, cannabis, sperre, max, desktop]

---

## 4. Mit Mastodon verknüpfen

### TC-055-022: Vorschaltseite, „Nein, wie geht das?" und „Lieber nicht, nur den Link nutzen"

**Requirement**: REQ-055 §25.4 PS-UX-008 Bildschirm 1
**PS-ACC**: PS-ACC-072 (erster Teil)
**Gerät**: Desktop
**Priority**: P1
**Category**: Navigation / Aufklärung
**Preconditions**:
- Julia, Mona mit Profil; keine Verknüpfung; Mock `plants.test` in der Serverliste; Betreiber-Server-Liste mit 3 Vorschlägen

**Testschritte**:
1. Julia öffnet im Tab „Profil" „Verknüpftes Mastodon-Konto" und klickt „Mit Mastodon verknüpfen" (`connection-start`)
2. Julia liest die Vorschaltseite (`connection-intro`)
3. Julia klickt „Nein, wie geht das?"
4. Julia klickt „Lieber nicht, nur den Link nutzen"

**Erwartete Ergebnisse**:
- Zuerst erscheint die Vorschaltseite: „Mastodon ist ein soziales Netzwerk aus vielen unabhängigen Servern — wie E-Mail. Dafür brauchst du ein Mastodon-Konto für Mona (nicht dein eigenes). … Hast du schon eins?" mit den Auswahlmöglichkeiten „Ja, verknüpfen", „Nein, wie geht das?" und „Lieber nicht, nur den Link nutzen"
- „Nein, wie geht das?" zeigt eine Kurzanleitung in drei Schritten, 3 bis 5 empfohlene Server, den Hinweis auf E-Mail-Bestätigung und Freischaltung und einen Vorschlag für den Mastodon-Namen, der aus der Adresse der Pflanze abgeleitet ist
- „Lieber nicht, nur den Link nutzen" führt zurück zum Tab „Profil" bzw. zum Link-Pfad; es entsteht keine Verknüpfung

**Nachbedingungen**:
- Keine Verknüpfung angelegt

**Tags**: [req055, ps-acc-072, ps-ux-008, vorschaltseite, mastodon, julia, desktop]
**Related**: TC-055-024

---

### TC-055-023: Zustimmung zur Übertragung an Mastodon

**Requirement**: REQ-055 §17.6, PS-PRI-054
**PS-ACC**: PS-ACC-035 (sichtbarer Teil)
**Gerät**: Desktop
**Priority**: P2
**Category**: Einwilligung
**Preconditions**:
- Julia, Zustimmung zur Übertragung an Mastodon **nicht** erteilt; Mona mit Profil

**Testschritte**:
1. Julia startet „Mit Mastodon verknüpfen", wählt „Ja, verknüpfen" und `plants.test`
2. Julia liest den Hinweis auf dem Auswahl-Bildschirm
3. Julia versucht, ohne Zustimmung fortzufahren
4. Julia erteilt das OK zur Übertragung und fährt fort
5. Später widerruft Julia in den Einstellungen das OK zur Übertragung

**Erwartete Ergebnisse**:
- Der Hinweis nennt, welche Daten an Mastodon gehen, und bietet „Jetzt geben" für das OK an
- Ohne Zustimmung geht es nicht weiter und es entsteht keine Weiterleitung zum Mock
- Nach Erteilung wird zur Login-Seite des Mocks weitergeleitet
- Nach dem Widerruf steht die Karte „Verknüpftes Mastodon-Konto" auf „Getrennt" bzw. „Aufgehoben"; neue Entwürfe kommen nicht mehr

**Nachbedingungen**:
- Verknüpfung widerrufen

**Tags**: [req055, ps-acc-035, einwilligung, mastodon, julia, desktop]

---

### TC-055-024: Verknüpfen — Mock-Login, Zurück, „Bestätigen"

**Requirement**: REQ-055 §13.3, §25.4 PS-UX-008 Bildschirm 2
**PS-ACC**: PS-ACC-072, PS-ACC-040, PS-ACC-041, PS-ACC-052
**Gerät**: Desktop
**Priority**: P1
**Category**: Happy Path
**Preconditions**:
- Julia, Zustimmung erteilt, Mona mit Profil; Mock liefert Konto `@monstera_mona@plants.test` mit Kennzeichen „automatisch"

**Testschritte**:
1. Julia wählt „Ja, verknüpfen" und `plants.test` aus der Liste (`connection-instance-plants.test`)
2. Julia liest die Hinweise auf dem Bildschirm
3. Julia wird zum Mock weitergeleitet, sieht die Login-Seite des Mocks, meldet sich an und klickt „Zustimmen"
4. Julia kehrt zu Kamerplanter zurück und betrachtet die Konto-Karte (`connection-card-<key>`)
5. Julia klickt „Bestätigen" (`connection-confirm`)

**Erwartete Ergebnisse**:
- Es steht: „Du wirst zu plants.test weitergeleitet, Kamerplanter sieht dein Passwort nicht"; die Rechte stehen in Alltagssprache („darf Beiträge und Fotos veröffentlichen — nicht lesen, nicht folgen")
- Die Adressleiste enthält nach der Rückkehr keinen Code und kein Token
- Die Konto-Karte zeigt Avatar, den Mastodon-Namen `@monstera_mona@plants.test` und das Kennzeichen „automatisch"; sie ist noch nicht aktiv, bis „Bestätigen" gedrückt wurde
- Nach „Bestätigen" steht die Karte auf aktiv; ein zweiter Aufruf des Rückkehr-Links zeigt eine verständliche Fehlerseite statt einer zweiten Verknüpfung
- Es existiert genau ein Konto; ein zweites Verknüpfen mit demselben Server legt keine zweite Server-Registrierung an (kein sichtbarer Unterschied)

**Nachbedingungen**:
- Mona hat ein aktives verknüpftes Mastodon-Konto

**Tags**: [req055, ps-acc-072, ps-acc-040, ps-acc-041, ps-acc-052, verknuepfen, mock, julia, desktop]
**Related**: TC-055-022, TC-055-025, TC-055-027

---

### TC-055-025: Konto ohne Kennzeichen „automatisch" — empfohlene Option zuerst

**Requirement**: REQ-055 §25.4 PS-UX-008 (Bot-Kennzeichen)
**PS-ACC**: PS-ACC-072 (zweiter Teil), PS-ACC-042
**Gerät**: Desktop
**Priority**: P1
**Category**: Fehlerbehandlung / Entscheidung
**Preconditions**:
- Wie TC-055-024, aber der Mock liefert das Konto **ohne** Kennzeichen „automatisch"

**Testschritte**:
1. Julia durchläuft Verknüpfen bis zur Rückkehr und „Bestätigen"
2. Julia liest den Dialog und die Reihenfolge der Optionen (`connection-botflag-<option>`)
3. Julia wählt „Kamerplanter soll das für mich einstellen" und liest den zweiten Zustimmungsschritt
4. Julia stimmt zu
5. In einem zweiten Durchlauf stellt der Test das Kennzeichen im Mock von Hand ein; Julia wählt „Ich mache das selbst in Mastodon (Anleitung)" und klickt danach „Nochmal prüfen"

**Erwartete Ergebnisse**:
- Der Titel lautet „Dein Konto ist noch nicht als ‚automatisch' gekennzeichnet" mit der Erklärung, dass sonst schnell Sperren drohen
- Die Optionen stehen in der Reihenfolge: „Kamerplanter soll das für mich einstellen" (als empfohlen markiert), „Ich mache das selbst in Mastodon (Anleitung)", „Ich poste nur selbst, ohne Automatik"
- Der zweite Schritt sagt: „Kamerplanter darf dann Name, Beschreibung und Kennzeichnung ändern — nicht lesen, nicht folgen"
- Nach der Zustimmung (und im Mock gesetztem Kennzeichen) zeigt die Konto-Karte „automatisch" und die Verknüpfung wird aktiv
- Solange das Kennzeichen fehlt, steht die Karte auf „Wartet auf Kennzeichnung" und es gehen keine Beiträge raus

**Nachbedingungen**:
- Verknüpfung aktiv, Kennzeichen gesetzt

**Tags**: [req055, ps-acc-072, ps-acc-042, ps-ux-008, bot-kennzeichen, julia, desktop]

---

### TC-055-026: Ungültiger Mastodon-Server wird abgelehnt

**Requirement**: REQ-055 §13.2, §18; PS-SEC
**PS-ACC**: PS-ACC-043
**Gerät**: Desktop
**Priority**: P2
**Category**: Validierung
**Preconditions**:
- Julia, Zustimmung erteilt; ein Server `blocked.test` steht auf der Sperrliste des Betreibers

**Testschritte**:
1. Julia startet „Mit Mastodon verknüpfen" und wählt „Ja, verknüpfen"
2. Julia trägt im freien Feld `localhost`, dann `10.0.0.5`, dann `blocked.test` ein und bestätigt jeweils
3. Julia trägt `plants.test` ein

**Erwartete Ergebnisse**:
- Für `localhost` und `10.0.0.5` erscheint „Das ist keine gültige Mastodon-Server-Adresse" (ohne Weiterleitung)
- Für `blocked.test` erscheint „Dieser Mastodon-Server ist bei dieser Kamerplanter-Installation nicht freigegeben."
- Es erfolgt in keinem der Fälle eine Weiterleitung zum Mock
- `plants.test` leitet zur Login-Seite des Mocks weiter

**Nachbedingungen**:
- Keine Verknüpfung

**Tags**: [req055, ps-acc-043, validierung, mastodon-server, julia, desktop]

---

### TC-055-027: „Bestätigen" nur durch die Person, die verknüpft hat

**Requirement**: REQ-055 §18 (S-001), PS-SEC-016
**PS-ACC**: PS-ACC-052
**Gerät**: Desktop
**Priority**: P2
**Category**: Berechtigung
**Preconditions**:
- Organisations-Mandant „Gemeinschaftsgarten": Tom (Leitung) und Aisha (Gärtnerin); zwei Browser-Sitzungen; Aisha hat die Verknüpfung gestartet und die Zustimmung auf dem Mock gegeben

**Testschritte**:
1. Aisha kehrt zurück und lässt die Konto-Karte offen, ohne „Bestätigen" zu drücken
2. Tom öffnet in seiner Sitzung dieselbe Konto-Karte und klickt „Bestätigen"
3. Aisha klickt „Bestätigen"
4. In einem weiteren Durchlauf öffnet der Test den Rückkehr-Link in einer **fremden** Sitzung (anderer Browser)

**Erwartete Ergebnisse**:
- Toms „Bestätigen" wird abgewiesen mit „Nur die Person, die das Konto verknüpft hat, kann das bestätigen"
- Aishas „Bestätigen" aktiviert die Verknüpfung
- Der Rückkehr-Link in der fremden Sitzung führt nicht zu einer Verknüpfung; es erscheint eine Fehlerseite „Die Verknüpfung ist abgelaufen oder ungültig. Bitte starte sie neu."

**Nachbedingungen**:
- Verknüpfung aktiv durch Aisha

**Tags**: [req055, ps-acc-052, bestaetigen, initiator, aisha, tom, desktop]

---

### TC-055-028: Verknüpfung trennen — Veröffentlicht-Historie bleibt, kein Zielkonto

**Requirement**: REQ-055 §19.2 PS-SOC-063
**PS-ACC**: PS-ACC-076, PS-ACC-044
**Gerät**: Desktop
**Priority**: P1
**Category**: Zustandsübergang
**Preconditions**:
- Julia, Mona mit aktivem verknüpftem Konto, 2 veröffentlichten Beiträgen, einem wartenden Entwurf; Regel „Neues Blatt → Erst fragen"

**Testschritte**:
1. Julia klickt auf der Konto-Karte „Verbindung trennen" (`connection-disconnect`)
2. Julia liest die Rückfrage und bestätigt
3. Julia öffnet den Tab „Veröffentlicht"
4. Julia legt einen neuen Meilenstein „Neues Blatt" an
5. Der Test betrachtet im Mock die Liste der verbundenen Apps

**Erwartete Ergebnisse**:
- Die Rückfrage erklärt, dass bereits veröffentlichte Beiträge auf Mastodon bleiben
- Die Karte zeigt „Getrennt"
- Der Tab „Veröffentlicht" zeigt beide Beiträge weiter mit Link; der wartende Entwurf steht als „Hat nicht geklappt" mit dem Grund, dass die Verknüpfung aufgehoben wurde
- Der neue Meilenstein erzeugt keinen Entwurf mit Zielkonto; stattdessen steht der Hinweis „Kein Konto verbunden"
- Im Mock ist die App nicht mehr autorisiert

**Nachbedingungen**:
- Mona hat keine aktive Verknüpfung

**Tags**: [req055, ps-acc-076, ps-acc-044, trennen, julia, desktop]

---

## 5. Was soll {Name} erzählen und „Wartet auf dein OK"

### TC-055-029: „Was soll Mona erzählen?" in zwei Ebenen

**Requirement**: REQ-055 §25.4 PS-UX-005, §12.3
**PS-ACC**: PS-ACC-020 (Modi), PS-ACC-026 (sichtbarer Teil)
**Gerät**: Desktop
**Priority**: P2
**Category**: Formular
**Preconditions**:
- Julia, Mona mit aktivem verknüpftem Konto; Erfahrungsstufe Fortgeschritten; Betreiber-Obergrenze „höchstens 10 Beiträge pro Tag"

**Testschritte**:
1. Julia öffnet im Tab „Profil" „Was soll Mona erzählen?" (`policy-simple-<question>`)
2. Julia liest die drei Fragen und stellt sie auf „Erst fragen", „Einmal pro Woche" und „Nicht erzählen"
3. Julia klickt „Mehr einstellen"
4. Julia betrachtet die Tabelle (`policy-row-<event_type>`) und die Schalter (`policy-mode-<mode>`)
5. Julia öffnet „Was wird gezeigt?" bei „Neues Blatt" und versucht, ein Produkt (Dünger) zu zeigen
6. Julia zieht den Regler für das Tageslimit auf 50
7. Julia klickt „Standard wiederherstellen"

**Erwartete Ergebnisse**:
- Ebene 1 zeigt: „Neues Blatt, Blüte, Umtopfen → [Erst fragen]", „Gießen → [Einmal pro Woche / Nicht erzählen]", „Alles andere → Nicht erzählen"
- Ebene 2 zeigt je Ereignistyp Symbol, Alltagsname und die Schalter „Nicht erzählen · Erst fragen · Gleich erzählen · Einmal pro Woche"; Typen ohne Zimmerpflanzen-Bezug (z. B. Ernte, Schädling) erscheinen nur, wenn der Mandant solche Ereignisse hat oder die Stufe Fortgeschritten ist
- Dünger/Produkt ist unter „Was wird gezeigt?" nicht auswählbar; der Hinweis nennt, dass er nie gezeigt wird
- Der Regler endet an der sichtbaren Betreiber-Obergrenze (10); 50 ist nicht einstellbar
- „Standard wiederherstellen" setzt alle Schalter auf die Ausgangswerte

**Nachbedingungen**:
- Regeln auf Standard

**Tags**: [req055, ps-ux-005, ps-acc-020, ps-acc-026, regeln, julia, desktop]

---

### TC-055-030: „Erst fragen" — Meilenstein, Karte, Alt-Text, „Freigeben", Beitrag im Mock

**Requirement**: REQ-055 §12.2, §25.4 PS-UX-006, PS-UX-007
**PS-ACC**: PS-ACC-073, PS-ACC-021
**Gerät**: Desktop
**Priority**: P1
**Category**: Happy Path / User Journey
**Preconditions**:
- Julia, Mona mit aktivem verknüpftem Konto (Kennzeichen „automatisch"); „Neues Blatt" auf „Erst fragen"; Freigaben noch nötig

**Testschritte**:
1. Julia öffnet den Tab „Verlauf" und klickt „Meilenstein festhalten"
2. Julia wählt „Neues Blatt", trägt 34 cm ein, wählt ein Foto und speichert
3. Julia öffnet „Wartet auf dein OK" (`review-card-<key>`)
4. Julia liest die Karte, ergänzt den Beschreibungstext des Bildes und klickt „Freigeben" (`review-approve`)
5. Julia öffnet den Tab „Veröffentlicht" und klickt den Link am Beitrag
6. Der Test öffnet die Zeitleiste des Mocks

**Erwartete Ergebnisse**:
- Es erscheint eine Karte mit gerendertem Text (enthält „34 cm"), Bild, Feld für den Alt-Text (`Beschreibung des Bildes`), Zielkonto `@monstera_mona@plants.test`, Wer-sieht-es-Symbol, Herkunft und Restlaufzeit („Noch 14 Tage")
- Der Beitrag enthält keinen Standort und keinen Namen von Julia
- Ohne Alt-Text lässt sich nicht freigeben (Hinweis auf das Feld) oder Julia muss „bewusst leer" bestätigen
- Nach „Freigeben" wechselt der Status-Chip auf „Veröffentlicht" mit Link; eine Statusmeldung „Beitrag veröffentlicht" wird angekündigt
- Der Beitrag steht in der Zeitleiste des Mocks mit Text, Bild und Beschreibung

**Nachbedingungen**:
- Ein veröffentlichter Beitrag

**Tags**: [req055, ps-acc-073, ps-acc-021, ps-ux-006, ps-ux-007, freigabe, julia, desktop]
**Related**: TC-055-034, TC-055-035

---

### TC-055-031: „Gleich erzählen" — Beitrag geht ohne Rückfrage raus

**Requirement**: REQ-055 §12.2, §12.3 (`review_required_until_posts`)
**PS-ACC**: PS-ACC-020
**Gerät**: Desktop
**Priority**: P2
**Category**: Happy Path
**Preconditions**:
- Julia, aktive Verknüpfung; „Neues Blatt" auf „Gleich erzählen"; Rückfragepflicht für die ersten Beiträge ausgeschaltet; Einstellung „Veröffentlichungsfenster" aus

**Testschritte**:
1. Julia legt einen Meilenstein „Neues Blatt" mit 34 cm und Foto an
2. Julia öffnet den Tab „Veröffentlicht"
3. Der Test öffnet die Zeitleiste des Mocks

**Erwartete Ergebnisse**:
- Es erscheint keine Karte in „Wartet auf dein OK"
- Der Beitrag steht kurz im Zustand „Wird gesendet" und dann auf „Veröffentlicht" mit Link
- Der Text enthält „34 cm" und die Schlagwörter #Monstera #PlantDiary, aber keinen Standort, keine Sensorwerte und keinen Namen
- Das Foto im Mock trägt eine Bildbeschreibung

**Nachbedingungen**:
- Ein veröffentlichter Beitrag

**Tags**: [req055, ps-acc-020, gleich-erzaehlen, julia, desktop]

---

### TC-055-032: „Einmal pro Woche" — ein Wochenrückblick auf Mastodon

**Requirement**: REQ-055 §12.5 PS-SOC-021
**PS-ACC**: PS-ACC-022
**Gerät**: Desktop
**Priority**: P2
**Category**: Zeitgesteuert
**Preconditions**:
- Julia, aktive Verknüpfung; Gießen auf „Einmal pro Woche" (Sonntag 18:00); 3 Gießvorgänge in dieser Woche; Rückfragepflicht aus

**Testschritte**:
1. Julia trägt drei Mal Gießen innerhalb der Woche ein
2. Der Test setzt die Uhr hinter Sonntag 18:00
3. Julia öffnet den Tab „Veröffentlicht"

**Erwartete Ergebnisse**:
- Vor dem Wochenende entsteht kein Beitrag
- Danach erscheint genau ein Beitrag „💧 Diese Woche wurde ich dreimal gegossen." mit der Kennzeichnung „Wochenrückblick"
- In einer Woche ohne Gießen erscheint kein Wochenrückblick

**Nachbedingungen**:
- Ein Wochenrückblick veröffentlicht

**Tags**: [req055, ps-acc-022, wochenrueckblick, julia, desktop]

---

### TC-055-033: Sammelaktionen und Ablauf-Hinweis

**Requirement**: REQ-055 §25.4 PS-UX-006, PS-UX-007
**PS-ACC**: abgeleitet aus PS-UX-006 / PS-UX-007 (ergänzt PS-ACC-073)
**Gerät**: Desktop
**Priority**: P2
**Category**: Listenaktion / Zeit
**Preconditions**:
- Julia, aktive Verknüpfung; Liste „Wartet auf dein OK" mit 1 Karte, später 3 Karten; eine Karte ist 14 Tage alt

**Testschritte**:
1. Julia öffnet die Liste mit einer Karte und sucht nach Sammelaktionen
2. Der Test legt zwei weitere Entwürfe an; Julia lädt die Liste neu
3. Julia liest die Restlaufzeit an den Karten
4. Julia klickt „Alle verwerfen" (`review-approve-all`/`review-discard` im Dialog) und liest die Rückfrage, dann bricht sie ab
5. Julia klickt „Alle freigeben"
6. Der Test lässt die vierzehn Tage alte Karte ablaufen; Julia öffnet den Tab „Veröffentlicht"

**Erwartete Ergebnisse**:
- Bei einer Karte gibt es keine Sammelaktionen; ab zwei Karten erscheinen „Alle freigeben" und „Alle verwerfen"
- Jede Karte zeigt die Restlaufzeit („Noch 3 Tage")
- „Alle verwerfen" fragt nach und lässt sich abbrechen
- „Alle freigeben" veröffentlicht alle Karten; die Chips wechseln auf „Veröffentlicht"
- Die abgelaufene Karte erscheint mit dem Chip „Abgelaufen" und dem Text „Abgelaufen — du hast diesen Vorschlag zwei Wochen nicht bearbeitet."
- Die Tasten A (freigeben), E (bearbeiten), D (verwerfen) funktionieren auf Desktop

**Nachbedingungen**:
- Keine wartenden Karten

**Tags**: [req055, ps-ux-006, ps-ux-007, sammelaktionen, ablauf, julia, desktop, abgeleitet]

---

### TC-055-034: Angebot nach dem 10. Beitrag — „Das lief 10-mal gut"

**Requirement**: REQ-055 §25.4 PS-UX-006
**PS-ACC**: PS-ACC-073 (zweiter Teil)
**Gerät**: Desktop
**Priority**: P2
**Category**: Hinweis / Einmaligkeit
**Preconditions**:
- Julia (persönlicher Mandant), 9 freigegebene Beiträge, ein zehnter wartet; Angebot noch nie gezeigt

**Testschritte**:
1. Julia gibt den zehnten Beitrag frei (`review-approve`)
2. Julia liest das Angebot (`review-auto-offer`) und klickt „Weiter erst fragen"
3. Der Test legt einen elften Beitrag an; Julia gibt ihn frei
4. Der Test wiederholt den Ablauf mit einer zweiten Pflanze, bei der Julia „Ja, gleich erzählen" wählt
5. Julia legt für diese Pflanze einen neuen Meilenstein an

**Erwartete Ergebnisse**:
- Nach dem zehnten Beitrag erscheint einmalig: „Das lief 10-mal gut. Soll Mona künftig ohne Rückfrage erzählen?" mit „Ja, gleich erzählen" und „Weiter erst fragen"
- Nach „Weiter erst fragen" erscheint das Angebot nicht noch einmal
- Nach „Ja, gleich erzählen" erscheint der neue Meilenstein ohne Karte direkt als „Veröffentlicht"
- Im Organisations-Mandanten sieht nur die Leitung das Angebot (siehe TC-055-041)

**Nachbedingungen**:
- Entscheidung gespeichert

**Tags**: [req055, ps-acc-073, ps-ux-006, angebot, julia, desktop]

---

### TC-055-035: Freigabe-Liste auf dem Smartphone — große Flächen, Rückfrage beim Verwerfen

**Requirement**: REQ-055 §26 PS-UX-030
**PS-ACC**: PS-ACC-074
**Gerät**: Smartphone 390 × 844
**Priority**: P1
**Category**: Mobil / Bedienbarkeit
**Preconditions**:
- Julia mit 3 wartenden Entwürfen

**Testschritte**:
1. Julia öffnet „Wartet auf dein OK" im Browser des Telefons
2. Julia streicht durch die drei Karten und betrachtet die Aktionsflächen
3. Julia tippt auf der ersten Karte „Verwerfen"
4. Julia bestätigt die Rückfrage
5. Julia tippt auf der zweiten Karte „Freigeben"

**Erwartete Ergebnisse**:
- Die Karten stehen als Stapel untereinander; kein horizontales Scrollen tritt auf
- „Freigeben" und „Verwerfen" sind mindestens 48 px hoch und breit
- „Verwerfen" fragt nach, bevor etwas gelöscht wird
- „Freigeben" veröffentlicht den Beitrag; ein Hinweis bestätigt es
- Verknüpfte Server, Rechte und Texte sind lesbar

**Nachbedingungen**:
- Eine Karte verworfen, eine veröffentlicht, eine wartet

**Tags**: [req055, ps-acc-074, ps-ux-030, freigabe, mobil, julia, smartphone]

---

### TC-055-036: Tageslimit und Veröffentlichungsfenster sind sichtbar

**Requirement**: REQ-055 §12.5 PS-SOC-020, PS-PRI-021
**PS-ACC**: PS-ACC-023, PS-ACC-083
**Gerät**: Desktop
**Priority**: P3
**Category**: Zeitsteuerung
**Preconditions**:
- Julia, aktive Verknüpfung; Tageslimit „3 Beiträge"; 3 Beiträge heute veröffentlicht; Veröffentlichungsfenster 12:00 und 18:00; Uhr eingefroren auf 09:13; „Neues Blatt" auf „Gleich erzählen"

**Testschritte**:
1. Julia legt einen Meilenstein „Neues Blatt" an
2. Julia öffnet den Tab „Veröffentlicht" und liest den Status
3. Julia versucht, einen manuellen Beitrag „Jetzt senden" zu schreiben
4. Der Test ändert das Tageslimit auf 10 und setzt die Uhr auf Vortag, Julia legt einen weiteren Meilenstein an

**Erwartete Ergebnisse**:
- Der Beitrag aus Schritt 1 steht auf „Geplant" mit Hinweis „Heute ist das Limit erreicht — wird morgen gesendet"
- Der manuelle Beitrag wird abgewiesen mit „Heute ist das Limit erreicht" und der Angabe, wann es wieder geht
- Mit freiem Limit steht der Beitrag auf „geplant für 12:00" (Zeit innerhalb 15 Minuten um 12:00) statt sofort gesendet zu werden
- Ein manueller Beitrag mit „Jetzt senden" geht dagegen sofort raus

**Nachbedingungen**:
- Beiträge geplant bzw. gesendet

**Tags**: [req055, ps-acc-023, ps-acc-083, tageslimit, fenster, julia, desktop]

---

### TC-055-037: Burst-Pause — Profil pausiert, Leitung wird benachrichtigt

**Requirement**: REQ-055 §12.5 PS-SOC-023, §19.2 PS-SOC-060, PS-SOC-081
**PS-ACC**: PS-ACC-024
**Gerät**: Desktop
**Priority**: P2
**Category**: Schutzfunktion
**Preconditions**:
- Julia, Mona mit aktiver Verknüpfung; Test-Import legt 25 Ereignisse in 10 Minuten an

**Testschritte**:
1. Der Test löst den Import aus
2. Julia öffnet die Benachrichtigungen und dann den Tab „Profil" von Mona
3. Julia öffnet „Wartet auf dein OK"
4. Julia klickt „Wieder aufnehmen"

**Erwartete Ergebnisse**:
- Eine Benachrichtigung „Mona wurde pausiert, weil sehr viele Ereignisse auf einmal kamen" erscheint
- Der Tab „Profil" zeigt „Pausiert" mit dem Grund; es entstehen keine Beiträge aus dem Import
- Neue Vorschläge zur Freigabe entstehen weiter; nichts geht verloren
- Nach „Wieder aufnehmen" ist die Pause aufgehoben

**Nachbedingungen**:
- Pflanze wieder aktiv

**Tags**: [req055, ps-acc-024, burst, pause, benachrichtigung, julia, desktop]

---

## 6. Veröffentlicht — Fehler, Wiederholen, Löschen

### TC-055-038: Fehlgeschlagener Beitrag — Text und „Nochmal senden"

**Requirement**: REQ-055 §13.6, §25.4 PS-UX-007
**PS-ACC**: PS-ACC-075, PS-ACC-046
**Gerät**: Desktop
**Priority**: P1
**Category**: Fehlerbehandlung
**Preconditions**:
- Julia, aktive Verknüpfung; Mock antwortet mit „nicht erreichbar"; ein Beitrag steht in der Warteschlange und die Versuche sind erschöpft

**Testschritte**:
1. Julia öffnet den Tab „Veröffentlicht"
2. Julia liest die Zeile des Beitrags
3. Der Test stellt den Mock wieder her
4. Julia klickt „Nochmal senden"

**Erwartete Ergebnisse**:
- Die Zeile trägt den Chip „Hat nicht geklappt" (Text, nicht nur Farbe) mit dem Satz „Hat nicht geklappt — Mastodon war gerade nicht erreichbar. Wir haben es mehrfach versucht."
- Daneben steht der Button „Nochmal senden"
- Nach dem Klick wechselt der Chip auf „Wird gesendet" und anschließend auf „Veröffentlicht" mit Link
- Der Beitrag steht im Mock

**Nachbedingungen**:
- Beitrag veröffentlicht

**Tags**: [req055, ps-acc-075, ps-acc-046, fehler, nochmal-senden, julia, desktop]

---

### TC-055-039: Weitere Fehlertexte — Zu viele Beiträge, Verknüpfung aufgehoben, Konto gesperrt

**Requirement**: REQ-055 §25.4 PS-UX-007
**PS-ACC**: PS-ACC-045, PS-ACC-047
**Gerät**: Desktop
**Priority**: P2
**Category**: Fehlerbehandlung
**Preconditions**:
- Julia, aktive Verknüpfung; Mock wird nacheinander so eingestellt: (a) „zu viele Anfragen, in 90 Sekunden wieder", (b) „Zugriff abgelehnt, App nicht mehr autorisiert", (c) „Konto gesperrt"

**Testschritte**:
1. Der Test stellt den Mock auf (a) und löst einen Beitrag aus; Julia öffnet den Tab „Veröffentlicht"
2. Der Test stellt den Mock auf (b) und löst einen Beitrag aus; Julia betrachtet Zeile und Konto-Karte
3. Julia klickt „Neu verknüpfen"
4. Der Test stellt den Mock auf (c) und löst einen Beitrag aus

**Erwartete Ergebnisse**:
- (a) „Zu viele Beiträge in kurzer Zeit. Wir senden später automatisch." — ohne Fehler-Chip und ohne Button; der Beitrag geht nach Ablauf selbständig raus
- (b) „Die Verknüpfung wurde in Mastodon aufgehoben. Verknüpfe das Konto neu, dann geht es weiter." mit „Neu verknüpfen"; die Konto-Karte zeigt einen Hinweis und eine Benachrichtigung ging an die verknüpfende Person; „Neu verknüpfen" startet den Ablauf aus TC-055-024
- (c) „Mastodon hat das Konto gesperrt. Wir senden nichts mehr. Das klärst du direkt bei deinem Mastodon-Server." mit „Wie geht das?"
- Jeder Text hat einen Handlungs-Button bzw. eine klare Auskunft

**Nachbedingungen**:
- Zustand je nach Mock

**Tags**: [req055, ps-acc-045, ps-acc-047, ps-ux-007, fehlertexte, julia, desktop]

---

### TC-055-040: Veröffentlichten Beitrag löschen

**Requirement**: REQ-055 §19.2 PS-SOC-062
**PS-ACC**: PS-ACC-029
**Gerät**: Desktop
**Priority**: P2
**Category**: Destruktive Aktion
**Preconditions**:
- Julia, ein veröffentlichter Beitrag; ein weiterer Beitrag, den der Mock bereits entfernt hat

**Testschritte**:
1. Julia öffnet den Tab „Veröffentlicht" und klickt beim ersten Beitrag „Beitrag löschen"
2. Julia liest die Rückfrage und bestätigt
3. Der Test prüft die Zeitleiste des Mocks
4. Julia löscht auch den zweiten Beitrag

**Erwartete Ergebnisse**:
- Die Rückfrage nennt, dass der Beitrag auch bei Mastodon gelöscht wird
- Der Chip wechselt auf „Gelöscht"; der Beitrag ist im Mock verschwunden
- Der zweite Beitrag zeigt ebenfalls „Gelöscht", ohne Fehlermeldung

**Nachbedingungen**:
- Beide Beiträge gelöscht

**Tags**: [req055, ps-acc-029, loeschen, beitrag, julia, desktop]

---

## 7. Garten-Konto im Organisations-Mandanten

### TC-055-041: Gärtnerin schlägt vor — Leitung gibt frei

**Requirement**: REQ-055 §19.1, PS-SEC-035
**PS-ACC**: PS-ACC-065
**Gerät**: Desktop
**Priority**: P1
**Category**: Berechtigung / Governance
**Preconditions**:
- Organisations-Mandant „Gemeinschaftsgarten"; Tom (Leitung) und Aisha (Gärtnerin); Pflanze „Rosi" mit verknüpftem Garten-Konto; Rückfragepflicht liegt bei der Leitung

**Testschritte**:
1. Aisha öffnet „Was soll Rosi erzählen?" und versucht, „Neues Blatt" auf „Gleich erzählen" zu stellen
2. Aisha versucht, die Rückfragepflicht für die ersten Beiträge auf 0 zu senken
3. Aisha schreibt im Tab „Veröffentlicht" einen manuellen Beitrag und klickt „Jetzt senden"
4. Aisha öffnet „Wartet auf dein OK"
5. Tom öffnet „Wartet auf dein OK" und gibt den Beitrag frei
6. Tom stellt „Neues Blatt" auf „Gleich erzählen"

**Erwartete Ergebnisse**:
- Aishas Einstellungen für „Gleich erzählen" sind deaktiviert oder werden abgewiesen mit „Das darf nur die Leitung"
- Dasselbe gilt für die Rückfragepflicht
- Aishas Beitrag landet als Karte bei Toms „Wartet auf dein OK" statt zu veröffentlichen; Aisha sieht ihn als „Wartet auf dein OK" ohne eigene „Freigeben"-Schaltfläche
- Im Mock steht noch nichts, bevor Tom freigibt; nach Toms „Freigeben" ist der Beitrag veröffentlicht
- Das Angebot „Das lief 10-mal gut …" erscheint nur Tom
- Tom kann „Gleich erzählen" einstellen, ändert er die Freigabe-Regeln des Gartens, verlangt eine zusätzliche Bestätigung seiner Identität

**Nachbedingungen**:
- Beitrag von Aisha durch Tom veröffentlicht

**Tags**: [req055, ps-acc-065, governance, garten-konto, aisha, tom, desktop]

---

### TC-055-042: Austritt der Gärtnerin — Garten-Konto pausiert

**Requirement**: REQ-055 PS-SEC-036, PS-SOC-081
**PS-ACC**: PS-ACC-068
**Gerät**: Desktop
**Priority**: P2
**Category**: Zustandsübergang / Berechtigung
**Preconditions**:
- Aisha hat das Konto für „Rosi" verknüpft und bestätigt; ein Beitrag ist für 12:00 geplant; Tom ist Leitung

**Testschritte**:
1. Tom entfernt Aisha aus dem Gemeinschaftsgarten
2. Tom öffnet die Benachrichtigungen
3. Tom öffnet die Konto-Karte von Rosi
4. Der Test lässt die Uhr 12:00 überschreiten

**Erwartete Ergebnisse**:
- Eine Benachrichtigung nennt, dass das verknüpfte Konto pausiert wurde, weil die verknüpfende Person ausgetreten ist
- Die Konto-Karte zeigt „Pausiert" mit dem Grund „Die Person, die das Konto verknüpft hat, ist nicht mehr dabei" und bietet „Neu verknüpfen"
- Der geplante Beitrag wird nicht gesendet
- Nach „Neu verknüpfen" durch Tom (TC-055-024) ist das Konto wieder aktiv

**Nachbedingungen**:
- Konto neu verknüpft oder pausiert

**Tags**: [req055, ps-acc-068, austritt, garten-konto, tom, desktop]

---

## 8. Betrieb

### TC-055-043: Ohne Social-Feature — Profil und Link funktionieren, Mastodon nirgends sichtbar

**Requirement**: REQ-055 §25.2 PS-UX-001, §27
**PS-ACC**: PS-ACC-055 (sichtbarer Teil)
**Gerät**: Desktop
**Priority**: P1
**Category**: Konfiguration
**Preconditions**:
- Installation mit abgeschaltetem Social-Feature; Julia, Mona mit Profil „Jeder mit dem Link"

**Testschritte**:
1. Julia öffnet Monas Detailseite
2. Julia durchsucht Tabs, Hauptnavigation und die Einstellungen → Module
3. Julia öffnet „Wer darf das sehen?" und den Profil-Link
4. Julia öffnet „Was soll Mona erzählen?" und stellt Gießen auf „Einmal pro Woche"
5. Der Test öffnet im zweiten Kontext den Profil-Link

**Erwartete Ergebnisse**:
- Die Tabs „Profil" und „Verlauf" sind vorhanden, der Tab „Veröffentlicht" und die Seite „Pflanzen-Posts" fehlen
- „Mit Mastodon verknüpfen" erscheint nirgends; „Was soll Mona erzählen?" bleibt vorhanden, aber ohne Mastodon-Spalte — die Regeln steuern nur, was auf dem Profil erscheint (PS-SOC-004a)
- Das Modul „Pflanzen-Posts" lässt sich in den Einstellungen nicht aktivieren oder steht nicht zur Auswahl
- Das Profil funktioniert wie sonst; die Stufen und die Gieß-Regel werden gespeichert
- Ist zusätzlich die Funktion „öffentliche Profile" abgeschaltet, ist „Für alle im Netz auffindbar" deaktiviert und das Profil unter Link nicht erreichbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req055, ps-acc-055, ps-ux-001, ohne-social, julia, desktop]

---

### TC-055-044: Kill-Switch — Beiträge bleiben stehen, Löschen und Trennen gehen weiter

**Requirement**: REQ-055 §18, §19.1; PS-SEC
**PS-ACC**: PS-ACC-057
**Gerät**: Desktop
**Priority**: P2
**Category**: Betrieb / Notfall
**Preconditions**:
- Plattform-Betreiber eingeloggt; Julia mit aktiver Verknüpfung, einem geplanten Beitrag und einem veröffentlichten Beitrag

**Testschritte**:
1. Der Betreiber öffnet den Betreiber-Bereich „Pflanzen-Posts" und schaltet „Veröffentlichen anhalten" ein
2. Der Test setzt die Uhr hinter die Zeit des geplanten Beitrags
3. Julia öffnet den Tab „Veröffentlicht"
4. Julia löscht den veröffentlichten Beitrag und trennt die Verknüpfung
5. Julia startet „Mit Mastodon verknüpfen" neu
6. Der Betreiber nimmt den Schalter zurück

**Erwartete Ergebnisse**:
- Julia sieht einen Hinweis „Das Veröffentlichen ist gerade vom Betreiber angehalten"; der geplante Beitrag bleibt „Geplant" ohne Fehler-Chip
- Löschen und Trennen funktionieren trotzdem (Beitrag im Mock weg, Konto getrennt)
- Neu verknüpfen wird mit einem Hinweis zur Pause abgewiesen
- Nach Rücknahme wird der geplante Beitrag gesendet und steht auf „Veröffentlicht"; der Hinweis verschwindet

**Nachbedingungen**:
- Veröffentlichen wieder frei

**Tags**: [req055, ps-acc-057, ps-acc-084, kill-switch, betreiber, julia, desktop]

---

### TC-055-045: Light-Modus — Verknüpfen nicht möglich, Link funktioniert

**Requirement**: REQ-055 §27
**PS-ACC**: PS-ACC-059
**Gerät**: Desktop
**Priority**: P2
**Category**: Konfiguration
**Preconditions**:
- Installation im Light-Modus; Lena, Mona mit Profil „Jeder mit dem Link"

**Testschritte**:
1. Lena öffnet den Tab „Profil" von Mona
2. Lena sucht nach „Mit Mastodon verknüpfen"
3. Der Test öffnet im zweiten Kontext den Profil-Link

**Erwartete Ergebnisse**:
- Der Tab „Profil" zeigt „Wer darf das sehen?", Link und Vorschau
- „Mit Mastodon verknüpfen" ist nicht angeboten; ein Hinweis erklärt, dass es in diesem Betriebsmodus nicht verfügbar ist
- Das Profil unter Link wird angezeigt wie sonst

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req055, ps-acc-059, light-modus, lena, desktop]

---

## Abdeckungs-Matrix

| PS-ACC / PS-UX | Kriterium (Kurzform) | Testfälle |
|----------------|----------------------|-----------|
| PS-ACC-001 | Profil anlegen, Adressvorschlag, Standardstufe | TC-055-002, TC-055-003, TC-055-017 |
| PS-ACC-002 | Adresse vergeben (sichtbarer Teil) | TC-055-018 |
| PS-ACC-003 | Ungültige Adresse (sichtbarer Teil) | TC-055-018 |
| PS-ACC-004 | Adresse ändern, Weiterleitung | TC-055-017 |
| PS-ACC-005 | Adresswechsel-Limit | TC-055-018 |
| PS-ACC-006 | Entfernte Pflanze → Archiv | TC-055-019 |
| PS-ACC-007 | Profil löschen mit Bestätigung | TC-055-020 |
| PS-ACC-008 | Rollen (sichtbarer Teil: Gärtnerin ohne Löschen) | TC-055-020 |
| PS-ACC-009 | Cannabis-Sperre | TC-055-021 |
| PS-ACC-010 | Verlauf (sichtbarer Teil) | TC-055-006 |
| PS-ACC-016 | Link-Reichweite, intern = nicht gefunden | TC-055-009, TC-055-011 |
| PS-ACC-020 | Gleich erzählen | TC-055-029, TC-055-031 |
| PS-ACC-021 | Erst fragen / Freigabe | TC-055-030 |
| PS-ACC-022 | Wochenrückblick | TC-055-008, TC-055-032 |
| PS-ACC-023 | Tageslimit | TC-055-036 |
| PS-ACC-024 | Burst-Pause | TC-055-037 |
| PS-ACC-026 | Obergrenze sichtbar (Regler) | TC-055-029 |
| PS-ACC-029 | Beitrag löschen | TC-055-040 |
| PS-ACC-035 | OK zur Übertragung | TC-055-023 |
| PS-ACC-038 | Foto-Adresse nach Verbergen ungültig | TC-055-011 |
| PS-ACC-039 | Ohne Link „nicht gefunden"; Link neu erzeugen | TC-055-009, TC-055-010 |
| PS-ACC-040 / 041 | Verknüpfen / Rückkehr | TC-055-024 |
| PS-ACC-042 | Kennzeichen „automatisch" fehlt | TC-055-025 |
| PS-ACC-043 | Ungültiger Server | TC-055-026 |
| PS-ACC-044 | Trennen | TC-055-028 |
| PS-ACC-045 / 046 / 047 | Fehlertexte | TC-055-038, TC-055-039 |
| PS-ACC-052 | Bestätigen nur Initiator | TC-055-024, TC-055-027 |
| PS-ACC-055 | Ohne Social-Feature | TC-055-043 |
| PS-ACC-057 | Kill-Switch | TC-055-044 |
| PS-ACC-058 | Gleiche „nicht gefunden"-Seite (sichtbarer Teil) | TC-055-009 |
| PS-ACC-059 | Light-Modus | TC-055-045 |
| PS-ACC-065 | Gärtner im Organisations-Mandanten | TC-055-041 |
| PS-ACC-068 | Austritt → Konto pausiert | TC-055-042 |
| PS-ACC-070 | Link-Pfad Lena | TC-055-001, TC-055-002, TC-055-006 |
| PS-ACC-071 | Auffindbar, Messenger-Vorschau | TC-055-012, TC-055-013 |
| PS-ACC-072 | Verknüpfen Julia, Vorschaltseite, Kennzeichen | TC-055-022, TC-055-024, TC-055-025 |
| PS-ACC-073 | Erst fragen → Freigeben, 10-Posts-Angebot | TC-055-030, TC-055-034 |
| PS-ACC-074 | Smartphone Freigabe-Liste | TC-055-035 |
| PS-ACC-075 | Fehlgeschlagen → Nochmal senden | TC-055-038 |
| PS-ACC-076 | Trennen, Historie bleibt | TC-055-028 |
| PS-ACC-077 | Cannabis (Max) | TC-055-021 |
| PS-ACC-078 | Begriffs-Guard als Sichtprüfung | TC-055-002, TC-055-005 |
| PS-ACC-079 | Foto zum Profil, Gießen als Wochenrückblick | TC-055-007, TC-055-008 |
| PS-ACC-083 | Veröffentlichungsfenster | TC-055-036 |
| PS-ACC-085 | Foto zum Profil, 3 Taps | TC-055-007 |
| PS-UX-005 | Zwei Ebenen | TC-055-029 |
| PS-UX-006 | Sammelaktionen, Angebot, Ablauf | TC-055-033, TC-055-034 |
| PS-UX-008 | Vorschaltseite, „Lieber nicht" | TC-055-022 |
| PS-UX-014 | Anstoß | TC-055-004 |
| PS-UX-016 | Aufrufzähler | TC-055-014 |
| PS-UX-017 | Jahresrückblick | TC-055-015 |
| PS-UX-018 | Vorher/Nachher | TC-055-016 |
| PS-UX-019 | Messenger-Vorschau | TC-055-012, TC-055-013 |

## Nicht abgedeckte Akzeptanzkriterien

| PS-ACC | Kriterium (Kurzform) | Grund |
|--------|----------------------|-------|
| PS-ACC-011 | Recorder-Fehlerinjektion, Reconcile | Integrationstest; Fehlerinjektion nicht über die Oberfläche möglich |
| PS-ACC-012, 013 | Payload-Klassifikation, Recorder-Inventar | Guard-Tests (G), kein sichtbares Gegenstück |
| PS-ACC-014 | Backfill Dry-Run und Zählung | Integrationstest; sichtbar nur indirekt über „Dein Verlauf ist schon da" (TC-055-001) |
| PS-ACC-015 | Änderung nach Veröffentlichung (`payload_version`, `source_changed`) | Integrationstest; es ist keine browser-sichtbare Anzeige definiert |
| PS-ACC-017 | Öffentliche Projektion ohne Standort/Nutzer | Unit-/Guard-Test; Sichtprüfung nur summarisch in TC-055-009 |
| PS-ACC-025 | Backfill/Import erzeugt keinen Beitrag | Integrationstest; sichtbar nur indirekt in TC-055-037 |
| PS-ACC-027 | Vorlagen-Guard | Guard-/Unit-Test |
| PS-ACC-028 | Anhänge: Anzahl, Alt-Text-Pflicht, fremde Anhänge | API-Vertrag; Alt-Text-Pflicht nur am Rande in TC-055-030 |
| PS-ACC-030 | Schema-Snapshot der öffentlichen Antwort | Schema-/Sicherheitstest |
| PS-ACC-031, 032 | Ortsangabe, Herkunftstext | Integrationstest; sichtbar nur in TC-055-009 (kein Wohnort) |
| PS-ACC-033 | EXIF-Entfernung | Byte-Prüfung am Medienkörper |
| PS-ACC-034 | Import-Guard Projektion | Guard-Test |
| PS-ACC-036, 037 | Art.-15-Export, Art.-17-Löschung, Purge | Integrations-/DSGVO-Test; nicht browser-spezifisch |
| PS-ACC-048, 049 | Medien-Polling, Idempotenz nach Worker-Abbruch | Integrationstest |
| PS-ACC-050 | Token-Felder, Log-Schwärzung | Guard-Test |
| PS-ACC-051 | Mandanten-Verbindung mit Namenszeile | Integrationstest; Garten-Konto sichtbar in TC-055-041 nur über Freigabe |
| PS-ACC-056 | Start ohne Schlüssel bricht ab | Startup-/Betriebstest |
| PS-ACC-060 bis 063 | Persönlichkeit, KI-Text | Nicht MVP; gelten ab Umsetzung |
| PS-ACC-066, 067 | Mandantengrenzen bei Posts; Titel nie öffentlich | API-/Sicherheitstest |
| PS-ACC-069 | Idempotenz-Schlüssel, mehrdeutiges Ergebnis | Integrationstest |
| PS-ACC-080, 081, 082 | Reconcile-Alter, Kappung Mock-Werte, Connect-Limit | Integrationstest |
| PS-ACC-084 | Löschen/Trennen bei Pause | Teilweise in TC-055-044 |
| PS-UX-007 (Texte `moderation_hold`, `text_too_long`, `media_rejected`, `instance_blocked` (teilweise), `consent_missing` (teilweise), `ambiguous_result`) | Weitere Fehlertexte | Nur Mindestsatz in TC-055-038 / -039 / -026 / -023 abgedeckt; die restlichen Texte als Folgefälle möglich |
| PS-UX-009 (Tooltip aller sieben Herkunftssymbole) | Symbolsatz | Nur Mensch/Kamerplanter in TC-055-006 |
| PS-UX-020 | Barrierefreiheit | e2e-nightly-a11y-Lauf |
| PS-UX-032 | Gebündelte Push-Nachricht | PWA-Push im Browser-Test nicht belegbar |
