# Review REQ-053 v1.1 (Grafische Garten- und Beetplanung) — Sicht Hobbygärtnerin / Gemeinschaftsgarten

**Erstellt von:** Ambitionierte Hobbygärtnerin (Subagent `outdoor-garden-planner-reviewer`)
**Datum:** 2026-10-04
**Geprüftes Dokument:** `spec/req/REQ-053_Grafische-Garten-Beetplanung.md` (v1.1, Entwurf). Gelesen: §1–§19, §22, §23, §28, §30 vollständig; §20/§21/§24–§27/§29/§31–§34 nur per Stichwortsuche.
**Referenz-Zielgruppen:** ZG-002 (Sabine), ZG-004 (Tom/Aisha), UZG-005 (Jonas)
**Profil:** 400 m² Hausgarten + 80 m² Parzelle (zwei Tenants), ~120 Pflanzen, 4-Jahres-Rotation, Excel-Beetplanung

**Schweregrad:** **kritisch** = ohne Änderung bleibe ich bei Excel/Papier oder der Entwurf widerspricht sich. **wichtig** = ich nutze es, aber mit Reibung oder Datenverlust-Risiko. **Hinweis** = Politur, Priorisierung.

---

## Gesamturteil

Die Spec ist für mich als Kartenwerkzeug und Pflegelogbuch stark: metrische Beete, Beet-Rahmen für die Slots (Beet verschieben ohne 40 Updates), Erledigen mit einem Tipp (GP-FR-084), append-only Protokoll, Feldmodus mit 64-px-Zielen und 7:1-Kontrast. Das ist näher an meinem Alltag als alle drei Apps, die ich probiert habe.

Als **Jahresplanungswerkzeug** trägt der MVP nicht. Die Fruchtfolge, wegen der ich überhaupt eine App will, steht komplett in SHOULD (GP-FR-131–135) und ist aus dem MVP ausgenommen (§28.2). Der MVP baut die Nachbarschaftsableitung (GP-FR-130), zeigt aber nirgends eine Mischkultur-Aussage. Die Überwinterung und der Frostschutz kommen im Dokument nur als Verweis „wird benötigt von REQ-047" vor. Ich würde den MVP im ersten Jahr für Plan, Pflege und Doku nutzen. Fruchtfolge und Winterplanung blieben im Excel.

Zwei strukturelle Löcher im Datenmodell würden mich im zweiten Jahr treffen: ein Slot kann nur einen Run auf einmal reservieren (F-01), und es gibt keinen Saisonwechsel (F-02).

---

## 1. Use Cases §6 und Feldmodus §18 — deckt das meinen Gartentag?

Der Feldmodus deckt das Erledigen, die Notiz, das Foto, „Gepflanzt" und die Positionskorrektur ab. Es fehlen die Handgriffe, die ich in Beet und Gewächshaus tatsächlich tue.

| Gartentag-Handgriff | Abgedeckt? |
|---|---|
| Gießen abhaken | ja (Schritt 5) |
| Ernten und wiegen („2 kg Zucchini") | nur wenn vorher ein Task existiert; kein Schnellpfad |
| Direktsaat (Möhren, Salat) | nein, nur „Gepflanzt" (Schritt 8) |
| Beet abräumen / Saisonende | kein UC |
| Gründüngung einsäen | kein UC; nur SHOULD-Material `green_manure` (GP-FR-124) |
| Vlies/Abdeckung auflegen, Dahlien ausgraben | keine Kategorie, kein UC |
| Gießdienst übernehmen/übergeben | kein UC, DutyRotation (REQ-024) nirgends referenziert |
| Gewächshaus lüften | keine Kategorie |

### F-01 [kritisch] Ein Slot, ein Run: Folgekultur und Nachkultur nicht planbar (GP-FR-065, V-08, GP-FR-066, GP-FR-074)

**Problem:** „Ein Slot kann für maximal einen Run gleichzeitig geplant sein, dessen Status `planned` oder `active` ist." Ich plane im August den Feldsalat auf den Platz der Tomaten, die noch stehen. Das wird mit 409 `slot.already_planned` abgelehnt. Ebenso mein Radieschen, dann Salat, dann Feldsalat im selben Beet. Sukzession (GP-FR-074) ist SHOULD und nicht im MVP.

**Änderung:** Reservierung mit Zeitfenster (`planned_from`, `planned_until`, aus Run-Start und erwartetem Ernteende). V-08 greift nur bei überlappenden Fenstern. Alternativ: ein Slot ist zeitlich versioniert. Dazu ein Abnahmekriterium: „Run B (Aug–Nov) auf Slot von Run A (Mai–Sep, active) → 200, Hinweis auf Überlappung Aug–Sep, kein 409".

### F-02 [kritisch] Kein Saisonwechsel: Slots wachsen jedes Jahr, V-06 blockiert die Zonen des Folgejahrs (GP-FR-064, V-06, §6, §7.4)

**Problem:** Jeder Run erzeugt neue Slots (GP-FR-064). Es steht nirgends, was mit den Slots abgeschlossener Runs passiert. Zonen dürfen sich laut V-06 nicht überlappen. Meine Zone „Möhren 2026" blockiert dann „Bohnen 2027" an derselben Stelle. Es gibt auch kein „Beet räumen" (alle Pflanzen eines Beets mit `termination_type` und Datum beenden) und keinen Jahreswechsel-Dialog. Die Beetliste und der Plan zeigen nicht, was „dieses Jahr" ist.

**Änderung:**
1. Neuer UC-18 „Beet räumen": Mehrfach-Beenden aller aktiven Pflanzen mit Grund (geerntet/Frost/Ende der Saison) und Datum, Rückfrage „Beet auf `fallow` setzen?". Das ist ein Request, nicht 40 Klicks.
2. Slots abgeschlossener Runs werden archiviert (aus Plan und Prüfungen ausgeblendet). V-06/V-08 prüfen nur gegen `planned`/`active`.
3. Einen „Saison"-Umschalter (Jahr) in der Planansicht einführen (siehe F-05).

### F-03 [wichtig] Handgriffe fehlen als Task-Kategorien und Schnellprotokoll (§12.1, GP-FR-082, GP-FR-090, §18.1)

§12.1 ergänzt `liming`, `ph_adjustment`, `ec_check`, `flush` und lässt aus: Winterschutz/Abdecken (Vlies, Reisig), Ausgraben/Einlagern (Dahlien, Gladiolen), Anhäufeln (Kartoffeln, Rosen), Ausdünnen/Vereinzeln, Lüften (Folientunnel), Beet räumen.

**Änderung:**
1. Neue Kategorien `winter_protection`, `lifting_storage`, `hilling`, `thinning`, `ventilation`, `clearing`.
2. `flush`, `ec_check`, `ph_adjustment` bleiben im Enum (Migration), erscheinen aber nur für Hydro/Indoor oder ab Erfahrungsstufe „Profi" (REQ-021).
3. Feldmodus erhält ein Schnellprotokoll (Schaltfläche „+") mit sechs Chips: Gegossen, Geerntet, Gesät, Gejätet/Gemulcht, Gepflanzt, Notiz. Jeder Chip ist maximal 3 Tipps und läuft über `POST /care-events` ohne Task (GP-FR-090).

**Widerspruch im Dokument:** GP-FR-090 ist SHOULD, steht aber mit MVP = „ja" in der Tabelle und fehlt in §28.3 Nr. 12. Entweder MUST oder streichen. Ich brauche es als MUST: ohne es kann ich im Feldmodus nichts erfassen, was nicht vorher als Task angelegt wurde.

### F-04 [wichtig] Frostschutz und Überwinterung sind im Plan nicht angebunden (Kopf, §7.1, §9.5)

REQ-047 (Überwinterung), die Frostprognose (REQ-392) und `frost_exposed` kommen in REQ-053 nur als „wird benötigt von" vor. Meine Tomaten sind durch zu frühes Auspflanzen erfroren. Der Plan weiß, welche Beete frostempfindliche Pflanzen tragen, und sagt es mir nicht.

**Änderung:**
1. Ebene „Frost" im Plan (SHOULD): Beetbadge, wenn Prognose unter 2 °C und im Beet eine Pflanze mit `frost_sensitivity` steht. Feldmodus-Sheet: „Heute Nacht Frost: Tomate, Zucchini — Vlies?".
2. Winterschutz als Task am Beet (F-03), Überwinterungsorte (Keller, Schuppen) als GardenObject/Location auf dem Plan (REQ-047 verweist darauf).
3. Mindestens im MVP: ein Textverweis, wie REQ-047 und REQ-053 zusammengreifen.

### F-05 [wichtig] Gießdienst (GP-FR-088/117): Mechanik ja, Organisation nein

**Problem:**
- GP-FR-088 (MUST) arbeitet auf bestehenden Tasks. Wer legt „Gießen" für 30 Parzellen an? In Aishas Sicht fehlt der Task, dann fehlt der Button.
- GP-FR-117 („alle Beete der Zone", Mengenverteilung nach Fläche) ist SHOULD und hängt an Zonen, die im MVP fehlen. Im MVP gibt es keine Zonen, also kein „alle Beete der Zone".
- DutyRotation und die Pinnwand aus ZG-004 §3.2 kommen im Dokument nicht vor. Es gibt keinen Übergabe-Hinweis („Beet 7 hat gewelkt, Tonne ist leer").
- „Zuletzt gegossen vor n Tagen" ist erst GP-FR-112 (SHOULD). Das ist reine Ableitung aus `care_events` und hätte als Planebene den größten Gießdienst-Nutzen.

**Änderung:**
1. Im MVP „Mehrere Beete wählen → Gegossen" (Mehrfachauswahl in der Kartenansicht, nicht nur Zone). Dazu ein Schnellprotokoll ohne Task.
2. Planebene „zuletzt gegossen" (Farbskala 0–1 / 2–3 / 4+ Tage) aus GP-FR-112 ins MVP.
3. Gießrunde = ein Task mit Beetliste, der von der DutyRotation (REQ-024) dem Diensthabenden zugewiesen wird. Am Ende ein Freitext-Übergabefeld, sichtbar für den Nächsten. Das ist klein: ein `care_event(category = handover)`.
4. „Regen hat gegossen" als Ein-Tipp-Überspringen (`skipped`, Grund `rain`).
5. Gießmenge in „Kannen" (konfigurierbar, Standard 10 l) zusätzlich zu Litern. Ich gieße mit Gießkanne, nicht mit Zähler.

---

## 2. Editor §9 und Beetverwaltung §10

### Was in der Winterplanung wirklich MUST ist
Rechteck/Polygon/Kreis (Gartengrenze ist bei mir unrechtwinklig, also ist Polygon-Punktbearbeitung GP-FR-023 richtig als MUST), Snap, Maßanzeige, Undo, Duplizieren, Eigenschaftenpanel mit Zahleneingabe, Sperren (GP-FR-032), Beetliste (GP-FR-042), Beet-Zusammenfassung (GP-FR-047), Zuweisung (GP-FR-050). Das stimmt.

### F-06 [Hinweis] MUST, das ich nie nutzen würde, und Reibungen daran

- **GP-FR-011** sechs Raster inkl. 1 cm: 5 / 10 / 25 / 50 cm / 1 m reichen; 1 cm erzeugt nur Rasterlinien-Rauschen.
- **GP-FR-027** z-Order im Kontextmenü, **GP-FR-020** `Ctrl+A`, Shift-Zehnerschritte: ohne Schaden, aber keine Priorität für den MVP.
- **GP-FR-043** `height_m` als Pflichtfeld der Vorlage: Vorlagen sind SHOULD, das Feld ist MUST. Als Pflichtfeld beim Hochbeet-Anlegen würde es mich stören; optional, Standard 0,8 m.
- **GP-FR-143** serverseitiger SVG-Export als MUST: Ich brauche PDF. SVG kann hinter PDF warten (intern trotzdem nötig).
- **GP-FR-081** „für jede Pflanze im Beet" erzeugt n Tasks: bei 40 Pflanzen ein Klon-Sturm. Nur für Gruppen sinnvoll (Beschränkung auf eine Spezies/Zone).
- **MoSCoW/MVP-Widersprüche** (SHOULD, aber MVP = „ja"): GP-FR-013, GP-FR-031, GP-FR-048, GP-FR-090, GP-UX-016; GP-FR-089 ist COULD mit MVP „ja (Badge)". §8-Zählung und §28 sollten bereinigt werden.

### F-07 [wichtig] Alltägliches am Beet fehlt: umbenennen, teilen, zusammenlegen (§10, GP-FR-064, R-7.6)

- **Umbenennen:** Die `slot_id` hat das Format `BEET03_R2P05` (GP-FR-064). Wenn ich „Beet 3" in „Tomatenbeet" umbenenne, brechen dann die slot_ids und die Historie? Festlegen: `slot_id` ist unveränderlich (`location_code` beim Anlegen vergeben), Name frei.
- **Teilen/Zusammenlegen:** In der Praxis teile ich ein 6-m-Beet in „3a/3b" oder lege zwei Beete zusammen. R-7.6 erlaubt keinen Typwechsel, aber nichts regelt Teilen. Die Fruchtfolge-Historie hängt über `placed_in` an Slots (§16.1): bei Teilen oder Zusammenlegen muss die Historie auf beide Teile gehen. Neue Operation `split_location`/`merge_locations` mit Historienübernahme (SHOULD, aber Datenmodell jetzt festlegen).
- **Skalieren eines Beets mit Pflanzen:** GP-FR-022 skaliert das Beet im Beet-Rahmen. Was passiert mit Slots, die danach außerhalb liegen (V-04)? Ablehnen mit Liste (wie V-19) oder Slots mit Hinweis übernehmen.

### F-08 [kritisch] Jahr-zu-Jahr: keine Kopie des Plans, keine Vorjahresansicht, „Was stand hier letztes Jahr?" erst im Tab (GP-FR-025, GP-FR-103, GP-UX-006)

- GP-FR-025 dupliziert Beete, nicht Bepflanzungen. Es gibt keine „Plan von 2026 als Entwurf für 2027 übernehmen, Starkzehrer-Beete um eins rotieren".
- „Was stand hier letztes Jahr?" gibt es nur im Historie-Tab (GP-FR-103) nach Öffnen des Beets. In der Winterplanung will ich es **am Plan** sehen, ohne 10 Beete einzeln zu öffnen.
- Zugleich ist die Rotationsmatrix (GP-FR-135) SHOULD, nicht MVP.

**Änderung:**
1. Planansicht mit Saison-Umschalter (Jahr −1 / aktuell / +1). Er zeigt je Beet die Familie/Spezies des gewählten Jahres, farbcodiert nach Zehrer-Stufe (Starkzehrer rot, Mittel gelb, Schwach grün, Gründüngung blau).
2. Info-Blase (GP-UX-006) erhält eine Zeile „Vorjahr: Tomate (Solanaceae)". Das ist eine einzige Abfrage auf `GET /locations/{key}/rotation` (GP-API-039, existiert im MVP).
3. „Saison kopieren" als SHOULD: Plan-Entwurf nächstes Jahr aus Vorjahr, Rotationsvorschlag nach GP-FR-133.
4. Erste Nutzung: Vorjahre nacherfassen (siehe F-12).

### F-09 [wichtig] Gemeinschaftsgarten: Plan-Revision blockiert bei Betrieb (GP-API-010, GP-NFR-013, GP-FR-026, GP-FR-068)

Das Geometrie-Update außerhalb des Batch erhöht ebenfalls `plan_revision`, und die Batch-API verlangt `expected_revision` für die ganze Site. Positionskorrekturen (GP-FR-068, Slot-Geometrie) und Schnellpflanzungen von 35 Mitgliedern in der Saison erhöhen die Revision. Tom hat den Plan zum Bearbeiten offen und bekommt 409, der Undo-Stapel wird geleert (GP-FR-026). §29 begründet „selten gleichzeitig bearbeitet" — im Gemeinschaftsgarten im Mai trifft das nicht zu.

**Änderung:**
1. Revision pro Fläche statt pro Site: Slots und Pflanzungen zählen nicht in `plan_revision`. Konflikt nur bei Berührung derselben Objekt-Keys (Revision je Location/Objekt).
2. Parzellen-Geometrien standardmäßig `locked` für Mitglieder, nur Leitung entsperrt (GP-FR-032, derzeit nur Gartengrenze). Als Massenoperation „alle Parzellen sperren".

### F-10 [wichtig] 30 Parzellen anlegen (UC-02/GP-FR-025/GP-FR-044/045, ZG-004)

Tom legt per `Ctrl+D` 30× ein Beet an und benennt jedes von Hand. Die Vorlagen (GP-FR-044) sind SHOULD, aber auch sie lösen die Reihung nicht.

**Änderung:** „Mehrfach duplizieren" im Kontextmenü (n Stück, Versatz in x/y, Namensschema „Parzelle {n}", Start n). Das ist MVP-tauglich und klein.

---

## 3. Pflanzplanung §11

### F-11 [wichtig] 7 Schritte: am Schreibtisch zumutbar, aber zu viele freie Zahlen (§11.1, GP-FR-061)

Für die Winterplanung ist der Dialog gut: Beet, Spezies, Layout, Abstände, Vorschau, anlegen. Reibung:
- Die Felder Pflanzabstand/Reihenabstand/Randabstand/Pflanztiefe sind ohne Steckbrief-Vorbelegung leer, und die Vorbelegung (GP-FR-061) ist SHOULD, also nicht MVP. Ich tippe für jede Pflanze vier Werte, und ich kenne sie nicht alle. „Kein stiller Default" ist richtig, aber ein zuletzt-verwendet pro Spezies/Sorte kostet nichts.
- **Änderung:** Im MVP „zuletzt verwendete Abstände dieser Spezies" vorbelegen (aus eigenen Runs). Randabstand und Pflanztiefe unter „Weitere Optionen" einklappen. Die Steckbrief-Defaults kommen später.
- **Sorte statt Spezies:** Schritt 2 sagt „Spezies/Sorte", der Feldmodus-Schnellpfad (Schritt 8) nur „Spezies". Ich will „San Marzano", nicht „Tomate", sonst ist der Sortenvergleich (meine Doku-Frage) tot. Die Sorte ist auch im Feldmodus auswählbar.

### Priorisierung der Layouts und der Mischkultur

- **Triangular** ist im MVP verzichtbar (§28 zählt nur grid/rows/free, aber GP-FR-060 führt alle fünf als MVP). **Zone** fehlt in der MVP-Liste, ist aber für Breitsaat und Direktsaat nötig (Möhren, Radieschen, Feldsalat). GP-FR-067 (MUST) beschreibt Zonen. Widerspruch: Zone in den MVP, `triangular` nach hinten.
- **Mischkultur-Zonen (GP-FR-070) SHOULD** ist als Zonen-Zuweisung vertretbar. **Alternierende Reihen** (Möhre/Zwiebel, Tomate/Basilikum) gehören aber in den MVP als einfache Reihenzuweisung am Entry (`row_pattern`, z. B. „A-B-A-B"). Sonst platziere ich 60 Positionen von Hand per `free`.
- **Randbepflanzung (GP-FR-071) SHOULD** ist hoch gegriffen. Studentenblume am Beetrand setze ich einmal von Hand (`free`). COULD wäre ehrlicher.
- **Die Mischkultur-Aussage selbst (GP-FR-132, Teil Kompatibilität) gehört in den MVP.** Der MVP leitet `adjacent_to` aus Geometrie ab (GP-FR-130) und beschreibt das als Voraussetzung, „sonst läuft die Mischkultur-Engine für Beete leer" (§28.1). Dann zeigt er aber nirgends ein Ergebnis. Das ist ein Guard, der gebaut und nicht sichtbar ist. `check_compatibility` existiert, braucht keine Beet-Historie. Nur der Fruchtfolge-Teil braucht Historie. Teilen: GP-FR-132a (Mischkultur-Hinweis im Dialog und im Info-Blasen-Text) MUST/MVP, GP-FR-132b (Fruchtfolge) siehe F-12.

---

## 4. Pflege §12 und Historie §13

### Erledigen-Dialog GP-FR-084
Richtig: kategoriespezifische Felder, alle optional, ein Tipp auf „Erledigt" genügt. Das ist das beste Stück der Spec. Drei Reibungen:

### F-13 [wichtig] Fehltipp im Feldmodus ohne Rückgängig (GP-FR-101, GP-UX-023, §18.1 Schritt 5)

Das Protokoll ist append-only, Korrektur nur per `supersede`/`void` (GP-FR-101). Mit nassen Händen tippe ich daneben. Es ist kein Rückgängig im Feldmodus vorgesehen, und das Abhaken eines Gießens, das nicht stattfand, bleibt als Eintrag stehen (Folgeeinträge `voided_at`).

**Änderung:**
1. Nach „Erledigt" eine Snackbar „Rückgängig" für 8 Sekunden. Sie storniert intern (void) ohne Begründungsdialog, und der Eintrag erscheint nicht in der Historie (Zeitfenster < 60 s).
2. UI-Begriff „Bearbeiten" statt „Supersede"; im Hintergrund bleibt es append-only.
3. Position-korrigiert-Ereignisse (GP-FR-068) standardmäßig aus der Historie ausblenden (Filter), sonst ist sie voller Rauschen.
4. In §18.1 Schritt 5 steht „ein Tipp genügt", die Spalte „Zielzeit" und GP-ACC-029 zählen 2 Tipps („Erledigt" + „Fertig"). Das ist inkonsistent. Mein Vorschlag: Ein Tipp auf „Erledigt" schließt, optional „Menge/Notiz" über die Snackbar nachtragen.

### F-14 [Hinweis] Revisionssicherer Pflegeeintrag (GP-FR-100)
Das Feld `outcome_rating` und `observed_outcome` sind gut für Lessons Learned. Im Dialog nur als „Ergebnis" einklappen, Standard leer. Gießmenge in Litern **oder** Kannen (siehe F-05). Pflegeeinträge von Gästen (`performed_by_label`, „Nachbarin") passen genau zu meinem Parzellenalltag.

### F-12 [kritisch] Fruchtfolge hat keine Datengrundlage im ersten Jahr (GP-FR-103, GP-FR-131–135, §28.2)

§28.2 begründet das Zurückstellen mit „braucht eine Saison Historie zum Testen". Für mich als Nutzerin ist das umgekehrt: Ich habe 15 Jahre Erfahrung und eine Excel-Tabelle Beet × Jahr. Ohne Nacherfassung der letzten 3–4 Jahre ist der Fruchtfolge-Hinweis im ersten Jahr leer und nutzlos, im zweiten Jahr zeigt er erst 1 Jahr Historie. Dazu kommen die voreingestellten 3 Jahre Rückblick (§16.1) für meine 4-Jahres-Rotation.

**Änderung:**
1. Nacherfassung: Rotationsmatrix editierbar (Beet × Jahr: Spezies/Familie/Zehrer-Stufe ohne Pflanzen und Positionen), schreibt `CropRotationPlan`-Einträge. CSV-Import meiner Excel-Matrix (Beet, Jahr, Spezies) als SHOULD.
2. GP-FR-131/133/135 in den MVP oder wenigstens GP-FR-131 + GP-FR-135 (lesend + editierbar), weil die Daten (`placed_in`, `rotation_after`) existieren.
3. `rotation_window_years` Standard 4 (Kohl/Kreuzblütler brauchen 4 Jahre Anbaupause), nicht 3.

---

## 5. MVP-Abgrenzung §28 — würde ich damit arbeiten?

**Mit dem MVP wie geschrieben:** Plan, Beete, Pflanzdurchläufe, Pflegeaufgaben und -historie, PDF. Dafür würde ich das Excel für die Karte weglassen. **Bei Papier/Excel bleibe ich** für: Fruchtfolge (§28.2), Jahreswechsel (F-02/F-08), Winterschutz (F-04), Gießdienst-Organisation (F-05), und überall, wo kein Netz ist (F-17).

### Sollte MUST sein (hochziehen)

| Anforderung | Begründung |
|---|---|
| GP-FR-132 (Mischkultur-Teil), GP-FR-130 sichtbar machen | MVP baut Nachbarschaft ohne Ausgabe (§3) |
| GP-FR-131, GP-FR-135 (lesend + Nacherfassung), GP-FR-133 | Kernnutzen Fruchtfolge (F-12) |
| GP-FR-090 (Schnellprotokoll) | steht schon als MVP-ja, ist de facto MUST (F-03) |
| GP-FR-112 (zuletzt gegossen) als Planebene | Gießdienst (F-05) |
| Zone-Layout, Reihenzuweisung für Mischkultur | Direktsaat und Mischkultur (§3) |
| Datenmodell zu F-01/F-02/F-07 | später kaum korrigierbar (Slots, Migrationen) |
| Offline-Puffer nur für Erledigen/Notiz (GP-UX-024-Teilmenge) | siehe F-17 |
| Mehrfach-Duplizieren | Tom (F-10) |

### Könnte warten (MUST → SHOULD/später)

GP-FR-143 (SVG-Export als eigenes Feature), Raster 1 cm (GP-FR-011), z-Order (GP-FR-027), `Ctrl+A` (GP-FR-020), GP-FR-081 „für jede Pflanze", Triangular-Layout (GP-FR-060), `height_m` als Pflichtfeld (GP-FR-043), GP-FR-103 mit „mindestens 5 Jahren" (3–4 reichen als Pflicht, Rest lazy).

### Bewusst richtig gestellt
Bewässerungszonen/Aktor/HA (§14) als SHOULD/COULD nach hinten: ja, richtig (Regentonne, Gießkanne). Nährstoff-Ampel und Flächendosierung SHOULD: richtig. Hintergrundbild, Messen, Ausrichten: COULD, in Ordnung.

---

## 6. Fruchtfolge als Hinweis (D-09, GP-FR-132)

**Richtig**, mit drei Ergänzungen. Ein Blocker würde mich im Gemeinschaftsgarten ärgern (ich habe nur ein Beet für Kohl) und ist fachlich falsch, weil Gründüngung, Substratwechsel und kurze Standzeiten die Regel brechen dürfen.

1. **Stärkestufen:** `severity` je Familie und Jahre-seit-letztem-Anbau (Kreuzblütler/Kohlhernie und Nachtschatten/Kraut- und Braunfäule hart, Rest weich). Stufen sind im Text von GP-FR-131 angelegt („mit `severity`"), aber ohne Skala.
2. **Sichtbar am Plan, nicht nur im Dialog:** Beetbadge bei „Hinweis aktiv" (z. B. gelber Punkt: Solanaceae nach Solanaceae). Wenn ich im Dialog „Trotzdem pflanzen" wähle, wird der Grund als `care_event(observation)` oder Beet-Notiz gespeichert (Lessons Learned).
3. **Kübel:** GP-FR-137 (Standard aus für `planter`) ist richtig, sollte aber vom ersten Tag an so gelten, nicht COULD.

---

## 7. PDF-Druck §23 (GP-FR-142) — reicht das zum Aushang am Gartentor?

Für meinen Hausgarten (10 × 6 m, 1:50 A4 quer, GP-ACC-030): ja. Für einen Aushang am Tor eines Gemeinschaftsgartens: nein.

### F-15 [wichtig] Gemeinschaftsgarten-Aushang (GP-FR-142, O-12)

- **Maßstabsstufen zu grob.** Größter aus 1:50/1:100/1:200/1:500. Ein 28 × 20 m Garten fällt auf 1:200: ein 2 × 1 m Beet ist 10 × 5 mm, Parzellennummern sind nicht lesbar. A4 quer allein reicht dann nicht.
  **Änderung:** „Einpassen" mit freiem Maßstab (gerundet auf 5er-Schritte, Maßstabsleiste zeigt ihn) und Papierformat A3 und Hochformat automatisch wählbar. Mindest-Schriftgröße für Parzellennummern 10 pt, sonst Nummern-Legende statt Beschriftung.
- **Ebenen für den Druck wählbar.** Der Aushang braucht Parzellennummern, Wege, Wasserhähne, Kompost, Schuppen, Notfall/Ansprechpartner, QR-Code zur Beetansicht (GP-FR-052). Pflanzen und Pflegestatus gehören nicht ans Tor (GP-FR-031 Ebenen auch für Druck).
- **Datenschutz.** Namen von Parzellennutzern auf einem öffentlichen Aushang: Standard aus, Opt-in je Mitglied (REQ-025). Als Anforderung festhalten, sonst druckt Tom es versehentlich.
- **Gießdienst-Plan am Tor** (wer diese Woche) wäre das, was wirklich hängt. Nicht Teil dieses Exports, aber als zweite Seite der Beetliste denkbar (REQ-024).
- **Druckvorschau** mit dem berechneten Maßstab, bevor das PDF erzeugt wird.

---

## 8. Mobile Nutzung: Hände nass, Sonne, eine Hand — was nervt

### F-16 [wichtig] Positionskorrektur und Speichern (GP-UX-008, GP-UX-023, GP-UX-003, §18.1 Schritt 9)

- **Long-Press 500 ms + Drag** auf einem nassen Display: Fehltreffer durch Tropfen und fehlendes Gefühl für Druck. Der Koordinaten-Stepper (±10 cm) ist die bessere Standardlösung. Der Stepper sollte **bildschirmbezogen** sein (hoch/runter/links/rechts, nicht Beet-x/y), sonst steht „x+10" bei einem gedrehten Beet falsch.
- **Speichern im Feldmodus unklar.** GP-UX-003: „kein Auto-Save im MVP, expliziter Speichern-Button". Im Feldmodus muss jede Aktion sofort gespeichert sein, mit Snackbar-Rückgängig. Sonst verliere ich beim Wegstecken des Handys die Änderung.
- **Tippziel „Erledigt" 64 px** ist gut. Zwei weitere Ziele nachziehen: Stepper-Pfeile und „Fertig" ebenfalls ≥ 64 px, Abstand ≥ 16 px zwischen „Erledigt" und „Verwerfen/Überspringen".
- **Doppeltipp-Schutz:** 300 ms Debounce (GP-UX-023) hilft nicht gegen versehentliches Zweitprotokoll bei langsamer Antwort. Nach dem ersten Tipp sofort Schaltfläche sperren und Zustand „gesendet" zeigen.

### F-17 [wichtig] Funkloch am Komposthaufen (GP-UX-024, §28.2)

Offline-Lesen und -Puffern ist SHOULD und nicht im MVP, weil „UI-NFR-012 repo-weit nicht umgesetzt" ist. Mein Gemeinschaftsgarten liegt im Hinterhof, die Parzelle hinten am Schuppen hat schlechten Empfang. Erledigen/Notiz, die dort scheitern, sind weg. Mindestens: ein fehlgeschlagenes „Erledigt"/„Gegossen" bleibt lokal erhalten („Nicht gesendet — wird erneut versucht") und geht beim nächsten Netz raus, mit `performed_at` aus dem Tippzeitpunkt. Der Foto-Upload darf warten. Das ist deutlich kleiner als ein vollständiges Offline-Konzept.

### F-18 [Hinweis] Einstieg im Feldmodus: Liste vor Karte, Tenant-Wechsel (§18.1 Schritt 1–2, REQ-024)

- Auf 390 px sind 30 Parzellen als Karte kaum treffbar (Auto-Zoom hilft, kostet Tipps). Einstieg als Liste „Meine Beete" (GP-FR-050 Filter) mit „Heute fällig" und Ein-Tipp-Zugriff, Karte als zweite Ansicht.
- Ich habe zwei Tenants (Hausgarten, Parzelle). Der Feldmodus soll sich Tenant, Site und Viewport merken und per QR-Link (GP-FR-052/GP-UX-028) direkt in den richtigen Tenant springen. Ein Tenant-Wechsel mit nassen Händen ist sonst ein Umweg.
- Kontrast 7:1 und Phasen-Umriss (GP-UX-021) gut. Zusätzlich: Schriftgröße ≥ 16 sp im Sheet, sonst Sonnenlicht-Lesbarkeit nicht erreichbar.
- „Foto: Zuordnung Beet oder Pflanze" (Schritt 7) mit Standard „Beet", sonst ein Extra-Tipp.
- Das Plan-Laden < 3 s auf 4G (GP-NFR-002) ist ein Ziel, aber der Kartenaufruf sollte zuerst die Aufgabenliste laden, die Geometrie danach (progressives Laden).

---

## Gut gelöst — das hilft mir direkt

- Beet-Rahmen für Slots (§9.2): Beet verschieben/drehen ist ein Update, Pflanzen wandern mit; Kübel beweglich (GP-FR-048).
- Layout-Berechnung als reine Funktion mit Testvektoren und Vorschau (GP-FR-062/063, GP-ACC-017): „Wie viele Tomaten passen bei 60 cm?" wird beantwortet.
- Erledigen mit einem Tipp, alle Felder optional (GP-FR-084, GP-ACC-029); Rückdatierung bis 365 Tage (GP-FR-085).
- Protokoll mit wer/wann/wo/warum/Produkt/Menge/betroffene Pflanzen (GP-FR-100), `performed_by_label` für Dritte.
- Fruchtfolge als Hinweis statt Blocker (D-09), 4 Zustände einer Pflanzung (§11.3) ohne zweites Statusfeld.
- Zuweisung ohne Schreibgrenze (GP-FR-050) — passt zur Koordination im Gemeinschaftsgarten.
- Feldmodus ohne Hover, ohne Swipe-Zwang, Löschen im Feldmodus nicht verfügbar (GP-UX-020/022/023/025).
- Gemeinsames Zehrer-Enum (GP-FR-138) inkl. `green_manure` und `fallow`: genau meine 4-Jahres-Logik.
- Freie Positionen mit Abstandshinweis statt Blocker (GP-FR-072, V-07).
- Quick-Planting in einem Request (GP-UX-027/GP-API-017).

## Klärungsbedarf `fallow` vs. Gründüngung (§7.4, GP-FR-124, GP-FR-138)

`fallow` = „Brache/Gründüngung" wird im Dokument gleichgesetzt. Gründüngung ist aber eine Pflanzung (Phacelia, Senf, Inkarnatklee, Run mit Spezies `green_manure_suitable`), Brache ist unbepflanzt. Wenn das Beet mit Phacelia auf `fallow` steht, widerspricht das V-09 (aktive Pflanzen) und der Fruchtfolge-Zählung. Festlegen: Gründüngung = Run auf einem `active`-Beet mit `FeederLevel.green_manure`, `fallow` nur unbepflanzt. Einsäen als `sowing` mit Material `green_manure` (heute nur SHOULD GP-FR-124) und eigener Chip im Schnellprotokoll.

---

## Zusammenfassung der Änderungen (prüfbar)

| # | Schwere | Abschnitt/GP-ID | Änderung |
|---|---|---|---|
| F-01 | kritisch | GP-FR-065, V-08 | Reservierung mit Zeitfenster statt global exklusiv |
| F-02 | kritisch | §6, GP-FR-064, V-06 | UC „Beet räumen", Slots abgeschlossener Runs archivieren, Jahr-Umschalter |
| F-08 | kritisch | GP-FR-025/103, GP-UX-006 | Planansicht mit Vorjahr, Info-Blase „Vorjahr: …", „Saison kopieren" |
| F-12 | kritisch | GP-FR-131–135, §28.2 | Nacherfassung Vorjahre, Rotationsmatrix editierbar im MVP, Fenster 4 Jahre |
| F-03 | wichtig | §12.1, GP-FR-082/090 | Kategorien `winter_protection`, `lifting_storage`, `hilling`, `thinning`, `ventilation`, `clearing`; Schnellprotokoll mit 6 Chips; GP-FR-090 MUST |
| F-04 | wichtig | Kopf, §9.5 | Frost-Ebene/Badge aus REQ-392, Überwinterungsorte auf dem Plan |
| F-05 | wichtig | GP-FR-088/112/117 | Mehrfachauswahl-Gegossen im MVP, Ebene „zuletzt gegossen", Gießrunde mit DutyRotation und Übergabe, Kannen-Einheit, „Regen" als Überspringen |
| F-07 | wichtig | §10, GP-FR-064, R-7.6 | `slot_id` unveränderlich, `split_location`/`merge_locations` mit Historienübernahme |
| F-09 | wichtig | GP-API-010, GP-NFR-013 | Revision je Fläche/Objekt statt je Site; Parzellen standardmäßig gesperrt |
| F-10 | wichtig | GP-FR-025/044 | Mehrfach-Duplizieren mit Namensschema |
| F-11 | wichtig | GP-FR-060/061/070/132, §18 Schritt 8 | zuletzt-verwendete Abstände, Sorte im Schnellpfad, Zone im MVP, Reihenzuweisung, Mischkultur-Hinweis im MVP |
| F-13 | wichtig | GP-FR-101, GP-UX-023, §18.1 | Rückgängig-Snackbar 8 s, „Bearbeiten" statt Supersede, Positionskorrekturen standardmäßig aus Historie, Tipp-Zahl vereinheitlichen |
| F-15 | wichtig | GP-FR-142 | freier Maßstab, A3/Hochformat, Ebenenwahl, Namen opt-in, Vorschau |
| F-16 | wichtig | GP-UX-003/008/023 | Stepper bildschirmbezogen als Standard, Feldmodus speichert sofort, Doppeltipp-Sperre |
| F-17 | wichtig | GP-UX-024 | minimaler Sendepuffer für Erledigen/Notiz im MVP |
| F-06 | Hinweis | GP-FR-011/020/027/043/081/143 | MUST-Ballast entschlacken, MoSCoW/MVP-Widersprüche bereinigen (GP-FR-013/031/048/089/090, GP-UX-016) |
| F-14 | Hinweis | GP-FR-100 | Ergebnisfelder einklappen, Kannen |
| F-18 | Hinweis | §18.1 | Liste vor Karte, Tenant-Merken, Schriftgröße, Foto-Standard Beet, progressives Laden |
| — | Hinweis | §7.4, GP-FR-124/138 | `fallow` ≠ Gründüngung klären |


---

## Einarbeitung (vom Aufrufer, REQ-053 v1.2, 2026-10-04)

| Befund | Status | Wo |
|--------|--------|----|
| F-01 | eingearbeitet (Betreiberentscheid) — Reservierung mit Zeitfenster | GP-FR-065, V-08, GP-ACC-039 |
| F-02 | eingearbeitet — UC „Beet räumen", Slots archiviert, V-06 nur aktiv/geplant | GP-FR-055, GP-API-019, GP-ACC-040 |
| F-03 | eingearbeitet — Kategorien, kontextabhängige Anzeige, Schnellprotokoll-Chips, GP-FR-090 MUST | §12.1, GP-UX-029 |
| F-04 | **nicht eingearbeitet** — Frost-/Überwinterungs-Ebene auf dem Plan ist REQ-047/REQ-392-Arbeit; als Bündel-Notiz für Welle 7 | — |
| F-05 | teilweise — Mehrfach-„Gegossen" war bereits MUST (GP-FR-088); Ebene „zuletzt gegossen" SHOULD (GP-UX-031); Gießrunde mit Übergabe/Regen in GP-FR-117 | §14 |
| F-06 | eingearbeitet — MoSCoW/MVP-Widersprüche bereinigt; `height_m` kein Pflichtfeld; 1 cm Raster, z-Order, `Ctrl+A`, SVG-MUST bleiben (SVG ist Grundlage des PDF) | §9, §10 |
| F-07 | eingearbeitet — Umbenennen MUST, Teilen/Zusammenlegen COULD | GP-FR-053/054 |
| F-08 | eingearbeitet — Vorjahr in Info-Blase, Jahr-Umschalter MVP; „Saison kopieren" COULD | GP-FR-077/078 |
| F-09 | eingearbeitet (Betreiberentscheid) — Revision nur für Struktur | GP-NFR-007, D-06 |
| F-10 | eingearbeitet (SHOULD) | GP-FR-025 |
| F-11 | eingearbeitet — „zuletzt verwendet", Sorte im Kurzpfad, `zone` im MVP, Reihenzuweisung MUST, Randbepflanzung COULD, Mischkultur-Hinweis MUST | §11.1, GP-FR-070/071/132 |
| F-12 | eingearbeitet (Betreiberentscheid) — Hinweise + Vorjahr im MVP; Rotationsmatrix/Overlay SHOULD; Nacherfassung als Dialog | GP-FR-131/132/135 |
| F-13 | eingearbeitet — Rückgängig-Snackbar, „Bearbeiten", `position_corrected` ausgeblendet, Tippzahl vereinheitlicht (2) | GP-FR-149, §18.1 |
| F-14 | Bündel-Notiz (Issue 33) | — |
| F-15 | eingearbeitet — feinere Maßstabsstufen, A3-Vorschlag, Ebenenwahl, keine Namen standardmäßig, Vorschau | GP-FR-142 |
| F-16 | eingearbeitet — Stepper Standard, Sofortspeichern im Feldmodus, Doppeltipp-Sperre | §18.1, GP-UX-003/023 |
| F-17 | **nicht im MVP** (Betreiberentscheid) — Offline-Hinweis + gesperrtes „Erledigt" statt stillem Verlust | GP-UX-024 |
| F-18 | eingearbeitet — Listen-Einstieg, Merken von Tenant/Site/Viewport, Schrift ≥ 16 px | GP-UX-030 |
| `fallow` vs. Gründüngung | eingearbeitet (Betreiberentscheid W-014) | §7.4, §16.3 |
